# Tutorial 01 — HTML5 Semantico e Accessibile: Dal Principiante all'Esperto

> **Companion a:** `01-html5.md`
> **Scope:** Struttura del documento, elementi semantici, content model, form e validazione nativa, Constraint Validation API, immagini responsive, video e audio, accessibilità e WCAG 2.2, ARIA, `<dialog>` e Popover API, meta tag e Open Graph, SVG inline, internazionalizzazione, Web Components, sicurezza del documento
> **Prerequisiti:** `tutorial_00_ambiente_setup_web.md` — un progetto Vite avviabile, VS Code con format-on-save
> **Durata stimata:** 20-25 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** HTML Living Standard · WCAG 2.2 · browser evergreen (Chrome, Firefox, Safari, Edge)

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Cosa fa davvero l'HTML](#a1-cosa-fa-davvero-lhtml)
  - [A2. Lo scheletro del documento](#a2-lo-scheletro-del-documento)
  - [A3. Il testo: titoli, paragrafi, liste](#a3-il-testo-titoli-paragrafi-liste)
  - [A4. Link e percorsi](#a4-link-e-percorsi)
  - [A5. Immagini e il significato di `alt`](#a5-immagini-e-il-significato-di-alt)
  - [A6. Gli elementi semantici strutturali](#a6-gli-elementi-semantici-strutturali)
  - [A7. Scegliere l'elemento giusto](#a7-scegliere-lelemento-giusto)
  - [A8. Il primo form](#a8-il-primo-form)
  - [A9. Tabelle di dati, annotate come si deve](#a9-tabelle-di-dati-annotate-come-si-deve)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. Content model: cosa può contenere cosa](#b1-content-model-cosa-può-contenere-cosa)
  - [B2. Il DOM non è l'HTML che hai scritto](#b2-il-dom-non-è-lhtml-che-hai-scritto)
  - [B3. Tipi di input e validazione nativa](#b3-tipi-di-input-e-validazione-nativa)
  - [B4. Constraint Validation API](#b4-constraint-validation-api)
  - [B5. `FormData` e l'invio senza ricaricare](#b5-formdata-e-linvio-senza-ricaricare)
  - [B6. Immagini responsive](#b6-immagini-responsive)
  - [B7. Video e audio](#b7-video-e-audio)
  - [B8. L'albero di accessibilità e il nome accessibile](#b8-lalbero-di-accessibilità-e-il-nome-accessibile)
  - [B9. ARIA: le cinque regole](#b9-aria-le-cinque-regole)
  - [B10. Tastiera e gestione del focus](#b10-tastiera-e-gestione-del-focus)
  - [B11. `<dialog>` e la Popover API](#b11-dialog-e-la-popover-api)
  - [B12. Meta tag, Open Graph e dati strutturati](#b12-meta-tag-open-graph-e-dati-strutturati)
  - [B13. SVG inline](#b13-svg-inline)
  - [B14. Internazionalizzazione](#b14-internazionalizzazione)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: portale informativo aziendale](#c2-mini-progetto-portale-informativo-aziendale)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. Web Components: Custom Elements](#d1-web-components-custom-elements)
  - [D2. Shadow DOM, slot e Declarative Shadow DOM](#d2-shadow-dom-slot-e-declarative-shadow-dom)
  - [D3. Sicurezza del documento](#d3-sicurezza-del-documento)
  - [D4. HTML per email: un altro linguaggio](#d4-html-per-email-un-altro-linguaggio)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                            DOCUMENTO HTML
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
   ┌────▼─────┐            ┌──────▼──────┐          ┌───────▼───────┐
   │  <head>  │            │   <body>    │          │  ATTRIBUTI    │
   │          │            │             │          │   GLOBALI     │
   │ charset  │            │  struttura  │          │               │
   │ viewport │            │  contenuto  │          │  id  class    │
   │ title    │            │  interattiv.│          │  lang  dir    │
   │ meta OG  │            │             │          │  hidden       │
   │ link CSS │            │             │          │  tabindex     │
   │ JSON-LD  │            │             │          │  data-*       │
   └──────────┘            └──────┬──────┘          └───────────────┘
                                  │
     ┌────────────────────────────┼────────────────────────────┐
     │                            │                            │
┌────▼──────────┐        ┌────────▼────────┐         ┌─────────▼────────┐
│  SEMANTICA    │        │      FORM       │         │    MULTIMEDIA    │
│               │        │                 │         │                  │
│  <header>     │        │  <form>         │         │  <img srcset>    │
│  <nav>        │        │  <label>        │         │  <picture>       │
│  <main>       │        │  <input type>   │         │  <video><track>  │
│  <article>    │        │  <fieldset>     │         │  <audio>         │
│  <section>    │        │  required       │         │  <svg> inline    │
│  <aside>      │        │  pattern        │         │  <canvas>        │
│  <footer>     │        │  Constraint     │         │                  │
│  <figure>     │        │   Validation    │         │  loading=lazy    │
│  <time>       │        │  FormData       │         │  fetchpriority   │
└───────┬───────┘        └────────┬────────┘         └────────┬─────────┘
        │                         │                           │
        └─────────────────────────┼───────────────────────────┘
                                  │
              ┌───────────────────▼────────────────────┐
              │          ACCESSIBILITÀ (WCAG 2.2)      │
              │                                        │
              │  albero di accessibilità               │
              │   ├── ruolo   (cos'è)                  │
              │   ├── nome    (come si chiama)         │
              │   ├── stato   (com'è adesso)           │
              │   └── valore  (quanto vale)            │
              │                                        │
              │  landmark · focus visibile · contrasto │
              │  ARIA solo quando l'HTML non basta     │
              └───────────────────┬────────────────────┘
                                  │
              ┌───────────────────▼────────────────────┐
              │      INTERATTIVITÀ NATIVA              │
              │                                        │
              │  <details>/<summary>   apri e chiudi   │
              │  <dialog>              modale vera     │
              │  popover               strato superiore│
              └────────────────────────────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Cosa fa davvero l'HTML

> **Analogia:** immagina di dettare un documento al telefono a qualcuno che non lo vedrà mai. Non puoi dire "questa riga in grassetto, grande, centrata": devi dire "questo è il titolo del capitolo", "questa è una citazione", "questo è l'elenco degli ingredienti". Chi ascolta deciderà come rappresentarlo — su carta, a voce, in Braille. L'HTML è quella dettatura: descrive **cosa è** ogni pezzo, non come deve apparire.

Questa distinzione è l'intero contenuto del tutorial, quindi vale la pena renderla concreta subito.

```html
<!-- ❌ SBAGLIATO — descrive l'aspetto. Il testo sembra un titolo, ma non lo è. -->
<div class="grande grassetto">Bilancio 2026</div>
<div>Il risultato d'esercizio è positivo.</div>

<!-- ✅ CORRETTO — descrive il ruolo. L'aspetto lo darà il CSS. -->
<h1>Bilancio 2026</h1>
<p>Il risultato d'esercizio è positivo.</p>
```

Visivamente puoi rendere i due esempi identici con poche righe di CSS. Non sono comunque equivalenti, e le differenze non sono estetiche:

| Chi legge | Cosa vede nella versione `<div>` | Cosa vede nella versione `<h1>` |
|---|---|---|
| Uno screen reader | Testo semplice, indistinguibile dal resto | "Intestazione livello 1, Bilancio 2026" |
| L'utente di screen reader che naviga per titoli | Niente: non trova il titolo | Salta direttamente qui |
| Un motore di ricerca | Testo di corpo | Il titolo principale della pagina |
| La modalità lettura del browser | Spesso scarta la pagina | Estrae titolo e corpo |
| Il tuo CSS fra sei mesi | Dipende da una classe che qualcuno può rinominare | Dipende dall'elemento, che non cambia |

**Le tre tecnologie e i tre mestieri.** Non si sovrappongono, e tenerle separate è ciò che rende un progetto manutenibile:

```
HTML  →  struttura e significato     "questo è un pulsante di invio"
CSS   →  presentazione               "i pulsanti di invio sono blu con angoli tondi"
JS    →  comportamento               "al clic, valida e manda i dati"
```

Quando le mescoli — un `<div>` reso cliccabile da JavaScript e colorato da CSS per sembrare un pulsante — ottieni qualcosa che *sembra* un pulsante e non lo è: non risponde alla barra spaziatrice, non compare nella navigazione da tastiera, non viene annunciato come pulsante. Ci torniamo in [B10](#b10-tastiera-e-gestione-del-focus).

---

## A2. Lo scheletro del documento

Ogni pagina parte da qui. Non è una formula magica: ogni riga fa una cosa precisa.

```html
<!-- index.html -->
<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Bilancio 2026 — Acme S.p.A.</title>
    <meta name="description" content="Il bilancio consolidato 2026 di Acme S.p.A." />
    <link rel="stylesheet" href="/src/style.css" />
  </head>
  <body>
    <h1>Bilancio 2026</h1>
    <p>Il risultato d'esercizio è positivo.</p>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

Riga per riga:

**`<!doctype html>`** — non è un tag, è un'istruzione al parser: "usa le regole standard". Senza, il browser entra in *quirks mode* e riproduce i bug di Internet Explorer 5 per compatibilità con pagine del 1998. In quirks mode il box model cambia, l'ereditarietà di alcune proprietà cambia, e passi ore a chiederti perché il CSS non fa quello che dice la documentazione.

**`<html lang="it">`** — dichiara la lingua del documento. Non è decorativo: lo screen reader sceglie la pronuncia in base a questo attributo. Con `lang="en"` su testo italiano, la sintesi vocale legge "bilancio" con fonetica inglese, e il risultato è incomprensibile. È anche un criterio di conformità WCAG (3.1.1, livello A).

**`<meta charset="UTF-8" />`** — deve stare **entro i primi 1024 byte** del documento, quindi in cima al `<head>`. Prima di leggerlo il browser non sa come decodificare i byte e tira a indovinare; il risultato sono le classiche `Ã¨` al posto di `è`.

**`<meta name="viewport" ...>`** — senza questa riga, i browser mobili fingono uno schermo da 980 pixel e rimpiccioliscono tutto. È il motivo per cui un sito non responsive appare minuscolo sul telefono. Ne riparliamo in `tutorial_02_css3.md`.

**`<title>`** — è il nome della scheda, il testo del segnalibro, il titolo nei risultati di ricerca e la prima cosa che uno screen reader annuncia quando la pagina si carica. Scrivilo dal particolare al generale: `Bilancio 2026 — Acme S.p.A.`, non `Acme S.p.A. — Bilancio 2026`, perché nella scheda viene troncato da destra.

**`<script type="module">` alla fine del `<body>`** — `type="module"` abilita gli `import` ES6 ed è **differito per definizione**: il browser scarica lo script in parallelo al parsing e lo esegue quando il documento è pronto. Non serve aggiungere `defer`.

### `<head>` e `<body>`, la distinzione

```
<head>  ──►  informazioni SULLA pagina.  Non si vede.
             titolo, codifica, fogli di stile, meta per i social,
             icone, dati strutturati.

<body>  ──►  la pagina.  Si vede.
             tutto il contenuto, la struttura, i form, i media.
```

L'errore tipico di chi inizia è mettere contenuto visibile nel `<head>`. Il browser non protesta: chiude il `<head>` da solo e sposta il contenuto nel `<body>`. Vedi [B2](#b2-il-dom-non-è-lhtml-che-hai-scritto).

---

## A3. Il testo: titoli, paragrafi, liste

### I titoli e la gerarchia

```html
<h1>Bilancio 2026</h1>

<h2>Conto economico</h2>
<h3>Ricavi</h3>
<h3>Costi operativi</h3>

<h2>Stato patrimoniale</h2>
<h3>Attivo</h3>
<h4>Immobilizzazioni</h4>
<h3>Passivo</h3>
```

I titoli formano un **indice**. Chi usa uno screen reader naviga la pagina saltando di titolo in titolo, esattamente come tu scorri con gli occhi cercando il paragrafo giusto. Perché quell'indice funzioni servono due regole:

```html
<!-- ❌ SBAGLIATO — salta un livello: il lettore non capisce
     se "Ricavi" è sottosezione di "Bilancio" o di qualcos'altro -->
<h1>Bilancio 2026</h1>
<h3>Ricavi</h3>

<!-- ❌ SBAGLIATO — usa il titolo per la dimensione del carattere.
     "Nota a piè di pagina" non è un sotto-sotto-sotto-argomento. -->
<h6>Nota a piè di pagina</h6>

<!-- ✅ CORRETTO — livelli consecutivi, e il testo piccolo si fa con il CSS -->
<h1>Bilancio 2026</h1>
<h2>Ricavi</h2>
<p class="nota">Nota a piè di pagina</p>
```

**Quanti `<h1>` per pagina?** Uno. Tecnicamente lo standard ne consente di più (uno per ogni `<article>` o `<section>`), ma l'*outline algorithm* che avrebbe reso utile quella flessibilità non è mai stato implementato da nessun browser ed è stato rimosso dalla specifica. Nella pratica: un `<h1>` per pagina, che dice di cosa parla la pagina.

### Paragrafi

```html
<p>Il risultato d'esercizio è positivo per il terzo anno consecutivo.</p>
<p>La liquidità disponibile copre dodici mesi di costi operativi.</p>
```

```html
<!-- ❌ SBAGLIATO — <br> per separare i paragrafi.
     Sono due pensieri distinti, non uno con un a capo dentro. -->
<p>Il risultato d'esercizio è positivo.<br /><br />La liquidità copre dodici mesi.</p>

<!-- ✅ CORRETTO — <br> serve dove l'a capo fa parte del contenuto -->
<p>
  Acme S.p.A.<br />
  Via Roma 12<br />
  20121 Milano
</p>
```

`<br>` è legittimo negli indirizzi, nei versi di una poesia, nei blocchi dove la riga è significativa. Non lo è per fare spazio: quello è un lavoro del CSS.

### Enfasi, con il significato giusto

```html
<p>Il pagamento va effettuato <strong>entro il 30 giugno</strong>.</p>
<p>Il termine <em>perentorio</em> non ammette proroghe.</p>

<p>
  Il tasso è del <b>3,5%</b> annuo.
  <!-- <b> = evidenziato senza maggiore importanza (es. parola chiave in un elenco) -->
</p>
<p>Il vascello si chiamava <i>Beagle</i>.</p>
<!-- <i> = voce fuori dal registro corrente: termine straniero, nome di nave, pensiero -->
```

| Elemento | Significato | Come lo legge uno screen reader |
|---|---|---|
| `<strong>` | Forte importanza, gravità, urgenza | Con enfasi vocale |
| `<em>` | Enfasi che cambia il senso della frase | Con enfasi vocale |
| `<b>` | Rilievo tipografico senza importanza aggiuntiva | Normale |
| `<i>` | Voce alternativa: termine tecnico, lingua straniera | Normale |
| `<mark>` | Evidenziato per rilevanza nel contesto attuale (es. risultato di ricerca) | Alcuni lo annunciano |
| `<small>` | Note legali, copyright, chiose | Normale |

Confronta il senso: *"il termine **perentorio** non ammette proroghe"* dice che la perentorietà è il punto. *"il termine perentorio **non** ammette proroghe"* nega la proroga. `<em>` cambia il significato della frase, `<b>` no.

### Liste

```html
<!-- Elenco non ordinato: l'ordine non conta -->
<ul>
  <li>Fatture emesse</li>
  <li>Note di credito</li>
  <li>Solleciti</li>
</ul>

<!-- Elenco ordinato: l'ordine È il contenuto -->
<ol>
  <li>Verificare l'anagrafica del cliente</li>
  <li>Emettere la fattura</li>
  <li>Registrare il pagamento</li>
</ol>

<!-- Elenco di definizioni: coppie termine/descrizione -->
<dl>
  <dt>Ricavo</dt>
  <dd>Incremento di risorse derivante dall'attività caratteristica.</dd>

  <dt>Costo</dt>
  <dd>Consumo di risorse necessario a produrre i ricavi.</dd>
</dl>
```

Lo screen reader annuncia "elenco di 3 elementi" e permette di saltarlo tutto insieme. Una serie di `<div>` non offre nulla di simile: va ascoltata riga per riga.

`<ol>` accetta attributi che a volte servono davvero:

```html
<ol start="4">
  <li>Quarto passo</li>
  <li>Quinto passo</li>
</ol>

<ol reversed>
  <li>Terzo classificato</li>
  <li>Secondo classificato</li>
  <li>Primo classificato</li>
</ol>
```

### Citazioni, codice, date

```html
<blockquote cite="https://example.org/relazione-2026">
  <p>La solidità patrimoniale resta il presupposto di ogni investimento.</p>
  <footer>— <cite>Relazione del Consiglio, 2026</cite></footer>
</blockquote>

<p>Come recita l'articolo, <q>ogni ritardo comporta interessi di mora</q>.</p>

<p>Esegui <code>pnpm build</code> prima del deploy.</p>

<pre><code>pnpm install
pnpm run build
pnpm run preview</code></pre>

<p>Pubblicato il <time datetime="2026-03-15">15 marzo 2026</time>.</p>
<p>La riunione dura <time datetime="PT2H30M">due ore e mezza</time>.</p>
```

`<time datetime="...">` è quello che permette a un calendario, a un motore di ricerca o a uno script di capire *quale* data sia "15 marzo": il formato leggibile resta per l'umano, quello macchina sta nell'attributo.

Attenzione a `<pre>`: gli spazi e gli a capo al suo interno sono contenuto. Indentare `<pre>` come il resto del markup inserisce quegli spazi nell'output — è il motivo per cui il blocco qui sopra è schiacciato a sinistra.

---

## A4. Link e percorsi

```html
<a href="/prodotti">Catalogo prodotti</a>
```

Il link è l'elemento che ha reso il web quello che è. Ha tre modi di indicare la destinazione:

```html
<!-- Assoluto: dominio incluso. Per risorse esterne. -->
<a href="https://developer.mozilla.org/it/">MDN Web Docs</a>

<!-- Radice-relativo: parte da / , cioè dalla radice del sito.
     È la forma da preferire: funziona uguale da qualunque pagina. -->
<a href="/prodotti/catalogo">Catalogo</a>

<!-- Relativo al documento: dipende da dove ti trovi adesso.
     Fragile: sposta il file e il link si rompe. -->
<a href="../catalogo">Catalogo</a>

<!-- Frammento: una posizione dentro la pagina corrente -->
<a href="#contatti">Vai ai contatti</a>

<!-- Altri protocolli -->
<a href="mailto:info@acme.it">Scrivici</a>
<a href="tel:+390212345678">02 1234 5678</a>
```

### Il testo del link

```html
<!-- ❌ SBAGLIATO — chi naviga elencando i link sente "clicca qui, clicca qui, clicca qui" -->
<p>Per il catalogo <a href="/catalogo">clicca qui</a>.</p>

<!-- ✅ CORRETTO — il testo dice dove porta, anche estratto dal contesto -->
<p>Consulta il <a href="/catalogo">catalogo prodotti</a>.</p>
```

Gli screen reader offrono un comando che elenca tutti i link della pagina. In quell'elenco il testo del link è tutto ciò che resta: `clicca qui` ripetuto dodici volte è un elenco inutilizzabile. È il criterio WCAG 2.4.4.

### `target="_blank"` e la sua trappola

```html
<!-- ❌ RISCHIOSO su browser datati — la pagina aperta può manipolare
     quella di partenza tramite window.opener -->
<a href="https://esterno.example" target="_blank">Sito esterno</a>

<!-- ✅ ESPLICITO -->
<a
  href="https://esterno.example"
  target="_blank"
  rel="noopener noreferrer"
>
  Sito esterno<span class="solo-screen-reader"> (si apre in una nuova scheda)</span>
</a>
```

I browser evergreen applicano `noopener` da soli quando c'è `target="_blank"`, quindi il rischio è oggi teorico. Scriverlo comunque costa nulla e documenta l'intenzione. `noreferrer` in più impedisce di trasmettere l'indirizzo di provenienza.

L'avviso testuale non è pedanteria: aprire una scheda senza dirlo disorienta chi non vede il cambiamento, e il pulsante "indietro" smette di funzionare come previsto.

### `<a>` o `<button>`?

La domanda si risolve con un criterio solo:

```
Porta ad un altro indirizzo?          →  <a href="...">
Compie un'azione su questa pagina?    →  <button>
```

```html
<!-- ❌ SBAGLIATO — un link che non naviga -->
<a href="#" onclick="salvaBozza()">Salva bozza</a>

<!-- ✅ CORRETTO -->
<button type="button" onclick="salvaBozza()">Salva bozza</button>

<!-- ❌ SBAGLIATO — un pulsante che naviga: perde apri-in-nuova-scheda,
     copia-indirizzo, e la cronologia -->
<button onclick="location.href='/catalogo'">Catalogo</button>

<!-- ✅ CORRETTO -->
<a href="/catalogo">Catalogo</a>
```

Non è pignoleria: `<a href>` risponde a `Invio`, `<button>` risponde a `Invio` **e** `Spazio`, e solo `<a href>` offre il menu contestuale con "apri in una nuova scheda".

---

## A5. Immagini e il significato di `alt`

```html
<img src="/img/sede-milano.jpg" alt="La sede di Milano vista dalla strada" width="800" height="600" />
```

Quattro attributi, tutti con un motivo:

- **`src`** — dove sta il file.
- **`alt`** — il testo alternativo. Obbligatorio, e il valore giusto dipende dal ruolo dell'immagine.
- **`width` e `height`** — le dimensioni **intrinseche** in pixel. Servono anche se poi il CSS ridimensiona tutto: il browser le usa per riservare lo spazio prima che l'immagine arrivi, evitando che il testo sotto salti. È il *Cumulative Layout Shift*, uno dei Core Web Vitals, e ne parliamo in `tutorial_17_performance_web.md`.

### Scrivere `alt` bene

Non descrive l'immagine: **la sostituisce**. La domanda giusta è "se questa immagine non ci fosse, quale testo servirebbe qui?".

```html
<!-- Immagine informativa: descrivi ciò che comunica -->
<img src="/img/grafico-ricavi.png"
     alt="I ricavi crescono da 4,2 a 6,8 milioni fra il 2024 e il 2026" />

<!-- ❌ SBAGLIATO — "immagine di" è ridondante: lo screen reader
     annuncia già che si tratta di un'immagine -->
<img src="/img/grafico-ricavi.png" alt="Immagine di un grafico" />

<!-- ❌ SBAGLIATO — il nome del file non è un'alternativa testuale -->
<img src="/img/grafico-ricavi.png" alt="grafico-ricavi.png" />

<!-- Immagine decorativa: alt VUOTO, non alt assente -->
<img src="/img/onda-decorativa.svg" alt="" />

<!-- Immagine che è l'unico contenuto di un link:
     alt descrive la DESTINAZIONE, non l'immagine -->
<a href="/">
  <img src="/img/logo.svg" alt="Acme S.p.A. — pagina iniziale" />
</a>

<!-- Immagine accanto a un testo che dice già la stessa cosa:
     alt vuoto, altrimenti l'informazione viene letta due volte -->
<a href="/catalogo">
  <img src="/img/icona-catalogo.svg" alt="" />
  Catalogo prodotti
</a>
```

**`alt=""` e nessun `alt` non sono la stessa cosa.**

| Markup | Comportamento dello screen reader |
|---|---|
| `alt="descrizione"` | Legge la descrizione |
| `alt=""` | **Ignora l'immagine.** È quello che vuoi per la decorazione |
| *(nessun `alt`)* | Ripiega sul nome del file: `"grafico-ricavi-v3-finale.png"` |

### `<figure>` e `<figcaption>`

Quando l'immagine ha una didascalia visibile:

```html
<figure>
  <img src="/img/organigramma.png"
       alt="Organigramma: la direzione generale coordina quattro divisioni operative"
       width="1200" height="800" />
  <figcaption>Organigramma aggiornato a marzo 2026.</figcaption>
</figure>
```

`alt` e `<figcaption>` fanno lavori diversi e non vanno duplicati: `alt` sostituisce l'immagine per chi non la vede, `<figcaption>` commenta l'immagine per tutti. Se scrivi lo stesso testo nei due posti, chi usa uno screen reader lo sente due volte.

`<figure>` non serve solo alle immagini: va bene per un blocco di codice, una tabella o una citazione che il testo richiama come unità autonoma.

---

## A6. Gli elementi semantici strutturali

> **Analogia:** un giornale. C'è la testata in cima, il sommario, l'articolo principale, la colonna delle brevi, il colophon in fondo. Nessuno ha bisogno che gliene spieghino la funzione: la posizione e la forma la dichiarano. Gli elementi semantici sono quella struttura resa esplicita, così che anche chi non vede la pagina possa orientarsi con la stessa immediatezza.

```html
<body>
  <header>
    <img src="/img/logo.svg" alt="Acme S.p.A." />
    <nav aria-label="Principale">
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/prodotti">Prodotti</a></li>
        <li><a href="/contatti">Contatti</a></li>
      </ul>
    </nav>
  </header>

  <main>
    <h1>Bilancio 2026</h1>

    <article>
      <h2>Conto economico</h2>
      <p>I ricavi crescono del 12% rispetto all'esercizio precedente.</p>
    </article>

    <article>
      <h2>Stato patrimoniale</h2>
      <p>L'attivo circolante copre integralmente i debiti a breve.</p>
    </article>
  </main>

  <aside aria-label="Approfondimenti">
    <h2>Documenti correlati</h2>
    <ul>
      <li><a href="/bilancio-2025">Bilancio 2025</a></li>
    </ul>
  </aside>

  <footer>
    <p><small>© 2026 Acme S.p.A. — P.IVA 01234567890</small></p>
  </footer>
</body>
```

Cosa fa ciascuno:

| Elemento | Significato | Quante volte |
|---|---|---|
| `<header>` | Intestazione della pagina **o** di una sezione | Una per contenitore |
| `<nav>` | Un blocco di link di navigazione **principale** | Più d'una, se etichettate |
| `<main>` | Il contenuto specifico di questa pagina | **Una sola, visibile** |
| `<article>` | Unità autonoma, che avrebbe senso anche estratta | Quante servono |
| `<section>` | Raggruppamento tematico, **con un titolo** | Quante servono |
| `<aside>` | Contenuto collegato ma non essenziale | Quante servono |
| `<footer>` | Chiusura della pagina o della sezione | Una per contenitore |

**`<main>` è speciale.** Contiene ciò che distingue questa pagina dalle altre — non il menu, non il piè di pagina, che si ripetono ovunque. Gli screen reader offrono un comando per saltarci dentro direttamente, ed è il modo in cui chi naviga a voce evita di riascoltare il menu su ogni pagina.

**Più `<nav>` vanno etichettate.** Con due o più navigazioni, `aria-label` è ciò che le distingue nell'elenco dei landmark:

```html
<nav aria-label="Principale">…</nav>
<nav aria-label="Percorso di navigazione">…</nav>
<nav aria-label="Piè di pagina">…</nav>
```

Non scrivere `aria-label="Navigazione principale"`: lo screen reader annuncia già il ruolo, e il risultato sarebbe "navigazione navigazione principale".

### Il salto al contenuto

Prima voce del `<body>`, il collegamento che permette a chi usa la tastiera di scavalcare il menu:

```html
<body>
  <a href="#contenuto" class="salta-al-contenuto">Vai al contenuto principale</a>

  <header>…menu con quindici voci…</header>

  <main id="contenuto" tabindex="-1">
    <h1>Bilancio 2026</h1>
  </main>
</body>
```

```css
/* Visibile solo quando riceve il focus da tastiera */
.salta-al-contenuto {
  position: absolute;
  left: -9999px;
}

.salta-al-contenuto:focus {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
  padding: 0.75rem 1rem;
  background: #000;
  color: #fff;
}
```

`tabindex="-1"` su `<main>` serve perché il focus si sposti davvero: senza, alcuni browser spostano solo lo scorrimento e il tasto `Tab` successivo riparte dall'inizio della pagina.

---

## A7. Scegliere l'elemento giusto

Il dubbio ricorrente è `<article>` contro `<section>` contro `<div>`. Si risolve con tre domande in sequenza.

```
                  Ho un blocco di contenuto da racchiudere.
                                   │
                                   ▼
              ┌────────────────────────────────────────┐
              │ Avrebbe senso da solo, estratto dalla  │
              │ pagina e messo in un feed RSS?         │
              └───────────┬───────────────┬────────────┘
                        sì│               │no
                          ▼               ▼
                    ┌──────────┐  ┌──────────────────────────────┐
                    │ <article>│  │ È un raggruppamento tematico │
                    └──────────┘  │ con un proprio titolo?       │
                                  └──────┬────────────┬──────────┘
                                       sì│            │no
                                         ▼            ▼
                                  ┌───────────┐  ┌───────────────────────┐
                                  │ <section> │  │ Serve solo per        │
                                  │ + <h2>    │  │ posizionare o stilare?│
                                  └───────────┘  └──────┬────────────────┘
                                                      sì│
                                                        ▼
                                                   ┌────────┐
                                                   │ <div>  │
                                                   └────────┘
```

```html
<!-- <article> — un post, una notizia, una scheda prodotto, un commento.
     Test: ha senso in un feed RSS? Sì. -->
<article>
  <h2>Nuova sede a Torino</h2>
  <p><time datetime="2026-02-10">10 febbraio 2026</time></p>
  <p>Da lunedì è operativa la sede di Torino.</p>
</article>

<!-- <section> — una parte tematica di un tutto. Vuole un titolo.
     Test: ha senso da sola? No, è un capitolo. -->
<section>
  <h2>Contatti commerciali</h2>
  <p>Per informazioni sui listini: commerciale@acme.it</p>
</section>

<!-- <div> — nessun significato. Onesto e legittimo quando serve
     solo un aggancio per il CSS. -->
<div class="griglia-due-colonne">
  <article>…</article>
  <article>…</article>
</div>
```

**`<div>` non è un errore.** L'errore è usarlo dove esiste un elemento con un significato. Un contenitore che serve solo a fare una griglia è esattamente il caso d'uso di `<div>`: aggiungere `<section>` lì darebbe al documento una struttura che non ha.

**`<section>` senza titolo è quasi sempre `<div>`.** Se non riesci a scrivere l'`<h2>` che gli va dentro, non stai raggruppando un tema: stai raggruppando dei pixel.

### Elementi che risolvono problemi ricorrenti

```html
<!-- Pannello richiudibile, senza una riga di JavaScript -->
<details>
  <summary>Termini e condizioni</summary>
  <p>Il pagamento è dovuto entro trenta giorni dalla data fattura.</p>
</details>

<!-- Aperto di partenza -->
<details open>
  <summary>Riepilogo</summary>
  <p>Tre fatture in scadenza questa settimana.</p>
</details>

<!-- Percorso di navigazione -->
<nav aria-label="Percorso">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/documenti">Documenti</a></li>
    <li><a href="/documenti/bilanci" aria-current="page">Bilanci</a></li>
  </ol>
</nav>

<!-- Indirizzo di contatto — NON per gli indirizzi postali generici -->
<address>
  Scrivi a <a href="mailto:info@acme.it">info@acme.it</a>
</address>

<!-- Abbreviazioni -->
<p>Il <abbr title="Documento Unico di Regolarità Contributiva">DURC</abbr> è valido.</p>

<!-- Testo inserito e rimosso, con data e motivo -->
<p>
  Il termine è
  <del datetime="2026-03-01" cite="/delibere/12">30 giugno</del>
  <ins datetime="2026-03-01" cite="/delibere/12">31 luglio</ins>.
</p>
```

`<details>`/`<summary>` merita attenzione: è un componente interattivo completo — apre, chiude, risponde alla tastiera, viene annunciato correttamente — che molti riscrivono in JavaScript senza motivo. `aria-current="page"` sull'ultima voce del percorso dice allo screen reader qual è la posizione attuale.

---

## A8. Il primo form

```html
<form action="/api/contatti" method="post">
  <label for="nome">Nome e cognome</label>
  <input type="text" id="nome" name="nome" required />

  <label for="email">Indirizzo email</label>
  <input type="email" id="email" name="email" required />

  <label for="messaggio">Messaggio</label>
  <textarea id="messaggio" name="messaggio" rows="5" required></textarea>

  <button type="submit">Invia</button>
</form>
```

Quattro cose da fissare subito, perché sono l'origine della maggior parte dei form difettosi.

**1. `<label for>` deve corrispondere a `id`, non a `name`.**

```html
<!-- ❌ SBAGLIATO — for punta al name: nessun collegamento -->
<label for="nome">Nome</label>
<input type="text" name="nome" />

<!-- ✅ CORRETTO -->
<label for="campo-nome">Nome</label>
<input type="text" id="campo-nome" name="nome" />

<!-- ✅ ANCHE CORRETTO — la label avvolge il campo, niente id necessario -->
<label>
  Nome
  <input type="text" name="nome" />
</label>
```

Senza il collegamento, lo screen reader annuncia "casella di testo" senza dire cosa vada scritto dentro, e il clic sull'etichetta non porta il focus nel campo — un aiuto che conta soprattutto per le caselle di spunta, che sono minuscole.

**2. `name` è la chiave con cui il dato arriva al server.** Un campo senza `name` non viene inviato. È l'errore che produce il classico "il form funziona ma sul server arriva vuoto".

**3. `placeholder` non è una label.**

```html
<!-- ❌ SBAGLIATO — sparisce appena scrivi, il contrasto è basso,
     e alcuni screen reader lo ignorano -->
<input type="text" name="nome" placeholder="Nome e cognome" />

<!-- ✅ CORRETTO — la label resta, il placeholder aggiunge un esempio -->
<label for="campo-nome">Nome e cognome</label>
<input type="text" id="campo-nome" name="nome" placeholder="Mario Rossi" />
```

**4. `type` sul pulsante.** Dentro un `<form>`, un `<button>` senza `type` vale `type="submit"`. Un pulsante "Annulla" senza `type="button"` invia il form.

```html
<!-- ❌ SBAGLIATO — invia il form -->
<button onclick="svuota()">Svuota</button>

<!-- ✅ CORRETTO -->
<button type="button" onclick="svuota()">Svuota</button>
```

### Raggruppare campi correlati

```html
<fieldset>
  <legend>Modalità di consegna</legend>

  <label>
    <input type="radio" name="consegna" value="standard" checked />
    Standard — 3-5 giorni lavorativi
  </label>

  <label>
    <input type="radio" name="consegna" value="espressa" />
    Espressa — 24 ore
  </label>
</fieldset>
```

Il gruppo di radio button è il caso in cui `<fieldset>` è indispensabile: `<legend>` è l'unico modo perché lo screen reader annunci la domanda a cui le opzioni rispondono. Senza, si sente "Standard, pulsante di opzione, 1 di 2" e resta ignoto di cosa si stia parlando.

I radio con lo **stesso `name`** sono mutuamente esclusivi; le checkbox con lo stesso `name` inviano più valori.

---

## A9. Tabelle di dati, annotate come si deve

Le tabelle servono ai dati tabellari. Per il layout esiste il CSS, e ci arriviamo in `tutorial_02_css3.md`.

```html
<table>
  <caption>Ricavi per divisione, esercizio 2026 (migliaia di euro)</caption>

  <thead>
    <tr>
      <th scope="col">Divisione</th>
      <th scope="col">Primo semestre</th>
      <th scope="col">Secondo semestre</th>
      <th scope="col">Totale</th>
    </tr>
  </thead>

  <tbody>
    <tr>
      <th scope="row">Industriale</th>
      <td>1.240</td>
      <td>1.580</td>
      <td>2.820</td>
    </tr>
    <tr>
      <th scope="row">Servizi</th>
      <td>860</td>
      <td>1.110</td>
      <td>1.970</td>
    </tr>
  </tbody>

  <tfoot>
    <tr>
      <th scope="row">Totale</th>
      <td>2.100</td>
      <td>2.690</td>
      <td>4.790</td>
    </tr>
  </tfoot>
</table>
```

Perché ognuno di questi elementi c'è:

- **`<caption>`** — il titolo della tabella, legato ad essa in modo programmatico. Va come primo figlio di `<table>`. Un `<h3>` sopra la tabella non produce lo stesso legame.
- **`<th scope="col">` e `<th scope="row">`** — dicono se l'intestazione governa una colonna o una riga. Grazie a `scope`, lo screen reader che si sposta sulla cella `1.580` annuncia "Industriale, Secondo semestre, 1.580" invece del solo numero. Senza, la tabella è una griglia di cifre senza contesto.
- **`<thead>`, `<tbody>`, `<tfoot>`** — separano intestazione, corpo e totali. Alla stampa il `<thead>` si ripete in cima a ogni pagina.

Per le tabelle con intestazioni su più livelli, `scope` non basta e servono `id` e `headers`:

```html
<table>
  <caption>Ricavi per divisione e trimestre</caption>
  <thead>
    <tr>
      <td></td>
      <th id="t1" scope="col">T1</th>
      <th id="t2" scope="col">T2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="ind" scope="row">Industriale</th>
      <td headers="ind t1">610</td>
      <td headers="ind t2">630</td>
    </tr>
  </tbody>
</table>
```

È verboso e va usato solo quando serve davvero. Una tabella che richiede `headers` è spesso una tabella che converrebbe spezzare in due.

---

# Parte B — Comprensione Profonda

---

## B1. Content model: cosa può contenere cosa

L'HTML non permette qualunque annidamento. Ogni elemento dichiara che **categoria di contenuto** appartiene e quale accetta al suo interno. Violare quelle regole non produce un errore: produce un DOM diverso da quello che hai scritto.

Le categorie che contano nella pratica:

```
FLOW CONTENT       quasi tutto ciò che sta nel <body>
                   <p> <div> <section> <table> <ul> <img> …

PHRASING CONTENT   il testo e ciò che lo marca dall'interno
                   <span> <a> <strong> <em> <code> <img> <input> …
                   ⚠ è un SOTTOINSIEME del flow content

HEADING CONTENT    <h1>…<h6>

SECTIONING CONTENT <article> <section> <nav> <aside>

INTERACTIVE        <a href> <button> <input> <select> <details> …
```

La regola che spiega più errori di tutte: **`<p>` accetta solo phrasing content.**

```html
<!-- ❌ SBAGLIATO — <div> è flow, non phrasing.
     Il parser chiude <p> PRIMA del <div>. -->
<p>
  Testo introduttivo
  <div>Un blocco</div>
  altro testo
</p>
```

Quello che il browser costruisce davvero:

```html
<p>Testo introduttivo</p>
<div>Un blocco</div>
altro testo
<p></p>
```

Un paragrafo vuoto in fondo, il testo finale fuori da ogni paragrafo, e le regole CSS scritte per `p div` che non si applicano mai. Il sintomo è "il CSS non funziona" e la causa è nel markup.

```html
<!-- ✅ CORRETTO -->
<p>Testo introduttivo</p>
<div>Un blocco</div>
<p>altro testo</p>
```

Altri annidamenti che il parser corregge a modo suo:

```html
<!-- ❌ Un <a> dentro un <a>: il parser chiude il primo -->
<a href="/a">esterno <a href="/b">interno</a></a>

<!-- ❌ <ul> accetta SOLO <li> come figlio diretto -->
<ul>
  <p>Introduzione</p>   <!-- viene spostato fuori -->
  <li>Voce</li>
</ul>

<!-- ✅ CORRETTO -->
<p>Introduzione</p>
<ul>
  <li>Voce</li>
</ul>

<!-- ❌ <button> è interattivo: non può contenere altro interattivo -->
<button>Salva e <a href="/aiuto">leggi la guida</a></button>

<!-- ✅ CORRETTO — due controlli distinti -->
<button type="submit">Salva</button>
<a href="/aiuto">Leggi la guida</a>
```

**La regola generale:** un elemento interattivo non contiene altri elementi interattivi. Un `<label>` contiene un solo controllo. `<ul>`, `<ol>`, `<dl>`, `<table>`, `<select>` accettano solo i figli previsti.

Come verificarlo senza impararlo a memoria: il validatore ufficiale del W3C, `validator.w3.org`, segnala ogni violazione con la riga esatta.

```powershell
# In locale, senza pubblicare nulla
pnpm dlx html-validate "src/**/*.html"
```

---

## B2. Il DOM non è l'HTML che hai scritto

Il parser HTML non fallisce mai. Qualunque sequenza di byte gli passi, produce un albero. Questa scelta di progetto — necessaria per non rompere il web esistente — significa che l'HTML sbagliato non dà errore: dà un albero diverso da quello atteso.

> **Analogia:** un traduttore che ha ordine di non interrompersi mai. Se gli detti una frase senza verbo, non ti ferma: ne inventa uno plausibile e prosegue. Il testo tradotto esiste, è comprensibile, e non è quello che intendevi. L'unico modo di accorgersene è rileggere la traduzione, non l'originale.

```html
<!-- Quello che scrivi -->
<table>
  <tr>
    <td>Cella</td>
  </tr>
</table>
```

```html
<!-- Quello che il browser costruisce: <tbody> inserito da solo -->
<table>
  <tbody>
    <tr>
      <td>Cella</td>
    </tr>
  </tbody>
</table>
```

Un selettore CSS `table > tr` non troverà mai nulla, perché fra i due c'è un `<tbody>` che non hai scritto.

**Come vedere l'albero vero.** Sono due cose diverse, e la distinzione è quotidiana:

| Strumento | Cosa mostra |
|---|---|
| `Ctrl+U` — Visualizza sorgente | I byte spediti dal server. Nessuna correzione, nessuna modifica di JavaScript |
| DevTools → **Elements** | Il DOM **adesso**: correzioni del parser incluse, modifiche di JavaScript incluse |

Quando un elemento c'è nel sorgente ma non in Elements, o viceversa, la spiegazione sta sempre in una di queste due colonne.

```javascript
// Verificare da console cosa è stato costruito davvero
document.querySelector('table').innerHTML
// "<tbody><tr><td>Cella</td></tr></tbody>"
```

### Tag da chiudere e tag che si chiudono da soli

```html
<!-- Elementi void: non hanno contenuto, non si chiudono -->
<img src="/logo.svg" alt="Acme" />
<br />
<hr />
<input type="text" name="nome" />
<meta charset="UTF-8" />
<link rel="stylesheet" href="/style.css" />

<!-- La barra finale è opzionale in HTML: <img> e <img /> sono identici.
     Serve in XHTML e in JSX. Metterla sempre è un'abitudine coerente. -->
```

Alcuni tag di chiusura sono opzionali per la specifica (`</li>`, `</p>`, `</tr>`) e il parser li inferisce. Ometterli è legale e sconsigliato: rende il markup dipendente da regole di inferenza che nessuno ricorda con precisione.

---

## B3. Tipi di input e validazione nativa

`type` non cambia solo l'aspetto: cambia la tastiera mostrata sul telefono, la validazione applicata e il modo in cui il browser suggerisce i valori.

```html
<input type="text" />           <!-- testo generico -->
<input type="email" />          <!-- tastiera con @, valida la forma -->
<input type="tel" />            <!-- tastierino numerico, NON valida -->
<input type="url" />            <!-- tastiera con .com, richiede lo schema -->
<input type="number" />         <!-- solo numeri, con frecce -->
<input type="password" />       <!-- nasconde i caratteri -->
<input type="search" />         <!-- mostra la X per svuotare -->
<input type="date" />           <!-- selettore data nativo -->
<input type="time" />
<input type="datetime-local" />
<input type="month" />
<input type="week" />
<input type="color" />          <!-- selettore colore -->
<input type="range" />          <!-- cursore -->
<input type="file" />
<input type="checkbox" />
<input type="radio" />
<input type="hidden" />
```

**`type="tel"` non valida niente.** I numeri di telefono nel mondo hanno formati incompatibili fra loro, quindi il browser mostra il tastierino numerico e si ferma lì. La validazione va scritta con `pattern`.

**`type="number"` è insidioso.** Accetta la notazione scientifica (`1e5`), scarta gli zeri iniziali, e sui browser desktop le frecce cambiano il valore quando l'utente scorre la pagina con la rotellina sul campo. Per i codici numerici che *non sono quantità* — CAP, partita IVA, codice cliente — `type="text"` con `inputmode` è la scelta corretta:

```html
<!-- ❌ SBAGLIATO — un CAP non è un numero su cui fare aritmetica.
     "00121" diventa "121". -->
<input type="number" name="cap" />

<!-- ✅ CORRETTO — testo, tastierino numerico, pattern esplicito -->
<label for="cap">CAP</label>
<input
  type="text"
  id="cap"
  name="cap"
  inputmode="numeric"
  pattern="[0-9]{5}"
  maxlength="5"
  autocomplete="postal-code"
/>
```

### Gli attributi di validazione

```html
<form>
  <!-- required — non vuoto -->
  <label for="nome">Nome</label>
  <input type="text" id="nome" name="nome" required />

  <!-- minlength / maxlength — lunghezza del testo -->
  <label for="codice">Codice cliente</label>
  <input type="text" id="codice" name="codice" minlength="6" maxlength="12" required />

  <!-- min / max / step — intervallo numerico o di date -->
  <label for="quantita">Quantità</label>
  <input type="number" id="quantita" name="quantita" min="1" max="999" step="1" />

  <label for="consegna">Data di consegna</label>
  <input type="date" id="consegna" name="consegna" min="2026-01-01" max="2026-12-31" />

  <!-- pattern — espressione regolare.
       È ancorata implicitamente: deve corrispondere all'INTERO valore. -->
  <label for="piva">Partita IVA</label>
  <input
    type="text"
    id="piva"
    name="piva"
    pattern="[0-9]{11}"
    title="Undici cifre, senza spazi né il prefisso IT"
    required
  />

  <button type="submit">Invia</button>
</form>
```

Due dettagli su `pattern` che fanno perdere tempo:

- **È ancorato.** `pattern="[0-9]{11}"` equivale a `^[0-9]{11}$`. Scrivere `^` e `$` è inutile ma innocuo.
- **`title` diventa il messaggio d'errore.** Senza, il browser dice "Corrispondere al formato richiesto", che non aiuta nessuno. Con `title`, mostra il testo che hai scritto.

### `autocomplete`: l'attributo più trascurato

```html
<input type="text" name="nome" autocomplete="given-name" />
<input type="text" name="cognome" autocomplete="family-name" />
<input type="email" name="email" autocomplete="email" />
<input type="tel" name="telefono" autocomplete="tel" />
<input type="text" name="indirizzo" autocomplete="street-address" />
<input type="text" name="citta" autocomplete="address-level2" />
<input type="text" name="cap" autocomplete="postal-code" />

<!-- Password: distinguere login da registrazione cambia
     il comportamento del gestore di password -->
<input type="password" name="password" autocomplete="current-password" />
<input type="password" name="nuova" autocomplete="new-password" />

<!-- Codice monouso da SMS: il telefono lo propone da solo -->
<input type="text" name="otp" autocomplete="one-time-code" inputmode="numeric" />
```

Compilare un form di dieci campi a mano su un telefono è la ragione principale per cui gli utenti abbandonano. `autocomplete` con i valori standard riduce l'operazione a due tocchi. È anche un criterio WCAG (1.3.5, livello AA): per chi ha difficoltà motorie o cognitive non è una comodità, è la differenza fra riuscire e non riuscire.

`autocomplete="off"` è quasi sempre un errore: i browser lo ignorano nei campi password per non ostacolare i gestori di password, e negli altri campi penalizza solo l'utente.

### Le pseudo-classi che il CSS ti mette a disposizione

```css
/* Stato di validità — attenzione: :invalid si attiva SUBITO,
   anche su un campo mai toccato. */
input:invalid { border-color: crimson; }

/* :user-invalid si attiva solo dopo che l'utente ha interagito.
   È quello che vuoi quasi sempre. */
input:user-invalid { border-color: crimson; }
input:user-valid { border-color: seagreen; }

/* Campo obbligatorio */
input:required { border-inline-start: 3px solid currentColor; }

/* Campo compilato — utile per le label flottanti */
input:not(:placeholder-shown) { … }
```

`:user-invalid` e `:user-valid` risolvono un difetto storico: un form appena aperto con tutti i campi in rosso perché ancora vuoti. Sono disponibili in tutti i browser evergreen.

---

## B4. Constraint Validation API

La validazione nativa mostra un fumetto di sistema, non stilabile, che sparisce da solo e non viene sempre annunciato dagli screen reader. Quando serve controllo, l'API permette di sostituirla mantenendo la logica dichiarativa.

```javascript
// src/validazione.js

const modulo = document.querySelector('#modulo-contatti')

/**
 * Traduce il motivo del fallimento in un messaggio comprensibile.
 * validity è un ValidityState: ogni proprietà dice PERCHÉ il campo non va bene.
 */
function messaggioPerCampo(campo) {
  const v = campo.validity

  if (v.valueMissing) return 'Questo campo è obbligatorio.'
  if (v.typeMismatch && campo.type === 'email') return "Manca la @ o il dominio nell'indirizzo."
  if (v.typeMismatch && campo.type === 'url') return "L'indirizzo deve iniziare con https://"
  if (v.tooShort) return `Servono almeno ${campo.minLength} caratteri (ne hai ${campo.value.length}).`
  if (v.tooLong) return `Massimo ${campo.maxLength} caratteri.`
  if (v.rangeUnderflow) return `Il valore minimo è ${campo.min}.`
  if (v.rangeOverflow) return `Il valore massimo è ${campo.max}.`
  if (v.stepMismatch) return `Il valore deve essere un multiplo di ${campo.step}.`
  if (v.patternMismatch) return campo.title || 'Il formato non è corretto.'
  if (v.badInput) return 'Il valore inserito non è leggibile.'
  if (v.customError) return campo.validationMessage

  return 'Valore non valido.'
}

function mostraErrore(campo, testo) {
  const contenitore = document.querySelector(`#errore-${campo.id}`)
  contenitore.textContent = testo
  campo.setAttribute('aria-invalid', 'true')
}

function pulisciErrore(campo) {
  const contenitore = document.querySelector(`#errore-${campo.id}`)
  contenitore.textContent = ''
  campo.removeAttribute('aria-invalid')
}

// Disattiva il fumetto nativo: da qui in poi gestiamo noi la presentazione.
modulo.setAttribute('novalidate', '')

// L'evento invalid scatta su OGNI campo non valido al submit.
// Non fa bubbling: va ascoltato in fase di cattura.
modulo.addEventListener(
  'invalid',
  (evento) => {
    evento.preventDefault()
    mostraErrore(evento.target, messaggioPerCampo(evento.target))
  },
  true,
)

// Ripulisci mentre l'utente corregge, ma solo se il campo era già in errore:
// segnalare l'errore mentre si sta ancora scrivendo è fastidioso.
modulo.addEventListener('input', (evento) => {
  const campo = evento.target
  if (campo.getAttribute('aria-invalid') === 'true' && campo.checkValidity()) {
    pulisciErrore(campo)
  }
})

modulo.addEventListener('submit', (evento) => {
  // reportValidity() valida tutto e fa scattare 'invalid' sui campi difettosi
  if (!modulo.reportValidity()) {
    evento.preventDefault()
    // Porta il focus sul primo campo in errore: senza, chi usa la tastiera
    // non sa dove sia il problema.
    modulo.querySelector(':invalid')?.focus()
  }
})
```

```html
<!-- Il markup che l'API richiede -->
<form id="modulo-contatti" action="/api/contatti" method="post">
  <div>
    <label for="email">Indirizzo email</label>
    <input
      type="email"
      id="email"
      name="email"
      required
      aria-describedby="errore-email"
    />
    <!-- role="alert" fa sì che il messaggio venga annunciato quando compare -->
    <p id="errore-email" role="alert" class="messaggio-errore"></p>
  </div>

  <button type="submit">Invia</button>
</form>
```

`aria-describedby` collega il messaggio al campo: quando il focus entra nel campo, lo screen reader legge l'etichetta **e** l'errore. `role="alert"` fa annunciare il testo nel momento in cui appare, senza che serva spostare il focus.

### Validazione personalizzata

```javascript
// Regole che nessun attributo può esprimere
const dataInizio = document.querySelector('#data-inizio')
const dataFine = document.querySelector('#data-fine')

function verificaIntervallo() {
  if (dataInizio.value && dataFine.value && dataFine.value < dataInizio.value) {
    // Con un messaggio non vuoto, il campo diventa non valido:
    // il form non si invia e validity.customError è true.
    dataFine.setCustomValidity('La data di fine deve seguire quella di inizio.')
  } else {
    // Stringa vuota = valido. Va SEMPRE azzerato, altrimenti il campo
    // resta non valido per sempre anche dopo la correzione.
    dataFine.setCustomValidity('')
  }
}

dataInizio.addEventListener('change', verificaIntervallo)
dataFine.addEventListener('change', verificaIntervallo)
```

> **La trappola di `setCustomValidity`:** dimenticare di richiamarlo con la stringa vuota quando il valore torna corretto. Il campo resta bloccato, l'utente vede il valore giusto e il form che non parte, e non c'è nulla a schermo che spieghi perché.

**La validazione lato client è un'agevolazione, non un controllo.** Serve a evitare un giro di rete per un errore di battitura. Chiunque può inviare una richiesta HTTP senza passare dalla pagina: la validazione che conta è quella sul server, e la trattiamo in `tutorial_11_api_design.md`.

---

## B5. `FormData` e l'invio senza ricaricare

```javascript
const modulo = document.querySelector('#modulo-contatti')

modulo.addEventListener('submit', async (evento) => {
  evento.preventDefault()

  if (!modulo.reportValidity()) return

  // FormData raccoglie i campi con un name, applicando le regole del form:
  // checkbox non spuntate assenti, radio con un solo valore, file inclusi.
  const dati = new FormData(modulo)

  const pulsante = modulo.querySelector('button[type="submit"]')
  pulsante.disabled = true
  pulsante.textContent = 'Invio…'

  try {
    const risposta = await fetch(modulo.action, {
      method: modulo.method,
      // Nessun Content-Type impostato a mano: con FormData il browser
      // deve generare il boundary di multipart/form-data da sé.
      body: dati,
    })

    if (!risposta.ok) {
      throw new Error(`Il server ha risposto ${risposta.status}`)
    }

    modulo.reset()
    document.querySelector('#esito').textContent = 'Messaggio inviato.'
  } catch (errore) {
    document.querySelector('#esito').textContent =
      `Invio non riuscito: ${errore.message}. Riprova fra qualche istante.`
  } finally {
    pulsante.disabled = false
    pulsante.textContent = 'Invia'
  }
})
```

```html
<!-- L'esito va in una live region, così viene annunciato senza spostare il focus -->
<p id="esito" role="status" aria-live="polite"></p>
```

Cosa sa fare `FormData` che una raccolta manuale non fa:

```javascript
const dati = new FormData(modulo)

dati.get('email')              // il primo valore
dati.getAll('interessi')       // tutti i valori di checkbox omonime
dati.has('newsletter')         // false se la checkbox non è spuntata
dati.append('origine', 'web')  // aggiunge un campo non presente nel markup
dati.delete('token-interno')

// Come oggetto — attenzione: perde i valori multipli
const oggetto = Object.fromEntries(dati)

// Come JSON, se l'API se lo aspetta
await fetch('/api/contatti', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(Object.fromEntries(dati)),
})
```

```javascript
// ❌ SBAGLIATO — impostare Content-Type con FormData rompe l'invio:
//    il browser non può più aggiungere il boundary e il server non
//    riesce a separare i campi.
await fetch(url, {
  method: 'POST',
  headers: { 'Content-Type': 'multipart/form-data' },
  body: new FormData(modulo),
})

// ✅ CORRETTO — lascia decidere al browser
await fetch(url, { method: 'POST', body: new FormData(modulo) })
```

---

## B6. Immagini responsive

Servire a un telefono da 400 pixel la stessa immagine da 2400 pixel del desktop spreca banda e tempo. `srcset` risolve il problema in modo dichiarativo: tu descrivi le varianti disponibili, il browser sceglie.

### `srcset` con descrittori di larghezza

```html
<img
  src="/img/sede-800.jpg"
  srcset="
    /img/sede-400.jpg   400w,
    /img/sede-800.jpg   800w,
    /img/sede-1600.jpg 1600w
  "
  sizes="(min-width: 64rem) 50vw, 100vw"
  alt="La sede di Milano vista dalla strada"
  width="800"
  height="600"
  loading="lazy"
  decoding="async"
/>
```

Come funziona la scelta:

- **`srcset`** elenca i file con la loro larghezza reale in pixel (`400w` = quel file è largo 400px).
- **`sizes`** dichiara quanto spazio occuperà l'immagine nel layout: qui metà viewport sopra i 1024px, tutta la viewport sotto.
- Il browser combina `sizes` con la densità dello schermo e sceglie il file più piccolo che basta.

**`sizes` va scritto in base al CSS che applicherai.** Se il CSS mette l'immagine in una colonna larga il 50% e `sizes` dice `100vw`, il browser scarica un file grande il doppio del necessario. È l'errore che vanifica tutto il meccanismo.

`src` resta come ripiego per i browser che non capiscono `srcset` — oggi praticamente nessuno, ma non costa nulla.

### `srcset` con densità

Quando l'immagine ha una dimensione fissa nel layout, la variabile è solo la densità dello schermo:

```html
<img
  src="/img/logo.png"
  srcset="/img/logo.png 1x, /img/logo@2x.png 2x, /img/logo@3x.png 3x"
  alt="Acme S.p.A."
  width="200"
  height="60"
/>
```

I due descrittori — `w` e `x` — non si mescolano nello stesso `srcset`.

### `<picture>`: quando cambia il file, non solo la dimensione

```html
<picture>
  <!-- Formati moderni per primi: il browser prende la prima <source>
       che sa decodificare -->
  <source srcset="/img/prodotto.avif" type="image/avif" />
  <source srcset="/img/prodotto.webp" type="image/webp" />

  <!-- Ritaglio diverso su schermi stretti: art direction -->
  <source media="(max-width: 40rem)" srcset="/img/prodotto-verticale.jpg" />

  <!-- <img> è obbligatorio: porta alt, width, height e fa da ripiego -->
  <img
    src="/img/prodotto.jpg"
    alt="Pompa centrifuga serie X, vista laterale"
    width="1200"
    height="800"
    loading="lazy"
  />
</picture>
```

`srcset` e `<picture>` risolvono problemi diversi:

| Serve | Strumento |
|---|---|
| Stessa immagine, dimensioni diverse | `srcset` + `sizes` |
| Formati diversi (AVIF, WebP, JPEG) | `<picture>` con `type` |
| Ritaglio o soggetto diverso per schermo | `<picture>` con `media` |
| Modalità scura | `<picture>` con `media="(prefers-color-scheme: dark)"` |

### `loading`, `decoding`, `fetchpriority`

```html
<!-- Immagine principale, visibile subito: NON differirla.
     fetchpriority="high" la anticipa rispetto alle altre risorse. -->
<img src="/img/copertina.jpg" alt="…" fetchpriority="high" width="1600" height="900" />

<!-- Immagini sotto la piega: differite fino all'avvicinamento -->
<img src="/img/galleria-1.jpg" alt="…" loading="lazy" decoding="async" width="800" height="600" />
```

```html
<!-- ❌ SBAGLIATO — loading="lazy" sull'immagine principale ritarda
     il Largest Contentful Paint, cioè peggiora esattamente la metrica
     che si voleva migliorare -->
<img src="/img/copertina.jpg" alt="…" loading="lazy" />
```

`loading="lazy"` va alle immagini **sotto la piega**. Su quella in cima produce l'effetto opposto a quello desiderato. `fetchpriority` è supportato in Chromium e Safari; dove manca viene ignorato senza danno.

**`width` e `height` sempre.** Anche quando il CSS li sovrascrive: servono al browser per calcolare il rapporto d'aspetto e riservare lo spazio, evitando che il contenuto sotto salti quando l'immagine arriva.

---

## B7. Video e audio

```html
<video
  src="/media/presentazione.mp4"
  poster="/media/presentazione-copertina.jpg"
  controls
  preload="metadata"
  width="1280"
  height="720"
>
  <track
    kind="captions"
    src="/media/presentazione-it.vtt"
    srclang="it"
    label="Italiano"
    default
  />
  <track kind="descriptions" src="/media/presentazione-audiodesc-it.vtt" srclang="it" label="Descrizioni" />
  <p>Il tuo browser non riproduce video. <a href="/media/presentazione.mp4">Scarica il file</a>.</p>
</video>
```

Gli attributi che contano:

| Attributo | Effetto |
|---|---|
| `controls` | Mostra i comandi nativi. Senza, il video non è controllabile se non scrivi tu un'interfaccia completa e accessibile |
| `poster` | Immagine mostrata prima della riproduzione. Evita il rettangolo nero |
| `preload="none"` | Non scarica nulla finché non si preme play |
| `preload="metadata"` | Scarica solo durata e dimensioni. **Il default sensato** |
| `preload="auto"` | Scarica in anticipo. Solo se sei certo che verrà guardato |
| `muted` | Necessario perché `autoplay` funzioni: i browser bloccano l'audio non richiesto |
| `playsinline` | Su iOS evita che il video passi a schermo intero da solo |

### `<track>` non è opzionale

I sottotitoli sono un criterio WCAG di livello A (1.2.2). Il formato è WebVTT, un file di testo:

```
WEBVTT

00:00:00.000 --> 00:00:04.500
Benvenuti alla presentazione del bilancio 2026.

00:00:04.500 --> 00:00:09.200
I ricavi consolidati raggiungono i 4,8 milioni di euro.
```

I `kind` disponibili: `captions` (dialoghi **e** suoni rilevanti, per chi non sente), `subtitles` (traduzione, per chi non capisce la lingua), `descriptions` (descrizione di ciò che accade a schermo, per chi non vede), `chapters`.

### Formati multipli

```html
<video controls preload="metadata" poster="/media/copertina.jpg" width="1280" height="720">
  <source src="/media/video.webm" type="video/webm" />
  <source src="/media/video.mp4" type="video/mp4" />
  <track kind="captions" src="/media/video-it.vtt" srclang="it" label="Italiano" default />
  <p>Video non riproducibile. <a href="/media/video.mp4">Scarica</a>.</p>
</video>
```

Con `<source>`, l'attributo `src` su `<video>` va tolto: se c'è, le `<source>` vengono ignorate.

### Autoplay, e perché quasi sempre no

```html
<!-- L'unica forma che i browser accettano: senza audio -->
<video autoplay muted loop playsinline preload="auto" width="1280" height="720">
  <source src="/media/sfondo.mp4" type="video/mp4" />
</video>
```

Un video in riproduzione automatica consuma dati sul traffico mobile, distrae, e per chi ha disturbi vestibolari può provocare malessere. Se serve davvero, rispetta la preferenza di sistema:

```css
@media (prefers-reduced-motion: reduce) {
  video[autoplay] {
    display: none;
  }
}
```

Meglio ancora: fornire un comando di pausa. Il criterio WCAG 2.2.2 richiede che qualunque cosa si muova per più di cinque secondi possa essere fermata.

---

## B8. L'albero di accessibilità e il nome accessibile

Accanto al DOM, il browser costruisce un secondo albero: l'**albero di accessibilità**. È quello che le tecnologie assistive leggono. Contiene meno nodi del DOM — gli elementi puramente visivi spariscono — e per ogni nodo espone quattro informazioni.

```
                         ELEMENTO
                             │
        ┌──────────┬─────────┴─────────┬──────────────┐
        ▼          ▼                   ▼              ▼
     RUOLO       NOME               STATO          VALORE
   (cos'è)   (come si chiama)   (com'è adesso)   (quanto vale)

  button      "Salva bozza"       disabled        —
  checkbox    "Accetto i termini" checked         —
  textbox     "Indirizzo email"   invalid         "mario@"
  slider      "Volume"            —               7 (min 0, max 10)
```

Il **ruolo** arriva dall'elemento: `<button>` ha ruolo `button`, `<nav>` ha ruolo `navigation`. Questo è il motivo per cui usare l'elemento giusto vale più di qualunque attributo ARIA: il ruolo c'è già, corretto, senza scrivere nulla.

### Come si calcola il nome accessibile

L'ordine di precedenza è fisso, e conoscerlo spiega comportamenti che altrimenti sembrano arbitrari:

```
1. aria-labelledby   ← vince su tutto
2. aria-label
3. il contenuto naturale
     <button>Salva</button>          → "Salva"
     <label for="x">Email</label>    → "Email"
     <img alt="Logo Acme">           → "Logo Acme"
     <table><caption>…</caption>     → il caption
4. title             ← ultimo ripiego, da non usare come unica fonte
```

```html
<!-- Nome dal contenuto: il caso normale, e il migliore -->
<button type="submit">Salva bozza</button>

<!-- aria-label: quando non c'è testo visibile.
     Serve perché "×" letto ad alta voce non significa nulla. -->
<button type="button" aria-label="Chiudi la finestra">×</button>

<!-- aria-labelledby: il nome è un testo che esiste già nella pagina.
     Da preferire ad aria-label: resta tradotto e resta sincronizzato. -->
<h2 id="titolo-sezione">Documenti riservati</h2>
<section aria-labelledby="titolo-sezione">…</section>

<!-- aria-labelledby può concatenare più riferimenti, nell'ordine indicato -->
<span id="etichetta-elimina">Elimina</span>
<span id="nome-file-3">bilancio-2026.pdf</span>
<button aria-labelledby="etichetta-elimina nome-file-3">🗑</button>
<!-- nome accessibile: "Elimina bilancio-2026.pdf" -->
```

### L'errore che rende il pulsante muto

```html
<!-- ❌ SBAGLIATO — aria-label sovrascrive il contenuto.
     Lo screen reader annuncia "Invia", chi usa il comando vocale
     dice "clicca Salva bozza" e non succede nulla. -->
<button aria-label="Invia">Salva bozza</button>

<!-- ❌ SBAGLIATO — icona senza nome: "pulsante", e basta -->
<button><svg>…</svg></button>

<!-- ✅ CORRETTO — l'icona è decorativa, il nome è esplicito -->
<button type="button" aria-label="Elimina la riga">
  <svg aria-hidden="true" focusable="false">…</svg>
</button>

<!-- ✅ ANCORA MEGLIO — testo visibile, nascosto solo visivamente.
     Funziona anche con il comando vocale e non richiede traduzione a parte. -->
<button type="button">
  <svg aria-hidden="true" focusable="false">…</svg>
  <span class="solo-screen-reader">Elimina la riga</span>
</button>
```

```css
/* La classe che nasconde visivamente senza nascondere alle tecnologie assistive.
   NON usare display:none o visibility:hidden: rimuovono l'elemento
   anche dall'albero di accessibilità. */
.solo-screen-reader {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}
```

`aria-hidden="true"` sull'SVG lo toglie dall'albero di accessibilità; `focusable="false"` evita che riceva il focus su Internet Explorer e su alcune versioni di Edge legacy. Insieme sono la formula standard per le icone decorative.

### Verificarlo, invece di dedurlo

DevTools → **Elements** → scheda **Accessibility**: mostra ruolo, nome calcolato, e la fonte da cui il nome proviene. È il modo per accorgersi che un `aria-label` sta silenziosamente sovrascrivendo il testo visibile.

---

## B9. ARIA: le cinque regole

ARIA aggiunge semantica dove l'HTML non arriva. È potente e pericoloso: un attributo ARIA non cambia il comportamento, cambia solo ciò che viene **annunciato**. Dichiarare `role="button"` su un `<div>` non gli dà la risposta alla tastiera: promette all'utente qualcosa che il codice non mantiene.

> **Prima regola di ARIA: non usare ARIA.** Se esiste un elemento HTML con il ruolo che ti serve, usa quello. `<button>` batte `<div role="button" tabindex="0">` su ogni fronte, e richiede meno codice.

Le cinque regole, nella forma in cui vale la pena ricordarle:

```
1. Non usare ARIA se esiste l'elemento HTML nativo.
2. Non alterare la semantica nativa senza una ragione forte.
     ❌ <h2 role="tab">     ✅ <div role="tab"><h2>…</h2></div>
3. Ogni controllo ARIA interattivo deve essere usabile da tastiera.
4. Non mettere role="presentation" o aria-hidden="true"
   su un elemento che può ricevere il focus: sparisce dall'albero
   ma resta raggiungibile con Tab. L'utente arriva sul nulla.
5. Ogni controllo interattivo deve avere un nome accessibile.
```

### Live regions

Il caso in cui ARIA è insostituibile: comunicare un cambiamento avvenuto altrove nella pagina, senza spostare il focus.

```html
<!-- polite — attende una pausa nel parlato. Per gli aggiornamenti normali. -->
<p role="status" aria-live="polite" id="esito"></p>

<!-- assertive — interrompe subito. Solo per ciò che è davvero urgente. -->
<p role="alert" id="errore-critico"></p>

<!-- La barra di avanzamento: valore annunciato agli aggiornamenti -->
<div
  role="progressbar"
  aria-valuenow="35"
  aria-valuemin="0"
  aria-valuemax="100"
  aria-label="Caricamento del file"
>
  35%
</div>
```

```javascript
// La live region deve ESISTERE nel DOM prima che il testo cambi.
// Inserire l'elemento e il testo insieme non produce alcun annuncio:
// lo screen reader osserva le modifiche dentro le regioni già registrate.

// ❌ SBAGLIATO
const avviso = document.createElement('p')
avviso.setAttribute('role', 'status')
avviso.textContent = 'Salvato.'
document.body.append(avviso) // nessun annuncio

// ✅ CORRETTO — il contenitore c'è già, vuoto, dall'inizio
document.querySelector('#esito').textContent = 'Salvato.'
```

`role="status"` implica `aria-live="polite"`, `role="alert"` implica `aria-live="assertive"`. Scriverli entrambi è ridondante ma migliora il supporto su qualche combinazione datata di browser e screen reader.

**`assertive` va usato con parsimonia.** Interrompe la lettura in corso. Un avviso assertivo ogni volta che si preme un tasto rende la pagina inutilizzabile.

### Gli attributi di stato che userai davvero

```html
<!-- Menu a scomparsa -->
<button aria-expanded="false" aria-controls="menu-utente">Il mio account</button>
<ul id="menu-utente" hidden>…</ul>

<!-- Campo in errore, collegato al messaggio -->
<input type="email" aria-invalid="true" aria-describedby="err-email" />
<p id="err-email" role="alert">Indirizzo non valido.</p>

<!-- Elemento premuto (toggle) — diverso da un pulsante normale -->
<button aria-pressed="true">Grassetto</button>

<!-- Selezione in una lista di opzioni -->
<li role="option" aria-selected="true">Milano</li>

<!-- Pagina corrente nella navigazione -->
<a href="/documenti" aria-current="page">Documenti</a>

<!-- Contenuto in caricamento: nasconde gli aggiornamenti parziali -->
<div aria-busy="true">…</div>
```

`aria-expanded` va **sul comando che apre**, non sul pannello che si apre. È l'errore più frequente nei menu a discesa, e il risultato è che lo screen reader non dice mai se il menu è aperto o chiuso.

```javascript
const comando = document.querySelector('#comando-menu')
const pannello = document.querySelector('#menu-utente')

comando.addEventListener('click', () => {
  const aperto = comando.getAttribute('aria-expanded') === 'true'
  comando.setAttribute('aria-expanded', String(!aperto))
  pannello.hidden = aperto
})
```

---

## B10. Tastiera e gestione del focus

Chi non usa il mouse — per disabilità motoria, perché usa uno screen reader, o semplicemente perché è più veloce — naviga con `Tab`. Se un'azione è raggiungibile solo con il mouse, per quelle persone non esiste.

### Cosa è raggiungibile di suo

```
Nativamente nell'ordine di tabulazione:
  <a href>  <button>  <input>  <select>  <textarea>
  <details>/<summary>  elementi con contenteditable
  <audio controls>  <video controls>  <iframe>

NON raggiungibili:
  <div>  <span>  <p>  <li>  <a> senza href
```

```html
<!-- ❌ SBAGLIATO — un div cliccabile. Non riceve il focus, non risponde
     a Invio né a Spazio, non viene annunciato come pulsante. -->
<div class="pulsante" onclick="salva()">Salva</div>

<!-- ⚠ MEGLIO MA ANCORA SBAGLIATO — ora riceve il focus e viene annunciato,
     ma continua a non rispondere alla tastiera. -->
<div class="pulsante" role="button" tabindex="0" onclick="salva()">Salva</div>

<!-- ⚠ FUNZIONA, ma sono sei righe per riottenere ciò che <button> dà gratis -->
<div
  class="pulsante"
  role="button"
  tabindex="0"
  onclick="salva()"
  onkeydown="if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); salva() }"
>
  Salva
</div>

<!-- ✅ CORRETTO -->
<button type="button" onclick="salva()">Salva</button>
```

### `tabindex`, i tre valori

```html
<!-- tabindex="0" — entra nell'ordine naturale, nella posizione del documento.
     Serve solo su elementi non nativamente focalizzabili. -->
<div role="button" tabindex="0">…</div>

<!-- tabindex="-1" — focalizzabile via JavaScript, fuori dall'ordine di Tab.
     Il caso d'uso corretto: spostare il focus dopo un'azione. -->
<main id="contenuto" tabindex="-1">…</main>

<!-- ❌ tabindex positivo — non usarlo mai.
     Crea un ordine parallelo che precede TUTTI gli elementi con tabindex 0,
     ovunque siano nella pagina. Diventa ingestibile al secondo componente. -->
<input tabindex="3" />
```

**L'ordine di tabulazione segue il DOM, non il CSS.** Se `order` di Flexbox o `grid-area` spostano visivamente un elemento, il focus continua a seguire l'ordine del markup. Il risultato è un focus che salta in modo incomprensibile a chi guarda. La soluzione è riordinare il markup, non il layout.

### Non cancellare l'indicatore di focus

```css
/* ❌ SBAGLIATO — il contorno sparisce e chi naviga da tastiera
   non sa più dove si trova. È la singola regola CSS che rompe
   più accessibilità di qualunque altra. */
*:focus {
  outline: none;
}

/* ✅ CORRETTO — sostituiscilo con qualcosa di meglio, non toglierlo */
:focus-visible {
  outline: 3px solid #0055ff;
  outline-offset: 2px;
  border-radius: 2px;
}

/* :focus-visible si attiva sul focus da tastiera e non sul clic del mouse.
   È il compromesso che i designer chiedevano da vent'anni. */
```

WCAG 2.4.11 (livello AA, nuovo in 2.2) richiede che l'indicatore di focus non sia coperto da altri elementi e abbia un contrasto sufficiente. Un `outline-offset` positivo e un colore ad alto contrasto soddisfano entrambi i requisiti.

### Trappola del focus in una modale

Quando una finestra modale è aperta, `Tab` non deve uscirne. `<dialog>` con `showModal()` lo fa da solo — è la ragione principale per preferirlo a una modale scritta a mano. Vedi [B11](#b11-dialog-e-la-popover-api).

---

## B11. `<dialog>` e la Popover API

### `<dialog>`

```html
<button type="button" id="apri-conferma">Elimina il documento</button>

<dialog id="conferma-eliminazione" aria-labelledby="titolo-conferma">
  <h2 id="titolo-conferma">Confermi l'eliminazione?</h2>
  <p>L'operazione non è reversibile.</p>

  <!-- method="dialog" chiude la dialog e registra il valore
       in dialog.returnValue, senza inviare nulla -->
  <form method="dialog">
    <button value="annulla">Annulla</button>
    <button value="conferma">Elimina</button>
  </form>
</dialog>
```

```javascript
const finestra = document.querySelector('#conferma-eliminazione')
const comando = document.querySelector('#apri-conferma')

comando.addEventListener('click', () => {
  // showModal() — non show():
  //   · mette la dialog nel top layer, sopra ogni z-index
  //   · rende inerte il resto della pagina
  //   · confina il focus dentro la dialog
  //   · abilita Esc per chiudere
  //   · abilita ::backdrop
  finestra.showModal()
})

finestra.addEventListener('close', () => {
  if (finestra.returnValue === 'conferma') {
    eliminaDocumento()
  }
  // Riportare il focus sul comando che ha aperto la dialog:
  // i browser lo fanno, ma non tutti in ogni situazione.
  comando.focus()
})
```

```css
/* Lo sfondo oscurato: pseudo-elemento nativo, disponibile solo con showModal() */
#conferma-eliminazione::backdrop {
  background: rgb(0 0 0 / 0.5);
  backdrop-filter: blur(2px);
}

/* La dialog è centrata di suo. Serve solo limitarne la larghezza. */
dialog {
  max-inline-size: 32rem;
  padding: 1.5rem;
  border: none;
  border-radius: 0.5rem;
}
```

`show()` contro `showModal()`, la differenza che conta:

| | `show()` | `showModal()` |
|---|---|---|
| Top layer | no | sì |
| Resto della pagina inerte | no | sì |
| Focus confinato | no | sì |
| `Esc` chiude | no | sì |
| `::backdrop` | no | sì |

Per una finestra di conferma vuoi sempre `showModal()`. `show()` serve per pannelli non bloccanti, dove però `popover` è spesso la scelta migliore.

**Cosa ti risparmia:** una modale scritta a mano richiede di gestire il top layer, l'inertizzazione dello sfondo, il confinamento del focus, `Esc`, il ripristino del focus alla chiusura e lo scroll della pagina sottostante. Sono le sei cose che quasi nessuna implementazione artigianale gestisce tutte.

### La Popover API

Per ciò che appare sopra il contenuto senza bloccarlo: menu, tooltip, pannelli di notifica.

```html
<!-- popovertarget collega il comando al pannello: nessun JavaScript -->
<button type="button" popovertarget="pannello-notifiche">Notifiche</button>

<div id="pannello-notifiche" popover>
  <h2>Notifiche recenti</h2>
  <ul>
    <li>Tre fatture in scadenza</li>
  </ul>
</div>
```

Quello che ottieni senza scrivere codice: il pannello va nel top layer sopra ogni `z-index`, `Esc` lo chiude, un clic fuori lo chiude, e l'attributo `aria-expanded` sul comando viene gestito dal browser.

```html
<!-- popover="auto" (il default) — si chiude con Esc e con il clic fuori -->
<div id="menu" popover="auto">…</div>

<!-- popover="manual" — si chiude solo dai comandi che indichi tu.
     Per i toast e le notifiche che devono restare. -->
<div id="avviso" popover="manual">
  <p>File salvato.</p>
  <button type="button" popovertarget="avviso" popovertargetaction="hide">Chiudi</button>
</div>
```

```css
#pannello-notifiche {
  /* Il popover è position: fixed di suo, dentro il top layer */
  inline-size: min(24rem, 90vw);
  padding: 1rem;
  border: 1px solid;
  border-radius: 0.5rem;

  /* Ancorarlo al comando richiede la CSS Anchor Positioning API,
     che non è ancora disponibile ovunque. Nel frattempo si posiziona
     a mano o si accetta il centro dello schermo. */
}
```

```javascript
// Controllo da JavaScript, quando serve
const pannello = document.querySelector('#pannello-notifiche')
pannello.showPopover()
pannello.hidePopover()
pannello.togglePopover()

// Evento di apertura e chiusura
pannello.addEventListener('toggle', (evento) => {
  if (evento.newState === 'open') caricaNotifiche()
})
```

**`<dialog>` o `popover`?**

```
Richiede una decisione prima di proseguire?     →  <dialog> + showModal()
   (conferma di eliminazione, form bloccante)

Informa o offre opzioni senza bloccare?         →  popover
   (menu, tooltip, pannello notifiche, toast)
```

La Popover API è disponibile in tutti i browser evergreen dal 2024. Su basi installate più datate serve una verifica:

```javascript
if (!HTMLElement.prototype.hasOwnProperty('popover')) {
  // Ripiego: <details>/<summary> copre gran parte dei casi
  // senza librerie e con l'accessibilità già corretta.
}
```

---

## B12. Meta tag, Open Graph e dati strutturati

```html
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />

  <title>Bilancio 2026 — Acme S.p.A.</title>
  <meta
    name="description"
    content="Il bilancio consolidato 2026 di Acme S.p.A.: ricavi in crescita del 12%, patrimonio netto a 8,4 milioni."
  />

  <!-- L'indirizzo canonico: evita che la stessa pagina raggiungibile
       da più URL venga trattata come contenuto duplicato -->
  <link rel="canonical" href="https://acme.it/bilancio-2026" />

  <!-- Colore della barra del browser su mobile -->
  <meta name="theme-color" content="#0b3d91" media="(prefers-color-scheme: light)" />
  <meta name="theme-color" content="#0a1a33" media="(prefers-color-scheme: dark)" />

  <!-- Icone -->
  <link rel="icon" href="/favicon.ico" sizes="32x32" />
  <link rel="icon" href="/icona.svg" type="image/svg+xml" />
  <link rel="apple-touch-icon" href="/icona-180.png" />
</head>
```

`<meta name="keywords">` non è usato da nessun motore di ricerca rilevante da oltre quindici anni. Ometterlo.

### Open Graph: l'anteprima nelle chat e sui social

```html
<meta property="og:type" content="article" />
<meta property="og:title" content="Bilancio 2026 — Acme S.p.A." />
<meta
  property="og:description"
  content="Ricavi in crescita del 12%, patrimonio netto a 8,4 milioni."
/>
<meta property="og:url" content="https://acme.it/bilancio-2026" />
<meta property="og:site_name" content="Acme S.p.A." />
<meta property="og:locale" content="it_IT" />

<!-- L'immagine DEVE essere assoluta: i crawler non risolvono i percorsi relativi -->
<meta property="og:image" content="https://acme.it/img/anteprima-bilancio.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="Grafico dei ricavi 2024-2026 in crescita" />

<!-- Twitter/X usa una propria serie, con il fallback su Open Graph -->
<meta name="twitter:card" content="summary_large_image" />
```

Le misure `1200×630` non sono arbitrarie: è il rapporto 1,91:1 che le principali piattaforme ritagliano senza tagliare nulla. Un'immagine con proporzioni diverse viene tagliata al centro, spesso perdendo il testo.

Nota la differenza di attributo: Open Graph usa `property`, i meta standard e Twitter usano `name`. Scambiarli fa ignorare il tag.

### Dati strutturati con JSON-LD

Descrivono il contenuto in modo che un motore di ricerca possa costruirci sopra un risultato arricchito.

```html
<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Acme S.p.A.",
    "url": "https://acme.it",
    "logo": "https://acme.it/img/logo.png",
    "address": {
      "@type": "PostalAddress",
      "streetAddress": "Via Roma 12",
      "addressLocality": "Milano",
      "postalCode": "20121",
      "addressCountry": "IT"
    },
    "contactPoint": {
      "@type": "ContactPoint",
      "telephone": "+39-02-1234-5678",
      "contactType": "customer service",
      "availableLanguage": ["Italian", "English"]
    }
  }
</script>
```

JSON-LD sta in un blocco separato e non si intreccia con il markup: è il formato raccomandato rispetto a Microdata proprio per questo. Deve però descrivere **contenuto realmente presente nella pagina**; dichiarare dati che l'utente non vede è una violazione delle linee guida dei motori di ricerca e produce penalizzazioni.

Si verifica con il *Rich Results Test* di Google e con il validatore di `schema.org`.

---

## B13. SVG inline

Un SVG può stare in un `<img>` o direttamente nel markup. Le due forme hanno capacità diverse.

```html
<!-- Come immagine: leggero, in cache, ma il CSS della pagina non lo raggiunge -->
<img src="/img/icona-cerca.svg" alt="" width="24" height="24" />

<!-- Inline: stilabile, animabile, ma pesa su ogni pagina -->
<svg
  width="24"
  height="24"
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  aria-hidden="true"
  focusable="false"
>
  <circle cx="11" cy="11" r="7" />
  <line x1="16.5" y1="16.5" x2="21" y2="21" />
</svg>
```

`stroke="currentColor"` è il motivo principale per andare inline: l'icona assume il colore del testo che la circonda, cambia con il tema scuro e con lo stato `:hover` senza duplicare i file.

### `viewBox`, spiegato una volta sola

```
viewBox="0 0 24 24"
          │ │ │  └── altezza del sistema di coordinate interno
          │ │ └───── larghezza
          │ └─────── y dell'angolo in alto a sinistra
          └───────── x

width e height  =  quanto spazio occupa nella pagina
viewBox         =  che sistema di coordinate usa il disegno dentro

Con entrambi, l'SVG scala senza deformarsi:
  width="48" height="48" viewBox="0 0 24 24"  → disegno raddoppiato, nitido
```

Un SVG **senza** `viewBox` non scala: resta della dimensione fissa dichiarata. È la causa più comune di icone che si rifiutano di ingrandirsi.

### Accessibilità dell'SVG

```html
<!-- Decorativo: fuori dall'albero di accessibilità -->
<svg aria-hidden="true" focusable="false">…</svg>

<!-- Significativo: ruolo img e nome accessibile -->
<svg role="img" aria-labelledby="titolo-grafico" viewBox="0 0 400 200">
  <title id="titolo-grafico">Ricavi in crescita da 4,2 a 6,8 milioni fra 2024 e 2026</title>
  …
</svg>

<!-- Descrizione estesa, per un grafico complesso -->
<svg role="img" aria-labelledby="tit-g desc-g" viewBox="0 0 400 200">
  <title id="tit-g">Ricavi per trimestre</title>
  <desc id="desc-g">
    Otto barre verticali. La crescita è costante fino al terzo trimestre 2025,
    con una flessione nel quarto e ripresa nel 2026.
  </desc>
  …
</svg>
```

`<title>` dentro `<svg>` non è il `<title>` del documento: è il nome accessibile dell'immagine, e deve essere il **primo figlio** di `<svg>` per essere riconosciuto.

### Animazioni e preferenza di movimento

```html
<svg viewBox="0 0 50 50" class="indicatore-caricamento" role="img" aria-label="Caricamento in corso">
  <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="4"
          stroke-dasharray="90 30" />
</svg>
```

```css
.indicatore-caricamento circle {
  animation: ruota 1s linear infinite;
  transform-origin: center;
}

@keyframes ruota {
  to { transform: rotate(360deg); }
}

/* Rispetta chi ha chiesto meno movimento a livello di sistema.
   Per i disturbi vestibolari non è una preferenza estetica. */
@media (prefers-reduced-motion: reduce) {
  .indicatore-caricamento circle {
    animation: none;
    stroke-dasharray: none;
    opacity: 0.6;
  }
}
```

### Ottimizzazione

Gli SVG esportati dagli strumenti di disegno contengono metadati, livelli nascosti e coordinate a quindici decimali.

```powershell
pnpm dlx svgo --folder src/icone --output src/icone-ottimizzate
```

Riduzioni del 50-70% sono normali. Va verificato il risultato: SVGO con impostazioni aggressive può rimuovere gli `id` a cui puntano `aria-labelledby` o i riferimenti interni.

---

## B14. Internazionalizzazione

### `lang`

```html
<html lang="it">
  <body>
    <p>Il documento è disponibile anche in inglese.</p>

    <!-- Cambio di lingua nel testo: lo screen reader cambia pronuncia -->
    <p>La società adotta un modello <span lang="en">customer-centric</span>.</p>

    <!-- Le citazioni in lingua originale -->
    <blockquote lang="en">
      <p>Everything should be made as simple as possible, but not simpler.</p>
    </blockquote>
  </body>
</html>
```

Senza `lang="en"` sull'inserto, la sintesi vocale italiana legge "customer-centric" con le regole fonetiche italiane. Con l'attributo, cambia voce. Sono i criteri WCAG 3.1.1 e 3.1.2.

I codici seguono la BCP 47: `it`, `it-IT`, `en-GB`, `de-CH`, `zh-Hans` (cinese semplificato), `zh-Hant` (tradizionale).

### `dir` e il testo bidirezionale

```html
<html lang="ar" dir="rtl">
  …
</html>

<!-- Un inserto in una direzione diversa -->
<p>Il titolo originale è <span lang="ar" dir="rtl">الكتاب الأول</span>.</p>

<!-- dir="auto" — la direzione la deduce il browser dal primo carattere forte.
     Indispensabile per il contenuto generato dagli utenti,
     di cui non conosci la lingua in anticipo. -->
<blockquote dir="auto">…testo di provenienza sconosciuta…</blockquote>
```

`dir="rtl"` non capovolge solo il testo: inverte l'ordine delle colonne, la posizione delle barre di scorrimento e il verso delle icone direzionali. È il motivo per cui in CSS conviene usare le proprietà logiche (`margin-inline-start` invece di `margin-left`), che seguono la direzione del testo senza bisogno di un foglio di stile separato. Ne parliamo in `tutorial_02_css3.md`.

```html
<!-- <bdi> isola un frammento: impedisce che la sua direzione
     scombini la punteggiatura del testo circostante.
     Il caso classico: nomi utente in una lista. -->
<ul>
  <li><bdi>مستخدم</bdi>: 12 messaggi</li>
  <li><bdi>Anna</bdi>: 8 messaggi</li>
</ul>

<!-- <bdo> forza una direzione. Serve raramente, solo per
     mostrare esplicitamente testo invertito. -->
<p><bdo dir="rtl">Questo testo è forzato da destra a sinistra</bdo></p>
```

### `hreflang` e `translate`

```html
<!-- Nel <head>: le versioni linguistiche della stessa pagina -->
<link rel="alternate" hreflang="it" href="https://acme.it/bilancio-2026" />
<link rel="alternate" hreflang="en" href="https://acme.it/en/annual-report-2026" />
<link rel="alternate" hreflang="x-default" href="https://acme.it/bilancio-2026" />

<!-- Sui link: dichiara la lingua della destinazione -->
<a href="/en/annual-report-2026" hreflang="en" lang="en">English version</a>

<!-- translate="no": ciò che la traduzione automatica non deve toccare -->
<p>Contatta <span translate="no">Acme S.p.A.</span> per informazioni.</p>
<p>Esegui <code translate="no">pnpm build</code> prima del deploy.</p>
```

`translate="no"` su nomi propri, marchi, comandi e identificatori evita traduzioni automatiche che rendono le istruzioni inutilizzabili.

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Convertire una zuppa di `<div>` in markup semantico

**Obiettivo:** riscrivere questa pagina usando gli elementi corretti, senza cambiare il contenuto.

```html
<!-- PARTENZA — funziona visivamente, non comunica nulla -->
<div class="testata">
  <div class="logo">Acme S.p.A.</div>
  <div class="menu">
    <div class="voce"><a href="/">Home</a></div>
    <div class="voce"><a href="/prodotti">Prodotti</a></div>
  </div>
</div>
<div class="contenuto">
  <div class="titolo-grande">Nuova sede a Torino</div>
  <div class="data">10 febbraio 2026</div>
  <div class="testo">Da lunedì è operativa la sede di Torino.</div>
</div>
<div class="laterale">
  <div class="titolo-medio">Correlati</div>
  <div class="voce"><a href="/sedi">Tutte le sedi</a></div>
</div>
<div class="fondo">© 2026 Acme S.p.A.</div>
```

```html
<!-- SOLUZIONE -->
<header>
  <a href="/"><img src="/img/logo.svg" alt="Acme S.p.A. — pagina iniziale" width="140" height="40" /></a>

  <nav aria-label="Principale">
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/prodotti">Prodotti</a></li>
    </ul>
  </nav>
</header>

<main>
  <!-- <article>: la notizia ha senso anche estratta dalla pagina -->
  <article>
    <h1>Nuova sede a Torino</h1>
    <p>
      Pubblicato il <time datetime="2026-02-10">10 febbraio 2026</time>
    </p>
    <p>Da lunedì è operativa la sede di Torino.</p>
  </article>
</main>

<aside aria-labelledby="titolo-correlati">
  <h2 id="titolo-correlati">Correlati</h2>
  <ul>
    <li><a href="/sedi">Tutte le sedi</a></li>
  </ul>
</aside>

<footer>
  <p><small>© 2026 Acme S.p.A.</small></p>
</footer>
```

```
# Cosa è cambiato, e perché:
#
# .testata      → <header>        landmark: lo screen reader lo elenca
# .menu         → <nav> + <ul>    "navigazione, elenco di 2 elementi"
# .voce         → <li>            la lista diventa una lista vera
# .contenuto    → <main>          landmark saltabile con un comando
# .titolo-grande→ <h1>            entra nell'indice della pagina
# .data         → <time datetime> data leggibile anche dalle macchine
# .testo        → <p>             paragrafo, non un blocco anonimo
# .laterale     → <aside>         landmark "complementary", etichettato
# .titolo-medio → <h2>            gerarchia coerente sotto l'h1
# .fondo        → <footer>        landmark "contentinfo"
#
# Il logo diventa un link alla home: è la convenzione che ogni utente
# si aspetta, e l'alt descrive la DESTINAZIONE, non l'immagine.
```

---

### Esercizio 2 — Form di registrazione accessibile

**Obiettivo:** costruire un form con i tipi di input corretti, `autocomplete`, validazione nativa e messaggi d'errore collegati.

```html
<!-- SOLUZIONE -->
<form id="registrazione" action="/api/registrazione" method="post">
  <h1>Crea un account</h1>

  <p id="istruzioni">I campi contrassegnati con un asterisco sono obbligatori.</p>

  <fieldset>
    <legend>Dati personali</legend>

    <div class="campo">
      <label for="nome">Nome <span aria-hidden="true">*</span></label>
      <input
        type="text"
        id="nome"
        name="nome"
        autocomplete="given-name"
        required
        aria-describedby="errore-nome"
      />
      <p id="errore-nome" role="alert" class="messaggio-errore"></p>
    </div>

    <div class="campo">
      <label for="cognome">Cognome <span aria-hidden="true">*</span></label>
      <input
        type="text"
        id="cognome"
        name="cognome"
        autocomplete="family-name"
        required
        aria-describedby="errore-cognome"
      />
      <p id="errore-cognome" role="alert" class="messaggio-errore"></p>
    </div>

    <div class="campo">
      <label for="nascita">Data di nascita</label>
      <input
        type="date"
        id="nascita"
        name="nascita"
        autocomplete="bday"
        max="2008-12-31"
        aria-describedby="aiuto-nascita errore-nascita"
      />
      <p id="aiuto-nascita" class="aiuto">Devi avere almeno 18 anni.</p>
      <p id="errore-nascita" role="alert" class="messaggio-errore"></p>
    </div>
  </fieldset>

  <fieldset>
    <legend>Credenziali</legend>

    <div class="campo">
      <label for="email">Email <span aria-hidden="true">*</span></label>
      <input
        type="email"
        id="email"
        name="email"
        autocomplete="email"
        required
        aria-describedby="errore-email"
      />
      <p id="errore-email" role="alert" class="messaggio-errore"></p>
    </div>

    <div class="campo">
      <label for="password">Password <span aria-hidden="true">*</span></label>
      <input
        type="password"
        id="password"
        name="password"
        autocomplete="new-password"
        minlength="12"
        required
        aria-describedby="aiuto-password errore-password"
      />
      <p id="aiuto-password" class="aiuto">Almeno 12 caratteri.</p>
      <p id="errore-password" role="alert" class="messaggio-errore"></p>
    </div>
  </fieldset>

  <fieldset>
    <legend>Recapito</legend>

    <div class="campo">
      <label for="telefono">Telefono</label>
      <input
        type="tel"
        id="telefono"
        name="telefono"
        autocomplete="tel"
        inputmode="tel"
        pattern="[0-9 +().-]{6,20}"
        title="Da 6 a 20 caratteri: cifre, spazi, +, (), . e -"
        aria-describedby="errore-telefono"
      />
      <p id="errore-telefono" role="alert" class="messaggio-errore"></p>
    </div>

    <div class="campo">
      <label for="cap">CAP</label>
      <input
        type="text"
        id="cap"
        name="cap"
        inputmode="numeric"
        pattern="[0-9]{5}"
        maxlength="5"
        autocomplete="postal-code"
        title="Cinque cifre"
        aria-describedby="errore-cap"
      />
      <p id="errore-cap" role="alert" class="messaggio-errore"></p>
    </div>
  </fieldset>

  <fieldset>
    <legend>Consensi</legend>

    <div class="campo-scelta">
      <input type="checkbox" id="termini" name="termini" required aria-describedby="errore-termini" />
      <label for="termini">
        Accetto i <a href="/termini">termini di servizio</a> <span aria-hidden="true">*</span>
      </label>
      <p id="errore-termini" role="alert" class="messaggio-errore"></p>
    </div>

    <div class="campo-scelta">
      <input type="checkbox" id="newsletter" name="newsletter" value="si" />
      <label for="newsletter">Desidero ricevere la newsletter mensile</label>
    </div>
  </fieldset>

  <button type="submit">Crea l'account</button>

  <p id="esito-invio" role="status" aria-live="polite"></p>
</form>
```

```
# Le scelte che contano:
#
# <fieldset>/<legend>  raggruppano i campi in blocchi tematici;
#                      il gruppo di checkbox NE HA BISOGNO
# autocomplete         valori standard: il browser compila da solo (WCAG 1.3.5)
# type="tel" + pattern  tel non valida nulla di suo: il pattern lo fa
# CAP come text        type="number" mangerebbe lo zero iniziale di "00121"
# new-password         dice al gestore di password di PROPORNE una,
#                      non di riempire quella salvata
# aria-describedby     collega aiuto ed errore al campo: lo screen reader
#                      li legge quando il focus entra
# role="alert"         l'errore viene annunciato appena compare
# asterisco aria-hidden lo screen reader legge già "obbligatorio" da required:
#                      senza aria-hidden sentirebbe "Nome asterisco"
# label sulla checkbox DOPO l'input: è l'ordine visivo atteso, e il for
#                      mantiene il collegamento
```

---

### Esercizio 3 — Validazione personalizzata con messaggi accessibili

**Obiettivo:** sostituire i fumetti nativi del form dell'esercizio 2 con messaggi in pagina, aggiungendo una regola che gli attributi non possono esprimere (età minima 18 anni).

```javascript
// src/validazione-registrazione.js

const modulo = document.querySelector('#registrazione')
const campoNascita = document.querySelector('#nascita')

/** Restituisce il messaggio corretto in base al motivo del fallimento. */
function messaggioPerCampo(campo) {
  const v = campo.validity

  if (v.customError) return campo.validationMessage
  if (v.valueMissing) {
    return campo.type === 'checkbox'
      ? 'Devi accettare i termini per proseguire.'
      : 'Questo campo è obbligatorio.'
  }
  if (v.typeMismatch && campo.type === 'email') {
    return "L'indirizzo deve contenere la @ e un dominio, ad esempio nome@esempio.it."
  }
  if (v.tooShort) {
    return `Servono almeno ${campo.minLength} caratteri: ne hai inseriti ${campo.value.length}.`
  }
  if (v.rangeOverflow) return `La data non può essere successiva al ${campo.max}.`
  if (v.patternMismatch) return campo.title || 'Il formato non è corretto.'

  return 'Il valore inserito non è valido.'
}

function contenitoreErrore(campo) {
  return document.querySelector(`#errore-${campo.id}`)
}

function mostraErrore(campo) {
  contenitoreErrore(campo).textContent = messaggioPerCampo(campo)
  campo.setAttribute('aria-invalid', 'true')
}

function pulisciErrore(campo) {
  contenitoreErrore(campo).textContent = ''
  campo.removeAttribute('aria-invalid')
}

/** Regola che nessun attributo HTML può esprimere: almeno 18 anni compiuti. */
function verificaMaggiorEta() {
  if (!campoNascita.value) {
    campoNascita.setCustomValidity('')
    return
  }

  const nascita = new Date(campoNascita.value)
  const oggi = new Date()

  let anni = oggi.getFullYear() - nascita.getFullYear()
  const meseNonAncoraCompiuto =
    oggi.getMonth() < nascita.getMonth() ||
    (oggi.getMonth() === nascita.getMonth() && oggi.getDate() < nascita.getDate())
  if (meseNonAncoraCompiuto) anni--

  if (anni < 18) {
    campoNascita.setCustomValidity(`Devi avere almeno 18 anni: ne risultano ${anni}.`)
  } else {
    // Azzerare SEMPRE quando la condizione torna valida,
    // altrimenti il campo resta bloccato per sempre.
    campoNascita.setCustomValidity('')
  }
}

campoNascita.addEventListener('change', verificaMaggiorEta)

// Il fumetto nativo va disattivato: da qui la presentazione è nostra.
modulo.setAttribute('novalidate', '')

// 'invalid' non fa bubbling: si ascolta in fase di cattura.
modulo.addEventListener(
  'invalid',
  (evento) => {
    evento.preventDefault()
    mostraErrore(evento.target)
  },
  true,
)

// Ripulisci mentre l'utente corregge, ma solo se era già in errore.
modulo.addEventListener('input', (evento) => {
  const campo = evento.target
  if (campo.getAttribute('aria-invalid') === 'true' && campo.checkValidity()) {
    pulisciErrore(campo)
  }
})

modulo.addEventListener('submit', (evento) => {
  evento.preventDefault()
  verificaMaggiorEta()

  if (!modulo.reportValidity()) {
    // Porta il focus sul primo campo in errore: senza, chi naviga
    // da tastiera non sa dove sia il problema.
    modulo.querySelector('[aria-invalid="true"], :invalid')?.focus()
    return
  }

  document.querySelector('#esito-invio').textContent = 'Registrazione inviata.'
})
```

```
# Output atteso, provando a mano:
#
# 1. Invio con tutti i campi vuoti
#    → "Questo campo è obbligatorio." sotto nome, cognome, email, password
#    → "Devi accettare i termini per proseguire." sotto la checkbox
#    → il focus va sul campo Nome
#
# 2. Email "mario@"
#    → "L'indirizzo deve contenere la @ e un dominio, ad esempio nome@esempio.it."
#
# 3. Password "breve"
#    → "Servono almeno 12 caratteri: ne hai inseriti 5."
#
# 4. Data di nascita 2015-06-01
#    → "Devi avere almeno 18 anni: ne risultano 11."
#
# 5. Correzione di un campo in errore
#    → il messaggio sparisce mentre si scrive, senza attendere l'invio
```

---

### Esercizio 4 — Tabella di dati completamente annotata

**Obiettivo:** trasformare una griglia di numeri in una tabella navigabile da uno screen reader.

```html
<!-- PARTENZA — leggibile con gli occhi, inutilizzabile a voce -->
<table>
  <tr>
    <td>Divisione</td><td>T1</td><td>T2</td><td>T3</td><td>T4</td>
  </tr>
  <tr>
    <td>Industriale</td><td>610</td><td>630</td><td>780</td><td>800</td>
  </tr>
  <tr>
    <td>Servizi</td><td>420</td><td>440</td><td>550</td><td>560</td>
  </tr>
</table>
```

```html
<!-- SOLUZIONE -->
<figure>
  <table>
    <caption>
      Ricavi per divisione e trimestre, esercizio 2026
      <span class="unita">(migliaia di euro)</span>
    </caption>

    <thead>
      <tr>
        <th scope="col">Divisione</th>
        <th scope="col"><abbr title="Primo trimestre">T1</abbr></th>
        <th scope="col"><abbr title="Secondo trimestre">T2</abbr></th>
        <th scope="col"><abbr title="Terzo trimestre">T3</abbr></th>
        <th scope="col"><abbr title="Quarto trimestre">T4</abbr></th>
        <th scope="col">Totale</th>
      </tr>
    </thead>

    <tbody>
      <tr>
        <th scope="row">Industriale</th>
        <td>610</td>
        <td>630</td>
        <td>780</td>
        <td>800</td>
        <td>2.820</td>
      </tr>
      <tr>
        <th scope="row">Servizi</th>
        <td>420</td>
        <td>440</td>
        <td>550</td>
        <td>560</td>
        <td>1.970</td>
      </tr>
    </tbody>

    <tfoot>
      <tr>
        <th scope="row">Totale</th>
        <td>1.030</td>
        <td>1.070</td>
        <td>1.330</td>
        <td>1.360</td>
        <td>4.790</td>
      </tr>
    </tfoot>
  </table>

  <figcaption>
    Fonte: bilancio consolidato approvato dall'assemblea del
    <time datetime="2026-04-28">28 aprile 2026</time>.
  </figcaption>
</figure>
```

```css
/* Su schermo stretto la tabella scorre invece di comprimersi.
   role="region" + tabindex la rendono raggiungibile da tastiera. */
.tabella-scorrevole {
  overflow-x: auto;
}

/* Allineare i numeri a destra e incolonnare le cifre */
td {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

th[scope='row'] {
  text-align: left;
}
```

```
# Cosa annuncia uno screen reader sulla cella "780", prima e dopo:
#
# PRIMA:  "780"
# DOPO:   "Industriale, T3, 780"
#
# La differenza la fanno gli scope. Senza, la tabella è una griglia
# di numeri di cui non si sa a cosa appartengano.
#
# <abbr title> sulle intestazioni: "T3" da solo è ambiguo.
# <caption> è legato programmaticamente alla tabella;
#   un <h3> sopra la tabella non lo sarebbe.
# <tfoot> per i totali: alla stampa resta in fondo e <thead>
#   si ripete su ogni pagina.
```

---

### Esercizio 5 — Galleria multimediale responsive

**Obiettivo:** una galleria che serva l'immagine giusta a ogni schermo, con formati moderni e caricamento differito corretto.

```html
<!-- SOLUZIONE -->
<section aria-labelledby="titolo-galleria">
  <h2 id="titolo-galleria">Gli stabilimenti</h2>

  <ul class="galleria">
    <!-- Prima immagine: visibile subito. NIENTE lazy, priorità alta. -->
    <li>
      <figure>
        <picture>
          <source
            type="image/avif"
            srcset="/img/milano-400.avif 400w, /img/milano-800.avif 800w, /img/milano-1600.avif 1600w"
            sizes="(min-width: 64rem) 33vw, (min-width: 40rem) 50vw, 100vw"
          />
          <source
            type="image/webp"
            srcset="/img/milano-400.webp 400w, /img/milano-800.webp 800w, /img/milano-1600.webp 1600w"
            sizes="(min-width: 64rem) 33vw, (min-width: 40rem) 50vw, 100vw"
          />
          <img
            src="/img/milano-800.jpg"
            srcset="/img/milano-400.jpg 400w, /img/milano-800.jpg 800w, /img/milano-1600.jpg 1600w"
            sizes="(min-width: 64rem) 33vw, (min-width: 40rem) 50vw, 100vw"
            alt="Lo stabilimento di Milano: capannone in acciaio e vetro su due livelli"
            width="800"
            height="600"
            fetchpriority="high"
            decoding="async"
          />
        </picture>
        <figcaption>Milano — sede storica, operativa dal 1978.</figcaption>
      </figure>
    </li>

    <!-- Le successive stanno sotto la piega: lazy -->
    <li>
      <figure>
        <picture>
          <source
            type="image/avif"
            srcset="/img/torino-400.avif 400w, /img/torino-800.avif 800w, /img/torino-1600.avif 1600w"
            sizes="(min-width: 64rem) 33vw, (min-width: 40rem) 50vw, 100vw"
          />
          <img
            src="/img/torino-800.jpg"
            srcset="/img/torino-400.jpg 400w, /img/torino-800.jpg 800w, /img/torino-1600.jpg 1600w"
            sizes="(min-width: 64rem) 33vw, (min-width: 40rem) 50vw, 100vw"
            alt="Lo stabilimento di Torino visto dal piazzale interno"
            width="800"
            height="600"
            loading="lazy"
            decoding="async"
          />
        </picture>
        <figcaption>Torino — inaugurato nel 2026.</figcaption>
      </figure>
    </li>
  </ul>

  <!-- Il video di presentazione, con sottotitoli -->
  <figure>
    <video
      poster="/media/visita-copertina.jpg"
      controls
      preload="metadata"
      width="1280"
      height="720"
    >
      <source src="/media/visita.webm" type="video/webm" />
      <source src="/media/visita.mp4" type="video/mp4" />
      <track
        kind="captions"
        src="/media/visita-it.vtt"
        srclang="it"
        label="Italiano"
        default
      />
      <p>
        Il browser non riproduce il video.
        <a href="/media/visita.mp4">Scarica il file</a>.
      </p>
    </video>
    <figcaption>Visita guidata allo stabilimento di Milano (4 minuti, con sottotitoli).</figcaption>
  </figure>
</section>
```

```
# I punti in cui è facile sbagliare:
#
# sizes deve rispecchiare il CSS reale. Qui la galleria è a 3 colonne
#   sopra 1024px, a 2 sopra 640px, a 1 sotto: da cui 33vw / 50vw / 100vw.
#   Un sizes="100vw" con un layout a 3 colonne fa scaricare file
#   grandi il triplo del necessario.
#
# sizes va ripetuto su ogni <source> e sull'<img>: non si eredita.
#
# fetchpriority="high" sulla prima immagine e loading="lazy" sulle altre:
#   invertirli peggiora il Largest Contentful Paint invece di migliorarlo.
#
# width e height su <img> anche dentro <picture>: servono a riservare
#   lo spazio ed evitare il salto del layout.
#
# <track kind="captions"> non è opzionale: WCAG 1.2.2, livello A.
```

---

### Esercizio 6 — Finestra di conferma con `<dialog>`

**Obiettivo:** una conferma di eliminazione che gestisca correttamente focus, tastiera e annuncio.

```html
<!-- SOLUZIONE -->
<table>
  <caption>Documenti archiviati</caption>
  <thead>
    <tr>
      <th scope="col">Nome</th>
      <th scope="col">Data</th>
      <th scope="col">Azioni</th>
    </tr>
  </thead>
  <tbody id="corpo-documenti">
    <tr data-id="17">
      <th scope="row">bilancio-2026.pdf</th>
      <td><time datetime="2026-04-28">28 aprile 2026</time></td>
      <td>
        <!-- Il nome accessibile include il file: nell'elenco dei pulsanti
             non ci sono dieci "Elimina" indistinguibili -->
        <button type="button" class="elimina" data-nome="bilancio-2026.pdf">
          Elimina<span class="solo-screen-reader"> bilancio-2026.pdf</span>
        </button>
      </td>
    </tr>
    <tr data-id="18">
      <th scope="row">verbale-assemblea.pdf</th>
      <td><time datetime="2026-04-28">28 aprile 2026</time></td>
      <td>
        <button type="button" class="elimina" data-nome="verbale-assemblea.pdf">
          Elimina<span class="solo-screen-reader"> verbale-assemblea.pdf</span>
        </button>
      </td>
    </tr>
  </tbody>
</table>

<dialog id="conferma" aria-labelledby="titolo-conferma">
  <h2 id="titolo-conferma">Confermi l'eliminazione?</h2>
  <p>Stai per eliminare <strong id="nome-documento"></strong>. L'operazione non è reversibile.</p>

  <form method="dialog">
    <button value="annulla" autofocus>Annulla</button>
    <button value="conferma" class="pericolo">Elimina definitivamente</button>
  </form>
</dialog>

<p id="esito" role="status" aria-live="polite"></p>
```

```javascript
// src/conferma-eliminazione.js

const finestra = document.querySelector('#conferma')
const nomeDocumento = document.querySelector('#nome-documento')
const esito = document.querySelector('#esito')
const corpo = document.querySelector('#corpo-documenti')

// Ricordare chi ha aperto la dialog, per restituirgli il focus.
let comandoDiPartenza = null
let rigaInAttesa = null

// Delegazione: un solo listener per tutte le righe, presenti e future.
corpo.addEventListener('click', (evento) => {
  const comando = evento.target.closest('.elimina')
  if (!comando) return

  comandoDiPartenza = comando
  rigaInAttesa = comando.closest('tr')
  nomeDocumento.textContent = comando.dataset.nome

  // showModal(): top layer, sfondo inerte, focus confinato, Esc attivo.
  finestra.showModal()
})

finestra.addEventListener('close', () => {
  if (finestra.returnValue === 'conferma' && rigaInAttesa) {
    const nome = rigaInAttesa.querySelector('th').textContent
    rigaInAttesa.remove()
    // L'annuncio arriva senza spostare il focus, grazie alla live region.
    esito.textContent = `${nome} è stato eliminato.`
    // Il comando che aveva il focus non esiste più: portalo su un ancoraggio stabile.
    corpo.closest('table').focus()
  } else {
    esito.textContent = ''
    // Restituire il focus a chi ha aperto la dialog.
    comandoDiPartenza?.focus()
  }

  comandoDiPartenza = null
  rigaInAttesa = null
})
```

```css
#conferma {
  max-inline-size: 32rem;
  padding: 1.5rem;
  border: none;
  border-radius: 0.5rem;
}

#conferma::backdrop {
  background: rgb(0 0 0 / 0.5);
}

.pericolo {
  background: crimson;
  color: white;
}

/* La tabella riceve il focus programmatico dopo l'eliminazione */
table[tabindex='-1']:focus {
  outline: none;
}
```

```
# Perché ognuna di queste scelte:
#
# showModal() e non show()   confina il focus, abilita Esc e ::backdrop
# <form method="dialog">     chiude la dialog e registra returnValue
#                            senza inviare niente e senza JavaScript
# autofocus su "Annulla"     l'azione non distruttiva riceve il focus:
#                            un Invio distratto non cancella nulla
# aria-labelledby            il titolo della dialog è il suo nome accessibile
# comandoDiPartenza          alla chiusura il focus torna dov'era.
#                            Senza, riparte dall'inizio della pagina
# role="status" sull'esito   l'eliminazione viene annunciata senza
#                            spostare il focus
# focus sulla tabella        il pulsante che aveva il focus è stato rimosso
#                            dal DOM: il focus finisce su <body> e si perde
```

---

### Esercizio 7 — Verificare l'accessibilità di quello che hai scritto

**Obiettivo:** una procedura ripetibile per trovare i difetti prima che li trovi un utente.

```powershell
# 1. Validità del markup
pnpm dlx html-validate "src/**/*.html"

# 2. Analisi automatica dell'accessibilità
pnpm dlx pa11y http://localhost:5173

# 3. Con più dettaglio, usando le regole axe
pnpm dlx @axe-core/cli http://localhost:5173
```

```javascript
// scripts/controlla-accessibilita.js
// Controlli statici che coprono gli errori più frequenti,
// eseguibili senza avviare un browser.
// Esegui con: node scripts/controlla-accessibilita.js src/index.html

import { readFileSync } from 'node:fs'

const percorso = process.argv[2]
if (!percorso) {
  console.error('Uso: node scripts/controlla-accessibilita.js <file.html>')
  process.exit(1)
}

const html = readFileSync(percorso, 'utf8')
const problemi = []

function segnala(condizione, messaggio) {
  if (condizione) problemi.push(messaggio)
}

// lang sul documento
segnala(!/<html[^>]+lang=/i.test(html), '<html> senza attributo lang (WCAG 3.1.1)')

// title presente e non vuoto
segnala(!/<title>\s*\S/i.test(html), '<title> assente o vuoto')

// viewport
segnala(
  !/<meta[^>]+name=["']viewport["']/i.test(html),
  '<meta name="viewport"> assente: la pagina non sarà usabile su mobile',
)

// Un solo <main>
const quantiMain = (html.match(/<main[\s>]/gi) ?? []).length
segnala(quantiMain === 0, 'nessun <main>: manca il landmark principale')
segnala(quantiMain > 1, `${quantiMain} elementi <main>: deve essercene uno solo visibile`)

// Immagini senza alt
const immagini = html.match(/<img\b[^>]*>/gi) ?? []
const senzaAlt = immagini.filter((tag) => !/\salt\s*=/.test(tag))
segnala(senzaAlt.length > 0, `${senzaAlt.length} <img> senza attributo alt`)

// Immagini senza dimensioni: causano salti di layout
const senzaDimensioni = immagini.filter(
  (tag) => !/\swidth\s*=/.test(tag) || !/\sheight\s*=/.test(tag),
)
segnala(
  senzaDimensioni.length > 0,
  `${senzaDimensioni.length} <img> senza width/height: rischio di layout shift`,
)

// outline: none, la regola che rompe più accessibilità di ogni altra
segnala(
  /outline\s*:\s*(none|0)\s*[;}]/i.test(html),
  'trovato "outline: none": verifica che esista un :focus-visible sostitutivo',
)

// tabindex positivo
const tabindexPositivo = html.match(/tabindex\s*=\s*["']?[1-9]/gi) ?? []
segnala(
  tabindexPositivo.length > 0,
  `${tabindexPositivo.length} tabindex positivi: creano un ordine di tabulazione parallelo`,
)

// Gerarchia dei titoli
const livelli = [...html.matchAll(/<h([1-6])\b/gi)].map((m) => Number(m[1]))
for (let i = 1; i < livelli.length; i++) {
  if (livelli[i] - livelli[i - 1] > 1) {
    problemi.push(`salto nella gerarchia dei titoli: h${livelli[i - 1]} seguito da h${livelli[i]}`)
    break
  }
}
segnala(livelli.filter((l) => l === 1).length > 1, 'più di un <h1> nella pagina')

// Esito
if (problemi.length === 0) {
  console.log(`${percorso}: nessun problema fra quelli controllati.`)
} else {
  console.log(`${percorso}: ${problemi.length} problema/i\n`)
  for (const p of problemi) console.log(`  - ${p}`)
  process.exitCode = 1
}
```

```
# Output atteso su un file con difetti:
src/index.html: 4 problema/i

  - <html> senza attributo lang (WCAG 3.1.1)
  - 3 <img> senza attributo alt
  - 5 <img> senza width/height: rischio di layout shift
  - salto nella gerarchia dei titoli: h1 seguito da h3
```

```
# Cosa NON sostituisce questo script:
#
# Gli strumenti automatici — questo incluso, axe e pa11y compresi —
# intercettano circa un terzo dei problemi reali di accessibilità.
# Il contrasto di un testo su un'immagine, un alt che descrive
# l'immagine sbagliata, un ordine di tabulazione illogico:
# nessuna macchina se ne accorge.
#
# I tre controlli manuali che valgono più di ogni strumento:
#   1. Percorri l'intera pagina con Tab: l'ordine è sensato?
#      Il focus è sempre visibile? Si resta bloccati da qualche parte?
#   2. Ingrandisci al 200%: il contenuto resta leggibile e nulla si sovrappone?
#   3. Ascoltala con uno screen reader (NVDA su Windows, gratuito;
#      VoiceOver su macOS, integrato). Bastano dieci minuti per capire
#      cosa la tua pagina comunica davvero.
```

---

## C2. Mini-progetto: portale informativo aziendale

L'esercizio chiave del modulo. Costruiamo un portale con navigazione, contenuti strutturati, form e multimedia, **usando esclusivamente HTML semantico** — nessun framework, nessuna libreria, e il CSS ridotto al minimo indispensabile perché il risultato sia usabile.

Il vincolo "solo HTML" non è un capriccio: costringe a ottenere dagli elementi nativi tutto ciò che di solito si delega a JavaScript, ed è il modo più rapido per scoprire quanto l'HTML già faccia.

### Cosa deve avere

1. Struttura a landmark completa, con salto al contenuto.
2. Navigazione principale e percorso di navigazione.
3. Una pagina di notizie con `<article>` datati.
4. Una tabella di dati completamente annotata.
5. Una galleria con immagini responsive e un video con sottotitoli.
6. Un form di contatto accessibile con validazione nativa.
7. Sezioni richiudibili senza JavaScript.
8. Meta tag completi, Open Graph e dati strutturati.
9. Nessun errore dal validatore W3C.

### Struttura dei file

```
portale-acme/
├── index.html
├── src/
│   └── stile.css
├── img/
│   ├── logo.svg
│   ├── milano-400.jpg   milano-800.jpg   milano-1600.jpg
│   └── torino-400.jpg   torino-800.jpg   torino-1600.jpg
└── media/
    ├── visita.mp4
    ├── visita-copertina.jpg
    └── visita-it.vtt
```

### `index.html`

```html
<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />

    <title>Acme S.p.A. — Portale informativo</title>
    <meta
      name="description"
      content="Portale informativo di Acme S.p.A.: notizie societarie, risultati economici, sedi operative e contatti."
    />
    <link rel="canonical" href="https://acme.it/" />

    <meta name="theme-color" content="#0b3d91" media="(prefers-color-scheme: light)" />
    <meta name="theme-color" content="#0a1a33" media="(prefers-color-scheme: dark)" />

    <link rel="icon" href="/img/logo.svg" type="image/svg+xml" />

    <meta property="og:type" content="website" />
    <meta property="og:title" content="Acme S.p.A. — Portale informativo" />
    <meta property="og:description" content="Notizie societarie, risultati economici e contatti." />
    <meta property="og:url" content="https://acme.it/" />
    <meta property="og:site_name" content="Acme S.p.A." />
    <meta property="og:locale" content="it_IT" />
    <meta property="og:image" content="https://acme.it/img/anteprima.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content="La sede di Milano di Acme S.p.A." />

    <link rel="alternate" hreflang="it" href="https://acme.it/" />
    <link rel="alternate" hreflang="en" href="https://acme.it/en/" />
    <link rel="alternate" hreflang="x-default" href="https://acme.it/" />

    <link rel="stylesheet" href="/src/stile.css" />

    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Acme S.p.A.",
        "url": "https://acme.it",
        "logo": "https://acme.it/img/logo.svg",
        "foundingDate": "1978",
        "address": {
          "@type": "PostalAddress",
          "streetAddress": "Via Roma 12",
          "addressLocality": "Milano",
          "postalCode": "20121",
          "addressCountry": "IT"
        },
        "contactPoint": {
          "@type": "ContactPoint",
          "telephone": "+39-02-1234-5678",
          "contactType": "customer service",
          "availableLanguage": ["Italian", "English"]
        }
      }
    </script>
  </head>

  <body>
    <a href="#contenuto" class="salta-al-contenuto">Vai al contenuto principale</a>

    <header class="testata">
      <a href="/" class="marchio">
        <img src="/img/logo.svg" alt="Acme S.p.A. — pagina iniziale" width="140" height="40" />
      </a>

      <nav aria-label="Principale">
        <ul class="menu">
          <li><a href="/" aria-current="page">Home</a></li>
          <li><a href="/societa">La società</a></li>
          <li><a href="/prodotti">Prodotti</a></li>
          <li><a href="#contatti">Contatti</a></li>
          <li><a href="/en/" hreflang="en" lang="en">English</a></li>
        </ul>
      </nav>
    </header>

    <nav aria-label="Percorso di navigazione" class="percorso">
      <ol>
        <li><a href="/">Home</a></li>
        <li><span aria-current="page">Portale informativo</span></li>
      </ol>
    </nav>

    <main id="contenuto" tabindex="-1">
      <h1>Portale informativo Acme S.p.A.</h1>

      <p class="occhiello">
        Notizie societarie, risultati economici e recapiti, aggiornati al
        <time datetime="2026-04-28">28 aprile 2026</time>.
      </p>

      <!-- ── Notizie ────────────────────────────────────────────── -->
      <section aria-labelledby="titolo-notizie">
        <h2 id="titolo-notizie">Ultime notizie</h2>

        <article class="notizia">
          <h3>Nuova sede operativa a Torino</h3>
          <p class="meta">
            <time datetime="2026-02-10">10 febbraio 2026</time>
          </p>
          <p>
            Da lunedì è operativa la sede di Torino, che ospita la divisione
            <span lang="en">research and development</span> e trenta postazioni di lavoro.
          </p>
          <p><a href="/notizie/sede-torino">Leggi la notizia completa sulla sede di Torino</a></p>
        </article>

        <article class="notizia">
          <h3>Approvato il bilancio 2026</h3>
          <p class="meta">
            <time datetime="2026-04-28">28 aprile 2026</time>
          </p>
          <p>
            L'assemblea ha approvato il bilancio consolidato: i ricavi crescono del 12% e il
            patrimonio netto raggiunge gli 8,4 milioni di euro.
          </p>
          <p><a href="/notizie/bilancio-2026">Leggi la notizia completa sul bilancio 2026</a></p>
        </article>
      </section>

      <!-- ── Risultati ──────────────────────────────────────────── -->
      <section aria-labelledby="titolo-risultati">
        <h2 id="titolo-risultati">Risultati per divisione</h2>

        <figure>
          <div class="tabella-scorrevole" role="region" aria-labelledby="titolo-risultati" tabindex="0">
            <table>
              <caption>
                Ricavi per divisione e trimestre, esercizio 2026
                <span class="unita">(migliaia di euro)</span>
              </caption>

              <thead>
                <tr>
                  <th scope="col">Divisione</th>
                  <th scope="col"><abbr title="Primo trimestre">T1</abbr></th>
                  <th scope="col"><abbr title="Secondo trimestre">T2</abbr></th>
                  <th scope="col"><abbr title="Terzo trimestre">T3</abbr></th>
                  <th scope="col"><abbr title="Quarto trimestre">T4</abbr></th>
                  <th scope="col">Totale</th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <th scope="row">Industriale</th>
                  <td>610</td><td>630</td><td>780</td><td>800</td><td>2.820</td>
                </tr>
                <tr>
                  <th scope="row">Servizi</th>
                  <td>420</td><td>440</td><td>550</td><td>560</td><td>1.970</td>
                </tr>
              </tbody>

              <tfoot>
                <tr>
                  <th scope="row">Totale</th>
                  <td>1.030</td><td>1.070</td><td>1.330</td><td>1.360</td><td>4.790</td>
                </tr>
              </tfoot>
            </table>
          </div>

          <figcaption>
            Fonte: bilancio consolidato approvato dall'assemblea del
            <time datetime="2026-04-28">28 aprile 2026</time>.
          </figcaption>
        </figure>
      </section>

      <!-- ── Sedi ───────────────────────────────────────────────── -->
      <section aria-labelledby="titolo-sedi">
        <h2 id="titolo-sedi">Le sedi</h2>

        <ul class="galleria">
          <li>
            <figure>
              <img
                src="/img/milano-800.jpg"
                srcset="/img/milano-400.jpg 400w, /img/milano-800.jpg 800w, /img/milano-1600.jpg 1600w"
                sizes="(min-width: 48rem) 50vw, 100vw"
                alt="Lo stabilimento di Milano: capannone in acciaio e vetro su due livelli"
                width="800"
                height="600"
                fetchpriority="high"
                decoding="async"
              />
              <figcaption>Milano — sede storica, operativa dal 1978.</figcaption>
            </figure>
          </li>

          <li>
            <figure>
              <img
                src="/img/torino-800.jpg"
                srcset="/img/torino-400.jpg 400w, /img/torino-800.jpg 800w, /img/torino-1600.jpg 1600w"
                sizes="(min-width: 48rem) 50vw, 100vw"
                alt="Lo stabilimento di Torino visto dal piazzale interno"
                width="800"
                height="600"
                loading="lazy"
                decoding="async"
              />
              <figcaption>Torino — inaugurato nel febbraio 2026.</figcaption>
            </figure>
          </li>
        </ul>

        <figure>
          <video
            poster="/media/visita-copertina.jpg"
            controls
            preload="metadata"
            width="1280"
            height="720"
          >
            <source src="/media/visita.mp4" type="video/mp4" />
            <track
              kind="captions"
              src="/media/visita-it.vtt"
              srclang="it"
              label="Italiano"
              default
            />
            <p>
              Il browser non riproduce il video.
              <a href="/media/visita.mp4">Scarica il file (18 MB)</a>.
            </p>
          </video>
          <figcaption>Visita guidata allo stabilimento di Milano — 4 minuti, con sottotitoli.</figcaption>
        </figure>
      </section>

      <!-- ── Domande frequenti, senza una riga di JavaScript ─────── -->
      <section aria-labelledby="titolo-faq">
        <h2 id="titolo-faq">Domande frequenti</h2>

        <details>
          <summary>Come richiedo un preventivo?</summary>
          <p>
            Compila il modulo in fondo a questa pagina indicando la divisione di interesse.
            Rispondiamo entro due giorni lavorativi.
          </p>
        </details>

        <details>
          <summary>Quali sono i termini di pagamento?</summary>
          <p>
            Trenta giorni data fattura fine mese, salvo diverso accordo contrattuale.
            Il <abbr title="Documento Unico di Regolarità Contributiva">DURC</abbr>
            è disponibile su richiesta.
          </p>
        </details>

        <details>
          <summary>È possibile visitare gli stabilimenti?</summary>
          <p>
            Le visite si svolgono il primo giovedì di ogni mese, su prenotazione.
            Scrivi a <a href="mailto:visite@acme.it">visite@acme.it</a>.
          </p>
        </details>
      </section>

      <!-- ── Contatti ───────────────────────────────────────────── -->
      <section aria-labelledby="titolo-contatti" id="contatti">
        <h2 id="titolo-contatti">Contattaci</h2>

        <form action="/api/contatti" method="post">
          <p id="istruzioni-modulo">I campi contrassegnati con un asterisco sono obbligatori.</p>

          <fieldset>
            <legend>I tuoi dati</legend>

            <div class="campo">
              <label for="nome">Nome e cognome <span aria-hidden="true">*</span></label>
              <input
                type="text"
                id="nome"
                name="nome"
                autocomplete="name"
                required
                aria-describedby="istruzioni-modulo"
              />
            </div>

            <div class="campo">
              <label for="azienda">Azienda</label>
              <input type="text" id="azienda" name="azienda" autocomplete="organization" />
            </div>

            <div class="campo">
              <label for="email">Email <span aria-hidden="true">*</span></label>
              <input type="email" id="email" name="email" autocomplete="email" required />
            </div>

            <div class="campo">
              <label for="telefono">Telefono</label>
              <input
                type="tel"
                id="telefono"
                name="telefono"
                autocomplete="tel"
                inputmode="tel"
                pattern="[0-9 +().-]{6,20}"
                title="Da 6 a 20 caratteri: cifre, spazi, +, (), . e -"
              />
            </div>
          </fieldset>

          <fieldset>
            <legend>La tua richiesta</legend>

            <div class="campo">
              <label for="divisione">Divisione di interesse</label>
              <select id="divisione" name="divisione">
                <option value="">Seleziona una divisione</option>
                <option value="industriale">Industriale</option>
                <option value="servizi">Servizi</option>
                <option value="altro">Altro</option>
              </select>
            </div>

            <div class="campo">
              <label for="messaggio">Messaggio <span aria-hidden="true">*</span></label>
              <textarea
                id="messaggio"
                name="messaggio"
                rows="6"
                minlength="20"
                maxlength="2000"
                required
                aria-describedby="aiuto-messaggio"
              ></textarea>
              <p id="aiuto-messaggio" class="aiuto">Da 20 a 2000 caratteri.</p>
            </div>
          </fieldset>

          <fieldset>
            <legend>Come preferisci essere ricontattato?</legend>

            <label class="scelta">
              <input type="radio" name="contatto" value="email" checked />
              Via email
            </label>

            <label class="scelta">
              <input type="radio" name="contatto" value="telefono" />
              Per telefono
            </label>
          </fieldset>

          <div class="campo-scelta">
            <input type="checkbox" id="privacy" name="privacy" required />
            <label for="privacy">
              Ho letto l'<a href="/privacy">informativa sul trattamento dei dati</a>
              <span aria-hidden="true">*</span>
            </label>
          </div>

          <button type="submit">Invia la richiesta</button>
        </form>
      </section>
    </main>

    <aside aria-labelledby="titolo-documenti">
      <h2 id="titolo-documenti">Documenti scaricabili</h2>
      <ul>
        <li><a href="/doc/bilancio-2026.pdf">Bilancio consolidato 2026 (PDF, 2,4 MB)</a></li>
        <li><a href="/doc/codice-etico.pdf">Codice etico (PDF, 380 kB)</a></li>
      </ul>
    </aside>

    <footer class="fondo">
      <address>
        Acme S.p.A. — Via Roma 12, 20121 Milano<br />
        Telefono <a href="tel:+390212345678">02 1234 5678</a><br />
        Email <a href="mailto:info@acme.it">info@acme.it</a>
      </address>

      <nav aria-label="Piè di pagina">
        <ul>
          <li><a href="/privacy">Privacy</a></li>
          <li><a href="/cookie">Cookie</a></li>
          <li><a href="/accessibilita">Dichiarazione di accessibilità</a></li>
        </ul>
      </nav>

      <p><small>© 2026 Acme S.p.A. — P.IVA 01234567890</small></p>
    </footer>
  </body>
</html>
```

### `src/stile.css` — il minimo perché sia usabile

```css
/* src/stile.css
   Solo quanto serve a rendere il documento leggibile e accessibile.
   L'impaginazione vera è oggetto di tutorial_02_css3.md. */

:root {
  --testo: #1a1a1a;
  --sfondo: #ffffff;
  --tenue: #5c5c5c;
  --bordo: #d4d4d4;
  --accento: #0b3d91;
  --spazio: 1rem;
}

@media (prefers-color-scheme: dark) {
  :root {
    --testo: #ececec;
    --sfondo: #131313;
    --tenue: #a8a8a8;
    --bordo: #3a3a3a;
    --accento: #7aa7ff;
  }
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
  line-height: 1.6;
  color: var(--testo);
  background: var(--sfondo);
}

/* Il salto al contenuto: invisibile finché non riceve il focus */
.salta-al-contenuto {
  position: absolute;
  left: -9999px;
}

.salta-al-contenuto:focus {
  position: fixed;
  inset-block-start: 0;
  inset-inline-start: 0;
  z-index: 100;
  padding: 0.75rem 1rem;
  background: var(--testo);
  color: var(--sfondo);
}

/* L'indicatore di focus: sostituito, mai rimosso */
:focus-visible {
  outline: 3px solid var(--accento);
  outline-offset: 2px;
}

/* Nasconde visivamente senza togliere dall'albero di accessibilità */
.solo-screen-reader {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}

.testata,
.percorso,
main,
aside,
.fondo {
  max-inline-size: 60rem;
  margin-inline: auto;
  padding-inline: var(--spazio);
}

.menu,
.percorso ol,
.galleria,
.fondo nav ul {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spazio);
  padding-left: 0;
  list-style: none;
}

.percorso li + li::before {
  content: '/';
  margin-inline-end: 0.5rem;
  color: var(--tenue);
}

.notizia {
  padding-block: var(--spazio);
  border-block-end: 1px solid var(--bordo);
}

.meta,
.aiuto,
.unita {
  color: var(--tenue);
  font-size: 0.9rem;
}

/* La tabella scorre invece di comprimersi su schermo stretto */
.tabella-scorrevole {
  overflow-x: auto;
}

table {
  border-collapse: collapse;
  inline-size: 100%;
}

caption {
  margin-block-end: 0.5rem;
  text-align: left;
  font-weight: 600;
}

th,
td {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--bordo);
}

td {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

th[scope='row'] {
  text-align: left;
}

tfoot {
  font-weight: 600;
}

img,
video {
  max-inline-size: 100%;
  block-size: auto;
}

figure {
  margin-inline: 0;
}

figcaption {
  color: var(--tenue);
  font-size: 0.9rem;
}

details {
  padding-block: 0.5rem;
  border-block-end: 1px solid var(--bordo);
}

summary {
  cursor: pointer;
  font-weight: 600;
}

.campo,
.campo-scelta {
  margin-block-end: var(--spazio);
}

label {
  display: block;
  margin-block-end: 0.25rem;
  font-weight: 600;
}

.campo-scelta label,
.scelta {
  display: inline;
  font-weight: normal;
}

input,
select,
textarea {
  inline-size: 100%;
  padding: 0.5rem;
  font: inherit;
  color: inherit;
  background: var(--sfondo);
  border: 1px solid var(--bordo);
  border-radius: 0.25rem;
}

input[type='checkbox'],
input[type='radio'] {
  inline-size: auto;
}

/* Errore visibile solo dopo l'interazione dell'utente */
input:user-invalid,
textarea:user-invalid {
  border-color: crimson;
}

fieldset {
  margin-block-end: calc(var(--spazio) * 1.5);
  padding: var(--spazio);
  border: 1px solid var(--bordo);
  border-radius: 0.25rem;
}

legend {
  padding-inline: 0.5rem;
  font-weight: 600;
}

button {
  padding: 0.6rem 1.2rem;
  font: inherit;
  color: var(--sfondo);
  background: var(--accento);
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

.fondo {
  margin-block-start: calc(var(--spazio) * 3);
  padding-block: calc(var(--spazio) * 2);
  border-block-start: 1px solid var(--bordo);
}

address {
  font-style: normal;
}

/* Rispetta la preferenza di sistema per il movimento ridotto */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Verifica

```powershell
# 1. Il markup è valido?
pnpm dlx html-validate index.html

# 2. Ci sono violazioni di accessibilità rilevabili automaticamente?
pnpm dev
# in un altro terminale:
pnpm dlx pa11y http://localhost:5173

# 3. I controlli statici scritti nell'esercizio 7
node scripts/controlla-accessibilita.js index.html
```

```
# Output atteso da html-validate su un file corretto:
index.html: 0 errors, 0 warnings

# Output atteso da pa11y:
No issues found!
```

**I tre controlli manuali che nessuno strumento sostituisce:**

```
1. TASTIERA
   Percorri l'intera pagina con Tab, dall'inizio alla fine.
   · Il primo Tab rivela "Vai al contenuto principale"?
   · Il focus è sempre visibile, senza eccezioni?
   · L'ordine segue la logica visiva?
   · I <details> si aprono con Invio?
   · Il form si invia con Invio dal campo di testo?
   · Si resta bloccati da qualche parte?

2. INGRANDIMENTO
   Porta lo zoom al 200% (Ctrl e +).
   · Il testo resta leggibile senza scorrimento orizzontale?
   · Nulla si sovrappone o esce dallo schermo?
   · La tabella scorre nel suo contenitore invece di rompere il layout?

3. SCREEN READER
   NVDA su Windows (gratuito, nvaccess.org) o VoiceOver su macOS (Cmd+F5).
   · L'elenco dei landmark contiene header, nav, main, aside, footer?
   · L'elenco dei titoli riproduce l'indice della pagina?
   · L'elenco dei link è comprensibile fuori contesto?
   · Sulla cella "780" senti "Industriale, T3, 780"?
   · Ogni campo del form annuncia la propria etichetta?
```

Se uno di questi tre controlli fallisce, il documento non è finito — indipendentemente da cosa dicano gli strumenti automatici.

---

# Parte D — Approfondimento per Esperti

---

## D1. Web Components: Custom Elements

I Web Components permettono di definire elementi propri, con comportamento e stile incapsulati, senza dipendere da un framework. Sono API native del browser: quello che scrivi oggi funzionerà fra dieci anni senza aggiornare nulla.

```javascript
// src/componenti/contatore-caratteri.js

/**
 * Mostra quanti caratteri restano in un campo di testo.
 * Uso: <contatore-caratteri per="messaggio" massimo="2000"></contatore-caratteri>
 */
class ContatoreCaratteri extends HTMLElement {
  // Solo gli attributi elencati qui fanno scattare attributeChangedCallback.
  static observedAttributes = ['massimo']

  #campo = null
  #gestoreInput = null

  // connectedCallback: l'elemento è entrato nel documento.
  // È qui che si aggancia tutto — NON nel costruttore, dove gli attributi
  // potrebbero non essere ancora stati assegnati.
  connectedCallback() {
    const idCampo = this.getAttribute('per')
    this.#campo = document.getElementById(idCampo)

    if (!this.#campo) {
      console.warn(`<contatore-caratteri>: nessun elemento con id "${idCampo}"`)
      return
    }

    // Live region: l'aggiornamento viene annunciato senza spostare il focus.
    this.setAttribute('role', 'status')
    this.setAttribute('aria-live', 'polite')

    this.#gestoreInput = () => this.#aggiorna()
    this.#campo.addEventListener('input', this.#gestoreInput)
    this.#aggiorna()
  }

  // disconnectedCallback: l'elemento è uscito dal documento.
  // Sganciare i listener qui evita perdite di memoria quando il DOM cambia.
  disconnectedCallback() {
    if (this.#campo && this.#gestoreInput) {
      this.#campo.removeEventListener('input', this.#gestoreInput)
    }
  }

  attributeChangedCallback(nome, precedente, attuale) {
    if (precedente !== attuale) this.#aggiorna()
  }

  get massimo() {
    return Number(this.getAttribute('massimo')) || 0
  }

  #aggiorna() {
    if (!this.#campo) return

    const usati = this.#campo.value.length
    const residui = this.massimo - usati

    this.textContent =
      residui >= 0
        ? `${residui} caratteri disponibili`
        : `${Math.abs(residui)} caratteri oltre il limite`

    this.toggleAttribute('oltre-limite', residui < 0)
  }
}

// Il nome DEVE contenere un trattino: è ciò che distingue
// gli elementi personalizzati da quelli che la specifica potrebbe
// introdurre in futuro.
customElements.define('contatore-caratteri', ContatoreCaratteri)
```

```html
<label for="messaggio">Messaggio</label>
<textarea id="messaggio" name="messaggio" maxlength="2000" rows="6"></textarea>
<contatore-caratteri per="messaggio" massimo="2000"></contatore-caratteri>

<script type="module" src="/src/componenti/contatore-caratteri.js"></script>
```

```css
contatore-caratteri {
  display: block;
  font-size: 0.9rem;
  color: var(--tenue);
}

contatore-caratteri[oltre-limite] {
  color: crimson;
  font-weight: 600;
}
```

Il ciclo di vita, per intero:

| Callback | Quando scatta | Cosa metterci |
|---|---|---|
| `constructor()` | Alla creazione dell'istanza | Solo inizializzazione dello stato interno. **Mai** leggere attributi né toccare il DOM |
| `connectedCallback()` | All'inserimento nel documento | Lettura degli attributi, listener, primo rendering |
| `disconnectedCallback()` | Alla rimozione dal documento | Rimozione dei listener, annullamento dei timer |
| `attributeChangedCallback()` | Alla modifica di un attributo osservato | Aggiornamento in risposta al nuovo valore |
| `adoptedCallback()` | Al passaggio a un altro documento | Raro: `<iframe>`, `document.adoptNode()` |

**Errori tipici:**

```javascript
class EsempioSbagliato extends HTMLElement {
  // ❌ SBAGLIATO — nel costruttore gli attributi potrebbero non esserci ancora,
  //    e toccare il DOM lì è vietato dalla specifica
  constructor() {
    super()
    this.innerHTML = `<span>${this.getAttribute('massimo')}</span>` // null
  }

  // ❌ SBAGLIATO — observedAttributes deve essere una proprietà STATICA.
  //    Come getter di istanza non viene mai letta, e
  //    attributeChangedCallback non scatta mai.
  get observedAttributes() {
    return ['massimo']
  }
}

class EsempioCorretto extends HTMLElement {
  static observedAttributes = ['massimo']

  constructor() {
    super()
    // Solo stato interno. Niente DOM, niente attributi.
    this._ultimoValore = null
  }

  connectedCallback() {
    // Qui gli attributi ci sono e il DOM è raggiungibile.
    this.textContent = `Massimo: ${this.getAttribute('massimo')}`
  }
}
```

### Estendere elementi nativi

```javascript
// Un <button> che chiede conferma prima di procedere
class BottoneConferma extends HTMLButtonElement {
  connectedCallback() {
    this.addEventListener('click', (evento) => {
      if (!confirm(this.dataset.domanda ?? 'Confermi?')) {
        evento.preventDefault()
        evento.stopImmediatePropagation()
      }
    })
  }
}

customElements.define('bottone-conferma', BottoneConferma, { extends: 'button' })
```

```html
<button is="bottone-conferma" data-domanda="Eliminare il documento?">Elimina</button>
```

Il vantaggio è che l'elemento resta un `<button>` vero: tastiera, ruolo, invio del form, tutto già corretto. Lo svantaggio è che **Safari non implementa `is=`** e non ha dichiarato l'intenzione di farlo. In un progetto che deve funzionare ovunque, va usato con un ripiego o evitato.

---

## D2. Shadow DOM, slot e Declarative Shadow DOM

Lo Shadow DOM isola un albero di nodi dal resto del documento: il CSS esterno non lo raggiunge e i suoi selettori non escono.

```javascript
// src/componenti/scheda-informativa.js

class SchedaInformativa extends HTMLElement {
  connectedCallback() {
    // Il rendering va fatto una volta sola: connectedCallback può
    // scattare più volte se l'elemento viene spostato nel DOM.
    if (this.shadowRoot) return

    // mode: 'open' → accessibile da JavaScript esterno via elemento.shadowRoot
    // mode: 'closed' → inaccessibile. Sconsigliato: complica i test
    //                  e l'incapsulamento non è comunque una barriera di sicurezza.
    const ombra = this.attachShadow({ mode: 'open' })

    ombra.innerHTML = `
      <style>
        /* :host è l'elemento stesso, visto dall'interno */
        :host {
          display: block;
          padding: 1rem;
          border: 1px solid var(--colore-bordo, #d4d4d4);
          border-radius: 0.5rem;
        }

        /* Reagire a un attributo sull'host */
        :host([variante="avviso"]) {
          border-color: #b45309;
          background: #fffbeb;
        }

        /* Questi selettori NON escono dallo shadow root:
           un h2 fuori dal componente non viene toccato */
        h2 {
          margin-block-start: 0;
          font-size: 1.1rem;
        }

        .corpo {
          color: var(--colore-testo-tenue, #5c5c5c);
        }
      </style>

      <h2><slot name="titolo">Senza titolo</slot></h2>
      <div class="corpo"><slot>Nessun contenuto.</slot></div>
    `
  }
}

customElements.define('scheda-informativa', SchedaInformativa)
```

```html
<scheda-informativa variante="avviso">
  <span slot="titolo">Scadenza imminente</span>
  <p>Tre fatture scadono entro venerdì.</p>
</scheda-informativa>
```

`<slot>` è il punto in cui il contenuto scritto dall'esterno viene proiettato dentro il componente. Il testo fra i tag dello `<slot>` è il contenuto di riserva, mostrato quando nulla viene fornito.

### Cosa attraversa il confine e cosa no

```
                    Shadow DOM
    ┌───────────────────────────────────────┐
    │                                       │
❌  │  selettori CSS esterni                │  il CSS del documento
    │  (.mia-classe { … } non entra)        │  non stila l'interno
    │                                       │
✅  │  proprietà personalizzate CSS         │  --colore-bordo passa
    │  (--colore-bordo: red)                │
    │                                       │
✅  │  proprietà ereditate                  │  font, color, line-height
    │  (font-family, color)                 │  attraversano
    │                                       │
✅  │  ::part() e ::slotted()               │  punti di stile esposti
    │                                       │  volontariamente
    │                                       │
✅  │  eventi con composed: true            │  click, input, keydown
    │                                       │  escono e fanno bubbling
    │                                       │
❌  │  document.querySelector()             │  non vede dentro
    │                                       │
    └───────────────────────────────────────┘
```

Le proprietà personalizzate sono il canale di personalizzazione previsto:

```css
/* Dal documento, senza toccare l'interno del componente */
scheda-informativa {
  --colore-bordo: #0b3d91;
  --colore-testo-tenue: #444;
}
```

Per esporre elementi interni allo stile esterno si usa `part`:

```javascript
ombra.innerHTML = `
  <style>
    h2 { margin: 0; }
  </style>
  <h2 part="titolo"><slot name="titolo"></slot></h2>
`
```

```css
scheda-informativa::part(titolo) {
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

### Eventi che escono

```javascript
class SchedaInformativa extends HTMLElement {
  #notificaChiusura() {
    this.dispatchEvent(
      new CustomEvent('scheda-chiusa', {
        detail: { id: this.id },
        bubbles: true,
        // composed: true è necessario perché l'evento attraversi
        // il confine dello shadow root. Senza, resta dentro.
        composed: true,
      }),
    )
  }
}
```

```javascript
document.addEventListener('scheda-chiusa', (evento) => {
  console.log('chiusa la scheda', evento.detail.id)
})
```

### Declarative Shadow DOM

Il problema dei Web Components tradizionali è che esistono solo dopo l'esecuzione di JavaScript: nel rendering lato server la pagina arriva vuota. Il Declarative Shadow DOM risolve la questione dichiarando lo shadow root direttamente nel markup.

```html
<scheda-informativa>
  <template shadowrootmode="open">
    <style>
      :host { display: block; padding: 1rem; border: 1px solid #d4d4d4; }
      h2 { margin-block-start: 0; }
    </style>
    <h2><slot name="titolo">Senza titolo</slot></h2>
    <div class="corpo"><slot></slot></div>
  </template>

  <span slot="titolo">Scadenza imminente</span>
  <p>Tre fatture scadono entro venerdì.</p>
</scheda-informativa>
```

Il browser costruisce lo shadow root durante il parsing dell'HTML, prima che qualunque script venga eseguito. Il componente è visibile e stilato immediatamente; il JavaScript, quando arriva, aggiunge solo il comportamento.

È disponibile in tutti i browser evergreen dal 2024. Va tenuto presente che `innerHTML` non lo analizza per motivi di sicurezza: serve `setHTMLUnsafe()` o il parsing lato server.

### Quando usare i Web Components, e quando no

```
Convengono quando:
  · il componente deve funzionare in pagine costruite con tecnologie diverse
  · serve un design system usato da più applicazioni non omogenee
  · si integra un widget in un sito di terzi, e l'isolamento CSS è il requisito
  · si vuole una dipendenza che non invecchia

Non convengono quando:
  · l'applicazione è già in React, Vue o Svelte: quei framework offrono
    composizione e stato migliori, e i Web Components aggiungono attrito
  · serve rendering lato server con idratazione fine
  · il componente ha stato complesso e molte interazioni fra parti
```

---

## D3. Sicurezza del documento

I meccanismi di difesa che si dichiarano nel markup. Il trattamento sistematico è in `tutorial_14_sicurezza_web.md`; qui vediamo cosa appartiene all'HTML.

### Content Security Policy

La CSP dice al browser da dove può caricare risorse. È la difesa più efficace contro il cross-site scripting, perché limita il danno anche quando un'iniezione riesce.

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-r4nd0m'; style-src 'self'; img-src 'self' data: https:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'
```

L'intestazione HTTP è la forma corretta. Il `<meta>` esiste come ripiego quando non si controlla il server, ma non supporta alcune direttive (`frame-ancestors`, `report-uri`) e agisce solo dal punto in cui compare:

```html
<meta
  http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'"
/>
```

Il **nonce** permette di autorizzare uno script inline specifico senza aprire la porta a tutti:

```html
<!-- Il valore deve essere generato dal server a ogni risposta,
     casuale e mai riutilizzato. Un nonce fisso non protegge da nulla. -->
<script nonce="r4nd0m-generato-dal-server">
  inizializzaApplicazione()
</script>
```

```
# ❌ SBAGLIATO — vanifica la CSP: 'unsafe-inline' autorizza
#    qualunque script iniettato
Content-Security-Policy: script-src 'self' 'unsafe-inline'

# ✅ CORRETTO — solo gli script con il nonce di questa risposta
Content-Security-Policy: script-src 'self' 'nonce-r4nd0m'
```

### Subresource Integrity

Quando carichi uno script da un CDN, stai eseguendo codice che non controlli. SRI verifica che il file sia esattamente quello atteso:

```html
<script
  src="https://cdn.example.com/libreria@2.1.0/libreria.min.js"
  integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
  crossorigin="anonymous"
></script>
```

Se il contenuto cambia di un solo byte, il browser rifiuta di eseguirlo. `crossorigin="anonymous"` è necessario perché la verifica possa avvenire su una risorsa di origine diversa.

```powershell
# Calcolare l'hash di un file
$bytes = [System.IO.File]::ReadAllBytes("libreria.min.js")
$hash = [System.Security.Cryptography.SHA384]::Create().ComputeHash($bytes)
"sha384-" + [Convert]::ToBase64String($hash)
```

L'alternativa migliore resta ospitare la dipendenza sul proprio dominio: elimina il problema invece di gestirlo, e toglie un punto di fallimento esterno.

### Iframe con sandbox

```html
<!-- sandbox senza valori: TUTTO bloccato.
     Ogni permesso va riconcesso esplicitamente. -->
<iframe src="/anteprima" sandbox title="Anteprima del documento"></iframe>

<!-- Permessi concessi uno a uno -->
<iframe
  src="https://widget.esempio.it/calcolatore"
  sandbox="allow-scripts allow-forms"
  title="Calcolatore di preventivo"
  loading="lazy"
  referrerpolicy="no-referrer"
></iframe>
```

```html
<!-- ❌ PERICOLOSO — insieme, questi due permessi annullano la sandbox:
     il contenuto può rimuovere l'attributo sandbox da sé stesso -->
<iframe sandbox="allow-scripts allow-same-origin" src="https://non-fidato.example"></iframe>
```

`title` su `<iframe>` non è opzionale: senza, lo screen reader annuncia "frame" e nulla più.

### Riferimenti in uscita

```html
<!-- Non trasmettere l'indirizzo di provenienza ai siti esterni -->
<a href="https://esterno.example" rel="noopener noreferrer external">Sito esterno</a>

<!-- Politica per l'intero documento -->
<meta name="referrer" content="strict-origin-when-cross-origin" />
```

`strict-origin-when-cross-origin` è il default dei browser moderni: manda l'URL completo alle richieste interne, solo l'origine a quelle esterne in HTTPS, e nulla quando si scende a HTTP.

### Sanitizzazione

Qualunque contenuto proveniente dall'utente inserito con `innerHTML` è un vettore di attacco.

```javascript
// ❌ SBAGLIATO — esegue qualunque cosa l'utente abbia scritto
elemento.innerHTML = commentoUtente

// ✅ CORRETTO quando serve solo testo — textContent non interpreta markup
elemento.textContent = commentoUtente

// ✅ CORRETTO quando serve markup limitato — sanitizzazione con una
//    libreria mantenuta e verificata
import DOMPurify from 'dompurify'

elemento.innerHTML = DOMPurify.sanitize(commentoUtente, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
  ALLOWED_ATTR: ['href', 'title'],
})
```

La Sanitizer API nativa esiste come proposta ed è passata attraverso revisioni sostanziali della specifica; il supporto non è ancora omogeneo fra i browser. Fino a quando non lo sarà, DOMPurify resta la scelta operativa.

**Non scrivere il proprio sanificatore.** L'elenco dei vettori — `javascript:` negli `href`, `on*` come attributi, `<svg><script>`, entità HTML annidate, `data:` con `text/html` — è più lungo di quanto sembri, e ogni versione del browser ne aggiunge.

Trusted Types offre una difesa più radicale — impedire del tutto l'assegnazione di stringhe grezze a `innerHTML` — ma è implementato in Chromium e non ovunque. Va considerato un rafforzamento, non la difesa principale.

---

## D4. HTML per email: un altro linguaggio

Chi scrive HTML per il web e si trova a produrre una newsletter scopre che quasi nulla di quanto sa si applica. I client di posta non sono browser: Outlook su Windows usa il motore di rendering di Word, Gmail riscrive l'HTML in ingresso, e ogni client applica i propri stili predefiniti.

```
Nel web (2026)                    Nell'email (2026)
─────────────────────────────     ────────────────────────────────
CSS Grid, Flexbox                 tabelle annidate
<link rel="stylesheet">           stili inline su ogni elemento
elementi semantici                <table> per il layout
media query                       supporto parziale e irregolare
webp, avif                        png, jpg, gif
JavaScript                        rimosso da ogni client
posizionamento                    nessuno
```

```html
<!-- Struttura minima che funziona quasi ovunque -->
<!doctype html>
<html lang="it" xmlns:v="urn:schemas-microsoft-com:vml">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="x-apple-disable-message-reformatting" />
    <title>Newsletter di aprile</title>
  </head>

  <body style="margin:0; padding:0; background-color:#f4f4f4;">
    <!-- Testo di anteprima: compare nell'elenco dei messaggi, non nel corpo -->
    <div style="display:none; max-height:0; overflow:hidden; opacity:0;">
      I risultati del primo trimestre e le prossime scadenze.
    </div>

    <!-- Tabella esterna: dà lo sfondo a tutta la larghezza -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background-color:#f4f4f4;">
      <tr>
        <td align="center" style="padding:24px 12px;">

          <!-- Tabella interna: il contenuto, a larghezza fissa -->
          <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
                 style="width:600px; max-width:600px; background-color:#ffffff;">
            <tr>
              <td style="padding:24px; font-family:Arial,Helvetica,sans-serif; font-size:16px; line-height:1.5; color:#1a1a1a;">
                <h1 style="margin:0 0 16px; font-size:22px; line-height:1.3;">
                  Risultati del primo trimestre
                </h1>

                <p style="margin:0 0 16px;">
                  I ricavi del trimestre raggiungono 1,03 milioni di euro.
                </p>

                <!-- Il pulsante è una tabella: <button> e i bordi CSS
                     non sono affidabili in Outlook -->
                <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td align="center" bgcolor="#0b3d91" style="border-radius:4px;">
                      <a href="https://acme.it/bilancio-2026"
                         style="display:inline-block; padding:12px 24px; font-family:Arial,sans-serif; font-size:16px; color:#ffffff; text-decoration:none;">
                        Leggi il documento completo
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>

        </td>
      </tr>
    </table>
  </body>
</html>
```

Le regole che governano tutto:

| Regola | Motivo |
|---|---|
| Layout con `<table>` annidate | Grid e Flexbox non sono affidabili in Outlook |
| Stili **inline** su ogni elemento | Gmail rimuove `<style>` in alcune viste |
| `role="presentation"` sulle tabelle di layout | Toglie la tabella dall'albero di accessibilità: non contiene dati |
| Larghezza fissa 600 px | Larghezza sicura sul riquadro di anteprima di Outlook |
| `width` come attributo **e** in `style` | Outlook legge l'attributo, gli altri lo stile |
| Font web-safe con ripiego | I font personalizzati non caricano quasi mai |
| `alt` su ogni immagine | Molti client bloccano le immagini di default: l'`alt` è ciò che resta |
| Nessun JavaScript | Rimosso da tutti i client |

```html
<!-- Modalità scura: i client la applicano invertendo i colori a modo loro.
     Queste due dichiarazioni riducono i risultati peggiori. -->
<meta name="color-scheme" content="light dark" />
<meta name="supported-color-schemes" content="light dark" />
```

**La prova sul campo è l'unica prova.** Servizi come Litmus o Email on Acid mostrano il messaggio in decine di client reali. Senza quel passaggio, non si sa cosa vedano i destinatari — e l'anteprima nel proprio client non è indicativa.

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
HTML5 — Mappa dei concetti

IL PRINCIPIO
└── L'HTML descrive COSA È il contenuto, non come appare.
    Da qui discende tutto il resto: accessibilità, SEO, manutenibilità.

STRUTTURA DEL DOCUMENTO
├── <!doctype html>        senza, quirks mode: il CSS si comporta diversamente
├── <html lang="it">       pronuncia dello screen reader (WCAG 3.1.1)
├── <meta charset>         entro i primi 1024 byte, altrimenti caratteri corrotti
├── <meta viewport>        senza, il mobile finge 980px e rimpicciolisce
└── <title>                scheda, segnalibro, risultato di ricerca, primo annuncio

SEMANTICA
├── Landmark: header · nav · main · article · section · aside · footer
│   ├── <main> una sola, visibile: è il salto diretto al contenuto
│   └── più <nav> vanno distinte con aria-label
├── <article>  ha senso estratto?  →  sì
├── <section>  raggruppa un tema?  →  sì, e vuole un titolo
├── <div>      serve solo al CSS?  →  legittimo, non è un errore
└── Titoli h1-h6: sono un INDICE, non dimensioni del carattere
    └── un h1 per pagina · nessun livello saltato

CONTENT MODEL
├── <p> accetta solo phrasing content
│   └── un <div> dentro <p> CHIUDE il paragrafo: il DOM ≠ il tuo markup
├── <ul>/<ol> accettano solo <li>
├── nessun elemento interattivo dentro un altro interattivo
└── il parser non fallisce mai: corregge in silenzio

FORM
├── <label for> ↔ id  (non name)
├── name = la chiave con cui il dato arriva al server
├── placeholder NON è una label
├── <button> senza type dentro un form = submit
├── type: email url tel number date … cambia tastiera e validazione
│   ├── tel non valida nulla: serve pattern
│   └── number mangia gli zeri iniziali: per i CAP usa text + inputmode
├── autocomplete con i valori standard (WCAG 1.3.5)
├── pattern è ancorato · title diventa il messaggio d'errore
├── Constraint Validation API
│   ├── validity.*  dice PERCHÉ è invalido
│   ├── setCustomValidity('') SEMPRE quando torna valido
│   └── novalidate + evento 'invalid' in cattura = messaggi propri
└── FormData: nessun Content-Type impostato a mano

MULTIMEDIA
├── alt: SOSTITUISCE l'immagine, non la descrive
│   ├── alt=""     decorativa → ignorata
│   └── assente    → legge il nome del file
├── width e height sempre: riservano lo spazio, evitano il layout shift
├── srcset + sizes   stessa immagine, dimensioni diverse
├── <picture>        formati diversi, o ritagli diversi
│   └── sizes non si eredita: va ripetuto su ogni <source>
├── loading="lazy"   SOLO sotto la piega
├── fetchpriority="high" sull'immagine principale
└── <track kind="captions">  WCAG 1.2.2, livello A

ACCESSIBILITÀ
├── Albero di accessibilità: ruolo · nome · stato · valore
├── Nome accessibile, in ordine di precedenza:
│     aria-labelledby → aria-label → contenuto → title
│     └── aria-label SOVRASCRIVE il testo visibile: rompe il comando vocale
├── ARIA, prima regola: non usare ARIA. L'elemento nativo ha già il ruolo.
├── Live region: deve ESISTERE prima che il testo cambi
│     role="status" (polite) · role="alert" (assertive, con parsimonia)
├── aria-expanded va sul COMANDO, non sul pannello
├── Tastiera: <div> cliccabile ≠ <button>
│     tabindex 0 = nell'ordine · -1 = solo via JS · positivo = mai
└── :focus-visible  sostituisci l'indicatore, non rimuoverlo

INTERATTIVITÀ NATIVA
├── <details>/<summary>   pannello richiudibile, zero JavaScript
├── <dialog>.showModal()  top layer · focus confinato · Esc · ::backdrop
│     └── show() non fa nulla di tutto questo
└── popover               menu e tooltip, con Esc e clic fuori inclusi

METADATI
├── canonical            evita il contenuto duplicato
├── Open Graph           property, non name · immagine ASSOLUTA · 1200×630
└── JSON-LD              deve descrivere contenuto realmente presente

SICUREZZA
├── CSP con nonce        'unsafe-inline' vanifica tutto
├── SRI                  o, meglio, ospita la dipendenza da te
├── iframe sandbox       allow-scripts + allow-same-origin = sandbox annullata
└── innerHTML            textContent, o DOMPurify. Mai un sanificatore proprio.
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Sai spiegare perché `<h1>` e un `<div>` grande e grassetto non sono equivalenti
- [ ] Scrivi lo scheletro di un documento sapendo cosa fa ogni riga del `<head>`
- [ ] Usi i titoli come indice: un `<h1>`, nessun livello saltato
- [ ] Distingui `<strong>` da `<b>` e `<em>` da `<i>` in base al significato
- [ ] Scegli fra `<a>` e `<button>` con il criterio "naviga o agisce"
- [ ] Scrivi testi di link comprensibili fuori dal contesto
- [ ] Sai quando `alt=""` è corretto e perché non è come omettere `alt`
- [ ] Applichi i landmark e sai perché `<main>` deve essere una sola
- [ ] Distingui `<article>`, `<section>` e `<div>` con l'albero decisionale
- [ ] Scrivi un form con `<label for>`, `name` e `type` sul pulsante
- [ ] Annoti una tabella con `<caption>`, `scope`, `<thead>` e `<tfoot>`

**Parte B — Comprensione**

- [ ] Sai perché un `<div>` dentro un `<p>` produce un DOM diverso dal markup
- [ ] Distingui "Visualizza sorgente" da DevTools → Elements e sai quando usare quale
- [ ] Scegli il `type` giusto e sai perché un CAP non è `type="number"`
- [ ] Usi `pattern` sapendo che è ancorato e che `title` diventa il messaggio
- [ ] Compili `autocomplete` con i valori standard
- [ ] Sostituisci i fumetti nativi leggendo `validity.*`
- [ ] Sai perché `setCustomValidity('')` va sempre richiamato
- [ ] Invii un form con `FormData` senza impostare `Content-Type`
- [ ] Scrivi `sizes` coerente con il layout CSS effettivo
- [ ] Sai perché `loading="lazy"` sull'immagine principale peggiora l'LCP
- [ ] Sai calcolare il nome accessibile e verificarlo in DevTools
- [ ] Sai perché `aria-label` su un testo visibile rompe il comando vocale
- [ ] Usi le live region sapendo che devono preesistere alla modifica
- [ ] Metti `aria-expanded` sul comando, non sul pannello
- [ ] Sai perché `outline: none` è la regola CSS che rompe più accessibilità
- [ ] Distingui `showModal()` da `show()` e sai cosa perdi con il secondo
- [ ] Scegli fra `<dialog>` e `popover` in base al blocco richiesto
- [ ] Sai perché `og:image` deve essere un indirizzo assoluto
- [ ] Sai a cosa serve `viewBox` e perché senza l'SVG non scala

**Parte C — Pratica**

- [ ] Hai riscritto una pagina a `<div>` in markup semantico
- [ ] Hai costruito un form con validazione personalizzata e messaggi annunciati
- [ ] Hai percorso il portale con `Tab` dall'inizio alla fine senza restare bloccato
- [ ] Hai ascoltato una tua pagina con uno screen reader

**Parte D — Esperto**

- [ ] Sai perché il costruttore di un Custom Element non deve leggere attributi
- [ ] Sai cosa attraversa il confine dello Shadow DOM e cosa no
- [ ] Sai perché serve `composed: true` per far uscire un evento personalizzato
- [ ] Sai perché `'unsafe-inline'` vanifica una CSP con nonce
- [ ] Sai perché `allow-scripts` con `allow-same-origin` annulla la sandbox
- [ ] Sai perché non si scrive un sanificatore HTML proprio

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| `<div>` con classe al posto degli elementi semantici | Nessun landmark, nessun titolo navigabile, contenuto opaco a screen reader e motori di ricerca | `<header>`, `<nav>`, `<main>`, `<article>`, `<h1>`… |
| Titoli scelti per la dimensione del carattere | L'indice della pagina diventa incoerente | Livello per gerarchia, dimensione con il CSS |
| Livelli di titolo saltati (`h1` → `h3`) | Chi naviga per titoli non capisce l'annidamento | Livelli consecutivi |
| `<div onclick>` al posto di `<button>` | Non riceve il focus, non risponde a Invio e Spazio, non è annunciato | `<button type="button">` |
| `<a href="#">` per un'azione | Naviga, sporca la cronologia, promette una destinazione | `<button type="button">` |
| `placeholder` usato come etichetta | Sparisce quando serve, contrasto basso, supporto irregolare | `<label>` sempre; il placeholder è un esempio |
| `<label for>` che punta al `name` | Nessun collegamento: il campo resta senza nome accessibile | `for` deve corrispondere all'`id` |
| `<button>` senza `type` dentro un form | Invia il form quando doveva fare altro | `type="button"` su tutto ciò che non invia |
| `type="number"` per CAP, partita IVA, codici | Perde gli zeri iniziali, accetta `1e5`, cambia con la rotellina | `type="text"` + `inputmode` + `pattern` |
| `autocomplete="off"` per abitudine | Costringe a digitare a mano su ogni dispositivo | Valori standard di `autocomplete` |
| `alt` assente | Lo screen reader legge il nome del file | `alt` descrittivo, o `alt=""` se decorativa |
| `alt="immagine di…"` | Ridondante: il ruolo è già annunciato | Descrivi il contenuto, non il mezzo |
| `<img>` senza `width` e `height` | Il contenuto salta quando l'immagine arriva (CLS) | Sempre le dimensioni intrinseche |
| `loading="lazy"` sull'immagine principale | Ritarda l'LCP: peggiora ciò che voleva migliorare | `lazy` solo sotto la piega; `fetchpriority="high"` in cima |
| `sizes="100vw"` con layout a colonne | Scarica file grandi il doppio o il triplo del necessario | `sizes` coerente con il CSS reale |
| `<video>` senza `<track>` | Inaccessibile a chi non sente (WCAG 1.2.2, livello A) | Sottotitoli WebVTT |
| `outline: none` senza sostituto | Chi naviga da tastiera non sa dove si trova | `:focus-visible` con contrasto e `outline-offset` |
| `tabindex` positivo | Crea un ordine parallelo che precede tutto il resto | Solo `0` e `-1`; riordina il markup |
| `aria-label` su un elemento con testo visibile | Sovrascrive il testo: il comando vocale non trova più il controllo | Rimuoverlo, o usare `.solo-screen-reader` |
| `role="button"` su un `<div>` | Promette un comportamento che il codice non fornisce | `<button>` |
| Live region creata insieme al testo | Nessun annuncio: lo screen reader osserva le regioni preesistenti | Contenitore vuoto già nel DOM |
| `aria-expanded` sul pannello | Lo stato non viene mai annunciato | Va sul comando che apre |
| Modale scritta a mano | Focus non confinato, `Esc` inerte, sfondo non inerte | `<dialog>` con `showModal()` |
| Tabelle per impaginare | Struttura di dati inesistente annunciata come tale | CSS Grid o Flexbox; `role="presentation"` solo nelle email |
| `og:image` con percorso relativo | I crawler non lo risolvono: l'anteprima resta vuota | Sempre indirizzo assoluto |
| `'unsafe-inline'` nella CSP | Autorizza qualunque script iniettato: la CSP non protegge più | Nonce o hash |
| `sandbox="allow-scripts allow-same-origin"` | Il contenuto può togliersi la sandbox da solo | Non concederli insieme a contenuto non fidato |
| `innerHTML` con contenuto dell'utente | Cross-site scripting | `textContent`, o DOMPurify se serve markup |

---

## Troubleshooting rapido

**Il CSS non si applica a un elemento che è chiaramente lì**
- Causa: il parser ha costruito un DOM diverso dal markup — tipicamente un `<div>` dentro un `<p>`, o un `<tbody>` inserito da solo in una tabella
- Fix: DevTools → Elements per vedere l'albero reale, poi `pnpm dlx html-validate` per la causa esatta

**I caratteri accentati appaiono come `Ã¨` o `�`**
- Causa: `<meta charset="UTF-8">` assente o oltre i primi 1024 byte, oppure il file non è salvato in UTF-8
- Fix: primo elemento del `<head>`; in VS Code verifica la codifica nella barra di stato

**La pagina appare minuscola sul telefono**
- Causa: manca `<meta name="viewport">`
- Fix: `<meta name="viewport" content="width=device-width, initial-scale=1" />`

**Il form si invia ma sul server i campi sono vuoti**
- Causa: gli input non hanno `name` — un campo senza `name` non viene serializzato
- Fix: `name` su ogni campo da inviare. Verifica in DevTools → Network → Payload

**Un pulsante "Annulla" invia il form**
- Causa: dentro un `<form>`, un `<button>` senza `type` vale `submit`
- Fix: `type="button"`

**Un campo resta non valido anche dopo la correzione**
- Causa: `setCustomValidity()` chiamato con un messaggio e mai azzerato
- Fix: `campo.setCustomValidity('')` in ogni ramo in cui il valore torna corretto

**I messaggi di errore non vengono letti dallo screen reader**
- Causa: il contenitore non è una live region, o viene creato insieme al testo
- Fix: `role="alert"` su un elemento **già presente e vuoto** nel DOM

**Il testo salta verso il basso mentre la pagina carica**
- Causa: immagini senza `width` e `height`: il browser non può riservare lo spazio
- Fix: dimensioni intrinseche su ogni `<img>`, anche se il CSS le sovrascrive

**Il browser scarica un'immagine molto più grande del necessario**
- Causa: `sizes` non corrisponde allo spazio reale nel layout
- Fix: allinea `sizes` al CSS. Verifica in DevTools → Network la colonna della dimensione

**`srcset` viene ignorato**
- Causa: `sizes` mancante con i descrittori `w`, oppure `w` e `x` mescolati nello stesso `srcset`
- Fix: con i descrittori `w` serve sempre `sizes`; non mescolare i due tipi

**`<source>` dentro `<video>` viene ignorata**
- Causa: c'è anche `src` sull'elemento `<video>`, che ha la precedenza
- Fix: togliere `src` quando si usano le `<source>`

**`::backdrop` non ha effetto sulla `<dialog>`**
- Causa: aperta con `show()` invece di `showModal()`
- Fix: `showModal()`

**Il focus dopo la chiusura di una modale riparte dall'inizio della pagina**
- Causa: l'elemento che aveva il focus è stato rimosso dal DOM, o non è stato ripristinato
- Fix: memorizzare il comando di apertura e richiamare `.focus()` nell'evento `close`

**Il popover non appare**
- Causa: l'attributo `popover` manca sull'elemento bersaglio, oppure `popovertarget` punta a un `id` inesistente
- Fix: verificare che entrambi ci siano e corrispondano; controllare il supporto con `HTMLElement.prototype.hasOwnProperty('popover')`

**L'anteprima del link nelle chat è vuota**
- Causa: `og:image` con percorso relativo, oppure immagine dietro autenticazione
- Fix: indirizzo assoluto e risorsa pubblica. Verifica con lo strumento di debug della piattaforma

**Lo screen reader annuncia un nome diverso dal testo visibile**
- Causa: un `aria-label` o `aria-labelledby` sta sovrascrivendo il contenuto
- Fix: DevTools → Elements → Accessibility per vedere la fonte del nome, poi rimuovere l'attributo superfluo

**Un elemento con `aria-hidden="true"` riceve comunque il focus con Tab**
- Causa: `aria-hidden` toglie dall'albero di accessibilità ma non dall'ordine di tabulazione
- Fix: aggiungere `tabindex="-1"`, o usare l'attributo `inert` sul contenitore

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_02_css3.md` | Dare forma alla struttura costruita qui: Grid, Flexbox, proprietà logiche per `dir="rtl"` |
| `tutorial_04_javascript_fondamenti.md` | Manipolare il DOM di cui qui hai visto la costruzione; eventi, delegazione |
| `tutorial_11_api_design.md` | Il server che riceve i `FormData` inviati da qui, e la validazione che conta davvero |
| `tutorial_14_sicurezza_web.md` | CSP, SRI, sandbox e sanitizzazione in modo sistematico |
| `tutorial_15_testing_web.md` | Test di accessibilità automatizzati con axe e Playwright |
| `tutorial_17_performance_web.md` | Core Web Vitals: LCP, CLS e le immagini responsive viste in B6 |
| `tutorial_18_pwa_tecnologie_avanzate.md` | Web Components in un'architettura completa |

---

## Risorse di riferimento

**Specifiche:**
- [HTML Living Standard](https://html.spec.whatwg.org/multipage/) — la specifica normativa, sempre aggiornata
- [WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/) — ruoli, stati e proprietà
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/) — pattern di componenti con implementazioni di riferimento
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) — i criteri di conformità
- [Come rispettare WCAG 2.2](https://www.w3.org/WAI/WCAG22/quickref/) — riferimento rapido, criterio per criterio

**Documentazione:**
- [MDN — HTML](https://developer.mozilla.org/it/docs/Web/HTML) — riferimento di ogni elemento e attributo
- [MDN — Accessibilità](https://developer.mozilla.org/it/docs/Web/Accessibility) — guide operative
- [MDN — Web Components](https://developer.mozilla.org/it/docs/Web/API/Web_components)
- [web.dev — Learn HTML](https://web.dev/learn/html) — corso strutturato, gratuito
- [Open Graph Protocol](https://ogp.me/) — la specifica
- [Schema.org](https://schema.org/docs/schemas.html) — vocabolario dei dati strutturati

**Strumenti:**
- [Validatore W3C](https://validator.w3.org/nu/) — validazione del markup
- [html-validate](https://html-validate.org/) — validazione in locale e in CI
- [axe DevTools](https://www.deque.com/axe/devtools/) — analisi dell'accessibilità nel browser
- [pa11y](https://pa11y.org/) — analisi da riga di comando
- [NVDA](https://www.nvaccess.org/) — screen reader gratuito per Windows
- [Can I use](https://caniuse.com/) — supporto dei browser, funzionalità per funzionalità

**Libri:**
- Adrian Roselli, *articoli su adrianroselli.com* — riferimento pratico su accessibilità e HTML, con esempi verificati sugli screen reader reali
- Heydon Pickering, *Inclusive Components* — pattern di componenti accessibili, con la motivazione di ogni scelta

---

> **Fine del Tutorial 01 — HTML5 Semantico e Accessibile**
>
> Prossimo tutorial: `tutorial_02_css3.md`

