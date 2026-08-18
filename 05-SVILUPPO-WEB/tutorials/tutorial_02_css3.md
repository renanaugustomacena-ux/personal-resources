# Tutorial 02 — CSS Moderno: Dal Principiante all'Esperto

> **Companion a:** `02-css3.md`
> **Scope:** Selettori e specificità, cascata e `@layer`, box model, Flexbox, Grid, Container Queries, media query e responsive design, custom properties e design token, temi e modalità scura, transizioni e animazioni, tipografia fluida, colori moderni, proprietà logiche, `:has()`, `@scope`, `@property`, scroll-driven animations, View Transitions
> **Prerequisiti:** `tutorial_01_html5.md` — struttura semantica, landmark, form; un documento HTML valido da stilare
> **Durata stimata:** 22-28 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** CSS Living Standard · browser evergreen (Chrome, Firefox, Safari, Edge)

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Cosa fa il CSS e come arriva alla pagina](#a1-cosa-fa-il-css-e-come-arriva-alla-pagina)
  - [A2. Selettori: come si indica un elemento](#a2-selettori-come-si-indica-un-elemento)
  - [A3. La cascata e l'ereditarietà](#a3-la-cascata-e-lereditarietà)
  - [A4. La specificità, calcolata a mano](#a4-la-specificità-calcolata-a-mano)
  - [A5. Il box model](#a5-il-box-model)
  - [A6. Le unità di misura](#a6-le-unità-di-misura)
  - [A7. `display`: il comportamento di base di ogni elemento](#a7-display-il-comportamento-di-base-di-ogni-elemento)
  - [A8. Flexbox: allineare lungo un asse](#a8-flexbox-allineare-lungo-un-asse)
  - [A9. Grid: righe e colonne insieme](#a9-grid-righe-e-colonne-insieme)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. Il flusso normale, il margin collapsing e i contesti di formattazione](#b1-il-flusso-normale-il-margin-collapsing-e-i-contesti-di-formattazione)
  - [B2. `position` e il contesto di impilamento](#b2-position-e-il-contesto-di-impilamento)
  - [B3. Flexbox in profondità: `flex-basis`, `min-width: auto`, `gap`](#b3-flexbox-in-profondità-flex-basis-min-width-auto-gap)
  - [B4. Grid in profondità: aree nominate, `minmax`, `auto-fit`, subgrid](#b4-grid-in-profondità-aree-nominate-minmax-auto-fit-subgrid)
  - [B5. Custom properties e design token](#b5-custom-properties-e-design-token)
  - [B6. Responsive: media query, unità del viewport, `clamp()`](#b6-responsive-media-query-unità-del-viewport-clamp)
  - [B7. Container queries: rispondere al contenitore, non alla finestra](#b7-container-queries-rispondere-al-contenitore-non-alla-finestra)
  - [B8. Cascade layers e `@scope`](#b8-cascade-layers-e-scope)
  - [B9. Il selettore `:has()`](#b9-il-selettore-has)
  - [B10. Proprietà logiche](#b10-proprietà-logiche)
  - [B11. Colori moderni e temi](#b11-colori-moderni-e-temi)
  - [B12. Transizioni, animazioni e il compositor](#b12-transizioni-animazioni-e-il-compositor)
  - [B13. Tipografia: `@font-face`, `font-display`, font variabili](#b13-tipografia-font-face-font-display-font-variabili)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: dashboard aziendale responsiva](#c2-mini-progetto-dashboard-aziendale-responsiva)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. `@property`: custom properties tipizzate e animabili](#d1-property-custom-properties-tipizzate-e-animabili)
  - [D2. Scroll-driven animations](#d2-scroll-driven-animations)
  - [D3. Anchor positioning e `@starting-style`](#d3-anchor-positioning-e-starting-style)
  - [D4. View Transitions](#d4-view-transitions)
  - [D5. Performance del rendering: `content-visibility`, `will-change`, contenimento](#d5-performance-del-rendering-content-visibility-will-change-contenimento)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                                 CSS
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
  ┌─────▼──────┐          ┌───────▼────────┐        ┌───────▼────────┐
  │  QUALE     │          │    QUANTO      │        │     DOVE       │
  │  ELEMENTO  │          │    SPAZIO      │        │                │
  │            │          │                │        │                │
  │ selettori  │          │  box model     │        │  flusso normale│
  │ specificità│          │  ├ content     │        │  position      │
  │ cascata    │          │  ├ padding     │        │  ├ static      │
  │  ├ @layer  │          │  ├ border      │        │  ├ relative    │
  │  ├ @scope  │          │  └ margin      │        │  ├ absolute    │
  │  └ !import.│          │  box-sizing    │        │  ├ fixed       │
  │ ereditarietà│         │  unità         │        │  └ sticky      │
  │ :has()     │          │  ├ px rem em   │        │  z-index       │
  └────────────┘          │  ├ % vw vh     │        │  contesti di   │
                          │  ├ fr          │        │   impilamento  │
                          │  └ ch cqi      │        └────────────────┘
                          └────────────────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      │                           │                           │
┌─────▼──────────┐      ┌─────────▼─────────┐      ┌──────────▼────────┐
│    LAYOUT      │      │   ADATTAMENTO     │      │    MOVIMENTO      │
│                │      │                   │      │                   │
│  Flexbox       │      │  media query      │      │  transition       │
│   └ un asse    │      │   └ la FINESTRA   │      │   └ da A a B      │
│  Grid          │      │  container query  │      │  @keyframes       │
│   └ due assi   │      │   └ il CONTENITORE│      │   └ sequenza      │
│   └ subgrid    │      │  clamp()          │      │  transform        │
│  proprietà     │      │   └ fluido        │      │   └ sul compositor│
│   logiche      │      │  prefers-*        │      │  scroll-driven    │
│                │      │   └ preferenze    │      │  View Transitions │
└────────────────┘      └───────────────────┘      └───────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │      ARCHITETTURA          │
                    │                            │
                    │  custom properties         │
                    │   └ --token: valore        │
                    │  @property                 │
                    │   └ tipizzate, animabili   │
                    │  design token              │
                    │   └ primitivi → semantici  │
                    │  @layer                    │
                    │   └ ordine esplicito       │
                    └────────────────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Cosa fa il CSS e come arriva alla pagina

> **Analogia:** il documento HTML è il testo di un'opera teatrale: dice chi parla e cosa dice. Il CSS è la regia: decide dove sta ciascuno sul palco, come è illuminato, che costume indossa. Cambiando regia lo stesso testo diventa un altro spettacolo — e il testo non si tocca. È il motivo per cui un sito può cambiare completamente aspetto senza che una riga di HTML si muova.

Una regola CSS ha tre parti:

```css
selettore {
  proprietà: valore;
}
```

```css
/* Il selettore dice QUALI elementi, la dichiarazione COSA fare */
h1 {
  font-size: 2rem;
  color: #0b3d91;
}
```

### I tre modi di collegare il CSS

```html
<!-- 1. Foglio esterno — l'unico da usare in un progetto reale.
        Si mette in cache, si condivide fra le pagine, si versiona. -->
<link rel="stylesheet" href="/src/stile.css" />

<!-- 2. Blocco interno — utile solo per il CSS critico
        che deve arrivare con il documento (vedi tutorial_17). -->
<style>
  body { margin: 0; }
</style>

<!-- 3. Attributo style — da evitare.
        Specificità altissima, nessun riuso, nessuna cache. -->
<p style="color: red;">Testo</p>
```

```html
<!-- ❌ SBAGLIATO — lo stile inline vince quasi su tutto e
     costringe a !important per sovrascriverlo -->
<div style="margin-top: 20px; color: #333;">…</div>

<!-- ✅ CORRETTO — una classe, sovrascrivibile con le regole normali -->
<div class="scheda">…</div>
```

L'unico uso legittimo dell'attributo `style` è passare un valore calcolato a runtime, quasi sempre attraverso una custom property:

```html
<!-- Legittimo: il valore non è noto a tempo di scrittura -->
<div class="barra-avanzamento" style="--percentuale: 62%">…</div>
```

### L'ordine di caricamento conta

```html
<head>
  <!-- Il CSS blocca il rendering: il browser non disegna nulla
       finché non ha ricevuto e analizzato i fogli di stile.
       È voluto: evita il lampo di pagina non stilata. -->
  <link rel="stylesheet" href="/src/stile.css" />
</head>
```

Questo è anche il motivo per cui un foglio di stile enorme rallenta la prima visualizzazione, e per cui esiste il concetto di CSS critico. Il tema è di `tutorial_17_performance_web.md`; qui basta sapere che il CSS va nel `<head>` e che la sua dimensione ha un costo.

---

## A2. Selettori: come si indica un elemento

```css
/* Per tipo di elemento */
p { line-height: 1.6; }

/* Per classe — il selettore che userai il 90% delle volte */
.scheda { padding: 1rem; }

/* Per id — unico nella pagina. Specificità alta: usalo con parsimonia. */
#intestazione-principale { position: sticky; }

/* Per attributo */
a[href] { text-decoration: underline; }
a[href^="https://"] { … }          /* inizia con */
a[href$=".pdf"] { … }              /* finisce con */
a[href*="acme"] { … }              /* contiene */
input[type="checkbox"] { … }
[data-stato="attivo"] { … }

/* Universale — tutti gli elementi */
* { box-sizing: border-box; }
```

### I combinatori

```css
/* Discendente (uno spazio): a qualunque profondità */
article p { margin-block: 1rem; }

/* Figlio diretto (>): solo un livello sotto */
.menu > li { display: inline-block; }

/* Fratello adiacente (+): il PRIMO fratello subito dopo */
h2 + p { margin-block-start: 0; }

/* Fratello generale (~): tutti i fratelli successivi */
h2 ~ p { color: var(--tenue); }
```

```
Dato questo markup:

<article>              article p       → tutti e tre
  <p>uno</p>           article > p     → uno, tre  (due è dentro <div>)
  <div>                h2 + p          → nessuno   (non c'è h2)
    <p>due</p>
  </div>
  <p>tre</p>
</article>
```

### Le pseudo-classi che servono davvero

```css
/* Stato dell'interazione — l'ordine conta: LVHA */
a:link { color: var(--accento); }
a:visited { color: var(--accento-visitato); }
a:hover { text-decoration: underline; }
a:active { transform: translateY(1px); }

/* Focus: :focus-visible reagisce alla tastiera, non al clic del mouse */
:focus-visible {
  outline: 3px solid var(--accento);
  outline-offset: 2px;
}

/* Posizione fra i fratelli */
li:first-child { … }
li:last-child { … }
li:only-child { … }
li:nth-child(2) { … }
li:nth-child(odd) { … }
li:nth-child(3n + 1) { … }

/* nth-of-type conta solo gli elementi dello stesso tipo */
p:nth-of-type(2) { … }

/* Stato dei form */
input:required { … }
input:disabled { … }
input:checked { … }
input:user-invalid { border-color: crimson; }   /* solo dopo l'interazione */
input:placeholder-shown { … }                    /* il campo è vuoto */

/* Negazione, e liste di selettori */
li:not(:last-child) { border-block-end: 1px solid; }
:is(h1, h2, h3) { text-wrap: balance; }
:where(h1, h2, h3) { margin-block: 0; }   /* come :is ma specificità ZERO */
```

`:is()` e `:where()` fanno la stessa cosa con una differenza cruciale: `:is()` assume la specificità del suo argomento più specifico, `:where()` vale sempre zero. `:where()` è quindi lo strumento giusto per scrivere stili di base che chiunque possa sovrascrivere senza combattere.

```css
/* Senza :is — ripetitivo e fragile */
article h1, article h2, article h3 { margin-block-start: 2rem; }

/* Con :is — leggibile */
article :is(h1, h2, h3) { margin-block-start: 2rem; }
```

### Gli pseudo-elementi

Non selezionano elementi esistenti: ne creano o ne isolano una parte.

```css
/* Due punti doppi per convenzione: distingue gli pseudo-ELEMENTI
   dalle pseudo-CLASSI (un solo due punti) */
.nota::before {
  content: '⚠ ';   /* content è OBBLIGATORIO, anche vuoto */
}

.citazione::after {
  content: '”';
}

/* La prima riga e la prima lettera */
p::first-line { font-variant: small-caps; }
p::first-letter { font-size: 3em; float: inline-start; }

/* La selezione dell'utente */
::selection { background: var(--accento); color: white; }

/* Il testo del placeholder */
input::placeholder { color: var(--tenue); }

/* Lo sfondo di una <dialog> aperta con showModal() */
dialog::backdrop { background: rgb(0 0 0 / 0.5); }

/* Il marcatore di una voce di lista */
li::marker { color: var(--accento); }
```

```css
/* ❌ SBAGLIATO — contenuto informativo dentro content:
   non è selezionabile, non è traducibile, e alcuni screen reader
   lo leggono e altri no */
.prezzo::before { content: 'Prezzo: '; }

/* ✅ CORRETTO — decorazione pura, invisibile alle tecnologie assistive */
.nota::before { content: ''; display: inline-block; width: 1em; }
```

---

## A3. La cascata e l'ereditarietà

Sono due meccanismi distinti che vengono spesso confusi.

**Ereditarietà** — alcune proprietà passano dal genitore ai figli, senza che tu faccia nulla.

```css
body {
  font-family: system-ui, sans-serif;
  color: #1a1a1a;
  line-height: 1.6;
}
/* Ogni paragrafo, titolo e voce di lista eredita queste tre proprietà. */
```

```
SI EREDITANO                      NON SI EREDITANO
──────────────────────────        ─────────────────────────────
color                             margin, padding, border
font-family, font-size            width, height
font-weight, font-style           background
line-height                       display, position
letter-spacing, word-spacing      overflow
text-align, text-indent           z-index
text-transform                    box-shadow
visibility                        transform
cursor                            
list-style                        
white-space                       
direction                         
```

La logica è coerente: si eredita ciò che riguarda il **testo**, non ciò che riguarda la **scatola**. Un `margin` ereditato moltiplicherebbe lo spazio a ogni livello di annidamento.

```css
/* Forzare l'ereditarietà quando serve */
button {
  font: inherit;        /* i pulsanti NON ereditano il font: va chiesto */
  color: inherit;
}

/* I quattro valori globali, disponibili su ogni proprietà */
.elemento {
  color: inherit;   /* prendi dal genitore */
  color: initial;   /* torna al valore iniziale della specifica */
  color: unset;     /* inherit se ereditabile, initial altrimenti */
  color: revert;    /* torna a quanto dice il foglio di stile del browser */
}
```

**Cascata** — quando più regole colpiscono lo stesso elemento con la stessa proprietà, la cascata decide chi vince. L'ordine di valutazione, dal criterio più forte al più debole:

```
1. ORIGINE E IMPORTANZA
     stile del browser
     < stile dell'utente
     < stile dell'autore (il tuo)
     < !important dell'autore
     < !important dell'utente          ← l'utente vince sull'autore
     < !important del browser

2. CASCADE LAYERS (@layer)
     l'ordine di dichiarazione dei layer, non la specificità

3. SPECIFICITÀ
     vedi A4

4. ORDINE DI APPARIZIONE
     a parità di tutto il resto, vince l'ultima dichiarata
```

```css
/* A parità di specificità, vince la seconda */
.pulsante { background: blue; }
.pulsante { background: green; }   /* ← vince */
```

**`!important` non è una soluzione.** Sposta il problema: la volta successiva servirà un `!important` più specifico, e la volta dopo ancora. Gli unici usi difendibili sono sovrascrivere lo stile inline di codice di terzi che non puoi modificare, e le utility a scopo unico in un framework.

```css
/* ❌ SBAGLIATO — l'inizio di una scalata senza fine */
.titolo { color: red !important; }

/* ✅ CORRETTO — sistema la specificità, o usa @layer (vedi B8) */
.scheda .titolo { color: red; }
```

---

## A4. La specificità, calcolata a mano

La specificità è una terna di numeri. Si confronta da sinistra a destra, e **non c'è riporto**: cento classi non arrivano a battere un id.

```
(A, B, C)
 │  │  └── elementi e pseudo-elementi:  p, h1, ::before
 │  └───── classi, attributi, pseudo-classi:  .scheda, [type], :hover
 └──────── id:  #intestazione
```

```css
p                          /* (0,0,1) */
.scheda                    /* (0,1,0) */
#menu                      /* (1,0,0) */

p.scheda                   /* (0,1,1) */
.scheda .titolo            /* (0,2,0) */
.scheda p::before          /* (0,1,2) */
#menu .voce a:hover        /* (1,2,1) */

/* :not(), :is(), :has() assumono la specificità del loro argomento più alto */
:is(#menu, .barra)         /* (1,0,0)  ← l'id la fa alzare */
:not(.attivo)              /* (0,1,0) */

/* :where() vale SEMPRE zero, qualunque cosa contenga */
:where(#menu, .barra)      /* (0,0,0) */

/* L'attributo style, fuori scala */
style="color: red"         /* batte qualunque selettore */

/* !important, fuori dal calcolo: agisce sull'origine */
```

Un esempio che chiarisce l'assenza di riporto:

```css
/* (0,11,0) — undici classi */
.a.b.c.d.e.f.g.h.i.j.k { color: blue; }

/* (1,0,0) — un id.  VINCE QUESTO. */
#titolo { color: red; }
```

**La conseguenza pratica.** Gli `id` nel CSS creano regole che diventano difficili da sovrascrivere. Riservali all'aggancio di JavaScript e ai frammenti dei link, e stila con le classi.

```css
/* ❌ SBAGLIATO — (1,1,1): per sovrascriverlo servirà un id */
#contenuto .scheda p { color: #333; }

/* ✅ CORRETTO — (0,2,0): sovrascrivibile con una regola normale */
.contenuto .scheda { color: #333; }
```

Un trucco legittimo per ridurre la specificità quando serve un selettore lungo:

```css
/* (0,1,0) invece di (0,3,0): solo .titolo conta */
:where(.pagina, .articolo) .contenitore .titolo { … }
```

---

## A5. Il box model

Ogni elemento è una scatola composta da quattro strati concentrici.

```
        ┌──────────────────────────────────────────┐
        │              MARGIN                      │  spazio esterno,
        │   ┌──────────────────────────────────┐   │  trasparente
        │   │           BORDER                 │   │
        │   │   ┌──────────────────────────┐   │   │
        │   │   │        PADDING           │   │   │  spazio interno,
        │   │   │   ┌──────────────────┐   │   │   │  prende lo sfondo
        │   │   │   │                  │   │   │   │
        │   │   │   │     CONTENT      │   │   │   │  width × height
        │   │   │   │                  │   │   │   │
        │   │   │   └──────────────────┘   │   │   │
        │   │   └──────────────────────────┘   │   │
        │   └──────────────────────────────────┘   │
        └──────────────────────────────────────────┘
```

```css
.scheda {
  width: 300px;
  padding: 20px;
  border: 2px solid;
  margin: 16px;
}
```

Quanto occupa `.scheda` in orizzontale? Dipende da `box-sizing`, ed è la domanda che confonde chiunque inizi.

```css
/* box-sizing: content-box — il DEFAULT della specifica.
   width descrive solo il contenuto: padding e border si SOMMANO. */
.scheda {
  box-sizing: content-box;
  width: 300px;
  padding: 20px;
  border: 2px solid;
}
/* Larghezza occupata: 300 + 20 + 20 + 2 + 2 = 344px
   più 16 + 16 di margin = 376px di spazio totale */

/* box-sizing: border-box — width include padding e border. */
.scheda {
  box-sizing: border-box;
  width: 300px;
  padding: 20px;
  border: 2px solid;
}
/* Larghezza occupata: 300px esatti.
   Il contenuto ne riceve 300 - 40 - 4 = 256px */
```

`border-box` è quello che chiunque si aspetta intuitivamente. La prima regola di ogni foglio di stile, da vent'anni:

```css
*,
*::before,
*::after {
  box-sizing: border-box;
}
```

### La sintassi abbreviata

```css
/* Un valore: tutti e quattro i lati */
padding: 1rem;

/* Due: verticale | orizzontale */
padding: 1rem 2rem;

/* Tre: alto | orizzontale | basso */
padding: 1rem 2rem 0.5rem;

/* Quattro: alto | destra | basso | sinistra — in senso orario */
padding: 1rem 2rem 0.5rem 1.5rem;

/* Le forme logiche, che seguono la direzione del testo (vedi B10) */
padding-block: 1rem;         /* alto e basso */
padding-inline: 2rem;        /* inizio e fine della riga */
margin-inline: auto;         /* centra orizzontalmente in un blocco */
```

`margin-inline: auto` su un elemento di larghezza definita è il modo canonico di centrarlo:

```css
.contenitore {
  max-inline-size: 60rem;
  margin-inline: auto;
}
```

---

## A6. Le unità di misura

```css
/* ASSOLUTE — un solo caso d'uso sensato: la stampa */
.etichetta { width: 5cm; }        /* cm, mm, in, pt, pc */

/* px — non è un pixel fisico, è un'unità di riferimento
   che il browser scala in base alla densità dello schermo */
.bordo { border-width: 1px; }

/* rem — relativa alla dimensione di base del ROOT (<html>).
   Di default 16px, ma l'utente può cambiarla nelle impostazioni. */
.titolo { font-size: 1.5rem; }    /* 24px con root a 16px */

/* em — relativa al font-size dell'ELEMENTO CORRENTE.
   Si compone: annidando, si moltiplica. */
.scheda { font-size: 1.2em; }

/* % — relativa alla stessa proprietà del genitore.
   Attenzione: padding e margin in % si riferiscono alla LARGHEZZA
   del contenitore, anche in verticale. */
.colonna { width: 50%; }

/* Viewport */
.eroe { block-size: 100vh; }      /* vh, vw, vmin, vmax */

/* Viewport dinamiche, per il mobile */
.eroe { block-size: 100dvh; }     /* dvh: si adatta alla barra del browser
                                     svh: viewport piccola (barre visibili)
                                     lvh: viewport grande (barre nascoste) */

/* Relative al carattere */
.testo { max-inline-size: 65ch; } /* ch = larghezza dello "0" */
.icona { block-size: 1lh; }       /* lh = line-height corrente */

/* Grid */
.griglia { grid-template-columns: 1fr 2fr; }  /* fr = frazione dello spazio libero */

/* Container query (vedi B7) */
.scheda { padding: 5cqi; }        /* cqi, cqb, cqw, cqh */
```

### `rem` contro `px`, la scelta che conta

```css
/* ❌ SBAGLIATO per il testo — ignora l'impostazione dell'utente.
   Chi ha alzato la dimensione base del browser per problemi di vista
   non vede alcun cambiamento. */
body { font-size: 16px; }
h1 { font-size: 32px; }

/* ✅ CORRETTO — scala con la preferenza dell'utente */
h1 { font-size: 2rem; }
```

```
Regola operativa:

  rem   →  font-size, spaziature, larghezze massime
           tutto ciò che deve scalare con la preferenza dell'utente

  px    →  bordi sottili, ombre, dettagli che non devono crescere
           (un bordo di 1px deve restare 1px anche a zoom 200%)

  em    →  spaziature interne a un componente che devono seguire
           la sua dimensione del carattere (padding di un pulsante)

  %     →  larghezze relative al contenitore

  fr    →  ripartizione dello spazio in Grid

  ch    →  larghezza di lettura ottimale (60-75ch)
```

```css
/* ❌ SBAGLIATO — non modificare mai la dimensione del root in %:
   annulla la preferenza dell'utente e rende ogni rem un enigma */
html { font-size: 62.5%; }   /* per far sì che 1rem = 10px */

/* ✅ CORRETTO — lascia stare il root, usa i valori reali */
.titolo { font-size: 1.5rem; }
```

### L'effetto composto di `em`

```css
.livello-1 { font-size: 1.2em; }   /* 16 × 1.2 = 19.2px */
.livello-1 .livello-2 { font-size: 1.2em; }   /* 19.2 × 1.2 = 23.04px */
.livello-1 .livello-2 .livello-3 { font-size: 1.2em; }   /* 27.6px */
```

È il motivo per cui `em` va usato con consapevolezza: in una struttura annidata cresce senza che nessuno lo abbia chiesto. `rem` non ha questo problema perché si riferisce sempre al root.

---

## A7. `display`: il comportamento di base di ogni elemento

```css
/* block — occupa tutta la larghezza disponibile, va a capo.
   Rispetta width, height, margin e padding su tutti i lati. */
div, p, h1, section, article { display: block; }

/* inline — sta nella riga del testo, si adatta al contenuto.
   IGNORA width e height, e i margini verticali non hanno effetto. */
span, a, strong, em, code { display: inline; }

/* inline-block — sta nella riga MA rispetta width, height e margini */
.pulsante-piccolo { display: inline-block; }

/* none — rimosso dal flusso E dall'albero di accessibilità */
.nascosto { display: none; }

/* contents — la scatola sparisce, i figli salgono di livello.
   Utile per far partecipare i nipoti a una griglia. */
.involucro { display: contents; }
```

```css
/* ❌ SBAGLIATO — l'altezza su un elemento inline non fa nulla */
a.pulsante {
  display: inline;
  height: 44px;      /* ignorato */
  padding-block: 12px;  /* applicato, ma non spinge le righe vicine */
}

/* ✅ CORRETTO */
a.pulsante {
  display: inline-block;
  min-block-size: 44px;
  padding-block: 12px;
}
```

**Nascondere: quattro modi, quattro significati diversi.**

| Tecnica | Occupa spazio | Visibile | Nell'albero di accessibilità | Raggiungibile con Tab |
|---|---|---|---|---|
| `display: none` | no | no | **no** | no |
| `visibility: hidden` | **sì** | no | no | no |
| `opacity: 0` | sì | no | **sì** | **sì** ← trappola |
| `.solo-screen-reader` | no | no | **sì** | sì |
| attributo `hidden` | no | no | no | no |
| attributo `inert` | sì | sì | **no** | **no** |

```css
/* Nascondere visivamente MANTENENDO l'accesso alle tecnologie assistive.
   È la classe vista in tutorial_01: serve per le etichette delle icone. */
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

`opacity: 0` è la trappola: l'elemento è invisibile ma riceve ancora il focus. Chi naviga con `Tab` finisce su un pulsante che non vede.

---

## A8. Flexbox: allineare lungo un asse

> **Analogia:** una mensola. Ci appoggi sopra degli oggetti e decidi come si distribuiscono lungo la mensola — tutti a sinistra, centrati, spaziati in modo uniforme — e come si allineano in altezza — appoggiati sul fondo, centrati, allungati a riempire. Flexbox governa **una** direzione alla volta: la mensola è una riga o una colonna, non una griglia.

```css
.contenitore {
  display: flex;
}
```

Con questa sola riga, i figli diretti diventano elementi flex: si dispongono in riga, non vanno a capo, e si allungano in altezza fino a pareggiare il più alto.

### I due assi

```
flex-direction: row  (default)

  asse principale  ──────────────────────────►
  ┌────────────────────────────────────────┐
  │  ┌──────┐  ┌──────┐  ┌──────┐          │  │ asse trasversale
  │  │  A   │  │  B   │  │  C   │          │  │
  │  └──────┘  └──────┘  └──────┘          │  ▼
  └────────────────────────────────────────┘

  justify-content  →  lungo l'asse PRINCIPALE
  align-items      →  lungo l'asse TRASVERSALE


flex-direction: column

  ┌──────────────┐    asse
  │  ┌────────┐  │    principale
  │  │   A    │  │        │
  │  └────────┘  │        │
  │  ┌────────┐  │        ▼
  │  │   B    │  │
  │  └────────┘  │    asse trasversale
  └──────────────┘    ──────────────►

  Cambiando direction, justify-content e align-items
  SI SCAMBIANO di significato. È la fonte di confusione più comune.
```

### Le proprietà del contenitore

```css
.contenitore {
  display: flex;

  /* Direzione dell'asse principale */
  flex-direction: row;              /* row | row-reverse | column | column-reverse */

  /* Andare a capo quando non c'è spazio.
     Il default è nowrap: gli elementi si comprimono invece di andare a capo. */
  flex-wrap: wrap;

  /* Abbreviazione delle due precedenti */
  flex-flow: row wrap;

  /* Distribuzione lungo l'asse PRINCIPALE */
  justify-content: flex-start;      /* flex-start | flex-end | center
                                       space-between | space-around | space-evenly */

  /* Allineamento lungo l'asse TRASVERSALE */
  align-items: stretch;             /* stretch | flex-start | flex-end | center | baseline */

  /* Allineamento delle RIGHE, quando c'è wrap e più di una riga */
  align-content: flex-start;

  /* Spazio fra gli elementi. Sostituisce i margini negativi
     e i :last-child { margin: 0 } di una volta. */
  gap: 1rem;
  /* oppure separatamente */
  row-gap: 1rem;
  column-gap: 2rem;
}
```

```
justify-content, visualizzato:

flex-start      │■■ ■■ ■■              │
center          │      ■■ ■■ ■■        │
flex-end        │              ■■ ■■ ■■│
space-between   │■■        ■■        ■■│   estremi attaccati ai bordi
space-around    │  ■■    ■■    ■■      │   metà spazio agli estremi
space-evenly    │   ■■   ■■   ■■       │   spazio uguale ovunque
```

### Le proprietà degli elementi

```css
.elemento {
  /* Quanto può CRESCERE se avanza spazio. 0 = non cresce. */
  flex-grow: 1;

  /* Quanto può RESTRINGERSI se manca spazio. Default 1. */
  flex-shrink: 1;

  /* Dimensione di partenza lungo l'asse principale, prima di crescere o restringersi */
  flex-basis: auto;

  /* L'abbreviazione — usa questa */
  flex: 1;              /* = 1 1 0%   cresce, si restringe, parte da zero */
  flex: auto;           /* = 1 1 auto cresce, si restringe, parte dal contenuto */
  flex: none;           /* = 0 0 auto rigido */
  flex: 0 0 200px;      /* larghezza fissa di 200px */

  /* Allineamento individuale sull'asse trasversale */
  align-self: center;

  /* Riordinare visivamente. ⚠ NON cambia l'ordine di tabulazione:
     il focus continua a seguire il DOM. */
  order: 2;
}
```

### I pattern che risolvono l'80% dei casi

```css
/* 1. Centrare qualcosa, in entrambe le direzioni */
.centrato {
  display: flex;
  justify-content: center;
  align-items: center;
  min-block-size: 100dvh;
}

/* 2. Barra di navigazione: logo a sinistra, menu a destra */
.testata {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

/* 3. Colonna che spinge il footer in fondo, anche con poco contenuto */
body {
  display: flex;
  flex-direction: column;
  min-block-size: 100dvh;
}
main {
  flex: 1;    /* prende tutto lo spazio avanzato */
}

/* 4. Elementi affiancati che vanno a capo da soli */
.elenco-tag {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

/* 5. Un elemento che occupa lo spazio rimanente */
.riga {
  display: flex;
  gap: 1rem;
}
.riga .flessibile {
  flex: 1;
}
```

---

## A9. Grid: righe e colonne insieme

> **Analogia:** una scacchiera disegnata sul pavimento. Prima decidi quante caselle ci sono e quanto sono grandi; poi ci appoggi sopra gli oggetti, e ognuno può occupare una casella o un rettangolo di caselle. La differenza con Flexbox è tutta qui: con Flexbox gli oggetti si dispongono e la mensola si adatta; con Grid la scacchiera esiste prima, e gli oggetti si collocano nelle sue caselle.

```css
.griglia {
  display: grid;
  grid-template-columns: 200px 1fr 200px;
  grid-template-rows: auto 1fr auto;
  gap: 1rem;
}
```

```
grid-template-columns: 200px 1fr 200px
grid-template-rows: auto 1fr auto

        200px        1fr         200px
      ┌──────────┬───────────┬──────────┐
 auto │          │           │          │
      ├──────────┼───────────┼──────────┤
      │          │           │          │
 1fr  │          │           │          │
      │          │           │          │
      ├──────────┼───────────┼──────────┤
 auto │          │           │          │
      └──────────┴───────────┴──────────┘

  1fr  = una frazione dello spazio LIBERO, dopo aver sottratto
         le tracce a dimensione fissa e i gap
  auto = quanto serve al contenuto
```

### Definire la griglia

```css
.griglia {
  display: grid;

  /* Colonne esplicite */
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-columns: repeat(3, 1fr);              /* uguale, più corto */
  grid-template-columns: 200px 1fr;                   /* fissa + flessibile */
  grid-template-columns: repeat(4, minmax(0, 1fr));   /* 4 colonne uguali che
                                                          possono restringersi */

  /* Colonne che si adattano da sole al numero di elementi */
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));

  /* Righe */
  grid-template-rows: auto 1fr auto;

  /* Dimensione delle righe create implicitamente */
  grid-auto-rows: minmax(8rem, auto);

  /* Spazio fra le celle */
  gap: 1rem;
}
```

`repeat(auto-fit, minmax(16rem, 1fr))` è la riga più utile di tutto il CSS Grid: crea quante colonne ci stanno, larghe almeno 16rem, che si dividono lo spazio in parti uguali. Una griglia responsiva **senza una sola media query**.

### Collocare gli elementi

```css
/* Per numero di linea. Attenzione: si contano le LINEE, non le colonne.
   Tre colonne hanno quattro linee. */
.elemento {
  grid-column: 1 / 3;      /* dalla linea 1 alla 3: occupa due colonne */
  grid-row: 2 / 4;
}

/* span: quante celle occupare, partendo da dove capita */
.elemento {
  grid-column: span 2;
}

/* -1 è l'ultima linea */
.larghezza-piena {
  grid-column: 1 / -1;
}
```

### Le aree nominate

La forma più leggibile, e quella da preferire quando il layout ha un nome per ogni zona:

```css
.pagina {
  display: grid;
  grid-template-columns: 16rem 1fr;
  grid-template-rows: auto 1fr auto;
  grid-template-areas:
    'testata testata'
    'barra   contenuto'
    'fondo   fondo';
  gap: 1rem;
  min-block-size: 100dvh;
}

.testata   { grid-area: testata; }
.barra     { grid-area: barra; }
.contenuto { grid-area: contenuto; }
.fondo     { grid-area: fondo; }
```

Il layout si legge nel CSS come un disegno. Riorganizzarlo per il mobile diventa banale:

```css
@media (width < 48rem) {
  .pagina {
    grid-template-columns: 1fr;
    grid-template-areas:
      'testata'
      'contenuto'
      'barra'
      'fondo';
  }
}
```

Nota che nella versione mobile la barra laterale è **sotto** il contenuto, mentre nel markup viene prima. Grid lo permette — ma il focus da tastiera continua a seguire il DOM, quindi va valutato se l'ordine risultante sia sensato. Vale la stessa avvertenza di `order` in Flexbox.

### Flexbox o Grid?

```
                    Il layout è unidimensionale?
                    (una riga, o una colonna)
                              │
              ┌───────────────┴───────────────┐
            sì│                               │no
              ▼                               ▼
        ┌──────────┐                   ┌──────────────┐
        │ FLEXBOX  │                   │     GRID     │
        └──────────┘                   └──────────────┘

Flexbox quando:
  · barra di navigazione, gruppo di pulsanti, elenco di tag
  · il contenuto determina la dimensione
  · gli elementi devono andare a capo naturalmente
  · non sai in anticipo quanti elementi ci saranno

Grid quando:
  · struttura di pagina (testata, barra, contenuto, fondo)
  · una galleria di schede allineate su righe E colonne
  · gli elementi devono allinearsi anche fra righe diverse
  · il contenitore determina la struttura

Insieme, ed è il caso più frequente:
  Grid per la pagina, Flexbox dentro i singoli componenti.
```

```css
/* Il caso tipico: Grid per il layout, Flexbox per il contenuto delle celle */
.griglia-schede {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
  gap: 1.5rem;
}

.scheda {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.scheda .azioni {
  margin-block-start: auto;   /* spinge le azioni in fondo alla scheda,
                                 così tutte le schede le hanno allineate */
}
```

---

# Parte B — Comprensione Profonda

---

## B1. Il flusso normale, il margin collapsing e i contesti di formattazione

Prima che tu scriva una riga di CSS, il browser dispone già gli elementi secondo il **flusso normale**: i blocchi uno sotto l'altro a tutta larghezza, gli inline uno accanto all'altro dentro le righe di testo. Ogni proprietà di layout che imparerai è una deviazione da questo comportamento predefinito.

### Il margin collapsing

Due margini verticali adiacenti non si sommano: **collassano**, e resta il maggiore dei due.

```html
<p style="margin-block-end: 20px">Primo</p>
<p style="margin-block-start: 30px">Secondo</p>
```

```
Ci si aspetta:  20 + 30 = 50px di distanza
In realtà:      max(20, 30) = 30px
```

È un comportamento voluto — nasce dalla tipografia, dove lo spazio fra due paragrafi non deve raddoppiare — e sorprende chiunque non lo sappia. Collassa in tre situazioni:

```css
/* 1. Fratelli adiacenti: il margine inferiore del primo con
      il margine superiore del secondo */

/* 2. Genitore e primo/ultimo figlio: se il genitore non ha
      padding, border o non crea un contesto di formattazione,
      il margine del figlio ESCE dal genitore */
.genitore {
  /* nessun padding, nessun border */
}
.genitore .primo-figlio {
  margin-block-start: 2rem;   /* spinge il GENITORE, non il figlio */
}

/* 3. Un blocco vuoto: il suo margine superiore e inferiore collassano
      fra loro */
```

**Cosa impedisce il collasso:**

```css
/* Il collasso NON avviene quando l'elemento partecipa a
   Flexbox, Grid, o crea un contesto di formattazione a blocco */

.genitore { display: flow-root; }   /* crea un BFC, il modo pulito */
.genitore { display: flex; }        /* nei contenitori flex non c'è collasso */
.genitore { display: grid; }        /* né in quelli grid */
.genitore { padding-block-start: 1px; }   /* funziona, ma è un trucco */
.genitore { overflow: hidden; }     /* funziona, ma taglia il contenuto */
```

**La soluzione che elimina il problema invece di gestirlo:** usare `gap` e margini in una sola direzione.

```css
/* ❌ SBAGLIATO — margini in entrambe le direzioni: il collasso
   diventa qualcosa da tenere a mente a ogni annidamento */
.blocco {
  margin-block: 1rem;
}

/* ✅ CORRETTO — una sola direzione, nessun collasso da calcolare */
.blocco + .blocco {
  margin-block-start: 1rem;
}

/* ✅ ANCORA MEGLIO — il contenitore governa lo spazio con gap */
.contenitore {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
```

### Contesto di formattazione a blocco (BFC)

Un BFC è una regione isolata: i float al suo interno non escono, i margini non collassano attraverso il suo confine, e il suo contenitore ne calcola correttamente l'altezza.

```css
/* Il modo moderno di crearne uno, senza effetti collaterali */
.contenitore { display: flow-root; }
```

Prima che `flow-root` esistesse si usava il *clearfix* con `::after`, o `overflow: hidden`. Il secondo funziona ma taglia i menu a discesa che sporgono, ed è la causa di un intero genere di bug difficili da diagnosticare.

```css
/* ❌ SBAGLIATO — risolve il float ma taglia tutto ciò che sporge */
.scheda { overflow: hidden; }

/* ✅ CORRETTO */
.scheda { display: flow-root; }
```

---

## B2. `position` e il contesto di impilamento

```css
/* static — il default. L'elemento sta nel flusso.
   top, right, bottom, left e z-index NON hanno effetto. */
.normale { position: static; }

/* relative — resta nel flusso e occupa il suo spazio,
   ma viene disegnato spostato. Diventa riferimento per i figli absolute. */
.spostato {
  position: relative;
  inset-block-start: 4px;
}

/* absolute — ESCE dal flusso. Si posiziona rispetto al primo antenato
   con position diversa da static. */
.sovrapposto {
  position: absolute;
  inset-block-start: 0;
  inset-inline-end: 0;
}

/* fixed — esce dal flusso, si posiziona rispetto al VIEWPORT.
   Non si muove con lo scorrimento. */
.barra-fissa {
  position: fixed;
  inset-block-end: 0;
  inset-inline: 0;
}

/* sticky — static finché non raggiunge la soglia, poi fixed
   dentro i confini del proprio contenitore. */
.intestazione-tabella {
  position: sticky;
  inset-block-start: 0;
}
```

### Perché `sticky` non funziona (le tre cause)

```css
/* 1. Manca la soglia. Senza almeno una fra top/right/bottom/left,
      sticky non ha un punto a cui agganciarsi e resta static. */
.intestazione {
  position: sticky;
  inset-block-start: 0;   /* ← obbligatorio */
}

/* 2. Un antenato ha overflow diverso da visible.
      overflow: hidden, auto o scroll su un contenitore
      disattiva sticky per tutti i discendenti. */
.contenitore {
  overflow: hidden;   /* ← rompe lo sticky dei figli */
}

/* 3. Il contenitore diretto è troppo basso.
      Sticky si muove solo dentro il proprio genitore:
      se il genitore è alto quanto l'elemento, non c'è spazio
      in cui restare appiccicato. */
```

### Il contesto di impilamento

`z-index` non è un numero globale. Ogni elemento che crea un **contesto di impilamento** confina i propri figli: un figlio con `z-index: 9999` non supererà mai un fratello del genitore con `z-index: 2`.

```
Cosa crea un contesto di impilamento:

  · position diverso da static CON uno z-index diverso da auto
  · position: fixed o sticky  (sempre, anche senza z-index)
  · opacity < 1
  · transform, filter, perspective, clip-path, mask diversi da none
  · will-change su una proprietà che ne creerebbe uno
  · isolation: isolate      ← il modo esplicito, da preferire
  · contain: layout | paint | strict | content
  · un figlio di un contenitore flex o grid con z-index diverso da auto
```

```html
<div class="genitore-a">        <!-- z-index: 1 -->
  <div class="figlio">…</div>   <!-- z-index: 9999 -->
</div>
<div class="genitore-b">…</div> <!-- z-index: 2 -->
```

```
Risultato: genitore-b sta SOPRA figlio.

  Il figlio compete solo dentro genitore-a. Fra i due genitori
  vince chi ha z-index maggiore, e tutto il sottoalbero segue.
  9999 non serve a nulla.
```

```css
/* ❌ SBAGLIATO — la scalata dei numeri.
   Ogni componente alza la posta e nessuno sa più chi vince. */
.modale { z-index: 9999; }
.notifica { z-index: 99999; }
.menu-a-tendina { z-index: 999999; }

/* ✅ CORRETTO — una scala dichiarata in un posto solo */
:root {
  --strato-base: 0;
  --strato-contenuto-sovrapposto: 10;
  --strato-barra-fissa: 100;
  --strato-menu: 200;
  --strato-modale: 300;
  --strato-notifica: 400;
}

.barra-fissa { z-index: var(--strato-barra-fissa); }
.modale { z-index: var(--strato-modale); }

/* ✅ ANCORA MEGLIO — isolare un componente perché non interferisca
   con il resto della pagina */
.componente {
  isolation: isolate;
}
```

`opacity: 0.99` su un antenato crea un contesto di impilamento ed è una delle cause più oscure di "il menu a tendina finisce sotto la scheda". Lo stesso vale per `transform`, e per questo un'animazione può rompere un layer che prima funzionava.

**La soluzione che elimina il problema.** Per le modali e i popover, il *top layer* — `<dialog>` con `showModal()` e l'attributo `popover`, visti in `tutorial_01_html5.md` — sta sopra tutto senza `z-index`, perché vive fuori dall'albero di impilamento del documento.

---

## B3. Flexbox in profondità: `flex-basis`, `min-width: auto`, `gap`

### `flex: 1` contro `flex: auto`

```css
/* flex: 1  =  flex-grow: 1  flex-shrink: 1  flex-basis: 0%
   Il contenuto NON conta: tutti gli elementi partono da zero
   e si dividono lo spazio in parti uguali. */
.uguali > * { flex: 1; }

/* flex: auto  =  flex-grow: 1  flex-shrink: 1  flex-basis: auto
   Ogni elemento parte dalla propria dimensione naturale,
   poi si divide lo spazio AVANZATO. Chi ha più testo resta più largo. */
.proporzionali > * { flex: auto; }
```

```
Tre elementi con testo di lunghezza diversa, in 900px:

flex: 1        │   300px   │   300px   │   300px   │  ← identici
flex: auto     │ 180px │      420px      │  300px  │  ← proporzionali al contenuto
```

È la distinzione che spiega perché "le colonne non sono uguali": quasi sempre è `flex: auto` dove serviva `flex: 1`.

### La trappola di `min-width: auto`

Il valore iniziale di `min-width` per un elemento flex non è `0`: è `auto`, che significa "non restringerti sotto la dimensione minima del tuo contenuto".

```css
/* ❌ Il testo lungo sfonda il contenitore invece di andare a capo */
.riga {
  display: flex;
}
.riga .colonna {
  flex: 1;
}
```

Il caso classico: una colonna contiene un `<pre>`, una tabella o un URL lunghissimo. Quel contenuto ha una larghezza minima intrinseca che l'elemento flex rispetta, e il layout esce dallo schermo.

```css
/* ✅ CORRETTO — autorizza esplicitamente la compressione */
.riga .colonna {
  flex: 1;
  min-inline-size: 0;
}

/* La stessa cosa su una colonna flex verticale */
.colonna-verticale {
  display: flex;
  flex-direction: column;
}
.colonna-verticale > * {
  min-block-size: 0;
}
```

`minmax(0, 1fr)` in Grid è l'equivalente esatto dello stesso problema:

```css
/* ❌ 1fr in realtà è minmax(auto, 1fr): non scende sotto il contenuto */
.griglia { grid-template-columns: repeat(3, 1fr); }

/* ✅ */
.griglia { grid-template-columns: repeat(3, minmax(0, 1fr)); }
```

### `gap` invece dei margini

```css
/* ❌ Il vecchio modo: margine su tutti tranne l'ultimo */
.elenco > * + * {
  margin-inline-start: 1rem;
}

/* ✅ gap: nessuna eccezione da gestire, funziona anche con il wrap */
.elenco {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}
```

Con `flex-wrap: wrap` la differenza è sostanziale: i margini producono spaziature errate sulle righe successive, `gap` no.

### Il centro perfetto, e i suoi limiti

```css
/* Centrare in entrambe le direzioni */
.centrato {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Con Grid, ancora più breve */
.centrato {
  display: grid;
  place-items: center;
}

/* Un solo figlio, centrato, senza toccare il contenitore */
.figlio {
  margin: auto;
}
```

```css
/* ❌ SBAGLIATO — 100vh su mobile include la barra del browser:
   il contenuto viene tagliato quando la barra è visibile */
.schermo-intero { min-block-size: 100vh; }

/* ✅ CORRETTO — dvh si adatta alla viewport dinamica */
.schermo-intero { min-block-size: 100dvh; }
```

---

## B4. Grid in profondità: aree nominate, `minmax`, `auto-fit`, subgrid

### `auto-fit` contro `auto-fill`

```css
.galleria-fit {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 1rem;
}

.galleria-fill {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
  gap: 1rem;
}
```

```
Contenitore da 1000px, due soli elementi, colonne da minimo 256px:

auto-fit   │ ■■■■■■■■■■■■■■■ │ ■■■■■■■■■■■■■■■ │
           Le tracce vuote COLLASSANO: i due elementi si dividono
           tutto lo spazio e diventano larghi 492px ciascuno.

auto-fill  │ ■■■■■ │ ■■■■■ │       │       │
           Le tracce vuote RESTANO: i due elementi occupano
           246px ciascuno e le altre due colonne sono vuote.

Quasi sempre vuoi auto-fit. auto-fill serve quando gli elementi
NON devono ingrandirsi solo perché sono pochi — un catalogo dove
le schede hanno una dimensione riconoscibile e costante.
```

### `minmax()`, `min-content`, `max-content`, `fit-content()`

```css
.griglia {
  display: grid;

  /* La colonna non scende sotto 12rem né supera 24rem */
  grid-template-columns: minmax(12rem, 24rem) 1fr;

  /* min-content: la larghezza minima possibile senza overflow
     (la parola più lunga) */
  grid-template-columns: min-content 1fr;

  /* max-content: la larghezza che il contenuto vorrebbe
     su una riga sola, senza andare a capo */
  grid-template-columns: max-content 1fr;

  /* fit-content(N): come max-content, ma non oltre N */
  grid-template-columns: fit-content(20rem) 1fr;
}
```

Il caso d'uso più frequente di `max-content`: una colonna di etichette che deve essere larga quanto l'etichetta più lunga, senza mandarla a capo.

```css
.modulo {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.5rem 1rem;
  align-items: baseline;
}
```

### Righe implicite

```css
.griglia {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  /* Nessuna riga dichiarata: il browser le crea al bisogno.
     grid-auto-rows dice quanto sono alte. */
  grid-auto-rows: minmax(10rem, auto);

  /* La direzione in cui riempire le celle non assegnate */
  grid-auto-flow: row;      /* row | column | row dense | column dense */
}
```

`dense` fa retrocedere gli elementi piccoli a riempire i buchi lasciati da quelli grandi. Produce una griglia più compatta ma **cambia l'ordine visivo rispetto al DOM**, quindi rende l'ordine di tabulazione incoerente con quello che si vede.

### Subgrid

Il problema che risolve: schede affiancate il cui contenuto interno deve allinearsi fra una scheda e l'altra.

```
Senza subgrid — ogni scheda si organizza da sola:

  ┌──────────────┐  ┌──────────────┐
  │ Titolo corto │  │ Titolo molto  │
  │              │  │ lungo su due  │
  │ Descrizione  │  │ righe         │
  │              │  │ Descrizione   │  ← disallineate
  │ [Azione]     │  │ [Azione]      │
  └──────────────┘  └──────────────┘

Con subgrid — le righe sono quelle della griglia esterna:

  ┌──────────────┐  ┌──────────────┐
  │ Titolo corto │  │ Titolo molto  │
  │              │  │ lungo su due  │
  ├──────────────┤  ├──────────────┤
  │ Descrizione  │  │ Descrizione   │  ← allineate
  ├──────────────┤  ├──────────────┤
  │ [Azione]     │  │ [Azione]      │
  └──────────────┘  └──────────────┘
```

```css
.galleria {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  /* Tre righe: titolo, corpo, azioni */
  grid-template-rows: repeat(3, auto);
  gap: 1rem;
}

.scheda {
  display: grid;
  /* La scheda occupa tre righe della griglia esterna... */
  grid-row: span 3;
  /* ...e le eredita invece di crearne di proprie */
  grid-template-rows: subgrid;
  gap: 0.5rem;
}
```

Subgrid è disponibile in tutti i browser evergreen dal 2023. Prima si otteneva lo stesso risultato solo con altezze fisse o con JavaScript.

### Allineamento in Grid

```css
.griglia {
  display: grid;

  /* Allineamento del CONTENUTO dentro ogni cella */
  justify-items: stretch;   /* asse in linea (orizzontale in scrittura latina) */
  align-items: stretch;     /* asse di blocco (verticale) */
  place-items: center;      /* abbreviazione: align + justify */

  /* Allineamento dell'INTERA GRIGLIA dentro il contenitore,
     quando la griglia è più piccola del contenitore */
  justify-content: start;
  align-content: start;
  place-content: center;
}

/* Su un singolo elemento */
.elemento {
  justify-self: end;
  align-self: center;
  place-self: center end;
}
```

La distinzione che confonde: `*-items` allinea il contenuto **dentro** le celle, `*-content` allinea le **tracce** dentro il contenitore.

---

## B5. Custom properties e design token

Le custom properties non sono variabili di un preprocessore: vivono nel browser a runtime, si ereditano, e si possono cambiare con JavaScript o con una media query.

```css
:root {
  --colore-accento: #0b3d91;
  --spazio-base: 1rem;
}

.pulsante {
  background: var(--colore-accento);
  padding: var(--spazio-base);
}
```

### `var()` con ripiego

```css
.componente {
  /* Se --colore-bordo non è definita, usa il secondo argomento */
  border-color: var(--colore-bordo, #d4d4d4);

  /* I ripieghi si annidano */
  color: var(--colore-testo, var(--colore-base, #1a1a1a));
}
```

È il meccanismo che rende personalizzabile un componente senza obbligare chi lo usa a definire tutto:

```css
/* Il componente dichiara i suoi punti di personalizzazione */
.scheda {
  padding: var(--scheda-padding, 1rem);
  border-radius: var(--scheda-raggio, 0.5rem);
  background: var(--scheda-sfondo, white);
}
```

```css
/* Chi lo usa cambia solo ciò che gli serve */
.scheda-evidenziata {
  --scheda-sfondo: #fffbeb;
  --scheda-padding: 1.5rem;
}
```

### Ambito ed ereditarietà

```css
/* Su :root — disponibile ovunque */
:root { --spazio: 1rem; }

/* Su un componente — disponibile solo dentro di esso e nei discendenti */
.scheda { --spazio: 0.5rem; }

/* La ridefinizione locale vince nel sottoalbero */
.scheda .compatto { --spazio: 0.25rem; }
```

```css
/* Il valore viene risolto DOVE VIENE USATO, non dove è dichiarato.
   Questo permette al componente di reagire al contesto. */
.contenitore-scuro {
  --colore-testo: white;
}

.testo {
  color: var(--colore-testo, black);
}
/* Lo stesso .testo è nero fuori e bianco dentro .contenitore-scuro */
```

### Design token: due livelli

L'errore tipico è usare direttamente nomi di colore nel codice dei componenti. Il rimedio è separare i **primitivi** (il colore che è) dai **semantici** (a cosa serve).

```css
:root {
  /* ── Livello 1: primitivi. Descrivono COSA SONO. ────────────── */
  --blu-50: #eff6ff;
  --blu-500: #3b82f6;
  --blu-700: #1d4ed8;
  --blu-900: #1e3a8a;

  --grigio-50: #fafafa;
  --grigio-200: #e5e5e5;
  --grigio-600: #525252;
  --grigio-900: #171717;

  --rosso-600: #dc2626;
  --verde-600: #16a34a;
  --ambra-500: #f59e0b;

  /* Scala di spazio su base 4px, in rem */
  --spazio-1: 0.25rem;
  --spazio-2: 0.5rem;
  --spazio-3: 0.75rem;
  --spazio-4: 1rem;
  --spazio-6: 1.5rem;
  --spazio-8: 2rem;
  --spazio-12: 3rem;

  /* Scala tipografica */
  --testo-sm: 0.875rem;
  --testo-base: 1rem;
  --testo-lg: 1.125rem;
  --testo-xl: 1.5rem;
  --testo-2xl: 2rem;

  --raggio-sm: 0.25rem;
  --raggio-md: 0.5rem;
  --raggio-lg: 1rem;
  --raggio-piena: 9999px;

  /* ── Livello 2: semantici. Descrivono A COSA SERVONO. ───────── */
  --superficie: white;
  --superficie-alternata: var(--grigio-50);
  --testo-principale: var(--grigio-900);
  --testo-tenue: var(--grigio-600);
  --bordo: var(--grigio-200);

  --azione: var(--blu-700);
  --azione-attiva: var(--blu-900);
  --azione-testo: white;

  --errore: var(--rosso-600);
  --successo: var(--verde-600);
  --avviso: var(--ambra-500);
}
```

```css
/* I componenti usano SOLO i token semantici */
.scheda {
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio-md);
  padding: var(--spazio-4);
  color: var(--testo-principale);
}
```

Il beneficio si vede al primo cambio di tema: ridefinire cinque token semantici cambia l'intera applicazione, senza toccare un solo componente.

```css
/* Modalità scura: solo i semantici cambiano.
   I primitivi restano gli stessi. */
@media (prefers-color-scheme: dark) {
  :root {
    --superficie: var(--grigio-900);
    --superficie-alternata: #202020;
    --testo-principale: var(--grigio-50);
    --testo-tenue: #a3a3a3;
    --bordo: #3a3a3a;
    --azione: var(--blu-500);
  }
}

/* Scelta esplicita dell'utente, che deve vincere sulla preferenza di sistema */
:root[data-tema='scuro'] {
  --superficie: var(--grigio-900);
  --testo-principale: var(--grigio-50);
  --bordo: #3a3a3a;
  --azione: var(--blu-500);
}

:root[data-tema='chiaro'] {
  --superficie: white;
  --testo-principale: var(--grigio-900);
  --bordo: var(--grigio-200);
  --azione: var(--blu-700);
}
```

```javascript
// Il selettore del tema, con tre stati: chiaro, scuro, sistema
const chiave = 'tema-preferito'
const salvato = localStorage.getItem(chiave)

if (salvato && salvato !== 'sistema') {
  document.documentElement.dataset.tema = salvato
}

function impostaTema(tema) {
  if (tema === 'sistema') {
    delete document.documentElement.dataset.tema
    localStorage.removeItem(chiave)
  } else {
    document.documentElement.dataset.tema = tema
    localStorage.setItem(chiave, tema)
  }
}
```

```html
<!-- Dichiarare gli schemi supportati fa sì che il browser stili
     correttamente i controlli nativi (barre di scorrimento, form) -->
<meta name="color-scheme" content="light dark" />
```

```css
/* Equivalente in CSS, e vale anche per i controlli di sistema */
:root {
  color-scheme: light dark;
}
```

### Custom properties e JavaScript

```javascript
const radice = document.documentElement

// Leggere: attenzione allo spazio iniziale nel valore restituito
const accento = getComputedStyle(radice).getPropertyValue('--azione').trim()

// Scrivere
radice.style.setProperty('--azione', '#7c3aed')

// Rimuovere l'override e tornare al valore del foglio di stile
radice.style.removeProperty('--azione')
```

Il ponte fra JavaScript e CSS più utile è passare un valore calcolato e lasciare che il CSS lo usi:

```html
<div class="barra-avanzamento" style="--percentuale: 62"></div>
```

```css
.barra-avanzamento::after {
  inline-size: calc(var(--percentuale) * 1%);
}
```

---

## B6. Responsive: media query, unità del viewport, `clamp()`

### La sintassi moderna

```css
/* La sintassi a intervalli, disponibile in tutti i browser evergreen.
   Più leggibile e senza i confronti a 0.02px di una volta. */
@media (width >= 48rem) { … }
@media (width < 48rem) { … }
@media (30rem <= width <= 60rem) { … }

/* La sintassi classica, ancora ovunque nei progetti esistenti */
@media (min-width: 48rem) { … }
@media (max-width: 47.99rem) { … }
```

**Perché `rem` e non `px` nelle media query.** Con `px`, chi ha alzato la dimensione del carattere nelle impostazioni del browser continua a ricevere il layout desktop su uno schermo che ormai è troppo stretto per contenerlo. Con `rem` il punto di rottura scala con la preferenza.

### I breakpoint, scelti dal contenuto

```css
/* ❌ SBAGLIATO — breakpoint copiati dai nomi dei dispositivi.
   I dispositivi cambiano ogni anno, il tuo contenuto no. */
@media (width >= 375px) { }   /* "iPhone" */
@media (width >= 768px) { }   /* "iPad" */
@media (width >= 1024px) { }  /* "laptop" */

/* ✅ CORRETTO — allarga la finestra finché il layout non si rompe:
   quello è il breakpoint. Pochi, e motivati. */
:root {
  --bp-medio: 48rem;    /* la barra laterale ci sta accanto al contenuto */
  --bp-grande: 72rem;   /* la griglia passa da 2 a 3 colonne */
}
```

Le custom properties non funzionano dentro le media query (la specifica lo esclude), quindi i valori vanno scritti a mano. Con un preprocessore o con `postcss-custom-media` si può centralizzarli.

### Mobile-first

```css
/* Stile di base = mobile. Nessuna media query. */
.griglia {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

/* Poi si AGGIUNGE per gli schermi più grandi */
@media (width >= 48rem) {
  .griglia { grid-template-columns: repeat(2, 1fr); }
}

@media (width >= 72rem) {
  .griglia { grid-template-columns: repeat(3, 1fr); }
}
```

Il vantaggio non è stilistico: il CSS di base è il più semplice, e i dispositivi meno potenti non devono valutare e sovrascrivere regole pensate per il desktop.

### Le media query che non riguardano la larghezza

```css
/* Movimento ridotto — una preferenza di sistema, non un capriccio */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* Schema di colore */
@media (prefers-color-scheme: dark) { … }

/* Contrasto elevato */
@media (prefers-contrast: more) {
  :root { --bordo: black; }
}

/* Tipo di puntatore: fine (mouse) o grossolano (dito) */
@media (pointer: coarse) {
  /* Bersagli più grandi per il tocco: WCAG 2.5.8 chiede almeno 24×24 CSS px,
     e 44×44 è la raccomandazione operativa */
  button { min-block-size: 44px; min-inline-size: 44px; }
}

/* Il dispositivo può fare hover? */
@media (hover: hover) {
  .scheda:hover { transform: translateY(-2px); }
}

/* Orientamento */
@media (orientation: landscape) { … }

/* Stampa */
@media print {
  nav, .barra-laterale, .pulsanti { display: none; }
  a[href^="http"]::after { content: ' (' attr(href) ')'; }
}
```

`@media (hover: hover)` risolve un problema reale: su un dispositivo touch lo stato `:hover` si attiva al primo tocco e resta appiccicato finché non si tocca altrove.

### Unità del viewport, e il problema del mobile

```
vh   viewport height   — su mobile usa la viewport GRANDE (barre nascoste):
                          il contenuto viene tagliato quando le barre appaiono
svh  small viewport    — la più piccola possibile (barre visibili)
lvh  large viewport    — la più grande possibile (barre nascoste)
dvh  dynamic viewport  — cambia mentre le barre appaiono e scompaiono
```

```css
/* ❌ Il classico "il pulsante in fondo è nascosto dalla barra del browser" */
.schermata { block-size: 100vh; }

/* ✅ */
.schermata { min-block-size: 100dvh; }
```

`dvh` provoca un ricalcolo del layout mentre l'utente scorre, il che può risultare scattoso. Quando il contenuto non deve necessariamente riempire lo schermo, `svh` è più stabile.

### Tipografia fluida con `clamp()`

```css
/* clamp(minimo, preferito, massimo) */
h1 {
  font-size: clamp(1.75rem, 1.2rem + 2.5vw, 3rem);
}
```

```
Come si legge:

  1.75rem              non scendere mai sotto
  1.2rem + 2.5vw       il valore che scala con la finestra
  3rem                 non salire mai sopra

Il termine in rem nella parte centrale è essenziale: garantisce
che il testo continui a rispondere allo zoom del browser.
Un clamp con solo vw al centro (clamp(1.75rem, 4vw, 3rem))
blocca l'ingrandimento — è una violazione di WCAG 1.4.4.
```

```css
/* Una scala tipografica fluida completa */
:root {
  --testo-sm: clamp(0.8rem, 0.77rem + 0.15vw, 0.9rem);
  --testo-base: clamp(1rem, 0.95rem + 0.25vw, 1.15rem);
  --testo-lg: clamp(1.15rem, 1.05rem + 0.5vw, 1.5rem);
  --testo-xl: clamp(1.4rem, 1.2rem + 1vw, 2rem);
  --testo-2xl: clamp(1.75rem, 1.2rem + 2.5vw, 3rem);
}

/* Anche gli spazi possono essere fluidi */
:root {
  --spazio-sezione: clamp(2rem, 1rem + 5vw, 6rem);
}
```

`clamp()` sostituisce interi blocchi di media query per la tipografia: una dichiarazione al posto di tre o quattro breakpoint.

---

## B7. Container queries: rispondere al contenitore, non alla finestra

> **Analogia:** una media query è un termostato centrale che regola tutta la casa in base alla temperatura esterna. Una container query è un termostato per stanza. Lo stesso radiatore si comporta diversamente in salotto e in bagno, perché reagisce a dove si trova, non a cosa succede fuori.

Il problema che risolve: la stessa scheda usata nella colonna principale (larga) e nella barra laterale (stretta) ha bisogno di layout diversi. Una media query non lo sa: conosce solo la finestra.

```css
/* 1. Dichiarare un contenitore */
.colonna-principale,
.barra-laterale {
  container-type: inline-size;
  /* Un nome, opzionale ma utile con contenitori annidati */
  container-name: colonna;
}

/* Abbreviazione */
.colonna-principale {
  container: colonna / inline-size;
}

/* 2. Interrogarlo */
@container colonna (width >= 30rem) {
  .scheda {
    display: grid;
    grid-template-columns: 12rem 1fr;
    gap: 1rem;
  }
}

@container colonna (width < 30rem) {
  .scheda {
    display: flex;
    flex-direction: column;
  }
}
```

```html
<!-- La STESSA scheda, due contesti, due layout — senza classi diverse -->
<div class="colonna-principale">
  <article class="scheda">…</article>   <!-- orizzontale -->
</div>

<aside class="barra-laterale">
  <article class="scheda">…</article>   <!-- verticale -->
</aside>
```

### La regola che sorprende

Un elemento **non può interrogare sé stesso**. `container-type` va sul genitore di ciò che vuoi stilare.

```css
/* ❌ SBAGLIATO — la scheda dichiara sé stessa contenitore
   e poi cerca di interrogarsi: non funziona */
.scheda {
  container-type: inline-size;
}
@container (width >= 30rem) {
  .scheda { … }   /* non si applica mai */
}

/* ✅ CORRETTO — il contenitore è il genitore */
.involucro-scheda {
  container-type: inline-size;
}
@container (width >= 30rem) {
  .scheda { … }
}
```

### `container-type`, i tre valori

```css
/* inline-size — interroga solo la larghezza. Il caso normale.
   Applica il contenimento sull'asse in linea. */
container-type: inline-size;

/* size — larghezza E altezza. Richiede che l'altezza del contenitore
   sia determinata indipendentemente dal contenuto, altrimenti
   si crea una dipendenza circolare. Raro. */
container-type: size;

/* normal — nessuna query di dimensione, ma abilita le container
   style query (vedi sotto) */
container-type: normal;
```

**Il costo:** `container-type` applica un contenimento del layout, il che significa che l'altezza del contenitore non dipende più dal contenuto nel modo consueto. Su `inline-size` l'effetto è limitato all'asse orizzontale ed è quasi sempre innocuo; con `size` va verificato.

### Le unità di container query

```css
@container colonna (width >= 30rem) {
  .scheda {
    /* cqi = 1% della dimensione in linea del contenitore
       cqb = 1% della dimensione di blocco
       cqw / cqh = larghezza / altezza
       cqmin / cqmax */
    padding: 3cqi;
    font-size: clamp(1rem, 4cqi, 1.5rem);
  }
}
```

Sono a `vw` ciò che le container query sono alle media query: proporzionali al contenitore invece che alla finestra.

### Style query

Interrogano il valore di una custom property invece di una dimensione:

```css
.scheda {
  --variante: standard;
}

.scheda.in-evidenza {
  --variante: evidenziata;
}

@container style(--variante: evidenziata) {
  .titolo-scheda {
    color: var(--azione);
    font-weight: 700;
  }
}
```

Il supporto delle style query sulle custom properties è arrivato nei browser evergreen; l'estensione alle proprietà CSS normali è ancora in definizione. Per ora è una comodità, non una fondamenta su cui costruire.

---

## B8. Cascade layers e `@scope`

### `@layer`

Il problema: il CSS di un framework, quello del tuo design system e le tue sovrascritture competono per specificità, e finisci per scrivere selettori sempre più lunghi. `@layer` sostituisce quella gara con un ordine dichiarato.

```css
/* L'ordine di DICHIARAZIONE stabilisce la priorità.
   Va scritto in cima, prima di qualunque regola. */
@layer reset, terze-parti, base, componenti, utility;

@layer reset {
  *, *::before, *::after { box-sizing: border-box; }
  body { margin: 0; }
}

@layer base {
  /* Selettore lunghissimo, ma sta in un layer basso */
  html body main article h1 { font-size: 2rem; }
}

@layer componenti {
  /* Selettore cortissimo: VINCE COMUNQUE,
     perché il suo layer viene dopo. */
  h1 { font-size: 2.5rem; }
}
```

```
La regola nuova:

  All'interno di un layer, vale la specificità normale.
  FRA layer diversi, vince sempre il layer dichiarato dopo —
  qualunque sia la specificità.

  Un selettore (0,0,1) in un layer alto batte
  un selettore (1,2,3) in un layer basso.
```

Il CSS scritto **fuori** da qualunque layer ha priorità su tutti i layer. È il comportamento voluto: permette di introdurre i layer gradualmente in un progetto esistente senza che il codice non ancora migrato smetta di funzionare.

```
Priorità complessiva:

  layer 1 < layer 2 < … < layer N < CSS senza layer < !important
```

```css
/* Importare un foglio di terze parti direttamente in un layer:
   così il suo CSS non compete più con il tuo */
@import url('normalize.css') layer(reset);
@import url('bootstrap.css') layer(terze-parti);
```

```css
/* Layer annidati, per organizzare un design system */
@layer componenti {
  @layer base, varianti, stati;

  @layer base {
    .pulsante { padding: 0.5rem 1rem; }
  }

  @layer stati {
    .pulsante:disabled { opacity: 0.5; }
  }
}
```

### `@scope`

Limita l'effetto delle regole a un sottoalbero, con un confine superiore e uno inferiore.

```css
/* Le regole valgono dentro .scheda, e si FERMANO a .contenuto-utente */
@scope (.scheda) to (.contenuto-utente) {
  p {
    margin-block: 0.5rem;
    color: var(--testo-tenue);
  }

  /* :scope è la radice dell'ambito */
  :scope {
    padding: 1rem;
  }
}
```

```html
<article class="scheda">
  <p>Stilato: sta dentro l'ambito.</p>

  <div class="contenuto-utente">
    <p>NON stilato: è oltre il confine inferiore.</p>
  </div>
</article>
```

Il caso d'uso concreto è isolare il contenuto generato dagli utenti — HTML che arriva da un editor di testo o da Markdown — dagli stili del componente che lo contiene. Senza `@scope` serve una serie di `:not()` fragili.

`@scope` ha anche una regola di prossimità: fra due regole di ambito applicabili vince quella la cui radice è più vicina all'elemento. È utile per i temi annidati.

```css
@scope (.tema-chiaro) {
  .pannello { background: white; }
}

@scope (.tema-scuro) {
  .pannello { background: #171717; }
}
```

Un `.pannello` dentro `.tema-chiaro > .tema-scuro` prende lo sfondo scuro, perché `.tema-scuro` è più vicino. Con i selettori normali sarebbe vinto dall'ordine di dichiarazione.

---

## B9. Il selettore `:has()`

Per vent'anni il CSS ha potuto guardare solo verso il basso e di lato. `:has()` permette a un elemento di essere selezionato in base a ciò che contiene — il "selettore del genitore" che è stato chiesto per due decenni.

```css
/* Una scheda che contiene un'immagine si comporta diversamente */
.scheda:has(img) {
  display: grid;
  grid-template-columns: 12rem 1fr;
}

/* Un form con almeno un campo in errore */
form:has(:user-invalid) {
  border-inline-start: 3px solid var(--errore);
}

/* Il gruppo di un checkbox spuntato */
.opzione:has(input:checked) {
  background: var(--azione);
  color: var(--azione-testo);
}

/* Un'etichetta il cui campo è obbligatorio */
.campo:has([required]) label::after {
  content: ' *';
  color: var(--errore);
}
```

### Combinato con i combinatori

```css
/* Un h2 SEGUITO da un p: togli il margine inferiore */
h2:has(+ p) {
  margin-block-end: 0.25rem;
}

/* Il contenitore di una figura senza didascalia */
figure:not(:has(figcaption)) {
  margin-block-end: 2rem;
}

/* Una tabella che contiene un tfoot */
table:has(tfoot) tbody tr:last-child td {
  border-block-end-width: 2px;
}
```

### Il pattern che elimina più JavaScript

```css
/* Quando la modale è aperta, blocca lo scorrimento del corpo.
   Prima serviva JavaScript per aggiungere e togliere una classe. */
body:has(dialog[open]) {
  overflow: hidden;
}

/* Il menu mobile aperto oscura il resto */
body:has(#menu-mobile:checked) .contenuto {
  filter: blur(2px);
  pointer-events: none;
}

/* Il layout cambia se la barra laterale esiste */
.pagina:has(> .barra-laterale) {
  grid-template-columns: 16rem 1fr;
}

.pagina:not(:has(> .barra-laterale)) {
  grid-template-columns: 1fr;
}
```

### Specificità e limiti

```css
/* :has() assume la specificità del suo argomento PIÙ ALTO */
.scheda:has(#speciale) { … }   /* (1,1,0) — l'id conta */
.scheda:has(.evidenza) { … }   /* (0,2,0) */

/* Neutralizzarla con :where() */
.scheda:has(:where(#speciale)) { … }   /* (0,1,0) */
```

```css
/* ❌ NON VALIDO — :has() non può contenere un altro :has() */
.a:has(.b:has(.c)) { … }

/* ❌ NON VALIDO — non si possono usare pseudo-elementi dentro :has() */
.scheda:has(::before) { … }
```

**Il costo prestazionale.** `:has()` è ottimizzato nei browser moderni, ma un selettore come `body:has(.qualsiasi-cosa)` costringe a rivalutare a ogni mutazione del DOM. Nella pratica il costo è trascurabile per la maggior parte dei casi; diventa misurabile su liste con migliaia di nodi che cambiano di continuo. La regola è: ancoralo a un contenitore ristretto, non a `body`, quando puoi.

---

## B10. Proprietà logiche

Le proprietà fisiche (`left`, `right`, `top`, `bottom`) presuppongono che il testo scorra da sinistra a destra e dall'alto in basso. Le proprietà logiche si riferiscono al **flusso del testo**, e si adattano da sole quando la direzione cambia.

```
Scrittura latina (horizontal-tb, ltr):

    block-start  =  top
    block-end    =  bottom
    inline-start =  left
    inline-end   =  right

Arabo o ebraico (rtl) — l'asse in linea si inverte:

    inline-start =  RIGHT
    inline-end   =  LEFT

Giapponese verticale (vertical-rl) — gli assi si scambiano:

    block-start  =  right
    inline-start =  top
```

```css
/* Fisiche → Logiche */
margin-left        →  margin-inline-start
margin-right       →  margin-inline-end
margin-top         →  margin-block-start
margin-bottom      →  margin-block-end

padding-left       →  padding-inline-start
border-left        →  border-inline-start

width              →  inline-size
height             →  block-size
min-width          →  min-inline-size
max-height         →  max-block-size

top: 0; left: 0    →  inset-block-start: 0; inset-inline-start: 0
text-align: left   →  text-align: start
float: left        →  float: inline-start
```

```css
/* Le abbreviazioni, che coprono i due lati insieme */
margin-inline: auto;              /* start e end */
margin-block: 1rem 2rem;          /* start 1rem, end 2rem */
padding-inline: 1rem;
inset: 0;                         /* tutti e quattro */
inset-inline: 0;
```

```css
/* ❌ SBAGLIATO — richiede un foglio di stile separato per l'arabo */
.scheda {
  margin-left: 1rem;
  border-left: 3px solid;
  text-align: left;
}

/* ✅ CORRETTO — un solo foglio di stile, si adatta a dir="rtl" */
.scheda {
  margin-inline-start: 1rem;
  border-inline-start: 3px solid;
  text-align: start;
}
```

Anche in un progetto che non prevede lingue da destra a sinistra, le proprietà logiche valgono la pena: `margin-inline: auto` per centrare è più espressivo di `margin-left: auto; margin-right: auto`, e `inline-size` dice a chi legge che quella è la dimensione lungo la riga.

**Le eccezioni.** `box-shadow`, `transform: translate()`, `background-position` e i gradienti non hanno ancora un equivalente logico: restano fisici e vanno invertiti a mano quando serve.

```css
/* Per le ombre direzionali in un contesto bidirezionale */
.scheda {
  box-shadow: 4px 0 8px rgb(0 0 0 / 0.1);
}

[dir='rtl'] .scheda {
  box-shadow: -4px 0 8px rgb(0 0 0 / 0.1);
}
```

---

## B11. Colori moderni e temi

### Le notazioni

```css
.elemento {
  /* Esadecimale, con canale alfa opzionale a 8 cifre */
  color: #0b3d91;
  color: #0b3d91cc;    /* 80% di opacità */

  /* Sintassi moderna: spazi invece di virgole, alfa dopo lo slash */
  color: rgb(11 61 145);
  color: rgb(11 61 145 / 0.8);
  color: hsl(220 86% 31%);
  color: hsl(220 86% 31% / 0.8);

  /* HSL è più maneggevole per costruire una scala:
     stessa tinta, luminosità diversa */
  --tinta: 220;
  --colore-500: hsl(var(--tinta) 86% 50%);
  --colore-700: hsl(var(--tinta) 86% 31%);
  --colore-900: hsl(var(--tinta) 86% 18%);
}
```

### Gli spazi colore percettivi

```css
.elemento {
  /* oklch(luminosità chroma tinta) — luminosità PERCETTIVAMENTE uniforme.
     A parità di L, due colori appaiono ugualmente luminosi:
     cosa che in HSL non è vera. */
  color: oklch(45% 0.18 264);
  color: oklch(45% 0.18 264 / 0.8);

  /* lch e lab, l'altra famiglia percettiva */
  color: lch(45% 60 264);
}
```

```
Il problema di HSL che oklch risolve:

  hsl(60 100% 50%)   giallo    → appare MOLTO luminoso
  hsl(240 100% 50%)  blu       → appare MOLTO scuro
  Stessa L dichiarata, luminosità percepita opposta.

  oklch(70% 0.15 60)  e  oklch(70% 0.15 264)
  appaiono ugualmente luminosi. È ciò che rende oklch
  adatto a costruire scale di colore coerenti.
```

`oklch` è disponibile in tutti i browser evergreen dal 2023. Permette anche colori fuori dal gamut sRGB su schermi che li supportano, il che è il motivo per cui i colori "accesi" dei design system recenti sono definiti così.

### `color-mix()`

```css
.elemento {
  /* Mescola due colori in uno spazio dichiarato */
  background: color-mix(in oklch, var(--azione) 20%, white);

  /* Uno stato hover derivato, senza definire un nuovo token */
  --azione-hover: color-mix(in oklch, var(--azione) 85%, black);

  /* Un bordo tenue derivato dal testo, che segue automaticamente il tema */
  border-color: color-mix(in srgb, currentColor 15%, transparent);
}
```

`color-mix(in srgb, currentColor 15%, transparent)` è il pattern che permette a un bordo di seguire il colore del testo in tema chiaro e scuro senza definire due token.

### Contrasto: il vincolo che non si negozia

```
WCAG 2.2 richiede:

  Testo normale (< 18pt o < 14pt grassetto)   4.5:1   livello AA
  Testo grande (≥ 18pt o ≥ 14pt grassetto)    3:1     livello AA
  Componenti dell'interfaccia e grafica       3:1     livello AA (1.4.11)
  Testo normale                                7:1     livello AAA

Va verificato in ENTRAMBI i temi. Un tema scuro costruito
invertendo i colori del chiaro quasi sempre fallisce da qualche parte.
```

```css
/* ❌ Frequente e sbagliato: testo tenue su sfondo tenue */
.testo-secondario {
  color: #999;        /* su bianco: 2.85:1 — non conforme */
}

/* ✅ */
.testo-secondario {
  color: #595959;     /* su bianco: 7:1 */
}
```

Il contrasto si verifica con il pannello Elements di DevTools — passando il puntatore su un colore compare il rapporto — o con strumenti come il *Colour Contrast Analyser*.

### Gradienti

```css
.elemento {
  background: linear-gradient(to bottom, var(--blu-500), var(--blu-900));
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  /* Radiale */
  background: radial-gradient(circle at 30% 20%, #fff, #ddd);

  /* Conico — utile per grafici a torta e indicatori circolari */
  background: conic-gradient(
    var(--azione) 0turn calc(var(--percentuale) * 1turn),
    var(--bordo) calc(var(--percentuale) * 1turn) 1turn
  );

  /* Interpolazione in uno spazio percettivo: evita la zona grigia
     che compare al centro dei gradienti fra colori complementari */
  background: linear-gradient(in oklch, blue, yellow);
}
```

---

## B12. Transizioni, animazioni e il compositor

### Transizioni

```css
.pulsante {
  background: var(--azione);
  /* proprietà | durata | funzione di temporizzazione | ritardo */
  transition: background 200ms ease-out;
}

.pulsante:hover {
  background: var(--azione-attiva);
}

/* Più proprietà, separate da virgola */
.scheda {
  transition:
    transform 200ms ease-out,
    box-shadow 200ms ease-out;
}
```

```css
/* ❌ SBAGLIATO — transition: all costringe il browser a osservare
   ogni proprietà, e anima cose che non volevi animare */
.scheda { transition: all 300ms; }

/* ✅ CORRETTO — dichiara cosa deve animarsi */
.scheda { transition: transform 300ms, opacity 300ms; }
```

**Non tutte le proprietà si possono animare.** Servono valori interpolabili: `display`, `position` e `font-family` cambiano di scatto. Da poco `display` è animabile con `transition-behavior: allow-discrete`, che permette la dissolvenza in uscita di un elemento che finisce a `display: none`:

```css
.pannello {
  opacity: 1;
  transition:
    opacity 200ms,
    display 200ms allow-discrete;
}

.pannello[hidden] {
  opacity: 0;
  display: none;
}
```

### Animazioni con `@keyframes`

```css
@keyframes comparsa {
  from {
    opacity: 0;
    transform: translateY(0.5rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.notifica {
  animation: comparsa 300ms ease-out;
}

/* La forma estesa */
.indicatore {
  animation-name: rotazione;
  animation-duration: 1s;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
  animation-direction: normal;      /* normal | reverse | alternate */
  animation-fill-mode: forwards;    /* mantiene lo stato finale */
  animation-play-state: running;
}
```

`animation-fill-mode: forwards` è quello che serve nove volte su dieci: senza, l'elemento torna allo stato iniziale appena l'animazione finisce.

### Cosa gira sul compositor e cosa no

```
Il rendering di un frame ha tre fasi:

  LAYOUT   →  dove sta ogni cosa e quanto è grande
  PAINT    →  che pixel disegnare
  COMPOSITE→  come sovrapporre i livelli già disegnati

Animare una proprietà che tocca il LAYOUT costringe a rifare
tutte e tre le fasi, per ogni fotogramma, sul thread principale.

  ❌ width, height, top, left, margin, padding, font-size
     → layout + paint + composite

  ⚠ background-color, color, box-shadow, border-radius
     → paint + composite

  ✅ transform, opacity, filter
     → SOLO composite, e su un thread separato dal principale
```

```css
/* ❌ SBAGLIATO — anima left: rifà il layout 60 volte al secondo */
.pannello {
  position: absolute;
  left: -300px;
  transition: left 300ms;
}
.pannello.aperto { left: 0; }

/* ✅ CORRETTO — transform gira sul compositor:
   scorre fluido anche mentre il thread principale è occupato */
.pannello {
  transform: translateX(-100%);
  transition: transform 300ms ease-out;
}
.pannello.aperto { transform: translateX(0); }
```

```css
/* ❌ SBAGLIATO — anima width e height */
.scheda:hover { width: 105%; height: 105%; }

/* ✅ CORRETTO */
.scheda { transition: transform 200ms; }
.scheda:hover { transform: scale(1.05); }
```

### `will-change`, da usare con parsimonia

```css
/* Dice al browser di preparare un livello separato in anticipo */
.pannello {
  will-change: transform;
}
```

```css
/* ❌ SBAGLIATO — will-change permanente su molti elementi:
   ogni livello consuma memoria video, e su mobile si arriva
   a peggiorare le prestazioni invece di migliorarle */
* { will-change: transform; }

/* ✅ CORRETTO — attivato solo poco prima dell'animazione,
   e rimosso dopo */
.pannello:hover { will-change: transform; }
```

```javascript
// Da JavaScript, il ciclo completo
elemento.style.willChange = 'transform'
elemento.addEventListener(
  'transitionend',
  () => {
    elemento.style.willChange = 'auto'
  },
  { once: true },
)
```

Nella maggior parte dei casi `will-change` non serve: i browser promuovono automaticamente gli elementi che animano `transform` e `opacity`.

### Rispettare la preferenza di movimento

```css
/* Il blocco che va in ogni progetto */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Non è una preferenza estetica: per chi ha disturbi vestibolari le animazioni di movimento provocano nausea e vertigini reali. `0.01ms` invece di `none` fa sì che gli eventi `transitionend` e `animationend` continuino a scattare, così il codice che li ascolta non si blocca.

Una versione più raffinata mantiene le dissolvenze — che raramente danno fastidio — ed elimina solo il movimento:

```css
@media (prefers-reduced-motion: reduce) {
  .scheda {
    transition: opacity 200ms;   /* la dissolvenza resta */
    transform: none;             /* il movimento sparisce */
  }
}
```

---

## B13. Tipografia: `@font-face`, `font-display`, font variabili

```css
@font-face {
  font-family: 'Inter';
  src: url('/font/inter-var.woff2') format('woff2-variations');
  font-weight: 100 900;      /* intervallo, non un valore singolo */
  font-style: normal;
  font-display: swap;
  /* Scarica solo i glifi latini: riduce sensibilmente il peso */
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+2000-206F;
}
```

### `font-display`, i cinque valori

```
auto      lascia decidere al browser (di norma come block)

block     ~3s invisibile, poi il ripiego.  FOIT: testo invisibile.
          Da evitare: il contenuto non si legge finché il font non arriva.

swap      ripiego SUBITO, sostituzione all'arrivo.  FOUT: il testo salta.
          Il default sensato: il contenuto è sempre leggibile.

fallback  ~100ms invisibile, poi il ripiego; sostituisce solo entro ~3s.
          Compromesso ragionevole.

optional  ~100ms invisibile; se il font non è pronto, NON lo usa affatto.
          Il migliore per le Core Web Vitals, il peggiore per la coerenza visiva.
```

Il salto del testo (`swap`) si riduce allineando le metriche del font di ripiego a quello reale:

```css
@font-face {
  font-family: 'Inter ripiego';
  src: local('Arial');
  size-adjust: 107%;
  ascent-override: 90%;
  descent-override: 22%;
  line-gap-override: 0%;
}

body {
  font-family: 'Inter', 'Inter ripiego', system-ui, sans-serif;
}
```

### Precaricare i font critici

```html
<!-- crossorigin è OBBLIGATORIO per i font, anche sullo stesso dominio:
     senza, il browser scarica il file due volte -->
<link
  rel="preload"
  href="/font/inter-var.woff2"
  as="font"
  type="font/woff2"
  crossorigin
/>
```

Precarica solo i font usati **sopra la piega**, e mai più di uno o due: ogni preload compete con le altre risorse critiche.

### Font di sistema, l'opzione che costa zero

```css
body {
  font-family:
    system-ui,
    -apple-system,
    'Segoe UI',
    Roboto,
    'Helvetica Neue',
    Arial,
    sans-serif;
}

code, pre {
  font-family: ui-monospace, 'SF Mono', 'Cascadia Code', Consolas, monospace;
}
```

Nessun download, nessun salto del testo, nessun impatto sulle metriche, e il testo appare familiare su ogni piattaforma. Per un pannello di amministrazione o uno strumento interno è quasi sempre la scelta giusta.

### Font variabili

Un solo file contiene tutti i pesi e le larghezze, invece di un file per variante.

```css
body {
  font-family: 'Inter', sans-serif;
  /* Qualunque valore intermedio, non solo i multipli di 100 */
  font-weight: 437;
  /* Assi personalizzati, se il font li espone */
  font-variation-settings: 'wght' 437, 'slnt' -6;
}
```

Un file variabile pesa più di un singolo peso statico ma molto meno di quattro o cinque, ed evita richieste multiple.

### Leggibilità

```css
.contenuto {
  /* 60-75 caratteri per riga: oltre, l'occhio fatica a trovare
     l'inizio della riga successiva */
  max-inline-size: 65ch;

  /* line-height senza unità: si moltiplica per il font-size
     dell'elemento, quindi si adatta ai figli */
  line-height: 1.6;

  /* Evita che una riga resti con una sola parola */
  text-wrap: pretty;
}

h1, h2, h3 {
  /* Bilancia le righe di un titolo su più righe */
  text-wrap: balance;
  line-height: 1.2;
}
```

```css
/* ❌ SBAGLIATO — line-height con unità non si adatta ai figli:
   un figlio con font-size maggiore avrà le righe sovrapposte */
body { line-height: 24px; }

/* ✅ CORRETTO */
body { line-height: 1.6; }
```

`text-wrap: balance` è pensato per i titoli — ha un limite di righe oltre il quale il browser smette di applicarlo — mentre `text-wrap: pretty` è per i paragrafi lunghi ed elimina le righe orfane.

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Calcolare la specificità e prevedere il vincitore

**Obiettivo:** dato un insieme di regole, dire di che colore risulta l'elemento — senza aprire il browser.

```html
<div id="pagina" class="tema-chiaro">
  <article class="scheda in-evidenza">
    <p class="testo">Di che colore sono?</p>
  </article>
</div>
```

```css
/* 1 */ p { color: black; }
/* 2 */ .testo { color: blue; }
/* 3 */ .scheda p { color: green; }
/* 4 */ .scheda .testo { color: orange; }
/* 5 */ article.in-evidenza p.testo { color: purple; }
/* 6 */ #pagina p { color: red; }
/* 7 */ :where(#pagina) .testo { color: teal; }
```

```
# SOLUZIONE — calcolo, regola per regola:
#
#  regola  selettore                      (A,B,C)   note
#  ──────  ─────────────────────────────  ───────   ─────────────────────
#    1     p                              (0,0,1)
#    2     .testo                         (0,1,0)
#    3     .scheda p                      (0,1,1)
#    4     .scheda .testo                 (0,2,0)
#    5     article.in-evidenza p.testo    (0,2,2)
#    6     #pagina p                      (1,0,1)   ← VINCE
#    7     :where(#pagina) .testo         (0,1,0)   :where azzera l'id
#
# Il confronto è da sinistra a destra, senza riporto:
# la regola 6 ha A=1, tutte le altre hanno A=0. Vince subito,
# senza nemmeno guardare B e C.
#
# RISPOSTA: rosso (red)
#
# Nota la regola 7: (0,1,0) invece di (1,1,0), perché :where()
# vale sempre zero qualunque cosa contenga. È il motivo per cui
# si usa per scrivere stili di base facilmente sovrascrivibili.
```

**Variante:** cosa cambia aggiungendo `@layer`?

```css
@layer base, componenti;

@layer componenti {
  /* (0,0,1) — la specificità più bassa di tutte */
  p { color: black; }
}

@layer base {
  /* (1,0,1) — la specificità più alta */
  #pagina p { color: red; }
}
```

```
# SOLUZIONE: NERO.
#
# I layer vengono confrontati PRIMA della specificità.
# 'componenti' è dichiarato dopo 'base' nella riga @layer,
# quindi vince l'intero layer — e con esso il suo p { color: black }
# nonostante abbia specificità (0,0,1) contro (1,0,1).
#
# È esattamente il punto di @layer: sostituire la gara di specificità
# con un ordine dichiarato una volta sola.
```

---

### Esercizio 2 — Layout di pagina con Grid e aree nominate

**Obiettivo:** una struttura testata / barra laterale / contenuto / piè di pagina che si riorganizza in colonna su schermo stretto.

```html
<div class="pagina">
  <header class="pagina__testata">Testata</header>
  <nav class="pagina__barra">Barra laterale</nav>
  <main class="pagina__contenuto">Contenuto</main>
  <aside class="pagina__spalla">Spalla</aside>
  <footer class="pagina__fondo">Piè di pagina</footer>
</div>
```

```css
/* SOLUZIONE */

/* Mobile-first: una colonna sola, nessuna media query */
.pagina {
  display: grid;
  grid-template-columns: 1fr;
  grid-template-areas:
    'testata'
    'contenuto'
    'barra'
    'spalla'
    'fondo';
  gap: 1rem;
  min-block-size: 100dvh;
  padding: 1rem;
}

.pagina__testata   { grid-area: testata; }
.pagina__barra     { grid-area: barra; }
.pagina__contenuto { grid-area: contenuto; }
.pagina__spalla    { grid-area: spalla; }
.pagina__fondo     { grid-area: fondo; }

/* Tablet: la barra affianca il contenuto */
@media (width >= 48rem) {
  .pagina {
    grid-template-columns: 14rem 1fr;
    grid-template-areas:
      'testata   testata'
      'barra     contenuto'
      'spalla    spalla'
      'fondo     fondo';
  }
}

/* Desktop: tre colonne */
@media (width >= 72rem) {
  .pagina {
    grid-template-columns: 14rem 1fr 18rem;
    grid-template-rows: auto 1fr auto;
    grid-template-areas:
      'testata   testata     testata'
      'barra     contenuto   spalla'
      'fondo     fondo       fondo';
  }
}
```

```
# Perché le aree nominate invece dei numeri di linea:
#
# 1. Il CSS si legge come un disegno del layout.
# 2. Riorganizzare per il mobile è riscrivere il disegno,
#    non ricalcolare dodici coppie di numeri di linea.
# 3. Aggiungere una zona non rompe le altre: con i numeri
#    di linea, inserire una colonna sposta tutti gli indici.
#
# ATTENZIONE all'ordine visivo contro l'ordine del DOM:
# nella versione mobile la barra sta SOTTO il contenuto,
# ma nel markup viene prima. Il focus da tastiera segue il DOM,
# quindi da mobile Tab passa per la barra prima di arrivare
# al contenuto — cosa che l'utente non si aspetta guardando
# lo schermo. Se questo conta, il salto al contenuto
# (tutorial_01, A6) risolve il problema.
#
# grid-template-rows: auto 1fr auto sul desktop fa sì che
# il contenuto occupi lo spazio avanzato e il piè di pagina
# resti in fondo anche con poco contenuto.
```

---

### Esercizio 3 — Sistema di design token con tema chiaro e scuro

**Obiettivo:** costruire i due livelli di token e un selettore di tema a tre stati che rispetti la preferenza di sistema.

```css
/* SOLUZIONE — src/token.css */

:root {
  /* ══ Livello 1: primitivi ═══════════════════════════════════ */
  --blu-100: oklch(94% 0.03 264);
  --blu-500: oklch(60% 0.18 264);
  --blu-600: oklch(52% 0.19 264);
  --blu-700: oklch(45% 0.18 264);
  --blu-900: oklch(30% 0.12 264);

  --neutro-0: oklch(100% 0 0);
  --neutro-50: oklch(98% 0 0);
  --neutro-200: oklch(90% 0 0);
  --neutro-400: oklch(70% 0 0);
  --neutro-600: oklch(50% 0 0);
  --neutro-800: oklch(28% 0 0);
  --neutro-900: oklch(18% 0 0);
  --neutro-950: oklch(12% 0 0);

  --rosso-600: oklch(55% 0.21 27);
  --verde-600: oklch(58% 0.16 150);
  --ambra-500: oklch(75% 0.16 75);

  /* Spazio: scala su base 0.25rem */
  --spazio-1: 0.25rem;
  --spazio-2: 0.5rem;
  --spazio-3: 0.75rem;
  --spazio-4: 1rem;
  --spazio-6: 1.5rem;
  --spazio-8: 2rem;
  --spazio-12: 3rem;
  --spazio-sezione: clamp(2rem, 1rem + 5vw, 6rem);

  /* Tipografia fluida — il termine in rem garantisce lo zoom */
  --testo-sm: clamp(0.8rem, 0.77rem + 0.15vw, 0.9rem);
  --testo-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --testo-lg: clamp(1.15rem, 1.05rem + 0.5vw, 1.5rem);
  --testo-xl: clamp(1.4rem, 1.2rem + 1vw, 2rem);
  --testo-2xl: clamp(1.75rem, 1.2rem + 2.5vw, 3rem);

  --raggio-sm: 0.25rem;
  --raggio-md: 0.5rem;
  --raggio-lg: 1rem;

  --ombra-sm: 0 1px 2px rgb(0 0 0 / 0.06);
  --ombra-md: 0 4px 12px rgb(0 0 0 / 0.1);

  --transizione: 200ms cubic-bezier(0.4, 0, 0.2, 1);

  /* ══ Livello 2: semantici — TEMA CHIARO ════════════════════ */
  --superficie: var(--neutro-0);
  --superficie-alternata: var(--neutro-50);
  --superficie-elevata: var(--neutro-0);
  --testo-principale: var(--neutro-900);
  --testo-tenue: var(--neutro-600);
  --bordo: var(--neutro-200);

  --azione: var(--blu-700);
  --azione-attiva: var(--blu-900);
  --azione-testo: var(--neutro-0);
  --azione-tenue: var(--blu-100);

  --errore: var(--rosso-600);
  --successo: var(--verde-600);
  --avviso: var(--ambra-500);

  /* Dichiara gli schemi supportati: stila anche i controlli nativi */
  color-scheme: light dark;
}

/* ══ Tema scuro: solo i SEMANTICI cambiano ═══════════════════ */
/* Il :not() fa sì che la preferenza di sistema non prevalga
   su una scelta esplicita dell'utente per il tema chiaro. */
@media (prefers-color-scheme: dark) {
  :root:not([data-tema='chiaro']) {
    --superficie: var(--neutro-950);
    --superficie-alternata: var(--neutro-900);
    --superficie-elevata: var(--neutro-800);
    --testo-principale: var(--neutro-50);
    --testo-tenue: var(--neutro-400);
    --bordo: var(--neutro-800);

    --azione: var(--blu-500);
    --azione-attiva: var(--blu-100);
    --azione-testo: var(--neutro-950);
    --azione-tenue: oklch(30% 0.08 264);

    --ombra-sm: 0 1px 2px rgb(0 0 0 / 0.4);
    --ombra-md: 0 4px 12px rgb(0 0 0 / 0.5);
  }
}

/* ══ Scelta esplicita: vince in entrambe le direzioni ════════ */
:root[data-tema='scuro'] {
  --superficie: var(--neutro-950);
  --superficie-alternata: var(--neutro-900);
  --superficie-elevata: var(--neutro-800);
  --testo-principale: var(--neutro-50);
  --testo-tenue: var(--neutro-400);
  --bordo: var(--neutro-800);
  --azione: var(--blu-500);
  --azione-attiva: var(--blu-100);
  --azione-testo: var(--neutro-950);
  --azione-tenue: oklch(30% 0.08 264);
  --ombra-sm: 0 1px 2px rgb(0 0 0 / 0.4);
  --ombra-md: 0 4px 12px rgb(0 0 0 / 0.5);
  color-scheme: dark;
}

:root[data-tema='chiaro'] {
  color-scheme: light;
}
```

```javascript
// src/tema.js — il selettore a tre stati

const CHIAVE = 'tema-preferito'
const radice = document.documentElement

/**
 * Applica il tema. 'sistema' rimuove l'override e lascia
 * decidere a prefers-color-scheme.
 */
function applicaTema(tema) {
  if (tema === 'sistema') {
    delete radice.dataset.tema
    localStorage.removeItem(CHIAVE)
  } else {
    radice.dataset.tema = tema
    localStorage.setItem(CHIAVE, tema)
  }
  aggiornaControlli(tema)
}

function aggiornaControlli(temaAttivo) {
  for (const comando of document.querySelectorAll('[data-imposta-tema]')) {
    const suo = comando.dataset.impostaTema
    comando.setAttribute('aria-pressed', String(suo === temaAttivo))
  }
}

// Ripristina la scelta salvata al caricamento
const salvato = localStorage.getItem(CHIAVE)
applicaTema(salvato ?? 'sistema')

document.addEventListener('click', (evento) => {
  const comando = evento.target.closest('[data-imposta-tema]')
  if (comando) applicaTema(comando.dataset.impostaTema)
})
```

```html
<!-- Va inserito nel <head>, PRIMA del CSS, per evitare
     il lampo di tema sbagliato al caricamento -->
<script>
  const t = localStorage.getItem('tema-preferito')
  if (t && t !== 'sistema') document.documentElement.dataset.tema = t
</script>
```

```html
<fieldset class="scelta-tema">
  <legend>Aspetto</legend>
  <button type="button" data-imposta-tema="chiaro" aria-pressed="false">Chiaro</button>
  <button type="button" data-imposta-tema="scuro" aria-pressed="false">Scuro</button>
  <button type="button" data-imposta-tema="sistema" aria-pressed="true">Sistema</button>
</fieldset>
```

```
# I punti in cui è facile sbagliare:
#
# 1. Lo script inline nel <head> non è una cattiva pratica qui:
#    senza, la pagina si dipinge con il tema chiaro e poi
#    passa allo scuro. Il lampo bianco è fastidioso di notte.
#
# 2. :root:not([data-tema='chiaro']) dentro la media query.
#    Senza il :not(), l'utente che sceglie esplicitamente
#    il chiaro su un sistema in modalità scura non ottiene nulla:
#    la media query continuerebbe ad applicarsi.
#
# 3. color-scheme non è decorativo: senza, le barre di scorrimento
#    e i controlli nativi dei form restano chiari su fondo scuro.
#
# 4. Le ombre vanno ridefinite: un'ombra nera al 10% è invisibile
#    su fondo scuro. Trasferire i token senza rivederle è
#    l'errore più comune nei temi scuri.
#
# 5. Il contrasto va RIVERIFICATO nel tema scuro. Invertire
#    i colori non conserva i rapporti: --testo-tenue su
#    --superficie va misurato in entrambi i temi.
```

---

### Esercizio 4 — Galleria di schede con container query

**Obiettivo:** una scheda che cambia layout in base allo spazio del suo contenitore, non della finestra — così la stessa scheda funziona nella colonna principale e nella barra laterale.

```html
<div class="disposizione">
  <div class="colonna-principale">
    <div class="involucro-scheda">
      <article class="scheda">
        <img class="scheda__figura" src="/img/prodotto.jpg" alt="Pompa centrifuga serie X"
             width="400" height="300" />
        <div class="scheda__corpo">
          <h3 class="scheda__titolo">Pompa centrifuga serie X</h3>
          <p class="scheda__testo">Portata fino a 120 m³/h, girante in acciaio inox.</p>
          <a class="scheda__azione" href="/prodotti/pompa-x">Scheda tecnica</a>
        </div>
      </article>
    </div>
  </div>

  <aside class="barra-laterale">
    <div class="involucro-scheda">
      <article class="scheda">
        <!-- markup identico -->
      </article>
    </div>
  </aside>
</div>
```

```css
/* SOLUZIONE */

.disposizione {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spazio-6);
}

@media (width >= 60rem) {
  .disposizione {
    grid-template-columns: 1fr 20rem;
  }
}

/* Il CONTENITORE è l'involucro, non la scheda:
   un elemento non può interrogare sé stesso. */
.involucro-scheda {
  container-type: inline-size;
  container-name: scheda;
}

/* Stile di base: verticale. Vale quando il contenitore è stretto. */
.scheda {
  display: flex;
  flex-direction: column;
  gap: var(--spazio-3);
  background: var(--superficie-elevata);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio-md);
  overflow: hidden;
}

.scheda__figura {
  inline-size: 100%;
  block-size: auto;
  aspect-ratio: 4 / 3;
  object-fit: cover;
}

.scheda__corpo {
  display: flex;
  flex-direction: column;
  gap: var(--spazio-2);
  /* min-inline-size: 0 evita che un testo lungo sfondi il contenitore */
  min-inline-size: 0;
  padding: var(--spazio-4);
}

.scheda__titolo {
  margin: 0;
  font-size: var(--testo-lg);
  text-wrap: balance;
}

.scheda__testo {
  margin: 0;
  color: var(--testo-tenue);
  font-size: var(--testo-sm);
}

.scheda__azione {
  margin-block-start: auto;   /* spinge il link in fondo */
  align-self: start;
}

/* Contenitore largo: la scheda diventa orizzontale */
@container scheda (width >= 26rem) {
  .scheda {
    display: grid;
    grid-template-columns: 12rem 1fr;
    align-items: start;
  }

  .scheda__figura {
    block-size: 100%;
    aspect-ratio: 1;
  }

  .scheda__titolo {
    font-size: var(--testo-xl);
  }

  /* Il padding scala con il contenitore, non con la finestra */
  .scheda__corpo {
    padding: 4cqi;
  }
}

/* Contenitore molto largo: aggiunge respiro */
@container scheda (width >= 40rem) {
  .scheda {
    grid-template-columns: 16rem 1fr;
  }

  .scheda__testo {
    font-size: var(--testo-base);
  }
}
```

```
# Cosa dimostra questo esercizio:
#
# La STESSA scheda, lo STESSO markup, senza classi condizionali:
#
#   nella colonna principale (larga)  → layout orizzontale
#   nella barra laterale (stretta)     → layout verticale
#
# Con le media query servirebbero due varianti (.scheda--compatta)
# e chi usa il componente dovrebbe sapere dove lo sta mettendo.
# Con le container query il componente si arrangia da solo:
# è ciò che rende possibile un design system davvero riusabile.
#
# ERRORE TIPICO: mettere container-type sulla .scheda stessa
# e poi interrogarla. Non funziona — il contenitore deve essere
# un ANTENATO di ciò che vuoi stilare.
#
# Le unità cq* (4cqi = 4% della larghezza del contenitore)
# stanno alle container query come vw sta alle media query.
```

---

### Esercizio 5 — Animazioni che girano sul compositor

**Obiettivo:** riscrivere tre animazioni scritte male perché usino solo `transform` e `opacity`, e rispettino `prefers-reduced-motion`.

```css
/* PARTENZA — tutte e tre rifanno il layout a ogni fotogramma */

/* 1. Pannello laterale */
.pannello {
  position: fixed;
  left: -320px;
  transition: left 300ms;
}
.pannello.aperto { left: 0; }

/* 2. Scheda che si ingrandisce al passaggio */
.scheda { transition: width 200ms, height 200ms; }
.scheda:hover { width: 105%; height: 105%; }

/* 3. Comparsa di una notifica */
@keyframes comparsa-sbagliata {
  from { margin-top: -50px; height: 0; }
  to { margin-top: 0; height: 60px; }
}
```

```css
/* SOLUZIONE */

/* ── 1. Pannello laterale ─────────────────────────────────── */
.pannello {
  position: fixed;
  inset-block: 0;
  inset-inline-start: 0;
  inline-size: 20rem;

  /* translateX(-100%) è relativo alla larghezza dell'elemento:
     funziona anche se la larghezza cambia */
  transform: translateX(-100%);
  transition: transform 300ms cubic-bezier(0.4, 0, 0.2, 1);

  /* Nasconde dal focus quando è chiuso: senza, Tab entra
     in un pannello invisibile */
  visibility: hidden;
  transition:
    transform 300ms cubic-bezier(0.4, 0, 0.2, 1),
    visibility 300ms;
}

.pannello.aperto {
  transform: translateX(0);
  visibility: visible;
}

/* ── 2. Scheda che si ingrandisce ─────────────────────────── */
.scheda {
  transition:
    transform 200ms ease-out,
    box-shadow 200ms ease-out;
}

/* Solo dove l'hover esiste davvero: su touch resterebbe appiccicato */
@media (hover: hover) {
  .scheda:hover {
    transform: scale(1.03);
    box-shadow: var(--ombra-md);
  }
}

/* ── 3. Comparsa della notifica ───────────────────────────── */
@keyframes comparsa {
  from {
    opacity: 0;
    transform: translateY(-0.75rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.notifica {
  animation: comparsa 250ms cubic-bezier(0.4, 0, 0.2, 1);
  animation-fill-mode: backwards;   /* applica lo stato 'from' prima dell'avvio */
}

/* ── Rispetto della preferenza di movimento ───────────────── */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  /* Versione raffinata: la dissolvenza resta, il movimento sparisce */
  .notifica {
    animation: none;
    opacity: 1;
  }

  .scheda:hover {
    transform: none;
    box-shadow: var(--ombra-md);   /* il riscontro visivo resta */
  }
}
```

```
# Come verificare che l'animazione giri davvero sul compositor:
#
# 1. DevTools → menu ⋮ → More tools → Rendering
# 2. Spunta "Paint flashing":
#      le aree ridisegnate lampeggiano in verde.
#      Un'animazione sul compositor NON fa lampeggiare nulla.
# 3. Spunta "Layer borders": vedi i livelli promossi.
# 4. Pannello Performance → registra durante l'animazione:
#      · barre viola  = Layout   → stai animando la proprietà sbagliata
#      · barre verdi  = Paint    → migliorabile
#      · nessuna delle due, solo Composite → corretto
#
# Il guadagno non è teorico: un'animazione di 'left' compete
# con il thread principale, quindi scatta ogni volta che
# JavaScript è occupato. transform gira su un thread separato
# e resta fluida anche durante un calcolo pesante.
#
# animation-fill-mode: backwards invece di forwards, qui:
# 'backwards' applica lo stato iniziale già prima che l'animazione
# parta, evitando il lampo dell'elemento in posizione finale
# nel fotogramma precedente all'avvio.
```

---

### Esercizio 6 — Sostituire JavaScript con `:has()`

**Obiettivo:** riscrivere in solo CSS tre comportamenti che di solito richiedono JavaScript.

```javascript
// PARTENZA — tre listener che aggiungono e tolgono classi

// 1. Blocca lo scorrimento quando una modale è aperta
finestra.addEventListener('open', () => document.body.classList.add('bloccato'))
finestra.addEventListener('close', () => document.body.classList.remove('bloccato'))

// 2. Evidenzia il gruppo di un radio selezionato
for (const radio of document.querySelectorAll('input[type=radio]')) {
  radio.addEventListener('change', () => {
    for (const etichetta of document.querySelectorAll('.opzione')) {
      etichetta.classList.toggle('scelta', etichetta.contains(document.activeElement))
    }
  })
}

// 3. Cambia il layout se la barra laterale esiste
if (document.querySelector('.barra-laterale')) {
  document.querySelector('.pagina').classList.add('con-barra')
}
```

```css
/* SOLUZIONE — zero JavaScript */

/* ── 1. Scorrimento bloccato con la modale aperta ─────────── */
body:has(dialog[open]) {
  overflow: hidden;
}

/* Funziona anche con i popover */
body:has([popover]:popover-open) {
  overflow: hidden;
}

/* ── 2. Gruppo evidenziato del radio selezionato ──────────── */
.opzione:has(input[type='radio']:checked) {
  background: var(--azione-tenue);
  border-color: var(--azione);
  font-weight: 600;
}

/* Lo stesso per le checkbox */
.opzione:has(input[type='checkbox']:checked) {
  background: var(--azione-tenue);
}

/* Il focus sul gruppo, non solo sul controllo */
.opzione:has(:focus-visible) {
  outline: 3px solid var(--azione);
  outline-offset: 2px;
}

/* ── 3. Layout condizionato dalla presenza della barra ────── */
.pagina {
  display: grid;
  gap: var(--spazio-6);
}

.pagina:has(> .barra-laterale) {
  grid-template-columns: 14rem 1fr;
}

.pagina:not(:has(> .barra-laterale)) {
  grid-template-columns: 1fr;
  max-inline-size: 60rem;
  margin-inline: auto;
}

/* ── Bonus: pattern che valgono la pena ───────────────────── */

/* Un form con almeno un errore */
form:has(:user-invalid) .riepilogo-errori {
  display: block;
}

/* Etichetta di un campo obbligatorio, senza toccare l'HTML */
.campo:has([required]) > label::after {
  content: ' *';
  color: var(--errore);
}

/* Una figura senza didascalia riceve più margine sotto */
figure:not(:has(figcaption)) {
  margin-block-end: var(--spazio-8);
}

/* Il titolo seguito da un paragrafo si avvicina */
h2:has(+ p) {
  margin-block-end: var(--spazio-1);
}

/* Una tabella con totali: bordo più marcato sopra il tfoot */
table:has(tfoot) tbody tr:last-child > * {
  border-block-end-width: 2px;
}
```

```
# Quanto codice sparisce:
#
#   3 listener, 2 cicli, 4 classi da mantenere sincronizzate
#   → 8 regole CSS dichiarative
#
# Il vantaggio non è la brevità: è che lo stato non può più
# desincronizzarsi. Una classe aggiunta da JavaScript può restare
# appiccicata se un ramo di codice dimentica di rimuoverla;
# :has() riflette sempre lo stato reale del DOM.
#
# SPECIFICITÀ: :has() assume quella del suo argomento più alto.
#   .scheda:has(#tizio)          → (1,1,0)
#   .scheda:has(:where(#tizio))  → (0,1,0)
#
# COSTO: ancoralo a un contenitore ristretto quando puoi.
# body:has(...) costringe a rivalutare a ogni mutazione del DOM;
# è accettabile per la modale (evento raro) e sconsigliato
# dentro una lista con migliaia di righe che cambiano di continuo.
```

---

### Esercizio 7 — Diagnosticare un layout rotto

**Obiettivo:** cinque sintomi frequenti, la causa e la correzione.

```css
/* ── SINTOMO 1 ─────────────────────────────────────────────
   "Una colonna con del codice dentro sfonda il contenitore
    e la pagina scorre in orizzontale." */

/* CAUSA: min-width degli elementi flex vale 'auto', non 0.
   Il contenuto con larghezza minima intrinseca (un <pre>,
   un URL lungo) impedisce alla colonna di restringersi. */

/* ❌ */
.riga { display: flex; }
.riga > .colonna { flex: 1; }

/* ✅ */
.riga > .colonna {
  flex: 1;
  min-inline-size: 0;
}
/* In Grid l'equivalente è minmax(0, 1fr) invece di 1fr */


/* ── SINTOMO 2 ─────────────────────────────────────────────
   "position: sticky non fa niente." */

/* CAUSA A: manca la soglia */
/* ❌ */
.intestazione { position: sticky; }
/* ✅ */
.intestazione { position: sticky; inset-block-start: 0; }

/* CAUSA B: un antenato ha overflow diverso da visible.
   È la causa più comune e la più difficile da trovare,
   perché l'antenato può essere molti livelli sopra. */
/* ❌ */
.contenitore { overflow: hidden; }   /* rompe lo sticky dei discendenti */
/* ✅ */
.contenitore { overflow: clip; }     /* clip NON rompe sticky */

/* CAUSA C: il genitore diretto è alto quanto l'elemento,
   quindi non c'è spazio in cui restare appiccicato. */


/* ── SINTOMO 3 ─────────────────────────────────────────────
   "Il menu a tendina finisce sotto la scheda, anche con
    z-index: 9999." */

/* CAUSA: un antenato crea un contesto di impilamento.
   opacity < 1, transform, filter, will-change lo fanno tutti. */

/* ❌ */
.scheda {
  opacity: 0.99;              /* ← crea un contesto di impilamento */
}
.scheda .menu { z-index: 9999; }   /* confinato dentro .scheda */

/* ✅ opzione A: togliere ciò che crea il contesto */
.scheda { /* niente opacity, niente transform */ }

/* ✅ opzione B: eliminare il problema — il top layer
   sta sopra tutto, senza z-index */
/* <div popover>…</div> oppure <dialog>.showModal() */


/* ── SINTOMO 4 ─────────────────────────────────────────────
   "C'è uno spazio bianco sotto ogni immagine che non riesco
    a togliere." */

/* CAUSA: <img> è inline per default, quindi si appoggia
   alla linea di base del testo, e sotto la linea di base
   resta lo spazio per i discendenti (la coda della 'g'). */

/* ❌ */
.figura img { /* display: inline implicito */ }

/* ✅ */
img, svg, video, canvas {
  display: block;
  max-inline-size: 100%;
  block-size: auto;
}
/* Alternativa: vertical-align: middle sull'immagine */


/* ── SINTOMO 5 ─────────────────────────────────────────────
   "Il margine superiore del primo figlio spinge giù il
    genitore invece di spaziarlo dall'alto." */

/* CAUSA: margin collapsing fra genitore e primo figlio,
   quando il genitore non ha padding, border né crea un BFC. */

/* ❌ */
.scheda { background: white; }
.scheda h2 { margin-block-start: 2rem; }   /* esce dal genitore */

/* ✅ opzione A: creare un contesto di formattazione */
.scheda { display: flow-root; }

/* ✅ opzione B: eliminare il problema alla radice —
   il contenitore governa lo spazio */
.scheda {
  display: flex;
  flex-direction: column;
  gap: var(--spazio-4);
}
.scheda > * { margin-block: 0; }
```

```
# La procedura di diagnosi, in ordine:
#
# 1. DevTools → Elements → seleziona l'elemento
#    · pannello Computed: quale regola sta vincendo, e da dove viene
#    · box model in fondo a Computed: dove finisce lo spazio
#
# 2. Se il layout non è quello che credi:
#    · seleziona il GENITORE e guarda il suo display
#    · in Elements, i badge "grid" e "flex" accanto al tag
#      mostrano le linee della griglia sovrapposte alla pagina
#
# 3. Per lo scorrimento orizzontale indesiderato,
#    da console:
#
#      for (const el of document.querySelectorAll('*')) {
#        if (el.scrollWidth > document.documentElement.clientWidth) {
#          console.log(el)
#        }
#      }
#
# 4. Per i contesti di impilamento, DevTools ha un pannello
#    dedicato: Elements → Layers.
#
# 5. Firefox Developer Edition per Grid e Flexbox:
#    il Grid Inspector disegna le linee con i numeri
#    e il Flexbox Inspector mostra, per ogni elemento,
#    la dimensione base, quanto ha chiesto e quanto ha ottenuto.
```

---

## C2. Mini-progetto: dashboard aziendale responsiva

L'esercizio chiave del modulo: replicare il layout di una dashboard con barra laterale, testata, griglia di schede e piè di pagina, completamente responsiva. Nessun framework, nessuna libreria.

### Cosa deve avere

1. Struttura Grid con aree nominate, che si riorganizza in tre configurazioni.
2. Design token su due livelli, con tema chiaro e scuro.
3. Schede che si adattano con container query, non con media query.
4. Tipografia fluida con `clamp()`.
5. Proprietà logiche ovunque.
6. Animazioni solo su `transform` e `opacity`, con `prefers-reduced-motion`.
7. Barra laterale a scomparsa su mobile, con `<dialog>` invece di CSS artigianale.
8. Cascade layers per tenere separati reset, base, componenti e utility.

### Struttura dei file

```
dashboard/
├── index.html
└── src/
    ├── stile.css          punto d'ingresso: dichiara i layer e importa
    ├── token.css          i design token
    ├── base.css           reset ed elementi
    ├── layout.css         la griglia di pagina
    ├── componenti.css     schede, tabella, pulsanti
    └── utility.css        classi a scopo unico
```

### `src/stile.css`

```css
/* src/stile.css
   L'ordine dei layer è dichiarato UNA VOLTA, qui.
   Da questo momento la specificità dei singoli file non compete
   più fra file diversi: comanda l'ordine. */

@layer reset, base, layout, componenti, utility;

@import url('./token.css') layer(base);
@import url('./base.css') layer(base);
@import url('./layout.css') layer(layout);
@import url('./componenti.css') layer(componenti);
@import url('./utility.css') layer(utility);

@layer reset {
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  * {
    margin: 0;
  }

  html {
    -webkit-text-size-adjust: 100%;
  }

  body {
    min-block-size: 100dvh;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  img,
  picture,
  video,
  canvas,
  svg {
    display: block;
    max-inline-size: 100%;
    block-size: auto;
  }

  input,
  button,
  textarea,
  select {
    font: inherit;
    color: inherit;
  }

  p,
  h1,
  h2,
  h3,
  h4 {
    overflow-wrap: break-word;
  }

  h1,
  h2,
  h3 {
    text-wrap: balance;
    line-height: 1.2;
  }

  p {
    text-wrap: pretty;
  }
}
```

### `src/base.css`

```css
/* src/base.css — elementi, non componenti */

body {
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  font-size: var(--testo-base);
  color: var(--testo-principale);
  background: var(--superficie-alternata);
}

/* :where() → specificità zero: qualunque componente sovrascrive
   senza dover competere */
:where(a) {
  color: var(--azione);
  text-decoration-thickness: 0.08em;
  text-underline-offset: 0.2em;
}

:where(a):hover {
  text-decoration-thickness: 0.15em;
}

/* L'indicatore di focus: sostituito, mai rimosso */
:focus-visible {
  outline: 3px solid var(--azione);
  outline-offset: 2px;
  border-radius: var(--raggio-sm);
}

/* Il salto al contenuto */
.salta-al-contenuto {
  position: absolute;
  inset-inline-start: -9999px;
}

.salta-al-contenuto:focus {
  position: fixed;
  inset-block-start: var(--spazio-2);
  inset-inline-start: var(--spazio-2);
  z-index: var(--strato-notifica);
  padding: var(--spazio-3) var(--spazio-4);
  background: var(--testo-principale);
  color: var(--superficie);
  border-radius: var(--raggio-sm);
}

/* Nasconde visivamente, mantenendo l'accesso alle tecnologie assistive */
.solo-screen-reader {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### `src/token.css`

Riusa il file dell'esercizio 3, con l'aggiunta della scala di impilamento:

```css
/* src/token.css — aggiunta alla soluzione dell'esercizio 3 */

:root {
  /* Scala di impilamento, dichiarata in un posto solo.
     Sostituisce la gara di z-index fra componenti. */
  --strato-base: 0;
  --strato-sovrapposto: 10;
  --strato-barra-fissa: 100;
  --strato-menu: 200;
  --strato-modale: 300;
  --strato-notifica: 400;

  /* Misure del layout */
  --larghezza-barra: 15rem;
  --altezza-testata: 3.5rem;
  --larghezza-contenuto: 80rem;
}
```

### `src/layout.css`

```css
/* src/layout.css — la struttura della pagina */

.dashboard {
  display: grid;
  min-block-size: 100dvh;

  /* Mobile: una colonna. La barra laterale non è nella griglia:
     su mobile è una <dialog>, gestita in componenti.css */
  grid-template-columns: 1fr;
  grid-template-rows: var(--altezza-testata) 1fr auto;
  grid-template-areas:
    'testata'
    'contenuto'
    'fondo';
}

/* Tablet e oltre: la barra laterale entra nella griglia */
@media (width >= 48rem) {
  .dashboard {
    grid-template-columns: var(--larghezza-barra) 1fr;
    grid-template-areas:
      'testata   testata'
      'barra     contenuto'
      'fondo     fondo';
  }
}

.dashboard__testata {
  grid-area: testata;
  position: sticky;
  inset-block-start: 0;
  z-index: var(--strato-barra-fissa);

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spazio-4);

  padding-inline: var(--spazio-4);
  background: var(--superficie);
  border-block-end: 1px solid var(--bordo);
}

.dashboard__barra {
  grid-area: barra;
  padding: var(--spazio-4);
  background: var(--superficie);
  border-inline-end: 1px solid var(--bordo);
}

.dashboard__contenuto {
  grid-area: contenuto;
  container-type: inline-size;
  container-name: contenuto;

  inline-size: 100%;
  max-inline-size: var(--larghezza-contenuto);
  margin-inline: auto;
  padding: var(--spazio-6) var(--spazio-4);
}

.dashboard__fondo {
  grid-area: fondo;
  padding: var(--spazio-4);
  border-block-start: 1px solid var(--bordo);
  color: var(--testo-tenue);
  font-size: var(--testo-sm);
}

/* Impilamento verticale con spaziatura uniforme.
   Sostituisce i margini e il margin collapsing. */
.pila {
  display: flex;
  flex-direction: column;
  gap: var(--gap-pila, var(--spazio-6));
}

/* Griglia di schede che si adatta da sola: nessuna media query */
.griglia-schede {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(18rem, 100%), 1fr));
  gap: var(--spazio-4);
}

/* min(18rem, 100%) evita l'overflow quando il contenitore
   è più stretto di 18rem: senza, la colonna sfonda su schermi molto piccoli */
```

### `src/componenti.css`

```css
/* src/componenti.css */

/* ── Scheda statistica ──────────────────────────────────────── */

.involucro-scheda {
  container-type: inline-size;
  container-name: scheda;
}

.scheda {
  display: flex;
  flex-direction: column;
  gap: var(--spazio-2);

  padding: var(--spazio-4);
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio-md);
  box-shadow: var(--ombra-sm);

  transition:
    transform var(--transizione),
    box-shadow var(--transizione);
}

@media (hover: hover) {
  .scheda:hover {
    transform: translateY(-2px);
    box-shadow: var(--ombra-md);
  }
}

.scheda__etichetta {
  color: var(--testo-tenue);
  font-size: var(--testo-sm);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.scheda__valore {
  font-size: var(--testo-2xl);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.scheda__variazione {
  display: inline-flex;
  align-items: center;
  gap: var(--spazio-1);
  font-size: var(--testo-sm);
  font-weight: 600;
}

.scheda__variazione[data-segno='positivo'] { color: var(--successo); }
.scheda__variazione[data-segno='negativo'] { color: var(--errore); }

/* Scheda larga: valore ed etichetta si affiancano */
@container scheda (width >= 22rem) {
  .scheda {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: var(--spazio-1) var(--spazio-4);
  }

  .scheda__valore {
    grid-column: 2;
    grid-row: 1 / 3;
    font-size: clamp(var(--testo-2xl), 10cqi, 3rem);
  }
}

/* ── Pulsanti ───────────────────────────────────────────────── */

.pulsante {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spazio-2);

  /* WCAG 2.5.8: bersaglio di almeno 24×24 CSS px.
     44px è la raccomandazione operativa per il tocco. */
  min-block-size: 2.75rem;
  padding-inline: var(--spazio-4);

  color: var(--azione-testo);
  background: var(--azione);
  border: 1px solid transparent;
  border-radius: var(--raggio-sm);
  cursor: pointer;

  transition:
    background var(--transizione),
    transform 100ms;
}

.pulsante:hover {
  background: var(--azione-attiva);
}

.pulsante:active {
  transform: translateY(1px);
}

.pulsante:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.pulsante--secondario {
  color: var(--azione);
  background: transparent;
  border-color: var(--bordo);
}

.pulsante--secondario:hover {
  background: var(--azione-tenue);
}

/* ── Tabella ────────────────────────────────────────────────── */

.involucro-tabella {
  overflow-x: auto;
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio-md);
}

.tabella {
  inline-size: 100%;
  border-collapse: collapse;
}

.tabella caption {
  padding: var(--spazio-4);
  text-align: start;
  font-weight: 600;
}

.tabella :is(th, td) {
  padding: var(--spazio-3) var(--spazio-4);
  border-block-end: 1px solid var(--bordo);
  text-align: start;
}

.tabella thead th {
  position: sticky;
  inset-block-start: 0;
  background: var(--superficie-alternata);
  font-size: var(--testo-sm);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* I numeri a destra, incolonnati */
.tabella :is(th, td).numerico {
  text-align: end;
  font-variant-numeric: tabular-nums;
}

.tabella tbody tr:last-child :is(th, td) {
  border-block-end: none;
}

@media (hover: hover) {
  .tabella tbody tr:hover {
    background: var(--superficie-alternata);
  }
}

/* ── Barra laterale mobile ──────────────────────────────────── */

/* Su mobile la barra è una <dialog>: il top layer, il confinamento
   del focus, Esc e lo sfondo inerte sono gestiti dal browser. */
.barra-mobile {
  margin: 0;
  margin-inline-end: auto;    /* ancorata al bordo iniziale */
  block-size: 100dvh;
  max-block-size: 100dvh;
  inline-size: min(20rem, 85vw);
  padding: var(--spazio-4);

  background: var(--superficie);
  border: none;
  border-inline-end: 1px solid var(--bordo);
}

.barra-mobile::backdrop {
  background: rgb(0 0 0 / 0.5);
}

/* Animazione di ingresso: @starting-style dichiara lo stato
   "prima che l'elemento esista", rendendo animabile la comparsa. */
.barra-mobile {
  transform: translateX(0);
  opacity: 1;
  transition:
    transform 250ms cubic-bezier(0.4, 0, 0.2, 1),
    opacity 250ms,
    overlay 250ms allow-discrete,
    display 250ms allow-discrete;
}

@starting-style {
  .barra-mobile[open] {
    transform: translateX(-100%);
    opacity: 0;
  }
}

.barra-mobile:not([open]) {
  transform: translateX(-100%);
  opacity: 0;
}

/* Sopra il tablet la barra è nella griglia: il comando sparisce */
@media (width >= 48rem) {
  .comando-barra {
    display: none;
  }
}

/* ── Navigazione ────────────────────────────────────────────── */

.navigazione ul {
  display: flex;
  flex-direction: column;
  gap: var(--spazio-1);
  padding: 0;
  list-style: none;
}

.navigazione a {
  display: block;
  padding: var(--spazio-2) var(--spazio-3);
  border-radius: var(--raggio-sm);
  color: var(--testo-principale);
  text-decoration: none;
}

.navigazione a:hover {
  background: var(--superficie-alternata);
}

.navigazione a[aria-current='page'] {
  background: var(--azione-tenue);
  color: var(--azione);
  font-weight: 600;
}

/* Blocca lo scorrimento del corpo con la barra aperta: :has() al posto
   di due listener JavaScript */
body:has(.barra-mobile[open]) {
  overflow: hidden;
}
```

### `src/utility.css`

```css
/* src/utility.css — classi a scopo unico.
   Stanno nel layer più alto, quindi vincono sui componenti
   senza bisogno di !important. */

.pila-stretta { --gap-pila: var(--spazio-3); }
.pila-larga { --gap-pila: var(--spazio-12); }

.testo-tenue { color: var(--testo-tenue); }
.testo-piccolo { font-size: var(--testo-sm); }
.testo-centrato { text-align: center; }

.nessun-margine { margin: 0; }
.riempi { flex: 1; }

.misura-lettura { max-inline-size: 65ch; }
```

### `index.html`

```html
<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Dashboard — Acme S.p.A.</title>
    <meta name="color-scheme" content="light dark" />

    <!-- Prima del CSS: evita il lampo di tema sbagliato -->
    <script>
      const t = localStorage.getItem('tema-preferito')
      if (t && t !== 'sistema') document.documentElement.dataset.tema = t
    </script>

    <link rel="stylesheet" href="/src/stile.css" />
  </head>

  <body>
    <a href="#contenuto" class="salta-al-contenuto">Vai al contenuto principale</a>

    <div class="dashboard">
      <header class="dashboard__testata">
        <button
          type="button"
          class="pulsante pulsante--secondario comando-barra"
          popovertarget="barra-mobile"
        >
          <span aria-hidden="true">☰</span>
          <span class="solo-screen-reader">Apri il menu di navigazione</span>
        </button>

        <strong>Acme S.p.A.</strong>

        <fieldset class="scelta-tema">
          <legend class="solo-screen-reader">Aspetto</legend>
          <button type="button" class="pulsante pulsante--secondario"
                  data-imposta-tema="chiaro" aria-pressed="false">Chiaro</button>
          <button type="button" class="pulsante pulsante--secondario"
                  data-imposta-tema="scuro" aria-pressed="false">Scuro</button>
          <button type="button" class="pulsante pulsante--secondario"
                  data-imposta-tema="sistema" aria-pressed="true">Sistema</button>
        </fieldset>
      </header>

      <!-- Barra laterale: nella griglia da 48rem in su -->
      <nav class="dashboard__barra navigazione" aria-label="Principale">
        <ul>
          <li><a href="/" aria-current="page">Panoramica</a></li>
          <li><a href="/fatture">Fatture</a></li>
          <li><a href="/clienti">Clienti</a></li>
          <li><a href="/report">Report</a></li>
        </ul>
      </nav>

      <main class="dashboard__contenuto pila" id="contenuto" tabindex="-1">
        <h1>Panoramica</h1>

        <section class="pila pila-stretta" aria-labelledby="titolo-indicatori">
          <h2 id="titolo-indicatori">Indicatori del trimestre</h2>

          <div class="griglia-schede">
            <div class="involucro-scheda">
              <article class="scheda">
                <p class="scheda__etichetta">Ricavi</p>
                <p class="scheda__valore">1.330</p>
                <p class="scheda__variazione" data-segno="positivo">
                  <span aria-hidden="true">▲</span> 12,4%
                  <span class="solo-screen-reader">in aumento rispetto al trimestre precedente</span>
                </p>
              </article>
            </div>

            <div class="involucro-scheda">
              <article class="scheda">
                <p class="scheda__etichetta">Fatture emesse</p>
                <p class="scheda__valore">248</p>
                <p class="scheda__variazione" data-segno="positivo">
                  <span aria-hidden="true">▲</span> 3,1%
                  <span class="solo-screen-reader">in aumento</span>
                </p>
              </article>
            </div>

            <div class="involucro-scheda">
              <article class="scheda">
                <p class="scheda__etichetta">Insoluti</p>
                <p class="scheda__valore">17</p>
                <p class="scheda__variazione" data-segno="negativo">
                  <span aria-hidden="true">▼</span> 8,2%
                  <span class="solo-screen-reader">in diminuzione</span>
                </p>
              </article>
            </div>
          </div>
        </section>

        <section class="pila pila-stretta" aria-labelledby="titolo-tabella">
          <h2 id="titolo-tabella">Ricavi per divisione</h2>

          <div class="involucro-tabella" role="region"
               aria-labelledby="titolo-tabella" tabindex="0">
            <table class="tabella">
              <caption>Esercizio 2026, in migliaia di euro</caption>
              <thead>
                <tr>
                  <th scope="col">Divisione</th>
                  <th scope="col" class="numerico">T1</th>
                  <th scope="col" class="numerico">T2</th>
                  <th scope="col" class="numerico">T3</th>
                  <th scope="col" class="numerico">Totale</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th scope="row">Industriale</th>
                  <td class="numerico">610</td>
                  <td class="numerico">630</td>
                  <td class="numerico">780</td>
                  <td class="numerico">2.020</td>
                </tr>
                <tr>
                  <th scope="row">Servizi</th>
                  <td class="numerico">420</td>
                  <td class="numerico">440</td>
                  <td class="numerico">550</td>
                  <td class="numerico">1.410</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </main>

      <footer class="dashboard__fondo">
        <p class="nessun-margine">© 2026 Acme S.p.A. — dati aggiornati al 28 aprile 2026</p>
      </footer>
    </div>

    <!-- Barra laterale mobile: popover, quindi top layer ed Esc gratis -->
    <div id="barra-mobile" popover class="barra-mobile">
      <nav class="navigazione" aria-label="Principale (mobile)">
        <ul>
          <li><a href="/" aria-current="page">Panoramica</a></li>
          <li><a href="/fatture">Fatture</a></li>
          <li><a href="/clienti">Clienti</a></li>
          <li><a href="/report">Report</a></li>
        </ul>
      </nav>
    </div>

    <script type="module" src="/src/tema.js"></script>
  </body>
</html>
```

### Verifica

```powershell
pnpm dev
```

```
# I controlli, in ordine:
#
# 1. TRE CONFIGURAZIONI DI LAYOUT
#    Restringi la finestra lentamente e verifica i due punti
#    di rottura: 48rem (la barra entra nella griglia) e
#    il punto in cui la griglia di schede passa da 3 a 2 a 1 colonna
#    — che NON è una media query: lo fa auto-fit da solo.
#
# 2. CONTAINER QUERY
#    Con DevTools, restringi solo .dashboard__contenuto
#    (non la finestra): le schede devono cambiare layout
#    anche a finestra invariata.
#
# 3. TEMA
#    · Cambia il tema di sistema: la pagina segue.
#    · Scegli "Chiaro" e rimetti il sistema su scuro:
#      la scelta esplicita deve vincere.
#    · Ricarica: la scelta persiste, senza lampo iniziale.
#
# 4. ZOOM
#    Ctrl e + fino al 200%: nessuno scorrimento orizzontale,
#    nessuna sovrapposizione, la tabella scorre nel suo contenitore.
#
# 5. TASTIERA
#    Tab dall'inizio: prima il salto al contenuto, poi il comando
#    del menu, poi la testata. Con la barra mobile aperta,
#    Tab resta confinato dentro e Esc la chiude.
#
# 6. MOVIMENTO RIDOTTO
#    Windows: Impostazioni → Accessibilità → Effetti visivi
#             → Effetti di animazione OFF
#    DevTools: ⋮ → More tools → Rendering → Emulate CSS
#              prefers-reduced-motion: reduce
#    Le transizioni devono sparire, il riscontro visivo restare.
#
# 7. COMPOSITOR
#    DevTools → Rendering → Paint flashing.
#    Passa il puntatore su una scheda: NON deve lampeggiare verde.
#    Se lampeggia, stai animando una proprietà che richiede paint.
#
# 8. CONTRASTO
#    DevTools → Elements → passa il puntatore su un colore:
#    compare il rapporto. Verifica --testo-tenue su --superficie
#    in ENTRAMBI i temi: deve essere almeno 4.5:1.
```

---

# Parte D — Approfondimento per Esperti

---

## D1. `@property`: custom properties tipizzate e animabili

Una custom property normale è una stringa. Il browser non sa cosa contenga, quindi non può interpolarla: animare `--angolo` da `0deg` a `360deg` produce uno scatto, non una rotazione.

```css
/* ❌ Non si anima: il browser non sa che --progresso è una percentuale */
.barra {
  --progresso: 0%;
  transition: --progresso 1s;
}
```

`@property` dichiara il tipo, e con il tipo arriva l'interpolazione.

```css
@property --progresso {
  syntax: '<percentage>';
  inherits: false;
  initial-value: 0%;
}

@property --angolo {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}

@property --colore-bordo {
  syntax: '<color>';
  inherits: true;
  initial-value: transparent;
}
```

Tutti e tre i descrittori sono obbligatori: `syntax`, `inherits`, `initial-value` (tranne che per `syntax: '*'`).

### Il caso d'uso: un indicatore circolare animato

```css
@property --percentuale {
  syntax: '<percentage>';
  inherits: false;
  initial-value: 0%;
}

.indicatore {
  --percentuale: 0%;

  inline-size: 8rem;
  aspect-ratio: 1;
  border-radius: 50%;

  background: conic-gradient(
    var(--azione) var(--percentuale),
    var(--bordo) var(--percentuale)
  );

  /* Ora si anima davvero, perché il tipo è dichiarato */
  transition: --percentuale 800ms cubic-bezier(0.4, 0, 0.2, 1);
}

.indicatore[data-valore='62'] {
  --percentuale: 62%;
}
```

### Sintassi disponibili

```
<length>        <percentage>    <length-percentage>
<number>        <integer>       <angle>
<time>          <color>         <image>
<url>           <resolution>    <transform-function>
<custom-ident>

Combinazioni:
  '<length> | <percentage>'      uno dei due
  '<length>+'                    uno o più, separati da spazio
  '<color>#'                     uno o più, separati da virgola
  'auto | <length>'              parole chiave e tipi insieme
  '*'                            qualunque cosa (nessuna interpolazione)
```

### Registrare da JavaScript

```javascript
// Equivalente a @property, utile quando il tipo dipende dal contesto
CSS.registerProperty({
  name: '--percentuale',
  syntax: '<percentage>',
  inherits: false,
  initialValue: '0%',
})
```

### Validazione e valore di ripiego

Una proprietà registrata rifiuta i valori del tipo sbagliato e torna al valore iniziale, invece di propagare un valore invalido:

```css
@property --spaziatura {
  syntax: '<length>';
  inherits: false;
  initial-value: 1rem;
}

.componente {
  --spaziatura: 24px;      /* accettato */
  --spaziatura: rosso;     /* rifiutato → torna a 1rem */
  padding: var(--spaziatura);
}
```

Senza `@property`, `--spaziatura: rosso` verrebbe accettata come stringa e produrrebbe `padding: rosso`, che rende la dichiarazione invalida al momento del calcolo. È il fenomeno noto come *invalid at computed-value time*, che rende difficile capire da dove venga il problema.

---

## D2. Scroll-driven animations

Legano l'avanzamento di un'animazione allo scorrimento, invece che al tempo. Girano sul compositor, quindi non richiedono un listener `scroll` sul thread principale.

### `scroll()` — la barra di avanzamento della lettura

```css
@keyframes avanzamento {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}

.barra-lettura {
  position: fixed;
  inset-block-start: 0;
  inset-inline: 0;
  block-size: 4px;
  background: var(--azione);
  transform-origin: left center;

  animation: avanzamento linear;
  /* Lega l'animazione allo scorrimento della radice, asse di blocco */
  animation-timeline: scroll(root block);
}
```

Nessun JavaScript, nessun `requestAnimationFrame`, nessun listener. L'equivalente in JavaScript richiederebbe un listener `scroll` con throttling e una lettura di `scrollHeight` a ogni fotogramma.

### `view()` — l'elemento entra nella vista

```css
@keyframes entra {
  from {
    opacity: 0;
    transform: translateY(2rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.scheda {
  animation: entra linear both;
  /* L'avanzamento va da quando l'elemento entra nella vista
     a quando la attraversa */
  animation-timeline: view();
  /* Copre solo il primo tratto: l'animazione finisce
     quando l'elemento è entrato per il 40% */
  animation-range: entry 0% cover 40%;
}
```

```
I nomi degli intervalli:

  cover     dal primo pixel visibile all'ultimo
  contain   da quando l'elemento è interamente visibile
            a quando comincia a uscire
  entry     la fase di ingresso
  exit      la fase di uscita
  entry-crossing / exit-crossing   il passaggio del bordo
```

### Timeline nominate

Quando lo scorrimento e l'elemento animato non sono nella stessa catena di antenati:

```css
.contenitore-scorrevole {
  overflow-y: scroll;
  scroll-timeline-name: --scorrimento-pannello;
  scroll-timeline-axis: block;
}

.indicatore {
  animation: avanzamento linear;
  animation-timeline: --scorrimento-pannello;
}

/* Se l'indicatore non è discendente del contenitore,
   serve dichiarare l'ambito su un antenato comune */
.pagina {
  timeline-scope: --scorrimento-pannello;
}
```

### Supporto e degradazione

Le scroll-driven animations sono in Chromium dal 2023; Firefox e Safari le hanno implementate più di recente. La degradazione è naturale: dove `animation-timeline` non è riconosciuto, l'animazione parte a tempo o non parte affatto.

```css
/* Applica l'animazione solo dove la timeline esiste */
@supports (animation-timeline: scroll()) {
  .scheda {
    animation: entra linear both;
    animation-timeline: view();
    animation-range: entry 0% cover 40%;
  }
}

/* E rispetta comunque la preferenza di movimento */
@media (prefers-reduced-motion: reduce) {
  .scheda {
    animation: none;
    opacity: 1;
    transform: none;
  }
}
```

---

## D3. Anchor positioning e `@starting-style`

### Anchor positioning

Posizionare un tooltip o un menu accanto al suo comando ha sempre richiesto JavaScript: leggere `getBoundingClientRect()`, calcolare, riposizionare a ogni scorrimento. L'anchor positioning lo porta nel CSS.

```css
.comando {
  anchor-name: --comando-notifiche;
}

.pannello {
  position: fixed;
  position-anchor: --comando-notifiche;

  /* Il bordo superiore del pannello va sul bordo inferiore dell'ancora */
  inset-block-start: anchor(bottom);
  inset-inline-start: anchor(start);
  margin-block-start: var(--spazio-2);

  /* Oppure, in forma dichiarativa */
  position-area: block-end span-inline-end;
}
```

`position-try` gestisce il caso in cui non ci sia spazio:

```css
.pannello {
  position-anchor: --comando-notifiche;
  position-area: block-end;

  /* Se non ci sta sotto, prova sopra; se nemmeno lì, a fianco */
  position-try-fallbacks: flip-block, flip-inline, --a-lato;
}

@position-try --a-lato {
  position-area: inline-end;
  margin-inline-start: var(--spazio-2);
}
```

Il supporto è arrivato prima in Chromium; negli altri browser è in corso di implementazione. Fino ad allora serve un ripiego:

```css
@supports not (anchor-name: --x) {
  .pannello {
    /* Centrato, che è il comportamento predefinito di un popover */
    position: fixed;
    inset: auto;
    margin: auto;
  }
}
```

### `@starting-style`

Il problema: un elemento che passa da `display: none` a visibile non ha uno stato "prima" da cui interpolare, quindi la transizione di ingresso non parte. È il motivo per cui le animazioni di comparsa hanno sempre richiesto una classe aggiunta dopo un `requestAnimationFrame`.

```css
.notifica {
  opacity: 1;
  transform: translateY(0);

  transition:
    opacity 300ms,
    transform 300ms,
    display 300ms allow-discrete,
    overlay 300ms allow-discrete;
}

/* Lo stato DA CUI partire la prima volta che l'elemento
   viene disegnato */
@starting-style {
  .notifica {
    opacity: 0;
    transform: translateY(-1rem);
  }
}

/* Lo stato di uscita */
.notifica[hidden] {
  opacity: 0;
  transform: translateY(-1rem);
  display: none;
}
```

Le tre parti che devono esserci tutte:

```
@starting-style              lo stato iniziale, prima del primo fotogramma
display … allow-discrete     rende animabile il passaggio a display:none
overlay … allow-discrete     mantiene l'elemento nel top layer durante
                             l'uscita (per <dialog> e popover)
```

Senza `overlay ... allow-discrete`, una `<dialog>` chiusa sparisce istantaneamente dal top layer e l'animazione di uscita non si vede.

```css
/* Applicato a una <dialog>, l'insieme completo */
dialog {
  opacity: 1;
  transform: scale(1);
  transition:
    opacity 200ms,
    transform 200ms,
    display 200ms allow-discrete,
    overlay 200ms allow-discrete;
}

dialog:not([open]) {
  opacity: 0;
  transform: scale(0.95);
}

@starting-style {
  dialog[open] {
    opacity: 0;
    transform: scale(0.95);
  }
}

dialog::backdrop {
  background: rgb(0 0 0 / 0);
  transition:
    background 200ms,
    display 200ms allow-discrete,
    overlay 200ms allow-discrete;
}

dialog[open]::backdrop {
  background: rgb(0 0 0 / 0.5);
}

@starting-style {
  dialog[open]::backdrop {
    background: rgb(0 0 0 / 0);
  }
}
```

---

## D4. View Transitions

Animano il passaggio fra due stati del DOM: il browser cattura uno snapshot prima e uno dopo, e interpola.

### Nella stessa pagina

```javascript
// La chiamata avvolge la modifica del DOM
if (document.startViewTransition) {
  document.startViewTransition(() => {
    aggiornaElenco()
  })
} else {
  aggiornaElenco()
}
```

```css
/* Gli pseudo-elementi generati dal browser */
::view-transition-old(root) {
  animation: dissolvi-via 200ms ease-out;
}

::view-transition-new(root) {
  animation: dissolvi-verso 200ms ease-in;
}

@keyframes dissolvi-via {
  to { opacity: 0; }
}

@keyframes dissolvi-verso {
  from { opacity: 0; }
}
```

### Elementi che si spostano fra i due stati

```css
/* Un nome univoco fa sì che il browser tratti l'elemento
   come lo STESSO fra prima e dopo, animando la sua posizione */
.scheda-prodotto {
  view-transition-name: var(--nome-transizione);
}
```

```html
<!-- Il nome deve essere unico nella pagina: due elementi
     con lo stesso view-transition-name annullano la transizione -->
<article class="scheda-prodotto" style="--nome-transizione: prodotto-17">…</article>
```

```javascript
// Assegnare il nome solo all'elemento coinvolto, e toglierlo dopo:
// mantenerlo su tutti gli elementi di una lista lunga costa
async function apriDettaglio(scheda, id) {
  scheda.style.viewTransitionName = 'elemento-attivo'

  const transizione = document.startViewTransition(() => {
    mostraDettaglio(id)
  })

  await transizione.finished
  scheda.style.viewTransitionName = ''
}
```

### Fra pagine diverse

```css
/* Nel CSS di ENTRAMBE le pagine, che devono essere sulla stessa origine */
@view-transition {
  navigation: auto;
}
```

Da questo momento la navigazione fra pagine dello stesso sito produce una transizione, senza single-page application e senza router. È la funzionalità che riduce il divario di percezione fra siti tradizionali e SPA.

### Rispettare la preferenza di movimento

```css
@media (prefers-reduced-motion: reduce) {
  ::view-transition-group(*),
  ::view-transition-old(*),
  ::view-transition-new(*) {
    animation: none !important;
  }
}
```

```javascript
// Oppure saltare del tutto la transizione
const movimentoRidotto = window.matchMedia('(prefers-reduced-motion: reduce)').matches

if (document.startViewTransition && !movimentoRidotto) {
  document.startViewTransition(() => aggiornaElenco())
} else {
  aggiornaElenco()
}
```

Le View Transitions per la stessa pagina sono in Chromium dal 2023 e sono state adottate dagli altri browser; quelle fra documenti sono più recenti. `document.startViewTransition` va sempre verificata prima dell'uso, e il ripiego è semplicemente eseguire la modifica senza animazione.

---

## D5. Performance del rendering: `content-visibility`, `will-change`, contenimento

### `content-visibility`

Dice al browser di saltare del tutto il rendering di ciò che non è visibile.

```css
.sezione-lunga {
  content-visibility: auto;
  /* Dimensione stimata: senza, la barra di scorrimento
     salta mentre l'utente scorre, perché il browser scopre
     via via l'altezza reale */
  contain-intrinsic-size: auto 40rem;
}
```

Su una pagina con molte sezioni pesanti il guadagno sul primo rendering è sostanziale: il browser calcola layout e paint solo per ciò che è nella vista o vicino.

```
Attenzione:

  · Il contenuto saltato NON è trovabile con Ctrl+F nei browser
    che non implementano il rendering per la ricerca. Verificare.
  · contain-intrinsic-size va stimato: un valore molto lontano
    dal reale produce salti della barra di scorrimento.
  · Non usarlo su ciò che sta sopra la piega: non c'è nulla
    da risparmiare e si aggiunge lavoro.
```

### `contain`

Dichiara che un sottoalbero non influenza il resto della pagina, permettendo al browser di limitare il ricalcolo.

```css
.componente-isolato {
  /* layout: il layout interno non influenza l'esterno
     paint: il contenuto non esce dai confini
     style: i contatori e le quote non escono
     size: la dimensione non dipende dal contenuto */
  contain: layout paint;

  /* Abbreviazioni */
  contain: content;   /* = layout paint style */
  contain: strict;    /* = layout paint style size */
}
```

`container-type: inline-size` applica implicitamente `contain: layout inline-size`: è il motivo per cui dichiarare un contenitore ha un effetto sul layout, e va verificato.

### `will-change`, di nuovo e con il costo

```css
/* Ogni will-change promuove l'elemento a un livello del compositor.
   Un livello costa memoria video: su mobile la quota è limitata,
   e superarla degrada le prestazioni invece di migliorarle. */

/* ❌ */
.scheda { will-change: transform; }   /* su cinquanta schede = cinquanta livelli */

/* ✅ — solo poco prima dell'animazione */
.scheda:hover { will-change: transform; }
```

```javascript
// Il ciclo esplicito, quando l'animazione è comandata da JavaScript
function animaPannello(pannello) {
  pannello.style.willChange = 'transform'

  requestAnimationFrame(() => {
    pannello.classList.add('aperto')
  })

  pannello.addEventListener(
    'transitionend',
    () => {
      pannello.style.willChange = 'auto'
    },
    { once: true },
  )
}
```

### Misurare invece di indovinare

```
DevTools → Performance → registra un'interazione

  Barre da leggere:
    viola   Layout (Recalculate Style, Layout)
    verde   Paint (Paint, Composite Layers)
    giallo  Scripting

  Un'animazione corretta produce solo Composite,
  senza Layout né Paint per fotogramma.

DevTools → Rendering:
    Paint flashing        lampeggia ciò che viene ridipinto
    Layer borders         mostra i livelli del compositor
    Frame rendering stats fotogrammi al secondo in tempo reale

DevTools → Layers:
    l'elenco dei livelli con il loro consumo di memoria,
    e il motivo per cui ciascuno è stato promosso
```

Il criterio operativo: non ottimizzare prima di aver misurato. `will-change`, `contain` e `content-visibility` hanno tutti un costo, e applicati a caso peggiorano le prestazioni.

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
CSS MODERNO — Mappa dei concetti

SELEZIONE E CASCATA
├── Specificità (A,B,C) — id, classi, elementi
│   └── SENZA RIPORTO: 11 classi (0,11,0) perdono contro 1 id (1,0,0)
├── :is()    assume la specificità dell'argomento più alto
├── :where() vale SEMPRE zero → per stili di base sovrascrivibili
├── :has()   il selettore del genitore: guarda dentro e di lato
├── Ordine di valutazione della cascata:
│     origine → @layer → specificità → ordine di apparizione
├── @layer   sostituisce la gara di specificità con un ordine dichiarato
│     └── fuori dai layer > dentro i layer
├── @scope   confine superiore E inferiore, con regola di prossimità
└── !important sposta il problema, non lo risolve

BOX MODEL
├── content → padding → border → margin
├── box-sizing: border-box  ← prima regola di ogni foglio di stile
├── Margin collapsing: verticali adiacenti NON si sommano
│     └── display: flow-root | flex | grid lo impedisce
│     └── gap lo elimina alla radice
└── Contesto di formattazione a blocco: flow-root, non overflow: hidden

UNITÀ
├── rem  testo e spazi — scala con la preferenza dell'utente
├── px   bordi e dettagli che non devono crescere
├── em   spaziature interne a un componente (si compone!)
├── ch   misura di lettura: 60-75ch
├── fr   ripartizione dello spazio in Grid
├── dvh  invece di vh su mobile (la barra del browser)
└── cqi  proporzionale al CONTENITORE, non alla finestra

LAYOUT
├── Flexbox — un asse
│   ├── flex: 1     tutti uguali (basis 0)
│   ├── flex: auto  proporzionali al contenuto
│   └── min-inline-size: 0  ← contro l'overflow del contenuto lungo
├── Grid — due assi
│   ├── grid-template-areas: il layout si legge come un disegno
│   ├── repeat(auto-fit, minmax(16rem, 1fr))  responsivo senza media query
│   ├── auto-fit collassa le tracce vuote, auto-fill le tiene
│   ├── minmax(0, 1fr) invece di 1fr, per lo stesso motivo di min-width
│   └── subgrid: allinea il contenuto fra schede diverse
├── position
│   ├── sticky richiede una soglia E nessun overflow negli antenati
│   └── z-index vive dentro il contesto di impilamento
│         opacity<1, transform, filter ne creano uno
│         top layer (dialog, popover) sta sopra tutto senza z-index
└── Proprietà logiche: inline/block invece di left/right/top/bottom

ADATTAMENTO
├── Media query — la FINESTRA
│   ├── in rem, non px (segue lo zoom dell'utente)
│   ├── breakpoint scelti dal contenuto, non dai dispositivi
│   └── mobile-first: il caso base è il più semplice
├── Container query — il CONTENITORE
│   ├── container-type sul GENITORE: nessuno interroga sé stesso
│   └── lo stesso componente si adatta a dove viene messo
├── clamp(min, preferito, max)
│   └── il termine centrale DEVE contenere rem, o si rompe lo zoom
└── prefers-reduced-motion · prefers-color-scheme · hover: hover

ARCHITETTURA
├── Custom properties: runtime, ereditate, leggibili da JavaScript
├── Design token su due livelli
│     primitivi (--blu-700)  →  semantici (--azione)
│     i componenti usano SOLO i semantici
│     cambiare tema = ridefinire i semantici
└── @property: tipizzate, validate, ANIMABILI

COLORE
├── oklch: luminosità percettivamente uniforme
├── color-mix(in oklch, …): stati derivati senza nuovi token
└── Contrasto WCAG 4.5:1 — da riverificare nel tema scuro

MOVIMENTO
├── Il rendering: Layout → Paint → Composite
│     ✅ transform, opacity, filter  → solo Composite
│     ❌ width, height, top, left    → tutte e tre, ogni fotogramma
├── transition: all → dichiara cosa animare
├── will-change: solo poco prima, e rimosso dopo
├── @starting-style: rende animabile la comparsa
│     serve anche display+overlay allow-discrete
├── Scroll-driven animations: sul compositor, zero JavaScript
└── View Transitions: interpolano fra due stati del DOM
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Calcoli la specificità di un selettore e prevedi quale regola vince
- [ ] Sai perché cento classi non battono un id
- [ ] Distingui cascata ed ereditarietà, e sai quali proprietà si ereditano
- [ ] Sai perché `box-sizing: border-box` è la prima regola di ogni progetto
- [ ] Scegli fra `rem`, `px`, `em`, `ch` e `fr` con un criterio
- [ ] Sai perché `100vh` taglia il contenuto su mobile e cosa usare
- [ ] Distingui `block`, `inline` e `inline-block` e sai cosa ignora `inline`
- [ ] Conosci le quattro tecniche per nascondere e cosa cambia per l'accessibilità
- [ ] Costruisci una barra di navigazione e un layout centrato con Flexbox
- [ ] Distingui `justify-content` da `align-items` e sai che si scambiano con `column`
- [ ] Costruisci un layout di pagina con `grid-template-areas`
- [ ] Sai quando serve Flexbox e quando Grid

**Parte B — Comprensione**

- [ ] Sai cos'è il margin collapsing e le tre situazioni in cui avviene
- [ ] Sai perché `display: flow-root` è meglio di `overflow: hidden`
- [ ] Sai elencare le tre cause per cui `position: sticky` non funziona
- [ ] Sai perché `z-index: 9999` non basta, e cosa crea un contesto di impilamento
- [ ] Distingui `flex: 1` da `flex: auto` e sai prevedere il risultato
- [ ] Sai perché serve `min-inline-size: 0` sugli elementi flex
- [ ] Sai la differenza fra `auto-fit` e `auto-fill`
- [ ] Sai a cosa serve `subgrid` e quale problema risolve
- [ ] Organizzi i token in primitivi e semantici, e sai perché
- [ ] Scrivi un tema a tre stati che rispetta la preferenza di sistema
- [ ] Sai perché le media query vanno in `rem` e non in `px`
- [ ] Sai perché `clamp()` con solo `vw` al centro viola WCAG 1.4.4
- [ ] Sai perché `container-type` va sul genitore
- [ ] Sai come `@layer` cambia l'ordine di valutazione della cascata
- [ ] Usi `:has()` e sai come neutralizzarne la specificità
- [ ] Usi le proprietà logiche e conosci le eccezioni che restano fisiche
- [ ] Sai perché `oklch` produce scale più coerenti di `hsl`
- [ ] Sai quali proprietà girano sul compositor e come verificarlo
- [ ] Scrivi il blocco `prefers-reduced-motion` e sai perché `0.01ms` e non `none`
- [ ] Sai a cosa serve `font-display` e cosa comporta ogni valore

**Parte C — Pratica**

- [ ] Hai costruito la dashboard e verificato le tre configurazioni di layout
- [ ] Hai verificato le container query restringendo il contenitore, non la finestra
- [ ] Hai controllato il contrasto in entrambi i temi
- [ ] Hai verificato con Paint flashing che le animazioni non ridipingano

**Parte D — Esperto**

- [ ] Sai perché `@property` è necessaria per animare una custom property
- [ ] Sai cosa succede a un valore invalido in una proprietà registrata
- [ ] Costruisci una barra di avanzamento con `animation-timeline: scroll()`
- [ ] Sai perché `@starting-style` richiede anche `allow-discrete`
- [ ] Sai perché serve `overlay ... allow-discrete` per animare l'uscita di una `<dialog>`
- [ ] Sai a cosa serve `view-transition-name` e perché deve essere univoco
- [ ] Conosci il costo di `will-change` e `content-visibility`

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| `!important` per far vincere una regola | Inizia una scalata senza fine | Sistemare la specificità, o usare `@layer` |
| `id` nei selettori di stile | Specificità (1,0,0): per sovrascriverla serve un altro id | Stilare con le classi; gli `id` per JavaScript e i frammenti |
| Attributo `style` nel markup statico | Vince quasi su tutto, nessun riuso, nessuna cache | Una classe; `style` solo per custom property calcolate |
| `html { font-size: 62.5% }` | Annulla la preferenza dell'utente sul carattere | Lasciare il root, usare i valori reali in `rem` |
| `font-size` in `px` | Ignora chi ha alzato la dimensione base del browser | `rem` |
| Media query in `px` | Il breakpoint non scala con lo zoom del testo | `rem` |
| Breakpoint copiati dai nomi dei dispositivi | I dispositivi cambiano ogni anno, il contenuto no | Allargare finché il layout non si rompe |
| `100vh` per l'altezza piena su mobile | La barra del browser taglia il contenuto | `100dvh`, o `svh` se serve stabilità |
| `clamp(1.75rem, 4vw, 3rem)` | Solo `vw` al centro blocca lo zoom (WCAG 1.4.4) | Includere un termine in `rem`: `1.2rem + 2.5vw` |
| `transition: all` | Anima proprietà non previste e costringe a osservarle tutte | Elencare le proprietà |
| Animare `width`, `height`, `top`, `left` | Layout + paint a ogni fotogramma, sul thread principale | `transform` e `opacity` |
| `will-change` permanente su molti elementi | Ogni livello consuma memoria video: peggiora invece di migliorare | Attivarlo poco prima, rimuoverlo dopo |
| `outline: none` senza sostituto | Chi naviga da tastiera non sa dove si trova | `:focus-visible` con contrasto e `outline-offset` |
| `overflow: hidden` per contenere i float | Taglia i menu a discesa che sporgono | `display: flow-root`, oppure `overflow: clip` |
| `overflow: hidden` su un antenato di uno sticky | Disattiva `position: sticky` su tutti i discendenti | `overflow: clip` |
| `z-index: 9999` per far stare sopra | Confinato dal contesto di impilamento: non serve a nulla | Scala di token; top layer per modali e popover |
| `1fr` in Grid con contenuto largo | In realtà è `minmax(auto, 1fr)`: non scende sotto il contenuto | `minmax(0, 1fr)` |
| `flex: 1` senza `min-inline-size: 0` | Un `<pre>` o un URL lungo sfonda il contenitore | `min-inline-size: 0` |
| Margini per spaziare in Flexbox e Grid | Eccezioni da gestire, e con il wrap sbagliano | `gap` |
| `line-height` con unità | Non si adatta ai figli con carattere diverso | Numero senza unità |
| Colori scritti direttamente nei componenti | Cambiare tema richiede di toccare ogni componente | Token semantici |
| Tema scuro ottenuto invertendo i colori | Il contrasto non si conserva, le ombre spariscono | Ridefinire i semantici e riverificare il contrasto |
| `container-type` sull'elemento da stilare | Un elemento non può interrogare sé stesso | Sul genitore |
| `:hover` senza `@media (hover: hover)` | Su touch resta appiccicato dopo il primo tocco | Racchiuderlo nella media query |
| Animazioni senza `prefers-reduced-motion` | Nausea e vertigini reali per chi ha disturbi vestibolari | Il blocco di neutralizzazione |
| `body:has(...)` in liste che mutano di continuo | Rivalutazione a ogni mutazione del DOM | Ancorare `:has()` a un contenitore ristretto |

---

## Troubleshooting rapido

**Una regola non si applica anche se il selettore sembra giusto**
- Causa: un'altra regola vince per specificità, per layer o per ordine
- Fix: DevTools → Elements → Computed → cerca la proprietà: mostra la regola vincente e quelle sbarrate, con il file e la riga

**Il layout è diverso da quello atteso e il CSS sembra corretto**
- Causa: il DOM non è quello che hai scritto — tipicamente un elemento chiuso dal parser
- Fix: DevTools → Elements per l'albero reale; `pnpm dlx html-validate` per la causa

**Il margine del primo figlio spinge il genitore invece di spaziarlo**
- Causa: margin collapsing fra genitore e primo figlio
- Fix: `display: flow-root` sul genitore, o `gap` invece dei margini

**Due paragrafi distano meno della somma dei loro margini**
- Causa: margin collapsing fra fratelli — resta il maggiore, non la somma
- Fix: margini in una sola direzione, o `gap` sul contenitore

**Il layout scorre in orizzontale su schermi stretti**
- Causa: un elemento flex o grid non può restringersi sotto il proprio contenuto
- Fix: `min-inline-size: 0` sugli elementi flex, `minmax(0, 1fr)` in Grid. Per trovare il colpevole: `document.querySelectorAll('*')` filtrando su `scrollWidth > clientWidth`

**`position: sticky` non fa nulla**
- Causa: manca la soglia (`inset-block-start`), oppure un antenato ha `overflow` diverso da `visible`, oppure il genitore diretto non è più alto dell'elemento
- Fix: aggiungere la soglia; sostituire `overflow: hidden` con `overflow: clip` sugli antenati

**Il menu a tendina finisce sotto un altro elemento nonostante `z-index` alto**
- Causa: un antenato crea un contesto di impilamento — `opacity < 1`, `transform`, `filter`, `will-change`
- Fix: DevTools → Layers per identificarlo. Rimuovere ciò che lo crea, o usare `popover` / `<dialog>` per uscire nel top layer

**C'è uno spazio bianco sotto un'immagine**
- Causa: `<img>` è `inline` e si appoggia alla linea di base
- Fix: `img { display: block }` nel reset

**Le colonne di un contenitore flex non sono uguali**
- Causa: `flex: auto` invece di `flex: 1` — la prima parte dal contenuto, la seconda da zero
- Fix: `flex: 1`

**La griglia crea colonne vuote quando gli elementi sono pochi**
- Causa: `auto-fill` mantiene le tracce vuote
- Fix: `auto-fit`, che le collassa

**Una container query non si attiva mai**
- Causa: `container-type` è sull'elemento stilato invece che su un suo antenato, oppure il nome non corrisponde
- Fix: spostare `container-type` sul genitore; verificare `container-name`

**Il tema scuro appare al primo caricamento e poi torna chiaro**
- Causa: lo script che legge `localStorage` viene eseguito dopo il primo rendering
- Fix: uno script inline nel `<head>`, prima del CSS

**I controlli nativi (barre di scorrimento, form) restano chiari nel tema scuro**
- Causa: manca `color-scheme`
- Fix: `color-scheme: light dark` su `:root`, e il meta corrispondente

**Un'animazione scatta quando la pagina è occupata**
- Causa: si sta animando una proprietà che richiede layout o paint
- Fix: passare a `transform` e `opacity`. Verificare con DevTools → Rendering → Paint flashing

**Un elemento appare senza animazione la prima volta**
- Causa: non c'è uno stato "prima" da cui interpolare
- Fix: `@starting-style`, insieme a `display ... allow-discrete`

**L'animazione di uscita di una `<dialog>` non si vede**
- Causa: l'elemento lascia il top layer immediatamente alla chiusura
- Fix: aggiungere `overlay 200ms allow-discrete` alla transizione

**Il testo salta quando il font si carica**
- Causa: `font-display: swap` con metriche molto diverse fra ripiego e font reale
- Fix: un `@font-face` di ripiego con `size-adjust` e `ascent-override`, oppure `font-display: optional`

**Il font viene scaricato due volte**
- Causa: `<link rel="preload" as="font">` senza `crossorigin`
- Fix: aggiungere `crossorigin`

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_03_css_framework.md` | Tailwind e Bootstrap: cosa automatizzano dei token e dei layer visti qui |
| `tutorial_04_javascript_fondamenti.md` | Leggere e scrivere le custom properties, reagire a `matchMedia` |
| `tutorial_07_react.md` | CSS Modules, `styled-components`, e i token in un'architettura a componenti |
| `tutorial_15_testing_web.md` | Visual regression testing: verificare che il CSS non cambi per sbaglio |
| `tutorial_17_performance_web.md` | CSS critico, CLS, e la misurazione di quanto il CSS costa |
| `tutorial_21_rsc_server_driven_ui.md` | View Transitions in un'architettura con rendering sul server |

---

## Risorse di riferimento

**Specifiche:**
- [CSS Cascading and Inheritance Level 5](https://www.w3.org/TR/css-cascade-5/) — cascata e `@layer`
- [CSS Grid Layout Level 2](https://www.w3.org/TR/css-grid-2/) — Grid e subgrid
- [CSS Containment Level 3](https://www.w3.org/TR/css-contain-3/) — container query
- [CSS Color Level 4](https://www.w3.org/TR/css-color-4/) — `oklch`, `color-mix`
- [WCAG 2.2 — Contrasto minimo (1.4.3)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum) — i rapporti richiesti

**Documentazione:**
- [MDN — CSS](https://developer.mozilla.org/it/docs/Web/CSS) — riferimento di ogni proprietà
- [web.dev — Learn CSS](https://web.dev/learn/css) — corso strutturato, gratuito
- [CSS-Tricks — A Complete Guide to Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [CSS-Tricks — A Complete Guide to Grid](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Josh Comeau — CSS for JavaScript Developers](https://www.joshwcomeau.com/) — articoli sul modello mentale del layout

**Strumenti:**
- [Can I use](https://caniuse.com/) — supporto dei browser
- [Baseline](https://web.dev/baseline) — quando una funzionalità è disponibile ovunque
- [Utopia](https://utopia.fyi/) — genera scale fluide di tipografia e spazio
- [oklch.com](https://oklch.com/) — selettore di colore in oklch
- [Colour Contrast Analyser](https://www.tpgi.com/color-contrast-checker/) — verifica del contrasto

**Libri:**
- Lea Verou, *CSS Secrets* — soluzioni non ovvie a problemi comuni, con la spiegazione del meccanismo
- Andy Bell e Heydon Pickering, *Every Layout* — layout come componenti algoritmici, invece che come breakpoint

---

> **Fine del Tutorial 02 — CSS Moderno**
>
> Prossimo tutorial: `tutorial_03_css_framework.md`
