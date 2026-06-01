---
corso: "Sviluppo Web"
fase: "3 — Framework Frontend"
modulo: "08"
titolo: "Vue.js"
versione: "Vue 3.5"
livello: "Intermedio"
prerequisiti:
  - "04 — JavaScript Fondamenti"
  - "06 — TypeScript"
obiettivi:
  - "Costruire applicazioni con Composition API e script setup"
  - "Gestire stato reattivo con ref, reactive e computed"
  - "Utilizzare Pinia per state management"
  - "Implementare routing con Vue Router"
  - "Creare componenti riutilizzabili con props, emit e slots"
  - "Testare componenti con Vue Test Utils e Vitest"
tag: [Vue, Composition-API, Pinia, Vue-Router, reattivita, Vitest]
---

# Vue.js — Guida Completa

> **Modulo 08** · **Aggiornamento:** 2026-05-24 · **Versione:** Vue 3.5

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [JavaScript Fondamenti](04-javascript-fondamenti.md), [TypeScript](06-typescript.md)
>
> Al termine di questo modulo saprai:
> 1. Costruire applicazioni con Composition API e `<script setup>`
> 2. Gestire stato reattivo con ref, reactive e computed
> 3. Utilizzare Pinia per state management
> 4. Implementare routing con Vue Router
> 5. Creare componenti riutilizzabili con props, emit e slots
> 6. Testare componenti con Vue Test Utils e Vitest
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio

## Idee guida
1. **Composition API > Options API.** Better TS support.
2. **`<script setup>` syntactic sugar standard.**
3. **Pinia > Vuex per state.** Pinia e ufficiale Vue 3.
4. **Nuxt 3 per SSR/SSG.**


## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti](#fondamenti)
3. [Composition API](#composition-api)
4. [State Management](#state-management)
5. [Routing](#routing)
6. [Forms](#forms)
7. [Ecosistema](#ecosistema)
8. [Best Practices](#best-practices)

---

## Panoramica

Vue.js è un framework JavaScript progressivo per la costruzione di interfacce utente, creato da Evan You nel 2014. La parola "progressivo" descrive la filosofia fondamentale di Vue: il framework può essere adottato incrementalmente, partendo da una semplice libreria per rendere reattive porzioni di una pagina fino a diventare un framework completo per applicazioni single-page di grande complessità. Questa flessibilità, unita a una curva di apprendimento graduale e a una documentazione di altissima qualità, ha reso Vue uno dei tre framework front-end più adottati al mondo, accanto a React e Angular.

### Vue 3 e la sua architettura

Vue 3, rilasciato nel settembre 2020 e diventato la versione ufficiale predefinita nel febbraio 2022, rappresenta una riscrittura quasi totale del framework. Il core è stato riscritto in TypeScript, garantendo un supporto nativo eccellente per la tipizzazione statica. Il sistema di reattività è stato completamente riprogettato utilizzando i Proxy ES6 al posto di `Object.defineProperty`, risolvendo le limitazioni storiche di Vue 2 nell'intercettare l'aggiunta e la cancellazione di proprietà degli oggetti e le modifiche agli array tramite indice.

L'architettura interna di Vue 3 è modulare: il compilatore dei template, il sistema di reattività, il renderer e il runtime sono pacchetti separati. Questa modularità consente il tree-shaking — le funzionalità non utilizzate vengono eliminate automaticamente dal bundle di produzione, riducendo significativamente la dimensione del codice distribuito. Un'applicazione Vue 3 minimale può pesare meno di 10 KB gzippati.

### Composition API vs Options API

Vue 3 offre due paradigmi per scrivere la logica dei componenti: la **Options API** e la **Composition API**.

**Options API.** È l'approccio originale di Vue, presente fin dalla versione 1. La logica del componente è organizzata in opzioni predefinite — `data`, `computed`, `methods`, `watch`, `mounted` e così via. Ogni opzione raccoglie un tipo specifico di logica. Questo approccio è intuitivo per chi inizia e funziona bene per componenti semplici.

```vue
<script>
export default {
  data() {
    return {
      contatore: 0,
      nome: "Mario"
    };
  },
  computed: {
    messaggio() {
      return `${this.nome} ha cliccato ${this.contatore} volte`;
    }
  },
  methods: {
    incrementa() {
      this.contatore++;
    }
  },
  mounted() {
    console.log("Componente montato");
  }
};
</script>
```

Il problema dell'Options API emerge con componenti complessi: la logica relativa a una singola funzionalità viene frammentata tra `data`, `computed`, `methods` e `watch`, rendendo difficile seguire il flusso logico e riutilizzare codice tra componenti.

**Composition API.** Introdotta in Vue 3, la Composition API permette di organizzare la logica per funzionalità anziché per tipo di opzione. Tutto il codice reattivo viene scritto all'interno della funzione `setup()` o, più comunemente, all'interno di un blocco `<script setup>`. Le funzionalità correlate restano vicine nel codice e possono essere estratte in funzioni riutilizzabili chiamate **composables**.

```vue
<script setup>
import { ref, computed, onMounted } from "vue";

const contatore = ref(0);
const nome = ref("Mario");

const messaggio = computed(() => `${nome.value} ha cliccato ${contatore.value} volte`);

function incrementa() {
  contatore.value++;
}

onMounted(() => {
  console.log("Componente montato");
});
</script>
```

La Composition API con `<script setup>` è l'approccio raccomandato per Vue 3. Offre migliore type inference con TypeScript, supporto nativo per il tree-shaking, codice più conciso e la possibilità di estrarre e riutilizzare logica complessa tramite composables. L'Options API resta disponibile e pienamente supportata, ma i nuovi progetti dovrebbero adottare la Composition API come standard.

### Panoramica dell'ecosistema

L'ecosistema Vue è curato e coeso. A differenza dell'ecosistema React, dove ogni libreria è indipendente, molti strumenti chiave di Vue sono mantenuti dal core team. **Vue Router** è il router ufficiale, integrato profondamente con il sistema di reattività. **Pinia** è lo state manager ufficiale, successore di Vuex. **Nuxt.js** è il meta-framework per SSR, SSG e applicazioni full-stack — l'equivalente di Next.js per React. **Vite** è il build tool creato dallo stesso Evan You, oggi adottato anche da React, Svelte e altri framework. Per i componenti UI, **Vuetify** e **PrimeVue** sono le librerie più consolidate. Per il testing, **Vitest** e **Vue Test Utils** formano la combinazione standard.

### Avviare un progetto Vue 3

Il modo raccomandato per creare un nuovo progetto Vue 3 è tramite `create-vue`, lo scaffolding ufficiale basato su Vite.

```bash
npm create vue@latest mio-progetto
```

Il comando interattivo permette di selezionare TypeScript, Vue Router, Pinia, Vitest, ESLint e Prettier. La struttura generata segue le convenzioni ufficiali con `src/components/`, `src/views/`, `src/stores/` e `src/router/`.

---

## Fondamenti

### Template Syntax

Vue utilizza un sistema di template basato su HTML che permette di legare dichiarativamente il DOM renderizzato ai dati del componente. I template Vue sono HTML valido che viene compilato in funzioni di rendering JavaScript ottimizzate. Il compilatore analizza staticamente i template per identificare le parti dinamiche e le parti statiche, applicando ottimizzazioni come lo static hoisting — i nodi statici vengono creati una sola volta e riutilizzati ad ogni re-render.

**Interpolazione di testo.** La forma più elementare di binding è l'interpolazione di testo tramite la sintassi "Mustache" con doppie parentesi graffe. Il contenuto viene trattato come testo puro — l'HTML viene automaticamente escapato per prevenire attacchi XSS.

```vue
<template>
  <h1>Benvenuto, {{ nomeUtente }}</h1>
  <p>Il totale è: {{ prezzo * quantita }} EUR</p>
  <p>{{ messaggio.split("").reverse().join("") }}</p>
</template>
```

**Binding di attributi con `v-bind`.** Per legare dinamicamente un attributo HTML ai dati del componente si usa la direttiva `v-bind`, abbreviabile con il prefisso `:`. Questo è fondamentale per attributi come `src`, `href`, `class`, `style`, `disabled` e qualsiasi attributo personalizzato.

```vue
<template>
  <img :src="urlImmagine" :alt="descrizione" />
  <a :href="linkProfilo">Profilo utente</a>
  <button :disabled="isCaricamento">Invia</button>

  <!-- Binding di classi con oggetto -->
  <div :class="{ attivo: isAttivo, errore: hasErrore }">Contenuto</div>

  <!-- Binding di classi con array -->
  <div :class="[classeBase, isAttivo ? 'attivo' : '']">Contenuto</div>

  <!-- Binding di stili inline -->
  <div :style="{ color: coloreTestuale, fontSize: dimensioneFont + 'px' }">Testo</div>
</template>
```

### Direttive

Le direttive sono attributi speciali prefissati con `v-` che applicano comportamento reattivo al DOM. Vue fornisce un insieme di direttive built-in per i pattern più comuni.

**`v-if`, `v-else-if`, `v-else` — Rendering condizionale.** Queste direttive controllano se un elemento viene effettivamente creato e inserito nel DOM. Quando la condizione è falsa, l'elemento e tutti i suoi figli vengono completamente rimossi dal DOM — non semplicemente nascosti. Questo comportamento è chiamato "lazy": il blocco condizionale non viene renderizzato finché la condizione non diventa vera per la prima volta.

```vue
<template>
  <div v-if="statoCaricamento === 'loading'">
    <SpinnerCaricamento />
  </div>
  <div v-else-if="statoCaricamento === 'error'">
    <p>Si è verificato un errore: {{ messaggioErrore }}</p>
  </div>
  <div v-else>
    <ul>
      <li v-for="elemento in lista" :key="elemento.id">
        {{ elemento.nome }}
      </li>
    </ul>
  </div>
</template>
```

**`v-show` — Visibilità tramite CSS.** A differenza di `v-if`, `v-show` mantiene sempre l'elemento nel DOM e ne controlla la visibilità tramite la proprietà CSS `display`. Preferisci `v-show` quando l'elemento cambia visibilità frequentemente (toggle), poiché evita il costo di creazione e distruzione del DOM. Preferisci `v-if` quando la condizione cambia raramente o quando il blocco condizionale è pesante.

```vue
<template>
  <div v-show="isPannelloAperto">
    <p>Contenuto del pannello laterale</p>
  </div>
</template>
```

**`v-for` — Rendering di liste.** La direttiva `v-for` itera su array, oggetti o range numerici. L'attributo `:key` è obbligatorio e deve essere un valore unico e stabile — tipicamente un ID dal database. L'uso dell'indice come chiave è sconsigliato quando la lista può essere riordinata o filtrata.

```vue
<template>
  <!-- Iterazione su array -->
  <ul>
    <li v-for="prodotto in prodotti" :key="prodotto.id">
      {{ prodotto.nome }} — {{ prodotto.prezzo }} EUR
    </li>
  </ul>

  <!-- Iterazione con indice -->
  <div v-for="(elemento, indice) in elementi" :key="elemento.id">
    {{ indice + 1 }}. {{ elemento.titolo }}
  </div>

  <!-- Iterazione su oggetto -->
  <div v-for="(valore, chiave) in oggetto" :key="chiave">
    {{ chiave }}: {{ valore }}
  </div>

  <!-- Range numerico -->
  <span v-for="n in 10" :key="n">{{ n }}</span>
</template>
```

**Attenzione:** non usare `v-if` e `v-for` sullo stesso elemento. Quando coesistono, `v-if` ha priorità maggiore e non ha accesso alle variabili di `v-for`. La soluzione è avvolgere `v-for` in un `<template>` oppure filtrare l'array tramite una computed property.

**`v-on` — Gestione degli eventi.** La direttiva `v-on`, abbreviabile con `@`, lega un listener a un evento DOM. Supporta eventi nativi del browser e eventi personalizzati dei componenti figli. I modificatori evitano la necessità di chiamare manualmente `event.preventDefault()` o `event.stopPropagation()`.

```vue
<template>
  <!-- Sintassi completa e abbreviata -->
  <button v-on:click="gestisciClick">Clicca</button>
  <button @click="gestisciClick">Clicca</button>

  <!-- Espressioni inline -->
  <button @click="contatore++">Incrementa</button>

  <!-- Accesso all'evento nativo -->
  <input @input="gestisciInput($event)" />

  <!-- Modificatori di evento -->
  <form @submit.prevent="inviaForm">...</form>
  <a @click.stop="gestisciClick">Link</a>
  <input @keyup.enter="cerca" />
  <button @click.once="inizializza">Solo una volta</button>

  <!-- Modificatori combinati -->
  <div @click.stop.prevent="gestisci">...</div>
</template>
```

**`v-model` — Two-way data binding.** La direttiva `v-model` crea un binding bidirezionale tra un input del form e un dato reattivo. È zucchero sintattico che combina un binding del valore e un listener per l'evento di aggiornamento. Funziona con `<input>`, `<textarea>`, `<select>` e i componenti personalizzati.

```vue
<script setup>
import { ref } from "vue";

const nome = ref("");
const accettato = ref(false);
const linguaggio = ref("javascript");
const competenze = ref([]);
</script>

<template>
  <input v-model="nome" placeholder="Il tuo nome" />
  <textarea v-model="nome"></textarea>

  <input type="checkbox" v-model="accettato" />

  <select v-model="linguaggio">
    <option value="javascript">JavaScript</option>
    <option value="typescript">TypeScript</option>
    <option value="python">Python</option>
  </select>

  <!-- Checkbox multipli con array -->
  <input type="checkbox" v-model="competenze" value="vue" />
  <input type="checkbox" v-model="competenze" value="react" />
  <input type="checkbox" v-model="competenze" value="angular" />

  <!-- Modificatori -->
  <input v-model.trim="nome" />         <!-- Rimuove spazi iniziali e finali -->
  <input v-model.number="eta" />         <!-- Converte a numero -->
  <input v-model.lazy="cerca" />         <!-- Sincronizza al change, non all'input -->
</template>
```

### Reattività

Il sistema di reattività è il cuore di Vue. In Vue 3, la reattività è basata sui Proxy ES6, che permettono di intercettare in modo trasparente lettura e scrittura delle proprietà di un oggetto. Quando un dato reattivo viene letto all'interno di un effetto (rendering del template, computed, watcher), Vue registra la dipendenza. Quando il dato viene modificato, tutti gli effetti dipendenti vengono rieseguiti automaticamente.

**`ref` — Reattività per valori primitivi e singoli.** La funzione `ref` crea un riferimento reattivo che avvolge un valore in un oggetto con una proprietà `.value`. Nel template Vue effettua l'unwrap automatico di `ref`; nel codice JavaScript l'accesso avviene sempre tramite `.value`.

```vue
<script setup>
import { ref } from "vue";

const contatore = ref(0);
const messaggio = ref("Ciao mondo");
const utente = ref({ nome: "Mario", eta: 30 });

function incrementa() {
  contatore.value++;
  messaggio.value = `Contatore: ${contatore.value}`;
  utente.value.nome = "Luigi";  // La reattività è profonda anche con ref
}
</script>

<template>
  <!-- Nel template, l'unwrap è automatico -->
  <p>{{ contatore }}</p>
  <p>{{ messaggio }}</p>
  <p>{{ utente.nome }}</p>
</template>
```

**`reactive` — Reattività per oggetti complessi.** La funzione `reactive` crea un proxy reattivo di un oggetto senza bisogno di `.value`. Ha limitazioni importanti: funziona solo con tipi oggetto (object, array, Map, Set), la riassegnazione dell'intero oggetto spezza la reattività, e la destrutturazione perde la reattività. Per queste ragioni, la documentazione ufficiale raccomanda `ref` come primitiva di default.

```vue
<script setup>
import { reactive } from "vue";

const stato = reactive({
  contatore: 0,
  utente: {
    nome: "Mario",
    indirizzo: {
      citta: "Roma"
    }
  }
});

function aggiorna() {
  stato.contatore++;  // Nessun .value necessario
  stato.utente.indirizzo.citta = "Milano";  // Reattività profonda

  // ERRORE: riassegnare l'intero oggetto spezza la reattività
  // stato = reactive({ contatore: 1 })
}

// ERRORE: la destrutturazione perde la reattività
// const { contatore } = stato;
</script>
```

**`computed` — Proprietà calcolate.** La funzione `computed` crea un valore derivato reattivo che viene ricalcolato solo quando cambiano le sue dipendenze. I valori computed sono memoizzati: finché le dipendenze non cambiano, l'accesso restituisce il risultato cached senza rieseguire la funzione. Questo li rende ideali per trasformazioni costose o derivazioni di dati.

```vue
<script setup>
import { ref, computed } from "vue";

const prodotti = ref([
  { nome: "Laptop", prezzo: 999, categoria: "elettronica" },
  { nome: "Libro", prezzo: 15, categoria: "libri" },
  { nome: "Tablet", prezzo: 499, categoria: "elettronica" }
]);

const filtroCategoria = ref("tutti");

const prodottiFiltrati = computed(() => {
  if (filtroCategoria.value === "tutti") return prodotti.value;
  return prodotti.value.filter((p) => p.categoria === filtroCategoria.value);
});

const totalePrezzo = computed(() =>
  prodottiFiltrati.value.reduce((acc, p) => acc + p.prezzo, 0)
);

// Computed con getter e setter (writable computed)
const nomeCompleto = computed({
  get: () => `${nome.value} ${cognome.value}`,
  set: (nuovoValore) => {
    const [n, c] = nuovoValore.split(" ");
    nome.value = n;
    cognome.value = c;
  }
});
</script>
```

**`watch` e `watchEffect` — Osservatori reattivi.** La funzione `watch` osserva una o più sorgenti reattive ed esegue una callback quando cambiano. A differenza di `computed`, è pensata per effetti collaterali: chiamate API, manipolazione del DOM, logging. `watchEffect` esegue immediatamente una funzione e traccia automaticamente tutte le dipendenze reattive utilizzate al suo interno.

```vue
<script setup>
import { ref, watch, watchEffect } from "vue";

const termineDiRicerca = ref("");
const risultati = ref([]);
const idCategoria = ref(1);

// Watch singolo con accesso al vecchio e nuovo valore
watch(termineDiRicerca, (nuovo, vecchio) => {
  console.log(`Ricerca cambiata da "${vecchio}" a "${nuovo}"`);
});

// Watch con opzione immediate (esegue subito)
watch(
  idCategoria,
  async (nuovoId) => {
    risultati.value = await fetchProdottiPerCategoria(nuovoId);
  },
  { immediate: true }
);

// Watch multiplo
watch([termineDiRicerca, idCategoria], ([nuovoTermine, nuovoId]) => {
  cercaProdotti(nuovoTermine, nuovoId);
});

// Watch profondo per oggetti annidati
const filtri = ref({ prezzo: { min: 0, max: 1000 }, nome: "" });
watch(filtri, (nuoviFiltri) => {
  applicaFiltri(nuoviFiltri);
}, { deep: true });

// watchEffect — traccia automaticamente le dipendenze
watchEffect(async () => {
  // Vue traccia automaticamente termineDiRicerca e idCategoria
  const dati = await fetch(`/api/cerca?q=${termineDiRicerca.value}&cat=${idCategoria.value}`);
  risultati.value = await dati.json();
});
</script>
```

### Componenti

I componenti sono i mattoncini fondamentali di ogni applicazione Vue. Ogni componente è un file `.vue` con estensione Single-File Component (SFC) che incapsula template, logica e stile in un unico file. Vue utilizza un compilatore SFC (integrato in Vite tramite `@vitejs/plugin-vue`) che trasforma i file `.vue` in moduli JavaScript standard.

**Props — Comunicazione genitore-figlio.** Le props permettono al componente genitore di passare dati al componente figlio. In `<script setup>`, le props vengono dichiarate con `defineProps`. Vue supporta la validazione delle props tramite tipo, obbligatorietà e valori predefiniti. Le props sono **di sola lettura** — il componente figlio non deve mai modificare direttamente una prop.

```vue
<!-- CardProdotto.vue -->
<script setup lang="ts">
interface Props {
  titolo: string;
  prezzo: number;
  descrizione?: string;
  inEvidenza?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  descrizione: "Nessuna descrizione disponibile",
  inEvidenza: false
});
</script>

<template>
  <div :class="['card', { evidenza: inEvidenza }]">
    <h3>{{ titolo }}</h3>
    <p>{{ descrizione }}</p>
    <span class="prezzo">{{ prezzo.toFixed(2) }} EUR</span>
  </div>
</template>
```

```vue
<!-- Utilizzo nel componente genitore -->
<template>
  <CardProdotto
    titolo="Laptop Pro"
    :prezzo="1299.99"
    descrizione="Laptop ad alte prestazioni"
    in-evidenza
  />
</template>
```

**Emits — Comunicazione figlio-genitore.** I componenti figli comunicano con il genitore emettendo eventi personalizzati. In `<script setup>`, gli eventi vengono dichiarati con `defineEmits`. Il genitore ascolta questi eventi con `@nomeEvento`.

```vue
<!-- BarraRicerca.vue -->
<script setup lang="ts">
const emit = defineEmits<{
  cerca: [termine: string];
  reset: [];
}>();

const termineLocale = ref("");

function eseguiRicerca() {
  emit("cerca", termineLocale.value);
}

function pulisci() {
  termineLocale.value = "";
  emit("reset");
}
</script>

<template>
  <div class="barra-ricerca">
    <input v-model="termineLocale" @keyup.enter="eseguiRicerca" placeholder="Cerca..." />
    <button @click="eseguiRicerca">Cerca</button>
    <button @click="pulisci">Pulisci</button>
  </div>
</template>
```

```vue
<!-- Utilizzo nel genitore -->
<template>
  <BarraRicerca @cerca="gestisciRicerca" @reset="ripristina" />
</template>
```

**Slots — Distribuzione del contenuto.** Gli slot permettono al componente genitore di iniettare contenuto all'interno del template del componente figlio. Gli slot nominati consentono di definire più punti di inserimento, mentre gli scoped slot passano dati dal figlio al genitore attraverso lo slot stesso.

```vue
<!-- LayoutScheda.vue -->
<script setup>
defineProps<{ titolo: string }>();
</script>

<template>
  <div class="scheda">
    <div class="scheda-header">
      <slot name="header">
        <h3>{{ titolo }}</h3>
      </slot>
    </div>
    <div class="scheda-body">
      <slot>
        <p>Contenuto predefinito</p>
      </slot>
    </div>
    <div class="scheda-footer">
      <slot name="footer" />
    </div>
  </div>
</template>
```

```vue
<!-- Utilizzo con slot nominati -->
<template>
  <LayoutScheda titolo="Utente">
    <template #header>
      <h2>Profilo Utente Personalizzato</h2>
    </template>

    <p>Questo contenuto va nello slot predefinito (body).</p>

    <template #footer>
      <button>Salva Modifiche</button>
    </template>
  </LayoutScheda>
</template>
```

**Scoped slots** permettono al componente figlio di esporre dati al template del genitore attraverso lo slot.

```vue
<!-- ListaElementi.vue -->
<template>
  <ul>
    <li v-for="elemento in elementi" :key="elemento.id">
      <slot :elemento="elemento" :indice="elementi.indexOf(elemento)">
        {{ elemento.nome }}
      </slot>
    </li>
  </ul>
</template>
```

```vue
<!-- Utilizzo con scoped slot -->
<template>
  <ListaElementi :elementi="prodotti">
    <template #default="{ elemento, indice }">
      <span>{{ indice + 1 }}. {{ elemento.nome }} — {{ elemento.prezzo }} EUR</span>
    </template>
  </ListaElementi>
</template>
```

---

## Composition API

### La funzione setup e `<script setup>`

La Composition API è il paradigma raccomandato per Vue 3. Il cuore è la funzione `setup()`, che viene eseguita prima della creazione del componente — prima ancora di risolvere le props e definire il contesto. Con la sintassi `<script setup>`, l'intero contenuto dello script diventa implicitamente il corpo della funzione `setup()`. Tutte le variabili, le funzioni e gli import dichiarati al livello superiore sono automaticamente disponibili nel template senza bisogno di un return esplicito.

```vue
<script setup lang="ts">
import { ref, onMounted } from "vue";
import type { Utente } from "@/types";

// Tutto ciò che viene dichiarato qui è disponibile nel template
const utenti = ref<Utente[]>([]);
const isCaricamento = ref(true);

async function caricaUtenti() {
  isCaricamento.value = true;
  try {
    const risposta = await fetch("/api/utenti");
    utenti.value = await risposta.json();
  } finally {
    isCaricamento.value = false;
  }
}

onMounted(caricaUtenti);
</script>
```

### Composables — Logica riutilizzabile

I composables sono funzioni che incapsulano e riutilizzano logica reattiva con la Composition API. Seguono la convenzione `use*` (ad esempio `useContatore`, `useFetch`, `useAuth`). Sono l'equivalente funzionale dei mixins di Vue 2, senza le problematiche di conflitto dei nomi.

```typescript
// composables/useFetch.ts
import { ref, watchEffect, type Ref } from "vue";

interface UseFetchReturn<T> {
  dati: Ref<T | null>;
  errore: Ref<string | null>;
  isCaricamento: Ref<boolean>;
  ricarica: () => Promise<void>;
}

export function useFetch<T>(url: Ref<string> | string): UseFetchReturn<T> {
  const dati = ref<T | null>(null) as Ref<T | null>;
  const errore = ref<string | null>(null);
  const isCaricamento = ref(false);

  async function carica() {
    isCaricamento.value = true;
    errore.value = null;
    try {
      const urlEffettivo = typeof url === "string" ? url : url.value;
      const risposta = await fetch(urlEffettivo);
      if (!risposta.ok) throw new Error(`HTTP ${risposta.status}`);
      dati.value = await risposta.json();
    } catch (e) {
      errore.value = e instanceof Error ? e.message : "Errore sconosciuto";
    } finally {
      isCaricamento.value = false;
    }
  }

  watchEffect(() => {
    carica();
  });

  return { dati, errore, isCaricamento, ricarica: carica };
}
```

```vue
<!-- Utilizzo del composable -->
<script setup lang="ts">
import { useFetch } from "@/composables/useFetch";

interface Prodotto {
  id: number;
  nome: string;
  prezzo: number;
}

const { dati: prodotti, errore, isCaricamento } = useFetch<Prodotto[]>("/api/prodotti");
</script>

<template>
  <div v-if="isCaricamento">Caricamento in corso...</div>
  <div v-else-if="errore">Errore: {{ errore }}</div>
  <ul v-else>
    <li v-for="prodotto in prodotti" :key="prodotto.id">
      {{ prodotto.nome }}
    </li>
  </ul>
</template>
```

### Provide / Inject

Il sistema `provide/inject` permette a un componente antenato di fornire dati a tutti i suoi discendenti, indipendentemente dalla profondità della gerarchia. È la soluzione ideale per evitare il "prop drilling" — il passaggio di props attraverso molteplici livelli di componenti intermedi che non utilizzano direttamente quei dati.

```vue
<!-- App.vue — Provider -->
<script setup lang="ts">
import { provide, ref } from "vue";

const tema = ref("chiaro");
const utente = ref({ nome: "Mario", ruolo: "admin" });

provide("tema", tema);
provide("utente", utente);

// Provide di un oggetto read-only per prevenire modifiche accidentali
provide("config", readonly({
  apiUrl: "https://api.esempio.it",
  versione: "2.0"
}));
</script>
```

```vue
<!-- ComponenteNipote.vue — Consumer (qualsiasi livello di profondità) -->
<script setup lang="ts">
import { inject } from "vue";

const tema = inject<Ref<string>>("tema", ref("chiaro"));
const utente = inject("utente");
</script>

<template>
  <div :class="tema">
    <p>Benvenuto, {{ utente?.nome }}</p>
  </div>
</template>
```

### Lifecycle Hooks

La Composition API offre funzioni per agganciarsi ai diversi momenti del ciclo di vita di un componente. Ogni hook accetta una callback che viene eseguita nella fase corrispondente.

```vue
<script setup>
import {
  onBeforeMount,
  onMounted,
  onBeforeUpdate,
  onUpdated,
  onBeforeUnmount,
  onUnmounted,
  onActivated,
  onDeactivated,
  onErrorCaptured
} from "vue";

onBeforeMount(() => {
  // Prima che il componente venga montato nel DOM.
  // Il template è compilato, ma il DOM non è ancora creato.
});

onMounted(() => {
  // Il componente è montato nel DOM.
  // Ideale per: fetch iniziali, setup di listener, accesso al DOM tramite template refs.
});

onBeforeUpdate(() => {
  // Prima che il DOM venga aggiornato dopo un cambio di stato reattivo.
});

onUpdated(() => {
  // Dopo che il DOM è stato aggiornato.
  // Attenzione: modificare lo stato qui può causare loop infiniti.
});

onBeforeUnmount(() => {
  // Prima che il componente venga rimosso dal DOM.
  // Ideale per: pulizia di timer, rimozione di listener manuali.
});

onUnmounted(() => {
  // Il componente è stato rimosso dal DOM e tutte le dipendenze reattive sono disconnesse.
});

onErrorCaptured((errore, istanza, info) => {
  // Cattura errori dai componenti figli. Funziona come un error boundary.
  console.error("Errore catturato:", errore, info);
  return false;  // Impedisce la propagazione dell'errore
});
</script>
```

---

## State Management

### Pinia — Lo state manager ufficiale

Pinia è lo state manager ufficiale per Vue 3, raccomandato dal core team come successore di Vuex. Pinia abbraccia pienamente la Composition API, offre un supporto TypeScript eccellente out of the box, non richiede mutations (a differenza di Vuex), è modulare per design e supporta il code splitting automatico tramite lazy loading degli store.

**Definizione di uno store.** Uno store Pinia viene definito con `defineStore`, che accetta un ID unico e una funzione di setup (stile Composition API) oppure un oggetto di opzioni. Lo stile setup è raccomandato perché offre massima flessibilità e migliore type inference.

```typescript
// stores/prodotti.ts
import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useProdottiStore = defineStore("prodotti", () => {
  // State (equivalente di ref)
  const prodotti = ref<Prodotto[]>([]);
  const isCaricamento = ref(false);
  const filtroCategoria = ref<string | null>(null);

  // Getters (equivalente di computed)
  const prodottiFiltrati = computed(() => {
    if (!filtroCategoria.value) return prodotti.value;
    return prodotti.value.filter((p) => p.categoria === filtroCategoria.value);
  });

  const totaleProdotti = computed(() => prodotti.value.length);

  const prodottiPerCategoria = computed(() => {
    const mappa = new Map<string, Prodotto[]>();
    for (const p of prodotti.value) {
      const lista = mappa.get(p.categoria) || [];
      lista.push(p);
      mappa.set(p.categoria, lista);
    }
    return mappa;
  });

  // Actions (funzioni normali, possono essere async)
  async function caricaProdotti() {
    isCaricamento.value = true;
    try {
      const risposta = await fetch("/api/prodotti");
      prodotti.value = await risposta.json();
    } finally {
      isCaricamento.value = false;
    }
  }

  function aggiungiProdotto(prodotto: Prodotto) {
    prodotti.value.push(prodotto);
  }

  async function eliminaProdotto(id: number) {
    await fetch(`/api/prodotti/${id}`, { method: "DELETE" });
    prodotti.value = prodotti.value.filter((p) => p.id !== id);
  }

  function impostaFiltro(categoria: string | null) {
    filtroCategoria.value = categoria;
  }

  return {
    prodotti,
    isCaricamento,
    filtroCategoria,
    prodottiFiltrati,
    totaleProdotti,
    prodottiPerCategoria,
    caricaProdotti,
    aggiungiProdotto,
    eliminaProdotto,
    impostaFiltro
  };
});
```

**Utilizzo dello store nei componenti.** Lo store viene invocato come una funzione all'interno di `<script setup>`. Le proprietà dello store sono reattive — qualsiasi modifica viene automaticamente riflessa nel template. Per destrutturare lo store mantenendo la reattività si usa `storeToRefs`.

```vue
<script setup lang="ts">
import { storeToRefs } from "pinia";
import { useProdottiStore } from "@/stores/prodotti";

const storeProdotti = useProdottiStore();

// Destrutturazione reattiva per state e getters
const { prodottiFiltrati, isCaricamento, totaleProdotti } = storeToRefs(storeProdotti);

// Le actions si destrutturano direttamente (non sono reattive)
const { caricaProdotti, eliminaProdotto, impostaFiltro } = storeProdotti;

onMounted(caricaProdotti);
</script>

<template>
  <div>
    <p>Totale prodotti: {{ totaleProdotti }}</p>

    <select @change="impostaFiltro(($event.target as HTMLSelectElement).value || null)">
      <option value="">Tutte le categorie</option>
      <option value="elettronica">Elettronica</option>
      <option value="libri">Libri</option>
    </select>

    <div v-if="isCaricamento">Caricamento...</div>
    <ul v-else>
      <li v-for="prodotto in prodottiFiltrati" :key="prodotto.id">
        {{ prodotto.nome }} — {{ prodotto.prezzo }} EUR
        <button @click="eliminaProdotto(prodotto.id)">Elimina</button>
      </li>
    </ul>
  </div>
</template>
```

**Persistenza dello stato.** Il plugin `pinia-plugin-persistedstate` permette di salvare automaticamente lo stato degli store in `localStorage` o `sessionStorage`, ripristinandolo al ricaricamento della pagina.

```typescript
// main.ts
import { createPinia } from "pinia";
import piniaPluginPersistedstate from "pinia-plugin-persistedstate";

const pinia = createPinia();
pinia.use(piniaPluginPersistedstate);
```

```typescript
// stores/preferenze.ts
export const usePreferenzeStore = defineStore("preferenze", () => {
  const tema = ref("chiaro");
  const lingua = ref("it");

  return { tema, lingua };
}, {
  persist: true  // Salva automaticamente in localStorage
});
```

---

## Routing

### Vue Router

Vue Router è il router ufficiale per Vue.js, progettato per integrarsi profondamente con il sistema di reattività di Vue 3. Gestisce la navigazione tra le viste dell'applicazione, supporta route nidificate, parametri dinamici, navigation guards, lazy loading e transizioni animate.

**Configurazione base.** La configurazione avviene creando un'istanza del router con `createRouter`, specificando la strategia di history e l'array delle route.

```typescript
// router/index.ts
import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("@/views/HomeView.vue")
    },
    {
      path: "/prodotti",
      name: "prodotti",
      component: () => import("@/views/ProdottiView.vue"),
      children: [
        {
          path: ":id",
          name: "dettaglio-prodotto",
          component: () => import("@/views/DettaglioProdottoView.vue"),
          props: true  // Passa i parametri della route come props
        }
      ]
    },
    {
      path: "/profilo",
      name: "profilo",
      component: () => import("@/views/ProfiloView.vue"),
      meta: { richiedeAuth: true }
    },
    {
      path: "/:pathMatch(.*)*",
      name: "non-trovata",
      component: () => import("@/views/NonTrovataView.vue")
    }
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition;
    if (to.hash) return { el: to.hash };
    return { top: 0 };
  }
});

export default router;
```

**Navigazione programmatica e accesso ai parametri.** All'interno dei componenti si utilizzano i composables `useRouter` e `useRoute` per navigare e accedere ai parametri della route corrente.

```vue
<script setup lang="ts">
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();

// Accesso ai parametri
const idProdotto = computed(() => route.params.id);
const termineDiRicerca = computed(() => route.query.q);

function vaiADettaglio(id: number) {
  router.push({ name: "dettaglio-prodotto", params: { id } });
}

function tornaIndietro() {
  router.back();
}

function vaiConQuery(termine: string) {
  router.push({ name: "prodotti", query: { q: termine } });
}
</script>

<template>
  <nav>
    <RouterLink to="/">Home</RouterLink>
    <RouterLink :to="{ name: 'prodotti' }">Prodotti</RouterLink>
    <RouterLink :to="{ name: 'profilo' }" active-class="attivo">Profilo</RouterLink>
  </nav>
  <RouterView />
</template>
```

**Navigation Guards — Controllo degli accessi.** I navigation guards intercettano la navigazione permettendo di autorizzarla, negarla o reindirizzarla. Il caso d'uso più comune è la protezione delle route che richiedono autenticazione.

```typescript
// router/index.ts
router.beforeEach(async (to, from) => {
  const authStore = useAuthStore();

  // Rotte che richiedono autenticazione
  if (to.meta.richiedeAuth && !authStore.isAutenticato) {
    return {
      name: "login",
      query: { redirect: to.fullPath }
    };
  }

  // Rotte solo per admin
  if (to.meta.richiedeAdmin && authStore.utente?.ruolo !== "admin") {
    return { name: "non-autorizzato" };
  }

  // Reindirizza utenti già autenticati dalla pagina di login
  if (to.name === "login" && authStore.isAutenticato) {
    return { name: "home" };
  }
});

// Guard per-route
const routes = [
  {
    path: "/admin",
    component: () => import("@/views/AdminView.vue"),
    beforeEnter: (to, from) => {
      // Logica specifica per questa route
    }
  }
];
```

**Lazy Loading delle route.** L'uso di import dinamici `() => import("...")` nelle definizioni delle route abilita automaticamente il code splitting. Ogni route viene caricata come un chunk separato, scaricato solo quando l'utente naviga verso quella route. Questo riduce drasticamente la dimensione del bundle iniziale — tutte le route nell'esempio di configurazione sopra utilizzano già questo pattern.

---

## Forms

### Gestione dei form con v-model

Vue rende la gestione dei form naturale grazie a `v-model`. Per form semplici, la combinazione di `v-model`, ref reattivi e validazione manuale è sufficiente. Per form complessi con molti campi, validazione avanzata e gestione degli errori, si utilizzano librerie dedicate.

```vue
<script setup lang="ts">
import { ref, computed } from "vue";

const form = ref({
  nome: "",
  email: "",
  messaggio: "",
  tipo: "feedback"
});

const errori = ref<Record<string, string>>({});

const isValido = computed(() => Object.keys(errori.value).length === 0 && form.value.nome !== "");

function valida() {
  const nuoviErrori: Record<string, string> = {};

  if (!form.value.nome.trim()) {
    nuoviErrori.nome = "Il nome è obbligatorio";
  }
  if (!form.value.email.includes("@")) {
    nuoviErrori.email = "Email non valida";
  }
  if (form.value.messaggio.length < 10) {
    nuoviErrori.messaggio = "Il messaggio deve avere almeno 10 caratteri";
  }

  errori.value = nuoviErrori;
  return Object.keys(nuoviErrori).length === 0;
}

async function invia() {
  if (!valida()) return;

  await fetch("/api/contatti", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(form.value)
  });
}
</script>

<template>
  <form @submit.prevent="invia">
    <div>
      <label for="nome">Nome</label>
      <input id="nome" v-model="form.nome" />
      <span v-if="errori.nome" class="errore">{{ errori.nome }}</span>
    </div>

    <div>
      <label for="email">Email</label>
      <input id="email" v-model="form.email" type="email" />
      <span v-if="errori.email" class="errore">{{ errori.email }}</span>
    </div>

    <div>
      <label for="messaggio">Messaggio</label>
      <textarea id="messaggio" v-model="form.messaggio"></textarea>
      <span v-if="errori.messaggio" class="errore">{{ errori.messaggio }}</span>
    </div>

    <button type="submit" :disabled="!isValido">Invia</button>
  </form>
</template>
```

### Validazione avanzata con VeeValidate e Zod

Per applicazioni professionali, la combinazione di **VeeValidate** (gestione dello stato del form) e **Zod** (schema di validazione type-safe) offre una soluzione robusta, dichiarativa e completamente tipizzata.

VeeValidate gestisce lo stato dei campi, il tracking delle interazioni (touched, dirty) e la visualizzazione degli errori. Zod è una libreria di validazione TypeScript-first: definisci uno schema una volta e ottieni sia la validazione runtime sia il tipo TypeScript inferito.

```bash
npm install vee-validate @vee-validate/zod zod
```

```vue
<script setup lang="ts">
import { useForm } from "vee-validate";
import { toTypedSchema } from "@vee-validate/zod";
import { z } from "zod";

// Schema Zod — definisce validazione e tipi simultaneamente
const schemaRegistrazione = z.object({
  nome: z
    .string()
    .min(2, "Il nome deve avere almeno 2 caratteri")
    .max(50, "Il nome non può superare i 50 caratteri"),
  email: z
    .string()
    .email("Inserisci un indirizzo email valido"),
  password: z
    .string()
    .min(8, "La password deve avere almeno 8 caratteri")
    .regex(/[A-Z]/, "Deve contenere almeno una lettera maiuscola")
    .regex(/[0-9]/, "Deve contenere almeno un numero"),
  confermaPassword: z.string(),
  accettaTermini: z.literal(true, {
    errorMap: () => ({ message: "Devi accettare i termini e le condizioni" })
  })
}).refine((dati) => dati.password === dati.confermaPassword, {
  message: "Le password non corrispondono",
  path: ["confermaPassword"]
});

// Tipo TypeScript inferito automaticamente dallo schema
type FormRegistrazione = z.infer<typeof schemaRegistrazione>;

const { handleSubmit, errors, defineField, isSubmitting, resetForm } = useForm({
  validationSchema: toTypedSchema(schemaRegistrazione),
  initialValues: {
    nome: "",
    email: "",
    password: "",
    confermaPassword: "",
    accettaTermini: false
  }
});

const [nome, nomeAttrs] = defineField("nome");
const [email, emailAttrs] = defineField("email");
const [password, passwordAttrs] = defineField("password");
const [confermaPassword, confermaPasswordAttrs] = defineField("confermaPassword");
const [accettaTermini, accettaTerminiAttrs] = defineField("accettaTermini");

const onSubmit = handleSubmit(async (valori) => {
  // valori è tipizzato come FormRegistrazione
  await fetch("/api/registrazione", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(valori)
  });
  resetForm();
});
</script>

<template>
  <form @submit="onSubmit" novalidate>
    <div>
      <label for="nome">Nome</label>
      <input id="nome" v-model="nome" v-bind="nomeAttrs" />
      <span v-if="errors.nome" class="errore">{{ errors.nome }}</span>
    </div>

    <div>
      <label for="email">Email</label>
      <input id="email" v-model="email" v-bind="emailAttrs" type="email" />
      <span v-if="errors.email" class="errore">{{ errors.email }}</span>
    </div>

    <div>
      <label for="password">Password</label>
      <input id="password" v-model="password" v-bind="passwordAttrs" type="password" />
      <span v-if="errors.password" class="errore">{{ errors.password }}</span>
    </div>

    <div>
      <label for="confermaPassword">Conferma Password</label>
      <input id="confermaPassword" v-model="confermaPassword" v-bind="confermaPasswordAttrs" type="password" />
      <span v-if="errors.confermaPassword" class="errore">{{ errors.confermaPassword }}</span>
    </div>

    <div>
      <input id="termini" v-model="accettaTermini" v-bind="accettaTerminiAttrs" type="checkbox" />
      <label for="termini">Accetto i termini e le condizioni</label>
      <span v-if="errors.accettaTermini" class="errore">{{ errors.accettaTermini }}</span>
    </div>

    <button type="submit" :disabled="isSubmitting">
      {{ isSubmitting ? "Registrazione..." : "Registrati" }}
    </button>
  </form>
</template>
```

---

## Ecosistema

### Nuxt.js — Il meta-framework Vue

Nuxt.js è il meta-framework ufficiale per Vue, sviluppato dalla Nuxt team in collaborazione con il core team di Vue. Nuxt 3, basato su Vue 3 e Vite, offre un'esperienza full-stack completa con rendering lato server, generazione statica, routing automatico basato sul file system, auto-import dei componenti e dei composables, e un sistema di moduli estensibile.

**Server-Side Rendering (SSR).** Nuxt esegue il rendering della pagina sul server a ogni richiesta, generando HTML completo. Il client poi "idrata" l'HTML statico rendendolo interattivo. Questo migliora il First Contentful Paint e l'indicizzazione SEO.

**Static Site Generation (SSG).** Con `nuxi generate`, Nuxt pre-genera tutte le pagine come file HTML statici a build time, servibili da qualsiasi CDN senza server Node.js. Ideale per blog, documentazione e siti marketing.

**Routing basato sul file system.** In Nuxt, la struttura delle cartelle dentro `pages/` definisce automaticamente le route dell'applicazione senza necessità di configurazione manuale.

```
pages/
  index.vue          → /
  about.vue          → /about
  prodotti/
    index.vue        → /prodotti
    [id].vue         → /prodotti/:id
  blog/
    [...slug].vue    → /blog/* (catch-all)
```

**Auto-import.** Nuxt importa automaticamente i componenti da `components/`, i composables da `composables/` e le utility da `utils/`. Non servono istruzioni `import` esplicite — il compilatore le aggiunge a build time mantenendo il tree-shaking funzionante.

**Data fetching con `useFetch` e `useAsyncData`.** Nuxt fornisce composables dedicati per il fetching dati che funzionano sia lato server che lato client, gestendo automaticamente la de-duplicazione delle richieste e la serializzazione dello stato per l'idratazione.

```vue
<!-- pages/prodotti/[id].vue -->
<script setup lang="ts">
const route = useRoute();

const { data: prodotto, error } = await useFetch(`/api/prodotti/${route.params.id}`);

if (error.value) {
  throw createError({ statusCode: 404, message: "Prodotto non trovato" });
}
</script>

<template>
  <div v-if="prodotto">
    <h1>{{ prodotto.nome }}</h1>
    <p>{{ prodotto.descrizione }}</p>
    <span>{{ prodotto.prezzo }} EUR</span>
  </div>
</template>
```

### Vuetify e PrimeVue — Librerie di componenti UI

**Vuetify** è la libreria di componenti UI più matura dell'ecosistema Vue, basata sulle specifiche Material Design di Google. Offre oltre 80 componenti pronti all'uso, un sistema di griglia responsivo a 12 colonne, un motore di temi personalizzabile, supporto completo per l'accessibilità e tipizzazione TypeScript. Vuetify 3 è riscritto per Vue 3 con pieno supporto per la Composition API.

```vue
<template>
  <v-container>
    <v-row>
      <v-col v-for="prodotto in prodotti" :key="prodotto.id" cols="12" md="4">
        <v-card>
          <v-img :src="prodotto.immagine" height="200" cover />
          <v-card-title>{{ prodotto.nome }}</v-card-title>
          <v-card-text>{{ prodotto.descrizione }}</v-card-text>
          <v-card-actions>
            <v-btn color="primary" variant="text">Dettagli</v-btn>
            <v-spacer />
            <v-btn color="success" variant="elevated">Acquista</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
```

**PrimeVue** offre oltre 90 componenti UI con un design non vincolato a Material Design. Fornisce temi diversi (Material, Bootstrap, Tailwind-based, Lara, Aura) e un sistema di tematizzazione tramite design tokens. È particolarmente forte nei componenti per dati tabulari (DataTable con ordinamento, paginazione, filtri, editing inline), grafici e calendari avanzati.

### Testing — Vitest e Vue Test Utils

**Vitest** è il framework di testing raccomandato per progetti Vue con Vite. Condivide la stessa configurazione e pipeline di trasformazione di Vite, eliminando la necessità di configurazione separata per i test. Offre una API compatibile con Jest, esecuzione parallela, watch mode istantaneo e supporto nativo per TypeScript e JSX.

**Vue Test Utils** è la libreria ufficiale di testing per componenti Vue. Fornisce utilità per montare componenti in isolamento, simulare interazioni utente, verificare il rendering e testare la logica dei componenti.

```typescript
// components/__tests__/Contatore.test.ts
import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import Contatore from "@/components/Contatore.vue";

describe("Contatore", () => {
  it("mostra il valore iniziale", () => {
    const wrapper = mount(Contatore, {
      props: { valoreIniziale: 5 }
    });
    expect(wrapper.text()).toContain("5");
  });

  it("incrementa il contatore al click del bottone", async () => {
    const wrapper = mount(Contatore);
    const bottone = wrapper.find("[data-test='incrementa']");

    await bottone.trigger("click");
    await bottone.trigger("click");

    expect(wrapper.text()).toContain("2");
  });

  it("emette l'evento 'cambiato' con il nuovo valore", async () => {
    const wrapper = mount(Contatore);

    await wrapper.find("[data-test='incrementa']").trigger("click");

    expect(wrapper.emitted("cambiato")).toBeTruthy();
    expect(wrapper.emitted("cambiato")![0]).toEqual([1]);
  });
});
```

**Testing degli store Pinia.** Pinia offre un helper dedicato `createTestingPinia` che crea un'istanza Pinia isolata per i test, con la possibilità di fornire stato iniziale e mockare le actions.

```typescript
// stores/__tests__/prodotti.test.ts
import { describe, it, expect, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useProdottiStore } from "@/stores/prodotti";

describe("Store Prodotti", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("filtra i prodotti per categoria", () => {
    const store = useProdottiStore();
    store.prodotti = [
      { id: 1, nome: "Laptop", categoria: "elettronica", prezzo: 999 },
      { id: 2, nome: "Libro Vue", categoria: "libri", prezzo: 25 },
      { id: 3, nome: "Tablet", categoria: "elettronica", prezzo: 499 }
    ];

    store.impostaFiltro("elettronica");

    expect(store.prodottiFiltrati).toHaveLength(2);
    expect(store.prodottiFiltrati.every((p) => p.categoria === "elettronica")).toBe(true);
  });
});
```

---

## Best Practices

1. **Usa la Composition API con `<script setup>` e TypeScript.** La Composition API con `<script setup>` è l'approccio raccomandato dalla documentazione ufficiale di Vue 3. Combinata con TypeScript, offre massima type safety, autocompletamento IDE eccellente, inferenza dei tipi nelle props e negli emits, e codice più conciso. Configura `strict: true` nel `tsconfig.json` e tipizza sempre le props con `defineProps<T>()`. L'investimento iniziale in TypeScript viene ripagato ampiamente dalla riduzione dei bug runtime e dalla facilità di refactoring.

2. **Organizza la logica in composables piccoli e focalizzati.** Estrai la logica riutilizzabile in composables con la convenzione `use*`. Ogni composable dovrebbe avere una singola responsabilità: `useFetch` per le chiamate HTTP, `useAuth` per l'autenticazione, `usePaginazione` per la logica di paginazione. Evita composables monolitici che gestiscono troppo. I composables sono la chiave per mantenere i componenti snelli e la logica testabile indipendentemente dall'interfaccia.

3. **Preferisci `ref` a `reactive` come primitiva di default.** La documentazione ufficiale raccomanda `ref` come primitiva reattiva principale. `ref` funziona con qualsiasi tipo di dato (primitivi, oggetti, array), non perde reattività quando destrutturato (tramite `toRefs` o `storeToRefs`), e il `.value` esplicito rende chiaro nel codice JavaScript quando si sta accedendo a un dato reattivo. Riserva `reactive` per oggetti di stato complessi dove la sintassi senza `.value` migliora significativamente la leggibilità.

4. **Gestisci lo stato globale con Pinia, non con provide/inject.** Pinia è progettato per lo state management: offre DevTools integration, persistenza, time-travel debugging, hot module replacement e una struttura chiara. Usa `provide/inject` solo per dati di configurazione o dipendenze che devono attraversare molti livelli di componenti (tema, configurazione locale, istanza del client API). Non usare `provide/inject` come sostituto di Pinia per lo stato applicativo globale — manca di strumenti di debug e può diventare difficile da tracciare.

5. **Implementa il lazy loading per route e componenti pesanti.** Ogni route della tua applicazione dovrebbe usare import dinamici `() => import("...")` per abilitare il code splitting automatico. Per componenti pesanti che non sono sempre visibili (modali, grafici, editor), usa `defineAsyncComponent` per caricarli solo quando necessari. Questo riduce drasticamente la dimensione del bundle iniziale e migliora il tempo di caricamento percepito dall'utente.

6. **Usa `v-for` sempre con una `:key` stabile e univoca.** L'attributo `:key` non è solo una best practice — è essenziale per il corretto funzionamento dell'algoritmo di riconciliazione di Vue. Usa sempre un identificatore unico e stabile (tipicamente l'ID dal database, mai l'indice dell'array) come chiave. Una chiave instabile o non unica causa bug sottili: componenti che mantengono lo stato sbagliato dopo un riordinamento, animazioni che non funzionano, e input che mostrano valori errati. Per le liste statiche che non vengono mai riordinate o filtrate, l'indice è accettabile.

7. **Valida i form con schema dichiarativi, non con logica imperativa.** Per qualsiasi form che vada oltre i due o tre campi, adotta VeeValidate con Zod (o Yup). Gli schemi di validazione dichiarativi sono più leggibili, più manutenibili e producono automaticamente i tipi TypeScript corrispondenti. La validazione imperativa sparsa nei metodi del componente diventa rapidamente ingestibile quando i requisiti di validazione crescono. Centralizza le regole in uno schema, riutilizzalo tra front-end e back-end se usi TypeScript full-stack.

8. **Testa componenti, composables e store in isolamento.** Usa Vitest come test runner e Vue Test Utils per montare i componenti. Testa i componenti dal punto di vista dell'utente: verifica il testo renderizzato, simula click e input, controlla gli eventi emessi. Non testare dettagli implementativi come lo stato interno di `ref`. Testa i composables tramite componenti wrapper minimali. Testa gli store Pinia con `createPinia()` isolato in ogni test. Punta a una copertura significativa della logica business, non a una copertura del 100% dei template.

9. **Preferisci computed properties alle funzioni nei template.** Quando un valore derivato viene usato nel template, usa una `computed` property anziché chiamare una funzione. Le computed sono memoizzate — ricalcolano solo quando le dipendenze cambiano. Una funzione chiamata nel template viene rieseguita a ogni re-render del componente, anche se le sue dipendenze non sono cambiate. La differenza di performance è trascurabile per calcoli semplici, ma diventa significativa per trasformazioni costose o liste lunghe.

10. **Mantieni i componenti piccoli e la struttura del progetto coerente.** Un componente dovrebbe idealmente restare sotto le 200 righe. Se cresce oltre, estrai sotto-componenti e composables. Organizza il progetto per funzionalità quando l'applicazione cresce: `features/prodotti/` contiene componenti, composables, store e tipi relativi ai prodotti. Segui le convenzioni di denominazione Vue: PascalCase per i componenti nei file e nel template, kebab-case per gli eventi personalizzati. Configura ESLint con `eslint-plugin-vue` e Prettier per garantire coerenza automatica nello stile del codice.

---

## Composition API Avanzata

### Composables avanzati — Pattern e architettura

I composables rappresentano il meccanismo principale per la riusabilità della logica in Vue 3. Al di là del pattern base `use*`, esistono tecniche avanzate che permettono di costruire composables robusti, componibili tra loro e pronti per applicazioni di scala enterprise.

**Composables con dipendenze iniettate.** Un composable avanzato può ricevere dipendenze esterne tramite parametri o tramite `inject`, permettendo l'inversione del controllo. Questo pattern rende il composable testabile in isolamento, poiché le dipendenze possono essere sostituite con mock nei test.

```typescript
// composables/useApiClient.ts
import { inject, type InjectionKey, type Ref } from "vue";

export interface ApiClient {
  get<T>(url: string): Promise<T>;
  post<T>(url: string, body: unknown): Promise<T>;
  delete(url: string): Promise<void>;
}

export const API_CLIENT_KEY: InjectionKey<ApiClient> = Symbol("api-client");

export function useApiClient(): ApiClient {
  const client = inject(API_CLIENT_KEY);
  if (!client) {
    throw new Error(
      "ApiClient non fornito. Usa provide(API_CLIENT_KEY, client) in un componente antenato."
    );
  }
  return client;
}
```

```typescript
// composables/useProdotti.ts
import { ref, computed } from "vue";
import { useApiClient } from "./useApiClient";
import type { Prodotto } from "@/types";

export function useProdotti() {
  const client = useApiClient();
  const prodotti = ref<Prodotto[]>([]);
  const isCaricamento = ref(false);
  const errore = ref<string | null>(null);

  async function carica() {
    isCaricamento.value = true;
    errore.value = null;
    try {
      prodotti.value = await client.get<Prodotto[]>("/api/prodotti");
    } catch (e) {
      errore.value = e instanceof Error ? e.message : "Errore sconosciuto";
    } finally {
      isCaricamento.value = false;
    }
  }

  const totale = computed(() => prodotti.value.length);

  return { prodotti, isCaricamento, errore, carica, totale };
}
```

**Composables componibili (composable composition).** Un composable può utilizzare altri composables al suo interno, creando catene di composizione. Questo approccio mantiene ogni funzione focalizzata su una singola responsabilità pur permettendo comportamenti complessi.

```typescript
// composables/usePaginatedSearch.ts
import { ref, computed, watch, type Ref } from "vue";
import { useDebouncedRef } from "./useDebouncedRef";
import { useFetch } from "./useFetch";

export function usePaginatedSearch<T>(baseUrl: string) {
  const query = useDebouncedRef("", 300);
  const pagina = ref(1);
  const perPagina = ref(20);

  const url = computed(
    () => `${baseUrl}?q=${query.value}&page=${pagina.value}&limit=${perPagina.value}`
  );

  const { dati, errore, isCaricamento } = useFetch<{ items: T[]; total: number }>(url);

  const items = computed(() => dati.value?.items ?? []);
  const totalePagine = computed(() =>
    Math.ceil((dati.value?.total ?? 0) / perPagina.value)
  );

  watch(query, () => {
    pagina.value = 1;
  });

  function paginaSuccessiva() {
    if (pagina.value < totalePagine.value) pagina.value++;
  }

  function paginaPrecedente() {
    if (pagina.value > 1) pagina.value--;
  }

  return {
    query, pagina, perPagina, items, totalePagine,
    errore, isCaricamento, paginaSuccessiva, paginaPrecedente
  };
}
```

**Composable con cleanup automatico.** Quando un composable crea risorse che devono essere liberate (listener, timer, connessioni WebSocket), è fondamentale registrare la pulizia tramite `onUnmounted` o restituire una funzione di cleanup esplicita.

```typescript
// composables/useWebSocket.ts
import { ref, onUnmounted } from "vue";

export function useWebSocket(url: string) {
  const dati = ref<unknown>(null);
  const stato = ref<"connecting" | "open" | "closed" | "error">("connecting");
  let ws: WebSocket | null = null;

  function connetti() {
    ws = new WebSocket(url);
    ws.onopen = () => { stato.value = "open"; };
    ws.onmessage = (evento) => { dati.value = JSON.parse(evento.data); };
    ws.onerror = () => { stato.value = "error"; };
    ws.onclose = () => { stato.value = "closed"; };
  }

  function disconnetti() {
    ws?.close();
    ws = null;
    stato.value = "closed";
  }

  function invia(payload: unknown) {
    if (ws && stato.value === "open") {
      ws.send(JSON.stringify(payload));
    }
  }

  connetti();
  onUnmounted(disconnetti);

  return { dati, stato, invia, disconnetti, connetti };
}
```

### Provide / Inject avanzato — InjectionKey e pattern di dependency injection

Il sistema `provide/inject` di Vue 3, combinato con `InjectionKey` tipizzate, permette di implementare un vero pattern di dependency injection con type safety completo. Questo va ben oltre il semplice passaggio di dati: permette di iniettare servizi, configurazioni e dipendenze in modo strutturato.

**InjectionKey tipizzate.** TypeScript fornisce l'interfaccia `InjectionKey<T>` che garantisce che `provide` e `inject` lavorino con lo stesso tipo, eliminando errori a runtime causati da tipi incompatibili.

```typescript
// injection-keys.ts
import type { InjectionKey, Ref } from "vue";

export interface TemaConfig {
  colori: {
    primario: string;
    secondario: string;
    sfondo: string;
    testo: string;
  };
  tipografia: {
    fontFamiglia: string;
    dimensioneBase: number;
  };
  modoScuro: boolean;
}

export const TEMA_KEY: InjectionKey<Ref<TemaConfig>> = Symbol("tema");
export const LOGGER_KEY: InjectionKey<Logger> = Symbol("logger");
export const NOTIFICHE_KEY: InjectionKey<NotificheService> = Symbol("notifiche");
```

```vue
<!-- App.vue — Root provider -->
<script setup lang="ts">
import { provide, ref, readonly } from "vue";
import { TEMA_KEY, type TemaConfig } from "@/injection-keys";

const tema = ref<TemaConfig>({
  colori: { primario: "#3b82f6", secondario: "#10b981", sfondo: "#ffffff", testo: "#1f2937" },
  tipografia: { fontFamiglia: "Inter, sans-serif", dimensioneBase: 16 },
  modoScuro: false
});

// Fornisci una versione readonly per prevenire modifiche non autorizzate
provide(TEMA_KEY, readonly(tema));

// Fornisci anche una funzione per aggiornare il tema in modo controllato
provide("aggiornaTema", (aggiornamenti: Partial<TemaConfig>) => {
  tema.value = { ...tema.value, ...aggiornamenti };
});
</script>
```

**Pattern factory con provide/inject.** Per servizi complessi, il pattern factory crea l'istanza del servizio nel provider e la inietta nei consumatori, garantendo un ciclo di vita controllato.

```typescript
// composables/useNotifiche.ts
import { inject } from "vue";
import { NOTIFICHE_KEY } from "@/injection-keys";

export function useNotifiche() {
  const servizio = inject(NOTIFICHE_KEY);
  if (!servizio) {
    throw new Error("NotificheService non fornito. Avvolgi l'app con NotificheProvider.");
  }
  return servizio;
}
```

### defineModel — v-model semplificato per componenti

La macro `defineModel`, stabilizzata in Vue 3.4, semplifica drasticamente la creazione di componenti che supportano `v-model`. Prima di `defineModel`, implementare `v-model` su un componente richiedeva dichiarare una prop `modelValue` e emettere manualmente l'evento `update:modelValue`. Con `defineModel`, tutto questo viene condensato in una singola dichiarazione.

```vue
<!-- InputTesto.vue — Con defineModel -->
<script setup lang="ts">
const modello = defineModel<string>({ required: true });
// modello è un Ref<string> — legge modelValue e emette update:modelValue automaticamente
</script>

<template>
  <input :value="modello" @input="modello = ($event.target as HTMLInputElement).value" />
</template>
```

```vue
<!-- Utilizzo nel genitore — identico al v-model classico -->
<template>
  <InputTesto v-model="nomeUtente" />
</template>
```

**v-model multipli con nomi.** `defineModel` supporta v-model multipli con nomi distinti, permettendo di controllare più valori con un singolo componente.

```vue
<!-- InputIntervallo.vue — Due v-model distinti -->
<script setup lang="ts">
const minimo = defineModel<number>("min", { default: 0 });
const massimo = defineModel<number>("max", { default: 100 });
</script>

<template>
  <div class="intervallo">
    <label>
      Min: <input type="number" v-model.number="minimo" />
    </label>
    <label>
      Max: <input type="number" v-model.number="massimo" />
    </label>
  </div>
</template>
```

```vue
<!-- Utilizzo nel genitore -->
<template>
  <InputIntervallo v-model:min="filtroPrezzo.min" v-model:max="filtroPrezzo.max" />
</template>
```

**defineModel con trasformazione e validazione.** È possibile aggiungere logica di trasformazione combinando `defineModel` con `watch` o `computed` per validare o normalizzare il valore prima di propagarlo.

```vue
<script setup lang="ts">
const modello = defineModel<string>({ default: "" });

// Trasformazione: forza lowercase
watch(modello, (valore) => {
  const normalizzato = valore.toLowerCase().trim();
  if (normalizzato !== valore) {
    modello.value = normalizzato;
  }
});
</script>
```

---

## Sistema di reattività — Internals

### Architettura basata su Proxy ES6

Il sistema di reattività di Vue 3 è costruito interamente sui Proxy ES6, un meccanismo nativo di JavaScript che permette di intercettare e ridefinire operazioni fondamentali sugli oggetti. Quando si chiama `reactive(oggetto)`, Vue crea un Proxy attorno all'oggetto originale. Questo Proxy intercetta le operazioni di lettura (get) e scrittura (set) sulle proprietà dell'oggetto.

**Il ciclo di tracciamento delle dipendenze** funziona in tre fasi. Nella fase di **track** (tracciamento), quando un dato reattivo viene letto all'interno di un effetto attivo (rendering del template, `computed`, `watchEffect`), Vue registra la dipendenza in una struttura dati interna chiamata `depsMap` — una `WeakMap` che mappa ogni oggetto sorgente alle sue proprietà tracciate. Nella fase di **trigger** (attivazione), quando un dato reattivo viene modificato, Vue consulta la `depsMap` per trovare tutti gli effetti che dipendono da quella proprietà e li schedula per la riesecuzione. La fase di **scheduling** (pianificazione) garantisce che gli aggiornamenti del DOM vengano raggruppati (batched): anche se più dati reattivi cambiano in rapida successione, Vue esegue un singolo aggiornamento del DOM nel prossimo microtask, ottimizzando le performance.

```typescript
// Illustrazione concettuale semplificata del meccanismo interno
// (NON è il codice reale di Vue, solo un modello didattico)

const targetMap = new WeakMap<object, Map<string | symbol, Set<Function>>>();
let activeEffect: Function | null = null;

function track(target: object, key: string | symbol) {
  if (!activeEffect) return;
  let depsMap = targetMap.get(target);
  if (!depsMap) {
    depsMap = new Map();
    targetMap.set(target, depsMap);
  }
  let deps = depsMap.get(key);
  if (!deps) {
    deps = new Set();
    depsMap.set(key, deps);
  }
  deps.add(activeEffect);
}

function trigger(target: object, key: string | symbol) {
  const depsMap = targetMap.get(target);
  if (!depsMap) return;
  const deps = depsMap.get(key);
  if (deps) {
    deps.forEach((effetto) => effetto());
  }
}
```

### Effect Scope — Gestione raggruppata degli effetti

L'API `effectScope` permette di raggruppare effetti reattivi (`watch`, `watchEffect`, `computed`) in un unico scope che può essere fermato (disposed) in blocco. Questo è particolarmente utile nei composables che creano molti effetti e devono poterli eliminare tutti contemporaneamente.

```typescript
import { effectScope, ref, computed, watch, onScopeDispose } from "vue";

const scope = effectScope();

scope.run(() => {
  const contatore = ref(0);

  const doppio = computed(() => contatore.value * 2);

  watch(contatore, (valore) => {
    console.log(`Contatore cambiato a: ${valore}`);
  });

  // onScopeDispose registra una callback di pulizia nello scope corrente
  const timer = setInterval(() => { contatore.value++; }, 1000);
  onScopeDispose(() => {
    clearInterval(timer);
  });
});

// Ferma tutti gli effetti creati dentro lo scope, eseguendo tutti gli onScopeDispose
scope.stop();
```

**Uso nei composables.** I composables avanzati usano `effectScope` internamente per controllare il ciclo di vita degli effetti indipendentemente dal componente che li utilizza. La libreria VueUse usa questo pattern estensivamente.

```typescript
// composables/usePolling.ts
import { effectScope, ref, onScopeDispose, type EffectScope } from "vue";

export function usePolling<T>(fetcher: () => Promise<T>, intervalloMs: number) {
  const dati = ref<T | null>(null) as Ref<T | null>;
  const errore = ref<string | null>(null);
  let scope: EffectScope | null = null;

  function avvia() {
    if (scope) return;
    scope = effectScope();
    scope.run(() => {
      const timer = setInterval(async () => {
        try {
          dati.value = await fetcher();
          errore.value = null;
        } catch (e) {
          errore.value = e instanceof Error ? e.message : "Errore";
        }
      }, intervalloMs);

      onScopeDispose(() => clearInterval(timer));
    });
  }

  function ferma() {
    scope?.stop();
    scope = null;
  }

  avvia();
  onScopeDispose(ferma);

  return { dati, errore, avvia, ferma };
}
```

### Computed vs Watch — Quando usare cosa

La distinzione tra `computed` e `watch`/`watchEffect` è fondamentale per scrivere codice Vue idiomatico. Sebbene entrambi reagiscano a cambiamenti di stato, hanno scopi radicalmente diversi.

**`computed`** è progettato per **derivare valori**. Una computed property rappresenta un calcolo puro: prende dati in input e restituisce un valore derivato. Non produce effetti collaterali. Vue la memoizza: il calcolo viene eseguito solo quando le dipendenze cambiano, e accessi successivi restituiscono il valore cached. Usa `computed` quando puoi esprimere la logica come "Y è funzione di X".

**`watch` e `watchEffect`** sono progettati per **effetti collaterali**: operazioni che interagiscono con il mondo esterno in risposta a cambiamenti di stato. Chiamate API, manipolazione diretta del DOM, salvataggio in localStorage, logging, invio di analytics — queste sono tutte situazioni in cui serve un watcher.

```vue
<script setup lang="ts">
import { ref, computed, watch, watchEffect } from "vue";

const prodotti = ref<Prodotto[]>([]);
const filtro = ref("");
const ordinamento = ref<"nome" | "prezzo">("nome");

// COMPUTED — derivazione pura di valori, memoizzata
const prodottiVisibili = computed(() => {
  let risultato = prodotti.value;
  if (filtro.value) {
    risultato = risultato.filter((p) =>
      p.nome.toLowerCase().includes(filtro.value.toLowerCase())
    );
  }
  return [...risultato].sort((a, b) => {
    if (ordinamento.value === "prezzo") return a.prezzo - b.prezzo;
    return a.nome.localeCompare(b.nome);
  });
});

// WATCH — effetto collaterale, NON derivazione
watch(filtro, (nuovoFiltro) => {
  // Analytics: traccia cosa cercano gli utenti
  analytics.track("product_search", { query: nuovoFiltro });
});

// WATCHEFFECT — traccia automaticamente le dipendenze
watchEffect(() => {
  // Aggiorna il titolo della pagina quando cambiano i risultati
  document.title = `Prodotti (${prodottiVisibili.value.length} risultati)`;
});
</script>
```

**Regola pratica.** Se il risultato è un valore che altri pezzi di codice leggono, usa `computed`. Se il risultato è un'azione che il codice esegue (scrivere, inviare, loggare), usa `watch` o `watchEffect`. Non usare `watch` per calcolare valori derivati — rende il codice più verboso e perde la memoizzazione automatica.

---

## Pinia — Approfondimento

### Plugin Pinia

Pinia supporta un sistema di plugin che permette di estendere il comportamento di tutti gli store. Un plugin Pinia è una funzione che riceve il contesto dello store e può aggiungere proprietà, azioni, wrappare metodi esistenti o iniettare logica cross-cutting.

```typescript
// plugins/piniaLogger.ts
import { type PiniaPluginContext } from "pinia";

export function piniaLoggerPlugin(context: PiniaPluginContext) {
  const { store } = context;

  // Logga ogni mutazione dello stato
  store.$subscribe((mutation, state) => {
    console.log(`[${store.$id}] Mutazione:`, mutation.type);
    console.log(`[${store.$id}] Nuovo stato:`, JSON.parse(JSON.stringify(state)));
  });

  // Logga ogni azione
  store.$onAction(({ name, args, after, onError }) => {
    const inizio = Date.now();
    console.log(`[${store.$id}] Azione: ${name}`, args);

    after((risultato) => {
      console.log(`[${store.$id}] ${name} completata in ${Date.now() - inizio}ms`, risultato);
    });

    onError((errore) => {
      console.error(`[${store.$id}] ${name} fallita:`, errore);
    });
  });
}

// main.ts
const pinia = createPinia();
pinia.use(piniaLoggerPlugin);
```

**Plugin per la gestione degli errori.** Un plugin che centralizza la gestione degli errori per tutte le azioni asincrone degli store.

```typescript
// plugins/piniaErrorHandler.ts
export function piniaErrorHandlerPlugin({ store }: PiniaPluginContext) {
  store.$onAction(({ name, onError }) => {
    onError((errore) => {
      // Invia a un servizio di error tracking
      errorTracker.captureException(errore, {
        extra: { store: store.$id, action: name }
      });

      // Notifica l'utente se l'errore è rilevante
      if (errore instanceof NetworkError) {
        notifiche.mostra({
          tipo: "errore",
          messaggio: "Errore di rete. Controlla la connessione."
        });
      }
    });
  });
}
```

### Comunicazione tra store

Nelle applicazioni complesse, gli store Pinia devono spesso comunicare tra loro. Pinia supporta questo naturalmente: uno store può importare e utilizzare un altro store all'interno delle proprie azioni e getters.

```typescript
// stores/carrello.ts
import { defineStore } from "pinia";
import { useProdottiStore } from "./prodotti";
import { useAuthStore } from "./auth";

export const useCarrelloStore = defineStore("carrello", () => {
  const items = ref<CarrelloItem[]>([]);

  const totale = computed(() => {
    const storeProdotti = useProdottiStore();
    return items.value.reduce((acc, item) => {
      const prodotto = storeProdotti.prodotti.find((p) => p.id === item.prodottoId);
      return acc + (prodotto?.prezzo ?? 0) * item.quantita;
    }, 0);
  });

  async function checkout() {
    const authStore = useAuthStore();
    if (!authStore.isAutenticato) {
      throw new Error("Autenticazione richiesta per il checkout");
    }

    const risposta = await fetch("/api/ordini", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ items: items.value })
    });

    if (risposta.ok) {
      items.value = [];
    }
  }

  return { items, totale, checkout };
});
```

### Idratazione SSR con Pinia

Quando Pinia viene usato con SSR (Server-Side Rendering), lo stato viene serializzato sul server e inviato al client come parte dell'HTML. Il client deve "idratare" gli store con questo stato iniziale per evitare che il rendering client-side ricalcoli tutto da zero.

In Nuxt 3, l'idratazione avviene automaticamente grazie al modulo `@pinia/nuxt`. Lo stato degli store popolati durante il rendering server-side viene serializzato nell'HTML come `__NUXT_STATE__` e Pinia lo ripristina automaticamente sul client.

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ["@pinia/nuxt"]
});
```

```typescript
// stores/articoli.ts — Funziona identicamente su server e client
export const useArticoliStore = defineStore("articoli", () => {
  const articoli = ref<Articolo[]>([]);
  const caricato = ref(false);

  async function carica() {
    if (caricato.value) return;
    // In SSR, questa fetch avviene sul server
    // Lo stato risultante viene automaticamente idratato sul client
    articoli.value = await $fetch("/api/articoli");
    caricato.value = true;
  }

  return { articoli, caricato, carica };
});
```

Per applicazioni Vue senza Nuxt che implementano SSR manuale, l'idratazione richiede la serializzazione esplicita dello stato nel template HTML e il ripristino tramite `pinia.state.value`.

```typescript
// entry-server.ts
const pinia = createPinia();
app.use(pinia);

// Dopo il rendering, serializza lo stato
const statoIniziale = JSON.stringify(pinia.state.value);
// Inietta nel template HTML come: window.__PINIA_STATE__ = ...

// entry-client.ts
const pinia = createPinia();
if (window.__PINIA_STATE__) {
  pinia.state.value = JSON.parse(window.__PINIA_STATE__);
}
app.use(pinia);
```

---

## Nuxt 3 — Approfondimento

### Server Routes e API con Nitro

Nuxt 3 include Nitro come engine server-side. Nitro permette di scrivere API routes direttamente all'interno del progetto Nuxt, nella directory `server/`. Ogni file in `server/api/` diventa un endpoint API accessibile dall'applicazione. Nitro compila le route server con code-splitting, il che significa che ogni route carica solo il codice necessario al momento della richiesta.

```typescript
// server/api/prodotti/index.get.ts
// Il suffisso .get indica che risponde solo a richieste GET
export default defineEventHandler(async (event) => {
  const query = getQuery(event);
  const pagina = Number(query.page) || 1;
  const limite = Math.min(Number(query.limit) || 20, 100);

  const prodotti = await db.prodotto.findMany({
    skip: (pagina - 1) * limite,
    take: limite,
    orderBy: { createdAt: "desc" }
  });

  const totale = await db.prodotto.count();

  return {
    items: prodotti,
    total: totale,
    page: pagina,
    limit: limite
  };
});
```

```typescript
// server/api/prodotti/index.post.ts
import { z } from "zod";

const schemaProdotto = z.object({
  nome: z.string().min(1).max(200),
  prezzo: z.number().positive(),
  categoria: z.string().min(1),
  descrizione: z.string().optional()
});

export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  const risultato = schemaProdotto.safeParse(body);

  if (!risultato.success) {
    throw createError({
      statusCode: 400,
      message: "Dati non validi",
      data: risultato.error.flatten()
    });
  }

  const prodotto = await db.prodotto.create({ data: risultato.data });
  setResponseStatus(event, 201);
  return prodotto;
});
```

```typescript
// server/api/prodotti/[id].delete.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, "id");
  if (!id) {
    throw createError({ statusCode: 400, message: "ID obbligatorio" });
  }

  await db.prodotto.delete({ where: { id: Number(id) } });
  setResponseStatus(event, 204);
  return null;
});
```

### Middleware in Nuxt 3

Nuxt 3 distingue due tipi di middleware: **route middleware** (lato client, per la navigazione) e **server middleware** (lato server, per le richieste HTTP).

**Route middleware** intercetta la navigazione tra le pagine. Può essere definito inline nella pagina, in file dedicati dentro `middleware/`, o come middleware globale con il suffisso `.global`.

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { isAutenticato } = useAuthState();

  if (!isAutenticato.value && to.path !== "/login") {
    return navigateTo("/login", { redirectCode: 302 });
  }
});
```

```vue
<!-- pages/dashboard.vue -->
<script setup lang="ts">
definePageMeta({
  middleware: "auth"
});

const { data: statistiche } = await useFetch("/api/statistiche");
</script>
```

**Middleware globale** viene eseguito su ogni navigazione e si dichiara aggiungendo il suffisso `.global` al nome del file.

```typescript
// middleware/analytics.global.ts
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.client) {
    analytics.pageView(to.fullPath);
  }
});
```

**Server middleware** opera a livello HTTP, prima che le route vengano gestite. Viene eseguito su ogni richiesta al server. Attenzione: poiché i server middleware globali vengono caricati per ogni richiesta, un uso eccessivo può degradare le performance. Per logica specifica a singole route, è preferibile utilizzare utility functions chiamate direttamente dentro gli event handler.

```typescript
// server/middleware/cors.ts
export default defineEventHandler((event) => {
  setResponseHeaders(event, {
    "Access-Control-Allow-Origin": "https://miodominio.it",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
  });

  if (event.method === "OPTIONS") {
    setResponseStatus(event, 204);
    return null;
  }
});
```

### Layers — Architettura modulare

I layers di Nuxt 3 permettono di estendere un'applicazione Nuxt con funzionalità, componenti, composables e configurazioni provenienti da moduli esterni o directory locali. Un layer è essenzialmente un'applicazione Nuxt parziale che può essere composta con l'applicazione principale.

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  extends: [
    "./layers/base-ui",      // Layer locale
    "nuxt-seo-utils",        // Layer da npm
    "github:team/shared-layer"  // Layer da GitHub
  ]
});
```

```
layers/
  base-ui/
    nuxt.config.ts
    components/
      BaseButton.vue
      BaseCard.vue
      BaseInput.vue
    composables/
      useTheme.ts
    assets/
      styles/
        tokens.css
```

I layers permettono di condividere codice tra più applicazioni Nuxt di un'organizzazione senza ricorrere a pacchetti npm separati. Il layer base può definire componenti UI, stili, composables e configurazioni che vengono ereditati da tutte le applicazioni che lo estendono. La risoluzione segue un ordine di precedenza: l'applicazione principale sovrascrive i layers, e i layers definiti dopo sovrascrivono quelli precedenti.

### Nitro — Il motore server

Nitro è il server engine di Nuxt 3, ma è anche un framework server indipendente. Nitro compila l'applicazione server in un bundle ottimizzato che può essere deployato su qualsiasi provider: Node.js, Deno, Cloudflare Workers, Vercel Edge Functions, AWS Lambda, Netlify Functions e molti altri. Il deploy su piattaforme edge è supportato nativamente tramite i preset di Nitro.

Nitro offre funzionalità server avanzate come il caching delle risposte, lo storage unificato tramite `useStorage()` (che supporta diversi driver: memory, filesystem, Redis, Cloudflare KV), e la gestione automatica delle rotte con code splitting.

```typescript
// server/api/articoli/[slug].get.ts
// Risposta cached per 60 secondi
export default defineCachedEventHandler(async (event) => {
  const slug = getRouterParam(event, "slug");
  const articolo = await db.articolo.findUnique({ where: { slug } });

  if (!articolo) {
    throw createError({ statusCode: 404, message: "Articolo non trovato" });
  }

  return articolo;
}, { maxAge: 60 });
```

```typescript
// server/utils/storage.ts
// Storage unificato — funziona con memory, filesystem, Redis, ecc.
export async function salvaSessione(id: string, dati: Record<string, unknown>) {
  const storage = useStorage("sessions");
  await storage.setItem(id, dati);
}

export async function leggiSessione(id: string) {
  const storage = useStorage("sessions");
  return await storage.getItem(id);
}
```

---

## Vue Router — Approfondimento

### Navigation Guards avanzati

Oltre al guard globale `beforeEach`, Vue Router offre un sistema granulare di guards che operano a diversi livelli: globale, per-route e per-componente.

**Per-route guards** sono definiti direttamente nella configurazione della route e permettono logica specifica a quella singola route.

```typescript
const routes = [
  {
    path: "/admin/utenti",
    component: () => import("@/views/AdminUtentiView.vue"),
    beforeEnter: [verificaRuoloAdmin, logAccesso],
    meta: { ruoloRichiesto: "admin" }
  }
];

function verificaRuoloAdmin(to, from) {
  const authStore = useAuthStore();
  if (authStore.utente?.ruolo !== "admin") {
    return { name: "non-autorizzato" };
  }
}

function logAccesso(to, from) {
  console.log(`Accesso admin: ${to.fullPath} da ${from.fullPath}`);
}
```

**In-component guards** permettono al componente stesso di controllare la navigazione tramite `onBeforeRouteLeave` e `onBeforeRouteUpdate`.

```vue
<script setup lang="ts">
import { onBeforeRouteLeave, onBeforeRouteUpdate } from "vue-router";

const formModificato = ref(false);

// Avvisa l'utente prima di lasciare la pagina con modifiche non salvate
onBeforeRouteLeave((to, from) => {
  if (formModificato.value) {
    const conferma = window.confirm("Hai modifiche non salvate. Vuoi uscire?");
    if (!conferma) return false;
  }
});

// Reagisce a cambiamenti dei parametri senza smontare il componente
onBeforeRouteUpdate(async (to, from) => {
  if (to.params.id !== from.params.id) {
    await caricaDati(to.params.id as string);
  }
});
</script>
```

### Lazy loading e chunking avanzato

Il lazy loading delle route tramite `() => import("...")` è il meccanismo base per il code splitting. Per applicazioni complesse, Vue Router supporta strategie di chunking avanzate tramite i magic comments di Vite/Webpack.

```typescript
const routes = [
  {
    path: "/dashboard",
    component: () => import(/* webpackChunkName: "dashboard" */ "@/views/DashboardView.vue"),
    children: [
      {
        path: "analisi",
        // Raggruppa sotto-route nello stesso chunk
        component: () => import(/* webpackChunkName: "dashboard" */ "@/views/AnalisiView.vue")
      },
      {
        path: "report",
        component: () => import(/* webpackChunkName: "dashboard" */ "@/views/ReportView.vue")
      }
    ]
  }
];
```

**Prefetch delle route.** Per migliorare la percezione di velocità, è possibile pre-caricare i chunk delle route che l'utente è più probabile che visiti.

```typescript
// Prefetch manuale dopo il caricamento della pagina corrente
router.afterEach((to) => {
  // Prefetch le route collegate nella navigazione
  if (to.name === "prodotti") {
    import("@/views/DettaglioProdottoView.vue");
  }
});
```

### Route dinamiche e pattern avanzati

Vue Router supporta pattern di route flessibili: parametri con regex personalizzate, parametri opzionali, route ripetibili e catch-all.

```typescript
const routes = [
  // Parametro con vincolo regex: solo numeri
  { path: "/prodotti/:id(\\d+)", component: ProdottoView },

  // Parametro opzionale
  { path: "/utenti/:id?", component: UtentiView },

  // Parametri ripetibili (uno o più segmenti)
  { path: "/documenti/:percorso+", component: DocumentoView },

  // Parametri ripetibili (zero o più segmenti)
  { path: "/file/:percorso*", component: FileView },

  // Catch-all con parametro nominato
  { path: "/:pathMatch(.*)*", name: "non-trovata", component: NotFoundView },

  // Route con alias multipli
  {
    path: "/impostazioni",
    alias: ["/settings", "/preferenze"],
    component: ImpostazioniView
  },

  // Redirect con funzione
  {
    path: "/vecchio-percorso/:id",
    redirect: (to) => ({
      name: "nuovo-percorso",
      params: { id: to.params.id }
    })
  }
];
```

---

## Pattern avanzati dei componenti

### Teleport — Rendering fuori dall'albero dei componenti

Il componente built-in `<Teleport>` permette di renderizzare una porzione di template in un nodo DOM differente dalla posizione del componente nell'albero. È indispensabile per modali, tooltip, drawer e notifiche che devono apparire sopra tutto il contenuto, senza essere vincolati dallo `z-index` e `overflow` dei componenti genitori.

```vue
<!-- ModaleConferma.vue -->
<script setup lang="ts">
const props = defineProps<{
  aperto: boolean;
  titolo: string;
}>();

const emit = defineEmits<{
  conferma: [];
  annulla: [];
}>();
</script>

<template>
  <Teleport to="body">
    <Transition name="modale">
      <div v-if="aperto" class="modale-overlay" @click.self="emit('annulla')">
        <div class="modale-contenuto" role="dialog" aria-modal="true" :aria-label="titolo">
          <h2>{{ titolo }}</h2>
          <slot />
          <div class="modale-azioni">
            <button @click="emit('annulla')">Annulla</button>
            <button @click="emit('conferma')" class="primario">Conferma</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modale-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
</style>
```

**Teleport condizionale.** La proprietà `disabled` di `<Teleport>` permette di controllare dinamicamente se il contenuto deve essere teletrasportato o restare nella sua posizione naturale — utile per componenti che funzionano come modale su mobile ma come pannello inline su desktop.

```vue
<template>
  <Teleport to="body" :disabled="!isMobile">
    <aside class="pannello-filtri">
      <slot />
    </aside>
  </Teleport>
</template>
```

### Suspense e componenti asincroni

`<Suspense>` è un componente built-in che gestisce le dipendenze asincrone nell'albero dei componenti. Quando un componente figlio (o qualsiasi suo discendente) ha un `<script setup>` con un `await` al livello superiore, `<Suspense>` mostra un fallback finché tutte le promesse asincrone non si risolvono.

```vue
<!-- DashboardLayout.vue -->
<template>
  <Suspense>
    <template #default>
      <DashboardContent />
    </template>
    <template #fallback>
      <div class="scheletro-caricamento">
        <ScheletroGrafico />
        <ScheletroTabella />
        <ScheletroStatistiche />
      </div>
    </template>
  </Suspense>
</template>
```

```vue
<!-- DashboardContent.vue — Componente asincrono -->
<script setup lang="ts">
// Questo await rende il componente asincrono
// Suspense mostrerà il fallback finché non si risolve
const statistiche = await fetch("/api/statistiche").then((r) => r.json());
const grafici = await fetch("/api/grafici").then((r) => r.json());
</script>

<template>
  <div class="dashboard">
    <GraficoVendite :dati="grafici.vendite" />
    <TabellaOrdini :dati="statistiche.ordiniRecenti" />
  </div>
</template>
```

**`defineAsyncComponent`** è la funzione per caricare componenti in modo lazy. Combinata con `<Suspense>`, permette di mostrare un placeholder mentre il componente viene scaricato.

```typescript
import { defineAsyncComponent } from "vue";

const EditorRichText = defineAsyncComponent({
  loader: () => import("@/components/EditorRichText.vue"),
  loadingComponent: SpinnerCaricamento,
  errorComponent: ErroreCaricamento,
  delay: 200,     // Mostra il loading solo dopo 200ms
  timeout: 10000  // Errore dopo 10 secondi
});
```

### Slots avanzati — Pattern renderless e compound components

**Renderless components** (componenti senza rendering) espongono logica tramite scoped slot senza imporre alcun markup. Il consumatore ha il pieno controllo del rendering.

```vue
<!-- DataFetcher.vue — Componente renderless -->
<script setup lang="ts" generic="T">
import { ref, watchEffect } from "vue";

const props = defineProps<{ url: string }>();

const dati = ref<T | null>(null) as Ref<T | null>;
const errore = ref<Error | null>(null);
const isCaricamento = ref(true);

watchEffect(async () => {
  isCaricamento.value = true;
  errore.value = null;
  try {
    const risposta = await fetch(props.url);
    if (!risposta.ok) throw new Error(`HTTP ${risposta.status}`);
    dati.value = await risposta.json();
  } catch (e) {
    errore.value = e instanceof Error ? e : new Error("Errore sconosciuto");
  } finally {
    isCaricamento.value = false;
  }
});
</script>

<template>
  <slot :dati="dati" :errore="errore" :isCaricamento="isCaricamento" />
</template>
```

```vue
<!-- Utilizzo — Il consumatore controlla completamente il rendering -->
<template>
  <DataFetcher url="/api/utenti">
    <template #default="{ dati: utenti, errore, isCaricamento }">
      <SkeletonLoader v-if="isCaricamento" />
      <AlertErrore v-else-if="errore" :messaggio="errore.message" />
      <TabellaUtenti v-else :utenti="utenti" />
    </template>
  </DataFetcher>
</template>
```

---

## Testing Vue — Vitest e Vue Test Utils

### Configurazione di Vitest per Vue

Vitest è il test runner raccomandato per progetti Vue con Vite. La configurazione richiede il plugin `@vitejs/plugin-vue` e, opzionalmente, jsdom o happy-dom per simulare l'ambiente browser.

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./test/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov", "html"],
      include: ["src/**/*.{ts,vue}"],
      exclude: ["src/**/*.test.ts", "src/**/*.spec.ts"]
    }
  },
  resolve: {
    alias: { "@": "/src" }
  }
});
```

```typescript
// test/setup.ts
import { config } from "@vue/test-utils";
import { createTestingPinia } from "@pinia/testing";

// Configurazione globale per tutti i test
config.global.plugins = [createTestingPinia({ createSpy: vi.fn })];
```

### Testing dei composables

I composables possono essere testati direttamente creando un componente wrapper minimale oppure, per composables che non dipendono dal ciclo di vita del componente, invocandoli direttamente.

```typescript
// composables/__tests__/usePaginazione.test.ts
import { describe, it, expect } from "vitest";
import { ref } from "vue";
import { usePaginazione } from "@/composables/usePaginazione";
import { withSetup } from "@/test/utils";

describe("usePaginazione", () => {
  it("calcola il numero totale di pagine", () => {
    const [risultato] = withSetup(() => usePaginazione(ref(100), 10));
    expect(risultato.totalePagine.value).toBe(10);
  });

  it("non va oltre l'ultima pagina", () => {
    const [risultato] = withSetup(() => usePaginazione(ref(25), 10));
    risultato.vaiAPagina(3);
    expect(risultato.paginaCorrente.value).toBe(3);

    risultato.paginaSuccessiva();
    expect(risultato.paginaCorrente.value).toBe(3); // Non supera totalePagine
  });

  it("non va sotto la prima pagina", () => {
    const [risultato] = withSetup(() => usePaginazione(ref(50), 10));
    risultato.paginaPrecedente();
    expect(risultato.paginaCorrente.value).toBe(1);
  });
});
```

```typescript
// test/utils.ts — Helper per testare composables
import { createApp, type App } from "vue";

export function withSetup<T>(composable: () => T): [T, App] {
  let risultato!: T;
  const app = createApp({
    setup() {
      risultato = composable();
      return () => {};
    }
  });
  app.mount(document.createElement("div"));
  return [risultato, app];
}
```

### Testing avanzato dei componenti

Oltre ai test base, Vue Test Utils permette di testare scenari complessi: componenti con slot, provide/inject, interazioni asincrone e routing.

```typescript
// components/__tests__/ListaProdotti.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createTestingPinia } from "@pinia/testing";
import ListaProdotti from "@/components/ListaProdotti.vue";
import { useProdottiStore } from "@/stores/prodotti";

describe("ListaProdotti", () => {
  const prodottiMock = [
    { id: 1, nome: "Laptop", prezzo: 999, categoria: "elettronica" },
    { id: 2, nome: "Libro", prezzo: 15, categoria: "libri" }
  ];

  it("mostra uno spinner durante il caricamento", () => {
    const wrapper = mount(ListaProdotti, {
      global: {
        plugins: [
          createTestingPinia({
            initialState: { prodotti: { isCaricamento: true, prodotti: [] } }
          })
        ]
      }
    });

    expect(wrapper.find("[data-test='spinner']").exists()).toBe(true);
    expect(wrapper.find("[data-test='lista']").exists()).toBe(false);
  });

  it("renderizza i prodotti dopo il caricamento", async () => {
    const wrapper = mount(ListaProdotti, {
      global: {
        plugins: [
          createTestingPinia({
            initialState: {
              prodotti: { isCaricamento: false, prodotti: prodottiMock }
            }
          })
        ]
      }
    });

    const items = wrapper.findAll("[data-test='prodotto-item']");
    expect(items).toHaveLength(2);
    expect(items[0].text()).toContain("Laptop");
  });

  it("gestisce lo slot personalizzato per ogni prodotto", () => {
    const wrapper = mount(ListaProdotti, {
      global: {
        plugins: [
          createTestingPinia({
            initialState: {
              prodotti: { isCaricamento: false, prodotti: prodottiMock }
            }
          })
        ]
      },
      slots: {
        item: `<template #item="{ prodotto }">
          <span class="custom">{{ prodotto.nome }}</span>
        </template>`
      }
    });

    expect(wrapper.find(".custom").exists()).toBe(true);
  });
});
```

### Testing dei componenti con provide/inject

```typescript
import { mount } from "@vue/test-utils";
import { TEMA_KEY } from "@/injection-keys";

it("applica il tema iniettato", () => {
  const temaMock = ref({
    colori: { primario: "#ff0000", secondario: "#00ff00", sfondo: "#fff", testo: "#000" },
    tipografia: { fontFamiglia: "Arial", dimensioneBase: 14 },
    modoScuro: false
  });

  const wrapper = mount(ComponenteConTema, {
    global: {
      provide: {
        [TEMA_KEY as symbol]: temaMock
      }
    }
  });

  expect(wrapper.element.style.fontFamily).toBe("Arial");
});
```

---

## VueUse — Libreria di composables essenziali

### Panoramica

VueUse è una raccolta di oltre 200 composables essenziali per Vue 3, creata e mantenuta da Anthony Fu (membro del Vue core team). Fornisce utility pronte all'uso per browser API, sensori, animazioni, stato, rete e molte altre categorie, evitando di riscrivere da zero logica comune.

L'installazione avviene tramite npm:

```bash
npm install @vueuse/core
```

### Categorie principali e composables notevoli

**Browser.** `useStorage` sincronizza un ref con localStorage/sessionStorage in modo reattivo, con serializzazione automatica basata sul tipo di dato. `useClipboard` gestisce la clipboard. `useMediaQuery` traccia le media query CSS in modo reattivo. `useTitle` aggiorna il titolo della pagina.

```vue
<script setup lang="ts">
import { useStorage, useMediaQuery, useTitle } from "@vueuse/core";

// Stato persistito in localStorage — sincronizzato cross-tab
const preferenze = useStorage("app-preferenze", {
  tema: "chiaro",
  lingua: "it",
  notifiche: true
});

// Media query reattiva
const isMobile = useMediaQuery("(max-width: 768px)");
const preferisceAnimazioniRidotte = useMediaQuery("(prefers-reduced-motion: reduce)");

// Titolo pagina reattivo
const titoloPagina = useTitle("La mia app");
</script>
```

**Sensori.** `useIntersectionObserver` rileva quando un elemento entra o esce dal viewport. `useResizeObserver` traccia le dimensioni di un elemento. `useMouse` fornisce la posizione del mouse in tempo reale. `useScroll` traccia la posizione di scroll di un elemento o della finestra.

```vue
<script setup lang="ts">
import { useIntersectionObserver, useScroll } from "@vueuse/core";
import { ref } from "vue";

const target = ref<HTMLElement | null>(null);
const isVisibile = ref(false);

const { stop } = useIntersectionObserver(
  target,
  ([{ isIntersecting }]) => {
    isVisibile.value = isIntersecting;
    if (isIntersecting) {
      // Carica il contenuto solo quando diventa visibile (lazy loading)
      caricaContenuto();
      stop(); // Smetti di osservare dopo il primo caricamento
    }
  },
  { threshold: 0.1 }
);

// Scroll tracking
const { y: scrollY, isScrolling, arrivedState } = useScroll(window);
</script>
```

**Rete.** `useFetch` (la versione VueUse, non quella di Nuxt) offre un wrapper completo per la Fetch API con supporto per abort, refetch, timeout e interceptor. `useWebSocket` gestisce connessioni WebSocket con riconnessione automatica. `useOnline` rileva lo stato della connessione di rete.

**Utility.** `useDebounceFn` e `useThrottleFn` creano versioni debounce/throttle di qualsiasi funzione. `useToggle` crea un booleano con funzione toggle. `useVModel` semplifica la creazione di v-model nei componenti figlio.

```vue
<script setup lang="ts">
import { useDebounceFn, useToggle, useVModel } from "@vueuse/core";

// Debounce per la ricerca
const cercaProdotti = useDebounceFn(async (termine: string) => {
  risultati.value = await fetch(`/api/cerca?q=${termine}`).then((r) => r.json());
}, 300);

// Toggle reattivo
const [mostraFiltri, toggleFiltri] = useToggle(false);
</script>
```

**Integrazione con il ciclo di vita.** VueUse rispetta automaticamente il ciclo di vita dei componenti: i listener vengono rimossi quando il componente viene smontato, i timer vengono cancellati, e le connessioni vengono chiuse. Questo avviene internamente tramite `onUnmounted` e `effectScope`.

**Stato.** `useRefHistory` traccia la cronologia dei cambiamenti di un ref con supporto per undo/redo. `useManualRefHistory` offre lo stesso meccanismo con commit manuali. `useLastChanged` tiene traccia del timestamp dell'ultimo cambiamento. `useAsyncState` semplifica la gestione di operazioni asincrone con stato di caricamento, errore e valore risultante integrati.

```vue
<script setup lang="ts">
import { useRefHistory, useAsyncState } from "@vueuse/core";
import { ref } from "vue";

const testoEditor = ref("Contenuto iniziale");

const { undo, redo, canUndo, canRedo, history } = useRefHistory(testoEditor, {
  capacity: 50 // Mantieni le ultime 50 modifiche
});

// Stato asincrono con gestione automatica di loading/errore
const { state: utenti, isLoading, error, execute: ricarica } = useAsyncState(
  () => fetch("/api/utenti").then((r) => r.json()),
  [],  // valore iniziale
  { resetOnExecute: false }
);
</script>

<template>
  <div>
    <textarea v-model="testoEditor" />
    <button :disabled="!canUndo" @click="undo()">Annulla</button>
    <button :disabled="!canRedo" @click="redo()">Ripeti</button>
    <p>Modifiche nella cronologia: {{ history.length }}</p>
  </div>
</template>
```

**Animazione e timing.** `useTransition` anima valori numerici tra due stati. `useInterval` e `useTimeout` offrono wrapper reattivi per `setInterval` e `setTimeout` con pulizia automatica. `useRafFn` esegue una funzione ad ogni frame di `requestAnimationFrame`.

**Componenti.** VueUse include anche componenti renderless come `<UseMouseInElement>`, `<OnClickOutside>` e `<UseImage>` che wrappano i composables corrispondenti in una forma dichiarativa utilizzabile direttamente nel template, offrendo una alternativa per chi preferisce il pattern a slot rispetto alla Composition API.

---

## Ottimizzazione delle performance

### shallowRef e shallowReactive

Per strutture dati di grandi dimensioni che non richiedono reattività profonda, Vue offre `shallowRef` e `shallowReactive`. Queste API creano stato reattivo solo al livello radice: le modifiche alle proprietà annidate non attivano aggiornamenti automatici. Questo riduce significativamente l'overhead del sistema di reattività per dataset con migliaia di elementi.

```vue
<script setup lang="ts">
import { shallowRef, triggerRef } from "vue";

// Per un dataset di 10.000 righe, shallowRef evita di creare proxy per ogni oggetto annidato
const righeTabella = shallowRef<RigaTabella[]>([]);

async function caricaDati() {
  const dati = await fetch("/api/dati-tabella").then((r) => r.json());
  // Riassegnare il ref attiva l'aggiornamento
  righeTabella.value = dati;
}

function aggiornaRiga(indice: number, campo: string, valore: unknown) {
  // La modifica diretta NON attiva l'aggiornamento con shallowRef
  righeTabella.value[indice][campo] = valore;
  // Forza manualmente l'aggiornamento
  triggerRef(righeTabella);
}
</script>
```

### v-memo — Memoizzazione condizionale nel template

La direttiva `v-memo` permette di saltare condizionalmente l'aggiornamento di sotto-alberi DOM pesanti o liste `v-for`. Vue confronta i valori nell'array di `v-memo` con quelli del render precedente: se sono tutti uguali, l'aggiornamento dell'intero sotto-albero viene saltato.

```vue
<template>
  <!-- Ricalcola il rendering della riga solo quando cambiano id o selezionato -->
  <div v-for="riga in righe" :key="riga.id" v-memo="[riga.id, riga.selezionato]">
    <div class="riga-complessa">
      <CheckboxSelezione :checked="riga.selezionato" />
      <CellaAnteprima :dati="riga" />
      <CellaStatistiche :metriche="riga.metriche" />
      <CellaAzioni :id="riga.id" />
    </div>
  </div>
</template>
```

`v-memo="[]"` con un array vuoto equivale a `v-once` — il contenuto viene renderizzato una sola volta e mai aggiornato. Usa `v-memo` con cautela: se il costo di confronto dell'array supera il costo del re-rendering, `v-memo` diventa controproducente. È efficace su liste lunghe (centinaia o migliaia di elementi) dove ogni elemento ha un rendering costoso.

### Virtual scrolling — Rendering virtualizzato

Per liste con migliaia di elementi, il virtual scrolling renderizza solo gli elementi visibili nel viewport, riducendo drasticamente il numero di nodi DOM. L'utente percepisce una lista continua, ma Vue mantiene in memoria solo i 20-50 elementi attualmente visibili più un buffer sopra e sotto.

La libreria più usata nell'ecosistema Vue è `vue-virtual-scroller`. Un'alternativa leggera è `@tanstack/vue-virtual`.

```bash
npm install @tanstack/vue-virtual
```

```vue
<script setup lang="ts">
import { useVirtualizer } from "@tanstack/vue-virtual";
import { ref } from "vue";

const contenitore = ref<HTMLElement | null>(null);

const elementi = ref(Array.from({ length: 50000 }, (_, i) => ({
  id: i,
  nome: `Elemento ${i}`,
  descrizione: `Descrizione dell'elemento numero ${i}`
})));

const virtualizer = useVirtualizer({
  count: elementi.value.length,
  getScrollElement: () => contenitore.value,
  estimateSize: () => 60,
  overscan: 5
});
</script>

<template>
  <div ref="contenitore" class="lista-virtuale" style="height: 600px; overflow-y: auto;">
    <div :style="{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }">
      <div
        v-for="item in virtualizer.getVirtualItems()"
        :key="item.key"
        :style="{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: `${item.size}px`,
          transform: `translateY(${item.start}px)`
        }"
      >
        <div class="elemento-lista">
          <strong>{{ elementi[item.index].nome }}</strong>
          <p>{{ elementi[item.index].descrizione }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
```

### Altre tecniche di ottimizzazione

**`KeepAlive` per caching dei componenti.** Il componente `<KeepAlive>` mantiene in cache i componenti quando vengono rimossi dal DOM, preservandone lo stato. Quando l'utente ritorna, il componente viene riattivato dalla cache senza ricrearlo. Utile per tab, wizard multistep e navigazione con frequenti ritorni.

```vue
<template>
  <KeepAlive :max="5" :include="['DashboardView', 'ImpostazioniView']">
    <RouterView />
  </KeepAlive>
</template>
```

**Chunking dei componenti pesanti.** Per componenti che includono dipendenze pesanti (editor di codice, grafici, mappe), usa `defineAsyncComponent` per caricarli solo quando necessari.

**Ottimizzazione delle computed con large dataset.** Per computed che operano su grandi array, considera tecniche di normalizzazione dei dati (oggetti indicizzati per ID invece di array) per ridurre il costo dei lookup.

```typescript
// Invece di un array, normalizza i dati per accesso O(1)
const prodottiPerId = computed(() => {
  const mappa: Record<number, Prodotto> = {};
  for (const p of prodotti.value) {
    mappa[p.id] = p;
  }
  return mappa;
});

// Accesso diretto: O(1) invece di O(n)
const prodottoSelezionato = computed(() => prodottiPerId.value[idSelezionato.value]);
```

---

## TypeScript con Vue

### Tipizzazione dei componenti

Vue 3 è scritto in TypeScript e offre un supporto di tipizzazione di prima classe. Con `<script setup lang="ts">` e `defineProps<T>()`, le props vengono tipizzate staticamente senza costo runtime aggiuntivo.

**Props generiche.** Vue 3.3 ha introdotto i componenti generici tramite l'attributo `generic` su `<script setup>`, permettendo di creare componenti riutilizzabili che preservano i tipi dei dati che gestiscono.

```vue
<!-- ListaOrdinabile.vue -->
<script setup lang="ts" generic="T extends { id: number }">
const props = defineProps<{
  items: T[];
  chiaveOrdinamento: keyof T;
  direzione?: "asc" | "desc";
}>();

const emit = defineEmits<{
  seleziona: [item: T];
  ordina: [chiave: keyof T];
}>();

const itemsOrdinati = computed(() => {
  const dir = props.direzione === "desc" ? -1 : 1;
  return [...props.items].sort((a, b) => {
    const va = a[props.chiaveOrdinamento];
    const vb = b[props.chiaveOrdinamento];
    if (va < vb) return -1 * dir;
    if (va > vb) return 1 * dir;
    return 0;
  });
});
</script>

<template>
  <ul>
    <li v-for="item in itemsOrdinati" :key="item.id" @click="emit('seleziona', item)">
      <slot :item="item" />
    </li>
  </ul>
</template>
```

```vue
<!-- Utilizzo — TypeScript infierisce T come Prodotto -->
<template>
  <ListaOrdinabile
    :items="prodotti"
    chiave-ordinamento="prezzo"
    direzione="desc"
    @seleziona="mostraDettaglio"
  >
    <template #default="{ item }">
      <!-- item è tipizzato come Prodotto -->
      {{ item.nome }} — {{ item.prezzo }} EUR
    </template>
  </ListaOrdinabile>
</template>
```

### Tipizzazione avanzata di emits, slots e provide/inject

```typescript
// Tipizzazione degli slot con defineSlots (Vue 3.3+)
const slots = defineSlots<{
  default(props: { item: Prodotto; indice: number }): unknown;
  header(): unknown;
  empty(): unknown;
}>();
```

```typescript
// Tipizzazione di RouteMeta per Vue Router
declare module "vue-router" {
  interface RouteMeta {
    richiedeAuth?: boolean;
    ruoloRichiesto?: "admin" | "editor" | "viewer";
    titolo?: string;
    breadcrumb?: string;
  }
}
```

```typescript
// Configurazione tsconfig.json consigliata per Vue 3
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "preserve",
    "paths": { "@/*": ["./src/*"] },
    "types": ["vite/client", "vitest/globals"]
  },
  "include": ["src/**/*.ts", "src/**/*.vue", "env.d.ts"]
}
```

---

## Vapor Mode

### Il futuro di Vue senza Virtual DOM

Vapor Mode è una modalità di compilazione sperimentale introdotta con Vue 3.6 che elimina completamente il Virtual DOM. Invece di creare un albero virtuale di nodi, confrontarlo con il precedente e applicare le differenze (il processo noto come "diffing" e "patching"), Vapor Mode compila i template in codice imperativo che aggiorna direttamente i nodi DOM reali. Il risultato è un approccio a reattività granulare simile a quello di Solid.js.

**Perché Vapor Mode è significativo.** Il Virtual DOM è stato una delle innovazioni più importanti dei framework JavaScript moderni, ma comporta un costo: ad ogni cambiamento di stato, l'intero sotto-albero del componente viene rieseguito per generare il nuovo albero virtuale, che viene poi confrontato con quello precedente. Per la maggior parte delle applicazioni questo costo è trascurabile, ma per interfacce con aggiornamenti frequenti e migliaia di nodi (dashboard real-time, tabelle di dati, visualizzazioni) diventa un collo di bottiglia.

Vapor Mode elimina questo overhead compilando ogni binding reattivo in un'operazione DOM diretta. In benchmark con 10.000 aggiornamenti semplici, Vapor Mode ha dimostrato tempi di circa 12ms con 8MB di memoria, rispetto ai 45ms e 24MB della modalità tradizionale con Virtual DOM.

**Adozione graduale.** Vapor Mode è progettato per coesistere con i componenti Vue tradizionali. Un'applicazione può avere componenti Vapor e componenti con Virtual DOM nella stessa pagina. Questo permette una migrazione graduale: i componenti critici per le performance possono essere convertiti a Vapor mentre il resto dell'applicazione continua a funzionare normalmente. Un componente Vapor può essere figlio di un componente tradizionale e viceversa.

**Stato attuale.** Al momento della stesura (maggio 2026), Vapor Mode è in fase beta avanzata con Vue 3.6. Supporta la maggior parte delle funzionalità di Vue — componenti, reattività, direttive, slot — con alcune limitazioni residue su funzionalità avanzate come `<Transition>` e `<KeepAlive>`. Per nuovi progetti che richiedono performance critiche, Vapor Mode è già sperimentabile in produzione con cautela.

**Come funziona internamente.** Nella modalità tradizionale, un template Vue come `<p>{{ messaggio }}</p>` viene compilato in una funzione di rendering che crea un nodo virtuale (`h('p', messaggio.value)`). Ad ogni cambiamento di `messaggio`, l'intera funzione di rendering viene rieseguita, il nuovo albero virtuale viene confrontato con il precedente, e solo le differenze vengono applicate al DOM reale. In Vapor Mode, lo stesso template viene compilato in codice imperativo: il compilatore genera un `document.createElement('p')`, lo inserisce nel DOM, e crea un effetto reattivo che aggiorna direttamente il `textContent` del nodo `<p>` quando `messaggio` cambia. Non c'è nessun albero virtuale, nessun confronto, nessun overhead.

**Interoperabilità.** L'aspetto più rilevante per l'adozione è che Vapor Mode non richiede una migrazione "tutto o niente". Un componente Vapor può essere importato e utilizzato dentro un componente tradizionale e viceversa. Questo significa che un team può iniziare convertendo i componenti più critici per le performance — tabelle dati con migliaia di righe, dashboard con aggiornamenti real-time, visualizzazioni complesse — mentre il resto dell'applicazione continua a funzionare con il Virtual DOM tradizionale. Il confine tra i due mondi è trasparente per lo sviluppatore.

**Quando non serve Vapor Mode.** La maggior parte delle applicazioni Vue non ha bisogno di Vapor Mode. Il Virtual DOM di Vue 3 è già altamente ottimizzato grazie al compilatore che analizza staticamente i template e applica ottimizzazioni come lo static hoisting, il patch flag system e il tree flattening. Vapor Mode diventa rilevante quando l'applicazione ha requisiti di performance estremi: aggiornamenti a 60fps di centinaia di nodi, rendering di dataset con decine di migliaia di elementi, o vincoli di memoria su dispositivi embedded.

---

## Transizioni e animazioni

### Sistema di transizioni built-in

Vue offre due componenti built-in per le animazioni: `<Transition>` per singoli elementi e `<TransitionGroup>` per liste di elementi. Questi componenti applicano automaticamente classi CSS durante le fasi di ingresso (enter) e uscita (leave) di un elemento dal DOM.

```vue
<template>
  <button @click="mostra = !mostra">Toggle</button>

  <Transition name="sfuma" mode="out-in">
    <div v-if="mostra" class="contenuto">
      Contenuto con transizione
    </div>
  </Transition>
</template>

<style>
.sfuma-enter-active,
.sfuma-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.sfuma-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.sfuma-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
```

**Le sei classi di transizione.** Vue applica automaticamente sei classi durante il ciclo di una transizione. Per una transizione chiamata `sfuma`: `sfuma-enter-from` (stato iniziale ingresso), `sfuma-enter-active` (fase attiva ingresso), `sfuma-enter-to` (stato finale ingresso), `sfuma-leave-from` (stato iniziale uscita), `sfuma-leave-active` (fase attiva uscita), `sfuma-leave-to` (stato finale uscita).

**`<TransitionGroup>` per liste animate.** A differenza di `<Transition>`, `<TransitionGroup>` renderizza un elemento reale (di default `<span>`, configurabile con la prop `tag`). Supporta la classe `*-move` per animare il riposizionamento degli elementi durante riordinamenti.

```vue
<script setup lang="ts">
import { ref, computed } from "vue";

const elementi = ref([
  { id: 1, nome: "Primo" },
  { id: 2, nome: "Secondo" },
  { id: 3, nome: "Terzo" }
]);

function aggiungi() {
  const nuovoId = Math.max(...elementi.value.map((e) => e.id)) + 1;
  elementi.value.push({ id: nuovoId, nome: `Elemento ${nuovoId}` });
}

function rimuovi(id: number) {
  elementi.value = elementi.value.filter((e) => e.id !== id);
}

function mescola() {
  elementi.value = [...elementi.value].sort(() => Math.random() - 0.5);
}
</script>

<template>
  <button @click="aggiungi">Aggiungi</button>
  <button @click="mescola">Mescola</button>

  <TransitionGroup name="lista" tag="ul">
    <li v-for="el in elementi" :key="el.id" @click="rimuovi(el.id)">
      {{ el.nome }}
    </li>
  </TransitionGroup>
</template>

<style>
.lista-enter-active,
.lista-leave-active {
  transition: all 0.4s ease;
}

.lista-enter-from,
.lista-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* Animazione FLIP per il riposizionamento durante il riordinamento */
.lista-move {
  transition: transform 0.4s ease;
}

/* Rimuove dal layout flow durante l'uscita per permettere il FLIP */
.lista-leave-active {
  position: absolute;
}
</style>
```

### Transizioni con JavaScript hooks

Per animazioni complesse che richiedono librerie come GSAP, Vue permette di usare hooks JavaScript al posto (o in aggiunta) delle classi CSS.

```vue
<template>
  <Transition
    @before-enter="primaIngresso"
    @enter="ingresso"
    @after-enter="dopoIngresso"
    @leave="uscita"
    :css="false"
  >
    <div v-if="mostra" class="elemento-animato">Contenuto</div>
  </Transition>
</template>

<script setup lang="ts">
import gsap from "gsap";

function primaIngresso(el: Element) {
  gsap.set(el, { opacity: 0, scale: 0.8, y: 20 });
}

function ingresso(el: Element, done: () => void) {
  gsap.to(el, {
    opacity: 1,
    scale: 1,
    y: 0,
    duration: 0.5,
    ease: "back.out(1.7)",
    onComplete: done
  });
}

function dopoIngresso(el: Element) {
  // Pulizia dopo l'animazione
}

function uscita(el: Element, done: () => void) {
  gsap.to(el, {
    opacity: 0,
    scale: 0.8,
    y: -20,
    duration: 0.3,
    ease: "power2.in",
    onComplete: done
  });
}
</script>
```

### Transizioni tra route

Vue Router si integra con `<Transition>` tramite `<RouterView>` per animare le transizioni tra le pagine.

```vue
<template>
  <RouterView v-slot="{ Component, route }">
    <Transition :name="route.meta.transizione || 'sfuma'" mode="out-in">
      <component :is="Component" :key="route.path" />
    </Transition>
  </RouterView>
</template>
```

---

## Accessibilità (a11y)

### Principi fondamentali per Vue

L'accessibilità web (a11y, abbreviazione di "accessibility" con 11 lettere tra la "a" e la "y") garantisce che le applicazioni siano utilizzabili da tutti gli utenti, incluse persone con disabilità visive, motorie, uditive o cognitive. Vue non aggiunge barriere intrinseche all'accessibilità, ma il modello a componenti richiede attenzione specifica per garantire che il risultato HTML renderizzato sia accessibile.

**HTML semantico prima di tutto.** La regola fondamentale dell'accessibilità in Vue è la stessa del web in generale: usa elementi HTML semantici. Un `<button>` è preferibile a un `<div @click>` perché è nativamente focusabile, attivabile da tastiera (Enter e Spazio) e annunciato correttamente dagli screen reader. Un `<nav>` è preferibile a un `<div class="navigazione">`. Un `<main>` indica il contenuto principale della pagina.

```vue
<!-- CORRETTO: HTML semantico con ARIA dove necessario -->
<template>
  <nav aria-label="Navigazione principale">
    <ul role="menubar">
      <li v-for="voce in menu" :key="voce.id" role="none">
        <RouterLink
          :to="voce.percorso"
          role="menuitem"
          :aria-current="route.path === voce.percorso ? 'page' : undefined"
        >
          {{ voce.etichetta }}
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>
```

### Gestione del focus

La gestione del focus è una delle sfide principali nelle SPA Vue. Quando la navigazione client-side cambia il contenuto della pagina senza un ricaricamento completo, gli screen reader e gli utenti da tastiera possono perdere il contesto.

```ts
// composables/useFocusTrap.ts
import { computed, onUnmounted, type Ref } from "vue";

export function useFocusTrap(containerRef: Ref<HTMLElement | null>) {
  const elementiFocusabili = computed(() => {
    if (!containerRef.value) return [];
    return Array.from(
      containerRef.value.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )
    );
  });

  function gestisciTab(evento: KeyboardEvent) {
    const elementi = elementiFocusabili.value;
    if (elementi.length === 0) return;

    const primo = elementi[0];
    const ultimo = elementi[elementi.length - 1];

    if (evento.shiftKey && document.activeElement === primo) {
      evento.preventDefault();
      ultimo.focus();
    } else if (!evento.shiftKey && document.activeElement === ultimo) {
      evento.preventDefault();
      primo.focus();
    }
  }

  function attiva() {
    document.addEventListener("keydown", gestisciTab);
    elementiFocusabili.value[0]?.focus();
  }

  function disattiva() {
    document.removeEventListener("keydown", gestisciTab);
  }

  onUnmounted(disattiva);

  return { attiva, disattiva };
}
```

### Rispetto di prefers-reduced-motion

Gli utenti che hanno attivato l'impostazione di sistema "riduci movimento" si aspettano che le animazioni siano minimizzate o eliminate. Vue non gestisce questo automaticamente — spetta allo sviluppatore rispettare questa preferenza.

```vue
<script setup lang="ts">
import { useMediaQuery } from "@vueuse/core";

const prefersReducedMotion = useMediaQuery("(prefers-reduced-motion: reduce)");
</script>

<template>
  <Transition :name="prefersReducedMotion ? '' : 'sfuma'" mode="out-in">
    <component :is="componenteCorrente" />
  </Transition>
</template>

<style>
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
```

### Annunci di navigazione per screen reader

Nuxt 3 include un Route Announcer automatico che annuncia i cambi di pagina agli screen reader tramite un `<div>` nascosto con `aria-live="assertive"`. In un'applicazione Vue pura con Vue Router, questo comportamento va implementato manualmente.

```typescript
// composables/useRouteAnnouncer.ts
import { watch, ref, onMounted } from "vue";
import { useRoute } from "vue-router";

export function useRouteAnnouncer() {
  const route = useRoute();
  const annuncio = ref("");

  onMounted(() => {
    const announcerEl = document.createElement("div");
    announcerEl.setAttribute("aria-live", "assertive");
    announcerEl.setAttribute("aria-atomic", "true");
    announcerEl.setAttribute("role", "status");
    announcerEl.style.cssText =
      "position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap";
    document.body.appendChild(announcerEl);

    watch(
      () => route.fullPath,
      () => {
        const titolo = route.meta.titolo ?? document.title;
        announcerEl.textContent = "";
        requestAnimationFrame(() => {
          announcerEl.textContent = `Navigato a: ${titolo}`;
        });
      }
    );
  });
}
```

### Checklist accessibilità per componenti Vue

- **Labels dei form:** ogni `<input>`, `<select>` e `<textarea>` deve avere un `<label>` associato tramite `for`/`id` o tramite `aria-label` / `aria-labelledby`.
- **Attributi ARIA:** usa `aria-expanded` per menu a tendina, `aria-selected` per tab, `aria-checked` per checkbox personalizzati, `aria-describedby` per istruzioni aggiuntive.
- **Navigazione da tastiera:** tutti i controlli interattivi devono essere accessibili tramite Tab e attivabili tramite Enter/Spazio. I menu devono supportare le frecce direzionali.
- **Contrasto colori:** rapporto minimo 4.5:1 per testo normale, 3:1 per testo grande (18px+ o 14px+ bold).
- **Skip links:** fornisci un link "Salta al contenuto" all'inizio della pagina per permettere agli utenti da tastiera di saltare la navigazione ripetitiva.
- **Contenuto dinamico:** usa `aria-live` per regioni che cambiano contenuto dinamicamente (notifiche, risultati di ricerca live, messaggi di errore).
- **Immagini:** ogni `<img>` deve avere un attributo `alt` descrittivo, o `alt=""` se l'immagine è decorativa.

---

## Esercizi

### Esercizio 1 — Componenti con Composition API e TypeScript

**Obiettivo:** costruire componenti riutilizzabili con `<script setup>`, props tipizzate e emit dichiarativi.

Creare una libreria di componenti per un sistema di notifiche:

- Un componente `NotificationCard` con props tipizzate tramite `defineProps<{ title: string; message: string; type: 'info' | 'success' | 'warning' | 'error'; dismissible?: boolean }>()`
- Un componente `NotificationStack` che gestisca una lista di notifiche con transizioni di ingresso e uscita (`<TransitionGroup>`)
- Emettere un evento `dismiss` tipizzato con `defineEmits<{ dismiss: [id: string] }>()`
- Usare slot con nome (`#icon`, `#actions`) per la personalizzazione del contenuto
- Le notifiche devono auto-chiudersi dopo un timeout configurabile tramite prop
- Scrivere test con Vue Test Utils e Vitest che verifichino il rendering condizionale, gli emit e il timeout
- Compilare con `strict: true` e zero errori TypeScript

### Esercizio 2 — Composables per Logica Riutilizzabile

**Obiettivo:** estrarre logica complessa in composables testabili e componibili.

Implementare un set di composables per un'applicazione:

- `useFetch<T>(url: MaybeRef<string>)` — gestisce loading, errore, dati, abort e refetch automatico quando l'URL cambia (watch)
- `usePagination(totalItems: Ref<number>, pageSize?: number)` — espone `currentPage`, `totalPages`, `nextPage()`, `prevPage()`, `goToPage(n)`
- `useLocalStorage<T>(key: string, defaultValue: T)` — sincronizza un `ref` con `localStorage`, gestisce serializzazione/deserializzazione e eventi `storage` cross-tab
- `useDebouncedRef<T>(value: T, delay: number)` — un ref che aggiorna il valore esposto solo dopo il delay di debounce
- Ogni composable deve essere testato in isolamento con Vitest, montando un componente wrapper minimale quando necessario
- Documentare le firme e i tipi di ritorno con JSDoc

### Esercizio 3 — State Management con Pinia

**Obiettivo:** gestire stato applicativo complesso con Pinia, includendo azioni asincrone, getters derivati e persistenza.

Creare un'applicazione e-commerce con due store Pinia:

- `useCartStore` — gestisce prodotti nel carrello, quantita, totale calcolato come getter, azioni per aggiungere/rimuovere/svuotare
- `useProductStore` — carica prodotti da un'API (simulata con `msw`), supporta filtri per categoria e ricerca, paginazione lato client
- I getter devono essere derivati (`computed`) e non duplicare dati gia presenti nello state
- Implementare la persistenza del carrello con `pinia-plugin-persistedstate`
- Scrivere test per entrambi gli store con `createPinia()` isolato per ogni test
- Testare le azioni asincrone mockando le chiamate API
- Verificare che lo stato sia reattivo: modifiche allo store devono riflettersi automaticamente nei componenti

### Esercizio 4 — Routing e Navigazione con Vue Router

**Obiettivo:** implementare un sistema di routing completo con navigazione protetta, lazy loading e parametri tipizzati.

Creare un'applicazione multi-pagina con Vue Router:

- Almeno 5 route: home, lista prodotti, dettaglio prodotto (`/prodotti/:id`), dashboard (protetta), login
- Implementare lazy loading per ogni route con `() => import(...)`
- Creare un navigation guard globale (`beforeEach`) che verifichi l'autenticazione per le route protette
- Usare `<RouterView>` con `<Transition>` per animazioni di transizione tra le pagine
- Implementare una pagina 404 come catch-all route
- Gestire i meta-dati delle route (`meta: { requiresAuth: true, title: string }`) con tipizzazione estesa di `RouteMeta`
- Aggiornare il titolo della pagina (`document.title`) tramite un guard `afterEach`
- Test E2E con Playwright per il flusso di navigazione: login, accesso a pagina protetta, logout e redirect

### Esercizio 5 — Applicazione Full-Stack con Nuxt 3

**Obiettivo:** costruire un'applicazione completa con Nuxt 3, sfruttando SSR, API routes e auto-import.

Creare un'applicazione di gestione note con Nuxt 3:

- Struttura: pagine per lista note, creazione, modifica, dettaglio
- Usare `useFetch` / `useAsyncData` di Nuxt per il data fetching con SSR
- Creare API routes in `server/api/` con validazione Zod dei body delle richieste
- Implementare autenticazione con sessioni lato server (cookie httpOnly)
- Usare il middleware di Nuxt per proteggere le pagine riservate
- Configurare SEO con `useHead` e `useSeoMeta` per ogni pagina
- Applicare auto-import per componenti, composables e utility
- Deployare con un adapter (Vercel, Netlify o Node) e verificare il corretto funzionamento in produzione
- Test unitari per le API routes e test E2E per i flussi utente principali

---

## Letture e Riferimenti

### Documentazione ufficiale

- **Vue.js Documentation** — guida ufficiale completa con tutorial interattivo e API reference. https://vuejs.org/ (consultato: 2026-05-24)
- **Vue.js API Reference** — riferimento dettagliato di Composition API, Options API e built-in. https://vuejs.org/api/ (consultato: 2026-05-24)
- **Pinia Documentation** — state management ufficiale per Vue 3. https://pinia.vuejs.org/ (consultato: 2026-05-24)
- **Vue Router Documentation** — routing ufficiale per applicazioni Vue. https://router.vuejs.org/ (consultato: 2026-05-24)
- **Nuxt 3 Documentation** — framework full-stack basato su Vue 3 con SSR e auto-import. https://nuxt.com/docs (consultato: 2026-05-24)
- **VeeValidate** — validazione form per Vue con supporto a Zod e Yup. https://vee-validate.logaretm.com/v4/ (consultato: 2026-05-24)
- **Vue Test Utils** — utility ufficiali per il testing di componenti Vue. https://test-utils.vuejs.org/ (consultato: 2026-05-24)

### Libri e approfondimenti

- Hanchett E., Listwon B., *Vue.js in Action*, Manning Publications, 2019.
- Macrae C., *Vue.js: Up and Running*, O'Reilly Media, 2018.
- Documentazione ufficiale Vue — *Vue.js Tutorial* — tutorial interattivo passo-passo. https://vuejs.org/tutorial/

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [06 — TypeScript](06-typescript.md) | Prerequisito: Composition API + `<script setup>` beneficiano fortemente della tipizzazione TypeScript |
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Basi necessarie per comprendere reattivita, proxy, destructuring e il modello a eventi in Vue |
| [09 — Svelte e SvelteKit](09-svelte.md) | Framework alternativo con approccio a compilazione: confronto architetturale e di paradigma reattivo |
| [15 — Testing Web](15-testing-web.md) | Strategie di testing per componenti Vue: unit con Vue Test Utils, integrazione, E2E con Playwright |
| [17 — Performance Web](17-performance-web.md) | Ottimizzazione dei bundle Vue: tree-shaking della Composition API, lazy loading delle route, Core Web Vitals |
| [14 — Sicurezza Web](14-sicurezza-web.md) | Prevenzione XSS nei template Vue, sanitizzazione di `v-html`, CSP e protezione CSRF nei form |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Composition API** | API introdotta in Vue 3 che permette di organizzare la logica del componente per funzionalita anziche per opzione, usando funzioni come `ref`, `computed` e `watch`. |
| **`<script setup>`** | Zucchero sintattico per la Composition API che elimina il boilerplate: variabili e funzioni dichiarate nel blocco sono automaticamente disponibili nel template. |
| **`ref`** | Primitiva reattiva che avvolge un valore in un oggetto con proprieta `.value`, permettendo a Vue di tracciarne le modifiche. |
| **`reactive`** | Funzione che rende un oggetto profondamente reattivo tramite Proxy, senza necessita di `.value` ma con limitazioni sulla destrutturazione. |
| **`computed`** | Proprieta derivata memoizzata che ricalcola automaticamente il proprio valore solo quando le dipendenze reattive cambiano. |
| **Composable** | Funzione con convenzione `use*` che incapsula e riutilizza logica stateful usando la Composition API. Equivalente concettuale dei custom hooks di React. |
| **Pinia** | Libreria ufficiale di state management per Vue 3, sostituta di Vuex. Supporta store tipizzati, DevTools e hot module replacement. |
| **Vue Router** | Libreria ufficiale di routing per Vue che gestisce navigazione client-side, route annidate, navigation guard e lazy loading. |
| **Direttiva** | Attributo speciale con prefisso `v-` (es. `v-if`, `v-for`, `v-model`, `v-bind`) che applica comportamento reattivo al DOM. |
| **`v-model`** | Direttiva che crea un binding bidirezionale tra un input del template e una variabile reattiva, con supporto per componenti personalizzati tramite `defineModel`. |
| **Slot** | Meccanismo per passare contenuto template da un componente genitore a un componente figlio, con supporto per slot con nome e scoped slot. |
| **`watch` / `watchEffect`** | API per eseguire effetti collaterali in risposta a cambiamenti di stato: `watch` osserva sorgenti specifiche, `watchEffect` traccia automaticamente le dipendenze. |
| **Teleport** | Componente built-in che renderizza il proprio contenuto in un nodo DOM diverso dalla posizione nell'albero dei componenti, utile per modali e tooltip. |
| **Nuxt** | Framework full-stack basato su Vue che aggiunge SSR, SSG, auto-import, routing basato su file system e API routes server-side. |
