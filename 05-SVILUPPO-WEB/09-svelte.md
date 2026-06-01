---
corso: "Sviluppo Web"
fase: "3 — Framework Frontend"
modulo: "09"
titolo: "Svelte e SvelteKit"
versione: "Svelte 5 / SvelteKit 2.x"
livello: "Intermedio"
prerequisiti:
  - "04 — JavaScript Fondamenti"
  - "06 — TypeScript"
obiettivi:
  - "Comprendere il modello di compilazione Svelte e runes"
  - "Costruire applicazioni full-stack con SvelteKit"
  - "Gestire stato reattivo senza virtual DOM"
  - "Implementare SSR, SSG e form actions con SvelteKit"
  - "Creare componenti con slot, binding e transizioni"
  - "Testare applicazioni Svelte con Vitest e Playwright"
tag: [Svelte, SvelteKit, runes, compilazione, SSR, reattivita, Vitest]
---

# Svelte e SvelteKit — Guida Completa

> **Modulo 09** · **Aggiornamento:** 2026-05-24 · **Versione:** Svelte 5

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [JavaScript Fondamenti](04-javascript-fondamenti.md), [TypeScript](06-typescript.md)
>
> Al termine di questo modulo saprai:
> 1. Comprendere il modello di compilazione Svelte e runes (`$state`, `$derived`, `$effect`)
> 2. Costruire applicazioni full-stack con SvelteKit
> 3. Gestire stato reattivo senza virtual DOM
> 4. Implementare SSR, SSG e form actions con SvelteKit
> 5. Creare componenti con slot, binding e transizioni
> 6. Testare applicazioni Svelte con Vitest e Playwright
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio

## Idee guida
1. **Svelte 5 introduces runes (`$state`, `$derived`, `$effect`).**
2. **No virtual DOM: compiled to imperative code.** Smaller bundles.
3. **SvelteKit fullstack.** Adapter Vercel/Netlify/Node.
4. **Best for small/medium apps; ecosystem piu piccolo di React.**


## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti di Svelte](#fondamenti-di-svelte)
3. [Svelte 5 — Runes](#svelte-5--runes)
4. [Store](#store)
5. [SvelteKit](#sveltekit)
6. [Ecosystem](#ecosystem)
7. [Confronto con React e Vue](#confronto-con-react-e-vue)
8. [Best Practices](#best-practices)
9. [Il Compilatore Svelte — Architettura Interna](#il-compilatore-svelte--architettura-interna)
10. [Pattern di Composizione dei Componenti](#pattern-di-composizione-dei-componenti)
11. [Migrazione Store verso Runes](#migrazione-store-verso-runes)
12. [SSR, Idratazione e Streaming](#ssr-idratazione-e-streaming)
13. [Accessibilità in Svelte](#accessibilità-in-svelte)
14. [Pattern di Gestione dello Stato](#pattern-di-gestione-dello-stato)
15. [Svelte con TypeScript — Approfondimento](#svelte-con-typescript--approfondimento)
16. [Strategie di Deploy](#strategie-di-deploy)
17. [Ottimizzazione delle Prestazioni](#ottimizzazione-delle-prestazioni)

---

## Panoramica

### Che cos'è Svelte

Svelte è un framework per la costruzione di interfacce utente che adotta un approccio radicalmente diverso rispetto ai framework tradizionali come React e Vue. La differenza fondamentale risiede nel **momento in cui avviene il lavoro**: mentre React e Vue eseguono la maggior parte della loro logica nel browser a runtime, Svelte sposta questo lavoro nella **fase di compilazione**. Il risultato è codice JavaScript vanilla altamente ottimizzato che manipola direttamente il DOM, senza la necessità di un virtual DOM o di un runtime pesante.

Svelte è stato creato da Rich Harris nel 2016 e ha guadagnato enorme popolarità grazie alla sua semplicità, alle prestazioni eccellenti e all'esperienza di sviluppo superiore. Con il rilascio di SvelteKit, il framework offre una soluzione full-stack completa per applicazioni web moderne.

### La filosofia compile-time

Il cuore della filosofia di Svelte è il concetto di **compiler-as-framework**. Quando si scrive un componente Svelte, il codice viene compilato in istruzioni imperative che aggiornano il DOM in modo chirurgico. Questo approccio elimina diversi problemi:

- **Nessun virtual DOM**: non è necessario calcolare differenze tra alberi virtuali. Svelte sa esattamente quali nodi del DOM devono cambiare quando lo stato si aggiorna, perché questa informazione viene determinata in fase di compilazione.
- **Bundle più leggeri**: poiché non c'è un runtime da includere, le applicazioni Svelte tendono ad avere dimensioni significativamente inferiori rispetto a quelle equivalenti in React o Vue.
- **Prestazioni superiori**: le operazioni di aggiornamento del DOM sono dirette e mirate, senza overhead di riconciliazione.
- **Meno boilerplate**: la sintassi di Svelte è progettata per essere concisa e leggibile, riducendo la quantità di codice necessario.

### Installazione e primo progetto

Per creare un nuovo progetto SvelteKit:

```bash
npx sv create nome-progetto
cd nome-progetto
npm install
npm run dev
```

Il comando `sv create` offre diversi template e opzioni di configurazione, tra cui TypeScript, ESLint, Prettier, Playwright e Vitest.

---

## Fondamenti di Svelte

### Componenti

In Svelte, ogni componente è un file `.svelte` che contiene tre sezioni opzionali: script, stile e markup. La struttura è intuitiva e rispecchia la naturale separazione delle responsabilità nel web development.

```svelte
<script>
  let nome = 'Mondo';
</script>

<h1>Ciao {nome}!</h1>

<style>
  h1 {
    color: #ff3e00;
    font-family: 'Comic Sans MS', cursive;
  }
</style>
```

Una caratteristica fondamentale è che gli **stili sono automaticamente scoped** al componente. Il CSS definito in un file `.svelte` non influenzerà mai altri componenti, eliminando i problemi di collisione dei nomi tipici dello sviluppo CSS tradizionale. Svelte aggiunge automaticamente classi univoche ai selettori per garantire l'isolamento.

### Reattività con `$:`

Svelte (nelle versioni precedenti alla 5) utilizza un sistema di reattività basato sulle assegnazioni. Quando si assegna un nuovo valore a una variabile dichiarata nel blocco `<script>`, Svelte aggiorna automaticamente il DOM. Per le espressioni derivate, si utilizza il costrutto **reactive statement** `$:`:

```svelte
<script>
  let conteggio = 0;
  $: doppio = conteggio * 2;
  $: quadruplo = doppio * 2;

  $: if (conteggio >= 10) {
    alert('Il conteggio è alto!');
    conteggio = 9;
  }

  $: {
    console.log('Il conteggio è cambiato:', conteggio);
    console.log('Il doppio è:', doppio);
  }

  function incrementa() {
    conteggio += 1;
  }
</script>

<button on:click={incrementa}>
  Conteggio: {conteggio} (doppio: {doppio}, quadruplo: {quadruplo})
</button>
```

Il prefisso `$:` indica al compilatore che l'istruzione o il blocco deve essere rieseguito ogni volta che le variabili da cui dipende cambiano. È possibile usare `$:` per dichiarazioni reattive, blocchi condizionali e blocchi di codice generici.

### Props con `export let`

Le proprietà (props) permettono di passare dati da un componente padre a un componente figlio. In Svelte, si dichiara una prop utilizzando `export let`:

```svelte
<!-- Saluto.svelte -->
<script>
  export let nome;
  export let saluto = 'Ciao'; // valore predefinito
</script>

<p>{saluto}, {nome}!</p>
```

```svelte
<!-- App.svelte -->
<script>
  import Saluto from './Saluto.svelte';
</script>

<Saluto nome="Marco" />
<Saluto nome="Lucia" saluto="Buongiorno" />
```

Se una prop non ha un valore predefinito e non viene passata dal padre, Svelte emetterà un warning in modalità sviluppo. È anche possibile usare lo spread operator per passare tutte le proprietà di un oggetto:

```svelte
<script>
  import Profilo from './Profilo.svelte';
  const dati = { nome: 'Marco', eta: 30, citta: 'Milano' };
</script>

<Profilo {...dati} />
```

### Eventi e dispatch

Svelte supporta tutti gli eventi DOM nativi tramite la direttiva `on:`. Per gli eventi personalizzati tra componenti, si utilizza `createEventDispatcher`:

```svelte
<!-- Pulsante.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function gestisciClick() {
    dispatch('messaggio', {
      testo: 'Ciao dal componente figlio!'
    });
  }
</script>

<button on:click={gestisciClick}>
  Invia messaggio
</button>
```

```svelte
<!-- App.svelte -->
<script>
  import Pulsante from './Pulsante.svelte';

  function gestisciMessaggio(evento) {
    console.log(evento.detail.testo);
  }
</script>

<Pulsante on:messaggio={gestisciMessaggio} />
```

I modificatori di eventi sono molto utili per gestire comportamenti comuni in modo dichiarativo:

```svelte
<button on:click|once|preventDefault={gestisci}>
  Clicca una volta sola
</button>

<form on:submit|preventDefault={inviaForm}>
  <!-- contenuto del form -->
</form>
```

I modificatori disponibili includono `preventDefault`, `stopPropagation`, `passive`, `nonpassive`, `capture`, `once` e `self`. È possibile concatenarli con il carattere `|`.

### Slot

Gli slot permettono di comporre componenti inserendo contenuto dall'esterno, analogamente ai children di React o agli slot di Vue:

```svelte
<!-- Scheda.svelte -->
<script>
  export let titolo;
</script>

<div class="scheda">
  <header>
    <slot name="intestazione">
      <h2>{titolo}</h2>
    </slot>
  </header>
  <div class="contenuto">
    <slot>
      <p>Contenuto predefinito</p>
    </slot>
  </div>
  <footer>
    <slot name="piede" />
  </footer>
</div>
```

```svelte
<!-- Utilizzo -->
<Scheda titolo="La mia scheda">
  <span slot="intestazione">
    <h2>Intestazione personalizzata</h2>
  </span>

  <p>Questo va nello slot predefinito.</p>
  <p>Anche questo contenuto va nello slot predefinito.</p>

  <div slot="piede">
    <button>Azione</button>
  </div>
</Scheda>
```

Lo slot predefinito (senza nome) accoglie tutto il contenuto che non è assegnato a uno slot con nome. Il contenuto fallback definito dentro il tag `<slot>` viene mostrato solo quando il padre non fornisce contenuto per quello slot.

### Binding

I binding bidirezionali sono una delle funzionalità più comode di Svelte. Permettono di sincronizzare automaticamente il valore di un elemento del DOM con una variabile:

```svelte
<script>
  let nome = '';
  let accettato = false;
  let colorePreferito = '#ff3e00';
  let volume = 50;
  let linguaggio = 'svelte';
  let gusti = [];
</script>

<!-- Input testuale -->
<input bind:value={nome} placeholder="Il tuo nome" />
<p>Ciao, {nome || 'sconosciuto'}!</p>

<!-- Checkbox -->
<label>
  <input type="checkbox" bind:checked={accettato} />
  Accetto i termini
</label>

<!-- Range -->
<input type="range" bind:value={volume} min="0" max="100" />
<p>Volume: {volume}%</p>

<!-- Select -->
<select bind:value={linguaggio}>
  <option value="svelte">Svelte</option>
  <option value="react">React</option>
  <option value="vue">Vue</option>
</select>

<!-- Checkbox multipli (bind:group) -->
<label><input type="checkbox" bind:group={gusti} value="vaniglia" /> Vaniglia</label>
<label><input type="checkbox" bind:group={gusti} value="cioccolato" /> Cioccolato</label>
<label><input type="checkbox" bind:group={gusti} value="fragola" /> Fragola</label>
<p>Gusti scelti: {gusti.join(', ')}</p>
```

Oltre agli input, è possibile usare bind su proprietà di elementi HTML come `clientWidth`, `clientHeight`, `offsetWidth`, `offsetHeight`, e persino `this` per ottenere un riferimento all'elemento DOM. Il binding `bind:this` è particolarmente utile per l'integrazione con librerie JavaScript di terze parti.

### Blocchi di controllo nel template

Svelte offre blocchi di controllo integrati nel template per la logica condizionale e le iterazioni:

```svelte
<script>
  let elementi = ['Mela', 'Banana', 'Ciliegia'];
  let mostraLista = true;
  let promessa = fetch('/api/dati').then(r => r.json());
</script>

<!-- Condizionali -->
{#if mostraLista}
  <ul>
    {#each elementi as elemento, indice (elemento)}
      <li>{indice + 1}. {elemento}</li>
    {/each}
  </ul>
{:else}
  <p>La lista è nascosta.</p>
{/if}

<!-- Await per le promise -->
{#await promessa}
  <p>Caricamento in corso...</p>
{:then dati}
  <p>Dati ricevuti: {JSON.stringify(dati)}</p>
{:catch errore}
  <p class="errore">Errore: {errore.message}</p>
{/await}
```

La chiave `(elemento)` nel blocco `{#each}` è fondamentale per le prestazioni: permette a Svelte di identificare univocamente ogni elemento della lista e di aggiornare il DOM in modo efficiente quando l'array cambia.

### Transizioni e animazioni

Svelte include un sistema di transizioni e animazioni potente e dichiarativo, pronto all'uso senza librerie esterne:

```svelte
<script>
  import { fade, fly, slide, scale, blur, crossfade } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import { quintOut, elasticOut } from 'svelte/easing';

  let visibile = true;
  let elementi = [1, 2, 3, 4, 5];
</script>

<!-- Transizione base -->
<button on:click={() => visibile = !visibile}>
  Mostra/Nascondi
</button>

{#if visibile}
  <p transition:fade>Appare e scompare con fade</p>

  <p in:fly={{ y: 200, duration: 500 }}
     out:fade={{ duration: 300 }}>
    Entra volando, esce con fade
  </p>

  <div transition:scale={{ delay: 100, duration: 400, easing: elasticOut }}>
    Scala con easing elastico
  </div>
{/if}

<!-- Animazione di lista con flip -->
{#each elementi as elemento (elemento)}
  <div animate:flip={{ duration: 300 }}>
    {elemento}
  </div>
{/each}
```

È possibile creare transizioni personalizzate definendo una funzione che restituisce un oggetto con proprietà CSS:

```svelte
<script>
  function transizionePersonalizzata(nodo, { duration = 400, delay = 0 }) {
    return {
      delay,
      duration,
      css: (t) => `
        transform: rotate(${t * 360}deg) scale(${t});
        opacity: ${t};
      `
    };
  }
</script>

{#if visibile}
  <div transition:transizionePersonalizzata={{ duration: 600 }}>
    Transizione personalizzata con rotazione
  </div>
{/if}
```

Il parametro `t` varia da 0 a 1 durante l'ingresso (in) e da 1 a 0 durante l'uscita (out). Svelte gestisce automaticamente l'interpolazione dei valori CSS.

### Crossfade e transizioni di lista

Il modulo `svelte/transition` include `crossfade`, una transizione coordinata che fa apparire un elemento in una posizione mentre lo fa scomparire da un'altra, creando l'illusione di un movimento fluido. È ideale per liste drag-and-drop, trasferimenti tra colonne e interfacce kanban:

```svelte
<script>
  import { crossfade } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';

  const [invia, ricevi] = crossfade({
    duration: 400,
    easing: quintOut,
    fallback(nodo) {
      // Fallback quando l'elemento non ha un corrispondente
      return {
        duration: 300,
        css: (t) => `opacity: ${t}; transform: scale(${t})`
      };
    }
  });

  let todoList = $state([
    { id: 1, testo: 'Comprare il latte', completato: false },
    { id: 2, testo: 'Scrivere documentazione', completato: false },
    { id: 3, testo: 'Fare esercizio', completato: true }
  ]);

  let attivi = $derived(todoList.filter(t => !t.completato));
  let completati = $derived(todoList.filter(t => t.completato));

  function toggle(id) {
    const item = todoList.find(t => t.id === id);
    if (item) item.completato = !item.completato;
  }
</script>

<div class="colonne">
  <div class="colonna">
    <h3>Da fare</h3>
    {#each attivi as todo (todo.id)}
      <div
        in:ricevi={{ key: todo.id }}
        out:invia={{ key: todo.id }}
        onclick={() => toggle(todo.id)}
      >
        {todo.testo}
      </div>
    {/each}
  </div>

  <div class="colonna">
    <h3>Completati</h3>
    {#each completati as todo (todo.id)}
      <div
        in:ricevi={{ key: todo.id }}
        out:invia={{ key: todo.id }}
        onclick={() => toggle(todo.id)}
      >
        {todo.testo}
      </div>
    {/each}
  </div>
</div>
```

La funzione `crossfade` restituisce una coppia `[invia, ricevi]` di transizioni coordinate tramite una chiave (`key`). Quando un elemento con una certa chiave esce da una lista e un elemento con la stessa chiave entra in un'altra, Svelte anima il passaggio come un movimento continuo.

### Transizioni con tick e JavaScript puro

Per animazioni che non possono essere espresse in CSS (ad esempio, animazione del contenuto testuale o manipolazione canvas), Svelte supporta transizioni basate su `tick` al posto di `css`:

```svelte
<script>
  function typewriter(nodo, { velocita = 30 }) {
    const testo = nodo.textContent;
    const durata = testo.length * velocita;

    return {
      duration: durata,
      tick(t) {
        // t va da 0 a 1 — mostriamo progressivamente i caratteri
        const i = Math.trunc(testo.length * t);
        nodo.textContent = testo.slice(0, i);
      }
    };
  }
</script>

{#if mostraTesto}
  <p transition:typewriter={{ velocita: 50 }}>
    Questo testo appare lettera per lettera, come una macchina da scrivere.
  </p>
{/if}
```

La differenza tra `css` e `tick` è significativa per le prestazioni. Le transizioni `css` vengono gestite dal browser sul thread di compositing (GPU-accelerate), mentre le transizioni `tick` eseguono JavaScript su ogni frame. Usare `tick` solo quando CSS non è sufficiente. Per animazioni complesse a 60fps su proprietà non-CSS, considerare `requestAnimationFrame` o librerie come GSAP con l'adapter Svelte.

### Deferred transitions e `{#key}`

Il blocco `{#key}` forza la distruzione e ricreazione di un componente o elemento quando l'espressione cambia, attivando le transizioni di ingresso e uscita:

```svelte
<script>
  import { fade, fly } from 'svelte/transition';
  let paginaCorrente = $state(0);
  let pagine = ['Introduzione', 'Contenuto', 'Conclusione'];
</script>

<button onclick={() => paginaCorrente = (paginaCorrente + 1) % pagine.length}>
  Prossima pagina
</button>

{#key paginaCorrente}
  <div
    in:fly={{ x: 200, duration: 300 }}
    out:fly={{ x: -200, duration: 300 }}
  >
    <h2>{pagine[paginaCorrente]}</h2>
  </div>
{/key}
```

Senza `{#key}`, Svelte riutilizzerebbe lo stesso elemento DOM aggiornandone il contenuto, senza attivare transizioni. `{#key}` garantisce che l'intero blocco venga rimosso e ricreato, forzando le animazioni `in:` e `out:`.

### Lifecycle

Svelte offre funzioni di lifecycle per eseguire codice in momenti specifici della vita del componente:

```svelte
<script>
  import { onMount, onDestroy, beforeUpdate, afterUpdate, tick } from 'svelte';

  let dati = [];

  onMount(async () => {
    // Eseguito dopo il primo rendering nel DOM
    const risposta = await fetch('/api/dati');
    dati = await risposta.json();

    // Restituire una funzione di cleanup (opzionale)
    return () => {
      console.log('Componente rimosso dal DOM');
    };
  });

  beforeUpdate(() => {
    // Eseguito prima di ogni aggiornamento del DOM
    console.log('Il DOM sta per aggiornarsi');
  });

  afterUpdate(() => {
    // Eseguito dopo ogni aggiornamento del DOM
    console.log('Il DOM è stato aggiornato');
  });

  onDestroy(() => {
    // Pulizia: rimuovere listener, timer, ecc.
    console.log('Componente distrutto');
  });
</script>
```

La funzione `tick()` è particolarmente utile: restituisce una promise che si risolve dopo che Svelte ha applicato tutti gli aggiornamenti pendenti al DOM, permettendo di leggere lo stato aggiornato.

---

## Svelte 5 — Runes

Svelte 5 introduce le **rune** (runes), un nuovo sistema di reattività che sostituisce i meccanismi precedenti (`$:`, `export let`, `createEventDispatcher`) con un approccio più esplicito, componibile e potente. Le rune sono identificate dal prefisso `$` e rappresentano la più grande evoluzione del framework dalla sua creazione.

### `$state`

La rune `$state` dichiara uno stato reattivo. A differenza del semplice `let` delle versioni precedenti, `$state` crea un vero proxy reattivo che traccia le mutazioni in profondità:

```svelte
<script>
  let conteggio = $state(0);
  let utente = $state({ nome: 'Marco', eta: 30 });
  let lista = $state(['mela', 'banana']);

  function incrementa() {
    conteggio++;
  }

  function aggiornaUtente() {
    // La mutazione diretta è ora reattiva grazie al proxy
    utente.eta += 1;
  }

  function aggiungiElemento() {
    // Anche i metodi mutanti degli array sono tracciati
    lista.push('ciliegia');
  }
</script>

<button onclick={incrementa}>Conteggio: {conteggio}</button>
<p>{utente.nome} ha {utente.eta} anni</p>
<ul>
  {#each lista as frutto}
    <li>{frutto}</li>
  {/each}
</ul>
```

Un aspetto importante è `$state.raw()`, che crea stato reattivo senza proxy profondo. È utile per grandi strutture dati immutabili dove non si vuole l'overhead del tracking delle mutazioni:

```svelte
<script>
  // Solo la riassegnazione attiverà aggiornamenti, non le mutazioni
  let datiPesanti = $state.raw(grandissimoArray);
</script>
```

### `$derived`

La rune `$derived` sostituisce le dichiarazioni reattive `$:` per i valori calcolati. Il valore viene ricalcolato automaticamente quando le dipendenze cambiano:

```svelte
<script>
  let larghezza = $state(10);
  let altezza = $state(20);

  // Valore derivato semplice
  let area = $derived(larghezza * altezza);
  let perimetro = $derived(2 * (larghezza + altezza));

  // Per logiche più complesse, usare $derived.by()
  let descrizione = $derived.by(() => {
    if (area > 200) return 'Grande';
    if (area > 100) return 'Medio';
    return 'Piccolo';
  });

  let elementiFiltrati = $derived.by(() => {
    const risultato = lista.filter(e => e.attivo);
    return risultato.sort((a, b) => a.nome.localeCompare(b.nome));
  });
</script>

<p>Rettangolo {larghezza}x{altezza}: area={area}, perimetro={perimetro}</p>
<p>Dimensione: {descrizione}</p>
```

La differenza tra `$derived(espressione)` e `$derived.by(funzione)` è che il primo accetta un'espressione singola, mentre il secondo accetta una funzione con logica complessa, blocchi condizionali, cicli e variabili locali.

### `$effect`

La rune `$effect` gestisce gli effetti collaterali reattivi, sostituendo i blocchi `$:` usati per side effects:

```svelte
<script>
  let query = $state('');
  let risultati = $state([]);

  // Effetto che si ri-esegue quando le dipendenze cambiano
  $effect(() => {
    if (query.length < 3) {
      risultati = [];
      return;
    }

    const controller = new AbortController();

    fetch(`/api/ricerca?q=${query}`, { signal: controller.signal })
      .then(r => r.json())
      .then(dati => { risultati = dati; })
      .catch(() => {});

    // Funzione di cleanup: eseguita prima della prossima esecuzione
    // dell'effetto e alla distruzione del componente
    return () => {
      controller.abort();
    };
  });

  // $effect.pre() si esegue PRIMA dell'aggiornamento del DOM
  $effect.pre(() => {
    console.log('DOM sta per aggiornarsi con:', query);
  });
</script>

<input bind:value={query} placeholder="Cerca..." />
{#each risultati as risultato}
  <p>{risultato.titolo}</p>
{/each}
```

Il tracking delle dipendenze è automatico: Svelte rileva quali valori `$state` e `$derived` vengono letti all'interno dell'effetto e riesegue la funzione quando cambiano. La funzione di cleanup restituita è essenziale per evitare memory leak e race condition.

### `$props`

La rune `$props` sostituisce `export let` per la dichiarazione delle proprietà del componente, con una sintassi basata sul destructuring:

```svelte
<!-- ComponenteFiglio.svelte -->
<script>
  // Dichiarazione delle props con valori predefiniti
  let { nome, saluto = 'Ciao', eta, ...resto } = $props();
</script>

<p>{saluto}, {nome}! Hai {eta} anni.</p>
<div>{JSON.stringify(resto)}</div>
```

```svelte
<!-- ComponentePadre.svelte -->
<script>
  import ComponenteFiglio from './ComponenteFiglio.svelte';
</script>

<ComponenteFiglio nome="Marco" eta={30} classe="extra" />
```

Per i callback (che sostituiscono gli eventi custom con `dispatch`), si passano semplicemente come props funzione:

```svelte
<!-- Pulsante.svelte (Svelte 5) -->
<script>
  let { onclick, testo = 'Clicca' } = $props();
</script>

<button {onclick}>{testo}</button>
```

```svelte
<!-- Utilizzo -->
<Pulsante onclick={() => console.log('Cliccato!')} testo="Premi qui" />
```

Questo approccio è più semplice e componibile rispetto al pattern `createEventDispatcher` delle versioni precedenti: le funzioni callback possono essere passate attraverso più livelli di componenti senza bisogno di event forwarding.

### `$bindable`

Quando una prop deve supportare il binding bidirezionale dal componente padre, si usa `$bindable`:

```svelte
<!-- CampoTesto.svelte -->
<script>
  let { value = $bindable(''), placeholder = '' } = $props();
</script>

<input bind:value {placeholder} />
```

```svelte
<!-- Utilizzo -->
<script>
  let testo = $state('');
</script>

<CampoTesto bind:value={testo} placeholder="Scrivi qui..." />
<p>Hai scritto: {testo}</p>
```

### `$inspect`

La rune `$inspect` è uno strumento di debug che stampa i valori reattivi nella console ogni volta che cambiano. Viene rimossa automaticamente nelle build di produzione, quindi può essere usata liberamente durante lo sviluppo senza preoccuparsi delle prestazioni:

```svelte
<script>
  let conteggio = $state(0);
  let utente = $state({ nome: 'Marco', ruolo: 'admin' });

  // Stampa ogni volta che conteggio o utente cambiano
  $inspect(conteggio);
  $inspect(utente);

  // Con callback personalizzata tramite .with()
  $inspect(conteggio).with((tipo, valore) => {
    if (tipo === 'update') {
      console.log('Conteggio aggiornato a:', valore);
    }
  });

  // Utile per debugger condizionale
  $inspect(conteggio).with((tipo, valore) => {
    if (valore > 10) debugger;
  });
</script>
```

Il parametro `tipo` nella callback può essere `'init'` (prima lettura) o `'update'` (aggiornamento successivo). `$inspect` accetta più argomenti: `$inspect(a, b, c)` monitora tutti e tre i valori. A differenza di `console.log`, `$inspect` stampa il valore aggiornato, non quello catturato al momento della chiamata, perché è reattivo.

### `$host`

La rune `$host` è disponibile esclusivamente all'interno di componenti compilati come custom element (Web Component). Restituisce un riferimento all'elemento host, permettendo di interagire con l'API dei custom element:

```svelte
<svelte:options customElement="mio-elemento" />

<script>
  let host = $host();

  $effect(() => {
    // Dispatch di un evento custom dal Web Component
    host.dispatchEvent(new CustomEvent('cambiamento', {
      detail: { valore: 42 },
      bubbles: true
    }));
  });

  // Accesso diretto all'elemento host per stili o attributi
  $effect(() => {
    host.style.setProperty('--colore-primario', '#ff3e00');
  });
</script>
```

### Riepilogo delle rune

| Rune | Scopo | Sostituisce |
|---|---|---|
| `$state(valore)` | Stato reattivo con proxy profondo | `let variabile` |
| `$state.raw(valore)` | Stato reattivo senza proxy | `let variabile` (dati immutabili) |
| `$derived(expr)` | Valore calcolato da dipendenze | `$: valore = expr` |
| `$derived.by(fn)` | Valore calcolato con logica complessa | `$: { ... }` con assegnazione |
| `$effect(fn)` | Effetto collaterale reattivo | `$: { sideEffect() }` |
| `$effect.pre(fn)` | Effetto prima dell'aggiornamento DOM | `beforeUpdate()` |
| `$props()` | Dichiarazione props componente | `export let prop` |
| `$bindable(default)` | Prop con binding bidirezionale | `export let prop` + `bind:` |
| `$inspect(val)` | Debug reattivo (solo dev) | `$: console.log(val)` |
| `$host()` | Riferimento host custom element | Nessun equivalente |

---

## Store

Gli store di Svelte forniscono un meccanismo per gestire stato condiviso tra componenti che non hanno una relazione diretta padre-figlio. Sono oggetti reattivi che seguono un contratto semplice basato su subscribe/unsubscribe.

### `writable`

Lo store scrivibile è il tipo più comune. Permette sia la lettura che la scrittura del valore:

```javascript
// stores.js
import { writable } from 'svelte/store';

// Crea uno store con valore iniziale
export const contatore = writable(0);

// Store con logica di inizializzazione e cleanup
export const posizioneMouse = writable({ x: 0, y: 0 }, (set) => {
  function gestisciMovimento(evento) {
    set({ x: evento.clientX, y: evento.clientY });
  }

  window.addEventListener('mousemove', gestisciMovimento);

  // Funzione di cleanup quando non ci sono più subscriber
  return () => {
    window.removeEventListener('mousemove', gestisciMovimento);
  };
});
```

```svelte
<script>
  import { contatore } from './stores.js';

  // Con il prefisso $, lo store si auto-sottoscrive e si cancella
  // automaticamente alla distruzione del componente
  function incrementa() {
    contatore.update(n => n + 1);
    // oppure: $contatore += 1;
  }

  function resetta() {
    contatore.set(0);
  }
</script>

<p>Contatore: {$contatore}</p>
<button on:click={incrementa}>+1</button>
<button on:click={resetta}>Reset</button>
```

Il prefisso `$` è una feature sintattica esclusiva dei file `.svelte`: gestisce automaticamente la sottoscrizione e la cancellazione, evitando memory leak.

### `readable`

Lo store di sola lettura non può essere modificato dall'esterno. Il valore viene impostato esclusivamente dalla funzione di inizializzazione:

```javascript
// stores.js
import { readable } from 'svelte/store';

export const oraCorrente = readable(new Date(), (set) => {
  const intervallo = setInterval(() => {
    set(new Date());
  }, 1000);

  return () => clearInterval(intervallo);
});

export const larghezzaFinestra = readable(0, (set) => {
  function aggiorna() {
    set(window.innerWidth);
  }
  aggiorna();
  window.addEventListener('resize', aggiorna);
  return () => window.removeEventListener('resize', aggiorna);
});
```

```svelte
<script>
  import { oraCorrente, larghezzaFinestra } from './stores.js';
</script>

<p>Ora: {$oraCorrente.toLocaleTimeString('it-IT')}</p>
<p>Larghezza finestra: {$larghezzaFinestra}px</p>
```

### `derived`

Lo store derivato calcola il suo valore a partire da uno o più store sorgente:

```javascript
// stores.js
import { writable, derived } from 'svelte/store';

export const nome = writable('Marco');
export const cognome = writable('Rossi');

// Derivato da due store
export const nomeCompleto = derived(
  [nome, cognome],
  ([$nome, $cognome]) => `${$nome} ${$cognome}`
);

// Derivato asincrono
export const risultatiRicerca = derived(
  queryRicerca,
  ($query, set) => {
    if ($query.length < 3) {
      set([]);
      return;
    }

    const timeout = setTimeout(async () => {
      const risposta = await fetch(`/api/ricerca?q=${$query}`);
      const dati = await risposta.json();
      set(dati);
    }, 300);

    return () => clearTimeout(timeout);
  },
  [] // valore iniziale
);
```

Gli store derivati sono particolarmente utili per creare pipeline di dati reattive dove più fonti contribuiscono a un risultato calcolato. Lo store derivato si aggiorna automaticamente ogni volta che una delle sue sorgenti cambia.

---

## SvelteKit

SvelteKit è il framework full-stack ufficiale per Svelte. Offre routing basato sul file system, rendering lato server, generazione di siti statici e molto altro. È l'equivalente di Next.js per React o Nuxt per Vue.

### Routing basato sul file system

SvelteKit utilizza il file system per definire le route dell'applicazione. La directory `src/routes` è la radice:

```
src/routes/
├── +page.svelte            → /
├── +layout.svelte          → Layout globale
├── chi-siamo/
│   └── +page.svelte        → /chi-siamo
├── blog/
│   ├── +page.svelte        → /blog
│   ├── +page.server.js     → Dati per /blog
│   └── [slug]/
│       ├── +page.svelte    → /blog/:slug
│       └── +page.server.js → Dati per /blog/:slug
├── api/
│   └── utenti/
│       └── +server.js      → /api/utenti (endpoint API)
└── (marketing)/
    ├── +layout.svelte      → Layout condiviso per il gruppo
    ├── prezzi/
    │   └── +page.svelte    → /prezzi
    └── funzionalita/
        └── +page.svelte    → /funzionalita
```

I parametri dinamici si definiscono con le parentesi quadre `[parametro]`. I gruppi di layout con le parentesi tonde `(nomeGruppo)` permettono di condividere un layout tra route senza influenzare l'URL. I parametri rest `[...percorso]` catturano segmenti multipli e sono utili per pagine 404 personalizzate o route catch-all.

### Load function

Le load function sono il cuore del data fetching in SvelteKit. Vengono eseguite prima del rendering della pagina, sia lato server che lato client:

```javascript
// src/routes/blog/+page.server.js
// Questa load function viene eseguita SOLO sul server
export async function load({ fetch, params, url, cookies, locals }) {
  const pagina = url.searchParams.get('pagina') ?? '1';
  const risposta = await fetch(`/api/articoli?pagina=${pagina}`);

  if (!risposta.ok) {
    throw error(404, 'Articoli non trovati');
  }

  const articoli = await risposta.json();

  return {
    articoli,
    paginaCorrente: parseInt(pagina)
  };
}
```

```svelte
<!-- src/routes/blog/+page.svelte -->
<script>
  export let data;
</script>

<h1>Blog</h1>
{#each data.articoli as articolo}
  <article>
    <h2><a href="/blog/{articolo.slug}">{articolo.titolo}</a></h2>
    <p>{articolo.estratto}</p>
  </article>
{/each}
```

Esistono due tipi di load function:

- **`+page.server.js`** (o `+layout.server.js`): eseguita solo sul server. Ha accesso a database, variabili d'ambiente, cookie e altri dati sensibili. I dati restituiti devono essere serializzabili.
- **`+page.js`** (o `+layout.js`): eseguita sia sul server (per SSR) che nel browser (per navigazione client-side). Utile per dati che non richiedono segreti server-side e per la composizione di dati da fonti diverse.

### Form Actions

Le form actions gestiscono l'invio di form in modo progressivamente migliorato. Funzionano senza JavaScript e migliorano l'esperienza quando JS è disponibile:

```javascript
// src/routes/login/+page.server.js
import { fail, redirect } from '@sveltejs/kit';

export const actions = {
  login: async ({ request, cookies }) => {
    const dati = await request.formData();
    const email = dati.get('email');
    const password = dati.get('password');

    if (!email || !password) {
      return fail(400, {
        email,
        errore: 'Email e password sono obbligatori'
      });
    }

    const utente = await autenticaUtente(email, password);

    if (!utente) {
      return fail(401, {
        email,
        errore: 'Credenziali non valide'
      });
    }

    cookies.set('session_id', utente.sessionId, {
      path: '/',
      httpOnly: true,
      sameSite: 'strict',
      secure: true,
      maxAge: 60 * 60 * 24 * 7 // 7 giorni
    });

    throw redirect(303, '/dashboard');
  },

  logout: async ({ cookies }) => {
    cookies.delete('session_id', { path: '/' });
    throw redirect(303, '/login');
  }
};
```

```svelte
<!-- src/routes/login/+page.svelte -->
<script>
  import { enhance } from '$app/forms';
  export let form;
</script>

<h1>Accedi</h1>

{#if form?.errore}
  <p class="errore">{form.errore}</p>
{/if}

<form method="POST" action="?/login" use:enhance>
  <label>
    Email
    <input name="email" type="email" value={form?.email ?? ''} />
  </label>
  <label>
    Password
    <input name="password" type="password" />
  </label>
  <button type="submit">Accedi</button>
</form>

<form method="POST" action="?/logout" use:enhance>
  <button type="submit">Esci</button>
</form>
```

La direttiva `use:enhance` abilita il progressive enhancement: senza JavaScript, il form funziona con un normale POST. Con JavaScript, l'invio avviene via fetch con aggiornamento della pagina senza ricaricamento completo.

### SSR, SSG e rendering ibrido

SvelteKit supporta diverse strategie di rendering configurabili per pagina:

```javascript
// src/routes/blog/+page.js

// Server-Side Rendering (predefinito)
export const ssr = true;

// Client-Side Rendering
export const csr = true;

// Pre-rendering (Static Site Generation)
export const prerender = true;

// Per pagine completamente statiche
export const prerender = true;
export const ssr = true;
export const csr = false;
```

Per la generazione statica completa del sito, si utilizza l'adapter statico:

```javascript
// svelte.config.js
import adapterStatic from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapterStatic({
      pages: 'build',
      assets: 'build',
      fallback: '404.html'
    })
  }
};
```

Gli adapter disponibili includono `adapter-auto` (rileva automaticamente la piattaforma), `adapter-node` (server Node.js), `adapter-static` (file statici), `adapter-vercel`, `adapter-netlify` e `adapter-cloudflare`. È possibile combinare SSR e SSG nella stessa applicazione, prerenderizzando le pagine statiche e usando SSR per quelle dinamiche.

### API Routes

Gli endpoint API si creano con file `+server.js` che esportano funzioni per i metodi HTTP:

```javascript
// src/routes/api/articoli/+server.js
import { json, error } from '@sveltejs/kit';

export async function GET({ url, locals }) {
  const pagina = parseInt(url.searchParams.get('pagina') ?? '1');
  const limite = parseInt(url.searchParams.get('limite') ?? '10');

  const articoli = await db.articoli.findMany({
    skip: (pagina - 1) * limite,
    take: limite,
    orderBy: { dataCreazione: 'desc' }
  });

  return json({
    articoli,
    pagina,
    totale: await db.articoli.count()
  });
}

export async function POST({ request, locals }) {
  if (!locals.utente) {
    throw error(401, 'Non autenticato');
  }

  const dati = await request.json();

  if (!dati.titolo || !dati.contenuto) {
    throw error(400, 'Titolo e contenuto sono obbligatori');
  }

  const articolo = await db.articoli.create({
    data: {
      titolo: dati.titolo,
      contenuto: dati.contenuto,
      autoreId: locals.utente.id
    }
  });

  return json(articolo, { status: 201 });
}

export async function DELETE({ params, locals }) {
  if (!locals.utente?.isAdmin) {
    throw error(403, 'Permesso negato');
  }

  await db.articoli.delete({ where: { id: params.id } });
  return new Response(null, { status: 204 });
}
```

### Hooks

I hook di SvelteKit intercettano e gestiscono le richieste a livello globale:

```javascript
// src/hooks.server.js
export async function handle({ event, resolve }) {
  // Eseguito per ogni richiesta
  const sessionId = event.cookies.get('session_id');

  if (sessionId) {
    const utente = await db.sessioni.findUnique({
      where: { id: sessionId },
      include: { utente: true }
    });
    event.locals.utente = utente?.utente;
  }

  // Protezione delle route autenticate
  if (event.url.pathname.startsWith('/dashboard') && !event.locals.utente) {
    return new Response(null, {
      status: 303,
      headers: { location: '/login' }
    });
  }

  const risposta = await resolve(event);
  return risposta;
}

export function handleError({ error, event }) {
  console.error('Errore server:', error);
  return {
    message: 'Errore interno del server',
    code: 'ERRORE_INTERNO'
  };
}
```

### Streaming con le Load Function

SvelteKit supporta lo streaming dei dati nelle load function. Invece di attendere che tutti i dati siano pronti prima di inviare la risposta, è possibile inviare la struttura HTML immediatamente e far arrivare i dati man mano che diventano disponibili. Questo migliora drasticamente il Time To First Byte (TTFB):

```javascript
// src/routes/dashboard/+page.server.js
export async function load({ fetch }) {
  // Dati critici: attendiamo prima di renderizzare
  const profilo = await fetch('/api/profilo').then(r => r.json());

  // Dati secondari: streammati dopo il rendering iniziale
  // NON usiamo await — restituiamo la promise direttamente
  const statistiche = fetch('/api/statistiche').then(r => r.json());
  const notifiche = fetch('/api/notifiche').then(r => r.json());
  const attivitaRecenti = fetch('/api/attivita').then(r => r.json());

  return {
    profilo,          // Disponibile immediatamente
    statistiche,      // Promise — streammata
    notifiche,        // Promise — streammata
    attivitaRecenti   // Promise — streammata
  };
}
```

```svelte
<!-- src/routes/dashboard/+page.svelte -->
<script>
  let { data } = $props();
</script>

<!-- Profilo renderizzato immediatamente -->
<h1>Benvenuto, {data.profilo.nome}</h1>

<!-- Statistiche streammati con fallback durante il caricamento -->
{#await data.statistiche}
  <div class="skeleton">Caricamento statistiche...</div>
{:then stats}
  <div class="statistiche">
    <p>Totale vendite: {stats.totaleVendite}</p>
    <p>Clienti attivi: {stats.clientiAttivi}</p>
  </div>
{:catch errore}
  <p class="errore">Impossibile caricare le statistiche</p>
{/await}

{#await data.notifiche}
  <div class="skeleton">Caricamento notifiche...</div>
{:then notifiche}
  <ul>
    {#each notifiche as n}
      <li>{n.messaggio}</li>
    {/each}
  </ul>
{/await}
```

La differenza fondamentale è che le promise non await-ate nella load function vengono streammete al client: SvelteKit invia l'HTML iniziale con i dati disponibili, poi completa la pagina man mano che le promise si risolvono. Questo è particolarmente efficace per dashboard con molte sezioni indipendenti.

### Sequenza di Hooks in SvelteKit

SvelteKit offre diversi punti di intercettazione a livello server e client. La sequenza completa è:

```
Richiesta in arrivo
  └─ hooks.server.ts → handle()
       ├─ Autenticazione, CORS, logging
       ├─ Modifica event.locals
       └─ resolve(event)
            ├─ Matching della route
            ├─ +layout.server.ts → load()
            ├─ +page.server.ts → load()
            ├─ +layout.ts → load() (SSR)
            ├─ +page.ts → load() (SSR)
            ├─ Rendering HTML
            └─ Risposta al client
  └─ hooks.server.ts → handleError() (se errore)

Navigazione client-side
  └─ hooks.client.ts → handleError() (se errore)
  └─ +layout.ts → load() (client)
  └─ +page.ts → load() (client)
```

Il file `hooks.server.ts` supporta anche `handleFetch`, che intercetta le chiamate `fetch` fatte nelle load function server-side, utile per riscrivere URL o aggiungere header di autenticazione verso servizi interni:

```typescript
// src/hooks.server.ts
export async function handleFetch({ event, request, fetch }) {
  // Riscrivere URL per servizi interni
  if (request.url.startsWith('https://api.pubblica.com')) {
    const url = request.url.replace(
      'https://api.pubblica.com',
      'http://api-interna:3000'
    );
    request = new Request(url, request);
  }

  // Aggiungere token di autenticazione per servizi interni
  if (request.url.startsWith('http://api-interna')) {
    request.headers.set('Authorization', `Bearer ${event.locals.tokenInterno}`);
  }

  return fetch(request);
}
```

---

## Ecosystem

### Skeleton UI

Skeleton UI è una libreria di componenti UI progettata specificamente per Svelte e SvelteKit. Offre componenti predefiniti, un sistema di temi e integrazione con Tailwind CSS:

```bash
npx sv create mio-progetto
# Selezionare Skeleton UI durante la configurazione
```

```svelte
<script>
  import { AppShell, AppBar, LightSwitch } from '@skeletonlabs/skeleton';
  import { TabGroup, Tab, SlideToggle } from '@skeletonlabs/skeleton';

  let tabCorrente = 0;
  let attivo = false;
</script>

<AppShell>
  <svelte:fragment slot="header">
    <AppBar>
      <svelte:fragment slot="lead">
        <strong>La Mia App</strong>
      </svelte:fragment>
      <svelte:fragment slot="trail">
        <LightSwitch />
      </svelte:fragment>
    </AppBar>
  </svelte:fragment>

  <div class="container mx-auto p-8">
    <TabGroup>
      <Tab bind:group={tabCorrente} name="tab1" value={0}>Primo</Tab>
      <Tab bind:group={tabCorrente} name="tab2" value={1}>Secondo</Tab>
      <Tab bind:group={tabCorrente} name="tab3" value={2}>Terzo</Tab>
    </TabGroup>

    <SlideToggle bind:checked={attivo} name="toggle">
      {attivo ? 'Attivo' : 'Disattivo'}
    </SlideToggle>
  </div>
</AppShell>
```

Altre librerie UI popolari nell'ecosistema Svelte includono **Flowbite Svelte** (componenti basati su Tailwind), **Melt UI** (componenti headless accessibili), **Bits UI** (primitivi UI componibili) e **shadcn-svelte** (componenti personalizzabili ispirati a shadcn/ui).

### Testing con Playwright e Vitest

SvelteKit integra nativamente Playwright per i test end-to-end e Vitest per i test unitari e di componente:

**Test unitari con Vitest:**

```javascript
// src/lib/utils.test.js
import { describe, it, expect } from 'vitest';
import { formattaPrezzo, calcolaSconto } from './utils.js';

describe('formattaPrezzo', () => {
  it('formatta correttamente i prezzi in euro', () => {
    expect(formattaPrezzo(1234.5)).toBe('1.234,50 €');
  });

  it('gestisce lo zero', () => {
    expect(formattaPrezzo(0)).toBe('0,00 €');
  });
});

describe('calcolaSconto', () => {
  it('calcola lo sconto percentuale', () => {
    expect(calcolaSconto(100, 20)).toBe(80);
  });

  it('non permette sconti superiori al 100%', () => {
    expect(calcolaSconto(100, 150)).toBe(0);
  });
});
```

**Test di componente con Vitest e testing-library:**

```javascript
// src/lib/components/Contatore.test.js
import { describe, it, expect } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import Contatore from './Contatore.svelte';

describe('Contatore', () => {
  it('mostra il valore iniziale', () => {
    const { getByText } = render(Contatore, { props: { iniziale: 5 } });
    expect(getByText('Conteggio: 5')).toBeTruthy();
  });

  it('incrementa al click', async () => {
    const { getByText, getByRole } = render(Contatore);
    const pulsante = getByRole('button', { name: '+1' });

    await fireEvent.click(pulsante);
    expect(getByText('Conteggio: 1')).toBeTruthy();
  });
});
```

**Test end-to-end con Playwright:**

```javascript
// tests/blog.test.js
import { expect, test } from '@playwright/test';

test.describe('Blog', () => {
  test('la pagina del blog carica correttamente', async ({ page }) => {
    await page.goto('/blog');
    await expect(page.locator('h1')).toHaveText('Blog');
    await expect(page.locator('article')).toHaveCount(10);
  });

  test('la ricerca filtra gli articoli', async ({ page }) => {
    await page.goto('/blog');
    await page.fill('input[name="ricerca"]', 'Svelte');
    await expect(page.locator('article')).toHaveCount(3);
    await expect(page.locator('article').first()).toContainText('Svelte');
  });

  test('la navigazione a un articolo funziona', async ({ page }) => {
    await page.goto('/blog');
    await page.click('article:first-child a');
    await expect(page).toHaveURL(/\/blog\/.+/);
    await expect(page.locator('article h1')).toBeVisible();
  });
});
```

La configurazione Vitest per SvelteKit si trova nel file `vite.config.js`:

```javascript
// vite.config.js
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    include: ['src/**/*.{test,spec}.{js,ts}'],
    environment: 'jsdom',
    globals: true
  }
});
```

### Testing di componenti Svelte 5 con rune

Il testing di componenti che usano rune richiede attenzione alla versione di `@testing-library/svelte`. La versione 5+ supporta nativamente Svelte 5 e le rune:

```bash
npm install -D @testing-library/svelte @testing-library/jest-dom vitest
```

```typescript
// src/lib/components/ListaSpesa.test.ts
import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent, screen, within } from '@testing-library/svelte';
import ListaSpesa from './ListaSpesa.svelte';

describe('ListaSpesa', () => {
  it('renderizza la lista di articoli passati come props', () => {
    render(ListaSpesa, {
      props: {
        articoli: [
          { id: '1', nome: 'Pane', quantita: 2 },
          { id: '2', nome: 'Latte', quantita: 1 }
        ]
      }
    });

    expect(screen.getByText('Pane')).toBeTruthy();
    expect(screen.getByText('Latte')).toBeTruthy();
  });

  it('aggiunge un articolo quando si preme il pulsante', async () => {
    render(ListaSpesa, {
      props: { articoli: [] }
    });

    const input = screen.getByPlaceholderText('Nuovo articolo');
    const pulsante = screen.getByRole('button', { name: 'Aggiungi' });

    await fireEvent.input(input, { target: { value: 'Uova' } });
    await fireEvent.click(pulsante);

    expect(screen.getByText('Uova')).toBeTruthy();
  });

  it('chiama la callback onRimuovi quando si elimina un articolo', async () => {
    const onRimuovi = vi.fn();
    render(ListaSpesa, {
      props: {
        articoli: [{ id: '1', nome: 'Pane', quantita: 2 }],
        onRimuovi
      }
    });

    const pulsanteRimuovi = screen.getByRole('button', { name: /rimuovi/i });
    await fireEvent.click(pulsanteRimuovi);

    expect(onRimuovi).toHaveBeenCalledWith('1');
  });
});
```

### Testing degli store e dello stato reattivo

Per testare la logica reattiva contenuta nei file `.svelte.ts`, si può creare un harness di test che simula l'ambiente reattivo:

```typescript
// src/lib/state/carrello.test.ts
import { describe, it, expect } from 'vitest';
import { carrello } from './carrello.svelte.ts';
import { flushSync } from 'svelte';

describe('StatoCarrello', () => {
  it('aggiunge un articolo al carrello', () => {
    carrello.svuota();
    carrello.aggiungi({ id: 'a1', nome: 'T-shirt', prezzo: 29.99 });

    flushSync(); // Forza la risoluzione degli aggiornamenti reattivi

    expect(carrello.articoli).toHaveLength(1);
    expect(carrello.totale).toBe(29.99);
  });

  it('incrementa la quantità se l\'articolo esiste già', () => {
    carrello.svuota();
    carrello.aggiungi({ id: 'a1', nome: 'T-shirt', prezzo: 29.99 });
    carrello.aggiungi({ id: 'a1', nome: 'T-shirt', prezzo: 29.99 });

    flushSync();

    expect(carrello.articoli).toHaveLength(1);
    expect(carrello.articoli[0].quantita).toBe(2);
    expect(carrello.totale).toBeCloseTo(59.98);
  });

  it('rimuove un articolo dal carrello', () => {
    carrello.svuota();
    carrello.aggiungi({ id: 'a1', nome: 'T-shirt', prezzo: 29.99 });
    carrello.rimuovi('a1');

    flushSync();

    expect(carrello.articoli).toHaveLength(0);
    expect(carrello.totale).toBe(0);
  });
});
```

### Testing delle Load Function e delle Actions

Le load function e le actions possono essere testate separatamente come normali funzioni asincrone, mockando le dipendenze:

```typescript
// src/routes/blog/+page.server.test.ts
import { describe, it, expect, vi } from 'vitest';
import { load, actions } from './+page.server';

describe('Blog load function', () => {
  it('restituisce gli articoli paginati', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { id: '1', titolo: 'Primo articolo', slug: 'primo' }
      ])
    });

    const risultato = await load({
      fetch: mockFetch,
      url: new URL('http://localhost/blog?pagina=1'),
      params: {},
      cookies: { get: vi.fn(), set: vi.fn() },
      locals: {}
    });

    expect(risultato.articoli).toHaveLength(1);
    expect(mockFetch).toHaveBeenCalledWith('/api/articoli?pagina=1');
  });
});

describe('Blog actions', () => {
  it('restituisce errore per dati mancanti', async () => {
    const formData = new FormData();
    // Non aggiungiamo titolo né contenuto

    const risultato = await actions.crea({
      request: { formData: () => Promise.resolve(formData) },
      locals: { utente: { id: '1' } }
    });

    expect(risultato?.status).toBe(400);
  });
});
```

---

## Confronto con React e Vue

La seguente tabella mette a confronto Svelte con React e Vue sui principali aspetti dello sviluppo frontend:

| Aspetto | Svelte | React | Vue |
|---|---|---|---|
| **Approccio** | Compilatore | Runtime (virtual DOM) | Runtime (virtual DOM) |
| **Dimensione bundle** | Molto piccola (~2 KB base) | ~42 KB (React + ReactDOM) | ~33 KB (Vue 3) |
| **Sintassi componenti** | File `.svelte` (HTML nativo) | JSX | SFC (`.vue`) / template |
| **Reattività** | Assegnazione / Runes | `useState`, `useReducer` | `ref`, `reactive` |
| **Stato derivato** | `$derived` / `$:` | `useMemo` | `computed` |
| **Effetti collaterali** | `$effect` / `$:` | `useEffect` | `watch`, `watchEffect` |
| **Stili** | Scoped automatico | CSS Modules / CSS-in-JS | Scoped con `<style scoped>` |
| **Animazioni** | Built-in (`transition:`) | Librerie esterne (Framer Motion) | Built-in (`<Transition>`) |
| **Curva apprendimento** | Bassa | Media | Media-bassa |
| **Framework full-stack** | SvelteKit | Next.js / Remix | Nuxt |
| **Gestione form** | Binding nativo + Actions | Controlled components | `v-model` |
| **Gestione stato globale** | Store integrati | Context / Redux / Zustand | Pinia / Vuex |
| **TypeScript** | Supporto nativo | Supporto nativo | Supporto nativo |
| **SSR** | SvelteKit (integrato) | Next.js / framework esterno | Nuxt / framework esterno |
| **Ecosistema** | In crescita | Molto ampio | Ampio |
| **Maturità** | 2016 (v5: 2024) | 2013 | 2014 |
| **Mercato del lavoro** | In crescita | Dominante | Forte in Europa/Asia |

### Vantaggi chiave di Svelte

- **Meno codice**: Svelte richiede tipicamente il 30-40% di codice in meno rispetto a React per la stessa funzionalità, grazie alla sintassi concisa e ai binding bidirezionali.
- **Prestazioni**: senza virtual DOM, le operazioni di aggiornamento sono dirette e misurabili come più veloci nei benchmark, specialmente per aggiornamenti frequenti e granulari.
- **Bundle size**: le applicazioni Svelte partono da pochi KB e crescono solo con il codice effettivamente utilizzato, a differenza dei framework con runtime fisso.
- **Esperienza sviluppatore**: la sintassi è vicina all'HTML/CSS/JS standard, con meno concetti astratti da apprendere.

### Limiti di Svelte

- **Ecosistema più piccolo**: meno librerie di terze parti rispetto a React. Tuttavia, la compatibilità con librerie JavaScript vanilla compensa parzialmente questo limite.
- **Mercato del lavoro**: meno offerte di lavoro rispetto a React, sebbene la domanda sia in crescita costante.
- **Breaking changes**: il passaggio a Svelte 5 con le rune ha introdotto cambiamenti significativi, richiedendo adattamento per i progetti esistenti (è comunque disponibile una modalità di compatibilità).

### Confronto architetturale: compilazione vs runtime

La differenza più profonda tra Svelte e React/Vue è **quando** viene eseguito il lavoro di rendering.

**React** mantiene un virtual DOM in memoria. Ad ogni cambio di stato, React esegue la funzione componente per generare un nuovo albero virtuale, lo confronta con il precedente (reconciliation/diffing) e applica le differenze al DOM reale. Questo approccio è universale ma introduce overhead proporzionale alla dimensione dell'albero, anche quando solo un singolo nodo cambia.

**Vue 3** utilizza un approccio ibrido. Il compilatore di template genera codice di rendering con "patch flags" che indicano quali parti del template sono dinamiche. Il runtime usa comunque un virtual DOM, ma il diffing è ottimizzato perché sa in anticipo dove cercare le differenze. La Composition API (`ref`, `reactive`) implementa un sistema reattivo basato su Proxy simile ai segnali.

**Svelte 5** elimina completamente il virtual DOM. Il compilatore analizza il codice sorgente e genera istruzioni imperative che aggiornano direttamente il DOM. Il sistema di segnali (rune) traccia le dipendenze a livello di singola proprietà, e gli aggiornamenti sono O(1) rispetto alla dimensione del componente: modificare un valore aggiorna solo i nodi DOM che lo leggono, senza attraversare l'intero albero.

In termini pratici, la differenza è misurabile nei seguenti scenari:

- **Liste grandi con aggiornamenti puntuali**: Svelte aggiorna il singolo nodo; React/Vue devono attraversare la lista virtuale.
- **Bundle size iniziale**: un'app Svelte vuota pesa ~2 KB; React + ReactDOM pesano ~42 KB; Vue ~33 KB.
- **Tempo di avvio**: Svelte non ha un runtime da inizializzare; React e Vue devono bootstrap-are il virtual DOM e il sistema reattivo.
- **Aggiornamenti frequenti** (animazioni, timer): Svelte applica le modifiche direttamente; React può accumulare re-render se non si usa `useMemo`/`useCallback` correttamente.

### Quando scegliere Svelte

Svelte è particolarmente adatto per:

- **Applicazioni con requisiti di prestazione stringenti**: portali embeddabili, widget, componenti interattivi da incorporare in pagine esistenti.
- **Prototipi rapidi e MVP**: la sintassi concisa accelera lo sviluppo e riduce il time-to-market.
- **Applicazioni con bundle budget limitato**: siti mobile-first dove ogni KB conta.
- **Team piccoli-medi**: meno boilerplate significa meno codice da mantenere e revisionare.
- **Applicazioni full-stack monolitiche**: SvelteKit fornisce tutto (routing, SSR, API, form) in un pacchetto integrato.

React resta preferibile per team molto grandi con competenze consolidate, applicazioni enterprise con ecosistema di librerie specializzate, o quando è necessaria la compatibilità con React Native per app mobile.

---

## Best Practices

### 1. Struttura del progetto chiara e consistente

Organizzare il codice seguendo convenzioni consolidate migliora la manutenibilità:

```
src/
├── lib/
│   ├── components/    # Componenti riutilizzabili
│   │   ├── ui/        # Componenti UI generici
│   │   └── layout/    # Componenti di layout
│   ├── stores/        # Store globali
│   ├── utils/         # Funzioni di utilità
│   ├── types/         # Tipi TypeScript
│   └── server/        # Codice esclusivamente server
├── routes/            # Pagine e API
├── params/            # Matcher per parametri route
└── app.html           # Template HTML base
```

Usare l'alias `$lib` per gli import dalla cartella `lib`: `import Pulsante from '$lib/components/ui/Pulsante.svelte'`. Mantenere i componenti piccoli e focalizzati su una singola responsabilità, suddividendo quelli che superano le 200-250 righe.

### 2. Usare TypeScript per la sicurezza dei tipi

TypeScript migliora drasticamente l'affidabilità del codice e l'esperienza di sviluppo con autocompletamento e rilevamento degli errori:

```svelte
<script lang="ts">
  interface Articolo {
    id: string;
    titolo: string;
    contenuto: string;
    dataCreazione: Date;
    autore: {
      nome: string;
      avatar: string;
    };
  }

  let { articoli, pagina = 1 }: { articoli: Articolo[]; pagina?: number } = $props();
</script>
```

Definire i tipi per le load function, le actions, e gli store globali. Utilizzare il file `app.d.ts` per i tipi di `locals`, `PageData` e `Error` personalizzati.

### 3. Gestire correttamente gli effetti e il cleanup

Ogni effetto che crea risorse (listener, timer, sottoscrizioni) deve implementare una funzione di cleanup per evitare memory leak:

```svelte
<script>
  let larghezza = $state(0);

  $effect(() => {
    function aggiorna() {
      larghezza = window.innerWidth;
    }
    aggiorna();
    window.addEventListener('resize', aggiorna);

    return () => window.removeEventListener('resize', aggiorna);
  });
</script>
```

Non eseguire mai side effects direttamente in `$derived`; usare sempre `$effect` per operazioni che interagiscono con il mondo esterno (API, DOM, storage).

### 4. Ottimizzare le prestazioni di rendering

Utilizzare chiavi stabili e univoche nei blocchi `{#each}` per garantire aggiornamenti efficienti. Evitare di usare l'indice dell'array come chiave quando gli elementi possono essere riordinati o rimossi:

```svelte
<!-- Corretto: chiave stabile e univoca -->
{#each utenti as utente (utente.id)}
  <ProfiloUtente {utente} />
{/each}

<!-- Evitare: indice come chiave con liste dinamiche -->
{#each utenti as utente, i (i)}
  <ProfiloUtente {utente} />
{/each}
```

Per grandi liste, considerare la virtualizzazione con librerie come `svelte-virtual-list`. Usare `$state.raw()` per strutture dati grandi e immutabili che non necessitano di tracking profondo delle mutazioni.

### 5. Implementare il progressive enhancement

Progettare le funzionalità in modo che funzionino senza JavaScript e migliorino con esso. Le form actions di SvelteKit sono progettate per questo scopo:

```svelte
<form method="POST" action="?/salva" use:enhance={({ formData, cancel }) => {
  // Validazione client-side (miglioramento progressivo)
  const titolo = formData.get('titolo');
  if (!titolo || titolo.toString().length < 3) {
    mostraErrore('Il titolo deve avere almeno 3 caratteri');
    cancel();
    return;
  }

  caricamento = true;

  return async ({ result, update }) => {
    caricamento = false;
    if (result.type === 'success') {
      mostraNotifica('Salvato con successo!');
    }
    await update();
  };
}}>
  <input name="titolo" required minlength="3" />
  <button disabled={caricamento}>
    {caricamento ? 'Salvataggio...' : 'Salva'}
  </button>
</form>
```

### 6. Separare la logica dal template

Estrarre la logica complessa in funzioni e moduli dedicati per mantenere i componenti leggibili e testabili:

```javascript
// src/lib/utils/validazione.js
export function validaEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function validaForm(dati) {
  const errori = {};
  if (!dati.nome) errori.nome = 'Il nome è obbligatorio';
  if (!validaEmail(dati.email)) errori.email = 'Email non valida';
  if (dati.password.length < 8) errori.password = 'Minimo 8 caratteri';
  return { valido: Object.keys(errori).length === 0, errori };
}
```

```svelte
<script>
  import { validaForm } from '$lib/utils/validazione.js';

  let datiForm = $state({ nome: '', email: '', password: '' });
  let errori = $state({});

  function gestisciInvio() {
    const risultato = validaForm(datiForm);
    errori = risultato.errori;
    if (risultato.valido) {
      // procedi con l'invio
    }
  }
</script>
```

### 7. Gestire errori e stati di caricamento in modo uniforme

Creare componenti e pattern riutilizzabili per gestire gli stati di caricamento, errore e assenza di dati:

```svelte
<!-- src/lib/components/AsyncContent.svelte -->
<script>
  let { caricamento = false, errore = null, dati = null } = $props();
</script>

{#if caricamento}
  <div class="caricamento" role="status" aria-label="Caricamento in corso">
    <slot name="caricamento">
      <p>Caricamento in corso...</p>
    </slot>
  </div>
{:else if errore}
  <div class="errore" role="alert">
    <slot name="errore" {errore}>
      <p>Si è verificato un errore: {errore.message}</p>
    </slot>
  </div>
{:else if dati}
  <slot {dati} />
{:else}
  <slot name="vuoto">
    <p>Nessun dato disponibile.</p>
  </slot>
{/if}
```

Utilizzare i boundary di errore di SvelteKit (`+error.svelte`) per gestire gli errori a livello di pagina e layout. Implementare pagine di errore personalizzate per codici specifici (404, 500).

### 8. Sicurezza e protezione dei dati sensibili

Mantenere una netta separazione tra codice server e client per evitare l'esposizione accidentale di dati sensibili:

```javascript
// src/lib/server/database.js
// Questo modulo è accessibile SOLO dal server grazie alla cartella 'server'
import { DATABASE_URL } from '$env/static/private';

export const db = new PrismaClient({
  datasources: { db: { url: DATABASE_URL } }
});
```

```javascript
// src/routes/api/utenti/+server.js
import { db } from '$lib/server/database.js';

export async function GET({ locals }) {
  if (!locals.utente?.isAdmin) {
    return new Response('Non autorizzato', { status: 403 });
  }

  const utenti = await db.utenti.findMany({
    select: {
      id: true,
      nome: true,
      email: true
      // NON esporre mai: passwordHash, token, datiSensibili
    }
  });

  return json(utenti);
}
```

Usare `$env/static/private` per le variabili d'ambiente sensibili (accessibili solo lato server) e `$env/static/public` per quelle pubbliche (prefisso `PUBLIC_`). Non memorizzare mai segreti, token o chiavi API nel codice client o negli store accessibili dal browser. Validare e sanitizzare sempre l'input utente, sia lato client che lato server, trattando il server come l'unica fonte di verità per la sicurezza.

---

> **Risorse utili:** [Documentazione ufficiale Svelte](https://svelte.dev/docs), [Tutorial interattivo](https://learn.svelte.dev), [SvelteKit docs](https://svelte.dev/docs/kit), [Svelte REPL](https://svelte.dev/playground)

---

## Il Compilatore Svelte — Architettura Interna

### Panoramica del processo di compilazione

Il compilatore Svelte è il cuore dell'intero framework. A differenza di React o Vue, dove un runtime interpreta i componenti a ogni ciclo di rendering, Svelte trasforma il codice sorgente in istruzioni JavaScript imperative durante la fase di build. Questo approccio elimina la necessità di un virtual DOM e produce bundle significativamente più piccoli.

Il processo di compilazione si articola in quattro fasi principali:

1. **Parsing** — Il codice sorgente `.svelte` viene analizzato e trasformato in un Abstract Syntax Tree (AST). Le sezioni `<script>`, il markup e `<style>` vengono parsate separatamente. Per il JavaScript, Svelte utilizza internamente il parser **Acorn**, lo stesso motore usato da webpack, ESLint e Rollup. Il markup HTML viene parsato con un parser custom che comprende la sintassi specifica di Svelte (`{#if}`, `{#each}`, `{@render}`, ecc.).

2. **Analisi** — L'AST viene attraversato per raccogliere informazioni semantiche: quali variabili sono dichiarate, quali sono reattive (tramite rune), quali dipendenze esistono tra esse e quali nodi DOM sono influenzati da ciascuna variabile. In Svelte 5, questa fase identifica le rune (`$state`, `$derived`, `$effect`) e le trasforma nei costrutti interni del sistema di segnali.

3. **Trasformazione** — L'AST viene modificato per inserire le istruzioni di aggiornamento. Per ogni binding reattivo, il compilatore genera codice che aggiorna chirurgicamente i nodi DOM corrispondenti quando il valore cambia. Questa è la fase dove Svelte "sa" esattamente quale nodo `<p>` aggiornare quando `conteggio` cambia, senza dover confrontare alberi virtuali.

4. **Generazione del codice** — L'AST trasformato viene convertito in codice JavaScript e CSS finali. Il risultato è un modulo ES che esporta il componente come classe istanziabile con metodi per il mount, l'aggiornamento e la distruzione.

### Output compilato: anatomia

Per comprendere cosa produce il compilatore, consideriamo un componente semplice:

```svelte
<script>
  let conteggio = $state(0);
  let doppio = $derived(conteggio * 2);
</script>

<button onclick={() => conteggio++}>
  {conteggio} (doppio: {doppio})
</button>
```

Il compilatore genera approssimativamente questo codice (semplificato):

```javascript
import { $, mount, text, element, listen, set_text } from 'svelte/internal';

export default function Componente(target) {
  // Creazione dei segnali reattivi
  let conteggio = $.source(0);
  let doppio = $.derived(() => $.get(conteggio) * 2);

  // Creazione degli elementi DOM
  let button = element('button');
  let txt = text('');

  // Funzione di aggiornamento — chiamata SOLO quando cambia conteggio
  function aggiorna() {
    set_text(txt, `${$.get(conteggio)} (doppio: ${$.get(doppio)})`);
  }

  // Event listener
  listen(button, 'click', () => {
    $.set(conteggio, $.get(conteggio) + 1);
  });

  // Effetto reattivo che lega il segnale al DOM
  $.render_effect(aggiorna);

  // Mount nel target
  mount(button, target);
}
```

I punti chiave dell'output compilato sono:

- **Nessun virtual DOM**: non c'è `createElement`, `diff` o `reconciliation`. Il compilatore genera codice che chiama direttamente `element()`, `text()` e `set_text()`.
- **Aggiornamenti mirati**: ogni binding reattivo produce un effetto di rendering che aggiorna solo il nodo DOM specifico interessato.
- **Tree-shaking aggressivo**: solo le funzioni runtime effettivamente usate vengono incluse nel bundle. Un componente senza transizioni non include il codice delle transizioni.
- **Segnali come primitiva**: in Svelte 5, `$state` si compila in un segnale (`$.source`), `$derived` in un segnale derivato (`$.derived`) e `$effect` in un effetto (`$.effect`).

### Il sistema di segnali in Svelte 5

Svelte 5 ha abbandonato il meccanismo di invalidazione basato su `$$invalidate()` di Svelte 4 in favore di un sistema di segnali (signals) più efficiente. I segnali sono la primitiva reattiva fondamentale: un valore che può essere letto e scritto, e che notifica automaticamente i suoi consumatori quando cambia.

Il sistema funziona in tre strati:

- **Source signals** (`$.source`): rappresentano lo stato primario. Corrispondono a `$state`. Mantengono un valore e una lista di sottoscrittori.
- **Derived signals** (`$.derived`): rappresentano valori calcolati. Corrispondono a `$derived`. Vengono ricalcolati solo quando le dipendenze effettivamente cambiano (lazy evaluation con memoizzazione).
- **Effects** (`$.effect`, `$.render_effect`): rappresentano side effects. I render effects aggiornano il DOM; gli user effects eseguono logica personalizzata. Entrambi tracciano automaticamente le dipendenze lette durante la loro esecuzione.

La granularità è a livello di singola proprietà. Se un oggetto `$state({ a: 1, b: 2 })` cambia solo `a`, gli effetti che leggono solo `b` non vengono rieseguiti. Questo è possibile grazie al proxy reattivo che Svelte 5 avvolge attorno agli oggetti `$state`.

### Opzioni del compilatore

Il compilatore accetta diverse opzioni tramite la funzione `svelte.compile()`:

```javascript
import { compile } from 'svelte/compiler';

const risultato = compile(sorgente, {
  // Genera codice per componenti server-side (SSR)
  generate: 'client', // 'client' | 'server'

  // Abilita il mode di sviluppo (warning, $inspect, ecc.)
  dev: false,

  // Prefisso per le classi CSS scoped
  cssHash: ({ hash, css }) => `s-${hash(css)}`,

  // Abilita le rune (default true in Svelte 5)
  runes: true,

  // Genera sourcemap
  enableSourcemap: true,

  // Nome del file sorgente (per i messaggi di errore)
  filename: 'Componente.svelte',

  // Namespace HTML (html, svg, mathml)
  namespace: 'html'
});

// risultato.js   — codice JavaScript generato
// risultato.css  — codice CSS generato (con classi scoped)
// risultato.warnings — avvisi del compilatore (inclusi a11y)
// risultato.metadata — informazioni sui rune usati, export, ecc.
```

Il compilatore espone anche `svelte.parse()` per ottenere solo l'AST senza compilare e `svelte.preprocess()` per applicare preprocessori (TypeScript, SCSS, PostCSS) prima della compilazione vera e propria.

---

## Pattern di Composizione dei Componenti

### Snippet e tag `{@render}`

Svelte 5 introduce gli **snippet** come sostituti moderni degli slot. Uno snippet è un blocco di markup riutilizzabile dichiarato con `{#snippet}` e renderizzato con `{@render}`:

```svelte
<script>
  let frutti = $state([
    { nome: 'Mela', colore: 'rosso', calorie: 52 },
    { nome: 'Banana', colore: 'giallo', calorie: 89 },
    { nome: 'Ciliegia', colore: 'rosso', calorie: 50 }
  ]);
</script>

<!-- Definizione dello snippet con parametri -->
{#snippet rigaFrutto(frutto, indice)}
  <tr class:evidenziato={frutto.calorie < 55}>
    <td>{indice + 1}</td>
    <td>{frutto.nome}</td>
    <td style="color: {frutto.colore}">{frutto.colore}</td>
    <td>{frutto.calorie} kcal</td>
  </tr>
{/snippet}

<table>
  <thead>
    <tr><th>#</th><th>Nome</th><th>Colore</th><th>Calorie</th></tr>
  </thead>
  <tbody>
    {#each frutti as frutto, i}
      {@render rigaFrutto(frutto, i)}
    {/each}
  </tbody>
</table>
```

Gli snippet risolvono il problema della duplicazione di markup all'interno dello stesso componente. A differenza dei componenti, non hanno il proprio lifecycle, stato o stili scoped: sono puro markup parametrizzato.

### Children: il sostituto dello slot predefinito

In Svelte 5, il contenuto passato tra i tag di un componente diventa automaticamente la prop `children`, una prop di tipo snippet:

```svelte
<!-- Scheda.svelte -->
<script>
  let { titolo, children } = $props();
</script>

<div class="scheda">
  <h2>{titolo}</h2>
  <div class="contenuto">
    {@render children()}
  </div>
</div>
```

```svelte
<!-- Utilizzo -->
<Scheda titolo="Informazioni">
  <p>Questo contenuto diventa la prop children.</p>
  <p>Viene renderizzato dentro la scheda.</p>
</Scheda>
```

### Snippet come props: il sostituto degli slot con nome

Per passare markup personalizzato a specifiche sezioni di un componente (l'equivalente degli slot con nome), si passano snippet come props:

```svelte
<!-- Layout.svelte -->
<script>
  import type { Snippet } from 'svelte';

  let {
    intestazione,
    sidebar,
    children,
    piePagina
  }: {
    intestazione: Snippet;
    sidebar: Snippet;
    children: Snippet;
    piePagina?: Snippet;
  } = $props();
</script>

<div class="layout">
  <header>
    {@render intestazione()}
  </header>
  <aside>
    {@render sidebar()}
  </aside>
  <main>
    {@render children()}
  </main>
  {#if piePagina}
    <footer>
      {@render piePagina()}
    </footer>
  {/if}
</div>
```

```svelte
<!-- Utilizzo -->
<Layout>
  {#snippet intestazione()}
    <nav>
      <a href="/">Home</a>
      <a href="/blog">Blog</a>
    </nav>
  {/snippet}

  {#snippet sidebar()}
    <ul>
      <li>Voce 1</li>
      <li>Voce 2</li>
    </ul>
  {/snippet}

  <p>Questo è il contenuto principale (children).</p>

  {#snippet piePagina()}
    <p>&copy; 2025 La Mia App</p>
  {/snippet}
</Layout>
```

### Snippet con parametri tipizzati

Gli snippet possono ricevere parametri dal componente figlio, creando un pattern simile ai render props di React. Questo è particolarmente utile per componenti generici come liste, tabelle e selettori:

```svelte
<!-- ListaGenerica.svelte -->
<script lang="ts" generics="T">
  import type { Snippet } from 'svelte';

  let {
    elementi,
    renderElemento,
    renderVuoto
  }: {
    elementi: T[];
    renderElemento: Snippet<[T, number]>;
    renderVuoto?: Snippet;
  } = $props();
</script>

{#if elementi.length === 0}
  {#if renderVuoto}
    {@render renderVuoto()}
  {:else}
    <p>Nessun elemento trovato.</p>
  {/if}
{:else}
  <ul>
    {#each elementi as elemento, indice}
      <li>
        {@render renderElemento(elemento, indice)}
      </li>
    {/each}
  </ul>
{/if}
```

```svelte
<!-- Utilizzo con tipizzazione -->
<script lang="ts">
  import ListaGenerica from './ListaGenerica.svelte';

  interface Utente {
    id: string;
    nome: string;
    email: string;
  }

  let utenti: Utente[] = $state([
    { id: '1', nome: 'Marco', email: 'marco@esempio.it' },
    { id: '2', nome: 'Lucia', email: 'lucia@esempio.it' }
  ]);
</script>

<ListaGenerica elementi={utenti}>
  {#snippet renderElemento(utente, i)}
    <strong>{utente.nome}</strong> — {utente.email}
  {/snippet}

  {#snippet renderVuoto()}
    <p>Nessun utente registrato.</p>
  {/snippet}
</ListaGenerica>
```

### Pattern Compound Component

Il pattern compound component organizza componenti correlati sotto un namespace comune, dove il componente padre gestisce lo stato condiviso tramite context:

```svelte
<!-- Tabs.svelte -->
<script>
  import { setContext } from 'svelte';

  let { children, defaultValue } = $props();
  let attivo = $state(defaultValue);

  setContext('tabs', {
    get attivo() { return attivo; },
    seleziona(valore) { attivo = valore; }
  });
</script>

<div class="tabs" role="tablist">
  {@render children()}
</div>
```

```svelte
<!-- TabTrigger.svelte -->
<script>
  import { getContext } from 'svelte';

  let { valore, children } = $props();
  const tabs = getContext('tabs');
  let isAttivo = $derived(tabs.attivo === valore);
</script>

<button
  role="tab"
  aria-selected={isAttivo}
  class:attivo={isAttivo}
  onclick={() => tabs.seleziona(valore)}
>
  {@render children()}
</button>
```

```svelte
<!-- TabContenuto.svelte -->
<script>
  import { getContext } from 'svelte';

  let { valore, children } = $props();
  const tabs = getContext('tabs');
  let visibile = $derived(tabs.attivo === valore);
</script>

{#if visibile}
  <div role="tabpanel">
    {@render children()}
  </div>
{/if}
```

```svelte
<!-- Utilizzo del compound component -->
<Tabs defaultValue="generale">
  <TabTrigger valore="generale">Generale</TabTrigger>
  <TabTrigger valore="avanzate">Avanzate</TabTrigger>

  <TabContenuto valore="generale">
    <p>Impostazioni generali dell'applicazione.</p>
  </TabContenuto>
  <TabContenuto valore="avanzate">
    <p>Opzioni avanzate per utenti esperti.</p>
  </TabContenuto>
</Tabs>
```

### Wrapper trasparenti con `{...resto}`

Un pattern comune è creare componenti wrapper che inoltrano tutte le props non utilizzate all'elemento interno. In Svelte 5, il rest operator nel destructuring di `$props()` lo rende naturale:

```svelte
<!-- InputConEtichetta.svelte -->
<script lang="ts">
  let {
    etichetta,
    id,
    errore,
    ...resto
  }: {
    etichetta: string;
    id: string;
    errore?: string;
    [chiave: string]: unknown;
  } = $props();
</script>

<div class="campo" class:ha-errore={!!errore}>
  <label for={id}>{etichetta}</label>
  <input {id} aria-invalid={!!errore} aria-describedby={errore ? `${id}-errore` : undefined} {...resto} />
  {#if errore}
    <span id="{id}-errore" class="messaggio-errore" role="alert">{errore}</span>
  {/if}
</div>
```

---

## Migrazione Store verso Runes

### Quando migrare e quando mantenere gli store

Con Svelte 5, il sistema di rune copre la maggior parte dei casi d'uso precedentemente gestiti dagli store. Tuttavia, la migrazione non è sempre necessaria né immediata. La regola pratica è:

| Caso d'uso | Raccomandazione |
|---|---|
| Stato locale di un componente | Rune (`$state`) — sempre |
| Stato condiviso tra componenti correlati | Rune in file `.svelte.ts` |
| Stato globale dell'applicazione | Rune in file `.svelte.ts` |
| Stream asincroni complessi | Store (mantenerli) |
| Interoperabilità con librerie RxJS | Store (mantenerli) |
| Stato restituito da load function SvelteKit | `$page.data` (automatico) |

### Da `writable` a `$state` in un modulo

Il pattern più comune di migrazione è convertire uno store writable in stato reattivo esportato da un file `.svelte.ts`:

**Prima (Svelte 4 con store):**

```javascript
// src/lib/stores/carrello.js
import { writable, derived } from 'svelte/store';

export const articoli = writable([]);

export const totale = derived(articoli, ($articoli) =>
  $articoli.reduce((somma, a) => somma + a.prezzo * a.quantita, 0)
);

export function aggiungiArticolo(articolo) {
  articoli.update(lista => [...lista, { ...articolo, quantita: 1 }]);
}

export function rimuoviArticolo(id) {
  articoli.update(lista => lista.filter(a => a.id !== id));
}
```

```svelte
<!-- Componente Svelte 4 -->
<script>
  import { articoli, totale, aggiungiArticolo } from '$lib/stores/carrello.js';
</script>
<p>Totale: {$totale} €</p>
```

**Dopo (Svelte 5 con rune):**

```typescript
// src/lib/state/carrello.svelte.ts
interface Articolo {
  id: string;
  nome: string;
  prezzo: number;
  quantita: number;
}

// Lo stato DEVE essere esportato come proprietà di un oggetto o classe,
// MAI come variabile primitiva top-level
class StatoCarrello {
  articoli = $state<Articolo[]>([]);
  totale = $derived(
    this.articoli.reduce((somma, a) => somma + a.prezzo * a.quantita, 0)
  );
  numeroArticoli = $derived(
    this.articoli.reduce((somma, a) => somma + a.quantita, 0)
  );

  aggiungi(articolo: Omit<Articolo, 'quantita'>) {
    const esistente = this.articoli.find(a => a.id === articolo.id);
    if (esistente) {
      esistente.quantita += 1;
    } else {
      this.articoli.push({ ...articolo, quantita: 1 });
    }
  }

  rimuovi(id: string) {
    const indice = this.articoli.findIndex(a => a.id === id);
    if (indice !== -1) {
      this.articoli.splice(indice, 1);
    }
  }

  svuota() {
    this.articoli.length = 0;
  }
}

export const carrello = new StatoCarrello();
```

```svelte
<!-- Componente Svelte 5 -->
<script>
  import { carrello } from '$lib/state/carrello.svelte.ts';
</script>

<p>Totale: {carrello.totale} €</p>
<p>Articoli: {carrello.numeroArticoli}</p>
{#each carrello.articoli as articolo}
  <div>
    {articolo.nome} x{articolo.quantita}
    <button onclick={() => carrello.rimuovi(articolo.id)}>Rimuovi</button>
  </div>
{/each}
```

### Regola fondamentale: mai esportare primitive reattive

Un errore comune nella migrazione è esportare una variabile `$state` primitiva come export top-level:

```typescript
// SBAGLIATO — la reattività si perde all'export
// src/lib/state/contatore.svelte.ts
export let conteggio = $state(0); // NON FUNZIONA come ci si aspetta
```

Il motivo è che l'import riceve il **valore** al momento dell'importazione, non un riferimento reattivo. La soluzione è sempre incapsulare in un oggetto, una classe o una funzione factory:

```typescript
// CORRETTO — oggetto con proprietà reattiva
// src/lib/state/contatore.svelte.ts
function creaContatore(iniziale = 0) {
  let conteggio = $state(iniziale);

  return {
    get valore() { return conteggio; },
    incrementa() { conteggio++; },
    decrementa() { conteggio--; },
    resetta() { conteggio = iniziale; }
  };
}

export const contatore = creaContatore(0);
```

Il getter `get valore()` è fondamentale: quando un componente legge `contatore.valore`, Svelte traccia la dipendenza reattiva. Senza il getter, il valore verrebbe letto una sola volta e mai aggiornato.

### Migrazione di `$app/stores` in SvelteKit

SvelteKit 2 ha introdotto equivalenti rune-compatibili per gli store dell'applicazione:

```svelte
<!-- Prima: $app/stores -->
<script>
  import { page, navigating, updated } from '$app/stores';
</script>
<p>Route: {$page.url.pathname}</p>
{#if $navigating}
  <div class="barra-caricamento" />
{/if}

<!-- Dopo: $app/state -->
<script>
  import { page, navigating, updated } from '$app/state';
</script>
<p>Route: {page.url.pathname}</p>
{#if navigating.to}
  <div class="barra-caricamento" />
{/if}
```

La differenza principale è che con `$app/state` non serve il prefisso `$` per la sottoscrizione — gli oggetti sono già reattivi grazie al sistema di segnali. Gli import da `$app/stores` continuano a funzionare per retrocompatibilità, ma il nuovo codice dovrebbe usare `$app/state`.

### Strumenti di migrazione automatica

Svelte fornisce uno strumento CLI per automatizzare la migrazione della maggior parte dei pattern:

```bash
# Migrazione automatica del progetto a Svelte 5
npx sv migrate svelte-5
```

Lo strumento gestisce automaticamente:
- Conversione di `let variabile` in `let variabile = $state(valore)`
- Conversione di `$: derivato = expr` in `let derivato = $derived(expr)`
- Conversione di `$: { sideEffect() }` in `$effect(() => { sideEffect() })`
- Conversione di `export let prop` in destructuring da `$props()`
- Conversione di `createEventDispatcher` in callback props

I pattern che richiedono revisione manuale sono quelli che usano `$$props`, `$$restProps` o pattern complessi di event forwarding, dove il nuovo modello a callback richiede verifica che il componente padre utilizzi correttamente la nuova interfaccia.

---

## SSR, Idratazione e Streaming

### Come funziona il Server-Side Rendering in SvelteKit

Quando un browser richiede una pagina SvelteKit, il framework esegue il componente sul server per generare HTML completo. Questo processo coinvolge diversi passaggi:

1. **Matching della route**: SvelteKit determina quale pagina corrisponde all'URL richiesto.
2. **Esecuzione delle load function**: le funzioni `load` in `+page.server.ts` e `+layout.server.ts` vengono eseguite per ottenere i dati.
3. **Rendering del componente**: Svelte renderizza il componente in una stringa HTML sul server, usando una versione speciale del codice compilato (`generate: 'server'`).
4. **Serializzazione dei dati**: i dati restituiti dalle load function vengono serializzati in JSON e iniettati nell'HTML come tag `<script>`.
5. **Invio della risposta**: l'HTML completo viene inviato al browser.

```javascript
// src/routes/prodotti/[id]/+page.server.ts
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, locals }) => {
  const prodotto = await locals.db.prodotti.findUnique({
    where: { id: params.id }
  });

  if (!prodotto) {
    throw error(404, 'Prodotto non trovato');
  }

  return { prodotto };
};
```

Il componente riceve i dati e viene renderizzato prima sul server, poi idratato nel browser:

```svelte
<!-- src/routes/prodotti/[id]/+page.svelte -->
<script lang="ts">
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
</script>

<svelte:head>
  <title>{data.prodotto.nome} — Il Mio Negozio</title>
  <meta name="description" content={data.prodotto.descrizione} />
</svelte:head>

<article>
  <h1>{data.prodotto.nome}</h1>
  <p class="prezzo">{data.prodotto.prezzo.toFixed(2)} €</p>
  <div class="descrizione">
    {@html data.prodotto.descrizioneHtml}
  </div>
</article>
```

### Il processo di idratazione

L'idratazione è il processo attraverso cui Svelte "risveglia" l'HTML statico generato dal server, collegandovi la reattività e gli event listener. In Svelte 5, l'idratazione è stata completamente riscritta per essere più efficiente:

- **Idratazione per percorso**: invece di ricreare l'intero albero DOM, Svelte 5 "cammina" attraverso il DOM esistente, collegando i segnali reattivi ai nodi già presenti. Questo elimina il costo di ri-creazione degli elementi.
- **Nessun mismatch silenzioso**: se l'HTML generato dal server non corrisponde a quello che il client produrrebbe, Svelte emette un warning in modalità sviluppo. Questo aiuta a identificare bug dove lo stato server e client divergono.
- **Idratazione selettiva**: le pagine marcate con `export const csr = false` non vengono idratate affatto — rimangono HTML statico puro, con zero JavaScript inviato al client per quella pagina.

### Pattern di idratazione selettiva ("Islands")

Sebbene SvelteKit non implementi nativamente il pattern "islands" come Astro, è possibile ottenere un risultato simile combinando le opzioni di rendering per pagina con import dinamici:

```svelte
<!-- Componente che si idrata solo quando visibile -->
<script>
  import { onMount } from 'svelte';

  let contenitore = $state(null);
  let ComponenteDinamico = $state(null);

  onMount(() => {
    const observer = new IntersectionObserver(
      async ([entry]) => {
        if (entry.isIntersecting && !ComponenteDinamico) {
          const modulo = await import('./ComponentePesante.svelte');
          ComponenteDinamico = modulo.default;
          observer.disconnect();
        }
      },
      { rootMargin: '200px' }
    );

    if (contenitore) observer.observe(contenitore);

    return () => observer.disconnect();
  });
</script>

<div bind:this={contenitore}>
  {#if ComponenteDinamico}
    <ComponenteDinamico />
  {:else}
    <div class="placeholder">Caricamento...</div>
  {/if}
</div>
```

### Configurazione SSR/CSR per pagina

SvelteKit permette un controllo granulare sul rendering a livello di singola pagina o layout:

```javascript
// Pagina completamente statica (pre-renderizzata, nessun JS)
// src/routes/about/+page.ts
export const prerender = true;
export const csr = false;

// Pagina solo client-side (nessun SSR — utile per dashboard con window/localStorage)
// src/routes/dashboard/+page.ts
export const ssr = false;

// Pagina ibrida con SSR e idratazione (default)
// src/routes/blog/[slug]/+page.ts
export const ssr = true;
export const csr = true;

// Layout che applica il prerendering a tutte le sotto-route
// src/routes/(docs)/+layout.ts
export const prerender = true;
```

La combinazione `prerender = true` + `csr = false` produce pagine puramente statiche senza alcun JavaScript, ideali per contenuti come documentazione, landing page informative o pagine legali.

---

## Accessibilità in Svelte

### Warning del compilatore per l'accessibilità

Una delle caratteristiche distintive di Svelte è che il compilatore esegue **controlli di accessibilità a compile-time**. Questo significa che molti problemi vengono individuati prima ancora di avviare l'applicazione. I warning includono:

- **`a11y-alt-text`**: immagini senza attributo `alt`
- **`a11y-aria-attributes`**: attributi ARIA non validi o applicati a elementi che non li supportano
- **`a11y-click-events-have-key-events`**: elementi con `onclick` ma senza handler per tastiera (`onkeydown`, `onkeypress`)
- **`a11y-label-has-associated-control`**: etichette `<label>` non associate a un controllo form
- **`a11y-missing-content`**: heading (`<h1>`-`<h6>`) o anchor (`<a>`) senza contenuto testuale accessibile
- **`a11y-no-noninteractive-element-interactions`**: eventi interattivi su elementi non interattivi
- **`a11y-role-has-required-aria-props`**: ruoli ARIA senza le proprietà obbligatorie

```svelte
<!-- Il compilatore emette warning per ciascuno di questi problemi -->

<!-- Warning: a11y-alt-text -->
<img src="foto.jpg" />
<!-- Corretto: -->
<img src="foto.jpg" alt="Panorama montano al tramonto" />

<!-- Warning: a11y-click-events-have-key-events -->
<div onclick={gestisci}>Clicca qui</div>
<!-- Corretto: -->
<div onclick={gestisci} onkeydown={gestisci} role="button" tabindex="0">
  Clicca qui
</div>

<!-- Warning: a11y-no-noninteractive-element-interactions -->
<p onclick={apriDettagli}>Vedi dettagli</p>
<!-- Corretto: usare un elemento interattivo -->
<button onclick={apriDettagli}>Vedi dettagli</button>
```

### Navigazione accessibile con SvelteKit

SvelteKit gestisce automaticamente l'annuncio delle navigazioni per le tecnologie assistive. Quando l'utente naviga tra pagine senza ricaricamento completo (navigazione client-side), SvelteKit:

1. Inietta una **live region** ARIA nascosta che annuncia il titolo della nuova pagina allo screen reader.
2. Sposta il **focus** sull'elemento principale della nuova pagina dopo la navigazione.
3. Gestisce correttamente la **history del browser** per consentire la navigazione con il pulsante indietro.

Per personalizzare il comportamento:

```svelte
<!-- src/routes/+layout.svelte -->
<script>
  import { afterNavigate } from '$app/navigation';

  afterNavigate(() => {
    // Focus sull'heading principale dopo ogni navigazione
    const heading = document.querySelector('h1');
    if (heading) {
      heading.setAttribute('tabindex', '-1');
      heading.focus();
    }
  });
</script>
```

### Pattern per componenti accessibili

Creare componenti che rispettano le linee guida WCAG richiede attenzione a ruoli, stati e proprietà ARIA:

```svelte
<!-- Modale.svelte -->
<script>
  let { aperto = $bindable(false), titolo, children } = $props();
  let dialogo = $state(null);

  $effect(() => {
    if (aperto && dialogo) {
      dialogo.showModal();
      // Trap focus dentro il modale
      const primoFocusabile = dialogo.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      primoFocusabile?.focus();
    }
  });

  function chiudi() {
    aperto = false;
  }

  function gestisciTastiera(evento) {
    if (evento.key === 'Escape') {
      chiudi();
    }
  }
</script>

{#if aperto}
  <dialog
    bind:this={dialogo}
    onclose={chiudi}
    onkeydown={gestisciTastiera}
    aria-labelledby="modale-titolo"
    aria-modal="true"
  >
    <header>
      <h2 id="modale-titolo">{titolo}</h2>
      <button onclick={chiudi} aria-label="Chiudi finestra di dialogo">
        &times;
      </button>
    </header>
    <div class="contenuto-modale">
      {@render children()}
    </div>
  </dialog>
{/if}
```

### Rispetto della preferenza `prefers-reduced-motion`

Svelte permette di rispettare la preferenza dell'utente per il movimento ridotto sia a livello CSS che JavaScript:

```svelte
<script>
  import { fly, fade } from 'svelte/transition';

  // Hook custom per rilevare la preferenza
  let prefersReduced = $state(false);

  $effect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    prefersReduced = mq.matches;

    function aggiorna(e) {
      prefersReduced = e.matches;
    }
    mq.addEventListener('change', aggiorna);
    return () => mq.removeEventListener('change', aggiorna);
  });

  // Scegliere la transizione basandosi sulla preferenza
  function transizioneSicura(nodo, params) {
    if (prefersReduced) {
      return fade(nodo, { duration: 0 });
    }
    return fly(nodo, params);
  }
</script>

{#if visibile}
  <div transition:transizioneSicura={{ y: 50, duration: 300 }}>
    Contenuto con transizione accessibile
  </div>
{/if}

<style>
  /* A livello CSS, disabilitare le animazioni se richiesto */
  @media (prefers-reduced-motion: reduce) {
    :global(*) {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }
  }
</style>
```

### Testing dell'accessibilità

Combinare i warning del compilatore con strumenti di testing automatizzato per una copertura completa:

```javascript
// src/lib/components/Form.test.ts
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import { axe, toHaveNoViolations } from 'jest-axe';
import Form from './Form.svelte';

expect.extend(toHaveNoViolations);

describe('Form accessibilità', () => {
  it('non presenta violazioni axe', async () => {
    const { container } = render(Form, {
      props: { campi: ['nome', 'email'] }
    });
    const risultati = await axe(container);
    expect(risultati).toHaveNoViolations();
  });

  it('i campi hanno label associate', () => {
    const { getByLabelText } = render(Form, {
      props: { campi: ['nome', 'email'] }
    });
    expect(getByLabelText('Nome')).toBeTruthy();
    expect(getByLabelText('Email')).toBeTruthy();
  });

  it('gli errori sono annunciati con role=alert', async () => {
    const { getByRole, component } = render(Form);
    // Simulare errore di validazione
    await component.$set({ errori: { nome: 'Campo obbligatorio' } });
    const alert = getByRole('alert');
    expect(alert.textContent).toContain('Campo obbligatorio');
  });
});
```

---

## Pattern di Gestione dello Stato

### Stato locale: `$state` e `$derived`

Lo stato locale di un componente è il caso più semplice e comune. In Svelte 5, `$state` e `$derived` coprono la totalità dei bisogni:

```svelte
<script lang="ts">
  // Stato primitivo
  let filtro = $state('');
  let ordinamento = $state<'asc' | 'desc'>('asc');

  // Stato oggetto con reattività profonda
  let formDati = $state({
    nome: '',
    email: '',
    newsletter: false
  });

  // Stato derivato con logica complessa
  let elementiVisibili = $derived.by(() => {
    let risultato = tutti.filter(e =>
      e.nome.toLowerCase().includes(filtro.toLowerCase())
    );
    return ordinamento === 'asc'
      ? risultato.sort((a, b) => a.nome.localeCompare(b.nome))
      : risultato.sort((a, b) => b.nome.localeCompare(a.nome));
  });

  let sommario = $derived({
    totale: tutti.length,
    filtrati: elementiVisibili.length,
    percentuale: Math.round((elementiVisibili.length / tutti.length) * 100)
  });
</script>
```

### Stato condiviso con Context API

Il context di Svelte è il meccanismo per condividere stato tra un componente padre e i suoi discendenti senza prop drilling. Con Svelte 5, il context funziona perfettamente con le rune:

```typescript
// src/lib/context/tema.svelte.ts
import { setContext, getContext } from 'svelte';

const CHIAVE_TEMA = Symbol('tema');

export interface Tema {
  modo: 'chiaro' | 'scuro';
  primario: string;
  raggio: string;
}

export function impostaTema(temaIniziale: Tema) {
  let tema = $state(temaIniziale);

  const ctx = {
    get tema() { return tema; },
    aggiorna(parziale: Partial<Tema>) {
      tema = { ...tema, ...parziale };
    },
    toggleModo() {
      tema = { ...tema, modo: tema.modo === 'chiaro' ? 'scuro' : 'chiaro' };
    }
  };

  setContext(CHIAVE_TEMA, ctx);
  return ctx;
}

export function usaTema() {
  return getContext<ReturnType<typeof impostaTema>>(CHIAVE_TEMA);
}
```

```svelte
<!-- Layout.svelte (provider) -->
<script>
  import { impostaTema } from '$lib/context/tema.svelte.ts';

  impostaTema({
    modo: 'chiaro',
    primario: '#ff3e00',
    raggio: '8px'
  });
</script>

<slot />
```

```svelte
<!-- ComponenteFiglio.svelte (consumer) -->
<script>
  import { usaTema } from '$lib/context/tema.svelte.ts';

  const { tema, toggleModo } = usaTema();
</script>

<div class="contenitore" class:scuro={tema.modo === 'scuro'}>
  <button onclick={toggleModo}>
    Tema: {tema.modo}
  </button>
</div>
```

### Stato globale con file `.svelte.ts`

Per lo stato veramente globale (autenticazione, preferenze utente, carrello), i file `.svelte.ts` sono il pattern raccomandato in Svelte 5:

```typescript
// src/lib/state/autenticazione.svelte.ts

interface Utente {
  id: string;
  nome: string;
  email: string;
  ruolo: 'utente' | 'admin';
}

class StatoAutenticazione {
  utente = $state<Utente | null>(null);
  caricamento = $state(true);
  errore = $state<string | null>(null);

  isAutenticato = $derived(this.utente !== null);
  isAdmin = $derived(this.utente?.ruolo === 'admin');

  async login(email: string, password: string) {
    this.caricamento = true;
    this.errore = null;

    try {
      const risposta = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!risposta.ok) {
        const dati = await risposta.json();
        throw new Error(dati.messaggio || 'Credenziali non valide');
      }

      this.utente = await risposta.json();
    } catch (e) {
      this.errore = e instanceof Error ? e.message : 'Errore sconosciuto';
      throw e;
    } finally {
      this.caricamento = false;
    }
  }

  async logout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    this.utente = null;
  }

  async verificaSessione() {
    try {
      const risposta = await fetch('/api/auth/sessione');
      if (risposta.ok) {
        this.utente = await risposta.json();
      }
    } finally {
      this.caricamento = false;
    }
  }
}

export const auth = new StatoAutenticazione();
```

### Pattern di stato con azioni asincrone

Per gestire operazioni asincrone ripetitive (fetch, mutazioni), un pattern factory riduce la duplicazione:

```typescript
// src/lib/state/async.svelte.ts
export function creaStatoAsync<T>(valore_iniziale: T) {
  let dati = $state<T>(valore_iniziale);
  let caricamento = $state(false);
  let errore = $state<string | null>(null);

  async function esegui(operazione: () => Promise<T>) {
    caricamento = true;
    errore = null;
    try {
      dati = await operazione();
    } catch (e) {
      errore = e instanceof Error ? e.message : 'Errore';
      throw e;
    } finally {
      caricamento = false;
    }
  }

  return {
    get dati() { return dati; },
    get caricamento() { return caricamento; },
    get errore() { return errore; },
    esegui,
    resetta() {
      dati = valore_iniziale;
      errore = null;
    }
  };
}
```

```svelte
<script>
  import { creaStatoAsync } from '$lib/state/async.svelte.ts';

  const prodotti = creaStatoAsync([]);

  $effect(() => {
    prodotti.esegui(() =>
      fetch('/api/prodotti').then(r => r.json())
    );
  });
</script>

{#if prodotti.caricamento}
  <p>Caricamento...</p>
{:else if prodotti.errore}
  <p class="errore">{prodotti.errore}</p>
{:else}
  {#each prodotti.dati as prodotto}
    <div>{prodotto.nome}</div>
  {/each}
{/if}
```

---

## Svelte con TypeScript — Approfondimento

### Configurazione TypeScript in SvelteKit

SvelteKit supporta TypeScript nativamente. Il file `tsconfig.json` viene generato automaticamente e estende la configurazione di SvelteKit:

```json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "strict": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true
  }
}
```

Il file `src/app.d.ts` definisce i tipi globali dell'applicazione:

```typescript
// src/app.d.ts
declare global {
  namespace App {
    // Tipo dell'errore personalizzato
    interface Error {
      codice: string;
      messaggio: string;
    }

    // Dati disponibili in event.locals (hooks, load function server-side)
    interface Locals {
      utente: {
        id: string;
        nome: string;
        ruolo: 'utente' | 'admin';
      } | null;
      db: import('$lib/server/database').Database;
      requestId: string;
    }

    // Dati aggiuntivi per la pagina
    interface PageData {
      flash?: { tipo: 'successo' | 'errore'; messaggio: string };
    }

    // Stato della pagina
    interface PageState {
      modaleAperta?: boolean;
      scrollPosition?: number;
    }

    // Piattaforma (specifico dell'adapter)
    interface Platform {}
  }
}

export {};
```

### Tipizzazione delle Load Function

SvelteKit genera automaticamente i tipi per le load function basandosi sulla struttura del progetto. Il tipo generato `$types` fornisce type safety end-to-end:

```typescript
// src/routes/blog/[slug]/+page.server.ts
import type { PageServerLoad, Actions } from './$types';
import { fail, redirect, error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params, locals }) => {
  // params.slug è tipizzato come string grazie al nome della directory [slug]
  const articolo = await locals.db.articoli.findUnique({
    where: { slug: params.slug }
  });

  if (!articolo) {
    throw error(404, { codice: 'NOT_FOUND', messaggio: 'Articolo non trovato' });
  }

  // Il tipo di ritorno è inferito e disponibile nel componente
  return {
    articolo,
    commenti: locals.db.commenti.findMany({ where: { articoloId: articolo.id } })
  };
};

export const actions: Actions = {
  commenta: async ({ request, params, locals }) => {
    if (!locals.utente) {
      throw redirect(303, '/login');
    }

    const dati = await request.formData();
    const testo = dati.get('testo')?.toString();

    if (!testo || testo.length < 10) {
      return fail(400, {
        testo,
        errore: 'Il commento deve avere almeno 10 caratteri'
      });
    }

    await locals.db.commenti.create({
      data: {
        testo,
        articoloSlug: params.slug,
        autoreId: locals.utente.id
      }
    });

    return { successo: true };
  }
};
```

```svelte
<!-- src/routes/blog/[slug]/+page.svelte -->
<script lang="ts">
  import type { PageData, ActionData } from './$types';

  // I tipi sono automaticamente inferiti dalla load function
  let { data, form }: { data: PageData; form: ActionData } = $props();
  // data.articolo è tipizzato, data.commenti è tipizzato
</script>
```

### Componenti generici

Svelte 5 supporta i generics a livello di componente tramite l'attributo `generics` sul tag `<script>`:

```svelte
<!-- Seleziona.svelte -->
<script lang="ts" generics="T extends { id: string; etichetta: string }">
  let {
    opzioni,
    selezionato = $bindable(null),
    placeholder = 'Seleziona...',
    onSeleziona
  }: {
    opzioni: T[];
    selezionato?: T | null;
    placeholder?: string;
    onSeleziona?: (opzione: T) => void;
  } = $props();

  let aperto = $state(false);

  function seleziona(opzione: T) {
    selezionato = opzione;
    aperto = false;
    onSeleziona?.(opzione);
  }
</script>

<div class="seleziona">
  <button onclick={() => aperto = !aperto}>
    {selezionato?.etichetta ?? placeholder}
  </button>
  {#if aperto}
    <ul role="listbox">
      {#each opzioni as opzione (opzione.id)}
        <li
          role="option"
          aria-selected={selezionato?.id === opzione.id}
          onclick={() => seleziona(opzione)}
        >
          {opzione.etichetta}
        </li>
      {/each}
    </ul>
  {/if}
</div>
```

```svelte
<!-- Utilizzo — TypeScript inferisce T come Citta -->
<script lang="ts">
  import Seleziona from './Seleziona.svelte';

  interface Citta {
    id: string;
    etichetta: string;
    regione: string;
    popolazione: number;
  }

  const citta: Citta[] = [
    { id: '1', etichetta: 'Milano', regione: 'Lombardia', popolazione: 1396059 },
    { id: '2', etichetta: 'Roma', regione: 'Lazio', popolazione: 2761632 }
  ];

  let cittaSelezionata: Citta | null = $state(null);
</script>

<!-- T viene inferito come Citta, onSeleziona riceve Citta -->
<Seleziona
  opzioni={citta}
  bind:selezionato={cittaSelezionata}
  onSeleziona={(c) => console.log(c.regione)}
/>
```

### Utility types di Svelte

Svelte fornisce tipi utili per lavorare con componenti e snippet:

```typescript
import type {
  Snippet,           // Tipo per le prop snippet
  Component,         // Tipo per i componenti Svelte
  ComponentProps,    // Estrae le props di un componente
  ComponentEvents,   // Estrae gli eventi di un componente (legacy)
  EventHandler       // Tipo per handler di eventi DOM
} from 'svelte';

// Esempio: creare un componente wrapper tipizzato
type PropsBottone = ComponentProps<typeof import('./Bottone.svelte').default>;

// Esempio: snippet con parametri tipizzati
type RenderRiga = Snippet<[{ dato: string; indice: number }]>;

// Esempio: handler di eventi
let gestisciClick: EventHandler<MouseEvent, HTMLButtonElement>;
```

### Tipizzazione degli eventi nel template

In Svelte 5, gli handler di eventi nel template possono essere tipizzati nativamente senza cast manuali:

```svelte
<script lang="ts">
  function gestisciSubmit(evento: SubmitEvent) {
    evento.preventDefault();
    const formData = new FormData(evento.currentTarget as HTMLFormElement);
    const email = formData.get('email') as string;
    console.log('Email inviata:', email);
  }

  function gestisciInput(evento: Event & { currentTarget: HTMLInputElement }) {
    const valore = evento.currentTarget.value;
    console.log('Input cambiato:', valore);
  }

  // Handler tipizzato per eventi custom con delegazione
  function gestisciDelegato(evento: MouseEvent) {
    const target = evento.target as HTMLElement;
    const azione = target.closest('[data-azione]')?.getAttribute('data-azione');
    if (azione) {
      console.log('Azione:', azione);
    }
  }
</script>

<form onsubmit={gestisciSubmit}>
  <input name="email" type="email" oninput={gestisciInput} />
  <button type="submit">Invia</button>
</form>

<div onclick={gestisciDelegato}>
  <button data-azione="modifica">Modifica</button>
  <button data-azione="elimina">Elimina</button>
</div>
```

### Tipizzazione dei parametri di route

SvelteKit genera automaticamente i tipi dei parametri di route basandosi sulla struttura delle directory. Per vincolare ulteriormente i parametri, si usano i **param matchers**:

```typescript
// src/params/intero.ts
import type { ParamMatcher } from '@sveltejs/kit';

export const match: ParamMatcher = (param) => {
  return /^\d+$/.test(param);
};
```

```
src/routes/prodotti/[id=intero]/+page.svelte
```

In questo modo, la route `/prodotti/abc` restituirà un 404 automaticamente, mentre `/prodotti/123` funzionerà correttamente. Il parametro `id` nel tipo `Params` generato sarà ancora una stringa, ma il matcher garantisce a runtime che contenga solo cifre.

---

## Strategie di Deploy

### Panoramica degli Adapter

Gli adapter SvelteKit trasformano l'output della build in un formato adatto a una piattaforma di deploy specifica. La scelta dell'adapter dipende dall'infrastruttura di destinazione:

| Adapter | Piattaforma | SSR | SSG | Serverless |
|---|---|---|---|---|
| `adapter-auto` | Rileva automaticamente | Si | Si | Si |
| `adapter-node` | Server Node.js / Docker | Si | Si | No |
| `adapter-static` | Hosting statico | No | Si | No |
| `adapter-vercel` | Vercel | Si | Si | Si |
| `adapter-netlify` | Netlify | Si | Si | Si |
| `adapter-cloudflare` | Cloudflare Pages/Workers | Si | Si | Si |

### Deploy con adapter-node e Docker

Per ambienti self-hosted, `adapter-node` produce un server Node.js standalone:

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-node';

export default {
  kit: {
    adapter: adapter({
      out: 'build',
      precompress: true, // Genera file .gz e .br
      envPrefix: 'APP_'  // Prefisso per variabili d'ambiente
    })
  }
};
```

Dockerfile per il deploy containerizzato:

```dockerfile
# Fase di build
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
RUN npm prune --production

# Fase di produzione
FROM node:22-alpine
WORKDIR /app
COPY --from=builder /app/build ./build
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

ENV NODE_ENV=production
ENV PORT=3000
ENV ORIGIN=https://miosito.it

EXPOSE 3000
USER node
CMD ["node", "build"]
```

Le variabili d'ambiente critiche per `adapter-node` in produzione sono:

```bash
PORT=3000            # Porta del server (default: 3000)
HOST=0.0.0.0         # Indirizzo di bind (default: 0.0.0.0)
ORIGIN=https://miosito.it  # URL di origine per CSRF protection
BODY_SIZE_LIMIT=512K # Limite dimensione body delle richieste
```

### Deploy su Vercel

Vercel offre un'integrazione zero-configuration con SvelteKit:

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-vercel';

export default {
  kit: {
    adapter: adapter({
      runtime: 'nodejs22.x',
      regions: ['fra1'],      // Frankfurt per utenti europei
      split: true,            // Ogni route diventa una funzione separata
      isr: {
        expiration: 60        // Incremental Static Regeneration
      }
    })
  }
};
```

### Deploy su Cloudflare

Cloudflare Pages con Workers offre esecuzione edge a latenza minima:

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-cloudflare';

export default {
  kit: {
    adapter: adapter({
      routes: {
        include: ['/*'],
        exclude: ['<all>']    // Esclude file statici automaticamente
      },
      platformProxy: {
        configPath: 'wrangler.toml'
      }
    })
  }
};
```

Per accedere ai binding di Cloudflare (D1, KV, R2) nelle load function e negli hook:

```typescript
// src/hooks.server.ts
export async function handle({ event, resolve }) {
  // I binding Cloudflare sono disponibili tramite event.platform
  const db = event.platform?.env?.DB;       // Cloudflare D1
  const kv = event.platform?.env?.CACHE;    // Cloudflare KV
  const bucket = event.platform?.env?.FILES; // Cloudflare R2

  if (db) {
    event.locals.db = db;
  }

  return resolve(event);
}
```

### Deploy statico

Per siti completamente statici (documentazione, blog, portfolio):

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: '404.html',   // Pagina di fallback per SPA
      precompress: true,       // File .gz e .br pre-compressi
      strict: true             // Errore se una pagina non è pre-renderizzabile
    }),
    prerender: {
      entries: ['*'],          // Pre-renderizza tutte le pagine
      handleHttpError: 'warn'  // Non bloccare la build per errori HTTP
    }
  }
};
```

### Variabili d'ambiente nei deploy

SvelteKit gestisce le variabili d'ambiente con moduli dedicati e separazione chiara tra server e client:

```typescript
// Solo server — mai esposti al client
import { DATABASE_URL, JWT_SECRET } from '$env/static/private';
// Usabile in: +page.server.ts, +server.ts, hooks.server.ts

// Variabili pubbliche — incluse nel bundle client
import { PUBLIC_API_BASE, PUBLIC_APP_NOME } from '$env/static/public';
// Usabile ovunque

// Variabili dinamiche (lette a runtime, non inline nella build)
import { env } from '$env/dynamic/private';
const url = env.DATABASE_URL; // Letto a runtime

import { env as envPubblico } from '$env/dynamic/public';
const apiBase = envPubblico.PUBLIC_API_BASE;
```

La distinzione tra `static` e `dynamic` ha implicazioni sulle prestazioni: le variabili `static` vengono sostituite a build-time (inline nel codice), mentre quelle `dynamic` vengono lette dall'ambiente a runtime. Preferire `static` quando i valori non cambiano tra build e deploy.

---

## Ottimizzazione delle Prestazioni

### Bundle Analysis e Code Splitting

SvelteKit implementa il code splitting automaticamente: ogni pagina e le sue dipendenze vengono raggruppate in chunk separati. Per analizzare la composizione del bundle:

```bash
# Installare il visualizzatore
npm install -D rollup-plugin-visualizer
```

```javascript
// vite.config.js
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    sveltekit(),
    visualizer({
      emitFile: true,
      filename: 'stats.html',
      gzipSize: true
    })
  ]
});
```

Per ottimizzare il bundle, evitare import di librerie pesanti a livello globale. Usare import dinamici per le dipendenze che servono solo in specifiche route:

```svelte
<script>
  let ChartComponent = $state(null);

  async function caricaGrafico() {
    const modulo = await import('$lib/components/Grafico.svelte');
    ChartComponent = modulo.default;
  }
</script>

<button onclick={caricaGrafico}>Mostra Grafico</button>

{#if ChartComponent}
  <ChartComponent dati={datiVendite} />
{/if}
```

### Lazy Loading dei componenti

Il lazy loading differito per visibilità è un pattern potente per pagine con molto contenuto below-the-fold:

```svelte
<!-- LazyLoad.svelte -->
<script>
  let { loader, fallback } = $props();
  let contenitore;
  let Componente = $state(null);
  let caricamento = $state(false);

  $effect(() => {
    if (!contenitore) return;

    const observer = new IntersectionObserver(
      async ([entry]) => {
        if (entry.isIntersecting && !Componente && !caricamento) {
          caricamento = true;
          try {
            const modulo = await loader();
            Componente = modulo.default;
          } finally {
            caricamento = false;
          }
          observer.disconnect();
        }
      },
      { rootMargin: '100px' }
    );

    observer.observe(contenitore);
    return () => observer.disconnect();
  });
</script>

<div bind:this={contenitore}>
  {#if Componente}
    <Componente />
  {:else if caricamento}
    <div class="skeleton" aria-busy="true">Caricamento...</div>
  {:else if fallback}
    {@render fallback()}
  {/if}
</div>
```

```svelte
<!-- Utilizzo -->
<LazyLoad loader={() => import('./MappaInterattiva.svelte')}>
  {#snippet fallback()}
    <div class="placeholder-mappa">Scorri per caricare la mappa</div>
  {/snippet}
</LazyLoad>
```

### Ottimizzazione della reattività

Svelte 5 ha prestazioni reattive eccellenti grazie ai segnali, ma alcune pratiche possono degradarle:

```svelte
<script>
  // EVITARE: $state per dati grandi e immutabili
  // Il proxy profondo ha un costo per strutture molto grandi
  let milleElementi = $state(arrayEnorme); // Proxy ricorsivo!

  // PREFERIRE: $state.raw per dati che cambiano per sostituzione
  let milleElementi = $state.raw(arrayEnorme); // Nessun proxy

  // Aggiornamento tramite sostituzione completa
  function aggiorna(id, nuoviDati) {
    milleElementi = milleElementi.map(e =>
      e.id === id ? { ...e, ...nuoviDati } : e
    );
  }
</script>
```

```svelte
<script>
  // EVITARE: effetti che leggono e scrivono le stesse dipendenze
  let conteggio = $state(0);
  $effect(() => {
    // Loop infinito: legge e scrive conteggio
    conteggio = conteggio + 1; // MAI FARE QUESTO
  });

  // EVITARE: $derived per operazioni costose senza memoizzazione
  // $derived ricalcola a ogni lettura delle dipendenze
  let risultatoCostoso = $derived(calcoloPesante(dati));

  // PREFERIRE: memoizzazione manuale per calcoli pesanti
  let risultatoCache = $state(null);
  let ultimiDati = $state(null);

  let risultato = $derived.by(() => {
    if (dati === ultimiDati && risultatoCache) return risultatoCache;
    ultimiDati = dati;
    risultatoCache = calcoloPesante(dati);
    return risultatoCache;
  });
</script>
```

### Precaricamento delle pagine

SvelteKit offre il precaricamento delle pagine per rendere la navigazione istantanea:

```svelte
<!-- Precaricamento al hover del link -->
<a href="/blog/articolo-1" data-sveltekit-preload-data="hover">
  Leggi l'articolo
</a>

<!-- Precaricamento al tap (mobile) -->
<a href="/blog/articolo-2" data-sveltekit-preload-data="tap">
  Leggi l'articolo
</a>

<!-- Precaricamento programmmatico -->
<script>
  import { preloadData, preloadCode } from '$app/navigation';

  async function precarica(href) {
    // Precarica sia il codice che i dati della pagina
    await preloadData(href);
  }

  function precaricaCodice(href) {
    // Precarica solo il codice JavaScript (senza eseguire load)
    preloadCode(href);
  }
</script>
```

### Ottimizzazione delle immagini

Le immagini sono spesso la parte più pesante di una pagina web. SvelteKit integra `@sveltejs/enhanced-img` per l'ottimizzazione automatica:

```bash
npm install -D @sveltejs/enhanced-img
```

```javascript
// vite.config.js
import { sveltekit } from '@sveltejs/kit/vite';
import { enhancedImages } from '@sveltejs/enhanced-img';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    enhancedImages(),
    sveltekit()
  ]
});
```

```svelte
<!-- Utilizzo con ottimizzazione automatica -->
<script>
  import fotoCopertina from '$lib/assets/copertina.jpg?enhanced';
</script>

<!-- Genera automaticamente srcset con formati AVIF e WebP -->
<enhanced:img
  src={fotoCopertina}
  alt="Copertina dell'articolo"
  loading="lazy"
  sizes="(max-width: 768px) 100vw, 50vw"
/>
```

### Checklist delle prestazioni

Prima del deploy in produzione, verificare:

- [ ] Ogni route ha solo le dipendenze necessarie (nessun import inutile)
- [ ] Le librerie pesanti usano import dinamici
- [ ] Le immagini hanno dimensioni esplicite (`width`/`height`) e `loading="lazy"` per below-the-fold
- [ ] Le pagine statiche sono marcate con `prerender = true`
- [ ] I dati non critici usano streaming (promise non await-ate nelle load function)
- [ ] `$state.raw()` è usato per dati grandi e immutabili
- [ ] Il precaricamento è attivo sui link principali con `data-sveltekit-preload-data`
- [ ] Il CSS è scoped per componente (evitare `:global` non necessari)
- [ ] I font sono precaricati con `<link rel="preload">`
- [ ] Il bundle è analizzato con un visualizzatore e non supera 150 KB (gzip) per la landing page

---

## Esercizi

### Esercizio 1 — Componenti e Runes in Svelte 5

**Obiettivo:** costruire componenti Svelte 5 usando le runes per la reattivita e comprendere il modello di compilazione.

Creare un set di componenti per un sistema di voto:

- Un componente `PollCard` con props dichiarate tramite `$props()`: `question: string`, `options: string[]`, `multiSelect?: boolean`
- Gestire lo stato locale con `$state` per i voti e `$derived` per il calcolo delle percentuali
- Un componente `PollResults` che mostra i risultati con barre di progresso animate tramite transizioni Svelte (`transition:slide`)
- Usare `$effect` per salvare i voti in `localStorage` e ripristinarli al mount
- Implementare un binding bidirezionale con `bind:` per un campo di testo che aggiunge opzioni dinamicamente
- Scrivere test con Vitest e `@testing-library/svelte` per il rendering e le interazioni
- Verificare che il bundle compilato non contenga alcun runtime framework (solo codice imperativo)

### Esercizio 2 — Reattivita Avanzata e Store

**Obiettivo:** padroneggiare il sistema reattivo di Svelte 5 e la creazione di store personalizzati.

Implementare un'applicazione timer/cronometro con reattivita avanzata:

- Creare uno store `timerStore` usando `$state` in un modulo `.svelte.ts` con metodi `start`, `pause`, `reset` e `lap`
- Usare `$derived` per calcolare minuti, secondi e millisecondi dal tempo totale
- Implementare `$effect` con cleanup per gestire `setInterval` senza memory leak
- Creare un componente `TimerDisplay` che mostri il tempo con formattazione automatica
- Implementare una lista di giri (lap) con `$state` array e transizioni animate per ogni nuovo giro
- Creare un composable `createStopwatch()` che ritorni stato e metodi, riutilizzabile in piu componenti
- Test unitari per la logica dello store e test di integrazione per il componente completo

### Esercizio 3 — Form Actions e Validazione con SvelteKit

**Obiettivo:** implementare form server-side con SvelteKit usando form actions, validazione e progressive enhancement.

Creare un sistema di registrazione utente con SvelteKit:

- Implementare una pagina `/registrazione` con form che usa `<form method="POST">`
- Definire form actions nel file `+page.server.ts`: `default` per la registrazione, `login` come named action
- Validare i dati del form lato server con Zod: email, password (min 8 char, maiuscola, numero), conferma password
- Restituire errori di validazione strutturati con `fail(400, { errors })` e mostrarli nel componente
- Il form deve funzionare senza JavaScript (progressive enhancement)
- Usare `use:enhance` per migliorare l'esperienza con JavaScript abilitato (loading state, errori inline)
- Implementare protezione CSRF e rate limiting sull'endpoint
- Test E2E con Playwright: invio form valido, validazione errori, funzionamento senza JS

### Esercizio 4 — Routing e Layout con SvelteKit

**Obiettivo:** costruire un'applicazione multi-pagina con il routing basato su file system di SvelteKit.

Creare un portale di documentazione con SvelteKit:

- Struttura route: `/` (home), `/docs/[categoria]/[slug]` (articolo), `/ricerca` (ricerca full-text), `/admin` (protetta)
- Implementare layout annidati: `+layout.svelte` con sidebar di navigazione persistente e `+layout.ts` per caricare i dati della sidebar
- Usare `+page.ts` con `load` function per caricare i dati di ogni pagina
- Implementare SSG con `export const prerender = true` per le pagine di documentazione
- Creare un hook `handle` in `hooks.server.ts` per l'autenticazione delle route protette
- Gestire errori con `+error.svelte` personalizzato a livello di layout
- Implementare breadcrumb dinamiche derivate dalla struttura delle route
- Usare `$page` store per evidenziare la voce attiva nella navigazione
- Test E2E per la navigazione, il rendering delle pagine e la protezione delle route

### Esercizio 5 — Applicazione Full-Stack con SvelteKit e Database

**Obiettivo:** costruire un'applicazione completa con SvelteKit, integrando database, autenticazione e deploy.

Creare un'applicazione di gestione spese personali:

- Pagine: dashboard con riepilogo mensile, lista transazioni con filtri, aggiunta/modifica transazione, impostazioni
- Backend: API endpoints in `+server.ts` e form actions per le mutazioni
- Database: Prisma o Drizzle ORM con SQLite per lo sviluppo, PostgreSQL per la produzione
- Autenticazione: sessioni basate su cookie httpOnly con `hooks.server.ts`
- Usare `$state` e `$derived` per lo stato locale, store condivisi per le preferenze utente
- Implementare grafici con una libreria leggera (es. Chart.js o LayerCake)
- Ottimizzare con `load` function che caricano dati in parallelo dove possibile
- Gestire variabili d'ambiente con `$env/static/private` e `$env/static/public`
- Test unitari per la logica business, test di integrazione per le API, test E2E per i flussi utente
- Configurare il deploy con un adapter (Node, Vercel o Netlify)

---

## Letture e Riferimenti

### Documentazione ufficiale

- **Svelte Documentation** — guida ufficiale al linguaggio, componenti e API. https://svelte.dev/docs/svelte (consultato: 2026-05-24)
- **SvelteKit Documentation** — framework full-stack: routing, SSR, form actions, adapter. https://svelte.dev/docs/kit (consultato: 2026-05-24)
- **Svelte Tutorial Interattivo** — tutorial passo-passo con editor integrato nel browser. https://learn.svelte.dev/ (consultato: 2026-05-24)
- **Svelte Playground** — ambiente online per sperimentare con componenti Svelte e visualizzare il codice compilato. https://svelte.dev/playground (consultato: 2026-05-24)
- **Svelte 5 Runes RFC** — specifica delle runes introdotte in Svelte 5. https://svelte.dev/blog/runes (consultato: 2026-05-24)
- **Svelte Society** — comunita, pacchetti e risorse dell'ecosistema Svelte. https://sveltesociety.dev/ (consultato: 2026-05-24)

### Libri e approfondimenti

- Harris R., *Rethinking Reactivity* — talk fondativo sull'approccio a compilazione di Svelte. https://www.youtube.com/watch?v=AdNJ3fydeao
- Volkov M., *Svelte and SvelteKit in Action*, Manning Publications, 2024.
- Documentazione Svelte — *Svelte FAQ* — risposte alle domande frequenti e confronti con altri framework. https://svelte.dev/faq

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [06 — TypeScript](06-typescript.md) | Prerequisito: Svelte 5 supporta nativamente TypeScript in `<script lang="ts">` e nei file `.svelte.ts` |
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Basi del linguaggio necessarie per comprendere la reattivita, i proxy e le closure usate dal compilatore Svelte |
| [07 — React](07-react.md) | Framework alternativo con virtual DOM: confronto architetturale tra compilazione (Svelte) e runtime (React) |
| [08 — Vue.js](08-vue.md) | Framework alternativo con reattivita basata su Proxy: confronto tra i modelli reattivi di Vue e Svelte |
| [15 — Testing Web](15-testing-web.md) | Strategie di testing per componenti Svelte: unit con Vitest, integrazione con Testing Library, E2E con Playwright |
| [16 — Build Tools e Deploy](16-build-tools-e-deploy.md) | Compilazione Svelte con Vite, configurazione degli adapter SvelteKit e pipeline di deploy |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Rune** | Primitiva reattiva introdotta in Svelte 5 (es. `$state`, `$derived`, `$effect`) che sostituisce le dichiarazioni reattive `$:` delle versioni precedenti. |
| **`$state`** | Rune che dichiara una variabile reattiva il cui valore viene tracciato dal compilatore e provoca aggiornamenti automatici del DOM quando cambia. |
| **`$derived`** | Rune che definisce un valore derivato calcolato automaticamente quando le sue dipendenze reattive cambiano, equivalente a una computed property. |
| **`$effect`** | Rune che esegue effetti collaterali in risposta a cambiamenti di stato reattivo, con supporto per funzioni di cleanup restituite. |
| **`$props`** | Rune che dichiara le props ricevute da un componente, sostituendo `export let` delle versioni precedenti e supportando la destrutturazione con valori di default. |
| **Compilazione** | Modello architetturale di Svelte: il codice sorgente viene trasformato a build-time in codice JavaScript imperativo che manipola direttamente il DOM, senza runtime framework. |
| **SvelteKit** | Framework full-stack costruito su Svelte che fornisce routing basato su file system, SSR, SSG, form actions, hooks server-side e adapter per il deploy. |
| **Form Action** | Funzione server-side definita in `+page.server.ts` che gestisce l'invio di form HTML, supportando progressive enhancement senza JavaScript obbligatorio. |
| **Load Function** | Funzione esportata da `+page.ts` o `+page.server.ts` che carica i dati necessari a una pagina prima del rendering, eseguita sia lato server che lato client. |
| **Adapter** | Modulo SvelteKit che adatta l'output della build a una piattaforma di deploy specifica (Node.js, Vercel, Netlify, Cloudflare, static). |
| **Transizione** | Animazione dichiarativa applicata con la direttiva `transition:` (es. `transition:fade`, `transition:slide`) che Svelte compila in codice di animazione ottimizzato. |
| **Binding** | Direttiva `bind:` che crea un collegamento bidirezionale tra una proprieta del DOM (es. `bind:value`) e una variabile reattiva nel componente. |
| **Progressive Enhancement** | Approccio in cui il form funziona con HTML standard senza JavaScript, e `use:enhance` aggiunge miglioramenti (loading state, validazione inline) quando JS e disponibile. |
| **Slot** | Meccanismo per passare contenuto dal componente genitore al figlio; in Svelte 5 sostituito da `{@render children()}` e snippet. |
| **Hook** | Funzione server-side in `hooks.server.ts` che intercetta ogni richiesta prima del routing, usata per autenticazione, logging e manipolazione della risposta. |
