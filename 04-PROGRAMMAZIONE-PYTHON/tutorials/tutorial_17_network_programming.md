# Tutorial 17 — Network Programming in Python: Socket, HTTP, gRPC

> **Companion a:** `17-network-programming.md`
> **Scope:** socket TCP/UDP, asyncio streams, HTTP/2, gRPC, protocolli custom, NAT/TLS
> **Prerequisiti:** `tutorial_10_programmazione_asincrona.md`, `tutorial_11_web_framework.md`
> **Durata stimata:** 16-20 ore
> **Stack:** Python 3.12+, asyncio, httpx, grpcio, protobuf

---

## Mappa concettuale

```
Network Programming
│
├── Socket di basso livello
│   ├── socket.socket — socket BSD
│   ├── TCP (SOCK_STREAM) — connection-oriented, affidabile
│   ├── UDP (SOCK_DGRAM) — connectionless, veloce
│   └── Unix Domain Socket — IPC locale
│
├── asyncio Streams (TCP alto livello)
│   ├── asyncio.start_server() — TCP server
│   ├── asyncio.open_connection() — TCP client
│   ├── StreamReader / StreamWriter
│   └── Protocollo linea / lunghezza prefissata
│
├── HTTP/HTTPS
│   ├── httpx — client HTTP/1.1 + HTTP/2
│   ├── aiohttp — client async alternativo
│   └── FastAPI/aiohttp — server
│
├── gRPC
│   ├── Protocol Buffers — schema IDL
│   ├── grpc.ServiceServicer — implementazione server
│   ├── grpc.Channel — connessione client
│   └── Streaming RPC — unary, server-stream, client-stream, bidi
│
└── Pattern
    ├── Protocol framing — length-prefix, delimiter
    ├── TLS con ssl module
    ├── Connection pooling
    └── Circuit breaker per chiamate remote
```

---

# Parte A — Socket TCP e UDP

---

## A1. Server TCP con socket

```python
import socket
import threading
import logging

logger = logging.getLogger(__name__)

def gestisci_client(conn: socket.socket, addr: tuple[str, int]) -> None:
    """Thread per gestire un client connesso."""
    logger.info(f"Client connesso: {addr}")
    try:
        while True:
            dati = conn.recv(1024)
            if not dati:
                break   # client disconnesso
            messaggio = dati.decode("utf-8").strip()
            logger.info(f"Ricevuto da {addr}: {messaggio}")
            risposta = f"ECHO: {messaggio}\n"
            conn.sendall(risposta.encode("utf-8"))
    except ConnectionResetError:
        pass
    finally:
        conn.close()
        logger.info(f"Client disconnesso: {addr}")

def server_tcp(host: str = "127.0.0.1", porta: int = 9000) -> None:
    """Echo server TCP multi-thread."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, porta))
        srv.listen(10)   # backlog: max connessioni in attesa
        logger.info(f"Server TCP in ascolto su {host}:{porta}")

        while True:
            conn, addr = srv.accept()
            t = threading.Thread(target=gestisci_client, args=(conn, addr), daemon=True)
            t.start()

def client_tcp(host: str, porta: int, messaggi: list[str]) -> list[str]:
    """Client TCP che invia messaggi e raccoglie risposte."""
    risposte = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, porta))
        s.settimeout(5.0)
        for msg in messaggi:
            s.sendall(f"{msg}\n".encode("utf-8"))
            risposta = b""
            while not risposta.endswith(b"\n"):
                chunk = s.recv(256)
                if not chunk:
                    break
                risposta += chunk
            risposte.append(risposta.decode("utf-8").strip())
    return risposte
```

---

## A2. Server UDP

```python
import socket
import logging

logger = logging.getLogger(__name__)

def server_udp(host: str = "127.0.0.1", porta: int = 9001) -> None:
    """Server UDP — ideale per telemetria, log, DNS-like."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((host, porta))
        logger.info(f"Server UDP in ascolto su {host}:{porta}")

        while True:
            dati, addr = s.recvfrom(4096)
            messaggio = dati.decode("utf-8")
            logger.info(f"UDP da {addr}: {messaggio}")

            # Risposta opzionale (UDP è connectionless)
            risposta = f"ACK:{messaggio}"
            s.sendto(risposta.encode("utf-8"), addr)

def client_udp(host: str, porta: int, messaggio: str) -> str:
    """Client UDP — fire and forget o con attesa ACK."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(2.0)
        s.sendto(messaggio.encode("utf-8"), (host, porta))
        try:
            risposta, _ = s.recvfrom(4096)
            return risposta.decode("utf-8")
        except socket.timeout:
            return ""   # UDP: nessuna garanzia di consegna
```

> **Analogia TCP vs UDP:** TCP è come una telefonata — stai sicuro che l'altro sente tutto, nell'ordine giusto, e ti avvisi se la connessione cade. UDP è come mandare cartoline — veloci, tante, ma alcune potrebbero non arrivare e non sai in che ordine. Per telemetria ad alta frequenza (100 metriche/s) preferisci UDP; per trasferire dati finanziari preferisci TCP.

---

## A3. asyncio Streams: TCP asincrono

```python
import asyncio

async def gestisci_client_async(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    """Gestione client con protocollo lunghezza-prefissata."""
    addr = writer.get_extra_info("peername")
    logger = __import__("logging").getLogger(__name__)
    logger.info(f"Connesso: {addr}")

    try:
        while True:
            # Leggi header (4 byte = lunghezza del messaggio)
            header = await reader.readexactly(4)
            lunghezza = int.from_bytes(header, "big")

            if lunghezza == 0 or lunghezza > 1_000_000:
                break   # protocollo invalido o EOF

            # Leggi body di esattamente `lunghezza` byte
            body = await reader.readexactly(lunghezza)
            messaggio = body.decode("utf-8")
            logger.info(f"Ricevuto da {addr}: {messaggio[:50]}")

            # Invia risposta con lo stesso framing
            risposta = f"OK:{messaggio}".encode("utf-8")
            writer.write(len(risposta).to_bytes(4, "big") + risposta)
            await writer.drain()

    except asyncio.IncompleteReadError:
        pass   # client disconnesso
    finally:
        writer.close()
        await writer.wait_closed()

async def avvia_server_async(host: str = "127.0.0.1", porta: int = 9002) -> None:
    server = await asyncio.start_server(gestisci_client_async, host, porta)
    logger = __import__("logging").getLogger(__name__)
    async with server:
        logger.info(f"Server async in ascolto su {host}:{porta}")
        await server.serve_forever()

async def client_async(host: str, porta: int, messaggi: list[str]) -> list[str]:
    reader, writer = await asyncio.open_connection(host, porta)
    risposte = []
    try:
        for msg in messaggi:
            encoded = msg.encode("utf-8")
            writer.write(len(encoded).to_bytes(4, "big") + encoded)
            await writer.drain()

            header = await reader.readexactly(4)
            lunghezza = int.from_bytes(header, "big")
            body = await reader.readexactly(lunghezza)
            risposte.append(body.decode("utf-8"))
    finally:
        writer.close()
        await writer.wait_closed()
    return risposte
```

---

# Parte B — TLS e sicurezza

---

## B1. TLS su socket

```python
import ssl
import socket

def crea_contesto_server(cert_file: str, key_file: str) -> ssl.SSLContext:
    """Contesto SSL per server."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert_file, key_file)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    # Disable old ciphers
    ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:!aNULL:!eNULL")
    return ctx

def crea_contesto_client(ca_file: str | None = None) -> ssl.SSLContext:
    """Contesto SSL per client con verifica certificato."""
    ctx = ssl.create_default_context(cafile=ca_file)
    # ctx.check_hostname = False   # SOLO per test con certificati self-signed
    # ctx.verify_mode = ssl.CERT_NONE
    return ctx

# Server TLS
def server_tls(host: str, porta: int, cert: str, key: str) -> None:
    ctx = crea_contesto_server(cert, key)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw:
        raw.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        raw.bind((host, porta))
        raw.listen(5)
        with ctx.wrap_socket(raw, server_side=True) as srv:
            while True:
                conn, addr = srv.accept()
                dati = conn.recv(1024)
                conn.sendall(dati)   # echo
                conn.close()

# asyncio con TLS
async def server_async_tls(host: str, porta: int, cert: str, key: str) -> None:
    ctx = crea_contesto_server(cert, key)
    server = await asyncio.start_server(
        gestisci_client_async, host, porta, ssl=ctx
    )
    async with server:
        await server.serve_forever()
```

---

# Parte C — gRPC

---

## C1. Definire un servizio con protobuf

```protobuf
// calcolatrice.proto
syntax = "proto3";

package calcolatrice;

service Calcolatrice {
  rpc Somma (OperazioneRequest) returns (RisultatoResponse);
  rpc SommaStream (stream NumeroRequest) returns (RisultatoResponse);
}

message OperazioneRequest {
  double a = 1;
  double b = 2;
}

message NumeroRequest {
  double valore = 1;
}

message RisultatoResponse {
  double risultato = 1;
  string messaggio = 2;
}
```

```bash
# Genera codice Python
python -m grpc_tools.protoc \
  -I. \
  --python_out=. \
  --grpc_python_out=. \
  calcolatrice.proto
```

---

## C2. Server e client gRPC

```python
# pip install grpcio grpcio-tools
import grpc
from concurrent import futures
import calcolatrice_pb2
import calcolatrice_pb2_grpc

# Server
class CalcolatriceServicer(calcolatrice_pb2_grpc.CalcolatriceServicer):
    def Somma(self, request, context):
        risultato = request.a + request.b
        return calcolatrice_pb2.RisultatoResponse(
            risultato=risultato,
            messaggio=f"{request.a} + {request.b} = {risultato}",
        )

    def SommaStream(self, request_iterator, context):
        totale = 0.0
        for req in request_iterator:
            totale += req.valore
        return calcolatrice_pb2.RisultatoResponse(
            risultato=totale,
            messaggio=f"Somma di tutti i valori: {totale}",
        )

def avvia_server_grpc(porta: int = 50051) -> None:
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_send_message_length", 10 * 1024 * 1024),
            ("grpc.max_receive_message_length", 10 * 1024 * 1024),
        ],
    )
    calcolatrice_pb2_grpc.add_CalcolatriceServicer_to_server(
        CalcolatriceServicer(), server
    )
    server.add_insecure_port(f"[::]:{porta}")
    server.start()
    print(f"gRPC server in ascolto su porta {porta}")
    server.wait_for_termination()

# Client
def client_grpc(host: str = "localhost", porta: int = 50051) -> None:
    with grpc.insecure_channel(f"{host}:{porta}") as channel:
        stub = calcolatrice_pb2_grpc.CalcolatriceStub(channel)

        # Unary RPC
        risposta = stub.Somma(
            calcolatrice_pb2.OperazioneRequest(a=3.14, b=2.72),
            timeout=5.0,
        )
        print(f"Somma: {risposta.risultato} — {risposta.messaggio}")

        # Client streaming
        def genera_numeri():
            for i in range(1, 6):
                yield calcolatrice_pb2.NumeroRequest(valore=float(i))

        risposta_stream = stub.SommaStream(genera_numeri(), timeout=10.0)
        print(f"Somma stream: {risposta_stream.risultato}")
```

---

# Parte D — Pattern di robustezza

---

## D1. Connection pool e retry per chiamate remote

```python
import asyncio
import logging
from collections.abc import Callable, Awaitable

logger = logging.getLogger(__name__)

async def richiesta_con_retry(
    fn: Callable[[], Awaitable],
    max_tentativi: int = 3,
    backoff_base: float = 1.0,
    eccezioni_ritentabili: tuple = (ConnectionError, OSError, asyncio.TimeoutError),
) -> object:
    """Retry con backoff esponenziale per chiamate di rete."""
    ultimo_errore: Exception | None = None
    for tentativo in range(max_tentativi):
        try:
            return await fn()
        except eccezioni_ritentabili as e:
            ultimo_errore = e
            if tentativo < max_tentativi - 1:
                attesa = backoff_base * (2 ** tentativo)
                logger.warning(f"Tentativo {tentativo+1} fallito: {e}, retry tra {attesa:.1f}s")
                await asyncio.sleep(attesa)
    raise RuntimeError(f"Tutti {max_tentativi} tentativi falliti: {ultimo_errore}")

class CircuitBreaker:
    """Circuit breaker per chiamate di rete."""
    def __init__(self, soglia_errori: int = 5, timeout_reset: float = 60.0) -> None:
        self._errori = 0
        self._soglia = soglia_errori
        self._timeout = timeout_reset
        self._aperto_da: float | None = None

    @property
    def aperto(self) -> bool:
        if self._aperto_da is None:
            return False
        import time
        if time.monotonic() - self._aperto_da > self._timeout:
            self._aperto_da = None
            self._errori = 0
            return False
        return True

    def registra_successo(self) -> None:
        self._errori = 0

    def registra_errore(self) -> None:
        import time
        self._errori += 1
        if self._errori >= self._soglia:
            self._aperto_da = time.monotonic()
            logger.error(f"Circuit breaker APERTO dopo {self._errori} errori")

    async def esegui(self, fn: Callable[[], Awaitable]) -> object:
        if self.aperto:
            raise RuntimeError("Circuit breaker aperto — chiamate bloccate")
        try:
            risultato = await fn()
            self.registra_successo()
            return risultato
        except Exception as e:
            self.registra_errore()
            raise
```

---

# Parte E — Riepilogo

## Tabella protocolli

| Protocollo | Libreria Python | Caso d'uso |
|---|---|---|
| TCP raw | `socket` | Protocolli custom, max controllo |
| TCP async | `asyncio.start_server` | Server ad alte performance |
| UDP | `socket` (DGRAM) | Telemetria, DNS, giochi |
| HTTP/1.1 | `httpx` / `requests` | REST API, web scraping |
| HTTP/2 | `httpx` (http2=True) | API con molte richieste |
| gRPC | `grpcio` | Microservizi, streaming RPC |
| WebSocket | `fastapi` / `websockets` | Real-time bidirectional |
| TLS | `ssl` module | Cifratura trasporto |

## Anti-pattern di rete

- **Socket senza timeout** — il programma si blocca indefinitamente; sempre `settimeout()`
- **Grandi buffer UDP** — pacchetti > 65535 byte vengono frammentati; tenerli < 1400 byte
- **gRPC senza timeout** — i metadata `timeout=N` sono obbligatori in produzione
- **Nessun retry** — le reti falliscono; implementare sempre backoff esponenziale

## Prossimi passi

- `tutorial_18_sicurezza.md` — crittografia, HMAC, JWT, sicurezza delle API
- `tutorial_19_cli_tools.md` — strumenti CLI che usano socket/HTTP
