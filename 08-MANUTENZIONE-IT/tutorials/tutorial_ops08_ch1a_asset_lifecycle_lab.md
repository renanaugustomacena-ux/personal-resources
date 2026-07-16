# Tutorial: Gestione Asset IT e ITAM — Hands-On Lab

> **Documento di riferimento:** `08-gestione-asset.md`
> **Dominio:** IT Operations — IT Asset Management (ITAM)
> **Ambito:** Inventario HW/SW/rete, ciclo di vita asset, gestione garanzie, conformità licenze, EOL/EOS planning, decommissioning sicuro, GLPI+FusionInventory, reportistica ITAM, KPI
> **Durata lab:** 4-5 ore
> **Livello:** Principiante-Intermedio (nessun prerequisito tecnico specifico)
> **Prerequisiti:** GLPI operativo (da ops01 o ops07a), accesso a SRV-LINUX-01
> **Ambiente:** SRV-LINUX-01 (GLPI, script), WKS-LAB-01 (FusionInventory agent), DC-LAB-01 (inventario Windows)

---

## Lab Environment Setup

```bash
# Su SRV-LINUX-01 — verifica GLPI e crea struttura per il lab ITAM
echo "=== SETUP AMBIENTE LAB ITAM ==="

# Verifica GLPI attivo
GLPI_OK=$(curl -s --connect-timeout 5 http://localhost:8080/glpi 2>/dev/null | grep -ci "glpi\|html" || echo 0)
if [[ "$GLPI_OK" -gt 0 ]]; then
    echo "[OK] GLPI raggiungibile"
else
    echo "[WARN] GLPI non raggiungibile — avvia con: docker start glpi-app"
fi

# Crea struttura directory per le esercitazioni ITAM
mkdir -p /itam-lab/{inventario,licenze,report,scripts,certificati}

echo "[OK] Struttura directory ITAM:"
ls /itam-lab
```

```powershell
# Su WKS-LAB-01 / DC-LAB-01 — verifica prerequisiti Windows
Write-Host "=== PREREQUISITI LAB ITAM (Windows) ==="
Write-Host "ComputerName: $env:COMPUTERNAME"
Write-Host "OS: $((Get-CimInstance Win32_OperatingSystem).Caption)"

$freeGB = [math]::Round((Get-PSDrive C).Free / 1GB, 1)
Write-Host "Spazio libero C: $freeGB GB"
```

---

## PART A: FONDAMENTI — Perché Ogni Dispositivo Deve Avere una Scheda

> Immagina di gestire una biblioteca. Se non sai quanti libri hai, quali sono prestati, a chi, quando tornano, e quali sono rovinati — non puoi gestirla. Eppure molte aziende gestiscono il proprio patrimonio tecnologico esattamente così: non sanno quanti dispositivi hanno, dove sono, chi li usa, quando scadono le garanzie, quante licenze hanno comprato rispetto a quante ne usano. L'ITAM — IT Asset Management — è il sistema di catalogazione che trasforma il caos in controllo.

---

### Concetto A1: Cos'è un "Asset IT" e Perché Tenerlo Tracciato

> **Analogia.** Un'automobile aziendale ha una targa (identità unica), una data di immatricolazione (quando è entrata in azienda), un proprietario registrato, un'assicurazione (garanzia), una revisione periodica (manutenzione), e quando viene dismessa ci sono procedure precise per la rottamazione. Nessuno oserebbe avere auto aziendali senza questi dati. Eppure laptop e server — che valgono quanto un'auto — spesso girano in azienda senza record.

**Che cos'è un asset IT:**

```
ASSET IT = qualsiasi risorsa tecnologica che ha un valore
           e richiede gestione durante la sua vita utile

CATEGORIE PRINCIPALI:
  Hardware fisico:
    - Server fisici e virtuali
    - Workstation desktop / laptop
    - Dispositivi mobili aziendali
    - Periferiche (monitor, stampanti)
    - Apparati di rete (switch, router, firewall)
    - Storage (NAS, SAN)
    - UPS e infrastruttura datacenter

  Software e Licenze:
    - Software installato sugli endpoint
    - Licenze software (per-seat, per-core, subscription)
    - Contratti cloud (Azure, AWS, M365)
    - Certificati digitali

  Asset documentali:
    - Contratti di garanzia/supporto
    - Accordi con i vendor
    - Documentazione di rete

PERCHÉ TENERLI TRACCIATI:
  
  1. CONTROLLO COSTI: senza inventario, si compra per duplicare
     "Ho già una stampante nell'altra stanza" — ma lo sapevi?
     Organizzazioni senza ITAM → over-provisioning 15-30%
     
  2. CONFORMITÀ LICENZE: un audit Microsoft trova 50 copie di Office
     senza licenza → multa + acquisto forzato + danni reputazionali
     
  3. SICUREZZA: dispositivo non tracciato = dispositivo non aggiornato
     = superficie di attacco non monitorata
     
  4. PIANIFICAZIONE: sai che tra 18 mesi scadono le garanzie di
     40 server? Puoi pianificare il budget. Senza ITAM, non puoi.
     
  5. EFFICIENZA SUPPORTO: quando un utente chiama, il tecnico apre
     il record GLPI e vede: "Dell Latitude 5540, Windows 11, 32GB RAM,
     garanzia fino a 2027, ultimo ticket: batteria" → diagnosi in secondi
```

---

### Concetto A2: Il Ciclo di Vita di un Asset

> **Analogia.** Pensa a un dipendente neoassunto. Viene reclutato (procurement), inizia il giorno 1 con onboarding e accessi (deployment), lavora per anni con performance review e formazione (operations + maintenance), poi a un certo punto lascia l'azienda con offboarding (retirement), e i suoi accessi vengono revocati e i suoi strumenti redistribuiti (disposal). Un asset IT ha esattamente lo stesso ciclo — con le stesse fasi e gli stessi rischi se una fase viene saltata.

**Le 7 fasi del ciclo di vita:**

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  CICLO DI VITA ASSET IT                                         │
  │                                                                  │
  │  [1.PROCUREMENT] → [2.RECEIVING] → [3.DEPLOYMENT] → [4.OPERATION]
  │                                                           │
  │  [7.DISPOSAL] ← [6.RETIREMENT] ← [5.MAINTENANCE] ←────────┘
  └─────────────────────────────────────────────────────────────────┘

Fase 1 — PROCUREMENT (Approvvigionamento):
  Richiesta utente → valutazione tecnica → approvazione budget →
  scelta configurazione standard → ordine al fornitore
  → L'asset entra nel CMDB PRIMA dell'arrivo fisico!
  
Fase 2 — RECEIVING (Ricezione):
  Verifica corrispondenza ordine/consegna → applicazione asset tag
  → registrazione serial number → aggiornamento CMDB
  → Dove finisce fisicamente? (magazzino, rack, ufficio)
  
Fase 3 — DEPLOYMENT (Distribuzione):
  Immagine OS standard → join dominio → software aziendale →
  crittografia disco → agente inventario → assegnazione utente →
  modulo di presa in consegna firmato
  
Fase 4 — OPERATION (Operatività):
  Uso produttivo quotidiano. Incidenti → ticket GLPI.
  Aggiornamenti pianificati. Monitoraggio prestazioni.
  
Fase 5 — MAINTENANCE (Manutenzione):
  Riparazioni → RMA (Return Merchandise Authorization)
  Upgrade componenti (RAM, SSD) → gestione sostituzione
  Rinnovo garanzia se necessario
  
Fase 6 — RETIREMENT (Dismisione):
  Fine vita utile (età, prestazioni, EOS software)
  Rimozione dall'ambiente produttivo
  IMPORTANTE: recupero licenze software (license harvesting)
  
Fase 7 — DISPOSAL (Smaltimento):
  Cancellazione sicura dei dati (NIST 800-88)
  Smaltimento conforme RAEE/WEEE (non nel cestino dell'ufficio!)
  Certificato di distruzione per dati sensibili
  Aggiornamento CMDB: stato "Dismesso"
  
ERRORI TIPICI PER FASE MANCANTE:
  Manca Receiving: serial number ignoto → non si trova in garanzia
  Manca Deployment: PC senza aggiornamenti → vulnerabile da giorno 1
  Manca Retirement: licenze bloccate su PC fermo in magazzino
  Manca Disposal: hard disk gettato con dati aziendali
```

---

### Concetto A3: Tipologie di Licenze Software — il Territorio Minato

> **Analogia.** Acquistare un biglietto del treno sembra semplice, ma le tariffe ferroviarie hanno trappole ovunque: tariffa base, supplemento rapido, prenotazione obbligatoria, cambio non rimborsabile, valido solo per quel treno specifico. Le licenze software sono peggio ancora: per-seat, per-device, per-core, subscription, OEM, Volume Licensing, floating, site license — ognuna con regole diverse su chi può usarla, dove, e cosa succede quando il contratto scade. Sbagliare vuol dire essere "under-licensed" e rischiare un audit.

**Le tipologie principali:**

```
TIPO                 REGOLA                           ESEMPIO
─────────────────────────────────────────────────────────────────────────
Per-seat/Per-user    1 licenza = 1 utente              Microsoft 365
                     (può usarla su più dispositivi)
                     
Per-device           1 licenza = 1 dispositivo          Antivirus endpoint
                     (non segue l'utente)
                     
Per-core/Per-CPU     Conta i core del server!           SQL Server Enterprise
                     ATTENZIONE: virtualizzazione        (€14.000 per 2 core)
                     può moltiplicare i core visibili
                     
Subscription         Rinnovo annuale/mensile            Adobe Creative Cloud
                     Se non rinnovi: smetti di usare    (non sei proprietario)
                     
OEM                  Legata al dispositivo fisico        Windows preinstallato
                     Non trasferibile ad altro PC        Non riutilizzabile
                     
Volume Licensing (VL)Blocco di licenze con sconto       Microsoft Open/EA
                     Richiede conteggio accurato         True-up annuale
                     
Perpetua             Acquisto una-tantum                AutoCAD 2023
                     Possiedi per sempre quella versione Aggiornamenti no
                     
Concurrent/Floating  Pool condiviso                     Software CAD lab
                     N utenti contemporanei max          Non per uso intensivo

PERICOLI COMUNI:
  Under-licensing: hai 50 installazioni, licenze per 35 → audit → multa
  Cambio server:   SQL Server su nuovo server con più core → violazione
  Utente che usa licenza di chi è in ferie → violazione (per-user)
  VM che cresce (vCPU aumenta) → violazione licenze per-core
```

---

### Concetto A4: EOL vs EOS — Quando il Fornitore si Dimentica di Te

> **Analogia.** Hai comprato un televisore nel 2018. Funziona perfettamente — ma il produttore non rilascia più aggiornamenti al sistema operativo interno. Le app Netflix e YouTube smettono di funzionare. Poi esce una vulnerabilità nel firmware: non verrà mai corretta. Il televisore fisicamente funziona, ma è diventato un problema. I sistemi operativi e i software IT hanno lo stesso ciclo: la fine del supporto è il momento in cui smettono di ricevere patch di sicurezza.

**EOL vs EOS:**

```
EOL (End of Life) = Fine Vendita
  Il vendor smette di vendere il prodotto
  Ma può ancora supportarlo per un po'
  
EOS (End of Support) = Fine Supporto
  Nessun aggiornamento, nessuna patch di sicurezza, nessun fix
  Da questo giorno: sistemi critici = rischio di sicurezza
  
DATA EOS PER I SISTEMI COMUNI (conoscerle è fondamentale!):

  Sistema                    EOS
  ─────────────────────────────────────────────────
  Windows 10                 14 Ottobre 2025 → SCADUTO
  Windows 11 22H2            8 Ottobre 2024 → SCADUTO
  Windows 11 23H2            11 Nov 2025
  Windows Server 2016        12 Gennaio 2027
  Windows Server 2019        9 Gennaio 2029
  Windows Server 2022        14 Ottobre 2031
  SQL Server 2016            14 Luglio 2026 → URGENTE
  Ubuntu 20.04 LTS (standard)  Aprile 2025
  Ubuntu 22.04 LTS           Aprile 2027
  PHP 8.1                    Fine 2025
  
COSA FARE PRIMA DELLA EOS:
  T-12 mesi: pianifica la migrazione, alloca budget
  T-6 mesi:  avvia il progetto di upgrade/migrazione
  T-3 mesi:  completare gli upgrade critici (Tier 1/2)
  T-0:       sistemi ancora su versione EOS = eccezione documentata
              con piano di migrazione e data
              
SISTEMI EOS IN PRODUZIONE = VIOLAZIONE DI POLICY
  Ogni sistema su versione EOS deve avere:
  → Ticket GLPI aperto (tipo: Change)
  → Piano di migrazione con data
  → Approvazione del responsabile IT
  → Eventuale compensazione (firewall aggiuntivo, isolamento VLAN)
```

---

### Concetto A5: La Sanificazione Sicura dei Dati — Non Basta Fare "Elimina"

> **Analogia.** Distruggere un documento segreto strappandolo in 4 pezzi non è sicuro — si può ricomporre. Bruciarlo è più sicuro, ma produce fumi. Lo shredder industriale a particelle è quello che vogliono i servizi segreti. I dischi rigidi hanno lo stesso problema: cancellare un file, persino formattare il disco, non cancella i dati — li rende solo "invisibili" al filesystem, ma i blocchi fisici contengono ancora i dati originali. Un investigatore forense li recupera in ore.

```
LIVELLI DI SANIFICAZIONE (NIST SP 800-88 Rev.1):

  CLEAR (Sovrascrittura logica):
    Sovrascrive i dati con zeri/dati casuali
    Adatto per: riutilizzo interno all'azienda
    Strumenti: shred, sdelete, dd
    Tempo: 30 min - 4 ore per disco
    
  PURGE (Cancellazione crittografica/hardware):
    Rende i dati irrecuperabili anche forensicamente
    Adatto per: riutilizzo esterno, donazione, rivendita
    Strumenti: ATA Secure Erase, NVMe Crypto Erase
    Tempo: secondi (hardware-level)
    
  DESTROY (Distruzione fisica):
    Distruzione fisica del supporto
    Adatto per: dati altamente sensibili, supporti guasti
    Strumenti: degausser, shredder industriale
    Non applicabile a SSD/NVMe (magnetismo non funziona su SSD)
    
COME SCEGLIERE:
  Asset va a un altro dipendente interno:  CLEAR
  Asset va a un fornitore di riparazione:  PURGE (prima di spedire)
  Asset venduto o donato:                  PURGE
  Asset con dati classificati/sensibili:   DESTROY
  Hard disk guasto/non accessibile:        DESTROY
  
ERRORI COMUNI:
  ✗ "Ho fatto Formatta C:" → I dati sono ancora lì!
  ✗ "Ho reinstallato Windows" → Stesso risultato
  ✗ SSD con degausser → Inutile, SSD non è magnetico
  ✗ Cestino e CANC → I file occupano ancora spazio fisico
```

---

## PART B: OPERAZIONI — Costruire il Sistema di Inventario nel Lab

---

### Esercizio B1: Creare il Primo Inventario Hardware di SRV-LINUX-01

**Obiettivo.** Raccogliere manualmente le informazioni hardware di SRV-LINUX-01 e creare il record completo in GLPI.

**Background.** Nel lab usiamo comandi Linux per raccogliere le stesse informazioni che uno strumento di discovery raccoglierebbe automaticamente. Questo esercizio ti insegna cosa viene raccolta e perché ogni campo è importante.

**Step 1 — Raccolta informazioni hardware:**

```bash
# Su SRV-LINUX-01

echo "=== RACCOLTA DATI INVENTARIO HARDWARE ==="
echo "Script: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Informazioni sistema
echo "=== SISTEMA ==="
echo "Hostname:    $(hostname)"
echo "OS:          $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel:      $(uname -r)"
echo ""

# CPU
echo "=== CPU ==="
CPU_INFO=$(grep -m1 "model name" /proc/cpuinfo | cut -d: -f2 | xargs)
CPU_CORES=$(nproc)
echo "Modello:     $CPU_INFO"
echo "Core:        $CPU_CORES"
echo ""

# RAM
echo "=== MEMORIA RAM ==="
TOTAL_RAM=$(free -m | awk 'NR==2 {print $2}')
echo "Totale:      ${TOTAL_RAM} MB ($(echo "scale=1; $TOTAL_RAM/1024" | bc) GB)"
# Dettaglio slot DIMM (richiede dmidecode)
if command -v dmidecode &>/dev/null; then
    sudo dmidecode -t memory 2>/dev/null | grep -A5 "Memory Device" | \
        grep -E "Size:|Type:|Speed:" | grep -v "No Module" | head -12
fi
echo ""

# Dischi
echo "=== STORAGE ==="
lsblk -d -o NAME,SIZE,MODEL,SERIAL,ROTA 2>/dev/null | \
    awk 'NR==1 || ($3!="") {print}'
echo ""
df -h --output=source,size,used,avail,pcent,target | grep -v tmpfs | head -10
echo ""

# Rete
echo "=== RETE ==="
ip -brief link show | grep -v "^lo"
echo ""
echo "Indirizzi IP:"
ip -brief addr show | grep -v "^lo"
echo ""

# Informazioni macchina (se VM)
echo "=== TIPO MACCHINA ==="
if systemd-detect-virt --quiet 2>/dev/null; then
    echo "Virtualizzazione: $(systemd-detect-virt)"
else
    echo "Sistema fisico o rilevamento non disponibile"
fi

# Numero di serie (se disponibile)
echo ""
echo "=== IDENTIFICATIVI ==="
if command -v dmidecode &>/dev/null; then
    SN=$(sudo dmidecode -s system-serial-number 2>/dev/null)
    UUID=$(sudo dmidecode -s system-uuid 2>/dev/null)
    echo "Serial Number: ${SN:-N/A}"
    echo "UUID:          ${UUID:-N/A}"
    echo "Produttore:    $(sudo dmidecode -s system-manufacturer 2>/dev/null || echo N/A)"
    echo "Prodotto:      $(sudo dmidecode -s system-product-name 2>/dev/null || echo N/A)"
fi
```

**Step 2 — Salva il report inventario:**

```bash
# Salva tutto in un file strutturato
INVENTORY_FILE="/itam-lab/inventario/SRV-LINUX-01-$(date +%Y%m%d).txt"

cat > "$INVENTORY_FILE" << EOF
=== SCHEDA INVENTARIO ASSET ===
Data rilevazione: $(date '+%Y-%m-%d %H:%M:%S')
Rilevato da: lab-admin
Metodo: Script manuale

IDENTIFICATIVI:
  Asset Tag:     HW-SRV-0001   ← (assegnato manualmente)
  Hostname:      $(hostname)
  IP (lab):      192.168.56.20

SISTEMA:
  OS:            $(lsb_release -ds 2>/dev/null || echo "Ubuntu 22.04")
  Kernel:        $(uname -r)
  Tipo:          Virtuale (VirtualBox/simile)

HARDWARE:
  CPU:           $(grep -m1 "model name" /proc/cpuinfo | cut -d: -f2 | xargs)
  Core CPU:      $(nproc)
  RAM:           $(free -m | awk 'NR==2 {print $2}') MB
  Disco root:    $(df -h / | awk 'NR==2 {print $2}') totali

RETE:
$(ip -brief addr show | grep -v "^lo" | awk '{printf "  %s: %s\n", $1, $3}')

RUOLO:
  Funzione:      Server applicazioni lab (GLPI, Prometheus, Grafana)
  Ambiente:      Laboratorio (non produzione)
  Criticità:     Tier 3 (lab)

GARANZIA:
  Tipo:          VM di laboratorio — nessuna garanzia hardware
  Supporto:      Interno

NOTE:
  Prima rilevazione manuale per il lab ITAM
  In produzione: FusionInventory popolerà automaticamente questi campi
EOF

echo "[OK] Report salvato: $INVENTORY_FILE"
cat "$INVENTORY_FILE"
```

**Step 3 — Crea il record in GLPI:**

```bash
echo ""
echo "=== CREAZIONE RECORD IN GLPI ==="
echo ""
echo "PROCEDURA INTERFACCIA WEB GLPI (http://192.168.56.20:8080/glpi):"
echo ""
cat << 'EOF'
1. Login come glpi/glpi (admin)

2. Menu: Asset → Computer → [+] Aggiungi

3. Compila i campi:
   Nome:        SRV-LINUX-01
   Tipo:        Server
   Produttore:  (lab VM)
   Modello:     VirtualBox VM
   Numero serie: (da dmidecode o "LAB-VM-001")
   OS:          Ubuntu 22.04 LTS
   
   Locazione:   Data Center Lab
   Stato:       In uso
   Utente:      lab-admin
   Gruppo:      IT Operations
   
   Rete:
     IP:        192.168.56.20
     MAC:       (da ip link)

4. Tab "Componenti" (se GLPI lo supporta):
   Aggiungi: RAM 4 GB, CPU 2 Core

5. Salva → otterrai ID interno (es: Computer #3)

6. Aggiungi documento allegato:
   Tab "Documenti" → Aggiungi → upload del file:
   /itam-lab/inventario/SRV-LINUX-01-YYYYMMDD.txt
EOF

echo ""
echo "In ambienti reali: FusionInventory popola GLPI automaticamente"
echo "senza questo passaggio manuale."
```

**Checkpoint di verifica B1:**
- [ ] Informazioni CPU/RAM/disco raccolte con i comandi
- [ ] File report inventario salvato in `/itam-lab/inventario/`
- [ ] Record "SRV-LINUX-01" creato in GLPI con campi principali
- [ ] Sai leggere l'output di `lsblk`, `free -h`, `ip addr`

---

### Esercizio B2: Inventario Software e Rilevamento Non Autorizzato

**Obiettivo.** Rilevare tutto il software installato su DC-LAB-01 (Windows), confrontarlo con una whitelist, e identificare eventuali software non autorizzati.

**Step 1 — Raccolta inventario software su DC-LAB-01:**

```powershell
# Su DC-LAB-01 (Windows Server 2022)

Write-Host "=== INVENTARIO SOFTWARE DC-LAB-01 ==="

# Metodo 1: Registro di sistema (più completo e veloce)
$paths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
)
$installed = Get-ItemProperty $paths -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName } |
    Select-Object DisplayName, DisplayVersion, Publisher, InstallDate |
    Sort-Object DisplayName

Write-Host "Software installato (totale: $($installed.Count)):"
$installed | Format-Table -AutoSize

# Salva report
$installed | Export-Csv -Path "C:\inventario_software.csv" -NoTypeInformation -Encoding UTF8
Write-Host "[OK] Report salvato: C:\inventario_software.csv"
```

```powershell
# Metodo 2: Verifica licenze Windows e Office
Write-Host ""
Write-Host "=== VERIFICA LICENZE SISTEMA ==="

# Stato attivazione Windows
$activation = Get-CimInstance SoftwareLicensingProduct -Filter "Name like 'Windows%'" |
    Where-Object { $_.LicenseStatus -ne 0 } |
    Select-Object Name, LicenseStatus, PartialProductKey
$activation | Format-List

# Versione Office (se installato)
$officePath = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Office\*\Registration\*" `
    -ErrorAction SilentlyContinue | Select-Object -First 1
if ($officePath) {
    Write-Host "Office: $($officePath.ProductName) — $($officePath.ProductID)"
} else {
    Write-Host "Microsoft Office: non trovato"
}
```

**Step 2 — Confronto con whitelist approvata:**

```powershell
# Su DC-LAB-01
Write-Host ""
Write-Host "=== RILEVAMENTO SOFTWARE NON AUTORIZZATO ==="

# Crea whitelist di esempio (in un ambiente reale: file condiviso su rete)
$whitelist = @(
    "Microsoft Windows",
    "Microsoft Visual C++",
    "Microsoft .NET",
    "Microsoft Edge",
    "Windows Defender",
    "7-Zip",
    "Notepad++",
    "Git",
    "PowerShell",
    "Windows Admin Center",
    "RSAT: Active Directory"
)

# Rileva software installato
$paths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
)
$installed = Get-ItemProperty $paths -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName } |
    Select-Object -ExpandProperty DisplayName

# Confronta con whitelist (match parziale sul nome)
$unauthorized = $installed | Where-Object {
    $sw = $_
    -not ($whitelist | Where-Object { $sw -like "*$_*" })
}

if ($unauthorized) {
    Write-Warning "SOFTWARE NON IN WHITELIST RILEVATO:"
    $unauthorized | ForEach-Object { Write-Host "  [!] $_" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "Azione richiesta: verificare autorizzazione o rimuovere"
} else {
    Write-Host "[OK] Tutto il software installato è nella whitelist"
}

# Salva risultato
$report = [PSCustomObject]@{
    DataAudit    = (Get-Date).ToString("yyyy-MM-dd")
    Hostname     = $env:COMPUTERNAME
    TotaleInst   = $installed.Count
    NonAutorizz  = $unauthorized.Count
}
$report | Format-List
```

**Step 3 — Inventario software su SRV-LINUX-01:**

```bash
# Su SRV-LINUX-01

echo "=== INVENTARIO SOFTWARE SRV-LINUX-01 ==="
echo ""

# Pacchetti installati via dpkg
echo "Pacchetti Debian installati:"
dpkg -l 2>/dev/null | awk '/^ii/ {print $2, $3}' | wc -l
echo " pacchetti totali"
dpkg -l 2>/dev/null | awk '/^ii/ {print $2, $3}' > /itam-lab/inventario/software-linux-$(date +%Y%m%d).txt
echo "[OK] Lista salvata"
echo ""

# Container Docker (sono anche "software" da tracciare)
echo "Container Docker attivi:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null || echo "(Docker non disponibile)"
echo ""

# Servizi systemd attivi (applicazioni di servizio)
echo "Servizi systemd in esecuzione (non-standard):"
systemctl list-units --type=service --state=running 2>/dev/null | \
    grep -v "^  \(sys\|dbus\|network\|ssh\|cron\|rsyslog\|snapd\|apt\|udev\|polkit\)" | \
    head -20
```

**Checkpoint di verifica B2:**
- [ ] Inventario software DC-LAB-01 salvato in CSV
- [ ] Confronto whitelist eseguito (output WARN se software non autorizzato)
- [ ] Inventario pacchetti SRV-LINUX-01 salvato
- [ ] Sai la differenza tra inventario hardware e software

---

### Esercizio B3: Installare FusionInventory Agent e Integrarlo con GLPI

**Obiettivo.** Configurare il discovery automatico dell'inventario tramite FusionInventory, eliminando la necessità di raccolta manuale.

**Background.** FusionInventory è un agente open-source che gira su ogni endpoint (Windows, Linux, macOS) e invia automaticamente l'inventario hardware e software a GLPI. Una volta configurato, GLPI si aggiorna da solo ogni 24 ore.

**Step 1 — Verifica/Installa FusionInventory Agent su SRV-LINUX-01:**

```bash
# Su SRV-LINUX-01

echo "=== SETUP FUSIONINVENTORY AGENT ==="

# Verifica se è già installato
if command -v fusioninventory-agent &>/dev/null; then
    echo "[OK] FusionInventory Agent già installato"
    fusioninventory-agent --version
else
    echo "Installazione FusionInventory Agent..."
    sudo apt-get install -y fusioninventory-agent 2>/dev/null || {
        echo "[INFO] Pacchetto non trovato nel repo standard"
        echo "Download da GitHub:"
        echo "  https://github.com/fusioninventory/fusioninventory-agent/releases"
        echo "  Scaricare il .deb e installare con: sudo dpkg -i fusioninventory-agent_*.deb"
    }
fi
```

**Step 2 — Configura FusionInventory per puntare a GLPI:**

```bash
# Su SRV-LINUX-01 — Configurazione agent

GLPI_URL="http://localhost:8080/glpi"
# FusionInventory plugin URL (plugin deve essere installato in GLPI)
FI_ENDPOINT="$GLPI_URL/plugins/fusioninventory/"

if [[ -f /etc/fusioninventory/agent.cfg ]]; then
    echo "=== CONFIGURAZIONE FUSIONINVENTORY ==="
    
    # Backup config originale
    sudo cp /etc/fusioninventory/agent.cfg /etc/fusioninventory/agent.cfg.bak
    
    # Configura endpoint GLPI
    sudo tee /etc/fusioninventory/agent.cfg > /dev/null << EOF
# FusionInventory Agent Configuration
# Target: GLPI Lab Server

server = $FI_ENDPOINT
tag = SRV-LINUX-LABS

# Intervallo inventario: 24 ore (86400 secondi)
delaytime = 86400

# Timeout connessione
timeout = 30

# Moduli attivi
modules = inventory,deploy
EOF
    
    echo "[OK] Configurazione salvata"
    cat /etc/fusioninventory/agent.cfg
    
    # Abilita e avvia il servizio
    sudo systemctl enable fusioninventory-agent 2>/dev/null
    sudo systemctl restart fusioninventory-agent 2>/dev/null
    echo ""
    echo "Stato servizio:"
    sudo systemctl status fusioninventory-agent --no-pager 2>/dev/null | head -10
else
    echo "[INFO] File config non trovato — FusionInventory non installato"
    echo "       Il setup manuale via GLPI Web UI è l'alternativa"
fi
```

**Step 3 — Test manuale invio inventario:**

```bash
# Su SRV-LINUX-01

echo "=== TEST INVIO INVENTARIO A GLPI ==="

if command -v fusioninventory-agent &>/dev/null; then
    echo "Invio inventario forzato (--force)..."
    sudo fusioninventory-agent --force --debug 2>&1 | head -30
    echo ""
    echo "Verifica in GLPI → Asset → Computer"
    echo "Dovrebbe apparire il record di SRV-LINUX-01 con tutti i dati"
else
    echo "[INFO] FusionInventory non installato"
    echo ""
    echo "Alternativa: genera file OCS/XML manuale"
    
    # Crea un report XML semplice per simulare l'invio
    cat > /itam-lab/inventario/inventory-simulation.xml << 'XMLEOF'
<?xml version="1.0" encoding="UTF-8"?>
<REQUEST>
  <DEVICEID>SRV-LINUX-01-2026</DEVICEID>
  <QUERY>INVENTORY</QUERY>
  <CONTENT>
    <HARDWARE>
      <NAME>SRV-LINUX-01</NAME>
      <OSNAME>Ubuntu 22.04 LTS</OSNAME>
      <MEMORY>4096</MEMORY>
      <PROCESSORS>2</PROCESSORS>
    </HARDWARE>
  </CONTENT>
</REQUEST>
XMLEOF
    echo "[OK] File XML di esempio creato (simulazione)"
fi
```

**Step 4 — Setup FusionInventory su DC-LAB-01 (Windows):**

```powershell
# Su DC-LAB-01

Write-Host "=== SETUP FUSIONINVENTORY AGENT — WINDOWS ==="
Write-Host ""
Write-Host "Opzione A: Installazione silenziosa (se hai il .exe):"
Write-Host '  fusioninventory-agent_windows-x64_2.6.exe /S \'
Write-Host '    /server="http://192.168.56.20:8080/glpi/plugins/fusioninventory/" \'
Write-Host '    /tag="DC-LAB-WINDOWS" /runnow'
Write-Host ""

Write-Host "Opzione B: Configura manualmente dopo l'installazione:"
$agentCfg = "$env:ProgramData\FusionInventory-Agent\agent.cfg"
if (Test-Path $agentCfg) {
    Write-Host "[OK] Agente trovato: $agentCfg"
    Get-Content $agentCfg | Select-String "server|tag"
} else {
    Write-Host "[INFO] FusionInventory non installato su questo sistema"
    Write-Host "       Scarica da: github.com/fusioninventory/fusioninventory-agent/releases"
}

Write-Host ""
Write-Host "Verifica manuale alternativa — informazioni sistema:"
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
Write-Host "  Hostname: $($cs.Name)"
Write-Host "  OS:       $($os.Caption) ($($os.BuildNumber))"
Write-Host "  RAM:      $([math]::Round($cs.TotalPhysicalMemory/1GB,1)) GB"
Write-Host "  Dominio:  $($cs.Domain)"
```

**Checkpoint di verifica B3:**
- [ ] FusionInventory Agent installato o tentato su SRV-LINUX-01
- [ ] Configurazione punta all'endpoint GLPI corretto
- [ ] Inventario inviato manualmente (--force) o simulato
- [ ] Sai la differenza tra discovery automatica e inventario manuale

---

### Esercizio B4: Gestione Garanzie — Alert Automatico in GLPI

**Obiettivo.** Creare una dashboard delle garanzie in scadenza e uno script di alert automatico.

**Step 1 — Configura i dati di garanzia in GLPI:**

```bash
# Su SRV-LINUX-01

echo "=== CONFIGURAZIONE GARANZIE IN GLPI ==="
echo ""
echo "PROCEDURA GLPI (interfaccia web):"
echo ""
cat << 'EOF'
Per ogni asset in GLPI → Tab "Gestione" → sezione "Garanzia":

  Computer SRV-LINUX-01:
    Data acquisto:      2024-01-15
    Garanzia (mesi):    36
    Data fine garanzia: 2027-01-15
    Tipo supporto:      NBD (Next Business Day)
    Fornitore:          Lab Supplier

  Computer WKS-LAB-01:
    Data acquisto:      2023-06-01
    Garanzia (mesi):    24
    Data fine garanzia: 2025-06-01 ← SCADUTA!
    Tipo supporto:      Basic
    Fornitore:          Lab Supplier
    
  Computer DC-LAB-01:
    Data acquisto:      2024-03-01
    Garanzia (mesi):    36
    Data fine garanzia: 2027-03-01
    Tipo supporto:      4-Hour Response

CONFIGURAZIONE ALERT IN GLPI:
  Configurazione → Notifiche → Configurazione degli avvisi
  → Attivare: "Scadenza garanzia"
  → Soglie: 90 giorni, 60 giorni, 30 giorni
  → Destinatario: admin IT (o gruppo IT)
  
  GLPI invierà email automatica quando la garanzia
  si avvicina alla scadenza.
EOF
```

**Step 2 — Script bash per report garanzie:**

```bash
# Su SRV-LINUX-01

cat > /itam-lab/scripts/warranty_check.sh << 'SCRIPT'
#!/usr/bin/env bash
# warranty_check.sh — Verifica scadenze garanzie da file CSV

# In un ambiente reale questo file viene esportato da GLPI
# Per il lab usiamo un file CSV di esempio
ASSET_FILE="/itam-lab/inventario/assets-garanzie.csv"
TODAY=$(date +%s)
WARNING_DAYS=90
CRITICAL_DAYS=30

if [[ ! -f "$ASSET_FILE" ]]; then
    echo "=== CREAZIONE FILE GARANZIE DI ESEMPIO ==="
    cat > "$ASSET_FILE" << 'CSV'
AssetTag,Nome,TipoAsset,DataFineGaranzia,TipoSupporto,Criticita
HW-SRV-0001,SRV-LINUX-01,Server,2027-01-15,NBD,Tier2
HW-SRV-0002,DC-LAB-01,Server,2027-03-01,4-Hour,Tier1
HW-WKS-0001,WKS-LAB-01,Workstation,2025-06-01,Basic,Tier3
HW-WKS-0002,WKS-LAB-02,Workstation,2026-11-20,Basic,Tier3
HW-NET-0001,SW-CORE-01,Switch,2028-05-10,4-Hour,Tier1
CSV
    echo "[OK] File garanzie creato"
fi

echo "=== REPORT SCADENZE GARANZIE ==="
echo "Data: $(date '+%Y-%m-%d')"
echo ""

SCADUTE=0
CRITICHE=0
WARNING=0
OK=0

while IFS=',' read -r tag nome tipo scadenza supporto criticita; do
    [[ "$tag" == "AssetTag" ]] && continue  # Skip header
    
    SCAD_EPOCH=$(date -d "$scadenza" +%s 2>/dev/null || echo 0)
    DAYS_LEFT=$(( (SCAD_EPOCH - TODAY) / 86400 ))
    
    if [[ $DAYS_LEFT -lt 0 ]]; then
        echo "[SCADUTA] $tag — $nome ($tipo)"
        echo "         Fine garanzia: $scadenza (${DAYS_LEFT#-} giorni fa)"
        echo "         Criticità: $criticita | Supporto: $supporto"
        SCADUTE=$((SCADUTE + 1))
    elif [[ $DAYS_LEFT -le $CRITICAL_DAYS ]]; then
        echo "[CRITICA] $tag — $nome ($tipo)"
        echo "         Fine garanzia: $scadenza (tra $DAYS_LEFT giorni)"
        CRITICHE=$((CRITICHE + 1))
    elif [[ $DAYS_LEFT -le $WARNING_DAYS ]]; then
        echo "[ATTENZIONE] $tag — $nome — scade tra $DAYS_LEFT giorni ($scadenza)"
        WARNING=$((WARNING + 1))
    else
        OK=$((OK + 1))
    fi
done < "$ASSET_FILE"

echo ""
echo "=== RIEPILOGO ==="
echo "SCADUTE:    $SCADUTE asset (AZIONE IMMEDIATA!)"
echo "CRITICHE:   $CRITICHE asset (< 30 giorni)"
echo "ATTENZIONE: $WARNING asset (< 90 giorni)"
echo "OK:         $OK asset"

# Exit code per integrazione con monitoraggio
if [[ $SCADUTE -gt 0 ]]; then
    exit 2  # CRITICAL
elif [[ $CRITICHE -gt 0 ]]; then
    exit 1  # WARNING
else
    exit 0  # OK
fi
SCRIPT

chmod +x /itam-lab/scripts/warranty_check.sh
echo "[OK] Script garanzie creato"
bash /itam-lab/scripts/warranty_check.sh
```

**Checkpoint di verifica B4:**
- [ ] Dati garanzia inseriti in GLPI per almeno 2 asset
- [ ] Alert garanzia configurati in GLPI (90/60/30 giorni)
- [ ] Script warranty_check.sh eseguito con output corretto
- [ ] Sai la differenza tra Basic, NBD e 4-Hour support

---

### Esercizio B5: Decommissioning Sicuro — Sanificazione Dati

**Obiettivo.** Eseguire la procedura di sanificazione sicura su un disco di test nel lab, documentare il processo e creare il certificato di distruzione.

**Background.** Questo esercizio usa un file di test (NON un disco reale di produzione). I comandi di sanificazione reali (`shred`, `nvme format`) vanno eseguiti SOLO su dispositivi destinati alla dismissione, dopo avere eseguito il backup di tutto.

**Step 1 — Crea un disco virtuale di test:**

```bash
# Su SRV-LINUX-01
# ATTENZIONE: Questo crea un file "disco virtuale" di test.
# NON tocchiamo dischi reali in questo esercizio.

echo "=== SETUP DISCO VIRTUALE DI TEST ==="

# Crea un file di 100 MB da usare come "disco virtuale di test"
TEST_DISK="/itam-lab/test-disk.img"
dd if=/dev/urandom of="$TEST_DISK" bs=1M count=100 2>&1 | tail -1
echo "[OK] Disco virtuale creato: $TEST_DISK (100 MB)"

# Crea un filesystem su di esso (simula un disco reale)
mkfs.ext4 "$TEST_DISK" -F -q 2>/dev/null
echo "[OK] Filesystem ext4 creato"

# Monta e crea alcuni "file con dati sensibili"
mkdir -p /mnt/test-disk-mount
mount -o loop "$TEST_DISK" /mnt/test-disk-mount 2>/dev/null && {
    echo "Dati aziendali confidenziali" > /mnt/test-disk-mount/contratto.pdf
    echo "Nome,Cognome,Stipendio" > /mnt/test-disk-mount/stipendi.xlsx
    echo "Password: SuperSegreto123" > /mnt/test-disk-mount/credenziali.txt
    sync
    umount /mnt/test-disk-mount
    echo "[OK] File sensibili creati nel disco virtuale"
}
echo ""
echo "Situazione: l'asset WKS-LAB-01 viene dismesso."
echo "Il disco contiene dati aziendali. Dobbiamo sanificarlo."
```

**Step 2 — Esegui la sanificazione (CLEAR level):**

```bash
echo ""
echo "=== SANIFICAZIONE DATI (METODO: CLEAR) ==="
echo "Livello: Clear (sovrascrittura con zeri — adatto per riutilizzo interno)"
echo ""

# VERIFICA PRE-SANIFICAZIONE: leggi i "dati sensibili"
echo "Prima della sanificazione:"
mount -o loop "$TEST_DISK" /mnt/test-disk-mount 2>/dev/null && {
    echo "  File presenti:"
    ls /mnt/test-disk-mount/
    echo "  Contenuto credenziali.txt:"
    cat /mnt/test-disk-mount/credenziali.txt
    umount /mnt/test-disk-mount
}

echo ""
echo "Inizio sanificazione (metodo: dd con zeri)..."
START_TIME=$(date +%s)

# Metodo CLEAR: sovrascrittura con zeri
dd if=/dev/zero of="$TEST_DISK" bs=1M 2>&1 | tail -1

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "[OK] Sanificazione completata in ${DURATION}s"

echo ""
echo "Verifica post-sanificazione:"
if mount -o loop "$TEST_DISK" /mnt/test-disk-mount 2>/dev/null; then
    echo "  File presenti dopo sanificazione:"
    ls /mnt/test-disk-mount/ 2>/dev/null && echo "    (filesystem corrotto — come atteso)"
    umount /mnt/test-disk-mount 2>/dev/null
else
    echo "  Il disco non è più montabile (filesystem distrutto — CORRETTO)"
fi
echo ""
echo "Metodi REALI su dischi fisici:"
echo "  HDD:  shred -vzn 3 /dev/sdX           (3 passaggi + verifica)"
echo "  SSD:  hdparm --security-erase PASS /dev/sdX  (ATA Secure Erase)"
echo "  NVMe: nvme format /dev/nvme0n1 --ses=2  (Crypto Erase)"
echo "  NOTA: su SSD/NVMe NON usare dd/shred — inefficace per tecnologia flash"
```

**Step 3 — Crea il certificato di distruzione:**

```bash
ASSET_TAG="HW-WKS-0001"
SERIAL="LAB-WKS-SN-20230601"
TECNICO="lab-admin"

cat > /itam-lab/certificati/CERT-DESTR-$(date +%Y%m%d)-${ASSET_TAG}.txt << EOF
===================================================
   CERTIFICATO DI AVVENUTA SANIFICAZIONE DATI
===================================================

Numero certificato: CERT-$(date +%Y%m%d)-001
Data operazione:    $(date '+%Y-%m-%d %H:%M:%S')

ASSET IDENTIFICATO:
  Asset Tag:        $ASSET_TAG
  Hostname:         WKS-LAB-01
  Numero di serie:  $SERIAL
  Tipo dispositivo: Workstation Desktop
  Produttore:       Lab Supplier
  Modello:          Lab Model A1

INFORMAZIONI STORAGE SANIFICATO:
  Tipo supporto:    Disco virtuale (lab) / In prod: HDD/SSD/NVMe
  Capacità:         100 MB (test) / In prod: capacità reale
  Posizione:        /itam-lab/test-disk.img

METODO DI SANIFICAZIONE:
  Standard:         NIST SP 800-88 Rev.1 — Livello CLEAR
  Metodo:           Sovrascrittura con zeri (dd if=/dev/zero)
  Numero passaggi:  1
  Verifica:         Filesystem non montabile post-sanificazione

MOTIVAZIONE DISMISSIONE:
  Fine vita utile (4 anni di utilizzo)
  Prestazioni non più adeguate ai requisiti

CLASSIFICAZIONE DATI PRESENTI:
  [ ] Nessun dato sensibile confermato
  [X] Dati aziendali generici (documenti, configurazioni)
  [ ] Dati personali (GDPR applicabile)
  [ ] Dati classificati

DESTINAZIONE FINALE:
  [X] Riutilizzo interno (CLEAR sufficiente)
  [ ] Donazione / Rivendita (PURGE richiesto)
  [ ] Smaltimento RAEE

FIRMA:
  Eseguito da:   $TECNICO                    Firma: ___________
  Verificato da: (non applicabile — lab)     Firma: ___________
  Data:          $(date '+%Y-%m-%d')

===================================================
   CATENA DI CUSTODIA
===================================================

Data         | Azione                    | Responsabile
-------------|---------------------------|---------------
$(date '+%Y-%m-%d') | Ritirato dall'utente       | lab-admin
$(date '+%Y-%m-%d') | Backup dati completato     | lab-admin
$(date '+%Y-%m-%d') | Sanificazione eseguita     | lab-admin
$(date '+%Y-%m-%d') | Certificato emesso         | lab-admin
Pendente     | Smaltimento RAEE           | Da assegnare

===================================================
EOF

echo "[OK] Certificato di distruzione creato:"
cat /itam-lab/certificati/CERT-DESTR-$(date +%Y%m%d)-${ASSET_TAG}.txt
```

**Cleanup esercizio:**

```bash
# Pulizia file di test (il certificato rimane)
rm -f "$TEST_DISK"
rmdir /mnt/test-disk-mount 2>/dev/null || true
echo "[OK] File di test rimosso (certificato conservato)"
ls /itam-lab/certificati/
```

**Checkpoint di verifica B5:**
- [ ] Disco virtuale creato con file "sensibili"
- [ ] Sanificazione eseguita (dd con zeri)
- [ ] Verifica post-sanificazione confermata (filesystem non montabile)
- [ ] Certificato di distruzione creato e salvato
- [ ] Sai quando usare CLEAR vs PURGE vs DESTROY

---

## PART C: SISTEMATIZZARE — ITAM come Processo Continuo

---

### Progetto C1: SOP-ASSET-001 — Procedura Standard Gestione Asset

```
Documento: SOP-ASSET-001
Titolo:    Procedura Standard di Gestione Asset IT
Versione:  1.0
Owner:     IT Operations

---

CHECKLIST RICEZIONE NUOVO ASSET:

  [ ] Verifica corrispondenza con ordine di acquisto (PO)
  [ ] Controllo danni fisici alla ricezione (fotografare se presenti)
  [ ] Lettura serial number → registrazione nel CMDB (GLPI)
  [ ] Applicazione asset tag (etichetta con codice univoco HW-XXX-NNNN)
  [ ] Creazione record GLPI:
      - Nome, Tipo, Produttore, Modello
      - Data acquisto, Fornitore, Numero PO
      - Data inizio/fine garanzia, tipo supporto
      - Locazione: magazzino (stato: "In stock")
  [ ] Prima accensione: verifica funzionamento
  [ ] Per laptop: registrazione numero di serie batteria

CHECKLIST DEPLOYMENT ENDPOINT UTENTE:

  [ ] Immagine OS standard applicata (da template IT)
  [ ] Join al dominio Active Directory
  [ ] GPO applicate e verificate (net policies)
  [ ] Software standard installato:
      → Antivirus, Office, VPN client, FusionInventory agent
  [ ] Aggiornamenti OS applicati (patch corrente)
  [ ] Crittografia disco attivata (BitLocker con chiave escrow in AD)
  [ ] FusionInventory invia primo inventario a GLPI
  [ ] Test funzionale: rete, stampa, login, applicazioni critiche
  [ ] GLPI aggiornato: stato "In uso", assegnatario, locazione
  [ ] Modulo presa in consegna firmato dall'utente (PDF → allegato GLPI)

CHECKLIST DISMISSIONE ASSET:

  [ ] Backup dati utente completato (verificato!)
  [ ] Software assegnato per-user rimosso/license harvested:
      → M365: utente disabilitato in admin.microsoft.com
      → Adobe CC: revoca assegnazione nel Creative Cloud portal
      → Altri: deassegnazione nel sistema specifico
  [ ] Sanificazione dati (metodo in base alla destinazione):
      → Riutilizzo interno: CLEAR (dd/shred)
      → Vendita/donazione: PURGE (Secure Erase)
      → Dati sensibili: DESTROY
  [ ] Certificato di sanificazione emesso e archiviato
  [ ] Catena di custodia documentata
  [ ] GLPI aggiornato: stato "Dismesso", data dismissione
  [ ] Per smaltimento RAEE: FIR (Formulario Identificazione Rifiuto)
      conservato per 5 anni

AUDIT PERIODICO INVENTARIO:

  Trimestrale (aree critiche — datacenter):
  [ ] Confronto CMDB vs inventario fisico
  [ ] Verifica che tutti i server siano nel CMDB
  [ ] Aggiornamento locazioni (rack, posizione U)
  
  Semestrale (endpoint utente):
  [ ] Audit fisico spot su 20% degli endpoint
  [ ] Verifica asset tag leggibili
  [ ] Confronto utente CMDB vs utente reale
  
  Annuale (conformità licenze):
  [ ] Inventario software completo (FusionInventory + manuale)
  [ ] Riconciliazione licenze acquistate vs installate
  [ ] Identificazione over/under-licensing
  [ ] Azione remediation entro 30 giorni dall'audit
```

---

### Progetto C2: Script asset_compliance.sh

```bash
#!/usr/bin/env bash
# asset_compliance.sh — Report di compliance ITAM mensile
# Controlla garanzie, EOL, e genera report

set -euo pipefail

ITAM_DIR="/itam-lab"
REPORT_FILE="$ITAM_DIR/report/compliance-$(date +%Y%m).txt"
TODAY=$(date +%s)
EXIT_CODE=0

mkdir -p "$ITAM_DIR/report"

log() { echo "$@" | tee -a "$REPORT_FILE"; }
warn() { echo "[WARN] $*" | tee -a "$REPORT_FILE"; EXIT_CODE=1; }
crit() { echo "[CRIT] $*" | tee -a "$REPORT_FILE"; EXIT_CODE=2; }

log "=== REPORT COMPLIANCE ITAM — $(date '+%Y-%m-%d') ==="
log ""

# ─── 1. GARANZIE ─────────────────────────────────────────
log "── GARANZIE ──────────────────────────────"
WARRANTY_FILE="$ITAM_DIR/inventario/assets-garanzie.csv"

if [[ -f "$WARRANTY_FILE" ]]; then
    SCADUTE=0
    EXPIRING=0
    
    while IFS=',' read -r tag nome tipo scadenza supporto criticita; do
        [[ "$tag" == "AssetTag" ]] && continue
        SCAD_EPOCH=$(date -d "$scadenza" +%s 2>/dev/null || echo 0)
        DAYS=$(( (SCAD_EPOCH - TODAY) / 86400 ))
        
        if [[ $DAYS -lt 0 ]]; then
            crit "Garanzia SCADUTA: $tag ($nome) — $scadenza"
            SCADUTE=$((SCADUTE+1))
        elif [[ $DAYS -le 90 ]]; then
            warn "Garanzia in scadenza: $tag ($nome) — tra $DAYS giorni"
            EXPIRING=$((EXPIRING+1))
        fi
    done < "$WARRANTY_FILE"
    
    log "  Totale scadute: $SCADUTE | In scadenza (90gg): $EXPIRING"
else
    warn "File garanzie non trovato: $WARRANTY_FILE"
fi

log ""

# ─── 2. SISTEMI EOL/EOS ─────────────────────────────────
log "── EOL/EOS STATUS ────────────────────────"
# Verifica versione OS su questo sistema
CURRENT_OS=$(lsb_release -rs 2>/dev/null || echo "unknown")
log "  Sistema corrente: Ubuntu $CURRENT_OS"

# Tabella EOL nota
declare -A EOL_DATES
EOL_DATES["20.04"]="2025-04-01"
EOL_DATES["22.04"]="2027-04-01"
EOL_DATES["24.04"]="2029-04-01"

if [[ -n "${EOL_DATES[$CURRENT_OS]:-}" ]]; then
    EOL_EPOCH=$(date -d "${EOL_DATES[$CURRENT_OS]}" +%s 2>/dev/null || echo 0)
    DAYS_TO_EOL=$(( (EOL_EPOCH - TODAY) / 86400 ))
    
    if [[ $DAYS_TO_EOL -lt 0 ]]; then
        crit "SISTEMA EOL! Ubuntu $CURRENT_OS — EOS: ${EOL_DATES[$CURRENT_OS]}"
    elif [[ $DAYS_TO_EOL -lt 365 ]]; then
        warn "EOL entro 12 mesi: Ubuntu $CURRENT_OS — EOS: ${EOL_DATES[$CURRENT_OS]} (tra $DAYS_TO_EOL giorni)"
    else
        log "  [OK] Ubuntu $CURRENT_OS — EOS: ${EOL_DATES[$CURRENT_OS]} (tra $DAYS_TO_EOL giorni)"
    fi
fi

log ""

# ─── 3. INVENTARIO CONSISTENCY ──────────────────────────
log "── INVENTARIO ────────────────────────────"
INVENTORY_DIR="$ITAM_DIR/inventario"
LAST_INV=$(find "$INVENTORY_DIR" -name "*.txt" -newer /tmp -type f 2>/dev/null | wc -l)
log "  File inventario presenti: $(ls "$INVENTORY_DIR"/*.txt 2>/dev/null | wc -l)"
log "  Ultimo inventario: $(find "$INVENTORY_DIR" -name "*.txt" -type f 2>/dev/null | xargs ls -t 2>/dev/null | head -1 || echo 'nessuno')"

# Verifica se l'inventario è recente (< 7 giorni)
NEWEST_INV=$(find "$INVENTORY_DIR" -name "*.txt" -mtime -7 2>/dev/null | wc -l)
if [[ "$NEWEST_INV" -eq 0 ]]; then
    warn "Nessun inventario aggiornato negli ultimi 7 giorni"
fi

log ""

# ─── 4. SUMMARY ─────────────────────────────────────────
log "── RIEPILOGO ─────────────────────────────"
case $EXIT_CODE in
    0) log "STATO COMPLESSIVO: OK" ;;
    1) log "STATO COMPLESSIVO: WARNING — verifica punti segnalati" ;;
    2) log "STATO COMPLESSIVO: CRITICAL — azione immediata richiesta" ;;
esac
log ""
log "Report: $REPORT_FILE"

exit $EXIT_CODE
```

**Installazione e crontab:**

```bash
# Su SRV-LINUX-01

# Installa lo script
sudo install -m 755 /dev/stdin /usr/local/bin/asset_compliance.sh << 'EOF'
# Contenuto dello script sopra
EOF

# Oppure copia direttamente
cp /itam-lab/scripts/../asset_compliance.sh /usr/local/bin/ 2>/dev/null || \
    echo "Copia manuale richiesta"

# Crontab: esegui il primo del mese
echo "Crontab raccomandato (primo di ogni mese, ore 08:00):"
echo "0 8 1 * * lab-admin /usr/local/bin/asset_compliance.sh >> /var/log/asset_compliance.log 2>&1"
```

---

### Progetto C3: Dashboard ITAM in GLPI — KPI Mensili

```
KPI DA MONITORARE IN GLPI (visualizzabili dalla Dashboard):

╔══════════════════════════════════════════════════════════════════╗
║  KPI                         │ TARGET  │ FORMULA                ║
╠══════════════════════════════════════════════════════════════════╣
║ Accuratezza inventario       │ > 95%   │ Asset CMDB / Asset fis.║
║ Copertura FusionInventory    │ > 98%   │ Agent attivi / Totale  ║
║ Conformità licenze           │  100%   │ SW conformi / Totale   ║
║ Asset con garanzia attiva    │ > 90%   │ Garantiti / Totale     ║
║ Età media laptop (mesi)      │ < 42    │ Media (data acq.)      ║
║ Tempo deploy (gg lavorativi) │ < 2     │ Receive→Deploy         ║
║ Asset fuori EOL              │   0     │ Asset su OS EOS        ║
║ Ticket aperti per asset      │ trend↓  │ Ticket / Asset         ║
╚══════════════════════════════════════════════════════════════════╝

REPORTISTICA MENSILE — checklist:
  [ ] Eseguire asset_compliance.sh (garanzie + EOL)
  [ ] Verificare KPI nella dashboard GLPI
  [ ] Identificare asset con più ticket nel mese (→ candidati al refresh)
  [ ] Aggiornare piano refresh triennale con nuove date EOL
  [ ] Comunicare al management: asset critici fuori garanzia

INTEGRAZIONE ITIL:
  
  ITAM ↔ Incident Management:
    Asset in GLPI → collegato ai ticket incident
    Quando arriva un incident: tecnico vede subito
      • garanzia attiva? → RMA immediato
      • età asset? → decide se riparare o sostituire
      • storico incidenti? → è il 3° problema? → candidato refresh
  
  ITAM ↔ Change Management:
    Ogni Change riguarda un asset specifico del CMDB
    Impact analysis: quali asset sono collegati? Chi è impattato?
    
  ITAM ↔ Problem Management:
    Asset con molti incident simili → Problem record in GLPI
    Causa radice: hardware difettoso? Driver? Configurazione?
    
  ITAM ↔ Service Level Management:
    RTO/RPO per servizio → quali asset supportano quel servizio?
    Asset Tier 1 → garanzia 4-Hour obbligatoria
    Asset Tier 2 → garanzia NBD accettabile
```

---

## Checklist di Validazione Lab — ops08a

```
FONDAMENTI (Part A):
  [ ] A1: Conosci le categorie di asset IT e perché tracciarle
  [ ] A2: Sai le 7 fasi del ciclo di vita di un asset con esempi
  [ ] A3: Conosci almeno 5 tipologie di licenze e i rischi di non-conformità
  [ ] A4: Sai la differenza tra EOL ed EOS, e almeno 3 date EOS importanti
  [ ] A5: Conosci i 3 livelli NIST 800-88 e quando usare ciascuno

OPERAZIONI (Part B):
  [ ] B1: Inventario hardware SRV-LINUX-01 raccolto e salvato
  [ ] B2: Inventario software DC-LAB-01 (PowerShell) con check whitelist
  [ ] B3: FusionInventory Agent configurato (o tentato) su almeno un sistema
  [ ] B4: Script warranty_check.sh eseguito con output garanzie scadute/OK
  [ ] B5: Sanificazione su disco di test + certificato emesso

SISTEMATIZZARE (Part C):
  [ ] C1: SOP-ASSET-001 letta — sai le 3 checklist (ricezione, deploy, dismissione)
  [ ] C2: asset_compliance.sh installato e testato
  [ ] C3: Comprendi i KPI ITAM e il collegamento con ITIL
```

---

## Appendice A: Asset Tag Schema per il Lab

```
SCHEMA DI NUMERAZIONE ASSET TAG:

  [TIPO]-[CATEGORIA]-[SEQUENZIALE]
  
  TIPO:     HW = hardware fisico/virtuale
            SW = licenza software
            
  CATEGORIA:
    SRV = Server
    WKS = Workstation
    LAP = Laptop
    NET = Apparati di rete (switch, router, firewall)
    PRN = Stampanti
    MON = Monitor
    MOB = Dispositivi mobili
    UPS = Gruppi di continuità
    STR = Storage (NAS, SAN)
    
  SEQUENZIALE: 4 cifre (0001-9999)

ESEMPI:
  HW-SRV-0001 → primo server fisico/virtuale
  HW-LAP-0042 → 42° laptop
  HW-NET-0005 → 5° apparato di rete

IN GLPI:
  Il campo "Asset Tag" in Computer/NetworkEquipment
  corrisponde a questo codice
  Abbina al codice QR stampato sull'etichetta fisica
```

---

## Appendice B: Quick Reference — Comandi Inventario

```bash
# LINUX — Informazioni hardware rapide
lshw -short 2>/dev/null          # Overview hardware
dmidecode -t system              # Sistema (produttore, serial)
dmidecode -t memory              # Dettaglio RAM
lsblk -d -o NAME,SIZE,MODEL,SERIAL  # Dischi
ip -brief addr show               # Interfacce di rete
free -h                          # RAM disponibile
nproc                            # Numero core CPU

# LINUX — Inventario software
dpkg -l | awk '/^ii/{print $2,$3}' > sw_inventory.txt
rpm -qa --queryformat '%{NAME} %{VERSION}\n' > sw_inventory.txt  # RHEL
snap list && flatpak list         # App extra

# WINDOWS — Inventario hardware
Get-CimInstance Win32_ComputerSystem        # Info sistema
Get-CimInstance Win32_PhysicalMemory        # RAM slots
Get-CimInstance Win32_DiskDrive             # Dischi
Get-NetAdapter                              # Adattatori rete

# WINDOWS — Inventario software
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
    Where-Object DisplayName | Select-Object DisplayName,DisplayVersion |
    Export-Csv sw_inventory.csv

# SANIFICAZIONE SICURA
shred -vzn 3 /dev/sdX             # HDD: 3 passaggi + verifica
hdparm --security-erase PASS /dev/sdX  # SSD: ATA Secure Erase
nvme format /dev/nvme0n1 --ses=2  # NVMe: Crypto Erase
sdelete64 -z C:                   # Windows: sovrascrittura spazio libero
```

---

## Riferimenti

- `08-gestione-asset.md` — sezioni 1-10 (inventario, ciclo di vita, garanzie, licenze, EOL, decommissioning, strumenti, report)
- ITIL v4 Practice: IT Asset Management
- ISO/IEC 19770 — Software Asset Management Standard
- NIST SP 800-88 Rev.1 — Guidelines for Media Sanitization
- **Tutorial successivo:** `tutorial_ops08_ch1b_cmdb_implementation_lab.md`
