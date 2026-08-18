# Tutorial 09 — Svelte 5: Dal Principiante all'Esperto

> **Companion a:** `09-svelte.md`
> **Scope:** Il compilatore invece del runtime, le rune (`$state`, `$derived`, `$effect`, `$props`, `$bindable`), snippet e `{@render}`, azioni e transizioni, store e classi reattive, SvelteKit (routing, `load`, form action, hook), rendering lato server e idratazione, migrazione dagli store di Svelte 4, performance, accessibilità, testing
> **Prerequisiti:** `tutorial_04_javascript_fondamenti.md`, `tutorial_06_typescript.md`; utile aver letto `tutorial_07_react.md` e `tutorial_08_vue.md` per il confronto
> **Durata stimata:** 22-28 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Svelte 5 · SvelteKit 2 · TypeScript 5.6+ · Vite · Vitest

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Un compilatore, non una libreria](#a1-un-compilatore-non-una-libreria)
  - [A2. Il componente Svelte](#a2-il-componente-svelte)
  - [A3. `$state`: la reattività](#a3-state-la-reattività)
  - [A4. `$derived`: i valori calcolati](#a4-derived-i-valori-calcolati)
  - [A5. Il markup: blocchi e direttive](#a5-il-markup-blocchi-e-direttive)
  - [A6. `$props` e `$bindable`](#a6-props-e-bindable)
  - [A7. `bind:` e i form](#a7-bind-e-i-form)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. Come funziona la compilazione](#b1-come-funziona-la-compilazione)
  - [B2. `$effect` e quando non usarlo](#b2-effect-e-quando-non-usarlo)
  - [B3. Snippet e `{@render}`](#b3-snippet-e-render)
  - [B4. Stato condiviso: file `.svelte.ts` e classi](#b4-stato-condiviso-file-sveltets-e-classi)
  - [B5. Context](#b5-context)
  - [B6. Azioni: `use:`](#b6-azioni-use)
  - [B7. Transizioni e animazioni](#b7-transizioni-e-animazioni)
  - [B8. SvelteKit: routing e caricamento dei dati](#b8-sveltekit-routing-e-caricamento-dei-dati)
  - [B9. SvelteKit: form action e progressive enhancement](#b9-sveltekit-form-action-e-progressive-enhancement)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: la dashboard, in SvelteKit](#c2-mini-progetto-la-dashboard-in-sveltekit)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. Il modello di reattività a grana fine](#d1-il-modello-di-reattività-a-grana-fine)
  - [D2. Migrare da Svelte 4 a Svelte 5](#d2-migrare-da-svelte-4-a-svelte-5)
  - [D3. Accessibilità: cosa Svelte verifica da solo](#d3-accessibilità-cosa-svelte-verifica-da-solo)
  - [D4. Testare i componenti Svelte](#d4-testare-i-componenti-svelte)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                             SVELTE 5
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
    ┌─────────▼──────────┐                ┌─────────▼──────────┐
    │  IL COMPILATORE    │                │     LE RUNE        │
    │                    │                │                    │
    │  legge il .svelte  │                │  $state()          │
    │  produce JS che    │                │   └ Proxy profondo │
    │  tocca il DOM      │                │  $derived()        │
    │  DIRETTAMENTE      │                │   └ pigro, in cache│
    │                    │                │  $effect()         │
    │  niente VDOM       │                │   └ dopo il DOM    │
    │  niente confronto  │                │   └ pulizia        │
    │  runtime minimo    │                │  $props()          │
    │                    │                │  $bindable()       │
    │  il codice non     │                │  $inspect()        │
    │  usato non finisce │                │                    │
    │  nel bundle        │                │  sono SIMBOLI del  │
    │                    │                │  compilatore, non  │
    │                    │                │  funzioni vere     │
    └─────────┬──────────┘                └─────────┬──────────┘
              └──────────────────┬──────────────────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                            │                            │
┌───▼─────────────┐   ┌──────────▼─────────┐   ┌──────────────▼────┐
│    IL MARKUP    │   │   COMPOSIZIONE     │   │    SVELTEKIT      │
│                 │   │                    │   │                   │
│ {espressione}   │   │ snippet            │   │ routing a file    │
│ {#if} {:else}   │   │  └ {#snippet}      │   │  +page.svelte     │
│ {#each} (chiave)│   │  └ {@render}       │   │  +page.ts   load  │
│ {#await}        │   │ children           │   │  +page.server.ts  │
│ {#key}          │   │ setContext         │   │  +layout          │
│                 │   │ getContext         │   │  +server.ts       │
│ on* / onclick   │   │                    │   │                   │
│ bind:valore     │   │ azioni use:        │   │ form action       │
│ class: style:   │   │  └ nodo + pulizia  │   │  └ funziona SENZA │
│ use:azione      │   │ transition:        │   │    JavaScript     │
│ transition:     │   │  in: out: animate: │   │ hooks.server.ts   │
└─────────────────┘   └────────────────────┘   └───────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Un compilatore, non una libreria

> **Analogia:** React e Vue sono un interprete che gira insieme al tuo programma: leggono le tue istruzioni a runtime e decidono cosa fare. Svelte è un traduttore: legge il tuo programma una volta sola, al momento della build, e produce codice macchina che fa direttamente il lavoro. Non c'è nessun interprete da spedire insieme al risultato.

```
                    REACT / VUE              SVELTE

Cosa spedisci       il tuo codice            SOLO il tuo codice,
                    + il runtime del         tradotto in operazioni
                    framework (~40 kB)       dirette sul DOM

Aggiornamento       il framework calcola     il codice compilato
                    cosa è cambiato          SA già cosa aggiornare

Dimensione del      cresce di poco con       cresce con il codice,
bundle              il codice, parte alta    parte quasi da zero

Reattività          esplicita (setState)     assegnazione, con le rune
                    o Proxy (Vue)            che marcano cosa è reattivo

Il compilatore vede tutto: sa che 'conteggio' è letto solo in
quel paragrafo, e genera l'istruzione che aggiorna quel nodo.
```

```svelte
<!-- Quello che scrivi -->
<script lang="ts">
  let conteggio = $state(0)
</script>

<button onclick={() => conteggio++}>
  Cliccato {conteggio} volte
</button>
```

```javascript
// Quello che il compilatore produce, in forma semplificata:
// nessun virtual DOM, nessun confronto, un'operazione diretta
function Contatore(nodo) {
  let conteggio = stato(0)

  const pulsante = document.createElement('button')
  const testo = document.createTextNode('')
  pulsante.append('Cliccato ', testo, ' volte')

  pulsante.addEventListener('click', () => set(conteggio, get(conteggio) + 1))

  // Un effetto che aggiorna SOLO questo nodo di testo
  effetto(() => {
    testo.data = get(conteggio)
  })

  nodo.append(pulsante)
}
```

### Il primo progetto

```powershell
pnpm create svelte@latest dashboard-svelte
# Rispondi: SvelteKit, TypeScript, ESLint, Vitest, Playwright

cd dashboard-svelte
pnpm install
pnpm dev
```

```powershell
# Solo Svelte, senza SvelteKit
pnpm create vite dashboard --template svelte-ts
```

---

## A2. Il componente Svelte

```svelte
<!-- src/lib/componenti/SchedaIndicatore.svelte -->
<script lang="ts">
  type Props = {
    titolo: string
    valore: number
    variazione?: number
    formato?: 'numero' | 'valuta' | 'percentuale'
  }

  let { titolo, valore, variazione, formato = 'numero' }: Props = $props()

  const formattato = $derived.by(() => {
    switch (formato) {
      case 'valuta':
        return new Intl.NumberFormat('it-IT', {
          style: 'currency',
          currency: 'EUR',
        }).format(valore)
      case 'percentuale':
        return `${valore.toFixed(1)}%`
      default:
        return new Intl.NumberFormat('it-IT').format(valore)
    }
  })

  const segno = $derived(
    variazione === undefined ? null : variazione >= 0 ? 'positiva' : 'negativa',
  )
</script>

<article class="scheda">
  <p class="scheda__etichetta">{titolo}</p>
  <p class="scheda__valore">{formattato}</p>

  {#if variazione !== undefined}
    <p class="scheda__variazione" data-segno={segno}>
      <span aria-hidden="true">{variazione >= 0 ? '▲' : '▼'}</span>
      {Math.abs(variazione)}%
      <span class="solo-screen-reader">
        {variazione >= 0 ? 'in aumento' : 'in diminuzione'}
      </span>
    </p>
  {/if}
</article>

<style>
  /* Il CSS è LOCALE per costruzione: nessun 'scoped' da scrivere.
     Il compilatore aggiunge una classe univoca. */
  .scheda {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
    background: var(--superficie);
    border: 1px solid var(--bordo);
    border-radius: 0.5rem;
  }

  .scheda__etichetta {
    margin: 0;
    color: var(--testo-tenue);
    font-size: 0.875rem;
    text-transform: uppercase;
  }

  .scheda__valore {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  .scheda__variazione[data-segno='positiva'] {
    color: var(--successo);
  }

  .scheda__variazione[data-segno='negativa'] {
    color: var(--errore);
  }
</style>
```

```svelte
<style>
  /* :global() esce dall'ambito locale */
  :global(body) {
    margin: 0;
  }

  /* Stilare un discendente generato da un figlio */
  .contenitore :global(.classe-esterna) {
    color: red;
  }

  /* Un selettore non usato nel markup produce un AVVISO
     in compilazione: il CSS morto viene segnalato,
     non silenziosamente incluso. */
</style>
```

Il CSS non usato che diventa un avviso di compilazione è una differenza pratica notevole: nei progetti React e Vue quel CSS si accumula per anni senza che nessuno se ne accorga.

---

## A3. `$state`: la reattività

Le **rune** sono simboli riconosciuti dal compilatore. Non sono funzioni: non si importano, non si possono passare in giro, e non esistono a runtime nella forma in cui le scrivi.

```typescript
// $state rende reattiva una variabile
let conteggio = $state(0)

conteggio++ // tutto ciò che legge conteggio si aggiorna
conteggio = 10
```

```svelte
<script lang="ts">
  // Funziona con qualunque tipo
  let conteggio = $state(0)
  let nome = $state('Anna')
  let attivo = $state(true)
  let utente = $state<Utente | null>(null)

  // Gli oggetti e gli array sono resi reattivi IN PROFONDITÀ
  // tramite un Proxy: la mutazione funziona
  let elenco = $state<string[]>([])
  let modulo = $state({ nome: '', indirizzo: { citta: '' } })

  function aggiungi() {
    elenco.push('nuovo') // reattivo
    modulo.indirizzo.citta = 'Milano' // reattivo anche in profondità
  }
</script>
```

### `$state.raw` e `$state.snapshot`

```typescript
// $state.raw: NON avvolge in un Proxy. Solo la sostituzione
// dell'intero valore è reattiva. Per strutture grandi che
// si sostituiscono per intero, evita il costo del Proxy.
let righe = $state.raw<Fattura[]>([])

righe.push(nuova) // NON reattivo
righe = [...righe, nuova] // reattivo

// $state.snapshot: una copia NON reattiva, senza Proxy.
// Serve quando si passa lo stato a codice esterno che
// non si aspetta un Proxy.
async function salva() {
  const copia = $state.snapshot(modulo)
  await fetch('/api', { method: 'POST', body: JSON.stringify(copia) })
}

// structuredClone su un Proxy solleva DataCloneError:
// $state.snapshot risolve esattamente questo
```

### Il limite: `$state` è legato alla dichiarazione

```typescript
// ❌ Il destructuring estrae il VALORE: la reattività si perde
let stato = $state({ conteggio: 0 })
let { conteggio } = stato // un numero normale

// ❌ Non si può passare una variabile reattiva a una funzione
//    e aspettarsi che resti collegata
function incrementa(valore: number) {
  valore++ // modifica la copia locale
}

// ✅ Passare un oggetto, o usare un getter
function incrementaOggetto(stato: { conteggio: number }) {
  stato.conteggio++ // funziona: l'oggetto è il Proxy
}
```

```typescript
// Il pattern per condividere un valore reattivo: getter e setter
function creaContatore(iniziale = 0) {
  let valore = $state(iniziale)

  return {
    get valore() {
      return valore
    },
    incrementa: () => valore++,
    azzera: () => (valore = iniziale),
  }
}
```

---

## A4. `$derived`: i valori calcolati

```svelte
<script lang="ts">
  let fatture = $state<Fattura[]>([])
  let ricerca = $state('')
  let soloInsolute = $state(false)

  // $derived per un'espressione singola
  const totale = $derived(fatture.reduce((s, f) => s + f.importo, 0))

  // $derived.by per la logica su più righe
  const filtrate = $derived.by(() => {
    const termine = ricerca.toLowerCase()

    return fatture.filter((f) => {
      if (soloInsolute && f.pagata) return false
      return f.cliente.toLowerCase().includes(termine)
    })
  })

  // Le derived si compongono
  const totaleFiltrato = $derived(filtrate.reduce((s, f) => s + f.importo, 0))
</script>

<input bind:value={ricerca} />
<p>{filtrate.length} fatture, {totaleFiltrato} euro</p>
```

```
$derived è PIGRO e in CACHE:

  · pigro    non calcola finché qualcuno non lo legge
  · cache    ricalcola solo se una dipendenza è cambiata
  · le dipendenze sono TRACCIATE, non dichiarate

È l'equivalente di computed in Vue, e di useMemo in React
senza l'array di dipendenze.
```

### `$derived` è sovrascrivibile

```svelte
<script lang="ts">
  let fatture = $state<Fattura[]>([])

  // Da Svelte 5 una derived si può RIASSEGNARE: il valore
  // resta finché una dipendenza non cambia, poi si ricalcola.
  // È il pattern per lo stato ottimistico.
  let selezionata = $derived(fatture[0])

  function seleziona(f: Fattura) {
    selezionata = f // sovrascrive temporaneamente
  }
</script>
```

### `$derived` contro `$effect` per derivare

```svelte
<script lang="ts">
  let primo = $state('Anna')
  let secondo = $state('Rossi')

  // ✅ CORRETTO
  const completo = $derived(`${primo} ${secondo}`)

  // ❌ SBAGLIATO — un effetto per derivare: un aggiornamento
  //    in più, e uno stato che può disallinearsi
  let completoSbagliato = $state('')
  $effect(() => {
    completoSbagliato = `${primo} ${secondo}`
  })
</script>
```

---

## A5. Il markup: blocchi e direttive

```svelte
<script lang="ts">
  let stato = $state<'inattiva' | 'caricamento' | 'riuscita' | 'fallita'>('inattiva')
  let fatture = $state<Fattura[]>([])
  let promessa = $state<Promise<Fattura[]>>()
</script>

<!-- Interpolazione -->
<p>{fatture.length} fatture</p>
<p>{fatture.length > 0 ? 'Ci sono dati' : 'Vuoto'}</p>

<!-- Condizionali -->
{#if stato === 'caricamento'}
  <p>Caricamento…</p>
{:else if stato === 'fallita'}
  <p role="alert">Errore</p>
{:else}
  <p>{fatture.length} risultati</p>
{/if}

<!-- Cicli: la chiave va fra parentesi tonde -->
<ul>
  {#each fatture as fattura (fattura.id)}
    <li>{fattura.numero} — {fattura.cliente}</li>
  {:else}
    <!-- :else in un each è il caso "elenco vuoto" -->
    <li>Nessuna fattura.</li>
  {/each}
</ul>

<!-- Con l'indice -->
{#each fatture as fattura, indice (fattura.id)}
  <li>{indice + 1}. {fattura.numero}</li>
{/each}

<!-- Destructuring nel ciclo -->
{#each fatture as { id, numero, cliente } (id)}
  <li>{numero} — {cliente}</li>
{/each}

<!-- await: gestisce una Promise direttamente nel markup -->
{#await promessa}
  <p>Caricamento…</p>
{:then risultato}
  <p>{risultato.length} elementi</p>
{:catch errore}
  <p role="alert">{errore.message}</p>
{/await}

<!-- Forma breve, senza il caso pendente -->
{#await promessa then risultato}
  <p>{risultato.length}</p>
{/await}

<!-- key: distrugge e ricrea il contenuto quando l'espressione cambia -->
{#key idUtente}
  <ModuloUtente {idUtente} />
{/key}
```

### Le direttive

```svelte
<script lang="ts">
  let valore = $state('')
  let attiva = $state(false)
  let colore = $state('#1d4ed8')
  let elemento = $state<HTMLDivElement>()

  function salva() {}
  function gestisciTasto(evento: KeyboardEvent) {}
</script>

<!-- Eventi: in Svelte 5 sono attributi normali, non direttive.
     Niente on:click, ma onclick. -->
<button onclick={salva}>Salva</button>
<button onclick={() => (attiva = !attiva)}>Commuta</button>
<input onkeydown={gestisciTasto} />

<!-- I modificatori di Svelte 4 non esistono più:
     si scrivono a mano -->
<form
  onsubmit={(evento) => {
    evento.preventDefault()
    salva()
  }}
>
  <!-- ... -->
</form>

<!-- bind: collegamento bidirezionale -->
<input bind:value={valore} />
<input type="checkbox" bind:checked={attiva} />
<div bind:this={elemento}>Riferimento al nodo</div>

<!-- class: e style: condizionali -->
<div class:attiva class:in-errore={valore === ''}>…</div>
<div style:color={colore} style:font-size="1rem">…</div>

<!-- Attributi condizionali: null o undefined li rimuove -->
<button disabled={valore === '' || undefined}>Invia</button>

<!-- Spread degli attributi -->
<input {...attributiInput} />
```

---

## A6. `$props` e `$bindable`

```svelte
<!-- src/lib/componenti/Pulsante.svelte -->
<script lang="ts">
  import type { Snippet } from 'svelte'
  import type { HTMLButtonAttributes } from 'svelte/elements'

  type Props = {
    variante?: 'primario' | 'secondario' | 'pericolo'
    dimensione?: 'piccolo' | 'medio' | 'grande'
    caricamento?: boolean
    children: Snippet
  } & HTMLButtonAttributes

  let {
    variante = 'primario',
    dimensione = 'medio',
    caricamento = false,
    children,
    // Il rest raccoglie tutti gli attributi nativi
    ...resto
  }: Props = $props()
</script>

<button
  class="pulsante pulsante--{variante} pulsante--{dimensione}"
  disabled={caricamento || resto.disabled}
  aria-busy={caricamento}
  {...resto}
>
  {#if caricamento}
    <span class="solo-screen-reader">Operazione in corso</span>
  {/if}
  {@render children()}
</button>
```

```svelte
<!-- L'uso -->
<script lang="ts">
  import Pulsante from '$lib/componenti/Pulsante.svelte'
</script>

<Pulsante variante="pericolo" caricamento={inCorso} onclick={elimina}>Elimina</Pulsante>
```

### `$bindable`: props bidirezionali

```svelte
<!-- src/lib/componenti/CampoTesto.svelte -->
<script lang="ts">
  type Props = {
    valore: string
    etichetta: string
    errore?: string
  }

  // $bindable rende la prop scrivibile dal figlio.
  // Senza, modificarla produce un errore.
  let { valore = $bindable(), etichetta, errore }: Props = $props()

  const id = $props.id() // identificativo univoco e stabile
</script>

<div class="campo">
  <label for={id}>{etichetta}</label>
  <input
    {id}
    bind:value={valore}
    aria-invalid={errore !== undefined}
    aria-describedby={errore ? `${id}-errore` : undefined}
  />
  {#if errore}
    <p id="{id}-errore" role="alert">{errore}</p>
  {/if}
</div>
```

```svelte
<!-- Il genitore: bind: attiva il collegamento bidirezionale -->
<script lang="ts">
  import CampoTesto from '$lib/componenti/CampoTesto.svelte'

  let email = $state('')
</script>

<CampoTesto bind:valore={email} etichetta="Email" />
<p>Hai scritto: {email}</p>
```

```typescript
// Con un valore predefinito
let { valore = $bindable('') } = $props()
```

**Da usare con parsimonia.** Il collegamento bidirezionale rende meno evidente da dove viene un cambiamento. Per la maggior parte dei componenti, una prop in ingresso e un callback in uscita è più chiaro.

```svelte
<script lang="ts">
  // L'alternativa esplicita: nessun bind:, un callback
  type Props = {
    valore: string
    alCambiare: (nuovo: string) => void
  }

  let { valore, alCambiare }: Props = $props()
</script>

<input {valore} oninput={(e) => alCambiare(e.currentTarget.value)} />
```

---

## A7. `bind:` e i form

```svelte
<script lang="ts">
  let testo = $state('')
  let numero = $state(0)
  let accettato = $state(false)
  let scelta = $state('')
  let interessi = $state<string[]>([])
  let file = $state<FileList | null>(null)
</script>

<!-- Testo -->
<input bind:value={testo} />
<textarea bind:value={testo}></textarea>

<!-- Numero: la conversione è automatica con type="number" -->
<input type="number" bind:value={numero} />
<input type="range" bind:value={numero} min="0" max="100" />

<!-- Checkbox singola -->
<input type="checkbox" bind:checked={accettato} />

<!-- Checkbox multiple: bind:group produce un array -->
<input type="checkbox" bind:group={interessi} value="sport" />
<input type="checkbox" bind:group={interessi} value="musica" />

<!-- Radio: bind:group produce il valore selezionato -->
<input type="radio" bind:group={scelta} value="email" />
<input type="radio" bind:group={scelta} value="telefono" />

<!-- Select -->
<select bind:value={scelta}>
  <option value="">Scegli</option>
  <option value="a">A</option>
</select>

<!-- File -->
<input type="file" bind:files={file} accept="image/*" />
```

```svelte
<script lang="ts">
  let contenitore = $state<HTMLDivElement>()
  let larghezza = $state(0)
  let altezza = $state(0)
  let scorrimento = $state(0)
</script>

<!-- Legami sugli elementi: dimensioni e scorrimento, in sola lettura -->
<div bind:this={contenitore} bind:clientWidth={larghezza} bind:clientHeight={altezza}>
  Larghezza: {larghezza}px
</div>

<!-- Sulla finestra -->
<svelte:window bind:scrollY={scorrimento} />

<p>Scorrimento: {scorrimento}px</p>
```

```svelte
<!-- Legare una funzione a un elemento del ciclo:
     bind: funziona anche su una proprietà di un oggetto -->
<script lang="ts">
  let righe = $state([
    { id: '1', testo: '', quantita: 1 },
    { id: '2', testo: '', quantita: 1 },
  ])
</script>

{#each righe as riga (riga.id)}
  <input bind:value={riga.testo} />
  <input type="number" bind:value={riga.quantita} />
{/each}
```

---

# Parte B — Comprensione Profonda

---

## B1. Come funziona la compilazione

```
Il compilatore Svelte fa tre passaggi:

  1. ANALISI       legge il .svelte, costruisce un AST,
                   individua quali variabili sono reattive
                   e QUALI NODI dipendono da ciascuna

  2. TRASFORMAZIONE genera funzioni JavaScript che creano
                   i nodi del DOM e li aggiornano

  3. OTTIMIZZAZIONE il markup statico diventa un template
                   clonato una volta; solo i punti dinamici
                   ricevono un effetto di aggiornamento
```

```svelte
<script lang="ts">
  let nome = $state('Anna')
  let eta = $state(34)
</script>

<div class="scheda">
  <h2>Profilo</h2>
  <p>{nome}</p>
  <p>Età fissa: 30</p>
  <p>{eta}</p>
</div>
```

```
Il compilatore sa che:

  · <div class="scheda">, <h2>Profilo</h2> e
    <p>Età fissa: 30</p> sono STATICI
    → clonati da un template, mai toccati

  · il primo {nome} dipende SOLO da nome
    → un effetto che scrive su quel nodo di testo

  · {eta} dipende SOLO da eta
    → un effetto separato

Cambiando 'nome', si esegue una sola assegnazione:
  nodoTesto1.data = nome

Nessun confronto, nessun attraversamento dell'albero,
nessuna funzione di rendering richiamata.
```

### Cosa questo comporta

```
✅ Il bundle contiene solo ciò che usi
   Un componente che non usa le transizioni non porta
   il codice delle transizioni. Il runtime di Svelte è
   un insieme di funzioni importate su richiesta.

✅ Nessuna memoizzazione da scrivere
   Non esiste il problema del "figlio che si ridisegna
   perché il genitore è cambiato": non c'è un rendering
   del genitore da cui discendere.

✅ Il CSS non usato è un avviso di compilazione

⚠ Il compilatore deve VEDERE il codice
   La reattività funziona su ciò che è dichiarato nel
   componente o in un file .svelte.ts. Un oggetto creato
   da una libreria esterna non è reattivo.

⚠ Le rune non sono valori
   Non si possono passare, memorizzare in una variabile,
   o usare condizionalmente. Sono istruzioni al compilatore.
```

```typescript
// ❌ Le rune non sono funzioni: questo non compila
// const mioStato = $state
// const x = condizione ? $state(1) : $state(2)

// ❌ Fuori da un componente o da un file .svelte.ts non esistono
// (in un normale .ts, $state non è definito)
```

---

## B2. `$effect` e quando non usarlo

```svelte
<script lang="ts">
  let conteggio = $state(0)

  $effect(() => {
    // Le dipendenze sono TRACCIATE da ciò che viene letto
    console.log('conteggio:', conteggio)

    // La funzione restituita è la pulizia: eseguita prima
    // della prossima esecuzione e allo smontaggio
    return () => console.log('pulizia')
  })
</script>
```

```
Quando $effect si esegue:

  · dopo che il DOM è stato aggiornato
  · quando una delle dipendenze LETTE cambia
  · mai durante il rendering lato server

$effect.pre si esegue PRIMA dell'aggiornamento del DOM:
serve per leggere lo stato precedente (una posizione
di scorrimento da ripristinare).
```

### I quattro casi in cui `$effect` non serve

```svelte
<script lang="ts">
  let primo = $state('Anna')
  let secondo = $state('Rossi')
  let elenco = $state<number[]>([])

  // ── 1. DERIVARE UN VALORE ────────────────────────────────
  // ❌
  let completoSbagliato = $state('')
  $effect(() => {
    completoSbagliato = `${primo} ${secondo}`
  })

  // ✅
  const completo = $derived(`${primo} ${secondo}`)

  // ── 2. SINCRONIZZARE DUE STATI ───────────────────────────
  // ❌ Due fonti di verità che possono disallinearsi
  let totale = $state(0)
  $effect(() => {
    totale = elenco.reduce((s, n) => s + n, 0)
  })

  // ✅ Una fonte sola
  const totaleDerivato = $derived(elenco.reduce((s, n) => s + n, 0))

  // ── 3. REAGIRE A UN EVENTO ───────────────────────────────
  // ❌ Uno stato usato come segnale
  let inviato = $state(false)
  $effect(() => {
    if (inviato) {
      mostraNotifica('Inviato')
      inviato = false
    }
  })

  // ✅ La logica nel gestore
  function gestisciInvio() {
    invia()
    mostraNotifica('Inviato')
  }

  // ── 4. AZZERARE LO STATO AL CAMBIO DI UNA PROP ───────────
  // ❌ Un effetto che azzera
  // ✅ {#key idUtente} attorno al componente
</script>
```

### Quando `$effect` è la scelta giusta

```svelte
<script lang="ts">
  let query = $state('')
  let contenitore = $state<HTMLElement>()

  // Sincronizzare con un'API del browser
  $effect(() => {
    document.title = query === '' ? 'Fatture' : `Ricerca: ${query}`
  })

  // Una libreria di terze parti che manipola il DOM
  $effect(() => {
    if (!contenitore) return

    const grafico = creaGrafico(contenitore, datiCorrenti)
    return () => grafico.distruggi()
  })

  // Una connessione esterna
  $effect(() => {
    const socket = new WebSocket(url)
    socket.addEventListener('message', gestisci)
    return () => socket.close()
  })
</script>
```

### La trappola delle dipendenze inattese

```svelte
<script lang="ts">
  let a = $state(0)
  let b = $state(0)

  // ⚠ L'effetto traccia TUTTO ciò che legge SINCRONAMENTE.
  //    Qui dipende da a E da b, anche se b serve solo in un ramo.
  $effect(() => {
    if (a > 0) {
      console.log(b) // b diventa una dipendenza
    }
  })

  // untrack esclude una lettura dal tracciamento
  import { untrack } from 'svelte'

  $effect(() => {
    console.log(a)
    // b viene letto ma NON diventa una dipendenza
    console.log(untrack(() => b))
  })
</script>
```

```svelte
<script lang="ts">
  // ⚠ Ciò che viene letto DOPO un await non è tracciato:
  //    l'effetto è già uscito dal contesto di tracciamento
  $effect(() => {
    const iniziale = valore // tracciato

    void (async () => {
      await qualcosa()
      console.log(altroValore) // NON tracciato
    })()
  })
</script>
```

### `$effect.tracking` e `$inspect`

```svelte
<script lang="ts">
  let conteggio = $state(0)

  // $inspect registra ogni cambiamento, solo in sviluppo:
  // viene rimosso dalla build di produzione
  $inspect(conteggio)

  // Con un callback personalizzato
  $inspect(conteggio).with((tipo, valore) => {
    if (tipo === 'update') console.trace('conteggio aggiornato a', valore)
  })
</script>
```

---

## B3. Snippet e `{@render}`

Gli snippet sostituiscono gli slot di Svelte 4. Sono frammenti di markup riutilizzabili, passabili come props.

```svelte
<!-- src/lib/componenti/Pannello.svelte -->
<script lang="ts">
  import type { Snippet } from 'svelte'

  type Props = {
    titolo: string
    children: Snippet
    azioni?: Snippet
    piede?: Snippet
  }

  let { titolo, children, azioni, piede }: Props = $props()
</script>

<section class="pannello">
  <header>
    <h2>{titolo}</h2>
    {#if azioni}
      {@render azioni()}
    {/if}
  </header>

  <div class="corpo">
    {@render children()}
  </div>

  {#if piede}
    <footer>{@render piede()}</footer>
  {/if}
</section>
```

```svelte
<script lang="ts">
  import Pannello from '$lib/componenti/Pannello.svelte'
</script>

<Pannello titolo="Fatture recenti">
  <!-- Il contenuto senza nome diventa 'children' -->
  <TabellaFatture {fatture} />

  <!-- Gli snippet nominati -->
  {#snippet azioni()}
    <button onclick={esporta}>Esporta</button>
  {/snippet}

  {#snippet piede()}
    <p>{fatture.length} righe</p>
  {/snippet}
</Pannello>
```

### Snippet con parametri

```svelte
<!-- src/lib/componenti/ElencoDati.svelte -->
<script lang="ts" generics="T">
  import type { Snippet } from 'svelte'

  type Props = {
    elementi: readonly T[]
    chiaveDi: (elemento: T) => string | number
    riga: Snippet<[elemento: T, indice: number]>
    vuoto?: Snippet
  }

  let { elementi, chiaveDi, riga, vuoto }: Props = $props()
</script>

{#if elementi.length === 0}
  {#if vuoto}
    {@render vuoto()}
  {:else}
    <p>Nessun elemento.</p>
  {/if}
{:else}
  <ul>
    {#each elementi as elemento, indice (chiaveDi(elemento))}
      <li>{@render riga(elemento, indice)}</li>
    {/each}
  </ul>
{/if}
```

```svelte
<script lang="ts">
  import ElencoDati from '$lib/componenti/ElencoDati.svelte'

  let fatture = $state<Fattura[]>([])
</script>

<ElencoDati elementi={fatture} chiaveDi={(f) => f.id}>
  <!-- Lo snippet riceve i parametri, tipizzati -->
  {#snippet riga(fattura, indice)}
    <strong>{indice + 1}.</strong>
    {fattura.numero} — {fattura.cliente}
  {/snippet}

  {#snippet vuoto()}
    <em>Nessuna fattura nel periodo selezionato.</em>
  {/snippet}
</ElencoDati>
```

### Snippet riutilizzabili nello stesso file

```svelte
<script lang="ts">
  let righe = $state<Fattura[]>([])
</script>

<!-- Definito una volta, usato più volte -->
{#snippet importo(valore: number, evidenzia = false)}
  <span class="importo" class:evidenzia>
    {new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(valore)}
  </span>
{/snippet}

<table>
  <tbody>
    {#each righe as riga (riga.id)}
      <tr>
        <td>{riga.numero}</td>
        <td>{@render importo(riga.importo)}</td>
      </tr>
    {/each}
  </tbody>
  <tfoot>
    <tr>
      <td>Totale</td>
      <td>{@render importo(totale, true)}</td>
    </tr>
  </tfoot>
</table>
```

Gli snippet sono più flessibili degli slot: sono valori, si possono passare in giro, condizionare, e ricevere parametri tipizzati.

---

## B4. Stato condiviso: file `.svelte.ts` e classi

Le rune funzionano anche fuori dai componenti, in file con estensione `.svelte.ts`.

```typescript
// src/lib/stato/attivita.svelte.ts
// L'estensione .svelte.ts abilita le rune in un file TypeScript

export type Attivita = {
  readonly id: string
  testo: string
  completata: boolean
}

export type Filtro = 'tutte' | 'da-fare' | 'completate'

function creaStoreAttivita() {
  let elenco = $state<Attivita[]>([])
  let filtro = $state<Filtro>('tutte')
  let inCaricamento = $state(false)
  let errore = $state<Error | null>(null)

  const visibili = $derived.by(() => {
    switch (filtro) {
      case 'da-fare':
        return elenco.filter((a) => !a.completata)
      case 'completate':
        return elenco.filter((a) => a.completata)
      default:
        return elenco
    }
  })

  const conteggi = $derived({
    tutte: elenco.length,
    daFare: elenco.filter((a) => !a.completata).length,
  })

  return {
    // I getter espongono lo stato in sola lettura:
    // chi consuma non può riassegnarlo
    get elenco() {
      return elenco
    },
    get visibili() {
      return visibili
    },
    get conteggi() {
      return conteggi
    },
    get inCaricamento() {
      return inCaricamento
    },
    get errore() {
      return errore
    },
    get filtro() {
      return filtro
    },
    set filtro(nuovo: Filtro) {
      filtro = nuovo
    },

    async carica() {
      inCaricamento = true
      errore = null
      try {
        elenco = await recuperaAttivita()
      } catch (e) {
        errore = e instanceof Error ? e : new Error(String(e))
      } finally {
        inCaricamento = false
      }
    },

    aggiungi(testo: string) {
      const pulito = testo.trim()
      if (pulito === '') return
      elenco.push({ id: crypto.randomUUID(), testo: pulito, completata: false })
    },

    commuta(id: string) {
      const attivita = elenco.find((a) => a.id === id)
      if (attivita) attivita.completata = !attivita.completata
    },

    elimina(id: string) {
      const indice = elenco.findIndex((a) => a.id === id)
      if (indice !== -1) elenco.splice(indice, 1)
    },
  }
}

// Creato al primo import: è uno stato GLOBALE, condiviso
export const storeAttivita = creaStoreAttivita()
```

```svelte
<script lang="ts">
  import { storeAttivita } from '$lib/stato/attivita.svelte'
  import { onMount } from 'svelte'

  onMount(() => storeAttivita.carica())
</script>

{#if storeAttivita.errore}
  <p role="alert">{storeAttivita.errore.message}</p>
{/if}

<ul>
  {#each storeAttivita.visibili as attivita (attivita.id)}
    <li>
      <input
        type="checkbox"
        checked={attivita.completata}
        onchange={() => storeAttivita.commuta(attivita.id)}
      />
      {attivita.testo}
    </li>
  {/each}
</ul>

<p>{storeAttivita.conteggi.daFare} da fare su {storeAttivita.conteggi.tutte}</p>
```

### Le classi reattive

```typescript
// src/lib/stato/Contatore.svelte.ts
export class Contatore {
  // I campi di classe possono usare $state
  valore = $state(0)
  readonly minimo: number
  readonly massimo: number

  // I getter derivati
  puoIncrementare = $derived(this.valore < this.massimo)
  puoDecrementare = $derived(this.valore > this.minimo)

  constructor({ iniziale = 0, minimo = 0, massimo = 100 } = {}) {
    this.valore = iniziale
    this.minimo = minimo
    this.massimo = massimo
  }

  incrementa(): void {
    if (this.puoIncrementare) this.valore++
  }

  decrementa(): void {
    if (this.puoDecrementare) this.valore--
  }

  azzera(): void {
    this.valore = this.minimo
  }
}
```

```svelte
<script lang="ts">
  import { Contatore } from '$lib/stato/Contatore.svelte'

  // Ogni istanza ha il proprio stato reattivo
  const carrello = new Contatore({ massimo: 10 })
  const quantita = new Contatore({ iniziale: 1, minimo: 1, massimo: 99 })
</script>

<button onclick={() => carrello.decrementa()} disabled={!carrello.puoDecrementare}>−</button>
<span>{carrello.valore}</span>
<button onclick={() => carrello.incrementa()} disabled={!carrello.puoIncrementare}>+</button>
```

### Le classi reattive della libreria standard

```typescript
import { SvelteMap, SvelteSet, SvelteDate, SvelteURL } from 'svelte/reactivity'

// Map e Set nativi NON sono reattivi: queste versioni lo sono
const cache = new SvelteMap<string, Fattura>()
const selezionate = new SvelteSet<string>()

cache.set('f-1', fattura) // reattivo
selezionate.add('f-1') // reattivo

// Una data che si aggiorna
const adesso = new SvelteDate()
```

---

## B5. Context

```typescript
// src/lib/contesti/tema.svelte.ts
import { getContext, setContext } from 'svelte'

const CHIAVE = Symbol('tema')

export type Tema = 'chiaro' | 'scuro'

class StatoTema {
  tema = $state<Tema>('chiaro')

  cambia(nuovo: Tema): void {
    this.tema = nuovo
    document.documentElement.dataset['tema'] = nuovo
  }
}

export function creaContestoTema(): StatoTema {
  const stato = new StatoTema()
  setContext(CHIAVE, stato)
  return stato
}

export function useTema(): StatoTema {
  const stato = getContext<StatoTema | undefined>(CHIAVE)

  if (!stato) {
    throw new Error('useTema richiede un antenato che chiami creaContestoTema()')
  }

  return stato
}
```

```svelte
<!-- Il fornitore, in cima all'albero -->
<script lang="ts">
  import { creaContestoTema } from '$lib/contesti/tema.svelte'

  creaContestoTema()
</script>

<slot />
```

```svelte
<!-- Il consumatore, a qualunque profondità -->
<script lang="ts">
  import { useTema } from '$lib/contesti/tema.svelte'

  const tema = useTema()
</script>

<button onclick={() => tema.cambia(tema.tema === 'chiaro' ? 'scuro' : 'chiaro')}>
  Tema: {tema.tema}
</button>
```

```
⚠ setContext e getContext vanno chiamati durante
  l'INIZIALIZZAZIONE del componente: non dentro un
  gestore di eventi, non dopo un await.

Come in Vue, non c'è cascata: cambiando il tema si
aggiorna solo ciò che lo LEGGE.
```

---

## B6. Azioni: `use:`

Un'azione è una funzione che riceve un nodo del DOM e ne gestisce il ciclo di vita. È il modo di incapsulare la manipolazione diretta del DOM.

```typescript
// src/lib/azioni/chiudiFuori.svelte.ts
import type { Action } from 'svelte/action'

/**
 * Chiama il callback al clic fuori dall'elemento, o alla pressione di Esc.
 */
export const chiudiFuori: Action<HTMLElement, () => void> = (nodo, alChiudere) => {
  // Il callback in una variabile aggiornabile: cambiandolo
  // non serve ricreare i listener
  let callback = alChiudere

  const controller = new AbortController()

  document.addEventListener(
    'pointerdown',
    (evento) => {
      if (evento.target instanceof Node && !nodo.contains(evento.target)) {
        callback?.()
      }
    },
    { signal: controller.signal },
  )

  document.addEventListener(
    'keydown',
    (evento) => {
      if (evento.key === 'Escape') callback?.()
    },
    { signal: controller.signal },
  )

  return {
    // Chiamato quando il parametro cambia
    update(nuovoCallback) {
      callback = nuovoCallback
    },
    // Chiamato allo smontaggio: la pulizia è obbligatoria
    destroy() {
      controller.abort()
    },
  }
}
```

```svelte
<script lang="ts">
  import { chiudiFuori } from '$lib/azioni/chiudiFuori.svelte'

  let aperto = $state(false)
</script>

<button onclick={() => (aperto = true)} aria-expanded={aperto}>Apri</button>

{#if aperto}
  <div use:chiudiFuori={() => (aperto = false)} role="dialog" aria-label="Pannello">
    Contenuto
  </div>
{/if}
```

```typescript
// src/lib/azioni/osservaIntersezione.svelte.ts
import type { Action } from 'svelte/action'

type Parametri = {
  alVisibile: () => void
  margine?: string
}

export const osservaIntersezione: Action<HTMLElement, Parametri> = (nodo, parametri) => {
  let attuali = parametri

  const osservatore = new IntersectionObserver(
    ([voce]) => {
      if (voce?.isIntersecting) attuali.alVisibile()
    },
    { rootMargin: attuali.margine ?? '200px' },
  )

  osservatore.observe(nodo)

  return {
    update(nuovi) {
      attuali = nuovi
    },
    destroy() {
      osservatore.disconnect()
    },
  }
}
```

```svelte
<!-- Scorrimento infinito, in una riga -->
<div use:osservaIntersezione={{ alVisibile: caricaAltro, margine: '400px' }}>
  <span class="solo-screen-reader">Caricamento della pagina successiva</span>
</div>
```

Le azioni sono l'equivalente dei ref callback di React e delle direttive personalizzate di Vue, con un'ergonomia migliore di entrambi: ricevono i parametri, hanno `update` e `destroy`, e si compongono.

---

## B7. Transizioni e animazioni

```svelte
<script lang="ts">
  import { fade, fly, slide, scale, blur } from 'svelte/transition'
  import { flip } from 'svelte/animate'
  import { cubicOut } from 'svelte/easing'

  let visibile = $state(true)
  let righe = $state<Fattura[]>([])
</script>

<!-- transition: entrata E uscita -->
{#if visibile}
  <p transition:fade={{ duration: 200 }}>Contenuto</p>
{/if}

<!-- in: e out: separate -->
{#if visibile}
  <p in:fly={{ y: 20, duration: 300 }} out:fade={{ duration: 150 }}>Contenuto</p>
{/if}

<!-- animate: anima gli SPOSTAMENTI in una lista con chiave -->
<ul>
  {#each righe as riga (riga.id)}
    <li animate:flip={{ duration: 300, easing: cubicOut }} transition:slide>
      {riga.numero}
    </li>
  {/each}
</ul>
```

### Una transizione personalizzata

```typescript
// src/lib/transizioni.ts
import type { TransitionConfig } from 'svelte/transition'
import { cubicOut } from 'svelte/easing'

export function scorriEDissolvi(
  nodo: Element,
  { duration = 300, delay = 0 } = {},
): TransitionConfig {
  const stile = getComputedStyle(nodo)
  const altezza = parseFloat(stile.height)
  const opacitaIniziale = +stile.opacity

  return {
    duration,
    delay,
    easing: cubicOut,
    // css è preferibile a tick: l'animazione gira sul
    // compositor, fuori dal thread principale
    css: (t) => `
      height: ${t * altezza}px;
      opacity: ${t * opacitaIniziale};
      overflow: hidden;
    `,
  }
}
```

### Il rispetto della preferenza di movimento

```svelte
<script lang="ts">
  import { fade } from 'svelte/transition'
  import { MediaQuery } from 'svelte/reactivity'

  // MediaQuery è una classe reattiva: si aggiorna da sola
  const movimentoRidotto = new MediaQuery('(prefers-reduced-motion: reduce)')

  let visibile = $state(true)
</script>

{#if visibile}
  <!-- Durata zero quando l'utente ha chiesto meno movimento -->
  <p transition:fade={{ duration: movimentoRidotto.current ? 0 : 200 }}>Contenuto</p>
{/if}
```

Svelte non rispetta `prefers-reduced-motion` automaticamente: va gestito, esattamente come in React e Vue.

---

## B8. SvelteKit: routing e caricamento dei dati

Il routing è basato sui file: la struttura delle cartelle è la struttura delle rotte.

```
src/routes/
├── +layout.svelte              il guscio di tutte le pagine
├── +layout.ts                  dati per il layout
├── +page.svelte                /
├── accesso/
│   ├── +page.svelte            /accesso
│   └── +page.server.ts         azioni del form
├── fatture/
│   ├── +page.svelte            /fatture
│   ├── +page.ts                load: gira su server E client
│   └── [id]/
│       ├── +page.svelte        /fatture/:id
│       └── +page.server.ts     load: SOLO sul server
├── api/
│   └── fatture/
│       └── +server.ts          endpoint JSON
└── +error.svelte               la pagina di errore
```

### `load`: caricare i dati prima del rendering

```typescript
// src/routes/fatture/+page.ts
// Gira sul SERVER al primo caricamento, e sul CLIENT alle
// navigazioni successive. Nessun segreto qui dentro.
import type { PageLoad } from './$types'

export const load: PageLoad = async ({ fetch, url, depends }) => {
  const pagina = Number(url.searchParams.get('pagina') ?? 1)
  const ricerca = url.searchParams.get('ricerca') ?? ''

  // 'depends' registra una dipendenza personalizzata:
  // invalidate('app:fatture') riesegue questo load
  depends('app:fatture')

  // Il fetch fornito da SvelteKit inoltra i cookie e
  // funziona anche durante il rendering sul server
  const risposta = await fetch(`/api/fatture?pagina=${pagina}&ricerca=${ricerca}`)

  if (!risposta.ok) {
    throw new Error(`Caricamento non riuscito: ${risposta.status}`)
  }

  return {
    fatture: await risposta.json(),
    pagina,
    ricerca,
  }
}
```

```typescript
// src/routes/fatture/[id]/+page.server.ts
// +page.server.ts gira SOLO sul server: qui possono stare
// le chiavi segrete e l'accesso diretto al database
import { error } from '@sveltejs/kit'
import type { PageServerLoad } from './$types'
import { db } from '$lib/server/database'

export const load: PageServerLoad = async ({ params, locals }) => {
  if (!locals.utente) {
    throw error(401, 'Autenticazione richiesta')
  }

  const fattura = await db.fattura.findUnique({ where: { id: params.id } })

  if (!fattura) {
    // 'error' produce la pagina +error.svelte con questo stato
    throw error(404, 'Fattura non trovata')
  }

  return { fattura }
}
```

```svelte
<!-- src/routes/fatture/+page.svelte -->
<script lang="ts">
  import type { PageData } from './$types'

  // I dati di load arrivano come prop, già tipizzati
  let { data }: { data: PageData } = $props()
</script>

<h1>Fatture</h1>

<ul>
  {#each data.fatture as fattura (fattura.id)}
    <li><a href="/fatture/{fattura.id}">{fattura.numero}</a></li>
  {/each}
</ul>
```

### Lo streaming delle promesse

```typescript
// src/routes/+page.server.ts
import type { PageServerLoad } from './$types'

export const load: PageServerLoad = async () => {
  return {
    // Atteso: la pagina non arriva finché non è pronto
    indicatori: await recuperaIndicatori(),

    // NON atteso: la pagina arriva subito, e questo
    // fluisce dopo. Il markup lo gestisce con {#await}.
    graficoLento: recuperaGraficoLento(),
  }
}
```

```svelte
<script lang="ts">
  let { data } = $props()
</script>

<!-- Gli indicatori ci sono già -->
<Indicatori dati={data.indicatori} />

<!-- Il grafico arriva dopo, senza bloccare il resto -->
{#await data.graficoLento}
  <ScheletroGrafico />
{:then grafico}
  <Grafico dati={grafico} />
{:catch errore}
  <p role="alert">Grafico non disponibile</p>
{/await}
```

### Gli hook del server

```typescript
// src/hooks.server.ts
import type { Handle } from '@sveltejs/kit'
import { verificaToken } from '$lib/server/autenticazione'

export const handle: Handle = async ({ event, resolve }) => {
  // Eseguito per OGNI richiesta, prima del load
  const token = event.cookies.get('sessione')

  if (token) {
    try {
      event.locals.utente = await verificaToken(token)
    } catch {
      event.cookies.delete('sessione', { path: '/' })
    }
  }

  const risposta = await resolve(event)

  // Le intestazioni di sicurezza
  risposta.headers.set('X-Content-Type-Options', 'nosniff')
  risposta.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')

  return risposta
}
```

---

## B9. SvelteKit: form action e progressive enhancement

Le form action sono la funzionalità che distingue di più SvelteKit: i form funzionano **senza JavaScript**, e con JavaScript diventano migliori.

```typescript
// src/routes/fatture/nuova/+page.server.ts
import { fail, redirect } from '@sveltejs/kit'
import type { Actions, PageServerLoad } from './$types'
import { z } from 'zod'

const SchemaFattura = z.object({
  cliente: z.string().min(1, 'Il cliente è obbligatorio'),
  importo: z.coerce.number().positive('L importo deve essere positivo'),
  scadenza: z.coerce.date(),
})

export const actions: Actions = {
  // L'azione predefinita
  default: async ({ request, locals }) => {
    if (!locals.utente) throw redirect(303, '/accesso')

    const dati = Object.fromEntries(await request.formData())
    const esito = SchemaFattura.safeParse(dati)

    if (!esito.success) {
      // fail restituisce lo stato e i dati al form,
      // SENZA reindirizzare: i valori digitati non si perdono
      return fail(422, {
        errori: esito.error.flatten().fieldErrors,
        valori: dati,
      })
    }

    const creata = await db.fattura.create({ data: esito.data })

    // 303 dopo un POST: evita il reinvio al ricaricamento
    throw redirect(303, `/fatture/${creata.id}`)
  },
}
```

```svelte
<!-- src/routes/fatture/nuova/+page.svelte -->
<script lang="ts">
  import { enhance } from '$app/forms'
  import type { ActionData } from './$types'

  let { form }: { form: ActionData } = $props()

  let inInvio = $state(false)
</script>

<!--
  SENZA JavaScript: il browser invia il form normalmente,
  il server risponde con una pagina. Funziona.

  CON JavaScript: use:enhance intercetta l'invio, lo manda
  via fetch, e aggiorna la pagina senza ricaricarla.
-->
<form
  method="POST"
  use:enhance={() => {
    inInvio = true

    return async ({ update }) => {
      await update()
      inInvio = false
    }
  }}
>
  <div class="campo">
    <label for="cliente">Cliente</label>
    <input
      id="cliente"
      name="cliente"
      value={form?.valori?.cliente ?? ''}
      aria-invalid={form?.errori?.cliente ? 'true' : undefined}
      aria-describedby={form?.errori?.cliente ? 'errore-cliente' : undefined}
      required
    />
    {#if form?.errori?.cliente}
      <p id="errore-cliente" role="alert">{form.errori.cliente[0]}</p>
    {/if}
  </div>

  <div class="campo">
    <label for="importo">Importo</label>
    <input
      id="importo"
      name="importo"
      type="number"
      step="0.01"
      value={form?.valori?.importo ?? ''}
      required
    />
    {#if form?.errori?.importo}
      <p role="alert">{form.errori.importo[0]}</p>
    {/if}
  </div>

  <button type="submit" disabled={inInvio}>
    {inInvio ? 'Salvataggio…' : 'Crea la fattura'}
  </button>
</form>
```

```typescript
// Più azioni nella stessa pagina
export const actions: Actions = {
  crea: async ({ request }) => {
    /* ... */
  },
  elimina: async ({ request }) => {
    /* ... */
  },
}
```

```svelte
<!-- Si selezionano con ?/nome -->
<form method="POST" action="?/crea">…</form>
<form method="POST" action="?/elimina">…</form>
```

```
Perché le form action contano:

  · funzionano senza JavaScript — su connessioni lente,
    con JavaScript bloccato, o mentre il bundle carica
  · la validazione è sul SERVER, dove conta
  · i valori digitati non si perdono in caso di errore
  · use:enhance aggiunge l'esperienza SPA senza cambiare
    il codice del form

È il progressive enhancement applicato bene: la versione
base funziona sempre, e JavaScript la migliora.
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Da Svelte 4 a Svelte 5

**Obiettivo:** convertire un componente scritto con la sintassi precedente, spiegando ogni cambiamento.

```svelte
<!-- PARTENZA — Svelte 4 -->
<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte'
  import { writable, derived } from 'svelte/store'

  export let elenco: Fattura[] = []
  export let filtro = ''

  const dispatch = createEventDispatcher<{ seleziona: { id: string } }>()

  let conteggio = 0

  // Etichetta reattiva
  $: filtrate = elenco.filter((f) => f.cliente.includes(filtro))
  $: totale = filtrate.reduce((s, f) => s + f.importo, 0)

  // Blocco reattivo con effetto collaterale
  $: {
    console.log('filtro cambiato:', filtro)
    conteggio++
  }

  const ricerca = writable('')
  const ricercaMaiuscola = derived(ricerca, ($r) => $r.toUpperCase())

  onMount(() => {
    const id = setInterval(aggiorna, 1000)
    return () => clearInterval(id)
  })
</script>

<input bind:value={$ricerca} />
<p>{$ricercaMaiuscola}</p>

{#each filtrate as fattura (fattura.id)}
  <button on:click={() => dispatch('seleziona', { id: fattura.id })}>
    {fattura.numero}
  </button>
{/each}

<slot name="piede" />
```

```svelte
<!-- SOLUZIONE — Svelte 5 -->
<script lang="ts">
  import { onMount, type Snippet } from 'svelte'

  type Props = {
    elenco?: Fattura[]
    filtro?: string
    // I callback SOSTITUISCONO createEventDispatcher
    alSelezionare?: (id: string) => void
    piede?: Snippet
  }

  let { elenco = [], filtro = '', alSelezionare, piede }: Props = $props()

  // $state al posto di let per ciò che è reattivo
  let conteggio = $state(0)
  let ricerca = $state('')

  // $derived al posto di $:
  const filtrate = $derived(elenco.filter((f) => f.cliente.includes(filtro)))
  const totale = $derived(filtrate.reduce((s, f) => s + f.importo, 0))

  // Gli store si sostituiscono con $state + $derived
  const ricercaMaiuscola = $derived(ricerca.toUpperCase())

  // $effect al posto del blocco reattivo con effetti
  $effect(() => {
    console.log('filtro cambiato:', filtro)
    conteggio++
  })

  onMount(() => {
    const id = setInterval(aggiorna, 1000)
    return () => clearInterval(id)
  })
</script>

<!-- bind:value su un $state, senza il prefisso $ degli store -->
<input bind:value={ricerca} />
<p>{ricercaMaiuscola}</p>

{#each filtrate as fattura (fattura.id)}
  <!-- onclick invece di on:click -->
  <button onclick={() => alSelezionare?.(fattura.id)}>
    {fattura.numero}
  </button>
{/each}

<!-- Snippet invece di slot -->
{#if piede}
  {@render piede()}
{/if}
```

```
# La tabella di conversione completa:
#
#   SVELTE 4                        SVELTE 5
#   ─────────────────────────────────────────────────────────
#   export let prop                 let { prop } = $props()
#   export let prop = valore        let { prop = valore } = $props()
#   let x (reattivo)                let x = $state(...)
#   $: derivato = a + b             const derivato = $derived(a + b)
#   $: { effetto() }                $effect(() => { effetto() })
#   $: if (cond) { ... }            $effect(() => { if (cond) ... })
#   createEventDispatcher           una prop callback
#   on:click                        onclick
#   on:click|preventDefault         onclick con e.preventDefault()
#   <slot />                        {@render children()}
#   <slot name="x" />               {@render x()}
#   <slot let:valore />             {@render riga(valore)}
#   writable(0)                     $state(0)
#   derived(s, fn)                  $derived(...)
#   $store nel markup               nessun prefisso
#   beforeUpdate/afterUpdate        $effect.pre / $effect
#
#
# LE DUE DIFFERENZE CONCETTUALI:
#
# 1. $: era AMBIGUO: il compilatore non poteva distinguere
#    una derivazione da un effetto collaterale. Le rune lo
#    rendono esplicito: $derived per i valori, $effect per
#    gli effetti. È il motivo principale del cambiamento.
#
# 2. La reattività ora funziona OVUNQUE, non solo al livello
#    superiore di un componente: nei file .svelte.ts, nelle
#    classi, dentro le funzioni. Con $: era limitata al
#    corpo del componente.
#
#
# LA COMPATIBILITÀ:
#   Svelte 5 esegue ancora la sintassi di Svelte 4. La
#   migrazione può essere incrementale, un componente
#   alla volta. Lo strumento ufficiale automatizza gran
#   parte della conversione:
#
#     pnpm dlx sv migrate svelte-5
```

---

### Esercizio 2 — Un'azione riusabile con parametri

**Obiettivo:** un'azione che gestisce la navigazione da tastiera in una lista, con il roving tabindex.

```typescript
// SOLUZIONE — src/lib/azioni/navigazioneTastiera.svelte.ts
import type { Action } from 'svelte/action'

type Parametri = {
  /** Il selettore delle voci navigabili. */
  selettore: string
  /** Chiamato quando una voce viene attivata. */
  alSelezionare?: (indice: number, elemento: HTMLElement) => void
  /** Se true, dall'ultima voce si torna alla prima. */
  circolare?: boolean
  orientamento?: 'verticale' | 'orizzontale'
}

export const navigazioneTastiera: Action<HTMLElement, Parametri> = (nodo, parametri) => {
  let attuali = parametri

  function voci(): HTMLElement[] {
    return [...nodo.querySelectorAll<HTMLElement>(attuali.selettore)].filter(
      (v) => !v.hasAttribute('disabled') && v.getAttribute('aria-disabled') !== 'true',
    )
  }

  /** Roving tabindex: una sola voce raggiungibile con Tab. */
  function aggiornaTabIndex(indiceAttivo: number): void {
    voci().forEach((voce, indice) => {
      voce.tabIndex = indice === indiceAttivo ? 0 : -1
    })
  }

  function muovi(da: number, direzione: 1 | -1): void {
    const elenco = voci()
    if (elenco.length === 0) return

    let prossimo = da + direzione

    if (attuali.circolare ?? true) {
      prossimo = (prossimo + elenco.length) % elenco.length
    } else {
      prossimo = Math.max(0, Math.min(elenco.length - 1, prossimo))
    }

    elenco[prossimo]?.focus()
    aggiornaTabIndex(prossimo)
  }

  function gestisciTasto(evento: KeyboardEvent): void {
    const elenco = voci()
    const attivo = document.activeElement
    const indice = elenco.findIndex((v) => v === attivo)
    if (indice === -1) return

    const orizzontale = (attuali.orientamento ?? 'verticale') === 'orizzontale'
    const avanti = orizzontale ? 'ArrowRight' : 'ArrowDown'
    const indietro = orizzontale ? 'ArrowLeft' : 'ArrowUp'

    switch (evento.key) {
      case avanti:
        evento.preventDefault()
        muovi(indice, 1)
        break

      case indietro:
        evento.preventDefault()
        muovi(indice, -1)
        break

      case 'Home':
        evento.preventDefault()
        elenco[0]?.focus()
        aggiornaTabIndex(0)
        break

      case 'End':
        evento.preventDefault()
        elenco.at(-1)?.focus()
        aggiornaTabIndex(elenco.length - 1)
        break

      case 'Enter':
      case ' ': {
        evento.preventDefault()
        const elemento = elenco[indice]
        if (elemento) attuali.alSelezionare?.(indice, elemento)
        break
      }

      default:
        // Ricerca digitando una lettera
        if (evento.key.length === 1 && /\S/.test(evento.key)) {
          const lettera = evento.key.toLowerCase()
          const dopo = elenco.findIndex(
            (v, i) => i > indice && v.textContent?.trim().toLowerCase().startsWith(lettera),
          )
          const daCapo = elenco.findIndex((v) =>
            v.textContent?.trim().toLowerCase().startsWith(lettera),
          )
          const trovato = dopo !== -1 ? dopo : daCapo

          if (trovato !== -1) {
            evento.preventDefault()
            elenco[trovato]?.focus()
            aggiornaTabIndex(trovato)
          }
        }
    }
  }

  function gestisciFocus(evento: FocusEvent): void {
    const elenco = voci()
    const indice = elenco.findIndex((v) => v === evento.target)
    if (indice !== -1) aggiornaTabIndex(indice)
  }

  nodo.addEventListener('keydown', gestisciTasto)
  nodo.addEventListener('focusin', gestisciFocus)

  // Stato iniziale del roving tabindex
  aggiornaTabIndex(0)

  return {
    update(nuovi) {
      attuali = nuovi
      aggiornaTabIndex(0)
    },
    destroy() {
      nodo.removeEventListener('keydown', gestisciTasto)
      nodo.removeEventListener('focusin', gestisciFocus)
    },
  }
}
```

```svelte
<!-- L'uso -->
<script lang="ts">
  import { navigazioneTastiera } from '$lib/azioni/navigazioneTastiera.svelte'

  let voci = $state([
    { id: '1', etichetta: 'Panoramica' },
    { id: '2', etichetta: 'Fatture' },
    { id: '3', etichetta: 'Clienti' },
  ])

  let selezionata = $state<string | null>(null)
</script>

<ul
  role="listbox"
  aria-label="Sezioni"
  use:navigazioneTastiera={{
    selettore: '[role="option"]',
    alSelezionare: (indice) => (selezionata = voci[indice]?.id ?? null),
    orientamento: 'verticale',
  }}
>
  {#each voci as voce (voce.id)}
    <li
      role="option"
      aria-selected={selezionata === voce.id}
      onclick={() => (selezionata = voce.id)}
    >
      {voce.etichetta}
    </li>
  {/each}
</ul>
```

```
# Perché un'azione è il posto giusto per questa logica:
#
# 1. È MANIPOLAZIONE DIRETTA DEL DOM.
#    Leggere document.activeElement, chiamare focus(),
#    impostare tabIndex: non è stato dell'applicazione,
#    è comportamento del widget.
#
# 2. IL CICLO DI VITA È GESTITO.
#    update quando i parametri cambiano, destroy allo
#    smontaggio. In React servirebbe un useEffect con
#    le dipendenze corrette; in Vue una direttiva
#    personalizzata con mounted/updated/unmounted.
#
# 3. SI RIUSA OVUNQUE.
#    La stessa azione serve un listbox, un menu, una
#    barra di schede: cambia solo il selettore.
#
# IL ROVING TABINDEX:
#   una sola voce ha tabIndex 0, le altre -1. Tab entra
#   e esce dal widget; dentro ci si muove con le frecce.
#   È il pattern richiesto da ARIA per i widget composti,
#   e senza di esso Tab passerebbe per tutte le voci.
```

---

### Esercizio 3 — Uno store condiviso con `.svelte.ts`

**Obiettivo:** uno store globale con persistenza, sincronizzazione fra schede e aggiornamento ottimistico.

```typescript
// SOLUZIONE — src/lib/stato/preferenze.svelte.ts
import { browser } from '$app/environment'
import { z } from 'zod'

const CHIAVE = 'app:preferenze:v1'

const SchemaPreferenze = z.object({
  tema: z.enum(['chiaro', 'scuro', 'sistema']).catch('sistema'),
  righePerPagina: z.number().int().min(10).max(200).catch(50),
  colonneVisibili: z.array(z.string()).catch(['numero', 'importo']),
})

export type Preferenze = z.infer<typeof SchemaPreferenze>

const PREDEFINITE: Preferenze = SchemaPreferenze.parse({})

function creaStorePreferenze() {
  // browser è false durante il rendering sul server:
  // localStorage non esiste lì
  let valori = $state<Preferenze>(browser ? carica() : PREDEFINITE)

  function carica(): Preferenze {
    try {
      const grezzo = localStorage.getItem(CHIAVE)
      if (grezzo === null) return PREDEFINITE

      // localStorage non è fidato: va validato
      return SchemaPreferenze.parse(JSON.parse(grezzo))
    } catch {
      return PREDEFINITE
    }
  }

  function salva(nuove: Preferenze): void {
    if (!browser) return
    try {
      localStorage.setItem(CHIAVE, JSON.stringify(nuove))
    } catch (errore) {
      console.warn('Preferenze non salvate', errore)
    }
  }

  // La sincronizzazione fra schede: l'evento storage
  // scatta nelle ALTRE schede dello stesso dominio
  if (browser) {
    window.addEventListener('storage', (evento) => {
      if (evento.key !== CHIAVE || evento.newValue === null) return

      try {
        valori = SchemaPreferenze.parse(JSON.parse(evento.newValue))
      } catch {
        /* valore non valido da un'altra scheda: si ignora */
      }
    })
  }

  return {
    get valori() {
      return valori
    },

    get tema() {
      return valori.tema
    },

    imposta<K extends keyof Preferenze>(chiave: K, valore: Preferenze[K]): void {
      const nuove = { ...valori, [chiave]: valore }
      valori = nuove
      salva(nuove)
    },

    azzera(): void {
      valori = PREDEFINITE
      salva(PREDEFINITE)
    },
  }
}

export const preferenze = creaStorePreferenze()
```

```svelte
<!-- L'uso -->
<script lang="ts">
  import { preferenze } from '$lib/stato/preferenze.svelte'
</script>

<fieldset>
  <legend>Aspetto</legend>

  {#each (['chiaro', 'scuro', 'sistema'] as const) as opzione}
    <label>
      <input
        type="radio"
        name="tema"
        value={opzione}
        checked={preferenze.tema === opzione}
        onchange={() => preferenze.imposta('tema', opzione)}
      />
      {opzione}
    </label>
  {/each}
</fieldset>

<label>
  Righe per pagina
  <input
    type="number"
    min="10"
    max="200"
    value={preferenze.valori.righePerPagina}
    onchange={(e) => preferenze.imposta('righePerPagina', Number(e.currentTarget.value))}
  />
</label>
```

```
# I punti che rendono lo store corretto:
#
# 1. 'browser' PRIMA DI TOCCARE localStorage.
#    Durante il rendering sul server localStorage non esiste:
#    senza la verifica, la pagina fallisce in produzione
#    e funziona in sviluppo con SSR disattivato.
#
# 2. VALIDAZIONE CON ZOD.
#    localStorage è modificabile dall'utente, e una versione
#    precedente dell'applicazione può averci scritto una forma
#    diversa. .catch() dà un ripiego PER CAMPO invece di
#    scartare tutto.
#
# 3. I GETTER ESPONGONO IN SOLA LETTURA.
#    Chi consuma legge preferenze.tema ma non può assegnarlo:
#    deve passare da imposta(), che salva anche.
#
# 4. LA SINCRONIZZAZIONE FRA SCHEDE.
#    L'evento storage non scatta nella scheda che ha scritto:
#    solo nelle altre. È esattamente il comportamento voluto.
#
# CONFRONTO CON GLI ALTRI FRAMEWORK:
#   in React servirebbe un Context più un provider, o Zustand.
#   In Vue, un composable con lo stato fuori dalla funzione,
#   oppure Pinia.
#   In Svelte 5 basta un file .svelte.ts con $state al livello
#   del modulo: è la forma più diretta delle tre.
```

---

### Esercizio 4 — Un form SvelteKit che funziona senza JavaScript

**Obiettivo:** un form di registrazione con validazione sul server, che funziona anche con JavaScript disattivato e migliora quando è attivo.

```typescript
// SOLUZIONE — src/routes/registrazione/+page.server.ts
import { fail, redirect } from '@sveltejs/kit'
import { z } from 'zod'
import type { Actions, PageServerLoad } from './$types'

const SchemaRegistrazione = z
  .object({
    nome: z.string().trim().min(1, 'Il nome è obbligatorio').max(100),
    email: z.string().trim().email('Indirizzo non valido'),
    password: z.string().min(12, 'La password deve avere almeno 12 caratteri'),
    conferma: z.string(),
    termini: z.literal('on', { errorMap: () => ({ message: 'Devi accettare i termini' }) }),
  })
  .refine((d) => d.password === d.conferma, {
    message: 'Le password non coincidono',
    path: ['conferma'],
  })

export const load: PageServerLoad = async ({ locals }) => {
  // Chi è già autenticato non deve vedere la registrazione
  if (locals.utente) throw redirect(303, '/')
  return {}
}

export const actions: Actions = {
  default: async ({ request, cookies, getClientAddress }) => {
    const dati = await request.formData()
    const grezzi = Object.fromEntries(dati)

    const esito = SchemaRegistrazione.safeParse(grezzi)

    if (!esito.success) {
      return fail(422, {
        errori: esito.error.flatten().fieldErrors,
        // I valori digitati tornano al form: senza, l'utente
        // dovrebbe riscrivere tutto. MAI restituire le password.
        valori: {
          nome: String(grezzi['nome'] ?? ''),
          email: String(grezzi['email'] ?? ''),
        },
      })
    }

    const esistente = await db.utente.findUnique({ where: { email: esito.data.email } })

    if (esistente) {
      return fail(409, {
        errori: { email: ['Questo indirizzo è già registrato'] },
        valori: { nome: esito.data.nome, email: esito.data.email },
      })
    }

    const utente = await db.utente.create({
      data: {
        nome: esito.data.nome,
        email: esito.data.email,
        passwordHash: await hashPassword(esito.data.password),
      },
    })

    const sessione = await creaSessione(utente.id, getClientAddress())

    cookies.set('sessione', sessione.token, {
      path: '/',
      httpOnly: true, // inaccessibile a JavaScript
      secure: true, // solo HTTPS
      sameSite: 'lax', // protezione CSRF
      maxAge: 60 * 60 * 24 * 7,
    })

    // 303 dopo un POST: il ricaricamento non reinvia il form
    throw redirect(303, '/')
  },
}
```

```svelte
<!-- src/routes/registrazione/+page.svelte -->
<script lang="ts">
  import { enhance } from '$app/forms'
  import type { ActionData } from './$types'

  let { form }: { form: ActionData } = $props()

  let inInvio = $state(false)
  // Il riferimento al primo campo in errore, per il focus
  let primoErrore = $state<HTMLElement | null>(null)

  // Quando arrivano errori, il focus va sul primo campo
  // interessato: senza, chi usa la tastiera non sa cosa correggere
  $effect(() => {
    if (form?.errori) {
      const primo = Object.keys(form.errori)[0]
      if (primo) {
        document.getElementById(primo)?.focus()
      }
    }
  })
</script>

<svelte:head>
  <title>Registrazione — Acme</title>
</svelte:head>

<h1>Crea un account</h1>

<form
  method="POST"
  use:enhance={() => {
    inInvio = true

    return async ({ update, result }) => {
      // reset: false conserva i valori digitati in caso di errore
      await update({ reset: result.type === 'redirect' })
      inInvio = false
    }
  }}
>
  <!-- Il riepilogo degli errori, annunciato -->
  {#if form?.errori}
    <div role="alert" class="riepilogo-errori">
      <h2>Correggi i seguenti errori</h2>
      <ul>
        {#each Object.entries(form.errori) as [campo, messaggi]}
          <li><a href="#{campo}">{messaggi?.[0]}</a></li>
        {/each}
      </ul>
    </div>
  {/if}

  <div class="campo">
    <label for="nome">Nome</label>
    <input
      id="nome"
      name="nome"
      value={form?.valori?.nome ?? ''}
      autocomplete="name"
      aria-invalid={form?.errori?.nome ? 'true' : undefined}
      aria-describedby={form?.errori?.nome ? 'errore-nome' : undefined}
      required
    />
    {#if form?.errori?.nome}
      <p id="errore-nome" class="errore">{form.errori.nome[0]}</p>
    {/if}
  </div>

  <div class="campo">
    <label for="email">Email</label>
    <input
      id="email"
      name="email"
      type="email"
      value={form?.valori?.email ?? ''}
      autocomplete="email"
      aria-invalid={form?.errori?.email ? 'true' : undefined}
      aria-describedby={form?.errori?.email ? 'errore-email' : undefined}
      required
    />
    {#if form?.errori?.email}
      <p id="errore-email" class="errore">{form.errori.email[0]}</p>
    {/if}
  </div>

  <div class="campo">
    <label for="password">Password</label>
    <input
      id="password"
      name="password"
      type="password"
      autocomplete="new-password"
      minlength="12"
      aria-describedby="aiuto-password {form?.errori?.password ? 'errore-password' : ''}"
      required
    />
    <p id="aiuto-password" class="aiuto">Almeno 12 caratteri.</p>
    {#if form?.errori?.password}
      <p id="errore-password" class="errore">{form.errori.password[0]}</p>
    {/if}
  </div>

  <div class="campo">
    <label for="conferma">Conferma la password</label>
    <input id="conferma" name="conferma" type="password" autocomplete="new-password" required />
    {#if form?.errori?.conferma}
      <p class="errore">{form.errori.conferma[0]}</p>
    {/if}
  </div>

  <div class="campo-scelta">
    <input id="termini" name="termini" type="checkbox" required />
    <label for="termini">Accetto i <a href="/termini">termini di servizio</a></label>
    {#if form?.errori?.termini}
      <p class="errore">{form.errori.termini[0]}</p>
    {/if}
  </div>

  <button type="submit" disabled={inInvio}>
    {inInvio ? 'Creazione in corso…' : 'Crea l account'}
  </button>
</form>
```

```
# LA PROVA CHE CONTA:
#
#   DevTools → Impostazioni → Debugger → Disable JavaScript
#   Ricarica e prova il form.
#
#   Deve funzionare COMPLETAMENTE: invio, validazione,
#   messaggi d'errore, valori conservati, registrazione,
#   reindirizzamento. Se qualcosa si rompe, use:enhance
#   sta nascondendo una funzionalità mancante.
#
#
# COSA JAVASCRIPT AGGIUNGE, e cosa NON deve aggiungere:
#
#   ✅ aggiunge: nessun ricaricamento della pagina,
#      lo stato "invio in corso", il focus sul primo errore
#
#   ❌ NON aggiunge: la validazione (è sul server),
#      il salvataggio, la sicurezza
#
#
# I DETTAGLI CHE FANNO LA DIFFERENZA:
#
#   · fail() invece di throw error(): restituisce i dati
#     al form senza reindirizzare
#   · i valori tornano al form, MENO LE PASSWORD
#   · redirect 303 dopo il POST: il ricaricamento non reinvia
#   · httpOnly + secure + sameSite sul cookie di sessione
#   · il riepilogo degli errori con role="alert" e i link
#     ai campi: è il pattern raccomandato da WCAG per i form
#   · il focus sul primo campo in errore
#
#
# PERCHÉ QUESTO È IL PUNTO DI FORZA DI SVELTEKIT:
#   in React o Vue, un form che funziona senza JavaScript
#   richiede di scrivere due percorsi: uno per il POST
#   tradizionale e uno per il fetch. Qui è lo stesso codice,
#   e use:enhance è un'aggiunta di sette righe.
```

---

### Esercizio 5 — Confronto dei tre framework a parità di funzionalità

**Obiettivo:** lo stesso componente in React, Vue e Svelte. Misurare cosa serve in ciascuno.

```svelte
<!-- SVELTE 5 -->
<script lang="ts">
  type Voce = { valore: number; quando: number }

  let { minimo = 0, massimo = 10 } = $props()

  let valore = $state(minimo)
  let cronologia = $state<Voce[]>([])

  const puoIncrementare = $derived(valore < massimo)
  const puoDecrementare = $derived(valore > minimo)

  function cambia(delta: number) {
    const nuovo = Math.min(massimo, Math.max(minimo, valore + delta))
    if (nuovo === valore) return

    cronologia.push({ valore, quando: Date.now() })
    valore = nuovo
  }

  function annulla() {
    const ultima = cronologia.pop()
    if (ultima) valore = ultima.valore
  }
</script>

<div>
  <p aria-live="polite">{valore}</p>
  <button onclick={() => cambia(-1)} disabled={!puoDecrementare}>−</button>
  <button onclick={() => cambia(1)} disabled={!puoIncrementare}>+</button>
  <button onclick={annulla} disabled={cronologia.length === 0}>Annulla</button>
</div>
```

```
# IL CONFRONTO COMPLETO — stessa funzionalità, tre framework:
#
#                          REACT       VUE        SVELTE
#   ──────────────────────────────────────────────────────
#   Righe di logica          30         18          16
#   Dichiarare lo stato    useState    ref()      $state()
#   Valore derivato        useMemo     computed   $derived
#     dipendenze            a mano     dedotte    dedotte
#   Funzioni stabili      useCallback  non serve  non serve
#   Aggiornare un array    [...c, x]   push()     push()
#   Accedere al valore      .value      .value     diretto
#     (nel JS)             implicito
#
#   Bundle del framework    ~45 kB      ~34 kB     ~2-5 kB
#     (gzip, minimo)                              (cresce con
#                                                  il codice)
#
#
# DOVE OGNUNO È MIGLIORE:
#
#   REACT     ecosistema più grande, più persone lo conoscono,
#             React Native, il modello mentale è uniforme
#             (tutto è una funzione)
#
#   VUE       equilibrio fra ergonomia e diffusione,
#             documentazione eccellente, Nuxt maturo,
#             la reattività fine senza compilazione
#
#   SVELTE    meno codice per lo stesso risultato,
#             bundle più piccolo, SvelteKit ha le migliori
#             form action e il progressive enhancement
#             più naturale dei tre
#
#
# I COSTI, onestamente:
#
#   REACT     memoizzazione da gestire (finché il Compiler
#             non è ovunque), 31 array di dipendenze in un
#             progetto medio
#
#   VUE       due sistemi di reattività (ref/reactive),
#             .value, il template è un secondo linguaggio
#
#   SVELTE    ecosistema più piccolo, meno persone disponibili
#             sul mercato, le rune sono nuove e la migrazione
#             da Svelte 4 è ancora in corso in molti progetti
#
#
# LA SCELTA NON È TECNICA:
#   tutti e tre risolvono il problema. Conta chi lavorerà
#   sul progetto, quali librerie servono, e quanto a lungo
#   il progetto vivrà. Un team che conosce React produrrà
#   codice migliore in React che in Svelte, anche se Svelte
#   richiede meno righe.
```

---

## C2. Mini-progetto: la dashboard, in SvelteKit

Lo stesso progetto di React e Vue, per completare il confronto.

### Struttura

```
dashboard-sveltekit/
├── src/
│   ├── app.html
│   ├── app.d.ts                 i tipi di App.Locals
│   ├── hooks.server.ts          autenticazione per ogni richiesta
│   ├── lib/
│   │   ├── server/
│   │   │   ├── database.ts      SOLO server: $lib/server è protetto
│   │   │   └── autenticazione.ts
│   │   ├── stato/
│   │   │   └── preferenze.svelte.ts
│   │   ├── azioni/
│   │   │   └── navigazioneTastiera.svelte.ts
│   │   └── componenti/
│   │       ├── SchedaIndicatore.svelte
│   │       └── TabellaDati.svelte
│   └── routes/
│       ├── +layout.svelte
│       ├── +layout.server.ts    l'utente, per ogni pagina
│       ├── +page.svelte         panoramica
│       ├── +error.svelte
│       ├── accesso/
│       │   ├── +page.svelte
│       │   └── +page.server.ts
│       └── fatture/
│           ├── +page.svelte
│           └── +page.server.ts
```

### `src/app.d.ts`

```typescript
// I tipi globali di SvelteKit
declare global {
  namespace App {
    interface Locals {
      utente: {
        readonly id: string
        readonly nome: string
        readonly ruoli: readonly string[]
      } | null
    }

    interface PageData {
      utente: App.Locals['utente']
    }

    interface Error {
      codice?: string
    }
  }
}

export {}
```

### `src/hooks.server.ts`

```typescript
import { redirect, type Handle } from '@sveltejs/kit'
import { verificaSessione } from '$lib/server/autenticazione'

const ROTTE_PROTETTE = ['/fatture', '/impostazioni']
const ROTTE_ADMIN = ['/impostazioni']

export const handle: Handle = async ({ event, resolve }) => {
  // 1. Autenticazione: eseguita per OGNI richiesta
  const token = event.cookies.get('sessione')
  event.locals.utente = null

  if (token) {
    try {
      event.locals.utente = await verificaSessione(token)
    } catch {
      event.cookies.delete('sessione', { path: '/' })
    }
  }

  // 2. Autorizzazione: centralizzata, non ripetuta in ogni load
  const percorso = event.url.pathname

  if (ROTTE_PROTETTE.some((r) => percorso.startsWith(r)) && !event.locals.utente) {
    throw redirect(303, `/accesso?da=${encodeURIComponent(percorso)}`)
  }

  if (
    ROTTE_ADMIN.some((r) => percorso.startsWith(r)) &&
    !event.locals.utente?.ruoli.includes('admin')
  ) {
    throw redirect(303, '/non-autorizzato')
  }

  const risposta = await resolve(event)

  // 3. Le intestazioni di sicurezza, su ogni risposta
  risposta.headers.set('X-Content-Type-Options', 'nosniff')
  risposta.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  risposta.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')

  return risposta
}
```

### `src/routes/fatture/+page.server.ts`

```typescript
import { fail } from '@sveltejs/kit'
import type { Actions, PageServerLoad } from './$types'
import { db } from '$lib/server/database'

export const load: PageServerLoad = async ({ url, locals, depends }) => {
  depends('app:fatture')

  const pagina = Math.max(1, Number(url.searchParams.get('pagina') ?? 1))
  const ricerca = url.searchParams.get('ricerca') ?? ''
  const stato = url.searchParams.get('stato') ?? ''
  const perPagina = 50

  const [elementi, totale] = await Promise.all([
    db.fattura.findMany({
      where: {
        clienteId: locals.utente!.id,
        ...(ricerca ? { cliente: { contains: ricerca, mode: 'insensitive' } } : {}),
        ...(stato ? { stato } : {}),
      },
      skip: (pagina - 1) * perPagina,
      take: perPagina,
      orderBy: { numero: 'desc' },
    }),
    db.fattura.count({ where: { clienteId: locals.utente!.id } }),
  ])

  return {
    fatture: elementi,
    totale,
    pagina,
    perPagina,
    filtri: { ricerca, stato },
  }
}

export const actions: Actions = {
  paga: async ({ request, locals }) => {
    const dati = await request.formData()
    const id = String(dati.get('id') ?? '')

    if (id === '') return fail(400, { messaggio: 'Identificativo mancante' })

    try {
      await db.fattura.update({
        where: { id, clienteId: locals.utente!.id },
        data: { pagata: true, pagataIl: new Date() },
      })
      return { successo: true }
    } catch {
      return fail(500, { messaggio: 'Aggiornamento non riuscito' })
    }
  },
}
```

### `src/routes/fatture/+page.svelte`

```svelte
<script lang="ts">
  import { enhance } from '$app/forms'
  import { goto } from '$app/navigation'
  import { page } from '$app/state'
  import type { PageData, ActionData } from './$types'

  let { data, form }: { data: PageData; form: ActionData } = $props()

  // Il filtro è locale, ma si sincronizza con l'URL:
  // la pagina resta condivisibile e il pulsante indietro funziona
  let ricerca = $state(data.filtri.ricerca)
  let temporizzatore: ReturnType<typeof setTimeout> | null = null

  function aggiornaRicerca(valore: string) {
    ricerca = valore

    if (temporizzatore !== null) clearTimeout(temporizzatore)

    temporizzatore = setTimeout(() => {
      const parametri = new URLSearchParams(page.url.searchParams)

      if (valore === '') {
        parametri.delete('ricerca')
      } else {
        parametri.set('ricerca', valore)
      }
      parametri.delete('pagina')

      // keepFocus: il campo non perde il focus durante la navigazione
      // noScroll: la pagina non salta in cima
      void goto(`?${parametri}`, { keepFocus: true, noScroll: true, replaceState: true })
    }, 300)
  }

  const totalePagine = $derived(Math.ceil(data.totale / data.perPagina))
</script>

<svelte:head>
  <title>Fatture — Acme</title>
</svelte:head>

<h1>Fatture</h1>

{#if form?.messaggio}
  <p role="alert">{form.messaggio}</p>
{/if}

<div class="filtri">
  <label for="ricerca">Cerca</label>
  <input
    id="ricerca"
    type="search"
    value={ricerca}
    oninput={(e) => aggiornaRicerca(e.currentTarget.value)}
  />
</div>

<p role="status" aria-live="polite">{data.totale} fatture</p>

<table>
  <caption>Fatture — pagina {data.pagina} di {totalePagine}</caption>
  <thead>
    <tr>
      <th scope="col">Numero</th>
      <th scope="col">Cliente</th>
      <th scope="col" class="numerico">Importo</th>
      <th scope="col">Azioni</th>
    </tr>
  </thead>
  <tbody>
    {#each data.fatture as fattura (fattura.id)}
      <tr>
        <th scope="row">{fattura.numero}</th>
        <td>{fattura.cliente}</td>
        <td class="numerico">{fattura.importo}</td>
        <td>
          {#if !fattura.pagata}
            <!-- Il form funziona anche senza JavaScript -->
            <form method="POST" action="?/paga" use:enhance>
              <input type="hidden" name="id" value={fattura.id} />
              <button type="submit">
                Segna pagata<span class="solo-screen-reader"> la fattura {fattura.numero}</span>
              </button>
            </form>
          {:else}
            <span>Pagata</span>
          {/if}
        </td>
      </tr>
    {/each}
  </tbody>
</table>

<nav aria-label="Paginazione">
  <a href="?pagina={data.pagina - 1}" aria-disabled={data.pagina === 1}>Precedente</a>
  <span>{data.pagina} / {totalePagine}</span>
  <a href="?pagina={data.pagina + 1}" aria-disabled={data.pagina === totalePagine}>Successiva</a>
</nav>
```

### Verifica

```
# 1. SENZA JAVASCRIPT — il controllo che distingue SvelteKit
#    DevTools → Disable JavaScript, ricarica.
#    · La pagina si vede
#    · La navigazione funziona
#    · "Segna pagata" funziona
#    · L'accesso funziona
#    Se qualcosa si rompe, la funzionalità dipende da
#    JavaScript senza motivo.
#
# 2. ROUTING E PROTEZIONE
#    /fatture da anonimo → /accesso?da=%2Ffatture
#    Dopo l'accesso si torna alla destinazione originale.
#    La protezione è in hooks.server.ts: centralizzata,
#    non ripetuta in ogni load.
#
# 3. I SEGRETI RESTANO SUL SERVER
#    · $lib/server/* NON può essere importato dal client:
#      SvelteKit lo impedisce in compilazione
#    · +page.server.ts gira solo sul server
#    · Verifica: cerca la stringa di connessione al database
#      nel bundle
#        Select-String -Path ".svelte-kit/output/client/**/*.js" -Pattern "postgres://"
#      Non deve trovare nulla.
#
# 4. STATO NELL'URL
#    Filtra, copia l'indirizzo, apri in una scheda nuova:
#    gli stessi filtri. Il pulsante indietro li ripercorre.
#
# 5. IL BUNDLE
#    pnpm build
#    Confronta la dimensione con le versioni React e Vue
#    dello stesso progetto.
#
# 6. TIPI
#    pnpm exec svelte-check
```

```
# Il confronto finale, sulle tre versioni della stessa dashboard:
#
#                          React      Vue      SvelteKit
#   ──────────────────────────────────────────────────────
#   File del progetto        24        21          19
#   Righe di codice        ~1.450   ~1.180      ~980
#   JS del framework        45 kB     34 kB       6 kB
#   JS totale (gzip)        89 kB     71 kB      38 kB
#   Funziona senza JS        no        no         SÌ
#
# La riga che conta di più è l'ultima. React e Vue possono
# fare rendering sul server (con Next e Nuxt), ma le
# interazioni restano dipendenti da JavaScript. In SvelteKit
# il progressive enhancement è il comportamento predefinito:
# scrivi un form normale, e funziona.
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Il modello di reattività a grana fine

Svelte 5 ha sostituito la reattività basata sulla compilazione di Svelte 4 con **i segnali**: lo stesso modello di Solid, Vue e Angular moderno.

```
                    SVELTE 4                  SVELTE 5

Come funziona       il compilatore            segnali: ogni $state
                    inseriva invalidate()     è una sorgente che
                    dopo ogni assegnazione    notifica i suoi lettori

Granularità         il COMPONENTE si          solo gli effetti che
                    ri-eseguiva               LEGGONO quel valore

Dove funziona       solo nel corpo del        ovunque: .svelte.ts,
                    componente                classi, funzioni

$: era              ambiguo: derivazione      $derived e $effect
                    o effetto?                sono distinti
```

```typescript
// Il modello dei segnali, in forma minima
type Segnale<T> = {
  leggi(): T
  scrivi(valore: T): void
}

let effettoCorrente: (() => void) | null = null

function creaSegnale<T>(iniziale: T): Segnale<T> {
  let valore = iniziale
  const lettori = new Set<() => void>()

  return {
    leggi() {
      // Chi legge si registra
      if (effettoCorrente !== null) lettori.add(effettoCorrente)
      return valore
    },

    scrivi(nuovo: T) {
      if (Object.is(valore, nuovo)) return
      valore = nuovo
      // Notifica solo chi aveva letto
      for (const lettore of [...lettori]) lettore()
    },
  }
}

function creaEffetto(funzione: () => void): void {
  const eseguibile = () => {
    effettoCorrente = eseguibile
    try {
      funzione()
    } finally {
      effettoCorrente = null
    }
  }
  eseguibile()
}
```

### Il push-pull di Svelte 5

```
Svelte 5 non è puramente push né puramente pull:

  PUSH   quando un $state cambia, marca i suoi dipendenti
         come "sporchi" — senza ricalcolarli

  PULL   quando qualcuno LEGGE un $derived sporco,
         allora viene ricalcolato

Il risultato: una derived che nessuno legge non viene
mai calcolata, anche se le sue dipendenze cambiano
mille volte.
```

```typescript
// La dimostrazione
let a = $state(0)

const costosa = $derived.by(() => {
  console.log('calcolo costoso')
  return a * 2
})

a = 1
a = 2
a = 3
// Nessun log: nessuno ha letto 'costosa'

console.log(costosa) // ora sì: un solo calcolo, non tre
```

### `$state.raw` e il costo del Proxy

```typescript
// $state avvolge in un Proxy RICORSIVO: ogni oggetto
// annidato viene reso reattivo alla prima lettura.
// Su strutture con migliaia di nodi, ha un costo.

// ❌ 50.000 oggetti resi reattivi, ognuno con il suo Proxy
let righe = $state<Fattura[]>(cinquantamila)

// ✅ Nessun Proxy: solo la sostituzione di righe è reattiva
let righeGrezze = $state.raw<Fattura[]>(cinquantamila)

// Il costo si sposta sulla sostituzione, che va fatta
// per intero invece che con push
righeGrezze = [...righeGrezze, nuova]
```

```typescript
// Misurare la differenza
function misura(nome: string, funzione: () => void) {
  const inizio = performance.now()
  funzione()
  console.log(`${nome}: ${(performance.now() - inizio).toFixed(1)} ms`)
}
```

```
Valori indicativi su 50.000 oggetti con cinque campi:

  $state      creazione ~180 ms, lettura completa ~90 ms
  $state.raw  creazione   ~2 ms, lettura completa  ~8 ms

La differenza conta solo su strutture grandi. Sotto
qualche migliaio di elementi è impercettibile, e la
reattività profonda vale la comodità.
```

### `untrack` e il controllo del tracciamento

```typescript
import { untrack } from 'svelte'

let a = $state(0)
let b = $state(0)

// L'effetto dipende solo da 'a'
$effect(() => {
  console.log(a)
  // b viene letto, ma non registrato come dipendenza
  const istantanea = untrack(() => b)
  registra(a, istantanea)
})
```

```typescript
// Il caso d'uso: un effetto che deve reagire a una cosa
// ma leggerne altre senza dipenderci
$effect(() => {
  // Reagisce ai cambiamenti di 'filtro'
  const f = filtro

  // Legge le opzioni correnti senza reagire ai loro cambiamenti
  untrack(() => {
    salvaRicerca(f, opzioni.perPagina, opzioni.ordine)
  })
})
```

---

## D2. Migrare da Svelte 4 a Svelte 5

```powershell
# Lo strumento ufficiale automatizza gran parte della conversione
pnpm dlx sv migrate svelte-5
```

```
Cosa lo strumento fa:

  ✅ export let → $props()
  ✅ $: derivato → $derived
  ✅ on:evento → onevento
  ✅ <slot> → {@render children()}
  ✅ createEventDispatcher → props callback (parzialmente)

Cosa NON fa, e resta a mano:

  ❌ distinguere $: che derivano da $: che hanno effetti
     (li converte tutti in $derived, e quelli con effetti
      vanno riscritti in $effect)
  ❌ gli store: writable/derived continuano a funzionare,
     ma la conversione a $state va fatta a giudizio
  ❌ i modificatori degli eventi: |preventDefault va scritto
  ❌ le librerie di terze parti non ancora aggiornate
```

### Gli store continuano a funzionare

```typescript
// Gli store di Svelte 4 sono ancora supportati:
// la migrazione può essere incrementale
import { writable, derived, get } from 'svelte/store'

export const ricerca = writable('')
export const maiuscola = derived(ricerca, ($r) => $r.toUpperCase())
```

```svelte
<script lang="ts">
  import { ricerca, maiuscola } from '$lib/store'
</script>

<!-- Il prefisso $ funziona ancora -->
<input bind:value={$ricerca} />
<p>{$maiuscola}</p>
```

```typescript
// toStore e fromStore: il ponte fra i due mondi
import { toStore, fromStore } from 'svelte/store'

// Da rune a store, per una libreria che si aspetta uno store
let conteggio = $state(0)
const storeConteggio = toStore(
  () => conteggio,
  (v) => (conteggio = v),
)

// Da store a rune
const daStore = fromStore(unoStoreEsistente)
console.log(daStore.current)
```

### Le trappole della migrazione

```svelte
<script lang="ts">
  // ❌ TRAPPOLA 1 — un $: con effetti convertito in $derived
  //    Svelte 4:
  //      $: { console.log(valore); salva(valore) }
  //    Convertito male:
  //      const x = $derived(...)   ← perde l'effetto
  //    Corretto:
  $effect(() => {
    console.log(valore)
    salva(valore)
  })

  // ❌ TRAPPOLA 2 — export let usato come stato interno
  //    In Svelte 4 una prop si poteva riassegnare dall'interno.
  //    In Svelte 5 serve $bindable, o uno stato locale derivato.

  // Svelte 4: export let valore = 0; valore++
  // Svelte 5:
  let { valoreIniziale = 0 } = $props()
  let valore = $state(valoreIniziale)

  // ❌ TRAPPOLA 3 — la reattività degli array
  //    In Svelte 4 serviva l'assegnazione:
  //      elenco = [...elenco, nuovo]
  //      elenco.push(nuovo); elenco = elenco   ← il trucco
  //    In Svelte 5 push funziona direttamente su $state
  let elenco = $state<string[]>([])
  elenco.push('nuovo') // reattivo
</script>
```

```
La strategia di migrazione:

  1. Aggiorna a Svelte 5: il codice esistente continua
     a funzionare
  2. Esegui 'sv migrate svelte-5' e RILEGGI il diff
  3. Cerca i $derived che dovrebbero essere $effect
  4. Converti gli store un modulo alla volta, quando
     lo tocchi per altri motivi
  5. Le librerie: verifica la compatibilità con Svelte 5
     prima di aggiornare
```

---

## D3. Accessibilità: cosa Svelte verifica da solo

Svelte è l'unico dei tre framework che segnala i problemi di accessibilità **in compilazione**, senza plugin.

```svelte
<!-- Ognuno di questi produce un avviso del compilatore -->

<!-- a11y_missing_attribute -->
<img src="/logo.svg" />
<!-- ⚠ <img> element should have an alt attribute -->

<!-- a11y_click_events_have_key_events -->
<div onclick={salva}>Salva</div>
<!-- ⚠ Visible, non-interactive elements with a click event
     must be accompanied by a keyboard event handler -->

<!-- a11y_no_noninteractive_element_interactions -->
<li onclick={seleziona}>Voce</li>

<!-- a11y_label_has_associated_control -->
<label>Nome</label>
<input />

<!-- a11y_autofocus -->
<input autofocus />
<!-- ⚠ Avoid using autofocus -->

<!-- a11y_media_has_caption -->
<video src="/video.mp4"></video>
<!-- ⚠ <video> elements must have a <track kind="captions"> -->

<!-- a11y_positive_tabindex -->
<div tabindex="3"></div>

<!-- a11y_role_has_required_aria_props -->
<div role="checkbox"></div>
<!-- ⚠ Elements with the ARIA role "checkbox" must have
     the following attributes defined: aria-checked -->

<!-- a11y_no_redundant_roles -->
<button role="button">…</button>
```

```javascript
// svelte.config.js — silenziare un avviso, con motivazione
export default {
  compilerOptions: {
    warningFilter: (avviso) => {
      // La libreria di terze parti genera questo markup:
      // non possiamo cambiarlo. Rivalutare all'aggiornamento.
      if (avviso.code === 'a11y_no_static_element_interactions') {
        return !avviso.filename?.includes('/vendor/')
      }
      return true
    },
  },
}
```

```svelte
<!-- Oppure per singola riga, con la motivazione -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<div onclick={chiudi}>
  <!-- Questo è lo sfondo della modale: il clic è un'aggiunta,
       la chiusura da tastiera è gestita con Esc altrove -->
</div>
```

### `$props.id()` e gli identificativi stabili

```svelte
<script lang="ts">
  // Svelte 5.20+: un identificativo univoco e stabile
  // fra server e client. Math.random() romperebbe
  // l'idratazione con il rendering sul server.
  const id = $props.id()

  let { etichetta, errore }: { etichetta: string; errore?: string } = $props()
  let valore = $state('')
</script>

<div class="campo">
  <label for={id}>{etichetta}</label>
  <input
    {id}
    bind:value={valore}
    aria-invalid={errore !== undefined}
    aria-describedby={errore ? `${id}-errore` : undefined}
  />
  {#if errore}
    <p id="{id}-errore" role="alert">{errore}</p>
  {/if}
</div>
```

### Il focus dopo la navigazione

```svelte
<!-- src/routes/+layout.svelte -->
<script lang="ts">
  import { afterNavigate } from '$app/navigation'
  import { page } from '$app/state'

  let annuncio = $state('')

  afterNavigate(() => {
    // SvelteKit sposta già il focus su <body> dopo una
    // navigazione, ma l'annuncio va aggiunto
    annuncio = `Pagina ${document.title}`
  })
</script>

<a href="#contenuto" class="salta-al-contenuto">Vai al contenuto principale</a>

<!-- La live region esiste sempre, anche vuota -->
<p role="status" aria-live="polite" class="solo-screen-reader">{annuncio}</p>

<header>
  <nav aria-label="Principale">
    <a href="/" aria-current={page.url.pathname === '/' ? 'page' : undefined}>Panoramica</a>
    <a href="/fatture" aria-current={page.url.pathname.startsWith('/fatture') ? 'page' : undefined}>
      Fatture
    </a>
  </nav>
</header>

<main id="contenuto">
  <slot />
</main>
```

SvelteKit gestisce il focus alla navigazione meglio di React Router e Vue Router: lo sposta su `<body>` e annuncia il titolo della pagina, comportandosi come una navigazione tradizionale. È un dettaglio che negli altri due va implementato a mano.

---

## D4. Testare i componenti Svelte

```powershell
pnpm add -D vitest @testing-library/svelte @testing-library/user-event @testing-library/jest-dom jsdom
```

```typescript
// vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite'
import { svelteTesting } from '@testing-library/svelte/vite'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [sveltekit(), svelteTesting()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./test/preparazione.ts'],
    globals: true,
  },
})
```

```typescript
// test/preparazione.ts
import '@testing-library/jest-dom/vitest'
```

### Testare i componenti

```typescript
import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import ModuloContatti from '$lib/componenti/ModuloContatti.svelte'

describe('ModuloContatti', () => {
  it('mostra un errore quando l email non è valida', async () => {
    const utente = userEvent.setup()
    render(ModuloContatti)

    await utente.type(screen.getByLabelText('Email'), 'non-valida')
    await utente.click(screen.getByRole('button', { name: 'Invia' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Indirizzo non valido')
  })

  it('chiama il callback con i dati corretti', async () => {
    const utente = userEvent.setup()
    const alInviare = vi.fn()

    // Le props si passano nella proprietà 'props'
    render(ModuloContatti, { props: { alInviare } })

    await utente.type(screen.getByLabelText('Nome'), 'Anna')
    await utente.type(screen.getByLabelText('Email'), 'anna@example.it')
    await utente.click(screen.getByRole('button', { name: 'Invia' }))

    expect(alInviare).toHaveBeenCalledWith({ nome: 'Anna', email: 'anna@example.it' })
  })
})
```

### Testare le rune fuori dai componenti

```typescript
// I file .svelte.test.ts possono usare le rune
// src/lib/stato/contatore.svelte.test.ts
import { describe, it, expect } from 'vitest'
import { flushSync } from 'svelte'
import { Contatore } from './Contatore.svelte'

describe('Contatore', () => {
  it('non supera il massimo', () => {
    const contatore = new Contatore({ iniziale: 9, massimo: 10 })

    contatore.incrementa()
    contatore.incrementa()

    // flushSync forza l'applicazione degli aggiornamenti,
    // che di norma sono accodati
    flushSync()

    expect(contatore.valore).toBe(10)
    expect(contatore.puoIncrementare).toBe(false)
  })
})
```

```typescript
// Testare un $effect richiede $effect.root, che crea
// un contesto di effetti fuori da un componente
import { flushSync } from 'svelte'

it('esegue l effetto quando la dipendenza cambia', () => {
  const chiamate: number[] = []

  const distruggi = $effect.root(() => {
    let valore = $state(0)

    $effect(() => {
      chiamate.push(valore)
    })

    flushSync()
    valore = 1
    flushSync()
    valore = 2
    flushSync()
  })

  expect(chiamate).toEqual([0, 1, 2])
  distruggi()
})
```

### Testare le form action di SvelteKit

```typescript
// Le action sono funzioni: si testano direttamente,
// senza montare nulla
import { describe, it, expect, vi } from 'vitest'
import { actions } from './+page.server'

describe('action di registrazione', () => {
  it('restituisce 422 con i dati non validi', async () => {
    const dati = new FormData()
    dati.set('nome', '')
    dati.set('email', 'non-valida')

    const esito = await actions.default({
      request: new Request('http://localhost', { method: 'POST', body: dati }),
      cookies: { set: vi.fn(), get: vi.fn(), delete: vi.fn() },
      getClientAddress: () => '127.0.0.1',
    } as never)

    expect(esito).toMatchObject({
      status: 422,
      data: {
        errori: {
          nome: ['Il nome è obbligatorio'],
          email: ['Indirizzo non valido'],
        },
      },
    })
  })

  it('non restituisce mai la password al client', async () => {
    const dati = new FormData()
    dati.set('password', 'segretissima')

    const esito = await actions.default({
      request: new Request('http://localhost', { method: 'POST', body: dati }),
      cookies: { set: vi.fn(), get: vi.fn(), delete: vi.fn() },
      getClientAddress: () => '127.0.0.1',
    } as never)

    expect(JSON.stringify(esito)).not.toContain('segretissima')
  })
})
```

### I test end-to-end con Playwright

```typescript
// e2e/registrazione.spec.ts
import { expect, test } from '@playwright/test'

test('il form funziona senza JavaScript', async ({ browser }) => {
  // Il controllo che distingue SvelteKit dagli altri
  const contesto = await browser.newContext({ javaScriptEnabled: false })
  const pagina = await contesto.newPage()

  await pagina.goto('/registrazione')

  await pagina.getByLabel('Nome').fill('Anna')
  await pagina.getByLabel('Email').fill('anna@example.it')
  await pagina.getByLabel('Password', { exact: true }).fill('unapasswordlunga')
  await pagina.getByLabel('Conferma la password').fill('unapasswordlunga')
  await pagina.getByLabel(/Accetto i termini/).check()

  await pagina.getByRole('button', { name: /Crea l account/ }).click()

  // Il reindirizzamento avviene senza JavaScript
  await expect(pagina).toHaveURL('/')

  await contesto.close()
})

test('mostra gli errori di validazione e conserva i valori', async ({ page }) => {
  await page.goto('/registrazione')

  await page.getByLabel('Nome').fill('Anna')
  await page.getByLabel('Email').fill('non-valida')
  await page.getByRole('button', { name: /Crea l account/ }).click()

  await expect(page.getByRole('alert')).toContainText('Indirizzo non valido')
  // Il nome digitato non si perde
  await expect(page.getByLabel('Nome')).toHaveValue('Anna')
})
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
SVELTE 5 — Mappa dei concetti

IL PRINCIPIO
└── Un COMPILATORE, non una libreria: il .svelte diventa
    JavaScript che tocca il DOM direttamente. Niente virtual
    DOM, niente confronto, runtime minimo che cresce solo
    con ciò che usi.

LE RUNE — simboli del compilatore, non funzioni
├── $state(valore)       Proxy PROFONDO: push e mutazioni funzionano
│   ├── $state.raw       nessun Proxy: solo la sostituzione
│   └── $state.snapshot  copia non reattiva, per l'esterno
├── $derived(espr)       PIGRO e in CACHE, dipendenze tracciate
│   ├── $derived.by(fn)  per la logica su più righe
│   └── sovrascrivibile  per lo stato ottimistico
├── $effect(fn)          DOPO il DOM; return = pulizia
│   ├── $effect.pre      prima dell'aggiornamento del DOM
│   └── $effect.root     un contesto di effetti nei test
├── $props()             con destructuring e valori predefiniti
│   └── $props.id()      identificativo stabile server/client
├── $bindable()          prop scrivibile dal figlio — con parsimonia
└── $inspect()           log dei cambiamenti, solo in sviluppo

QUANDO NON USARE $effect
├── derivare un valore   → $derived
├── sincronizzare stati  → una fonte sola
├── reagire a un evento  → il gestore
└── azzerare al cambio   → {#key ...}

IL MARKUP
├── {#if} {:else if} {:else}
├── {#each x as v (chiave)} {:else}   ← :else = elenco vuoto
├── {#await} {:then} {:catch}
├── {#key espr}          distrugge e ricrea
├── onclick (non on:click) — i modificatori si scrivono a mano
├── bind:valore · bind:group · bind:this · bind:clientWidth
├── class: · style: · use:azione · transition: in: out: animate:
└── Il CSS è LOCALE per costruzione; :global() per uscire
    └── il CSS non usato è un AVVISO di compilazione

COMPOSIZIONE
├── Snippet: {#snippet nome(par)} … {@render nome(arg)}
│     sostituiscono gli slot; sono VALORI, tipizzabili,
│     con parametri
├── children è lo snippet predefinito
├── setContext / getContext, all'inizializzazione
└── Azioni use: nodo + { update, destroy }
      il posto giusto per la manipolazione diretta del DOM

STATO CONDIVISO
├── File .svelte.ts: le rune funzionano fuori dai componenti
├── $state al livello del modulo = stato GLOBALE
├── Classi con campi $state e getter $derived
└── SvelteMap, SvelteSet, MediaQuery da svelte/reactivity

SVELTEKIT
├── Routing a file: +page.svelte, +layout, +server.ts
├── load in +page.ts       server E client
│   load in +page.server.ts SOLO server (segreti, database)
│   └── le promesse non attese FLUISCONO, con {#await}
├── form action            funzionano SENZA JavaScript
│   ├── fail() restituisce i dati al form
│   ├── redirect 303 dopo il POST
│   └── use:enhance aggiunge l'esperienza SPA
├── hooks.server.ts        autenticazione e autorizzazione
│                          centralizzate, per ogni richiesta
└── $lib/server/*          non importabile dal client,
                           verificato in compilazione

ACCESSIBILITÀ
└── Svelte segnala i problemi IN COMPILAZIONE, senza plugin:
    alt mancante, div cliccabili, label senza controllo,
    autofocus, video senza track, tabindex positivo,
    ruoli ARIA senza gli attributi richiesti

MIGRAZIONE DA SVELTE 4
├── sv migrate svelte-5 automatizza gran parte
├── ⚠ i $: con EFFETTI vanno riscritti in $effect a mano
├── Gli store continuano a funzionare: migrazione incrementale
└── toStore / fromStore fanno da ponte
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Sai spiegare cosa distingue un compilatore da una libreria a runtime
- [ ] Sai perché il bundle di Svelte cresce con il codice invece di partire alto
- [ ] Sai che le rune non sono funzioni e non si possono passare in giro
- [ ] Distingui `$state`, `$state.raw` e `$state.snapshot`
- [ ] Sai perché il destructuring di uno `$state` perde la reattività
- [ ] Usi `$derived` per i valori calcolati e sai che è pigro e in cache
- [ ] Conosci i blocchi del markup e sai che `{:else}` in un `each` è il caso vuoto
- [ ] Sai che in Svelte 5 gli eventi sono `onclick`, non `on:click`
- [ ] Tipizzi le props con `$props()` e il rest per gli attributi nativi
- [ ] Sai quando `$bindable` è giustificato e quando è meglio un callback

**Parte B — Comprensione**

- [ ] Sai cosa il compilatore considera statico e cosa dinamico
- [ ] Sai elencare i quattro casi in cui `$effect` non serve
- [ ] Sai che un effetto traccia solo le letture sincrone
- [ ] Usi `untrack` per escludere una lettura dal tracciamento
- [ ] Usi gli snippet con parametri e sai perché battono gli slot
- [ ] Sai creare uno stato condiviso in un file `.svelte.ts`
- [ ] Sai scrivere una classe con campi `$state` e getter `$derived`
- [ ] Sai perché servono `SvelteMap` e `SvelteSet`
- [ ] Scrivi un'azione con `update` e `destroy`
- [ ] Sai che le transizioni non rispettano `prefers-reduced-motion` da sole
- [ ] Distingui `+page.ts` da `+page.server.ts` e sai cosa può stare in ciascuno
- [ ] Sai come fluiscono le promesse non attese da `load`
- [ ] Sai scrivere una form action che funziona senza JavaScript
- [ ] Sai perché serve `redirect(303)` dopo un POST

**Parte C — Pratica**

- [ ] Hai convertito un componente da Svelte 4 a Svelte 5
- [ ] Hai scritto un'azione riusabile con il roving tabindex
- [ ] Hai costruito uno store condiviso con validazione e sincronizzazione fra schede
- [ ] Hai verificato che il form funzioni con JavaScript disattivato
- [ ] Hai confrontato lo stesso componente nei tre framework

**Parte D — Esperto**

- [ ] Sai spiegare il modello a segnali e il push-pull
- [ ] Sai perché una `$derived` non letta non viene mai calcolata
- [ ] Sai quando `$state.raw` vale la pena
- [ ] Conosci le tre trappole della migrazione da Svelte 4
- [ ] Sai quali problemi di accessibilità Svelte segnala in compilazione
- [ ] Usi `$props.id()` e sai perché conta con il rendering sul server
- [ ] Testi le rune con `flushSync` e `$effect.root`
- [ ] Testi una form action senza montare componenti
- [ ] Sai scrivere un test Playwright con JavaScript disattivato

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Destructuring di uno `$state` | Il valore si stacca: nessuna reattività | Passare l'oggetto, o esporre un getter |
| `$effect` per derivare un valore | Un aggiornamento in più, e stati disallineabili | `$derived` |
| `$effect` per reagire a un evento | La logica è lontana dal fatto | Il gestore dell'evento |
| `$effect` per azzerare al cambio di prop | Un aggiornamento con i dati vecchi | `{#key}` |
| `$state` su strutture enormi | Un Proxy per ogni nodo annidato | `$state.raw` |
| `$state.raw` modificato in profondità | Traccia solo la sostituzione | Sostituire per intero |
| `{#each}` senza chiave | Svelte riusa i nodi per posizione | `(elemento.id)` |
| `$bindable` ovunque | Rende opaco da dove viene un cambiamento | Prop in ingresso, callback in uscita |
| Ignorare gli avvisi di accessibilità | Sono corretti quasi sempre | Correggere, o `svelte-ignore` con motivazione |
| Transizioni senza `prefers-reduced-motion` | Nausea e vertigini reali | Durata zero quando la preferenza è attiva |
| Segreti in `+page.ts` | Gira anche sul client: finiscono nel bundle | `+page.server.ts`, o `$lib/server` |
| Validazione solo nel form | Chi disattiva JavaScript la salta | Sempre nell'action, sul server |
| `throw error()` dove serviva `fail()` | Reindirizza a una pagina d'errore e perde i valori | `fail(422, { errori, valori })` |
| Restituire la password in `fail()` | Finisce nell'HTML della risposta | Restituire solo i campi non sensibili |
| `Math.random()` per gli id | Rompe l'idratazione con il rendering sul server | `$props.id()` |
| `setContext` dentro un gestore | Va chiamato all'inizializzazione | Nel corpo di `<script>` |
| Azione senza `destroy` | Listener e osservatori che sopravvivono | Restituire `{ destroy }` |
| Test sui valori interni | Si rompono a ogni refactoring | Testare il comportamento osservabile |

---

## Troubleshooting rapido

**Il valore cambia ma il markup non si aggiorna**
- Causa: la variabile non è `$state`, oppure è stata destrutturata
- Fix: `$state`, e passare l'oggetto invece del valore estratto

**"`$state` is not defined" in un file `.ts`**
- Causa: le rune funzionano solo in `.svelte` e `.svelte.ts`
- Fix: rinominare il file in `*.svelte.ts`

**"Cannot assign to derived state"**
- Causa: si assegna a un `$derived` non sovrascrivibile in quel contesto
- Fix: se serve sovrascriverlo, dichiararlo con `let` e assegnare; altrimenti usare `$state`

**Un `$effect` si esegue in ciclo infinito**
- Causa: l'effetto scrive uno stato che legge
- Fix: `untrack` sulla lettura, oppure `$derived` se stava derivando

**Il `$derived` non si aggiorna**
- Causa: dipende da qualcosa che non è reattivo — una variabile normale, o un oggetto esterno
- Fix: verificare che tutte le fonti siano `$state` o props

**`{#each}` produce lo stato sull'elemento sbagliato**
- Causa: manca la chiave, o la chiave non è stabile
- Fix: `{#each elenco as v (v.id)}`

**"`localStorage` is not defined" in produzione**
- Causa: il codice gira durante il rendering sul server
- Fix: `import { browser } from '$app/environment'` e verificare prima

**Il segreto finisce nel bundle del client**
- Causa: importato in `+page.ts` o in un componente
- Fix: spostarlo in `+page.server.ts` o in `$lib/server/*`; verificare con una ricerca nel bundle

**Il form perde i valori dopo un errore**
- Causa: `use:enhance` con `update()` che azzera il form
- Fix: `update({ reset: false })` quando l'esito è un fallimento

**"Cannot use `$props()` outside a component"**
- Causa: chiamata in un file `.svelte.ts` o in una funzione
- Fix: `$props()` va nel corpo di `<script>` di un componente

**Le transizioni non partono**
- Causa: l'elemento non entra né esce dal DOM — un `class:` non basta
- Fix: `{#if}` o `{#each}` che aggiunge e rimuove il nodo

**`svelte-check` segnala errori che l'editor non mostra**
- Causa: versioni diverse dell'estensione e del pacchetto
- Fix: allineare `svelte` e `@sveltejs/kit`, riavviare il server della lingua

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_10_nodejs.md` | Il server sotto SvelteKit: adapter, Node, edge |
| `tutorial_11_api_design.md` | Gli endpoint `+server.ts` e le convenzioni REST |
| `tutorial_13_autenticazione_autorizzazione.md` | Sessioni, cookie e `hooks.server.ts` in profondità |
| `tutorial_15_testing_web.md` | Playwright e i test senza JavaScript |
| `tutorial_17_performance_web.md` | Core Web Vitals e il vantaggio reale di un bundle piccolo |
| `tutorial_18_pwa_tecnologie_avanzate.md` | Service worker con SvelteKit |

---

## Risorse di riferimento

**Documentazione:**
- [svelte.dev](https://svelte.dev/docs/svelte/overview) — la documentazione, riscritta per Svelte 5
- [Svelte — Runes](https://svelte.dev/docs/svelte/what-are-runes) — le rune spiegate dagli autori
- [SvelteKit](https://svelte.dev/docs/kit/introduction)
- [Svelte 5 Migration Guide](https://svelte.dev/docs/svelte/v5-migration-guide) — la tabella di conversione completa

**Approfondimenti:**
- [Svelte Tutorial](https://svelte.dev/tutorial) — interattivo, il modo più rapido per iniziare
- [Rich Harris — Rethinking Reactivity](https://www.youtube.com/watch?v=AdNJ3fydeao) — perché Svelte esiste
- [Svelte Society](https://sveltesociety.dev/) — componenti, template, ricette

**Strumenti:**
- [Svelte Playground](https://svelte.dev/playground) — con l'output del compilatore visibile
- [svelte-check](https://www.npmjs.com/package/svelte-check) — verifica dei tipi nei componenti
- [sv](https://www.npmjs.com/package/sv) — la CLI: creazione, migrazione, aggiunta di integrazioni
- [Testing Library — Svelte](https://testing-library.com/docs/svelte-testing-library/intro)

---

> **Fine del Tutorial 09 — Svelte 5**
>
> Prossimo tutorial: `tutorial_10_nodejs.md`
