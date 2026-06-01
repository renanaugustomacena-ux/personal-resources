# Scenario 02 — ZFS Degraded Pool Recovery

> **Modulo di riferimento:** [25-zfs-guida-operativa.md](../25-zfs-guida-operativa.md)
> **Tempo stimato:** 1.5-2 ore
> **Livello:** proficient
> **Prerequisiti:** VM con pool ZFS su ≥ 3 dischi virtuali, completamento moduli 06, 25
> **Ultimo aggiornamento:** 2026-05-23

---

## Scenario

Un server di produzione ha un pool ZFS raidz1 con 3 dischi. Il monitoring ha segnalato errori I/O su uno dei dischi e il pool è in stato DEGRADED. Il tuo compito è:

1. Diagnosticare il problema
2. Sostituire il disco difettoso senza downtime
3. Verificare l'integrità dei dati
4. Documentare la procedura

---

## Setup Lab (15 min)

### Creare l'ambiente di test

```bash
# Creare 3 file-backed vdev (simulano dischi)
mkdir -p /zfslab
for i in 1 2 3; do
    truncate -s 1G /zfslab/disk${i}.img
done

# Creare pool raidz1
zpool create labpool raidz1 /zfslab/disk1.img /zfslab/disk2.img /zfslab/disk3.img

# Popolare con dati
for i in $(seq 1 100); do
    dd if=/dev/urandom of=/labpool/file_${i}.dat bs=1K count=$((RANDOM % 512 + 1)) 2>/dev/null
done

# Creare snapshot di riferimento
zfs snapshot labpool@before-failure

# Verificare stato iniziale
zpool status labpool
zpool list labpool
```

### Simulare il guasto

```bash
# Corrompere un disco
dd if=/dev/urandom of=/zfslab/disk2.img bs=1M count=100 conv=notrunc 2>/dev/null

# Forzare ZFS a rilevare il problema
zpool scrub labpool

# Attendere completamento scrub
while zpool status labpool | grep -q "scrub in progress"; do
    sleep 2
done

# Verificare stato
zpool status labpool
# Deve mostrare DEGRADED con errori su disk2
```

---

## Fase 1 — Diagnosi (15 min)

### 1.1 Valutare lo stato del pool

```bash
# Stato dettagliato
zpool status -v labpool

# Interpretare l'output:
# state: DEGRADED  ← il pool funziona ma senza ridondanza
# scan: scrub ... with N errors
# config:
#   NAME                    STATE     READ WRITE CKSUM
#   labpool                 DEGRADED     0     0     0
#     raidz1-0              DEGRADED     0     0     0
#       /zfslab/disk1.img   ONLINE       0     0     0
#       /zfslab/disk2.img   UNAVAIL      X     X     X  ← disco guasto
#       /zfslab/disk3.img   ONLINE       0     0     0
```

### 1.2 Verificare integrità dati

```bash
# Controllare se ci sono dati persi
zpool status -v labpool | grep -A 20 "errors:"

# Con raidz1 e un solo disco guasto, tutti i dati devono essere recuperabili
# Se si vedono "permanent errors", il danno è più esteso

# Verificare leggibilità dei file
find /labpool -type f -exec md5sum {} \; > /tmp/checksums-degraded.txt 2>&1
grep -c "^" /tmp/checksums-degraded.txt  # contare file leggibili
```

### 1.3 Controllare smart (su dischi reali)

```bash
# Su dischi reali si userebbe:
# smartctl -a /dev/sdX
# smartctl -t long /dev/sdX

# Cercare:
# - Reallocated Sector Count elevato
# - Current Pending Sector > 0
# - Offline Uncorrectable > 0
# - SMART overall-health: FAILED
```

---

## Fase 2 — Sostituzione Disco (20 min)

### 2.1 Preparare il disco di sostituzione

```bash
# Creare il nuovo disco
truncate -s 1G /zfslab/disk2_new.img

# Su sistemi reali:
# 1. Identificare fisicamente il disco guasto (led, serial number)
# 2. Installare il nuovo disco
# 3. Verificare che sia visibile: lsblk, fdisk -l
```

### 2.2 Sostituire il vdev

```bash
# Sostituire il disco guasto
zpool replace labpool /zfslab/disk2.img /zfslab/disk2_new.img

# Monitorare il resilver
watch -n 2 zpool status labpool

# Il resilver ricostruisce i dati del disco guasto sulla nuova unità
# usando la parità dei dischi rimanenti
```

### 2.3 Attendere il completamento del resilver

```bash
# Monitorare progresso
while zpool status labpool | grep -q "resilver in progress"; do
    progress=$(zpool status labpool | grep -oP '\d+\.\d+% done')
    echo "Resilver: $progress"
    sleep 5
done

echo "Resilver completato!"
zpool status labpool
# Stato deve essere ONLINE (non più DEGRADED)
```

---

## Fase 3 — Verifica Post-Sostituzione (15 min)

### 3.1 Scrub di verifica

```bash
# Eseguire un scrub completo per verificare integrità
zpool scrub labpool

# Attendere completamento
while zpool status labpool | grep -q "scrub in progress"; do
    sleep 2
done

# Verificare risultato
zpool status labpool
# "scan: scrub repaired 0B ... with 0 errors" ← successo
```

### 3.2 Confronto checksums

```bash
# Verificare che tutti i file siano identici a prima del guasto
find /labpool -type f -exec md5sum {} \; > /tmp/checksums-recovered.txt 2>&1

# I checksum devono corrispondere se il raidz1 ha funzionato
diff /tmp/checksums-degraded.txt /tmp/checksums-recovered.txt && echo "INTEGRITÀ OK"
```

### 3.3 Verificare snapshot

```bash
# Lo snapshot deve essere ancora accessibile
zfs list -t snapshot labpool
ls /labpool/.zfs/snapshot/before-failure/

# Verificare rollback possibile
zfs clone labpool@before-failure labpool/recovery-test
ls /labpool/recovery-test/
zfs destroy labpool/recovery-test
```

---

## Fase 4 — Cleanup e Documentazione (10 min)

### 4.1 Rimuovere il vecchio disco dal pool

```bash
# Verificare che il vecchio disco non sia più referenziato
zpool status labpool

# Il vecchio device dovrebbe essere stato automaticamente rimosso
# dopo il replace. Se appare ancora:
# zpool detach labpool /zfslab/disk2.img  # solo per mirror
```

### 4.2 Documentare la procedura

Registrare nel runbook:

| Step | Azione | Comando | Tempo |
|------|--------|---------|-------|
| 1 | Diagnosi | `zpool status -v` | 5 min |
| 2 | Verifica SMART | `smartctl -a /dev/sdX` | 5 min |
| 3 | Sostituzione | `zpool replace pool old new` | 1 min |
| 4 | Resilver | Automatico, monitorare | variabile |
| 5 | Scrub verifica | `zpool scrub pool` | variabile |
| 6 | Cleanup | Rimuovere vecchio disco | 5 min |

### 4.3 Cleanup lab

```bash
zpool destroy labpool
rm -rf /zfslab
```

---

## Sfide Extra

1. **Dual failure**: su un raidz2 con 4 dischi, simulare il guasto di 2 dischi. Come cambia la procedura?
2. **Hot spare**: configurare un hot spare e verificare che il resilver parta automaticamente.
3. **ZFS send durante degraded**: eseguire un backup `zfs send` mentre il pool è degraded. Funziona?

---

## Criteri di Completamento

- [ ] Pool creato e popolato con dati di test
- [ ] Guasto simulato e pool in stato DEGRADED
- [ ] Diagnosi corretta (identificato il disco guasto)
- [ ] Sostituzione eseguita con `zpool replace`
- [ ] Resilver completato con successo
- [ ] Scrub di verifica senza errori
- [ ] Integrità dati confermata (checksum match)
- [ ] Procedura documentata nel runbook

---

## Riferimenti

- OpenZFS Documentation — https://openzfs.github.io/openzfs-docs/ (consultato: 2026-05-23)
- [25-zfs-guida-operativa.md](../25-zfs-guida-operativa.md)
- [06-storage.md](../06-storage.md)
