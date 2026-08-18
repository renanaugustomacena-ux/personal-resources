# Tutorial 07 — React: Dal Principiante all'Esperto

> **Companion a:** `07-react.md`
> **Scope:** JSX e rendering dichiarativo, componenti e props, `useState` e `useReducer`, `useEffect` e le sue dipendenze, `useRef`, `useMemo` e `useCallback`, Context, hook personalizzati, form e `useActionState`, data fetching con TanStack Query, React Router, Error Boundary e Suspense, React 19 (`use`, Server Actions, `useOptimistic`), performance e il React Compiler, accessibilità, testing con React Testing Library
> **Prerequisiti:** `tutorial_04_javascript_fondamenti.md` — closure e `this`; `tutorial_05_javascript_avanzato.md` — Promise e `AbortController`; `tutorial_06_typescript.md` — generics e discriminated union
> **Durata stimata:** 32-40 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** React 19 · TypeScript 5.6+ · Vite · TanStack Query 5 · React Router 7 · Vitest e Testing Library

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Il modello mentale: descrivere invece di comandare](#a1-il-modello-mentale-descrivere-invece-di-comandare)
  - [A2. JSX](#a2-jsx)
  - [A3. Componenti e props](#a3-componenti-e-props)
  - [A4. Liste, chiavi e rendering condizionale](#a4-liste-chiavi-e-rendering-condizionale)
  - [A5. `useState`: lo stato locale](#a5-usestate-lo-stato-locale)
  - [A6. Eventi e form controllati](#a6-eventi-e-form-controllati)
  - [A7. `useEffect`: sincronizzare con l'esterno](#a7-useeffect-sincronizzare-con-lesterno)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. Come React decide cosa ridisegnare](#b1-come-react-decide-cosa-ridisegnare)
  - [B2. Lo stato: dove metterlo, e quando non serve](#b2-lo-stato-dove-metterlo-e-quando-non-serve)
  - [B3. `useEffect` in profondità, e quando non usarlo](#b3-useeffect-in-profondità-e-quando-non-usarlo)
  - [B4. `useReducer` e le macchine a stati](#b4-usereducer-e-le-macchine-a-stati)
  - [B5. `useRef`: ciò che non fa ridisegnare](#b5-useref-ciò-che-non-fa-ridisegnare)
  - [B6. Context: quando serve e quando fa danni](#b6-context-quando-serve-e-quando-fa-danni)
  - [B7. Hook personalizzati](#b7-hook-personalizzati)
  - [B8. `useMemo`, `useCallback` e il React Compiler](#b8-usememo-usecallback-e-il-react-compiler)
  - [B9. Data fetching: perché non con `useEffect`](#b9-data-fetching-perché-non-con-useeffect)
  - [B10. Error Boundary e Suspense](#b10-error-boundary-e-suspense)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: dashboard aziendale](#c2-mini-progetto-dashboard-aziendale)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. React 19: `use`, Actions e `useOptimistic`](#d1-react-19-use-actions-e-useoptimistic)
  - [D2. Rendering concorrente e transizioni](#d2-rendering-concorrente-e-transizioni)
  - [D3. Componenti accessibili](#d3-componenti-accessibili)
  - [D4. Testare i componenti](#d4-testare-i-componenti)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                              REACT
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
    ┌─────────▼──────────┐              ┌─────────▼──────────┐
    │   IL COMPONENTE    │              │   IL RENDERING     │
    │                    │              │                    │
    │  funzione          │              │  stato cambiato?   │
    │  props → JSX       │              │   → ridisegna      │
    │                    │              │     l'albero       │
    │  puro: stesse      │              │  diff col          │
    │  props → stesso    │              │   precedente       │
    │  risultato         │              │  applica solo      │
    │                    │              │   le differenze    │
    └─────────┬──────────┘              └─────────┬──────────┘
              └─────────────────┬─────────────────┘
                                │
    ┌───────────────────────────┼───────────────────────────┐
    │                           │                           │
┌───▼────────────┐   ┌──────────▼─────────┐   ┌─────────────▼──────┐
│    LO STATO    │   │    GLI EFFETTI     │   │   I RIFERIMENTI    │
│                │   │                    │   │                    │
│ useState       │   │ useEffect          │   │ useRef             │
│  └ locale      │   │  └ SINCRONIZZA con │   │  └ NON fa          │
│ useReducer     │   │    l'esterno       │   │    ridisegnare     │
│  └ transizioni │   │  └ non "fai dopo   │   │  └ nodo del DOM    │
│    esplicite   │   │     il rendering"  │   │  └ valore che      │
│ Context        │   │  └ pulizia SEMPRE  │   │     sopravvive     │
│  └ evitare il  │   │  └ dipendenze:     │   │                    │
│    prop drill  │   │     tutte, davvero │   │                    │
│  ⚠ non è uno   │   │  ⚠ NON per:        │   │                    │
│    state       │   │    derivare dati   │   │                    │
│    manager     │   │    reagire a eventi│   │                    │
│                │   │    fetch (usa Query│   │                    │
└────────────────┘   └────────────────────┘   └────────────────────┘
                                │
    ┌───────────────────────────┼───────────────────────────┐
    │                           │                           │
┌───▼────────────┐   ┌──────────▼─────────┐   ┌─────────────▼──────┐
│  PERFORMANCE   │   │     REACT 19       │   │   AFFIDABILITÀ     │
│                │   │                    │   │                    │
│ chiavi stabili │   │ use()              │   │ Error Boundary     │
│ stato in basso │   │ Actions            │   │  └ classe, o       │
│ useMemo        │   │ useActionState     │   │    react-error-    │
│ useCallback    │   │ useOptimistic      │   │    boundary        │
│ memo           │   │ useFormStatus      │   │ Suspense           │
│                │   │ ref come prop      │   │  └ fallback        │
│ React Compiler │   │ Server Components  │   │    dichiarativo    │
│  └ li rende    │   │  (tutorial 21)     │   │ StrictMode         │
│    superflui   │   │                    │   │  └ doppio effetto  │
└────────────────┘   └────────────────────┘   └────────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Il modello mentale: descrivere invece di comandare

> **Analogia:** la differenza fra dare indicazioni stradali e dare un indirizzo. Con le indicazioni — "gira a destra, poi a sinistra, poi avanti trecento metri" — sei tu a gestire ogni passo, e se il traffico cambia devi ricalcolare tutto. Con l'indirizzo dici *dove* si deve arrivare e il navigatore trova la strada. React è il navigatore: tu descrivi come deve apparire l'interfaccia per un certo stato, e lui calcola le modifiche da fare al DOM.

```javascript
// IMPERATIVO — dici COME cambiare il DOM, passo per passo
const elenco = document.querySelector('#elenco')
const contatore = document.querySelector('#contatore')

function aggiungiAttivita(testo) {
  const voce = document.createElement('li')
  voce.textContent = testo
  elenco.append(voce)
  contatore.textContent = `${elenco.children.length} attività`
  // E ricordarsi di aggiornare tutto il resto che dipende dall'elenco...
}
```

```tsx
// DICHIARATIVO — descrivi COM'È l'interfaccia per uno stato dato
function Elenco() {
  const [attivita, impostaAttivita] = useState<string[]>([])

  return (
    <>
      <ul>
        {attivita.map((testo, indice) => (
          <li key={indice}>{testo}</li>
        ))}
      </ul>
      <p>{attivita.length} attività</p>
    </>
  )
}
```

Non c'è codice che aggiorna il contatore: il contatore **è** `attivita.length`. Cambiando lo stato, tutto ciò che ne dipende si ricalcola. È questo il guadagno, e il costo è dover pensare in termini di stato invece che di operazioni.

### La formula che riassume React

```
  interfaccia = f(stato)

  Il componente è la funzione f.
  Cambia lo stato → React richiama f → confronta il risultato
  con il precedente → applica al DOM solo le differenze.
```

### Il primo progetto

```powershell
pnpm create vite dashboard --template react-ts
cd dashboard
pnpm install
pnpm dev
```

```tsx
// src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

const radice = document.querySelector('#root')
if (!radice) throw new Error('Elemento #root non trovato')

createRoot(radice).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

`StrictMode` non è decorativo: in sviluppo monta ogni componente **due volte** e richiama gli effetti due volte, per far emergere gli effetti senza pulizia. Non è un bug — è il modo in cui React ti dice che un effetto non è idempotente. Ne parliamo in [A7](#a7-useeffect-sincronizzare-con-lesterno).

---

## A2. JSX

JSX è una sintassi che si trasforma in chiamate di funzione. Non è HTML, e le differenze contano.

```tsx
// Quello che scrivi
const elemento = <h1 className="titolo">Ciao</h1>

// Quello che il transpiler produce (con la trasformazione moderna)
import { jsx } from 'react/jsx-runtime'
const elemento2 = jsx('h1', { className: 'titolo', children: 'Ciao' })
```

### Le differenze rispetto all'HTML

```tsx
// class → className  (class è una parola riservata in JavaScript)
<div className="scheda" />

// for → htmlFor
<label htmlFor="nome">Nome</label>

// Gli attributi sono in camelCase
<input onChange={gestisci} tabIndex={0} readOnly autoFocus maxLength={100} />

// Gli stili sono un OGGETTO, non una stringa, e in camelCase
<div style={{ backgroundColor: 'white', fontSize: '1rem', marginInline: 'auto' }} />

// Ogni tag va chiuso, anche quelli void
<img src="/logo.svg" alt="Acme" />
<br />

// I data-* e aria-* restano con il trattino
<div data-stato="attivo" aria-live="polite" aria-labelledby="titolo" />
```

### Le espressioni

```tsx
function Riepilogo({ utente, fatture }: { utente: Utente; fatture: Fattura[] }) {
  const totale = fatture.reduce((s, f) => s + f.importo, 0)

  return (
    <section>
      {/* Le graffe contengono un'ESPRESSIONE, non un'istruzione */}
      <h2>{utente.nome}</h2>
      <p>{fatture.length} fatture per {totale} euro</p>

      {/* Un ternario per il condizionale */}
      <p>{totale > 10_000 ? 'Cliente principale' : 'Cliente standard'}</p>

      {/* && per mostrare solo se vero */}
      {fatture.length === 0 && <p>Nessuna fattura emessa.</p>}
    </section>
  )
}
```

```tsx
// ❌ LA TRAPPOLA di &&: se il valore a sinistra è 0, React lo STAMPA.
//    0 è falsy, quindi && restituisce 0 — e React disegna gli zeri.
{fatture.length && <ElencoFatture fatture={fatture} />}
//  con zero fatture, a schermo compare: 0

// ✅ Convertire esplicitamente in booleano
{fatture.length > 0 && <ElencoFatture fatture={fatture} />}

// ✅ Oppure il ternario con null
{fatture.length > 0 ? <ElencoFatture fatture={fatture} /> : null}
```

### Cosa React disegna e cosa ignora

```tsx
<div>
  {null}       {/* niente */}
  {undefined}  {/* niente */}
  {false}      {/* niente */}
  {true}       {/* niente */}
  {0}          {/* ZERO: viene disegnato */}
  {''}         {/* stringa vuota: niente di visibile */}
  {[1, 2, 3]}  {/* '123' */}
</div>
```

### Un solo elemento radice

```tsx
// ❌ Due elementi adiacenti non sono un'espressione
// function Sbagliato() {
//   return <h1>Titolo</h1><p>Testo</p>
// }

// ✅ Un contenitore
function ConDiv() {
  return (
    <div>
      <h1>Titolo</h1>
      <p>Testo</p>
    </div>
  )
}

// ✅ Un Fragment, quando il div non serve nel DOM
function ConFragment() {
  return (
    <>
      <h1>Titolo</h1>
      <p>Testo</p>
    </>
  )
}

// La forma estesa, necessaria quando serve una key
import { Fragment } from 'react'

function ConChiave({ righe }: { righe: Riga[] }) {
  return (
    <dl>
      {righe.map((riga) => (
        <Fragment key={riga.id}>
          <dt>{riga.etichetta}</dt>
          <dd>{riga.valore}</dd>
        </Fragment>
      ))}
    </dl>
  )
}
```

Il Fragment conta più di quanto sembri: dentro una griglia CSS o una tabella, un `<div>` in più rompe il layout.

---

## A3. Componenti e props

Un componente è una funzione che riceve props e restituisce JSX. Il nome **deve** iniziare con la maiuscola: è così che JSX distingue un componente da un tag HTML.

```tsx
type SchedaProps = {
  titolo: string
  valore: number
  variazione?: number
  formato?: 'numero' | 'valuta' | 'percentuale'
}

function Scheda({ titolo, valore, variazione, formato = 'numero' }: SchedaProps) {
  const formattato = formatta(valore, formato)

  return (
    <article className="scheda">
      <p className="scheda__etichetta">{titolo}</p>
      <p className="scheda__valore">{formattato}</p>
      {variazione !== undefined && (
        <p className={variazione >= 0 ? 'positiva' : 'negativa'}>
          {variazione >= 0 ? '▲' : '▼'} {Math.abs(variazione)}%
        </p>
      )}
    </article>
  )
}
```

```tsx
// L'uso
<Scheda titolo="Ricavi" valore={133_000} variazione={12.4} formato="valuta" />
<Scheda titolo="Fatture" valore={248} />
```

### `children`

```tsx
import type { ReactNode } from 'react'

type PannelloProps = {
  titolo: string
  children: ReactNode
  azioni?: ReactNode
}

function Pannello({ titolo, children, azioni }: PannelloProps) {
  return (
    <section className="pannello">
      <header className="pannello__intestazione">
        <h2>{titolo}</h2>
        {azioni}
      </header>
      <div className="pannello__corpo">{children}</div>
    </section>
  )
}
```

```tsx
<Pannello titolo="Fatture recenti" azioni={<button>Esporta</button>}>
  <TabellaFatture fatture={fatture} />
</Pannello>
```

Passare JSX come prop — `azioni` qui — è la composizione, e risolve la maggior parte dei problemi per cui si sarebbe tentati di usare l'ereditarietà o una prop booleana in più.

### Le props sono in sola lettura

```tsx
// ❌ Modificare una prop: React non lo impedisce, ma rompe
//    il modello. Il componente non è più una funzione pura.
function Sbagliato({ elenco }: { elenco: string[] }) {
  elenco.push('nuovo') // muta l'array del genitore
  return <ul>{elenco.map((v, i) => <li key={i}>{v}</li>)}</ul>
}

// ✅ Derivare senza modificare
function Corretto({ elenco }: { elenco: readonly string[] }) {
  const ordinato = [...elenco].sort()
  return (
    <ul>
      {ordinato.map((v) => (
        <li key={v}>{v}</li>
      ))}
    </ul>
  )
}
```

`readonly string[]` nella firma rende l'errore un problema di compilazione invece di un bug sottile.

### Tipizzare le props con gli attributi nativi

```tsx
import type { ComponentPropsWithoutRef, ReactNode } from 'react'

type PulsanteProps = {
  variante?: 'primario' | 'secondario' | 'pericolo'
  dimensione?: 'piccolo' | 'medio' | 'grande'
  icona?: ReactNode
} & ComponentPropsWithoutRef<'button'>

function Pulsante({
  variante = 'primario',
  dimensione = 'medio',
  icona,
  children,
  className = '',
  ...resto
}: PulsanteProps) {
  return (
    <button
      className={`pulsante pulsante--${variante} pulsante--${dimensione} ${className}`}
      {...resto}
    >
      {icona}
      {children}
    </button>
  )
}
```

```tsx
// Da qui, tutti gli attributi di <button> sono disponibili E tipizzati
<Pulsante variante="pericolo" onClick={elimina} disabled={inCorso} type="submit"
          aria-describedby="avviso">
  Elimina
</Pulsante>
```

`ComponentPropsWithoutRef<'button'>` dà `onClick`, `disabled`, `type`, `aria-*` e tutto il resto, con i tipi corretti. È il pattern standard per i componenti di base di un design system.

---

## A4. Liste, chiavi e rendering condizionale

```tsx
function ElencoFatture({ fatture }: { fatture: readonly Fattura[] }) {
  return (
    <ul>
      {fatture.map((fattura) => (
        <li key={fattura.id}>
          {fattura.numero} — {fattura.cliente}
        </li>
      ))}
    </ul>
  )
}
```

### Le chiavi: perché l'indice è quasi sempre sbagliato

La `key` dice a React **quale elemento è quale** fra un rendering e il successivo. Senza un'identità stabile, React abbina gli elementi per posizione, e lo stato interno finisce sull'elemento sbagliato.

```
Stato iniziale, con key={indice}:

  indice 0 → "Comprare il latte"      [ ] casella non spuntata
  indice 1 → "Chiamare il fornitore"  [x] casella spuntata
  indice 2 → "Inviare la fattura"     [ ]

Elimino il primo elemento. Ora:

  indice 0 → "Chiamare il fornitore"  [ ]  ← ha perso la spunta!
  indice 1 → "Inviare la fattura"     [x]  ← ha preso la spunta di un altro!

React ha visto: "l'elemento a indice 0 è cambiato di testo,
lo stato resta". Ma l'elemento non è cambiato: è sparito
quello prima.
```

```tsx
// ❌ L'indice come chiave, con una lista che cambia
{attivita.map((a, indice) => (
  <VoceAttivita key={indice} attivita={a} />
))}

// ✅ Un identificativo stabile, legato al DATO
{attivita.map((a) => (
  <VoceAttivita key={a.id} attivita={a} />
))}
```

```
Quando l'indice è accettabile — e sono tre condizioni INSIEME:
  1. la lista non viene mai riordinata
  2. non si aggiunge né si toglie nulla in mezzo
  3. gli elementi non hanno stato interno né sono componenti

Fuori da questi casi, serve un id. Se i dati non ne hanno uno,
generarlo alla creazione — non durante il rendering, o
cambierebbe a ogni giro.
```

### Rendering condizionale

```tsx
function Contenuto({ stato }: { stato: StatoRichiesta }) {
  // Uscita anticipata: la forma più leggibile quando i rami
  // producono alberi molto diversi
  if (stato.tipo === 'caricamento') return <Scheletro />
  if (stato.tipo === 'errore') return <Errore errore={stato.errore} />
  if (stato.dati.length === 0) return <Vuoto />

  return <Tabella righe={stato.dati} />
}
```

```tsx
// Una mappa di componenti, quando i casi sono molti
const PER_STATO = {
  inattiva: Inattiva,
  caricamento: Scheletro,
  riuscita: Tabella,
  fallita: Errore,
} as const

function ContenutoConMappa({ stato }: { stato: StatoRichiesta }) {
  const Componente = PER_STATO[stato.tipo]
  return <Componente stato={stato} />
}
```

---

## A5. `useState`: lo stato locale

```tsx
import { useState } from 'react'

function Contatore() {
  const [conteggio, impostaConteggio] = useState(0)

  return (
    <div>
      <p>{conteggio}</p>
      <button onClick={() => impostaConteggio(conteggio + 1)}>Incrementa</button>
    </div>
  )
}
```

### Lo stato non cambia subito

```tsx
// ❌ Tre chiamate, un solo incremento.
//    'conteggio' è il valore CATTURATO da questo rendering:
//    resta 0 in tutte e tre le righe.
function Sbagliato() {
  const [conteggio, impostaConteggio] = useState(0)

  function incrementaTre() {
    impostaConteggio(conteggio + 1) // 0 + 1
    impostaConteggio(conteggio + 1) // 0 + 1
    impostaConteggio(conteggio + 1) // 0 + 1
  }

  return <button onClick={incrementaTre}>+3</button>
}

// ✅ La forma funzionale riceve il valore PIÙ RECENTE
function Corretto() {
  const [conteggio, impostaConteggio] = useState(0)

  function incrementaTre() {
    impostaConteggio((precedente) => precedente + 1)
    impostaConteggio((precedente) => precedente + 1)
    impostaConteggio((precedente) => precedente + 1)
  }

  return <button onClick={incrementaTre}>+3</button>
}
```

**La regola:** quando il nuovo valore dipende dal precedente, usa la forma funzionale. Sempre — non solo quando le chiamate sono più d'una: dentro un `setTimeout` o un callback asincrono il valore catturato è vecchio allo stesso modo.

### Aggiornare oggetti e array senza modificarli

```tsx
function Modulo() {
  const [modulo, impostaModulo] = useState({ nome: '', email: '', note: '' })

  function aggiornaCampo(campo: keyof typeof modulo, valore: string) {
    // Un oggetto NUOVO: React confronta per identità.
    // Modificando quello esistente, il confronto darebbe uguale
    // e il componente non si ridisegnerebbe.
    impostaModulo((precedente) => ({ ...precedente, [campo]: valore }))
  }

  return (
    <input
      value={modulo.nome}
      onChange={(evento) => aggiornaCampo('nome', evento.target.value)}
    />
  )
}
```

```tsx
// Gli array, con i metodi che non modificano
impostaElenco((p) => [...p, nuovo]) // aggiungere
impostaElenco((p) => p.filter((x) => x.id !== id)) // rimuovere
impostaElenco((p) => p.map((x) => (x.id === id ? { ...x, fatto: true } : x))) // modificare
impostaElenco((p) => p.toSorted((a, b) => a.n - b.n)) // ordinare
impostaElenco((p) => p.toSpliced(indice, 0, nuovo)) // inserire in mezzo
```

### L'inizializzatore pigro

```tsx
// ❌ leggiDaArchivio() viene chiamata a OGNI rendering,
//    anche se il valore serve solo la prima volta
const [stato, impostaStato] = useState(leggiDaArchivio())

// ✅ Passando una funzione, React la chiama solo al primo rendering
const [stato2, impostaStato2] = useState(() => leggiDaArchivio())
```

La differenza si nota quando l'inizializzazione è costosa: un `JSON.parse` di un archivio grande, o un calcolo. Con un valore letterale (`useState(0)`) non serve.

### Tipizzare lo stato

```tsx
// Dedotto dal valore iniziale
const [conteggio, impostaConteggio] = useState(0) // number
const [testo, impostaTesto] = useState('') // string

// Esplicito quando l'iniziale è null o vuoto
const [utente, impostaUtente] = useState<Utente | null>(null)
const [righe, impostaRighe] = useState<Fattura[]>([])

// ❌ Senza il generico, il tipo è never[] e non si può aggiungere nulla
// const [vuoto, impostaVuoto] = useState([])
```

---

## A6. Eventi e form controllati

```tsx
function Modulo() {
  const [email, impostaEmail] = useState('')

  // Il tipo dell'evento è dedotto dal contesto
  function gestisciInvio(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    console.log(email)
  }

  return (
    <form onSubmit={gestisciInvio}>
      <label htmlFor="email">Email</label>
      <input
        type="email"
        id="email"
        value={email}
        onChange={(evento) => impostaEmail(evento.target.value)}
        required
      />
      <button type="submit">Invia</button>
    </form>
  )
}
```

### Controllato o non controllato

```tsx
// CONTROLLATO — React possiede il valore.
// Serve quando devi reagire a ogni carattere: validazione
// mentre si scrive, filtri, contatori, campi collegati fra loro.
function Controllato() {
  const [valore, impostaValore] = useState('')
  return <input value={valore} onChange={(e) => impostaValore(e.target.value)} />
}

// NON CONTROLLATO — il DOM possiede il valore.
// Meno rendering, e con React 19 il form si legge al submit.
function NonControllato() {
  function gestisci(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const dati = new FormData(evento.currentTarget)
    console.log(dati.get('email'))
  }

  return (
    <form onSubmit={gestisci}>
      <input name="email" defaultValue="" />
      <button type="submit">Invia</button>
    </form>
  )
}
```

```
Il criterio:

  Controllato quando lo stato del campo serve ALTROVE
  mentre si digita: un filtro che aggiorna una lista,
  una validazione immediata, due campi che si condizionano.

  Non controllato per i form normali che si leggono
  all'invio. È meno codice, meno rendering, e con
  <form action={...}> di React 19 è la forma naturale.
```

```tsx
// ❌ La trappola: value senza onChange rende il campo non modificabile
// <input value={valore} />
//   Warning: You provided a 'value' prop to a form field without
//   an 'onChange' handler.

// ✅ Sola lettura voluta
<input value={valore} readOnly />

// ✅ Non controllato con valore iniziale
<input defaultValue={valore} />
```

```tsx
// ❌ undefined come valore iniziale: il campo passa da
//    non controllato a controllato, e React avvisa
const [nome, impostaNome] = useState<string | undefined>(undefined)
// <input value={nome} onChange={...} />

// ✅ Stringa vuota
const [nome2, impostaNome2] = useState('')
```

### I tipi degli eventi

```tsx
import type { ChangeEvent, FormEvent, MouseEvent, KeyboardEvent } from 'react'

function gestisciCambio(evento: ChangeEvent<HTMLInputElement>) {
  console.log(evento.target.value)
}

function gestisciSelezione(evento: ChangeEvent<HTMLSelectElement>) {
  console.log(evento.target.value)
}

function gestisciInvio(evento: FormEvent<HTMLFormElement>) {
  evento.preventDefault()
}

function gestisciClic(evento: MouseEvent<HTMLButtonElement>) {
  console.log(evento.currentTarget.dataset['id'])
}

function gestisciTasto(evento: KeyboardEvent<HTMLInputElement>) {
  if (evento.key === 'Escape') evento.currentTarget.blur()
}
```

Scrivendo il gestore **inline** i tipi sono dedotti e non serve annotarli: `onChange={(e) => ...}` sa già che `e` è un `ChangeEvent<HTMLInputElement>`.

---

## A7. `useEffect`: sincronizzare con l'esterno

> **Analogia:** `useEffect` non è "esegui questo dopo il rendering". È un contratto di manutenzione: dici a React *questa cosa esterna deve restare allineata a questo stato*, e React si occupa di attivarla, riattivarla quando lo stato cambia, e disattivarla quando non serve più. La funzione di pulizia non è un'aggiunta: è metà del contratto.

```tsx
import { useEffect, useState } from 'react'

function Orologio() {
  const [ora, impostaOra] = useState(() => new Date())

  useEffect(() => {
    const intervallo = setInterval(() => impostaOra(new Date()), 1000)

    // La pulizia: eseguita allo smontaggio E prima di ogni
    // riesecuzione dell'effetto
    return () => clearInterval(intervallo)
  }, []) // array vuoto: solo al montaggio

  return <time>{ora.toLocaleTimeString('it-IT')}</time>
}
```

### L'array delle dipendenze

```tsx
// Nessun array: dopo OGNI rendering
useEffect(() => {
  console.log('sempre')
})

// Array vuoto: solo al montaggio, pulizia allo smontaggio
useEffect(() => {
  console.log('una volta')
}, [])

// Con dipendenze: quando almeno una cambia (confronto con Object.is)
useEffect(() => {
  console.log('quando cambia idUtente')
}, [idUtente])
```

```tsx
// ❌ Dipendenza omessa: l'effetto usa un valore vecchio.
//    È il bug più comune con useEffect.
function Sbagliato({ idUtente }: { idUtente: string }) {
  const [utente, impostaUtente] = useState<Utente | null>(null)

  useEffect(() => {
    recuperaUtente(idUtente).then(impostaUtente)
  }, []) // ← manca idUtente: cambiandolo, il dato non si aggiorna

  return <div>{utente?.nome}</div>
}

// ✅ Tutte le dipendenze dichiarate
function Corretto({ idUtente }: { idUtente: string }) {
  const [utente, impostaUtente] = useState<Utente | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    recuperaUtente(idUtente, { signal: controller.signal })
      .then(impostaUtente)
      .catch((errore) => {
        if (errore.name !== 'AbortError') console.error(errore)
      })

    // Annulla la richiesta precedente quando idUtente cambia
    return () => controller.abort()
  }, [idUtente])

  return <div>{utente?.nome}</div>
}
```

L'ESLint plugin `react-hooks` con la regola `exhaustive-deps` segnala le dipendenze mancanti. **Non disattivarla**: quando avvisa, ha ragione, e la soluzione è quasi sempre ristrutturare il codice, non silenziarla.

### La pulizia, e perché `StrictMode` monta due volte

```tsx
// In sviluppo, StrictMode esegue: effetto → pulizia → effetto.
// Se il componente si rompe o duplica qualcosa, l'effetto
// non è idempotente e in produzione avrebbe comunque un bug
// (basta un rimontaggio, che con il routing accade di continuo).

// ❌ Senza pulizia: due sottoscrizioni, due listener, due timer
useEffect(() => {
  const socket = new WebSocket(url)
  socket.addEventListener('message', gestisci)
}, [url])

// ✅ Con pulizia: la seconda esecuzione parte da pulito
useEffect(() => {
  const socket = new WebSocket(url)
  socket.addEventListener('message', gestisci)

  return () => socket.close()
}, [url])
```

```
Cosa richiede SEMPRE una pulizia:

  timer            clearTimeout · clearInterval
  listener         removeEventListener, o AbortController
  sottoscrizioni   WebSocket, EventSource, store esterni
  osservatori      IntersectionObserver, ResizeObserver, MutationObserver
  richieste        AbortController
  animazioni       cancelAnimationFrame
```

### Il ciclo di vita, in ordine

```
  1. React chiama il componente     → calcola il JSX
  2. React aggiorna il DOM
  3. Il browser DIPINGE
  4. React esegue useEffect

  useLayoutEffect si inserisce fra il 2 e il 3:
  blocca il dipinto. Serve solo per le misure del DOM
  che devono avvenire prima che l'utente veda qualcosa —
  altrimenti si vede uno sfarfallio.
```

---

# Parte B — Comprensione Profonda

---

## B1. Come React decide cosa ridisegnare

```
Quando lo stato di un componente cambia:

  1. React richiama QUEL componente
  2. E TUTTI i suoi discendenti, per intero
  3. Confronta l'albero prodotto con il precedente
  4. Applica al DOM solo le differenze

Il punto 2 sorprende: React NON verifica se le props
di un figlio sono cambiate prima di richiamarlo.
Lo richiama e basta.

Non è uno spreco: richiamare una funzione è veloce.
Ciò che costa è toccare il DOM, e quello React lo
riduce al minimo con il confronto.
```

```tsx
function Genitore() {
  const [conteggio, impostaConteggio] = useState(0)

  return (
    <div>
      <button onClick={() => impostaConteggio((c) => c + 1)}>{conteggio}</button>
      {/* Figlio viene richiamato a ogni clic, anche se
          le sue props non cambiano mai */}
      <Figlio testo="costante" />
    </div>
  )
}
```

### Il pattern che elimina il problema senza `memo`

```tsx
// ❌ La soluzione istintiva: avvolgere in memo
const FiglioMemo = memo(Figlio)

// ✅ La soluzione strutturale: passare il figlio come children.
//    Il JSX di 'children' viene creato nel NONNO, e non
//    cambia identità quando cambia lo stato del genitore.
function Contenitore({ children }: { children: ReactNode }) {
  const [conteggio, impostaConteggio] = useState(0)

  return (
    <div>
      <button onClick={() => impostaConteggio((c) => c + 1)}>{conteggio}</button>
      {children}
    </div>
  )
}

function App() {
  return (
    <Contenitore>
      {/* Creato qui: il rendering di Contenitore non lo tocca */}
      <Figlio testo="costante" />
    </Contenitore>
  )
}
```

### Cosa fa cambiare identità a una prop

```tsx
// A ogni rendering, questi sono OGGETTI NUOVI:
<Componente
  stile={{ colore: 'rosso' }}       // nuovo oggetto
  elenco={[1, 2, 3]}                 // nuovo array
  alClic={() => salva()}             // nuova funzione
  opzioni={{ ...predefinite }}       // nuovo oggetto
/>

// Con memo, questi annullerebbero la memoizzazione:
// il confronto superficiale li vede sempre diversi.
```

```tsx
// Le soluzioni, in ordine di preferenza:

// 1. Spostare fuori dal componente ciò che è costante:
//    l'identità non cambia mai
const STILE_FISSO = { colore: 'rosso' } as const
const OPZIONI_PREDEFINITE = { timeout: 5000 } as const

function ConCostanti() {
  return <Componente stile={STILE_FISSO} opzioni={OPZIONI_PREDEFINITE} />
}

// 2. Passare i valori PRIMITIVI invece degli oggetti:
//    i primitivi si confrontano per valore
function ConPrimitivi() {
  return <Componente colore="rosso" timeout={5000} />
}

// 3. useMemo / useCallback — solo se le prime due non bastano
```

### `key` per forzare la ricreazione

```tsx
// Cambiando la key, React DISTRUGGE il componente e ne crea
// uno nuovo: tutto lo stato interno si azzera.
// È il modo dichiarativo di dire "ricomincia da capo".
function ModuloUtente({ idUtente }: { idUtente: string }) {
  return <ModuloModifica key={idUtente} idUtente={idUtente} />
}
```

Senza la `key`, passando da un utente all'altro il form conserverebbe i valori digitati per il precedente. L'alternativa — un `useEffect` che azzera i campi quando `idUtente` cambia — è più codice e ha più modi di sbagliare.

---

## B2. Lo stato: dove metterlo, e quando non serve

### Non mettere nello stato ciò che si può calcolare

```tsx
// ❌ Stato ridondante: totale e filtrate si possono DERIVARE.
//    Ogni stato in più è un'occasione di desincronizzazione.
function Sbagliato({ fatture }: { fatture: Fattura[] }) {
  const [filtro, impostaFiltro] = useState('')
  const [filtrate, impostaFiltrate] = useState(fatture)
  const [totale, impostaTotale] = useState(0)

  useEffect(() => {
    const risultato = fatture.filter((f) => f.cliente.includes(filtro))
    impostaFiltrate(risultato)
    impostaTotale(risultato.reduce((s, f) => s + f.importo, 0))
  }, [fatture, filtro])

  return <Tabella righe={filtrate} totale={totale} />
}

// ✅ Un solo stato, il resto calcolato durante il rendering
function Corretto({ fatture }: { fatture: readonly Fattura[] }) {
  const [filtro, impostaFiltro] = useState('')

  const filtrate = fatture.filter((f) => f.cliente.includes(filtro))
  const totale = filtrate.reduce((s, f) => s + f.importo, 0)

  return <Tabella righe={filtrate} totale={totale} />
}
```

Il calcolo durante il rendering non è un problema di prestazioni: filtrare un array di centinaia di elementi costa microsecondi. Diventa un problema solo su decine di migliaia, e allora c'è `useMemo`.

```
Le tre domande, in ordine:

  1. Si può calcolare dalle props o da un altro stato?
     → non è stato, è una variabile
  2. Cambia nel tempo?
     → no: è una costante fuori dal componente
  3. Il componente si ridisegna quando cambia?
     → no: è un useRef
```

### Sollevare lo stato

```tsx
// Quando due componenti devono condividere uno stato,
// va nel loro antenato comune più VICINO — non più in alto.
function Pagina() {
  const [selezionata, impostaSelezionata] = useState<string | null>(null)

  return (
    <div className="disposizione">
      <ElencoFatture selezionata={selezionata} alSelezionare={impostaSelezionata} />
      <DettaglioFattura id={selezionata} />
    </div>
  )
}
```

### E abbassarlo, quando isola i rendering

```tsx
// ❌ Lo stato del campo di ricerca è nella pagina:
//    ogni carattere digitato ridisegna la tabella intera
function PaginaSbagliata({ fatture }: { fatture: readonly Fattura[] }) {
  const [ricerca, impostaRicerca] = useState('')

  return (
    <>
      <input value={ricerca} onChange={(e) => impostaRicerca(e.target.value)} />
      <TabellaPesante fatture={fatture} />
      <GraficoPesante fatture={fatture} />
    </>
  )
}

// ✅ Lo stato scende nel componente che lo usa davvero
function CampoRicerca({ alCercare }: { alCercare: (v: string) => void }) {
  const [ricerca, impostaRicerca] = useState('')

  return (
    <input
      value={ricerca}
      onChange={(evento) => {
        impostaRicerca(evento.target.value)
        alCercare(evento.target.value)
      }}
    />
  )
}
```

### Lo stato in un componente non montato sparisce

```tsx
// ❌ Il testo digitato si perde quando il pannello si chiude
function ConDisplayNone({ aperto }: { aperto: boolean }) {
  return aperto ? <ModuloComplesso /> : null
}

// ✅ Nascosto con il CSS: il componente resta montato,
//    lo stato sopravvive. Costa il rendering, ma conserva i dati.
function ConHidden({ aperto }: { aperto: boolean }) {
  return (
    <div hidden={!aperto}>
      <ModuloComplesso />
    </div>
  )
}
```

---

## B3. `useEffect` in profondità, e quando non usarlo

La maggior parte degli `useEffect` che si trovano nel codice non dovrebbe esistere. Ecco i quattro casi.

### Caso 1 — Derivare dati

```tsx
// ❌ Un effetto per calcolare qualcosa dalle props
function Sbagliato({ primo, secondo }: { primo: string; secondo: string }) {
  const [completo, impostaCompleto] = useState('')

  useEffect(() => {
    impostaCompleto(`${primo} ${secondo}`)
  }, [primo, secondo])

  return <p>{completo}</p>
}

// ✅ Calcola e basta. Un rendering invece di due.
function Corretto({ primo, secondo }: { primo: string; secondo: string }) {
  const completo = `${primo} ${secondo}`
  return <p>{completo}</p>
}
```

### Caso 2 — Reagire a un evento dell'utente

```tsx
// ❌ Un effetto che osserva lo stato per capire che è successo qualcosa
function Sbagliato2() {
  const [inviato, impostaInviato] = useState(false)

  useEffect(() => {
    if (inviato) {
      mostraNotifica('Inviato')
      registraEvento('modulo-inviato')
    }
  }, [inviato])

  return <button onClick={() => impostaInviato(true)}>Invia</button>
}

// ✅ La logica sta nel gestore dell'evento: è lì che il fatto accade
function Corretto2() {
  function gestisciInvio() {
    invia()
    mostraNotifica('Inviato')
    registraEvento('modulo-inviato')
  }

  return <button onClick={gestisciInvio}>Invia</button>
}
```

```
Il criterio che risolve la maggior parte dei casi:

  È successo QUALCOSA (un clic, un invio)?
    → la logica va nel GESTORE DELL'EVENTO

  Il componente è VISIBILE e deve restare allineato
  a qualcosa di esterno (una connessione, un timer,
  un'API del browser)?
    → è un EFFETTO
```

### Caso 3 — Azzerare lo stato quando cambia una prop

```tsx
// ❌ Un effetto per azzerare: produce un rendering con
//    i dati vecchi, poi uno con quelli azzerati
function Sbagliato3({ idUtente }: { idUtente: string }) {
  const [bozza, impostaBozza] = useState('')

  useEffect(() => {
    impostaBozza('')
  }, [idUtente])

  return <textarea value={bozza} onChange={(e) => impostaBozza(e.target.value)} />
}

// ✅ La key: React ricrea il componente, lo stato riparte da zero
function Corretto3({ idUtente }: { idUtente: string }) {
  return <Bozza key={idUtente} />
}

function Bozza() {
  const [bozza, impostaBozza] = useState('')
  return <textarea value={bozza} onChange={(e) => impostaBozza(e.target.value)} />
}
```

### Caso 4 — Recuperare dati

È il caso più diffuso, e quello dove l'effetto scritto a mano sbaglia di più. Ne parliamo in [B9](#b9-data-fetching-perché-non-con-useeffect).

### Quando `useEffect` è la scelta giusta

```tsx
// Sincronizzare con un'API del browser
function useLarghezzaFinestra() {
  const [larghezza, impostaLarghezza] = useState(() => window.innerWidth)

  useEffect(() => {
    const controller = new AbortController()

    window.addEventListener('resize', () => impostaLarghezza(window.innerWidth), {
      signal: controller.signal,
    })

    return () => controller.abort()
  }, [])

  return larghezza
}
```

```tsx
// Sincronizzare con una connessione esterna
function useConnessione(url: string) {
  const [stato, impostaStato] = useState<'chiusa' | 'aperta'>('chiusa')

  useEffect(() => {
    const socket = new WebSocket(url)
    socket.addEventListener('open', () => impostaStato('aperta'))
    socket.addEventListener('close', () => impostaStato('chiusa'))

    return () => socket.close()
  }, [url])

  return stato
}
```

```tsx
// useSyncExternalStore: la via corretta per uno store esterno,
// perché gestisce anche il rendering concorrente
import { useSyncExternalStore } from 'react'

function useOnline() {
  return useSyncExternalStore(
    // sottoscrizione
    (alCambiamento) => {
      window.addEventListener('online', alCambiamento)
      window.addEventListener('offline', alCambiamento)
      return () => {
        window.removeEventListener('online', alCambiamento)
        window.removeEventListener('offline', alCambiamento)
      }
    },
    // valore sul client
    () => navigator.onLine,
    // valore sul server, per il rendering lato server
    () => true,
  )
}
```

### Le dipendenze che cambiano a ogni rendering

```tsx
// ❌ 'opzioni' è un oggetto nuovo a ogni rendering:
//    l'effetto si riesegue sempre, e con una fetch dentro
//    diventa un ciclo infinito
function Sbagliato4({ id }: { id: string }) {
  const opzioni = { includiArchiviate: true }

  useEffect(() => {
    recupera(id, opzioni)
  }, [id, opzioni]) // opzioni cambia sempre
}

// ✅ Opzione 1: spostare l'oggetto fuori dal componente
const OPZIONI = { includiArchiviate: true } as const

function Corretto4a({ id }: { id: string }) {
  useEffect(() => {
    recupera(id, OPZIONI)
  }, [id])
}

// ✅ Opzione 2: dipendere dai valori primitivi
function Corretto4b({ id, includiArchiviate }: { id: string; includiArchiviate: boolean }) {
  useEffect(() => {
    recupera(id, { includiArchiviate })
  }, [id, includiArchiviate])
}
```

---

## B4. `useReducer` e le macchine a stati

Quando gli stati sono più d'uno e cambiano insieme, `useReducer` rende le transizioni esplicite e testabili.

```tsx
import { useReducer } from 'react'

type Stato = {
  valori: { nome: string; email: string; messaggio: string }
  errori: Partial<Record<'nome' | 'email' | 'messaggio', string>>
  invio: 'inattivo' | 'in-corso' | 'riuscito' | 'fallito'
  messaggioErrore: string | null
}

type Azione =
  | { tipo: 'cambia-campo'; campo: keyof Stato['valori']; valore: string }
  | { tipo: 'valida'; errori: Stato['errori'] }
  | { tipo: 'invio-iniziato' }
  | { tipo: 'invio-riuscito' }
  | { tipo: 'invio-fallito'; messaggio: string }
  | { tipo: 'azzera' }

const STATO_INIZIALE: Stato = {
  valori: { nome: '', email: '', messaggio: '' },
  errori: {},
  invio: 'inattivo',
  messaggioErrore: null,
}

// Una funzione PURA: si testa senza React, senza DOM, senza mock
function riduttore(stato: Stato, azione: Azione): Stato {
  switch (azione.tipo) {
    case 'cambia-campo':
      return {
        ...stato,
        valori: { ...stato.valori, [azione.campo]: azione.valore },
        // Digitando, l'errore di quel campo sparisce
        errori: { ...stato.errori, [azione.campo]: undefined },
      }

    case 'valida':
      return { ...stato, errori: azione.errori }

    case 'invio-iniziato':
      return { ...stato, invio: 'in-corso', messaggioErrore: null }

    case 'invio-riuscito':
      return { ...STATO_INIZIALE, invio: 'riuscito' }

    case 'invio-fallito':
      return { ...stato, invio: 'fallito', messaggioErrore: azione.messaggio }

    case 'azzera':
      return STATO_INIZIALE

    default: {
      const esaustivo: never = azione
      throw new Error(`Azione non gestita: ${JSON.stringify(esaustivo)}`)
    }
  }
}

function ModuloContatti() {
  const [stato, invia] = useReducer(riduttore, STATO_INIZIALE)

  async function gestisciInvio(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault()

    const errori = valida(stato.valori)
    if (Object.keys(errori).length > 0) {
      invia({ tipo: 'valida', errori })
      return
    }

    invia({ tipo: 'invio-iniziato' })

    try {
      await inviaContatto(stato.valori)
      invia({ tipo: 'invio-riuscito' })
    } catch (errore) {
      invia({
        tipo: 'invio-fallito',
        messaggio: errore instanceof Error ? errore.message : 'Errore sconosciuto',
      })
    }
  }

  return (
    <form onSubmit={gestisciInvio}>
      <input
        value={stato.valori.nome}
        onChange={(e) => invia({ tipo: 'cambia-campo', campo: 'nome', valore: e.target.value })}
        aria-invalid={stato.errori.nome !== undefined}
        aria-describedby={stato.errori.nome ? 'errore-nome' : undefined}
      />
      {stato.errori.nome && (
        <p id="errore-nome" role="alert">
          {stato.errori.nome}
        </p>
      )}

      <button type="submit" disabled={stato.invio === 'in-corso'}>
        {stato.invio === 'in-corso' ? 'Invio…' : 'Invia'}
      </button>

      {stato.messaggioErrore && <p role="alert">{stato.messaggioErrore}</p>}
    </form>
  )
}
```

```
useState o useReducer:

  useState     uno o due valori indipendenti
               le transizioni sono ovvie

  useReducer   più valori che cambiano INSIEME
               la prossima transizione dipende dalla precedente
               la logica va testata senza React
               le azioni vanno registrate o ripetute

Il riduttore è una funzione pura: si testa chiamandola.
È il motivo principale per cui conviene, più della comodità.
```

---

## B5. `useRef`: ciò che non fa ridisegnare

`useRef` ha due usi distinti che condividono lo stesso hook.

### Uso 1 — Un riferimento a un nodo del DOM

```tsx
import { useRef, useEffect } from 'react'

function CampoConFocus() {
  const campo = useRef<HTMLInputElement>(null)

  useEffect(() => {
    campo.current?.focus()
  }, [])

  return <input ref={campo} />
}
```

```tsx
// In React 19 'ref' è una prop normale: niente forwardRef
type CampoProps = {
  ref?: React.Ref<HTMLInputElement>
  etichetta: string
} & React.ComponentPropsWithoutRef<'input'>

function Campo({ ref, etichetta, id, ...resto }: CampoProps) {
  return (
    <div>
      <label htmlFor={id}>{etichetta}</label>
      <input ref={ref} id={id} {...resto} />
    </div>
  )
}
```

```tsx
// Un ref callback che restituisce la pulizia (React 19)
function ConOsservatore() {
  const osserva = (elemento: HTMLDivElement | null) => {
    if (!elemento) return

    const osservatore = new IntersectionObserver(([voce]) => {
      if (voce?.isIntersecting) caricaAltro()
    })
    osservatore.observe(elemento)

    // La pulizia, restituita direttamente dal ref
    return () => osservatore.disconnect()
  }

  return <div ref={osserva}>Sentinella</div>
}
```

### Uso 2 — Un valore che sopravvive senza far ridisegnare

```tsx
function ConCronometro() {
  const [tempo, impostaTempo] = useState(0)
  // L'identificativo dell'intervallo non serve al rendering:
  // metterlo nello stato causerebbe un rendering inutile
  const intervallo = useRef<number | null>(null)

  function avvia() {
    if (intervallo.current !== null) return
    intervallo.current = window.setInterval(() => impostaTempo((t) => t + 1), 1000)
  }

  function ferma() {
    if (intervallo.current === null) return
    clearInterval(intervallo.current)
    intervallo.current = null
  }

  useEffect(() => ferma, [])

  return (
    <div>
      <p>{tempo}</p>
      <button onClick={avvia}>Avvia</button>
      <button onClick={ferma}>Ferma</button>
    </div>
  )
}
```

```tsx
// Il pattern del valore precedente
function usaPrecedente<T>(valore: T): T | undefined {
  const riferimento = useRef<T | undefined>(undefined)

  useEffect(() => {
    riferimento.current = valore
  }, [valore])

  // Durante il rendering, current contiene ancora il valore
  // del rendering PRECEDENTE
  return riferimento.current
}
```

```tsx
// ❌ Leggere o scrivere un ref DURANTE il rendering rende
//    il componente non puro, e rompe il rendering concorrente
function Sbagliato() {
  const contatore = useRef(0)
  contatore.current++ // ← durante il rendering
  return <p>{contatore.current}</p>
}

// ✅ I ref si toccano negli effetti e nei gestori di eventi
function Corretto() {
  const contatore = useRef(0)

  useEffect(() => {
    contatore.current++
  })

  return <p>ok</p>
}
```

---

## B6. Context: quando serve e quando fa danni

Context risolve **un** problema: passare un valore attraverso molti livelli senza inoltrarlo a mano. Non è uno state manager, e usarlo come tale produce rendering a cascata.

```tsx
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

type Tema = 'chiaro' | 'scuro'

type ContestoTema = {
  tema: Tema
  cambiaTema: (tema: Tema) => void
}

// Senza valore predefinito: l'assenza del provider deve essere un errore
const ContestoTema = createContext<ContestoTema | null>(null)

export function FornitoreTema({ children }: { children: ReactNode }) {
  const [tema, impostaTema] = useState<Tema>('chiaro')

  // Senza useMemo, il valore è un oggetto nuovo a ogni rendering
  // del fornitore, e OGNI consumatore si ridisegna
  const valore = useMemo(() => ({ tema, cambiaTema: impostaTema }), [tema])

  return <ContestoTema.Provider value={valore}>{children}</ContestoTema.Provider>
}

// L'hook che nasconde il context e verifica il fornitore
export function useTema(): ContestoTema {
  const contesto = useContext(ContestoTema)

  if (contesto === null) {
    throw new Error('useTema va usato dentro <FornitoreTema>')
  }

  return contesto
}
```

### Il problema dei rendering a cascata

```
Quando il valore di un Context cambia, TUTTI i componenti
che lo consumano si ridisegnano — anche quelli che usano
solo la parte che non è cambiata.

  ContestoApp = { utente, tema, notifiche, carrello }

  Cambia una notifica → si ridisegna anche chi legge
  solo il tema.
```

```tsx
// ✅ Contesti separati per dati che cambiano con frequenze diverse
const ContestoUtente = createContext<Utente | null>(null) // cambia raramente
const ContestoTemaSolo = createContext<Tema>('chiaro') // cambia raramente
const ContestoNotifiche = createContext<Notifica[]>([]) // cambia spesso
```

```tsx
// ✅ Separare il valore dal dispatch: chi invia azioni
//    non si ridisegna quando lo stato cambia
const ContestoStato = createContext<Stato | null>(null)
const ContestoInvia = createContext<React.Dispatch<Azione> | null>(null)

function Fornitore({ children }: { children: ReactNode }) {
  const [stato, invia] = useReducer(riduttore, STATO_INIZIALE)

  return (
    <ContestoInvia.Provider value={invia}>
      <ContestoStato.Provider value={stato}>{children}</ContestoStato.Provider>
    </ContestoInvia.Provider>
  )
}
```

`invia` da `useReducer` ha identità stabile: chi consuma solo quello non si ridisegna mai per un cambiamento di stato.

```
Quando Context NON è la risposta:

  ❌ Stato del server (dati da un'API)
     → TanStack Query, che gestisce cache, refetch,
       deduplicazione e stati di caricamento

  ❌ Stato globale che cambia spesso
     → Zustand, Jotai: sottoscrizioni selettive, senza
       ridisegnare tutti i consumatori

  ❌ Solo per evitare due livelli di prop drilling
     → passare le props, o comporre con children

  ✅ Tema, lingua, utente autenticato, configurazione
     → valori che cambiano raramente e servono ovunque
```

---

## B7. Hook personalizzati

Un hook personalizzato è una funzione che chiama altri hook. Il nome deve iniziare con `use`, o il linter non può applicare le regole degli hook.

```tsx
/** Sincronizza uno stato con localStorage. */
function useArchivioLocale<T>(chiave: string, valoreIniziale: T) {
  const [valore, impostaValore] = useState<T>(() => {
    try {
      const grezzo = localStorage.getItem(chiave)
      return grezzo === null ? valoreIniziale : (JSON.parse(grezzo) as T)
    } catch {
      return valoreIniziale
    }
  })

  const aggiorna = useCallback(
    (nuovo: T | ((precedente: T) => T)) => {
      impostaValore((precedente) => {
        const risultato = nuovo instanceof Function ? nuovo(precedente) : nuovo

        try {
          localStorage.setItem(chiave, JSON.stringify(risultato))
        } catch (errore) {
          console.warn('Salvataggio non riuscito', errore)
        }

        return risultato
      })
    },
    [chiave],
  )

  // Sincronizza fra schede diverse
  useEffect(() => {
    function gestisci(evento: StorageEvent) {
      if (evento.key !== chiave || evento.newValue === null) return
      try {
        impostaValore(JSON.parse(evento.newValue) as T)
      } catch {
        /* valore non analizzabile: si ignora */
      }
    }

    window.addEventListener('storage', gestisci)
    return () => window.removeEventListener('storage', gestisci)
  }, [chiave])

  return [valore, aggiorna] as const
}
```

```tsx
/** Un valore che si aggiorna solo dopo una pausa nella digitazione. */
function useRitardato<T>(valore: T, ritardo = 300): T {
  const [ritardato, impostaRitardato] = useState(valore)

  useEffect(() => {
    const temporizzatore = setTimeout(() => impostaRitardato(valore), ritardo)
    return () => clearTimeout(temporizzatore)
  }, [valore, ritardo])

  return ritardato
}
```

```tsx
/** Una query media, con useSyncExternalStore per il rendering concorrente. */
function useMediaQuery(query: string): boolean {
  const sottoscrivi = useCallback(
    (alCambiamento: () => void) => {
      const lista = window.matchMedia(query)
      lista.addEventListener('change', alCambiamento)
      return () => lista.removeEventListener('change', alCambiamento)
    },
    [query],
  )

  return useSyncExternalStore(
    sottoscrivi,
    () => window.matchMedia(query).matches,
    () => false, // sul server non c'è matchMedia
  )
}

function useMovimentoRidotto() {
  return useMediaQuery('(prefers-reduced-motion: reduce)')
}
```

```tsx
/** Chiude un pannello al clic esterno e con Esc. */
function useChiudiFuori<T extends HTMLElement>(alChiudere: () => void) {
  const riferimento = useRef<T>(null)
  // Il ref evita di riregistrare i listener quando il callback cambia
  const callback = useRef(alChiudere)

  useEffect(() => {
    callback.current = alChiudere
  }, [alChiudere])

  useEffect(() => {
    const controller = new AbortController()

    document.addEventListener(
      'pointerdown',
      (evento) => {
        const nodo = riferimento.current
        if (nodo && evento.target instanceof Node && !nodo.contains(evento.target)) {
          callback.current()
        }
      },
      { signal: controller.signal },
    )

    document.addEventListener(
      'keydown',
      (evento) => {
        if (evento.key === 'Escape') callback.current()
      },
      { signal: controller.signal },
    )

    return () => controller.abort()
  }, [])

  return riferimento
}
```

```
Cosa un hook personalizzato condivide, e cosa no:

  ✅ Condivide la LOGICA
  ❌ NON condivide lo STATO

Due componenti che usano useContatore() hanno due contatori
indipendenti. Per condividere lo stato servono Context,
uno store esterno, o il sollevamento dello stato.
```

---

## B8. `useMemo`, `useCallback` e il React Compiler

```tsx
// useMemo memorizza un VALORE
const filtrate = useMemo(
  () => fatture.filter((f) => f.cliente.includes(ricerca)),
  [fatture, ricerca],
)

// useCallback memorizza una FUNZIONE
// (è useMemo(() => fn, deps) con una sintassi più comoda)
const gestisci = useCallback((id: string) => elimina(id), [elimina])
```

### Quando servono davvero

```
Tre casi, e sono gli unici:

  1. Un calcolo COSTOSO su un dato che cambia raramente
     (migliaia di elementi da ordinare, un parsing pesante)

  2. Una prop passata a un componente avvolto in memo
     — altrimenti la memoizzazione non serve a nulla

  3. Una dipendenza di useEffect che altrimenti
     cambierebbe a ogni rendering
```

```tsx
// ❌ Memoizzare un calcolo banale costa PIÙ del calcolo:
//    useMemo deve confrontare le dipendenze e conservare il valore
const doppio = useMemo(() => conteggio * 2, [conteggio])

// ✅
const doppio2 = conteggio * 2
```

```tsx
// ✅ Il caso 2, completo: senza useCallback, memo non serve
const RigaMemo = memo(function Riga({
  fattura,
  alSelezionare,
}: {
  fattura: Fattura
  alSelezionare: (id: string) => void
}) {
  return <li onClick={() => alSelezionare(fattura.id)}>{fattura.numero}</li>
})

function Elenco({ fatture }: { fatture: readonly Fattura[] }) {
  const [selezionata, impostaSelezionata] = useState<string | null>(null)

  // Senza useCallback, questa funzione è nuova a ogni rendering
  // e RigaMemo si ridisegna comunque: memo diventa solo un costo
  const alSelezionare = useCallback((id: string) => impostaSelezionata(id), [])

  return (
    <ul>
      {fatture.map((f) => (
        <RigaMemo key={f.id} fattura={f} alSelezionare={alSelezionare} />
      ))}
    </ul>
  )
}
```

### `memo` e il confronto superficiale

```tsx
// memo confronta le props con Object.is, una per una.
// Un oggetto o un array nuovo lo vede sempre diverso.
const Componente = memo(function Componente({ opzioni }: { opzioni: { a: number } }) {
  return <div>{opzioni.a}</div>
})

// ❌ La memoizzazione non serve: opzioni è nuovo ogni volta
// <Componente opzioni={{ a: 1 }} />

// ✅ Passare primitivi
// <Componente a={1} />
```

### Il React Compiler

```powershell
pnpm add -D babel-plugin-react-compiler
```

```javascript
// vite.config.ts
import react from '@vitejs/plugin-react'

export default {
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler', {}]],
      },
    }),
  ],
}
```

Il compilatore analizza i componenti e inserisce la memoizzazione dove serve, automaticamente. Con il compilatore attivo, `useMemo`, `useCallback` e `memo` scritti a mano diventano in gran parte superflui.

```
La condizione perché funzioni: i componenti devono essere PURI.
Il compilatore verifica e, dove trova una violazione,
salta il componente invece di ottimizzarlo male.

Le violazioni tipiche:
  · modificare le props o lo stato direttamente
  · leggere o scrivere un ref durante il rendering
  · effetti collaterali nel corpo del componente
  · leggere variabili globali mutabili

Le regole di eslint-plugin-react-hooks le intercettano quasi tutte:
tenerle attive è il prerequisito per adottare il compilatore.
```

---

## B9. Data fetching: perché non con `useEffect`

Recuperare dati con `useEffect` richiede di gestire a mano una decina di cose, e quasi nessuna implementazione le gestisce tutte.

```tsx
// L'implementazione "completa" a mano — e le manca ancora molto
function useDati(url: string) {
  const [dati, impostaDati] = useState<unknown>(null)
  const [caricamento, impostaCaricamento] = useState(true)
  const [errore, impostaErrore] = useState<Error | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    impostaCaricamento(true)
    impostaErrore(null)

    fetch(url, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`)
        return r.json()
      })
      .then(impostaDati)
      .catch((e) => {
        if (e.name !== 'AbortError') impostaErrore(e)
      })
      .finally(() => impostaCaricamento(false))

    return () => controller.abort()
  }, [url])

  return { dati, caricamento, errore }
}
```

```
Cosa manca ancora, e serve in ogni applicazione reale:

  · cache fra componenti     due componenti, due richieste identiche
  · deduplicazione            tre montaggi insieme, tre richieste
  · aggiornamento in fondo    dati vecchi mostrati mentre si aggiornano
  · ritentativi               con backoff, sugli errori transitori
  · invalidazione             dopo una modifica, i dati vanno rinfrescati
  · aggiornamento al focus    tornando sulla scheda dopo mezz'ora
  · paginazione               e scorrimento infinito
  · aggiornamento ottimistico
  · stato condiviso           la stessa query in dieci componenti
```

```powershell
pnpm add @tanstack/react-query
```

```tsx
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const clienteQuery = new QueryClient({
  defaultOptions: {
    queries: {
      // Per quanto i dati sono considerati freschi
      staleTime: 60_000,
      // Quanto restano in cache dopo che nessuno li usa più
      gcTime: 5 * 60_000,
      retry: (tentativo, errore) => {
        // Non ritentare gli errori del client: non migliorano
        if (errore instanceof ErroreHttp && errore.stato < 500) return false
        return tentativo < 3
      },
      refetchOnWindowFocus: true,
    },
  },
})

function Radice() {
  return (
    <QueryClientProvider client={clienteQuery}>
      <App />
    </QueryClientProvider>
  )
}
```

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// Le chiavi in un posto solo: senza, si sbagliano
const chiavi = {
  fatture: {
    tutte: ['fatture'] as const,
    elenco: (filtri: Filtri) => ['fatture', 'elenco', filtri] as const,
    dettaglio: (id: string) => ['fatture', 'dettaglio', id] as const,
  },
}

function ElencoFatture({ filtri }: { filtri: Filtri }) {
  const { data, isPending, isError, error, isFetching } = useQuery({
    queryKey: chiavi.fatture.elenco(filtri),
    queryFn: ({ signal }) => recuperaFatture(filtri, { signal }),
  })

  if (isPending) return <Scheletro />
  if (isError) return <Errore errore={error} />

  return (
    <>
      {/* isFetching distingue "sto caricando la prima volta"
          da "sto aggiornando dati che ho già" */}
      {isFetching && <IndicatoreAggiornamento />}
      <Tabella righe={data} />
    </>
  )
}
```

```tsx
// Le mutazioni, con aggiornamento ottimistico
function usaPagaFattura() {
  const cliente = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => pagaFattura(id),

    async onMutate(id) {
      // Ferma le richieste in corso, o sovrascriverebbero
      // l'aggiornamento ottimistico
      await cliente.cancelQueries({ queryKey: chiavi.fatture.tutte })

      const precedenti = cliente.getQueryData(chiavi.fatture.tutte)

      cliente.setQueryData<Fattura[]>(chiavi.fatture.tutte, (vecchie) =>
        vecchie?.map((f) => (f.id === id ? { ...f, pagata: true } : f)),
      )

      return { precedenti }
    },

    onError(_errore, _id, contesto) {
      // Ripristina lo stato precedente
      if (contesto?.precedenti) {
        cliente.setQueryData(chiavi.fatture.tutte, contesto.precedenti)
      }
    },

    onSettled() {
      // In ogni caso, riallinea con il server
      cliente.invalidateQueries({ queryKey: chiavi.fatture.tutte })
    },
  })
}
```

```
La distinzione che cambia l'architettura:

  STATO DEL CLIENT      possiedi tu, è sincrono, è la verità
                        → useState, useReducer, Zustand
                        (un pannello aperto, un filtro, una bozza)

  STATO DEL SERVER      non lo possiedi, è asincrono, può
                        essere già vecchio mentre lo leggi
                        → TanStack Query
                        (elenchi, dettagli, tutto ciò che viene da un'API)

Trattare lo stato del server come stato del client è la
causa principale della complessità nelle applicazioni React.
```

---

## B10. Error Boundary e Suspense

### Error Boundary

Un errore durante il rendering, senza un boundary, smonta l'intera applicazione: schermo bianco.

```tsx
import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = {
  children: ReactNode
  fallback: (errore: Error, riprova: () => void) => ReactNode
  alErrore?: (errore: Error, info: ErrorInfo) => void
}

type Stato = { errore: Error | null }

// Deve essere una CLASSE: non esiste un hook equivalente
export class ConfineErrore extends Component<Props, Stato> {
  override state: Stato = { errore: null }

  static getDerivedStateFromError(errore: Error): Stato {
    return { errore }
  }

  override componentDidCatch(errore: Error, info: ErrorInfo): void {
    this.props.alErrore?.(errore, info)
    console.error('Errore catturato', errore, info.componentStack)
  }

  riprova = (): void => {
    this.setState({ errore: null })
  }

  override render(): ReactNode {
    if (this.state.errore) {
      return this.props.fallback(this.state.errore, this.riprova)
    }
    return this.props.children
  }
}
```

```tsx
// L'uso: boundary GRANULARI, non uno solo attorno a tutto
function Pagina() {
  return (
    <Layout>
      <ConfineErrore fallback={(e, riprova) => <ErroreSezione errore={e} riprova={riprova} />}>
        <Grafico />
      </ConfineErrore>

      <ConfineErrore fallback={() => <p>Tabella non disponibile.</p>}>
        <Tabella />
      </ConfineErrore>
    </Layout>
  )
}
```

Con boundary separati, un errore nel grafico non fa sparire la tabella. Con un boundary solo attorno all'applicazione, qualunque errore svuota lo schermo.

```
Cosa un Error Boundary NON cattura:

  · errori nei gestori di eventi      → try/catch nel gestore
  · errori nel codice asincrono       → .catch() sulla Promise
  · errori nel rendering lato server
  · errori del boundary stesso

Per i primi due serve la gestione esplicita, o un boundary
combinato con TanStack Query (throwOnError: true).
```

### Suspense

```tsx
import { Suspense, lazy } from 'react'

// Il componente viene scaricato solo quando serve
const Grafici = lazy(() => import('./Grafici.tsx'))

function Pagina() {
  return (
    <Suspense fallback={<Scheletro />}>
      <Grafici />
    </Suspense>
  )
}
```

```tsx
// Suspense annidati: ogni sezione ha il proprio fallback,
// e compare appena è pronta
function Cruscotto() {
  return (
    <>
      <Intestazione />

      <Suspense fallback={<ScheletroIndicatori />}>
        <Indicatori />
      </Suspense>

      <Suspense fallback={<ScheletroTabella />}>
        <TabellaFatture />
      </Suspense>
    </>
  )
}
```

```tsx
// La combinazione che serve davvero: boundary + Suspense
function Sezione({ children }: { children: ReactNode }) {
  return (
    <ConfineErrore fallback={(e, riprova) => <ErroreSezione errore={e} riprova={riprova} />}>
      <Suspense fallback={<Scheletro />}>{children}</Suspense>
    </ConfineErrore>
  )
}
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Eliminare gli `useEffect` superflui

**Obiettivo:** un componente con quattro effetti, di cui tre non dovrebbero esistere. Individuarli e riscriverlo.

```tsx
// PARTENZA
function CruscottoSbagliato({ fatture, idUtente }: Props) {
  const [filtro, impostaFiltro] = useState('')
  const [filtrate, impostaFiltrate] = useState<Fattura[]>([])
  const [totale, impostaTotale] = useState(0)
  const [utente, impostaUtente] = useState<Utente | null>(null)
  const [salvato, impostaSalvato] = useState(false)

  // Effetto 1
  useEffect(() => {
    impostaFiltrate(fatture.filter((f) => f.cliente.includes(filtro)))
  }, [fatture, filtro])

  // Effetto 2
  useEffect(() => {
    impostaTotale(filtrate.reduce((s, f) => s + f.importo, 0))
  }, [filtrate])

  // Effetto 3
  useEffect(() => {
    if (salvato) {
      mostraNotifica('Salvato')
      registraEvento('cruscotto-salvato')
      impostaSalvato(false)
    }
  }, [salvato])

  // Effetto 4
  useEffect(() => {
    fetch(`/api/utenti/${idUtente}`)
      .then((r) => r.json())
      .then(impostaUtente)
  }, [idUtente])

  return (
    <>
      <input value={filtro} onChange={(e) => impostaFiltro(e.target.value)} />
      <p>{utente?.nome}</p>
      <Tabella righe={filtrate} totale={totale} />
      <button onClick={() => impostaSalvato(true)}>Salva</button>
    </>
  )
}
```

```tsx
// SOLUZIONE

function Cruscotto({ fatture, idUtente }: Props) {
  const [filtro, impostaFiltro] = useState('')

  // ── EFFETTI 1 e 2 ELIMINATI ──────────────────────────────
  // Erano dati DERIVATI: si calcolano durante il rendering.
  // Costavano due rendering in più a ogni digitazione, e
  // introducevano un fotogramma in cui filtrate e totale
  // erano disallineati fra loro.
  const filtrate = fatture.filter((f) => f.cliente.includes(filtro))
  const totale = filtrate.reduce((s, f) => s + f.importo, 0)

  // ── EFFETTO 4 SOSTITUITO ─────────────────────────────────
  // L'originale non aveva: gestione dell'errore, annullamento
  // al cambio di idUtente, stato di caricamento, cache,
  // deduplicazione. Query le dà tutte.
  const {
    data: utente,
    isPending,
    isError,
  } = useQuery({
    queryKey: ['utenti', idUtente],
    queryFn: ({ signal }) => recuperaUtente(idUtente, { signal }),
  })

  // ── EFFETTO 3 SPOSTATO NEL GESTORE ───────────────────────
  // Non serviva uno stato per segnalare che era successo
  // qualcosa: il fatto accade nel gestore, e lì va la logica.
  function gestisciSalvataggio() {
    salva(filtrate)
    mostraNotifica('Salvato')
    registraEvento('cruscotto-salvato')
  }

  return (
    <>
      <input value={filtro} onChange={(e) => impostaFiltro(e.target.value)} />

      {isPending && <span>Caricamento…</span>}
      {isError && <span role="alert">Utente non disponibile</span>}
      {utente && <p>{utente.nome}</p>}

      <Tabella righe={filtrate} totale={totale} />
      <button onClick={gestisciSalvataggio}>Salva</button>
    </>
  )
}
```

```
# Il bilancio:
#
#   4 effetti → 0 effetti
#   5 stati   → 1 stato
#
# Effetto 1 e 2: dati DERIVATI.
#   Un effetto che chiama setState su un valore calcolabile
#   dalle props produce SEMPRE un rendering in più:
#   React disegna con il vecchio valore, esegue l'effetto,
#   e ridisegna. Con due effetti concatenati, tre rendering.
#
# Effetto 3: reazione a un EVENTO.
#   Lo stato 'salvato' serviva solo a segnalare all'effetto
#   che era stato premuto un pulsante. Il pulsante lo sa già.
#   Il pattern "imposta un flag e reagisci nell'effetto"
#   è quasi sempre un gestore di eventi travestito.
#
# Effetto 4: FETCH.
#   L'unico che aveva ragione di esistere, ed è quello
#   che va delegato a una libreria: la versione a mano
#   manca di otto comportamenti che servono davvero.
#
# LA DOMANDA DA PORSI davanti a ogni useEffect:
#   "Sto sincronizzando con qualcosa di ESTERNO a React?"
#   Se la risposta è no, l'effetto non serve.
```

---

### Esercizio 2 — Un hook per la ricerca, con annullamento

**Obiettivo:** un campo di ricerca che ritarda le richieste, annulla quelle superate e non produce risultati fuori ordine.

```tsx
// SOLUZIONE

/** Ritarda un valore: si aggiorna solo dopo una pausa. */
function useRitardato<T>(valore: T, ritardo = 300): T {
  const [ritardato, impostaRitardato] = useState(valore)

  useEffect(() => {
    const temporizzatore = setTimeout(() => impostaRitardato(valore), ritardo)
    return () => clearTimeout(temporizzatore)
  }, [valore, ritardo])

  return ritardato
}

type StatoRicerca<T> =
  | { stato: 'inattiva' }
  | { stato: 'caricamento' }
  | { stato: 'riuscita'; risultati: readonly T[] }
  | { stato: 'fallita'; errore: Error }

function useRicerca<T>(
  termine: string,
  cerca: (termine: string, opzioni: { signal: AbortSignal }) => Promise<readonly T[]>,
  { ritardo = 300, lunghezzaMinima = 2 } = {},
): StatoRicerca<T> {
  const ritardato = useRitardato(termine, ritardo)
  const [stato, impostaStato] = useState<StatoRicerca<T>>({ stato: 'inattiva' })

  // Il callback in un ref: cambiandone l'identità non
  // deve riavviare la ricerca
  const cercaRef = useRef(cerca)
  useEffect(() => {
    cercaRef.current = cerca
  }, [cerca])

  useEffect(() => {
    if (ritardato.trim().length < lunghezzaMinima) {
      impostaStato({ stato: 'inattiva' })
      return
    }

    const controller = new AbortController()
    impostaStato({ stato: 'caricamento' })

    cercaRef
      .current(ritardato, { signal: controller.signal })
      .then((risultati) => {
        // Il segnale è già annullato se una ricerca più recente
        // è partita: senza questa verifica, una risposta lenta
        // sovrascriverebbe una veloce più recente
        if (controller.signal.aborted) return
        impostaStato({ stato: 'riuscita', risultati })
      })
      .catch((errore: unknown) => {
        if (errore instanceof Error && errore.name === 'AbortError') return
        impostaStato({
          stato: 'fallita',
          errore: errore instanceof Error ? errore : new Error(String(errore)),
        })
      })

    return () => controller.abort()
  }, [ritardato, lunghezzaMinima])

  return stato
}
```

```tsx
// L'uso, con l'accessibilità che il pattern richiede
function CampoRicerca() {
  const [termine, impostaTermine] = useState('')
  const stato = useRicerca(termine, cercaClienti)

  return (
    <div className="ricerca">
      <label htmlFor="ricerca">Cerca un cliente</label>
      <input
        type="search"
        id="ricerca"
        value={termine}
        onChange={(evento) => impostaTermine(evento.target.value)}
        role="combobox"
        aria-expanded={stato.stato === 'riuscita' && stato.risultati.length > 0}
        aria-controls="risultati-ricerca"
        aria-describedby="stato-ricerca"
        autoComplete="off"
      />

      {/* La live region annuncia gli aggiornamenti senza
          spostare il focus dal campo */}
      <p id="stato-ricerca" role="status" aria-live="polite" className="solo-screen-reader">
        {stato.stato === 'caricamento' && 'Ricerca in corso'}
        {stato.stato === 'riuscita' && `${stato.risultati.length} risultati`}
        {stato.stato === 'fallita' && 'Ricerca non riuscita'}
      </p>

      {stato.stato === 'riuscita' && (
        <ul id="risultati-ricerca" role="listbox">
          {stato.risultati.map((cliente) => (
            <li key={cliente.id} role="option" aria-selected={false}>
              {cliente.nome}
            </li>
          ))}
        </ul>
      )}

      {stato.stato === 'fallita' && (
        <p role="alert">Ricerca non riuscita: {stato.errore.message}</p>
      )}
    </div>
  )
}
```

```
# I quattro problemi che questo hook risolve, e che
# un'implementazione ingenua ha tutti:
#
# 1. TROPPE RICHIESTE
#    Senza il ritardo, digitare "milano" produce sei richieste.
#    Con 300 ms, ne produce una.
#
# 2. RISPOSTE FUORI ORDINE
#    Cercando "a" e poi "ab", la risposta di "a" può arrivare
#    DOPO quella di "ab" e sovrascriverla: l'utente vede
#    i risultati sbagliati. L'AbortController annulla la
#    richiesta superata, e la verifica su signal.aborted
#    scarta comunque una risposta arrivata in ritardo.
#
# 3. LO STATO INCOERENTE
#    Con { caricamento, risultati, errore } separati sono
#    possibili stati insensati: caricamento true insieme
#    a un errore. La discriminated union li rende
#    irrappresentabili.
#
# 4. IL CALLBACK NELLE DIPENDENZE
#    Mettendo 'cerca' fra le dipendenze, un callback inline
#    definito nel genitore riavvierebbe la ricerca a ogni
#    rendering. Il ref lo tiene aggiornato senza
#    farlo diventare una dipendenza.
#
# NOTA: in un progetto reale, useQuery con la chiave
# ['ricerca', termineRitardato] fa tutto questo e in più
# mette in cache i risultati fra ricerche ripetute.
# Questo esercizio serve a capire COSA la libreria fa.
```

---

### Esercizio 3 — Un form complesso con `useReducer`

**Obiettivo:** un form a più passi con validazione, dove le transizioni sono esplicite e testabili senza React.

```tsx
// SOLUZIONE — src/modulo-ordine/riduttore.ts

export type Passo = 'dati' | 'spedizione' | 'pagamento' | 'riepilogo'

export type ValoriModulo = {
  nome: string
  email: string
  indirizzo: string
  citta: string
  cap: string
  metodoPagamento: 'carta' | 'bonifico' | ''
}

export type Errori = Partial<Record<keyof ValoriModulo, string>>

export type Stato = {
  passo: Passo
  valori: ValoriModulo
  errori: Errori
  passiVisitati: readonly Passo[]
  invio: 'inattivo' | 'in-corso' | 'riuscito' | 'fallito'
  messaggioErrore: string | null
}

export type Azione =
  | { tipo: 'cambia-campo'; campo: keyof ValoriModulo; valore: string }
  | { tipo: 'vai-a'; passo: Passo }
  | { tipo: 'avanti' }
  | { tipo: 'indietro' }
  | { tipo: 'errori-validazione'; errori: Errori }
  | { tipo: 'invio-iniziato' }
  | { tipo: 'invio-riuscito' }
  | { tipo: 'invio-fallito'; messaggio: string }
  | { tipo: 'azzera' }

export const PASSI: readonly Passo[] = ['dati', 'spedizione', 'pagamento', 'riepilogo']

/** I campi che ogni passo richiede: la validazione li usa. */
const CAMPI_PER_PASSO: Record<Passo, readonly (keyof ValoriModulo)[]> = {
  dati: ['nome', 'email'],
  spedizione: ['indirizzo', 'citta', 'cap'],
  pagamento: ['metodoPagamento'],
  riepilogo: [],
}

export const STATO_INIZIALE: Stato = {
  passo: 'dati',
  valori: { nome: '', email: '', indirizzo: '', citta: '', cap: '', metodoPagamento: '' },
  errori: {},
  passiVisitati: ['dati'],
  invio: 'inattivo',
  messaggioErrore: null,
}

/** Valida solo i campi del passo indicato. */
export function validaPasso(valori: ValoriModulo, passo: Passo): Errori {
  const errori: Errori = {}

  for (const campo of CAMPI_PER_PASSO[passo]) {
    const valore = valori[campo].trim()

    if (valore === '') {
      errori[campo] = 'Campo obbligatorio'
      continue
    }

    if (campo === 'email' && !valore.includes('@')) {
      errori[campo] = 'Indirizzo non valido'
    }

    if (campo === 'cap' && !/^\d{5}$/.test(valore)) {
      errori[campo] = 'Il CAP deve avere cinque cifre'
    }
  }

  return errori
}

/** Una funzione PURA: si testa senza React, senza DOM, senza mock. */
export function riduttore(stato: Stato, azione: Azione): Stato {
  switch (azione.tipo) {
    case 'cambia-campo':
      return {
        ...stato,
        valori: { ...stato.valori, [azione.campo]: azione.valore },
        // Digitando, l'errore di QUEL campo sparisce
        errori: { ...stato.errori, [azione.campo]: undefined },
      }

    case 'vai-a': {
      // Si può tornare solo su un passo già visitato
      if (!stato.passiVisitati.includes(azione.passo)) return stato
      return { ...stato, passo: azione.passo, errori: {} }
    }

    case 'avanti': {
      const errori = validaPasso(stato.valori, stato.passo)
      if (Object.keys(errori).length > 0) {
        return { ...stato, errori }
      }

      const indice = PASSI.indexOf(stato.passo)
      const prossimo = PASSI[indice + 1]
      if (prossimo === undefined) return stato

      return {
        ...stato,
        passo: prossimo,
        errori: {},
        passiVisitati: stato.passiVisitati.includes(prossimo)
          ? stato.passiVisitati
          : [...stato.passiVisitati, prossimo],
      }
    }

    case 'indietro': {
      const indice = PASSI.indexOf(stato.passo)
      const precedente = PASSI[indice - 1]
      if (precedente === undefined) return stato
      return { ...stato, passo: precedente, errori: {} }
    }

    case 'errori-validazione':
      return { ...stato, errori: azione.errori }

    case 'invio-iniziato':
      return { ...stato, invio: 'in-corso', messaggioErrore: null }

    case 'invio-riuscito':
      return { ...stato, invio: 'riuscito' }

    case 'invio-fallito':
      return { ...stato, invio: 'fallito', messaggioErrore: azione.messaggio }

    case 'azzera':
      return STATO_INIZIALE

    default: {
      const esaustivo: never = azione
      throw new Error(`Azione non gestita: ${JSON.stringify(esaustivo)}`)
    }
  }
}
```

```tsx
// src/modulo-ordine/ModuloOrdine.tsx
import { useReducer } from 'react'
import { PASSI, riduttore, STATO_INIZIALE, type Passo } from './riduttore.js'

const ETICHETTE: Record<Passo, string> = {
  dati: 'I tuoi dati',
  spedizione: 'Spedizione',
  pagamento: 'Pagamento',
  riepilogo: 'Riepilogo',
}

export function ModuloOrdine() {
  const [stato, invia] = useReducer(riduttore, STATO_INIZIALE)

  async function gestisciInvio(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault()

    if (stato.passo !== 'riepilogo') {
      invia({ tipo: 'avanti' })
      return
    }

    invia({ tipo: 'invio-iniziato' })

    try {
      await inviaOrdine(stato.valori)
      invia({ tipo: 'invio-riuscito' })
    } catch (errore) {
      invia({
        tipo: 'invio-fallito',
        messaggio: errore instanceof Error ? errore.message : 'Errore sconosciuto',
      })
    }
  }

  if (stato.invio === 'riuscito') {
    return (
      <div role="status">
        <h2>Ordine ricevuto</h2>
        <button onClick={() => invia({ tipo: 'azzera' })}>Nuovo ordine</button>
      </div>
    )
  }

  const indiceCorrente = PASSI.indexOf(stato.passo)

  return (
    <form onSubmit={gestisciInvio} noValidate>
      {/* La navigazione fra i passi, accessibile */}
      <nav aria-label="Passi dell'ordine">
        <ol>
          {PASSI.map((passo, indice) => {
            const visitato = stato.passiVisitati.includes(passo)
            const corrente = passo === stato.passo

            return (
              <li key={passo}>
                <button
                  type="button"
                  onClick={() => invia({ tipo: 'vai-a', passo })}
                  disabled={!visitato}
                  aria-current={corrente ? 'step' : undefined}
                >
                  {indice + 1}. {ETICHETTE[passo]}
                </button>
              </li>
            )
          })}
        </ol>
      </nav>

      <fieldset>
        <legend>{ETICHETTE[stato.passo]}</legend>

        {stato.passo === 'dati' && (
          <>
            <Campo
              id="nome"
              etichetta="Nome e cognome"
              valore={stato.valori.nome}
              errore={stato.errori.nome}
              autoComplete="name"
              alCambiare={(v) => invia({ tipo: 'cambia-campo', campo: 'nome', valore: v })}
            />
            <Campo
              id="email"
              etichetta="Email"
              tipo="email"
              valore={stato.valori.email}
              errore={stato.errori.email}
              autoComplete="email"
              alCambiare={(v) => invia({ tipo: 'cambia-campo', campo: 'email', valore: v })}
            />
          </>
        )}

        {stato.passo === 'spedizione' && (
          <>
            <Campo
              id="indirizzo"
              etichetta="Indirizzo"
              valore={stato.valori.indirizzo}
              errore={stato.errori.indirizzo}
              autoComplete="street-address"
              alCambiare={(v) => invia({ tipo: 'cambia-campo', campo: 'indirizzo', valore: v })}
            />
            <Campo
              id="cap"
              etichetta="CAP"
              valore={stato.valori.cap}
              errore={stato.errori.cap}
              autoComplete="postal-code"
              inputMode="numeric"
              alCambiare={(v) => invia({ tipo: 'cambia-campo', campo: 'cap', valore: v })}
            />
          </>
        )}
      </fieldset>

      <div className="azioni">
        {indiceCorrente > 0 && (
          <button type="button" onClick={() => invia({ tipo: 'indietro' })}>
            Indietro
          </button>
        )}

        <button type="submit" disabled={stato.invio === 'in-corso'}>
          {stato.passo === 'riepilogo'
            ? stato.invio === 'in-corso'
              ? 'Invio…'
              : 'Conferma l ordine'
            : 'Avanti'}
        </button>
      </div>

      {stato.messaggioErrore && <p role="alert">{stato.messaggioErrore}</p>}
    </form>
  )
}
```

```typescript
// src/modulo-ordine/riduttore.test.ts
// Il riduttore è puro: si testa senza montare nulla
import { describe, it, expect } from 'vitest'
import { riduttore, STATO_INIZIALE, validaPasso } from './riduttore.js'

describe('riduttore del modulo ordine', () => {
  it('non avanza se il passo corrente ha errori', () => {
    const dopo = riduttore(STATO_INIZIALE, { tipo: 'avanti' })

    expect(dopo.passo).toBe('dati') // non è avanzato
    expect(dopo.errori.nome).toBe('Campo obbligatorio')
    expect(dopo.errori.email).toBe('Campo obbligatorio')
  })

  it('avanza quando i campi del passo sono validi', () => {
    let stato = STATO_INIZIALE
    stato = riduttore(stato, { tipo: 'cambia-campo', campo: 'nome', valore: 'Anna' })
    stato = riduttore(stato, {
      tipo: 'cambia-campo',
      campo: 'email',
      valore: 'anna@example.it',
    })
    stato = riduttore(stato, { tipo: 'avanti' })

    expect(stato.passo).toBe('spedizione')
    expect(stato.passiVisitati).toContain('spedizione')
  })

  it('cancella l errore del campo mentre si digita', () => {
    const conErrore = riduttore(STATO_INIZIALE, { tipo: 'avanti' })
    expect(conErrore.errori.nome).toBeDefined()

    const dopo = riduttore(conErrore, {
      tipo: 'cambia-campo',
      campo: 'nome',
      valore: 'A',
    })

    expect(dopo.errori.nome).toBeUndefined()
    // L'errore dell'ALTRO campo resta
    expect(dopo.errori.email).toBeDefined()
  })

  it('non permette di saltare a un passo non visitato', () => {
    const dopo = riduttore(STATO_INIZIALE, { tipo: 'vai-a', passo: 'pagamento' })
    expect(dopo).toBe(STATO_INIZIALE) // stesso oggetto: nessun cambiamento
  })

  it('valida il CAP con cinque cifre', () => {
    const errori = validaPasso(
      { ...STATO_INIZIALE.valori, indirizzo: 'Via Roma 1', citta: 'Milano', cap: '123' },
      'spedizione',
    )
    expect(errori.cap).toBe('Il CAP deve avere cinque cifre')
  })
})
```

```
# Output atteso:
 ✓ riduttore del modulo ordine (5)
   ✓ non avanza se il passo corrente ha errori
   ✓ avanza quando i campi del passo sono validi
   ✓ cancella l errore del campo mentre si digita
   ✓ non permette di saltare a un passo non visitato
   ✓ valida il CAP con cinque cifre
```

```
# Perché useReducer invece di sei useState:
#
# 1. LE TRANSIZIONI SONO ESPLICITE.
#    'avanti' valida, e avanza solo se la validazione passa.
#    Con useState separati, quella logica finirebbe sparsa
#    nel gestore del pulsante, e sarebbe da duplicare
#    per ogni punto che fa avanzare.
#
# 2. IL RIDUTTORE È PURO: SI TESTA SENZA REACT.
#    I cinque test qui sopra non montano nulla, non usano
#    il DOM, non hanno mock. Girano in millisecondi.
#    Testare la stessa logica attraverso l'interfaccia
#    richiederebbe render, click e attese.
#
# 3. LO STATO NON PUÒ DESINCRONIZZARSI.
#    passo, errori e passiVisitati cambiano insieme in una
#    sola transizione. Con setState separati, un ramo che
#    dimentica di aggiornarne uno produce uno stato incoerente.
#
# 4. L'ESAUSTIVITÀ.
#    Aggiungendo un'azione senza gestirla, il caso 'never'
#    nel default diventa un errore di compilazione.
#
# QUANDO BASTA useState:
#   uno o due valori indipendenti, transizioni ovvie.
#   Non ogni form ha bisogno di un riduttore.
```

---

### Esercizio 4 — Un componente accessibile: il menu a discesa

**Obiettivo:** un menu con navigazione da tastiera completa, gestione del focus e attributi ARIA corretti.

```tsx
// SOLUZIONE
import { useEffect, useId, useRef, useState } from 'react'

type Voce = {
  id: string
  etichetta: string
  alSelezionare: () => void
  disabilitata?: boolean
}

type MenuProps = {
  etichetta: string
  voci: readonly Voce[]
}

export function Menu({ etichetta, voci }: MenuProps) {
  const [aperto, impostaAperto] = useState(false)
  // -1 = nessuna voce evidenziata
  const [evidenziata, impostaEvidenziata] = useState(-1)

  const idMenu = useId()
  const comando = useRef<HTMLButtonElement>(null)
  const pannello = useRef<HTMLUListElement>(null)

  const selezionabili = voci.filter((v) => !v.disabilitata)

  function apri(indiceIniziale: number) {
    impostaAperto(true)
    impostaEvidenziata(indiceIniziale)
  }

  function chiudi({ ridaiIlFocus = true } = {}) {
    impostaAperto(false)
    impostaEvidenziata(-1)
    // Il focus torna al comando: senza, finirebbe su <body>
    // e la navigazione da tastiera ricomincerebbe dall'inizio
    if (ridaiIlFocus) comando.current?.focus()
  }

  function seleziona(indice: number) {
    const voce = voci[indice]
    if (!voce || voce.disabilitata) return
    voce.alSelezionare()
    chiudi()
  }

  /** Sposta l'evidenziazione, saltando le voci disabilitate. */
  function muovi(direzione: 1 | -1) {
    impostaEvidenziata((corrente) => {
      let prossimo = corrente

      for (let passi = 0; passi < voci.length; passi++) {
        prossimo = (prossimo + direzione + voci.length) % voci.length
        if (!voci[prossimo]?.disabilitata) return prossimo
      }

      return corrente
    })
  }

  // Chiusura al clic esterno
  useEffect(() => {
    if (!aperto) return

    const controller = new AbortController()

    document.addEventListener(
      'pointerdown',
      (evento) => {
        const bersaglio = evento.target
        if (!(bersaglio instanceof Node)) return
        if (comando.current?.contains(bersaglio)) return
        if (pannello.current?.contains(bersaglio)) return
        chiudi({ ridaiIlFocus: false })
      },
      { signal: controller.signal },
    )

    return () => controller.abort()
  }, [aperto])

  // Il focus segue l'evidenziazione
  useEffect(() => {
    if (!aperto || evidenziata < 0) return

    const voce = pannello.current?.querySelectorAll('[role="menuitem"]')[evidenziata]
    if (voce instanceof HTMLElement) voce.focus()
  }, [aperto, evidenziata])

  function gestisciTastoComando(evento: React.KeyboardEvent<HTMLButtonElement>) {
    switch (evento.key) {
      case 'ArrowDown':
      case 'Enter':
      case ' ':
        evento.preventDefault()
        apri(0) // dalla prima voce
        break

      case 'ArrowUp':
        evento.preventDefault()
        apri(voci.length - 1) // dall'ultima
        break
    }
  }

  function gestisciTastoPannello(evento: React.KeyboardEvent<HTMLUListElement>) {
    switch (evento.key) {
      case 'ArrowDown':
        evento.preventDefault()
        muovi(1)
        break

      case 'ArrowUp':
        evento.preventDefault()
        muovi(-1)
        break

      case 'Home':
        evento.preventDefault()
        impostaEvidenziata(0)
        break

      case 'End':
        evento.preventDefault()
        impostaEvidenziata(voci.length - 1)
        break

      case 'Enter':
      case ' ':
        evento.preventDefault()
        seleziona(evidenziata)
        break

      case 'Escape':
        evento.preventDefault()
        chiudi()
        break

      case 'Tab':
        // Tab chiude il menu e prosegue la navigazione:
        // è il comportamento atteso, non va impedito
        chiudi({ ridaiIlFocus: false })
        break

      default:
        // Ricerca digitando: salta alla prima voce che inizia
        // con la lettera premuta
        if (evento.key.length === 1 && /\S/.test(evento.key)) {
          const lettera = evento.key.toLowerCase()
          const indice = voci.findIndex(
            (v, i) =>
              i > evidenziata && !v.disabilitata && v.etichetta.toLowerCase().startsWith(lettera),
          )
          const daCapo = voci.findIndex(
            (v) => !v.disabilitata && v.etichetta.toLowerCase().startsWith(lettera),
          )
          const trovato = indice !== -1 ? indice : daCapo
          if (trovato !== -1) {
            evento.preventDefault()
            impostaEvidenziata(trovato)
          }
        }
    }
  }

  return (
    <div className="menu">
      <button
        ref={comando}
        type="button"
        id={`${idMenu}-comando`}
        aria-haspopup="menu"
        aria-expanded={aperto}
        aria-controls={aperto ? `${idMenu}-pannello` : undefined}
        onClick={() => (aperto ? chiudi() : apri(0))}
        onKeyDown={gestisciTastoComando}
      >
        {etichetta}
        <span aria-hidden="true">{aperto ? '▲' : '▼'}</span>
      </button>

      {aperto && (
        <ul
          ref={pannello}
          id={`${idMenu}-pannello`}
          role="menu"
          aria-labelledby={`${idMenu}-comando`}
          onKeyDown={gestisciTastoPannello}
          className="menu__pannello"
        >
          {voci.map((voce, indice) => (
            <li key={voce.id} role="none">
              <button
                type="button"
                role="menuitem"
                // Roving tabindex: una sola voce è raggiungibile
                // con Tab, le altre con le frecce
                tabIndex={indice === evidenziata ? 0 : -1}
                aria-disabled={voce.disabilitata}
                onClick={() => seleziona(indice)}
                onMouseEnter={() => !voce.disabilitata && impostaEvidenziata(indice)}
                className="menu__voce"
              >
                {voce.etichetta}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
```

```
# I comportamenti che il pattern ARIA richiede, e che
# quasi nessuna implementazione artigianale ha tutti:
#
#   Freccia giù sul comando   apre ed evidenzia la PRIMA voce
#   Freccia su sul comando    apre ed evidenzia l'ULTIMA
#   Invio / Spazio            apre, o seleziona se già aperto
#   Frecce nel pannello       si spostano, SALTANDO le disabilitate
#   Home / End                prima e ultima voce
#   Esc                       chiude E RIDÀ IL FOCUS al comando
#   Tab                       chiude e prosegue la navigazione
#   digitare una lettera      salta alla voce che inizia con quella
#   clic esterno              chiude SENZA rubare il focus
#
# GLI ATTRIBUTI ARIA:
#   aria-haspopup="menu"   dice che il comando apre un menu
#   aria-expanded          sul COMANDO, non sul pannello
#   aria-controls          collega comando e pannello
#   role="menu"/"menuitem" la semantica del widget
#   role="none" sul <li>   il ruolo di lista è sostituito dal menu
#   aria-disabled          invece di 'disabled': una voce disabilitata
#                          resta ANNUNCIABILE, e l'utente sa che esiste
#
# IL ROVING TABINDEX:
#   Una sola voce ha tabIndex 0, le altre -1. Tab entra e
#   esce dal menu; dentro ci si muove con le frecce.
#   È il pattern standard dei widget composti.
#
# QUANDO NON SCRIVERLO A MANO:
#   Radix UI o React Aria forniscono questo comportamento
#   già verificato sugli screen reader reali. Questo esercizio
#   serve a capire COSA quelle librerie fanno, e perché
#   un menu scritto in venti righe è quasi sempre rotto.
```

---

### Esercizio 5 — Rendere veloce una lista lenta

**Obiettivo:** una tabella con 5.000 righe che scatta a ogni digitazione. Trovare la causa e correggerla.

```tsx
// PARTENZA — tre problemi distinti
function TabellaLenta({ fatture }: { fatture: Fattura[] }) {
  const [ricerca, impostaRicerca] = useState('')
  const [ordinamento, impostaOrdinamento] = useState<keyof Fattura>('numero')

  // Problema 1: filtro e ordinamento a ogni rendering
  const visibili = fatture
    .filter((f) => f.cliente.toLowerCase().includes(ricerca.toLowerCase()))
    .sort((a, b) => String(a[ordinamento]).localeCompare(String(b[ordinamento])))

  return (
    <>
      <input value={ricerca} onChange={(e) => impostaRicerca(e.target.value)} />
      <table>
        <tbody>
          {visibili.map((f, indice) => (
            // Problema 2: la chiave è l'indice
            <RigaFattura
              key={indice}
              fattura={f}
              // Problema 3: funzione nuova a ogni rendering
              alSelezionare={() => seleziona(f.id)}
            />
          ))}
        </tbody>
      </table>
    </>
  )
}
```

```tsx
// SOLUZIONE
import { memo, useCallback, useDeferredValue, useMemo, useState } from 'react'

const RigaFattura = memo(function RigaFattura({
  fattura,
  alSelezionare,
}: {
  fattura: Fattura
  alSelezionare: (id: string) => void
}) {
  return (
    <tr onClick={() => alSelezionare(fattura.id)}>
      <th scope="row">{fattura.numero}</th>
      <td>{fattura.cliente}</td>
      <td className="numerico">{fattura.importo}</td>
    </tr>
  )
})

function Tabella({
  fatture,
  alSelezionare,
}: {
  fatture: readonly Fattura[]
  alSelezionare: (id: string) => void
}) {
  const [ricerca, impostaRicerca] = useState('')
  const [ordinamento, impostaOrdinamento] = useState<keyof Fattura>('numero')

  // ── CORREZIONE 1 ──────────────────────────────────────────
  // useDeferredValue: il campo resta reattivo mentre la tabella
  // si aggiorna in ritardo. È meglio del debounce, perché React
  // può INTERROMPERE il rendering della lista se l'utente
  // continua a digitare.
  const ricercaDifferita = useDeferredValue(ricerca)

  // useMemo evita di rifiltrare e riordinare 5.000 righe
  // quando cambia qualcos'altro nel componente
  const visibili = useMemo(() => {
    const termine = ricercaDifferita.toLowerCase()

    return fatture
      .filter((f) => f.cliente.toLowerCase().includes(termine))
      .toSorted((a, b) => String(a[ordinamento]).localeCompare(String(b[ordinamento]), 'it'))
  }, [fatture, ricercaDifferita, ordinamento])

  // ── CORREZIONE 3 ──────────────────────────────────────────
  // Identità stabile: senza, memo su RigaFattura non servirebbe
  const gestisciSelezione = useCallback(
    (id: string) => alSelezionare(id),
    [alSelezionare],
  )

  // L'utente vede che i risultati stanno per aggiornarsi
  const inAggiornamento = ricerca !== ricercaDifferita

  return (
    <>
      <input
        value={ricerca}
        onChange={(evento) => impostaRicerca(evento.target.value)}
        aria-describedby="conteggio-risultati"
      />

      <p id="conteggio-risultati" role="status" aria-live="polite">
        {visibili.length} risultati
      </p>

      <table style={{ opacity: inAggiornamento ? 0.6 : 1 }}>
        <tbody>
          {visibili.map((f) => (
            // ── CORREZIONE 2 ──────────────────────────────
            // La chiave è l'id: React abbina le righe per
            // identità, non per posizione
            <RigaFattura key={f.id} fattura={f} alSelezionare={gestisciSelezione} />
          ))}
        </tbody>
      </table>
    </>
  )
}
```

```tsx
// ── CORREZIONE 4: la virtualizzazione ────────────────────────
// Oltre qualche centinaio di righe, la soluzione vera non è
// ottimizzare il rendering di 5.000 nodi: è non crearli.
import { useVirtualizer } from '@tanstack/react-virtual'
import { useRef } from 'react'

function TabellaVirtuale({ righe }: { righe: readonly Fattura[] }) {
  const contenitore = useRef<HTMLDivElement>(null)

  const virtualizzatore = useVirtualizer({
    count: righe.length,
    getScrollElement: () => contenitore.current,
    estimateSize: () => 48,
    overscan: 8, // righe extra sopra e sotto, per lo scorrimento fluido
  })

  return (
    <div ref={contenitore} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizzatore.getTotalSize()}px`, position: 'relative' }}>
        {virtualizzatore.getVirtualItems().map((virtuale) => {
          const fattura = righe[virtuale.index]
          if (!fattura) return null

          return (
            <div
              key={fattura.id}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtuale.size}px`,
                transform: `translateY(${virtuale.start}px)`,
              }}
            >
              {fattura.numero} — {fattura.cliente}
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

```
# COME MISURARE, invece di indovinare:
#
# 1. React DevTools → Profiler → registra durante la digitazione
#    · "Ranked" mostra i componenti per tempo impiegato
#    · "Why did this render?" (va attivato nelle impostazioni)
#      dice QUALE prop è cambiata
#
# 2. DevTools → Performance → cerca i long task (> 50 ms)
#    Un task lungo durante la digitazione è la causa
#    della sensazione di lentezza.
#
# 3. Il conteggio dei nodi del DOM:
#      document.querySelectorAll('*').length
#    Oltre 5.000 nodi, il browser stesso rallenta,
#    indipendentemente da React.
#
#
# L'ORDINE IN CUI INTERVENIRE:
#
#   1. Chiavi stabili           ← gratis, e corregge anche i bug
#   2. Meno nodi (virtualizzazione) ← il guadagno maggiore
#   3. useDeferredValue         ← mantiene reattivo l'input
#   4. useMemo sui calcoli pesanti
#   5. memo + useCallback       ← solo insieme, o memo è inutile
#
# CON IL REACT COMPILER attivo, i punti 4 e 5 diventano
# in gran parte superflui: il compilatore inserisce la
# memoizzazione dove serve. I punti 1, 2 e 3 restano
# scelte architetturali che nessun compilatore può fare.
#
# useDeferredValue contro debounce:
#   il debounce ASPETTA un tempo fisso prima di aggiornare.
#   useDeferredValue aggiorna SUBITO se c'è tempo, e rinvia
#   solo se il thread è occupato — e può interrompere un
#   rendering già iniziato. Su un dispositivo veloce non
#   si nota alcun ritardo; su uno lento degrada con grazia.
```

---

## C2. Mini-progetto: dashboard aziendale

L'esercizio chiave del modulo: una dashboard con autenticazione simulata, grafici, tabelle con ordinamento e filtri, e routing multipagina.

### Cosa deve avere

1. Routing con React Router 7, con rotte protette.
2. Autenticazione simulata, con contesto e persistenza.
3. Dati dal server via TanStack Query, con cache e stati di caricamento.
4. Tabella con ordinamento, filtri e paginazione, con lo stato nell'URL.
5. Error Boundary e Suspense per sezione.
6. Accessibilità: landmark, focus alla navigazione, live region.

### Struttura

```
dashboard/
├── src/
│   ├── main.tsx
│   ├── rotte.tsx
│   ├── autenticazione/
│   │   ├── ContestoAutenticazione.tsx
│   │   └── RottaProtetta.tsx
│   ├── api/
│   │   ├── cliente.ts        fetch con verifica di risposta.ok
│   │   ├── schemi.ts         Zod
│   │   └── query.ts          chiavi e hook di query
│   ├── componenti/
│   │   ├── ConfineErrore.tsx
│   │   ├── Tabella.tsx
│   │   └── Scheletro.tsx
│   └── pagine/
│       ├── Accesso.tsx
│       ├── Panoramica.tsx
│       └── Fatture.tsx
```

### `src/autenticazione/ContestoAutenticazione.tsx`

```tsx
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

export type Utente = {
  readonly id: string
  readonly nome: string
  readonly ruoli: readonly string[]
}

type StatoAutenticazione =
  | { stato: 'anonimo' }
  | { stato: 'autenticazione' }
  | { stato: 'autenticato'; utente: Utente }

type ContestoAutenticazione = {
  readonly autenticazione: StatoAutenticazione
  accedi(email: string, password: string): Promise<void>
  esci(): void
  haRuolo(ruolo: string): boolean
}

const Contesto = createContext<ContestoAutenticazione | null>(null)

export function FornitoreAutenticazione({ children }: { children: ReactNode }) {
  const [autenticazione, impostaAutenticazione] = useState<StatoAutenticazione>(() => {
    // Ripristino dalla sessione, validato
    try {
      const grezzo = sessionStorage.getItem('utente')
      if (grezzo === null) return { stato: 'anonimo' }

      const analizzato: unknown = JSON.parse(grezzo)
      if (
        typeof analizzato === 'object' &&
        analizzato !== null &&
        'id' in analizzato &&
        'nome' in analizzato
      ) {
        return { stato: 'autenticato', utente: analizzato as Utente }
      }
      return { stato: 'anonimo' }
    } catch {
      return { stato: 'anonimo' }
    }
  })

  const accedi = useCallback(async (email: string, password: string) => {
    impostaAutenticazione({ stato: 'autenticazione' })

    try {
      const utente = await autenticaUtente(email, password)
      sessionStorage.setItem('utente', JSON.stringify(utente))
      impostaAutenticazione({ stato: 'autenticato', utente })
    } catch (errore) {
      impostaAutenticazione({ stato: 'anonimo' })
      throw errore
    }
  }, [])

  const esci = useCallback(() => {
    sessionStorage.removeItem('utente')
    impostaAutenticazione({ stato: 'anonimo' })
  }, [])

  const haRuolo = useCallback(
    (ruolo: string) =>
      autenticazione.stato === 'autenticato' && autenticazione.utente.ruoli.includes(ruolo),
    [autenticazione],
  )

  // useMemo indispensabile: senza, il valore è un oggetto nuovo
  // a ogni rendering e OGNI consumatore si ridisegna
  const valore = useMemo(
    () => ({ autenticazione, accedi, esci, haRuolo }),
    [autenticazione, accedi, esci, haRuolo],
  )

  return <Contesto.Provider value={valore}>{children}</Contesto.Provider>
}

export function useAutenticazione(): ContestoAutenticazione {
  const contesto = useContext(Contesto)
  if (contesto === null) {
    throw new Error('useAutenticazione va usato dentro <FornitoreAutenticazione>')
  }
  return contesto
}
```

### `src/autenticazione/RottaProtetta.tsx`

```tsx
import { Navigate, Outlet, useLocation } from 'react-router'
import { useAutenticazione } from './ContestoAutenticazione.js'

export function RottaProtetta({ ruoloRichiesto }: { ruoloRichiesto?: string }) {
  const { autenticazione, haRuolo } = useAutenticazione()
  const posizione = useLocation()

  if (autenticazione.stato === 'autenticazione') {
    return <p role="status">Verifica delle credenziali…</p>
  }

  if (autenticazione.stato === 'anonimo') {
    // 'state' conserva la destinazione: dopo l'accesso
    // si torna dove si stava andando, non alla home
    return <Navigate to="/accesso" state={{ da: posizione.pathname }} replace />
  }

  if (ruoloRichiesto !== undefined && !haRuolo(ruoloRichiesto)) {
    return (
      <div role="alert">
        <h1>Accesso negato</h1>
        <p>Non hai i permessi per questa sezione.</p>
      </div>
    )
  }

  return <Outlet />
}
```

### `src/pagine/Fatture.tsx`

```tsx
import { useSearchParams } from 'react-router'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { useDeferredValue, useMemo } from 'react'

export function Fatture() {
  // Lo stato dei filtri sta nell'URL: la pagina è condivisibile,
  // il pulsante indietro funziona, e un ricaricamento non perde nulla
  const [parametri, impostaParametri] = useSearchParams()

  const filtri = useMemo(
    () => ({
      pagina: Number(parametri.get('pagina') ?? '1'),
      ricerca: parametri.get('ricerca') ?? '',
      stato: parametri.get('stato') ?? '',
      ordine: parametri.get('ordine') ?? '-numero',
    }),
    [parametri],
  )

  const ricercaDifferita = useDeferredValue(filtri.ricerca)

  const { data, isPending, isError, error, isFetching } = useQuery({
    queryKey: ['fatture', { ...filtri, ricerca: ricercaDifferita }],
    queryFn: ({ signal }) => recuperaFatture({ ...filtri, ricerca: ricercaDifferita }, { signal }),
    // Mantiene i dati precedenti mentre carica la pagina nuova:
    // senza, la tabella lampeggia a ogni cambio di pagina
    placeholderData: keepPreviousData,
  })

  function aggiornaFiltro(chiave: string, valore: string) {
    impostaParametri((precedenti) => {
      const nuovi = new URLSearchParams(precedenti)
      if (valore === '') {
        nuovi.delete(chiave)
      } else {
        nuovi.set(chiave, valore)
      }
      // Cambiando un filtro si torna alla prima pagina
      if (chiave !== 'pagina') nuovi.delete('pagina')
      return nuovi
    })
  }

  if (isPending) return <ScheletroTabella />
  if (isError) return <Errore errore={error} />

  return (
    <section aria-labelledby="titolo-fatture">
      <h1 id="titolo-fatture">Fatture</h1>

      <div className="filtri">
        <label htmlFor="ricerca">Cerca</label>
        <input
          type="search"
          id="ricerca"
          value={filtri.ricerca}
          onChange={(evento) => aggiornaFiltro('ricerca', evento.target.value)}
        />

        <label htmlFor="stato">Stato</label>
        <select
          id="stato"
          value={filtri.stato}
          onChange={(evento) => aggiornaFiltro('stato', evento.target.value)}
        >
          <option value="">Tutti</option>
          <option value="emessa">Emesse</option>
          <option value="pagata">Pagate</option>
        </select>
      </div>

      <p role="status" aria-live="polite">
        {isFetching ? 'Aggiornamento…' : `${data.totale} fatture`}
      </p>

      <Tabella righe={data.elementi} inAggiornamento={isFetching} />

      <Paginazione
        pagina={filtri.pagina}
        totale={data.totale}
        perPagina={50}
        alCambiare={(p) => aggiornaFiltro('pagina', String(p))}
      />
    </section>
  )
}
```

### `src/rotte.tsx`

```tsx
import { createBrowserRouter, RouterProvider } from 'react-router'
import { lazy, Suspense } from 'react'

const Panoramica = lazy(() => import('./pagine/Panoramica.js'))
const Fatture = lazy(() => import('./pagine/Fatture.js'))
const Impostazioni = lazy(() => import('./pagine/Impostazioni.js'))

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    errorElement: <ErrorePagina />,
    children: [
      { path: 'accesso', element: <Accesso /> },
      {
        element: <RottaProtetta />,
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<Scheletro />}>
                <Panoramica />
              </Suspense>
            ),
          },
          {
            path: 'fatture',
            element: (
              <Suspense fallback={<ScheletroTabella />}>
                <Fatture />
              </Suspense>
            ),
          },
        ],
      },
      {
        element: <RottaProtetta ruoloRichiesto="admin" />,
        children: [
          {
            path: 'impostazioni',
            element: (
              <Suspense fallback={<Scheletro />}>
                <Impostazioni />
              </Suspense>
            ),
          },
        ],
      },
    ],
  },
])

export function Rotte() {
  return <RouterProvider router={router} />
}
```

### L'accessibilità del routing

```tsx
// Cambiando pagina in una SPA, il focus resta dov'era e
// gli screen reader non annunciano nulla: l'utente non
// sa che la pagina è cambiata.
import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router'

function Layout() {
  const posizione = useLocation()
  const titolo = useRef<HTMLHeadingElement>(null)
  const annunci = useRef<HTMLParagraphElement>(null)

  useEffect(() => {
    // Il focus sul titolo della pagina nuova
    titolo.current?.focus()

    // E l'annuncio, per chi non vede lo spostamento del focus
    if (annunci.current) {
      annunci.current.textContent = `Pagina ${document.title}`
    }
  }, [posizione.pathname])

  return (
    <>
      <a href="#contenuto" className="salta-al-contenuto">
        Vai al contenuto principale
      </a>

      <p ref={annunci} role="status" aria-live="polite" className="solo-screen-reader" />

      <header>
        <Navigazione />
      </header>

      <main id="contenuto">
        {/* tabindex -1 rende il titolo focalizzabile via JavaScript
            senza inserirlo nell'ordine di tabulazione */}
        <h1 ref={titolo} tabIndex={-1} className="titolo-pagina">
          {/* ... */}
        </h1>
        <Outlet />
      </main>
    </>
  )
}
```

### Verifica

```
# I controlli, in ordine:
#
# 1. ROUTING E PROTEZIONE
#    · Vai a /fatture da anonimo: reindirizza ad /accesso
#    · Accedi: torni su /fatture, non sulla home
#      (è lo state.da del Navigate)
#    · Vai a /impostazioni senza il ruolo admin:
#      messaggio di accesso negato, non schermo bianco
#
# 2. STATO NELL'URL
#    · Filtra e ordina, poi copia l'indirizzo e aprilo
#      in una scheda nuova: gli stessi filtri
#    · Il pulsante indietro ripercorre i filtri
#    · Un ricaricamento non perde nulla
#
# 3. CACHE E AGGIORNAMENTO
#    · Naviga fra due pagine e torna: i dati compaiono
#      SUBITO dalla cache, e si aggiornano in sottofondo
#    · React Query DevTools mostra lo stato di ogni query
#
# 4. ERROR BOUNDARY
#    · Fai fallire una sola sezione (blocca una richiesta
#      in DevTools → Network): solo quella mostra l'errore,
#      il resto della pagina resta usabile
#
# 5. ACCESSIBILITÀ
#    · Tab dall'inizio: il salto al contenuto è il primo
#    · Cambiando pagina, il focus va sul titolo e lo
#      screen reader lo annuncia
#    · Le tabelle hanno caption e scope
#    · Zoom al 200%: nessuno scorrimento orizzontale
#
# 6. TIPI
#    pnpm exec tsc --noEmit
```

```
# I meccanismi del tutorial usati, e dove:
#
#   Context           autenticazione: cambia raramente, serve ovunque
#                     → il caso d'uso corretto per Context
#   useMemo sul valore del provider  senza, ogni consumatore
#                     si ridisegna a ogni rendering del provider
#   TanStack Query    lo stato del SERVER, con cache e deduplicazione
#   useSearchParams   lo stato dei filtri nell'URL, non in useState:
#                     condivisibile, e il pulsante indietro funziona
#   useDeferredValue  il campo resta reattivo mentre la tabella carica
#   Suspense + lazy   ogni pagina è un bundle separato
#   Error Boundary    granulari: un errore non svuota la pagina
#   discriminated union  lo stato dell'autenticazione
#   focus alla navigazione  ciò che una SPA rompe e va rimesso a mano
```

---

# Parte D — Approfondimento per Esperti

---

## D1. React 19: `use`, Actions e `useOptimistic`

### `use`

`use` legge una Promise o un Context. A differenza degli altri hook, può stare dentro un `if` e dentro un ciclo.

```tsx
import { use, Suspense } from 'react'

// La Promise si crea FUORI dal componente, o in un genitore.
// Crearla dentro produrrebbe una Promise nuova a ogni rendering,
// e un ciclo infinito.
function Dettaglio({ promessaUtente }: { promessaUtente: Promise<Utente> }) {
  // Sospende finché la Promise non si risolve: il fallback
  // del Suspense più vicino compare al suo posto
  const utente = use(promessaUtente)

  return <h1>{utente.nome}</h1>
}

function Pagina({ id }: { id: string }) {
  // In un'applicazione reale la Promise viene dal router,
  // da un Server Component, o da una cache
  const promessa = useMemo(() => recuperaUtente(id), [id])

  return (
    <Suspense fallback={<Scheletro />}>
      <Dettaglio promessaUtente={promessa} />
    </Suspense>
  )
}
```

```tsx
// use con Context: si può chiamare condizionalmente
function Componente({ mostraTema }: { mostraTema: boolean }) {
  if (mostraTema) {
    const tema = use(ContestoTema) // legale: useContext non lo sarebbe
    return <div className={tema}>…</div>
  }
  return <div>…</div>
}
```

### Le Actions e `useActionState`

```tsx
import { useActionState } from 'react'

type StatoModulo = {
  esito: 'inattivo' | 'riuscito' | 'fallito'
  messaggio: string
  errori?: Record<string, string>
}

async function inviaContatto(
  statoPrecedente: StatoModulo,
  dati: FormData,
): Promise<StatoModulo> {
  const nome = String(dati.get('nome') ?? '').trim()
  const email = String(dati.get('email') ?? '').trim()

  const errori: Record<string, string> = {}
  if (nome === '') errori['nome'] = 'Campo obbligatorio'
  if (!email.includes('@')) errori['email'] = 'Indirizzo non valido'

  if (Object.keys(errori).length > 0) {
    return { esito: 'fallito', messaggio: 'Correggi i campi segnalati', errori }
  }

  try {
    await salvaContatto({ nome, email })
    return { esito: 'riuscito', messaggio: 'Messaggio inviato' }
  } catch (errore) {
    return {
      esito: 'fallito',
      messaggio: errore instanceof Error ? errore.message : 'Invio non riuscito',
    }
  }
}

function ModuloContatti() {
  const [stato, azione, inCorso] = useActionState(inviaContatto, {
    esito: 'inattivo',
    messaggio: '',
  })

  return (
    <form action={azione}>
      <label htmlFor="nome">Nome</label>
      <input
        id="nome"
        name="nome"
        aria-invalid={stato.errori?.['nome'] !== undefined}
        aria-describedby={stato.errori?.['nome'] ? 'errore-nome' : undefined}
      />
      {stato.errori?.['nome'] && (
        <p id="errore-nome" role="alert">
          {stato.errori['nome']}
        </p>
      )}

      <label htmlFor="email">Email</label>
      <input id="email" name="email" type="email" />

      <button type="submit" disabled={inCorso}>
        {inCorso ? 'Invio…' : 'Invia'}
      </button>

      {stato.messaggio && (
        <p role={stato.esito === 'fallito' ? 'alert' : 'status'}>{stato.messaggio}</p>
      )}
    </form>
  )
}
```

Il form è **non controllato**: nessun `useState` per i campi, nessun `onChange`. React legge il `FormData` all'invio, gestisce lo stato di caricamento e azzera il form quando l'azione riesce.

### `useFormStatus`

```tsx
import { useFormStatus } from 'react-dom'

// Legge lo stato del form PADRE: va usato in un componente
// figlio, non nello stesso che contiene <form>
function PulsanteInvio({ children }: { children: ReactNode }) {
  const { pending } = useFormStatus()

  return (
    <button type="submit" disabled={pending} aria-busy={pending}>
      {pending ? 'Invio in corso…' : children}
    </button>
  )
}

function Modulo() {
  return (
    <form action={azione}>
      <input name="email" />
      {/* Il pulsante sa da solo se il form sta inviando */}
      <PulsanteInvio>Iscriviti</PulsanteInvio>
    </form>
  )
}
```

### `useOptimistic`

```tsx
import { useOptimistic, useRef } from 'react'

function ElencoMessaggi({ messaggi }: { messaggi: readonly Messaggio[] }) {
  const modulo = useRef<HTMLFormElement>(null)

  const [ottimistici, aggiungiOttimistico] = useOptimistic(
    messaggi,
    (stato, nuovoTesto: string) => [
      ...stato,
      { id: `provvisorio-${Date.now()}`, testo: nuovoTesto, inInvio: true },
    ],
  )

  async function azione(dati: FormData) {
    const testo = String(dati.get('testo') ?? '')

    // Compare SUBITO nell'elenco, prima che il server risponda
    aggiungiOttimistico(testo)
    modulo.current?.reset()

    await inviaMessaggio(testo)
    // Quando l'azione finisce, React scarta lo stato ottimistico
    // e usa quello reale. Se fallisce, il messaggio sparisce.
  }

  return (
    <>
      <ul>
        {ottimistici.map((messaggio) => (
          <li key={messaggio.id} style={{ opacity: messaggio.inInvio ? 0.5 : 1 }}>
            {messaggio.testo}
            {messaggio.inInvio && <span className="solo-screen-reader"> in invio</span>}
          </li>
        ))}
      </ul>

      <form action={azione} ref={modulo}>
        <label htmlFor="testo">Messaggio</label>
        <input id="testo" name="testo" required />
        <PulsanteInvio>Invia</PulsanteInvio>
      </form>
    </>
  )
}
```

### Le altre novità di React 19

```tsx
// ref come prop normale: forwardRef non serve più
function Campo({ ref, ...resto }: { ref?: React.Ref<HTMLInputElement> }) {
  return <input ref={ref} {...resto} />
}

// I metadati del documento si dichiarano dove servono:
// React li sposta nel <head>
function PaginaFattura({ fattura }: { fattura: Fattura }) {
  return (
    <article>
      <title>Fattura {fattura.numero} — Acme</title>
      <meta name="description" content={`Fattura ${fattura.numero}`} />
      <link rel="canonical" href={`https://acme.it/fatture/${fattura.id}`} />

      <h1>Fattura {fattura.numero}</h1>
    </article>
  )
}

// I fogli di stile con precedenza: React ne gestisce l'ordine
function Componente() {
  return (
    <>
      <link rel="stylesheet" href="/base.css" precedence="default" />
      <link rel="stylesheet" href="/tema.css" precedence="high" />
      <div className="componente">…</div>
    </>
  )
}
```

---

## D2. Rendering concorrente e transizioni

React può **interrompere** un rendering in corso per gestire un aggiornamento più urgente. È il meccanismo che rende reattive le interfacce con liste lunghe.

```tsx
import { useTransition, useDeferredValue, useState } from 'react'

function Ricerca() {
  const [termine, impostaTermine] = useState('')
  const [inTransizione, avviaTransizione] = useTransition()
  const [risultati, impostaRisultati] = useState<readonly Risultato[]>([])

  function gestisciCambio(evento: React.ChangeEvent<HTMLInputElement>) {
    // URGENTE: il campo deve rispondere immediatamente
    impostaTermine(evento.target.value)

    // NON urgente: può essere interrotto se l'utente
    // continua a digitare
    avviaTransizione(() => {
      impostaRisultati(cercaSincrono(evento.target.value))
    })
  }

  return (
    <>
      <input value={termine} onChange={gestisciCambio} />
      <div style={{ opacity: inTransizione ? 0.6 : 1 }}>
        <Risultati elementi={risultati} />
      </div>
    </>
  )
}
```

```
useTransition o useDeferredValue:

  useTransition     hai il CONTROLLO dell'aggiornamento:
                    lo avvolgi tu in startTransition.
                    Dà anche il booleano isPending.

  useDeferredValue  ricevi un VALORE dall'esterno (una prop,
                    uno stato che non controlli) e vuoi che
                    il suo consumo sia meno urgente.
                    Il "pending" si deduce confrontando
                    valore e valore differito.
```

```tsx
// startTransition fuori da un componente, per le navigazioni
import { startTransition } from 'react'

function naviga(percorso: string) {
  startTransition(() => {
    router.navigate(percorso)
  })
}
```

```tsx
// ⚠ startTransition non funziona con gli aggiornamenti
//    che avvengono DOPO un await: quelli sono già
//    fuori dal contesto della transizione.

// ❌
avviaTransizione(async () => {
  const dati = await recupera()
  impostaDati(dati) // fuori dalla transizione
})

// ✅ React 19 supporta le funzioni async in startTransition,
//    ma la forma esplicita resta più chiara
async function carica() {
  const dati = await recupera()
  startTransition(() => impostaDati(dati))
}
```

---

## D3. Componenti accessibili

React non rende accessibile nulla di per sé: al contrario, rende facile costruire componenti che sembrano funzionare e non lo sono.

### `useId` per collegare etichette e messaggi

```tsx
import { useId } from 'react'

function CampoTesto({
  etichetta,
  aiuto,
  errore,
  ...resto
}: {
  etichetta: string
  aiuto?: string
  errore?: string
} & React.ComponentPropsWithoutRef<'input'>) {
  // useId genera un identificativo stabile fra server e client:
  // Math.random() produrrebbe valori diversi e romperebbe l'idratazione
  const id = useId()
  const idAiuto = `${id}-aiuto`
  const idErrore = `${id}-errore`

  const descrittori = [aiuto ? idAiuto : null, errore ? idErrore : null]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="campo">
      <label htmlFor={id}>{etichetta}</label>

      <input
        id={id}
        aria-invalid={errore !== undefined}
        aria-describedby={descrittori || undefined}
        {...resto}
      />

      {aiuto && (
        <p id={idAiuto} className="aiuto">
          {aiuto}
        </p>
      )}

      {errore && (
        <p id={idErrore} role="alert" className="errore">
          {errore}
        </p>
      )}
    </div>
  )
}
```

### La gestione del focus in una modale

```tsx
import { useEffect, useRef } from 'react'

function Modale({
  aperta,
  alChiudere,
  titolo,
  children,
}: {
  aperta: boolean
  alChiudere: () => void
  titolo: string
  children: ReactNode
}) {
  const finestra = useRef<HTMLDialogElement>(null)
  const focusPrecedente = useRef<HTMLElement | null>(null)

  useEffect(() => {
    const nodo = finestra.current
    if (!nodo) return

    if (aperta) {
      // Ricorda chi aveva il focus, per restituirglielo
      focusPrecedente.current = document.activeElement as HTMLElement | null

      // showModal() e non show(): confinamento del focus,
      // Esc, ::backdrop e top layer sono gestiti dal browser
      nodo.showModal()
    } else if (nodo.open) {
      nodo.close()
    }
  }, [aperta])

  useEffect(() => {
    if (aperta) return
    // Restituisce il focus alla chiusura
    focusPrecedente.current?.focus()
  }, [aperta])

  return (
    <dialog
      ref={finestra}
      // 'cancel' scatta con Esc: senza preventDefault,
      // la dialog si chiude senza avvisare React
      onCancel={(evento) => {
        evento.preventDefault()
        alChiudere()
      }}
      onClose={alChiudere}
      aria-labelledby="titolo-modale"
    >
      <h2 id="titolo-modale">{titolo}</h2>
      {children}
      <button type="button" onClick={alChiudere}>
        Chiudi
      </button>
    </dialog>
  )
}
```

### Le live region per gli aggiornamenti asincroni

```tsx
function ElencoConAnnunci({ filtri }: { filtri: Filtri }) {
  const { data, isFetching } = useQuery({
    queryKey: ['fatture', filtri],
    queryFn: () => recuperaFatture(filtri),
  })

  return (
    <>
      {/* La region ESISTE sempre, anche vuota: creandola
          insieme al testo, l'annuncio non avverrebbe */}
      <p role="status" aria-live="polite" className="solo-screen-reader">
        {isFetching ? 'Caricamento dei risultati' : `${data?.length ?? 0} risultati trovati`}
      </p>

      <Tabella righe={data ?? []} />
    </>
  )
}
```

### Gli errori più comuni nei componenti React

```tsx
// ❌ Un div cliccabile: nessun ruolo, nessuna risposta alla tastiera
<div onClick={salva} className="pulsante">Salva</div>

// ✅
<button type="button" onClick={salva}>Salva</button>

// ❌ Un'icona senza nome accessibile
<button onClick={elimina}><IconaCestino /></button>

// ✅
<button type="button" onClick={elimina} aria-label="Elimina la fattura">
  <IconaCestino aria-hidden="true" focusable="false" />
</button>

// ❌ Lo stato del caricamento solo visivo
{caricamento && <Rotella />}

// ✅ Annunciato anche a chi non vede
{caricamento && (
  <div role="status" aria-live="polite">
    <Rotella aria-hidden="true" />
    <span className="solo-screen-reader">Caricamento in corso</span>
  </div>
)}

// ❌ aria-hidden su un elemento focalizzabile: l'utente
//    ci arriva con Tab e non sa dove si trova
<button aria-hidden="true">Nascosto</button>

// ✅
<button aria-hidden="true" tabIndex={-1} disabled>Nascosto</button>
```

```javascript
// eslint.config.js — le regole che intercettano quasi tutto
import jsxA11y from 'eslint-plugin-jsx-a11y'

export default [
  {
    plugins: { 'jsx-a11y': jsxA11y },
    rules: {
      ...jsxA11y.configs.recommended.rules,
      'jsx-a11y/no-static-element-interactions': 'error',
      'jsx-a11y/click-events-have-key-events': 'error',
      'jsx-a11y/label-has-associated-control': 'error',
    },
  },
]
```

---

## D4. Testare i componenti

```powershell
pnpm add -D vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom happy-dom
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    setupFiles: ['./test/preparazione.ts'],
    globals: true,
  },
})
```

```typescript
// test/preparazione.ts
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => cleanup())
```

### Il principio: testare come usa l'utente

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'

describe('ModuloContatti', () => {
  it('mostra un errore quando l email non è valida', async () => {
    const utente = userEvent.setup()
    render(<ModuloContatti />)

    // Le query per RUOLO e per ETICHETTA: sono quelle che
    // un utente e uno screen reader usano davvero.
    // Un test che passa con getByRole prova anche che
    // il componente è accessibile.
    await utente.type(screen.getByLabelText('Email'), 'non-valida')
    await utente.click(screen.getByRole('button', { name: 'Invia' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Indirizzo non valido')
  })

  it('invia i dati corretti', async () => {
    const utente = userEvent.setup()
    const alInviare = vi.fn()

    render(<ModuloContatti alInviare={alInviare} />)

    await utente.type(screen.getByLabelText('Nome'), 'Anna')
    await utente.type(screen.getByLabelText('Email'), 'anna@example.it')
    await utente.click(screen.getByRole('button', { name: 'Invia' }))

    expect(alInviare).toHaveBeenCalledWith({ nome: 'Anna', email: 'anna@example.it' })
  })
})
```

```
La priorità delle query, dalla migliore alla peggiore:

  1. getByRole          come lo trova uno screen reader
  2. getByLabelText     per i campi di form
  3. getByPlaceholderText
  4. getByText          per il contenuto non interattivo
  5. getByDisplayValue
  6. getByAltText
  7. getByTitle
  8. getByTestId        ← ultima risorsa: non è ciò che l'utente vede

Se serve getByTestId, spesso il componente manca di
un'etichetta accessibile — e il test lo sta segnalando.
```

### Le tre varianti, e quando usarle

```tsx
it('mostra le tre varianti in azione', async () => {
  // getBy*    solleva se non trova. Per ciò che DEVE esserci ora.
  screen.getByRole('button')

  // queryBy*  restituisce null. L'UNICA per verificare l'ASSENZA.
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()

  // findBy*   restituisce una Promise. Per ciò che compare DOPO.
  expect(await screen.findByText('Salvato')).toBeInTheDocument()
})
```

### Testare i componenti che recuperano dati

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'

/** Un client nuovo per test, senza ritentativi né cache condivisa. */
function disegnaConQuery(componente: ReactElement) {
  const cliente = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  })

  return render(<QueryClientProvider client={cliente}>{componente}</QueryClientProvider>)
}
```

```typescript
// MSW intercetta a livello di rete: il componente usa fetch
// vero, e non sa di essere in un test
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { beforeAll, afterEach, afterAll } from 'vitest'

const server = setupServer(
  http.get('/api/fatture', () =>
    HttpResponse.json({ elementi: [{ id: '1', numero: '2026-001', importo: 1200 }] }),
  ),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

```tsx
it('mostra un messaggio quando il server fallisce', async () => {
  // Sovrascrive il gestore solo per questo test
  server.use(http.get('/api/fatture', () => new HttpResponse(null, { status: 500 })))

  disegnaConQuery(<ElencoFatture />)

  expect(await screen.findByRole('alert')).toHaveTextContent(/non disponibil/i)
})
```

### Cosa non testare

```
❌ NON testare:
   · lo stato interno del componente
     (useState, useReducer: sono dettagli implementativi)
   · che un mock restituisca ciò che gli hai detto di restituire
   · i nomi delle classi CSS
   · il numero di rendering
   · React stesso

✅ Testare:
   · cosa l'utente VEDE dopo un'interazione
   · cosa il componente CHIAMA (le funzioni ricevute come prop)
   · i casi limite: elenco vuoto, errore di rete, dati parziali
   · l'accessibilità: se getByRole non trova, c'è un problema

Il criterio: un refactoring che non cambia il comportamento
non deve rompere i test. Se li rompe, i test verificavano
l'implementazione invece del comportamento.
```

### Testare l'accessibilità automaticamente

```tsx
import { axe } from 'vitest-axe'

it('non ha violazioni di accessibilità rilevabili', async () => {
  const { container } = render(<ModuloContatti />)
  const risultati = await axe(container)

  expect(risultati.violations).toHaveLength(0)
})
```

Intercetta circa un terzo dei problemi reali. Il resto — ordine di tabulazione, contrasto su immagini, alt sbagliati — richiede la verifica manuale descritta in `tutorial_01_html5.md`.

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
REACT — Mappa dei concetti

IL PRINCIPIO
└── interfaccia = f(stato)
    Descrivi COM'È, non COME cambiarla.
    Cambia lo stato → React richiama f → confronta → aggiorna il DOM.

JSX
├── className · htmlFor · camelCase · style come oggetto
├── {espressioni}, non istruzioni
├── ⚠ {0 && <X/>} STAMPA lo zero → usa length > 0
├── null, undefined, false, true → non disegnati
└── Un solo elemento radice: <>...</> o Fragment con key

COMPONENTI
├── Funzioni pure: stesse props → stesso risultato
├── Le props sono in SOLA LETTURA (readonly nella firma)
├── children e le prop di tipo ReactNode = composizione
└── ComponentPropsWithoutRef<'button'> per i componenti di base

RENDERING
├── Cambia lo stato → si ridisegna il componente E TUTTI i figli
│     React NON verifica le props prima di richiamarli
├── children creato nel NONNO non cambia identità
│     → composizione invece di memo
├── Oggetti, array e funzioni inline sono NUOVI a ogni rendering
└── key diversa → React DISTRUGGE e ricrea (azzera lo stato)

LISTE E CHIAVI
└── key = identità stabile legata al DATO
    L'indice va bene solo se: mai riordinata, mai inserimenti
    in mezzo, nessuno stato interno. Fuori da lì, produce bug
    di stato assegnato all'elemento sbagliato.

STATO
├── useState
│     forma FUNZIONALE quando dipende dal precedente
│     inizializzatore pigro: useState(() => costoso())
│     oggetti e array NUOVI, mai modificati
├── Non mettere nello stato ciò che si può CALCOLARE
├── Sollevarlo all'antenato comune più VICINO
├── Abbassarlo dove isola i rendering
└── useReducer quando più valori cambiano insieme
      il riduttore è puro → si testa senza React

EFFETTI
├── useEffect SINCRONIZZA con l'esterno, non "esegue dopo"
├── La pulizia è metà del contratto
├── StrictMode monta due volte per farlo emergere
├── Le dipendenze: tutte, davvero (exhaustive-deps)
└── ❌ NON serve per:
      derivare dati        → calcola durante il rendering
      reagire a un evento  → la logica va nel gestore
      azzerare lo stato    → usa la key
      recuperare dati      → TanStack Query

REF
├── Nodo del DOM (in React 19 'ref' è una prop normale)
├── Valore che sopravvive senza far ridisegnare
└── ⚠ Mai leggerlo o scriverlo durante il rendering

CONTEXT
├── Risolve il prop drilling, NON è uno state manager
├── useMemo sul valore, o ogni consumatore si ridisegna
├── Contesti separati per dati con frequenze diverse
├── Separare stato e dispatch: dispatch ha identità stabile
└── ❌ Non per lo stato del server, né per ciò che cambia spesso

MEMOIZZAZIONE
├── useMemo (valore) · useCallback (funzione) · memo (componente)
├── Servono in TRE casi: calcolo costoso, prop di un memo,
│     dipendenza di un effetto
├── memo senza useCallback sulle prop funzione = solo costo
└── Il React Compiler li rende in gran parte superflui
      → richiede componenti PURI

DATI DAL SERVER
├── Stato del CLIENT (possiedi tu) ≠ stato del SERVER
├── useEffect + fetch manca di: cache, deduplicazione,
│     ritentativi, invalidazione, aggiornamento al focus
└── TanStack Query: chiavi in un posto solo, mutazioni
      con aggiornamento ottimistico e rollback

AFFIDABILITÀ
├── Error Boundary: classe, GRANULARI (uno per sezione)
│     non cattura eventi né codice asincrono
└── Suspense: fallback dichiarativo, annidabile

REACT 19
├── use()             legge Promise e Context, anche condizionale
├── <form action={}>  form non controllati, con FormData
├── useActionState    stato, azione e pending in un hook
├── useFormStatus     nel FIGLIO, legge il form padre
├── useOptimistic     aggiornamento immediato, rollback automatico
└── ref come prop · metadati del documento inline

CONCORRENZA
├── useTransition     tu controlli l'aggiornamento, e hai isPending
└── useDeferredValue  ricevi un valore, ne rinvii il consumo

ACCESSIBILITÀ
├── useId per collegare label, aiuto ed errori
├── Il focus alla navigazione: una SPA lo rompe, va rimesso
├── Le live region devono ESISTERE prima del testo
└── Testare con getByRole: se non trova, manca un'etichetta
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Sai spiegare la differenza fra imperativo e dichiarativo con un esempio
- [ ] Conosci le differenze fra JSX e HTML e sai perché esistono
- [ ] Sai perché `{elenco.length && <X/>}` stampa uno zero
- [ ] Tipizzi le props e usi `ComponentPropsWithoutRef`
- [ ] Sai spiegare perché l'indice come `key` produce bug di stato
- [ ] Usi la forma funzionale di `setState` quando dipende dal precedente
- [ ] Sai perché serve l'inizializzatore pigro e quando
- [ ] Aggiorni oggetti e array creandone di nuovi
- [ ] Distingui form controllati e non controllati e sai scegliere
- [ ] Sai cosa fa `StrictMode` e perché il doppio montaggio è utile
- [ ] Scrivi la pulizia di ogni effetto che ne ha bisogno

**Parte B — Comprensione**

- [ ] Sai che React richiama tutti i figli senza verificarne le props
- [ ] Usi `children` per evitare rendering, invece di `memo`
- [ ] Sai perché cambiare `key` azzera lo stato, e quando conviene
- [ ] Sai riconoscere lo stato ridondante e sostituirlo con un calcolo
- [ ] Sai dove sollevare lo stato e dove abbassarlo
- [ ] Sai elencare i quattro casi in cui `useEffect` non serve
- [ ] Sai quando `useEffect` è invece la scelta corretta
- [ ] Usi `useSyncExternalStore` per uno store esterno
- [ ] Sai perché un oggetto nelle dipendenze produce un ciclo
- [ ] Scrivi un riduttore puro con verifica di esaustività
- [ ] Distingui i due usi di `useRef` e sai che non va toccato nel rendering
- [ ] Sai perché il valore di un Context va memoizzato
- [ ] Sai separare stato e dispatch in due contesti, e perché
- [ ] Sai cosa un hook personalizzato condivide e cosa no
- [ ] Conosci i tre casi in cui `useMemo` e `useCallback` servono
- [ ] Sai perché `memo` senza `useCallback` è solo un costo
- [ ] Sai cosa richiede il React Compiler per funzionare
- [ ] Sai elencare cosa manca a un `useEffect` che recupera dati
- [ ] Distingui stato del client e stato del server
- [ ] Sai perché gli Error Boundary vanno granulari

**Parte C — Pratica**

- [ ] Hai eliminato tre `useEffect` su quattro dal componente dell'esercizio 1
- [ ] Hai scritto l'hook di ricerca con annullamento e ordine garantito
- [ ] Hai testato un riduttore senza montare alcun componente
- [ ] Hai costruito il menu con la navigazione da tastiera completa
- [ ] Hai misurato con il Profiler prima di ottimizzare
- [ ] Hai costruito la dashboard con lo stato dei filtri nell'URL

**Parte D — Esperto**

- [ ] Sai perché la Promise passata a `use` non va creata nel componente
- [ ] Usi `useActionState` e sai che il form diventa non controllato
- [ ] Sai perché `useFormStatus` va in un componente figlio
- [ ] Usi `useOptimistic` e sai cosa succede quando l'azione fallisce
- [ ] Sai scegliere fra `useTransition` e `useDeferredValue`
- [ ] Usi `useId` e sai perché `Math.random()` romperebbe l'idratazione
- [ ] Rimetti il focus dopo una navigazione in una SPA
- [ ] Conosci la priorità delle query di Testing Library
- [ ] Sai quando serve `queryBy*` invece di `getBy*`
- [ ] Sai cosa non va testato in un componente

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| `key={indice}` su una lista che cambia | Lo stato finisce sull'elemento sbagliato | Un id stabile legato al dato |
| `useEffect` per derivare dati | Un rendering in più, e stati temporaneamente disallineati | Calcolare durante il rendering |
| `useEffect` per reagire a un evento | La logica è lontana dal fatto che l'ha causata | Nel gestore dell'evento |
| `useEffect` per azzerare lo stato | Un rendering con i dati vecchi | Cambiare la `key` |
| `useEffect` + `fetch` a mano | Manca cache, deduplicazione, ritentativi, invalidazione | TanStack Query |
| Dipendenze omesse in `useEffect` | L'effetto usa valori vecchi | Dichiararle tutte; `exhaustive-deps` attivo |
| `// eslint-disable exhaustive-deps` | Silenzia un avviso che aveva ragione | Ristrutturare: `useCallback`, ref, o spostare la logica |
| Effetto senza pulizia | Sottoscrizioni e timer duplicati a ogni rimontaggio | `return () => …` sempre |
| Oggetto nelle dipendenze di un effetto | Nuovo a ogni rendering: ciclo infinito | Dipendere dai primitivi, o spostare fuori |
| `setState` con l'oggetto modificato | React confronta per identità: non ridisegna | Creare un oggetto nuovo |
| `setState(conteggio + 1)` più volte | Usa il valore catturato: un solo incremento | Forma funzionale |
| Stato ridondante calcolabile | Due fonti che si desincronizzano | Calcolare durante il rendering |
| Stato in cima quando serve in basso | Ridisegna mezza applicazione a ogni digitazione | Abbassarlo nel componente che lo usa |
| Context per lo stato del server | Nessuna cache, nessuna deduplicazione, rendering a cascata | TanStack Query |
| Valore di Context non memoizzato | Ogni consumatore si ridisegna a ogni rendering del provider | `useMemo` |
| Un Context unico per tutto | Cambia una parte, si ridisegna chi legge le altre | Contesti separati per frequenza |
| `memo` senza `useCallback` sulle prop funzione | Il confronto vede sempre props diverse: solo costo | Entrambi, o nessuno dei due |
| `useMemo` su un calcolo banale | Il confronto delle dipendenze costa più del calcolo | Calcolare e basta |
| Un solo Error Boundary attorno all'app | Qualunque errore svuota lo schermo | Boundary per sezione |
| Ref letto o scritto nel rendering | Rompe la purezza e il rendering concorrente | Negli effetti e nei gestori |
| `<div onClick>` come pulsante | Nessun ruolo, nessuna risposta alla tastiera | `<button type="button">` |
| Icona senza nome accessibile | Lo screen reader annuncia solo "pulsante" | `aria-label`, o testo `sr-only` |
| Nessun focus dopo la navigazione | Chi usa lo screen reader non sa che la pagina è cambiata | Focus sul titolo + live region |
| `getByTestId` come prima scelta | Non è ciò che l'utente percepisce | `getByRole`, e se manca aggiungere l'etichetta |
| Test sullo stato interno | Si rompono a ogni refactoring | Testare il comportamento osservabile |

---

## Troubleshooting rapido

**"Too many re-renders. React limits the number of renders"**
- Causa: `setState` chiamato durante il rendering — spesso `onClick={salva()}` invece di `onClick={salva}`
- Fix: passare la funzione, non il risultato della chiamata

**Un `useEffect` va in ciclo infinito**
- Causa: una dipendenza è un oggetto, un array o una funzione ricreata a ogni rendering
- Fix: dipendere dai primitivi, spostare la costante fuori dal componente, o `useCallback`

**Lo stato non si aggiorna subito dopo `setState`**
- Causa: non è un bug — la variabile è il valore catturato da questo rendering
- Fix: usare il nuovo valore nell'effetto, o la forma funzionale

**"Cannot update a component while rendering a different component"**
- Causa: `setState` di un altro componente durante il rendering
- Fix: spostarlo in un effetto o in un gestore di eventi

**Il campo di input non si modifica**
- Causa: `value` senza `onChange`
- Fix: aggiungere `onChange`, o usare `defaultValue`, o `readOnly`

**"A component is changing an uncontrolled input to be controlled"**
- Causa: il valore iniziale è `undefined` e poi diventa una stringa
- Fix: inizializzare con `''`

**Lo stato di una riga finisce su un'altra dopo un'eliminazione**
- Causa: `key={indice}`
- Fix: un id stabile

**Il componente si ridisegna anche con `memo`**
- Causa: una prop oggetto, array o funzione è nuova a ogni rendering
- Fix: `useCallback`/`useMemo`, o passare primitivi, o composizione con `children`

**L'effetto si esegue due volte in sviluppo**
- Causa: `StrictMode`, ed è voluto
- Fix: rendere l'effetto idempotente con la pulizia. Non rimuovere `StrictMode`

**"Rendered more hooks than during the previous render"**
- Causa: un hook dentro un `if` o un ciclo
- Fix: gli hook al livello superiore, sempre nello stesso ordine

**"Objects are not valid as a React child"**
- Causa: si sta disegnando un oggetto invece di una stringa
- Fix: la proprietà giusta, o `JSON.stringify` per il debug

**`useContext` restituisce il valore predefinito invece di quello atteso**
- Causa: il componente è fuori dal Provider
- Fix: verificare l'albero; un contesto senza valore predefinito e con un errore esplicito lo rende evidente

**Il focus si perde dopo un aggiornamento della lista**
- Causa: l'elemento con il focus è stato rimosso dal DOM
- Fix: ripristinare il focus su un ancoraggio stabile in un effetto

**L'idratazione fallisce: "Hydration failed because the server rendered HTML didn't match"**
- Causa: `Math.random()`, `Date.now()`, o `typeof window` nel rendering
- Fix: `useId` per gli identificativi; i valori dipendenti dal client in un effetto

**React Query rifà la richiesta di continuo**
- Causa: la `queryKey` contiene un oggetto ricreato a ogni rendering
- Fix: memoizzare la chiave, o costruirla da primitivi

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_08_vue.md` | Lo stesso problema risolto con la reattività fine invece del rendering |
| `tutorial_09_svelte.md` | Un compilatore invece di una libreria a runtime |
| `tutorial_15_testing_web.md` | Testing Library, MSW e Playwright in profondità |
| `tutorial_17_performance_web.md` | Core Web Vitals, INP e il costo reale del JavaScript |
| `tutorial_21_rsc_server_driven_ui.md` | Server Components: dove `use` e le Actions danno il meglio |
| `tutorial_25_nextjs.md` | React con routing, rendering sul server e deploy |

---

## Risorse di riferimento

**Documentazione:**
- [react.dev](https://react.dev/) — la documentazione riscritta, con il modello mentale spiegato bene
- [react.dev — You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect) — da leggere per intero
- [TanStack Query](https://tanstack.com/query/latest) — guida e riferimento
- [React Router](https://reactrouter.com/) — versione 7
- [Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

**Approfondimenti:**
- [Dan Abramov — A Complete Guide to useEffect](https://overreacted.io/a-complete-guide-to-useeffect/) — perché gli effetti funzionano così
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/patterns/) — i pattern dei componenti, con il comportamento atteso
- [Josh Comeau — The Interactive Guide to Rendering in React](https://www.joshwcomeau.com/react/why-react-re-renders/)

**Strumenti:**
- [React DevTools](https://react.dev/learn/react-developer-tools) — Profiler e "why did this render"
- [Radix UI](https://www.radix-ui.com/primitives) — componenti accessibili senza stile
- [React Aria](https://react-spectrum.adobe.com/react-aria/) — hook per il comportamento accessibile
- [eslint-plugin-react-hooks](https://www.npmjs.com/package/eslint-plugin-react-hooks) — le regole degli hook
- [eslint-plugin-jsx-a11y](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y)

---

> **Fine del Tutorial 07 — React**
>
> Prossimo tutorial: `tutorial_08_vue.md`

