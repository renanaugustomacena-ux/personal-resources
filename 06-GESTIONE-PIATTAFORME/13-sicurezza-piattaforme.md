---
corso: "Gestione Piattaforme e DevOps"
fase: "6 — Sicurezza e Compliance"
modulo: 13
titolo: "Sicurezza delle Piattaforme"
versione: "OWASP 2025 · CIS Benchmarks v9 · NIST CSF 2.0"
livello: "Avanzato"
prerequisiti:
  - "05-kubernetes.md"
  - "09-service-mesh.md"
  - "10-load-balancer-reverse-proxy.md"
obiettivi:
  - "Applicare il modello defense-in-depth a tutti i layer dell'infrastruttura"
  - "Implementare zero-trust networking con mTLS, identity-aware proxy e microsegmentazione"
  - "Configurare vulnerability scanning automatico (Trivy, tfsec, Checkov, gitleaks) nella CI/CD"
  - "Eseguire hardening di OS, container e cluster Kubernetes seguendo CIS Benchmarks"
  - "Progettare e testare procedure di incident response con playbook e tabletop exercise"
tag: [zero-trust, defense-in-depth, cis-benchmark, vulnerability-scanning, hardening, incident-response, waf, mtls]
---

# Sicurezza delle Piattaforme — Documentazione Completa

> **Modulo 13** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Applicare il modello defense-in-depth a tutti i layer dell'infrastruttura
> 2. Implementare zero-trust networking con mTLS, identity-aware proxy e microsegmentazione
> 3. Configurare vulnerability scanning automatico (Trivy, tfsec, Checkov, gitleaks) nella CI/CD
> 4. Eseguire hardening di OS, container e cluster Kubernetes seguendo CIS Benchmarks
> 5. Progettare e testare procedure di incident response con playbook e tabletop exercise
>
> **Prerequisiti:** [Kubernetes](05-kubernetes.md) · [Service Mesh](09-service-mesh.md) · [Load Balancer e Reverse Proxy](10-load-balancer-reverse-proxy.md)
> **Tempo stimato:** 10-14 ore · **Livello:** Avanzato

## Idee guida

1. **Defense in depth a layer multipli.** WAF, DDoS, IAM, network seg, encryption.
2. **Zero-trust: never trust, always verify.** Pubblico/privato non garantisce trust.
3. **CIS Benchmark per OS + Kubernetes + cloud.** Standard di partenza.
4. **Automated scan: trivy + tfsec + checkov + gitleaks.** Pre-deploy.


## Indice

1. [Panoramica e Principi Fondamentali](#1-panoramica-e-principi-fondamentali)
2. [Network Security e Segmentation](#2-network-security-e-segmentation)
3. [Web Application Firewall (WAF)](#3-web-application-firewall-waf)
4. [DDoS Mitigation](#4-ddos-mitigation)
5. [Vulnerability Management](#5-vulnerability-management)
6. [Zero Trust Architecture](#6-zero-trust-architecture)
7. [Runtime Security](#7-runtime-security)
8. [SIEM e Security Operations](#8-siem-e-security-operations)
9. [Cloud Security Posture Management (CSPM)](#9-cloud-security-posture-management-cspm)
10. [Supply Chain Security](#10-supply-chain-security)
11. [Incident Response](#11-incident-response)
12. [Best Practices](#12-best-practices)

---

## 1. Panoramica e Principi Fondamentali

### Defense in Depth

Il principio di **Defense in Depth** prevede l'implementazione di molteplici livelli di sicurezza sovrapposti.
La compromissione di un singolo livello non deve garantire all'attaccante l'accesso completo al sistema.
I livelli tipici includono: perimetro di rete, segmentazione interna, sicurezza applicativa, protezione dei dati,
controllo degli accessi e monitoraggio continuo.

```
┌─────────────────────────────────────────────────┐
│  Layer 1: Perimetro (Firewall, WAF, DDoS)       │
│  ┌─────────────────────────────────────────────┐ │
│  │  Layer 2: Rete (Segmentazione, IDS/IPS)     │ │
│  │  ┌─────────────────────────────────────────┐ │ │
│  │  │  Layer 3: Host (Hardening, EDR)         │ │ │
│  │  │  ┌─────────────────────────────────────┐ │ │ │
│  │  │  │  Layer 4: Applicazione (Auth, WAF)   │ │ │ │
│  │  │  │  ┌─────────────────────────────────┐ │ │ │ │
│  │  │  │  │  Layer 5: Dati (Encryption, DLP) │ │ │ │ │
│  │  │  │  └─────────────────────────────────┘ │ │ │ │
│  │  │  └─────────────────────────────────────┘ │ │ │
│  │  └─────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Zero Trust Model — Never Trust, Always Verify

Il modello **Zero Trust** parte dal presupposto che nessuna entita, interna o esterna, debba essere considerata
automaticamente affidabile. Ogni richiesta di accesso deve essere autenticata, autorizzata e continuamente
validata, indipendentemente dalla posizione nella rete.

Principi chiave:
- **Verify explicitly**: autenticare e autorizzare ogni richiesta basandosi su tutti i segnali disponibili
  (identita, posizione, stato del dispositivo, classificazione dei dati, anomalie)
- **Least privilege access**: limitare l'accesso al minimo necessario con politiche just-in-time e just-enough-access
- **Assume breach**: progettare come se la compromissione fosse gia avvenuta, minimizzare il blast radius,
  segmentare l'accesso, verificare la crittografia end-to-end, usare analytics per rilevare anomalie

### Principio del Least Privilege

Ogni utente, processo o servizio deve avere esclusivamente i permessi strettamente necessari per svolgere
la propria funzione. Questo riduce la superficie di attacco e limita il danno potenziale in caso di compromissione.

```bash
# Esempio: creazione di un service account con permessi minimi su Kubernetes
kubectl create serviceaccount app-reader --namespace=production

# Role con permessi minimi (solo lettura sui pods)
cat <<'EOF' > minimal-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
EOF

kubectl apply -f minimal-role.yaml
kubectl create rolebinding app-reader-binding \
  --role=pod-reader \
  --serviceaccount=production:app-reader \
  --namespace=production
```

### Micro-segmentation

La **micro-segmentation** divide la rete in segmenti granulari, applicando policy di sicurezza a livello
di singolo workload o applicazione, anziche a livello di segmento di rete tradizionale.
Questo impedisce il movimento laterale degli attaccanti all'interno dell'infrastruttura.

### Shift-Left Security e DevSecOps Pipeline

Lo **shift-left** integra la sicurezza nelle fasi iniziali del ciclo di sviluppo, anziche trattarla come
un'aggiunta tardiva. Il modello **DevSecOps** incorpora i controlli di sicurezza direttamente nella pipeline CI/CD.

```yaml
# Pipeline DevSecOps di esempio (GitLab CI)
stages:
  - build
  - sast        # Static Application Security Testing
  - sca         # Software Composition Analysis
  - container   # Container Image Scanning
  - dast        # Dynamic Application Security Testing
  - deploy

sast_scan:
  stage: sast
  image: returntocorp/semgrep
  script:
    - semgrep ci --config=auto --json --output=sast-report.json
  artifacts:
    reports:
      sast: sast-report.json

dependency_check:
  stage: sca
  image: owasp/dependency-check
  script:
    - /usr/share/dependency-check/bin/dependency-check.sh
      --project "myapp"
      --scan /src
      --format JSON
      --out dependency-report.json
      --failOnCVSS 7

container_scan:
  stage: container
  image: aquasec/trivy
  script:
    - trivy image --severity HIGH,CRITICAL --exit-code 1 $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### Threat Modeling — STRIDE e DREAD

**STRIDE** classifica le minacce in sei categorie:
- **S**poofing: impersonare un'entita legittima
- **T**ampering: modificare dati o codice in modo non autorizzato
- **R**epudiation: negare di aver eseguito un'azione
- **I**nformation Disclosure: esporre informazioni riservate
- **D**enial of Service: rendere un servizio indisponibile
- **E**levation of Privilege: ottenere permessi non autorizzati

**DREAD** valuta la gravita di ogni minaccia:
- **D**amage potential: quanto danno puo causare
- **R**eproducibility: quanto e facile riprodurre l'attacco
- **E**xploitability: quanto impegno richiede lo sfruttamento
- **A**ffected users: quanti utenti sono colpiti
- **D**iscoverability: quanto e facile scoprire la vulnerabilita

### Attack Surface Management

La gestione della superficie di attacco prevede l'inventario continuo di tutti gli asset esposti,
l'identificazione delle vulnerabilita e la riduzione sistematica dei punti di ingresso.

```bash
# Discovery della superficie di attacco con nmap
nmap -sS -sV -O -p- --script=vuln -oA attack_surface_scan target.example.com

# Enumerazione DNS per identificare tutti i sottodomini
subfinder -d example.com -o subdomains.txt

# Scansione dei sottodomini scoperti
cat subdomains.txt | httpx -title -status-code -tech-detect -o live_hosts.txt
```

---

## 2. Network Security e Segmentation

### Pericoli di una Flat Network

Una rete piatta (flat network) consente a qualsiasi dispositivo di comunicare direttamente con qualsiasi altro.
In caso di compromissione di un singolo host, l'attaccante puo muoversi lateralmente senza ostacoli,
raggiungendo database, sistemi di gestione e infrastruttura critica.

### Strategie di Segmentazione

La segmentazione della rete divide l'infrastruttura in zone isolate con controlli di accesso
tra una zona e l'altra. Le strategie principali includono:

- **Segmentazione fisica**: reti separate con hardware dedicato
- **VLAN**: segmentazione logica a livello Layer 2
- **Segmentazione basata su firewall**: regole tra subnet
- **Micro-segmentation**: policy a livello di singolo workload (SDN-based)

### Configurazione VLAN

```bash
# Configurazione VLAN su switch Cisco (esempio)
enable
configure terminal

# Creazione delle VLAN
vlan 10
  name DMZ
vlan 20
  name APPLICATION
vlan 30
  name DATABASE
vlan 40
  name MANAGEMENT

# Assegnazione porte alle VLAN
interface GigabitEthernet0/1
  switchport mode access
  switchport access vlan 10
  spanning-tree portfast

interface GigabitEthernet0/5
  switchport mode access
  switchport access vlan 30
  no cdp enable

# Trunk port verso il firewall
interface GigabitEthernet0/24
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30,40
  switchport trunk native vlan 999
```

### Security Zones

```
Internet
    │
    ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   DMZ    │───▶│   APP    │───▶│   DATA   │    │  MGMT    │
│ VLAN 10  │    │ VLAN 20  │    │ VLAN 30  │    │ VLAN 40  │
│          │    │          │    │          │    │          │
│ WAF      │    │ App      │    │ Database │    │ Bastion  │
│ LB       │    │ Servers  │    │ Cache    │    │ Ansible  │
│ Reverse  │    │ API GW   │    │ Storage  │    │ Logs     │
│ Proxy    │    │          │    │          │    │ Monitor  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

- **DMZ**: servizi esposti a Internet, reverse proxy, load balancer, WAF
- **Application Zone**: server applicativi, API, microservizi
- **Data Zone**: database, cache, storage, zone a massima protezione
- **Management Zone**: bastion host, sistemi di monitoraggio, automazione, accesso amministrativo

### Firewall Rules Design — Deny by Default

```bash
# iptables — policy deny by default
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Consentire traffico loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Consentire connessioni stabilite
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# DMZ -> Internet: solo HTTP/HTTPS in uscita
iptables -A FORWARD -s 10.0.10.0/24 -o eth0 -p tcp --dport 443 -j ACCEPT
iptables -A FORWARD -s 10.0.10.0/24 -o eth0 -p tcp --dport 80 -j ACCEPT

# Internet -> DMZ: solo HTTPS in entrata verso il load balancer
iptables -A FORWARD -i eth0 -d 10.0.10.10 -p tcp --dport 443 -j ACCEPT

# DMZ -> Application Zone: solo porte applicative specifiche
iptables -A FORWARD -s 10.0.10.0/24 -d 10.0.20.0/24 -p tcp --dport 8080 -j ACCEPT
iptables -A FORWARD -s 10.0.10.0/24 -d 10.0.20.0/24 -p tcp --dport 8443 -j ACCEPT

# Application -> Data Zone: solo porte database
iptables -A FORWARD -s 10.0.20.0/24 -d 10.0.30.0/24 -p tcp --dport 5432 -j ACCEPT
iptables -A FORWARD -s 10.0.20.0/24 -d 10.0.30.0/24 -p tcp --dport 6379 -j ACCEPT

# Management Zone: accesso SSH solo da bastion
iptables -A FORWARD -s 10.0.40.5 -p tcp --dport 22 -j ACCEPT

# Logging del traffico bloccato
iptables -A FORWARD -j LOG --log-prefix "FW-BLOCKED: " --log-level 4
iptables -A FORWARD -j DROP
```

### East-West Traffic Inspection

Il traffico east-west (tra servizi interni) rappresenta la maggior parte del traffico in un datacenter moderno.
L'ispezione di questo traffico e fondamentale per rilevare il movimento laterale degli attaccanti.

```yaml
# Kubernetes NetworkPolicy per ispezione east-west
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrict-internal-traffic
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

### IDS/IPS — Suricata

```yaml
# /etc/suricata/suricata.yaml — configurazione base
vars:
  address-groups:
    HOME_NET: "[10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16]"
    EXTERNAL_NET: "!$HOME_NET"
    DMZ_NET: "10.0.10.0/24"
    DB_SERVERS: "10.0.30.0/24"

default-rule-path: /etc/suricata/rules/

rule-files:
  - suricata.rules
  - custom.rules

af-packet:
  - interface: eth0
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes

outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: /var/log/suricata/eve.json
      types:
        - alert
        - http
        - dns
        - tls
        - flow
```

```bash
# Regole Suricata custom per rilevare attivita sospette
# /etc/suricata/rules/custom.rules

# Rilevamento SQL injection
alert http $EXTERNAL_NET any -> $HOME_NET any (
  msg:"SQL Injection Attempt Detected";
  flow:to_server,established;
  content:"UNION"; nocase;
  content:"SELECT"; nocase;
  sid:1000001; rev:1;
  classtype:web-application-attack;
  severity:1;
)

# Rilevamento scansione porte
alert tcp $EXTERNAL_NET any -> $HOME_NET any (
  msg:"Possible Port Scan Detected";
  flags:S;
  threshold: type both, track by_src, count 20, seconds 60;
  sid:1000002; rev:1;
  classtype:attempted-recon;
)

# Rilevamento accesso non autorizzato alla zona database
alert tcp !$DMZ_NET any -> $DB_SERVERS 5432 (
  msg:"Unauthorized Direct DB Access Attempt";
  flow:to_server;
  sid:1000003; rev:1;
  classtype:policy-violation;
  severity:2;
)
```

```bash
# Avvio e gestione Suricata
sudo suricata -c /etc/suricata/suricata.yaml -i eth0 --init-errors-fatal

# Verifica regole
sudo suricata -T -c /etc/suricata/suricata.yaml

# Analisi degli alert
sudo tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'
```

### Network Access Control (NAC)

Il NAC verifica che i dispositivi soddisfino i requisiti di sicurezza prima di concedere l'accesso alla rete.
I controlli includono: stato dell'antivirus, aggiornamenti del sistema operativo, conformita alle policy,
certificati validi e stato di salute del dispositivo.

---

## 3. Web Application Firewall (WAF)

### Cos'e un WAF e Come Funziona

Un **Web Application Firewall** opera al Layer 7 del modello OSI, analizzando il traffico HTTP/HTTPS
per identificare e bloccare attacchi diretti alle applicazioni web. A differenza di un firewall tradizionale
che opera a livello di rete (Layer 3/4), il WAF comprende il protocollo applicativo e puo ispezionare
il contenuto delle richieste, inclusi header, body, parametri e cookie.

### Positive vs Negative Security Model

- **Negative Security Model**: blocca le richieste che corrispondono a pattern di attacco noti (blacklist).
  Efficace contro attacchi conosciuti ma vulnerabile a tecniche di evasione e attacchi zero-day.
- **Positive Security Model**: consente solo le richieste che corrispondono a un profilo di traffico
  legittimo predefinito (whitelist). Piu sicuro ma richiede una configurazione dettagliata per ogni applicazione.

### ModSecurity con Nginx

```bash
# Installazione ModSecurity per Nginx su Debian/Ubuntu
sudo apt install libmodsecurity3 libmodsecurity-dev
sudo apt install libnginx-mod-http-modsecurity

# Abilitazione in nginx.conf
```

```nginx
# /etc/nginx/nginx.conf — configurazione WAF ModSecurity
http {
    modsecurity on;
    modsecurity_rules_file /etc/nginx/modsecurity/main.conf;

    server {
        listen 443 ssl http2;
        server_name app.example.com;

        ssl_certificate     /etc/ssl/certs/app.crt;
        ssl_certificate_key /etc/ssl/private/app.key;

        location / {
            proxy_pass http://backend_servers;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

```bash
# /etc/nginx/modsecurity/main.conf
Include /etc/nginx/modsecurity/modsecurity.conf
Include /etc/nginx/modsecurity/crs/crs-setup.conf
Include /etc/nginx/modsecurity/crs/rules/*.conf
Include /etc/nginx/modsecurity/custom-rules.conf
```

### OWASP Core Rule Set (CRS)

```bash
# Download e installazione OWASP CRS
cd /etc/nginx/modsecurity/
git clone https://github.com/coreruleset/coreruleset.git crs
cp crs/crs-setup.conf.example crs/crs-setup.conf
```

```bash
# /etc/nginx/modsecurity/crs/crs-setup.conf — configurazione CRS
SecAction "id:900000,phase:1,pass,t:none,\
  setvar:tx.blocking_paranoia_level=2,\
  setvar:tx.detection_paranoia_level=3"

# Paranoia Level:
# 1 = Base (pochi falsi positivi, copertura standard)
# 2 = Elevato (bilancio tra sicurezza e falsi positivi)
# 3 = Alto (molti controlli, possibili falsi positivi)
# 4 = Massimo (molto aggressivo, richiede tuning)

SecAction "id:900110,phase:1,pass,t:none,\
  setvar:tx.inbound_anomaly_score_threshold=5,\
  setvar:tx.outbound_anomaly_score_threshold=4"
```

### Regole Custom WAF

```bash
# /etc/nginx/modsecurity/custom-rules.conf

# Blocco accesso a file sensibili
SecRule REQUEST_URI "@rx \.(env|git|svn|htaccess|htpasswd|bak|old|temp|swp)$" \
  "id:10001,phase:1,deny,status:403,\
  msg:'Access to sensitive file blocked',\
  severity:CRITICAL,\
  tag:'custom/sensitive-files'"

# Protezione contro path traversal
SecRule REQUEST_URI "@contains ../" \
  "id:10002,phase:1,deny,status:403,\
  msg:'Path traversal attempt blocked',\
  severity:CRITICAL,\
  tag:'custom/path-traversal'"

# Rate limiting per endpoint di login (max 10 richieste/minuto)
SecRule REQUEST_URI "@streq /api/auth/login" \
  "id:10003,phase:1,pass,nolog,\
  setvar:ip.login_counter=+1,\
  expirevar:ip.login_counter=60"

SecRule IP:LOGIN_COUNTER "@ge 10" \
  "id:10004,phase:1,deny,status:429,\
  msg:'Login rate limit exceeded',\
  severity:WARNING,\
  tag:'custom/rate-limit'"

# Blocco user-agent sospetti (scanner automatici)
SecRule REQUEST_HEADERS:User-Agent "@rx (nikto|sqlmap|nmap|masscan|dirbuster|gobuster)" \
  "id:10005,phase:1,deny,status:403,\
  msg:'Automated scanner blocked',\
  severity:WARNING,\
  tag:'custom/bot-detection'"

# Protezione API: validazione Content-Type su POST/PUT
SecRule REQUEST_METHOD "@rx ^(POST|PUT|PATCH)$" \
  "id:10006,phase:1,chain,deny,status:415,\
  msg:'Missing or invalid Content-Type'"
  SecRule REQUEST_HEADERS:Content-Type "!@rx ^application/(json|xml|x-www-form-urlencoded)" ""
```

### Gestione dei False Positives

```bash
# Esclusione di regole specifiche per un endpoint
SecRule REQUEST_URI "@beginsWith /api/content/upload" \
  "id:10100,phase:1,pass,nolog,\
  ctl:ruleRemoveById=941100,\
  ctl:ruleRemoveById=941160,\
  ctl:ruleRemoveById=942100"

# Esclusione per parametro specifico
SecRule REQUEST_URI "@beginsWith /api/articles" \
  "id:10101,phase:1,pass,nolog,\
  ctl:ruleRemoveTargetById=942100;ARGS:body,\
  ctl:ruleRemoveTargetById=941100;ARGS:body"

# Monitoraggio: modalita DetectionOnly per tuning iniziale
SecRuleEngine DetectionOnly
# Passare a On dopo il tuning:
# SecRuleEngine On
```

### Cloud WAF — AWS WAF

```bash
# Creazione Web ACL con AWS CLI
aws wafv2 create-web-acl \
  --name "production-waf" \
  --scope REGIONAL \
  --default-action '{"Allow":{}}' \
  --rules '[
    {
      "Name": "AWSManagedRulesCommonRuleSet",
      "Priority": 1,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesCommonRuleSet"
        }
      },
      "OverrideAction": {"None": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "CommonRuleSet"
      }
    },
    {
      "Name": "AWSManagedRulesSQLiRuleSet",
      "Priority": 2,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesSQLiRuleSet"
        }
      },
      "OverrideAction": {"None": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "SQLiRuleSet"
      }
    },
    {
      "Name": "RateLimitRule",
      "Priority": 3,
      "Statement": {
        "RateBasedStatement": {
          "Limit": 2000,
          "AggregateKeyType": "IP"
        }
      },
      "Action": {"Block": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimit"
      }
    }
  ]' \
  --visibility-config '{
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "production-waf"
  }'
```

---

## 4. DDoS Mitigation

### Tipi di Attacco DDoS

**Volumetric Attacks** (Layer 3/4):
- UDP flood, ICMP flood, DNS amplification, NTP amplification, memcached amplification
- Obiettivo: saturare la banda disponibile
- Volumi: da 1 Gbps a oltre 1 Tbps

**Protocol Attacks** (Layer 3/4):
- SYN flood, ACK flood, fragmented packet attacks
- Obiettivo: esaurire le risorse degli apparati di rete (firewall, load balancer)
- Sfruttano debolezze nei protocolli TCP/IP

**Application Layer Attacks** (Layer 7):
- HTTP flood, Slowloris, RUDY (R-U-Dead-Yet), attacchi mirati a endpoint costosi
- Obiettivo: esaurire le risorse applicative (CPU, memoria, connessioni)
- Piu difficili da rilevare perche simulano traffico legittimo

### Difesa Multi-Layer

```
┌───────────────────────────────────────────────────┐
│ Layer 1: Upstream Provider / Anycast / Scrubbing  │
│   Mitigazione volumetrica (1+ Tbps capacity)      │
├───────────────────────────────────────────────────┤
│ Layer 2: Edge / CDN / Cloud DDoS Protection       │
│   Rate limiting, geo-blocking, bot detection      │
├───────────────────────────────────────────────────┤
│ Layer 3: Firewall / IPS                           │
│   SYN cookies, connection limits, protocol checks │
├───────────────────────────────────────────────────┤
│ Layer 4: Load Balancer                            │
│   Connection draining, health checks, scaling     │
├───────────────────────────────────────────────────┤
│ Layer 5: Application                              │
│   WAF, rate limiting per-user, CAPTCHA challenge  │
└───────────────────────────────────────────────────┘
```

### Protezione a Livello di Sistema Operativo

```bash
# Abilitazione SYN cookies (protezione SYN flood)
sysctl -w net.ipv4.tcp_syncookies=1
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
sysctl -w net.ipv4.tcp_synack_retries=2

# Limitazione connessioni simultanee per IP
iptables -A INPUT -p tcp --syn --dport 443 \
  -m connlimit --connlimit-above 50 --connlimit-mask 32 \
  -j DROP

# Rate limiting con iptables (max 25 nuove connessioni/secondo per IP)
iptables -A INPUT -p tcp --dport 443 -m state --state NEW \
  -m recent --set --name DDOS --rsource
iptables -A INPUT -p tcp --dport 443 -m state --state NEW \
  -m recent --update --seconds 1 --hitcount 25 --name DDOS --rsource \
  -j DROP

# Protezione contro ICMP flood
iptables -A INPUT -p icmp --icmp-type echo-request \
  -m limit --limit 1/s --limit-burst 4 -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

# Protezione contro UDP flood
iptables -A INPUT -p udp -m limit --limit 50/s --limit-burst 100 -j ACCEPT
iptables -A INPUT -p udp -j DROP

# Persistenza delle regole sysctl
cat >> /etc/sysctl.d/99-ddos-protection.conf << 'EOF'
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_synack_retries = 2
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
EOF

sysctl -p /etc/sysctl.d/99-ddos-protection.conf
```

### Protezione Nginx contro Application-Layer DDoS

```nginx
# /etc/nginx/conf.d/ddos-protection.conf

# Limitazione rate per zona
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=3r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;

# Limitazione connessioni simultanee
limit_conn_zone $binary_remote_addr zone=conn_per_ip:10m;

server {
    listen 443 ssl http2;

    # Limite connessioni simultanee per IP
    limit_conn conn_per_ip 20;

    # Timeout aggressivi contro Slowloris
    client_body_timeout 10s;
    client_header_timeout 10s;
    keepalive_timeout 15s;
    send_timeout 10s;

    # Limite dimensione body
    client_max_body_size 10m;

    location / {
        limit_req zone=general burst=20 nodelay;
        proxy_pass http://backend;
    }

    location /api/auth/login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://backend;
    }

    location /api/ {
        limit_req zone=api burst=50 nodelay;
        proxy_pass http://backend;
    }
}
```

### Cloud DDoS Protection

```bash
# AWS Shield Advanced — abilitazione
aws shield create-subscription

# Associazione risorsa protetta
aws shield create-protection \
  --name "production-alb" \
  --resource-arn "arn:aws:elasticloadbalancing:eu-west-1:123456789:loadbalancer/app/prod-alb/abc123"

# Azure DDoS Protection
az network ddos-protection create \
  --resource-group production-rg \
  --name production-ddos-plan

az network vnet update \
  --resource-group production-rg \
  --name production-vnet \
  --ddos-protection-plan production-ddos-plan \
  --ddos-protection true
```

### BGP Blackholing e Anycast

**BGP Blackholing** (Remote Triggered Black Hole):
consente di scartare il traffico verso un IP sotto attacco a livello del provider upstream,
impedendo al traffico malevolo di raggiungere l'infrastruttura. Il trade-off e che anche
il traffico legittimo viene scartato.

**Anycast**: distribuisce lo stesso indirizzo IP su piu datacenter geograficamente dispersi.
Il traffico viene instradato al datacenter piu vicino, distribuendo il carico di un attacco
DDoS su molteplici punti di presenza e aumentando la capacita complessiva di assorbimento.

---

## 5. Vulnerability Management

### Vulnerability Scanning con Nessus e OpenVAS

```bash
# Installazione OpenVAS (GVM - Greenbone Vulnerability Management)
sudo apt install gvm
sudo gvm-setup
sudo gvm-check-setup

# Avvio scansione da CLI con gvm-cli
gvm-cli --gmp-username admin --gmp-password admin socket \
  --xml '<create_task>
    <name>Infrastructure Scan</name>
    <config id="daba56c8-73ec-11df-a475-002264764cea"/>
    <target id="TARGET_ID"/>
  </create_task>'

# Scansione di rete con nmap per discovery iniziale
nmap -sV -sC -O --script=vuln -oX nmap_vuln_scan.xml 10.0.0.0/24
```

### Container Image Scanning con Trivy

```bash
# Scansione di un'immagine container
trivy image --severity HIGH,CRITICAL nginx:1.25

# Scansione con output JSON per integrazione CI/CD
trivy image --format json --output results.json myapp:latest

# Scansione con exit code per fallimento pipeline
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Scansione del filesystem (IaC e codice sorgente)
trivy fs --security-checks vuln,secret,config /path/to/project

# Scansione configurazioni Kubernetes
trivy config /path/to/kubernetes/manifests/

# Scansione di un cluster Kubernetes in esecuzione
trivy k8s --report summary cluster

# Configurazione per ignorare vulnerabilita accettate
cat > .trivyignore << 'EOF'
# Vulnerabilita accettata con giustificazione
CVE-2023-12345
# Non applicabile al nostro caso d'uso
CVE-2023-67890
EOF

trivy image --ignorefile .trivyignore myapp:latest
```

### Dependency Scanning nella Pipeline CI/CD

```yaml
# GitHub Actions — pipeline di vulnerability scanning completa
name: Security Scanning
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Scansione settimanale il lunedi

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run OWASP Dependency Check
        uses: dependency-check/Dependency-Check_Action@main
        with:
          project: 'my-application'
          path: '.'
          format: 'JSON'
          args: >
            --failOnCVSS 7
            --enableRetired

      - name: Run Snyk Security Scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

  container-scan:
    runs-on: ubuntu-latest
    needs: dependency-scan
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker Image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Trivy Container Scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'HIGH,CRITICAL'
          exit-code: '1'

      - name: Grype Container Scan
        uses: anchore/scan-action@v3
        with:
          image: 'myapp:${{ github.sha }}'
          fail-build: true
          severity-cutoff: high

  infrastructure-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Checkov IaC Scan
        uses: bridgecrewio/checkov-action@master
        with:
          directory: terraform/
          framework: terraform
          output_format: sarif

      - name: AWS Security Scan with Prowler
        run: |
          pip install prowler
          prowler aws --severity critical high \
            --output-formats json-ocsf \
            --output-directory prowler-results/
```

### CVSS Scoring

Il **Common Vulnerability Scoring System** (CVSS) assegna un punteggio da 0.0 a 10.0 alle vulnerabilita:

| Punteggio | Severita  | SLA Remediation |
|-----------|-----------|-----------------|
| 9.0-10.0  | Critical  | 24-48 ore       |
| 7.0-8.9   | High      | 7 giorni        |
| 4.0-6.9   | Medium    | 30 giorni       |
| 0.1-3.9   | Low       | 90 giorni       |
| 0.0       | None      | Best effort     |

### Patch Management Process

```bash
# Script di patch management automatizzato per Linux
#!/bin/bash
set -euo pipefail

LOG_FILE="/var/log/patch-management/$(date +%Y%m%d).log"
BACKUP_DIR="/var/backups/pre-patch/$(date +%Y%m%d)"

mkdir -p "$(dirname "$LOG_FILE")" "$BACKUP_DIR"

echo "[$(date)] Inizio processo di patching" | tee -a "$LOG_FILE"

# Backup della lista pacchetti installati
dpkg --get-selections > "$BACKUP_DIR/packages.list"

# Aggiornamento indice pacchetti
apt update 2>&1 | tee -a "$LOG_FILE"

# Elenco aggiornamenti di sicurezza disponibili
apt list --upgradable 2>/dev/null | grep -i security | tee -a "$LOG_FILE"

# Applicazione solo aggiornamenti di sicurezza
apt upgrade -y -o Dpkg::Options::="--force-confold" 2>&1 | tee -a "$LOG_FILE"

# Verifica servizi da riavviare
checkrestart 2>/dev/null | tee -a "$LOG_FILE" || true
needrestart -r l 2>/dev/null | tee -a "$LOG_FILE" || true

echo "[$(date)] Patching completato" | tee -a "$LOG_FILE"
```

---

## 6. Zero Trust Architecture

### Principi Fondamentali

Il modello **Zero Trust** si basa su tre principi cardine:

1. **Verify Explicitly**: autenticare e autorizzare ogni richiesta basandosi su tutti i data point disponibili,
   includendo identita dell'utente, posizione, stato del dispositivo, servizio richiesto,
   classificazione dei dati e anomalie comportamentali.

2. **Least Privilege Access**: limitare l'accesso con politiche just-in-time (JIT) e just-enough-access (JEA),
   protezione adattiva basata sul rischio e protezione dei dati.

3. **Assume Breach**: minimizzare il blast radius e segmentare l'accesso. Verificare la crittografia
   end-to-end e usare analytics per detection, threat intelligence e miglioramento delle difese.

### Componenti dell'Architettura Zero Trust

```
┌─────────────────────────────────────────────────────────┐
│                    Policy Engine                         │
│    (Decisioni di accesso basate su contesto completo)    │
├───────────┬──────────┬──────────┬──────────┬────────────┤
│ Identity  │ Device   │ Network  │ App/     │ Data       │
│ Pillar    │ Pillar   │ Pillar   │ Workload │ Pillar     │
│           │          │          │ Pillar   │            │
│ - MFA     │ - MDM    │ - Micro- │ - Secure │ - Classif. │
│ - SSO     │ - Health │   segm.  │   by     │ - Encrypt. │
│ - RBAC    │ - Compli │ - Encryp │   design │ - DLP      │
│ - Risk    │ - Patch  │ - SDP    │ - API    │ - Access   │
│   based   │   level  │          │   sec.   │   control  │
└───────────┴──────────┴──────────┴──────────┴────────────┘
```

### Implementazione Pratica — BeyondCorp Model

Il modello **BeyondCorp** (originato da Google) elimina la distinzione tra rete interna e esterna.
L'accesso alle risorse e determinato esclusivamente dall'identita dell'utente, dallo stato del dispositivo
e dal contesto della richiesta, non dalla posizione nella rete.

```yaml
# Configurazione Identity-Aware Proxy con OAuth2 Proxy
# oauth2-proxy.cfg
provider = "oidc"
oidc_issuer_url = "https://idp.example.com/realms/corporate"
client_id = "zero-trust-proxy"
client_secret_file = "/run/secrets/oauth2-proxy-secret"

# Ogni richiesta deve essere autenticata
skip_auth_regex = []

# Verifica email domain
email_domains = ["example.com"]

# Header forwarding per il backend
set_xauthrequest = true
set_authorization_header = true
pass_access_token = true

# Cookie sicuro
cookie_secure = true
cookie_httponly = true
cookie_samesite = "lax"
cookie_expire = "1h"
cookie_refresh = "15m"

# Upstream
upstreams = ["http://internal-app:8080"]

# Logging per audit
request_logging = true
auth_logging = true
standard_logging = true
```

```yaml
# Kubernetes: deployment Identity-Aware Proxy
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oauth2-proxy
  namespace: zero-trust
spec:
  replicas: 2
  selector:
    matchLabels:
      app: oauth2-proxy
  template:
    metadata:
      labels:
        app: oauth2-proxy
    spec:
      containers:
      - name: oauth2-proxy
        image: quay.io/oauth2-proxy/oauth2-proxy:v7.6.0
        args:
        - --config=/etc/oauth2-proxy/oauth2-proxy.cfg
        ports:
        - containerPort: 4180
        volumeMounts:
        - name: config
          mountPath: /etc/oauth2-proxy/
          readOnly: true
        - name: secret
          mountPath: /run/secrets/
          readOnly: true
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /ping
            port: 4180
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: oauth2-proxy-config
      - name: secret
        secret:
          secretName: oauth2-proxy-secret
```

### ZTNA vs VPN Tradizionale

| Caratteristica         | VPN Tradizionale           | ZTNA                           |
|------------------------|----------------------------|--------------------------------|
| Modello di accesso     | Accesso alla rete          | Accesso alla singola app       |
| Trust                  | Implicito dopo connessione | Nessuno, verifica continua     |
| Visibilita rete        | Intera rete interna        | Solo risorse autorizzate       |
| Superficie di attacco  | Ampia                      | Minima                         |
| Performance            | Bottleneck centralizzato   | Accesso diretto ottimizzato    |
| Movimento laterale     | Possibile                  | Impedito by design             |
| Scalabilita            | Limitata dall'hardware     | Cloud-native, elastica         |

### Software Defined Perimeter (SDP)

```bash
# Principio SDP: i servizi sono invisibili a chi non e autorizzato
# Prima dell'autenticazione, nessuna porta e visibile

# Esempio con iptables: blocco totale, apertura solo dopo SPA (Single Packet Authorization)
iptables -A INPUT -p tcp --dport 22 -j DROP  # SSH non raggiungibile

# fwknop — implementazione SPA open-source
# Client invia un pacchetto crittografato per aprire temporaneamente la porta
fwknop -A tcp/22 -D server.example.com --key-gen

# Server: la porta si apre solo per l'IP del client, solo per 30 secondi
# /etc/fwknop/access.conf
SOURCE              ANY
OPEN_PORTS          tcp/22
FW_ACCESS_TIMEOUT   30
REQUIRE_SOURCE_ADDRESS  Y
KEY_BASE64          <chiave_generata>
HMAC_KEY_BASE64     <hmac_key_generata>
```

---

## 7. Runtime Security

### Container Runtime Security con Falco

**Falco** e un tool open-source per la runtime security dei container che monitora le system call
del kernel per rilevare comportamenti anomali in tempo reale.

```yaml
# /etc/falco/falco.yaml — configurazione base
rules_file:
  - /etc/falco/falco_rules.yaml
  - /etc/falco/falco_rules.local.yaml
  - /etc/falco/custom_rules.yaml

json_output: true
json_include_output_property: true
log_stderr: true
log_syslog: true
log_level: info

outputs:
  rate: 1
  max_burst: 1000

stdout_output:
  enabled: true

syslog_output:
  enabled: true

http_output:
  enabled: true
  url: "http://falco-sidekick:2801/"

grpc:
  enabled: true
  bind_address: "unix:///run/falco/falco.sock"
  threadiness: 4

grpc_output:
  enabled: true
```

```yaml
# /etc/falco/custom_rules.yaml — regole personalizzate

# Rilevamento shell interattiva in un container
- rule: Interactive Shell in Container
  desc: Rilevata apertura di shell interattiva in un container di produzione
  condition: >
    spawned_process and
    container and
    container.image.repository != "debug-tools" and
    proc.name in (bash, sh, zsh, dash, ksh) and
    proc.tty != 0
  output: >
    Shell interattiva rilevata in container
    (user=%user.name container=%container.name
    image=%container.image.repository:%container.image.tag
    shell=%proc.name parent=%proc.pname cmdline=%proc.cmdline
    terminal=%proc.tty)
  priority: WARNING
  tags: [container, shell, mitre_execution]

# Rilevamento lettura di file sensibili
- rule: Read Sensitive File in Container
  desc: Tentativo di lettura di file sensibili in un container
  condition: >
    open_read and
    container and
    fd.name in (/etc/shadow, /etc/sudoers, /root/.ssh/authorized_keys,
                /root/.bash_history, /proc/1/environ) and
    not proc.name in (sshd, sudo)
  output: >
    Lettura file sensibile in container
    (user=%user.name file=%fd.name container=%container.name
    image=%container.image.repository command=%proc.cmdline)
  priority: CRITICAL
  tags: [container, filesystem, mitre_credential_access]

# Rilevamento connessioni di rete inattese
- rule: Unexpected Outbound Connection
  desc: Connessione in uscita verso IP non autorizzato da container di produzione
  condition: >
    outbound and
    container and
    container.image.repository in (api-server, web-frontend, worker) and
    not fd.sip in (10.0.0.0/8, 172.16.0.0/12) and
    not fd.sport in (53, 443, 8443)
  output: >
    Connessione in uscita inattesa da container
    (container=%container.name image=%container.image.repository
    connection=%fd.name destination=%fd.sip:%fd.sport
    process=%proc.name user=%user.name)
  priority: WARNING
  tags: [container, network, mitre_command_and_control]

# Rilevamento modifica file di sistema
- rule: Write to System Directories in Container
  desc: Scrittura in directory di sistema in un container
  condition: >
    open_write and
    container and
    fd.name startswith /etc/ and
    not proc.name in (adduser, useradd, groupadd)
  output: >
    Scrittura in directory di sistema
    (user=%user.name file=%fd.name container=%container.name
    image=%container.image.repository command=%proc.cmdline)
  priority: ERROR
  tags: [container, filesystem, mitre_persistence]

# Rilevamento esecuzione di crypto miner
- rule: Crypto Mining Activity
  desc: Rilevata possibile attivita di crypto mining
  condition: >
    spawned_process and
    container and
    (proc.name in (xmrig, minerd, minergate, cpuminer) or
     proc.cmdline contains "stratum+tcp" or
     proc.cmdline contains "pool.minexmr" or
     proc.cmdline contains "cryptonight")
  output: >
    Possibile crypto mining rilevato
    (container=%container.name process=%proc.name
    cmdline=%proc.cmdline user=%user.name
    image=%container.image.repository)
  priority: CRITICAL
  tags: [container, crypto, mitre_resource_hijacking]
```

### Pod Security Standards in Kubernetes

```yaml
# Pod Security Standards — Restricted (massimo livello di sicurezza)
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
# Esempio di Pod conforme al profilo Restricted
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  namespace: production
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myregistry.io/myapp:v2.1.0@sha256:abc123...
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
      runAsNonRoot: true
      runAsUser: 10001
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /app/cache
  volumes:
  - name: tmp
    emptyDir:
      sizeLimit: 100Mi
  - name: cache
    emptyDir:
      sizeLimit: 200Mi
  automountServiceAccountToken: false
```

### Seccomp Profiles

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_AARCH64"
  ],
  "syscalls": [
    {
      "names": [
        "accept4", "access", "arch_prctl", "bind", "brk",
        "clone", "close", "connect", "epoll_create1",
        "epoll_ctl", "epoll_wait", "execve", "exit",
        "exit_group", "fcntl", "fstat", "futex",
        "getdents64", "getpeername", "getpid", "getsockname",
        "getsockopt", "ioctl", "listen", "lseek",
        "madvise", "mmap", "mprotect", "munmap",
        "nanosleep", "newfstatat", "open", "openat",
        "pipe2", "poll", "pread64", "pwrite64",
        "read", "recvfrom", "recvmsg", "rt_sigaction",
        "rt_sigprocmask", "rt_sigreturn", "sched_getaffinity",
        "sched_yield", "sendmsg", "sendto", "set_robust_list",
        "set_tid_address", "setsockopt", "sigaltstack",
        "socket", "stat", "tgkill", "uname", "write",
        "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

### OPA Gatekeeper — Admission Controller

```yaml
# ConstraintTemplate: richiede immagini da registry autorizzati
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sallowedregistries
spec:
  crd:
    spec:
      names:
        kind: K8sAllowedRegistries
      validation:
        openAPIV3Schema:
          type: object
          properties:
            registries:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sallowedregistries

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not registry_allowed(container.image)
          msg := sprintf(
            "L'immagine '%v' non proviene da un registry autorizzato. Registry consentiti: %v",
            [container.image, input.parameters.registries]
          )
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.initContainers[_]
          not registry_allowed(container.image)
          msg := sprintf(
            "L'immagine init '%v' non proviene da un registry autorizzato.",
            [container.image]
          )
        }

        registry_allowed(image) {
          registry := input.parameters.registries[_]
          startswith(image, registry)
        }
---
# Constraint: applicazione della policy
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sAllowedRegistries
metadata:
  name: allowed-registries
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    - apiGroups: ["apps"]
      kinds: ["Deployment", "StatefulSet", "DaemonSet"]
    namespaces:
    - production
    - staging
  parameters:
    registries:
    - "myregistry.io/"
    - "gcr.io/my-project/"
    - "docker.io/library/"
```

### Kyverno — Policy Engine per Kubernetes

```yaml
# Policy Kyverno: impedire container con privilegi elevati
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-privileged-containers
  annotations:
    policies.kyverno.io/title: Disallow Privileged Containers
    policies.kyverno.io/severity: critical
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: deny-privileged
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "I container con privilegi elevati non sono consentiti."
      pattern:
        spec:
          containers:
          - securityContext:
              privileged: "false"
  - name: deny-privilege-escalation
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "L'escalation dei privilegi non e consentita."
      pattern:
        spec:
          containers:
          - securityContext:
              allowPrivilegeEscalation: "false"
  - name: require-non-root
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "I container devono essere eseguiti come utente non-root."
      pattern:
        spec:
          securityContext:
            runAsNonRoot: true
          containers:
          - securityContext:
              runAsNonRoot: true
```

---

## 8. SIEM e Security Operations

### Componenti di un SIEM

Un **Security Information and Event Management** (SIEM) integra quattro funzionalita fondamentali:

1. **Log Collection**: raccolta centralizzata dei log da tutte le fonti (server, applicazioni,
   dispositivi di rete, servizi cloud, endpoint)
2. **Normalization**: standardizzazione dei formati di log eterogenei in uno schema comune
3. **Correlation**: analisi incrociata degli eventi per identificare pattern di attacco
   che sarebbero invisibili esaminando le singole fonti
4. **Alerting**: generazione di allarmi basati su regole, soglie e anomalie comportamentali

### Wazuh — SIEM/XDR Open-Source

```yaml
# /var/ossec/etc/ossec.conf — configurazione Wazuh Manager
<ossec_config>
  <global>
    <jsonout_output>yes</jsonout_output>
    <alerts_log>yes</alerts_log>
    <logall>yes</logall>
    <logall_json>yes</logall_json>
    <email_notification>yes</email_notification>
    <smtp_server>smtp.example.com</smtp_server>
    <email_from>wazuh@example.com</email_from>
    <email_to>security-team@example.com</email_to>
    <email_maxperhour>12</email_maxperhour>
  </global>

  <!-- Vulnerability Detection -->
  <vulnerability-detector>
    <enabled>yes</enabled>
    <interval>12h</interval>
    <run_on_start>yes</run_on_start>
    <provider name="canonical">
      <enabled>yes</enabled>
      <os>focal</os>
      <os>jammy</os>
      <update_interval>1h</update_interval>
    </provider>
    <provider name="nvd">
      <enabled>yes</enabled>
      <update_interval>1h</update_interval>
    </provider>
  </vulnerability-detector>

  <!-- File Integrity Monitoring -->
  <syscheck>
    <disabled>no</disabled>
    <frequency>43200</frequency>
    <scan_on_start>yes</scan_on_start>
    <directories check_all="yes" realtime="yes">/etc,/usr/bin,/usr/sbin</directories>
    <directories check_all="yes" realtime="yes">/boot</directories>
    <ignore>/etc/mtab</ignore>
    <ignore>/etc/hosts.deny</ignore>
    <ignore>/etc/adjtime</ignore>
  </syscheck>

  <!-- Log Analysis -->
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/auth.log</location>
  </localfile>
  <localfile>
    <log_format>json</log_format>
    <location>/var/log/suricata/eve.json</location>
  </localfile>
  <localfile>
    <log_format>json</log_format>
    <location>/var/log/falco/events.json</location>
  </localfile>
</ossec_config>
```

### Regole di Correlazione Wazuh

```xml
<!-- /var/ossec/etc/rules/custom_rules.xml -->
<group name="custom,security">

  <!-- Rilevamento brute force SSH: 5 tentativi falliti in 2 minuti -->
  <rule id="100001" level="10" frequency="5" timeframe="120">
    <if_matched_sid>5710</if_matched_sid>
    <same_source_ip />
    <description>Brute force SSH: 5+ tentativi falliti da $(srcip)</description>
    <mitre>
      <id>T1110.001</id>
    </mitre>
    <group>authentication_failures,brute_force</group>
  </rule>

  <!-- Rilevamento privilege escalation: uso di sudo da utente non autorizzato -->
  <rule id="100002" level="12">
    <if_sid>5401</if_sid>
    <match>NOT in sudoers</match>
    <description>Tentativo di privilege escalation: utente non in sudoers</description>
    <mitre>
      <id>T1548.003</id>
    </mitre>
    <group>privilege_escalation</group>
  </rule>

  <!-- Rilevamento lateral movement: connessione SSH dopo brute force -->
  <rule id="100003" level="14" frequency="1" timeframe="300">
    <if_matched_sid>100001</if_matched_sid>
    <if_sid>5715</if_sid>
    <same_source_ip />
    <description>Lateral movement sospetto: login SSH riuscito dopo brute force da $(srcip)</description>
    <mitre>
      <id>T1021.004</id>
    </mitre>
    <group>lateral_movement</group>
  </rule>

  <!-- Rilevamento esfiltrazione dati: trasferimento file di grandi dimensioni -->
  <rule id="100004" level="10">
    <if_sid>80700</if_sid>
    <field name="http.response_content_length">>52428800</field>
    <description>Possibile esfiltrazione dati: risposta HTTP > 50MB</description>
    <mitre>
      <id>T1048</id>
    </mitre>
    <group>data_exfiltration</group>
  </rule>

  <!-- Rilevamento modifica file critico -->
  <rule id="100005" level="12">
    <if_sid>550</if_sid>
    <field name="syscheck.path">/etc/passwd|/etc/shadow|/etc/sudoers</field>
    <description>Modifica rilevata su file critico: $(syscheck.path)</description>
    <mitre>
      <id>T1098</id>
    </mitre>
    <group>file_integrity,critical_file</group>
  </rule>

</group>
```

### ELK Stack per Security Operations

```yaml
# Logstash pipeline per normalizzazione log di sicurezza
# /etc/logstash/conf.d/security-pipeline.conf

input {
  beats {
    port => 5044
    ssl => true
    ssl_certificate => "/etc/logstash/ssl/logstash.crt"
    ssl_key => "/etc/logstash/ssl/logstash.key"
  }
  kafka {
    bootstrap_servers => "kafka:9092"
    topics => ["security-events"]
    group_id => "logstash-security"
    codec => json
  }
}

filter {
  if [event][module] == "suricata" {
    json {
      source => "message"
      target => "suricata"
    }
    mutate {
      add_field => { "security.category" => "ids" }
    }
    if [suricata][alert] {
      mutate {
        add_field => { "security.severity" => "%{[suricata][alert][severity]}" }
        add_tag => ["security_alert"]
      }
    }
  }

  if [event][module] == "falco" {
    json {
      source => "message"
      target => "falco"
    }
    mutate {
      add_field => { "security.category" => "runtime" }
      add_field => { "security.severity" => "%{[falco][priority]}" }
      add_tag => ["security_alert"]
    }
  }

  # Arricchimento con GeoIP
  if [source][ip] {
    geoip {
      source => "[source][ip]"
      target => "[source][geo]"
    }
  }

  # Correlazione con MITRE ATT&CK
  if [rule][mitre] {
    translate {
      field => "[rule][mitre][id]"
      destination => "[mitre][technique_name]"
      dictionary_path => "/etc/logstash/mitre-techniques.yml"
    }
  }
}

output {
  if "security_alert" in [tags] {
    elasticsearch {
      hosts => ["https://elasticsearch:9200"]
      index => "security-alerts-%{+YYYY.MM}"
      ssl => true
      user => "logstash_writer"
      password => "${ELASTIC_PASSWORD}"
    }
    # Notifica immediata per alert critici
    if [security][severity] == "1" or [security][severity] == "CRITICAL" {
      http {
        url => "https://webhook.example.com/security-alerts"
        http_method => "post"
        format => "json"
      }
    }
  } else {
    elasticsearch {
      hosts => ["https://elasticsearch:9200"]
      index => "security-logs-%{+YYYY.MM}"
      ssl => true
      user => "logstash_writer"
      password => "${ELASTIC_PASSWORD}"
    }
  }
}
```

### MITRE ATT&CK Framework

Il **MITRE ATT&CK** e una knowledge base di tattiche e tecniche degli avversari basata su osservazioni
reali. Le tattiche rappresentano il "perche" di un'azione (l'obiettivo dell'attaccante), le tecniche
il "come" (il metodo utilizzato).

Tattiche principali:
- **Reconnaissance** (TA0043): raccolta informazioni sul target
- **Initial Access** (TA0001): ottenere un punto di ingresso
- **Execution** (TA0002): eseguire codice malevolo
- **Persistence** (TA0003): mantenere l'accesso nel tempo
- **Privilege Escalation** (TA0004): ottenere permessi elevati
- **Defense Evasion** (TA0005): evitare il rilevamento
- **Credential Access** (TA0006): rubare credenziali
- **Discovery** (TA0007): esplorare l'ambiente compromesso
- **Lateral Movement** (TA0008): muoversi attraverso la rete
- **Collection** (TA0009): raccogliere dati di interesse
- **Exfiltration** (TA0010): estrarre i dati
- **Impact** (TA0040): distruggere o manipolare dati/sistemi

---

## 9. Cloud Security Posture Management (CSPM)

### Cos'e il CSPM

Il **Cloud Security Posture Management** automatizza l'identificazione e la correzione
di configurazioni errate nelle risorse cloud. Le misconfigurazioni sono la causa principale
delle violazioni di sicurezza nel cloud (secondo il rapporto IBM Cost of a Data Breach).

### AWS Security Hub

```bash
# Abilitazione AWS Security Hub
aws securityhub enable-security-hub \
  --enable-default-standards

# Verifica standard abilitati
aws securityhub get-enabled-standards

# Visualizzazione finding critici
aws securityhub get-findings \
  --filters '{
    "SeverityLabel": [{"Value": "CRITICAL", "Comparison": "EQUALS"}],
    "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}],
    "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}]
  }' \
  --sort-criteria '{"Field": "SeverityNormalized", "SortOrder": "desc"}' \
  --max-items 20

# Prowler — scansione di sicurezza AWS completa
pip install prowler
prowler aws \
  --severity critical high \
  --compliance cis_2.0_aws \
  --output-formats json-ocsf html \
  --output-directory /tmp/prowler-results/

# Verifica specifica: S3 bucket pubblici
aws s3api list-buckets --query 'Buckets[].Name' --output text | \
while read bucket; do
  acl=$(aws s3api get-bucket-acl --bucket "$bucket" 2>/dev/null)
  policy=$(aws s3api get-bucket-policy-status --bucket "$bucket" 2>/dev/null)
  if echo "$policy" | grep -q '"IsPublic": true'; then
    echo "ALERT: Bucket pubblico rilevato: $bucket"
  fi
done

# Verifica: security group con porte aperte al mondo
aws ec2 describe-security-groups \
  --filters 'Name=ip-permission.cidr,Values=0.0.0.0/0' \
  --query 'SecurityGroups[*].{ID:GroupId,Name:GroupName,Rules:IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`)]}' \
  --output table
```

### Azure Defender for Cloud

```bash
# Abilitazione Azure Defender for Cloud
az security pricing create \
  --name VirtualMachines \
  --tier Standard

az security pricing create \
  --name SqlServers \
  --tier Standard

az security pricing create \
  --name Containers \
  --tier Standard

az security pricing create \
  --name KeyVaults \
  --tier Standard

# Visualizzazione raccomandazioni di sicurezza
az security assessment list \
  --query "[?status.code=='Unhealthy'].{Name:displayName, Severity:metadata.severity, Status:status.code}" \
  --output table

# Verifica compliance CIS
az security regulatory-compliance-standards list \
  --query "[].{Standard:name, State:state}" \
  --output table

# Azure Security Benchmark — risultati
az security regulatory-compliance-assessments list \
  --standard-name "Azure-CIS-1.3.0" \
  --query "[?state=='Failed'].{Control:id, Description:displayName}" \
  --output table
```

### GCP Security Command Center

```bash
# Abilitazione Security Command Center
gcloud services enable securitycenter.googleapis.com

# Elenco finding di sicurezza attivi
gcloud scc findings list organizations/ORG_ID \
  --source="-" \
  --filter="state=\"ACTIVE\" AND severity=\"CRITICAL\"" \
  --format="table(finding.category, finding.resourceName, finding.severity, finding.state)"

# Scansione con ScoutSuite (multi-cloud)
pip install scoutsuite
scout gcp --project-id my-project-id \
  --report-dir /tmp/scout-results/

# Verifica: firewall rules troppo permissive
gcloud compute firewall-rules list \
  --filter="sourceRanges:0.0.0.0/0 AND direction:INGRESS" \
  --format="table(name, network, allowed[].map().firewall_rule().list(), sourceRanges)"
```

### CIS Benchmarks

I **CIS Benchmarks** (Center for Internet Security) forniscono configurazioni di sicurezza
raccomandate per sistemi operativi, servizi cloud, database e applicazioni.

```bash
# Verifica CIS Benchmark su un server Linux con Lynis
sudo apt install lynis
sudo lynis audit system --cronjob --quiet

# Output del punteggio di hardening
sudo lynis audit system | grep "Hardening index"

# Docker Bench for Security (CIS Docker Benchmark)
docker run --rm --net host --pid host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /etc:/etc:ro \
  -v /usr/bin/containerd:/usr/bin/containerd:ro \
  -v /usr/bin/runc:/usr/bin/runc:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  docker/docker-bench-security

# Kubernetes CIS Benchmark con kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench
```

### Multi-Cloud Security Governance

```yaml
# Terraform: configurazione di sicurezza cross-cloud
# Modulo comune per policy di sicurezza

# AWS: encryption at rest obbligatoria
resource "aws_s3_bucket_server_side_encryption_configuration" "mandatory" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data_key.arn
    }
    bucket_key_enabled = true
  }
}

# AWS: blocco accesso pubblico S3
resource "aws_s3_bucket_public_access_block" "mandatory" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Azure: encryption e network rules per Storage Account
resource "azurerm_storage_account" "data" {
  name                     = "securedatastorage"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = "westeurope"
  account_tier             = "Standard"
  account_replication_type = "GRS"

  min_tls_version                 = "TLS1_2"
  enable_https_traffic_only       = true
  allow_nested_items_to_be_public = false

  network_rules {
    default_action = "Deny"
    ip_rules       = var.allowed_ips
    virtual_network_subnet_ids = [azurerm_subnet.app.id]
  }

  identity {
    type = "SystemAssigned"
  }
}

# GCP: VPC con Private Google Access
resource "google_compute_subnetwork" "private" {
  name                     = "private-subnet"
  ip_cidr_range            = "10.0.1.0/24"
  region                   = "europe-west1"
  network                  = google_compute_network.main.id
  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}
```

---

## 10. Supply Chain Security

### Attacchi alla Supply Chain del Software

Gli attacchi alla supply chain del software mirano a compromettere componenti di terze parti
(librerie, immagini container, tool di build) per infiltrare codice malevolo nelle applicazioni
che li utilizzano. Esempi noti: SolarWinds (2020), Codecov (2021), Log4Shell (2021),
xz-utils backdoor (2024).

### SBOM — Software Bill of Materials

```bash
# Generazione SBOM con Syft (formato SPDX)
syft packages myapp:latest -o spdx-json > sbom-spdx.json

# Generazione SBOM in formato CycloneDX
syft packages myapp:latest -o cyclonedx-json > sbom-cyclonedx.json

# Scansione SBOM per vulnerabilita con Grype
grype sbom:sbom-cyclonedx.json --output json > vulnerabilities.json

# Analisi delle dipendenze dalla SBOM
cat sbom-cyclonedx.json | jq '.components | length'
cat sbom-cyclonedx.json | jq '[.components[] | .purl] | sort'
```

### Container Image Signing con Cosign (Sigstore)

```bash
# Generazione chiave per la firma
cosign generate-key-pair

# Firma di un'immagine container
cosign sign --key cosign.key myregistry.io/myapp:v2.1.0

# Verifica della firma
cosign verify --key cosign.pub myregistry.io/myapp:v2.1.0

# Firma keyless con OIDC (Fulcio + Rekor)
cosign sign --identity-token=$(gcloud auth print-identity-token) \
  myregistry.io/myapp:v2.1.0

# Verifica keyless
cosign verify \
  --certificate-identity=ci@project.iam.gserviceaccount.com \
  --certificate-oidc-issuer=https://accounts.google.com \
  myregistry.io/myapp:v2.1.0

# Attestazione di vulnerabilita (allegare risultati scan)
trivy image --format cosign-vuln myregistry.io/myapp:v2.1.0 > vuln-att.json
cosign attest --key cosign.key --predicate vuln-att.json \
  --type vuln myregistry.io/myapp:v2.1.0

# Verifica attestazione
cosign verify-attestation --key cosign.pub \
  --type vuln myregistry.io/myapp:v2.1.0
```

### SLSA Framework (Supply-chain Levels for Software Artifacts)

Il framework **SLSA** (pronunciato "salsa") definisce quattro livelli di garanzia per la supply chain:

| Livello  | Requisiti                                                            |
|----------|----------------------------------------------------------------------|
| SLSA L1  | Documentazione del processo di build                                 |
| SLSA L2  | Build service ospitato, provenienza firmata                          |
| SLSA L3  | Build isolato con provenienza non-falsificabile, hardened build env  |
| SLSA L4  | Build ermetico, riproducibile, con revisione a due persone           |

```yaml
# GitHub Actions con SLSA provenance (Level 3)
name: Build with SLSA Provenance
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Build and Push Image
        id: build
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }}

      - name: Generate SLSA Provenance
        uses: slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@v2.0.0
        with:
          image: ghcr.io/${{ github.repository }}
          digest: ${{ steps.build.outputs.digest }}
```

### Dependency Pinning e Reproducible Builds

```dockerfile
# Dockerfile con immagine base pinned al digest SHA256
FROM node:20.12.0-alpine3.19@sha256:ef3f47741e161900ddd07addcaca7e76534a9205e4cd73b2ed091ba339004a75

WORKDIR /app

# Copia solo i file di lock per sfruttare la cache
COPY package.json package-lock.json ./

# Installazione deterministica (rispetta il lockfile esattamente)
RUN npm ci --ignore-scripts && npm cache clean --force

COPY . .

RUN npm run build

# Immagine finale minimale
FROM node:20.12.0-alpine3.19@sha256:ef3f47741e161900ddd07addcaca7e76534a9205e4cd73b2ed091ba339004a75
WORKDIR /app
COPY --from=0 /app/dist ./dist
COPY --from=0 /app/node_modules ./node_modules
COPY --from=0 /app/package.json ./

USER 10001
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

### Kubernetes Admission con Image Verification

```yaml
# Kyverno Policy: verifica firma immagini prima del deploy
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
  rules:
  - name: verify-cosign-signature
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "myregistry.io/*"
      attestors:
      - count: 1
        entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----
      attestations:
      - type: https://trivy.dev/scan/v1
        conditions:
        - all:
          - key: "{{ Results[].Vulnerabilities[?Severity == 'CRITICAL'] | length(@) }}"
            operator: Equals
            value: "0"
          message: "L'immagine contiene vulnerabilita critiche non risolte."
    - imageReferences:
      - "ghcr.io/*"
      attestors:
      - count: 1
        entries:
        - keyless:
            url: https://fulcio.sigstore.dev
            rekor:
              url: https://rekor.sigstore.dev
            subject: "https://github.com/myorg/*"
            issuer: "https://token.actions.githubusercontent.com"
```

---

## 11. Incident Response

### Incident Response Plan — Le Sei Fasi

Un piano di risposta agli incidenti strutturato segue il framework NIST SP 800-61r2,
organizzato in sei fasi interconnesse.

### Fase 1: Preparazione

La preparazione e la fase piu importante. Include la creazione del team di risposta (CSIRT/CERT),
la definizione di procedure, la predisposizione degli strumenti e l'addestramento del personale.

```bash
# Checklist di preparazione

# 1. Inventario degli asset critici
cat > /opt/incident-response/asset-inventory.yaml << 'EOF'
critical_assets:
  - name: production-database
    type: PostgreSQL
    owner: platform-team
    classification: confidential
    backup_frequency: hourly
    rto: 1h    # Recovery Time Objective
    rpo: 15m   # Recovery Point Objective

  - name: authentication-service
    type: microservice
    owner: security-team
    classification: critical
    dependencies:
      - production-database
      - redis-sessions
    rto: 30m
    rpo: 0

  - name: customer-data-store
    type: S3/GCS
    owner: data-team
    classification: pii-restricted
    encryption: AES-256-GCM
    rto: 4h
    rpo: 1h
EOF

# 2. Preparazione toolkit forense
cat > /opt/incident-response/toolkit-setup.sh << 'SCRIPT'
#!/bin/bash
set -euo pipefail

TOOLKIT_DIR="/opt/ir-toolkit"
mkdir -p "$TOOLKIT_DIR"

# Tool per raccolta evidence
apt install -y volatility3 sleuthkit dc3dd autopsy

# Tool per analisi rete
apt install -y tcpdump wireshark-common tshark ngrep

# Tool per analisi malware (sandbox)
apt install -y clamav yara

# Tool per analisi log
apt install -y jq csvkit ripgrep

echo "IR toolkit installato in $TOOLKIT_DIR"
SCRIPT
chmod +x /opt/incident-response/toolkit-setup.sh
```

### Fase 2: Identificazione

Determinare se un evento e effettivamente un incidente di sicurezza, valutarne la gravita
e classificarlo.

```bash
# Script di triage iniziale per raccolta rapida delle informazioni
cat > /opt/incident-response/triage.sh << 'SCRIPT'
#!/bin/bash
set -euo pipefail

OUTDIR="/tmp/ir-triage-$(hostname)-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTDIR"

echo "[*] Raccolta informazioni di triage..."

# Informazioni di sistema
uname -a > "$OUTDIR/system-info.txt"
uptime >> "$OUTDIR/system-info.txt"
last -50 > "$OUTDIR/last-logins.txt"
w > "$OUTDIR/who-is-on.txt"

# Processi in esecuzione
ps auxwwf > "$OUTDIR/processes.txt"
ss -tulnp > "$OUTDIR/network-connections.txt"

# Connessioni di rete attive
ss -antp | grep ESTABLISHED > "$OUTDIR/established-connections.txt"

# File modificati nelle ultime 24 ore in directory critiche
find /etc /usr/bin /usr/sbin /tmp /var/tmp -mtime -1 -type f 2>/dev/null > "$OUTDIR/recently-modified.txt"

# Crontab di tutti gli utenti
for user in $(cut -d: -f1 /etc/passwd); do
  crontab -l -u "$user" 2>/dev/null >> "$OUTDIR/crontabs.txt"
done

# Log di autenticazione recenti
tail -1000 /var/log/auth.log > "$OUTDIR/auth-log-recent.txt" 2>/dev/null

# Moduli kernel caricati
lsmod > "$OUTDIR/kernel-modules.txt"

# Hash dei file di sistema critici
sha256sum /usr/bin/sudo /usr/bin/ssh /usr/bin/sshd /bin/bash 2>/dev/null > "$OUTDIR/critical-file-hashes.txt"

echo "[*] Triage completato. Output in: $OUTDIR"
tar czf "${OUTDIR}.tar.gz" -C "$(dirname "$OUTDIR")" "$(basename "$OUTDIR")"
echo "[*] Archivio creato: ${OUTDIR}.tar.gz"
SCRIPT
chmod +x /opt/incident-response/triage.sh
```

### Fase 3: Contenimento

Limitare il danno e impedire la propagazione dell'attacco. Si distingue tra contenimento
a breve termine (immediato) e a lungo termine (strutturale).

```bash
# Contenimento a breve termine

# Isolamento di un host compromesso dalla rete (preservando i dati)
# Blocco di tutto il traffico in entrata e uscita tranne la connessione forense
iptables -I INPUT 1 -s FORENSIC_WORKSTATION_IP -j ACCEPT
iptables -I OUTPUT 1 -d FORENSIC_WORKSTATION_IP -j ACCEPT
iptables -I INPUT 2 -j DROP
iptables -I OUTPUT 2 -j DROP

# Kubernetes: isolamento di un pod compromesso con NetworkPolicy
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-compromised-pod
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: compromised-service
  policyTypes:
  - Ingress
  - Egress
  ingress: []   # Blocca tutto il traffico in entrata
  egress: []    # Blocca tutto il traffico in uscita
EOF

# Revoca immediata delle credenziali compromesse
# AWS: disabilitazione access key
aws iam update-access-key --access-key-id AKIA_COMPROMISED --status Inactive --user-name compromised-user
aws iam create-login-profile --user-name compromised-user --password-reset-required

# Rotazione dei secret in Kubernetes
kubectl delete secret db-credentials -n production
kubectl create secret generic db-credentials -n production \
  --from-literal=username=dbuser \
  --from-literal=password="$(openssl rand -base64 32)"
kubectl rollout restart deployment/api-server -n production
```

### Fase 4: Eradicazione

Rimuovere completamente la causa dell'incidente dal sistema.

### Fase 5: Recupero

Ripristinare i sistemi alla normale operativita, verificando l'integrita e monitorando
attentamente per segni di ricorrenza.

```bash
# Verifica integrita del sistema dopo eradicazione
# Confronto hash dei file di sistema con valori noti
debsums -c 2>&1 | tee /tmp/integrity-check.txt
rpm -Va 2>&1 | tee /tmp/rpm-verify.txt  # Per sistemi RHEL

# Verifica assenza di rootkit
chkrootkit 2>&1 | tee /tmp/chkrootkit.txt
rkhunter --check --skip-keypress 2>&1 | tee /tmp/rkhunter.txt

# Monitoraggio intensivo post-recovery (30 giorni)
# Aumentare il livello di logging
auditctl -w /etc/passwd -p wa -k passwd_changes
auditctl -w /etc/shadow -p wa -k shadow_changes
auditctl -w /usr/bin/sudo -p x -k sudo_usage
auditctl -w /tmp -p x -k tmp_execution
```

### Fase 6: Lessons Learned

Il post-mortem e essenziale per migliorare continuamente il processo di risposta.

```yaml
# Template Post-Mortem
incident_report:
  id: "INC-2026-042"
  title: "Accesso non autorizzato al database di produzione"
  severity: "P1 - Critical"
  date_detected: "2026-04-10T14:23:00Z"
  date_resolved: "2026-04-10T18:45:00Z"
  duration: "4h 22m"
  impact: "Potenziale esposizione di dati PII di ~5000 utenti"

  timeline:
    - time: "14:23"
      event: "Alert Wazuh: query anomala rilevata sul database"
    - time: "14:30"
      event: "CSIRT attivato, inizio triage"
    - time: "14:45"
      event: "Confermato: accesso non autorizzato tramite credenziali compromesse"
    - time: "15:00"
      event: "Contenimento: credenziali revocate, connessioni bloccate"
    - time: "16:30"
      event: "Eradicazione: punto di ingresso identificato (API key esposta in repository pubblico)"
    - time: "18:00"
      event: "Recovery: nuove credenziali distribuite, monitoraggio intensivo attivato"
    - time: "18:45"
      event: "Incidente chiuso, notifica al DPO avviata"

  root_cause: "API key del database inserita accidentalmente in un commit e pushata su un repository GitHub pubblico. Un attaccante ha utilizzato tool di scanning automatizzato per individuarla."

  action_items:
    - description: "Implementare pre-commit hook per rilevamento secret"
      owner: "security-team"
      deadline: "2026-04-17"
      status: "in-progress"
    - description: "Abilitare AWS Secrets Manager per tutte le credenziali"
      owner: "platform-team"
      deadline: "2026-04-24"
      status: "planned"
    - description: "Formazione sviluppatori su gestione sicura dei secret"
      owner: "security-team"
      deadline: "2026-05-01"
      status: "planned"
    - description: "Audit completo dei repository per secret esposti"
      owner: "security-team"
      deadline: "2026-04-14"
      status: "in-progress"
```

### Tabletop Exercises

Le esercitazioni tabletop simulano scenari di incidente per testare la preparazione del team
senza impattare i sistemi reali. Devono essere condotte almeno trimestralmente e includere
tutti gli stakeholder (team tecnico, management, comunicazione, legale).

Scenari da esercitare:
- Ransomware su infrastruttura critica
- Compromissione di credenziali privilegiate
- Data breach con esfiltrazione di dati PII
- Attacco DDoS su servizi di produzione
- Compromissione della supply chain (dipendenza malevola)
- Insider threat con accesso privilegiato

---

## 12. Best Practices

### Security Hardening Checklist per Piattaforme

```bash
# === HARDENING SISTEMA OPERATIVO ===

# Disabilitazione servizi non necessari
systemctl disable --now avahi-daemon cups bluetooth
systemctl mask ctrl-alt-del.target

# Configurazione SSH sicura
cat > /etc/ssh/sshd_config.d/hardening.conf << 'EOF'
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
MaxSessions 3
ClientAliveInterval 300
ClientAliveCountMax 2
AllowTcpForwarding no
X11Forwarding no
PermitEmptyPasswords no
LoginGraceTime 30
Protocol 2
KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
EOF

systemctl restart sshd

# Configurazione password policy
cat > /etc/security/pwquality.conf << 'EOF'
minlen = 14
dcredit = -1
ucredit = -1
ocredit = -1
lcredit = -1
maxrepeat = 3
maxclassrepeat = 4
enforce_for_root
EOF

# Configurazione audit daemon
cat > /etc/audit/rules.d/security.rules << 'EOF'
# Monitoraggio file critici
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers

# Monitoraggio comandi privilegiati
-a always,exit -F path=/usr/bin/sudo -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/su -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/chsh -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/chfn -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged

# Monitoraggio modifiche di sistema
-a always,exit -F arch=b64 -S execve -F auid>=1000 -F auid!=4294967295 -k exec
-a always,exit -F arch=b64 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts
-a always,exit -F arch=b64 -S unlink -S rmdir -F auid>=1000 -F auid!=4294967295 -k delete

# Protezione regole audit (rendere immutabili)
-e 2
EOF

augenrules --load

# === HARDENING KUBERNETES ===

# Verifica configurazione API server
kubectl get pods -n kube-system -l component=kube-apiserver -o yaml | \
  grep -E "(--anonymous-auth|--authorization-mode|--audit-log)"

# Abilitazione audit logging
cat > /etc/kubernetes/audit-policy.yaml << 'EOF'
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: None
    resources:
    - group: ""
      resources: ["endpoints", "services", "services/status"]
  - level: Metadata
    resources:
    - group: ""
      resources: ["secrets", "configmaps"]
  - level: Request
    resources:
    - group: ""
      resources: ["pods", "pods/log", "pods/status"]
  - level: RequestResponse
    users: ["system:admin"]
    verbs: ["create", "update", "patch", "delete"]
  - level: Metadata
    omitStages:
    - RequestReceived
EOF
```

### Defense in Depth — Layers

```
Layer 1 — Governance:     Policy, compliance, training, risk assessment
Layer 2 — Perimetro:      WAF, DDoS mitigation, CDN, DNS security
Layer 3 — Rete:           Segmentazione, firewall, IDS/IPS, NAC
Layer 4 — Host:           OS hardening, EDR, patch management, FIM
Layer 5 — Applicazione:   SAST, DAST, dependency scanning, secure coding
Layer 6 — Dati:           Encryption at rest/in transit, DLP, access control, backup
Layer 7 — Identity:       MFA, SSO, RBAC, PAM, zero trust
Layer 8 — Monitoraggio:   SIEM, log analysis, threat detection, incident response
```

### Security Monitoring Baseline

```yaml
# Monitoring minimo richiesto per ogni piattaforma
monitoring_baseline:
  log_sources:
    - os_auth_logs        # /var/log/auth.log, Windows Security
    - application_logs    # Structured JSON logging
    - network_flow_logs   # VPC Flow Logs, NetFlow
    - dns_query_logs      # DNS resolution logging
    - waf_logs            # WAF decision logs
    - api_gateway_logs    # API access logs
    - database_audit_logs # Query audit trail
    - container_logs      # stdout/stderr + runtime events

  alert_rules:
    critical:
      - multiple_failed_logins_same_source     # >5 in 5 min
      - successful_login_after_failures         # brute force success
      - privilege_escalation_attempt             # sudo/su anomalo
      - database_export_large_dataset            # >10k records
      - new_admin_account_created                # account creation
      - security_group_opened_to_world           # 0.0.0.0/0 rule
      - secret_accessed_by_unknown_identity      # vault/KMS audit
      - container_escape_attempt                 # Falco alert
    high:
      - unusual_outbound_traffic                 # data exfiltration
      - new_scheduled_task_or_cron               # persistence
      - binary_executed_from_tmp                 # malware execution
      - dns_query_to_known_bad_domain            # C2 communication
      - certificate_expiring_within_7_days       # operational risk
    medium:
      - failed_login_from_new_geography          # account takeover
      - api_rate_limit_exceeded                  # abuse detection
      - dependency_vulnerability_critical        # supply chain
      - configuration_drift_detected             # IaC compliance

  retention:
    security_alerts: 365d
    authentication_logs: 180d
    application_logs: 90d
    network_flow_logs: 30d
    raw_events: 14d
```

### Secret Management

```bash
# Principi di gestione dei secret:
# 1. Mai in codice sorgente o file di configurazione versionati
# 2. Rotazione automatica programmata
# 3. Accesso audit-logged
# 4. Encryption at rest e in transit
# 5. Principio del least privilege

# Verifica assenza di secret nei repository
# Pre-commit hook con gitleaks
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
    - id: gitleaks
EOF

# Scansione retrospettiva di un repository
gitleaks detect --source=. --report-format=json --report-path=leaks-report.json

# Trufflehog per scansione approfondita
trufflehog git file://. --json --only-verified > verified-secrets.json
```

### Network Encryption

```bash
# Verifica configurazione TLS di un servizio
# Scansione con testssl.sh
testssl.sh --severity HIGH --jsonfile tls-report.json https://app.example.com

# Verifica con nmap
nmap --script ssl-enum-ciphers -p 443 app.example.com

# Configurazione TLS minima raccomandata (Nginx)
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

### Access Control Review Process

```yaml
# Processo di revisione accessi (trimestrale)
access_review_process:
  frequency: quarterly
  scope:
    - production_systems
    - cloud_iam_policies
    - database_access
    - kubernetes_rbac
    - vpn_and_bastion_access
    - third_party_integrations

  steps:
    1_extract:
      description: "Esportare la lista completa degli accessi da tutti i sistemi"
      commands:
        - "aws iam get-credential-report --output text --query Content | base64 -d > aws-users.csv"
        - "kubectl auth can-i --list --all-namespaces > k8s-permissions.txt"
        - "az ad user list --query '[].{Name:displayName,UPN:userPrincipalName,Enabled:accountEnabled}' -o table"

    2_review:
      description: "Ogni manager verifica gli accessi del proprio team"
      criteria:
        - "L'accesso e ancora necessario per il ruolo attuale?"
        - "Il livello di privilegio e appropriato (least privilege)?"
        - "Ci sono account inattivi (>90 giorni senza login)?"
        - "Ci sono account di servizio con permessi eccessivi?"

    3_remediate:
      description: "Rimuovere accessi non piu necessari"
      sla: "5 giorni lavorativi dalla segnalazione"

    4_document:
      description: "Documentare decisioni e eccezioni"
      retention: "3 anni per compliance"
```

### Security as Code

```yaml
# Terraform: enforcement automatico di policy di sicurezza
# tfsec / Checkov nella pipeline CI/CD
name: Infrastructure Security
on:
  pull_request:
    paths: ['terraform/**']

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: tfsec Security Scan
        uses: aquasecurity/tfsec-action@v1.0.0
        with:
          working_directory: terraform/
          soft_fail: false

      - name: Checkov IaC Scan
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: terraform/
          framework: terraform
          check: CKV_AWS_18,CKV_AWS_19,CKV_AWS_21,CKV_AWS_145
          # CKV_AWS_18: S3 logging
          # CKV_AWS_19: S3 encryption
          # CKV_AWS_21: S3 versioning
          # CKV_AWS_145: RDS encryption
```

### Compliance Alignment

| Framework      | Ambito                              | Settore         |
|----------------|-------------------------------------|-----------------|
| SOC 2 Type II  | Controlli di sicurezza e privacy    | SaaS, Cloud     |
| ISO 27001      | Sistema di gestione sicurezza info  | Tutti           |
| PCI DSS        | Dati carte di pagamento             | Finanza, Retail |
| HIPAA          | Dati sanitari                       | Sanita          |
| GDPR           | Dati personali cittadini UE         | Tutti (UE)      |
| NIS2           | Sicurezza reti e sistemi info       | Infrastrutture  |
| NIST CSF       | Framework cybersecurity             | Governo US      |

Ogni framework richiede specifici controlli tecnici e organizzativi. L'allineamento deve essere
verificato periodicamente tramite audit interni e, ove richiesto, certificazioni esterne.
L'approccio "security as code" consente di codificare i requisiti di compliance come policy
automatiche verificate nella pipeline CI/CD, riducendo il rischio di drift e garantendo
la conformita continua.

### Security Training

La formazione sulla sicurezza deve essere continua e adattata ai ruoli:

- **Sviluppatori**: secure coding practices, OWASP Top 10, gestione dei secret, threat modeling
- **Operations**: hardening, incident response, log analysis, patch management
- **Management**: risk assessment, compliance, incident communication, business continuity
- **Tutti**: phishing awareness, password hygiene, social engineering, reporting procedure

Le esercitazioni pratiche (CTF, tabletop, red team/blue team) sono significativamente piu efficaci
della formazione passiva. Devono essere condotte almeno semestralmente con metriche di partecipazione
e risultati tracciati nel tempo.

---

## 13. Zero Trust Architecture — Approfondimento

### Architettura Zero Trust per Piattaforme Distribuite

L'implementazione di Zero Trust in ambienti distribuiti richiede un approccio sistematico
che coinvolge ogni livello dello stack tecnologico. Secondo il Red Hat State of Kubernetes
Security Report 2024, le organizzazioni che hanno implementato principi Zero Trust nei
propri ambienti container hanno registrato il 57% in meno di attacchi riusciti rispetto
a quelle che si affidavano a modelli di sicurezza tradizionali.

L'architettura Zero Trust per piattaforme cloud-native si articola in cinque pilastri
interconnessi, ciascuno con responsabilita specifiche e strumenti dedicati.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     ZERO TRUST CONTROL PLANE                            │
│                                                                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐            │
│  │  Policy    │  │  Identity  │  │  Device    │  │  Threat    │           │
│  │  Decision  │  │  Provider  │  │  Trust     │  │  Intelli-  │           │
│  │  Point     │  │  (IdP)     │  │  Evaluator │  │  gence     │           │
│  │  (PDP)     │  │            │  │            │  │  Engine    │           │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘           │
│        │               │               │               │                 │
│        └───────────────┴───────────────┴───────────────┘                 │
│                              │                                           │
│                    ┌─────────▼──────────┐                                │
│                    │  Policy Enforcement │                                │
│                    │  Point (PEP)        │                                │
│                    └─────────┬──────────┘                                │
│                              │                                           │
├──────────────────────────────┼───────────────────────────────────────────┤
│               DATA PLANE     │                                           │
│                              ▼                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │                │
│  │ A        │──│ B        │──│ C        │──│ D        │                │
│  │ (mTLS)   │  │ (mTLS)   │  │ (mTLS)   │  │ (mTLS)   │                │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                │
└──────────────────────────────────────────────────────────────────────────┘
```

### SPIFFE/SPIRE — Identita Crittografica per Workload

**SPIFFE** (Secure Production Identity Framework for Everyone) definisce uno standard
per l'identita dei workload in ambienti distribuiti. **SPIRE** e l'implementazione
di riferimento che automatizza l'emissione e la rotazione delle identita crittografiche,
eliminando la necessita di credenziali statiche a lunga durata.

```yaml
# Configurazione SPIRE Server su Kubernetes
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: spire-server
  namespace: spire
spec:
  replicas: 1
  selector:
    matchLabels:
      app: spire-server
  template:
    metadata:
      labels:
        app: spire-server
    spec:
      serviceAccountName: spire-server
      containers:
      - name: spire-server
        image: ghcr.io/spiffe/spire-server:1.10.0
        args:
        - -config
        - /run/spire/config/server.conf
        ports:
        - containerPort: 8081
        volumeMounts:
        - name: spire-config
          mountPath: /run/spire/config
          readOnly: true
        - name: spire-data
          mountPath: /run/spire/data
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
      volumes:
      - name: spire-config
        configMap:
          name: spire-server-config
---
# Configurazione SPIRE Server
apiVersion: v1
kind: ConfigMap
metadata:
  name: spire-server-config
  namespace: spire
data:
  server.conf: |
    server {
      bind_address = "0.0.0.0"
      bind_port = "8081"
      trust_domain = "example.org"
      data_dir = "/run/spire/data"
      log_level = "INFO"
      ca_ttl = "24h"
      default_x509_svid_ttl = "1h"

      ca_subject {
        country = ["IT"]
        organization = ["Example Corp"]
        common_name = ""
      }
    }

    plugins {
      DataStore "sql" {
        plugin_data {
          database_type = "sqlite3"
          connection_string = "/run/spire/data/datastore.sqlite3"
        }
      }

      NodeAttestor "k8s_psat" {
        plugin_data {
          clusters = {
            "production" = {
              service_account_allow_list = ["spire:spire-agent"]
            }
          }
        }
      }

      KeyManager "disk" {
        plugin_data {
          keys_path = "/run/spire/data/keys.json"
        }
      }
    }
```

```bash
# Registrazione di workload con SPIRE
# Ogni workload riceve un SPIFFE ID univoco
spire-server entry create \
  -spiffeID spiffe://example.org/ns/production/sa/api-server \
  -parentID spiffe://example.org/node/k8s-worker-1 \
  -selector k8s:ns:production \
  -selector k8s:sa:api-server \
  -ttl 3600

spire-server entry create \
  -spiffeID spiffe://example.org/ns/production/sa/database-proxy \
  -parentID spiffe://example.org/node/k8s-worker-1 \
  -selector k8s:ns:production \
  -selector k8s:sa:database-proxy \
  -ttl 3600

# Verifica identita registrate
spire-server entry show
```

### Continuous Adaptive Trust — Valutazione Dinamica del Rischio

Il modello **Continuous Adaptive Trust** estende il concetto di Zero Trust introducendo
la valutazione continua e dinamica del livello di fiducia, che si adatta in tempo reale
in base ai segnali di rischio. A differenza dell'approccio binario (accesso concesso o negato),
il trust score puo variare nel tempo e determinare livelli di accesso differenziati.

```yaml
# Esempio di policy di trust scoring per OPA (Open Policy Agent)
# Le decisioni di accesso considerano molteplici fattori
# trust-scoring-policy.rego
package trust.scoring

import rego.v1

default trust_score := 0
default access_decision := "deny"

# Fattori che contribuiscono al trust score
trust_score := score if {
    identity_score := identity_trust_factor
    device_score := device_trust_factor
    behavior_score := behavior_trust_factor
    network_score := network_trust_factor
    score := (identity_score + device_score + behavior_score + network_score) / 4
}

# Identita verificata con MFA = alto trust
identity_trust_factor := 100 if {
    input.authentication.method == "mfa"
    input.authentication.mfa_type == "hardware_key"
} else := 70 if {
    input.authentication.method == "mfa"
    input.authentication.mfa_type == "totp"
} else := 30 if {
    input.authentication.method == "password"
} else := 0

# Dispositivo conforme = alto trust
device_trust_factor := 100 if {
    input.device.managed == true
    input.device.os_patched == true
    input.device.disk_encrypted == true
    input.device.edr_active == true
} else := 50 if {
    input.device.managed == true
    input.device.os_patched == true
} else := 10

# Comportamento nella norma = alto trust
behavior_trust_factor := 100 if {
    input.behavior.login_time_normal == true
    input.behavior.geo_consistent == true
    input.behavior.no_anomalies == true
} else := 40 if {
    input.behavior.geo_consistent == true
} else := 0

# Rete affidabile = alto trust
network_trust_factor := 100 if {
    input.network.type == "corporate_managed"
} else := 60 if {
    input.network.type == "known_vpn"
} else := 20 if {
    input.network.type == "public"
} else := 0

# Decisioni di accesso basate sul trust score
access_decision := "full_access" if {
    trust_score >= 80
}

access_decision := "limited_access" if {
    trust_score >= 50
    trust_score < 80
}

access_decision := "step_up_required" if {
    trust_score >= 30
    trust_score < 50
}

access_decision := "deny" if {
    trust_score < 30
}
```

---

## 14. Container Security — Deep Dive

### Image Scanning Avanzato e Image Supply Chain

La sicurezza delle immagini container rappresenta il primo livello di difesa nell'ecosistema
cloud-native. Un'immagine compromessa o vulnerabile puo propagare rischi a ogni ambiente
in cui viene eseguita.

```bash
# Scansione multi-scanner per massimizzare la copertura
# Trivy: scansione completa (OS + librerie + IaC + secret)
trivy image --scanners vuln,secret,misconfig \
  --severity HIGH,CRITICAL \
  --format json \
  --output trivy-scan.json \
  myregistry.io/myapp:v3.0.0

# Grype: scansione vulnerabilita con database aggiornato
grype myregistry.io/myapp:v3.0.0 \
  --output json \
  --file grype-scan.json \
  --fail-on high

# Scansione dell'intera catena di dipendenze con Syft + Grype
syft myregistry.io/myapp:v3.0.0 -o cyclonedx-json > sbom.json
grype sbom:sbom.json --output table

# Confronto risultati tra scanner per ridurre falsi negativi
cat trivy-scan.json | jq '[.Results[].Vulnerabilities[]? | .VulnerabilityID] | unique | length'
cat grype-scan.json | jq '[.matches[].vulnerability.id] | unique | length'
```

### Distroless e Minimal Base Images

Le immagini **distroless** eliminano shell, package manager e utilities di sistema,
riducendo drasticamente la superficie di attacco. In un'immagine distroless,
l'assenza di una shell impedisce agli attaccanti di eseguire comandi arbitrari
anche in caso di compromissione del container.

```dockerfile
# Multi-stage build con immagine distroless
# Stage 1: build
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w" -o /app ./cmd/server

# Stage 2: runtime distroless
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app /app
USER 65534:65534
EXPOSE 8080
ENTRYPOINT ["/app"]
```

```bash
# Confronto dimensioni e vulnerabilita tra base images
# Ubuntu: ~78MB, ~100+ CVE note
trivy image ubuntu:24.04 --severity HIGH,CRITICAL -q | tail -1

# Alpine: ~7MB, ~10-20 CVE note
trivy image alpine:3.20 --severity HIGH,CRITICAL -q | tail -1

# Distroless: ~2MB, ~0-5 CVE note
trivy image gcr.io/distroless/static-debian12:nonroot --severity HIGH,CRITICAL -q | tail -1

# Chainguard: immagini con zero CVE note (build quotidiane)
trivy image cgr.dev/chainguard/static:latest --severity HIGH,CRITICAL -q | tail -1
```

### Runtime Security con Sysdig e Tetragon

Oltre a Falco (trattato nella sezione 7), strumenti come **Sysdig Secure** e **Tetragon**
offrono capacita avanzate di runtime security basate su eBPF per il monitoraggio
delle system call a basso overhead.

```yaml
# Tetragon (Cilium): policy di sicurezza basate su eBPF
# Rilevamento e blocco di esecuzioni sospette a livello kernel
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-binary-execution-in-tmp
spec:
  kprobes:
  - call: "security_bprm_check"
    syscall: false
    args:
    - index: 0
      type: "linux_binprm"
    selectors:
    - matchArgs:
      - index: 0
        operator: "Prefix"
        values:
        - "/tmp/"
        - "/var/tmp/"
        - "/dev/shm/"
      matchActions:
      - action: Sigkill
        rateLimit: "1m"
      - action: Post
        rateLimit: "1m"
---
# Tetragon: monitoraggio accesso a file sensibili
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: monitor-sensitive-file-access
spec:
  kprobes:
  - call: "fd_install"
    syscall: false
    args:
    - index: 0
      type: "int"
    - index: 1
      type: "file"
    selectors:
    - matchArgs:
      - index: 1
        operator: "Prefix"
        values:
        - "/etc/shadow"
        - "/etc/passwd"
        - "/root/.ssh/"
        - "/var/run/secrets/kubernetes.io/"
      matchNamespaces:
      - namespace: Mnt
        operator: NotIn
        values:
        - "host_mnt"
      matchActions:
      - action: Post
```

```bash
# Sysdig: cattura forense di un container in esecuzione
# Cattura tutti gli eventi di sistema per analisi offline
sysdig -s 4096 -w capture.scap container.name=suspicious-container

# Analisi degli eventi catturati
# File aperti dal container
sysdig -r capture.scap -p"%evt.time %proc.name %fd.name" evt.type=open

# Connessioni di rete stabilite
sysdig -r capture.scap -p"%evt.time %proc.name %fd.name" evt.type=connect

# Processi creati
sysdig -r capture.scap -p"%evt.time %proc.pname -> %proc.name %proc.args" evt.type=execve

# Csysdig: interfaccia interattiva per l'analisi
csysdig -r capture.scap
```

### Container Isolation — gVisor e Kata Containers

Per workload ad alto rischio, l'isolamento standard dei container Linux (cgroups + namespaces)
potrebbe non essere sufficiente. Soluzioni come **gVisor** e **Kata Containers** offrono
un livello aggiuntivo di isolamento.

```yaml
# Kubernetes: utilizzo di gVisor come runtime per workload sensibili
# RuntimeClass per gVisor
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
scheduling:
  nodeSelector:
    runtime: gvisor
---
# Pod che utilizza gVisor per isolamento rafforzato
apiVersion: v1
kind: Pod
metadata:
  name: untrusted-workload
  namespace: sandbox
spec:
  runtimeClassName: gvisor
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: processing
    image: myregistry.io/data-processor:v1.0.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      requests:
        cpu: 500m
        memory: 256Mi
      limits:
        cpu: "1"
        memory: 512Mi
```

| Tecnologia | Tipo di isolamento | Overhead | Compatibilita | Caso d'uso |
|---|---|---|---|---|
| **runc** (default) | Namespaces + cgroups | Minimo | Massima | Workload trusted, sviluppo |
| **gVisor** | User-space kernel | Moderato (5-15%) | Buona, alcune syscall limitate | Multi-tenant, workload untrusted |
| **Kata Containers** | VM leggera | Moderato (10-20%) | Eccellente | Isolamento forte, compliance |
| **Firecracker** | microVM | Basso (3-5%) | Buona | Serverless, funzioni isolate |

---

## 15. Kubernetes Security — Approfondimento

### RBAC — Configurazione Avanzata

Il **Role-Based Access Control** di Kubernetes e il meccanismo primario per controllare
l'accesso alle risorse del cluster. Organizzazioni che implementano RBAC correttamente
configurato hanno ridotto gli incidenti di sicurezza del 64% rispetto ad ambienti
senza controlli di accesso strutturati.

```yaml
# ClusterRole per operatori con permessi limitati per namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: namespace-operator
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets", "daemonsets"]
  verbs: ["get", "list", "watch", "create", "update", "delete"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
  # N.B.: nessun permesso di create/update/delete sui secret
- apiGroups: [""]
  resources: ["nodes", "persistentvolumes"]
  verbs: ["get", "list", "watch"]
  # Solo lettura sulle risorse cluster-wide
---
# ClusterRole per auditor (solo lettura su tutto)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: security-auditor
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- nonResourceURLs: ["*"]
  verbs: ["get"]
---
# Aggregazione RBAC: composizione di ruoli
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-reader
  labels:
    rbac.authorization.k8s.io/aggregate-to-view: "true"
rules:
- apiGroups: ["monitoring.coreos.com"]
  resources: ["prometheusrules", "servicemonitors", "podmonitors"]
  verbs: ["get", "list", "watch"]
```

```bash
# Audit dei permessi RBAC nel cluster
# Chi puo creare pod nel namespace production?
kubectl auth can-i create pods -n production --list

# Verifica permessi di un service account specifico
kubectl auth can-i --as=system:serviceaccount:production:api-server \
  --list -n production

# Elenco di tutti i ClusterRoleBinding con permessi cluster-admin
kubectl get clusterrolebindings -o json | \
  jq '.items[] | select(.roleRef.name=="cluster-admin") |
      {name: .metadata.name,
       subjects: [.subjects[]? | {kind, name, namespace}]}'

# Identificazione di service account con permessi eccessivi
kubectl get rolebindings,clusterrolebindings --all-namespaces -o json | \
  jq '.items[] | select(.roleRef.name | test("admin|cluster-admin|edit")) |
      {binding: .metadata.name,
       namespace: .metadata.namespace,
       role: .roleRef.name,
       subjects: [.subjects[]? | "\(.kind)/\(.name)"]}'

# rbac-tool: analisi visuale dei permessi
kubectl krew install rbac-tool
kubectl rbac-tool who-can create deployments -n production
kubectl rbac-tool analysis
```

### Network Policies — Segmentazione a Livello di Cluster

Le **Network Policies** di Kubernetes implementano la microsegmentazione a livello di pod,
controllando il traffico in ingresso e in uscita per ogni workload.

```yaml
# Default deny: bloccare tutto il traffico non esplicitamente autorizzato
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# Consentire solo il traffico necessario al frontend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-traffic
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: api-server
    ports:
    - protocol: TCP
      port: 8080
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
---
# Cilium: Network Policy avanzata con filtraggio L7
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-server-l7-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: api-server
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/api/v1/.*"
        - method: "POST"
          path: "/api/v1/orders"
          headers:
          - 'Content-Type: application/json'
  egress:
  - toEndpoints:
    - matchLabels:
        app: database
    toPorts:
    - ports:
      - port: "5432"
        protocol: TCP
  - toFQDNs:
    - matchName: "api.external-service.com"
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP
```

### OPA Gatekeeper — Policy Avanzate

```yaml
# ConstraintTemplate: limitare le risorse CPU/memoria
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sresourcelimits
spec:
  crd:
    spec:
      names:
        kind: K8sResourceLimits
      validation:
        openAPIV3Schema:
          type: object
          properties:
            maxCpu:
              type: string
            maxMemory:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sresourcelimits

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.cpu
          msg := sprintf("Il container '%v' deve avere limiti CPU definiti.", [container.name])
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.memory
          msg := sprintf("Il container '%v' deve avere limiti di memoria definiti.", [container.name])
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          cpu_limit := container.resources.limits.cpu
          max_cpu := input.parameters.maxCpu
          units.parse_cpu(cpu_limit) > units.parse_cpu(max_cpu)
          msg := sprintf(
            "Il container '%v' ha un limite CPU (%v) superiore al massimo consentito (%v).",
            [container.name, cpu_limit, max_cpu]
          )
        }
---
# Constraint: applicazione dei limiti
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sResourceLimits
metadata:
  name: enforce-resource-limits
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces:
    - production
    - staging
  parameters:
    maxCpu: "2"
    maxMemory: "4Gi"
---
# ConstraintTemplate: impedire hostPath mounts
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8snohostpath
spec:
  crd:
    spec:
      names:
        kind: K8sNoHostPath
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8snohostpath

        violation[{"msg": msg}] {
          volume := input.review.object.spec.volumes[_]
          volume.hostPath
          msg := sprintf(
            "Il volume '%v' utilizza hostPath, che non e consentito per motivi di sicurezza.",
            [volume.name]
          )
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sNoHostPath
metadata:
  name: deny-host-path
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces:
    - production
    - staging
```

### Kubernetes Audit Logging Avanzato

```yaml
# Audit policy granulare per Kubernetes
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Non loggare le richieste di health check
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
    - group: ""
      resources: ["endpoints", "services", "services/status"]

  # Non loggare i read su configmap e secret del kube-system
  - level: None
    users: ["kubelet", "system:node-*"]
    verbs: ["get"]
    resources:
    - group: ""
      resources: ["configmaps"]
    namespaces: ["kube-system"]

  # Loggare ogni accesso ai secret a livello Metadata
  - level: Metadata
    resources:
    - group: ""
      resources: ["secrets"]
    omitStages:
    - "RequestReceived"

  # Loggare operazioni di scrittura su risorse critiche a livello RequestResponse
  - level: RequestResponse
    verbs: ["create", "update", "patch", "delete"]
    resources:
    - group: ""
      resources: ["pods", "services"]
    - group: "apps"
      resources: ["deployments", "statefulsets", "daemonsets"]
    - group: "rbac.authorization.k8s.io"
      resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
    - group: "networking.k8s.io"
      resources: ["networkpolicies"]

  # Loggare tutte le operazioni degli utenti admin a livello RequestResponse
  - level: RequestResponse
    users: ["admin", "system:admin"]
    verbs: ["*"]

  # Loggare tutto il resto a livello Metadata
  - level: Metadata
    omitStages:
    - "RequestReceived"
```

---

## 16. Secrets Management — Confronto Approfondito

### Confronto tra Soluzioni di Secrets Management

La gestione sicura dei secret e un requisito fondamentale per qualsiasi piattaforma.
La scelta della soluzione dipende dall'ecosistema cloud, dalla complessita dell'infrastruttura
e dai requisiti di conformita.

| Caratteristica | HashiCorp Vault | AWS Secrets Manager | Azure Key Vault | GCP Secret Manager |
|---|---|---|---|---|
| **Deployment** | Self-hosted o HCP | Managed (AWS) | Managed (Azure) | Managed (GCP) |
| **Multi-cloud** | Nativo | Solo AWS | Solo Azure | Solo GCP |
| **Secret dinamici** | Database, PKI, SSH, Cloud | RDS, Redshift | Limitato | Limitato |
| **Rotazione auto** | Si (custom + built-in) | Si (Lambda) | Si (Event Grid) | Si (Cloud Functions) |
| **Encryption** | Transit engine (EaaS) | KMS integrato | HSM integrato | KMS integrato |
| **PKI** | CA completa integrata | ACM separato | Certificati integrati | CAS separato |
| **Audit logging** | File, syslog, socket | CloudTrail | Monitor + Diagnostic | Cloud Audit Logs |
| **Costo** | OSS gratuito / HCP a consumo | $0.40/secret/mese | $0.03/operazione | $0.06/10k operazioni |
| **K8s integration** | CSI driver, Agent sidecar | CSI driver, ASCP | CSI driver, AKSC | CSI driver, Workload ID |

### HashiCorp Vault — Configurazione Avanzata

```bash
# Inizializzazione e unseal di Vault
vault operator init -key-shares=5 -key-threshold=3

# Abilitazione del secrets engine per database dinamici
vault secrets enable database

# Configurazione connessione PostgreSQL
vault write database/config/production-db \
  plugin_name=postgresql-database-plugin \
  connection_url="postgresql://{{username}}:{{password}}@db.example.com:5432/production?sslmode=verify-full" \
  allowed_roles="readonly,readwrite" \
  username="vault_admin" \
  password="INITIAL_PASSWORD"

# Rotazione della password root (Vault la gestisce, nessuno la conosce)
vault write -force database/rotate-root/production-db

# Creazione ruolo per credenziali dinamiche (readonly)
vault write database/roles/readonly \
  db_name=production-db \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  revocation_statements="REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM \"{{name}}\"; DROP ROLE IF EXISTS \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"

# Ottenimento credenziali dinamiche (create on-demand, revocate automaticamente)
vault read database/creds/readonly
# Ogni chiamata genera un nuovo utente DB con password unica e TTL

# Abilitazione PKI per emissione certificati
vault secrets enable pki
vault secrets tune -max-lease-ttl=87600h pki

# Generazione CA root
vault write -field=certificate pki/root/generate/internal \
  common_name="example.com" \
  issuer_name="root-2025" \
  ttl=87600h > CA_cert.crt

# Creazione ruolo per emissione certificati server
vault write pki/roles/server-certs \
  allowed_domains="example.com,internal.example.com" \
  allow_subdomains=true \
  max_ttl="720h" \
  key_type="ec" \
  key_bits=256 \
  require_cn=false
```

### Vault Agent Sidecar su Kubernetes

```yaml
# Injector di secret Vault con annotazioni sui Pod
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "api-server"
        vault.hashicorp.com/agent-inject-secret-db-creds: "database/creds/readonly"
        vault.hashicorp.com/agent-inject-template-db-creds: |
          {{- with secret "database/creds/readonly" -}}
          export DB_USERNAME="{{ .Data.username }}"
          export DB_PASSWORD="{{ .Data.password }}"
          {{- end }}
        vault.hashicorp.com/agent-inject-secret-tls: "pki/issue/server-certs"
        vault.hashicorp.com/agent-inject-template-tls: |
          {{- with secret "pki/issue/server-certs" "common_name=api.internal.example.com" -}}
          {{ .Data.certificate }}
          {{ .Data.private_key }}
          {{- end }}
    spec:
      serviceAccountName: api-server
      containers:
      - name: api-server
        image: myregistry.io/api-server:v3.0.0
        command: ["sh", "-c", "source /vault/secrets/db-creds && exec ./server"]
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: "1"
            memory: 512Mi
```

### External Secrets Operator

```yaml
# External Secrets Operator: sincronizzazione da provider esterni
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-store
  namespace: production
spec:
  provider:
    vault:
      server: "https://vault.example.com:8200"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "production-reader"
          serviceAccountRef:
            name: "external-secrets-sa"
---
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-store
  namespace: production
spec:
  provider:
    aws:
      service: SecretsManager
      region: eu-west-1
      auth:
        jwt:
          serviceAccountRef:
            name: "external-secrets-sa"
---
# ExternalSecret: sincronizzazione automatica
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: api-credentials
  namespace: production
spec:
  refreshInterval: 15m
  secretStoreRef:
    name: vault-store
    kind: SecretStore
  target:
    name: api-credentials
    creationPolicy: Owner
    deletionPolicy: Retain
  data:
  - secretKey: database-url
    remoteRef:
      key: production/api-server
      property: database_url
  - secretKey: api-key
    remoteRef:
      key: production/api-server
      property: api_key
  - secretKey: jwt-secret
    remoteRef:
      key: production/api-server
      property: jwt_secret
```

---

## 17. Identity and Access Management (IAM) per Piattaforme

### Federazione delle Identita e SSO

In ambienti multi-piattaforma, la gestione centralizzata delle identita tramite
**Single Sign-On** (SSO) e **federation** riduce la superficie di attacco
eliminando la proliferazione di credenziali.

```yaml
# Keycloak: configurazione realm per SSO aziendale
# realm-export.json (struttura semplificata)
realm_config:
  realm: "corporate"
  enabled: true
  sslRequired: "all"
  bruteForceProtected: true
  failureFactor: 5
  waitIncrementSeconds: 60
  maxFailureWaitSeconds: 900
  permanentLockout: false

  passwordPolicy: >-
    length(14) and
    upperCase(1) and
    lowerCase(1) and
    digits(1) and
    specialChars(1) and
    notUsername and
    passwordHistory(5) and
    hashAlgorithm(pbkdf2-sha512) and
    hashIterations(210000)

  clients:
    - clientId: "kubernetes-dashboard"
      protocol: "openid-connect"
      publicClient: false
      standardFlowEnabled: true
      directAccessGrantsEnabled: false
      rootUrl: "https://dashboard.k8s.example.com"
      redirectUris:
        - "https://dashboard.k8s.example.com/oauth2/callback"
      webOrigins:
        - "https://dashboard.k8s.example.com"
      defaultClientScopes:
        - "openid"
        - "profile"
        - "email"
        - "groups"

    - clientId: "argocd"
      protocol: "openid-connect"
      publicClient: false
      standardFlowEnabled: true
      rootUrl: "https://argocd.example.com"
      redirectUris:
        - "https://argocd.example.com/auth/callback"
      defaultClientScopes:
        - "openid"
        - "profile"
        - "groups"

  identityProviders:
    - alias: "corporate-saml"
      providerId: "saml"
      enabled: true
      config:
        singleSignOnServiceUrl: "https://idp.corporate.example.com/saml/sso"
        validateSignature: "true"
        wantAuthnRequestsSigned: "true"
        signingCertificate: "MII..."
```

### Privileged Access Management (PAM)

```bash
# Configurazione di accesso privilegiato just-in-time (JIT)
# Esempio con Teleport per accesso SSH e Kubernetes

# teleport.yaml — configurazione Teleport Auth Server
cat > /etc/teleport/teleport.yaml << 'EOF'
version: v3
teleport:
  nodename: teleport-auth
  data_dir: /var/lib/teleport
  auth_token: ""
  log:
    output: stderr
    severity: INFO

auth_service:
  enabled: true
  cluster_name: production.example.com
  authentication:
    type: oidc
    second_factor: on
    webauthn:
      rp_id: teleport.example.com
  session_recording: node-sync

  # Access request: elevazione temporanea dei privilegi
  # Gli utenti devono richiedere l'accesso e ottenere approvazione
  roles:
    - name: production-readonly
      options:
        max_session_ttl: 8h
      allow:
        logins: ["readonly"]
        kubernetes_groups: ["view"]
        kubernetes_labels:
          env: ["production"]
        rules:
        - resources: ["session"]
          verbs: ["list", "read"]

    - name: production-admin-jit
      options:
        max_session_ttl: 2h
        request_access: always
        request_prompt: "Motivo dell'accesso admin a production:"
      allow:
        logins: ["admin"]
        kubernetes_groups: ["system:masters"]
        kubernetes_labels:
          env: ["production"]
        request:
          roles: ["production-admin-jit"]
          thresholds:
          - approve: 2
            deny: 1
            filter: 'contains(reviewer.roles, "security-team")'
          max_duration: 2h
EOF
```

---

## 18. Compliance Automation

### Compliance as Code — Approccio Automatizzato

L'automazione della compliance trasforma i requisiti normativi in policy verificabili
eseguibili nella pipeline CI/CD, garantendo conformita continua anziche verifiche
periodiche manuali. Attualmente solo il 13% delle organizzazioni adotta pienamente
l'approccio compliance-as-code, ma la tendenza e in forte crescita.

```yaml
# Checkov: policy di compliance per Terraform
# Verifica conformita CIS AWS Foundations Benchmark
# checkov -d terraform/ --framework terraform --check CKV_AWS_*

# Esempio di custom policy Checkov per requisiti GDPR
# custom_policy/gdpr_encryption.py
# from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck
# from checkov.common.models.enums import CheckResult, CheckCategories

# class GDPREncryptionAtRest(BaseResourceCheck):
#     def __init__(self):
#         name = "Ensure all storage is encrypted at rest (GDPR Art. 32)"
#         id = "CKV_GDPR_1"
#         supported = ["aws_s3_bucket", "aws_rds_instance",
#                      "aws_ebs_volume", "aws_efs_file_system"]
#         categories = [CheckCategories.ENCRYPTION]
#         super().__init__(name=name, id=id,
#                         categories=categories,
#                         supported_resources=supported)
```

### Mapping Controlli Tecnici a Framework di Compliance

```yaml
# Mappa dei controlli tecnici per framework di compliance
compliance_control_mapping:

  encryption_at_rest:
    technical_control: "AES-256 encryption su tutti i volumi e database"
    verification: "checkov -c CKV_AWS_19,CKV_AWS_145,CKV_AWS_17"
    frameworks:
      PCI-DSS: "Req 3.4 — Render PAN unreadable"
      SOC2: "CC6.1 — Logical and Physical Access Controls"
      GDPR: "Art 32 — Security of Processing"
      ISO27001: "A.10.1.1 — Policy on use of cryptographic controls"

  access_control:
    technical_control: "RBAC + MFA su tutti gli accessi privilegiati"
    verification: "kubectl rbac-tool analysis && vault audit"
    frameworks:
      PCI-DSS: "Req 7.1 — Limit access to need-to-know"
      SOC2: "CC6.2 — Prior to Registration"
      GDPR: "Art 25 — Data protection by design"
      ISO27001: "A.9.2.3 — Management of privileged access rights"

  logging_monitoring:
    technical_control: "Audit logging centralizzato con retention >= 1 anno"
    verification: "prowler aws --check check11,check12"
    frameworks:
      PCI-DSS: "Req 10 — Track and monitor all access"
      SOC2: "CC7.2 — System monitoring"
      GDPR: "Art 30 — Records of processing activities"
      ISO27001: "A.12.4 — Logging and monitoring"

  vulnerability_management:
    technical_control: "Scansione settimanale + patch critici entro 48h"
    verification: "trivy image --exit-code 1 && prowler aws --severity critical"
    frameworks:
      PCI-DSS: "Req 6.1 — Identify vulnerabilities"
      SOC2: "CC7.1 — Detection of Changes"
      GDPR: "Art 32.1.d — Regular testing and evaluating"
      ISO27001: "A.12.6.1 — Management of technical vulnerabilities"

  network_segmentation:
    technical_control: "Microsegmentazione con NetworkPolicy deny-default"
    verification: "kubectl get networkpolicies --all-namespaces"
    frameworks:
      PCI-DSS: "Req 1.3 — Prohibit unauthorized traffic"
      SOC2: "CC6.6 — System boundaries"
      NIS2: "Art 21 — Network segmentation"
      ISO27001: "A.13.1.3 — Segregation in networks"

  data_residency:
    technical_control: "Restrizione regione di deployment a EU-only"
    verification: "aws ec2 describe-regions --query 'Regions[].RegionName'"
    frameworks:
      GDPR: "Art 44-49 — Transfers of personal data to third countries"
      NIS2: "Art 21 — Cybersecurity risk-management measures"
```

### Pipeline di Compliance Automatizzata

```yaml
# GitHub Actions: pipeline di compliance continua
name: Compliance Gate
on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Verifica settimanale il lunedi

jobs:
  infrastructure-compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Checkov IaC Compliance
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: terraform/
          framework: terraform
          check: >-
            CKV_AWS_18,CKV_AWS_19,CKV_AWS_21,CKV_AWS_145,
            CKV_AWS_17,CKV_AWS_41,CKV_AWS_23,CKV_AWS_24
          soft_fail: false

      - name: Prowler Cloud Compliance
        run: |
          pip install prowler
          prowler aws \
            --compliance cis_2.0_aws pci_3.2.1_aws gdpr_aws \
            --severity critical high \
            --output-formats json-ocsf html \
            --output-directory prowler-results/

      - name: Upload Compliance Report
        uses: actions/upload-artifact@v4
        with:
          name: compliance-report-${{ github.run_number }}
          path: prowler-results/
          retention-days: 365

  kubernetes-compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Kube-bench CIS Benchmark
        run: |
          kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
          kubectl wait --for=condition=complete job/kube-bench --timeout=300s
          kubectl logs job/kube-bench > kube-bench-results.txt

      - name: Polaris Best Practices
        run: |
          polaris audit --audit-path kubernetes/ \
            --format json \
            --output-file polaris-results.json \
            --set-exit-code-on-danger

      - name: Kubescape NSA/CISA Hardening
        run: |
          kubescape scan framework nsa,mitre \
            --format json \
            --output kubescape-results.json \
            --compliance-threshold 80
```

---

## 19. DevSecOps Pipeline Integration

### Architettura Completa della Pipeline DevSecOps

La pipeline DevSecOps integra controlli di sicurezza in ogni fase del ciclo di vita del software,
dalla scrittura del codice alla produzione. In ambienti moderni, il 45% delle violazioni
significative nel 2025 ha coinvolto qualche forma di compromissione della pipeline di build.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEVSECOPS PIPELINE                                │
│                                                                      │
│  Developer       Build          Test         Stage        Prod       │
│  ┌──────────┐   ┌──────────┐  ┌──────────┐  ┌─────────┐ ┌────────┐│
│  │ Pre-     │   │ SAST     │  │ DAST     │  │ Staging │ │ Runtime││
│  │ commit   │──▶│ SCA      │─▶│ IAST     │─▶│ Pen     │─▶│ Monit- ││
│  │ Hooks    │   │ License  │  │ API Sec  │  │ test    │ │ oring  ││
│  │          │   │ IaC Scan │  │ Fuzz     │  │ Chaos   │ │ SIEM   ││
│  └──────────┘   └──────────┘  └──────────┘  └─────────┘ └────────┘│
│       │              │              │             │           │      │
│       ▼              ▼              ▼             ▼           ▼      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Security Dashboard + Defect Tracking            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Pre-Commit Security Hooks

```yaml
# .pre-commit-config.yaml — security hooks completi
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.0
    hooks:
    - id: gitleaks
      name: Detect hardcoded secrets

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
    - id: detect-private-key
    - id: check-added-large-files
      args: ['--maxkb=500']

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']

  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
    - id: hadolint-docker
      name: Lint Dockerfiles

  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.96.0
    hooks:
    - id: terraform_tfsec
    - id: terraform_checkov
      args: ['--args=--check CKV_AWS_18 CKV_AWS_19']
```

### SAST e DAST nella Pipeline

```yaml
# Pipeline di sicurezza completa — GitLab CI
stages:
  - pre-build
  - build
  - test
  - security-scan
  - deploy-staging
  - security-test-dynamic
  - deploy-production

secret_detection:
  stage: pre-build
  image: zricethezav/gitleaks:latest
  script:
    - gitleaks detect --source=. --report-format=json --report-path=gitleaks-report.json
  artifacts:
    reports:
      secret_detection: gitleaks-report.json

sast_semgrep:
  stage: security-scan
  image: returntocorp/semgrep
  script:
    - semgrep ci
      --config=auto
      --config=p/owasp-top-ten
      --config=p/cwe-top-25
      --json --output=semgrep-results.json
      --severity ERROR
  artifacts:
    reports:
      sast: semgrep-results.json

sca_scan:
  stage: security-scan
  image: aquasec/trivy
  script:
    - trivy fs --scanners vuln --severity HIGH,CRITICAL
      --format json --output sca-results.json
      --exit-code 1 .
  artifacts:
    reports:
      dependency_scanning: sca-results.json

container_scan:
  stage: security-scan
  image: aquasec/trivy
  script:
    - trivy image --severity HIGH,CRITICAL
      --format json --output container-results.json
      --exit-code 1 $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  artifacts:
    reports:
      container_scanning: container-results.json

iac_scan:
  stage: security-scan
  image: bridgecrew/checkov
  script:
    - checkov -d terraform/
      --framework terraform
      --output json
      --output-file-path checkov-results/
      --hard-fail-on CRITICAL,HIGH

dast_zap:
  stage: security-test-dynamic
  image: ghcr.io/zaproxy/zaproxy:stable
  script:
    - zap-api-scan.py
      -t https://staging-api.example.com/openapi.json
      -f openapi
      -r dast-report.html
      -J dast-report.json
      -c zap-rules.conf
      -I  # Non fallire sulla scansione, solo report
  artifacts:
    reports:
      dast: dast-report.json
    paths:
      - dast-report.html
```

---

## 20. Incident Response per Ambienti Cloud e Container

### Sfide Specifiche della Forensics in Ambienti Container

La risposta agli incidenti in ambienti containerizzati presenta sfide uniche rispetto
agli ambienti tradizionali: i container sono effimeri (durata media di poche ore),
i filesystem sono stratificati e immutabili, i log sono distribuiti su molteplici nodi,
e le evidenze possono essere perse in pochi secondi con il rescheduling di un pod.

### Playbook di Incident Response per Kubernetes

```bash
#!/bin/bash
# Playbook automatizzato per incident response Kubernetes
# Fase 1: Preservazione delle evidenze
set -euo pipefail

INCIDENT_ID="INC-$(date +%Y%m%d-%H%M%S)"
EVIDENCE_DIR="/opt/ir-evidence/${INCIDENT_ID}"
NAMESPACE="${1:-production}"
POD_NAME="${2:-}"

mkdir -p "${EVIDENCE_DIR}"
echo "[${INCIDENT_ID}] Inizio raccolta evidenze — $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Snapshot dello stato del cluster
kubectl get pods -n "${NAMESPACE}" -o wide > "${EVIDENCE_DIR}/pods-state.txt"
kubectl get events -n "${NAMESPACE}" --sort-by='.lastTimestamp' > "${EVIDENCE_DIR}/events.txt"
kubectl get networkpolicies -n "${NAMESPACE}" -o yaml > "${EVIDENCE_DIR}/netpol.yaml"

if [ -n "${POD_NAME}" ]; then
    # Dettagli del pod sospetto
    kubectl describe pod "${POD_NAME}" -n "${NAMESPACE}" > "${EVIDENCE_DIR}/pod-describe.txt"
    kubectl get pod "${POD_NAME}" -n "${NAMESPACE}" -o yaml > "${EVIDENCE_DIR}/pod-manifest.yaml"
    kubectl logs "${POD_NAME}" -n "${NAMESPACE}" --all-containers --timestamps > "${EVIDENCE_DIR}/pod-logs.txt" 2>&1
    kubectl logs "${POD_NAME}" -n "${NAMESPACE}" --all-containers --previous --timestamps > "${EVIDENCE_DIR}/pod-logs-previous.txt" 2>&1 || true

    # Cattura del filesystem del container (senza alterare l'originale)
    NODE=$(kubectl get pod "${POD_NAME}" -n "${NAMESPACE}" -o jsonpath='{.spec.nodeName}')
    CONTAINER_ID=$(kubectl get pod "${POD_NAME}" -n "${NAMESPACE}" -o jsonpath='{.status.containerStatuses[0].containerID}' | sed 's|containerd://||')

    echo "[${INCIDENT_ID}] Pod su nodo: ${NODE}, Container ID: ${CONTAINER_ID}"

    # Fase 2: Isolamento del pod (NetworkPolicy deny-all)
    kubectl apply -f - << EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-${POD_NAME}
  namespace: ${NAMESPACE}
  labels:
    incident: "${INCIDENT_ID}"
spec:
  podSelector:
    matchLabels:
      $(kubectl get pod "${POD_NAME}" -n "${NAMESPACE}" -o jsonpath='{.metadata.labels}' | jq -r 'to_entries[] | "\(.key): \"\(.value)\""' | head -1)
  policyTypes:
  - Ingress
  - Egress
  ingress: []
  egress: []
EOF

    echo "[${INCIDENT_ID}] Pod ${POD_NAME} isolato dalla rete"

    # Fase 3: Cordon del nodo (impedire nuovi scheduling)
    kubectl cordon "${NODE}"
    echo "[${INCIDENT_ID}] Nodo ${NODE} in cordon"
fi

# Raccolta RBAC e service account
kubectl get rolebindings,clusterrolebindings -n "${NAMESPACE}" -o yaml > "${EVIDENCE_DIR}/rbac.yaml"
kubectl get serviceaccounts -n "${NAMESPACE}" -o yaml > "${EVIDENCE_DIR}/serviceaccounts.yaml"

# Audit log del cluster (se disponibile)
kubectl logs -n kube-system -l component=kube-apiserver --tail=10000 > "${EVIDENCE_DIR}/apiserver-logs.txt" 2>&1 || true

# Compressione e hash delle evidenze
tar czf "${EVIDENCE_DIR}.tar.gz" -C "$(dirname "${EVIDENCE_DIR}")" "$(basename "${EVIDENCE_DIR}")"
sha256sum "${EVIDENCE_DIR}.tar.gz" > "${EVIDENCE_DIR}.tar.gz.sha256"

echo "[${INCIDENT_ID}] Evidenze salvate in: ${EVIDENCE_DIR}.tar.gz"
echo "[${INCIDENT_ID}] SHA256: $(cat "${EVIDENCE_DIR}.tar.gz.sha256")"
```

### Cloud Forensics — Preservazione delle Evidenze

```bash
# AWS: snapshot forense di un'istanza EC2 compromessa
INSTANCE_ID="i-0abc123def456"
INCIDENT_ID="INC-20260524-142300"

# Snapshot di tutti i volumi EBS
for VOLUME_ID in $(aws ec2 describe-instances \
    --instance-ids "${INSTANCE_ID}" \
    --query 'Reservations[].Instances[].BlockDeviceMappings[].Ebs.VolumeId' \
    --output text); do

    aws ec2 create-snapshot \
        --volume-id "${VOLUME_ID}" \
        --description "Forensic snapshot - ${INCIDENT_ID}" \
        --tag-specifications "ResourceType=snapshot,Tags=[{Key=incident,Value=${INCIDENT_ID}},{Key=purpose,Value=forensics}]"

    echo "Snapshot creato per volume ${VOLUME_ID}"
done

# Cattura del traffico di rete con VPC Flow Logs
aws ec2 create-flow-logs \
    --resource-type Instance \
    --resource-ids "${INSTANCE_ID}" \
    --traffic-type ALL \
    --log-destination-type s3 \
    --log-destination "arn:aws:s3:::forensics-bucket/${INCIDENT_ID}/flow-logs/" \
    --max-aggregation-interval 60

# Isolamento dell'istanza: rimozione da tutti i security group
# e assegnazione di un SG che blocca tutto
ISOLATION_SG=$(aws ec2 create-security-group \
    --group-name "isolation-${INCIDENT_ID}" \
    --description "Isolation SG for incident ${INCIDENT_ID}" \
    --query 'GroupId' --output text)

# Nessuna regola in ingresso o uscita = isolamento totale
aws ec2 modify-instance-attribute \
    --instance-id "${INSTANCE_ID}" \
    --groups "${ISOLATION_SG}"

echo "Istanza ${INSTANCE_ID} isolata con SG ${ISOLATION_SG}"

# Cattura della memoria RAM con SSM (se disponibile)
aws ssm send-command \
    --instance-ids "${INSTANCE_ID}" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["dd if=/proc/kcore of=/tmp/memdump.raw bs=1M count=4096 2>/dev/null; aws s3 cp /tmp/memdump.raw s3://forensics-bucket/'${INCIDENT_ID}'/memory/"]'
```

---

## 21. Threat Modeling per Sistemi Distribuiti

### STRIDE Applicato ai Microservizi

Nei sistemi distribuiti, il numero di trust boundary, flussi di dati e canali di comunicazione
aumenta esponenzialmente rispetto alle architetture monolitiche. Ogni canale di comunicazione
tra microservizi rappresenta un potenziale vettore di attacco.

L'applicazione di STRIDE ai microservizi richiede l'analisi sistematica di ogni componente:
API gateway, service mesh, database condivisi, code di messaggi, service discovery
e pipeline CI/CD.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  THREAT MODEL — MICROSERVIZI                            │
│                                                                          │
│  EXTERNAL            TRUST BOUNDARY 1              TRUST BOUNDARY 2     │
│  ┌──────┐         ┌───────────────┐             ┌──────────────────┐   │
│  │      │  HTTPS  │  ┌─────────┐  │   mTLS     │  ┌────────────┐  │   │
│  │ User │────────▶│  │ API GW  │──│────────────▶│  │ Service A  │  │   │
│  │      │         │  │ (AuthN) │  │             │  │            │  │   │
│  └──────┘         │  └────┬────┘  │             │  └─────┬──────┘  │   │
│                   │       │       │             │        │         │   │
│  S: Token theft   │  T: Param     │  S: Service │  I: Data leak   │   │
│  T: Request tamper│     tampering │     spoofing│  D: DB DoS      │   │
│  R: No audit trail│  I: Error     │  R: No log  │  E: Container   │   │
│  I: Token leak    │     info leak │  I: Plain   │     escape      │   │
│  D: Rate limit    │  D: API abuse │     text    │                 │   │
│  E: Privilege esc │  E: Authz     │  D: Network │                 │   │
│                   │     bypass    │     flood   │                 │   │
│                   └───────────────┘             └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Threat Modeling Template per Piattaforme Cloud-Native

```yaml
# Template di threat modeling per piattaforma distribuita
threat_model:
  system: "E-Commerce Platform v3"
  date: "2026-05-24"
  authors: ["security-team"]

  assets:
    - name: "Dati PII clienti"
      classification: "Restricted"
      location: "PostgreSQL (encrypted at rest)"
    - name: "Credenziali di pagamento"
      classification: "PCI-DSS scope"
      location: "Payment gateway (tokenized)"
    - name: "Session tokens"
      classification: "Confidential"
      location: "Redis cluster"
    - name: "API keys terze parti"
      classification: "Secret"
      location: "HashiCorp Vault"

  components:
    - name: "API Gateway"
      type: "Kong/Envoy"
      trust_boundary: "external-to-dmz"
      threats:
        - category: "Spoofing"
          threat: "Utilizzo di token JWT rubati per impersonare utenti"
          likelihood: "High"
          impact: "Critical"
          mitigation: "Token rotation breve (15min), binding a device fingerprint, JTI blacklist"
          residual_risk: "Low"
        - category: "Denial of Service"
          threat: "API abuse con richieste massive"
          likelihood: "High"
          impact: "High"
          mitigation: "Rate limiting per-user, WAF, CDN caching, autoscaling"
          residual_risk: "Medium"

    - name: "Inter-Service Communication"
      type: "gRPC over Istio mTLS"
      trust_boundary: "service-to-service"
      threats:
        - category: "Tampering"
          threat: "Man-in-the-middle tra servizi"
          likelihood: "Low"
          impact: "Critical"
          mitigation: "mTLS strict mode via Istio, SPIFFE identity verification"
          residual_risk: "Very Low"
        - category: "Information Disclosure"
          threat: "Intercettazione di dati in transito"
          likelihood: "Low"
          impact: "High"
          mitigation: "mTLS con cipher suite forti, no fallback a plaintext"
          residual_risk: "Very Low"

    - name: "Container Runtime"
      type: "containerd con Falco"
      trust_boundary: "host-to-container"
      threats:
        - category: "Elevation of Privilege"
          threat: "Container escape tramite vulnerabilita kernel"
          likelihood: "Low"
          impact: "Critical"
          mitigation: "Pod Security Standards restricted, seccomp, AppArmor, gVisor per workload untrusted"
          residual_risk: "Low"
        - category: "Tampering"
          threat: "Modifica del filesystem del container"
          likelihood: "Medium"
          impact: "High"
          mitigation: "readOnlyRootFilesystem, Falco monitoring, image signing con cosign"
          residual_risk: "Low"

  risk_matrix:
    critical: 2
    high: 3
    medium: 5
    low: 8
    accepted: 2
```

### DREAD Scoring Quantitativo

```yaml
# Scoring DREAD per le minacce identificate
dread_scoring:
  - threat: "SQL injection via API non sanitizzata"
    damage: 9        # Accesso completo al database
    reproducibility: 8  # Facilmente riproducibile con sqlmap
    exploitability: 7   # Richiede conoscenze moderate
    affected_users: 10  # Tutti gli utenti della piattaforma
    discoverability: 6  # Rilevabile con scanning automatico
    total: 8.0          # Media: (9+8+7+10+6)/5 = 8.0 → CRITICAL
    action: "BLOCK — Correzione immediata richiesta"

  - threat: "Brute force su endpoint di login"
    damage: 6
    reproducibility: 10
    exploitability: 9
    affected_users: 3
    discoverability: 10
    total: 7.6          # HIGH
    action: "WARN — Rate limiting e account lockout obbligatori"

  - threat: "Information disclosure via error stack trace"
    damage: 4
    reproducibility: 9
    exploitability: 3
    affected_users: 5
    discoverability: 8
    total: 5.8          # MEDIUM
    action: "INFO — Sanitizzare messaggi di errore in produzione"
```

---

## 22. Security Monitoring e SIEM Integration

### Architettura di Security Monitoring Centralizzata

Un sistema di security monitoring efficace per piattaforme distribuite richiede
la correlazione di eventi provenienti da molteplici fonti: cluster Kubernetes,
servizi cloud, applicazioni, rete e endpoint.

```
┌──────────────────────────────────────────────────────────────────────┐
│                SECURITY MONITORING ARCHITECTURE                       │
│                                                                       │
│  Sources                  Collection        Analysis       Response   │
│  ┌─────────────┐         ┌──────────┐     ┌──────────┐  ┌────────┐  │
│  │ K8s Audit   │────────▶│          │     │          │  │        │  │
│  │ Falco       │────────▶│  Fluent- │────▶│  SIEM    │─▶│ SOAR   │  │
│  │ Cloud Logs  │────────▶│  bit /   │     │  (ELK /  │  │ (auto  │  │
│  │ WAF Logs    │────────▶│  Vector  │     │  Wazuh / │  │  resp) │  │
│  │ App Logs    │────────▶│          │     │  Splunk) │  │        │  │
│  │ Flow Logs   │────────▶│          │     │          │  │        │  │
│  └─────────────┘         └──────────┘     └─────┬────┘  └───┬────┘  │
│                                                  │           │       │
│                                           ┌──────▼───────────▼────┐  │
│                                           │   Dashboard / Alert   │  │
│                                           │   (Grafana / PagerD.) │  │
│                                           └───────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### Integrazione Falco con SIEM

```yaml
# Falco Sidekick: routing degli alert verso SIEM e strumenti di risposta
# falcosidekick-values.yaml per Helm
config:
  # Output verso Elasticsearch (ELK Stack)
  elasticsearch:
    hostport: "https://elasticsearch.security:9200"
    index: "falco-alerts"
    type: "_doc"
    minimumpriority: "warning"
    mutualtls: true
    checkcert: true
    username: "falco_writer"
    password: ""  # Da secret K8s

  # Output verso Slack per notifiche immediate
  slack:
    webhookurl: ""  # Da secret K8s
    channel: "#security-alerts"
    minimumpriority: "error"
    messageformat: |
      *Falco Alert:* {{ .Output }}
      *Priority:* {{ .Priority }}
      *Rule:* {{ .Rule }}
      *Time:* {{ .Time }}
      *Source:* {{ .Source }}

  # Output verso PagerDuty per alert critici
  pagerduty:
    routingkey: ""  # Da secret K8s
    minimumpriority: "critical"

  # Output verso Loki per correlazione con metriche Grafana
  loki:
    hostport: "http://loki.monitoring:3100"
    minimumpriority: "notice"
    tenant: "security"

  # Prometheus metrics per alerting basato su soglie
  prometheus:
    extralabels: "source:falco"
```

### Detection Rules per Ambienti Cloud-Native

```yaml
# Sigma rules convertite per il SIEM — rilevamento attacchi cloud-native

# Rilevamento accesso anomalo all'API Kubernetes
title: Suspicious Kubernetes API Access
status: stable
level: high
logsource:
  product: kubernetes
  service: audit
detection:
  selection_verb:
    verb:
      - create
      - patch
      - delete
  selection_resource:
    objectRef.resource:
      - secrets
      - clusterroles
      - clusterrolebindings
  selection_user:
    user.username|endswith:
      - '@'
  filter_system:
    user.username|startswith:
      - 'system:'
  condition: (selection_verb and selection_resource and selection_user) and not filter_system
---
# Rilevamento container escape tentativo
title: Container Escape Attempt Detection
status: stable
level: critical
logsource:
  product: falco
detection:
  selection:
    rule:
      - "Terminal shell in container"
      - "Contact K8S API Server From Container"
      - "Mount host filesystem"
      - "Privileged container started"
      - "Write below /etc"
  condition: selection
---
# Rilevamento esfiltrazione dati via DNS tunneling
title: DNS Tunneling Detection
status: stable
level: high
logsource:
  product: dns
detection:
  selection:
    query|re: '^[a-z0-9]{30,}\.'
  filter_known:
    query|endswith:
      - '.googleapis.com'
      - '.amazonaws.com'
      - '.azure.com'
  condition: selection and not filter_known
  timeframe: 5m
  count:
    field: query
    condition: '>= 50'
```

---

## 23. Infrastructure Security Hardening

### Hardening Avanzato per Host Container

```bash
# CIS Benchmark per host che eseguono container
# Verifica automatizzata con InSpec

# 1. Partizione /var/lib/docker o /var/lib/containerd separata
mount | grep -E "(docker|containerd)"
# Deve essere su partizione dedicata con opzioni nosuid,nodev

# 2. Configurazione containerd sicura
cat > /etc/containerd/config.toml << 'EOF'
version = 2

[plugins."io.containerd.grpc.v1.cri"]
  sandbox_image = "registry.k8s.io/pause:3.10"
  max_container_log_line_size = 16384

  [plugins."io.containerd.grpc.v1.cri".containerd]
    default_runtime_name = "runc"

    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
      runtime_type = "io.containerd.runc.v2"

      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
        SystemdCgroup = true
        # Non permettere binari con setuid nei container
        NoNewPrivileges = true

  [plugins."io.containerd.grpc.v1.cri".registry]
    # Richiedere sempre HTTPS per i registry
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
        endpoint = ["https://registry-1.docker.io"]
EOF

# 3. AppArmor profile per container
cat > /etc/apparmor.d/container-restricted << 'EOF'
#include <tunables/global>

profile container-restricted flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Impedire mount operations
  deny mount,

  # Impedire accesso a /proc sensibili
  deny /proc/*/mem rwklx,
  deny /proc/kcore rwklx,
  deny /proc/sysrq-trigger rwklx,

  # Impedire accesso a device files
  deny /dev/mem rwklx,
  deny /dev/kmem rwklx,

  # Impedire modifica a file di sistema
  deny /etc/shadow rwklx,
  deny /etc/sudoers rwklx,

  # Consentire operazioni standard
  /usr/bin/** ix,
  /app/** rix,
  /tmp/** rw,
}
EOF

apparmor_parser -r /etc/apparmor.d/container-restricted

# 4. Kernel hardening per container host
cat > /etc/sysctl.d/99-container-hardening.conf << 'EOF'
# Protezione contro container escape
kernel.unprivileged_userns_clone = 0
kernel.unprivileged_bpf_disabled = 1
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.perf_event_paranoid = 3

# Protezione rete
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Protezione memoria
vm.mmap_min_addr = 65536
kernel.randomize_va_space = 2
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.protected_fifos = 2
fs.protected_regular = 2
EOF

sysctl --system
```

### Hardening delle Pipeline CI/CD

```yaml
# Sicurezza della pipeline CI/CD stessa
# Principi: immutabilita dei build, isolamento, firma degli artefatti

# GitHub Actions: runner self-hosted hardened
name: Secure Build Pipeline
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: self-hosted
    permissions:
      contents: read
      packages: write
      id-token: write
    env:
      # Nessun secret in variabili d'ambiente — usare OIDC
      COSIGN_EXPERIMENTAL: "1"
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Per verifica commit signatures

      # Verifica che i commit recenti siano firmati
      - name: Verify Commit Signatures
        run: |
          UNSIGNED=$(git log --format='%H %G?' origin/main..HEAD | grep -c ' N$' || true)
          if [ "$UNSIGNED" -gt 0 ]; then
            echo "ERRORE: Trovati ${UNSIGNED} commit non firmati"
            exit 1
          fi

      # Build in ambiente isolato (no network durante build)
      - name: Build Container Image
        run: |
          docker build \
            --network=none \
            --no-cache \
            --label "org.opencontainers.image.source=${{ github.server_url }}/${{ github.repository }}" \
            --label "org.opencontainers.image.revision=${{ github.sha }}" \
            -t myregistry.io/myapp:${{ github.sha }} .

      # Scansione vulnerabilita prima del push
      - name: Security Scan
        run: |
          trivy image --exit-code 1 --severity CRITICAL \
            myregistry.io/myapp:${{ github.sha }}

      # Firma dell'immagine con cosign (keyless via OIDC)
      - name: Sign Container Image
        run: |
          cosign sign --yes myregistry.io/myapp:${{ github.sha }}

      # Generazione e allegamento SBOM
      - name: Generate and Attach SBOM
        run: |
          syft myregistry.io/myapp:${{ github.sha }} -o cyclonedx-json > sbom.json
          cosign attach sbom --sbom sbom.json myregistry.io/myapp:${{ github.sha }}
```

---

## Esercizi

### Esercizio 1 — CIS Benchmark Hardening

Scaricare il CIS Benchmark per Ubuntu 24.04 o Amazon Linux 2023. Applicare almeno 15 controlli di hardening su una VM di test (SSH config, firewall, auditd, permessi filesystem, disabilitazione servizi non necessari). Verificare la conformita con `lynis audit system` e documentare i risultati.

### Esercizio 2 — Vulnerability Scanning Pipeline

Configurare una pipeline CI/CD che esegua in sequenza: `gitleaks` per secret detection, `trivy` per container image scanning, `tfsec` per IaC scanning e `checkov` per policy compliance. Introdurre intenzionalmente vulnerabilita in un Dockerfile e un file Terraform e verificare che la pipeline li blocchi.

### Esercizio 3 — Zero-Trust Network con mTLS

Configurare mTLS tra due microservizi usando cert-manager su Kubernetes. Generare certificati client e server, configurare il service mesh (Istio o Linkerd) per imporre mTLS strict mode. Verificare che la comunicazione senza certificato valido venga rifiutata.

### Esercizio 4 — Incident Response Tabletop Exercise

Progettare e condurre un tabletop exercise per uno scenario di data breach. Definire il playbook con fasi di detection, containment, eradication, recovery e post-incident. Coinvolgere almeno 3 ruoli (security, ops, management). Documentare le lessons learned e aggiornare il runbook.

### Esercizio 5 — WAF e DDoS Mitigation

Configurare un Web Application Firewall (ModSecurity o AWS WAF) davanti a un'applicazione web. Creare regole personalizzate per bloccare SQL injection, XSS e rate limiting. Simulare attacchi con strumenti come `nikto` o `sqlmap` e verificare che il WAF li rilevi e blocchi correttamente.

---

## Letture e Riferimenti

### Documentazione ufficiale

- CIS Benchmarks — <https://www.cisecurity.org/cis-benchmarks> (consultato: 2026-05-24)
- OWASP Top 10 2025 — <https://owasp.org/www-project-top-ten/> (consultato: 2026-05-24)
- NIST Cybersecurity Framework 2.0 — <https://www.nist.gov/cyberframework> (consultato: 2026-05-24)
- Trivy Documentation — <https://aquasecurity.github.io/trivy/> (consultato: 2026-05-24)
- Falco Documentation — <https://falco.org/docs/> (consultato: 2026-05-24)
- Kubernetes Security Best Practices — <https://kubernetes.io/docs/concepts/security/> (consultato: 2026-05-24)

### Libri consigliati

- Kim G., Humble J., Debois P., *The DevOps Handbook*, IT Revolution Press, 2021
- Rice L., *Container Security*, O'Reilly, 2020
- Madakor G., *Kubernetes Security and Observability*, O'Reilly, 2022

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione con Sicurezza delle Piattaforme |
|--------|--------|-------------------------------------------|
| [05](05-kubernetes.md) | Kubernetes | Pod Security Standards, RBAC, NetworkPolicy, admission controllers |
| [06](06-docker-avanzato.md) | Docker Avanzato | Image scanning, rootless containers, seccomp/AppArmor profiles |
| [07](07-ci-cd.md) | CI/CD | Security gates nella pipeline, SAST/DAST, supply chain security |
| [09](09-service-mesh.md) | Service Mesh | mTLS automatico, authorization policy, traffic encryption |
| [14](14-compliance.md) | Compliance e Normative | Mapping controlli tecnici a requisiti normativi (GDPR, NIS2, SOC 2) |
| [20](20-supply-chain-slsa-cosign.md) | Supply Chain SLSA e Cosign | Firma immagini, SBOM, provenance, integrita della supply chain |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Defense in depth** | Strategia di sicurezza a layer multipli dove ogni livello fornisce protezione indipendente |
| **Zero-trust** | Modello di sicurezza che non concede fiducia implicita basata sulla posizione di rete |
| **CIS Benchmark** | Standard di configurazione sicura pubblicato dal Center for Internet Security per OS, DB e cloud |
| **Hardening** | Processo di riduzione della superficie di attacco eliminando servizi, porte e accessi non necessari |
| **mTLS (mutual TLS)** | Autenticazione TLS bidirezionale in cui sia client che server presentano un certificato |
| **WAF (Web Application Firewall)** | Firewall applicativo che filtra traffico HTTP/HTTPS basandosi su regole contro attacchi noti |
| **SAST (Static Application Security Testing)** | Analisi del codice sorgente per vulnerabilita senza esecuzione del programma |
| **DAST (Dynamic Application Security Testing)** | Test di sicurezza eseguito su un'applicazione in esecuzione per trovare vulnerabilita runtime |
| **Microsegmentazione** | Suddivisione della rete in segmenti granulari con policy di accesso indipendenti per ogni segmento |
| **Incident response** | Processo strutturato per rilevare, contenere, eliminare e recuperare da un incidente di sicurezza |
| **Playbook** | Documento operativo con procedure dettagliate step-by-step per rispondere a uno specifico tipo di incidente |
| **CVSS (Common Vulnerability Scoring System)** | Sistema standard per valutare la gravita delle vulnerabilita su una scala 0-10 |
| **Threat modeling** | Processo sistematico per identificare minacce, vulnerabilita e contromisure in un sistema |
| **SBOM (Software Bill of Materials)** | Inventario formale dei componenti software e delle relative dipendenze di un'applicazione |
