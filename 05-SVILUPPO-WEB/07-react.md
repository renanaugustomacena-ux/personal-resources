---
corso: "Sviluppo Web"
fase: "3 — Framework Frontend"
modulo: "07"
titolo: "React"
versione: "React 19"
livello: "Intermedio"
prerequisiti:
  - "04 — JavaScript Fondamenti"
  - "06 — TypeScript"
obiettivi:
  - "Costruire applicazioni con componenti funzionali e hooks"
  - "Gestire stato con useState, useReducer e context"
  - "Implementare data fetching con React Server Components e Suspense"
  - "Ottimizzare performance con memo, useMemo e useCallback"
  - "Utilizzare React Router per navigazione client-side"
  - "Testare componenti con React Testing Library"
tag: [React, hooks, RSC, Suspense, stato, React-Router, testing]
---

# React — Guida Completa

> **Modulo 07** · **Aggiornamento:** 2026-05-24 · **Versione:** React 19

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [JavaScript Fondamenti](04-javascript-fondamenti.md), [TypeScript](06-typescript.md)
>
> Al termine di questo modulo saprai:
> 1. Costruire applicazioni con componenti funzionali e hooks
> 2. Gestire stato con useState, useReducer e context
> 3. Implementare data fetching con React Server Components e Suspense
> 4. Ottimizzare performance con memo, useMemo e useCallback
> 5. Utilizzare React Router per navigazione client-side
> 6. Testare componenti con React Testing Library
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio

## Idee guida
1. **Server Components + Suspense > Client-only.** RSC default in Next 15.
2. **`use` hook: read promise/context.**
3. **`useEffect` quasi sempre code smell.** Server-side fetch + Action piu corretto.
4. **TanStack Query > Redux per server state.** Redux per state UI complex only.


## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti](#fondamenti)
3. [Hooks](#hooks)
4. [Gestione Stato](#gestione-stato)
5. [Routing](#routing)
6. [Forms](#forms)
7. [Fetch e Server State](#fetch-e-server-state)
8. [Styling](#styling)
9. [Testing](#testing)
10. [Performance](#performance)
11. [Next.js (Panoramica)](#nextjs-panoramica)
12. [Best Practices](#best-practices)

---

## Panoramica

React è una libreria JavaScript open source per la costruzione di interfacce utente, sviluppata originariamente da Meta (Facebook) nel 2013. A differenza di framework monolitici come Angular, React si concentra esclusivamente sul layer di presentazione — la "V" nel pattern MVC — lasciando allo sviluppatore la libertà di scegliere le soluzioni migliori per routing, gestione dello stato e comunicazione con il server. Questa filosofia modulare ha reso React la libreria front-end più adottata al mondo, con un ecosistema vasto e una community attivissima.

### Filosofia di React

La filosofia alla base di React si fonda su tre pilastri fondamentali.

**Approccio dichiarativo.** In React si descrive *come* l'interfaccia deve apparire per un dato stato, non *quali passi* eseguire per aggiornarla. Quando lo stato cambia, React calcola automaticamente le modifiche necessarie al DOM. Questo approccio riduce drasticamente la complessità del codice rispetto alla manipolazione imperativa del DOM tipica di jQuery e del JavaScript vanilla.

**Architettura a componenti.** L'intera interfaccia utente è suddivisa in componenti riutilizzabili e indipendenti. Ogni componente incapsula la propria logica, il proprio markup (tramite JSX) e spesso il proprio stile. I componenti si compongono fra loro come mattoncini, formando gerarchie complesse a partire da elementi semplici. Un pulsante, un campo di input, un form, una pagina intera — tutto è un componente.

**Virtual DOM.** React mantiene una rappresentazione virtuale del DOM in memoria. Quando lo stato di un componente cambia, React genera un nuovo Virtual DOM, lo confronta con il precedente tramite un algoritmo di **reconciliation** (diffing) e applica al DOM reale solo le modifiche strettamente necessarie. Questo meccanismo garantisce aggiornamenti efficienti senza costringere lo sviluppatore a ottimizzare manualmente le manipolazioni del DOM.

### Panoramica dell'ecosistema

L'ecosistema React è maturo e ricco di librerie consolidate. Per il routing si utilizza quasi universalmente **React Router**. Per la gestione dello stato globale le scelte principali sono **Zustand** (leggero e moderno), **Redux Toolkit** (per applicazioni enterprise complesse) e **Jotai** o **Recoil** per approcci atomici. Per la gestione dello stato server si è affermato **TanStack Query** (ex React Query). Per i form, **React Hook Form** con **Zod** rappresenta lo standard de facto. Per lo styling, **Tailwind CSS** è ormai la scelta dominante, affiancato da CSS Modules e soluzioni CSS-in-JS come **styled-components**.

### Create React App vs Vite vs Next.js

**Create React App (CRA)** è stato per anni lo strumento ufficiale per avviare un progetto React. Basato su Webpack, configura automaticamente Babel, ESLint e un dev server. Tuttavia, CRA è ormai considerato **deprecato** dalla stessa documentazione ufficiale di React. I tempi di build e di avvio del dev server sono lenti, la configurazione è rigida e la manutenzione del progetto è stata sostanzialmente abbandonata.

**Vite** è il sostituto moderno consigliato per le single-page application. Creato da Evan You (autore di Vue), Vite utilizza **esbuild** per il pre-bundling delle dipendenze e **Rollup** per il build di produzione. L'avvio del dev server è quasi istantaneo grazie al supporto nativo degli ES Modules, e l'Hot Module Replacement (HMR) è fulmineo. Per creare un nuovo progetto React con Vite basta eseguire `npm create vite@latest mio-progetto -- --template react-ts`.

**Next.js** è un framework full-stack costruito su React, sviluppato da Vercel. Offre rendering lato server (SSR), generazione statica (SSG), Server Components, routing basato sul file system, API routes e molto altro. Se il progetto richiede SEO, rendering server-side o una struttura full-stack, Next.js è la scelta raccomandata dalla stessa documentazione ufficiale di React.

---

## Fondamenti

### JSX

JSX (JavaScript XML) è un'estensione sintattica di JavaScript che permette di scrivere markup direttamente all'interno del codice JavaScript. JSX non è HTML — viene trasformato in chiamate `React.createElement()` dal compilatore (Babel o SWC). Questa trasformazione avviene a build time, quindi JSX non ha alcun costo a runtime.

**Sintassi base e espressioni.** All'interno di JSX si possono inserire espressioni JavaScript racchiudendole in parentesi graffe `{}`. Qualsiasi espressione valida è ammessa: variabili, operazioni aritmetiche, chiamate a funzione, operatori ternari.

```jsx
function Benvenuto({ nome, messaggi }) {
  const dataCorrente = new Date().toLocaleDateString("it-IT");

  return (
    <div>
      <h1>Ciao, {nome}!</h1>
      <p>Oggi è il {dataCorrente}</p>
      <p>Hai {messaggi.length} {messaggi.length === 1 ? "messaggio" : "messaggi"}</p>
    </div>
  );
}
```

**Rendering condizionale.** Esistono diverse strategie per rendere condizionalmente il contenuto in JSX. L'operatore ternario `condizione ? elementoA : elementoB` è il più comune. Per mostrare o nascondere un elemento senza alternativa, si usa l'operatore logico AND: `condizione && <Elemento />`. Attenzione con valori falsy numerici — `0 && <Elemento />` renderizza `0`, non nulla. In questi casi conviene scrivere `conteggio > 0 && <Elemento />`.

```jsx
function Profilo({ utente, isAdmin }) {
  return (
    <div>
      {utente ? <p>Benvenuto, {utente.nome}</p> : <p>Effettua il login</p>}
      {isAdmin && <button>Pannello Admin</button>}
    </div>
  );
}
```

**Liste e keys.** Per renderizzare una lista di elementi si usa il metodo `map()` su un array. Ogni elemento nella lista **deve** avere una prop `key` univoca e stabile. La key aiuta React a identificare quali elementi sono cambiati, aggiunti o rimossi durante la reconciliation. Non usare mai l'indice dell'array come key se la lista può essere riordinata o modificata — farlo causa bug sottili e problemi di performance.

```jsx
function ListaUtenti({ utenti }) {
  return (
    <ul>
      {utenti.map((utente) => (
        <li key={utente.id}>
          {utente.nome} — {utente.email}
        </li>
      ))}
    </ul>
  );
}
```

**Fragments.** Un componente React deve restituire un singolo elemento radice. Quando non si vuole aggiungere un nodo DOM extra, si usano i **Fragment**: `<React.Fragment>` o la sintassi abbreviata `<>...</>`. I Fragment con la sintassi completa accettano la prop `key`, utile quando si rendono liste.

```jsx
function InfoUtente({ nome, email }) {
  return (
    <>
      <dt>{nome}</dt>
      <dd>{email}</dd>
    </>
  );
}
```

**Differenze tra JSX e HTML.** JSX somiglia a HTML ma presenta differenze importanti. L'attributo `class` diventa `className`. L'attributo `for` (nelle label) diventa `htmlFor`. Lo stile inline è un oggetto JavaScript con proprietà in camelCase: `style={{ backgroundColor: "red", fontSize: "16px" }}`. Tutti i tag devono essere chiusi, inclusi quelli self-closing come `<img />`, `<input />`, `<br />`. Gli attributi degli eventi usano il camelCase: `onClick`, `onChange`, `onSubmit` anziché `onclick`, `onchange`, `onsubmit`.

### Componenti

In React moderno, i componenti sono **funzioni JavaScript** che restituiscono JSX. I componenti classe esistono ancora ma sono considerati legacy — tutto il codice nuovo dovrebbe usare componenti funzione con hooks.

**Function components.** Un function component è semplicemente una funzione che accetta un oggetto `props` come argomento e restituisce JSX. Il nome del componente deve iniziare con lettera maiuscola — è così che React distingue i componenti dai normali tag HTML.

```jsx
function Card({ titolo, descrizione, children }) {
  return (
    <div className="card">
      <h2>{titolo}</h2>
      <p>{descrizione}</p>
      <div className="card-body">{children}</div>
    </div>
  );
}
```

**Props.** Le props (abbreviazione di properties) rappresentano l'interfaccia pubblica di un componente. Sono di sola lettura — un componente non deve mai modificare le proprie props. Le props si passano come attributi JSX e si ricevono come oggetto nel componente. Il destructuring nell'argomento della funzione è lo standard moderno. Con TypeScript si definisce un'interfaccia o un type per tipizzare le props.

```tsx
interface ButtonProps {
  label: string;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
  onClick: () => void;
}

function Button({ label, variant = "primary", disabled = false, onClick }: ButtonProps) {
  return (
    <button
      className={`btn btn-${variant}`}
      disabled={disabled}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
```

La prop speciale `children` rappresenta il contenuto inserito tra i tag di apertura e chiusura del componente. È il meccanismo fondamentale per la **composizione** — il pattern più potente di React.

**Composizione dei componenti.** La composizione consiste nel costruire componenti complessi combinando componenti più semplici. Questo approccio è preferibile all'ereditarietà. Un componente `Layout` può contenere `Header`, `Sidebar` e `Footer`. Una `Card` può contenere qualsiasi contenuto tramite `children`. Il pattern "slot" permette di passare più aree di contenuto tramite props con nomi diversi.

```jsx
function Layout({ sidebar, children }) {
  return (
    <div className="layout">
      <Header />
      <div className="layout-body">
        <aside>{sidebar}</aside>
        <main>{children}</main>
      </div>
      <Footer />
    </div>
  );
}

// Utilizzo
<Layout sidebar={<NavigazioneMenu />}>
  <h1>Contenuto principale</h1>
  <p>Qui va il corpo della pagina.</p>
</Layout>
```

### State e Lifecycle

Lo **state** (stato) è un dato interno al componente che può cambiare nel tempo. Quando lo stato cambia, React ri-renderizza il componente e i suoi figli. A differenza delle props, lo stato è gestito internamente dal componente stesso.

**useState.** L'hook `useState` è il modo fondamentale per aggiungere stato a un function component. Restituisce un array con due elementi: il valore corrente dello stato e una funzione per aggiornarlo.

```jsx
import { useState } from "react";

function Contatore() {
  const [conteggio, setConteggio] = useState(0);

  return (
    <div>
      <p>Conteggio: {conteggio}</p>
      <button onClick={() => setConteggio(conteggio + 1)}>Incrementa</button>
      <button onClick={() => setConteggio(0)}>Reset</button>
    </div>
  );
}
```

**Aggiornamenti dello stato.** Gli aggiornamenti dello stato in React sono **asincroni** e vengono raggruppati in **batch** per efficienza. Se si deve calcolare il nuovo stato basandosi sul valore precedente, bisogna usare la forma funzionale del setter: `setConteggio(prev => prev + 1)`. Questo garantisce che il valore precedente sia sempre quello corretto, anche quando più aggiornamenti avvengono nello stesso ciclo di rendering.

```jsx
function ContatoreVeloce() {
  const [conteggio, setConteggio] = useState(0);

  const incrementaTre = () => {
    // Sbagliato: tutti e tre leggono lo stesso valore di conteggio
    // setConteggio(conteggio + 1);
    // setConteggio(conteggio + 1);
    // setConteggio(conteggio + 1);

    // Corretto: ogni aggiornamento parte dal valore precedente
    setConteggio((prev) => prev + 1);
    setConteggio((prev) => prev + 1);
    setConteggio((prev) => prev + 1);
  };

  return <button onClick={incrementaTre}>+3 (attuale: {conteggio})</button>;
}
```

**Ciclo di vita del componente.** In React funzionale, il ciclo di vita si gestisce tramite `useEffect`. Un componente attraversa tre fasi: **mount** (inserimento nel DOM), **update** (ri-rendering a seguito di cambiamenti di props o stato) e **unmount** (rimozione dal DOM). L'hook `useEffect` può eseguire codice in ciascuna di queste fasi, come vedremo nella sezione dedicata agli hooks.

---

## Hooks

Gli hooks sono funzioni speciali introdotte in React 16.8 che permettono di aggiungere stato, effetti collaterali e altre funzionalità ai function component. Prima degli hooks, queste funzionalità erano disponibili solo nei componenti classe.

### Hook Base

**useState** gestisce lo stato locale del componente. Può contenere qualsiasi tipo di valore: primitivi, oggetti, array. Per lo stato oggetto e array, è fondamentale creare sempre un **nuovo riferimento** quando si aggiorna — React usa l'uguaglianza referenziale per decidere se ri-renderizzare.

```jsx
// Stato primitivo
const [nome, setNome] = useState("");

// Stato oggetto — spread per creare nuovo oggetto
const [utente, setUtente] = useState({ nome: "", email: "" });
const aggiornaNome = (nuovoNome) => {
  setUtente((prev) => ({ ...prev, nome: nuovoNome }));
};

// Stato array — metodi immutabili
const [items, setItems] = useState([]);
const aggiungiItem = (item) => setItems((prev) => [...prev, item]);
const rimuoviItem = (id) => setItems((prev) => prev.filter((item) => item.id !== id));
const aggiornaItem = (id, dati) =>
  setItems((prev) =>
    prev.map((item) => (item.id === id ? { ...item, ...dati } : item))
  );
```

**useEffect** gestisce gli **effetti collaterali**: chiamate API, sottoscrizioni, manipolazioni del DOM, timer. Accetta due argomenti: una funzione effetto e un array di dipendenze opzionale. La funzione effetto può restituire una funzione di **cleanup** che viene eseguita prima del prossimo effetto e allo smontaggio del componente.

```jsx
import { useState, useEffect } from "react";

function ProfiloUtente({ userId }) {
  const [utente, setUtente] = useState(null);
  const [caricamento, setCaricamento] = useState(true);

  useEffect(() => {
    let annullato = false;

    async function caricaUtente() {
      setCaricamento(true);
      try {
        const risposta = await fetch(`/api/utenti/${userId}`);
        const dati = await risposta.json();
        if (!annullato) {
          setUtente(dati);
        }
      } finally {
        if (!annullato) {
          setCaricamento(false);
        }
      }
    }

    caricaUtente();

    // Cleanup: evita aggiornamenti di stato su componente smontato
    return () => {
      annullato = true;
    };
  }, [userId]); // Si riesegue solo quando userId cambia

  if (caricamento) return <p>Caricamento...</p>;
  if (!utente) return <p>Utente non trovato</p>;
  return <h1>{utente.nome}</h1>;
}
```

Le regole dell'array di dipendenze sono precise: **array vuoto `[]`** significa che l'effetto viene eseguito solo al mount (e il cleanup allo unmount); **array con valori `[a, b]`** significa che l'effetto viene rieseguito quando uno dei valori cambia; **nessun array** significa che l'effetto viene eseguito a ogni render (da evitare nella maggior parte dei casi).

**useContext** consente di consumare un valore da un Context senza prop drilling. Il Context è il meccanismo di React per condividere dati attraverso l'albero dei componenti senza passarli manualmente ad ogni livello tramite props.

```jsx
import { createContext, useContext, useState } from "react";

const TemaContext = createContext("chiaro");

function TemaProvider({ children }) {
  const [tema, setTema] = useState("chiaro");
  const toggleTema = () => setTema((prev) => (prev === "chiaro" ? "scuro" : "chiaro"));

  return (
    <TemaContext.Provider value={{ tema, toggleTema }}>
      {children}
    </TemaContext.Provider>
  );
}

function useTema() {
  const contesto = useContext(TemaContext);
  if (!contesto) throw new Error("useTema deve essere usato dentro TemaProvider");
  return contesto;
}

function BottoneTema() {
  const { tema, toggleTema } = useTema();
  return <button onClick={toggleTema}>Tema attuale: {tema}</button>;
}
```

**useRef** restituisce un oggetto mutabile `{ current: valoreIniziale }` che persiste per l'intera vita del componente. Ha due usi principali: accedere direttamente agli elementi del DOM e memorizzare valori mutabili che non devono causare un re-render quando cambiano (a differenza dello stato).

```jsx
import { useRef, useEffect } from "react";

function InputConFocus() {
  const inputRef = useRef(null);
  const renderCountRef = useRef(0);

  useEffect(() => {
    // Accesso diretto al DOM
    inputRef.current.focus();
  }, []);

  useEffect(() => {
    // Valore mutabile che non causa re-render
    renderCountRef.current += 1;
  });

  return <input ref={inputRef} placeholder="Questo campo ha il focus automatico" />;
}
```

Per passare un ref a un componente figlio si usa `forwardRef` (oppure, a partire da React 19, si può ricevere `ref` direttamente come prop):

```jsx
import { forwardRef } from "react";

const InputPersonalizzato = forwardRef(function InputPersonalizzato({ label, ...props }, ref) {
  return (
    <label>
      {label}
      <input ref={ref} {...props} />
    </label>
  );
});
```

### Hook Avanzati

**useReducer** è l'alternativa a `useState` per logiche di stato complesse. Funziona come Redux in miniatura: si definisce una funzione reducer che, dato lo stato corrente e un'azione, restituisce il nuovo stato. È particolarmente utile quando lo stato ha molti sotto-valori correlati o quando la logica di aggiornamento è articolata.

```jsx
import { useReducer } from "react";

const statoIniziale = { conteggio: 0, passo: 1 };

function reducer(stato, azione) {
  switch (azione.type) {
    case "incrementa":
      return { ...stato, conteggio: stato.conteggio + stato.passo };
    case "decrementa":
      return { ...stato, conteggio: stato.conteggio - stato.passo };
    case "imposta_passo":
      return { ...stato, passo: azione.payload };
    case "reset":
      return statoIniziale;
    default:
      throw new Error(`Azione sconosciuta: ${azione.type}`);
  }
}

function ContatoreAvanzato() {
  const [stato, dispatch] = useReducer(reducer, statoIniziale);

  return (
    <div>
      <p>Conteggio: {stato.conteggio} (passo: {stato.passo})</p>
      <button onClick={() => dispatch({ type: "incrementa" })}>+</button>
      <button onClick={() => dispatch({ type: "decrementa" })}>-</button>
      <input
        type="number"
        value={stato.passo}
        onChange={(e) =>
          dispatch({ type: "imposta_passo", payload: Number(e.target.value) })
        }
      />
      <button onClick={() => dispatch({ type: "reset" })}>Reset</button>
    </div>
  );
}
```

**useMemo** memorizza il risultato di un calcolo costoso, ricalcolandolo solo quando le dipendenze cambiano. Non usarlo ovunque — è un'ottimizzazione che ha un suo costo (memoria e confronto delle dipendenze). Riservalo a calcoli genuinamente pesanti o a oggetti/array che servono come dipendenze stabili per altri hook o componenti memoizzati.

```jsx
import { useMemo } from "react";

function ListaFiltrata({ items, filtro }) {
  const itemsFiltrati = useMemo(() => {
    return items.filter((item) =>
      item.nome.toLowerCase().includes(filtro.toLowerCase())
    );
  }, [items, filtro]);

  return (
    <ul>
      {itemsFiltrati.map((item) => (
        <li key={item.id}>{item.nome}</li>
      ))}
    </ul>
  );
}
```

**useCallback** memorizza una funzione, restituendo la stessa referenza finché le dipendenze non cambiano. È utile quando si passano callback a componenti figli ottimizzati con `React.memo`, evitando ri-render inutili causati da nuove referenze di funzione a ogni render.

```jsx
import { useCallback, useState } from "react";

function ComponenteGenitore() {
  const [conteggio, setConteggio] = useState(0);
  const [testo, setTesto] = useState("");

  // Senza useCallback, questa funzione viene ricreata a ogni render
  const gestisciClick = useCallback(() => {
    setConteggio((prev) => prev + 1);
  }, []);

  return (
    <div>
      <input value={testo} onChange={(e) => setTesto(e.target.value)} />
      <BottoneMemoizzato onClick={gestisciClick} conteggio={conteggio} />
    </div>
  );
}

const BottoneMemoizzato = React.memo(function BottoneMemoizzato({ onClick, conteggio }) {
  console.log("BottoneMemoizzato renderizzato");
  return <button onClick={onClick}>Cliccato {conteggio} volte</button>;
});
```

**useId** genera un identificatore univoco stabile tra server e client, utile per associare label e input accessibili senza rischio di collisioni.

```jsx
import { useId } from "react";

function CampoForm({ label }) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id}>{label}</label>
      <input id={id} />
    </div>
  );
}
```

**useDeferredValue e useTransition** sono hook per le funzionalità di rendering concorrente di React. `useTransition` permette di marcare un aggiornamento di stato come non urgente, mantenendo l'interfaccia reattiva mentre avviene una transizione costosa. `useDeferredValue` accetta un valore e restituisce una versione "ritardata" che può restare indietro rispetto all'ultima.

```jsx
import { useState, useTransition, useDeferredValue } from "react";

function RicercaConcorrente() {
  const [query, setQuery] = useState("");
  const [isPending, startTransition] = useTransition();

  const handleChange = (e) => {
    const valore = e.target.value;
    // Aggiornamento urgente: campo di input
    setQuery(valore);
  };

  // La lista usa il valore differito, permettendo all'input di restare fluido
  const deferredQuery = useDeferredValue(query);

  return (
    <div>
      <input value={query} onChange={handleChange} placeholder="Cerca..." />
      {isPending && <span>Aggiornamento in corso...</span>}
      <ListaRisultati query={deferredQuery} />
    </div>
  );
}
```

### Custom Hooks

I **custom hooks** sono funzioni JavaScript il cui nome inizia con `use` che possono chiamare altri hooks. Permettono di estrarre e riutilizzare logica stateful tra componenti diversi. Non condividono stato — ogni componente che usa un custom hook ha la propria istanza di stato indipendente.

```jsx
// useLocalStorage — stato sincronizzato con localStorage
function useLocalStorage(chiave, valoreIniziale) {
  const [valore, setValore] = useState(() => {
    try {
      const item = window.localStorage.getItem(chiave);
      return item ? JSON.parse(item) : valoreIniziale;
    } catch {
      return valoreIniziale;
    }
  });

  useEffect(() => {
    window.localStorage.setItem(chiave, JSON.stringify(valore));
  }, [chiave, valore]);

  return [valore, setValore];
}

// useFetch — fetch con gestione di caricamento ed errori
function useFetch(url) {
  const [dati, setDati] = useState(null);
  const [errore, setErrore] = useState(null);
  const [caricamento, setCaricamento] = useState(true);

  useEffect(() => {
    let annullato = false;
    setCaricamento(true);

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`Errore HTTP: ${res.status}`);
        return res.json();
      })
      .then((dati) => {
        if (!annullato) setDati(dati);
      })
      .catch((err) => {
        if (!annullato) setErrore(err);
      })
      .finally(() => {
        if (!annullato) setCaricamento(false);
      });

    return () => { annullato = true; };
  }, [url]);

  return { dati, errore, caricamento };
}

// useDebounce — valore con ritardo (debounce)
function useDebounce(valore, ritardo = 300) {
  const [valoreRitardato, setValoreRitardato] = useState(valore);

  useEffect(() => {
    const timer = setTimeout(() => setValoreRitardato(valore), ritardo);
    return () => clearTimeout(timer);
  }, [valore, ritardo]);

  return valoreRitardato;
}

// useMediaQuery — reattività a media query CSS
function useMediaQuery(query) {
  const [corrisponde, setCorrisponde] = useState(
    () => window.matchMedia(query).matches
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const handler = (e) => setCorrisponde(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, [query]);

  return corrisponde;
}
```

**Regole degli hooks.** Due regole inviolabili governano gli hooks: (1) chiamare gli hooks solo al livello più alto della funzione componente, mai dentro condizioni, loop o funzioni annidate; (2) chiamare gli hooks solo da function component React o da custom hooks. Queste regole esistono perché React identifica gli hooks in base all'ordine in cui vengono chiamati — un ordine diverso tra render causerebbe comportamenti imprevedibili. Il plugin ESLint `eslint-plugin-react-hooks` verifica automaticamente il rispetto di queste regole.

---

## Gestione Stato

### Context API

Il Context API è la soluzione nativa di React per condividere dati tra componenti senza prop drilling. Si crea un contesto con `createContext`, si fornisce un valore tramite il componente `Provider` e si consuma con l'hook `useContext`.

Il Context è ideale per dati che cambiano raramente e sono necessari a molti componenti: tema (chiaro/scuro), locale/lingua, dati di autenticazione, preferenze dell'utente. Non è adatto per stato che cambia frequentemente (come i dati di un form) perché ogni modifica del valore del Provider causa il ri-render di **tutti** i consumatori, anche se usano solo una parte del valore.

```jsx
import { createContext, useContext, useState, useCallback } from "react";

// Contesto di autenticazione
const AuthContext = createContext(null);

function AuthProvider({ children }) {
  const [utente, setUtente] = useState(null);

  const login = useCallback(async (credenziali) => {
    const risposta = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credenziali),
    });
    const dati = await risposta.json();
    setUtente(dati.utente);
  }, []);

  const logout = useCallback(() => {
    setUtente(null);
  }, []);

  return (
    <AuthContext.Provider value={{ utente, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

function useAuth() {
  const contesto = useContext(AuthContext);
  if (!contesto) throw new Error("useAuth deve essere usato dentro AuthProvider");
  return contesto;
}
```

**Considerazioni sulla performance.** Per mitigare i re-render non necessari, si possono separare i contesti (un contesto per il valore, un altro per il dispatch), memoizzare il valore del Provider con `useMemo` e suddividere contesti grandi in contesti più piccoli e specifici.

### Librerie di State Management

**Zustand** è la libreria raccomandata per la maggior parte dei progetti React moderni. È minimale (meno di 1 KB gzippato), non richiede Provider, supporta middleware (persist, devtools, immer) e offre un'API estremamente semplice basata su hooks.

```jsx
import { create } from "zustand";

const useCarrelloStore = create((set) => ({
  articoli: [],
  aggiungiArticolo: (articolo) =>
    set((stato) => ({ articoli: [...stato.articoli, articolo] })),
  rimuoviArticolo: (id) =>
    set((stato) => ({ articoli: stato.articoli.filter((a) => a.id !== id) })),
  svuota: () => set({ articoli: [] }),
  totale: () => 0, // calcolato tramite selector
}));

// Utilizzo nel componente — re-render solo quando articoli cambia
function BadgeCarrello() {
  const conteggio = useCarrelloStore((stato) => stato.articoli.length);
  return <span className="badge">{conteggio}</span>;
}
```

**Redux Toolkit (RTK)** è la scelta appropriata per applicazioni enterprise di grandi dimensioni con logica di stato complessa, molti sviluppatori nel team e necessità di debug avanzato con Redux DevTools. RTK semplifica enormemente Redux classico grazie a `createSlice`, `createAsyncThunk` e l'integrazione con Immer per aggiornamenti mutabili dello stato.

**Jotai e Recoil** propongono un approccio **atomico** alla gestione dello stato: ogni pezzo di stato è un "atomo" indipendente, e i componenti si sottoscrivono solo agli atomi che usano, minimizzando i re-render. Jotai è più leggero e moderno, Recoil è il progetto originale di Meta (attualmente meno mantenuto).

**TanStack Query** non è una libreria di stato generico — gestisce specificamente lo **stato server**: dati provenienti da API, caching, refetching automatico, sincronizzazione. È la soluzione consigliata per tutta la logica di fetch dati, ed è trattata in dettaglio nella sezione dedicata.

---

## Routing

React Router v6 è la libreria di routing standard per le applicazioni React a pagina singola. Fornisce un sistema di routing dichiarativo basato su componenti.

```jsx
import { BrowserRouter, Routes, Route, Link, NavLink, Outlet } from "react-router-dom";

// Layout con navigazione e area per le route figlie
function Layout() {
  return (
    <div>
      <nav>
        <NavLink to="/" className={({ isActive }) => (isActive ? "attivo" : "")}>
          Home
        </NavLink>
        <NavLink to="/prodotti">Prodotti</NavLink>
        <NavLink to="/chi-siamo">Chi siamo</NavLink>
      </nav>
      <main>
        <Outlet /> {/* Qui vengono renderizzate le route figlie */}
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="prodotti" element={<Prodotti />} />
          <Route path="prodotti/:id" element={<DettaglioProdotto />} />
          <Route path="chi-siamo" element={<ChiSiamo />} />
          <Route path="*" element={<PaginaNonTrovata />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

**Route dinamiche** usano i parametri prefissati da `:`. Il valore viene letto con l'hook `useParams`.

```jsx
import { useParams } from "react-router-dom";

function DettaglioProdotto() {
  const { id } = useParams();
  // Usa id per caricare i dati del prodotto
  return <h1>Prodotto #{id}</h1>;
}
```

**Navigazione programmatica** si esegue con l'hook `useNavigate`.

```jsx
import { useNavigate } from "react-router-dom";

function FormLogin() {
  const navigate = useNavigate();

  const gestisciSubmit = async (dati) => {
    await effettuaLogin(dati);
    navigate("/dashboard", { replace: true });
  };

  return <form onSubmit={gestisciSubmit}>{/* campi del form */}</form>;
}
```

**Route protette.** Un pattern comune per proteggere le route che richiedono autenticazione è un componente wrapper che verifica lo stato di login e reindirizza se necessario.

```jsx
import { Navigate, useLocation } from "react-router-dom";

function RouteProtetta({ children }) {
  const { utente } = useAuth();
  const location = useLocation();

  if (!utente) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

// Utilizzo nella configurazione delle route
<Route
  path="dashboard"
  element={
    <RouteProtetta>
      <Dashboard />
    </RouteProtetta>
  }
/>
```

**Data loading.** React Router v6.4+ introduce `loader` e `action` per caricare dati e gestire mutazioni a livello di route, ispirandosi a Remix. I loader vengono eseguiti prima del rendering della route, eliminando i loading spinner nei componenti.

---

## Forms

### Componenti controllati e non controllati

In React, un **componente controllato** è un input il cui valore è gestito dallo stato React. Ogni modifica dell'utente passa attraverso un handler `onChange` che aggiorna lo stato, e lo stato aggiornato viene riflesso nell'input tramite la prop `value`. Questo dà un controllo completo ma richiede più codice.

Un **componente non controllato** lascia che il DOM gestisca il valore dell'input. Si accede al valore tramite `ref` quando necessario (ad esempio al submit). È più semplice ma offre meno controllo.

### React Hook Form

**React Hook Form** è la libreria raccomandata per gestire form complessi in React. Usa un approccio non controllato internamente (per la performance) ma espone un'API che permette di lavorare come se i componenti fossero controllati. I re-render sono minimizzati perché la libreria isola le sottoscrizioni ai singoli campi.

```jsx
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

// Schema di validazione con Zod
const schemaRegistrazione = z.object({
  nome: z.string().min(2, "Il nome deve avere almeno 2 caratteri"),
  email: z.string().email("Email non valida"),
  password: z
    .string()
    .min(8, "La password deve avere almeno 8 caratteri")
    .regex(/[A-Z]/, "Deve contenere almeno una lettera maiuscola")
    .regex(/[0-9]/, "Deve contenere almeno un numero"),
  confermaPassword: z.string(),
}).refine((data) => data.password === data.confermaPassword, {
  message: "Le password non corrispondono",
  path: ["confermaPassword"],
});

type DatiRegistrazione = z.infer<typeof schemaRegistrazione>;

function FormRegistrazione() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DatiRegistrazione>({
    resolver: zodResolver(schemaRegistrazione),
  });

  const onSubmit = async (dati: DatiRegistrazione) => {
    await fetch("/api/registrazione", {
      method: "POST",
      body: JSON.stringify(dati),
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="nome">Nome</label>
        <input id="nome" {...register("nome")} />
        {errors.nome && <span className="errore">{errors.nome.message}</span>}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...register("email")} />
        {errors.email && <span className="errore">{errors.email.message}</span>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input id="password" type="password" {...register("password")} />
        {errors.password && <span className="errore">{errors.password.message}</span>}
      </div>

      <div>
        <label htmlFor="confermaPassword">Conferma Password</label>
        <input id="confermaPassword" type="password" {...register("confermaPassword")} />
        {errors.confermaPassword && (
          <span className="errore">{errors.confermaPassword.message}</span>
        )}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Registrazione..." : "Registrati"}
      </button>
    </form>
  );
}
```

**Pattern per form avanzati.** Per form multi-step si può usare uno stato che traccia il passo corrente e condividere i dati tra i passi tramite un contesto o lo stato del componente genitore. Per campi dinamici (ad esempio, aggiungere righe a una fattura), React Hook Form offre l'hook `useFieldArray` che gestisce automaticamente array di campi con operazioni di append, remove e move.

---

## Fetch e Server State

### TanStack Query (React Query)

TanStack Query rivoluziona la gestione dei dati provenienti dal server in React. Gestisce automaticamente caching, refetching in background, sincronizzazione, paginazione, gestione degli errori e deduplicazione delle richieste. Separa concettualmente lo **stato server** (dati dal backend) dallo **stato client** (dati dell'interfaccia).

```jsx
import { useQuery, useMutation, useQueryClient, QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // Dati considerati freschi per 5 minuti
      retry: 2,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
```

**useQuery** per leggere dati. Le query keys identificano univocamente ogni query e determinano quando la cache viene invalidata.

```jsx
function ListaProdotti({ categoria }) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["prodotti", { categoria }],
    queryFn: () =>
      fetch(`/api/prodotti?categoria=${categoria}`).then((res) => {
        if (!res.ok) throw new Error("Errore nel caricamento");
        return res.json();
      }),
  });

  if (isLoading) return <Skeleton />;
  if (isError) return <Errore messaggio={error.message} />;

  return (
    <div className="griglia-prodotti">
      {data.map((prodotto) => (
        <CardProdotto key={prodotto.id} prodotto={prodotto} />
      ))}
    </div>
  );
}
```

**useMutation** per creare, aggiornare o eliminare dati. Supporta aggiornamenti ottimistici, invalidazione della cache e rollback in caso di errore.

```jsx
function AggiungiProdotto() {
  const queryClient = useQueryClient();

  const mutazione = useMutation({
    mutationFn: (nuovoProdotto) =>
      fetch("/api/prodotti", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(nuovoProdotto),
      }).then((res) => res.json()),

    // Aggiornamento ottimistico
    onMutate: async (nuovoProdotto) => {
      await queryClient.cancelQueries({ queryKey: ["prodotti"] });
      const precedente = queryClient.getQueryData(["prodotti"]);
      queryClient.setQueryData(["prodotti"], (vecchi) => [
        ...vecchi,
        { ...nuovoProdotto, id: Date.now() },
      ]);
      return { precedente };
    },
    onError: (_err, _nuovo, contesto) => {
      queryClient.setQueryData(["prodotti"], contesto.precedente);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["prodotti"] });
    },
  });

  return (
    <button
      onClick={() => mutazione.mutate({ nome: "Nuovo prodotto", prezzo: 29.99 })}
      disabled={mutazione.isPending}
    >
      {mutazione.isPending ? "Salvataggio..." : "Aggiungi Prodotto"}
    </button>
  );
}
```

**Paginazione e query infinite.** TanStack Query offre `useInfiniteQuery` per implementare scroll infinito o caricamento progressivo.

```jsx
function ListaInfinita() {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ["articoli"],
    queryFn: ({ pageParam = 1 }) =>
      fetch(`/api/articoli?pagina=${pageParam}`).then((res) => res.json()),
    getNextPageParam: (ultimaPagina) => ultimaPagina.prossimaPagina ?? undefined,
    initialPageParam: 1,
  });

  return (
    <div>
      {data?.pages.map((pagina) =>
        pagina.articoli.map((articolo) => (
          <Articolo key={articolo.id} articolo={articolo} />
        ))
      )}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? "Caricamento..." : "Carica altri"}
        </button>
      )}
    </div>
  );
}
```

### Fetch Patterns

**Gestione di caricamento e errori.** Ogni fetch dovrebbe gestire tre stati: caricamento, successo e errore. Con TanStack Query questi stati sono forniti automaticamente. Senza libreria, si gestiscono manualmente con `useState`.

**Suspense per il data fetching.** React Suspense permette di dichiarare uno stato di caricamento a livello di albero dei componenti. Con TanStack Query basta abilitare l'opzione `suspense: true` nella query e avvolgere i componenti in un boundary `<Suspense fallback={<Skeleton />}>`.

**Error boundaries.** Gli error boundary catturano errori JavaScript nei componenti figli durante il rendering. Si implementano con componenti classe (l'unico caso d'uso rimasto per le classi) o con la libreria `react-error-boundary` che offre un'API funzionale.

```jsx
import { ErrorBoundary } from "react-error-boundary";
import { Suspense } from "react";

function App() {
  return (
    <ErrorBoundary fallback={<p>Qualcosa è andato storto.</p>}>
      <Suspense fallback={<p>Caricamento...</p>}>
        <ContenutoApp />
      </Suspense>
    </ErrorBoundary>
  );
}
```

---

## Styling

Esistono diversi approcci per lo styling dei componenti React, ciascuno con vantaggi e svantaggi.

**CSS Modules** offrono scope locale automatico per le classi CSS. Ogni file `.module.css` genera nomi di classe univoci a build time, eliminando il rischio di conflitti. È un approccio semplice che non richiede librerie aggiuntive.

```jsx
import styles from "./Button.module.css";

function Button({ children, variant }) {
  return (
    <button className={`${styles.button} ${styles[variant]}`}>
      {children}
    </button>
  );
}
```

**Tailwind CSS** è la soluzione utility-first dominante nell'ecosistema React. Le classi di utilità vengono composte direttamente nel JSX, eliminando il context switching tra file CSS e componenti. In combinazione con la libreria `clsx` (o `cn` con `tailwind-merge`), si possono gestire classi condizionali in modo pulito.

```jsx
import { clsx } from "clsx";

function Button({ children, variant = "primary", disabled }) {
  return (
    <button
      className={clsx(
        "rounded-lg px-4 py-2 font-semibold transition-colors",
        {
          "bg-blue-600 text-white hover:bg-blue-700": variant === "primary",
          "bg-gray-200 text-gray-800 hover:bg-gray-300": variant === "secondary",
          "opacity-50 cursor-not-allowed": disabled,
        }
      )}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
```

**styled-components e Emotion** sono librerie CSS-in-JS che permettono di definire stili come componenti JavaScript. Supportano props dinamiche, temi e SSR. Tuttavia, hanno un costo a runtime (il CSS viene generato in JavaScript) e la community si sta spostando verso soluzioni zero-runtime o utility-first.

```jsx
import styled from "styled-components";

const StyledButton = styled.button`
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 600;
  background-color: ${(props) => (props.$primary ? "#2563eb" : "#e5e7eb")};
  color: ${(props) => (props.$primary ? "white" : "#1f2937")};
`;

function Esempio() {
  return <StyledButton $primary>Bottone primario</StyledButton>;
}
```

**CSS-in-JS vs utility-first.** Il dibattito tra CSS-in-JS e Tailwind si è in gran parte risolto a favore di Tailwind per i nuovi progetti. CSS-in-JS ha il vantaggio della co-locazione stili-logica e delle API dinamiche, ma il costo a runtime e la dimensione del bundle sono svantaggi significativi. Tailwind offre performance superiori (CSS statico, purgato a build time), una developer experience eccellente e un design system implicito grazie ai valori predefiniti dello spacing, dei colori e della tipografia.

---

## Testing

Il testing in React si basa su **React Testing Library (RTL)**, una libreria che incoraggia a testare i componenti dal punto di vista dell'utente — interagendo con elementi visibili piuttosto che con dettagli implementativi. Combinata con **Vitest** come test runner, offre un'esperienza di testing veloce e moderna.

**Setup base con Vitest e React Testing Library.**

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
  },
});

// src/test/setup.ts
import "@testing-library/jest-dom/vitest";
```

**Test di rendering e interazione.**

```jsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import Contatore from "./Contatore";

describe("Contatore", () => {
  it("renderizza il conteggio iniziale", () => {
    render(<Contatore />);
    expect(screen.getByText("Conteggio: 0")).toBeInTheDocument();
  });

  it("incrementa il conteggio al click", async () => {
    const user = userEvent.setup();
    render(<Contatore />);

    await user.click(screen.getByRole("button", { name: /incrementa/i }));

    expect(screen.getByText("Conteggio: 1")).toBeInTheDocument();
  });
});
```

**Test asincroni** usano `waitFor` o `findBy*` per attendere che elementi appaiano dopo operazioni asincrone.

```jsx
import { render, screen, waitFor } from "@testing-library/react";

it("carica e mostra i dati utente", async () => {
  render(<ProfiloUtente userId="123" />);

  expect(screen.getByText("Caricamento...")).toBeInTheDocument();

  // findBy attende automaticamente (timeout di default: 1000ms)
  const nomeUtente = await screen.findByText("Mario Rossi");
  expect(nomeUtente).toBeInTheDocument();
});
```

**Mock API con MSW (Mock Service Worker).** MSW intercetta le richieste di rete a livello di service worker, permettendo di testare i componenti con dati realistici senza dipendere da un server reale.

```jsx
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

const server = setupServer(
  http.get("/api/utenti/:id", ({ params }) => {
    return HttpResponse.json({ id: params.id, nome: "Mario Rossi" });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

**Snapshot testing.** Gli snapshot catturano l'output renderizzato e lo confrontano con una versione salvata. Sono utili per rilevare cambiamenti accidentali ma vanno usati con parsimonia — snapshot troppo grandi diventano fragili e vengono aggiornati meccanicamente senza revisione. Preferisci assertion specifiche sugli elementi visibili.

---

## Performance

Le performance in React si ottimizzano su più fronti: evitare re-render non necessari, ridurre il bundle e caricare il codice in modo intelligente.

**React.memo** avvolge un componente e ne previene il re-render se le props non sono cambiate (confronto shallow). Utile per componenti pesanti o che ricevono sempre le stesse props anche quando il genitore si ri-renderizza.

```jsx
const RigaTabella = React.memo(function RigaTabella({ dati, onModifica }) {
  return (
    <tr>
      <td>{dati.nome}</td>
      <td>{dati.valore}</td>
      <td>
        <button onClick={() => onModifica(dati.id)}>Modifica</button>
      </td>
    </tr>
  );
});
```

**useMemo e useCallback** sono stati trattati nella sezione hooks. Ricorda: sono ottimizzazioni, non soluzioni universali. Profilare prima di ottimizzare — spesso un re-render "non necessario" è talmente veloce da non giustificare il costo della memoizzazione.

**Code splitting con React.lazy e Suspense.** Permette di dividere il bundle in chunk caricati on-demand. Le pagine o i componenti pesanti vengono caricati solo quando necessario, riducendo il tempo di caricamento iniziale.

```jsx
import { lazy, Suspense } from "react";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Impostazioni = lazy(() => import("./pages/Impostazioni"));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/impostazioni" element={<Impostazioni />} />
      </Routes>
    </Suspense>
  );
}
```

**Virtualizzazione con react-window.** Per liste con migliaia di elementi, il rendering di tutti i nodi DOM è proibitivo. `react-window` (o `@tanstack/react-virtual`) renderizza solo gli elementi visibili nella viewport, mantenendo la lista fluida indipendentemente dalla dimensione dei dati.

```jsx
import { FixedSizeList } from "react-window";

function ListaVirtualizzata({ items }) {
  const Riga = ({ index, style }) => (
    <div style={style} className="riga">
      {items[index].nome}
    </div>
  );

  return (
    <FixedSizeList
      height={600}
      width="100%"
      itemCount={items.length}
      itemSize={50}
    >
      {Riga}
    </FixedSizeList>
  );
}
```

**React DevTools Profiler.** Il Profiler integrato nelle React DevTools permette di registrare sessioni di rendering e analizzare quali componenti si ri-renderizzano, quanto tempo impiegano e perché. È lo strumento indispensabile per identificare colli di bottiglia prima di applicare qualsiasi ottimizzazione.

**Trappole comuni di performance.** Oggetti e array inline nelle props (`style={{}}`, `options={[]}`) creano nuovi riferimenti a ogni render, vanificando `React.memo`. Funzioni definite inline (`onClick={() => ...}`) hanno lo stesso problema. Il Context con valori che cambiano frequentemente causa re-render a cascata. Effetti senza dipendenze corrette possono generare loop infiniti. Lo stato "sollevato" troppo in alto nell'albero causa ri-render di interi sotto-alberi. La soluzione è spesso spostare lo stato il più vicino possibile a dove viene usato.

---

## Next.js (Panoramica)

Next.js è il framework React full-stack raccomandato dalla documentazione ufficiale di React. Sviluppato da Vercel, estende React con funzionalità server-side, routing basato sul file system e ottimizzazioni automatiche.

**App Router vs Pages Router.** Next.js offre due sistemi di routing. Il **Pages Router** (directory `pages/`) è il sistema originale, stabile e ben documentato. L'**App Router** (directory `app/`), introdotto nella versione 13, è il futuro di Next.js e supporta React Server Components, layout annidati, loading e error states dichiarativi. Per i nuovi progetti si raccomanda l'App Router.

**Server Components.** I React Server Components (RSC) sono componenti che vengono eseguiti esclusivamente sul server. Non vengono inclusi nel bundle JavaScript del client, possono accedere direttamente al database e al file system, e riducono drasticamente la quantità di JavaScript inviata al browser. Nell'App Router, tutti i componenti sono Server Components per default — si aggiunge la direttiva `"use client"` in cima al file solo per i componenti che necessitano di interattività (stato, effetti, event handler).

```jsx
// app/prodotti/page.tsx — Server Component (default)
async function PaginaProdotti() {
  // Accesso diretto al database — questo codice non arriva mai al client
  const prodotti = await db.prodotti.findMany();

  return (
    <div>
      <h1>Prodotti</h1>
      {prodotti.map((p) => (
        <CardProdotto key={p.id} prodotto={p} />
      ))}
    </div>
  );
}
```

**Server Actions.** Le Server Actions sono funzioni asincrone eseguite sul server, invocabili direttamente dai componenti client tramite form o chiamate dirette. Sostituiscono la necessità di creare endpoint API manuali per le mutazioni.

```jsx
// app/actions.ts
"use server";

export async function creaProdotto(formData: FormData) {
  const nome = formData.get("nome") as string;
  const prezzo = parseFloat(formData.get("prezzo") as string);

  await db.prodotti.create({ data: { nome, prezzo } });
  revalidatePath("/prodotti");
}
```

**Routing basato sul file system.** Nell'App Router, la struttura delle cartelle dentro `app/` definisce le route. `app/page.tsx` corrisponde a `/`, `app/prodotti/page.tsx` a `/prodotti`, `app/prodotti/[id]/page.tsx` a `/prodotti/:id`. File speciali come `layout.tsx`, `loading.tsx`, `error.tsx` e `not-found.tsx` gestiscono rispettivamente layout persistenti, stati di caricamento, errori e pagine 404 a livello di segmento di route.

**SSR, SSG, ISR.** Next.js supporta tre strategie di rendering. Il **Server-Side Rendering (SSR)** genera la pagina HTML a ogni richiesta — utile per contenuti personalizzati o che cambiano frequentemente. La **Static Site Generation (SSG)** pre-genera le pagine a build time — ideale per contenuti che non cambiano spesso come blog e documentazione. L'**Incremental Static Regeneration (ISR)** combina i vantaggi di entrambi: le pagine vengono generate staticamente ma possono essere rigenerate in background dopo un intervallo configurabile, senza necessità di un nuovo deploy.

**API Routes.** Next.js permette di creare endpoint API direttamente nel progetto. Nell'App Router si definiscono come `route.ts` all'interno della struttura delle cartelle, esportando funzioni per i metodi HTTP (GET, POST, PUT, DELETE). Per le semplici mutazioni, le Server Actions sono spesso preferibili.

---

## Best Practices

1. **Mantieni i componenti piccoli e focalizzati.** Ogni componente dovrebbe avere una singola responsabilità chiara. Se un componente supera le 150-200 righe, probabilmente va suddiviso. Estrai la logica riutilizzabile in custom hooks e i sotto-componenti in file separati. Componenti piccoli sono più facili da testare, comprendere e riutilizzare.

2. **Usa TypeScript in ogni progetto React.** TypeScript non è opzionale — è una necessità per qualsiasi progetto che superi il livello del prototipo. Tipizza le props con interface o type, usa i generici dove appropriato e configura `strict: true` nel `tsconfig.json`. Il costo iniziale viene ripagato enormemente dalla riduzione dei bug, dall'autocompletamento dell'IDE e dalla documentazione implicita del codice.

3. **Gestisci lo stato al livello giusto.** Lo stato locale del componente (`useState`) è sufficiente per la maggior parte dei casi. Solleva lo stato al genitore comune più vicino solo quando due componenti fratelli devono condividerlo. Usa il Context per dati globali che cambiano raramente (tema, autenticazione). Usa Zustand o Redux solo per stato complesso condiviso tra molte parti dell'applicazione. Usa TanStack Query per lo stato server — non reinventare la gestione del caching.

4. **Separa lo stato server dallo stato client.** I dati provenienti dalle API non sono stato dell'applicazione — sono una cache di dati remoti. Trattali come tali usando TanStack Query, che gestisce automaticamente caching, invalidazione, refetching e sincronizzazione. Lo stato client (interfaccia, preferenze utente, stato del form) va gestito separatamente.

5. **Preferisci la composizione all'astrazione prematura.** Non creare astrazioni finché non hai almeno tre casi d'uso concreti. Il pattern "children" e la composizione di componenti risolvono la maggior parte dei problemi di riutilizzo. Un componente `Card` generico con slot (`header`, `body`, `footer`) è quasi sempre preferibile a una `Card` con decine di props condizionali.

6. **Gestisci sempre gli stati di caricamento e di errore.** Ogni operazione asincrona (fetch, mutazioni, navigazioni) deve mostrare feedback visivo all'utente durante il caricamento e gestire gracefully gli errori. Usa Suspense e error boundary per gestire questi stati in modo dichiarativo a livello di albero dei componenti, evitando il pattern ripetitivo `if (loading)... if (error)...` in ogni componente.

7. **Testa dal punto di vista dell'utente.** Con React Testing Library, interroga gli elementi tramite ruolo (`getByRole`), testo (`getByText`) o label (`getByLabelText`) — non tramite classi CSS, ID o data attributes per il test. Simula interazioni reali con `userEvent`. Testa il comportamento visibile, non i dettagli implementativi. Un test che verifica "il bottone mostra il conteggio corretto dopo il click" è molto più robusto di uno che verifica "lo stato interno vale 5".

8. **Ottimizza le performance con consapevolezza.** Non applicare `React.memo`, `useMemo` e `useCallback` ovunque preventivamente. Usa il React DevTools Profiler per identificare i componenti che effettivamente causano problemi di performance. Applica code splitting con `React.lazy` per le route principali e i componenti pesanti. Per liste lunghe, usa la virtualizzazione. Per immagini, usa lazy loading nativo o il componente `Image` di Next.js.

9. **Struttura il progetto per funzionalità, non per tipo.** Organizza i file per dominio funzionale anziché raggruppare tutti i componenti in una cartella, tutti gli hook in un'altra e tutti i test in un'altra ancora. Una struttura come `features/prodotti/` che contiene componenti, hooks, tipi e test relativi ai prodotti è più navigabile e manutenibile di una struttura piatta con cartelle `components/`, `hooks/`, `types/`.

10. **Mantieni le dipendenze aggiornate e il codice pulito.** Aggiorna regolarmente React e le dipendenze dell'ecosistema. Usa ESLint con le regole raccomandate per React e gli hooks (`eslint-plugin-react-hooks`). Configura Prettier per la formattazione automatica. Rimuovi il codice morto e i componenti inutilizzati. Segui la documentazione ufficiale di React come fonte primaria di verità — è eccellente e costantemente aggiornata.

---

## React 19 — Novità e Funzionalità

React 19, rilasciato a dicembre 2024, rappresenta il salto evolutivo più significativo dalla versione 16.8 (che introdusse gli hooks). Questa versione introduce nuovi hook, un sistema di Actions per la gestione di operazioni asincrone, miglioramenti al rendering server-side e il React Compiler come strumento di build-time per l'ottimizzazione automatica. Comprendere queste novità è essenziale per scrivere codice React moderno e performante.

### L'hook `use`

L'hook `use` è una primitiva completamente nuova che rompe le regole tradizionali degli hooks: può essere chiamato **condizionalmente**, dentro blocchi `if`, loop e funzioni annidate. Accetta due tipi di risorse: una **Promise** o un **Context**. Quando riceve una Promise, `use` si integra con il boundary `<Suspense>` più vicino, sospendendo il rendering fino alla risoluzione della Promise e mostrando il fallback nel frattempo. Quando riceve un Context, funziona come `useContext` ma con la flessibilità di poter essere chiamato condizionalmente.

```tsx
import { use, Suspense } from "react";

// use() con Promise — integrazione nativa con Suspense
function DettaglioArticolo({ articoloPromise }: { articoloPromise: Promise<Articolo> }) {
  const articolo = use(articoloPromise);

  return (
    <article>
      <h1>{articolo.titolo}</h1>
      <p>{articolo.contenuto}</p>
    </article>
  );
}

function PaginaArticolo({ id }: { id: string }) {
  // La Promise viene creata nel componente genitore
  const articoloPromise = fetchArticolo(id);

  return (
    <Suspense fallback={<SkeletonArticolo />}>
      <DettaglioArticolo articoloPromise={articoloPromise} />
    </Suspense>
  );
}

// use() condizionale — impossibile con useContext
function Pannello({ mostraDettagli }: { mostraDettagli: boolean }) {
  if (mostraDettagli) {
    const tema = use(TemaContext);
    return <div className={tema}>Dettagli visibili</div>;
  }
  return <div>Riepilogo</div>;
}
```

La differenza fondamentale rispetto al pattern `useEffect` + `useState` per il data fetching è che `use` elimina il boilerplate degli stati di caricamento e errore nei singoli componenti, delegando la gestione al boundary `Suspense` dichiarativo nell'albero dei componenti. Il componente che chiama `use` non ha bisogno di sapere nulla sugli stati transitori — si limita a leggere il dato risolto.

**Attenzione critica:** la Promise passata a `use` deve essere creata al di fuori del componente che la consuma (nel genitore, in un loader, o in un Server Component), altrimenti verrebbe ricreata a ogni render, causando fetch infiniti. Questo vincolo architetturale spinge naturalmente verso un pattern in cui i dati vengono preparati ai livelli alti dell'albero e consumati nei livelli bassi.

### Actions e `useActionState`

Il concetto di **Actions** in React 19 è un nuovo paradigma per gestire le mutazioni di dati e le operazioni asincrone. Un'Action è una funzione asincrona che React gestisce automaticamente, tracciandone lo stato di pending, il risultato e gli eventuali errori. Le Actions si integrano con i form HTML nativi, eliminando la necessità di `event.preventDefault()` e della gestione manuale dello stato di submit.

L'hook `useActionState` (che sostituisce il precedente `useFormState` di React DOM) accetta una funzione Action e uno stato iniziale, restituendo lo stato corrente, una funzione Action wrappata da usare come `action` del form, e un booleano `isPending` che indica se l'azione è in corso.

```tsx
import { useActionState } from "react";

interface StatoForm {
  errore: string | null;
  successo: boolean;
}

async function azioneRegistrazione(
  statoPrecedente: StatoForm,
  formData: FormData
): Promise<StatoForm> {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  if (password.length < 8) {
    return { errore: "La password deve avere almeno 8 caratteri", successo: false };
  }

  try {
    await fetch("/api/registrazione", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      headers: { "Content-Type": "application/json" },
    });
    return { errore: null, successo: true };
  } catch {
    return { errore: "Errore durante la registrazione", successo: false };
  }
}

function FormRegistrazione() {
  const [stato, azioneForm, isPending] = useActionState(azioneRegistrazione, {
    errore: null,
    successo: false,
  });

  return (
    <form action={azioneForm}>
      <input name="email" type="email" required placeholder="Email" />
      <input name="password" type="password" required placeholder="Password" />
      {stato.errore && <p className="errore">{stato.errore}</p>}
      {stato.successo && <p className="successo">Registrazione completata!</p>}
      <button type="submit" disabled={isPending}>
        {isPending ? "Registrazione in corso..." : "Registrati"}
      </button>
    </form>
  );
}
```

Il vantaggio rispetto al pattern tradizionale `handleSubmit` + `useState` per `isLoading` + `useState` per `error` è evidente: `useActionState` gestisce l'intero ciclo di vita dell'azione in modo dichiarativo, riducendo drasticamente il boilerplate.

### `useOptimistic`

L'hook `useOptimistic` permette di mostrare un aggiornamento ottimistico dell'interfaccia mentre un'operazione asincrona è in corso. L'utente vede immediatamente il risultato atteso, senza attendere la risposta del server. Se l'operazione fallisce, React ripristina automaticamente lo stato precedente. Questo pattern migliora enormemente la percezione di velocità dell'applicazione.

```tsx
import { useOptimistic, useActionState } from "react";

interface Commento {
  id: string;
  testo: string;
  inviato: boolean;
}

function ListaCommenti({ commenti }: { commenti: Commento[] }) {
  const [commentiOttimistici, aggiungiOttimistico] = useOptimistic(
    commenti,
    (statoCorrente: Commento[], nuovoCommento: string) => [
      ...statoCorrente,
      {
        id: `temp-${Date.now()}`,
        testo: nuovoCommento,
        inviato: false, // Marcato come non ancora confermato dal server
      },
    ]
  );

  async function azioneInvio(_stato: unknown, formData: FormData) {
    const testo = formData.get("testo") as string;
    aggiungiOttimistico(testo); // Aggiornamento immediato dell'UI
    await inviaCommentoAlServer(testo); // Operazione server
  }

  const [, azione, isPending] = useActionState(azioneInvio, null);

  return (
    <div>
      <ul>
        {commentiOttimistici.map((c) => (
          <li key={c.id} style={{ opacity: c.inviato ? 1 : 0.6 }}>
            {c.testo} {!c.inviato && <span>(invio in corso...)</span>}
          </li>
        ))}
      </ul>
      <form action={azione}>
        <input name="testo" placeholder="Scrivi un commento..." required />
        <button type="submit" disabled={isPending}>Invia</button>
      </form>
    </div>
  );
}
```

### `useFormStatus`

L'hook `useFormStatus` è progettato per essere usato nei componenti figli di un `<form>` per accedere allo stato di submission senza prop drilling. Deve essere chiamato da un componente renderizzato all'interno di un `<form>` — non funziona se il componente è nello stesso livello del form. Restituisce un oggetto con `pending` (booleano che indica se il form è in fase di invio), `data` (il `FormData` inviato), `method` e `action`.

```tsx
import { useFormStatus } from "react-dom";

function BottoneSubmit() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? "Invio in corso..." : "Invia"}
    </button>
  );
}

function IndicatoreProgresso() {
  const { pending, data } = useFormStatus();
  if (!pending) return null;
  return (
    <div className="barra-progresso" role="status" aria-live="polite">
      <p>Invio dei dati in corso...</p>
      {data && <p>Email: {data.get("email")}</p>}
    </div>
  );
}

// Utilizzo — BottoneSubmit DEVE essere figlio del <form>
function FormContatto() {
  return (
    <form action={azioneContatto}>
      <input name="email" type="email" required />
      <textarea name="messaggio" required />
      <IndicatoreProgresso />
      <BottoneSubmit />
    </form>
  );
}
```

### React Compiler

Il **React Compiler** (precedentemente noto come React Forget) è uno strumento di build-time che analizza il codice React e inserisce automaticamente le ottimizzazioni di memoizzazione dove necessario. Rilasciato come versione stabile 1.0 nell'ottobre 2025, elimina la necessità di scrivere manualmente `React.memo`, `useMemo` e `useCallback` nella stragrande maggioranza dei casi.

**Come funziona.** Il Compiler analizza il codice sorgente a tempo di compilazione, comprende il flusso dei dati attraverso i componenti e determina automaticamente quali valori e funzioni devono essere memoizzati per evitare re-render non necessari. Il risultato è un codice che mantiene esattamente la stessa semantica ma con ottimizzazioni di performance inserite dove effettivamente utili — non ovunque indiscriminatamente.

**Risultati in produzione.** Meta ha adottato il Compiler nelle proprie applicazioni, compilando 1.231 componenti su 1.411 totali, con una riduzione del 20-30% del tempo di rendering e della latenza. I caricamenti iniziali e le navigazioni tra pagine migliorano fino al 12%, mentre certe interazioni risultano fino a 2.5 volte più veloci.

**Installazione e configurazione.** Il Compiler si integra con i principali tool di build: Babel, Vite, Metro (React Native) e Rsbuild. Per un progetto Vite, la configurazione è minimale:

```typescript
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import reactCompiler from "babel-plugin-react-compiler";

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [reactCompiler],
      },
    }),
  ],
});
```

**Compatibilità con il codice esistente.** Il Compiler funziona con il codice React esistente senza richiedere riscritture. Tuttavia, il codice deve seguire le **Regole di React** (Rules of React): componenti e hooks devono essere puri, senza effetti collaterali durante il rendering. Il Compiler skippa silenziosamente i componenti che violano queste regole. Per verificare la compatibilità prima di adottare il Compiler, si può usare la modalità `eslint-plugin-react-compiler` in modalità strict.

**Coesistenza con memoizzazione manuale.** Se il codice contiene già `React.memo`, `useMemo` e `useCallback`, il Compiler li riconosce e non li duplica. È possibile adottare il Compiler gradualmente, iniziando da directory o componenti specifici tramite la configurazione `sources` nel plugin.

### Altre novità di React 19

**`ref` come prop.** A partire da React 19, i function component possono ricevere `ref` direttamente come prop, senza necessità di `forwardRef`. Il wrapper `forwardRef` è ancora supportato ma considerato legacy.

```tsx
// React 19 — ref come prop diretta
function InputPersonalizzato({ label, ref, ...props }: InputProps & { ref?: React.Ref<HTMLInputElement> }) {
  return (
    <label>
      {label}
      <input ref={ref} {...props} />
    </label>
  );
}
```

**Metadati del documento.** React 19 supporta nativamente il rendering di tag `<title>`, `<meta>` e `<link>` all'interno dei componenti. React li hoista automaticamente nella sezione `<head>` del documento, semplificando la gestione dei metadati per SEO e social sharing senza librerie esterne come `react-helmet`.

**Supporto per fogli di stile.** React 19 gestisce nativamente i fogli di stile con priorità, assicurando che vengano caricati nell'ordine corretto e prima che il componente che li richiede venga renderizzato.

**Preloading delle risorse.** Nuove API (`preload`, `preinit`, `prefetchDNS`, `preconnect`) permettono di ottimizzare il caricamento delle risorse in modo dichiarativo, anticipando font, script e fogli di stile necessari.

---

## Server Components — Architettura Approfondita

I React Server Components (RSC) rappresentano il cambiamento architetturale più significativo nella storia di React. Non sono un semplice miglioramento incrementale del Server-Side Rendering tradizionale — sono un **nuovo paradigma** che ridefinisce il confine tra client e server nell'architettura delle applicazioni web.

### Architettura RSC

L'architettura RSC introduce una distinzione fondamentale tra due tipi di componenti: i **Server Components**, che vengono eseguiti esclusivamente sul server, e i **Client Components**, che vengono eseguiti nel browser (e opzionalmente pre-renderizzati sul server per l'SSR). Questa distinzione non riguarda dove il componente viene *renderizzato* — entrambi possono essere pre-renderizzati sul server — ma dove il componente *vive* e quale codice viene inviato al client.

**Server Components:**
- Vengono eseguiti solo sul server, mai nel browser
- Non contribuiscono al bundle JavaScript del client (zero KB aggiuntivi)
- Possono accedere direttamente a database, filesystem, variabili d'ambiente e API interne
- Non possono usare hooks interattivi (`useState`, `useEffect`, event handler)
- Possono essere asincroni (`async function`) e usare `await` direttamente nel corpo del componente
- Sono il default nell'App Router di Next.js

**Client Components:**
- Vengono inclusi nel bundle JavaScript del client
- Possono usare hooks, stato, effetti e event handler
- Vengono pre-renderizzati sul server (SSR tradizionale) ma poi idratati nel browser
- Si dichiarano con la direttiva `"use client"` in cima al file
- Dovrebbero essere usati solo dove è necessaria interattività

```tsx
// Server Component (default) — accesso diretto al database
async function ListaArticoli() {
  const articoli = await db.articoli.findMany({
    orderBy: { dataPubblicazione: "desc" },
    take: 20,
  });

  return (
    <section>
      <h2>Ultimi articoli</h2>
      {articoli.map((articolo) => (
        <CardArticolo key={articolo.id} articolo={articolo} />
      ))}
    </section>
  );
}

// Client Component — interattività lato browser
"use client";

import { useState } from "react";

function BottoneLike({ articoloId, likesIniziali }: { articoloId: string; likesIniziali: number }) {
  const [likes, setLikes] = useState(likesIniziali);
  const [liked, setLiked] = useState(false);

  const toggleLike = async () => {
    setLiked(!liked);
    setLikes((prev) => (liked ? prev - 1 : prev + 1));
    await fetch(`/api/articoli/${articoloId}/like`, { method: "POST" });
  };

  return (
    <button onClick={toggleLike} aria-pressed={liked}>
      {liked ? "❤️" : "🤍"} {likes}
    </button>
  );
}
```

### Server Actions in profondità

Le **Server Actions** sono funzioni asincrone marcate con la direttiva `"use server"` che vengono eseguite sul server ma possono essere invocate direttamente dai Client Components. Sono il meccanismo primario per le mutazioni di dati nell'architettura RSC, eliminando la necessità di creare endpoint API REST manuali per ogni operazione CRUD.

```tsx
// app/actions/articoli.ts
"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";

const schemaArticolo = z.object({
  titolo: z.string().min(5).max(200),
  contenuto: z.string().min(50),
  categoria: z.enum(["tech", "design", "business"]),
});

export async function creaArticolo(formData: FormData) {
  // Validazione server-side — MAI fidarsi del client
  const risultato = schemaArticolo.safeParse({
    titolo: formData.get("titolo"),
    contenuto: formData.get("contenuto"),
    categoria: formData.get("categoria"),
  });

  if (!risultato.success) {
    return { errore: risultato.error.flatten().fieldErrors };
  }

  await db.articoli.create({ data: risultato.data });
  revalidatePath("/articoli");
  redirect("/articoli");
}

export async function eliminaArticolo(id: string) {
  await db.articoli.delete({ where: { id } });
  revalidatePath("/articoli");
}
```

**Sicurezza delle Server Actions.** Le Server Actions sono esposte come endpoint HTTP POST e pertanto devono essere trattate come qualsiasi endpoint pubblico. Ogni Server Action deve: validare tutti gli input (con Zod o simili), verificare l'autenticazione e l'autorizzazione, sanificare i dati prima di inserirli nel database, e non esporre mai informazioni sensibili nella risposta. La direttiva `"use server"` non è una garanzia di sicurezza — è solo un'indicazione per il bundler.

### Streaming SSR

Lo streaming SSR è una delle innovazioni più impattanti dell'architettura RSC. A differenza del SSR tradizionale, che deve attendere il completamento di tutto il data fetching prima di inviare qualsiasi HTML al browser, lo streaming SSR invia progressivamente parti della pagina man mano che diventano disponibili.

Il flusso è il seguente: (1) il server inizia immediatamente a inviare lo shell della pagina (header, layout, navigazione); (2) per ogni boundary `<Suspense>`, il server invia il fallback e continua il rendering degli altri componenti; (3) quando i dati per un componente sospeso diventano disponibili, il server invia un chunk HTML con il contenuto reale e un piccolo script inline che sostituisce il fallback nel DOM; (4) questo processo continua fino al completamento di tutti i componenti.

```tsx
// Layout con streaming — le sezioni si caricano indipendentemente
import { Suspense } from "react";

async function PaginaDashboard() {
  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      {/* I dati critici si caricano per primi */}
      <Suspense fallback={<SkeletonMetriche />}>
        <MetrichePrincipali />
      </Suspense>

      <div className="griglia">
        {/* Questi si caricano in parallelo, indipendentemente */}
        <Suspense fallback={<SkeletonGrafico />}>
          <GraficoVendite />
        </Suspense>

        <Suspense fallback={<SkeletonTabella />}>
          <TabellaOrdiniRecenti />
        </Suspense>

        {/* Sezioni meno critiche possono arrivare per ultime */}
        <Suspense fallback={<SkeletonAttivita />}>
          <FeedAttivitaRecente />
        </Suspense>
      </div>
    </div>
  );
}
```

Il vantaggio dello streaming è duplice: l'utente vede contenuto significativo molto prima (migliorando la metrica Time to First Byte e il First Contentful Paint), e le sezioni indipendenti della pagina non si bloccano a vicenda — una query lenta al database non impedisce al resto della pagina di apparire.

---

## Hooks Avanzati — Approfondimento

### Pattern avanzati con `useReducer`

`useReducer` diventa particolarmente potente quando combinato con pattern architetturali strutturati. Per applicazioni con logica di stato complessa, è consigliabile definire le azioni come unione discriminata TypeScript, separare il reducer dal componente per facilitarne il testing, e comporre reducer più piccoli per gestire sotto-domini dello stato.

**Pattern: Reducer con middleware.** Si può implementare un sistema di middleware che intercetta le azioni prima che raggiungano il reducer, utile per logging, validazione o side effects.

```tsx
type AzioneCarrello =
  | { type: "AGGIUNGI_PRODOTTO"; payload: Prodotto }
  | { type: "RIMUOVI_PRODOTTO"; payload: { id: string } }
  | { type: "AGGIORNA_QUANTITA"; payload: { id: string; quantita: number } }
  | { type: "APPLICA_SCONTO"; payload: { codice: string; percentuale: number } }
  | { type: "SVUOTA" };

interface StatoCarrello {
  articoli: ArticoloCarrello[];
  scontoApplicato: { codice: string; percentuale: number } | null;
  ultimaModifica: number;
}

function carrelloReducer(stato: StatoCarrello, azione: AzioneCarrello): StatoCarrello {
  const timestamp = Date.now();

  switch (azione.type) {
    case "AGGIUNGI_PRODOTTO": {
      const esistente = stato.articoli.find((a) => a.id === azione.payload.id);
      if (esistente) {
        return {
          ...stato,
          articoli: stato.articoli.map((a) =>
            a.id === azione.payload.id ? { ...a, quantita: a.quantita + 1 } : a
          ),
          ultimaModifica: timestamp,
        };
      }
      return {
        ...stato,
        articoli: [...stato.articoli, { ...azione.payload, quantita: 1 }],
        ultimaModifica: timestamp,
      };
    }
    case "RIMUOVI_PRODOTTO":
      return {
        ...stato,
        articoli: stato.articoli.filter((a) => a.id !== azione.payload.id),
        ultimaModifica: timestamp,
      };
    case "AGGIORNA_QUANTITA":
      return {
        ...stato,
        articoli: stato.articoli.map((a) =>
          a.id === azione.payload.id ? { ...a, quantita: azione.payload.quantita } : a
        ),
        ultimaModifica: timestamp,
      };
    case "APPLICA_SCONTO":
      return { ...stato, scontoApplicato: azione.payload, ultimaModifica: timestamp };
    case "SVUOTA":
      return { articoli: [], scontoApplicato: null, ultimaModifica: timestamp };
  }
}
```

**Pattern: Reducer con init lazy.** Il terzo argomento di `useReducer` è una funzione di inizializzazione lazy, utile quando lo stato iniziale richiede un calcolo costoso o la lettura da `localStorage`.

```tsx
function initCarrello(sorgente: string): StatoCarrello {
  try {
    const salvato = localStorage.getItem(sorgente);
    if (salvato) return JSON.parse(salvato);
  } catch {
    // localStorage non disponibile o dati corrotti
  }
  return { articoli: [], scontoApplicato: null, ultimaModifica: Date.now() };
}

function ComponenteCarrello() {
  const [stato, dispatch] = useReducer(carrelloReducer, "carrello-v1", initCarrello);
  // ...
}
```

### `useSyncExternalStore`

`useSyncExternalStore` è un hook introdotto in React 18 per sottoscriversi a store esterni in modo **concurrent-safe**. Il problema che risolve è il **tearing**: in modalità concorrente, React può interrompere e riprendere il rendering, e durante questa pausa uno store esterno potrebbe aggiornarsi, causando inconsistenze dove parti diverse dell'interfaccia mostrano valori diversi dello stesso dato.

L'hook accetta tre argomenti: una funzione `subscribe` per registrare un callback di notifica, una funzione `getSnapshot` che restituisce il valore corrente dello store, e una funzione opzionale `getServerSnapshot` per il rendering server-side.

```tsx
import { useSyncExternalStore } from "react";

// Store esterno semplice — pattern "pub/sub"
function creaStore<T>(valoreIniziale: T) {
  let stato = valoreIniziale;
  const listeners = new Set<() => void>();

  return {
    getSnapshot: () => stato,
    subscribe: (listener: () => void) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    aggiorna: (nuovoStato: T | ((prev: T) => T)) => {
      stato = typeof nuovoStato === "function"
        ? (nuovoStato as (prev: T) => T)(stato)
        : nuovoStato;
      listeners.forEach((l) => l());
    },
  };
}

const contratoreStore = creaStore(0);

// Custom hook basato su useSyncExternalStore
function useContatoreEsterno() {
  const valore = useSyncExternalStore(
    contratoreStore.subscribe,
    contratoreStore.getSnapshot,
    () => 0 // Server snapshot per SSR
  );
  return { valore, incrementa: () => contratoreStore.aggiorna((v) => v + 1) };
}
```

**Casi d'uso principali:** sottoscrizione a API del browser (come `navigator.onLine`, `matchMedia`, `IntersectionObserver`), integrazione con librerie di stato non-React, lettura da `localStorage` o `sessionStorage` in modo reattivo, e sincronizzazione con WebSocket o EventSource.

```tsx
// Hook per monitorare lo stato di connessione
function useOnline(): boolean {
  return useSyncExternalStore(
    (callback) => {
      window.addEventListener("online", callback);
      window.addEventListener("offline", callback);
      return () => {
        window.removeEventListener("online", callback);
        window.removeEventListener("offline", callback);
      };
    },
    () => navigator.onLine,
    () => true // Sul server si assume connessione attiva
  );
}
```

### Composizione avanzata di Custom Hooks

I custom hooks raggiungono la loro massima espressività quando vengono **composti** — un custom hook può chiamare altri custom hooks, costruendo astrazioni a strati come mattoncini. Questo approccio produce codice altamente riutilizzabile e testabile.

```tsx
// Composizione: useDebounce + useFetch = useSearchResults
function useSearchResults(query: string) {
  const debouncedQuery = useDebounce(query, 300);
  const { dati, errore, caricamento } = useFetch(
    debouncedQuery.length >= 2 ? `/api/ricerca?q=${encodeURIComponent(debouncedQuery)}` : null
  );
  return { risultati: dati, errore, caricamento, queryAttiva: debouncedQuery };
}

// Composizione: useLocalStorage + useMediaQuery = usePreferenzeUtente
function usePreferenzeUtente() {
  const [lingua, setLingua] = useLocalStorage("lingua", "it");
  const [tema, setTema] = useLocalStorage("tema", "auto");
  const preferisceScuro = useMediaQuery("(prefers-color-scheme: dark)");

  const temaEffettivo = tema === "auto" ? (preferisceScuro ? "scuro" : "chiaro") : tema;

  return {
    lingua,
    setLingua,
    tema: temaEffettivo,
    setTema,
    preferisceScuro,
  };
}

// Hook con cleanup e gestione del ciclo di vita
function useIntervallo(callback: () => void, delayMs: number | null) {
  const callbackSalvato = useRef(callback);

  useEffect(() => {
    callbackSalvato.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delayMs === null) return;
    const id = setInterval(() => callbackSalvato.current(), delayMs);
    return () => clearInterval(id);
  }, [delayMs]);
}
```

**Principi per custom hooks ben progettati:** (1) un hook dovrebbe fare **una sola cosa** — se fa troppo, probabilmente va scomposto; (2) i nomi devono essere **descrittivi e specifici** — `useAuth` è chiaro, `useData` è troppo vago; (3) il tipo di ritorno deve essere coerente — un hook che a volte restituisce un array e a volte un oggetto confonde l'utilizzatore; (4) la gestione degli errori deve essere esplicita — non ingoiare eccezioni silenziosamente; (5) i hook devono essere **testabili indipendentemente** dal componente che li usa, tramite `renderHook` di React Testing Library.

---

## Gestione Stato — Confronto Approfondito

La scelta della libreria di state management è una delle decisioni architetturali più importanti in un progetto React. Ogni libreria incarna una filosofia diversa, e la scelta giusta dipende dalla dimensione del progetto, dalla complessità dello stato e dalle preferenze del team.

### Zustand — Store Centralizzato Minimale

Zustand utilizza un pattern di **store centralizzato** esterno a React. Lo store è un singolo oggetto JavaScript con stato e azioni, accessibile tramite un hook generato automaticamente. I componenti si sottoscrivono a porzioni specifiche dello store tramite **selettori**, minimizzando i re-render.

```tsx
import { create } from "zustand";
import { persist, devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

interface StatoApp {
  utente: Utente | null;
  notifiche: Notifica[];
  login: (credenziali: Credenziali) => Promise<void>;
  logout: () => void;
  aggiungiNotifica: (notifica: Omit<Notifica, "id">) => void;
  rimuoviNotifica: (id: string) => void;
}

const useAppStore = create<StatoApp>()(
  devtools(
    persist(
      immer((set) => ({
        utente: null,
        notifiche: [],
        login: async (credenziali) => {
          const risposta = await fetch("/api/login", {
            method: "POST",
            body: JSON.stringify(credenziali),
            headers: { "Content-Type": "application/json" },
          });
          const dati = await risposta.json();
          set((stato) => {
            stato.utente = dati.utente;
          });
        },
        logout: () =>
          set((stato) => {
            stato.utente = null;
          }),
        aggiungiNotifica: (notifica) =>
          set((stato) => {
            stato.notifiche.push({ ...notifica, id: crypto.randomUUID() });
          }),
        rimuoviNotifica: (id) =>
          set((stato) => {
            stato.notifiche = stato.notifiche.filter((n) => n.id !== id);
          }),
      })),
      { name: "app-store" }
    )
  )
);

// Selettori per minimizzare re-render
function BarraNavigazione() {
  const nomeUtente = useAppStore((s) => s.utente?.nome);
  const conteggioNotifiche = useAppStore((s) => s.notifiche.length);
  // Si ri-renderizza solo quando nomeUtente o conteggioNotifiche cambiano
  return (
    <nav>
      <span>{nomeUtente ?? "Ospite"}</span>
      <span>Notifiche: {conteggioNotifiche}</span>
    </nav>
  );
}
```

**Punti di forza di Zustand:** dimensione minima (~3 KB gzippato), nessun Provider necessario, API semplice e intuitiva, middleware ricco (persist per localStorage, devtools per Redux DevTools, immer per aggiornamenti mutabili), e possibilità di accedere allo store al di fuori di React (utile per middleware, test o logica non-componente).

### Jotai — Stato Atomico

Jotai adotta un approccio radicalmente diverso: lo stato è suddiviso in **atomi** indipendenti, e i componenti si sottoscrivono solo agli atomi che utilizzano. Quando un atomo cambia, solo i componenti che lo leggono si ri-renderizzano. Non esiste uno store centralizzato — gli atomi sono entità autonome che possono essere composte e derivate.

```tsx
import { atom, useAtom, useAtomValue, useSetAtom } from "jotai";
import { atomWithStorage } from "jotai/utils";

// Atomi primitivi
const temaAtom = atomWithStorage("tema", "chiaro");
const linguaAtom = atomWithStorage("lingua", "it");
const contatoreSidebarAtom = atom(false);

// Atomo derivato (computed) — si aggiorna automaticamente quando le dipendenze cambiano
const classiTemaAtom = atom((get) => {
  const tema = get(temaAtom);
  return {
    sfondo: tema === "scuro" ? "bg-gray-900" : "bg-white",
    testo: tema === "scuro" ? "text-white" : "text-gray-900",
  };
});

// Atomo asincrono — carica dati dal server
const profiloUtenteAtom = atom(async () => {
  const risposta = await fetch("/api/profilo");
  return risposta.json();
});

// Atomo write-only
const resetTuttoAtom = atom(null, (_get, set) => {
  set(temaAtom, "chiaro");
  set(linguaAtom, "it");
  set(contatoreSidebarAtom, false);
});

function ToggleTema() {
  const [tema, setTema] = useAtom(temaAtom);
  return (
    <button onClick={() => setTema(tema === "chiaro" ? "scuro" : "chiaro")}>
      Tema: {tema}
    </button>
  );
}
```

**Punti di forza di Jotai:** re-render ultra-granulari (solo i componenti che leggono l'atomo modificato), composabilità eccellente degli atomi, supporto nativo per atomi asincroni con Suspense, nessun boilerplate per definire lo store, e performance superiore con molti pezzi di stato indipendenti.

### Signals — Reattività Fine

I **signals** (implementati da librerie come `@preact/signals-react`) rappresentano un approccio alla reattività fine che aggiorna direttamente il DOM senza passare attraverso il ciclo di re-render di React. Un signal è un contenitore reattivo il cui valore, quando cambia, propaga l'aggiornamento solo ai punti esatti del DOM che lo consumano.

**Performance comparata:** in benchmark con 1000 componenti sottoscritti, i signals aggiornano il DOM in circa 3ms (contro i 12ms di Zustand e i 14ms di Jotai), grazie al bypass del sistema di reconciliation di React. L'uso di memoria è anch'esso inferiore: 1.4 MB per i signals contro 2.1 MB per Zustand e 1.8 MB per Jotai.

**Quando usare cosa:**

| Scenario | Libreria consigliata |
|---|---|
| Progetto di dimensione media, stato condiviso moderato | **Zustand** |
| Molti pezzi di stato indipendenti, dashboard complesse | **Jotai** |
| Stato enterprise con molti sviluppatori e middleware | **Redux Toolkit** |
| Performance critica con aggiornamenti ultra-frequenti | **Signals** |
| Stato server (cache di dati API) | **TanStack Query** |
| Stato globale raro (tema, auth, locale) | **Context API** |
| Stato locale del componente | **useState / useReducer** |

---

## Routing Avanzato

### React Router v7

React Router v7 (evoluzione di Remix) opera in due modalità distinte. In **modalità libreria**, funziona come il tradizionale router client-side per SPA. In **modalità framework**, diventa un framework full-stack con file-based routing, SSR, streaming e server actions — sostituendo di fatto Remix.

La modalità framework introduce `loader` e `action` a livello di route, permettendo di caricare dati e gestire mutazioni prima che il componente venga renderizzato. Questo elimina i loading spinner nei componenti e garantisce che i dati siano disponibili al momento del rendering.

```tsx
// route.tsx — React Router v7 in modalità framework
import type { Route } from "./+types/route";

export async function loader({ params }: Route.LoaderArgs) {
  const prodotto = await db.prodotti.findUnique({ where: { id: params.id } });
  if (!prodotto) throw new Response("Non trovato", { status: 404 });
  return { prodotto };
}

export async function action({ request }: Route.ActionArgs) {
  const formData = await request.formData();
  const intento = formData.get("intento");

  if (intento === "elimina") {
    await db.prodotti.delete({ where: { id: formData.get("id") as string } });
    return { successo: true };
  }
}

export default function DettaglioProdotto({ loaderData }: Route.ComponentProps) {
  const { prodotto } = loaderData;

  return (
    <div>
      <h1>{prodotto.nome}</h1>
      <p>€{prodotto.prezzo}</p>
      <Form method="post">
        <input type="hidden" name="id" value={prodotto.id} />
        <button name="intento" value="elimina">Elimina</button>
      </Form>
    </div>
  );
}
```

### TanStack Router

TanStack Router si distingue per la **type-safety al 100%**: parametri di route, search params e dati dei loader sono completamente tipizzati senza casting manuale. Il router genera automaticamente i tipi dalle definizioni delle route, offrendo autocompletamento e verifica a compile-time per ogni aspetto della navigazione.

```tsx
import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

// Schema per i search params tipizzati
const searchSchema = z.object({
  pagina: z.number().default(1),
  ordinamento: z.enum(["nome", "prezzo", "data"]).default("data"),
  direzione: z.enum(["asc", "desc"]).default("desc"),
});

export const Route = createFileRoute("/prodotti")({
  validateSearch: searchSchema,
  loaderDeps: ({ search }) => ({ search }),
  loader: async ({ deps: { search } }) => {
    return fetchProdotti(search);
  },
  component: PaginaProdotti,
});

function PaginaProdotti() {
  const { pagina, ordinamento, direzione } = Route.useSearch();
  const prodotti = Route.useLoaderData();
  const navigate = Route.useNavigate();

  // Tutti i tipi sono inferiti automaticamente — nessun cast
  const cambiaPagina = (nuovaPagina: number) => {
    navigate({ search: (prev) => ({ ...prev, pagina: nuovaPagina }) });
  };

  return (
    <div>
      {prodotti.map((p) => <CardProdotto key={p.id} prodotto={p} />)}
      <Paginazione pagina={pagina} onChange={cambiaPagina} />
    </div>
  );
}
```

**Quando scegliere TanStack Router:** per progetti che richiedono type-safety estrema su search params e parametri di route, per SPA client-side dove la tipizzazione end-to-end è prioritaria, e per team che apprezzano la DX TypeScript-first. **Quando scegliere React Router v7:** per applicazioni che necessitano di SSR, streaming e server actions integrati, per migrazioni da Remix, e per progetti enterprise che privilegiano la maturità e la stabilità dell'ecosistema.

---

## Error Boundaries e Suspense — Approfondimento

### Error Boundaries: Architettura e Pattern

Gli Error Boundaries sono componenti che intercettano gli errori JavaScript nei componenti figli durante il rendering, nei lifecycle method e nei costruttori. Sono l'unico caso d'uso rimasto per i componenti classe in React moderno (non esiste un equivalente hook per `componentDidCatch`). La libreria `react-error-boundary` offre un'API funzionale moderna che copre la maggior parte dei casi d'uso.

**Strategia di posizionamento.** Gli Error Boundary dovrebbero essere posizionati a livelli strategici dell'albero dei componenti: (1) a livello di applicazione per catturare errori catastrofici; (2) a livello di route per isolare gli errori alle singole pagine; (3) a livello di sezione per proteggere aree indipendenti dell'interfaccia.

```tsx
import { ErrorBoundary } from "react-error-boundary";

// Fallback con azione di recupero
function FallbackErrore({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div role="alert" className="pannello-errore">
      <h2>Si è verificato un errore</h2>
      <pre>{error.message}</pre>
      <button onClick={resetErrorBoundary}>Riprova</button>
    </div>
  );
}

// Architettura stratificata di error boundaries
function App() {
  return (
    <ErrorBoundary
      FallbackComponent={FallbackErroreCritico}
      onError={(error, info) => {
        // Invio a servizio di monitoraggio (Sentry, DataDog)
        monitoraggio.captureException(error, { extra: info });
      }}
    >
      <Layout>
        <ErrorBoundary
          FallbackComponent={FallbackErrore}
          onReset={() => { /* Reset dello stato se necessario */ }}
          resetKeys={[location.pathname]} // Reset automatico al cambio di route
        >
          <Suspense fallback={<SkeletonPagina />}>
            <ContenutoPagina />
          </Suspense>
        </ErrorBoundary>
      </Layout>
    </ErrorBoundary>
  );
}
```

**Limitazioni degli Error Boundary.** Non catturano errori: negli event handler (vanno gestiti con try/catch), nel codice asincrono (Promise reject non intercettate), nel rendering server-side, e negli errori generati dall'Error Boundary stesso. Per gli errori asincroni, è necessario catturarli esplicitamente e propagarli allo stato del componente, oppure usare le Actions di React 19 che gestiscono automaticamente gli errori nelle operazioni asincrone.

### Pattern Suspense avanzati

Suspense non è semplicemente un meccanismo per mostrare un loading spinner — è un **sistema di coordinazione del rendering** che permette a React di gestire in modo dichiarativo le dipendenze asincrone dei componenti.

**Suspense annidato con cascading fallback.** Quando più boundary Suspense sono annidati, React mostra il fallback del boundary più vicino al componente che si sospende. Questo permette di creare esperienze di caricamento graduali dove le parti critiche dell'interfaccia appaiono per prime.

```tsx
function PaginaProdotto({ id }: { id: string }) {
  return (
    <Suspense fallback={<SkeletonPaginaIntera />}>
      {/* Il titolo e il prezzo appaiono subito */}
      <InfoProdotto id={id} />

      <div className="griglia-dettagli">
        <Suspense fallback={<SkeletonRecensioni />}>
          {/* Le recensioni si caricano indipendentemente */}
          <Recensioni prodottoId={id} />
        </Suspense>

        <Suspense fallback={<SkeletonProdottiCorrelati />}>
          {/* I prodotti correlati possono arrivare per ultimi */}
          <ProdottiCorrelati prodottoId={id} />
        </Suspense>
      </div>
    </Suspense>
  );
}
```

**Suspense + Error Boundary combinati.** Il pattern robusto per la gestione dei dati in React 19 combina `use()`, `Suspense` e `ErrorBoundary` in un sistema stratificato dove Suspense gestisce l'attesa e Error Boundary gestisce i fallimenti.

---

## Funzionalità Concorrenti

### Transizioni (`useTransition`)

Le **transizioni** permettono di marcare un aggiornamento di stato come **non urgente**, comunicando a React che può interromperlo se arriva un aggiornamento più urgente (come un input dell'utente). Questo mantiene l'interfaccia reattiva anche durante aggiornamenti computazionalmente costosi.

React utilizza internamente un sistema di **lane** (corsie) per assegnare priorità agli aggiornamenti: gli aggiornamenti urgenti (input dell'utente, click) hanno priorità alta, mentre le transizioni hanno priorità bassa. Il schedulatore decide quale lavoro eseguire immediatamente e quale posticipare.

```tsx
import { useState, useTransition, memo } from "react";

function FiltroArticoli({ articoli }: { articoli: Articolo[] }) {
  const [inputRicerca, setInputRicerca] = useState("");
  const [filtro, setFiltro] = useState("");
  const [isPending, startTransition] = useTransition();

  const gestisciRicerca = (e: React.ChangeEvent<HTMLInputElement>) => {
    const valore = e.target.value;
    // Aggiornamento urgente: l'input riflette immediatamente la digitazione
    setInputRicerca(valore);
    // Transizione: il filtro della lista può attendere
    startTransition(() => {
      setFiltro(valore);
    });
  };

  const articoliFiltrati = articoli.filter((a) =>
    a.titolo.toLowerCase().includes(filtro.toLowerCase())
  );

  return (
    <div>
      <input value={inputRicerca} onChange={gestisciRicerca} placeholder="Cerca..." />
      {isPending && <span className="indicatore-caricamento" />}
      <div style={{ opacity: isPending ? 0.7 : 1 }}>
        {articoliFiltrati.map((a) => (
          <ArticoloMemo key={a.id} articolo={a} />
        ))}
      </div>
    </div>
  );
}

const ArticoloMemo = memo(function ArticoloMemo({ articolo }: { articolo: Articolo }) {
  return (
    <article>
      <h3>{articolo.titolo}</h3>
      <p>{articolo.anteprima}</p>
    </article>
  );
});
```

### Valori Differiti (`useDeferredValue`)

`useDeferredValue` è il complemento di `useTransition` per i casi in cui non si ha il controllo diretto sull'aggiornamento dello stato. Accetta un valore e restituisce una versione "differita" che resta indietro durante aggiornamenti rapidi, permettendo a React di dare priorità al rendering dell'interfaccia interattiva.

```tsx
import { useState, useDeferredValue, Suspense } from "react";

function RicercaConAnteprima() {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Cerca articoli..."
      />
      <Suspense fallback={<SkeletonRisultati />}>
        <div style={{ opacity: isStale ? 0.6 : 1, transition: "opacity 200ms" }}>
          <RisultatiRicerca query={deferredQuery} />
        </div>
      </Suspense>
    </div>
  );
}
```

**Differenza tra `useTransition` e `useDeferredValue`.** `useTransition` si usa quando si ha il controllo del setter di stato — si avvolge il `setState` in `startTransition`. `useDeferredValue` si usa quando si riceve un valore dall'esterno (da una prop o da un contesto) e non si può controllare come viene aggiornato. Entrambi comunicano a React che l'aggiornamento è a bassa priorità, ma si applicano a scenari diversi.

---

## React Patterns Avanzati

### Compound Components

I **compound components** sono un insieme di componenti che lavorano insieme sotto un genitore condiviso, comunicando tramite Context. Il genitore gestisce lo stato condiviso e i figli lo consumano. Questo pattern è utilizzato da librerie UI come Radix UI, Headless UI e Material UI.

```tsx
import { createContext, useContext, useState, type ReactNode } from "react";

// Context condiviso tra i compound components
interface AccordionContextType {
  pannelloAperto: string | null;
  toggle: (id: string) => void;
}

const AccordionContext = createContext<AccordionContextType | null>(null);

function useAccordionContext() {
  const ctx = useContext(AccordionContext);
  if (!ctx) throw new Error("Componente Accordion.* usato fuori da <Accordion>");
  return ctx;
}

// Componente radice
function Accordion({ children }: { children: ReactNode }) {
  const [pannelloAperto, setPannelloAperto] = useState<string | null>(null);
  const toggle = (id: string) =>
    setPannelloAperto((prev) => (prev === id ? null : id));

  return (
    <AccordionContext.Provider value={{ pannelloAperto, toggle }}>
      <div className="accordion" role="region">{children}</div>
    </AccordionContext.Provider>
  );
}

// Sotto-componente: header cliccabile
function AccordionItem({ id, titolo, children }: { id: string; titolo: string; children: ReactNode }) {
  const { pannelloAperto, toggle } = useAccordionContext();
  const aperto = pannelloAperto === id;

  return (
    <div className="accordion-item">
      <button
        onClick={() => toggle(id)}
        aria-expanded={aperto}
        aria-controls={`pannello-${id}`}
        className="accordion-header"
      >
        {titolo}
        <span aria-hidden="true">{aperto ? "▲" : "▼"}</span>
      </button>
      {aperto && (
        <div id={`pannello-${id}`} role="region" className="accordion-body">
          {children}
        </div>
      )}
    </div>
  );
}

// Attacca i sotto-componenti al namespace
Accordion.Item = AccordionItem;

// Utilizzo — API pulita e dichiarativa
function FAQ() {
  return (
    <Accordion>
      <Accordion.Item id="q1" titolo="Cos'è React?">
        <p>React è una libreria per costruire interfacce utente.</p>
      </Accordion.Item>
      <Accordion.Item id="q2" titolo="Cosa sono gli hooks?">
        <p>Funzioni che aggiungono stato e funzionalità ai componenti.</p>
      </Accordion.Item>
    </Accordion>
  );
}
```

### Evoluzione dei pattern: HOC, Render Props e Hooks

L'evoluzione dei pattern di riuso in React segue una traiettoria chiara: **Higher-Order Components (HOC)** → **Render Props** → **Custom Hooks**.

**Higher-Order Components.** Un HOC è una funzione che prende un componente e restituisce un nuovo componente arricchito. Erano il pattern dominante prima degli hooks. Oggi gli HOC rimangono utili in casi specifici: aggiungere logica trasversale (logging, analytics, autorizzazione) a componenti esistenti senza modificarli, e integrare con API legacy che si aspettano componenti classe.

```tsx
// HOC per autorizzazione — ancora utile nel 2025
function conAutorizzazione<P extends object>(
  Componente: React.ComponentType<P>,
  ruoloRichiesto: string
) {
  return function ComponenteAutorizzato(props: P) {
    const { utente } = useAuth();

    if (!utente) return <Navigate to="/login" />;
    if (!utente.ruoli.includes(ruoloRichiesto)) return <PaginaNonAutorizzato />;

    return <Componente {...props} />;
  };
}

const PaginaAdminProtetta = conAutorizzazione(PaginaAdmin, "admin");
```

**Render Props.** Il pattern render props delega il rendering al chiamante passando una funzione come prop (o come children). È stato largamente sostituito dagli hooks, ma rimane utile per componenti **headless** che separano la logica dall'interfaccia.

**Custom Hooks come evoluzione.** Gli hooks risolvono i problemi sia degli HOC (wrapper hell, conflitti di naming tra props) sia dei render props (callback nesting, false gerarchie nell'albero dei componenti). Oggi, per qualsiasi logica riutilizzabile, i custom hooks sono la scelta predefinita. Gli HOC e i render props sopravvivono in nicchie specifiche dove il pattern hook non si adatta naturalmente.

---

## Testing Avanzato

### Pattern di testing con React Testing Library

React Testing Library (RTL) impone un approccio al testing orientato all'utente: si interrogano gli elementi tramite il loro ruolo accessibile, il testo visibile o la label associata — mai tramite classi CSS, ID o attributi specifici per il test (a meno che non ci siano alternative).

**Gerarchia delle query raccomandata.** RTL definisce una priorità chiara per le query: (1) `getByRole` — la prima scelta, riflette come utenti e tecnologie assistive percepiscono la pagina; (2) `getByLabelText` — ideale per gli input dei form; (3) `getByPlaceholderText` — quando non c'è label; (4) `getByText` — per testo statico; (5) `getByTestId` — ultimo ricorso, quando nessuna query semantica è applicabile.

```tsx
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

describe("FormRegistrazione", () => {
  it("mostra errori di validazione per campi vuoti", async () => {
    const user = userEvent.setup();
    render(<FormRegistrazione />);

    await user.click(screen.getByRole("button", { name: /registrati/i }));

    expect(screen.getByText(/il nome deve avere almeno 2 caratteri/i)).toBeInTheDocument();
    expect(screen.getByText(/email non valida/i)).toBeInTheDocument();
  });

  it("invia il form con dati validi", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<FormRegistrazione onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/nome/i), "Mario Rossi");
    await user.type(screen.getByLabelText(/email/i), "mario@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "Password123");
    await user.type(screen.getByLabelText(/conferma password/i), "Password123");
    await user.click(screen.getByRole("button", { name: /registrati/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        nome: "Mario Rossi",
        email: "mario@example.com",
      })
    );
  });

  it("disabilita il bottone durante l'invio", async () => {
    const user = userEvent.setup();
    render(<FormRegistrazione />);

    // Compila i campi
    await user.type(screen.getByLabelText(/nome/i), "Test");
    await user.type(screen.getByLabelText(/email/i), "test@test.com");
    await user.type(screen.getByLabelText(/^password$/i), "Password1");
    await user.type(screen.getByLabelText(/conferma password/i), "Password1");
    await user.click(screen.getByRole("button", { name: /registrati/i }));

    expect(screen.getByRole("button", { name: /registrazione/i })).toBeDisabled();
  });
});
```

### Testing con MSW (Mock Service Worker) Avanzato

MSW intercetta le richieste HTTP a livello di network, permettendo ai test di esercitare i percorsi di codice reali dell'applicazione. A differenza del mocking di `fetch` o `axios`, MSW non modifica il codice dell'applicazione — le richieste partono normalmente e vengono intercettate prima di raggiungere la rete.

```tsx
import { http, HttpResponse, delay } from "msw";
import { setupServer } from "msw/node";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Definizione degli handler
const handlers = [
  http.get("/api/prodotti", async () => {
    return HttpResponse.json([
      { id: "1", nome: "Laptop", prezzo: 999 },
      { id: "2", nome: "Mouse", prezzo: 29 },
    ]);
  }),

  http.post("/api/prodotti", async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ id: "3", ...body }, { status: 201 });
  }),

  // Simulazione di errore
  http.get("/api/prodotti/:id", ({ params }) => {
    if (params.id === "non-esiste") {
      return HttpResponse.json({ errore: "Non trovato" }, { status: 404 });
    }
    return HttpResponse.json({ id: params.id, nome: "Prodotto Test" });
  }),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Helper per wrappare i componenti con i provider necessari
function renderConProvider(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("ListaProdotti", () => {
  it("gestisce errori di rete", async () => {
    // Override dell'handler per questo singolo test
    server.use(
      http.get("/api/prodotti", () => {
        return HttpResponse.error();
      })
    );

    renderConProvider(<ListaProdotti />);
    expect(await screen.findByText(/errore nel caricamento/i)).toBeInTheDocument();
  });

  it("gestisce risposte lente", async () => {
    server.use(
      http.get("/api/prodotti", async () => {
        await delay(2000);
        return HttpResponse.json([]);
      })
    );

    renderConProvider(<ListaProdotti />);
    expect(screen.getByText(/caricamento/i)).toBeInTheDocument();
  });
});
```

### Testing di Custom Hooks

I custom hooks si testano con `renderHook` di React Testing Library, che li esegue in un componente wrapper minimale.

```tsx
import { renderHook, act } from "@testing-library/react";
import { useDebounce } from "./useDebounce";

describe("useDebounce", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("ritorna il valore iniziale immediatamente", () => {
    const { result } = renderHook(() => useDebounce("ciao", 300));
    expect(result.current).toBe("ciao");
  });

  it("aggiorna il valore dopo il ritardo", () => {
    const { result, rerender } = renderHook(
      ({ valore, ritardo }) => useDebounce(valore, ritardo),
      { initialProps: { valore: "ciao", ritardo: 300 } }
    );

    rerender({ valore: "mondo", ritardo: 300 });
    expect(result.current).toBe("ciao"); // Non ancora aggiornato

    act(() => vi.advanceTimersByTime(300));
    expect(result.current).toBe("mondo"); // Aggiornato dopo il ritardo
  });
});
```

---

## Accessibilità in React

L'accessibilità (a11y) non è un'aggiunta opzionale — è un requisito legale nella UE dal giugno 2025 (European Accessibility Act) e un obbligo etico verso tutti gli utenti. React facilita la costruzione di interfacce accessibili grazie al supporto nativo per gli attributi ARIA e all'incoraggiamento verso l'HTML semantico.

### Principi fondamentali

**HTML semantico prima di ARIA.** Usare sempre l'elemento HTML nativo corretto prima di aggiungere attributi ARIA. Un `<button>` ha già il ruolo, la gestione del focus e il supporto tastiera integrati — un `<div onClick>` non ha nulla di tutto ciò e richiede ARIA, tabindex e gestione manuale degli eventi tastiera per raggiungere la stessa accessibilità.

**Gestione del focus.** Gli aggiornamenti dinamici dell'interfaccia (apertura di modali, cambio di tab, caricamento di nuovi contenuti) devono gestire il focus in modo esplicito. Quando un modale si apre, il focus deve spostarsi al primo elemento focusable al suo interno. Quando si chiude, il focus deve tornare all'elemento che lo ha aperto.

```tsx
import { useRef, useEffect } from "react";

function Modale({ aperto, onChiudi, titolo, children }: ModaleProps) {
  const chiudiRef = useRef<HTMLButtonElement>(null);
  const attivatorePrecedenteRef = useRef<Element | null>(null);

  useEffect(() => {
    if (aperto) {
      // Salva l'elemento che aveva il focus
      attivatorePrecedenteRef.current = document.activeElement;
      // Sposta il focus al modale
      chiudiRef.current?.focus();
    } else {
      // Ripristina il focus all'elemento precedente
      (attivatorePrecedenteRef.current as HTMLElement)?.focus();
    }
  }, [aperto]);

  // Trap del focus — impedisce di uscire dal modale con Tab
  const gestisciFocusTrap = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onChiudi();
      return;
    }

    if (e.key !== "Tab") return;

    const elementiFocusabili = e.currentTarget.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const primo = elementiFocusabili[0];
    const ultimo = elementiFocusabili[elementiFocusabili.length - 1];

    if (e.shiftKey && document.activeElement === primo) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primo.focus();
    }
  };

  if (!aperto) return null;

  return (
    <div className="modale-overlay" onClick={onChiudi}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titolo-modale"
        className="modale"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={gestisciFocusTrap}
      >
        <h2 id="titolo-modale">{titolo}</h2>
        {children}
        <button ref={chiudiRef} onClick={onChiudi} aria-label="Chiudi modale">
          ✕
        </button>
      </div>
    </div>
  );
}
```

### Navigazione da tastiera

Ogni componente interattivo deve essere utilizzabile interamente da tastiera. Le convenzioni sono: `Tab` per navigare tra gli elementi interattivi, `Enter`/`Space` per attivare, `Escape` per chiudere, e tasti freccia per navigare all'interno di widget compositi (tab, menu, listbox).

```tsx
function TabPanel({ tabs }: { tabs: { id: string; label: string; contenuto: ReactNode }[] }) {
  const [tabAttiva, setTabAttiva] = useState(tabs[0].id);

  const gestisciTastiera = (e: React.KeyboardEvent, indice: number) => {
    let nuovoIndice = indice;

    switch (e.key) {
      case "ArrowRight":
        nuovoIndice = (indice + 1) % tabs.length;
        break;
      case "ArrowLeft":
        nuovoIndice = (indice - 1 + tabs.length) % tabs.length;
        break;
      case "Home":
        nuovoIndice = 0;
        break;
      case "End":
        nuovoIndice = tabs.length - 1;
        break;
      default:
        return;
    }

    e.preventDefault();
    setTabAttiva(tabs[nuovoIndice].id);
    // Sposta il focus alla nuova tab
    document.getElementById(`tab-${tabs[nuovoIndice].id}`)?.focus();
  };

  return (
    <div>
      <div role="tablist" aria-label="Sezioni">
        {tabs.map((tab, i) => (
          <button
            key={tab.id}
            id={`tab-${tab.id}`}
            role="tab"
            aria-selected={tabAttiva === tab.id}
            aria-controls={`pannello-${tab.id}`}
            tabIndex={tabAttiva === tab.id ? 0 : -1}
            onClick={() => setTabAttiva(tab.id)}
            onKeyDown={(e) => gestisciTastiera(e, i)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab) => (
        <div
          key={tab.id}
          id={`pannello-${tab.id}`}
          role="tabpanel"
          aria-labelledby={`tab-${tab.id}`}
          hidden={tabAttiva !== tab.id}
          tabIndex={0}
        >
          {tab.contenuto}
        </div>
      ))}
    </div>
  );
}
```

### Live Regions e annunci

Per aggiornamenti dinamici che non spostano il focus (messaggi di successo, errori di validazione, contatori), usare `aria-live` per annunciarli agli screen reader.

```tsx
function MessaggioStato({ tipo, testo }: { tipo: "successo" | "errore"; testo: string }) {
  return (
    <div
      role={tipo === "errore" ? "alert" : "status"}
      aria-live={tipo === "errore" ? "assertive" : "polite"}
      className={`messaggio messaggio-${tipo}`}
    >
      {testo}
    </div>
  );
}
```

### React Aria e librerie headless

Per componenti complessi (combobox, datepicker, menu multilivello), implementare manualmente tutta la logica ARIA è proibitivo e soggetto a errori. Librerie headless come **React Aria** (Adobe), **Radix UI** e **Headless UI** forniscono primitivi accessibili senza stile, garantendo conformità WCAG e supporto completo per tastiera e screen reader. Si consiglia fortemente di usare queste librerie piuttosto che re-implementare pattern ARIA complessi.

---

## Performance — Approfondimento

### React.memo: Quando e Come

`React.memo` è una funzione di ordine superiore che avvolge un componente e previene il re-render se le props non sono cambiate (confronto shallow). Il suo utilizzo ha senso in tre scenari precisi: (1) il componente è **computazionalmente costoso** da renderizzare; (2) il componente riceve le **stesse props frequentemente** anche quando il genitore si ri-renderizza per altre ragioni; (3) il componente è in una **lista lunga** dove anche piccoli risparmi per singolo elemento si sommano.

**Trappole comuni con React.memo:** passare oggetti o array inline come props (`options={{}}`, `items={[]}`) vanifica la memoizzazione perché ogni render crea nuovi riferimenti. Passare callback inline (`onClick={() => ...}`) ha lo stesso effetto. La soluzione è usare `useMemo` per gli oggetti e `useCallback` per le funzioni — oppure adottare il React Compiler che gestisce tutto automaticamente.

### React DevTools Profiler

Il Profiler è lo strumento indispensabile per diagnosticare problemi di performance prima di applicare qualsiasi ottimizzazione. Registra una sessione di rendering e mostra: quali componenti si sono ri-renderizzati, quanto tempo ha impiegato ogni render, perché il componente si è ri-renderizzato (cambio di props, stato o contesto), e il commit timeline con i tempi di rendering.

**Workflow di ottimizzazione consigliato:** (1) identificare il problema con il Profiler; (2) analizzare la causa del re-render; (3) applicare l'ottimizzazione minima necessaria; (4) verificare con il Profiler che l'ottimizzazione abbia effetto; (5) misurare l'impatto su utenti reali con metriche Core Web Vitals.

### React Compiler e auto-memoizzazione

Con React Compiler 1.0, il workflow di ottimizzazione cambia radicalmente. Il Compiler analizza il codice a build-time e inserisce automaticamente `useMemo`, `useCallback` e `React.memo` dove determina che siano necessari. Questo significa che nella maggior parte dei casi lo sviluppatore non deve più pensare alla memoizzazione manuale — il Compiler la gestisce in modo più preciso e coerente di quanto farebbe un umano.

Per i progetti che adottano il Compiler, la raccomandazione è: (1) rimuovere gradualmente la memoizzazione manuale, (2) concentrarsi sulla correttezza del codice piuttosto che sull'ottimizzazione, (3) assicurarsi che i componenti seguano le Regole di React (purezza, nessun side effect nel render), e (4) usare l'ESLint plugin del Compiler per identificare i componenti non compilabili.

---

## Esercizi

### Esercizio 1 — Componenti e Props Tipizzate

**Obiettivo:** costruire un insieme di componenti React con TypeScript, gestendo props, children e composizione.

Creare una piccola libreria di componenti UI:

- Un componente `Card` con props tipizzate: `title: string`, `children: ReactNode`, `variant?: 'default' | 'outlined' | 'elevated'`
- Un componente `CardList` che riceva un array di dati generici e usi render props per delegare il rendering di ciascun elemento
- Un componente `Badge` con varianti colore gestite tramite discriminated union nelle props
- Tutti i componenti devono esportare il proprio tipo di props
- Scrivere test con React Testing Library che verifichino il rendering condizionale e l'accessibilita (ruoli ARIA)
- Zero warning nel browser e zero errori TypeScript con `strict: true`

### Esercizio 2 — Gestione dello Stato con Hooks

**Obiettivo:** padroneggiare `useState`, `useReducer` e custom hooks per stato complesso.

Implementare un'applicazione "Task Board" (kanban semplificato):

- Tre colonne: "Da Fare", "In Corso", "Completato"
- Ogni task ha `id`, `title`, `description`, `priority: 'low' | 'medium' | 'high'` e `column`
- Usare `useReducer` con un reducer tipizzato e action discriminate (`ADD_TASK`, `MOVE_TASK`, `DELETE_TASK`, `EDIT_TASK`)
- Creare un custom hook `useTaskBoard` che incapsuli il reducer e esponga metodi semantici
- Implementare drag-and-drop tra le colonne (anche con semplice click per spostare)
- Persistere lo stato in `localStorage` tramite un custom hook `useLocalStorage<T>`
- Test unitari per il reducer e test di integrazione per il componente board

### Esercizio 3 — Data Fetching con TanStack Query

**Obiettivo:** implementare data fetching robusto con caching, invalidazione e stati di loading/errore.

Creare un'applicazione che consumi un'API REST pubblica (es. JSONPlaceholder o PokeAPI):

- Configurare `QueryClient` con opzioni di default sensate (`staleTime`, `gcTime`, `retry`)
- Implementare una lista paginata con `useInfiniteQuery` e scroll infinito
- Implementare una pagina di dettaglio con `useQuery` e prefetching al hover del link
- Creare una mutation con `useMutation` per aggiungere un elemento, con invalidazione della cache e aggiornamento ottimistico
- Gestire gli stati di loading con `Suspense` e gli errori con un error boundary personalizzato
- Tipizzare completamente le risposte API con interfacce TypeScript e validazione Zod
- Test con `msw` (Mock Service Worker) per simulare le risposte API

### Esercizio 4 — Server Components e Suspense (Next.js App Router)

**Obiettivo:** costruire un'applicazione con architettura Server Components + Client Components.

Creare un blog con Next.js App Router:

- Struttura route: `/` (lista articoli), `/articoli/[slug]` (dettaglio), `/admin` (gestione)
- I Server Components caricano i dati direttamente (database o API) senza `useEffect`
- I Client Components gestiscono interattivita: form di ricerca, toggle tema, contatore like
- Usare `loading.tsx` per gli stati di caricamento e `error.tsx` per la gestione errori a livello di route
- Implementare le Server Actions per creare e modificare articoli
- Usare `generateStaticParams` per pre-generare le pagine degli articoli a build time (SSG)
- Implementare `generateMetadata` dinamico per ogni articolo (SEO)
- Test E2E con Playwright per il flusso completo: visualizzazione lista, lettura articolo, creazione articolo

### Esercizio 5 — Performance e Accessibilita

**Obiettivo:** ottimizzare una applicazione React esistente e garantirne l'accessibilita.

Partendo da un'applicazione React volutamente non ottimizzata (fornita o creata ad hoc):

- Identificare i componenti che causano re-render inutili con React DevTools Profiler
- Applicare `React.memo`, `useMemo` e `useCallback` dove effettivamente necessario, giustificando ogni scelta
- Implementare code splitting con `React.lazy` e `Suspense` per almeno 3 route
- Virtualizzare una lista di 10.000 elementi con `@tanstack/react-virtual`
- Aggiungere tutti gli attributi ARIA necessari: `aria-label`, `aria-live`, ruoli, gestione del focus
- Implementare la navigazione completa via tastiera (Tab, Enter, Escape, frecce)
- Verificare con Lighthouse un punteggio superiore a 90 in Performance e 100 in Accessibility
- Documentare le ottimizzazioni applicate e il loro impatto misurato

---

## Letture e Riferimenti

### Documentazione ufficiale

- **React Documentation** — documentazione ufficiale con tutorial interattivi e API reference. https://react.dev/ (consultato: 2026-05-24)
- **React API Reference** — riferimento completo di tutti gli hooks, componenti e API. https://react.dev/reference/react (consultato: 2026-05-24)
- **Next.js Documentation** — framework React per produzione con SSR, SSG e App Router. https://nextjs.org/docs (consultato: 2026-05-24)
- **React Router Documentation** — routing client-side per applicazioni React SPA. https://reactrouter.com/ (consultato: 2026-05-24)
- **TanStack Query** — libreria di data fetching e caching per React. https://tanstack.com/query/latest (consultato: 2026-05-24)
- **React Testing Library** — utility di testing orientate all'utente. https://testing-library.com/docs/react-testing-library/intro/ (consultato: 2026-05-24)
- **Zustand** — state management minimale per React. https://zustand.docs.pmnd.rs/ (consultato: 2026-05-24)

### Libri e approfondimenti

- Banks A., Porcello E., *Learning React*, O'Reilly Media, 2020.
- Dodds K. C., *Epic React* — corso avanzato con pattern e best practices. https://epicreact.dev/
- Abramov D., *Overreacted* — blog tecnico approfondito su React internals. https://overreacted.io/

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [06 — TypeScript](06-typescript.md) | Prerequisito: React moderno richiede TypeScript per props tipizzate, hooks generici e Context tipizzato |
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Basi del linguaggio necessarie per comprendere JSX, closure nei hooks e il modello a eventi |
| [25 — Next.js Guida Completa](25-nextjs-guida-completa.md) | Framework di produzione basato su React: App Router, Server Components, SSR/SSG |
| [15 — Testing Web](15-testing-web.md) | Strategie di testing per componenti React: unit con RTL, integrazione, E2E con Playwright |
| [17 — Performance Web](17-performance-web.md) | Tecniche di ottimizzazione applicabili ai bundle React: code splitting, lazy loading, Core Web Vitals |
| [21 — RSC e Server-Driven UI](21-rsc-server-driven-ui.md) | Approfondimento su React Server Components e il paradigma server-driven |

---

## Glossario

| Termine | Definizione |
|---|---|
| **JSX** | Estensione sintattica di JavaScript che permette di scrivere markup simile a HTML all'interno del codice, compilato in chiamate `React.createElement`. |
| **Hook** | Funzione che inizia con `use` e permette ai componenti funzionali di accedere a stato, effetti collaterali, contesto e altre funzionalita di React. |
| **Server Component (RSC)** | Componente che viene eseguito esclusivamente sul server, puo accedere direttamente a database e filesystem, e invia al client solo il risultato renderizzato. |
| **Client Component** | Componente marcato con `"use client"` che viene eseguito nel browser e puo utilizzare hooks interattivi come `useState` e `useEffect`. |
| **Suspense** | Meccanismo dichiarativo che permette a un componente di "sospendere" il rendering in attesa di dati asincroni, mostrando un fallback nel frattempo. |
| **Error Boundary** | Componente classe che intercetta gli errori JavaScript nei componenti figli e mostra un'interfaccia di fallback invece di un crash. |
| **Context** | Meccanismo per passare dati attraverso l'albero dei componenti senza prop drilling, creato con `createContext` e consumato con `useContext`. |
| **Reconciliation** | Algoritmo con cui React confronta il virtual DOM precedente con quello nuovo per determinare gli aggiornamenti minimi da applicare al DOM reale. |
| **Virtual DOM** | Rappresentazione in memoria del DOM reale che React usa per calcolare le differenze e applicare solo gli aggiornamenti necessari. |
| **Render Prop** | Pattern in cui un componente riceve una funzione come prop (o come children) e la invoca per delegare il rendering al chiamante. |
| **Code Splitting** | Tecnica che divide il bundle JavaScript in chunk separati caricati on-demand, riducendo il tempo di caricamento iniziale. |
| **Hydration** | Processo con cui React associa gli event handler e lo stato ai nodi HTML gia generati dal server, rendendo la pagina interattiva. |
| **Memoization** | Ottimizzazione che memorizza il risultato di un calcolo o il rendering di un componente, ricalcolando solo quando le dipendenze cambiano (`React.memo`, `useMemo`). |
| **Server Action** | Funzione asincrona marcata con `"use server"` che viene eseguita sul server quando invocata dal client, utilizzabile per mutazioni e form submission. |