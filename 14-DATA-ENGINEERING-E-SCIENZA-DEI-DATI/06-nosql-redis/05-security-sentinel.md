# Redis: Security and Redis Sentinel

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [x] Review tecnica
- [x] Formattazione
- [ ] Pubblicazione

## Table of Contents

1. [Security Overview](#1-security-overview)
2. [Authentication (AUTH)](#2-authentication-auth)
3. [Access Control Lists (ACLs)](#3-access-control-lists-acls)
4. [TLS Encryption](#4-tls-encryption)
5. [Protected Mode](#5-protected-mode)
6. [Network Security](#6-network-security)
7. [Sentinel Architecture](#7-sentinel-architecture)
8. [Sentinel Configuration](#8-sentinel-configuration)
9. [Client-Side Discovery](#9-client-side-discovery)
10. [Monitoring Sentinel](#10-monitoring-sentinel)
11. [Troubleshooting](#11-troubleshooting)
12. [Q&A](#12-qa)
13. [Exercises](#13-exercises)

---

## 1. Security Overview

### 1.1 Redis Threat Model

Redis was originally designed for trusted networks. Security was added incrementally. Many production breaches involve Redis instances exposed to the internet with no authentication.

Common attack vectors:

| Vector | Risk | Mitigation |
|--------|------|------------|
| Unauthenticated access | Full data read/write/delete | AUTH + ACLs |
| Network sniffing | Credential and data exposure | TLS encryption |
| Command injection via client | Arbitrary command execution | ACLs, command renaming |
| Dangerous commands (FLUSHALL, DEBUG, CONFIG) | Data loss, config tampering | Rename/disable commands |
| Replica abuse | Exfiltrate data via rogue replica | requirepass, ACLs, network segmentation |
| Lua script abuse | Resource exhaustion, sandbox escape | ACLs limiting EVAL |
| Module loading | Arbitrary code execution | Disable MODULE LOAD in prod |

### 1.2 Defense-in-Depth Layers

```
Layer 1: Network    -- Bind to internal IPs, firewall rules, VPC/VLAN isolation
Layer 2: Transport  -- TLS encryption for data in transit
Layer 3: Auth       -- Password authentication (AUTH command)
Layer 4: AuthZ      -- ACLs for fine-grained command/key permissions
Layer 5: Commands   -- Rename/disable dangerous commands
Layer 6: Monitoring -- Audit logging, intrusion detection
```

Never rely on a single layer. A production Redis deployment should implement all six.

### 1.3 Security Baseline Checklist

```
- [ ] AUTH password set (strong, 32+ characters)
- [ ] ACLs configured (no default user with full access)
- [ ] TLS enabled for client and replication traffic
- [ ] Bound to internal interfaces only (not 0.0.0.0)
- [ ] Protected mode enabled
- [ ] Dangerous commands renamed or disabled
- [ ] MODULE LOAD disabled
- [ ] Firewall allows only known client IPs
- [ ] No Redis port exposed to the internet
- [ ] Log monitoring for AUTH failures
- [ ] Regular security patches applied
```

---

## 2. Authentication (AUTH)

### 2.1 Legacy Password Authentication (Pre-Redis 6)

Before Redis 6, there was a single server-wide password:

```bash
# redis.conf
requirepass "YourStr0ngP@ssw0rd!WithSpecialChars#2026"

# Client authentication
redis-cli
> AUTH "YourStr0ngP@ssw0rd!WithSpecialChars#2026"
# OK

> PING
# PONG

# Without auth:
> PING
# (error) NOAUTH Authentication required.
```

Redis can process 100K+ AUTH attempts per second. A weak password falls to brute force in minutes. Use at least 32 random characters:

```bash
# Generate a strong password
openssl rand -base64 48
# Output: xK3j9mR2vLpQw7nY5tS1uA8cF6gH4iB0eD3kJ9mN2oP
```

### 2.2 Username + Password Authentication (Redis 6+)

Redis 6 introduced ACLs with per-user authentication:

```bash
# Connect with username and password
redis-cli
> AUTH username password
# OK

# Or on connection
redis-cli --user myuser --pass mypassword

# In redis-cli URL format
redis-cli -u redis://myuser:mypassword@localhost:6379
```

### 2.3 AUTH in Connection Strings

```
# Standard Redis URI
redis://username:password@host:port/db

# With TLS
rediss://username:password@host:port/db

# Examples
redis://default:s3cur3p4ss@redis.internal:6379/0
rediss://appuser:xK3j9mR2vLp@redis.internal:6380/0
```

### 2.4 Password Hashing

```bash
# Store password as SHA-256 hash instead of plaintext
user myuser on #a1b2c3d4e5f67890...sha256hex... ~* +@all

# Generate SHA-256 hash for a password
echo -n "my_password" | sha256sum
# Output: 89e01536ac207279409d4de1e5253e01f4a1769e696db0d6062ca9b8f56767c8

# Use the hash in ACL (prefix with #)
ACL SETUSER myuser on #89e01536ac207279409d4de1e5253e01f4a1769e696db0d6062ca9b8f56767c8 ~* +@all
```

### 2.5 AUTH Failure Monitoring

```bash
# Monitor AUTH failures in Redis logs
# redis.conf: set loglevel to notice or verbose
loglevel notice

# Log entries on failed AUTH:
# "User <user> failed AUTH with username <name>"

# Redis does NOT rate-limit AUTH attempts natively
# Implement rate limiting at the network layer (see section 6)
```

---

## 3. Access Control Lists (ACLs)

### 3.1 ACL Fundamentals

ACLs provide fine-grained control over what each user can do and which keys they can access. An ACL rule defines:

- **Username**: Identity for authentication
- **Password(s)**: One or more passwords (supports rotation)
- **Enabled/disabled**: Whether the user can authenticate
- **Commands**: Which commands the user can execute
- **Keys**: Which key patterns the user can access
- **Channels**: Which Pub/Sub channels the user can access (Redis 7+)

### 3.2 ACL Syntax Reference

```bash
# Full syntax
ACL SETUSER <username> [rule [rule ...]]

# Rules:
# on/off        -- Enable/disable user
# >password     -- Add password (plaintext, Redis hashes it internally)
# #hash         -- Add password by SHA-256 hash
# <password     -- Remove password
# nopass        -- No password needed (dangerous -- avoid)
# resetpass     -- Remove all passwords
# ~pattern      -- Allow key pattern (glob syntax)
# %R~pattern    -- Read-only key pattern (Redis 7+)
# %W~pattern    -- Write-only key pattern (Redis 7+)
# %RW~pattern   -- Read-write key pattern (Redis 7+)
# allkeys       -- Allow all keys (~*)
# resetkeys     -- Remove all key patterns
# +command      -- Allow command
# -command      -- Deny command
# +@category    -- Allow command category
# -@category    -- Deny command category
# +command|subcommand -- Allow specific subcommand (Redis 7+)
# allcommands   -- Allow all commands (+@all)
# nocommands    -- Deny all commands (-@all)
# &pattern      -- Allow Pub/Sub channel pattern (Redis 7+)
# allchannels   -- Allow all channels
# resetchannels -- Remove all channel patterns
```

### 3.3 Practical ACL Examples

```bash
# Read-only user for monitoring dashboards
ACL SETUSER grafana on >grafanaP@ss \
    ~metrics:* ~stats:* \
    -@all +@read +@connection +info +dbsize +slowlog

# Application user with limited write access
ACL SETUSER appuser on >appS3cur3 \
    ~app:* ~session:* ~cache:* \
    +@read +@write +@connection +@string +@hash +@list +@set +@sortedset \
    -@admin -@dangerous

# Queue worker user (list commands only)
ACL SETUSER worker on >w0rk3rP@ss \
    ~queue:* ~job:* ~dlq:* \
    +lpush +rpush +lpop +rpop +brpop +blpop +llen +lrange \
    +@connection

# Admin user (restrict even for admins)
ACL SETUSER admin on >adm1nStr0ng \
    ~* &* \
    +@all -module -debug

# Pub/Sub only user (Redis 7+)
ACL SETUSER pubsub_user on >pubsubP@ss \
    &events:* &notifications:* \
    +subscribe +publish +unsubscribe +psubscribe +punsubscribe \
    +@connection

# Read-only for some keys, read-write for others (Redis 7+ selectors)
ACL SETUSER hybrid on >hybridP@ss \
    %R~reports:* %RW~cache:* \
    +@read +@write +@connection
```

### 3.4 ACL File

Store ACLs in a file for persistence and version control:

```bash
# redis.conf
aclfile /etc/redis/users.acl

# /etc/redis/users.acl
user default off
user admin on >adm1nStr0ng ~* &* +@all -module -debug
user appuser on >appS3cur3 ~app:* ~session:* +@read +@write +@connection -@admin -@dangerous
user grafana on >grafanaP@ss ~metrics:* ~stats:* -@all +@read +@connection +info
user worker on >w0rk3rP@ss ~queue:* +lpush +rpush +lpop +rpop +brpop +blpop +@connection
```

```bash
# Reload ACL file at runtime (no restart needed)
redis-cli ACL LOAD
# OK

# Save in-memory ACL changes to file
redis-cli ACL SAVE

# Verify loaded users
redis-cli ACL LIST
```

### 3.5 ACL Categories

Redis groups commands into categories. Use `ACL CAT` to explore:

```bash
redis-cli ACL CAT
# 1) "keyspace"
# 2) "read"
# 3) "write"
# 4) "set"
# 5) "sortedset"
# 6) "list"
# 7) "hash"
# 8) "string"
# 9) "bitmap"
# 10) "hyperloglog"
# 11) "geo"
# 12) "stream"
# 13) "pubsub"
# 14) "admin"
# 15) "fast"
# 16) "slow"
# 17) "blocking"
# 18) "dangerous"
# 19) "connection"
# 20) "transaction"
# 21) "scripting"

# List commands in the "dangerous" category
redis-cli ACL CAT dangerous
# 1) "flushall"
# 2) "flushdb"
# 3) "keys"
# 4) "debug"
# 5) "sort"
# ...
```

### 3.6 The Default User

```bash
# The "default" user is used when clients AUTH with just a password (no username)
# In Redis 6+, control it like any other ACL user:

# Disable the default user entirely (force username+password auth)
ACL SETUSER default off

# Or restrict the default user
ACL SETUSER default on >legacyP@ss ~cache:* +@read +@connection

# Check current default user ACL
ACL GETUSER default
```

### 3.7 ACL Log (Audit Trail)

```bash
# View denied command attempts
redis-cli ACL LOG
# Shows recent permission denials with:
# - count: number of similar events
# - reason: "command", "key", "channel", "auth"
# - context: "toplevel", "multi", "lua"
# - object: the command or key that was denied
# - username: which user was denied
# - age-seconds: how long ago
# - client-info: IP, port, etc.

# View last 20 entries
redis-cli ACL LOG 20

# Reset the log
redis-cli ACL LOG RESET

# Configure log size
redis-cli CONFIG SET acllog-max-len 256
```

### 3.8 Password Rotation with ACLs

ACLs support multiple passwords per user, enabling zero-downtime rotation:

```bash
# Step 1: Add new password (keep old one active)
ACL SETUSER appuser >newP@ssw0rd2026

# Step 2: Update all clients to use the new password
# (rolling deployment across app instances)

# Step 3: Remove old password
ACL SETUSER appuser <oldP@ssw0rd2025

# Step 4: Save to ACL file
ACL SAVE

# Verify
ACL GETUSER appuser
```

### 3.9 ACL Best Practices

1. **Disable the default user** in production. Force explicit username+password auth.
2. **Use the principle of least privilege**. Grant only the commands and keys each user needs.
3. **Use hashed passwords** (`#hash`) in ACL files to avoid plaintext secrets on disk.
4. **Separate read and write users** for applications that have distinct read/write paths.
5. **Use ACL categories** rather than individual commands when possible (easier to maintain).
6. **Monitor ACL LOG** regularly for unexpected denials (may indicate misconfiguration or attack).
7. **Version control the ACL file**. Track changes to user permissions over time.

---

## 4. TLS Encryption

### 4.1 Why TLS for Redis

Redis commands and data travel in plaintext by default. On any shared network, TLS prevents:

- **Eavesdropping**: Intercepting AUTH passwords, sensitive key values
- **Tampering**: Modifying commands in transit (MITM)
- **Replay attacks**: Re-sending captured AUTH sequences

### 4.2 Generating Certificates

```bash
# Generate a self-signed CA (for internal use)
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days 1825 \
    -out ca.crt -subj "/CN=Redis Internal CA"

# Generate server certificate
openssl genrsa -out redis-server.key 4096
openssl req -new -key redis-server.key -out redis-server.csr \
    -subj "/CN=redis.internal.example.com"

# Sign with CA (include SANs for all hostnames/IPs)
openssl x509 -req -in redis-server.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out redis-server.crt -days 365 -sha256 \
    -extfile <(printf "subjectAltName=DNS:redis.internal.example.com,\
DNS:redis-0.redis.default.svc.cluster.local,\
IP:10.0.1.50")

# Generate client certificate (for mutual TLS)
openssl genrsa -out redis-client.key 4096
openssl req -new -key redis-client.key -out redis-client.csr \
    -subj "/CN=redis-client"
openssl x509 -req -in redis-client.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out redis-client.crt -days 365 -sha256

# Generate DH parameters for forward secrecy
openssl dhparam -out dhparam.pem 2048

# Set permissions
chmod 600 redis-server.key redis-client.key ca.key
chmod 644 redis-server.crt redis-client.crt ca.crt
```

### 4.3 TLS Server Configuration

```bash
# redis.conf -- TLS settings

# Disable non-TLS port
port 0

# Enable TLS port
tls-port 6379

# Server certificate and key
tls-cert-file /etc/redis/tls/redis-server.crt
tls-key-file /etc/redis/tls/redis-server.key

# CA certificate (for verifying clients in mutual TLS)
tls-ca-cert-file /etc/redis/tls/ca.crt

# DH parameters
tls-dh-params-file /etc/redis/tls/dhparam.pem

# Require client certificates (mutual TLS)
# Options: yes, no, optional
tls-auth-clients yes

# Minimum TLS version (never allow TLS 1.0 or 1.1)
tls-protocols "TLSv1.2 TLSv1.3"

# Cipher suites (TLS 1.2)
tls-ciphers "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"

# Cipher suites (TLS 1.3)
tls-ciphersuites "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256"

# Session caching (improves performance for repeated connections)
tls-session-caching yes
tls-session-cache-size 20480
tls-session-cache-timeout 300

# TLS for replication traffic
tls-replication yes

# TLS for cluster bus
tls-cluster yes
```

### 4.4 TLS Client Connection

```bash
# redis-cli with TLS
redis-cli --tls \
    --cert /etc/redis/tls/redis-client.crt \
    --key /etc/redis/tls/redis-client.key \
    --cacert /etc/redis/tls/ca.crt \
    -h redis.internal.example.com \
    -p 6379

# Test TLS connection
redis-cli --tls --cacert ca.crt PING
# PONG

# Verify certificate details from the server
openssl s_client -connect redis.internal.example.com:6379 \
    -CAfile ca.crt -cert redis-client.crt -key redis-client.key \
    </dev/null 2>/dev/null | openssl x509 -noout -subject -dates
```

### 4.5 TLS Performance Impact

TLS adds CPU overhead for encryption/decryption:

```bash
# Without TLS
redis-benchmark -t set,get -n 100000 -c 50
# SET: ~150,000 ops/sec
# GET: ~155,000 ops/sec

# With TLS
redis-benchmark --tls --cert client.crt --key client.key --cacert ca.crt \
    -t set,get -n 100000 -c 50
# SET: ~85,000 ops/sec  (~40-50% reduction)
# GET: ~90,000 ops/sec

# Mitigation strategies:
# 1. Use TLS session caching (reduces handshake overhead for reconnections)
# 2. Use connection pooling (amortizes handshake cost)
# 3. Use TLS 1.3 (1-RTT handshake vs 2-RTT for TLS 1.2)
# 4. Use hardware AES-NI acceleration (most modern CPUs support it)
# 5. Use Unix sockets for same-host connections (bypasses TLS entirely)
```

### 4.6 Certificate Rotation

```bash
# Zero-downtime certificate rotation (Redis 7+)

# 1. Generate new certificates signed by the same CA (or a new CA)
# 2. Copy new certs to the server
# 3. Reload at runtime:
redis-cli CONFIG SET tls-cert-file /etc/redis/tls/redis-server-new.crt
redis-cli CONFIG SET tls-key-file /etc/redis/tls/redis-server-new.key

# If changing CA:
# 1. First, add the new CA to clients' trust stores
# 2. Then rotate the server certificate
# 3. Finally, remove the old CA from trust stores

# 4. For file-based rotation, prepare both certs in a combined CA file:
cat old-ca.crt new-ca.crt > combined-ca.crt
# Use combined-ca.crt during the transition period
```

---

## 5. Protected Mode

### 5.1 What Protected Mode Does

Protected mode is a safety net introduced in Redis 3.2. When enabled (the default), Redis refuses connections from non-loopback addresses if no password is set:

```bash
# redis.conf
protected-mode yes   # Default: yes

# Protected mode activates when BOTH conditions are true:
# 1. No password is set (no requirepass, no ACL passwords)
# 2. Redis is bound to all interfaces (bind not set, or bind 0.0.0.0)

# Error when protected mode blocks a connection:
# "DENIED Redis is running in protected mode because protected mode is enabled,
#  no password is set, and Redis is listening on all interfaces."
```

### 5.2 When to Disable Protected Mode

Never in production without compensating controls. The only legitimate cases:

```bash
# Development environment with firewall-isolated VM
protected-mode no
bind 0.0.0.0

# Always combine with:
# - Firewall rules blocking external access
# - VPC/VLAN isolation
# - AUTH password (which disables protected mode behavior anyway)
```

Setting a password (via `requirepass` or ACLs) effectively makes protected mode irrelevant, since the auth check takes priority.

---

## 6. Network Security

### 6.1 Bind Configuration

```bash
# Bind to specific interfaces only
# NEVER bind 0.0.0.0 in production without TLS + AUTH
bind 127.0.0.1 10.0.1.50

# IPv6 support
bind 127.0.0.1 ::1 10.0.1.50

# Bind to Unix socket (highest performance, local only)
unixsocket /var/run/redis/redis.sock
unixsocketperm 770

# Disable TCP entirely (Unix socket only -- maximum isolation)
port 0
unixsocket /var/run/redis/redis.sock
```

### 6.2 Disabling Dangerous Commands

```bash
# redis.conf -- rename or disable dangerous commands

# Completely disable (empty string)
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
rename-command CONFIG ""
rename-command SHUTDOWN ""
rename-command KEYS ""
rename-command MODULE ""

# Rename to obscure strings (less secure than ACLs, but additional layer)
rename-command CONFIG "CONFIG_a8f3b2e1d7c9"
rename-command SHUTDOWN "SHUTDOWN_7c9d4e5f2a3b"

# In Redis 7+ with ACLs, prefer ACL rules over rename-command
# ACLs are more flexible, per-user, and auditable
```

### 6.3 Firewall Rules

```bash
# iptables: Allow Redis only from specific subnets
iptables -A INPUT -p tcp --dport 6379 -s 10.0.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 6379 -s 10.0.2.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 6379 -j DROP

# Sentinel port
iptables -A INPUT -p tcp --dport 26379 -s 10.0.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 26379 -j DROP

# nftables equivalent
nft add rule inet filter input tcp dport 6379 ip saddr 10.0.1.0/24 accept
nft add rule inet filter input tcp dport 6379 ip saddr 10.0.2.0/24 accept
nft add rule inet filter input tcp dport 6379 drop

# AWS Security Group (Terraform)
resource "aws_security_group_rule" "redis_ingress" {
  type              = "ingress"
  from_port         = 6379
  to_port           = 6379
  protocol          = "tcp"
  cidr_blocks       = ["10.0.0.0/16"]
  security_group_id = aws_security_group.redis.id
  description       = "Redis access from VPC only"
}
```

### 6.4 Rate Limiting AUTH Attempts

```bash
# Redis does not natively rate-limit AUTH attempts
# Implement at the network level:

# iptables: limit new connections per source IP to 10/minute
iptables -A INPUT -p tcp --dport 6379 -m conntrack --ctstate NEW \
    -m recent --set --name redis_auth
iptables -A INPUT -p tcp --dport 6379 -m conntrack --ctstate NEW \
    -m recent --update --seconds 60 --hitcount 10 --name redis_auth -j DROP

# Connection limits in redis.conf
maxclients 10000
timeout 300           # Close idle connections after 5 minutes
tcp-keepalive 300     # TCP keepalive interval
```

### 6.5 Securing Redis in Docker

```yaml
# docker-compose.yml -- secure Redis
services:
  redis:
    image: redis:7.4-alpine
    command: >
      redis-server
      --requirepass "${REDIS_PASSWORD}"
      --bind 0.0.0.0
      --protected-mode yes
      --tls-port 6379
      --port 0
      --tls-cert-file /tls/redis.crt
      --tls-key-file /tls/redis.key
      --tls-ca-cert-file /tls/ca.crt
      --tls-auth-clients yes
    ports:
      - "127.0.0.1:6379:6379"   # Bind to localhost only on the host
    volumes:
      - redis-data:/data
      - ./tls:/tls:ro
    networks:
      - backend
    deploy:
      resources:
        limits:
          memory: 4g

volumes:
  redis-data:

networks:
  backend:
    internal: true               # No external access
```

### 6.6 Disabling Lua Script Abuse

```bash
# Limit Lua script execution time (milliseconds)
lua-time-limit 5000

# Disable EVAL for non-admin users via ACL
ACL SETUSER appuser -eval -evalsha -evalro -evalsha_ro -script -function

# Disable module loading at runtime
rename-command MODULE ""
# Or via ACL:
ACL SETUSER appuser -module
```

### 6.7 MONITOR Command Security

```bash
# MONITOR streams ALL commands in real time -- severe risk in production
# It exposes plaintext passwords in AUTH commands
# It also degrades performance by ~50%

# Never leave MONITOR running in production
# If needed for brief debugging, use CLIENT LIST filtering instead:
CLIENT LIST TYPE normal

# Restrict MONITOR via ACL
ACL SETUSER appuser -monitor
```

---

## 7. Sentinel Architecture

### 7.1 What Sentinel Solves

Redis Sentinel provides automatic high availability. Without Sentinel, if the master fails, someone must manually:

1. Detect the failure
2. Choose a replica to promote
3. Reconfigure the promoted replica as master
4. Reconfigure all other replicas to follow the new master
5. Update all application clients to point to the new master

Sentinel automates all five steps.

### 7.2 Sentinel Components

```
                    +------------+
                    | Sentinel   |
                    |    #1      |
                    +-----+------+
                          |
         +----------------+----------------+
         |                |                |
    +----+----+     +-----+-----+    +-----+-----+
    |Sentinel |     |   Redis   |    |   Redis   |
    |   #2    |     |  Master   |    |  Replica  |
    +----+----+     +-----+-----+    +-----+-----+
         |                |                |
         |           +----+-----+          |
    +----+----+     |   Redis   |          |
    |Sentinel |     |  Replica  |<---------+
    |   #3    |     +----------+
    +---------+
```

Sentinels communicate with each other and with Redis instances to:
- **Monitor**: Continuously check if master and replicas are working
- **Notify**: Alert administrators or systems about failures
- **Failover**: Promote a replica to master when the master fails
- **Configuration provider**: Clients query Sentinel for the current master address

### 7.3 Sentinel vs. Redis Cluster

| Feature | Sentinel | Cluster |
|---------|----------|---------|
| Purpose | HA (failover only) | HA + horizontal sharding |
| Data sharding | No (single dataset) | Yes (16384 hash slots) |
| Max dataset size | Single node memory | Sum of all master node memories |
| Write scaling | No (single master) | Yes (multiple masters) |
| Minimum nodes | 3 Sentinel + 1 master + 1 replica | 6 (3 masters + 3 replicas) |
| Client complexity | Sentinel-aware client | Cluster-aware client |
| When to use | Dataset fits on one machine | Need to shard across machines |

### 7.4 Quorum and Majority

**Quorum**: The minimum number of Sentinels that must agree a master is down before initiating failover.

**Majority**: The minimum number of Sentinels that must be reachable to authorize a failover. Always `floor(N/2) + 1`.

```
Sentinels   Quorum    Majority    Tolerates Failures
    3          2          2              1
    5          3          3              2
    7          4          4              3
```

Why these numbers matter:

```
3 Sentinels, quorum=2:
  1 Sentinel down: quorum=2 met (2 remain), majority=2 met -> failover works
  2 Sentinels down: quorum=2 not met (only 1 remains) -> no failover

5 Sentinels, quorum=3:
  1 down: 4 remain, quorum met, majority met -> works
  2 down: 3 remain, quorum=3 met, majority=3 met -> works
  3 down: 2 remain, quorum not met -> no failover
```

### 7.5 Leader Election

When a master is detected as down:

1. A Sentinel detects the master is unresponsive and marks it **SDOWN** (subjectively down)
2. It asks other Sentinels to confirm. When `quorum` Sentinels agree, the master is marked **ODOWN** (objectively down)
3. The Sentinel that detected ODOWN requests votes from a majority of Sentinels to become the **failover leader** (Raft-like protocol)
4. The leader selects the best replica (by priority, replication offset, run ID)
5. The leader sends `REPLICAOF NO ONE` to the chosen replica
6. The leader reconfigures remaining replicas to follow the new master
7. The leader updates its configuration epoch

### 7.6 Failover Timeline

```
T+0s     Master stops responding
T+5s     First Sentinel detects SDOWN (after down-after-milliseconds)
T+5.1s   Sentinel queries others for ODOWN confirmation
T+5.5s   ODOWN confirmed (quorum reached)
T+5.5s   Leader election begins
T+6s     Leader elected, selects best replica
T+6.5s   REPLICAOF NO ONE sent to chosen replica
T+7s     Replica promoted, starts accepting writes
T+8s     Other replicas reconfigured to new master
T+10s    Clients discover new master via Sentinel
Total:   ~10 seconds (configurable via down-after-milliseconds)
```

### 7.7 Replica Selection Priority

The failover leader selects a replica based on (in order):

1. **replica-priority**: Lower values preferred (0 = never promote)
2. **Replication offset**: Most up-to-date replica preferred
3. **Run ID**: Lexicographically smallest as tiebreaker

```bash
# Set replica priority (in redis.conf on each replica)
replica-priority 100   # Default: 100
replica-priority 0     # Never promote this replica (e.g., analytics replica)

# Check current replication state
redis-cli -h replica1 INFO replication
# role:slave
# master_link_status:up
# slave_repl_offset:1234567
# slave_priority:100
```

---

## 8. Sentinel Configuration

### 8.1 Basic Sentinel Configuration

```bash
# sentinel.conf

# Port for Sentinel (default: 26379)
port 26379

# Bind to internal interfaces
bind 10.0.1.51 127.0.0.1

# Sentinel needs its own data directory for state persistence
dir /var/lib/redis-sentinel

# Password for Sentinel itself (Redis 6.2+)
requirepass sentinel_password_here

# Monitor definition:
# sentinel monitor <master-name> <ip> <port> <quorum>
sentinel monitor mymaster 10.0.1.50 6379 2

# Password for connecting to monitored Redis instances
sentinel auth-pass mymaster "MasterP@ssword"

# ACL user for Sentinel connections to Redis (Redis 6.2+)
# sentinel auth-user mymaster sentinel_user

# Time before marking a master SDOWN
sentinel down-after-milliseconds mymaster 5000

# Number of replicas reconfigured simultaneously during failover
sentinel parallel-syncs mymaster 1

# Maximum time for failover to complete
sentinel failover-timeout mymaster 60000

# Notification script (called on any Sentinel event)
# sentinel notification-script mymaster /usr/local/bin/sentinel-notify.sh

# Reconfig script (called after failover completes)
# sentinel client-reconfig-script mymaster /usr/local/bin/sentinel-reconfig.sh

# Deny runtime script changes (security hardening)
sentinel deny-scripts-reconfig yes

# DNS hostname resolution (Redis 6.2+)
sentinel resolve-hostnames yes
sentinel announce-hostnames yes
```

### 8.2 Multi-Master Sentinel Configuration

A single Sentinel deployment can monitor multiple independent master groups:

```bash
# sentinel.conf -- monitoring two masters

# Master 1: User database
sentinel monitor users-master 10.0.1.50 6379 2
sentinel auth-pass users-master "usersP@ss"
sentinel down-after-milliseconds users-master 5000
sentinel failover-timeout users-master 60000
sentinel parallel-syncs users-master 1

# Master 2: Session store
sentinel monitor sessions-master 10.0.2.50 6379 2
sentinel auth-pass sessions-master "sessionsP@ss"
sentinel down-after-milliseconds sessions-master 5000
sentinel failover-timeout sessions-master 30000
sentinel parallel-syncs sessions-master 2
```

### 8.3 Deploying Sentinel

Minimum deployment: **3 Sentinel instances on separate machines**.

```bash
# Start Sentinel
redis-sentinel /etc/redis/sentinel.conf
# or
redis-server /etc/redis/sentinel.conf --sentinel

# systemd unit file
cat > /etc/systemd/system/redis-sentinel.service << 'EOF'
[Unit]
Description=Redis Sentinel
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=redis
Group=redis
ExecStart=/usr/local/bin/redis-sentinel /etc/redis/sentinel.conf
ExecStop=/usr/local/bin/redis-cli -p 26379 shutdown
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable redis-sentinel
systemctl start redis-sentinel
```

### 8.4 Sentinel Placement Guidelines

```
WRONG: All Sentinels on the same machine or rack
  Single point of failure defeats the purpose

WRONG: Sentinels co-located only with Redis instances
  If the machine running master + Sentinel fails, you lose a Sentinel vote

RIGHT: Sentinels distributed across failure domains
  Different machines, racks, or availability zones
  At least one Sentinel reachable from the application tier

Example 3-AZ deployment:
  AZ-A: Redis Master  + Sentinel #1
  AZ-B: Redis Replica1 + Sentinel #2
  AZ-C: Redis Replica2 + Sentinel #3
```

### 8.5 Sentinel TLS Configuration

```bash
# sentinel.conf -- TLS

tls-port 26379
port 0

tls-cert-file /etc/redis/tls/sentinel.crt
tls-key-file /etc/redis/tls/sentinel.key
tls-ca-cert-file /etc/redis/tls/ca.crt

# TLS for communication with Redis instances
tls-replication yes
```

### 8.6 Sentinel Configuration Auto-Rewrite

Sentinel automatically rewrites `sentinel.conf` to persist runtime state changes (failover results, discovered replicas). This is expected:

```bash
# After failover, sentinel.conf may change from:
sentinel monitor mymaster 10.0.1.50 6379 2
# to:
sentinel monitor mymaster 10.0.2.50 6379 2

# Known replicas and Sentinels are also persisted:
sentinel known-replica mymaster 10.0.1.50 6379
sentinel known-sentinel mymaster 10.0.3.50 26379 <runid>
```

Do not store `sentinel.conf` on read-only filesystems. Sentinel must be able to write to its own config.

### 8.7 Split-Brain Prevention

```bash
# On the Redis master, configure:
# Reject writes if fewer than N replicas are connected with lag <= M seconds
min-replicas-to-write 1
min-replicas-max-lag 10

# This prevents the old master from accepting writes during a network partition
# If it loses contact with all replicas, it stops accepting writes
# This is the primary defense against split-brain data divergence
```

---

## 9. Client-Side Discovery

### 9.1 How Clients Find the Master

Clients should never connect to a fixed Redis IP. They query Sentinel for the current master:

```bash
# Query Sentinel for master address
redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster
# 1) "10.0.2.50"
# 2) "6379"

# Get all master info
redis-cli -p 26379 SENTINEL master mymaster

# List all replicas
redis-cli -p 26379 SENTINEL replicas mymaster

# List all Sentinels
redis-cli -p 26379 SENTINEL sentinels mymaster
```

### 9.2 Python Client with Sentinel

```python
from redis.sentinel import Sentinel

sentinel = Sentinel(
    [
        ('sentinel-1.internal', 26379),
        ('sentinel-2.internal', 26379),
        ('sentinel-3.internal', 26379),
    ],
    socket_timeout=0.5,
    sentinel_kwargs={'password': 'sentinel_password'}
)

# Connection to the master (auto-follows failover)
master = sentinel.master_for(
    'mymaster',
    password='masterP@ss',
    socket_timeout=0.5,
    retry_on_timeout=True,
    decode_responses=True
)

# Connection to a replica (read-only)
replica = sentinel.slave_for(
    'mymaster',
    password='masterP@ss',
    socket_timeout=0.5,
    decode_responses=True
)

master.set('key', 'value')
value = replica.get('key')
```

### 9.3 Node.js Client with Sentinel (ioredis)

```javascript
const Redis = require('ioredis');

const redis = new Redis({
    sentinels: [
        { host: 'sentinel-1.internal', port: 26379 },
        { host: 'sentinel-2.internal', port: 26379 },
        { host: 'sentinel-3.internal', port: 26379 },
    ],
    name: 'mymaster',
    password: 'masterP@ss',
    sentinelPassword: 'sentinel_password',
    role: 'master',
    enableReadyCheck: true,
    retryStrategy: (times) => Math.min(times * 200, 2000),
});

redis.on('connect', () => console.log('Connected to Redis master'));
redis.on('error', (err) => console.error('Redis error:', err));
redis.on('+switch-master', (data) => {
    console.log('Master switched:', data);
});

await redis.set('key', 'value');
const value = await redis.get('key');
```

### 9.4 Java Client with Sentinel (Lettuce)

```java
import io.lettuce.core.RedisURI;
import io.lettuce.core.RedisClient;
import io.lettuce.core.api.StatefulRedisConnection;
import io.lettuce.core.masterreplica.MasterReplica;
import io.lettuce.core.codec.StringCodec;
import io.lettuce.core.ReadFrom;

RedisURI sentinelUri = RedisURI.builder()
    .withSentinel("sentinel-1.internal", 26379)
    .withSentinel("sentinel-2.internal", 26379)
    .withSentinel("sentinel-3.internal", 26379)
    .withSentinelMasterId("mymaster")
    .withPassword("masterP@ss".toCharArray())
    .build();

RedisClient client = RedisClient.create(sentinelUri);
StatefulRedisMasterReplicaConnection<String, String> connection =
    MasterReplica.connect(client, StringCodec.UTF8, sentinelUri);

connection.setReadFrom(ReadFrom.REPLICA_PREFERRED);

RedisCommands<String, String> commands = connection.sync();
commands.set("key", "value");
String value = commands.get("key");
```

### 9.5 Go Client with Sentinel

```go
package main

import (
    "context"
    "fmt"
    "github.com/redis/go-redis/v9"
)

func main() {
    ctx := context.Background()

    client := redis.NewFailoverClient(&redis.FailoverOptions{
        MasterName:       "mymaster",
        SentinelAddrs:    []string{
            "sentinel-1.internal:26379",
            "sentinel-2.internal:26379",
            "sentinel-3.internal:26379",
        },
        Password:         "masterP@ss",
        SentinelPassword: "sentinel_password",
        DB:               0,
    })

    err := client.Set(ctx, "key", "value", 0).Err()
    if err != nil {
        panic(err)
    }

    val, err := client.Get(ctx, "key").Result()
    if err != nil {
        panic(err)
    }
    fmt.Println("key:", val)
}
```

### 9.6 HAProxy as Sentinel-Aware Proxy

For clients that do not support Sentinel natively:

```
# /etc/haproxy/haproxy.cfg

frontend redis_front
    bind *:6380
    default_backend redis_back

backend redis_back
    option tcp-check
    tcp-check connect
    tcp-check send AUTH\ masterP@ss\r\n
    tcp-check expect string +OK
    tcp-check send PING\r\n
    tcp-check expect string +PONG
    tcp-check send info\ replication\r\n
    tcp-check expect string role:master
    tcp-check send QUIT\r\n
    tcp-check expect string +OK

    server redis-1 10.0.1.50:6379 check inter 3s fall 3 rise 2
    server redis-2 10.0.2.50:6379 check inter 3s fall 3 rise 2
    server redis-3 10.0.3.50:6379 check inter 3s fall 3 rise 2
```

HAProxy checks `INFO replication` and only routes to the node reporting `role:master`.

---

## 10. Monitoring Sentinel

### 10.1 Sentinel INFO Command

```bash
redis-cli -p 26379 INFO sentinel
# sentinel_masters:1
# sentinel_tilt:0
# sentinel_running_scripts:0
# sentinel_scripts_queue_length:0
# master0:name=mymaster,status=ok,address=10.0.2.50:6379,slaves=2,sentinels=3
```

### 10.2 Key Sentinel Events (Pub/Sub)

```bash
redis-cli -p 26379 PSUBSCRIBE '*'
# Events:
# +sdown           -- Instance is subjectively down
# -sdown           -- Instance is no longer subjectively down
# +odown           -- Instance is objectively down (quorum reached)
# -odown           -- Instance is no longer objectively down
# +switch-master   -- Master address changed (failover completed)
# +failover-state-reconf-slaves -- Reconfiguring replicas
# +slave-reconf-done -- Replica reconfiguration complete
# +sentinel        -- New Sentinel discovered
# +slave           -- New replica discovered
# +tilt            -- Sentinel entered TILT mode
# -tilt            -- Sentinel exited TILT mode
```

### 10.3 Prometheus Alerting Rules

```yaml
# prometheus-alerts.yml
groups:
  - name: redis_sentinel
    rules:
      - alert: RedisMasterDown
        expr: redis_sentinel_master_status > 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Redis master {{ $labels.master_name }} is down"

      - alert: RedisSentinelQuorumLow
        expr: redis_sentinel_master_ok_sentinels < 2
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Sentinel quorum at risk for {{ $labels.master_name }}"

      - alert: RedisReplicaDown
        expr: redis_sentinel_master_ok_slaves < redis_sentinel_master_slaves
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis replica(s) down for {{ $labels.master_name }}"
```

### 10.4 Sentinel Health Check Script

```bash
#!/bin/bash
# /usr/local/bin/sentinel-health-check.sh

SENTINELS=("sentinel-1:26379" "sentinel-2:26379" "sentinel-3:26379")
MASTER_NAME="mymaster"

echo "=== Sentinel Cluster Health ==="
for s in "${SENTINELS[@]}"; do
    HOST=$(echo "$s" | cut -d: -f1)
    PORT=$(echo "$s" | cut -d: -f2)

    RESULT=$(redis-cli -h "$HOST" -p "$PORT" SENTINEL master "$MASTER_NAME" 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "UNREACHABLE: Sentinel $s"
        continue
    fi

    STATUS=$(echo "$RESULT" | grep -A1 "^flags$" | tail -1)
    SLAVES=$(echo "$RESULT" | grep -A1 "^num-slaves$" | tail -1)
    echo "Sentinel $s: master_flags=$STATUS replicas=$SLAVES"
done

# Quorum check
QUORUM_RESULT=$(redis-cli -h sentinel-1 -p 26379 SENTINEL ckquorum "$MASTER_NAME" 2>/dev/null)
echo "Quorum: $QUORUM_RESULT"
```

---

## 11. Troubleshooting

### 11.1 Sentinel Not Failing Over

```bash
# Check 1: Is quorum met?
redis-cli -p 26379 SENTINEL ckquorum mymaster
# "OK 3 usable Sentinels. Quorum and failover authorization is possible."
# or: "NOQUORUM ..."

# Check 2: Is ODOWN achieved?
redis-cli -p 26379 SENTINEL master mymaster | grep -A1 flags
# If "sdown" but not "odown", other Sentinels disagree

# Check 3: Is failover-timeout blocking a retry?
# After a failed failover, Sentinel waits 2x failover-timeout before retrying

# Check 4: Is there a valid replica to promote?
redis-cli -p 26379 SENTINEL replicas mymaster
# Replicas with priority=0 or link-down are skipped
```

### 11.2 Split-Brain Detection

```bash
# Two instances both reporting role:master
for host in redis-1 redis-2 redis-3; do
    echo "$host: $(redis-cli -h $host INFO replication | grep role)"
done

# If two masters exist, data divergence has occurred
# Resolve: identify which has more data, manually demote the other
```

### 11.3 TLS Handshake Failures

```bash
# Error: "SSL_connect: certificate verify failed"
# Check certificate validity
openssl x509 -in redis-server.crt -noout -dates

# Check SAN matches hostname
openssl x509 -in redis-server.crt -noout -text | grep -A1 "Subject Alternative Name"

# Verify CA chain
openssl verify -CAfile ca.crt redis-server.crt
```

### 11.4 ACL Permission Denied

```bash
# Error: "NOPERM this user has no permissions to run the 'config' command"
redis-cli --user admin --pass adm1nStr0ng ACL GETUSER appuser
redis-cli --user admin --pass adm1nStr0ng ACL LOG 10

# Fix: Add needed permission
ACL SETUSER appuser +config|get   # Redis 7+ subcommand ACL
```

### 11.5 Stale Sentinel Configuration

```bash
# Sentinel reports old/wrong master address
# Fix: Reset Sentinel state
redis-cli -p 26379 SENTINEL RESET mymaster
# Forces rediscovery of master, replicas, and other Sentinels
```

### 11.6 Replica Not Syncing After Failover

```bash
# Old master shows role:slave but master_link_status:down
# Check: password mismatch, network issue, or TLS mismatch
redis-cli -h old-master INFO replication
# Verify masterauth matches the new master's password
```

---

## 12. Q&A

**Q1: Should I use Sentinel or Redis Cluster for HA?**
A: Sentinel: single master + replicas, dataset fits on one machine. Cluster: need to shard across nodes. Sentinel is simpler to operate; Cluster scales horizontally.

**Q2: How many Sentinels should I run?**
A: Minimum 3 (tolerates 1 failure). Use 5 for production systems (tolerates 2). Always odd numbers to avoid tie votes.

**Q3: Can Sentinel monitor Redis Cluster?**
A: No. Cluster has its own built-in failover. Sentinel is for standalone master-replica setups only.

**Q4: What is the default user in Redis ACLs?**
A: The user clients connect as when they AUTH with password only (no username). Disable it in production to force explicit usernames.

**Q5: Does TLS work with Redis Cluster?**
A: Yes. Set `tls-cluster yes`. All cluster bus traffic uses TLS. Requires Redis 6.0+.

**Q6: What happens to writes during failover?**
A: Writes to the old master after it becomes unreachable are lost. Clients reconnect to the new master via Sentinel. Use `min-replicas-to-write` to reject writes on a partitioned master.

**Q7: Can I use Redis ACLs with Sentinel?**
A: Yes. Create a dedicated Sentinel user with permissions: `+ping +info +multi +exec +subscribe +publish +slaveof +replicaof +config|set +config|get +client +auth`.

**Q8: What is TILT mode in Sentinel?**
A: Activates when Sentinel detects abnormal system behavior (e.g., timer interrupt stalled). In TILT, Sentinel monitors but does not act on failures. Exits after 30 seconds of stable operation.

**Q9: How do I rotate passwords without downtime?**
A: ACLs support multiple passwords. Add the new password, update clients, remove the old one. No restart needed.

**Q10: Is rename-command deprecated?**
A: Not formally, but ACLs are preferred in Redis 6+. ACLs are per-user; rename-command is server-wide.

**Q11: How do I prevent a replica from being promoted?**
A: Set `replica-priority 0` on that replica. Sentinel will never auto-promote it.

**Q12: What is `sentinel deny-scripts-reconfig`?**
A: Prevents runtime changes to notification/reconfig scripts via `SENTINEL SET`. Security hardening -- scripts should be set in config files only.

**Q13: Can Sentinel handle cross-region deployments?**
A: Yes, but carefully. Place Sentinels in each region. Use `sentinel announce-ip` and `sentinel announce-port` for NAT traversal. Set DR-region replicas to `replica-priority 0` to avoid cross-region promotion unless deliberately overridden.

---

## 13. Exercises

### Exercise 1: Configure ACLs for Multi-Team Access

1. Create a Redis instance with these users:
   - `admin`: full access
   - `web_app`: read/write to `web:*` keys, no admin commands
   - `analytics`: read-only access to all keys
   - `worker`: read/write to `queue:*`, limited to list commands
2. Store ACLs in a file and reload
3. Test each user can only access permitted keys and commands
4. Verify denied commands appear in `ACL LOG`
5. Rotate the `web_app` password without disconnecting active sessions

### Exercise 2: Set Up TLS Encryption

1. Generate CA, server cert, and client cert
2. Configure Redis to accept only TLS connections (`port 0`, `tls-port 6379`)
3. Connect with `redis-cli --tls` and verify
4. Configure a Python client to connect over TLS
5. Benchmark with/without TLS to measure performance impact
6. Enable mutual TLS (require client certificates)

### Exercise 3: Deploy Redis Sentinel (3-Node)

1. Start one Redis master and two replicas
2. Start three Sentinel instances monitoring the master
3. Verify Sentinel discovers all replicas and other Sentinels
4. Kill the master process
5. Observe failover in Sentinel logs
6. Verify the promoted replica is accepting writes
7. Bring the old master back and verify it becomes a replica

### Exercise 4: Client Failover Handling

1. Write a Python script using `redis-py` Sentinel support
2. Connect to master via Sentinel, write keys in a loop
3. While the script runs, trigger manual failover: `SENTINEL FAILOVER mymaster`
4. Verify the script reconnects and continues without crashing
5. Read from a replica via Sentinel and verify data consistency

### Exercise 5: Split-Brain Prevention

1. Configure `min-replicas-to-write 1` and `min-replicas-max-lag 10`
2. Stop both replicas
3. Try writing to the master -- verify it rejects writes with `NOREPLICAS`
4. Start one replica back
5. Verify writes resume after synchronization

### Exercise 6: Security Hardening Audit

Audit a Redis deployment:
1. Check AUTH status (`CONFIG GET requirepass`)
2. Check protected mode (`CONFIG GET protected-mode`)
3. Check bind address (`CONFIG GET bind`)
4. Test dangerous commands (FLUSHALL, DEBUG, CONFIG, KEYS)
5. Check TLS (`CONFIG GET tls-port`)
6. Review ACL configuration (`ACL LIST`)
7. Check for default user with unrestricted access
8. Document findings and remediation

### Exercise 7: Sentinel Monitoring Setup

1. Deploy Prometheus + redis_exporter for Sentinel metrics
2. Create Grafana dashboards for master status, replica count, Sentinel count
3. Configure alerts for master down, quorum risk, replica failure
4. Trigger a failover and observe dashboard and alert behavior

---

*Questo documento fa parte del modulo 06 "NoSQL Redis" della Data Encyclopedia.*
