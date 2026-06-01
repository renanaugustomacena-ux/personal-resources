---
corso: "Programmazione Python"
fase: "4 — Applicazioni Specializzate"
modulo: "17"
titolo: "Network Programming"
versione: "socket (stdlib) / httpx 0.27+ / dnspython 2.6+ / paramiko 3.x / grpcio 1.64+ / scapy 2.5+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01-06 — Python Base"
  - "10 — Programmazione Asincrona"
  - "07 — Error Handling e Logging"
obiettivi:
  - "Programmare socket TCP/UDP e comprendere il modello client-server"
  - "Utilizzare httpx per client HTTP/2 sincroni e asincroni"
  - "Implementare comunicazione gRPC con protobuf"
  - "Gestire DNS, SSH e protocolli di rete con librerie specializzate"
  - "Analizzare traffico di rete con scapy per security e debugging"
  - "Costruire server concorrenti con asyncio e selectors"
tag: [network, socket, httpx, gRPC, protobuf, DNS, scapy, paramiko, asyncio]
---

# Network Programming — Guida Completa

> **Modulo 17** · **Aggiornamento:** 2026-05-24 · **Versione:** socket (stdlib) / httpx 0.27+ / dnspython 2.6+ / paramiko 3.x / grpcio 1.64+ / scapy 2.5+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [Programmazione Asincrona](10-programmazione-asincrona.md), [Error Handling](07-error-handling-e-logging.md)
>
> Al termine di questo modulo saprai:
> 1. Programmare socket TCP/UDP e comprendere il modello client-server
> 2. Utilizzare httpx per client HTTP/2 sincroni e asincroni
> 3. Implementare comunicazione gRPC con protobuf
> 4. Gestire DNS, SSH e protocolli di rete con librerie specializzate
> 5. Analizzare traffico di rete con scapy per security e debugging
> 6. Costruire server concorrenti con asyncio e selectors
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **`asyncio` networking > raw socket per concurrency.**
2. **`websockets` library standard.**
3. **`scapy` per packet manipulation low-level.**
4. **TLS via `ssl` module + `cryptography` library.**

### Mappa concettuale

```
                        ┌─────────────────────┐
                        │ NETWORK PROGRAMMING  │
                        └──────────┬──────────┘
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
 ┌─────────────────┐     ┌─────────────────┐      ┌─────────────────┐
 │  Livello 4       │     │  Livello 7       │      │  Sicurezza      │
 │  TCP / UDP       │     │  HTTP/2 (httpx)  │      │  TLS / mTLS     │
 │  socket (stdlib) │     │  gRPC (grpcio)   │      │  ssl + crypto   │
 │  asyncio.streams │     │  WebSocket       │      │  certificati    │
 └────────┬────────┘     └────────┬────────┘      └────────┬────────┘
          │                       │                        │
          ▼                       ▼                        ▼
 ┌─────────────────┐     ┌─────────────────┐      ┌─────────────────┐
 │  Protocolli       │     │  Monitoraggio    │      │  Scanning       │
 │  DNS (dnspython) │     │  Ping / Port     │      │  scapy          │
 │  SMTP / IMAP     │     │  Health Check    │      │  python-nmap    │
 │  SSH (paramiko)  │     │  SNMP (pysnmp)   │      │  discovery      │
 └─────────────────┘     └─────────────────┘      └─────────────────┘
```


## Indice

1. [Panoramica](#panoramica)
   - [Fondamenti del Network Programming](#fondamenti-del-network-programming)
   - [Modello OSI — Riepilogo](#modello-osi--riepilogo)
   - [TCP vs UDP](#tcp-vs-udp)
2. [Socket Programming](#socket-programming)
   - [TCP Socket](#tcp-socket)
   - [UDP Socket](#udp-socket)
   - [Socket Avanzato](#socket-avanzato)
3. [HTTP Client](#http-client)
   - [urllib](#urllib)
   - [requests](#requests)
   - [httpx](#httpx)
   - [Confronto Client HTTP Python](#confronto-client-http-python)
   - [aiohttp — Client e Server HTTP Asincrono](#aiohttp--client-e-server-http-asincrono)
4. [SNMP](#snmp)
   - [pysnmp](#pysnmp)
5. [DNS](#dns)
   - [dnspython](#dnspython)
6. [SSH/SFTP](#sshsftp)
   - [paramiko](#paramiko)
   - [asyncssh](#asyncssh)
   - [Fabric — Automazione SSH ad Alto Livello](#fabric--automazione-ssh-ad-alto-livello)
7. [Email Protocols](#email-protocols)
   - [SMTP (smtplib)](#smtp-smtplib)
   - [IMAP (imaplib)](#imap-imaplib)
   - [POP3 (poplib)](#pop3-poplib)
8. [Network Scanning e Discovery](#network-scanning-e-discovery)
   - [scapy](#scapy)
   - [python-nmap](#python-nmap)
9. [WebSocket Programming](#websocket-programming)
   - [websockets — Server e Client](#websockets--server-e-client)
   - [python-socketio — Socket.IO per Python](#python-socketio--socketio-per-python)
10. [Analisi Pacchetti e Parsing PCAP](#analisi-pacchetti-e-parsing-pcap)
    - [pyshark — Analisi pcap con Wireshark/tshark](#pyshark--analisi-pcap-con-wiresharktshark)
    - [dpkt — Parsing pcap leggero](#dpkt--parsing-pcap-leggero)
    - [scapy per analisi offline](#scapy-per-analisi-offline)
11. [FTP e FTPS Automation](#ftp-e-ftps-automation)
    - [ftplib — Client FTP/FTPS](#ftplib--client-ftpftps)
12. [Network Monitoring](#network-monitoring)
    - [Ping Monitoring](#ping-monitoring)
    - [Port Monitoring](#port-monitoring)
    - [Service Health Checks](#service-health-checks)
    - [Bandwidth Monitoring](#bandwidth-monitoring)
    - [Alert Integration](#alert-integration)
13. [Best Practices](#best-practices)
14. [asyncio.streams — Networking Asincrono](#asynciostreams--networking-asincrono)
15. [HTTP/2 con httpx e h2](#http2-con-httpx-e-h2)
16. [gRPC con grpcio e Protocol Buffers](#grpc-con-grpcio-e-protocol-buffers)
    - [gRPC Asincrono con grpc.aio](#grpc-asincrono-con-grpcaio)
    - [gRPC Bidirectional Streaming](#grpc-bidirectional-streaming)
    - [Interceptor gRPC per Logging e Autenticazione](#interceptor-grpc-per-logging-e-autenticazione)
17. [mTLS — Mutual TLS con cryptography](#mtls--mutual-tls-con-cryptography)
    - [Ispezione Certificati TLS Remoti](#ispezione-certificati-tls-remoti)
18. [DNS Avanzato — DNSSEC e DoH](#dns-avanzato--dnssec-e-doh)
19. [FAQ](#faq)
20. [Esercizi](#esercizi)
21. [Letture](#letture)
22. [Glossario](#glossario)

---

## Panoramica

Il network programming rappresenta una delle competenze fondamentali per qualsiasi sviluppatore Python che operi in ambito sistemistico, DevOps o backend. Python offre un ecosistema straordinariamente ricco per interagire con la rete a ogni livello dello stack: dai socket grezzi a basso livello fino alle librerie HTTP ad alto livello, passando per protocolli specializzati come SNMP, DNS, SSH e SMTP.

Questa guida copre l'intero spettro della programmazione di rete in Python, partendo dalle basi dei socket fino ad arrivare a scenari avanzati di monitoraggio e scansione di rete. Ogni sezione include esempi pratici e completi, pronti per essere adattati a contesti reali.

### Fondamenti del Network Programming

La comunicazione di rete si basa su un principio semplice: due programmi, in esecuzione su macchine diverse (o sulla stessa macchina), scambiano dati attraverso un canale di comunicazione. Ogni partecipante e identificato da un indirizzo IP e un numero di porta. L'indirizzo IP identifica la macchina nella rete, mentre la porta identifica il servizio specifico su quella macchina.

```python
import socket

# Ottenere informazioni di rete della macchina locale
hostname = socket.gethostname()
ip_locale = socket.gethostbyname(hostname)
print(f"Hostname: {hostname}")
print(f"IP locale: {ip_locale}")

# Risolvere un hostname remoto
ip_remoto = socket.gethostbyname("www.python.org")
print(f"IP di python.org: {ip_remoto}")

# Ottenere tutte le informazioni di indirizzo
info = socket.getaddrinfo("www.python.org", 443, socket.AF_INET, socket.SOCK_STREAM)
for famiglia, tipo, proto, canonname, indirizzo in info:
    print(f"  {indirizzo[0]}:{indirizzo[1]} (famiglia={famiglia}, tipo={tipo})")
```

### Modello OSI — Riepilogo

Il modello OSI (Open Systems Interconnection) suddivide la comunicazione di rete in sette livelli. Per il network programming in Python, ci concentriamo principalmente sui livelli superiori:

| Livello | Nome          | Protocolli Comuni    | Rilevanza Python           |
|---------|---------------|----------------------|----------------------------|
| 7       | Applicazione  | HTTP, SMTP, DNS, SSH | requests, smtplib, paramiko|
| 6       | Presentazione | TLS/SSL, MIME        | ssl, email                 |
| 5       | Sessione      | NetBIOS, RPC         | xmlrpc, jsonrpc            |
| 4       | Trasporto     | TCP, UDP             | socket                     |
| 3       | Rete          | IP, ICMP, ARP        | scapy, icmplib             |
| 2       | Data Link     | Ethernet, Wi-Fi      | scapy (raw sockets)        |
| 1       | Fisico        | Cavi, segnali        | Non gestito via software   |

La maggior parte del lavoro quotidiano si svolge ai livelli 4-7. I socket operano al livello 4 (trasporto), mentre librerie come `requests` operano al livello 7 (applicazione).

### TCP vs UDP

I due protocolli di trasporto principali sono TCP e UDP, con caratteristiche profondamente diverse.

**TCP (Transmission Control Protocol)** garantisce la consegna affidabile e ordinata dei dati. Stabilisce una connessione prima del trasferimento (three-way handshake), conferma ogni pacchetto ricevuto e ritrasmette i pacchetti persi. E il protocollo ideale per HTTP, SSH, email e qualsiasi scenario in cui la perdita di dati non e accettabile.

**UDP (User Datagram Protocol)** e un protocollo senza connessione (connectionless). Non garantisce la consegna ne l'ordine dei pacchetti, ma offre latenza inferiore e overhead minimo. E ideale per streaming video/audio, DNS, giochi online e scenari dove la velocita conta piu della completezza.

```python
import socket

# Socket TCP — orientato alla connessione
sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Socket UDP — senza connessione
sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
```

---

## Socket Programming

Il modulo `socket` della libreria standard di Python fornisce accesso diretto all'interfaccia socket BSD, il meccanismo fondamentale per la comunicazione di rete in tutti i sistemi operativi moderni.

### TCP Socket

Un'applicazione TCP si compone di due ruoli: il **server** che ascolta le connessioni in arrivo e il **client** che si connette al server.

**Ciclo di vita del server TCP:**

1. `socket()` — Crea il socket
2. `bind()` — Associa il socket a un indirizzo e porta
3. `listen()` — Mette il socket in ascolto
4. `accept()` — Accetta una connessione in arrivo
5. `recv()`/`send()` — Scambia dati
6. `close()` — Chiude la connessione

**Ciclo di vita del client TCP:**

1. `socket()` — Crea il socket
2. `connect()` — Si connette al server
3. `send()`/`recv()` — Scambia dati
4. `close()` — Chiude la connessione

#### Echo Server completo

```python
import socket
import threading


def gestisci_client(conn, indirizzo):
    """Gestisce un singolo client in un thread separato."""
    print(f"[CONNESSIONE] {indirizzo} connesso")
    with conn:
        while True:
            dati = conn.recv(4096)
            if not dati:
                break
            messaggio = dati.decode("utf-8")
            print(f"[{indirizzo}] Ricevuto: {messaggio}")
            # Echo: rimanda lo stesso messaggio al client
            conn.sendall(dati)
    print(f"[DISCONNESSIONE] {indirizzo} disconnesso")


def avvia_server(host="127.0.0.1", porta=9000):
    """Avvia un echo server TCP multi-client."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        # SO_REUSEADDR permette di riutilizzare la porta immediatamente
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, porta))
        server.listen(5)
        print(f"[SERVER] In ascolto su {host}:{porta}")

        while True:
            conn, indirizzo = server.accept()
            thread = threading.Thread(
                target=gestisci_client,
                args=(conn, indirizzo),
                daemon=True
            )
            thread.start()
            print(f"[SERVER] Connessioni attive: {threading.active_count() - 1}")


if __name__ == "__main__":
    avvia_server()
```

#### Echo Client

```python
import socket


def avvia_client(host="127.0.0.1", porta=9000):
    """Client che invia messaggi e riceve l'echo dal server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, porta))
        print(f"Connesso a {host}:{porta}")
        print("Digita un messaggio (o 'esci' per uscire):")

        while True:
            messaggio = input("> ")
            if messaggio.lower() == "esci":
                break
            client.sendall(messaggio.encode("utf-8"))
            risposta = client.recv(4096)
            print(f"Echo: {risposta.decode('utf-8')}")


if __name__ == "__main__":
    avvia_client()
```

#### Uso del Context Manager

L'uso di `with` garantisce che il socket venga sempre chiuso correttamente, anche in caso di eccezioni. E la pratica raccomandata per ogni operazione con i socket.

```python
import socket

# Il context manager chiude automaticamente il socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(10.0)  # Timeout di 10 secondi
    s.connect(("httpbin.org", 80))
    richiesta = "GET /get HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n"
    s.sendall(richiesta.encode())

    risposta = b""
    while True:
        blocco = s.recv(4096)
        if not blocco:
            break
        risposta += blocco

    print(risposta.decode("utf-8"))
# Socket automaticamente chiuso qui
```

### UDP Socket

A differenza di TCP, con UDP non c'e una connessione da stabilire. I datagrammi vengono inviati e ricevuti in modo indipendente.

#### Server UDP

```python
import socket


def server_udp(host="127.0.0.1", porta=9001):
    """Server UDP che riceve datagrammi e risponde."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((host, porta))
        print(f"[UDP SERVER] In ascolto su {host}:{porta}")

        while True:
            dati, indirizzo = server.recvfrom(4096)
            messaggio = dati.decode("utf-8")
            print(f"[{indirizzo}] Ricevuto: {messaggio}")
            risposta = f"ECHO: {messaggio}"
            server.sendto(risposta.encode("utf-8"), indirizzo)


if __name__ == "__main__":
    server_udp()
```

#### Client UDP

```python
import socket


def client_udp(host="127.0.0.1", porta=9001):
    """Client UDP che invia datagrammi."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        while True:
            messaggio = input("> ")
            if messaggio.lower() == "esci":
                break
            client.sendto(messaggio.encode("utf-8"), (host, porta))
            dati, _ = client.recvfrom(4096)
            print(f"Risposta: {dati.decode('utf-8')}")


if __name__ == "__main__":
    client_udp()
```

#### UDP Broadcast

Il broadcast permette di inviare un messaggio a tutti i dispositivi nella rete locale.

```python
import socket


def invia_broadcast(messaggio, porta=9999):
    """Invia un messaggio broadcast sulla rete locale."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(messaggio.encode("utf-8"), ("<broadcast>", porta))
        print(f"Broadcast inviato sulla porta {porta}")


def ascolta_broadcast(porta=9999):
    """Ascolta messaggi broadcast sulla porta specificata."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", porta))
        print(f"In ascolto per broadcast sulla porta {porta}")
        while True:
            dati, indirizzo = s.recvfrom(4096)
            print(f"Broadcast da {indirizzo}: {dati.decode('utf-8')}")
```

### Socket Avanzato

#### Non-blocking Sockets e select

I socket non bloccanti permettono di gestire multiple connessioni senza threading.

```python
import socket
import select


def server_select(host="127.0.0.1", porta=9002):
    """Server che usa select() per gestire piu client senza threading."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(False)
    server.bind((host, porta))
    server.listen(5)

    # Lista dei socket da monitorare in lettura
    input_sockets = [server]
    # Dizionario per i messaggi in uscita
    messaggi_in_uscita = {}

    print(f"[SELECT SERVER] In ascolto su {host}:{porta}")

    while input_sockets:
        leggibili, scrivibili, errori = select.select(
            input_sockets, list(messaggi_in_uscita.keys()), input_sockets, 1.0
        )

        for s in leggibili:
            if s is server:
                conn, indirizzo = s.accept()
                conn.setblocking(False)
                input_sockets.append(conn)
                messaggi_in_uscita[conn] = []
                print(f"Nuova connessione da {indirizzo}")
            else:
                dati = s.recv(4096)
                if dati:
                    messaggi_in_uscita[s].append(dati)
                else:
                    if s in messaggi_in_uscita:
                        del messaggi_in_uscita[s]
                    input_sockets.remove(s)
                    s.close()

        for s in scrivibili:
            if messaggi_in_uscita.get(s):
                msg = messaggi_in_uscita[s].pop(0)
                s.send(msg)

        for s in errori:
            input_sockets.remove(s)
            if s in messaggi_in_uscita:
                del messaggi_in_uscita[s]
            s.close()
```

#### Opzioni Socket Avanzate

Le opzioni socket (`setsockopt`) permettono di controllare finemente il comportamento della connessione a livello di kernel.

```python
import socket
import struct


def configura_socket_produzione(sock: socket.socket):
    """Configura un socket con opzioni ottimali per ambienti di produzione."""

    # --- SO_REUSEADDR ---
    # Permette di riutilizzare una porta immediatamente dopo la chiusura,
    # evitando l'errore "Address already in use" durante i restart del server.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # --- SO_KEEPALIVE ---
    # Abilita i pacchetti keep-alive TCP per rilevare connessioni morte.
    # Senza keepalive, un client che si disconnette bruscamente (crash, rete down)
    # lascia il socket del server bloccato indefinitamente.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    # Su Linux, parametri granulari per il keepalive:
    # Tempo di inattivita prima del primo probe (secondi)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
    # Intervallo tra i probe successivi (secondi)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
    # Numero massimo di probe prima di chiudere la connessione
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

    # --- TCP_NODELAY ---
    # Disabilita l'algoritmo di Nagle che raggruppa i piccoli pacchetti.
    # Riduce la latenza per protocolli interattivi (chat, gaming, telemetria).
    # Trade-off: maggiore overhead di rete per pacchetti piccoli.
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    # --- SO_RCVBUF / SO_SNDBUF ---
    # Aumenta i buffer di ricezione e invio del kernel.
    # Utile per connessioni ad alta latenza o ad alto throughput.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 256 * 1024)  # 256 KB
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 256 * 1024)  # 256 KB

    return sock


def configura_socket_linger(sock: socket.socket, abilitato: bool, timeout: int = 0):
    """Configura il comportamento di chiusura del socket con SO_LINGER.

    - abilitato=False: chiusura normale (default), i dati in coda vengono inviati.
    - abilitato=True, timeout=0: chiusura immediata con RST, dati non inviati persi.
    - abilitato=True, timeout>0: close() blocca fino a N secondi per inviare i dati.
    """
    valore = struct.pack("ii", int(abilitato), timeout)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, valore)


def mostra_opzioni_socket(sock: socket.socket):
    """Stampa le opzioni correnti di un socket."""
    opzioni = {
        "SO_REUSEADDR": (socket.SOL_SOCKET, socket.SO_REUSEADDR),
        "SO_KEEPALIVE": (socket.SOL_SOCKET, socket.SO_KEEPALIVE),
        "SO_RCVBUF": (socket.SOL_SOCKET, socket.SO_RCVBUF),
        "SO_SNDBUF": (socket.SOL_SOCKET, socket.SO_SNDBUF),
        "TCP_NODELAY": (socket.IPPROTO_TCP, socket.TCP_NODELAY),
    }

    print("Opzioni socket:")
    for nome, (livello, opzione) in opzioni.items():
        try:
            valore = sock.getsockopt(livello, opzione)
            print(f"  {nome}: {valore}")
        except OSError:
            print(f"  {nome}: non disponibile")
```

#### selectors — I/O Multiplexing ad Alte Prestazioni

Il modulo `selectors` fornisce un'API ad alto livello per l'I/O multiplexing, selezionando automaticamente il meccanismo piu efficiente disponibile sul sistema operativo (`epoll` su Linux, `kqueue` su macOS/BSD, `select` come fallback). E preferibile a `select.select()` per server di produzione perche `epoll`/`kqueue` scalano a O(1) con il numero di file descriptor, mentre `select()` scala a O(n).

```python
import selectors
import socket
import types

# DefaultSelector sceglie automaticamente epoll/kqueue/select
sel = selectors.DefaultSelector()


def avvia_server_selectors(host: str = "127.0.0.1", porta: int = 9010):
    """Server TCP ad alte prestazioni con selectors (epoll su Linux)."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(False)
    server.bind((host, porta))
    server.listen(100)

    # Registra il socket del server per lettura (nuove connessioni)
    sel.register(server, selectors.EVENT_READ, data=None)
    print(f"[SELECTORS] Server su {host}:{porta} "
          f"(backend: {type(sel).__name__})")

    try:
        while True:
            # Attende eventi I/O (timeout opzionale)
            eventi = sel.select(timeout=None)
            for chiave, maschera in eventi:
                if chiave.data is None:
                    # Evento sul server socket: nuova connessione
                    _accetta_connessione(chiave.fileobj)
                else:
                    # Evento su un client socket: dati disponibili
                    _gestisci_evento(chiave, maschera)
    except KeyboardInterrupt:
        print("\nServer interrotto")
    finally:
        sel.close()


def _accetta_connessione(server_sock: socket.socket):
    """Accetta una nuova connessione e la registra nel selector."""
    conn, addr = server_sock.accept()
    conn.setblocking(False)

    # Dati associati alla connessione
    dati = types.SimpleNamespace(
        addr=addr,
        buffer_in=b"",
        buffer_out=b"",
    )

    # Registra per lettura E scrittura
    eventi = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, eventi, data=dati)
    print(f"  Connessione accettata da {addr}")


def _gestisci_evento(chiave: selectors.SelectorKey, maschera: int):
    """Gestisce gli eventi di lettura/scrittura su un socket client."""
    sock = chiave.fileobj
    dati = chiave.data

    if maschera & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(4096)
        except ConnectionResetError:
            recv_data = b""

        if recv_data:
            # Echo: prepara la risposta nel buffer di uscita
            dati.buffer_out += recv_data
        else:
            # Client disconnesso
            print(f"  Disconnessione da {dati.addr}")
            sel.unregister(sock)
            sock.close()
            return

    if maschera & selectors.EVENT_WRITE:
        if dati.buffer_out:
            inviati = sock.send(dati.buffer_out)
            dati.buffer_out = dati.buffer_out[inviati:]


# avvia_server_selectors()
```

#### socketserver Module

Il modulo `socketserver` semplifica la creazione di server fornendo classi base pronte all'uso.

```python
import socketserver


class GestoreEcho(socketserver.BaseRequestHandler):
    """Handler per ogni connessione in arrivo."""

    def handle(self):
        print(f"Connessione da {self.client_address}")
        while True:
            dati = self.request.recv(4096)
            if not dati:
                break
            self.request.sendall(dati)
        print(f"Disconnessione di {self.client_address}")


class ServerThreaded(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Server TCP multi-threaded."""
    allow_reuse_address = True
    daemon_threads = True


# Avvio del server
with ServerThreaded(("127.0.0.1", 9003), GestoreEcho) as server:
    print("Server threaded in ascolto sulla porta 9003")
    server.serve_forever()
```

#### asyncio Streams

Per applicazioni ad alte prestazioni, `asyncio` offre un'API elegante basata su stream.

```python
import asyncio


async def gestisci_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Gestisce un client con asyncio streams."""
    indirizzo = writer.get_extra_info("peername")
    print(f"[CONNESSIONE] {indirizzo}")

    while True:
        dati = await reader.read(4096)
        if not dati:
            break
        messaggio = dati.decode("utf-8")
        print(f"[{indirizzo}] {messaggio}")
        writer.write(dati)
        await writer.drain()

    print(f"[DISCONNESSIONE] {indirizzo}")
    writer.close()
    await writer.wait_closed()


async def main():
    server = await asyncio.start_server(gestisci_client, "127.0.0.1", 9004)
    indirizzo = server.sockets[0].getsockname()
    print(f"[ASYNCIO SERVER] In ascolto su {indirizzo}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## HTTP Client

La comunicazione HTTP e il pilastro delle applicazioni web moderne. Python offre diverse librerie, dalla standard library fino a librerie di terze parti estremamente potenti.

### urllib

`urllib` fa parte della libreria standard e non richiede installazioni aggiuntive.

```python
from urllib.request import urlopen, Request
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.error import HTTPError, URLError
import json

# --- GET semplice ---
with urlopen("https://httpbin.org/get") as risposta:
    corpo = risposta.read().decode("utf-8")
    dati = json.loads(corpo)
    print(f"Status: {risposta.status}")
    print(f"IP origine: {dati['origin']}")

# --- GET con headers personalizzati ---
req = Request(
    "https://httpbin.org/get",
    headers={
        "User-Agent": "PythonBot/1.0",
        "Accept": "application/json",
    }
)
with urlopen(req) as risposta:
    print(json.loads(risposta.read()))

# --- POST con dati ---
parametri = urlencode({"nome": "Mario", "citta": "Roma"}).encode("utf-8")
req = Request("https://httpbin.org/post", data=parametri, method="POST")
with urlopen(req) as risposta:
    print(json.loads(risposta.read()))

# --- Parsing URL ---
url = "https://example.com/search?q=python&page=2&lang=it"
parti = urlparse(url)
print(f"Schema: {parti.scheme}")      # https
print(f"Host: {parti.netloc}")         # example.com
print(f"Path: {parti.path}")           # /search
print(f"Query: {parse_qs(parti.query)}")  # {'q': ['python'], 'page': ['2'], ...}

# --- Gestione errori ---
try:
    with urlopen("https://httpbin.org/status/404") as r:
        print(r.read())
except HTTPError as e:
    print(f"Errore HTTP: {e.code} {e.reason}")
except URLError as e:
    print(f"Errore URL: {e.reason}")
```

### requests

La libreria `requests` e lo standard de facto per le richieste HTTP in Python. Offre un'API intuitiva e potente.

```bash
pip install requests
```

#### Operazioni CRUD complete

```python
import requests

BASE_URL = "https://httpbin.org"

# --- GET ---
risposta = requests.get(
    f"{BASE_URL}/get",
    params={"chiave": "valore", "lingua": "it"},
    headers={"Accept": "application/json"},
    timeout=10
)
print(f"Status: {risposta.status_code}")
print(f"JSON: {risposta.json()}")
print(f"Headers risposta: {dict(risposta.headers)}")

# --- POST con JSON ---
risposta = requests.post(
    f"{BASE_URL}/post",
    json={"nome": "Maria", "ruolo": "admin"},
    timeout=10
)
print(risposta.json())

# --- POST con form data ---
risposta = requests.post(
    f"{BASE_URL}/post",
    data={"campo1": "valore1", "campo2": "valore2"},
    timeout=10
)

# --- PUT ---
risposta = requests.put(
    f"{BASE_URL}/put",
    json={"id": 1, "nome": "Nome Aggiornato"},
    timeout=10
)

# --- DELETE ---
risposta = requests.delete(f"{BASE_URL}/delete", timeout=10)
print(f"Eliminazione: {risposta.status_code}")
```

#### Sessioni, Cookie e Autenticazione

```python
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

# --- Sessione (mantiene cookie e headers tra le richieste) ---
with requests.Session() as sessione:
    sessione.headers.update({"User-Agent": "MioBot/2.0"})

    # Login (i cookie vengono salvati automaticamente)
    sessione.post("https://httpbin.org/cookies/set/session_id/abc123")

    # Richiesta successiva (include i cookie della sessione)
    risposta = sessione.get("https://httpbin.org/cookies")
    print(f"Cookie: {risposta.json()}")

# --- Autenticazione Basic ---
risposta = requests.get(
    "https://httpbin.org/basic-auth/utente/password",
    auth=HTTPBasicAuth("utente", "password"),
    timeout=10
)
print(f"Auth Basic: {risposta.status_code}")

# --- Autenticazione Digest ---
risposta = requests.get(
    "https://httpbin.org/digest-auth/auth/utente/password",
    auth=HTTPDigestAuth("utente", "password"),
    timeout=10
)

# --- Autenticazione con token Bearer ---
headers = {"Authorization": "Bearer il_mio_token_jwt_qui"}
risposta = requests.get(
    "https://api.esempio.com/dati",
    headers=headers,
    timeout=10
)
```

#### Upload e Download di File

```python
import requests

# --- Upload file ---
with open("documento.pdf", "rb") as f:
    risposta = requests.post(
        "https://httpbin.org/post",
        files={"file": ("documento.pdf", f, "application/pdf")},
        timeout=30
    )

# Upload multiplo
file_multipli = [
    ("files", ("file1.txt", open("file1.txt", "rb"), "text/plain")),
    ("files", ("file2.txt", open("file2.txt", "rb"), "text/plain")),
]
risposta = requests.post("https://httpbin.org/post", files=file_multipli, timeout=30)

# --- Download file con streaming ---
url = "https://speed.hetzner.de/100MB.bin"
with requests.get(url, stream=True, timeout=30) as r:
    r.raise_for_status()
    dimensione_totale = int(r.headers.get("Content-Length", 0))
    scaricati = 0
    with open("file_scaricato.bin", "wb") as f:
        for blocco in r.iter_content(chunk_size=8192):
            f.write(blocco)
            scaricati += len(blocco)
            if dimensione_totale:
                percentuale = (scaricati / dimensione_totale) * 100
                print(f"\rProgresso: {percentuale:.1f}%", end="", flush=True)
    print("\nDownload completato!")
```

#### Retry con urllib3

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def crea_sessione_resiliente(
    tentativi=3,
    backoff_factor=0.5,
    status_forcelist=(500, 502, 503, 504),
):
    """Crea una sessione HTTP con retry automatico."""
    sessione = requests.Session()

    strategia_retry = Retry(
        total=tentativi,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST", "PUT", "DELETE"],
    )

    adapter = HTTPAdapter(max_retries=strategia_retry)
    sessione.mount("http://", adapter)
    sessione.mount("https://", adapter)

    return sessione


# Uso: la sessione ritenta automaticamente in caso di errori 5xx
sessione = crea_sessione_resiliente()
risposta = sessione.get("https://httpbin.org/get", timeout=10)
print(risposta.json())
```

### httpx

`httpx` e l'evoluzione moderna di `requests`, con supporto nativo per async e HTTP/2.

```bash
pip install httpx[http2]
```

#### Client Sincrono e Asincrono

```python
import httpx
import asyncio

# --- Client sincrono ---
with httpx.Client(http2=True, timeout=10.0) as client:
    risposta = client.get("https://httpbin.org/get")
    print(f"HTTP versione: {risposta.http_version}")
    print(f"Status: {risposta.status_code}")

# --- Client asincrono ---
async def richieste_parallele():
    async with httpx.AsyncClient(http2=True) as client:
        urls = [
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
        ]
        compiti = [client.get(url) for url in urls]
        risposte = await asyncio.gather(*compiti)
        for r in risposte:
            print(f"{r.url} -> {r.status_code}")


asyncio.run(richieste_parallele())

# --- Configurazione avanzata ---
client = httpx.Client(
    base_url="https://api.esempio.com",
    headers={"Authorization": "Bearer token123"},
    timeout=httpx.Timeout(
        connect=5.0,       # Timeout connessione
        read=30.0,         # Timeout lettura
        write=10.0,        # Timeout scrittura
        pool=5.0,          # Timeout pool connessioni
    ),
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20,
    ),
    follow_redirects=True,
)
```

### Confronto Client HTTP Python

La scelta del client HTTP dipende dal pattern di utilizzo, dai requisiti di concorrenza e dal supporto protocollare necessario.

| Caratteristica | `urllib` (stdlib) | `requests` | `httpx` | `aiohttp` | `urllib3` |
|----------------|:-----------------:|:----------:|:-------:|:---------:|:---------:|
| Parte della stdlib | Si | No | No | No | No |
| API intuitiva | No | Si | Si | Si | Parziale |
| Async nativo | No | No | Si | Si | No |
| HTTP/2 | No | No | Si | No | No |
| Streaming | Manuale | Si | Si | Si | Si |
| Connection pooling | No | Si (session) | Si | Si | Si |
| Timeout granulari | Basico | Basico | Si (4 livelli) | Si | Si |
| Retry integrato | No | Via adapter | Via transport | Manuale | Si |
| WebSocket | No | No | No | Si | No |
| Peso dipendenze | Zero | Medio | Medio | Medio | Leggero |

**Raccomandazione pratica:**
- **Nuovi progetti** → `httpx`: API compatibile con `requests`, supporto async e HTTP/2.
- **Progetti esistenti** → `requests`: ecosistema maturo, middleware e adapter di terze parti vastissimi.
- **Server asincroni** → `aiohttp`: se serve sia client sia server HTTP su asyncio nella stessa applicazione.
- **Basso livello / retry** → `urllib3`: quando si vuole controllo fine su pool, retry e trasporto senza l'overhead di un'API ad alto livello.
- **Zero dipendenze** → `urllib`: accettabile per script singoli dove installare librerie non e un'opzione.

### aiohttp — Client e Server HTTP Asincrono

`aiohttp` e l'alternativa storica ad `httpx` nel mondo asyncio. Il suo punto di forza principale e la capacita di fungere sia da client sia da server HTTP, con supporto nativo per WebSocket, il che lo rende ideale per applicazioni che devono esporre endpoint HTTP e contemporaneamente chiamare API esterne.

```bash
pip install aiohttp
```

#### Client asincrono con aiohttp

```python
import aiohttp
import asyncio


async def demo_aiohttp_client():
    """Esempi di client HTTP asincrono con aiohttp."""

    # --- Session con connection pooling automatico ---
    connector = aiohttp.TCPConnector(
        limit=100,                 # Max connessioni totali
        limit_per_host=10,         # Max connessioni per host
        ttl_dns_cache=300,         # Cache DNS in secondi
        enable_cleanup_closed=True,
    )

    timeout = aiohttp.ClientTimeout(
        total=30,       # Timeout totale
        connect=5,      # Timeout connessione
        sock_read=10,   # Timeout lettura socket
    )

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={"User-Agent": "PythonClient/1.0"},
    ) as session:

        # GET semplice
        async with session.get("https://httpbin.org/get") as resp:
            print(f"Status: {resp.status}")
            dati = await resp.json()
            print(f"Origin: {dati['origin']}")

        # POST con JSON
        async with session.post(
            "https://httpbin.org/post",
            json={"chiave": "valore", "numero": 42},
        ) as resp:
            risultato = await resp.json()
            print(f"POST risposta: {risultato['json']}")

        # Richieste parallele (beneficio principale di async)
        urls = [f"https://httpbin.org/delay/{i}" for i in range(1, 4)]
        tasks = [session.get(url) for url in urls]
        risposte = await asyncio.gather(*tasks, return_exceptions=True)

        for resp in risposte:
            if isinstance(resp, Exception):
                print(f"Errore: {resp}")
            else:
                print(f"{resp.url} -> {resp.status}")
                resp.release()

        # Download streaming
        async with session.get("https://httpbin.org/bytes/1024") as resp:
            async for chunk in resp.content.iter_chunked(256):
                print(f"  Chunk: {len(chunk)} bytes")


asyncio.run(demo_aiohttp_client())
```

#### Server HTTP minimale con aiohttp

```python
from aiohttp import web
import json


async def handle_index(request: web.Request) -> web.Response:
    """Handler per la rotta principale."""
    return web.json_response({"stato": "attivo", "versione": "1.0"})


async def handle_echo(request: web.Request) -> web.Response:
    """Echo POST handler."""
    corpo = await request.json()
    return web.json_response({"echo": corpo})


async def handle_ws(request: web.Request) -> web.WebSocketResponse:
    """Handler WebSocket integrato nel server HTTP."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            await ws.send_str(f"Echo: {msg.data}")
        elif msg.type == web.WSMsgType.ERROR:
            print(f"WebSocket errore: {ws.exception()}")

    return ws


app = web.Application()
app.router.add_get("/", handle_index)
app.router.add_post("/echo", handle_echo)
app.router.add_get("/ws", handle_ws)

# web.run_app(app, host="0.0.0.0", port=8080)
```

---

## SNMP

SNMP (Simple Network Management Protocol) e il protocollo standard per il monitoraggio e la gestione di dispositivi di rete come switch, router, access point e server.

### pysnmp

```bash
pip install pysnmp-lextudio
```

#### SNMP GET, GETNEXT e GETBULK

```python
from pysnmp.hlapi import (
    getCmd, nextCmd, bulkCmd,
    SnmpEngine, CommunityData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity
)

# --- SNMP GET — Recupera un singolo OID ---
iterator = getCmd(
    SnmpEngine(),
    CommunityData("public"),                       # Community string
    UdpTransportTarget(("192.168.1.1", 161)),      # Dispositivo target
    ContextData(),
    ObjectType(ObjectIdentity("SNMPv2-MIB", "sysDescr", 0)),
    ObjectType(ObjectIdentity("SNMPv2-MIB", "sysUpTime", 0)),
)

errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

if errorIndication:
    print(f"Errore: {errorIndication}")
elif errorStatus:
    print(f"Errore SNMP: {errorStatus.prettyPrint()}")
else:
    for nome, valore in varBinds:
        print(f"{nome.prettyPrint()} = {valore.prettyPrint()}")

# --- SNMP GETNEXT — Recupera l'OID successivo ---
iterator = nextCmd(
    SnmpEngine(),
    CommunityData("public"),
    UdpTransportTarget(("192.168.1.1", 161)),
    ContextData(),
    ObjectType(ObjectIdentity("IF-MIB", "ifDescr")),
)

for errorIndication, errorStatus, errorIndex, varBinds in iterator:
    if errorIndication or errorStatus:
        break
    for nome, valore in varBinds:
        print(f"{nome.prettyPrint()} = {valore.prettyPrint()}")

# --- SNMP GETBULK — Recupero massivo (efficiente per tabelle) ---
iterator = bulkCmd(
    SnmpEngine(),
    CommunityData("public"),
    UdpTransportTarget(("192.168.1.1", 161)),
    ContextData(),
    0, 25,  # nonRepeaters=0, maxRepetitions=25
    ObjectType(ObjectIdentity("IF-MIB", "ifTable")),
)

for errorIndication, errorStatus, errorIndex, varBinds in iterator:
    if errorIndication or errorStatus:
        break
    for nome, valore in varBinds:
        print(f"{nome.prettyPrint()} = {valore.prettyPrint()}")
```

#### SNMP SET

```python
from pysnmp.hlapi import (
    setCmd, SnmpEngine, CommunityData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity, OctetString
)

# Modifica il sysContact del dispositivo
iterator = setCmd(
    SnmpEngine(),
    CommunityData("private"),  # Community write
    UdpTransportTarget(("192.168.1.1", 161)),
    ContextData(),
    ObjectType(
        ObjectIdentity("SNMPv2-MIB", "sysContact", 0),
        OctetString("admin@esempio.it")
    ),
)

errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
if errorIndication:
    print(f"Errore: {errorIndication}")
elif errorStatus:
    print(f"Errore SET: {errorStatus.prettyPrint()}")
else:
    for nome, valore in varBinds:
        print(f"Impostato: {nome.prettyPrint()} = {valore.prettyPrint()}")
```

#### SNMPv3 con Autenticazione e Crittografia

```python
from pysnmp.hlapi import (
    getCmd, SnmpEngine, UsmUserData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity,
    usmHMACMD5AuthProtocol, usmDESPrivProtocol
)

# SNMPv3 con autenticazione MD5 e crittografia DES
iterator = getCmd(
    SnmpEngine(),
    UsmUserData(
        "snmpv3user",
        "authPassword123",          # Password autenticazione
        "privPassword456",          # Password crittografia
        authProtocol=usmHMACMD5AuthProtocol,
        privProtocol=usmDESPrivProtocol,
    ),
    UdpTransportTarget(("192.168.1.1", 161)),
    ContextData(),
    ObjectType(ObjectIdentity("SNMPv2-MIB", "sysDescr", 0)),
)

errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
if not errorIndication and not errorStatus:
    for nome, valore in varBinds:
        print(f"{nome.prettyPrint()} = {valore.prettyPrint()}")
```

#### Monitoraggio Pratico di Dispositivi di Rete

```python
from pysnmp.hlapi import (
    getCmd, SnmpEngine, CommunityData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity
)
import time


def monitora_interfacce(target, community="public", intervallo=60):
    """Monitora il traffico sulle interfacce di un dispositivo di rete."""
    oids = [
        ObjectType(ObjectIdentity("IF-MIB", "ifInOctets", 1)),
        ObjectType(ObjectIdentity("IF-MIB", "ifOutOctets", 1)),
        ObjectType(ObjectIdentity("IF-MIB", "ifOperStatus", 1)),
    ]

    valori_precedenti = {}
    while True:
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((target, 161)),
            ContextData(),
            *oids,
        )

        errInd, errSt, errIdx, varBinds = next(iterator)
        if errInd or errSt:
            print(f"Errore SNMP: {errInd or errSt}")
            time.sleep(intervallo)
            continue

        valori_attuali = {}
        for nome, valore in varBinds:
            chiave = nome.prettyPrint()
            valori_attuali[chiave] = int(valore)

        if valori_precedenti:
            for chiave in valori_attuali:
                if "Octets" in chiave and chiave in valori_precedenti:
                    delta = valori_attuali[chiave] - valori_precedenti[chiave]
                    bps = (delta * 8) / intervallo
                    print(f"{chiave}: {bps:.0f} bps")

        valori_precedenti = valori_attuali
        time.sleep(intervallo)
```

---

## DNS

Il DNS (Domain Name System) e il servizio che traduce i nomi di dominio in indirizzi IP. Python offre la libreria `dnspython` per interrogazioni DNS avanzate.

### dnspython

```bash
pip install dnspython
```

#### Lookup Diretto e Inverso

```python
import dns.resolver
import dns.reversename

# --- Lookup diretto (nome -> IP) ---
risposte = dns.resolver.resolve("python.org", "A")
for rdata in risposte:
    print(f"python.org A -> {rdata.address}")

# --- Lookup inverso (IP -> nome) ---
nome_inverso = dns.reversename.from_address("8.8.8.8")
risposte = dns.resolver.resolve(nome_inverso, "PTR")
for rdata in risposte:
    print(f"8.8.8.8 PTR -> {rdata.target}")
```

#### Tutti i Tipi di Record

```python
import dns.resolver


def interroga_dns(dominio):
    """Interroga tutti i record DNS comuni per un dominio."""
    tipi_record = ["A", "AAAA", "MX", "NS", "TXT", "SRV", "CNAME", "SOA"]

    for tipo in tipi_record:
        try:
            risposte = dns.resolver.resolve(dominio, tipo)
            for rdata in risposte:
                if tipo == "MX":
                    print(f"  {tipo}: {rdata.preference} {rdata.exchange}")
                elif tipo == "NS":
                    print(f"  {tipo}: {rdata.target}")
                elif tipo == "SOA":
                    print(f"  {tipo}: {rdata.mname} (serial: {rdata.serial})")
                elif tipo == "SRV":
                    print(f"  {tipo}: {rdata.priority} {rdata.weight} "
                          f"{rdata.port} {rdata.target}")
                else:
                    print(f"  {tipo}: {rdata}")
        except dns.resolver.NoAnswer:
            pass  # Nessun record di questo tipo
        except dns.resolver.NXDOMAIN:
            print(f"  Dominio {dominio} non trovato!")
            return
        except Exception as e:
            print(f"  {tipo}: Errore - {e}")


interroga_dns("google.com")
```

#### Zone Transfer

```python
import dns.zone
import dns.query


def trasferimento_zona(dominio, nameserver):
    """Tenta un trasferimento di zona AXFR."""
    try:
        zona = dns.zone.from_xfr(dns.query.xfr(nameserver, dominio))
        print(f"Trasferimento zona per {dominio}:")
        for nome, nodo in sorted(zona.nodes.items()):
            rdatasets = nodo.rdatasets
            for rdataset in rdatasets:
                print(f"  {nome} {rdataset}")
    except dns.exception.FormError:
        print("Trasferimento di zona rifiutato dal server")
    except Exception as e:
        print(f"Errore: {e}")


trasferimento_zona("esempio.it", "ns1.esempio.it")
```

#### DNS Health Checker Pratico

```python
import dns.resolver
import time
from dataclasses import dataclass


@dataclass
class RisultatoCheck:
    dominio: str
    tipo_record: str
    successo: bool
    tempo_ms: float
    dettaglio: str


def dns_health_check(domini, nameserver=None):
    """Controlla lo stato DNS di una lista di domini."""
    resolver = dns.resolver.Resolver()
    if nameserver:
        resolver.nameservers = [nameserver]
    resolver.timeout = 5
    resolver.lifetime = 10

    risultati = []

    for dominio in domini:
        for tipo in ["A", "MX", "NS"]:
            inizio = time.time()
            try:
                risposte = resolver.resolve(dominio, tipo)
                tempo = (time.time() - inizio) * 1000
                records = [str(r) for r in risposte]
                risultati.append(RisultatoCheck(
                    dominio=dominio,
                    tipo_record=tipo,
                    successo=True,
                    tempo_ms=tempo,
                    dettaglio=", ".join(records)
                ))
            except dns.resolver.NoAnswer:
                tempo = (time.time() - inizio) * 1000
                risultati.append(RisultatoCheck(
                    dominio=dominio,
                    tipo_record=tipo,
                    successo=True,
                    tempo_ms=tempo,
                    dettaglio="Nessun record"
                ))
            except Exception as e:
                tempo = (time.time() - inizio) * 1000
                risultati.append(RisultatoCheck(
                    dominio=dominio,
                    tipo_record=tipo,
                    successo=False,
                    tempo_ms=tempo,
                    dettaglio=str(e)
                ))

    # Report
    print(f"{'Dominio':<25} {'Tipo':<6} {'Stato':<10} {'Tempo':<10} {'Dettaglio'}")
    print("-" * 90)
    for r in risultati:
        stato = "OK" if r.successo else "ERRORE"
        print(f"{r.dominio:<25} {r.tipo_record:<6} {stato:<10} "
              f"{r.tempo_ms:<10.1f} {r.dettaglio[:40]}")


dns_health_check(["google.com", "python.org", "github.com"])
```

---

## SSH/SFTP

L'accesso remoto tramite SSH e fondamentale per l'automazione di sistemi e la gestione dell'infrastruttura.

### paramiko

```bash
pip install paramiko
```

#### Connessione SSH e Esecuzione Comandi

```python
import paramiko


def esegui_comando_ssh(host, username, password=None, key_filename=None, comando=""):
    """Esegue un comando su un host remoto via SSH."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=22,
            username=username,
            password=password,
            key_filename=key_filename,
            timeout=10,
        )

        stdin, stdout, stderr = client.exec_command(comando, timeout=30)
        exit_code = stdout.channel.recv_exit_status()

        output = stdout.read().decode("utf-8").strip()
        errore = stderr.read().decode("utf-8").strip()

        return {
            "exit_code": exit_code,
            "stdout": output,
            "stderr": errore,
        }
    finally:
        client.close()


# Uso con password
risultato = esegui_comando_ssh(
    host="192.168.1.100",
    username="admin",
    password="password123",
    comando="df -h"
)
print(f"Exit code: {risultato['exit_code']}")
print(f"Output:\n{risultato['stdout']}")

# Uso con chiave SSH
risultato = esegui_comando_ssh(
    host="192.168.1.100",
    username="admin",
    key_filename="/home/utente/.ssh/id_rsa",
    comando="uptime"
)
```

#### SFTP Client

```python
import paramiko
import os
from pathlib import Path


class ClienteSFTP:
    """Client SFTP per upload, download e gestione file remoti."""

    def __init__(self, host, username, password=None, key_filename=None, porta=22):
        self.transport = paramiko.Transport((host, porta))
        if key_filename:
            chiave = paramiko.RSAKey.from_private_key_file(key_filename)
            self.transport.connect(username=username, pkey=chiave)
        else:
            self.transport.connect(username=username, password=password)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def upload(self, percorso_locale, percorso_remoto):
        """Carica un file sul server remoto."""
        self.sftp.put(percorso_locale, percorso_remoto)
        info = self.sftp.stat(percorso_remoto)
        print(f"Upload completato: {percorso_remoto} ({info.st_size} bytes)")

    def download(self, percorso_remoto, percorso_locale):
        """Scarica un file dal server remoto."""
        self.sftp.get(percorso_remoto, percorso_locale)
        dimensione = os.path.getsize(percorso_locale)
        print(f"Download completato: {percorso_locale} ({dimensione} bytes)")

    def lista_directory(self, percorso_remoto="."):
        """Elenca il contenuto di una directory remota."""
        entries = self.sftp.listdir_attr(percorso_remoto)
        for entry in sorted(entries, key=lambda e: e.filename):
            tipo = "d" if entry.longname.startswith("d") else "-"
            print(f"  {tipo} {entry.st_size:>10} {entry.filename}")
        return entries

    def upload_directory(self, dir_locale, dir_remoto):
        """Carica ricorsivamente una directory."""
        try:
            self.sftp.mkdir(dir_remoto)
        except IOError:
            pass  # La directory esiste gia

        for elemento in Path(dir_locale).rglob("*"):
            percorso_relativo = elemento.relative_to(dir_locale)
            remoto = f"{dir_remoto}/{percorso_relativo}"

            if elemento.is_dir():
                try:
                    self.sftp.mkdir(remoto)
                except IOError:
                    pass
            else:
                self.sftp.put(str(elemento), remoto)
                print(f"  Caricato: {remoto}")

    def chiudi(self):
        """Chiude la connessione SFTP."""
        self.sftp.close()
        self.transport.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.chiudi()


# Uso
with ClienteSFTP("192.168.1.100", "admin", password="pass123") as sftp:
    sftp.lista_directory("/var/log")
    sftp.upload("report.csv", "/home/admin/report.csv")
    sftp.download("/var/log/syslog", "./syslog_backup.txt")
```

#### Jump Host (ProxyCommand)

```python
import paramiko


def ssh_via_jump_host(
    jump_host, jump_user, jump_password,
    target_host, target_user, target_password,
    comando
):
    """Connessione SSH attraverso un jump host (bastion)."""
    # Connessione al jump host
    jump = paramiko.SSHClient()
    jump.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump.connect(jump_host, username=jump_user, password=jump_password)

    # Crea un canale TCP verso il target attraverso il jump host
    jump_transport = jump.get_transport()
    canale = jump_transport.open_channel(
        "direct-tcpip",
        (target_host, 22),
        ("127.0.0.1", 0)
    )

    # Connessione al target attraverso il canale
    target = paramiko.SSHClient()
    target.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    target.connect(
        target_host,
        username=target_user,
        password=target_password,
        sock=canale
    )

    stdin, stdout, stderr = target.exec_command(comando)
    output = stdout.read().decode("utf-8")

    target.close()
    jump.close()

    return output


output = ssh_via_jump_host(
    "bastion.esempio.it", "admin", "pass_jump",
    "10.0.0.50", "root", "pass_target",
    "hostname && uptime"
)
print(output)
```

### asyncssh

`asyncssh` permette operazioni SSH asincrone, ideale per gestire molti host in parallelo.

```bash
pip install asyncssh
```

```python
import asyncio
import asyncssh


async def esegui_su_host(host, username, password, comando):
    """Esegue un comando SSH in modo asincrono."""
    try:
        async with asyncssh.connect(
            host, username=username, password=password,
            known_hosts=None
        ) as conn:
            risultato = await conn.run(comando, check=True)
            return {
                "host": host,
                "stdout": risultato.stdout.strip(),
                "successo": True,
            }
    except Exception as e:
        return {
            "host": host,
            "stdout": str(e),
            "successo": False,
        }


async def esegui_su_multipli_host(host_list, comando):
    """Esecuzione parallela su piu host."""
    compiti = [
        esegui_su_host(h["host"], h["user"], h["password"], comando)
        for h in host_list
    ]
    risultati = await asyncio.gather(*compiti)

    for r in risultati:
        stato = "OK" if r["successo"] else "ERRORE"
        print(f"[{stato}] {r['host']}: {r['stdout'][:80]}")

    return risultati


# Definizione degli host
hosts = [
    {"host": "192.168.1.10", "user": "admin", "password": "pass1"},
    {"host": "192.168.1.11", "user": "admin", "password": "pass2"},
    {"host": "192.168.1.12", "user": "admin", "password": "pass3"},
]

asyncio.run(esegui_su_multipli_host(hosts, "uptime && free -h"))
```

### Fabric — Automazione SSH ad Alto Livello

`fabric` costruisce su paramiko fornendo un'API dichiarativa per l'esecuzione remota di comandi, il deployment automatizzato e la gestione di gruppi di server. E ideale per operazioni DevOps ripetitive dove paramiko risulterebbe troppo verboso.

```bash
pip install fabric
```

#### Comandi remoti con Fabric

```python
from fabric import Connection, Config
from invoke import Responder


def deploy_applicazione(host: str, utente: str, chiave: str):
    """Esempio di deployment automatizzato con Fabric."""
    config = Config(overrides={"sudo": {"password": "sudo_password_qui"}})

    conn = Connection(
        host=host,
        user=utente,
        connect_kwargs={"key_filename": chiave},
        config=config,
    )

    with conn:
        # Aggiorna il repository
        risultato = conn.run("cd /opt/app && git pull origin main", hide=True)
        print(f"Git pull: {risultato.stdout.strip()}")

        # Installa dipendenze
        conn.run("cd /opt/app && pip install -r requirements.txt", hide=True)

        # Restart del servizio con sudo
        conn.sudo("systemctl restart app.service", hide=True)

        # Verifica che il servizio sia attivo
        risultato = conn.run("systemctl is-active app.service", hide=True)
        stato = risultato.stdout.strip()

        if stato == "active":
            print(f"Deploy su {host}: servizio attivo")
        else:
            print(f"ERRORE: servizio in stato '{stato}'")
            # Rollback
            conn.run("cd /opt/app && git checkout HEAD~1", hide=True)
            conn.sudo("systemctl restart app.service", hide=True)
            print("Rollback eseguito")


deploy_applicazione("192.168.1.100", "deployer", "/home/deployer/.ssh/id_ed25519")
```

#### Esecuzione su gruppi di server

```python
from fabric import SerialGroup, ThreadingGroup


def aggiorna_tutti_i_server(hosts: list[str], utente: str, chiave: str):
    """Esegue comandi su un gruppo di server in parallelo."""
    # ThreadingGroup esegue in parallelo
    gruppo = ThreadingGroup(
        *hosts,
        user=utente,
        connect_kwargs={"key_filename": chiave},
    )

    # Aggiornamento sistema
    risultati = gruppo.run("apt-get update -qq && apt-get upgrade -y -qq", hide=True)
    for conn, risultato in risultati.items():
        print(f"  {conn.host}: exit_code={risultato.exited}")

    # Trasferimento file a tutti i server
    for conn in gruppo:
        conn.put("config_nuovo.yml", "/etc/app/config.yml")
        print(f"  Config copiata su {conn.host}")


servers = ["web1.esempio.it", "web2.esempio.it", "web3.esempio.it"]
# aggiorna_tutti_i_server(servers, "admin", "/home/admin/.ssh/id_ed25519")
```

---

## Email Protocols

Python include nella libreria standard il supporto completo per l'invio e la ricezione di email tramite SMTP, IMAP e POP3.

### SMTP (smtplib)

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def invia_email_html(
    smtp_host, smtp_porta, mittente, password,
    destinatario, oggetto, corpo_html, allegati=None
):
    """Invia un'email HTML con allegati opzionali."""
    msg = MIMEMultipart("mixed")
    msg["From"] = mittente
    msg["To"] = destinatario
    msg["Subject"] = oggetto

    # Corpo HTML
    parte_html = MIMEText(corpo_html, "html", "utf-8")
    msg.attach(parte_html)

    # Allegati
    if allegati:
        for percorso_file in allegati:
            with open(percorso_file, "rb") as f:
                parte = MIMEBase("application", "octet-stream")
                parte.set_payload(f.read())
                encoders.encode_base64(parte)
                nome_file = percorso_file.split("/")[-1]
                parte.add_header(
                    "Content-Disposition",
                    f"attachment; filename={nome_file}"
                )
                msg.attach(parte)

    # Invio con TLS
    with smtplib.SMTP(smtp_host, smtp_porta) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(mittente, password)
        server.send_message(msg)
        print(f"Email inviata a {destinatario}")


# Uso
corpo = """
<html>
<body>
    <h1>Report Giornaliero</h1>
    <p>In allegato il report di monitoraggio di oggi.</p>
    <table border="1">
        <tr><th>Servizio</th><th>Stato</th></tr>
        <tr><td>Web Server</td><td style="color:green">Online</td></tr>
        <tr><td>Database</td><td style="color:green">Online</td></tr>
        <tr><td>Cache</td><td style="color:red">Offline</td></tr>
    </table>
</body>
</html>
"""

invia_email_html(
    smtp_host="smtp.gmail.com",
    smtp_porta=587,
    mittente="admin@esempio.it",
    password="app_password_qui",
    destinatario="team@esempio.it",
    oggetto="Report Monitoraggio - Giornaliero",
    corpo_html=corpo,
    allegati=["report.pdf", "log.txt"]
)
```

### IMAP (imaplib)

```python
import imaplib
import email
from email.header import decode_header


def leggi_email(host, username, password, cartella="INBOX", limite=10):
    """Legge le email piu recenti da una casella IMAP."""
    with imaplib.IMAP4_SSL(host) as mail:
        mail.login(username, password)

        # Lista delle cartelle disponibili
        stato, cartelle = mail.list()
        print("Cartelle disponibili:")
        for c in cartelle:
            print(f"  {c.decode()}")

        # Seleziona la cartella
        mail.select(cartella)

        # Cerca tutte le email (o filtri specifici)
        stato, messaggi = mail.search(None, "ALL")
        # Alternativa: cercare email non lette
        # stato, messaggi = mail.search(None, "UNSEEN")
        # Alternativa: cercare per mittente
        # stato, messaggi = mail.search(None, 'FROM "admin@esempio.it"')

        id_email = messaggi[0].split()
        # Prendi le ultime N email
        id_recenti = id_email[-limite:] if len(id_email) >= limite else id_email

        for email_id in reversed(id_recenti):
            stato, dati = mail.fetch(email_id, "(RFC822)")
            messaggio_raw = dati[0][1]
            msg = email.message_from_bytes(messaggio_raw)

            # Decodifica l'oggetto
            oggetto, encoding = decode_header(msg["Subject"])[0]
            if isinstance(oggetto, bytes):
                oggetto = oggetto.decode(encoding or "utf-8")

            mittente = msg["From"]
            data = msg["Date"]
            print(f"\n{'='*60}")
            print(f"Da: {mittente}")
            print(f"Oggetto: {oggetto}")
            print(f"Data: {data}")

            # Estrai il corpo del messaggio
            if msg.is_multipart():
                for parte in msg.walk():
                    content_type = parte.get_content_type()
                    if content_type == "text/plain":
                        corpo = parte.get_payload(decode=True)
                        charset = parte.get_content_charset() or "utf-8"
                        print(f"Corpo:\n{corpo.decode(charset)[:500]}")
                        break
            else:
                corpo = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or "utf-8"
                print(f"Corpo:\n{corpo.decode(charset)[:500]}")

        mail.close()


leggi_email("imap.gmail.com", "utente@gmail.com", "app_password")
```

### POP3 (poplib)

POP3 e un protocollo piu semplice di IMAP, adatto al recupero base delle email.

```python
import poplib
import email


def leggi_email_pop3(host, username, password, limite=5):
    """Recupera le email piu recenti via POP3."""
    with poplib.POP3_SSL(host) as server:
        server.user(username)
        server.pass_(password)

        # Statistiche della casella
        num_messaggi, dimensione = server.stat()
        print(f"Messaggi: {num_messaggi}, Dimensione totale: {dimensione} bytes")

        # Recupera gli ultimi N messaggi
        inizio = max(1, num_messaggi - limite + 1)
        for i in range(num_messaggi, inizio - 1, -1):
            stato, linee, dimensione = server.retr(i)
            messaggio_raw = b"\r\n".join(linee)
            msg = email.message_from_bytes(messaggio_raw)
            print(f"\n[{i}] Da: {msg['From']}")
            print(f"     Oggetto: {msg['Subject']}")


leggi_email_pop3("pop.gmail.com", "utente@gmail.com", "app_password")
```

---

## Network Scanning e Discovery

La scansione di rete e fondamentale per l'inventario dei dispositivi, la verifica della sicurezza e la diagnostica di rete.

### scapy

`scapy` e una libreria potentissima per la creazione, manipolazione e analisi di pacchetti di rete a basso livello.

```bash
pip install scapy
```

#### Crafting e Invio Pacchetti

```python
from scapy.all import IP, TCP, UDP, ICMP, Ether, ARP, sr1, srp, send, conf

# Disabilita la verbosita di default
conf.verb = 0

# --- ICMP Ping ---
pacchetto = IP(dst="8.8.8.8") / ICMP()
risposta = sr1(pacchetto, timeout=2)
if risposta:
    print(f"Ping verso 8.8.8.8: RTT={risposta.time - pacchetto.sent_time:.3f}s")
else:
    print("Nessuna risposta")

# --- TCP SYN (verifica se una porta e aperta) ---
pacchetto = IP(dst="scanme.nmap.org") / TCP(dport=80, flags="S")
risposta = sr1(pacchetto, timeout=2)
if risposta and risposta.haslayer(TCP):
    if risposta[TCP].flags == "SA":  # SYN-ACK
        print("Porta 80: APERTA")
        # Invia RST per chiudere la connessione
        send(IP(dst="scanme.nmap.org") / TCP(dport=80, flags="R"))
    elif risposta[TCP].flags == "RA":  # RST-ACK
        print("Porta 80: CHIUSA")
```

#### ARP Scan (Discovery sulla rete locale)

```python
from scapy.all import ARP, Ether, srp, conf

conf.verb = 0


def arp_scan(rete):
    """Scansione ARP per scoprire dispositivi sulla rete locale."""
    # Crea pacchetto ARP broadcast
    arp = ARP(pdst=rete)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    pacchetto = broadcast / arp

    risposte, _ = srp(pacchetto, timeout=3)

    dispositivi = []
    for inviato, ricevuto in risposte:
        dispositivi.append({
            "ip": ricevuto.psrc,
            "mac": ricevuto.hwsrc,
        })

    print(f"\nDispositivi trovati sulla rete {rete}:")
    print(f"{'IP':<18} {'MAC':<20}")
    print("-" * 38)
    for d in dispositivi:
        print(f"{d['ip']:<18} {d['mac']:<20}")

    return dispositivi


# Scansiona la rete locale
arp_scan("192.168.1.0/24")
```

#### TCP SYN Scan

```python
from scapy.all import IP, TCP, sr1, conf

conf.verb = 0


def syn_scan(target, porte):
    """Scansione SYN sulle porte specificate."""
    porte_aperte = []
    porte_chiuse = []
    porte_filtrate = []

    for porta in porte:
        pacchetto = IP(dst=target) / TCP(dport=porta, flags="S")
        risposta = sr1(pacchetto, timeout=1)

        if risposta is None:
            porte_filtrate.append(porta)
        elif risposta.haslayer(TCP):
            if risposta[TCP].flags == 0x12:  # SYN-ACK
                porte_aperte.append(porta)
                # Invia RST per chiudere
                rst = IP(dst=target) / TCP(dport=porta, flags="R")
                sr1(rst, timeout=0.5)
            elif risposta[TCP].flags == 0x14:  # RST-ACK
                porte_chiuse.append(porta)

    print(f"\nRisultati scansione SYN per {target}:")
    if porte_aperte:
        print(f"  Porte aperte: {porte_aperte}")
    if porte_filtrate:
        print(f"  Porte filtrate: {porte_filtrate}")
    print(f"  Porte chiuse: {len(porte_chiuse)}")

    return porte_aperte


porte_comuni = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 5432, 8080]
syn_scan("scanme.nmap.org", porte_comuni)
```

#### ICMP Ping Sweep

```python
from scapy.all import IP, ICMP, sr, conf
import ipaddress

conf.verb = 0


def ping_sweep(rete):
    """Scansiona un'intera rete con ICMP ping."""
    rete_obj = ipaddress.ip_network(rete, strict=False)
    target_ips = [str(ip) for ip in rete_obj.hosts()]

    pacchetti = [IP(dst=ip) / ICMP() for ip in target_ips]
    risposte, _ = sr(pacchetti, timeout=2)

    host_attivi = []
    for inviato, ricevuto in risposte:
        host_attivi.append(ricevuto.src)

    print(f"\nPing sweep su {rete}:")
    print(f"Host attivi: {len(host_attivi)}/{len(target_ips)}")
    for ip in sorted(host_attivi, key=lambda x: ipaddress.ip_address(x)):
        print(f"  {ip}")

    return host_attivi


ping_sweep("192.168.1.0/24")
```

#### Packet Sniffing

```python
from scapy.all import sniff, IP, TCP, DNS, DNSQR


def analizza_pacchetto(pacchetto):
    """Callback per analizzare ogni pacchetto catturato."""
    if pacchetto.haslayer(IP):
        ip_src = pacchetto[IP].src
        ip_dst = pacchetto[IP].dst

        if pacchetto.haslayer(TCP):
            porta_src = pacchetto[TCP].sport
            porta_dst = pacchetto[TCP].dport
            flags = pacchetto[TCP].flags
            print(f"TCP {ip_src}:{porta_src} -> {ip_dst}:{porta_dst} [{flags}]")

        if pacchetto.haslayer(DNS) and pacchetto.haslayer(DNSQR):
            dominio = pacchetto[DNSQR].qname.decode()
            print(f"DNS Query: {ip_src} -> {dominio}")


# Cattura 100 pacchetti sull'interfaccia di rete
# NOTA: richiede privilegi di root
print("Avvio cattura pacchetti (100 pacchetti)...")
sniff(
    count=100,
    prn=analizza_pacchetto,
    filter="tcp or udp",  # Filtro BPF
    store=False,           # Non conservare i pacchetti in memoria
)
```

### python-nmap

`python-nmap` fornisce un'interfaccia Python a Nmap, lo scanner di rete piu utilizzato al mondo.

```bash
pip install python-nmap
# Richiede nmap installato sul sistema: sudo apt install nmap
```

```python
import nmap


def scansione_completa(target, porte="1-1024"):
    """Scansione completa con rilevamento servizi e OS."""
    scanner = nmap.PortScanner()

    # --- Scansione porte ---
    print(f"Scansione porte su {target}...")
    scanner.scan(target, porte, arguments="-sV")

    for host in scanner.all_hosts():
        print(f"\nHost: {host} ({scanner[host].hostname()})")
        print(f"Stato: {scanner[host].state()}")

        for protocollo in scanner[host].all_protocols():
            print(f"\n  Protocollo: {protocollo}")
            porte_trovate = sorted(scanner[host][protocollo].keys())

            for porta in porte_trovate:
                info = scanner[host][protocollo][porta]
                stato = info["state"]
                servizio = info["name"]
                versione = info.get("version", "")
                prodotto = info.get("product", "")
                print(f"    Porta {porta:<6} {stato:<8} {servizio:<15} "
                      f"{prodotto} {versione}")

    # --- Rilevamento OS (richiede root) ---
    print(f"\nRilevamento OS su {target}...")
    try:
        scanner.scan(target, arguments="-O")
        if "osmatch" in scanner[target]:
            for os_match in scanner[target]["osmatch"][:3]:
                print(f"  OS: {os_match['name']} (accuratezza: {os_match['accuracy']}%)")
    except nmap.PortScannerError:
        print("  Rilevamento OS richiede privilegi di root")


scansione_completa("scanme.nmap.org")


def scansione_rete(rete):
    """Scansione rapida di discovery sulla rete."""
    scanner = nmap.PortScanner()
    scanner.scan(hosts=rete, arguments="-sn")  # Ping scan

    print(f"\nHost attivi nella rete {rete}:")
    for host in scanner.all_hosts():
        stato = scanner[host].state()
        hostname = scanner[host].hostname() or "N/A"
        print(f"  {host:<18} {stato:<8} {hostname}")


scansione_rete("192.168.1.0/24")
```

---

## WebSocket Programming

Il protocollo WebSocket (RFC 6455) fornisce comunicazione full-duplex su una singola connessione TCP, ideale per applicazioni real-time come chat, notifiche live, dashboard di monitoraggio e giochi multiplayer. A differenza di HTTP, il canale resta aperto e sia client sia server possono inviare messaggi in qualsiasi momento.

### websockets — Server e Client

La libreria `websockets` e l'implementazione di riferimento per WebSocket in Python, costruita interamente su asyncio.

```bash
pip install websockets
```

#### Server WebSocket

```python
import asyncio
import websockets
import json
from datetime import datetime


# Insieme dei client connessi
CLIENTS: set[websockets.WebSocketServerProtocol] = set()


async def registra(ws: websockets.WebSocketServerProtocol):
    """Registra un nuovo client."""
    CLIENTS.add(ws)
    print(f"[+] Client connesso: {ws.remote_address} "
          f"(totale: {len(CLIENTS)})")


async def cancella_registrazione(ws: websockets.WebSocketServerProtocol):
    """Rimuove un client disconnesso."""
    CLIENTS.discard(ws)
    print(f"[-] Client disconnesso: {ws.remote_address} "
          f"(totale: {len(CLIENTS)})")


async def broadcast(messaggio: str, mittente: websockets.WebSocketServerProtocol):
    """Invia un messaggio a tutti i client connessi tranne il mittente."""
    destinatari = CLIENTS - {mittente}
    if destinatari:
        await asyncio.gather(
            *(client.send(messaggio) for client in destinatari),
            return_exceptions=True,
        )


async def gestisci_connessione(ws: websockets.WebSocketServerProtocol):
    """Handler principale per ogni connessione WebSocket."""
    await registra(ws)
    try:
        async for messaggio_raw in ws:
            try:
                dati = json.loads(messaggio_raw)
            except json.JSONDecodeError:
                await ws.send(json.dumps({"errore": "JSON non valido"}))
                continue

            tipo = dati.get("tipo")
            if tipo == "chat":
                payload = json.dumps({
                    "tipo": "chat",
                    "utente": dati.get("utente", "Anonimo"),
                    "testo": dati.get("testo", ""),
                    "timestamp": datetime.now().isoformat(),
                })
                await broadcast(payload, ws)
                # Conferma al mittente
                await ws.send(json.dumps({"tipo": "ack", "id": dati.get("id")}))

            elif tipo == "ping":
                await ws.send(json.dumps({
                    "tipo": "pong",
                    "timestamp": datetime.now().isoformat(),
                }))

    except websockets.ConnectionClosed as e:
        print(f"Connessione chiusa: {e.code} {e.reason}")
    finally:
        await cancella_registrazione(ws)


async def avvia_server_ws(host: str = "0.0.0.0", porta: int = 8765):
    """Avvia il server WebSocket."""
    async with websockets.serve(
        gestisci_connessione,
        host,
        porta,
        ping_interval=20,     # Keepalive ogni 20 secondi
        ping_timeout=10,      # Timeout risposta pong
        max_size=2**20,       # Max dimensione messaggio: 1 MB
        compression="deflate",  # Compressione permessage-deflate
    ):
        print(f"Server WebSocket in ascolto su ws://{host}:{porta}")
        await asyncio.Future()  # Esegue indefinitamente


# asyncio.run(avvia_server_ws())
```

#### Client WebSocket

```python
import asyncio
import websockets
import json


async def client_ws(uri: str = "ws://localhost:8765"):
    """Client WebSocket che invia e riceve messaggi."""
    async with websockets.connect(
        uri,
        additional_headers={"User-Agent": "PythonWSClient/1.0"},
    ) as ws:
        # Task per ricevere messaggi
        async def ricevi():
            async for messaggio in ws:
                dati = json.loads(messaggio)
                if dati["tipo"] == "chat":
                    print(f"[{dati['utente']}] {dati['testo']}")
                elif dati["tipo"] == "pong":
                    print(f"Pong ricevuto: {dati['timestamp']}")

        # Task per inviare messaggi
        async def invia():
            messaggi = ["Ciao!", "Come state?", "Buon lavoro a tutti!"]
            for testo in messaggi:
                payload = json.dumps({
                    "tipo": "chat",
                    "utente": "Mario",
                    "testo": testo,
                })
                await ws.send(payload)
                await asyncio.sleep(2)

        # Esecuzione parallela di invio e ricezione
        await asyncio.gather(ricevi(), invia())


# asyncio.run(client_ws())
```

#### WebSocket con reconnect automatico

```python
import asyncio
import websockets
import json
import logging

log = logging.getLogger(__name__)


async def client_resiliente(
    uri: str,
    max_tentativi: int = 10,
    backoff_base: float = 1.0,
    backoff_max: float = 60.0,
):
    """Client WebSocket con reconnect automatico e backoff esponenziale."""
    tentativo = 0

    while tentativo < max_tentativi:
        try:
            async with websockets.connect(uri) as ws:
                tentativo = 0  # Reset dopo connessione riuscita
                log.info("Connesso a %s", uri)

                async for messaggio in ws:
                    dati = json.loads(messaggio)
                    await processa_messaggio(dati)

        except websockets.ConnectionClosed as e:
            log.warning("Connessione chiusa: %s %s", e.code, e.reason)
        except (ConnectionRefusedError, OSError) as e:
            log.warning("Connessione fallita: %s", e)

        tentativo += 1
        attesa = min(backoff_base * (2 ** tentativo), backoff_max)
        log.info("Riconnessione in %.1fs (tentativo %d/%d)",
                 attesa, tentativo, max_tentativi)
        await asyncio.sleep(attesa)

    log.error("Numero massimo di tentativi raggiunto, chiusura client")


async def processa_messaggio(dati: dict):
    """Processa un messaggio ricevuto dal server."""
    print(f"Ricevuto: {dati}")
```

### python-socketio — Socket.IO per Python

Socket.IO e un protocollo che opera sopra WebSocket con fallback automatico a HTTP long-polling, fornendo funzionalita aggiuntive come namespace, stanze (rooms) e acknowledgement.

```bash
pip install python-socketio aiohttp
```

#### Server Socket.IO

```python
import socketio
import aiohttp.web

# Crea l'istanza Socket.IO
sio = socketio.AsyncServer(
    async_mode="aiohttp",
    cors_allowed_origins="*",
)
app = aiohttp.web.Application()
sio.attach(app)


@sio.event
async def connect(sid, environ):
    """Handler per nuova connessione."""
    print(f"Client connesso: {sid}")
    await sio.emit("benvenuto", {"messaggio": "Benvenuto nel server!"}, room=sid)


@sio.event
async def disconnect(sid):
    """Handler per disconnessione."""
    print(f"Client disconnesso: {sid}")


@sio.event
async def messaggio_chat(sid, data):
    """Riceve un messaggio chat e lo inoltra a tutti."""
    print(f"[{sid}] {data['testo']}")
    # Broadcast a tutti i client nella stanza "generale"
    await sio.emit("messaggio_chat", {
        "utente": data.get("utente", "Anonimo"),
        "testo": data["testo"],
    }, room="generale", skip_sid=sid)


@sio.event
async def entra_stanza(sid, data):
    """Fa entrare un client in una stanza specifica."""
    stanza = data["stanza"]
    sio.enter_room(sid, stanza)
    await sio.emit("sistema", {
        "messaggio": f"Utente entrato nella stanza {stanza}"
    }, room=stanza)


# aiohttp.web.run_app(app, host="0.0.0.0", port=8080)
```

#### Client Socket.IO

```python
import asyncio
import socketio

sio = socketio.AsyncClient()


@sio.event
async def connect():
    print("Connesso al server Socket.IO")
    await sio.emit("entra_stanza", {"stanza": "generale"})


@sio.event
async def benvenuto(data):
    print(f"Server dice: {data['messaggio']}")


@sio.event
async def messaggio_chat(data):
    print(f"[{data['utente']}] {data['testo']}")


@sio.event
async def disconnect():
    print("Disconnesso dal server")


async def main():
    await sio.connect("http://localhost:8080")
    await sio.emit("messaggio_chat", {
        "utente": "Luigi",
        "testo": "Ciao dalla libreria python-socketio!",
    })
    await asyncio.sleep(5)
    await sio.disconnect()


# asyncio.run(main())
```

---

## Analisi Pacchetti e Parsing PCAP

L'analisi dei file di cattura (pcap/pcapng) e fondamentale per il debugging di protocolli, l'analisi forense di rete e la ricerca di sicurezza. Python offre diverse librerie per il parsing e l'analisi offline dei pacchetti catturati.

### pyshark — Analisi pcap con Wireshark/tshark

`pyshark` e un wrapper Python per tshark (Wireshark a linea di comando) che permette di analizzare file pcap con la stessa potenza dei dissettori di Wireshark.

```bash
pip install pyshark
# Richiede tshark installato: sudo apt install tshark
```

#### Analisi di un file pcap

```python
import pyshark


def analizza_pcap(file_path: str, filtro_display: str = ""):
    """Analizza un file pcap e stampa un riepilogo dei pacchetti."""
    if filtro_display:
        cattura = pyshark.FileCapture(file_path, display_filter=filtro_display)
    else:
        cattura = pyshark.FileCapture(file_path)

    statistiche = {
        "totale": 0,
        "tcp": 0,
        "udp": 0,
        "dns": 0,
        "http": 0,
        "tls": 0,
    }
    conversazioni = {}

    for pacchetto in cattura:
        statistiche["totale"] += 1

        # Analisi per protocollo
        if hasattr(pacchetto, "tcp"):
            statistiche["tcp"] += 1
        if hasattr(pacchetto, "udp"):
            statistiche["udp"] += 1
        if hasattr(pacchetto, "dns"):
            statistiche["dns"] += 1
        if hasattr(pacchetto, "http"):
            statistiche["http"] += 1
        if hasattr(pacchetto, "tls"):
            statistiche["tls"] += 1

        # Tracciamento conversazioni IP
        if hasattr(pacchetto, "ip"):
            coppia = tuple(sorted([pacchetto.ip.src, pacchetto.ip.dst]))
            conversazioni[coppia] = conversazioni.get(coppia, 0) + 1

    cattura.close()

    # Report
    print(f"\nAnalisi di {file_path}:")
    print(f"  Pacchetti totali: {statistiche['totale']}")
    print(f"  TCP: {statistiche['tcp']}, UDP: {statistiche['udp']}")
    print(f"  DNS: {statistiche['dns']}, HTTP: {statistiche['http']}")
    print(f"  TLS: {statistiche['tls']}")

    print(f"\n  Top 10 conversazioni:")
    top = sorted(conversazioni.items(), key=lambda x: x[1], reverse=True)[:10]
    for (ip1, ip2), conteggio in top:
        print(f"    {ip1} <-> {ip2}: {conteggio} pacchetti")

    return statistiche


analizza_pcap("cattura.pcap")
# Con filtro: solo traffico HTTP
analizza_pcap("cattura.pcap", filtro_display="http")
```

#### Cattura live con pyshark

```python
import pyshark


def cattura_live(interfaccia: str = "eth0", durata: int = 30, filtro: str = ""):
    """Cattura pacchetti in tempo reale dall'interfaccia di rete."""
    cattura = pyshark.LiveCapture(
        interface=interfaccia,
        bpf_filter=filtro,  # Filtro BPF (es. "tcp port 80")
    )

    print(f"Cattura live su {interfaccia} per {durata} secondi...")

    for pacchetto in cattura.sniff_continuously(packet_count=100):
        timestamp = pacchetto.sniff_time
        protocollo = pacchetto.highest_layer

        if hasattr(pacchetto, "ip"):
            src = pacchetto.ip.src
            dst = pacchetto.ip.dst
            print(f"[{timestamp:%H:%M:%S}] {protocollo:<8} "
                  f"{src} -> {dst}")

        if hasattr(pacchetto, "dns") and hasattr(pacchetto.dns, "qry_name"):
            print(f"  DNS Query: {pacchetto.dns.qry_name}")

        if hasattr(pacchetto, "http"):
            if hasattr(pacchetto.http, "request_method"):
                print(f"  HTTP {pacchetto.http.request_method} "
                      f"{pacchetto.http.request_uri}")


# Richiede privilegi root
# cattura_live("eth0", filtro="tcp port 80 or tcp port 443")
```

### dpkt — Parsing pcap leggero

`dpkt` e una libreria leggera e veloce per il parsing di pacchetti di rete, ideale per l'elaborazione di grandi file pcap senza dipendenze esterne come tshark.

```bash
pip install dpkt
```

```python
import dpkt
import socket
from collections import Counter
from datetime import datetime, timezone


def analizza_pcap_dpkt(file_path: str):
    """Analizza un file pcap con dpkt per statistiche dettagliate."""
    protocolli = Counter()
    ip_sorgenti = Counter()
    ip_destinazioni = Counter()
    porte_dst = Counter()
    dimensione_totale = 0
    primo_ts = None
    ultimo_ts = None

    with open(file_path, "rb") as f:
        pcap = dpkt.pcap.Reader(f)

        for timestamp, buf in pcap:
            if primo_ts is None:
                primo_ts = timestamp
            ultimo_ts = timestamp

            dimensione_totale += len(buf)

            try:
                eth = dpkt.ethernet.Ethernet(buf)
            except dpkt.NeedData:
                continue

            if not isinstance(eth.data, dpkt.ip.IP):
                continue

            ip = eth.data
            ip_src = socket.inet_ntoa(ip.src)
            ip_dst = socket.inet_ntoa(ip.dst)

            ip_sorgenti[ip_src] += 1
            ip_destinazioni[ip_dst] += 1

            if isinstance(ip.data, dpkt.tcp.TCP):
                protocolli["TCP"] += 1
                porte_dst[ip.data.dport] += 1
            elif isinstance(ip.data, dpkt.udp.UDP):
                protocolli["UDP"] += 1
                porte_dst[ip.data.dport] += 1
            elif isinstance(ip.data, dpkt.icmp.ICMP):
                protocolli["ICMP"] += 1

    # Report
    durata = ultimo_ts - primo_ts if primo_ts and ultimo_ts else 0
    print(f"\nAnalisi pcap (dpkt): {file_path}")
    print(f"  Durata cattura: {durata:.1f} secondi")
    print(f"  Dimensione totale: {dimensione_totale / 1024:.1f} KB")

    print(f"\n  Protocolli:")
    for proto, count in protocolli.most_common():
        print(f"    {proto}: {count}")

    print(f"\n  Top 5 IP sorgenti:")
    for ip, count in ip_sorgenti.most_common(5):
        print(f"    {ip}: {count} pacchetti")

    print(f"\n  Top 5 porte destinazione:")
    for porta, count in porte_dst.most_common(5):
        print(f"    {porta}: {count} connessioni")


# analizza_pcap_dpkt("cattura.pcap")
```

### scapy per analisi offline

```python
from scapy.all import rdpcap, IP, TCP, DNS, DNSQR
from collections import Counter


def analizza_con_scapy(file_path: str):
    """Analizza un file pcap usando scapy per ispezione dettagliata."""
    pacchetti = rdpcap(file_path)

    print(f"\nAnalisi scapy di {file_path}")
    print(f"  Pacchetti totali: {len(pacchetti)}")

    # Estrazione query DNS
    query_dns = []
    for pkt in pacchetti:
        if pkt.haslayer(DNS) and pkt.haslayer(DNSQR):
            dominio = pkt[DNSQR].qname.decode().rstrip(".")
            query_dns.append(dominio)

    if query_dns:
        print(f"\n  Query DNS univoche: {len(set(query_dns))}")
        for dominio, count in Counter(query_dns).most_common(10):
            print(f"    {dominio}: {count} query")

    # Analisi connessioni TCP (SYN)
    syn_packets = [
        pkt for pkt in pacchetti
        if pkt.haslayer(TCP) and pkt[TCP].flags == "S"
    ]
    if syn_packets:
        print(f"\n  Connessioni TCP iniziate (SYN): {len(syn_packets)}")
        porte = Counter(pkt[TCP].dport for pkt in syn_packets)
        for porta, count in porte.most_common(5):
            print(f"    Porta {porta}: {count} connessioni")


# analizza_con_scapy("cattura.pcap")
```

---

## FTP e FTPS Automation

Il protocollo FTP (File Transfer Protocol) resta diffuso in ambienti legacy, sistemi embedded e per lo scambio automatizzato di file con fornitori esterni. Python fornisce il modulo `ftplib` nella libreria standard per operazioni FTP e FTPS (FTP over TLS).

### ftplib — Client FTP/FTPS

```python
import ftplib
from pathlib import Path


def connessione_ftp(host: str, username: str, password: str, tls: bool = True):
    """Crea una connessione FTP o FTPS."""
    if tls:
        ftp = ftplib.FTP_TLS(host, timeout=30)
        ftp.login(username, password)
        ftp.prot_p()  # Attiva la protezione dati (crittografia sul canale dati)
    else:
        ftp = ftplib.FTP(host, timeout=30)
        ftp.login(username, password)

    print(f"Connesso a {host} (TLS: {tls})")
    print(f"Banner: {ftp.getwelcome()}")
    return ftp


def lista_directory(ftp: ftplib.FTP, percorso: str = "."):
    """Elenca il contenuto di una directory remota con dettagli."""
    entries = []
    ftp.cwd(percorso)

    # MLSD fornisce dati strutturati (RFC 3659)
    try:
        for nome, fatti in ftp.mlsd():
            entries.append({
                "nome": nome,
                "tipo": fatti.get("type", "unknown"),
                "dimensione": int(fatti.get("size", 0)),
                "modificato": fatti.get("modify", ""),
            })
    except ftplib.error_perm:
        # Fallback a LIST se MLSD non e supportato
        linee = []
        ftp.retrlines("LIST", linee.append)
        for linea in linee:
            print(f"  {linea}")
        return []

    # Stampa risultati
    print(f"\nContenuto di {percorso}:")
    for entry in entries:
        tipo = "DIR" if entry["tipo"] == "dir" else "FILE"
        dim = f"{entry['dimensione']:>10}" if tipo == "FILE" else f"{'':>10}"
        print(f"  [{tipo}] {dim} {entry['nome']}")

    return entries


def upload_file(ftp: ftplib.FTP, locale: str, remoto: str):
    """Carica un file locale sul server FTP."""
    dimensione = Path(locale).stat().st_size
    caricati = 0

    def callback(blocco):
        nonlocal caricati
        caricati += len(blocco)
        percentuale = (caricati / dimensione) * 100
        print(f"\rUpload: {percentuale:.1f}%", end="", flush=True)

    with open(locale, "rb") as f:
        ftp.storbinary(f"STOR {remoto}", f, blocksize=8192, callback=callback)
    print(f"\nUpload completato: {remoto}")


def download_file(ftp: ftplib.FTP, remoto: str, locale: str):
    """Scarica un file dal server FTP."""
    with open(locale, "wb") as f:
        ftp.retrbinary(f"RETR {remoto}", f.write, blocksize=8192)
    dimensione = Path(locale).stat().st_size
    print(f"Download completato: {locale} ({dimensione} bytes)")


def upload_directory(ftp: ftplib.FTP, dir_locale: str, dir_remoto: str):
    """Carica ricorsivamente una directory sul server FTP."""
    # Crea la directory remota se non esiste
    try:
        ftp.mkd(dir_remoto)
    except ftplib.error_perm:
        pass  # Directory esiste gia

    for elemento in Path(dir_locale).iterdir():
        percorso_remoto = f"{dir_remoto}/{elemento.name}"
        if elemento.is_dir():
            upload_directory(ftp, str(elemento), percorso_remoto)
        else:
            upload_file(ftp, str(elemento), percorso_remoto)


# Esempio di utilizzo completo
def automazione_ftp_completa():
    """Esempio completo di automazione FTP."""
    ftp = connessione_ftp("ftp.esempio.it", "utente", "password", tls=True)

    try:
        # Listare directory
        files = lista_directory(ftp, "/dati")

        # Upload
        upload_file(ftp, "report_locale.csv", "/dati/report.csv")

        # Download
        download_file(ftp, "/dati/archivio.zip", "./archivio_scaricato.zip")

        # Operazioni di gestione
        ftp.rename("/dati/vecchio.txt", "/dati/nuovo.txt")  # Rinomina
        ftp.delete("/dati/temporaneo.txt")                   # Elimina file
        ftp.mkd("/dati/backup")                              # Crea directory
        ftp.rmd("/dati/vuota")                               # Rimuovi directory vuota

    finally:
        ftp.quit()
        print("Connessione FTP chiusa")


# automazione_ftp_completa()
```

---

## Network Monitoring

Il monitoraggio continuo della rete e essenziale per garantire la disponibilita e le prestazioni dei servizi.

### Ping Monitoring

```python
from icmplib import ping, multiping


def monitora_ping(host, conteggio=4):
    """Esegue un ping monitoring dettagliato verso un host."""
    risultato = ping(host, count=conteggio, interval=0.5, timeout=2)

    print(f"Ping verso {host}:")
    print(f"  Pacchetti inviati: {risultato.packets_sent}")
    print(f"  Pacchetti ricevuti: {risultato.packets_received}")
    print(f"  Perdita pacchetti: {risultato.packet_loss * 100:.1f}%")
    print(f"  RTT min/avg/max: {risultato.min_rtt:.1f}/"
          f"{risultato.avg_rtt:.1f}/{risultato.max_rtt:.1f} ms")
    print(f"  Host raggiungibile: {risultato.is_alive}")

    return risultato


def monitora_multipli_host(hosts):
    """Ping parallelo verso piu host."""
    risultati = multiping(hosts, count=3, timeout=2)

    print(f"\n{'Host':<20} {'Stato':<12} {'RTT avg':<12} {'Perdita':<10}")
    print("-" * 54)
    for r in risultati:
        stato = "ONLINE" if r.is_alive else "OFFLINE"
        rtt = f"{r.avg_rtt:.1f} ms" if r.is_alive else "N/A"
        perdita = f"{r.packet_loss * 100:.0f}%"
        print(f"{r.address:<20} {stato:<12} {rtt:<12} {perdita:<10}")


monitora_ping("8.8.8.8")
monitora_multipli_host(["8.8.8.8", "1.1.1.1", "9.9.9.9", "208.67.222.222"])
```

### Port Monitoring

```python
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def controlla_porta(host, porta, timeout=3):
    """Controlla se una porta e aperta su un host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            inizio = time.time()
            risultato = s.connect_ex((host, porta))
            tempo = (time.time() - inizio) * 1000
            return {
                "host": host,
                "porta": porta,
                "aperta": risultato == 0,
                "tempo_ms": tempo,
            }
    except socket.timeout:
        return {"host": host, "porta": porta, "aperta": False, "tempo_ms": -1}
    except Exception as e:
        return {"host": host, "porta": porta, "aperta": False, "tempo_ms": -1, "errore": str(e)}


def monitora_servizi(servizi, intervallo=30):
    """Monitora continuamente una lista di servizi (host:porta)."""
    while True:
        print(f"\n--- Controllo servizi: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(controlla_porta, s["host"], s["porta"]): s
                for s in servizi
            }

            for future in as_completed(futures):
                servizio = futures[future]
                risultato = future.result()
                stato = "APERTA" if risultato["aperta"] else "CHIUSA"
                nome = servizio.get("nome", f"{servizio['host']}:{servizio['porta']}")
                tempo = f"{risultato['tempo_ms']:.0f}ms" if risultato["tempo_ms"] > 0 else "N/A"
                print(f"  {nome:<30} porta {risultato['porta']:<6} "
                      f"{stato:<8} {tempo}")

        time.sleep(intervallo)


# Definizione dei servizi da monitorare
servizi = [
    {"host": "google.com", "porta": 443, "nome": "Google HTTPS"},
    {"host": "google.com", "porta": 80, "nome": "Google HTTP"},
    {"host": "8.8.8.8", "porta": 53, "nome": "Google DNS"},
    {"host": "github.com", "porta": 22, "nome": "GitHub SSH"},
    {"host": "github.com", "porta": 443, "nome": "GitHub HTTPS"},
]

# monitora_servizi(servizi, intervallo=60)
```

### Service Health Checks

```python
import requests
import time
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HealthCheck:
    nome: str
    url: str
    metodo: str = "GET"
    timeout: int = 10
    codice_atteso: int = 200
    contenuto_atteso: str = ""
    headers: dict = field(default_factory=dict)


def esegui_health_check(check: HealthCheck) -> dict:
    """Esegue un singolo health check su un servizio HTTP."""
    try:
        inizio = time.time()
        risposta = requests.request(
            method=check.metodo,
            url=check.url,
            headers=check.headers,
            timeout=check.timeout,
        )
        tempo = (time.time() - inizio) * 1000

        # Verifica il codice di stato
        codice_ok = risposta.status_code == check.codice_atteso

        # Verifica il contenuto se specificato
        contenuto_ok = True
        if check.contenuto_atteso:
            contenuto_ok = check.contenuto_atteso in risposta.text

        return {
            "nome": check.nome,
            "stato": "SANO" if codice_ok and contenuto_ok else "DEGRADATO",
            "codice": risposta.status_code,
            "tempo_ms": tempo,
            "timestamp": datetime.now().isoformat(),
        }
    except requests.exceptions.Timeout:
        return {
            "nome": check.nome,
            "stato": "TIMEOUT",
            "codice": 0,
            "tempo_ms": check.timeout * 1000,
            "timestamp": datetime.now().isoformat(),
        }
    except requests.exceptions.ConnectionError:
        return {
            "nome": check.nome,
            "stato": "IRRAGGIUNGIBILE",
            "codice": 0,
            "tempo_ms": 0,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "nome": check.nome,
            "stato": f"ERRORE: {e}",
            "codice": 0,
            "tempo_ms": 0,
            "timestamp": datetime.now().isoformat(),
        }


# Definizione dei servizi
checks = [
    HealthCheck(nome="API Principale", url="https://api.esempio.it/health"),
    HealthCheck(nome="Frontend", url="https://www.esempio.it", contenuto_atteso="<!DOCTYPE"),
    HealthCheck(
        nome="API Autenticazione",
        url="https://auth.esempio.it/status",
        headers={"Authorization": "Bearer monitoring_token"},
    ),
]

for check in checks:
    risultato = esegui_health_check(check)
    print(f"  [{risultato['stato']:<15}] {risultato['nome']:<25} "
          f"HTTP {risultato['codice']} ({risultato['tempo_ms']:.0f}ms)")
```

### Bandwidth Monitoring

```python
import psutil
import time


def monitora_banda(interfaccia=None, intervallo=2, durata=60):
    """Monitora l'utilizzo di banda in tempo reale."""
    contatori = psutil.net_io_counters(pernic=True)

    if interfaccia:
        if interfaccia not in contatori:
            print(f"Interfaccia '{interfaccia}' non trovata.")
            print(f"Interfacce disponibili: {list(contatori.keys())}")
            return
        contatori_prev = contatori[interfaccia]
    else:
        contatori_prev = psutil.net_io_counters()

    print(f"{'Tempo':<12} {'Download':<15} {'Upload':<15} "
          f"{'Pacchetti RX':<15} {'Pacchetti TX':<15}")
    print("-" * 72)

    iterazioni = durata // intervallo
    for _ in range(iterazioni):
        time.sleep(intervallo)

        if interfaccia:
            contatori_now = psutil.net_io_counters(pernic=True)[interfaccia]
        else:
            contatori_now = psutil.net_io_counters()

        bytes_ricevuti = contatori_now.bytes_recv - contatori_prev.bytes_recv
        bytes_inviati = contatori_now.bytes_sent - contatori_prev.bytes_sent
        pkts_rx = contatori_now.packets_recv - contatori_prev.packets_recv
        pkts_tx = contatori_now.packets_sent - contatori_prev.packets_sent

        # Converti in velocita (per secondo)
        download_speed = bytes_ricevuti / intervallo
        upload_speed = bytes_inviati / intervallo

        print(f"{time.strftime('%H:%M:%S'):<12} "
              f"{formatta_byte(download_speed)}/s{'':<5} "
              f"{formatta_byte(upload_speed)}/s{'':<5} "
              f"{pkts_rx:<15} {pkts_tx:<15}")

        contatori_prev = contatori_now


def formatta_byte(byte_value):
    """Formatta i bytes in formato leggibile."""
    for unita in ["B", "KB", "MB", "GB"]:
        if byte_value < 1024:
            return f"{byte_value:.1f} {unita}"
        byte_value /= 1024
    return f"{byte_value:.1f} TB"


# monitora_banda(intervallo=2, durata=30)
```

### Alert Integration

```python
import requests
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime


class SistemaAllarmi:
    """Sistema di notifiche per il monitoraggio di rete."""

    def __init__(self):
        self.canali = []

    def aggiungi_webhook_slack(self, webhook_url):
        """Aggiunge un canale di notifica Slack."""
        self.canali.append(("slack", webhook_url))

    def aggiungi_email(self, smtp_host, smtp_porta, mittente, password, destinatari):
        """Aggiunge un canale di notifica email."""
        self.canali.append(("email", {
            "host": smtp_host,
            "porta": smtp_porta,
            "mittente": mittente,
            "password": password,
            "destinatari": destinatari,
        }))

    def aggiungi_webhook_teams(self, webhook_url):
        """Aggiunge un canale di notifica Microsoft Teams."""
        self.canali.append(("teams", webhook_url))

    def invia_allarme(self, titolo, messaggio, severita="warning"):
        """Invia un allarme a tutti i canali configurati."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for tipo_canale, config in self.canali:
            try:
                if tipo_canale == "slack":
                    self._invia_slack(config, titolo, messaggio, severita, timestamp)
                elif tipo_canale == "email":
                    self._invia_email(config, titolo, messaggio, severita, timestamp)
                elif tipo_canale == "teams":
                    self._invia_teams(config, titolo, messaggio, severita, timestamp)
            except Exception as e:
                print(f"Errore invio allarme via {tipo_canale}: {e}")

    def _invia_slack(self, webhook_url, titolo, messaggio, severita, timestamp):
        colori = {"critical": "#FF0000", "warning": "#FFA500", "info": "#36A64F"}
        payload = {
            "attachments": [{
                "color": colori.get(severita, "#808080"),
                "title": titolo,
                "text": messaggio,
                "footer": f"Network Monitor | {timestamp}",
            }]
        }
        requests.post(webhook_url, json=payload, timeout=10)

    def _invia_email(self, config, titolo, messaggio, severita, timestamp):
        corpo = f"Severita: {severita.upper()}\nData: {timestamp}\n\n{messaggio}"
        msg = MIMEText(corpo, "plain", "utf-8")
        msg["Subject"] = f"[{severita.upper()}] {titolo}"
        msg["From"] = config["mittente"]
        msg["To"] = ", ".join(config["destinatari"])

        with smtplib.SMTP(config["host"], config["porta"]) as server:
            server.starttls()
            server.login(config["mittente"], config["password"])
            server.send_message(msg)

    def _invia_teams(self, webhook_url, titolo, messaggio, severita, timestamp):
        colori = {"critical": "FF0000", "warning": "FFA500", "info": "36A64F"}
        payload = {
            "@type": "MessageCard",
            "themeColor": colori.get(severita, "808080"),
            "summary": titolo,
            "sections": [{
                "activityTitle": titolo,
                "facts": [
                    {"name": "Severita", "value": severita.upper()},
                    {"name": "Timestamp", "value": timestamp},
                ],
                "text": messaggio,
            }]
        }
        requests.post(webhook_url, json=payload, timeout=10)


# Esempio di integrazione nel monitoraggio
allarmi = SistemaAllarmi()
allarmi.aggiungi_webhook_slack("https://hooks.slack.com/services/xxx/yyy/zzz")
allarmi.aggiungi_email(
    "smtp.gmail.com", 587, "monitor@esempio.it",
    "app_password", ["admin@esempio.it", "team@esempio.it"]
)

# Utilizzo durante il monitoraggio
def monitora_con_allarmi(host, porta, nome_servizio):
    """Esempio di monitoraggio con allarmi integrati."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((host, porta))
            print(f"[OK] {nome_servizio} raggiungibile")
    except (socket.timeout, ConnectionRefusedError, OSError):
        allarmi.invia_allarme(
            titolo=f"Servizio non raggiungibile: {nome_servizio}",
            messaggio=(
                f"Il servizio {nome_servizio} ({host}:{porta}) "
                f"non risponde. Verificare immediatamente."
            ),
            severita="critical"
        )
```

---

## Best Practices

1. **Impostare sempre i timeout.** Ogni operazione di rete deve avere un timeout esplicito. Senza timeout, un'applicazione puo restare bloccata indefinitamente in attesa di una risposta che non arrivera mai. Usare `socket.settimeout()`, il parametro `timeout` di `requests`, o `asyncio.wait_for()` per le operazioni asincrone.

2. **Usare i context manager per le risorse di rete.** Socket, connessioni SSH, sessioni HTTP e client SFTP devono sempre essere gestiti con l'istruzione `with`. Questo garantisce che le risorse vengano rilasciate correttamente anche in caso di eccezioni, evitando file descriptor orfani e connessioni appese.

3. **Gestire tutte le eccezioni di rete in modo specifico.** La rete e intrinsecamente inaffidabile. Distinguere tra `ConnectionRefusedError`, `socket.timeout`, `ConnectionResetError` e `OSError` generici permette di implementare strategie di recupero appropriate per ogni scenario. Non catturare mai `Exception` generico senza loggare il tipo specifico dell'errore.

4. **Implementare meccanismi di retry con backoff esponenziale.** Le connessioni di rete possono fallire temporaneamente per mille motivi. Un sistema robusto ritenta le operazioni con intervalli crescenti tra i tentativi (ad esempio 1s, 2s, 4s, 8s). Librerie come `urllib3.Retry` e `tenacity` forniscono implementazioni pronte all'uso.

5. **Non esporre mai credenziali nel codice sorgente.** Password, API key, community string SNMP e chiavi private non devono mai essere scritte direttamente nel codice. Usare variabili d'ambiente (`os.environ`), file di configurazione esterni (non versionati) o strumenti dedicati come vault. Questo vale in modo critico per le community string SNMP "private" che danno accesso in scrittura ai dispositivi.

6. **Validare e sanitizzare tutti i dati ricevuti dalla rete.** I dati provenienti dalla rete sono per definizione non fidati. Verificare sempre la dimensione dei dati ricevuti (per evitare esaurimento della memoria), il formato atteso (JSON valido, encoding corretto) e il contenuto (injection attacks). Mai fidarsi del contenuto di un header o di un campo ricevuto da un peer remoto.

7. **Usare TLS/SSL per tutte le comunicazioni sensibili.** Ogni trasferimento di dati che include credenziali, dati personali o informazioni riservate deve essere protetto con TLS. Usare `ssl.create_default_context()` per i socket, HTTPS per le richieste HTTP, SFTP invece di FTP, e SSH invece di Telnet. Verificare sempre i certificati in produzione e non disabilitare mai la verifica SSL se non in ambienti di test controllati.

8. **Limitare la concorrenza nelle operazioni di rete.** Aprire troppi socket o connessioni simultanee puo esaurire i file descriptor del sistema operativo, sovraccaricare il target o causare comportamenti imprevedibili. Usare `asyncio.Semaphore`, pool di connessioni o `ThreadPoolExecutor` con un numero massimo di worker ragionevole. Per le scansioni di rete, limitare il rate per non sovraccaricare la rete e i dispositivi target.

9. **Implementare logging strutturato per le operazioni di rete.** Ogni connessione, errore, retry e operazione significativa deve essere loggata con timestamp, indirizzo remoto, protocollo e risultato. Questo e fondamentale per il debugging e l'analisi post-incidente. Usare il modulo `logging` con livelli appropriati (DEBUG per il traffico dettagliato, INFO per le operazioni riuscite, WARNING per i retry, ERROR per i fallimenti).

10. **Usare asyncio per operazioni di rete su scala.** Per applicazioni che gestiscono decine o centinaia di connessioni simultanee, `asyncio` e quasi sempre la scelta migliore rispetto al threading. Un singolo thread con event loop asyncio puo gestire decine di migliaia di connessioni TCP con un overhead di memoria minimo (pochi KB per connessione contro ~8 MB per thread). Usare `asyncio.Semaphore` per limitare la concorrenza e prevenire l'esaurimento dei file descriptor o il sovraccarico del target. Per operazioni CPU-bound (crittografia, compressione), delegare a `asyncio.to_thread()` o a un `ProcessPoolExecutor`.

11. **Scegliere il livello di astrazione appropriato.** Non usare socket grezzi quando `httpx` risolve il problema. Non usare `requests` quando serve concorrenza asincrona. Non usare `asyncio` per uno script che fa tre richieste HTTP sequenziali. Il livello giusto dipende dal contesto: socket per protocolli custom e debugging di basso livello, librerie specializzate (httpx, paramiko, dnspython) per protocolli standard, framework (aiohttp, gRPC) per architetture di servizi. Sovra-ingegnerizzare il livello di astrazione aggiunge complessita senza beneficio.

12. **Rispettare le normative e l'etica nel network scanning.** La scansione di rete e l'analisi dei pacchetti possono avere implicazioni legali significative. Eseguire scansioni solo su reti e sistemi per i quali si ha esplicita autorizzazione. In ambienti aziendali, documentare le attivita di scansione e ottenere l'approvazione preventiva. Strumenti come Nmap e scapy sono potenti ma il loro uso improprio puo violare leggi sulla sicurezza informatica.

---

## asyncio.streams — Networking Asincrono

Il modulo `asyncio.streams` fornisce API ad alto livello per networking asincrono, astraendo i socket grezzi con reader/writer basati su stream.

### Server TCP asincrono

```python
import asyncio
import logging
from datetime import datetime

log = logging.getLogger(__name__)


async def gestisci_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Handler per ogni client connesso."""
    addr = writer.get_extra_info("peername")
    log.info("Nuova connessione da %s", addr)

    try:
        while True:
            dati = await asyncio.wait_for(reader.readline(), timeout=30.0)
            if not dati:
                break

            messaggio = dati.decode("utf-8").strip()
            log.debug("Ricevuto da %s: %s", addr, messaggio)

            # Echo con timestamp
            risposta = f"[{datetime.now():%H:%M:%S}] {messaggio}\n"
            writer.write(risposta.encode("utf-8"))
            await writer.drain()
    except asyncio.TimeoutError:
        log.info("Timeout per %s", addr)
    except ConnectionResetError:
        log.info("Connessione resettata da %s", addr)
    finally:
        writer.close()
        await writer.wait_closed()
        log.info("Connessione chiusa: %s", addr)


async def avvia_server(host: str = "0.0.0.0", porta: int = 8888):
    """Avvia un server TCP asincrono."""
    server = await asyncio.start_server(
        gestisci_client, host, porta,
        limit=2**16,  # buffer size per stream
    )

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    log.info("Server in ascolto su %s", addrs)

    async with server:
        await server.serve_forever()


# asyncio.run(avvia_server())
```

### Protocolli e Trasporti asyncio

Oltre alle stream API ad alto livello, asyncio offre un'architettura a basso livello basata su **Protocol** e **Transport**, ispirata al pattern di Twisted. Questa separazione permette di scrivere protocolli riutilizzabili indipendenti dal meccanismo di trasporto sottostante (TCP, UDP, SSL, pipe).

**Transport** gestisce il *come* i dati vengono inviati e ricevuti: buffer, connessione, chiusura. **Protocol** gestisce il *cosa*: parsing dei dati, logica applicativa, gestione degli errori. Questa separazione e utile per implementare protocolli custom complessi dove la gestione del framing e critica.

```python
import asyncio


class ProtocolloLinea(asyncio.Protocol):
    """Protocol che processa messaggi delimitati da newline."""

    def __init__(self):
        self._buffer = b""
        self._transport: asyncio.Transport | None = None

    def connection_made(self, transport: asyncio.Transport):
        self._transport = transport
        peer = transport.get_extra_info("peername")
        print(f"Connessione da {peer}")

    def data_received(self, data: bytes):
        self._buffer += data
        # Processa linee complete dal buffer
        while b"\n" in self._buffer:
            linea, self._buffer = self._buffer.split(b"\n", 1)
            self._processa_linea(linea.decode("utf-8").strip())

    def _processa_linea(self, linea: str):
        """Logica applicativa per ogni linea ricevuta."""
        if linea.upper() == "QUIT":
            self._transport.write(b"Arrivederci!\n")
            self._transport.close()
            return

        risposta = f"Ricevuto: {linea}\n"
        self._transport.write(risposta.encode("utf-8"))

    def connection_lost(self, exc: Exception | None):
        if exc:
            print(f"Errore: {exc}")
        print("Connessione terminata")


async def avvia_server_protocol(host: str = "0.0.0.0", porta: int = 8887):
    """Avvia un server usando il pattern Protocol/Transport."""
    loop = asyncio.get_running_loop()
    server = await loop.create_server(
        ProtocolloLinea,  # Factory: crea una nuova istanza per ogni connessione
        host, porta,
    )
    print(f"Server Protocol/Transport su {host}:{porta}")

    async with server:
        await server.serve_forever()


# asyncio.run(avvia_server_protocol())
```

La scelta tra stream API (`asyncio.open_connection`/`start_server`) e Protocol/Transport dipende dalla complessita del protocollo: le stream API sono piu semplici per protocolli basati su richiesta/risposta, mentre Protocol/Transport offre controllo piu fine per protocolli con framing complesso, gestione di backpressure e integrazione con trasporti custom (es. serial, named pipes).

### Client TCP asincrono con pool di connessioni

```python
import asyncio
from contextlib import asynccontextmanager


class PoolConnessioni:
    """Pool di connessioni TCP asincrone con riutilizzo."""

    def __init__(self, host: str, porta: int, max_conn: int = 10):
        self.host = host
        self.porta = porta
        self._pool: asyncio.Queue[tuple[asyncio.StreamReader, asyncio.StreamWriter]] = (
            asyncio.Queue(maxsize=max_conn)
        )
        self._dimensione = 0
        self._max = max_conn

    async def _crea_connessione(self):
        reader, writer = await asyncio.open_connection(self.host, self.porta)
        self._dimensione += 1
        return reader, writer

    @asynccontextmanager
    async def connessione(self):
        """Context manager che preleva e restituisce una connessione al pool."""
        try:
            reader, writer = self._pool.get_nowait()
        except asyncio.QueueEmpty:
            if self._dimensione < self._max:
                reader, writer = await self._crea_connessione()
            else:
                reader, writer = await self._pool.get()

        try:
            yield reader, writer
        finally:
            if not writer.is_closing():
                await self._pool.put((reader, writer))
            else:
                self._dimensione -= 1

    async def chiudi_tutte(self):
        while not self._pool.empty():
            _, writer = await self._pool.get()
            writer.close()
            await writer.wait_closed()
```

### Server UDP asincrono

```python
import asyncio


class ProtocolloUDP(asyncio.DatagramProtocol):
    """Server UDP asincrono basato su protocol."""

    def connection_made(self, transport: asyncio.DatagramTransport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str, int]):
        messaggio = data.decode("utf-8")
        print(f"Ricevuto da {addr}: {messaggio}")
        # Echo
        self.transport.sendto(f"ACK: {messaggio}".encode("utf-8"), addr)


async def avvia_server_udp(host: str = "0.0.0.0", porta: int = 9999):
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        ProtocolloUDP, local_addr=(host, porta)
    )
    print(f"Server UDP in ascolto su {host}:{porta}")

    try:
        await asyncio.sleep(3600)  # Esegue per 1 ora
    finally:
        transport.close()
```

---

## HTTP/2 con httpx e h2

HTTP/2 offre multiplexing delle richieste su una singola connessione TCP, header compression (HPACK) e server push. `httpx` supporta HTTP/2 nativamente.

```bash
pip install httpx[http2]
```

```python
import httpx
import asyncio


async def demo_http2():
    """Dimostra le funzionalita HTTP/2 di httpx."""
    async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
        # La connessione negozia automaticamente HTTP/2 se il server lo supporta
        risposta = await client.get("https://httpbin.org/get")
        print(f"Protocollo: {risposta.http_version}")  # HTTP/2
        print(f"Stato: {risposta.status_code}")

        # Multiplexing — richieste parallele sulla stessa connessione
        urls = [
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
        ]
        tasks = [client.get(url) for url in urls]
        risposte = await asyncio.gather(*tasks)
        for r in risposte:
            print(f"  {r.url} — {r.status_code} ({r.http_version})")


asyncio.run(demo_http2())
```

### Confronto HTTP/1.1 vs HTTP/2

| Caratteristica | HTTP/1.1 | HTTP/2 |
|----------------|----------|--------|
| Connessioni per host | 6 (tipico) | 1 (multiplexed) |
| Header | Testo, ripetuti | Compressi (HPACK) |
| Request/Response | Sequenziale per connessione | Parallelo (streams) |
| Server Push | Non supportato | Supportato |
| Overhead TCP handshake | Per ogni connessione | Una sola volta |
| Libreria Python | requests, urllib3 | httpx con `http2=True` |

### Streaming con httpx

```python
import httpx


async def scarica_file_grande(url: str, destinazione: str):
    """Scarica un file grande in streaming senza caricarlo in memoria."""
    async with httpx.AsyncClient(http2=True) as client:
        async with client.stream("GET", url) as risposta:
            risposta.raise_for_status()
            with open(destinazione, "wb") as f:
                async for chunk in risposta.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
```

---

## gRPC con grpcio e Protocol Buffers

gRPC e un framework RPC ad alte prestazioni sviluppato da Google. Usa Protocol Buffers (protobuf) come formato di serializzazione e HTTP/2 come trasporto.

```bash
pip install grpcio grpcio-tools
```

### Definizione del servizio (.proto)

```protobuf
// servizio.proto
syntax = "proto3";

package monitoraggio;

service MonitoraggioService {
    // Unary RPC
    rpc OttieniStato (RichiestaStato) returns (RispostaStato);

    // Server streaming RPC
    rpc StreamMetriche (RichiestaMetriche) returns (stream Metrica);
}

message RichiestaStato {
    string hostname = 1;
}

message RispostaStato {
    string hostname = 1;
    double cpu_percent = 2;
    double memoria_percent = 3;
    int64 uptime_secondi = 4;
    bool attivo = 5;
}

message RichiestaMetriche {
    string hostname = 1;
    int32 intervallo_secondi = 2;
}

message Metrica {
    string nome = 1;
    double valore = 2;
    int64 timestamp = 3;
}
```

### Generazione del codice Python

```bash
python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    servizio.proto
# Genera: servizio_pb2.py e servizio_pb2_grpc.py
```

### Server gRPC

```python
import grpc
from concurrent import futures
import time
import psutil

import servizio_pb2
import servizio_pb2_grpc


class MonitoraggioServicer(servizio_pb2_grpc.MonitoraggioServiceServicer):

    def OttieniStato(self, request, context):
        """Unary RPC — restituisce lo stato del server."""
        return servizio_pb2.RispostaStato(
            hostname=request.hostname,
            cpu_percent=psutil.cpu_percent(interval=0.5),
            memoria_percent=psutil.virtual_memory().percent,
            uptime_secondi=int(time.time() - psutil.boot_time()),
            attivo=True,
        )

    def StreamMetriche(self, request, context):
        """Server streaming — invia metriche periodicamente."""
        while context.is_active():
            yield servizio_pb2.Metrica(
                nome="cpu_percent",
                valore=psutil.cpu_percent(interval=1),
                timestamp=int(time.time()),
            )
            time.sleep(request.intervallo_secondi)


def avvia_server(porta: int = 50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servizio_pb2_grpc.add_MonitoraggioServiceServicer_to_server(
        MonitoraggioServicer(), server
    )
    server.add_insecure_port(f"[::]:{porta}")
    server.start()
    print(f"Server gRPC in ascolto su porta {porta}")
    server.wait_for_termination()
```

### Client gRPC

```python
import grpc
import servizio_pb2
import servizio_pb2_grpc


def client_unary():
    """Chiamata unary — richiesta/risposta singola."""
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = servizio_pb2_grpc.MonitoraggioServiceStub(channel)
        risposta = stub.OttieniStato(
            servizio_pb2.RichiestaStato(hostname="server01")
        )
        print(f"CPU: {risposta.cpu_percent}%")
        print(f"Memoria: {risposta.memoria_percent}%")


def client_streaming():
    """Streaming — riceve metriche in tempo reale."""
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = servizio_pb2_grpc.MonitoraggioServiceStub(channel)
        stream = stub.StreamMetriche(
            servizio_pb2.RichiestaMetriche(hostname="server01", intervallo_secondi=5)
        )
        for metrica in stream:
            print(f"[{metrica.timestamp}] {metrica.nome}: {metrica.valore}")
```

### gRPC Asincrono con grpc.aio

Il modulo `grpc.aio` fornisce un'implementazione nativa asyncio per gRPC, eliminando la necessita di pool di thread e migliorando le prestazioni per server ad alta concorrenza.

```python
import grpc.aio
import asyncio
import servizio_pb2
import servizio_pb2_grpc


class MonitoraggioAsyncServicer(servizio_pb2_grpc.MonitoraggioServiceServicer):
    """Servicer gRPC completamente asincrono."""

    async def OttieniStato(self, request, context):
        """Unary RPC asincrono."""
        import psutil
        import time

        # Le operazioni possono essere asincrone
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent

        return servizio_pb2.RispostaStato(
            hostname=request.hostname,
            cpu_percent=cpu,
            memoria_percent=mem,
            uptime_secondi=int(time.time() - psutil.boot_time()),
            attivo=True,
        )

    async def StreamMetriche(self, request, context):
        """Server streaming RPC asincrono."""
        import psutil
        import time

        while not context.cancelled():
            yield servizio_pb2.Metrica(
                nome="cpu_percent",
                valore=psutil.cpu_percent(interval=0.5),
                timestamp=int(time.time()),
            )
            await asyncio.sleep(request.intervallo_secondi)


async def avvia_server_async(porta: int = 50051):
    """Avvia un server gRPC completamente asincrono."""
    server = grpc.aio.server()
    servizio_pb2_grpc.add_MonitoraggioServiceServicer_to_server(
        MonitoraggioAsyncServicer(), server
    )
    server.add_insecure_port(f"[::]:{porta}")

    await server.start()
    print(f"Server gRPC async in ascolto su porta {porta}")
    await server.wait_for_termination()


# asyncio.run(avvia_server_async())
```

#### Client gRPC asincrono

```python
import grpc.aio
import asyncio
import servizio_pb2
import servizio_pb2_grpc


async def client_async():
    """Client gRPC completamente asincrono."""
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = servizio_pb2_grpc.MonitoraggioServiceStub(channel)

        # Unary call asincrono
        risposta = await stub.OttieniStato(
            servizio_pb2.RichiestaStato(hostname="server01")
        )
        print(f"CPU: {risposta.cpu_percent}%")
        print(f"Memoria: {risposta.memoria_percent}%")

        # Server streaming asincrono con timeout
        try:
            stream = stub.StreamMetriche(
                servizio_pb2.RichiestaMetriche(
                    hostname="server01", intervallo_secondi=2
                ),
                timeout=30,  # Timeout dopo 30 secondi
            )
            async for metrica in stream:
                print(f"[{metrica.timestamp}] {metrica.nome}: {metrica.valore:.1f}")
        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                print("Timeout raggiunto, stream chiuso")
            else:
                raise


asyncio.run(client_async())
```

### gRPC Bidirectional Streaming

Il bidirectional streaming consente a client e server di inviare messaggi indipendentemente l'uno dall'altro, ideale per scenari di comunicazione real-time come chat, telemetria interattiva e pipeline di dati.

```protobuf
// Aggiungere al file .proto esistente
service ChatService {
    // Bidirectional streaming RPC
    rpc Chat (stream MessaggioChat) returns (stream MessaggioChat);
}

message MessaggioChat {
    string utente = 1;
    string testo = 2;
    int64 timestamp = 3;
}
```

```python
import grpc.aio
import asyncio
import time

# Supponendo che chat_pb2 e chat_pb2_grpc siano generati dal .proto sopra
import chat_pb2
import chat_pb2_grpc


class ChatServicer(chat_pb2_grpc.ChatServiceServicer):
    """Server bidirezionale: riceve messaggi e li trasmette a tutti i client."""

    def __init__(self):
        self._clients: list[asyncio.Queue] = []

    async def Chat(self, request_iterator, context):
        """Bidirectional streaming: ogni client riceve i messaggi degli altri."""
        coda = asyncio.Queue()
        self._clients.append(coda)

        async def leggi_messaggi():
            async for msg in request_iterator:
                print(f"[{msg.utente}] {msg.testo}")
                # Broadcast a tutti i client connessi
                for client_queue in self._clients:
                    if client_queue is not coda:
                        await client_queue.put(msg)

        task_lettura = asyncio.create_task(leggi_messaggi())

        try:
            while not context.cancelled():
                try:
                    msg = await asyncio.wait_for(coda.get(), timeout=1.0)
                    yield msg
                except asyncio.TimeoutError:
                    continue
        finally:
            task_lettura.cancel()
            self._clients.remove(coda)


async def client_bidirezionale(nome_utente: str):
    """Client che invia e riceve messaggi in modo bidirezionale."""
    async with grpc.aio.insecure_channel("localhost:50052") as channel:
        stub = chat_pb2_grpc.ChatServiceStub(channel)

        async def generatore_messaggi():
            """Genera messaggi da inviare al server."""
            messaggi = ["Ciao a tutti!", "Come va?", "Arrivederci!"]
            for testo in messaggi:
                yield chat_pb2.MessaggioChat(
                    utente=nome_utente,
                    testo=testo,
                    timestamp=int(time.time()),
                )
                await asyncio.sleep(2)

        # Avvia lo streaming bidirezionale
        stream = stub.Chat(generatore_messaggi())

        async for risposta in stream:
            print(f"  Ricevuto da {risposta.utente}: {risposta.testo}")
```

### Interceptor gRPC per Logging e Autenticazione

```python
import grpc
import grpc.aio
import time
import logging

log = logging.getLogger(__name__)


class LoggingInterceptor(grpc.aio.UnaryUnaryClientInterceptor):
    """Interceptor client che logga tempi di risposta e errori."""

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        metodo = client_call_details.method
        inizio = time.perf_counter()

        try:
            risposta = await continuation(client_call_details, request)
            durata = (time.perf_counter() - inizio) * 1000
            log.info("gRPC %s completato in %.1fms", metodo, durata)
            return risposta
        except grpc.aio.AioRpcError as e:
            durata = (time.perf_counter() - inizio) * 1000
            log.error("gRPC %s fallito: %s (%.1fms)", metodo, e.code(), durata)
            raise


class AuthInterceptor(grpc.aio.UnaryUnaryClientInterceptor):
    """Interceptor che aggiunge un token di autenticazione ai metadata."""

    def __init__(self, token: str):
        self._token = token

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        # Aggiunge il token ai metadata della richiesta
        metadata = list(client_call_details.metadata or [])
        metadata.append(("authorization", f"Bearer {self._token}"))

        new_details = grpc.aio.ClientCallDetails(
            method=client_call_details.method,
            timeout=client_call_details.timeout,
            metadata=metadata,
            credentials=client_call_details.credentials,
            wait_for_ready=client_call_details.wait_for_ready,
        )
        return await continuation(new_details, request)


# Uso degli interceptor
async def client_con_interceptor():
    interceptors = [
        LoggingInterceptor(),
        AuthInterceptor("mio_token_jwt_qui"),
    ]
    async with grpc.aio.insecure_channel(
        "localhost:50051",
        interceptors=interceptors,
    ) as channel:
        stub = servizio_pb2_grpc.MonitoraggioServiceStub(channel)
        risposta = await stub.OttieniStato(
            servizio_pb2.RichiestaStato(hostname="server01")
        )
        print(f"CPU: {risposta.cpu_percent}%")
```

---

## mTLS — Mutual TLS con cryptography

Il mutual TLS (mTLS) richiede che sia il client sia il server presentino un certificato, garantendo autenticazione bidirezionale. E lo standard per la comunicazione tra microservizi in ambienti zero-trust.

```python
import ssl
import socket


def crea_contesto_mtls_server(
    cert_server: str,
    key_server: str,
    ca_cert: str,
) -> ssl.SSLContext:
    """Crea un contesto SSL per un server con mTLS."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=cert_server, keyfile=key_server)
    ctx.load_verify_locations(cafile=ca_cert)
    ctx.verify_mode = ssl.CERT_REQUIRED  # Richiede certificato client
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    return ctx


def crea_contesto_mtls_client(
    cert_client: str,
    key_client: str,
    ca_cert: str,
) -> ssl.SSLContext:
    """Crea un contesto SSL per un client con mTLS."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_cert_chain(certfile=cert_client, keyfile=key_client)
    ctx.load_verify_locations(cafile=ca_cert)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    return ctx


# Server mTLS
def server_mtls(host: str, porta: int, contesto: ssl.SSLContext):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, porta))
        sock.listen(5)

        with contesto.wrap_socket(sock, server_side=True) as ssock:
            print(f"Server mTLS in ascolto su {host}:{porta}")
            conn, addr = ssock.accept()
            with conn:
                # Verifica certificato client
                cert_client = conn.getpeercert()
                cn = dict(x[0] for x in cert_client["subject"])["commonName"]
                print(f"Client autenticato: {cn}")
                dati = conn.recv(4096)
                conn.sendall(b"ACK: " + dati)
```

### Generazione certificati con cryptography

```python
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from datetime import datetime, timedelta, timezone


def genera_ca(cn: str = "MiaCA") -> tuple[ec.EllipticCurvePrivateKey, x509.Certificate]:
    """Genera una CA root per firmare certificati."""
    chiave = ec.generate_private_key(ec.SECP384R1())
    soggetto = emittente = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, cn),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Lab mTLS"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(soggetto)
        .issuer_name(emittente)
        .public_key(chiave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(chiave, hashes.SHA384())
    )
    return chiave, cert


def genera_certificato(
    cn: str,
    ca_key: ec.EllipticCurvePrivateKey,
    ca_cert: x509.Certificate,
    san_dns: list[str] | None = None,
) -> tuple[ec.EllipticCurvePrivateKey, x509.Certificate]:
    """Genera un certificato firmato dalla CA."""
    chiave = ec.generate_private_key(ec.SECP384R1())
    soggetto = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])

    builder = (
        x509.CertificateBuilder()
        .subject_name(soggetto)
        .issuer_name(ca_cert.subject)
        .public_key(chiave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
    )

    if san_dns:
        nomi = [x509.DNSName(d) for d in san_dns]
        builder = builder.add_extension(
            x509.SubjectAlternativeName(nomi), critical=False
        )

    cert = builder.sign(ca_key, hashes.SHA384())
    return chiave, cert
```

### Ispezione Certificati TLS Remoti

L'ispezione programmatica dei certificati TLS e fondamentale per il monitoraggio della scadenza, la verifica della catena di fiducia e l'audit di sicurezza delle connessioni crittografate.

#### Recupero e analisi del certificato

```python
import ssl
import socket
from datetime import datetime, timezone
from cryptography import x509
from cryptography.hazmat.primitives import hashes


def ispeziona_certificato(hostname: str, porta: int = 443) -> dict:
    """Recupera e analizza il certificato TLS di un host remoto."""
    ctx = ssl.create_default_context()

    with socket.create_connection((hostname, porta), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
            # Informazioni sulla connessione TLS
            cipher = ssock.cipher()
            tls_version = ssock.version()

            # Certificato in formato DER
            cert_der = ssock.getpeercert(binary_form=True)

            # Certificato in formato dizionario Python
            cert_dict = ssock.getpeercert()

    # Parsing con cryptography per dettagli avanzati
    cert = x509.load_der_x509_certificate(cert_der)

    # Estrazione Subject Alternative Names (SAN)
    try:
        san_ext = cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )
        san_nomi = san_ext.value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        san_nomi = []

    # Calcolo fingerprint
    fingerprint_sha256 = cert.fingerprint(hashes.SHA256()).hex(":")

    # Giorni alla scadenza
    now = datetime.now(timezone.utc)
    scadenza = cert.not_valid_after_utc
    giorni_rimanenti = (scadenza - now).days

    return {
        "hostname": hostname,
        "subject": cert.subject.rfc4514_string(),
        "issuer": cert.issuer.rfc4514_string(),
        "serial": cert.serial_number,
        "not_before": cert.not_valid_before_utc.isoformat(),
        "not_after": scadenza.isoformat(),
        "giorni_rimanenti": giorni_rimanenti,
        "san": san_nomi,
        "fingerprint_sha256": fingerprint_sha256,
        "tls_version": tls_version,
        "cipher_suite": cipher[0] if cipher else "N/A",
        "key_bits": cipher[2] if cipher else 0,
        "signature_algorithm": cert.signature_algorithm_oid.dotted_string,
    }


# Uso
info = ispeziona_certificato("github.com")
print(f"Subject: {info['subject']}")
print(f"Issuer: {info['issuer']}")
print(f"Scadenza: {info['not_after']}")
print(f"Giorni rimanenti: {info['giorni_rimanenti']}")
print(f"TLS: {info['tls_version']} / {info['cipher_suite']}")
print(f"SAN: {', '.join(info['san'][:5])}")
print(f"SHA-256: {info['fingerprint_sha256']}")
```

#### Monitoraggio scadenza certificati

```python
import ssl
import socket
from datetime import datetime, timezone
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class StatoCertificato:
    hostname: str
    giorni_rimanenti: int
    scadenza: str
    issuer: str
    errore: str = ""

    @property
    def stato(self) -> str:
        if self.errore:
            return "ERRORE"
        if self.giorni_rimanenti < 0:
            return "SCADUTO"
        if self.giorni_rimanenti < 14:
            return "CRITICO"
        if self.giorni_rimanenti < 30:
            return "WARNING"
        return "OK"


def controlla_certificato(hostname: str, porta: int = 443) -> StatoCertificato:
    """Controlla lo stato di scadenza di un certificato TLS."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, porta), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        # Parsing data di scadenza
        scadenza_str = cert["notAfter"]
        scadenza = datetime.strptime(scadenza_str, "%b %d %H:%M:%S %Y %Z")
        scadenza = scadenza.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        giorni = (scadenza - now).days

        # Estrazione issuer
        issuer_parts = dict(x[0] for x in cert.get("issuer", ()))
        issuer = issuer_parts.get("organizationName", "Sconosciuto")

        return StatoCertificato(
            hostname=hostname,
            giorni_rimanenti=giorni,
            scadenza=scadenza.strftime("%Y-%m-%d"),
            issuer=issuer,
        )
    except Exception as e:
        return StatoCertificato(
            hostname=hostname,
            giorni_rimanenti=-1,
            scadenza="N/A",
            issuer="N/A",
            errore=str(e),
        )


def monitora_certificati(hosts: list[str], max_workers: int = 10):
    """Monitora i certificati TLS di una lista di host in parallelo."""
    risultati = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(controlla_certificato, host): host
            for host in hosts
        }
        for future in as_completed(futures):
            risultati.append(future.result())

    # Report ordinato per giorni rimanenti
    risultati.sort(key=lambda r: r.giorni_rimanenti)

    print(f"\n{'Hostname':<30} {'Stato':<10} {'Giorni':<8} "
          f"{'Scadenza':<12} {'Issuer':<25}")
    print("-" * 95)
    for r in risultati:
        print(f"{r.hostname:<30} {r.stato:<10} {r.giorni_rimanenti:<8} "
              f"{r.scadenza:<12} {r.issuer:<25}")

    # Alert per certificati in scadenza
    critici = [r for r in risultati if r.stato in ("CRITICO", "SCADUTO")]
    if critici:
        print(f"\n ATTENZIONE: {len(critici)} certificati richiedono intervento!")

    return risultati


# Uso
domini = [
    "github.com", "python.org", "pypi.org",
    "docs.python.org", "fastapi.tiangolo.com",
]
monitora_certificati(domini)
```

#### Verifica della catena di certificati

```python
import ssl
import socket
from cryptography import x509
from cryptography.hazmat.primitives import serialization


def ottieni_catena_certificati(hostname: str, porta: int = 443) -> list[x509.Certificate]:
    """Recupera l'intera catena di certificati da un server TLS.

    Nota: SSLSocket.get_unverified_chain() richiede Python >= 3.13.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # Solo per ispezione, non per connessioni di produzione

    with socket.create_connection((hostname, porta), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
            certs_der = ssock.get_unverified_chain()

    if not certs_der:
        return []

    catena = []
    for cert_der in certs_der:
        cert = x509.load_der_x509_certificate(cert_der.public_bytes(serialization.Encoding.DER))
        catena.append(cert)

    return catena


def stampa_catena(hostname: str):
    """Stampa la catena di certificati di un host."""
    catena = ottieni_catena_certificati(hostname)

    print(f"\nCatena certificati per {hostname} ({len(catena)} certificati):")
    for i, cert in enumerate(catena):
        prefisso = "  " * i + ("└─ " if i > 0 else "")
        cn = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
        nome = cn[0].value if cn else "N/A"
        scadenza = cert.not_valid_after_utc.strftime("%Y-%m-%d")

        is_ca = False
        try:
            bc = cert.extensions.get_extension_for_class(x509.BasicConstraints)
            is_ca = bc.value.ca
        except x509.ExtensionNotFound:
            pass

        tipo = "CA" if is_ca else "End-Entity"
        print(f"{prefisso}[{tipo}] {nome} (scade: {scadenza})")
```

---

## DNS Avanzato — DNSSEC e DoH

### Verifica DNSSEC

```python
import dns.resolver
import dns.dnssec
import dns.name
import dns.rdatatype


def verifica_dnssec(dominio: str) -> bool:
    """Verifica la catena DNSSEC di un dominio."""
    nome = dns.name.from_text(dominio)
    resolver = dns.resolver.Resolver()
    resolver.use_edns(edns=0, ednsflags=dns.flags.DO, payload=4096)

    try:
        risposta = resolver.resolve(dominio, "A")
        rrset = risposta.rrset

        # Ottenere i record DNSKEY
        dnskey_risposta = resolver.resolve(dominio, "DNSKEY")
        dnskey_rrset = dnskey_risposta.rrset

        # Ottenere i record RRSIG per la validazione
        rrsig_risposta = resolver.resolve(dominio, "RRSIG")

        print(f"DNSSEC abilitato per {dominio}")
        print(f"  Record A: {[str(r) for r in rrset]}")
        print(f"  DNSKEY trovati: {len(dnskey_rrset)}")
        return True

    except dns.resolver.NoAnswer:
        print(f"DNSSEC non configurato per {dominio}")
        return False
    except Exception as e:
        print(f"Errore verifica DNSSEC: {e}")
        return False
```

### DNS over HTTPS (DoH)

```python
import httpx
import dns.message
import dns.rdatatype
import base64


async def query_doh(
    dominio: str,
    tipo: str = "A",
    server_doh: str = "https://1.1.1.1/dns-query",
) -> list[str]:
    """Esegue una query DNS over HTTPS (RFC 8484)."""
    # Costruire il messaggio DNS
    query = dns.message.make_query(dominio, dns.rdatatype.from_text(tipo))
    query_wire = query.to_wire()

    # Encoding base64url per GET (RFC 8484 Section 4.1)
    dns_param = base64.urlsafe_b64encode(query_wire).rstrip(b"=").decode()

    async with httpx.AsyncClient(http2=True) as client:
        risposta = await client.get(
            server_doh,
            params={"dns": dns_param},
            headers={"Accept": "application/dns-message"},
        )
        risposta.raise_for_status()

        msg = dns.message.from_wire(risposta.content)
        risultati = []
        for rrset in msg.answer:
            for rdata in rrset:
                risultati.append(str(rdata))

        return risultati


# asyncio.run(query_doh("python.org", "A"))
```

---

## FAQ

### 1. Quando usare socket grezzi vs asyncio.streams?

Socket grezzi (`socket` stdlib) per controllo granulare a basso livello, protocolli custom, o quando si lavora con UDP. `asyncio.streams` per server/client TCP che devono gestire molte connessioni concorrenti con un'API piu semplice e sicura.

### 2. httpx o requests per nuovi progetti?

`httpx` per nuovi progetti: supporta async, HTTP/2, timeout strutturati e ha un'API quasi identica a `requests`. `requests` resta valido per progetti esistenti e per la sua enorme comunita e middleware di terze parti.

### 3. Quando serve gRPC invece di REST?

gRPC eccelle quando: la comunicazione e tra servizi interni (non browser), la latenza e critica, i contratti di interfaccia devono essere rigorosi (protobuf), o si necessita di streaming bidirezionale. REST resta preferibile per API pubbliche e quando l'interoperabilita con client diversi e prioritaria.

### 4. Come gestisco la verifica dei certificati TLS in Python?

Usare sempre `ssl.create_default_context()` che verifica i certificati di default. Non disabilitare mai `verify_mode` in produzione. Per certificati self-signed in ambienti di test, creare un contesto che carica il CA specifico con `load_verify_locations()`.

### 5. Qual e la differenza tra TCP e UDP per il mio caso d'uso?

TCP per dati che non possono essere persi (HTTP, email, file transfer, database). UDP per dati dove la latenza e piu importante della completezza (DNS, streaming video/audio, monitoraggio real-time, gaming). UDP richiede gestione manuale della perdita pacchetti.

### 6. Come implemento il retry per le connessioni di rete?

Usare `tenacity` con backoff esponenziale e jitter: `@retry(wait=wait_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))`. Per `httpx`, configurare `httpx.HTTPTransport(retries=3)`. Non fare retry su errori 4xx (sono errori del client).

### 7. Come funziona il DNS over HTTPS e perche usarlo?

DoH incapsula le query DNS in richieste HTTPS, criptando il traffico DNS che altrimenti viaggia in chiaro. Previene l'intercettazione e la manipolazione delle risposte DNS. Utile per privacy e per bypassare filtri DNS basati su ispezione del traffico.

### 8. Come monitoro le prestazioni di rete di un'applicazione Python?

Usare `psutil.net_io_counters()` per throughput, `time.perf_counter()` per misurare latenza delle singole operazioni, `asyncio.create_task()` con timeout per rilevare connessioni lente. In produzione, usare metriche Prometheus con historgram per la distribuzione della latenza.

### 9. Qual e il limite di connessioni simultanee?

Dipende dal sistema operativo (file descriptor limit, tipicamente 1024 soft / 65536 hard su Linux). Verificare con `ulimit -n`. Per server ad alta concorrenza, aumentare il limite e usare `asyncio` o `epoll` per gestire migliaia di connessioni.

### 10. Come implemento WebSocket in Python?

Usare la libreria `websockets` per server e client: `async with websockets.serve(handler, host, port)` per il server, `async with websockets.connect(uri)` per il client. Per integrazioni con web framework, FastAPI supporta WebSocket nativamente.

### 11. Qual e la differenza tra WebSocket e Socket.IO?

WebSocket (RFC 6455) e un protocollo di trasporto: fornisce un canale bidirezionale full-duplex su una singola connessione TCP e nulla di piu. Non gestisce riconnessione, routing dei messaggi o raggruppamento dei client. Socket.IO e un protocollo applicativo costruito sopra WebSocket che aggiunge: riconnessione automatica con backoff esponenziale, namespace e stanze (rooms) per organizzare i canali logici di comunicazione, acknowledgement dei messaggi con callback, multiplexing di piu canali sulla stessa connessione, e fallback trasparente a HTTP long-polling quando WebSocket non e disponibile (es. proxy aziendali restrittivi). Se si comunica con un server Socket.IO, il client deve usare la libreria Socket.IO (non un WebSocket puro), perche il protocollo include un framing proprietario. Se il server e WebSocket puro (RFC 6455), usare la libreria `websockets`.

### 12. Quando usare selectors vs select vs asyncio per I/O multiplexing?

`select.select()` funziona su tutti i sistemi operativi ma scala male oltre poche centinaia di socket (O(n) per ogni chiamata, limite di 1024 fd su alcuni sistemi). `selectors` (stdlib) sceglie automaticamente il backend migliore (`epoll` su Linux, `kqueue` su macOS) e scala a O(1) con decine di migliaia di connessioni. `asyncio` costruisce sopra `selectors` aggiungendo coroutine, futures e un ecosistema di librerie compatibili. Per server di produzione, preferire `asyncio` per la sua ergonomia; usare `selectors` direttamente solo quando si ha bisogno di controllo totale sul loop di eventi senza il framework asyncio.

### 13. Come analizzo un file pcap senza installare Wireshark?

Tre opzioni principali: (1) `scapy` con `rdpcap()` per caricare e ispezionare pacchetti singolarmente — potente ma lento per file grandi; (2) `dpkt` per parsing ad alte prestazioni di file pcap con accesso ai campi dei protocolli a basso livello — leggero e senza dipendenze C; (3) `pyshark` che richiede tshark ma offre la stessa profondita di dissection di Wireshark via Python. Per file superiori a 100 MB, preferire `dpkt` per il minor consumo di memoria.

### 14. Come gestisco il FTP sicuro in Python?

Usare `ftplib.FTP_TLS` per FTPS (FTP over TLS): dopo `login()`, chiamare `prot_p()` per attivare la crittografia sul canale dati. Per SFTP (SSH File Transfer Protocol, completamente diverso da FTPS), usare `paramiko.SFTPClient`. SFTP e generalmente preferibile perche opera su una singola connessione SSH crittografata, mentre FTPS richiede porte aggiuntive per i canali dati e ha problemi noti con NAT e firewall. Usare FTP/FTPS solo quando richiesto da sistemi legacy o fornitori esterni.

### 15. Come scelgo tra paramiko, asyncssh e fabric per SSH?

`paramiko` e la libreria di riferimento: sincrona, basso livello, massimo controllo su canali, forwarding, e transport. `asyncssh` e la scelta per operazioni SSH su molti host in parallelo: nativo asyncio, fino a 15 volte piu veloce di paramiko in scenari multihost. `fabric` costruisce su paramiko aggiungendo un'API dichiarativa orientata al deployment e all'esecuzione di comandi su gruppi di server. Per script DevOps e deployment, usare Fabric; per integrazione in applicazioni async, usare asyncssh; per controllo granulare su sessioni SSH, usare paramiko direttamente.

### 16. Come implemento interceptor e autenticazione in gRPC?

Lato client, usare `grpc.aio.UnaryUnaryClientInterceptor` (e le varianti per streaming) per aggiungere metadata come token JWT a ogni richiesta. Lato server, accedere ai metadata nel `context` del servicer: `token = dict(context.invocation_metadata()).get("authorization")`. Per autenticazione mutua, usare credenziali TLS con `grpc.ssl_channel_credentials()` e `grpc.ssl_server_credentials()` specificando certificato CA, certificato server/client e chiave privata. gRPC supporta anche token OAuth2 tramite `grpc.access_token_call_credentials()`.

---

## Esercizi

### Esercizio 0 — Socket Options Benchmark (Propedeutico)

Scrivere uno script che confronta le prestazioni di un echo server TCP con e senza `TCP_NODELAY`. Inviare 10.000 messaggi da 64 byte e misurare il throughput e la latenza media. Ripetere con `SO_RCVBUF`/`SO_SNDBUF` a 8 KB, 64 KB e 256 KB. Presentare i risultati in una tabella comparativa.

### Esercizio 1 — Server TCP asincrono (Fondamentale)

Implementare un server echo TCP con `asyncio.streams` che: gestisce N client concorrenti, implementa timeout per inattivita, logga connessioni/disconnessioni, e limita il numero massimo di client con un semaforo.

### Esercizio 2 — Client HTTP/2 con benchmark

Scrivere uno script che confronta le prestazioni di HTTP/1.1 vs HTTP/2 scaricando 50 risorse dallo stesso server. Misurare tempo totale, numero di connessioni TCP, e overhead di handshake. Usare `httpx` con e senza `http2=True`.

### Esercizio 3 — Servizio gRPC di monitoraggio

Implementare il servizio gRPC definito nella sezione gRPC: server con metriche di sistema reali (psutil), client che stampa le metriche in formato tabellare, streaming di metriche ogni 5 secondi. Aggiungere autenticazione con token nei metadata.

### Esercizio 4 — mTLS con certificati auto-generati

Usare la libreria `cryptography` per generare: (1) una CA root, (2) un certificato server, (3) un certificato client. Implementare un server e un client che comunicano con mTLS. Verificare che la connessione fallisca senza certificato client.

### Esercizio 5 — DNS health checker avanzato

Estendere il DNS health checker della sezione DNS con: (1) verifica DNSSEC, (2) query DoH per confrontare le risposte, (3) misurazione della latenza per ogni nameserver, (4) report in formato JSON e HTML.

### Esercizio 6 — Scanner di porte con asyncio

Scrivere un port scanner asincrono che verifica le porte aperte di un host con concorrenza limitata (semaforo). Implementare: timeout per porta, rilevamento del servizio (banner grabbing), output in formato CSV. Nota: eseguire solo su sistemi autorizzati.

### Esercizio 7 — Proxy HTTP semplice

Implementare un proxy HTTP forward con `asyncio.streams` che: riceve richieste HTTP dai client, le inoltra al server di destinazione, restituisce le risposte. Loggare tutte le richieste con timestamp, URL e status code.

### Esercizio 8 — WebSocket chat server

Creare un server chat basato su WebSocket con la libreria `websockets`: supporto per piu stanze, broadcast dei messaggi, lista utenti connessi, comandi speciali (/nick, /list, /join).

### Esercizio 9 — Analizzatore pcap forense

Scrivere uno script che analizza un file pcap e produce un report forense con: (1) timeline delle connessioni TCP con durata e volume dati, (2) estrazione di tutte le query DNS con i corrispondenti indirizzi risolti, (3) rilevamento di porte non standard in uso, (4) identificazione di possibili data exfiltration (connessioni con volume di upload anomalo), (5) output in JSON e CSV.

### Esercizio 10 — Monitor certificati TLS con alerting

Costruire un servizio di monitoraggio certificati TLS che: (1) verifica periodicamente una lista di domini configurabili, (2) controlla la scadenza e la validita della catena, (3) invia alert (email o webhook) quando un certificato scade entro 30/14/7 giorni, (4) genera un report settimanale in formato HTML con lo stato di tutti i certificati, (5) registra uno storico in SQLite per trend analysis.

### Esercizio 11 — Pipeline FTP automatizzata

Implementare una pipeline di automazione FTP/FTPS che: (1) scarica ogni giorno file CSV da un server FTP remoto, (2) valida la struttura del CSV (colonne attese, tipi di dato), (3) trasforma i dati applicando regole di normalizzazione, (4) archivia i file elaborati in una directory con naming basato su data, (5) invia un report di sintesi via email con eventuali errori riscontrati, (6) gestisce i lock per evitare elaborazioni duplicate in caso di esecuzioni concorrenti.

### Esercizio 12 — Client HTTP comparativo

Scrivere uno script di benchmarking che confronta `requests`, `httpx` (sync e async), `aiohttp` e `urllib` sulle seguenti metriche: (1) tempo medio per 100 richieste GET sequenziali, (2) tempo totale per 100 richieste GET parallele (solo async), (3) throughput di download per file da 10 MB, (4) consumo di memoria durante le richieste parallele, (5) comportamento con errori di rete simulati (timeout, connection reset). Presentare i risultati con grafici (matplotlib) e una tabella riepilogativa.

---

## Letture

- Documentazione socket (Python stdlib). https://docs.python.org/3/library/socket.html
- Documentazione asyncio — Streams. https://docs.python.org/3/library/asyncio-stream.html
- Documentazione ssl (Python stdlib). https://docs.python.org/3/library/ssl.html
- Documentazione httpx. https://www.python-httpx.org/
- Documentazione h2 (HTTP/2). https://h2.readthedocs.io/en/stable/
- Documentazione gRPC Python. https://grpc.io/docs/languages/python/
- Documentazione Protocol Buffers. https://protobuf.dev/programming-guides/proto3/
- Documentazione dnspython. https://dnspython.readthedocs.io/en/stable/
- Documentazione paramiko. https://www.paramiko.org/
- Documentazione cryptography. https://cryptography.io/en/latest/
- Documentazione websockets. https://websockets.readthedocs.io/en/stable/
- Documentazione python-socketio. https://python-socketio.readthedocs.io/en/stable/
- Documentazione aiohttp. https://docs.aiohttp.org/en/stable/
- Documentazione Fabric. https://www.fabfile.org/
- Documentazione ftplib (Python stdlib). https://docs.python.org/3/library/ftplib.html
- Documentazione selectors (Python stdlib). https://docs.python.org/3/library/selectors.html
- Documentazione pyshark. https://github.com/KimiNewt/pyshark
- Documentazione dpkt. https://dpkt.readthedocs.io/en/latest/
- Documentazione scapy. https://scapy.readthedocs.io/en/latest/
- RFC 8484 — DNS Queries over HTTPS (DoH). https://www.rfc-editor.org/rfc/rfc8484
- RFC 7540 — HTTP/2. https://www.rfc-editor.org/rfc/rfc7540
- RFC 8446 — TLS 1.3. https://www.rfc-editor.org/rfc/rfc8446

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **asyncio.streams** | API ad alto livello di asyncio per networking basato su stream (reader/writer) su socket TCP. |
| **CDP** | Chrome DevTools Protocol — usato qui nel contesto gRPC per indicare il protocollo di comunicazione client-server. |
| **DNSSEC** | DNS Security Extensions — estensioni che aggiungono firme crittografiche alle risposte DNS per verificarne l'autenticita. |
| **DoH** | DNS over HTTPS — protocollo che incapsula query DNS in richieste HTTPS per privacy e integrita (RFC 8484). |
| **gRPC** | Framework RPC ad alte prestazioni di Google basato su HTTP/2 e Protocol Buffers. |
| **h2** | Libreria Python per il protocollo HTTP/2, usata come backend da httpx per il supporto HTTP/2. |
| **HPACK** | Algoritmo di compressione degli header HTTP/2 che riduce il overhead di header ripetuti. |
| **HTTP/2** | Versione del protocollo HTTP con multiplexing, compressione header e push server su singola connessione TCP (RFC 7540). |
| **httpx** | Client HTTP Python moderno con supporto sincrono/asincrono, HTTP/2, timeout strutturati e streaming. |
| **mTLS** | Mutual TLS — TLS con autenticazione bidirezionale dove sia client sia server presentano certificati. |
| **Multiplexing** | Tecnica di HTTP/2 che consente di inviare piu richieste/risposte in parallelo su una singola connessione TCP. |
| **Protocol Buffers** | Formato di serializzazione binario di Google, usato da gRPC per definire contratti di servizio e strutture dati. |
| **RRSIG** | Resource Record Signature — record DNS che contiene la firma crittografica di un set di record per DNSSEC. |
| **Semaphore** | Primitiva di sincronizzazione che limita l'accesso concorrente a una risorsa condivisa a un numero massimo di task. |
| **StreamReader** | Oggetto asyncio che fornisce un'interfaccia per leggere dati da uno stream di rete in modo asincrono. |
| **StreamWriter** | Oggetto asyncio che fornisce un'interfaccia per scrivere dati su uno stream di rete in modo asincrono. |
| **TLS 1.3** | Versione piu recente del protocollo TLS con handshake ridotto, forward secrecy obbligatoria (RFC 8446). |
| **WebSocket** | Protocollo di comunicazione full-duplex su una singola connessione TCP, ideale per applicazioni real-time. |
| **Zero-trust** | Modello di sicurezza che non assume fiducia implicita per nessuna connessione, richiedendo autenticazione per ogni comunicazione. |
| **aiohttp** | Libreria Python asincrona che fornisce client e server HTTP basati su asyncio, con supporto nativo per WebSocket. |
| **dpkt** | Libreria Python leggera per la creazione e il parsing di pacchetti di rete a basso livello, alternativa a scapy per analisi pcap. |
| **epoll** | Meccanismo di I/O multiplexing ad alte prestazioni specifico di Linux, esposto in Python tramite il modulo `selectors`. |
| **Fabric** | Libreria Python di alto livello per l'esecuzione remota di comandi SSH e il deployment automatizzato di applicazioni. |
| **ftplib** | Modulo della libreria standard Python per operazioni FTP e FTPS (FTP over TLS). |
| **pcap** | Formato di file standard per la cattura di pacchetti di rete, leggibile con pyshark, dpkt e scapy. |
| **pyshark** | Wrapper Python per tshark (Wireshark CLI) che permette l'analisi di file pcap e la cattura live di pacchetti. |
| **python-socketio** | Libreria Python per il protocollo Socket.IO, che fornisce comunicazione bidirezionale real-time con fallback automatico. |
| **selectors** | Modulo della libreria standard Python che fornisce un'API ad alto livello per I/O multiplexing (select, poll, epoll, kqueue). |
| **Socket.IO** | Protocollo di comunicazione real-time bidirezionale che opera sopra WebSocket con fallback a HTTP long-polling. |
| **SO_KEEPALIVE** | Opzione socket che abilita l'invio periodico di pacchetti keep-alive per rilevare connessioni interrotte. |
| **TCP_NODELAY** | Opzione socket che disabilita l'algoritmo di Nagle, riducendo la latenza per pacchetti piccoli a costo di maggiore overhead di rete. |

---

> **Moduli correlati**: [16-automazione.md](16-automazione.md) (SSH con paramiko, fabric), [15-web-scraping.md](15-web-scraping.md) (HTTP client per scraping), [10-programmazione-asincrona.md](10-programmazione-asincrona.md) (asyncio fondamenti), [18-sicurezza.md](18-sicurezza.md) (TLS, crittografia), [13-rest-api.md](13-rest-api.md) (API HTTP), [31-osservabilita-otel-prometheus.md](31-osservabilita-otel-prometheus.md) (gRPC instrumentation con OTel).
