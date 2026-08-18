# Tutorial 00 — Ambiente di Sviluppo Web su Windows: Dal Principiante all'Esperto

> **Companion a:** `00-guida-allo-studio.md` § Ambiente di Laboratorio
> **Scope:** Node.js e gestione delle versioni con nvm, npm e pnpm, `package.json` e lockfile, VS Code ed estensioni, ESLint e Prettier, Chrome e Firefox DevTools, Git configurato per il web, Docker per i servizi locali, variabili d'ambiente, primo progetto Vite funzionante
> **Prerequisiti:** Nessuno. Serve un PC Windows 10 o 11, una connessione internet e i permessi di installazione software.
> **Durata stimata:** 8-12 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Node.js LTS · nvm-windows 1.1+ · pnpm 9+ · VS Code · Git 2.45+ · Docker Desktop 4.x

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Cosa succede davvero quando apri una pagina web](#a1-cosa-succede-davvero-quando-apri-una-pagina-web)
  - [A2. Il terminale: PowerShell come strumento di lavoro](#a2-il-terminale-powershell-come-strumento-di-lavoro)
  - [A3. Node.js: JavaScript fuori dal browser](#a3-nodejs-javascript-fuori-dal-browser)
  - [A4. Installare Node con nvm-windows](#a4-installare-node-con-nvm-windows)
  - [A5. npm e `package.json`: il contratto del progetto](#a5-npm-e-packagejson-il-contratto-del-progetto)
  - [A6. pnpm: lo stesso lavoro, meno disco](#a6-pnpm-lo-stesso-lavoro-meno-disco)
  - [A7. VS Code e le estensioni che servono davvero](#a7-vs-code-e-le-estensioni-che-servono-davvero)
  - [A8. Il primo progetto: da cartella vuota a pagina che gira](#a8-il-primo-progetto-da-cartella-vuota-a-pagina-che-gira)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. PATH e shim: perché "comando non trovato"](#b1-path-e-shim-perché-comando-non-trovato)
  - [B2. `node_modules`, lockfile e riproducibilità](#b2-node_modules-lockfile-e-riproducibilità)
  - [B3. Semver: cosa significano davvero `^` e `~`](#b3-semver-cosa-significano-davvero--e-)
  - [B4. ESLint e Prettier: due mestieri diversi](#b4-eslint-e-prettier-due-mestieri-diversi)
  - [B5. Chrome DevTools: i pannelli che userai ogni giorno](#b5-chrome-devtools-i-pannelli-che-userai-ogni-giorno)
  - [B6. Git configurato per il web: la trappola dei fine riga](#b6-git-configurato-per-il-web-la-trappola-dei-fine-riga)
  - [B7. Docker: i servizi locali senza sporcare il sistema](#b7-docker-i-servizi-locali-senza-sporcare-il-sistema)
  - [B8. Variabili d'ambiente e `.env`](#b8-variabili-dambiente-e-env)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: il banco di lavoro](#c2-mini-progetto-il-banco-di-lavoro)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. Corepack: bloccare il package manager nel repository](#d1-corepack-bloccare-il-package-manager-nel-repository)
  - [D2. pnpm workspaces: più pacchetti, un repository](#d2-pnpm-workspaces-più-pacchetti-un-repository)
  - [D3. Sicurezza delle dipendenze e supply chain](#d3-sicurezza-delle-dipendenze-e-supply-chain)
  - [D4. Riprodurre lo stesso ambiente su un'altra macchina e in CI](#d4-riprodurre-lo-stesso-ambiente-su-unaltra-macchina-e-in-ci)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                     AMBIENTE DI SVILUPPO WEB
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
┌──────▼───────┐      ┌───────▼────────┐     ┌───────▼────────┐
│   RUNTIME    │      │    EDITOR      │     │    BROWSER     │
│              │      │                │     │                │
│  nvm         │      │  VS Code       │     │  Chrome        │
│   └ Node.js  │      │   ├ ESLint     │     │   └ DevTools   │
│      ├ npm   │      │   ├ Prettier   │     │  Firefox       │
│      └ pnpm  │      │   └ Tailwind   │     │   └ Grid/Flex  │
└──────┬───────┘      └───────┬────────┘     └───────┬────────┘
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   IL PROGETTO      │
                    │                    │
                    │  package.json      │ ← cosa serve e come si avvia
                    │  pnpm-lock.yaml    │ ← esattamente quali versioni
                    │  node_modules/     │ ← le dipendenze installate
                    │  .gitignore        │ ← cosa NON entra in Git
                    │  .env              │ ← segreti, mai in Git
                    │  eslint.config.js  │ ← regole di correttezza
                    │  .prettierrc       │ ← regole di formattazione
                    └─────────┬──────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
┌──────▼───────┐      ┌───────▼────────┐     ┌───────▼────────┐
│  VERSIONING  │      │    SERVIZI     │     │  TEST DELLE    │
│              │      │                │     │      API       │
│  Git         │      │  Docker        │     │                │
│   ├ commit   │      │   ├ PostgreSQL │     │  Thunder Client│
│   ├ branch   │      │   ├ Redis      │     │  Postman       │
│   └ remote   │      │   └ MongoDB    │     │  curl          │
└──────────────┘      └────────────────┘     └────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Cosa succede davvero quando apri una pagina web

> **Analogia:** Ordinare da un ristorante con consegna a domicilio. Tu (il **browser**) telefoni al ristorante (il **server**) e ordini un piatto (una **richiesta HTTP** per un indirizzo). Il ristorante prepara e ti spedisce il pacco (la **risposta HTTP**). Ma il pacco non contiene un piatto pronto: contiene gli ingredienti (HTML), le istruzioni di impiattamento (CSS) e un fornello con la ricetta da eseguire a casa tua (JavaScript). Il piatto lo finisci tu, in cucina, e chi guarda vede solo il risultato.

Questo è il punto che confonde chi inizia: **il browser non riceve una pagina, riceve il materiale per costruirla**. Tutta la fatica successiva la fa la tua macchina.

Il ciclo completo, quando digiti un indirizzo e premi Invio:

```
1.  DNS          "esempio.it" → 93.184.216.34
                 Il browser chiede a un server DNS l'indirizzo numerico.

2.  TCP + TLS    Apre una connessione e la cifra (HTTPS).

3.  RICHIESTA    GET / HTTP/1.1
                 Host: esempio.it

4.  RISPOSTA     200 OK
                 Content-Type: text/html
                 <!DOCTYPE html>...

5.  PARSING      Il browser legge l'HTML e costruisce il DOM.
                 Trova <link rel="stylesheet"> → nuova richiesta per il CSS
                 Trova <script src="..."> → nuova richiesta per il JS

6.  RENDERING    DOM + CSSOM → render tree → layout → paint

7.  ESECUZIONE   Il JavaScript gira, modifica il DOM, aggiunge interattività
```

Ogni passo di questa catena può rompersi in modo diverso, e ogni strumento che installi in questo tutorial serve a vedere e sistemare uno di quei passi. Il browser ti fa vedere i passi 4-7; Node ti permette di scrivere il passo 3-4 dal lato del ristorante; Docker ti dà il magazzino degli ingredienti (il database) senza doverlo costruire davvero.

**Frontend e backend, definiti una volta sola:**

- **Frontend** — tutto quello che gira nel browser dell'utente. Ha accesso allo schermo, alla tastiera e a niente che sia segreto: qualunque cosa mandi al browser è pubblica.
- **Backend** — tutto quello che gira sul tuo server. Ha accesso al database, alle chiavi API, ai file. Non è mai visibile all'utente.

> **Regola d'oro:** se un segreto arriva al browser, non è più un segreto. Non c'è configurazione, offuscamento o minificazione che cambi questo fatto. Ci torneremo in [B8](#b8-variabili-dambiente-e-env) e in modo sistematico nel `tutorial_14_sicurezza_web.md`.

---

## A2. Il terminale: PowerShell come strumento di lavoro

Nello sviluppo web il terminale non è opzionale. Ogni strumento — Node, Git, i bundler, Docker — si guida da riga di comando. Su Windows userai **PowerShell**.

**Aprirlo:** premi `Win`, scrivi `powershell`, premi Invio. Oppure, dentro VS Code, `` Ctrl+ù `` (o `Terminale → Nuovo terminale`).

I comandi che ti serviranno davvero, con la loro traduzione mentale:

```powershell
# Dove sono adesso?
Get-Location            # alias: pwd

# Cosa c'è in questa cartella?
Get-ChildItem           # alias: ls, dir

# Spostati in una cartella
Set-Location C:\progetti\mio-sito    # alias: cd
cd ..                                # sali di un livello
cd ~                                 # torna alla cartella utente

# Crea una cartella
New-Item -ItemType Directory progetti

# Crea una cartella e tutte quelle intermedie che mancano
New-Item -ItemType Directory -Force C:\progetti\web\esperimenti

# Leggi un file
Get-Content package.json             # alias: cat

# Cancella (attenzione: non passa dal cestino)
Remove-Item file.txt
Remove-Item -Recurse -Force cartella # cancella una cartella e il contenuto
```

Tre cose che ti fanno risparmiare ore:

```powershell
# 1. TAB completa i nomi. Scrivi "cd prog" e premi TAB.

# 2. FRECCIA SU ripercorre i comandi precedenti.

# 3. Ctrl+C ferma un processo in esecuzione.
#    Ti servirà continuamente: i server di sviluppo non finiscono da soli.
```

**Percorsi con spazi.** Windows ha cartelle con spazi nel nome (`C:\Program Files`, `C:\Users\Nome Cognome`). Vanno sempre fra virgolette:

```powershell
# ❌ SBAGLIATO — PowerShell legge due argomenti separati
cd C:\Users\Nome Cognome\progetti

# ✅ CORRETTO
cd "C:\Users\Nome Cognome\progetti"
```

**Dove mettere i progetti.** Evita `Documenti` e il Desktop se sono sincronizzati con OneDrive: la sincronizzazione di `node_modules` — decine di migliaia di file piccoli — rallenta la macchina e ogni tanto corrompe un'installazione. Usa una cartella fuori dalla sincronizzazione:

```powershell
New-Item -ItemType Directory -Force C:\progetti
cd C:\progetti
```

---

## A3. Node.js: JavaScript fuori dal browser

> **Analogia:** JavaScript è nato come la lingua parlata dentro un solo edificio, il browser. Node.js ha preso il motore linguistico di quell'edificio (V8, lo stesso di Chrome) e lo ha portato fuori, dandogli il permesso di fare cose che nel browser sono vietate: aprire file, ascoltare su una porta di rete, avviare altri programmi. Stessa lingua, quartiere diverso, regole diverse.

Concretamente, Node ti serve per tre cose distinte, e conviene tenerle separate in testa:

1. **Far girare il tuo backend** — un server che risponde alle richieste HTTP. Questo è l'uso "ovvio".
2. **Far girare gli strumenti di sviluppo** — Vite, ESLint, Prettier, TypeScript, i test. Anche se il tuo progetto è solo frontend e non avrà mai un backend, ti serve comunque Node, perché gli strumenti che compilano e controllano il tuo codice sono scritti in JavaScript e girano su Node.
3. **Installare pacchetti** — `npm` arriva insieme a Node ed è la porta d'accesso all'ecosistema.

Il punto 2 è quello che sorprende chi inizia: **si installa Node anche per scrivere una pagina HTML statica**, perché senza Node non hai né un server di sviluppo con ricarica automatica, né un linter, né un formattatore.

**Verifica se ce l'hai già:**

```powershell
node --version
npm --version
```

```
# Output atteso (i numeri esatti variano):
v24.4.1
10.9.0

# Se invece vedi:
# node : Termine 'node' non riconosciuto come nome di cmdlet...
# allora Node non è installato, o non è nel PATH. Prosegui con A4.
```

**LTS e Current, e perché ti interessa.** Node pubblica due linee:

| Linea | Cosa significa | Quando usarla |
|---|---|---|
| **LTS** (Long Term Support) | Numero di versione **pari** (20, 22, 24…). Riceve correzioni di sicurezza per circa 30 mesi. | Sempre, per lavorare. È quello che le piattaforme di hosting e le librerie supportano. |
| **Current** | Numero **dispari** (21, 23, 25…) o l'ultima pari prima che entri in LTS. Ha le novità, ma vita breve. | Solo per provare funzionalità nuove in un progetto usa-e-getta. |

Le versioni cambiano nel tempo: la linea LTS attiva mentre leggi potrebbe non essere quella degli esempi. Il modo corretto di installarla non è scrivere un numero, è chiedere l'LTS corrente — vedi [A4](#a4-installare-node-con-nvm-windows). L'elenco aggiornato con le date di fine supporto sta su `nodejs.org/en/about/previous-releases`.

---

## A4. Installare Node con nvm-windows

Potresti scaricare l'installer da `nodejs.org` e finire in due minuti. **Non farlo.** Ecco perché.

> **Analogia:** installare Node dall'installer è come murare una lampadina nel soffitto invece di montare un portalampada. Funziona benissimo finché non devi cambiarla. Il giorno in cui un progetto richiede una versione diversa da quella murata, devi disinstallare tutto e ricominciare — e se hai due progetti che richiedono versioni diverse, non c'è soluzione.

Questo succede davvero: un progetto aziendale fermo su una versione vecchia e uno nuovo sulla LTS attuale sono la norma, non l'eccezione. **nvm-windows** (Node Version Manager per Windows) tiene installate più versioni e ti fa passare dall'una all'altra con un comando.

### Installazione

1. Vai su `github.com/coreybutler/nvm-windows/releases`.
2. Scarica `nvm-setup.exe` dell'ultima release.
3. **Prima di eseguirlo, disinstalla Node se lo avevi installato con l'installer ufficiale** — Pannello di controllo → Programmi → Node.js → Disinstalla. Due installazioni in parallelo si contendono il PATH e il risultato è imprevedibile.
4. Esegui `nvm-setup.exe`, accetta i percorsi proposti.
5. **Chiudi e riapri PowerShell.** Il PATH viene letto all'avvio della sessione: senza riaprire, `nvm` non risulta installato. Vedi [B1](#b1-path-e-shim-perché-comando-non-trovato).

### Uso

```powershell
# Verifica che nvm risponda
nvm version
# 1.2.2

# Installa l'ultima LTS — questo è il comando giusto,
# non scrivere un numero di versione a mano
nvm install lts

# Elenca cosa hai installato
nvm list
#     24.4.1
#   * 22.14.0 (Currently using 64-bit executable)

# Attiva una versione
nvm use 24.4.1

# Verifica
node --version
# v24.4.1
```

**Il passo che tutti dimenticano:** `nvm install` scarica, `nvm use` attiva. Dopo un `install` senza `use`, `node --version` continua a mostrare la versione precedente e sembra che l'installazione sia fallita.

**PowerShell come amministratore.** `nvm use` modifica un collegamento simbolico dentro `C:\Program Files\nodejs`, e su alcune configurazioni serve il terminale come amministratore. Se ottieni un errore di accesso negato:

```powershell
# Chiudi PowerShell, poi: tasto destro sull'icona di PowerShell
# → "Esegui come amministratore", e ripeti nvm use.
```

### Fissare la versione per progetto

Un file `.nvmrc` nella radice del progetto dichiara quale versione serve. È una riga:

```
24
```

```powershell
# Nella cartella del progetto
nvm use $(Get-Content .nvmrc)
```

Su Windows `nvm use` non legge `.nvmrc` da solo — è una limitazione di nvm-windows rispetto alla versione Unix. Il file resta comunque utile: lo leggono le pipeline di CI (`actions/setup-node` lo supporta nativamente) e i colleghi su macOS o Linux. Riprendiamo il discorso in [D4](#d4-riprodurre-lo-stesso-ambiente-su-unaltra-macchina-e-in-ci).

---

## A5. npm e `package.json`: il contratto del progetto

`npm` si installa insieme a Node. Fa due cose: scarica pacchetti dal registro pubblico e lancia gli script che dichiari.

### Creare un progetto

```powershell
New-Item -ItemType Directory -Force C:\progetti\primo-sito
cd C:\progetti\primo-sito

# Crea package.json accettando tutti i default
npm init -y
```

```json
// package.json — generato da npm init -y
{
  "name": "primo-sito",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "keywords": [],
  "author": "",
  "license": "ISC"
}
```

Questo file è **il contratto del progetto**: dice cosa serve per farlo funzionare e come si avvia. Chiunque riceva la cartella senza `node_modules` può ricostruire tutto leggendo questo file.

### Installare dipendenze

```powershell
# Dipendenza di produzione: serve anche all'applicazione in esecuzione
npm install dayjs

# Dipendenza di sviluppo: serve solo a te che sviluppi
npm install --save-dev vite
# forma breve: npm i -D vite
```

Il `package.json` cambia così:

```json
{
  "dependencies": {
    "dayjs": "^1.11.13"
  },
  "devDependencies": {
    "vite": "^7.0.0"
  }
}
```

**La distinzione non è cosmetica.** Quando costruisci l'immagine Docker per la produzione installi solo le `dependencies`: le `devDependencies` sono centinaia di megabyte di strumenti che sul server non servono. Metterle nel posto sbagliato significa immagini enormi e superficie di attacco inutile.

| Va in `dependencies` | Va in `devDependencies` |
|---|---|
| Framework usati a runtime (`react`, `express`) | Bundler (`vite`, `webpack`) |
| Client di database (`pg`, `mongodb`) | Linter e formattatori (`eslint`, `prettier`) |
| Librerie di utilità usate dal codice (`zod`, `dayjs`) | Compilatore TypeScript (`typescript`) |
| | Framework di test (`vitest`, `playwright`) |
| | Tipi (`@types/node`) |

### Gli script

Il campo `scripts` è dove definisci i comandi del progetto:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "format": "prettier --write ."
  }
}
```

```powershell
npm run dev
npm run build
```

Perché passare da `npm run` invece di chiamare `vite` direttamente: gli script hanno nel PATH la cartella `node_modules/.bin`, quindi usano **la versione di Vite installata in questo progetto**, non una eventuale versione globale diversa. È la differenza fra "funziona sulla mia macchina" e "funziona".

Due nomi sono speciali e non vogliono `run`:

```powershell
npm start     # equivale a npm run start
npm test      # equivale a npm run test
```

### Cosa NON deve finire in Git

Prima ancora di scrivere codice, crea il `.gitignore`:

```gitignore
# .gitignore
node_modules/
dist/
build/
.env
.env.local
*.log
.DS_Store
Thumbs.db
.vite/
coverage/
```

`node_modules` è ricostruibile da `package.json` più il lockfile, pesa centinaia di megabyte e contiene binari compilati specifici per il sistema operativo. Non entra mai in Git. Ne parliamo in [B2](#b2-node_modules-lockfile-e-riproducibilità).

---

## A6. pnpm: lo stesso lavoro, meno disco

npm funziona. Il problema è come conserva i pacchetti: **ogni progetto ha la sua copia completa di tutto**. Dieci progetti che usano React hanno dieci copie di React sul disco.

> **Analogia:** npm è una biblioteca dove ogni lettore riceve una fotocopia integrale di ogni libro che consulta. pnpm è una biblioteca normale: il libro sta su uno scaffale centrale e ogni lettore riceve un segnalibro che punta lì. Occupa lo spazio di una copia sola, e prestarlo è istantaneo perché non c'è niente da fotocopiare.

Il "segnalibro" tecnico è un **hard link**: una voce di directory che punta agli stessi dati su disco. pnpm tiene un archivio unico (il *content-addressable store*) in `%LOCALAPPDATA%\pnpm\store` e ogni `node_modules` è fatto di link a quell'archivio.

### Installazione

```powershell
# Corepack arriva con Node e attiva pnpm senza installazioni globali
corepack enable pnpm

# Verifica
pnpm --version
# 9.15.0
```

Se `corepack` non è disponibile sulla tua versione di Node:

```powershell
npm install --global pnpm
```

### I comandi, tradotti da npm

| npm | pnpm |
|---|---|
| `npm install` | `pnpm install` (o `pnpm i`) |
| `npm install dayjs` | `pnpm add dayjs` |
| `npm install -D vite` | `pnpm add -D vite` |
| `npm uninstall dayjs` | `pnpm remove dayjs` |
| `npm run dev` | `pnpm dev` (`run` è opzionale) |
| `npm ci` | `pnpm install --frozen-lockfile` |
| `npx vite` | `pnpm dlx vite` |

**Non mescolare i due nel medesimo progetto.** Ogni package manager scrive il proprio lockfile (`package-lock.json` per npm, `pnpm-lock.yaml` per pnpm) e ognuno ignora quello dell'altro. Due lockfile nella stessa cartella significano che due colleghi installano versioni diverse e nessuno capisce perché.

```powershell
# ❌ SBAGLIATO — genera package-lock.json accanto a pnpm-lock.yaml
pnpm install
npm install express

# ✅ CORRETTO — un solo package manager per progetto
pnpm install
pnpm add express
```

In questo corso useremo **pnpm**. Tutti i comandi hanno l'equivalente npm nella tabella qui sopra, quindi se il tuo contesto aziendale impone npm non perdi nulla.

---

## A7. VS Code e le estensioni che servono davvero

Scaricalo da `code.visualstudio.com`. Durante l'installazione spunta **"Aggiungi a PATH"** e **"Apri con Code"** nel menu contestuale: la prima ti dà il comando `code`, la seconda il tasto destro su una cartella.

```powershell
# Apri VS Code nella cartella corrente
code .
```

### Le estensioni

Installa dalla barra laterale (`Ctrl+Shift+X`) o da terminale. Queste sono quelle che cambiano il lavoro quotidiano, non un elenco esaustivo:

```powershell
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension bradlc.vscode-tailwindcss
code --install-extension usernamehw.errorlens
code --install-extension eamodio.gitlens
code --install-extension rangav.vscode-thunder-client
code --install-extension formulahendry.auto-rename-tag
code --install-extension christian-kohler.path-intellisense
```

| Estensione | Cosa fa | Perché non se ne fa a meno |
|---|---|---|
| **ESLint** | Segnala errori logici e pattern problematici mentre scrivi | Trova i bug prima di eseguire il codice |
| **Prettier** | Riformatta il codice al salvataggio | Elimina ogni discussione sullo stile |
| **Error Lens** | Scrive l'errore *sulla riga stessa*, non solo nel pannello Problemi | Vedi il problema dove sta, senza spostare gli occhi |
| **GitLens** | Mostra chi ha scritto ogni riga e quando | Rispondere a "perché questa riga esiste?" senza aprire il terminale |
| **Tailwind IntelliSense** | Autocompletamento delle classi, anteprima dei colori | Le classi Tailwind sono centinaia: a memoria non si fa |
| **Thunder Client** | Client HTTP dentro l'editor | Testare un endpoint senza cambiare finestra |
| **Auto Rename Tag** | Rinomina il tag di chiusura quando modifichi l'apertura | Errore banale, ricorrente, eliminato |
| **Path Intellisense** | Autocompleta i percorsi dei file negli import | Gli import sbagliati sono la prima causa di build rotte |

TypeScript non è un'estensione: VS Code lo include già.

### La configurazione che serve

Crea `.vscode/settings.json` **dentro il progetto**, non nelle impostazioni globali. Così la configurazione viaggia con il repository e vale per tutti:

```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "files.eol": "\n",
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true,
  "editor.tabSize": 2,
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true
}
```

Riga per riga, quello che ottieni:

- `formatOnSave` — ogni salvataggio riformatta. Smetti di pensare all'indentazione.
- `codeActionsOnSave` con ESLint — le correzioni automatiche (import non usati, `let` che dovrebbe essere `const`) si applicano da sole.
- `files.eol: "\n"` — fine riga in stile Unix anche su Windows. Ci torniamo in [B6](#b6-git-configurato-per-il-web-la-trappola-dei-fine-riga): è la causa più comune di diff illeggibili nei team misti.
- `typescript.tsdk` — usa la versione di TypeScript del progetto, non quella integrata in VS Code. Senza questa riga vedi errori che in `pnpm build` non compaiono, e viceversa.

---

## A8. Il primo progetto: da cartella vuota a pagina che gira

Adesso mettiamo insieme tutto. **Vite** è lo strumento che serve la pagina durante lo sviluppo e la costruisce per la produzione.

```powershell
cd C:\progetti

# Crea un progetto Vite con template "vanilla" (HTML + CSS + JS, nessun framework)
pnpm create vite primo-sito --template vanilla

cd primo-sito
pnpm install
pnpm dev
```

```
# Output atteso:
  VITE v7.0.0  ready in 312 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

Apri `http://localhost:5173/` nel browser. La pagina c'è.

**La cosa importante viene adesso.** Lascia il terminale in esecuzione, apri `index.html` in VS Code, cambia il testo dentro `<h1>` e salva. Il browser si aggiorna da solo, senza che tu tocchi nulla. Questo è l'**Hot Module Replacement**: Vite tiene aperto un canale con il browser e gli spedisce solo il pezzo cambiato.

Struttura di quello che è stato creato:

```
primo-sito/
├── index.html          ← il punto d'ingresso. Vite parte da qui.
├── package.json        ← dipendenze e script
├── pnpm-lock.yaml      ← le versioni esatte installate
├── .gitignore
├── public/             ← file copiati così come sono (favicon, robots.txt)
│   └── vite.svg
└── src/
    ├── main.js         ← il JavaScript, importato da index.html
    ├── style.css
    ├── counter.js
    └── javascript.svg
```

```html
<!-- index.html -->
<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Il mio primo sito</title>
  </head>
  <body>
    <div id="app"></div>
    <!-- type="module" è ciò che permette gli import ES6 -->
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

### Sviluppo e produzione sono due cose diverse

```powershell
# Ctrl+C per fermare il server di sviluppo, poi:
pnpm build
```

```
# Output atteso:
vite v7.0.0 building for production...
✓ 9 modules transformed.
dist/index.html                  0.46 kB │ gzip: 0.30 kB
dist/assets/index-C4z8kQ1x.css   1.24 kB │ gzip: 0.65 kB
dist/assets/index-DmY2p9Lf.js    2.31 kB │ gzip: 1.18 kB
✓ built in 287ms
```

`pnpm dev` non produce file: tiene tutto in memoria e ricompila al volo. `pnpm build` scrive in `dist/` i file veri, minificati e con un **hash nel nome** (`index-C4z8kQ1x.js`). L'hash cambia quando cambia il contenuto: è così che si può dire ai browser di tenere il file in cache per un anno senza mai servire una versione vecchia.

```powershell
# Servi la build di produzione in locale, per verificarla prima del deploy
pnpm preview
```

> **Regola:** quello che funziona con `dev` non è garantito che funzioni in `build`. Il server di sviluppo è permissivo, la build applica minificazione e tree shaking. Prova sempre `build` + `preview` prima di considerare finito un lavoro.

---

# Parte B — Comprensione Profonda

---

## B1. PATH e shim: perché "comando non trovato"

Quando scrivi `node` nel terminale, il sistema deve trovare `node.exe`. Non lo cerca ovunque: consulta un elenco ordinato di cartelle, la variabile d'ambiente **PATH**.

```powershell
# Vedi il PATH, una cartella per riga
$env:PATH -split ';'
```

```
# Output atteso (estratto):
C:\Windows\system32
C:\Windows
C:\Program Files\nodejs\
C:\Users\Renan\AppData\Roaming\npm
C:\Users\Renan\AppData\Local\Programs\Microsoft VS Code\bin
C:\Program Files\Git\cmd
```

L'ordine conta: viene usata la **prima** corrispondenza. Se hai due installazioni di Node, vince quella la cui cartella compare prima.

```powershell
# Quale eseguibile viene usato davvero?
(Get-Command node).Source
# C:\Program Files\nodejs\node.exe
```

### Come funziona nvm

`C:\Program Files\nodejs` non contiene Node: è un **collegamento simbolico** che nvm fa puntare alla versione attiva.

```
C:\Program Files\nodejs  ──(symlink)──►  C:\Users\Renan\AppData\Roaming\nvm\v24.4.1
                                          └── node.exe
                                          └── npm.cmd

nvm use 22.14.0 sposta il puntatore:

C:\Program Files\nodejs  ──(symlink)──►  C:\Users\Renan\AppData\Roaming\nvm\v22.14.0
```

Il PATH non cambia mai. Cambia dove punta il link. Da qui discendono due comportamenti che sembrano bug:

**1. Il PATH viene letto all'avvio della sessione.** Dopo aver installato qualcosa che modifica il PATH, i terminali già aperti non lo sanno.

```powershell
# ❌ Installi qualcosa, poi nello stesso terminale:
pnpm --version
# pnpm : Termine 'pnpm' non riconosciuto...

# ✅ Chiudi e riapri PowerShell. Oppure, per la sola sessione corrente:
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("PATH", "User")
```

**2. I pacchetti globali sono legati alla versione di Node.** `npm install --global` scrive dentro la cartella della versione attiva. Dopo `nvm use` di un'altra versione, quei pacchetti globali non ci sono più — non sono spariti, sono in un'altra cartella.

> **Conseguenza pratica:** installa il meno possibile a livello globale. Le dipendenze del progetto stanno nel progetto, e `pnpm dlx` (o `npx`) esegue uno strumento una volta sola senza installarlo.

```powershell
# Invece di installare globalmente per usarlo due volte
pnpm dlx degit sveltejs/template mio-progetto
```

### Diagnosticare "comando non trovato"

```powershell
# 1. È nel PATH?
$env:PATH -split ';' | Select-String "nodejs"

# 2. L'eseguibile esiste?
Test-Path "C:\Program Files\nodejs\node.exe"

# 3. Quale versione sta usando nvm?
nvm list

# 4. Il collegamento è valido?
Get-Item "C:\Program Files\nodejs" | Select-Object LinkType, Target
```

---

## B2. `node_modules`, lockfile e riproducibilità

`package.json` dichiara `"dayjs": "^1.11.13"`. Quel `^` significa "1.11.13 o qualsiasi versione successiva finché il primo numero resta 1". Quindi due installazioni fatte a distanza di un mese possono produrre alberi di dipendenze diversi.

> **Analogia:** `package.json` è la lista della spesa scritta a mano — "una scatola di pelati, marca a piacere". Il lockfile è lo scontrino: dice esattamente quale scatola, di quale marca, di quale lotto, hai comprato. La lista serve a fare la spesa; lo scontrino serve a rifare *esattamente la stessa* spesa fra sei mesi.

```yaml
# pnpm-lock.yaml (estratto, semplificato)
lockfileVersion: '9.0'

importers:
  .:
    dependencies:
      dayjs:
        specifier: ^1.11.13
        version: 1.11.13

packages:
  dayjs@1.11.13:
    resolution: {integrity: sha512-oaMBel6gjolK862uaPQOVTA7q3TZhuSvuMQAAglQDOWYO9A91IrAOUJEyKVlqJlHE0vq5p5UXxzdPfMH/x6xNg==}
```

Il campo `integrity` è un hash del contenuto del pacchetto: se qualcuno sostituisse quel pacchetto sul registro con una versione modificata, l'installazione fallirebbe. È la difesa di base contro gli attacchi alla supply chain, e funziona **solo se il lockfile è in Git**.

**Il lockfile va sempre committato.** Non è un file generato da ignorare: è parte della definizione del progetto.

```gitignore
# ❌ SBAGLIATO — così ogni macchina installa versioni diverse
node_modules/
pnpm-lock.yaml

# ✅ CORRETTO — node_modules no, il lockfile sì
node_modules/
```

### Due comandi diversi per due situazioni diverse

```powershell
# Sviluppo: risolve le versioni secondo package.json e AGGIORNA il lockfile
pnpm install

# CI e produzione: installa ESATTAMENTE il lockfile, fallisce se non combacia
pnpm install --frozen-lockfile
```

In CI usa sempre la seconda forma. Se qualcuno ha modificato `package.json` senza rigenerare il lockfile, vuoi che la pipeline si fermi con un errore chiaro, non che installi qualcosa che nessuno ha verificato.

### Perché `node_modules` è enorme

```powershell
# Conta i file (aspetta qualche secondo)
(Get-ChildItem -Recurse -File node_modules).Count
```

Anche un progetto piccolo arriva a decine di migliaia di file. La ragione è che ogni dipendenza porta le proprie dipendenze, ricorsivamente. È il motivo per cui:

- `node_modules` non va in Git;
- non va in una cartella sincronizzata con OneDrive o Dropbox;
- va escluso dalle scansioni dell'antivirus in tempo reale, se le installazioni sono lente;
- va escluso dalla ricerca di VS Code (lo fa già di default).

Quando qualcosa è inspiegabilmente rotto, la ricostruzione da zero è legittima:

```powershell
Remove-Item -Recurse -Force node_modules
Remove-Item -Force pnpm-lock.yaml   # solo se sospetti che il lockfile sia corrotto
pnpm install
```

Cancellare il lockfile è l'ultima risorsa, non la prima: significa rinunciare alle versioni verificate e riaprire la porta a un aggiornamento che rompe qualcosa.

---

## B3. Semver: cosa significano davvero `^` e `~`

Il versionamento semantico assegna un significato a ciascuno dei tre numeri:

```
        1  .  11  .  13
        │      │      │
        │      │      └── PATCH: correzione di bug, nessun cambiamento di comportamento
        │      └───────── MINOR: funzionalità nuove, retrocompatibili
        └──────────────── MAJOR: cambiamenti che rompono il codice esistente
```

I simboli davanti al numero dicono quanto margine concedi:

| Notazione | Accetta | Non accetta | Uso |
|---|---|---|---|
| `1.11.13` | solo 1.11.13 | tutto il resto | Quando una versione precisa è l'unica che funziona |
| `~1.11.13` | 1.11.x | 1.12.0 | Solo correzioni di bug |
| `^1.11.13` | 1.x.x | 2.0.0 | **Il default di npm e pnpm** |
| `*` o `latest` | qualsiasi cosa | — | Mai, in un progetto reale |

**Il caso particolare dello zero.** Per le versioni `0.x.y` la specifica considera il progetto instabile e `^` si comporta in modo più stretto: `^0.5.2` accetta `0.5.x` ma **non** `0.6.0`. È corretto — in `0.x` un incremento di minor può contenere cambiamenti che rompono tutto.

```json
{
  "dependencies": {
    "dayjs": "^1.11.13",     // accetta 1.99.0, non accetta 2.0.0
    "qualcosa": "^0.5.2"     // accetta 0.5.9, NON accetta 0.6.0
  }
}
```

### Ispezionare cosa è installato davvero

```powershell
# Albero delle dipendenze dirette
pnpm list

# Fino a 2 livelli di profondità
pnpm list --depth 2

# Chi ha portato dentro questo pacchetto?
pnpm why dayjs

# Cosa è disponibile rispetto a cosa hai
pnpm outdated
```

```
# Output atteso di pnpm outdated:
┌─────────────┬─────────┬────────┐
│ Package     │ Current │ Latest │
├─────────────┼─────────┼────────┤
│ vite (dev)  │ 7.0.0   │ 7.1.2  │
├─────────────┼─────────┼────────┤
│ dayjs       │ 1.11.13 │ 2.0.1  │
└─────────────┴─────────┴────────┘
```

Aggiornare dentro il range dichiarato è di norma sicuro; superare un major richiede di leggere le note di rilascio.

```powershell
# Aggiorna restando dentro i range di package.json
pnpm update

# Supera i major — leggi prima i changelog
pnpm update --latest
```

---

## B4. ESLint e Prettier: due mestieri diversi

Vengono confusi di continuo. Fanno cose che non si sovrappongono:

| | ESLint | Prettier |
|---|---|---|
| **Domanda a cui risponde** | Questo codice è corretto? | Questo codice è leggibile allo stesso modo di tutto il resto? |
| **Esempio di segnalazione** | "questa variabile non è mai usata", "await dentro un ciclo" | "questa riga supera 80 colonne" |
| **Si discute?** | Sì, le regole sono scelte di progetto | No, e il punto è proprio quello |

> **Analogia:** ESLint è il revisore che ti dice che nel testo hai scritto due volte lo stesso paragrafo e che una frase non ha il verbo. Prettier è il tipografo: non legge il contenuto, impagina. Litigano solo se il revisore comincia a occuparsi dei margini — ed è esattamente il problema che si risolve disattivando le regole di stile di ESLint.

### Installazione e configurazione

```powershell
pnpm add -D eslint @eslint/js globals
pnpm add -D prettier eslint-config-prettier
```

```javascript
// eslint.config.js — formato "flat config", lo standard da ESLint 9
import js from '@eslint/js'
import globals from 'globals'
import prettier from 'eslint-config-prettier'

export default [
  js.configs.recommended,

  {
    files: ['**/*.{js,mjs,cjs}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,   // window, document, fetch...
        ...globals.node,      // process, __dirname...
      },
    },
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'prefer-const': 'error',
      eqeqeq: ['error', 'always'],
    },
  },

  // DEVE stare per ultimo: disattiva le regole di ESLint
  // che si sovrappongono a Prettier.
  prettier,
]
```

```json
// .prettierrc
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "printWidth": 100,
  "trailingComma": "all",
  "endOfLine": "lf"
}
```

```
# .prettierignore
node_modules
dist
pnpm-lock.yaml
```

```json
// package.json — gli script
{
  "scripts": {
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  }
}
```

`format:check` è la variante che serve in CI: non modifica nulla, esce con codice diverso da zero se qualcosa non è formattato.

### Le regole che valgono la pena

```javascript
// eqeqeq — perché == fa conversioni implicite che nessuno ricorda
console.log(0 == '')        // true  ← praticamente mai quello che vuoi
console.log(0 == '0')       // true
console.log('' == '0')      // false ← e non è nemmeno transitivo
console.log(null == undefined)  // true

console.log(0 === '')       // false ← prevedibile
console.log(0 === '0')      // false

// prefer-const — una variabile mai riassegnata dichiarata come let
// è una domanda senza risposta per chi legge: "cambierà più avanti?"

// ❌ SBAGLIATO — chi legge deve leggere tutta la funzione per sapere se cambia
async function contaUtentiSbagliato() {
  let utenti = await recuperaUtenti()
  return utenti.length
}

// ✅ CORRETTO — la dichiarazione stessa risponde alla domanda
async function contaUtenti() {
  const utenti = await recuperaUtenti()
  return utenti.length
}
```

---

## B5. Chrome DevTools: i pannelli che userai ogni giorno

`F12` oppure `Ctrl+Shift+I`. Sei pannelli, ognuno per una domanda diversa.

```
┌──────────────────────────────────────────────────────────────────┐
│ Elements │ Console │ Sources │ Network │ Performance │ Application│
└────┬─────────┬─────────┬─────────┬──────────┬─────────────┬──────┘
     │         │         │         │          │             │
     │         │         │         │          │             └─ Cosa è
     │         │         │         │          │                salvato?
     │         │         │         │          │                (cookie,
     │         │         │         │          │                localStorage,
     │         │         │         │          │                service worker)
     │         │         │         │          │
     │         │         │         │          └─ Perché è lento?
     │         │         │         │             (registrazione, flame chart)
     │         │         │         │
     │         │         │         └─ Cosa ha chiesto e cosa ha ricevuto?
     │         │         │            (richieste, header, tempi, payload)
     │         │         │
     │         │         └─ Perché fa questo?
     │         │            (breakpoint, esecuzione passo passo)
     │         │
     │         └─ Cosa dice il codice?
     │            (log, errori, REPL)
     │
     └─ Com'è fatta la pagina adesso?
        (DOM live, CSS calcolato, box model)
```

### Elements

Mostra il DOM **come è adesso**, non l'HTML che il server ha mandato. Se JavaScript ha aggiunto elementi, li vedi qui e non nel sorgente della pagina.

Cosa fare qui:
- Modificare CSS in tempo reale nel pannello Styles per provare un valore prima di scriverlo nel file.
- Leggere `Computed` per sapere quale regola sta vincendo e da dove viene.
- Guardare il box model in fondo a `Computed`: margin, border, padding, content in un colpo d'occhio.

### Console

```javascript
// Non solo log: la console ha metodi che fanno risparmiare tempo

console.table([
  { nome: 'Anna', ruolo: 'admin' },
  { nome: 'Marco', ruolo: 'utente' },
])
// Stampa una tabella vera, non un oggetto da srotolare

console.group('Caricamento dati')
console.log('inizio')
console.log('fine')
console.groupEnd()
// Raggruppa e permette di collassare

console.time('query')
// ...operazione da misurare...
console.timeEnd('query')
// query: 143.28ms

// $0 è l'elemento selezionato in Elements — utilissimo
$0.classList

// $$ è document.querySelectorAll abbreviato
$$('a[href^="http"]').length
```

### Network

Il pannello dove si risolvono più problemi di tutti gli altri messi insieme.

- **Disable cache** (con DevTools aperto) — evita di inseguire per mezz'ora un file vecchio in cache.
- **Throttling** → `Slow 4G` — la tua fibra nasconde ogni problema di performance.
- Colonna **Status**: `200` ok, `304` non modificato, `404` non trovato, `500` errore del server, **`(failed) net::ERR_...`** è il tipico errore di CORS o di connessione.
- Fai clic su una richiesta → `Headers` per vedere cosa è stato mandato e ricevuto, `Payload` per il corpo, `Response` per la risposta grezza.
- Tasto destro su una richiesta → **Copy → Copy as fetch** ti dà il codice JavaScript per rifarla. **Copy as cURL** ti dà il comando da terminale.

### Application

- **Storage** → `Local storage`, `Session storage`, `Cookies`. Qui verifichi se un token è dove pensi che sia — e se un cookie ha davvero i flag `HttpOnly` e `Secure`.
- **Service Workers** — registrazione, stato, il pulsante `Unregister`. Un service worker vecchio che serve file in cache è una delle cause più frustranti di "ho corretto il bug ma il sito mostra ancora l'errore".
- **Clear storage** → `Clear site data` azzera tutto per quel dominio.

### Firefox, per due cose specifiche

Firefox Developer Edition ha due ispettori che Chrome non eguaglia: **Grid Inspector** e **Flexbox Inspector**. Disegnano sopra la pagina le linee della griglia con i numeri di riga e colonna, e mostrano per ogni elemento flex quanto spazio ha chiesto e quanto ne ha ottenuto. Quando un layout CSS Grid non torna, aprilo lì.

---

## B6. Git configurato per il web: la trappola dei fine riga

Git dovrebbe essere già installato (`git --version`). Se manca: `git-scm.com`.

```powershell
git config --global user.name "Nome Cognome"
git config --global user.email "tua@email.it"
git config --global init.defaultBranch main
git config --global core.editor "code --wait"

# Verifica
git config --global --list
```

### Il problema dei fine riga

Windows termina le righe con due caratteri (`CRLF`, ritorno carrello più avanzamento riga); Linux e macOS con uno solo (`LF`). I server web, Docker e la maggior parte degli strumenti si aspettano `LF`.

Se non si interviene, succede questo: apri un file scritto da un collega su macOS, il tuo editor lo salva con `CRLF`, e Git segnala che **ogni riga del file è cambiata** anche se hai corretto un refuso. La revisione diventa impossibile.

> **Analogia:** è come se ogni volta che presti un libro a qualcuno lui te lo restituisse ricopiato a mano con la sua calligrafia. Il testo è identico, ma per capire cosa ha cambiato devi rileggere tutto.

La soluzione non è una configurazione globale, è un file nel repository che vale per chiunque:

```gitattributes
# .gitattributes — questo file va committato

# Normalizza tutto a LF dentro il repository,
# lasciando che Git decida cosa scrivere sul disco.
* text=auto eol=lf

# File che devono restare CRLF anche su disco
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf

# File binari: Git non deve toccarli
*.png binary
*.jpg binary
*.webp binary
*.woff binary
*.woff2 binary
*.pdf binary
```

Con `files.eol: "\n"` in `.vscode/settings.json` (vedi [A7](#a7-vs-code-e-le-estensioni-che-servono-davvero)) e questo `.gitattributes`, il problema sparisce alla radice invece di essere gestito ogni volta.

### Il flusso quotidiano

```powershell
# Inizializzare
git init
git add .
git commit -m "chore: struttura iniziale del progetto"

# Il ciclo di lavoro
git status                    # cosa è cambiato?
git diff                      # cosa esattamente?
git add src/main.js           # prepara un file specifico
git add -p                    # prepara pezzo per pezzo, rileggendo
git commit -m "feat: aggiunge validazione del form di contatto"
git log --oneline --graph     # la storia in forma leggibile

# Lavorare su un branch
git switch -c feat/form-contatti
# ...lavori...
git switch main
git merge feat/form-contatti
```

`git add -p` merita attenzione: mostra ogni modifica e chiede se includerla. È il modo più efficace per accorgersi di aver lasciato un `console.log` o una chiave di prova prima che finisca nella storia del repository.

### Il file che non deve mai entrare

```powershell
# Se hai già committato .env per errore, rimuoverlo dal commit NON basta:
# resta nella storia e chiunque abbia il repository può recuperarlo.

# 1. Toglilo dal tracking
git rm --cached .env
echo ".env" >> .gitignore
git commit -m "chore: rimuove .env dal tracking"

# 2. RUOTA LE CREDENZIALI. Sempre. Non c'è alternativa:
#    quel segreto va considerato compromesso.
```

Riprendiamo il tema in [B8](#b8-variabili-dambiente-e-env) e nel `tutorial_14_sicurezza_web.md`.

---

## B7. Docker: i servizi locali senza sporcare il sistema

Prima o poi ti serviranno PostgreSQL, Redis o MongoDB. Installarli sul sistema significa servizi che partono all'avvio, versioni difficili da cambiare e configurazioni che divergono da quelle di produzione.

> **Analogia:** installare PostgreSQL sul sistema è come tenere un frigorifero industriale in salotto perché ogni tanto ti serve. Docker è affittarne uno per il tempo che serve, con la garanzia che sia identico a quello che useranno gli altri, e restituirlo senza lasciare traccia.

### Installazione

Scarica **Docker Desktop** da `docker.com`. Su Windows 10/11 richiede **WSL2**: l'installer lo propone, accetta.

```powershell
# Verifica dopo il riavvio
docker --version
docker compose version
```

### Un file, tutti i servizi

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:17-alpine
    container_name: dev-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: sviluppo
      POSTGRES_PASSWORD: sviluppo_locale
      POSTGRES_DB: app_dev
    ports:
      - '5432:5432'
    volumes:
      - dati-postgres:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U sviluppo -d app_dev']
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: dev-redis
    restart: unless-stopped
    ports:
      - '6379:6379'
    volumes:
      - dati-redis:/data

  mongo:
    image: mongo:8
    container_name: dev-mongo
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: sviluppo
      MONGO_INITDB_ROOT_PASSWORD: sviluppo_locale
    ports:
      - '27017:27017'
    volumes:
      - dati-mongo:/data/db

volumes:
  dati-postgres:
  dati-redis:
  dati-mongo:
```

```powershell
# Avvia tutto in background
docker compose up -d

# Cosa sta girando
docker compose ps

# I log di un servizio, in tempo reale
docker compose logs -f postgres

# Ferma, mantenendo i dati
docker compose stop

# Ferma e rimuove i container, mantenendo i dati nei volumi
docker compose down

# ⚠ Ferma e CANCELLA anche i dati
docker compose down -v
```

Due dettagli del file che non sono decorativi:

- **`volumes:`** — senza un volume nominato, i dati vivono dentro il container e spariscono con `docker compose down`. Con il volume, sopravvivono.
- **`healthcheck:`** — dice a Docker come capire se PostgreSQL è pronto ad accettare connessioni, non solo se il processo è partito. Serve quando un altro servizio deve aspettarlo con `depends_on: condition: service_healthy`.

**La password qui è finta e locale.** `sviluppo_locale` va bene per un database che ascolta solo su `localhost` e contiene dati di prova. Non è un modello per la produzione: lì le credenziali arrivano da un gestore di segreti, mai da un file nel repository.

### Connettersi

```powershell
# PostgreSQL, dal container
docker compose exec postgres psql -U sviluppo -d app_dev

# Redis
docker compose exec redis redis-cli
```

```
# Stringhe di connessione, da mettere in .env
DATABASE_URL=postgresql://sviluppo:sviluppo_locale@localhost:5432/app_dev
REDIS_URL=redis://localhost:6379
MONGO_URL=mongodb://sviluppo:sviluppo_locale@localhost:27017
```

---

## B8. Variabili d'ambiente e `.env`

La configurazione che cambia fra la tua macchina, lo staging e la produzione non sta nel codice. Sta nell'ambiente.

```
# .env — NON va in Git
DATABASE_URL=postgresql://sviluppo:sviluppo_locale@localhost:5432/app_dev
JWT_SECRET=una-stringa-lunga-e-casuale-solo-per-lo-sviluppo
PORT=3000
```

```
# .env.example — QUESTO va in Git
# Copia in .env e compila con i valori reali.
DATABASE_URL=postgresql://utente:password@localhost:5432/nome_db
JWT_SECRET=
PORT=3000
```

`.env.example` risolve un problema concreto: chi clona il repository sa quali variabili servono senza doverle indovinare leggendo il codice o chiedendo.

```gitignore
.env
.env.local
.env.*.local

# l'esempio invece si committa
!.env.example
```

### Leggere le variabili

Da Node 20 in poi non serve la libreria `dotenv` per i casi semplici:

```javascript
// server.js
// Avvia con: node --env-file=.env server.js

const porta = process.env.PORT ?? 3000
const urlDatabase = process.env.DATABASE_URL

if (!urlDatabase) {
  // Fallire subito e con un messaggio chiaro è molto meglio
  // che scoprire alla prima query che la variabile mancava.
  throw new Error('DATABASE_URL non impostata. Copia .env.example in .env.')
}

console.log(`Server in ascolto sulla porta ${porta}`)
```

### La distinzione che conta: frontend e backend

Questo è il punto in cui si commettono gli errori più gravi.

Vite include nel bundle **ogni** variabile il cui nome inizia con `VITE_`. Non è un
comportamento accidentale ed è documentato: quel prefisso serve proprio a dichiarare che il
valore può diventare pubblico.

```
# .env — ❌ SBAGLIATO
# La chiave segreta ha il prefisso VITE_, quindi finisce nel JavaScript
# scaricato dal browser, leggibile da chiunque apra DevTools.
VITE_STRIPE_SECRET_KEY=sk_live_51H8xQeEsempio
```

```
# .env — ✅ CORRETTO
# Senza prefisso: resta sul server, il bundle non la vede.
STRIPE_SECRET_KEY=sk_live_51H8xQeEsempio

# Con prefisso: è la chiave pubblicabile, progettata per stare nel browser.
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_51H8xQeEsempio
```

```javascript
// src/main.js — nel frontend si legge da import.meta.env
const chiavePubblica = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY

// process.env qui non esiste: nel browser non c'è nessun processo Node
```

> **Regola:** il prefisso `VITE_` (o `NEXT_PUBLIC_` in Next.js) è una **dichiarazione che quel valore sarà pubblico**. Se qualcosa non può essere pubblico, non deve avere quel prefisso, e il codice che lo usa deve girare sul server.

**Verificare di non aver sbagliato:**

```powershell
pnpm build
Select-String -Path "dist/assets/*.js" -Pattern "sk_live|SECRET|PRIVATE"
```

Se questo comando trova qualcosa, hai un segreto nel bundle. Va rimosso e la credenziale va ruotata.

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Diagnosticare quale Node è in uso

**Obiettivo:** scrivere uno script PowerShell che riporti la versione attiva di Node, dove si trova l'eseguibile, quali versioni sono installate in nvm e se la cartella corrente dichiara una versione con `.nvmrc`.

```powershell
# diagnostica-node.ps1

Write-Output "=== Ambiente Node ==="

# Versione attiva
$versioneNode = node --version
Write-Output "Node attivo:      $versioneNode"

# Percorso reale dell'eseguibile
$percorsoNode = (Get-Command node -ErrorAction SilentlyContinue).Source
Write-Output "Eseguibile:       $percorsoNode"

# Package manager disponibili
$versioneNpm = npm --version
Write-Output "npm:              $versioneNpm"

$versionePnpm = try { pnpm --version } catch { "non installato" }
Write-Output "pnpm:             $versionePnpm"

# Versioni gestite da nvm
Write-Output ""
Write-Output "=== Versioni installate in nvm ==="
nvm list

# Versione richiesta dal progetto
Write-Output ""
if (Test-Path .nvmrc) {
    $versioneRichiesta = (Get-Content .nvmrc).Trim()
    Write-Output "Il progetto richiede Node $versioneRichiesta (da .nvmrc)"

    # Confronto: .nvmrc contiene "24", node --version restituisce "v24.4.1"
    $majorAttuale = $versioneNode.TrimStart('v').Split('.')[0]
    if ($majorAttuale -eq $versioneRichiesta.TrimStart('v').Split('.')[0]) {
        Write-Output "Versione corretta."
    } else {
        Write-Output "DISALLINEAMENTO: attivo $majorAttuale, richiesto $versioneRichiesta"
        Write-Output "Esegui: nvm use $versioneRichiesta"
    }
} else {
    Write-Output "Nessun .nvmrc: il progetto non dichiara una versione."
}
```

```
# Output atteso in un progetto allineato:
=== Ambiente Node ===
Node attivo:      v24.4.1
Eseguibile:       C:\Program Files\nodejs\node.exe
npm:              10.9.0
pnpm:             9.15.0

=== Versioni installate in nvm ===
  * 24.4.1 (Currently using 64-bit executable)
    22.14.0

Il progetto richiede Node 24 (da .nvmrc)
Versione corretta.
```

---

### Esercizio 2 — Distinguere dependencies da devDependencies

**Obiettivo:** dato un elenco di pacchetti, collocarli nel campo giusto e giustificare ogni scelta con una riga.

```json
// package.json — soluzione commentata
{
  "name": "esercizio-dipendenze",
  "type": "module",
  "dependencies": {
    "express": "^5.1.0",
    "pg": "^8.13.1",
    "zod": "^3.24.1",
    "dayjs": "^1.11.13"
  },
  "devDependencies": {
    "vite": "^7.0.0",
    "eslint": "^9.18.0",
    "prettier": "^3.4.2",
    "typescript": "^5.7.3",
    "vitest": "^2.1.8",
    "@types/express": "^5.0.0"
  }
}
```

```
# Motivazione, pacchetto per pacchetto:
#
# dependencies — il codice le importa e girano in produzione
#   express   il server è express: senza, l'applicazione non parte
#   pg        il client PostgreSQL serve a ogni query a runtime
#   zod       se valida gli input delle richieste, gira in produzione
#   dayjs     se formatta date mostrate all'utente, gira in produzione
#
# devDependencies — servono a costruire, controllare o testare
#   vite         costruisce il bundle; il risultato non ha bisogno di lui
#   eslint       controlla il codice sorgente, mai il codice in esecuzione
#   prettier     formatta i file sorgente
#   typescript   compila; in produzione gira JavaScript
#   vitest       esegue i test, che non si eseguono in produzione
#   @types/*     esistono solo per il compilatore, spariscono nel JS emesso
#
# Il criterio in una domanda sola:
#   "se cancello questo pacchetto dal server dove l'app è già costruita,
#    l'applicazione smette di funzionare?"
#   Sì → dependencies.  No → devDependencies.
```

---

### Esercizio 3 — Leggere i range semver

**Obiettivo:** per ogni riga, dire quali versioni sono accettate.

```javascript
// verifica-semver.js
// Esegui con: node verifica-semver.js

const casi = [
  { range: '1.2.3',    candidate: ['1.2.3', '1.2.4', '1.3.0', '2.0.0'] },
  { range: '~1.2.3',   candidate: ['1.2.3', '1.2.9', '1.3.0', '2.0.0'] },
  { range: '^1.2.3',   candidate: ['1.2.3', '1.9.9', '2.0.0', '1.2.2'] },
  { range: '^0.5.2',   candidate: ['0.5.2', '0.5.9', '0.6.0', '1.0.0'] },
]

/**
 * Verifica se una versione rientra nel range.
 * Implementazione didattica: gestisce solo i casi esatti, ~ e ^.
 * In produzione si usa la libreria `semver`.
 */
function versioneAccettata(range, versione) {
  const [majV, minV, patV] = versione.split('.').map(Number)

  if (range.startsWith('~')) {
    const [maj, min, pat] = range.slice(1).split('.').map(Number)
    // ~1.2.3 → major e minor fissi, patch >= 3
    return majV === maj && minV === min && patV >= pat
  }

  if (range.startsWith('^')) {
    const [maj, min, pat] = range.slice(1).split('.').map(Number)
    if (maj > 0) {
      // ^1.2.3 → major fisso, il resto può salire
      return majV === maj && (minV > min || (minV === min && patV >= pat))
    }
    // ^0.x.y → anche il minor è bloccato: in 0.x un minor può rompere tutto
    return majV === 0 && minV === min && patV >= pat
  }

  return range === versione
}

// Test
for (const { range, candidate } of casi) {
  console.log(`\nRange ${range}`)
  for (const v of candidate) {
    const esito = versioneAccettata(range, v) ? 'accettata' : 'RIFIUTATA'
    console.log(`  ${v.padEnd(8)} ${esito}`)
  }
}
```

```
# Output atteso:

Range 1.2.3
  1.2.3    accettata
  1.2.4    RIFIUTATA
  1.3.0    RIFIUTATA
  2.0.0    RIFIUTATA

Range ~1.2.3
  1.2.3    accettata
  1.2.9    accettata
  1.3.0    RIFIUTATA
  2.0.0    RIFIUTATA

Range ^1.2.3
  1.2.3    accettata
  1.9.9    accettata
  2.0.0    RIFIUTATA
  1.2.2    RIFIUTATA

Range ^0.5.2
  0.5.2    accettata
  0.5.9    accettata
  0.6.0    RIFIUTATA
  1.0.0    RIFIUTATA
```

---

### Esercizio 4 — Trovare un segreto finito nel bundle

**Obiettivo:** costruire un progetto che espone per errore una chiave segreta, dimostrare che è nel bundle, poi correggerlo.

```powershell
# 1. Prepara il caso sbagliato
pnpm create vite prova-segreti --template vanilla
cd prova-segreti
pnpm install
```

```
# .env — la versione SBAGLIATA
VITE_API_SECRET=sk_live_51H8xQeFakeKeyPerEsercizio
```

```javascript
// src/main.js — la versione SBAGLIATA
const segreto = import.meta.env.VITE_API_SECRET
document.querySelector('#app').innerHTML = `<p>Applicazione avviata</p>`
console.log('chiave caricata', segreto?.slice(0, 6))
```

```powershell
# 2. Costruisci e cerca il segreto nel risultato
pnpm build
Select-String -Path "dist/assets/*.js" -Pattern "sk_live"
```

```
# Output atteso — il segreto È nel file servito al browser:
dist\assets\index-BqK2mN7x.js:1:...const s="sk_live_51H8xQeFakeKeyPerEsercizio"...
```

```javascript
// 3. LA CORREZIONE
//
// La chiave segreta non deve mai raggiungere il browser. La si sposta
// sul server e il frontend chiama un endpoint che la usa per suo conto.

// .env — senza prefisso VITE_, quindi invisibile al bundle
// API_SECRET=sk_live_51H8xQeFakeKeyPerEsercizio

// server.js — gira su Node, non nel browser
import express from 'express'

const app = express()
const chiaveSegreta = process.env.API_SECRET

if (!chiaveSegreta) {
  throw new Error('API_SECRET non impostata.')
}

app.post('/api/pagamento', async (richiesta, risposta) => {
  // La chiave viene usata QUI, sul server. Il browser non la vede mai.
  const esito = await chiamaFornitorePagamenti(chiaveSegreta, richiesta.body)
  risposta.json({ stato: esito.stato })
})

app.listen(3000)

// src/main.js — il frontend chiama l'endpoint, senza conoscere la chiave
async function avviaPagamento(importo) {
  const risposta = await fetch('/api/pagamento', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ importo }),
  })
  return risposta.json()
}
```

```powershell
# 4. Verifica che la correzione funzioni
pnpm build
Select-String -Path "dist/assets/*.js" -Pattern "sk_live"
# Nessun risultato: il segreto non è più nel bundle.
```

```
# Nota che chiude l'esercizio:
# se un segreto è STATO pubblicato anche una sola volta, rimuoverlo
# non basta. Va ruotato presso il fornitore. Il bundle potrebbe essere
# ancora nella cache di un CDN, nella cronologia di Git o nell'archivio
# di una build precedente.
```

---

### Esercizio 5 — Verificare che l'ambiente Docker sia davvero pronto

**Obiettivo:** scrivere uno script che avvia i servizi e attende che PostgreSQL accetti connessioni, invece di sperare che due secondi bastino.

```powershell
# avvia-servizi.ps1

Write-Output "Avvio dei servizi..."
docker compose up -d

$tentativiMassimi = 30
$tentativo = 0
$pronto = $false

while ($tentativo -lt $tentativiMassimi -and -not $pronto) {
    $tentativo++

    # pg_isready esce con 0 quando il server accetta connessioni
    docker compose exec -T postgres pg_isready -U sviluppo -d app_dev *> $null

    if ($?) {
        $pronto = $true
        Write-Output "PostgreSQL pronto dopo $tentativo tentativi."
    } else {
        Write-Output "Attendo PostgreSQL... ($tentativo/$tentativiMassimi)"
        Start-Sleep -Seconds 1
    }
}

if (-not $pronto) {
    Write-Output "PostgreSQL non è diventato disponibile. Controlla i log:"
    docker compose logs postgres
    exit 1
}

# Verifica Redis
docker compose exec -T redis redis-cli ping
Write-Output "Tutti i servizi sono operativi."
```

```
# Output atteso:
Avvio dei servizi...
[+] Running 3/3
 ✔ Container dev-postgres  Started
 ✔ Container dev-redis     Started
 ✔ Container dev-mongo     Started
Attendo PostgreSQL... (1/30)
Attendo PostgreSQL... (2/30)
PostgreSQL pronto dopo 3 tentativi.
PONG
Tutti i servizi sono operativi.
```

```
# Perché non "Start-Sleep -Seconds 5" e via:
# il tempo di avvio dipende dalla macchina, dal carico e dal fatto che
# il volume sia nuovo o esistente. Un'attesa fissa o è troppo corta
# (e la pipeline fallisce a intermittenza) o è troppo lunga
# (e ogni sviluppatore perde quei secondi ogni giorno).
# Interrogare lo stato reale risolve entrambi i casi.
```

---

### Esercizio 6 — Uno script `setup` che prepara tutto

**Obiettivo:** aggiungere al `package.json` un comando unico che un nuovo collega possa eseguire per passare da repository clonato ad ambiente funzionante.

```json
// package.json
{
  "scripts": {
    "setup": "node scripts/setup.js",
    "dev": "vite",
    "services:up": "docker compose up -d",
    "services:down": "docker compose down"
  }
}
```

```javascript
// scripts/setup.js
// Esegui con: pnpm setup

import { existsSync, copyFileSync, readFileSync } from 'node:fs'
import { execSync } from 'node:child_process'

const passi = []

function registra(descrizione, esito) {
  passi.push({ descrizione, esito })
  console.log(`${esito ? '  ok  ' : ' SALTA'} ${descrizione}`)
}

console.log('Preparazione ambiente di sviluppo\n')

// 1. Versione di Node
const versioneRichiesta = existsSync('.nvmrc')
  ? Number(readFileSync('.nvmrc', 'utf8').trim().replace(/^v/, '').split('.')[0])
  : null
const versioneAttuale = Number(process.versions.node.split('.')[0])

if (versioneRichiesta && versioneAttuale !== versioneRichiesta) {
  console.error(
    `\nNode ${versioneAttuale} attivo, il progetto richiede ${versioneRichiesta}.\n` +
      `Esegui: nvm use ${versioneRichiesta}\n`,
  )
  process.exit(1)
}
registra(`Node ${versioneAttuale}`, true)

// 2. File di ambiente
if (!existsSync('.env')) {
  if (existsSync('.env.example')) {
    copyFileSync('.env.example', '.env')
    registra('.env creato da .env.example — compilalo prima di procedere', true)
  } else {
    registra('.env assente e nessun .env.example disponibile', false)
  }
} else {
  registra('.env già presente', true)
}

// 3. Servizi Docker
try {
  execSync('docker compose up -d', { stdio: 'inherit' })
  registra('Servizi Docker avviati', true)
} catch {
  registra('Docker non disponibile — avvia Docker Desktop e riprova', false)
}

// 4. Riepilogo
const saltati = passi.filter((p) => !p.esito)
console.log(
  saltati.length === 0
    ? '\nAmbiente pronto. Avvia con: pnpm dev'
    : `\n${saltati.length} passo/i da completare a mano prima di procedere.`,
)
```

```
# Output atteso su una macchina già configurata:
Preparazione ambiente di sviluppo

  ok   Node 24
  ok   .env già presente
[+] Running 3/3
 ✔ Container dev-postgres  Running
 ✔ Container dev-redis     Running
 ✔ Container dev-mongo     Running
  ok   Servizi Docker avviati

Ambiente pronto. Avvia con: pnpm dev
```

---

## C2. Mini-progetto: il banco di lavoro

Costruiamo il repository che userai come base per tutti gli esercizi del corso. Non è un esempio giocattolo: è la configurazione minima che un progetto reale deve avere prima che si scriva la prima riga di logica.

### Cosa deve fare

1. Servire una pagina in sviluppo con ricarica automatica.
2. Controllare il codice con ESLint e formattarlo con Prettier, in modo automatico al salvataggio e verificabile da riga di comando.
3. Avere PostgreSQL e Redis disponibili in locale via Docker.
4. Dichiarare le variabili d'ambiente necessarie, senza esporre segreti.
5. Bloccare le versioni di Node e del package manager.
6. Essere clonabile e funzionante con un comando solo.

### Passo 1 — Struttura

```powershell
cd C:\progetti
pnpm create vite banco-di-lavoro --template vanilla
cd banco-di-lavoro
pnpm install
```

### Passo 2 — Bloccare le versioni

```
# .nvmrc
24
```

```json
// package.json — aggiungi questi campi
{
  "name": "banco-di-lavoro",
  "private": true,
  "type": "module",
  "packageManager": "pnpm@9.15.0",
  "engines": {
    "node": ">=24.0.0",
    "pnpm": ">=9.0.0"
  }
}
```

`packageManager` è letto da Corepack: chi lancia `npm install` in questo repository riceve un errore invece di generare un lockfile concorrente. `engines` fa fallire l'installazione su una versione di Node troppo vecchia, con un messaggio comprensibile.

### Passo 3 — Qualità del codice

```powershell
pnpm add -D eslint @eslint/js globals prettier eslint-config-prettier
```

```javascript
// eslint.config.js
import js from '@eslint/js'
import globals from 'globals'
import prettier from 'eslint-config-prettier'

export default [
  { ignores: ['dist/**', 'node_modules/**', 'coverage/**'] },

  js.configs.recommended,

  {
    files: ['src/**/*.js'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: globals.browser,
    },
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'prefer-const': 'error',
      eqeqeq: ['error', 'always'],
    },
  },

  {
    // Gli script e la configurazione girano su Node, non nel browser
    files: ['scripts/**/*.js', '*.config.js'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: globals.node,
    },
  },

  prettier,
]
```

```json
// .prettierrc
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "printWidth": 100,
  "trailingComma": "all",
  "endOfLine": "lf"
}
```

```
# .prettierignore
node_modules
dist
pnpm-lock.yaml
```

### Passo 4 — Servizi

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:17-alpine
    container_name: banco-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: sviluppo
      POSTGRES_PASSWORD: sviluppo_locale
      POSTGRES_DB: banco_dev
    ports:
      - '5432:5432'
    volumes:
      - dati-postgres:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U sviluppo -d banco_dev']
      interval: 5s
      timeout: 3s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: banco-redis
    restart: unless-stopped
    ports:
      - '6379:6379'
    volumes:
      - dati-redis:/data
    healthcheck:
      test: ['CMD', 'redis-cli', 'ping']
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  dati-postgres:
  dati-redis:
```

### Passo 5 — Ambiente

```
# .env.example — va in Git
DATABASE_URL=postgresql://sviluppo:sviluppo_locale@localhost:5432/banco_dev
REDIS_URL=redis://localhost:6379

# Visibile nel browser: usa il prefisso VITE_ solo per valori pubblici
VITE_APP_TITLE=Banco di lavoro
VITE_API_BASE_URL=http://localhost:3000
```

```gitignore
# .gitignore
node_modules/
dist/
coverage/
*.log

.env
.env.local
.env.*.local
!.env.example

.DS_Store
Thumbs.db
```

```gitattributes
# .gitattributes
* text=auto eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf
*.png binary
*.jpg binary
*.webp binary
*.woff2 binary
```

### Passo 6 — Editor

```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": { "source.fixAll.eslint": "explicit" },
  "files.eol": "\n",
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true,
  "editor.tabSize": 2
}
```

```json
// .vscode/extensions.json — VS Code le propone a chi apre il progetto
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "usernamehw.errorlens",
    "eamodio.gitlens",
    "rangav.vscode-thunder-client"
  ]
}
```

### Passo 7 — Gli script

```json
// package.json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "services:up": "docker compose up -d --wait",
    "services:down": "docker compose down",
    "services:reset": "docker compose down -v && docker compose up -d --wait",
    "check": "pnpm lint && pnpm format:check && pnpm build"
  }
}
```

`--wait` su `docker compose up` sfrutta gli `healthcheck` definiti: il comando ritorna solo quando i servizi sono davvero pronti, il che rende superfluo lo script di attesa dell'esercizio 5.

`check` è il comando che riproduce in locale quello che farà la CI. Se passa qui, passa lì.

### Passo 8 — Una pagina che dimostra che tutto funziona

```html
<!-- index.html -->
<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Banco di lavoro</title>
    <link rel="stylesheet" href="/src/style.css" />
  </head>
  <body>
    <main id="app">
      <h1 id="titolo">Caricamento…</h1>
      <ul id="diagnostica"></ul>
    </main>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

```javascript
// src/main.js
const titolo = import.meta.env.VITE_APP_TITLE ?? 'Applicazione senza nome'
document.querySelector('#titolo').textContent = titolo

/**
 * Righe di diagnostica dell'ambiente, mostrate in pagina.
 * Serve a verificare a colpo d'occhio che la configurazione sia caricata.
 */
const righe = [
  ['Modalità', import.meta.env.MODE],
  ['Base URL API', import.meta.env.VITE_API_BASE_URL ?? 'non impostata'],
  ['Build di produzione', String(import.meta.env.PROD)],
]

const elenco = document.querySelector('#diagnostica')
for (const [etichetta, valore] of righe) {
  const voce = document.createElement('li')
  voce.textContent = `${etichetta}: ${valore}`
  elenco.append(voce)
}
```

```css
/* src/style.css */
:root {
  --colore-testo: #1a1a1a;
  --colore-sfondo: #fafafa;
  --spazio: 1rem;
}

@media (prefers-color-scheme: dark) {
  :root {
    --colore-testo: #f0f0f0;
    --colore-sfondo: #1a1a1a;
  }
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
  color: var(--colore-testo);
  background: var(--colore-sfondo);
}

#app {
  max-width: 40rem;
  margin-inline: auto;
  padding: calc(var(--spazio) * 3) var(--spazio);
}

#diagnostica {
  padding-left: 0;
  list-style: none;
}

#diagnostica li {
  padding: 0.5rem 0;
  border-bottom: 1px solid color-mix(in srgb, var(--colore-testo) 15%, transparent);
  font-family: ui-monospace, monospace;
  font-size: 0.9rem;
}
```

### Passo 9 — Il README, che è parte del progetto

````markdown
# Banco di lavoro

Base di partenza per gli esercizi del corso di sviluppo web.

## Requisiti

- Node.js 24 (`nvm use 24`)
- pnpm 9 (`corepack enable pnpm`)
- Docker Desktop, per PostgreSQL e Redis

## Avvio

```powershell
cp .env.example .env
pnpm install
pnpm services:up
pnpm dev
```

L'applicazione risponde su http://localhost:5173.

## Comandi

| Comando | Cosa fa |
|---|---|
| `pnpm dev` | Server di sviluppo con ricarica automatica |
| `pnpm build` | Build di produzione in `dist/` |
| `pnpm preview` | Serve la build di produzione in locale |
| `pnpm lint` | Controlla il codice con ESLint |
| `pnpm format` | Formatta tutti i file con Prettier |
| `pnpm check` | lint + verifica formato + build — quello che gira in CI |
| `pnpm services:up` | Avvia PostgreSQL e Redis e attende che siano pronti |
| `pnpm services:reset` | Ricrea i servizi CANCELLANDO i dati |
````

### Passo 10 — Verifica finale

```powershell
git init
git add .
git commit -m "chore: configurazione iniziale del banco di lavoro"

# Il controllo completo
pnpm check
```

```
# Output atteso:
> eslint .

> prettier --check .
Checking formatting...
All matched files use Prettier code style!

> vite build
vite v7.0.0 building for production...
✓ 4 modules transformed.
dist/index.html                 0.51 kB │ gzip: 0.32 kB
dist/assets/index-9nT4wKzE.css  0.89 kB │ gzip: 0.47 kB
dist/assets/index-B3xL2mQp.js   0.72 kB │ gzip: 0.44 kB
✓ built in 241ms
```

**La prova che conta:** clona il repository in un'altra cartella, come farebbe un collega, e verifica che i tre comandi del README bastino.

```powershell
cd C:\progetti
git clone C:\progetti\banco-di-lavoro prova-clone
cd prova-clone
Copy-Item .env.example .env
pnpm install
pnpm dev
```

Se serve un passo non scritto nel README, il README è incompleto. Correggilo adesso, non fra sei mesi quando qualcuno resterà bloccato.

---

# Parte D — Approfondimento per Esperti

---

## D1. Corepack: bloccare il package manager nel repository

Il campo `packageManager` in `package.json` non è documentazione: Corepack — incluso in Node — lo legge e attiva quella versione esatta.

```json
{
  "packageManager": "pnpm@9.15.0+sha512.10dd8f7c14bcf2b0c0e69a7e94f95e13b5f5b1a6cd4c8fb08a54b0f1e6c8e4e2..."
}
```

```powershell
corepack enable
```

Da quel momento, in quel repository:

- `pnpm install` usa la 9.15.0 anche se ne hai installata un'altra globalmente;
- `npm install` fallisce con un messaggio esplicito, invece di generare un secondo lockfile.

L'hash dopo `+sha512.` è opzionale ma consigliato: verifica l'integrità del package manager scaricato. Lo si ottiene con:

```powershell
corepack use pnpm@9.15.0
```

che aggiorna `package.json` con hash e tutto.

> **Il problema che risolve:** un collega su pnpm 8 e uno su pnpm 9 producono lockfile in formati diversi. Ogni pull genera un conflitto sul lockfile e qualcuno finisce per cancellarlo "per sbloccare la situazione", perdendo le versioni verificate.

---

## D2. pnpm workspaces: più pacchetti, un repository

Quando un progetto ha frontend e backend che condividono tipi o utilità, tenerli in due repository significa pubblicare un pacchetto su un registro per ogni modifica condivisa. Un monorepo elimina il passaggio.

```yaml
# pnpm-workspace.yaml — nella radice
packages:
  - 'apps/*'
  - 'packages/*'
```

```
mio-monorepo/
├── pnpm-workspace.yaml
├── package.json              ← solo script e devDependencies condivise
├── apps/
│   ├── web/                  ← il frontend
│   │   └── package.json      → name: "@app/web"
│   └── api/                  ← il backend
│       └── package.json      → name: "@app/api"
└── packages/
    ├── tipi-condivisi/
    │   └── package.json      → name: "@app/tipi"
    └── config-eslint/
        └── package.json      → name: "@app/eslint-config"
```

```json
// apps/web/package.json
{
  "name": "@app/web",
  "dependencies": {
    "@app/tipi": "workspace:*"
  }
}
```

`workspace:*` dice a pnpm di collegare il pacchetto locale invece di cercarlo sul registro. Le modifiche a `packages/tipi-condivisi` sono immediatamente visibili in `apps/web`, senza pubblicare né reinstallare.

```powershell
# Installa per tutto il workspace
pnpm install

# Esegui uno script in un pacchetto specifico
pnpm --filter @app/web dev

# Esegui in tutti i pacchetti che lo definiscono
pnpm -r build

# Aggiungi una dipendenza a un pacchetto specifico
pnpm --filter @app/api add express

# Aggiungi alla radice (per gli strumenti condivisi)
pnpm add -D -w prettier
```

`pnpm -r build` rispetta l'ordine delle dipendenze: costruisce `@app/tipi` prima di `@app/web`, perché il secondo dipende dal primo. Non serve orchestrarlo a mano.

---

## D3. Sicurezza delle dipendenze e supply chain

Un progetto web medio ha centinaia di pacchetti transitivi. Ognuno è codice che gira sulla tua macchina in fase di build e sul tuo server in produzione.

### Audit

```powershell
# Vulnerabilità note nelle dipendenze installate
pnpm audit

# Solo quelle gravi — utile come soglia in CI
pnpm audit --audit-level high
```

```
# Output atteso quando c'è un problema:
┌─────────────────────┬────────────────────────────────────────┐
│ high                │ Prototype Pollution                    │
├─────────────────────┼────────────────────────────────────────┤
│ Package             │ pacchetto-esempio                      │
├─────────────────────┼────────────────────────────────────────┤
│ Vulnerable versions │ <4.17.21                               │
├─────────────────────┼────────────────────────────────────────┤
│ Patched versions    │ >=4.17.21                              │
├─────────────────────┼────────────────────────────────────────┤
│ Paths               │ . > vite > pacchetto-esempio           │
└─────────────────────┴────────────────────────────────────────┘
```

La riga `Paths` è quella che dice cosa fare: se la dipendenza vulnerabile è transitiva (arriva tramite `vite`), non puoi aggiornarla direttamente. Due strade:

```json
// package.json — forzare una versione nell'intero albero
{
  "pnpm": {
    "overrides": {
      "pacchetto-esempio": ">=4.17.21"
    }
  }
}
```

Oppure aggiornare il pacchetto padre, se ha già rilasciato una versione che usa la dipendenza corretta. Gli `overrides` sono una soluzione tampone: annotare perché esistono e rimuoverli quando non servono più evita che diventino un mistero fra un anno.

```json
{
  "pnpm": {
    "overrides": {
      // Rimuovere quando vite >= 7.2 rilascerà la correzione a monte.
      "pacchetto-esempio": ">=4.17.21"
    }
  }
}
```

### Script post-installazione

L'attacco più diretto alla supply chain sfrutta gli script `postinstall`: codice che si esegue automaticamente quando installi un pacchetto, con i tuoi permessi.

```
# .npmrc
# Nessuno script di dipendenza si esegue senza approvazione esplicita.
enable-pre-post-scripts=false
```

pnpm 10 e successivi bloccano gli script di build per impostazione predefinita e chiedono di elencare i pacchetti autorizzati:

```yaml
# pnpm-workspace.yaml
onlyBuiltDependencies:
  - esbuild
  - sharp
```

Solo questi due pacchetti — che hanno bisogno di compilare un binario nativo — possono eseguire script. Tutti gli altri no.

### Verificare prima di aggiungere

```powershell
# Chi lo mantiene, quando è stato pubblicato l'ultima volta, quante dipendenze porta
pnpm info nome-pacchetto

# La dimensione reale, transitive incluse
pnpm dlx package-size nome-pacchetto
```

Le domande da porsi prima di aggiungere una dipendenza per una funzione di venti righe: quante dipendenze porta con sé, quando è stato aggiornato l'ultima volta, quante persone lo mantengono. Il costo di una dipendenza non è il tempo di installazione, è il fatto che entra nella superficie di attacco e che qualcuno dovrà aggiornarla.

---

## D4. Riprodurre lo stesso ambiente su un'altra macchina e in CI

Quattro file dichiarano l'ambiente in modo che una macchina qualunque possa ricostruirlo:

| File | Cosa dichiara | Chi lo legge |
|---|---|---|
| `.nvmrc` | Versione di Node | nvm, `actions/setup-node`, Netlify, Vercel |
| `packageManager` in `package.json` | Versione del package manager | Corepack |
| `engines` in `package.json` | Versioni minime accettate | npm/pnpm all'installazione |
| `pnpm-lock.yaml` | Ogni versione esatta dell'albero | pnpm |

### La pipeline che ne consegue

```yaml
# .github/workflows/verifica.yml
name: Verifica

on:
  push:
    branches: [main]
  pull_request:

jobs:
  controlli:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        # nessuna versione qui: la legge da packageManager in package.json

      - uses: actions/setup-node@v4
        with:
          node-version-file: '.nvmrc'   # nessun numero duplicato nel workflow
          cache: 'pnpm'

      - name: Installa le dipendenze
        run: pnpm install --frozen-lockfile

      - name: Lint
        run: pnpm lint

      - name: Verifica formattazione
        run: pnpm format:check

      - name: Build
        run: pnpm build
```

Il punto di questa configurazione è che **non contiene numeri di versione**. `node-version-file: '.nvmrc'` e `pnpm/action-setup` senza versione leggono i file del repository. Aggiornare la versione di Node è modificare `.nvmrc`, e la pipeline segue. Scrivere `node-version: 24` nel workflow crea un secondo posto da tenere allineato, e i due divergono al primo aggiornamento distratto.

`--frozen-lockfile` fa fallire il job se `package.json` e il lockfile non combaciano — esattamente quello che vuoi che succeda.

### Dev container, quando serve la stessa macchina e non solo lo stesso Node

Se il progetto ha dipendenze di sistema (una libreria nativa, una versione specifica di un client di database), dichiarare Node non basta.

```json
// .devcontainer/devcontainer.json
{
  "name": "Sviluppo web",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:24",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "forwardPorts": [5173, 3000, 5432, 6379],
  "postCreateCommand": "corepack enable && pnpm install",
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "usernamehw.errorlens"
      ]
    }
  }
}
```

VS Code con l'estensione Dev Containers apre il progetto dentro un container che ha già tutto. Il costo è un livello di indirezione in più e prestazioni del filesystem inferiori su Windows; il beneficio è che "sulla mia macchina funziona" smette di essere una frase possibile.

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
AMBIENTE DI SVILUPPO WEB — Mappa dei concetti

RUNTIME
├── Node.js — motore V8 fuori dal browser
│   ├── Serve al backend, agli strumenti di build e ai linter
│   └── LTS (pari) per lavorare, Current (dispari) per provare
├── nvm — più versioni installate, una attiva
│   ├── nvm install lts / nvm use <versione>
│   └── Modifica un symlink, non il PATH
└── PATH — elenco ordinato di cartelle; vince la prima corrispondenza
    └── Letto all'avvio della sessione: dopo un'installazione, riapri il terminale

PACCHETTI
├── package.json — il contratto: cosa serve, come si avvia
│   ├── dependencies      → serve all'applicazione in esecuzione
│   ├── devDependencies   → serve solo a costruire e controllare
│   ├── scripts           → i comandi del progetto
│   ├── packageManager    → letto da Corepack, blocca il gestore
│   └── engines           → versioni minime, fallisce presto e chiaro
├── lockfile — le versioni esatte + hash di integrità
│   ├── Va sempre in Git
│   └── pnpm install --frozen-lockfile in CI
├── semver — MAJOR.MINOR.PATCH
│   ├── ^1.2.3 → 1.x.x     ~1.2.3 → 1.2.x     ^0.5.2 → 0.5.x
└── node_modules — mai in Git, mai in OneDrive, ricostruibile

QUALITÀ
├── ESLint — è corretto?      (regole discutibili, scelte di progetto)
├── Prettier — è uniforme?    (non si discute, ed è il punto)
└── eslint-config-prettier ultimo nella catena, disattiva le sovrapposizioni

BROWSER
└── DevTools
    ├── Elements     com'è fatta la pagina adesso
    ├── Console      cosa dice il codice
    ├── Sources      perché fa questo (breakpoint)
    ├── Network      cosa ha chiesto e ricevuto
    ├── Performance  perché è lento
    └── Application  cosa è salvato (cookie, storage, service worker)

VERSIONING
├── Git — commit, branch, remote
└── .gitattributes con eol=lf — elimina i diff fantasma su team misti

SERVIZI
└── Docker Compose
    ├── volumes    → i dati sopravvivono a docker compose down
    ├── healthcheck → "pronto" ≠ "processo avviato"
    └── down -v    → CANCELLA i dati

CONFIGURAZIONE
├── .env          mai in Git
├── .env.example  sempre in Git, dice quali variabili servono
└── VITE_ / NEXT_PUBLIC_ = dichiarazione che il valore sarà PUBBLICO
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Sai descrivere cosa succede fra la pressione di Invio e la pagina visibile
- [ ] Ti muovi in PowerShell fra cartelle, crei file e fermi un processo con `Ctrl+C`
- [ ] Sai spiegare perché serve Node anche per un sito puramente statico
- [ ] Installi e cambi versione di Node con nvm, e sai che `install` non implica `use`
- [ ] Distingui `dependencies` da `devDependencies` e sai motivare ogni collocazione
- [ ] Sai perché `npm run` è preferibile a chiamare direttamente il binario
- [ ] Hai configurato VS Code con format-on-save e le estensioni essenziali
- [ ] Crei un progetto Vite, lo avvii in sviluppo e ne produci la build

**Parte B — Comprensione**

- [ ] Sai leggere il PATH e diagnosticare un "comando non riconosciuto"
- [ ] Sai spiegare come nvm cambia versione senza toccare il PATH
- [ ] Sai perché il lockfile va in Git e `node_modules` no
- [ ] Sai leggere `^`, `~` e il comportamento particolare di `^0.x.y`
- [ ] Sai perché ESLint e Prettier non si sovrappongono, e come impedirglielo
- [ ] Apri Network in DevTools e leggi status, header e payload di una richiesta
- [ ] Sai cosa fa `.gitattributes` con `eol=lf` e quale problema elimina
- [ ] Avvii i servizi con Docker Compose e sai distinguere `stop`, `down` e `down -v`
- [ ] Sai perché il prefisso `VITE_` è una dichiarazione di pubblicità del valore

**Parte C — Pratica**

- [ ] Hai costruito il banco di lavoro e `pnpm check` passa
- [ ] Hai clonato il tuo repository e verificato che il README basti ad avviarlo
- [ ] Hai dimostrato a te stesso che un segreto con prefisso `VITE_` finisce nel bundle

**Parte D — Esperto**

- [ ] Sai a cosa serve `packageManager` e cosa succede a chi lancia il gestore sbagliato
- [ ] Sai impostare un workspace pnpm e cosa significa `workspace:*`
- [ ] Sai leggere l'output di `pnpm audit` e distinguere una vulnerabilità diretta da una transitiva
- [ ] Sai perché gli script `postinstall` sono un rischio e come si limitano
- [ ] Sai scrivere una pipeline CI che non contiene numeri di versione duplicati

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Installare Node dall'installer ufficiale | Una sola versione, cambiarla richiede di disinstallare | nvm-windows, `nvm install lts` |
| `node_modules` in Git | Centinaia di MB, binari specifici per sistema operativo, conflitti irrisolvibili | `.gitignore`, e committare il lockfile |
| Lockfile in `.gitignore` | Ogni macchina installa versioni diverse, i bug non si riproducono | Committare `pnpm-lock.yaml` |
| npm e pnpm nello stesso progetto | Due lockfile in conflitto, installazioni divergenti | Un solo gestore, dichiarato in `packageManager` |
| Progetti in una cartella OneDrive | `node_modules` sincronizzato: lentezza e installazioni corrotte | Cartella fuori dalla sincronizzazione, es. `C:\progetti` |
| Segreti con prefisso `VITE_` | Finiscono nel bundle scaricato dal browser, pubblici per chiunque | Prefisso solo per valori pubblici; i segreti restano sul server |
| `.env` committato | Credenziali nella storia di Git, recuperabili anche dopo la rimozione | `.gitignore` + `.env.example`, e **ruotare** il segreto esposto |
| `pnpm install` in CI | Può risolvere versioni diverse da quelle verificate | `pnpm install --frozen-lockfile` |
| Numero di versione di Node duplicato nel workflow | Diverge da `.nvmrc` al primo aggiornamento | `node-version-file: '.nvmrc'` |
| `Start-Sleep` per aspettare un servizio | O troppo corto (fallimenti intermittenti) o troppo lungo (tempo sprecato) | `healthcheck` + `docker compose up --wait` |
| Installare pacchetti globalmente | Legati alla versione di Node attiva, spariscono con `nvm use` | Dipendenze nel progetto, `pnpm dlx` per l'uso occasionale |
| Considerare finito ciò che gira solo con `dev` | La build applica minificazione e tree shaking: rompe cose che dev tollera | `pnpm build && pnpm preview` prima di dichiarare fatto |

---

## Troubleshooting rapido

**`node : Termine 'node' non riconosciuto come nome di cmdlet`**
- Causa: Node non installato, oppure PATH non ancora ricaricato nella sessione corrente
- Fix: chiudi e riapri PowerShell. Se persiste: `nvm list`, poi `nvm use <versione>`

**`nvm use` risponde `exit status 5: Accesso negato`**
- Causa: `nvm use` modifica un symlink in `C:\Program Files`, che richiede privilegi elevati
- Fix: riapri PowerShell come amministratore ed esegui di nuovo `nvm use`

**`pnpm : Impossibile caricare il file ... perché l'esecuzione di script è disabilitata`**
- Causa: la Execution Policy di PowerShell blocca gli script `.ps1`
- Fix: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

**`ERR_PNPM_OUTDATED_LOCKFILE`**
- Causa: `package.json` è stato modificato senza rigenerare il lockfile
- Fix: in locale `pnpm install` e committa il lockfile aggiornato. In CI **non** rimuovere `--frozen-lockfile`: l'errore sta segnalando esattamente il problema che deve segnalare

**`EADDRINUSE: address already in use :::5173`**
- Causa: un'istanza precedente del server di sviluppo è ancora viva
- Fix: `Get-NetTCPConnection -LocalPort 5173 | Select-Object OwningProcess`, poi `Stop-Process -Id <pid>`. Oppure cambia porta: `pnpm dev --port 5174`

**Le modifiche al codice non appaiono nel browser**
- Causa (in ordine di probabilità): cache del browser; un service worker registrato da un progetto precedente sulla stessa porta; il file modificato non è quello incluso nel bundle
- Fix: DevTools → Network → `Disable cache`; DevTools → Application → Service Workers → `Unregister`; `Ctrl+Shift+R` per ricaricare ignorando la cache

**`docker: error during connect ... the system cannot find the file specified`**
- Causa: Docker Desktop non è in esecuzione
- Fix: avvia Docker Desktop e attendi che l'icona indichi lo stato "running"

**`ECONNREFUSED 127.0.0.1:5432`**
- Causa: il container PostgreSQL non è partito, oppure è partito ma non è ancora pronto ad accettare connessioni
- Fix: `docker compose ps` per lo stato, `docker compose logs postgres` per il motivo. Usa `docker compose up --wait` con un `healthcheck` definito

**Git segnala l'intero file come modificato dopo un cambiamento di una riga**
- Causa: fine riga normalizzati diversamente fra le macchine
- Fix: aggiungi `.gitattributes` con `* text=auto eol=lf`, poi `git add --renormalize .` e committa la normalizzazione in un commit dedicato

**`import.meta.env.MIA_VARIABILE` è `undefined` nel browser**
- Causa: manca il prefisso `VITE_`, oppure il server di sviluppo non è stato riavviato dopo la modifica di `.env`
- Fix: rinomina in `VITE_MIA_VARIABILE` **solo se il valore può essere pubblico**, e riavvia `pnpm dev`

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_01_html5.md` | Il primo linguaggio da scrivere nel progetto Vite appena creato |
| `tutorial_04_javascript_fondamenti.md` | Il linguaggio che gira sia nel browser sia su Node |
| `tutorial_10_nodejs.md` | Il runtime installato qui, usato per costruire un backend |
| `tutorial_12_database_web.md` | Il PostgreSQL avviato con Docker Compose, popolato e interrogato |
| `tutorial_14_sicurezza_web.md` | Trattamento sistematico dei segreti e delle dipendenze |
| `tutorial_16_build_tools_deploy.md` | Vite in profondità, Docker per la produzione, pipeline complete |

---

## Risorse di riferimento

**Documentazione ufficiale:**
- [Node.js — Previous Releases](https://nodejs.org/en/about/previous-releases) — calendario LTS e date di fine supporto
- [pnpm](https://pnpm.io/motivation) — motivazione, comandi, workspaces
- [Vite](https://vite.dev/guide/) — guida, configurazione, variabili d'ambiente
- [ESLint — Configuration Files](https://eslint.org/docs/latest/use/configure/configuration-files) — il formato flat config
- [Prettier — Options](https://prettier.io/docs/en/options) — ogni opzione e il suo default
- [Docker Compose — Specification](https://docs.docker.com/reference/compose-file/) — riferimento completo del file
- [Chrome DevTools](https://developer.chrome.com/docs/devtools) — documentazione pannello per pannello

**Specifiche e convenzioni:**
- [Semantic Versioning 2.0.0](https://semver.org/lang/it/) — la specifica, in italiano
- [gitattributes](https://git-scm.com/docs/gitattributes) — normalizzazione dei fine riga
- [Conventional Commits](https://www.conventionalcommits.org/it/v1.0.0/) — convenzione dei messaggi di commit

**Strumenti:**
- [nvm-windows](https://github.com/coreybutler/nvm-windows) — release e problemi noti
- [Corepack](https://nodejs.org/api/corepack.html) — gestione del package manager

---

> **Fine del Tutorial 00 — Ambiente di Sviluppo Web su Windows**
>
> Prossimo tutorial: `tutorial_01_html5.md`
