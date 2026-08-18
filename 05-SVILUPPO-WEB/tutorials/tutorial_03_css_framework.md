# Tutorial 03 — Framework CSS: Dal Principiante all'Esperto

> **Companion a:** `03-css-framework.md`
> **Scope:** Perché esistono i framework CSS, Sass e PostCSS, Tailwind CSS 4 e la configurazione con `@theme`, Bootstrap 5 e la personalizzazione via Sass, metodologie (BEM, ITCSS, Cube CSS), librerie headless (Radix, Headless UI), shadcn/ui, CSS-in-JS runtime e zero-runtime, CSS Modules, UnoCSS, criteri di scelta e strategie di migrazione
> **Prerequisiti:** `tutorial_02_css3.md` — cascata, specificità, custom properties, design token, `@layer`, Grid e Flexbox
> **Durata stimata:** 18-24 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Tailwind CSS 4.x · Bootstrap 5.3+ · Sass (Dart Sass) · PostCSS 8 · Vite

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Quale problema risolvono i framework CSS](#a1-quale-problema-risolvono-i-framework-css)
  - [A2. Le tre famiglie, e come si riconoscono](#a2-le-tre-famiglie-e-come-si-riconoscono)
  - [A3. Sass: cosa aggiunge, e cosa non serve più](#a3-sass-cosa-aggiunge-e-cosa-non-serve-più)
  - [A4. PostCSS: la pipeline sotto tutto](#a4-postcss-la-pipeline-sotto-tutto)
  - [A5. Tailwind: il primo componente utility-first](#a5-tailwind-il-primo-componente-utility-first)
  - [A6. Bootstrap: la griglia e i componenti pronti](#a6-bootstrap-la-griglia-e-i-componenti-pronti)
  - [A7. BEM: dare un nome alle classi senza pentirsene](#a7-bem-dare-un-nome-alle-classi-senza-pentirsene)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. Tailwind 4: `@theme`, il motore Oxide e i token](#b1-tailwind-4-theme-il-motore-oxide-e-i-token)
  - [B2. Come Tailwind trova le classi, e quando non le trova](#b2-come-tailwind-trova-le-classi-e-quando-non-le-trova)
  - [B3. Estrarre componenti da Tailwind senza rifare un framework](#b3-estrarre-componenti-da-tailwind-senza-rifare-un-framework)
  - [B4. Bootstrap personalizzato via Sass, non sovrascritto](#b4-bootstrap-personalizzato-via-sass-non-sovrascritto)
  - [B5. Architetture: ITCSS e Cube CSS, e cosa `@layer` cambia](#b5-architetture-itcss-e-cube-css-e-cosa-layer-cambia)
  - [B6. CSS Modules: l'ambito senza convenzioni](#b6-css-modules-lambito-senza-convenzioni)
  - [B7. CSS-in-JS: runtime contro zero-runtime](#b7-css-in-js-runtime-contro-zero-runtime)
  - [B8. Librerie headless: comportamento senza aspetto](#b8-librerie-headless-comportamento-senza-aspetto)
  - [B9. shadcn/ui: il codice è tuo](#b9-shadcnui-il-codice-è-tuo)
  - [B10. Accessibilità: cosa il framework ti dà e cosa no](#b10-accessibilità-cosa-il-framework-ti-dà-e-cosa-no)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: la dashboard, ricostruita con Tailwind](#c2-mini-progetto-la-dashboard-ricostruita-con-tailwind)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. UnoCSS e il CSS atomico su misura](#d1-unocss-e-il-css-atomico-su-misura)
  - [D2. Design token condivisi fra CSS, JavaScript e Figma](#d2-design-token-condivisi-fra-css-javascript-e-figma)
  - [D3. Misurare il costo reale di ogni approccio](#d3-misurare-il-costo-reale-di-ogni-approccio)
  - [D4. Migrare da un framework a un altro senza fermare il progetto](#d4-migrare-da-un-framework-a-un-altro-senza-fermare-il-progetto)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                        FRAMEWORK E STRUMENTI CSS
                                  │
     ┌────────────────────────────┼────────────────────────────┐
     │                            │                            │
┌────▼─────────┐        ┌─────────▼─────────┐        ┌─────────▼────────┐
│ PREPROCESSORI│        │  UTILITY-FIRST    │        │ COMPONENT-BASED  │
│              │        │                   │        │                  │
│  Sass/SCSS   │        │  Tailwind CSS 4   │        │  Bootstrap 5     │
│   ├ @use     │        │   ├ @theme        │        │   ├ griglia      │
│   ├ mixin    │        │   ├ motore Oxide  │        │   ├ componenti   │
│   ├ funzioni │        │   └ scansione file│        │   └ Sass vars    │
│   └ @each    │        │  UnoCSS           │        │  Bulma, Foundation│
│  PostCSS     │        │   └ preset        │        │                  │
│   └ plugin   │        │                   │        │                  │
└──────┬───────┘        └─────────┬─────────┘        └────────┬─────────┘
       │                          │                           │
       │   classi nel markup ─────┤                           │
       │   scritte a mano ────────┼───── classi pronte ───────┘
       │                          │
       └──────────────────────────┼───────────────────────────┐
                                  │                           │
                        ┌─────────▼─────────┐       ┌─────────▼────────┐
                        │   AMBITO E JS     │       │   METODOLOGIE    │
                        │                   │       │                  │
                        │  CSS Modules      │       │  BEM             │
                        │   └ hash sui nomi │       │   └ blocco__el   │
                        │  CSS-in-JS        │       │  ITCSS           │
                        │   ├ runtime       │       │   └ a strati     │
                        │   │  styled-comp. │       │  Cube CSS        │
                        │   │  Emotion      │       │   └ C U B E      │
                        │   └ zero-runtime  │       │  OOCSS, SMACSS   │
                        │      Panda CSS    │       │                  │
                        │      vanilla-extr.│       │  @layer li rende │
                        └───────────────────┘       │  quasi superflui │
                                  │                 └──────────────────┘
                        ┌─────────▼─────────┐
                        │     HEADLESS      │
                        │                   │
                        │  Radix UI         │  comportamento + a11y
                        │  Headless UI      │  ZERO aspetto
                        │  Ark UI           │
                        │       │           │
                        │  shadcn/ui        │  Radix + Tailwind,
                        │   └ copi il codice│  copiato nel tuo repo
                        └───────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Quale problema risolvono i framework CSS

> **Analogia:** costruire una casa. Puoi tagliare ogni trave su misura — controllo totale, tempo lungo, e ogni casa è diversa dalle altre anche quando non serve. Oppure puoi partire da elementi prefabbricati — porte, finestre, moduli — e montarli: più veloce, più uniforme, e vincolato a ciò che il catalogo offre. I framework CSS sono il catalogo. La domanda non è quale approccio sia "migliore", ma quale problema hai.

Il CSS scritto a mano su un progetto che cresce incontra tre problemi ricorrenti:

**1. Il file cresce e non si restringe mai.** Nessuno cancella una regola per paura di rompere qualcosa altrove. Dopo due anni il foglio di stile contiene regole che non si applicano più a nulla, e nessuno sa quali.

```css
/* Chi lo sa se .scheda-vecchia è ancora usata da qualche parte? */
.scheda-vecchia { … }
.scheda-vecchia-2 { … }
.scheda-vecchia-2-definitiva { … }
```

**2. I nomi delle classi diventano un problema di per sé.** `.titolo` è già preso, `.titolo-scheda` anche, e si finisce con `.scheda-prodotto-titolo-piccolo-variante-b`.

**3. La coerenza si perde.** Tre sviluppatori producono `padding: 16px`, `padding: 1rem` e `padding: 15px` per lo stesso spazio, e nessuno se ne accorge finché un designer non lo nota.

I framework attaccano questi problemi in modi diversi e incompatibili fra loro:

```
Bootstrap    ti dà i componenti già fatti.
             Problema risolto: velocità di partenza.
             Costo: il sito somiglia agli altri siti Bootstrap,
                    personalizzare richiede di combattere.

Tailwind     ti dà un vocabolario di utility con valori vincolati.
             Problema risolto: coerenza e crescita del CSS
                              (il CSS smette di crescere).
             Costo: il markup diventa verboso.

Sass         ti dà variabili, mixin e funzioni.
             Problema risolto: ripetizione.
             Costo: un passo di compilazione, e molto di ciò
                    che offriva è ora nativo.

CSS Modules  ti dà l'ambito locale.
             Problema risolto: collisione dei nomi.
             Costo: richiede un bundler.

Headless     ti dà comportamento e accessibilità senza aspetto.
             Problema risolto: componenti interattivi corretti.
             Costo: lo stile lo scrivi tutto tu.
```

**La domanda che precede la scelta.** Nel 2026 il CSS nativo ha custom properties, `@layer`, `@scope`, container query, nesting e `:has()`. Molto di ciò per cui i framework esistevano è entrato nella piattaforma. La scelta va rifatta, non ereditata.

```
Quando il CSS nativo basta:
  · progetto piccolo o medio, una o due persone
  · design proprio, non derivato da un catalogo
  · nessuna necessità di prototipare in fretta
  · il team conosce il CSS

Quando un framework aggiunge valore:
  · un team numeroso deve restare coerente senza riunioni
  · serve prototipare in giorni, non settimane
  · il progetto ha centinaia di componenti
  · l'applicazione è un pannello interno: l'aspetto standard va bene
```

---

## A2. Le tre famiglie, e come si riconoscono

Guardando il markup si capisce subito quale famiglia è in uso.

```html
<!-- ── COMPONENT-BASED (Bootstrap) ─────────────────────────────
     Classi che nominano un COMPONENTE. Il CSS lo fornisce il framework. -->
<div class="card">
  <div class="card-body">
    <h5 class="card-title">Ricavi</h5>
    <p class="card-text">1.330 migliaia di euro</p>
    <a href="#" class="btn btn-primary">Dettagli</a>
  </div>
</div>

<!-- ── UTILITY-FIRST (Tailwind) ────────────────────────────────
     Classi che nominano una SINGOLA DICHIARAZIONE.
     Il componente non esiste nel CSS: esiste nel markup. -->
<div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
  <h5 class="text-sm font-semibold uppercase tracking-wide text-neutral-600">Ricavi</h5>
  <p class="text-3xl font-bold tabular-nums">1.330</p>
  <a href="#" class="inline-flex h-11 items-center rounded bg-blue-700 px-4 text-white">
    Dettagli
  </a>
</div>

<!-- ── SEMANTICO (CSS proprio, con o senza BEM) ────────────────
     Classi che nominano il RUOLO. Il CSS lo scrivi tu. -->
<div class="scheda">
  <h5 class="scheda__etichetta">Ricavi</h5>
  <p class="scheda__valore">1.330</p>
  <a href="#" class="pulsante pulsante--primario">Dettagli</a>
</div>
```

### Il confronto che conta

| | Component-based | Utility-first | CSS semantico |
|---|---|---|---|
| **Velocità di partenza** | altissima | alta | bassa |
| **Il CSS cresce con il progetto** | no (è fisso) | **quasi no** | sì, sempre |
| **Il markup resta leggibile** | sì | no | sì |
| **Personalizzare è facile** | no | sì | sì |
| **Serve un passo di build** | no | **sì** | no |
| **Cancellare un componente cancella il suo CSS** | n.d. | **sì, automaticamente** | no, resta orfano |
| **Il risultato somiglia ad altri siti** | sì | no | no |
| **Curva di apprendimento** | bassa | media (il vocabolario) | alta (il CSS vero) |

La riga che spiega perché Tailwind ha vinto tanto terreno è "il CSS cresce con il progetto". In un progetto con CSS semantico, ogni componente nuovo aggiunge righe che non se ne vanno mai. Con le utility, il CSS generato contiene solo le classi effettivamente usate: cancellare un componente ne cancella lo stile, senza che nessuno debba ricordarsene.

### Il costo del markup verboso, misurato

```html
<!-- Tailwind: 11 classi per un pulsante -->
<button class="inline-flex h-11 items-center justify-center rounded bg-blue-700 px-4
               font-medium text-white transition hover:bg-blue-900
               focus-visible:outline focus-visible:outline-2 disabled:opacity-55">
  Salva
</button>
```

Questa è l'obiezione principale a Tailwind, ed è legittima. La risposta operativa non è "abituati": è **estrarre il componente** nel linguaggio che stai già usando — un componente React, un partial, una direttiva `@apply` in un caso ristretto. Il punto è che l'astrazione va fatta dove sta già la logica, non in un secondo linguaggio parallelo. Ne parliamo in [B3](#b3-estrarre-componenti-da-tailwind-senza-rifare-un-framework).

---

## A3. Sass: cosa aggiunge, e cosa non serve più

Sass è nato nel 2006 per dare al CSS ciò che non aveva: variabili, annidamento, funzioni, riuso. Quasi vent'anni dopo, metà di quella lista è nativa. Vale la pena sapere cosa resta.

```powershell
pnpm add -D sass
```

```scss
// src/stile.scss

// ── Variabili ──────────────────────────────────────────────────
// Risolte a COMPILAZIONE: nel CSS prodotto restano solo i valori.
$colore-azione: #1d4ed8;
$spazio-base: 1rem;
$punto-medio: 48rem;

.pulsante {
  background: $colore-azione;
  padding: $spazio-base;
}
```

### Annidamento

```scss
.scheda {
  padding: 1rem;
  border: 1px solid #e5e5e5;

  &__titolo {           // & = il selettore genitore, concatenato
    font-size: 1.25rem;
  }

  &--evidenziata {
    border-color: $colore-azione;
  }

  &:hover {
    box-shadow: 0 4px 12px rgb(0 0 0 / 0.1);
  }

  .icona {              // discendente
    inline-size: 1.5rem;
  }
}
```

```css
/* Compilato in: */
.scheda { padding: 1rem; border: 1px solid #e5e5e5; }
.scheda__titolo { font-size: 1.25rem; }
.scheda--evidenziata { border-color: #1d4ed8; }
.scheda:hover { box-shadow: 0 4px 12px rgb(0 0 0 / 0.1); }
.scheda .icona { inline-size: 1.5rem; }
```

```scss
/* ❌ SBAGLIATO — annidamento profondo: produce selettori lunghissimi
   e specificità alta, difficile da sovrascrivere */
.pagina {
  .contenuto {
    .scheda {
      .titolo {
        span { color: red; }
      }
    }
  }
}
/* → .pagina .contenuto .scheda .titolo span  (0,4,1) */

/* ✅ CORRETTO — mai oltre due livelli.
   La regola operativa: se il selettore compilato ha più di due classi,
   hai annidato troppo. */
.scheda {
  &__titolo {
    span { color: red; }
  }
}
```

### Mixin: il riuso con parametri

```scss
@mixin troncamento-righe($righe: 1) {
  display: -webkit-box;
  -webkit-line-clamp: $righe;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@mixin bersaglio-tocco($dimensione: 2.75rem) {
  min-block-size: $dimensione;
  min-inline-size: $dimensione;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.scheda__descrizione {
  @include troncamento-righe(3);
}

.pulsante-icona {
  @include bersaglio-tocco;
}
```

### Cicli e mappe: dove Sass è ancora insostituibile

```scss
$spazi: (
  1: 0.25rem,
  2: 0.5rem,
  3: 0.75rem,
  4: 1rem,
  6: 1.5rem,
  8: 2rem,
);

// Genera le classi di utility per padding e margin,
// in tutte le direzioni logiche
@each $nome, $valore in $spazi {
  .p-#{$nome} { padding: $valore; }
  .pi-#{$nome} { padding-inline: $valore; }
  .pb-#{$nome} { padding-block: $valore; }
  .m-#{$nome} { margin: $valore; }
  .mi-#{$nome} { margin-inline: $valore; }
  .mb-#{$nome} { margin-block: $valore; }
}
```

Generare centinaia di regole da una struttura dati è l'unica cosa che il CSS nativo non sa fare, e resta il motivo più solido per tenere Sass. È anche esattamente quello che Tailwind fa internamente.

### `@use` e `@forward`, non `@import`

```scss
// ❌ DEPRECATO — @import in Sass produce collisioni di nomi
//    e ricompila lo stesso file più volte. È in via di rimozione.
@import 'variabili';
@import 'mixin';

// ✅ CORRETTO — @use carica una volta sola e crea uno spazio dei nomi
@use 'variabili' as var;
@use 'mixin' as mix;

.pulsante {
  background: var.$colore-azione;
  @include mix.bersaglio-tocco;
}

// Senza spazio dei nomi, quando serve
@use 'variabili' as *;

.pulsante {
  background: $colore-azione;
}
```

```scss
// _indice.scss — @forward ri-espone i moduli, per avere un solo punto d'ingresso
@forward 'variabili';
@forward 'mixin';
@forward 'funzioni';
```

### Cosa NON serve più fare in Sass

```scss
// ❌ Variabili Sass per i valori che cambiano a runtime.
//    Sono risolte a compilazione: un tema scuro richiederebbe
//    di ricompilare due fogli di stile interi.
$colore-testo: #1a1a1a;

// ✅ Custom properties: vivono nel browser, cambiano con una media query
:root {
  --colore-testo: #1a1a1a;
}

@media (prefers-color-scheme: dark) {
  :root { --colore-testo: #ececec; }
}
```

```scss
// ❌ Mixin per le media query, quando basta la sintassi nativa
@mixin da-tablet {
  @media (min-width: 48rem) { @content; }
}

// ✅ La sintassi a intervalli è già leggibile
@media (width >= 48rem) { … }
```

```scss
// ❌ Annidamento Sass, quando il CSS lo fa nativamente
// ✅ CSS nativo:
.scheda {
  padding: 1rem;

  & .titolo {
    font-size: 1.25rem;
  }

  &:hover {
    box-shadow: var(--ombra-md);
  }
}
```

Il nesting nativo è in tutti i browser evergreen dal 2023. **Una differenza che conta:** in CSS nativo il concatenamento `&__titolo` di Sass non esiste — `&` va usato con uno spazio o con una pseudo-classe, non incollato a un suffisso.

```css
/* ❌ NON VALIDO in CSS nativo */
.scheda {
  &__titolo { … }
}

/* ✅ */
.scheda {
  & .scheda__titolo { … }
}
```

**Il bilancio.** Sass resta giustificato per i cicli su mappe, i mixin con parametri e le funzioni di calcolo. Per variabili, annidamento e media query, il CSS nativo fa lo stesso lavoro senza un passo di build. Su un progetto nuovo, partire senza Sass e aggiungerlo se serve è la scelta più difendibile.

---

## A4. PostCSS: la pipeline sotto tutto

PostCSS non è un preprocessore: è un'infrastruttura che analizza il CSS in un albero e lo passa a una catena di plugin. Tailwind, Autoprefixer e decine di altri strumenti sono plugin PostCSS.

```powershell
pnpm add -D postcss autoprefixer postcss-preset-env
```

```javascript
// postcss.config.mjs
export default {
  plugins: {
    // Aggiunge i prefissi dei fornitori in base ai browser dichiarati
    autoprefixer: {},

    // Permette di usare CSS futuro, traducendolo per i browser attuali
    'postcss-preset-env': {
      stage: 2,
      features: {
        'nesting-rules': true,
      },
    },
  },
}
```

```json
// package.json — la lista dei browser da supportare.
// La leggono Autoprefixer, preset-env, Vite e esbuild.
{
  "browserslist": [
    "> 0.5%",
    "last 2 versions",
    "not dead",
    "not op_mini all"
  ]
}
```

```powershell
# Cosa significa davvero quella lista di browser
pnpm dlx browserslist
```

```
# Output atteso (estratto):
and_chr 131
chrome 131
chrome 130
edge 131
firefox 133
ios_saf 18.2
safari 18.2
samsung 27
```

**Il valore di `browserslist`:** dichiara una volta i browser da supportare, e ogni strumento della catena si adegua. Senza, ogni strumento usa il proprio default e le decisioni divergono.

Con Vite, PostCSS è già integrato: basta il file di configurazione e i plugin installati, senza altro.

---

## A5. Tailwind: il primo componente utility-first

```powershell
pnpm add -D tailwindcss @tailwindcss/vite
```

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],
})
```

```css
/* src/stile.css — in Tailwind 4 basta una riga */
@import 'tailwindcss';
```

Nella versione 3 servivano tre direttive (`@tailwind base; @tailwind components; @tailwind utilities;`) e un file `tailwind.config.js`. La versione 4 le sostituisce entrambe: un `@import` e la configurazione nel CSS.

### Il vocabolario

```html
<div class="p-4 bg-white rounded-lg shadow-sm">…</div>
```

Ogni classe è una dichiarazione:

```
p-4          padding: 1rem
px-4         padding-inline: 1rem
py-2         padding-block: 0.5rem
pt-4         padding-top: 1rem
ps-4         padding-inline-start: 1rem   ← logica, segue dir="rtl"

m-4          margin
mx-auto      margin-inline: auto
gap-4        gap: 1rem
space-y-4    margine fra i figli (non gap: agisce con > * + *)

w-full       width: 100%
max-w-prose  max-width: 65ch
h-11         height: 2.75rem
size-6       width e height: 1.5rem

flex         display: flex
grid         display: grid
hidden       display: none
items-center align-items: center
justify-between  justify-content: space-between

text-sm      font-size: 0.875rem
font-bold    font-weight: 700
text-neutral-600   color
bg-blue-700  background-color
border       border-width: 1px
rounded-lg   border-radius
shadow-sm    box-shadow
```

La scala numerica non è arbitraria: `4` significa `1rem` perché l'unità di base è `0.25rem`. `p-2` è mezzo, `p-8` è doppio. Il vincolo è il punto: non puoi scrivere `padding: 15px` per sbaglio.

### Varianti: stati, breakpoint, preferenze

```html
<!-- Il prefisso prima dei due punti condiziona quando la classe si applica -->
<button
  class="
    bg-blue-700
    hover:bg-blue-900
    focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-700
    active:translate-y-px
    disabled:opacity-55 disabled:cursor-not-allowed
  "
>
  Salva
</button>

<!-- Breakpoint: mobile-first, la variante si applica DA quella larghezza in su -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">…</div>

<!-- Tema scuro -->
<div class="bg-white text-neutral-900 dark:bg-neutral-950 dark:text-neutral-50">…</div>

<!-- Le varianti si combinano -->
<div class="md:hover:bg-neutral-100 dark:md:hover:bg-neutral-800">…</div>

<!-- Condizionare al genitore (group) o al fratello precedente (peer) -->
<div class="group">
  <p class="text-neutral-600 group-hover:text-neutral-900">Cambia al passaggio sul genitore</p>
</div>

<input type="email" class="peer" required />
<p class="hidden peer-user-invalid:block text-red-600">Indirizzo non valido</p>

<!-- Container query -->
<div class="@container">
  <article class="flex flex-col @md:flex-row @md:gap-4">…</article>
</div>
```

`peer-user-invalid:block` è un buon esempio di cosa Tailwind automatizza: il messaggio d'errore appare solo quando il campo precedente è invalido, dopo che l'utente ci ha interagito, senza JavaScript.

### Valori arbitrari, con parsimonia

```html
<!-- Quando serve un valore fuori scala, la sintassi con parentesi quadre -->
<div class="w-[37.5%] top-[117px] bg-[#1a2b3c] grid-cols-[16rem_1fr]">…</div>

<!-- Leggere una custom property -->
<div class="bg-(--colore-marchio)">…</div>
```

```html
<!-- ❌ SBAGLIATO — se ogni valore è arbitrario, il vincolo sparisce
     e con esso il motivo per usare Tailwind -->
<div class="p-[13px] mt-[7px] text-[15px] gap-[9px]">…</div>

<!-- ✅ CORRETTO — resta nella scala; l'arbitrario è l'eccezione motivata -->
<div class="p-3 mt-2 text-sm gap-2">…</div>
```

---

## A6. Bootstrap: la griglia e i componenti pronti

```powershell
pnpm add bootstrap
```

```javascript
// src/main.js
import 'bootstrap/dist/css/bootstrap.min.css'
// Il JavaScript serve solo per i componenti interattivi
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
```

### La griglia a dodici colonne

```html
<div class="container">
  <div class="row g-3">
    <!-- Sotto 768px occupa 12/12 (tutta la riga),
         da 768px 6/12 (metà), da 992px 4/12 (un terzo) -->
    <div class="col-12 col-md-6 col-lg-4">Colonna A</div>
    <div class="col-12 col-md-6 col-lg-4">Colonna B</div>
    <div class="col-12 col-md-12 col-lg-4">Colonna C</div>
  </div>
</div>
```

```
I breakpoint di Bootstrap 5:

  (nessuno)  < 576px    portrait phone
  sm         ≥ 576px
  md         ≥ 768px
  lg         ≥ 992px
  xl         ≥ 1200px
  xxl        ≥ 1400px

Sono in px, quindi non scalano con lo zoom del testo.
È una differenza rispetto ai breakpoint in rem raccomandati
in tutorial_02: un compromesso di compatibilità del framework.
```

### I componenti

```html
<!-- Scheda -->
<div class="card">
  <div class="card-body">
    <h5 class="card-title">Ricavi del trimestre</h5>
    <h6 class="card-subtitle mb-2 text-body-secondary">T3 2026</h6>
    <p class="card-text">1.330 migliaia di euro, in crescita del 12,4%.</p>
    <a href="/report" class="btn btn-primary">Apri il report</a>
  </div>
</div>

<!-- Finestra modale: il markup ARIA è già corretto -->
<button type="button" class="btn btn-danger"
        data-bs-toggle="modal" data-bs-target="#conferma">
  Elimina
</button>

<div class="modal fade" id="conferma" tabindex="-1"
     aria-labelledby="titolo-conferma" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h1 class="modal-title fs-5" id="titolo-conferma">Confermi l'eliminazione?</h1>
        <button type="button" class="btn-close"
                data-bs-dismiss="modal" aria-label="Chiudi"></button>
      </div>
      <div class="modal-body">
        <p>L'operazione non è reversibile.</p>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
          Annulla
        </button>
        <button type="button" class="btn btn-danger">Elimina definitivamente</button>
      </div>
    </div>
  </div>
</div>
```

`data-bs-toggle` e `data-bs-target` collegano comando e bersaglio senza scrivere JavaScript. Il confinamento del focus, `Esc`, lo sfondo e il ripristino del focus alla chiusura sono già gestiti — è ciò per cui si sceglie Bootstrap.

### Le utility

Bootstrap 5 ha anche un livello di utility, che riduce la distanza con Tailwind:

```html
<div class="d-flex justify-content-between align-items-center gap-3 p-4 bg-body-tertiary rounded">
  <span class="fw-semibold">Etichetta</span>
  <span class="text-body-secondary small">Valore</span>
</div>
```

```
Le convenzioni di denominazione, che vanno imparate:

  d-flex          display: flex
  justify-content-between
  align-items-center
  gap-3           (la scala è 0-5, non lineare)
  p-4 / px-4 / pt-4
  m-auto / mx-auto
  text-body-secondary
  bg-body-tertiary
  fw-semibold     font-weight
  fs-5            font-size
  rounded / rounded-3
  border / border-top-0
  d-none d-md-block   (nascosto sotto md)
```

---

## A7. BEM: dare un nome alle classi senza pentirsene

Quando scrivi CSS proprio, il problema è dare i nomi. BEM è la convenzione più diffusa perché risolve due cose insieme: dice a cosa serve una classe e mantiene la specificità piatta.

```
Blocco__Elemento--Modificatore

  Blocco        un componente autonomo         .scheda
  __Elemento    una parte del blocco           .scheda__titolo
  --Modificatore una variante                  .scheda--evidenziata
```

```html
<article class="scheda scheda--evidenziata">
  <header class="scheda__intestazione">
    <h3 class="scheda__titolo">Ricavi</h3>
    <span class="scheda__etichetta scheda__etichetta--positiva">+12,4%</span>
  </header>

  <div class="scheda__corpo">
    <p class="scheda__valore">1.330</p>
  </div>

  <footer class="scheda__azioni">
    <a class="pulsante pulsante--primario" href="/report">Dettagli</a>
  </footer>
</article>
```

```css
/* Tutte le classi hanno specificità (0,1,0). Nessuna gerarchia,
   nessuna sorpresa su chi vince. */
.scheda { … }
.scheda--evidenziata { … }
.scheda__titolo { … }
.scheda__etichetta { … }
.scheda__etichetta--positiva { … }
```

### Le regole che rendono BEM utile invece che pedante

```html
<!-- ❌ SBAGLIATO — l'elemento riflette l'annidamento del DOM.
     Se sposti il titolo di un livello, la classe è da riscrivere. -->
<article class="scheda">
  <header class="scheda__intestazione">
    <h3 class="scheda__intestazione__titolo">…</h3>
  </header>
</article>

<!-- ✅ CORRETTO — l'elemento appartiene al BLOCCO, non al suo genitore.
     Un solo livello di __, sempre. -->
<article class="scheda">
  <header class="scheda__intestazione">
    <h3 class="scheda__titolo">…</h3>
  </header>
</article>
```

```html
<!-- ❌ SBAGLIATO — il modificatore da solo: perde tutto lo stile di base -->
<article class="scheda--evidenziata">…</article>

<!-- ✅ CORRETTO — il modificatore ACCOMPAGNA il blocco -->
<article class="scheda scheda--evidenziata">…</article>
```

```html
<!-- Quando un blocco ne contiene un altro, il blocco interno resta
     autonomo. Non diventa un elemento del blocco esterno. -->
<article class="scheda">
  <!-- .pulsante è un blocco a sé: si usa anche fuori dalla scheda -->
  <a class="pulsante pulsante--primario">Dettagli</a>
</article>
```

### BEM con il nesting nativo

```css
.scheda {
  padding: var(--spazio-4);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio-md);

  /* Il concatenamento &__ di Sass NON esiste in CSS nativo.
     Va scritto per esteso. */
  & .scheda__titolo {
    font-size: var(--testo-lg);
  }

  &.scheda--evidenziata {
    border-color: var(--azione);
  }
}
```

**BEM è ancora necessario?** Meno di prima. `@layer` risolve il problema della specificità in modo più diretto, e i CSS Modules risolvono le collisioni di nomi senza convenzioni. BEM resta utile quando il CSS è servito come file globale senza un bundler — siti tradizionali, temi, pagine di terzi — e quando il team ha bisogno di una convenzione condivisa scritta.

---

# Parte B — Comprensione Profonda

---

## B1. Tailwind 4: `@theme`, il motore Oxide e i token

La versione 4 ha spostato la configurazione dal JavaScript al CSS. Non è un cambiamento cosmetico: `@theme` genera contemporaneamente le classi utility **e** le custom properties corrispondenti.

```css
/* src/stile.css */
@import 'tailwindcss';

@theme {
  /* ── Colori ─────────────────────────────────────────────── */
  --color-marchio-50: oklch(97% 0.02 264);
  --color-marchio-500: oklch(60% 0.18 264);
  --color-marchio-700: oklch(45% 0.18 264);
  --color-marchio-900: oklch(30% 0.12 264);

  /* ── Tipografia ─────────────────────────────────────────── */
  --font-testo: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;

  --text-titolo: 2rem;
  --text-titolo--line-height: 1.2;
  --text-titolo--letter-spacing: -0.02em;

  /* ── Spazio ─────────────────────────────────────────────── */
  --spacing-sezione: 4rem;

  /* ── Breakpoint ─────────────────────────────────────────── */
  --breakpoint-tablet: 48rem;
  --breakpoint-desktop: 72rem;

  /* ── Altro ──────────────────────────────────────────────── */
  --radius-scheda: 0.75rem;
  --shadow-scheda: 0 1px 2px rgb(0 0 0 / 0.06);
  --ease-morbida: cubic-bezier(0.4, 0, 0.2, 1);
}
```

Da questa dichiarazione nascono, contemporaneamente:

```html
<!-- Le classi utility -->
<div class="bg-marchio-700 text-titolo rounded-scheda shadow-scheda p-sezione">…</div>
<div class="tablet:grid-cols-2 desktop:grid-cols-3">…</div>
```

```css
/* E le custom properties nel :root, usabili da CSS esterno e da JavaScript */
.componente-legacy {
  background: var(--color-marchio-700);
  border-radius: var(--radius-scheda);
}
```

```javascript
// Leggibili anche da JavaScript
const colore = getComputedStyle(document.documentElement)
  .getPropertyValue('--color-marchio-700')
  .trim()
```

Questo è il punto che rende `@theme` diverso da `tailwind.config.js`: i token non sono più chiusi dentro il framework. Un componente che non usa Tailwind può leggere gli stessi valori.

### Il prefisso dello spazio dei nomi determina cosa viene generato

```
--color-*        →  bg-*, text-*, border-*, fill-*, ring-*, …
--font-*         →  font-*
--text-*         →  text-* (dimensione)
--spacing-*      →  p-*, m-*, gap-*, w-*, h-*, …
--breakpoint-*   →  le varianti responsive
--container-*    →  le varianti @container
--radius-*       →  rounded-*
--shadow-*       →  shadow-*
--ease-*         →  ease-*
--animate-*      →  animate-*
```

Un token con un prefisso non riconosciuto diventa solo una custom property, senza generare utility.

### Sostituire la scala predefinita invece di estenderla

```css
@theme {
  /* Azzera l'intera scala dei colori predefinita:
     restano solo i tuoi. Utile per impedire che qualcuno
     usi bg-fuchsia-400 per sbaglio. */
  --color-*: initial;

  --color-bianco: #fff;
  --color-nero: #000;
  --color-marchio-500: oklch(60% 0.18 264);
  --color-neutro-100: oklch(96% 0 0);
  --color-neutro-900: oklch(18% 0 0);
}
```

### Il motore Oxide

Tailwind 4 ha riscritto la pipeline in Rust, con Lightning CSS come backend. In pratica significa build molto più rapide e nessuna dipendenza obbligatoria da PostCSS: il plugin Vite (`@tailwindcss/vite`) è la via più diretta, e PostCSS resta disponibile per integrarsi con pipeline esistenti.

```javascript
// Con Vite — la via consigliata
import tailwindcss from '@tailwindcss/vite'
export default { plugins: [tailwindcss()] }
```

```javascript
// Con PostCSS — quando la pipeline esiste già
// postcss.config.mjs
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
}
```

### Utility e componenti propri

```css
@import 'tailwindcss';

/* @utility crea una utility vera: funziona con tutte le varianti
   (hover:, md:, dark:) come quelle native */
@utility area-lettura {
  max-inline-size: 65ch;
  margin-inline: auto;
}

/* Con un valore parametrico */
@utility troncato-* {
  display: -webkit-box;
  -webkit-line-clamp: --value(integer);
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

```html
<p class="area-lettura md:troncato-3">…</p>
```

```css
/* @layer components per gli stili di componente: stanno in un layer
   più basso delle utility, quindi le utility li sovrascrivono sempre */
@layer components {
  .prosa {
    & h2 {
      font-size: var(--text-2xl);
      margin-block: var(--spacing-8) var(--spacing-4);
    }

    & p {
      margin-block-end: var(--spacing-4);
      max-inline-size: 65ch;
    }
  }
}
```

### Varianti personalizzate

```css
/* Una variante per uno stato applicativo */
@custom-variant caricamento (&[data-stato='caricamento']);

/* Tema scuro comandato da un attributo invece che dalla media query */
@custom-variant dark (&:where([data-tema='scuro'], [data-tema='scuro'] *));
```

```html
<button class="bg-marchio-700 caricamento:opacity-50 caricamento:cursor-wait"
        data-stato="caricamento">
  Salva
</button>
```

---

## B2. Come Tailwind trova le classi, e quando non le trova

Tailwind genera solo il CSS delle classi che trova nei file sorgente. La scansione è **testuale**: cerca stringhe che somigliano a nomi di classe, senza eseguire il codice e senza capire il linguaggio.

Questo spiega il problema più frequente di chi inizia.

```jsx
// ❌ SBAGLIATO — la classe non esiste da nessuna parte come stringa intera.
//    Tailwind vede "bg-", "500" e "rosso", mai "bg-rosso-500".
//    Il CSS non viene generato e in produzione lo sfondo manca.
function Distintivo({ colore }) {
  return <span className={`bg-${colore}-500 text-white px-2`}>…</span>
}
```

```jsx
// ✅ CORRETTO — le classi complete compaiono nel sorgente
const CLASSI_PER_COLORE = {
  verde: 'bg-green-500 text-white',
  rosso: 'bg-red-500 text-white',
  ambra: 'bg-amber-500 text-black',
}

function Distintivo({ colore = 'verde' }) {
  return <span className={`${CLASSI_PER_COLORE[colore]} px-2 rounded`}>…</span>
}
```

```jsx
// ✅ ALTERNATIVA — una custom property come ponte:
//    la classe è statica, il valore è dinamico
function Distintivo({ colore }) {
  return (
    <span className="bg-(--colore-distintivo) px-2 rounded"
          style={{ '--colore-distintivo': colore }}>
      …
    </span>
  )
}
```

### Il funzionamento in v4: rilevamento automatico

Tailwind 4 individua da solo i file da scansionare, escludendo `.gitignore`, i binari e `node_modules`. Non serve più il campo `content` della configurazione. Quando serve intervenire:

```css
@import 'tailwindcss';

/* Aggiungere una sorgente che il rilevamento non trova —
   tipicamente una libreria in node_modules che contiene classi Tailwind */
@source '../node_modules/@azienda/ui/dist';

/* Escludere una cartella dalla scansione */
@source not '../src/legacy';

/* Registrare classi che non compaiono nel sorgente
   (arrivano da un CMS, da un database, da HTML remoto) */
@source inline('bg-red-500 bg-green-500 bg-amber-500');

/* Con espansione delle varianti */
@source inline('{hover:,focus:,}bg-{red,green,amber}-{500,600}');
```

### Diagnosticare una classe mancante

```powershell
# 1. La classe esiste nel CSS prodotto?
pnpm build
Select-String -Path "dist/assets/*.css" -Pattern "bg-marchio-700"

# 2. Se non c'è, cercala nel sorgente come stringa intera
Select-String -Path "src/**/*.{js,jsx,ts,tsx,html}" -Pattern "bg-marchio-700"
```

```
# Se il passo 2 non trova nulla, la classe viene composta a runtime:
# è il caso dell'esempio sbagliato qui sopra.
#
# Se il passo 2 la trova ma il passo 1 no, il file non viene scansionato:
# aggiungilo con @source.
```

### L'ordine delle classi nel markup non conta

```html
<!-- Queste due righe producono lo stesso risultato -->
<div class="p-4 bg-white rounded">…</div>
<div class="rounded bg-white p-4">…</div>
```

L'ordine nel CSS generato è deciso da Tailwind, non dall'attributo. Ne consegue che due utility in conflitto non si risolvono per ordine di scrittura:

```html
<!-- ❌ Ambiguo: quale padding vince? Dipende dall'ordine INTERNO
     di Tailwind, non da come le hai scritte. -->
<div class="p-4 p-8">…</div>
```

Il problema si presenta davvero quando un componente riceve classi dall'esterno:

```jsx
// ❌ La classe passata dal chiamante potrebbe non vincere
function Scheda({ className }) {
  return <div className={`p-4 bg-white ${className}`}>…</div>
}

// <Scheda className="p-8" />  → indeterminato
```

```powershell
pnpm add tailwind-merge clsx
```

```jsx
// ✅ tailwind-merge risolve i conflitti: l'ultima utility della stessa
//    famiglia vince, come ci si aspetta
import { twMerge } from 'tailwind-merge'
import clsx from 'clsx'

function Scheda({ className, evidenziata }) {
  return (
    <div
      className={twMerge(
        clsx(
          'p-4 bg-white rounded-lg border border-neutral-200',
          evidenziata && 'border-marchio-700 shadow-md',
        ),
        className,
      )}
    >
      …
    </div>
  )
}

// <Scheda className="p-8" />  → p-8 vince, p-4 viene rimossa
```

`clsx` compone condizionalmente, `twMerge` risolve i conflitti. Insieme sono la coppia standard in ogni progetto React con Tailwind.

---

## B3. Estrarre componenti da Tailwind senza rifare un framework

Il markup verboso è l'obiezione legittima a Tailwind. Ci sono tre risposte, e solo due sono buone.

### Estrazione nel linguaggio dei componenti — la risposta giusta

```jsx
// src/componenti/Pulsante.jsx
import { twMerge } from 'tailwind-merge'
import clsx from 'clsx'

const BASE =
  'inline-flex h-11 items-center justify-center gap-2 rounded px-4 font-medium ' +
  'transition-colors focus-visible:outline focus-visible:outline-2 ' +
  'focus-visible:outline-offset-2 disabled:opacity-55 disabled:cursor-not-allowed'

const VARIANTI = {
  primario: 'bg-marchio-700 text-white hover:bg-marchio-900 focus-visible:outline-marchio-700',
  secondario:
    'border border-neutral-200 text-marchio-700 hover:bg-marchio-50 ' +
    'dark:border-neutral-800 dark:hover:bg-neutral-900',
  pericolo: 'bg-red-600 text-white hover:bg-red-700 focus-visible:outline-red-600',
}

const DIMENSIONI = {
  piccolo: 'h-9 px-3 text-sm',
  medio: '',
  grande: 'h-12 px-6 text-lg',
}

export function Pulsante({
  variante = 'primario',
  dimensione = 'medio',
  className,
  ...resto
}) {
  return (
    <button
      className={twMerge(clsx(BASE, VARIANTI[variante], DIMENSIONI[dimensione]), className)}
      {...resto}
    />
  )
}
```

```jsx
// L'uso torna leggibile, e le utility restano disponibili per i casi particolari
<Pulsante variante="pericolo">Elimina</Pulsante>
<Pulsante variante="secondario" dimensione="piccolo" className="w-full">Annulla</Pulsante>
```

### `@apply` — la risposta da usare con parsimonia

```css
@layer components {
  .pulsante {
    @apply inline-flex h-11 items-center justify-center rounded px-4 font-medium;
    @apply transition-colors focus-visible:outline focus-visible:outline-2;
  }

  .pulsante--primario {
    @apply bg-marchio-700 text-white hover:bg-marchio-900;
  }
}
```

```
Perché @apply va limitato ai casi giusti:

  ❌ Ricrea esattamente il problema che Tailwind risolveva:
     un foglio di stile che cresce e non si restringe.
  ❌ Il CSS torna a essere un secondo posto in cui cercare,
     separato dal componente.
  ❌ Perdi la lettura immediata: dal markup non si vede più
     cosa fa quella classe.

  ✅ Legittimo quando NON hai un linguaggio di componenti:
     un sito con template server-side, un tema WordPress,
     una email, un widget distribuito come HTML.

  ✅ Legittimo per elementi ripetuti che non sono componenti:
     lo stile del contenuto generato da Markdown.
```

### Class Variance Authority — quando le varianti diventano molte

```powershell
pnpm add class-variance-authority
```

```jsx
// src/componenti/Pulsante.jsx
import { cva } from 'class-variance-authority'
import { twMerge } from 'tailwind-merge'

const pulsante = cva(
  // classi di base
  'inline-flex items-center justify-center gap-2 rounded font-medium transition-colors ' +
    'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ' +
    'disabled:opacity-55 disabled:cursor-not-allowed',
  {
    variants: {
      variante: {
        primario: 'bg-marchio-700 text-white hover:bg-marchio-900',
        secondario: 'border border-neutral-200 text-marchio-700 hover:bg-marchio-50',
        pericolo: 'bg-red-600 text-white hover:bg-red-700',
      },
      dimensione: {
        piccolo: 'h-9 px-3 text-sm',
        medio: 'h-11 px-4',
        grande: 'h-12 px-6 text-lg',
      },
      larghezzaPiena: {
        true: 'w-full',
      },
    },
    // Combinazioni che richiedono uno stile specifico
    compoundVariants: [
      {
        variante: 'pericolo',
        dimensione: 'grande',
        class: 'font-bold uppercase tracking-wide',
      },
    ],
    defaultVariants: {
      variante: 'primario',
      dimensione: 'medio',
    },
  },
)

export function Pulsante({ variante, dimensione, larghezzaPiena, className, ...resto }) {
  return (
    <button
      className={twMerge(pulsante({ variante, dimensione, larghezzaPiena }), className)}
      {...resto}
    />
  )
}
```

`cva` diventa utile a partire da tre varianti con combinazioni; sotto quella soglia un oggetto di mappatura è più leggibile.

---

## B4. Bootstrap personalizzato via Sass, non sovrascritto

L'errore che rende Bootstrap sgradevole è usarlo compilato e poi combatterlo con sovrascritture.

```css
/* ❌ SBAGLIATO — la scalata comincia qui */
.btn-primary {
  background-color: #1d4ed8 !important;
  border-color: #1d4ed8 !important;
}

.btn-primary:hover {
  background-color: #1e3a8a !important;
}
/* …e poi servirà lo stesso per :active, :focus, .disabled,
   e per ogni altro componente che usa il colore primario. */
```

```scss
// ✅ CORRETTO — cambiare le variabili PRIMA di compilare Bootstrap.
//    Il colore si propaga a pulsanti, link, form, badge, alert,
//    barre di avanzamento: ovunque Bootstrap lo usi.

// src/bootstrap-personalizzato.scss

// 1. Funzioni: servono alle variabili che seguono
@import 'bootstrap/scss/functions';

// 2. Le TUE variabili, prima dei default di Bootstrap
$primary: #1d4ed8;
$danger: #dc2626;
$success: #16a34a;

$font-family-sans-serif: 'Inter', system-ui, sans-serif;
$border-radius: 0.5rem;
$border-radius-lg: 0.75rem;

// Ridefinire i breakpoint
$grid-breakpoints: (
  xs: 0,
  sm: 576px,
  md: 768px,
  lg: 992px,
  xl: 1200px,
  xxl: 1400px,
);

// Disattivare ciò che non usi: riduce sensibilmente il file finale
$enable-shadows: false;
$enable-gradients: false;
$enable-smooth-scroll: false;

// 3. I default di Bootstrap (le variabili già definite non vengono toccate,
//    grazie al flag !default nel loro sorgente)
@import 'bootstrap/scss/variables';
@import 'bootstrap/scss/variables-dark';
@import 'bootstrap/scss/maps';
@import 'bootstrap/scss/mixins';
@import 'bootstrap/scss/root';

// 4. SOLO i moduli che servono davvero
@import 'bootstrap/scss/reboot';
@import 'bootstrap/scss/type';
@import 'bootstrap/scss/containers';
@import 'bootstrap/scss/grid';
@import 'bootstrap/scss/buttons';
@import 'bootstrap/scss/forms';
@import 'bootstrap/scss/card';
@import 'bootstrap/scss/modal';
@import 'bootstrap/scss/nav';
@import 'bootstrap/scss/tables';

// 5. Le utility (opzionale, ma è la parte che si usa di più)
@import 'bootstrap/scss/helpers';
@import 'bootstrap/scss/utilities';
@import 'bootstrap/scss/utilities/api';
```

```powershell
# Il risparmio è misurabile
pnpm build
Get-ChildItem dist/assets/*.css | Select-Object Name, @{n='kB';e={[math]::Round($_.Length/1kb,1)}}
```

```
# Bootstrap completo minificato:        ~230 kB
# Solo i moduli elencati sopra:          ~90 kB
# Con purge delle classi inutilizzate:   ~30 kB
```

### Aggiungere utility proprie all'API di Bootstrap

```scss
// Dopo @import 'bootstrap/scss/utilities';
// e PRIMA di 'bootstrap/scss/utilities/api';

$utilities: map-merge(
  $utilities,
  (
    'opacity': (
      property: opacity,
      values: (0: 0, 25: 0.25, 50: 0.5, 75: 0.75, 100: 1),
      responsive: true,
      state: hover,
    ),
    'cursor': (
      property: cursor,
      class: cursor,
      values: auto pointer grab not-allowed,
    ),
  )
);

@import 'bootstrap/scss/utilities/api';
```

```html
<div class="opacity-50 hover-opacity-100 md:opacity-75 cursor-pointer">…</div>
```

---

## B5. Architetture: ITCSS e Cube CSS, e cosa `@layer` cambia

### ITCSS — il triangolo rovesciato

Organizza il CSS in strati, dal più generico al più specifico. L'ordine di importazione è l'architettura.

```
       ╲                                          ╱
        ╲  1. SETTINGS   variabili, token         ╱   nessun CSS prodotto
         ╲ 2. TOOLS      mixin, funzioni         ╱    nessun CSS prodotto
          ╲3. GENERIC    reset, normalize       ╱     specificità 0
           ╲4. ELEMENTS  h1, p, a (senza classi)╱     specificità 0,0,1
            ╲5. OBJECTS  layout senza aspetto  ╱      specificità 0,1,0
             ╲6. COMPONENTS  i componenti     ╱       specificità 0,1,0
              ╲7. UTILITIES  a scopo unico   ╱        specificità 0,1,0 + !important
               ╲___________________________╱

  Larghezza = quanto del sito è colpito (da tutto a un elemento solo)
  Profondità = specificità (crescente)
```

```scss
// src/stile.scss — l'ordine È l'architettura
@use 'settings/colori';
@use 'settings/spazio';
@use 'tools/mixin';
@use 'generic/reset';
@use 'elements/tipografia';
@use 'objects/contenitore';
@use 'objects/griglia';
@use 'components/scheda';
@use 'components/pulsante';
@use 'utilities/visibilita';
```

**Cosa `@layer` cambia.** ITCSS esisteva per garantire l'ordine con l'ordine dei file. `@layer` lo rende esplicito e indipendente dall'ordine di importazione:

```css
/* L'ordine è dichiarato, non implicito.
   Chi legge il file lo capisce subito, e nessuno lo rompe
   spostando una riga di @import. */
@layer generic, elements, objects, components, utilities;
```

Con `@layer`, la parte di ITCSS che riguardava la disciplina della specificità diventa superflua. Resta utile la sua tassonomia — la distinzione fra *object* (layout senza aspetto) e *component* (aspetto) è un buon modo di pensare.

### Cube CSS

Un'organizzazione più recente, pensata per convivere con le utility.

```
C  Composition   il layout: come i blocchi si dispongono
                 (.pila, .griglia, .barra) — niente colori né bordi

U  Utility       una dichiarazione, un compito
                 (.testo-tenue, .misura-lettura)

B  Block         il componente vero e proprio
                 (.scheda, .navigazione)

E  Exception     una variante, dichiarata con un attributo data-*
                 ([data-stato="compatto"])
```

```html
<article class="scheda pila" data-stato="compatto">
  <h3 class="scheda__titolo misura-lettura">Ricavi</h3>
  <p class="testo-tenue">In crescita del 12,4%</p>
</article>
```

```css
/* Composition: solo layout */
.pila {
  display: flex;
  flex-direction: column;
  gap: var(--gap-pila, 1rem);
}

/* Block: solo aspetto */
.scheda {
  padding: var(--spazio-4);
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio-md);
}

/* Exception: con un attributo, non con una classe modificatore */
.scheda[data-stato='compatto'] {
  --gap-pila: 0.5rem;
  padding: var(--spazio-2);
}
```

Il valore di Cube CSS è la separazione fra layout e aspetto: `.pila` funziona su qualunque componente, e `.scheda` non sa nulla di come si dispone. È l'idea alla base di *Every Layout*.

---

## B6. CSS Modules: l'ambito senza convenzioni

Un file `*.module.css` viene trasformato dal bundler: ogni nome di classe diventa unico, e il file JavaScript riceve la mappatura.

```css
/* src/componenti/Scheda.module.css */
.contenitore {
  padding: var(--spazio-4);
  background: var(--superficie);
  border: 1px solid var(--bordo);
  border-radius: var(--raggio-md);
}

.titolo {
  margin: 0;
  font-size: var(--testo-lg);
}

.evidenziata {
  border-color: var(--azione);
}

/* :global esce dall'ambito, quando serve toccare qualcosa di esterno */
:global(.legacy-widget) .titolo {
  font-size: var(--testo-base);
}

/* composes riusa un'altra classe senza duplicare le dichiarazioni */
.titoloGrande {
  composes: titolo;
  font-size: var(--testo-2xl);
}
```

```jsx
// src/componenti/Scheda.jsx
import stili from './Scheda.module.css'
import clsx from 'clsx'

export function Scheda({ titolo, evidenziata, children }) {
  return (
    <article className={clsx(stili.contenitore, evidenziata && stili.evidenziata)}>
      <h3 className={stili.titolo}>{titolo}</h3>
      {children}
    </article>
  )
}
```

```html
<!-- Nel DOM: il nome è stato reso univoco -->
<article class="Scheda_contenitore__a3f9k Scheda_evidenziata__b71m2">
  <h3 class="Scheda_titolo__c8x1p">Ricavi</h3>
</article>
```

```
Cosa risolvono e cosa no:

  ✅ Collisione dei nomi: impossibile per costruzione
  ✅ CSS non usato: il bundler lo elimina insieme al componente
  ✅ Resta CSS normale: nessun linguaggio nuovo da imparare
  ✅ Nessun costo a runtime: è tutto a tempo di build

  ❌ Richiede un bundler
  ❌ I nomi nel DOM sono illeggibili in produzione
       (in sviluppo Vite li mantiene leggibili)
  ❌ Nessun aiuto sulla coerenza: nulla impedisce
     padding: 15px in un modulo e 16px nell'altro
```

```javascript
// vite.config.js — nomi leggibili in sviluppo
export default {
  css: {
    modules: {
      generateScopedName:
        process.env.NODE_ENV === 'production'
          ? '[hash:base64:8]'
          : '[name]__[local]__[hash:base64:4]',
    },
  },
}
```

I CSS Modules si combinano bene con Tailwind: le utility per il grosso, un modulo per ciò che le utility non esprimono (selettori complessi, `::before` articolati, animazioni con molti keyframe).

---

## B7. CSS-in-JS: runtime contro zero-runtime

### Runtime: styled-components ed Emotion

```jsx
import styled from 'styled-components'

const Pulsante = styled.button`
  display: inline-flex;
  align-items: center;
  height: 2.75rem;
  padding-inline: 1rem;
  border-radius: 0.25rem;

  /* Le props condizionano lo stile */
  background: ${(p) => (p.$primario ? 'var(--azione)' : 'transparent')};
  color: ${(p) => (p.$primario ? 'white' : 'var(--azione)')};

  &:hover {
    background: ${(p) => (p.$primario ? 'var(--azione-attiva)' : 'var(--azione-tenue)')};
  }
`

// Il $ nel nome della prop evita che venga passata al DOM
;<Pulsante $primario>Salva</Pulsante>
```

```
Il costo, misurabile:

  · Il CSS viene generato NEL BROWSER, a ogni rendering
  · La libreria pesa 12-16 kB gzip nel bundle
  · Con React 18+ e i Server Components l'integrazione
    richiede accorgimenti: lo stile si genera sul client,
    quindi arriva dopo il primo dipinto
  · Il costo cresce con il numero di componenti stilati
```

Nel 2026 le soluzioni runtime sono in netto declino. Il team di styled-components ha dichiarato il progetto in manutenzione. Non è una scelta da fare su un progetto nuovo.

### Zero-runtime: vanilla-extract e Panda CSS

Stessa ergonomia — scrivere lo stile in TypeScript, con i tipi — ma il CSS viene estratto a tempo di build.

```typescript
// src/componenti/pulsante.css.ts
import { style, styleVariants } from '@vanilla-extract/css'
import { vars } from '../temi/contratto.css'

const base = style({
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: '2.75rem',
  paddingInline: vars.spazio[4],
  borderRadius: vars.raggio.sm,
  transition: 'background 200ms',

  ':disabled': {
    opacity: 0.55,
    cursor: 'not-allowed',
  },
})

export const varianti = styleVariants({
  primario: [
    base,
    {
      background: vars.colore.azione,
      color: vars.colore.azioneTesto,
      selectors: {
        '&:hover:not(:disabled)': { background: vars.colore.azioneAttiva },
      },
    },
  ],
  secondario: [
    base,
    {
      background: 'transparent',
      color: vars.colore.azione,
      border: `1px solid ${vars.colore.bordo}`,
    },
  ],
})
```

```tsx
import { varianti } from './pulsante.css'

<button className={varianti.primario}>Salva</button>
```

```
Il risultato:

  ✅ Zero JavaScript a runtime: il CSS è un file statico
  ✅ Tipi completi: un token inesistente è un errore di compilazione
  ✅ Il tema è un contratto tipizzato
  ✅ Funziona con i Server Components

  ❌ Un linguaggio in più da imparare
  ❌ Legato al bundler
  ❌ Ecosistema molto più piccolo di Tailwind
```

### Il confronto, per decidere

| | styled-components | vanilla-extract | Panda CSS | Tailwind | CSS Modules |
|---|---|---|---|---|---|
| Costo a runtime | **alto** | zero | zero | zero | zero |
| Peso nel bundle JS | 12-16 kB | 0 | 0 | 0 | 0 |
| Tipi sui token | parziale | **completo** | **completo** | parziale | no |
| Server Components | problematico | sì | sì | sì | sì |
| Ecosistema | in declino | medio | medio | **molto ampio** | universale |
| Curva | bassa | media | media | media | **bassa** |

---

## B8. Librerie headless: comportamento senza aspetto

Un menu a discesa accessibile richiede: gestione del focus, navigazione con le frecce, `Esc` per chiudere, ricerca digitando, `aria-expanded`, `aria-activedescendant`, posizionamento che tiene conto dei bordi dello schermo, e chiusura al clic esterno. Sono centinaia di righe, e le implementazioni artigianali ne sbagliano quasi sempre almeno tre.

Le librerie headless forniscono tutto questo **senza una riga di stile**.

```powershell
pnpm add @radix-ui/react-dialog @radix-ui/react-dropdown-menu
```

```jsx
import * as Dialog from '@radix-ui/react-dialog'

export function ConfermaEliminazione({ nomeDocumento, onConferma }) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button className="rounded bg-red-600 px-4 h-11 text-white">Elimina</button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 data-[state=open]:animate-in" />

        <Dialog.Content
          className="fixed left-1/2 top-1/2 w-[min(32rem,90vw)] -translate-x-1/2
                     -translate-y-1/2 rounded-lg bg-white p-6 shadow-lg
                     dark:bg-neutral-900"
        >
          <Dialog.Title className="text-lg font-semibold">
            Confermi l'eliminazione?
          </Dialog.Title>

          <Dialog.Description className="mt-2 text-neutral-600 dark:text-neutral-400">
            Stai per eliminare <strong>{nomeDocumento}</strong>. L'operazione non è reversibile.
          </Dialog.Description>

          <div className="mt-6 flex justify-end gap-2">
            <Dialog.Close asChild>
              <button className="h-11 rounded border border-neutral-200 px-4">Annulla</button>
            </Dialog.Close>
            <Dialog.Close asChild>
              <button onClick={onConferma} className="h-11 rounded bg-red-600 px-4 text-white">
                Elimina definitivamente
              </button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
```

Radix fornisce, senza che tu scriva nulla: il portale nel `<body>`, il confinamento del focus, il ripristino del focus al comando di apertura, `Esc`, il blocco dello scorrimento, `aria-labelledby` e `aria-describedby` collegati automaticamente a `Title` e `Description`, e `role="dialog"` con `aria-modal`.

```
Gli attributi data-* che espone per lo stile:

  data-state="open" | "closed"
  data-side="top" | "right" | "bottom" | "left"
  data-align="start" | "center" | "end"
  data-disabled
  data-highlighted

Si usano come varianti Tailwind:
  data-[state=open]:animate-in
  data-[side=bottom]:slide-in-from-top-2
```

`asChild` merita attenzione: fa sì che Radix passi le sue props all'elemento figlio invece di generarne uno proprio. È ciò che permette di usare i propri componenti senza wrapper superflui.

### Il confronto

| | Radix UI | Headless UI | Ark UI |
|---|---|---|---|
| Framework | React (+ port) | React, Vue | React, Vue, Svelte, Solid |
| Numero di componenti | ~30 | ~12 | ~45 |
| Accessibilità | riferimento del settore | ottima | ottima |
| Legame con Tailwind | nessuno | dello stesso team | nessuno |
| Base | proprio | proprio | Zag.js (macchine a stati) |

Radix è la scelta più diffusa in React e la base di shadcn/ui. Ark è l'unica opzione quando servono più framework.

---

## B9. shadcn/ui: il codice è tuo

shadcn/ui non è una libreria da installare: è un catalogo di componenti che **copi nel tuo repository**. Sono Radix per il comportamento, Tailwind per lo stile, e da quel momento il codice è tuo.

```powershell
pnpm dlx shadcn@latest init
pnpm dlx shadcn@latest add button dialog dropdown-menu
```

```
Cosa succede davvero:

  src/components/ui/button.tsx     ← file NUOVI nel tuo repo
  src/components/ui/dialog.tsx
  src/lib/utils.ts                 ← la funzione cn() = clsx + twMerge

  Nessuna dipendenza da "shadcn" in package.json.
  Le dipendenze sono @radix-ui/*, class-variance-authority,
  clsx e tailwind-merge — tutte librerie ordinarie.
```

```tsx
// src/components/ui/button.tsx — un file che puoi modificare liberamente
import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md ' +
    'text-sm font-medium transition-colors focus-visible:outline-none ' +
    'focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none ' +
    'disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        default: 'h-11 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-12 rounded-md px-8',
        icon: 'h-11 w-11',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    )
  },
)
Button.displayName = 'Button'

export { Button, buttonVariants }
```

### Il tema, in variabili semantiche

```css
/* src/stile.css */
@import 'tailwindcss';

@layer base {
  :root {
    --background: oklch(100% 0 0);
    --foreground: oklch(18% 0 0);
    --primary: oklch(45% 0.18 264);
    --primary-foreground: oklch(98% 0 0);
    --destructive: oklch(55% 0.21 27);
    --destructive-foreground: oklch(98% 0 0);
    --muted: oklch(96% 0 0);
    --muted-foreground: oklch(50% 0 0);
    --border: oklch(90% 0 0);
    --ring: oklch(45% 0.18 264);
    --radius: 0.5rem;
  }

  .dark {
    --background: oklch(12% 0 0);
    --foreground: oklch(98% 0 0);
    --primary: oklch(60% 0.18 264);
    --primary-foreground: oklch(12% 0 0);
    --muted: oklch(22% 0 0);
    --muted-foreground: oklch(65% 0 0);
    --border: oklch(28% 0 0);
  }
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-destructive: var(--destructive);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-border: var(--border);
  --color-ring: var(--ring);
  --radius-lg: var(--radius);
  --radius-md: calc(var(--radius) - 2px);
  --radius-sm: calc(var(--radius) - 4px);
}
```

`@theme inline` è la variante che serve qui: i token puntano a custom properties che cambiano con il tema, invece di essere valori fissi. Senza `inline`, Tailwind risolverebbe il valore a tempo di build e il tema scuro non funzionerebbe.

```
Il compromesso di shadcn/ui:

  ✅ Nessuna dipendenza che invecchia: il codice è nel tuo repo
  ✅ Personalizzazione senza limiti: modifichi il file
  ✅ Accessibilità di Radix, senza scriverla
  ✅ Leggibile: è codice normale, non una scatola nera

  ❌ Gli aggiornamenti sono manuali: un miglioramento a monte
     non arriva da solo
  ❌ Il tuo repository cresce
  ❌ Se un componente ha un bug, lo correggi tu
```

---

## B10. Accessibilità: cosa il framework ti dà e cosa no

Nessun framework CSS rende accessibile un'applicazione. Alcuni aiutano, altri offrono trappole comode.

### Cosa arriva gratis

```
Bootstrap        markup ARIA corretto sui componenti JavaScript,
                 gestione del focus nelle modali, testo per screen reader

Radix / Headless comportamento di riferimento: focus, tastiera, ARIA,
                 annunci. È il loro unico scopo.

Tailwind         niente. È un vocabolario di dichiarazioni CSS:
                 non sa cosa stai costruendo.
```

### Le trappole ricorrenti

```html
<!-- ❌ Il contrasto non è garantito da nessuna palette.
     text-neutral-400 su bg-white è 2.6:1 — sotto il minimo di 4.5:1 -->
<p class="text-neutral-400">Testo secondario</p>

<!-- ✅ -->
<p class="text-neutral-600">Testo secondario</p>
```

```html
<!-- ❌ outline-none senza sostituto: la classe più pericolosa di Tailwind -->
<button class="outline-none">Salva</button>

<!-- ✅ -->
<button class="focus-visible:outline focus-visible:outline-2
               focus-visible:outline-offset-2 focus-visible:outline-marchio-700">
  Salva
</button>
```

```html
<!-- ❌ Un div che sembra un pulsante: le utility non danno né ruolo
     né risposta alla tastiera -->
<div class="cursor-pointer rounded bg-blue-700 px-4 py-2 text-white" onclick="salva()">
  Salva
</div>

<!-- ✅ -->
<button type="button" class="rounded bg-blue-700 px-4 py-2 text-white" onclick="salva()">
  Salva
</button>
```

```html
<!-- ❌ hidden nasconde a tutti, anche alle tecnologie assistive -->
<span class="hidden">Elimina la riga</span>

<!-- ✅ sr-only nasconde solo visivamente -->
<span class="sr-only">Elimina la riga</span>
```

```html
<!-- ❌ Bersaglio troppo piccolo: WCAG 2.5.8 chiede almeno 24×24 CSS px -->
<button class="p-1"><svg class="size-4">…</svg></button>

<!-- ✅ -->
<button class="inline-flex size-11 items-center justify-center">
  <svg class="size-5" aria-hidden="true" focusable="false">…</svg>
  <span class="sr-only">Elimina</span>
</button>
```

### Le classi che aiutano

```html
<!-- Nascondere solo visivamente -->
<span class="sr-only">Elimina la riga</span>

<!-- Visibile solo quando riceve il focus: il salto al contenuto -->
<a href="#contenuto" class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2
                            focus:z-50 focus:bg-neutral-900 focus:px-4 focus:py-3
                            focus:text-white">
  Vai al contenuto principale
</a>

<!-- Rispettare la preferenza di movimento -->
<div class="transition-transform hover:scale-105 motion-reduce:transition-none
            motion-reduce:hover:scale-100">
  …
</div>

<!-- Contrasto elevato -->
<div class="border-neutral-200 contrast-more:border-neutral-900">…</div>

<!-- Solo dove l'hover esiste -->
<div class="hover:bg-neutral-100 [@media(hover:none)]:hover:bg-transparent">…</div>
```

### Verificare, non presumere

```powershell
pnpm dlx pa11y http://localhost:5173
pnpm dlx @axe-core/cli http://localhost:5173
```

```javascript
// eslint.config.js — il plugin che intercetta gli errori nel JSX
import jsxA11y from 'eslint-plugin-jsx-a11y'

export default [
  {
    plugins: { 'jsx-a11y': jsxA11y },
    rules: {
      ...jsxA11y.configs.recommended.rules,
      'jsx-a11y/no-static-element-interactions': 'error',
      'jsx-a11y/click-events-have-key-events': 'error',
    },
  },
]
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Configurare Tailwind 4 con design token propri

**Obiettivo:** partire da un progetto Vite, installare Tailwind 4 e definire una scala di colori, tipografia e spazio propri, verificando che i token siano leggibili anche da CSS esterno.

```powershell
# SOLUZIONE — i comandi
pnpm create vite progetto-tailwind --template vanilla
cd progetto-tailwind
pnpm install
pnpm add -D tailwindcss @tailwindcss/vite
```

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],
})
```

```css
/* src/stile.css */
@import 'tailwindcss';

@theme {
  /* Azzera la palette predefinita: restano solo i token dichiarati qui.
     Impedisce che qualcuno usi bg-fuchsia-400 per sbaglio. */
  --color-*: initial;

  --color-bianco: oklch(100% 0 0);
  --color-nero: oklch(0% 0 0);

  --color-marchio-50: oklch(97% 0.02 264);
  --color-marchio-100: oklch(94% 0.04 264);
  --color-marchio-500: oklch(60% 0.18 264);
  --color-marchio-700: oklch(45% 0.18 264);
  --color-marchio-900: oklch(30% 0.12 264);

  --color-neutro-0: oklch(100% 0 0);
  --color-neutro-50: oklch(98% 0 0);
  --color-neutro-200: oklch(90% 0 0);
  --color-neutro-400: oklch(70% 0 0);
  --color-neutro-600: oklch(50% 0 0);
  --color-neutro-800: oklch(28% 0 0);
  --color-neutro-950: oklch(12% 0 0);

  --color-errore: oklch(55% 0.21 27);
  --color-successo: oklch(58% 0.16 150);
  --color-avviso: oklch(75% 0.16 75);

  /* Tipografia */
  --font-testo: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;

  --text-etichetta: 0.8125rem;
  --text-etichetta--line-height: 1.4;
  --text-etichetta--letter-spacing: 0.04em;

  --text-titolo: clamp(1.75rem, 1.2rem + 2.5vw, 3rem);
  --text-titolo--line-height: 1.15;
  --text-titolo--letter-spacing: -0.02em;

  /* Spazio: una voce aggiuntiva per le sezioni */
  --spacing-sezione: clamp(2rem, 1rem + 5vw, 6rem);

  /* Breakpoint in rem, così scalano con lo zoom del testo */
  --breakpoint-tablet: 48rem;
  --breakpoint-desktop: 72rem;
  --breakpoint-largo: 90rem;

  /* Container query */
  --container-scheda: 26rem;

  --radius-scheda: 0.75rem;
  --shadow-scheda: 0 1px 2px oklch(0% 0 0 / 0.06);
  --shadow-elevata: 0 4px 16px oklch(0% 0 0 / 0.12);
  --ease-morbida: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Una utility vera: funziona con tutte le varianti */
@utility area-lettura {
  max-inline-size: 65ch;
  margin-inline: auto;
}
```

```html
<!-- index.html — verifica che i token generino le utility -->
<div class="p-sezione">
  <h1 class="text-titolo font-testo text-marchio-900">Titolo</h1>

  <p class="text-etichetta uppercase text-neutro-600">Etichetta</p>

  <div class="rounded-scheda shadow-scheda bg-neutro-0 p-4
              tablet:grid tablet:grid-cols-2 desktop:grid-cols-3 gap-4">
    …
  </div>

  <article class="area-lettura">…</article>
</div>
```

```css
/* La verifica che conta: i token sono leggibili anche FUORI da Tailwind.
   Questo con tailwind.config.js della v3 non era possibile. */
.componente-non-tailwind {
  background: var(--color-marchio-700);
  border-radius: var(--radius-scheda);
  box-shadow: var(--shadow-scheda);
  font-family: var(--font-testo);
}
```

```powershell
# Verifica
pnpm build
Select-String -Path "dist/assets/*.css" -Pattern "--color-marchio-700"
```

```
# Output atteso — il token è nel :root del CSS prodotto:
dist\assets\index-Bx7k2Nq9.css:1:...:root{--color-marchio-700:oklch(45% 0.18 264);...

# Il che significa che:
#   1. le utility bg-marchio-700, text-marchio-700, border-marchio-700 esistono
#   2. var(--color-marchio-700) funziona da qualunque CSS
#   3. getComputedStyle lo legge da JavaScript
```

---

### Esercizio 2 — Componente con Sass, riscritto in CSS nativo

**Obiettivo:** scrivere un componente in Sass usando mixin e cicli, poi riscrivere in CSS nativo la parte che non richiede più il preprocessore, e dire cosa resta giustificato.

```scss
// SOLUZIONE — versione Sass: src/componenti/_scheda.scss
@use 'sass:map';

$varianti: (
  neutra: (bordo: #e5e5e5, accento: #525252),
  successo: (bordo: #16a34a, accento: #15803d),
  errore: (bordo: #dc2626, accento: #b91c1c),
  avviso: (bordo: #f59e0b, accento: #b45309),
);

@mixin troncamento($righe: 1) {
  display: -webkit-box;
  -webkit-line-clamp: $righe;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@mixin bersaglio-tocco($dimensione: 2.75rem) {
  min-block-size: $dimensione;
  min-inline-size: $dimensione;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.scheda {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border: 1px solid;
  border-radius: 0.5rem;

  &__titolo {
    margin: 0;
    font-size: 1.125rem;
    @include troncamento(2);
  }

  &__descrizione {
    color: #525252;
    @include troncamento(3);
  }

  &__azione {
    @include bersaglio-tocco;
    align-self: start;
    margin-block-start: auto;
  }

  // Il ciclo genera quattro varianti da una struttura dati.
  // È la cosa che il CSS nativo NON sa fare.
  @each $nome, $valori in $varianti {
    &--#{$nome} {
      border-color: map.get($valori, bordo);

      .scheda__titolo {
        color: map.get($valori, accento);
      }
    }
  }
}
```

```css
/* SOLUZIONE — versione CSS nativo: src/componenti/scheda.css
   Le varianti diventano custom properties invece di regole generate. */

.scheda {
  /* I valori di riserva definiscono la variante neutra */
  --scheda-bordo: var(--bordo, #e5e5e5);
  --scheda-accento: var(--testo-tenue, #525252);

  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border: 1px solid var(--scheda-bordo);
  border-radius: 0.5rem;

  /* Nesting nativo: & con uno spazio, NON &__ concatenato */
  & .scheda__titolo {
    margin: 0;
    font-size: 1.125rem;
    color: var(--scheda-accento);

    /* Il mixin diventa una utility, o si ripete: sono tre righe */
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  & .scheda__descrizione {
    color: var(--testo-tenue);
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  & .scheda__azione {
    min-block-size: 2.75rem;
    min-inline-size: 2.75rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    align-self: start;
    margin-block-start: auto;
  }
}

/* Le varianti: quattro regole scritte a mano invece di generate.
   Con quattro varianti è accettabile. Con quaranta, no. */
.scheda--successo {
  --scheda-bordo: var(--successo);
  --scheda-accento: var(--successo);
}

.scheda--errore {
  --scheda-bordo: var(--errore);
  --scheda-accento: var(--errore);
}

.scheda--avviso {
  --scheda-bordo: var(--avviso);
  --scheda-accento: var(--avviso);
}
```

```
# COSA RESTA GIUSTIFICATO IN SASS, dopo questo confronto:
#
#   ✅ @each su una mappa
#      Generare 40 varianti, o una scala di 12 spazi × 6 direzioni,
#      resta impossibile in CSS nativo. È il motivo più solido.
#
#   ✅ @mixin con parametri
#      @include troncamento(3) contro tre righe ripetute:
#      con dieci punti d'uso, la differenza è reale.
#
#   ✅ Funzioni di calcolo
#      math.div, color.adjust, e i calcoli su liste.
#
# COSA NON LO È PIÙ:
#
#   ❌ Variabili        → custom properties: cambiano a runtime
#   ❌ Annidamento      → nativo dal 2023
#   ❌ Media query mixin→ la sintassi a intervalli è già leggibile
#   ❌ @import          → deprecato anche in Sass, sostituito da @use
#
# ATTENZIONE alla differenza che rompe le migrazioni:
#   Sass:        &__titolo { }      → .scheda__titolo
#   CSS nativo:  NON esiste. Va scritto & .scheda__titolo { }
#
# Su un progetto nuovo: partire senza Sass. Aggiungerlo il giorno
# in cui serve un @each — non prima.
```

---

### Esercizio 3 — La classe Tailwind che sparisce in produzione

**Obiettivo:** riprodurre il bug più frequente di Tailwind, diagnosticarlo e correggerlo in tre modi diversi.

```jsx
// PARTENZA — funziona in sviluppo, si rompe in produzione
function Distintivo({ stato, children }) {
  const colore = stato === 'attivo' ? 'green' : stato === 'sospeso' ? 'amber' : 'red'
  return (
    <span className={`bg-${colore}-100 text-${colore}-800 px-2 py-1 rounded text-sm`}>
      {children}
    </span>
  )
}
```

```powershell
# LA DIAGNOSI
pnpm build
Select-String -Path "dist/assets/*.css" -Pattern "bg-green-100"
```

```
# Output atteso: NESSUN RISULTATO.
#
# Perché: Tailwind scansiona i file come TESTO. Non esegue il codice,
# non valuta i template literal. Nel sorgente vede:
#
#     `bg-${colore}-100`
#
# e non trova mai la stringa "bg-green-100". La classe non viene
# generata, e in produzione lo sfondo manca.
#
# In sviluppo può sembrare funzionare se quella classe è usata
# altrove nel progetto: è ciò che rende il bug insidioso.
```

```jsx
// ✅ CORREZIONE 1 — mappa di classi complete.
//    La soluzione da preferire: leggibile, esplicita, tipizzabile.
const CLASSI_STATO = {
  attivo: 'bg-green-100 text-green-800',
  sospeso: 'bg-amber-100 text-amber-800',
  cessato: 'bg-red-100 text-red-800',
}

function Distintivo({ stato = 'cessato', children }) {
  return (
    <span className={`${CLASSI_STATO[stato]} px-2 py-1 rounded text-sm`}>
      {children}
    </span>
  )
}
```

```jsx
// ✅ CORREZIONE 2 — cva, quando le varianti sono molte
import { cva } from 'class-variance-authority'

const distintivo = cva('px-2 py-1 rounded text-sm font-medium', {
  variants: {
    stato: {
      attivo: 'bg-green-100 text-green-800',
      sospeso: 'bg-amber-100 text-amber-800',
      cessato: 'bg-red-100 text-red-800',
    },
  },
  defaultVariants: { stato: 'cessato' },
})

function Distintivo({ stato, children }) {
  return <span className={distintivo({ stato })}>{children}</span>
}
```

```css
/* ✅ CORREZIONE 3 — @source inline, quando i valori arrivano
   da fuori dal codice: un CMS, un database, un'API */
@import 'tailwindcss';

@source inline('bg-{green,amber,red}-100 text-{green,amber,red}-800');
```

```jsx
// Solo con la correzione 3 il template literal resta legittimo,
// perché le classi sono state registrate esplicitamente.
function Distintivo({ colore, children }) {
  return <span className={`bg-${colore}-100 text-${colore}-800 px-2 py-1 rounded`}>
    {children}
  </span>
}
```

```powershell
# LA VERIFICA, dopo ogni correzione
pnpm build
Select-String -Path "dist/assets/*.css" -Pattern "bg-green-100"
```

```
# Output atteso ora:
dist\assets\index-Bx7k2Nq9.css:1:...bg-green-100{background-color:oklch(...)}...

# La regola generale che riassume tutto:
#   Una classe Tailwind deve comparire nel sorgente come
#   STRINGA COMPLETA E CONTIGUA. Non composta, non concatenata,
#   non calcolata.
```

---

### Esercizio 4 — Bootstrap personalizzato: da 230 kB a meno di 100

**Obiettivo:** partire da Bootstrap completo, personalizzarlo via Sass e importare solo i moduli necessari, misurando il risultato.

```powershell
# SOLUZIONE
pnpm create vite prototipo-bootstrap --template vanilla
cd prototipo-bootstrap
pnpm install
pnpm add bootstrap
pnpm add -D sass
```

```scss
// src/bootstrap-personalizzato.scss

// ── 1. Funzioni ──────────────────────────────────────────────
// Servono alle variabili che seguono (tint-color, shade-color)
@import 'bootstrap/scss/functions';

// ── 2. LE TUE variabili, PRIMA dei default ───────────────────
// Bootstrap dichiara le proprie con !default: una variabile
// già definita non viene sovrascritta.
$primary: #1d4ed8;
$secondary: #525252;
$success: #16a34a;
$danger: #dc2626;
$warning: #f59e0b;

$font-family-sans-serif: 'Inter', system-ui, -apple-system, sans-serif;
$font-size-base: 1rem;
$line-height-base: 1.6;

$border-radius: 0.5rem;
$border-radius-sm: 0.25rem;
$border-radius-lg: 0.75rem;

$btn-padding-y: 0.625rem;
$btn-padding-x: 1rem;
$btn-font-weight: 500;

// Disattivare ciò che non usi: ogni flag toglie regole dal file finale
$enable-shadows: false;
$enable-gradients: false;
$enable-smooth-scroll: false;
$enable-cssgrid: false;

// ── 3. I default di Bootstrap ────────────────────────────────
@import 'bootstrap/scss/variables';
@import 'bootstrap/scss/variables-dark';
@import 'bootstrap/scss/maps';
@import 'bootstrap/scss/mixins';
@import 'bootstrap/scss/root';

// ── 4. SOLO i moduli che servono ─────────────────────────────
@import 'bootstrap/scss/reboot';
@import 'bootstrap/scss/type';
@import 'bootstrap/scss/containers';
@import 'bootstrap/scss/grid';
@import 'bootstrap/scss/tables';
@import 'bootstrap/scss/forms';
@import 'bootstrap/scss/buttons';
@import 'bootstrap/scss/card';
@import 'bootstrap/scss/nav';
@import 'bootstrap/scss/navbar';
@import 'bootstrap/scss/modal';
@import 'bootstrap/scss/alert';
@import 'bootstrap/scss/badge';

// NON importati: accordion, carousel, offcanvas, toast, tooltip,
// popover, spinners, progress, list-group, pagination, breadcrumb,
// dropdown, button-group, close, placeholders

// ── 5. Utility ───────────────────────────────────────────────
@import 'bootstrap/scss/helpers';
@import 'bootstrap/scss/utilities';

// Utility proprie, aggiunte all'API prima di generarle
$utilities: map-merge(
  $utilities,
  (
    'cursor': (
      property: cursor,
      class: cursor,
      values: auto pointer grab not-allowed,
    ),
    'tabular': (
      property: font-variant-numeric,
      class: fvn,
      values: (tabular: tabular-nums),
    ),
  )
);

@import 'bootstrap/scss/utilities/api';
```

```javascript
// src/main.js
import './bootstrap-personalizzato.scss'

// Solo i moduli JavaScript necessari, invece del bundle intero
import Modal from 'bootstrap/js/dist/modal'
import Collapse from 'bootstrap/js/dist/collapse'
```

```powershell
# LA MISURA
pnpm build
Get-ChildItem dist/assets/*.css, dist/assets/*.js |
  Select-Object Name, @{n='kB';e={[math]::Round($_.Length/1kb,1)}}
```

```
# Output atteso — confronto delle tre configurazioni:
#
#                                          CSS      JS
#   bootstrap.min.css + bundle.js         232 kB   80 kB
#   solo i moduli elencati sopra           94 kB   22 kB
#   + purge delle classi inutilizzate      31 kB   22 kB
#
# La differenza sta quasi tutta nei componenti mai usati:
# carousel, accordion, offcanvas, tooltip e popover da soli
# pesano oltre 40 kB di CSS.
```

```
# PERCHÉ le variabili Sass e non le sovrascritture:
#
#   $primary: #1d4ed8 si propaga a:
#     .btn-primary, .btn-outline-primary, .text-primary, .bg-primary,
#     .border-primary, .link-primary, .alert-primary, .badge.bg-primary,
#     .list-group-item-primary, .progress-bar, .form-check-input:checked,
#     .nav-pills .nav-link.active, .page-item.active .page-link
#
#   Ottenere lo stesso con le sovrascritture richiede almeno
#   quaranta regole, ognuna con i suoi stati :hover, :focus,
#   :active e .disabled. E ogni aggiornamento di Bootstrap
#   può aggiungerne di nuove che non hai sovrascritto.
```

---

### Esercizio 5 — Scegliere l'approccio, con un criterio

**Obiettivo:** dati cinque scenari reali, motivare la scelta dell'approccio CSS.

```
# SCENARIO 1
# Pannello di amministrazione interno. Due sviluppatori, nessun designer,
# sei settimane di tempo. L'aspetto deve essere professionale, non originale.

# SCELTA: Bootstrap, o un catalogo equivalente.
#
# Motivo: il valore qui è la velocità, e "somiglia agli altri pannelli"
# non è un difetto — è un vantaggio, perché gli utenti riconoscono
# i pattern. Modali, tabelle, form e navigazione arrivano già
# accessibili e testati.
# Costo accettato: personalizzare oltre le variabili Sass sarà scomodo.
# Se il progetto durasse anni con un design proprio, sarebbe la scelta sbagliata.


# SCENARIO 2
# Prodotto SaaS. Design system proprio disegnato da un designer,
# otto sviluppatori, React, orizzonte pluriennale.

# SCELTA: Tailwind 4 + shadcn/ui + Radix.
#
# Motivo: il design è proprio, quindi un catalogo di componenti
# sarebbe da combattere. Tailwind dà i vincoli (nessuno scrive
# padding: 15px) senza imporre un aspetto. Radix dà il comportamento
# accessibile, che con otto persone nessuno riscriverebbe bene
# ogni volta. shadcn/ui mette il codice nel repository, quindi
# la personalizzazione non ha limiti.
# Costo accettato: markup verboso, mitigato estraendo i componenti.


# SCENARIO 3
# Sito editoriale. Contenuti da un CMS, molto testo, priorità
# assoluta alle Core Web Vitals, poco JavaScript.

# SCELTA: CSS nativo, con custom properties e @layer.
#
# Motivo: le pagine sono poche e ripetitive; il CSS non crescerà.
# Nessun passo di build significa nessuna complessità e nessun
# JavaScript aggiunto. Le container query e :has() coprono
# ciò per cui prima servivano i framework.
# Se il CMS produce HTML che non controlli, @scope isola
# il contenuto dagli stili del tema.


# SCENARIO 4
# Widget incorporabile in siti di terzi. Non conosci il CSS
# della pagina ospite e non puoi toccarlo.

# SCELTA: Web Components con Shadow DOM, e CSS dentro lo shadow root.
#
# Motivo: è l'unico approccio che garantisce isolamento in ENTRAMBE
# le direzioni — il CSS della pagina ospite non entra, il tuo non esce.
# Tailwind qui non aiuta: le sue utility sono globali e verrebbero
# comunque sovrascritte dal foglio di stile dell'ospite, o lo
# sovrascriverebbero.
# La personalizzazione da parte dell'ospite si espone con
# custom properties dichiarate come contratto pubblico.


# SCENARIO 5
# Applicazione esistente, 80.000 righe di CSS legacy con Sass e BEM.
# Il team vuole passare a Tailwind senza fermare lo sviluppo.

# SCELTA: convivenza tramite @layer, migrazione per componenti.
#
#   @layer legacy, tailwind;
#   @import 'stile-legacy.css' layer(legacy);
#   @import 'tailwindcss' layer(tailwind);
#
# Motivo: il layer Tailwind viene dopo, quindi le utility vincono
# sempre sul CSS legacy — senza !important e senza toccare
# 80.000 righe. Ogni componente si migra quando lo si tocca
# per altri motivi. Il CSS legacy si assottiglia da solo.
# Vedi D4 per la procedura completa.
```

```
# IL CRITERIO, in tre domande:
#
#   1. Il design è mio o va bene quello di un catalogo?
#        catalogo  → component-based (Bootstrap)
#        mio       → prosegui
#
#   2. Quanto durerà, e quante persone ci lavorano?
#        breve, 1-2 persone   → CSS nativo
#        lungo, team          → prosegui
#
#   3. C'è un linguaggio di componenti (React, Vue, Svelte)?
#        sì   → Tailwind + headless, oppure CSS Modules
#        no   → CSS nativo con @layer, oppure Tailwind con @apply
#
# La domanda che NON va posta: "qual è il migliore".
# Nessuno di questi approcci è migliore in astratto,
# e l'errore più costoso è sceglierne uno per abitudine.
```

---

### Esercizio 6 — Misurare il costo reale del CSS

**Obiettivo:** uno script che estragga da una build le metriche che contano, per confrontare due approcci con dei numeri invece che con delle opinioni.

```javascript
// scripts/misura-css.js
// Uso: node scripts/misura-css.js dist

import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { gzipSync, brotliCompressSync } from 'node:zlib'

const cartella = process.argv[2] ?? 'dist'

/** Elenca ricorsivamente i file con una data estensione. */
function trovaFile(percorso, estensione, trovati = []) {
  for (const voce of readdirSync(percorso)) {
    const completo = join(percorso, voce)
    if (statSync(completo).isDirectory()) {
      trovaFile(completo, estensione, trovati)
    } else if (voce.endsWith(estensione)) {
      trovati.push(completo)
    }
  }
  return trovati
}

/**
 * Conta le regole di un foglio di stile senza analizzarlo davvero:
 * bastano le graffe di apertura fuori dalle at-rule annidate.
 * Approssimazione sufficiente per un confronto.
 */
function statistiche(css) {
  const senzaCommenti = css.replace(/\/\*[\s\S]*?\*\//g, '')

  return {
    regole: (senzaCommenti.match(/\{/g) ?? []).length,
    mediaQuery: (senzaCommenti.match(/@media/g) ?? []).length,
    containerQuery: (senzaCommenti.match(/@container/g) ?? []).length,
    layer: (senzaCommenti.match(/@layer/g) ?? []).length,
    customProperties: new Set(senzaCommenti.match(/--[\w-]+(?=\s*:)/g) ?? []).size,
    important: (senzaCommenti.match(/!important/g) ?? []).length,
    selettoriConId: (senzaCommenti.match(/#[\w-]+\s*[,{]/g) ?? []).length,
  }
}

function formattaKb(byte) {
  return `${(byte / 1024).toFixed(1)} kB`
}

const fogli = trovaFile(cartella, '.css')

if (fogli.length === 0) {
  console.error(`Nessun file .css trovato in ${cartella}. Hai eseguito la build?`)
  process.exit(1)
}

let totaleGrezzo = 0
let totaleGzip = 0
let totaleBrotli = 0
const complessivo = {
  regole: 0,
  mediaQuery: 0,
  containerQuery: 0,
  layer: 0,
  customProperties: 0,
  important: 0,
  selettoriConId: 0,
}

console.log('CSS prodotto\n')

for (const percorso of fogli) {
  const contenuto = readFileSync(percorso)
  const testo = contenuto.toString('utf8')

  const grezzo = contenuto.length
  const gzip = gzipSync(contenuto).length
  const brotli = brotliCompressSync(contenuto).length

  totaleGrezzo += grezzo
  totaleGzip += gzip
  totaleBrotli += brotli

  const stat = statistiche(testo)
  for (const chiave of Object.keys(complessivo)) {
    complessivo[chiave] += stat[chiave]
  }

  console.log(`  ${percorso}`)
  console.log(
    `    ${formattaKb(grezzo)} grezzo · ${formattaKb(gzip)} gzip · ${formattaKb(brotli)} brotli`,
  )
  console.log(`    ${stat.regole} regole · ${stat.customProperties} custom properties`)
}

console.log('\nTotale')
console.log(
  `  ${formattaKb(totaleGrezzo)} grezzo · ${formattaKb(totaleGzip)} gzip · ${formattaKb(totaleBrotli)} brotli`,
)
console.log(`  regole:            ${complessivo.regole}`)
console.log(`  media query:       ${complessivo.mediaQuery}`)
console.log(`  container query:   ${complessivo.containerQuery}`)
console.log(`  @layer:            ${complessivo.layer}`)
console.log(`  custom properties: ${complessivo.customProperties}`)

// Le due metriche che segnalano un problema di architettura
if (complessivo.important > 0) {
  console.log(`\n  ⚠ ${complessivo.important} !important — considera @layer`)
}
if (complessivo.selettoriConId > 0) {
  console.log(`  ⚠ ${complessivo.selettoriConId} selettori con id — specificità (1,0,0)`)
}

// Soglia indicativa: oltre 50 kB gzip il CSS pesa sul First Contentful Paint
if (totaleGzip > 50 * 1024) {
  console.log(`\n  ⚠ ${formattaKb(totaleGzip)} gzip: valuta il code splitting del CSS`)
}
```

```
# Output atteso su un progetto Tailwind:
CSS prodotto

  dist/assets/index-Bx7k2Nq9.css
    28.4 kB grezzo · 6.9 kB gzip · 5.4 kB brotli
    412 regole · 87 custom properties

Totale
  28.4 kB grezzo · 6.9 kB gzip · 5.4 kB brotli
  regole:            412
  media query:       9
  container query:   3
  @layer:            4
  custom properties: 87
```

```
# Il confronto che questo script permette, sullo stesso progetto:
#
#                              grezzo    gzip    regole  !important
#   Bootstrap completo         232 kB   31 kB     2.400       12
#   Bootstrap solo moduli usati 94 kB   16 kB       980        4
#   Tailwind 4                  28 kB    7 kB       412        0
#   CSS nativo scritto a mano   41 kB    9 kB       520        2
#   CSS Modules                 35 kB    8 kB       470        0
#
# Le due colonne che raccontano di più:
#
#   'regole' cresce con il progetto in tutti gli approcci
#   TRANNE che nelle utility, dove satura: le classi si riusano.
#
#   '!important' e 'selettori con id' misurano il debito
#   di architettura. Zero non è un obiettivo estetico:
#   ogni !important è una sovrascrittura che qualcuno dovrà
#   scavalcare in futuro.
#
# ATTENZIONE: la dimensione del CSS non è l'unica metrica.
# Un bundle CSS di 7 kB con 40 kB di JavaScript per generarlo
# (CSS-in-JS runtime) costa più di 30 kB di CSS statico.
# Va sempre misurato l'insieme.
```

---

## C2. Mini-progetto: la dashboard, ricostruita con Tailwind

L'esercizio chiave del modulo: riprendere la dashboard costruita in CSS puro in `tutorial_02_css3.md` e ricostruirla con Tailwind 4, per confrontare produttività e manutenibilità sullo stesso risultato.

### Il confronto va fatto sulle stesse cose

```
Stesso risultato visivo, stesse funzionalità:
  · layout a tre configurazioni
  · tema chiaro/scuro a tre stati
  · schede che si adattano al contenitore
  · tabella scorrevole con intestazioni fisse
  · barra laterale a scomparsa su mobile
  · accessibilità: focus visibile, sr-only, bersagli da 44px

Cosa misureremo alla fine:
  · righe di CSS scritte a mano
  · dimensione del CSS prodotto
  · righe di markup
  · tempo per aggiungere una variante nuova
```

### Struttura

```
dashboard-tailwind/
├── index.html
├── vite.config.js
└── src/
    ├── stile.css        @import + @theme: tutto il CSS del progetto
    └── tema.js          il selettore di tema, identico a tutorial_02
```

Due file invece di sei. È già un dato.

### `vite.config.js`

```javascript
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],
})
```

### `src/stile.css`

```css
@import 'tailwindcss';

/* Tema comandato da un attributo invece che dalla sola media query:
   serve per il selettore a tre stati. */
@custom-variant dark (&:where([data-tema='scuro'], [data-tema='scuro'] *));

@theme {
  --color-*: initial;

  --color-bianco: oklch(100% 0 0);

  --color-marchio-50: oklch(97% 0.02 264);
  --color-marchio-100: oklch(94% 0.04 264);
  --color-marchio-500: oklch(60% 0.18 264);
  --color-marchio-700: oklch(45% 0.18 264);
  --color-marchio-900: oklch(30% 0.12 264);

  --color-neutro-0: oklch(100% 0 0);
  --color-neutro-50: oklch(98% 0 0);
  --color-neutro-200: oklch(90% 0 0);
  --color-neutro-400: oklch(70% 0 0);
  --color-neutro-600: oklch(50% 0 0);
  --color-neutro-800: oklch(28% 0 0);
  --color-neutro-900: oklch(18% 0 0);
  --color-neutro-950: oklch(12% 0 0);

  --color-successo: oklch(58% 0.16 150);
  --color-errore: oklch(55% 0.21 27);

  --font-testo: 'Inter', system-ui, -apple-system, sans-serif;

  --text-valore: clamp(1.75rem, 1.2rem + 2.5vw, 3rem);
  --text-valore--line-height: 1;

  --breakpoint-tablet: 48rem;
  --breakpoint-desktop: 72rem;

  --container-scheda: 22rem;

  --radius-scheda: 0.5rem;
  --shadow-scheda: 0 1px 2px oklch(0% 0 0 / 0.06);
  --shadow-elevata: 0 4px 12px oklch(0% 0 0 / 0.1);
}

/* Stile degli elementi: il poco CSS scritto a mano che resta */
@layer base {
  html {
    color-scheme: light dark;
  }

  body {
    font-family: var(--font-testo);
    background: var(--color-neutro-50);
    color: var(--color-neutro-900);
  }

  [data-tema='scuro'] body {
    background: var(--color-neutro-950);
    color: var(--color-neutro-50);
  }

  @media (prefers-color-scheme: dark) {
    :root:not([data-tema='chiaro']) body {
      background: var(--color-neutro-950);
      color: var(--color-neutro-50);
    }
  }

  /* La preferenza di movimento: l'unico blocco che Tailwind
     non copre a livello globale */
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
}

/* Una utility propria: la misura di lettura */
@utility area-lettura {
  max-inline-size: 65ch;
  margin-inline: auto;
}
```

Il CSS scritto a mano è finito qui: circa 70 righe, contro le oltre 600 della versione in CSS puro.

### `index.html`

```html
<!doctype html>
<html lang="it">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Dashboard — Acme S.p.A.</title>
    <meta name="color-scheme" content="light dark" />

    <script>
      const t = localStorage.getItem('tema-preferito')
      if (t && t !== 'sistema') document.documentElement.dataset.tema = t
    </script>

    <link rel="stylesheet" href="/src/stile.css" />
  </head>

  <body class="min-h-dvh">
    <a
      href="#contenuto"
      class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50
             focus:rounded focus:bg-neutro-900 focus:px-4 focus:py-3 focus:text-neutro-0"
    >
      Vai al contenuto principale
    </a>

    <div
      class="grid min-h-dvh grid-rows-[3.5rem_1fr_auto]
             tablet:grid-cols-[15rem_1fr]
             tablet:grid-areas-[testata_testata,barra_contenuto,fondo_fondo]"
    >
      <!-- ── Testata ─────────────────────────────────────────── -->
      <header
        class="sticky top-0 z-20 flex items-center justify-between gap-4 border-b
               border-neutro-200 bg-neutro-0 px-4
               dark:border-neutro-800 dark:bg-neutro-900
               tablet:col-span-2"
      >
        <button
          type="button"
          popovertarget="barra-mobile"
          class="inline-flex size-11 items-center justify-center rounded border
                 border-neutro-200 focus-visible:outline focus-visible:outline-2
                 focus-visible:outline-offset-2 focus-visible:outline-marchio-700
                 dark:border-neutro-800 tablet:hidden"
        >
          <span aria-hidden="true">☰</span>
          <span class="sr-only">Apri il menu di navigazione</span>
        </button>

        <strong>Acme S.p.A.</strong>

        <fieldset class="flex gap-1">
          <legend class="sr-only">Aspetto</legend>
          <button
            type="button"
            data-imposta-tema="chiaro"
            aria-pressed="false"
            class="h-9 rounded border border-neutro-200 px-3 text-sm
                   aria-pressed:border-marchio-700 aria-pressed:bg-marchio-50
                   aria-pressed:text-marchio-900 focus-visible:outline
                   focus-visible:outline-2 focus-visible:outline-offset-2
                   focus-visible:outline-marchio-700 dark:border-neutro-800"
          >
            Chiaro
          </button>
          <button
            type="button"
            data-imposta-tema="scuro"
            aria-pressed="false"
            class="h-9 rounded border border-neutro-200 px-3 text-sm
                   aria-pressed:border-marchio-700 aria-pressed:bg-marchio-50
                   aria-pressed:text-marchio-900 dark:border-neutro-800"
          >
            Scuro
          </button>
          <button
            type="button"
            data-imposta-tema="sistema"
            aria-pressed="true"
            class="h-9 rounded border border-neutro-200 px-3 text-sm
                   aria-pressed:border-marchio-700 aria-pressed:bg-marchio-50
                   aria-pressed:text-marchio-900 dark:border-neutro-800"
          >
            Sistema
          </button>
        </fieldset>
      </header>

      <!-- ── Barra laterale (da tablet in su) ─────────────────── -->
      <nav
        class="hidden border-r border-neutro-200 bg-neutro-0 p-4
               dark:border-neutro-800 dark:bg-neutro-900 tablet:block"
        aria-label="Principale"
      >
        <ul class="flex flex-col gap-1">
          <li>
            <a
              href="/"
              aria-current="page"
              class="block rounded px-3 py-2 aria-[current=page]:bg-marchio-50
                     aria-[current=page]:font-semibold aria-[current=page]:text-marchio-900
                     hover:bg-neutro-50 dark:hover:bg-neutro-800
                     dark:aria-[current=page]:bg-marchio-900/30"
            >
              Panoramica
            </a>
          </li>
          <li>
            <a href="/fatture" class="block rounded px-3 py-2 hover:bg-neutro-50
                                       dark:hover:bg-neutro-800">Fatture</a>
          </li>
          <li>
            <a href="/clienti" class="block rounded px-3 py-2 hover:bg-neutro-50
                                       dark:hover:bg-neutro-800">Clienti</a>
          </li>
          <li>
            <a href="/report" class="block rounded px-3 py-2 hover:bg-neutro-50
                                      dark:hover:bg-neutro-800">Report</a>
          </li>
        </ul>
      </nav>

      <!-- ── Contenuto ───────────────────────────────────────── -->
      <main
        id="contenuto"
        tabindex="-1"
        class="@container mx-auto flex w-full max-w-[80rem] flex-col gap-8 p-4 tablet:p-6"
      >
        <h1 class="text-3xl font-bold">Panoramica</h1>

        <section class="flex flex-col gap-3" aria-labelledby="titolo-indicatori">
          <h2 id="titolo-indicatori" class="text-xl font-semibold">
            Indicatori del trimestre
          </h2>

          <div class="grid gap-4 grid-cols-[repeat(auto-fit,minmax(min(18rem,100%),1fr))]">
            <!-- La scheda: @container sull'involucro -->
            <div class="@container">
              <article
                class="flex flex-col gap-2 rounded-scheda border border-neutro-200
                       bg-neutro-0 p-4 shadow-scheda transition
                       hover:-translate-y-0.5 hover:shadow-elevata
                       motion-reduce:transform-none motion-reduce:transition-none
                       dark:border-neutro-800 dark:bg-neutro-900
                       @scheda:grid @scheda:grid-cols-[1fr_auto] @scheda:items-center"
              >
                <p class="text-sm uppercase tracking-wide text-neutro-600 dark:text-neutro-400">
                  Ricavi
                </p>
                <p class="text-valore font-bold tabular-nums @scheda:col-start-2 @scheda:row-span-2">
                  1.330
                </p>
                <p class="inline-flex items-center gap-1 text-sm font-semibold text-successo">
                  <span aria-hidden="true">▲</span> 12,4%
                  <span class="sr-only">in aumento rispetto al trimestre precedente</span>
                </p>
              </article>
            </div>

            <div class="@container">
              <article
                class="flex flex-col gap-2 rounded-scheda border border-neutro-200
                       bg-neutro-0 p-4 shadow-scheda dark:border-neutro-800
                       dark:bg-neutro-900"
              >
                <p class="text-sm uppercase tracking-wide text-neutro-600 dark:text-neutro-400">
                  Fatture emesse
                </p>
                <p class="text-valore font-bold tabular-nums">248</p>
                <p class="inline-flex items-center gap-1 text-sm font-semibold text-successo">
                  <span aria-hidden="true">▲</span> 3,1%
                  <span class="sr-only">in aumento</span>
                </p>
              </article>
            </div>

            <div class="@container">
              <article
                class="flex flex-col gap-2 rounded-scheda border border-neutro-200
                       bg-neutro-0 p-4 shadow-scheda dark:border-neutro-800
                       dark:bg-neutro-900"
              >
                <p class="text-sm uppercase tracking-wide text-neutro-600 dark:text-neutro-400">
                  Insoluti
                </p>
                <p class="text-valore font-bold tabular-nums">17</p>
                <p class="inline-flex items-center gap-1 text-sm font-semibold text-errore">
                  <span aria-hidden="true">▼</span> 8,2%
                  <span class="sr-only">in diminuzione</span>
                </p>
              </article>
            </div>
          </div>
        </section>

        <section class="flex flex-col gap-3" aria-labelledby="titolo-tabella">
          <h2 id="titolo-tabella" class="text-xl font-semibold">Ricavi per divisione</h2>

          <div
            role="region"
            aria-labelledby="titolo-tabella"
            tabindex="0"
            class="overflow-x-auto rounded-scheda border border-neutro-200 bg-neutro-0
                   focus-visible:outline focus-visible:outline-2
                   focus-visible:outline-marchio-700
                   dark:border-neutro-800 dark:bg-neutro-900"
          >
            <table class="w-full border-collapse">
              <caption class="p-4 text-left font-semibold">
                Esercizio 2026, in migliaia di euro
              </caption>
              <thead>
                <tr>
                  <th
                    scope="col"
                    class="sticky top-0 border-b border-neutro-200 bg-neutro-50 px-4 py-3
                           text-left text-sm uppercase tracking-wide
                           dark:border-neutro-800 dark:bg-neutro-800"
                  >
                    Divisione
                  </th>
                  <th
                    scope="col"
                    class="sticky top-0 border-b border-neutro-200 bg-neutro-50 px-4 py-3
                           text-right text-sm uppercase tracking-wide
                           dark:border-neutro-800 dark:bg-neutro-800"
                  >
                    T1
                  </th>
                  <th
                    scope="col"
                    class="sticky top-0 border-b border-neutro-200 bg-neutro-50 px-4 py-3
                           text-right text-sm uppercase tracking-wide
                           dark:border-neutro-800 dark:bg-neutro-800"
                  >
                    T2
                  </th>
                  <th
                    scope="col"
                    class="sticky top-0 border-b border-neutro-200 bg-neutro-50 px-4 py-3
                           text-right text-sm uppercase tracking-wide
                           dark:border-neutro-800 dark:bg-neutro-800"
                  >
                    Totale
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr class="hover:bg-neutro-50 dark:hover:bg-neutro-800">
                  <th scope="row" class="border-b border-neutro-200 px-4 py-3 text-left
                                          font-normal dark:border-neutro-800">
                    Industriale
                  </th>
                  <td class="border-b border-neutro-200 px-4 py-3 text-right tabular-nums
                             dark:border-neutro-800">610</td>
                  <td class="border-b border-neutro-200 px-4 py-3 text-right tabular-nums
                             dark:border-neutro-800">630</td>
                  <td class="border-b border-neutro-200 px-4 py-3 text-right tabular-nums
                             dark:border-neutro-800">1.240</td>
                </tr>
                <tr class="hover:bg-neutro-50 dark:hover:bg-neutro-800">
                  <th scope="row" class="px-4 py-3 text-left font-normal">Servizi</th>
                  <td class="px-4 py-3 text-right tabular-nums">420</td>
                  <td class="px-4 py-3 text-right tabular-nums">440</td>
                  <td class="px-4 py-3 text-right tabular-nums">860</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </main>

      <footer
        class="border-t border-neutro-200 p-4 text-sm text-neutro-600
               dark:border-neutro-800 dark:text-neutro-400 tablet:col-span-2"
      >
        <p>© 2026 Acme S.p.A. — dati aggiornati al 28 aprile 2026</p>
      </footer>
    </div>

    <!-- ── Barra laterale mobile ─────────────────────────────── -->
    <div
      id="barra-mobile"
      popover
      class="m-0 mr-auto h-dvh max-h-dvh w-[min(20rem,85vw)] border-r border-neutro-200
             bg-neutro-0 p-4 backdrop:bg-black/50
             dark:border-neutro-800 dark:bg-neutro-900"
    >
      <nav aria-label="Principale (mobile)">
        <ul class="flex flex-col gap-1">
          <li>
            <a href="/" aria-current="page"
               class="block rounded px-3 py-2 aria-[current=page]:bg-marchio-50
                      aria-[current=page]:font-semibold aria-[current=page]:text-marchio-900">
              Panoramica
            </a>
          </li>
          <li><a href="/fatture" class="block rounded px-3 py-2 hover:bg-neutro-50">Fatture</a></li>
          <li><a href="/clienti" class="block rounded px-3 py-2 hover:bg-neutro-50">Clienti</a></li>
          <li><a href="/report" class="block rounded px-3 py-2 hover:bg-neutro-50">Report</a></li>
        </ul>
      </nav>
    </div>

    <script type="module" src="/src/tema.js"></script>
  </body>
</html>
```

### Il confronto, con i numeri

```powershell
pnpm build
node scripts/misura-css.js dist
```

```
# Confronto con la versione in CSS puro di tutorial_02:
#
#                              CSS puro    Tailwind 4
#   ─────────────────────────────────────────────────
#   File CSS del progetto            6            1
#   Righe di CSS scritte a mano    ~640          ~70
#   CSS prodotto (gzip)           9,1 kB       6,8 kB
#   Righe di markup                ~190         ~260
#   Regole nel CSS finale           520          412
#
# Cosa dicono davvero questi numeri:
#
#   · Il CSS scritto a mano crolla di dieci volte. È il guadagno
#     principale, e cresce con la dimensione del progetto.
#
#   · Il markup cresce del 35%. È il costo, ed è reale.
#     In un progetto con React o Vue sparirebbe quasi del tutto
#     estraendo i componenti — qui non c'è un linguaggio
#     di componenti, quindi si vede tutto.
#
#   · Il CSS prodotto è più piccolo nonostante ci siano più
#     dichiarazioni, perché le utility si riusano: la terza scheda
#     non aggiunge una riga di CSS.
#
# LA PROVA CHE CONTA, e che i numeri non mostrano:
#   aggiungi una quarta scheda. Nella versione CSS puro
#   non serve toccare il CSS — la classe .scheda c'è già.
#   Nella versione Tailwind nemmeno.
#
#   Ora aggiungi una scheda con una VARIANTE nuova
#   (bordo colorato secondo lo stato):
#     CSS puro  → una regola nuova nel foglio di stile,
#                 che resterà lì per sempre
#     Tailwind  → tre utility nel markup, che spariscono
#                 insieme all'elemento se lo cancelli
#
#   È questa asimmetria — non la dimensione del bundle —
#   il motivo per cui il CSS utility-first ha preso piede.
```

```
# CONTROLLI DA FARE, identici a tutorial_02:
#
# 1. Le tre configurazioni di layout, restringendo la finestra
# 2. Le container query: restringi SOLO il <main> con DevTools
# 3. Il tema a tre stati, con la scelta esplicita che vince
# 4. Zoom al 200%: nessuno scorrimento orizzontale
# 5. Tab dall'inizio: salto al contenuto, poi il menu
# 6. prefers-reduced-motion: le transizioni spariscono
# 7. Contrasto in entrambi i temi
#
# Il risultato deve essere indistinguibile dalla versione
# in CSS puro. Se non lo è, il confronto non è valido.
```

---

# Parte D — Approfondimento per Esperti

---

## D1. UnoCSS e il CSS atomico su misura

UnoCSS non è un framework: è un **motore** per generare CSS atomico, con i preset che scegli. Il preset `wind` riproduce la sintassi di Tailwind; gli altri fanno cose che Tailwind non fa.

```powershell
pnpm add -D unocss
```

```javascript
// uno.config.js
import {
  defineConfig,
  presetWind4,
  presetAttributify,
  presetIcons,
  presetTypography,
  transformerDirectives,
  transformerVariantGroup,
} from 'unocss'

export default defineConfig({
  presets: [
    presetWind4(),          // la sintassi di Tailwind
    presetAttributify(),    // le utility come attributi
    presetIcons({           // le icone come classi, senza componenti
      scale: 1.2,
      extraProperties: { display: 'inline-block', 'vertical-align': 'middle' },
    }),
    presetTypography(),
  ],

  transformers: [
    transformerDirectives(),      // abilita @apply
    transformerVariantGroup(),    // hover:(bg-blue-700 text-white)
  ],

  // Regole proprie, con espressioni regolari
  rules: [
    ['area-lettura', { 'max-inline-size': '65ch', 'margin-inline': 'auto' }],
    [/^troncato-(\d+)$/, ([, n]) => ({
      display: '-webkit-box',
      '-webkit-line-clamp': n,
      '-webkit-box-orient': 'vertical',
      overflow: 'hidden',
    })],
  ],

  // Abbreviazioni: un nome per un insieme di utility
  shortcuts: {
    'pulsante':
      'inline-flex h-11 items-center justify-center rounded px-4 font-medium transition',
    'pulsante-primario': 'pulsante bg-marchio-700 text-white hover:bg-marchio-900',
    'scheda': 'rounded-lg border border-neutro-200 bg-white p-4 shadow-sm',
  },

  theme: {
    colors: {
      marchio: {
        500: 'oklch(60% 0.18 264)',
        700: 'oklch(45% 0.18 264)',
        900: 'oklch(30% 0.12 264)',
      },
    },
  },
})
```

### Le due cose che UnoCSS fa e Tailwind no

**Le icone come classi.** Nessun componente, nessun import: l'icona è una classe, e finisce nel CSS come `background-image` con un SVG in linea.

```powershell
pnpm add -D @iconify-json/lucide @iconify-json/simple-icons
```

```html
<!-- Nessun import, nessun componente. Solo la classe. -->
<span class="i-lucide-download text-xl"></span>
<span class="i-lucide-trash-2 text-red-600"></span>
<span class="i-simple-icons-github"></span>

<!-- Le varianti funzionano come su qualunque utility -->
<span class="i-lucide-chevron-down transition group-open:rotate-180"></span>
```

Solo le icone effettivamente usate finiscono nel CSS. Con una libreria di componenti tipica, importare tre icone porta con sé l'intero pacchetto o richiede una configurazione di tree shaking che spesso non funziona.

**La modalità attributify.** Le utility diventano attributi raggruppati per proprietà.

```html
<!-- Da questo -->
<button class="inline-flex h-11 items-center rounded bg-marchio-700 px-4 text-white
               hover:bg-marchio-900">
  Salva
</button>

<!-- A questo: raggruppato, leggibile -->
<button
  flex="inline ~"
  h="11"
  items="center"
  rounded
  bg="marchio-700 hover:marchio-900"
  px="4"
  text="white"
>
  Salva
</button>
```

È l'unica risposta strutturale all'obiezione del markup verboso che non richieda un linguaggio di componenti. Divide le opinioni: rende il markup più leggibile a chi ci lavora, meno familiare a chi arriva da fuori.

### Il confronto

| | Tailwind 4 | UnoCSS |
|---|---|---|
| Velocità di build | molto alta (Oxide, Rust) | molto alta |
| Ecosistema e documentazione | **molto ampio** | medio |
| Icone come classi | no | **sì** |
| Attributify | no | **sì** |
| Regole proprie con regex | limitato | **completo** |
| Adozione in azienda | **standard di fatto** | di nicchia |

La scelta operativa: Tailwind quando il progetto deve essere leggibile a chiunque arrivi; UnoCSS quando servono le icone come classi o regole molto specifiche, e il team è disposto a documentare una scelta meno diffusa.

---

## D2. Design token condivisi fra CSS, JavaScript e Figma

Il problema: il designer cambia il colore primario in Figma, e la modifica deve arrivare al CSS, al JavaScript e alla documentazione senza che nessuno la ricopi a mano.

La soluzione è una **sola fonte di verità** in un formato neutro, da cui si generano tutti gli altri.

```json
// token/base.json — formato W3C Design Tokens
{
  "colore": {
    "marchio": {
      "500": { "$type": "color", "$value": "oklch(60% 0.18 264)" },
      "700": { "$type": "color", "$value": "oklch(45% 0.18 264)" },
      "900": { "$type": "color", "$value": "oklch(30% 0.12 264)" }
    },
    "neutro": {
      "0": { "$type": "color", "$value": "oklch(100% 0 0)" },
      "600": { "$type": "color", "$value": "oklch(50% 0 0)" },
      "950": { "$type": "color", "$value": "oklch(12% 0 0)" }
    }
  },
  "spazio": {
    "1": { "$type": "dimension", "$value": "0.25rem" },
    "2": { "$type": "dimension", "$value": "0.5rem" },
    "4": { "$type": "dimension", "$value": "1rem" },
    "8": { "$type": "dimension", "$value": "2rem" }
  },
  "raggio": {
    "sm": { "$type": "dimension", "$value": "0.25rem" },
    "md": { "$type": "dimension", "$value": "0.5rem" }
  }
}
```

```json
// token/semantico.json — riferimenti ai primitivi, non valori duplicati
{
  "superficie": { "$type": "color", "$value": "{colore.neutro.0}" },
  "testo": {
    "principale": { "$type": "color", "$value": "{colore.neutro.950}" },
    "tenue": { "$type": "color", "$value": "{colore.neutro.600}" }
  },
  "azione": {
    "sfondo": { "$type": "color", "$value": "{colore.marchio.700}" },
    "sfondoAttivo": { "$type": "color", "$value": "{colore.marchio.900}" }
  }
}
```

```javascript
// scripts/genera-token.js
// Genera CSS, TypeScript e JSON da un'unica fonte.
// Uso: node scripts/genera-token.js

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'

const base = JSON.parse(readFileSync('token/base.json', 'utf8'))
const semantico = JSON.parse(readFileSync('token/semantico.json', 'utf8'))

/**
 * Appiattisce l'albero dei token in coppie nome→valore.
 * { colore: { marchio: { 500: {...} } } } → { 'colore-marchio-500': 'oklch(...)' }
 */
function appiattisci(albero, prefisso = '', esito = {}) {
  for (const [chiave, valore] of Object.entries(albero)) {
    const nome = prefisso ? `${prefisso}-${chiave}` : chiave

    if (valore && typeof valore === 'object' && '$value' in valore) {
      esito[nome] = valore.$value
    } else if (valore && typeof valore === 'object') {
      appiattisci(valore, nome, esito)
    }
  }
  return esito
}

/** Risolve i riferimenti {colore.marchio.700} nel valore corrispondente. */
function risolvi(valore, tabella) {
  if (typeof valore !== 'string') return valore

  return valore.replace(/\{([^}]+)\}/g, (_, riferimento) => {
    const nome = riferimento.replaceAll('.', '-')
    if (!(nome in tabella)) {
      throw new Error(`Riferimento non risolto: {${riferimento}}`)
    }
    return tabella[nome]
  })
}

const primitivi = appiattisci(base)
const semantici = appiattisci(semantico)

// I semantici possono riferirsi ai primitivi
const risolti = {}
for (const [nome, valore] of Object.entries(semantici)) {
  risolti[nome] = risolvi(valore, primitivi)
}

const tutti = { ...primitivi, ...risolti }

mkdirSync('src/generato', { recursive: true })

// ── 1. CSS: custom properties + @theme per Tailwind ──────────
const righeCss = Object.entries(tutti)
  .map(([nome, valore]) => `  --${nome}: ${valore};`)
  .join('\n')

writeFileSync(
  'src/generato/token.css',
  `/* Generato da scripts/genera-token.js — non modificare a mano */\n\n` +
    `@theme {\n${righeCss}\n}\n`,
)

// ── 2. TypeScript: costanti tipizzate ────────────────────────
const righeTs = Object.entries(tutti)
  .map(([nome, valore]) => `  '${nome}': ${JSON.stringify(valore)},`)
  .join('\n')

writeFileSync(
  'src/generato/token.ts',
  `// Generato da scripts/genera-token.js — non modificare a mano\n\n` +
    `export const token = {\n${righeTs}\n} as const\n\n` +
    `export type NomeToken = keyof typeof token\n\n` +
    `/** Restituisce il riferimento CSS al token, non il valore letterale:\n` +
    ` *  così il tema scuro continua a funzionare. */\n` +
    `export function varToken(nome: NomeToken): string {\n` +
    `  return \`var(--\${nome})\`\n` +
    `}\n`,
)

// ── 3. JSON piatto, per Figma e per la documentazione ────────
writeFileSync('src/generato/token.json', JSON.stringify(tutti, null, 2) + '\n')

console.log(`Generati ${Object.keys(tutti).length} token in src/generato/`)
```

```json
// package.json
{
  "scripts": {
    "token": "node scripts/genera-token.js",
    "dev": "pnpm token && vite",
    "build": "pnpm token && vite build"
  }
}
```

```
# Output atteso:
Generati 14 token in src/generato/
```

```typescript
// L'uso nel codice: il riferimento, non il valore
import { varToken } from './generato/token'

// ✅ var(--azione-sfondo): segue il tema
elemento.style.background = varToken('azione-sfondo')

// ❌ Il valore letterale: bloccato sul tema chiaro
import { token } from './generato/token'
elemento.style.background = token['azione-sfondo']
```

```
# Il punto: i file in src/generato/ NON si modificano e NON
# si committano (vanno in .gitignore). L'unica fonte è token/*.json.
#
# Il ciclo diventa:
#   il designer cambia un valore in Figma
#   → esporta token/base.json
#   → pnpm token
#   → CSS, TypeScript e documentazione sono allineati
#
# Nessuno ricopia un colore a mano, quindi nessuno lo sbaglia.
#
# Per progetti che hanno bisogno di più formati (iOS, Android,
# Flutter), Style Dictionary fa lo stesso lavoro con più
# trasformazioni già pronte.
```

---

## D3. Misurare il costo reale di ogni approccio

Le discussioni sui framework CSS si risolvono con i numeri. Ecco cosa misurare e come.

### Cosa contare

```
1. CSS servito              kB gzip/brotli sul primo caricamento
2. JavaScript aggiunto      il costo nascosto di CSS-in-JS runtime
3. Tempo di build           quanto rallenta il ciclo di sviluppo
4. Regole non usate         quanto del CSS servito serve davvero
5. Debito di architettura   !important, selettori con id, specificità
```

### Misurare il CSS non usato

```powershell
pnpm dev
```

```
# DevTools → menu ⋮ → More tools → Coverage
# → ricarica la pagina → naviga per le schermate principali
#
# La colonna "Unused Bytes" dice quanto del CSS servito
# non è mai stato applicato.
#
# Valori tipici su una pagina singola:
#   Bootstrap completo         85-92% non usato
#   Bootstrap solo moduli usati 60-70% non usato
#   Tailwind                    15-25% non usato
#   CSS scritto a mano          30-50% non usato
#
# ATTENZIONE all'interpretazione: "non usato su QUESTA pagina"
# non significa "inutile". Un pannello di amministrazione con
# venti schermate usa su ognuna solo una frazione del CSS,
# ed è normale. La metrica va letta sull'insieme delle schermate,
# non su una sola.
```

### Il costo nascosto del CSS-in-JS runtime

```javascript
// scripts/misura-bundle.js
// Confronta il peso di CSS e JavaScript insieme.
// Uso: node scripts/misura-bundle.js dist

import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { gzipSync } from 'node:zlib'

const cartella = process.argv[2] ?? 'dist'

function trovaFile(percorso, estensioni, trovati = []) {
  for (const voce of readdirSync(percorso)) {
    const completo = join(percorso, voce)
    if (statSync(completo).isDirectory()) {
      trovaFile(completo, estensioni, trovati)
    } else if (estensioni.some((e) => voce.endsWith(e))) {
      trovati.push(completo)
    }
  }
  return trovati
}

function pesoGzip(percorsi) {
  return percorsi.reduce((somma, p) => somma + gzipSync(readFileSync(p)).length, 0)
}

const css = trovaFile(cartella, ['.css'])
const js = trovaFile(cartella, ['.js', '.mjs'])

const pesoCss = pesoGzip(css)
const pesoJs = pesoGzip(js)

const kb = (b) => `${(b / 1024).toFixed(1)} kB`

console.log(`CSS:        ${kb(pesoCss)} gzip  (${css.length} file)`)
console.log(`JavaScript: ${kb(pesoJs)} gzip  (${js.length} file)`)
console.log(`Totale:     ${kb(pesoCss + pesoJs)} gzip`)
console.log(
  `\nRapporto CSS/JS: ${((pesoCss / (pesoCss + pesoJs)) * 100).toFixed(0)}% / ` +
    `${((pesoJs / (pesoCss + pesoJs)) * 100).toFixed(0)}%`,
)
```

```
# Output atteso su tre configurazioni dello stesso progetto:
#
#   Tailwind 4
#     CSS:         6.8 kB gzip
#     JavaScript: 52.1 kB gzip     ← React e le dipendenze
#     Totale:     58.9 kB gzip
#
#   CSS Modules
#     CSS:         8.2 kB gzip
#     JavaScript: 52.1 kB gzip
#     Totale:     60.3 kB gzip
#
#   styled-components
#     CSS:         0.4 kB gzip     ← quasi nulla: è generato a runtime
#     JavaScript: 68.7 kB gzip     ← +16 kB di libreria
#     Totale:     69.1 kB gzip
#
# Il CSS-in-JS runtime sembra vincere sulla colonna CSS
# e perde del 17% sul totale — che è ciò che l'utente scarica.
# In più il CSS viene generato NEL BROWSER, quindi il primo
# dipinto arriva dopo l'esecuzione del JavaScript.
```

### Il tempo di build

```powershell
# Misurare, invece di percepire
Measure-Command { pnpm build } | Select-Object TotalSeconds
```

```
# Valori indicativi su un progetto medio (200 componenti):
#
#   CSS nativo + Vite            2,1 s
#   Tailwind 4 (motore Oxide)    2,4 s
#   CSS Modules                  2,6 s
#   Sass (progetto strutturato)  4,8 s
#   vanilla-extract              5,2 s
#
# La differenza conta soprattutto in sviluppo, dove la build
# incrementale si ripete a ogni salvataggio. Un secondo in più
# per centinaia di salvataggi al giorno è tempo reale.
```

---

## D4. Migrare da un framework a un altro senza fermare il progetto

Una migrazione "big bang" — riscrivere tutto e rilasciare — fallisce quasi sempre: blocca lo sviluppo per settimane e produce un rilascio troppo grande per essere verificato. La strategia praticabile è la convivenza.

### Il meccanismo: `@layer`

```css
/* src/stile.css */

/* L'ordine dei layer decide chi vince, indipendentemente
   dalla specificità. Tailwind viene dopo, quindi le sue utility
   scavalcano il CSS legacy SENZA !important. */
@layer legacy, framework, componenti, utility;

@import './legacy/tutto.css' layer(legacy);
@import 'tailwindcss' layer(framework);
```

Da questo momento:

```html
<!-- La classe legacy fornisce lo stile di base;
     l'utility Tailwind sovrascrive ciò che serve, senza combattere -->
<div class="scheda-legacy p-6 rounded-lg">…</div>
```

```
Quello che succede:

  .scheda-legacy { padding: 1rem }     → layer 'legacy'
  .p-6 { padding: 1.5rem }             → layer 'framework'

  Il layer 'framework' viene dopo → p-6 vince,
  anche se .scheda-legacy avesse specificità più alta.

  Senza @layer servirebbe !important su ogni utility,
  e il risultato sarebbe ingestibile.
```

### Le cinque fasi

```
FASE 1 — Convivenza (settimana 1)
  · Installa il nuovo framework in un layer superiore
  · Verifica che NULLA cambi visivamente: il layer legacy
    è ancora l'unico che produce stile
  · Rilascia. Questo rilascio non deve cambiare niente.

FASE 2 — Token condivisi (settimane 2-3)
  · Estrai i colori, gli spazi e la tipografia del CSS legacy
    in custom properties
  · Configura il nuovo framework perché usi GLI STESSI token
  · Ora i due sistemi producono gli stessi valori:
    un componente migrato è indistinguibile da uno non migrato

FASE 3 — Migrazione opportunistica (in corso)
  · Regola: quando tocchi un componente per altri motivi,
    lo migri. Nessuno migra componenti "per migrarli".
  · Ogni componente migrato: rimuovi le sue regole dal CSS legacy
  · Il CSS legacy si assottiglia da solo, senza un progetto dedicato

FASE 4 — Componenti condivisi (settimane 4-8)
  · Migra per primi i componenti usati ovunque:
    pulsanti, campi di form, schede
  · Sono quelli che danno il guadagno maggiore

FASE 5 — Rimozione (quando il legacy è sotto il 10%)
  · Rimuovi il layer legacy
  · Rimuovi la dipendenza dal vecchio framework
  · Elimina @layer se non serve più
```

### Tracciare l'avanzamento

```javascript
// scripts/avanzamento-migrazione.js
// Uso: node scripts/avanzamento-migrazione.js

import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, extname } from 'node:path'

const ESTENSIONI = new Set(['.jsx', '.tsx', '.vue', '.svelte', '.html'])
const IGNORA = new Set(['node_modules', 'dist', '.git', 'coverage'])

/** Riconosce le classi del vecchio sistema: prefisso o convenzione BEM. */
const LEGACY = /\b(?:bs-|btn-|card-|nav-|form-control|col-(?:xs|sm|md|lg|xl)-\d+)/
/** Riconosce le utility del nuovo: un campione rappresentativo. */
const NUOVO = /\b(?:flex|grid|p-\d|px-\d|py-\d|m-\d|gap-\d|text-|bg-|rounded|border)\b/

function scansiona(percorso, esito = { legacy: [], nuovo: [], misti: [], puliti: [] }) {
  for (const voce of readdirSync(percorso)) {
    if (IGNORA.has(voce)) continue

    const completo = join(percorso, voce)

    if (statSync(completo).isDirectory()) {
      scansiona(completo, esito)
      continue
    }

    if (!ESTENSIONI.has(extname(voce))) continue

    const testo = readFileSync(completo, 'utf8')
    const haLegacy = LEGACY.test(testo)
    const haNuovo = NUOVO.test(testo)

    if (haLegacy && haNuovo) esito.misti.push(completo)
    else if (haLegacy) esito.legacy.push(completo)
    else if (haNuovo) esito.nuovo.push(completo)
    else esito.puliti.push(completo)
  }
  return esito
}

const esito = scansiona('src')
const totale = esito.legacy.length + esito.nuovo.length + esito.misti.length

if (totale === 0) {
  console.log('Nessun file con classi riconosciute.')
  process.exit(0)
}

const percentuale = (n) => ((n / totale) * 100).toFixed(0)

console.log('Avanzamento della migrazione\n')
console.log(`  solo nuovo:   ${String(esito.nuovo.length).padStart(4)}  ${percentuale(esito.nuovo.length)}%`)
console.log(`  misti:        ${String(esito.misti.length).padStart(4)}  ${percentuale(esito.misti.length)}%`)
console.log(`  solo legacy:  ${String(esito.legacy.length).padStart(4)}  ${percentuale(esito.legacy.length)}%`)
console.log(`  senza classi: ${String(esito.puliti.length).padStart(4)}`)

if (esito.legacy.length > 0) {
  console.log('\nProssimi candidati (solo legacy):')
  for (const percorso of esito.legacy.slice(0, 10)) {
    console.log(`  ${percorso}`)
  }
  if (esito.legacy.length > 10) {
    console.log(`  … e altri ${esito.legacy.length - 10}`)
  }
}
```

```
# Output atteso a metà migrazione:
Avanzamento della migrazione

  solo nuovo:     84  58%
  misti:          31  21%
  solo legacy:    30  21%
  senza classi:   12

Prossimi candidati (solo legacy):
  src/componenti/TabellaFatture.jsx
  src/componenti/FiltroPeriodo.jsx
  src/pagine/Impostazioni.jsx
  …
```

```
# La metrica che conta davvero NON è la percentuale di file
# migrati: è la dimensione del CSS legacy.
#
#   Get-Item src/legacy/tutto.css | Select-Object Length
#
# Se dopo due mesi il file non si è ridotto, la fase 3
# non sta funzionando: i componenti vengono migrati ma
# nessuno rimuove le regole corrispondenti dal legacy.
# È l'errore più comune, e produce un progetto che ha
# entrambi i sistemi e i costi di entrambi.
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
FRAMEWORK CSS — Mappa dei concetti

IL PROBLEMA CHE RISOLVONO
├── Il CSS cresce e non si restringe (nessuno cancella per paura)
├── I nomi delle classi diventano un problema di per sé
└── La coerenza si perde fra più persone
    └── Ogni famiglia attacca UN problema, non tutti

LE TRE FAMIGLIE
├── Component-based (Bootstrap)
│     classi = COMPONENTI · velocissimo · aspetto standard
│     personalizzare = combattere, se non via Sass
├── Utility-first (Tailwind, UnoCSS)
│     classi = DICHIARAZIONI · il CSS satura, non cresce
│     markup verboso → si estrae nel linguaggio dei componenti
└── CSS proprio (con BEM, CSS Modules, o niente)
      classi = RUOLI · controllo totale · cresce sempre

PREPROCESSORI
├── Sass: cosa RESTA giustificato
│     @each su mappe · @mixin con parametri · funzioni di calcolo
├── Sass: cosa NON serve più
│     variabili (→ custom properties, cambiano a runtime)
│     annidamento (→ nativo dal 2023)
│     media query mixin (→ sintassi a intervalli)
│     @import (→ deprecato, usa @use)
│     ⚠ &__titolo di Sass NON esiste in CSS nativo
└── PostCSS: infrastruttura, non preprocessore
      browserslist dichiara i browser UNA volta per tutta la catena

TAILWIND 4
├── @theme: un token genera INSIEME l'utility e la custom property
│     → i token sono leggibili anche da CSS e JavaScript esterni
├── Motore Oxide (Rust) · @tailwindcss/vite · niente config JS
├── Rilevamento automatico dei file · @source per i casi limite
├── LA REGOLA: la classe deve esistere nel sorgente come
│     STRINGA COMPLETA. `bg-${colore}-500` non viene generata.
│     → mappa di classi, cva, oppure @source inline
├── L'ordine nel markup NON conta → tailwind-merge per i conflitti
├── @utility (con le varianti) · @layer components · @custom-variant
└── Estrazione: nel linguaggio dei componenti, non con @apply
      @apply solo dove NON c'è un linguaggio di componenti

BOOTSTRAP
├── Personalizzare = variabili Sass PRIMA dell'import
│     mai sovrascritture con !important
├── Importare solo i moduli usati: 232 kB → 94 kB
└── map-merge su $utilities per aggiungerne di proprie

ARCHITETTURE
├── BEM        blocco__elemento--modificatore, specificità piatta
│              ⚠ un solo livello di __, il modificatore accompagna il blocco
├── ITCSS      strati dal generico allo specifico
│              → @layer lo rende esplicito e superfluo
├── Cube CSS   Composition · Utility · Block · Exception
└── CSS Modules  ambito per costruzione, nessuna convenzione

CSS-IN-JS
├── Runtime (styled-components, Emotion)
│     +12-16 kB nel bundle · CSS generato nel browser
│     problematico con i Server Components · in declino
└── Zero-runtime (vanilla-extract, Panda)
      tipi completi · CSS estratto a build · ecosistema piccolo

HEADLESS
├── Radix / Headless UI / Ark
│     comportamento + accessibilità, ZERO aspetto
│     focus, tastiera, ARIA, portale: tutto già corretto
│     data-state="open" per lo stile
└── shadcn/ui = Radix + Tailwind COPIATO nel tuo repo
      nessuna dipendenza che invecchia · aggiornamenti manuali
      @theme inline per i token che cambiano con il tema

ACCESSIBILITÀ
├── Tailwind non ne fornisce: è un vocabolario CSS
├── Le trappole: text-neutral-400 (2.6:1), outline-none,
│     div cliccabili, hidden invece di sr-only, bersagli sotto 44px
└── Le classi utili: sr-only, focus:not-sr-only, motion-reduce:,
      contrast-more:

SCELTA
├── Il design è mio o va bene un catalogo?
├── Quanto dura e quante persone?
└── C'è un linguaggio di componenti?
      Nessun approccio è migliore in astratto.

MIGRAZIONE
└── @layer legacy, framework → convivenza senza !important
      migrazione opportunistica · la metrica è la DIMENSIONE
      del CSS legacy, non la percentuale di file
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Sai enunciare i tre problemi che i framework CSS risolvono
- [ ] Riconosci dalla sola lettura del markup quale famiglia è in uso
- [ ] Sai perché "il CSS satura invece di crescere" è l'argomento forte delle utility
- [ ] Sai cosa resta giustificato in Sass e cosa è diventato nativo
- [ ] Sai perché `@use` ha sostituito `@import` in Sass
- [ ] Sai a cosa serve `browserslist` e chi lo legge
- [ ] Installi Tailwind 4 con il plugin Vite e configuri `@theme`
- [ ] Conosci il vocabolario di base e le varianti (`hover:`, `md:`, `dark:`, `group-`, `peer-`)
- [ ] Sai quando un valore arbitrario `[...]` è legittimo e quando è un sintomo
- [ ] Usi la griglia di Bootstrap e ne conosci i breakpoint
- [ ] Scrivi classi BEM rispettando il livello unico di `__` e l'accoppiata blocco+modificatore

**Parte B — Comprensione**

- [ ] Sai che `@theme` genera insieme utility e custom properties, e perché conta
- [ ] Conosci i prefissi di spazio dei nomi e cosa generano
- [ ] Sai spiegare perché `bg-${colore}-500` non produce CSS
- [ ] Sai diagnosticare una classe mancante con due comandi
- [ ] Sai perché l'ordine delle classi nel markup non risolve i conflitti
- [ ] Usi `clsx` e `tailwind-merge` e sai cosa fa ciascuno
- [ ] Sai quando `@apply` è legittimo e quando ricrea il problema
- [ ] Personalizzi Bootstrap con le variabili Sass invece delle sovrascritture
- [ ] Sai quanto si risparmia importando solo i moduli usati
- [ ] Sai cosa `@layer` rende superfluo di ITCSS
- [ ] Conosci vantaggi e limiti dei CSS Modules
- [ ] Sai perché il CSS-in-JS runtime costa di più anche quando il CSS è più piccolo
- [ ] Sai cosa fornisce una libreria headless e cosa resta da fare
- [ ] Sai perché shadcn/ui non è una dipendenza, e cosa comporta
- [ ] Sai perché serve `@theme inline` per i token che cambiano con il tema
- [ ] Conosci le cinque trappole di accessibilità delle utility

**Parte C — Pratica**

- [ ] Hai configurato Tailwind 4 con token propri e verificato che siano nel `:root`
- [ ] Hai riprodotto e corretto in tre modi il bug della classe composta
- [ ] Hai personalizzato Bootstrap via Sass e misurato il risparmio
- [ ] Hai ricostruito la dashboard con Tailwind e confrontato i numeri con la versione in CSS puro

**Parte D — Esperto**

- [ ] Sai cosa UnoCSS fa che Tailwind non fa
- [ ] Sai generare CSS, TypeScript e JSON da un'unica fonte di token
- [ ] Sai perché il codice deve usare `var(--token)` e non il valore letterale
- [ ] Misuri CSS e JavaScript insieme, non solo il CSS
- [ ] Sai leggere il pannello Coverage e cosa non significa
- [ ] Sai impostare la convivenza fra due sistemi con `@layer`
- [ ] Sai qual è la metrica reale di avanzamento di una migrazione

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Scegliere il framework per abitudine | Il criterio giusto dipende dal progetto, non dalle preferenze | Le tre domande di C1 esercizio 5 |
| Sovrascrivere Bootstrap con `!important` | Servono decine di regole per ogni colore, e ogni aggiornamento ne aggiunge | Variabili Sass prima dell'import |
| Importare Bootstrap completo | 232 kB di cui l'85% non usato | Solo i moduli necessari |
| `bg-${colore}-500` in Tailwind | La classe non esiste come stringa: il CSS non viene generato | Mappa di classi complete, `cva`, o `@source inline` |
| `@apply` per ogni componente | Ricrea il foglio di stile che cresce, cioè il problema che Tailwind risolveva | Estrarre nel linguaggio dei componenti |
| Valori arbitrari `[13px]` ovunque | Il vincolo sparisce, e con esso il motivo per usare Tailwind | Restare nella scala; l'arbitrario è l'eccezione |
| Concatenare classi senza `tailwind-merge` | Le classi passate dal chiamante possono non vincere | `twMerge(clsx(...))` |
| `text-neutral-400` per il testo secondario | 2.6:1 su bianco: sotto il minimo WCAG di 4.5:1 | `text-neutral-600` |
| `outline-none` senza sostituto | Chi naviga da tastiera non sa dove si trova | `focus-visible:outline focus-visible:outline-2` |
| `hidden` per il testo degli screen reader | Nasconde a tutti, tecnologie assistive incluse | `sr-only` |
| `<div>` cliccabile stilato come pulsante | Le utility non danno ruolo né risposta alla tastiera | `<button>` |
| Annidamento Sass oltre due livelli | Selettori lunghi e specificità alta, difficili da sovrascrivere | Massimo due livelli |
| `&__elemento__sotto` in BEM | Riflette il DOM: spostare l'elemento rompe la classe | Un solo livello di `__` |
| `.scheda--evidenziata` senza `.scheda` | Il modificatore da solo perde lo stile di base | Il modificatore accompagna sempre il blocco |
| Variabili Sass per i colori del tema | Risolte a compilazione: il tema scuro richiederebbe due fogli | Custom properties |
| `@import` in Sass | Deprecato: collisioni di nomi e ricompilazioni multiple | `@use` e `@forward` |
| styled-components su un progetto nuovo | Progetto in manutenzione, +16 kB, problematico con RSC | Zero-runtime o utility |
| Migrazione "big bang" | Blocca lo sviluppo e produce un rilascio non verificabile | Convivenza con `@layer`, migrazione opportunistica |
| Migrare senza rimuovere il CSS legacy | Si finisce con due sistemi e i costi di entrambi | Rimuovere le regole a ogni componente migrato |
| Misurare solo il CSS | Il CSS-in-JS runtime sposta il costo sul JavaScript | Misurare CSS e JS insieme |
| Copiare i valori dei token a mano | Divergono al primo aggiornamento | Generarli da un'unica fonte |

---

## Troubleshooting rapido

**Una classe Tailwind non produce alcun effetto**
- Causa: la classe è composta a runtime, oppure il file non viene scansionato
- Fix: `Select-String -Path "dist/assets/*.css" -Pattern "la-classe"`. Se manca, cercala nel sorgente come stringa intera; se il sorgente non è scansionato, aggiungi `@source`

**In sviluppo funziona, in produzione lo stile manca**
- Causa: quasi sempre la stessa — classe composta con un template literal
- Fix: mappa di classi complete, `cva`, oppure `@source inline`

**Due utility Tailwind in conflitto: vince quella sbagliata**
- Causa: l'ordine nel markup non conta, decide l'ordine interno di Tailwind
- Fix: `tailwind-merge`, che risolve i conflitti nella famiglia di utility

**`@apply` non riconosce una classe**
- Causa: `@apply` non funziona con le classi di altri layer, né con le varianti complesse
- Fix: scrivere il CSS per esteso, o spostare la regola in `@layer components`

**Il tema scuro non funziona con i token di shadcn/ui**
- Causa: `@theme` invece di `@theme inline` — il valore viene risolto a build e non segue la custom property
- Fix: `@theme inline` per i token che puntano a variabili che cambiano

**Bootstrap ignora le variabili Sass che hai impostato**
- Causa: le tue variabili sono dopo `@import 'bootstrap/scss/variables'`
- Fix: `functions` → **le tue variabili** → `variables` → il resto

**Il CSS di Bootstrap pesa più di 200 kB**
- Causa: importato `bootstrap.min.css` invece dei singoli moduli
- Fix: importare solo i moduli usati; disattivare `$enable-shadows` e `$enable-gradients`

**Un componente Radix non è visibile**
- Causa: manca `Portal`, oppure il contenuto non ha `position` e dimensioni
- Fix: `<Dialog.Portal>` attorno a `Overlay` e `Content`; posizionare `Content` esplicitamente

**Le animazioni `data-[state=open]` non partono**
- Causa: `tailwindcss-animate` non installato, o le keyframe non definite
- Fix: installare il plugin, oppure definire le animazioni in `@theme` con `--animate-*`

**Il CSS Module ha nomi illeggibili anche in sviluppo**
- Causa: `generateScopedName` non differenzia sviluppo e produzione
- Fix: `'[name]__[local]__[hash:base64:4]'` in sviluppo

**Il selettore Sass compilato ha specificità inattesa**
- Causa: annidamento profondo — ogni livello aggiunge una classe
- Fix: verificare il CSS prodotto; mai oltre due livelli

**Il nesting nativo non funziona come in Sass**
- Causa: `&__titolo` concatenato non esiste in CSS nativo
- Fix: `& .blocco__titolo` per esteso

**Le utility non sovrascrivono il CSS legacy**
- Causa: il CSS legacy è fuori da qualunque layer, quindi vince su tutti i layer
- Fix: importarlo dentro un layer: `@import './legacy.css' layer(legacy)`

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_06_typescript.md` | Tipizzare le props delle varianti; `VariantProps` di `cva` |
| `tutorial_07_react.md` | Estrarre i componenti Tailwind; `cn()`, `forwardRef`, `asChild` |
| `tutorial_15_testing_web.md` | Visual regression: verificare che una migrazione non cambi la resa |
| `tutorial_16_build_tools_deploy.md` | La pipeline che genera i token e misura il bundle in CI |
| `tutorial_17_performance_web.md` | CSS critico, Coverage, e il costo del CSS sul primo dipinto |
| `tutorial_25_nextjs.md` | Tailwind con i Server Components e il rendering sul server |

---

## Risorse di riferimento

**Documentazione ufficiale:**
- [Tailwind CSS](https://tailwindcss.com/docs) — riferimento completo delle utility e di `@theme`
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/) — componenti, griglia, personalizzazione Sass
- [Sass](https://sass-lang.com/documentation/) — `@use`, `@forward`, moduli
- [PostCSS](https://postcss.org/) — plugin e API
- [Radix UI Primitives](https://www.radix-ui.com/primitives/docs/overview/introduction)
- [shadcn/ui](https://ui.shadcn.com/) — catalogo e istruzioni di installazione
- [UnoCSS](https://unocss.dev/) — preset, regole, trasformatori
- [vanilla-extract](https://vanilla-extract.style/) — CSS in TypeScript a zero runtime

**Specifiche e convenzioni:**
- [CSS Cascading Level 5 — `@layer`](https://www.w3.org/TR/css-cascade-5/#layering)
- [Design Tokens Format Module](https://tr.designtokens.org/format/) — il formato W3C
- [BEM](https://getbem.com/) — la convenzione, con esempi
- [Cube CSS](https://cube.fyi/) — la metodologia, dall'autore

**Strumenti:**
- [Style Dictionary](https://styledictionary.com/) — generazione di token multi-piattaforma
- [class-variance-authority](https://cva.style/) — varianti tipizzate
- [tailwind-merge](https://github.com/dcastil/tailwind-merge) — risoluzione dei conflitti
- [eslint-plugin-jsx-a11y](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y) — accessibilità nel JSX
- [Can I use](https://caniuse.com/) — supporto dei browser

**Libri e articoli:**
- Andy Bell e Heydon Pickering, *Every Layout* — il layout come componente algoritmico, alla base di Cube CSS
- Harry Roberts, *articoli su csswizardry.com* — ITCSS, specificità, performance del CSS

---

> **Fine del Tutorial 03 — Framework CSS**
>
> Prossimo tutorial: `tutorial_04_javascript_fondamenti.md`
