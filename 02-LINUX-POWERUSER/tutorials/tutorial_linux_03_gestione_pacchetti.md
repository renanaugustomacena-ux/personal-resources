# Tutorial Linux 03 — Gestione Pacchetti: apt, dnf, pacman, snap, flatpak

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** apt/dpkg, dnf/rpm, pacman/AUR, snap, flatpak, pip system-level, repository
> **Prerequisiti:** `tutorial_linux_02_shell_mastery.md`
> **Durata stimata:** 10-14 ore

---

## Mappa concettuale

```
Gestione Pacchetti Linux
│
├── Debian/Ubuntu — APT
│   ├── apt — front-end moderno
│   ├── apt-get / apt-cache — scriptable
│   ├── dpkg — back-end basso livello
│   └── /etc/apt/sources.list, sources.list.d/
│
├── RHEL/Fedora/CentOS — DNF/RPM
│   ├── dnf — front-end moderno (sostituisce yum)
│   ├── rpm — back-end basso livello
│   └── /etc/yum.repos.d/
│
├── Arch Linux — Pacman/AUR
│   ├── pacman — gestore ufficiale
│   ├── AUR — Arch User Repository
│   └── paru / yay — AUR helper
│
├── Distribuzione-agnostico
│   ├── snap — Canonical
│   ├── flatpak — cross-distro
│   └── AppImage — portable
│
└── Aggiornamenti sicuri
    ├── unattended-upgrades
    ├── dnf-automatic
    └── verificare firme GPG
```

---

# Parte A — APT (Debian/Ubuntu)

---

## A1. Operazioni base apt

```bash
# Aggiorna lista pacchetti (MAI salta questo prima di install)
apt update

# Aggiorna tutti i pacchetti
apt upgrade                    # conservativo (no rimozioni)
apt full-upgrade               # completo (può rimuovere pacchetti)
apt dist-upgrade               # equivalente a full-upgrade

# Installazione
apt install nginx postgresql-16 git
apt install -y nginx           # no conferma interattiva (script)
apt install --no-install-recommends nginx   # solo dipendenze strette
apt install nginx=1.24.0-1     # versione specifica

# Rimozione
apt remove nginx               # rimuove ma lascia config
apt purge nginx                # rimuove + config
apt autoremove                 # rimuove dipendenze orfane
apt autoremove --purge         # rimuove + config orfane

# Ricerca
apt search "web server"
apt show nginx                 # dettagli pacchetto
apt list --installed           # lista installati
apt list --upgradable          # lista aggiornabili

# Cache
apt clean                      # svuota /var/cache/apt/archives
apt autoclean                  # rimuove solo pacchetti vecchi
```

---

## A2. Repository e chiavi GPG

```bash
# Aggiungere repository (modo moderno)
# 1. Scarica chiave GPG
curl -fsSL https://nginx.org/keys/nginx_signing.key \
  | gpg --dearmor \
  | tee /usr/share/keyrings/nginx-archive-keyring.gpg > /dev/null

# 2. Aggiungi sorgente con chiave associata
echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
  http://nginx.org/packages/ubuntu $(lsb_release -cs) nginx" \
  | tee /etc/apt/sources.list.d/nginx.list

# 3. Aggiorna e installa
apt update && apt install nginx

# Verificare chiave GPG pacchetto
apt-key list   # obsoleto ma ancora funziona
gpg --verify /var/cache/apt/archives/nginx_*.deb

# Pinning pacchetti — blocca versione specifica
cat > /etc/apt/preferences.d/nginx << 'EOF'
Package: nginx
Pin: version 1.24.*
Pin-Priority: 1001
EOF

# dpkg — basso livello
dpkg -i pacchetto.deb          # installa .deb locale
dpkg -r nginx                  # rimuove
dpkg -l | grep nginx           # lista con filtro
dpkg -L nginx                  # file installati da nginx
dpkg -S /usr/sbin/nginx        # quale pacchetto ha installato questo file
dpkg --get-selections          # tutti i pacchetti installati
```

---

## A3. unattended-upgrades

```bash
# Installazione
apt install unattended-upgrades

# Configurazione
cat /etc/apt/apt.conf.d/50unattended-upgrades
# Uncomment per ricevere email su problemi:
# Unattended-Upgrade::Mail "admin@example.com";
# Unattended-Upgrade::Remove-Unused-Dependencies "true";

# Abilita
dpkg-reconfigure --priority=low unattended-upgrades
systemctl enable --now unattended-upgrades

# Test esecuzione
unattended-upgrade -d --dry-run   # simula
```

---

# Parte B — DNF/RPM (RHEL/Fedora)

---

## B1. Operazioni base dnf

```bash
# Aggiorna
dnf check-update               # controlla aggiornamenti
dnf upgrade                    # aggiorna tutto
dnf upgrade --security         # solo patch di sicurezza

# Installazione
dnf install nginx
dnf install -y nginx postgresql-server
dnf install /percorso/pacchetto.rpm   # file locale
dnf install "nginx = 1.24.0"

# Rimozione
dnf remove nginx
dnf autoremove                 # rimuove dipendenze orfane

# Ricerca
dnf search nginx
dnf info nginx
dnf provides /usr/sbin/nginx   # quale pacchetto ha questo file
dnf repoquery --list nginx     # file di un pacchetto

# History (potente!)
dnf history                    # storico transazioni
dnf history info 5             # dettagli transazione 5
dnf history undo 5             # annulla transazione 5 (rollback!)

# Gruppi
dnf group list
dnf group install "Development Tools"

# Moduli (RHEL 8+)
dnf module list
dnf module enable nodejs:18
dnf module install nodejs:18/default

# RPM basso livello
rpm -ivh pacchetto.rpm         # installa
rpm -qa | grep nginx           # query installati
rpm -ql nginx                  # file del pacchetto
rpm -qf /usr/sbin/nginx        # a quale pacchetto appartiene
rpm -V nginx                   # verifica integrità
```

---

# Parte C — Pacman/AUR (Arch Linux)

---

## C1. Pacman

```bash
# Aggiorna
pacman -Syu                    # aggiorna tutto il sistema

# Installazione
pacman -S nginx
pacman -S --needed nginx       # salta se già installato
pacman -U /percorso/pacchetto.pkg.tar.zst   # file locale

# Rimozione
pacman -R nginx                # rimuove pacchetto
pacman -Rs nginx               # rimuove + dipendenze orfane
pacman -Rns nginx              # rimuove + dipendenze + config

# Ricerca
pacman -Ss nginx               # cerca nei repo
pacman -Si nginx               # info pacchetto
pacman -Qs nginx               # cerca tra installati
pacman -Ql nginx               # file del pacchetto
pacman -Qo /usr/sbin/nginx     # a quale pacchetto appartiene

# Cache
pacman -Sc                     # pulisce cache vecchie versioni
pacman -Scc                    # pulisce tutta la cache

# AUR — Arch User Repository
# Usa paru o yay come AUR helper
paru -S google-chrome
yay -S visual-studio-code-bin
```

---

# Parte D — snap e flatpak

---

## D1. snap

```bash
# Installazione snapd
apt install snapd

# Comandi base
snap install code --classic   # VS Code
snap install vlc
snap install --edge firefox   # canale edge

# Gestione
snap list                     # installati
snap info code                # dettagli
snap find "video player"      # cerca
snap refresh                  # aggiorna tutti
snap refresh code             # aggiorna specifico
snap remove vlc               # rimuove
snap revert code              # torna alla versione precedente

# Connessioni (permessi)
snap connections vlc          # connessioni attuali
snap connect vlc:removable-media   # dai accesso a /media

# Canali
# stable (default), candidate, beta, edge
snap install --channel=beta node
```

---

## D2. flatpak

```bash
# Installazione
apt install flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Comandi base
flatpak install flathub org.gimp.GIMP
flatpak install --user flathub org.mozilla.firefox   # solo utente corrente
flatpak run org.gimp.GIMP
flatpak list
flatpak update
flatpak remove org.gimp.GIMP

# Permessi
flatpak info --show-permissions org.gimp.GIMP
flatpak override --filesystem=home org.gimp.GIMP   # accesso alla home

# Pulizia
flatpak uninstall --unused   # rimuove runtimes non usati
```

---

# Parte E — Riepilogo

## Confronto gestori pacchetti

| Operazione | APT | DNF | Pacman |
|---|---|---|---|
| Aggiorna indice | `apt update` | (automatico) | (automatico) |
| Aggiorna tutto | `apt upgrade` | `dnf upgrade` | `pacman -Syu` |
| Installa | `apt install` | `dnf install` | `pacman -S` |
| Rimuovi | `apt purge` | `dnf remove` | `pacman -Rns` |
| Cerca | `apt search` | `dnf search` | `pacman -Ss` |
| Info | `apt show` | `dnf info` | `pacman -Si` |
| File pacchetto | `dpkg -L` | `rpm -ql` | `pacman -Ql` |
| Quale pacchetto | `dpkg -S` | `rpm -qf` | `pacman -Qo` |

## Best practice sicurezza

- Aggiorna regolarmente — `apt upgrade` almeno settimanalmente
- Abilita unattended-upgrades per patch sicurezza automatiche
- Verifica sempre la firma GPG dei repository aggiunti
- Preferisci pacchetti distro-nativi a compilazione da sorgente
- Testa aggiornamenti in staging prima di produzione

## Prossimi passi

- `tutorial_linux_04_systemd.md` — gestire servizi con systemd
- `tutorial_linux_11_sicurezza.md` — hardening sistema post-installazione
