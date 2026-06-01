---
corso: "Sviluppo Web"
fase: "1 — Fondamenti"
modulo: "01"
titolo: "HTML5"
versione: "HTML Living Standard"
livello: "Base"
prerequisiti: []
obiettivi:
  - "Padroneggiare la semantica HTML5 e la struttura del documento"
  - "Utilizzare elementi semantici (header, nav, main, article, section, aside)"
  - "Implementare form accessibili con validazione nativa"
  - "Integrare media (audio, video, canvas, SVG)"
  - "Applicare best practice di accessibilita (ARIA, landmark)"
  - "Comprendere il DOM e la relazione con CSS e JavaScript"
tag: [HTML5, semantica, form, accessibilita, ARIA, DOM, media]
---

# HTML5 — Guida Completa

> **Modulo 01** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare la semantica HTML5 e la struttura del documento
> 2. Utilizzare elementi semantici (header, nav, main, article, section, aside)
> 3. Implementare form accessibili con validazione nativa
> 4. Integrare media (audio, video, canvas, SVG)
> 5. Applicare best practice di accessibilita (ARIA, landmark roles)
> 6. Comprendere il DOM e la relazione con CSS e JavaScript
>
> **Tempo stimato:** 4-6 ore · **Livello:** Base

## Idee guida
1. **Semantic HTML > div soup.** `<article>`, `<section>`, `<nav>` aiutano accessibility + SEO.
2. **WCAG 2.2 e standard 2024+.** Aria-labels, keyboard navigation, contrast 4.5:1.
3. **Dialog element + popover API moderni.**
4. **Form validation: HTML5 attributes + JS for UX.**


## Indice

1. [Panoramica](#panoramica)
2. [Semantica Strutturale](#semantica-strutturale)
3. [Forms e Dati](#forms-e-dati)
4. [Multimedia e Performance](#multimedia-e-performance)
5. [API HTML5 Avanzate](#api-html5-avanzate)
6. [Accessibilita (ARIA)](#accessibilità-aria)
7. [Sicurezza Documento](#sicurezza-documento)
8. [Dialog Element e Popover API](#dialog-element-e-popover-api)
9. [Web Components](#web-components)
10. [Meta Tags, SEO e Open Graph](#meta-tags-seo-e-open-graph)
11. [SVG in HTML](#svg-in-html)
12. [HTML per Email](#html-per-email)
13. [Internazionalizzazione](#internazionalizzazione)
14. [Best Practices](#best-practices)

---

## Panoramica

### Evoluzione di HTML5

HTML5 rappresenta la quinta revisione principale del linguaggio di markup che costituisce la base strutturale del World Wide Web. Pubblicato come Recommendation dal W3C nel 2014 e successivamente mantenuto dal WHATWG come "Living Standard", HTML5 ha segnato un cambio di paradigma rispetto alle versioni precedenti. Mentre HTML 4.01 e XHTML 1.0 si concentravano prevalentemente sulla struttura documentale, HTML5 ha introdotto un ecosistema completo che comprende semantica avanzata, API JavaScript native, supporto multimedia integrato e meccanismi di storage lato client.

Le motivazioni principali dietro lo sviluppo di HTML5 includono: l'eliminazione della dipendenza da plugin esterni come Flash e Silverlight per la riproduzione di contenuti multimediali, la standardizzazione di pratiche comuni gia diffuse tra gli sviluppatori, l'introduzione di elementi semantici per migliorare l'accessibilita e l'indicizzazione da parte dei motori di ricerca, e la creazione di una piattaforma applicativa robusta direttamente nel browser.

### Struttura del Documento

Ogni documento HTML5 segue una struttura fondamentale che il browser interpreta per costruire il DOM (Document Object Model):

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Descrizione della pagina">
    <title>Titolo della Pagina</title>
    <link rel="stylesheet" href="stile.css">
</head>
<body>
    <!-- Contenuto della pagina -->
    <script src="script.js"></script>
</body>
</html>
```

### Il DOCTYPE

La dichiarazione `<!DOCTYPE html>` e notevolmente semplificata rispetto alle versioni precedenti. In HTML 4.01 e XHTML era necessario specificare un DTD (Document Type Definition) completo con URI, mentre HTML5 richiede solamente questa breve dichiarazione. Il DOCTYPE serve al browser per attivare la modalita "standards mode" anziche la "quirks mode", garantendo un rendering coerente e prevedibile. La sua semplicita riflette la filosofia pragmatica di HTML5: ridurre la complessita senza sacrificare la funzionalita.

L'elemento `<html>` con l'attributo `lang` indica la lingua principale del documento, informazione fondamentale per screen reader, motori di ricerca e strumenti di traduzione automatica. Il `<head>` contiene i metadata, mentre il `<body>` racchiude tutto il contenuto visibile.

---

## Semantica Strutturale

### Elementi Semantici

HTML5 ha introdotto una serie di elementi semantici che sostituiscono l'uso generico e indiscriminato di `<div>` e `<span>`, conferendo significato strutturale al markup. Questi elementi comunicano il ruolo del contenuto sia ai browser che alle tecnologie assistive.

**`<header>`** rappresenta il contenuto introduttivo di una sezione o dell'intero documento. Puo contenere heading, logo, navigazione e strumenti di ricerca. Un documento puo avere piu elementi `<header>`, ciascuno associato alla propria sezione genitrice.

```html
<header>
    <h1>Nome del Sito</h1>
    <nav>
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/chi-siamo">Chi Siamo</a></li>
        </ul>
    </nav>
</header>
```

**`<nav>`** identifica un blocco di link di navigazione principale. Non tutti i gruppi di link necessitano di un `<nav>` — si utilizza per la navigazione primaria del sito, menu di sezione o breadcrumb. I link nel footer, ad esempio, tipicamente non richiedono `<nav>`.

**`<main>`** rappresenta il contenuto principale del documento, unico e non ripetuto tra le pagine. Deve comparire una sola volta per documento e non deve essere annidato dentro `<article>`, `<aside>`, `<header>`, `<footer>` o `<nav>`. Questo elemento e fondamentale per l'accessibilita, poiche permette agli screen reader di saltare direttamente al contenuto rilevante.

**`<article>`** incapsula un contenuto autonomo e indipendente, che potrebbe essere estratto dal contesto e mantenere il proprio significato. Esempi tipici: un post di blog, un commento, un articolo di giornale, un widget interattivo. Gli `<article>` possono essere annidati quando il contenuto interno e correlato a quello esterno (ad esempio, commenti dentro un articolo).

**`<section>`** raggruppa contenuti tematicamente correlati, tipicamente con un proprio heading. A differenza di `<article>`, una `<section>` non e necessariamente autonoma — rappresenta un raggruppamento logico dentro un contesto piu ampio.

**`<aside>`** contiene contenuti tangenzialmente correlati al contenuto circostante: barre laterali, note a margine, box informativi, pubblicita contestuali. In un articolo, potrebbe contenere una citazione evidenziata o un glossario di termini.

**`<footer>`** rappresenta il pie di pagina della sezione o del documento. Contiene tipicamente informazioni sull'autore, copyright, link correlati, dati di contatto. Come `<header>`, puo comparire piu volte nel documento.

**`<figure>` e `<figcaption>`** raggruppano contenuti illustrativi (immagini, diagrammi, esempi di codice, citazioni) con la relativa didascalia:

```html
<figure>
    <img src="grafico-vendite.png" alt="Grafico delle vendite trimestrali 2025">
    <figcaption>Fig. 1 — Andamento delle vendite nel primo trimestre 2025.</figcaption>
</figure>
```

**`<details>` e `<summary>`** creano un widget di disclosure nativo, espandibile e comprimibile senza JavaScript:

```html
<details>
    <summary>Specifiche tecniche</summary>
    <p>Processore: ARM Cortex-A78, 2.8 GHz</p>
    <p>Memoria: 8 GB LPDDR5</p>
</details>
```

**`<dialog>`** rappresenta una finestra di dialogo o un componente interattivo modale/non modale. Supporta i metodi `.showModal()` e `.show()` tramite JavaScript, gestendo automaticamente il focus trapping e il backdrop:

```html
<dialog id="conferma">
    <h2>Conferma operazione</h2>
    <p>Procedere con l'eliminazione?</p>
    <form method="dialog">
        <button value="annulla">Annulla</button>
        <button value="conferma">Conferma</button>
    </form>
</dialog>
```

**`<template>`** contiene contenuto HTML che non viene renderizzato al caricamento della pagina, ma puo essere clonato e inserito dinamicamente tramite JavaScript. E utile per pattern ripetitivi come righe di tabella o card di prodotto:

```html
<template id="card-template">
    <article class="card">
        <h3></h3>
        <p></p>
    </article>
</template>

<script>
const template = document.getElementById('card-template');
const clone = template.content.cloneNode(true);
clone.querySelector('h3').textContent = 'Titolo';
document.body.appendChild(clone);
</script>
```

### Document Outline Algorithm

L'algoritmo di outline definisce la struttura gerarchica del documento basandosi sugli elementi di sectioning (`<article>`, `<section>`, `<nav>`, `<aside>`) e sugli heading (`<h1>`-`<h6>`). L'idea originale di HTML5 prevedeva che ogni sectioning element potesse ricominciare la gerarchia degli heading da `<h1>`, ma questa specifica non e mai stata implementata dai browser ne dalle tecnologie assistive. La raccomandazione pratica e di utilizzare una gerarchia di heading lineare e coerente nell'intero documento, evitando di saltare livelli (ad esempio da `<h2>` a `<h4>` senza passare per `<h3>`).

### Guida alla Scelta degli Elementi

La selezione dell'elemento semantico corretto segue un processo decisionale preciso:

1. Il contenuto e autonomo e redistribuibile? Usa `<article>`.
2. Il contenuto e un raggruppamento tematico con heading? Usa `<section>`.
3. Il contenuto e navigazione principale? Usa `<nav>`.
4. Il contenuto e tangenziale o supplementare? Usa `<aside>`.
5. Il contenuto e introduttivo per la sezione? Usa `<header>`.
6. Il contenuto e informazioni di chiusura? Usa `<footer>`.
7. Nessuna delle precedenti si applica? Usa `<div>`.

La regola fondamentale e: se un `<div>` serve esclusivamente per lo styling, allora `<div>` e appropriato. Se il contenuto ha un significato strutturale, esiste quasi certamente un elemento semantico piu adatto.

### Microdata e Schema.org

I microdata permettono di annotare il contenuto HTML con informazioni strutturate leggibili dai motori di ricerca, abilitando i rich snippet nei risultati di ricerca:

```html
<article itemscope itemtype="https://schema.org/Article">
    <h2 itemprop="headline">Guida alla Cucina Italiana</h2>
    <span itemprop="author" itemscope itemtype="https://schema.org/Person">
        <span itemprop="name">Marco Rossi</span>
    </span>
    <time itemprop="datePublished" datetime="2025-06-15">15 giugno 2025</time>
    <div itemprop="articleBody">
        <p>Contenuto dell'articolo...</p>
    </div>
</article>
```

Gli attributi chiave sono `itemscope` (definisce un nuovo elemento strutturato), `itemtype` (specifica il tipo secondo il vocabolario schema.org) e `itemprop` (associa una proprieta al valore). I formati alternativi includono JSON-LD (raccomandato da Google) e RDFa.

### Content Model Categories

HTML5 classifica gli elementi in categorie di contenuto che determinano dove possono essere posizionati e cosa possono contenere:

- **Flow content**: la categoria piu ampia, comprende la maggior parte degli elementi utilizzabili nel `<body>` (`<div>`, `<p>`, `<table>`, `<form>`, ecc.).
- **Phrasing content**: elementi inline come `<span>`, `<strong>`, `<em>`, `<a>`, `<img>`, `<input>`. Costituiscono il testo e i suoi marcatori.
- **Interactive content**: elementi con cui l'utente puo interagire — `<a>`, `<button>`, `<input>`, `<select>`, `<textarea>`, `<details>`.
- **Heading content**: `<h1>` attraverso `<h6>` e il gruppo `<hgroup>`.
- **Sectioning content**: `<article>`, `<aside>`, `<nav>`, `<section>` — creano nuovi ambiti nell'outline del documento.
- **Embedded content**: contenuti esterni incorporati — `<img>`, `<video>`, `<audio>`, `<canvas>`, `<iframe>`, `<svg>`.
- **Metadata content**: informazioni sul documento o sul suo comportamento — `<meta>`, `<link>`, `<style>`, `<script>`, `<title>`.

La comprensione di queste categorie e cruciale per scrivere markup valido: ad esempio, un `<p>` puo contenere solo phrasing content, quindi annidare un `<div>` (flow content) al suo interno e invalido.

### Pattern Avanzati di Annidamento Semantico

L'uso corretto degli elementi semantici richiede una comprensione approfondita delle relazioni gerarchiche tra i diversi elementi di sectioning. I pattern di annidamento seguono regole precise che determinano la leggibilita del documento sia per le tecnologie assistive che per i motori di ricerca.

**Pattern article dentro article** — utilizzato quando il contenuto interno e logicamente subordinato ma comunque autonomo. L'esempio canonico e un articolo con commenti:

```html
<article>
    <header>
        <h2>Come configurare un server Node.js</h2>
        <time datetime="2025-11-20">20 novembre 2025</time>
    </header>
    <p>Contenuto dell'articolo principale...</p>

    <section aria-label="Commenti">
        <h3>Commenti (3)</h3>
        <article>
            <header>
                <strong>Maria Bianchi</strong>
                <time datetime="2025-11-21">21 novembre 2025</time>
            </header>
            <p>Ottima guida, molto chiara!</p>
        </article>
        <article>
            <header>
                <strong>Giuseppe Verdi</strong>
                <time datetime="2025-11-22">22 novembre 2025</time>
            </header>
            <p>Potresti aggiungere un esempio con Express?</p>
        </article>
    </section>
</article>
```

**Pattern section dentro article** — raggruppamento tematico all'interno di un contenuto autonomo. Le sezioni suddividono l'articolo in parti logiche, ciascuna con il proprio heading:

```html
<article>
    <h2>Guida alla sicurezza web</h2>
    <section>
        <h3>Autenticazione</h3>
        <p>Implementare OAuth 2.0 con PKCE...</p>
    </section>
    <section>
        <h3>Autorizzazione</h3>
        <p>Role-Based Access Control (RBAC)...</p>
    </section>
    <section>
        <h3>Protezione dei dati</h3>
        <p>Crittografia at-rest e in-transit...</p>
    </section>
</article>
```

**Pattern aside nel contesto** — il significato di `<aside>` cambia in base alla posizione. Dentro un `<article>`, rappresenta contenuto tangenziale all'articolo specifico (una citazione, un glossario, una nota a margine). Fuori da qualsiasi `<article>`, rappresenta contenuto supplementare rispetto all'intera pagina (barra laterale, link correlati, widget).

```html
<main>
    <article>
        <h2>Introduzione a Rust</h2>
        <p>Rust e un linguaggio di sistema...</p>
        <aside>
            <!-- Tangenziale all'articolo -->
            <p><strong>Nota:</strong> Rust e stato votato
            "linguaggio piu amato" su Stack Overflow per 8 anni consecutivi.</p>
        </aside>
    </article>

    <aside>
        <!-- Supplementare alla pagina intera -->
        <h3>Articoli correlati</h3>
        <ul>
            <li><a href="/go">Introduzione a Go</a></li>
            <li><a href="/zig">Introduzione a Zig</a></li>
        </ul>
    </aside>
</main>
```

**Pattern nav multipli** — un documento puo contenere piu elementi `<nav>`, ciascuno identificato con un'etichetta accessibile per distinguerli. Tipicamente si hanno una navigazione principale e una secondaria:

```html
<header>
    <nav aria-label="Navigazione principale">
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/prodotti">Prodotti</a></li>
            <li><a href="/contatti">Contatti</a></li>
        </ul>
    </nav>
</header>

<nav aria-label="Breadcrumb">
    <ol>
        <li><a href="/">Home</a></li>
        <li><a href="/prodotti">Prodotti</a></li>
        <li aria-current="page">Laptop Pro 16</li>
    </ol>
</nav>

<footer>
    <nav aria-label="Navigazione footer">
        <ul>
            <li><a href="/privacy">Privacy Policy</a></li>
            <li><a href="/termini">Termini di Servizio</a></li>
        </ul>
    </nav>
</footer>
```

### Elementi Semantici Complementari

Oltre ai principali elementi di sectioning, HTML5 include elementi semantici specifici per contesti particolari che spesso vengono trascurati:

**`<hgroup>`** raggruppa un heading con sottotitoli o paragrafi supplementari. Dopo anni di discussioni, la specifica Living Standard ha ridefinito `<hgroup>` per contenere un heading (`<h1>`-`<h6>`) insieme a `<p>` che fungono da sottotitoli:

```html
<hgroup>
    <h1>Architettura dei Microservizi</h1>
    <p>Una guida pratica alla progettazione di sistemi distribuiti</p>
</hgroup>
```

**`<address>`** contiene le informazioni di contatto per l'autore dell'`<article>` o del documento piu vicino. Non e destinato a indirizzi fisici generici, ma specificamente alle informazioni di contatto dell'autore:

```html
<article>
    <h2>Ottimizzazione delle query PostgreSQL</h2>
    <p>Contenuto dell'articolo...</p>
    <footer>
        <address>
            Scritto da <a href="mailto:autore@esempio.com">Luca Rossi</a>.
            <a href="https://twitter.com/lucarossi">@lucarossi</a>
        </address>
    </footer>
</article>
```

**`<time>`** rappresenta una data, un'ora o una durata temporale. L'attributo `datetime` fornisce il valore in formato machine-readable (ISO 8601), mentre il contenuto testuale puo essere in qualsiasi formato leggibile dall'utente:

```html
<time datetime="2025-12-25">Natale 2025</time>
<time datetime="2025-11-15T14:30:00+01:00">15 novembre 2025 alle 14:30</time>
<time datetime="PT2H30M">2 ore e 30 minuti</time>
<time datetime="P3D">3 giorni</time>
```

**`<mark>`** evidenzia testo rilevante nel contesto corrente, come i termini di ricerca nei risultati o un passaggio particolarmente importante. Non e un sostituto di `<strong>` o `<em>`:

```html
<p>La ricerca per "HTML5 semantica" ha restituito 42 risultati.</p>
<p>...il documento descrive la <mark>semantica</mark> degli elementi
<mark>HTML5</mark> e il loro impatto sull'accessibilita...</p>
```

**`<data>`** associa un valore machine-readable a un contenuto leggibile dall'utente, utile per prodotti, codici o qualsiasi dato che necessita di un identificativo processabile:

```html
<p>Prodotto: <data value="SKU-12345">Laptop Pro 16 pollici</data></p>
<p>Stato: <data value="2">In lavorazione</data></p>
```

### Sectioning Roots vs Sectioning Content

HTML5 distingue tra **sectioning content** e **sectioning roots**. Gli elementi di sectioning content (`<article>`, `<section>`, `<nav>`, `<aside>`) contribuiscono all'outline del documento e creano nuovi ambiti per gli heading. I sectioning roots (`<blockquote>`, `<details>`, `<fieldset>`, `<figure>`, `<td>`) hanno un proprio outline interno che non contribuisce all'outline del documento genitore. Questa distinzione e importante perche significa che un `<h1>` dentro un `<blockquote>` non interferisce con la gerarchia di heading del documento principale, mentre un `<h1>` dentro un `<section>` ne fa parte a tutti gli effetti.

---

## Forms e Dati

### Input Types

HTML5 ha ampliato significativamente i tipi di input disponibili, permettendo ai browser di offrire interfacce native ottimizzate per ciascun tipo di dato, specialmente su dispositivi mobili dove la tastiera virtuale si adatta al tipo di input.

**`type="text"`** — Campo di testo generico, il valore predefinito. Accetta qualsiasi carattere senza validazione specifica.

**`type="email"`** — Validazione automatica del formato email. Su mobile mostra una tastiera con il simbolo `@` in evidenza. Supporta l'attributo `multiple` per accettare piu indirizzi separati da virgola.

**`type="password"`** — Oscura i caratteri inseriti. Attenzione: non cifra il valore, che viene inviato in chiaro se il form non usa HTTPS.

**`type="number"`** — Accetta valori numerici con controlli di incremento/decremento nativi. Gli attributi `min`, `max` e `step` definiscono l'intervallo e la granularita.

**`type="tel"`** — Per numeri telefonici. Non applica validazione automatica (i formati telefonici variano globalmente), ma su mobile mostra il tastierino numerico.

**`type="url"`** — Valida che il valore sia un URL assoluto. La tastiera mobile mostra tasti dedicati come `/` e `.com`.

**`type="search"`** — Funzionalmente simile a `text`, ma il browser puo applicare styling specifico (icona di cancellazione, angoli arrotondati) e integrazioni con la cronologia di ricerca.

**`type="date"`** — Mostra un date picker nativo. Il valore e sempre nel formato `YYYY-MM-DD`, indipendentemente dalla localizzazione visiva.

**`type="time"`** — Selettore di orario nativo, formato `HH:MM` o `HH:MM:SS`.

**`type="datetime-local"`** — Combinazione di data e ora locale (senza timezone). Formato: `YYYY-MM-DDTHH:MM`.

**`type="month"`** — Seleziona mese e anno. Formato: `YYYY-MM`.

**`type="week"`** — Seleziona settimana e anno. Formato: `YYYY-Www`.

**`type="range"`** — Slider per selezionare un valore numerico in un intervallo. Ideale per impostazioni come volume, luminosita, filtri di prezzo.

**`type="color"`** — Apre un color picker nativo. Il valore e nel formato esadecimale `#RRGGBB`.

**`type="file"`** — Selettore di file dal dispositivo. L'attributo `accept` filtra i tipi accettati, `multiple` permette selezione multipla.

**`type="hidden"`** — Non visualizzato, utilizzato per inviare dati al server senza interazione dell'utente (token CSRF, identificatori di sessione).

### Attributi dei Form

```html
<form action="/api/registrazione" method="POST" novalidate>
    <label for="nome">Nome completo</label>
    <input type="text" id="nome" name="nome"
           required
           minlength="2"
           maxlength="100"
           placeholder="Mario Rossi"
           autofocus
           autocomplete="name">

    <label for="email">Email</label>
    <input type="email" id="email" name="email"
           required
           pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
           autocomplete="email">

    <label for="eta">Eta</label>
    <input type="number" id="eta" name="eta"
           min="18" max="120" step="1">

    <label for="linguaggio">Linguaggio preferito</label>
    <input type="text" id="linguaggio" name="linguaggio" list="linguaggi">
    <datalist id="linguaggi">
        <option value="JavaScript">
        <option value="Python">
        <option value="TypeScript">
        <option value="Rust">
    </datalist>

    <label for="documenti">Documenti</label>
    <input type="file" id="documenti" name="documenti"
           multiple
           accept=".pdf,.doc,.docx,image/*">

    <button type="submit">Invia</button>
</form>
```

Gli attributi principali:
- **`required`**: rende il campo obbligatorio.
- **`pattern`**: espressione regolare per la validazione personalizzata.
- **`min` / `max`**: limiti numerici o di data.
- **`step`**: incremento consentito per input numerici.
- **`placeholder`**: testo suggeritivo (non sostituisce il `<label>`).
- **`autofocus`**: sposta il focus sul campo al caricamento della pagina.
- **`autocomplete`**: suggerisce valori in base alla cronologia dell'utente.
- **`multiple`**: consente valori multipli (email, file).
- **`accept`**: filtra i tipi di file accettati.
- **`list` / `<datalist>`**: fornisce suggerimenti predefiniti senza limitare l'input.

### Validazione

#### Constraint Validation API

HTML5 integra un sistema di validazione nativo che verifica automaticamente i valori dei campi prima dell'invio del form. Ogni elemento di input espone l'oggetto `validity` con proprieta booleane dettagliate:

```javascript
const input = document.getElementById('email');

// Proprieta dell'oggetto ValidityState
input.validity.valueMissing;    // true se required e vuoto
input.validity.typeMismatch;    // true se il formato non corrisponde al tipo
input.validity.patternMismatch; // true se non corrisponde al pattern
input.validity.tooLong;         // true se supera maxlength
input.validity.tooShort;        // true se inferiore a minlength
input.validity.rangeUnderflow;  // true se inferiore a min
input.validity.rangeOverflow;   // true se superiore a max
input.validity.stepMismatch;    // true se non corrisponde a step
input.validity.badInput;        // true se il browser non puo convertire l'input
input.validity.valid;           // true se tutte le validazioni passano

// Metodi
input.checkValidity();          // verifica e restituisce boolean
input.reportValidity();         // verifica, mostra messaggio e restituisce boolean
```

#### setCustomValidity()

Il metodo `setCustomValidity()` permette di definire messaggi di errore personalizzati e implementare logiche di validazione custom:

```javascript
const password = document.getElementById('password');
const conferma = document.getElementById('conferma-password');

conferma.addEventListener('input', function() {
    if (this.value !== password.value) {
        this.setCustomValidity('Le password non corrispondono');
    } else {
        this.setCustomValidity(''); // stringa vuota = valido
    }
});
```

Quando `setCustomValidity()` riceve una stringa non vuota, il campo viene considerato invalido e il messaggio fornito viene mostrato nel tooltip di validazione nativo.

#### Pseudo-classi CSS per la Validazione

CSS offre pseudo-classi per stilizzare i campi in base al loro stato di validazione:

```css
/* Campo valido */
input:valid {
    border-color: #22c55e;
}

/* Campo invalido */
input:invalid {
    border-color: #ef4444;
}

/* Campo obbligatorio */
input:required {
    border-left: 3px solid #3b82f6;
}

/* Campo opzionale */
input:optional {
    border-left: 3px solid #9ca3af;
}

/* Campo nel range consentito */
input:in-range {
    background-color: #f0fdf4;
}

/* Campo fuori range */
input:out-of-range {
    background-color: #fef2f2;
}

/* Mostra errore solo dopo interazione dell'utente */
input:not(:placeholder-shown):invalid {
    border-color: #ef4444;
    box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2);
}
```

#### Pattern di Validazione Personalizzati

Per scenari complessi, si combinano la validazione nativa con logica JavaScript custom:

```javascript
const form = document.getElementById('registrazione');

form.addEventListener('submit', function(evento) {
    evento.preventDefault();

    const campi = this.querySelectorAll('input, select, textarea');
    let valido = true;

    campi.forEach(campo => {
        if (!campo.checkValidity()) {
            valido = false;
            mostraErrore(campo, campo.validationMessage);
        } else {
            rimuoviErrore(campo);
        }
    });

    if (valido) {
        this.submit();
    }
});

function mostraErrore(campo, messaggio) {
    const contenitore = campo.closest('.campo-form');
    let errore = contenitore.querySelector('.messaggio-errore');
    if (!errore) {
        errore = document.createElement('span');
        errore.className = 'messaggio-errore';
        errore.setAttribute('role', 'alert');
        contenitore.appendChild(errore);
    }
    errore.textContent = messaggio;
    campo.setAttribute('aria-invalid', 'true');
}
```

### Form Features

#### FormData API

L'oggetto `FormData` fornisce un'interfaccia per costruire coppie chiave-valore che rappresentano i dati del form, particolarmente utile per l'invio tramite `fetch()`:

```javascript
const form = document.getElementById('profilo');

form.addEventListener('submit', async function(evento) {
    evento.preventDefault();
    const dati = new FormData(this);

    // Aggiungere dati programmaticamente
    dati.append('timestamp', Date.now());

    // Iterare sui dati
    for (const [chiave, valore] of dati.entries()) {
        console.log(`${chiave}: ${valore}`);
    }

    const risposta = await fetch('/api/profilo', {
        method: 'POST',
        body: dati  // Content-Type impostato automaticamente a multipart/form-data
    });
});
```

#### Attributo form

L'attributo `form` permette di associare un input a un form specifico anche quando l'input e posizionato al di fuori dell'elemento `<form>` nel DOM:

```html
<form id="checkout">
    <input type="text" name="indirizzo">
    <button type="submit">Completa ordine</button>
</form>

<!-- Questo input e fuori dal form ma vi partecipa comunque -->
<input type="text" name="note" form="checkout" placeholder="Note aggiuntive">
```

#### Encoding Types

L'attributo `enctype` del form specifica la codifica dei dati inviati:
- **`application/x-www-form-urlencoded`** (default): i dati vengono codificati come coppie chiave=valore nella query string.
- **`multipart/form-data`**: necessario per l'upload di file; i dati vengono inviati come parti separate con boundary.
- **`text/plain`**: codifica minimale, usata raramente.

#### Fieldset, Legend e Output

```html
<form oninput="risultato.value = parseInt(a.value) + parseInt(b.value)">
    <fieldset>
        <legend>Calcolatrice</legend>
        <input type="number" id="a" name="a" value="0"> +
        <input type="number" id="b" name="b" value="0"> =
        <output name="risultato" for="a b">0</output>
    </fieldset>

    <fieldset disabled>
        <legend>Sezione disabilitata</legend>
        <input type="text" name="campo_disabilitato">
    </fieldset>
</form>
```

`<fieldset>` raggruppa controlli correlati, `<legend>` fornisce un titolo per il gruppo, e `<output>` rappresenta il risultato di un calcolo. L'attributo `disabled` su `<fieldset>` disabilita tutti i controlli contenuti.

### Elementi di Misurazione e Progresso

HTML5 fornisce due elementi specifici per rappresentare visivamente valori numerici e stati di avanzamento, spesso confusi tra loro ma con semantiche distinte.

**`<meter>`** rappresenta un valore scalare all'interno di un intervallo noto. E adatto per indicatori come livelli di utilizzo, punteggi, livelli di carica o percentuali di completamento di un obiettivo. Non deve essere usato per indicare un progresso nel tempo — per quello esiste `<progress>`:

```html
<!-- Utilizzo disco -->
<label for="disco">Spazio disco utilizzato:</label>
<meter id="disco" value="68" min="0" max="100"
       low="50" high="80" optimum="30">68%</meter>

<!-- Punteggio esame -->
<label for="punteggio">Punteggio esame:</label>
<meter id="punteggio" value="7.5" min="0" max="10"
       low="4" high="8" optimum="10">7.5 su 10</meter>

<!-- Livello batteria -->
<label for="batteria">Batteria:</label>
<meter id="batteria" value="0.15" min="0" max="1"
       low="0.2" high="0.8" optimum="1">15%</meter>
```

Gli attributi `low`, `high` e `optimum` permettono al browser di applicare colorazioni automatiche: verde quando il valore e nella zona ottimale, giallo nella zona di attenzione e rosso nella zona critica. L'algoritmo di colorazione dipende dalla relazione tra `optimum` e le soglie `low`/`high`.

**`<progress>`** rappresenta lo stato di avanzamento di un'operazione in corso. A differenza di `<meter>`, indica un processo che evolve nel tempo — un download, un upload, un'elaborazione:

```html
<!-- Progresso determinato -->
<label for="upload">Upload file:</label>
<progress id="upload" value="45" max="100">45%</progress>

<!-- Progresso indeterminato (senza value) -->
<label for="caricamento">Caricamento in corso:</label>
<progress id="caricamento">Caricamento...</progress>

<script>
// Aggiornamento programmatico
const barra = document.getElementById('upload');
function aggiornaProgresso(percentuale) {
    barra.value = percentuale;
    barra.textContent = `${percentuale}%`; // Fallback testuale
}
</script>
```

Quando `<progress>` non ha l'attributo `value`, il browser mostra un'animazione indeterminata (tipicamente una barra che scorre), utile quando la durata dell'operazione non e prevedibile.

### Tecniche Avanzate con FormData

L'API `FormData` offre funzionalita avanzate oltre alla semplice raccolta dei dati del form. Permette la manipolazione granulare dei dati, la conversione tra formati e la gestione di scenari complessi come upload multipli e invio in formato JSON.

```javascript
const form = document.getElementById('profilo');
const dati = new FormData(form);

// Iterazione con destructuring
for (const [chiave, valore] of dati.entries()) {
    console.log(`${chiave}: ${valore}`);
}

// Verifica esistenza di una chiave
if (dati.has('avatar')) {
    const file = dati.get('avatar');
    console.log(`File: ${file.name}, Dimensione: ${file.size} bytes`);
}

// Ottenere tutti i valori per una chiave (utile per checkbox multipli)
const interessi = dati.getAll('interessi');
console.log('Interessi selezionati:', interessi);

// Rimuovere una chiave
dati.delete('campo_temporaneo');

// Sovrascrivere un valore
dati.set('timestamp', new Date().toISOString());

// Conversione a oggetto JavaScript
const oggetto = Object.fromEntries(dati.entries());

// Conversione a JSON per API REST
const json = JSON.stringify(oggetto);

// Invio come JSON anziche multipart
const risposta = await fetch('/api/profilo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: json
});
```

#### Upload di File con FormData e Monitoraggio del Progresso

Per upload di file con monitoraggio del progresso, `FormData` si combina con `XMLHttpRequest` (che espone l'evento `progress`) oppure con l'API `fetch` e i ReadableStream:

```javascript
const form = document.getElementById('form-upload');

form.addEventListener('submit', async function(evento) {
    evento.preventDefault();
    const dati = new FormData(this);

    // Validazione lato client dei file
    const file = dati.get('documento');
    const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
    const TIPI_CONSENTITI = ['application/pdf', 'image/png', 'image/jpeg'];

    if (file.size > MAX_SIZE) {
        mostraErrore('Il file supera il limite di 10 MB');
        return;
    }

    if (!TIPI_CONSENTITI.includes(file.type)) {
        mostraErrore('Formato file non supportato');
        return;
    }

    // Upload con monitoraggio del progresso via XMLHttpRequest
    const xhr = new XMLHttpRequest();
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentuale = Math.round((e.loaded / e.total) * 100);
            aggiornaBarraProgresso(percentuale);
        }
    });

    xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
            mostraSuccesso('File caricato con successo');
        } else {
            mostraErrore(`Errore server: ${xhr.status}`);
        }
    });

    xhr.addEventListener('error', () => mostraErrore('Errore di rete'));
    xhr.open('POST', '/api/upload');
    xhr.send(dati);
});
```

### Validazione Avanzata con la Constraint Validation API

Oltre ai metodi di base, la Constraint Validation API offre funzionalita avanzate per scenari complessi di validazione.

**`reportValidity()`** e simile a `checkValidity()` ma mostra anche il tooltip nativo del browser con il messaggio di errore. Utile per validazioni triggered da eventi diversi dal submit:

```javascript
// Validazione in tempo reale su blur
document.querySelectorAll('input').forEach(campo => {
    campo.addEventListener('blur', function() {
        this.reportValidity();
    });
});
```

**`formnovalidate`** e un attributo applicabile ai button di submit per bypassare la validazione del form su quel singolo pulsante. Utile per pulsanti "Salva come bozza" che non richiedono tutti i campi obbligatori:

```html
<form action="/api/articolo" method="POST">
    <input type="text" name="titolo" required>
    <textarea name="contenuto" required></textarea>

    <!-- Questo pulsante bypassa la validazione -->
    <button type="submit" formnovalidate formaction="/api/bozza">
        Salva come bozza
    </button>

    <!-- Questo pulsante richiede la validazione completa -->
    <button type="submit">Pubblica</button>
</form>
```

**Validazione cross-field** — pattern per validare relazioni tra piu campi, come intervalli di date o confronto di password:

```javascript
const form = document.getElementById('prenotazione');
const dataInizio = form.querySelector('#data-inizio');
const dataFine = form.querySelector('#data-fine');

function validaIntervallo() {
    const inizio = new Date(dataInizio.value);
    const fine = new Date(dataFine.value);

    if (fine <= inizio) {
        dataFine.setCustomValidity(
            'La data di fine deve essere successiva alla data di inizio'
        );
    } else if ((fine - inizio) / (1000 * 60 * 60 * 24) > 30) {
        dataFine.setCustomValidity(
            'La prenotazione non puo superare i 30 giorni'
        );
    } else {
        dataFine.setCustomValidity('');
    }
}

dataInizio.addEventListener('change', validaIntervallo);
dataFine.addEventListener('change', validaIntervallo);
```

**Evento `invalid`** — viene emesso quando un campo non supera la validazione. Puo essere intercettato per personalizzare completamente l'interfaccia di errore:

```javascript
const campo = document.getElementById('email');

campo.addEventListener('invalid', function(evento) {
    evento.preventDefault(); // Impedisce il tooltip nativo del browser

    const messaggio = this.validity.valueMissing
        ? 'L\'indirizzo email e obbligatorio'
        : this.validity.typeMismatch
        ? 'Inserisci un indirizzo email valido (es. nome@dominio.it)'
        : this.validity.patternMismatch
        ? 'L\'email deve appartenere al dominio aziendale'
        : 'Valore non valido';

    mostraErrorePersonalizzato(this, messaggio);
});
```

---

## Multimedia e Performance

### Immagini

#### Immagini Responsive con srcset e sizes

L'attributo `srcset` consente di fornire versioni multiple di un'immagine a risoluzioni differenti, permettendo al browser di scegliere la piu appropriata in base alla densita di pixel del dispositivo e alle dimensioni del viewport:

```html
<!-- Descrittori di larghezza (w) -->
<img src="foto-800.jpg"
     srcset="foto-400.jpg 400w,
             foto-800.jpg 800w,
             foto-1200.jpg 1200w,
             foto-1600.jpg 1600w"
     sizes="(max-width: 600px) 100vw,
            (max-width: 1200px) 50vw,
            33vw"
     alt="Panorama montano al tramonto">

<!-- Descrittori di densita (x) -->
<img src="logo.png"
     srcset="logo.png 1x,
             logo@2x.png 2x,
             logo@3x.png 3x"
     alt="Logo aziendale">
```

L'attributo `sizes` indica al browser le dimensioni che l'immagine occupera a diversi breakpoint, permettendogli di scaricare la versione ottimale prima ancora che il CSS venga elaborato.

#### L'Elemento picture per Art Direction

`<picture>` offre un controllo piu granulare sulla selezione dell'immagine, consentendo l'art direction — ovvero la scelta di ritagli o composizioni diverse in base al contesto:

```html
<picture>
    <source media="(max-width: 600px)"
            srcset="hero-mobile.webp" type="image/webp">
    <source media="(max-width: 600px)"
            srcset="hero-mobile.jpg" type="image/jpeg">
    <source media="(min-width: 601px)"
            srcset="hero-desktop.avif" type="image/avif">
    <source media="(min-width: 601px)"
            srcset="hero-desktop.webp" type="image/webp">
    <img src="hero-desktop.jpg" alt="Immagine principale del sito"
         width="1200" height="600">
</picture>
```

#### Formati Moderni: WebP e AVIF

**WebP** offre compressione superiore del 25-35% rispetto a JPEG con qualita comparabile, supporta trasparenza (come PNG) e animazioni (come GIF). Il supporto browser e ormai universale.

**AVIF** (AV1 Image File Format) rappresenta la generazione successiva: compressione fino al 50% migliore di JPEG, supporto per HDR e wide color gamut. Il supporto browser e in rapida espansione ma non ancora universale, rendendo necessario il fallback tramite `<picture>`.

#### Lazy Loading

L'attributo `loading="lazy"` differisce il caricamento delle immagini fino a quando non si avvicinano al viewport, riducendo il tempo di caricamento iniziale e il consumo di banda:

```html
<!-- Le immagini above-the-fold NON devono essere lazy -->
<img src="hero.jpg" alt="..." loading="eager" fetchpriority="high">

<!-- Le immagini below-the-fold beneficiano del lazy loading -->
<img src="galleria-01.jpg" alt="..." loading="lazy" width="800" height="600">
<img src="galleria-02.jpg" alt="..." loading="lazy" width="800" height="600">
```

#### Aspect Ratio e CLS

Specificare `width` e `height` nell'elemento `<img>` permette al browser di riservare lo spazio corretto prima del caricamento dell'immagine, evitando il Cumulative Layout Shift (CLS) — uno dei Core Web Vitals. Il browser calcola automaticamente l'aspect ratio da questi attributi:

```html
<!-- Il browser riserva lo spazio con rapporto 16:9 -->
<img src="foto.jpg" width="1600" height="900" alt="..." style="width: 100%; height: auto;">
```

### Video e Audio

#### Elementi video e audio

```html
<video controls width="720" height="405" poster="anteprima.jpg"
       preload="metadata" playsinline>
    <source src="video.mp4" type="video/mp4">
    <source src="video.webm" type="video/webm">
    <track kind="subtitles" src="sottotitoli-it.vtt"
           srclang="it" label="Italiano" default>
    <track kind="subtitles" src="sottotitoli-en.vtt"
           srclang="en" label="English">
    <track kind="descriptions" src="descrizioni.vtt"
           srclang="it" label="Audiodescrizioni">
    <p>Il tuo browser non supporta il tag video.
       <a href="video.mp4">Scarica il video</a>.</p>
</video>

<audio controls preload="none">
    <source src="podcast.mp3" type="audio/mpeg">
    <source src="podcast.ogg" type="audio/ogg">
    <p>Il tuo browser non supporta l'elemento audio.</p>
</audio>
```

L'attributo `playsinline` e essenziale per iOS, dove i video senza questo attributo si aprono automaticamente in modalita fullscreen. L'attributo `poster` definisce l'immagine di anteprima. L'attributo `preload` controlla il precaricamento: `none` (nessun dato), `metadata` (solo durata e dimensioni), `auto` (il browser decide).

#### Sottotitoli con WebVTT

Il formato WebVTT (Web Video Text Tracks) gestisce sottotitoli, didascalie e metadati temporali:

```
WEBVTT

00:00:01.000 --> 00:00:04.000
Benvenuti alla nostra guida
su HTML5.

00:00:04.500 --> 00:00:08.000
In questo video tratteremo
gli elementi semantici.
```

#### Media API

L'API JavaScript per il controllo dei media offre metodi e proprieta per l'interazione programmatica:

```javascript
const video = document.querySelector('video');

video.play();                    // Avvia la riproduzione
video.pause();                   // Mette in pausa
video.currentTime = 30;          // Salta al secondo 30
video.playbackRate = 1.5;        // Velocita 1.5x
video.volume = 0.8;              // Volume all'80%
video.muted = true;              // Silenzia

video.addEventListener('timeupdate', () => {
    const percentuale = (video.currentTime / video.duration) * 100;
    barraProgresso.style.width = `${percentuale}%`;
});

video.addEventListener('ended', () => {
    console.log('Riproduzione terminata');
});
```

### Performance

#### Resource Hints

I resource hints informano il browser sulle risorse che saranno necessarie, permettendogli di ottimizzare il caricamento:

```html
<!-- Preconnect: stabilisce la connessione anticipatamente -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://cdn.esempio.com" crossorigin>

<!-- DNS Prefetch: risolve il DNS anticipatamente (meno aggressivo) -->
<link rel="dns-prefetch" href="https://analytics.esempio.com">

<!-- Preload: carica risorse critiche con alta priorita -->
<link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/css/critico.css" as="style">
<link rel="preload" href="/img/hero.webp" as="image">

<!-- Prefetch: carica risorse per la navigazione futura con bassa priorita -->
<link rel="prefetch" href="/pagina-successiva.html">
<link rel="prefetch" href="/js/modulo-checkout.js" as="script">
```

#### Caricamento degli Script

La modalita di caricamento degli script influenza significativamente le performance di rendering:

```html
<!-- Bloccante: il parsing HTML si ferma fino al download e all'esecuzione -->
<script src="bloccante.js"></script>

<!-- Async: download parallelo, esecuzione appena disponibile (ordine non garantito) -->
<script src="analytics.js" async></script>

<!-- Defer: download parallelo, esecuzione dopo il parsing HTML (ordine preservato) -->
<script src="app.js" defer></script>

<!-- Module: comportamento defer implicito, supporta import/export -->
<script type="module" src="modulo.js"></script>
```

**`async`** e ideale per script indipendenti come analytics o widget di terze parti. **`defer`** e preferibile per script applicativi che dipendono dal DOM o da altri script. **`type="module"`** abilita i moduli ES con scope isolato e `defer` implicito.

#### Critical Rendering Path

Il percorso critico di rendering comprende i passaggi che il browser esegue per trasformare HTML, CSS e JavaScript nel primo frame visibile:

1. **Costruzione del DOM**: il parser HTML converte il markup in un albero di nodi.
2. **Costruzione del CSSOM**: i fogli di stile vengono elaborati in un modello a oggetti CSS.
3. **Render Tree**: DOM e CSSOM vengono combinati (escludendo elementi con `display: none`).
4. **Layout**: il browser calcola posizione e dimensioni di ogni elemento.
5. **Paint**: i pixel vengono disegnati sullo schermo.

Per ottimizzare il percorso critico: minimizzare le risorse bloccanti, inline il CSS critico, differire gli script non essenziali, e utilizzare resource hints per le risorse prioritarie.

#### Fetchpriority e Prioritizzazione Granulare

L'attributo `fetchpriority` permette di influenzare la priorita di download delle risorse rispetto ad altre risorse dello stesso tipo. Accetta tre valori: `high`, `low` e `auto` (default). Questo attributo e particolarmente utile per ottimizzare il LCP:

```html
<!-- Immagine hero: massima priorita -->
<img src="hero.webp" alt="..." fetchpriority="high" loading="eager">

<!-- Immagini di galleria sotto il fold: bassa priorita -->
<img src="galleria-01.jpg" alt="..." fetchpriority="low" loading="lazy">

<!-- Script critico con alta priorita -->
<script src="app-core.js" fetchpriority="high"></script>

<!-- Script non critico con bassa priorita -->
<script src="analytics.js" fetchpriority="low" async></script>

<!-- Preload con priorita specifica -->
<link rel="preload" href="/fonts/inter-var.woff2" as="font"
      type="font/woff2" crossorigin fetchpriority="high">
```

La differenza chiave rispetto a `loading` e che `fetchpriority` non cambia il timing del caricamento (quando la risorsa viene richiesta) ma la sua precedenza nella coda di download del browser. Due immagini `loading="eager"` competono per la stessa banda; `fetchpriority="high"` su una di esse le garantisce la precedenza.

#### Modulepreload

`<link rel="modulepreload">` e specifico per i moduli ES: oltre a scaricare il file, esegue anche il parsing e la compilazione del modulo, rendendolo immediatamente disponibile quando viene importato:

```html
<!-- Precarica e compila il modulo -->
<link rel="modulepreload" href="/js/app.js">
<link rel="modulepreload" href="/js/utils.js">

<!-- Il modulo e gia pronto quando viene richiesto -->
<script type="module" src="/js/app.js"></script>
```

A differenza di `<link rel="preload" as="script">`, `modulepreload` gestisce automaticamente la catena di dipendenze del modulo e non richiede l'attributo `as`.

#### Speculation Rules API

La Speculation Rules API (Baseline dal 2025) rappresenta un'evoluzione rispetto a `<link rel="prefetch">`, offrendo un controllo piu granulare sul precaricamento speculativo delle pagine:

```html
<script type="speculationrules">
{
    "prerender": [
        {
            "where": { "href_matches": "/prodotti/*" },
            "eagerness": "moderate"
        }
    ],
    "prefetch": [
        {
            "urls": ["/chi-siamo", "/contatti"],
            "eagerness": "eager"
        },
        {
            "where": { "selector_matches": ".link-navigazione" },
            "eagerness": "moderate"
        }
    ]
}
</script>
```

I livelli di `eagerness` controllano quando il browser avvia la speculazione: `immediate` (subito), `eager` (molto presto), `moderate` (all'hover) e `conservative` (al click). La differenza tra `prefetch` (scarica solo le risorse) e `prerender` (costruisce l'intera pagina in background, incluso il DOM e l'esecuzione JavaScript) e significativa in termini di risorse consumate. Il prerender rende la navigazione quasi istantanea ma consuma CPU, memoria e banda.

#### Core Web Vitals

I Core Web Vitals sono metriche centrate sull'utente che Google utilizza come fattori di ranking:

- **LCP (Largest Contentful Paint)**: misura il tempo di rendering dell'elemento piu grande visibile nel viewport. Obiettivo: entro 2.5 secondi. Ottimizzare immagini, font, CSS critico e tempo di risposta del server.
- **INP (Interaction to Next Paint)**: ha sostituito FID (First Input Delay). Misura la latenza complessiva delle interazioni dell'utente durante l'intera sessione. Obiettivo: entro 200 millisecondi. Ridurre i long task JavaScript, ottimizzare gli event handler.
- **CLS (Cumulative Layout Shift)**: misura la stabilita visiva, cioe quanto gli elementi si spostano durante il caricamento. Obiettivo: sotto 0.1. Specificare dimensioni per immagini e iframe, evitare inserimento dinamico di contenuti above-the-fold.

---

## API HTML5 Avanzate

### Web Storage

Web Storage fornisce un meccanismo semplice per memorizzare coppie chiave-valore nel browser:

```javascript
// localStorage: persiste anche dopo la chiusura del browser
localStorage.setItem('tema', 'scuro');
localStorage.setItem('utente', JSON.stringify({ nome: 'Luca', ruolo: 'admin' }));

const tema = localStorage.getItem('tema');
const utente = JSON.parse(localStorage.getItem('utente'));
localStorage.removeItem('tema');
localStorage.clear(); // rimuove tutto

// sessionStorage: persiste solo nella sessione della tab
sessionStorage.setItem('filtro', 'attivi');

// Evento storage per sincronizzazione tra tab
window.addEventListener('storage', (evento) => {
    console.log(`Chiave: ${evento.key}, Vecchio: ${evento.oldValue}, Nuovo: ${evento.newValue}`);
});
```

La capacita tipica e di 5-10 MB per origine. I dati sono sincronizzati e bloccano il thread principale — per grandi volumi di dati, preferire IndexedDB.

### IndexedDB

IndexedDB e un database transazionale asincrono nel browser, capace di memorizzare grandi quantita di dati strutturati, inclusi file e blob:

```javascript
const richiesta = indexedDB.open('MioDatabase', 1);

richiesta.onupgradeneeded = (evento) => {
    const db = evento.target.result;
    const store = db.createObjectStore('prodotti', { keyPath: 'id', autoIncrement: true });
    store.createIndex('nome', 'nome', { unique: false });
    store.createIndex('categoria', 'categoria', { unique: false });
};

richiesta.onsuccess = (evento) => {
    const db = evento.target.result;
    const transazione = db.transaction(['prodotti'], 'readwrite');
    const store = transazione.objectStore('prodotti');

    store.add({ nome: 'Laptop', categoria: 'elettronica', prezzo: 999 });

    const indiceCat = store.index('categoria');
    const query = indiceCat.getAll('elettronica');
    query.onsuccess = () => console.log(query.result);
};
```

### Web Workers

I Web Workers eseguono JavaScript in thread separati, evitando di bloccare il thread principale dell'interfaccia utente:

```javascript
// main.js — Thread principale
const worker = new Worker('elaborazione.js');

worker.postMessage({ dati: grandeArray, operazione: 'ordina' });

worker.onmessage = (evento) => {
    console.log('Risultato dal worker:', evento.data);
};

worker.onerror = (errore) => {
    console.error('Errore nel worker:', errore.message);
};

// elaborazione.js — Worker dedicato
self.onmessage = (evento) => {
    const { dati, operazione } = evento.data;
    if (operazione === 'ordina') {
        const risultato = dati.sort((a, b) => a - b);
        self.postMessage(risultato);
    }
};
```

I **Shared Workers** (`new SharedWorker('shared.js')`) possono essere condivisi tra piu tab o finestre della stessa origine, utili per gestire connessioni WebSocket centralizzate o stato condiviso.

### Service Workers

I Service Workers agiscono come proxy di rete programmabili, intercettando le richieste HTTP e abilitando funzionalita offline, caching avanzato e notifiche push:

```javascript
// Registrazione
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
        .then(reg => console.log('Service Worker registrato', reg.scope))
        .catch(err => console.error('Registrazione fallita', err));
}

// sw.js
const CACHE = 'app-v1';
const RISORSE = ['/', '/css/app.css', '/js/app.js', '/offline.html'];

self.addEventListener('install', evento => {
    evento.waitUntil(
        caches.open(CACHE).then(cache => cache.addAll(RISORSE))
    );
});

self.addEventListener('fetch', evento => {
    evento.respondWith(
        caches.match(evento.request)
            .then(risposta => risposta || fetch(evento.request))
            .catch(() => caches.match('/offline.html'))
    );
});
```

### WebSocket API

I WebSocket forniscono comunicazione bidirezionale persistente tra client e server:

```javascript
const ws = new WebSocket('wss://api.esempio.com/ws');

ws.addEventListener('open', () => {
    console.log('Connessione stabilita');
    ws.send(JSON.stringify({ tipo: 'saluto', messaggio: 'Ciao server' }));
});

ws.addEventListener('message', (evento) => {
    const dati = JSON.parse(evento.data);
    console.log('Messaggio ricevuto:', dati);
});

ws.addEventListener('close', (evento) => {
    console.log(`Connessione chiusa: ${evento.code} ${evento.reason}`);
});

ws.addEventListener('error', (errore) => {
    console.error('Errore WebSocket:', errore);
});
```

### Geolocation API

L'API di geolocalizzazione permette di ottenere la posizione dell'utente (con il suo consenso esplicito):

```javascript
if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
        (posizione) => {
            const { latitude, longitude, accuracy } = posizione.coords;
            console.log(`Lat: ${latitude}, Lon: ${longitude}, Precisione: ${accuracy}m`);
        },
        (errore) => {
            switch (errore.code) {
                case errore.PERMISSION_DENIED:
                    console.log('Permesso negato dall\'utente');
                    break;
                case errore.POSITION_UNAVAILABLE:
                    console.log('Posizione non disponibile');
                    break;
                case errore.TIMEOUT:
                    console.log('Timeout della richiesta');
                    break;
            }
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );

    // Monitoraggio continuo della posizione
    const watchId = navigator.geolocation.watchPosition(callback, errorCallback);
    navigator.geolocation.clearWatch(watchId); // Per interrompere
}
```

### Notification API

Le notifiche desktop informano l'utente anche quando la tab non e in primo piano:

```javascript
async function inviaNotifica(titolo, corpo) {
    if (!('Notification' in window)) return;

    if (Notification.permission === 'default') {
        await Notification.requestPermission();
    }

    if (Notification.permission === 'granted') {
        new Notification(titolo, {
            body: corpo,
            icon: '/img/icona-notifica.png',
            badge: '/img/badge.png',
            tag: 'aggiornamento',       // Raggruppa notifiche simili
            requireInteraction: false
        });
    }
}
```

### Intersection Observer

Osserva quando un elemento entra o esce dal viewport, ideale per lazy loading, animazioni allo scroll e infinite scrolling:

```javascript
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visibile');
            // Lazy load dell'immagine
            if (entry.target.dataset.src) {
                entry.target.src = entry.target.dataset.src;
                observer.unobserve(entry.target);
            }
        }
    });
}, {
    root: null,             // viewport come root
    rootMargin: '0px 0px 200px 0px', // pre-carica 200px prima
    threshold: [0, 0.25, 0.5, 0.75, 1]
});

document.querySelectorAll('.lazy-img').forEach(img => observer.observe(img));
```

### Resize Observer

Osserva i cambiamenti di dimensione di un elemento, piu efficiente e preciso di `window.resize`:

```javascript
const resizeObserver = new ResizeObserver((entries) => {
    entries.forEach(entry => {
        const { width, height } = entry.contentRect;
        if (width < 400) {
            entry.target.classList.add('compatto');
        } else {
            entry.target.classList.remove('compatto');
        }
    });
});

resizeObserver.observe(document.querySelector('.container-adattivo'));
```

### MutationObserver

Monitora le modifiche al DOM in modo asincrono ed efficiente:

```javascript
const mutationObserver = new MutationObserver((mutazioni) => {
    mutazioni.forEach(mutazione => {
        if (mutazione.type === 'childList') {
            mutazione.addedNodes.forEach(nodo => {
                if (nodo.nodeType === Node.ELEMENT_NODE) {
                    console.log('Elemento aggiunto:', nodo.tagName);
                }
            });
        }
    });
});

mutationObserver.observe(document.getElementById('lista-dinamica'), {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class', 'data-stato']
});
```

### Clipboard API

Accesso asincrono agli appunti di sistema con gestione dei permessi:

```javascript
// Copiare testo
async function copiaTestoNegli Appunti(testo) {
    try {
        await navigator.clipboard.writeText(testo);
        console.log('Testo copiato');
    } catch (errore) {
        console.error('Copia fallita:', errore);
    }
}

// Leggere testo
async function leggiDagliAppunti() {
    try {
        const testo = await navigator.clipboard.readText();
        return testo;
    } catch (errore) {
        console.error('Lettura appunti fallita:', errore);
    }
}
```

### Drag and Drop API

L'API nativa per il trascinamento di elementi:

```javascript
const trascinabile = document.getElementById('elemento');
const zona = document.getElementById('zona-rilascio');

trascinabile.addEventListener('dragstart', (evento) => {
    evento.dataTransfer.setData('text/plain', evento.target.id);
    evento.dataTransfer.effectAllowed = 'move';
    evento.target.classList.add('trascinando');
});

trascinabile.addEventListener('dragend', (evento) => {
    evento.target.classList.remove('trascinando');
});

zona.addEventListener('dragover', (evento) => {
    evento.preventDefault(); // Necessario per permettere il drop
    evento.dataTransfer.dropEffect = 'move';
});

zona.addEventListener('drop', (evento) => {
    evento.preventDefault();
    const id = evento.dataTransfer.getData('text/plain');
    const elemento = document.getElementById(id);
    zona.appendChild(elemento);
});
```

### Canvas 2D

L'elemento `<canvas>` fornisce una superficie di disegno bitmap programmabile tramite JavaScript:

```html
<canvas id="grafico" width="600" height="400"></canvas>
```

```javascript
const canvas = document.getElementById('grafico');
const ctx = canvas.getContext('2d');

// Rettangolo con gradiente
const gradiente = ctx.createLinearGradient(0, 0, 600, 0);
gradiente.addColorStop(0, '#3b82f6');
gradiente.addColorStop(1, '#8b5cf6');
ctx.fillStyle = gradiente;
ctx.fillRect(50, 50, 500, 300);

// Testo
ctx.font = 'bold 24px Inter, sans-serif';
ctx.fillStyle = '#ffffff';
ctx.textAlign = 'center';
ctx.fillText('Grafico di Esempio', 300, 200);

// Cerchio
ctx.beginPath();
ctx.arc(300, 300, 40, 0, Math.PI * 2);
ctx.fillStyle = '#22c55e';
ctx.fill();
ctx.strokeStyle = '#ffffff';
ctx.lineWidth = 3;
ctx.stroke();
```

Canvas e ideale per grafici, visualizzazioni dati, giochi 2D e manipolazione di immagini. Per grafica vettoriale scalabile, preferire SVG inline.

### Canvas 2D — Approfondimento

#### Tracciati Complessi e Trasformazioni

Il contesto 2D di Canvas supporta tracciati complessi con curve di Bezier, trasformazioni matriciali e compositing avanzato:

```javascript
const canvas = document.getElementById('disegno');
const ctx = canvas.getContext('2d');

// Salva lo stato corrente (trasformazioni, stili, clip)
ctx.save();

// Trasformazioni
ctx.translate(200, 200);     // Sposta l'origine
ctx.rotate(Math.PI / 4);     // Ruota di 45 gradi
ctx.scale(1.5, 1.5);         // Scala 150%

// Curva di Bezier cubica
ctx.beginPath();
ctx.moveTo(0, 0);
ctx.bezierCurveTo(50, -80, 150, -80, 200, 0);
ctx.strokeStyle = '#6366f1';
ctx.lineWidth = 2;
ctx.stroke();

// Ripristina lo stato precedente
ctx.restore();

// Compositing: controlla come i nuovi disegni si sovrappongono
ctx.globalCompositeOperation = 'multiply';  // 'source-over' e il default
ctx.globalAlpha = 0.7;  // Trasparenza globale
```

#### Manipolazione dei Pixel e Esportazione

Canvas permette l'accesso diretto ai dati pixel dell'immagine per elaborazioni come filtri, analisi cromatiche o generazione procedurale:

```javascript
// Ottenere i dati pixel di un'area
const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
const pixels = imageData.data; // Uint8ClampedArray [R, G, B, A, R, G, B, A, ...]

// Applicare un filtro in scala di grigi
for (let i = 0; i < pixels.length; i += 4) {
    const media = (pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3;
    pixels[i] = media;       // R
    pixels[i + 1] = media;   // G
    pixels[i + 2] = media;   // B
    // pixels[i + 3] = alpha (invariato)
}

// Riscrivere i pixel modificati
ctx.putImageData(imageData, 0, 0);

// Esportazione come data URL (base64)
const dataUrl = canvas.toDataURL('image/png');
// Risultato: "data:image/png;base64,iVBORw0KGgo..."

// Esportazione come Blob (per upload o download)
canvas.toBlob((blob) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'grafico.png';
    link.click();
    URL.revokeObjectURL(url);
}, 'image/png');
```

#### OffscreenCanvas

`OffscreenCanvas` separa il rendering del canvas dal thread principale dell'interfaccia, permettendo di eseguire operazioni grafiche intensive in un Web Worker senza bloccare l'interazione dell'utente:

```javascript
// main.js — Thread principale
const canvas = document.getElementById('grafico');
const offscreen = canvas.transferControlToOffscreen();
const worker = new Worker('render-worker.js');
worker.postMessage({ canvas: offscreen }, [offscreen]);

// render-worker.js — Web Worker
self.onmessage = (evento) => {
    const canvas = evento.data.canvas;
    const ctx = canvas.getContext('2d');

    function loop() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        // Operazioni di disegno intensive...
        ctx.fillStyle = '#3b82f6';
        ctx.fillRect(Math.random() * canvas.width, 0, 10, canvas.height);
        requestAnimationFrame(loop);
    }
    loop();
};
```

#### Accessibilita del Canvas

L'elemento `<canvas>` e intrinsecamente inaccessibile: il suo contenuto e un bitmap opaco che le tecnologie assistive non possono interpretare. E fondamentale fornire alternative accessibili:

```html
<canvas id="grafico-vendite" width="600" height="400"
        role="img"
        aria-label="Grafico a barre delle vendite trimestrali 2025">
    <!-- Contenuto fallback per screen reader e browser senza canvas -->
    <table>
        <caption>Vendite trimestrali 2025</caption>
        <tr><th>Q1</th><td>€ 150.000</td></tr>
        <tr><th>Q2</th><td>€ 180.000</td></tr>
        <tr><th>Q3</th><td>€ 165.000</td></tr>
        <tr><th>Q4</th><td>€ 210.000</td></tr>
    </table>
</canvas>
```

Per grafici interattivi, considerare `role="application"` con gestione keyboard completa, oppure utilizzare librerie come Chart.js che generano automaticamente tabelle dati accessibili come fallback.

### History API

L'API History permette la manipolazione della cronologia del browser senza ricaricare la pagina, fondamentale per le Single Page Application:

```javascript
// Aggiungere una nuova voce nella cronologia
history.pushState({ pagina: 'prodotti', filtro: 'attivi' }, '', '/prodotti?filtro=attivi');

// Sostituire la voce corrente
history.replaceState({ pagina: 'prodotti', filtro: 'tutti' }, '', '/prodotti');

// Gestire la navigazione avanti/indietro
window.addEventListener('popstate', (evento) => {
    if (evento.state) {
        caricaPagina(evento.state.pagina, evento.state.filtro);
    }
});
```

### Fullscreen API

Permette di visualizzare un elemento a schermo intero:

```javascript
async function attivaSchermointero(elemento) {
    try {
        if (elemento.requestFullscreen) {
            await elemento.requestFullscreen();
        }
    } catch (errore) {
        console.error('Errore fullscreen:', errore);
    }
}

document.addEventListener('fullscreenchange', () => {
    if (document.fullscreenElement) {
        console.log('Modalita schermo intero attiva');
    } else {
        console.log('Uscita dallo schermo intero');
    }
});

// Uscire dal fullscreen
document.exitFullscreen();
```

---

## Accessibilita (ARIA)

### Ruoli ARIA

ARIA (Accessible Rich Internet Applications) estende HTML con attributi che comunicano semantica aggiuntiva alle tecnologie assistive. I ruoli si dividono in tre categorie principali:

**Landmark roles** — Identificano le regioni principali della pagina, permettendo la navigazione rapida con screen reader:
- `role="banner"` (implicito in `<header>` figlio di `<body>`)
- `role="navigation"` (implicito in `<nav>`)
- `role="main"` (implicito in `<main>`)
- `role="complementary"` (implicito in `<aside>`)
- `role="contentinfo"` (implicito in `<footer>` figlio di `<body>`)
- `role="search"` (associabile a un form di ricerca)
- `role="region"` (implicito in `<section>` con label accessibile)

**Widget roles** — Definiscono componenti interattivi personalizzati:
- `role="tablist"`, `role="tab"`, `role="tabpanel"` per interfacce a tab
- `role="dialog"`, `role="alertdialog"` per finestre modali
- `role="menu"`, `role="menuitem"` per menu applicativi
- `role="tree"`, `role="treeitem"` per strutture ad albero
- `role="tooltip"`, `role="status"`, `role="alert"` per informazioni contestuali

**Document structure roles** — Forniscono informazioni sulla struttura del contenuto:
- `role="list"`, `role="listitem"` per liste personalizzate
- `role="table"`, `role="row"`, `role="cell"` per tabelle personalizzate
- `role="img"` per raggruppare elementi che formano un'immagine composita
- `role="heading"` con `aria-level` per heading personalizzati

### Attributi ARIA Fondamentali

```html
<!-- aria-label: etichetta accessibile diretta -->
<button aria-label="Chiudi finestra di dialogo">
    <svg><!-- icona X --></svg>
</button>

<!-- aria-labelledby: etichetta tramite riferimento a un altro elemento -->
<div role="dialog" aria-labelledby="titolo-modale">
    <h2 id="titolo-modale">Conferma eliminazione</h2>
    <p>Questa azione non puo essere annullata.</p>
</div>

<!-- aria-describedby: descrizione aggiuntiva -->
<input type="password" id="pwd"
       aria-describedby="requisiti-pwd">
<p id="requisiti-pwd">La password deve contenere almeno 8 caratteri,
   una lettera maiuscola e un numero.</p>
```

### Live Regions

Le live region informano gli screen reader dei cambiamenti dinamici nel contenuto:

```html
<!-- polite: annuncia quando lo screen reader non e occupato -->
<div aria-live="polite" aria-atomic="true">
    <p>3 nuovi messaggi</p>
</div>

<!-- assertive: interrompe immediatamente per annunciare -->
<div aria-live="assertive" role="alert">
    <p>Errore: la sessione e scaduta. Effettua nuovamente il login.</p>
</div>

<!-- Uso tipico con JavaScript -->
<div id="stato-ricerca" aria-live="polite" aria-busy="false"></div>

<script>
const stato = document.getElementById('stato-ricerca');
stato.setAttribute('aria-busy', 'true');
// Dopo il caricamento
stato.setAttribute('aria-busy', 'false');
stato.textContent = '42 risultati trovati per "HTML5"';
</script>
```

### Stati ARIA

```html
<!-- Elemento nascosto alle tecnologie assistive -->
<div aria-hidden="true">Icona decorativa</div>

<!-- Elemento espandibile -->
<button aria-expanded="false" aria-controls="menu-principale">
    Menu
</button>
<nav id="menu-principale" hidden>
    <!-- contenuto del menu -->
</nav>

<!-- Elemento selezionato in una lista -->
<ul role="listbox">
    <li role="option" aria-selected="true">Opzione 1</li>
    <li role="option" aria-selected="false">Opzione 2</li>
</ul>
```

### Navigazione da Tastiera

L'accessibilita da tastiera e fondamentale per utenti con disabilita motorie e per chi utilizza screen reader:

```html
<!-- tabindex="0": inserisce l'elemento nel flusso di tab naturale -->
<div role="button" tabindex="0" onclick="azione()"
     onkeydown="if(event.key==='Enter'||event.key===' ') azione()">
    Pulsante Personalizzato
</div>

<!-- tabindex="-1": focusabile programmaticamente ma non via tab -->
<h2 id="sezione-risultati" tabindex="-1">Risultati</h2>

<script>
// Focus management dopo navigazione dinamica
document.getElementById('sezione-risultati').focus();
</script>
```

La gestione del focus richiede attenzione in diversi scenari: apertura di modali (il focus deve spostarsi dentro la modale e restarci), chiusura di modali (il focus deve tornare all'elemento attivante), aggiornamento di contenuti dinamici (il focus deve spostarsi sul nuovo contenuto quando rilevante).

### Testing con Screen Reader

Per garantire un'accessibilita efficace, e necessario testare con gli screen reader principali:
- **NVDA** (gratuito, Windows) — il piu diffuso tra gli utenti Windows
- **JAWS** (commerciale, Windows) — standard in ambienti professionali
- **VoiceOver** (integrato, macOS/iOS) — attivabile con Cmd+F5 su Mac
- **TalkBack** (integrato, Android) — per il testing su dispositivi mobili

Il testing dovrebbe verificare: la lettura corretta di tutti i contenuti, la navigazione logica tramite heading e landmark, l'annuncio corretto degli stati interattivi, e la comprensibilita dei messaggi di errore.

### Conformita WCAG 2.1

Le Web Content Accessibility Guidelines definiscono tre livelli di conformita:

**Livello A** (minimo): requisiti essenziali che devono essere soddisfatti. Include testo alternativo per immagini, navigazione da tastiera, contenuto non dipendente esclusivamente dal colore, assenza di contenuto lampeggiante pericoloso.

**Livello AA** (raccomandato): il livello target per la maggior parte dei siti web e richiesto da molte legislazioni. Include rapporto di contrasto minimo 4.5:1 per testo normale e 3:1 per testo grande, ridimensionamento del testo fino al 200% senza perdita di funzionalita, sottotitoli per contenuti multimediali in diretta.

**Livello AAA** (ottimale): il livello piu alto, non sempre raggiungibile per tutti i contenuti. Include rapporto di contrasto 7:1, lingua dei segni per contenuti audio, spiegazioni per abbreviazioni e contenuti complessi.

### Pattern di Accessibilita Comuni

**Finestra modale accessibile:**

```html
<div role="dialog" aria-modal="true" aria-labelledby="titolo-modale"
     tabindex="-1" id="modale">
    <h2 id="titolo-modale">Titolo della Modale</h2>
    <div class="contenuto-modale">
        <p>Contenuto della modale.</p>
    </div>
    <button onclick="chiudiModale()">Chiudi</button>
</div>

<script>
function apriModale() {
    const modale = document.getElementById('modale');
    modale.hidden = false;
    modale.focus();
    // Implementare focus trap
    document.addEventListener('keydown', gestisciFocusTrap);
}

function gestisciFocusTrap(evento) {
    if (evento.key === 'Escape') chiudiModale();
    if (evento.key === 'Tab') {
        // Limitare il focus agli elementi dentro la modale
        const focusabili = modale.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const primo = focusabili[0];
        const ultimo = focusabili[focusabili.length - 1];

        if (evento.shiftKey && document.activeElement === primo) {
            evento.preventDefault();
            ultimo.focus();
        } else if (!evento.shiftKey && document.activeElement === ultimo) {
            evento.preventDefault();
            primo.focus();
        }
    }
}
</script>
```

**Interfaccia a tab accessibile:**

```html
<div role="tablist" aria-label="Sezioni informative">
    <button role="tab" id="tab-1" aria-selected="true"
            aria-controls="panel-1" tabindex="0">Generale</button>
    <button role="tab" id="tab-2" aria-selected="false"
            aria-controls="panel-2" tabindex="-1">Dettagli</button>
    <button role="tab" id="tab-3" aria-selected="false"
            aria-controls="panel-3" tabindex="-1">Recensioni</button>
</div>

<div role="tabpanel" id="panel-1" aria-labelledby="tab-1" tabindex="0">
    <p>Contenuto generale.</p>
</div>
<div role="tabpanel" id="panel-2" aria-labelledby="tab-2"
     tabindex="0" hidden>
    <p>Contenuto dettagliato.</p>
</div>
<div role="tabpanel" id="panel-3" aria-labelledby="tab-3"
     tabindex="0" hidden>
    <p>Recensioni degli utenti.</p>
</div>
```

La navigazione tra tab deve utilizzare le frecce sinistra/destra (non Tab), con Tab che sposta il focus dal tablist al contenuto del pannello attivo.

### Attributi ARIA Avanzati

Oltre agli attributi fondamentali, ARIA offre attributi specializzati per scenari complessi:

**`aria-current`** indica l'elemento corrente all'interno di un set. I valori possibili sono `page` (pagina corrente nella navigazione), `step` (passo corrente in un processo), `location` (posizione corrente in un percorso), `date` (data corrente in un calendario), `time` (ora corrente) e `true` (generico):

```html
<nav aria-label="Navigazione principale">
    <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/prodotti" aria-current="page">Prodotti</a></li>
        <li><a href="/contatti">Contatti</a></li>
    </ul>
</nav>

<nav aria-label="Procedura di checkout">
    <ol>
        <li><a href="/carrello">Carrello</a></li>
        <li><a href="/spedizione" aria-current="step">Spedizione</a></li>
        <li>Pagamento</li>
        <li>Conferma</li>
    </ol>
</nav>
```

**`aria-roledescription`** personalizza la descrizione del ruolo annunciata dallo screen reader. Deve essere usato con estrema cautela e solo quando il ruolo standard non descrive adeguatamente il componente:

```html
<div role="region" aria-roledescription="presentazione a diapositive"
     aria-label="Tour del prodotto">
    <div role="group" aria-roledescription="diapositiva"
         aria-label="Diapositiva 1 di 5">
        <img src="slide-1.jpg" alt="Panoramica funzionalita">
    </div>
</div>
```

**`aria-keyshortcuts`** dichiara le scorciatoie da tastiera associate a un elemento, permettendo alle tecnologie assistive di annunciarle all'utente:

```html
<button aria-keyshortcuts="Control+S" onclick="salva()">
    Salva (Ctrl+S)
</button>

<button aria-keyshortcuts="Alt+N" onclick="nuovo()">
    Nuovo documento (Alt+N)
</button>
```

**`aria-errormessage`** punta all'elemento che contiene il messaggio di errore per un campo invalido, complementando `aria-invalid`:

```html
<label for="codice">Codice fiscale</label>
<input type="text" id="codice" name="codice"
       aria-invalid="true"
       aria-errormessage="errore-codice"
       pattern="[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]">
<span id="errore-codice" role="alert" class="errore">
    Il codice fiscale inserito non e valido. Formato: RSSMRA80A01H501U
</span>
```

### Novita WCAG 2.2

WCAG 2.2, pubblicato come W3C Recommendation nell'ottobre 2023 e diventato lo standard di riferimento nel 2024-2025, introduce nove nuovi criteri di successo. I piu rilevanti per lo sviluppo HTML:

**2.4.11 Focus Appearance (AA)** — quando un elemento riceve il focus da tastiera, l'indicatore di focus deve soddisfare requisiti minimi di dimensione e contrasto. L'area dell'indicatore deve essere almeno pari al perimetro dell'elemento con spessore di 2 pixel CSS, e deve avere un rapporto di contrasto di almeno 3:1 tra lo stato con focus e senza focus:

```css
/* Indicatore di focus conforme a WCAG 2.2 */
:focus-visible {
    outline: 3px solid #2563eb;
    outline-offset: 2px;
    /* Contrasto >= 3:1 rispetto allo sfondo adiacente */
}

/* Rimuovere l'outline solo per click, mantenerlo per tastiera */
:focus:not(:focus-visible) {
    outline: none;
}
```

**2.4.13 Focus Not Obscured (AA)** — l'elemento con focus non deve essere completamente nascosto da contenuti posizionati dall'autore (header sticky, banner, footer fissi). Se un header sticky copre l'elemento focalizzato, la navigazione da tastiera diventa inutilizzabile:

```css
/* Assicurare che il contenuto focusabile non sia coperto da header sticky */
:target {
    scroll-margin-top: 80px; /* Altezza dell'header sticky */
}

/* Alternativa per focus management */
[tabindex]:focus {
    scroll-margin-top: 80px;
}
```

**2.5.7 Dragging Movements (AA)** — ogni funzionalita che utilizza il trascinamento deve offrire un'alternativa a singolo puntatore senza trascinamento. Questo criterio richiede che le interfacce drag-and-drop forniscano sempre controlli alternativi (pulsanti sposta su/giu, menu contestuale con opzioni di spostamento).

**2.5.8 Target Size (Minimum) (AA)** — i target interattivi devono avere una dimensione minima di 24x24 pixel CSS, oppure devono avere spaziatura sufficiente rispetto ai target adiacenti. Eccezioni per link inline nel testo e per target la cui dimensione e determinata dallo user agent.

**Accordion accessibile:**

```html
<div class="accordion">
    <h3>
        <button aria-expanded="false" aria-controls="contenuto-1"
                id="accordion-1">
            Domanda frequente 1
        </button>
    </h3>
    <div id="contenuto-1" role="region" aria-labelledby="accordion-1" hidden>
        <p>Risposta alla domanda 1.</p>
    </div>
</div>
```

---

## Sicurezza Documento

### Content Security Policy (CSP)

La CSP e un meccanismo di difesa contro attacchi XSS (Cross-Site Scripting) e data injection, che specifica quali origini di contenuto il browser deve considerare attendibili:

```html
<!-- Tramite meta tag (limitato rispetto all'header HTTP) -->
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self';
               script-src 'self' https://cdn.attendibile.com;
               style-src 'self' 'unsafe-inline';
               img-src 'self' data: https:;
               font-src 'self' https://fonts.gstatic.com;
               connect-src 'self' https://api.esempio.com;
               frame-ancestors 'none';
               base-uri 'self';
               form-action 'self'">
```

Le direttive principali:
- **`default-src`**: fallback per tutte le categorie non specificate.
- **`script-src`**: origini consentite per JavaScript. Evitare `'unsafe-inline'` e `'unsafe-eval'`; preferire nonce o hash.
- **`style-src`**: origini consentite per CSS.
- **`img-src`**: origini per immagini.
- **`connect-src`**: origini per connessioni (fetch, XHR, WebSocket).
- **`frame-ancestors`**: chi puo incorporare la pagina in un frame (sostituisce X-Frame-Options).

Per ambienti di produzione, l'header HTTP e preferibile al meta tag perche supporta tutte le direttive e non puo essere rimosso da script malevoli.

### Subresource Integrity (SRI)

SRI verifica che le risorse caricate da CDN di terze parti non siano state manomesse, confrontando un hash crittografico:

```html
<script src="https://cdn.esempio.com/libreria.js"
        integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
        crossorigin="anonymous"></script>

<link rel="stylesheet" href="https://cdn.esempio.com/stile.css"
      integrity="sha256-abc123def456..."
      crossorigin="anonymous">
```

Se l'hash non corrisponde, il browser rifiuta di eseguire la risorsa. L'attributo `crossorigin="anonymous"` e necessario per le richieste cross-origin.

### Sandbox per Iframe

L'attributo `sandbox` limita le capacita del contenuto caricato in un iframe, applicando il principio del minimo privilegio:

```html
<!-- Sandbox restrittivo: tutto disabilitato -->
<iframe src="contenuto-esterno.html" sandbox></iframe>

<!-- Sandbox con permessi selettivi -->
<iframe src="widget.html"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        loading="lazy"
        title="Widget di feedback">
</iframe>
```

I valori di sandbox includono:
- `allow-scripts`: permette l'esecuzione di JavaScript.
- `allow-same-origin`: tratta il contenuto come proveniente dalla stessa origine.
- `allow-forms`: permette l'invio di form.
- `allow-popups`: permette l'apertura di nuove finestre.
- `allow-modals`: permette alert, confirm e prompt.

Attenzione: combinare `allow-scripts` e `allow-same-origin` riduce significativamente la protezione, poiche lo script potrebbe rimuovere l'attributo sandbox.

### Header e Attributi di Sicurezza

```html
<!-- Prevenire il clickjacking (preferire frame-ancestors in CSP) -->
<meta http-equiv="X-Frame-Options" content="DENY">

<!-- Controllare il referrer inviato nelle richieste -->
<meta name="referrer" content="strict-origin-when-cross-origin">

<!-- Link esterni sicuri -->
<a href="https://esterno.com" target="_blank" rel="noopener noreferrer">
    Sito esterno
</a>
```

**`rel="noopener"`** impedisce alla pagina aperta di accedere a `window.opener`, prevenendo attacchi di reverse tabnapping. **`rel="noreferrer"`** evita l'invio dell'header Referer, proteggendo la privacy dell'utente. Nei browser moderni, `target="_blank"` implica automaticamente `noopener`, ma specificarlo esplicitamente garantisce la compatibilita con browser meno recenti.

**`referrerpolicy`** puo essere applicato a singoli elementi (`<a>`, `<img>`, `<script>`, `<link>`) per un controllo granulare:

```html
<img src="https://analytics.esterno.com/pixel.gif" referrerpolicy="no-referrer">
```

### Sanitizzazione dell'Input

Sebbene la sanitizzazione completa avvenga lato server, HTML5 offre alcune protezioni lato client:

```javascript
// MAI inserire input utente con innerHTML
elemento.innerHTML = inputUtente; // PERICOLOSO — possibile XSS

// Usare textContent per testo semplice
elemento.textContent = inputUtente; // SICURO — nessun parsing HTML

// Per contenuto HTML, utilizzare la Sanitizer API (dove supportata)
// oppure librerie come DOMPurify
const pulito = DOMPurify.sanitize(inputUtente, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p'],
    ALLOWED_ATTR: ['href', 'title']
});
elemento.innerHTML = pulito;

// L'attributo pattern non e una misura di sicurezza
// ma solo UX — la validazione DEVE avvenire anche lato server
```

L'attributo `inputmode` puo migliorare l'esperienza utente sui dispositivi mobili senza implicazioni di sicurezza:

```html
<input type="text" inputmode="numeric" pattern="[0-9]*"
       placeholder="Codice di verifica">
```

### CSP Avanzata: Nonce e Hash

La strategia nonce-based e il metodo raccomandato per consentire script inline mantenendo una CSP rigorosa. Un nonce (Number used Once) e un valore casuale crittograficamente sicuro, generato dal server per ogni risposta HTTP:

```html
<!-- Il server genera un nonce unico per ogni richiesta -->
<meta http-equiv="Content-Security-Policy"
      content="script-src 'nonce-a1b2c3d4e5f6' 'strict-dynamic';
               style-src 'self' 'nonce-a1b2c3d4e5f6';
               object-src 'none';
               base-uri 'self'">

<!-- Solo gli script con il nonce corretto vengono eseguiti -->
<script nonce="a1b2c3d4e5f6">
    // Questo script viene eseguito
    document.getElementById('app').textContent = 'Caricato';
</script>

<!-- Senza nonce, lo script viene bloccato dalla CSP -->
<script>
    // BLOCCATO — nessun nonce corrispondente
    alert('XSS tentato');
</script>
```

La direttiva `'strict-dynamic'` permette agli script autorizzati (con nonce valido) di caricare dinamicamente altri script senza richiedere nonce aggiuntivi, semplificando l'integrazione con bundler e librerie che iniettano script a runtime.

In alternativa ai nonce, si possono utilizzare hash degli script inline. Il browser calcola l'hash del contenuto dello script e lo confronta con quello dichiarato nella CSP:

```html
<meta http-equiv="Content-Security-Policy"
      content="script-src 'sha256-RFWPLDbv2BY+rCkDzsE+0fr8ylGr2R2faWMhq4lfEQc='">

<!-- Solo questo esatto contenuto viene eseguito -->
<script>document.getElementById('app').textContent = 'OK';</script>
```

### Trusted Types API

L'API Trusted Types (supportata in Chromium, in via di adozione in altri browser) elimina le vulnerabilita XSS basate su DOM forzando la sanitizzazione dei valori passati a sink pericolosi come `innerHTML`, `document.write()` e `eval()`:

```html
<meta http-equiv="Content-Security-Policy"
      content="require-trusted-types-for 'script';
               trusted-types default sanitizer">

<script>
// Definire una policy di sanitizzazione
if (window.trustedTypes) {
    const policy = trustedTypes.createPolicy('default', {
        createHTML: (input) => {
            // Sanitizzare l'input — rimuovere tag pericolosi
            const div = document.createElement('div');
            div.textContent = input;
            return div.innerHTML;
        },
        createScript: (input) => input,
        createScriptURL: (input) => {
            const url = new URL(input, document.baseURI);
            if (url.origin === location.origin) return input;
            throw new TypeError('URL non attendibile: ' + input);
        }
    });
}

// Senza Trusted Types abilitato:
elemento.innerHTML = inputUtente; // OK (ma pericoloso)

// Con Trusted Types abilitato:
elemento.innerHTML = inputUtente; // TypeError! Non e un TrustedHTML
elemento.innerHTML = policy.createHTML(inputUtente); // OK, sanitizzato
```

### Sanitizer API

La Sanitizer API (in fase di standardizzazione, disponibile dietro flag in alcuni browser) offre una primitiva di sanitizzazione HTML nativa e sicura, eliminando la necessita di librerie esterne come DOMPurify per molti casi d'uso:

```javascript
// Verificare il supporto
if ('Sanitizer' in window) {
    const sanitizer = new Sanitizer({
        allowElements: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'li'],
        allowAttributes: {
            'href': ['a'],
            'title': ['*']
        },
        blockElements: ['script', 'style', 'iframe'],
        dropAttributes: {
            'onclick': ['*'],
            'onerror': ['*'],
            'onload': ['*']
        }
    });

    // Sanitizzare e inserire in un solo passaggio
    elemento.setHTML(inputUtente, { sanitizer });
}
```

Il vantaggio rispetto a DOMPurify e che la Sanitizer API opera a livello di parser del browser, non tramite espressioni regolari, garantendo una sanitizzazione piu robusta e resistente a bypass basati su parsing differentials.

---

## Dialog Element e Popover API

### L'Elemento Dialog in Profondita

L'elemento `<dialog>` fornisce una finestra di dialogo nativa con supporto integrato per la gestione del focus, la navigazione da tastiera e l'interazione con le tecnologie assistive. Rappresenta un'evoluzione fondamentale rispetto ai modale costruiti con `<div>` e JavaScript personalizzato.

#### Modalita Modale e Non-Modale

`<dialog>` supporta due modalita di apertura distinte con comportamenti radicalmente diversi:

```html
<dialog id="modale-conferma">
    <h2>Conferma eliminazione</h2>
    <p>Questa operazione eliminera definitivamente l'elemento.
       L'azione non puo essere annullata.</p>
    <form method="dialog">
        <button value="annulla">Annulla</button>
        <button value="conferma" autofocus>Conferma</button>
    </form>
</dialog>

<dialog id="pannello-info">
    <h2>Informazioni aggiuntive</h2>
    <p>Dettagli supplementari sul prodotto selezionato.</p>
    <button onclick="this.closest('dialog').close()">Chiudi</button>
</dialog>

<script>
const modaleConferma = document.getElementById('modale-conferma');
const pannelloInfo = document.getElementById('pannello-info');

// Modale: rende il resto della pagina inerte
modaleConferma.showModal();

// Non-modale: la pagina resta interattiva
pannelloInfo.show();
</script>
```

**`showModal()`** rende il dialog modale: il focus viene intrappolato al suo interno, il contenuto sottostante diventa inerte (non cliccabile e non focusabile), il tasto Escape chiude automaticamente il dialog e viene mostrato un `::backdrop` semi-trasparente.

**`show()`** apre il dialog in modalita non modale: il resto della pagina rimane interattivo, non c'e focus trap, il tasto Escape non chiude il dialog e non viene mostrato il backdrop.

#### Valore di Ritorno e form method="dialog"

Un `<form method="dialog">` all'interno del `<dialog>` chiude automaticamente il dialog quando viene inviato. Il valore del pulsante di submit viene salvato nella proprieta `returnValue` del dialog:

```javascript
const dialog = document.getElementById('modale-conferma');

dialog.addEventListener('close', () => {
    if (dialog.returnValue === 'conferma') {
        eseguiEliminazione();
    } else {
        console.log('Operazione annullata');
    }
});
```

#### Styling del Backdrop

Il pseudo-elemento `::backdrop` permette di stilizzare lo sfondo oscurato dietro un dialog modale:

```css
dialog::backdrop {
    background-color: oklch(0% 0 0 / 0.6);
    backdrop-filter: blur(4px);
}

/* Animazione di apertura */
dialog[open] {
    animation: dialog-comparsa 300ms ease-out;
}

@keyframes dialog-comparsa {
    from {
        opacity: 0;
        transform: translateY(-20px) scale(0.95);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}
```

#### Chiusura con Light Dismiss

Per impostazione predefinita, un click sul backdrop non chiude il dialog modale. Per implementare il "light dismiss" (chiusura cliccando fuori), si sfrutta il fatto che il click sul backdrop viene registrato come click sul dialog stesso nelle coordinate esterne:

```javascript
dialog.addEventListener('click', (evento) => {
    const rect = dialog.getBoundingClientRect();
    const fuoriContenuto =
        evento.clientX < rect.left ||
        evento.clientX > rect.right ||
        evento.clientY < rect.top ||
        evento.clientY > rect.bottom;

    if (fuoriContenuto) {
        dialog.close('dismiss');
    }
});
```

### La Popover API

La Popover API (Baseline dal 2024) fornisce un meccanismo nativo per creare contenuti flottanti come tooltip, menu, notifiche toast e pannelli informativi. A differenza di `<dialog>`, i popover non rendono la pagina inerte e non hanno semantica intrinseca — richiedono l'aggiunta esplicita di ruoli ARIA appropriati.

#### Popover Dichiarativo

La versione dichiarativa (solo HTML, senza JavaScript) utilizza tre attributi:

```html
<!-- Popover auto: si chiude con click esterno o Escape -->
<button popovertarget="menu-azioni">Azioni</button>

<div id="menu-azioni" popover>
    <ul role="menu">
        <li role="menuitem"><button>Modifica</button></li>
        <li role="menuitem"><button>Duplica</button></li>
        <li role="menuitem"><button>Elimina</button></li>
    </ul>
</div>

<!-- Popover manual: deve essere chiuso esplicitamente -->
<button popovertarget="notifica-toast">Mostra notifica</button>

<div id="notifica-toast" popover="manual" role="status">
    <p>Elemento salvato con successo.</p>
</div>

<!-- Controllo esplicito dell'azione: show, hide, toggle -->
<button popovertarget="pannello" popovertargetaction="show">Apri</button>
<button popovertarget="pannello" popovertargetaction="hide">Chiudi</button>

<div id="pannello" popover>
    <p>Contenuto del pannello.</p>
</div>
```

**`popover` o `popover="auto"`** — comportamento automatico: il popover si chiude quando l'utente clicca fuori da esso, preme Escape o apre un altro popover auto. Un solo popover auto puo essere visibile contemporaneamente (a meno che non siano annidati).

**`popover="manual"`** — il popover non si chiude automaticamente; richiede un'azione esplicita (pulsante di chiusura o JavaScript). Piu popover manual possono essere visibili simultaneamente.

#### Popover Programmatico

```javascript
const popover = document.getElementById('pannello');

popover.showPopover();    // Apre il popover
popover.hidePopover();    // Chiude il popover
popover.togglePopover();  // Alterna aperto/chiuso

// Eventi
popover.addEventListener('beforetoggle', (evento) => {
    console.log(`Stato precedente: ${evento.oldState}`); // 'closed' o 'open'
    console.log(`Nuovo stato: ${evento.newState}`);
    // evento.preventDefault() puo bloccare l'apertura
});

popover.addEventListener('toggle', (evento) => {
    if (evento.newState === 'open') {
        // Popover appena aperto — caricare dati, posizionare, ecc.
    }
});
```

#### CSS Anchor Positioning con Popover

Il CSS Anchor Positioning (Baseline dal 2025) permette di posizionare i popover relativamente al loro elemento attivante senza JavaScript:

```html
<button id="btn-info" popovertarget="tooltip-info"
        style="anchor-name: --btn-info">
    Informazioni
</button>

<div id="tooltip-info" popover role="tooltip"
     style="position-anchor: --btn-info">
    <p>Dettagli aggiuntivi sul campo selezionato.</p>
</div>

<style>
#tooltip-info {
    margin: 0;
    inset: auto;
    /* Posiziona sotto il pulsante, centrato */
    top: anchor(bottom);
    justify-self: anchor-center;
    /* Fallback se esce dal viewport */
    position-try-fallbacks: flip-block, flip-inline;
}
</style>
```

#### Dialog vs Popover: Quando Usare Cosa

| Criterio | `<dialog>` modale | `<dialog>` non-modale | Popover |
|---|---|---|---|
| Pagina inerte | Si | No | No |
| Focus trap | Si | No | No |
| Escape chiude | Si | No | Si (auto) |
| Backdrop | Si (`::backdrop`) | No | No |
| Semantica intrinseca | `role="dialog"` | `role="dialog"` | Nessuna |
| Click esterno chiude | Solo con JS | No | Si (auto) |
| Uso tipico | Conferme, form critici | Pannelli laterali | Tooltip, menu, toast |

---

## Web Components

### Panoramica

I Web Components sono un insieme di tecnologie native del browser che permettono di creare elementi HTML personalizzati, riutilizzabili e incapsulati. Comprendono tre specifiche principali: Custom Elements, Shadow DOM e HTML Templates con Slots. A differenza di framework come React o Vue, i Web Components operano a livello di piattaforma web e sono interoperabili con qualsiasi framework o con nessuno.

### Custom Elements

I Custom Elements permettono di definire nuovi tag HTML con logica e comportamento personalizzati. Il nome deve contenere un trattino per distinguerli dagli elementi nativi:

```javascript
class ContatoreClic extends HTMLElement {
    #conteggio = 0;

    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        // Invocato quando l'elemento viene inserito nel DOM
        this.render();
    }

    disconnectedCallback() {
        // Invocato quando l'elemento viene rimosso dal DOM
        console.log('Contatore rimosso');
    }

    attributeChangedCallback(nome, vecchio, nuovo) {
        // Invocato quando un attributo osservato cambia
        if (nome === 'iniziale') {
            this.#conteggio = parseInt(nuovo) || 0;
            this.render();
        }
    }

    static get observedAttributes() {
        return ['iniziale'];
    }

    adoptedCallback() {
        // Invocato quando l'elemento viene spostato in un nuovo documento
    }

    incrementa() {
        this.#conteggio++;
        this.render();
        this.dispatchEvent(new CustomEvent('conteggio-cambiato', {
            detail: { conteggio: this.#conteggio },
            bubbles: true,
            composed: true  // Attraversa il confine del Shadow DOM
        }));
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: inline-block;
                    font-family: system-ui;
                }
                button {
                    padding: 0.5rem 1rem;
                    cursor: pointer;
                    border: 2px solid currentColor;
                    border-radius: 4px;
                    background: transparent;
                    color: inherit;
                    font-size: 1rem;
                }
                span { margin-left: 0.5rem; font-weight: bold; }
            </style>
            <button>Incrementa</button>
            <span>${this.#conteggio}</span>
        `;
        this.shadowRoot.querySelector('button')
            .addEventListener('click', () => this.incrementa());
    }
}

// Registrazione del custom element
customElements.define('contatore-clic', ContatoreClic);
```

```html
<!-- Uso nel markup -->
<contatore-clic iniziale="5"></contatore-clic>

<script>
// Attendere che il custom element sia definito
customElements.whenDefined('contatore-clic').then(() => {
    console.log('contatore-clic e pronto');
});
</script>
```

Il ciclo di vita comprende quattro callback: `connectedCallback()` (inserimento nel DOM), `disconnectedCallback()` (rimozione dal DOM), `attributeChangedCallback()` (modifica di attributi osservati) e `adoptedCallback()` (spostamento tra documenti, ad esempio in un iframe).

### Shadow DOM

Lo Shadow DOM crea un albero DOM incapsulato, isolato dal documento principale. Gli stili definiti all'interno del Shadow DOM non fuoriescono, e gli stili esterni non penetrano, eliminando i conflitti CSS:

```javascript
class CardProdotto extends HTMLElement {
    constructor() {
        super();
        // mode: 'open' — il shadowRoot e accessibile dall'esterno
        // mode: 'closed' — il shadowRoot non e accessibile
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* :host seleziona l'elemento custom stesso */
                :host {
                    display: block;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    overflow: hidden;
                }

                /* :host con selettore contestuale */
                :host(.evidenziato) {
                    border-color: #3b82f6;
                    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
                }

                /* :host-context controlla il contesto genitore */
                :host-context(.tema-scuro) {
                    background-color: #1f2937;
                    color: #f9fafb;
                }

                h3 { margin: 0 0 0.5rem; }
                .prezzo { color: #059669; font-weight: bold; }
            </style>
            <div class="card-body">
                <h3><slot name="titolo">Prodotto</slot></h3>
                <p><slot name="descrizione">Descrizione non disponibile</slot></p>
                <p class="prezzo"><slot name="prezzo"></slot></p>
                <slot></slot> <!-- Slot di default -->
            </div>
        `;
    }
}

customElements.define('card-prodotto', CardProdotto);
```

#### Stili dall'Esterno con CSS Parts

`::part()` permette al CSS esterno di stilizzare parti specifiche del Shadow DOM, espressamente designate dal componente con l'attributo `part`:

```javascript
// Nel componente
shadow.innerHTML = `
    <button part="pulsante">
        <span part="icona"><slot name="icona"></slot></span>
        <span part="testo"><slot></slot></span>
    </button>
`;
```

```css
/* CSS esterno — stilizza le parti esposte */
card-prodotto::part(pulsante) {
    background-color: #3b82f6;
    color: white;
}

card-prodotto::part(pulsante):hover {
    background-color: #2563eb;
}
```

### Template e Slots

L'elemento `<template>` contiene markup che non viene renderizzato fino alla clonazione programmatica. Gli `<slot>` definiscono punti di inserimento nel Shadow DOM dove il consumatore del componente puo inserire il proprio contenuto:

```html
<template id="template-allarme">
    <style>
        .allarme {
            padding: 1rem;
            border-radius: 4px;
            border-left: 4px solid;
        }
        .allarme[data-tipo="errore"] {
            background: #fef2f2;
            border-color: #ef4444;
        }
        .allarme[data-tipo="successo"] {
            background: #f0fdf4;
            border-color: #22c55e;
        }
    </style>
    <div class="allarme" role="alert">
        <strong><slot name="titolo">Attenzione</slot></strong>
        <p><slot>Messaggio non specificato.</slot></p>
    </div>
</template>

<!-- Uso con slot nominati -->
<allarme-componente tipo="errore">
    <span slot="titolo">Errore critico</span>
    La connessione al database e fallita. Riprovare tra 30 secondi.
</allarme-componente>

<!-- Uso con slot di default -->
<allarme-componente tipo="successo">
    Operazione completata con successo.
</allarme-componente>
```

### Declarative Shadow DOM

Il Declarative Shadow DOM (Baseline dal 2024) permette di definire Shadow DOM direttamente nel markup HTML, senza JavaScript, abilitando il server-side rendering dei Web Components:

```html
<card-prodotto>
    <template shadowrootmode="open">
        <style>
            :host { display: block; padding: 1rem; }
            ::slotted(h3) { color: #1e40af; }
        </style>
        <slot name="titolo"></slot>
        <slot></slot>
    </template>
    <h3 slot="titolo">Laptop Pro</h3>
    <p>Computer portatile ad alte prestazioni.</p>
</card-prodotto>
```

L'attributo `shadowrootmode` accetta `"open"` o `"closed"`, con la stessa semantica di `attachShadow({ mode })`. Il template viene processato dal parser HTML e il suo contenuto diventa il Shadow DOM dell'elemento genitore.

### Form-Associated Custom Elements

I custom elements possono partecipare ai form HTML nativi implementando l'interfaccia `ElementInternals`:

```javascript
class InputPersonalizzato extends HTMLElement {
    static formAssociated = true;

    #internals;

    constructor() {
        super();
        this.#internals = this.attachInternals();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.shadowRoot.innerHTML = `
            <input type="text" part="input">
        `;
        const input = this.shadowRoot.querySelector('input');
        input.addEventListener('input', () => {
            this.#internals.setFormValue(input.value);
            // Validazione
            if (input.value.length < 3) {
                this.#internals.setValidity(
                    { tooShort: true },
                    'Minimo 3 caratteri',
                    input
                );
            } else {
                this.#internals.setValidity({});
            }
        });
    }

    // Metodi del ciclo di vita del form
    formResetCallback() {
        this.shadowRoot.querySelector('input').value = '';
        this.#internals.setFormValue('');
    }
}

customElements.define('input-personalizzato', InputPersonalizzato);
```

---

## Meta Tags, SEO e Open Graph

### Meta Tags Essenziali

I meta tag nel `<head>` del documento forniscono metadata cruciali per il browser, i motori di ricerca e le piattaforme social. Una configurazione completa e accurata influenza direttamente la visibilita del sito nei risultati di ricerca e la qualita delle anteprime condivise sui social media.

```html
<head>
    <!-- Codifica e viewport (indispensabili) -->
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- SEO fondamentale -->
    <title>Titolo della Pagina — Nome del Sito</title>
    <meta name="description" content="Descrizione concisa della pagina,
          150-160 caratteri massimo. Deve contenere le keyword principali
          e invitare al click nei risultati di ricerca.">

    <!-- Controllo dei crawler -->
    <meta name="robots" content="index, follow">
    <!-- Per pagine che non devono essere indicizzate -->
    <!-- <meta name="robots" content="noindex, nofollow"> -->

    <!-- URL canonico — previene contenuto duplicato -->
    <link rel="canonical" href="https://www.esempio.com/pagina-corrente">

    <!-- Lingua alternativa per siti multilingua -->
    <link rel="alternate" hreflang="en"
          href="https://www.esempio.com/en/current-page">
    <link rel="alternate" hreflang="it"
          href="https://www.esempio.com/it/pagina-corrente">
    <link rel="alternate" hreflang="x-default"
          href="https://www.esempio.com/en/current-page">

    <!-- Favicon e icone -->
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="icon" href="/favicon.ico" sizes="32x32">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <link rel="manifest" href="/site.webmanifest">

    <!-- Tema colore per la barra del browser -->
    <meta name="theme-color" content="#1e40af"
          media="(prefers-color-scheme: light)">
    <meta name="theme-color" content="#1e3a5f"
          media="(prefers-color-scheme: dark)">
</head>
```

### Viewport Meta Tag in Dettaglio

Il meta tag viewport controlla come il browser ridimensiona la pagina sui dispositivi mobili. I parametri principali:

- **`width=device-width`** — la larghezza del viewport corrisponde alla larghezza del dispositivo.
- **`initial-scale=1.0`** — lo zoom iniziale e al 100%.
- **`maximum-scale`** — lo zoom massimo consentito. Evitare `maximum-scale=1.0` o `user-scalable=no` perche impediscono lo zoom accessibile (violazione WCAG 1.4.4).
- **`interactive-widget=resizes-visual`** — (moderno) controlla il comportamento del viewport quando la tastiera virtuale appare su mobile. I valori sono `resizes-visual` (la tastiera ridimensiona solo il viewport visuale), `resizes-content` (ridimensiona il viewport del layout) e `overlays-content` (la tastiera si sovrappone senza ridimensionare).

### Open Graph Protocol

Il protocollo Open Graph, sviluppato originariamente da Facebook, standardizza i metadata per le anteprime dei link condivisi sui social media. Le proprieta OG sono supportate da Facebook, LinkedIn, Discord, Slack, Telegram e la maggior parte delle piattaforme social:

```html
<!-- Open Graph essenziali -->
<meta property="og:title" content="Guida Completa a HTML5">
<meta property="og:description" content="Tutto quello che serve sapere
      su HTML5: semantica, form, accessibilita e API moderne.">
<meta property="og:image" content="https://www.esempio.com/img/og-html5.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Copertina della guida HTML5">
<meta property="og:url" content="https://www.esempio.com/guida-html5">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Studio Lavoro Academy">
<meta property="og:locale" content="it_IT">

<!-- Specifiche per articolo -->
<meta property="article:published_time" content="2025-11-20T10:00:00+01:00">
<meta property="article:modified_time" content="2025-12-15T14:30:00+01:00">
<meta property="article:author" content="https://www.esempio.com/autore/marco">
<meta property="article:section" content="Sviluppo Web">
<meta property="article:tag" content="HTML5">
<meta property="article:tag" content="Semantica">

<!-- Twitter Card (complementare a OG) -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@esempio_dev">
<meta name="twitter:creator" content="@marco_dev">
<!-- Twitter usa og:title, og:description e og:image come fallback -->
```

Per le immagini OG, la dimensione raccomandata e 1200x630 pixel (rapporto ~1.91:1). L'immagine deve essere accessibile via HTTPS e pesare meno di 5 MB. E fondamentale che `og:url` corrisponda al `<link rel="canonical">` per evitare discrepanze nei conteggi di condivisione.

### Dati Strutturati con JSON-LD

JSON-LD (JavaScript Object Notation for Linked Data) e il formato raccomandato da Google per i dati strutturati. A differenza dei microdata (attributi inline), JSON-LD separa i dati strutturati dal markup visuale, semplificando la manutenzione:

```html
<!-- Organizzazione -->
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Studio Lavoro Academy",
    "url": "https://www.esempio.com",
    "logo": "https://www.esempio.com/img/logo.png",
    "contactPoint": {
        "@type": "ContactPoint",
        "telephone": "+39-02-12345678",
        "contactType": "customer service",
        "availableLanguage": ["Italian", "English"]
    },
    "sameAs": [
        "https://www.linkedin.com/company/esempio",
        "https://github.com/esempio"
    ]
}
</script>

<!-- Articolo con breadcrumb -->
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Guida Completa a HTML5",
    "author": {
        "@type": "Person",
        "name": "Marco Rossi"
    },
    "datePublished": "2025-11-20",
    "dateModified": "2025-12-15",
    "image": "https://www.esempio.com/img/og-html5.jpg",
    "publisher": {
        "@type": "Organization",
        "name": "Studio Lavoro Academy",
        "logo": {
            "@type": "ImageObject",
            "url": "https://www.esempio.com/img/logo.png"
        }
    }
}
</script>

<!-- FAQ — abilita il rich snippet FAQ nei risultati di ricerca -->
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {
            "@type": "Question",
            "name": "Qual e la differenza tra article e section?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "article rappresenta un contenuto autonomo e redistribuibile, mentre section raggruppa contenuti tematicamente correlati all'interno di un contesto piu ampio."
            }
        },
        {
            "@type": "Question",
            "name": "Quando usare dialog vs popover?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Usare dialog per interazioni modali che richiedono una risposta dell'utente prima di continuare. Usare popover per contenuti flottanti non modali come tooltip, menu e notifiche."
            }
        }
    ]
}
</script>
```

I tipi di schema piu comuni includono: `Article`, `Product`, `FAQPage`, `HowTo`, `BreadcrumbList`, `Event`, `LocalBusiness`, `Person`, `Organization`, `Recipe` e `VideoObject`. Google fornisce il Rich Results Test (`search.google.com/test/rich-results`) per validare i dati strutturati e verificare l'idoneita ai rich snippet.

---

## SVG in HTML

### SVG Inline vs Esterno

SVG (Scalable Vector Graphics) puo essere incorporato in HTML in diversi modi, ciascuno con vantaggi specifici:

**SVG inline** — inserito direttamente nel markup HTML. Offre il massimo controllo: lo SVG fa parte del DOM, puo essere stilizzato con CSS, manipolato con JavaScript e reso accessibile con ARIA:

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
     width="24" height="24" fill="none" stroke="currentColor"
     stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
     role="img" aria-labelledby="icona-check-titolo">
    <title id="icona-check-titolo">Operazione completata</title>
    <polyline points="20 6 9 17 4 12"/>
</svg>
```

**SVG come immagine** — tramite `<img>`, `background-image` CSS o `<picture>`. Non e manipolabile con CSS/JS, ma e cachabile indipendentemente e non appesantisce il DOM:

```html
<img src="icona.svg" alt="Descrizione dell'icona" width="24" height="24">
```

**SVG tramite `<use>`** — referenzia un simbolo SVG definito altrove (sprite o definizione nascosta). Buon compromesso tra flessibilita e performance:

```html
<!-- Definizione dello sprite (nascosto) -->
<svg style="display: none" aria-hidden="true">
    <defs>
        <symbol id="icona-freccia" viewBox="0 0 24 24">
            <path d="M5 12h14M12 5l7 7-7 7"/>
        </symbol>
        <symbol id="icona-utente" viewBox="0 0 24 24">
            <circle cx="12" cy="8" r="4"/>
            <path d="M20 21a8 8 0 1 0-16 0"/>
        </symbol>
    </defs>
</svg>

<!-- Uso tramite riferimento -->
<svg width="24" height="24" role="img" aria-label="Freccia avanti">
    <use href="#icona-freccia"/>
</svg>
```

### ViewBox e Sistema di Coordinate

L'attributo `viewBox` definisce il sistema di coordinate interno dell'SVG, indipendente dalle dimensioni fisiche di rendering. Il formato e `viewBox="minX minY larghezza altezza"`:

```html
<!-- viewBox 0 0 100 100: il contenuto e mappato in un quadrato 100x100 -->
<!-- width e height controllano la dimensione di rendering -->
<svg viewBox="0 0 100 100" width="200" height="200">
    <!-- Questo cerchio occupa il centro del viewBox -->
    <circle cx="50" cy="50" r="40" fill="#3b82f6"/>
</svg>
```

L'attributo `preserveAspectRatio` controlla come il contenuto SVG viene scalato quando il rapporto d'aspetto del viewBox non corrisponde a quello del contenitore. Il valore predefinito `xMidYMid meet` centra il contenuto e lo scala per adattarsi senza taglio.

### Accessibilita SVG

L'accessibilita degli SVG richiede attenzione specifica a seconda dell'uso:

**SVG decorativo** — icone puramente visive senza informazione aggiuntiva:

```html
<svg aria-hidden="true" focusable="false" width="16" height="16">
    <use href="#icona-decorativa"/>
</svg>
```

**SVG informativo** — trasmette informazioni che devono essere accessibili:

```html
<svg role="img" aria-labelledby="titolo-grafico desc-grafico"
     viewBox="0 0 400 300">
    <title id="titolo-grafico">Distribuzione delle vendite per regione</title>
    <desc id="desc-grafico">Grafico a torta che mostra le vendite 2025:
        Nord 40%, Centro 35%, Sud 25%.</desc>
    <!-- Contenuto grafico -->
</svg>
```

**SVG interattivo** — contiene elementi cliccabili o navigabili da tastiera:

```html
<svg role="group" aria-label="Controlli di navigazione">
    <a href="/precedente" aria-label="Pagina precedente">
        <rect x="0" y="0" width="40" height="40" fill="transparent"/>
        <path d="M25 10 L10 20 L25 30"/>
    </a>
</svg>
```

### Animazioni SVG e Riduzione del Moto

Le animazioni SVG possono essere realizzate tramite CSS, SMIL (nativo SVG) o JavaScript. E obbligatorio rispettare la preferenza dell'utente per il moto ridotto:

```css
/* Animazione SVG con CSS */
.icona-caricamento path {
    animation: rotazione 1s linear infinite;
    transform-origin: center;
}

@keyframes rotazione {
    to { transform: rotate(360deg); }
}

/* Rispettare la preferenza di riduzione del moto (WCAG 2.3.3) */
@media (prefers-reduced-motion: reduce) {
    .icona-caricamento path {
        animation: none;
    }

    /* Alternativa: ridurre senza eliminare */
    svg * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

Le animazioni SVG non devono lampeggiare piu di 3 volte al secondo (WCAG 2.3.1) e quelle che durano piu di 5 secondi devono poter essere messe in pausa dall'utente (WCAG 2.2.2).

### Ottimizzazione degli SVG

I file SVG generati dagli editor grafici (Illustrator, Figma, Inkscape) contengono tipicamente metadati, commenti, attributi ridondanti e precisioni decimali eccessive che ne aumentano significativamente il peso. L'ottimizzazione e un passaggio essenziale prima dell'inclusione nel markup:

- Rimuovere i metadati dell'editor (`<metadata>`, commenti XML, namespace inutilizzati).
- Ridurre la precisione dei numeri decimali (da 6-8 cifre a 1-2, sufficiente per la resa visiva).
- Eliminare attributi con valori predefiniti (ad esempio `fill-opacity="1"` e il default).
- Convertire forme base (`<rect>`, `<circle>`, `<ellipse>`) in `<path>` solo quando produce un risultato piu compatto.
- Unire tracciati contigui con stili identici.

Strumenti come SVGO (usato a riga di comando o come plugin di build) automatizzano queste ottimizzazioni. Un SVG complesso puo ridursi del 40-60% dopo l'ottimizzazione, con un impatto diretto sulla dimensione del documento HTML e sul tempo di parsing del browser.

---

## HTML per Email

### Il Contesto delle Email HTML

Lo sviluppo di email HTML rappresenta un ambiente radicalmente diverso dalla costruzione di pagine web moderne. I client di posta elettronica utilizzano motori di rendering obsoleti e frammentati: Outlook per desktop si basa sul motore di rendering di Microsoft Word (dalla versione 2007), Gmail rimuove e sanifica aggressivamente il DOM, Apple Mail usa WebKit e Yahoo Mail applica il proprio set di restrizioni. Questa frammentazione impone vincoli tecnici significativi.

### Struttura e Layout

Le email HTML devono utilizzare layout basato su tabelle (`<table>`) anziche `<div>` con Flexbox o Grid, che non sono supportati in Outlook e in diversi client webmail:

```html
<!DOCTYPE html>
<html lang="it" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light dark">
    <meta name="supported-color-schemes" content="light dark">
    <title>Oggetto dell'email</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f4;">
    <!-- Tabella contenitore centrata -->
    <table role="presentation" width="100%" cellpadding="0"
           cellspacing="0" border="0">
        <tr>
            <td align="center">
                <!-- Tabella contenuto — larghezza massima 600px -->
                <table role="presentation" width="600" cellpadding="0"
                       cellspacing="0" border="0"
                       style="max-width: 600px; width: 100%;">
                    <tr>
                        <td style="padding: 20px; background-color: #ffffff;
                                   font-family: Arial, Helvetica, sans-serif;
                                   font-size: 16px; line-height: 1.5;
                                   color: #333333;">
                            <h1 style="margin: 0 0 16px; font-size: 24px;
                                       color: #1a1a1a;">
                                Benvenuto
                            </h1>
                            <p style="margin: 0 0 16px;">
                                Contenuto dell'email...
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
```

### Regole Fondamentali per le Email HTML

**CSS inline obbligatorio** — Gmail e molti client rimuovono i tag `<style>` dal `<head>`. Tutti gli stili critici devono essere applicati inline con l'attributo `style`. I blocchi `<style>` nel `<head>` possono servire come enhancement progressivo per i client che li supportano.

**Tabelle con `role="presentation"`** — le tabelle usate per il layout devono avere `role="presentation"` per indicare alle tecnologie assistive che non sono tabelle di dati.

**Font sicuri** — utilizzare font web-safe (Arial, Helvetica, Georgia, Times New Roman, Verdana) come base. I web font (`@font-face`) sono supportati solo da Apple Mail, iOS Mail e pochi altri client. Specificarli sempre come enhancement con un fallback solido.

**Immagini** — specificare sempre `width`, `height` e `alt` sulle immagini. Molti client bloccano le immagini per default; il testo alternativo deve comunicare l'informazione essenziale. Evitare email composte interamente da immagini.

**Larghezza massima 600px** — la larghezza del contenuto non deve superare 600-640 pixel per adattarsi ai pannelli di anteprima dei client desktop.

### Dark Mode nelle Email

Il supporto per il dark mode nelle email varia enormemente tra i client. Alcuni (Apple Mail, Outlook.com) applicano un'inversione automatica dei colori; altri (Gmail) non lo fanno. Per gestire il dark mode dove supportato:

```html
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">

<style>
    /* Solo per client che supportano @media */
    @media (prefers-color-scheme: dark) {
        .sfondo-email {
            background-color: #1a1a2e !important;
        }
        .testo-email {
            color: #e0e0e0 !important;
        }
    }
</style>
```

### Accessibilita nelle Email

L'European Accessibility Act (EAA), entrato in vigore il 28 giugno 2025, impone requisiti di accessibilita che si estendono anche alle comunicazioni digitali. Le pratiche essenziali includono: utilizzare `role="presentation"` sulle tabelle di layout, fornire testo alternativo per tutte le immagini informative, mantenere un rapporto di contrasto minimo di 4.5:1, strutturare il contenuto con una gerarchia di heading logica e assicurarsi che i link siano comprensibili fuori contesto.

---

## Internazionalizzazione

### Attributo lang

L'attributo `lang` specifica la lingua del contenuto di un elemento. Deve essere presente sull'elemento `<html>` per indicare la lingua principale del documento e puo essere applicato a qualsiasi elemento per indicare cambio di lingua all'interno della pagina:

```html
<html lang="it">
<body>
    <p>La documentazione ufficiale e disponibile in
       <a href="/en" lang="en">English</a> e
       <a href="/de" lang="de">Deutsch</a>.</p>

    <blockquote lang="la">
        <p>Cogito, ergo sum.</p>
    </blockquote>

    <p>Il termine giapponese <span lang="ja">改善</span>
       (kaizen) significa miglioramento continuo.</p>
</body>
</html>
```

I valori dell'attributo `lang` seguono lo standard BCP 47. I codici piu comuni: `it` (italiano), `en` (inglese), `en-US` (inglese americano), `en-GB` (inglese britannico), `fr` (francese), `de` (tedesco), `es` (spagnolo), `ja` (giapponese), `zh-Hans` (cinese semplificato), `zh-Hant` (cinese tradizionale), `ar` (arabo), `he` (ebraico).

L'attributo `lang` influenza: la pronuncia degli screen reader (che selezionano la sintesi vocale appropriata), la sillabazione automatica del browser, la selezione dei font (il browser puo scegliere glifi diversi per lo stesso codepoint Unicode in base alla lingua), i suggerimenti ortografici e le regole tipografiche (come le virgolette: italiane "" vs inglesi "").

### Attributo dir e Testo Bidirezionale

L'attributo `dir` specifica la direzionalita del testo. Accetta tre valori: `ltr` (left-to-right, default), `rtl` (right-to-left) e `auto` (determinata automaticamente dal primo carattere con direzionalita forte):

```html
<!-- Pagina in arabo -->
<html lang="ar" dir="rtl">
<body>
    <h1>مرحبا بالعالم</h1>
    <p>Questo paragrafo e scritto da destra a sinistra.</p>

    <!-- Contenuto inline con direzionalita diversa -->
    <p>Il sito <span dir="ltr">https://www.esempio.com</span>
       e disponibile in arabo.</p>
</body>
</html>
```

#### Elementi BDI e BDO

**`<bdi>`** (Bidirectional Isolate) isola un segmento di testo dal contesto bidirezionale circostante. E fondamentale quando si inserisce contenuto generato dall'utente di cui non si conosce la direzionalita:

```html
<!-- Senza bdi: nomi RTL possono corrompere la formattazione -->
<ul>
    <li>Utente <bdi>إيان</bdi>: 3 nuovi messaggi</li>
    <li>Utente <bdi>Marco</bdi>: 1 nuovo messaggio</li>
    <li>Utente <bdi>محمد</bdi>: 5 nuovi messaggi</li>
</ul>
```

Senza `<bdi>`, un nome in arabo o ebraico inserito in una frase LTR puo causare il riordinamento errato del testo circostante a causa dell'algoritmo bidirezionale Unicode. `<bdi>` crea un contesto bidirezionale isolato che previene questa interferenza.

**`<bdo>`** (Bidirectional Override) forza la direzionalita del testo, sovrascrivendo l'algoritmo bidirezionale. Deve sempre specificare l'attributo `dir`:

```html
<!-- Forzare una direzione specifica -->
<p>Testo normale: <bdo dir="rtl">Questo testo e invertito</bdo></p>
<!-- Risultato visivo: "otitrevni è otset otseuQ" -->
```

### Elemento Ruby per Annotazioni Fonetiche

L'elemento `<ruby>` marca annotazioni fonetiche (furigana in giapponese, zhuyin in cinese, romanizzazioni) sopra o accanto al testo base. E essenziale per la tipografia dell'Asia orientale:

```html
<!-- Giapponese: kanji con lettura hiragana -->
<p lang="ja">
    <ruby>
        漢<rp>(</rp><rt>かん</rt><rp>)</rp>
        字<rp>(</rp><rt>じ</rt><rp>)</rp>
    </ruby>
    を学ぶ。
</p>

<!-- Cinese: caratteri con pinyin -->
<p lang="zh">
    <ruby>
        中<rp>(</rp><rt>zhōng</rt><rp>)</rp>
        国<rp>(</rp><rt>guó</rt><rp>)</rp>
    </ruby>
</p>
```

`<rt>` (Ruby Text) contiene l'annotazione. `<rp>` (Ruby Parenthesis) fornisce parentesi di fallback per browser che non supportano ruby — il suo contenuto viene visualizzato solo quando il rendering ruby non e disponibile, mostrando le annotazioni tra parentesi inline.

### Attributo translate

L'attributo `translate` indica se il contenuto di un elemento deve essere tradotto dagli strumenti di traduzione automatica. Accetta `yes` (default) o `no`:

```html
<p>Per configurare il server, eseguire il comando
   <code translate="no">npm run build</code>
   nella directory del progetto.</p>

<p>Il nome del prodotto <span translate="no">CloudSync Pro</span>
   non deve essere tradotto.</p>

<p>Inserire il codice errore <code translate="no">ERR_CONN_REFUSED</code>
   nel campo di ricerca.</p>
```

Questo attributo e particolarmente utile per nomi di brand, comandi tecnici, codici e identificativi che non devono essere alterati dalla traduzione automatica di Google Translate o servizi simili.

### Attributo hreflang per Link Multilingua

L'attributo `hreflang` sui link indica la lingua del documento collegato. Oltre all'uso nei `<link>` per l'indicizzazione SEO (gia mostrato nella sezione Meta Tags), puo essere applicato ai link di navigazione:

```html
<nav aria-label="Selezione lingua">
    <ul>
        <li><a href="/it" hreflang="it" lang="it">Italiano</a></li>
        <li><a href="/en" hreflang="en" lang="en">English</a></li>
        <li><a href="/fr" hreflang="fr" lang="fr">Français</a></li>
        <li><a href="/ar" hreflang="ar" lang="ar" dir="rtl">العربية</a></li>
    </ul>
</nav>
```

---

## Best Practices

### 1. Utilizzare sempre il DOCTYPE e la dichiarazione della lingua

Ogni documento deve iniziare con `<!DOCTYPE html>` e l'elemento `<html>` deve includere l'attributo `lang` con il codice della lingua corretta. Questo garantisce il rendering in standards mode e permette alle tecnologie assistive di selezionare la sintesi vocale appropriata.

### 2. Preferire elementi semantici ai div generici

Sostituire i `<div>` con elementi semantici come `<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<aside>` e `<footer>` migliora l'accessibilita, l'indicizzazione SEO e la leggibilita del codice. Un documento ben strutturato semanticamente e comprensibile anche senza CSS.

### 3. Garantire l'accessibilita come requisito, non come optional

Includere attributi `alt` significativi per tutte le immagini informative (e `alt=""` per quelle decorative), mantenere una gerarchia di heading coerente, assicurare contrasti di colore adeguati e testare la navigazione da tastiera. L'accessibilita non e un'aggiunta successiva, ma una caratteristica fondamentale del prodotto.

### 4. Ottimizzare il caricamento delle risorse

Utilizzare `defer` per gli script applicativi e `async` per quelli indipendenti. Applicare `loading="lazy"` alle immagini below-the-fold. Impiegare resource hints (`preconnect`, `preload`, `prefetch`) per le risorse critiche. Specificare `width` e `height` su immagini e iframe per prevenire il CLS.

### 5. Validare i form sia lato client che lato server

La validazione HTML5 nativa migliora l'esperienza utente con feedback immediato, ma non e mai sufficiente come unica misura di sicurezza. Ogni dato inviato dall'utente deve essere validato e sanitizzato sul server. Utilizzare `novalidate` sul form quando si implementa una validazione JavaScript personalizzata, per evitare la doppia visualizzazione degli errori.

### 6. Adottare una strategia di immagini responsive

Utilizzare `srcset` e `sizes` per servire immagini adatte al dispositivo. Impiegare l'elemento `<picture>` per l'art direction e il supporto a formati moderni come WebP e AVIF con fallback. Comprimere le immagini e specificare sempre dimensioni esplicite per prevenire lo spostamento del layout.

### 7. Implementare una Content Security Policy

Definire una CSP che limiti le origini consentite per script, stili e altre risorse. Evitare `'unsafe-inline'` e `'unsafe-eval'` per gli script; preferire nonce o hash. Utilizzare SRI per verificare l'integrita delle risorse esterne. Testare la policy in modalita report-only prima di applicarla in produzione.

### 8. Strutturare i form per l'usabilita e l'accessibilita

Ogni input deve avere un `<label>` associato tramite l'attributo `for`. Raggruppare campi correlati con `<fieldset>` e `<legend>`. Non utilizzare il `placeholder` come sostituto del label. Fornire messaggi di errore chiari e associarli al campo corrispondente tramite `aria-describedby`.

### 9. Scrivere markup valido e ben formattato

Utilizzare un validatore HTML per verificare la correttezza del markup. Rispettare il content model degli elementi (ad esempio, non annidare `<div>` dentro `<p>`, non usare `<a>` dentro `<a>`). Chiudere tutti i tag che lo richiedono. Utilizzare un linter come HTMLHint o il validatore W3C per automatizzare i controlli.

### 10. Separare struttura, presentazione e comportamento

HTML definisce la struttura e la semantica del contenuto. CSS gestisce la presentazione visiva. JavaScript controlla il comportamento interattivo. Evitare stili inline e gestori di eventi negli attributi HTML quando possibile. Utilizzare classi CSS significative e gestori di eventi registrati tramite `addEventListener()`. Questa separazione migliora la manutenibilita, la testabilita e le performance grazie a un caching piu efficiente delle risorse esterne.

---

## Esercizi

### Esercizio 1 — Struttura semantica di un articolo di blog

**Obiettivo:** Costruire una pagina HTML5 con markup semantico corretto per un articolo di blog.

- Creare un documento con `<!DOCTYPE html>`, lingua (`lang="it"`), charset UTF-8 e viewport meta tag
- Utilizzare `<header>`, `<nav>`, `<main>`, `<article>`, `<aside>` e `<footer>` come elementi strutturali
- L'articolo deve contenere `<h1>`, almeno due `<section>` con `<h2>`, un elemento `<time datetime="...">` e un `<figure>` con `<figcaption>`
- Il `<nav>` deve contenere una lista non ordinata con almeno 5 link
- L'`<aside>` deve contenere articoli correlati e un breve profilo autore
- Validare il documento con il validatore W3C (`validator.w3.org`) e correggere eventuali errori

### Esercizio 2 — Form di registrazione accessibile

**Obiettivo:** Implementare un form di registrazione multi-campo con validazione HTML5 nativa e attributi di accessibilita.

- Creare un form con i campi: nome, cognome, email, password, data di nascita, numero di telefono, selezione paese (dropdown), accettazione termini (checkbox)
- Associare ogni campo a un `<label>` tramite attributo `for`/`id`
- Raggruppare i campi correlati con `<fieldset>` e `<legend>` (es. "Dati personali", "Credenziali")
- Applicare validazione nativa: `required`, `type="email"`, `pattern` per la password (minimo 8 caratteri, una maiuscola, un numero), `min`/`max` per la data
- Aggiungere `aria-describedby` per collegare suggerimenti e messaggi di errore ai campi
- Testare la navigazione completa del form usando solo la tastiera (Tab, Shift+Tab, Enter, Spazio)

### Esercizio 3 — Galleria multimediale responsive

**Obiettivo:** Creare una pagina con contenuti multimediali ottimizzati per diversi dispositivi.

- Inserire almeno 3 immagini usando `<picture>` con sorgenti WebP e AVIF e fallback JPEG
- Configurare `srcset` e `sizes` per servire risoluzioni differenti in base alla viewport
- Aggiungere un elemento `<video>` con `<source>` multipli (MP4, WebM), poster, controlli nativi e sottotitoli via `<track kind="subtitles">`
- Aggiungere un elemento `<audio>` con `<source>` multipli e testo di fallback
- Specificare `width` e `height` espliciti su tutte le immagini e il video per prevenire il CLS
- Applicare `loading="lazy"` alle immagini below-the-fold e `loading="eager"` con `fetchpriority="high"` all'immagine hero

### Esercizio 4 — Dashboard accessibile con tabelle e ARIA

**Obiettivo:** Costruire una dashboard informativa con tabelle dati, landmark ARIA e navigazione da tastiera completa.

- Creare una tabella dati complessa con `<thead>`, `<tbody>`, `<tfoot>`, `<caption>`, e attributi `scope="col"` / `scope="row"` sugli header
- Implementare un sistema di tab panel con `role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected` e `aria-controls`
- Aggiungere un dialog modale usando `<dialog>` con gestione del focus trap (il focus non deve uscire dal modale finche e aperto)
- Includere un live region con `aria-live="polite"` che annuncia aggiornamenti dinamici
- Verificare con uno screen reader (NVDA, VoiceOver o Orca) che tutti i contenuti siano leggibili e navigabili
- La pagina deve superare un audit Lighthouse Accessibility con punteggio >= 95

### Esercizio 5 — Pagina completa con CSP e ottimizzazione del caricamento

**Obiettivo:** Assemblare una pagina production-ready che integri sicurezza, performance e accessibilita.

- Creare una landing page completa con hero, sezione feature, testimonial, pricing e footer
- Implementare una Content Security Policy via meta tag con `default-src 'self'`, restrizioni su `script-src` e `style-src` (nonce-based), e `frame-src 'none'`
- Aggiungere resource hints: `<link rel="preconnect">` per i font, `<link rel="preload">` per il CSS critico e l'immagine hero, `<link rel="prefetch">` per una pagina secondaria
- Caricare gli script con `defer` (applicativi) e `async` (analytics)
- Aggiungere dati strutturati JSON-LD (`<script type="application/ld+json">`) con schema Organization
- Verificare con Lighthouse che tutte le categorie (Performance, Accessibility, Best Practices, SEO) raggiungano un punteggio >= 90

---

## Letture e Riferimenti

### Documentazione ufficiale

- **WHATWG HTML Living Standard** — Specifica normativa completa e aggiornata di HTML. <https://html.spec.whatwg.org/multipage/> (consultato: 2026-05-24)
- **MDN Web Docs — HTML** — Riferimento pratico con esempi per ogni elemento e attributo HTML. <https://developer.mozilla.org/en-US/docs/Web/HTML> (consultato: 2026-05-24)
- **MDN Web Docs — HTML Elements Reference** — Lista completa di tutti gli elementi HTML con descrizione e compatibilita browser. <https://developer.mozilla.org/en-US/docs/Web/HTML/Element> (consultato: 2026-05-24)
- **W3C WAI — ARIA Authoring Practices** — Pattern e linee guida per l'implementazione di widget ARIA accessibili. <https://www.w3.org/WAI/ARIA/apg/> (consultato: 2026-05-24)
- **W3C — Web Content Accessibility Guidelines (WCAG) 2.2** — Standard internazionale per l'accessibilita dei contenuti web. <https://www.w3.org/TR/WCAG22/> (consultato: 2026-05-24)
- **MDN Web Docs — Content Security Policy (CSP)** — Guida all'implementazione di CSP per la protezione del documento. <https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP> (consultato: 2026-05-24)
- **Schema.org** — Vocabolario per dati strutturati utilizzato dai motori di ricerca. <https://schema.org/> (consultato: 2026-05-24)
- **W3C Markup Validation Service** — Validatore ufficiale per documenti HTML. <https://validator.w3.org/> (consultato: 2026-05-24)

### Libri e approfondimenti

- Duckett J., *HTML and CSS: Design and Build Websites*, Wiley, 2011.
- Keith J., Andrew R., *HTML5 for Web Designers* (2nd ed.), A Book Apart, 2016.
- Lawson B., Sharp R., *Introducing HTML5* (2nd ed.), New Riders, 2011.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [02 — CSS3](02-css3.md) | Il CSS applica la presentazione visiva alla struttura semantica definita in HTML |
| [03 — CSS Framework](03-css-framework.md) | I framework CSS come Tailwind e Bootstrap operano sulle classi degli elementi HTML |
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | JavaScript interagisce con il DOM generato dal parser HTML per il comportamento dinamico |
| [06 — TypeScript](06-typescript.md) | TypeScript tipizza le interazioni con il DOM HTML tramite le interfacce `HTMLElement` |
| [14 — Sicurezza Web](14-sicurezza-web.md) | La Content Security Policy e gli attributi di sicurezza HTML prevengono XSS e injection |
| [17 — Performance Web](17-performance-web.md) | Attributi HTML come `loading`, `fetchpriority` e resource hints influenzano direttamente i Core Web Vitals |

---

## Glossario

| Termine | Definizione |
|---|---|
| **DOM** | Document Object Model: rappresentazione ad albero del documento HTML che il browser costruisce e che JavaScript puo manipolare. |
| **Elemento semantico** | Tag HTML che comunica il significato del contenuto (es. `<article>`, `<nav>`, `<aside>`) anziche solo la sua presentazione. |
| **ARIA** | Accessible Rich Internet Applications: insieme di attributi che estendono HTML per migliorare l'accessibilita delle interfacce dinamiche. |
| **Landmark** | Regione della pagina identificata da elementi semantici o ruoli ARIA (es. `<main>`, `role="navigation"`) usata dagli screen reader per la navigazione rapida. |
| **CSP** | Content Security Policy: header HTTP o meta tag che definisce le origini consentite per script, stili e altre risorse nel documento. |
| **SRI** | Subresource Integrity: attributo `integrity` su `<script>` e `<link>` che verifica l'hash della risorsa esterna contro una manomissione. |
| **Resource hint** | Direttiva `<link>` (`preconnect`, `preload`, `prefetch`, `dns-prefetch`) che suggerisce al browser di anticipare il caricamento di risorse. |
| **CLS** | Cumulative Layout Shift: metrica Core Web Vitals che misura gli spostamenti inattesi degli elementi durante il caricamento della pagina. |
| **Validazione nativa** | Sistema di validazione form integrato nel browser tramite attributi HTML (`required`, `pattern`, `min`, `max`, `type`) senza JavaScript. |
| **Content model** | Regole che definiscono quali elementi possono essere contenuti all'interno di un dato elemento HTML (es. `<p>` non puo contenere `<div>`). |
| **JSON-LD** | JavaScript Object Notation for Linked Data: formato per dati strutturati incorporati nella pagina tramite `<script type="application/ld+json">`. |
| **Viewport meta tag** | Tag `<meta name="viewport">` che controlla le dimensioni e la scala della viewport sui dispositivi mobili. |
| **Fallback** | Contenuto alternativo mostrato quando il browser non supporta un elemento o formato (es. testo dentro `<video>`, JPEG dopo WebP). |
| **Focus trap** | Tecnica che confina la navigazione da tastiera (Tab) all'interno di un componente modale finche non viene chiuso. |
| **Art direction** | Tecnica di responsive images che serve immagini con composizione diversa (non solo risoluzione) in base alla viewport, tramite `<picture>`. |
| **Popover API** | API nativa HTML per creare contenuti flottanti (tooltip, menu, toast) con dismissione automatica e gestione del top layer, senza JavaScript. |
| **Web Components** | Insieme di tecnologie native (Custom Elements, Shadow DOM, Templates/Slots) per creare elementi HTML personalizzati, riutilizzabili e incapsulati. |
| **Shadow DOM** | Albero DOM incapsulato associato a un elemento, con stili isolati dal documento principale. Previene conflitti CSS tra componenti. |
| **Custom Element** | Elemento HTML personalizzato definito con `customElements.define()`, il cui nome deve contenere un trattino (es. `<mio-componente>`). |
| **Open Graph** | Protocollo di metadati (`og:title`, `og:image`, ecc.) sviluppato da Facebook per standardizzare le anteprime dei link condivisi sui social media. |
| **Anchor Positioning** | Meccanismo CSS per posizionare un elemento relativamente a un altro elemento (l'ancora), usato tipicamente con popover e tooltip. |
| **Speculation Rules** | API per il precaricamento speculativo delle pagine, successore di `<link rel="prefetch">`, con controllo granulare sull'eagerness. |
| **OffscreenCanvas** | API che permette di eseguire operazioni di rendering Canvas in un Web Worker, separando il disegno dal thread principale dell'UI. |
| **Trusted Types** | API di sicurezza del browser che previene XSS basato su DOM forzando la sanitizzazione dei valori passati a sink pericolosi come `innerHTML`. |
| **Declarative Shadow DOM** | Modalita per definire Shadow DOM direttamente nel markup HTML tramite `<template shadowrootmode>`, senza necessita di JavaScript. |
| **BDI** | Bidirectional Isolate: elemento che isola un segmento di testo dall'algoritmo bidirezionale Unicode, utile per contenuto di direzionalita sconosciuta. |
| **Ruby** | Elemento HTML per annotazioni fonetiche tipiche della tipografia dell'Asia orientale (furigana giapponese, pinyin cinese). |
| **WCAG 2.2** | Versione 2.2 delle Web Content Accessibility Guidelines (2023), con nuovi criteri per focus appearance, target size e dragging movements. |
