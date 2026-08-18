# Tutorial 08 — Vue 3: Dal Principiante all'Esperto

> **Companion a:** `08-vue.md`
> **Scope:** Single File Component, template e direttive, `ref` e `reactive`, `computed` e `watch`, Composition API con `<script setup>`, props ed emit tipizzati, `v-model` sui componenti, slot, provide/inject, composables, ciclo di vita, Pinia, Vue Router, Teleport e Transition, il sistema di reattività dall'interno, Vapor Mode, testing con Vitest e Testing Library
> **Prerequisiti:** `tutorial_04_javascript_fondamenti.md`, `tutorial_06_typescript.md`; utile aver letto `tutorial_07_react.md` per il confronto
> **Durata stimata:** 24-30 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Vue 3.5+ · TypeScript 5.6+ · Vite · Pinia 2 · Vue Router 4 · Vitest

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Cosa cambia rispetto a React](#a1-cosa-cambia-rispetto-a-react)
  - [A2. Il Single File Component](#a2-il-single-file-component)
  - [A3. `ref` e `reactive`](#a3-ref-e-reactive)
  - [A4. Il template e le direttive](#a4-il-template-e-le-direttive)
  - [A5. `computed`: i valori derivati](#a5-computed-i-valori-derivati)
  - [A6. Props ed emit](#a6-props-ed-emit)
  - [A7. `v-model` e i form](#a7-v-model-e-i-form)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. Come funziona la reattività](#b1-come-funziona-la-reattività)
  - [B2. `watch` e `watchEffect`](#b2-watch-e-watcheffect)
  - [B3. Il ciclo di vita](#b3-il-ciclo-di-vita)
  - [B4. Slot: la composizione in Vue](#b4-slot-la-composizione-in-vue)
  - [B5. `provide` e `inject`](#b5-provide-e-inject)
  - [B6. I composables](#b6-i-composables)
  - [B7. Pinia](#b7-pinia)
  - [B8. Vue Router](#b8-vue-router)
  - [B9. Teleport, Transition e `<KeepAlive>`](#b9-teleport-transition-e-keepalive)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: la dashboard, in Vue](#c2-mini-progetto-la-dashboard-in-vue)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. Il sistema di reattività dall'interno](#d1-il-sistema-di-reattività-dallinterno)
  - [D2. Performance e Vapor Mode](#d2-performance-e-vapor-mode)
  - [D3. Componenti accessibili in Vue](#d3-componenti-accessibili-in-vue)
  - [D4. Testare i componenti Vue](#d4-testare-i-componenti-vue)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                               VUE 3
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
    ┌─────────▼──────────┐                ┌─────────▼──────────┐
    │   LA REATTIVITÀ    │                │    IL TEMPLATE     │
    │                    │                │                    │
    │  ref(valore)       │                │  {{ interpolazione}}│
    │   └ .value in JS   │                │  v-bind  :prop     │
    │   └ auto nel       │                │  v-on    @evento   │
    │     template       │                │  v-model           │
    │  reactive(oggetto) │                │  v-if / v-else     │
    │   └ Proxy          │                │  v-for  :key       │
    │   └ niente .value  │                │  v-show            │
    │   ⚠ si rompe con   │                │                    │
    │     il destructuring│               │  compilato in      │
    │  computed()        │                │  render function   │
    │   └ cache          │                │  ottimizzata       │
    │  watch / watchEffect│               │                    │
    └─────────┬──────────┘                └─────────┬──────────┘
              └──────────────────┬──────────────────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                            │                            │
┌───▼─────────────┐   ┌──────────▼─────────┐   ┌──────────────▼────┐
│  IL COMPONENTE  │   │   COMPOSIZIONE     │   │   ECOSISTEMA      │
│                 │   │                    │   │                   │
│ <script setup>  │   │ slot               │   │ Pinia             │
│ defineProps     │   │  └ nominali        │   │  └ store          │
│ defineEmits     │   │  └ con scope       │   │ Vue Router        │
│ defineModel     │   │ provide / inject   │   │ VueUse            │
│ defineExpose    │   │  └ chiavi tipizzate│   │ Nuxt              │
│                 │   │ composables        │   │                   │
│ ciclo di vita   │   │  └ use*            │   │ Teleport          │
│  onMounted      │   │  └ CONDIVIDONO lo  │   │ Transition        │
│  onUnmounted    │   │    stato se creati │   │ KeepAlive         │
│  ...            │   │    fuori           │   │ Suspense          │
└─────────────────┘   └────────────────────┘   └───────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Cosa cambia rispetto a React

Vue e React risolvono lo stesso problema con due filosofie diverse. Conoscere la differenza rende Vue immediato per chi arriva da React, e viceversa.

```
                    REACT                      VUE

Il componente       una FUNZIONE che           un OGGETTO con un
                    viene richiamata           template compilato
                    a ogni cambiamento

Aggiornamento       ridisegna il               aggiorna SOLO ciò che
                    componente e i figli,      dipende dal dato
                    poi confronta              cambiato

Reattività          esplicita: setState        automatica: assegni,
                    e React ridisegna          e Vue lo sa

Come lo sa          non lo sa: ridisegna       Proxy: intercetta
                    e confronta                lettura e scrittura

Il template         JSX = JavaScript           template = HTML,
                                               compilato e ottimizzato

Memoizzazione       useMemo, useCallback,      quasi mai necessaria:
                    memo — o il Compiler       la reattività è già fine

Stile               CSS-in-JS, Modules,        <style scoped> nel file
                    Tailwind
```

```tsx
// REACT — dichiari che il valore cambia, React ridisegna
function Contatore() {
  const [conteggio, impostaConteggio] = useState(0)
  const doppio = conteggio * 2 // ricalcolato a ogni rendering

  return <button onClick={() => impostaConteggio((c) => c + 1)}>{conteggio} / {doppio}</button>
}
```

```vue
<!-- VUE — assegni, e solo ciò che dipende si aggiorna -->
<script setup lang="ts">
import { ref, computed } from 'vue'

const conteggio = ref(0)
const doppio = computed(() => conteggio.value * 2) // ricalcolato SOLO se conteggio cambia
</script>

<template>
  <button @click="conteggio++">{{ conteggio }} / {{ doppio }}</button>
</template>
```

> **Analogia:** React è una fotografia scattata di nuovo a ogni cambiamento, poi confrontata con la precedente per capire cosa ritoccare. Vue è un impianto elettrico: ogni interruttore è cablato alle lampadine che comanda, e accendendolo si illuminano solo quelle. La fotografia è più semplice da capire; il cablaggio fa meno lavoro.

### Il primo progetto

```powershell
pnpm create vue@latest dashboard-vue
# Rispondi sì a: TypeScript, Router, Pinia, Vitest, ESLint

cd dashboard-vue
pnpm install
pnpm dev
```

---

## A2. Il Single File Component

Un file `.vue` contiene struttura, logica e stile di un componente. Non è una mescolanza di responsabilità: è la stessa responsabilità — un componente — vista da tre angolazioni.

```vue
<!-- src/componenti/SchedaIndicatore.vue -->
<script setup lang="ts">
import { computed } from 'vue'

// Le props: dichiarate con i tipi, senza oggetti di configurazione
const props = defineProps<{
  titolo: string
  valore: number
  variazione?: number
  formato?: 'numero' | 'valuta' | 'percentuale'
}>()

const formattato = computed(() => {
  switch (props.formato ?? 'numero') {
    case 'valuta':
      return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR',
      }).format(props.valore)
    case 'percentuale':
      return `${props.valore.toFixed(1)}%`
    default:
      return new Intl.NumberFormat('it-IT').format(props.valore)
  }
})

const segnoVariazione = computed(() =>
  props.variazione === undefined ? null : props.variazione >= 0 ? 'positiva' : 'negativa',
)
</script>

<template>
  <article class="scheda">
    <p class="scheda__etichetta">{{ titolo }}</p>
    <p class="scheda__valore">{{ formattato }}</p>

    <p v-if="variazione !== undefined" class="scheda__variazione" :data-segno="segnoVariazione">
      <span aria-hidden="true">{{ variazione >= 0 ? '▲' : '▼' }}</span>
      {{ Math.abs(variazione) }}%
      <span class="solo-screen-reader">
        {{ variazione >= 0 ? 'in aumento' : 'in diminuzione' }}
      </span>
    </p>
  </article>
</template>

<!-- scoped: il CSS vale SOLO per questo componente.
     Il compilatore aggiunge un attributo univoco a ogni elemento
     e lo usa nei selettori. -->
<style scoped>
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
  letter-spacing: 0.04em;
}

.scheda__valore {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.scheda__variazione[data-segno='positiva'] {
  color: var(--successo);
}

.scheda__variazione[data-segno='negativa'] {
  color: var(--errore);
}
</style>
```

### `<style scoped>` e i suoi confini

```vue
<style scoped>
/* Vale solo per questo componente */
.titolo {
  font-size: 1.25rem;
}

/* :deep() attraversa il confine, per stilare un componente figlio.
   Da usare con parsimonia: rompe l'incapsulamento. */
:deep(.componente-figlio .interno) {
  color: red;
}

/* :slotted() stila il contenuto passato via slot */
:slotted(p) {
  margin-block: 0.5rem;
}

/* :global() esce dall'ambito */
:global(body) {
  overflow: hidden;
}
</style>
```

```vue
<!-- I CSS Modules, quando servono i nomi in JavaScript -->
<script setup lang="ts">
import { useCssModule } from 'vue'

const stili = useCssModule()
</script>

<template>
  <div :class="stili.contenitore">…</div>
</template>

<style module>
.contenitore {
  padding: 1rem;
}
</style>
```

```vue
<!-- v-bind nel CSS: un valore reattivo diventa una custom property -->
<script setup lang="ts">
import { ref } from 'vue'

const percentuale = ref(62)
const colore = ref('#1d4ed8')
</script>

<template>
  <div class="barra" />
</template>

<style scoped>
.barra {
  /* Il compilatore genera --xxx e la aggiorna quando il ref cambia */
  inline-size: v-bind('percentuale + "%"');
  background: v-bind(colore);
  block-size: 0.5rem;
}
</style>
```

---

## A3. `ref` e `reactive`

Vue ha due modi di rendere reattivo un valore, e la distinzione è la prima cosa che confonde.

```typescript
import { ref, reactive } from 'vue'

// ref: avvolge QUALUNQUE valore, primitivi compresi.
// In JavaScript si accede con .value
const conteggio = ref(0)
console.log(conteggio.value) // 0
conteggio.value++

const utente = ref<Utente | null>(null)
utente.value = { nome: 'Anna' }

// reactive: solo OGGETTI, e senza .value
const stato = reactive({ conteggio: 0, nome: 'Anna' })
console.log(stato.conteggio) // 0
stato.conteggio++
```

### Nel template `.value` sparisce

```vue
<script setup lang="ts">
import { ref } from 'vue'

const conteggio = ref(0)

function incrementa() {
  conteggio.value++ // in JavaScript SERVE .value
}
</script>

<template>
  <!-- Nel template NO: il compilatore lo aggiunge da solo -->
  <p>{{ conteggio }}</p>
  <button @click="conteggio++">Incrementa</button>
</template>
```

### I limiti di `reactive`

```typescript
import { reactive, ref, toRefs } from 'vue'

const stato = reactive({ conteggio: 0, nome: 'Anna' })

// ❌ 1. Il destructuring ROMPE la reattività: si estrae il valore,
//    non il collegamento
const { conteggio } = stato
// conteggio è un numero normale: cambiarlo non aggiorna nulla

// ✅ toRefs conserva il collegamento
const { conteggio: conteggioRef, nome } = toRefs(stato)
conteggioRef.value++ // aggiorna stato.conteggio

// ❌ 2. Non si può riassegnare l'intero oggetto
let statoModificabile = reactive({ a: 1 })
// statoModificabile = reactive({ a: 2 })   // il collegamento si perde

// ✅ Con ref si può
const statoRef = ref({ a: 1 })
statoRef.value = { a: 2 } // funziona

// ❌ 3. Non funziona con i primitivi
// const numero = reactive(0)   // avviso: value cannot be made reactive
```

```
La regola operativa, che evita di doverci pensare:

  USA SEMPRE ref.

  ref funziona con tutto, sopravvive al destructuring
  (passando il ref stesso), si può riassegnare, e il costo
  è scrivere .value in JavaScript.

  reactive è utile in un caso: un oggetto di stato locale
  con molte proprietà che non viene mai riassegnato né
  destrutturato. La documentazione ufficiale raccomanda ref.
```

### Reattività profonda e superficiale

```typescript
import { ref, shallowRef, triggerRef } from 'vue'

// ref è PROFONDO: anche gli oggetti annidati sono reattivi
const profondo = ref({ utente: { indirizzo: { citta: 'Milano' } } })
profondo.value.utente.indirizzo.citta = 'Torino' // reattivo

// shallowRef: solo la sostituzione di .value è reattiva.
// Per strutture grandi che si sostituiscono per intero,
// evita il costo di rendere reattivo l'intero albero.
const superficiale = shallowRef({ righe: milleRighe })
superficiale.value.righe.push(nuova) // NON reattivo
superficiale.value = { righe: [...superficiale.value.righe, nuova] } // reattivo

// Forzare l'aggiornamento quando si è modificato in profondità
triggerRef(superficiale)
```

```typescript
// readonly: una vista non modificabile, per esporre lo stato
import { reactive, readonly } from 'vue'

const statoInterno = reactive({ conteggio: 0 })
export const stato = readonly(statoInterno)
// stato.conteggio++   // avviso in sviluppo, e non modifica nulla
```

---

## A4. Il template e le direttive

```vue
<template>
  <!-- Interpolazione -->
  <p>{{ messaggio }}</p>
  <p>{{ conteggio * 2 }}</p>
  <p>{{ utente?.nome ?? 'Anonimo' }}</p>

  <!-- v-bind: lega un attributo a un'espressione -->
  <img v-bind:src="urlImmagine" v-bind:alt="descrizione" />
  <img :src="urlImmagine" :alt="descrizione" />

  <!-- Forma breve per attributo e variabile omonimi (Vue 3.4+) -->
  <img :src :alt />

  <!-- Legare più attributi insieme -->
  <input v-bind="attributiInput" />

  <!-- v-on: gli eventi -->
  <button v-on:click="salva">Salva</button>
  <button @click="salva">Salva</button>
  <button @click="conteggio++">Incrementa</button>
  <button @click="elimina(riga.id)">Elimina</button>

  <!-- I modificatori: sostituiscono il codice ripetitivo -->
  <form @submit.prevent="invia">…</form>
  <div @click.stop="…">…</div>
  <div @click.self="…">…</div>
  <button @click.once="…">…</button>
  <div @scroll.passive="…">…</div>
  <input @keyup.enter="cerca" @keyup.esc="annulla" />
  <input @keyup.ctrl.s.prevent="salva" />
</template>
```

### Condizionali

```vue
<template>
  <!-- v-if: rimuove dal DOM. Costa di più a commutare,
       meno se la condizione cambia raramente. -->
  <p v-if="stato === 'caricamento'">Caricamento…</p>
  <p v-else-if="stato === 'errore'">Si è verificato un errore.</p>
  <p v-else>{{ dati.length }} risultati</p>

  <!-- v-show: resta nel DOM con display:none.
       Costa il rendering iniziale, poi commutare è gratuito. -->
  <div v-show="pannelloAperto">…</div>

  <!-- template come contenitore invisibile -->
  <template v-if="autenticato">
    <Intestazione />
    <Contenuto />
  </template>
</template>
```

```
v-if o v-show:

  v-if    la condizione cambia raramente, o il contenuto è pesante
          e non deve nemmeno essere creato

  v-show  commutazione frequente, contenuto leggero
          ⚠ display:none lo toglie anche dall'albero di accessibilità
```

### Cicli

```vue
<template>
  <!-- key sempre, e legata al DATO come in React -->
  <ul>
    <li v-for="fattura in fatture" :key="fattura.id">
      {{ fattura.numero }} — {{ fattura.cliente }}
    </li>
  </ul>

  <!-- Con l'indice -->
  <li v-for="(fattura, indice) in fatture" :key="fattura.id">
    {{ indice + 1 }}. {{ fattura.numero }}
  </li>

  <!-- Su un oggetto: valore, chiave, indice -->
  <li v-for="(valore, chiave) in configurazione" :key="chiave">
    {{ chiave }}: {{ valore }}
  </li>

  <!-- Su un intervallo, che parte da 1 -->
  <span v-for="n in 5" :key="n">{{ n }}</span>

  <!-- ⚠ v-if e v-for sullo STESSO elemento: v-if ha priorità
       più alta e non vede la variabile del ciclo -->
  <!-- <li v-for="f in fatture" v-if="!f.pagata">✗ errore</li> -->

  <!-- ✅ Filtrare a monte, con una computed -->
  <li v-for="f in insolute" :key="f.id">{{ f.numero }}</li>

  <!-- ✅ Oppure il template intermedio -->
  <template v-for="f in fatture" :key="f.id">
    <li v-if="!f.pagata">{{ f.numero }}</li>
  </template>
</template>
```

### Classi e stili

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'

const attiva = ref(true)
const errore = ref(false)
const dimensione = ref<'piccolo' | 'grande'>('grande')
</script>

<template>
  <!-- Oggetto: la chiave è la classe, il valore la condizione -->
  <div :class="{ attiva, 'in-errore': errore }">…</div>

  <!-- Array -->
  <div :class="['scheda', `scheda--${dimensione}`, { attiva }]">…</div>

  <!-- Le classi statiche si FONDONO con quelle legate -->
  <div class="scheda" :class="{ attiva }">…</div>

  <!-- Stili: oggetto in camelCase, o kebab fra apici -->
  <div :style="{ backgroundColor: colore, 'font-size': dimensione + 'px' }">…</div>
  <div :style="[stileBase, stileCondizionale]">…</div>
</template>
```

---

## A5. `computed`: i valori derivati

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'

const fatture = ref<Fattura[]>([])
const ricerca = ref('')
const soloInsolute = ref(false)

// computed mette in CACHE: si ricalcola solo se una delle
// dipendenze lette al suo interno cambia
const filtrate = computed(() => {
  const termine = ricerca.value.toLowerCase()

  return fatture.value.filter((f) => {
    if (soloInsolute.value && f.pagata) return false
    return f.cliente.toLowerCase().includes(termine)
  })
})

// Le computed si compongono: totale dipende da filtrate
const totale = computed(() => filtrate.value.reduce((s, f) => s + f.importo, 0))
</script>

<template>
  <input v-model="ricerca" />
  <label><input type="checkbox" v-model="soloInsolute" /> Solo insolute</label>

  <p>{{ filtrate.length }} fatture, {{ totale }} euro</p>
</template>
```

### `computed` contro metodo

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'

const numeri = ref([5, 3, 8, 1])

// computed: calcolata una volta, poi in cache finché numeri non cambia
const ordinati = computed(() => numeri.value.toSorted((a, b) => a - b))

// metodo: eseguito a OGNI rendering che lo chiama
function ordina() {
  return numeri.value.toSorted((a, b) => a - b)
}
</script>

<template>
  <!-- Tre usi, un solo calcolo -->
  <p>{{ ordinati[0] }}</p>
  <p>{{ ordinati.at(-1) }}</p>
  <p>{{ ordinati.length }}</p>

  <!-- Tre usi, TRE calcoli -->
  <p>{{ ordina()[0] }}</p>
</template>
```

### `computed` scrivibile

```typescript
import { computed, ref } from 'vue'

const nome = ref('Anna')
const cognome = ref('Rossi')

const nomeCompleto = computed({
  get: () => `${nome.value} ${cognome.value}`,
  set: (nuovo: string) => {
    const parti = nuovo.trim().split(/\s+/)
    nome.value = parti[0] ?? ''
    cognome.value = parti.slice(1).join(' ')
  },
})

nomeCompleto.value = 'Marco Bianchi'
console.log(nome.value) // 'Marco'
console.log(cognome.value) // 'Bianchi'
```

```typescript
// ❌ Una computed deve essere PURA: nessun effetto collaterale.
//    Gli effetti vanno in watch o watchEffect.
const sbagliata = computed(() => {
  fetch('/api/log') // ✗ effetto collaterale
  return conteggio.value * 2
})
```

---

## A6. Props ed emit

```vue
<!-- src/componenti/Pulsante.vue -->
<script setup lang="ts">
// Props tipizzate: il compilatore genera la validazione
const props = withDefaults(
  defineProps<{
    variante?: 'primario' | 'secondario' | 'pericolo'
    dimensione?: 'piccolo' | 'medio' | 'grande'
    caricamento?: boolean
  }>(),
  {
    variante: 'primario',
    dimensione: 'medio',
    caricamento: false,
  },
)

// Gli eventi emessi, con la firma
const emit = defineEmits<{
  clic: [evento: MouseEvent]
  'clic-lungo': [durataMs: number]
}>()

let inizioPressione = 0

function gestisciDown() {
  inizioPressione = Date.now()
}

function gestisciUp(evento: MouseEvent) {
  const durata = Date.now() - inizioPressione
  if (durata > 500) {
    emit('clic-lungo', durata)
  } else {
    emit('clic', evento)
  }
}
</script>

<template>
  <button
    class="pulsante"
    :class="[`pulsante--${variante}`, `pulsante--${dimensione}`]"
    :disabled="caricamento"
    :aria-busy="caricamento"
    @mousedown="gestisciDown"
    @mouseup="gestisciUp"
  >
    <span v-if="caricamento" class="solo-screen-reader">Operazione in corso</span>
    <slot />
  </button>
</template>
```

```vue
<!-- L'uso -->
<template>
  <Pulsante variante="pericolo" :caricamento="inCorso" @clic="elimina" @clic-lungo="conferma">
    Elimina
  </Pulsante>
</template>
```

### Le props sono in sola lettura

```vue
<script setup lang="ts">
const props = defineProps<{ elenco: readonly string[] }>()

// ❌ Modificare una prop: Vue avvisa in sviluppo
// props.elenco.push('x')

// ✅ Derivare con una computed
import { computed } from 'vue'
const ordinato = computed(() => [...props.elenco].sort())
</script>
```

### Il destructuring delle props

```vue
<script setup lang="ts">
// Da Vue 3.5 il destructuring delle props CONSERVA la reattività:
// il compilatore riscrive gli accessi.
const { titolo, valore = 0 } = defineProps<{
  titolo: string
  valore?: number
}>()

// I valori predefiniti si scrivono qui: withDefaults non serve più
</script>

<template>
  <p>{{ titolo }}: {{ valore }}</p>
</template>
```

### `defineExpose`

```vue
<script setup lang="ts">
import { ref } from 'vue'

const campo = ref<HTMLInputElement | null>(null)

function daiFocus() {
  campo.value?.focus()
}

// Di default un componente con <script setup> è CHIUSO:
// il genitore non vede nulla. defineExpose apre ciò che serve.
defineExpose({ daiFocus })
</script>

<template>
  <input ref="campo" />
</template>
```

```vue
<!-- Nel genitore -->
<script setup lang="ts">
import { useTemplateRef } from 'vue'

// useTemplateRef (Vue 3.5) sostituisce il ref con lo stesso nome
const modulo = useTemplateRef('modulo')

function focalizza() {
  modulo.value?.daiFocus()
}
</script>

<template>
  <CampoTesto ref="modulo" />
</template>
```

---

## A7. `v-model` e i form

```vue
<script setup lang="ts">
import { ref } from 'vue'

const testo = ref('')
const numero = ref(0)
const accettato = ref(false)
const scelta = ref('')
const interessi = ref<string[]>([])
</script>

<template>
  <!-- v-model è zucchero su :value + @input -->
  <input v-model="testo" />
  <textarea v-model="testo" />

  <!-- I modificatori -->
  <input v-model.trim="testo" />
  <input v-model.number="numero" />
  <input v-model.lazy="testo" />
  <!-- aggiorna su change, non su input -->

  <!-- Checkbox singola: booleano -->
  <input type="checkbox" v-model="accettato" />

  <!-- Checkbox multiple con lo stesso v-model: array -->
  <input type="checkbox" value="sport" v-model="interessi" />
  <input type="checkbox" value="musica" v-model="interessi" />

  <!-- Radio -->
  <input type="radio" value="email" v-model="scelta" />
  <input type="radio" value="telefono" v-model="scelta" />

  <!-- Select -->
  <select v-model="scelta">
    <option value="">Scegli</option>
    <option value="a">A</option>
  </select>
</template>
```

### `v-model` sui componenti

```vue
<!-- src/componenti/CampoTesto.vue -->
<script setup lang="ts">
// defineModel (Vue 3.4+): crea un ref bidirezionale.
// Sostituisce la coppia prop 'modelValue' + evento 'update:modelValue'.
const valore = defineModel<string>({ required: true })

// Più modelli, con nomi
const aperto = defineModel<boolean>('aperto', { default: false })

defineProps<{ etichetta: string; errore?: string }>()

const id = `campo-${Math.random().toString(36).slice(2)}`
</script>

<template>
  <div class="campo">
    <label :for="id">{{ etichetta }}</label>
    <input
      :id="id"
      v-model="valore"
      :aria-invalid="errore !== undefined"
      :aria-describedby="errore ? `${id}-errore` : undefined"
    />
    <p v-if="errore" :id="`${id}-errore`" role="alert">{{ errore }}</p>
  </div>
</template>
```

```vue
<!-- L'uso: bidirezionale, senza scrivere l'evento -->
<script setup lang="ts">
import { ref } from 'vue'

const email = ref('')
const pannelloAperto = ref(false)
</script>

<template>
  <CampoTesto v-model="email" v-model:aperto="pannelloAperto" etichetta="Email" />
</template>
```

```vue
<!-- Con una trasformazione -->
<script setup lang="ts">
const valore = defineModel<string>({
  required: true,
  // get e set intercettano lettura e scrittura
  get: (v) => v.trim(),
  set: (v) => v.toLowerCase(),
})
</script>
```

---

# Parte B — Comprensione Profonda

---

## B1. Come funziona la reattività

> **Analogia:** un foglio di calcolo. Scrivi `=A1+B1` in C1, e quando cambi A1 la cella C1 si aggiorna da sola. Nessuno le ha detto di ricalcolarsi: il foglio ha registrato, mentre calcolava C1, che aveva letto A1 e B1. Vue fa esattamente questo con `Proxy`: mentre esegue una computed o un rendering, annota quali reattivi legge, e quando uno cambia riesegue solo chi lo aveva letto.

```
                    ┌─────────────────────────────┐
                    │  const conteggio = ref(0)   │
                    └──────────────┬──────────────┘
                                   │
    LETTURA (get)                  │              SCRITTURA (set)
    "chi mi sta leggendo?"         │              "chi mi aveva letto?"
                                   │
    ┌──────────────────────────────┴──────────────────────────────┐
    │                                                             │
    ▼                                                             ▼
  track()                                                     trigger()
  registra l'effetto corrente                    riesegue gli effetti registrati
  nella lista dei dipendenti
    │                                                             │
    ▼                                                             ▼
  ┌────────────────────────┐                    ┌────────────────────────┐
  │ conteggio → [          │                    │ per ogni effetto:      │
  │   render del componente│                    │   se è computed →      │
  │   computed 'doppio'    │                    │     invalida la cache  │
  │   watch su conteggio   │                    │   se è render →        │
  │ ]                      │                    │     accoda l'aggiorn.  │
  └────────────────────────┘                    └────────────────────────┘
```

```typescript
// Una versione minima del meccanismo, per capirlo
let effettoCorrente: (() => void) | null = null
const dipendenze = new WeakMap<object, Map<string | symbol, Set<() => void>>>()

function traccia(bersaglio: object, chiave: string | symbol): void {
  if (effettoCorrente === null) return

  let perOggetto = dipendenze.get(bersaglio)
  if (!perOggetto) {
    perOggetto = new Map()
    dipendenze.set(bersaglio, perOggetto)
  }

  let perChiave = perOggetto.get(chiave)
  if (!perChiave) {
    perChiave = new Set()
    perOggetto.set(chiave, perChiave)
  }

  perChiave.add(effettoCorrente)
}

function scatena(bersaglio: object, chiave: string | symbol): void {
  const effetti = dipendenze.get(bersaglio)?.get(chiave)
  if (!effetti) return

  // Copia: un effetto potrebbe modificare l'insieme mentre lo si percorre
  for (const effetto of [...effetti]) effetto()
}

function reattivoMinimale<T extends object>(oggetto: T): T {
  return new Proxy(oggetto, {
    get(bersaglio, chiave, ricevitore) {
      traccia(bersaglio, chiave)
      return Reflect.get(bersaglio, chiave, ricevitore)
    },

    set(bersaglio, chiave, valore, ricevitore) {
      const precedente = Reflect.get(bersaglio, chiave, ricevitore)
      const esito = Reflect.set(bersaglio, chiave, valore, ricevitore)

      // Solo se il valore è DAVVERO cambiato
      if (!Object.is(precedente, valore)) scatena(bersaglio, chiave)

      return esito
    },
  })
}

function effettoReattivo(funzione: () => void): void {
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

```typescript
// Il meccanismo in azione
const stato = reattivoMinimale({ conteggio: 0 })

effettoReattivo(() => {
  // Leggendo stato.conteggio, questo effetto si registra
  console.log('conteggio:', stato.conteggio)
})

stato.conteggio = 1 // l'effetto si riesegue
stato.conteggio = 1 // NON si riesegue: il valore non è cambiato
```

```
# Output atteso:
conteggio: 0
conteggio: 1
```

### Le conseguenze pratiche

```typescript
import { reactive, ref, watchEffect } from 'vue'

const stato = reactive({ a: 1, b: 2 })

// Questo effetto dipende solo da 'a': cambiando 'b' non si riesegue
watchEffect(() => console.log(stato.a))

// ⚠ La dipendenza si registra alla LETTURA. In un ramo condizionale,
//    ciò che non viene letto non viene tracciato.
const mostra = ref(true)
watchEffect(() => {
  if (mostra.value) {
    console.log(stato.a) // tracciato solo quando mostra è true
  }
})
```

```typescript
// ⚠ La reattività si perde estraendo il valore
const stato2 = reactive({ conteggio: 0 })

// ❌ Il numero è una copia: nessun Proxy, nessun tracciamento
const { conteggio } = stato2

// ✅ Passare l'oggetto, o usare toRefs
import { toRefs } from 'vue'
const { conteggio: rif } = toRefs(stato2)
```

```typescript
// ⚠ Map e Set sono reattivi, ma vanno usati con i loro metodi
const mappa = reactive(new Map<string, number>())
mappa.set('a', 1) // reattivo

// Gli array sono reattivi anche con push, splice, sort:
// Vue intercetta i metodi che modificano
const elenco = reactive<number[]>([])
elenco.push(1) // reattivo
```

---

## B2. `watch` e `watchEffect`

```typescript
import { ref, watch, watchEffect } from 'vue'

const idUtente = ref('u-1')
const utente = ref<Utente | null>(null)

// watch: dichiari ESPLICITAMENTE cosa osservare.
// Riceve nuovo e vecchio valore.
watch(idUtente, async (nuovo, vecchio, alRiavvio) => {
  const controller = new AbortController()

  // alRiavvio: eseguito prima della prossima esecuzione
  // e allo smontaggio. È la pulizia.
  alRiavvio(() => controller.abort())

  utente.value = await recuperaUtente(nuovo, { signal: controller.signal })
})

// watchEffect: le dipendenze si deducono da ciò che LEGGE.
// Si esegue subito, senza aspettare un cambiamento.
watchEffect(async (alRiavvio) => {
  const controller = new AbortController()
  alRiavvio(() => controller.abort())

  utente.value = await recuperaUtente(idUtente.value, { signal: controller.signal })
})
```

### Le opzioni

```typescript
// immediate: esegue subito, non solo al primo cambiamento
watch(idUtente, carica, { immediate: true })

// deep: osserva anche le modifiche annidate.
// Costa: percorre l'intero oggetto a ogni verifica.
watch(oggettoComplesso, gestisci, { deep: true })

// Da Vue 3.5, deep accetta una profondità
watch(oggettoComplesso, gestisci, { deep: 2 })

// once: si rimuove dopo la prima esecuzione (Vue 3.4+)
watch(pronto, avvia, { once: true })

// flush: quando eseguire rispetto al rendering
watch(valore, gestisci, { flush: 'pre' }) // prima (default)
watch(valore, gestisci, { flush: 'post' }) // dopo: il DOM è aggiornato
watch(valore, gestisci, { flush: 'sync' }) // subito, in modo sincrono
```

### Osservare più fonti

```typescript
// Un array di fonti: il callback riceve array di nuovi e vecchi
watch([pagina, filtro], ([nuovaPagina, nuovoFiltro], [vecchiaPagina]) => {
  if (nuovaPagina !== vecchiaPagina) scorriInCima()
  carica(nuovaPagina, nuovoFiltro)
})

// Una proprietà di un reactive richiede un getter:
// passando stato.conteggio si passerebbe il NUMERO, non il collegamento
watch(
  () => stato.conteggio,
  (nuovo) => console.log(nuovo),
)

// Più proprietà con i getter
watch([() => stato.a, () => stato.b], ([a, b]) => console.log(a, b))
```

```typescript
// ❌ Errore comune: passare il VALORE invece del getter.
//    watch riceve il numero 1, non una fonte reattiva:
//    non scatta mai, e Vue non può avvisare.
// watch(stato.conteggio, (nuovo) => console.log(nuovo))

// ✅ Il getter viene rieseguito, e la lettura viene tracciata
watch(
  () => stato.conteggio,
  (nuovo) => console.log(nuovo),
)
```

### Fermare un osservatore

```typescript
// watch restituisce la funzione per fermarlo.
// Creato dentro setup(), si ferma da solo allo smontaggio.
const ferma = watch(valore, gestisci)
ferma()

// ⚠ Un watch creato in una callback asincrona NON è legato
//    al componente: va fermato a mano
onMounted(async () => {
  await qualcosa()
  const ferma2 = watch(valore, gestisci) // non si ferma da solo
  onUnmounted(ferma2) // ← va collegato esplicitamente
})
```

```
watch o watchEffect:

  watch        · vuoi il valore VECCHIO
               · vuoi controllare esattamente cosa osservare
               · l'effetto non deve partire subito
               · le dipendenze sono poche e note

  watchEffect  · le dipendenze sono molte e ovvie
               · deve partire subito
               ⚠ traccia TUTTO ciò che legge: è facile
                 dipendere da qualcosa senza accorgersene

  computed     · stai DERIVANDO un valore, non facendo un effetto
                 → quasi sempre è questa la risposta giusta
```

---

## B3. Il ciclo di vita

```vue
<script setup lang="ts">
import {
  onMounted,
  onUpdated,
  onUnmounted,
  onBeforeMount,
  onBeforeUpdate,
  onBeforeUnmount,
  onErrorCaptured,
  onActivated,
  onDeactivated,
  ref,
} from 'vue'

// Il corpo di <script setup> è l'equivalente di 'setup':
// eseguito PRIMA del montaggio
console.log('setup')

onBeforeMount(() => {
  // Il DOM non esiste ancora
})

onMounted(() => {
  // Il DOM c'è: qui si accede ai ref del template,
  // si registrano listener, si avviano osservatori
})

onBeforeUpdate(() => {
  // Prima di un aggiornamento del DOM: per leggere
  // lo stato precedente (una posizione di scorrimento)
})

onUpdated(() => {
  // Dopo un aggiornamento del DOM
  // ⚠ Modificare lo stato qui produce un ciclo infinito
})

onBeforeUnmount(() => {
  // Il componente c'è ancora: ultimo momento per leggerlo
})

onUnmounted(() => {
  // Pulizia: timer, listener, connessioni
})

// Cattura gli errori dei DISCENDENTI
onErrorCaptured((errore, istanza, informazioni) => {
  registra(errore, informazioni)
  return false // false ferma la propagazione verso l'alto
})

// Solo dentro <KeepAlive>
onActivated(() => {})
onDeactivated(() => {})
</script>
```

```vue
<script setup lang="ts">
import { onMounted, onUnmounted, useTemplateRef } from 'vue'

const contenitore = useTemplateRef('contenitore')
let osservatore: IntersectionObserver | null = null

onMounted(() => {
  if (!contenitore.value) return

  osservatore = new IntersectionObserver(([voce]) => {
    if (voce?.isIntersecting) caricaAltro()
  })

  osservatore.observe(contenitore.value)
})

onUnmounted(() => {
  // La pulizia è obbligatoria come in React
  osservatore?.disconnect()
})
</script>

<template>
  <div ref="contenitore">Sentinella</div>
</template>
```

```typescript
// nextTick: attende che il DOM sia aggiornato
import { nextTick, ref } from 'vue'

const elenco = ref<string[]>([])

async function aggiungi(voce: string) {
  elenco.value.push(voce)

  // Il DOM non è ancora aggiornato: Vue accoda gli aggiornamenti
  await nextTick()
  // Adesso sì
  document.querySelector('#elenco')?.lastElementChild?.scrollIntoView()
}
```

---

## B4. Slot: la composizione in Vue

```vue
<!-- src/componenti/Pannello.vue -->
<script setup lang="ts">
defineProps<{ titolo: string }>()
</script>

<template>
  <section class="pannello">
    <header class="pannello__intestazione">
      <h2>{{ titolo }}</h2>
      <!-- Slot nominale, con contenuto di riserva -->
      <slot name="azioni">
        <span class="solo-screen-reader">Nessuna azione disponibile</span>
      </slot>
    </header>

    <div class="pannello__corpo">
      <!-- Slot predefinito -->
      <slot />
    </div>

    <!-- v-if sullo slot: si disegna il piè di pagina solo se
         qualcuno ha passato del contenuto -->
    <footer v-if="$slots.piede" class="pannello__piede">
      <slot name="piede" />
    </footer>
  </section>
</template>
```

```vue
<template>
  <Pannello titolo="Fatture recenti">
    <!-- Il contenuto senza nome va nello slot predefinito -->
    <TabellaFatture :fatture="fatture" />

    <!-- #nome è la forma breve di v-slot:nome -->
    <template #azioni>
      <button @click="esporta">Esporta</button>
    </template>

    <template #piede>
      <p>{{ fatture.length }} righe</p>
    </template>
  </Pannello>
</template>
```

### Slot con scope: il figlio passa dati al genitore

```vue
<!-- src/componenti/ElencoDati.vue -->
<script setup lang="ts" generic="T">
defineProps<{
  elementi: readonly T[]
  chiaveDi: (elemento: T) => string | number
}>()
</script>

<template>
  <ul class="elenco">
    <li v-for="(elemento, indice) in elementi" :key="chiaveDi(elemento)">
      <!-- Il componente PASSA i dati allo slot -->
      <slot :elemento="elemento" :indice="indice" :primo="indice === 0" />
    </li>
  </ul>

  <p v-if="elementi.length === 0">
    <slot name="vuoto">Nessun elemento.</slot>
  </p>
</template>
```

```vue
<template>
  <!-- Il genitore RICEVE i dati e decide come disegnarli.
       Il componente gestisce la struttura, il genitore l'aspetto. -->
  <ElencoDati :elementi="fatture" :chiave-di="(f) => f.id">
    <template #default="{ elemento, indice, primo }">
      <strong v-if="primo">Più recente:</strong>
      {{ indice + 1 }}. {{ elemento.numero }} — {{ elemento.cliente }}
    </template>

    <template #vuoto>
      <em>Nessuna fattura nel periodo selezionato.</em>
    </template>
  </ElencoDati>
</template>
```

Gli slot con scope sono l'equivalente delle *render props* di React, e permettono i componenti "headless": logica e struttura nel componente, aspetto nel chiamante.

```vue
<script setup lang="ts">
// L'attributo generic su <script setup> rende il componente
// generico: T viene dedotto da elementi, e lo slot è tipizzato
</script>
```

---

## B5. `provide` e `inject`

L'equivalente di Context: passare un valore a discendenti profondi senza inoltrarlo.

```typescript
// src/chiavi.ts — le chiavi tipizzate, in un file condiviso
import type { InjectionKey, Ref } from 'vue'

export type ContestoTema = {
  tema: Ref<'chiaro' | 'scuro'>
  cambiaTema: (tema: 'chiaro' | 'scuro') => void
}

// InjectionKey lega il tipo alla chiave: inject lo deduce
export const CHIAVE_TEMA: InjectionKey<ContestoTema> = Symbol('tema')
```

```vue
<!-- Il fornitore -->
<script setup lang="ts">
import { provide, readonly, ref } from 'vue'
import { CHIAVE_TEMA } from '@/chiavi'

const tema = ref<'chiaro' | 'scuro'>('chiaro')

function cambiaTema(nuovo: 'chiaro' | 'scuro') {
  tema.value = nuovo
  document.documentElement.dataset['tema'] = nuovo
}

// readonly sul ref esposto: i discendenti leggono,
// solo il fornitore modifica
provide(CHIAVE_TEMA, { tema: readonly(tema), cambiaTema })
</script>
```

```vue
<!-- Il consumatore, a qualunque profondità -->
<script setup lang="ts">
import { inject } from 'vue'
import { CHIAVE_TEMA } from '@/chiavi'

const contesto = inject(CHIAVE_TEMA)

if (!contesto) {
  throw new Error('Questo componente richiede un fornitore del tema')
}

const { tema, cambiaTema } = contesto
</script>

<template>
  <button @click="cambiaTema(tema === 'chiaro' ? 'scuro' : 'chiaro')">
    Tema: {{ tema }}
  </button>
</template>
```

```typescript
// Il composable che nasconde inject e verifica il fornitore:
// il pattern da preferire
export function useTema(): ContestoTema {
  const contesto = inject(CHIAVE_TEMA)

  if (!contesto) {
    throw new Error('useTema richiede <FornitoreTema> fra gli antenati')
  }

  return contesto
}
```

```
Differenza importante rispetto al Context di React:

  In React, cambiando il valore del Context si ridisegnano
  TUTTI i consumatori.

  In Vue, il valore fornito è un ref: cambiandolo si aggiorna
  solo ciò che LEGGE quel ref. Non c'è cascata, e non serve
  memoizzare il valore fornito.

  È una conseguenza diretta della reattività fine.
```

---

## B6. I composables

Un composable è una funzione che usa le API di reattività di Vue. La convenzione è il prefisso `use`.

```typescript
// src/composables/useArchivioLocale.ts
import { ref, watch, type Ref } from 'vue'

export function useArchivioLocale<T>(chiave: string, valoreIniziale: T): Ref<T> {
  const memorizzato = ref<T>(valoreIniziale) as Ref<T>

  try {
    const grezzo = localStorage.getItem(chiave)
    if (grezzo !== null) memorizzato.value = JSON.parse(grezzo) as T
  } catch {
    // Valore corrotto: si tiene l'iniziale
  }

  // deep: anche le modifiche annidate vanno salvate
  watch(
    memorizzato,
    (nuovo) => {
      try {
        localStorage.setItem(chiave, JSON.stringify(nuovo))
      } catch (errore) {
        console.warn('Salvataggio non riuscito', errore)
      }
    },
    { deep: true },
  )

  return memorizzato
}
```

```typescript
// src/composables/useRecupero.ts
import { ref, shallowRef, watchEffect, type Ref } from 'vue'

type StatoRecupero<T> = {
  dati: Ref<T | null>
  errore: Ref<Error | null>
  inCaricamento: Ref<boolean>
  ricarica: () => void
}

export function useRecupero<T>(url: Ref<string> | (() => string)): StatoRecupero<T> {
  // shallowRef: i dati si sostituiscono per intero, non serve
  // la reattività profonda su un oggetto potenzialmente grande
  const dati = shallowRef<T | null>(null)
  const errore = ref<Error | null>(null)
  const inCaricamento = ref(false)
  const contatore = ref(0)

  watchEffect(async (alRiavvio) => {
    // Leggere contatore lo registra come dipendenza:
    // incrementandolo si riesegue l'effetto
    contatore.value

    const indirizzo = typeof url === 'function' ? url() : url.value
    const controller = new AbortController()
    alRiavvio(() => controller.abort())

    inCaricamento.value = true
    errore.value = null

    try {
      const risposta = await fetch(indirizzo, { signal: controller.signal })
      if (!risposta.ok) throw new Error(`${risposta.status} ${risposta.statusText}`)

      dati.value = (await risposta.json()) as T
    } catch (e) {
      if (e instanceof Error && e.name === 'AbortError') return
      errore.value = e instanceof Error ? e : new Error(String(e))
    } finally {
      inCaricamento.value = false
    }
  })

  return { dati, errore, inCaricamento, ricarica: () => contatore.value++ }
}
```

```typescript
// src/composables/useEventoFinestra.ts
import { onMounted, onUnmounted } from 'vue'

/** Registra un listener e lo rimuove allo smontaggio, automaticamente. */
export function useEventoFinestra<K extends keyof WindowEventMap>(
  tipo: K,
  gestore: (evento: WindowEventMap[K]) => void,
  opzioni?: AddEventListenerOptions,
): void {
  onMounted(() => window.addEventListener(tipo, gestore, opzioni))
  onUnmounted(() => window.removeEventListener(tipo, gestore, opzioni))
}
```

### Il composable che condivide lo stato

```typescript
// src/composables/useContatoreGlobale.ts
import { ref, readonly } from 'vue'

// Lo stato è FUORI dalla funzione: creato una volta sola
// al primo import, condiviso da tutti i chiamanti.
const conteggio = ref(0)

export function useContatoreGlobale() {
  return {
    conteggio: readonly(conteggio),
    incrementa: () => conteggio.value++,
  }
}
```

```typescript
// Contro quello che NON lo condivide
export function useContatoreLocale() {
  // Lo stato è DENTRO: ogni chiamante ha il proprio
  const conteggio = ref(0)
  return { conteggio, incrementa: () => conteggio.value++ }
}
```

È la differenza principale con React, dove un hook non può condividere stato senza Context o uno store: in Vue basta dichiarare il `ref` fuori dalla funzione. Comodo, e da usare con consapevolezza — è uno stato globale a tutti gli effetti.

```
Le regole dei composables:

  · il nome inizia con 'use'
  · vanno chiamati SINCRONAMENTE in <script setup> o setup(),
    se registrano hook di ciclo di vita
  · restituiscono ref, non valori estratti
  · la pulizia va in onUnmounted, o alRiavvio di watch
```

---

## B7. Pinia

Lo store ufficiale di Vue. Più semplice di Vuex, e con i tipi dedotti.

```typescript
// src/store/fatture.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const useStoreFatture = defineStore('fatture', () => {
  // ── Stato ──────────────────────────────────────────────────
  const elenco = ref<Fattura[]>([])
  const inCaricamento = ref(false)
  const errore = ref<Error | null>(null)
  const filtro = ref('')

  // ── Getter (computed) ──────────────────────────────────────
  const filtrate = computed(() => {
    const termine = filtro.value.toLowerCase()
    return elenco.value.filter((f) => f.cliente.toLowerCase().includes(termine))
  })

  const totale = computed(() => filtrate.value.reduce((s, f) => s + f.importo, 0))

  const insolute = computed(() => elenco.value.filter((f) => !f.pagata))

  // ── Azioni (funzioni) ──────────────────────────────────────
  async function carica() {
    inCaricamento.value = true
    errore.value = null

    try {
      elenco.value = await recuperaFatture()
    } catch (e) {
      errore.value = e instanceof Error ? e : new Error(String(e))
    } finally {
      inCaricamento.value = false
    }
  }

  async function paga(id: string) {
    // Aggiornamento ottimistico
    const indice = elenco.value.findIndex((f) => f.id === id)
    const precedente = elenco.value[indice]
    if (!precedente) return

    elenco.value[indice] = { ...precedente, pagata: true }

    try {
      await pagaFattura(id)
    } catch (e) {
      // Ripristino in caso di errore
      elenco.value[indice] = precedente
      throw e
    }
  }

  return { elenco, inCaricamento, errore, filtro, filtrate, totale, insolute, carica, paga }
})
```

```vue
<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'
import { useStoreFatture } from '@/store/fatture'

const store = useStoreFatture()

// ⚠ Il destructuring diretto ROMPE la reattività:
//    lo store è un reactive.
// const { filtrate, totale } = store   // ✗

// ✅ storeToRefs conserva il collegamento su stato e getter
const { filtrate, totale, inCaricamento, filtro } = storeToRefs(store)

// Le AZIONI si destrutturano normalmente: sono funzioni
const { carica, paga } = store

onMounted(carica)
</script>

<template>
  <input v-model="filtro" />
  <p v-if="inCaricamento">Caricamento…</p>
  <p v-else>{{ filtrate.length }} fatture — {{ totale }} euro</p>
</template>
```

```typescript
// Altri modi di interagire con lo store
const store = useStoreFatture()

// Modificare più proprietà insieme
store.$patch({ filtro: '', inCaricamento: false })

// Con una funzione, per le modifiche complesse
store.$patch((stato) => {
  stato.elenco.push(nuovaFattura)
  stato.filtro = ''
})

// Riportare allo stato iniziale (solo con la sintassi a opzioni)
store.$reset()

// Osservare ogni mutazione: per i log, o per la persistenza
store.$subscribe((mutazione, stato) => {
  localStorage.setItem('fatture', JSON.stringify(stato.elenco))
})

// Osservare le azioni
store.$onAction(({ name, args, after, onError }) => {
  console.log(`azione ${name}`, args)
  after((risultato) => console.log('completata', risultato))
  onError((errore) => console.error('fallita', errore))
})
```

```
Pinia contro Context contro composable con stato globale:

  composable con ref fuori    lo stato globale più semplice.
                              Nessuna dipendenza, nessun DevTools.

  provide/inject              quando l'ambito è un SOTTOALBERO,
                              non tutta l'applicazione

  Pinia                       stato globale con: DevTools,
                              hot module replacement, plugin,
                              rendering lato server, e una
                              convenzione condivisa dal team
```

---

## B8. Vue Router

```typescript
// src/router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const rotte: readonly RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layout/Principale.vue'),
    children: [
      { path: '', name: 'panoramica', component: () => import('@/pagine/Panoramica.vue') },
      {
        path: 'fatture',
        name: 'fatture',
        component: () => import('@/pagine/Fatture.vue'),
        // I parametri della query diventano props
        props: (rotta) => ({
          pagina: Number(rotta.query['pagina'] ?? 1),
          ricerca: String(rotta.query['ricerca'] ?? ''),
        }),
      },
      {
        path: 'fatture/:id',
        name: 'dettaglio-fattura',
        component: () => import('@/pagine/DettaglioFattura.vue'),
        props: true, // i parametri del percorso diventano props
        meta: { richiedeAutenticazione: true },
      },
      {
        path: 'impostazioni',
        name: 'impostazioni',
        component: () => import('@/pagine/Impostazioni.vue'),
        meta: { richiedeAutenticazione: true, ruolo: 'admin' },
      },
    ],
  },
  { path: '/accesso', name: 'accesso', component: () => import('@/pagine/Accesso.vue') },
  // La cattura di tutto va per ULTIMA
  { path: '/:percorso(.*)*', name: 'non-trovata', component: () => import('@/pagine/NonTrovata.vue') },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...rotte],

  scrollBehavior(a, da, posizioneSalvata) {
    // Tornando indietro, si ripristina la posizione
    if (posizioneSalvata) return posizioneSalvata
    if (a.hash) return { el: a.hash, behavior: 'smooth' }
    return { top: 0 }
  },
})

// La guardia globale: protezione delle rotte
router.beforeEach((a, da) => {
  const autenticazione = useStoreAutenticazione()

  if (a.meta['richiedeAutenticazione'] && !autenticazione.autenticato) {
    // Restituendo una destinazione, la navigazione viene reindirizzata
    return { name: 'accesso', query: { da: a.fullPath } }
  }

  const ruolo = a.meta['ruolo']
  if (typeof ruolo === 'string' && !autenticazione.haRuolo(ruolo)) {
    return { name: 'non-autorizzato' }
  }

  return true
})
```

```vue
<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'

const rotta = useRoute()
const router = useRouter()

// La rotta è reattiva: le computed che la leggono si aggiornano
const pagina = computed(() => Number(rotta.query['pagina'] ?? 1))

function vaiAPagina(numero: number) {
  router.push({ query: { ...rotta.query, pagina: String(numero) } })
}

function vaiAlDettaglio(id: string) {
  router.push({ name: 'dettaglio-fattura', params: { id } })
}
</script>

<template>
  <!-- RouterLink invece di <a>: nessun ricaricamento della pagina -->
  <RouterLink :to="{ name: 'fatture' }">Fatture</RouterLink>

  <!-- La classe attiva viene aggiunta automaticamente -->
  <RouterLink :to="{ name: 'panoramica' }" active-class="attiva">Panoramica</RouterLink>

  <!-- Il punto in cui la vista viene disegnata -->
  <RouterView v-slot="{ Component }">
    <Transition name="dissolvenza" mode="out-in">
      <component :is="Component" />
    </Transition>
  </RouterView>
</template>
```

```vue
<script setup lang="ts">
import { onBeforeRouteLeave } from 'vue-router'
import { ref } from 'vue'

const bozzaModificata = ref(false)

// Impedisce di lasciare la pagina con modifiche non salvate
onBeforeRouteLeave((a, da) => {
  if (!bozzaModificata.value) return true
  return window.confirm('Ci sono modifiche non salvate. Vuoi uscire?')
})
</script>
```

---

## B9. Teleport, Transition e `<KeepAlive>`

### Teleport

```vue
<script setup lang="ts">
import { ref } from 'vue'

const aperta = ref(false)
</script>

<template>
  <button @click="aperta = true">Apri</button>

  <!-- Il contenuto viene spostato nel body: esce da qualunque
       overflow:hidden e da qualunque contesto di impilamento
       dei genitori. Lo stato e le props restano quelli di qui. -->
  <Teleport to="body">
    <dialog v-if="aperta" open aria-labelledby="titolo-modale">
      <h2 id="titolo-modale">Conferma</h2>
      <button @click="aperta = false">Chiudi</button>
    </dialog>
  </Teleport>
</template>
```

`Teleport` risolve il problema descritto in `tutorial_02_css3.md`: un `transform` o un `opacity` su un antenato crea un contesto di impilamento che intrappola le modali. Spostando il nodo nel `body`, il problema sparisce.

### Transition

```vue
<script setup lang="ts">
import { ref } from 'vue'

const visibile = ref(true)
</script>

<template>
  <Transition name="dissolvenza">
    <p v-if="visibile">Contenuto</p>
  </Transition>

  <!-- TransitionGroup per le liste: anima anche gli spostamenti -->
  <TransitionGroup name="elenco" tag="ul">
    <li v-for="f in fatture" :key="f.id">{{ f.numero }}</li>
  </TransitionGroup>
</template>

<style scoped>
/* Le classi che Vue applica automaticamente */
.dissolvenza-enter-active,
.dissolvenza-leave-active {
  transition: opacity 200ms ease;
}

.dissolvenza-enter-from,
.dissolvenza-leave-to {
  opacity: 0;
}

/* v-move anima gli elementi che cambiano posizione */
.elenco-move {
  transition: transform 300ms ease;
}

/* Il rispetto della preferenza di movimento non è automatico */
@media (prefers-reduced-motion: reduce) {
  .dissolvenza-enter-active,
  .dissolvenza-leave-active,
  .elenco-move {
    transition: none;
  }
}
</style>
```

### `<KeepAlive>`

```vue
<template>
  <!-- I componenti restano in memoria invece di essere distrutti:
       lo stato sopravvive, e onActivated/onDeactivated
       sostituiscono onMounted/onUnmounted -->
  <RouterView v-slot="{ Component }">
    <KeepAlive :max="5" :include="['Fatture', 'Clienti']">
      <component :is="Component" />
    </KeepAlive>
  </RouterView>
</template>
```

`max` è importante: senza, ogni pagina visitata resta in memoria per sempre.

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Diagnosticare la reattività perduta

**Obiettivo:** cinque componenti che non si aggiornano. Spiegare la causa di ciascuno e correggerla.

```vue
<!-- PROBLEMA 1 -->
<script setup lang="ts">
import { reactive } from 'vue'

const stato = reactive({ conteggio: 0, nome: 'Anna' })
const { conteggio } = stato

function incrementa() {
  conteggio++
}
</script>

<template>
  <p>{{ conteggio }}</p>
  <button @click="incrementa">+</button>
</template>
```

```vue
<!-- SOLUZIONE 1 -->
<script setup lang="ts">
import { ref } from 'vue'

// CAUSA: il destructuring di un reactive estrae il VALORE.
//   'conteggio' è un numero normale: incrementarlo non tocca
//   il Proxy, quindi nessun trigger, quindi nessun aggiornamento.
//
// FIX: usare ref, che sopravvive al passaggio come valore.
const conteggio = ref(0)

function incrementa() {
  conteggio.value++
}
</script>

<template>
  <p>{{ conteggio }}</p>
  <button @click="incrementa">+</button>
</template>
```

```vue
<!-- PROBLEMA 2 -->
<script setup lang="ts">
import { reactive, watch } from 'vue'

const stato = reactive({ pagina: 1 })

// Il watch non scatta mai
watch(stato.pagina, (nuova) => carica(nuova))
</script>
```

```vue
<!-- SOLUZIONE 2 -->
<script setup lang="ts">
import { reactive, watch } from 'vue'

const stato = reactive({ pagina: 1 })

// CAUSA: watch riceve il NUMERO 1, non una fonte reattiva.
//   Osservare un numero non ha senso, e Vue non può saperlo.
//
// FIX: un getter, che viene rieseguito e traccia la lettura.
watch(
  () => stato.pagina,
  (nuova) => carica(nuova),
)

// In alternativa, con ref il problema non si pone:
// watch(pagina, ...) funziona perché pagina È un ref.
</script>
```

```vue
<!-- PROBLEMA 3 -->
<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ elenco: string[] }>()

// Ordinare così modifica la prop del genitore
const ordinato = props.elenco.sort()
</script>
```

```vue
<!-- SOLUZIONE 3 -->
<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ elenco: readonly string[] }>()

// CAUSA DOPPIA:
//   1. sort() modifica l'array del GENITORE (mutazione di una prop)
//   2. il calcolo avviene una volta sola: cambiando la prop,
//      'ordinato' resta quello vecchio
//
// FIX: computed su una copia. Si ricalcola quando la prop cambia,
//   e toSorted non tocca l'originale.
const ordinato = computed(() => props.elenco.toSorted())
</script>
```

```vue
<!-- PROBLEMA 4 -->
<script setup lang="ts">
import { shallowRef } from 'vue'

const dati = shallowRef({ righe: [] as string[] })

function aggiungi(riga: string) {
  dati.value.righe.push(riga) // la tabella non si aggiorna
}
</script>
```

```vue
<!-- SOLUZIONE 4 -->
<script setup lang="ts">
import { shallowRef, triggerRef } from 'vue'

const dati = shallowRef({ righe: [] as string[] })

// CAUSA: shallowRef traccia solo la sostituzione di .value.
//   Modificare in profondità non produce alcun trigger.
//
// FIX A: sostituire .value per intero
function aggiungi(riga: string) {
  dati.value = { ...dati.value, righe: [...dati.value.righe, riga] }
}

// FIX B: modificare e forzare il trigger — più efficiente
//   su strutture molto grandi
function aggiungiEfficiente(riga: string) {
  dati.value.righe.push(riga)
  triggerRef(dati)
}

// FIX C: se serve la reattività profonda, usare ref e non shallowRef
</script>
```

```vue
<!-- PROBLEMA 5 -->
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const valore = ref(0)

onMounted(async () => {
  await caricaConfigurazione()

  // Questo watch non si ferma mai
  watch(valore, salva)
})
</script>
```

```vue
<!-- SOLUZIONE 5 -->
<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

const valore = ref(0)

// CAUSA: un watch creato SINCRONAMENTE in setup viene legato
//   al componente e si ferma allo smontaggio. Creato dopo
//   un await, quel legame si è perso: il watch sopravvive
//   al componente. È un memory leak.
//
// FIX A: creare il watch sincronamente, e attivarlo dopo
const pronto = ref(false)
watch(valore, (nuovo) => {
  if (pronto.value) salva(nuovo)
})

onMounted(async () => {
  await caricaConfigurazione()
  pronto.value = true
})

// FIX B: fermarlo esplicitamente
onMounted(async () => {
  await caricaConfigurazione()
  const ferma = watch(valore, salva)
  onUnmounted(ferma)
})
</script>
```

```
# I cinque errori, riassunti:
#
# 1. Destructuring di reactive     → il valore si stacca dal Proxy
# 2. watch su un valore            → serve un getter, o un ref
# 3. Mutazione di una prop         → e nessun ricalcolo
# 4. shallowRef modificato         → traccia solo la sostituzione
# 5. watch creato dopo un await    → non si ferma allo smontaggio
#
# IL FILO COMUNE:
#   la reattività di Vue funziona sui PROXY e sui REF.
#   Ogni volta che si estrae un valore primitivo da uno di
#   questi, il collegamento si spezza — e Vue non può avvisare,
#   perché a quel punto sta guardando un numero qualunque.
#
# LA REGOLA CHE EVITA QUATTRO CASI SU CINQUE:
#   usa ref, non reactive.
```

---

### Esercizio 2 — Un composable riusabile con pulizia

**Obiettivo:** un composable per la ricerca con ritardo e annullamento, con la pulizia gestita automaticamente.

```typescript
// SOLUZIONE — src/composables/useRicerca.ts
import { ref, shallowRef, watch, onUnmounted, type Ref } from 'vue'

export type StatoRicerca<T> =
  | { stato: 'inattiva' }
  | { stato: 'caricamento' }
  | { stato: 'riuscita'; risultati: readonly T[] }
  | { stato: 'fallita'; errore: Error }

export function useRicerca<T>(
  termine: Ref<string>,
  cerca: (termine: string, opzioni: { signal: AbortSignal }) => Promise<readonly T[]>,
  { ritardo = 300, lunghezzaMinima = 2 } = {},
) {
  const stato = shallowRef<StatoRicerca<T>>({ stato: 'inattiva' })

  let temporizzatore: ReturnType<typeof setTimeout> | null = null
  let controller: AbortController | null = null

  function annulla() {
    if (temporizzatore !== null) clearTimeout(temporizzatore)
    controller?.abort()
    temporizzatore = null
    controller = null
  }

  watch(
    termine,
    (nuovo) => {
      // Ogni digitazione annulla il timer e la richiesta precedenti
      annulla()

      if (nuovo.trim().length < lunghezzaMinima) {
        stato.value = { stato: 'inattiva' }
        return
      }

      temporizzatore = setTimeout(async () => {
        controller = new AbortController()
        const segnale = controller.signal

        stato.value = { stato: 'caricamento' }

        try {
          const risultati = await cerca(nuovo, { signal: segnale })

          // Una richiesta più recente potrebbe aver già annullato
          // questa: senza la verifica, una risposta lenta
          // sovrascriverebbe una veloce più recente
          if (segnale.aborted) return

          stato.value = { stato: 'riuscita', risultati }
        } catch (errore) {
          if (errore instanceof Error && errore.name === 'AbortError') return
          stato.value = {
            stato: 'fallita',
            errore: errore instanceof Error ? errore : new Error(String(errore)),
          }
        }
      }, ritardo)
    },
    { immediate: true },
  )

  // La pulizia allo smontaggio: senza, il timer scatterebbe
  // su un componente che non esiste più
  onUnmounted(annulla)

  return { stato, annulla }
}
```

```vue
<!-- L'uso -->
<script setup lang="ts">
import { ref } from 'vue'
import { useRicerca } from '@/composables/useRicerca'

const termine = ref('')
const { stato } = useRicerca(termine, cercaClienti)
</script>

<template>
  <div class="ricerca">
    <label for="ricerca">Cerca un cliente</label>
    <input
      id="ricerca"
      v-model="termine"
      type="search"
      role="combobox"
      :aria-expanded="stato.stato === 'riuscita' && stato.risultati.length > 0"
      aria-controls="risultati"
      aria-describedby="stato-ricerca"
      autocomplete="off"
    />

    <!-- La live region annuncia senza spostare il focus -->
    <p id="stato-ricerca" role="status" aria-live="polite" class="solo-screen-reader">
      <template v-if="stato.stato === 'caricamento'">Ricerca in corso</template>
      <template v-else-if="stato.stato === 'riuscita'">
        {{ stato.risultati.length }} risultati
      </template>
      <template v-else-if="stato.stato === 'fallita'">Ricerca non riuscita</template>
    </p>

    <ul v-if="stato.stato === 'riuscita'" id="risultati" role="listbox">
      <li v-for="cliente in stato.risultati" :key="cliente.id" role="option" :aria-selected="false">
        {{ cliente.nome }}
      </li>
    </ul>

    <p v-else-if="stato.stato === 'fallita'" role="alert">
      {{ stato.errore.message }}
    </p>
  </div>
</template>
```

```
# Cosa il composable garantisce:
#
# 1. UNA richiesta invece di sei, digitando "milano"
# 2. Le risposte fuori ordine vengono SCARTATE
# 3. Lo stato è una discriminated union: caricamento e
#    errore insieme sono irrappresentabili
# 4. Il timer e la richiesta si annullano allo smontaggio
#
# DIFFERENZA CON REACT:
#   in React lo stesso hook deve gestire le dipendenze di
#   useEffect e i callback che cambiano identità. In Vue
#   il watch traccia il ref e basta: il callback 'cerca'
#   non è una dipendenza, quindi non serve un ref per stabilizzarlo.
#
#   È il vantaggio della reattività esplicita: si dichiara
#   COSA osservare, non si deduce da cosa viene letto.
```

---

### Esercizio 3 — Uno store Pinia con aggiornamento ottimistico

**Obiettivo:** uno store che aggiorna subito l'interfaccia e ripristina in caso di errore.

```typescript
// SOLUZIONE — src/store/attivita.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type Attivita = {
  readonly id: string
  readonly testo: string
  readonly completata: boolean
  readonly creataIl: string
}

export type Filtro = 'tutte' | 'da-fare' | 'completate'

export const useStoreAttivita = defineStore('attivita', () => {
  // ── Stato ──────────────────────────────────────────────────
  const elenco = ref<Attivita[]>([])
  const filtro = ref<Filtro>('tutte')
  const inCaricamento = ref(false)
  const errore = ref<Error | null>(null)
  // Le operazioni in volo, per mostrare lo stato per riga
  const inSincronizzazione = ref(new Set<string>())

  // ── Getter ─────────────────────────────────────────────────
  const visibili = computed(() => {
    switch (filtro.value) {
      case 'da-fare':
        return elenco.value.filter((a) => !a.completata)
      case 'completate':
        return elenco.value.filter((a) => a.completata)
      default:
        return elenco.value
    }
  })

  const conteggi = computed(() => ({
    tutte: elenco.value.length,
    daFare: elenco.value.filter((a) => !a.completata).length,
    completate: elenco.value.filter((a) => a.completata).length,
  }))

  const staSincronizzando = computed(() => inSincronizzazione.value.size > 0)

  // ── Azioni ─────────────────────────────────────────────────
  async function carica() {
    inCaricamento.value = true
    errore.value = null

    try {
      elenco.value = await recuperaAttivita()
    } catch (e) {
      errore.value = e instanceof Error ? e : new Error(String(e))
    } finally {
      inCaricamento.value = false
    }
  }

  async function aggiungi(testo: string) {
    const pulito = testo.trim()
    if (pulito === '') return

    // Un identificativo provvisorio, sostituito dal server
    const provvisorio: Attivita = {
      id: `provvisorio-${crypto.randomUUID()}`,
      testo: pulito,
      completata: false,
      creataIl: new Date().toISOString(),
    }

    // OTTIMISTICO: compare subito
    elenco.value = [...elenco.value, provvisorio]
    inSincronizzazione.value.add(provvisorio.id)

    try {
      const salvata = await creaAttivita({ testo: pulito })
      // Sostituisce la provvisoria con quella del server
      elenco.value = elenco.value.map((a) => (a.id === provvisorio.id ? salvata : a))
    } catch (e) {
      // ROLLBACK
      elenco.value = elenco.value.filter((a) => a.id !== provvisorio.id)
      errore.value = e instanceof Error ? e : new Error(String(e))
      throw e
    } finally {
      inSincronizzazione.value.delete(provvisorio.id)
    }
  }

  async function commuta(id: string) {
    const indice = elenco.value.findIndex((a) => a.id === id)
    const precedente = elenco.value[indice]
    if (indice === -1 || precedente === undefined) return

    // OTTIMISTICO
    elenco.value = elenco.value.with(indice, {
      ...precedente,
      completata: !precedente.completata,
    })
    inSincronizzazione.value.add(id)

    try {
      await aggiornaAttivita(id, { completata: !precedente.completata })
    } catch (e) {
      // ROLLBACK al valore esatto precedente
      const indiceAttuale = elenco.value.findIndex((a) => a.id === id)
      if (indiceAttuale !== -1) {
        elenco.value = elenco.value.with(indiceAttuale, precedente)
      }
      errore.value = e instanceof Error ? e : new Error(String(e))
    } finally {
      inSincronizzazione.value.delete(id)
    }
  }

  async function elimina(id: string) {
    const indice = elenco.value.findIndex((a) => a.id === id)
    const rimossa = elenco.value[indice]
    if (indice === -1 || rimossa === undefined) return

    // OTTIMISTICO
    elenco.value = elenco.value.toSpliced(indice, 1)

    try {
      await eliminaAttivita(id)
    } catch (e) {
      // ROLLBACK nella POSIZIONE originale, non in fondo
      elenco.value = elenco.value.toSpliced(indice, 0, rimossa)
      errore.value = e instanceof Error ? e : new Error(String(e))
    }
  }

  function stanoSincronizzando(id: string): boolean {
    return inSincronizzazione.value.has(id)
  }

  return {
    elenco,
    filtro,
    inCaricamento,
    errore,
    visibili,
    conteggi,
    staSincronizzando,
    carica,
    aggiungi,
    commuta,
    elimina,
    stanoSincronizzando,
  }
})
```

```vue
<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'
import { useStoreAttivita } from '@/store/attivita'

const store = useStoreAttivita()
const { visibili, conteggi, filtro, inCaricamento, errore } = storeToRefs(store)
const { carica, commuta, elimina, stanoSincronizzando } = store

onMounted(carica)
</script>

<template>
  <p v-if="errore" role="alert">{{ errore.message }}</p>
  <p v-if="inCaricamento" role="status">Caricamento…</p>

  <nav aria-label="Filtro">
    <button
      v-for="opzione in (['tutte', 'da-fare', 'completate'] as const)"
      :key="opzione"
      :aria-pressed="filtro === opzione"
      @click="filtro = opzione"
    >
      {{ opzione }}
    </button>
  </nav>

  <ul>
    <li
      v-for="attivita in visibili"
      :key="attivita.id"
      :style="{ opacity: stanoSincronizzando(attivita.id) ? 0.5 : 1 }"
    >
      <input
        :id="`fatto-${attivita.id}`"
        type="checkbox"
        :checked="attivita.completata"
        @change="commuta(attivita.id)"
      />
      <label :for="`fatto-${attivita.id}`">{{ attivita.testo }}</label>

      <span v-if="stanoSincronizzando(attivita.id)" class="solo-screen-reader">
        sincronizzazione in corso
      </span>

      <button @click="elimina(attivita.id)">
        Elimina<span class="solo-screen-reader"> {{ attivita.testo }}</span>
      </button>
    </li>
  </ul>

  <p>{{ conteggi.daFare }} da fare su {{ conteggi.tutte }}</p>
</template>
```

```
# I punti che fanno funzionare l'aggiornamento ottimistico:
#
# 1. RICORDARE IL VALORE ESATTO, non ricalcolarlo.
#    Nel rollback di 'commuta' si ripristina 'precedente',
#    non si inverte di nuovo il booleano: nel frattempo
#    un'altra operazione potrebbe averlo cambiato.
#
# 2. RIPRISTINARE NELLA POSIZIONE ORIGINALE.
#    In 'elimina' il rollback usa toSpliced(indice, 0, rimossa):
#    rimettere in fondo cambierebbe l'ordine sotto gli occhi
#    dell'utente.
#
# 3. RICERCARE L'INDICE AL MOMENTO DEL ROLLBACK.
#    Fra l'aggiornamento ottimistico e l'errore possono
#    essere avvenute altre modifiche: l'indice salvato prima
#    potrebbe non essere più valido.
#
# 4. LO STATO PER RIGA, non globale.
#    inSincronizzazione è un Set: due operazioni contemporanee
#    su righe diverse mostrano entrambe il proprio stato.
#
# 5. L'ANNUNCIO PER GLI SCREEN READER.
#    L'opacità ridotta comunica "in corso" solo a chi vede.
#
# PERCHÉ FUNZIONA IN VUE SENZA ACCORGIMENTI:
#   in React lo stesso codice richiederebbe attenzione alle
#   closure che catturano valori vecchi. In Vue i ref sono
#   contenitori: leggere .value dà sempre il valore corrente,
#   anche dentro una funzione asincrona iniziata molto prima.
```

---

### Esercizio 4 — Un componente headless con slot con scope

**Obiettivo:** un componente che gestisce la logica di una tabella ordinabile e paginata, lasciando l'intero aspetto al chiamante.

```vue
<!-- SOLUZIONE — src/componenti/TabellaDati.vue -->
<script setup lang="ts" generic="T extends Record<string, unknown>">
import { computed, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    righe: readonly T[]
    chiaveDi: (riga: T) => string | number
    perPagina?: number
  }>(),
  { perPagina: 25 },
)

type Direzione = 'crescente' | 'decrescente'

const campoOrdinamento = ref<keyof T | null>(null)
const direzione = ref<Direzione>('crescente')
const pagina = ref(1)
const ricerca = ref('')

const filtrate = computed(() => {
  const termine = ricerca.value.trim().toLowerCase()
  if (termine === '') return props.righe

  return props.righe.filter((riga) =>
    Object.values(riga).some((v) => String(v).toLowerCase().includes(termine)),
  )
})

const ordinate = computed(() => {
  const campo = campoOrdinamento.value
  if (campo === null) return filtrate.value

  const segno = direzione.value === 'crescente' ? 1 : -1

  return filtrate.value.toSorted((a, b) => {
    const va = a[campo]
    const vb = b[campo]

    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * segno
    return String(va).localeCompare(String(vb), 'it') * segno
  })
})

const totalePagine = computed(() =>
  Math.max(1, Math.ceil(ordinate.value.length / props.perPagina)),
)

const visibili = computed(() => {
  const inizio = (pagina.value - 1) * props.perPagina
  return ordinate.value.slice(inizio, inizio + props.perPagina)
})

function ordinaPer(campo: keyof T) {
  if (campoOrdinamento.value === campo) {
    direzione.value = direzione.value === 'crescente' ? 'decrescente' : 'crescente'
  } else {
    campoOrdinamento.value = campo
    direzione.value = 'crescente'
  }
  pagina.value = 1
}

/** Lo stato di ordinamento per l'attributo aria-sort. */
function ariaSort(campo: keyof T): 'ascending' | 'descending' | 'none' {
  if (campoOrdinamento.value !== campo) return 'none'
  return direzione.value === 'crescente' ? 'ascending' : 'descending'
}

function vaiA(numero: number) {
  pagina.value = Math.min(Math.max(1, numero), totalePagine.value)
}
</script>

<template>
  <!-- Tutto lo stato e tutti i comandi vengono ESPOSTI.
       Il componente non disegna nulla di proprio. -->
  <slot
    :righe="visibili"
    :totale="ordinate.length"
    :pagina="pagina"
    :totale-pagine="totalePagine"
    :ricerca="ricerca"
    :ordina-per="ordinaPer"
    :aria-sort="ariaSort"
    :vai-a="vaiA"
    :aggiorna-ricerca="(v: string) => { ricerca = v; pagina = 1 }"
    :chiave-di="chiaveDi"
  />
</template>
```

```vue
<!-- L'uso: il chiamante decide OGNI aspetto della resa -->
<script setup lang="ts">
import TabellaDati from '@/componenti/TabellaDati.vue'

type Fattura = {
  id: string
  numero: string
  cliente: string
  importo: number
  [chiave: string]: unknown
}

const fatture: Fattura[] = []
</script>

<template>
  <TabellaDati :righe="fatture" :chiave-di="(f) => f.id" :per-pagina="20">
    <template
      #default="{ righe, totale, pagina, totalePagine, ricerca, ordinaPer, ariaSort, vaiA, aggiornaRicerca }"
    >
      <label for="cerca">Cerca</label>
      <input
        id="cerca"
        type="search"
        :value="ricerca"
        @input="aggiornaRicerca(($event.target as HTMLInputElement).value)"
      />

      <p role="status" aria-live="polite">{{ totale }} risultati</p>

      <table>
        <caption>
          Fatture — pagina {{ pagina }} di {{ totalePagine }}
        </caption>

        <thead>
          <tr>
            <th scope="col" :aria-sort="ariaSort('numero')">
              <button type="button" @click="ordinaPer('numero')">Numero</button>
            </th>
            <th scope="col" :aria-sort="ariaSort('cliente')">
              <button type="button" @click="ordinaPer('cliente')">Cliente</button>
            </th>
            <th scope="col" :aria-sort="ariaSort('importo')">
              <button type="button" @click="ordinaPer('importo')">Importo</button>
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="riga in righe" :key="riga.id">
            <th scope="row">{{ riga.numero }}</th>
            <td>{{ riga.cliente }}</td>
            <td class="numerico">{{ riga.importo }}</td>
          </tr>
        </tbody>
      </table>

      <nav aria-label="Paginazione">
        <button type="button" :disabled="pagina === 1" @click="vaiA(pagina - 1)">
          Precedente
        </button>
        <span>{{ pagina }} / {{ totalePagine }}</span>
        <button type="button" :disabled="pagina === totalePagine" @click="vaiA(pagina + 1)">
          Successiva
        </button>
      </nav>
    </template>
  </TabellaDati>
</template>
```

```
# Il pattern headless, e perché conta:
#
# Il componente possiede la LOGICA — ordinamento, filtro,
# paginazione, stato ARIA — e nessuna decisione di aspetto.
# Il chiamante riceve tutto tramite lo slot con scope e
# disegna come vuole.
#
# CONSEGUENZE:
#   · lo stesso componente serve una tabella, una griglia
#     di schede e un elenco mobile
#   · l'aspetto non richiede props di configurazione che
#     crescono all'infinito (variante, dimensione, colore…)
#   · la logica si testa una volta sola
#
# generic="T extends Record<string, unknown>" rende il
# componente tipizzato: 'riga' nello slot ha il tipo di
# Fattura, e riga.inesistente è un errore di compilazione.
#
# È l'equivalente delle render props di React, con due
# differenze: la sintassi è più leggibile, e non c'è
# il problema dell'identità della funzione che cambia
# a ogni rendering.
```

---

### Esercizio 5 — Le stesse funzionalità in React e in Vue

**Obiettivo:** un contatore con validazione, cronologia e annullamento, scritto nei due framework. Confrontare cosa serve in ciascuno.

```tsx
// VERSIONE REACT
import { useCallback, useMemo, useState } from 'react'

type Voce = { valore: number; quando: number }

export function ContatoreReact({ minimo = 0, massimo = 10 }) {
  const [valore, impostaValore] = useState(minimo)
  const [cronologia, impostaCronologia] = useState<Voce[]>([])

  // useMemo: senza, si ricalcolerebbe a ogni rendering
  const puoIncrementare = useMemo(() => valore < massimo, [valore, massimo])
  const puoDecrementare = useMemo(() => valore > minimo, [valore, minimo])

  // useCallback: necessario se passato a un figlio memoizzato
  const cambia = useCallback(
    (delta: number) => {
      impostaValore((precedente) => {
        const nuovo = Math.min(massimo, Math.max(minimo, precedente + delta))
        if (nuovo === precedente) return precedente

        impostaCronologia((c) => [...c, { valore: precedente, quando: Date.now() }])
        return nuovo
      })
    },
    [minimo, massimo],
  )

  const annulla = useCallback(() => {
    impostaCronologia((c) => {
      const ultima = c.at(-1)
      if (!ultima) return c
      impostaValore(ultima.valore)
      return c.slice(0, -1)
    })
  }, [])

  return (
    <div>
      <p aria-live="polite">{valore}</p>
      <button onClick={() => cambia(-1)} disabled={!puoDecrementare}>−</button>
      <button onClick={() => cambia(1)} disabled={!puoIncrementare}>+</button>
      <button onClick={annulla} disabled={cronologia.length === 0}>Annulla</button>
    </div>
  )
}
```

```vue
<!-- VERSIONE VUE -->
<script setup lang="ts">
import { computed, ref } from 'vue'

type Voce = { valore: number; quando: number }

const props = withDefaults(defineProps<{ minimo?: number; massimo?: number }>(), {
  minimo: 0,
  massimo: 10,
})

const valore = ref(props.minimo)
const cronologia = ref<Voce[]>([])

// computed: la cache è automatica, e si invalida da sola
const puoIncrementare = computed(() => valore.value < props.massimo)
const puoDecrementare = computed(() => valore.value > props.minimo)

// Nessun useCallback: l'identità della funzione non conta,
// perché Vue non ridisegna i figli quando il genitore cambia
function cambia(delta: number) {
  const nuovo = Math.min(props.massimo, Math.max(props.minimo, valore.value + delta))
  if (nuovo === valore.value) return

  cronologia.value.push({ valore: valore.value, quando: Date.now() })
  valore.value = nuovo
}

function annulla() {
  const ultima = cronologia.value.pop()
  if (ultima) valore.value = ultima.valore
}
</script>

<template>
  <div>
    <p aria-live="polite">{{ valore }}</p>
    <button :disabled="!puoDecrementare" @click="cambia(-1)">−</button>
    <button :disabled="!puoIncrementare" @click="cambia(1)">+</button>
    <button :disabled="cronologia.length === 0" @click="annulla">Annulla</button>
  </div>
</template>
```

```
# IL CONFRONTO, riga per riga:
#
#                              REACT              VUE
#   ────────────────────────────────────────────────────────
#   Valori derivati            useMemo            computed
#                              (dipendenze a mano) (automatiche)
#
#   Funzioni stabili           useCallback        non serve
#                              (dipendenze a mano)
#
#   Aggiornare un array        [...c, nuovo]      push()
#                              (immutabile        (Vue intercetta
#                               obbligatorio)      i metodi)
#
#   Leggere il valore corrente forma funzionale   valore.value
#                              di setState        (sempre attuale)
#
#   Righe di logica            ~30                ~18
#
#
# DOVE VUE È PIÙ SEMPLICE:
#   · le dipendenze delle computed sono dedotte: non si
#     possono dimenticare né sbagliare
#   · non serve memoizzare: un figlio non si ridisegna
#     perché il genitore è cambiato
#   · la mutazione è ammessa: push, splice e sort funzionano
#
# DOVE REACT È PIÙ PREVEDIBILE:
#   · l'immutabilità obbligatoria rende ovvio quando lo stato
#     cambia, e semplifica il debug della cronologia
#   · una funzione è una funzione: non c'è un Proxy fra te
#     e i dati, e il modello mentale è più piccolo
#   · nessuna distinzione fra ref e reactive, nessun .value
#
# NON C'È UN VINCITORE. Vue fa meno lavoro a runtime e
# richiede meno cerimonie; React ha un modello mentale più
# uniforme. La scelta dipende dal team e dall'ecosistema,
# non da una superiorità tecnica.
```

---

## C2. Mini-progetto: la dashboard, in Vue

Lo stesso progetto di `tutorial_07_react.md`, ricostruito in Vue per rendere il confronto concreto.

### Struttura

```
dashboard-vue/
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── router/index.ts
│   ├── store/
│   │   ├── autenticazione.ts
│   │   └── fatture.ts
│   ├── composables/
│   │   └── useAnnunci.ts
│   ├── componenti/
│   │   ├── SchedaIndicatore.vue
│   │   └── TabellaDati.vue
│   └── pagine/
│       ├── Accesso.vue
│       ├── Panoramica.vue
│       └── Fatture.vue
```

### `src/store/autenticazione.ts`

```typescript
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type Utente = {
  readonly id: string
  readonly nome: string
  readonly ruoli: readonly string[]
}

export const useStoreAutenticazione = defineStore('autenticazione', () => {
  const utente = ref<Utente | null>(null)
  const inVerifica = ref(false)

  const autenticato = computed(() => utente.value !== null)

  function haRuolo(ruolo: string): boolean {
    return utente.value?.ruoli.includes(ruolo) ?? false
  }

  async function accedi(email: string, password: string) {
    inVerifica.value = true
    try {
      utente.value = await autenticaUtente(email, password)
      sessionStorage.setItem('utente', JSON.stringify(utente.value))
    } finally {
      inVerifica.value = false
    }
  }

  function esci() {
    utente.value = null
    sessionStorage.removeItem('utente')
  }

  function ripristina() {
    try {
      const grezzo = sessionStorage.getItem('utente')
      if (grezzo === null) return

      const analizzato: unknown = JSON.parse(grezzo)
      if (typeof analizzato === 'object' && analizzato !== null && 'id' in analizzato) {
        utente.value = analizzato as Utente
      }
    } catch {
      sessionStorage.removeItem('utente')
    }
  }

  return { utente, inVerifica, autenticato, haRuolo, accedi, esci, ripristina }
})
```

### `src/pagine/Fatture.vue`

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useStoreFatture } from '@/store/fatture'
import TabellaDati from '@/componenti/TabellaDati.vue'

const rotta = useRoute()
const router = useRouter()
const store = useStoreFatture()
const { visibili, inCaricamento, errore } = storeToRefs(store)

// Lo stato dei filtri sta nell'URL: la pagina è condivisibile
// e il pulsante indietro funziona
const filtri = computed(() => ({
  pagina: Number(rotta.query['pagina'] ?? 1),
  ricerca: String(rotta.query['ricerca'] ?? ''),
  stato: String(rotta.query['stato'] ?? ''),
}))

function aggiornaFiltro(chiave: string, valore: string) {
  const query = { ...rotta.query }

  if (valore === '') {
    delete query[chiave]
  } else {
    query[chiave] = valore
  }

  // Cambiando un filtro si torna alla prima pagina
  if (chiave !== 'pagina') delete query['pagina']

  router.replace({ query })
}
</script>

<template>
  <section aria-labelledby="titolo-fatture">
    <h1 id="titolo-fatture">Fatture</h1>

    <p v-if="errore" role="alert">{{ errore.message }}</p>

    <div class="filtri">
      <label for="ricerca">Cerca</label>
      <input
        id="ricerca"
        type="search"
        :value="filtri.ricerca"
        @input="aggiornaFiltro('ricerca', ($event.target as HTMLInputElement).value)"
      />

      <label for="stato">Stato</label>
      <select
        id="stato"
        :value="filtri.stato"
        @change="aggiornaFiltro('stato', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">Tutti</option>
        <option value="emessa">Emesse</option>
        <option value="pagata">Pagate</option>
      </select>
    </div>

    <p role="status" aria-live="polite">
      {{ inCaricamento ? 'Caricamento…' : `${visibili.length} fatture` }}
    </p>

    <TabellaDati :righe="visibili" :chiave-di="(f) => f.id">
      <template #default="{ righe, ordinaPer, ariaSort }">
        <table>
          <caption>Fatture del periodo selezionato</caption>
          <thead>
            <tr>
              <th scope="col" :aria-sort="ariaSort('numero')">
                <button type="button" @click="ordinaPer('numero')">Numero</button>
              </th>
              <th scope="col" :aria-sort="ariaSort('importo')">
                <button type="button" @click="ordinaPer('importo')">Importo</button>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="riga in righe" :key="riga.id">
              <th scope="row">{{ riga.numero }}</th>
              <td class="numerico">{{ riga.importo }}</td>
            </tr>
          </tbody>
        </table>
      </template>
    </TabellaDati>
  </section>
</template>
```

### L'accessibilità del routing

```typescript
// src/composables/useAnnunci.ts
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

/**
 * In una SPA il cambio di pagina non sposta il focus e non
 * viene annunciato: l'utente di uno screen reader non sa
 * che è successo qualcosa. Va rimesso a mano.
 */
export function useAnnunciNavigazione() {
  const router = useRouter()
  const annuncio = ref('')

  router.afterEach((a) => {
    const titolo = typeof a.meta['titolo'] === 'string' ? a.meta['titolo'] : a.name
    annuncio.value = `Pagina ${String(titolo)}`
    document.title = `${String(titolo)} — Acme`

    // Il focus sul titolo della pagina nuova
    requestAnimationFrame(() => {
      const h1 = document.querySelector<HTMLElement>('main h1')
      h1?.focus()
    })
  })

  return { annuncio }
}
```

```vue
<!-- src/App.vue -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { useStoreAutenticazione } from '@/store/autenticazione'
import { useAnnunciNavigazione } from '@/composables/useAnnunci'

const autenticazione = useStoreAutenticazione()
const { annuncio } = useAnnunciNavigazione()

onMounted(autenticazione.ripristina)
</script>

<template>
  <a href="#contenuto" class="salta-al-contenuto">Vai al contenuto principale</a>

  <!-- La live region esiste sempre, anche vuota -->
  <p role="status" aria-live="polite" class="solo-screen-reader">{{ annuncio }}</p>

  <header>
    <nav aria-label="Principale">
      <RouterLink :to="{ name: 'panoramica' }">Panoramica</RouterLink>
      <RouterLink :to="{ name: 'fatture' }">Fatture</RouterLink>
    </nav>
  </header>

  <main id="contenuto">
    <RouterView v-slot="{ Component }">
      <Suspense>
        <component :is="Component" />
        <template #fallback>
          <p role="status">Caricamento della pagina…</p>
        </template>
      </Suspense>
    </RouterView>
  </main>
</template>
```

### Verifica

```
# Gli stessi controlli di tutorial_07, più quelli specifici di Vue:
#
# 1. ROUTING E PROTEZIONE
#    /fatture da anonimo → reindirizza ad /accesso con ?da=
#    Dopo l'accesso, si torna alla destinazione originale
#
# 2. STATO NELL'URL
#    Filtra, copia l'indirizzo, apri in una scheda nuova:
#    gli stessi filtri. Il pulsante indietro li ripercorre.
#
# 3. REATTIVITÀ
#    Vue DevTools → scheda Components: si vedono ref e computed
#    con i valori correnti, e quali dipendenze hanno.
#    Scheda Pinia: lo stato dello store, e la cronologia
#    delle mutazioni.
#
# 4. NESSUN AGGIORNAMENTO SUPERFLUO
#    Vue DevTools → Performance → Component Render.
#    Cambiando un filtro, si devono aggiornare SOLO i
#    componenti che dipendono da quel dato — non l'intera
#    pagina come farebbe React senza memo.
#
# 5. ACCESSIBILITÀ
#    Tab dall'inizio: il salto al contenuto è il primo.
#    Cambiando pagina, il focus va sull'h1 e lo screen
#    reader annuncia il nome della pagina.
#
# 6. TIPI
#    pnpm exec vue-tsc --noEmit
#    (vue-tsc, non tsc: verifica anche i template)
```

```
# Il confronto con la versione React, a parità di funzionalità:
#
#                            React      Vue
#   ─────────────────────────────────────────────
#   File del progetto          24        21
#   Righe di codice          ~1.450    ~1.180
#   useMemo / useCallback       19         0
#   Dipendenze dichiarate       31         4
#     a mano (deps array)
#
# La differenza NON è che Vue sia migliore: è che sposta
# il lavoro dal programmatore al runtime. Vue traccia le
# dipendenze a runtime con i Proxy; React le fa dichiarare
# e non traccia nulla.
#
# Il costo di Vue è un modello mentale con più concetti
# (ref contro reactive, .value, i modificatori del template).
# Il costo di React sono 31 array di dipendenze da tenere
# corretti a mano, e 19 memoizzazioni da valutare — che il
# React Compiler sta rendendo superflue.
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Il sistema di reattività dall'interno

Le API di reattività di Vue sono disponibili anche fuori dai componenti: `@vue/reactivity` è un pacchetto autonomo, utilizzabile in qualunque contesto JavaScript.

```typescript
import { effect, effectScope, reactive, ref, stop } from 'vue'

// effect è ciò che sta sotto watchEffect e al rendering
const contatore = ref(0)

const eseguibile = effect(() => {
  console.log('conteggio:', contatore.value)
})

contatore.value++ // l'effetto si riesegue

// Fermarlo
stop(eseguibile)
contatore.value++ // non si riesegue più
```

### `effectScope`

```typescript
// Raccoglie più effetti per fermarli tutti insieme.
// È il meccanismo con cui Vue ferma automaticamente gli
// effetti di un componente allo smontaggio.
const ambito = effectScope()

ambito.run(() => {
  const a = ref(0)
  const b = computed(() => a.value * 2)

  watch(a, () => console.log('a è cambiato'))
  watchEffect(() => console.log(b.value))
})

// Un solo stop ferma watch, watchEffect e le computed
ambito.stop()
```

```typescript
// Il caso d'uso: uno store globale creato fuori da un componente,
// che va potuto smontare (nei test, o in un'applicazione
// con più istanze)
function creaStoreIsolato() {
  const ambito = effectScope(true) // 'detached': non si lega al genitore

  const stato = ambito.run(() => {
    const elenco = ref<string[]>([])
    const conteggio = computed(() => elenco.value.length)

    watch(elenco, (nuovo) => localStorage.setItem('elenco', JSON.stringify(nuovo)), {
      deep: true,
    })

    return { elenco, conteggio }
  })

  return { ...stato!, distruggi: () => ambito.stop() }
}
```

### Personalizzare il tracciamento

```typescript
import { customRef } from 'vue'

/** Un ref che ritarda l'aggiornamento dei suoi lettori. */
function refRitardato<T>(valore: T, ritardo = 300) {
  let temporizzatore: ReturnType<typeof setTimeout> | null = null

  return customRef<T>((traccia, scatena) => ({
    get() {
      traccia() // registra il lettore
      return valore
    },
    set(nuovo) {
      if (temporizzatore !== null) clearTimeout(temporizzatore)

      temporizzatore = setTimeout(() => {
        valore = nuovo
        scatena() // notifica i lettori
      }, ritardo)
    },
  }))
}
```

```typescript
import { toRef, toValue, type MaybeRefOrGetter } from 'vue'

/**
 * toValue accetta un valore, un ref o un getter e restituisce
 * il valore. È il modo di scrivere composables che accettano
 * qualunque forma di ingresso.
 */
function useRaddoppio(fonte: MaybeRefOrGetter<number>) {
  return computed(() => toValue(fonte) * 2)
}

// Tutte e tre le chiamate funzionano
useRaddoppio(5)
useRaddoppio(ref(5))
useRaddoppio(() => stato.conteggio)
```

### Gli strumenti di diagnosi

```typescript
import { onRenderTracked, onRenderTriggered } from 'vue'

// Solo in sviluppo: dicono QUALE dipendenza ha causato
// un aggiornamento. Utile quando un componente si aggiorna
// e non si capisce perché.
onRenderTracked((evento) => {
  console.log('dipendenza tracciata', evento.key, evento.target)
})

onRenderTriggered((evento) => {
  console.log('aggiornamento causato da', evento.key, evento.oldValue, '→', evento.newValue)
})
```

```typescript
import { watch } from 'vue'

// onTrack e onTrigger sulle singole watch
watch(fonte, gestore, {
  onTrack: (evento) => console.log('traccia', evento),
  onTrigger: (evento) => console.log('scatena', evento),
})
```

---

## D2. Performance e Vapor Mode

### Cosa Vue ottimizza da solo

Il compilatore dei template analizza staticamente il markup e produce codice che salta il confronto dove non serve.

```vue
<template>
  <div class="contenitore">
    <!-- STATICO: compilato una volta, mai riconfrontato -->
    <h1>Titolo fisso</h1>
    <p>Testo che non cambia mai</p>

    <!-- DINAMICO: marcato con un patch flag che dice
         ESATTAMENTE cosa può cambiare -->
    <p>{{ messaggio }}</p>
    <div :class="classe">…</div>
  </div>
</template>
```

```
Il compilatore produce:

  · hoisting statico: i nodi che non cambiano sono creati
    una volta sola, fuori dalla funzione di rendering

  · patch flags: ogni nodo dinamico porta un numero che dice
    cosa confrontare — solo il testo, solo la classe, solo
    le props. Il confronto non percorre l'intero nodo.

  · block tree: i nodi dinamici sono raccolti in un array
    piatto. L'aggiornamento li percorre direttamente, senza
    attraversare l'albero.

È il motivo per cui Vue non ha bisogno dell'equivalente
di React.memo: il lavoro di confronto è già ridotto
al minimo dal compilatore.
```

### Le ottimizzazioni che restano a carico tuo

```vue
<script setup lang="ts">
import { computed, shallowRef, ref } from 'vue'

// 1. shallowRef per le strutture grandi che si sostituiscono
//    per intero: evita di rendere reattivo l'intero albero
const righe = shallowRef<Fattura[]>([])

// 2. computed invece di metodi nel template
const totale = computed(() => righe.value.reduce((s, f) => s + f.importo, 0))

// 3. v-once per il contenuto che non cambia mai
// 4. v-memo per saltare l'aggiornamento a condizioni date
</script>

<template>
  <!-- v-once: disegnato una volta, mai aggiornato -->
  <header v-once>
    <h1>{{ titoloStatico }}</h1>
  </header>

  <!-- v-memo: salta l'aggiornamento se le dipendenze
       elencate non sono cambiate. Da usare solo su liste
       lunghe, dopo aver misurato. -->
  <div v-for="riga in righe" :key="riga.id" v-memo="[riga.id, riga.selezionata]">
    <!-- Questo sottoalbero si aggiorna solo se id o
         selezionata cambiano -->
    <ComponentePesante :riga="riga" />
  </div>
</template>
```

```vue
<script setup lang="ts">
// 5. La virtualizzazione: oltre qualche centinaio di righe,
//    la soluzione è non creare i nodi
import { useVirtualList } from '@vueuse/core'
import { ref } from 'vue'

const tutte = ref<Fattura[]>([])

const { list, containerProps, wrapperProps } = useVirtualList(tutte, {
  itemHeight: 48,
  overscan: 8,
})
</script>

<template>
  <div v-bind="containerProps" style="height: 600px">
    <div v-bind="wrapperProps">
      <div v-for="{ data, index } in list" :key="data.id" style="height: 48px">
        {{ data.numero }}
      </div>
    </div>
  </div>
</template>
```

### Vapor Mode

Vapor Mode è una modalità di compilazione che elimina del tutto il virtual DOM: il template viene compilato in operazioni dirette sul DOM.

```
                      Vue classico            Vapor Mode

  Rendering           funzione → VDOM →       operazioni dirette
                      confronto → DOM         sul DOM

  Runtime incluso     ~34 kB gzip             molto ridotto:
                                              solo la reattività

  Aggiornamento       confronto del           il ref è cablato
                      sottoalbero con         al nodo: aggiorna
                      i patch flag            quel nodo e basta

  Compatibilità       tutto                   un sottoinsieme:
                                              niente API che
                                              richiedono il VDOM
```

```vue
<!-- Un componente Vapor si dichiara nel file -->
<script setup vapor lang="ts">
import { ref } from 'vue'

const conteggio = ref(0)
</script>

<template>
  <button @click="conteggio++">{{ conteggio }}</button>
</template>
```

```
Lo stato di Vapor Mode: è in sviluppo attivo e non ancora
stabile per la produzione al momento in cui questo tutorial
è scritto. Va verificato sul repository ufficiale prima di
adottarlo.

Il concetto conta comunque, perché è la stessa direzione
presa da Svelte (tutorial 09) e da Solid: compilare in
operazioni dirette invece di confrontare alberi a runtime.
La differenza è che Vue lo offre come modalità aggiuntiva,
conservando la compatibilità con l'esistente.
```

### Misurare

```
Vue DevTools:

  Components    l'albero, con ref e computed di ogni istanza
                e il loro valore corrente

  Timeline      gli eventi di rendering: quali componenti
                si sono aggiornati e quando

  Pinia         lo stato degli store e la cronologia
                delle mutazioni

  Performance   il tempo di rendering per componente

E in aggiunta, onRenderTriggered dice QUALE dipendenza
ha causato un aggiornamento — l'equivalente del
"why did this render" di React DevTools.
```

---

## D3. Componenti accessibili in Vue

Vale tutto ciò che è stato detto in `tutorial_01_html5.md` e in `tutorial_07_react.md`. Qui le specificità di Vue.

### `useId`

```vue
<script setup lang="ts">
import { useId } from 'vue'

// Vue 3.5: un identificativo stabile fra server e client.
// Math.random() romperebbe l'idratazione con SSR.
const id = useId()

defineProps<{ etichetta: string; aiuto?: string; errore?: string }>()

const valore = defineModel<string>({ required: true })
</script>

<template>
  <div class="campo">
    <label :for="id">{{ etichetta }}</label>

    <input
      :id="id"
      v-model="valore"
      :aria-invalid="errore !== undefined"
      :aria-describedby="
        [aiuto ? `${id}-aiuto` : null, errore ? `${id}-errore` : null].filter(Boolean).join(' ') ||
        undefined
      "
    />

    <p v-if="aiuto" :id="`${id}-aiuto`" class="aiuto">{{ aiuto }}</p>
    <p v-if="errore" :id="`${id}-errore`" role="alert" class="errore">{{ errore }}</p>
  </div>
</template>
```

### `v-show` e l'albero di accessibilità

```vue
<template>
  <!-- ⚠ v-show usa display:none, che toglie l'elemento
       anche dall'albero di accessibilità. Per un pannello
       che deve restare annunciabile serve un'altra tecnica. -->
  <div v-show="aperto">…</div>

  <!-- ✅ Per nascondere visivamente MANTENENDO l'accesso -->
  <div :class="{ 'solo-screen-reader': !visibile }">…</div>

  <!-- ✅ Per il contenuto veramente nascosto, l'attributo
       hidden è più esplicito -->
  <div :hidden="!aperto">…</div>

  <!-- ✅ inert rende un sottoalbero non interattivo e
       invisibile alle tecnologie assistive, restando visibile -->
  <div :inert="modaleAperta">…</div>
</template>
```

### La gestione del focus con `<Transition>`

```vue
<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const aperto = ref(false)
const primoElemento = ref<HTMLElement | null>(null)
const comandoApertura = ref<HTMLElement | null>(null)

watch(aperto, async (nuovo) => {
  if (nuovo) {
    // Il DOM non è ancora aggiornato: nextTick attende
    await nextTick()
    primoElemento.value?.focus()
  } else {
    // Alla chiusura, il focus torna al comando che aveva aperto
    comandoApertura.value?.focus()
  }
})
</script>

<template>
  <button ref="comandoApertura" :aria-expanded="aperto" @click="aperto = !aperto">
    Apri il pannello
  </button>

  <Transition name="dissolvenza">
    <div v-if="aperto" role="region" aria-label="Pannello dei filtri">
      <button ref="primoElemento">Primo comando</button>
    </div>
  </Transition>
</template>
```

Con `<Transition>` il `nextTick` non basta sempre: durante l'animazione di ingresso l'elemento potrebbe non essere ancora focalizzabile. L'evento `@after-enter` è più affidabile.

```vue
<template>
  <Transition name="dissolvenza" @after-enter="primoElemento?.focus()">
    <div v-if="aperto">…</div>
  </Transition>
</template>
```

### Le regole del linter

```javascript
// eslint.config.js
import vue from 'eslint-plugin-vue'
import vuejsAccessibility from 'eslint-plugin-vuejs-accessibility'

export default [
  ...vue.configs['flat/recommended'],
  ...vuejsAccessibility.configs['flat/recommended'],
  {
    rules: {
      // Intercetta i div cliccabili senza tastiera
      'vuejs-accessibility/click-events-have-key-events': 'error',
      'vuejs-accessibility/label-has-for': 'error',
      'vuejs-accessibility/form-control-has-label': 'error',
      // v-for senza key
      'vue/require-v-for-key': 'error',
      // v-if e v-for sullo stesso elemento
      'vue/no-use-v-if-with-v-for': 'error',
    },
  },
]
```

---

## D4. Testare i componenti Vue

```powershell
pnpm add -D vitest @vue/test-utils @testing-library/vue @testing-library/user-event happy-dom
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./test/preparazione.ts'],
  },
})
```

### Testing Library: testare come usa l'utente

```typescript
import { render, screen } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import ModuloContatti from '@/componenti/ModuloContatti.vue'

describe('ModuloContatti', () => {
  it('mostra un errore quando l email non è valida', async () => {
    const utente = userEvent.setup()
    render(ModuloContatti)

    // Le stesse query di React: per RUOLO e per ETICHETTA
    await utente.type(screen.getByLabelText('Email'), 'non-valida')
    await utente.click(screen.getByRole('button', { name: 'Invia' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Indirizzo non valido')
  })

  it('emette l evento con i dati corretti', async () => {
    const utente = userEvent.setup()
    const { emitted } = render(ModuloContatti)

    await utente.type(screen.getByLabelText('Nome'), 'Anna')
    await utente.type(screen.getByLabelText('Email'), 'anna@example.it')
    await utente.click(screen.getByRole('button', { name: 'Invia' }))

    // emitted() raccoglie gli eventi emessi dal componente
    expect(emitted()['invia']).toBeTruthy()
    expect(emitted()['invia']?.[0]).toEqual([{ nome: 'Anna', email: 'anna@example.it' }])
  })
})
```

### Testare i composables senza montare nulla

```typescript
import { describe, it, expect } from 'vitest'
import { effectScope, ref, nextTick } from 'vue'
import { useRicerca } from '@/composables/useRicerca'

describe('useRicerca', () => {
  it('non cerca sotto la lunghezza minima', async () => {
    // effectScope permette di usare i composables fuori
    // da un componente, e di fermarli alla fine
    const ambito = effectScope()

    const risultato = ambito.run(() => {
      const termine = ref('')
      const { stato } = useRicerca(termine, async () => [])
      return { termine, stato }
    })!

    risultato.termine.value = 'a'
    await nextTick()

    expect(risultato.stato.value.stato).toBe('inattiva')

    ambito.stop()
  })
})
```

```typescript
// I composables che usano gli hook di ciclo di vita
// vanno testati montando un componente minimo
import { defineComponent } from 'vue'
import { mount } from '@vue/test-utils'

function conComposable<T>(composable: () => T) {
  let risultato!: T

  const componente = defineComponent({
    setup() {
      risultato = composable()
      return () => null // nessun template
    },
  })

  const wrapper = mount(componente)
  return { risultato, wrapper }
}

it('rimuove il listener allo smontaggio', () => {
  const rimuovi = vi.spyOn(window, 'removeEventListener')

  const { wrapper } = conComposable(() => useEventoFinestra('resize', () => {}))
  wrapper.unmount()

  expect(rimuovi).toHaveBeenCalledWith('resize', expect.any(Function), undefined)
})
```

### Testare uno store Pinia

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useStoreAttivita } from '@/store/attivita'

describe('store attivita', () => {
  beforeEach(() => {
    // Un Pinia nuovo per ogni test: nessuno stato condiviso
    setActivePinia(createPinia())
  })

  it('ripristina lo stato quando l aggiornamento fallisce', async () => {
    const store = useStoreAttivita()
    store.elenco = [{ id: '1', testo: 'Prova', completata: false, creataIl: '' }]

    vi.mocked(aggiornaAttivita).mockRejectedValue(new Error('rete'))

    await store.commuta('1')

    // L'aggiornamento ottimistico è stato annullato
    expect(store.elenco[0]?.completata).toBe(false)
    expect(store.errore?.message).toBe('rete')
  })
})
```

```typescript
// Montare un componente che usa uno store
import { createTestingPinia } from '@pinia/testing'
import { render } from '@testing-library/vue'

it('mostra le attività dello store', () => {
  render(ElencoAttivita, {
    global: {
      plugins: [
        createTestingPinia({
          // Le azioni sono automaticamente sostituite da spie
          createSpy: vi.fn,
          initialState: {
            attivita: { elenco: [{ id: '1', testo: 'Prova', completata: false }] },
          },
        }),
      ],
    },
  })

  expect(screen.getByText('Prova')).toBeInTheDocument()
})
```

```
Cosa testare, e cosa no — vale lo stesso criterio di React:

  ✅ cosa l'utente VEDE dopo un'interazione
  ✅ quali eventi il componente EMETTE
  ✅ i casi limite: elenco vuoto, errore, dati parziali
  ✅ la logica pura dei composables e degli store

  ❌ i valori interni dei ref
  ❌ quante volte un componente si è aggiornato
  ❌ i nomi delle classi CSS
  ❌ che un mock restituisca ciò che gli hai detto

Un refactoring che non cambia il comportamento non deve
rompere i test.
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
VUE 3 — Mappa dei concetti

IL PRINCIPIO
└── Reattività a GRANA FINE: cambiando un dato si aggiorna
    solo ciò che lo LEGGE. Nessun confronto dell'albero,
    nessuna memoizzazione da scrivere a mano.

REATTIVITÀ
├── ref(qualunque cosa)   → .value in JS, automatico nel template
├── reactive(oggetto)     → Proxy, niente .value
│     ⚠ si rompe con il destructuring
│     ⚠ non si può riassegnare
│     ⚠ non funziona con i primitivi
│     → LA REGOLA: usa ref
├── shallowRef            traccia solo la sostituzione di .value
│     └── triggerRef per forzare dopo una modifica profonda
├── computed()            CACHE automatica, dipendenze dedotte
│     └── deve essere PURA
├── watch(fonte, cb)      dichiari cosa osservare
│     └── su una proprietà serve un GETTER, non il valore
│     └── alRiavvio è la pulizia
├── watchEffect(cb)       le dipendenze si deducono dalla lettura
└── Il meccanismo: Proxy → track alla lettura, trigger alla scrittura

SINGLE FILE COMPONENT
├── <script setup lang="ts">  il corpo È setup()
├── <template>                compilato e ottimizzato staticamente
├── <style scoped>            CSS locale, con :deep() e :slotted()
└── v-bind() nel CSS          lega un reattivo a una custom property

TEMPLATE
├── {{ }} · :attributo · @evento · v-model
├── Modificatori: .prevent .stop .self .once .enter .trim .number
├── v-if (rimuove) / v-show (display:none)
│     ⚠ v-show toglie anche dall'albero di accessibilità
├── v-for con :key SEMPRE, legata al dato
│     ⚠ mai v-if e v-for sullo stesso elemento
└── :class con oggetto o array, si fonde con class statica

COMPONENTE
├── defineProps<{...}>()   tipizzate; il destructuring è
│                          reattivo da Vue 3.5
├── defineEmits<{...}>()   eventi con firma
├── defineModel()          v-model bidirezionale, senza la coppia
│                          prop + evento
├── defineExpose()         il componente è CHIUSO di default
└── useTemplateRef()       il riferimento a un nodo (Vue 3.5)

COMPOSIZIONE
├── slot                   predefinito, nominali, con contenuto
│                          di riserva; $slots per il v-if
├── slot con SCOPE         il figlio passa dati al genitore
│                          → componenti headless
├── provide / inject       con InjectionKey tipizzata
│     └── nessuna cascata: il consumatore legge un ref
└── composables use*       lo stato DENTRO = locale
                           lo stato FUORI  = condiviso

CICLO DI VITA
└── onMounted · onUpdated · onUnmounted · onErrorCaptured
    nextTick() attende l'aggiornamento del DOM

ECOSISTEMA
├── Pinia          store con getter e azioni; storeToRefs per
│                  destrutturare senza perdere la reattività
├── Vue Router     rotte pigre, guardie, props dai parametri
├── Teleport       esce dai contesti di impilamento
├── Transition     classi automatiche di entrata e uscita
└── KeepAlive      conserva lo stato; :max è obbligatorio

PERFORMANCE
├── Il compilatore fa già: hoisting statico, patch flag, block tree
├── A carico tuo: shallowRef, computed, v-once, v-memo,
│     virtualizzazione
└── Vapor Mode: compilazione senza virtual DOM (in sviluppo)

DIFFERENZE CON REACT
├── Vue non ridisegna i figli quando il genitore cambia
│     → memo, useCallback e useMemo quasi mai necessari
├── Le dipendenze sono TRACCIATE, non dichiarate
│     → nessun array di dipendenze da tenere corretto
├── La mutazione è ammessa (push, splice, sort)
└── Il costo: ref contro reactive, .value, più concetti
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Sai spiegare la differenza fra il modello di React e quello di Vue
- [ ] Sai perché `.value` serve in JavaScript e non nel template
- [ ] Sai elencare i tre limiti di `reactive` e perché si preferisce `ref`
- [ ] Conosci le direttive principali e i modificatori più usati
- [ ] Sai quando usare `v-if` e quando `v-show`
- [ ] Sai perché `v-if` e `v-for` non vanno sullo stesso elemento
- [ ] Sai perché una `computed` batte un metodo nel template
- [ ] Tipizzi props ed emit con la sintassi generica
- [ ] Usi `defineModel` per il `v-model` sui componenti
- [ ] Sai che un componente con `<script setup>` è chiuso di default

**Parte B — Comprensione**

- [ ] Sai spiegare track e trigger, e cosa fa il Proxy
- [ ] Sai perché una dipendenza in un ramo non letto non viene tracciata
- [ ] Sai quando serve un getter in `watch`
- [ ] Distingui `watch`, `watchEffect` e `computed`
- [ ] Sai a cosa serve `alRiavvio` e perché è la pulizia
- [ ] Sai perché un `watch` creato dopo un `await` non si ferma da solo
- [ ] Usi gli slot con scope per costruire componenti headless
- [ ] Sai perché `provide`/`inject` non produce rendering a cascata
- [ ] Sai cosa distingue un composable con stato locale da uno globale
- [ ] Usi `storeToRefs` e sai perché il destructuring diretto non basta
- [ ] Sai proteggere una rotta con `beforeEach`
- [ ] Sai a cosa serve `Teleport` e quale problema CSS risolve
- [ ] Sai perché `:max` su `<KeepAlive>` non è opzionale

**Parte C — Pratica**

- [ ] Hai diagnosticato i cinque casi di reattività perduta
- [ ] Hai scritto un composable con annullamento e pulizia
- [ ] Hai implementato l'aggiornamento ottimistico con rollback corretto
- [ ] Hai costruito un componente headless con slot con scope
- [ ] Hai confrontato la stessa funzionalità in React e in Vue

**Parte D — Esperto**

- [ ] Sai usare `effectScope` per fermare più effetti insieme
- [ ] Sai scrivere un `customRef`
- [ ] Usi `toValue` per accettare valore, ref o getter
- [ ] Sai cosa il compilatore ottimizza da solo
- [ ] Sai quando `v-memo` è giustificato
- [ ] Sai cos'è Vapor Mode e in che direzione va
- [ ] Usi `useId` e sai perché conta con il rendering sul server
- [ ] Sai perché `v-show` toglie dall'albero di accessibilità
- [ ] Testi un composable con `effectScope`, senza montare componenti
- [ ] Testi uno store Pinia isolando l'istanza in `beforeEach`

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Destructuring di un `reactive` | Il valore si stacca dal Proxy: nessuna reattività | `ref`, o `toRefs` |
| `reactive` per un valore che va riassegnato | Il collegamento si perde all'assegnazione | `ref` |
| `watch(stato.campo, …)` | Osserva un valore, non una fonte: non scatta mai | `watch(() => stato.campo, …)` |
| Modificare una prop | Cambia lo stato del genitore senza che lo sappia | `computed` su una copia |
| `v-if` e `v-for` sullo stesso elemento | `v-if` ha priorità e non vede la variabile del ciclo | Filtrare in una `computed` |
| `v-for` senza `:key` | Vue riusa i nodi per posizione: stato sull'elemento sbagliato | `:key` legata al dato |
| Metodo nel template invece di `computed` | Rieseguito a ogni rendering, senza cache | `computed` |
| Effetti collaterali in una `computed` | Deve essere pura: gli effetti vanno altrove | `watch` o `watchEffect` |
| `watch` creato dopo un `await` | Non è legato al componente: memory leak | Crearlo sincronamente, o fermarlo a mano |
| `deep: true` su oggetti grandi | Percorre l'intero albero a ogni verifica | Osservare le proprietà specifiche |
| `shallowRef` modificato in profondità | Traccia solo la sostituzione di `.value` | Sostituire, o `triggerRef` |
| Destructuring diretto di uno store | Perde la reattività di stato e getter | `storeToRefs` |
| `<KeepAlive>` senza `:max` | Ogni pagina visitata resta in memoria per sempre | `:max="5"` |
| `v-show` su ciò che deve restare annunciabile | `display:none` toglie dall'albero di accessibilità | `.solo-screen-reader`, o `inert` |
| `Math.random()` per gli id | Rompe l'idratazione con il rendering sul server | `useId()` |
| `:deep()` usato ovunque | Rompe l'incapsulamento di `<style scoped>` | Esporre custom property, o props |
| `v-html` con dati dell'utente | Cross-site scripting | Interpolazione `{{ }}`, o sanitizzazione |
| Test sui valori interni dei ref | Si rompono a ogni refactoring | Testare il comportamento osservabile |

---

## Troubleshooting rapido

**Il valore cambia ma il template non si aggiorna**
- Causa: la reattività si è persa — destructuring di un `reactive`, un valore estratto, o `shallowRef` modificato in profondità
- Fix: verificare in Vue DevTools se il valore è un ref o un numero qualunque

**`watch` non scatta mai**
- Causa: si sta passando un valore invece di una fonte reattiva
- Fix: un getter `() => stato.campo`, oppure un `ref`

**"Cannot read properties of null" su un ref del template**
- Causa: si accede al nodo prima del montaggio
- Fix: dentro `onMounted`, o dopo `await nextTick()`

**Il DOM non è aggiornato subito dopo aver cambiato un ref**
- Causa: Vue accoda gli aggiornamenti e li applica in blocco
- Fix: `await nextTick()`

**"Extraneous non-props attributes were passed"**
- Causa: il componente ha più nodi radice, e Vue non sa a quale applicare gli attributi ereditati
- Fix: un solo nodo radice, oppure `v-bind="$attrs"` esplicito su quello giusto

**Le props arrivano come stringa invece che come numero**
- Causa: `numero="5"` passa la stringa
- Fix: `:numero="5"` con i due punti

**`emit` non arriva al genitore**
- Causa: il nome nel template è in kebab-case, quello in `emit()` in camelCase — o viceversa
- Fix: `emit('clic-lungo')` si ascolta con `@clic-lungo`

**Lo store Pinia perde la reattività dopo il destructuring**
- Causa: lo store è un `reactive`
- Fix: `storeToRefs(store)` per stato e getter; le azioni si destrutturano normalmente

**`<style scoped>` non stila un componente figlio**
- Causa: è voluto — lo scope si ferma al confine del componente
- Fix: `:deep(.selettore)`, o esporre una custom property

**La transizione non parte**
- Causa: `<Transition>` accetta un solo figlio, e serve una chiave o un `v-if`/`v-show` che cambi
- Fix: verificare che ci sia un solo elemento e che la condizione cambi

**`vue-tsc` segnala errori che l'editor non mostra**
- Causa: l'estensione Vue - Official usa una versione diversa di TypeScript
- Fix: `"vue.server.hybridMode": true` e allineare la versione del workspace

**L'idratazione fallisce con il rendering sul server**
- Causa: `Math.random()`, `Date.now()`, o l'accesso a `window` durante il setup
- Fix: `useId()` per gli identificativi; ciò che dipende dal client in `onMounted`

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_09_svelte.md` | Il terzo approccio: un compilatore che elimina il runtime |
| `tutorial_11_api_design.md` | Le API che gli store consumano |
| `tutorial_15_testing_web.md` | Testing Library, MSW e Playwright in profondità |
| `tutorial_17_performance_web.md` | Core Web Vitals e il costo reale del JavaScript |
| `tutorial_18_pwa_tecnologie_avanzate.md` | Vue in un'applicazione installabile |

---

## Risorse di riferimento

**Documentazione:**
- [vuejs.org](https://vuejs.org/guide/introduction.html) — la guida ufficiale, ottima e con esempi interattivi
- [Vue — Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth.html) — il meccanismo spiegato dagli autori
- [Pinia](https://pinia.vuejs.org/)
- [Vue Router](https://router.vuejs.org/)
- [VueUse](https://vueuse.org/) — oltre duecento composables pronti

**Approfondimenti:**
- [Vue — Composition API FAQ](https://vuejs.org/guide/extras/composition-api-faq.html) — perché esiste, e quando usare l'Options API
- [Vue — Rendering Mechanism](https://vuejs.org/guide/extras/rendering-mechanism.html) — patch flag e block tree
- [Evan You — Vue 3 One Piece](https://www.youtube.com/results?search_query=evan+you+vue+3) — i talk dell'autore sulle scelte di progetto

**Strumenti:**
- [Vue DevTools](https://devtools.vuejs.org/) — componenti, timeline, Pinia
- [vue-tsc](https://www.npmjs.com/package/vue-tsc) — verifica dei tipi anche nei template
- [eslint-plugin-vue](https://eslint.vuejs.org/)
- [eslint-plugin-vuejs-accessibility](https://vue-a11y.github.io/eslint-plugin-vuejs-accessibility/)
- [Vue Playground](https://play.vuejs.org/) — per provare senza un progetto

---

> **Fine del Tutorial 08 — Vue 3**
>
> Prossimo tutorial: `tutorial_09_svelte.md`

