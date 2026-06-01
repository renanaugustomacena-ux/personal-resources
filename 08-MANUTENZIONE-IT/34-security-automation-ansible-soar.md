# Security Automation con Ansible, SOAR e Infrastructure as Code Security

> **Modulo:** Operations IT · Modulo 34
> **Prerequisiti:** Moduli 05, 07, 23; Linux sysadmin; YAML; basic Python; networking fundamentals.
> **Obiettivi:** automatizzare operazioni di sicurezza end-to-end; hardening con Ansible; orchestrare incident response via SOAR; proteggere IaC pipeline; integrare threat intelligence; compliance-as-code.
> **Tempo:** 90 min teoria · lab 480 min · **Livello:** advanced · **Aggiornamento:** 2026-05-07

---

## 1. Fondamenti Security Automation

### Why Automate Security Operations

Manual security operations do not scale. A SOC receiving 11,000 alerts/day cannot triage each one with a human analyst. Automation addresses four fundamental problems:

**Speed.** Mean-time-to-respond (MTTR) for automated containment is measured in seconds, not hours. When a credential compromise alert fires, an automated playbook can disable the account, revoke tokens, and isolate the host before a human even reads the alert.

**Consistency.** Humans forget steps. A hardening checklist with 147 items executed by 5 admins produces 5 different results. An Ansible playbook produces one result, every time, on every host.

**Scalability.** An environment growing from 50 to 5000 nodes does not require 100x more security engineers — it requires automation that scales horizontally. The same playbook hardens one host or ten thousand.

**Human Error Reduction.** Typos in firewall rules, missed patches, inconsistent configurations — these are the primary attack surface in most enterprises. Automation eliminates this class of vulnerability entirely.

### Security Automation Maturity Model

Organizations progress through four stages:

```
Level 0 — MANUAL
├── Ad-hoc scripts, copy-paste commands
├── No version control on security configs
├── Reactive only — respond after incident
└── Knowledge lives in individual heads

Level 1 — SCRIPTED
├── Bash/PowerShell scripts for common tasks
├── Scripts in version control
├── Some scheduled execution (cron)
└── Documentation exists but may be stale

Level 2 — ORCHESTRATED
├── Configuration management (Ansible/Puppet/Chef)
├── CI/CD pipelines include security gates
├── SOAR platform handles common incidents
├── Centralized secrets management
├── Infrastructure as Code for all deployments
└── Metrics on automation coverage

Level 3 — AUTONOMOUS
├── Self-healing infrastructure
├── Automated threat hunting
├── ML-driven alert triage and prioritization
├── Closed-loop remediation (detect → contain → fix → verify)
├── Continuous compliance with zero manual intervention
└── Human-in-the-loop only for novel threats and policy decisions
```

Most organizations live between Level 1 and Level 2. The goal of this module is to build competence at Level 2 with architectural awareness of Level 3.

### Security Automation Use Cases

| Use Case | Manual MTTR | Automated MTTR | Impact |
|----------|-------------|----------------|--------|
| Vulnerability remediation | 60 days | 4 hours | Reduces attack window by 99.7% |
| Compliance enforcement | Quarterly audit | Continuous | Eliminates drift between audits |
| Incident response (phishing) | 45 min | 90 sec | Prevents lateral movement |
| Threat intel operationalization | Never (stays in PDF) | Real-time blocking | Converts intel into defense |
| Credential rotation | Manual/never | Scheduled + on-compromise | Reduces credential exposure |
| Certificate renewal | Firefighting on expiry | Auto-renew at 30 days | Zero downtime from expired certs |

### Risk Considerations

Automation is not without risk:

- **Blast radius amplification:** A misconfigured playbook can brick 5000 hosts simultaneously. Always use canary deployments and `--limit` in production.
- **Over-automation:** Automatically blocking an IP without context can disrupt legitimate business. Human-in-the-loop gates matter for high-impact actions.
- **Secret sprawl:** Automation requires credentials. Those credentials become high-value targets. Vault integration is mandatory, not optional.
- **Complexity debt:** 500 playbooks with no testing, no documentation, and no ownership become a liability, not an asset.

---

## 2. Ansible per Security Operations

### Ansible Security Automation Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CONTROL NODE                          │
│  ┌─────────┐  ┌──────────┐  ┌────────────────────┐    │
│  │ Ansible │  │ Ansible  │  │  Ansible Vault     │    │
│  │ Engine  │  │ Galaxy   │  │  (secrets encrypt)  │    │
│  └────┬────┘  └──────────┘  └────────────────────┘    │
│       │                                                 │
│  ┌────┴─────────────────────────────────────────┐      │
│  │  Inventory (static/dynamic)                   │      │
│  │  ├── production/                              │      │
│  │  │   ├── hosts.yml                            │      │
│  │  │   ├── group_vars/                          │      │
│  │  │   └── host_vars/                           │      │
│  │  └── staging/                                 │      │
│  └──────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────┘
                         │ SSH / WinRM / NETCONF / API
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────┴────┐    ┌─────┴────┐   ┌─────┴──────┐
    │ Linux   │    │ Windows  │   │ Network    │
    │ Managed │    │ Managed  │   │ Devices    │
    │ Nodes   │    │ Nodes    │   │            │
    └─────────┘    └──────────┘   └────────────┘
```

### Security-Specific Ansible Collections

```yaml
# requirements.yml — security automation dependencies
---
collections:
  - name: ansible.posix
    version: ">=1.5.0"
  - name: community.general
    version: ">=7.0.0"
  - name: ansible.netcommon
    version: ">=5.0.0"
  - name: community.crypto
    version: ">=2.0.0"
  - name: ansible.windows
    version: ">=2.0.0"
  - name: community.windows
    version: ">=2.0.0"
  - name: cisco.ios
    version: ">=5.0.0"
  - name: junipernetworks.junos
    version: ">=5.0.0"
  - name: paloaltonetworks.panos
    version: ">=2.0.0"
  - name: community.docker
    version: ">=3.0.0"
  - name: kubernetes.core
    version: ">=2.0.0"

roles:
  - name: devsec.hardening
    version: ">=9.0.0"
  - name: geerlingguy.security
    version: ">=2.0.0"
```

Install:

```bash
ansible-galaxy collection install -r requirements.yml --force
ansible-galaxy role install -r requirements.yml --force
```

### Hardening Playbooks — CIS Benchmarks as Ansible Roles

The `ansible-lockdown` project provides CIS benchmark implementations as Ansible roles. The approach:

1. Each CIS control maps to one or more Ansible tasks
2. Controls are toggled via variables (enable/disable per environment)
3. Idempotent — safe to run repeatedly
4. Audit mode available (report without remediating)

```yaml
# playbooks/cis-hardening.yml
---
- name: Apply CIS Level 1 hardening to Ubuntu 22.04
  hosts: linux_servers
  become: true
  vars:
    cis_level: 1
    cis_ubuntu2204_rule_1_1_1_1: true   # Disable cramfs
    cis_ubuntu2204_rule_1_1_1_2: true   # Disable freevxfs
    cis_ubuntu2204_rule_5_2_1: true     # SSH hardening
    cis_ubuntu2204_rule_5_3_1: true     # PAM config
    cis_ubuntu2204_audit_only: false    # Set true for dry-run

  roles:
    - role: ansible-lockdown.cis_ubuntu2204
      tags: [cis, hardening]

  post_tasks:
    - name: Generate compliance report
      ansible.builtin.template:
        src: compliance-report.j2
        dest: "/var/log/compliance/cis-{{ ansible_date_time.iso8601_basic_short }}.json"
        mode: '0640'
      tags: [report]
```

### Compliance-as-Code — OpenSCAP + Ansible

```yaml
# playbooks/openscap-scan.yml
---
- name: Run OpenSCAP compliance scan
  hosts: linux_servers
  become: true
  vars:
    scap_profile: xccdf_org.ssgproject.content_profile_cis_level1_server
    scap_content: /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
    report_dir: /var/log/openscap

  tasks:
    - name: Install OpenSCAP scanner
      ansible.builtin.apt:
        name:
          - libopenscap8
          - openscap-scanner
          - ssg-base
          - ssg-debderived
        state: present
        update_cache: true

    - name: Ensure report directory exists
      ansible.builtin.file:
        path: "{{ report_dir }}"
        state: directory
        mode: '0750'
        owner: root
        group: adm

    - name: Run SCAP evaluation
      ansible.builtin.command:
        cmd: >
          oscap xccdf eval
          --profile {{ scap_profile }}
          --results {{ report_dir }}/results-{{ ansible_date_time.iso8601_basic_short }}.xml
          --report {{ report_dir }}/report-{{ ansible_date_time.iso8601_basic_short }}.html
          {{ scap_content }}
      register: scap_result
      failed_when: scap_result.rc not in [0, 2]
      changed_when: false

    - name: Parse compliance score
      ansible.builtin.shell: |
        set -o pipefail
        oscap xccdf eval --profile {{ scap_profile }} {{ scap_content }} 2>&1 | \
          grep -oP 'Score: \K[0-9.]+'
      register: compliance_score
      changed_when: false

    - name: Fail if compliance below threshold
      ansible.builtin.fail:
        msg: "Compliance score {{ compliance_score.stdout }}% below 85% threshold"
      when: compliance_score.stdout | float < 85.0
```

### Automated Patching Playbook

```yaml
# playbooks/security-patching.yml
---
- name: Automated security patching with pre/post validation
  hosts: patch_group_{{ patch_wave }}
  become: true
  serial: "25%"    # Rolling update — 25% at a time
  max_fail_percentage: 10
  vars:
    reboot_timeout: 600
    health_check_url: "http://{{ inventory_hostname }}:8080/health"
    pre_snapshot: true

  pre_tasks:
    - name: Pre-patch health check
      ansible.builtin.uri:
        url: "{{ health_check_url }}"
        status_code: 200
        timeout: 10
      register: pre_health
      failed_when: pre_health.status != 200

    - name: Create pre-patch snapshot (if VM)
      ansible.builtin.command:
        cmd: "virsh snapshot-create-as {{ inventory_hostname }} pre-patch-{{ ansible_date_time.epoch }}"
      delegate_to: "{{ hypervisor_host }}"
      when: pre_snapshot and virtualization_type == 'kvm'

  tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: 0

    - name: Install security updates only
      ansible.builtin.apt:
        upgrade: safe
        default_release: "{{ ansible_distribution_release }}-security"
      register: patch_result

    - name: Check if reboot required
      ansible.builtin.stat:
        path: /var/run/reboot-required
      register: reboot_needed

    - name: Reboot if required
      ansible.builtin.reboot:
        msg: "Security patch reboot"
        reboot_timeout: "{{ reboot_timeout }}"
        post_reboot_delay: 30
      when: reboot_needed.stat.exists

  post_tasks:
    - name: Post-patch health check
      ansible.builtin.uri:
        url: "{{ health_check_url }}"
        status_code: 200
        timeout: 30
      register: post_health
      retries: 5
      delay: 10
      until: post_health.status == 200

    - name: Verify no critical services failed
      ansible.builtin.systemd:
        name: "{{ item }}"
        state: started
      loop:
        - sshd
        - auditd
        - wazuh-agent
      register: service_check

    - name: Log patch results
      ansible.builtin.lineinfile:
        path: /var/log/patch-history.log
        line: "{{ ansible_date_time.iso8601 }} | {{ patch_result.changed | ternary('PATCHED', 'NO_UPDATES') }} | {{ inventory_hostname }}"
        create: true
        mode: '0640'
```

### Credential Rotation Automation

```yaml
# playbooks/credential-rotation.yml
---
- name: Rotate service account credentials
  hosts: localhost
  gather_facts: false
  vars:
    vault_addr: "https://vault.internal.corp:8200"
    rotation_targets:
      - name: db_app_user
        backend: database/creds/app-role
        inject_targets: ["app_servers"]
      - name: rabbitmq_producer
        backend: rabbitmq/creds/producer
        inject_targets: ["queue_workers"]

  tasks:
    - name: Generate new credentials from Vault
      community.hashi_vault.vault_read:
        url: "{{ vault_addr }}"
        path: "{{ item.backend }}"
        auth_method: approle
        role_id: "{{ lookup('env', 'VAULT_ROLE_ID') }}"
        secret_id: "{{ lookup('env', 'VAULT_SECRET_ID') }}"
      loop: "{{ rotation_targets }}"
      register: new_creds
      no_log: true

    - name: Deploy new credentials to targets
      ansible.builtin.include_tasks: deploy-credential.yml
      loop: "{{ rotation_targets }}"
      loop_control:
        index_var: idx
      vars:
        cred_data: "{{ new_creds.results[idx] }}"
        target_group: "{{ item.inject_targets }}"

    - name: Verify services using new credentials
      ansible.builtin.uri:
        url: "http://{{ item }}:8080/health"
        status_code: 200
      loop: "{{ groups['app_servers'] }}"
      retries: 3
      delay: 5

    - name: Revoke old lease if rotation successful
      community.hashi_vault.vault_write:
        url: "{{ vault_addr }}"
        path: "sys/leases/revoke"
        data:
          lease_id: "{{ old_lease_id }}"
        auth_method: approle
        role_id: "{{ lookup('env', 'VAULT_ROLE_ID') }}"
        secret_id: "{{ lookup('env', 'VAULT_SECRET_ID') }}"
      when: old_lease_id is defined
      no_log: true
```

---

## 3. Ansible Hardening Playbooks in Depth

### Linux Hardening — Complete Playbook

```yaml
# roles/linux-hardening/tasks/main.yml
---
# === SSH HARDENING ===
- name: SSH - Deploy hardened sshd_config
  ansible.builtin.template:
    src: sshd_config.j2
    dest: /etc/ssh/sshd_config
    owner: root
    group: root
    mode: '0600'
    validate: '/usr/sbin/sshd -t -f %s'
  notify: restart sshd
  tags: [ssh]

- name: SSH - Disable root login
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^#?PermitRootLogin'
    line: 'PermitRootLogin no'
    validate: '/usr/sbin/sshd -t -f %s'
  notify: restart sshd
  tags: [ssh]

- name: SSH - Enforce key-only authentication
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: "{{ item.regexp }}"
    line: "{{ item.line }}"
  loop:
    - { regexp: '^#?PasswordAuthentication', line: 'PasswordAuthentication no' }
    - { regexp: '^#?ChallengeResponseAuthentication', line: 'ChallengeResponseAuthentication no' }
    - { regexp: '^#?PubkeyAuthentication', line: 'PubkeyAuthentication yes' }
    - { regexp: '^#?MaxAuthTries', line: 'MaxAuthTries 3' }
    - { regexp: '^#?ClientAliveInterval', line: 'ClientAliveInterval 300' }
    - { regexp: '^#?ClientAliveCountMax', line: 'ClientAliveCountMax 2' }
    - { regexp: '^#?X11Forwarding', line: 'X11Forwarding no' }
    - { regexp: '^#?AllowAgentForwarding', line: 'AllowAgentForwarding no' }
    - { regexp: '^#?AllowTcpForwarding', line: 'AllowTcpForwarding no' }
  notify: restart sshd
  tags: [ssh]

# === PAM HARDENING ===
- name: PAM - Configure password complexity
  ansible.builtin.lineinfile:
    path: /etc/security/pwquality.conf
    regexp: "{{ item.regexp }}"
    line: "{{ item.line }}"
  loop:
    - { regexp: '^#?minlen', line: 'minlen = 14' }
    - { regexp: '^#?dcredit', line: 'dcredit = -1' }
    - { regexp: '^#?ucredit', line: 'ucredit = -1' }
    - { regexp: '^#?ocredit', line: 'ocredit = -1' }
    - { regexp: '^#?lcredit', line: 'lcredit = -1' }
    - { regexp: '^#?maxrepeat', line: 'maxrepeat = 3' }
  tags: [pam]

- name: PAM - Configure account lockout
  ansible.builtin.blockinfile:
    path: /etc/pam.d/common-auth
    insertbefore: "^auth.*pam_unix.so"
    block: |
      auth required pam_faillock.so preauth silent deny=5 unlock_time=900
      auth [default=die] pam_faillock.so authfail deny=5 unlock_time=900
    marker: "# {mark} ANSIBLE MANAGED — faillock"
  tags: [pam]

# === AUDITD ===
- name: Auditd - Install and enable
  ansible.builtin.apt:
    name:
      - auditd
      - audispd-plugins
    state: present
  tags: [audit]

- name: Auditd - Deploy comprehensive audit rules
  ansible.builtin.template:
    src: audit.rules.j2
    dest: /etc/audit/rules.d/99-security.rules
    owner: root
    group: root
    mode: '0640'
  notify: restart auditd
  tags: [audit]

# === SYSCTL HARDENING ===
- name: Sysctl - Network hardening parameters
  ansible.posix.sysctl:
    name: "{{ item.key }}"
    value: "{{ item.value }}"
    sysctl_set: true
    state: present
    reload: true
    sysctl_file: /etc/sysctl.d/99-security.conf
  loop:
    # Disable IP forwarding
    - { key: 'net.ipv4.ip_forward', value: '0' }
    - { key: 'net.ipv6.conf.all.forwarding', value: '0' }
    # Disable source routing
    - { key: 'net.ipv4.conf.all.accept_source_route', value: '0' }
    - { key: 'net.ipv6.conf.all.accept_source_route', value: '0' }
    # Disable ICMP redirects
    - { key: 'net.ipv4.conf.all.accept_redirects', value: '0' }
    - { key: 'net.ipv4.conf.all.send_redirects', value: '0' }
    - { key: 'net.ipv6.conf.all.accept_redirects', value: '0' }
    # Enable TCP SYN cookies
    - { key: 'net.ipv4.tcp_syncookies', value: '1' }
    # Log martian packets
    - { key: 'net.ipv4.conf.all.log_martians', value: '1' }
    # Disable SUID core dumps
    - { key: 'fs.suid_dumpable', value: '0' }
    # ASLR
    - { key: 'kernel.randomize_va_space', value: '2' }
    # Restrict kernel pointers
    - { key: 'kernel.kptr_restrict', value: '2' }
    # Restrict dmesg
    - { key: 'kernel.dmesg_restrict', value: '1' }
    # Restrict ptrace
    - { key: 'kernel.yama.ptrace_scope', value: '2' }
  tags: [sysctl]

# === FIREWALL ===
- name: UFW - Set default policies
  community.general.ufw:
    state: enabled
    default: deny
    direction: incoming
  tags: [firewall]

- name: UFW - Allow SSH from management network only
  community.general.ufw:
    rule: allow
    port: '22'
    proto: tcp
    src: "{{ management_network }}"
    comment: "SSH from management"
  tags: [firewall]

- name: UFW - Allow monitoring agent
  community.general.ufw:
    rule: allow
    port: "{{ wazuh_agent_port | default('1514') }}"
    proto: tcp
    src: "{{ wazuh_manager_ip }}"
    comment: "Wazuh agent"
  tags: [firewall]

# === FILE PERMISSIONS ===
- name: Permissions - Restrict critical file permissions
  ansible.builtin.file:
    path: "{{ item.path }}"
    owner: root
    group: "{{ item.group | default('root') }}"
    mode: "{{ item.mode }}"
  loop:
    - { path: '/etc/passwd', mode: '0644' }
    - { path: '/etc/shadow', mode: '0640', group: 'shadow' }
    - { path: '/etc/gshadow', mode: '0640', group: 'shadow' }
    - { path: '/etc/group', mode: '0644' }
    - { path: '/boot/grub/grub.cfg', mode: '0600' }
    - { path: '/etc/crontab', mode: '0600' }
    - { path: '/etc/ssh/sshd_config', mode: '0600' }
  tags: [permissions]

- name: Permissions - Find world-writable files
  ansible.builtin.command:
    cmd: find / -xdev -type f -perm -0002 -not -path '/proc/*' -not -path '/sys/*'
  register: world_writable
  changed_when: false
  failed_when: false
  tags: [permissions]

- name: Permissions - Remove world-writable bit
  ansible.builtin.file:
    path: "{{ item }}"
    mode: 'o-w'
  loop: "{{ world_writable.stdout_lines }}"
  when: world_writable.stdout_lines | length > 0
  tags: [permissions]

# === USER ACCOUNTS ===
- name: Users - Lock default system accounts
  ansible.builtin.user:
    name: "{{ item }}"
    shell: /usr/sbin/nologin
    password_lock: true
  loop:
    - daemon
    - bin
    - sys
    - sync
    - games
    - man
    - lp
    - mail
    - news
    - uucp
    - proxy
    - www-data
    - backup
    - list
    - irc
    - gnats
    - nobody
  tags: [users]

- name: Users - Ensure no UID 0 accounts except root
  ansible.builtin.shell: |
    set -o pipefail
    awk -F: '$3 == 0 && $1 != "root" {print $1}' /etc/passwd
  register: uid0_accounts
  changed_when: false
  tags: [users]

- name: Users - Alert on non-root UID 0 accounts
  ansible.builtin.fail:
    msg: "SECURITY: Non-root accounts with UID 0 found: {{ uid0_accounts.stdout_lines }}"
  when: uid0_accounts.stdout_lines | length > 0
  tags: [users]
```

### Audit Rules Template

```jinja2
{# templates/audit.rules.j2 #}
# Ansible managed — do not edit manually
# CIS Benchmark audit rules

# Remove existing rules
-D

# Buffer size
-b 8192

# Failure mode: 1=printk, 2=panic
-f 1

# Monitor time changes
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# Monitor user/group changes
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

# Monitor network configuration
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /etc/network -p wa -k system-locale

# Monitor login/logout
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins

# Monitor session initiation
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k session
-w /var/log/btmp -p wa -k session

# Monitor privilege escalation
-a always,exit -F arch=b64 -S execve -C uid!=euid -F euid=0 -k privilege_escalation
-a always,exit -F arch=b64 -S execve -C gid!=egid -F egid=0 -k privilege_escalation
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d -p wa -k sudoers

# Monitor file deletion by users
-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete

# Monitor kernel module loading
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -S delete_module -k modules

# Make configuration immutable (requires reboot to change)
{% if auditd_immutable | default(true) %}
-e 2
{% endif %}
```

### Windows Hardening Playbook

```yaml
# roles/windows-hardening/tasks/main.yml
---
- name: Windows - Disable SMBv1
  ansible.windows.win_optional_feature:
    name: SMB1Protocol
    state: absent
  tags: [smb]

- name: Windows - Configure Windows Firewall
  community.windows.win_firewall:
    state: enabled
    profiles:
      - Domain
      - Private
      - Public
  tags: [firewall]

- name: Windows - Set audit policies
  ansible.windows.win_command: >
    auditpol /set /subcategory:"{{ item.subcategory }}"
    /success:{{ item.success }} /failure:{{ item.failure }}
  loop:
    - { subcategory: 'Logon', success: 'enable', failure: 'enable' }
    - { subcategory: 'Logoff', success: 'enable', failure: 'enable' }
    - { subcategory: 'Account Lockout', success: 'enable', failure: 'enable' }
    - { subcategory: 'User Account Management', success: 'enable', failure: 'enable' }
    - { subcategory: 'Security Group Management', success: 'enable', failure: 'enable' }
    - { subcategory: 'Process Creation', success: 'enable', failure: 'enable' }
    - { subcategory: 'Sensitive Privilege Use', success: 'enable', failure: 'enable' }
  tags: [audit]

- name: Windows - Harden registry security settings
  ansible.windows.win_regedit:
    path: "{{ item.path }}"
    name: "{{ item.name }}"
    data: "{{ item.data }}"
    type: "{{ item.type }}"
  loop:
    # Disable LLMNR
    - path: HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient
      name: EnableMulticast
      data: 0
      type: dword
    # Disable WPAD
    - path: HKLM:\SYSTEM\CurrentControlSet\Services\WinHttpAutoProxySvc
      name: Start
      data: 4
      type: dword
    # Enable LSA protection
    - path: HKLM:\SYSTEM\CurrentControlSet\Control\Lsa
      name: RunAsPPL
      data: 1
      type: dword
    # Disable WDigest
    - path: HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest
      name: UseLogonCredential
      data: 0
      type: dword
    # Restrict anonymous SAM enumeration
    - path: HKLM:\SYSTEM\CurrentControlSet\Control\Lsa
      name: RestrictAnonymousSAM
      data: 1
      type: dword
    # NTLMv2 only
    - path: HKLM:\SYSTEM\CurrentControlSet\Control\Lsa
      name: LmCompatibilityLevel
      data: 5
      type: dword
    # Command line in process creation events
    - path: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit
      name: ProcessCreationIncludeCmdLine_Enabled
      data: 1
      type: dword
  tags: [registry]

- name: Windows - Configure account lockout policy
  ansible.windows.win_command: >
    net accounts /lockoutthreshold:5 /lockoutduration:30 /lockoutwindow:30
  tags: [accounts]

- name: Windows - Disable unused services
  ansible.windows.win_service:
    name: "{{ item }}"
    start_mode: disabled
    state: stopped
  loop:
    - RemoteRegistry
    - Fax
    - Spooler        # Disable if no printing needed
    - SSDPSRV        # SSDP Discovery
    - upnphost       # UPnP
    - lltdsvc        # Link-Layer Topology Discovery
    - WMPNetworkSvc  # Windows Media Player Sharing
  ignore_errors: true
  tags: [services]
```

### Network Device Hardening — Cisco IOS

```yaml
# playbooks/cisco-hardening.yml
---
- name: Harden Cisco IOS devices
  hosts: cisco_switches
  gather_facts: false
  connection: ansible.netcommon.network_cli

  tasks:
    - name: Configure secure management plane
      cisco.ios.ios_config:
        lines:
          - service password-encryption
          - no ip http server
          - no ip http secure-server
          - no cdp run
          - no ip source-route
          - no ip finger
          - no service tcp-small-servers
          - no service udp-small-servers
          - service timestamps log datetime msec localtime show-timezone
          - logging buffered 65536 informational
          - login block-for 120 attempts 3 within 60
      tags: [management]

    - name: Configure SSH hardening
      cisco.ios.ios_config:
        lines:
          - ip ssh version 2
          - ip ssh time-out 60
          - ip ssh authentication-retries 3
          - ip ssh source-interface Loopback0
          - crypto key generate rsa modulus 4096
        parents: []
      tags: [ssh]

    - name: Configure ACL for management access
      cisco.ios.ios_config:
        lines:
          - permit tcp {{ management_network }} {{ management_wildcard }} any eq 22
          - deny ip any any log
        parents: "ip access-list extended MGMT-ACCESS"
      tags: [acl]

    - name: Apply ACL to VTY lines
      cisco.ios.ios_config:
        lines:
          - access-class MGMT-ACCESS in
          - transport input ssh
          - exec-timeout 5 0
          - logging synchronous
        parents: "line vty 0 4"
      tags: [vty]

    - name: Configure NTP authentication
      cisco.ios.ios_config:
        lines:
          - ntp authenticate
          - ntp authentication-key 1 md5 {{ ntp_key | hash('md5') }}
          - ntp trusted-key 1
          - ntp server {{ ntp_server_1 }} key 1
          - ntp server {{ ntp_server_2 }} key 1
      tags: [ntp]

    - name: Save running configuration
      cisco.ios.ios_config:
        save_when: always
      tags: [save]
```

### Kubernetes Hardening Playbook

```yaml
# playbooks/k8s-hardening.yml
---
- name: Harden Kubernetes cluster
  hosts: k8s_control_plane
  become: true

  tasks:
    - name: Deploy Pod Security Standards
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: v1
          kind: Namespace
          metadata:
            name: "{{ item }}"
            labels:
              pod-security.kubernetes.io/enforce: restricted
              pod-security.kubernetes.io/audit: restricted
              pod-security.kubernetes.io/warn: restricted
      loop: "{{ production_namespaces }}"
      tags: [pss]

    - name: Deploy NetworkPolicy - default deny all
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: networking.k8s.io/v1
          kind: NetworkPolicy
          metadata:
            name: default-deny-all
            namespace: "{{ item }}"
          spec:
            podSelector: {}
            policyTypes:
              - Ingress
              - Egress
      loop: "{{ production_namespaces }}"
      tags: [network-policy]

    - name: Deploy ResourceQuotas
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: v1
          kind: ResourceQuota
          metadata:
            name: security-quota
            namespace: "{{ item }}"
          spec:
            hard:
              pods: "50"
              requests.cpu: "10"
              requests.memory: 20Gi
              limits.cpu: "20"
              limits.memory: 40Gi
              persistentvolumeclaims: "10"
      loop: "{{ production_namespaces }}"
      tags: [quotas]

    - name: Configure RBAC - restrict cluster-admin
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: rbac.authorization.k8s.io/v1
          kind: ClusterRoleBinding
          metadata:
            name: restricted-cluster-admin
          roleRef:
            apiGroup: rbac.authorization.k8s.io
            kind: ClusterRole
            name: cluster-admin
          subjects:
            - kind: Group
              name: "platform-admins"
              apiGroup: rbac.authorization.k8s.io
      tags: [rbac]

    - name: Deploy OPA Gatekeeper constraints
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: constraints.gatekeeper.sh/v1beta1
          kind: K8sDisallowedTags
          metadata:
            name: no-latest-tag
          spec:
            match:
              kinds:
                - apiGroups: [""]
                  kinds: ["Pod"]
            parameters:
              tags: ["latest"]
      tags: [opa]
```

---

## 4. SOAR — Security Orchestration Automation Response

### SOAR Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOAR PLATFORM                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Playbook    │  │    Case      │  │   Integration Hub    │  │
│  │  Engine      │  │  Management  │  │                      │  │
│  │              │  │              │  │  ┌────┐ ┌────┐ ┌───┐ │  │
│  │  • Triggers  │  │  • Tickets   │  │  │SIEM│ │EDR │ │FW │ │  │
│  │  • Actions   │  │  • Evidence  │  │  └────┘ └────┘ └───┘ │  │
│  │  • Decisions │  │  • Timeline  │  │  ┌────┐ ┌────┐ ┌───┐ │  │
│  │  • Loops     │  │  • Metrics   │  │  │TIP │ │IAM │ │DNS│ │  │
│  │  • Parallel  │  │  • SLA       │  │  └────┘ └────┘ └───┘ │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    METRICS & REPORTING                     │   │
│  │  MTTR | Playbook runs | Automation rate | Analyst time    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │              │              │
    ┌────┴───┐    ┌────┴───┐    ┌────┴───┐
    │  SIEM  │    │  Email │    │  EDR   │
    │ Alerts │    │ Report │    │ Alerts │
    └────────┘    └────────┘    └────────┘
```

### Platform Comparison

| Feature | Cortex XSOAR | Splunk SOAR | Shuffle | TheHive+Cortex | Tines |
|---------|-------------|-------------|---------|----------------|-------|
| Deployment | On-prem/Cloud | On-prem/Cloud | Self-hosted | Self-hosted | SaaS |
| Playbook style | YAML + Python | Visual + Python | Visual + JSON | Webhooks + analyzers | No-code drag&drop |
| Integrations | 800+ content packs | 300+ phantom apps | 200+ apps | Cortex analyzers | HTTP actions |
| Case management | Built-in | Built-in | Basic | TheHive (excellent) | Minimal |
| Cost | Enterprise $$$$ | Enterprise $$$$ | Free (OSS) | Free (OSS) | Per-story pricing |
| Learning curve | High | Medium | Low | Medium | Low |
| Best for | Large SOC | Splunk shops | Startups/labs | Purple teams | Non-dev teams |

### Cortex XSOAR — Architecture Deep Dive

Cortex XSOAR (formerly Demisto) operates on:

- **Content Packs:** Bundled integrations, playbooks, scripts, classifiers, mappers
- **Playbooks:** DAG-based workflows with conditional logic, loops, error handling
- **War Room:** Per-incident collaboration space with full audit trail
- **Indicators:** Centralized IOC management with TTP context
- **Jobs:** Scheduled playbook execution (feed ingestion, maintenance)

### TheHive + Cortex — Open Source SOAR

TheHive provides case management. Cortex provides automation (analyzers + responders).

**TheHive Architecture:**

- Case → Observables → Tasks → Analyzers → Reports
- Observable types: IP, domain, hash, email, URL, filename, custom
- Configurable templates per alert type
- MITRE ATT&CK integration for TTP tagging

**Cortex Analyzers (detection/enrichment):**

- VirusTotal_GetReport
- AbuseIPDB_CheckIP
- Shodan_Host
- MISP_SearchAttributes
- DomainTools_RiskScore
- OTXQuery
- PassiveTotal_Lookup

**Cortex Responders (containment/remediation):**

- Wazuh_BlockIP
- CrowdStrike_ContainHost
- AzureAD_DisableUser
- PaloAlto_BlockIP
- DNS_Sinkhole

### Shuffle — Open-Source SOAR Setup

```yaml
# docker-compose.yml — Shuffle SOAR deployment
version: "3.8"
services:
  shuffle-frontend:
    image: ghcr.io/shuffle/shuffle-frontend:latest
    container_name: shuffle-frontend
    hostname: shuffle-frontend
    ports:
      - "3443:443"
      - "3001:80"
    environment:
      - BACKEND_HOSTNAME=shuffle-backend
    restart: unless-stopped

  shuffle-backend:
    image: ghcr.io/shuffle/shuffle-backend:latest
    container_name: shuffle-backend
    hostname: shuffle-backend
    ports:
      - "5001:5001"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - shuffle-apps:/shuffle-apps
      - shuffle-files:/shuffle-files
    environment:
      - SHUFFLE_APP_SDK_VERSION=1.2.0
      - SHUFFLE_OPENSEARCH_URL=https://shuffle-opensearch:9200
      - SHUFFLE_DEFAULT_USERNAME=admin
      - SHUFFLE_DEFAULT_PASSWORD=${SHUFFLE_ADMIN_PASSWORD}
      - SHUFFLE_ORBORUS_EXECUTION_TIMEOUT=600
    restart: unless-stopped
    depends_on:
      - shuffle-opensearch

  shuffle-orborus:
    image: ghcr.io/shuffle/shuffle-orborus:latest
    container_name: shuffle-orborus
    hostname: shuffle-orborus
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - SHUFFLE_WORKER_VERSION=latest
      - BASE_URL=http://shuffle-backend:5001
      - ENVIRONMENT_NAME=Shuffle
      - ORG_ID=Shuffle
      - CLEANUP=true
    restart: unless-stopped
    depends_on:
      - shuffle-backend

  shuffle-opensearch:
    image: opensearchproject/opensearch:2.11.0
    container_name: shuffle-opensearch
    hostname: shuffle-opensearch
    environment:
      - cluster.name=shuffle-cluster
      - node.name=shuffle-opensearch
      - discovery.type=single-node
      - OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g
      - bootstrap.memory_lock=true
      - DISABLE_INSTALL_DEMO_CONFIG=true
      - DISABLE_SECURITY_PLUGIN=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - shuffle-opensearch-data:/usr/share/opensearch/data
    restart: unless-stopped

volumes:
  shuffle-apps:
  shuffle-files:
  shuffle-opensearch-data:
```

---

## 5. SOAR Playbook Design

### Playbook Development Methodology

1. **Define trigger:** What event starts this playbook?
2. **Map decision tree:** What conditions branch the logic?
3. **Identify integrations:** What tools/APIs are needed?
4. **Design error handling:** What happens when an integration fails?
5. **Set SLA timers:** When does escalation occur?
6. **Define human gates:** Which decisions require analyst approval?
7. **Build metrics hooks:** What telemetry do we collect?
8. **Test with synthetic data:** Never test on production incidents first.

### Phishing Response Playbook

```yaml
# shuffle/workflows/phishing-response.json (conceptual YAML representation)
---
name: Phishing Triage and Response
trigger:
  type: webhook
  source: email_gateway
  filter:
    category: suspicious_email

steps:
  - id: extract_observables
    action: email_parser
    inputs:
      raw_email: "{{ trigger.body.raw_email }}"
    outputs:
      sender_address: "{{ result.from }}"
      sender_domain: "{{ result.from_domain }}"
      urls: "{{ result.urls }}"
      attachments: "{{ result.attachments }}"
      headers: "{{ result.headers }}"

  - id: check_sender_reputation
    action: parallel
    steps:
      - action: abuseipdb_check
        inputs:
          ip: "{{ steps.extract_observables.outputs.sender_ip }}"
      - action: virustotal_domain
        inputs:
          domain: "{{ steps.extract_observables.outputs.sender_domain }}"
      - action: internal_whitelist_check
        inputs:
          email: "{{ steps.extract_observables.outputs.sender_address }}"

  - id: detonate_attachments
    action: parallel
    condition: "{{ steps.extract_observables.outputs.attachments | length > 0 }}"
    steps:
      - action: sandbox_submit
        inputs:
          file: "{{ item }}"
          timeout: 300
        loop: "{{ steps.extract_observables.outputs.attachments }}"
      - action: virustotal_file
        inputs:
          hash: "{{ item.sha256 }}"
        loop: "{{ steps.extract_observables.outputs.attachments }}"

  - id: check_urls
    action: parallel
    condition: "{{ steps.extract_observables.outputs.urls | length > 0 }}"
    steps:
      - action: urlscan_submit
        inputs:
          url: "{{ item }}"
        loop: "{{ steps.extract_observables.outputs.urls }}"
      - action: safebrowsing_check
        inputs:
          url: "{{ item }}"
        loop: "{{ steps.extract_observables.outputs.urls }}"

  - id: calculate_verdict
    action: script
    language: python
    code: |
      score = 0
      if sender_reputation['abuseipdb_score'] > 50:
          score += 30
      if any(d['malicious'] > 3 for d in detonation_results):
          score += 50
      if any(u['verdict'] == 'malicious' for u in url_results):
          score += 40
      if not spf_pass or not dkim_pass:
          score += 20

      if score >= 70:
          verdict = "MALICIOUS"
      elif score >= 40:
          verdict = "SUSPICIOUS"
      else:
          verdict = "BENIGN"
      return {"verdict": verdict, "score": score}

  - id: auto_contain
    condition: "{{ steps.calculate_verdict.outputs.verdict == 'MALICIOUS' }}"
    action: sequential
    steps:
      - action: email_gateway_block_sender
        inputs:
          sender: "{{ steps.extract_observables.outputs.sender_address }}"
      - action: email_search_and_purge
        inputs:
          sender: "{{ steps.extract_observables.outputs.sender_address }}"
          time_window: "24h"
      - action: firewall_block_urls
        inputs:
          urls: "{{ steps.extract_observables.outputs.urls }}"
      - action: edr_search_iocs
        inputs:
          indicators: "{{ all_iocs }}"

  - id: human_review
    condition: "{{ steps.calculate_verdict.outputs.verdict == 'SUSPICIOUS' }}"
    action: human_decision
    assignee: soc_tier2
    sla: 30m
    escalation:
      target: soc_manager
      after: 45m
    context:
      email_summary: "{{ steps.extract_observables.outputs }}"
      reputation_data: "{{ steps.check_sender_reputation.outputs }}"
      detonation_results: "{{ steps.detonate_attachments.outputs }}"
    options:
      - label: "Malicious — Block and purge"
        goto: auto_contain
      - label: "Benign — Release"
        goto: close_benign
      - label: "Needs more analysis"
        goto: escalate_tier3

  - id: create_case
    condition: "{{ steps.calculate_verdict.outputs.verdict != 'BENIGN' }}"
    action: thehive_create_case
    inputs:
      title: "Phishing: {{ steps.extract_observables.outputs.sender_address }}"
      severity: "{{ 3 if verdict == 'MALICIOUS' else 2 }}"
      tags: ["phishing", "automated"]
      observables: "{{ all_iocs }}"
      description: |
        Automated phishing analysis complete.
        Verdict: {{ verdict }} (score: {{ score }})
        Sender: {{ sender_address }}
        URLs: {{ urls | join(', ') }}
        Actions taken: {{ actions_log }}

  - id: notify
    action: parallel
    steps:
      - action: slack_notify
        inputs:
          channel: "#soc-alerts"
          message: "Phishing playbook completed: {{ verdict }}"
      - action: metrics_record
        inputs:
          playbook: phishing_response
          verdict: "{{ verdict }}"
          duration: "{{ elapsed_time }}"
          automated: "{{ verdict != 'SUSPICIOUS' }}"
```

### Malware Containment Playbook

```yaml
---
name: Automated Malware Containment
trigger:
  type: siem_alert
  rule: "EDR_MALWARE_DETECTED"
  severity: ["high", "critical"]

steps:
  - id: enrich_alert
    action: parallel
    steps:
      - action: edr_get_process_tree
        inputs:
          host: "{{ trigger.hostname }}"
          pid: "{{ trigger.process_id }}"
      - action: siem_get_recent_events
        inputs:
          host: "{{ trigger.hostname }}"
          timeframe: "1h"
      - action: cmdb_get_asset_info
        inputs:
          hostname: "{{ trigger.hostname }}"

  - id: assess_criticality
    action: script
    language: python
    code: |
      asset = cmdb_result
      is_critical = asset.get('criticality', '') in ['critical', 'high']
      is_server = asset.get('type', '') == 'server'
      has_lateral = len([e for e in siem_events if e['type'] == 'lateral_movement']) > 0

      if has_lateral:
          response = "IMMEDIATE_ISOLATE"
      elif is_critical and is_server:
          response = "HUMAN_DECISION"
      else:
          response = "AUTO_CONTAIN"

      return {"response_type": response, "is_critical": is_critical}

  - id: immediate_isolate
    condition: "{{ steps.assess_criticality.outputs.response_type == 'IMMEDIATE_ISOLATE' }}"
    action: sequential
    steps:
      - action: edr_isolate_host
        inputs:
          host: "{{ trigger.hostname }}"
          allow_rdp: true
      - action: ad_disable_account
        inputs:
          user: "{{ trigger.username }}"
      - action: revoke_sessions
        inputs:
          user: "{{ trigger.username }}"
          providers: ["okta", "azure_ad", "google_workspace"]
      - action: page_incident_commander
        inputs:
          severity: critical
          summary: "Lateral movement detected from {{ trigger.hostname }}"

  - id: auto_contain
    condition: "{{ steps.assess_criticality.outputs.response_type == 'AUTO_CONTAIN' }}"
    action: sequential
    steps:
      - action: edr_isolate_host
        inputs:
          host: "{{ trigger.hostname }}"
          allow_rdp: true
      - action: edr_kill_process
        inputs:
          host: "{{ trigger.hostname }}"
          pid: "{{ trigger.process_id }}"
      - action: collect_forensic_artifacts
        inputs:
          host: "{{ trigger.hostname }}"
          artifacts: ["memory_dump", "prefetch", "amcache", "event_logs"]

  - id: ioc_hunt
    action: parallel
    steps:
      - action: edr_threat_hunt
        inputs:
          iocs:
            hashes: "{{ trigger.file_hashes }}"
            ips: "{{ process_tree.network_connections }}"
            domains: "{{ process_tree.dns_queries }}"
          scope: "all_endpoints"
      - action: siem_search
        inputs:
          query: |
            (file.hash.sha256:"{{ trigger.file_hash }}" OR
             destination.ip:{{ process_tree.c2_ips | join(' OR destination.ip:') }})
            AND NOT host.name:"{{ trigger.hostname }}"
          timeframe: "7d"

  - id: block_iocs
    action: parallel
    steps:
      - action: firewall_block_ips
        inputs:
          ips: "{{ process_tree.c2_ips }}"
          comment: "Automated block — malware C2 — case {{ case_id }}"
      - action: proxy_block_domains
        inputs:
          domains: "{{ process_tree.c2_domains }}"
      - action: edr_block_hash
        inputs:
          hashes: "{{ trigger.file_hashes }}"

  - id: create_case
    action: thehive_create_case
    inputs:
      title: "Malware: {{ trigger.malware_name }} on {{ trigger.hostname }}"
      severity: "{{ 4 if response_type == 'IMMEDIATE_ISOLATE' else 3 }}"
      tags: ["malware", "{{ trigger.malware_family }}", "automated-containment"]
      tasks:
        - title: "Forensic Analysis"
          status: Waiting
        - title: "Root Cause Analysis"
          status: Waiting
        - title: "Remediation and Recovery"
          status: Waiting
        - title: "Lessons Learned"
          status: Waiting
```

### Error Handling in SOAR Playbooks

```python
# Generic error handler pattern for SOAR playbook steps
import traceback
from datetime import datetime, timezone


class PlaybookStepError(Exception):
    def __init__(self, step_id, action, error, recoverable=True):
        self.step_id = step_id
        self.action = action
        self.error = error
        self.recoverable = recoverable
        self.timestamp = datetime.now(timezone.utc).isoformat()
        super().__init__(f"Step {step_id} ({action}) failed: {error}")


def execute_with_retry(step_func, step_id, max_retries=3, backoff_base=2):
    """Execute a playbook step with exponential backoff retry."""
    last_error = None

    for attempt in range(max_retries):
        try:
            result = step_func()
            return {"status": "success", "result": result, "attempts": attempt + 1}
        except Exception as e:
            last_error = e
            wait_time = backoff_base ** attempt

            # Log retry attempt
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step_id": step_id,
                "attempt": attempt + 1,
                "max_retries": max_retries,
                "error": str(e),
                "next_retry_in": wait_time,
            }
            audit_log(log_entry)

            if attempt < max_retries - 1:
                time.sleep(wait_time)

    # All retries exhausted
    return {
        "status": "failed",
        "error": str(last_error),
        "traceback": traceback.format_exc(),
        "attempts": max_retries,
        "escalation_required": True,
    }


def playbook_error_handler(error, context):
    """Central error handler for playbook execution failures."""
    severity = assess_error_severity(error)

    if severity == "critical":
        # Integration completely down — escalate immediately
        page_oncall(
            message=f"SOAR playbook failure: {error.step_id} - {error.action}",
            context=context,
        )
        create_incident_ticket(
            title=f"SOAR Integration Failure: {error.action}",
            severity="P1",
            description=f"Automated containment blocked. Manual action required.\n"
                       f"Error: {error.error}\n"
                       f"Context: {context}",
        )
    elif severity == "degraded":
        # Partial failure — continue with reduced capability
        notify_soc_channel(
            message=f"Warning: {error.action} failed, continuing with degraded playbook",
        )
        # Skip non-critical enrichment, proceed to containment
        return {"action": "continue_degraded", "skipped_step": error.step_id}
    else:
        # Non-critical — log and continue
        audit_log({"level": "warn", "error": str(error)})
        return {"action": "continue", "note": f"Step {error.step_id} skipped"}
```

### SLA Enforcement

```python
# SOAR SLA enforcement engine
from dataclasses import dataclass, field
from enum import Enum


class SLAPriority(Enum):
    CRITICAL = "critical"   # 15 min response, 1 hour resolution
    HIGH = "high"           # 30 min response, 4 hour resolution
    MEDIUM = "medium"       # 2 hour response, 24 hour resolution
    LOW = "low"             # 8 hour response, 72 hour resolution


@dataclass
class SLAPolicy:
    priority: SLAPriority
    response_minutes: int
    resolution_minutes: int
    escalation_chain: list = field(default_factory=list)
    business_hours_only: bool = False


SLA_POLICIES = {
    SLAPriority.CRITICAL: SLAPolicy(
        priority=SLAPriority.CRITICAL,
        response_minutes=15,
        resolution_minutes=60,
        escalation_chain=["soc_tier2", "soc_manager", "ciso"],
        business_hours_only=False,
    ),
    SLAPriority.HIGH: SLAPolicy(
        priority=SLAPriority.HIGH,
        response_minutes=30,
        resolution_minutes=240,
        escalation_chain=["soc_tier2", "soc_manager"],
        business_hours_only=False,
    ),
    SLAPriority.MEDIUM: SLAPolicy(
        priority=SLAPriority.MEDIUM,
        response_minutes=120,
        resolution_minutes=1440,
        escalation_chain=["soc_tier1", "soc_tier2"],
        business_hours_only=True,
    ),
    SLAPriority.LOW: SLAPolicy(
        priority=SLAPriority.LOW,
        response_minutes=480,
        resolution_minutes=4320,
        escalation_chain=["soc_tier1"],
        business_hours_only=True,
    ),
}


def check_sla_breach(case, current_time):
    """Check if a case has breached SLA and trigger escalation."""
    policy = SLA_POLICIES[case.priority]
    elapsed = (current_time - case.created_at).total_seconds() / 60

    result = {"breached": False, "warnings": []}

    # Response SLA check
    if not case.first_response_at:
        if elapsed > policy.response_minutes:
            result["breached"] = True
            result["breach_type"] = "response"
            escalate(case, policy, "Response SLA breached")
        elif elapsed > policy.response_minutes * 0.8:
            result["warnings"].append("Response SLA 80% consumed")
            notify_assignee(case, "SLA warning: respond within "
                          f"{policy.response_minutes - elapsed:.0f} min")

    # Resolution SLA check
    if case.status not in ["resolved", "closed"]:
        if elapsed > policy.resolution_minutes:
            result["breached"] = True
            result["breach_type"] = "resolution"
            escalate(case, policy, "Resolution SLA breached")
        elif elapsed > policy.resolution_minutes * 0.75:
            result["warnings"].append("Resolution SLA 75% consumed")

    return result
```

---

## 6. Infrastructure as Code Security

### Terraform Security — Comprehensive Controls

```hcl
# terraform/main.tf — Security-hardened Terraform configuration

terraform {
  required_version = ">= 1.6.0"

  # Remote state with encryption and locking
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "production/infrastructure.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:eu-west-1:123456789:key/mrk-abc123"
    dynamodb_table = "terraform-state-lock"

    # Prevent state from containing secrets in logs
    skip_metadata_api_check = false
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40.0"  # Pin minor version
    }
  }
}

# Provider with assume role — never use static keys
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn     = "arn:aws:iam::${var.aws_account_id}:role/TerraformDeployRole"
    session_name = "terraform-${var.environment}"
    external_id  = var.external_id  # Confused deputy prevention
  }

  default_tags {
    tags = {
      ManagedBy   = "terraform"
      Environment = var.environment
      Owner       = "platform-team"
      CostCenter  = var.cost_center
    }
  }
}

# === VPC with security controls ===
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  # VPC Flow Logs for network visibility
  tags = {
    Name = "${var.project}-${var.environment}-vpc"
  }
}

resource "aws_flow_log" "vpc_flow_log" {
  iam_role_arn    = aws_iam_role.flow_log_role.arn
  log_destination = aws_cloudwatch_log_group.flow_log.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Name = "${var.project}-vpc-flow-logs"
  }
}

# === S3 Bucket with security hardening ===
resource "aws_s3_bucket" "data" {
  bucket = "${var.project}-${var.environment}-data"

  tags = {
    DataClassification = "confidential"
  }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data_key.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_logging" "data" {
  bucket = aws_s3_bucket.data.id

  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "s3-access-logs/${aws_s3_bucket.data.id}/"
}

# === KMS Key with rotation ===
resource "aws_kms_key" "data_key" {
  description             = "Encryption key for ${var.project} data"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  rotation_period_in_days = 90

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableRootAccountAccess"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${var.aws_account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid    = "AllowTerraformRole"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.aws_account_id}:role/TerraformDeployRole"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
}

# === Security Group — restrictive by default ===
resource "aws_security_group" "app" {
  name_prefix = "${var.project}-app-"
  description = "Application security group — managed by Terraform"
  vpc_id      = aws_vpc.main.id

  # No inline rules — use aws_security_group_rule for auditability
  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project}-app-sg"
  }
}

# Explicit ingress rules — no 0.0.0.0/0
resource "aws_security_group_rule" "app_ingress_alb" {
  type                     = "ingress"
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  security_group_id        = aws_security_group.app.id
  source_security_group_id = aws_security_group.alb.id
  description              = "Allow traffic from ALB only"
}

# Restrictive egress
resource "aws_security_group_rule" "app_egress_https" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  security_group_id = aws_security_group.app.id
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow HTTPS outbound"
}
```

### HashiCorp Sentinel Policies

```python
# sentinel/restrict-instance-types.sentinel
import "tfplan/v2" as tfplan

# Restrict EC2 instance types to approved list
allowed_types = [
  "t3.micro", "t3.small", "t3.medium",
  "m6i.large", "m6i.xlarge",
  "c6i.large", "c6i.xlarge",
]

ec2_instances = filter tfplan.resource_changes as _, rc {
  rc.type is "aws_instance" and
  rc.mode is "managed" and
  (rc.change.actions contains "create" or rc.change.actions contains "update")
}

instance_type_allowed = rule {
  all ec2_instances as _, instance {
    instance.change.after.instance_type in allowed_types
  }
}

# Ensure encryption at rest
ebs_encrypted = rule {
  all ec2_instances as _, instance {
    all instance.change.after.root_block_device as _, rbd {
      rbd.encrypted is true
    }
  }
}

main = rule {
  instance_type_allowed and ebs_encrypted
}
```

### Policy-as-Code — OPA/Rego

```rego
# policy/terraform/security.rego
package terraform.security

import rego.v1

# Deny S3 buckets without encryption
deny contains msg if {
    resource := input.resource_changes[_]
    resource.type == "aws_s3_bucket"
    not has_encryption(resource)
    msg := sprintf("S3 bucket '%s' must have server-side encryption enabled", [resource.name])
}

# Deny security groups with 0.0.0.0/0 ingress
deny contains msg if {
    resource := input.resource_changes[_]
    resource.type == "aws_security_group_rule"
    resource.change.after.type == "ingress"
    cidr := resource.change.after.cidr_blocks[_]
    cidr == "0.0.0.0/0"
    msg := sprintf("Security group rule '%s' allows ingress from 0.0.0.0/0", [resource.name])
}

# Deny RDS instances without encryption
deny contains msg if {
    resource := input.resource_changes[_]
    resource.type == "aws_db_instance"
    resource.change.after.storage_encrypted != true
    msg := sprintf("RDS instance '%s' must have storage encryption enabled", [resource.name])
}

# Deny IAM policies with *:* (admin access)
deny contains msg if {
    resource := input.resource_changes[_]
    resource.type == "aws_iam_policy"
    policy_doc := json.unmarshal(resource.change.after.policy)
    statement := policy_doc.Statement[_]
    statement.Effect == "Allow"
    statement.Action[_] == "*"
    statement.Resource[_] == "*"
    msg := sprintf("IAM policy '%s' grants admin access (*:*)", [resource.name])
}

# Deny resources without required tags
required_tags := {"Environment", "Owner", "ManagedBy"}

deny contains msg if {
    resource := input.resource_changes[_]
    resource.change.after.tags != null
    existing_tags := {key | resource.change.after.tags[key]}
    missing := required_tags - existing_tags
    count(missing) > 0
    msg := sprintf("Resource '%s' missing required tags: %v", [resource.name, missing])
}

has_encryption(resource) if {
    resource.change.after.server_side_encryption_configuration != null
}
```

### IaC Scanning — CI Integration

```yaml
# .github/workflows/iac-security.yml
---
name: IaC Security Scan
on:
  pull_request:
    paths:
      - 'terraform/**'
      - 'cloudformation/**'
      - 'kubernetes/**'

jobs:
  checkov:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Checkov
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: terraform/
          framework: terraform
          output_format: sarif
          output_file_path: checkov-results.sarif
          soft_fail: false
          skip_check: CKV_AWS_999  # Document any skips with justification
          compact: true

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: checkov-results.sarif

  tfsec:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run tfsec
        uses: aquasecurity/tfsec-action@v1.0.3
        with:
          working_directory: terraform/
          format: sarif
          out: tfsec-results.sarif
          soft_fail: false

  opa-policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.6.6"

      - name: Terraform Plan (JSON)
        run: |
          cd terraform/
          terraform init -backend=false
          terraform plan -out=tfplan
          terraform show -json tfplan > tfplan.json

      - name: Run OPA Policy Check
        uses: open-policy-agent/opa-action@v2
        with:
          command: eval
          input: terraform/tfplan.json
          policy: policy/terraform/
          query: "data.terraform.security.deny"
          fail-on-result: true

  kics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run KICS
        uses: checkmarx/kics-github-action@v2.1.0
        with:
          path: .
          output_path: kics-results/
          output_formats: sarif,json
          fail_on: high
          exclude_queries: "exclude-list.txt"
```

### Drift Detection

```python
#!/usr/bin/env python3
"""
Infrastructure drift detection script.
Compares Terraform state against actual cloud resources.
Flags security-relevant drifts for immediate remediation.
"""
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class DriftSeverity(Enum):
    CRITICAL = "critical"  # Security control removed/weakened
    HIGH = "high"          # Configuration changed, security impact
    MEDIUM = "medium"      # Configuration changed, no direct security impact
    LOW = "low"            # Cosmetic or tag drift


@dataclass
class DriftFinding:
    resource_type: str
    resource_id: str
    attribute: str
    expected: str
    actual: str
    severity: DriftSeverity
    remediation: str


# Security-critical attributes that constitute high/critical drift
SECURITY_CRITICAL_ATTRIBUTES = {
    "aws_security_group_rule": {
        "cidr_blocks": DriftSeverity.CRITICAL,
        "from_port": DriftSeverity.HIGH,
        "to_port": DriftSeverity.HIGH,
    },
    "aws_s3_bucket_public_access_block": {
        "block_public_acls": DriftSeverity.CRITICAL,
        "block_public_policy": DriftSeverity.CRITICAL,
        "restrict_public_buckets": DriftSeverity.CRITICAL,
    },
    "aws_s3_bucket_server_side_encryption_configuration": {
        "rule": DriftSeverity.CRITICAL,
    },
    "aws_iam_policy": {
        "policy": DriftSeverity.CRITICAL,
    },
    "aws_db_instance": {
        "storage_encrypted": DriftSeverity.CRITICAL,
        "publicly_accessible": DriftSeverity.CRITICAL,
    },
    "aws_kms_key": {
        "enable_key_rotation": DriftSeverity.HIGH,
        "deletion_window_in_days": DriftSeverity.HIGH,
    },
}


def detect_drift(terraform_dir: str) -> list[DriftFinding]:
    """Run terraform plan and parse drift."""
    result = subprocess.run(
        ["terraform", "plan", "-detailed-exitcode", "-json", "-refresh-only"],
        capture_output=True,
        text=True,
        cwd=terraform_dir,
    )

    # Exit code 2 = changes detected (drift)
    if result.returncode == 0:
        print("No drift detected.")
        return []

    if result.returncode != 2:
        print(f"Terraform error: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    findings = []
    for line in result.stdout.strip().split("\n"):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if entry.get("type") == "resource_drift":
            change = entry.get("change", {})
            resource = change.get("resource", {})
            resource_type = resource.get("type", "")
            resource_id = resource.get("addr", "")

            before = change.get("before", {})
            after = change.get("after", {})

            for attr, before_val in _diff_attrs(before, after):
                severity = _classify_severity(resource_type, attr)
                findings.append(DriftFinding(
                    resource_type=resource_type,
                    resource_id=resource_id,
                    attribute=attr,
                    expected=str(before_val),
                    actual=str(after.get(attr)),
                    severity=severity,
                    remediation=f"terraform apply -target={resource_id}",
                ))

    return findings


def _diff_attrs(before: dict, after: dict) -> list:
    """Find attributes that differ between before and after state."""
    diffs = []
    all_keys = set(list(before.keys()) + list(after.keys()))
    for key in all_keys:
        if before.get(key) != after.get(key):
            diffs.append((key, before.get(key)))
    return diffs


def _classify_severity(resource_type: str, attribute: str) -> DriftSeverity:
    """Classify drift severity based on resource type and attribute."""
    resource_rules = SECURITY_CRITICAL_ATTRIBUTES.get(resource_type, {})
    return resource_rules.get(attribute, DriftSeverity.MEDIUM)


def generate_report(findings: list[DriftFinding]) -> dict:
    """Generate drift report for SOAR ingestion."""
    critical = [f for f in findings if f.severity == DriftSeverity.CRITICAL]
    high = [f for f in findings if f.severity == DriftSeverity.HIGH]

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_findings": len(findings),
        "critical": len(critical),
        "high": len(high),
        "requires_immediate_action": len(critical) > 0,
        "findings": [
            {
                "resource": f.resource_id,
                "attribute": f.attribute,
                "severity": f.severity.value,
                "expected": f.expected,
                "actual": f.actual,
                "remediation": f.remediation,
            }
            for f in findings
        ],
    }

    return report


if __name__ == "__main__":
    terraform_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    findings = detect_drift(terraform_dir)

    if findings:
        report = generate_report(findings)
        report_path = Path("drift-report.json")
        report_path.write_text(json.dumps(report, indent=2))
        print(f"Drift report written to {report_path}")
        print(f"Critical: {report['critical']}, High: {report['high']}")

        if report["requires_immediate_action"]:
            print("ALERT: Critical security drift detected!")
            sys.exit(2)
```

---

## 7. CI/CD Security Automation

### Comprehensive Secure Pipeline

```yaml
# .github/workflows/secure-pipeline.yml
---
name: Secure CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read
  security-events: write
  id-token: write  # OIDC for keyless signing

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # === SAST — Static Analysis ===
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Semgrep SAST
        uses: semgrep/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/secrets
            p/owasp-top-ten
            p/typescript
            p/python
          generateSarif: true
        env:
          SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}

      - name: CodeQL Analysis
        uses: github/codeql-action/init@v3
        with:
          languages: javascript, python
          queries: security-extended

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3

  # === SCA — Dependency Scanning ===
  sca:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Snyk Dependency Check
        uses: snyk/actions/node@master
        with:
          args: --severity-threshold=high --json-file-output=snyk-results.json
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

      - name: OSV Scanner (Google)
        uses: google/osv-scanner/actions/scanner@v1
        with:
          scan-args: |-
            --lockfile=package-lock.json
            --lockfile=requirements.txt
            --format=json
            --output=osv-results.json

      - name: License Compliance Check
        run: |
          npx license-checker --production --failOn "GPL-3.0;AGPL-3.0" \
            --json > license-report.json

  # === Container Security ===
  container-scan:
    runs-on: ubuntu-latest
    needs: [sast, sca]
    steps:
      - uses: actions/checkout@v4

      - name: Build container image
        run: |
          docker build --no-cache \
            --label "org.opencontainers.image.source=${{ github.repositoryUrl }}" \
            --label "org.opencontainers.image.revision=${{ github.sha }}" \
            -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} .

      - name: Trivy vulnerability scan
        uses: aquasecurity/trivy-action@0.28.0
        with:
          image-ref: "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}"
          format: sarif
          output: trivy-results.sarif
          severity: "CRITICAL,HIGH"
          exit-code: "1"
          ignore-unfixed: true

      - name: Grype scan (secondary scanner)
        uses: anchore/scan-action@v4
        with:
          image: "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}"
          severity-cutoff: high
          fail-build: true
          output-format: sarif

      - name: Dockerfile linting
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: Dockerfile
          failure-threshold: warning

  # === DAST — Dynamic Analysis ===
  dast:
    runs-on: ubuntu-latest
    needs: [container-scan]
    services:
      app:
        image: "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}"
        ports:
          - 8080:8080
    steps:
      - uses: actions/checkout@v4

      - name: Wait for app ready
        run: |
          timeout 60 bash -c 'until curl -sf http://localhost:8080/health; do sleep 2; done'

      - name: OWASP ZAP Baseline Scan
        uses: zaproxy/action-baseline@v0.12.0
        with:
          target: "http://localhost:8080"
          rules_file_name: "zap-rules.tsv"
          fail_action: true

      - name: Nuclei scan
        run: |
          docker run --network host projectdiscovery/nuclei:latest \
            -u http://localhost:8080 \
            -t cves/ -t misconfiguration/ -t exposures/ \
            -severity critical,high \
            -jsonl -o nuclei-results.jsonl

  # === Supply Chain Security ===
  supply-chain:
    runs-on: ubuntu-latest
    needs: [container-scan]
    steps:
      - uses: actions/checkout@v4

      - name: Install Cosign
        uses: sigstore/cosign-installer@v3

      - name: Login to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Sign container image (keyless)
        run: |
          cosign sign --yes \
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          image: "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}"
          format: spdx-json
          output-file: sbom.spdx.json

      - name: Attest SBOM
        run: |
          cosign attest --yes --predicate sbom.spdx.json \
            --type spdxjson \
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Generate SLSA provenance
        uses: slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@v2.0.0
        with:
          image: "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}"
          digest: ${{ github.sha }}

  # === Secret Scanning ===
  secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for secret scanning

      - name: Gitleaks secret scan
        uses: gitleaks/gitleaks-action@v2
        with:
          config-path: .gitleaks.toml
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: TruffleHog scan
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified --json
```

### Pipeline Runner Hardening

```yaml
# ansible/playbooks/harden-ci-runner.yml
---
- name: Harden self-hosted CI/CD runner
  hosts: ci_runners
  become: true

  tasks:
    - name: Create dedicated runner user (non-root)
      ansible.builtin.user:
        name: ci-runner
        shell: /bin/bash
        system: true
        create_home: true
        home: /opt/ci-runner

    - name: Restrict runner filesystem access
      ansible.builtin.file:
        path: "{{ item }}"
        owner: root
        group: root
        mode: '0700'
      loop:
        - /root
        - /etc/shadow
        - /etc/sudoers.d

    - name: Configure AppArmor profile for runner
      ansible.builtin.copy:
        dest: /etc/apparmor.d/ci-runner
        content: |
          #include <tunables/global>
          /opt/ci-runner/** {
            #include <abstractions/base>
            #include <abstractions/nameservice>

            /opt/ci-runner/** rwk,
            /tmp/** rwk,
            /var/tmp/** rwk,

            # Deny access to sensitive paths
            deny /etc/shadow r,
            deny /etc/gshadow r,
            deny /root/** rwklx,
            deny /home/** rwklx,

            # Allow docker socket if needed
            /var/run/docker.sock rw,

            # Network access
            network inet stream,
            network inet dgram,
          }
        mode: '0644'
      notify: reload apparmor

    - name: Enable ephemeral runner (clean workspace per job)
      ansible.builtin.cron:
        name: "Clean CI workspace"
        minute: "*/5"
        job: "find /opt/ci-runner/_work -maxdepth 1 -mmin +60 -exec rm -rf {} +"
        user: root

    - name: Restrict outbound network (allow only required registries)
      community.general.ufw:
        rule: allow
        direction: out
        port: '443'
        proto: tcp
        dest: "{{ item }}"
        comment: "CI registry access"
      loop:
        - registry.npmjs.org
        - pypi.org
        - ghcr.io
        - docker.io
```

---

## 8. Threat Intelligence Automation

### MISP Integration Script

```python
#!/usr/bin/env python3
"""
Automated threat intelligence pipeline.
Ingests IOCs from MISP, enriches them, and pushes blocking rules.
"""
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Any

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ThreatIndicator:
    """Normalized threat indicator."""
    type: str          # ip, domain, hash_sha256, url, email
    value: str
    source: str
    confidence: int    # 0-100
    tlp: str           # white, green, amber, red
    tags: list = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""
    enrichments: dict = field(default_factory=dict)


class MISPClient:
    """MISP API client for IOC retrieval."""

    def __init__(self, url: str, api_key: str, verify_ssl: bool = True):
        self.url = url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self.session.verify = verify_ssl

    def get_recent_indicators(self, hours: int = 24, types: list = None) -> list[ThreatIndicator]:
        """Fetch indicators published in the last N hours."""
        if types is None:
            types = ["ip-dst", "domain", "sha256", "url", "email-src"]

        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        payload = {
            "returnFormat": "json",
            "timestamp": int(since.timestamp()),
            "type": {"OR": types},
            "enforceWarninglist": True,  # Exclude whitelisted
            "includeDecayScore": True,
        }

        response = self.session.post(
            f"{self.url}/attributes/restSearch",
            json=payload,
        )
        response.raise_for_status()

        indicators = []
        for attr in response.json().get("response", {}).get("Attribute", []):
            indicator = ThreatIndicator(
                type=self._normalize_type(attr["type"]),
                value=attr["value"],
                source=f"MISP-Event-{attr.get('event_id', 'unknown')}",
                confidence=self._calc_confidence(attr),
                tlp=self._extract_tlp(attr.get("Tag", [])),
                tags=[t["name"] for t in attr.get("Tag", [])],
                first_seen=attr.get("first_seen", ""),
                last_seen=attr.get("last_seen", ""),
            )
            indicators.append(indicator)

        logger.info(f"Retrieved {len(indicators)} indicators from MISP (last {hours}h)")
        return indicators

    @staticmethod
    def _normalize_type(misp_type: str) -> str:
        type_map = {
            "ip-dst": "ip",
            "ip-src": "ip",
            "domain": "domain",
            "hostname": "domain",
            "sha256": "hash_sha256",
            "md5": "hash_md5",
            "url": "url",
            "email-src": "email",
        }
        return type_map.get(misp_type, misp_type)

    @staticmethod
    def _calc_confidence(attr: dict) -> int:
        """Calculate confidence score from MISP attribute metadata."""
        base = 50
        if attr.get("to_ids"):
            base += 20
        if attr.get("decay_score"):
            base = int(attr["decay_score"].get("score", base))
        return min(base, 100)

    @staticmethod
    def _extract_tlp(tags: list) -> str:
        for tag in tags:
            name = tag.get("name", "").lower()
            if "tlp:red" in name:
                return "red"
            if "tlp:amber" in name:
                return "amber"
            if "tlp:green" in name:
                return "green"
        return "white"


class EnrichmentEngine:
    """Enrich indicators with external intelligence sources."""

    def __init__(self, config: dict):
        self.vt_key = config.get("virustotal_api_key", "")
        self.abuseipdb_key = config.get("abuseipdb_api_key", "")
        self.shodan_key = config.get("shodan_api_key", "")

    def enrich(self, indicator: ThreatIndicator) -> ThreatIndicator:
        """Enrich a single indicator based on its type."""
        if indicator.type == "ip":
            indicator.enrichments["abuseipdb"] = self._check_abuseipdb(indicator.value)
            indicator.enrichments["shodan"] = self._check_shodan(indicator.value)
        elif indicator.type == "hash_sha256":
            indicator.enrichments["virustotal"] = self._check_virustotal_hash(indicator.value)
        elif indicator.type == "domain":
            indicator.enrichments["virustotal"] = self._check_virustotal_domain(indicator.value)

        # Recalculate confidence based on enrichment
        indicator.confidence = self._recalculate_confidence(indicator)
        return indicator

    def _check_abuseipdb(self, ip: str) -> dict:
        """Query AbuseIPDB for IP reputation."""
        try:
            resp = requests.get(
                "https://api.abuseipdb.com/api/v2/check",
                headers={"Key": self.abuseipdb_key, "Accept": "application/json"},
                params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": True},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return {
                "abuse_score": data.get("abuseConfidenceScore", 0),
                "total_reports": data.get("totalReports", 0),
                "country": data.get("countryCode", ""),
                "isp": data.get("isp", ""),
                "is_tor": data.get("isTor", False),
            }
        except requests.RequestException as e:
            logger.warning(f"AbuseIPDB lookup failed for {ip}: {e}")
            return {"error": str(e)}

    def _check_shodan(self, ip: str) -> dict:
        """Query Shodan for host information."""
        try:
            resp = requests.get(
                f"https://api.shodan.io/shodan/host/{ip}",
                params={"key": self.shodan_key},
                timeout=10,
            )
            if resp.status_code == 404:
                return {"found": False}
            resp.raise_for_status()
            data = resp.json()
            return {
                "found": True,
                "ports": data.get("ports", []),
                "os": data.get("os"),
                "vulns": data.get("vulns", []),
                "last_update": data.get("last_update", ""),
            }
        except requests.RequestException as e:
            logger.warning(f"Shodan lookup failed for {ip}: {e}")
            return {"error": str(e)}

    def _check_virustotal_hash(self, file_hash: str) -> dict:
        """Query VirusTotal for file hash reputation."""
        try:
            resp = requests.get(
                f"https://www.virustotal.com/api/v3/files/{file_hash}",
                headers={"x-apikey": self.vt_key},
                timeout=15,
            )
            if resp.status_code == 404:
                return {"found": False}
            resp.raise_for_status()
            attrs = resp.json().get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            return {
                "found": True,
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "undetected": stats.get("undetected", 0),
                "names": attrs.get("names", [])[:5],
                "type": attrs.get("type_description", ""),
            }
        except requests.RequestException as e:
            logger.warning(f"VirusTotal lookup failed for {file_hash}: {e}")
            return {"error": str(e)}

    def _check_virustotal_domain(self, domain: str) -> dict:
        """Query VirusTotal for domain reputation."""
        try:
            resp = requests.get(
                f"https://www.virustotal.com/api/v3/domains/{domain}",
                headers={"x-apikey": self.vt_key},
                timeout=15,
            )
            if resp.status_code == 404:
                return {"found": False}
            resp.raise_for_status()
            attrs = resp.json().get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            return {
                "found": True,
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "categories": attrs.get("categories", {}),
                "reputation": attrs.get("reputation", 0),
            }
        except requests.RequestException as e:
            logger.warning(f"VirusTotal lookup failed for {domain}: {e}")
            return {"error": str(e)}

    @staticmethod
    def _recalculate_confidence(indicator: ThreatIndicator) -> int:
        """Recalculate confidence score based on enrichment data."""
        score = indicator.confidence

        enrichments = indicator.enrichments
        if "abuseipdb" in enrichments and "abuse_score" in enrichments["abuseipdb"]:
            abuse = enrichments["abuseipdb"]["abuse_score"]
            if abuse > 80:
                score = min(score + 25, 100)
            elif abuse > 50:
                score = min(score + 10, 100)

        if "virustotal" in enrichments and "malicious" in enrichments["virustotal"]:
            vt_mal = enrichments["virustotal"]["malicious"]
            if vt_mal > 10:
                score = min(score + 30, 100)
            elif vt_mal > 5:
                score = min(score + 15, 100)

        return score


class BlockingEngine:
    """Push verified IOCs to blocking infrastructure."""

    def __init__(self, config: dict):
        self.firewall_api = config.get("firewall_api_url", "")
        self.firewall_key = config.get("firewall_api_key", "")
        self.dns_sinkhole_api = config.get("dns_sinkhole_url", "")
        self.confidence_threshold = config.get("auto_block_threshold", 75)

    def process_indicators(self, indicators: list[ThreatIndicator]) -> dict:
        """Process enriched indicators and apply blocking rules."""
        results = {"blocked": [], "skipped": [], "errors": []}

        for indicator in indicators:
            if indicator.confidence < self.confidence_threshold:
                results["skipped"].append({
                    "value": indicator.value,
                    "reason": f"confidence {indicator.confidence} < threshold {self.confidence_threshold}",
                })
                continue

            if indicator.tlp == "red":
                results["skipped"].append({
                    "value": indicator.value,
                    "reason": "TLP:RED — manual review required",
                })
                continue

            try:
                if indicator.type == "ip":
                    self._block_ip(indicator)
                elif indicator.type == "domain":
                    self._sinkhole_domain(indicator)
                elif indicator.type == "hash_sha256":
                    self._block_hash(indicator)

                results["blocked"].append({
                    "value": indicator.value,
                    "type": indicator.type,
                    "confidence": indicator.confidence,
                })
            except Exception as e:
                results["errors"].append({
                    "value": indicator.value,
                    "error": str(e),
                })

        logger.info(
            f"Blocking results: {len(results['blocked'])} blocked, "
            f"{len(results['skipped'])} skipped, {len(results['errors'])} errors"
        )
        return results

    def _block_ip(self, indicator: ThreatIndicator):
        """Add IP to firewall block list."""
        payload = {
            "action": "block",
            "ip": indicator.value,
            "direction": "both",
            "comment": f"TI-auto: {indicator.source} conf:{indicator.confidence}",
            "expiry": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }
        resp = requests.post(
            f"{self.firewall_api}/blocklist",
            headers={"Authorization": f"Bearer {self.firewall_key}"},
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()

    def _sinkhole_domain(self, indicator: ThreatIndicator):
        """Add domain to DNS sinkhole."""
        payload = {
            "domain": indicator.value,
            "action": "sinkhole",
            "source": indicator.source,
            "ttl": 2592000,  # 30 days
        }
        resp = requests.post(
            f"{self.dns_sinkhole_api}/entries",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()

    def _block_hash(self, indicator: ThreatIndicator):
        """Add hash to EDR block list."""
        # Implementation depends on EDR vendor API
        logger.info(f"Hash {indicator.value} queued for EDR blocking")


def main():
    """Main threat intelligence pipeline execution."""
    # Load configuration from environment/vault
    config = {
        "misp_url": "https://misp.internal.corp",
        "misp_key": "LOADED_FROM_VAULT",
        "virustotal_api_key": "LOADED_FROM_VAULT",
        "abuseipdb_api_key": "LOADED_FROM_VAULT",
        "shodan_api_key": "LOADED_FROM_VAULT",
        "firewall_api_url": "https://fw-mgmt.internal.corp/api/v2",
        "firewall_api_key": "LOADED_FROM_VAULT",
        "dns_sinkhole_url": "https://dns-admin.internal.corp/api",
        "auto_block_threshold": 75,
    }

    # 1. Ingest from MISP
    misp = MISPClient(config["misp_url"], config["misp_key"])
    indicators = misp.get_recent_indicators(hours=24)

    # 2. Enrich
    enricher = EnrichmentEngine(config)
    enriched = [enricher.enrich(ioc) for ioc in indicators]

    # 3. Block
    blocker = BlockingEngine(config)
    results = blocker.process_indicators(enriched)

    # 4. Report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline_run": "threat_intel_daily",
        "total_ingested": len(indicators),
        "total_enriched": len(enriched),
        "blocked": len(results["blocked"]),
        "skipped": len(results["skipped"]),
        "errors": len(results["errors"]),
        "details": results,
    }

    # Push report to SOAR for case creation if errors > 0
    if results["errors"]:
        logger.warning(f"{len(results['errors'])} blocking errors — creating SOAR case")
        # webhook call to SOAR omitted for brevity

    return report


if __name__ == "__main__":
    main()
```

### STIX/TAXII Integration

```python
#!/usr/bin/env python3
"""
STIX/TAXII client for consuming threat intelligence feeds.
Supports TAXII 2.1 protocol.
"""
from taxii2client.v21 import Server, Collection, as_pages
from stix2 import parse, Filter, MemoryStore


class TAXIIFeedConsumer:
    """Consume STIX 2.1 objects from TAXII 2.1 servers."""

    def __init__(self, server_url: str, username: str, password: str):
        self.server = Server(
            server_url,
            user=username,
            password=password,
        )

    def list_collections(self) -> list[dict]:
        """List available TAXII collections."""
        collections = []
        for api_root in self.server.api_roots:
            for collection in api_root.collections:
                collections.append({
                    "id": collection.id,
                    "title": collection.title,
                    "description": collection.description,
                    "can_read": collection.can_read,
                })
        return collections

    def fetch_indicators(self, collection_id: str, added_after: str = None) -> list:
        """Fetch STIX indicator objects from a collection."""
        collection = self._get_collection(collection_id)
        if not collection:
            return []

        kwargs = {}
        if added_after:
            kwargs["added_after"] = added_after

        indicators = []
        for bundle in as_pages(collection.get_objects, per_request=100, **kwargs):
            for obj in bundle.get("objects", []):
                if obj.get("type") == "indicator":
                    parsed = parse(obj, allow_custom=True)
                    indicators.append(parsed)

        return indicators

    def _get_collection(self, collection_id: str):
        """Find collection by ID across all API roots."""
        for api_root in self.server.api_roots:
            for collection in api_root.collections:
                if collection.id == collection_id:
                    return collection
        return None
```

---

## 9. Compliance Automation

### Chef InSpec Compliance Profile

```ruby
# inspec/profiles/cis-linux/controls/ssh.rb
title 'CIS SSH Server Configuration'

control 'cis-5.2.1' do
  impact 1.0
  title 'Ensure SSH Protocol is set to 2'
  desc 'SSH supports two different and incompatible protocols. SSH Protocol 1 is less secure.'

  describe sshd_config do
    its('Protocol') { should cmp 2 }
  end
end

control 'cis-5.2.2' do
  impact 1.0
  title 'Ensure SSH root login is disabled'

  describe sshd_config do
    its('PermitRootLogin') { should match(/no/i) }
  end
end

control 'cis-5.2.3' do
  impact 0.7
  title 'Ensure SSH MaxAuthTries is set to 4 or less'

  describe sshd_config do
    its('MaxAuthTries') { should cmp <= 4 }
  end
end

control 'cis-5.2.4' do
  impact 1.0
  title 'Ensure SSH PasswordAuthentication is disabled'

  describe sshd_config do
    its('PasswordAuthentication') { should match(/no/i) }
  end
end

control 'cis-5.2.5' do
  impact 0.7
  title 'Ensure SSH Idle Timeout Interval is configured'

  describe sshd_config do
    its('ClientAliveInterval') { should cmp <= 300 }
    its('ClientAliveCountMax') { should cmp <= 3 }
  end
end

control 'cis-5.2.6' do
  impact 1.0
  title 'Ensure SSH X11 forwarding is disabled'

  describe sshd_config do
    its('X11Forwarding') { should match(/no/i) }
  end
end

control 'cis-5.2.7' do
  impact 0.5
  title 'Ensure SSH warning banner is configured'

  describe sshd_config do
    its('Banner') { should_not be_nil }
    its('Banner') { should match(%r{/etc/issue}) }
  end
end
```

### Automated Evidence Collection

```python
#!/usr/bin/env python3
"""
Automated compliance evidence collector.
Gathers evidence artifacts for audit purposes and stores with integrity hashes.
"""
import hashlib
import json
import os
import subprocess
import tarfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class EvidenceArtifact:
    """Single piece of compliance evidence."""
    control_id: str
    framework: str
    title: str
    collection_time: str
    hostname: str
    data: Any
    sha256: str = ""
    collector: str = "automated"

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of evidence data."""
        content = json.dumps(self.data, sort_keys=True, default=str)
        self.sha256 = hashlib.sha256(content.encode()).hexdigest()
        return self.sha256


class ComplianceEvidenceCollector:
    """Collect and package compliance evidence."""

    def __init__(self, output_dir: str = "/var/evidence"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.hostname = os.uname().nodename
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.artifacts: list[EvidenceArtifact] = []

    def collect_all(self) -> list[EvidenceArtifact]:
        """Run all evidence collectors."""
        collectors = [
            self._collect_user_accounts,
            self._collect_ssh_config,
            self._collect_firewall_rules,
            self._collect_running_services,
            self._collect_installed_packages,
            self._collect_file_permissions,
            self._collect_audit_config,
            self._collect_network_config,
            self._collect_cron_jobs,
            self._collect_kernel_params,
        ]

        for collector in collectors:
            try:
                collector()
            except Exception as e:
                self.artifacts.append(EvidenceArtifact(
                    control_id="ERROR",
                    framework="system",
                    title=f"Collection error: {collector.__name__}",
                    collection_time=self.timestamp,
                    hostname=self.hostname,
                    data={"error": str(e)},
                ))

        return self.artifacts

    def _collect_user_accounts(self):
        """CIS 5.x — User account configuration."""
        # Get all users with login shells
        result = subprocess.run(
            ["getent", "passwd"],
            capture_output=True, text=True, check=True,
        )
        users = []
        for line in result.stdout.strip().split("\n"):
            parts = line.split(":")
            users.append({
                "username": parts[0],
                "uid": int(parts[2]),
                "gid": int(parts[3]),
                "home": parts[5],
                "shell": parts[6],
                "has_password": self._user_has_password(parts[0]),
            })

        artifact = EvidenceArtifact(
            control_id="CIS-5.4",
            framework="CIS-Ubuntu-22.04-L1",
            title="User Account Inventory",
            collection_time=self.timestamp,
            hostname=self.hostname,
            data={
                "total_users": len(users),
                "interactive_users": [u for u in users if u["shell"] not in ["/usr/sbin/nologin", "/bin/false"]],
                "uid0_users": [u for u in users if u["uid"] == 0],
                "users": users,
            },
        )
        artifact.compute_hash()
        self.artifacts.append(artifact)

    def _collect_ssh_config(self):
        """CIS 5.2 — SSH server configuration."""
        ssh_config_path = Path("/etc/ssh/sshd_config")
        if not ssh_config_path.exists():
            return

        config_content = ssh_config_path.read_text()

        # Parse key settings
        settings = {}
        for line in config_content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    settings[parts[0]] = parts[1]

        artifact = EvidenceArtifact(
            control_id="CIS-5.2",
            framework="CIS-Ubuntu-22.04-L1",
            title="SSH Server Configuration",
            collection_time=self.timestamp,
            hostname=self.hostname,
            data={
                "permit_root_login": settings.get("PermitRootLogin", "NOT_SET"),
                "password_auth": settings.get("PasswordAuthentication", "NOT_SET"),
                "max_auth_tries": settings.get("MaxAuthTries", "NOT_SET"),
                "x11_forwarding": settings.get("X11Forwarding", "NOT_SET"),
                "client_alive_interval": settings.get("ClientAliveInterval", "NOT_SET"),
                "protocol": settings.get("Protocol", "NOT_SET"),
                "all_settings": settings,
            },
        )
        artifact.compute_hash()
        self.artifacts.append(artifact)

    def _collect_firewall_rules(self):
        """CIS 3.5 — Firewall configuration."""
        # UFW status
        ufw_result = subprocess.run(
            ["ufw", "status", "verbose"],
            capture_output=True, text=True,
        )

        # iptables rules
        ipt_result = subprocess.run(
            ["iptables", "-L", "-n", "-v", "--line-numbers"],
            capture_output=True, text=True,
        )

        artifact = EvidenceArtifact(
            control_id="CIS-3.5",
            framework="CIS-Ubuntu-22.04-L1",
            title="Firewall Configuration",
            collection_time=self.timestamp,
            hostname=self.hostname,
            data={
                "ufw_status": ufw_result.stdout if ufw_result.returncode == 0 else "UFW not available",
                "iptables_rules": ipt_result.stdout if ipt_result.returncode == 0 else "iptables not available",
            },
        )
        artifact.compute_hash()
        self.artifacts.append(artifact)

    def _collect_running_services(self):
        """CIS 2.x — Service inventory."""
        result = subprocess.run(
            ["systemctl", "list-units", "--type=service", "--state=running", "--no-pager", "--plain"],
            capture_output=True, text=True, check=True,
        )

        services = []
        for line in result.stdout.strip().split("\n")[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 4:
                services.append({
                    "name": parts[0],
                    "load": parts[1],
                    "active": parts[2],
                    "sub": parts[3],
                })

        artifact = EvidenceArtifact(
            control_id="CIS-2.1",
            framework="CIS-Ubuntu-22.04-L1",
            title="Running Services Inventory",
            collection_time=self.timestamp,
            hostname=self.hostname,
            data={
                "total_running": len(services),
                "services": services,
            },
        )
        artifact.compute_hash()
        self.artifacts.append(artifact)

    def _collect_installed_packages(self):
        """Software inventory for vulnerability management."""
        result = subprocess.run(
            ["dpkg-query", "-W", "-f", "${Package}\t${Version}\t${Architecture}\n"],
            capture_output=True, text=True, check=True,
        )

        packages = []
        for line in result.stdout.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) == 3:
                packages.append({
                    "name": parts[0],
                    "version": parts[1],
                    "arch": parts[2],
                })

        artifact = EvidenceArtifact(
            control_id="INV-1.0",
            framework="internal",
            title="Installed Packages Inventory",
            collection_time=self.timestamp,
            hostname=self.hostname,
            data={
                "total_packages": len(packages),
                "packages": packages,
            },
        )
        artifact.compute_hash()
        self.artifacts.append(artifact)

    def _collect_file_permissions(self):
        """CIS 6.1 — Critical file permissions."""
        critical_files = [
            "/etc/passwd", "/etc/shadow", "/etc/group", "/etc/gshadow",
            "/etc/ssh/sshd_config", "/etc/crontab", "/boot/grub/grub.cfg",
        ]

        permissions = []
        for filepath in critical_files:
            path = Path(filepath)
            if path.exists():
                stat = path.stat()
                permissions.append({
                    "path": filepath,
                    "mode": oct(stat.st_mode)[-4:],
                    "owner_uid": stat.st_uid,
                    "group_gid": stat.st_gid,
                })

        artifact = EvidenceArtifact(
            control_id="CIS-6.1",
            framework="CIS-Ubuntu-22.04-L1",
            title="Critical File Permissions",
            collection_time=self.timestamp,
            hostname=self.hostname,
            data={"files": permissions},
        )
        artifact.compute_hash()
        self.artifacts.append(artifact)

    def _collect_audit_config(self):
        """CIS 4.1 — Audit configuration."""
        rules_result = subprocess.run(
            ["auditctl", "-l"],
            capture_output=True, text=True,
        )

        status_result = subprocess.run(
            ["auditctl", "-s"],
            capture_output=True, text=True,
        )

        artifact = EvidenceArtifact(
            control_id="CIS-4.1",
            framework="CIS-Ubuntu-22.04-L1",
            title="Audit System Configuration",
            collection_time=self.timestamp,
            hostname=self.hostname,
            data={
                "audit_rules": rules_result.stdout if rules_result.returncode == 0 else "auditd not configured",
                "audit_status": status_result.stdout if status_result.returncode == 0 else "auditd not running",
            },
        )
        artifact.compute_hash()
        self.artifacts.append(artifact)

    def _collect_network_config(self):
        """CIS 3.x — Network configuration."""
        sysctl_result = subprocess.run(
            ["sysctl", "-a"],
            capture_output=True, text=True,
        )

        # Filter security-relevant parameters
        security_params = {}
        relevant_prefixes = ["net.ipv4", "net.ipv6", "kernel.randomize", "kernel.kptr", "fs.suid"]
        for line in sysctl_result.stdout.split("\n"):
            for prefix in relevant_prefixes:
                if line.startswith(prefix):
                    parts = line.split(" = ", 1)
                    if len(parts) == 2:
                        security_params[parts[0].strip()] = parts[1].strip()

        artifact = EvidenceArtifact(
            control_id="CIS-3.1",
            framework="CIS-Ubuntu-22.04-L1",
            title="Network Security Parameters",
            collection_time=self.timestamp,
            hostname=self.hostname,
            data={"sysctl_params": security_params},
        )
        artifact.compute_hash()
        self.artifacts.append(artifact)

    def _collect_cron_jobs(self):
        """CIS 5.1 — Cron configuration."""
        cron_data = {"system_crontab": "", "user_crontabs": {}}

        crontab_path = Path("/etc/crontab")
        if crontab_path.exists():
            cron_data["system_crontab"] = crontab_path.read_text()

        cron_dir = Path("/var/spool/cron/crontabs")
        if cron_dir.exists():
            for cron_file in cron_dir.iterdir():
                cron_data["user_crontabs"][cron_file.name] = cron_file.read_text()

        artifact = EvidenceArtifact(
            control_id="CIS-5.1",
            framework="CIS-Ubuntu-22.04-L1",
            title="Cron Job Configuration",
            collection_time=self.timestamp,
            hostname=self.hostname,
            data=cron_data,
        )
        artifact.compute_hash()
        self.artifacts.append(artifact)

    def _collect_kernel_params(self):
        """Kernel security configuration."""
        result = subprocess.run(
            ["uname", "-a"],
            capture_output=True, text=True, check=True,
        )

        artifact = EvidenceArtifact(
            control_id="CIS-1.5",
            framework="CIS-Ubuntu-22.04-L1",
            title="Kernel Configuration",
            collection_time=self.timestamp,
            hostname=self.hostname,
            data={"kernel_version": result.stdout.strip()},
        )
        artifact.compute_hash()
        self.artifacts.append(artifact)

    @staticmethod
    def _user_has_password(username: str) -> bool:
        """Check if user has a password set."""
        result = subprocess.run(
            ["passwd", "-S", username],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return "P" in result.stdout.split()[1]
        return False

    def package_evidence(self) -> str:
        """Package all evidence into a signed archive."""
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive_name = f"evidence-{self.hostname}-{timestamp_str}"
        archive_path = self.output_dir / f"{archive_name}.tar.gz"

        # Write individual evidence files
        evidence_dir = self.output_dir / archive_name
        evidence_dir.mkdir(exist_ok=True)

        manifest = []
        for artifact in self.artifacts:
            filename = f"{artifact.control_id.replace('.', '-')}_{artifact.title.replace(' ', '_')}.json"
            filepath = evidence_dir / filename
            filepath.write_text(json.dumps({
                "control_id": artifact.control_id,
                "framework": artifact.framework,
                "title": artifact.title,
                "collection_time": artifact.collection_time,
                "hostname": artifact.hostname,
                "sha256": artifact.sha256,
                "collector": artifact.collector,
                "data": artifact.data,
            }, indent=2, default=str))

            manifest.append({
                "file": filename,
                "control_id": artifact.control_id,
                "sha256": artifact.sha256,
            })

        # Write manifest
        manifest_path = evidence_dir / "MANIFEST.json"
        manifest_path.write_text(json.dumps({
            "generated": self.timestamp,
            "hostname": self.hostname,
            "total_artifacts": len(self.artifacts),
            "artifacts": manifest,
        }, indent=2))

        # Create tar archive
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(evidence_dir, arcname=archive_name)

        return str(archive_path)


if __name__ == "__main__":
    collector = ComplianceEvidenceCollector()
    collector.collect_all()
    archive = collector.package_evidence()
    print(f"Evidence packaged: {archive}")
```

### Regulatory Mapping Automation

```yaml
# compliance/regulatory-mapping.yml
---
# Maps CIS Controls → NIST CSF → ISO 27001 for automated cross-framework reporting
mappings:
  - cis_control: "CIS-5.2"
    cis_title: "SSH Server Configuration"
    nist_csf:
      - id: "PR.AC-3"
        title: "Remote access is managed"
      - id: "PR.AC-7"
        title: "Users, devices, and other assets are authenticated"
    iso_27001:
      - id: "A.9.1.2"
        title: "Access to networks and network services"
      - id: "A.13.1.1"
        title: "Network controls"
    evidence_types:
      - sshd_config_snapshot
      - ssh_key_inventory
      - login_audit_logs

  - cis_control: "CIS-3.5"
    cis_title: "Firewall Configuration"
    nist_csf:
      - id: "PR.AC-5"
        title: "Network integrity is protected"
      - id: "DE.CM-1"
        title: "The network is monitored"
    iso_27001:
      - id: "A.13.1.1"
        title: "Network controls"
      - id: "A.13.1.3"
        title: "Segregation in networks"
    evidence_types:
      - firewall_ruleset
      - network_flow_logs
      - zone_architecture_diagram

  - cis_control: "CIS-4.1"
    cis_title: "Audit and Logging"
    nist_csf:
      - id: "DE.AE-3"
        title: "Event data are collected and correlated"
      - id: "PR.PT-1"
        title: "Audit/log records are maintained"
    iso_27001:
      - id: "A.12.4.1"
        title: "Event logging"
      - id: "A.12.4.3"
        title: "Administrator and operator logs"
    evidence_types:
      - audit_rules_config
      - log_retention_policy
      - siem_integration_proof

  - cis_control: "CIS-6.1"
    cis_title: "File Permissions"
    nist_csf:
      - id: "PR.AC-4"
        title: "Access permissions and authorizations are managed"
      - id: "PR.DS-5"
        title: "Protections against data leaks"
    iso_27001:
      - id: "A.9.4.1"
        title: "Information access restriction"
      - id: "A.12.6.2"
        title: "Restrictions on software installation"
    evidence_types:
      - file_permission_scan
      - suid_sgid_inventory
      - world_writable_report
```

---

## 10. Laboratorio

### Lab Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LAB ENVIRONMENT                                   │
│                                                                           │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐           │
│  │   Ansible     │    │    Wazuh      │    │    MISP       │           │
│  │ Control Node  │    │   Manager     │    │  Threat Intel │           │
│  │               │    │  + Dashboard  │    │               │           │
│  │ 10.0.1.10     │    │  10.0.1.20    │    │  10.0.1.40    │           │
│  └───────┬───────┘    └───────┬───────┘    └───────┬───────┘           │
│          │                    │                    │                     │
│  ────────┼────────────────────┼────────────────────┼─── Management ──── │
│          │                    │                    │     10.0.1.0/24     │
│  ┌───────┴───────┐    ┌──────┴────────┐    ┌─────┴─────────┐          │
│  │  TheHive +    │    │   Shuffle     │    │  Target VMs   │          │
│  │   Cortex      │    │   SOAR        │    │               │          │
│  │               │    │               │    │  Ubuntu 22.04 │          │
│  │  10.0.1.30    │    │  10.0.1.50    │    │  10.0.2.0/24  │          │
│  └───────────────┘    └───────────────┘    └───────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Lab Deployment — Docker Compose

```yaml
# lab/docker-compose.yml
---
version: "3.8"

networks:
  lab-mgmt:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.1.0/24
  lab-targets:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.2.0/24

volumes:
  wazuh-indexer-data:
  thehive-data:
  cortex-data:
  misp-db-data:
  misp-data:
  shuffle-opensearch-data:
  shuffle-files:

services:
  # === Wazuh Manager ===
  wazuh-manager:
    image: wazuh/wazuh-manager:4.7.2
    container_name: wazuh-manager
    hostname: wazuh-manager
    networks:
      lab-mgmt:
        ipv4_address: 10.0.1.20
    ports:
      - "1514:1514"
      - "1515:1515"
      - "514:514/udp"
      - "55000:55000"
    environment:
      - INDEXER_URL=https://wazuh-indexer:9200
      - INDEXER_USERNAME=admin
      - INDEXER_PASSWORD=${WAZUH_INDEXER_PASSWORD}
      - FILEBEAT_SSL_VERIFICATION_MODE=none
    volumes:
      - ./wazuh/ossec.conf:/var/ossec/etc/ossec.conf
      - ./wazuh/rules:/var/ossec/etc/rules
    restart: unless-stopped

  wazuh-indexer:
    image: wazuh/wazuh-indexer:4.7.2
    container_name: wazuh-indexer
    hostname: wazuh-indexer
    networks:
      lab-mgmt:
    environment:
      - OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g
      - bootstrap.memory_lock=true
      - discovery.type=single-node
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - wazuh-indexer-data:/var/lib/wazuh-indexer
    restart: unless-stopped

  wazuh-dashboard:
    image: wazuh/wazuh-dashboard:4.7.2
    container_name: wazuh-dashboard
    hostname: wazuh-dashboard
    networks:
      lab-mgmt:
    ports:
      - "443:5601"
    environment:
      - INDEXER_USERNAME=admin
      - INDEXER_PASSWORD=${WAZUH_INDEXER_PASSWORD}
      - WAZUH_API_URL=https://wazuh-manager:55000
    depends_on:
      - wazuh-indexer
      - wazuh-manager
    restart: unless-stopped

  # === TheHive ===
  thehive:
    image: strangebee/thehive:5.2
    container_name: thehive
    hostname: thehive
    networks:
      lab-mgmt:
        ipv4_address: 10.0.1.30
    ports:
      - "9000:9000"
    environment:
      - TH_SECRET=${THEHIVE_SECRET}
      - TH_NO_CONFIG_CORTEX=false
      - TH_CORTEX_URL=http://cortex:9001
    volumes:
      - thehive-data:/opt/thp/thehive/data
      - ./thehive/application.conf:/etc/thehive/application.conf
    depends_on:
      - thehive-db
      - cortex
    restart: unless-stopped

  thehive-db:
    image: cassandra:4.1
    container_name: thehive-db
    hostname: thehive-db
    networks:
      lab-mgmt:
    environment:
      - CASSANDRA_CLUSTER_NAME=TheHive
      - MAX_HEAP_SIZE=1G
      - HEAP_NEWSIZE=256M
    volumes:
      - thehive-data:/var/lib/cassandra
    restart: unless-stopped

  # === Cortex (Analyzers + Responders) ===
  cortex:
    image: thehiveproject/cortex:3.1.7
    container_name: cortex
    hostname: cortex
    networks:
      lab-mgmt:
    ports:
      - "9001:9001"
    environment:
      - job_directory=/opt/cortex/jobs
    volumes:
      - cortex-data:/opt/cortex/data
      - /var/run/docker.sock:/var/run/docker.sock
      - ./cortex/application.conf:/etc/cortex/application.conf
    restart: unless-stopped

  # === MISP ===
  misp-core:
    image: ghcr.io/misp/misp-docker/misp-core:latest
    container_name: misp-core
    hostname: misp
    networks:
      lab-mgmt:
        ipv4_address: 10.0.1.40
    ports:
      - "8443:443"
      - "8080:80"
    environment:
      - MISP_ADMIN_EMAIL=admin@lab.local
      - MISP_ADMIN_PASSPHRASE=${MISP_ADMIN_PASSWORD}
      - MISP_BASEURL=https://misp.lab.local
    volumes:
      - misp-data:/var/www/MISP/app/files
    depends_on:
      - misp-db
      - misp-redis
    restart: unless-stopped

  misp-db:
    image: mariadb:10.11
    container_name: misp-db
    networks:
      lab-mgmt:
    environment:
      - MYSQL_ROOT_PASSWORD=${MISP_DB_ROOT_PASSWORD}
      - MYSQL_DATABASE=misp
      - MYSQL_USER=misp
      - MYSQL_PASSWORD=${MISP_DB_PASSWORD}
    volumes:
      - misp-db-data:/var/lib/mysql
    restart: unless-stopped

  misp-redis:
    image: redis:7-alpine
    container_name: misp-redis
    networks:
      lab-mgmt:
    restart: unless-stopped

  # === Shuffle SOAR ===
  shuffle-backend:
    image: ghcr.io/shuffle/shuffle-backend:latest
    container_name: shuffle-backend
    hostname: shuffle-backend
    networks:
      lab-mgmt:
        ipv4_address: 10.0.1.50
    ports:
      - "5001:5001"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - shuffle-files:/shuffle-files
    environment:
      - SHUFFLE_OPENSEARCH_URL=https://shuffle-opensearch:9200
      - SHUFFLE_DEFAULT_USERNAME=admin
      - SHUFFLE_DEFAULT_PASSWORD=${SHUFFLE_ADMIN_PASSWORD}
    depends_on:
      - shuffle-opensearch
    restart: unless-stopped

  shuffle-frontend:
    image: ghcr.io/shuffle/shuffle-frontend:latest
    container_name: shuffle-frontend
    networks:
      lab-mgmt:
    ports:
      - "3443:443"
      - "3001:80"
    environment:
      - BACKEND_HOSTNAME=shuffle-backend
    depends_on:
      - shuffle-backend
    restart: unless-stopped

  shuffle-orborus:
    image: ghcr.io/shuffle/shuffle-orborus:latest
    container_name: shuffle-orborus
    networks:
      lab-mgmt:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - BASE_URL=http://shuffle-backend:5001
      - SHUFFLE_WORKER_VERSION=latest
      - ENVIRONMENT_NAME=Lab
      - ORG_ID=Lab
      - CLEANUP=true
    depends_on:
      - shuffle-backend
    restart: unless-stopped

  shuffle-opensearch:
    image: opensearchproject/opensearch:2.11.0
    container_name: shuffle-opensearch
    networks:
      lab-mgmt:
    environment:
      - cluster.name=shuffle-cluster
      - node.name=shuffle-opensearch
      - discovery.type=single-node
      - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
      - DISABLE_INSTALL_DEMO_CONFIG=true
      - DISABLE_SECURITY_PLUGIN=true
    volumes:
      - shuffle-opensearch-data:/usr/share/opensearch/data
    restart: unless-stopped

  # === Target VMs (vulnerable for testing) ===
  target-ubuntu:
    image: ubuntu:22.04
    container_name: target-ubuntu
    hostname: target-ubuntu
    networks:
      lab-targets:
        ipv4_address: 10.0.2.10
      lab-mgmt:
    command: /bin/bash -c "apt-get update && apt-get install -y openssh-server && /usr/sbin/sshd -D"
    restart: unless-stopped
```

### Lab Exercise — End-to-End Automation Pipeline

```yaml
# lab/ansible/playbooks/full-pipeline.yml
# Exercise: CIS hardening → vuln scan → alert → SOAR → containment → verification
---
# STEP 1: Apply CIS hardening
- name: "STEP 1 — Apply CIS hardening to target hosts"
  hosts: lab_targets
  become: true
  tags: [step1, hardening]

  roles:
    - role: linux-hardening
      vars:
        management_network: "10.0.1.0/24"
        wazuh_manager_ip: "10.0.1.20"

  post_tasks:
    - name: Install Wazuh agent
      ansible.builtin.apt:
        deb: "https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.7.2-1_amd64.deb"
      environment:
        WAZUH_MANAGER: "10.0.1.20"
        WAZUH_AGENT_GROUP: "linux-servers"

    - name: Start Wazuh agent
      ansible.builtin.systemd:
        name: wazuh-agent
        state: started
        enabled: true

# STEP 2: Run vulnerability scan
- name: "STEP 2 — Vulnerability scan with OpenSCAP"
  hosts: lab_targets
  become: true
  tags: [step2, scan]

  tasks:
    - name: Install OpenSCAP
      ansible.builtin.apt:
        name: [libopenscap8, openscap-scanner, ssg-base, ssg-debderived]
        state: present
        update_cache: true

    - name: Run OpenSCAP vulnerability scan
      ansible.builtin.command:
        cmd: >
          oscap oval eval
          --results /tmp/oval-results.xml
          --report /tmp/oval-report.html
          /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-oval.xml
      register: oval_scan
      changed_when: false
      failed_when: false

    - name: Extract vulnerabilities found
      ansible.builtin.shell: |
        set -o pipefail
        grep -c 'result="true"' /tmp/oval-results.xml || echo 0
      register: vuln_count
      changed_when: false

    - name: Send scan results to Wazuh
      ansible.builtin.copy:
        content: |
          {"type": "vulnerability_scan", "host": "{{ inventory_hostname }}",
           "vulnerabilities_found": {{ vuln_count.stdout }},
           "timestamp": "{{ ansible_date_time.iso8601 }}"}
        dest: /var/ossec/logs/active-responses/scan-results.json
        mode: '0640'

# STEP 3: Simulate alert → SOAR picks up
- name: "STEP 3 — Trigger Wazuh alert for SOAR ingestion"
  hosts: lab_targets
  become: true
  tags: [step3, alert]

  tasks:
    - name: Simulate suspicious activity (trigger Wazuh rule)
      ansible.builtin.shell: |
        # Simulate brute force (triggers Wazuh rule 5712)
        for i in $(seq 1 6); do
          logger -p auth.warning "Failed password for invalid user attacker from 203.0.113.{{ 100 + i }} port 22 ssh2"
        done
      changed_when: true

    - name: Wait for alert propagation
      ansible.builtin.pause:
        seconds: 15

# STEP 4: Verify SOAR received and processed alert
- name: "STEP 4 — Verify SOAR automation triggered"
  hosts: localhost
  gather_facts: false
  tags: [step4, verify-soar]

  tasks:
    - name: Check Shuffle workflow execution
      ansible.builtin.uri:
        url: "http://10.0.1.50:5001/api/v1/workflows/executions"
        headers:
          Authorization: "Bearer {{ shuffle_api_key }}"
        method: GET
        status_code: 200
      register: shuffle_executions
      retries: 5
      delay: 10
      until: shuffle_executions.json | length > 0

    - name: Verify TheHive case created
      ansible.builtin.uri:
        url: "http://10.0.1.30:9000/api/v1/query"
        headers:
          Authorization: "Bearer {{ thehive_api_key }}"
        method: POST
        body_format: json
        body:
          query:
            - _name: listCase
            - _name: filter
              _and:
                - _field: title
                  _value: "*brute*force*"
        status_code: 200
      register: thehive_cases

    - name: Assert case was created
      ansible.builtin.assert:
        that:
          - thehive_cases.json | length > 0
        fail_msg: "TheHive case not created — SOAR pipeline broken"

# STEP 5: Run compliance verification after remediation
- name: "STEP 5 — Post-remediation compliance verification"
  hosts: lab_targets
  become: true
  tags: [step5, compliance]

  tasks:
    - name: Run CIS benchmark evaluation
      ansible.builtin.command:
        cmd: >
          oscap xccdf eval
          --profile xccdf_org.ssgproject.content_profile_cis_level1_server
          --results /tmp/cis-post-results.xml
          --report /tmp/cis-post-report.html
          /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
      register: cis_eval
      changed_when: false
      failed_when: cis_eval.rc not in [0, 2]

    - name: Parse compliance score
      ansible.builtin.shell: |
        set -o pipefail
        grep -oP 'score.*?>\K[0-9.]+' /tmp/cis-post-results.xml | tail -1
      register: compliance_score
      changed_when: false

    - name: Display compliance score
      ansible.builtin.debug:
        msg: "Compliance score: {{ compliance_score.stdout }}%"

    - name: Assert minimum compliance threshold
      ansible.builtin.assert:
        that:
          - compliance_score.stdout | float >= 85.0
        fail_msg: "Compliance score {{ compliance_score.stdout }}% below 85% threshold"
        success_msg: "Compliance verification PASSED: {{ compliance_score.stdout }}%"

    - name: Generate final report
      ansible.builtin.template:
        src: final-report.j2
        dest: /var/log/compliance/lab-pipeline-report-{{ ansible_date_time.iso8601_basic_short }}.json
        mode: '0640'
```

### Lab Shuffle Workflow — Wazuh Alert to Containment

```json
{
  "name": "Wazuh Alert → Enrich → Contain → Case",
  "description": "Automated response to Wazuh high-severity alerts",
  "triggers": [
    {
      "type": "webhook",
      "name": "wazuh_webhook",
      "environment": "Lab"
    }
  ],
  "actions": [
    {
      "id": "parse_alert",
      "name": "Parse Wazuh Alert",
      "app_name": "Shuffle Tools",
      "app_action": "parse_json",
      "parameters": {
        "input": "$exec.wazuh_webhook"
      }
    },
    {
      "id": "enrich_ip",
      "name": "Enrich Source IP",
      "app_name": "AbuseIPDB",
      "app_action": "check_ip",
      "parameters": {
        "ip": "$parse_alert.data.srcip",
        "max_age_in_days": "90"
      },
      "conditions": {
        "source": "$parse_alert.data.srcip",
        "condition": "is_not_empty"
      }
    },
    {
      "id": "check_threshold",
      "name": "Check if Auto-Block Threshold Met",
      "app_name": "Shuffle Tools",
      "app_action": "compare_values",
      "parameters": {
        "value1": "$enrich_ip.data.abuseConfidenceScore",
        "operator": ">=",
        "value2": "75"
      }
    },
    {
      "id": "block_ip",
      "name": "Block IP on Firewall",
      "app_name": "HTTP",
      "app_action": "POST",
      "parameters": {
        "url": "http://10.0.1.10:8080/api/firewall/block",
        "headers": "Authorization: Bearer $workflow.variables.fw_token",
        "body": "{\"ip\": \"$parse_alert.data.srcip\", \"comment\": \"Auto-blocked by SOAR — abuse score $enrich_ip.data.abuseConfidenceScore\"}"
      },
      "conditions": {
        "source": "$check_threshold.result",
        "condition": "equals",
        "value": "true"
      }
    },
    {
      "id": "create_thehive_alert",
      "name": "Create TheHive Alert",
      "app_name": "TheHive",
      "app_action": "create_alert",
      "parameters": {
        "title": "Wazuh: $parse_alert.rule.description",
        "description": "Source IP: $parse_alert.data.srcip\nRule: $parse_alert.rule.id\nAgent: $parse_alert.agent.name\nAbuseIPDB Score: $enrich_ip.data.abuseConfidenceScore",
        "severity": "3",
        "type": "wazuh_alert",
        "source": "Shuffle-SOAR",
        "sourceRef": "$parse_alert.id",
        "tags": ["wazuh", "automated", "$parse_alert.rule.groups"]
      }
    },
    {
      "id": "notify_soc",
      "name": "Notify SOC Channel",
      "app_name": "HTTP",
      "app_action": "POST",
      "parameters": {
        "url": "$workflow.variables.slack_webhook",
        "body": "{\"text\": \"🚨 SOAR Playbook Executed\\nAlert: $parse_alert.rule.description\\nSource: $parse_alert.data.srcip\\nAction: $block_ip.status_code == 200 ? 'BLOCKED' : 'ENRICHED ONLY'\\nCase: $create_thehive_alert.id\"}"
      }
    }
  ]
}
```

### Lab Exercise Checklist

```markdown
## Verifica completamento laboratorio

### Fase 1 — Infrastruttura
- [ ] Docker Compose stack running (Wazuh + TheHive + Cortex + MISP + Shuffle)
- [ ] All services reachable on management network
- [ ] Target VM deployed and SSH accessible
- [ ] Wazuh agent registered and reporting

### Fase 2 — Hardening
- [ ] Ansible playbook applies CIS L1 hardening
- [ ] SSH hardened (key-only, no root, limited retries)
- [ ] Firewall configured (default deny, management ACL)
- [ ] Auditd rules deployed
- [ ] Sysctl security parameters applied
- [ ] World-writable files remediated

### Fase 3 — Detection
- [ ] Wazuh detects simulated brute force
- [ ] Alert forwarded to Shuffle via webhook
- [ ] Alert severity correctly classified

### Fase 4 — SOAR Response
- [ ] Shuffle workflow triggers on Wazuh webhook
- [ ] AbuseIPDB enrichment returns score
- [ ] Auto-block triggered for high-confidence malicious IPs
- [ ] TheHive case created with full context
- [ ] SOC notification sent

### Fase 5 — Compliance
- [ ] OpenSCAP scan runs successfully
- [ ] Compliance score >= 85%
- [ ] Evidence artifacts collected with SHA-256 hashes
- [ ] Report generated and accessible

### Fase 6 — Integration Verification
- [ ] End-to-end pipeline: hardening → scan → alert → SOAR → contain → verify
- [ ] No manual intervention required for high-confidence threats
- [ ] Human-in-the-loop triggered for ambiguous cases
- [ ] Metrics captured (MTTR, automation rate, false positive rate)
```

---

## Auto-valutazione

1. Describe the four levels of security automation maturity. Where does your organization sit today?
2. Explain how Ansible Vault protects secrets in playbooks. What is the risk of not using it?
3. Design a SOAR playbook for ransomware detection that includes: isolation, evidence preservation, and executive notification. What human gates would you include?
4. What is the difference between Checkov, tfsec, and KICS? When would you use each?
5. Explain the STIX/TAXII protocol. How does MISP implement threat intelligence sharing?
6. What is infrastructure drift? Why is security-relevant drift more dangerous than cosmetic drift?
7. Design a CI/CD pipeline that implements SLSA Level 3 provenance. What attestations are required?
8. How does the CIS benchmark differ from NIST CSF? How do you automate cross-framework compliance mapping?

---

## Letture primarie

- Ansible Security Automation documentation — https://docs.ansible.com/ansible/latest/collections/ansible/posix/
- CIS Benchmarks — https://www.cisecurity.org/cis-benchmarks
- NIST SP 800-53 Rev 5 — Security and Privacy Controls
- TheHive Project documentation — https://docs.strangebee.com/
- Cortex XSOAR documentation — https://xsoar.pan.dev/docs/
- Shuffle SOAR — https://shuffler.io/docs
- MISP Project — https://www.misp-project.org/documentation/
- STIX/TAXII specification — https://oasis-open.github.io/cti-documentation/
- Terraform security best practices — https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement
- SLSA framework — https://slsa.dev/
- Sigstore/cosign — https://docs.sigstore.dev/
- Chef InSpec documentation — https://docs.chef.io/inspec/
- OpenSCAP — https://www.open-scap.org/
- Checkov — https://www.checkov.io/
- OPA/Rego — https://www.openpolicyagent.org/docs/latest/

---

## Collegamenti incrociati

- Modulo 05 — `05-sicurezza-operativa.md` — fondamenti sicurezza operativa
- Modulo 07 — `07-monitoraggio-incidenti.md` — incident management base
- Modulo 23 — `23-change-automation-validation.md` — change automation
- Modulo 06 — `06-backup-disaster-recovery.md` — recovery procedures

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **SOAR** | Security Orchestration, Automation and Response — piattaforma che orchestra risposte automatizzate ad incidenti |
| **IaC** | Infrastructure as Code — gestione infrastruttura tramite file dichiarativi versionati |
| **CIS Benchmark** | Center for Internet Security Benchmark — standard di hardening per sistemi operativi e applicazioni |
| **STIX** | Structured Threat Information eXpression — linguaggio per descrivere threat intelligence |
| **TAXII** | Trusted Automated eXchange of Intelligence Information — protocollo di trasporto per STIX |
| **OPA** | Open Policy Agent — motore policy-as-code general-purpose |
| **Rego** | Linguaggio di policy per OPA |
| **SLSA** | Supply-chain Levels for Software Artifacts — framework per supply chain security |
| **Sentinel** | HashiCorp policy-as-code framework per Terraform Enterprise |
| **IOC** | Indicator of Compromise — artefatto osservabile che indica compromissione |
| **TLP** | Traffic Light Protocol — classificazione per condivisione intelligence (RED/AMBER/GREEN/WHITE) |
| **MTTR** | Mean Time To Respond — tempo medio di risposta ad un incidente |
| **Drift** | Differenza tra stato desiderato (IaC) e stato reale dell'infrastruttura |
| **Playbook** | Workflow automatizzato che definisce sequenza di azioni per risposta ad incidenti |
| **Analyzer** | Componente Cortex che arricchisce observables con intelligence esterna |
| **Responder** | Componente Cortex che esegue azioni di containment/remediation |
| **Idempotent** | Proprietà di un'operazione che produce lo stesso risultato indipendentemente dal numero di esecuzioni |
