# Tutorial: Metodologia di Troubleshooting e Diagnostica di Rete — Hands-On Lab

> **Documento di riferimento:** `11-troubleshooting-generale.md` (sezioni 1-4)
> **Dominio:** Troubleshooting
> **Ambito:** Framework metodologico 6-step, diagnostica di rete OSI layer-by-layer, strumenti diagnostici Windows e Linux
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio — richiede ops00 (lab), ops01a (ITIL), ops03a/b (OS admin)
> **Prerequisiti:** Lab con DC-LAB-01, SRV-LINUX-01, WKS-LAB-01 funzionanti
> **Ambiente:** Tutti e 3 i nodi del lab — il troubleshooting è trasversale

---

## Lab Environment Setup

```powershell
# Verifica rapida da WKS-LAB-01 — tutti i nodi devono rispondere
$nodes = @(
    @{ Name = "DC-LAB-01";    IP = "192.168.56.10"; Port = 389 },  # LDAP
    @{ Name = "SRV-LINUX-01"; IP = "192.168.56.20"; Port = 22  },  # SSH
    @{ Name = "WKS-LAB-01";   IP = "192.168.56.30"; Port = 445 }   # SMB (locale)
)
foreach ($n in $nodes) {
    $result = Test-NetConnection -ComputerName $n.IP -Port $n.Port -WarningAction SilentlyContinue
    $status = if ($result.TcpTestSucceeded) { "[ OK]" } else { "[ERR]" }
    Write-Host "$status $($n.Name) ($($n.IP)):$($n.Port)"
}
```

Output atteso — tutti e 3 i nodi con `[ OK]`.

---

## PART A: FONDAMENTI — Il Metodo Prima degli Strumenti

> Il troubleshooting è come essere un detective: Sherlock Holmes non comincia a sparare a caso sperando di colpire il colpevole. Osserva, raccoglie indizi, formula ipotesi, le testa, elimina le impossibilità, e arriva alla soluzione per esclusione. Un tecnico IT che "prova a caso" non è un troubleshooter — è un roulette russe per l'infrastruttura.

---

### Concetto A1: Il Framework 6-Step — La Metodologia Universale

> **Analogia.** Un pilota di aereo che sente un rumore strano non preme bottoni a caso sperando di fermarlo. Segue la checklist di emergenza: identifica l'anomalia, ne valuta la possibile causa, testa la teoria (isola il motore sospetto), implementa la procedura, verifica il risultato, documenta nel log di bordo. Il Framework 6-Step del troubleshooting IT è la stessa checklist.

**Le 6 fasi, in sequenza obbligatoria:**

```
STEP 1: IDENTIFICARE IL PROBLEMA
  ↓  Raccoglie informazioni precise, NON accettare "non funziona"
  ↓  Riproduci il problema di persona se possibile
  ↓  Definisci lo scope: 1 utente? 1 piano? tutti?
  ↓  Cerca modifiche recenti: patch, change, nuovi dispositivi

STEP 2: FORMULARE UNA TEORIA DELLE CAUSE PROBABILI
  ↓  Lista di cause possibili, dalla più probabile alla meno
  ↓  Rasoio di Occam: la causa più semplice è spesso quella giusta
  ↓  Considera le basi: cavo, IP, DNS, prima di cercare bug esotici

STEP 3: TESTARE LA TEORIA
  ↓  UNA variabile alla volta — mai due modifiche contemporanee
  ↓  Test falsificabile: cosa vedrei se la teoria è giusta? sbagliata?
  ↓  Se il test esclude la teoria: torna a step 2 con la teoria successiva

STEP 4: IMPLEMENTARE LA SOLUZIONE
  ↓  Solo dopo che la teoria è CONFERMATA da un test
  ↓  Documenta cosa stai cambiando PRIMA di cambiarlo (rollback!)
  ↓  Cambia UNA COSA ALLA VOLTA

STEP 5: VERIFICARE IL RISULTATO E PREVENIRE RICORRENZE
  ↓  Testa funzionalità completa — non solo il sintomo
  ↓  Chiedi all'utente di confermare
  ↓  Pensa: cosa può impedire che accada di nuovo?

STEP 6: DOCUMENTARE I RISULTATI
  ↓  Aggiorna il ticket con causa, soluzione, tempo impiegato
  ↓  Aggiungi alla Knowledge Base se non c'era già
  ↓  Apri Problem ticket se è un incidente ricorrente
```

**La trappola più comune: saltare il passo 2**

Il 70% dei tecnici inesperti va direttamente da "problema segnalato" ad "azione correttiva" senza formulare una teoria. Risultato: lavorano per 2 ore sulla rete quando il problema era il DNS. Il passo 2 è la differenza tra un tecnico efficace e uno che "prova cose a caso".

**Regola d'oro: "Come faccio a sapere che HO TROVATO la causa?"**

Devi poter rispondere: "Se stacco/riaccendo/cambio X, il problema sparisce. Se riaccendo X al contrario, il problema ritorna." La causa è identificata solo quando puoi riprodurre il problema e risolverlo su comando.

---

### Concetto A2: Raccolta Informazioni — Le Domande Giuste

> **Analogia.** Un medico non dice "prenda questi antibiotici" alla prima lamentela. Prima fa le domande giuste: da quando? dove fa male? pulsante o continuo? ha febbre? ha viaggiato? ha preso farmaci? Le risposte guidano verso la diagnosi. Nel troubleshooting IT, le prime 5 domande determinano il 80% dell'investigazione.

**Le 5 domande fondamentali da fare all'utente (o al monitoring):**

1. **"Cos'è esattamente il sintomo?"** — Non accettare "non funziona". Forza dettagli: "Quando clicco su XYZ appare il messaggio ABC e poi la finestra si chiude." O: "L'alert Zabbix dice 'disk I/O wait > 80% per 5 minuti'."

2. **"Da quando succede?"** — Timestamp preciso, o almeno approssimativo. Correlato con il change log.

3. **"È successo prima? Quante volte?"** — Prima volta = causa acuta. Ricorrente = problema sistemico → aprire Problem ticket.

4. **"Cosa è cambiato di recente?"** — Patch, aggiornamenti, nuovi dispositivi, configurazioni, nuovo software installato dall'utente, personale nuovo.

5. **"Chi/cosa è impattato?"** — Solo questo utente? Tutti nel piano? Solo quando usano WiFi? Solo certe ore del giorno? Lo scope guida l'ipotesi.

**L'arte di riprodurre il problema:**

```
"Funziona adesso"  ≠  "Il problema è risolto"
"Non riesco a riprodurlo" ≠  "Il problema non esiste"

Strategie per problemi intermittenti:
1. Chiedi all'utente di registrare uno screen recording
2. Abilita logging verbose prima del prossimo episodio
3. Installa monitoring granulare (ogni 30 secondi invece di 5 minuti)
4. Cattura di rete continua con Wireshark (ring buffer — non riempie il disco)
```

---

### Concetto A3: Il Modello OSI — La Mappa del Troubleshooting di Rete

> **Analogia.** Quando la tua lettera non arriva a destinazione, il problema può essere a diversi livelli: il foglio su cui hai scritto è illeggibile (fisico), la busta è strappata (data link), l'indirizzo è sbagliato (network), la buca postale era piena (trasporto), il destinatario non era in casa (sessione), parlavate lingue diverse (presentazione), la richiesta era grammaticalmente sbagliata (applicazione). Il modello OSI è quella mappa del "dove si è persa la lettera".

**Il modello OSI a 7 livelli per il troubleshooting:**

```
LAYER 7 — APPLICATION  (HTTP, SMTP, DNS, SSH, FTP)
  "Il servizio applicativo funziona correttamente?"
  Strumenti: curl, telnet, browser, applicazione stessa
  
LAYER 6 — PRESENTATION (SSL/TLS, encoding, compressione)
  "I certificati sono validi? L'encoding è corretto?"
  Strumenti: openssl s_client, curl -v (per HTTPS)
  
LAYER 5 — SESSION      (NetBIOS sessions, RPC)
  "La sessione viene stabilita e mantenuta?"
  Strumenti: netstat, ss, Wireshark (seguire sessione TCP)
  
LAYER 4 — TRANSPORT    (TCP/UDP, porte, connessioni)
  "La porta è raggiungibile? TCP o UDP funziona?"
  Strumenti: Test-NetConnection, nc, nmap, telnet
  
LAYER 3 — NETWORK      (IP, routing, ICMP)
  "Il pacchetto IP arriva a destinazione? Il routing è corretto?"
  Strumenti: ping, traceroute/tracert, route print
  
LAYER 2 — DATA LINK    (MAC, Ethernet, switch, VLAN)
  "Il frame Ethernet arriva allo switch corretto?"
  Strumenti: arp -a, MAC table dello switch, ipconfig /all
  
LAYER 1 — PHYSICAL     (cavo, NIC, segnale fisico)
  "Il cavo è collegato? La NIC è attiva? Segnale fisico presente?"
  Strumenti: controllo fisico, LED porta switch, Get-NetAdapter
```

**La regola del bottom-up:**

Inizia sempre dal Layer 1 e sali. Non ha senso debuggare l'applicazione HTTPS (L7) se il cavo è scollegato (L1). Questo sembra ovvio, ma il 30% dei troubleshooting si perde ore a livello applicativo per un problema fisico.

```
Sequenza operativa per "utente non naviga su internet":
L1: Il cavo è collegato? Led della porta NIC verde?
L2: La NIC ha MAC address? arp -a mostra entry?
L3: L'host ha IP? Ping al gateway funziona?
L4: Ping a 8.8.8.8 funziona? (IP diretto, no DNS)
L7: nslookup google.com funziona? (DNS test)
L7: curl https://google.com funziona? (HTTPS test)
```

---

### Concetto A4: Strumenti Diagnostici di Rete — Il Toolkit del Troubleshooter

> **Analogia.** Un medico ha lo stetoscopio, il termometro, il saturimetro, la pressione — ognuno misura qualcosa di diverso. Un troubleshooter di rete ha ping, traceroute, nslookup, netstat, Wireshark — ognuno illumina un livello OSI diverso. Sapere quando usare quale strumento è la differenza tra 5 minuti e 5 ore di debug.

**Windows — strumenti integrati:**

| Strumento | Cosa misura | Uso tipico |
|---|---|---|
| `ping <IP>` | ICMP round-trip (L3) | "Il target è raggiungibile a livello IP?" |
| `tracert <IP>` | Percorso hop-by-hop | "Dove si perde il pacchetto?" |
| `nslookup <nome>` | Risoluzione DNS (L7) | "Il DNS risolve correttamente?" |
| `ipconfig /all` | Config IP completa | "Che IP/mask/gateway/DNS ho?" |
| `route print` | Tabella di routing | "Il mio computer sa dove mandare i pacchetti?" |
| `netstat -ano` | Connessioni e porte (L4) | "Che porte sono in ascolto? Chi si sta connettendo?" |
| `arp -a` | Cache ARP (L2-L3) | "Conosco il MAC del gateway?" |
| `Test-NetConnection` | TCP port test | "La porta 443 di quel server è aperta?" |
| `pathping <IP>` | tracert + ping statistico | "Dove c'è packet loss nel percorso?" |

**Linux (SRV-LINUX-01) — strumenti:**

| Strumento | Cosa misura | Uso tipico |
|---|---|---|
| `ping -c 4 <IP>` | ICMP round-trip | Raggiungibilità L3 |
| `traceroute <IP>` | Hop-by-hop (richiede `traceroute`) | Percorso pacchetti |
| `nslookup` o `dig` | DNS lookup | `dig @192.168.56.10 lab.local` |
| `ip addr show` | Config IP | `ip addr show enp0s8` |
| `ip route show` | Tabella routing | `ip route show` |
| `ss -tlnp` | Porte TCP in ascolto | "Che servizi sono attivi?" |
| `ss -tunp` | Tutte le connessioni | "Chi è connesso a questo server?" |
| `nc -zv <IP> <port>` | Test porta TCP | "La porta 8080 è aperta?" |
| `curl -v <URL>` | HTTP(S) request verbosa | "Cosa risponde il web server?" |
| `tcpdump` | Cattura pacchetti | "Cosa viaggia sul filo?" |

---

### Concetto A5: Performance Troubleshooting — I 4 Colli di Bottiglia

> **Analogia.** Un'autostrada a 4 corsie ma con un casello a 1 corsia blocca tutto. In un server, il problema può essere il casello del traffico dati — CPU, RAM, disco o rete. Ogni collo di bottiglia ha i suoi sintomi caratteristici, come ogni malattia ha i suoi sintomi.

**CPU Alta:**

```
Sintomi: lentezza generale, timeout applicativi, utenti che si lamentano
Diagnosi Windows: Task Manager → CPU, Get-Process | Sort-Object CPU -Desc
Diagnosi Linux:   top, htop, ps aux --sort=-%cpu
Cause comuni:
  - Processo runaway (loop infinito, bug)
  - Antivirus scan durante orario lavorativo
  - Batch job pianificato male
  - VM con vCPU insufficienti per il carico
Fix temporaneo: identifica il processo, valutas se killarlo
Fix permanente: ottimizza il codice / sposta il batch / aumenta CPU
```

**RAM Insufficiente:**

```
Sintomi: paginazione su disco (swap), lentezza estrema, OOM killer
Diagnosi Windows: Get-Counter "\Memory\Available MBytes" < 200 MB
                  Task Manager → Memory → "In Use" vs "Available"
Diagnosi Linux:   free -h → swap in uso alto
                  vmstat 1 → si column (swap in) > 0 continuamente
                  dmesg | grep -i "out of memory"
Cause comuni:
  - Memory leak in applicazione
  - Troppi servizi avviati contemporaneamente  
  - VM con RAM insufficiente
Fix temporaneo: kill processo con leak, libera cache
Fix permanente: aumenta RAM / ottimizza applicazione / separa servizi
```

**Disco Lento (I/O Bottleneck):**

```
Sintomi: query DB lente, log scritti lentamente, swap lento
Diagnosi Windows: Get-Counter "\PhysicalDisk(_Total)\Avg. Disk Queue Length"
                  Se > 2 per > 5 minuti: collo di bottiglia disco
Diagnosi Linux:   iostat -x 1 → %util colonna → se > 90%: disco saturo
                  iotop → chi scrive di più?
Cause comuni:
  - Disco HDD meccanico vs workload SSD
  - Tanti small I/O (inefficiente per HDD)
  - Disco quasi pieno (frammentazione + metadata overhead)
Fix: SSD, ottimizzazione query (meno I/O), striping RAID, cache
```

**Rete Lenta:**

```
Sintomi: trasferimenti file lenti, timeout remote, VoIP jitter/dropout
Diagnosi: iperf3 per bandwidth test, ping per latency, Wireshark per retransmit
Windows: Get-NetAdapterStatistics | Errori in ingresso/uscita
Linux:   ip -s link show → errors, dropped
Cause comuni:
  - Duplex mismatch (auto-negotiate fallito)
  - Interfaccia a 100Mbps invece di 1Gbps
  - Packet loss (cavo degradato, porta switch difettosa)
  - MTU mismatch (jumbo frames non supportati in tutta la path)
```

---

## PART B: OPERAZIONI — Troubleshooting Guidato nel Lab

> Ogni esercizio simula un problema reale. Applica il Framework 6-Step per risolverlo.

---

### Esercizio B1: Problema di Rete Base — Diagnosi Layer-by-Layer

**Obiettivo.** Data una segnalazione vaga ("non mi connetto"), applicare la metodologia OSI bottom-up per identificare il problema.

**Setup del problema simulato:**

```bash
# Su SRV-LINUX-01: simula temporaneamente un problema di rete
# Aggiungi una route sbagliata che interferisce con lab.local

# Prima: salva la configurazione attuale
ip route show

# Poi: aggiungi una route errata
sudo ip route add 192.168.56.10/32 via 192.168.56.1 2>/dev/null || echo "Route già presente o gateway non valido"
# (se il comando fallisce perché il gateway 56.1 non esiste, è perfetto — simula il problema)
```

Oppure usa questo problema più semplice da WKS-LAB-01:

```powershell
# Disabilita temporaneamente la scheda di rete host-only su WKS-LAB-01
# (se hai accesso a VirtualBox Guest Additions)
# Oppure: simula un problema DNS

# Aggiungi un'entry DNS sbagliata in hosts per simulare problema di risoluzione
Add-Content "C:\Windows\System32\drivers\etc\hosts" "192.168.99.99 srv-linux-01.lab.local"
# Ora "srv-linux-01.lab.local" risolve all'IP sbagliato
```

**Applica il Framework 6-Step:**

```powershell
# STEP 1: IDENTIFICARE IL PROBLEMA
# La segnalazione: "Non riesco a connettermi a SRV-LINUX-01"

# Raccoglie info:
# - Quale servizio? GLPI (porta 8080)
# - Da quando? Adesso
# - Chi? Solo WKS-LAB-01
# - Si può riprodurre? Sì

# STEP 2: TEORIE PROBABILI (elenca prima di procedere)
# 1. Problema Layer 1: NIC non attiva
# 2. Problema Layer 3: IP sbagliato o non assegnato
# 3. Problema Layer 3: DNS sbagliato (risolve all'IP errato)
# 4. Problema Layer 4: porta 8080 non raggiungibile
# 5. Problema Layer 7: GLPI non in esecuzione

# STEP 3: TESTA LE TEORIE (dal basso verso l'alto)

# Test L1/L2: La NIC è attiva?
Get-NetAdapter | Select-Object Name, Status, LinkSpeed

# Test L3a: IP corretto?
ipconfig /all | Select-String -Pattern "IPv4|Subnet|Gateway"

# Test L3b: Ping a IP diretto (bypass DNS)
ping 192.168.56.20 -n 4

# Test L3c: DNS risolve correttamente? (QUESTO troverà il problema)
Resolve-DnsName "srv-linux-01.lab.local"
nslookup srv-linux-01.lab.local

# Test L4: La porta 8080 è raggiungibile a quell'IP?
Test-NetConnection -ComputerName 192.168.56.20 -Port 8080

# Test L7: Il servizio GLPI risponde?
Invoke-WebRequest -Uri "http://192.168.56.20:8080/glpi" -TimeoutSec 5
```

**STEP 4: Implementa la soluzione (fix il problema DNS):**

```powershell
# Rimuovi l'entry sbagliata dal file hosts
$hostsPath = "C:\Windows\System32\drivers\etc\hosts"
$content = Get-Content $hostsPath | Where-Object { $_ -notmatch "srv-linux-01.lab.local" }
Set-Content $hostsPath $content

# Svuota la cache DNS per applicare subito la modifica
ipconfig /flushdns

# STEP 5: Verifica
Resolve-DnsName "srv-linux-01.lab.local"
Test-NetConnection -ComputerName 192.168.56.20 -Port 8080
Invoke-WebRequest -Uri "http://192.168.56.20:8080/glpi" -TimeoutSec 5
```

**STEP 6: Documenta (nel ticket GLPI o nel tuo notebook di lab):**

```
Problema: Connessione a GLPI su srv-linux-01 fallita
Causa: Entry errata nel file hosts di WKS-LAB-01 (192.168.99.99 invece di 192.168.56.20)
Diagnosi: Risoluzione DNS restituiva IP errato. Ping diretto a IP OK, nslookup falliva.
Soluzione: Rimossa entry da C:\Windows\System32\drivers\etc\hosts + ipconfig /flushdns
Prevenzione: Aggiungere monitoraggio su file hosts (FIM - File Integrity Monitoring)
```

**Checkpoint B1:**
- [ ] Framework 6-step applicato in sequenza (non saltare al passo 4 direttamente!)
- [ ] Test OSI bottom-up eseguiti nell'ordine corretto (L1→L3→L4→L7)
- [ ] Problema DNS identificato: nslookup risolve all'IP sbagliato
- [ ] Hosts file ripulito, DNS cache svuotata
- [ ] Connessione GLPI verificata funzionante
- [ ] Documentazione scritta con causa, soluzione, prevenzione

---

### Esercizio B2: Diagnosi di Rete Avanzata — Toolkit Completo

**Obiettivo.** Padroneggiare tutti i principali strumenti di diagnostica di rete, sia su Windows che su Linux.

**Setup: Installa gli strumenti su SRV-LINUX-01:**

```bash
# SSH su SRV-LINUX-01
ssh lab-admin@192.168.56.20

# Installa strumenti di rete necessari
sudo apt install -y \
    traceroute \
    dnsutils \
    nmap \
    iperf3 \
    tcpdump \
    netcat-openbsd \
    mtr

echo "Strumenti installati"
```

**Esercizio 2a: Mappatura completa della connettività del lab**

```bash
# Su SRV-LINUX-01: esegui diagnostica completa

echo "=== DIAGNOSTICA RETE LAB ==="

echo ""
echo "1. IP Configuration:"
ip addr show enp0s8

echo ""
echo "2. Routing Table:"
ip route show

echo ""
echo "3. DNS Resolution:"
dig @192.168.56.10 lab.local
dig @192.168.56.10 dc-lab-01.lab.local

echo ""
echo "4. Raggiungibilità nodi:"
for ip in 192.168.56.10 192.168.56.30; do
    ping -c 2 -W 1 $ip > /dev/null 2>&1 && echo "  [OK] $ip" || echo "  [FAIL] $ip"
done

echo ""
echo "5. Porte in ascolto:"
ss -tlnp | grep -v "127.0.0.1\|::1"

echo ""
echo "6. Test porta specifica (DC-LAB-01 LDAP):"
nc -zv 192.168.56.10 389 2>&1

echo ""
echo "7. Traceroute verso DC-LAB-01:"
traceroute 192.168.56.10
```

**Esercizio 2b: Test di banda con iperf3**

```bash
# Su SRV-LINUX-01: avvia il server iperf3
iperf3 -s -D  # -D = daemon mode (background)

# Su DC-LAB-01 (PowerShell):
# Scarica iperf3 per Windows: https://iperf.fr/iperf-download.php
# Per il lab, usa netcat per test base

# Oppure: test da SRV-LINUX-01 a se stesso
iperf3 -c 127.0.0.1 -t 5   # bandwidth test verso localhost
```

**Esercizio 2c: tcpdump — cattura e analisi traffico**

```bash
# Cattura il traffico HTTP su SRV-LINUX-01 mentre accedi a GLPI

# Finestra 1 — Su SRV-LINUX-01: avvia la cattura
sudo tcpdump -i enp0s8 -n port 8080 -w /tmp/glpi_traffic.pcap

# Finestra 2 — Su WKS-LAB-01 (PowerShell): genera traffico
Invoke-WebRequest "http://192.168.56.20:8080/glpi" -UseBasicParsing

# Finestra 1 — Ferma la cattura (Ctrl+C) e analizza
sudo tcpdump -r /tmp/glpi_traffic.pcap -n | head -30

# Leggi l'output: dovresti vedere il 3-way handshake TCP
# SYN → SYN-ACK → ACK
# poi le richieste HTTP GET
```

**Checkpoint B2:**
- [ ] `ip addr`, `ip route`, `dig`, `ss -tlnp` eseguiti e output interpretato
- [ ] Raggiungibilità di tutti i nodi del lab verificata
- [ ] Porta LDAP (389) su DC-LAB-01 verificata con `nc -zv`
- [ ] `traceroute` eseguito verso DC-LAB-01 (dovrebbe essere 1 hop — stessa subnet)
- [ ] `tcpdump` avviato, traffico catturato, file .pcap analizzato

---

### Esercizio B3: Troubleshooting Performance — Diagnosi CPU e RAM

**Obiettivo.** Simulare un problema di performance, diagnosticarlo con i tool corretti, e identificare il responsabile.

**Setup — Simula carico su SRV-LINUX-01:**

```bash
# Installa stress-ng per generare carico controllato
sudo apt install stress-ng -y

# Simula carico CPU (4 worker per 60 secondi)
stress-ng --cpu 2 --timeout 60s --metrics-brief &
STRESS_PID=$!
echo "Stress test avviato (PID: $STRESS_PID, durata: 60s)"
```

**Diagnosi performance mentre il carico è attivo:**

```bash
# 1. Top: panoramica interattiva
top -bn1 | head -20

# 2. Carico corrente (load average)
uptime
# Output: load average: 2.14, 1.05, 0.45
# → 3 valori: 1 min, 5 min, 15 min
# → se > numero CPU: sistema sotto pressione

# 3. Chi usa la CPU?
ps aux --sort=-%cpu | head -10
# → stress-ng deve apparire in cima

# 4. Uso memoria (incluso swap)
free -h
cat /proc/meminfo | grep -E "MemFree|MemAvailable|SwapFree|SwapTotal"

# 5. I/O in tempo reale
iostat -x 1 3   # 3 campioni ogni 1 secondo

# 6. Riepilogo statistiche (vmstat)
vmstat 1 5
# Colonne chiave:
#   r  = processi in attesa della CPU
#   b  = processi bloccati in I/O
#   si = swap in (da disco a RAM — MALE se alto)
#   so = swap out (da RAM a disco — MALE se alto)
#   us = CPU user  |  sy = CPU system  |  id = CPU idle

# 7. Per PID specifico: quanto usa?
ps -p $(pgrep stress-ng | head -1) -o pid,comm,%cpu,%mem,vsz,rss
```

**Confronta prima e dopo (baseline vs carico):**

```bash
# PRIMA del carico (baseline)
echo "=== BASELINE ===" > /tmp/perf_comparison.txt
uptime >> /tmp/perf_comparison.txt
free -h >> /tmp/perf_comparison.txt

# DURANTE il carico (già in esecuzione dall'esercizio sopra)
echo "=== CON CARICO ===" >> /tmp/perf_comparison.txt
uptime >> /tmp/perf_comparison.txt
free -h >> /tmp/perf_comparison.txt
ps aux --sort=-%cpu | head -5 >> /tmp/perf_comparison.txt

# Visualizza confronto
cat /tmp/perf_comparison.txt

# Dopo che il carico finisce (attendi 60s)
wait $STRESS_PID
echo "Stress test completato"
echo "=== POST-CARICO ===" >> /tmp/perf_comparison.txt
uptime >> /tmp/perf_comparison.txt
```

**Checkpoint B3:**
- [ ] `stress-ng` installato e avviato con successo
- [ ] `top` mostra `stress-ng` in cima per uso CPU durante il carico
- [ ] `uptime` mostra load average > numero di CPU durante il carico
- [ ] `vmstat` colonna `r` > 1 durante il carico
- [ ] Tabella comparativa baseline/carico/post-carico prodotta

---

### Esercizio B4: Troubleshooting DNS — Il Problema più Comune

**Obiettivo.** DNS è la causa del 30% dei "problemi di rete". Questo esercizio insegna a diagnosticare ogni tipo di problema DNS.

```powershell
# Su WKS-LAB-01 — Test DNS completo verso DC-LAB-01

# 1. Chi è il mio server DNS configurato?
Get-DnsClientServerAddress | Where-Object {$_.AddressFamily -eq 2} |
    Select-Object InterfaceAlias, ServerAddresses

# 2. Risoluzione di un nome AD
Resolve-DnsName "dc-lab-01.lab.local"
Resolve-DnsName "lab.local"  # Dovrebbe risolvere all'IP del DC

# 3. Test di risoluzione inversa (da IP a nome)
Resolve-DnsName "192.168.56.10" -Type PTR

# 4. Risoluzione verso un DNS pubblico (test Internet)
Resolve-DnsName "google.com" -Server "8.8.8.8"

# 5. Debug specifico: qual è il percorso di risoluzione?
nslookup -debug dc-lab-01.lab.local 192.168.56.10

# 6. Verifica record SRV critici per Active Directory
nslookup -type=srv _ldap._tcp.dc._msdcs.lab.local 192.168.56.10
nslookup -type=srv _kerberos._tcp.dc._msdcs.lab.local 192.168.56.10
```

```bash
# Su SRV-LINUX-01 — Test DNS dal lato Linux

# 1. Configurazione DNS attuale
cat /etc/resolv.conf

# 2. Test risoluzione avanzato con dig
dig @192.168.56.10 lab.local

# 3. Verifica la latenza DNS (tempi di risposta)
dig @192.168.56.10 lab.local | grep "Query time"

# 4. Trace DNS completo (come viene risolto il nome)
dig +trace lab.local

# 5. Test reverse lookup
dig @192.168.56.10 -x 192.168.56.10

# 6. Verifica propagazione (stesso nome su DNS diversi)
for dns in 192.168.56.10 8.8.8.8; do
    echo -n "DNS $dns: "
    dig @$dns lab.local +short 2>/dev/null || echo "FAIL"
done
```

**Simula e risolvi problemi DNS comuni:**

```powershell
# Scenario: "Il mio PC non naviga ma il ping funziona"
# Causa tipica: DNS non configurato o non raggiungibile

# Test 1: ping a IP diretto (bypass DNS) — se funziona, il problema è DNS
ping 8.8.8.8 -n 3

# Test 2: ping a nome — se fallisce, confermato problema DNS
ping google.com -n 3

# Test 3: nslookup specifico
nslookup google.com
nslookup google.com 8.8.8.8   # Usa direttamente 8.8.8.8 come DNS

# Fix: svuota la cache DNS e testa di nuovo
ipconfig /flushdns
ipconfig /registerdns
nslookup google.com
```

**Checkpoint B4:**
- [ ] `Resolve-DnsName dc-lab-01.lab.local` restituisce `192.168.56.10`
- [ ] Record SRV LDAP e Kerberos trovati correttamente
- [ ] `dig @192.168.56.10 lab.local` da SRV-LINUX-01 risponde correttamente
- [ ] Sai distinguere un problema DNS (ping IP OK, ping nome FAIL) da un problema di routing (ping IP FAIL)

---

### Esercizio B5: Troubleshooting Guidato — Scenario Complesso

**Obiettivo.** Affrontare un problema multi-livello applicando il Framework 6-Step completo senza suggerimenti.

**Scenario:** Un utente segnala: "GLPI non mi carica ma ieri funzionava. Anche i log di questa mattina ci sono. Ho dovuto fare un reboot del computer stamattina."

**Il tuo compito:**

1. Formulas le domande da fare all'utente (Step 1)
2. Lista almeno 4 teorie probabili in ordine di probabilità (Step 2)
3. Esegui i test in ordine (Step 3)
4. Quando trovi il problema, implementa la soluzione (Step 4)
5. Verifica funzionalità completa (Step 5)
6. Scrivi la documentazione (Step 6)

**Verifica la situazione reale nel lab:**

```bash
# Su SRV-LINUX-01: controlla lo stato di tutti i servizi
docker compose -f ~/glpi-docker/docker-compose.yml ps
systemctl status docker
ss -tlnp | grep 8080

# Se GLPI non risponde, restart:
cd ~/glpi-docker
docker compose down
docker compose up -d
sleep 15
docker compose ps
```

```powershell
# Su WKS-LAB-01: test completo verso GLPI
Test-NetConnection -ComputerName 192.168.56.20 -Port 8080
Invoke-WebRequest -Uri "http://192.168.56.20:8080/glpi" -TimeoutSec 10 -UseBasicParsing |
    Select-Object StatusCode, StatusDescription
```

**Checkpoint B5:**
- [ ] Hai scritto le 5 domande da fare all'utente (Step 1)
- [ ] Hai listato 4 teorie (Step 2) — possibili risposte: Docker non avviato, container GLPI crashato, rete problema, porta bloccata, DNS
- [ ] Hai eseguito i test in ordine OSI bottom-up (Step 3)
- [ ] GLPI funziona alla fine (Step 4-5)
- [ ] Hai scritto documentazione strutturata: causa, soluzione, prevenzione (Step 6)

---

## PART C: SISTEMATIZZARE — Governance del Troubleshooting

---

### Progetto C1: Knowledge Base — Template Articolo di Troubleshooting

Il valore del troubleshooting non è solo risolvere il problema, ma documentarlo affinché il prossimo tecnico impieghi 5 minuti invece di 2 ore.

```markdown
# KB-YYYY-XXXXX: [Titolo breve del problema]

**Categoria:** [Rete / Performance / Auth / Storage / Applicazione]
**Sistemi coinvolti:** [Server/servizio specifico]
**Data aggiunta:** 2026-07-15
**Autore:** [nome tecnico]
**Ultima verifica:** 2026-07-15

---

## Sintomo

[Descrizione esatta di ciò che vede l'utente o il monitoring.
Includi: messaggio di errore esatto, comportamento osservato, quando si manifesta]

Esempio: L'utente vede "ERR_CONNECTION_REFUSED" nel browser quando cerca di
aprire GLPI su http://192.168.56.20:8080. Il problema si manifesta dopo il
riavvio del server SRV-LINUX-01.

---

## Causa

[Descrizione tecnica della causa radice]

Il container Docker di GLPI non è configurato per ripartire automaticamente
dopo il riavvio del sistema operativo host. Il parametro `restart: unless-stopped`
non era presente nel docker-compose.yml.

---

## Soluzione

[Procedura step-by-step]

### Step 1 — Verifica lo stato del container
```bash
docker compose -f ~/glpi-docker/docker-compose.yml ps
```

### Step 2 — Riavvia i container
```bash
cd ~/glpi-docker && docker compose up -d
```

### Step 3 — Abilita auto-restart permanente
```yaml
# Nel file docker-compose.yml, aggiungi a ogni servizio:
services:
  db:
    restart: unless-stopped
  glpi:
    restart: unless-stopped
```

### Step 4 — Verifica
```bash
docker compose ps  # tutti i container devono essere in stato "Up"
```

---

## Verifica

Come confermare che il problema è risolto:
- `http://192.168.56.20:8080/glpi` carica la pagina di login
- Dopo un riavvio di SRV-LINUX-01: i container si avviano automaticamente in < 2 minuti

---

## Prevenzione

- Monitorare lo stato dei container Docker (alert se container non è "Up")
- Verificare i parametri di restart nelle docker-compose.yml prima del go-live
- Test di reboot pianificato mensile per verificare l'auto-recovery dei servizi

---

## Articoli Correlati

- KB per problema DNS su WKS-LAB-01
- Tutorial ops01a (GLPI install e configurazione)
```

---

### Progetto C2: Script — Diagnostica Automatizzata del Lab

```bash
#!/bin/bash
# lab_full_diagnostic.sh — Diagnostica completa del lab in un unico script
# Esegui su SRV-LINUX-01: bash /opt/lab-scripts/lab_full_diagnostic.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[ OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; }

echo ""
echo "================================================="
echo " LAB FULL DIAGNOSTIC — $(hostname) — $(date '+%Y-%m-%d %H:%M')"
echo "================================================="

# === 1. RETE ===
echo ""
echo "[ 1. RETE ]"

# IP configurato
MY_IP=$(ip addr show enp0s8 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
if [ "$MY_IP" = "192.168.56.20" ]; then
    ok "IP: $MY_IP"
else
    warn "IP: $MY_IP (atteso: 192.168.56.20)"
fi

# Raggiungibilità nodi
for host_ip in "DC-LAB-01:192.168.56.10" "WKS-LAB-01:192.168.56.30"; do
    name=$(echo "$host_ip" | cut -d: -f1)
    ip=$(echo "$host_ip" | cut -d: -f2)
    if ping -c 1 -W 2 "$ip" > /dev/null 2>&1; then
        latency=$(ping -c 1 -W 2 "$ip" | grep "time=" | awk -F"time=" '{print $2}' | cut -d' ' -f1)
        ok "Ping $name ($ip): ${latency}ms"
    else
        err "Ping $name ($ip): TIMEOUT"
    fi
done

# DNS
DNS_RESULT=$(dig @192.168.56.10 lab.local +short 2>/dev/null)
if [ -n "$DNS_RESULT" ]; then
    ok "DNS lab.local → $DNS_RESULT"
else
    err "DNS: lab.local non risolvibile da 192.168.56.10"
fi

# Test porta LDAP su DC-LAB-01
if nc -zv 192.168.56.10 389 2>/dev/null; then
    ok "LDAP (porta 389) su DC-LAB-01: raggiungibile"
else
    err "LDAP (porta 389) su DC-LAB-01: non raggiungibile"
fi

# === 2. SERVIZI SYSTEMD ===
echo ""
echo "[ 2. SERVIZI ]"

failed=$(systemctl --failed --no-legend --no-pager 2>/dev/null | wc -l)
if [ "$failed" -eq 0 ]; then
    ok "Nessun servizio systemd in stato failed"
else
    err "$failed servizi in stato failed:"
    systemctl --failed --no-legend --no-pager
fi

for svc in sshd docker; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        ok "Servizio $svc: attivo"
    else
        warn "Servizio $svc: non attivo"
    fi
done

# === 3. DOCKER / GLPI ===
echo ""
echo "[ 3. DOCKER E GLPI ]"

if command -v docker &>/dev/null; then
    RUNNING=$(docker ps -q 2>/dev/null | wc -l)
    ok "Docker attivo: $RUNNING container in esecuzione"
    
    if docker ps 2>/dev/null | grep -q "glpi"; then
        ok "Container GLPI: in esecuzione"
        
        # Test HTTP
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/glpi --max-time 5 2>/dev/null)
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
            ok "GLPI HTTP: risponde (codice $HTTP_CODE)"
        else
            err "GLPI HTTP: non risponde (codice: $HTTP_CODE)"
        fi
    else
        err "Container GLPI: non trovato (usare: docker compose up -d)"
    fi
else
    warn "Docker non installato"
fi

# === 4. PERFORMANCE ===
echo ""
echo "[ 4. PERFORMANCE ]"

# CPU Load
LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
CPUS=$(nproc)
LOAD_INT=$(echo "$LOAD * 10" | awk '{printf "%d", $1}')
THRESHOLD=$((CPUS * 10))
if [ "$LOAD_INT" -le "$THRESHOLD" ]; then
    ok "CPU Load average: $LOAD (CPUs: $CPUS)"
else
    warn "CPU Load alto: $LOAD (CPUs: $CPUS)"
fi

# RAM disponibile
RAM_FREE=$(free -m | awk 'NR==2{print $7}')
if [ "$RAM_FREE" -gt 200 ]; then
    ok "RAM disponibile: ${RAM_FREE}MB"
else
    err "RAM bassa: ${RAM_FREE}MB disponibili"
fi

# Disco
DISK_PCT=$(df / | awk 'NR==2{print $5}' | tr -d '%')
if [ "$DISK_PCT" -lt 80 ]; then
    ok "Disco root: ${DISK_PCT}% usato"
elif [ "$DISK_PCT" -lt 90 ]; then
    warn "Disco root: ${DISK_PCT}% usato (soglia: 80%)"
else
    err "Disco root: ${DISK_PCT}% usato — CRITICO"
fi

echo ""
echo "================================================="
echo " FINE DIAGNOSTICA"
echo "================================================="
```

**Installazione e test:**

```bash
sudo cp /tmp/lab_full_diagnostic.sh /opt/lab-scripts/
sudo chmod +x /opt/lab-scripts/lab_full_diagnostic.sh
/opt/lab-scripts/lab_full_diagnostic.sh
```

---

### Progetto C3: Connessione ITIL — Il Troubleshooting nelle Pratiche ITIL v4

**Troubleshooting come pratica integrata:**

Il troubleshooting non è una pratica ITIL a sé, ma trasversale a tutte:

| Pratica ITIL | Ruolo del Troubleshooting |
|---|---|
| **Incident Management** | Il Framework 6-Step IS il processo di risoluzione degli incidenti |
| **Problem Management** | La Root Cause Analysis (RCA) è il troubleshooting portato a termine |
| **Knowledge Management** | Gli articoli KB nascono dai problemi risolti con il troubleshooting |
| **Monitoring & Event Management** | Il monitoring rileva i sintomi che avviano il troubleshooting |
| **Service Continuity** | Troubleshooting rapido riduce il MTTR e migliora RTO |

**Il ciclo virtuoso:**

```
Symptom rilevato (monitoring)
    ↓
Incident aperto (GLPI)
    ↓
Troubleshooting (Framework 6-Step)
    ↓
Risoluzione documentata (ticket chiuso)
    ↓
Pattern ricorrente? → Problem ticket → RCA → Fix permanente
    ↓
Knowledge Base aggiornata
    ↓
Prossimo incidente simile: 5 minuti invece di 2 ore
```

---

## Checklist di Validazione — Tutorial ops11a Completato

### Fondamenti (Part A)
- [ ] Sai elencare le 6 fasi del Framework di Troubleshooting nell'ordine corretto
- [ ] Sai formulare le 5 domande fondamentali da fare a un utente che segnala un problema
- [ ] Sai elencare i 7 layer OSI e associare a ciascuno almeno uno strumento diagnostico
- [ ] Sai diagnosticare i 4 tipi di collo di bottiglia (CPU, RAM, Disco, Rete)
- [ ] Sai distinguere un problema DNS da un problema di routing (ping IP vs ping nome)

### Operazioni (Part B)
- [ ] B1: Framework 6-Step applicato per il problema hosts file — documentazione scritta
- [ ] B2: `dig`, `nc -zv`, `ss -tlnp`, `traceroute` eseguiti e output interpretato
- [ ] B2: `tcpdump` cattura avviata e analisi di base eseguita
- [ ] B3: `stress-ng` avviato, impatto su CPU e load average osservato
- [ ] B3: `top`, `ps aux --sort=-%cpu`, `vmstat`, `iostat` eseguiti durante il carico
- [ ] B4: Record SRV DNS per Active Directory verificati correttamente
- [ ] B5: Scenario complesso affrontato con Framework 6-Step — documentazione completa

### Governance (Part C)
- [ ] Template articolo KB scritto per almeno un problema del lab
- [ ] Script `lab_full_diagnostic.sh` eseguito con tutti i check verdi
- [ ] Sai spiegare come il troubleshooting si integra con Incident, Problem e Knowledge Management ITIL

---

## Appendice A: Cheat Sheet Comandi Troubleshooting

### Windows
```powershell
# Rete
ipconfig /all                                           # Config completa
Test-NetConnection -ComputerName IP -Port PORTA         # Test porta TCP
Resolve-DnsName nome.dominio                            # Test DNS
tracert IP                                              # Percorso hop-by-hop
ping IP -n 4                                            # Test ICMP
netstat -ano | findstr :PORTA                           # Processo su porta
arp -a                                                  # Cache ARP
route print                                             # Routing table
ipconfig /flushdns                                      # Svuota cache DNS

# Performance
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
Get-Counter "\Processor(_Total)\% Processor Time"
Get-Counter "\Memory\Available MBytes"
Get-Counter "\PhysicalDisk(_Total)\Avg. Disk Queue Length"

# Servizi
Get-Service ServiceName | Select Status, StartType
Start-Service ServiceName
Restart-Service ServiceName
Get-EventLog -LogName System -Newest 20 -EntryType Error
```

### Linux
```bash
# Rete
ip addr show                  # Interfacce e IP
ip route show                 # Routing table
ping -c 4 IP                  # Test ICMP
traceroute IP                 # Hop-by-hop
dig @DNS nome                 # DNS test avanzato
nc -zv IP PORTA               # Test porta TCP
ss -tlnp                      # Porte in ascolto
ss -tunp                      # Tutte le connessioni
tcpdump -i eth0 -n port 80    # Cattura traffico

# Performance
top                           # Monitor interattivo
ps aux --sort=-%cpu | head    # Processi per CPU
free -h                       # RAM e swap
vmstat 1 5                    # CPU+RAM+IO ogni 1 sec
iostat -x 1 3                 # I/O disco
df -h                         # Spazio disco
du -sh /var/* | sort -rh      # Uso per directory

# Servizi
systemctl status nome.service
journalctl -u nome -n 50
systemctl --failed
```

---

## Riferimenti

| Risorsa | Posizione | Contenuto |
|---|---|---|
| Documento sorgente | `../11-troubleshooting-generale.md` (sez. 1-4) | Metodologia e diagnostica |
| Tutorial ops11b | `tutorial_ops11_ch1b_performance_auth_storage_lab.md` | Troubleshooting avanzato: Performance, Auth, Storage, RCA |
| Tutorial ops01b | `tutorial_ops01_ch1b_incident_problem_change_lab.md` | Incident/Problem ITIL (prerequisito) |
| RFC 793 (TCP) | tools.ietf.org/html/rfc793 | Specifiche TCP — utile per Wireshark |
| OSI Model | wikipedia.org/wiki/OSI_model | Referenza completa livelli OSI |

---

*Fine tutorial ops11a — Prossimo: `tutorial_ops11_ch1b_performance_auth_storage_lab.md`*
