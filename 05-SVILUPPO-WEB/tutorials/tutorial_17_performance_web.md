# Tutorial 17 — Performance Web: Dal Principiante all'Esperto

> **Companion a:** `17-performance-web.md`
> **Scope:** Core Web Vitals, misurazione in laboratorio e sul campo, percorso critico di rendering, LCP, INP e CLS in profondità, immagini e font, JavaScript e main thread, prestazioni del server e caching, resource hints, script di terze parti, budget di prestazione, monitoraggio continuo
> **Prerequisiti:** `tutorial_16_build_tools_deploy.md` — dimensione del bundle e code splitting; `tutorial_02_css3.md` — layout e compositor; `tutorial_04_javascript_fondamenti.md` — event loop
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Chrome DevTools · Lighthouse · web-vitals · CrUX · PageSpeed Insights

---

## Indice Generale

- [Mappa concettuale](#mappa-concettuale)
- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Cosa significa "veloce", e per chi](#a1-cosa-significa-veloce-e-per-chi)
  - [A2. I Core Web Vitals](#a2-i-core-web-vitals)
  - [A3. Misurare prima di cambiare](#a3-misurare-prima-di-cambiare)
  - [A4. Il percorso critico di rendering](#a4-il-percorso-critico-di-rendering)
  - [A5. Immagini e font: i due pesi maggiori](#a5-immagini-e-font-i-due-pesi-maggiori)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. LCP: trovare l'elemento e le sue quattro fasi](#b1-lcp-trovare-lelemento-e-le-sue-quattro-fasi)
  - [B2. INP: il costo di ogni interazione](#b2-inp-il-costo-di-ogni-interazione)
  - [B3. CLS: perché la pagina salta](#b3-cls-perché-la-pagina-salta)
  - [B4. Il main thread: long task e come spezzarli](#b4-il-main-thread-long-task-e-come-spezzarli)
  - [B5. Rendering: layout, paint e compositor](#b5-rendering-layout-paint-e-compositor)
  - [B6. Resource hints e speculation rules](#b6-resource-hints-e-speculation-rules)
  - [B7. Prestazioni del server: TTFB e caching](#b7-prestazioni-del-server-ttfb-e-caching)
  - [B8. Script di terze parti](#b8-script-di-terze-parti)
  - [B9. Budget e monitoraggio continuo](#b9-budget-e-monitoraggio-continuo)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: da Lighthouse 60 a 90+](#c2-mini-progetto-da-lighthouse-60-a-90)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Dati di laboratorio contro dati sul campo](#d1-dati-di-laboratorio-contro-dati-sul-campo)
  - [D2. Prestazioni percepite](#d2-prestazioni-percepite)
  - [D3. Memoria e perdite](#d3-memoria-e-perdite)
  - [D4. Prestazioni e accessibilità si aiutano](#d4-prestazioni-e-accessibilità-si-aiutano)
  - [D5. Quando smettere di ottimizzare](#d5-quando-smettere-di-ottimizzare)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   LA RICHIESTA                    IL RENDERING              L'USO
   ────────────                    ────────────              ─────
   DNS · TCP · TLS · TTFB    →  HTML → DOM                →  clic
   ↓ server, cache, CDN         CSS  → CSSOM                  scroll
   ↓                            ↓ albero di rendering         digitazione
   HTML                         layout → paint → compositing  ↓
   ↓ scopre le risorse          ↓                             INP
   CSS (bloccante)              LCP · CLS
   JS (bloccante se sync)

   ┌───────────────────────────────────────────────────────────┐
   │  I TRE CORE WEB VITALS, E COSA MISURANO DAVVERO           │
   │   LCP  quando compare il contenuto principale   ≤ 2,5 s   │
   │   INP  quanto è reattiva OGNI interazione       ≤ 200 ms  │
   │   CLS  quanto la pagina si sposta sotto gli occhi ≤ 0,1   │
   └───────────────────────────────────────────────────────────┘

   L'ORDINE IN CUI SI LAVORA, SEMPRE
     1. MISURARE  sul campo, non solo in laboratorio
     2. TROVARE IL COLLO DI BOTTIGLIA  un solo elemento spiega
        quasi sempre l'LCP; un solo gestore spiega l'INP
     3. CORREGGERE quello, e solo quello
     4. RIMISURARE  e verificare che il numero sia sceso davvero
     5. IMPEDIRE IL RITORNO  budget in CI
```

---

# Parte A — Basi Assolute

---

## A1. Cosa significa "veloce", e per chi

> **Analogia:** un ristorante. Non conta quanto ci mette il cuoco: conta quando arriva il piatto al tavolo, e se il cameriere risponde quando alzi la mano. Il tempo che il cuoco misura in cucina e quello che il cliente vive al tavolo sono due numeri diversi — e solo il secondo decide se il cliente torna.

```
"IL SITO È VELOCE SUL MIO COMPUTER" NON È UN DATO.
  Il tuo computer ha un processore recente, memoria abbondante, una
  connessione in fibra e la cache già calda. Chi visita il sito ha
  spesso un telefono di tre anni fa su una rete mobile instabile, e
  la prima visita ha la cache vuota.

  ➜ Ogni misura va fatta almeno una volta con:
      · CPU rallentata 4× (DevTools → Performance → CPU throttling)
      · rete "Slow 4G"
      · cache disabilitata
    Se il numero regge lì, regge ovunque.
```

```
LE DUE FAMIGLIE DI DATI, ED ENTRAMBE SERVONO
  LABORATORIO (Lighthouse, DevTools)  una misura riproducibile in
    condizioni controllate. ✅ diagnostica: dice COSA è lento.
    ❌ non dice cosa vivono gli utenti veri.
  CAMPO (RUM, CrUX)  le misure raccolte dai browser degli utenti
    reali. ✅ è la verità. ❌ non spiega la causa da sola.

  ⚠ Un punteggio Lighthouse di 95 con il campo a 4 secondi di LCP
    significa che stai misurando una macchina che non esiste. Il
    contrario — laboratorio brutto, campo buono — capita quando la
    prima visita è lenta ma quasi tutti tornano con la cache piena.
```

```
PERCHÉ CONTA, IN TERMINI CONCRETI
  · gli utenti abbandonano: la probabilità di uscita cresce
    rapidamente con i secondi di attesa
  · i Core Web Vitals sono un segnale di ranking dichiarato da Google
  · una pagina più leggera consuma meno batteria e meno traffico —
    e per una parte degli utenti il traffico si paga
  ⚠ Le percentuali precise cambiano da studio a studio e da settore
    a settore: misura le TUE, correlando i tuoi dati sul campo con
    le tue conversioni, invece di citare numeri altrui.
```

---

## A2. I Core Web Vitals

```
LCP — Largest Contentful Paint
  Quando l'elemento più grande dell'area visibile finisce di essere
  disegnato. È il momento in cui l'utente pensa "la pagina c'è".
  ✅ ≤ 2,5 s   ⚠ 2,5-4 s   ❌ > 4 s
  Quasi sempre è l'immagine principale, un video di copertina o un
  blocco di testo grande.

INP — Interaction to Next Paint
  Dal momento in cui l'utente interagisce a quando il browser
  disegna la risposta visiva. Considera TUTTE le interazioni della
  visita e riporta (circa) la peggiore.
  ✅ ≤ 200 ms  ⚠ 200-500 ms  ❌ > 500 ms
  Ha sostituito FID nel 2024: FID misurava solo il RITARDO del primo
  input, cioè la parte più facile.

CLS — Cumulative Layout Shift
  Quanto il contenuto si sposta senza che l'utente lo abbia chiesto.
  Non è un tempo: è un punteggio.
  ✅ ≤ 0,1   ⚠ 0,1-0,25   ❌ > 0,25
  È la metrica che misura la frustrazione: il pulsante che si sposta
  mentre lo stai premendo.
```

```
LE METRICHE DI SUPPORTO, CHE SERVONO A DIAGNOSTICARE
  TTFB   Time To First Byte — la parte server della latenza. Se è
    alto, tutto il resto parte in ritardo e non c'è ottimizzazione
    frontend che rimedi. ✅ ≤ 800 ms
  FCP    First Contentful Paint — il primo pixel di contenuto.
    Se FCP è buono e LCP no, il problema è l'elemento grande.
  TBT    Total Blocking Time — quanto il main thread è rimasto
    occupato oltre i 50 ms per task. È il migliore predittore
    dell'INP disponibile in laboratorio.

⚠ IL PUNTEGGIO LIGHTHOUSE (0-100) È UNA SINTESI PESATA, NON UNA
  METRICA. Inseguire il numero porta a ottimizzare ciò che pesa nel
  calcolo invece di ciò che l'utente sente. Si guardano le metriche;
  il punteggio è un riassunto per chi non le guarda.
```

---

## A3. Misurare prima di cambiare

```powershell
# LABORATORIO — Lighthouse da riga di comando, riproducibile
pnpm dlx lighthouse https://esempio.it `
  --preset=desktop --output=json --output-path=./rapporto.json

# Su mobile (il predefinito) e con tre esecuzioni, perché una sola
# misura ha una varianza notevole
pnpm dlx lighthouse https://esempio.it --output=html --view
```

```typescript
// CAMPO — la libreria ufficiale, tre righe che valgono più di
// qualunque strumento di laboratorio
import { onLCP, onINP, onCLS, onTTFB, type Metric } from 'web-vitals'

function invia(metrica: Metric) {
  const corpo = JSON.stringify({
    nome: metrica.name,
    valore: metrica.value,
    valutazione: metrica.rating, // 'good' | 'needs-improvement' | 'poor'
    // `attribution` dice QUALE elemento o QUALE gestore: senza,
    // sai che è lento ma non cosa
    dettaglio: metrica.attribution,
    percorso: location.pathname,
    connessione: (navigator as { connection?: { effectiveType?: string } }).connection
      ?.effectiveType,
  })

  // sendBeacon sopravvive alla chiusura della pagina: con fetch la
  // richiesta verrebbe annullata proprio quando serve
  navigator.sendBeacon('/api/metriche', corpo)
}

onLCP(invia)
onINP(invia)
onCLS(invia)
onTTFB(invia)
```

```
COME SI LEGGONO I DATI SUL CAMPO
  ⚠ MAI LA MEDIA. Una media di 2 s può nascondere che il 25% degli
    utenti aspetta 6 secondi. Si usa il 75° PERCENTILE — è quello
    che usano anche i Core Web Vitals: "tre utenti su quattro hanno
    almeno questa esperienza".
  Si segmenta per: dispositivo (mobile contro desktop), tipo di
  connessione, pagina, paese. Il problema è quasi sempre concentrato
  in un segmento, e la media di tutti lo nasconde.
```

---

## A4. Il percorso critico di rendering

```
   COSA FA IL BROWSER, IN ORDINE, E DOVE SI FERMA

   1. riceve l'HTML e comincia ad analizzarlo
   2. incontra <link rel="stylesheet">
        → SCARICA E ASPETTA: il CSS BLOCCA il rendering, perché
          senza non sa come disegnare nulla
   3. incontra <script src>
        → SCARICA E ASPETTA: blocca anche l'ANALISI dell'HTML,
          perché lo script potrebbe scrivere nel documento
   4. costruisce il DOM e il CSSOM, li unisce nell'albero di
      rendering
   5. layout (dove va ogni cosa) → paint (di che colore) →
      compositing (in quale ordine)

   ⚠ Il punto 3 è il più costoso: uno script sincrono nell'head
     ferma tutto, e la pagina resta bianca.
```

```html
<!-- ❌ Ogni script sincrono ferma l'analisi dell'HTML -->
<head>
  <script src="/analytics.js"></script>
  <script src="/app.js"></script>
</head>

<!-- ✅ defer: scarica in parallelo, esegue DOPO l'analisi, e
     mantiene l'ORDINE fra gli script. È il predefinito ragionevole. -->
<head>
  <script src="/app.js" defer></script>
  <!-- async: esegue appena è pronto, in ordine imprevedibile.
       Solo per script indipendenti da tutto, come le statistiche -->
  <script src="/analytics.js" async></script>

  <!-- I moduli ES sono deferred per natura: `type="module"` non ha
       bisogno di `defer` -->
  <script type="module" src="/app.js"></script>
</head>
```

```
LE TRE REGOLE DEL PERCORSO CRITICO
  1. IL CSS DEL PRIMO SCHERMO va inline nell'head (o comunque
     servito subito); il resto si carica dopo. Un foglio di stile da
     200 kB per una pagina che ne usa 8 blocca il rendering per il
     tempo di scaricarli tutti.
  2. NESSUNO SCRIPT SINCRONO nell'head. `defer` come predefinito,
     `async` solo per ciò che è davvero indipendente.
  3. IL PRIMO HTML DEVE CONTENERE QUALCOSA. Una pagina che è un
     `<div id="root"></div>` vuoto ha l'LCP dopo il download del
     JavaScript, la sua esecuzione, la richiesta dei dati e il
     rendering: quattro attese in fila.
```

---

## A5. Immagini e font: i due pesi maggiori

```html
<!-- ❌ Il caso peggiore: nessuna dimensione, un solo formato, una
     sola risoluzione, e nessuna priorità dichiarata -->
<img src="/copertina.jpg" alt="Copertina">

<!-- ✅ Ogni attributo risolve un problema preciso -->
<img
  src="/copertina-800.jpg"
  srcset="/copertina-400.avif 400w, /copertina-800.avif 800w, /copertina-1600.avif 1600w"
  sizes="(max-width: 600px) 100vw, 800px"
  width="800" height="450"
  alt="Vista della sala principale"
  fetchpriority="high"
>
```

```
COSA FA CIASCUNO
  width e height   riservano lo spazio PRIMA che l'immagine arrivi:
    senza, il contenuto sotto salta quando carica → CLS.
    ⚠ Servono anche quando il CSS ridimensiona: il browser usa il
      rapporto per calcolare l'altezza.
  srcset + sizes   il browser sceglie la risoluzione giusta per lo
    schermo e la densità: su un telefono non scarica l'immagine da
    1600 px.
  AVIF/WebP        30-50% più leggeri di JPEG a parità di qualità.
    Con <picture> si dà il ripiego per i browser vecchi.
  fetchpriority="high"  sull'immagine LCP: dice al browser di
    scaricarla prima delle altre. È spesso il singolo intervento
    più efficace sull'LCP.
  loading="lazy"   sulle immagini SOTTO la piega. ⚠ MAI
    sull'immagine LCP: la ritarderebbe di proposito.
```

```css
/* I FONT: tre problemi e tre soluzioni */

/* 1. Il testo invisibile mentre il font carica (FOIT) */
@font-face {
  font-family: 'Inter';
  src: url('/font/inter.woff2') format('woff2');
  /* swap: mostra subito il font di ripiego, poi sostituisce.
     Il testo si legge da subito. */
  font-display: swap;
  /* Solo i caratteri che servono davvero: un font completo pesa
     anche dieci volte il sottoinsieme latino */
  unicode-range: U+0000-00FF, U+0131, U+0152-0153;
}

/* 2. Lo spostamento quando il font vero sostituisce il ripiego */
@font-face {
  font-family: 'Inter fallback';
  src: local('Arial');
  /* Queste metriche allineano il ripiego al font vero: la
     sostituzione non sposta più il testo → niente CLS */
  size-adjust: 107%;
  ascent-override: 90%;
  descent-override: 22%;
}

body { font-family: 'Inter', 'Inter fallback', sans-serif; }
```

```html
<!-- 3. Il font viene scoperto tardi, perché è dentro il CSS.
     Il preload lo anticipa. ⚠ crossorigin è OBBLIGATORIO sui font,
     anche dallo stesso dominio: senza, il browser scarica DUE volte. -->
<link rel="preload" href="/font/inter.woff2" as="font" type="font/woff2" crossorigin>
```

---

# Parte B — Comprensione Profonda

---

## B1. LCP: trovare l'elemento e le sue quattro fasi

```javascript
// Il primo passo non è ottimizzare: è sapere QUALE elemento è
new PerformanceObserver((elenco) => {
  const ultimo = elenco.getEntries().at(-1)
  console.log('LCP:', ultimo.startTime, ultimo.element)
}).observe({ type: 'largest-contentful-paint', buffered: true })
```

```
L'LCP SI SCOMPONE IN QUATTRO FASI, E OGNUNA HA CURE DIVERSE

  1. TTFB                    dal clic al primo byte
  2. RITARDO DI CARICAMENTO  dal primo byte all'inizio del download
                             della risorsa LCP
  3. TEMPO DI CARICAMENTO    il download della risorsa
  4. RITARDO DI RENDERING    dal download completato al disegno

  ⚠ Il ritardo di CARICAMENTO è quasi sempre la fase più grande, e
    quasi sempre viene ignorata. Significa che il browser ha
    scoperto TARDI quale immagine gli serviva: perché era in un CSS
    (background-image), o perché arriva da JavaScript.
```

```
LE CURE, PER FASE
  TTFB alto        → B7: cache, database, CDN
  RITARDO DI CARICAMENTO
    · l'immagine LCP in un <img> nell'HTML, non in un background CSS
      né inserita da JavaScript
    · fetchpriority="high" su quell'immagine
    · <link rel="preload"> se è dentro un componente caricato pigro
    · MAI loading="lazy" sull'immagine LCP
  TEMPO DI CARICAMENTO
    · AVIF/WebP, srcset con le dimensioni giuste, compressione
    · CDN vicina all'utente
  RITARDO DI RENDERING
    · niente contenuto nascosto in attesa di JavaScript
    · font con font-display: swap
    · evitare che l'elemento LCP dipenda da una richiesta di dati
```

```html
<!-- ❌ Il caso peggiore: l'immagine LCP è uno sfondo CSS. Il
     browser deve scaricare il CSS, analizzarlo, calcolare quale
     regola si applica, e solo allora scopre l'URL -->
<div class="copertina"></div>
<style>.copertina { background-image: url('/copertina.jpg'); }</style>

<!-- ✅ Nell'HTML: il preload scanner del browser la trova prima
     ancora di aver finito di analizzare la pagina -->
<img src="/copertina.avif" width="1600" height="900" alt="…" fetchpriority="high">
```

---

## B2. INP: il costo di ogni interazione

```
   OGNI INTERAZIONE HA TRE PARTI, E TUTTE CONTANO

   clic ──► [ritardo di input] ──► [elaborazione] ──► [presentazione] ──► pixel
            il main thread è      i gestori di       layout, paint,
            occupato: l'evento    evento girano      compositing
            aspetta

   INP = il tempo totale, dalla prima all'ultima.
   ⚠ Il RITARDO è spesso la parte maggiore, e non dipende dal
     gestore: dipende da cos'altro stava facendo il main thread.
     Ottimizzare il gestore di un pulsante lento non serve, se il
     ritardo viene da uno script di terze parti che gira in quel
     momento.
```

```javascript
// Trovare le interazioni lente, con l'elemento che le ha causate
new PerformanceObserver((elenco) => {
  for (const voce of elenco.getEntries()) {
    if (voce.duration > 200) {
      console.warn('interazione lenta', {
        durata: voce.duration,
        tipo: voce.name,
        elemento: voce.target,
        // La differenza fra processingStart e startTime È il ritardo
        ritardo: voce.processingStart - voce.startTime,
        elaborazione: voce.processingEnd - voce.processingStart,
      })
    }
  }
}).observe({ type: 'event', durationThreshold: 200, buffered: true })
```

```javascript
// ❌ Tutto il lavoro prima del rendering: l'utente non vede nulla
//    finché non è finito
pulsante.addEventListener('click', async () => {
  const risultato = elaboraDiecimilaRighe(dati)  // 400 ms
  aggiornaInterfaccia(risultato)
})

// ✅ Prima il riscontro visivo, poi il lavoro pesante
pulsante.addEventListener('click', async () => {
  mostraCaricamento()  // l'utente vede subito che è successo qualcosa

  // Cede il controllo al browser, che disegna. scheduler.yield() è
  // la forma moderna e mantiene la priorità del task; setTimeout(0)
  // è il ripiego, ma finisce in fondo alla coda.
  await (globalThis.scheduler?.yield?.() ?? new Promise((r) => setTimeout(r, 0)))

  const risultato = elaboraDiecimilaRighe(dati)
  aggiornaInterfaccia(risultato)
})
```

```
LE CINQUE CAUSE PIÙ FREQUENTI DI UN INP ALTO
  1. UN GESTORE CHE FA TROPPO — validazione, ricalcolo e rendering
     tutti insieme
  2. UN RE-RENDER TROPPO GRANDE — in React, uno stato in cima
     all'albero che ridisegna mezza pagina
  3. UNO SCRIPT DI TERZE PARTI che occupa il main thread proprio
     mentre l'utente interagisce
  4. TROPPI LISTENER, o listener registrati in un ciclo
  5. LAYOUT SINCRONO FORZATO — leggere una proprietà geometrica
     subito dopo averne scritta un'altra (vedi B5)
```

---

## B3. CLS: perché la pagina salta

```
IL PUNTEGGIO = frazione dell'area visibile spostata × distanza dello
spostamento, sommato su tutta la visita.

⚠ NON contano gli spostamenti entro 500 ms da un'interazione
  dell'utente: aprire un menù a fisarmonica sposta il contenuto, ed
  è esattamente ciò che l'utente ha chiesto.
```

```
LE CINQUE CAUSE, IN ORDINE DI FREQUENZA
  1. IMMAGINI SENZA DIMENSIONI  il browser non sa quanto spazio
     riservare, e quando l'immagine arriva spinge giù tutto
  2. ANNUNCI O WIDGET INSERITI  uno spazio che compare dopo
  3. FONT che sostituiscono il ripiego con metriche diverse
  4. CONTENUTO INSERITO SOPRA quello esistente (una barra di avviso
     aggiunta dopo il caricamento)
  5. ANIMAZIONI SU PROPRIETÀ CHE CAUSANO LAYOUT (width, height, top)
     invece che su transform
```

```css
/* 1. Il rapporto d'aspetto riserva lo spazio anche senza
      width/height nell'HTML */
.copertina {
  aspect-ratio: 16 / 9;
  width: 100%;
  /* Impedisce all'immagine di deformarsi mentre carica */
  object-fit: cover;
}

/* 2. Lo spazio per un widget si riserva PRIMA, con un'altezza
      minima che corrisponde a quella reale */
.contenitore-annuncio { min-height: 250px; }

/* 4. Un avviso che compare deve stare in overlay, non spingere:
      position: fixed non partecipa al flusso */
.avviso { position: fixed; inset-block-start: 0; inset-inline: 0; }

/* 5. transform e opacity sono le UNICHE due proprietà che il
      compositor gestisce senza layout né paint */
.pannello {
  transform: translateY(-100%);
  transition: transform 200ms ease-out;
}
.pannello.aperto { transform: translateY(0); }
```

```javascript
// Trovare CHI sposta: senza questo si tira a indovinare
new PerformanceObserver((elenco) => {
  for (const voce of elenco.getEntries()) {
    if (!voce.hadRecentInput && voce.value > 0.01) {
      console.warn('spostamento', voce.value, voce.sources?.map((s) => s.node))
    }
  }
}).observe({ type: 'layout-shift', buffered: true })
```

---

## B4. Il main thread: long task e come spezzarli

> **Analogia:** un unico sportello che fa tutto: emette biglietti, risponde al telefono e riordina l'archivio. Mentre riordina l'archivio per trenta secondi, chi è in fila aspetta — anche chi voleva solo un'informazione da cinque secondi.

```
IL MAIN THREAD FA TUTTO: eseguire JavaScript, calcolare il layout,
disegnare, rispondere agli eventi. Un task che dura più di 50 ms è
un LONG TASK: durante quel tempo nessuna interazione può essere
servita.
  · a 60 fps il browser ha 16,6 ms per fotogramma
  · un task da 300 ms significa 18 fotogrammi persi e un'interfaccia
    che sembra bloccata
```

```javascript
// LA STRATEGIA 1 — spezzare, cedendo il controllo
async function elaboraTutto(elementi) {
  const risultati = []
  let inizioBlocco = performance.now()

  for (const elemento of elementi) {
    risultati.push(elabora(elemento))

    // Si cede ogni 50 ms, non ogni N elementi: il costo per
    // elemento varia, il tempo no
    if (performance.now() - inizioBlocco > 50) {
      await (globalThis.scheduler?.yield?.() ?? new Promise((r) => setTimeout(r, 0)))
      inizioBlocco = performance.now()
    }
  }

  return risultati
}
```

```javascript
// LA STRATEGIA 2 — spostare fuori dal main thread, quando il lavoro
// è puro calcolo e non tocca il DOM
const lavoratore = new Worker(new URL('./calcolo.worker.ts', import.meta.url), {
  type: 'module',
})

export function calcolaInSottofondo(dati) {
  return new Promise((risolvi, rifiuta) => {
    const canale = new MessageChannel()
    canale.port1.onmessage = ({ data }) => (data.errore ? rifiuta(data.errore) : risolvi(data))
    // ⚠ Il passaggio COPIA i dati: su array grandi il costo della
    //   copia può superare il guadagno. Con un ArrayBuffer si usa il
    //   TRASFERIMENTO, che è istantaneo ma svuota l'originale.
    lavoratore.postMessage(dati, [canale.port2])
  })
}
```

```
LA STRATEGIA 3 — NON FARE IL LAVORO
  Spesso la soluzione migliore non è spezzare né spostare: è
  chiedersi perché si stanno elaborando diecimila righe nel browser.
   · l'ordinamento e il filtro possono stare sul server, che ha un
     indice
   · la lista lunga può essere virtualizzata: si disegnano venti
     righe, non diecimila
   · il calcolo può essere memorizzato in cache invece di ripetuto
```

---

## B5. Rendering: layout, paint e compositor

```
   LE TRE FASI, IN ORDINE DI COSTO
   LAYOUT (reflow)  calcola posizione e dimensione di ogni elemento.
     La più costosa: una modifica in cima può ricalcolare tutto.
     La causano: width, height, margin, padding, top, left, font-size…
   PAINT            riempie i pixel. Costosa su aree grandi.
     La causano: color, background, box-shadow, border-radius…
   COMPOSITING      compone i livelli già disegnati. Quasi gratis, e
     avviene sulla GPU.
     La causano SOLO: transform e opacity.

   ➜ Animare `left` costa layout + paint + composite a ogni
     fotogramma. Animare `transform` costa solo composite.
```

```javascript
// ❌ IL LAYOUT SINCRONO FORZATO (layout thrashing) — il difetto di
//    rendering più comune, e il meno visibile leggendo il codice
for (const elemento of elementi) {
  // LEGGE una proprietà geometrica → il browser DEVE calcolare il
  // layout adesso, perché la scrittura precedente lo ha invalidato
  const altezza = elemento.offsetHeight
  elemento.style.height = `${altezza * 2}px` // SCRIVE → invalida
}
// Con cento elementi sono cento ricalcoli completi del layout.

// ✅ Separare le letture dalle scritture: un solo ricalcolo
const altezze = elementi.map((e) => e.offsetHeight)   // tutte le letture
elementi.forEach((e, i) => (e.style.height = `${altezze[i] * 2}px`)) // tutte le scritture
```

```
LE PROPRIETÀ CHE FORZANO IL LAYOUT QUANDO LE LEGGI
  offsetTop/Left/Width/Height · clientTop/Left/Width/Height
  scrollTop/Left/Width/Height · getBoundingClientRect()
  getComputedStyle() · window.scrollY

LE ALTRE LEVE
  content-visibility: auto  il browser salta layout e paint per ciò
    che è fuori schermo. Su una pagina lunga è un guadagno grande,
    e costa una riga. ⚠ Va accompagnata da `contain-intrinsic-size`
    con un'altezza stimata, altrimenti la barra di scorrimento salta.
  will-change: transform  promuove l'elemento a un livello proprio.
    ⚠ Ogni livello costa memoria: si applica al momento del bisogno
    e si rimuove dopo, non si lascia su venti elementi.
```

---

## B6. Resource hints e speculation rules

```html
<!-- I quattro suggerimenti, dal più leggero al più aggressivo -->

<!-- 1. Risolve il DNS in anticipo: pochi millisecondi, costo zero -->
<link rel="dns-prefetch" href="https://cdn.esempio.it">

<!-- 2. Apre anche la connessione TCP e il TLS: 100-300 ms
     risparmiati. ⚠ Costa una connessione: massimo 2-3 origini, e
     solo quelle da cui scarichi DAVVERO qualcosa di critico -->
<link rel="preconnect" href="https://cdn.esempio.it" crossorigin>

<!-- 3. Scarica ORA una risorsa che servirà FRA POCO in questa
     pagina. `as` è obbligatorio: senza, il browser non sa la
     priorità e può scaricarla due volte -->
<link rel="preload" href="/font/inter.woff2" as="font" type="font/woff2" crossorigin>

<!-- 4. Scarica a bassa priorità qualcosa che servirà nella PROSSIMA
     pagina -->
<link rel="prefetch" href="/dashboard.js" as="script">
```

```html
<!-- Speculation Rules: il browser prepara — o addirittura RENDE —
     la pagina successiva prima che l'utente ci clicchi -->
<script type="speculationrules">
{
  "prerender": [{
    "where": { "href_matches": "/prodotti/*" },
    // "moderate" = al passaggio del mouse; "eager" preparerebbe
    // troppo. La navigazione diventa istantanea.
    "eagerness": "moderate"
  }],
  "prefetch": [{
    "where": { "href_matches": "/*" },
    "eagerness": "conservative"
  }]
}
</script>
```

```
⚠ I SUGGERIMENTI SONO A COSTO NON NULLO, E ABUSARNE PEGGIORA
  · dieci `preload` competono per la banda con ciò che serve ADESSO
  · un `preload` sbagliato (`as` mancante o errato) fa scaricare la
    risorsa DUE volte
  · il prerender esegue davvero la pagina: JavaScript, richieste,
    statistiche. Su una pagina che modifica lo stato è un problema —
    e va gestito con `document.prerendering`.
  ➜ Si aggiungono UNO ALLA VOLTA, misurando. Il rapporto Lighthouse
    segnala sia i preload mancanti sia quelli inutilizzati.
```

---

## B7. Prestazioni del server: TTFB e caching

```
IL TTFB È IL PAVIMENTO DI TUTTO: se il primo byte arriva dopo 1,5 s,
l'LCP non può scendere sotto 1,5 s per quanto si ottimizzi il
frontend. Si scompone in:
  · latenza di rete (distanza fisica) → CDN
  · attesa in coda sul server → più istanze, o meno lavoro
  · generazione della risposta → query, template, chiamate esterne
```

```typescript
// La cache HTTP è la leva più efficace, e spesso non viene usata
import type { RequestHandler } from 'express'

export const cachePubblica: RequestHandler = (_richiesta, risposta, prossimo) => {
  risposta.setHeader(
    'Cache-Control',
    // stale-while-revalidate: per 60 s dopo la scadenza la CDN serve
    // la copia vecchia SUBITO e la aggiorna in sottofondo. L'utente
    // non aspetta mai il ricalcolo.
    'public, max-age=300, stale-while-revalidate=60, stale-if-error=86400',
  )
  prossimo()
}
```

```
I QUATTRO LIVELLI DI CACHE, DAL PIÙ ECONOMICO
  1. BROWSER      zero rete. Asset con impronta: max-age=31536000, immutable
  2. CDN          la risposta non arriva mai al tuo server
  3. APPLICAZIONE Redis, per i calcoli costosi (tutorial_12 §B9)
  4. DATABASE     query e indici (tutorial_12 §B1-B2)

  ⚠ `stale-if-error` è la difesa più sottovalutata: se il server
    cade, la CDN continua a servire l'ultima copia buona per 24 ore.
    Un guasto diventa invisibile agli utenti.

LE ALTRE LEVE DEL TTFB
  · compressione brotli sui testi
  · HTTP/2 o HTTP/3: multiplexing, e con HTTP/3 nessun blocco di
    testa della coda a livello TCP
  · lo streaming dell'HTML: inviare l'inizio del documento mentre il
    resto si genera — il browser comincia a scaricare CSS e font
    mentre il server è ancora al lavoro (vedi tutorial_21)
```

---

## B8. Script di terze parti

```
UNO SCRIPT DI TERZE PARTI GIRA CON I PRIVILEGI DELLA TUA PAGINA E
SUL TUO MAIN THREAD. È spesso la causa maggiore di INP alto, e
quasi sempre nessuno lo misura perché "non è codice nostro".

  Un tag manager tipico porta: statistiche, mappe di calore, chat,
  test A/B, pixel pubblicitari. Ognuno scarica altro codice a
  cascata, e il totale supera facilmente il bundle dell'applicazione.
```

```
LE CINQUE MOSSE, IN ORDINE DI RESA
  1. INVENTARIO E RIMOZIONE  quanti script ci sono, chi li ha
     aggiunti, chi guarda ancora i dati che producono? Rimuoverne
     uno è l'ottimizzazione più efficace che esista, e la più
     trascurata.
  2. CARICAMENTO RITARDATO  la chat non serve nel primo secondo: si
     carica al primo movimento del mouse, al primo scorrimento, o
     dopo che la pagina è interattiva.
  3. FUORI DAL MAIN THREAD  Partytown esegue gli script di terze
     parti in un web worker. ⚠ Non funziona con tutti: quelli che
     toccano il DOM in modo complesso si rompono.
  4. ALTERNATIVE LEGGERE  molte statistiche si possono fare con
     poche decine di kilobyte invece di centinaia.
  5. MISURARE OGNUNO  DevTools → Performance → "Bottom-Up" filtrato
     per dominio dice quanto main thread consuma ciascuno.
```

```javascript
// Caricare al primo segnale di interesse, non all'avvio
function caricaAlPrimoContatto(url) {
  let caricato = false
  const carica = () => {
    if (caricato) return
    caricato = true
    const script = document.createElement('script')
    script.src = url
    script.async = true
    document.head.append(script)
  }

  // `once` rimuove il listener da solo; `passive` non blocca lo scroll
  for (const evento of ['pointerdown', 'keydown', 'scroll']) {
    addEventListener(evento, carica, { once: true, passive: true })
  }
  // E comunque dopo qualche secondo, per chi non interagisce
  setTimeout(carica, 5000)
}
```

---

## B9. Budget e monitoraggio continuo

```
UN BUDGET NON MISURATO NON ESISTE. Le prestazioni peggiorano di poco
a ogni rilascio, e nessuno se ne accorge finché non sono da rifare —
a quel punto la causa è distribuita su duecento commit.
```

```json
// lighthouse-budget.json — i limiti che la CI fa rispettare
[
  {
    "path": "/*",
    "timings": [
      { "metric": "largest-contentful-paint", "budget": 2500 },
      { "metric": "total-blocking-time", "budget": 200 },
      { "metric": "cumulative-layout-shift", "budget": 0.1 }
    ],
    "resourceSizes": [
      { "resourceType": "script", "budget": 170 },
      { "resourceType": "stylesheet", "budget": 50 },
      { "resourceType": "image", "budget": 400 },
      { "resourceType": "total", "budget": 800 }
    ],
    "resourceCounts": [{ "resourceType": "third-party", "budget": 5 }]
  }
]
```

```yaml
# In CI, su ogni pull request
- name: Lighthouse CI
  run: |
    pnpm dlx @lhci/cli autorun \
      --collect.url=http://localhost:3000 \
      --collect.numberOfRuns=3 \
      --assert.budgetsFile=./lighthouse-budget.json
```

```
⚠ TRE ESECUZIONI, NON UNA: la varianza di Lighthouse su una sola
  misura è alta, e un budget che fallisce a caso viene disattivato
  dopo tre giorni.

IL MONITORAGGIO SUL CAMPO È QUELLO CHE CONTA DAVVERO
  · web-vitals che invia a un endpoint proprio (vedi A3)
  · un cruscotto con il 75° percentile per metrica, segmentato per
    dispositivo e per pagina
  · un allarme quando una metrica peggiora oltre una soglia
  · l'annotazione dei rilasci sui grafici: quando LCP peggiora alle
    14:32, la riga verticale "rilascio v2.4.1 alle 14:30" è la
    diagnosi già fatta
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — LCP da 4,8 s a meno di 2,5 s

**Obiettivo:** trovare l'elemento LCP, scomporre il tempo in fasi e correggere la fase dominante.

```
# LA MISURA DI PARTENZA (mobile, CPU 4×, Slow 4G)
#   LCP    4,82 s      TTFB   0,62 s      FCP  1,10 s
#
# IL PRIMO PASSO — QUALE elemento è?
#   DevTools → Performance → il marcatore LCP, oppure:
#   new PerformanceObserver(l => console.log(l.getEntries().at(-1).element))
#     .observe({ type: 'largest-contentful-paint', buffered: true })
#   → <div class="eroe">  (un'immagine di sfondo CSS)
```

```
# LA SCOMPOSIZIONE IN FASI
#   TTFB                     620 ms   (13%)
#   ritardo di caricamento  2.740 ms  (57%)  ← il colpevole
#   tempo di caricamento    1.180 ms  (24%)
#   ritardo di rendering      280 ms   (6%)
#
# La lettura: 2,7 secondi PRIMA che il download cominci. Il browser
# ha scoperto tardi quale immagine gli serviva.
```

```html
<!-- LA CAUSA -->
<div class="eroe"></div>
<link rel="stylesheet" href="/stili.css">   <!-- 180 kB -->
<style>
  /* Il browser deve: scaricare stili.css → analizzarlo → capire che
     questa regola si applica → SOLO ALLORA scoprire l'URL. Il
     preload scanner, che legge l'HTML in anticipo, non vede
     l'immagine perché non è nell'HTML. */
  .eroe { background-image: url('/eroe.jpg'); height: 60vh; }
</style>
```

```html
<!-- LA CORREZIONE — quattro interventi, uno per fase -->

<!-- 1. RITARDO DI CARICAMENTO: l'immagine nell'HTML, dove il
     preload scanner la trova subito, con priorità alta -->
<img
  src="/eroe-1600.avif"
  srcset="/eroe-800.avif 800w, /eroe-1600.avif 1600w, /eroe-2400.avif 2400w"
  sizes="100vw"
  width="1600" height="900"
  alt="Vista della sala principale"
  fetchpriority="high"
  class="eroe"
>

<!-- 2. TEMPO DI CARICAMENTO: AVIF invece di JPEG (−58%), e la
     risoluzione giusta per lo schermo grazie a srcset -->

<!-- 3. TTFB: preconnect verso la CDN, e cache sulla risposta HTML -->
<link rel="preconnect" href="https://cdn.esempio.it" crossorigin>

<!-- 4. RITARDO DI RENDERING: il CSS del primo schermo inline, il
     resto caricato senza bloccare -->
<style>/* solo le regole del primo schermo, ~4 kB */</style>
<link rel="stylesheet" href="/stili.css" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="/stili.css"></noscript>
```

```
# IL RISULTATO
#   TTFB                     410 ms  (−34%)
#   ritardo di caricamento    90 ms  (−97%)  ← il preload scanner la
#                                              trova immediatamente
#   tempo di caricamento     620 ms  (−47%)  ← AVIF + dimensione giusta
#   ritardo di rendering     180 ms  (−36%)
#   LCP                     1,30 s   ← da 4,82 s
#
# ⚠ L'intervento più efficace non è stato comprimere l'immagine: è
#   stato renderla VISIBILE al browser prima. È il caso più comune,
#   e quello che si trascura di più.
```

---

### Esercizio 2 — INP da 620 ms a meno di 200 ms

**Obiettivo:** una tabella con filtro: ogni carattere digitato blocca l'interfaccia.

```javascript
// IL CODICE DA CORREGGERE
campoRicerca.addEventListener('input', (evento) => {
  const termine = evento.target.value.toLowerCase()

  // 12.000 righe, filtrate a ogni carattere
  const filtrate = tutteLeRighe.filter(
    (r) =>
      r.nome.toLowerCase().includes(termine) ||
      r.email.toLowerCase().includes(termine) ||
      r.note.toLowerCase().includes(termine),
  )

  // E ridisegnate tutte
  tabella.innerHTML = filtrate.map((r) => `<tr><td>${r.nome}</td>…</tr>`).join('')
})
```

```
# LA DIAGNOSI
#   PerformanceObserver su 'event' con durationThreshold: 200
#     ritardo di input        40 ms
#     elaborazione           480 ms  ← il filtro e la stringa HTML
#     presentazione          100 ms  ← 12.000 <tr> da disegnare
#     INP                    620 ms
#
#   Tre problemi distinti:
#    1. il filtro gira a OGNI carattere, anche mentre si digita
#    2. `toLowerCase()` viene chiamato 36.000 volte per battuta
#    3. si disegnano 12.000 righe, di cui l'utente ne vede 20
```

```javascript
// LA CORREZIONE 1 — separare il riscontro immediato dal lavoro
// pesante, e non filtrare a ogni battuta
let attesa
campoRicerca.addEventListener('input', (evento) => {
  const termine = evento.target.value

  // Il campo si aggiorna subito: l'utente vede ciò che digita, e
  // questo è tutto ciò che l'INP misura per questa interazione
  clearTimeout(attesa)
  attesa = setTimeout(() => applicaFiltro(termine), 150)
})

// LA CORREZIONE 2 — l'indice si prepara UNA volta, non a ogni tasto
const indice = tutteLeRighe.map((r) => ({
  riga: r,
  cercabile: `${r.nome} ${r.email} ${r.note}`.toLowerCase(),
}))

function applicaFiltro(termine) {
  const cercato = termine.toLowerCase()
  const filtrate = cercato ? indice.filter((v) => v.cercabile.includes(cercato)) : indice
  disegna(filtrate.map((v) => v.riga))
}
```

```javascript
// LA CORREZIONE 3 — disegnare solo ciò che si vede
// (virtualizzazione): 20 righe invece di 12.000
function disegna(righe) {
  const altezzaRiga = 44
  const primaVisibile = Math.floor(contenitore.scrollTop / altezzaRiga)
  const quante = Math.ceil(contenitore.clientHeight / altezzaRiga) + 5 // margine

  // Il contenitore mantiene l'altezza TOTALE: la barra di
  // scorrimento resta corretta
  spaziatore.style.height = `${righe.length * altezzaRiga}px`

  const visibili = righe.slice(primaVisibile, primaVisibile + quante)

  // replaceChildren invece di innerHTML: niente analisi di HTML,
  // niente rischio di XSS, e un solo aggiornamento del DOM
  corpo.replaceChildren(...visibili.map(creaRiga))
  corpo.style.transform = `translateY(${primaVisibile * altezzaRiga}px)`
}
```

```
# IL RISULTATO
#   ritardo di input      30 ms
#   elaborazione          18 ms  (−96%)
#   presentazione         22 ms  (−78%)
#   INP                   70 ms  ← da 620 ms
#
# ⚠ L'intervento decisivo è il TERZO: disegnare 12.000 nodi costa al
#   browser anche quando il JavaScript è istantaneo. Su liste lunghe
#   la virtualizzazione non è un'ottimizzazione avanzata — è la
#   condizione perché la pagina funzioni.
```

---

### Esercizio 3 — CLS da 0,42 a meno di 0,1

**Obiettivo:** una pagina di articolo che "salta" tre volte durante il caricamento.

```
# LA DIAGNOSI — quali nodi si spostano
#   new PerformanceObserver(l => {
#     for (const v of l.getEntries())
#       if (!v.hadRecentInput) console.warn(v.value, v.sources.map(s => s.node))
#   }).observe({ type: 'layout-shift', buffered: true })
#
#   0,21  <img class="copertina">     ← nessuna dimensione
#   0,14  <div id="annuncio">          ← inserito dopo, spinge giù
#   0,07  <body>                       ← il font sostituisce il ripiego
#   ────
#   0,42
```

```html
<!-- CORREZIONE 1 (0,21) — le dimensioni intrinseche riservano lo
     spazio prima che l'immagine arrivi -->
<img src="/copertina.avif" width="1200" height="675" alt="…" class="copertina">
```

```css
/* E il CSS mantiene il rapporto quando l'immagine è responsiva:
   senza aspect-ratio, width:100% + height:auto ricalcola l'altezza
   solo quando l'immagine è arrivata */
.copertina {
  width: 100%;
  height: auto;
  aspect-ratio: 16 / 9;
}

/* CORREZIONE 2 (0,14) — lo spazio dell'annuncio è riservato PRIMA,
   con l'altezza reale che occuperà */
#annuncio {
  min-height: 250px;
  display: grid;
  place-items: center;
}
/* Un segnaposto visivo evita anche il "buco bianco" percepito */
#annuncio:empty::before {
  content: '';
  inline-size: 100%;
  block-size: 250px;
  background: var(--colore-segnaposto);
}
```

```css
/* CORREZIONE 3 (0,07) — il ripiego con le metriche allineate al
   font vero: la sostituzione non sposta più nulla */
@font-face {
  font-family: 'Merriweather fallback';
  src: local('Georgia');
  size-adjust: 103%;
  ascent-override: 92%;
  descent-override: 24%;
  line-gap-override: 0%;
}

body {
  font-family: 'Merriweather', 'Merriweather fallback', serif;
}
```

```
# IL RISULTATO
#   copertina   0,21 → 0,00
#   annuncio    0,14 → 0,00
#   font        0,07 → 0,01
#   CLS         0,42 → 0,01
#
# COME SI TROVANO I VALORI DI size-adjust E DEGLI OVERRIDE
#   Non a tentativi: si calcolano dalle metriche dei due font
#   (unitsPerEm, ascender, descender). Lo strumento
#   `fontaine` o il generatore di Malte Ubl lo fanno in automatico,
#   e Next.js lo applica da sé con next/font.
#
# ⚠ IL CLS SI MISURA SU TUTTA LA VISITA, non solo al caricamento.
#   Uno spostamento causato da un caricamento pigro a metà pagina
#   conta quanto uno iniziale: va provato SCORRENDO, non solo
#   aprendo.
```

---

## C2. Mini-progetto: da Lighthouse 60 a 90+

L'esercizio chiave del modulo: portare un'applicazione reale da un punteggio insufficiente a uno buono, con interventi mirati e misurati.

```
# LA SITUAZIONE DI PARTENZA (mobile, Slow 4G, CPU 4×)
#   Performance  61
#   LCP  4,2 s │ TBT  890 ms │ CLS  0,28 │ TTFB  1,1 s
#   JS 1.240 kB │ CSS 180 kB │ immagini 2,1 MB │ 14 script di terzi
```

```
LA PROCEDURA, IN SEI FASI

1. MISURARE E FISSARE IL PUNTO DI PARTENZA
   Tre esecuzioni di Lighthouse, e i dati sul campo se esistono. Il
   numero di partenza va SALVATO: senza, non si potrà dire se gli
   interventi hanno funzionato.

2. TROVARE I COLLI DI BOTTIGLIA, NON OTTIMIZZARE A CASO
   · LCP  → quale elemento, e quale delle quattro fasi domina
   · TBT  → DevTools → Performance → i long task, e chi li causa
   · CLS  → PerformanceObserver → quali nodi si spostano
   · peso → vite-bundle-visualizer, e il pannello Network per
     immagini e terze parti

3. ORDINARE PER RAPPORTO FRA EFFETTO E COSTO
   Quasi sempre l'ordine è: immagini → terze parti → JavaScript →
   CSS → server. Le prime due danno il 70% del risultato con il 20%
   del lavoro.

4. INTERVENIRE UNO ALLA VOLTA, MISURANDO OGNI VOLTA
   Cinque modifiche insieme e un miglioramento di 20 punti non
   dicono quale ha funzionato — e se una ha PEGGIORATO, non si vede.

5. VERIFICARE SUL CAMPO
   Il laboratorio migliora sempre. Il campo è la prova.

6. IMPEDIRE IL RITORNO
   Budget in CI, e monitoraggio con allarme.
```

```
# GLI INTERVENTI, CON L'EFFETTO MISURATO
#
# 1. IMMAGINI  AVIF + srcset + dimensioni + lazy sotto la piega
#    2,1 MB → 340 kB          LCP 4,2 → 2,9 s     +9 punti
# 2. TERZE PARTI  rimossi 6 script inutilizzati, gli altri caricati
#    al primo contatto
#    14 → 5 script            TBT 890 → 420 ms    +11 punti
# 3. JAVASCRIPT  moment → date-fns, icone per percorso, rotte pigre
#    1.240 → 310 kB           TBT 420 → 180 ms    +8 punti
# 4. CLS  dimensioni sulle immagini, spazio per l'annuncio, metriche
#    del font di ripiego
#    0,28 → 0,02                                   +5 punti
# 5. CSS  critico inline, il resto senza bloccare
#    FCP 1,8 → 0,9 s                               +3 punti
# 6. SERVER  cache CDN con stale-while-revalidate, brotli
#    TTFB 1,1 → 0,3 s         LCP 2,9 → 1,6 s     +6 punti
#
#   RISULTATO   Performance 61 → 93
#   LCP 1,6 s │ TBT 180 ms │ CLS 0,02 │ TTFB 0,3 s
```

```
# LA VERIFICA, IN ORDINE
# 1. TRE ESECUZIONI, non una: la varianza è alta
# 2. SU MOBILE con CPU 4× e Slow 4G, non su desktop in fibra
# 3. IL CAMPO conferma il laboratorio dopo 28 giorni di raccolta
# 4. IL BUDGET è in CI e fallisce se si supera
# 5. NESSUNA REGRESSIONE FUNZIONALE: la suite di test è verde
#    (le ottimizzazioni rompono le cose: il lazy loading applicato
#     all'immagine sbagliata, l'HTML critico che dimentica una regola)
# 6. IL CLS SI PROVA SCORRENDO tutta la pagina, non solo aprendola
# 7. L'ACCESSIBILITÀ non è peggiorata: axe pulito, e il percorso
#    principale completabile con la sola tastiera
# 8. IL MONITORAGGIO sul campo è attivo, con i rilasci annotati
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Dati di laboratorio contro dati sul campo

```
QUANDO I DUE NON COINCIDONO, LA RISPOSTA È QUASI SEMPRE UNA DI QUESTE

  LABORATORIO BUONO, CAMPO CATTIVO
   · gli utenti veri hanno dispositivi più lenti della simulazione
   · una parte del traffico arriva da un paese lontano dal server
   · gli script di terze parti si comportano diversamente in
     produzione (consenso, test A/B, personalizzazione)
   · Lighthouse misura una pagina, gli utenti ne visitano altre

  LABORATORIO CATTIVO, CAMPO BUONO
   · quasi tutti tornano con la cache piena, e la misura di
     laboratorio è sempre a cache vuota
   · gli utenti reali interagiscono poco, quindi l'INP resta basso
     nonostante il TBT alto

  ➜ IL CAMPO VINCE SEMPRE. Il laboratorio serve a spiegare il campo,
    non a sostituirlo.
```

```
CrUX (Chrome UX Report) è il dato sul campo raccolto da Google:
gratuito, aggregato su 28 giorni, disponibile per qualunque sito
con traffico sufficiente. È anche ciò che alimenta il segnale di
ranking, quindi è il numero che conta ufficialmente.
  ⚠ Ha tre limiti: solo Chrome, solo utenti che hanno acconsentito,
    e nessuna segmentazione fine. Un RUM proprio (A3) li supera
    tutti e tre, e i due si affiancano.
```

---

## D2. Prestazioni percepite

> **Analogia:** la fila alla cassa. Se vedi lo scontrino stamparsi riga per riga, l'attesa è tollerabile. Se il cassiere sparisce nel retro senza dire nulla, tre minuti sembrano dieci. Il tempo misurato è lo stesso; l'esperienza no.

```
LE CINQUE TECNICHE CHE CAMBIANO L'ESPERIENZA SENZA CAMBIARE I
MILLISECONDI

1. SCHELETRI, non spinner. Uno scheletro con la forma del contenuto
   dice cosa sta arrivando, e non produce lo spostamento che un
   contenitore vuoto causerebbe al riempirsi.
2. AGGIORNAMENTO OTTIMISTICO. L'interfaccia mostra il risultato
   PRIMA della conferma del server, e torna indietro se fallisce.
   Un "mi piace" deve sembrare istantaneo. ⚠ Solo per operazioni che
   falliscono raramente e il cui annullamento è innocuo — mai per un
   pagamento.
3. PRECARICAMENTO SULL'INTENZIONE. Al passaggio del mouse su un
   link, i dati della pagina successiva sono già in viaggio: fra il
   passaggio e il clic passano 150-300 ms, che sono gratis.
4. TRANSIZIONI. `startViewTransition` rende visibile la continuità
   fra due stati: il cambiamento sembra più fluido anche se dura
   uguale.
5. STREAMING. Mostrare la parte pronta invece di aspettare il tutto.
   È il principio dietro Suspense e l'HTML in streaming.
```

```javascript
// L'aggiornamento ottimistico, con l'annullamento che quasi tutti
// dimenticano di scrivere
async function alternaPreferito(id) {
  const precedente = stato.preferiti.has(id)

  // 1. l'interfaccia cambia SUBITO
  precedente ? stato.preferiti.delete(id) : stato.preferiti.add(id)
  aggiorna()

  try {
    const risposta = await fetch(`/api/preferiti/${id}`, {
      method: precedente ? 'DELETE' : 'PUT',
    })
    if (!risposta.ok) throw new Error(String(risposta.status))
  } catch {
    // 2. se fallisce, si torna allo stato precedente E si dice
    //    perché: un ripristino silenzioso confonde più di un errore
    precedente ? stato.preferiti.add(id) : stato.preferiti.delete(id)
    aggiorna()
    mostraAvviso('Non è stato possibile salvare. Riprova.')
  }
}
```

---

## D3. Memoria e perdite

```
UNA PERDITA DI MEMORIA IN UNA SPA NON SI VEDE SUBITO: si vede dopo
venti minuti d'uso, quando la scheda occupa un gigabyte e ogni
interazione diventa lenta. È il tipo di problema che i test non
trovano, perché i test durano secondi.

LE QUATTRO CAUSE, IN ORDINE DI FREQUENZA
  1. LISTENER NON RIMOSSI  un componente si smonta ma il suo
     listener su `window` resta, e trattiene tutto ciò che la
     closure cattura
  2. TIMER NON FERMATI  setInterval che continua dopo lo smontaggio
  3. OSSERVATORI NON DISCONNESSI  IntersectionObserver,
     ResizeObserver, MutationObserver
  4. CACHE SENZA LIMITE  una Map che cresce a ogni navigazione
```

```javascript
// AbortController risolve tre delle quattro cause con una riga sola
function montaComponente() {
  const controller = new AbortController()
  const { signal } = controller

  addEventListener('resize', suRidimensionamento, { signal })
  addEventListener('scroll', suScorrimento, { signal, passive: true })
  fetch('/api/dati', { signal })

  const osservatore = new IntersectionObserver(suIntersezione)
  osservatore.observe(elemento)

  return () => {
    // Rimuove TUTTI i listener e annulla il fetch in una volta
    controller.abort()
    osservatore.disconnect()
  }
}
```

```
COME SI TROVA UNA PERDITA
  1. DevTools → Memory → Heap snapshot subito dopo il caricamento
  2. usare l'applicazione per qualche minuto (navigare, aprire e
     chiudere le stesse viste dieci volte)
  3. forzare la garbage collection, poi un secondo snapshot
  4. "Comparison": cosa è cresciuto e non è mai sceso
  ⚠ Il segnale più chiaro sono i "Detached HTMLElement": nodi
    rimossi dal DOM che qualcosa trattiene ancora.
```

---

## D4. Prestazioni e accessibilità si aiutano

```
NON SONO IN CONFLITTO — quasi sempre lo stesso intervento migliora
entrambe, e questo è il motivo per non trattarle come due progetti
separati.

  MENO JAVASCRIPT  → più veloce, e funziona anche quando lo script
    fallisce (rete instabile, blocco degli script)
  HTML SEMANTICO   → meno codice per ottenere lo stesso risultato, e
    navigabile con la tastiera e con uno screen reader senza ARIA
  DIMENSIONI SULLE IMMAGINI  → niente CLS, e niente contenuto che si
    sposta sotto il puntatore di chi ha difficoltà motorie
  `prefers-reduced-motion` → meno animazioni da comporre, e
    accessibile a chi soffre di disturbi vestibolari
  FONT LEGGIBILI E CARICATI BENE → font-display: swap significa
    testo leggibile subito, per tutti
```

```css
/* Rispettare la preferenza di sistema costa cinque righe, e vale
   sia come accessibilità sia come prestazione */
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

```
⚠ IL CASO IN CUI CONFLIGGONO DAVVERO, E COME SI RISOLVE
  `content-visibility: auto` salta il rendering di ciò che è fuori
  schermo — e con esso lo salta anche la ricerca nella pagina e, su
  alcune combinazioni, lo screen reader. Va applicata a sezioni
  grandi e non critiche, e va PROVATA con la tastiera e con la
  ricerca del browser prima di lasciarla.
```

---

## D5. Quando smettere di ottimizzare

```
L'OTTIMIZZAZIONE HA RENDIMENTI DECRESCENTI, E OGNI INTERVENTO HA UN
COSTO DI MANUTENZIONE.
  · da LCP 5 s a 2,5 s: gli utenti lo sentono, i numeri cambiano
  · da 2,5 s a 2,0 s: qualche utente lo sente
  · da 2,0 s a 1,8 s: nessuno lo sente, e il codice è più complesso

LE QUATTRO DOMANDE PER DECIDERE SE CONTINUARE
  1. Il numero è nella fascia BUONA sul CAMPO (non in laboratorio)?
     Se sì, il lavoro successivo ha un valore molto minore.
  2. C'è un segmento di utenti ancora in difficoltà? Spesso la media
     è buona e il 25% su rete mobile no: quello è il lavoro che resta.
  3. L'intervento successivo aggiunge COMPLESSITÀ permanente? Una
     cache in più, un livello in più, un caso limite in più: si paga
     a ogni modifica futura.
  4. C'è qualcosa di più importante da fare? Un bug, una
     funzionalità attesa, un rischio di sicurezza. Le prestazioni
     sono una qualità fra le altre, non l'unica.

⚠ E LA REGOLA CHE VIENE PRIMA DI TUTTE: non ottimizzare ciò che non
  hai misurato. Il tempo speso su un'ipotesi sbagliata è tempo perso
  due volte — quello dell'intervento, e quello della complessità che
  resta.
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
PERFORMANCE WEB — Mappa dei concetti

MISURARE
├── laboratorio (Lighthouse) diagnostica · campo (RUM, CrUX) è la verità
├── mai la media: 75° percentile, segmentato per dispositivo e pagina
├── sempre con CPU 4× e Slow 4G: "sul mio computer" non è un dato
└── tre esecuzioni, non una: la varianza è alta

I TRE VITALS
├── LCP ≤ 2,5 s   quando compare il contenuto principale
├── INP ≤ 200 ms  reattività di OGNI interazione
├── CLS ≤ 0,1     quanto la pagina si sposta da sola
└── supporto: TTFB ≤ 800 ms · FCP · TBT (predice l'INP in laboratorio)

PERCORSO CRITICO
├── il CSS blocca il rendering, lo script sincrono anche l'analisi
├── defer come predefinito, async solo per ciò che è indipendente
├── il CSS del primo schermo inline, il resto senza bloccare
└── il primo HTML deve contenere qualcosa: un div vuoto costa
      quattro attese in fila

LCP — quattro fasi
├── TTFB · ritardo di caricamento · caricamento · ritardo di rendering
├── il RITARDO DI CARICAMENTO domina quasi sempre: il browser ha
│     scoperto tardi l'immagine
├── immagine LCP in un <img> nell'HTML, con fetchpriority="high"
└── mai loading="lazy" sull'immagine LCP

INP — tre parti
├── ritardo · elaborazione · presentazione
├── il ritardo dipende da cos'altro occupa il main thread
├── prima il riscontro visivo, poi il lavoro: cedere con
│     scheduler.yield()
└── liste lunghe: virtualizzare, non disegnare diecimila nodi

CLS
├── dimensioni o aspect-ratio su ogni immagine
├── spazio riservato per annunci e widget
├── ripiego del font con size-adjust e override delle metriche
├── animare transform e opacity, mai width/height/top
└── si misura su tutta la visita: provare SCORRENDO

MAIN THREAD E RENDERING
├── long task > 50 ms: l'interfaccia non risponde
├── spezzare · spostare in un worker · o non fare il lavoro
├── layout → paint → compositing, in ordine di costo
└── layout sincrono forzato: separare letture e scritture

RETE E SERVER
├── TTFB è il pavimento di tutto
├── cache: browser → CDN → applicazione → database
├── stale-while-revalidate e stale-if-error
├── preconnect (2-3 origini) · preload con `as` · speculation rules
└── terze parti: inventariare, rimuovere, ritardare, misurare

BUDGET
├── in CI con tre esecuzioni, altrimenti fallisce a caso
├── monitoraggio sul campo con allarme e rilasci annotati
└── smettere quando il campo è buono e il costo supera il beneficio
```

---

## Checklist di competenze

**Parte A — Basi**

- [ ] Misuri con CPU rallentata, rete lenta e cache vuota
- [ ] Distingui dati di laboratorio e dati sul campo, e sai a cosa servono
- [ ] Conosci le soglie di LCP, INP e CLS e cosa misura ciascuno
- [ ] Sai perché il punteggio Lighthouse non è una metrica
- [ ] Usi il 75° percentile e non la media
- [ ] Sai cosa blocca il rendering e cosa blocca anche l'analisi dell'HTML
- [ ] Sai quando usare `defer` e quando `async`
- [ ] Conosci il ruolo di ogni attributo di un `<img>` ottimizzato
- [ ] Sai perché `crossorigin` è obbligatorio nel preload di un font

**Parte B — Comprensione**

- [ ] Sai identificare l'elemento LCP e scomporre il tempo in quattro fasi
- [ ] Sai perché un'immagine di sfondo CSS ritarda l'LCP
- [ ] Sai scomporre l'INP in ritardo, elaborazione e presentazione
- [ ] Cedi il controllo al browser prima di un lavoro lungo
- [ ] Conosci le cinque cause del CLS e la correzione di ciascuna
- [ ] Sai calcolare le metriche di un font di ripiego
- [ ] Sai cos'è un long task e le tre strategie per affrontarlo
- [ ] Sai quali proprietà causano layout, quali paint, quali solo compositing
- [ ] Riconosci un layout sincrono forzato e sai separare letture e scritture
- [ ] Usi i resource hints con parsimonia e sai perché abusarne peggiora
- [ ] Conosci i quattro livelli di cache e a cosa serve `stale-if-error`
- [ ] Sai misurare quanto main thread consuma ogni script di terze parti
- [ ] Imposti un budget in CI con tre esecuzioni

**Parte C — Pratica**

- [ ] Hai trovato l'elemento LCP prima di intervenire
- [ ] Hai corretto la fase dominante, non quella più facile
- [ ] Hai ridotto l'INP separando riscontro e lavoro, e virtualizzando
- [ ] Hai identificato i nodi che spostano il layout
- [ ] Hai eseguito i sei passi dell'audit misurando un intervento alla volta
- [ ] Hai verificato sul campo, non solo in laboratorio

**Parte D — Esperto**

- [ ] Sai spiegare le divergenze fra laboratorio e campo
- [ ] Conosci i limiti di CrUX e perché un RUM proprio li supera
- [ ] Sai quando un aggiornamento ottimistico è appropriato e quando no
- [ ] Trovi una perdita di memoria con due heap snapshot
- [ ] Usi un `AbortController` per la pulizia dei listener
- [ ] Sai in quali casi prestazioni e accessibilità confliggono davvero
- [ ] Sai decidere quando smettere di ottimizzare

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Misurare sul proprio computer | CPU veloce, fibra, cache calda: dati inutili | CPU 4×, Slow 4G, cache vuota |
| Guardare solo Lighthouse | Misura una macchina che non esiste | Dati sul campo, 75° percentile |
| Usare la media | Nasconde il segmento che sta male | Percentili, segmentati |
| Inseguire il punteggio | Si ottimizza il calcolo, non l'esperienza | Guardare le metriche |
| Ottimizzare senza misurare | Tempo perso due volte: intervento e complessità | Misurare, trovare il collo di bottiglia, poi agire |
| Cinque modifiche insieme | Non si sa quale ha funzionato, né se una ha peggiorato | Una alla volta, misurando |
| Script sincrono nell'head | Ferma l'analisi dell'HTML: pagina bianca | `defer`, o `async` se indipendente |
| Immagine LCP come sfondo CSS | Scoperta tardi: il ritardo di caricamento esplode | `<img>` nell'HTML con `fetchpriority="high"` |
| `loading="lazy"` sull'immagine LCP | La ritarda di proposito | Lazy solo sotto la piega |
| Immagini senza `width`/`height` | Il contenuto salta al caricamento | Dimensioni o `aspect-ratio` |
| Font senza `font-display` | Testo invisibile mentre carica | `swap`, e ripiego con metriche allineate |
| Preload di un font senza `crossorigin` | Il browser lo scarica due volte | `crossorigin` sempre sui font |
| Dieci `preload` | Competono per la banda con ciò che serve adesso | Uno alla volta, misurando |
| `preconnect` verso otto origini | Ogni connessione costa | Massimo 2-3, solo per risorse critiche |
| Tutto il lavoro nel gestore di evento | L'utente non vede nulla per centinaia di ms | Riscontro subito, poi `scheduler.yield()` |
| Disegnare diecimila righe | Il costo è del browser, non del JavaScript | Virtualizzazione |
| Leggere e scrivere geometrie alternate | Layout sincrono forzato a ogni iterazione | Tutte le letture, poi tutte le scritture |
| Animare `width`, `height`, `top` | Layout + paint a ogni fotogramma | `transform` e `opacity` |
| `will-change` su venti elementi | Ogni livello costa memoria | Solo al bisogno, e rimuoverlo dopo |
| Script di terze parti mai inventariati | Spesso la causa maggiore dell'INP | Contare, rimuovere, ritardare, misurare |
| Nessun budget in CI | Peggiora di poco a ogni rilascio | Budget con tre esecuzioni |
| Listener non rimossi | Perdita di memoria: la scheda cresce e rallenta | `AbortController` con `signal` |
| Ottimizzare oltre la fascia buona | Complessità permanente senza beneficio percepito | Verificare il campo, e fermarsi |

---

## Troubleshooting rapido

**LCP alto ma l'immagine è piccola e ottimizzata**
- Causa: ritardo di *caricamento* — il browser la scopre tardi (sfondo CSS, inserita da JavaScript, dentro un componente pigro)
- Fix: `<img>` nell'HTML con `fetchpriority="high"`, o `preload`

**LCP peggiorato dopo aver aggiunto il lazy loading**
- Causa: `loading="lazy"` applicato anche all'immagine principale
- Fix: lazy solo sotto la piega; sull'LCP `fetchpriority="high"`

**INP alto solo su alcune interazioni**
- Causa: un gestore specifico, o un re-render troppo ampio
- Fix: `PerformanceObserver` su `event` con `durationThreshold` per identificare l'elemento

**INP alto ma i gestori sono veloci**
- Causa: il *ritardo* di input — il main thread è occupato da altro, spesso terze parti
- Fix: profilo delle prestazioni durante l'interazione; ritardare gli script non essenziali

**CLS basso in Lighthouse e alto sul campo**
- Causa: gli spostamenti avvengono scorrendo, e Lighthouse non scorre
- Fix: provare scorrendo tutta la pagina; riservare lo spazio dei contenuti caricati pigri

**Il font sposta il testo nonostante `font-display: swap`**
- Causa: le metriche del ripiego non corrispondono
- Fix: `size-adjust` e gli override calcolati sulle metriche dei due font

**La pagina è veloce al primo caricamento e lenta dopo l'uso**
- Causa: perdita di memoria — listener, timer o osservatori non ripuliti
- Fix: due heap snapshot a confronto; cercare i "Detached HTMLElement"

**TTFB alto solo per alcuni utenti**
- Causa: distanza dal server, o cache CDN che non copre quella regione
- Fix: segmentare i dati sul campo per paese; CDN con più punti di presenza

**Lo scorrimento è a scatti**
- Causa: listener non passivi, o layout durante lo scroll
- Fix: `{ passive: true }`; animare solo `transform`; `content-visibility: auto`

**Il budget in CI fallisce a caso**
- Causa: una sola esecuzione di Lighthouse, che ha una varianza alta
- Fix: `numberOfRuns: 3`, e soglie con un margine ragionevole

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_18_pwa_tecnologie_avanzate.md` | Service worker e caching offline: il livello sopra la cache HTTP |
| `tutorial_19_troubleshooting.md` | Diagnosi in produzione quando i numeri peggiorano all'improvviso |
| `tutorial_16_build_tools_deploy.md` | Da dove vengono i byte: bundle, splitting, budget di dimensione |
| `tutorial_12_database_web.md` | Il TTFB che nasce da una query senza indice |
| `tutorial_21_rsc_server_driven_ui.md` | Streaming dell'HTML e meno JavaScript sul client |
| `tutorial_22_rate_limiting_edge.md` | Calcolo vicino all'utente per abbattere la latenza |

---

## Risorse di riferimento

**Riferimenti primari:** [web.dev — Core Web Vitals](https://web.dev/articles/vitals) e le guide dedicate a [LCP](https://web.dev/articles/optimize-lcp), [INP](https://web.dev/articles/optimize-inp) e [CLS](https://web.dev/articles/optimize-cls) · [MDN — Performance](https://developer.mozilla.org/docs/Web/Performance) · [Chrome DevTools — Performance](https://developer.chrome.com/docs/devtools/performance)

**Approfondimenti:** [Browser rendering — Paul Lewis](https://developers.google.com/web/fundamentals/performance/rendering) · [High Performance Browser Networking](https://hpbn.co/), gratuito e ancora il riferimento sulla rete · [Chrome UX Report](https://developer.chrome.com/docs/crux)

**Strumenti:** [PageSpeed Insights](https://pagespeed.web.dev/) (laboratorio e campo insieme) · [WebPageTest](https://www.webpagetest.org/) per la cascata dettagliata · [web-vitals](https://github.com/GoogleChrome/web-vitals) · [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci) · [Squoosh](https://squoosh.app/) per le immagini · [fontaine](https://github.com/unjs/fontaine) per le metriche dei font di ripiego

---

> **Fine del Tutorial 17 — Performance Web**
>
> Prossimo tutorial: `tutorial_18_pwa_tecnologie_avanzate.md`
