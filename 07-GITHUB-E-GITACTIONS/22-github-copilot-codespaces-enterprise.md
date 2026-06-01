---
corso: "GitHub e Git Actions"
fase: "6 — Avanzato"
modulo: 22
titolo: "GitHub Copilot, Codespaces e Enterprise: Funzionalità Moderne di GitHub"
versione: "GitHub Enterprise Cloud 2024 / Copilot Business"
livello: "Avanzato"
prerequisiti: ["Piattaforma GitHub (modulo 03)", "GitHub Repository Management (modulo 12)", "VS Code base"]
obiettivi:
  - "Configurare GitHub Copilot Individual/Business e integrarlo con VS Code, JetBrains e CLI"
  - "Creare e personalizzare Codespaces con devcontainer.json, prebuild e lifecycle scripts"
  - "Implementare SAML SSO, SCIM provisioning e Enterprise Managed Users (EMU)"
  - "Gestire audit log, IP allow list e policy di sicurezza a livello enterprise"
  - "Ottimizzare costi Codespaces con machine type policies, timeout e spending limits"
tag: [github-copilot, codespaces, enterprise, saml-sso, scim, emu, devcontainer, audit-log, ip-allowlist, ai-coding]
---

# 22 — GitHub Copilot, Codespaces e Enterprise: Funzionalità Moderne di GitHub

> **Modulo 22** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Configurare GitHub Copilot Individual/Business e integrarlo con VS Code, JetBrains e CLI
> 2. Creare e personalizzare Codespaces con devcontainer.json, prebuild e lifecycle scripts
> 3. Implementare SAML SSO, SCIM provisioning e Enterprise Managed Users (EMU)
> 4. Gestire audit log, IP allow list e policy di sicurezza a livello enterprise
> 5. Ottimizzare costi Codespaces con machine type policies, timeout e spending limits

## Idee guida
1. **Copilot Workspace 2024+: agentic coding integrato.**
2. **Codespaces: dev env standardizzato, no "works on my machine".**
3. **Enterprise: SAML SSO, audit log, IP allowlist.**
4. **EMU (Enterprise Managed Users) per company-controlled identity.**


## Indice

1. [Introduzione](#introduzione)
2. [GitHub Copilot](#github-copilot)
   - [Setup e Configurazione](#setup-e-configurazione)
   - [Integrazione con IDE](#integrazione-con-ide)
   - [Copilot Chat](#copilot-chat)
   - [Copilot CLI](#copilot-cli)
   - [Prompt Engineering per Copilot](#prompt-engineering-per-copilot)
   - [Privacy e Sicurezza](#privacy-e-sicurezza-copilot)
   - [Policy Organizzative](#policy-organizzative-copilot)
   - [Copilot Agent Mode](#copilot-agent-mode)
   - [Copilot Coding Agent (Cloud Agent)](#copilot-coding-agent-cloud-agent)
   - [Copilot Code Review Agentico](#copilot-code-review-agentico)
   - [Selezione Multi-Modello](#selezione-multi-modello)
   - [Copilot Extensions e MCP](#copilot-extensions-e-mcp)
   - [Custom Instructions](#custom-instructions)
   - [GitHub Spark](#github-spark)
   - [Piani e Pricing Copilot 2026](#piani-e-pricing-copilot-2026)
3. [GitHub Codespaces](#github-codespaces)
   - [Configurazione devcontainer.json](#configurazione-devcontainerjson)
   - [Prebuilds](#prebuilds)
   - [Dotfiles e Personalizzazione](#dotfiles-e-personalizzazione)
   - [Port Forwarding](#port-forwarding)
   - [Estensioni e Tool](#estensioni-e-tool)
   - [Gestione Costi](#gestione-costi-codespaces)
   - [Confronto con Sviluppo Locale](#confronto-con-sviluppo-locale)
   - [GPU e Machine Learning in Codespaces](#gpu-e-machine-learning-in-codespaces)
   - [Lifecycle Hooks Avanzati](#lifecycle-hooks-avanzati)
   - [Multi-Repository e Monorepo](#multi-repository-e-monorepo)
   - [Sicurezza e Hardening Codespaces](#sicurezza-e-hardening-codespaces)
4. [GitHub Enterprise](#github-enterprise)
   - [GHES vs GHEC](#ghes-vs-ghec)
   - [SAML SSO](#saml-sso)
   - [SCIM Provisioning](#scim-provisioning)
   - [Audit Log](#audit-log)
   - [IP Allow Lists](#ip-allow-lists)
   - [Gestione Organizzazioni](#gestione-organizzazioni)
   - [InnerSource](#innersource)
   - [Enterprise Managed Users (EMU) — Approfondimento](#enterprise-managed-users-emu--approfondimento)
   - [Data Residency e Compliance](#data-residency-e-compliance)
   - [Audit Log Avanzato](#audit-log-avanzato)
   - [IP Allow List Avanzata](#ip-allow-list-avanzata)
   - [Enterprise Security Hardening](#enterprise-security-hardening)
5. [Integrazione tra le Funzionalità](#integrazione-tra-le-funzionalità)
6. [Riepilogo](#riepilogo)

---

## Introduzione

GitHub si è evoluto da semplice hosting di repository Git a una piattaforma di sviluppo completa. Tre delle sue funzionalità più significative degli ultimi anni sono GitHub Copilot (assistente AI per la programmazione), GitHub Codespaces (ambienti di sviluppo cloud), e le funzionalità Enterprise (gestione aziendale della piattaforma). Queste tre aree, pur essendo distinte, si integrano tra loro per creare un ecosistema di sviluppo coerente e potente.

GitHub Copilot ha cambiato il modo in cui molti sviluppatori scrivono codice, offrendo suggerimenti contestuali basati su modelli di intelligenza artificiale. GitHub Codespaces ha eliminato il problema del "funziona sulla mia macchina" fornendo ambienti di sviluppo identici e istantanei nel cloud. E le funzionalità Enterprise hanno reso GitHub adatto all'uso in grandi organizzazioni con requisiti stringenti di sicurezza, compliance e governance.

Questa guida esplora ciascuna di queste aree in profondità, con configurazioni pratiche, esempi reali, e le considerazioni necessarie per un'adozione efficace in contesti professionali.

---

## GitHub Copilot

### Setup e Configurazione

GitHub Copilot è disponibile in tre versioni:
- **Copilot Individual**: Per sviluppatori singoli ($10/mese o $100/anno)
- **Copilot Business**: Per organizzazioni ($19/utente/mese), con controlli enterprise
- **Copilot Enterprise**: Per enterprise ($39/utente/mese), con personalizzazione su codebase privato

#### Attivazione

```bash
# Verificare lo stato dell'abbonamento
gh copilot status

# Per organizzazioni: abilitare tramite le impostazioni
# Settings > Copilot > Access > Enable for all members
# Oppure selezionare team/utenti specifici
```

#### Configurazione in VS Code

```json
// .vscode/settings.json
{
  // Abilitare/disabilitare Copilot per linguaggio
  "github.copilot.enable": {
    "*": true,
    "plaintext": false,
    "markdown": true,
    "yaml": true,
    "scminput": false
  },

  // Configurazione avanzata
  "github.copilot.advanced": {
    "length": 500,
    "temperature": "",
    "top_p": "",
    "stops": {
      "*": ["\n\n\n"],
      "python": ["\ndef ", "\nclass ", "\nif __name__"]
    },
    "indentationMode": {
      "python": false,
      "javascript": false
    }
  },

  // Copilot Chat
  "github.copilot.chat.localeOverride": "it",
  "github.copilot.chat.useProjectTemplates": true
}
```

#### Configurazione in JetBrains (IntelliJ, PyCharm, etc.)

Per le IDE JetBrains, il plugin GitHub Copilot si installa dal Marketplace:

```
Settings > Plugins > Marketplace > Cerca "GitHub Copilot" > Install

Dopo l'installazione:
Settings > Tools > GitHub Copilot
  - Enable auto-completions: checked
  - Enable Copilot Chat: checked
```

#### Configurazione in Neovim

```lua
-- Usando lazy.nvim come plugin manager
{
  "zbirenbaum/copilot.lua",
  cmd = "Copilot",
  event = "InsertEnter",
  config = function()
    require("copilot").setup({
      suggestion = {
        enabled = true,
        auto_trigger = true,
        debounce = 75,
        keymap = {
          accept = "<M-l>",
          accept_word = "<M-k>",
          accept_line = "<M-j>",
          next = "<M-]>",
          prev = "<M-[>",
          dismiss = "<C-]>",
        },
      },
      panel = {
        enabled = true,
        auto_refresh = true,
      },
      filetypes = {
        yaml = true,
        markdown = true,
        ["."] = false,
      },
    })
  end,
},

-- Per Copilot Chat in Neovim
{
  "CopilotC-Nvim/CopilotChat.nvim",
  branch = "canary",
  dependencies = {
    { "zbirenbaum/copilot.lua" },
    { "nvim-lua/plenary.nvim" },
  },
  config = function()
    require("CopilotChat").setup({
      model = "gpt-4",
      temperature = 0.1,
      window = {
        layout = "vertical",
        width = 0.4,
      },
    })
  end,
}
```

### Integrazione con IDE

#### Come Funzionano i Suggerimenti

Copilot analizza il contesto circostante — il file corrente, i file aperti, i commenti, i nomi delle funzioni — per generare suggerimenti di codice. Più contesto fornisci, migliori saranno i suggerimenti.

```python
# Esempio: Copilot genera l'implementazione basandosi sul nome e il docstring

def calculate_compound_interest(
    principal: float,
    annual_rate: float,
    times_compounded: int,
    years: float
) -> float:
    """
    Calcola l'interesse composto.

    Args:
        principal: Capitale iniziale
        annual_rate: Tasso di interesse annuo (es. 0.05 per 5%)
        times_compounded: Numero di volte che l'interesse viene composto per anno
        years: Numero di anni

    Returns:
        Il valore finale dell'investimento

    Example:
        >>> calculate_compound_interest(1000, 0.05, 12, 10)
        1647.01
    """
    # Copilot suggerirà:
    amount = principal * (1 + annual_rate / times_compounded) ** (times_compounded * years)
    return round(amount, 2)
```

```typescript
// Esempio: Copilot genera una funzione completa dal commento

// Funzione che valida un indirizzo email italiano,
// accettando solo domini .it, .com e .eu
// Deve controllare formato, lunghezza massima 254 caratteri,
// e che non ci siano caratteri speciali non validi

function validateItalianEmail(email: string): {
  valid: boolean;
  error?: string;
} {
  // Copilot genererà l'implementazione completa:
  if (!email || email.length > 254) {
    return { valid: false, error: "Email troppo lunga o vuota" };
  }

  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(it|com|eu)$/;

  if (!emailRegex.test(email)) {
    return {
      valid: false,
      error: "Formato email non valido o dominio non accettato (.it, .com, .eu)"
    };
  }

  const [localPart, domain] = email.split("@");

  if (localPart.length > 64) {
    return { valid: false, error: "Parte locale troppo lunga (max 64 caratteri)" };
  }

  return { valid: true };
}
```

#### Shortcut Principali

| Azione | VS Code | JetBrains |
|--------|---------|-----------|
| Accettare suggerimento | `Tab` | `Tab` |
| Rifiutare suggerimento | `Esc` | `Esc` |
| Suggerimento successivo | `Alt+]` | `Alt+]` |
| Suggerimento precedente | `Alt+[` | `Alt+[` |
| Aprire pannello suggerimenti | `Ctrl+Enter` | `Alt+Enter` |
| Accettare una parola | `Ctrl+→` | `Ctrl+→` |
| Aprire Copilot Chat | `Ctrl+Shift+I` | `Ctrl+Shift+C` |

### Copilot Chat

Copilot Chat è un'interfaccia conversazionale integrata nell'IDE che permette di interagire con l'AI per comprendere, modificare, e generare codice.

#### Comandi Slash Principali

```
/explain     — Spiega il codice selezionato
/fix         — Propone una correzione per un errore
/tests       — Genera test per il codice selezionato
/doc         — Genera documentazione
/optimize    — Suggerisce ottimizzazioni
/clear       — Pulisce la conversazione
/new         — Crea un nuovo file o progetto
/newNotebook — Crea un nuovo Jupyter notebook
```

#### Esempi di Utilizzo

```
# Selezionare un blocco di codice e chiedere:

> /explain Spiega questa funzione, inclusi i casi edge e la complessità computazionale

> /fix Questo codice lancia un TypeError quando l'input è None. Correggi gestendo i casi null.

> /tests Genera test unitari con pytest per questa funzione, coprendo:
  - Input validi
  - Input al boundary
  - Input non validi
  - Casi speciali (stringhe vuote, numeri negativi)

> /doc Genera documentazione JSDoc completa per questa classe, inclusi tutti i metodi pubblici

> Come posso refactorizzare questo codice per seguire il Single Responsibility Principle?
  Il metodo processOrder fa troppe cose: valida l'ordine, calcola il totale,
  applica sconti, processa il pagamento, e invia l'email di conferma.
```

#### Agenti Chat (`@workspace`, `@terminal`, `@vscode`)

```
# @workspace - Domande sul progetto intero
@workspace Come è strutturato il modulo di autenticazione?
@workspace Trova tutti i file che importano il modulo database
@workspace Qual è il flusso di una richiesta API dall'endpoint al database?

# @terminal - Aiuto con comandi terminale
@terminal Come faccio a trovare tutti i file modificati negli ultimi 7 giorni?
@terminal Qual è il comando per verificare le porte in uso su Linux?

# @vscode - Aiuto con l'editor
@vscode Come configuro il debugger per un'app Node.js con TypeScript?
@vscode Come creo uno snippet personalizzato per i test?
```

### Copilot CLI

GitHub Copilot CLI fornisce assistenza AI direttamente nel terminale.

```bash
# Installazione
gh extension install github/gh-copilot

# Spiegare un comando
gh copilot explain "find . -name '*.log' -mtime +30 -exec rm {} \;"
# Output:
# Questo comando:
# 1. Cerca file con estensione .log nella directory corrente e sottodirectory
# 2. Filtra quelli modificati più di 30 giorni fa
# 3. Li elimina uno per uno

# Suggerire un comando
gh copilot suggest "comprimi tutti i file .log in un archivio tar.gz e poi eliminali"
# Output suggerito:
# tar czf logs-archive-$(date +%Y%m%d).tar.gz *.log && rm *.log

# Aiuto con Git
gh copilot suggest "mostra i commit dell'ultimo mese che hanno modificato file nella directory src/auth/"
# Output:
# git log --since="1 month ago" -- src/auth/

# Alias per uso rapido
alias '??'='gh copilot suggest -t shell'
alias 'git?'='gh copilot suggest -t git'
alias 'gh?'='gh copilot suggest -t gh'

# Uso con alias
?? "trova i 10 processi che usano più memoria"
git? "annulla l'ultimo commit mantenendo le modifiche"
gh? "crea una release con le note generate automaticamente"
```

### Prompt Engineering per Copilot

La qualità dei suggerimenti di Copilot dipende enormemente dalla qualità del contesto fornito. Ecco le tecniche per ottenere suggerimenti migliori.

#### 1. Commenti Descrittivi

```python
# CATTIVO: commento vago
# Processa i dati
def process(data):
    pass

# BUONO: commento specifico con dettagli
# Processa una lista di transazioni bancarie:
# - Filtra le transazioni con importo > 0
# - Raggruppa per categoria (food, transport, entertainment, other)
# - Calcola il totale per ogni categoria
# - Restituisce un dizionario ordinato per totale decrescente
# Input: List[Transaction] dove Transaction ha: amount, category, date
# Output: Dict[str, float] es. {"food": 450.0, "transport": 120.0}
def process_transactions(transactions: list[Transaction]) -> dict[str, float]:
    pass  # Copilot genererà l'implementazione
```

#### 2. Fornire Esempi (Few-Shot)

```javascript
// Funzione per convertire una stringa di tempo in secondi
// Esempi:
//   "2h30m" -> 9000
//   "45m" -> 2700
//   "1h" -> 3600
//   "90s" -> 90
//   "1h30m45s" -> 5445
//   "0" -> 0
//   "" -> 0
function parseTimeToSeconds(timeStr) {
  // Copilot genererà una soluzione che gestisce tutti i casi
}
```

#### 3. Struttura del File

```python
# Copilot usa il contesto del file intero.
# Mettere import, tipi, e costanti in alto fornisce contesto prezioso.

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal

@dataclass
class Order:
    id: str
    customer_id: str
    items: list['OrderItem']
    status: str  # 'pending', 'confirmed', 'shipped', 'delivered', 'cancelled'
    created_at: datetime
    total: Decimal

@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: Decimal
    discount_percent: float = 0.0

# Repository pattern per gli ordini
# Usa PostgreSQL come backend con asyncpg
# Tutte le query sono parametrizzate per sicurezza
class OrderRepository:
    def __init__(self, pool):
        self.pool = pool

    async def find_by_id(self, order_id: str) -> Optional[Order]:
        # Copilot avrà abbastanza contesto per generare una query corretta
        pass

    async def find_by_customer(self, customer_id: str, limit: int = 50) -> list[Order]:
        pass

    async def update_status(self, order_id: str, new_status: str) -> bool:
        pass
```

#### 4. File Adiacenti

Copilot legge anche i file aperti nell'editor come contesto. Aprire file correlati (interfacce, tipi, test esistenti) migliora significativamente i suggerimenti.

#### 5. Pattern di Naming Consistente

```typescript
// Se il codebase usa un pattern consistente, Copilot lo seguirà

// Servizio esistente nel codebase:
class UserService {
  async getById(id: string): Promise<User> { /* ... */ }
  async getAll(filters: UserFilters): Promise<PaginatedResult<User>> { /* ... */ }
  async create(data: CreateUserDto): Promise<User> { /* ... */ }
  async update(id: string, data: UpdateUserDto): Promise<User> { /* ... */ }
  async delete(id: string): Promise<void> { /* ... */ }
}

// Quando crei un nuovo servizio con lo stesso pattern:
class ProductService {
  // Copilot suggerirà metodi con la stessa struttura:
  // getById, getAll, create, update, delete
  // usando i tipi corretti (Product, ProductFilters, etc.)
}
```

### Privacy e Sicurezza Copilot

#### Cosa Viene Inviato a GitHub

Copilot invia a GitHub il contesto necessario per generare suggerimenti:
- Il contenuto del file corrente
- Parti dei file aperti nell'editor
- Il percorso del file e il nome del repository
- Il linguaggio di programmazione
- Commenti e nomi di variabili/funzioni

#### Cosa NON Viene Fatto

Con Copilot Business e Enterprise:
- Il codice dell'organizzazione NON viene usato per addestrare modelli
- I prompt e i suggerimenti NON vengono conservati dopo la generazione
- Il codice NON viene condiviso con altre organizzazioni

#### Configurazione Privacy per Organizzazioni

```
# Settings > Copilot > Policies

# Suggerimenti che matchano codice pubblico
# Se abilitato, blocca suggerimenti identici a codice open source
"Suggestions matching public code": "Block"

# Raccolta dati per miglioramento
# Disabilitare per massima privacy
"Allow GitHub to use Copilot telemetry": "Disabled"

# Copilot Chat in IDE
"Copilot Chat in the IDE": "Enabled" o "Disabled"

# Copilot in the CLI
"Copilot in the CLI": "Enabled" o "Disabled"
```

#### File da Escludere da Copilot

```json
// .github/copilot-config.json (a livello di repository)
{
  "copilot": {
    "content_exclusion": {
      "exclude": [
        "**/.env*",
        "**/secrets/**",
        "**/credentials/**",
        "**/*.pem",
        "**/*.key",
        "**/config/production.*",
        "**/migrations/**"
      ]
    }
  }
}
```

A livello di organizzazione, si possono escludere interi repository:

```
# Organization Settings > Copilot > Content exclusion

Repositories:
  - org/secret-project
  - org/compliance-sensitive-code

Paths:
  - "**/infrastructure/secrets/**"
  - "**/.env*"
  - "**/terraform/*.tfvars"
```

### Policy Organizzative Copilot

#### Gestione delle Licenze

```bash
# Visualizzare l'uso delle licenze Copilot nell'organizzazione
gh api orgs/{org}/copilot/billing/seats \
  --jq '{
    total_seats: .total_seats,
    seats: [.seats[] | {
      login: .assignee.login,
      last_activity: .last_activity_at,
      editor: .last_activity_editor
    }]
  }'

# Revocare una licenza (utente inattivo)
gh api orgs/{org}/copilot/billing/selected_users \
  --method DELETE \
  --input - << 'EOF'
{
  "selected_usernames": ["utente-inattivo"]
}
EOF
```

#### Linee Guida per il Team

```markdown
## Linee Guida Copilot per il Team

### FARE:
- Usare Copilot come punto di partenza, mai come soluzione finale
- Revisionare SEMPRE il codice generato prima di accettarlo
- Verificare che il codice generato sia coperto da test
- Usare commenti descrittivi per guidare i suggerimenti
- Segnalare suggerimenti problematici al team

### NON FARE:
- Non accettare codice senza comprenderlo
- Non usare Copilot per codice critico di sicurezza senza review approfondita
- Non incollare dati sensibili nei prompt di Copilot Chat
- Non affidarsi a Copilot per la correttezza di algoritmi crittografici
- Non usare codice generato che include licenze incompatibili

### ATTENZIONE:
- Copilot può generare codice con vulnerabilità di sicurezza
- Copilot può suggerire pattern deprecati o non ottimali
- Copilot può "allucinare" API o funzioni che non esistono
- Il codice generato deve passare la stessa review di qualsiasi altro codice
```

### Copilot Agent Mode

Agent Mode rappresenta il salto evolutivo più significativo di GitHub Copilot dal suo lancio. A differenza del completamento inline tradizionale, Agent Mode permette a Copilot di operare come un agente autonomo all'interno dell'IDE, capace di iterare sui propri risultati, riconoscere e correggere errori, e completare richieste complesse che coinvolgono più file.

#### Come Funziona Agent Mode

Quando si attiva Agent Mode (disponibile su VS Code, JetBrains, Eclipse e Xcode), Copilot non si limita a suggerire singole linee di codice. Invece, esegue un ciclo iterativo:

1. **Analisi del contesto**: legge i file rilevanti nel progetto
2. **Pianificazione**: determina quali file devono essere modificati
3. **Implementazione**: scrive il codice necessario in uno o più file
4. **Verifica**: esegue il codice, controlla l'output, identifica errori lint o fallimenti nei test
5. **Auto-correzione**: se qualcosa fallisce, torna al passo 3 e corregge automaticamente

```
# Flusso Agent Mode in VS Code

Prompt utente: "Aggiungi validazione input a tutti gli endpoint API nel progetto"

Agent Mode esegue:
  1. Scansiona tutti i file in src/api/
  2. Identifica 12 endpoint senza validazione
  3. Crea uno schema di validazione per ciascuno
  4. Modifica ogni endpoint per usare lo schema
  5. Esegue i test esistenti → 3 falliscono
  6. Analizza i fallimenti → mancano import
  7. Aggiunge gli import mancanti
  8. Riesegue i test → tutti verdi
  9. Presenta il diff completo per review
```

#### Attivare Agent Mode

```
# In VS Code:
# 1. Aprire Copilot Chat (Ctrl+Shift+I)
# 2. Nel selettore di modalità in alto, scegliere "Agent"
#    (le opzioni sono: Ask, Edit, Agent)
# 3. Digitare il prompt

# In JetBrains:
# Agent Mode è disponibile in Copilot Chat dalla versione GA (marzo 2026)
# Selezionare "Agent" nel menu a tendina della modalità chat
```

#### Agent Mode vs Ask Mode vs Edit Mode

| Caratteristica | Ask Mode | Edit Mode | Agent Mode |
|---------------|----------|-----------|------------|
| Scope | Singola domanda | File selezionati | Intero progetto |
| Modifica file | No (solo suggerisce) | Sì (file specifici) | Sì (multipli, auto-scelti) |
| Esecuzione comandi | No | No | Sì (terminale) |
| Auto-correzione | No | No | Sì |
| Installazione pacchetti | No | No | Sì |
| Loop iterativo | No | No | Sì |
| Uso token | Basso | Medio | Alto |

#### Esempi Pratici di Agent Mode

```
# Prompt 1: Migrazione database
> Migra il progetto da Sequelize a Prisma. Genera lo schema Prisma basandoti
  sui modelli Sequelize esistenti, aggiorna tutti i file che usano Sequelize,
  e assicurati che i test passino.

# Prompt 2: Aggiunta feature completa
> Aggiungi un sistema di notifiche email al progetto. Serve:
  - Un servizio per l'invio email con template
  - Endpoint API per gestire le preferenze di notifica
  - Migration per la tabella notification_preferences
  - Test unitari per il servizio e gli endpoint
  Usa Nodemailer per l'invio e Handlebars per i template.

# Prompt 3: Refactoring architetturale
> Refactorizza il modulo di pagamento da una singola classe monolitica
  a un pattern Strategy. Ogni metodo di pagamento (carta, PayPal, bonifico)
  deve avere la sua strategia. Mantieni la backward compatibility
  con l'interfaccia pubblica esistente.

# Prompt 4: Debugging complesso
> L'applicazione ha un memory leak che si manifesta dopo 24 ore
  di uptime. Analizza il codice in src/services/ cercando:
  - Event listener non rimossi
  - Timer non clearati
  - Connessioni database non chiuse
  - Cache senza limiti di dimensione
  Proponi fix per ogni problema trovato.
```

#### Configurazione Agent Mode per Organizzazioni

```
# Nelle policy dell'organizzazione, è possibile controllare Agent Mode:

# Organization Settings > Copilot > Policies
# Agent mode in the IDE: "Enabled" / "Disabled" / "No policy"

# Per controllare quali comandi terminale Agent Mode può eseguire:
# Organization Settings > Copilot > Policies > Agent mode
#   - Allow terminal commands: "Enabled"
#   - Command allow list: (opzionale, per limitare i comandi eseguibili)
```

### Copilot Coding Agent (Cloud Agent)

Il Copilot Coding Agent è un agente autonomo e asincrono che opera direttamente su GitHub, senza richiedere un IDE aperto. Si assegna un'issue a Copilot, e l'agente crea automaticamente un ambiente sicuro tramite GitHub Actions, implementa le modifiche, e apre una pull request in bozza.

#### Flusso di Lavoro del Coding Agent

```
                    ┌──────────────┐
                    │  Issue creata│
                    │  su GitHub   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Assegna a   │
                    │  "Copilot"   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Agent avvia │
                    │  ambiente    │
                    │  GitHub      │
                    │  Actions     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Legge le    │
                    │  istruzioni  │
                    │  del repo    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Esplora il  │
                    │  codebase    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Implementa  │
                    │  le modifiche│
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Esegue test │
                    │  e fix       │
                    │  iterativi   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Apre Draft  │
                    │  PR con      │
                    │  commit      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Esegue scan │
                    │  sicurezza   │
                    │  (CodeQL,    │
                    │  secret,     │
                    │  dependency) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Notifica lo │
                    │  sviluppatore│
                    │  per review  │
                    └──────────────┘
```

#### Attivazione e Configurazione

```bash
# Metodo 1: Assegnare un'issue a Copilot via GitHub UI
# Nella pagina dell'issue > Assignees > selezionare "Copilot"

# Metodo 2: Assegnare un'issue a Copilot via CLI
gh issue edit 42 --add-assignee @copilot

# Metodo 3: Avviare da VS Code
# In Copilot Chat con Agent Mode, digitare un prompt che richiede
# lavoro asincrono. Copilot proporrà di usare il cloud agent.

# Metodo 4: Menzione in un commento dell'issue
# Aggiungere un commento "@copilot implementa questa funzionalità"
```

#### Configurare il Coding Agent per il Repository

```yaml
# .github/copilot-coding-agent.yml
# File di configurazione opzionale per personalizzare il comportamento

# Ambiente di esecuzione
environment:
  # Immagine Docker personalizzata (opzionale)
  image: "mcr.microsoft.com/devcontainers/typescript-node:20"

  # Comandi di setup eseguiti prima che l'agente inizi a lavorare
  setup:
    - "npm ci"
    - "npx prisma generate"

  # Variabili d'ambiente (riferire segreti tramite GitHub Secrets)
  env:
    NODE_ENV: "test"
    DATABASE_URL: "${{ secrets.TEST_DATABASE_URL }}"

# Limiti
limits:
  # Tempo massimo di esecuzione (default: 60 minuti)
  max_runtime_minutes: 90

  # Numero massimo di file modificabili
  max_files_changed: 20
```

#### Casi d'Uso Ideali per il Coding Agent

Il Coding Agent eccelle nei task a complessità bassa-media in codebase ben testate:

```markdown
## Task Ideali per il Coding Agent:

### Aggiunte di Feature Semplici
- "Aggiungi un endpoint GET /api/users/:id/preferences"
- "Implementa il filtro per data nella lista ordini"
- "Aggiungi il campo 'notes' al form di creazione contatto"

### Bug Fix con Contesto Chiaro
- "Il calcolo dello sconto non considera le quantità superiori a 100"
- "L'API restituisce 500 quando il campo email è vuoto invece di 400"
- "Il timestamp delle notifiche è in UTC ma dovrebbe essere in fuso orario locale"

### Test e Documentazione
- "Aggiungi test unitari per il modulo src/services/payment.ts"
- "Aumenta la copertura test del modulo auth dal 60% all'80%"
- "Genera documentazione JSDoc per tutte le funzioni pubbliche in src/utils/"

### Refactoring Localizzato
- "Sostituisci tutte le callback con async/await nel modulo database"
- "Rinomina il campo 'user_name' in 'username' in tutto il codebase"
- "Estrai le costanti hardcoded in un file di configurazione centralizzato"

## Task NON Ideali per il Coding Agent:
- Riscrittura architetturale completa
- Decisioni di design che richiedono contesto di business
- Modifiche a infrastruttura critica di produzione
- Task che richiedono accesso a servizi esterni non configurati
```

#### Monitorare le Sessioni del Coding Agent

```bash
# Visualizzare le sessioni attive
gh api repos/{owner}/{repo}/copilot/sessions \
  --jq '.sessions[] | {
    id: .id,
    issue: .issue_number,
    status: .status,
    started_at: .started_at,
    pr_number: .pull_request_number
  }'

# I log dettagliati della sessione sono disponibili:
# - Nella pagina dell'issue (sezione "Copilot activity")
# - Nella PR generata (tab "Copilot session")
# - Nei log del workflow GitHub Actions
```

#### MCP Servers per il Coding Agent

Il Coding Agent può utilizzare server MCP (Model Context Protocol) per estendere le sue capacità:

```jsonc
// .github/copilot-mcp.json
{
  "mcpServers": {
    // Server MCP GitHub (configurato automaticamente)
    "github": {
      "type": "builtin"
    },

    // Server MCP Playwright (configurato automaticamente)
    "playwright": {
      "type": "builtin"
    },

    // Server MCP personalizzato per database di test
    "test-database": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_URL": "${{ secrets.TEST_DB_URL }}"
      }
    },

    // Server MCP per documentazione interna
    "internal-docs": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@company/docs-mcp-server"],
      "env": {
        "DOCS_API_KEY": "${{ secrets.DOCS_API_KEY }}"
      }
    }
  }
}
```

#### Custom Agents per il Coding Agent

È possibile creare agenti personalizzati con istruzioni, strumenti e server MCP specifici:

```jsonc
// .github/agents/security-fixer.json
{
  "name": "security-fixer",
  "description": "Agente specializzato nella correzione di vulnerabilità di sicurezza",
  "instructions": [
    "Sei un esperto di sicurezza applicativa.",
    "Quando correggi vulnerabilità:",
    "1. Identifica la root cause della vulnerabilità",
    "2. Applica la fix minima necessaria senza refactoring non richiesto",
    "3. Aggiungi test che verificano che la vulnerabilità sia risolta",
    "4. Aggiungi commenti che spiegano perché la fix è necessaria",
    "5. Verifica che non ci siano vulnerabilità simili in altri file"
  ],
  "mcp-servers": {
    "codeql-results": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@github/codeql-mcp-server"]
    }
  }
}
```

```jsonc
// .github/agents/docs-writer.json
{
  "name": "docs-writer",
  "description": "Agente specializzato nella documentazione tecnica",
  "instructions": [
    "Genera documentazione tecnica in italiano.",
    "Usa il formato JSDoc per JavaScript/TypeScript.",
    "Includi sempre esempi d'uso per funzioni pubbliche.",
    "Documenta i parametri, i valori di ritorno, e le eccezioni.",
    "Mantieni la documentazione concisa ma completa."
  ]
}
```

### Copilot Code Review Agentico

Da marzo 2026, Copilot Code Review utilizza un'architettura agentica basata su tool-calling. A differenza della precedente implementazione che si limitava ad analizzare il diff, il sistema agentico esplora attivamente il repository per costruire un contesto più ampio prima di generare commenti di review.

#### Architettura della Code Review Agentica

```
PR aperta con modifiche
        │
        ▼
┌─────────────────────────────────┐
│  Copilot analizza il diff       │
│  della PR                       │
└─────────┬───────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│  Tool-calling: esplora il repo  │
│  - Legge file correlati         │
│  - Traccia dipendenze cross-file│
│  - Analizza la struttura dir    │
│  - Verifica convenzioni del     │
│    codebase                     │
└─────────┬───────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│  Genera commenti di review      │
│  contestualizzati               │
│  - Bug potenziali               │
│  - Violazioni di pattern        │
│  - Suggerimenti di miglioramento│
│  - Problemi di sicurezza        │
└─────────┬───────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│  (Opzionale) Passa suggerimenti │
│  al Coding Agent per generare   │
│  una PR di fix automatica       │
└─────────────────────────────────┘
```

#### Abilitare la Code Review Agentica

```
# Metodo 1: Richiedere review su una PR
# Nella pagina della PR > Reviewers > aggiungere "Copilot"

# Metodo 2: Impostare come reviewer automatico
# Repository Settings > Rules > Rulesets
# Aggiungere un ruleset che include Copilot come reviewer obbligatorio

# Metodo 3: Via commento nella PR
# Aggiungere un commento: "@copilot review this PR"

# Metodo 4: Configurazione organizzativa
# Organization Settings > Copilot > Code review
# "Automatically request Copilot review on PRs": Enabled
```

#### Custom Instructions per Code Review

```markdown
<!-- .github/copilot-review-instructions.md -->

## Istruzioni per la Review di Copilot

### Priorità di Review
1. **Sicurezza**: Verifica input validation, SQL injection, XSS, autenticazione
2. **Correttezza**: Logica di business, edge case, gestione errori
3. **Performance**: N+1 query, loop inefficienti, caching mancante
4. **Manutenibilità**: Nomi chiari, funzioni piccole, DRY

### Convenzioni del Progetto
- Tutti i nuovi endpoint API devono avere validazione con Zod
- Le query database devono usare il repository pattern
- I servizi devono essere stateless e iniettabili
- Il coverage minimo è 80% per nuovo codice
- I messaggi di errore devono essere in italiano per l'utente e in inglese nei log

### Non Segnalare
- Differenze di stile (gestite da ESLint/Prettier)
- Commenti TODO con issue linkate
- Import non usati (gestiti dal CI)
```

#### Integrazione Code Review con Coding Agent

Quando la code review agentica trova problemi, può passare i suggerimenti direttamente al Coding Agent per generare una PR di fix:

```
Esempio di flusso integrato:

1. Sviluppatore apre una PR con 15 file modificati
2. Copilot Code Review analizza la PR
3. Trova 3 problemi:
   - Bug: race condition nel handler di concorrenza
   - Sicurezza: input non validato nell'endpoint /api/upload
   - Performance: query N+1 nel loop di caricamento ordini
4. Lo sviluppatore clicca "Apply suggestion via Copilot"
5. Il Coding Agent:
   - Crea un branch dalla PR originale
   - Implementa i 3 fix
   - Esegue i test per verificare
   - Apre una PR di fix collegata alla PR originale
6. Lo sviluppatore fa merge della PR di fix nella sua PR
```

#### Scanning di Sicurezza Integrato

Il Coding Agent esegue automaticamente tre livelli di scanning di sicurezza:

| Livello | Strumento | Cosa Verifica |
|---------|-----------|--------------|
| Analisi statica | CodeQL | Pattern di vulnerabilità nel codice sorgente |
| Secret scanning | Pattern matching + entropia | Credenziali, API key, token committati |
| Dependency review | GitHub Advisory Database | Vulnerabilità note nelle dipendenze |

```yaml
# Lo scanning è automatico, ma è possibile configurare la severità minima:
# Repository Settings > Code security > Code scanning
#   - Severity threshold: "High" (blocca la PR se trova vulnerabilità High o Critical)
#   - Auto-dismiss: "Low" (archivia automaticamente i finding Low)
```

### Selezione Multi-Modello

A partire dal 2025, GitHub ha aperto Copilot alla selezione multi-modello, permettendo agli utenti di scegliere quale modello LLM usare per diversi task. Questa flessibilità consente di ottimizzare il rapporto qualità-velocità-costo in base al tipo di attività.

#### Modelli Disponibili (Maggio 2026)

| Modello | Forza | Uso Ideale | Disponibilità |
|---------|-------|-----------|---------------|
| GPT-4.1 | Velocità | Completamento inline rapido | Tutti i piani |
| GPT-5 mini | Bilanciato | Chat e suggerimenti generali | Tutti i piani |
| GPT-5.2-Codex | Codice avanzato | Generazione codice complessa | Pro, Pro+, Business, Enterprise |
| GPT-5.4 | Ragionamento profondo | Architettura e debugging complesso | Pro+, Enterprise |
| Claude Haiku 4.5 | Velocità con qualità | Worker agent, task ripetitivi | Tutti i piani |
| Claude Sonnet 4.5 | Coding bilanciato | Sviluppo quotidiano | Pro, Pro+, Business, Enterprise |
| Claude Sonnet 4.6 | Coding avanzato | Refactoring e debug multi-file | Pro+, Enterprise |
| Claude Opus 4.5 | Ragionamento massimo | Architettura e analisi profonda | Pro+, Enterprise |
| Gemini 2.5 Pro | Contesto ampio | Codebase grandi, documentazione | Pro, Pro+, Business, Enterprise |
| Gemini 3 Flash | Ultra veloce | Boilerplate, generazione rapida | Pro+, Enterprise |

#### Cambiare Modello

```
# In VS Code / JetBrains:
# In basso a sinistra nella finestra di Copilot Chat, cliccare sul nome del modello
# Selezionare il modello desiderato dal menu

# Impostare Auto (selezione automatica):
# Selezionare "Auto" nel selettore modello
# Copilot sceglierà il modello ottimale per il tipo di richiesta
# Vantaggio: 10% di sconto sui premium request multiplier
```

#### Strategia di Selezione Modello per Team

```markdown
## Raccomandazioni per la selezione modello in team:

### Sviluppo Quotidiano (completamento inline)
- **Modello consigliato**: Auto o GPT-4.1
- **Motivo**: velocità massima, latenza minima, costo basso

### Chat e Spiegazioni
- **Modello consigliato**: Claude Sonnet 4.5 o GPT-5.2-Codex
- **Motivo**: buon equilibrio tra qualità delle risposte e velocità

### Debugging Complesso
- **Modello consigliato**: Claude Opus 4.5 o GPT-5.4
- **Motivo**: ragionamento profondo necessario per tracciare bug complessi

### Code Review
- **Modello consigliato**: Claude Sonnet 4.6
- **Motivo**: eccellente nel trovare bug sottili e suggerire miglioramenti

### Documentazione e Test
- **Modello consigliato**: Gemini 2.5 Pro
- **Motivo**: contesto ampio, buono per comprendere intere classi/moduli

### Generazione Rapida di Boilerplate
- **Modello consigliato**: Gemini 3 Flash o Claude Haiku 4.5
- **Motivo**: velocità estrema per codice ripetitivo/template
```

#### Policy Organizzative per i Modelli

```
# Organization Settings > Copilot > Policies > Model selection

# Opzione 1: Permettere tutti i modelli
# Model selection policy: "No policy" (ogni utente sceglie liberamente)

# Opzione 2: Limitare i modelli disponibili
# Model selection policy: "Selected models only"
# Modelli abilitati:
#   ☑ GPT-4.1
#   ☑ GPT-5.2-Codex
#   ☑ Claude Sonnet 4.5
#   ☐ Claude Opus 4.5 (disabilitato per contenere i costi)
#   ☐ GPT-5.4 (disabilitato per contenere i costi)
#   ☑ Auto

# Opzione 3: Forzare un modello specifico
# Model selection policy: "Single model"
# Modello forzato: GPT-5.2-Codex
# Nota: scelta limitante, sconsigliata nella maggior parte dei casi
```

### Copilot Extensions e MCP

Le Copilot Extensions permettono a strumenti di terze parti di integrarsi direttamente nell'interfaccia chat di Copilot. Tramite il protocollo MCP (Model Context Protocol), è possibile connettere Copilot a qualsiasi sorgente dati o strumento esterno.

#### Architettura MCP

```
┌─────────────────────────────────────────────────────┐
│                 GitHub Copilot Chat                   │
│  "Quale lo stato del deploy su staging?"             │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              MCP Client (in Copilot)                 │
│  Seleziona il server MCP appropriato                 │
└───────────────────────┬─────────────────────────────┘
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ MCP      │ │ MCP      │ │ MCP      │
    │ Server   │ │ Server   │ │ Server   │
    │ GitHub   │ │ Deploy   │ │ Database │
    │ (builtin)│ │ (custom) │ │ (custom) │
    └──────────┘ └──────────┘ └──────────┘
```

#### Configurare MCP in VS Code

```jsonc
// .vscode/mcp.json
{
  "servers": {
    // Server MCP per PostgreSQL - query di sviluppo
    "dev-postgres": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://dev:dev@localhost:5432/devdb"
      ]
    },

    // Server MCP per filesystem
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/workspace/docs"
      ]
    },

    // Server MCP per Sentry (error tracking)
    "sentry": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@sentry/mcp-server"],
      "env": {
        "SENTRY_AUTH_TOKEN": "${env:SENTRY_AUTH_TOKEN}"
      }
    },

    // Server MCP personalizzato per API interne
    "internal-api": {
      "type": "sse",
      "url": "https://mcp.internal.company.com/sse",
      "headers": {
        "Authorization": "Bearer ${env:INTERNAL_API_TOKEN}"
      }
    }
  }
}
```

#### Utilizzo di MCP con Copilot Chat

```
# Con i server MCP configurati, si possono fare richieste come:

# Query al database di sviluppo
> Mostra le ultime 10 righe della tabella users create oggi

# Analisi errori da Sentry
> Quali sono gli errori più frequenti nelle ultime 24 ore in produzione?

# Verifica stato deploy
> Qual è lo stato dell'ultimo deploy su staging?

# Documentazione interna
> Cerca nella documentazione interna le specifiche dell'API di pagamento
```

#### Copilot Extensions di Terze Parti

```markdown
## Extensions Disponibili (Maggio 2026)

### DevOps e CI/CD
- **Docker**: gestione container e immagini da chat
- **Azure**: deploy e gestione risorse Azure
- **Datadog**: query metriche e analisi performance

### Database
- **MongoDB**: query e analisi dati MongoDB
- **Supabase**: gestione database e auth Supabase

### Project Management
- **Jira**: creazione e aggiornamento issue Jira
- **Linear**: gestione task Linear

### Documentazione
- **Notion**: ricerca e aggiornamento pagine Notion
- **Confluence**: accesso alla knowledge base aziendale

### Sicurezza
- **Snyk**: analisi vulnerabilità delle dipendenze
- **SonarQube**: analisi qualità del codice

# Nota: le Extensions attualmente funzionano solo in Ask Mode,
# non in Agent Mode. L'integrazione con Agent Mode è prevista.
```

### Custom Instructions

Le Custom Instructions permettono di personalizzare il comportamento di Copilot a livello di repository, organizzazione, o utente personale. Copilot legge queste istruzioni e le applica automaticamente a ogni interazione.

#### Istruzioni a Livello di Repository

```markdown
<!-- .github/copilot-instructions.md -->

## Progetto: E-Commerce Backend

### Tecnologie
- Runtime: Node.js 20 LTS con TypeScript 5.4
- Framework: NestJS 10
- Database: PostgreSQL 16 con Prisma 5
- Cache: Redis 7
- Test: Jest con supertest per e2e

### Convenzioni di Codice
- Usa sempre `async/await`, mai callback o `.then()`
- Tutti i servizi devono essere iniettabili via DI di NestJS
- Le response API devono seguire il formato: `{ success, data, error, meta }`
- Tutte le query devono essere parametrizzate (mai string interpolation)
- I nomi delle variabili e dei metodi sono in camelCase inglese
- I commenti nel codice sono in inglese
- La documentazione utente è in italiano

### Sicurezza
- Input validation obbligatoria con class-validator su ogni DTO
- Autenticazione via JWT con refresh token rotation
- Rate limiting su tutti gli endpoint pubblici
- CORS configurato per domini specifici, mai wildcard in produzione

### Pattern Architetturali
- Repository pattern per l'accesso ai dati
- CQRS per le operazioni complesse
- Event-driven per le notifiche
- Circuit breaker per le chiamate a servizi esterni

### Test
- Coverage minimo: 80% per unit test
- Ogni nuovo endpoint deve avere almeno 1 test e2e
- Usare factory pattern per i dati di test (no dati hardcoded)
```

#### Istruzioni per File Specifici

```markdown
<!-- .github/instructions/api-endpoints.instructions.md -->
---
applyTo: "src/modules/**/controllers/*.ts"
---

## Istruzioni per i Controller API

Quando generi o modifichi un controller NestJS:

1. Ogni metodo del controller deve avere:
   - Decoratore `@ApiOperation` con summary e description
   - Decoratore `@ApiResponse` per i codici 200, 400, 401, 404
   - Validazione del body con `@Body() dto: ClassValidator`
   - Gestione errori con `HttpException`

2. Formato della response:
   ```typescript
   return {
     success: true,
     data: result,
     meta: { timestamp: new Date().toISOString() }
   };
   ```

3. Logging: ogni endpoint deve loggar l'ingresso con il livello `debug`
```

```markdown
<!-- .github/instructions/database-queries.instructions.md -->
---
applyTo: "src/modules/**/repositories/*.ts"
---

## Istruzioni per i Repository

1. Usa sempre Prisma client, mai query SQL raw
2. Includi `select` esplicito per evitare di caricare campi non necessari
3. Per le liste, includi sempre paginazione con `skip` e `take`
4. Wrap ogni operazione di scrittura in una transazione
5. Usa `findUniqueOrThrow` e `findFirstOrThrow` quando l'entità deve esistere
```

#### Priorità delle Custom Instructions

```
Le istruzioni vengono applicate in questo ordine di priorità (dalla più alta):

1. Istruzioni personali dell'utente (configurate in VS Code Settings)
2. Istruzioni del repository (.github/copilot-instructions.md)
3. Istruzioni specifiche per file (.github/instructions/*.instructions.md)
4. Istruzioni dell'organizzazione (configurate dall'admin)

In caso di conflitto, le istruzioni con priorità più alta prevalgono.
```

#### Istruzioni per Copilot CLI

```markdown
<!-- ~/.config/gh-copilot/instructions.md -->

## Istruzioni per Copilot CLI

### Contesto Operativo
- Sistema operativo: Ubuntu 22.04 LTS
- Shell: Bash 5.1 con Starship prompt
- Container runtime: Docker con Podman come fallback
- Orchestratore: Kubernetes 1.29 con kubectl e helm

### Preferenze
- Preferisci comandi POSIX-compliant quando possibile
- Usa `jq` per il parsing JSON
- Usa `ripgrep` (rg) invece di grep
- Suggerisci sempre l'opzione `--dry-run` per comandi distruttivi
- Mostra il flag `--help` quando il comando ha opzioni complesse
```

### GitHub Spark

GitHub Spark è una piattaforma che permette di creare applicazioni funzionali partendo da descrizioni in linguaggio naturale. A differenza degli strumenti che generano solo UI statica, Spark costruisce applicazioni complete con frontend React/TypeScript e backend con capacità LLM integrate.

#### Caratteristiche Principali

```markdown
## Capacità di GitHub Spark

### Cosa Può Fare
- Generare applicazioni web complete da prompt in linguaggio naturale
- Creare UI interattive con React e TypeScript
- Integrare nativamente con GitHub Models per funzionalità AI
- Sincronizzare il codice con un GitHub Codespace per editing avanzato
- Gestire dati persistenti senza configurare database
- Deploy automatico con URL accessibile

### Stack Tecnico Generato
- Frontend: TypeScript + React
- Styling: Tailwind CSS
- Backend: Functions serverless
- AI: GitHub Models (GPT-4, Claude, etc.)
- Storage: Key-value store integrato

### Disponibilità
- Copilot Pro+: $39/mese (preview pubblica)
- Copilot Enterprise: $39/utente/mese (preview pubblica)
- Non disponibile su: Free, Pro, Business
```

#### Esempi di Prompt per Spark

```
# Prompt 1: Dashboard analitica
> Crea una dashboard che mostra le metriche di un team di sviluppo:
  - Numero di PR aperte, in review, e chiuse questa settimana
  - Grafico a barre del tempo medio di merge per membro del team
  - Lista delle PR più vecchie ancora aperte
  Usa colori pastello e un layout a griglia responsive.

# Prompt 2: Tool interno
> Crea un'app per tracciare le richieste di ferie del team.
  Deve avere:
  - Form per richiedere ferie (data inizio, data fine, tipo)
  - Calendario che mostra le ferie approvate
  - Dashboard per il manager con pulsanti approva/rifiuta
  - Contatore dei giorni rimanenti per persona

# Prompt 3: Utility con AI
> Crea un'app che prende un testo tecnico in inglese e lo traduce
  in italiano mantenendo la terminologia tecnica invariata.
  Deve mostrare il testo originale e tradotto fianco a fianco,
  con evidenziazione dei termini tecnici preservati.
```

### Piani e Pricing Copilot 2026

Il pricing di GitHub Copilot ha subito una trasformazione significativa nel 2026, passando da un modello a richieste fisse a un modello basato sull'utilizzo.

#### Piani Disponibili (Maggio 2026)

| Piano | Prezzo | AI Credits Inclusi | Destinazione |
|-------|--------|-------------------|-------------|
| **Free** | $0 | Limitato (2000 completamenti, 50 chat) | Sviluppatori individuali |
| **Pro** | $10/mese | $10 di crediti AI mensili | Sviluppatori individuali |
| **Pro+** | $39/mese | $39 di crediti AI mensili | Sviluppatori individuali avanzati |
| **Business** | $19/utente/mese | $19 di crediti AI per utente | Organizzazioni |
| **Enterprise** | $39/utente/mese | $39 di crediti AI per utente | Enterprise con governance |
| **Student** | $0 | Come Pro | Studenti verificati |

#### Transizione alla Fatturazione Basata sull'Utilizzo

A partire dal 1 giugno 2026, tutti i piani Copilot passano alla fatturazione basata sull'utilizzo (usage-based billing):

```markdown
## Come Funziona il Nuovo Billing

### Credits AI
- Ogni piano include un monte di crediti AI mensili
- I crediti vengono consumati in base all'utilizzo effettivo
- L'utilizzo è calcolato in base al consumo di token (input + output + cached)
- Ogni modello ha un "premium multiplier" che indica il costo relativo

### Cosa NON consuma crediti
- Completamenti inline di codice (illimitati su tutti i piani a pagamento)
- Next Edit Suggestions (illimitati)
- Queste funzionalità core rimangono illimitate per i piani a pagamento

### Cosa consuma crediti
- Chat (ogni messaggio consuma crediti in base al modello usato)
- Agent Mode (consumo più elevato per il loop iterativo)
- Coding Agent (consumo basato sulla durata e complessità)
- Code Review (consumo moderato per analisi)

### Premium Multiplier per Modello (esempio)
| Modello | Multiplier | Note |
|---------|-----------|------|
| GPT-4.1 | 1x | Base |
| Claude Sonnet 4.5 | 1x | Base |
| GPT-5.2-Codex | 2x | Premium |
| Claude Opus 4.5 | 3x | Premium |
| Auto | 0.9x | Sconto 10% |

### Acquistare Crediti Aggiuntivi
- I crediti aggiuntivi si acquistano automaticamente se l'admin lo abilita
- Il costo dei crediti aggiuntivi dipende dal piano
- È possibile impostare un limite mensile per evitare sorprese
```

#### Confronto tra i Piani

| Funzionalità | Free | Pro | Pro+ | Business | Enterprise |
|-------------|------|-----|------|----------|-----------|
| Completamento inline | Limitato | Illimitato | Illimitato | Illimitato | Illimitato |
| Chat | 50 msg | Sì | Sì | Sì | Sì |
| Agent Mode | No | Sì | Sì | Sì | Sì |
| Coding Agent | No | Sì | Sì | Sì | Sì |
| Code Review | No | Sì | Sì | Sì | Sì |
| Multi-modello | GPT-4.1 | Selezionati | Tutti | Selezionati | Tutti |
| Spark | No | No | Sì | No | Sì |
| Custom Instructions | No | Sì | Sì | Sì | Sì |
| Content Exclusion | No | No | No | Sì | Sì |
| Policy organizzative | No | No | No | Sì | Sì |
| Audit log Copilot | No | No | No | No | Sì |
| Knowledge base | No | No | No | No | Sì |
| SAML SSO | No | No | No | Sì | Sì |
| Data Residency | No | No | No | No | Sì |

#### Monitorare il Consumo dei Crediti

```bash
# Visualizzare il consumo dei crediti per l'organizzazione
gh api orgs/{org}/copilot/billing/usage \
  --jq '{
    total_credits_used: .total_credits_used,
    credits_remaining: .credits_remaining,
    billing_period_end: .billing_period_end,
    top_users: [.users[:10][] | {
      login: .login,
      credits_used: .credits_used,
      primary_model: .most_used_model
    }]
  }'

# Impostare alert sul consumo
# Organization Settings > Billing > Copilot > Usage alerts
# Alert at: 80% of monthly credits
# Notify: billing-admins@company.com

# Impostare limite di spesa per crediti aggiuntivi
# Organization Settings > Billing > Copilot > Spending limit
# Additional credits limit: $200/month
```

---

## GitHub Codespaces

GitHub Codespaces fornisce ambienti di sviluppo completi nel cloud, accessibili dal browser o da VS Code locale. Ogni Codespace è un container Docker personalizzabile con tutto il necessario per sviluppare: editor, runtime, tool, estensioni, e configurazione dell'ambiente.

### Configurazione devcontainer.json

Il file `devcontainer.json` definisce l'ambiente del Codespace. È la "ricetta" per creare un ambiente di sviluppo riproducibile.

#### Configurazione Base

```jsonc
// .devcontainer/devcontainer.json
{
  // Nome visualizzato
  "name": "Progetto Full-Stack",

  // Immagine Docker base
  "image": "mcr.microsoft.com/devcontainers/typescript-node:20-bullseye",

  // Oppure usare un Dockerfile personalizzato:
  // "build": {
  //   "dockerfile": "Dockerfile",
  //   "context": "..",
  //   "args": {
  //     "NODE_VERSION": "20",
  //     "VARIANT": "bullseye"
  //   }
  // },

  // Oppure Docker Compose:
  // "dockerComposeFile": "docker-compose.yml",
  // "service": "app",
  // "workspaceFolder": "/workspace",

  // Feature aggiuntive (tool preconfigurati)
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {
      "version": "latest",
      "moby": true
    },
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.12"
    },
    "ghcr.io/devcontainers/features/aws-cli:1": {},
    "ghcr.io/devcontainers/features/terraform:1": {
      "version": "1.7"
    },
    "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": {
      "version": "latest"
    },
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },

  // Comandi da eseguire durante la creazione
  "onCreateCommand": "npm install && npm run build",

  // Comandi da eseguire dopo l'attach
  "postAttachCommand": "npm run dev &",

  // Comandi da eseguire ad ogni avvio
  "postStartCommand": "git fetch --all",

  // Porte da forwardare automaticamente
  "forwardPorts": [3000, 5432, 6379],

  // Configurazione delle porte
  "portsAttributes": {
    "3000": {
      "label": "Frontend",
      "onAutoForward": "notify",
      "visibility": "public"
    },
    "5432": {
      "label": "PostgreSQL",
      "onAutoForward": "silent",
      "visibility": "private"
    },
    "6379": {
      "label": "Redis",
      "onAutoForward": "silent",
      "visibility": "private"
    }
  },

  // Estensioni VS Code
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "bradlc.vscode-tailwindcss",
        "ms-python.python",
        "ms-azuretools.vscode-docker",
        "github.copilot",
        "github.copilot-chat",
        "eamodio.gitlens",
        "streetsidesoftware.code-spell-checker",
        "streetsidesoftware.code-spell-checker-italian"
      ],
      "settings": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.rulers": [80, 120],
        "typescript.preferences.importModuleSpecifier": "relative",
        "files.eol": "\n",
        "terminal.integrated.defaultProfile.linux": "bash"
      }
    },
    "jetbrains": {
      "plugins": [
        "com.intellij.plugins.html.instantEdit"
      ]
    }
  },

  // Variabili d'ambiente
  "containerEnv": {
    "NODE_ENV": "development",
    "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/devdb",
    "REDIS_URL": "redis://localhost:6379"
  },

  // Utente non-root
  "remoteUser": "vscode",

  // Montare segreti GitHub Codespaces
  "secrets": {
    "NPM_TOKEN": {
      "description": "Token per il registry npm privato"
    },
    "AWS_ACCESS_KEY_ID": {
      "description": "AWS Access Key per deploy"
    }
  },

  // Requisiti hardware
  "hostRequirements": {
    "cpus": 4,
    "memory": "8gb",
    "storage": "32gb"
  }
}
```

#### Configurazione con Docker Compose

```jsonc
// .devcontainer/devcontainer.json
{
  "name": "Full Stack con Servizi",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  "forwardPorts": [3000, 5432, 6379, 8080],
  "postCreateCommand": "npm install",
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "github.copilot"
      ]
    }
  }
}
```

```yaml
# .devcontainer/docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ../..:/workspaces:cached
    command: sleep infinity
    network_mode: service:db
    depends_on:
      - db
      - redis
      - minio

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: devdb
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio-data:/data

volumes:
  postgres-data:
  minio-data:
```

```dockerfile
# .devcontainer/Dockerfile
FROM mcr.microsoft.com/devcontainers/typescript-node:20-bullseye

# Installare tool aggiuntivi
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
       postgresql-client \
       redis-tools \
       httpie \
       jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installare tool globali Node
RUN su vscode -c "npm install -g \
    typescript \
    ts-node \
    nodemon \
    prisma \
    @nestjs/cli"

# Copiare script di setup
COPY setup.sh /usr/local/bin/setup.sh
RUN chmod +x /usr/local/bin/setup.sh
```

### Prebuilds

I Prebuilds sono Codespace pre-costruiti che eliminano il tempo di attesa per l'installazione delle dipendenze e la configurazione dell'ambiente. Quando uno sviluppatore apre un Codespace, trova già tutto pronto.

```
Senza prebuild:
  Apri Codespace → Scarica immagine (2min) → npm install (3min) → Build (2min) → Pronto (7 min)

Con prebuild:
  Apri Codespace → Pronto (30 secondi)
```

#### Configurazione Prebuilds

```
Repository Settings > Codespaces > Set up prebuild

Configuration:
  - Branch: main (e/o develop, release/*)
  - Configuration file: .devcontainer/devcontainer.json
  - Trigger: On push to branch, On configuration change
  - Region: Europe West (scegliere la regione più vicina al team)

Advanced:
  - Template reduction: Enabled (riduce i costi)
  - Retention: 2 versions (mantiene le ultime 2 versioni)
```

#### Prebuild con GitHub Actions

```yaml
# .github/workflows/codespace-prebuild.yml
name: Codespace Prebuild

on:
  push:
    branches: [main, develop]
    paths:
      - '.devcontainer/**'
      - 'package.json'
      - 'package-lock.json'
      - 'requirements.txt'
  schedule:
    - cron: '0 6 * * 1-5'  # Lun-Ven alle 6:00 UTC

jobs:
  prebuild:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validare devcontainer.json
        run: |
          # Verificare che il file sia JSON valido
          python3 -c "
          import json
          with open('.devcontainer/devcontainer.json') as f:
              content = f.read()
              # Rimuovere commenti JSONC
              import re
              content = re.sub(r'//.*?\n', '\n', content)
              content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
              json.loads(content)
          print('devcontainer.json è valido')
          "
```

### Dotfiles e Personalizzazione

Ogni sviluppatore può personalizzare i propri Codespace usando un repository di dotfiles.

```
# Configurazione: Settings > Codespaces > Dotfiles
# Repository: username/dotfiles
# Auto-install: enabled
```

```bash
# Struttura tipica di un repository dotfiles per Codespaces
dotfiles/
├── install.sh          # Script eseguito automaticamente
├── .bashrc
├── .bash_aliases
├── .gitconfig
├── .vimrc
├── .tmux.conf
└── .config/
    └── starship.toml
```

```bash
#!/bin/bash
# install.sh - Script di installazione dotfiles

set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Installazione dotfiles ==="

# Symlink dei dotfiles
for file in .bashrc .bash_aliases .gitconfig .vimrc .tmux.conf; do
  if [ -f "$DOTFILES_DIR/$file" ]; then
    ln -sf "$DOTFILES_DIR/$file" "$HOME/$file"
    echo "Linked $file"
  fi
done

# Configurazione directory
mkdir -p "$HOME/.config"
if [ -d "$DOTFILES_DIR/.config/starship.toml" ]; then
  ln -sf "$DOTFILES_DIR/.config/starship.toml" "$HOME/.config/starship.toml"
fi

# Installare tool aggiuntivi
if command -v apt-get &>/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq \
    tmux \
    htop \
    ripgrep \
    fd-find \
    bat \
    fzf
fi

# Installare Starship prompt
if ! command -v starship &>/dev/null; then
  curl -sS https://starship.rs/install.sh | sh -s -- -y
  echo 'eval "$(starship init bash)"' >> ~/.bashrc
fi

# Configurazione Git
git config --global core.editor "code --wait"
git config --global pull.rebase true
git config --global init.defaultBranch main

echo "=== Dotfiles installati ==="
```

### Port Forwarding

Codespaces supporta il forwarding automatico delle porte, permettendo di accedere ai servizi in esecuzione nel Codespace dal browser locale o dall'IDE.

```bash
# Visualizzare le porte forwardate
gh codespace ports

# Output:
# LABEL       PORT  VISIBILITY  BROWSE URL
# Frontend    3000  public      https://username-repo-abc123-3000.preview.app.github.dev
# API         8080  private     https://username-repo-abc123-8080.preview.app.github.dev
# PostgreSQL  5432  private     -

# Cambiare la visibilità di una porta
gh codespace ports visibility 3000:public -c codespace-name
gh codespace ports visibility 5432:private -c codespace-name

# Forwarding manuale di una porta aggiuntiva
gh codespace ports forward 9090:9090 -c codespace-name
```

Le visibilità delle porte sono:

| Visibilità | Chi può accedere |
|-----------|------------------|
| `private` | Solo il proprietario del Codespace (richiede autenticazione GitHub) |
| `org` | Membri dell'organizzazione GitHub |
| `public` | Chiunque con l'URL (utile per demo, webhook di test) |

### Gestione Costi Codespaces

#### Pricing

| Tipo Macchina | CPU | RAM | Storage | Costo/ora |
|--------------|-----|-----|---------|-----------|
| 2-core | 2 | 8 GB | 32 GB | $0.18 |
| 4-core | 4 | 16 GB | 32 GB | $0.36 |
| 8-core | 8 | 32 GB | 64 GB | $0.72 |
| 16-core | 16 | 64 GB | 128 GB | $1.44 |
| 32-core | 32 | 128 GB | 128 GB | $2.88 |

Storage aggiuntivo: $0.07/GB/mese

#### Strategie di Riduzione Costi

```
# Organization Settings > Codespaces > Spending limit

# Impostare un limite mensile
Spending limit: $500/month

# Impostare policy per la dimensione delle macchine
Machine type policy:
  - Maximum machine type: 8-core (impedisce l'uso di macchine più grandi)

# Timeout di inattività (default 30 minuti)
Default idle timeout: 15 minutes

# Retention period (quanti giorni un Codespace inattivo viene mantenuto prima della cancellazione)
Default retention period: 14 days
```

```bash
# Monitorare l'uso dei Codespace nell'organizzazione
gh api orgs/{org}/codespaces \
  --jq '.codespaces[] | {
    owner: .owner.login,
    name: .name,
    machine: .machine.display_name,
    state: .state,
    created: .created_at,
    last_used: .last_used_at
  }'

# Fermare Codespace inattivi
gh codespace list --org org-name | while read -r name owner _; do
  LAST_USED=$(gh codespace view "$name" --json lastUsedAt -q '.lastUsedAt')
  DAYS_INACTIVE=$(( ($(date +%s) - $(date -d "$LAST_USED" +%s)) / 86400 ))

  if [ "$DAYS_INACTIVE" -gt 7 ]; then
    echo "Stopping inactive codespace: $name (owner: $owner, inactive: ${DAYS_INACTIVE}d)"
    gh codespace stop -c "$name"
  fi
done
```

### Confronto con Sviluppo Locale

| Aspetto | Sviluppo Locale | GitHub Codespaces |
|---------|----------------|-------------------|
| Setup iniziale | Ore/giorni | Minuti |
| Onboarding nuovi dev | Complesso | Istantaneo |
| Consistenza ambiente | Variabile | Identica per tutti |
| Costo | Hardware una tantum | Pay-per-use |
| Performance rete | Piena | Latenza aggiuntiva |
| Offline | Sì | No |
| File locali | Accesso diretto | Upload/download |
| GPU | Se disponibile localmente | Non disponibile |
| Dimensione progetto | Illimitata | Limitata dallo storage |
| Sicurezza codice | Locale | Nel cloud GitHub |
| Configurazione IDE | Piena libertà | VS Code + limitazioni |

**Quando usare Codespaces**: Onboarding, contributi open source, team distribuiti, macchine diverse, ambienti complessi con molte dipendenze.

**Quando preferire locale**: Progetti con requisiti GPU, lavoro offline frequente, preferenza per IDE non VS Code, costi ridotti per uso intensivo.

### GPU e Machine Learning in Codespaces

GitHub Codespaces ha offerto per un periodo limitato macchine virtuali con GPU (basate su Azure NCv3-series) per carichi di lavoro di machine learning e data science. Questa offerta è stata deprecata il 29 agosto 2025 a causa del ritiro delle VM NCv3-series da parte di Azure il 30 settembre 2025.

#### Stato Attuale della GPU in Codespaces

```markdown
## Timeline GPU in Codespaces

- 2023-2024: GPU disponibile in trial limitato per clienti selezionati
- Agosto 2025: Annuncio deprecazione delle macchine GPU
- 29 agosto 2025: Fine del supporto GPU in Codespaces
- Settembre 2025: Ritiro delle VM NCv3-series da Azure

## Alternative per Workload ML/AI

### Opzione 1: Sviluppo Locale con GPU
- Usare Codespaces per il codice e sincronizzare con la macchina locale per il training
- Pro: costo zero per la GPU, performance nativa
- Contro: richiede hardware locale

### Opzione 2: Servizi Cloud ML
- Usare Codespaces per sviluppo e cloud ML per training:
  - Azure ML Workspace
  - AWS SageMaker
  - Google Vertex AI
- Pro: GPU on-demand, scalabile
- Contro: costi variabili, latenza

### Opzione 3: GitHub Actions con Runner GPU
- Configurare self-hosted runner con GPU per eseguire notebook e training
- Pro: integrato con CI/CD
- Contro: richiede manutenzione del runner
```

#### Configurazione per Data Science (senza GPU)

```jsonc
// .devcontainer/devcontainer.json per data science
{
  "name": "Data Science Environment",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",

  "features": {
    "ghcr.io/devcontainers/features/conda:1": {},
    "ghcr.io/devcontainers/features/node:1": {
      "version": "20"
    }
  },

  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-toolsai.jupyter",
        "ms-toolsai.datawrangler",
        "github.copilot",
        "github.copilot-chat"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/opt/conda/bin/python",
        "jupyter.askForKernelRestart": false,
        "notebook.output.textLineLimit": 500
      }
    }
  },

  "postCreateCommand": "pip install pandas numpy scikit-learn matplotlib seaborn plotly jupyterlab torch --index-url https://download.pytorch.org/whl/cpu",

  "forwardPorts": [8888],
  "portsAttributes": {
    "8888": {
      "label": "JupyterLab",
      "onAutoForward": "openBrowser"
    }
  },

  "hostRequirements": {
    "cpus": 8,
    "memory": "32gb",
    "storage": "64gb"
  }
}
```

### Lifecycle Hooks Avanzati

Il sistema di lifecycle hooks di devcontainer permette di eseguire comandi in momenti precisi del ciclo di vita del container. Comprendere l'ordine di esecuzione è fondamentale per configurazioni complesse.

#### Ordine di Esecuzione dei Lifecycle Hooks

```
┌─────────────────────────────────────────────────────────┐
│  FASE 1: CREAZIONE DEL CONTAINER                         │
│                                                          │
│  1. initializeCommand                                    │
│     → Eseguito sulla macchina HOST, prima del container  │
│     → Uso: validazione prerequisiti, download asset       │
│                                                          │
│  2. onCreateCommand                                      │
│     → Eseguito DENTRO il container alla prima creazione  │
│     → Uso: installare dipendenze, compilare, migrare DB  │
│     → Eseguito UNA SOLA volta per Codespace              │
│                                                          │
│  3. updateContentCommand                                 │
│     → Eseguito quando il contenuto del repo cambia       │
│     → Uso: aggiornare dipendenze, ricompilare            │
│     → Eseguito dopo onCreateCommand e ad ogni rebuild     │
│                                                          │
│  4. postCreateCommand                                    │
│     → Eseguito dopo onCreateCommand + updateContent      │
│     → Uso: setup finale che richiede che tutto sia pronto│
│                                                          │
│  FASE 2: AVVIO DEL CONTAINER                             │
│                                                          │
│  5. postStartCommand                                     │
│     → Eseguito ad OGNI avvio del Codespace               │
│     → Uso: avviare servizi, sincronizzare stato           │
│                                                          │
│  6. postAttachCommand                                    │
│     → Eseguito quando un client si connette               │
│     → Uso: comandi specifici per la sessione utente       │
│                                                          │
│  FASE 3: ARRESTO                                         │
│                                                          │
│  7. shutdownAction (configurazione, non comando)          │
│     → "none": il container resta attivo                   │
│     → "stopContainer": il container viene fermato         │
└─────────────────────────────────────────────────────────┘
```

#### Esempio Completo con Tutti i Lifecycle Hooks

```jsonc
// .devcontainer/devcontainer.json
{
  "name": "Full Lifecycle Example",
  "image": "mcr.microsoft.com/devcontainers/typescript-node:20-bullseye",

  // 1. Eseguito sull'host prima della creazione del container
  "initializeCommand": "echo 'Verifico prerequisiti...' && docker --version",

  // 2. Eseguito alla prima creazione (può essere un object per comandi paralleli)
  "onCreateCommand": {
    "install-deps": "npm ci",
    "generate-prisma": "npx prisma generate",
    "setup-db": "npx prisma db push --accept-data-loss"
  },

  // 3. Eseguito quando il contenuto del repository cambia
  "updateContentCommand": "npm ci && npm run build",

  // 4. Eseguito dopo che tutto il setup è completato
  "postCreateCommand": {
    "seed-db": "npx prisma db seed",
    "verify-setup": "npm test -- --bail --silent"
  },

  // 5. Eseguito ad ogni avvio del Codespace
  "postStartCommand": {
    "start-services": "npm run dev &",
    "sync-git": "git fetch --all --prune"
  },

  // 6. Eseguito quando l'utente si connette
  "postAttachCommand": "echo '=== Ambiente pronto. Buon lavoro! ==='",

  // Comportamento all'arresto
  "shutdownAction": "stopContainer"
}
```

#### Lifecycle Hooks nelle Features

Le features di devcontainer possono contribuire i propri lifecycle hooks. I comandi delle features vengono eseguiti PRIMA dei comandi definiti dall'utente in devcontainer.json:

```
Ordine di esecuzione per onCreateCommand:
  1. Feature A: onCreateCommand (ordine di installazione della feature)
  2. Feature B: onCreateCommand
  3. devcontainer.json: onCreateCommand (definito dall'utente)
```

### Multi-Repository e Monorepo

Per progetti che coinvolgono più repository o monorepo, Codespaces offre pattern specifici.

#### Pattern Multi-Repository

```jsonc
// .devcontainer/devcontainer.json per multi-repo
{
  "name": "Multi-Repo Workspace",
  "image": "mcr.microsoft.com/devcontainers/typescript-node:20",

  // Clonare repository aggiuntivi al setup
  "initializeCommand": ".devcontainer/clone-repos.sh",

  "postCreateCommand": {
    "install-main": "npm ci",
    "install-shared": "cd ../shared-libs && npm ci",
    "install-proto": "cd ../api-proto && npm ci",
    "link-packages": "npm link ../shared-libs ../api-proto"
  },

  // Workspace multi-root
  "customizations": {
    "vscode": {
      "settings": {
        "workbench.experimental.multiRoot": true
      }
    }
  }
}
```

```bash
#!/bin/bash
# .devcontainer/clone-repos.sh
# Clona i repository correlati nella stessa directory parent

PARENT_DIR="$(dirname "$PWD")"

# Clonare le librerie condivise se non esistono
if [ ! -d "$PARENT_DIR/shared-libs" ]; then
  git clone https://github.com/org/shared-libs.git "$PARENT_DIR/shared-libs"
fi

# Clonare le definizioni delle API protobuf
if [ ! -d "$PARENT_DIR/api-proto" ]; then
  git clone https://github.com/org/api-proto.git "$PARENT_DIR/api-proto"
fi
```

#### Pattern Monorepo

```jsonc
// .devcontainer/devcontainer.json per monorepo con Turborepo/Nx
{
  "name": "Monorepo Workspace",
  "image": "mcr.microsoft.com/devcontainers/typescript-node:20",

  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/python:1": { "version": "3.12" }
  },

  // Installare tutte le dipendenze del monorepo
  "onCreateCommand": {
    "install": "npm ci",
    "build-packages": "npx turbo build --filter='./packages/*'",
    "generate": "npx turbo generate --filter='./apps/*'"
  },

  "postStartCommand": {
    "dev-frontend": "npx turbo dev --filter=@org/web &",
    "dev-backend": "npx turbo dev --filter=@org/api &"
  },

  "forwardPorts": [3000, 4000, 5432],
  "portsAttributes": {
    "3000": { "label": "Web App", "onAutoForward": "notify" },
    "4000": { "label": "API Server", "onAutoForward": "silent" },
    "5432": { "label": "PostgreSQL", "onAutoForward": "silent" }
  },

  // Requisiti più elevati per monorepo
  "hostRequirements": {
    "cpus": 8,
    "memory": "16gb",
    "storage": "64gb"
  }
}
```

### Sicurezza e Hardening Codespaces

La sicurezza dei Codespaces è critica perché il codice e i segreti risiedono nel cloud. Ecco le best practice per l'hardening.

#### Gestione dei Segreti

```markdown
## Best Practice per i Segreti in Codespaces

### Livelli di Segreti
1. **Segreti Utente**: disponibili in tutti i Codespace dell'utente
   - Settings > Codespaces > Secrets > New secret
   - Uso: token personali, configurazioni personali

2. **Segreti Organizzazione**: disponibili in Codespace specifici
   - Organization Settings > Codespaces > Secrets
   - Uso: API key condivise, credenziali di servizi interni
   - Scopo: specifici per repository o per tutta l'organizzazione

3. **Segreti Repository**: disponibili nei Codespace di quel repository
   - Repository Settings > Codespaces > Secrets
   - Uso: credenziali specifiche del progetto

### Ordine di Priorità (in caso di nome duplicato)
1. Segreto utente (più alto)
2. Segreto organizzazione
3. Segreto repository (più basso)
```

#### Policy di Sicurezza Organizzative

```bash
# Configurazione delle policy di sicurezza per Codespaces

# 1. Limitare i repository che possono creare Codespaces
# Organization Settings > Codespaces > Access
# "Enable for selected repositories" > selezionare i repository

# 2. Richiedere trust per repository di proprietà esterna
# Organization Settings > Codespaces
# "Restrict codespace creation to org-owned repositories only": Enabled

# 3. Configurare retention automatica
# Organization Settings > Codespaces > Retention
# "Default retention period": 14 days
# "Maximum retention period": 30 days

# 4. Limitare le porte pubbliche
# Organization Settings > Codespaces > Port visibility
# "Allow users to set port visibility to public": Disabled
# Questo previene l'esposizione accidentale di servizi

# 5. Audit dell'uso dei Codespaces
gh api orgs/{org}/codespaces \
  --jq '.codespaces[] | {
    owner: .owner.login,
    repo: .repository.full_name,
    machine: .machine.display_name,
    created: .created_at,
    last_used: .last_used_at,
    state: .state
  }'
```

#### Network Security per Codespaces

```markdown
## Sicurezza di Rete

### VPN e Rete Privata
- I Codespaces NON supportano nativamente connessioni VPN
- Per accedere a risorse private, usare:
  1. GitHub Actions self-hosted runner come proxy
  2. SSH tunneling dal Codespace alla rete aziendale
  3. Tailscale / WireGuard installati nel devcontainer

### Proxy Configuration
- Configurare proxy via variabili d'ambiente nel devcontainer.json:
  ```json
  {
    "containerEnv": {
      "HTTP_PROXY": "http://proxy.company.com:8080",
      "HTTPS_PROXY": "http://proxy.company.com:8080",
      "NO_PROXY": "localhost,127.0.0.1,.company.internal"
    }
  }
  ```

### GPG Commit Signing nei Codespaces
- I Codespaces possono usare GPG key per firmare i commit
- La chiave GPG viene montata automaticamente dal profilo GitHub
- Configurazione: Settings > Codespaces > GPG verification > Enabled
```

---

## GitHub Enterprise

GitHub Enterprise è l'offerta di GitHub per grandi organizzazioni con requisiti avanzati di sicurezza, compliance e gestione.

### GHES vs GHEC

GitHub offre due varianti Enterprise:

| Aspetto | GHES (Server) | GHEC (Cloud) |
|---------|:------------:|:------------:|
| Hosting | Self-hosted (on-premise o cloud privato) | GitHub.com cloud |
| Manutenzione | A carico dell'azienda | GitHub |
| Aggiornamenti | Manuali, versioned | Automatici, continui |
| Personalizzazione | Alta (accesso completo) | Limitata (multi-tenant) |
| Data residency | Pieno controllo | Regioni GitHub (EU disponibile) |
| Uptime SLA | Dipende dall'infrastruttura | 99.9% |
| Costo | Licenza per utente + infrastruttura | Licenza per utente |
| Funzionalità nuove | Ritardo (ogni release) | Immediatamente |
| Network isolation | Completa | IP allow lists |
| SAML SSO | Sì | Sì |
| SCIM | Sì | Sì |
| Audit log | Sì (locale + streaming) | Sì (con streaming) |
| GitHub Connect | Opzionale | N/A |

#### GHES: Requisiti Infrastruttura

```
Requisiti minimi GHES:
  CPU: 4 core
  RAM: 32 GB
  Storage root: 200 GB SSD
  Storage dati: 100+ GB SSD (cresce con i dati)
  Rete: 1 Gbps

Requisiti raccomandati per 500+ utenti:
  CPU: 8+ core
  RAM: 64+ GB
  Storage root: 200 GB SSD
  Storage dati: 500+ GB NVMe
  Rete: 10 Gbps
  High Availability: 2 nodi + NFS condiviso

Sistemi supportati:
  - AWS (AMI ufficiale)
  - Azure (VHD ufficiale)
  - GCP (immagine ufficiale)
  - VMware ESXi
  - Hyper-V
  - OpenStack KVM
```

### SAML SSO

SAML Single Sign-On permette di centralizzare l'autenticazione usando il provider di identità aziendale (Azure AD, Okta, OneLogin, etc.).

#### Configurazione SAML con Azure AD

```
# Passo 1: Configurare Azure AD
Azure Portal > Enterprise Applications > New Application > GitHub Enterprise Cloud

SAML Configuration:
  Identifier (Entity ID): https://github.com/orgs/{org}
  Reply URL (ACS): https://github.com/orgs/{org}/saml/consume
  Sign-On URL: https://github.com/orgs/{org}/sso

Attribute Mappings:
  user.mail           -> http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress
  user.displayname    -> http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name
  user.userprincipalname -> http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier

# Passo 2: Configurare GitHub
Organization Settings > Authentication security > SAML single sign-on

  Enable SAML authentication: checked
  Sign on URL: https://login.microsoftonline.com/{tenant-id}/saml2
  Issuer: https://sts.windows.net/{tenant-id}/
  Public certificate: [incolla il certificato X.509 da Azure AD]

# Passo 3: Testare
  Click "Test SAML configuration"
  Verificare il login
  Salvare

# Passo 4: Enforcement (opzionale ma raccomandato)
  Require SAML SSO authentication for all members: checked
  # Questo richiede a tutti i membri di autenticarsi via SAML
```

#### Gestione delle Identità con SAML

```bash
# Visualizzare le identità SAML collegate
gh api orgs/{org}/members \
  --jq '.[] | {login: .login, saml: .saml_name_id}'

# Trovare utenti senza identità SAML
gh api orgs/{org}/outside_collaborators \
  --jq '.[] | .login'
```

### SCIM Provisioning

SCIM (System for Cross-domain Identity Management) automatizza il provisioning e deprovisioning degli utenti. Quando un dipendente viene aggiunto o rimosso dal provider di identità, GitHub viene aggiornato automaticamente.

```
# Configurazione SCIM con Azure AD

Azure Portal > Enterprise Applications > GitHub > Provisioning

  Provisioning Mode: Automatic
  Admin Credentials:
    Tenant URL: https://api.github.com/scim/v2/organizations/{org}
    Secret Token: [PAT con scope admin:org]

  Mappings:
    Provision Azure Active Directory Users: Yes
    Provision Azure Active Directory Groups: Yes

  Attribute Mapping (Users):
    userPrincipalName -> userName
    mail -> emails[type eq "work"].value
    displayName -> displayName
    givenName -> name.givenName
    surname -> name.familyName
    Switch([IsSoftDeleted], , "False", "True", "True", "False") -> active

  Attribute Mapping (Groups):
    displayName -> displayName
    members -> members
```

Il ciclo di vita dell'utente con SCIM:

```
Nuovo dipendente (HR -> Azure AD):
  1. HR aggiunge l'utente in Azure AD
  2. SCIM provisiona l'utente in GitHub
  3. L'utente viene aggiunto ai team corrispondenti ai gruppi AD
  4. L'utente riceve un invito email

Dipendente lascia l'azienda:
  1. HR disabilita l'utente in Azure AD
  2. SCIM deprovisiona l'utente da GitHub
  3. L'accesso a tutti i repository viene revocato
  4. I Codespace dell'utente vengono cancellati
  5. I PAT e le SSH key vengono invalidati
```

### Audit Log

L'audit log registra tutte le azioni significative nell'organizzazione, essenziale per compliance e investigazione di incidenti di sicurezza.

#### Consultazione Audit Log

```bash
# Via web: Organization Settings > Audit log

# Via API
gh api orgs/{org}/audit-log \
  --method GET \
  -f phrase='action:repo.create' \
  -f per_page=100

# Cercare eventi specifici
# Tutti gli accessi ai repository negli ultimi 7 giorni
gh api orgs/{org}/audit-log \
  -f phrase='action:repo.access created:>2026-04-05' \
  --jq '.[] | {actor: .actor, action: .action, repo: .repo, timestamp: .created_at}'

# Azioni degli amministratori
gh api orgs/{org}/audit-log \
  -f phrase='action:org' \
  --jq '.[] | select(.actor_is_admin == true) | {actor: .actor, action: .action}'

# Modifiche alle permission
gh api orgs/{org}/audit-log \
  -f phrase='action:team.add_member OR action:team.remove_member' \
  --jq '.[] | {actor: .actor, action: .action, user: .user, team: .team}'
```

#### Streaming dell'Audit Log

Per organizzazioni enterprise, l'audit log può essere trasmesso in streaming verso sistemi SIEM esterni:

```
# Organization Settings > Audit log > Log streaming

Destinazioni supportate:
  - Amazon S3
  - Azure Blob Storage
  - Azure Event Hubs
  - Google Cloud Storage
  - Splunk
  - Datadog

# Esempio: Streaming verso Amazon S3
Configuration:
  Bucket: github-audit-logs-{org}
  Region: eu-west-1
  Access Key ID: AKIA...
  Secret Access Key: ****
  Path prefix: audit-logs/
```

### IP Allow Lists

Le IP allow lists limitano l'accesso all'organizzazione a specifici indirizzi IP, tipicamente gli IP aziendali e delle VPN.

```bash
# Aggiungere IP alla allow list
gh api orgs/{org}/interaction-limits \
  --method PUT \
  --input - << 'EOF'
{
  "limit": "collaborators_only",
  "expiry": "one_month"
}
EOF

# Gestire la IP allow list via API
# Aggiungere un IP
gh api graphql -f query='
mutation {
  createIpAllowListEntry(input: {
    ownerId: "ORG_ID",
    allowListValue: "203.0.113.0/24",
    name: "Ufficio Milano",
    isActive: true
  }) {
    ipAllowListEntry {
      id
      allowListValue
      name
    }
  }
}'

# Elencare tutti gli IP
gh api graphql -f query='
query {
  organization(login: "org-name") {
    ipAllowListEntries(first: 100) {
      nodes {
        allowListValue
        name
        isActive
        createdAt
      }
    }
  }
}'
```

### Gestione Organizzazioni

#### Struttura Enterprise

```
Enterprise Account
├── Organization: engineering
│   ├── Team: backend
│   │   ├── Sub-team: backend-api
│   │   └── Sub-team: backend-data
│   ├── Team: frontend
│   ├── Team: devops
│   └── Team: security
├── Organization: mobile
│   ├── Team: ios
│   └── Team: android
└── Organization: research
    └── Team: ml
```

#### Gestione Team e Permessi

```bash
# Creare un team
gh api orgs/{org}/teams \
  --method POST \
  --input - << 'EOF'
{
  "name": "backend-api",
  "description": "Team responsabile delle API backend",
  "privacy": "closed",
  "parent_team_id": 123,
  "permission": "push"
}
EOF

# Aggiungere un membro al team
gh api orgs/{org}/teams/backend-api/memberships/username \
  --method PUT \
  --input - << 'EOF'
{
  "role": "member"
}
EOF

# Assegnare un repository al team
gh api orgs/{org}/teams/backend-api/repos/{org}/api-service \
  --method PUT \
  --input - << 'EOF'
{
  "permission": "push"
}
EOF

# Visualizzare i permessi effettivi di un utente
gh api repos/{org}/{repo}/collaborators/username/permission \
  --jq '.permission'
```

### InnerSource

InnerSource è la pratica di applicare le metodologie open source all'interno di un'azienda. GitHub Enterprise facilita questo approccio con funzionalità specifiche.

#### Configurazione per InnerSource

```
# 1. Abilitare la visibilità "internal" per i repository
Organization Settings > Member privileges > Repository creation
  - Allow members to create internal repositories: Yes

# 2. Repository di default per linee guida
Creare un repository .github nell'organizzazione con:
  - profile/README.md (profilo dell'organizzazione)
  - CONTRIBUTING.md (linee guida generali per contribuire)
  - CODE_OF_CONDUCT.md
```

```markdown
<!-- .github/profile/README.md -->
# Engineering Organization

## Come Contribuire (InnerSource)

Tutti i dipendenti sono incoraggiati a contribuire a qualsiasi repository
interno. Segui queste linee guida:

1. **Cerca prima**: Qualcuno potrebbe aver già risolto il tuo problema
2. **Apri un'issue**: Discuti la proposta prima di scrivere codice
3. **Fork e PR**: Usa il flusso standard GitHub
4. **Revisione**: Attendi la review del team owner
5. **Documenta**: Aggiorna la documentazione se necessario

## Repository Principali

| Repository | Descrizione | Team Owner |
|-----------|-------------|------------|
| api-gateway | Gateway API principale | @backend |
| design-system | Componenti UI condivisi | @frontend |
| shared-libs | Librerie condivise | @platform |
| infra-modules | Moduli Terraform | @devops |
```

#### Metriche InnerSource

```bash
# Analizzare le contribuzioni cross-team
# Trovare PR da utenti esterni al team owner
gh api repos/{org}/{repo}/pulls \
  -f state=closed \
  -f per_page=100 \
  --jq '[.[] | select(.merged_at != null) | {
    author: .user.login,
    title: .title,
    merged: .merged_at
  }]'

# Script per report InnerSource mensile
gh api search/issues \
  -f q="org:{org} is:pr is:merged merged:>2026-03-01" \
  --jq '.items | group_by(.user.login) | map({
    contributor: .[0].user.login,
    pr_count: length,
    repos: [.[].repository_url | split("/") | last] | unique
  }) | sort_by(.pr_count) | reverse'
```

### Enterprise Managed Users (EMU) — Approfondimento

Enterprise Managed Users (EMU) è il modello di identità dove gli account GitHub sono completamente controllati dall'azienda tramite il provider di identità (IdP). A differenza degli account GitHub tradizionali, gli account EMU sono di proprietà dell'enterprise e non dell'utente.

#### EMU vs Account Tradizionali

| Aspetto | Account Tradizionale | Account EMU |
|---------|---------------------|-------------|
| Proprietà dell'account | L'utente | L'enterprise |
| Formato username | Scelto dall'utente | `shortcode_nomeutente` |
| Email | Personale o aziendale | Solo aziendale |
| Autenticazione | Password + MFA opzionale | Solo SAML SSO (obbligatorio) |
| Accesso open source | Pieno | Solo repo interni + org |
| Contributi GitHub.com | Sì | No (account separato necessario) |
| Deprovisioning | Manuale | Automatico via IdP |
| Fork di repo pubblici | Sì | No (restrizioni configurabili) |
| Creazione organizzazioni | Sì | No |
| GitHub Marketplace | Sì | Limitato |

#### Configurazione EMU con IdP

```
## Flusso di Setup EMU

1. Acquistare GitHub Enterprise Cloud con EMU
   - Contattare il team vendite GitHub
   - Ricevere l'enterprise slug (es. "acme-corp")

2. Configurare il Setup User
   - L'account setup ha il formato: {slug}_admin
   - Usare questo account per la configurazione iniziale
   - Attivare SAML SSO e SCIM per il provider di identità

3. Provider di Identità Supportati (con integrazione "paved-path"):
   - Microsoft Entra ID (ex Azure AD) — integrazione nativa
   - Okta — integrazione nativa
   - PingFederate — integrazione nativa

4. Configurare SAML SSO per EMU:
   Enterprise Settings > Authentication security
   - SAML single sign-on: Required
   - SSO URL: https://login.microsoftonline.com/{tenant}/saml2
   - Issuer: https://sts.windows.net/{tenant}/
   - Certificate: [certificato X.509 dall'IdP]

5. Configurare SCIM Provisioning:
   Enterprise Settings > Authentication security > SCIM
   - SCIM base URL: https://api.github.com/scim/v2/enterprises/{slug}
   - Token: [PAT del setup user con scope admin:enterprise]

6. Mappatura Gruppi:
   Nell'IdP, mappare i gruppi aziendali ai team GitHub:
   - Gruppo "Engineering" → Team "engineering" nell'org
   - Gruppo "DevOps" → Team "devops" nell'org
   - Gruppo "QA" → Team "qa" nell'org
```

#### Enterprise Access Restrictions

Le restrizioni di accesso enterprise controllano dove gli utenti EMU possono interagire su GitHub. Dalla versione GA (settembre 2025), le restrizioni sono applicabili anche tramite proxy aziendali.

```markdown
## Enterprise Access Restrictions

### Restrizioni Base
- Gli utenti EMU possono accedere SOLO ai repository dell'enterprise
- Non possono creare repository personali
- Non possono interagire con repository pubblici come utenti EMU
- Non possono installare app dal GitHub Marketplace

### Restrizioni via Corporate Proxy (GA settembre 2025)
- Limitare il traffico EMU a github.com solo tramite proxy aziendali
- Bloccare accesso non approvato da reti non aziendali
- Configurazione:
  Enterprise Settings > Policies > Access restrictions
  "Restrict access to corporate proxy only": Enabled
  Proxy configuration: [dettagli del proxy aziendale]

### Repository Collaborators per EMU (GA giugno 2025)
- Aggiungere utenti esterni a singoli repository senza aggiungerli all'org
- Permette collaborazione con contractor e consulenti esterni
- L'accesso è limitato al repository specifico
- Configurazione:
  Enterprise Settings > Policies > Repository collaborators
  "Allow repository collaborators": Enabled
```

#### Contributi Open Source con EMU

Gli utenti EMU non possono contribuire direttamente a repository pubblici. GitHub ha creato il pattern "Private Mirrors" per risolvere questa limitazione:

```markdown
## Pattern Private Mirrors per Open Source

1. Installare la Private Mirrors App nell'enterprise
2. Creare un mirror privato del progetto open source upstream
3. Lo sviluppatore lavora sul mirror privato:
   - Crea branch, scrive codice, apre PR interna
   - Il codice passa review e approvazione interna
4. Dopo l'approvazione, il codice viene pushato su un fork pubblico
   (da un account GitHub personale, non EMU)
5. Lo sviluppatore apre una PR upstream dal fork pubblico

Vantaggi:
- Il codice passa review interna prima di diventare pubblico
- La proprietà intellettuale resta protetta
- L'azienda ha visibilità sulle contribuzioni open source
- La cronologia dei commit viene preservata
```

#### Migrazione a EMU

```markdown
## Checklist di Migrazione a EMU

### Pre-Migrazione
- [ ] Inventario completo di organizzazioni, repository, team, e utenti
- [ ] Identificare repository con collaboratori esterni
- [ ] Mappare i gruppi IdP ai team GitHub desiderati
- [ ] Comunicare il piano di migrazione a tutti gli stakeholder
- [ ] Pianificare il periodo di migrazione (raccomandato: weekend o freeze)

### Attenzione: Cosa NON Viene Migrato
- Account personali degli utenti (sono nuovi account EMU)
- Cronologia dei contributi personali
- SSH key e PAT esistenti
- Stelle e watch dei repository
- Notifiche e impostazioni personali

### Fasi della Migrazione
1. Configurare l'enterprise EMU con l'IdP
2. Importare i repository con GitHub Enterprise Importer
3. Attivare SCIM per creare gli account EMU
4. Comunicare le credenziali agli utenti
5. Periodo di transizione: vecchio e nuovo enterprise attivi
6. Disattivare l'enterprise precedente
7. Verificare che tutti gli accessi funzionino

### Post-Migrazione
- [ ] Verificare che tutti gli utenti possano accedere ai repository
- [ ] Verificare che i workflow GitHub Actions funzionino
- [ ] Verificare che le integrazioni esterne funzionino
- [ ] Aggiornare la documentazione interna
- [ ] Raccogliere feedback dal team
```

### Data Residency e Compliance

GitHub Enterprise Cloud offre la residenza dei dati per le organizzazioni con requisiti normativi stringenti (GDPR, CCPA, FedRAMP). I dati vengono memorizzati in infrastruttura Azure nella regione geografica scelta.

#### Regioni Disponibili (Maggio 2026)

| Regione | Copertura Geografica | Infrastruttura |
|---------|---------------------|----------------|
| US | Stati Uniti | Azure US |
| EU | UE + EFTA (dal 1 maggio 2026: Norvegia, Svizzera, Islanda, Liechtenstein) | Azure EU |

#### Cosa Viene Memorizzato nella Regione

```markdown
## Dati con Residenza Garantita

### Inclusi nella Residenza
- Repository Git (codice sorgente, branch, tag)
- Issue, PR, discussioni
- GitHub Actions artifacts e log
- GitHub Packages (container, npm, Maven, etc.)
- GitHub Pages (contenuto)
- Codespaces (storage)
- Audit log
- Dati SCIM e identità EMU
- Metadati delle organizzazioni

### Copilot Data Residency (GA aprile 2026)
- Tutta l'elaborazione di inferenza avviene nella regione designata
- I prompt e le risposte non lasciano la regione
- Disponibile per piani Business e Enterprise
- Configurazione:
  Enterprise Settings > Copilot > Data residency
  "Processing region": "EU" o "US"

### Considerazioni sulla Compliance
- Le certificazioni ISO 27001, SOC 2 si applicano anche con data residency
- L'URL dell'enterprise cambia: da github.com a ghe.com
  (es. https://acme.ghe.com invece di https://github.com/acme)
- Tutte le API REST e GraphQL funzionano con il dominio ghe.com
- GitHub CLI supporta ghe.com nativamente
```

#### Configurazione GDPR per Enterprise

```bash
# Verificare la configurazione della data residency
gh api enterprises/{enterprise}/settings \
  --jq '{
    data_residency: .data_residency_region,
    domain: .enterprise_url,
    created_at: .created_at
  }'

# Esportare i dati di un utente (GDPR Data Subject Request)
# Enterprise Settings > Compliance > Data subject request
# Oppure via API:
gh api enterprises/{enterprise}/data-export \
  --method POST \
  --input - << 'EOF'
{
  "user": "username",
  "type": "export",
  "reason": "GDPR data subject access request"
}
EOF

# Eliminare i dati di un utente (GDPR Right to Erasure)
# Nota: richiede la rimozione dell'utente dall'IdP + deprovisioning SCIM
# I dati vengono eliminati secondo la retention policy dell'enterprise
```

### Audit Log Avanzato

L'audit log enterprise ha ricevuto miglioramenti significativi nel 2025-2026, incluso lo streaming delle richieste API e la configurazione programmatica.

#### Streaming delle Richieste API (GA gennaio 2025)

```markdown
## API Request Audit Log Streaming

Il streaming delle richieste API fornisce visibilità sulle attività API
che accedono a risorse private dell'enterprise. Questo include:

- Chiamate API REST e GraphQL
- Richieste da GitHub App e OAuth App
- Accessi da PAT (Personal Access Token)
- Operazioni Git via HTTPS
- Operazioni da GitHub Actions

### Configurazione
Enterprise Settings > Audit log > Log streaming > Configure stream

### Informazioni Incluse per Ogni Richiesta API
- Timestamp UTC
- IP sorgente
- User agent
- Endpoint API chiamato
- Metodo HTTP
- Status code della risposta
- Token type (PAT, OAuth, GitHub App)
- Token ID (per tracciabilità)
- Repository e organizzazione di destinazione
```

#### Configurazione Programmatica dell'Audit Log

```bash
# Creare un nuovo stream di audit log via API REST
gh api enterprises/{enterprise}/audit-log/streams \
  --method POST \
  --input - << 'EOF'
{
  "enabled": true,
  "stream_type": "AmazonS3",
  "vendor_specific": {
    "bucket": "github-audit-logs-enterprise",
    "region": "eu-west-1",
    "key_id": "AKIA...",
    "key_secret": "****",
    "path_prefix": "audit/"
  }
}
EOF

# Aggiornare la configurazione di un stream esistente
gh api enterprises/{enterprise}/audit-log/streams/{stream_id} \
  --method PATCH \
  --input - << 'EOF'
{
  "enabled": true,
  "vendor_specific": {
    "key_id": "AKIA_NUOVO...",
    "key_secret": "****_NUOVO"
  }
}
EOF

# Elencare tutti gli stream configurati
gh api enterprises/{enterprise}/audit-log/streams \
  --jq '.[] | {
    id: .id,
    type: .stream_type,
    enabled: .enabled,
    created_at: .created_at,
    updated_at: .updated_at
  }'

# Eliminare uno stream
gh api enterprises/{enterprise}/audit-log/streams/{stream_id} \
  --method DELETE
```

#### Multi-Endpoint Streaming

Le enterprise possono configurare fino a due endpoint di streaming, anche di tipi diversi:

```markdown
## Configurazione Multi-Endpoint

### Esempio: Splunk (real-time) + S3 (archivio)

Endpoint 1: Splunk
  - Tipo: Splunk HTTP Event Collector
  - URL: https://splunk.company.com:8088/services/collector
  - Token: [Splunk HEC token]
  - Uso: analisi real-time, alerting, dashboard SIEM

Endpoint 2: Amazon S3
  - Tipo: Amazon S3
  - Bucket: github-audit-archive
  - Region: eu-west-1
  - Path prefix: year={year}/month={month}/
  - Uso: archivio a lungo termine, compliance, forensics

### Vantaggi del Multi-Endpoint
- Separazione tra analisi real-time e archivio a lungo termine
- Resilienza: se un endpoint è down, l'altro continua a ricevere
- Team diversi possono usare strumenti diversi (SOC usa Splunk, Compliance usa S3)
```

#### Query Avanzate sull'Audit Log

```bash
# Trovare tutte le azioni di un utente specifico negli ultimi 30 giorni
gh api orgs/{org}/audit-log \
  -f phrase='actor:mario.rossi created:>2026-04-24' \
  -f per_page=100 \
  --jq '.[] | {
    action: .action,
    repo: .repo,
    timestamp: .created_at,
    ip: .actor_ip
  }'

# Monitorare creazione e cancellazione di repository
gh api orgs/{org}/audit-log \
  -f phrase='action:repo.create OR action:repo.destroy' \
  -f per_page=50 \
  --jq '.[] | {
    action: .action,
    actor: .actor,
    repo: .repo,
    visibility: .visibility,
    timestamp: .created_at
  }'

# Tracciare modifiche ai permessi dei team
gh api orgs/{org}/audit-log \
  -f phrase='action:team.add_repository OR action:team.remove_repository OR action:team.change_privacy' \
  --jq '.[] | {
    action: .action,
    actor: .actor,
    team: .team,
    repo: .repo,
    old_permission: .old_permission,
    new_permission: .permission
  }'

# Rilevare accessi sospetti (IP non nella allow list)
gh api orgs/{org}/audit-log \
  -f phrase='action:org.sso_response' \
  --jq '[.[] | .actor_ip] | unique | sort'

# Monitorare l'uso dei PAT (Personal Access Token)
gh api orgs/{org}/audit-log \
  -f phrase='action:personal_access_token' \
  --jq '.[] | {
    action: .action,
    actor: .actor,
    token_scopes: .scopes,
    timestamp: .created_at
  }'
```

### IP Allow List Avanzata

L'IP allow list è stata estesa nel 2025-2026 con il supporto per i namespace EMU e IPv6.

#### Configurazione Completa dell'IP Allow List

```bash
# Aggiungere un range CIDR (ufficio principale)
gh api graphql -f query='
mutation {
  createIpAllowListEntry(input: {
    ownerId: "ENTERPRISE_ID",
    allowListValue: "203.0.113.0/24",
    name: "Ufficio Milano - Principale",
    isActive: true
  }) {
    ipAllowListEntry { id allowListValue name isActive }
  }
}'

# Aggiungere un range per VPN aziendale
gh api graphql -f query='
mutation {
  createIpAllowListEntry(input: {
    ownerId: "ENTERPRISE_ID",
    allowListValue: "198.51.100.0/24",
    name: "VPN Aziendale",
    isActive: true
  }) {
    ipAllowListEntry { id allowListValue name isActive }
  }
}'

# Aggiungere IPv6 (importante: GitHub sta gradualmente abilitando IPv6)
gh api graphql -f query='
mutation {
  createIpAllowListEntry(input: {
    ownerId: "ENTERPRISE_ID",
    allowListValue: "2001:db8::/32",
    name: "IPv6 - Ufficio Milano",
    isActive: true
  }) {
    ipAllowListEntry { id allowListValue name isActive }
  }
}'

# Abilitare l'enforcement dell'IP allow list
gh api graphql -f query='
mutation {
  updateIpAllowListEnabledSetting(input: {
    ownerId: "ENTERPRISE_ID",
    settingValue: ENABLED
  }) {
    enterprise {
      ownerInfo { ipAllowListEnabledSetting }
    }
  }
}'
```

#### IP Allow List per EMU Namespace (Preview febbraio 2026)

```markdown
## Copertura IP Allow List per Namespace EMU

A partire da febbraio 2026, l'IP allow list copre anche i namespace
degli utenti EMU, non solo le organizzazioni dell'enterprise.

### Cosa Copre
- Accesso via web UI ai namespace utente EMU
- Operazioni Git (push, pull, clone) sui repository del namespace
- Accesso API ai repository del namespace EMU
- Tutti i tipi di credenziali: PAT, SSH key, app token

### Configurazione
Enterprise Settings > Policies > IP allow list
"Extend IP allow list to user namespaces": Enabled (preview)

### Implicazioni
- Gli utenti EMU possono accedere ai propri namespace SOLO dagli IP consentiti
- Questo include l'accesso dal browser e da IDE locali
- I Codespace NON sono soggetti all'IP allow list (hanno IP dinamici)
```

#### Best Practice per IP Allow List

```markdown
## Best Practice

1. **Ridondanza degli Amministratori**
   - Avere almeno 2 enterprise owner con accesso da IP nella allow list
   - Documentare la procedura di emergenza per sbloccare l'accesso

2. **Usare CIDR Ampi**
   - Preferire range /24 o /16 per IP dinamici
   - Minimizzare il numero di entry (meno entry = meno manutenzione)

3. **Includere IPv6**
   - GitHub sta gradualmente abilitando IPv6
   - Aggiungere i range IPv6 preventivamente per evitare interruzioni

4. **GitHub Actions**
   - Self-hosted runner: aggiungere gli IP dei runner
   - GitHub-hosted runner con IP statico: usare larger runner con IP statico
   - Aggiungere il range IP di GitHub Actions meta API:
     gh api meta --jq '.actions'

5. **Load Balancer**
   - Per molti sviluppatori, usare un load balancer come punto di uscita
   - Un singolo range CIDR copre tutti gli sviluppatori

6. **Monitoraggio**
   - Controllare l'audit log per tentativi bloccati
   - Impostare alert per modifiche all'IP allow list
   - Audit periodico: rimuovere IP non più necessari
```

### Enterprise Security Hardening

Una checklist completa per l'hardening di un'enterprise GitHub.

#### Checklist di Sicurezza Enterprise

```markdown
## Hardening Checklist — GitHub Enterprise Cloud

### Identità e Accesso
- [ ] SAML SSO abilitato e enforcement attivo
- [ ] SCIM provisioning configurato con l'IdP
- [ ] MFA obbligatoria per tutti gli utenti (anche con SAML)
- [ ] Session timeout configurato (max 8 ore raccomandato)
- [ ] PAT con scadenza obbligatoria (max 90 giorni)
- [ ] SSH key con scadenza obbligatoria
- [ ] Review periodica degli outside collaborator

### Rete
- [ ] IP allow list configurata e attiva
- [ ] IPv6 incluso nell'allow list
- [ ] GitHub Actions: self-hosted runner con IP statico nell'allow list
- [ ] Webhook secrets configurati per tutti i webhook

### Repository
- [ ] Branch protection su tutti i branch principali
- [ ] Code review obbligatoria (minimo 1 reviewer)
- [ ] Signed commits obbligatori per branch protetti
- [ ] Secret scanning abilitato su tutti i repository
- [ ] Dependabot security updates abilitato
- [ ] CodeQL abilitato per linguaggi supportati
- [ ] Repository visibility default: private o internal

### Copilot
- [ ] Content exclusion configurata per file sensibili
- [ ] Suggerimenti matching codice pubblico: bloccati
- [ ] Telemetria: disabilitata se richiesto dalla compliance
- [ ] Policy modelli: limitare i modelli disponibili se necessario
- [ ] Data residency: configurata per la regione corretta

### Audit e Compliance
- [ ] Audit log streaming configurato verso SIEM
- [ ] API request logging abilitato
- [ ] Retention dell'audit log: conforme alle policy aziendali
- [ ] Data subject request process documentato (GDPR)
- [ ] Incident response runbook aggiornato

### GitHub Actions
- [ ] Self-hosted runner in rete isolata
- [ ] Runner group con accesso limitato a organizzazioni specifiche
- [ ] OIDC configurato per cloud provider (no credenziali statiche)
- [ ] Approved actions: limitare a azioni verificate o interne
- [ ] Fork pull request workflow: richiede approvazione
```

#### Automazione dell'Audit di Sicurezza

```bash
#!/bin/bash
# security-audit.sh — Script di audit automatizzato per GitHub Enterprise

ORG="nome-organizzazione"
REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="security-audit-${REPORT_DATE}.json"

echo "=== Security Audit Report: ${REPORT_DATE} ==="
echo "=== Organizzazione: ${ORG} ==="

# 1. Verificare che SAML SSO sia attivo
echo "--- SAML SSO Status ---"
gh api orgs/${ORG} --jq '{
  two_factor_required: .two_factor_requirement_enabled,
  plan: .plan.name
}'

# 2. Trovare repository senza branch protection
echo "--- Repository senza Branch Protection ---"
gh api orgs/${ORG}/repos --paginate --jq '.[] | .full_name' | while read -r repo; do
  PROTECTED=$(gh api repos/${repo}/branches/main/protection 2>&1)
  if echo "$PROTECTED" | grep -q "Branch not protected"; then
    echo "ATTENZIONE: ${repo}/main non è protetto"
  fi
done

# 3. Trovare repository con visibilità pubblica
echo "--- Repository Pubblici ---"
gh api orgs/${ORG}/repos --paginate \
  --jq '.[] | select(.visibility == "public") | .full_name'

# 4. Verificare secret scanning
echo "--- Repository senza Secret Scanning ---"
gh api orgs/${ORG}/repos --paginate \
  --jq '.[] | select(.security_and_analysis.secret_scanning.status != "enabled") | .full_name'

# 5. Elencare outside collaborator
echo "--- Outside Collaborator ---"
gh api orgs/${ORG}/outside_collaborators --paginate \
  --jq '.[] | {login: .login, type: .type}'

# 6. PAT attivi senza scadenza
echo "--- Verifica PAT senza scadenza ---"
gh api orgs/${ORG}/personal-access-tokens \
  --jq '.[] | select(.token_expired == false and .token_expires_at == null) | {
    owner: .owner.login,
    permissions: .permissions,
    created: .created_at
  }'

echo "=== Fine Audit ==="
```

---

## Integrazione tra le Funzionalità

Le tre funzionalità si integrano in modo sinergico:

1. **Copilot + Codespaces**: Copilot è pre-installato nei Codespace. Un nuovo sviluppatore apre un Codespace e ha immediatamente un ambiente completo con assistenza AI, senza configurare nulla.

2. **Codespaces + Enterprise**: Le policy enterprise controllano quali macchine sono disponibili, i limiti di spesa, e i segreti accessibili. I Codespace rispettano SAML SSO e IP allow lists.

3. **Copilot + Enterprise**: Le organizzazioni enterprise possono controllare chi ha accesso a Copilot, quali repository sono esclusi dall'invio di contesto, e se il filtro per codice pubblico è attivo.

```yaml
# Esempio: Workflow che combina tutte e tre le funzionalità
#
# 1. Un nuovo sviluppatore si unisce al team
# 2. SCIM lo provisiona automaticamente nell'organizzazione
# 3. Apre un Codespace dal repository principale
# 4. L'ambiente è pronto in 30 secondi (prebuild)
# 5. Copilot è attivo e configurato secondo le policy aziendali
# 6. Le estensioni e i tool sono pre-installati
# 7. Inizia a contribuire immediatamente
```

---

## Riepilogo

GitHub Copilot, Codespaces e le funzionalità Enterprise rappresentano l'evoluzione di GitHub da piattaforma di hosting di codice a ecosistema di sviluppo completo. Copilot accelera la scrittura di codice fornendo suggerimenti contestuali intelligenti, ma richiede discipline nell'uso: il codice generato deve essere compreso e revisionato come qualsiasi altro codice. Codespaces elimina i problemi di configurazione dell'ambiente e accelera l'onboarding, ma introduce costi operativi che devono essere gestiti con attenzione. Le funzionalità Enterprise forniscono il controllo e la governance necessari per l'uso di GitHub in grandi organizzazioni, con SAML SSO, SCIM, audit logging e policy granulari.

L'adozione di queste funzionalità dovrebbe essere incrementale e guidata da esigenze reali. Non ogni team ha bisogno di Codespaces o di funzionalità Enterprise. Ma per i team che ne beneficiano, l'impatto sulla produttività e sulla qualità dello sviluppo può essere significativo.

---

## Esercizi Pratici

### Esercizio 1: Configurare Codespaces con devcontainer.json

Crea un ambiente di sviluppo reproducibile con Codespaces:

```json
// .devcontainer/devcontainer.json
// 1. Scegliere una base image appropriata:
//    "image": "mcr.microsoft.com/devcontainers/typescript-node:20"
// 2. Aggiungere features:
//    - Docker-in-Docker (per build container)
//    - GitHub CLI
//    - PostgreSQL client
// 3. Configurare estensioni VS Code:
//    "customizations.vscode.extensions": [
//      "dbaeumer.vscode-eslint",
//      "esbenp.prettier-vscode",
//      "ms-azuretools.vscode-docker"
//    ]
// 4. Definire lifecycle scripts:
//    "postCreateCommand": "npm ci && npm run build"
//    "postStartCommand": "npm run dev &"
// 5. Configurare port forwarding:
//    "forwardPorts": [3000, 5432]
//    "portsAttributes": { "3000": { "label": "App", "onAutoForward": "openBrowser" } }

// Verifica:
// - Aprire un Codespace dal repository
// - L'ambiente è pronto in < 2 minuti
// - Le estensioni sono pre-installate
// - L'app si avvia automaticamente su porta 3000
```

**Criteri di successo:** l'ambiente è identico per ogni sviluppatore, zero configurazione manuale richiesta.

### Esercizio 2: Prebuild Codespaces per Onboarding Rapido

Configura prebuild per ridurre il tempo di avvio:

```yaml
# .devcontainer/devcontainer.json
# Aggiungere configurazione prebuild

# 1. Abilitare prebuild nelle impostazioni del repository:
#    Settings > Codespaces > Set up prebuild
# 2. Configurare trigger:
#    - Su push a main
#    - Su modifica di .devcontainer/, package-lock.json
# 3. Configurare regione: scegliere le regioni usate dal team
# 4. Impostare retention: 2 prebuild (current + previous)
# 5. Misurare il tempo di avvio:
#    - Senza prebuild: annotare il tempo
#    - Con prebuild: annotare il tempo
#    - Calcolare il miglioramento (target: < 30 secondi)

# Verifica:
# - Prebuild appare in Settings > Codespaces > Prebuilds
# - Apertura Codespace usa il prebuild (icona verde)
# - Tempo di avvio < 30 secondi
```

### Esercizio 3: GitHub Copilot — Produttività e Limiti

Esplora le capacità e i limiti di GitHub Copilot:

```bash
# 1. Installare l'estensione GitHub Copilot in VS Code
# 2. Test di completamento:
#    - Creare una funzione con nome descrittivo e verificare il suggerimento
#    - Scrivere un commento che descrive una funzione e accettare il suggerimento
#    - Usare Copilot Chat per spiegare un pezzo di codice complesso
# 3. Test di qualità:
#    - Accettare un suggerimento Copilot per una funzione di validazione email
#    - Scrivere test unitari per verificare edge case (il suggerimento li gestisce?)
#    - Chiedere a Copilot Chat di migliorare la sicurezza del codice generato
# 4. Test CLI:
#    - gh copilot explain "git rebase -i HEAD~5"
#    - gh copilot suggest "find all files modified in the last 24 hours"
# 5. Documentare:
#    - 3 casi dove Copilot ha accelerato il lavoro
#    - 3 casi dove il suggerimento era errato o insicuro
#    - Best practice personali per l'uso di Copilot
```

### Esercizio 4: Enterprise — SAML SSO e SCIM

Configura (o simula la configurazione di) SAML SSO per un'organizzazione:

```bash
# Nota: richiede GitHub Enterprise Cloud e un IdP (Okta, Azure AD, ecc.)
# Se non disponibile, documentare i passaggi come runbook

# 1. Configurare SAML SSO nell'organizzazione:
#    Settings > Authentication security > Enable SAML authentication
# 2. Configurare l'IdP:
#    - SSO URL: https://github.com/orgs/{org}/saml/consume
#    - Entity ID: https://github.com/orgs/{org}
#    - Certificato X.509
# 3. Testare l'autenticazione SSO con un utente di test
# 4. Abilitare SCIM per provisioning automatico:
#    - Configurare SCIM endpoint nell'IdP
#    - Mappare gruppi IdP → team GitHub
# 5. Verificare:
#    - Utente creato nell'IdP → appare nell'organizzazione GitHub
#    - Utente rimosso dall'IdP → rimosso dall'organizzazione
#    - Login richiede SSO (non è possibile usare solo password)

# 6. Configurare IP allow list (se applicabile):
#    gh api orgs/{org}/ip-allow-list -X POST -f ip="203.0.113.0/24" -f name="Office"
```

### Esercizio 5: Policy di Costo e Governance Codespaces

Configura policy organizzative per controllare i costi di Codespaces:

```bash
# 1. Impostare spending limit:
#    Settings > Billing > Codespaces > Spending limit
# 2. Configurare machine type policy:
#    - Limitare a 2-core e 4-core per la maggior parte dei repository
#    - Permettere 8-core solo per repository specifici (data science, ML)
# 3. Impostare idle timeout:
#    - Default: 30 minuti di inattività
#    - Maximum: 4 ore
# 4. Configurare retention period:
#    - Default: 14 giorni per Codespace inattivi
#    - Maximum: 30 giorni
# 5. Monitorare i costi:
#    gh api orgs/{org}/settings/billing/codespaces
# 6. Creare alert per:
#    - Spesa mensile > 80% del budget
#    - Codespace attivo da più di 8 ore continue
#    - Machine type 16-core usata senza giustificazione

# Verifica:
# - Utente non può creare Codespace con machine type non permessa
# - Codespace si ferma dopo il timeout configurato
# - Dashboard mostra consumo per utente e repository
```

---

## Letture Consigliate

- **GitHub Docs — Copilot**: "Getting started with GitHub Copilot" — https://docs.github.com/en/copilot/using-github-copilot/getting-code-suggestions-in-your-ide-with-github-copilot (consultato: 2026-05-24)
- **GitHub Docs — Codespaces**: "Deep dive into Codespaces" — https://docs.github.com/en/codespaces/overview (consultato: 2026-05-24)
- **GitHub Docs — Enterprise Cloud**: "About GitHub Enterprise Cloud" — https://docs.github.com/en/enterprise-cloud@latest/admin/overview/about-github-enterprise-cloud (consultato: 2026-05-24)
- **GitHub Blog**: "GitHub Copilot Workspace" — https://github.blog/news-insights/product-news/github-copilot-workspace/ (consultato: 2026-05-24)
- **Dev Containers Specification**: https://containers.dev/implementors/spec/ (consultato: 2026-05-24)
- **Libro**: "GitHub For Dummies" di Sarah Guthals, Phil Haack, Wiley, 2023 — capitoli su Codespaces e funzionalità enterprise

---

## Collegamenti Incrociati

| Modulo | Collegamento | Relazione |
|--------|-------------|-----------|
| 03 | [03-piattaforma-github.md](03-piattaforma-github.md) | Piattaforma GitHub — funzionalità base su cui si costruiscono Copilot, Codespaces, Enterprise |
| 12 | [12-github-repository-management.md](12-github-repository-management.md) | Repository management — impostazioni base dei repository |
| 16 | [16-github-security-scanning.md](16-github-security-scanning.md) | Security — Copilot suggerimenti sicuri, Enterprise audit log |
| 15 | [15-github-api-cli-webhooks.md](15-github-api-cli-webhooks.md) | API e CLI — gh copilot, API enterprise, webhooks |
| 21 | [21-github-actions-self-hosted-runners.md](21-github-actions-self-hosted-runners.md) | Self-hosted runners — runner groups enterprise |
| 13 | [13-github-issues-projects-collaboration.md](13-github-issues-projects-collaboration.md) | Issues e Projects — collaborazione enterprise |
| 24 | [24-devops-completo-con-github.md](24-devops-completo-con-github.md) | DevOps — pipeline che sfruttano Codespaces e Enterprise |
| 28 | [28-codeql-advanced-security.md](28-codeql-advanced-security.md) | CodeQL Advanced Security — disponibile in Enterprise |
| 14 | [14-github-packages-pages-releases.md](14-github-packages-pages-releases.md) | Packages — distribuzione controllata in contesto enterprise |

---

## Glossario Locale

| Termine | Definizione |
|---------|------------|
| **Codespace** | Ambiente di sviluppo cloud-hosted basato su container, accessibile da browser o VS Code |
| **Copilot** | Assistente AI di GitHub per il completamento di codice, basato su modelli LLM addestrati su codice pubblico |
| **Copilot Chat** | Interfaccia conversazionale di Copilot per spiegazioni, refactoring e generazione di codice complesso |
| **devcontainer.json** | File di configurazione che definisce l'ambiente di un Codespace: immagine base, features, estensioni, lifecycle |
| **EMU (Enterprise Managed Users)** | Modello dove gli account GitHub sono controllati centralmente dall'azienda via IdP, non dagli utenti |
| **Feature** | Componente aggiuntivo installabile in un devcontainer (Docker-in-Docker, GitHub CLI, database client) |
| **IdP (Identity Provider)** | Servizio di identità (Okta, Azure AD, OneLogin) che gestisce autenticazione e provisioning utenti |
| **IP allow list** | Lista di indirizzi IP autorizzati ad accedere all'organizzazione Enterprise |
| **Prebuild** | Build anticipata dell'ambiente Codespace che riduce il tempo di avvio a pochi secondi |
| **SAML SSO** | Security Assertion Markup Language — protocollo di Single Sign-On per autenticazione federata |
| **SCIM** | System for Cross-domain Identity Management — protocollo per provisioning e deprovisioning automatico utenti |
| **Spending limit** | Limite di spesa mensile configurabile per Codespaces a livello di organizzazione |
| **Audit log** | Registro dettagliato di tutte le azioni nell'organizzazione Enterprise, esportabile via API o streaming |

---

## Evoluzioni Recenti dell'Ecosistema (2025-2026)

### Copilot Spaces

Copilot Spaces è una funzionalità introdotta nel 2025 che risolve il problema della conoscenza frammentata nei progetti, centralizzando il contesto di progetto affinché Copilot fornisca risposte più intelligenti e pertinenti, radicate nel lavoro effettivo del team. Tra gli aggiornamenti principali si annoverano gli spazi pubblici (condivisibili con chiunque), la condivisione individuale tra collaboratori, e la possibilità di aggiungere file a uno spazio direttamente dal visualizzatore di codice su github.com. Gli spazi pubblici consentono ai maintainer di progetti open source di creare contesti curati che guidano sia Copilot che i contributori nella comprensione della codebase.

### Copilot CLI come Agente Completo

A partire da gennaio 2026, la Copilot CLI è stata rinnovata come assistente AI completamente agentico nel terminale, sostituendo la precedente estensione `gh-copilot` deprecata nell'ottobre 2025. La nuova versione include agenti personalizzati specializzati per compiti comuni: **Explore** per l'analisi rapida della codebase e **Task** per l'esecuzione di comandi come test e build. I modelli GPT-5 mini e GPT-4.1 sono disponibili senza consumare richieste premium nei piani a pagamento. La Copilot CLI è ora inclusa nell'immagine predefinita di GitHub Codespaces ed è disponibile come Dev Container Feature, semplificando l'onboarding degli sviluppatori in ambienti cloud-hosted. Inoltre, il modello GPT-5.1-Codex-Max è accessibile per gli abbonati Copilot Pro, Pro+, Business ed Enterprise tramite il selettore di modelli in VS Code, github.com, GitHub Mobile e Copilot CLI.|
