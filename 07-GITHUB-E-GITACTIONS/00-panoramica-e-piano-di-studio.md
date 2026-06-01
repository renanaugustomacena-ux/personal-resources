# Panoramica e Piano di Studio — Git, GitHub e GitHub Actions

## Indice

- [Panoramica](#panoramica)
- [Piano di Studio](#piano-di-studio)
- [Ambiente di Laboratorio](#ambiente-di-laboratorio)
- [Glossario](#glossario)
- [Risorse Consigliate](#risorse-consigliate)

---

## Panoramica

Questo modulo copre l'ecosistema Git, GitHub e GitHub Actions — tre pilastri dello sviluppo software moderno e dell'infrastruttura IT. Git è il sistema di version control distribuito più utilizzato al mondo, GitHub è la piattaforma di hosting e collaborazione, e GitHub Actions fornisce CI/CD integrato direttamente nella piattaforma.

### Perché è Importante

- **Version Control** è fondamentale per ogni professionista IT: sviluppatori, DevOps, sysadmin
- **Collaboration** strutturata con pull request, code review, issue tracking
- **CI/CD** automatizza build, test, deploy — riduce errori e accelera il delivery
- **Infrastructure as Code**: configurazioni, playbook Ansible, Terraform — tutto versionato in Git

---

## Piano di Studio

### Fase 1: Fondamenti Git (Settimana 1-2)

| Modulo | Argomento | Priorità |
|--------|-----------|----------|
| 01 | Fondamenti Git — init, staging, commit, branch, merge, remote | Critica |
| 02 | Strategie Branching — GitFlow, GitHub Flow, trunk-based | Alta |

### Fase 2: Piattaforma GitHub (Settimana 3-4)

| Modulo | Argomento | Priorità |
|--------|-----------|----------|
| 03 | Piattaforma GitHub — repo, Issues, PR, review, API, CLI, sicurezza | Alta |

### Fase 3: Automazione (Settimana 5-6)

| Modulo | Argomento | Priorità |
|--------|-----------|----------|
| 04 | GitHub Actions — workflow YAML, trigger, jobs, matrix, secrets, CD | Critica |
| 05 | Progetti Pratici — pipeline CI/CD, automazione release, monorepo | Alta |

### Certificazioni Correlate

| Certificazione | Focus |
|---------------|-------|
| GitHub Foundations | Concetti base Git e GitHub |
| GitHub Actions | CI/CD con GitHub Actions |
| GitHub Advanced Security | CodeQL, Dependabot, secret scanning |
| GitHub Administration | Gestione organization e enterprise |

---

## Ambiente di Laboratorio

### Setup

```bash
# Installare Git
# Linux
sudo apt install git

# macOS
brew install git

# Windows
winget install Git.Git

# Configurazione iniziale
git config --global user.name "Nome Cognome"
git config --global user.email "email@esempio.com"
git config --global init.defaultBranch main
git config --global core.editor "code --wait"    # VS Code
git config --global pull.rebase false             # merge come default
git config --global push.autoSetupRemote true     # push crea branch remoto

# SSH key per GitHub
ssh-keygen -t ed25519 -C "email@esempio.com"
# Aggiungere la chiave pubblica a GitHub → Settings → SSH and GPG keys
ssh -T git@github.com    # Testare

# Installare GitHub CLI
# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
sudo apt update && sudo apt install gh

# Autenticare
gh auth login

# VS Code extensions consigliate
# - GitLens (visualizzazione avanzata Git)
# - GitHub Pull Requests and Issues
# - GitHub Actions
```

---

## Glossario

| Termine | Descrizione |
|---------|-------------|
| **Repository (repo)** | Progetto versionato con Git, contiene file e cronologia completa |
| **Commit** | Snapshot dello stato dei file in un momento specifico |
| **Branch** | Linea di sviluppo indipendente |
| **Merge** | Unire due branch |
| **Rebase** | Riapplicare i commit di un branch sopra un altro (cronologia lineare) |
| **Remote** | Repository remoto (es. su GitHub) |
| **Origin** | Nome convenzionale del remote principale |
| **HEAD** | Puntatore al commit corrente (dove ci si trova) |
| **Staging Area (Index)** | Area di preparazione per il prossimo commit |
| **Working Directory** | I file effettivi su disco |
| **Pull Request (PR)** | Richiesta di merge su GitHub, con code review |
| **Fork** | Copia personale di un repository altrui |
| **Clone** | Copia locale di un repository remoto |
| **Tag** | Etichetta su un commit specifico (tipicamente per release) |
| **Stash** | Salvataggio temporaneo di modifiche non committate |
| **Cherry-pick** | Applicare un singolo commit da un altro branch |
| **Conflict** | Modifiche incompatibili su stesse righe che richiedono risoluzione manuale |
| **CI/CD** | Continuous Integration / Continuous Delivery — automazione build+test+deploy |
| **Workflow** | File YAML che definisce un processo automatizzato in GitHub Actions |
| **Runner** | Macchina (GitHub-hosted o self-hosted) che esegue i workflow |

---

## Risorse Consigliate

### Documentazione
- [Git Reference](https://git-scm.com/docs) — Documentazione ufficiale Git
- [Pro Git Book](https://git-scm.com/book/en/v2) — Libro completo gratuito
- [GitHub Docs](https://docs.github.com) — Documentazione GitHub
- [GitHub Actions Docs](https://docs.github.com/actions)

### Strumenti
- **Git** — Version control CLI
- **GitHub CLI (`gh`)** — Gestione GitHub da terminale
- **VS Code + GitLens** — IDE con integrazione Git avanzata
- **tig** — Interfaccia ncurses per Git (terminale)
- **lazygit** — TUI interattiva per Git

### Practice
- [Learn Git Branching](https://learngitbranching.js.org) — Tutorial interattivo visuale
- [GitHub Skills](https://skills.github.com) — Corsi pratici ufficiali GitHub
