# Gestione Pacchetti Linux — Guida Completa

> **Modulo 03** · **Aggiornamento:** 2026-05-24

## Idee guida
1. **`apt` (Debian/Ubuntu) vs `dnf` (RHEL/Fedora) vs `pacman` (Arch).**
2. **Hold (`apt-mark hold`) per kernel e pacchetti production-critical.**
3. **Snap/Flatpak per app desktop; container per server side.**
4. **GPG keys + repository signing: mai fidarsi di un repository senza verifica crittografica.**
5. **dpkg e RPM sono i fondamenti: capirne gli internals prima di usare i frontend (apt/dnf).**
6. **Nix/Guix: il futuro della riproducibilita dichiarativa.**
7. **Unattended-upgrades: automatizzare la sicurezza, mai la pigrizia.**
8. **Private repos: controllare la supply chain del software nella propria infrastruttura.**


## Indice

- [Panoramica](#panoramica)
- [APT — Deep Dive](#apt--deep-dive)
  - [apt vs apt-get](#apt-vs-apt-get)
  - [apt-cache — Interrogazione della cache](#apt-cache--interrogazione-della-cache)
  - [apt-mark — Gestione stato pacchetti](#apt-mark--gestione-stato-pacchetti)
  - [sources.list — Formato e sintassi](#sourceslist--formato-e-sintassi)
  - [Pinning con apt preferences](#pinning-con-apt-preferences)
  - [Configurazione proxy APT](#configurazione-proxy-apt)
  - [APT 3.0 — Novita e Solver3](#apt-30--novita-e-solver3)
  - [Aggiornamenti graduali (Phased Updates)](#aggiornamenti-graduali-phased-updates)
- [dpkg — Internals](#dpkg--internals)
  - [Formato .deb](#formato-deb)
  - [File di controllo](#file-di-controllo)
  - [Maintainer scripts](#maintainer-scripts)
  - [Query e verifica dpkg](#query-e-verifica-dpkg)
- [DNF/YUM — Deep Dive](#dnfyum--deep-dive)
  - [Configurazione dnf.conf](#configurazione-dnfconf)
  - [Gestione repository DNF](#gestione-repository-dnf)
  - [Moduli e gruppi](#moduli-e-gruppi)
  - [DNF history e rollback](#dnf-history-e-rollback)
  - [DNF5 — Architettura di nuova generazione](#dnf5--architettura-di-nuova-generazione)
- [RPM — Internals](#rpm--internals)
  - [Formato .rpm](#formato-rpm)
  - [Spec files](#spec-files)
  - [Query RPM avanzate](#query-rpm-avanzate)
  - [Verifica RPM](#verifica-rpm)
- [Pacman — Arch Linux](#pacman--arch-linux)
- [Costruzione pacchetti](#costruzione-pacchetti)
  - [Creare pacchetti .deb](#creare-pacchetti-deb)
  - [Creare pacchetti .rpm](#creare-pacchetti-rpm)
- [Snap, Flatpak e AppImage — Confronto approfondito](#snap-flatpak-e-appimage--confronto-approfondito)
  - [Portali XDG e modello di sicurezza Flatpak](#portali-xdg-e-modello-di-sicurezza-flatpak)
  - [Verifica e sicurezza su Flathub](#verifica-e-sicurezza-su-flathub)
- [Nix e Guix — Gestione dichiarativa](#nix-e-guix--gestione-dichiarativa)
  - [Nix su distribuzioni non-NixOS](#nix-su-distribuzioni-non-nixos)
- [Compilazione da Sorgente](#compilazione-da-sorgente)
- [Gestione Repository e GPG](#gestione-repository-e-gpg)
  - [Creare un repository privato APT](#creare-un-repository-privato-apt)
  - [Gestione avanzata con Aptly](#gestione-avanzata-con-aptly)
  - [Creare un repository privato RPM](#creare-un-repository-privato-rpm)
  - [Firma GPG dei pacchetti](#firma-gpg-dei-pacchetti)
- [Risoluzione dipendenze](#risoluzione-dipendenze)
- [Gestione pacchetti kernel](#gestione-pacchetti-kernel)
- [Aggiornamenti automatici (Unattended Upgrades)](#aggiornamenti-automatici-unattended-upgrades)
- [Sicurezza pacchetti](#sicurezza-pacchetti)
  - [Sigstore, SLSA e supply chain moderna](#sigstore-slsa-e-supply-chain-moderna)
- [Gestione pacchetti nei container](#gestione-pacchetti-nei-container)
- [Artefatti OCI per distribuzione non-container](#artefatti-oci-per-distribuzione-non-container)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Matrice decisionale](#matrice-decisionale)

---

## Panoramica

Il package manager e lo strumento fondamentale per installare, aggiornare e rimuovere software in modo sicuro e controllato. Ogni famiglia di distribuzioni ha il proprio: APT per Debian/Ubuntu, DNF per Fedora/RHEL, Pacman per Arch. I formati universali (Snap, Flatpak) sono alternative cross-distribuzione. La padronanza del package manager e essenziale per la gestione dei server e la sicurezza del sistema.

### Architettura a livelli

La gestione pacchetti in Linux segue un modello a due livelli:

```
+-------------------------------+
|   Frontend (alto livello)     |
|   apt / dnf / pacman          |
|   Risoluzione dipendenze      |
|   Repository remoti           |
+-------------------------------+
         |
+-------------------------------+
|   Backend (basso livello)     |
|   dpkg / rpm                  |
|   Installazione file          |
|   Database locale             |
+-------------------------------+
```

- **Backend (dpkg/rpm)**: gestisce l'installazione fisica dei file, il database locale dei pacchetti installati, gli script di manutenzione. Non sa nulla di repository o dipendenze.
- **Frontend (apt/dnf)**: interroga i repository remoti, risolve le dipendenze, scarica i pacchetti e li passa al backend per l'installazione effettiva.

### Ciclo di vita di un pacchetto

```
Sviluppatore → Build (.deb/.rpm) → Repository → Download → Installazione → Aggiornamento → Rimozione
     ↑                                  ↑                         ↑
   Spec/Control                     GPG Sign                  Maintainer
    files                           + Metadata                 Scripts
```

---

## APT — Deep Dive

### Comandi fondamentali

```bash
# AGGIORNAMENTO
sudo apt update                      # Aggiorna lista pacchetti
sudo apt upgrade                     # Aggiorna pacchetti installati
sudo apt full-upgrade                # Upgrade con rimozione pacchetti obsoleti
sudo apt dist-upgrade                # Upgrade della distribuzione

# INSTALLAZIONE E RIMOZIONE
sudo apt install nginx               # Installa
sudo apt install nginx=1.18.0-0ubuntu1  # Versione specifica
sudo apt install -y nginx php-fpm    # Multipli, senza conferma
sudo apt remove nginx                # Rimuove (mantiene configurazione)
sudo apt purge nginx                 # Rimuove + configurazione
sudo apt autoremove                  # Rimuove dipendenze orfane

# RICERCA E INFORMAZIONI
apt search nginx                     # Cerca pacchetti
apt show nginx                       # Dettagli pacchetto
apt list --installed                 # Pacchetti installati
apt list --upgradable                # Pacchetti aggiornabili
dpkg -L nginx                        # File installati da un pacchetto
dpkg -S /usr/sbin/nginx             # Quale pacchetto possiede il file

# DPKG — gestione pacchetti .deb
sudo dpkg -i pacchetto.deb          # Installa .deb locale
sudo dpkg -r pacchetto              # Rimuovi
dpkg -l | grep nginx                # Lista con filtro
sudo apt install -f                  # Fix dipendenze rotte dopo dpkg -i

# PIN E HOLD
sudo apt-mark hold nginx             # Blocca aggiornamento
sudo apt-mark unhold nginx           # Sblocca
apt-mark showhold                    # Lista pacchetti bloccati
```

### Repository APT

```bash
# /etc/apt/sources.list e /etc/apt/sources.list.d/

# Aggiungere repository PPA (Ubuntu)
sudo add-apt-repository ppa:nome/ppa
sudo apt update

# Aggiungere repository custom
echo "deb https://repo.example.com/apt stable main" | \
  sudo tee /etc/apt/sources.list.d/example.list

# Aggiungere chiave GPG
curl -fsSL https://repo.example.com/gpg.key | \
  sudo gpg --dearmor -o /etc/apt/keyrings/example.gpg
```

### apt vs apt-get

`apt` (introdotto in Debian 8 / Ubuntu 16.04) e il frontend moderno pensato per l'uso interattivo. `apt-get` resta il tool da usare negli script per la stabilita dell'output.

| Caratteristica | `apt` | `apt-get` |
|---|---|---|
| Barra di progresso | Si, colorata | No |
| Output stabile per parsing | No (cambia tra versioni) | Si |
| `list` command | `apt list` | Non esiste, usare `dpkg -l` |
| `full-upgrade` | `apt full-upgrade` | `apt-get dist-upgrade` |
| `autoremove` integrato | Suggerisce dopo install | Serve comando separato |
| Uso raccomandato | Terminale interattivo | Script, cron, Ansible |

```bash
# In uno script di automazione, usare SEMPRE apt-get:
apt-get update -qq
apt-get install -y --no-install-recommends nginx

# -qq: output minimale
# --no-install-recommends: installa solo dipendenze obbligatorie,
#   non i pacchetti "raccomandati" (risparmio spazio, specialmente container)
```

Comandi esclusivi di `apt-get`:

```bash
apt-get source nginx               # Scarica sorgenti del pacchetto
apt-get build-dep nginx            # Installa dipendenze di build
apt-get download nginx             # Scarica .deb senza installare
apt-get changelog nginx            # Visualizza il changelog
apt-get check                      # Verifica consistenza dipendenze
```

### apt-cache — Interrogazione della cache

`apt-cache` interroga il database locale dei metadati (dopo `apt update`). Non richiede privilegi root.

```bash
# Cercare pacchetti per nome o descrizione
apt-cache search "web server"

# Dettagli completi di un pacchetto
apt-cache show nginx

# Solo le informazioni del pacchetto (senza descrizione lunga)
apt-cache showpkg nginx

# Albero delle dipendenze
apt-cache depends nginx
# Output:
#   nginx
#     Depends: nginx-core | nginx-full | nginx-extras | nginx-light
#     ...

# Dipendenze inverse: chi dipende da questo pacchetto?
apt-cache rdepends libssl3
# Utile per valutare l'impatto di una rimozione

# Statistiche della cache
apt-cache stats
# Mostra: pacchetti totali, versioni, dipendenze, spazio

# Policy: da quale repository viene un pacchetto?
apt-cache policy nginx
# Output:
#   nginx:
#     Installed: 1.18.0-6ubuntu14.4
#     Candidate: 1.18.0-6ubuntu14.4
#     Version table:
#      *** 1.18.0-6ubuntu14.4 500
#             500 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64

# Pacchetti virtuali: cosa fornisce "httpd"?
apt-cache showvirtualpkg httpd
```

### apt-mark — Gestione stato pacchetti

`apt-mark` controlla lo stato dei pacchetti nel database dpkg. Due dimensioni: **hold/unhold** (blocco aggiornamenti) e **auto/manual** (come e stato installato).

```bash
# HOLD: blocca un pacchetto a una versione specifica
sudo apt-mark hold linux-image-$(uname -r)
sudo apt-mark hold linux-headers-$(uname -r)
# Nessun apt upgrade potra toccare questi pacchetti

# UNHOLD: sblocca
sudo apt-mark unhold nginx

# Lista tutti i pacchetti in hold
apt-mark showhold

# AUTO/MANUAL: gestione dipendenze orfane
# "auto" = installato come dipendenza → rimovibile con autoremove
# "manual" = installato esplicitamente dall'utente → mai rimosso automaticamente

# Mostra pacchetti installati manualmente
apt-mark showmanual

# Mostra pacchetti installati automaticamente
apt-mark showauto

# Cambiare stato: marcare un pacchetto come "auto"
# (verra rimosso da autoremove se nessuno lo richiede piu)
sudo apt-mark auto libsomething-dev

# Marcare come "manual" (protegge da autoremove)
sudo apt-mark manual libcurl4
```

### sources.list — Formato e sintassi

Il file `/etc/apt/sources.list` e la pratica moderna `/etc/apt/sources.list.d/*.list` definiscono dove APT cerca i pacchetti.

#### Formato one-line (classico)

```
deb [opzioni] uri distribuzione componenti
deb-src [opzioni] uri distribuzione componenti
```

Esempio annotato:

```
# Pacchetti binari dalla release "jammy" (Ubuntu 22.04), componenti main e universe
deb http://archive.ubuntu.com/ubuntu jammy main restricted universe multiverse

# Sorgenti (necessari per apt-get source / apt-get build-dep)
deb-src http://archive.ubuntu.com/ubuntu jammy main restricted universe multiverse

# Security updates — repository separato
deb http://security.ubuntu.com/ubuntu jammy-security main restricted

# Backports — versioni piu recenti backportate
deb http://archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse

# Repository terzo con firma GPG (metodo moderno signed-by)
deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu jammy stable
```

#### Formato DEB822 (moderno, `.sources`)

A partire da Debian 12 / Ubuntu 24.04, il formato preferito usa file `.sources`:

```
# /etc/apt/sources.list.d/ubuntu.sources
Types: deb deb-src
URIs: http://archive.ubuntu.com/ubuntu
Suites: noble noble-updates noble-backports
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg

Types: deb deb-src
URIs: http://security.ubuntu.com/ubuntu
Suites: noble-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
```

#### Componenti Debian/Ubuntu

| Componente | Debian | Ubuntu |
|---|---|---|
| `main` | Software libero (DFSG) | Software supportato da Canonical |
| `contrib` | Libero ma dipende da non-libero | — |
| `non-free` | Software proprietario | — |
| `non-free-firmware` | Firmware proprietario (Debian 12+) | — |
| `restricted` | — | Driver proprietari supportati |
| `universe` | — | Community-maintained |
| `multiverse` | — | Software con restrizioni legali |

### Pinning con apt preferences

Il pinning permette di controllare quale versione/repository ha priorita durante l'installazione e l'aggiornamento.

File: `/etc/apt/preferences` o `/etc/apt/preferences.d/*.pref`

#### Priorita APT

| Priorita | Significato |
|---|---|
| < 0 | Mai installare |
| 0 < P < 100 | Installa solo se esplicitamente richiesto |
| 100 | Default per pacchetti gia installati |
| 500 | Default per pacchetti candidati |
| 990 | Quasi sempre preferito |
| 1001+ | Forza downgrade se necessario |

```
# /etc/apt/preferences.d/pin-nginx.pref

# Bloccare nginx alla versione da jammy (non jammy-updates)
Package: nginx
Pin: release a=jammy
Pin-Priority: 900

# Mai installare pacchetti da testing (se il repo e configurato)
Package: *
Pin: release a=testing
Pin-Priority: -1

# Preferire tutto da jammy-security (priorita alta per security patches)
Package: *
Pin: release a=jammy-security
Pin-Priority: 990

# Pinnare un pacchetto specifico da un repository specifico
Package: docker-ce
Pin: origin download.docker.com
Pin-Priority: 900

# Pinnare per versione
Package: postgresql-16
Pin: version 16.2*
Pin-Priority: 1001
```

Verificare il pinning attivo:

```bash
apt-cache policy nginx
# L'output mostra le priorita effettive per ogni versione disponibile
```

### Configurazione proxy APT

Per ambienti aziendali con proxy HTTP.

```bash
# Metodo 1: file di configurazione persistente
# /etc/apt/apt.conf.d/95proxy
Acquire::http::Proxy "http://proxy.azienda.it:8080";
Acquire::https::Proxy "http://proxy.azienda.it:8080";

# Con autenticazione
Acquire::http::Proxy "http://utente:password@proxy.azienda.it:8080";

# Proxy solo per repository specifici
Acquire::http::Proxy::archive.ubuntu.com "http://proxy.azienda.it:8080";
Acquire::http::Proxy::download.docker.com "DIRECT";

# Metodo 2: variabile d'ambiente (temporanea)
sudo http_proxy="http://proxy.azienda.it:8080" apt update

# Metodo 3: configurazione apt per caching locale (apt-cacher-ng)
Acquire::http::Proxy "http://apt-cache-server:3142";
```

Configurazione completa di APT in `/etc/apt/apt.conf.d/`:

```bash
# /etc/apt/apt.conf.d/99custom

# Timeout connessione (default: 120s)
Acquire::http::Timeout "30";
Acquire::https::Timeout "30";

# Numero di retry
Acquire::Retries "3";

# Non installare pacchetti raccomandati per default
APT::Install-Recommends "false";
APT::Install-Suggests "false";

# Dimensione massima cache
APT::Cache-Limit "100000000";
```

### APT 3.0 — Novita e Solver3

APT 3.0 (rilasciato nel 2025 come evoluzione della serie 2.9) e il primo major release dopo APT 2.0 (2020). Diventa il package manager predefinito in Debian 13 "Trixie" e Ubuntu 25.04. Le novita principali riguardano il solver delle dipendenze, l'interfaccia utente e la gestione dei conflitti.

#### Solver3: risoluzione dipendenze con backtracking

Il nuovo Solver3 sostituisce il solver tradizionale con un algoritmo a **backtracking completo**. A differenza del vecchio solver che prendeva decisioni irreversibili e poteva fallire in situazioni risolvibili, Solver3 esplora lo spazio delle soluzioni in modo sistematico: se una scelta porta a un conflitto, torna indietro e prova un'alternativa.

```bash
# Attivare esplicitamente Solver3 (default in APT 3.0+)
sudo apt -o APT::Solver=3.0 install pacchetto-complesso

# Debug della risoluzione: mostra il ragionamento del solver
sudo apt install -o Debug::APT::Solver3=true pacchetto 2>&1 | less

# Il solver parte con un insieme vuoto, aggiunge i pacchetti installati
# manualmente, poi risolve le dipendenze incrementalmente.
# Se incontra un conflitto, esegue backtracking e prova alternative.
```

Vantaggi rispetto al solver precedente:

| Aspetto | Solver legacy | Solver3 |
|---|---|---|
| Strategia | Greedy (scelta irreversibile) | Backtracking (esplorazione completa) |
| Conflitti complessi | Puo fallire con "broken packages" | Trova la soluzione se esiste |
| Diagnostica errori | Messaggi generici | Spiegazione dettagliata del conflitto |
| Performance | Piu veloce su casi semplici | Ottimizzato con pruning e clausole persistenti |

#### Interfaccia utente rinnovata

APT 3.0 introduce un output completamente rielaborato per l'uso interattivo:

```bash
# Output colorato (default in APT 3.0+)
# Pacchetti da installare: verde
# Pacchetti da rimuovere: rosso
# Pacchetti da aggiornare: standard
sudo apt install nginx
# L'output usa colori per distinguere immediatamente le azioni

# Display colonnare per le ricerche
apt search "web server"
# I risultati sono allineati in colonne: nome, versione, descrizione

# Barra di progresso migliorata
# Durante download e installazione, una barra in fondo al terminale
# mostra la percentuale di completamento con stima del tempo rimanente

# Disabilitare i colori (per script o pipe)
apt --no-color search nginx
# oppure:
APT_COLOR=0 apt search nginx
```

#### DPkg::Lock::Timeout — Gestione lock senza script

L'opzione `DPkg::Lock::Timeout` permette ad APT di attendere automaticamente il rilascio del lock, senza necessita di script bash per il polling.

```bash
# Attendere fino a 120 secondi per il rilascio del lock
sudo apt-get -o DPkg::Lock::Timeout=120 install nginx

# Configurazione persistente in /etc/apt/apt.conf.d/99lock-timeout
# DPkg::Lock::Timeout "120";

# Particolarmente utile in:
# - Ambienti CI/CD dove unattended-upgrades puo acquisire il lock
# - Cloud-init che esegue apt in parallelo con configurazioni utente
# - Ansible/Puppet che invocano apt su macchine appena create

# Valore -1: attesa infinita (usare con cautela)
sudo apt-get -o DPkg::Lock::Timeout=-1 install nginx
```

#### Altre novita APT 3.0+

```bash
# APT 3.2: logging JSONL per metriche di performance
# Ogni operazione APT puo produrre un log strutturato in formato JSONL
# utile per debug, testing e analisi del comportamento

# APT 3.2: miglioramenti al rollback della cronologia
# (in sviluppo, segue il modello di dnf history undo)

# Pattern matching migliorato
apt list --installed '~nlib*ssl*'
# Supporta globbing e pattern estesi per le query
```

### Aggiornamenti graduali (Phased Updates)

Ubuntu implementa un sistema di **phased updates**: gli aggiornamenti non vengono rilasciati a tutti gli utenti contemporaneamente ma in fasi progressive, in modo da rilevare eventuali regressioni prima che l'intera base utenti sia colpita.

#### Come funzionano

```
Fase 1: aggiornamento disponibile per il 10% degli utenti
   ↓ (monitoraggio crash reports, apport, errori)
Fase 2: 20% degli utenti
   ↓
Fase 3: 50% degli utenti
   ↓
Fase 4: 100% degli utenti (update completo)

Se vengono rilevate regressioni in qualsiasi fase → rollback
```

La macchina viene assegnata a una fase in base all'hash del proprio `machine-id` combinato con il nome del pacchetto. Il risultato e deterministico: la stessa macchina e sempre nella stessa fase per lo stesso pacchetto.

```bash
# Verificare se un pacchetto e in phased update
apt-cache policy firefox
# Phased-Update-Percentage: 20
# Significa: solo il 20% delle macchine riceve questo aggiornamento ora

# Forzare l'installazione di un pacchetto in phased update
# (NON raccomandato in produzione)
sudo apt install -o APT::Get::Always-Include-Phased-Updates=true firefox

# Configurazione persistente per ricevere sempre tutti gli aggiornamenti
# /etc/apt/apt.conf.d/99phased-updates
# APT::Get::Always-Include-Phased-Updates "true";

# In ambienti di test/staging, ricevere tutti gli aggiornamenti e utile
# per anticipare i problemi prima del rollout in produzione

# Verificare il proprio machine-id
cat /etc/machine-id
```

> **In produzione:** non forzare i phased updates. Il sistema e progettato per proteggere dagli aggiornamenti difettosi. Se un aggiornamento e necessario immediatamente, installarlo esplicitamente per versione: `sudo apt install firefox=versione-specifica`.

#### Impatto dei phased updates su infrastrutture gestite

In ambienti con flotte di server gestiti (Ansible, Puppet, Chef), i phased updates possono causare incoerenze: macchine diverse nella stessa flotta possono avere versioni diverse dello stesso pacchetto. Strategie di mitigazione:

```bash
# Strategia 1: Disabilitare phased updates su tutta la flotta
# /etc/apt/apt.conf.d/99phased-updates
APT::Get::Always-Include-Phased-Updates "true";
# Tutte le macchine ricevono lo stesso aggiornamento nello stesso momento
# Testare prima in staging

# Strategia 2: Pinning esplicito delle versioni in produzione
# Aggiornare solo tramite playbook Ansible con versioni specificate
# ansible task:
# apt: name=nginx=1.24.0-2ubuntu1 state=present

# Strategia 3: Repository mirror controllato
# Usare apt-mirror o aptly per creare uno snapshot del repository
# Aggiornare il mirror solo dopo test in staging
# Tutte le macchine puntano allo stesso snapshot
```

---

## dpkg — Internals

### Formato .deb

Un file `.deb` e un archivio `ar(1)` che contiene tre componenti:

```bash
# Esaminare la struttura di un .deb
ar t pacchetto.deb
# Output:
#   debian-binary        ← Versione del formato (attualmente "2.0")
#   control.tar.zst      ← Metadati e script di manutenzione
#   data.tar.zst         ← File effettivi da installare

# Estrarre il contenuto
ar x pacchetto.deb
# Produce: debian-binary, control.tar.zst, data.tar.zst

# Visualizzare debian-binary
cat debian-binary
# 2.0

# Estrarre i metadati
tar xf control.tar.zst
# Produce: control, md5sums, conffiles, preinst, postinst, prerm, postrm

# Estrarre i file installabili
mkdir data && tar xf data.tar.zst -C data
# Produce l'albero dei file (usr/, etc/, ...)
```

### File di controllo

Il file `control` dentro `control.tar` e il cuore dei metadati:

```
Package: mio-software
Version: 1.2.3-1
Section: utils
Priority: optional
Architecture: amd64
Depends: libc6 (>= 2.31), libssl3 (>= 3.0.0)
Pre-Depends: dpkg (>= 1.17.5)
Recommends: mio-software-doc
Suggests: mio-software-extras
Conflicts: vecchio-software
Replaces: vecchio-software
Provides: servizio-generico
Installed-Size: 1024
Maintainer: Nome Cognome <email@example.com>
Description: Breve descrizione del software
 Descrizione lunga che puo occupare
 piu righe, indentate con uno spazio.
 .
 Un punto su riga a se stante indica un paragrafo vuoto.
Homepage: https://example.com
```

Campi di dipendenza:

| Campo | Significato |
|---|---|
| `Depends` | Obbligatorio, deve essere installato |
| `Pre-Depends` | Come Depends, ma deve essere configurato PRIMA dell'unpack |
| `Recommends` | Fortemente consigliato (installato per default con apt) |
| `Suggests` | Opzionale, migliora la funzionalita |
| `Conflicts` | Non puo coesistere con questi pacchetti |
| `Replaces` | Questo pacchetto sovrascrive file di un altro |
| `Provides` | Questo pacchetto fornisce un pacchetto virtuale |
| `Breaks` | Rompe versioni precedenti di un altro pacchetto |

File `conffiles` — elenca i file di configurazione che non devono essere sovrascritti automaticamente:

```
/etc/mio-software/config.conf
/etc/mio-software/rules.d/default.conf
```

File `md5sums` — checksum di tutti i file installati, usato per la verifica di integrita.

### Maintainer scripts

Il ciclo di vita dell'installazione/rimozione esegue script in ordine preciso:

#### Installazione nuova

```
1. preinst install
2. (unpack dei file)
3. postinst configure
```

#### Upgrade

```
1. prerm upgrade <nuova-versione>     (vecchio pacchetto)
2. preinst upgrade <vecchia-versione> (nuovo pacchetto)
3. (unpack dei nuovi file)
4. postrm upgrade <nuova-versione>    (vecchio pacchetto)
5. postinst configure <vecchia-versione> (nuovo pacchetto)
```

#### Rimozione

```
1. prerm remove
2. (rimozione file, eccetto conffiles)
3. postrm remove
```

#### Purge (rimozione completa)

```
1. postrm purge
   (rimozione conffiles e pulizia finale)
```

Esempio di `postinst`:

```bash
#!/bin/bash
set -e

case "$1" in
    configure)
        # Creare utente di sistema se non esiste
        if ! getent passwd miosoftware > /dev/null 2>&1; then
            adduser --system --group --no-create-home \
                --home /var/lib/miosoftware miosoftware
        fi

        # Impostare permessi
        chown -R miosoftware:miosoftware /var/lib/miosoftware

        # Abilitare e avviare il servizio
        systemctl daemon-reload
        systemctl enable miosoftware.service
        ;;
    abort-upgrade|abort-remove|abort-deconfigure)
        ;;
    *)
        echo "postinst: argomento sconosciuto '$1'" >&2
        exit 1
        ;;
esac

exit 0
```

### Query e verifica dpkg

```bash
# Stato di un pacchetto
dpkg -s nginx
# Mostra: stato (installed/not-installed), versione, dipendenze

# Lista file di un pacchetto installato
dpkg -L nginx

# Trovare il pacchetto che possiede un file
dpkg -S /usr/bin/curl
# curl: /usr/bin/curl

# Verificare integrita di tutti i pacchetti installati
dpkg -V
# Mostra file modificati rispetto all'installazione originale

# Verificare un singolo pacchetto
dpkg -V nginx
# Output vuoto = tutto ok
# Output con flag: c = conffile, 5 = md5sum diverso

# Elenco con stato dettagliato
dpkg -l 'nginx*'
# ii = installed, rc = removed but config remains, un = not installed

# Riconfigurare un pacchetto
sudo dpkg-reconfigure locales
sudo dpkg-reconfigure tzdata

# Ripristinare il database dpkg (emergenza)
sudo dpkg --configure -a    # Configura tutti i pacchetti semi-installati
sudo dpkg --audit            # Mostra pacchetti in stato inconsistente
```

---

## DNF/YUM — Deep Dive

### Comandi fondamentali

```bash
# DNF (Fedora, RHEL 8+, CentOS Stream)
sudo dnf update                      # Aggiorna tutto
sudo dnf install httpd               # Installa
sudo dnf remove httpd                # Rimuove
sudo dnf search nginx                # Cerca
dnf info nginx                       # Info
dnf list installed                   # Pacchetti installati
sudo dnf autoremove                  # Orfani
sudo dnf clean all                   # Pulisci cache
```

### Configurazione dnf.conf

File principale: `/etc/dnf/dnf.conf`

```ini
[main]
# Directory cache
cachedir=/var/cache/dnf
# Mantieni la cache dopo installazione (utile per rollback)
keepcache=True
# Log file
logdir=/var/log/dnf
# Livello di debug (0-10)
debuglevel=2
# Verifica GPG obbligatoria
gpgcheck=True
# Installa solo pacchetti con firma GPG valida
localpkg_gpgcheck=True
# Numero massimo di download paralleli
max_parallel_downloads=10
# Timeout connessione
timeout=30
# Tentativi di retry
retries=5
# Versioni del kernel da mantenere
installonly_limit=3
# Migliore candidato per l'architettura
best=True
# Non installare pacchetti "deboli" (Recommends equivalente)
install_weak_deps=False
# Proxy
proxy=http://proxy.azienda.it:8080
proxy_username=utente
proxy_password=password
# Plugin
plugins=True
# Escludere pacchetti globalmente
excludepkgs=kernel*-debug
```

### Gestione repository DNF

File: `/etc/yum.repos.d/*.repo`

```ini
# /etc/yum.repos.d/custom.repo
[custom-repo]
name=Repository Personalizzato
baseurl=https://repo.example.com/el9/$basearch/
# Alternativa: mirrorlist o metalink
# mirrorlist=https://mirrors.example.com/el9
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-custom
# Priorita (plugin priorities): 1 = massima, 99 = minima
priority=10
# Metadati: per quanto tempo la cache e valida (secondi)
metadata_expire=86400
# Escludere specifici pacchetti da questo repo
exclude=debug* *-devel
# Includere solo specifici pacchetti
# includepkgs=nginx* httpd*
# Throttle bandwidth
throttle=1M
# SSL
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
```

```bash
# Gestione repository da CLI
sudo dnf config-manager --add-repo https://repo.example.com/example.repo
sudo dnf config-manager --set-enabled custom-repo
sudo dnf config-manager --set-disabled custom-repo
sudo dnf install epel-release        # Repository EPEL (Extra Packages)

# Lista repository attivi
dnf repolist
dnf repolist all                     # Tutti, inclusi i disabilitati

# Info su un repository
dnf repoinfo epel

# Pacchetti disponibili da un repository specifico
dnf repo-pkgs epel list available
```

### Moduli e gruppi

```bash
# GRUPPI: insiemi tematici di pacchetti
sudo dnf group list                  # Lista gruppi disponibili
sudo dnf group list --hidden         # Anche gruppi nascosti
sudo dnf group info "Development Tools"  # Dettagli: mandatory, default, optional
sudo dnf group install "Development Tools"
sudo dnf group remove "Development Tools"
sudo dnf group upgrade "Development Tools"

# MODULI (RHEL 8+, CentOS Stream): versioni multiple dello stesso software
dnf module list                      # Lista tutti i moduli
dnf module list nodejs               # Versioni disponibili di nodejs
dnf module info nodejs:18            # Dettagli di uno stream specifico

sudo dnf module enable nodejs:18     # Abilita lo stream (non installa)
sudo dnf module install nodejs:18    # Abilita + installa
sudo dnf module install nodejs:18/development  # Profilo specifico

# Cambiare stream (es. da nodejs:18 a nodejs:20)
sudo dnf module reset nodejs         # Reset dello stream corrente
sudo dnf module enable nodejs:20     # Abilita il nuovo
sudo dnf module install nodejs:20    # Installa

sudo dnf module disable nodejs       # Disabilita completamente il modulo
```

### DNF history e rollback

DNF registra ogni transazione nel suo database. Si possono ispezionare e annullare.

```bash
# Visualizzare la cronologia
dnf history
# Output:
# ID | Comando          | Data/Ora           | Azione | Modificati
#  7 | install httpd    | 2026-05-20 14:30   | I      | 4

# Dettagli di una transazione
dnf history info 7

# Pacchetti modificati nella transazione
dnf history info 7 --verbose

# ROLLBACK: annullare una transazione specifica
sudo dnf history undo 7
# Questo rimuove httpd e le sue dipendenze installate nella transazione 7

# ROLLBACK a uno stato precedente (annulla TUTTE le transazioni dopo l'ID)
sudo dnf history rollback 5
# Riporta il sistema allo stato dopo la transazione 5

# Ripetere una transazione
sudo dnf history redo 7

# Salvare e ripristinare la lista pacchetti
dnf repoquery --installed --qf '%{name}' > pacchetti-installati.txt
# Su un altro sistema:
sudo dnf install $(cat pacchetti-installati.txt)
```

### DNF5 — Architettura di nuova generazione

DNF5 e il successore di DNF4, riscritto in C++ per eliminare la dipendenza da Python nel core e migliorare le prestazioni. Diventa il package manager predefinito a partire da **Fedora 41** (ottobre 2024) e sara adottato in **RHEL 10**. Unifica le funzionalita di DNF e MicroDNF in un singolo tool.

#### Architettura DNF5

```
+--------------------------------------------------+
|              Interfacce utente                    |
|  dnf5 CLI  |  dnf5daemon (D-Bus)  |  Bindings    |
+--------------------------------------------------+
|              libdnf5-cli                          |
|  Formattazione output, progress bar, tabelle      |
+--------------------------------------------------+
|              libdnf5 (core C++)                   |
|  Repository, solver (libsolv), RPM, config,       |
|  download, transaction                            |
+--------------------------------------------------+
|              libsolv + librpm                     |
|  Risoluzione dipendenze + database RPM            |
+--------------------------------------------------+
```

Tre livelli distinti:

- **libdnf5**: libreria core C++ con tutta la logica di gestione pacchetti, repository, download e transazioni. Non dipende da Python.
- **libdnf5-cli**: libreria per la formattazione dell'output CLI (tabelle, progress bar, colori).
- **dnf5**: il tool da riga di comando che usa le due librerie.
- **dnf5daemon-server**: servizio D-Bus per l'integrazione con desktop environment (alternativa a PackageKit).

#### Differenze principali da DNF4

| Aspetto | DNF4 | DNF5 |
|---|---|---|
| Linguaggio | Python + C (librerie) | C++ (core) + binding Python |
| Dipendenza Python | Obbligatoria | Solo per plugin Python |
| Daemon | PackageKit (separato) | dnf5daemon integrato |
| Plugin | Solo Python | C++ e Python |
| MicroDNF | Tool separato | Fuso in dnf5 |
| Uso disco | ~45 MB (Python + dipendenze) | ~15 MB |
| Velocita avvio | ~1.5s | ~0.3s |
| History migration | — | Stato di sistema migrato, history no |

#### Comandi DNF5

La maggior parte dei comandi e compatibile con DNF4, ma con alcune differenze sintattiche:

```bash
# Comandi base (identici a DNF4)
sudo dnf5 install httpd
sudo dnf5 remove httpd
sudo dnf5 update
sudo dnf5 search nginx
dnf5 info nginx
dnf5 list --installed

# Comandi rinominati o modificati
dnf5 repoquery --whatprovides "*/nginx"   # Era: dnf provides
dnf5 repoquery --requires nginx           # Era: dnf repoquery --requires
dnf5 advisory list                        # Era: dnf updateinfo list

# Nuovi comandi
dnf5 versionlock add nginx                # Blocco versione (era un plugin)
dnf5 versionlock list
dnf5 versionlock delete nginx

# Offline updates (integrato nel core)
sudo dnf5 offline upgrade                 # Prepara aggiornamento offline
sudo dnf5 offline reboot                  # Riavvia e applica
sudo dnf5 offline status                  # Stato dell'aggiornamento
sudo dnf5 offline log                     # Log dell'ultimo aggiornamento

# System upgrade (sostituzione di dnf-plugin-system-upgrade)
sudo dnf5 system-upgrade download --releasever=42
sudo dnf5 system-upgrade reboot

# Gestione gruppi e ambienti
dnf5 group list
sudo dnf5 group install "Development Tools"
dnf5 environment list
```

#### Plugin DNF5

Il sistema di plugin e stato riprogettato. I plugin libdnf5 (C++ o Python) operano a livello di libreria e sono disponibili sia per dnf5 CLI che per dnf5daemon.

```bash
# Plugin inclusi nel pacchetto dnf5-plugins:
# - automatic: aggiornamenti automatici (sostituzione di dnf-automatic)
# - changelog: visualizzazione changelog
# - copr: gestione repository COPR
# - versionlock: blocco versioni (precedentemente plugin separato)

# Installare i plugin
sudo dnf5 install dnf5-plugins

# Esempio: dnf5 automatic (sostituzione di dnf-automatic)
# Configurazione: /etc/dnf/automatic.conf (formato compatibile)
sudo systemctl enable --now dnf5-automatic.timer

# Verificare plugin attivi
dnf5 --help | grep -A2 "Plugin commands"
```

#### dnf5daemon — Servizio D-Bus

Il daemon D-Bus fornisce accesso alla gestione pacchetti per applicazioni desktop (GNOME Software, KDE Discover) senza richiedere accesso root diretto.

```bash
# Il daemon si attiva automaticamente via D-Bus on-demand
# Servizio: org.rpm.dnf.v0

# Verifica stato
systemctl status dnf5daemon-server

# Interazione via D-Bus (esempio)
busctl introspect org.rpm.dnf.v0 /org/rpm/dnf/v0

# Le applicazioni desktop (GNOME Software) usano il daemon
# per installare, aggiornare e rimuovere pacchetti con PolicyKit
```

#### Migrazione da DNF4 a DNF5

```bash
# Su Fedora 41+, la migrazione e automatica durante l'upgrade
# Il pacchetto "dnf" diventa un alias per "dnf5"

# Lo stato del sistema (pacchetti user-installed vs auto) viene migrato
# La cronologia delle transazioni NON viene migrata

# Verificare la migrazione
dnf5 --version
which dnf     # Dovrebbe puntare a dnf5

# Compatibilita: il vecchio comando "dnf" continua a funzionare
# come alias/wrapper per dnf5

# Script che usano "dnf" direttamente continuano a funzionare
# per la maggior parte dei casi d'uso

# Differenze che possono rompere script:
# - Output formattato diversamente (non fare parsing dell'output dnf)
# - Alcuni plugin Python DNF4 non sono compatibili
# - Flag --setopt ha sintassi leggermente diversa
# - Le query repoquery hanno output diverso

# Raccomandazione: negli script, usare le opzioni long-form
# e non fare parsing dell'output di dnf
```

#### Configurazione DNF5

Il file di configurazione principale resta `/etc/dnf/dnf.conf`, con compatibilita quasi completa con DNF4:

```ini
# /etc/dnf/dnf.conf — opzioni specifiche DNF5
[main]
gpgcheck=True
installonly_limit=3
best=True
skip_if_unavailable=False
# Nuove opzioni DNF5:
# Numero massimo di download paralleli (default: 3, massimo: 20)
max_parallel_downloads=10
# Timeout per i metadati del repository (secondi)
metadata_expire=172800
# Percorso per il database delle transazioni DNF5
# (separato da DNF4, migrato automaticamente)
system_state_dir=/usr/lib/sysimage/libdnf5
```

#### createrepo_c avanzato per repository RPM

`createrepo_c` e il tool standard per generare e mantenere metadati di repository RPM. La versione C e significativamente piu veloce della versione Python originale.

```bash
# Installazione
sudo dnf install createrepo_c

# Creare un repository con metadati completi
sudo createrepo_c --database /srv/rpm-repo/el9/x86_64/
# --database: genera database SQLite per query veloci

# Aggiornamento incrementale (molto piu veloce per repository grandi)
sudo createrepo_c --update --recycle-pkglist /srv/rpm-repo/el9/x86_64/
# --recycle-pkglist: riutilizza la lista pacchetti esistente
# Solo i pacchetti nuovi o modificati vengono analizzati

# Generare metadati con checksum SHA512 (sicurezza migliorata)
sudo createrepo_c --checksum sha512 /srv/rpm-repo/el9/x86_64/

# Includere gruppi e ambienti (comps.xml)
sudo createrepo_c --groupfile comps.xml /srv/rpm-repo/el9/x86_64/

# Aggiungere moduli (modulemd)
sudo createrepo_c --mdtype modules \
  --extra-metadata modules.yaml.gz /srv/rpm-repo/el9/x86_64/

# Firmare i metadati del repository
gpg --detach-sign --armor /srv/rpm-repo/el9/x86_64/repodata/repomd.xml

# Verificare il repository
sudo createrepo_c --check-ts /srv/rpm-repo/el9/x86_64/

# Statistiche del repository
createrepo_c --stats /srv/rpm-repo/el9/x86_64/
```

**Struttura dei metadati repodata:**

```
repodata/
├── repomd.xml              ← Indice principale (firmato con GPG)
├── primary.xml.zst         ← Pacchetti: nome, versione, dipendenze
├── filelists.xml.zst       ← Lista file per ogni pacchetto
├── other.xml.zst           ← Changelog per ogni pacchetto
├── primary.sqlite.zst      ← Database SQLite per query rapide
├── comps.xml.zst           ← Gruppi e ambienti (opzionale)
└── modules.yaml.zst        ← Metadati modulari (opzionale)
```

---

## RPM — Internals

### Formato .rpm

Un file RPM e composto da quattro sezioni:

```
+-------------------+
| Lead              |  ← Identificatore "magic number" RPM
+-------------------+
| Signature         |  ← Firma GPG + digest del pacchetto
+-------------------+
| Header            |  ← Metadati: nome, versione, dipendenze, script
+-------------------+
| Payload           |  ← Archivio cpio compresso con i file effettivi
+-------------------+
```

```bash
# Gestione RPM diretta
sudo rpm -ivh pacchetto.rpm          # Installa (verbose + hash progress)
sudo rpm -Uvh pacchetto.rpm          # Upgrade (installa se non presente)
sudo rpm -Fvh pacchetto.rpm          # Freshen (upgrade solo se gia installato)
sudo rpm -e pacchetto                # Rimuovi
rpm -qa | grep nginx                 # Lista con filtro
rpm -ql nginx                        # File del pacchetto
rpm -qf /usr/sbin/nginx             # Pacchetto proprietario del file

# Esaminare un .rpm senza installarlo
rpm -qip pacchetto.rpm              # Info del pacchetto
rpm -qlp pacchetto.rpm              # Lista file contenuti
rpm -qRp pacchetto.rpm              # Dipendenze richieste
rpm -q --scripts pacchetto           # Visualizza script pre/post
```

### Spec files

Il file `.spec` e la ricetta per costruire un pacchetto RPM. Risiede in `~/rpmbuild/SPECS/`.

```spec
Name:           mio-software
Version:        1.2.3
Release:        1%{?dist}
Summary:        Breve descrizione del software
License:        MIT
URL:            https://example.com
Source0:        https://example.com/releases/%{name}-%{version}.tar.gz

BuildRequires:  gcc >= 10
BuildRequires:  make
BuildRequires:  openssl-devel
Requires:       openssl >= 3.0
Requires:       glibc >= 2.34

%description
Descrizione lunga del pacchetto.
Puo occupare piu righe.

%prep
# Preparazione dei sorgenti
%autosetup -n %{name}-%{version}

%build
# Compilazione
%configure
%make_build

%install
# Installazione nella buildroot
%make_install

%files
# Lista dei file da includere nel pacchetto
%license LICENSE
%doc README.md
%{_bindir}/mio-software
%{_mandir}/man1/mio-software.1*
%config(noreplace) %{_sysconfdir}/mio-software/config.conf
%dir %{_datadir}/mio-software/

%pre
# Script pre-installazione
getent group miosoftware >/dev/null || groupadd -r miosoftware
getent passwd miosoftware >/dev/null || \
    useradd -r -g miosoftware -d /var/lib/miosoftware -s /sbin/nologin miosoftware

%post
# Script post-installazione
systemctl daemon-reload
systemctl enable miosoftware.service

%preun
# Script pre-rimozione (solo se rimozione completa, non upgrade)
if [ $1 -eq 0 ]; then
    systemctl stop miosoftware.service
    systemctl disable miosoftware.service
fi

%postun
# Script post-rimozione
if [ $1 -eq 0 ]; then
    systemctl daemon-reload
fi

%changelog
* Thu May 22 2026 Nome Cognome <email@example.com> - 1.2.3-1
- Rilascio iniziale
```

Nota: la variabile `$1` negli script RPM indica:
- `1` = prima installazione
- `2` = upgrade (vecchio pacchetto rimosso dopo l'installazione del nuovo)
- `0` = rimozione completa

### Query RPM avanzate

```bash
# Formato personalizzato delle query
rpm -qa --qf '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n'

# Pacchetti installati ordinati per data
rpm -qa --qf '%{INSTALLTIME:date} %{NAME}-%{VERSION}\n' | sort

# Pacchetti installati nelle ultime 24 ore
rpm -qa --qf '%{INSTALLTIME} %{NAME}\n' | \
  awk -v cutoff="$(date -d '24 hours ago' +%s)" '$1 > cutoff {print $2}'

# Dimensione di tutti i pacchetti installati
rpm -qa --qf '%{SIZE} %{NAME}\n' | sort -rn | head -20

# Dipendenze di un pacchetto
rpm -qR nginx

# Cosa fornisce un pacchetto (Provides)
rpm -q --provides nginx

# Capacita richieste non soddisfatte
rpm -Va --nofiles --nodigest

# Script di un pacchetto
rpm -q --scripts nginx

# Changelog
rpm -q --changelog nginx | head -50
```

### Verifica RPM

```bash
# Verificare l'integrita di un pacchetto installato
rpm -V nginx
# Output vuoto = tutto ok
# Flag:
#   S = dimensione diversa
#   M = permessi diversi
#   5 = MD5 checksum diverso
#   D = device diverso
#   L = link diverso
#   U = utente proprietario diverso
#   G = gruppo proprietario diverso
#   T = timestamp diverso
#   P = capabilities diverse

# Esempio output:
# S.5....T.  c /etc/nginx/nginx.conf
# Significa: dimensione cambiata, md5 diverso, timestamp diverso,
# "c" indica che e un conffile

# Verificare TUTTI i pacchetti
rpm -Va

# Verificare firma GPG di un .rpm
rpm --checksig pacchetto.rpm
# pacchetto.rpm: digests signatures OK

# Importare una chiave GPG
sudo rpm --import https://example.com/RPM-GPG-KEY

# Lista chiavi GPG importate
rpm -qa gpg-pubkey*
rpm -qi gpg-pubkey-XXXX
```

---

## Pacman — Arch Linux

```bash
# Pacman
sudo pacman -Syu                     # Sincronizza DB + aggiorna tutto
sudo pacman -S nginx                 # Installa
sudo pacman -R nginx                 # Rimuove
sudo pacman -Rs nginx                # Rimuove + dipendenze orfane
sudo pacman -Ss nginx                # Cerca
pacman -Qi nginx                     # Info pacchetto installato
pacman -Ql nginx                     # File del pacchetto
sudo pacman -Sc                      # Pulisci cache vecchie versioni

# AUR (Arch User Repository) — con yay
yay -S pacchetto-aur                 # Installa da AUR
yay -Syu                             # Aggiorna tutto (repo + AUR)
```

### Comandi avanzati Pacman

```bash
# Pacchetti orfani (installati come dipendenza, non piu richiesti)
pacman -Qdt

# Rimuovere tutti gli orfani
sudo pacman -Rns $(pacman -Qdtq)

# Pacchetti installati esplicitamente (non come dipendenza)
pacman -Qet

# File di un pacchetto NON installato (dal repository)
pacman -Fl nginx

# Quale pacchetto possiede un file
pacman -Qo /usr/bin/curl

# Verifica integrita
pacman -Qk nginx
# nginx: 45 total files, 0 missing files

# Cache: versioni disponibili
ls /var/cache/pacman/pkg/ | grep nginx

# Downgrade con cache locale
sudo pacman -U /var/cache/pacman/pkg/nginx-1.24.0-1-x86_64.pkg.tar.zst

# Database delle chiavi
sudo pacman-key --init
sudo pacman-key --populate archlinux
sudo pacman-key --refresh-keys
```

---

## Costruzione pacchetti

### Creare pacchetti .deb

#### Metodo 1: dpkg-buildpackage (standard Debian)

Struttura di un pacchetto sorgente Debian:

```
mio-software-1.0/
├── debian/
│   ├── control          # Metadati del pacchetto
│   ├── rules            # Makefile di build
│   ├── changelog        # Cronologia versioni (formato specifico)
│   ├── copyright        # Licenza
│   ├── compat           # Livello di compatibilita debhelper
│   ├── install          # File da installare
│   ├── dirs             # Directory da creare
│   ├── mio-software.service  # Unit systemd (opzionale)
│   ├── postinst         # Script post-installazione
│   └── source/
│       └── format       # Formato del pacchetto sorgente ("3.0 (quilt)")
└── src/
    └── main.c
```

```bash
# Prerequisiti
sudo apt install build-essential devscripts debhelper dh-make

# Creare lo scheletro iniziale
cd mio-software-1.0/
dh_make --createorig -s -y
# -s: single binary package
# --createorig: crea il tarball .orig.tar.gz

# Modificare debian/control, debian/rules, debian/changelog

# Build del pacchetto
dpkg-buildpackage -us -uc -b
# -us: non firmare sorgente
# -uc: non firmare changes
# -b: solo binario (no sorgente)
# Il .deb viene creato nella directory parent

# Alternativa piu automatizzata
debuild -us -uc

# Controllare il pacchetto risultante
lintian ../mio-software_1.0-1_amd64.deb
# lintian verifica conformita alla Debian policy
```

Il file `debian/rules` minimo con debhelper:

```makefile
#!/usr/bin/make -f
%:
	dh $@
```

Il file `debian/changelog` ha un formato preciso:

```
mio-software (1.0-1) stable; urgency=medium

  * Rilascio iniziale.
  * Aggiunta funzionalita X.

 -- Nome Cognome <email@example.com>  Wed, 22 May 2026 10:00:00 +0200
```

#### Metodo 2: Pacchetto binario semplice con fpm

```bash
# fpm: tool multi-formato per creare pacchetti rapidamente
sudo gem install fpm

# Creare un .deb da una directory
fpm -s dir -t deb \
  --name mio-software \
  --version 1.0 \
  --description "Descrizione" \
  --depends "libssl3 >= 3.0" \
  --after-install scripts/postinst.sh \
  /opt/mio-software/=/opt/mio-software/

# Creare un .deb da un tarball
fpm -s tar -t deb --name mio-software --version 1.0 \
  mio-software-1.0.tar.gz
```

### Creare pacchetti .rpm

```bash
# Prerequisiti
sudo dnf install rpm-build rpmdevtools

# Creare la struttura di directory standard
rpmdev-setuptree
# Crea ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Copiare il tarball sorgente
cp mio-software-1.2.3.tar.gz ~/rpmbuild/SOURCES/

# Creare il file spec (vedi sezione RPM Internals sopra)
vim ~/rpmbuild/SPECS/mio-software.spec

# Build del pacchetto
rpmbuild -ba ~/rpmbuild/SPECS/mio-software.spec
# -ba: build all (binary + source RPM)
# -bb: solo binary RPM
# -bs: solo source RPM

# Il risultato si trova in:
# ~/rpmbuild/RPMS/x86_64/mio-software-1.2.3-1.el9.x86_64.rpm
# ~/rpmbuild/SRPMS/mio-software-1.2.3-1.el9.src.rpm

# Verificare il pacchetto
rpmlint ~/rpmbuild/RPMS/x86_64/mio-software-1.2.3-1.el9.x86_64.rpm

# Build in ambiente isolato (mock)
sudo dnf install mock
sudo usermod -aG mock $USER
mock -r rocky-9-x86_64 --rebuild ~/rpmbuild/SRPMS/mio-software-1.2.3-1.el9.src.rpm
```

---

## Snap, Flatpak e AppImage — Confronto approfondito

### Snap (Canonical)

```bash
sudo apt install snapd               # Installa snapd
snap find firefox                    # Cerca
sudo snap install firefox            # Installa
sudo snap remove firefox             # Rimuovi
snap list                            # Lista installati
sudo snap refresh                    # Aggiorna tutti gli snap
snap info firefox                    # Dettagli
```

**Architettura Snap:**

- Il demone `snapd` gestisce tutto il ciclo di vita.
- Ogni snap e un file `.snap`: un filesystem SquashFS montato in sola lettura.
- Punto di mount: `/snap/<nome>/<revisione>/`
- Dati utente: `~/snap/<nome>/current/`
- Il confinamento usa AppArmor (obbligatorio) + seccomp + cgroups + namespaces.

```bash
# Livelli di confinamento
snap install --classic code          # classic: accesso completo (no sandbox)
snap install firefox                 # strict: sandbox completa (default)
snap install --devmode test-app      # devmode: sandbox permissiva (sviluppo)

# Connessioni (interfacce)
snap connections firefox             # Mostra interfacce connesse
snap connect firefox:camera          # Concedi accesso alla camera
snap disconnect firefox:camera       # Revoca

# Canali di distribuzione
snap info firefox                    # Mostra canali: stable, candidate, beta, edge
sudo snap refresh firefox --channel=beta

# Revisioni e rollback
snap list --all firefox              # Tutte le revisioni installate
sudo snap revert firefox             # Torna alla revisione precedente

# Servizi snap
snap services                        # Lista servizi snap
sudo snap start mio-servizio
sudo snap stop mio-servizio
sudo snap restart mio-servizio
```

### Flatpak

```bash
sudo apt install flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak search gimp                  # Cerca
flatpak install flathub org.gimp.GIMP  # Installa
flatpak update                       # Aggiorna tutti
flatpak list                         # Lista installati
flatpak uninstall org.gimp.GIMP      # Rimuovi
```

**Architettura Flatpak:**

- Basato su OSTree (sistema di versionamento per filesystem).
- Runtime condivisi: `org.freedesktop.Platform`, `org.gnome.Platform`, `org.kde.Platform`.
- Sandbox: Bubblewrap + portals per accesso controllato al sistema.
- Dati: `~/.var/app/<app-id>/`

```bash
# Gestione runtime
flatpak list --runtime                # Runtime installati
flatpak update --runtime              # Aggiorna solo runtime

# Permessi
flatpak info --show-permissions org.gimp.GIMP

# Override permessi per utente
flatpak override --user --filesystem=home org.gimp.GIMP
flatpak override --user --nofilesystem=home org.gimp.GIMP
flatpak override --user --show org.gimp.GIMP

# Pulizia
flatpak uninstall --unused           # Rimuovi runtime non piu necessari
flatpak repair                       # Ripara installazione corrotta
```

#### Portali XDG e modello di sicurezza Flatpak

I portali (XDG Desktop Portals) sono il meccanismo con cui le applicazioni Flatpak sandboxed accedono alle risorse del sistema senza avere permessi statici. Il portale funge da intermediario: l'app chiede accesso, il desktop environment presenta un dialog all'utente, e solo con il consenso esplicito l'accesso viene concesso.

**Portali disponibili:**

| Portale | Funzione | Esempio |
|---|---|---|
| `FileChooser` | Accesso a file tramite dialog nativo | "Apri file" / "Salva con nome" |
| `Camera` | Accesso alla webcam | Videochiamata |
| `Screenshot` | Cattura schermo | Tool di annotazione |
| `ScreenCast` | Condivisione schermo / registrazione | Streaming |
| `Notification` | Invio notifiche desktop | Avvisi in background |
| `Secret` | Accesso al portachiavi | Password manager |
| `Location` | Geolocalizzazione | Mappe |
| `Print` | Stampa | Stampa documenti |
| `Clipboard` | Accesso alla clipboard | Copia/incolla tra app |
| `Background` | Esecuzione in background | Sincronizzazione |
| `Trash` | Spostamento nel cestino | Eliminazione file |
| `USB` | Accesso a dispositivi USB | Trasferimento dati |
| `GlobalShortcuts` | Scorciatoie da tastiera globali | Azioni rapide |
| `Inhibit` | Impedire sospensione / spegnimento | Presentazione |
| `InputCapture` | Cattura input (mouse/tastiera) | Barrier/KVM software |

```bash
# Visualizzare i portali disponibili sul sistema
ls /usr/share/xdg-desktop-portal/portals/

# Verificare il backend dei portali attivo
# GNOME: xdg-desktop-portal-gnome
# KDE: xdg-desktop-portal-kde
# wlroots: xdg-desktop-portal-wlr

# Diagnostica portali
busctl --user list | grep portal
systemctl --user status xdg-desktop-portal
```

**Permessi statici vs portali dinamici:**

I permessi statici sono dichiarati nel manifest dell'app e concessi all'installazione. I portali sono dinamici: richiesti a runtime, con consenso dell'utente. Flatpak preferisce i portali dove possibile.

```bash
# Visualizzare i permessi statici di un'app
flatpak info --show-permissions org.gimp.GIMP

# Permessi comuni statici
# --share=network        → accesso rete
# --share=ipc            → IPC tra processi
# --socket=x11           → display X11
# --socket=wayland       → display Wayland
# --socket=pulseaudio    → audio
# --device=dri           → accelerazione GPU
# --filesystem=home      → accesso a ~/  (PERICOLOSO)
# --filesystem=host      → accesso a /   (MOLTO PERICOLOSO)
# --talk-name=org.freedesktop.Notifications  → D-Bus specifico

# Flatseal: GUI per gestire i permessi
flatpak install flathub com.github.tchx84.Flatseal
# Permette di aggiungere/revocare permessi per ogni app installata

# Override permessi da CLI (per utente)
# Concedere accesso a una directory specifica
flatpak override --user --filesystem=/media/dati org.gimp.GIMP

# Revocare accesso alla rete
flatpak override --user --no-share=network org.app.Sospetta

# Revocare accesso al filesystem home
flatpak override --user --nofilesystem=home org.app.Esempio

# Visualizzare tutti gli override attivi
flatpak override --user --show org.gimp.GIMP

# Resettare tutti gli override
flatpak override --user --reset org.gimp.GIMP
```

#### Verifica e sicurezza su Flathub

Flathub implementa un modello di sicurezza a piu livelli per garantire l'affidabilita delle applicazioni distribuite.

**Sistema di verifica degli sviluppatori:**

Flathub distingue tra app **verificate** e non verificate. Un'app verificata mostra un badge di spunta che indica che lo sviluppatore ha dimostrato il controllo sull'identita associata (dominio web o account GitHub/GitLab).

```bash
# Controllare se un'app e verificata
flatpak remote-info flathub org.mozilla.firefox
# Il campo "metadata" include informazioni sulla verifica

# Installare solo da remote verificati
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
# Flathub e il remote verificato principale
```

**Processo di build sicuro:**

1. **Manifest pubblico**: ogni app su Flathub ha un manifest (YAML/JSON) in un repository Git pubblico che dichiara tutte le sorgenti e i passaggi di build.
2. **Build su infrastruttura Flathub**: il build avviene su server controllati da Flathub, non sulla macchina dello sviluppatore.
3. **Build senza rete**: durante la compilazione, l'accesso alla rete e disabilitato. Tutte le sorgenti devono essere pre-dichiarate con checksum.
4. **Verifica checksum**: le sorgenti scaricate vengono validate contro i checksum nel manifest. Se non corrispondono, il build fallisce.
5. **Firma Flathub**: il build risultante e firmato con la chiave di Flathub.
6. **Test automatici**: controlli automatici bloccano permessi pericolosi (accesso a bus D-Bus di sistema, nomi di bus non sicuri).

**Sicurezza per l'utente finale:**

```bash
# Le app Flatpak hanno ID reverse-DNS (org.mozilla.firefox)
# Questo identifica univocamente l'app e il suo sviluppatore

# Aggiornare tutte le app (le firme vengono verificate automaticamente)
flatpak update

# Verificare le app installate
flatpak list --columns=application,version,origin
# origin = "flathub" indica la fonte

# Rimuovere app da fonti non fidate
flatpak remote-list
flatpak remote-delete repo-sospetto
```

### AppImage

```bash
# File eseguibile autonomo, nessuna installazione
chmod +x applicazione.AppImage       # Rendi eseguibile
./applicazione.AppImage              # Esegui

# Estrarre il contenuto
./applicazione.AppImage --appimage-extract
# Produce la directory squashfs-root/

# Integrare nel desktop (opzionale)
# Usare appimaged o AppImageLauncher per integrazione automatica menu
```

**Architettura AppImage:**

- File singolo contenente: runtime + librerie + applicazione.
- Usa FUSE per montare il filesystem SquashFS interno.
- Nessun demone necessario, nessun sandboxing nativo.
- L'applicazione deve includere tutte le dipendenze tranne libc e il kernel.

### Confronto approfondito 2025

La maturazione dei tre formati nel 2024-2025 ha chiarito i rispettivi punti di forza. Snap ha migliorato i tempi di avvio con la compressione LZO e il pre-seeding, ma resta il piu lento in cold start. Flatpak ha consolidato il modello dei runtime condivisi e portali XDG, diventando il formato preferito dalla comunita desktop cross-distribuzione. AppImage resta la scelta piu semplice per distribuzione portatile ma senza sandboxing nativo.

**Benchmark tipici (cold start, SSD NVMe, 2025):**

| Applicazione | Nativo | Flatpak | Snap | AppImage |
|---|---|---|---|---|
| Firefox | ~0.8s | ~1.2s | ~2.5s | ~1.1s |
| LibreOffice Writer | ~1.5s | ~2.0s | ~3.8s | ~2.2s |
| GIMP | ~2.0s | ~2.5s | ~4.2s | ~2.8s |

> I tempi variano significativamente in base a hardware, filesystem e versione del kernel. Il warm start (seconda apertura) e molto piu veloce per tutti i formati grazie al caching del kernel.

**Impatto su disco (esempio con 5 app GNOME installate):**

| Metrica | Snap | Flatpak | AppImage |
|---|---|---|---|
| Runtime/base condiviso | No (ogni snap include tutto) | Si (~800 MB per org.gnome.Platform, condiviso) | No |
| Spazio 5 app | ~3.5 GB | ~2.0 GB (runtime + 5 app) | ~4.0 GB |
| Vecchie versioni | 2-3 revisioni mantenute di default | Solo ultima versione + delta OSTree | Manuale (file singoli) |

| Aspetto | Apt/Dnf | Snap | Flatpak | AppImage |
|---|---|---|---|---|
| Sandboxing | No | Si (AppArmor) | Si (Bubblewrap) | No |
| Aggiornamento auto | Manuale | Automatico (4x/giorno) | Manuale | Manuale |
| Dimensione | Piccola | Grande | Media (runtime condivisi) | Grande |
| Dipendenze | Condivise | Bundle | Runtime condivisi + bundle | Bundle completo |
| Storage dedup | Condivisione librerie | No | Si (OSTree) | No |
| Avvio a freddo | Veloce | Lento (mount SquashFS) | Medio | Medio (mount FUSE) |
| Desktop integration | Nativa | Limitata (temi, portals) | Buona (portals XDG) | Variabile |
| Distribuzione | Repo distro | Snap Store (Canonical) | Flathub + altri | Download diretto |
| Server use | Si | Possibile | No (solo desktop) | No |
| Root richiesto | Si | Si (snapd) | No (user install) | No |
| Ideale per | Server, sistema | Desktop Ubuntu | Desktop (cross-distro) | Distribuzione portatile |

### Impatto su disco

```bash
# Snap: ogni revisione occupa spazio separato
du -sh /snap/*/                      # Spazio per snap
snap list --all | awk 'NR>1{print $1, $2, $3, $6}'  # Revisioni conservate

# Rimuovere vecchie revisioni snap
sudo snap set system refresh.retain=2     # Mantieni solo 2 revisioni

# Flatpak: controllare spazio runtime
flatpak list --columns=application,installed-size,runtime

# Rimuovere dati residui di app disinstallate
flatpak uninstall --delete-data org.gimp.GIMP
```

---

## Nix e Guix — Gestione dichiarativa

### Nix

Nix e un package manager puramente funzionale: ogni pacchetto e costruito in isolamento e identificato da un hash crittografico dei suoi input. Due pacchetti con input diversi coesistono senza conflitti.

```bash
# Installazione di Nix (single-user)
sh <(curl -L https://nixos.org/nix/install) --no-daemon

# Installazione multi-user (raccomandato per produzione)
sh <(curl -L https://nixos.org/nix/install) --daemon

# Comandi base
nix-env -iA nixpkgs.firefox          # Installa
nix-env -e firefox                   # Rimuovi
nix-env -u                           # Aggiorna tutti
nix-env -qa 'firefox.*'              # Cerca
nix-env --list-generations            # Lista generazioni (snapshot)
nix-env --rollback                    # Torna alla generazione precedente
nix-env --switch-generation 5         # Passa a una generazione specifica

# Pulizia
nix-collect-garbage -d               # Rimuovi generazioni vecchie + garbage collect
nix-store --optimise                  # Deduplicazione hard links nel Nix store
```

**Nix store:**

```
/nix/store/
├── abc123...-firefox-128.0/           # Firefox versione 128
├── def456...-firefox-127.0/           # Firefox versione 127 (coesiste!)
├── ghi789...-glibc-2.39/             # glibc usata da entrambi
└── ...
```

Ogni path include l'hash dei build inputs. Cambiare una dipendenza produce un hash diverso, quindi un path diverso. Nessun conflitto possibile.

**Nix con flakes (approccio moderno):**

```nix
# flake.nix — definizione dichiarativa di un ambiente di sviluppo
{
  description = "Ambiente di sviluppo per il progetto";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
  };

  outputs = { self, nixpkgs }: {
    devShells.x86_64-linux.default = let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
    in pkgs.mkShell {
      buildInputs = [
        pkgs.python311
        pkgs.nodejs_20
        pkgs.postgresql_16
      ];
    };
  };
}
```

```bash
# Entrare nell'ambiente definito dal flake
nix develop

# Build di un pacchetto dal flake
nix build

# Eseguire un programma senza installarlo
nix run nixpkgs#cowsay -- "Ciao Nix"

# Shell temporanea con pacchetti specifici
nix shell nixpkgs#python311 nixpkgs#git
```

### Nix su distribuzioni non-NixOS

Nix funziona perfettamente su Ubuntu, Debian, Fedora, Arch e qualsiasi distribuzione Linux. Non e necessario usare NixOS per beneficiare del package manager Nix. L'installazione aggiunge solo la directory `/nix/store/` e un demone; non modifica il sistema host.

#### Installazione e configurazione

```bash
# Installazione multi-user (raccomandato, richiede systemd)
sh <(curl -L https://nixos.org/nix/install) --daemon

# Abilitare le funzionalita sperimentali (flakes + nix command)
mkdir -p ~/.config/nix
cat > ~/.config/nix/nix.conf <<'EOF'
experimental-features = nix-command flakes
# Cache binaria aggiuntiva (accelera i download)
extra-substituters = https://nix-community.cachix.org
extra-trusted-public-keys = nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs=
EOF

# Verificare l'installazione
nix --version
nix doctor
```

#### nix profile — Gestione imperativa moderna

`nix profile` sostituisce il vecchio `nix-env` con un approccio piu pulito e riproducibile. I pacchetti installati con `nix profile` sono tracciati da un manifest JSON, non da un'espressione Nix opaca.

```bash
# Installare pacchetti
nix profile install nixpkgs#firefox
nix profile install nixpkgs#git nixpkgs#ripgrep nixpkgs#fd

# Lista pacchetti installati nel profilo
nix profile list
# Output:
# Index: 0, Flake: nixpkgs#firefox, Store path: /nix/store/abc...-firefox-128.0
# Index: 1, Flake: nixpkgs#git, Store path: /nix/store/def...-git-2.45.0

# Aggiornare tutti i pacchetti
nix profile upgrade '.*'

# Aggiornare un singolo pacchetto (per indice)
nix profile upgrade 0

# Rimuovere un pacchetto
nix profile remove nixpkgs#firefox
# oppure per indice:
nix profile remove 0

# Rollback al profilo precedente
nix profile rollback

# Visualizzare la cronologia delle generazioni
nix profile history

# Differenze tra generazioni
nix profile diff-closures
```

#### Flakes per ambienti di sviluppo

I flakes definiscono ambienti di sviluppo riproducibili in un file `flake.nix` alla radice del progetto. Chiunque cloni il repository ottiene esattamente le stesse versioni degli strumenti.

```nix
# flake.nix — ambiente di sviluppo per un progetto web full-stack
{
  description = "Ambiente dev per progetto web";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.nodejs_22
            pkgs.pnpm
            pkgs.python312
            pkgs.postgresql_16
            pkgs.redis
            pkgs.docker-compose
            pkgs.jq
            pkgs.httpie
          ];

          shellHook = ''
            echo "Ambiente di sviluppo attivo"
            echo "Node: $(node --version)"
            echo "Python: $(python3 --version)"
            export DATABASE_URL="postgresql://localhost:5432/dev"
          '';
        };
      }
    );
}
```

```bash
# Entrare nell'ambiente (scarica e configura tutto automaticamente)
nix develop
# Equivalente di: attivare un virtualenv + nvm use + installare tool

# Entrare senza clonare il repository (da un flake remoto)
nix develop github:org/progetto

# Eseguire un singolo comando nell'ambiente
nix develop --command bash -c "node --version && python3 --version"

# nix run: eseguire un programma senza installarlo permanentemente
nix run nixpkgs#cowsay -- "Test rapido"
nix run nixpkgs#python312 -- -c "print('ciao')"

# nix shell: shell temporanea con pacchetti specifici (senza flake.nix)
nix shell nixpkgs#nodejs_22 nixpkgs#pnpm
# I pacchetti sono disponibili solo in questa sessione
```

#### direnv + Nix: attivazione automatica

Con `direnv` e `nix-direnv`, l'ambiente di sviluppo si attiva automaticamente quando si entra nella directory del progetto.

```bash
# Installare direnv e nix-direnv
nix profile install nixpkgs#direnv nixpkgs#nix-direnv

# Aggiungere al .bashrc / .zshrc
eval "$(direnv hook bash)"   # oppure: eval "$(direnv hook zsh)"

# Nel progetto, creare .envrc
echo "use flake" > .envrc
direnv allow

# Ora: cd nel progetto → ambiente Nix attivato automaticamente
# cd fuori → ambiente disattivato
# Nessun "nix develop" manuale necessario
```

#### Garbage collection e manutenzione

```bash
# Lo store Nix puo crescere significativamente nel tempo
du -sh /nix/store/

# Rimuovere generazioni vecchie (tutte tranne l'ultima)
nix profile wipe-history --older-than 30d

# Garbage collection: rimuove tutto cio che non e referenziato
nix store gc

# Ottimizzazione: deduplicazione via hard links
nix store optimise

# Nix su non-NixOS: aggiornare Nix stesso
nix upgrade-nix

# Aggiornare il flake registry
nix registry pin nixpkgs
```

#### Nix vs container per ambienti di sviluppo

| Aspetto | Nix (nix develop) | Docker (devcontainer) |
|---|---|---|
| Overhead | Nessun layer di virtualizzazione | Layer kernel + rete |
| Velocita avvio | Istantanea (symlink) | Secondi (avvio container) |
| Accesso filesystem | Nativo | Mount bind (lento su macOS) |
| GPU/hardware | Accesso diretto | Richiede configurazione extra |
| Riproducibilita | Hash-based (esatta) | Layer-based (dipende da base image) |
| Isolamento | Solo PATH e variabili | Completo (namespace, cgroups) |
| Curva apprendimento | Alta (linguaggio Nix) | Media (Dockerfile) |
| IDE integration | Nativo (il PATH funziona) | Remote container necessario |

Nix e preferibile per ambienti di sviluppo locali dove si vuole riproducibilita senza il peso della virtualizzazione. I container restano superiori per l'isolamento completo e la simulazione dell'ambiente di produzione.

#### Troubleshooting Nix su non-NixOS

```bash
# Problema: "error: getting status of /nix": No such file or directory
# Il Nix store non e stato creato. Reinstallare con:
sh <(curl -L https://nixos.org/nix/install) --daemon

# Problema: "error: cannot connect to daemon"
sudo systemctl restart nix-daemon

# Problema: build lentissima (compila da sorgente)
# Aggiungere cache binarie in /etc/nix/nix.conf:
# substituters = https://cache.nixos.org https://nix-community.cachix.org
# trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=

# Problema: conflitto con package manager di sistema
# Nix non tocca /usr, /lib, /bin — usa solo /nix/store
# Non c'e conflitto a livello di filesystem
# Ma attenzione: LD_LIBRARY_PATH puo creare confusione
# Nix imposta RPATH nei binari, evitando dipendenza da variabili ambiente

# Problema: lo spazio disco cresce
du -sh /nix/store/ | sort -rh
# Le build Nix accumulano derivazioni nel tempo
# Soluzione: gc periodico
nix store gc --max 10G    # Libera fino a ridurre a 10 GB
```

### GNU Guix

Guix condivide l'architettura funzionale di Nix, ma usa Guile Scheme al posto del linguaggio Nix.

```bash
# Installare Guix su distribuzione esistente
# (seguire la guida ufficiale per lo script di installazione)

# Comandi base
guix install firefox                  # Installa
guix remove firefox                   # Rimuovi
guix upgrade                          # Aggiorna tutti
guix search "web browser"             # Cerca
guix package --list-installed         # Lista installati
guix package --list-generations       # Generazioni
guix package --roll-back              # Rollback

# Ambiente temporaneo
guix shell python gcc-toolchain make
# Crea una shell con questi pacchetti disponibili, senza installazione permanente

# Pulizia
guix gc                               # Garbage collection
```

### Confronto Nix/Guix vs tradizionali

| Aspetto | APT/DNF | Nix/Guix |
|---|---|---|
| Modello | Imperativo (stato mutabile) | Funzionale (immutabile) |
| Conflitti | Possibili | Impossibili per design |
| Rollback | Limitato (dnf history) | Completo (generazioni) |
| Multi-versione | No (una versione per pacchetto) | Si (hash diversi) |
| Riproducibilita | Approssimativa | Esatta (hash-based) |
| Curva di apprendimento | Bassa | Alta |
| Ambienti isolati | No (o virtualenv/containers) | Nativo (nix shell / guix shell) |
| Uso disco | Efficiente (condivisione) | Alto (ma dedup disponibile) |

---

## Compilazione da Sorgente

```bash
# Workflow standard: download → configure → compile → install

# 1. Prerequisiti
sudo apt install build-essential     # gcc, make, libc-dev (Debian/Ubuntu)
sudo dnf group install "Development Tools"  # (Fedora/RHEL)

# 2. Download e estrazione
wget https://example.com/software-1.0.tar.gz
tar xzf software-1.0.tar.gz
cd software-1.0/

# 3. Configurazione
./configure --prefix=/usr/local      # Verifica dipendenze, genera Makefile
# --prefix: dove installare (default /usr/local)
# Se mancano dipendenze: installare i pacchetti -dev corrispondenti

# 4. Compilazione
make -j$(nproc)                      # Compila con tutti i core disponibili

# 5. Installazione
sudo make install                    # Installa in --prefix

# 6. Pulizia
make clean                           # Pulisci file di build

# CHECKINSTALL: crea un .deb/.rpm dalla compilazione
sudo apt install checkinstall
sudo checkinstall                    # Dopo make, al posto di make install
# → Crea un pacchetto .deb/rpm gestibile dal package manager
```

### Gestione software compilato

```bash
# Problemi di "make install" su produzione:
# 1. Nessun tracciamento dei file installati
# 2. Nessun modo pulito di disinstallare
# 3. Potenziali conflitti con pacchetti di sistema

# Soluzione 1: GNU stow (symlink farm manager)
sudo apt install stow
./configure --prefix=/usr/local/stow/software-1.0
make -j$(nproc) && sudo make install
cd /usr/local/stow
sudo stow software-1.0              # Crea symlink in /usr/local/bin/, lib/, ...
sudo stow -D software-1.0           # Rimuovi i symlink (disinstalla pulito)

# Soluzione 2: checkinstall (gia visto sopra)
# Soluzione 3: fpm (vedi sezione Costruzione pacchetti)
```

---

## Gestione Repository e GPG

```bash
# Verificare firme GPG dei pacchetti
# APT verifica automaticamente le firme con le chiavi in /etc/apt/trusted.gpg.d/

# Aggiungere chiave GPG (metodo moderno, Debian/Ubuntu)
curl -fsSL https://example.com/key.gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/example.gpg

# Nel sources.list.d:
# deb [signed-by=/etc/apt/keyrings/example.gpg] https://repo.example.com/apt stable main

# RPM: importare chiave
sudo rpm --import https://example.com/RPM-GPG-KEY
```

### Creare un repository privato APT

**Step-by-step completo per un repository APT privato servito via HTTPS.**

#### Step 1: Preparare la struttura

```bash
# Scegliere la directory base
REPO_BASE="/srv/apt-repo"
sudo mkdir -p ${REPO_BASE}/pool/main
sudo mkdir -p ${REPO_BASE}/dists/stable/main/binary-amd64
```

#### Step 2: Generare la chiave GPG per la firma

```bash
# Generare una chiave GPG dedicata al repository
gpg --full-generate-key
# Tipo: RSA and RSA
# Lunghezza: 4096 bit
# Scadenza: 2 anni (per forzare la rotazione)
# Nome: "Repository Interno <repo@azienda.it>"

# Esportare la chiave pubblica
gpg --export --armor "repo@azienda.it" > ${REPO_BASE}/repo-pubkey.asc

# Esportare per il formato apt moderno
gpg --export "repo@azienda.it" | sudo tee /etc/apt/keyrings/repo-interno.gpg > /dev/null
```

#### Step 3: Popolare con pacchetti

```bash
# Copiare i .deb nella pool
cp mio-software_1.0-1_amd64.deb ${REPO_BASE}/pool/main/

# Generare i metadati
cd ${REPO_BASE}

# Packages: indice dei pacchetti binari
dpkg-scanpackages pool/ > dists/stable/main/binary-amd64/Packages
gzip -k dists/stable/main/binary-amd64/Packages
```

#### Step 4: Creare il file Release e firmarlo

```bash
# Release file
cd ${REPO_BASE}/dists/stable

cat > Release <<EOF
Origin: Repository Interno
Label: repo-interno
Suite: stable
Codename: stable
Architectures: amd64
Components: main
Description: Repository aziendale interno
Date: $(date -Ru)
EOF

# Aggiungere hash dei file Packages
apt-ftparchive release . >> Release

# Firmare il Release
gpg --default-key "repo@azienda.it" -abs -o Release.gpg Release
gpg --default-key "repo@azienda.it" --clearsign -o InRelease Release
```

#### Step 5: Servire via HTTPS

```bash
# Con nginx
sudo tee /etc/nginx/sites-available/apt-repo <<'EOF'
server {
    listen 443 ssl;
    server_name repo.azienda.it;

    ssl_certificate /etc/ssl/certs/repo.azienda.it.crt;
    ssl_certificate_key /etc/ssl/private/repo.azienda.it.key;

    root /srv/apt-repo;
    autoindex on;

    location / {
        try_files $uri $uri/ =404;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/apt-repo /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

#### Step 6: Configurare i client

```bash
# Scaricare e installare la chiave pubblica
curl -fsSL https://repo.azienda.it/repo-pubkey.asc | \
  sudo gpg --dearmor -o /etc/apt/keyrings/repo-interno.gpg

# Aggiungere il repository
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/repo-interno.gpg] https://repo.azienda.it stable main" | \
  sudo tee /etc/apt/sources.list.d/repo-interno.list

sudo apt update
sudo apt install mio-software
```

#### Automazione con reprepro

```bash
# reprepro: gestore di repository APT piu robusto di dpkg-scanpackages
sudo apt install reprepro

# Struttura reprepro
mkdir -p /srv/apt-repo/conf
cat > /srv/apt-repo/conf/distributions <<EOF
Origin: Repository Interno
Label: repo-interno
Codename: stable
Architectures: amd64
Components: main
Description: Repository aziendale
SignWith: repo@azienda.it
EOF

# Aggiungere un pacchetto
reprepro -b /srv/apt-repo includedeb stable mio-software_1.0-1_amd64.deb

# Rimuovere un pacchetto
reprepro -b /srv/apt-repo remove stable mio-software

# Lista pacchetti nel repository
reprepro -b /srv/apt-repo list stable
```

#### Gestione avanzata con Aptly

Aptly e un gestore di repository Debian piu flessibile di reprepro: supporta mirroring di repository remoti, snapshot immutabili, merge tra snapshot, e pubblicazione con firma GPG. Offre anche una REST API per l'integrazione in pipeline CI/CD.

```bash
# Installazione
sudo apt install aptly
# oppure da binario ufficiale:
# wget https://github.com/aptly-dev/aptly/releases/download/v1.5.0/aptly_1.5.0_linux_amd64.tar.gz

# Creare un repository locale
aptly repo create -distribution=stable -component=main repo-interno

# Aggiungere pacchetti
aptly repo add repo-interno /path/to/*.deb

# Lista pacchetti nel repository
aptly repo show -with-packages repo-interno

# Creare uno snapshot (immutabile, perfetto per release)
aptly snapshot create release-1.0 from repo repo-interno

# Pubblicare lo snapshot come repository APT
aptly publish snapshot -distribution=stable release-1.0
# I file vengono generati in ~/.aptly/public/

# MIRRORING: creare un mirror di un repository remoto
aptly mirror create ubuntu-noble \
  http://archive.ubuntu.com/ubuntu noble main restricted
aptly mirror update ubuntu-noble

# Creare uno snapshot dal mirror
aptly snapshot create ubuntu-noble-snap from mirror ubuntu-noble

# MERGE: combinare snapshot da fonti diverse
aptly snapshot merge combined-release release-1.0 ubuntu-noble-snap

# Pubblicare il merge
aptly publish snapshot -distribution=stable combined-release

# AGGIORNAMENTO: aggiornare un repository pubblicato
aptly repo add repo-interno mio-software_1.1-1_amd64.deb
aptly snapshot create release-1.1 from repo repo-interno
aptly publish switch stable release-1.1

# Diff tra snapshot
aptly snapshot diff release-1.0 release-1.1

# API REST (avviare il server)
aptly api serve -listen=:8080
# Endpoint disponibili:
# GET  /api/repos           — lista repository
# POST /api/repos           — crea repository
# POST /api/repos/:name/add — aggiungi pacchetti
# POST /api/publish         — pubblica
```

**Confronto reprepro vs Aptly:**

| Aspetto | reprepro | Aptly |
|---|---|---|
| Snapshot immutabili | No | Si |
| Mirroring repository | No | Si |
| Merge tra repository | No | Si |
| REST API | No | Si |
| Complessita | Bassa | Media |
| Multi-distribuzione | Si (nativo) | Si |
| Database | Berkeley DB | LevelDB |
| Ideale per | Repository semplici | CI/CD, infrastruttura complessa |

**Workflow CI/CD con Aptly:**

Un pattern comune in ambienti enterprise e integrare Aptly nella pipeline CI/CD per pubblicare automaticamente i pacchetti costruiti:

```bash
# Pipeline: build .deb → test → push al repository Aptly → snapshot → publish

# 1. Il sistema CI costruisce il pacchetto
dpkg-buildpackage -us -uc -b

# 2. Upload al repository Aptly via REST API
curl -X POST http://aptly.interno:8080/api/files/upload \
  -F "file=@../mio-software_1.1-1_amd64.deb"

curl -X POST http://aptly.interno:8080/api/repos/repo-interno/file/upload

# 3. Creare snapshot datato per tracciabilita
curl -X POST http://aptly.interno:8080/api/snapshots \
  -H 'Content-Type: application/json' \
  -d "{\"Name\": \"release-$(date +%Y%m%d-%H%M%S)\", \"SourceKind\": \"local\", \"SourceName\": \"repo-interno\"}"

# 4. Pubblicare (o aggiornare la pubblicazione esistente)
curl -X PUT http://aptly.interno:8080/api/publish/repo-interno/stable \
  -H 'Content-Type: application/json' \
  -d '{"Snapshots": [{"Component": "main", "Name": "release-20260524-143000"}]}'

# Lo snapshot permette rollback istantaneo: basta ripubblicare
# uno snapshot precedente senza modificare i pacchetti fisici
```

#### Mirror con apt-mirror

```bash
# Creare un mirror locale di un repository ufficiale
sudo apt install apt-mirror

# /etc/apt/mirror.list
# set base_path /srv/apt-mirror
# deb http://archive.ubuntu.com/ubuntu noble main restricted universe
# clean http://archive.ubuntu.com/ubuntu

sudo apt-mirror                      # Avvia il download (puo richiedere ore)
# Poi servire /srv/apt-mirror/mirror/ via nginx
```

### Creare un repository privato RPM

```bash
# Prerequisiti
sudo dnf install createrepo_c httpd

# Struttura
sudo mkdir -p /srv/rpm-repo/el9/x86_64/Packages

# Copiare i .rpm
sudo cp mio-software-1.2.3-1.el9.x86_64.rpm /srv/rpm-repo/el9/x86_64/Packages/

# Generare i metadati del repository
sudo createrepo_c /srv/rpm-repo/el9/x86_64/
# Crea la directory repodata/ con i file XML di metadati

# Aggiornare dopo aver aggiunto nuovi pacchetti
sudo createrepo_c --update /srv/rpm-repo/el9/x86_64/

# Firmare i metadati
gpg --detach-sign --armor /srv/rpm-repo/el9/x86_64/repodata/repomd.xml

# Servire via Apache
sudo tee /etc/httpd/conf.d/rpm-repo.conf <<'EOF'
<VirtualHost *:443>
    ServerName repo.azienda.it
    DocumentRoot /srv/rpm-repo
    <Directory /srv/rpm-repo>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/repo.azienda.it.crt
    SSLCertificateKeyFile /etc/ssl/private/repo.azienda.it.key
</VirtualHost>
EOF

sudo systemctl reload httpd
```

Configurazione client:

```bash
# /etc/yum.repos.d/interno.repo
sudo tee /etc/yum.repos.d/interno.repo <<'EOF'
[interno]
name=Repository Aziendale
baseurl=https://repo.azienda.it/el9/$basearch/
enabled=1
gpgcheck=1
gpgkey=https://repo.azienda.it/RPM-GPG-KEY-interno
EOF

sudo dnf update
sudo dnf install mio-software
```

### Firma GPG dei pacchetti

```bash
# Firmare un pacchetto .deb
dpkg-sig --sign builder mio-software_1.0-1_amd64.deb

# Verificare la firma
dpkg-sig --verify mio-software_1.0-1_amd64.deb

# Firmare un pacchetto .rpm
rpm --addsign mio-software-1.2.3-1.el9.x86_64.rpm
# Richiede la configurazione in ~/.rpmmacros:
# %_gpg_name repo@azienda.it
# %_gpg_sign_cmd_extra_args --pinentry-mode loopback

# Verificare la firma
rpm --checksig mio-software-1.2.3-1.el9.x86_64.rpm

# Best practices GPG per repository:
# 1. Chiave dedicata (mai la chiave personale)
# 2. Scadenza impostata (2 anni max)
# 3. Chiave privata su macchina di build isolata
# 4. Rotazione programmata con overlap (nuova chiave valida prima della scadenza)
# 5. Backup sicuro della chiave in offline storage
```

---

## Risoluzione dipendenze

### Come funziona il solver APT

APT utilizza un solver SAT (satisfiability) per risolvere le dipendenze. Il processo:

1. **Lettura delle richieste**: l'utente chiede di installare/rimuovere pacchetti.
2. **Costruzione del grafo**: APT costruisce un grafo di tutte le dipendenze, conflitti e versioni disponibili.
3. **Risoluzione**: il solver cerca una soluzione che soddisfi tutti i vincoli contemporaneamente.
4. **Ottimizzazione**: tra le soluzioni valide, preferisce quella con meno modifiche.

```bash
# Visualizzare il processo di risoluzione
apt install -s nginx                  # Simulazione: mostra cosa farebbe
apt install -o Debug::pkgProblemResolver=true nginx 2>&1 | less

# Dipendenze di un pacchetto
apt depends nginx
apt rdepends nginx                    # Chi dipende da nginx

# Conflitti e alternative
apt-cache show nginx | grep -E '^(Depends|Conflicts|Provides|Replaces):'
```

### Pacchetti virtuali

Un pacchetto virtuale non esiste come .deb ma e un "contratto" che piu pacchetti possono soddisfare.

```bash
# Esempio: "mail-transport-agent" e un pacchetto virtuale
apt-cache showvirtualpkg mail-transport-agent
# Fornito da: postfix, exim4, sendmail, ...

# Se un pacchetto dipende da "mail-transport-agent",
# qualsiasi MTA soddisfa la dipendenza.

# Alternatives system: gestione di implementazioni multiple
update-alternatives --list editor
sudo update-alternatives --config editor
# Sceglie quale programma risponde a /usr/bin/editor
```

### Come funziona il solver DNF

DNF usa `libsolv` (dalla tradizione openSUSE), un solver SAT ottimizzato.

```bash
# Debug della risoluzione
dnf install --best --allowerasing nginx 2>&1 | less
# --best: fallisci se la versione migliore non e installabile
# --allowerasing: consenti di rimuovere pacchetti in conflitto

# Dipendenze ad albero
dnf repoquery --requires --resolve nginx
dnf repoquery --whatrequires nginx    # Chi dipende da nginx

# Conflitti
dnf repoquery --conflicts nginx

# Provides: cosa fornisce un pacchetto
dnf repoquery --provides nginx

# Risolvere conflitti manualmente
sudo dnf remove pacchetto-in-conflitto
sudo dnf install --allowerasing nginx
```

### Relazioni tra pacchetti

| Relazione | Significato (Debian) | Significato (RPM) |
|---|---|---|
| Depends / Requires | Obbligatorio per funzionare | Obbligatorio |
| Pre-Depends / — | Deve essere configurato prima dell'unpack | — |
| Recommends / Weak | Fortemente consigliato | Dipendenza debole |
| Suggests / Supplements | Opzionale, migliora l'esperienza | Complementare |
| Conflicts / Conflicts | Non puo coesistere | Non puo coesistere |
| Breaks / — | Rompe un altro pacchetto | — |
| Replaces / Obsoletes | Sovrascrive file / sostituisce | Sostituisce |
| Provides / Provides | Fornisce un virtuale | Fornisce una capability |

---

## Gestione pacchetti kernel

Il kernel e il pacchetto piu critico del sistema. Errori nella gestione del kernel possono rendere il sistema non avviabile.

### Debian/Ubuntu

```bash
# Kernel installati
dpkg -l | grep linux-image

# Kernel attualmente in uso
uname -r

# Installare un kernel specifico
sudo apt install linux-image-6.8.0-45-generic linux-headers-6.8.0-45-generic

# Rimuovere vecchi kernel (mai rimuovere quello in uso!)
sudo apt remove linux-image-6.5.0-35-generic
sudo apt autoremove --purge          # Rimuove anche headers e moduli orfani

# Bloccare il kernel attuale (impedire aggiornamenti automatici)
sudo apt-mark hold linux-image-$(uname -r) linux-headers-$(uname -r)
sudo apt-mark hold linux-image-generic linux-headers-generic

# Sbloccare
sudo apt-mark unhold linux-image-generic linux-headers-generic

# Aggiornare GRUB dopo modifiche al kernel
sudo update-grub

# Mantenere solo gli ultimi N kernel (cleanup automatico)
# In /etc/apt/apt.conf.d/50unattended-upgrades:
# Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
```

### Fedora/RHEL

```bash
# Kernel installati
rpm -qa kernel-core

# Configurare quanti kernel mantenere
# In /etc/dnf/dnf.conf:
# installonly_limit=3

# Installare un kernel specifico
sudo dnf install kernel-core-6.8.5-301.fc40

# Rimuovere vecchi kernel
sudo dnf remove $(dnf repoquery --installonly --latest-limit=-2)

# Impostare il kernel di default
sudo grubby --default-kernel
sudo grubby --set-default /boot/vmlinuz-6.8.5-301.fc40.x86_64

# Parametri kernel
sudo grubby --update-kernel=ALL --args="quiet splash"
sudo grubby --info=ALL
```

### Procedura sicura di aggiornamento kernel

```
1. Verificare il kernel attuale: uname -r
2. Installare il nuovo kernel (senza rimuovere il vecchio)
3. Aggiornare GRUB / grubby
4. Riavviare
5. Verificare che il nuovo kernel funzioni correttamente
6. Solo DOPO il test: rimuovere il kernel vecchio
7. Mantenere sempre almeno 2 kernel installati come fallback
```

---

## Aggiornamenti automatici (Unattended Upgrades)

### Debian/Ubuntu: unattended-upgrades

```bash
# Installazione
sudo apt install unattended-upgrades apt-listchanges

# Abilitare
sudo dpkg-reconfigure -plow unattended-upgrades
```

Configurazione principale: `/etc/apt/apt.conf.d/50unattended-upgrades`

```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    // "${distro_id}:${distro_codename}-updates";  // Decommentare per tutti gli update
    // "${distro_id}ESMApps:${distro_codename}-apps-security";
};

// Pacchetti da NON aggiornare mai automaticamente
Unattended-Upgrade::Package-Blacklist {
    "linux-image*";       // Kernel: aggiornare manualmente
    "linux-headers*";
    "postgresql*";        // Database: aggiornare con piano
    "mysql*";
    "docker*";
};

// Riavvio automatico se necessario (ATTENZIONE in produzione)
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";

// Rimuovere dipendenze non necessarie
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";

// Notifica email
Unattended-Upgrade::Mail "admin@azienda.it";
Unattended-Upgrade::MailReport "on-change";

// Dimensione massima download
// Unattended-Upgrade::Download-Limit "70";
```

Schedulazione: `/etc/apt/apt.conf.d/20auto-upgrades`

```
APT::Periodic::Update-Package-Lists "1";          // apt update ogni giorno
APT::Periodic::Unattended-Upgrade "1";             // upgrade ogni giorno
APT::Periodic::Download-Upgradeable-Packages "1";  // pre-download
APT::Periodic::AutocleanInterval "7";              // pulizia cache settimanale
```

```bash
# Test manuale (dry-run)
sudo unattended-upgrade --dry-run --debug

# Esecuzione manuale
sudo unattended-upgrade -v

# Log
cat /var/log/unattended-upgrades/unattended-upgrades.log
cat /var/log/unattended-upgrades/unattended-upgrades-dpkg.log
```

### Fedora/RHEL: dnf-automatic

```bash
# Installazione
sudo dnf install dnf-automatic

# Configurazione: /etc/dnf/automatic.conf
sudo tee /etc/dnf/automatic.conf <<'EOF'
[commands]
# Cosa fare: download_only, download_and_apply
apply_updates = yes
# Tipo di aggiornamenti: default, security
upgrade_type = security

[emitters]
# Notifica via email
emit_via = email

[email]
email_from = dnf-auto@azienda.it
email_to = admin@azienda.it
email_host = smtp.azienda.it

[base]
debuglevel = 1
EOF

# Abilitare il timer
sudo systemctl enable --now dnf-automatic.timer

# Verificare lo stato
systemctl status dnf-automatic.timer
systemctl list-timers dnf-automatic*
```

---

## Sicurezza pacchetti

### Catena di fiducia GPG

```
Repository owner → GPG private key → firma i metadati Release/repomd.xml
                                                    ↓
Client → GPG public key in /etc/apt/keyrings/ → verifica firma
                                                    ↓
                                            se valida → accetta i pacchetti
                                            se invalida → RIFIUTA
```

```bash
# APT: verificare le chiavi installate
apt-key list                          # Legacy (deprecato)
ls /etc/apt/keyrings/                 # Metodo moderno
ls /etc/apt/trusted.gpg.d/           # Chiavi system-wide

# APT: verificare che un pacchetto sia autenticato
apt download nginx
dpkg-sig --verify nginx_*.deb 2>/dev/null || echo "Nessuna firma dpkg-sig"

# RPM: verificare le chiavi importate
rpm -qa gpg-pubkey*
rpm -qi gpg-pubkey-XXXXXXXX          # Dettagli di una chiave specifica
```

### Scansione vulnerabilita

```bash
# Debian/Ubuntu: debsecan
sudo apt install debsecan
debsecan                              # Mostra CVE che riguardano il sistema
debsecan --only-fixed                 # Solo quelli con fix disponibile
debsecan --suite bookworm --format detail

# Ubuntu: ubuntu-security-status
ubuntu-security-status                # Mostra lo stato ESM/security
ubuntu-security-status --thirdparty   # Include repository terzi

# Fedora/RHEL: dnf updateinfo
dnf updateinfo list security          # CVE con fix disponibile
dnf updateinfo info CESA-2026:1234    # Dettagli di un advisory
sudo dnf update --security            # Installa solo security updates

# Multi-distro: trivy
# Scansione vulnerabilita su pacchetti installati
trivy rootfs /
trivy image ubuntu:24.04              # Scansione di un'immagine container
```

### CVE tracking e policy

```bash
# Feed CVE per distribuzione:
# Debian: https://security-tracker.debian.org/tracker/
# Ubuntu: https://ubuntu.com/security/cves
# Red Hat: https://access.redhat.com/security/cve/
# NIST NVD: https://nvd.nist.gov/

# Automatizzare il monitoraggio:
# 1. Integrare debsecan/dnf updateinfo nei cron job
# 2. Notifica se ci sono CVE con CVSS >= 7.0
# 3. SLA: Critical (CVSS >= 9.0) → patch entro 24h
#         High (CVSS >= 7.0) → patch entro 7 giorni
#         Medium → patch entro 30 giorni

# Esempio cron per alert security
# /etc/cron.daily/security-check
#!/bin/bash
FIXES=$(debsecan --only-fixed 2>/dev/null | wc -l)
if [ "$FIXES" -gt 0 ]; then
    debsecan --only-fixed | \
    mail -s "[SECURITY] ${FIXES} pacchetti con fix disponibile su $(hostname)" admin@azienda.it
fi
```

### Sigstore, SLSA e supply chain moderna

La sicurezza tradizionale dei pacchetti Linux si basa su chiavi GPG a lunga durata: il maintainer firma i pacchetti con la propria chiave privata, i client verificano con la chiave pubblica. Questo modello presenta debolezze strutturali: le chiavi a lunga durata possono essere compromesse, la rotazione e complessa, e non esiste un log pubblico di trasparenza.

**Sigstore** (progetto della Linux Foundation / OpenSSF) introduce un paradigma diverso: **firma keyless** con certificati effimeri legati a identita OIDC.

#### Componenti Sigstore

| Componente | Funzione |
|---|---|
| **Cosign** | Tool CLI per firmare e verificare artefatti (container, blob, pacchetti) |
| **Fulcio** | Certificate Authority che emette certificati X.509 a breve durata (10 minuti) legati a un token OIDC |
| **Rekor** | Log di trasparenza append-only: ogni firma e registrata pubblicamente e immutabile |
| **Gitsign** | Firma dei commit Git con identita Sigstore (alternativa a GPG per git) |

```bash
# Firmare un artefatto con cosign (keyless, tramite OIDC)
cosign sign-blob --yes mio-software_1.0-1_amd64.deb \
  --bundle mio-software.bundle
# Si apre il browser per l'autenticazione OIDC (GitHub, Google, Microsoft)
# Il certificato effimero viene emesso da Fulcio
# La firma viene registrata in Rekor

# Verificare la firma
cosign verify-blob mio-software_1.0-1_amd64.deb \
  --bundle mio-software.bundle \
  --certificate-identity=dev@azienda.it \
  --certificate-oidc-issuer=https://accounts.google.com

# Firmare un'immagine container
cosign sign ghcr.io/org/app:v1.0

# Verificare un'immagine container
cosign verify ghcr.io/org/app:v1.0 \
  --certificate-identity-regexp='.*@azienda\.it' \
  --certificate-oidc-issuer=https://accounts.google.com

# Firmare in CI/CD (GitHub Actions, senza interazione browser)
# Il token OIDC viene fornito automaticamente dal runner
cosign sign-blob --yes artefatto.tar.gz \
  --bundle artefatto.bundle \
  --oidc-issuer=https://token.actions.githubusercontent.com
```

#### SLSA (Supply-chain Levels for Software Artifacts)

SLSA (pronunciato "salsa") e un framework di sicurezza della supply chain che definisce livelli progressivi di garanzia:

| Livello | Requisiti | Significato |
|---|---|---|
| SLSA 1 | Il processo di build e documentato | Provenienza base |
| SLSA 2 | Build service ospitato, provenienza firmata | Provenienza autenticata |
| SLSA 3 | Build isolato, provenienza non falsificabile | Garanzia robusta |
| SLSA 4 | Dipendenze verificate, build ermetico | Massima assicurazione |

```bash
# Generare attestazione SLSA con slsa-verifier (GitHub Actions)
# L'attestazione certifica: CHI ha costruito, COSA e stato costruito,
# COME e stato costruito (parametri, dipendenze, commit)

# Verificare un artefatto con provenienza SLSA
slsa-verifier verify-artifact mio-software_1.0.tar.gz \
  --provenance-path mio-software.intoto.jsonl \
  --source-uri github.com/org/mio-software \
  --source-tag v1.0
```

#### in-toto: attestazioni nella supply chain

in-toto definisce un formato standard per le attestazioni: dichiarazioni firmate su un artefatto che documentano ogni passo della supply chain (build, test, scansione, firma).

```bash
# Struttura di un'attestazione in-toto
# {
#   "_type": "https://in-toto.io/Statement/v1",
#   "subject": [{"name": "mio-software_1.0.deb", "digest": {"sha256": "abc..."}}],
#   "predicateType": "https://slsa.dev/provenance/v1",
#   "predicate": {
#     "buildDefinition": { ... },
#     "runDetails": { ... }
#   }
# }

# Cosign supporta nativamente le attestazioni in-toto
cosign attest --predicate provenance.json \
  --type slsaprovenance \
  ghcr.io/org/app:v1.0

# Verificare l'attestazione
cosign verify-attestation ghcr.io/org/app:v1.0 \
  --type slsaprovenance \
  --certificate-identity-regexp='.*@azienda\.it' \
  --certificate-oidc-issuer=https://accounts.google.com
```

#### Integrazione con APT e RPM

I package manager tradizionali non supportano nativamente Sigstore, ma l'integrazione e in evoluzione:

| Ecosistema | Stato Sigstore (2025) |
|---|---|
| Container (Docker, Podman) | Pieno supporto nativo via cosign |
| Python (PyPI) | Supporto nativo, PEP 740 |
| npm | Supporto provenance SLSA |
| Homebrew | Firma Sigstore attiva |
| Rust (crates.io) | In sviluppo |
| APT/Debian | GPG tradizionale, nessun piano Sigstore ufficiale |
| RPM/Fedora | GPG tradizionale, discussioni in corso |

Per ambienti che necessitano di Sigstore con pacchetti .deb/.rpm, la strategia raccomandata e distribuire tramite artefatti OCI (vedi sezione dedicata) e verificare con cosign, oppure aggiungere attestazioni SLSA alla pipeline CI/CD senza sostituire la firma GPG nativa.

```bash
# Workflow ibrido: GPG + Sigstore per massima copertura
# 1. Firma GPG tradizionale (compatibilita APT/DNF)
dpkg-sig --sign builder mio-software_1.0-1_amd64.deb

# 2. Firma Sigstore (supply chain moderna)
cosign sign-blob --yes mio-software_1.0-1_amd64.deb \
  --bundle mio-software.sigstore.bundle

# 3. Attestazione SLSA di provenienza
cosign attest-blob --yes mio-software_1.0-1_amd64.deb \
  --predicate provenance.json \
  --type slsaprovenance \
  --bundle mio-software.provenance.bundle

# I client possono verificare entrambi i livelli
```

#### SBOM (Software Bill of Materials)

Un SBOM e l'elenco completo dei componenti software inclusi in un pacchetto o artefatto. Nel contesto della supply chain, l'SBOM documenta esattamente cosa contiene un pacchetto, permettendo il tracciamento delle vulnerabilita a livello di componente.

```bash
# Generare un SBOM da un pacchetto .deb con syft
syft packages mio-software_1.0-1_amd64.deb -o spdx-json > sbom.spdx.json
syft packages mio-software_1.0-1_amd64.deb -o cyclonedx-json > sbom.cdx.json

# Generare un SBOM dall'intero sistema installato
syft packages dir:/ -o spdx-json > sistema-sbom.spdx.json

# Generare un SBOM da un'immagine container
syft packages ubuntu:24.04 -o spdx-json > ubuntu-sbom.spdx.json

# Scansionare un SBOM per vulnerabilita con grype
grype sbom:sbom.spdx.json
# Output: lista di CVE con severita, pacchetto affetto, versione fixata

# Formati SBOM standard:
# SPDX (ISO/IEC 5962:2021): formato ISO, supportato da Linux Foundation
# CycloneDX (OWASP): focalizzato sulla sicurezza, piu compatto
# Entrambi supportano JSON e XML
```

**Requisiti normativi:** L'Executive Order 14028 (USA, 2021) e il Cyber Resilience Act (UE, 2024) richiedono SBOM per il software venduto a enti governativi e per prodotti digitali nell'UE. La generazione di SBOM sta diventando un requisito standard nella supply chain del software.

---

## Gestione pacchetti nei container

### Alpine apk

Alpine Linux usa `apk` (Alpine Package Keeper) ed e la scelta prevalente per container Docker per la dimensione minima (~5 MB base image).

```bash
# Comandi base
apk update                           # Aggiorna indice
apk add nginx                        # Installa
apk del nginx                        # Rimuove
apk search nginx                     # Cerca
apk info nginx                       # Info

# Flag per Dockerfile (best practice)
apk add --no-cache nginx             # Non salvare la cache (risparmio spazio)
apk add --virtual .build-deps gcc make libc-dev   # Gruppo virtuale di build
apk del .build-deps                  # Rimuovi tutto il gruppo in un colpo

# Fix: repository non disponibile
apk add --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing nomepkg
```

Best practice per Dockerfile:

```dockerfile
# Pattern multi-stage per build dependencies
FROM alpine:3.20 AS builder
RUN apk add --no-cache gcc make musl-dev
COPY . /src
RUN cd /src && make

FROM alpine:3.20
# Solo runtime dependencies, nessun compilatore
RUN apk add --no-cache libgcc
COPY --from=builder /src/bin/app /usr/local/bin/
CMD ["/usr/local/bin/app"]
```

### Immagini distroless

Le immagini distroless (Google) non contengono alcun package manager, shell, o utility. Contengono solo l'applicazione e le sue librerie runtime.

```dockerfile
# Build stage con strumenti completi
FROM golang:1.22 AS builder
COPY . /app
WORKDIR /app
RUN CGO_ENABLED=0 go build -o /server .

# Runtime: nessun package manager, nessuna shell
FROM gcr.io/distroless/static-debian12
COPY --from=builder /server /server
CMD ["/server"]
```

Vantaggi distroless:
- Superficie di attacco minima (nessun tool da sfruttare)
- Dimensione ridotta
- Conformita a compliance (meno software = meno CVE)

Svantaggi:
- Debugging difficile (nessuna shell per `exec -it`)
- Nessun modo di installare tool a runtime

### Confronto package manager per container

| PM | Base image | Uso tipico |
|---|---|---|
| `apk` (Alpine) | ~5 MB | Container leggeri, microservizi |
| `apt` (Debian slim) | ~75 MB | Compatibilita massima, librerie C |
| `dnf` (UBI minimal) | ~100 MB | Ambienti Red Hat / OpenShift |
| `microdnf` (UBI micro) | ~35 MB | Red Hat minimale |
| Nessuno (distroless) | ~2-20 MB | Produzione, supply chain sicura |

---

## Artefatti OCI per distribuzione non-container

### Il concetto di OCI Artifact

La specifica OCI (Open Container Initiative) definisce un formato standard per le immagini container, ma lo stesso formato puo trasportare qualsiasi tipo di artefatto: chart Helm, moduli WASM, SBOM, pesi di modelli ML, policy bundle, firme crittografiche e persino pacchetti software tradizionali. Un **artefatto OCI** e un blob con un `mediaType` arbitrario, memorizzato in un registry OCI standard (Docker Hub, GitHub Container Registry, Harbor, Zot, ecc.).

Questo approccio unifica la distribuzione: lo stesso registry che ospita le immagini container serve anche gli artefatti di supporto, eliminando la necessita di infrastrutture di distribuzione separate.

### ORAS — OCI Registry As Storage

ORAS e lo strumento di riferimento per interagire con artefatti OCI non-container. Supporta push, pull, attach e discover su qualsiasi registry conforme alla specifica OCI Distribution.

```bash
# Installazione di ORAS
# Linux amd64
curl -LO https://github.com/oras-project/oras/releases/download/v1.2.2/oras_1.2.2_linux_amd64.tar.gz
tar xzf oras_1.2.2_linux_amd64.tar.gz
sudo mv oras /usr/local/bin/

# Push di un artefatto arbitrario (es. un pacchetto .deb)
oras push ghcr.io/org/mio-software:1.0 \
  --artifact-type application/vnd.deb.package \
  mio-software_1.0-1_amd64.deb:application/vnd.debian.binary-package

# Pull dell'artefatto
oras pull ghcr.io/org/mio-software:1.0

# Push di piu file con manifest personalizzato
oras push ghcr.io/org/deploy-bundle:v2 \
  --artifact-type application/vnd.deploy.bundle \
  config.yaml:application/yaml \
  policy.rego:application/vnd.opa.policy \
  checksums.sha256:text/plain

# Attach: allegare un SBOM o una firma a un'immagine esistente
oras attach ghcr.io/org/app:v1.0 \
  --artifact-type application/spdx+json \
  sbom.spdx.json:application/spdx+json

# Discover: trovare gli artefatti allegati
oras discover ghcr.io/org/app:v1.0

# Autenticazione (stessa logica di docker login)
oras login ghcr.io -u utente -p token
```

### Casi d'uso concreti

| Artefatto | mediaType | Vantaggio |
|---|---|---|
| Pacchetti .deb/.rpm | `application/vnd.deb.package` | Distribuzione centralizzata senza repo APT/DNF separato |
| Chart Helm | `application/vnd.cncf.helm.chart.content.v1.tar+gzip` | Helm 3 supporta nativamente OCI |
| Policy OPA/Gatekeeper | `application/vnd.opa.policy` | Versioning e distribuzione uniforme |
| SBOM (SPDX/CycloneDX) | `application/spdx+json` | Allegato direttamente all'immagine che descrive |
| Firma Cosign/Sigstore | `application/vnd.dev.cosign.simplesigning.v1+json` | Verifica integrita senza infrastruttura aggiuntiva |
| Moduli WASM | `application/vnd.wasm.content.layer.v1+wasm` | Distribuzione edge/serverless |
| Modelli ML | `application/vnd.ml.model` | Versionamento pesi e checkpoint |

### Confronto con repository tradizionali

| Aspetto | Repo APT/DNF | Registry OCI + ORAS |
|---|---|---|
| Infrastruttura | Server dedicato + createrepo/reprepro | Qualsiasi registry OCI |
| Autenticazione | GPG + HTTPS | Token OAuth / OIDC |
| Firma | GPG manuale | Cosign / Sigstore nativo |
| Multi-artefatto | Solo pacchetti | Qualsiasi tipo di file |
| Deduplicazione | No | Si (content-addressable storage) |
| Garbage collection | Manuale | Nativa nel registry |
| SBOM allegato | Separato | Attach nativo (`oras attach`) |

### Integrare OCI nella pipeline CI/CD

```bash
# Esempio: build di un .deb → push come artefatto OCI → attach SBOM

# 1. Build del pacchetto
dpkg-buildpackage -us -uc -b

# 2. Generare SBOM con syft
syft packages ../mio-software_1.0-1_amd64.deb -o spdx-json > sbom.spdx.json

# 3. Push come artefatto OCI
oras push ghcr.io/org/mio-software:1.0-deb \
  --artifact-type application/vnd.deb.package \
  ../mio-software_1.0-1_amd64.deb:application/vnd.debian.binary-package

# 4. Allegare SBOM
oras attach ghcr.io/org/mio-software:1.0-deb \
  --artifact-type application/spdx+json \
  sbom.spdx.json:application/spdx+json

# 5. Firmare con cosign
cosign sign ghcr.io/org/mio-software:1.0-deb

# 6. Sui client: pull e verifica
oras pull ghcr.io/org/mio-software:1.0-deb
cosign verify ghcr.io/org/mio-software:1.0-deb \
  --certificate-identity=ci@org.com \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com

sudo dpkg -i mio-software_1.0-1_amd64.deb
```

> **Quando preferire OCI a un repository tradizionale:** quando l'organizzazione gestisce gia un registry OCI (Harbor, GHCR, ECR), quando si distribuiscono artefatti eterogenei (pacchetti + chart + policy), quando si vuole Sigstore nativo senza infrastruttura GPG separata. Per ambienti puramente Debian/RHEL con centinaia di pacchetti, un repository APT/DNF tradizionale resta piu efficiente per la risoluzione delle dipendenze.

### Registry OCI self-hosted

Per ambienti che necessitano di un registry OCI privato, le opzioni principali sono:

```bash
# Zot: registry OCI minimalista, conforme alla specifica OCI Distribution
# Supporta nativamente artefatti non-container
docker run -p 5000:5000 ghcr.io/project-zot/zot-linux-amd64:latest

# Harbor: registry enterprise con RBAC, scansione vulnerabilita, replica
# Supporta artefatti OCI, firma cosign, policy OPA
# Installazione via Helm:
helm install harbor harbor/harbor --set expose.type=nodePort

# Distribution (ex Docker Registry): registry minimale
# Manca il supporto nativo per artefatti non-container
# Preferire Zot o Harbor per casi d'uso con ORAS

# Push verso un registry self-hosted
oras push localhost:5000/mio-artefatto:v1 \
  --artifact-type application/vnd.custom.type \
  file.tar.gz:application/gzip

# Configurare autenticazione
oras login localhost:5000 -u admin -p password
```

**Garbage collection degli artefatti OCI:**

```bash
# I registry OCI accumulano blob non referenziati nel tempo
# Harbor: garbage collection via UI o API
curl -X POST https://harbor.azienda.it/api/v2.0/system/gc/schedule \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)" \
  -H "Content-Type: application/json" \
  -d '{"schedule": {"type": "Manual"}}'

# Zot: garbage collection automatica configurabile
# In config.json:
# "storage": { "gc": true, "gcDelay": "1h", "gcInterval": "24h" }

# Policy di retention: mantenere solo le ultime N versioni
# Harbor supporta tag retention policy native
# Zot: retention configurabile per repository
```

---

## Best Practices

1. **Aggiornare regolarmente**: `apt update && apt upgrade` almeno settimanalmente su server di produzione. Automatizzare con unattended-upgrades (security only)
2. **Non mischiare package manager**: su un sistema, usare il package manager nativo. Non installare con apt E snap lo stesso software
3. **Evitare `make install` su produzione**: usare checkinstall per creare un pacchetto gestibile, o meglio: usare il pacchetto della distribuzione
4. **Pin le versioni critiche**: per software critico (database, runtime), bloccare la versione e aggiornare consapevolmente
5. **Verificare le fonti**: aggiungere solo repository fidati. Verificare le chiavi GPG. Mai `apt-key add` con pipe da curl senza verifica
6. **Pulizia periodica**: `apt autoremove`, `apt clean`, rimuovere PPA non usati
7. **Documentare le modifiche**: registrare ogni pacchetto installato manualmente (non come dipendenza) per riproducibilita
8. **Separare le responsabilita**: pacchetti nativi per il sistema base, container per applicazioni, Flatpak/Snap per desktop
9. **Testare gli aggiornamenti**: in ambiente staging prima di produzione, specialmente per kernel e librerie critiche
10. **Monitorare le CVE**: integrare debsecan o `dnf updateinfo` nel flusso di lavoro di sicurezza
11. **Repository privati**: per software interno, creare un repository privato firmato con GPG. Mai distribuire .deb/.rpm via scp o condivisione file
12. **Backup prima di upgrade**: snapshot del disco o backup completo prima di dist-upgrade / major version bump

---

## Troubleshooting

### 1. "Dipendenze rotte (unmet dependencies)"

```bash
# Approccio graduale:
sudo apt install -f                   # Tentativo automatico di fix
sudo dpkg --configure -a              # Configura pacchetti semi-installati
sudo apt update && sudo apt upgrade   # Aggiorna tutto
sudo apt --fix-broken install         # Fix piu aggressivo

# Se persiste: identificare il pacchetto problematico
dpkg -l | grep -E '^..[^i]'          # Pacchetti in stato anomalo
sudo dpkg --remove --force-remove-reinstreq pacchetto-rotto
sudo apt install -f
```

### 2. "E: Could not get lock /var/lib/dpkg/lock"

```bash
# Un altro processo apt/dpkg e in esecuzione
ps aux | grep -E 'apt|dpkg'

# Se nessun processo legittimo:
sudo rm /var/lib/dpkg/lock-frontend
sudo rm /var/lib/dpkg/lock
sudo rm /var/cache/apt/archives/lock
sudo dpkg --configure -a

# MAI rimuovere i lock se un processo e ancora in esecuzione!
# Attendere il completamento o terminarlo con:
sudo kill <PID>
```

### 3. "Package has no installation candidate"

```bash
# Cause possibili:
# 1. Nome errato del pacchetto
apt-cache search parola-chiave        # Cercare il nome corretto

# 2. Repository non abilitato
grep -r "universe\|multiverse" /etc/apt/sources.list*
sudo add-apt-repository universe
sudo apt update

# 3. Architettura sbagliata
dpkg --print-architecture             # La propria architettura
apt-cache show pacchetto | grep Architecture

# 4. Pacchetto rimosso dalla distribuzione
# Cercare nei backports o in un PPA
```

### 4. "GPG error: NO_PUBKEY"

```bash
# Metodo moderno (raccomandato)
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://url-della-chiave/key.gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/nome-repo.gpg

# Aggiornare sources.list con signed-by
# deb [signed-by=/etc/apt/keyrings/nome-repo.gpg] https://...

# Metodo legacy (se il moderno non funziona)
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CHIAVE_MANCANTE
```

### 5. "Hash Sum mismatch"

```bash
# Il mirror ha dati inconsistenti
sudo rm -rf /var/lib/apt/lists/*      # Pulisci completamente la cache
sudo apt clean
sudo apt update

# Se persiste: cambiare mirror
# Modificare /etc/apt/sources.list con un mirror diverso
# Oppure usare il main archive:
# deb http://archive.ubuntu.com/ubuntu ...
```

### 6. "dpkg: error processing package (--configure)"

```bash
# Pacchetto bloccato a meta configurazione
sudo dpkg --configure -a              # Riconfigura tutti
sudo apt install -f                   # Fix dipendenze

# Se un maintainer script fallisce:
# Esaminare l'errore nel log
cat /var/log/dpkg.log | tail -50

# Forzare la rimozione del pacchetto rotto
sudo dpkg --remove --force-remove-reinstreq pacchetto
sudo apt install -f
```

### 7. "Conflicting packages" / "Trying to overwrite file"

```bash
# File posseduto da un altro pacchetto
dpkg -S /percorso/del/file            # Chi possiede il file?

# Forzare sovrascrittura (usare con cautela)
sudo dpkg -i --force-overwrite pacchetto.deb
sudo apt install -f

# Soluzione pulita: rimuovere il pacchetto in conflitto
sudo apt remove pacchetto-vecchio
sudo apt install pacchetto-nuovo
```

### 8. "Sub-process /usr/bin/dpkg returned an error code (1)"

```bash
# Un maintainer script e fallito
# Esaminare quale script:
cat /var/log/dpkg.log | tail -20

# Forzare la rimozione
sudo dpkg --purge --force-all pacchetto
sudo apt install -f
sudo apt install pacchetto            # Reinstallare pulito
```

### 9. Disco pieno durante installazione

```bash
# Liberare spazio nella cache APT
sudo apt clean                        # Rimuove TUTTI i .deb dalla cache
du -sh /var/cache/apt/archives/       # Verificare lo spazio liberato

# Rimuovere vecchi kernel
dpkg -l | grep linux-image | grep -v $(uname -r)
sudo apt autoremove --purge

# Rimuovere log vecchi
sudo journalctl --vacuum-size=100M

# Identificare file grandi
du -sh /var/log/* | sort -rh | head -10
```

### 10. Repository HTTPS non funziona

```bash
# Manca il transport HTTPS
sudo apt install apt-transport-https ca-certificates

# Certificato scaduto / non valido
# Temporaneo (solo per debug, MAI in produzione):
# Acquire::https::Verify-Peer "false";  ← NON FARLO

# Soluzione: aggiornare i certificati
sudo apt install --reinstall ca-certificates
sudo update-ca-certificates
```

### 11. "dpkg was interrupted, you must manually run 'dpkg --configure -a'"

```bash
sudo dpkg --configure -a
sudo apt update
sudo apt upgrade
```

### 12. Pacchetto installato ma comando non trovato

```bash
# Il binario non e nel PATH
dpkg -L pacchetto | grep bin/

# Aggiungere al PATH se necessario
which comando
type comando

# Hash della shell non aggiornata
hash -r                               # Bash: svuota la cache dei path
```

### 13. "E: The repository ... is not signed" (APT)

```bash
# Il repository non ha Release.gpg o InRelease
# Opzione 1 (raccomandato): contattare il maintainer del repository
# Opzione 2 (temporaneo, NON per produzione):
# deb [trusted=yes] https://repo.insicuro.com/apt stable main
# ← ATTENZIONE: disabilita la verifica GPG per questo repo
```

### 14. DNF: "Error: Failed to download metadata for repo"

```bash
# Pulire la cache
sudo dnf clean all
sudo dnf makecache

# Repository non raggiungibile
sudo dnf repolist -v                  # Mostra URL effettivi
curl -I https://url-del-repo/repodata/repomd.xml  # Test connettivita

# Disabilitare temporaneamente un repository rotto
sudo dnf --disablerepo=repo-rotto update
```

### 15. DNF: "Error: Transaction check error"

```bash
# File in conflitto tra pacchetti
# Identificare il conflitto
sudo dnf install --allowerasing pacchetto

# Rebuild del database RPM
sudo rpm --rebuilddb
sudo dnf clean all
sudo dnf update
```

### 16. Snap: "error: snap is not available on stable for this architecture"

```bash
# Lo snap non supporta la propria architettura
snap info nome-snap                   # Verificare le architetture supportate

# Alternativa: cercare il software come Flatpak o pacchetto nativo
flatpak search nome
apt search nome
```

### 17. Flatpak: runtime non trovato

```bash
# Installare il runtime richiesto
flatpak install flathub org.freedesktop.Platform//24.08

# Elencare runtime disponibili
flatpak remote-ls flathub --runtime
```

### 18. "Temporary failure resolving 'archive.ubuntu.com'"

```bash
# Problema DNS
# Verificare la connettivita
ping -c 1 8.8.8.8                     # Rete OK?
nslookup archive.ubuntu.com           # DNS OK?

# Fix temporaneo
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# Fix permanente: configurare systemd-resolved o NetworkManager
```

### 19. Database RPM corrotto

```bash
# Backup e rebuild
sudo cp -r /var/lib/rpm /var/lib/rpm.backup
sudo rpm --rebuilddb

# Se il rebuild fallisce:
sudo rm -f /var/lib/rpm/__db*         # Rimuovi solo i file di lock Berkeley DB
sudo rpm --rebuilddb
```

### 20. Downgrade di un pacchetto

```bash
# APT: installare una versione specifica precedente
apt-cache showpkg nginx               # Versioni disponibili
sudo apt install nginx=1.18.0-0ubuntu1

# DNF: downgrade
sudo dnf downgrade nginx

# DNF: rollback a una transazione precedente
dnf history
sudo dnf history undo <ID>

# Pacman: dalla cache locale
sudo pacman -U /var/cache/pacman/pkg/nginx-1.24.0-1-x86_64.pkg.tar.zst
```

### 21. Apt continua a proporre aggiornamenti per un pacchetto bloccato

```bash
# Verificare che l'hold sia attivo
apt-mark showhold

# Verificare che non ci siano pin in conflitto
apt-cache policy pacchetto

# Alternativa: pin con priorita negativa
# /etc/apt/preferences.d/no-pacchetto.pref
# Package: pacchetto
# Pin: release *
# Pin-Priority: -1
```

---

## FAQ

### 1. Qual e la differenza tra `apt remove` e `apt purge`?

`remove` rimuove i file binari del pacchetto ma mantiene i file di configurazione in `/etc/`. `purge` rimuove tutto, incluse le configurazioni. Usare `purge` quando non si intende mai reinstallare, `remove` quando si vuole mantenere la configurazione per una futura reinstallazione.

### 2. Posso usare `apt` negli script di automazione?

No. `apt` e progettato per l'uso interattivo: l'output cambia tra versioni e puo includere prompt. Negli script, cron job e playbook Ansible usare sempre `apt-get` e `apt-cache`, il cui output e stabile e documentato.

### 3. Come faccio a sapere quali pacchetti ho installato manualmente?

```bash
# Debian/Ubuntu
apt-mark showmanual

# Fedora/RHEL
dnf repoquery --userinstalled

# Arch
pacman -Qet
```

### 4. Cosa sono i "recommended packages" e devo installarli?

I pacchetti `Recommends` in Debian/Ubuntu sono installati per default da `apt` perche migliorano significativamente la funzionalita. Su server o container, disabilitarli con `--no-install-recommends` riduce lo spazio disco. Su desktop, tenerli attivi.

### 5. Come gestire software che non e nei repository ufficiali?

Ordine di preferenza:
1. Repository ufficiale della distribuzione
2. Repository ufficiale del progetto (Docker, Node, PostgreSQL hanno i propri)
3. Flatpak/Snap per applicazioni desktop
4. Compilazione con checkinstall per creare un .deb/.rpm tracciabile
5. Container Docker per applicazioni server isolate
6. `make install` solo in ambienti effimeri di sviluppo

### 6. E sicuro usare PPA su Ubuntu?

I PPA sono repository di terze parti non verificati da Canonical. Rischi: pacchetti non aggiornati, malware, conflitti con pacchetti ufficiali. Regole: usare solo PPA di sviluppatori noti, non aggiungerne piu del necessario, rimuoverli con `ppa-purge` quando non servono piu.

### 7. Come migrare i pacchetti installati su un nuovo sistema?

```bash
# Debian/Ubuntu: esportare la lista
dpkg --get-selections > pacchetti.txt
# Sul nuovo sistema:
sudo dpkg --set-selections < pacchetti.txt
sudo apt-get dselect-upgrade

# Fedora/RHEL
dnf repoquery --installed --qf '%{name}' > pacchetti.txt
sudo dnf install $(cat pacchetti.txt)
```

### 8. Perche Snap e piu lento all'avvio rispetto ai pacchetti nativi?

Snap usa filesystem SquashFS montati a runtime tramite loop device. L'avvio richiede: mount del SquashFS + setup del confinamento AppArmor + mount dei bind per le interfacce. Questo aggiunge 1-5 secondi al primo avvio (cold start). Il warm start e piu veloce grazie al caching del kernel.

### 9. Posso mescolare repository di distribuzioni diverse?

No. Mai aggiungere repository di Ubuntu a Debian o viceversa, ne repository di Fedora a CentOS. Le dipendenze sono compilate e testate per la distribuzione specifica. Mescolare causa conflitti di librerie, pacchetti rotti e potenziali instabilita del sistema.

### 10. Come funziona `apt autoremove` e quando e sicuro?

`autoremove` rimuove i pacchetti marcati come "auto" (installati come dipendenza) che non sono piu richiesti da nessun altro pacchetto. E sicuro nella grande maggioranza dei casi. Se un pacchetto importante verrebbe rimosso, marcarlo come "manual": `sudo apt-mark manual pacchetto`.

### 11. Qual e la differenza tra `dnf update` e `dnf upgrade`?

In DNF moderno sono sinonimi. Storicamente in YUM, `update` non rimuoveva pacchetti obsoleti mentre `upgrade` si. In DNF entrambi si comportano come il vecchio `upgrade`. Usare indifferentemente.

### 12. Come posso verificare se un pacchetto e stato manomesso?

```bash
# Debian: verificare i checksum dei file installati
debsums -c                            # Mostra solo file modificati
debsums -a pacchetto                  # Verifica un pacchetto specifico

# RPM: verifica integrita
rpm -V pacchetto                      # Flag per ogni file diverso dall'originale
rpm -Va                               # Verifica TUTTI i pacchetti
```

### 13. Come faccio il rollback di un aggiornamento che ha rotto qualcosa?

```bash
# DNF: rollback nativo
dnf history
sudo dnf history undo <ID-transazione>

# APT: nessun rollback nativo
# Opzioni:
# 1. Installare la versione precedente manualmente con apt install pacchetto=versione
# 2. Ripristinare da snapshot filesystem (btrfs/LVM)
# 3. Per questo motivo: snapshot PRIMA di aggiornamenti critici
```

### 14. Flatpak consuma troppo spazio disco. Come ridurre?

```bash
# Rimuovere runtime e app inutilizzati
flatpak uninstall --unused

# Rimuovere dati residui
flatpak uninstall --delete-data app.non.usata

# Verificare lo spazio usato
du -sh ~/.local/share/flatpak
du -sh /var/lib/flatpak

# Flatpak condivide i runtime tra applicazioni:
# 3 app GNOME usano lo stesso org.gnome.Platform, non tre copie
```

### 15. Come impedire che un pacchetto venga installato, anche come dipendenza?

```bash
# APT: pin con priorita negativa
# /etc/apt/preferences.d/block-pacchetto.pref
Package: pacchetto-indesiderato
Pin: release *
Pin-Priority: -1

# DNF: excludepkgs in dnf.conf
# excludepkgs=pacchetto-indesiderato

# Oppure per un singolo comando:
sudo dnf install --exclude=pacchetto-indesiderato altro-pacchetto
```

### 16. Quale package manager universale scegliere: Snap o Flatpak?

Dipende dal contesto. Snap e integrato nativamente in Ubuntu e supporta sia applicazioni desktop che servizi server (es. LXD, MicroK8s). Flatpak e focalizzato esclusivamente sul desktop, ha migliore integrazione temi/portals e non richiede un demone root. Per ambienti multi-distribuzione desktop, Flatpak e generalmente preferito. Per ambienti Ubuntu-centrici o servizi, Snap.

---

## Matrice decisionale

### Quando usare cosa

| Scenario | Scelta raccomandata | Motivazione |
|---|---|---|
| Server produzione | `apt`/`dnf` nativo | Stabilita, supporto LTS, security updates |
| Applicazione desktop cross-distro | Flatpak | Portals XDG, sandboxing, runtime condivisi |
| Applicazione desktop su Ubuntu | Snap o nativo | Integrazione nativa, aggiornamenti automatici |
| Microservizio in container | Alpine `apk` + multi-stage | Dimensione minima, superficie attacco ridotta |
| Applicazione portatile (USB) | AppImage | File singolo, zero dipendenze di sistema |
| Ambiente di sviluppo isolato | Nix (nix shell / nix develop) | Riproducibilita, nessun conflitto |
| Software interno aziendale | Repository privato apt/dnf | Controllo completo, firma GPG, audit |
| Kernel personalizzato | Pacchetto nativo (.deb/.rpm) | Integrazione GRUB, mkinitramfs |
| Software compilato da sorgente | checkinstall o fpm | Tracciabilita nel package manager |
| CI/CD pipeline | Distroless o Alpine | Velocita build, sicurezza, dimensione |
| Database produzione | Pacchetto nativo + version pin | Aggiornamenti controllati, rollback |
| Infrastruttura immutabile | Nix/NixOS | Intera configurazione dichiarativa |

### Albero decisionale rapido

```
Il software e nel repository ufficiale della distro?
├── Si → Usare il package manager nativo (apt/dnf/pacman)
│        E' un server di produzione?
│        ├── Si → Pin la versione, abilita unattended-upgrades solo per security
│        └── No → Upgrade standard
└── No → E' un'applicazione desktop?
         ├── Si → Disponibile come Flatpak/Snap?
         │        ├── Si → Preferire Flatpak (cross-distro) o Snap (Ubuntu)
         │        └── No → Repository ufficiale del progetto, poi AppImage
         └── No → E' per un container?
                  ├── Si → Alpine apk o distroless
                  └── No → Repository privato aziendale o compilazione con checkinstall
```
