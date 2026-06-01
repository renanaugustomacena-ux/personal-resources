# Sviluppo Web — Panoramica e Piano di Studio

Guida completa allo studio dello sviluppo web full-stack, dal markup semantico alla messa
in produzione. Questo documento fornisce la struttura organizzativa, il piano di studio
progressivo, gli strumenti di laboratorio e il glossario di riferimento per l'intero modulo
dedicato al web development.

---

## Indice

1. [Panoramica del Campo](#panoramica-del-campo)
2. [Piano di Studio](#piano-di-studio)
   - [Fase 1: Fondamenti Frontend (settimane 1-3)](#fase-1-fondamenti-frontend-settimane-1-3)
   - [Fase 2: JavaScript e TypeScript (settimane 4-7)](#fase-2-javascript-e-typescript-settimane-4-7)
   - [Fase 3: Framework Frontend (settimane 8-11)](#fase-3-framework-frontend-settimane-8-11)
   - [Fase 4: Backend e Database (settimane 12-15)](#fase-4-backend-e-database-settimane-12-15)
   - [Fase 5: Produzione (settimane 16-19)](#fase-5-produzione-settimane-16-19)
3. [Ambiente di Laboratorio](#ambiente-di-laboratorio)
4. [Glossario](#glossario)
5. [Certificazioni Rilevanti](#certificazioni-rilevanti)
6. [Risorse Consigliate](#risorse-consigliate)

---

## Panoramica del Campo

Lo sviluppo web moderno rappresenta una delle discipline informatiche piu dinamiche e in
continua evoluzione. Da pagine statiche servite da un singolo server LAMP si e passati ad
architetture distribuite, rendering ibrido, edge computing e applicazioni progressive che
rivaleggiano con il software nativo. Per un professionista IT che opera in contesti
aziendali — costruendo strumenti interni, dashboard e applicazioni web a supporto dei
processi — la padronanza dello stack web costituisce una competenza fondamentale.

### Il Panorama Full-Stack

Il concetto di "full-stack" abbraccia l'intero spettro tecnologico necessario per portare
un'applicazione web dall'idea alla produzione:

- Progettare e implementare interfacce utente reattive e accessibili.
- Costruire API robuste che espongano logica di business e dati.
- Gestire la persistenza dei dati attraverso database relazionali e non relazionali.
- Configurare pipeline di build, test e deploy automatizzati.
- Garantire sicurezza, performance e affidabilita in ambiente di produzione.

Non si tratta di essere esperti al massimo livello in ogni area, ma di possedere una
comprensione operativa sufficiente a fare scelte architetturali informate e collaborare
efficacemente con specialisti di ciascun dominio.

### Frontend, Backend e Full-Stack

**Frontend** — Tutto cio che l'utente vede e con cui interagisce nel browser: struttura del
documento (HTML), presentazione visiva (CSS) e comportamento interattivo (JavaScript). I
framework moderni come React, Vue e Svelte gestiscono stato, routing e rendering in modo
dichiarativo. Il frontend e responsabile di velocita percepita, accessibilita, responsivita
e coerenza visiva.

**Backend** — La logica che opera sul server. Riceve richieste HTTP, applica regole di
business, interagisce con database e servizi esterni, e restituisce risposte strutturate.
Node.js, Python (Django/Flask), Go e Rust dominano questo spazio. Responsabile di
autenticazione, autorizzazione, validazione dei dati e integrazione con sistemi terzi.

**Full-Stack** — La capacita di operare su entrambi i lati con una visione unificata.
Particolarmente prezioso in contesti aziendali dove i team sono ridotti e la stessa persona
puo modificare un componente React al mattino e un endpoint Express al pomeriggio.

### Flusso di Lavoro Moderno

Il ciclo di sviluppo web contemporaneo si articola in fasi supportate da strumenti
sofisticati:

1. **Progettazione** — Wireframe, prototipi interattivi, design system con strumenti come Figma.
2. **Sviluppo locale** — Hot module replacement, linting automatico, type checking in tempo reale.
3. **Versionamento** — Git, branch strategy, code review tramite pull request.
4. **Testing** — Unit test, integration test, end-to-end test automatizzati.
5. **CI/CD** — Pipeline automatizzate con GitHub Actions o GitLab CI.
6. **Monitoraggio** — Logging strutturato, metriche di performance, error tracking.

### Profilo Target

Questo percorso e progettato per un professionista IT che costruisce:

- **Strumenti interni** — Pannelli di amministrazione, CRM personalizzati, sistemi di ticketing.
- **Dashboard** — Visualizzazione dati in tempo reale, report interattivi, KPI monitoring.
- **Applicazioni web** — Portali clienti, gestione documentale, piattaforme di collaborazione.
- **Automazioni con interfaccia** — Frontend per script automatizzati che necessitano di input
  umano o monitoraggio visivo.

La scelta tecnologica riflette questo obiettivo: React per la sua adozione enterprise, Node.js
per la coerenza linguistica tra frontend e backend, TypeScript per la robustezza del codice.

---

## Piano di Studio

Il percorso e strutturato in cinque fasi progressive che coprono 19 settimane. I riferimenti
tra parentesi quadre indicano i file di studio specifici.

### Fase 1: Fondamenti Frontend (settimane 1-3)

La prima fase getta le fondamenta su cui poggia tutto il resto. HTML e CSS non sono tecnologie
banali: la padronanza del markup semantico e del layout moderno richiede studio deliberato.

#### Settimana 1-2: HTML5 Semantico e Accessibile `[01-html5.md]`

- Struttura del documento e DOCTYPE moderno.
- Elementi semantici: `<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<aside>`,
  `<footer>` e il loro impatto su accessibilita e SEO.
- Formulari avanzati: tipi di input HTML5, validazione nativa, attributi di accessibilita.
- Elementi multimediali: `<video>`, `<audio>`, `<picture>` e caricamento responsivo.
- Attributi ARIA e principi di accessibilita WCAG 2.1.
- Meta tag, Open Graph e struttura per la condivisione social.

**Esercizio chiave**: Costruire un portale informativo aziendale con navigazione, formulari
e contenuti multimediali, utilizzando esclusivamente HTML semantico.

#### Settimana 2: CSS3 Moderno `[02-css3.md]`

- Il modello a cascata, specificita e ereditarieta.
- Box model, margin collapsing e comportamenti controintuitivi.
- Flexbox: asse principale, asse trasversale, distribuzione dello spazio.
- CSS Grid: template, aree nominate, auto-placement, grid implicita.
- Custom Properties (variabili CSS) e theming dinamico.
- Transizioni e animazioni con `@keyframes`.
- Media queries, container queries e responsive design mobile-first.

**Esercizio chiave**: Replicare il layout di una dashboard aziendale con sidebar, header,
griglia di card e footer, completamente responsiva.

#### Settimana 3: CSS Framework `[03-css-framework.md]`

- Tailwind CSS: filosofia utility-first, configurazione, personalizzazione, plugin.
- Bootstrap: sistema a griglia, componenti predefiniti, personalizzazione via Sass.
- Confronto tra approcci utility-first e component-based.
- CSS-in-JS: cenni su Styled Components e Emotion.
- Design system: token di design, coerenza visiva, documentazione dei componenti.

**Esercizio chiave**: Ricostruire la dashboard con Tailwind CSS, confrontando produttivita
e manutenibilita con il CSS puro.

---

### Fase 2: JavaScript e TypeScript (settimane 4-7)

JavaScript e il linguaggio che da vita alle interfacce web e, con Node.js, alimenta anche il
backend. TypeScript aggiunge tipizzazione statica per maggiore manutenibilita.

#### Settimane 4-5: JavaScript Fondamenti `[04-javascript-fondamenti.md]`

- Tipi primitivi e oggetti, coercizione di tipo, uguaglianza stretta vs debole.
- Variabili: `var`, `let`, `const`, hoisting, temporal dead zone, scope lessicale.
- Funzioni: dichiarazioni, espressioni, arrow function, closure, IIFE.
- Oggetti e prototipi: catena prototipale, classi ES6+.
- Array e metodi funzionali: `map()`, `filter()`, `reduce()`, `find()`, `some()`, `every()`.
- Destructuring, spread/rest, template literal, optional chaining, nullish coalescing.
- Gestione degli errori: `try/catch/finally`, errori personalizzati.
- Manipolazione del DOM: selezione, creazione, modifica, rimozione di elementi.
- Eventi: bubbling, capturing, delegation, preventDefault, custom events.

**Esercizio chiave**: Costruire un'applicazione todo-list con filtri, persistenza in
localStorage e drag-and-drop — tutto in JavaScript vanilla.

#### Settimane 6-7: JavaScript Avanzato `[05-javascript-avanzato.md]`

- Programmazione asincrona: callback, Promise, async/await, gestione errori asincroni.
- Event loop: call stack, task queue, microtask queue, rendering pipeline.
- Moduli ES6: `import`/`export`, dynamic import, tree shaking.
- Iteratori e generatori: protocollo iterabile, `function*`, `yield`.
- Proxy e Reflect: intercettazione delle operazioni, metaprogrammazione.
- Web API avanzate: Fetch, AbortController, IntersectionObserver, Web Workers, WebSocket.
- Pattern di design: Module, Observer, Pub/Sub, Factory, Singleton, Strategy.
- Gestione della memoria: garbage collection, memory leak comuni, profiling.

**Esercizio chiave**: Implementare un client di chat in tempo reale con WebSocket e pattern
Observer.

#### Settimana 7: TypeScript `[06-typescript.md]`

- Sistema di tipi: primitivi, union, intersection, literal types.
- Interfacce e type alias: differenze e casi d'uso.
- Generics: funzioni generiche, classi generiche, constraint, utility types.
- Type narrowing e type guards: `typeof`, `instanceof`, discriminated unions.
- Configurazione di `tsconfig.json`: strict mode, target, module resolution.
- Tipi per il DOM e librerie esterne: DefinitelyTyped, declaration files.
- Pattern avanzati: mapped types, conditional types, template literal types, `infer`.

**Esercizio chiave**: Convertire la todo-list da JavaScript puro a TypeScript con interfacce
rigorose e generics.

---

### Fase 3: Framework Frontend (settimane 8-11)

I framework frontend astraggono la complessita della manipolazione del DOM e forniscono
pattern strutturati per interfacce complesse e manutenibili.

#### Settimane 8-10: React `[07-react.md]`

- Filosofia component-based e rendering dichiarativo.
- JSX: sintassi, espressioni, rendering condizionale, liste e chiavi.
- Hook fondamentali: `useState`, `useEffect`, `useContext`, `useRef`, `useMemo`, `useCallback`.
- Gestione dello stato: stato locale, Context API, Zustand, Redux Toolkit.
- React Router: routing dichiarativo, parametri dinamici, nested routes.
- Formulari: controlled components, React Hook Form, Zod.
- Data fetching: TanStack Query per caching e sincronizzazione.
- Styling: CSS Modules, Tailwind con React, Styled Components.
- Performance: React.memo, lazy loading con `Suspense`, code splitting.
- Testing: React Testing Library, test di componenti e integrazione.
- Next.js: cenni su SSR, static generation e API routes.

**Esercizio chiave**: Costruire una dashboard aziendale completa con autenticazione simulata,
grafici, tabelle con ordinamento/filtri e routing multipage.

#### Settimana 11: Vue e Svelte (panoramica) `[08-vue.md]` `[09-svelte.md]`

**Vue.js** — Framework progressivo con curva di apprendimento dolce. La Composition API
(Vue 3) si avvicina concettualmente ai React Hooks. Eccelle in progetti dove si vuole
adottare un framework gradualmente.

**Svelte** — Compilatore piuttosto che framework runtime. Genera codice JavaScript imperativo
durante la build, eliminando il virtual DOM e producendo bundle leggeri. Ideale dove la
dimensione del bundle e la performance sono critiche.

Lo studio si concentra sulle differenze architetturali, non sulla padronanza completa.

---

### Fase 4: Backend e Database (settimane 12-15)

Il backend completa il quadro full-stack con logica server-side, accesso ai dati e
meccanismi di sicurezza.

#### Settimana 12: Node.js `[10-nodejs.md]`

- Runtime V8, event loop di Node.js, modello non-bloccante.
- Moduli core: `fs`, `path`, `http`, `crypto`, `stream`.
- npm e gestione delle dipendenze: `package.json`, versionamento semantico, lockfile.
- Express.js: routing, middleware, gestione errori, struttura del progetto.
- Fastify come alternativa: performance, schema validation, plugin system.
- Stream e buffer per operazioni I/O intensive.
- Worker threads per operazioni CPU-intensive.
- Variabili d'ambiente e configurazione multi-ambiente.

**Esercizio chiave**: Costruire un server Express modulare con middleware personalizzati e
gestione centralizzata degli errori.

#### Settimana 13: API Design `[11-api-design.md]`

- REST: principi, verbi HTTP, codici di stato, naming convention, HATEOAS.
- Versionamento delle API: strategie (URL, header, query parameter).
- Paginazione: cursor-based vs offset-based.
- GraphQL: schema, query, mutation, subscription, confronto con REST.
- Documentazione API: OpenAPI/Swagger, generazione automatica.
- Rate limiting e throttling.
- Gestione degli errori: formato consistente, codici applicativi.

**Esercizio chiave**: Progettare e implementare un'API RESTful per un sistema di gestione
progetti con documentazione OpenAPI.

#### Settimana 14: Database `[12-database-web.md]`

- SQL e PostgreSQL: DDL, DML, join, subquery, indici, transazioni, ACID.
- ORM: Prisma per TypeScript — schema definition, migration, query builder.
- NoSQL e MongoDB: documenti, collezioni, query, aggregation pipeline.
- Redis: caching, session store, pub/sub.
- Pattern di accesso ai dati: repository pattern, unit of work.
- Migration: versionamento schema, rollback, seed data.
- Ottimizzazione: query plan, indici composti, N+1 problem, connection pooling.

**Esercizio chiave**: Schema di database per un sistema e-commerce con Prisma, migration,
seed data e query ottimizzate.

#### Settimana 15: Autenticazione e Autorizzazione `[13-autenticazione-autorizzazione.md]`

- Autenticazione: concetti fondamentali, fattori di autenticazione, MFA.
- Password: hashing con bcrypt/argon2, policy di sicurezza, gestione reset.
- JWT: struttura, firma, refresh token, token rotation.
- Session-based authentication: cookie, session store, confronto con JWT.
- OAuth 2.0 e OpenID Connect: flussi di autorizzazione, provider esterni.
- RBAC: ruoli, permessi, middleware di autorizzazione.
- Passport.js e NextAuth.js: integrazione con provider di autenticazione.

**Esercizio chiave**: Sistema di autenticazione completo con registrazione, login, refresh
token, ruoli utente e protezione delle route frontend e backend.

---

### Fase 5: Produzione (settimane 16-19)

L'ultima fase copre tutto cio che serve per portare un'applicazione in produzione con
fiducia e affidabilita.

#### Settimana 16: Sicurezza Web `[14-sicurezza-web.md]`

- OWASP Top 10: vulnerabilita comuni e mitigazioni.
- XSS: reflected, stored, DOM-based; sanitizzazione e CSP.
- CSRF: token anti-CSRF, SameSite cookie.
- SQL Injection e NoSQL Injection: prepared statement, validazione input.
- CSP: direttive, nonce, hash, report-uri.
- HTTPS e TLS: certificati, HSTS, certificate pinning.
- Header di sicurezza: X-Content-Type-Options, X-Frame-Options, Referrer-Policy.
- Dependency security: audit automatico, Dependabot, supply chain attack.

**Esercizio chiave**: Audit di sicurezza su un'applicazione esistente con implementazione
delle contromisure.

#### Settimana 17: Testing `[15-testing-web.md]`

- Piramide dei test: unit, integration, e2e e rapporto costo/beneficio.
- Unit testing con Vitest: assertion, mock, stub, spy, coverage.
- Testing componenti React con Testing Library: query, user event, async testing.
- Integration testing: test API con Supertest, test database con container.
- End-to-end con Playwright: navigazione, interazione, visual regression.
- Test-Driven Development (TDD): red-green-refactor.
- CI integration: test nella pipeline, parallelizzazione, flaky test.

**Esercizio chiave**: Suite di test completa per la dashboard: unit, componenti e e2e.

#### Settimana 18: Build Tools e Deploy `[16-build-tools-e-deploy.md]`

- Bundler moderni: Vite come standard, confronto con Webpack e esbuild.
- Configurazione Vite: plugin, alias, variabili d'ambiente, build.
- Docker: Dockerfile multi-stage, docker-compose per sviluppo locale.
- CI/CD con GitHub Actions: workflow di build, test, deploy automatico.
- Piattaforme di hosting: Vercel, Netlify, Railway, AWS (S3 + CloudFront, ECS).
- Strategie di deploy: blue-green, canary, rolling update.
- Monitoraggio post-deploy: health check, logging, alerting.

**Esercizio chiave**: Pipeline CI/CD completa con lint, type check, test, build e deploy
automatico su ogni push.

#### Settimana 18-19: Performance Web `[17-performance-web.md]`

- Core Web Vitals: LCP, FID/INP, CLS — misurazione e ottimizzazione.
- Lighthouse e Chrome DevTools Performance: profiling e colli di bottiglia.
- Ottimizzazione immagini: WebP, AVIF, lazy loading, responsive images.
- Code splitting e lazy loading dei moduli.
- Caching: HTTP caching, service worker caching, CDN strategies.
- Rendering optimization: virtual scrolling, debounce/throttle, requestAnimationFrame.
- Bundle analysis: dipendenze pesanti, tree shaking efficace.

**Esercizio chiave**: Portare un'applicazione da score Lighthouse 60 a 90+ con interventi
mirati.

#### Settimana 19: PWA e Tecnologie Avanzate `[18-pwa-e-tecnologie-avanzate.md]`

- Manifest file: configurazione, icone, splash screen, display mode.
- Service Worker: ciclo di vita, strategie di caching (cache-first, network-first,
  stale-while-revalidate).
- API avanzate: Background Sync, Push Notification, File System Access, Web Share.
- Web Component: Custom Elements, Shadow DOM, HTML Templates.
- WebAssembly: cenni su performance near-native nel browser.
- Micro-frontend: architettura, Module Federation, integrazione di applicazioni indipendenti.

**Esercizio chiave**: Trasformare la dashboard in una PWA installabile con supporto offline
e caching intelligente.

#### Riferimento Trasversale: Troubleshooting `[19-troubleshooting-e-guide-pratiche.md]`

Il file di troubleshooting e un riferimento costante durante tutto il percorso. Contiene
guide pratiche per la risoluzione dei problemi piu comuni, pattern di debug, checklist
operative e soluzioni a scenari ricorrenti.

---

## Ambiente di Laboratorio

Un ambiente di sviluppo ben configurato e il prerequisito per uno studio produttivo.

### Runtime e Package Manager

- **Node.js LTS** — Utilizzare `nvm` (Node Version Manager) per gestire versioni multiple.
  La versione Long Term Support garantisce stabilita e compatibilita con l'ecosistema.
- **npm** — Package manager predefinito di Node.js. Comprendere `package.json`,
  `package-lock.json` e i comandi fondamentali: `install`, `run`, `audit`.
- **pnpm** — Alternativa performante che utilizza un content-addressable store per risparmiare
  spazio disco. Vantaggioso in monorepo e progetti con dipendenze condivise.

### Editor e Estensioni

- **Visual Studio Code** — Editor di riferimento per lo sviluppo web con ecosistema di
  estensioni completo.
- **ESLint** — Linting statico per JavaScript e TypeScript. Identifica errori e pattern
  problematici prima dell'esecuzione.
- **Prettier** — Formattazione automatica del codice con regole configurabili.
- **Tailwind CSS IntelliSense** — Autocompletamento classi Tailwind, preview colori, hover
  per il CSS generato.
- **TypeScript** — Supporto nativo in VS Code con intellisense e type checking in tempo reale.
- **Estensioni aggiuntive** — Error Lens, GitLens, Thunder Client, Auto Rename Tag, Path
  Intellisense.

### Browser DevTools

- **Chrome DevTools** — Pannelli Elements, Console, Network, Performance, Application e
  Sources. Padroneggiare il debugging con breakpoint, la Network tab e il Performance profiler.
- **Firefox Developer Edition** — CSS Grid Inspector, Flexbox Inspector. Utile per testing
  cross-browser.

### Controllo Versione

- **Git** — Oltre ai comandi base, padroneggiare branching, merging, rebasing, stashing e
  risoluzione conflitti. Configurare alias per i comandi frequenti.

### Containerizzazione

- **Docker** — Essenziale per servizi locali riproducibili. Un `docker-compose.yml` avvia
  PostgreSQL, Redis, MongoDB con un singolo comando senza inquinare il sistema host.

### Test delle API

- **Postman** — Client HTTP con interfaccia grafica per progettare, testare e documentare API.
  Supporta collezioni, variabili d'ambiente e test automatici.
- **Thunder Client** — Estensione VS Code con funzionalita simili a Postman direttamente
  nell'editor.

---

## Glossario

Terminologia essenziale dello sviluppo web moderno, organizzata per area tematica.

### Browser e Rendering

- **DOM (Document Object Model)** — Rappresentazione ad albero del documento HTML nel browser.
  JavaScript manipola il DOM per aggiornare dinamicamente la pagina.
- **Virtual DOM** — Rappresentazione in-memory del DOM reale usata da React per calcolare le
  differenze e applicare solo gli aggiornamenti necessari.
- **SPA (Single Page Application)** — Applicazione che carica una singola pagina HTML e
  aggiorna il contenuto dinamicamente senza ricaricare la pagina.
- **MPA (Multi Page Application)** — Architettura tradizionale dove ogni navigazione carica
  una nuova pagina HTML dal server.
- **SSR (Server-Side Rendering)** — Il server genera HTML completo per ogni richiesta.
  Migliora FCP e SEO. Next.js supporta SSR nativamente.
- **SSG (Static Site Generation)** — Pagine HTML generate durante la build. Performance
  eccellente perche servite direttamente da CDN.
- **ISR (Incremental Static Regeneration)** — Pagine statiche che possono essere rigenerate
  incrementalmente dopo un intervallo configurabile.
- **CSR (Client-Side Rendering)** — Il rendering avviene interamente nel browser. Tipico
  delle SPA tradizionali.
- **Hydration** — Processo che attiva l'HTML generato dal server collegando event listener e
  stato ai componenti gia renderizzati.

### Build e Tooling

- **Bundler** — Strumento che combina moduli JavaScript, CSS e risorse in file ottimizzati.
  Vite e Webpack sono i piu diffusi.
- **Transpiler** — Converte codice da una versione del linguaggio a un'altra (TypeScript a
  JavaScript, JSX a JavaScript).
- **Minification** — Riduzione della dimensione del codice rimuovendo spazi e commenti senza
  alterare il comportamento.
- **Tree Shaking** — Eliminazione del codice non utilizzato durante la build analizzando le
  dichiarazioni import/export ES6.
- **Hot Module Replacement (HMR)** — Aggiornamento dei moduli nel browser in tempo reale
  durante lo sviluppo, preservando lo stato dell'applicazione.

### Rete e Comunicazione

- **CORS (Cross-Origin Resource Sharing)** — Meccanismo HTTP che consente a un server di
  indicare quali origini diverse possono accedere alle sue risorse.
- **REST (Representational State Transfer)** — Stile architetturale per API basato su risorse,
  verbi HTTP e rappresentazioni stateless.
- **GraphQL** — Linguaggio di query per API che permette al client di richiedere esattamente
  i dati necessari.
- **WebSocket** — Protocollo di comunicazione full-duplex su TCP per comunicazione bidirezionale
  in tempo reale.
- **API Gateway** — Punto di ingresso unico per richieste API che gestisce routing,
  autenticazione e rate limiting.
- **Rate Limiting** — Meccanismo che limita il numero di richieste per intervallo di tempo,
  proteggendo da abusi.

### Sicurezza

- **JWT (JSON Web Token)** — Standard per trasmissione sicura di informazioni come oggetto
  JSON firmato digitalmente.
- **OAuth** — Framework di autorizzazione per accesso limitato a risorse su servizi terzi
  senza esporre credenziali.
- **XSS (Cross-Site Scripting)** — Vulnerabilita che permette iniezione di script malevoli in
  pagine web. Mitigata con sanitizzazione e CSP.
- **CSRF (Cross-Site Request Forgery)** — Attacco che induce un utente autenticato a eseguire
  azioni non intenzionali. Mitigato con token anti-CSRF e SameSite cookie.
- **CSP (Content Security Policy)** — Header HTTP che controlla quali risorse il browser puo
  caricare, riducendo il rischio di XSS.
- **CDN (Content Delivery Network)** — Rete di server distribuiti che servono contenuti
  statici dall'edge piu vicina all'utente.

### Applicazioni Avanzate

- **PWA (Progressive Web App)** — Applicazione web installabile, funzionante offline, con
  notifiche push e accesso a funzionalita del dispositivo.
- **Service Worker** — Script eseguito in background che intercetta richieste di rete per
  caching offline, notifiche push e sincronizzazione.
- **Web Component** — API native del browser (Custom Elements, Shadow DOM, HTML Templates) per
  componenti riutilizzabili senza dipendenza da framework.

### Layout e Design

- **Responsive Design** — Progettazione che garantisce adattamento corretto a schermi di
  dimensioni diverse.
- **Mobile First** — Strategia che parte dall'esperienza mobile e aggiunge progressivamente
  funzionalita per schermi piu grandi.
- **Viewport** — Area visibile della pagina nel browser. Il meta tag viewport controlla
  dimensionamento e scala sui dispositivi mobili.
- **Breakpoint** — Punto di larghezza dello schermo al quale il layout cambia. Definiti
  con media query CSS.
- **Flexbox** — Modello di layout CSS unidimensionale per distribuzione dello spazio lungo un
  asse principale.
- **Grid** — Modello di layout CSS bidimensionale che organizza elementi in righe e colonne
  simultaneamente.

### Backend e Dati

- **Middleware** — Funzione nel ciclo richiesta-risposta che esegue logica prima del gestore
  finale: logging, autenticazione, validazione, compressione.
- **ORM (Object-Relational Mapping)** — Libreria che mappa oggetti del linguaggio a tabelle
  del database, permettendo interazione senza SQL diretto.
- **Migration** — Script versionato che modifica lo schema del database in modo controllato e
  riproducibile.
- **Schema** — Definizione della struttura dati: tabelle, colonne, tipi, relazioni e vincoli.

---

## Certificazioni Rilevanti

### Meta Front-End Developer Professional Certificate

Certificazione offerta da Meta attraverso Coursera. Copre HTML, CSS, JavaScript, React e
principi di UX design con progetti pratici. Particolarmente rilevante per le Fasi 1-3 di
questo percorso.

### Meta Back-End Developer Professional Certificate

Complementare alla certificazione frontend, copre Python, Django, database, API REST e
deployment. I concetti di design API e architettura server-side sono trasferibili a Node.js.
Allineata con la Fase 4.

### AWS Certified Developer — Associate

Certifica la capacita di sviluppare applicazioni su Amazon Web Services: EC2, S3, Lambda,
DynamoDB, API Gateway, CloudFormation. Rilevante per la Fase 5 e per ambienti aziendali con
infrastruttura AWS.

### Google UX Design Professional Certificate

Copre i fondamenti dell'esperienza utente: ricerca, wireframing, prototyping e test di
usabilita. La comprensione dei principi UX migliora la qualita delle interfacce prodotte e
la collaborazione con designer professionisti.

---

## Risorse Consigliate

### Documentazione e Riferimenti Online

- **MDN Web Docs** (developer.mozilla.org) — Risorsa di riferimento assoluto per HTML, CSS,
  JavaScript e Web API. Documentazione completa, accurata e costantemente aggiornata.
- **javascript.info** — Tutorial moderno e approfondito su JavaScript, dalla sintassi base ai
  concetti avanzati. Apprezzato per chiarezza e esempi interattivi.
- **web.dev** — Risorsa Google dedicata alle best practice: performance, accessibilita,
  sicurezza e PWA con guide pratiche e strumenti di misurazione.

### Piattaforme di Apprendimento Interattivo

- **freeCodeCamp** (freecodecamp.org) — Curriculum gratuito che copre HTML, CSS, JavaScript,
  React, Node.js e database. Formato basato su sfide progressive con progetti di certificazione.
- **The Odin Project** (theodinproject.com) — Curriculum open-source per sviluppo web
  full-stack. Enfasi sulla documentazione ufficiale e la risoluzione autonoma dei problemi.

### Libri

- **Eloquent JavaScript** di Marijn Haverbeke — Testo fondamentale che combina teoria e
  pratica. Disponibile gratuitamente online. Copre JavaScript dalle basi alla programmazione
  nel browser e su Node.js con esercizi progressivi.
- **You Don't Know JS** (serie) di Kyle Simpson — Sei libri che esplorano JavaScript in
  profondita: scope, closure, `this`, prototipi e asincronia. Disponibile gratuitamente su
  GitHub.

---

*Ultimo aggiornamento: 2026-03-28*
