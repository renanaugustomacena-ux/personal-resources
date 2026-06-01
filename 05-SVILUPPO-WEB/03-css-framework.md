---
corso: "Sviluppo Web"
fase: "1 — Fondamenti"
modulo: "03"
titolo: "CSS Framework e Preprocessori"
versione: "Tailwind 4.x / Bootstrap 5.x / Sass / PostCSS"
livello: "Intermedio"
prerequisiti:
  - "02 — CSS3"
obiettivi:
  - "Configurare e utilizzare Tailwind CSS con utility-first approach"
  - "Comprendere Bootstrap per prototyping rapido"
  - "Utilizzare Sass/SCSS per CSS scalabile e manutenibile"
  - "Configurare PostCSS con plugin per CSS moderno"
  - "Scegliere il framework appropriato in base al progetto"
  - "Implementare design system con token e componenti riutilizzabili"
tag: [Tailwind, Bootstrap, Sass, PostCSS, utility-first, design-system, preprocessori]
---

# CSS Framework e Preprocessori — Guida Completa

> **Modulo 03** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [CSS3](02-css3.md)
>
> Al termine di questo modulo saprai:
> 1. Configurare e utilizzare Tailwind CSS con utility-first approach
> 2. Comprendere Bootstrap per prototyping rapido
> 3. Utilizzare Sass/SCSS per CSS scalabile e manutenibile
> 4. Configurare PostCSS con plugin per CSS moderno
> 5. Scegliere il framework appropriato in base al progetto
> 6. Implementare design system con token e componenti riutilizzabili
>
> **Tempo stimato:** 5-7 ore · **Livello:** Intermedio

## Idee guida
1. **Tailwind CSS dominante, ma non sempre best.** Bootstrap legacy ma stabile.
2. **Utility-first vs component-first: trade-off.**
3. **PostCSS > Sass per nuovi progetti.** CSS native + plugin.
4. **Design system token > bare CSS.** Coerenza scale.


## Indice

1. [Panoramica](#panoramica)
2. [Preprocessori CSS](#preprocessori-css)
   - [Sass/SCSS](#sassscss)
   - [PostCSS](#postcss)
3. [Utility-First: Tailwind CSS](#utility-first-tailwind-css)
   - [Fondamenti](#fondamenti)
   - [Personalizzazione](#personalizzazione)
   - [Componenti](#componenti)
   - [Tailwind CSS v4](#tailwind-css-v4)
4. [Component-Based: Bootstrap](#component-based-bootstrap)
   - [Fondamenti Bootstrap](#fondamenti-bootstrap)
   - [Componenti Bootstrap](#componenti-bootstrap)
   - [Personalizzazione Bootstrap](#personalizzazione-bootstrap)
5. [Metodologie CSS](#metodologie-css)
   - [BEM](#bem-block-element-modifier)
   - [OOCSS](#oocss-object-oriented-css)
   - [SMACSS](#smacss)
   - [ITCSS](#itcss-inverted-triangle-css)
   - [Cube CSS](#cube-css)
6. [Librerie di Componenti Headless](#librerie-di-componenti-headless)
   - [Radix UI](#radix-ui)
   - [Headless UI](#headless-ui)
   - [Ark UI](#ark-ui)
7. [shadcn/ui — Component System](#shadcnui--component-system)
8. [CSS-in-JS — Analisi Comparativa](#css-in-js--analisi-comparativa)
   - [Soluzioni Runtime](#soluzioni-runtime-styled-components-e-emotion)
   - [Soluzioni Zero-Runtime](#soluzioni-zero-runtime-panda-css-e-vanilla-extract)
9. [CSS Modules](#css-modules)
10. [UnoCSS e CSS Atomico](#unocss-e-css-atomico)
11. [CSS Moderno vs Framework](#css-moderno-vs-framework)
    - [Design Token e Strategie di Theming](#design-token-e-strategie-di-theming)
    - [Pattern di Design Responsive Avanzati](#pattern-di-design-responsive-avanzati)
    - [Implementazione del Dark Mode](#implementazione-del-dark-mode)
    - [Librerie di Animazione per il Web](#librerie-di-animazione-per-il-web)
    - [Architettura di Component Library](#architettura-di-component-library)
    - [Accessibilita nei CSS Framework](#accessibilita-nei-css-framework)
    - [Confronto di Performance degli Approcci CSS](#confronto-di-performance-degli-approcci-css)
    - [Strategie di Migrazione tra Framework](#strategie-di-migrazione-tra-framework)
12. [Best Practices](#best-practices)

---

## Panoramica

### Perche esistono i CSS Framework

Il CSS, nella sua forma nativa, offre un controllo completo sulla presentazione visiva di un sito web. Tuttavia, man mano che i progetti crescono in complessita, emergono problemi ricorrenti: duplicazione del codice, incoerenza visiva tra le pagine, difficolta nella manutenzione e tempi di sviluppo che si allungano notevolmente. I CSS framework nascono proprio per risolvere queste criticita.

Un CSS framework fornisce una base predefinita di stili, componenti e convenzioni che permettono agli sviluppatori di costruire interfacce coerenti e responsive in modo piu rapido ed efficiente. Invece di scrivere ogni regola da zero, si parte da un sistema collaudato che gestisce le problematiche piu comuni: reset dei browser, griglie responsive, tipografia coerente, componenti interattivi e pattern di design consolidati.

I vantaggi principali dell'adozione di un framework includono:

- **Velocita di sviluppo**: componenti pronti all'uso riducono il tempo di implementazione
- **Coerenza**: un design system unificato garantisce uniformita visiva
- **Responsivita**: sistemi di griglia e breakpoint gia configurati
- **Manutenibilita**: convenzioni condivise facilitano il lavoro di team
- **Accessibilita**: molti framework includono best practice per l'accessibilita
- **Documentazione**: ecosistemi maturi con guide dettagliate

### Categorie di framework

I CSS framework si dividono in tre categorie principali, ciascuna con una filosofia e un approccio distinti:

**Preprocessori** (Sass, Less, PostCSS): estendono il linguaggio CSS con funzionalita di programmazione come variabili, funzioni, cicli e modularizzazione. Non impongono uno stile visivo, ma potenziano il linguaggio stesso.

**Utility-First** (Tailwind CSS, UnoCSS, Tachyons): forniscono un vasto insieme di classi di utilita a basso livello che si compongono direttamente nell'HTML. Favoriscono la composizione rispetto all'astrazione.

**Component-Based** (Bootstrap, Bulma, Foundation): offrono componenti predefiniti come navbar, card, modal e bottoni con stili gia applicati. Si personalizzano tramite variabili e override.

### Tabella comparativa

| Caratteristica         | Sass/SCSS    | PostCSS      | Tailwind CSS | Bootstrap    |
|------------------------|--------------|--------------|--------------|--------------|
| Tipo                   | Preprocessore| Post-processore| Utility-First| Component-Based|
| Curva di apprendimento | Media        | Bassa-Media  | Media-Alta   | Bassa        |
| Dimensione bundle      | Dipende      | Dipende      | Piccola (purge)| Media-Grande|
| Personalizzazione      | Totale       | Totale       | Alta         | Media        |
| Componenti pronti      | No           | No           | No (headless)| Si           |
| Ecosistema plugin      | Limitato     | Molto ampio  | Buono        | Moderato     |
| Integrazione build     | Nativa       | Eccellente   | Buona        | Buona        |
| Approccio design       | Libero       | Libero       | Utility      | Opinionated  |

---

## Preprocessori CSS

### Sass/SCSS

Sass (Syntactically Awesome Stylesheets) e il preprocessore CSS piu diffuso e maturo. Estende il CSS con funzionalita tipiche dei linguaggi di programmazione, rendendo i fogli di stile piu potenti, organizzati e manutenibili. Esiste in due sintassi: la sintassi originale Sass (indentata, senza parentesi graffe) e SCSS (Sassy CSS), che e un superset del CSS standard ed e la piu utilizzata.

#### Installazione e compilazione

L'implementazione raccomandata e Dart Sass, che ha sostituito le versioni precedenti Ruby Sass (deprecato) e LibSass (deprecato). Si installa tramite npm:

```bash
# Installazione globale
npm install -g sass

# Installazione come dipendenza di progetto
npm install --save-dev sass

# Compilazione singolo file
sass src/styles/main.scss dist/css/main.css

# Compilazione con watch (ricompila automaticamente ad ogni modifica)
sass --watch src/styles/main.scss:dist/css/main.css

# Compilazione compressa per produzione
sass --style=compressed src/styles/main.scss dist/css/main.min.css

# Compilazione di un'intera directory
sass --watch src/styles:dist/css
```

#### Variabili

Le variabili Sass permettono di definire valori riutilizzabili in tutto il progetto, facilitando la manutenzione e la coerenza del design:

```scss
// Definizione delle variabili
$colore-primario: #2563eb;
$colore-secondario: #7c3aed;
$colore-testo: #1f2937;
$colore-sfondo: #f9fafb;

$font-principale: 'Inter', system-ui, sans-serif;
$font-mono: 'JetBrains Mono', monospace;

$spaziatura-base: 1rem;
$spaziatura-grande: $spaziatura-base * 2;
$spaziatura-piccola: $spaziatura-base * 0.5;

$raggio-bordo: 0.5rem;
$ombra-leggera: 0 1px 3px rgba(0, 0, 0, 0.12);
$ombra-media: 0 4px 6px rgba(0, 0, 0, 0.1);

$breakpoint-sm: 640px;
$breakpoint-md: 768px;
$breakpoint-lg: 1024px;
$breakpoint-xl: 1280px;

// Utilizzo delle variabili
.pulsante-primario {
  background-color: $colore-primario;
  font-family: $font-principale;
  padding: $spaziatura-piccola $spaziatura-base;
  border-radius: $raggio-bordo;
  box-shadow: $ombra-leggera;
}
```

Le variabili Sass sono imperative (vengono sostituite al momento della compilazione), a differenza delle CSS custom properties che sono reattive e possono cambiare a runtime.

#### Nesting

Il nesting permette di annidare i selettori rispecchiando la struttura HTML, riducendo la ripetizione e migliorando la leggibilita. Il selettore `&` fa riferimento al selettore genitore:

```scss
.card {
  background: white;
  border-radius: $raggio-bordo;
  box-shadow: $ombra-leggera;
  overflow: hidden;

  // & si riferisce a .card
  &:hover {
    box-shadow: $ombra-media;
    transform: translateY(-2px);
  }

  &--evidenziata {
    border: 2px solid $colore-primario;
  }

  &__header {
    padding: $spaziatura-base;
    border-bottom: 1px solid #e5e7eb;

    h3 {
      margin: 0;
      color: $colore-testo;
    }
  }

  &__body {
    padding: $spaziatura-base;
  }

  &__footer {
    padding: $spaziatura-piccola $spaziatura-base;
    background: $colore-sfondo;
    display: flex;
    justify-content: flex-end;
    gap: $spaziatura-piccola;
  }
}

// Nesting con media queries
.contenitore {
  width: 100%;
  padding: 0 $spaziatura-base;

  @media (min-width: $breakpoint-md) {
    max-width: 768px;
    margin: 0 auto;
  }

  @media (min-width: $breakpoint-lg) {
    max-width: 1024px;
  }
}
```

Attenzione: un nesting eccessivo (oltre 3-4 livelli) genera selettori troppo specifici e difficili da sovrascrivere. Mantenere il nesting superficiale e una best practice fondamentale.

#### Mixin

I mixin sono blocchi di stili riutilizzabili che possono accettare parametri, funzionando come funzioni che generano CSS:

```scss
// Mixin semplice
@mixin flex-center {
  display: flex;
  justify-content: center;
  align-items: center;
}

// Mixin con parametri
@mixin dimensione-testo($dimensione, $peso: 400, $altezza-linea: 1.5) {
  font-size: $dimensione;
  font-weight: $peso;
  line-height: $altezza-linea;
}

// Mixin per breakpoint responsive
@mixin responsive($breakpoint) {
  @if $breakpoint == sm {
    @media (min-width: $breakpoint-sm) { @content; }
  } @else if $breakpoint == md {
    @media (min-width: $breakpoint-md) { @content; }
  } @else if $breakpoint == lg {
    @media (min-width: $breakpoint-lg) { @content; }
  } @else if $breakpoint == xl {
    @media (min-width: $breakpoint-xl) { @content; }
  }
}

// Mixin con @content per wrapper flessibili
@mixin overlay($colore-sfondo: rgba(0, 0, 0, 0.5)) {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: $colore-sfondo;
  @content;
}

// Utilizzo dei mixin
.hero {
  @include flex-center;
  min-height: 100vh;

  h1 {
    @include dimensione-testo(3rem, 700, 1.2);
  }

  p {
    @include dimensione-testo(1.25rem);
  }

  @include responsive(md) {
    min-height: 80vh;
  }
}

.modale-sfondo {
  @include overlay {
    z-index: 1000;
    display: flex;
    justify-content: center;
    align-items: center;
  }
}
```

#### Funzioni

Le funzioni Sass restituiscono un valore e sono ideali per calcoli e trasformazioni:

```scss
// Funzione per convertire px in rem
@function px-a-rem($px, $base: 16) {
  @return calc($px / $base) * 1rem;
}

// Funzione per generare scale di colore
@function tinta($colore, $percentuale) {
  @return mix(white, $colore, $percentuale);
}

@function ombra($colore, $percentuale) {
  @return mix(black, $colore, $percentuale);
}

// Funzione per calcolare rapporti
@function rapporto($larghezza, $altezza) {
  @return calc($altezza / $larghezza) * 100%;
}

// Utilizzo
.titolo {
  font-size: px-a-rem(32);        // 2rem
  margin-bottom: px-a-rem(24);    // 1.5rem
}

.pulsante {
  background: $colore-primario;

  &:hover {
    background: ombra($colore-primario, 15%);
  }

  &--chiaro {
    background: tinta($colore-primario, 85%);
    color: $colore-primario;
  }
}
```

#### Partial e import (@use, @forward vs @import)

Il sistema modulare di Sass si basa sui partial (file con prefisso underscore) e sulle direttive `@use` e `@forward`, che hanno sostituito il vecchio `@import` (ora deprecato):

```scss
// _variabili.scss (partial — il file non viene compilato singolarmente)
$colore-primario: #2563eb;
$colore-secondario: #7c3aed;
$font-base: 16px;

// _mixin.scss
@use 'variabili' as var;

@mixin pulsante-base {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-size: var.$font-base;
  cursor: pointer;
  transition: all 0.2s ease;
}

// _componenti/_pulsanti.scss
@use '../variabili' as var;
@use '../mixin';

.pulsante {
  @include mixin.pulsante-base;

  &--primario {
    background: var.$colore-primario;
    color: white;
  }

  &--secondario {
    background: var.$colore-secondario;
    color: white;
  }
}

// _index.scss (usa @forward per re-esportare)
@forward 'variabili';
@forward 'mixin';

// main.scss (punto di ingresso)
@use 'base';
@use 'componenti/pulsanti';
@use 'layout/griglia';
@use 'pagine/home';
```

Le differenze chiave tra `@use`/`@forward` e il vecchio `@import`:

- `@use` importa con namespace, evitando conflitti di nomi
- I membri privati (prefisso `_` o `-`) non vengono esposti
- Ogni file viene caricato una sola volta, migliorando le performance
- `@forward` permette di re-esportare membri da un file intermedio

#### Extend e inheritance

`@extend` permette a un selettore di ereditare gli stili di un altro. I placeholder (`%`) definiscono stili che esistono solo per essere estesi:

```scss
// Placeholder — non genera CSS da solo
%stile-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:focus {
    outline: none;
    border-color: $colore-primario;
    box-shadow: 0 0 0 3px rgba($colore-primario, 0.1);
  }
}

.input-testo {
  @extend %stile-input;
}

.textarea {
  @extend %stile-input;
  min-height: 120px;
  resize: vertical;
}

.select {
  @extend %stile-input;
  appearance: none;
  background-image: url("data:image/svg+xml,...");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
}
```

Si preferisca `@extend` con placeholder quando piu selettori condividono esattamente gli stessi stili base, e i mixin quando servono parametri o variazioni.

#### Flusso di controllo

Sass offre strutture di controllo per generare CSS dinamicamente:

```scss
// @if / @else
@mixin tema($nome) {
  @if $nome == chiaro {
    background: white;
    color: #1f2937;
  } @else if $nome == scuro {
    background: #111827;
    color: #f9fafb;
  } @else {
    @error "Tema '#{$nome}' non riconosciuto.";
  }
}

// @for — genera classi con indice numerico
@for $i from 1 through 6 {
  .m-#{$i} {
    margin: $i * 0.25rem;
  }
}
// Genera: .m-1 { margin: 0.25rem } ... .m-6 { margin: 1.5rem }

// @each — itera su liste e mappe
$colori-stato: (
  successo: #10b981,
  errore: #ef4444,
  avviso: #f59e0b,
  info: #3b82f6
);

@each $nome, $colore in $colori-stato {
  .badge-#{$nome} {
    background-color: tinta($colore, 85%);
    color: ombra($colore, 20%);
    border: 1px solid tinta($colore, 50%);
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 500;
  }
}

// @while
$livelli: 5;
$i: 1;
@while $i <= $livelli {
  .z-#{$i * 10} {
    z-index: $i * 10;
  }
  $i: $i + 1;
}
```

#### Mappe e liste

Le mappe e le liste sono strutture dati fondamentali per organizzare design token e generare classi in modo sistematico:

```scss
// Mappe — coppie chiave-valore
$breakpoints: (
  sm: 640px,
  md: 768px,
  lg: 1024px,
  xl: 1280px,
  2xl: 1536px
);

$scala-tipografica: (
  xs: 0.75rem,
  sm: 0.875rem,
  base: 1rem,
  lg: 1.125rem,
  xl: 1.25rem,
  2xl: 1.5rem,
  3xl: 1.875rem,
  4xl: 2.25rem
);

// Accesso ai valori
.testo-grande {
  font-size: map-get($scala-tipografica, xl);
}

// Iterazione su mappa
@each $nome, $dimensione in $scala-tipografica {
  .testo-#{$nome} {
    font-size: $dimensione;
  }
}

// Mixin responsive basato su mappa
@mixin breakpoint($nome) {
  $valore: map-get($breakpoints, $nome);
  @if $valore {
    @media (min-width: $valore) {
      @content;
    }
  } @else {
    @warn "Breakpoint '#{$nome}' non trovato nella mappa.";
  }
}

// Liste
$famiglie-font: ('Inter', 'Roboto', 'Open Sans');

@each $font in $famiglie-font {
  .font-#{to-lower-case($font)} {
    font-family: $font, sans-serif;
  }
}
```

#### Struttura completa di progetto

Una struttura modulare ben organizzata e fondamentale per progetti Sass di medie-grandi dimensioni:

```
styles/
├── main.scss                 # Punto di ingresso — importa tutto
├── abstracts/                # Nessun CSS generato direttamente
│   ├── _index.scss           # @forward di tutti i file
│   ├── _variabili.scss       # Variabili globali e design token
│   ├── _mixin.scss           # Mixin riutilizzabili
│   ├── _funzioni.scss        # Funzioni personalizzate
│   └── _breakpoints.scss     # Mappa e mixin breakpoint
├── base/                     # Stili di base e reset
│   ├── _index.scss
│   ├── _reset.scss           # CSS reset / normalize
│   ├── _tipografia.scss      # Stili tipografici globali
│   └── _globali.scss         # Stili globali (html, body, *)
├── componenti/               # Componenti riutilizzabili
│   ├── _index.scss
│   ├── _pulsanti.scss
│   ├── _card.scss
│   ├── _form.scss
│   ├── _modale.scss
│   ├── _navbar.scss
│   └── _badge.scss
├── layout/                   # Struttura delle pagine
│   ├── _index.scss
│   ├── _griglia.scss
│   ├── _header.scss
│   ├── _footer.scss
│   └── _sidebar.scss
├── pagine/                   # Stili specifici per pagina
│   ├── _home.scss
│   ├── _chi-siamo.scss
│   └── _contatti.scss
├── temi/                     # Varianti tematiche
│   ├── _chiaro.scss
│   └── _scuro.scss
└── vendor/                   # Stili di terze parti
    └── _normalize.scss
```

```scss
// main.scss
@use 'abstracts';
@use 'base';
@use 'layout';
@use 'componenti';
@use 'pagine';
@use 'temi';
```

---

### PostCSS

PostCSS e un tool per trasformare il CSS tramite plugin JavaScript. A differenza di Sass, non e un preprocessore monolitico ma una piattaforma modulare: il CSS viene analizzato in un AST (Abstract Syntax Tree) e ogni plugin puo operare trasformazioni specifiche. Questo approccio permette di comporre pipeline personalizzate con esattamente le funzionalita necessarie.

#### Architettura a plugin

Il nucleo di PostCSS e minimalista: si occupa solo del parsing e della serializzazione del CSS. Tutta la logica di trasformazione e delegata ai plugin:

```javascript
// postcss.config.js
module.exports = {
  plugins: [
    require('postcss-import'),          // Gestisce @import inline
    require('postcss-preset-env')({     // Funzionalita CSS future
      stage: 2,
      features: {
        'nesting-rules': true,
        'custom-media-queries': true,
        'media-query-ranges': true
      }
    }),
    require('autoprefixer'),            // Vendor prefix automatici
    require('cssnano')({                // Minificazione
      preset: ['default', {
        discardComments: { removeAll: true }
      }]
    })
  ]
};
```

#### Autoprefixer

Autoprefixer aggiunge automaticamente i vendor prefix basandosi sui dati di Can I Use e sulla configurazione browserslist del progetto:

```css
/* Input */
.elemento {
  display: flex;
  user-select: none;
  backdrop-filter: blur(10px);
}

/* Output (con i prefix necessari per i browser target) */
.elemento {
  display: flex;
  -webkit-user-select: none;
     -moz-user-select: none;
          user-select: none;
  -webkit-backdrop-filter: blur(10px);
          backdrop-filter: blur(10px);
}
```

La configurazione dei browser target si definisce nel `package.json` o in un file `.browserslistrc`:

```json
{
  "browserslist": [
    "> 1%",
    "last 2 versions",
    "not dead",
    "not ie 11"
  ]
}
```

#### postcss-preset-env

Questo plugin permette di utilizzare funzionalita CSS di prossima standardizzazione, compilandole in CSS compatibile con i browser attuali:

```css
/* Input — CSS moderno con nesting nativo e custom media */
@custom-media --viewport-medium (min-width: 768px);

.card {
  background: oklch(95% 0.02 240);

  & .titolo {
    font-size: 1.25rem;
  }

  @media (--viewport-medium) {
    display: grid;
    grid-template-columns: 1fr 2fr;
  }
}
```

#### cssnano

cssnano ottimizza e minifica il CSS per la produzione, applicando numerose micro-ottimizzazioni:

```javascript
// Configurazione dettagliata di cssnano
const cssnano = require('cssnano');

module.exports = {
  plugins: [
    cssnano({
      preset: ['advanced', {
        discardComments: { removeAll: true },
        reduceIdents: false,        // Non rinominare animazioni
        zindex: false,              // Non ricalcolare z-index
        cssDeclarationSorter: true, // Ordina le proprietà
        mergeRules: true,           // Unisci regole duplicate
        minifyFontValues: true,     // Ottimizza font shorthand
        colormin: true              // Ottimizza valori colore
      }]
    })
  ]
};
```

#### Plugin personalizzati

PostCSS permette di creare plugin personalizzati per trasformazioni specifiche del progetto:

```javascript
// plugin-spacing-custom.js
const plugin = () => {
  return {
    postcssPlugin: 'postcss-spacing-custom',
    Declaration(decl) {
      // Converti unità personalizzate in rem
      if (decl.value.includes('su')) {
        const valore = parseFloat(decl.value);
        decl.value = `${valore * 0.25}rem`;
      }
    }
  };
};

plugin.postcss = true;
module.exports = plugin;
```

#### Integrazione con build tool

PostCSS si integra nativamente con i principali build tool:

```javascript
// vite.config.js
import { defineConfig } from 'vite';

export default defineConfig({
  css: {
    postcss: './postcss.config.js'
  }
});
```

```javascript
// webpack.config.js
module.exports = {
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          'style-loader',
          'css-loader',
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                config: './postcss.config.js'
              }
            }
          }
        ]
      }
    ]
  }
};
```

---

## Utility-First: Tailwind CSS

### Fondamenti

Tailwind CSS rappresenta un cambio di paradigma nello sviluppo CSS. Invece di scrivere classi semantiche personalizzate, si compongono stili direttamente nell'HTML utilizzando classi di utilita a basso livello. Questo approccio elimina il problema della denominazione delle classi, riduce il CSS inutilizzato e velocizza notevolmente lo sviluppo.

#### Installazione e configurazione

```bash
# Installazione con npm
npm install -D tailwindcss @tailwindcss/postcss postcss

# Inizializzazione del file di configurazione
npx tailwindcss init
```

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx,vue,svelte}',
    './components/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {}
  },
  plugins: []
};
```

```css
/* src/styles/main.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

#### Filosofia delle classi di utilita

Il principio fondamentale di Tailwind e che ogni classe fa una cosa sola. Gli stili si costruiscono componendo queste classi atomiche:

```html
<!-- Approccio tradizionale (CSS semantico) -->
<div class="card">
  <h2 class="card-title">Titolo</h2>
  <p class="card-description">Descrizione del contenuto</p>
  <button class="card-button">Leggi di piu</button>
</div>

<!-- Approccio Tailwind (utility-first) -->
<div class="rounded-lg bg-white p-6 shadow-md">
  <h2 class="mb-2 text-xl font-bold text-gray-900">Titolo</h2>
  <p class="mb-4 text-gray-600">Descrizione del contenuto</p>
  <button class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white
                 hover:bg-blue-700 focus:outline-none focus:ring-2
                 focus:ring-blue-500 focus:ring-offset-2">
    Leggi di piu
  </button>
</div>
```

#### Design responsive

Tailwind utilizza un sistema di breakpoint mobile-first con prefissi intuitivi:

```html
<!-- Layout responsive: colonna su mobile, griglia su desktop -->
<div class="flex flex-col gap-4 sm:grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
  <div class="rounded-lg bg-white p-4 shadow">
    <h3 class="text-base sm:text-lg lg:text-xl">Titolo</h3>
    <p class="mt-2 text-sm text-gray-600 lg:text-base">Contenuto</p>
  </div>
</div>

<!-- Navigazione che cambia layout ai diversi breakpoint -->
<nav class="flex flex-col space-y-2
            md:flex-row md:space-x-4 md:space-y-0
            lg:space-x-8">
  <a href="#" class="text-sm md:text-base lg:text-lg">Link 1</a>
  <a href="#" class="text-sm md:text-base lg:text-lg">Link 2</a>
</nav>
```

I breakpoint predefiniti sono: `sm` (640px), `md` (768px), `lg` (1024px), `xl` (1280px), `2xl` (1536px). Ogni prefisso significa "da questa larghezza in su".

#### Stati interattivi

Tailwind gestisce pseudo-classi, pseudo-elementi e stati dei genitori tramite prefissi dedicati:

```html
<!-- Hover, focus, active -->
<button class="bg-blue-500 text-white
               hover:bg-blue-600
               focus:ring-2 focus:ring-blue-400 focus:outline-none
               active:bg-blue-700
               disabled:cursor-not-allowed disabled:opacity-50">
  Pulsante interattivo
</button>

<!-- Dark mode -->
<div class="bg-white text-gray-900 dark:bg-gray-800 dark:text-gray-100">
  <p class="text-gray-600 dark:text-gray-300">
    Contenuto che si adatta al tema
  </p>
</div>

<!-- Group hover — stile dei figli al hover del genitore -->
<div class="group rounded-lg p-4 hover:bg-blue-50">
  <h3 class="text-gray-900 group-hover:text-blue-600">Titolo</h3>
  <p class="text-gray-500 group-hover:text-blue-500">Descrizione</p>
  <span class="translate-x-0 transition-transform group-hover:translate-x-2">
    →
  </span>
</div>

<!-- Peer — stile condizionato da un fratello -->
<div>
  <input type="email" class="peer border p-2" placeholder="Email" />
  <p class="invisible text-sm text-red-500 peer-invalid:visible">
    Inserire un indirizzo email valido
  </p>
</div>

<!-- First, last, odd, even -->
<ul>
  <li class="border-b py-2 first:pt-0 last:border-b-0 last:pb-0
             odd:bg-gray-50 even:bg-white">
    Elemento lista
  </li>
</ul>
```

#### Valori arbitrari

Quando le utilita predefinite non bastano, Tailwind permette di specificare valori personalizzati con la sintassi `[valore]`:

```html
<!-- Valori arbitrari per proprietà specifiche -->
<div class="top-[117px] w-[calc(100%-2rem)] bg-[#1a1a2e]
            text-[clamp(1rem,2.5vw,2rem)]
            grid-cols-[200px_1fr_200px]
            shadow-[0_0_15px_rgba(0,0,0,0.1)]">
  Contenuto con valori personalizzati
</div>

<!-- Proprietà CSS arbitrarie -->
<div class="[mask-type:luminance] [--colore-custom:#ff6b6b]">
  Proprietà CSS personalizzate
</div>
```

### Personalizzazione

#### Configurazione del tema

Il file `tailwind.config.js` permette di personalizzare ogni aspetto del framework:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,js,jsx,tsx}'],
  darkMode: 'class', // 'media' per preferenza di sistema
  theme: {
    // Sovrascrive completamente i valori predefiniti
    screens: {
      tablet: '640px',
      laptop: '1024px',
      desktop: '1280px'
    },

    // Estende i valori predefiniti (approccio consigliato)
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554'
        },
        success: '#10b981',
        danger: '#ef4444'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace']
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem'
      },
      borderRadius: {
        '4xl': '2rem'
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        }
      }
    }
  },
  plugins: []
};
```

#### Utilita personalizzate

Si possono aggiungere utilita personalizzate tramite il layer `utilities`:

```css
@layer utilities {
  .text-balance {
    text-wrap: balance;
  }

  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
}
```

#### Plugin

L'ecosistema di plugin Tailwind estende il framework con funzionalita aggiuntive:

```javascript
// tailwind.config.js
module.exports = {
  plugins: [
    require('@tailwindcss/forms'),             // Stili di base per form
    require('@tailwindcss/typography'),         // Classe 'prose' per contenuti ricchi
    require('@tailwindcss/container-queries'),  // Container queries con @container
    require('@tailwindcss/aspect-ratio')        // Rapporti d'aspetto
  ]
};
```

```html
<!-- @tailwindcss/typography — stile automatico per contenuto editoriale -->
<article class="prose prose-lg prose-blue dark:prose-invert mx-auto max-w-3xl">
  <h1>Titolo dell'articolo</h1>
  <p>Il contenuto viene stilizzato automaticamente con tipografia
     leggibile e gradevole.</p>
  <ul>
    <li>Liste formattate</li>
    <li>Link colorati</li>
  </ul>
  <pre><code>// Anche i blocchi di codice</code></pre>
</article>

<!-- @tailwindcss/container-queries -->
<div class="@container">
  <div class="flex flex-col @md:flex-row @lg:grid @lg:grid-cols-3">
    <!-- Layout che risponde alla dimensione del contenitore -->
  </div>
</div>
```

#### Design token integration

I design token si possono centralizzare e condividere tra Tailwind e altre parti del progetto:

```javascript
// tokens/design-tokens.js
module.exports = {
  colors: {
    primary: { DEFAULT: '#2563eb', light: '#60a5fa', dark: '#1d4ed8' },
    neutral: { 100: '#f5f5f5', 500: '#737373', 900: '#171717' }
  },
  spacing: { xs: '0.25rem', sm: '0.5rem', md: '1rem', lg: '1.5rem', xl: '2rem' },
  typography: { base: '1rem', lg: '1.125rem', xl: '1.25rem' }
};

// tailwind.config.js
const tokens = require('./tokens/design-tokens');

module.exports = {
  theme: {
    extend: {
      colors: tokens.colors,
      spacing: tokens.spacing
    }
  }
};
```

### Componenti

#### @apply per stili riutilizzabili

La direttiva `@apply` permette di estrarre pattern di utilita ripetuti in classi CSS:

```css
@layer components {
  .btn {
    @apply inline-flex items-center justify-center rounded-md px-4 py-2
           text-sm font-medium transition-colors focus:outline-none
           focus:ring-2 focus:ring-offset-2 disabled:pointer-events-none
           disabled:opacity-50;
  }

  .btn-primary {
    @apply btn bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500;
  }

  .btn-secondary {
    @apply btn border border-gray-300 bg-white text-gray-700
           hover:bg-gray-50 focus:ring-gray-500;
  }

  .input {
    @apply block w-full rounded-md border border-gray-300 px-3 py-2
           text-sm placeholder-gray-400 shadow-sm
           focus:border-blue-500 focus:outline-none focus:ring-1
           focus:ring-blue-500;
  }
}
```

Tuttavia, l'uso eccessivo di `@apply` vanifica i vantaggi dell'approccio utility-first. Il team di Tailwind raccomanda di usare `@apply` con parsimonia e preferire l'estrazione di componenti nel framework JavaScript (React, Vue, Svelte) piuttosto che nel CSS.

#### Pattern di estrazione componenti

L'approccio consigliato e creare componenti nel framework JavaScript:

```jsx
// Button.jsx — componente React con Tailwind
const varianteStili = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
  secondary: 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
};

const dimensioneStili = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base'
};

function Button({ variante = 'primary', dimensione = 'md', children, ...props }) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-md font-medium
                  transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2
                  disabled:pointer-events-none disabled:opacity-50
                  ${varianteStili[variante]} ${dimensioneStili[dimensione]}`}
      {...props}
    >
      {children}
    </button>
  );
}
```

#### Class merging con tailwind-merge e clsx

Quando si compongono classi condizionalmente, e essenziale gestire correttamente i conflitti. Le librerie `clsx` e `tailwind-merge` risolvono questo problema:

```javascript
// lib/utils.js
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Funzione helper 'cn' — standard de facto nell'ecosistema Tailwind
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
```

```jsx
// Utilizzo in un componente
import { cn } from '../lib/utils';

function Card({ className, evidenziata, children }) {
  return (
    <div
      className={cn(
        'rounded-lg bg-white p-6 shadow-md',       // Stili base
        evidenziata && 'border-2 border-blue-500',  // Condizionale
        className                                    // Override dall'esterno
      )}
    >
      {children}
    </div>
  );
}

// L'override funziona correttamente grazie a twMerge
<Card className="p-8 shadow-xl">  {/* p-8 sovrascrive p-6 */}
```

### Tailwind CSS v4

Tailwind CSS v4 introduce un cambiamento architetturale significativo: la configurazione passa dal file JavaScript al CSS nativo, rendendo il framework piu semplice e allineato con gli standard web.

#### Configurazione CSS-first

```css
/* Tailwind v4 — configurazione direttamente nel CSS */
@import 'tailwindcss';

@theme {
  --color-brand-500: #3b82f6;
  --color-brand-600: #2563eb;
  --color-brand-700: #1d4ed8;

  --font-display: 'Poppins', sans-serif;
  --font-body: 'Inter', sans-serif;

  --breakpoint-tablet: 640px;
  --breakpoint-laptop: 1024px;

  --animate-fade-in: fade-in 0.5s ease-in-out;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

#### Cambiamenti principali rispetto alla v3

Le differenze fondamentali tra v3 e v4 includono:

- **Nessun file `tailwind.config.js` necessario**: la configurazione avviene tramite `@theme` nel CSS
- **Import semplificato**: `@import 'tailwindcss'` sostituisce le tre direttive `@tailwind`
- **CSS custom properties native**: i token del tema sono esposti come variabili CSS
- **Rilevamento automatico del contenuto**: non serve piu configurare `content` manualmente
- **Performance migliorate**: nuovo engine Oxide scritto in Rust, compilazione fino a 10 volte piu veloce
- **Nesting CSS nativo**: supporto completo senza plugin aggiuntivi
- **Composizione con `@theme`**: aggiungere o sovrascrivere token e piu intuitivo

```css
/* v3 — tre direttive separate */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* v4 — un solo import */
@import 'tailwindcss';
```

La migrazione da v3 a v4 e supportata da un tool automatico: `npx @tailwindcss/upgrade`.

#### Oxide Engine — architettura interna

Il cuore di Tailwind CSS v4 e il motore Oxide, una riscrittura completa in Rust che sostituisce l'intera pipeline di compilazione precedente. Oxide non e un semplice wrapper: integra un parser CSS personalizzato, un motore di risoluzione delle utilita e Lightning CSS come backend per parsing, trasformazione e ottimizzazione del CSS prodotto.

I miglioramenti di performance sono sostanziali e misurabili:

- **Build complete**: fino a 5x piu veloci rispetto alla v3 (benchmark interni mostrano range tra 3.5x e 10x a seconda della complessita del progetto)
- **Build incrementali**: oltre 100x piu veloci, misurati in microsecondi anziche millisecondi. Quando un aggiornamento non introduce nuove classi CSS, la rigenerazione e essenzialmente istantanea (fino a 182x piu veloce)
- **Consumo di memoria**: ridotto significativamente grazie alla gestione della memoria di Rust rispetto al garbage collector di Node.js

L'architettura Oxide elimina la dipendenza da PostCSS per il processing interno. Tailwind v4 puo ancora essere usato come plugin PostCSS per integrarsi con pipeline esistenti, ma internamente utilizza Lightning CSS per:

- **Parsing CSS**: analisi sintattica del CSS sorgente con supporto completo per le specifiche moderne
- **Vendor prefixing automatico**: non serve piu Autoprefixer come dipendenza separata
- **Minificazione integrata**: riduzione del bundle senza bisogno di cssnano
- **Nesting nativo**: supporto per il nesting CSS senza plugin aggiuntivi
- **Syntax lowering**: compilazione automatica di funzionalita CSS moderne in forme compatibili con i browser target

```bash
# Installazione Tailwind v4 — piu semplice rispetto alla v3
npm install tailwindcss @tailwindcss/vite   # Per progetti Vite
npm install tailwindcss @tailwindcss/postcss # Per pipeline PostCSS

# Nessun npx tailwindcss init necessario — la configurazione e nel CSS
```

```javascript
// vite.config.js — integrazione Vite nativa (approccio consigliato)
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [tailwindcss()]
});
```

#### @theme — sistema di configurazione CSS-native

La direttiva `@theme` e il sostituto completo di `tailwind.config.js`. Ogni token definito in `@theme` diventa simultaneamente una CSS custom property e una classe utility di Tailwind:

```css
@import 'tailwindcss';

@theme {
  /* Colori — generano classi come bg-brand-500, text-brand-700, etc. */
  --color-brand-50: #eff6ff;
  --color-brand-100: #dbeafe;
  --color-brand-200: #bfdbfe;
  --color-brand-300: #93c5fd;
  --color-brand-400: #60a5fa;
  --color-brand-500: #3b82f6;
  --color-brand-600: #2563eb;
  --color-brand-700: #1d4ed8;
  --color-brand-800: #1e40af;
  --color-brand-900: #1e3a8a;

  --color-surface: oklch(98% 0.005 265);
  --color-surface-elevated: oklch(100% 0 0);

  /* Tipografia */
  --font-display: 'Poppins', 'Inter', sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;

  /* Spaziatura personalizzata */
  --spacing-18: 4.5rem;
  --spacing-88: 22rem;
  --spacing-128: 32rem;

  /* Breakpoint personalizzati */
  --breakpoint-tablet: 640px;
  --breakpoint-laptop: 1024px;
  --breakpoint-desktop: 1280px;
  --breakpoint-wide: 1536px;

  /* Animazioni */
  --animate-fade-in: fade-in 0.5s ease-out;
  --animate-slide-up: slide-up 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  --animate-scale-in: scale-in 0.2s ease-out;

  /* Ombre */
  --shadow-soft: 0 1px 3px oklch(0% 0 0 / 8%);
  --shadow-elevated: 0 4px 12px oklch(0% 0 0 / 12%);

  /* Raggi di bordo */
  --radius-pill: 9999px;
  --radius-card: 0.75rem;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
```

I token definiti in `@theme` sono esposti come CSS custom properties nel `:root`, il che significa che sono accessibili anche dal JavaScript e da qualsiasi CSS esterno al framework:

```javascript
// Accesso ai token dal JavaScript
const brandColor = getComputedStyle(document.documentElement)
  .getPropertyValue('--color-brand-500');
```

#### Sovrascrittura e composizione dei temi

`@theme` supporta la composizione: si possono definire token base e poi sovrascriverli in file separati o in blocchi successivi. Questo abilita pattern come temi multipli o white-labeling:

```css
/* tema-base.css */
@import 'tailwindcss';

@theme {
  --color-primary: #2563eb;
  --color-primary-foreground: #ffffff;
  --color-secondary: #7c3aed;
  --radius-base: 0.5rem;
}

/* tema-cliente-a.css — sovrascrive solo i token necessari */
@import './tema-base.css';

@theme {
  --color-primary: #059669;
  --color-primary-foreground: #ffffff;
  --color-secondary: #0891b2;
  --radius-base: 0.75rem;
}
```

Per rimuovere completamente i valori predefiniti di un namespace del tema e ricominciare da zero, si utilizza `initial`:

```css
@theme {
  --color-*: initial;          /* Rimuove TUTTI i colori predefiniti */
  --color-brand-500: #3b82f6;  /* Definisce solo quelli necessari */
  --color-brand-600: #2563eb;
}
```

#### Lightning CSS — il backend di compilazione

Lightning CSS, sviluppato da Devon Govett (autore anche di Parcel), e il motore che Tailwind v4 utilizza internamente per tutte le trasformazioni CSS. Scritto in Rust, offre performance significativamente superiori rispetto alla combinazione PostCSS + Autoprefixer + cssnano:

- **Parsing**: 2x piu veloce rispetto a PostCSS
- **Vendor prefixing**: integrato nativamente, elimina la necessita di Autoprefixer
- **Minificazione**: integrata, elimina la necessita di cssnano
- **Nesting CSS**: supporto nativo per la specifica CSS Nesting
- **`@property`**: supporto per le registered custom properties
- **`color-mix()`**: supporto nativo per le funzioni di colore moderne
- **Cascade Layers**: supporto completo per `@layer`

Lightning CSS gestisce anche la trasformazione delle funzionalita CSS moderne in forme compatibili con i browser target configurati nel `browserslist` del progetto, fungendo da sostituto di `postcss-preset-env` per la maggior parte dei casi d'uso.

#### Rilevamento automatico del contenuto

In Tailwind v4, non e piu necessario configurare manualmente l'array `content` nel file di configurazione. Il framework rileva automaticamente i file del progetto tramite euristiche intelligenti:

- Scansiona tutti i file nella directory del progetto (escludendo `node_modules`, `.git`, e directory di build)
- Rispetta le regole del `.gitignore`
- Supporta pattern glob per inclusioni ed esclusioni personalizzate

Per casi particolari dove il rilevamento automatico non e sufficiente, si possono specificare sorgenti aggiuntive tramite la direttiva `@source`:

```css
@import 'tailwindcss';

/* Aggiungere sorgenti extra (es. pacchetti in node_modules) */
@source "../node_modules/@mia-libreria/componenti/src/**/*.tsx";

/* Escludere directory */
@source not "../src/legacy/**";
```

#### Plugin e preset in Tailwind v4

L'ecosistema di plugin evolve con la v4. I plugin ufficiali si integrano tramite import CSS:

```css
@import 'tailwindcss';
@import '@tailwindcss/typography';
@import '@tailwindcss/forms';
@import '@tailwindcss/container-queries';
```

I plugin JavaScript della v3 rimangono compatibili tramite la direttiva `@plugin`:

```css
@import 'tailwindcss';

/* Plugin JavaScript legacy */
@plugin "@tailwindcss/forms";
@plugin "./plugins/mio-plugin-personalizzato.js";
```

I **preset** permettono di raggruppare configurazioni di tema riutilizzabili tra piu progetti:

```css
/* preset-azienda.css */
@theme {
  --color-primary: #0066cc;
  --color-secondary: #ff6600;
  --font-body: 'Roboto', sans-serif;
  --radius-base: 0.375rem;
}

/* In ogni progetto dell'azienda */
@import 'tailwindcss';
@import './preset-azienda.css';

@theme {
  /* Override specifici del progetto */
  --color-accent: #10b981;
}
```

Questo approccio consente di mantenere coerenza visiva tra i progetti aziendali permettendo personalizzazioni locali.

---

## Component-Based: Bootstrap

### Fondamenti Bootstrap

Bootstrap e il framework CSS component-based piu utilizzato al mondo. Offre un sistema completo di componenti predefiniti, una griglia responsive flessibile e utilita CSS pronte all'uso. La versione attuale (Bootstrap 5) ha eliminato la dipendenza da jQuery e utilizza JavaScript vanilla.

#### Installazione

```bash
# Installazione tramite npm
npm install bootstrap
npm install @popperjs/core   # Necessario per dropdown, tooltip, popover

# Oppure tramite CDN nell'HTML
```

```html
<!-- Installazione via CDN -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
      rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js">
</script>
```

```javascript
// Import in un progetto con bundler
import 'bootstrap/dist/css/bootstrap.min.css';
import * as bootstrap from 'bootstrap';

// Oppure import selettivo dei componenti SCSS
// nel file main.scss:
// @import 'bootstrap/scss/functions';
// @import 'bootstrap/scss/variables';
// @import 'bootstrap/scss/mixins';
// @import 'bootstrap/scss/grid';
// @import 'bootstrap/scss/buttons';
```

#### Sistema a griglia

Il sistema a griglia di Bootstrap si basa su flexbox con un layout a 12 colonne:

```html
<!-- Griglia base responsive -->
<div class="container">
  <div class="row">
    <!-- 12 colonne su mobile, 6 su medium, 4 su large -->
    <div class="col-12 col-md-6 col-lg-4">
      <div class="p-3 bg-light border">Colonna 1</div>
    </div>
    <div class="col-12 col-md-6 col-lg-4">
      <div class="p-3 bg-light border">Colonna 2</div>
    </div>
    <div class="col-12 col-md-12 col-lg-4">
      <div class="p-3 bg-light border">Colonna 3</div>
    </div>
  </div>
</div>

<!-- Colonne con larghezza automatica -->
<div class="container">
  <div class="row">
    <div class="col">Uguale</div>
    <div class="col">Uguale</div>
    <div class="col">Uguale</div>
  </div>
</div>

<!-- Offset e ordinamento -->
<div class="row">
  <div class="col-md-4 offset-md-2 order-md-2">Prima visualmente su desktop</div>
  <div class="col-md-4 order-md-1">Seconda visualmente su desktop</div>
</div>

<!-- Gutter (spaziatura tra colonne) -->
<div class="row g-4">  <!-- g-0 a g-5, gx- per orizzontale, gy- per verticale -->
  <div class="col-6"><div class="p-3 border">Con gutter</div></div>
  <div class="col-6"><div class="p-3 border">Con gutter</div></div>
</div>
```

I breakpoint della griglia sono: `sm` (>=576px), `md` (>=768px), `lg` (>=992px), `xl` (>=1200px), `xxl` (>=1400px). Il `container` ha varianti `container-sm`, `container-md`, etc., e `container-fluid` per larghezza piena.

#### Utilita di spaziatura

Bootstrap fornisce classi di spaziatura sistematiche con la notazione `{proprieta}{lato}-{breakpoint}-{dimensione}`:

```html
<!-- m = margin, p = padding -->
<!-- t = top, b = bottom, s = start(left), e = end(right), x = orizzontale, y = verticale -->
<!-- 0-5 o auto -->

<div class="mt-3 mb-4 px-3 py-2">Spaziatura</div>
<div class="mx-auto" style="width: 200px;">Centrato orizzontalmente</div>
<div class="mt-md-5 mt-2">Spaziatura responsive</div>
```

#### Tipografia

```html
<h1 class="display-1">Display 1</h1>
<h2 class="display-4">Display 4</h2>
<p class="lead">Paragrafo in evidenza con font-size piu grande.</p>
<p class="fs-4 fw-bold text-muted">Testo personalizzato</p>
<p class="text-center text-md-start text-uppercase">Allineamento responsive</p>
<mark>Evidenziato</mark>
<del>Cancellato</del>
<abbr title="Abbreviazione">abbr</abbr>
```

#### Colori

```html
<!-- Colori tematici -->
<p class="text-primary">Primario (blu)</p>
<p class="text-secondary">Secondario (grigio)</p>
<p class="text-success">Successo (verde)</p>
<p class="text-danger">Pericolo (rosso)</p>
<p class="text-warning">Avviso (giallo)</p>
<p class="text-info">Informazione (azzurro)</p>

<!-- Sfondi -->
<div class="bg-primary text-white p-3">Sfondo primario</div>
<div class="bg-light text-dark p-3">Sfondo chiaro</div>
<div class="bg-dark text-white p-3">Sfondo scuro</div>
```

### Componenti Bootstrap

Bootstrap offre una vasta libreria di componenti pronti all'uso:

#### Navbar

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container">
    <a class="navbar-brand" href="#">MioSito</a>
    <button class="navbar-toggler" type="button"
            data-bs-toggle="collapse" data-bs-target="#navMenu">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navMenu">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <a class="nav-link active" href="#">Home</a>
        </li>
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" role="button"
             data-bs-toggle="dropdown">Servizi</a>
          <ul class="dropdown-menu">
            <li><a class="dropdown-item" href="#">Web Design</a></li>
            <li><a class="dropdown-item" href="#">Sviluppo</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="#">Consulenza</a></li>
          </ul>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#">Contatti</a>
        </li>
      </ul>
    </div>
  </div>
</nav>
```

#### Card

```html
<div class="card" style="width: 18rem;">
  <img src="immagine.jpg" class="card-img-top" alt="Immagine card">
  <div class="card-body">
    <h5 class="card-title">Titolo della card</h5>
    <p class="card-text">Descrizione breve del contenuto della card.</p>
    <a href="#" class="btn btn-primary">Vai al dettaglio</a>
  </div>
  <div class="card-footer text-muted">
    Pubblicato 2 giorni fa
  </div>
</div>

<!-- Card group per layout uniforme -->
<div class="row row-cols-1 row-cols-md-3 g-4">
  <div class="col">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title">Card 1</h5>
        <p class="card-text">Contenuto variabile.</p>
      </div>
    </div>
  </div>
  <!-- Ripetere per altre card -->
</div>
```

#### Modal

```html
<!-- Pulsante che apre il modal -->
<button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#mioModal">
  Apri Modal
</button>

<!-- Struttura del modal -->
<div class="modal fade" id="mioModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Conferma azione</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <p>Sei sicuro di voler procedere con questa operazione?</p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Annulla</button>
        <button class="btn btn-primary">Conferma</button>
      </div>
    </div>
  </div>
</div>
```

#### Form, Buttons, Alerts e altri componenti

```html
<!-- Form -->
<form>
  <div class="mb-3">
    <label for="email" class="form-label">Indirizzo email</label>
    <input type="email" class="form-control" id="email"
           placeholder="nome@esempio.com">
    <div class="form-text">Non condivideremo mai la tua email.</div>
  </div>
  <div class="mb-3">
    <label for="password" class="form-label">Password</label>
    <input type="password" class="form-control" id="password">
  </div>
  <div class="mb-3 form-check">
    <input type="checkbox" class="form-check-input" id="ricorda">
    <label class="form-check-label" for="ricorda">Ricordami</label>
  </div>
  <div class="mb-3">
    <select class="form-select">
      <option selected>Seleziona un'opzione</option>
      <option value="1">Opzione 1</option>
      <option value="2">Opzione 2</option>
    </select>
  </div>
  <button type="submit" class="btn btn-primary">Invia</button>
</form>

<!-- Pulsanti -->
<button class="btn btn-primary">Primario</button>
<button class="btn btn-outline-secondary">Outline</button>
<button class="btn btn-success btn-lg">Grande</button>
<button class="btn btn-danger btn-sm">Piccolo</button>
<div class="btn-group">
  <button class="btn btn-primary">Sinistra</button>
  <button class="btn btn-primary">Centro</button>
  <button class="btn btn-primary">Destra</button>
</div>

<!-- Alert -->
<div class="alert alert-success alert-dismissible fade show" role="alert">
  <strong>Operazione completata!</strong> I dati sono stati salvati correttamente.
  <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>

<div class="alert alert-danger" role="alert">
  Errore: compilare tutti i campi obbligatori.
</div>
```

#### Componenti JavaScript

I componenti interattivi di Bootstrap possono essere controllati sia tramite attributi data che tramite l'API JavaScript:

```html
<!-- Controllo tramite attributi data (approccio dichiarativo) -->
<button data-bs-toggle="tooltip" data-bs-placement="top" title="Suggerimento">
  Passa il mouse
</button>

<!-- Carousel -->
<div id="mioCarousel" class="carousel slide" data-bs-ride="carousel">
  <div class="carousel-indicators">
    <button data-bs-target="#mioCarousel" data-bs-slide-to="0" class="active"></button>
    <button data-bs-target="#mioCarousel" data-bs-slide-to="1"></button>
  </div>
  <div class="carousel-inner">
    <div class="carousel-item active">
      <img src="slide1.jpg" class="d-block w-100" alt="Slide 1">
    </div>
    <div class="carousel-item">
      <img src="slide2.jpg" class="d-block w-100" alt="Slide 2">
    </div>
  </div>
  <button class="carousel-control-prev" data-bs-target="#mioCarousel" data-bs-slide="prev">
    <span class="carousel-control-prev-icon"></span>
  </button>
  <button class="carousel-control-next" data-bs-target="#mioCarousel" data-bs-slide="next">
    <span class="carousel-control-next-icon"></span>
  </button>
</div>
```

```javascript
// Controllo tramite API JavaScript (approccio programmatico)
import { Modal, Tooltip, Toast } from 'bootstrap';

// Modal
const modalEl = document.getElementById('mioModal');
const modal = new Modal(modalEl, { backdrop: 'static', keyboard: false });
modal.show();

// Inizializzazione tooltip su tutti gli elementi
document.querySelectorAll('[data-bs-toggle="tooltip"]')
  .forEach(el => new Tooltip(el));

// Toast
const toastEl = document.getElementById('mioToast');
const toast = new Toast(toastEl, { autohide: true, delay: 3000 });
toast.show();

// Eventi
modalEl.addEventListener('hidden.bs.modal', () => {
  console.log('Modal chiuso');
});
```

### Personalizzazione Bootstrap

#### Override delle variabili Sass

Il metodo raccomandato per personalizzare Bootstrap e sovrascrivere le variabili Sass prima di importare i sorgenti:

```scss
// custom-bootstrap.scss

// 1. Sovrascrittura delle variabili (PRIMA dell'import)
$primary: #6366f1;
$secondary: #8b5cf6;
$success: #10b981;
$danger: #ef4444;
$warning: #f59e0b;
$info: #06b6d4;
$dark: #111827;

$font-family-base: 'Inter', system-ui, sans-serif;
$font-size-base: 1rem;
$line-height-base: 1.6;

$border-radius: 0.5rem;
$border-radius-lg: 0.75rem;
$border-radius-sm: 0.375rem;

$box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
$box-shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

$spacer: 1rem;
$grid-gutter-width: 2rem;

$enable-rounded: true;
$enable-shadows: true;
$enable-negative-margins: true;

// 2. Import dei sorgenti Bootstrap
@import 'bootstrap/scss/bootstrap';

// 3. Stili personalizzati aggiuntivi (DOPO l'import)
.navbar {
  box-shadow: $box-shadow;
}
```

#### Build personalizzata

Per ridurre la dimensione del bundle, si possono importare solo i componenti necessari:

```scss
// bootstrap-custom.scss — Import selettivo

// Obbligatori
@import 'bootstrap/scss/functions';
@import 'bootstrap/scss/variables';
@import 'bootstrap/scss/variables-dark';
@import 'bootstrap/scss/maps';
@import 'bootstrap/scss/mixins';
@import 'bootstrap/scss/root';

// Opzionali — importare solo cio che serve
@import 'bootstrap/scss/reboot';
@import 'bootstrap/scss/type';
@import 'bootstrap/scss/containers';
@import 'bootstrap/scss/grid';
@import 'bootstrap/scss/buttons';
@import 'bootstrap/scss/card';
@import 'bootstrap/scss/nav';
@import 'bootstrap/scss/navbar';
@import 'bootstrap/scss/modal';
@import 'bootstrap/scss/forms';
@import 'bootstrap/scss/utilities';
@import 'bootstrap/scss/utilities/api';
```

#### Bootstrap Icons

Bootstrap fornisce una libreria di icone SVG integrata:

```bash
npm install bootstrap-icons
```

```html
<!-- Utilizzo tramite font -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css">

<i class="bi bi-house-fill"></i>
<i class="bi bi-person-circle fs-3 text-primary"></i>
<i class="bi bi-search"></i>

<!-- Utilizzo tramite SVG inline -->
<svg class="bi" width="24" height="24" fill="currentColor">
  <use xlink:href="bootstrap-icons.svg#heart-fill"/>
</svg>
```

---

## Metodologie CSS

Le metodologie CSS sono convenzioni e architetture per organizzare il codice CSS in modo scalabile e manutenibile. Non sono framework da installare, ma approcci concettuali applicabili a qualsiasi progetto.

### BEM (Block Element Modifier)

BEM e la metodologia di naming convention piu diffusa. Organizza il CSS in tre livelli concettuali:

- **Block**: componente autonomo e riutilizzabile (`.card`, `.menu`, `.form`)
- **Element**: parte interna del blocco che non ha senso indipendente (`.card__title`, `.menu__item`)
- **Modifier**: variante di un blocco o elemento (`.card--evidenziata`, `.menu__item--attivo`)

La sintassi segue il pattern: `.blocco__elemento--modificatore`

```html
<!-- Esempio completo BEM -->
<form class="form-ricerca form-ricerca--espansa">
  <div class="form-ricerca__campo">
    <label class="form-ricerca__etichetta">Cerca</label>
    <input class="form-ricerca__input form-ricerca__input--grande" type="text">
  </div>
  <button class="form-ricerca__pulsante form-ricerca__pulsante--primario">
    Cerca
  </button>
</form>
```

```scss
// CSS corrispondente
.form-ricerca {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 0.5rem;

  &--espansa {
    width: 100%;
  }

  &__campo {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__etichetta {
    font-size: 0.875rem;
    font-weight: 500;
    color: #4b5563;
  }

  &__input {
    padding: 0.5rem 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;

    &--grande {
      padding: 0.75rem 1rem;
      font-size: 1.125rem;
    }
  }

  &__pulsante {
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 0.375rem;
    cursor: pointer;

    &--primario {
      background: #2563eb;
      color: white;
    }
  }
}
```

**Vantaggi di BEM**: selettori a bassa specificita (una sola classe), struttura prevedibile, facile da trovare nel codice, evita conflitti di nomi. **Svantaggi**: nomi di classe lunghi, richiede disciplina nel team, il markup puo risultare verboso.

### OOCSS (Object-Oriented CSS)

OOCSS, ideato da Nicole Sullivan, si basa su due principi fondamentali:

**Separazione di struttura e skin (aspetto)**:

```css
/* Struttura — layout e dimensioni */
.oggetto-media {
  display: flex;
  gap: 1rem;
  padding: 1rem;
}

/* Skin — aspetto visivo */
.tema-chiaro {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
}

.tema-scuro {
  background: #1f2937;
  color: white;
  border-radius: 0.5rem;
}
```

```html
<!-- Combinazione struttura + skin -->
<div class="oggetto-media tema-chiaro">...</div>
<div class="oggetto-media tema-scuro">...</div>
```

**Separazione di contenitore e contenuto**:

```css
/* ERRATO — stile dipendente dal contenitore */
.sidebar h3 { font-size: 1.25rem; color: blue; }

/* CORRETTO — stile indipendente, riutilizzabile ovunque */
.titolo-sezione { font-size: 1.25rem; color: blue; }
```

### SMACSS

SMACSS (Scalable and Modular Architecture for CSS) organizza gli stili in cinque categorie:

```css
/* 1. BASE — Stili di default per elementi HTML (no classi) */
html { font-size: 16px; }
body { font-family: 'Inter', sans-serif; line-height: 1.6; color: #1f2937; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }

/* 2. LAYOUT — Struttura delle aree principali della pagina (prefisso l-) */
.l-header { position: sticky; top: 0; z-index: 100; }
.l-sidebar { width: 250px; }
.l-contenuto { flex: 1; }
.l-footer { padding: 2rem 0; }

/* 3. MODULE — Componenti riutilizzabili */
.card { background: white; border-radius: 0.5rem; padding: 1.5rem; }
.card-titolo { font-size: 1.25rem; margin-bottom: 0.5rem; }
.nav-item { padding: 0.5rem 1rem; }

/* 4. STATE — Stati dinamici (prefisso is-) */
.is-attivo { font-weight: bold; color: #2563eb; }
.is-nascosto { display: none; }
.is-disabilitato { opacity: 0.5; pointer-events: none; }
.is-caricamento { position: relative; }

/* 5. THEME — Varianti tematiche */
.tema-festival .l-header { background: #7c3aed; }
.tema-festival .card { border-left: 4px solid #7c3aed; }
```

### ITCSS (Inverted Triangle CSS)

ITCSS, ideato da Harry Roberts, organizza il CSS come un triangolo invertito dove gli stili procedono dal piu generico al piu specifico. Ogni layer successivo ha maggiore specificita e portata piu ristretta:

```
  SETTINGS     ← Variabili, design token (nessun CSS generato)
   TOOLS       ← Mixin e funzioni (nessun CSS generato)
    GENERIC    ← Reset, normalize, box-sizing
     ELEMENTS  ← Stili per elementi HTML nativi (h1, p, a)
      OBJECTS  ← Pattern strutturali astratti (media object, griglia)
       COMP.   ← Componenti UI specifici (card, navbar, form)
        UTILS  ← Utilità con !important (visibilità, spaziatura)
```

```scss
// Organizzazione file ITCSS
// settings/_variabili.scss
$colori: (primario: #2563eb, secondario: #7c3aed);
$font-stack: 'Inter', sans-serif;

// tools/_mixin.scss
@mixin breakpoint($nome) { /* ... */ }

// generic/_reset.scss
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

// elements/_tipografia.scss
h1, h2, h3 { line-height: 1.2; font-weight: 700; }
a { color: map-get($colori, primario); }

// objects/_contenitore.scss
.o-contenitore { max-width: 1200px; margin: 0 auto; padding: 0 1rem; }
.o-griglia { display: grid; gap: 1rem; }

// components/_card.scss
.c-card { background: white; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.c-card__body { padding: 1.5rem; }

// utilities/_visibilita.scss
.u-nascosto { display: none !important; }
.u-sr-only { position: absolute !important; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
```

Il vantaggio principale di ITCSS e che gestisce la specificita in modo ordinato, evitando guerre di specificita e sovrascritture caotiche.

### Cube CSS

Cube CSS (Composition Utility Block Exception) e una metodologia moderna ideata da Andy Bell che combina il meglio di diversi approcci:

```html
<!-- Cube CSS in pratica -->
<article class="card [ flow ] [ bg-light border-radius-md ]" data-stato="evidenziata">
  <h2 class="card__titolo [ text-lg font-bold ]">Titolo</h2>
  <p class="[ text-base color-muted ]">Descrizione del contenuto.</p>
  <a href="#" class="card__link [ text-sm font-medium ]">Leggi di piu</a>
</article>
```

```css
/* COMPOSITION — layout macro, come fluiscono gli elementi */
.flow > * + * {
  margin-top: var(--flow-space, 1em);
}

.cluster {
  display: flex;
  flex-wrap: wrap;
  gap: var(--cluster-space, 1rem);
}

.sidebar-layout {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

/* UTILITY — classi atomiche a singolo scopo */
.bg-light { background: var(--color-light); }
.text-lg { font-size: var(--text-lg); }
.font-bold { font-weight: 700; }
.border-radius-md { border-radius: var(--radius-md); }

/* BLOCK — componenti contestuali con stili specifici */
.card {
  padding: var(--space-m);
}

.card__titolo {
  color: var(--color-dark);
}

.card__link {
  display: inline-flex;
  align-items: center;
  color: var(--color-primary);
}

/* EXCEPTION — variazioni basate su stato o contesto */
.card[data-stato='evidenziata'] {
  border: 2px solid var(--color-primary);
  box-shadow: var(--shadow-lg);
}
```

Cube CSS utilizza le parentesi quadre `[ ]` nei nomi delle classi HTML come convenzione visiva per separare i diversi tipi di classi (composizione, utilita, blocco). Questo migliora la leggibilita del markup.

---

## Librerie di Componenti Headless

Le librerie headless rappresentano un paradigma emergente nello sviluppo frontend: forniscono componenti con logica, accessibilita e gestione dello stato completi, ma senza alcuno stile visivo predefinito. Questo approccio separa nettamente il comportamento dalla presentazione, lasciando allo sviluppatore la liberta totale di applicare qualsiasi sistema di stili.

### Radix UI

Radix UI e la libreria headless piu diffusa nell'ecosistema React. Sviluppata da WorkOS, fornisce primitive UI accessibili, non stilizzate, con supporto completo per ARIA, gestione del focus e navigazione da tastiera.

#### Caratteristiche principali

- **Accessibilita nativa**: ogni componente implementa i pattern ARIA corretti senza configurazione
- **Composizione**: architettura basata su compound components che permette la massima flessibilita
- **Gestione del focus**: trap del focus nei dialog, navigation da tastiera nei menu, roving tabindex
- **Animazioni**: supporto per animazioni di entrata/uscita tramite attributi `data-state`
- **Portali**: rendering automatico in portali per overlay, tooltip e popover
- **Copertura**: oltre 30 componenti (Dialog, Dropdown, Tooltip, Accordion, Tabs, Select, Popover, Toast, etc.)

```bash
# Installazione dei singoli componenti
npm install @radix-ui/react-dialog
npm install @radix-ui/react-dropdown-menu
npm install @radix-ui/react-tooltip
```

```tsx
// Esempio: Dialog accessibile con Radix + Tailwind
import * as Dialog from '@radix-ui/react-dialog';

function ConfermaDialog() {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button className="rounded-md bg-blue-600 px-4 py-2 text-white">
          Apri Dialog
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50
                                   data-[state=open]:animate-fade-in" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2
                                   -translate-y-1/2 rounded-lg bg-white p-6
                                   shadow-xl data-[state=open]:animate-scale-in">
          <Dialog.Title className="text-lg font-semibold">
            Conferma eliminazione
          </Dialog.Title>
          <Dialog.Description className="mt-2 text-sm text-gray-600">
            Questa azione non puo essere annullata.
          </Dialog.Description>
          <div className="mt-4 flex justify-end gap-3">
            <Dialog.Close asChild>
              <button className="rounded-md px-4 py-2 text-gray-700">
                Annulla
              </button>
            </Dialog.Close>
            <button className="rounded-md bg-red-600 px-4 py-2 text-white">
              Elimina
            </button>
          </div>
          <Dialog.Close asChild>
            <button className="absolute right-3 top-3" aria-label="Chiudi">
              ✕
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

### Headless UI

Headless UI, sviluppata dal team di Tailwind Labs, e progettata specificamente per integrarsi con Tailwind CSS. Offre un insieme piu ridotto di componenti (16 principali) ma con un'integrazione nativa con le transition di Tailwind.

```tsx
// Esempio: Menu dropdown con Headless UI
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';

function OpzioniMenu() {
  return (
    <Menu>
      <MenuButton className="rounded-md bg-gray-800 px-4 py-2 text-white">
        Opzioni
      </MenuButton>
      <MenuItems className="mt-1 rounded-md bg-white py-1 shadow-lg ring-1
                            ring-black/5">
        <MenuItem>
          {({ active }) => (
            <button className={`block w-full px-4 py-2 text-left text-sm
                               ${active ? 'bg-blue-50 text-blue-700' : 'text-gray-700'}`}>
              Modifica
            </button>
          )}
        </MenuItem>
        <MenuItem>
          {({ active }) => (
            <button className={`block w-full px-4 py-2 text-left text-sm
                               ${active ? 'bg-red-50 text-red-700' : 'text-gray-700'}`}>
              Elimina
            </button>
          )}
        </MenuItem>
      </MenuItems>
    </Menu>
  );
}
```

### Ark UI

Ark UI, sviluppata dal team di Chakra UI, si distingue per il supporto multi-framework: funziona con React, Vue e Solid. Utilizza state machine (basate su Zag.js) per gestire la logica dei componenti, garantendo un comportamento identico indipendentemente dal framework:

- **React, Vue, Solid**: stessa API e comportamento su tutti i framework supportati
- **State machine-driven**: la logica e modellata come macchine a stati finiti, rendendo il comportamento prevedibile e testabile
- **Styling agnostico**: compatibile con qualsiasi approccio (Tailwind, Panda CSS, CSS Modules, styled-components)
- **Copertura ampia**: oltre 40 componenti, inclusi pattern complessi come DatePicker, ColorPicker e TreeView

### Tabella comparativa delle librerie headless

| Caratteristica | Radix UI | Headless UI | Ark UI |
|----------------|----------|-------------|--------|
| Framework | React | React | React, Vue, Solid |
| Componenti | 30+ | 16 | 40+ |
| Accessibilita | Eccellente | Buona | Eccellente |
| Integrazione Tailwind | Buona | Nativa | Buona |
| Dimensione bundle | Modulare | ~10kb | Modulare |
| Maturita | Alta | Alta | Media |
| Documentazione | Eccellente | Buona | Buona |
| Caso d'uso ideale | Design system custom | Progetti Tailwind | Multi-framework |

---

## shadcn/ui — Component System

shadcn/ui non e una libreria di componenti tradizionale installata come dipendenza npm. E un sistema di componenti copiabili: il codice sorgente di ogni componente viene aggiunto direttamente al progetto, diventando proprieta dello sviluppatore. Questo approccio elimina la dipendenza dal versionamento della libreria e permette la personalizzazione totale.

### Architettura e filosofia

Il sistema si basa su tre pilastri:

1. **Radix UI Primitives**: fornisce la logica, l'accessibilita e la gestione dello stato
2. **Tailwind CSS**: fornisce lo stile visivo tramite classi utility
3. **CSS custom properties**: token semantici che permettono il theming globale

```bash
# Inizializzazione in un progetto esistente
npx shadcn@latest init

# Aggiunta di singoli componenti
npx shadcn@latest add button
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
npx shadcn@latest add form
npx shadcn@latest add table
```

Dopo l'esecuzione di `add`, il codice del componente viene copiato nella directory configurata (tipicamente `src/components/ui/`). Da quel momento e codice del progetto, modificabile senza vincoli.

### Sistema di theming

shadcn/ui utilizza un sistema di token semantici basato su CSS custom properties. I colori usano coppie `background` / `foreground` che permettono al testo e alle icone di adattarsi automaticamente alla superficie su cui si trovano:

```css
/* Tema chiaro — definizione dei token nel :root */
:root {
  --background: 0 0% 100%;          /* Sfondo pagina */
  --foreground: 222.2 84% 4.9%;     /* Testo principale */
  --card: 0 0% 100%;                /* Sfondo card */
  --card-foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;     /* Azione primaria */
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;       /* Azione secondaria */
  --secondary-foreground: 222.2 47.4% 11.2%;
  --muted: 210 40% 96.1%;           /* Elementi attenuati */
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96.1%;          /* Accenti e hover */
  --accent-foreground: 222.2 47.4% 11.2%;
  --destructive: 0 84.2% 60.2%;     /* Azioni distruttive */
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;      /* Bordi */
  --input: 214.3 31.8% 91.4%;       /* Input */
  --ring: 222.2 84% 4.9%;           /* Focus ring */
  --radius: 0.5rem;                 /* Raggio base */
}

/* Tema scuro — override degli stessi token */
.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;
  --primary: 210 40% 98%;
  --primary-foreground: 222.2 47.4% 11.2%;
  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;
  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;
  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;
  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 212.7 26.8% 83.9%;
}
```

Cambiare il valore di `--radius` aggiorna automaticamente la scala dei raggi in tutti i componenti. Analogamente, cambiare `--primary` modifica il colore di tutti i bottoni, link e elementi di accento.

### Personalizzazione dei componenti

Poiche il codice e di proprieta del progetto, la personalizzazione avviene modificando direttamente i file:

```tsx
// components/ui/button.tsx — componente generato da shadcn
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium ' +
  'ring-offset-background transition-colors focus-visible:outline-none ' +
  'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ' +
  'disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
```

Il pattern usa `class-variance-authority` (cva) per definire le varianti in modo type-safe, e la funzione `cn` (basata su `clsx` + `tailwind-merge`) per comporre e risolvere conflitti tra classi.

### Componenti disponibili e pattern comuni

shadcn/ui offre componenti per le categorie principali di una UI:

- **Layout**: Card, Separator, Collapsible, Resizable, ScrollArea
- **Navigazione**: Tabs, Menubar, NavigationMenu, Breadcrumb, Pagination, Sidebar
- **Form**: Input, Textarea, Select, Checkbox, RadioGroup, Switch, Slider, DatePicker, Combobox
- **Overlay**: Dialog, AlertDialog, Sheet, Popover, Tooltip, HoverCard, ContextMenu
- **Feedback**: Alert, Toast, Progress, Skeleton, Badge
- **Dati**: Table, DataTable (con TanStack Table), Chart (con Recharts), Calendar

---

## CSS-in-JS — Analisi Comparativa

CSS-in-JS e un insieme di approcci che permettono di scrivere stili direttamente nel codice JavaScript, co-locando stili e logica nello stesso file o modulo. L'ecosistema si e diviso in due categorie fondamentalmente diverse: soluzioni runtime e soluzioni zero-runtime (a tempo di compilazione).

### Soluzioni Runtime: styled-components e Emotion

Le soluzioni runtime iniettano gli stili nel DOM durante il rendering del componente. Questo offre massima dinamicita ma ha costi di performance.

#### styled-components

styled-components, creato da Max Stoiber e Glen Maddern, ha pionieristicamente introdotto il pattern dei tagged template literals per la definizione degli stili:

```tsx
import styled from 'styled-components';

const Card = styled.div`
  background: ${props => props.theme.colors.surface};
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }
`;

const Title = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: ${props => props.theme.colors.text};
  margin-bottom: 0.5rem;
`;

// Composizione con estensione
const CardEvidenziata = styled(Card)`
  border-left: 4px solid ${props => props.theme.colors.primary};
`;
```

#### Emotion

Emotion offre due API: una basata su `css` prop e una basata su `styled` (compatibile con styled-components). E il motore CSS-in-JS dietro MUI (Material UI):

```tsx
/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';
import styled from '@emotion/styled';

// API con css prop
function Badge({ children, variante = 'info' }) {
  return (
    <span
      css={css`
        display: inline-flex;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
        background: ${variante === 'info' ? '#dbeafe' : '#fee2e2'};
        color: ${variante === 'info' ? '#1d4ed8' : '#dc2626'};
      `}
    >
      {children}
    </span>
  );
}
```

#### Limitazioni delle soluzioni runtime

Le soluzioni runtime presentano problematiche significative nei contesti moderni:

- **Incompatibilita con React Server Components**: iniettano stili tramite React context, che non e disponibile nei Server Components
- **Overhead di rendering**: ogni render richiede la generazione e l'iniezione degli stili nel DOM
- **Dimensione del bundle**: il runtime della libreria (20-40kb gzip) viene incluso nel bundle client
- **Benchmark**: styled-components v6 impiega circa 62ms per 1.000 re-render di componenti, Emotion circa 38ms

I download di entrambe le librerie sono in stagnazione o declino dal 2023, indicando uno spostamento dell'ecosistema verso soluzioni alternative.

### Soluzioni Zero-Runtime: Panda CSS e vanilla-extract

Le soluzioni zero-runtime estraggono gli stili a tempo di compilazione, producendo CSS statico senza alcun runtime JavaScript nel browser.

#### Panda CSS

Panda CSS, creato dal team di Chakra UI, offre un'esperienza di authoring familiare per chi viene da CSS-in-JS, ma genera CSS atomico statico:

```tsx
// panda.config.ts
import { defineConfig } from '@pandacss/dev';

export default defineConfig({
  preflight: true,
  include: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    tokens: {
      colors: {
        primary: { value: '#2563eb' },
        surface: { value: '#f9fafb' }
      }
    }
  },
  outdir: 'styled-system'
});
```

```tsx
// Utilizzo con pattern functions
import { css } from '../styled-system/css';

function Card({ children }) {
  return (
    <div className={css({
      bg: 'surface',
      borderRadius: 'md',
      p: '6',
      shadow: 'sm',
      _hover: { shadow: 'md', transform: 'translateY(-2px)' }
    })}>
      {children}
    </div>
  );
}
```

Panda CSS e entrato in modalita maintenance nel 2025. Per nuovi progetti, il team raccomanda di valutare Tailwind CSS o CSS Modules.

#### vanilla-extract

vanilla-extract offre la piu forte integrazione TypeScript nell'ecosistema di styling. Gli stili si scrivono in file `.css.ts` con type-safety completa e zero overhead a runtime:

```typescript
// card.css.ts
import { style, createTheme } from '@vanilla-extract/css';

export const [themeClass, vars] = createTheme({
  color: {
    brand: '#2563eb',
    surface: '#ffffff',
    text: '#1f2937'
  },
  space: {
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem'
  }
});

export const card = style({
  background: vars.color.surface,
  borderRadius: '0.5rem',
  padding: vars.space.lg,
  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12)',
  ':hover': {
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    transform: 'translateY(-2px)'
  }
});

export const title = style({
  fontSize: '1.25rem',
  fontWeight: 600,
  color: vars.color.text,
  marginBottom: vars.space.sm
});
```

### Tabella comparativa CSS-in-JS

| Soluzione | Runtime | SSR/RSC | Bundle (gzip) | TypeScript | Stile output |
|-----------|---------|---------|---------------|------------|-------------|
| styled-components | Si | Parziale | ~12kb | Buono | CSS dinamico |
| Emotion | Si | Parziale | ~8kb | Buono | CSS dinamico |
| Panda CSS | No | Completo | 0kb | Eccellente | Atomic CSS |
| vanilla-extract | No | Completo | 0kb | Eccellente | Scoped CSS |
| StyleX (Meta) | No | Completo | 0kb | Eccellente | Atomic CSS |

Per nuovi progetti nel 2025, le raccomandazioni sono:
- **Tailwind CSS o CSS Modules**: scelta predefinita per la maggior parte dei casi
- **Panda CSS**: per chi desidera l'ergonomia CSS-in-JS senza il runtime
- **vanilla-extract**: per chi vuole la massima type-safety
- **Emotion**: per progetti esistenti che lo utilizzano gia (migrazione non urgente)

---

## CSS Modules

CSS Modules e un approccio allo stile che genera automaticamente nomi di classe unici a tempo di compilazione, garantendo scope locale per default. Ogni file `.module.css` produce un mapping tra nomi originali e nomi trasformati, eliminando i conflitti globali senza runtime aggiuntivo.

### Come funzionano

```css
/* Card.module.css */
.container {
  background: white;
  border-radius: 0.5rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.description {
  color: #6b7280;
  line-height: 1.6;
}

/* Composizione — importa stili da un altro modulo */
.cardEvidenziata {
  composes: container;
  border-left: 4px solid #2563eb;
}
```

```tsx
// Card.tsx — i nomi delle classi sono importati come oggetto
import styles from './Card.module.css';

function Card({ titolo, descrizione, evidenziata }) {
  return (
    <div className={evidenziata ? styles.cardEvidenziata : styles.container}>
      <h2 className={styles.title}>{titolo}</h2>
      <p className={styles.description}>{descrizione}</p>
    </div>
  );
}
```

Il CSS generato in produzione avra nomi come `Card_container_x7f2a`, `Card_title_k9m3b`, garantendo unicita globale senza convenzioni manuali come BEM.

### Vantaggi e limiti

**Vantaggi**: scope locale automatico, zero runtime, compatibilita con qualsiasi framework CSS (Sass, PostCSS), supporto nativo in Vite, webpack, Next.js, e ottimo per team che preferiscono scrivere CSS standard.

**Limiti**: mancanza di theming dinamico nativo (richiede CSS custom properties), nessuna logica condizionale basata su props (richiede composizione manuale con `clsx`), meno adatto per design system complessi rispetto a Tailwind o CSS-in-JS.

---

## UnoCSS e CSS Atomico

UnoCSS, creato da Anthony Fu, e un motore CSS atomico on-demand. A differenza di Tailwind CSS (che e un framework con un set fisso di utilita), UnoCSS e un engine senza opinioni: non ha utilita predefinite e tutto e fornito tramite preset.

### Architettura a preset

```javascript
// uno.config.ts
import { defineConfig, presetUno, presetAttributify, presetIcons } from 'unocss';

export default defineConfig({
  presets: [
    presetUno(),          // Preset default (compatibile con Tailwind/Windi)
    presetAttributify(),  // Scrivere utility come attributi HTML
    presetIcons({         // Icone come classi CSS
      collections: {
        'lucide': () => import('@iconify-json/lucide/icons.json')
          .then(m => m.default)
      }
    })
  ],
  rules: [
    // Regole personalizzate con regex
    [/^m-(\d+)$/, ([, d]) => ({ margin: `${Number(d) * 0.25}rem` })],
    [/^glass$/, () => ({
      'backdrop-filter': 'blur(10px) saturate(180%)',
      'background': 'rgba(255, 255, 255, 0.7)',
      'border': '1px solid rgba(255, 255, 255, 0.18)'
    })]
  ],
  shortcuts: {
    'btn': 'py-2 px-4 rounded-md font-medium transition-colors',
    'btn-primary': 'btn bg-blue-600 text-white hover:bg-blue-700'
  }
});
```

### Attributify Mode — un approccio unico

La modalita Attributify permette di scrivere le utilita come attributi HTML invece che come classi, migliorando la leggibilita del markup:

```html
<!-- Approccio classico con classi -->
<div class="bg-white rounded-lg p-6 shadow-md text-gray-900 font-medium">
  Contenuto
</div>

<!-- Approccio Attributify di UnoCSS -->
<div
  bg="white"
  rounded="lg"
  p="6"
  shadow="md"
  text="gray-900"
  font="medium"
>
  Contenuto
</div>
```

### Pure CSS Icons

UnoCSS permette di utilizzare qualsiasi set di icone (Lucide, Phosphor, Material Symbols, etc.) come classi CSS, senza font icon o SVG inline:

```html
<!-- Icone come classi -->
<span class="i-lucide-search text-lg"></span>
<span class="i-lucide-settings text-gray-500 hover:text-blue-600"></span>
<span class="i-lucide-check-circle text-green-500 text-2xl"></span>
```

### Confronto UnoCSS vs Tailwind CSS

| Aspetto | UnoCSS | Tailwind CSS v4 |
|---------|--------|-----------------|
| Tipo | Engine senza opinioni | Framework opinionated |
| Performance dev | ~100x piu veloce (v3), gap ridotto con v4 | Molto veloce con Oxide |
| Personalizzazione | Totale (regex rules) | Alta (con @theme) |
| Preset system | Core feature | Plugin system |
| Attributify | Nativo | Non supportato |
| Pure CSS Icons | Nativo | Richiede plugin |
| Ecosistema | In crescita (~2M download/mese) | Dominante (~12M download/mese) |
| Documentazione | Buona | Eccellente |
| Caso d'uso | Progetti con esigenze non convenzionali | Scelta predefinita |

---

## CSS Moderno vs Framework

### Quando il CSS nativo e sufficiente

Le specifiche CSS si sono evolute enormemente negli ultimi anni. Molte funzionalita che un tempo richiedevano preprocessori o framework sono ora disponibili nativamente:

```css
/* CSS Custom Properties (variabili native) */
:root {
  --color-primary: #2563eb;
  --color-text: #1f2937;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --radius: 0.5rem;
}

/* CSS Nesting nativo (supportato nei browser moderni) */
.card {
  background: white;
  border-radius: var(--radius);

  & .titolo {
    color: var(--color-text);
  }

  &:hover {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  @media (width >= 768px) {
    display: grid;
    grid-template-columns: 1fr 2fr;
  }
}

/* Container Queries */
.card-container {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card {
    display: flex;
    gap: 1rem;
  }
}

/* :has() — il selettore genitore */
.form-group:has(input:invalid) {
  .etichetta {
    color: red;
  }
}

.card:has(img) {
  grid-template-rows: auto 1fr;
}

/* CSS Layers — gestione esplicita della specificita */
@layer reset, base, componenti, utilita;

@layer reset {
  * { margin: 0; padding: 0; box-sizing: border-box; }
}

@layer componenti {
  .btn { padding: 0.5rem 1rem; border-radius: 0.375rem; }
}

@layer utilita {
  .mt-1 { margin-top: 0.25rem; }
}

/* Nuove funzionalita di colore */
.elemento {
  background: oklch(70% 0.15 240);
  color: color-mix(in oklch, var(--color-primary), white 20%);
}

/* Subgrid */
.griglia-genitore {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.elemento-figlio {
  display: grid;
  grid-template-columns: subgrid;
  grid-column: span 3;
}
```

### Quando i framework aggiungono valore

Nonostante i progressi del CSS nativo, i framework rimangono preziosi in diversi scenari:

- **Progetti con team medio-grandi**: le convenzioni condivise riducono l'attrito e garantiscono coerenza
- **Prototipazione rapida**: utilita predefinite e componenti pronti accelerano lo sviluppo iniziale
- **Design system aziendali**: framework come Tailwind forniscono una base sistematica per token e scale
- **Compatibilita browser**: i preprocessori e PostCSS gestiscono automaticamente i prefix e i fallback
- **Progetti con scadenze strette**: componenti Bootstrap pronti riducono i tempi di consegna
- **Onboarding di nuovi sviluppatori**: le convenzioni del framework facilitano l'ingresso nel progetto

### Design Token e Strategie di Theming

I design token rappresentano il livello piu basso e atomico di un design system: sono i valori fondamentali (colori, spaziature, tipografia, ombre, raggi di bordo, durate di animazione) che definiscono l'identita visiva di un prodotto. Indipendentemente dal framework CSS scelto, i design token forniscono una singola fonte di verita condivisa tra design (Figma, Sketch) e codice.

#### Struttura dei token

I token si organizzano tipicamente su tre livelli di astrazione:

```css
/* LIVELLO 1 — Token globali (palette grezza) */
:root {
  --blue-50: oklch(97% 0.02 240);
  --blue-100: oklch(93% 0.04 240);
  --blue-500: oklch(55% 0.21 255);
  --blue-700: oklch(42% 0.18 255);
  --blue-900: oklch(28% 0.12 255);
  --red-500: oklch(55% 0.22 25);
  --gray-100: oklch(96% 0.005 265);
  --gray-900: oklch(18% 0.005 265);
}

/* LIVELLO 2 — Token semantici (scopo, non colore) */
:root {
  --color-primary: var(--blue-500);
  --color-primary-hover: var(--blue-700);
  --color-danger: var(--red-500);
  --color-background: var(--gray-100);
  --color-text: var(--gray-900);
  --color-text-muted: oklch(50% 0.01 265);
}

/* LIVELLO 3 — Token componente (specifici per componente) */
:root {
  --button-bg: var(--color-primary);
  --button-bg-hover: var(--color-primary-hover);
  --button-text: white;
  --button-radius: var(--radius-md);
  --button-padding-x: var(--space-4);
  --button-padding-y: var(--space-2);
}
```

Questo approccio a tre livelli permette di cambiare l'intera palette di un'applicazione modificando solo il livello 1, di cambiare il significato semantico dei colori al livello 2, e di personalizzare singoli componenti al livello 3.

#### Formati interoperabili

Per condividere token tra piattaforme diverse (web, iOS, Android, Figma), lo standard emergente e il formato W3C Design Tokens (precedentemente noto come Style Dictionary):

```json
{
  "color": {
    "primary": {
      "$value": "#2563eb",
      "$type": "color",
      "$description": "Colore principale del brand"
    },
    "surface": {
      "$value": "{color.neutral.50}",
      "$type": "color"
    }
  },
  "spacing": {
    "sm": { "$value": "0.5rem", "$type": "dimension" },
    "md": { "$value": "1rem", "$type": "dimension" },
    "lg": { "$value": "1.5rem", "$type": "dimension" }
  }
}
```

Strumenti come **Style Dictionary** (Amazon), **Tokens Studio** (plugin Figma) e **Cobalt** trasformano questa definizione nei formati specifici di ogni piattaforma (CSS custom properties, Tailwind config, Swift, Kotlin).

### Pattern di Design Responsive Avanzati

Oltre ai breakpoint classici basati sulla viewport, il CSS moderno introduce approcci piu sofisticati per il design responsive.

#### Container Queries — responsive al contenitore

Le container queries permettono ai componenti di adattarsi alla dimensione del loro contenitore, non della viewport. Questo rende i componenti veramente riutilizzabili in contesti di layout diversi:

```css
/* Definizione del contenitore */
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}

/* Layout che risponde alla dimensione del contenitore */
@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 1rem;
  }
}

@container card (min-width: 600px) {
  .card {
    grid-template-columns: 250px 1fr auto;
  }

  .card__actions {
    flex-direction: column;
  }
}
```

In Tailwind v4, le container queries sono supportate nativamente con il prefisso `@`:

```html
<div class="@container">
  <div class="flex flex-col @md:flex-row @lg:grid @lg:grid-cols-3">
    <!-- Layout adattivo al contenitore -->
  </div>
</div>
```

#### Fluid Typography e Spacing

Invece di definire breakpoint discreti per le dimensioni del testo, il fluid design utilizza `clamp()` per creare transizioni continue:

```css
:root {
  /* Tipografia fluida — scala automaticamente tra 320px e 1440px */
  --text-sm: clamp(0.8rem, 0.75rem + 0.25vw, 0.875rem);
  --text-base: clamp(1rem, 0.92rem + 0.4vw, 1.125rem);
  --text-lg: clamp(1.125rem, 1rem + 0.6vw, 1.25rem);
  --text-xl: clamp(1.25rem, 1rem + 1.2vw, 1.75rem);
  --text-2xl: clamp(1.5rem, 1rem + 2.5vw, 2.5rem);
  --text-hero: clamp(2.5rem, 1rem + 6vw, 5rem);

  /* Spaziatura fluida */
  --space-section: clamp(3rem, 2rem + 5vw, 8rem);
  --space-content: clamp(1rem, 0.5rem + 2vw, 2rem);
}

.hero h1 {
  font-size: var(--text-hero);
  margin-bottom: var(--space-content);
}
```

#### Layout moderni con CSS Grid e Subgrid

```css
/* Layout Bento — griglia asimmetrica con span variabili */
.griglia-bento {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: minmax(150px, auto);
  gap: 1rem;
}

.bento-item--grande {
  grid-column: span 2;
  grid-row: span 2;
}

.bento-item--largo {
  grid-column: span 2;
}

.bento-item--alto {
  grid-row: span 2;
}

/* Subgrid — figli allineati alla griglia del genitore */
.griglia-prodotti {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.card-prodotto {
  display: grid;
  grid-template-rows: subgrid;
  grid-row: span 4; /* immagine, titolo, descrizione, prezzo */
}
```

### Implementazione del Dark Mode

L'implementazione del dark mode richiede una strategia coerente che vada oltre il semplice inversione dei colori. Esistono due approcci principali: basato su media query (segue la preferenza di sistema) e basato su classe CSS (controllato dall'utente).

#### Strategia con CSS custom properties

```css
/* Definizione dei token per entrambi i temi */
:root {
  color-scheme: light;
  --color-bg: oklch(98% 0.005 265);
  --color-bg-elevated: oklch(100% 0 0);
  --color-text: oklch(18% 0.005 265);
  --color-text-muted: oklch(45% 0.01 265);
  --color-border: oklch(90% 0.005 265);
  --color-surface: oklch(100% 0 0);
  --color-primary: oklch(55% 0.22 255);
  --shadow-sm: 0 1px 3px oklch(0% 0 0 / 8%);
  --shadow-md: 0 4px 12px oklch(0% 0 0 / 10%);
}

/* Tema scuro — media query (preferenza di sistema) */
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --color-bg: oklch(15% 0.005 265);
    --color-bg-elevated: oklch(20% 0.005 265);
    --color-text: oklch(92% 0.005 265);
    --color-text-muted: oklch(65% 0.01 265);
    --color-border: oklch(28% 0.005 265);
    --color-surface: oklch(18% 0.005 265);
    --color-primary: oklch(65% 0.2 255);
    --shadow-sm: 0 1px 3px oklch(0% 0 0 / 25%);
    --shadow-md: 0 4px 12px oklch(0% 0 0 / 35%);
  }
}

/* Override con classe (controllato dall'utente) */
[data-theme="dark"] {
  color-scheme: dark;
  --color-bg: oklch(15% 0.005 265);
  --color-bg-elevated: oklch(20% 0.005 265);
  /* ... stessi override ... */
}
```

#### Toggle con persistenza

```javascript
// dark-mode.js — toggle con persistenza in localStorage
function initDarkMode() {
  const savedTheme = localStorage.getItem('theme');
  const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = savedTheme || (systemPreference ? 'dark' : 'light');

  document.documentElement.setAttribute('data-theme', theme);

  // Reagire ai cambiamenti della preferenza di sistema
  window.matchMedia('(prefers-color-scheme: dark)')
    .addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        document.documentElement.setAttribute(
          'data-theme', e.matches ? 'dark' : 'light'
        );
      }
    });
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}
```

In Tailwind CSS, il dark mode si configura con la strategia `selector` (precedentemente `class`):

```css
/* Tailwind v4 dark mode con @variant */
@import 'tailwindcss';

@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));
```

```html
<div class="bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
  <p class="text-gray-600 dark:text-gray-400">Contenuto adattivo</p>
</div>
```

### Librerie di Animazione per il Web

Le animazioni web moderne si dividono tra soluzioni CSS pure, librerie JavaScript leggere e motori di animazione completi. La scelta dipende dalla complessita delle animazioni richieste e dal framework JavaScript utilizzato.

#### Motion (ex Framer Motion)

Motion (precedentemente Framer Motion) e la libreria di animazione piu diffusa nell'ecosistema React, con oltre 16 milioni di download mensili. Offre un'API dichiarativa che si integra naturalmente con il modello a componenti di React:

```tsx
import { motion, AnimatePresence } from 'motion/react';

// Animazione dichiarativa con varianti
const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2 } }
};

function AnimatedCard({ children, isVisible }) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          variants={cardVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          whileHover={{ scale: 1.02, boxShadow: '0 8px 30px rgba(0,0,0,0.12)' }}
          className="rounded-lg bg-white p-6 shadow-md"
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Layout animations — animazione automatica dei cambiamenti di layout
function ListaAnimata({ items }) {
  return (
    <motion.ul layout>
      {items.map(item => (
        <motion.li
          key={item.id}
          layout
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {item.name}
        </motion.li>
      ))}
    </motion.ul>
  );
}
```

Motion supporta anche animazioni scroll-driven, gesture, spring physics e path morphing. Il bundle e circa 32kb gzipped, ma il tree-shaking riduce significativamente il peso per i casi d'uso tipici.

#### GSAP (GreenSock Animation Platform)

GSAP e il motore di animazione piu potente e versatile per il web, con oltre 15 anni di maturita. Non e legato a nessun framework JavaScript ed eccelle in animazioni complesse, timeline sequenziate e effetti scroll-driven:

```javascript
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

// Timeline — sequenza di animazioni orchestrate
const tl = gsap.timeline({ defaults: { ease: 'power3.out', duration: 0.6 } });

tl.from('.hero-titolo', { y: 50, opacity: 0 })
  .from('.hero-descrizione', { y: 30, opacity: 0 }, '-=0.3')
  .from('.hero-cta', { y: 20, opacity: 0 }, '-=0.2')
  .from('.hero-immagine', { scale: 0.9, opacity: 0 }, '-=0.4');

// ScrollTrigger — animazione guidata dallo scroll
gsap.from('.feature-card', {
  scrollTrigger: {
    trigger: '.sezione-feature',
    start: 'top 80%',
    end: 'top 20%',
    toggleActions: 'play none none reverse'
  },
  y: 60,
  opacity: 0,
  stagger: 0.15,
  duration: 0.8,
  ease: 'power2.out'
});

// Parallax con ScrollTrigger
gsap.to('.sfondo-parallax', {
  scrollTrigger: {
    trigger: '.sezione-parallax',
    start: 'top bottom',
    end: 'bottom top',
    scrub: true
  },
  y: -100,
  ease: 'none'
});
```

GSAP offre benchmark superiori per animazioni complesse (fino a 20x piu veloce delle CSS transitions in scenari con 50+ elementi simultanei), con un core di circa 23kb gzipped.

#### CSS Animations e Spring Physics

Per animazioni semplici, il CSS nativo rimane la scelta piu performante. Le CSS animations utilizzano il compositor del browser, evitando completamente il thread principale:

```css
/* Spring-like easing con cubic-bezier */
:root {
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out-circ: cubic-bezier(0.85, 0, 0.15, 1);
}

.card {
  transition: transform 0.3s var(--ease-spring),
              box-shadow 0.3s var(--ease-out-expo);
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

/* Animazione con @keyframes e prefers-reduced-motion */
@keyframes reveal {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animazione-reveal {
  animation: reveal 0.5s var(--ease-out-expo) both;
}

/* Rispetto delle preferenze utente */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

#### Quando usare quale strumento

| Scenario | Raccomandazione |
|----------|-----------------|
| Hover, focus, transizioni semplici | CSS nativo |
| Animazioni di entrata/uscita in React | Motion |
| Timeline complesse, scroll-driven | GSAP |
| Animazioni di layout in React | Motion (layout animations) |
| Siti non-React con animazioni ricche | GSAP |
| Micro-interazioni e feedback | CSS nativo o Motion |
| Parallax e scroll narrative | GSAP ScrollTrigger |

### Architettura di Component Library

Costruire una component library richiede decisioni architetturali che influenzano la manutenibilita, la riutilizzabilita e l'adozione nel lungo periodo.

#### Principi fondamentali

1. **Composizione sopra configurazione**: preferire componenti componibili (slot, render props, compound components) rispetto a mega-componenti con decine di props
2. **Separazione della logica dalla presentazione**: usare librerie headless (Radix, Ark UI) per la logica e applicare lo stile come layer separato
3. **Token come contratto**: i design token definiscono il contratto tra la component library e i progetti che la consumano
4. **Versioning semantico rigoroso**: qualsiasi cambiamento visivo e una breaking change se non e opt-in

```
architettura-component-library/
├── tokens/
│   ├── colors.json            # Token colore (formato W3C)
│   ├── spacing.json           # Scale di spaziatura
│   └── typography.json        # Scale tipografiche
├── primitives/                # Componenti headless
│   ├── Dialog/
│   ├── Dropdown/
│   └── Tooltip/
├── components/                # Componenti stilizzati
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.module.css  # o variante Tailwind
│   │   ├── Button.test.tsx
│   │   └── Button.stories.tsx
│   ├── Card/
│   └── Form/
├── themes/
│   ├── default.css
│   └── dark.css
└── index.ts                   # Entry point con export nominati
```

#### Storybook come documentazione vivente

Storybook e lo standard de facto per la documentazione di component library. Ogni componente ha le sue "stories" che documentano tutte le varianti, gli stati e i casi d'uso:

```tsx
// Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  component: Button,
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'ghost'] },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
    disabled: { control: 'boolean' }
  }
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: { variant: 'primary', children: 'Pulsante primario' }
};

export const Secondary: Story = {
  args: { variant: 'secondary', children: 'Pulsante secondario' }
};

export const Disabled: Story = {
  args: { variant: 'primary', disabled: true, children: 'Disabilitato' }
};
```

### Accessibilita nei CSS Framework

L'accessibilita non e un optional: e un requisito legale in molte giurisdizioni (EAA in Europa, ADA negli USA, AODA in Canada) e un imperativo etico. I CSS framework possono sia facilitare che ostacolare l'accessibilita.

#### Focus management e visibilita

Ogni elemento interattivo deve avere un focus ring visibile e ad alto contrasto. Molti framework nascondono il focus ring per estetica, creando barriere per utenti che navigano da tastiera:

```css
/* Focus ring accessibile — approccio moderno */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Rimuovere l'outline solo per interazioni mouse */
:focus:not(:focus-visible) {
  outline: none;
}

/* Focus ring con ring-offset per Tailwind */
.btn:focus-visible {
  @apply outline-none ring-2 ring-blue-500 ring-offset-2;
}
```

#### Contrasto e leggibilita

I token di colore devono garantire i rapporti di contrasto minimi WCAG:

- **AA**: 4.5:1 per testo normale, 3:1 per testo grande (18px+ o 14px+ bold)
- **AAA**: 7:1 per testo normale, 4.5:1 per testo grande

```css
/* Colori che rispettano WCAG AA */
:root {
  --text-on-light: oklch(25% 0 0);     /* Contrasto ~12:1 su bianco */
  --text-muted-on-light: oklch(42% 0 0); /* Contrasto ~5.5:1 su bianco */
  --text-on-dark: oklch(92% 0 0);       /* Contrasto ~13:1 su nero */
  --text-on-primary: oklch(98% 0 0);    /* Verificare con il colore primary */
}
```

#### Riduzione del movimento

Rispettare la preferenza `prefers-reduced-motion` e critico per utenti con disturbi vestibolari o fotosensibili:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

In Tailwind, il modificatore `motion-reduce:` e `motion-safe:` permettono di gestire questo caso direttamente nel markup:

```html
<div class="motion-safe:animate-fade-in motion-reduce:opacity-100">
  Contenuto con animazione condizionale
</div>
```

#### Screen reader utilities

```css
/* Visivamente nascosto ma accessibile agli screen reader */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Rendere visibile al focus (skip links) */
.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: 0.5rem 1rem;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

### Confronto di Performance degli Approcci CSS

La scelta dell'approccio CSS ha un impatto diretto sulle metriche di performance web (Core Web Vitals). Ecco un confronto basato su dati e benchmark reali.

#### Dimensione del bundle CSS

| Approccio | Bundle tipico (gzip) | Note |
|-----------|---------------------|------|
| Tailwind CSS v4 | 6-12 kb | Solo utilita effettivamente usate |
| Bootstrap 5 (completo) | 25-30 kb | Include tutti i componenti |
| Bootstrap 5 (selettivo) | 12-18 kb | Import selettivo dei moduli |
| CSS Modules | Variabile | Dipende dal CSS scritto |
| styled-components | 12 kb + CSS generato | Runtime incluso |
| vanilla-extract | 0 kb runtime + CSS | Zero overhead runtime |
| CSS nativo | Variabile | Nessun overhead framework |

#### Impatto su Largest Contentful Paint (LCP)

Il CSS e una risorsa render-blocking: il browser non puo renderizzare la pagina finche non ha scaricato e parsato tutto il CSS linkato. Strategie di mitigazione:

1. **Inline critical CSS**: inserire il CSS necessario per il contenuto above-the-fold direttamente nel `<head>`
2. **Async non-critical CSS**: caricare il CSS non critico in modo asincrono
3. **Code splitting CSS**: con CSS Modules o CSS-in-JS, il CSS viene diviso per route
4. **Compressione**: Brotli offre 15-20% di riduzione in piu rispetto a gzip per il CSS

#### Impatto su Cumulative Layout Shift (CLS)

Framework e approcci che iniettano CSS a runtime (styled-components, Emotion) possono causare flash of unstyled content (FOUC) se il Server-Side Rendering (SSR) non e configurato correttamente. Le soluzioni zero-runtime (Tailwind, CSS Modules, vanilla-extract) non hanno questo problema perche il CSS e statico e disponibile al primo render.

#### Runtime performance

Le animazioni e le transizioni CSS sono gestite dal compositor del browser su un thread separato, evitando di bloccare il thread principale. Le soluzioni CSS-in-JS runtime possono introdurre overhead durante il re-render dei componenti, particolarmente visibile in liste con molti elementi.

### Strategie di Migrazione tra Framework

La migrazione tra framework CSS e un'operazione complessa che va pianificata attentamente. Ecco le strategie per le migrazioni piu comuni.

#### Da Bootstrap a Tailwind CSS

Questa e la migrazione piu richiesta. L'approccio consigliato e incrementale:

1. **Fase 1 — Coesistenza**: installare Tailwind accanto a Bootstrap. Configurare Tailwind con un prefix per evitare conflitti:

```css
/* Tailwind v4 con prefix per coesistenza */
@import 'tailwindcss' prefix(tw);

/* Le classi Tailwind diventano: tw-bg-blue-500, tw-p-4, tw-flex */
```

2. **Fase 2 — Migrazione incrementale**: convertire un componente alla volta, partendo dai piu semplici. Per ogni componente:
   - Riscrivere il markup con classi Tailwind
   - Verificare visivamente la parita
   - Rimuovere le classi Bootstrap dal componente

3. **Fase 3 — Rimozione**: quando tutti i componenti sono migrati, rimuovere Bootstrap come dipendenza

#### Da CSS-in-JS a Tailwind CSS

Per progetti che utilizzano styled-components o Emotion:

1. Installare Tailwind e configurarlo
2. Creare un mapping dei token esistenti nel tema CSS-in-JS verso i token Tailwind
3. Convertire i componenti styled in componenti con classi Tailwind, uno alla volta
4. Usare `cn()` (clsx + tailwind-merge) per la composizione condizionale
5. Rimuovere il provider del tema CSS-in-JS quando non ha piu consumatori

#### Da Sass/BEM a Tailwind CSS

La migrazione da Sass con convenzioni BEM e spesso la piu graduale:

1. Mappare le variabili Sass sui token `@theme` di Tailwind
2. Convertire i mixin Sass piu usati in classi utility o plugin Tailwind
3. Riscrivere i componenti BEM in markup con classi utility
4. Mantenere BEM per i componenti piu complessi durante la transizione

#### Strumenti di supporto

- **`npx @tailwindcss/upgrade`**: tool ufficiale per la migrazione da Tailwind v3 a v4
- **Windy**: estensione VS Code che suggerisce equivalenti Tailwind per CSS custom
- **CSS-to-Tailwind converters**: strumenti online che convertono blocchi CSS in classi Tailwind (utili come punto di partenza, richiedono revisione manuale)
- **Tailwind CSS IntelliSense**: estensione VS Code ufficiale che fornisce autocompletamento, preview dei colori e diagnostica per le classi Tailwind — essenziale durante la migrazione per esplorare le classi disponibili

#### Rischi e mitigazioni nella migrazione

La migrazione tra framework CSS presenta rischi specifici che vanno considerati nella pianificazione:

- **Regressioni visive**: ogni componente migrato deve essere verificato visualmente a tutti i breakpoint. Utilizzare test di visual regression (Playwright screenshot, Chromatic) per automatizzare il confronto prima/dopo
- **Specificita inaspettata**: durante la coesistenza di due framework, le regole CSS possono interagire in modi imprevisti. CSS Layers (`@layer`) possono aiutare a gestire la specificita in modo esplicito
- **Perdita di funzionalita**: framework component-based (Bootstrap) includono JavaScript per dropdown, modal, tooltip. Nella migrazione a Tailwind, queste funzionalita devono essere reimplementate con librerie headless (Radix, Headless UI) o componenti JavaScript personalizzati
- **Formazione del team**: il passaggio da un approccio component-based a uno utility-first richiede un cambio di mentalita. Prevedere tempo per la formazione e la definizione di convenzioni condivise
- **Stima dei tempi**: una migrazione completa su un progetto di media complessita richiede tipicamente 2-4 settimane di lavoro, non ore. L'approccio incrementale permette di distribuire lo sforzo nel tempo senza bloccare lo sviluppo di nuove funzionalita

### Approcci ibridi

In pratica, molti progetti adottano approcci combinati:

```css
/* Approccio ibrido: CSS moderno + PostCSS + struttura metodologica */

/* CSS custom properties per i token */
:root {
  --color-primary: oklch(55% 0.25 265);
  --color-surface: oklch(98% 0.005 265);
  --space-unit: 0.25rem;
  --radius-md: 0.5rem;
}

/* Nesting nativo per i componenti (con BEM per il naming) */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: calc(var(--space-unit) * 6);

  &__header {
    border-bottom: 1px solid oklch(90% 0.01 265);
  }

  &__body {
    padding-top: calc(var(--space-unit) * 4);
  }

  &--evidenziata {
    border: 2px solid var(--color-primary);
  }
}
```

### Framework decisionale per la scelta

La scelta tra CSS nativo, preprocessore o framework dipende dal contesto specifico del progetto. Ecco un framework decisionale strutturato:

**Scegliere CSS nativo quando**:
- Il progetto e piccolo o medio con poche pagine
- Il team ha esperienza CSS solida
- Si vuole minimizzare le dipendenze esterne
- I browser target supportano le funzionalita moderne necessarie
- Il progetto ha requisiti di performance stringenti

**Scegliere Sass/PostCSS quando**:
- Serve un sistema di design token e variabili complesso
- Il progetto richiede calcoli e logica nella generazione degli stili
- Si vuole mantenere liberta totale nel design senza vincoli di framework
- Il team ha una metodologia CSS consolidata (BEM, ITCSS)

**Scegliere Tailwind CSS quando**:
- La velocita di sviluppo e prioritaria
- Si lavora con framework a componenti (React, Vue, Svelte)
- Si vuole un design system coerente e flessibile
- Il team apprezza l'approccio utility-first
- Si sviluppano interfacce personalizzate (non basate su componenti predefiniti)

**Scegliere Bootstrap quando**:
- Servono componenti pronti all'uso rapidamente
- Il progetto e un'applicazione interna, un pannello admin o un prototipo
- Il team ha esperienza limitata con CSS
- L'aspetto visivo standard di Bootstrap e accettabile
- Si deve garantire coerenza con il minimo sforzo

---

## Best Practices

### 1. Adottare una metodologia e mantenerla con coerenza

Qualunque metodologia si scelga (BEM, ITCSS, Cube CSS o un approccio personalizzato), la coerenza e piu importante della scelta stessa. Definire convenzioni chiare in un documento condiviso con il team e assicurarsi che ogni membro le rispetti. Un progetto con uno stile organizzativo misto e peggiore di uno che segue coerentemente un approccio imperfetto.

### 2. Evitare il nesting eccessivo

Sia con Sass che con il nesting CSS nativo, limitare la profondita a massimo 3-4 livelli. Un nesting profondo genera selettori troppo specifici, difficili da sovrascrivere e da debuggare. Se ci si trova a nidificare piu di tre livelli, e probabilmente il momento di estrarre un nuovo componente.

```scss
// ERRATO — troppo profondo
.pagina {
  .sezione {
    .contenitore {
      .card {
        .card-body {
          .titolo { /* Specificità troppo alta */ }
        }
      }
    }
  }
}

// CORRETTO — piatto e specifico
.card__titolo {
  font-size: 1.25rem;
  color: var(--color-text);
}
```

### 3. Utilizzare design token come singola fonte di verita

Centralizzare i valori di design (colori, spaziature, tipografia, ombre, raggi di bordo) in un unico punto di definizione, che siano variabili Sass, CSS custom properties o la configurazione del tema Tailwind. Ogni componente deve fare riferimento a questi token, mai a valori hardcoded.

### 4. Ottimizzare il bundle CSS per la produzione

Rimuovere il CSS inutilizzato tramite PurgeCSS (integrato in Tailwind), tree-shaking dei moduli (import selettivi di Bootstrap) o strumenti di analisi. Minificare con cssnano. Comprimere con gzip o brotli. Un CSS piu piccolo migliora i tempi di caricamento e le metriche Core Web Vitals.

### 5. Preferire la composizione all'ereditarieta

Invece di creare gerarchie profonde di stili ereditati con `@extend`, favorire la composizione di classi indipendenti. Questo approccio e piu prevedibile, piu facile da debuggare e meno soggetto a effetti collaterali inattesi.

### 6. Scrivere CSS mobile-first

Iniziare sempre dagli stili per schermi piccoli e aggiungere complessita con media query progressive (`min-width`). Questo garantisce che l'esperienza base sia sempre funzionante e che gli stili desktop siano un miglioramento incrementale, non un requisito.

```css
/* Mobile first */
.griglia {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

@media (min-width: 768px) {
  .griglia {
    flex-direction: row;
    flex-wrap: wrap;
  }
}

@media (min-width: 1024px) {
  .griglia {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
  }
}
```

### 7. Documentare le decisioni architetturali

Commentare il "perche" delle scelte non ovvie, non il "cosa". Spiegare hack, workaround per bug dei browser, e decisioni di design che potrebbero confondere chi legge il codice in futuro. Mantenere una guida di stile aggiornata con esempi dei componenti e delle loro varianti.

### 8. Testare su dispositivi e browser reali

Non affidarsi solo alle DevTools del browser. Testare su dispositivi fisici con diverse dimensioni di schermo, densita di pixel e sistemi operativi. Utilizzare servizi come BrowserStack o LambdaTest per la compatibilita cross-browser. Verificare che le animazioni e le transizioni siano fluide anche su hardware meno potente.

### 9. Gestire la specificita in modo intenzionale

Evitare l'uso di `!important` (eccetto che nei layer di utilita dove e intenzionale). Non usare selettori ID per gli stili. Mantenere la specificita bassa e uniforme utilizzando classi singole. Se si ha bisogno di specificita maggiore, utilizzare CSS Layers (`@layer`) per gestirla in modo esplicito e controllato.

### 10. Mantenersi aggiornati e rivalutare periodicamente le scelte

L'ecosistema CSS evolve rapidamente. Funzionalita che ieri richiedevano un framework domani potrebbero essere native. Rivalutare periodicamente le dipendenze del progetto: se un preprocessore viene usato solo per le variabili, forse le CSS custom properties sono ora sufficienti. Se Bootstrap viene usato solo per la griglia, forse CSS Grid nativo e la scelta migliore. L'obiettivo e sempre ridurre la complessita mantenendo la funzionalita necessaria.

---

> **Nota**: Questa guida copre le versioni piu recenti degli strumenti trattati al momento della stesura (Sass/Dart Sass, PostCSS 8, Tailwind CSS v3/v4, Bootstrap 5.3). Consultare sempre la documentazione ufficiale per gli aggiornamenti piu recenti e le eventuali breaking change.

---

## Esercizi

### Esercizio 1 — Setup Tailwind CSS con design token personalizzati

**Obiettivo:** Configurare un progetto Tailwind CSS da zero con un sistema di design token coerente.

- Inizializzare un progetto con Vite e installare Tailwind CSS (v4.x) tramite PostCSS
- Configurare `tailwind.config.js` con una palette colori personalizzata (primary, secondary, accent, neutral) con almeno 5 livelli ciascuna (50-900)
- Definire scale tipografiche personalizzate (`fontFamily`, `fontSize` con line-height) e scale di spaziatura coerenti
- Creare una landing page con hero, feature grid (3 colonne), pricing cards e footer usando esclusivamente classi utility di Tailwind
- Implementare il responsive design con i breakpoint di Tailwind (`sm`, `md`, `lg`, `xl`) usando l'approccio mobile-first
- Implementare dark mode con la strategia `class` e un toggle funzionante
- Verificare la dimensione del CSS generato in produzione (deve essere < 15kb gzip con il purge attivo)

### Esercizio 2 — Componente riutilizzabile con Sass/SCSS

**Obiettivo:** Costruire un sistema di componenti modulare usando le funzionalita avanzate di Sass.

- Configurare Dart Sass in un progetto con struttura 7-1 semplificata: `abstracts/` (variabili, mixin, funzioni), `base/` (reset, tipografia), `components/`, `layout/`
- Creare un mixin per breakpoint responsive (`@mixin respond-to($breakpoint)`) con una mappa di breakpoint
- Implementare un sistema di bottoni con mixin parametrici: varianti (primary, secondary, outline, ghost), dimensioni (sm, md, lg), stati (hover, focus, disabled)
- Creare un mixin per la generazione automatica di classi utility di spaziatura (`m-1`, `p-2`, ecc.) usando `@each` e mappe Sass
- Utilizzare `@use` e `@forward` (non `@import` deprecato) per l'organizzazione dei moduli
- Il CSS compilato deve essere privo di selettori duplicati e nesting inutile (verificare con `sass --style=expanded`)

### Esercizio 3 — Pipeline PostCSS con plugin moderni

**Obiettivo:** Configurare una pipeline PostCSS che abiliti funzionalita CSS moderne con compatibilita browser.

- Inizializzare un progetto con PostCSS e configurare `postcss.config.js`
- Installare e configurare i plugin: `postcss-preset-env` (stage 2+), `autoprefixer`, `cssnano` (solo produzione), `postcss-import`
- Scrivere CSS usando funzionalita moderne: nesting nativo, `@custom-media`, color functions (`oklch()`, `color-mix()`), range media queries (`@media (width >= 768px)`)
- Configurare il `browserslist` target nel `package.json` per gli ultimi 2 versioni dei browser principali
- Creare una pagina dimostrativa con i componenti stilizzati usando queste funzionalita
- Confrontare il CSS sorgente con il CSS compilato per verificare che le trasformazioni siano corrette
- Misurare la riduzione di dimensione tra CSS sviluppo e CSS produzione (con cssnano)

### Esercizio 4 — Prototipo rapido con Bootstrap e personalizzazione Sass

**Obiettivo:** Costruire un prototipo funzionale con Bootstrap personalizzato, importando solo i moduli necessari.

- Installare Bootstrap 5.x via npm e configurare la compilazione Sass
- Sovrascrivere le variabili Bootstrap prima dell'importazione: `$primary`, `$font-family-base`, `$border-radius`, `$spacer`, `$grid-breakpoints`
- Importare selettivamente solo i moduli necessari (grid, utilities, navbar, cards, modal) anziche l'intero framework
- Costruire una pagina dashboard con: navbar responsive con dropdown, sidebar collassabile, griglia di card con badge e progress bar, modal per dettagli
- Estendere il sistema di utility Bootstrap aggiungendo utility personalizzate tramite la mappa `$utilities`
- Confrontare la dimensione del CSS risultante con un'importazione completa di Bootstrap e documentare la riduzione

### Esercizio 5 — Confronto framework e migrazione

**Obiettivo:** Implementare lo stesso componente con tre approcci diversi e analizzare i trade-off.

- Progettare un componente card complesso: immagine, badge di stato, titolo, descrizione, avatar autore, data, tag, bottoni azione, stati hover/focus
- Implementare la card tre volte: (1) CSS puro con custom properties e BEM, (2) Tailwind CSS con classi utility, (3) Bootstrap con classi del framework + override Sass
- Per ciascuna implementazione misurare: righe di CSS/HTML, dimensione CSS finale, tempo di sviluppo, leggibilita del markup
- Creare una tabella comparativa con i risultati
- Scrivere la versione Tailwind anche come componente con `@apply` per confrontare utility inline vs classi estratte
- Identificare in quali scenari progettuali ciascun approccio risulta piu vantaggioso (prototipo rapido, design system, progetto legacy, team grande)

---

## Letture e Riferimenti

### Documentazione ufficiale

- **Tailwind CSS Documentation** — Guida completa all'utility-first framework con esempi interattivi. <https://tailwindcss.com/docs> (consultato: 2026-05-24)
- **Bootstrap Documentation (v5.3)** — Documentazione ufficiale del framework con componenti, utility e personalizzazione. <https://getbootstrap.com/docs/5.3/> (consultato: 2026-05-24)
- **Sass Documentation** — Riferimento ufficiale per Dart Sass: variabili, mixin, moduli, funzioni. <https://sass-lang.com/documentation/> (consultato: 2026-05-24)
- **PostCSS** — Documentazione del tool per la trasformazione del CSS tramite plugin. <https://postcss.org/> (consultato: 2026-05-24)
- **postcss-preset-env** — Plugin per scrivere CSS moderno con polyfill automatici. <https://preset-env.cssdb.org/> (consultato: 2026-05-24)
- **MDN Web Docs — CSS** — Riferimento autorevole per verificare il supporto browser delle funzionalita CSS. <https://developer.mozilla.org/en-US/docs/Web/CSS> (consultato: 2026-05-24)
- **Can I Use** — Database di compatibilita browser per funzionalita CSS e web. <https://caniuse.com/> (consultato: 2026-05-24)

### Libri e approfondimenti

- Rappin N., *Modern CSS with Tailwind* (2nd ed.), Pragmatic Bookshelf, 2023.
- Verou L., *CSS Secrets: Better Solutions to Everyday Web Design Problems*, O'Reilly, 2015.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [02 — CSS3](02-css3.md) | I framework astraggono le proprieta CSS fondamentali trattate nel modulo precedente |
| [01 — HTML5](01-html5.md) | Le classi dei framework si applicano agli elementi HTML semantici del modulo 01 |
| [07 — React](07-react.md) | Tailwind e CSS Modules sono gli approcci di styling piu diffusi nei progetti React |
| [08 — Vue](08-vue.md) | Vue supporta Tailwind, Sass scoped e CSS Modules per lo styling dei componenti |
| [09 — Svelte](09-svelte.md) | Svelte ha CSS scoped nativo e integra Tailwind e PostCSS nella pipeline di build |
| [16 — Build Tools e Deploy](16-build-tools-e-deploy.md) | I bundler (Vite, webpack) gestiscono la compilazione Sass, PostCSS e il purging di Tailwind |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Utility-first** | Approccio CSS che compone gli stili tramite piccole classi a singola responsabilita (es. `text-lg`, `flex`, `p-4`) direttamente nel markup. |
| **Preprocessore CSS** | Strumento (Sass, Less, Stylus) che estende la sintassi CSS con variabili, nesting, mixin e funzioni, compilando in CSS standard. |
| **PostCSS** | Strumento che trasforma il CSS tramite plugin JavaScript, usato per autoprefixing, polyfill e minificazione. |
| **Mixin** | Blocco di stili riutilizzabile in Sass che puo accettare parametri e generare CSS diverso in base agli argomenti. |
| **Design token** | Valore atomico di design (colore, spaziatura, tipografia) definito come variabile e condiviso tra codice e strumenti di design. |
| **Tree shaking (CSS)** | Processo di eliminazione automatica delle classi CSS non utilizzate nel codice sorgente per ridurre la dimensione del bundle. |
| **`@use` / `@forward`** | Direttive Sass moderne che sostituiscono `@import`, offrendo namespace, incapsulamento e caricamento singolo dei moduli. |
| **Autoprefixer** | Plugin PostCSS che aggiunge automaticamente i prefissi vendor (`-webkit-`, `-moz-`) in base al target browser. |
| **JIT (Just-in-Time)** | Modalita di compilazione di Tailwind che genera solo le classi effettivamente usate nel codice, on-demand. |
| **BEM** | Block-Element-Modifier: convenzione di nomenclatura che struttura le classi come `.block__element--modifier` per evitare conflitti. |
| **`@apply`** | Direttiva Tailwind che permette di estrarre classi utility in selettori CSS tradizionali per ridurre la ripetizione nel markup. |
| **Breakpoint** | Soglia di larghezza viewport (o contenitore) alla quale il layout cambia configurazione, definita nelle media o container query. |
| **Purge** | Processo di scansione del codice sorgente per identificare e rimuovere le classi CSS non utilizzate dal bundle finale. |
| **Headless UI** | Libreria di componenti che fornisce logica, accessibilita e gestione dello stato senza alcuno stile visivo predefinito. |
| **Radix UI** | Libreria headless per React che fornisce primitive UI accessibili con supporto completo ARIA, gestione del focus e navigazione da tastiera. |
| **shadcn/ui** | Sistema di componenti copiabili basato su Radix UI e Tailwind CSS, dove il codice diventa proprieta del progetto anziche dipendenza npm. |
| **CSS-in-JS** | Approccio che permette di definire stili CSS direttamente nel codice JavaScript, co-locando stili e logica del componente. |
| **Zero-runtime CSS** | Soluzioni di styling (vanilla-extract, Panda CSS, StyleX) che estraggono il CSS a tempo di compilazione senza aggiungere runtime JavaScript nel browser. |
| **CSS Modules** | Approccio che genera automaticamente nomi di classe unici a tempo di compilazione, garantendo scope locale per ogni file CSS. |
| **UnoCSS** | Engine CSS atomico on-demand creato da Anthony Fu, senza utilita predefinite, dove tutto e fornito tramite preset componibili. |
| **Oxide Engine** | Motore di compilazione di Tailwind CSS v4, riscritto in Rust, che integra Lightning CSS per performance fino a 10x superiori alla v3. |
| **Lightning CSS** | Compilatore CSS scritto in Rust (da Devon Govett) usato internamente da Tailwind v4 per parsing, prefixing e minificazione. |
| **`@theme`** | Direttiva CSS di Tailwind v4 che sostituisce `tailwind.config.js`, permettendo di definire design token direttamente nel CSS. |
| **Container Query** | Regola CSS che permette ai componenti di adattarsi alla dimensione del contenitore anziche della viewport. |
| **Motion** | Libreria di animazione per React (successore di Framer Motion), con API dichiarativa, layout animations e spring physics. |
| **GSAP** | GreenSock Animation Platform — motore di animazione JavaScript maturo, performante e framework-agnostico per animazioni web complesse. |
| **Fluid Typography** | Tecnica che utilizza `clamp()` per creare dimensioni di testo che scalano in modo continuo tra un minimo e un massimo in base alla viewport. |
| **Design Token (livelli)** | Sistema a tre livelli di astrazione: token globali (palette grezza), token semantici (scopo), token componente (specifici per widget). |
