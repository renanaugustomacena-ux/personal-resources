# Tutorial 15 — Testing Web: Dal Principiante all'Esperto

> **Companion a:** `15-testing-web.md`
> **Scope:** cosa rende utile un test, Vitest, test di componenti con Testing Library, mock e MSW, test di integrazione con database reale, end-to-end con Playwright, stabilità e attese, accessibilità, snapshot e regressione visiva, contract testing, testing in CI, strategia
> **Prerequisiti:** `tutorial_06_typescript.md` — tipi; `tutorial_07_react.md` — componenti; `tutorial_12_database_web.md` — Testcontainers; `tutorial_11_api_design.md` — conformità al contratto
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** Vitest 3 · Testing Library · MSW 2 · Playwright 1.5x · Testcontainers

---

## Indice Generale

- [Mappa concettuale](#mappa-concettuale)
- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Cosa rende utile un test](#a1-cosa-rende-utile-un-test)
  - [A2. Vitest: il primo test, e come si scrive bene](#a2-vitest-il-primo-test-e-come-si-scrive-bene)
  - [A3. Testare i componenti dal punto di vista dell'utente](#a3-testare-i-componenti-dal-punto-di-vista-dellutente)
  - [A4. Mock: quando servono e quando fanno danni](#a4-mock-quando-servono-e-quando-fanno-danni)
  - [A5. Il primo test end-to-end con Playwright](#a5-il-primo-test-end-to-end-con-playwright)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. La piramide, il trofeo, e cosa scegliere davvero](#b1-la-piramide-il-trofeo-e-cosa-scegliere-davvero)
  - [B2. I selettori che non si rompono](#b2-i-selettori-che-non-si-rompono)
  - [B3. Test instabili: le cinque cause e le loro cure](#b3-test-instabili-le-cinque-cause-e-le-loro-cure)
  - [B4. MSW: intercettare la rete invece dei moduli](#b4-msw-intercettare-la-rete-invece-dei-moduli)
  - [B5. Test di integrazione con un database vero](#b5-test-di-integrazione-con-un-database-vero)
  - [B6. Isolamento e dati di prova](#b6-isolamento-e-dati-di-prova)
  - [B7. Copertura: cosa misura e cosa non misura](#b7-copertura-cosa-misura-e-cosa-non-misura)
  - [B8. Snapshot e regressione visiva](#b8-snapshot-e-regressione-visiva)
  - [B9. Accessibilità e contract testing](#b9-accessibilità-e-contract-testing)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: suite di test completa per la dashboard](#c2-mini-progetto-suite-di-test-completa-per-la-dashboard)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Testing in CI: velocità e affidabilità](#d1-testing-in-ci-velocità-e-affidabilità)
  - [D2. Test basati su proprietà](#d2-test-basati-su-proprietà)
  - [D3. Mutation testing: chi controlla i test](#d3-mutation-testing-chi-controlla-i-test)
  - [D4. Testare il tempo, la casualità e la rete](#d4-testare-il-tempo-la-casualità-e-la-rete)
  - [D5. Quando NON scrivere un test](#d5-quando-non-scrivere-un-test)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   COSA VERIFICO                        CON COSA                COSTO
   ─────────────────────────────────────────────────────────────────
   una funzione pura                    Vitest                  ~1 ms
   un componente con le sue interazioni Testing Library         ~50 ms
   un endpoint con il database vero     Supertest + Testcontainers ~1 s
   un percorso utente completo          Playwright              ~5-30 s
   il contratto fra due servizi         Pact / OpenAPI          ~1 s

   ┌──────────────────────────────────────────────────────────┐
   │  UN TEST UTILE                                           │
   │   · fallisce quando il comportamento si rompe            │
   │   · NON fallisce quando cambia solo l'implementazione    │
   │   · dice cosa è rotto senza bisogno del debugger         │
   │   · dà lo stesso risultato ogni volta                    │
   └──────────────────────────────────────────────────────────┘

   LE TRE DOMANDE PRIMA DI SCRIVERE UN TEST
     1. quale comportamento sto verificando, dal punto di vista di chi
        usa questo codice?
     2. se cambio l'implementazione lasciando il comportamento, il
        test deve restare verde?
     3. quando fallirà, saprò subito perché?
```

---

# Parte A — Basi Assolute

---

## A1. Cosa rende utile un test

> **Analogia:** il collaudo di un ponte. Non si verifica che i bulloni siano avvitati in senso orario: si verifica che il ponte regga il carico. Un collaudo che descrive il metodo di montaggio fallisce ogni volta che si cambia il metodo, e non dice niente sul fatto che il ponte stia in piedi.

```tsx
// ❌ UN TEST CHE VERIFICA L'IMPLEMENTAZIONE
it('chiama setState con il nuovo valore', () => {
  const setState = vi.fn()
  vi.spyOn(React, 'useState').mockReturnValue([0, setState])
  render(<Contatore />)
  fireEvent.click(screen.getByRole('button'))
  expect(setState).toHaveBeenCalledWith(1)
})
// Si rompe se passi a useReducer, anche se il contatore funziona
// ancora perfettamente. E resta verde se il numero non compare a
// schermo: verifica il meccanismo, non il risultato.
```

```tsx
// ✅ UN TEST CHE VERIFICA IL COMPORTAMENTO
it('incrementa il conteggio mostrato quando si preme il pulsante', async () => {
  const utente = userEvent.setup()
  render(<Contatore />)

  await utente.click(screen.getByRole('button', { name: /incrementa/i }))

  expect(screen.getByText('1')).toBeInTheDocument()
})
// Resta verde con useState, useReducer, un signal o una variabile
// globale. Fallisce se il numero non arriva sullo schermo — cioè
// esattamente quando l'utente se ne accorgerebbe.
```

```
LA REGOLA CHE RIASSUME TUTTO
  Un test verifica il CONTRATTO di ciò che prova, dal punto di vista
  di chi lo usa. Per una funzione, chi la usa è chi la chiama: input
  e output. Per un componente, è l'utente: cosa vede e cosa può fare.
  Per un endpoint, è il client: richiesta e risposta.

⚠ UN TEST CHE ASSERISCE CIÒ CHE UN MOCK È STATO ISTRUITO A
  RESTITUIRE NON È UN TEST. Verifica che il mock funzioni, e il mock
  funziona sempre. È il modo più comune di ottenere il 90% di
  copertura senza nessuna garanzia.

I CASI DA COPRIRE PER PRIMI, IN ORDINE
  1. ciò che fa perdere soldi o una causa: calcoli su denaro, date,
     permessi, quantità
  2. i valori limite: vuoto, zero, negativo, uno, molto grande
  3. gli errori: rete che cade, database non disponibile, timeout
  4. le regressioni: ogni bug corretto diventa un test
  La percentuale di copertura non è in questa lista.
```

---

## A2. Vitest: il primo test, e come si scrive bene

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'node', // 'jsdom' per i test di componenti
    globals: false,      // import espliciti: più chiaro e più portabile
    setupFiles: ['./test/setup.ts'],
    coverage: { provider: 'v8', reporter: ['text', 'lcov'] },
  },
})
```

```typescript
// src/fatturazione.test.ts — la struttura di un test leggibile
import { describe, it, expect } from 'vitest'
import { calcolaTotale } from './fatturazione.js'

describe('calcolaTotale', () => {
  it('somma le righe applicando la quantità', () => {
    // ORGANIZZA: i dati, espliciti nel test — chi legge non deve
    // andare a cercare una fixture in un altro file
    const righe = [
      { quantita: 2, prezzoUnitarioCentesimi: 1000 },
      { quantita: 3, prezzoUnitarioCentesimi: 500 },
    ]

    // AGISCI: una sola azione
    const totale = calcolaTotale(righe)

    // VERIFICA: sul risultato, non sui passaggi
    expect(totale).toBe(3500)
  })

  // I casi limite hanno lo stesso peso del caso normale
  it('restituisce zero su un elenco vuoto', () => {
    expect(calcolaTotale([])).toBe(0)
  })

  it('rifiuta una quantità negativa invece di produrre un totale negativo', () => {
    expect(() => calcolaTotale([{ quantita: -1, prezzoUnitarioCentesimi: 100 }])).toThrow(
      /quantità/i,
    )
  })
})
```

```
IL NOME DEL TEST È DOCUMENTAZIONE
  ❌ it('funziona')
  ❌ it('test calcolaTotale')
  ✅ it('somma le righe applicando la quantità')
  ✅ it('restituisce zero su un elenco vuoto')
  Quando fallisce, il nome deve bastare a capire cosa è rotto: è
  l'unica cosa che si legge nell'output della CI.

LE MATCHER CHE CONTANO
  toBe            uguaglianza per identità (Object.is): primitivi
  toEqual         confronto ricorsivo per valore: oggetti e array
  toStrictEqual   come toEqual ma distingue undefined da assente
  toThrow         con una regex o una classe, mai nudo: `toThrow()`
                  passa per QUALUNQUE errore, anche un typo
  toMatchObject   verifica un sottoinsieme: utile sulle risposte API
```

---

## A3. Testare i componenti dal punto di vista dell'utente

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ModuloAccesso } from './ModuloAccesso.js'

describe('ModuloAccesso', () => {
  it('mostra un errore quando l’email non è valida', async () => {
    // userEvent simula l'interazione reale: focus, tastiera, eventi
    // intermedi. fireEvent lancia un evento sintetico e basta, e
    // lascia passare bug che l'utente incontrerebbe.
    const utente = userEvent.setup()
    render(<ModuloAccesso onInvio={vi.fn()} />)

    // I selettori sono quelli che userebbe una persona: l'etichetta,
    // il ruolo, il testo. Non le classi CSS.
    await utente.type(screen.getByLabelText(/email/i), 'non-una-email')
    await utente.click(screen.getByRole('button', { name: /accedi/i }))

    // findBy* aspetta la comparsa: niente attese arbitrarie
    expect(await screen.findByText(/email non valida/i)).toBeInTheDocument()
  })

  it('invia i dati quando il modulo è valido', async () => {
    const utente = userEvent.setup()
    const onInvio = vi.fn()
    render(<ModuloAccesso onInvio={onInvio} />)

    await utente.type(screen.getByLabelText(/email/i), 'mario@esempio.it')
    await utente.type(screen.getByLabelText(/password/i), 'password-lunga-e-valida')
    await utente.click(screen.getByRole('button', { name: /accedi/i }))

    expect(onInvio).toHaveBeenCalledWith({
      email: 'mario@esempio.it',
      password: 'password-lunga-e-valida',
    })
  })
})
```

```
LE TRE FAMIGLIE DI QUERY, E QUANDO USARLE
  getBy*    l'elemento c'è ORA. Fallisce subito se manca.
  queryBy*  può non esserci: l'unica che restituisce null, e quindi
            l'unica adatta a `expect(...).not.toBeInTheDocument()`
  findBy*   ASPETTA che compaia (Promise). Per tutto ciò che arriva
            dopo un'operazione asincrona.

⚠ `expect(screen.getByText('x')).not.toBeInTheDocument()` non
  funziona: getBy solleva PRIMA che l'assertion venga valutata.
  Serve queryBy.

L'ORDINE DI PREFERENZA DEI SELETTORI (dal più al meno robusto)
  1. getByRole con `name` — è ciò che vede anche uno screen reader:
     se il test passa, l'elemento è accessibile
  2. getByLabelText — per i campi di modulo
  3. getByText — per il contenuto visibile
  4. getByTestId — l'ultima risorsa, quando non c'è nient'altro
  ❌ container.querySelector('.btn-primary') — si rompe al primo
     ritocco del CSS e non dice nulla sull'esperienza reale
```

---

## A4. Mock: quando servono e quando fanno danni

```
UN MOCK SOSTITUISCE UNA DIPENDENZA. Ogni sostituzione allontana il
test dalla realtà: è un costo, e va pagato solo quando serve.

QUANDO SERVE
  ✅ la dipendenza è LENTA (rete, filesystem su file grandi)
  ✅ la dipendenza è NON DETERMINISTICA (data corrente, casualità)
  ✅ la dipendenza ha EFFETTI REALI (invia email, addebita una carta)
  ✅ serve provocare un caso difficile da ottenere (timeout, errore 500)

QUANDO NON SERVE, E FA DANNI
  ❌ funzioni pure: sostituirle nasconde i bug e non fa risparmiare
  ❌ il database, se puoi usarne uno vero (vedi B5): un mock del
     database non ha vincoli, transazioni né tipi
  ❌ i moduli interni della tua applicazione: se devi mockarli per
     testare, il problema è l'accoppiamento, non il test
```

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('invioNotifica', () => {
  beforeEach(() => {
    vi.restoreAllMocks() // ⚠ senza, i mock sopravvivono fra i test
  })

  it('registra un avviso quando il servizio email fallisce', async () => {
    // Si sostituisce il CONFINE esterno, non la logica interna
    const invia = vi.spyOn(servizioEmail, 'invia').mockRejectedValue(new Error('SMTP giù'))
    const avviso = vi.spyOn(registro, 'warn')

    // L'operazione NON deve fallire: una notifica persa non annulla
    // l'ordine. È questo il comportamento che il test protegge.
    await expect(notificaOrdine('ord_1')).resolves.toBeUndefined()

    expect(invia).toHaveBeenCalledOnce()
    expect(avviso).toHaveBeenCalledWith(
      expect.objectContaining({ idOrdine: 'ord_1' }),
      expect.stringMatching(/notifica/i),
    )
  })
})
```

```
IL MOCK CHE NON VERIFICA NULLA — l'anti-pattern più diffuso
  const db = { trovaUtente: vi.fn().mockResolvedValue({ id: 1, nome: 'Mario' }) }
  const risultato = await servizio.profilo(1, db)
  expect(risultato.nome).toBe('Mario')

  Questo test passa anche se `servizio.profilo` è
  `(id, db) => db.trovaUtente(id)`. Non verifica nessuna logica:
  verifica che il mock restituisca ciò che gli è stato detto.
  Se non c'è logica da verificare, il test non serve.
```

---

## A5. Il primo test end-to-end con Playwright

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  // Un fallimento su tre browser diversi è più informativo di uno solo
  projects: [
    { name: 'chromium', use: devices['Desktop Chrome'] },
    { name: 'firefox', use: devices['Desktop Firefox'] },
    { name: 'mobile', use: devices['iPhone 14'] },
  ],
  use: {
    baseURL: 'http://localhost:3000',
    // Le tracce solo al primo tentativo fallito: pesano, ma
    // contengono screenshot, rete e DOM di ogni passo
    trace: 'on-first-retry',
    video: 'retain-on-failure',
  },
  // ⚠ I retry SOLO in CI: in locale un test instabile deve
  //    fallire, altrimenti non lo si corregge mai
  retries: process.env['CI'] ? 2 : 0,
  webServer: {
    command: 'pnpm build && pnpm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env['CI'],
  },
})
```

```typescript
// e2e/accesso.spec.ts
import { test, expect } from '@playwright/test'

test('un utente registrato accede e vede la propria dashboard', async ({ page }) => {
  await page.goto('/accedi')

  // getByRole e getByLabel anche qui: gli stessi selettori dei test
  // di componente, per gli stessi motivi
  await page.getByLabel('Email').fill('mario@esempio.it')
  await page.getByLabel('Password').fill('password-di-prova')
  await page.getByRole('button', { name: 'Accedi' }).click()

  // Le expect di Playwright RIPROVANO finché non passano o scade il
  // timeout: non serve nessun waitForTimeout
  await expect(page).toHaveURL('/dashboard')
  await expect(page.getByRole('heading', { name: /benvenuto, mario/i })).toBeVisible()
})

test('le credenziali sbagliate mostrano un errore e restano sulla pagina', async ({ page }) => {
  await page.goto('/accedi')

  await page.getByLabel('Email').fill('mario@esempio.it')
  await page.getByLabel('Password').fill('sbagliata')
  await page.getByRole('button', { name: 'Accedi' }).click()

  await expect(page.getByRole('alert')).toContainText(/credenziali non valide/i)
  await expect(page).toHaveURL('/accedi')
})
```

---

# Parte B — Comprensione Profonda

---

## B1. La piramide, il trofeo, e cosa scegliere davvero

```
LA PIRAMIDE CLASSICA           IL "TROFEO" (Kent C. Dodds)
      /\  pochi E2E                  ▲   pochi E2E
     /  \ alcuni integrazione      ▄███▄ MOLTI di integrazione
    /____\ MOLTI unit               ███  alcuni unit
                                     █   analisi statica (TS, lint)

La piramide nasce quando i test di integrazione erano lentissimi.
Con Vitest, MSW e Testcontainers non lo sono più — e i test di
integrazione trovano una classe di bug che quelli unitari non
vedono: i pezzi che non si parlano.

⚠ NESSUNA DELLE DUE È UNA REGOLA. La forma giusta dipende da dove
  nascono i tuoi bug, e quello lo sai solo guardando i tuoi incidenti
  passati.
```

```
COSA DECIDE DAVVERO IL LIVELLO A CUI SCRIVERE UN TEST
  Quanto è LOGICA la cosa che verifichi?
    molta logica, poche dipendenze  → unitario, veloce e preciso
    poca logica, molte connessioni  → integrazione
  Quanto costa il fallimento?
    un percorso critico (pagamento, accesso, invio ordine)
    merita anche un E2E, perché è l'unico che verifica la catena
    completa — browser, rete, sessione, database.
  Quanto è instabile?
    un E2E fragile che fallisce a caso viene ignorato, e allora vale
    meno di zero: consuma tempo e nasconde i fallimenti veri.

LA PROPORZIONE CHE FUNZIONA IN PRATICA
  analisi statica  TypeScript strict + ESLint: prende gratis una
    classe intera di errori, e va contata come primo livello
  unitari         la logica di dominio: prezzi, date, permessi,
    validazioni, trasformazioni
  integrazione    ogni endpoint, ogni componente con stato
  E2E             5-15 percorsi, non 200. I percorsi che, se rotti,
    fanno perdere denaro o fiducia.
```

---

## B2. I selettori che non si rompono

```tsx
// ❌ I QUATTRO SELETTORI FRAGILI, in ordine di fragilità
container.querySelector('.btn.btn-primary')     // si rompe col CSS
container.querySelector('div > div > span')      // si rompe col markup
screen.getByText('Salva le modifiche')           // si rompe con la copy
page.locator('#root > div:nth-child(3) > button') // si rompe con tutto
```

```tsx
// ✅ IL RUOLO E IL NOME ACCESSIBILE: cambia il CSS, cambia il
//    markup, il test resta verde
import { screen, within } from '@testing-library/react'

screen.getByRole('button', { name: /salva/i })
screen.getByRole('textbox', { name: /email/i })
screen.getByRole('alert')
screen.getByRole('table', { name: /ordini recenti/i })

// Quando il ruolo non basta a distinguere, si restringe l'ambito
export async function eliminaRiga(utente: UserEvent) {
  const riga = screen.getByRole('row', { name: /ORD-2026-001/ })
  await utente.click(within(riga).getByRole('button', { name: /elimina/i }))
}

// L'ultima risorsa: un attributo dedicato al test, stabile per
// contratto. Va usato quando l'elemento non ha un ruolo sensato —
// un contenitore, un grafico su canvas.
//   page.getByTestId('grafico-fatturato')
```

```
IL VANTAGGIO NASCOSTO DI getByRole
  Se il test lo trova, l'elemento è nell'albero di accessibilità: ha
  un ruolo e un nome. Se NON lo trova, spesso il problema non è il
  test — è che l'elemento non è accessibile (un `<div onClick>`
  invece di un `<button>`, un input senza label). Il test di
  comportamento diventa così anche un test di accessibilità, senza
  costo aggiuntivo.

⚠ SUI TESTI VISIBILI USA LE REGEX, non l'uguaglianza esatta:
  /salva/i sopravvive a "Salva", "Salva modifiche" e "  Salva  ".
  Se il testo è tradotto, il test va scritto sull'identificativo
  della traduzione o sul ruolo, mai sulla stringa italiana.
```

---

## B3. Test instabili: le cinque cause e le loro cure

> **Analogia:** un allarme antincendio che suona a caso. Dopo la terza volta nessuno esce più dall'edificio — e il giorno dell'incendio vero l'allarme suona invano. Un test instabile non è un test debole: è un test dannoso, perché insegna a ignorare i fallimenti.

```
CAUSA 1 — ATTESE ARBITRARIE
  ❌ await page.waitForTimeout(2000)
  Troppo corto: fallisce su una macchina lenta. Troppo lungo:
  la suite dura un'ora. E non c'è un valore giusto.
  ✅ await expect(locator).toBeVisible()   ← riprova fino al timeout
  ✅ await page.waitForResponse('**/api/ordini')
  ✅ await screen.findByText(/…/)          ← nei test di componente

CAUSA 2 — STATO CONDIVISO FRA I TEST
  Il test B passa solo se A è girato prima; l'ordine cambia e crolla
  tutto. ✅ ogni test crea i propri dati con identificativi unici, e
  li elimina o annulla la transazione al termine.

CAUSA 3 — CONCORRENZA REALE
  Due test in parallelo scrivono la stessa riga.
  ✅ dati separati per worker, oppure serializzazione esplicita solo
  per i pochi test che la richiedono.

CAUSA 4 — TEMPO E FUSI ORARI
  Un test che passa fino alle 23:00 e fallisce dopo, o solo il 31
  del mese. ✅ orologio finto, e TZ fissato nella configurazione.

CAUSA 5 — ANIMAZIONI E CARICAMENTI PIGRI
  Il clic arriva mentre l'elemento si sta ancora muovendo.
  ✅ disattivare le animazioni nei test; Playwright aspetta già la
  stabilità dell'elemento, ma un'animazione infinita lo blocca.
```

```typescript
// La configurazione che elimina due cause in una volta
// e2e/fixture.ts
import { test as base } from '@playwright/test'

export const test = base.extend({
  page: async ({ page }, use) => {
    // Niente animazioni: gli elementi sono subito stabili
    await page.addStyleTag({
      content: `*, *::before, *::after {
        animation-duration: 0s !important;
        transition-duration: 0s !important;
      }`,
    })
    await use(page)
  },
})
```

```
COSA FARE CON UN TEST INSTABILE, IN ORDINE
  1. NON aggiungere un retry per farlo passare: nasconde il problema
  2. guardare la TRACCIA del fallimento (Playwright la registra):
     nove volte su dieci mostra l'attesa mancante
  3. correggere la causa
  4. se non si riesce subito, marcarlo `test.fixme` con un
     riferimento: un test disattivato e tracciato è onesto, un test
     che fallisce a caso non lo è

⚠ IL RETRY IN CI È UNA RETE DI SICUREZZA, NON UNA CURA. Se un test
  passa solo al secondo tentativo, va registrato e corretto: la CI
  deve dire quali test hanno avuto bisogno di retry.
```

---

## B4. MSW: intercettare la rete invece dei moduli

```typescript
// ❌ Mockare `fetch` o il modulo del client API significa testare
//    codice che in produzione non gira: URL, parsing, header e
//    gestione degli errori restano non verificati.

// ✅ MSW intercetta a livello di RETE: il codice esegue davvero il
//    suo fetch, e la risposta arriva dal handler
// test/msw/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/ordini', ({ request }) => {
    const url = new URL(request.url)
    const stato = url.searchParams.get('stato')

    return HttpResponse.json({
      elementi: [
        { id: 'ord_1', numero: 'ORD-2026-001', stato: stato ?? 'pagato', totaleCentesimi: 12_000 },
      ],
      paginazione: { limite: 20, haAltri: false },
    })
  }),

  http.post('/api/ordini', async ({ request }) => {
    const corpo = (await request.json()) as { righe: unknown[] }
    if (!corpo.righe?.length) {
      return HttpResponse.json({ title: 'Errore di validazione' }, { status: 422 })
    }
    return HttpResponse.json({ id: 'ord_2' }, { status: 201 })
  }),
]
```

```typescript
// test/setup.ts
import { setupServer } from 'msw/node'
import { beforeAll, afterEach, afterAll } from 'vitest'
import { handlers } from './msw/handlers.js'

export const server = setupServer(...handlers)

beforeAll(() => {
  // 'error' fa fallire il test su una chiamata non prevista: senza,
  // una richiesta dimenticata passa inosservata e il test verifica
  // meno di quanto sembra
  server.listen({ onUnhandledRequest: 'error' })
})

// ⚠ Senza questo, un override di un test si porta nel successivo
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

```tsx
// Nel singolo test si sovrascrive solo il caso che serve
import { http, HttpResponse } from 'msw'
import { server } from '../setup.js'

it('mostra un messaggio quando il server non risponde', async () => {
  server.use(http.get('/api/ordini', () => HttpResponse.error()))

  render(<ElencoOrdini />)

  expect(await screen.findByRole('alert')).toHaveTextContent(/non è stato possibile/i)
})
```

```
IL VANTAGGIO DECISIVO DI MSW  gli stessi handler girano nei test
  unitari (node), nei test di componente (jsdom), in Playwright e
  nello sviluppo con un service worker. Una definizione sola, che
  non diverge — e che documenta come si comporta l'API.
```

---

## B5. Test di integrazione con un database vero

```typescript
// Un mock del database verifica che il mock funzioni. I vincoli, le
// transazioni, i tipi e i piani di esecuzione esistono solo in un
// database reale: quelli sono i bug che i test devono trovare.
import { PostgreSqlContainer, type StartedPostgreSqlContainer } from '@testcontainers/postgresql'
import { beforeAll, afterAll } from 'vitest'

let container: StartedPostgreSqlContainer

beforeAll(async () => {
  container = await new PostgreSqlContainer('postgres:17-alpine')
    // tmpfs: il database sta in RAM, e i test diventano molto più veloci
    .withTmpFs({ '/var/lib/postgresql/data': 'rw,size=512m' })
    .start()

  process.env['DATABASE_URL'] = container.getConnectionUri()
  await eseguiMigrazioni()
}, 120_000)

afterAll(async () => {
  await container?.stop()
})
```

```typescript
// I test che solo un database vero permette
import { describe, it, expect } from 'vitest'
import request from 'supertest'

describe('POST /api/ordini', () => {
  it('rifiuta un ordine quando la giacenza non basta', async () => {
    const prodotto = await creaProdotto({ giacenza: 1 })

    const risposta = await request(app)
      .post('/api/ordini')
      .set('Authorization', `Bearer ${token}`)
      .send({ righe: [{ prodottoId: prodotto.id, quantita: 5 }] })

    expect(risposta.status).toBe(409)
    // ← e il magazzino non è stato toccato
    expect((await leggiProdotto(prodotto.id)).giacenza).toBe(1)
  })

  it('venti ordini concorrenti sull’ultimo pezzo: uno solo riesce', async () => {
    const prodotto = await creaProdotto({ giacenza: 1 })

    const esiti = await Promise.all(
      Array.from({ length: 20 }, () =>
        request(app)
          .post('/api/ordini')
          .set('Authorization', `Bearer ${token}`)
          .send({ righe: [{ prodottoId: prodotto.id, quantita: 1 }] }),
      ),
    )

    // Questo test con un mock del database passerebbe SEMPRE, e non
    // direbbe nulla: la transazione esiste solo nel database vero
    expect(esiti.filter((r) => r.status === 201)).toHaveLength(1)
    expect((await leggiProdotto(prodotto.id)).giacenza).toBe(0)
  })
})
```

---

## B6. Isolamento e dati di prova

```
IL PROBLEMA: i test devono partire da uno stato noto, e non devono
lasciare tracce che influenzino i successivi.

LE TRE STRATEGIE, DALLA PIÙ VELOCE ALLA PIÙ ROBUSTA
  1. TRANSAZIONE ANNULLATA  BEGIN in beforeEach, ROLLBACK in
     afterEach. Velocissima e non tocca le sequenze.
     ⚠ Non funziona se il codice sotto test apre una transazione
       propria o usa una connessione diversa.
  2. TRUNCATE delle tabelle fra i test. Più lenta ma sempre valida.
     `TRUNCATE … RESTART IDENTITY CASCADE` in un solo comando.
  3. UN DATABASE PER WORKER  isolamento perfetto e parallelismo
     pieno; costa più memoria e tempo di avvio.
```

```typescript
// I dati di prova: una factory con valori predefiniti sensati, e
// solo ciò che il test dichiara esplicitamente
let contatore = 0

export function datiUtente(sovrascritture: Partial<Utente> = {}): NuovoUtente {
  contatore += 1
  return {
    // L'unicità è garantita dal contatore, non dalla casualità: un
    // test che fallisce si riproduce identico
    email: `utente-${contatore}@prova.local`,
    nome: 'Utente di prova',
    ruoli: ['utente'],
    ...sovrascritture,
  }
}

export async function creaUtente(sovrascritture: Partial<Utente> = {}) {
  return db.utente.create({ data: datiUtente(sovrascritture) })
}
```

```
⚠ LA REGOLA CHE RENDE I TEST LEGGIBILI: nel test si scrive SOLO ciò
  che è rilevante per quel test.
    const admin = await creaUtente({ ruoli: ['admin'] })
  Chi legge capisce subito che conta il ruolo, e che il nome e
  l'email non c'entrano. Una fixture con venti campi espliciti
  nasconde quale sia quello che fa fallire il test.

⚠ E MAI DATI CASUALI VERI (faker senza seme): un test che fallisce
  una volta su cento e non si riproduce è peggio di un test assente.
```

---

## B7. Copertura: cosa misura e cosa non misura

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      // ⚠ Senza `all`, i file MAI importati da un test non compaiono
      //    nel rapporto: la copertura sembra alta perché ignora ciò
      //    che nessuno tocca
      all: true,
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.test.*', 'src/**/*.d.ts', 'src/main.tsx'],
      thresholds: {
        // Una soglia bassa che impedisce le regressioni, non una
        // alta che si insegue con test inutili
        lines: 70,
        // Le soglie mirate sono più utili di quella globale
        'src/dominio/**': { lines: 95, branches: 90 },
      },
    },
  },
})
```

```
COSA LA COPERTURA MISURA
  quali RIGHE sono state ESEGUITE durante i test.

COSA NON MISURA
  ❌ se le assertion verificano qualcosa di sensato
  ❌ se i casi limite sono coperti
  ❌ se il comportamento è corretto

  function dividi(a, b) { return a / b }
  it('divide', () => { dividi(10, 2) })
  → 100% di copertura, zero assertion, e `dividi(1, 0)` non è mai
    stato provato.

COME SI USA DAVVERO
  ✅ come RICERCA: guardare quali rami non sono mai stati eseguiti
     spesso rivela un caso d'errore dimenticato
  ✅ come SOGLIA DI NON REGRESSIONE: non scendere sotto il valore
     attuale
  ✅ alta e stretta sul DOMINIO (calcoli, regole), bassa sul resto
  ❌ come obiettivo: "arriviamo al 90%" produce test scritti per
     coprire righe, che è esattamente ciò che non serve
```

---

## B8. Snapshot e regressione visiva

```typescript
// ❌ LO SNAPSHOT DI UN COMPONENTE INTERO
expect(container).toMatchSnapshot()
// Cambia una classe CSS e lo snapshot fallisce. Nessuno legge un
// diff di trecento righe: si esegue `-u` e si aggiorna. Da quel
// momento lo snapshot non protegge più nulla — e i bug veri passano
// insieme alle modifiche innocue.

// ✅ Uno snapshot MIRATO su un dato serializzato, dove il diff è
//    leggibile e ogni cambiamento è significativo
expect(normalizzaFattura(risposta.body)).toMatchInlineSnapshot(`
  {
    "numero": "FT-2026-0001",
    "righe": 3,
    "totaleCentesimi": 12000,
    "valuta": "EUR",
  }
`)
```

```
LO SNAPSHOT È UTILE QUANDO
  ✅ il valore è piccolo e strutturato
  ✅ ogni modifica DEVE essere notata (formato di una fattura, di
     un messaggio verso l'esterno, di un file generato)
  ✅ è inline: si legge accanto al test, e il diff è nel commit
LO SNAPSHOT È DANNOSO QUANDO
  ❌ è grande: nessuno lo rilegge, e `-u` diventa un riflesso
  ❌ contiene dati variabili (date, id, ordinamenti non stabili)
```

```
LA REGRESSIONE VISIVA È UN'ALTRA COSA: confronta IMMAGINI, e prende
i bug che nessun test del DOM vede (un elemento coperto, un testo
che esce dal contenitore, un contrasto perso).
  await expect(page).toHaveScreenshot('dashboard.png', {
    maxDiffPixelRatio: 0.01,
    mask: [page.getByTestId('data-corrente')],  // le parti variabili
  })

⚠ È FRAGILE PER NATURA: font diversi, antialiasing e versioni del
  browser cambiano i pixel. Va eseguita in un CONTENITORE identico a
  quello della CI, altrimenti le immagini di riferimento generate in
  locale falliranno sempre. Vale la pena su poche pagine chiave, non
  su tutte.
```

---

## B9. Accessibilità e contract testing

```tsx
// Un controllo automatico di accessibilità costa tre righe e prende
// una parte reale dei problemi
import { render } from '@testing-library/react'
import { axe } from 'vitest-axe'
import { expect, it } from 'vitest'

it('la pagina non ha violazioni di accessibilità rilevabili', async () => {
  const { container } = render(<Dashboard />)
  const risultato = await axe(container)
  expect(risultato.violations).toEqual([])
})
```

```
⚠ AXE TROVA CIRCA IL 30-40% DEI PROBLEMI: contrasti, etichette
  mancanti, ruoli sbagliati, attributi ARIA non validi. Non trova
  l'ordine di lettura illogico, la trappola di focus, il testo
  alternativo scritto male o un flusso impossibile da completare
  con la sola tastiera. Il resto richiede una prova con la tastiera
  e con uno screen reader. È un filtro, non un certificato.
```

```typescript
// Contract testing: il test che impedisce a codice e OpenAPI di
// divergere. Costa poco e sostituisce quasi sempre Pact nei
// progetti che non hanno molti servizi indipendenti.
import jestOpenAPI from 'jest-openapi'
import request from 'supertest'
import { it, expect } from 'vitest'

jestOpenAPI(new URL('../openapi.yaml', import.meta.url).pathname)

it('la risposta rispetta lo schema dichiarato', async () => {
  const risposta = await request(app).get('/api/ordini').set('Authorization', `Bearer ${token}`)

  // Fallisce se c'è un campo in più, uno in meno, un tipo diverso o
  // un formato non conforme
  expect(risposta).toSatisfyApiSpec()
})
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Riscrivere un test che verifica l'implementazione

**Obiettivo:** capire perché questo test non protegge nulla, e riscriverlo.

```tsx
// IL TEST DA CORREGGERE
it('ElencoOrdini funziona', async () => {
  const useOrdini = vi.spyOn(hooks, 'useOrdini').mockReturnValue({
    dati: [{ id: '1', numero: 'ORD-1', totaleCentesimi: 1000 }],
    inCaricamento: false,
    errore: null,
  })

  const { container } = render(<ElencoOrdini />)

  expect(useOrdini).toHaveBeenCalled()
  expect(container.querySelectorAll('.riga-ordine')).toHaveLength(1)
  expect(container.innerHTML).toContain('ORD-1')
})
```

```
# LA DIAGNOSI — cinque problemi
# 1. IL NOME non dice cosa verifica: quando fallisce in CI non aiuta
# 2. MOCK DELL'HOOK INTERNO: il fetch, l'URL, il parsing e la
#    gestione degli errori non vengono mai eseguiti. Se l'hook è
#    rotto, il test resta verde.
# 3. `expect(useOrdini).toHaveBeenCalled()` verifica il MECCANISMO,
#    non il risultato: passa anche se non compare nulla a schermo.
# 4. `.riga-ordine` si rompe al primo ritocco del CSS.
# 5. `container.innerHTML` verifica una stringa, non ciò che l'utente
#    vede: passerebbe anche con il testo in un elemento nascosto.
```

```tsx
// LA SOLUZIONE — la rete è finta, tutto il resto è vero
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../test/setup.js'
import { ElencoOrdini } from './ElencoOrdini.js'

describe('ElencoOrdini', () => {
  it('mostra gli ordini restituiti dall’API', async () => {
    server.use(
      http.get('/api/ordini', () =>
        HttpResponse.json({
          elementi: [{ id: '1', numero: 'ORD-1', totaleCentesimi: 1000, stato: 'pagato' }],
          paginazione: { limite: 20, haAltri: false },
        }),
      ),
    )

    render(<ElencoOrdini />)

    // findBy* aspetta il caricamento: nessuna attesa arbitraria
    expect(await screen.findByRole('row', { name: /ORD-1/ })).toBeInTheDocument()
    expect(screen.getByText('10,00 €')).toBeInTheDocument()
  })

  it('mostra uno stato vuoto quando non ci sono ordini', async () => {
    server.use(
      http.get('/api/ordini', () =>
        HttpResponse.json({ elementi: [], paginazione: { limite: 20, haAltri: false } }),
      ),
    )

    render(<ElencoOrdini />)

    expect(await screen.findByText(/nessun ordine/i)).toBeInTheDocument()
    // queryBy per l'assenza: getBy solleverebbe prima dell'assertion
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('mostra un errore quando la richiesta fallisce', async () => {
    server.use(http.get('/api/ordini', () => HttpResponse.json({}, { status: 500 })))

    render(<ElencoOrdini />)

    expect(await screen.findByRole('alert')).toHaveTextContent(/non è stato possibile/i)
  })
})
```

```
# COSA È CAMBIATO
#   Il test ora esegue il fetch reale del componente, verifica ciò
#   che l'utente vede e copre tre stati invece di uno. Sopravvive a
#   una riscrittura dell'hook e a un cambio di CSS, e fallisce se il
#   formato dell'importo o la gestione dell'errore si rompono.
```

---

### Esercizio 2 — Stabilizzare un test end-to-end instabile

**Obiettivo:** un test fallisce circa una volta su cinque in CI. Trovare le cause e correggerle senza aggiungere retry.

```typescript
// IL TEST INSTABILE
test('creazione di un ordine', async ({ page }) => {
  await page.goto('/ordini')
  await page.click('.btn-nuovo')
  await page.waitForTimeout(1000)

  await page.fill('#cliente', 'Rossi SPA')
  await page.click('.prodotto-item:first-child')
  await page.click('button[type=submit]')

  await page.waitForTimeout(2000)
  expect(await page.locator('.toast').textContent()).toContain('creato')
  expect(await page.locator('.riga-ordine').count()).toBe(1)
})
```

```
# LE SEI CAUSE
# 1. waitForTimeout(1000) e (2000): su una CI carica non bastano, in
#    locale sono tempo sprecato. Non esiste un valore giusto.
# 2. Selettori CSS: `.btn-nuovo` e `.toast` si rompono col design.
# 3. `:first-child` dipende dall'ORDINE dei prodotti, che può
#    cambiare fra un'esecuzione e l'altra.
# 4. `textContent()` legge UNA VOLTA: se il toast non è ancora
#    apparso, legge null. Non riprova.
# 5. `.count()).toBe(1)` presuppone che il database sia vuoto: se un
#    altro test ha creato un ordine, fallisce.
# 6. Il toast SPARISCE dopo qualche secondo: fra il primo
#    waitForTimeout e la lettura può essere già svanito.
```

```typescript
// LA SOLUZIONE
import { test, expect } from '@playwright/test'

test('la creazione di un ordine lo aggiunge all’elenco', async ({ page }) => {
  // 1. Dati unici per questa esecuzione: nessuna dipendenza dallo
  //    stato lasciato da altri test
  const cliente = `Rossi SPA ${Date.now()}`

  await page.goto('/ordini')
  await page.getByRole('button', { name: /nuovo ordine/i }).click()

  // 2. Nessuna attesa arbitraria: si aspetta l'elemento, non il tempo
  const modulo = page.getByRole('dialog', { name: /nuovo ordine/i })
  await expect(modulo).toBeVisible()

  await modulo.getByLabel('Cliente').fill(cliente)

  // 3. Il prodotto si sceglie per NOME, non per posizione
  await modulo.getByRole('option', { name: 'Tastiera meccanica' }).click()

  // 4. Si aspetta la RISPOSTA della richiesta, non un tempo: così il
  //    test non dipende dalla velocità del server
  const creazione = page.waitForResponse(
    (r) => r.url().includes('/api/ordini') && r.request().method() === 'POST',
  )
  await modulo.getByRole('button', { name: /crea/i }).click()
  const risposta = await creazione
  expect(risposta.status()).toBe(201)

  // 5. expect di Playwright: riprova finché non passa. E si verifica
  //    la RIGA dell'ordine creato, non il conteggio totale.
  await expect(page.getByRole('alert')).toContainText(/ordine creato/i)
  await expect(page.getByRole('row', { name: new RegExp(cliente) })).toBeVisible()
})
```

```
# LA VERIFICA CHE LA CORREZIONE HA FUNZIONATO
#   npx playwright test --repeat-each=20 e2e/ordini.spec.ts
#   Venti esecuzioni consecutive verdi. E in CI, con la macchina
#   carica, `--workers=4` per riprodurre le condizioni reali.
#
# ⚠ Il tempo di esecuzione dovrebbe essere anche SCESO: i
#   waitForTimeout aspettavano tre secondi a ogni giro, le attese
#   sugli eventi si sbloccano appena l'evento arriva.
```

---

### Esercizio 3 — Scrivere il test che riproduce un bug

**Obiettivo:** un ordine con uno sconto del 100% viene rifiutato con "importo non valido". Riprodurre, correggere, e impedire il ritorno.

```
# LA SEGNALAZIONE
#   "Con il codice sconto BENVENUTO100 il carrello dà errore
#    'Importo non valido' e non si riesce a concludere."
```

```typescript
// PASSO 1 — il test che RIPRODUCE il bug, e che deve FALLIRE ora.
// Scriverlo prima della correzione è ciò che garantisce che il test
// verifichi davvero il bug: un test scritto dopo può passare per
// caso.
import { describe, it, expect } from 'vitest'
import { calcolaTotale } from './carrello.js'

describe('calcolaTotale con sconti', () => {
  it('accetta uno sconto del 100% e produce un totale di zero', () => {
    const totale = calcolaTotale({
      righe: [{ quantita: 1, prezzoUnitarioCentesimi: 5000 }],
      scontoPercentuale: 100,
    })

    expect(totale).toBe(0) // ← attualmente solleva "Importo non valido"
  })
})
```

```typescript
// PASSO 2 — la causa, trovata dal test
export function calcolaTotale(carrello: Carrello): number {
  const lordo = carrello.righe.reduce((s, r) => s + r.quantita * r.prezzoUnitarioCentesimi, 0)
  const netto = Math.round(lordo * (1 - carrello.scontoPercentuale / 100))

  // ❌ Il difetto: zero è un totale legittimo. La condizione avrebbe
  //    dovuto escludere solo i valori NEGATIVI.
  if (!netto) throw new ErroreValidazione('Importo non valido')

  return netto
}
```

```typescript
// PASSO 3 — la correzione, e i casi limite intorno che il bug ha
// rivelato: quando ne trovi uno, gli altri della stessa famiglia
// sono quasi sempre lì accanto
export function calcolaTotale(carrello: Carrello): number {
  if (carrello.scontoPercentuale < 0 || carrello.scontoPercentuale > 100) {
    throw new ErroreValidazione('Sconto fuori intervallo')
  }

  const lordo = carrello.righe.reduce((s, r) => s + r.quantita * r.prezzoUnitarioCentesimi, 0)
  const netto = Math.round(lordo * (1 - carrello.scontoPercentuale / 100))

  if (netto < 0) throw new ErroreValidazione('Importo non valido')

  return netto
}
```

```typescript
// PASSO 4 — la famiglia di casi limite, tutta insieme
it.each([
  { sconto: 0, atteso: 5000 },
  { sconto: 50, atteso: 2500 },
  { sconto: 100, atteso: 0 },
])('sconto del $sconto% su 50,00 € dà $atteso centesimi', ({ sconto, atteso }) => {
  expect(
    calcolaTotale({ righe: [{ quantita: 1, prezzoUnitarioCentesimi: 5000 }], scontoPercentuale: sconto }),
  ).toBe(atteso)
})

it('rifiuta uno sconto fuori intervallo', () => {
  const righe = [{ quantita: 1, prezzoUnitarioCentesimi: 5000 }]
  expect(() => calcolaTotale({ righe, scontoPercentuale: 101 })).toThrow(/intervallo/i)
  expect(() => calcolaTotale({ righe, scontoPercentuale: -1 })).toThrow(/intervallo/i)
})

it('un carrello vuoto vale zero, non è un errore', () => {
  expect(calcolaTotale({ righe: [], scontoPercentuale: 0 })).toBe(0)
})
```

```
# LA PROCEDURA, IN GENERALE
#   1. il test che riproduce, PRIMA della correzione — e deve fallire
#   2. la correzione minima
#   3. il test diventa verde
#   4. i casi limite della stessa famiglia
#   5. il test resta per sempre: è il solo modo perché il bug non
#      torni al terzo rilascio
#
# ⚠ `if (!valore)` è falso anche per 0, "" e NaN. È una delle cause
#   più frequenti di questa famiglia di bug in JavaScript: la
#   condizione va scritta su ciò che si intende davvero escludere.
```

---

## C2. Mini-progetto: suite di test completa per la dashboard

L'esercizio chiave del modulo: unit, componenti ed end-to-end sulla dashboard costruita nei tutorial precedenti.

```
dashboard/
├── src/
│   ├── dominio/          logica pura → test unitari, copertura alta
│   ├── componenti/       → Testing Library + MSW
│   └── api/              → Supertest + Testcontainers
├── test/
│   ├── setup.ts          MSW, matcher, TZ fissato
│   ├── msw/handlers.ts   una definizione per tutti i livelli
│   └── factory.ts        creaUtente, creaOrdine, creaProdotto
├── e2e/
│   ├── fixture.ts        animazioni disattivate, accesso già fatto
│   └── *.spec.ts         i percorsi critici, non tutti
└── vitest.config.ts · playwright.config.ts

COSA VERIFICARE, PER LIVELLO
  UNITARI (millisecondi, molti)
    calcolo dei totali con IVA e sconti · formattazione di importi e
    date · validazione degli schemi · trasformazione dei filtri in
    parametri di query
  COMPONENTI (decine di ms)
    stato di caricamento, vuoto ed errore per ogni vista · filtri
    che aggiornano l'URL · ordinamento della tabella · paginazione
    a cursore · accessibilità con axe
  INTEGRAZIONE (secondi)
    ogni endpoint: senza autenticazione, con l'utente sbagliato
    (IDOR), con corpo non valido, con campi in più · concorrenza
    sulla giacenza · conformità a openapi.yaml
  E2E (5-15 percorsi, non di più)
    accesso e uscita · creare un ordine dall'inizio alla fine ·
    filtrare e paginare · un errore del server gestito con garbo ·
    il percorso completo con la sola tastiera
```

```typescript
// e2e/fixture.ts — l'accesso si fa UNA VOLTA e si riusa: firmare i
// token a ogni test costa secondi che si moltiplicano
import { test as base, expect } from '@playwright/test'

export const test = base.extend<{ paginaAutenticata: Page }>({
  paginaAutenticata: async ({ browser }, use) => {
    const contesto = await browser.newContext({ storageState: 'e2e/.auth/utente.json' })
    const page = await contesto.newPage()
    await page.addStyleTag({
      content: `*, *::before, *::after { animation-duration: 0s !important;
                transition-duration: 0s !important; }`,
    })
    await use(page)
    await contesto.close()
  },
})

export { expect }
```

```
# LA VERIFICA, IN ORDINE
# 1. LA SUITE È DETERMINISTICA
#    vitest --run --sequence.shuffle   → verde con qualunque ordine
#    playwright test --repeat-each=10  → dieci volte verde
# 2. I TEST FALLISCONO QUANDO DEVONO
#    rompi di proposito il calcolo del totale: almeno un test rosso.
#    Se resta tutto verde, la suite non protegge quel codice.
# 3. NESSUNA CHIAMATA DI RETE NON PREVISTA
#    onUnhandledRequest: 'error' in MSW → nessun errore
# 4. LA COPERTURA DEL DOMINIO È ALTA, quella del resto è quella che è
# 5. IL TEMPO È SOSTENIBILE
#    unit+componenti sotto i 30 s, E2E sotto i 5 minuti in parallelo
# 6. L'ACCESSIBILITÀ
#    axe pulito su ogni vista, e il percorso principale completabile
#    con la sola tastiera
# 7. IL CONTRATTO
#    toSatisfyApiSpec su ogni endpoint
# 8. IN CI
#    la suite gira su ogni push, e un test che ha avuto bisogno di
#    retry viene SEGNALATO, non nascosto
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Testing in CI: velocità e affidabilità

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  verifica:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: '.nvmrc'
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile --ignore-scripts

      # I controlli veloci per primi: falliscono in secondi e
      # risparmiano i minuti dei test
      - run: pnpm exec tsc --noEmit
      - run: pnpm exec eslint . --max-warnings 0
      - run: pnpm vitest run --coverage

  e2e:
    runs-on: ubuntu-latest
    needs: verifica
    strategy:
      fail-fast: false
      # Il partizionamento: quattro macchine, un quarto dei test
      # ciascuna. È il modo più semplice di dimezzare i tempi.
      matrix:
        parte: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec playwright install --with-deps chromium
      - run: pnpm exec playwright test --shard=${{ matrix.parte }}/4

      # Le tracce dei fallimenti sono ciò che rende diagnosticabile
      # un test rotto in CI senza riprodurlo in locale
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: traccia-${{ matrix.parte }}
          path: test-results/
```

```
LE QUATTRO LEVE SUI TEMPI, IN ORDINE DI RESA
  1. ORDINE  tipi e lint prima dei test: un errore di battitura non
     deve costare cinque minuti di E2E
  2. PARTIZIONAMENTO  --shard su più macchine; è lineare
  3. CACHE  dipendenze, build e browser di Playwright
  4. SELEZIONE  eseguire solo i test toccati dal cambiamento
     (`vitest --changed`) sulle pull request, tutto sul ramo
     principale

⚠ NON DISATTIVARE MAI UN TEST PER FAR PASSARE LA CI. Se serve
  sbloccare, si marca `fixme` con un riferimento e una scadenza: un
  test disattivato e tracciato è un debito, uno cancellato è una
  perdita silenziosa.
```

---

## D2. Test basati su proprietà

```typescript
// Invece di scegliere tu i casi, si dichiara una PROPRIETÀ che deve
// valere per QUALUNQUE input, e la libreria cerca il controesempio
import fc from 'fast-check'
import { it, expect } from 'vitest'
import { formattaCentesimi, analizzaImporto } from './denaro.js'

it('formattare e rianalizzare un importo restituisce lo stesso valore', () => {
  fc.assert(
    fc.property(fc.integer({ min: 0, max: 100_000_000 }), (centesimi) => {
      expect(analizzaImporto(formattaCentesimi(centesimi))).toBe(centesimi)
    }),
  )
})

it('il totale non è mai negativo, qualunque sconto valido', () => {
  fc.assert(
    fc.property(
      fc.array(
        fc.record({
          quantita: fc.integer({ min: 1, max: 100 }),
          prezzoUnitarioCentesimi: fc.integer({ min: 0, max: 1_000_000 }),
        }),
        { maxLength: 50 },
      ),
      fc.integer({ min: 0, max: 100 }),
      (righe, scontoPercentuale) => {
        expect(calcolaTotale({ righe, scontoPercentuale })).toBeGreaterThanOrEqual(0)
      },
    ),
  )
})
```

```
QUANDO VALE LA PENA
  ✅ funzioni con un'inversa (serializza/deserializza, cifra/decifra,
     formatta/analizza)
  ✅ invarianti: "il totale non è mai negativo", "l'ordinamento non
     perde elementi", "l'output è sempre valido secondo lo schema"
  ✅ parser e validatori, dove i casi limite sono infiniti

IL VALORE VERO: quando fallisce, `fast-check` RESTRINGE l'input al
controesempio minimo. Non ti dice "fallisce con questo array di
cinquanta elementi": ti dice "fallisce con [0]". È spesso la
diagnosi già fatta.

⚠ Non sostituisce i test a esempi: quelli documentano il
  comportamento atteso e si leggono. I due si affiancano.
```

---

## D3. Mutation testing: chi controlla i test

```powershell
pnpm add -D @stryker-mutator/core @stryker-mutator/vitest-runner
pnpm exec stryker run
```

```
COME FUNZIONA  Stryker introduce mutazioni nel codice — cambia > in
>=, sostituisce true con false, elimina una riga — ed esegue la
suite. Se i test restano VERDI con il codice mutato, quella mutazione
è "sopravvissuta": significa che nessun test copre quel comportamento.

  Righe coperte:      94%   ← ciò che misura la copertura
  Mutazioni uccise:   61%   ← ciò che i test verificano DAVVERO

  La distanza fra i due numeri è la misura più onesta della qualità
  di una suite. Una copertura del 94% con il 61% di mutazioni uccise
  significa che un terzo del codice è eseguito senza essere
  verificato.

⚠ È LENTO: esegue la suite una volta per mutazione. Si usa sui
  moduli critici (il dominio, i calcoli su denaro), non su tutto, e
  a cadenza — non a ogni push.
```

---

## D4. Testare il tempo, la casualità e la rete

```typescript
import { vi, it, expect, afterEach } from 'vitest'

afterEach(() => {
  vi.useRealTimers() // ⚠ senza, i timer finti restano attivi nel test dopo
})

it('un abbonamento scade dopo trenta giorni', () => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-01-01T10:00:00Z'))

  const abbonamento = creaAbbonamento({ giorni: 30 })
  expect(abbonamento.attivo()).toBe(true)

  // Il tempo si sposta senza aspettare
  vi.setSystemTime(new Date('2026-01-31T09:59:00Z'))
  expect(abbonamento.attivo()).toBe(true)

  vi.setSystemTime(new Date('2026-01-31T10:00:01Z'))
  expect(abbonamento.attivo()).toBe(false)
})

it('il backoff aspetta gli intervalli previsti', async () => {
  vi.useFakeTimers()
  const tentativo = vi.fn().mockRejectedValueOnce(new Error('rete')).mockResolvedValue('ok')

  const promessa = conRiprova(tentativo, { tentativi: 2, attesaMs: 1000 })
  // advanceTimersByTimeAsync fa avanzare i timer E svuota le
  // microtask: senza la variante async, le Promise restano appese
  await vi.advanceTimersByTimeAsync(1000)

  await expect(promessa).resolves.toBe('ok')
  expect(tentativo).toHaveBeenCalledTimes(2)
})
```

```
LE ALTRE FONTI DI NON DETERMINISMO
  FUSO ORARIO  fissarlo nella configurazione, non nel singolo test:
    `env: { TZ: 'Europe/Rome' }` in vitest.config. Un test che passa
    in Italia e fallisce sulla CI in UTC è la causa più comune di
    "sul mio computer funziona".
  CASUALITÀ  vi.spyOn(Math, 'random').mockReturnValue(0.5), oppure —
    meglio — iniettare la fonte di casualità come parametro: il
    codice diventa testabile senza mock.
  ORDINE DI Object.keys  è stabile in JavaScript moderno per le
    chiavi stringa, ma NON assumerlo per l'output di una query
    (senza ORDER BY, l'ordine non è garantito).
  UUID  se il test lo confronta, va iniettato; se no, va ignorato
    nell'assertion (expect.any(String)).
```

---

## D5. Quando NON scrivere un test

```
UN TEST HA UN COSTO: si scrive, si legge, si mantiene, e ogni
modifica del codice può richiedere di aggiornarlo. Vale la pena solo
se il costo è inferiore al rischio che copre.

NON SCRIVERE UN TEST PER
  ❌ i getter e i setter banali, e i tipi che TypeScript già verifica
  ❌ le librerie di terzi: non è compito tuo verificare che React
     renderizzi
  ❌ la configurazione statica: un file di costanti non ha
     comportamento
  ❌ il codice che stai per buttare: un prototipo esplorativo
  ❌ ciò che un tipo esprime meglio: se il test verifica che una
     funzione rifiuti una stringa dove serve un numero, quel test
     è un tipo scritto male

SCRIVI SEMPRE UN TEST PER
  ✅ qualunque bug corretto — è l'unico modo perché non torni
  ✅ la logica su denaro, date, fusi orari e permessi
  ✅ i casi limite: vuoto, zero, uno, negativo, molto grande
  ✅ i percorsi d'errore: cosa succede quando la dipendenza cade
  ✅ tutto ciò che, rompendosi, ti sveglierebbe di notte

LA DOMANDA CHE RISOLVE I CASI DUBBI
  "Se questo si rompesse senza che nessuno se ne accorga, quanto
  costerebbe?" Se la risposta è "poco", il test può aspettare. Se è
  "un cliente perso" o "una segnalazione all'autorità", si scrive
  adesso.
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
TESTING WEB — Mappa dei concetti

COSA RENDE UTILE UN TEST
├── verifica il COMPORTAMENTO, non l'implementazione
├── resta verde se cambia l'implementazione, rosso se si rompe il
│     comportamento
├── un test che asserisce ciò che un mock restituisce non è un test
└── priorità: denaro e permessi · casi limite · errori · regressioni

LIVELLI
├── analisi statica (TS strict + ESLint) è il primo livello, gratis
├── unitari: logica pura, molti, millisecondi
├── integrazione: endpoint e componenti — dove stanno i bug veri
├── E2E: 5-15 percorsi critici, non 200
└── la forma giusta dipende da dove nascono i TUOI bug

COMPONENTI E MOCK
├── userEvent, non fireEvent
├── getByRole con name > getByLabelText > getByText > getByTestId
├── getBy (c'è) · queryBy (può non esserci) · findBy (aspetta)
├── se getByRole non lo trova, spesso l'elemento non è accessibile
├── si sostituisce il CONFINE esterno, non la logica interna: lento ·
│     non deterministico · effetti reali · casi d'errore difficili
├── MSW intercetta la RETE: gli stessi handler in unit, jsdom,
│     Playwright e sviluppo
└── restoreAllMocks e resetHandlers fra i test, o sopravvivono

INTEGRAZIONE E DATI
├── database vero con Testcontainers, non un mock
├── isolamento: transazione annullata · TRUNCATE · database per worker
├── factory con valori predefiniti; nel test solo ciò che è rilevante
└── unicità da un contatore, mai da dati casuali senza seme

STABILITÀ
├── mai waitForTimeout: attendere l'elemento, la risposta, lo stato
├── nessuno stato condiviso · dati unici per test
├── tempo e fusi finti; animazioni disattivate
└── il retry in CI è una rete, non una cura: va segnalato

MISURE E PRODUZIONE
├── la copertura misura le righe eseguite, non ciò che è verificato:
│     soglia alta sul dominio, mai come obiettivo
├── mutation testing dice quanto i test verificano davvero
├── axe trova il 30-40%: filtro, non certificato
├── in CI: tipi e lint prima, partizionamento, cache, tracce
├── property-based per invarianti e funzioni inverse
└── non testare ciò che i tipi già garantiscono
```

---

## Checklist di competenze

**Parte A — Basi**

- [ ] Sai distinguere un test sul comportamento da uno sull'implementazione
- [ ] Sai perché un test che asserisce il valore di un mock non verifica nulla
- [ ] Scrivi nomi di test che bastano a capire cosa è rotto
- [ ] Conosci la differenza fra `toBe`, `toEqual` e `toStrictEqual`
- [ ] Sai perché `toThrow()` senza argomenti è quasi inutile
- [ ] Usi `userEvent` e sai perché è preferibile a `fireEvent`
- [ ] Conosci le tre famiglie di query e quando usare ciascuna
- [ ] Sai perché `getBy` non funziona con `not.toBeInTheDocument()`
- [ ] Sai quando un mock serve e quando fa danni
- [ ] Hai scritto un test end-to-end senza attese arbitrarie

**Parte B — Comprensione**

- [ ] Sai scegliere il livello di un test in base a logica e connessioni
- [ ] Conosci l'ordine di preferenza dei selettori e il perché di ciascuno
- [ ] Sai perché `getByRole` è anche un controllo di accessibilità
- [ ] Sai riconoscere le cinque cause dei test instabili
- [ ] Sai perché un test instabile è peggio di un test assente
- [ ] Usi MSW e sai perché è preferibile a mockare `fetch`
- [ ] Sai perché `onUnhandledRequest: 'error'` è importante
- [ ] Testi contro un database reale e conosci le tre strategie di isolamento
- [ ] Sai perché i dati di prova non devono essere casuali senza seme
- [ ] Sai cosa la copertura misura e cosa non misura
- [ ] Sai quando uno snapshot è utile e quando è dannoso
- [ ] Sai quanta parte dei problemi di accessibilità axe trova

**Parte C — Pratica**

- [ ] Hai riscritto il test che verificava l'implementazione, coprendo tre stati
- [ ] Hai stabilizzato l'E2E eliminando le sei cause, senza retry
- [ ] Hai verificato la stabilità con `--repeat-each`
- [ ] Hai scritto il test che riproduce un bug PRIMA di correggerlo
- [ ] Hai coperto la famiglia di casi limite che il bug ha rivelato

**Parte D — Esperto**

- [ ] Ordini i lavori della CI dal più veloce al più lento
- [ ] Partizioni gli E2E e conservi le tracce dei fallimenti
- [ ] Sai quando un test basato su proprietà vale più di dieci a esempi
- [ ] Sai leggere la distanza fra copertura e mutazioni uccise
- [ ] Controlli tempo, fuso e casualità nei test
- [ ] Sai elencare i casi in cui NON scrivere un test è la scelta giusta

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Test che verifica l'implementazione | Rosso a ogni refactoring, verde con il bug | Verificare il comportamento osservabile |
| Asserire il valore restituito da un mock | Verifica il mock, non il codice | Mockare il confine esterno, non la logica |
| `it('funziona')` | In CI il nome è l'unica diagnosi disponibile | Nome che descrive il comportamento atteso |
| `toThrow()` senza argomenti | Passa per qualunque errore, anche un typo | `toThrow(/messaggio/)` o la classe |
| Selettori CSS (`.btn-primary`) | Si rompono al primo ritocco del design | `getByRole` con `name` |
| `getByText('Salva le modifiche')` | Si rompe cambiando la copy | Regex, o il ruolo |
| `waitForTimeout` | Troppo corto fallisce, troppo lungo rallenta | Attendere l'elemento, la risposta o lo stato |
| Test dipendenti dall'ordine | Passano insieme, falliscono da soli | Ogni test crea e pulisce i propri dati |
| Dati casuali senza seme | Fallimenti non riproducibili | Contatore, o seme fisso |
| Mock del database | Nessun vincolo, nessuna transazione, nessun tipo | Testcontainers |
| Mock di `fetch` | URL, parsing e gestione errori non verificati | MSW |
| Dimenticare `resetHandlers` | Un override si porta nel test successivo | `afterEach(() => server.resetHandlers())` |
| Snapshot di un componente intero | Nessuno legge il diff: si aggiorna e basta | Snapshot inline e mirati |
| Copertura come obiettivo | Test scritti per coprire righe, non per verificare | Soglia di non regressione; alta solo sul dominio |
| Retry per far passare un test instabile | Nasconde il problema e insegna a ignorare i rossi | Correggere la causa; segnalare i retry |
| Disattivare un test per sbloccare la CI | Debito che nessuno ripaga | `fixme` con riferimento e scadenza |
| E2E per ogni funzionalità | Suite lentissima e fragile | 5-15 percorsi critici |
| Nessun test per un bug corretto | Il bug torna al terzo rilascio | Il test che riproduce, scritto prima |
| Testare ciò che il tipo già garantisce | Costo senza rischio coperto | Un tipo scritto meglio |

---

## Troubleshooting rapido

**Un test passa da solo e fallisce con gli altri**
- Causa: stato condiviso — database, mock non ripristinati, variabili di modulo
- Fix: `restoreAllMocks` e `resetHandlers` in `afterEach`; dati unici per test

**`getByRole` non trova un elemento che si vede**
- Causa: l'elemento non ha un ruolo (un `<div onClick>`), o manca il nome accessibile
- Fix: usare l'elemento semantico giusto; è un problema di accessibilità, non del test

**`act(...)` warning in React**
- Causa: uno stato si aggiorna fuori da un'azione attesa dal test
- Fix: `userEvent` (che avvolge già), e `findBy*` per attendere il risultato

**Il test è verde ma il codice è rotto**
- Causa: si asserisce il valore di un mock, o non c'è nessuna assertion significativa
- Fix: rompere il codice di proposito — se resta verde, il test non serve

**L'E2E fallisce solo in CI**
- Causa: macchina più lenta, fusi diversi, dati residui, font mancanti
- Fix: guardare la traccia; fissare TZ; eliminare le attese arbitrarie

**Playwright non trova un elemento visibile a schermo**
- Causa: è dentro un iframe o uno shadow DOM, oppure c'è un secondo elemento che combacia
- Fix: `frameLocator`; restringere con `within`/`filter`; `--debug` per ispezionare

**La suite è diventata lentissima**
- Causa: troppi E2E, container ricreati a ogni file, nessun parallelismo
- Fix: spostare le verifiche al livello più basso possibile; container condiviso; `--shard`

**MSW non intercetta**
- Causa: il server non è avviato, l'URL non combacia (relativo contro assoluto), o il codice usa un client che non passa da `fetch`
- Fix: `onUnhandledRequest: 'error'` per vedere l'URL reale nel messaggio

**Il rapporto di copertura mostra numeri troppo alti**
- Causa: manca `all: true`, quindi i file mai importati non sono contati
- Fix: `all: true` con `include` esplicito

**Un test sul tempo fallisce a fine mese o di notte**
- Causa: dipende dall'ora reale o dal fuso della macchina
- Fix: `vi.setSystemTime`, e `TZ` fissato nella configurazione

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_16_build_tools_deploy.md` | La pipeline in cui questa suite gira, e il deploy che dipende dal verde |
| `tutorial_17_performance_web.md` | Misurare le prestazioni con lo stesso rigore, e i budget in CI |
| `tutorial_14_sicurezza_web.md` | Trasformare ogni correzione di sicurezza in un test |
| `tutorial_19_troubleshooting.md` | Dal fallimento in produzione al test che lo riproduce |
| `tutorial_11_api_design.md` | Il contratto OpenAPI verificato a ogni build |
| `tutorial_21_rsc_server_driven_ui.md` | Testare i componenti che girano sul server |

---

## Risorse di riferimento

**Documentazione:** [Vitest](https://vitest.dev/) · [Testing Library](https://testing-library.com/docs/) — in particolare *Guiding Principles* e *About Queries* · [Playwright](https://playwright.dev/docs/intro), con *Best Practices* e *Trace Viewer* · [MSW](https://mswjs.io/docs/)

**Approfondimenti:** [Testing Library — Common mistakes](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library) · [Playwright — Best Practices](https://playwright.dev/docs/best-practices) · [Google Testing Blog](https://testing.googleblog.com/), in particolare la serie sui test di dimensione piccola, media e grande

**Strumenti:** [Testcontainers](https://node.testcontainers.org/) · [fast-check](https://fast-check.dev/) per i test basati su proprietà · [Stryker](https://stryker-mutator.io/) per il mutation testing · [axe-core](https://github.com/dequelabs/axe-core) · [jest-openapi](https://github.com/openapi-library/OpenAPIValidators)

---

> **Fine del Tutorial 15 — Testing Web**
>
> Prossimo tutorial: `tutorial_16_build_tools_deploy.md`
