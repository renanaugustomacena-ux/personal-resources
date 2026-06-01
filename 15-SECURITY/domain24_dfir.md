---
corso: "Cybersecurity Masterclass"
fase: "Domain 24 — Digital Forensics and Incident Response"
modulo: "24.1"
titolo: "Digital Forensics and Incident Response"
versione: "Volatility 3 v2.27 / Velociraptor 0.76 / KAPE 2025 / Plaso 20250401"
livello: "Advanced"
prerequisiti:
  - "Operating system internals (filesystems, process model, virtual memory)"
  - "Networking fundamentals (TCP/IP, DNS, HTTP/TLS)"
  - "Familiarity with Linux and Windows command-line environments"
  - "Basic understanding of malware behavior and persistence mechanisms"
  - "Introductory knowledge of SIEM and log-management platforms"
obiettivi:
  - "Acquire forensic disk images using write-blocking and cryptographic verification, and parse NTFS/ext4/APFS artifacts to reconstruct file-system activity"
  - "Perform Windows and Linux memory forensics with Volatility 3, detecting process injection, DKOM rootkits, and fileless malware"
  - "Detect and attribute anti-forensics techniques including timestomping, log clearing, MFT manipulation, and encrypted-container usage"
  - "Build and analyze super-timelines with Plaso/Timesketch, applying windowing methodology and pivot-point identification to scope incidents"
  - "Execute the full PICERL/NIST 800-61 IR lifecycle using Velociraptor, KAPE, GRR, and osquery for evidence acquisition, containment, and threat hunting"
tag: [security, dfir, forensics, memory-forensics, incident-response, volatility, velociraptor, timeline-analysis, threat-hunting]
---

# Domain 24 — Digital Forensics and Incident Response

> **After completing this module, the student will be able to:**
>
> 1. Acquire forensic disk images using write-blocking and cryptographic verification, and parse NTFS/ext4/APFS artifacts to reconstruct file-system activity.
> 2. Perform Windows and Linux memory forensics with Volatility 3, detecting process injection, DKOM rootkits, and fileless malware.
> 3. Detect and attribute anti-forensics techniques including timestomping, log clearing, MFT manipulation, and encrypted-container usage.
> 4. Build and analyze super-timelines with Plaso/Timesketch, applying windowing methodology and pivot-point identification to scope incidents.
> 5. Execute the full PICERL/NIST 800-61 IR lifecycle using Velociraptor, KAPE, GRR, and osquery for evidence acquisition, containment, and threat hunting.

> **Scope.** Disk/filesystem forensics: NTFS ($MFT, $LogFile, $USN_JRNL, $I30 INDX slack), ext4 (superblock, inodes, journal/JBD2), APFS (container, Object Map, B-tree, checkpoints, VEK/KEK encryption). File carving (foremost, scalpel, photorec, bulk_extractor). VSS. Memory forensics: Volatility 3 (Windows/Linux/macOS plugins), LiME, osxpmem, Rekall. Anti-forensics attack techniques and detection: timestomping, log clearing, MFT manipulation, encrypted container forensics, event log tampering. Timeline analysis: Plaso/Timesketch, MACB timestamps, timestomping detection, windowing methodology, pivot-point identification. Log analysis: Windows Event Log, Sysmon event IDs, auditd, macOS Unified Logs, CloudTrail/Azure Monitor/GCP Audit. IR workflows: PICERL, NIST 800-61, scoping/pivoting, containment, evidence acquisition (order of volatility, imaging), Velociraptor/GRR/osquery, KAPE collection, threat hunting (ATT&CK, hypothesis-driven), YARA, Sigma rules. Threat hunting packages: lateral movement, persistence mechanism, credential access.

---

## 1. Disk and filesystem forensics

### 1.1 NTFS internals for forensics

**$MFT (Master File Table).** Every file and directory on an NTFS volume has at least one entry in the $MFT. Each MFT entry is 1024 bytes (configurable, but 1024 is standard). The entry contains a header (signature `FILE`, sequence number, link count, first attribute offset, flags — in-use or deleted) followed by a sequence of attributes.

Key attributes: **$STANDARD_INFORMATION (type 0x10)** — creation time, modification time, MFT modification time, access time, file attributes (read-only, hidden, system, archive), owner ID, security ID, USN (Update Sequence Number). **$FILE_NAME (type 0x30)** — the file name (in Unicode), parent directory reference, and a separate set of timestamps (creation, modification, access, MFT modification). A file can have multiple $FILE_NAME attributes (for the 8.3 short name and the long name). **$DATA (type 0x80)** — the file's content. For small files (< ~700 bytes), the data is stored resident (inline in the MFT entry). For larger files, the $DATA attribute contains a run list (a sequence of cluster runs: starting cluster + length) pointing to the file's data on disk. **$OBJECT_ID (type 0x40)** — a GUID assigned to the file (used for distributed link tracking).

**Forensic significance of dual timestamps.** $STANDARD_INFORMATION timestamps are easily modified by user-mode APIs (`SetFileTime`). $FILE_NAME timestamps are updated only by the NTFS driver during specific operations (rename, move, create). Comparing $SI and $FN timestamps reveals **timestomping**: if $SI timestamps are earlier than $FN timestamps (the modification time in $SI is before the file's creation time in $FN), the $SI timestamps have been manipulated. This is a primary anti-forensics detection technique.

**$LogFile.** The NTFS transactional journal: records all metadata changes (MFT entry modifications, index updates, attribute changes) as redo and undo records. The $LogFile allows NTFS to recover from crashes (replaying committed transactions and undoing uncommitted ones). Forensic value: the $LogFile contains historical metadata states — even if the current MFT entry has been modified (timestomped, deleted, overwritten), the $LogFile may contain earlier versions.

**$UsnJrnl (Update Sequence Number Journal).** A change journal that records file-system operations: file creation, deletion, rename, modification, attribute change. Each entry contains: the file's MFT reference number, the parent directory's MFT reference, the USN (a monotonically-increasing sequence number), the timestamp, the reason (bit flags: `USN_REASON_FILE_CREATE`, `USN_REASON_FILE_DELETE`, `USN_REASON_DATA_OVERWRITE`, `USN_REASON_RENAME_OLD_NAME`, `USN_REASON_RENAME_NEW_NAME`, etc.), and the file name.

$UsnJrnl is stored in `$Extend\$UsnJrnl` and consists of two data streams: `$J` (the journal data — the actual entries) and `$Max` (metadata: maximum journal size, allocation delta). The journal is circular: old entries are overwritten when the journal reaches its maximum size. Depending on the volume's activity, the journal may contain days to weeks of history.

Forensic use: constructing a timeline of file operations (creation, modification, deletion, rename) with precise timestamps and file names. $UsnJrnl is particularly valuable because: it records events that leave no trace in the MFT (e.g., a file that was created, used, and deleted — the MFT entry may be reallocated, but the $UsnJrnl entry persists until overwritten by the circular buffer).

**$I30 index and INDX slack.** Directory entries in NTFS are stored in B-tree indexes. The $I30 attribute (type 0x90) is the index root; for large directories, $INDEX_ALLOCATION (type 0xA0) stores additional index entries in INDX records (4096-byte blocks). When a file is deleted from a directory, its index entry is removed from the B-tree — but the B-tree rebalancing may leave the deleted entry's data in the **INDX slack space** (unused space at the end of an INDX record, or in deallocated but not zeroed portions of the record). Parsing INDX slack recovers the names, MFT references, and timestamps of deleted files — even if the MFT entry has been reallocated.

### 1.1.1 NTFS artifact extraction — tool commands

**MFTECmd for $MFT parsing.** MFTECmd (from Eric Zimmerman's suite) parses the raw $MFT file (extracted via FTK Imager, `RawCopy.exe`, or Velociraptor's `Windows.NTFS.MFT` artifact) and produces structured output including both $SI and $FN timestamps, resident data indicators, ADS names, and in-use/deleted status. The basic CSV export:

```
MFTECmd.exe -f C:\Evidence\$MFT --csv C:\Output --csvf mft_parsed.csv
```

The resulting CSV contains one row per MFT entry with columns for entry number, sequence number, parent entry, in-use flag, filename, $SI timestamps, $FN timestamps, file size, and $DATA residency. For JSON output:

```
MFTECmd.exe -f C:\Evidence\$MFT --json C:\Output --jsonf mft_parsed.json
```

MFTECmd also flags potential timestomping by comparing $SI and $FN timestamps internally. Entries where the $SI Created timestamp predates the $FN Created timestamp are flagged in the output, providing an immediate indicator of anti-forensics activity without requiring the analyst to write custom comparison logic.

**MFTECmd for $UsnJrnl parsing.** The $UsnJrnl's `$J` data stream is extracted as a raw file (using FTK Imager to export `$Extend\$UsnJrnl:$J`). MFTECmd parses it with the `--usn` flag, which switches the parser to expect USN Journal V2/V3 record format:

```
MFTECmd.exe -f C:\Evidence\$J --csv C:\Output --csvf usnjrnl_parsed.csv
```

The output contains one row per journal entry: the entry offset, the file's MFT reference and parent MFT reference, the timestamp, the update reason flags (decoded to human-readable strings like `FileCreate`, `DataOverwrite`, `RenameNewName`, `SecurityChange`, `Close`), the update source flags, and the filename. Filtering this output by timestamp range and reason flags reveals the sequence of file-system operations during the incident window. For example, filtering for `RenameOldName` and `RenameNewName` in sequence reveals file renames that an attacker used to disguise dropped tools.

**INDX parsing with INDXParse.py.** The $I30 index records (including slack space) are parsed using INDXParse.py from the `indxparse` project by Willi Ballenthin. The tool reads raw INDX record data and extracts both active and deleted (slack) directory entries. To parse INDX records from a specific directory, the analyst first extracts the raw $I30 data using `icat` from The Sleuth Kit (passing the MFT entry number of the target directory and the $INDEX_ALLOCATION attribute type) and then feeds it to INDXParse:

```
icat -o 2048 image.raw 36543-160 > indx_raw.bin
python INDXParse.py indx_raw.bin
```

The output includes the filename, parent directory reference, file size, and all four timestamps for each entry found — both entries in active B-tree nodes and entries recovered from slack space. Deleted entries recovered from slack provide evidence of files that existed in the directory before being deleted, even if the MFT entry was subsequently overwritten.

### 1.1.2 Forensic acquisition workflow

Sound forensic acquisition requires write-blocking the source media, creating a bit-for-bit copy, and verifying integrity via cryptographic hashing.

**Write-blocking.** On Linux, `blockdev` sets the device's read-only flag at the kernel level before any imaging tool accesses it:

```bash
blockdev --setro /dev/sdb
blockdev --getro /dev/sdb  # should return 1
```

This must be done before mounting or imaging. Hardware write-blockers (Tableau, CRU WiebeTech) provide stronger assurance and are preferred for evidentiary work because they block writes at the hardware interface level, independent of the operating system's cooperation.

**dc3dd with hash verification.** dc3dd (from the Department of Defense Cyber Crime Center) is a forensic fork of `dd` that adds on-the-fly hashing, split output, and progress reporting. A typical acquisition command hashes the input as it reads and writes a raw image:

```bash
dc3dd if=/dev/sdb of=/evidence/disk.raw hash=sha256 log=/evidence/acquisition.log
```

The `hash=sha256` flag computes a running SHA-256 hash of the input data and appends it to the log file. The log includes the source device, the start and end times, the total bytes read and written, and the hash value. For subsequent verification, the analyst re-hashes the output image and compares:

```bash
sha256sum /evidence/disk.raw
```

If the image hash matches the acquisition hash, the image is an exact copy of the source. dc3dd also supports split output for large disks where the output filesystem cannot hold a single file exceeding a size limit:

```bash
dc3dd if=/dev/sdb ofs=/evidence/disk.raw.000 ofsz=4G hash=sha256 log=/evidence/acquisition.log
```

This splits the output into 4 GB chunks, each with sequential numbering.

**ewfacquire for E01 format.** The EnCase Evidence File (E01) format provides compression, integrated hashing (both per-segment and global), and case metadata (examiner name, case number, evidence number, description, notes). The `ewfacquire` tool from the libewf library creates E01 images:

```bash
ewfacquire /dev/sdb -t /evidence/disk -f encase6 -c deflate:best \
  -C "Case-2026-0508" -D "Suspect workstation primary drive" \
  -e "Forensic Examiner" -E "EV-001" -m removable -S 2G
```

The `-t` flag sets the output base filename (`.E01` extension is appended automatically), `-f encase6` selects the EnCase 6/7 compatible format, `-c deflate:best` applies maximum compression, `-C` through `-E` set case metadata embedded in the image header, `-m` sets the media type, and `-S 2G` splits the output into 2 GB segments. ewfacquire computes MD5 and SHA-1 hashes during acquisition and stores them in the E01 metadata. Verification uses `ewfverify`:

```bash
ewfverify /evidence/disk.E01
```

This recomputes the hashes and compares them against the stored values, reporting pass or fail.

### 1.2 ext4 forensics

**Superblock.** Located at byte offset 1024 (block group 0). Contains: total inode count, total block count, blocks per group, inodes per group, mount time, write time, mount count, filesystem state (clean/errors), and feature flags (has_journal, extents, flex_bg, etc.). Backup superblocks at block-group boundaries provide redundancy.

**Inodes.** Each file/directory has an inode (256 bytes in ext4). Key fields: mode (file type and permissions), owner UID/GID, size, atime/ctime/mtime/crtime (creation time — ext4-specific), block count, and extent tree (or direct/indirect block pointers for legacy mode). The **extent tree** uses a B-tree of extents (each extent: logical block offset + physical block start + length) for efficient mapping of file data to disk blocks.

**Journal (JBD2).** ext4's journaling (using the JBD2 layer) records metadata changes (and optionally data, in `data=journal` mode) as transactions. Each transaction contains: a descriptor block (listing the filesystem blocks being journaled), the journaled block data, and a commit block. The journal is circular; old transactions are overwritten. Forensic value: recovering previous inode states (timestamps, block mappings, permissions) from uncommitted or recently-committed journal transactions.

**Deletion recovery.** When a file is deleted on ext4, the inode's link count is decremented (and the inode is marked free if zero), the directory entry is removed, and the data blocks are released to the block allocator. However: the inode's block pointers (extent tree) are zeroed (making data recovery from the inode impossible — unlike ext3, which preserved them). Recovery options: journal recovery (if the inode data is in a recent journal transaction), file carving (scanning free blocks for file signatures), and $UsnJrnl-equivalent (ext4 has no built-in change journal like NTFS's $UsnJrnl — the analyst relies on the ext4 journal's limited history and external logs).

### 1.2.1 ext4 forensic tool commands

The Sleuth Kit (TSK) and `debugfs` are the primary tools for ext4 forensic examination. TSK provides a filesystem-agnostic interface, while `debugfs` is the native ext4 debugging tool that offers deeper access to ext4-specific structures.

**debugfs for inode examination.** The `debugfs` tool opens an ext4 filesystem image in read-only mode and provides an interactive shell for examining inodes, directory entries, and journal transactions. The `-R` flag allows running a single command non-interactively:

```bash
debugfs -R "ls -d -l /home/user/Documents" /evidence/partition.raw
```

The `ls -d` command lists directory entries including deleted entries (marked with angle brackets around the inode number). The `-l` flag adds long-format output with inode numbers, file types, and sizes. To examine a specific inode's metadata, including all four timestamps and block mappings:

```bash
debugfs -R "stat <12345>" /evidence/partition.raw
```

This returns the inode's mode, owner, size, link count, all timestamps (ctime, atime, mtime, crtime), the extent tree or block list, and flags. To extract a file's content by inode number (useful for recovering deleted files whose directory entry is gone but whose inode still contains valid extent data):

```bash
debugfs -R "dump <12345> /evidence/recovered_file.bin" /evidence/partition.raw
```

**Journal examination with debugfs.** The ext4 journal contains transaction records that preserve previous inode states. The `logdump` command in debugfs dumps the journal contents:

```bash
debugfs -R "logdump -a" /evidence/partition.raw
```

The `-a` flag dumps all journal blocks including their contents. The output shows each transaction's sequence number, the filesystem blocks that were journaled, and the raw block data. For targeted journal analysis of a specific inode, the `-i` flag filters to transactions affecting that inode:

```bash
debugfs -R "logdump -i <12345>" /evidence/partition.raw
```

This shows every journal transaction that modified inode 12345, allowing the analyst to trace the inode's state changes over time — previous timestamps, previous block mappings, and previous permissions.

**Sleuth Kit tools for ext4.** TSK's `istat` displays inode details in a standardized format across filesystems, and `icat` extracts file content by inode number. These are the cross-platform equivalents of debugfs commands:

```bash
istat -o 2048 /evidence/disk.raw 12345
```

The `-o 2048` flag specifies the partition offset in sectors (if the image contains a full disk with a partition table). The output includes the inode's allocation status, timestamps, size, and the list of allocated blocks. To extract a file by inode:

```bash
icat -o 2048 /evidence/disk.raw 12345 > /evidence/recovered_file.bin
```

For journal examination, TSK provides `jls` (list journal entries) and `jcat` (extract journal block content):

```bash
jls -o 2048 /evidence/disk.raw
jcat -o 2048 /evidence/disk.raw 8 42 > /evidence/journal_block_42.bin
```

The `jls` command lists all journal entries with their transaction sequence numbers and the filesystem block numbers they contain. `jcat` extracts a specific journal block by inode (8 is the journal inode on ext4) and block offset, allowing the analyst to reconstruct previous versions of filesystem structures from the journal.

### 1.3 APFS forensics

**Container and volumes.** APFS uses a container (spanning the entire partition) that hosts one or more volumes (each volume is a separate filesystem sharing the container's storage). The container superblock (`nx_superblock_t`) is at a fixed location; it points to the Object Map (a B-tree mapping object IDs to physical block addresses) and the checkpoint descriptor area (a list of recent consistent states).

**Checkpoints.** APFS uses copy-on-write with checkpoints: each metadata change creates a new version of the affected B-tree nodes without overwriting the old ones. A checkpoint captures a consistent snapshot of the entire filesystem state. Old checkpoints are retained until their blocks are reclaimed. Forensic value: previous checkpoints contain older filesystem states — deleted files, previous file content, and previous timestamps may be recoverable from old checkpoint data.

**Encryption.** APFS supports per-volume encryption. Each volume has a VEK (Volume Encryption Key — AES-256-XTS for data encryption) wrapped by a KEK (Key Encryption Key), which is in turn protected by the user's password (via PBKDF2) or a hardware key (the Secure Enclave on Apple devices). Without the password or hardware key, the volume's content is inaccessible. Forensic implication: acquiring an encrypted APFS volume requires either the user's password, a recovery key (FileVault recovery key stored in iCloud or MDM escrow), or exploitation of the Secure Enclave (extremely difficult).

### 1.3.1 APFS checkpoint recovery

APFS's copy-on-write design means that previous filesystem states persist on disk until the space they occupy is reclaimed for new data. The `apfs-fuse` tool provides read-only FUSE-based mounting of APFS containers and can access historical checkpoints. Mounting the current (latest) checkpoint:

```bash
apfs-fuse -o allow_other /evidence/apfs_partition.raw /mnt/apfs
```

To list available checkpoints and mount a specific historical one, the analyst must first enumerate the container's checkpoint descriptor area. Tools like `apfs-dump-quick` (from the apfs-fuse project) dump the container superblock and checkpoint descriptor list, showing the transaction ID (xid) and timestamp of each retained checkpoint. Once the target checkpoint is identified, mounting at that xid recovers the filesystem state as it existed at that point in time — including files that were subsequently deleted.

The forensic value of checkpoint recovery is highest on recently-wiped or modified systems: an attacker who deletes their tools and cleans up artifacts on an APFS volume may not realize that the previous checkpoint still contains the pre-deletion state. The window of recoverability depends on disk activity after the deletion — heavy writes reclaim old checkpoint blocks quickly, while an idle system may retain weeks of history.

### 1.4 File carving and VSS

**File carving.** Recovering files from unallocated space by identifying file signatures (magic bytes): JPEG (`0xFFD8FF`), PDF (`%PDF`), PNG (`0x89504E47`), ZIP/DOCX/XLSX (`0x504B0304`), ELF (`0x7F454C46`), PE (`MZ`). Tools: **foremost** (header/footer carving), **scalpel** (configurable carving rules), **photorec** (deep carving with hundreds of file-type signatures), **bulk_extractor** (feature-based extraction — scans raw disk for patterns: email addresses, URLs, credit card numbers, EXIF data, GPS coordinates, JSON, domain names — without parsing the filesystem structure).

### 1.4.1 File carving tool commands

**foremost with custom configuration.** foremost scans a raw image for file headers and footers, extracting complete files. The basic invocation for all supported types:

```bash
foremost -t all -i /evidence/disk.raw -o /evidence/carved_files
```

For custom carving rules (e.g., SQLite databases containing browser history), create a custom `foremost.conf` and pass it with `-c`:

```bash
foremost -c /evidence/custom_foremost.conf -i /evidence/disk.raw -o /evidence/carved_files
```

A custom rule in `foremost.conf` specifies the file extension, case sensitivity flag, maximum file size, header bytes, and (optionally) footer bytes. For example, a rule for SQLite databases: `sqlite  y  50000000  \x53\x51\x4c\x69\x74\x65\x20\x66\x6f\x72\x6d\x61\x74\x20\x33\x00` (the "SQLite format 3\0" header).

**bulk_extractor with specific scanners.** bulk_extractor extracts structured data features (not complete files) from raw media. Each scanner targets a specific data type. Running all scanners:

```bash
bulk_extractor -o /evidence/be_output /evidence/disk.raw
```

The output directory contains one text file per scanner (`email.txt`, `url.txt`, `domain.txt`, `ccn.txt`, `exif.txt`, `json.txt`, etc.). To run only specific scanners:

```bash
bulk_extractor -E email -E url -E domain -E json -o /evidence/be_output /evidence/disk.raw
```

The `-E` flag enables only the named scanners. For forensic triage, `email.txt` and `url.txt` outputs are immediately valuable — they reveal communication patterns and accessed resources without filesystem parsing.

**photorec CLI usage.** photorec operates in both interactive (ncurses) and command-line modes. For scripted forensic workflows, the command-line mode is preferred:

```bash
photorec /log /d /evidence/photorec_output /cmd /evidence/disk.raw partition_none,fileopt,everything,enable,search
```

The `/log` flag creates a log file, `/d` specifies the output directory, and the `/cmd` flag enables non-interactive mode with a comma-separated command string. photorec supports over 480 file formats and uses both header/footer matching and internal structure validation (checking that carved file headers are consistent with their claimed format), which produces fewer false positives than simple header-only carving.

### 1.4.2 Volume Shadow Copy access

**Volume Shadow Copies (VSS).** Windows creates periodic snapshots (shadow copies) of volumes. Each shadow copy preserves the state of all files at the snapshot time. The VSS diff area stores the blocks that have changed since the snapshot. Tools: `vssadmin list shadows` (enumerate existing shadow copies), `mklink /d C:\shadow \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\` (mount a shadow copy). Forensic use: shadow copies may contain deleted files, previous file versions, and pre-modification registry hives.

When working with a forensic image offline (not a live system), the `libvshadow` toolkit provides access to VSS data within raw or E01 images. First, enumerate available shadow copies:

```bash
vshadowinfo /evidence/ntfs_partition.raw
```

This lists all shadow copy stores found in the image, with their creation timestamps, store identifiers, and volume sizes. To mount shadow copies as virtual raw files for analysis:

```bash
vshadowmount /evidence/ntfs_partition.raw /mnt/vss_stores
```

This creates virtual device files under `/mnt/vss_stores/` — one per shadow copy (e.g., `vss1`, `vss2`). Each virtual file represents the volume as it existed at the shadow copy's creation time. The analyst then mounts each shadow copy read-only as an NTFS filesystem (via `ntfs-3g` in read-only mode) and compares file contents and timestamps across shadow copies and the current volume state:

```bash
mount -o ro,show_sys_files,streams_interface=windows /mnt/vss_stores/vss1 /mnt/shadow1
mount -o ro,show_sys_files,streams_interface=windows /mnt/vss_stores/vss2 /mnt/shadow2
```

Comparing registry hives (`SAM`, `SYSTEM`, `SOFTWARE`, `NTUSER.DAT`) across shadow copies reveals account creation, service installation, and configuration changes that occurred between snapshots. A common investigation technique is diffing the `NTUSER.DAT` hive between the shadow copy before the incident and the current state, identifying registry keys the attacker created for persistence.

---

## 2. Memory forensics

### 2.1 Volatility 3 — Windows

Volatility 3 is the standard memory-forensics framework. Given a memory image (acquired via LiME, WinPmem, FTK Imager, or Magnet RAM Capture), Volatility parses kernel data structures to extract forensic artifacts.

**Process analysis.** `windows.pslist.PsList`: walks the `ActiveProcessLinks` doubly-linked list (the same list DKOM hides from — Domain 11 Chapter 11A §3.3) to list running processes (PID, PPID, name, creation time). `windows.psscan.PsScan`: scans the entire memory image for `EPROCESS` pool tags (`Proc`) — finds processes that are hidden from the `ActiveProcessLinks` list (DKOM-hidden processes, terminated processes whose memory hasn't been reclaimed). Comparing PsList and PsScan output reveals hidden processes.

**Injection detection.** `windows.malfind.Malfind`: scans process VADs (Virtual Address Descriptors) for regions that are: executable, committed, and not backed by a file (non-image-backed). These regions are suspicious — legitimate code runs from image-backed memory (DLLs loaded by the Windows loader); code in unbacked executable memory is likely injected (shellcode, reflective DLL, process-hollowed code). Malfind dumps the first bytes of each suspicious region for analysis.

**Network.** `windows.netscan.NetScan`: scans for network-connection structures (`_TCP_LISTENER`, `_TCP_ENDPOINT`, `_UDP_ENDPOINT`) in memory, listing active and recently-closed connections (local/remote IP:port, PID, state). Reveals C2 connections that may not be visible in current netstat output (if the connection was closed or the process was hidden).

**YARA scanning.** `windows.vadyarascan.VadYaraScan`: applies YARA rules to each process's VAD regions, searching for malware signatures (byte patterns, strings, regular expressions) in process memory. This detects malware that is running in memory but not on disk (fileless malware, reflectively-loaded DLLs).

**DLL and handle analysis.** `windows.dlllist.DllList`: lists DLLs loaded in each process (from the PEB's InLoadOrderModuleList). `windows.handles.Handles`: lists open handles (files, registry keys, mutexes, events) per process — reveals what resources each process is accessing.

### 2.1.1 Complete Volatility 3 investigation workflow

The workflow follows a triage-to-deep-dive progression, starting with broad characterization and narrowing to suspicious artifacts. Assumes a Windows memory image acquired with WinPmem or similar.

**Step 1: System identification.** Confirm the OS version and build for correct ISF (symbol table) selection:

```
vol -f /evidence/memory.raw windows.info
```

This outputs OS version, build number, system time, and bitness.

**Step 2: Process enumeration and hidden-process detection.** Run both pslist and psscan, then compare. Processes present in psscan but absent from pslist are either terminated (normal) or DKOM-hidden (suspicious):

```
vol -f /evidence/memory.raw windows.pslist
vol -f /evidence/memory.raw windows.psscan
```

A process with a recent creation time in psscan but not pslist has been unlinked from the active process list — a strong rootkit indicator.

**Step 3: Injection detection.** Malfind identifies executable memory regions not backed by a file on disk — the primary indicators of injected code:

```
vol -f /evidence/memory.raw windows.malfind
```

Each result includes PID, virtual address, protection flags, and a hex dump. Look for `FC E8` (x86 shellcode `call $+5` / `pop`) or `4D 5A` (MZ header indicating a reflectively loaded PE).

**Step 4: Network connections.** NetScan reveals active, listening, and recently-closed connections with their owning process:

```
vol -f /evidence/memory.raw windows.netscan
```

Look for: connections to unusual external IPs (C2 ports 443, 8443, high ephemeral), processes that should not have network connections (`notepad.exe` calling out), and unexpected listening sockets.

**Step 5: Command-line reconstruction.** Malicious processes often have distinctive command lines:

```
vol -f /evidence/memory.raw windows.cmdline
```

Key indicators: `powershell.exe -enc <base64>`, `cmd.exe /c` with long compound commands, processes launched from `AppData\Local\Temp\` or `ProgramData\`, and processes with no command line at all.

**Step 6: File scanning and extraction.** File objects in memory represent open or recently-accessed files. Extracting them recovers files that may be deleted from disk:

```
vol -f /evidence/memory.raw windows.filescan
vol -f /evidence/memory.raw windows.dumpfiles --pid 1234
```

The `filescan` plugin finds `_FILE_OBJECT` structures; `dumpfiles` extracts a process's open files by PID.

**Step 7: Registry analysis.** Registry hives in memory snapshot system configuration at capture time — persistence mechanisms, service configs, recently-accessed resources:

```
vol -f /evidence/memory.raw windows.registry.hivelist
vol -f /evidence/memory.raw windows.registry.printkey --key "Software\Microsoft\Windows\CurrentVersion\Run"
```

The `hivelist` plugin lists all loaded hives; `printkey` reads specific keys. Other forensically significant keys: `Services` (service persistence), `Classes\CLSID` (COM hijacking), `Explorer\RunMRU` (recently executed commands).

### 2.1.2 YARA rules for in-memory artifact detection

YARA rules applied to memory images detect fileless malware, reflective loaders, and post-exploitation frameworks that exist only in process memory.

**Cobalt Strike Beacon detection.** Beacon's named-pipe defaults (often not customized by operators), configuration block header, and sleep-mask XOR routine leave identifiable patterns:

```
rule CobaltStrike_Beacon_Memory {
    meta:
        description = "Detects Cobalt Strike Beacon in process memory"
        reference = "https://www.cobaltstrike.com"
        severity = "CRITICAL"
    strings:
        $pipe1 = "\\\\.\\pipe\\msagent_" ascii
        $pipe2 = "\\\\.\\pipe\\MSSE-" ascii
        $pipe3 = "\\\\.\\pipe\\postex_" ascii
        $config_header = { 00 01 00 01 00 02 ?? ?? 00 02 00 01 00 02 ?? ?? }
        $beacon_dll = "beacon.dll" ascii wide
        $reflective_loader = { 4D 5A 41 52 55 48 89 E5 }
        $sleep_mask = { 48 8B 44 24 ?? 48 89 44 24 ?? 48 8B 44 24 ?? 48 C1 E8 }
    condition:
        any of ($pipe*) or $config_header or
        ($beacon_dll and $reflective_loader) or
        $sleep_mask
}
```

**Mimikatz in-memory detection.** Even when executed via `Invoke-Mimikatz` or reflective loading (never touching disk), Mimikatz's string constants persist in process memory:

```
rule Mimikatz_Memory_Indicators {
    meta:
        description = "Detects Mimikatz strings and patterns in memory"
        severity = "CRITICAL"
    strings:
        $func1 = "sekurlsa::logonpasswords" ascii wide
        $func2 = "sekurlsa::wdigest" ascii wide
        $func3 = "lsadump::dcsync" ascii wide
        $func4 = "kerberos::golden" ascii wide
        $func5 = "privilege::debug" ascii wide
        $str1 = "mimikatz" ascii wide nocase
        $str2 = "gentilkiwi" ascii wide
        $str3 = "benjamin@gentilkiwi.com" ascii wide
        $str4 = "A]A\\A[A^A_" ascii
        $primary = "Primary" wide
        $credman = "CredMan" wide
        $wdigest = "wdigest" ascii wide
    condition:
        3 of ($func*) or
        2 of ($str*) or
        (($primary and $credman and $wdigest) and 1 of ($func*))
}
```

**Meterpreter detection.** The reflective DLL injection stage and transport configuration leave identifiable patterns:

```
rule Meterpreter_Reflective_Loader {
    meta:
        description = "Detects Meterpreter reflective loader and stage patterns"
        severity = "CRITICAL"
    strings:
        $mz_header = { 4D 5A }
        $reflective_export = "ReflectiveLoader" ascii
        $transport_config = { 68 74 74 70 73 3A 2F 2F }
        $stage_pattern = { FC E8 89 00 00 00 60 89 E5 31 D2 64 8B 52 30 }
        $reverse_tcp = { 6A 05 68 ?? ?? ?? ?? 68 02 00 ?? ?? 89 E6 }
        $stdapi = "stdapi" ascii
        $core_transport = "core_transport" ascii
    condition:
        ($mz_header at 0 and $reflective_export) or
        $stage_pattern or
        ($reverse_tcp and ($stdapi or $core_transport))
}
```

Applying these rules to a memory image with Volatility:

```
vol -f /evidence/memory.raw windows.vadyarascan --yara-file /rules/implant_detection.yar
```

Output identifies which process contains matching strings at what virtual address, correlating with pslist/psscan results.

### 2.2 Volatility 3 — Linux and macOS

**Linux.** `linux.pslist.PsList`: walks the `task_struct` linked list. `linux.proc.Maps`: parses `/proc/PID/maps` from kernel memory, listing each process's memory mappings (virtual address ranges, permissions, backing files). `linux.check_afinfo.CheckAfinfo`: checks for netfilter rootkit hooks by verifying the `seq_operations` function pointers in `tcp_seq_afinfo` and `udp_seq_afinfo` (a rootkit that hides network connections by hooking these pointers is detected when the pointers don't match known-good kernel functions).

### 2.2.1 Linux memory acquisition and analysis

**LiME acquisition commands.** LiME (Linux Memory Extractor) is a kernel module that dumps physical memory. It must be compiled against the target system's running kernel headers. On the target system (or a matching build environment):

```bash
cd /path/to/LiME/src
make
```

This produces `lime-$(uname -r).ko`. To acquire memory to a local file in LiME format (which Volatility 3 natively supports):

```bash
insmod lime-$(uname -r).ko "path=/evidence/memory.lime format=lime timeout=0"
```

The `format=lime` produces the LiME-specific format with address-range metadata. Alternative formats are `raw` (padded raw dump, where unreadable ranges are filled with zeros) and `padded` (equivalent to raw). The `timeout=0` disables the acquisition timeout. For network-based acquisition (avoiding writes to the target's disk — critical for volatile evidence preservation):

```bash
insmod lime-$(uname -r).ko "path=tcp:4444 format=lime"
```

On the forensic workstation, the analyst receives the dump via netcat:

```bash
nc <target_ip> 4444 > /evidence/memory.lime
```

**Linux Volatility 3 workflow.** After acquisition, the analyst processes the Linux memory image through Volatility 3's Linux plugin suite. The workflow mirrors the Windows process but uses Linux-specific plugins:

```
vol -f /evidence/memory.lime linux.pslist
vol -f /evidence/memory.lime linux.proc.Maps --pid 1234
vol -f /evidence/memory.lime linux.check_afinfo
vol -f /evidence/memory.lime linux.check_syscall
vol -f /evidence/memory.lime linux.lsmod
vol -f /evidence/memory.lime linux.bash
```

The `linux.check_syscall` plugin verifies that syscall table entries point to legitimate kernel functions — modified entries indicate a syscall-hooking rootkit. `linux.lsmod` lists loaded kernel modules, and comparing with the expected module list identifies suspicious modules (rootkit LKMs). `linux.bash` recovers bash command history from process memory, which may include commands the attacker typed that were not written to `.bash_history` (because the shell was still running when memory was captured).

### 2.2.2 Anti-forensics detection in memory

Memory analysis reveals anti-forensics techniques that are invisible to disk-based examination.

**Process hollowing indicators.** Process hollowing replaces a legitimate process's code with malicious code while keeping the original process name and PID. In memory, hollowed processes exhibit a mismatch between the PEB's `ImageBaseAddress` (which points to the original PE's base) and the actual code at that address (which contains the attacker's PE). Volatility's `windows.malfind` detects this when the VAD region at the process's image base has `PAGE_EXECUTE_READWRITE` protection (legitimate image sections use `PAGE_EXECUTE_READ`) and contains an MZ/PE header different from the on-disk executable.

**DKOM (Direct Kernel Object Manipulation) detection.** DKOM hides processes by unlinking their `EPROCESS` structures from the `ActiveProcessLinks` list. Detection relies on the psscan-versus-pslist comparison described in §2.1.1, but additional indicators include: the hidden process's `EPROCESS.ActiveProcessLinks.Flink` and `Blink` pointers both pointing to the process itself (self-referencing — the process was unlinked and had its links set to itself), and the process's thread list entries (`ETHREAD.ThreadListEntry`) still being linked into the kernel's thread scheduler (a process hidden from the process list but with actively scheduled threads is definitively DKOM-hidden, not terminated).

**Fileless malware patterns.** Fileless malware executes entirely in memory — PowerShell scripts, .NET assemblies loaded via reflection, and JavaScript/VBScript executed by WScript/CScript. In memory, these leave patterns: PowerShell's `System.Management.Automation.dll` loaded in unexpected processes (not `powershell.exe`), .NET CLR structures (`clr.dll`, `mscorlib.dll`) loaded in processes that do not normally use .NET, and large unbacked executable memory regions containing ASCII/Unicode strings with PowerShell cmdlet names, .NET class names, or JavaScript/VBScript syntax.

### 2.3 Rekall

Rekall (now largely unmaintained, superseded by Volatility 3) provided the `pmem` suite for memory acquisition (WinPmem for Windows, LinPmem for Linux, MacPmem for macOS) and a memory-analysis framework. Rekall's profile system (automatically determining the kernel version and symbol offsets from the memory image) was influential; Volatility 3 adopted a similar approach with its ISF (Intermediate Symbol Format) files.

---

## 3. Anti-forensics attack techniques and detection

The traces left by evidence destruction often provide stronger indicators of compromise than the evidence the attacker was trying to hide.

### 3.1 Timestomping

Timestomping modifies file timestamps to blend malicious files with legitimate system files or place them outside the investigation's time window.

**Attack tools.** Meterpreter's `timestomp` modifies $STANDARD_INFORMATION timestamps:

```
meterpreter> timestomp C:\\Windows\\Temp\\payload.exe -c "01/15/2020 08:30:00"
meterpreter> timestomp C:\\Windows\\Temp\\payload.exe -m "01/15/2020 08:30:00"
meterpreter> timestomp C:\\Windows\\Temp\\payload.exe -a "01/15/2020 08:30:00"
```

Native PowerShell timestomping does not require external tools:

```powershell
$file = "C:\Windows\Temp\payload.exe"
[IO.File]::SetCreationTime($file, "01/15/2020 08:30:00")
[IO.File]::SetLastWriteTime($file, "01/15/2020 08:30:00")
[IO.File]::SetLastAccessTime($file, "01/15/2020 08:30:00")
```

Both methods modify only $SI — they cannot modify $FN timestamps because those are updated exclusively by the NTFS driver during kernel-mode operations.

**Detection via $SI/$FN comparison.** MFTECmd flags entries where $SI Created predates $FN Created (logically impossible without manipulation). Additional detection: $UsnJrnl records the true creation time — if $SI claims 2020 but the $UsnJrnl `FileCreate` entry for the same MFT reference shows 2026, the file was timestomped. The $LogFile redo records provide similar corroboration.

### 3.2 Log clearing and event log tampering

The most common method is `wevtutil`:

```cmd
wevtutil cl Security
wevtutil cl System
wevtutil cl Application
wevtutil cl "Microsoft-Windows-Sysmon/Operational"
wevtutil cl "Microsoft-Windows-PowerShell/Operational"
```

Detection: **Event ID 1102** in Security (survives the clear — written after completion) and **Event ID 104** in System (records which log was cleared and by whom).

**Sigma rule for log clearing detection:**

```yaml
title: Windows Event Log Cleared
id: d99b79d2-0a6f-4f46-964e-4b09f3e91f70
status: stable
description: Detects clearing of Windows Event Logs
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 1102
    condition: selection
level: high
tags:
    - attack.defense_evasion
    - attack.t1070.001
```

```yaml
title: System Log Cleared via Event ID 104
id: a2b5c68e-3f2d-4a91-b6e4-8d7f9e1c4a2b
status: stable
description: Detects clearing of any Windows event log channel
logsource:
    product: windows
    service: system
detection:
    selection:
        EventID: 104
    condition: selection
level: high
tags:
    - attack.defense_evasion
    - attack.t1070.001
```

**Advanced event log tampering.** Mimikatz `event::drop` patches the Event Log service in memory to stop recording events. `Invoke-Phant0m` kills the threads of the `svchost.exe` hosting `EventLog` — the service appears running but records nothing. Detection: thread-count monitoring on the Event Log Service host process, and gaps in event log record sequence numbers (a gap without a clear event indicates selective deletion or service disruption).

**EvtxECmd for event log analysis.** Parses `.evtx` files into structured output revealing tampering indicators:

```
EvtxECmd.exe -f C:\Evidence\Security.evtx --csv C:\Output --csvf security_parsed.csv
EvtxECmd.exe -d C:\Evidence\winevt\Logs\ --csv C:\Output --csvf all_logs_parsed.csv
```

The `-f` flag processes a single file; `-d` processes all `.evtx` files in a directory. Examine record numbers for gaps (deleted events) and timestamps for chronological anomalies (suggesting injection or modification).

### 3.3 MFT manipulation

**SetMace** and similar tools write directly to raw disk sectors, modifying both $SI and $FN timestamps — defeating the standard $SI/$FN comparison. Detection requires comparing MFT timestamps against independent sources: $UsnJrnl entries, $LogFile redo records, Prefetch execution timestamps (records the last eight execution times independently of the program's MFT timestamps), and Shimcache/AmCache entries (which record their own timestamps at execution or install time).

### 3.4 Encrypted container forensics

Attackers use encrypted containers (VeraCrypt, BitLocker, LUKS) to store tools and exfiltrated data, preventing analysis even after disk acquisition.

**VeraCrypt detection.** VeraCrypt containers have no file signature by design — they appear as random data. Detection relies on entropy analysis: uniformly high Shannon entropy across the entire file length with a size that is an exact multiple of 512 bytes suggests an encrypted container.

**BitLocker detection and key recovery.** Identified by the `-FVE-FS-` signature in the volume boot sector. Key recovery sources: Active Directory (query `msFVE-RecoveryPassword` attribute on the computer object), memory capture (the FVEK is in kernel memory while mounted — Volatility's `windows.bitlocker` plugin extracts it), or TPM-only configurations (key released at boot without PIN — requires memory dump or DMA attack before system locks).

**Key recovery from memory.** When an encrypted volume is mounted, the key necessarily exists in RAM. `aeskeyfind` scans a raw memory image for AES key schedules:

```bash
aeskeyfind /evidence/memory.raw
```

This outputs candidate AES keys. For BitLocker, the FVEK extracted from memory is used with `dislocker`:

```bash
dislocker -K /evidence/fvek.key /evidence/bitlocker_partition.raw /mnt/bitlocker
mount -o ro /mnt/bitlocker/dislocker-file /mnt/decrypted
```

### 3.5 USN Journal, Prefetch, Shimcache, and AmCache deletion

**USN Journal deletion.** The `fsutil` command deletes the USN Journal:

```cmd
fsutil usn deletejournal /D C:
```

Detection: absence of the $UsnJrnl in the $MFT is anomalous — Windows recreates it automatically, so a freshly-created journal with only recent entries on a long-uptime system indicates deletion. Sysmon Event ID 1 captures the `fsutil` execution.

**Prefetch deletion.** Prefetch files (`C:\Windows\Prefetch\*.pf`) record program execution history. Attackers delete them with:

```cmd
del /q C:\Windows\Prefetch\*.pf
```

Detection: $UsnJrnl records the deletion (if not also cleared), and the $MFT retains deleted Prefetch entries until reallocation. On Windows 10+, absence of baseline system Prefetch files (`SVCHOST.EXE`, `CSRSS.EXE`) indicates wholesale deletion.

**Shimcache and AmCache.** Shimcache resides in the `SYSTEM` hive (`AppCompatCache` key); AmCache in `C:\Windows\appcompat\Programs\Amcache.hve`. Modification traces persist in registry transaction logs (`.LOG1`, `.LOG2`) and VSS copies. The analyst recovers previous versions from VSS snapshots (§1.4.2) and transaction logs, comparing against the current state to identify deletions.

**Sigma rule for anti-forensics tool execution:**

```yaml
title: Anti-Forensics Artifact Deletion Detected
id: f8b3c1a7-4e2d-4b98-a9c5-7d6e8f0b2a1c
status: experimental
description: Detects commands commonly used to delete forensic artifacts
logsource:
    category: process_creation
    product: windows
detection:
    selection_usn:
        CommandLine|contains:
            - 'fsutil usn deletejournal'
    selection_prefetch:
        CommandLine|contains|all:
            - 'del'
            - 'Prefetch'
    selection_evtx:
        CommandLine|contains:
            - 'wevtutil cl'
            - 'Clear-EventLog'
            - 'Remove-EventLog'
    selection_shadow:
        CommandLine|contains:
            - 'vssadmin delete shadows'
            - 'wmic shadowcopy delete'
    condition: 1 of selection_*
level: high
tags:
    - attack.defense_evasion
    - attack.t1070
    - attack.t1070.001
    - attack.t1070.004
```

---

## 4. Timeline analysis

### 4.1 Plaso and Timesketch

**Plaso (log2timeline).** A super-timeline tool: extracts timestamps from dozens of artifact sources (filesystem metadata, event logs, browser history, registry hives, Prefetch files, LNK files, MFT, $UsnJrnl, Windows Event Logs, Sysmon, Apache/IIS logs, macOS FSEvents, and many more), normalizes them into a unified format, and outputs a single chronological timeline.

Plaso's output (a Plaso storage file) is loaded into **Timesketch** (a web-based timeline-analysis interface) for interactive exploration: searching by timestamp range, keyword, source type, or artifact type; tagging events of interest; and annotating findings.

### 4.1.1 Complete Plaso/log2timeline pipeline

The Plaso pipeline has three stages: extraction (log2timeline.py), filtering/export (psort.py), and analysis (Timesketch or manual review). Each stage has critical configuration options that affect the completeness and usability of the timeline.

**Stage 1: Extraction.** log2timeline.py processes a forensic image (raw, E01, or a mounted filesystem) and extracts timestamped events into a Plaso storage file. For a full disk image with all parsers enabled:

```bash
log2timeline.py --storage-file /evidence/timeline.plaso /evidence/disk.raw
```

This runs all available parsers against the image. Processing a full disk image with all parsers can take many hours on large disks. To reduce processing time during initial triage, parser presets limit extraction to specific artifact categories. The `win7` preset (or `win10`, `linux`, `macos` — matching the target OS) includes the parsers most relevant to that operating system:

```bash
log2timeline.py --parsers "win_gen,webhist" \
    --storage-file /evidence/timeline_triage.plaso /evidence/disk.raw
```

The `win_gen` parser group includes MFT, $UsnJrnl, Windows Event Logs, Prefetch, registry hives, LNK files, and other common Windows artifacts. The `webhist` group adds browser history parsing. For specific artifact targeting (when the analyst knows which artifacts are relevant):

```bash
log2timeline.py --parsers "mft,usnjrnl,winevtx,prefetch" \
    --storage-file /evidence/timeline_targeted.plaso /evidence/disk.raw
```

**Stage 2: Filtering and export.** psort.py reads the Plaso storage file, applies filters, and exports the timeline in various formats. To export the full timeline as a CSV:

```bash
psort.py -o l2tcsv -w /evidence/timeline.csv /evidence/timeline.plaso
```

The `-o l2tcsv` flag selects the log2timeline CSV output format (a pipe-delimited format with standardized columns: date, time, timezone, MACB indicator, source, sourcetype, type, user, host, short description, long description, version, filename, inode, notes, format, extra). For Timesketch import, the output format is either the native Plaso format (imported directly) or JSONL:

```bash
psort.py -o json_line -w /evidence/timeline.jsonl /evidence/timeline.plaso
```

Filtering reduces the timeline to the investigation's relevant time window. The `--slice` flag extracts events within a specific range around a pivot point:

```bash
psort.py -o l2tcsv -w /evidence/timeline_filtered.csv \
    --slice "2026-05-01T00:00:00" --slice_size 604800 \
    /evidence/timeline.plaso
```

This exports events within 604800 seconds (7 days) of 2026-05-01T00:00:00. Date-based filtering:

```bash
psort.py -o l2tcsv -w /evidence/timeline_window.csv \
    "date > '2026-04-28 00:00:00' AND date < '2026-05-08 23:59:59'" \
    /evidence/timeline.plaso
```

**Stage 3: Timesketch import and analysis.** Timesketch provides a web-based interface for collaborative timeline analysis. Importing a Plaso storage file directly:

```bash
timesketch_importer --host https://timesketch.local \
    --timeline_name "Workstation_001" \
    --sketch_id 1 \
    /evidence/timeline.plaso
```

Within Timesketch, the analyst uses search queries to identify events of interest: `data_type:windows:evtx:record AND event_identifier:4624` (logon events), `data_type:fs:stat AND filename:*.exe AND timestamp_desc:Creation Time` (new executable files). Timesketch supports tagging events, adding comments, creating saved searches, and generating analysis views that combine multiple queries. Its Sigma analyzer automatically applies Sigma rules to the timeline data, flagging events that match known detection signatures.

### 4.2 MACB timestamps

Each filesystem records different timestamp types: **M** (Modified — content modification), **A** (Accessed — last read), **C** (Changed — metadata modification), **B** (Birth — creation time). Behavior varies:

NTFS: $SI stores M, A, C, B. $FN stores M, A, C, B (updated less frequently). Windows updates A-time by default only for directories (file A-time updates disabled by default since Vista for performance — controlled by `NtfsDisableLastAccessUpdate` registry value).

ext4: stores mtime (M), atime (A), ctime (C), crtime (B). The `noatime` mount option (common on Linux servers for performance) disables A-time updates entirely.

APFS: stores date_created (B), date_modified (M), date_accessed (A), date_added (specific to the directory entry).

### 4.3 Timestomping detection

Timestomping (modifying timestamps to hide activity) is detected by comparing timestamps across different sources: $SI vs $FN (§1.1), $MFT timestamps vs $LogFile records (the $LogFile contains the original timestamps at the time of the logged operation), $MFT timestamps vs $UsnJrnl entries (the $UsnJrnl records the timestamp at the time of the journaled event), and filesystem timestamps vs application logs (a file's modification time claims 2020, but a Windows Event Log records the file being written in 2026).

### 4.4 Windowing methodology and pivot-point identification

Raw super-timelines contain millions of events. The windowing methodology establishes anchor points and progressively expands the analysis window.

**Pivot-point identification.** The investigation starts with a "first-known-bad" event — the earliest confirmed IOC (EDR alert timestamp, phishing delivery time, malicious file creation timestamp, first C2 connection in proxy logs).

From the pivot point, the analyst expands **backward** (initial access vector: what process launched the malware? were staging files dropped? was there earlier C2? any suspicious logon preceding the activity?) and **forward** (lateral movement, persistence installation, data staging/exfiltration, cleanup activity). Each discovery becomes a new pivot point, and the process repeats recursively until the full attack chain is mapped. The window typically starts at +/-2 hours, expands to +/-24 hours, then +/-7 days, and for APTs, +/-30 days or longer.

### 4.5 Log analysis

**Windows Event Logs.** Stored in `.evtx` files in `%SystemRoot%\System32\winevt\Logs\`. Key logs: **Security.evtx** (logon events 4624/4625, privilege use, object access, policy changes), **System.evtx** (service starts/stops, driver loads, time changes), **Microsoft-Windows-Sysmon/Operational.evtx** (Sysmon events — see below).

**Sysmon event IDs.** Event 1 (ProcessCreate — command line, parent process, hashes), Event 3 (NetworkConnect — source/dest IP:port, process), Event 7 (ImageLoad — DLL loads, signed/unsigned), Event 8 (CreateRemoteThread — source/target process, start address), Event 10 (ProcessAccess — source process, target process, granted access mask — detects LSASS access for credential dumping), Event 11 (FileCreate — filename, creation time), Event 12/13/14 (RegistryEvent — create/delete key, set value, rename), Event 15 (FileCreateStreamHash — alternate data stream creation), Event 22 (DNSEvent — DNS query and response), Event 23 (FileDelete — file deletion with optional archiving).

**Linux auditd.** The Linux Audit System logs syscalls and security-relevant events. Configuration: `/etc/audit/audit.rules` (rules specifying which syscalls, files, or users to audit). Tools: `ausearch` (search audit logs by event type, user, time), `aureport` (generate reports — summaries of logins, file accesses, syscall events). Key audit event types: `SYSCALL` (syscall invocation with arguments), `EXECVE` (command execution with full argument list), `PATH` (file access), `USER_AUTH` / `USER_LOGIN` (authentication events).

**macOS Unified Logs.** macOS uses a binary log format (introduced in Sierra) accessed via `log show` and `log collect`. The unified log aggregates: kernel, system, and application events with subsystem and category filtering. Forensic queries: `log show --predicate 'process == "sshd"' --info` (SSH events), `log show --predicate 'eventMessage contains "TCC"'` (TCC access events).

**Cloud logs.** AWS CloudTrail (Domain 10 Chapter 10A §1.5): every API call logged with userIdentity, eventSource, eventName, sourceIPAddress, requestParameters. Azure Monitor: Activity Log (management-plane operations), Sign-in Logs (authentication events), Audit Logs (Azure AD changes). GCP Cloud Audit Logs: Admin Activity (always-on, configuration changes), Data Access (requires enablement, data read/write).

---

## 5. Incident response workflows

### 5.1 PICERL and NIST models

**PICERL (SANS).** Preparation (IR plan, team, tools, training) → Identification (detect the incident — via alert, report, anomaly) → Containment (stop the spread — short-term: isolate affected systems; long-term: apply patches, credential rotation) → Eradication (remove the attacker — delete malware, close backdoors, remove persistence mechanisms) → Recovery (restore systems to normal — rebuild compromised systems, restore from backups, monitor for re-compromise) → Lessons Learned (post-incident review — what happened, what worked, what didn't, and how to improve).

**NIST SP 800-61.** Similar lifecycle: Preparation → Detection and Analysis → Containment, Eradication, and Recovery → Post-Incident Activity. NIST emphasizes: documenting everything (chain of custody, analyst notes, timeline), coordinating with stakeholders (legal, management, law enforcement), and sharing indicators with the security community (via ISACs, STIX/TAXII).

### 5.2 Scoping and pivoting

The initial lead (an EDR alert, a phishing report, a threat-intel indicator) is the starting point. The analyst expands scope by **pivoting** on indicators: an IP address → query firewall logs for all connections to/from that IP → identify all affected hosts. A malware hash → search all endpoints for the hash (via EDR or Velociraptor) → identify all infected hosts. A domain → query DNS logs for all resolutions of that domain → identify all hosts that contacted it. An email address → search email logs for all messages from that address → identify all recipients.

Each pivot produces new indicators, which feed the next round of pivoting. The scoping process continues until no new indicators are found — the analyst has identified the full extent of the compromise.

### 5.3 Evidence acquisition

**Order of volatility.** Evidence is acquired in order of volatility (most volatile first): CPU registers and cache (lost immediately — typically not acquired outside specialized hardware forensics), RAM (lost on power-off — acquire with LiME, WinPmem, or EDR memory-dump capability), network state (ephemeral — capture with `netstat`, `ss`, packet captures), running processes (can be terminated — snapshot with `ps`, `tasklist`, Volatility), disk (persistent but mutable — image with `dd`, `dcfldd`, `dc3dd`, or FTK Imager).

**Disk imaging.** `dd if=/dev/sda of=image.raw bs=4M status=progress` (raw bit-for-bit copy). `dcfldd` adds hashing (MD5/SHA-256 computed during imaging for integrity verification) and logging. FTK Imager creates E01 (EnCase Evidence File) format images with built-in compression and integrity hashes. The image must be acquired in a forensically sound manner: write-blocking (using a hardware write-blocker or software write-blocking — `blockdev --setro /dev/sda`) to prevent modifying the source, and hash verification (compare the source hash against the image hash).

### 5.4 Endpoint interrogation tools

**Velociraptor.** A forensic and IR tool for endpoint interrogation at scale. **VQL (Velociraptor Query Language)**: a SQL-like language for querying endpoint artifacts. Example: `SELECT * FROM Artifact.Windows.System.Pslist()` (list processes), `SELECT * FROM Artifact.Windows.Detection.Yara.Process(rules=MyYaraRule)` (scan process memory with YARA). **Hunts**: deploy a VQL query to all endpoints simultaneously (searching for a specific IOC across thousands of machines). Velociraptor collects artifacts (predefined VQL queries for common forensic tasks: MFT analysis, Prefetch parsing, Shimcache, AmCache, event-log extraction) and returns results to the server for centralized analysis.

**GRR Rapid Response.** Google's open-source IR framework. Agents on endpoints receive **Flows** (tasks): file collection, registry analysis, memory acquisition, timeline creation. GRR's **Hunt** feature deploys flows to all endpoints matching a criteria.

**osquery.** Facebook's open-source endpoint-inspection tool. Exposes the operating system as a relational database: `SELECT pid, name, path, cmdline FROM processes WHERE name = 'powershell.exe'`. osquery tables cover: processes, users, network connections, listening ports, kernel modules, cron jobs, browser extensions, installed packages, file integrity, and hundreds more. osquery is deployed as an agent; the analyst queries endpoints via osqueryd (daemon mode with scheduled queries) or osqueryi (interactive mode).

### 5.4.1 Velociraptor VQL examples per IR phase

**Identification phase — event log triage.** Collect relevant event logs to confirm and characterize the incident:

```sql
SELECT EventData.TargetUserName AS User,
       EventData.IpAddress AS SourceIP,
       EventData.LogonType AS LogonType,
       System.TimeCreated.SystemTime AS Timestamp
FROM Artifact.Windows.EventLogs.EvtxHunter(
    EvtxGlob="C:/Windows/System32/winevt/Logs/Security.evtx",
    IdRegex="^(4624|4625)$",
    DateAfter="2026-05-01"
)
WHERE EventData.LogonType IN ("3", "10")
```

Type 3 (network) and Type 10 (RDP) logons from unexpected IPs are immediate lateral-movement indicators.

**Scoping phase — IOC file search.** Once a malicious file hash or filename is identified, a fleet-wide hunt searches all endpoints for the IOC:

```sql
SELECT OSPath, Size, Mtime, Hash.SHA256
FROM Artifact.Windows.Search.FileFinder(
    SearchFilesGlob="C:/Users/*/AppData/**/*.exe",
    Upload_File=TRUE
)
WHERE Hash.SHA256 = "a1b2c3d4e5f6..."
```

The `Upload_File=TRUE` flag collects matching files to the Velociraptor server.

**Containment phase — network isolation.** Block all traffic except Velociraptor server communication:

```sql
SELECT * FROM Artifact.Windows.Remediation.Quarantine(
    MessageBox="This system is under investigation. Contact IT Security.",
    ServerAddresses="10.0.0.50"
)
```

This configures Windows Firewall to allow only the Velociraptor server IP while blocking all other connections — the endpoint remains manageable but isolated.

### 5.4.2 osquery scheduled query configurations

osquery scheduled queries run at defined intervals and log to a centralized pipeline (Fleet, Fleetsmith, or osqueryd file logger). Continuous-monitoring configuration for common attack indicators:

```json
{
  "schedule": {
    "process_listening_ports": {
      "query": "SELECT p.name, p.path, p.cmdline, lp.port, lp.protocol, lp.address FROM listening_ports lp JOIN processes p ON lp.pid = p.pid WHERE lp.port NOT IN (22, 80, 443, 3389) AND lp.address != '127.0.0.1';",
      "interval": 300,
      "description": "Processes listening on non-standard ports"
    },
    "new_autoruns": {
      "query": "SELECT name, path, source FROM autoexec WHERE path NOT LIKE '%Microsoft%' AND path NOT LIKE '%Windows%';",
      "interval": 3600,
      "description": "Non-Microsoft autostart entries"
    },
    "suspicious_powershell": {
      "query": "SELECT pid, name, cmdline, parent FROM processes WHERE name = 'powershell.exe' AND (cmdline LIKE '%-enc%' OR cmdline LIKE '%-nop%' OR cmdline LIKE '%IEX%' OR cmdline LIKE '%Invoke-Expression%');",
      "interval": 60,
      "description": "PowerShell with encoded or download-execute patterns"
    },
    "lsass_access": {
      "query": "SELECT p.name AS source_process, p.path, p.cmdline FROM processes p JOIN process_open_handles poh ON p.pid = poh.pid WHERE poh.type = 'Process' AND poh.name LIKE '%lsass%' AND p.name NOT IN ('csrss.exe', 'services.exe', 'wininit.exe', 'MsMpEng.exe');",
      "interval": 120,
      "description": "Non-system processes with handles to LSASS"
    }
  }
}
```

Each query targets a specific technique: unusual listening ports, non-standard autostart entries, encoded PowerShell, and LSASS access from non-system processes.

### 5.4.3 GRR flow examples

GRR's flow system dispatches tasks to endpoints and collects results. Common forensic flows include:

**File collection flow.** The GRR API client dispatches a `FileFinder` flow specifying artifact paths and a `DOWNLOAD` action. A typical forensic triage collects event logs (`/C:/Windows/System32/winevt/Logs/*.evtx`), Prefetch files, Amcache, $MFT, and registry hives (`SAM`, `SYSTEM`, `SOFTWARE`, `NTUSER.DAT`). **Timeline flow.** The `TimelineFlow` creates a MACB timeline remotely on the endpoint from the filesystem root. GRR hunts deploy these flows across all enrolled clients matching specified criteria (operating system, labels, last-seen time), enabling fleet-wide evidence collection during large-scale incidents.

### 5.4.4 KAPE collection targets and modules

KAPE (Kroll Artifact Parser and Extractor) automates forensic artifact collection and processing. It operates in two modes: **Targets** (collecting raw artifact files from a live system or mounted image) and **Modules** (processing collected artifacts with parsing tools).

**Target collection.** KAPE's target definitions specify which files to collect. A typical IR triage collection:

```
KAPE.exe --tsource C: --tdest E:\Evidence\%m --target KapeTriage \
    --vhdx WORKSTATION01 --zv true
```

The `KapeTriage` compound target includes event logs, registry hives, Prefetch, AmCache, Shimcache, browser history, $MFT, $UsnJrnl, LNK files, jump lists, SRUM, WMI repository, PowerShell history, and scheduled tasks. The `--vhdx` flag packages into a VHDX virtual disk; `--zv true` adds hash verification.

For targeted collections (when the analyst needs specific artifacts only):

```
KAPE.exe --tsource C: --tdest E:\Evidence\%m \
    --target EventLogs,RegistryHives,Prefetch,MFT,UsnJrnl
```

**Module processing.** After collection, KAPE's module mode runs parsing tools against the collected artifacts:

```
KAPE.exe --msource E:\Evidence\WORKSTATION01 --mdest E:\Processed\WORKSTATION01 \
    --module MFTECmd,EvtxECmd,PECmd,AmcacheParser,AppCompatCacheParser,RECmd
```

Each module invokes its corresponding parser and places output in the destination directory — CSV and JSON files ready for timeline analysis or Timesketch import.

### 5.5 Threat hunting and detection engineering

**Hypothesis-driven hunting.** The analyst formulates a hypothesis based on threat intelligence or ATT&CK techniques: "The attacker may have achieved persistence via a scheduled task" (T1053.005). The analyst then searches for evidence: `SELECT * FROM scheduled_tasks WHERE action LIKE '%powershell%'` (osquery), or `EventID: 4698 AND TaskContent: *powershell*` (Windows Event Log), or the Velociraptor artifact `Windows.System.TaskScheduler`.

**MITRE ATT&CK as a hunt matrix.** ATT&CK provides a taxonomy of adversary techniques organized by tactic (Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Exfiltration, Command and Control, Impact). Each technique has a detection section describing the data sources and analytics that can detect it. The hunt team systematically works through ATT&CK techniques relevant to their threat model, creating hunts for each.

**YARA rules.** Pattern-matching rules for malware detection. A YARA rule specifies: strings (byte sequences, regular expressions, text strings) and a condition (logical expression combining string matches, file size, entry point, imports, etc.). Example structure: `rule MalwareFamily { meta: author = "analyst" strings: $s1 = { 4D 5A 90 00 } $s2 = "C:\\Windows\\Temp\\payload" condition: $s1 at 0 and $s2 }`. YARA rules are applied to: files on disk (scanning for malware), process memory (via Volatility's VadYaraScan or Velociraptor's Yara.Process artifact), and network traffic (via YARA-integrated IDS).

**Sigma rules.** A generic, open-source signature format for SIEM detections. A Sigma rule describes: the log source (product: windows, service: sysmon, category: process_creation), the detection logic (field-value conditions), and metadata (title, description, ATT&CK mapping, severity). Sigma rules are translated into SIEM-specific queries by backends: `sigmac` or `pySigma` convert to Splunk SPL, Elastic KQL, Azure Sentinel KQL, QRadar AQL, and others. Example: a Sigma rule for "LSASS memory access" detects Sysmon Event ID 10 where `TargetImage` contains `lsass.exe` and `GrantedAccess` includes `0x1010` (PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION).

---

## 6. Threat hunting packages

Each package below is a self-contained investigation unit: hypothesis, data sources, queries, detection rules, and escalation criteria.

### 6.1 Lateral movement hunt

**Hypothesis.** The adversary moved laterally using PsExec (T1569.002), WMI (T1047), DCOM (T1021.003), or WinRM (T1021.006).

**Data sources.** Security Event Log (4624, 4648, 4672), Sysmon (1, 3, 17, 18), System Event Log (7045), network connections.

**VQL — PsExec service-based execution.** PsExec installs a temporary service on the remote host, generating System Event ID 7045:

```sql
SELECT System.TimeCreated.SystemTime AS Timestamp,
       EventData.ServiceName,
       EventData.ImagePath,
       EventData.ServiceType,
       EventData.StartType,
       System.Computer
FROM Artifact.Windows.EventLogs.EvtxHunter(
    EvtxGlob="C:/Windows/System32/winevt/Logs/System.evtx",
    IdRegex="^7045$"
)
WHERE EventData.ServiceName =~ "(PSEXE|^[a-z]{8}$)"
   OR EventData.ImagePath =~ "(%COMSPEC%|cmd\\.exe|powershell)"
```

The regex catches randomly-named services from customized PsExec. Image paths with `cmd.exe` or `powershell` indicate remote command execution.

**VQL — WMI process creation.** WMI-based lateral movement spawns processes under `WmiPrvSE.exe`:

```sql
SELECT Timestamp, Pid, Name, CommandLine, ParentName
FROM Artifact.Windows.EventLogs.EvtxHunter(
    EvtxGlob="C:/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%2FOperational.evtx",
    IdRegex="^1$"
)
WHERE ParentName =~ "WmiPrvSE"
  AND Name NOT IN ("WmiPrvSE.exe", "mofcomp.exe", "WmiApSrv.exe")
```

**osquery query — active lateral movement indicators:**

```sql
SELECT p.pid, p.name, p.path, p.cmdline, p.parent,
       pp.name AS parent_name, pp.cmdline AS parent_cmdline
FROM processes p
JOIN processes pp ON p.parent = pp.pid
WHERE pp.name IN ('wmiprvse.exe', 'wsmprovhost.exe', 'services.exe')
  AND p.name NOT IN ('svchost.exe', 'spoolsv.exe', 'msdtc.exe')
ORDER BY p.start_time DESC;
```

Identifies running processes parented by WMI provider host, WinRM host process, or the services controller.

**Sigma rule — PsExec service installation:**

```yaml
title: PsExec Service Installation
id: c4d3a2b1-7f8e-4d5c-9a6b-3e2f1d0c8b7a
status: stable
description: Detects PsExec-style remote service installation
logsource:
    product: windows
    service: system
detection:
    selection:
        EventID: 7045
    filter_name:
        ServiceName|contains:
            - 'PSEXE'
    filter_cmd:
        ImagePath|contains:
            - '%COMSPEC%'
            - 'cmd.exe'
            - 'powershell'
    condition: selection AND (filter_name OR filter_cmd)
level: high
tags:
    - attack.lateral_movement
    - attack.execution
    - attack.t1569.002
    - attack.t1021.002
```

**Escalation criteria.** Escalate when: (1) service installations on >2 endpoints in a short window, (2) source logon IP is not a known admin workstation, (3) service executes encoded PowerShell or downloads from external URLs, or (4) correlates with credential access or persistence findings.

### 6.2 Persistence mechanism hunt

**Hypothesis.** The adversary established persistence via scheduled tasks (T1053.005), services (T1543.003), registry run keys (T1547.001), or WMI event subscriptions (T1546.003).

**Data sources.** Security Event Log (4698, 4697), Sysmon (1, 12, 13, 19, 20, 21), Task Scheduler and WMI operational logs, registry hives.

**VQL — scheduled task creation:**

```sql
SELECT EventData.TaskName,
       EventData.TaskContent,
       System.TimeCreated.SystemTime AS Timestamp,
       System.Security.UserID AS Creator
FROM Artifact.Windows.EventLogs.EvtxHunter(
    EvtxGlob="C:/Windows/System32/winevt/Logs/Security.evtx",
    IdRegex="^4698$"
)
WHERE EventData.TaskContent =~ "(powershell|cmd\\.exe|mshta|rundll32|regsvr32|certutil|bitsadmin)"
```

**VQL — WMI event subscriptions.** WMI persistence uses filter + consumer + binding (Sysmon events 19/20/21). Query the WMI repository directly:

```sql
SELECT * FROM Artifact.Windows.Persistence.PermanentWMIEvents()
```

**osquery — registry run keys:**

```sql
SELECT r.key, r.name, r.data, r.mtime
FROM registry r
WHERE r.key LIKE 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run%'
   OR r.key LIKE 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce%'
   OR r.key LIKE 'HKEY_USERS\%\SOFTWARE\Microsoft\Windows\CurrentVersion\Run%'
ORDER BY r.mtime DESC;
```

**Sigma rule — suspicious scheduled task creation:**

```yaml
title: Scheduled Task Created with Suspicious Action
id: b7e4d2a1-3f6c-4e8d-9b5a-2c1f0e7d6a3b
status: stable
description: Detects scheduled task creation with potentially malicious commands
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4698
    keywords:
        TaskContent|contains:
            - 'powershell'
            - 'cmd /c'
            - 'mshta'
            - 'rundll32'
            - 'regsvr32'
            - 'certutil'
            - 'bitsadmin'
            - 'wscript'
            - 'cscript'
    condition: selection AND keywords
level: high
tags:
    - attack.persistence
    - attack.t1053.005
```

**Escalation criteria.** Escalate when: (1) multiple persistence mechanisms on the same host (high sophistication), (2) payload contacts external IP/domain, (3) creation outside maintenance windows by non-service account, or (4) targets a high-value system (DC, backup server, security infra).

### 6.3 Credential access hunt

**Hypothesis.** The adversary dumped credentials via LSASS memory access (T1003.001), Kerberoasting (T1558.003), or DCSync (T1003.006).

**Data sources.** Sysmon (1, 10), Security Event Log (4662, 4769, 4624), DC Security Event Log.

**VQL — LSASS access detection.** Sysmon Event ID 10 captures cross-process access. The `GrantedAccess` masks `0x1010` and `0x1FFFFF` are high-confidence indicators of memory reading:

```sql
SELECT EventData.SourceImage AS SourceProcess,
       EventData.TargetImage AS TargetProcess,
       EventData.GrantedAccess AS AccessMask,
       EventData.SourceProcessGUID,
       System.TimeCreated.SystemTime AS Timestamp
FROM Artifact.Windows.EventLogs.EvtxHunter(
    EvtxGlob="C:/Windows/System32/winevt/Logs/Microsoft-Windows-Sysmon%2FOperational.evtx",
    IdRegex="^10$"
)
WHERE TargetImage =~ "lsass\\.exe"
  AND NOT SourceImage =~ "(csrss|services|wininit|lsass|MsMpEng|svchost|wmiprvse)\\.exe$"
  AND GrantedAccess IN ("0x1010", "0x1038", "0x1FFFFF", "0x1F3FFF")
```

**VQL — Kerberoasting detection.** On the DC, Event ID 4769 with encryption type `0x17` (RC4-HMAC) is suspicious — modern environments should use AES:

```sql
SELECT EventData.TargetUserName AS ServiceAccount,
       EventData.ServiceName,
       EventData.TicketEncryptionType,
       EventData.IpAddress AS RequestorIP,
       System.TimeCreated.SystemTime AS Timestamp
FROM Artifact.Windows.EventLogs.EvtxHunter(
    EvtxGlob="C:/Windows/System32/winevt/Logs/Security.evtx",
    IdRegex="^4769$"
)
WHERE TicketEncryptionType = "0x17"
  AND ServiceName NOT LIKE "%$"
  AND ServiceName != "krbtgt"
```

**VQL — DCSync detection.** DCSync uses DRS protocol to request credentials. Event ID 4662 logs the replication GUIDs:

```sql
SELECT EventData.SubjectUserName,
       EventData.ObjectName,
       EventData.Properties,
       System.TimeCreated.SystemTime AS Timestamp
FROM Artifact.Windows.EventLogs.EvtxHunter(
    EvtxGlob="C:/Windows/System32/winevt/Logs/Security.evtx",
    IdRegex="^4662$"
)
WHERE Properties =~ "(1131f6aa-9c07-11d1-f79f-00c04fc2dcd2|1131f6ad-9c07-11d1-f79f-00c04fc2dcd2)"
  AND NOT SubjectUserName =~ "\\$$"
```

The GUIDs are DS-Replication-Get-Changes and DS-Replication-Get-Changes-All. Machine accounts are filtered out — a user account requesting replication rights is definitively DCSync.

**osquery — LSASS handle detection:**

```sql
SELECT p.name AS source_name, p.path AS source_path,
       p.cmdline, p.uid, p.start_time,
       poh.pid AS target_pid
FROM process_open_handles poh
JOIN processes p ON poh.pid = p.pid
JOIN processes t ON poh.handle = t.pid
WHERE t.name = 'lsass.exe'
  AND p.name NOT IN ('csrss.exe', 'services.exe', 'wininit.exe',
                      'lsass.exe', 'svchost.exe', 'MsMpEng.exe');
```

**Sigma rule — LSASS memory access:**

```yaml
title: LSASS Memory Access by Non-System Process
id: 5ba9b852-f39e-4b90-84b2-c4517dc97f01
status: stable
description: Detects LSASS memory access indicating credential dumping
logsource:
    product: windows
    service: sysmon
detection:
    selection:
        EventID: 10
        TargetImage|endswith: '\lsass.exe'
        GrantedAccess|contains:
            - '0x1010'
            - '0x1038'
            - '0x1FFFFF'
            - '0x1F3FFF'
    filter:
        SourceImage|endswith:
            - '\csrss.exe'
            - '\services.exe'
            - '\wininit.exe'
            - '\lsass.exe'
            - '\svchost.exe'
            - '\MsMpEng.exe'
            - '\wmiprvse.exe'
    condition: selection AND NOT filter
level: critical
tags:
    - attack.credential_access
    - attack.t1003.001
```

**Sigma rule — Kerberoasting via RC4 TGS request:**

```yaml
title: Kerberoasting - RC4 Ticket Encryption Downgrade
id: a3c8f72e-1d4b-4e96-8a5f-9b3c2d7e6f01
status: stable
description: Detects TGS requests with RC4 encryption targeting service accounts
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4769
        TicketEncryptionType: '0x17'
    filter:
        ServiceName|endswith: '$'
    condition: selection AND NOT filter
level: high
tags:
    - attack.credential_access
    - attack.t1558.003
```

**Escalation criteria.** Escalate immediately when: (1) LSASS access from a non-security-tool process, (2) Kerberoasting targets >5 service accounts in a short window (automated tooling), (3) DCSync from a non-DC machine (never legitimate from a workstation), or (4) correlates with lateral movement or persistence findings.

---

## 7. Windows forensic artifacts deep dive

This section extends the NTFS-level analysis in §1 and the event log overview in §4.5 with artifact-by-artifact parsing detail: exact registry paths, tool commands, and interpretation guidance.

### 7.1 Registry forensics — execution artifacts

**ShimCache (AppCompatCache).** The Application Compatibility Cache records metadata for executables that Windows evaluates against the Shim Database at execution or file-access time. On modern Windows (8+), ShimCache entries are written at shutdown and stored in the SYSTEM hive.

Registry path:

```
HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\AppCompatCache
```

The `AppCompatCache` value is a binary blob with a version-dependent header. Each entry contains: the full file path, the file's last-modification timestamp ($SI `LastWriteTime`), and (on Windows 7/Server 2008R2) an `Executed` flag. On Windows 10+, the `Executed` flag is absent — presence in ShimCache confirms only that the OS evaluated the file, not that it ran. However, files that were never staged to disk cannot appear in ShimCache, so it proves the file existed on the filesystem at some point.

Parsing with AppCompatCacheParser (Eric Zimmerman):

```
AppCompatCacheParser.exe -f C:\Evidence\SYSTEM --csv C:\Output --csvf shimcache.csv
```

Parsing with RegRipper:

```
rip.exe -r C:\Evidence\SYSTEM -p appcompatcache
```

RegRipper's `appcompatcache` plugin decodes the binary blob and outputs entries in chronological order (most recent first). The analyst cross-references ShimCache paths with timeline data: a file path in ShimCache that does not exist on the current filesystem indicates the file was deleted after execution — a common attacker cleanup pattern.

**Amcache.** The Amcache hive records detailed execution and installation metadata including SHA-1 hashes, file sizes, publisher information, PE compilation timestamps, and the first-execution timestamp. Amcache is critical because it provides hash values even after the executable has been deleted from disk.

Hive location:

```
C:\Windows\appcompat\Programs\Amcache.hve
```

Key paths within the hive:

```
Root\InventoryApplicationFile     — per-file execution records (Win10 1607+)
Root\File\{volume GUID}\          — earlier format, keyed by volume GUID + MFT entry
```

Each `InventoryApplicationFile` entry contains: `LowerCaseLongPath` (full file path), `FileId` (volume GUID + MFT sequence), `SHA1` (prefixed with `0000`), `Size`, `Publisher`, `Version`, `BinaryType`, `LinkDate` (PE compilation timestamp), and `LastWriteTimestamp`.

Parsing with AmcacheParser (Eric Zimmerman):

```
AmcacheParser.exe -f C:\Evidence\Amcache.hve --csv C:\Output --csvf amcache.csv
```

The resulting CSV lets the analyst search by SHA-1 hash across threat-intelligence feeds even when the original binary is gone. The `LinkDate` field is forensically valuable: a PE compiled yesterday but timestomped to appear years old is exposed by the Amcache `LinkDate` preserving the true compilation timestamp.

**BAM/DAM (Background Activity Moderator / Desktop Activity Moderator).** Introduced in Windows 10 1709, BAM tracks execution of background applications per user. DAM tracks the same for desktop applications on systems with Connected Standby.

Registry paths:

```
HKLM\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings\{SID}
HKLM\SYSTEM\CurrentControlSet\Services\dam\State\UserSettings\{SID}
```

Each value name is the full executable path; the value data is a FILETIME timestamp of the last execution. BAM/DAM entries tie execution to a specific user SID and provide timestamps that survive ShimCache overwrites and Amcache hive compaction.

Parsing with RECmd:

```
RECmd.exe -f C:\Evidence\SYSTEM --bn C:\RECmd\BatchExamples\RECmd_Batch_MC.reb \
    --csv C:\Output --csvf bam_dam.csv
```

**UserAssist.** Tracks GUI program launches per user. Stored in each user's NTUSER.DAT hive under a ROT-13 encoded subkey.

Registry path:

```
NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist\{GUID}\Count
```

GUIDs: `{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}` (executable file execution) and `{F4E57C4B-2036-45F0-A9AB-443BCFE33D9F}` (shortcut file execution). Each value name is ROT-13 encoded; the value data contains a run counter, focus time, focus count, and a FILETIME timestamp of the last execution.

Parsing with RegRipper:

```
rip.exe -r C:\Evidence\NTUSER.DAT -p userassist
```

UserAssist is particularly useful for proving interactive user activity — it only records GUI launches, so a UserAssist entry for a tool like `mimikatz.exe` proves someone ran it through the desktop, not via a service or scheduled task.

**MRU (Most Recently Used) lists.** Multiple MRU registries track user activity. Key locations in NTUSER.DAT:

```
Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs
Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU
Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU
Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU
Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths
```

`RecentDocs` records recently opened files (by extension and by order). `OpenSavePidlMRU` records files opened or saved through standard file dialogs — valuable for proving a user opened a specific document. `RunMRU` records commands typed in the Run dialog. `TypedPaths` records paths typed into Explorer's address bar. Each provides timestamps and filenames that survive file deletion.

### 7.2 Event log forensics — security-relevant Event ID mapping

The following table maps security-relevant Event IDs to their forensic significance. These supplement the Sysmon event overview in §4.5 with the full Windows Security, System, and PowerShell operational logs.

**Security log — authentication and access:**

| Event ID | Description | Forensic significance |
|----------|-------------|----------------------|
| 4624 | Successful logon | Logon type (2=interactive, 3=network, 10=RDP), source IP, account name |
| 4625 | Failed logon | Brute force detection, password spraying (many 4625s then one 4624) |
| 4648 | Explicit credential logon | `runas`, mapped drives, scheduled tasks running as another user |
| 4672 | Special privileges assigned | Indicates admin-equivalent logon (SeDebugPrivilege, SeTcbPrivilege) |
| 4688 | Process creation | Full command line (requires audit policy), parent PID, token elevation |
| 4697 | Service installed | Persistence via new service, PsExec-style lateral movement |
| 4768 | TGT requested (AS-REQ) | AS-REP Roasting detection (RC4 requests for accounts with DONT_REQ_PREAUTH) |
| 4769 | TGS requested (TGS-REQ) | Kerberoasting detection (RC4 encryption type 0x17) |
| 4720 | User account created | Attacker-created accounts for persistence |
| 4728/4732 | Member added to security group | Privilege escalation via group membership |
| 4662 | Operation on AD object | DCSync detection (replication rights GUIDs) |
| 4698 | Scheduled task created | Persistence, lateral movement payload delivery |

**PowerShell logging:**

| Event ID | Log | Description |
|----------|-----|-------------|
| 4103 | Microsoft-Windows-PowerShell/Operational | Module logging — records pipeline execution details, parameters, output |
| 4104 | Microsoft-Windows-PowerShell/Operational | Script block logging — records the full text of executed script blocks including deobfuscated content |

Event ID 4104 is the single most valuable PowerShell forensic artifact. When Windows detects suspicious content (via AMSI integration), it logs the script block even if standard script block logging is disabled. This captures `Invoke-Mimikatz`, `Invoke-Expression(New-Object Net.WebClient).DownloadString(...)`, and other PowerShell-based attack payloads in clear text regardless of obfuscation layers.

**WMI operational log:**

| Event ID | Log | Description |
|----------|-----|-------------|
| 5857 | Microsoft-Windows-WMI-Activity/Operational | WMI provider loaded — identifies which provider DLL serviced a WMI query |
| 5858 | Microsoft-Windows-WMI-Activity/Operational | WMI provider error — failed WMI operations (reconnaissance failures) |
| 5859 | Microsoft-Windows-WMI-Activity/Operational | WMI filter activation — permanent event subscription filter triggered |
| 5860 | Microsoft-Windows-WMI-Activity/Operational | WMI temporary event registration — short-lived subscriptions |
| 5861 | Microsoft-Windows-WMI-Activity/Operational | WMI permanent event registration — persistence mechanism creation |

Event ID 5861 is the definitive indicator of WMI persistence (T1546.003). The event contains the filter query, consumer command, and the binding between them — a complete record of the persistence mechanism.

**Sysmon complete event mapping (IDs 1-26):**

| ID | Event | Key fields |
|----|-------|-----------|
| 1 | Process Create | Image, CommandLine, ParentImage, Hashes, User |
| 2 | File creation time changed | TargetFilename, PreviousCreationUtcTime (timestomping) |
| 3 | Network connection | SourceIp, DestinationIp, DestinationPort, Image |
| 4 | Sysmon service state changed | Service start/stop |
| 5 | Process terminated | Image, ProcessId |
| 6 | Driver loaded | ImageLoaded, Hashes, Signed |
| 7 | Image loaded | ImageLoaded (DLL), Hashes, Signed, Signature |
| 8 | CreateRemoteThread | SourceImage, TargetImage, StartAddress |
| 9 | RawAccessRead | Direct disk read (bypassing filesystem API) |
| 10 | ProcessAccess | SourceImage, TargetImage, GrantedAccess |
| 11 | FileCreate | TargetFilename, CreationUtcTime |
| 12 | Registry key/value create or delete | EventType, TargetObject |
| 13 | Registry value set | TargetObject, Details |
| 14 | Registry key/value rename | EventType, TargetObject, NewName |
| 15 | FileCreateStreamHash | TargetFilename, Hash (ADS creation) |
| 16 | Sysmon configuration change | Configuration hash |
| 17 | Pipe created | PipeName, Image |
| 18 | Pipe connected | PipeName, Image |
| 19 | WMI filter | EventNamespace, Name, Query |
| 20 | WMI consumer | Name, Type, Destination |
| 21 | WMI binding | Consumer, Filter |
| 22 | DNS query | QueryName, QueryResults, Image |
| 23 | File delete (archived) | TargetFilename, Hashes, IsExecutable |
| 24 | Clipboard change | ClientInfo (requires explicit configuration) |
| 25 | Process tampering | Type (image or process hollowing detected) |
| 26 | File delete logged | TargetFilename, Hashes (log-only, no archive) |

**Log retention best practices.** Default Windows event log sizes are insufficient for incident response. Recommended minimum sizes for Security.evtx: 1 GB (captures weeks of activity on busy DCs). Sysmon operational log: 512 MB. PowerShell operational log: 256 MB. Configure via Group Policy (`Computer Configuration → Administrative Templates → Windows Components → Event Log Service → <log> → Maximum Log Size`). Forward logs to a SIEM with a minimum 90-day hot retention and 1-year cold retention. Ensure the SIEM ingestion pipeline does not silently drop events when overwhelmed — monitor for ingestion gaps.

### 7.3 Prefetch and Superfetch analysis

**Prefetch files.** Located in `C:\Windows\Prefetch\`, each `.pf` file records: the executable name, the last eight execution timestamps (Windows 10+; only one on Windows 7), the run count, and the list of files and directories accessed during the first 10 seconds of execution. The filename format is `EXECUTABLE.EXE-XXXXXXXX.pf` where `XXXXXXXX` is a hash of the executable path.

Parsing with PECmd (Eric Zimmerman):

```
PECmd.exe -f "C:\Evidence\Prefetch\CMD.EXE-4A81B364.pf" --csv C:\Output
PECmd.exe -d "C:\Evidence\Prefetch" --csv C:\Output --csvf prefetch_all.csv
```

PECmd extracts execution timestamps, run count, and the referenced files/directories. Forensic applications: proving program execution (especially after the binary has been deleted), identifying what files a tool accessed (the file-reference list reveals data-staging directories, credential dump output paths, and lateral-movement payloads), and establishing execution frequency (run count + timestamps).

**Superfetch (SysMain).** The Superfetch database (`C:\Windows\Prefetch\Ag*.db`) contains historical execution records spanning weeks. `CrowdResponse` and custom parsers extract entries that complement Prefetch data with broader historical coverage.

### 7.4 Browser forensics

Modern browsers store forensic artifacts in SQLite databases and LevelDB stores.

**Chrome/Edge (Chromium-based).** Profile data is stored under `%LOCALAPPDATA%\Google\Chrome\User Data\Default\` (Chrome) or `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\` (Edge).

| Artifact | Database | Key tables/fields |
|----------|----------|-------------------|
| History | History | `urls` (url, title, visit_count, last_visit_time), `visits` (visit_time, from_visit, transition) |
| Downloads | History | `downloads` (target_path, start_time, end_time, received_bytes, total_bytes, url) |
| Cookies | Cookies | `cookies` (host_key, name, value, creation_utc, expires_utc, last_access_utc) |
| Autofill | Web Data | `autofill` (name, value, date_created, date_last_used, count) |
| Login data | Login Data | `logins` (origin_url, username_value, date_created, date_last_used) |

Chromium timestamps use WebKit epoch (microseconds since 1601-01-01). Convert to Unix time: `(webkit_timestamp / 1000000) - 11644473600`.

**Firefox.** Profile data in `%APPDATA%\Mozilla\Firefox\Profiles\<profile>\`.

| Artifact | Database | Key tables |
|----------|----------|------------|
| History/Bookmarks | places.db | `moz_places` (url, title, visit_count, last_visit_date), `moz_historyvisits` (visit_date, visit_type, from_visit) |
| Downloads | places.db | `moz_annos` (annotation entries for download metadata) |
| Cookies | cookies.sqlite | `moz_cookies` (host, name, value, creationTime, lastAccessed, expiry) |
| Form data | formhistory.sqlite | `moz_formhistory` (fieldname, value, firstUsed, lastUsed, timesUsed) |

Firefox timestamps use PRTime (microseconds since 1970-01-01 UTC). Divide by 1000000 for Unix seconds.

Query browser history with `sqlite3`:

```bash
sqlite3 /evidence/History "SELECT url, title, datetime(last_visit_time/1000000-11644473600,'unixepoch') AS visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 50;"
```

### 7.5 Email forensics

**PST/OST parsing.** Microsoft Outlook stores email in PST (Personal Storage Table) and OST (Offline Storage Table) files. Both use the same binary format. `pffexport` from the libpff library extracts messages, attachments, contacts, and calendar entries:

```bash
pffexport -t /evidence/email_export /evidence/user.pst
```

The export produces a directory tree mirroring the folder structure, with each message as a text file and attachments extracted alongside. For structured analysis, `pff2csv.py` (community tool) converts PST contents to CSV for timeline integration.

**Exchange journal analysis.** Exchange journaling captures a copy of every email sent or received. Journal reports contain: the original sender, all recipients (To/CC/BCC), the timestamp, and the full message body and attachments. Journal exports in EML format are parsed with standard email-parsing libraries. The analyst searches journal data for: phishing emails (initial access), data exfiltration via email (large attachments to external addresses), and BEC correspondence (fraudulent wire-transfer instructions).

### 7.6 USB forensics

USB device connections leave multiple artifact trails on Windows.

**USBSTOR registry key.** Records every USB mass-storage device that was connected:

```
HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR\{Disk&Ven_VENDOR&Prod_PRODUCT&Rev_REV}\{SerialNumber}
```

Each subkey contains: `FriendlyName` (device description), `HardwareID` (VID/PID), and timestamps. The `ContainerID` value links to the device's entry in `HKLM\SYSTEM\CurrentControlSet\Enum\USB`.

**SetupAPI logs.** `C:\Windows\inf\setupapi.dev.log` records device-installation events with timestamps. Search for `USBSTOR` entries to find the first connection time of each device:

```
grep -i "USBSTOR" /evidence/setupapi.dev.log
```

**Mountpoints2.** Per-user evidence of mounted volumes:

```
NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\MountPoints2
```

Each GUID subkey corresponds to a mounted volume; the last-write timestamp indicates when the user last accessed that volume.

**Device identification workflow.** Correlate USBSTOR serial number with SetupAPI first-connect timestamp, MountPoints2 per-user mount evidence, and the `SYSTEM\MountedDevices` values (mapping drive letters to device signatures) to build a complete picture: which device, when it was first connected, which user account accessed it, and which drive letter it was assigned.

---

## 8. Linux and macOS forensic artifacts

### 8.1 Linux log analysis

**auth.log / secure.** On Debian-based systems, `/var/log/auth.log` records authentication events: SSH logins, `sudo` usage, PAM authentication, `su` transitions, and account lockouts. On RHEL-based systems, the equivalent is `/var/log/secure`. Key patterns:

```bash
# Failed SSH attempts (brute force detection)
grep "Failed password" /evidence/var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn

# Successful SSH logins
grep "Accepted publickey\|Accepted password" /evidence/var/log/auth.log

# sudo command execution
grep "COMMAND=" /evidence/var/log/auth.log
```

**syslog.** `/var/log/syslog` (or `/var/log/messages`) captures kernel messages, daemon output, and application logs. Forensically relevant entries: cron job execution (lines from `CRON[PID]`), service start/stop events, kernel module loading (`kernel: [module_name]: module loaded`), and network interface state changes.

**systemd journal.** On systemd-based distributions, the binary journal (`/var/log/journal/`) is the primary log store. Query with `journalctl`:

```bash
# Export journal from evidence image to text
journalctl --directory=/evidence/var/log/journal --no-pager --output=short-iso > /evidence/journal_export.txt

# Filter by unit (service)
journalctl --directory=/evidence/var/log/journal -u sshd --since "2026-05-01" --until "2026-05-10"

# Filter by priority (errors and above)
journalctl --directory=/evidence/var/log/journal -p err --no-pager

# Export as JSON for parsing
journalctl --directory=/evidence/var/log/journal --output=json > /evidence/journal.jsonl
```

The journal preserves structured metadata (boot ID, machine ID, unit name, PID, UID) that flat text logs lose. The `_TRANSPORT` field distinguishes kernel, syslog, journal, stdout, and audit sources.

### 8.2 Shell history and cron artifacts

**bash_history.** `~/.bash_history` records commands entered by each user. Forensic caveats: history is typically written at shell exit (commands in an active session are only in memory — recoverable via memory forensics per §2.2.1's `linux.bash` plugin), the `HISTCONTROL` variable may suppress duplicate or space-prefixed commands, and attackers commonly clear history via `history -c; rm ~/.bash_history` or `unset HISTFILE`.

Detection of history manipulation: a `.bash_history` file with a last-modified timestamp much earlier than the user's last login (history was replaced or truncated), or a missing `.bash_history` on an account with recent activity.

**Cron artifacts.** Cron job definitions persist in multiple locations:

```
/var/spool/cron/crontabs/<username>    — per-user crontabs
/etc/crontab                            — system crontab
/etc/cron.d/                            — system cron drop-in directory
/etc/cron.{hourly,daily,weekly,monthly} — periodic scripts
```

Cron execution is logged in syslog/journal. The analyst cross-references cron definitions with execution logs to identify attacker-installed cron jobs (persistence) and their execution history.

### 8.3 auditd logs and /proc filesystem

**auditd configuration and analysis.** The Linux Audit framework logs security-relevant syscalls. Audit rules in `/etc/audit/audit.rules` define what is captured:

```bash
# Log all execve calls (command execution)
-a always,exit -F arch=b64 -S execve -k exec_log

# Log file access to sensitive paths
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k priv_esc

# Log network connections
-a always,exit -F arch=b64 -S connect -k network_connect
```

Searching audit logs with `ausearch`:

```bash
# All execve events in a time range
ausearch --start 05/01/2026 00:00:00 --end 05/10/2026 23:59:59 -sc execve -i

# Authentication failures
ausearch -m USER_AUTH --success no -i

# File access to /etc/shadow
ausearch -k identity -i
```

**`/proc` filesystem forensics.** On a live Linux system, `/proc` exposes kernel data structures. Key entries for forensic triage:

| Path | Content |
|------|---------|
| `/proc/<PID>/cmdline` | Full command line (null-separated) |
| `/proc/<PID>/exe` | Symlink to the executable binary (persists even if deleted from disk) |
| `/proc/<PID>/fd/` | Open file descriptors — reveals open files, sockets, pipes |
| `/proc/<PID>/maps` | Memory mappings — loaded libraries, heap, stack, anonymous regions |
| `/proc/<PID>/environ` | Environment variables at process start (may contain credentials) |
| `/proc/<PID>/status` | Process state, UID, GID, capabilities, thread count |

A critical forensic technique: if an attacker deletes their binary after execution, `/proc/<PID>/exe` still points to the deleted file and the kernel retains the inode. The binary can be recovered:

```bash
cp /proc/<PID>/exe /evidence/recovered_binary
```

### 8.4 Container forensics (overview)

Container forensics bridges host-level DFIR and the cloud/Kubernetes forensics covered in depth in Chapter 24B.

**Docker layer analysis.** Docker images consist of stacked filesystem layers (each stored as a diff tarball). The `docker diff` command shows filesystem changes in a running container relative to its image. For forensic analysis of a stopped container:

```bash
docker export <container_id> -o /evidence/container_fs.tar
docker inspect <container_id> > /evidence/container_metadata.json
docker logs <container_id> > /evidence/container_stdout.log 2>&1
```

Compare the exported filesystem against the original image layers to identify attacker modifications: added binaries, modified configuration files, and new cron jobs or SSH keys.

**Kubernetes audit logs.** K8s API server audit logs record every API request with: the requesting user/service account, the resource type and name, the verb (get, create, patch, delete), the request body, and the response code. Key events for forensic investigation: `exec` into pods (attacker establishing interactive shells), `create` of privileged pods or pods with `hostPID`/`hostNetwork` (container escape preparation), `create` or `patch` of Secrets (credential access), and `delete` of audit policy or logging configurations (anti-forensics). Detailed Kubernetes forensic procedures are in Chapter 24B.

### 8.5 macOS forensic artifacts

macOS presents a unique forensic landscape due to Apple's Unified Log, filesystem event tracking, and privacy-protection databases.

**Unified Log.** macOS's binary logging system (replacing ASL logs from Sierra onward) is queried with `log show` and collected with `log collect`. The log volume is enormous — targeted queries are essential:

```bash
# Collect logs for a specific time range (creates a .logarchive)
log collect --start "2026-05-01 00:00:00" --output /evidence/macos_logs.logarchive

# Query SSH activity
log show /evidence/macos_logs.logarchive --predicate 'process == "sshd"' --style compact

# Query process execution
log show --predicate 'eventMessage contains "execve"' --info --start "2026-05-07"

# Query TCC (Transparency, Consent, and Control) access decisions
log show --predicate 'subsystem == "com.apple.TCC"' --info

# Query Gatekeeper and quarantine events
log show --predicate 'subsystem == "com.apple.syspolicy"' --info
```

**FSEvents.** The FSEvents database (`/.fseventsd/`) records filesystem change events: file creation, deletion, modification, rename, and metadata changes. Each event has a flags field indicating the change type and a path. FSEvents are stored in compressed binary files that roll over based on size. Tools: `FSEventsParser` (Python) parses the raw `.fseventsd` directory:

```bash
python FSEventsParser.py -s /evidence/.fseventsd -o /evidence/fsevents.csv
```

FSEvents provide a filesystem-change timeline analogous to NTFS $UsnJrnl but for APFS/HFS+ volumes.

**Spotlight metadata.** The Spotlight index (`/.Spotlight-V100/`) stores metadata for every indexed file: file type, creation date, last-opened date, content keywords, and more. The `mdls` command queries metadata for a specific file; forensic tools parse the Spotlight database to recover metadata for deleted files still in the index.

**Quarantine events (XProtect).** When a file is downloaded from the internet, macOS applies a quarantine attribute (`com.apple.quarantine`) containing: the timestamp, the application that downloaded it (browser, email client), and the source URL. The quarantine database at `~/Library/Preferences/com.apple.LaunchServices.QuarantineEventsV2` (SQLite) records all quarantine events:

```bash
sqlite3 /evidence/QuarantineEventsV2 "SELECT datetime(LSQuarantineTimeStamp + 978307200, 'unixepoch') AS download_time, LSQuarantineAgentName AS app, LSQuarantineDataURLString AS url, LSQuarantineOriginURLString AS origin FROM LSQuarantineEvent ORDER BY LSQuarantineTimeStamp DESC;"
```

The offset `978307200` converts macOS Core Data timestamps (seconds since 2001-01-01) to Unix epoch.

**TCC database.** The TCC (Transparency, Consent, and Control) database records which applications have been granted access to protected resources (camera, microphone, Full Disk Access, screen recording, accessibility, contacts, etc.). Database locations:

```
/Library/Application Support/com.apple.TCC/TCC.db          — system-level
~/Library/Application Support/com.apple.TCC/TCC.db         — per-user
```

Forensic queries reveal applications with Full Disk Access (potential data exfiltration tool), accessibility access (keylogger capability), and screen recording access (surveillance capability).

**KnowledgeC.** The KnowledgeC database (`~/Library/Application Support/Knowledge/knowledgeC.db`) records detailed user activity: application usage (foreground time, sessions), device power state, screen lock/unlock events, media playback, Safari browsing activity, and Siri interactions. Timestamps and durations provide a granular timeline of user behavior.

**launchd plist analysis.** macOS persistence mechanisms center on `launchd` plists:

```
/Library/LaunchDaemons/           — system-wide daemons (root context)
/Library/LaunchAgents/            — system-wide agents (user session)
~/Library/LaunchAgents/           — per-user agents
```

Each plist specifies: `ProgramArguments` (the executable and arguments), `RunAtLoad` (execute at login/boot), `StartInterval` or `StartCalendarInterval` (periodic execution), and `WatchPaths` or `QueueDirectories` (filesystem-triggered execution). Identify attacker-installed plists by checking for: non-Apple reverse-DNS labels, executables in user-writable directories, Base64-encoded arguments, and plists created within the incident time window.

### 8.6 Mobile device forensics overview

Mobile forensics employs three extraction tiers of increasing invasiveness and completeness.

**Logical extraction.** Uses official APIs to copy accessible data (contacts, messages, call logs, photos, app data). On Android: `adb backup` or vendor-specific tools. On iOS: iTunes/Finder backup (encrypted backups contain Keychain data including saved passwords). Logical extraction does not recover deleted data.

**Filesystem extraction.** Accesses the full filesystem including application sandboxes and system databases. On Android: requires root access (achieved via `adb root` on eng builds, or exploitation). On iOS: requires a jailbreak or uses forensic tools (Cellebrite, GrayKey) that exploit bootrom or kernel vulnerabilities. Recovers deleted SQLite records via WAL (Write-Ahead Log) analysis and freelist page parsing.

**Physical extraction.** Raw bit-level dump of flash storage (NAND/NOR). Provides access to unallocated space for file carving. On Android: achieved via custom recovery images, JTAG, or chip-off. On iOS: extremely limited on modern devices due to Secure Enclave encryption.

**Android ADB forensic triage.** For quick evidence collection on an accessible Android device:

```bash
adb shell dumpsys activity activities > /evidence/android_activities.txt
adb shell dumpsys package > /evidence/android_packages.txt
adb pull /data/data/com.android.providers.contacts/databases/ /evidence/android_contacts/
adb pull /data/data/com.android.providers.telephony/databases/ /evidence/android_sms/
adb logcat -d > /evidence/android_logcat.txt
```

**iOS backup analysis.** iTunes/Finder backups (encrypted with a user-set password) are parsed with `idevicebackup2` from libimobiledevice or forensic suites. The `Manifest.db` SQLite database maps backup file hashes to their original filesystem paths, enabling targeted extraction of specific application databases (WhatsApp, Signal, Telegram message stores).

---

## 9. DFIR detection engineering

This section provides detection rules and automation content that extends the hunt packages in §6 with additional techniques, YARA rules for post-exploitation tooling on disk, Velociraptor artifact development, KAPE customization, and live-response scripting.

### 9.1 Sigma rules — additional coverage

The following Sigma rules cover techniques not addressed by the rules in §3.2 and §6.1-§6.3, avoiding duplication.

**DCOM lateral movement (T1021.003).** DCOM-based lateral movement spawns processes under `svchost.exe` hosting the DcomLaunch service, or under `mmc.exe` (via MMC20.Application):

```yaml
title: DCOM Lateral Movement via MMC20.Application
id: 8a2e6b3f-7d4c-4f9a-b1e5-3c8d2f7a9e6b
status: stable
description: Detects process execution via DCOM MMC20.Application abuse
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        ParentImage|endswith: '\mmc.exe'
    filter_legit:
        Image|endswith:
            - '\mmc.exe'
            - '\explorer.exe'
    condition: selection AND NOT filter_legit
level: high
tags:
    - attack.lateral_movement
    - attack.t1021.003
```

**WinRM lateral movement (T1021.006).** WinRM-spawned processes have `wsmprovhost.exe` as their parent:

```yaml
title: Suspicious Process via WinRM Provider
id: 4b7c9d2e-1a3f-4e8b-9d6c-5f2a8e3b7c1d
status: stable
description: Detects potentially malicious process execution via WinRM
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        ParentImage|endswith: '\wsmprovhost.exe'
    filter_legit:
        Image|endswith:
            - '\conhost.exe'
            - '\wsmprovhost.exe'
    condition: selection AND NOT filter_legit
level: medium
tags:
    - attack.lateral_movement
    - attack.t1021.006
```

**Registry Run Key persistence (T1547.001):**

```yaml
title: Registry Run Key Modification for Persistence
id: 6e9f2a3b-8c1d-4f7e-a5b4-2d3c1e8f7a6b
status: stable
description: Detects modification of registry Run keys for persistence
logsource:
    product: windows
    service: sysmon
detection:
    selection:
        EventID:
            - 12
            - 13
        TargetObject|contains:
            - '\CurrentVersion\Run\'
            - '\CurrentVersion\RunOnce\'
            - '\CurrentVersion\RunServices\'
            - '\Explorer\Shell Folders'
            - '\Explorer\User Shell Folders'
    filter_legit:
        Image|contains:
            - '\Windows\System32\'
            - '\Program Files\'
            - '\Program Files (x86)\'
    condition: selection AND NOT filter_legit
level: medium
tags:
    - attack.persistence
    - attack.t1547.001
```

**DNS tunneling detection (T1071.004).** DNS tunneling exfiltrates data by encoding it in DNS query labels. Indicators: high query volume to a single domain, unusually long subdomain labels (>30 characters), high entropy in query names, and TXT record queries to non-CDN domains:

```yaml
title: Potential DNS Tunneling Activity
id: 2c4e8f1a-3b7d-4a9e-8c5f-1d6b3e2a7f4c
status: experimental
description: Detects DNS query patterns consistent with DNS tunneling
logsource:
    product: windows
    service: sysmon
detection:
    selection:
        EventID: 22
    filter_long_subdomain:
        QueryName|re: '^[a-zA-Z0-9]{30,}\.'
    filter_high_volume:
        QueryName|endswith:
            - '.dnscat.'
            - '.dnstunnel.'
    condition: selection AND (filter_long_subdomain OR filter_high_volume)
level: high
tags:
    - attack.exfiltration
    - attack.command_and_control
    - attack.t1071.004
    - attack.t1048.003
```

**Data staging via archive creation (T1560.001).** Attackers compress data before exfiltration. Detect archive-tool invocations targeting sensitive directories:

```yaml
title: Data Staging via Archive Tool on Sensitive Path
id: 7f3a9c2d-4e8b-4b1a-9d5e-6c2f1a8b3d7e
status: experimental
description: Detects archive creation targeting potentially sensitive directories
logsource:
    category: process_creation
    product: windows
detection:
    selection_tools:
        Image|endswith:
            - '\7z.exe'
            - '\7za.exe'
            - '\rar.exe'
            - '\WinRAR.exe'
    selection_paths:
        CommandLine|contains:
            - '\Users\'
            - '\Documents\'
            - '\Desktop\'
            - '\Shares\'
            - '\Finance\'
            - '\HR\'
    condition: selection_tools AND selection_paths
level: medium
tags:
    - attack.collection
    - attack.t1560.001
```

**Large outbound transfer detection (T1048).** Proxy or firewall logs showing unusually large outbound transfers to a single destination:

```yaml
title: Large Outbound Data Transfer
id: 9a1b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d
status: experimental
description: Detects processes initiating large outbound network connections
logsource:
    product: windows
    service: sysmon
detection:
    selection:
        EventID: 3
        Initiated: 'true'
    filter_internal:
        DestinationIp|startswith:
            - '10.'
            - '172.16.'
            - '172.17.'
            - '172.18.'
            - '172.19.'
            - '172.20.'
            - '172.21.'
            - '172.22.'
            - '172.23.'
            - '172.24.'
            - '172.25.'
            - '172.26.'
            - '172.27.'
            - '172.28.'
            - '172.29.'
            - '172.30.'
            - '172.31.'
            - '192.168.'
    filter_browsers:
        Image|endswith:
            - '\chrome.exe'
            - '\msedge.exe'
            - '\firefox.exe'
    condition: selection AND NOT filter_internal AND NOT filter_browsers
level: low
falsepositives:
    - Legitimate file uploads
    - Cloud sync tools
tags:
    - attack.exfiltration
    - attack.t1048
```

### 9.2 YARA rules for post-exploitation tools

The Mimikatz in-memory YARA rule is in §2.1.2. The following rules target on-disk variants and additional post-exploitation tools.

**Rubeus (Kerberos abuse tool):**

```
rule Rubeus_Kerberos_Tool {
    meta:
        description = "Detects Rubeus Kerberos abuse tool on disk or in memory"
        reference = "https://github.com/GhostPack/Rubeus"
        severity = "CRITICAL"
    strings:
        $cmd1 = "asreproast" ascii wide
        $cmd2 = "kerberoast" ascii wide
        $cmd3 = "s4u" ascii wide
        $cmd4 = "createnetonly" ascii wide
        $cmd5 = "ptt" ascii wide
        $cmd6 = "harvest" ascii wide
        $cmd7 = "tgtdeleg" ascii wide
        $ns1 = "Rubeus.Commands" ascii
        $ns2 = "Rubeus.lib.Interop" ascii
        $ns3 = "Rubeus.Domain" ascii
        $str1 = "[*] Action: " ascii wide
        $str2 = "[*] Target Domain" ascii wide
        $str3 = "KRB_AS_REQ w/o preauth" ascii wide
        $str4 = "Ticket Granting Ticket" ascii wide
    condition:
        (3 of ($cmd*) and 1 of ($ns*)) or
        (2 of ($ns*)) or
        (3 of ($str*) and 2 of ($cmd*))
}
```

**SharpHound (BloodHound data collector):**

```
rule SharpHound_Collector {
    meta:
        description = "Detects SharpHound BloodHound data collector"
        reference = "https://github.com/BloodHoundAD/SharpHound"
        severity = "HIGH"
    strings:
        $ns1 = "SharpHound.Runtime" ascii
        $ns2 = "Sharphound.Client" ascii
        $ns3 = "SharpHoundCommonLib" ascii
        $str1 = "Initializing SharpHound" ascii wide
        $str2 = "CollectionMethodResolved" ascii wide
        $str3 = "Creating output channel" ascii wide
        $str4 = "_BloodHound" ascii wide
        $str5 = "SharpHound Enumeration Completed" ascii wide
        $json1 = "\"ObjectIdentifier\":" ascii
        $json2 = "\"PrimaryGroupSID\":" ascii
        $json3 = "\"AllowedToDelegate\":" ascii
        $method1 = "CollectionMethod" ascii wide
        $method2 = "--CollectionMethods" ascii wide
        $method3 = "SessionLoop" ascii wide
    condition:
        (2 of ($ns*)) or
        (3 of ($str*)) or
        (2 of ($json*) and 1 of ($method*)) or
        (2 of ($method*) and 2 of ($str*))
}
```

**Mimikatz on-disk variant** (complementing the in-memory rule in §2.1.2 — targets the PE binary rather than runtime strings):

```
rule Mimikatz_PE_Binary {
    meta:
        description = "Detects Mimikatz PE binary on disk via exports and version info"
        severity = "CRITICAL"
    strings:
        $export1 = "powershell_reflective_mimikatz" ascii
        $export2 = "mimikatz_initOrClean" ascii
        $export3 = "mimikatz_doLocal" ascii
        $vi_company = "gentilkiwi (Benjamin DELPY)" ascii wide
        $vi_product = "mimikatz" ascii wide
        $vi_desc = "mimikatz for Windows" ascii wide
        $pdb1 = "mimikatz.pdb" ascii
        $pdb2 = "mimilib.pdb" ascii
        $pdb3 = "mimidrv.pdb" ascii
    condition:
        uint16(0) == 0x5A4D and
        (any of ($export*) or
         ($vi_company and $vi_product) or
         any of ($pdb*))
}
```

### 9.3 Velociraptor artifact development

Velociraptor artifacts are VQL queries packaged with metadata for deployment via hunts or collections. A custom artifact definition:

```yaml
name: Custom.Windows.Detection.SuspiciousService
description: |
  Detects services with suspicious characteristics: services executing from
  temp directories, user profile paths, or with encoded command-line arguments.
type: CLIENT
parameters:
  - name: SuspiciousPaths
    type: regex
    default: "(Temp|AppData|ProgramData|Users\\\\[^\\\\]+\\\\)"
sources:
  - query: |
      LET services = SELECT Name, DisplayName, PathName, StartMode,
                            State, StartName
      FROM Artifact.Windows.System.Services()

      SELECT Name, DisplayName, PathName, StartMode, State, StartName,
             timestamp(epoch=now()) AS DetectionTime
      FROM services
      WHERE PathName =~ SuspiciousPaths
         OR PathName =~ "(?i)(powershell|cmd\\.exe.*(/c|/k)|mshta|rundll32)"
         OR PathName =~ "(?i)-enc[oded]*\\s"
```

**VQL for collecting forensic artifacts in bulk:**

```sql
-- Collect Prefetch, Amcache, ShimCache, and recent event logs in one hunt
LET prefetch = SELECT * FROM Artifact.Windows.Forensics.Prefetch()
LET amcache = SELECT * FROM Artifact.Windows.Detection.Amcache()
LET shimcache = SELECT * FROM Artifact.Windows.Registry.AppCompatCache()

SELECT * FROM chain(
    a={ SELECT *, "Prefetch" AS Source FROM prefetch },
    b={ SELECT *, "Amcache" AS Source FROM amcache },
    c={ SELECT *, "ShimCache" AS Source FROM shimcache }
)
```

### 9.4 KAPE target and module development

Custom KAPE targets are YAML files defining artifact collection paths. A target for collecting attacker-common staging directories:

```yaml
Description: Attacker staging directory collection
Author: DFIR Team
Version: 1.0
Id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
RecreateDirectories: true
Targets:
    -
        Name: ProgramData staging
        Category: SuspiciousLocations
        Path: C:\ProgramData\
        FileMask: '*.exe;*.dll;*.ps1;*.bat;*.vbs;*.js'
        Recursive: true
    -
        Name: Public profile staging
        Category: SuspiciousLocations
        Path: C:\Users\Public\
        Recursive: true
    -
        Name: Temp directories
        Category: SuspiciousLocations
        Path: C:\Windows\Temp\
        FileMask: '*.exe;*.dll;*.ps1;*.bat;*.vbs;*.js;*.zip;*.rar;*.7z'
        Recursive: true
    -
        Name: Perflogs (common APT staging)
        Category: SuspiciousLocations
        Path: C:\PerfLogs\
        Recursive: true
```

A custom module that chains multiple parsers in a processing pipeline:

```yaml
Description: Full forensic artifact processing pipeline
Category: ForensicParsing
Author: DFIR Team
Version: 1.0
Id: b2c3d4e5-f6a7-8901-bcde-f12345678901
BinaryUrl: null
Processors:
    -
        Executable: MFTECmd.exe
        CommandLine: -f %sourceDirectory%\C\$MFT --csv %destinationDirectory% --csvf mft.csv
        ExportFormat: csv
    -
        Executable: PECmd.exe
        CommandLine: -d %sourceDirectory%\C\Windows\Prefetch --csv %destinationDirectory% --csvf prefetch.csv
        ExportFormat: csv
    -
        Executable: AmcacheParser.exe
        CommandLine: -f %sourceDirectory%\C\Windows\appcompat\Programs\Amcache.hve --csv %destinationDirectory% --csvf amcache.csv -i
        ExportFormat: csv
    -
        Executable: EvtxECmd.exe
        CommandLine: -d %sourceDirectory%\C\Windows\System32\winevt\Logs --csv %destinationDirectory% --csvf evtx.csv
        ExportFormat: csv
```

### 9.5 Live-response automation scripts

**PowerShell live-response collector.** Gathers volatile and semi-volatile artifacts from a live Windows system:

```powershell
$OutDir = "C:\IR_Collection_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

# Network state
Get-NetTCPConnection | Select-Object LocalAddress,LocalPort,RemoteAddress,
    RemotePort,State,OwningProcess,
    @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}} |
    Export-Csv "$OutDir\netstat.csv" -NoTypeInformation

# Running processes with hashes
Get-Process | ForEach-Object {
    $hash = if ($_.Path) { (Get-FileHash $_.Path -Algorithm SHA256 -ErrorAction SilentlyContinue).Hash } else { "N/A" }
    [PSCustomObject]@{
        PID = $_.Id; Name = $_.ProcessName; Path = $_.Path;
        CommandLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine;
        ParentPID = $_.Parent.Id; SHA256 = $hash; StartTime = $_.StartTime
    }
} | Export-Csv "$OutDir\processes.csv" -NoTypeInformation

# Scheduled tasks
Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' } |
    Select-Object TaskName,TaskPath,State,
    @{N='Actions';E={$_.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" }}} |
    Export-Csv "$OutDir\scheduled_tasks.csv" -NoTypeInformation

# Autostart entries
Get-CimInstance Win32_StartupCommand |
    Export-Csv "$OutDir\autoruns.csv" -NoTypeInformation

# DNS cache
Get-DnsClientCache | Export-Csv "$OutDir\dns_cache.csv" -NoTypeInformation

# Recent PowerShell history per user
Get-ChildItem "C:\Users\*\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt" -ErrorAction SilentlyContinue |
    ForEach-Object { Copy-Item $_.FullName "$OutDir\ps_history_$($_.Directory.Parent.Parent.Parent.Parent.Name).txt" }

Write-Host "[+] Collection complete: $OutDir"
```

**Bash live-response collector for Linux:**

```bash
#!/usr/bin/env bash
set -euo pipefail
OUTDIR="/tmp/ir_collection_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTDIR"

# Network state
ss -tulnp > "$OUTDIR/listening_sockets.txt" 2>&1
ss -anp > "$OUTDIR/all_connections.txt" 2>&1

# Running processes
ps auxwwf > "$OUTDIR/processes_tree.txt"
ls -la /proc/*/exe 2>/dev/null > "$OUTDIR/proc_exe_links.txt"

# Open files (network and regular)
lsof -i -P -n > "$OUTDIR/lsof_network.txt" 2>&1
lsof +L1 > "$OUTDIR/lsof_deleted_files.txt" 2>&1

# Cron jobs (all users)
for user in $(cut -d: -f1 /etc/passwd); do
    crontab -l -u "$user" 2>/dev/null > "$OUTDIR/cron_${user}.txt"
done
cp -r /etc/cron.d "$OUTDIR/etc_cron_d/" 2>/dev/null || true

# Shell histories
find /home /root -maxdepth 2 -name ".*_history" -exec cp {} "$OUTDIR/" \; 2>/dev/null

# Recent logins
last -Fai > "$OUTDIR/last_logins.txt"
lastlog > "$OUTDIR/lastlog.txt"

# Systemd timers (persistence)
systemctl list-timers --all --no-pager > "$OUTDIR/systemd_timers.txt"
systemctl list-units --type=service --state=running --no-pager > "$OUTDIR/running_services.txt"

# Loaded kernel modules
lsmod > "$OUTDIR/kernel_modules.txt"

# Collect auth logs
cp /var/log/auth.log "$OUTDIR/" 2>/dev/null || cp /var/log/secure "$OUTDIR/" 2>/dev/null || true

echo "[+] Collection complete: $OUTDIR"
```

---

## 10. Advanced IR scenarios

### 10.1 Ransomware IR playbook

Ransomware incidents require immediate containment to stop encryption propagation, followed by a structured recovery process.

**Phase 1: Containment (0-4 hours).**

1. Network isolation. Disconnect affected segments at the switch level (VLAN isolation or port shutdown). Do not power off encrypted machines — memory may contain the encryption key. If Velociraptor or EDR is available, deploy a quarantine artifact (§5.4.1) to isolate endpoints while maintaining management connectivity.
2. Disable file shares. On domain controllers, disable the Server service or remove share permissions to prevent SMB-based propagation: `Set-SmbShare -Name "ShareName" -EncryptData $true -Force; Revoke-SmbShareAccess -Name "ShareName" -AccountName "Everyone" -Force`.
3. Disable compromised accounts. If the ransomware used stolen credentials for lateral movement, disable those accounts immediately. Reset the KRBTGT account password twice (with a 12-hour interval between resets per Microsoft guidance) if golden-ticket compromise is suspected.
4. Preserve evidence. Before wiping or rebuilding, capture memory dumps from encrypted systems (the ransomware process may still hold the encryption key in memory), image at least one encrypted disk, and collect event logs from the affected segment's domain controller.

**Phase 2: Assessment (4-24 hours).**

1. Identify the ransomware family. Submit ransom note text and encrypted file samples to ID Ransomware (id-ransomware.malwarehunterteam.com) or No More Ransom (nomoreransom.org). Check the note for known negotiation portals and cryptocurrency wallets.
2. Check decryptor availability. Known decryptors exist for older ransomware families and those with implementation flaws. No More Ransom, Emsisoft, and Kaspersky maintain decryptor repositories. Verify the decryptor matches the exact variant before running it on evidence copies.
3. Scope the blast radius. Use EDR telemetry, event logs, and network flow data to determine: how many systems are encrypted, the initial access vector (phishing email, exposed RDP, VPN vulnerability), the dwell time before encryption, and whether data was exfiltrated before encryption (double extortion).

**Phase 3: Recovery (24-72+ hours).**

1. Prioritize recovery order: domain controllers, authentication infrastructure, backup systems, then business-critical applications, then user workstations.
2. Rebuild from known-good images. Do not attempt to decrypt and reuse compromised systems — the attacker may have installed additional backdoors. Rebuild from golden images and restore data from offline/immutable backups.
3. Validate backup integrity. Before restoring, verify that backups were not encrypted or tampered with. Check backup timestamps against the estimated date of initial compromise — backups taken after compromise may contain the attacker's persistence mechanisms.

**Negotiation considerations.** Paying ransom is a business decision with legal, ethical, and practical implications. Factors: OFAC sanctions (paying sanctioned groups carries legal liability in the US), reliability of decryptors (some groups provide working decryptors, others do not), data-exfiltration leverage (paying the ransom may not prevent data publication), and cyber-insurance policy terms. The IR team provides technical input (recovery feasibility, data-loss assessment) but the payment decision belongs to executive leadership and legal counsel.

### 10.2 Business Email Compromise IR

BEC incidents involve unauthorized access to email accounts, typically for financial fraud. The investigation focuses on determining access scope, identifying fraudulent actions, and preventing further damage.

**Mailbox forensics.** Audit logs reveal the attacker's actions within the compromised mailbox. In Microsoft 365:

```powershell
# Search unified audit log for mailbox activity
Search-UnifiedAuditLog -StartDate "2026-05-01" -EndDate "2026-05-10" `
    -UserIds "compromised@company.com" `
    -Operations MailItemsAccessed,Send,MoveToDeletedItems,UpdateInboxRules,Set-Mailbox `
    -ResultSize 5000 | Export-Csv "C:\IR\mailbox_audit.csv" -NoTypeInformation
```

Key operations to investigate: `UpdateInboxRules` (attacker creating mail-forwarding rules to exfiltrate email silently), `Set-Mailbox` (auto-forwarding configuration), `Send` (emails sent by the attacker impersonating the victim), and `MailItemsAccessed` (which emails the attacker read — determines data-exposure scope).

**OAuth token analysis.** Modern BEC attacks use OAuth consent grants to maintain persistent access without needing the user's password. Investigate Azure AD sign-in logs for consent grants and application registrations:

```powershell
# Review OAuth application consents
Get-AzureADAuditSignInLogs -Filter "appId eq '<suspicious_app_id>'" |
    Select-Object CreatedDateTime, UserPrincipalName, IpAddress, Status

# List consent grants for the compromised user
Get-AzureADOAuth2PermissionGrant | Where-Object { $_.PrincipalId -eq $CompromisedUserId }
```

Revoke suspicious OAuth grants and rotate the user's refresh tokens. Check for attacker-registered applications in Azure AD that may provide ongoing access.

**Inbox-rule forensics.** The attacker's most common BEC persistence mechanism is a hidden inbox rule that auto-forwards incoming mail or moves specific messages to obscure folders (RSS Feeds, Conversation History, Deleted Items) to hide replies from the legitimate user. Enumerate and inspect all mailbox rules:

```powershell
# List inbox rules for the compromised mailbox
Get-InboxRule -Mailbox "compromised@company.com" |
    Select-Object Name, Enabled, Description, ForwardTo, ForwardAsAttachmentTo,
    RedirectTo, DeleteMessage, MoveToFolder, MarkAsRead |
    Format-List

# Check for SMTP forwarding at the mailbox level (bypasses inbox rules)
Get-Mailbox -Identity "compromised@company.com" |
    Select-Object ForwardingSMTPAddress, DeliverToMailboxAndForward
```

Suspicious indicators: rules with `ForwardTo` or `RedirectTo` pointing to external addresses, rules that `DeleteMessage` based on keywords like "invoice", "payment", "wire", "fraud", or "security", rules that `MoveToFolder` to rarely-checked folders, and rules created during the compromise window. Disable all attacker-created rules before notifying the user that their account has been recovered — otherwise the attacker receives the notification and pivots.

**Financial fraud recovery.** If the attacker initiated fraudulent wire transfers via impersonation emails: contact the receiving bank immediately (recovery success drops dramatically after 24 hours), file an IC3 complaint (FBI's Internet Crime Complaint Center), and preserve the fraudulent email chain (headers, body, and any attached invoices) as evidence for law enforcement and insurance claims.

### 10.3 Supply chain compromise IR

Supply chain attacks are among the most difficult IR scenarios because the malicious code arrives through a trusted channel: a software update, a compromised library, or a pre-infected hardware component.

**Identifying the vector.** The investigation starts by determining which trusted component was compromised:

1. Software update poisoning. Compare the hash of the installed update against the vendor's published hash (if available). Analyze the update package for modifications: additional DLLs, patched executables, or post-install scripts not present in clean versions. Examine the update's digital signature — a valid signature from the vendor's certificate indicates a deep compromise of the vendor's build pipeline (as in SolarWinds), while an invalid or missing signature suggests a man-in-the-middle or repository compromise.
2. Dependency poisoning. For open-source dependencies, compare `package-lock.json`, `requirements.txt`, `go.sum`, or equivalent lock files against known-good versions. Identify newly introduced or modified dependencies. Check package registries for typosquatting or version-confusion attacks.
3. Vendor access compromise. If the vendor had remote access (VPN, RMM tool, API keys), review access logs for the vendor's accounts for anomalous activity: unusual hours, unusual source IPs, or unusual actions.

**Scope assessment.** Determine which systems consumed the compromised component: software inventory databases, deployment logs, package-manager caches, and update-server access logs all provide scope data. The timeline of exposure (from when the compromised component was first deployed to when it was discovered) defines the investigation window.

**Vendor coordination.** Notify the vendor of the suspected compromise (they may not know). Establish a shared communication channel (encrypted, out-of-band from potentially compromised infrastructure). Coordinate on a remediation timeline: the vendor patches their distribution pipeline, you replace the compromised component. Preserve evidence of the compromise for potential legal proceedings and insurance claims.

### 10.4 Insider threat investigation

Insider threat investigations carry unique legal and procedural constraints that do not apply to external-threat IR.

**Legal considerations.** Before beginning the investigation, involve legal counsel and HR. Ensure the investigation is authorized under applicable employment law and privacy regulations. In many jurisdictions, monitoring employee activity requires prior notice (employment agreement, acceptable-use policy) or specific legal authorization. Evidence collected in violation of privacy laws may be inadmissible and expose the organization to liability.

**Evidence preservation.** Insider-threat evidence must be collected with chain-of-custody documentation suitable for potential litigation or regulatory proceedings. Use forensic imaging (not file-copy) for disk evidence. Document every investigative step with timestamps, analyst names, and justifications. Preserve original evidence in read-only storage; work only on verified copies.

**User activity reconstruction.** Build a comprehensive timeline of the suspect's activity across all available data sources:

- Authentication logs: logon/logoff times, VPN connections, badge access records (physical access).
- Email: messages sent/received (especially to personal email addresses or external entities), attachment sizes, and mail-rule changes.
- Endpoint telemetry: file access patterns (EDR file-access logs, Windows Object Access auditing Event ID 4663), USB device connections (§7.6), print jobs, and screenshot/screen-recording evidence.
- Cloud activity: file downloads from SharePoint/OneDrive/Google Drive (focus on bulk downloads), sharing-permission changes, and external sharing links created.
- Network: proxy logs showing uploads to personal cloud storage (Dropbox, Google Drive personal, WeTransfer), DNS queries to file-sharing services, and large outbound data transfers.

Correlate these data sources into a unified timeline (using Plaso/Timesketch per §4.1) to establish patterns of data access and exfiltration.

**VQL — bulk file access and USB exfiltration correlation.** Deploy this Velociraptor hunt to identify users who accessed large numbers of sensitive files and connected USB devices in the same time window:

```sql
-- Correlate USB device connections with bulk file access
LET usb_events = SELECT EventData.DeviceId AS DeviceId,
                        System.TimeCreated.SystemTime AS USBTime,
                        System.Computer AS Host
FROM Artifact.Windows.EventLogs.EvtxHunter(
    EvtxGlob="C:/Windows/System32/winevt/Logs/Microsoft-Windows-DriverFrameworks-UserMode%2FOperational.evtx",
    IdRegex="^2003$"
)

LET file_access = SELECT EventData.ObjectName AS FilePath,
                         EventData.SubjectUserName AS User,
                         System.TimeCreated.SystemTime AS AccessTime
FROM Artifact.Windows.EventLogs.EvtxHunter(
    EvtxGlob="C:/Windows/System32/winevt/Logs/Security.evtx",
    IdRegex="^4663$"
)
WHERE EventData.ObjectName =~ "(?i)(\\\\(finance|hr|confidential|restricted)\\\\)"

SELECT * FROM usb_events
WHERE USBTime > timestamp(string="2026-04-01")
```

**osquery — personal cloud storage detection:**

```sql
SELECT p.name, p.path, p.cmdline, p.uid,
       u.username, pp.name AS parent_name
FROM processes p
JOIN users u ON p.uid = u.uid
JOIN processes pp ON p.parent = pp.pid
WHERE p.name IN ('Dropbox.exe', 'OneDrive.exe', 'googledrivesync.exe',
                  'MEGAsync.exe', 'rclone.exe')
   OR p.cmdline LIKE '%rclone%copy%'
   OR p.cmdline LIKE '%rclone%sync%';
```

Detection of `rclone` specifically is high-priority — it is commonly abused by both insiders and ransomware operators for rapid data exfiltration to cloud storage.

### 10.5 Multi-stage APT IR

Advanced persistent threat incidents involve sophisticated adversaries with extended dwell times (weeks to months), multiple persistence mechanisms, and deliberate anti-forensics measures. The IR process is iterative and may span weeks.

**Initial access identification.** APT initial access vectors include: spear-phishing with zero-day or macro-enabled documents, exploitation of internet-facing services (VPN concentrators, web servers, email gateways), compromised credentials purchased from initial access brokers, and supply-chain compromise (§10.3). Identifying the initial access vector is critical for two reasons: it determines the scope of the investigation (all systems accessible from the entry point must be examined) and it informs remediation (the vector must be closed before recovery, or the adversary will simply re-enter).

Techniques for finding initial access: work backward from the earliest known-bad indicator. If the first detection was lateral movement at time T, examine network logs, email logs, and endpoint telemetry for the 30-90 days before T. Look for: anomalous VPN connections (unusual hours, unusual source countries), phishing emails to the earliest-compromised user, web-server exploitation artifacts in access logs, and new user accounts or service accounts created before T.

**Lateral movement mapping.** APT actors move methodically through the network. Map their path by correlating: Type 3 (network logon) Event ID 4624 events across hosts, service installations (Event ID 7045) correlated across time, remote scheduled-task creation (Event ID 4698), and named-pipe connections (Sysmon Event IDs 17/18 for PsExec-style tools). Build a graph of compromised hosts with edges representing lateral-movement events, annotated with timestamps and techniques. This graph reveals: the adversary's objectives (what they moved toward), their operational tempo (time between movements), and the full scope of compromise.

**Persistence removal.** APT actors install multiple persistence mechanisms across different hosts to survive partial remediation. Common persistence inventory:

1. Scheduled tasks and services (check all compromised hosts).
2. Registry Run keys and Winlogon modifications.
3. WMI event subscriptions.
4. DLL search-order hijacking in system directories.
5. Backdoored legitimate tools (trojanized DLLs replacing genuine system libraries).
6. Webshells on internet-facing servers.
7. Golden/Silver Kerberos tickets (require KRBTGT password reset).
8. OAuth application grants and federated trust abuse (Azure AD).

Remediation must address all persistence mechanisms simultaneously — a coordinated "eviction day" where all compromised hosts are rebuilt and all compromised credentials are rotated within the same maintenance window. Partial remediation (cleaning one host at a time) allows the adversary to re-compromise cleaned hosts from their remaining footholds.

**Long-term monitoring.** After eviction, maintain heightened monitoring for 90+ days. Deploy targeted detections for the specific TTPs observed during the incident. Monitor for: re-establishment of C2 channels (the same domains, IPs, or JA3 hashes), re-creation of persistence mechanisms, and exploitation of the same initial access vector. The adversary may attempt to re-enter using previously-stolen credentials, dormant backdoors missed during remediation, or a completely different initial access vector if they have strategic interest in the target.

Cross-reference Domain 25 (Threat Intelligence) for IOC management and adversary tracking during extended APT IR engagements. Cross-reference Domain 27C for building durable detection rules from APT incident findings.

---

## 11. Cross-references

**To Domain 11 (malware):** Memory forensics (§2) detects the injection techniques from Chapter 11A §1 (Malfind finds injected code), the rootkit techniques from Chapter 11A §3 (PsScan reveals DKOM-hidden processes), and the C2 connections from Chapter 11A §5 (NetScan reveals network connections to C2 infrastructure).

**To Domain 14 (AD):** Windows Event Log analysis (§4.5) detects the AD attacks from Chapter 14A: Event ID 4662 with replication rights detects DCSync (§6.3), Event ID 4768/4769 anomalies detect Kerberoasting and AS-REP Roasting, Event ID 4720/4728/4732 detect account creation and group modifications. The Windows registry forensics in §7.1 directly supports the AD persistence and credential-theft investigations from Domain 14.

**To Domain 10 (cloud):** Cloud log analysis (§4.5) detects the cloud attacks from Chapter 10A: CloudTrail events for `AssumeRole`, `PutBucketPolicy`, `StopLogging`; Azure Sign-in Logs for MFA fatigue, device-code abuse, and consent-grant phishing.

**To Domain 2 (OS primitives):** NTFS internals (§1.1) build on the filesystem concepts from Domain 2 Chapter 2A. ext4 inodes and the extent tree are the on-disk representation of the `vm_area_struct` memory mappings described in Chapter 2A §2. The process structures analyzed by Volatility (`EPROCESS`, `task_struct`) are the same kernel data structures described in Domain 2.

**To Domain 24B (cloud/container forensics):** This chapter covers host-level disk, memory, and endpoint forensics. Chapter 24B covers cloud-native forensics (AWS/Azure/GCP log analysis, container forensics, K8s audit), enterprise IR playbooks (ransomware, BEC, supply chain), and evidence handling procedures (chain of custody, ISO 27037, expert witness). The two chapters form a complete DFIR reference when read together.

**To Domain 25 (Threat Intelligence):** IOC management, adversary tracking, and STIX/TAXII feed integration support the extended investigation cycles in §10.5 (multi-stage APT IR) and the detection-engineering workflows in §9.

**To Domain 27C (Detection Engineering):** The Sigma rules in §9.1 and YARA rules in §9.2 feed into the detection-engineering lifecycle described in Domain 27C. Detection rules derived from IR findings (§10) should be promoted through the Domain 27C validation pipeline before production deployment.

---

## Exercises

1. **Memory forensics with Volatility 3.** Acquire a memory image from a Windows 10/11 VM using WinPmem. Using Volatility 3, run `windows.pslist`, `windows.psscan`, and `windows.malfind` to identify a simulated injected process. Compare PsList and PsScan output, document any DKOM-hidden processes, and extract suspicious VAD regions with `windows.dumpfiles`. Write a short report identifying the injected PID, the injection technique, and the YARA rule that would detect the in-memory artifact.

2. **Forensic disk imaging and NTFS artifact extraction.** Using a prepared USB drive containing planted evidence, create an E01 image with `ewfacquire` (including case metadata and SHA-256 hashing). Mount the image read-only and extract the $MFT with FTK Imager. Parse the $MFT with MFTECmd, identify three timestomped files by comparing $SI and $FN timestamps, and correlate findings against $UsnJrnl entries to establish the true file-creation times.

3. **Timeline analysis with Plaso/Timesketch.** Given a forensic image from a compromised Linux server, run `log2timeline.py` with the `linux` parser preset to generate a Plaso storage file. Export the timeline to Timesketch, establish a pivot point from a known SSH brute-force event (auth.log), and use the windowing methodology (+/- 2 hours, then +/- 24 hours) to identify the attacker's lateral-movement chain. Document at least five pivot events and their timestamps.

4. **KAPE triage collection and processing.** On a live Windows endpoint with simulated compromise artifacts, execute a KAPE `KapeTriage` collection targeting event logs, registry hives, Prefetch, AmCache, and $MFT. Process the collected artifacts using KAPE's module mode with MFTECmd, EvtxECmd, PECmd, and AmcacheParser. Cross-reference the parsed outputs to build a timeline of the attacker's activity from initial execution through persistence installation.

5. **Velociraptor fleet-wide IOC hunt.** Deploy Velociraptor server and enroll three Windows endpoints. Write a VQL hunt that searches all endpoints for: (a) files matching a specific SHA-256 hash in user-writable directories, (b) scheduled tasks containing `powershell -enc`, and (c) network connections to a specified C2 IP range. Execute the hunt, analyze results, and draft a scoping report identifying all affected endpoints with evidence timestamps.

---

## Readings and References

- NIST SP 800-86 — *Guide to Integrating Forensic Techniques into Incident Response* (August 2006; current version). <https://csrc.nist.gov/pubs/sp/800/86/final> (retrieved: 2026-05-29)
- NIST SP 800-61 Rev. 2 — *Computer Security Incident Handling Guide* (August 2012). <https://csrc.nist.gov/pubs/sp/800/61/r2/final> (retrieved: 2026-05-29)
- Volatility 3 documentation and plugin reference. <https://volatility3.readthedocs.io/en/latest/> (retrieved: 2026-05-29)
- Velociraptor documentation — VQL reference and artifact library. <https://docs.velociraptor.app/> (retrieved: 2026-05-29)
- Hale Ligh, M., Case, A., et al. *The Art of Memory Forensics*. Wiley, 2014. ISBN 978-1118825099.
- Zimmerman, Eric. KAPE documentation and tool suite. <https://ericzimmerman.github.io/KapeDocs/> (retrieved: 2026-05-29)
- Plaso (log2timeline) documentation. <https://plaso.readthedocs.io/en/latest/> (retrieved: 2026-05-29)
- SANS DFIR poster — *Windows Forensic Analysis*. <https://www.sans.org/posters/windows-forensic-analysis/> (retrieved: 2026-05-29)
- Carrier, Brian. *File System Forensic Analysis*. Addison-Wesley, 2005. ISBN 978-0321268174.
- MITRE ATT&CK — Defense Evasion: Indicator Removal (T1070). <https://attack.mitre.org/techniques/T1070/> (retrieved: 2026-05-29)

---

## Cross-Reference Matrix

| Domain / Chapter | Relationship to This Chapter | Key Linked Sections |
|---|---|---|
| Domain 2 — OS Primitives | NTFS/ext4 filesystem structures, kernel process data structures (`EPROCESS`, `task_struct`) analyzed by Volatility | §1.1, §1.2, §2.1, §2.2 |
| Domain 10 — Cloud Security | Cloud log analysis (CloudTrail, Azure Monitor, GCP Audit Logs) for cloud-based incident detection | §4.5 |
| Domain 11 — Malware Analysis | Memory forensics detects injection (Malfind), rootkits (PsScan), and C2 (NetScan) from Chapter 11A | §2.1, §2.2, §6.3 |
| Domain 14 — Active Directory | Windows Event Log analysis detects DCSync (4662), Kerberoasting (4769), account manipulation | §4.5, §6.3, §7.1 |
| Domain 24B — Cloud/Container IR | Extends host-level forensics to cloud-native (AWS/Azure/GCP), container, and enterprise IR playbooks | §4.5, §5.1–§5.4 |
| Domain 25 — Threat Intelligence | IOC management, adversary tracking, and STIX/TAXII feeds support extended APT investigations | §5.5, §6.1–§6.3 |

---

## Glossary

- **$MFT (Master File Table):** NTFS metadata file containing one 1024-byte entry per file/directory; stores $STANDARD_INFORMATION and $FILE_NAME timestamps, data run lists, and attribute metadata.
- **ASLR (Address Space Layout Randomization):** OS mitigation that randomizes memory layout; relevant to memory forensics because kernel structure offsets vary across boots.
- **Chain of custody:** Documented chronological history of evidence handling from acquisition through analysis and presentation, ensuring integrity and admissibility.
- **DKOM (Direct Kernel Object Manipulation):** Rootkit technique that unlinks process `EPROCESS` structures from the kernel's `ActiveProcessLinks` list to hide from process enumeration.
- **E01 (EnCase Evidence File):** Forensic image format providing compression, segmentation, integrated MD5/SHA-1 hashing, and case metadata embedding.
- **INDX slack:** Residual data in NTFS B-tree index records that may contain directory entries of deleted files, recoverable even after MFT entry reallocation.
- **ISF (Intermediate Symbol Format):** Volatility 3's symbol-table format mapping kernel data-structure offsets for a specific OS build, enabling correct parsing of memory images.
- **KAPE (Kroll Artifact Parser and Extractor):** Triage tool operating in Target (collection) and Module (parsing) modes for rapid forensic artifact acquisition and processing.
- **Order of volatility:** Evidence-acquisition priority sequence from most volatile (CPU registers, RAM) to least volatile (disk), per RFC 3227.
- **Pivot point:** The first confirmed indicator of compromise in a timeline; the anchor from which backward (root cause) and forward (impact) analysis expands.
- **Plaso (log2timeline):** Super-timeline tool that extracts timestamps from dozens of artifact sources and normalizes them into a unified chronological format.
- **Sigma rule:** Platform-agnostic YAML detection signature for SIEM/EDR systems, compilable to Splunk SPL, Elastic KQL, Microsoft Sentinel KQL, and others.
- **Timestomping:** Anti-forensics technique modifying $STANDARD_INFORMATION timestamps via user-mode APIs; detected by comparing against $FILE_NAME timestamps.
- **VQL (Velociraptor Query Language):** SQL-like language for querying endpoint artifacts via Velociraptor agents, supporting fleet-wide hunts and real-time collection.
- **Write-blocker:** Hardware or software mechanism preventing any write operations to source evidence media during forensic acquisition.
