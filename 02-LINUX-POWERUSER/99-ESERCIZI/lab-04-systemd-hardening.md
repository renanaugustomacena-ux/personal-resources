# Lab 04 — Hardening Unit systemd

> **Modulo di riferimento:** [04-systemd.md](../04-systemd.md), [34-hardening-sicurezza-avanzata.md](../34-hardening-sicurezza-avanzata.md)
> **Tempo stimato:** 2-3 ore
> **Livello:** competent → proficient
> **Prerequisiti:** VM Debian 12, completamento moduli 04, 09, 11
> **Ultimo aggiornamento:** 2026-05-23

---

## Obiettivo

Applicare direttive di hardening systemd.exec a servizi reali, misurare il punteggio di sicurezza con `systemd-analyze security`, e comprendere l'impatto di ogni direttiva.

---

## Parte 1 — Baseline Assessment (20 min)

### 1.1 Audit di tutti i servizi

```bash
# Punteggio sicurezza di tutti i servizi attivi
systemd-analyze security

# Output esempio:
# UNIT                      EXPOSURE PREDICATE HAPPY
# nginx.service             9.6      UNSAFE    😨
# postgresql.service        9.2      UNSAFE    😨
# sshd.service              9.6      UNSAFE    😨
# prometheus.service        7.1      MEDIUM    😐
```

### 1.2 Analisi dettagliata di un servizio

```bash
# Analisi dettagliata di nginx
systemd-analyze security nginx.service

# Mostra ogni direttiva, se impostata, e il suo impatto sul punteggio
```

Annotare il punteggio iniziale di ogni servizio target.

---

## Parte 2 — Servizio Custom di Esempio (30 min)

### 2.1 Creare un'applicazione di test

```bash
cat > /usr/local/bin/demo-app.py << 'PYEOF'
#!/usr/bin/env python3
"""Simple HTTP server for systemd hardening lab."""
import http.server
import json
import os
import sys

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = {
                'status': 'ok',
                'pid': os.getpid(),
                'uid': os.getuid(),
                'cwd': os.getcwd()
            }
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[demo-app] {args[0]} {args[1]} {args[2]}", file=sys.stderr, flush=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8080'))
    server = http.server.HTTPServer(('127.0.0.1', port), Handler)
    print(f"[demo-app] Listening on 127.0.0.1:{port}", flush=True)
    server.serve_forever()
PYEOF
chmod 755 /usr/local/bin/demo-app.py
```

### 2.2 Unit non hardened (baseline)

```bash
cat > /etc/systemd/system/demo-app.service << 'EOF'
[Unit]
Description=Demo Application (unhardened)
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/demo-app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start demo-app

# Punteggio baseline
systemd-analyze security demo-app.service
# Atteso: ~9.6 UNSAFE
```

### 2.3 Unit hardened progressivamente

```bash
cat > /etc/systemd/system/demo-app.service << 'EOF'
[Unit]
Description=Demo Application (hardened)
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/demo-app.py
Restart=on-failure
RestartSec=5s

# === Utente e gruppo dedicato ===
DynamicUser=yes

# === Filesystem ===
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=

# === Rete ===
RestrictAddressFamilies=AF_INET AF_INET6
IPAddressDeny=any
IPAddressAllow=127.0.0.0/8 ::1/128

# === Capacita ===
CapabilityBoundingSet=
AmbientCapabilities=
NoNewPrivileges=yes

# === Namespace ===
PrivateDevices=yes
PrivateUsers=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectClock=yes
ProtectHostname=yes

# === Syscall filtering ===
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources @mount @swap @reboot @raw-io
SystemCallArchitectures=native
LockPersonality=yes

# === Memoria ===
MemoryDenyWriteExecute=yes

# === Misc ===
RestrictRealtime=yes
RestrictSUIDSGID=yes
RestrictNamespaces=yes
RemoveIPC=yes
PrivateNetwork=no
UMask=0077

# === Logging ===
StandardOutput=journal
StandardError=journal
SyslogIdentifier=demo-app

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl restart demo-app

# Verificare funzionamento
curl -s http://127.0.0.1:8080/health | python3 -m json.tool

# Punteggio post-hardening
systemd-analyze security demo-app.service
# Target: ≤ 2.0 OK
```

---

## Parte 3 — Hardening di Servizi Reali (60 min)

### 3.1 Nginx

```bash
mkdir -p /etc/systemd/system/nginx.service.d

cat > /etc/systemd/system/nginx.service.d/hardening.conf << 'EOF'
[Service]
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectClock=yes
ProtectHostname=yes

NoNewPrivileges=yes
CapabilityBoundingSet=CAP_NET_BIND_SERVICE CAP_DAC_OVERRIDE CAP_SETUID CAP_SETGID
AmbientCapabilities=

RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
RestrictNamespaces=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
LockPersonality=yes

SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources
SystemCallArchitectures=native

ReadWritePaths=/var/log/nginx /run/nginx /var/cache/nginx
ReadOnlyPaths=/etc/nginx /etc/ssl

MemoryDenyWriteExecute=yes
RemoveIPC=yes
UMask=0027
EOF

systemctl daemon-reload
systemctl restart nginx

# Verificare
curl -s http://localhost/ > /dev/null && echo "nginx OK" || echo "nginx FAIL"
systemd-analyze security nginx.service
```

### 3.2 PostgreSQL

```bash
mkdir -p /etc/systemd/system/postgresql@.service.d

cat > /etc/systemd/system/postgresql@.service.d/hardening.conf << 'EOF'
[Service]
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectClock=yes

NoNewPrivileges=yes
CapabilityBoundingSet=CAP_DAC_OVERRIDE CAP_CHOWN CAP_FOWNER CAP_SETUID CAP_SETGID

RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
RestrictNamespaces=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
LockPersonality=yes

SystemCallFilter=@system-service @io-event
SystemCallFilter=~@privileged
SystemCallArchitectures=native

ReadWritePaths=/var/lib/postgresql /var/log/postgresql /run/postgresql /etc/postgresql

RemoveIPC=yes
UMask=0077
EOF

systemctl daemon-reload
systemctl restart postgresql

# Verificare
sudo -u postgres psql -c "SELECT 1;" && echo "PostgreSQL OK" || echo "PostgreSQL FAIL"
systemd-analyze security postgresql@16-main.service
```

### 3.3 Gestire errori

Se un servizio non si avvia dopo l'hardening:

```bash
# Controllare i log
journalctl -u nginx.service -n 50 --no-pager

# Errori comuni:
# - "Permission denied": aggiungere il path a ReadWritePaths=
# - "Operation not permitted": aggiungere la capability necessaria a CapabilityBoundingSet=
# - "System call filtered": usare strace per identificare la syscall bloccata

# Debugging con strace
strace -ff -e trace=all -p $(systemctl show -p MainPID --value nginx.service) 2>&1 | grep EPERM
```

---

## Parte 4 — Watchdog e Health Check (20 min)

### 4.1 Aggiungere watchdog alla demo app

```bash
cat > /usr/local/bin/demo-app-watchdog.py << 'PYEOF'
#!/usr/bin/env python3
"""HTTP server with systemd watchdog support."""
import http.server
import json
import os
import socket
import sys
import threading
import time

WATCHDOG_USEC = int(os.environ.get('WATCHDOG_USEC', '0'))
NOTIFY_SOCKET = os.environ.get('NOTIFY_SOCKET', '')

def sd_notify(msg):
    if not NOTIFY_SOCKET:
        return
    addr = NOTIFY_SOCKET
    if addr.startswith('@'):
        addr = '\0' + addr[1:]
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        sock.connect(addr)
        sock.sendall(msg.encode())
    finally:
        sock.close()

def watchdog_loop():
    if not WATCHDOG_USEC:
        return
    interval = int(WATCHDOG_USEC) / 1_000_000 / 2
    while True:
        sd_notify('WATCHDOG=1')
        time.sleep(interval)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[demo-app] {args[0]} {args[1]} {args[2]}", file=sys.stderr, flush=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8080'))
    t = threading.Thread(target=watchdog_loop, daemon=True)
    t.start()
    sd_notify('READY=1')
    server = http.server.HTTPServer(('127.0.0.1', port), Handler)
    print(f"[demo-app] Listening on 127.0.0.1:{port}", flush=True)
    server.serve_forever()
PYEOF
chmod 755 /usr/local/bin/demo-app-watchdog.py
```

### 4.2 Unit con watchdog

```bash
cat > /etc/systemd/system/demo-app-watchdog.service << 'EOF'
[Unit]
Description=Demo App with Watchdog
After=network.target

[Service]
Type=notify
ExecStart=/usr/local/bin/demo-app-watchdog.py
Restart=on-failure
RestartSec=5s
WatchdogSec=30s

DynamicUser=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
NoNewPrivileges=yes
CapabilityBoundingSet=
SystemCallFilter=@system-service
SystemCallArchitectures=native
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
MemoryDenyWriteExecute=yes
LockPersonality=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start demo-app-watchdog

# Verificare watchdog
systemctl status demo-app-watchdog
# Deve mostrare "watchdog" nel StatusText
```

---

## Parte 5 — Confronto Punteggi (10 min)

### 5.1 Tabella riassuntiva

```bash
echo "=== SECURITY SCORES ==="
printf "%-30s %s\n" "SERVICE" "SCORE"
printf "%-30s %s\n" "-------" "-----"
for svc in demo-app demo-app-watchdog nginx postgresql@16-main; do
    score=$(systemd-analyze security "$svc.service" 2>/dev/null | tail -1 | awk '{print $2}')
    printf "%-30s %s\n" "$svc" "${score:-N/A}"
done
```

---

## Criteri di Completamento

- [ ] Demo app hardened: punteggio ≤ 2.0
- [ ] Nginx hardened: punteggio ≤ 4.0
- [ ] PostgreSQL hardened: punteggio ≤ 4.5
- [ ] Watchdog funzionante (test con kill -STOP)
- [ ] Tutti i servizi funzionanti dopo hardening
- [ ] Documentato ogni override necessario con motivazione

---

## Sfide Extra

1. **Hardening sshd**: applicare direttive systemd a sshd senza rompere l'accesso.
2. **Seccomp profile**: generare un profilo seccomp custom per la demo app.
3. **Resource limits**: aggiungere `MemoryMax=`, `CPUQuota=`, `TasksMax=` alla demo app e testare i limiti.

---

## Riferimenti

- systemd.exec(5) — `man systemd.exec` (consultato: 2026-05-23)
- systemd.resource-control(5) — `man systemd.resource-control` (consultato: 2026-05-23)
- [04-systemd.md](../04-systemd.md)
- [34-hardening-sicurezza-avanzata.md](../34-hardening-sicurezza-avanzata.md)
