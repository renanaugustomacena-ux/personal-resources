# Automazione tramite API REST di Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 5 — Operativita post-migrazione · Modulo 14.2 (chiude sezione automazione, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** Proxmox cluster operativo; HTTP/REST basics, JSON; Python o Bash + `curl`; concetti di token auth, rate limit, idempotency; fluenza con webhook.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. autenticare richieste API con **token API** (`pveum user token add ...`) o ticket session-based (deprecated per scripting);
> 2. invocare endpoint principali (`/api2/json/cluster/status`, `/nodes/<node>/qemu`, `/nodes/<node>/qemu/<vmid>/status/start`) via `curl` o `proxmoxer` (Python);
> 3. costruire script di **migrazione batch** (provisioning multiple VM in parallelo) con gestione errori robusta;
> 4. applicare **rate limiting**: l'API Proxmox accetta ~30 req/s; oltre, errori 429 — implementare retry con backoff;
> 5. gestire **token refresh** per token con TTL (rotation policy);
> 6. implementare **partial-state cleanup**: se uno script di provisioning fallisce a meta, le VM create devono essere o committed o rollback (transazionale) o documented (out-of-band cleanup);
> 7. orchestrare con **Ansible proxmox modules** (`community.general.proxmox*`) e **Terraform Telmate provider** per IaC dichiarativo.
> **Tempo stimato:** lettura 60-90 min · lab 360 min (script Python end-to-end + test failure scenarios)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; proxmoxer 2.0+; Ansible 2.16+; Terraform Telmate provider 3.x; Python 3.11+.

## Mappa concettuale

```
+============================================================+
|     Proxmox API: stack di automazione                       |
+============================================================+
|                                                            |
|   AUTH                                                     |
|   - pveum user token add admin@pve api-script              |
|     → genera token "admin@pve!api-script=UUID"             |
|   - HTTP header: Authorization: PVEAPIToken=...            |
|   - TLS verify: SEMPRE in produzione                       |
|                                                            |
|   ENDPOINTS PRINCIPALI                                     |
|   GET  /api2/json/cluster/status                           |
|   GET  /api2/json/nodes/<node>/qemu                        |
|   POST /api2/json/nodes/<node>/qemu (create VM)            |
|   POST /api2/json/nodes/<node>/qemu/<vmid>/clone           |
|   POST /api2/json/nodes/<node>/qemu/<vmid>/migrate         |
|   POST /api2/json/nodes/<node>/qemu/<vmid>/status/start    |
|                                                            |
|   ASYNC TASKS                                              |
|   Most write operations return UPID:                       |
|     UPID:pve1:00012345:abc:00000000:qmstart:100:user@pve:  |
|   Polling: GET /api2/json/nodes/<node>/tasks/<UPID>/status |
|     → status, exitstatus                                   |
|                                                            |
|   ERROR HANDLING                                           |
|   200 OK                                                   |
|   400 Bad Request (validation)                             |
|   401 Unauthorized (bad token)                             |
|   403 Forbidden (no permission)                            |
|   429 Too Many Requests (rate limit)                       |
|   500/502/503 server errors                                |
|                                                            |
|   IDEMPOTENCY                                              |
|   - Tag risorse con request-id custom                      |
|   - Verifica esistenza prima di create                     |
|   - Cleanup partial-state in catch                         |
|                                                            |
|   TOOLS                                                    |
|   curl + jq           ad-hoc scripting bash                |
|   proxmoxer (Python)  client library                       |
|   Ansible             provisioning dichiarativo            |
|   Terraform Telmate   IaC                                  |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Token API > ticket session per scripting.** Token sono long-lived, ticket scadono in 2 ore. Per cron job e scripting headless, sempre token. Per uso umano interattivo, ticket.
2. **Rate limit e errore reale, non teorico.** Provisioning di 100 VM in loop sequenziale colpisce 429. Implementare semaphore (max 10 req parallele) + backoff esponenziale.
3. **Partial-state cleanup e la differenza tra script production-ready e script demo.** "L'ho creato a meta e ho avuto un errore" = stato sporco. Try/finally, transactional pattern, idempotency.
4. **Ansible e Terraform sono complementari, non alternative.** Terraform per infrastructure shape (VM, network, storage). Ansible per configuration (packages, services). IaC + config management = full coverage.

---

## Introduzione

Proxmox VE espone una API REST completa che permette di gestire ogni aspetto dell'infrastruttura virtuale in modo programmatico. Questa API rappresenta il fondamento su cui si basano tutti gli strumenti di automazione (Terraform, Ansible, interfacce web personalizzate) e costituisce il punto di accesso diretto per script personalizzati e integrazioni con sistemi esistenti.

Nel contesto della migrazione da VMware, l'API Proxmox sostituisce le API di vCenter/vSphere e offre un'interfaccia più diretta e meno stratificata. Questo documento illustra come utilizzare l'API Proxmox con diversi linguaggi e strumenti, dalla libreria Python `proxmoxer` agli script Bash con `curl`, fino alla costruzione di script di automazione complessi per la migrazione.

---

## Riferimento API REST

### Struttura dell'API

L'API Proxmox è accessibile all'endpoint:

```
https://<host>:8006/api2/json/
```

La documentazione interattiva è disponibile su ogni nodo Proxmox all'indirizzo:

```
https://<host>:8006/pve-docs/api-viewer/
```

### Principali Endpoint

| Endpoint | Metodo | Descrizione |
|---|---|---|
| `/access/ticket` | POST | Ottenere ticket di autenticazione |
| `/nodes` | GET | Elencare i nodi del cluster |
| `/nodes/{node}/qemu` | GET | Elencare VM su un nodo |
| `/nodes/{node}/qemu/{vmid}/status/current` | GET | Stato corrente di una VM |
| `/nodes/{node}/qemu/{vmid}/status/start` | POST | Avviare una VM |
| `/nodes/{node}/qemu/{vmid}/status/stop` | POST | Fermare una VM |
| `/nodes/{node}/qemu/{vmid}/status/shutdown` | POST | Spegnimento ordinato VM |
| `/nodes/{node}/qemu/{vmid}/status/reboot` | POST | Riavviare una VM |
| `/nodes/{node}/qemu/{vmid}/clone` | POST | Clonare una VM |
| `/nodes/{node}/qemu/{vmid}/migrate` | POST | Migrare una VM |
| `/nodes/{node}/qemu/{vmid}/snapshot` | GET/POST | Gestire snapshot |
| `/nodes/{node}/qemu/{vmid}/config` | GET/PUT | Configurazione VM |
| `/nodes/{node}/qemu` | POST | Creare una nuova VM |
| `/nodes/{node}/qemu/{vmid}` | DELETE | Eliminare una VM |
| `/nodes/{node}/lxc` | GET/POST | Gestire container LXC |
| `/nodes/{node}/storage` | GET | Elencare storage |
| `/nodes/{node}/network` | GET | Elencare interfacce di rete |
| `/nodes/{node}/tasks` | GET | Elencare task |
| `/nodes/{node}/tasks/{upid}/status` | GET | Stato di un task |
| `/cluster/resources` | GET | Risorse del cluster |
| `/cluster/tasks` | GET | Task del cluster |
| `/cluster/status` | GET | Stato del cluster |
| `/pools` | GET/POST | Gestione pool |

---

## Metodi di Autenticazione

### Metodo 1: Ticket (Cookie)

Il metodo ticket è utile per sessioni interattive e richiede due elementi:
- Un cookie `PVEAuthCookie`
- Un header `CSRFPreventionToken` per le richieste di modifica (POST, PUT, DELETE)

```bash
# Ottenere il ticket di autenticazione
RESPONSE=$(curl -s -k -d "username=root@pam&password=YourPassword" \
  https://pve01.example.local:8006/api2/json/access/ticket)

# Estrarre ticket e CSRF token
TICKET=$(echo "$RESPONSE" | jq -r '.data.ticket')
CSRF_TOKEN=$(echo "$RESPONSE" | jq -r '.data.CSRFPreventionToken')

# Utilizzare il ticket per le richieste successive
curl -s -k \
  -b "PVEAuthCookie=$TICKET" \
  https://pve01.example.local:8006/api2/json/nodes

# Per richieste POST/PUT/DELETE, aggiungere il CSRF token
curl -s -k \
  -b "PVEAuthCookie=$TICKET" \
  -H "CSRFPreventionToken: $CSRF_TOKEN" \
  -X POST \
  https://pve01.example.local:8006/api2/json/nodes/pve01/qemu/100/status/start
```

### Metodo 2: API Token (Raccomandato)

Gli API token sono persistenti, non scadono e non richiedono CSRF token. Sono il metodo raccomandato per l'automazione.

```bash
# Formato dell'header di autenticazione
# Authorization: PVEAPIToken=USER@REALM!TOKENID=TOKEN_SECRET

# Esempio
curl -s -k \
  -H "Authorization: PVEAPIToken=terraform@pve!automation-token=a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  https://pve01.example.local:8006/api2/json/nodes
```

### Creazione API Token

```bash
# Creare un utente dedicato per l'automazione
pveum user add automation@pve --comment "Utente per automazione API"

# Creare il ruolo con i permessi necessari
pveum role add AutomationRole -privs \
  "VM.Allocate,VM.Clone,VM.Config.CDROM,VM.Config.Cloudinit,VM.Config.CPU,\
VM.Config.Disk,VM.Config.HWType,VM.Config.Memory,VM.Config.Network,\
VM.Config.Options,VM.Audit,VM.Monitor,VM.PowerMgmt,VM.Snapshot,\
VM.Snapshot.Rollback,VM.Migrate,VM.Console,\
Datastore.AllocateSpace,Datastore.AllocateTemplate,Datastore.Audit,\
Sys.Audit,Sys.Console,Sys.Modify,SDN.Use,Pool.Allocate,Pool.Audit"

# Assegnare il ruolo
pveum aclmod / -user automation@pve -role AutomationRole

# Creare il token (privsep=0 per ereditare tutti i permessi dell'utente)
pveum user token add automation@pve automation-token --privsep=0

# Con privsep=1, il token ha solo i permessi esplicitamente assegnati
pveum user token add automation@pve readonly-token --privsep=1
pveum aclmod / -token 'automation@pve!readonly-token' -role PVEAuditor
```

---

## Automazione con Python e Proxmoxer

### Installazione

```bash
pip install proxmoxer requests paramiko
```

### Classe Wrapper per Proxmox API

```python
#!/usr/bin/env python3
"""
proxmox_manager.py - Classe wrapper per la gestione di Proxmox VE via API
"""

import time
import logging
import json
from typing import Optional, List, Dict, Any
from proxmoxer import ProxmoxAPI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProxmoxManager:
    """Gestore centralizzato per le operazioni Proxmox VE."""

    def __init__(
        self,
        host: str,
        user: str,
        token_name: str,
        token_value: str,
        verify_ssl: bool = False,
        port: int = 8006
    ):
        """
        Inizializzare la connessione all'API Proxmox.

        Args:
            host: Hostname o IP del nodo Proxmox
            user: Utente nel formato user@realm
            token_name: Nome del token API
            token_value: Valore segreto del token
            verify_ssl: Verificare il certificato TLS
            port: Porta dell'API (default 8006)
        """
        self.proxmox = ProxmoxAPI(
            host,
            user=user,
            token_name=token_name,
            token_value=token_value,
            verify_ssl=verify_ssl,
            port=port
        )
        self.host = host
        logger.info(f"Connessione stabilita a {host}:{port}")

    # =========================================================================
    # Informazioni Cluster e Nodi
    # =========================================================================

    def get_cluster_status(self) -> List[Dict]:
        """Ottenere lo stato del cluster."""
        return self.proxmox.cluster.status.get()

    def get_nodes(self) -> List[Dict]:
        """Elencare tutti i nodi del cluster."""
        return self.proxmox.nodes.get()

    def get_node_status(self, node: str) -> Dict:
        """Ottenere lo stato dettagliato di un nodo."""
        return self.proxmox.nodes(node).status.get()

    def get_cluster_resources(
        self, resource_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Ottenere le risorse del cluster.

        Args:
            resource_type: Filtro per tipo (vm, storage, node, sdn)
        """
        params = {}
        if resource_type:
            params['type'] = resource_type
        return self.proxmox.cluster.resources.get(**params)

    # =========================================================================
    # Gestione VM
    # =========================================================================

    def list_vms(self, node: str) -> List[Dict]:
        """Elencare tutte le VM su un nodo."""
        return self.proxmox.nodes(node).qemu.get()

    def get_vm_config(self, node: str, vmid: int) -> Dict:
        """Ottenere la configurazione di una VM."""
        return self.proxmox.nodes(node).qemu(vmid).config.get()

    def get_vm_status(self, node: str, vmid: int) -> Dict:
        """Ottenere lo stato corrente di una VM."""
        return self.proxmox.nodes(node).qemu(vmid).status.current.get()

    def create_vm(
        self,
        node: str,
        vmid: int,
        name: str,
        cores: int = 2,
        memory: int = 2048,
        storage: str = "local-zfs",
        disk_size: str = "32G",
        net_bridge: str = "vmbr0",
        os_type: str = "l26",
        **kwargs
    ) -> str:
        """
        Creare una nuova VM.

        Args:
            node: Nodo di destinazione
            vmid: ID della VM
            name: Nome della VM
            cores: Numero di core CPU
            memory: Memoria RAM in MB
            storage: Storage per il disco
            disk_size: Dimensione del disco
            net_bridge: Bridge di rete
            os_type: Tipo di sistema operativo
            **kwargs: Parametri aggiuntivi

        Returns:
            UPID del task di creazione
        """
        params = {
            'vmid': vmid,
            'name': name,
            'cores': cores,
            'memory': memory,
            'scsi0': f"{storage}:{disk_size}",
            'scsihw': 'virtio-scsi-single',
            'net0': f"virtio,bridge={net_bridge}",
            'ostype': os_type,
            'agent': 'enabled=1',
            'boot': 'order=scsi0;net0',
            **kwargs
        }

        upid = self.proxmox.nodes(node).qemu.post(**params)
        logger.info(f"Creazione VM {name} (VMID: {vmid}) avviata: {upid}")
        return upid

    def clone_vm(
        self,
        node: str,
        vmid: int,
        new_vmid: int,
        name: str,
        full: bool = True,
        target_storage: Optional[str] = None,
        target_node: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Clonare una VM esistente.

        Args:
            node: Nodo dove risiede la VM sorgente
            vmid: VMID della VM sorgente
            new_vmid: VMID della nuova VM
            name: Nome della nuova VM
            full: Clone completo (True) o linked clone (False)
            target_storage: Storage di destinazione
            target_node: Nodo di destinazione (per clone cross-node)
            description: Descrizione della nuova VM

        Returns:
            UPID del task di clonazione
        """
        params = {
            'newid': new_vmid,
            'name': name,
            'full': 1 if full else 0,
        }

        if target_storage:
            params['storage'] = target_storage
        if target_node:
            params['target'] = target_node
        if description:
            params['description'] = description

        upid = self.proxmox.nodes(node).qemu(vmid).clone.post(**params)
        logger.info(f"Clonazione VM {vmid} -> {new_vmid} ({name}) avviata: {upid}")
        return upid

    def update_vm_config(self, node: str, vmid: int, **config) -> None:
        """Aggiornare la configurazione di una VM."""
        self.proxmox.nodes(node).qemu(vmid).config.put(**config)
        logger.info(f"Configurazione VM {vmid} aggiornata: {config}")

    def start_vm(self, node: str, vmid: int) -> str:
        """Avviare una VM."""
        upid = self.proxmox.nodes(node).qemu(vmid).status.start.post()
        logger.info(f"Avvio VM {vmid}: {upid}")
        return upid

    def stop_vm(self, node: str, vmid: int) -> str:
        """Fermare forzatamente una VM."""
        upid = self.proxmox.nodes(node).qemu(vmid).status.stop.post()
        logger.info(f"Stop forzato VM {vmid}: {upid}")
        return upid

    def shutdown_vm(self, node: str, vmid: int, timeout: int = 120) -> str:
        """Spegnimento ordinato di una VM (ACPI shutdown)."""
        upid = self.proxmox.nodes(node).qemu(vmid).status.shutdown.post(
            timeout=timeout
        )
        logger.info(f"Shutdown VM {vmid}: {upid}")
        return upid

    def reboot_vm(self, node: str, vmid: int) -> str:
        """Riavviare una VM."""
        upid = self.proxmox.nodes(node).qemu(vmid).status.reboot.post()
        logger.info(f"Reboot VM {vmid}: {upid}")
        return upid

    def delete_vm(self, node: str, vmid: int, purge: bool = True) -> str:
        """
        Eliminare una VM.

        Args:
            node: Nodo dove risiede la VM
            vmid: VMID della VM
            purge: Rimuovere anche dalla configurazione del firewall e HA

        Returns:
            UPID del task di eliminazione
        """
        params = {}
        if purge:
            params['purge'] = 1
            params['destroy-unreferenced-disks'] = 1

        upid = self.proxmox.nodes(node).qemu(vmid).delete(**params)
        logger.info(f"Eliminazione VM {vmid}: {upid}")
        return upid

    def migrate_vm(
        self,
        node: str,
        vmid: int,
        target_node: str,
        online: bool = True,
        with_local_disks: bool = False,
        target_storage: Optional[str] = None
    ) -> str:
        """
        Migrare una VM verso un altro nodo.

        Args:
            node: Nodo sorgente
            vmid: VMID della VM
            target_node: Nodo di destinazione
            online: Migrazione live (True) o offline (False)
            with_local_disks: Migrare anche i dischi locali
            target_storage: Storage di destinazione per i dischi locali

        Returns:
            UPID del task di migrazione
        """
        params = {
            'target': target_node,
            'online': 1 if online else 0,
        }

        if with_local_disks:
            params['with-local-disks'] = 1
        if target_storage:
            params['targetstorage'] = target_storage

        upid = self.proxmox.nodes(node).qemu(vmid).migrate.post(**params)
        logger.info(
            f"Migrazione VM {vmid} da {node} a {target_node}: {upid}"
        )
        return upid

    # =========================================================================
    # Snapshot
    # =========================================================================

    def create_snapshot(
        self,
        node: str,
        vmid: int,
        snap_name: str,
        description: str = "",
        include_ram: bool = False
    ) -> str:
        """Creare uno snapshot di una VM."""
        params = {
            'snapname': snap_name,
            'description': description,
            'vmstate': 1 if include_ram else 0,
        }

        upid = self.proxmox.nodes(node).qemu(vmid).snapshot.post(**params)
        logger.info(f"Snapshot '{snap_name}' per VM {vmid}: {upid}")
        return upid

    def list_snapshots(self, node: str, vmid: int) -> List[Dict]:
        """Elencare gli snapshot di una VM."""
        return self.proxmox.nodes(node).qemu(vmid).snapshot.get()

    def rollback_snapshot(
        self, node: str, vmid: int, snap_name: str
    ) -> str:
        """Ripristinare uno snapshot."""
        upid = self.proxmox.nodes(node).qemu(vmid).snapshot(
            snap_name
        ).rollback.post()
        logger.info(f"Rollback a '{snap_name}' per VM {vmid}: {upid}")
        return upid

    def delete_snapshot(
        self, node: str, vmid: int, snap_name: str
    ) -> str:
        """Eliminare uno snapshot."""
        upid = self.proxmox.nodes(node).qemu(vmid).snapshot(
            snap_name
        ).delete()
        logger.info(f"Eliminazione snapshot '{snap_name}' per VM {vmid}: {upid}")
        return upid

    # =========================================================================
    # Backup
    # =========================================================================

    def backup_vm(
        self,
        node: str,
        vmid: int,
        storage: str = "local",
        mode: str = "snapshot",
        compress: str = "zstd",
        notes: str = ""
    ) -> str:
        """
        Eseguire il backup di una VM.

        Args:
            node: Nodo dove risiede la VM
            vmid: VMID della VM
            storage: Storage per il backup
            mode: Modalità (snapshot, suspend, stop)
            compress: Compressione (zstd, lzo, gzip, none)
            notes: Note per il backup

        Returns:
            UPID del task di backup
        """
        params = {
            'vmid': vmid,
            'storage': storage,
            'mode': mode,
            'compress': compress,
        }
        if notes:
            params['notes-template'] = notes

        upid = self.proxmox.nodes(node).vzdump.post(**params)
        logger.info(f"Backup VM {vmid}: {upid}")
        return upid

    # =========================================================================
    # Task Management
    # =========================================================================

    def get_task_status(self, node: str, upid: str) -> Dict:
        """Ottenere lo stato di un task."""
        return self.proxmox.nodes(node).tasks(upid).status.get()

    def wait_for_task(
        self,
        node: str,
        upid: str,
        timeout: int = 600,
        poll_interval: int = 5
    ) -> Dict:
        """
        Attendere il completamento di un task.

        Args:
            node: Nodo dove è in esecuzione il task
            upid: UPID del task
            timeout: Timeout massimo in secondi
            poll_interval: Intervallo di polling in secondi

        Returns:
            Stato finale del task

        Raises:
            TimeoutError: Se il task non termina entro il timeout
            RuntimeError: Se il task termina con errore
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Task {upid} non completato entro {timeout}s"
                )

            status = self.get_task_status(node, upid)

            if status['status'] == 'stopped':
                if status.get('exitstatus') == 'OK':
                    logger.info(
                        f"Task completato con successo in {elapsed:.1f}s"
                    )
                    return status
                else:
                    raise RuntimeError(
                        f"Task fallito: {status.get('exitstatus', 'unknown')}"
                    )

            logger.debug(
                f"Task in esecuzione... ({elapsed:.0f}s/{timeout}s)"
            )
            time.sleep(poll_interval)

    def get_next_vmid(self) -> int:
        """Ottenere il prossimo VMID disponibile."""
        return int(self.proxmox.cluster.nextid.get())

    # =========================================================================
    # Cloud-init
    # =========================================================================

    def configure_cloudinit(
        self,
        node: str,
        vmid: int,
        ciuser: str = "sysadmin",
        cipassword: Optional[str] = None,
        sshkeys: Optional[str] = None,
        ipconfig0: Optional[str] = None,
        nameserver: Optional[str] = None,
        searchdomain: Optional[str] = None
    ) -> None:
        """Configurare cloud-init per una VM."""
        config = {}

        if ciuser:
            config['ciuser'] = ciuser
        if cipassword:
            config['cipassword'] = cipassword
        if sshkeys:
            config['sshkeys'] = sshkeys
        if ipconfig0:
            config['ipconfig0'] = ipconfig0
        if nameserver:
            config['nameserver'] = nameserver
        if searchdomain:
            config['searchdomain'] = searchdomain

        self.update_vm_config(node, vmid, **config)
        logger.info(f"Cloud-init configurato per VM {vmid}")
```

### Esempio di Utilizzo della Classe

```python
#!/usr/bin/env python3
"""
esempio_utilizzo.py - Esempio di utilizzo del ProxmoxManager
"""

import os
import sys
from proxmox_manager import ProxmoxManager

def main():
    # Inizializzazione
    pm = ProxmoxManager(
        host=os.getenv("PROXMOX_HOST", "pve01.example.local"),
        user="automation@pve",
        token_name="automation-token",
        token_value=os.getenv("PROXMOX_TOKEN_SECRET"),
        verify_ssl=False
    )

    # Elencare tutti i nodi
    print("=== Nodi del Cluster ===")
    for node in pm.get_nodes():
        print(f"  {node['node']}: {node['status']} "
              f"(CPU: {node.get('cpu', 0)*100:.1f}%, "
              f"RAM: {node.get('mem', 0)/node.get('maxmem', 1)*100:.1f}%)")

    # Elencare tutte le VM del cluster
    print("\n=== VM del Cluster ===")
    resources = pm.get_cluster_resources(resource_type='vm')
    for vm in sorted(resources, key=lambda x: x.get('vmid', 0)):
        print(f"  VMID: {vm['vmid']:>6} | "
              f"Nome: {vm.get('name', 'N/A'):<25} | "
              f"Stato: {vm['status']:<10} | "
              f"Nodo: {vm['node']}")

    # Clonare una VM da template
    print("\n=== Clonazione VM ===")
    new_vmid = pm.get_next_vmid()

    upid = pm.clone_vm(
        node="pve01",
        vmid=9000,            # Template Ubuntu
        new_vmid=new_vmid,
        name="test-api-vm",
        full=True,
        target_storage="local-zfs"
    )

    # Attendere il completamento della clonazione
    pm.wait_for_task("pve01", upid, timeout=300)

    # Configurare cloud-init
    pm.configure_cloudinit(
        node="pve01",
        vmid=new_vmid,
        ciuser="sysadmin",
        cipassword="TempPassword123!",
        ipconfig0="ip=10.0.1.100/24,gw=10.0.1.1",
        nameserver="10.0.1.10 10.0.1.11",
        searchdomain="example.local"
    )

    # Ridimensionare il disco
    pm.update_vm_config("pve01", new_vmid, cores=4, memory=8192)

    # Avviare la VM
    upid = pm.start_vm("pve01", new_vmid)
    pm.wait_for_task("pve01", upid, timeout=120)

    print(f"\nVM {new_vmid} creata e avviata con successo!")


if __name__ == "__main__":
    main()
```

---

## Automazione con Bash e cURL

### Script Helper per le Chiamate API

```bash
#!/bin/bash
# proxmox-api-helper.sh - Funzioni helper per l'API Proxmox

# Configurazione
PROXMOX_HOST="${PROXMOX_HOST:-pve01.example.local}"
PROXMOX_PORT="${PROXMOX_PORT:-8006}"
PROXMOX_TOKEN_ID="${PROXMOX_TOKEN_ID:-automation@pve!automation-token}"
PROXMOX_TOKEN_SECRET="${PROXMOX_TOKEN_SECRET}"
BASE_URL="https://${PROXMOX_HOST}:${PROXMOX_PORT}/api2/json"
AUTH_HEADER="Authorization: PVEAPIToken=${PROXMOX_TOKEN_ID}=${PROXMOX_TOKEN_SECRET}"

# Funzione per chiamate GET
api_get() {
    local endpoint="$1"
    curl -s -k \
        -H "$AUTH_HEADER" \
        "${BASE_URL}${endpoint}"
}

# Funzione per chiamate POST
api_post() {
    local endpoint="$1"
    shift
    curl -s -k \
        -H "$AUTH_HEADER" \
        -X POST \
        "$@" \
        "${BASE_URL}${endpoint}"
}

# Funzione per chiamate PUT
api_put() {
    local endpoint="$1"
    shift
    curl -s -k \
        -H "$AUTH_HEADER" \
        -X PUT \
        "$@" \
        "${BASE_URL}${endpoint}"
}

# Funzione per chiamate DELETE
api_delete() {
    local endpoint="$1"
    curl -s -k \
        -H "$AUTH_HEADER" \
        -X DELETE \
        "${BASE_URL}${endpoint}"
}

# Attendere il completamento di un task
wait_for_task() {
    local node="$1"
    local upid="$2"
    local timeout="${3:-300}"
    local interval="${4:-5}"
    local elapsed=0

    echo "Attendere il completamento del task..."
    while [ $elapsed -lt $timeout ]; do
        local status
        status=$(api_get "/nodes/${node}/tasks/${upid}/status" | jq -r '.data.status')

        if [ "$status" = "stopped" ]; then
            local exit_status
            exit_status=$(api_get "/nodes/${node}/tasks/${upid}/status" | jq -r '.data.exitstatus')

            if [ "$exit_status" = "OK" ]; then
                echo "Task completato con successo (${elapsed}s)"
                return 0
            else
                echo "ERRORE: Task fallito con stato: $exit_status"
                return 1
            fi
        fi

        sleep "$interval"
        elapsed=$((elapsed + interval))
        echo "  ... in attesa (${elapsed}s/${timeout}s)"
    done

    echo "ERRORE: Timeout raggiunto (${timeout}s)"
    return 1
}

# Ottenere il prossimo VMID disponibile
get_next_vmid() {
    api_get "/cluster/nextid" | jq -r '.data'
}
```

### Script per Operazioni Comuni

```bash
#!/bin/bash
# proxmox-operations.sh - Operazioni comuni sulle VM
source "$(dirname "$0")/proxmox-api-helper.sh"

# Elencare tutte le VM del cluster
list_all_vms() {
    echo "=== VM nel Cluster ==="
    api_get "/cluster/resources?type=vm" | \
        jq -r '.data | sort_by(.vmid) | .[] |
        "VMID: \(.vmid)\tNome: \(.name // "N/A")\tStato: \(.status)\tNodo: \(.node)\tCPU: \(.maxcpu)\tRAM: \(.maxmem / 1073741824 | floor)GB"' | \
        column -t -s $'\t'
}

# Creare una VM da template con cloud-init
create_vm_from_template() {
    local template_vmid="$1"
    local vm_name="$2"
    local node="${3:-pve01}"
    local ip_address="$4"
    local gateway="$5"

    local new_vmid
    new_vmid=$(get_next_vmid)

    echo "Clonazione template $template_vmid -> VM $new_vmid ($vm_name)..."

    # Clonare
    local upid
    upid=$(api_post "/nodes/${node}/qemu/${template_vmid}/clone" \
        -d "newid=${new_vmid}" \
        -d "name=${vm_name}" \
        -d "full=1" \
        -d "storage=local-zfs" | jq -r '.data')

    wait_for_task "$node" "$upid" 300 || return 1

    # Configurare cloud-init
    echo "Configurazione cloud-init..."
    api_put "/nodes/${node}/qemu/${new_vmid}/config" \
        -d "cores=2" \
        -d "memory=2048" \
        -d "ciuser=sysadmin" \
        -d "sshkeys=$(cat ~/.ssh/id_ed25519.pub | python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.stdin.read().strip()))')" \
        -d "ipconfig0=ip=${ip_address},gw=${gateway}" \
        -d "nameserver=10.0.1.10 10.0.1.11" \
        -d "searchdomain=example.local" > /dev/null

    # Avviare la VM
    echo "Avvio VM $new_vmid..."
    upid=$(api_post "/nodes/${node}/qemu/${new_vmid}/status/start" | jq -r '.data')
    wait_for_task "$node" "$upid" 120 || return 1

    echo "VM $vm_name (VMID: $new_vmid) creata e avviata con successo!"
    echo "IP: ${ip_address%%/*}"
}

# Creare snapshot di una VM
create_snapshot() {
    local node="$1"
    local vmid="$2"
    local snap_name="${3:-snapshot-$(date +%Y%m%d-%H%M%S)}"
    local description="${4:-Snapshot automatico}"

    echo "Creazione snapshot '$snap_name' per VM $vmid..."

    local upid
    upid=$(api_post "/nodes/${node}/qemu/${vmid}/snapshot" \
        -d "snapname=${snap_name}" \
        -d "description=${description}" \
        -d "vmstate=0" | jq -r '.data')

    wait_for_task "$node" "$upid" 300
}

# Migrare una VM
migrate_vm() {
    local source_node="$1"
    local vmid="$2"
    local target_node="$3"
    local online="${4:-1}"

    echo "Migrazione VM $vmid da $source_node a $target_node..."

    local upid
    upid=$(api_post "/nodes/${source_node}/qemu/${vmid}/migrate" \
        -d "target=${target_node}" \
        -d "online=${online}" | jq -r '.data')

    wait_for_task "$source_node" "$upid" 600 10
}

# Backup di una VM
backup_vm() {
    local node="$1"
    local vmid="$2"
    local storage="${3:-pbs}"
    local mode="${4:-snapshot}"

    echo "Backup VM $vmid su storage $storage (modalità: $mode)..."

    local upid
    upid=$(api_post "/nodes/${node}/vzdump" \
        -d "vmid=${vmid}" \
        -d "storage=${storage}" \
        -d "mode=${mode}" \
        -d "compress=zstd" \
        -d "notes-template=Backup automatico - {{guestname}}" | jq -r '.data')

    wait_for_task "$node" "$upid" 3600 30
}

# Menu principale
case "${1}" in
    list)
        list_all_vms
        ;;
    create)
        create_vm_from_template "$2" "$3" "$4" "$5" "$6"
        ;;
    snapshot)
        create_snapshot "$2" "$3" "$4" "$5"
        ;;
    migrate)
        migrate_vm "$2" "$3" "$4" "$5"
        ;;
    backup)
        backup_vm "$2" "$3" "$4" "$5"
        ;;
    *)
        echo "Uso: $0 {list|create|snapshot|migrate|backup} [args...]"
        echo ""
        echo "Comandi:"
        echo "  list                                      - Elencare tutte le VM"
        echo "  create <template_id> <name> <node> <ip/cidr> <gw>  - Creare VM"
        echo "  snapshot <node> <vmid> [name] [desc]      - Creare snapshot"
        echo "  migrate <src_node> <vmid> <dst_node> [online]  - Migrare VM"
        echo "  backup <node> <vmid> [storage] [mode]     - Backup VM"
        ;;
esac
```

---

## Script di Automazione per la Migrazione

```python
#!/usr/bin/env python3
"""
migration_automation.py - Script di automazione per la migrazione batch
da VMware a Proxmox VE

Legge un file CSV con la lista delle VM da migrare e per ciascuna:
1. Verifica i prerequisiti
2. Crea la VM su Proxmox dal template appropriato
3. Configura le risorse (CPU, RAM, disco)
4. Configura cloud-init (rete, utente, SSH)
5. Avvia la VM
6. Verifica la raggiungibilità
"""

import csv
import json
import logging
import os
import socket
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional
from proxmox_manager import ProxmoxManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class VMSpec:
    """Specifica di una VM da creare/migrare."""
    name: str
    source_name: str
    target_node: str
    template_vmid: int
    cores: int
    memory: int          # in MB
    disk_size: int       # in GB
    ip_address: str      # con CIDR, es. 10.0.1.100/24
    gateway: str
    vlan: Optional[int] = None
    storage: str = "local-zfs"
    additional_disks: List[int] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    os_type: str = "l26"
    notes: str = ""


def load_vm_specs(csv_path: str) -> List[VMSpec]:
    """Caricare le specifiche VM da un file CSV."""
    specs = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            additional_disks = []
            if row.get('additional_disks'):
                additional_disks = [
                    int(d.strip())
                    for d in row['additional_disks'].split(';')
                    if d.strip()
                ]

            tags = []
            if row.get('tags'):
                tags = [t.strip() for t in row['tags'].split(';')]

            spec = VMSpec(
                name=row['name'],
                source_name=row.get('source_name', row['name']),
                target_node=row['target_node'],
                template_vmid=int(row['template_vmid']),
                cores=int(row['cores']),
                memory=int(row['memory']),
                disk_size=int(row['disk_size']),
                ip_address=row['ip_address'],
                gateway=row['gateway'],
                vlan=int(row['vlan']) if row.get('vlan') else None,
                storage=row.get('storage', 'local-zfs'),
                additional_disks=additional_disks,
                tags=tags,
                os_type=row.get('os_type', 'l26'),
                notes=row.get('notes', '')
            )
            specs.append(spec)
    return specs


def check_ip_available(ip: str, timeout: float = 1.0) -> bool:
    """Verificare che un IP non sia già in uso."""
    ip_clean = ip.split('/')[0]
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((ip_clean, 22))
        sock.close()
        return result != 0  # True se la porta NON è raggiungibile
    except (socket.timeout, OSError):
        return True  # Non raggiungibile = disponibile


def wait_for_ssh(ip: str, timeout: int = 300, interval: int = 10) -> bool:
    """Attendere che SSH sia raggiungibile su un IP."""
    ip_clean = ip.split('/')[0]
    start = time.time()

    while time.time() - start < timeout:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex((ip_clean, 22))
            sock.close()
            if result == 0:
                logger.info(f"SSH raggiungibile su {ip_clean}")
                return True
        except (socket.timeout, OSError):
            pass
        time.sleep(interval)

    return False


def migrate_vm(pm: ProxmoxManager, spec: VMSpec, dry_run: bool = False) -> dict:
    """
    Eseguire la migrazione di una singola VM.

    Returns:
        Dizionario con il risultato della migrazione
    """
    result = {
        'name': spec.name,
        'status': 'pending',
        'vmid': None,
        'errors': [],
        'warnings': [],
    }

    try:
        # Fase 1: Verifiche preliminari
        logger.info(f"[{spec.name}] Avvio migrazione...")

        # Verificare disponibilità IP
        if not check_ip_available(spec.ip_address):
            result['warnings'].append(
                f"IP {spec.ip_address} potrebbe essere già in uso"
            )
            logger.warning(f"[{spec.name}] IP {spec.ip_address} potrebbe essere in uso")

        # Verificare che il nodo target sia disponibile
        node_status = pm.get_node_status(spec.target_node)
        if node_status.get('status') != 'running' if 'status' in node_status else False:
            raise RuntimeError(
                f"Nodo {spec.target_node} non disponibile"
            )

        if dry_run:
            result['status'] = 'dry_run'
            logger.info(f"[{spec.name}] DRY RUN - nessuna azione eseguita")
            return result

        # Fase 2: Ottenere VMID
        new_vmid = pm.get_next_vmid()
        result['vmid'] = new_vmid
        logger.info(f"[{spec.name}] VMID assegnato: {new_vmid}")

        # Fase 3: Clonare dal template
        logger.info(f"[{spec.name}] Clonazione dal template {spec.template_vmid}...")
        upid = pm.clone_vm(
            node=spec.target_node,
            vmid=spec.template_vmid,
            new_vmid=new_vmid,
            name=spec.name,
            full=True,
            target_storage=spec.storage,
            description=f"Migrato da VMware: {spec.source_name}\n{spec.notes}"
        )
        pm.wait_for_task(spec.target_node, upid, timeout=600)

        # Fase 4: Configurare risorse
        logger.info(f"[{spec.name}] Configurazione risorse...")

        net_config = f"virtio,bridge=vmbr0"
        if spec.vlan:
            net_config += f",tag={spec.vlan}"

        config_params = {
            'cores': spec.cores,
            'memory': spec.memory,
            'balloon': spec.memory,
            'net0': net_config,
            'agent': 'enabled=1,fstrim_cloned_disks=1',
            'onboot': 1,
        }

        if spec.tags:
            config_params['tags'] = ';'.join(spec.tags)

        pm.update_vm_config(spec.target_node, new_vmid, **config_params)

        # Fase 5: Configurare cloud-init
        logger.info(f"[{spec.name}] Configurazione cloud-init...")
        pm.configure_cloudinit(
            node=spec.target_node,
            vmid=new_vmid,
            ciuser="sysadmin",
            ipconfig0=f"ip={spec.ip_address},gw={spec.gateway}",
            nameserver="10.0.1.10 10.0.1.11",
            searchdomain="example.local"
        )

        # Fase 6: Avviare la VM
        logger.info(f"[{spec.name}] Avvio VM...")
        upid = pm.start_vm(spec.target_node, new_vmid)
        pm.wait_for_task(spec.target_node, upid, timeout=120)

        # Fase 7: Verificare raggiungibilità SSH
        logger.info(f"[{spec.name}] Attesa raggiungibilità SSH...")
        if wait_for_ssh(spec.ip_address, timeout=300):
            result['status'] = 'success'
            logger.info(f"[{spec.name}] Migrazione completata con successo!")
        else:
            result['status'] = 'warning'
            result['warnings'].append("SSH non raggiungibile entro il timeout")
            logger.warning(f"[{spec.name}] VM avviata ma SSH non raggiungibile")

    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(str(e))
        logger.error(f"[{spec.name}] Errore durante la migrazione: {e}")

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Automazione migrazione VM da VMware a Proxmox'
    )
    parser.add_argument(
        'csv_file', help='File CSV con le specifiche delle VM'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Eseguire solo le verifiche senza creare VM'
    )
    parser.add_argument(
        '--parallel', type=int, default=1,
        help='Numero di migrazioni parallele (default: 1)'
    )
    args = parser.parse_args()

    # Inizializzare ProxmoxManager
    pm = ProxmoxManager(
        host=os.getenv("PROXMOX_HOST", "pve01.example.local"),
        user="automation@pve",
        token_name="automation-token",
        token_value=os.getenv("PROXMOX_TOKEN_SECRET"),
        verify_ssl=False
    )

    # Caricare le specifiche
    specs = load_vm_specs(args.csv_file)
    logger.info(f"Caricate {len(specs)} VM da migrare")

    # Eseguire le migrazioni
    results = []
    for spec in specs:
        result = migrate_vm(pm, spec, dry_run=args.dry_run)
        results.append(result)

    # Report finale
    print("\n" + "=" * 70)
    print("REPORT MIGRAZIONE")
    print("=" * 70)

    success_count = sum(1 for r in results if r['status'] == 'success')
    warning_count = sum(1 for r in results if r['status'] == 'warning')
    error_count = sum(1 for r in results if r['status'] == 'error')

    for r in results:
        status_icon = {
            'success': '[OK]',
            'warning': '[WARN]',
            'error': '[FAIL]',
            'dry_run': '[DRY]',
            'pending': '[SKIP]',
        }.get(r['status'], '[???]')

        print(f"  {status_icon} {r['name']:<30} VMID: {r.get('vmid', 'N/A')}")
        for err in r.get('errors', []):
            print(f"         ERRORE: {err}")
        for warn in r.get('warnings', []):
            print(f"         AVVISO: {warn}")

    print(f"\nTotale: {len(results)} | "
          f"Successo: {success_count} | "
          f"Avvisi: {warning_count} | "
          f"Errori: {error_count}")

    # Salvare il report in JSON
    report_path = f"migration_report_{int(time.time())}.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Report salvato in {report_path}")

    # Exit code basato sui risultati
    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
```

### File CSV di Esempio

```csv
name,source_name,target_node,template_vmid,cores,memory,disk_size,ip_address,gateway,vlan,storage,additional_disks,tags,os_type,notes
prod-web01,vmw-web01,pve01,9000,4,8192,50,10.0.100.10/24,10.0.100.1,100,local-zfs,,production;webserver;linux,l26,Web server principale
prod-web02,vmw-web02,pve02,9000,4,8192,50,10.0.100.11/24,10.0.100.1,100,local-zfs,,production;webserver;linux,l26,Web server secondario
prod-db01,vmw-db01,pve01,9000,8,32768,100,10.0.200.10/24,10.0.200.1,200,local-zfs,500;100,production;database;linux,l26,Database primario PostgreSQL
prod-app01,vmw-app01,pve03,9000,4,16384,80,10.0.150.10/24,10.0.150.1,150,local-zfs,,production;appserver;linux,l26,Application server Java
```

---

## Webhook e Integrazioni

### Webhook con Flask per Trigger Automatici

```python
#!/usr/bin/env python3
"""
webhook_server.py - Server webhook per trigger automatici di operazioni Proxmox
"""

from flask import Flask, request, jsonify
import hmac
import hashlib
import threading
from proxmox_manager import ProxmoxManager

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your-secret-key")

pm = ProxmoxManager(
    host=os.getenv("PROXMOX_HOST"),
    user="automation@pve",
    token_name="automation-token",
    token_value=os.getenv("PROXMOX_TOKEN_SECRET"),
)


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verificare la firma HMAC del webhook."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@app.route('/webhook/create-vm', methods=['POST'])
def create_vm_webhook():
    """Endpoint per la creazione di VM via webhook."""
    # Verificare la firma
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not verify_signature(request.data, signature):
        return jsonify({'error': 'Firma non valida'}), 401

    data = request.json

    # Validare i campi obbligatori
    required = ['name', 'node', 'template_vmid', 'ip_address', 'gateway']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Campi mancanti: {missing}'}), 400

    # Eseguire la creazione in background
    def create_async():
        try:
            new_vmid = pm.get_next_vmid()
            upid = pm.clone_vm(
                node=data['node'],
                vmid=data['template_vmid'],
                new_vmid=new_vmid,
                name=data['name'],
                full=True
            )
            pm.wait_for_task(data['node'], upid)
            pm.configure_cloudinit(
                node=data['node'],
                vmid=new_vmid,
                ipconfig0=f"ip={data['ip_address']},gw={data['gateway']}",
            )
            pm.start_vm(data['node'], new_vmid)
        except Exception as e:
            app.logger.error(f"Errore creazione VM: {e}")

    thread = threading.Thread(target=create_async)
    thread.start()

    return jsonify({
        'status': 'accepted',
        'message': f"Creazione VM '{data['name']}' avviata"
    }), 202


@app.route('/webhook/snapshot', methods=['POST'])
def snapshot_webhook():
    """Endpoint per la creazione di snapshot via webhook."""
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not verify_signature(request.data, signature):
        return jsonify({'error': 'Firma non valida'}), 401

    data = request.json
    node = data.get('node', 'pve01')
    vmid = data.get('vmid')
    snap_name = data.get('snap_name', f"webhook-{int(time.time())}")

    if not vmid:
        return jsonify({'error': 'vmid obbligatorio'}), 400

    try:
        upid = pm.create_snapshot(node, vmid, snap_name)
        return jsonify({'status': 'started', 'upid': upid}), 202
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

---

## Gestione degli Errori e Rate Limiting

```python
import time
from functools import wraps

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator per retry con exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise
                    logger.warning(
                        f"Tentativo {attempt + 1}/{max_retries} fallito: {e}. "
                        f"Nuovo tentativo tra {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator


class RateLimiter:
    """Rate limiter semplice per le chiamate API."""

    def __init__(self, calls_per_second: float = 5.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait(self):
        """Attendere se necessario per rispettare il rate limit."""
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()


# Esempio di utilizzo
rate_limiter = RateLimiter(calls_per_second=5)

@retry_with_backoff(max_retries=3, initial_delay=2.0)
def safe_api_call(pm, node, vmid):
    """Chiamata API con retry e rate limiting."""
    rate_limiter.wait()
    return pm.get_vm_status(node, vmid)
```

---

## Conclusione

L'API REST di Proxmox VE offre un'interfaccia completa e ben documentata per l'automazione di ogni aspetto dell'infrastruttura virtuale. Utilizzando Python con la libreria `proxmoxer` o Bash con `curl`, è possibile costruire script di automazione potenti per la migrazione batch, il provisioning automatizzato e l'integrazione con sistemi esterni tramite webhook. La gestione corretta degli errori, il rate limiting e il monitoraggio dei task sono elementi essenziali per costruire automazioni robuste e affidabili in ambienti di produzione.

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — Token API con privilege separation.** Best practice per token API: (1) creare un user dedicato `automation@pve` (NON usare `root@pam`); (2) creare un ruolo custom con permessi minimi richiesti dallo script (es. `VM.Allocate`, `VM.Migrate`, `Datastore.AllocateSpace`); (3) `pveum aclmod / -user automation@pve -role <CustomRole>`; (4) `pveum user token add automation@pve script1 --privsep 1`; (5) salvare il token in vault (HashiCorp, AWS Secrets Manager); (6) script reads token via env var `PROXMOX_TOKEN`. Privsep=1 forza uso esplicito dell'ACL del token (vs ereditare quella dell'utente), riducendo blast radius in caso di token compromise. Fonte: [Proxmox VE — User Management Tokens](https://pve.proxmox.com/pve-docs/chapter-pveum.html#pveum_tokens), retrieved 2026-04-27.

> **Errore comune — Script che assume completion immediato dei task async.** Sintomo: script crea VM con `qm create` poi tenta `qm start` immediatamente, ottiene errore "VM is locked (creating disk)". Causa: `qm create` ritorna UPID immediatamente ma il task continua in background; tentare uso prima della completion fallisce. Soluzione: dopo ogni POST che ritorna UPID, polling `GET /nodes/<node>/tasks/<UPID>/status` finche `status=stopped` AND `exitstatus=OK`; timeout 5-30 min; gestire `exitstatus != OK` come errore. Implementazione corretta in proxmoxer: `task = node.qemu.create(...)` poi `wait_for_task(task)`. Fonte: [proxmoxer — async task handling](https://proxmoxer.github.io/docs/2.0/), retrieved 2026-04-27.

---

## Esercizi

1. **Lab — script Python provisioning.** Scrivere uno script `proxmoxer` che: legge un YAML con N VM da creare (specifiche RAM/CPU/disk/IP), per ognuna: clona un template, customizza cloud-init, avvia, attende guest-agent ready, valida ping. Gestione errori: rollback (delete VM creata) se step fallisce.

2. **Stretch — Ansible playbook end-to-end.** Playbook che: (1) crea 3 VM su Proxmox via `community.general.proxmox_kvm`; (2) attende che siano up; (3) esegue role di hardening (CIS); (4) installa applicazione (es. nginx); (5) configura monitoring agent; (6) report completion.

3. **Stretch — Terraform IaC.** Modulo Terraform per deploy completo: VLAN, storage pool, 5 VM web + 2 DB + 1 LB; output IP delle VM. Gestire state remoto su S3 / GCS.

## Auto-valutazione

1. Token API vs ticket: differenze e quando usare ognuno.
2. Cosa ritorna un'operazione async Proxmox e come fare polling?
3. `privsep=1` per token: cosa significa praticamente?
4. Rate limit Proxmox API: cosa succede oltre 30 req/s?
5. Idempotency in API scripting: come implementare?
6. Differenza fra Ansible proxmox modules e Terraform Telmate provider.

## Letture primarie consigliate

- Proxmox VE — API Documentation. https://pve.proxmox.com/pve-docs/api-viewer/ (retrieved 2026-04-27).
- Proxmox VE — User Management. https://pve.proxmox.com/pve-docs/chapter-pveum.html (retrieved 2026-04-27).
- proxmoxer — Python client documentation. https://proxmoxer.github.io/docs/2.0/ (retrieved 2026-04-27).
- Ansible community.general — Proxmox modules. https://docs.ansible.com/ansible/latest/collections/community/general/ (retrieved 2026-04-27).
- Telmate Proxmox Terraform provider. https://registry.terraform.io/providers/Telmate/proxmox/latest/docs (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 14.1 — `cloud-init-template-vm.md`: template lato cui l'API esegue clone.
- Modulo 12.2 — `../12-SICUREZZA-E-COMPLIANCE/autenticazione-ldap-ad-proxmox.md`: user management.
- Modulo 16.x — `../16-PROCEDURE-OPERATIVE-E-RUNBOOK/`: runbook automatizzati via API.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Proxmox API** | REST endpoints `/api2/json/...`. |
| **API Token** | Long-lived secret per auth scripting. |
| **Ticket** | Session-based auth, scade in 2h. |
| **`privsep`** | Privilege separation: token usa ACL proprio invece di quello dell'utente. |
| **UPID** | Unique Process ID; identificatore di un task async. |
| **`proxmoxer`** | Libreria Python client per Proxmox API. |
| **Rate limit** | Limite richieste/secondo (default ~30 req/s). |
| **Idempotency** | Operazione ripetibile con stesso effetto. |
| **Partial-state** | Stato in cui un'operazione e a meta. |
| **Ansible proxmox modules** | `community.general.proxmox*` per provisioning Ansible. |
| **Terraform Telmate provider** | IaC per Proxmox via Terraform. |
