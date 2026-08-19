# Tutorial 11 — API Design: Dal Principiante all'Esperto

> **Companion a:** `11-api-design.md`
> **Scope:** REST, risorse e URI, metodi HTTP e codici di stato, errori RFC 9457, paginazione offset/cursore/keyset, filtri, idempotenza, concorrenza con ETag, caching HTTP, versionamento, OpenAPI 3.1, rate limiting, webhook, operazioni bulk, scelta del paradigma
> **Prerequisiti:** `tutorial_10_nodejs.md` — Express, middleware, gestione centralizzata degli errori; `tutorial_06_typescript.md` — tipi e validazione con Zod
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** OpenAPI 3.1 · RFC 9457 · Express 5 · Zod 3 · PostgreSQL 17

---

## Indice Generale

- [Mappa concettuale](#mappa-concettuale)
- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Il contratto che sopravvive al codice](#a1-il-contratto-che-sopravvive-al-codice)
  - [A2. Risorse e URI: sostantivi, mai verbi](#a2-risorse-e-uri-sostantivi-mai-verbi)
  - [A3. I metodi HTTP: safe e idempotente](#a3-i-metodi-http-safe-e-idempotente)
  - [A4. I codici di stato che servono davvero](#a4-i-codici-di-stato-che-servono-davvero)
  - [A5. La forma della risposta e degli errori](#a5-la-forma-della-risposta-e-degli-errori)
  - [A6. Validare al confine con Zod](#a6-validare-al-confine-con-zod)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. Il Richardson Maturity Model](#b1-il-richardson-maturity-model)
  - [B2. Paginazione: offset, cursore, keyset](#b2-paginazione-offset-cursore-keyset)
  - [B3. Filtri e ordinamento: la lista chiusa](#b3-filtri-e-ordinamento-la-lista-chiusa)
  - [B4. Idempotenza e Idempotency-Key](#b4-idempotenza-e-idempotency-key)
  - [B5. Concorrenza: ETag e If-Match](#b5-concorrenza-etag-e-if-match)
  - [B6. Caching HTTP](#b6-caching-http)
  - [B7. Versionamento: cos'è un breaking change](#b7-versionamento-cosè-un-breaking-change)
  - [B8. OpenAPI 3.1 come sorgente di verità](#b8-openapi-31-come-sorgente-di-verità)
  - [B9. Rate limiting, webhook, operazioni bulk](#b9-rate-limiting-webhook-operazioni-bulk)
  - [B10. Scegliere il paradigma](#b10-scegliere-il-paradigma)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: API di gestione progetti con OpenAPI](#c2-mini-progetto-api-di-gestione-progetti-con-openapi)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. HATEOAS che serve davvero](#d1-hateoas-che-serve-davvero)
  - [D2. Contract testing e il deploy indipendente](#d2-contract-testing-e-il-deploy-indipendente)
  - [D3. Operazioni lunghe: 202 e la risorsa di stato](#d3-operazioni-lunghe-202-e-la-risorsa-di-stato)
  - [D4. Deprecare senza rompere](#d4-deprecare-senza-rompere)
  - [D5. Osservabilità di un'API](#d5-osservabilità-di-unapi)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
                    openapi.yaml — il contratto
       ┌──────────────┬───────┴───────┬──────────────┐
       ▼              ▼               ▼              ▼
  documentazione  tipi client    server mock    test in CI

   GET /api/v1/progetti?stato=attivo&limite=20   →  200 OK
   Authorization: Bearer …  ·  If-None-Match: "a3f9"
   ┌────────────────────────────────────────────────────────┐
   │ 1. rate limiting     → 429 + Retry-After               │
   │ 2. autenticazione    → 401    3. autorizzazione → 403  │
   │ 4. validazione (Zod) → 422 + Problem Details           │
   │ 5. idempotenza       → risposta memorizzata            │
   │ 6. concorrenza       → 412 se If-Match non combacia    │
   │ 7. logica            → 200 / 201 + Location / 204      │
   │ 8. errore imprevisto → 500, dettaglio SOLO nei log     │
   └────────────────────────────────────────────────────────┘
   LE QUATTRO DECISIONI CHE NON SI TORNANO INDIETRO
     formato degli identificatori · strategia di paginazione ·
     formato degli errori · strategia di versionamento
```

---
# Parte A — Basi Assolute

---

## A1. Il contratto che sopravvive al codice

> **Analogia:** un'API è la presa elettrica a muro. Dietro può esserci una centrale a carbone o un pannello solare; il tostapane non lo sa. Quello che conta è che i due fori restino a 230 volt, alla stessa distanza. Il giorno in cui qualcuno ruota la presa di novanta gradi, ogni elettrodomestico del paese smette di funzionare — e non è colpa degli elettrodomestici.

Un'API è un contratto, non il codice che la implementa: quel codice verrà riscritto, cambierà linguaggio e database, il contratto resta. Da qui l'asimmetria da interiorizzare subito: cambiare l'implementazione costa il tuo tempo, cambiare il contratto costa il tempo di tutti quelli che ti usano, più il coordinamento.

Immagina di aver pubblicato questo sei mesi fa:

```json
{ "prodotti": [{ "id": 1042, "nome": "Tastiera", "prezzo": 49.9 }], "pagina": 3 }
```

Sembra ragionevole, ma contiene già tre decisioni irreversibili:

```
1. ID NUMERICI SEQUENZIALI   chiunque enumera tutto il catalogo, e
   il volume dei dati è pubblicamente deducibile
2. PREZZO IN VIRGOLA MOBILE  0.1 + 0.2 !== 0.3: sui totali con IVA
   arrivano gli errori di arrotondamento
3. PAGINAZIONE A PAGINE      se qualcuno inserisce mentre l'utente
   scorre, un prodotto scivola dalla pagina 3 alla 4 e non viene
   mai visto
```

La versione che non si pente:

```json
{
  "elementi": [
    { "id": "prod_01HQ8X2K", "nome": "Tastiera", "prezzoCentesimi": 4990, "valuta": "EUR" }
  ],
  "paginazione": { "limite": 20, "cursoreSuccessivo": "eyJpZCI6…", "haAltri": true }
}
```

L'id opaco non è enumerabile e lascia al server la libertà di cambiare schema interno; i centesimi interi eliminano l'arrotondamento e il nome del campo dice l'unità; la valuta esplicita evita il bug che aspetta il primo cliente estero; `elementi` è un nome generico, così il client scrive una funzione di paginazione sola invece di venti; il cursore opaco permette di cambiare strategia senza rompere nulla.

**Il principio operativo:** prima di pubblicare un endpoint, chiediti cosa succederebbe se dovessi cambiare ogni sua decisione fra un anno. Quelle costose da cambiare vanno prese con cura; le altre possono aspettare.

---
## A2. Risorse e URI: sostantivi, mai verbi

> **Analogia:** un URI è un indirizzo postale, non un ordine. "Via Roma 12" identifica un luogo; cosa vuoi farci — consegnare, ritirare, demolire — lo dici a parte.

```
# ❌ SBAGLIATO — verbi nell'URI: ogni azione nuova è un endpoint
#    nuovo, e dopo due anni ce ne sono trecento
GET  /api/getProgetti          POST /api/creaProgetto
POST /api/eliminaProgetto/42   GET  /api/progettiPerUtente/7

# ✅ CORRETTO — sostantivi plurali, l'azione la dice il metodo
GET    /api/v1/progetti          elenca      POST   … crea
GET    /api/v1/progetti/{id}     legge       PATCH  … aggiorna
DELETE /api/v1/progetti/{id}     elimina
GET    /api/v1/progetti?membro=usr_7         filtra
```

La struttura diventa deducibile: chi ha capito `/progetti` sa già come funzionerà `/attivita`.

```
LE CONVENZIONI, E LA RAGIONE DI CIASCUNA
 1. PLURALE SEMPRE  /progetti è la collezione, /progetti/42 un
    elemento. Il singolare costringe a due nomi per la stessa cosa.
 2. kebab-case NEGLI URI  /ordini-di-acquisto. ⚠ Vale per gli URI:
    nel CORPO JSON la convenzione più diffusa è camelCase. Sono due
    linguaggi diversi; l'importante è non mescolare DENTRO ciascuno.
 3. MAI L'ESTENSIONE  il formato si negozia con Accept.
 4. MASSIMO DUE LIVELLI  /progetti/42/attivita ✅
    /progetti/42/attivita/9/commenti ❌ — la sotto-risorsa profonda
    diventa risorsa di primo livello: /attivita/9/commenti
 5. I FILTRI SONO QUERY  /progetti?stato=attivo ✅
    /progetti/stato/attivo ❌ è indistinguibile da
    /progetti/{id}/{sotto}: il routing diventa ambiguo.

LE AZIONI CHE NON SONO CRUD — tre strade oneste
  PATCH /progetti/42 { "stato": "archiviato" } quando l'azione È un
    cambio di stato. Da preferire.
  POST /progetti/42/inviti quando l'azione È una risorsa: l'invito ha
    un id, uno stato (in attesa, accettato, scaduto), si elenca e si
    revoca.
  POST /progetti/42/ricalcolo — un sostantivo che descrive
    l'operazione, non un verbo. Con parsimonia: se ne servono più di
    due o tre in tutta l'API, il modello delle risorse è sbagliato.
```

---
## A3. I metodi HTTP: safe e idempotente

> **Analogia:** i cartelli di un magazzino. "Sola lettura" vuol dire che chiunque può entrare senza cambiare nulla. "Ripetibile" vuol dire che se il fattorino consegna due volte lo stesso pacco per un errore di comunicazione, alla fine il magazzino contiene un pacco, non due. Proxy, browser e client automatici *contano* su queste proprietà.

| Metodo | Semantica | Safe | Idempotente |
|---|---|---|---|
| `GET` | Legge | ✅ | ✅ |
| `POST` | Crea, o azione non idempotente | ❌ | ❌ |
| `PUT` | Sostituisce integralmente | ❌ | ✅ |
| `PATCH` | Aggiorna parzialmente | ❌ | Dipende |
| `DELETE` | Elimina | ❌ | ✅ |

```
SAFE = non modifica lo stato del server. Il browser può fare prefetch
  senza chiedere permesso. Una GET che cancella è un incidente che
  aspetta: basta un antivirus aziendale che apre i link delle email.
IDEMPOTENTE = N ripetizioni producono lo stesso STATO FINALE. NON
  significa "stessa risposta": il primo DELETE dà 204, il secondo
  404. Lo stato finale è identico, ed è quello che conta.
```

```http
### PUT — sostituzione INTEGRALE: un campo omesso viene AZZERATO
PUT /api/v1/progetti/42
{ "nome": "Migrazione", "stato": "attivo", "responsabile": "usr_7" }

### PATCH con JSON Merge Patch (RFC 7396) — la forma più usata
PATCH /api/v1/progetti/42
Content-Type: application/merge-patch+json
{ "stato": "archiviato", "responsabile": null }
```

```
⚠ Con PUT, se il client invia solo { "nome": "Nuovo" }, il progetto
  perde stato e responsabile. È il comportamento CORRETTO di PUT: il
  bug è del client che lo usa per un aggiornamento parziale. Molte
  API "risolvono" trattando PUT come PATCH — è un errore: rende
  impossibile azzerare un campo di proposito.

JSON MERGE PATCH, LE TRE REGOLE
  valore → imposta    null → RIMUOVE    assente → invariato
  Il limite: non si può impostare un campo A null. Se il dominio
  distingue "nessun valore" da "campo assente" serve JSON Patch
  (RFC 6902): più potente (opera dentro gli array, e `test` dà un
  controllo di concorrenza gratuito) e molto meno comodo — quasi
  nessun client lo implementa.

PATCH È IDEMPOTENTE? Dipende dalle operazioni: { "stato": … } sì,
  [{ "op": "add", "path": "/tag/-" }] no (dieci volte, dieci tag).
  La specifica dice di no in generale. Se la tua implementazione lo
  è, DICHIARALO: i client possono allora riprovare.
```

---
## A4. I codici di stato che servono davvero

Ci sono oltre sessanta codici HTTP. In un'API ne servono dodici.

```
SUCCESSO
  200 OK       GET, PATCH, PUT riusciti. C'è un corpo.
  201 Created  POST che ha creato. DEVE avere l'header Location.
  202 Accepted Accettata ma NON ancora eseguita. Deve dire dove
               seguirne lo stato.
  204 No Content  Successo senza corpo, tipicamente DELETE.
               ⚠ Mai mandare un corpo con 204.
  304 Not Modified  Non cambiata dall'ETag inviato. Nessun corpo.

ERRORE DEL CLIENT
  400 Bad Request  MALFORMATA: il server non è riuscito a leggerla.
  401 Unauthorized  "Non so chi sei." ⚠ Il nome è storicamente
               sbagliato: significa NON AUTENTICATO.
  403 Forbidden  "So chi sei, e non puoi." Riprovare è inutile.
  404 Not Found  Non esiste — anche quando esiste ma l'utente non
               deve saperlo: evita di confermare l'esistenza.
  405 Method Not Allowed  L'URI esiste, il metodo no. Header Allow.
  409 Conflict  Contrasta con lo stato attuale.
  412 Precondition Failed  If-Match non combacia.
  422 Unprocessable Content  Sintassi corretta, SEMANTICA no.
  429 Too Many Requests  Limite superato. Deve avere Retry-After.

ERRORE DEL SERVER
  500 Internal Server Error  Messaggio pubblico generico, dettaglio
               nei log.   503 Service Unavailable  Manutenzione.

400 CONTRO 422 — la distinzione che quasi tutti sbagliano
  Il server è riuscito a LEGGERE la richiesta?
    NO → 400   { "nome": "Test",        ← virgola di troppo
    SÌ → rispetta le regole del dominio?
           NO → 422  { "inizio": "2026-12-31", "fine": "2026-01-01" }
           SÌ → procedi
  Usare 400 per tutto perde informazione: il client non sa se il
  problema è nel formato (bug suo) o nei dati (l'utente ha compilato
  male il modulo, e va evidenziato sul campo).

401 CONTRO 403  401 = "rifai il login", il client mostra l'accesso;
  403 = "non hai i permessi", il client mostra un messaggio.
  Confonderli produce l'interfaccia che rimanda al login in ciclo:
  l'utente accede, torna indietro, riaccede, e non capisce mai che
  semplicemente non ha i diritti.
```

---
## A5. La forma della risposta e degli errori

> **Analogia:** un modulo della pubblica amministrazione. Se "data di nascita" sta in alto a destra su un modulo e in basso a sinistra su un altro, chi compila deve ricominciare a cercare ogni volta.

```
// ❌ SBAGLIATO — tre endpoint, tre forme: il client scrive tre
//    funzioni di lettura invece di una
{ "progetti": [], "count": 27 }     { "data": [], "total": 143 }     [ ]
```

```json
// ✅ CORRETTO — una forma per ogni collezione. Per la singola
//    risorsa: l'oggetto, senza involucro.
{
  "elementi": [
    { "id": "prg_01HQ8X2K", "nome": "Migrazione", "stato": "attivo",
      "creatoIl": "2026-03-14T09:22:01Z" }
  ],
  "paginazione": { "limite": 20, "cursoreSuccessivo": "eyJpZCI6…", "haAltri": true }
}
```

```
LE CONVENZIONI SUI CAMPI
DATE   ISO 8601 in UTC con la Z: "2026-08-18T14:30:00Z". "18/08/2026"
       è ambiguo; senza la Z, 14:30 dove?
DENARO interi nell'unità minore più la valuta:
       { "importoCentesimi": 4990, "valuta": "EUR" }. Su mille righe
       l'errore in virgola mobile diventa visibile; su un documento
       fiscale è un problema legale. ⚠ Non tutte le valute hanno due
       decimali: lo yen ne ha zero, il dinaro tunisino tre.
ID     stringhe opache con prefisso: "prg_01HQ8X2K". Il prefisso rende
       visibile a occhio nudo un id di progetto passato dove serve un
       utente.
BOOL   nomi affermativi: "attivo": true, non "nonAttivo"
ENUM   stringhe: "in_revisione", non 2 (cosa vuol dire 2?)
NULL o ASSENTE?  Non sono la stessa cosa. La maggior parte delle API
       include sempre tutti i campi, con null dove manca il valore:
       forma prevedibile, tipi generati precisi.
camelCase o snake_case?  Non esiste una risposta giusta, esiste una
       risposta COERENTE. Scegline una, scrivila nella
       documentazione, non derogare mai.
```
## A6. Validare al confine con Zod

> **Analogia:** il controllo passaporti. Avviene una volta sola, all'ingresso. Dentro l'aeroporto nessuno ricontrolla a ogni negozio.

```typescript
// ❌ SBAGLIATO — richiesta.body è `any`: i tipi mentono. Se il
//    client manda { nome: 12345 }, arriva 12345 nel database.
//      risposta.status(201).json(await servizio.crea(richiesta.body))

// ✅ CORRETTO — uno schema al confine, tipi veri dentro
import { z } from 'zod'
import type { RequestHandler } from 'express'

const SchemaCreazioneProgetto = z
  .object({
    nome: z.string().trim().min(1, 'Il nome non può essere vuoto').max(200),
    inizio: z.coerce.date(),
    fine: z.coerce.date(),
    responsabile: z.string().regex(/^usr_[0-9A-HJKMNP-TV-Z]{10}$/),
  })
  // Le regole che coinvolgono PIÙ campi vanno in refine: una regola
  // per campo non può esprimerle
  .refine((dati) => dati.fine > dati.inizio, {
    message: 'La data di fine deve essere successiva alla data di inizio',
    path: ['fine'],
  })

// Il tipo si DERIVA dallo schema: uno solo, sempre allineato
export type CreazioneProgetto = z.infer<typeof SchemaCreazioneProgetto>

export const creaProgetto: RequestHandler = async (richiesta, risposta) => {
  // parse solleva ZodError, che il gestore traduce in 422. Da qui in
  // poi `dati` è tipato e VERO: nessun controllo ulteriore serve nei
  // livelli sottostanti.
  const dati = SchemaCreazioneProgetto.parse(richiesta.body)
  const progetto = await servizio.crea(dati)
  risposta.status(201).location(`/api/v1/progetti/${progetto.id}`).json(progetto)
}

// I query parameter arrivano SEMPRE come stringhe: serve coerce.
// L'ordinamento è una LISTA CHIUSA: mai passare la stringa del
// client direttamente in una ORDER BY. Anche l'id nel percorso va
// validato con la sua regex: senza, un id di un ALTRO tipo produce
// un 404 misterioso invece di un errore di validazione chiaro.
const SchemaElenco = z.object({
  limite: z.coerce.number().int().min(1).max(100).default(20),
  cursore: z.string().base64url().optional(),
  stato: z.enum(['bozza', 'attivo', 'sospeso', 'archiviato']).optional(),
  ordina: z.enum(['creatoIl', '-creatoIl', 'nome', '-nome']).default('-creatoIl'),
})
```

---
# Parte B — Comprensione Profonda

---

## B1. Il Richardson Maturity Model

Il modello serve non per assegnarsi un voto, ma per capire cosa si guadagna a ogni gradino.

```
LIVELLO 0 — un endpoint, un metodo
  POST /api/servizio  { "azione": "leggiProgetto", "id": 42 }
  Si perde: caching HTTP (tutto è POST allo stesso URI), retry
  sicuri (nulla è idempotente), log leggibili (dicono solo
  "POST /api/servizio" per tutto).
LIVELLO 1 — risorse: POST /api/progetti { "azione": "leggi", … }
  Si guadagna solo che i log dicono QUALE risorsa.
LIVELLO 2 — verbi HTTP e codici di stato
  Il caching funziona, i retry sono sicuri su GET/PUT/DELETE, proxy
  e browser capiscono la semantica, gli strumenti generici (curl,
  Postman, i client generati da OpenAPI) funzionano senza adattamenti.
  ➜ QUI SI FERMA IL 95% DELLE API IN PRODUZIONE, ed è una scelta
    ragionevole, non una resa.
LIVELLO 3 — hypermedia (HATEOAS)
  La risposta include i link alle azioni possibili: il server cambia
  gli URI senza rompere i client, e i permessi diventano impliciti.
  Costa risposte più grandi e client più complessi — e quasi nessun
  client segue davvero i link, quindi il vantaggio spesso evapora.
```

**Raccomandazione:** punta al livello 2 e fallo bene. Aggiungi hypermedia selettivamente dove porta un vantaggio concreto, tipicamente le azioni disponibili su una risorsa con macchina a stati (vedi D1).

---
## B2. Paginazione: offset, cursore, keyset

> **Analogia:** un elenco affisso in bacheca. L'offset è "riparti dalla riga 41": se qualcuno ha aggiunto un foglio all'inizio, la riga 41 non è più quella di prima. Il cursore è "riparti dopo la riga che diceva *Rossi Mario*": quella riga esiste ancora dov'era.

```
I DUE PROBLEMI DELL'OFFSET
1. I RISULTATI CHE SCIVOLANO
   t0  l'utente carica la pagina 1 → [P100 … P81]
   t1  qualcuno crea P101
   t2  l'utente chiede offset=20 → l'elenco è slittato, e l'offset
       20 punta a P81, che ha GIÀ visto
   Su uno scorrimento infinito produce elementi duplicati; con una
   cancellazione, un elemento sparisce senza essere mai visto.
2. LA DEGRADAZIONE PROFONDA
   LIMIT 20 OFFSET 100000 → il database legge e scarta centomila
   righe prima di restituirne venti. Il tempo cresce linearmente con
   l'offset, fino a saturare il pool di connessioni.
   ⚠ Misuralo sul tuo schema con EXPLAIN ANALYZE.
```

```sql
-- ❌ OFFSET: il database scarta 100.000 righe
SELECT id, nome FROM progetti
WHERE stato = 'attivo' ORDER BY creato_il DESC, id DESC
LIMIT 20 OFFSET 100000;

-- ✅ KEYSET: il database salta direttamente al punto
SELECT id, nome FROM progetti
WHERE stato = 'attivo'
  AND (creato_il, id) < ('2026-03-14 09:22:01+00', 'prg_01HQ8X2K')
ORDER BY creato_il DESC, id DESC LIMIT 20;
```

```
IL CONFRONTO A TUPLA È LA PARTE CHE QUASI TUTTI SBAGLIANO
  ❌ WHERE creato_il < X — se dieci progetti hanno lo STESSO istante
     di creazione (import di massa, precisione al secondo), nove
     vengono saltati.
  ❌ WHERE creato_il < X OR (creato_il = X AND id < Y) — logicamente
     corretto, ma il pianificatore spesso non usa l'indice composto.
  ✅ WHERE (creato_il, id) < (X, Y) — PostgreSQL lo traduce in una
     ricerca diretta sull'indice; MySQL 8 e SQLite lo supportano. La
     seconda colonna deve essere UNICA e stabile: l'id rompe i
     pareggi in modo deterministico.

IL CURSORE È IL CONTRATTO, IL KEYSET L'IMPLEMENTAZIONE  il cursore è
  OPACO: il client lo ripassa così com'è. Se resta opaco, il server
  può cambiare strategia senza rompere nulla; se il client impara che
  è base64 di un id, quel dettaglio è diventato parte del contratto.

IL TRUCCO DEL "LIMITE + 1"  si chiede un elemento in più del limite:
  la sua presenza dice se ci sono altre pagine, senza un
  SELECT COUNT(*) — un secondo scan completo, spesso più costoso
  della query principale.

LA PAGINAZIONE NON È FACOLTATIVA  un endpoint che restituisce tutta
  la collezione funziona con i cinquanta record dello sviluppo e
  mette in ginocchio il server con i due milioni della produzione.
  Il limite lo IMPONE il server: assente → 20; 5000 → 422.
```

| Situazione | Strategia | Perché |
|---|---|---|
| Feed, scorrimento infinito | Cursore + keyset | I dati cambiano sotto; l'offset duplica |
| Tabella con "vai a pagina 47" | Offset | Il salto arbitrario è un requisito |
| Esportazione completa | Cursore | L'offset profondo satura il database |
| Elenco piccolo e stabile (<500) | Nessuna | La complessità non si ripaga |
| Ricerca per rilevanza | Offset limitato a N pagine | Il punteggio non ha chiave stabile |

---
## B3. Filtri e ordinamento: la lista chiusa

```
GET /api/v1/progetti?stato=attivo,sospeso          lista OR
GET /api/v1/progetti?budget[gte]=10000&budget[lte]=50000
GET /api/v1/progetti?cerca=migrazione+contabilità
GET /api/v1/progetti?ordina=-priorita,nome         - = discendente
GET /api/v1/progetti?campi=id,nome,stato           sparse fieldsets
```

La sintassi a parentesi per gli operatori vince perché Express e Fastify la analizzano nativamente in oggetti annidati ed è rappresentabile in OpenAPI con `style: deepObject`. L'alternativa `?filtro=budget>=10000` è la più espressiva e la peggiore: diventa un linguaggio da analizzare, con i problemi di sicurezza che comporta.

```typescript
// ❌ PERICOLOSO — l'ordinamento del client finisce in SQL
// db.query(`SELECT * FROM progetti ORDER BY ${richiesta.query['ordina']}`)
//   → ordina=id; DROP TABLE progetti; --
//   Le query parametrizzate NON proteggono i nomi di colonna: un
//   identificatore non può essere un parametro.

// ✅ SICURO — una mappa da valore pubblico a frammento reale. La
//    chiave è già ristretta dal tipo: qualunque altra stringa è
//    stata rifiutata da Zod prima di arrivare qui.
const ORDINAMENTI = {
  creatoIl: 'creato_il ASC',
  '-creatoIl': 'creato_il DESC',
  nome: 'nome ASC',
  '-nome': 'nome DESC',
} as const

function clausolaOrdinamento(richiesto: keyof typeof ORDINAMENTI): string {
  return ORDINAMENTI[richiesto]
}
```

```
IL PRINCIPIO, VALIDO OLTRE L'ORDINAMENTO  tutto ciò che dal client
  finisce in una posizione STRUTTURALE — nome di colonna, di tabella,
  direzione, nome di file, chiave di configurazione — passa per una
  MAPPA con chiavi note, mai per concatenazione. I parametri
  proteggono i VALORI, non la STRUTTURA.

LA REGOLA CHE VALE PER TUTTI I FILTRI  ogni combinazione esprimibile
  dal client deve poter essere servita da un INDICE. Se un filtro non
  ha un indice, o lo si indicizza o non lo si espone. La terza via —
  esporlo e sperare — finisce in una chiamata notturna.

SPARSE FIELDSETS: valgono quando la risorsa ha campi pesanti e
  raramente usati e il client mobile ha banda limitata. Su otto campi
  scalari no: si risparmiano poche centinaia di byte e in cambio il
  caching si frammenta e i tipi generati diventano tutti Partial<T>.
  ⚠ L'id va incluso SEMPRE, anche se non richiesto.
```

---
## B4. Idempotenza e Idempotency-Key

> **Analogia:** l'ascensore. Premere il pulsante del terzo piano dieci volte non fa salire l'ascensore al trentesimo: esprime uno stato desiderato, non un incremento.

```
   CLIENT                                      SERVER
     │  POST /pagamenti { importo: 10000 }        │
     │───────────────────────────────────────────►│ addebita 100 €
     │            201 Created                     │ ✅ riuscito
     │◄──────────────╳ la connessione cade        │
     │  Il client NON SA se è andato a buon fine.
     │  Riprova?     → rischio di doppio addebito
     │  Non riprova? → forse il cliente non ha pagato
     │  Non c'è una scelta giusta: il problema è nel
     │  PROTOCOLLO, non nel client.

L'IDEMPOTENZA NATURALE  GET per definizione; PUT perché esprime uno
  STATO desiderato; DELETE perché il primo elimina e i successivi
  trovano già eliminato. POST no: crea qualcosa di nuovo ogni volta,
  ed è l'unico che ha bisogno di aiuto.
```

```typescript
// src/middleware/idempotenza.ts — deve stare DOPO il parsing del
// corpo (serve l'impronta) e PRIMA delle rotte
import type { RequestHandler } from 'express'
import { createHash } from 'node:crypto'
import { z } from 'zod'
import { redis } from '../redis.js'
import { ErroreConflitto, ErroreValidazione } from '../errori/problema.js'

type RispostaMemorizzata = { status: number; corpo: unknown; impronta: string }

export const idempotenza: RequestHandler = async (richiesta, risposta, prossimo) => {
  const intestazione = richiesta.get('Idempotency-Key')
  if (richiesta.method !== 'POST' || !intestazione) return prossimo()

  const chiaveValida = z.string().uuid().safeParse(intestazione)
  if (!chiaveValida.success) {
    return prossimo(
      new ErroreValidazione([{ percorso: 'Idempotency-Key', messaggio: 'deve essere un UUID' }]),
    )
  }

  // La chiave è per ENDPOINT: la stessa chiave su percorsi diversi
  // sono operazioni diverse. L'impronta del corpo scopre il riuso
  // ERRATO della chiave.
  const chiave = `idem:${richiesta.path}:${chiaveValida.data}`
  const impronta = createHash('sha256')
    .update(JSON.stringify(richiesta.body ?? {}))
    .digest('hex')

  const memorizzato = await redis.get(chiave)

  if (memorizzato) {
    const precedente = JSON.parse(memorizzato) as RispostaMemorizzata

    // ⚠ Stessa chiave, corpo DIVERSO: è un bug del client, non un
    //   retry. Restituire la risposta vecchia produrrebbe un
    //   pagamento che il cliente crede fatto e non è stato.
    if (precedente.impronta !== impronta) {
      return prossimo(new ErroreConflitto('Chiave già usata con un corpo diverso.'))
    }

    risposta.setHeader('Idempotent-Replay', 'true')
    risposta.status(precedente.status).json(precedente.corpo)
    return
  }

  // Il lock impedisce che due richieste concorrenti con la stessa
  // chiave (doppio clic, retry aggressivo) eseguano entrambe
  if (!(await redis.set(`${chiave}:lock`, '1', { NX: true, EX: 60 }))) {
    return prossimo(new ErroreConflitto('Una richiesta con la stessa chiave è in corso.'))
  }

  const jsonOriginale = risposta.json.bind(risposta)

  risposta.json = (corpo: unknown) => {
    // SOLO i successi: un 500 memorizzato bloccherebbe per
    // ventiquattro ore la possibilità di riprovare
    if (risposta.statusCode >= 200 && risposta.statusCode < 300) {
      void redis.set(chiave, JSON.stringify({ status: risposta.statusCode, corpo, impronta }), {
        EX: 24 * 60 * 60,
      })
    }
    void redis.del(`${chiave}:lock`)
    return jsonOriginale(corpo)
  }

  // Il lock va rilasciato anche se non si arriva mai a json()
  risposta.on('close', () => void redis.del(`${chiave}:lock`))

  prossimo()
}
```

```
DOVE SERVE  pagamenti e rimborsi · invio di email e notifiche ·
  creazione di ordini · chiamate a servizi esterni a pagamento →
  obbligatoria. Creazione di risorse ordinarie → consigliata.
  Regola: se ripetere l'operazione costa denaro, imbarazza un utente
  o produce un duplicato che qualcuno dovrà ripulire a mano, serve
  l'idempotenza.
```

---
## B5. Concorrenza: ETag e If-Match

> **Analogia:** due persone modificano lo stesso documento cartaceo. Anna lo fotocopia alle 9:00, Bruno alle 9:05. Anna corregge il paragrafo 3 e rimette il foglio alle 9:30. Bruno corregge il paragrafo 7 sulla SUA copia — che non contiene la correzione di Anna — e la rimette alle 9:40. Il lavoro di Anna è sparito, e nessuno dei due lo sa.

```
LE TRE RISPOSTE POSSIBILI
  1. NON FARE NULLA (l'ultimo vince)  la scelta implicita di chi non
     ci pensa. Accettabile solo se le modifiche concorrenti sono rare
     e il danno lieve.
  2. LOCKING PESSIMISTICO  Bruno non può nemmeno aprire finché Anna
     non ha finito. Corretto ma pessimo da usare: i lock restano
     appesi quando qualcuno chiude il browser.
  3. LOCKING OTTIMISTICO (ETag + If-Match)  tutti possono modificare;
     chi arriva secondo con una copia vecchia viene RIFIUTATO e deve
     rileggere. ← quasi sempre la risposta giusta per un'API HTTP

  GET  /progetti/prg_01HQ8X2K              → 200 · ETag: "7a3f9c2e"
  PATCH … con If-Match: "7a3f9c2e"         → 200 · ETag: "b1e4d8a0"
  PATCH … con lo stesso If-Match, dopo che qualcuno ha modificato
                                           → 412 Precondition Failed
```

```typescript
// ❌ IL DIFETTO CHE HANNO QUASI TUTTE LE IMPLEMENTAZIONI: fra la
//    lettura e la scrittura c'è una finestra in cui un altro
//    processo può scrivere. Il controllo passa, la scrittura
//    sovrascrive comunque.
//      const attuale = await trova(id)
//      if (calcolaEtag(attuale) !== ifMatch) throw new ErrorePrecondizione()
//      await aggiorna(id, dati)       ← la finestra è già aperta

// ✅ Il controllo va DENTRO la scrittura, in una sola operazione
//    atomica. Nessuna riga restituita = la versione era cambiata → 412
export async function aggiornaSeVersione(
  id: string,
  versioneAttesa: number,
  dati: { budgetCentesimi: number },
): Promise<Progetto | null> {
  const righe = await sql<Progetto[]>`
    UPDATE progetti
    SET budget_centesimi = ${dati.budgetCentesimi},
        versione = versione + 1, aggiornato_il = now()
    WHERE id = ${id} AND versione = ${versioneAttesa}
    RETURNING *
  `
  return righe[0] ?? null
}
```

```
412 CONTRO 428
  412 Precondition Failed    If-Match c'è ma non combacia.
  428 Precondition Required  If-Match manca del tutto.
  Richiedere If-Match su tutte le scritture è la scelta rigorosa;
  molte API lo rendono facoltativo. Va documentato quale delle due
  si adotta: è parte del contratto.
```

---
## B6. Caching HTTP

> **Analogia:** la biblioteca. Se il libro è sul tuo scrittoio lo apri; se è nella tua stanza ti alzi; se è in biblioteca ci vai. Ogni gradino costa un ordine di grandezza in più.

```http
### Risorsa pubblica e stabile
Cache-Control: public, max-age=300, stale-while-revalidate=60

### Dati personali: mai in una cache condivisa
Cache-Control: private, max-age=0, must-revalidate
Vary: Authorization

### Token e risposte di pagamento: da non memorizzare affatto
Cache-Control: no-store

### Asset con impronta nel nome (app.a3f9c2.js)
Cache-Control: public, max-age=31536000, immutable
```

```
LE DIRETTIVE CHE SI CONFONDONO
  public  qualunque cache, CDN comprese. ⚠ Su una risposta con dati
          personali significa che la CDN può servirli a un altro
          utente: è l'errore che produce i titoli sui giornali.
  no-cache  ⚠ NON significa "non memorizzare", significa "memorizza
          ma chiedi sempre se è ancora valida". Con l'ETag la
          risposta è un 304 senza corpo.  no-store  QUESTO sì.
  immutable  non chiedere mai la rivalidazione. Solo per URI con
          impronta nel nome.
  stale-while-revalidate=N  per N secondi dopo la scadenza serve la
          copia vecchia SUBITO e aggiorna in sottofondo.

LA RIVALIDAZIONE CON ETag  una GET con If-None-Match su una risorsa
  non cambiata torna 304 senza corpo: su 240 kB il round-trip resta,
  il trasferimento no.

L'HEADER `Vary` È LA PARTE CHE SI DIMENTICA  elenca gli header di
  RICHIESTA che cambiano la risposta: la cache costruisce la chiave
  con URI + questi header. Qualunque risposta che dipende
  dall'identità porta SIA `private` SIA `Vary: Authorization`.

⚠ `max-age=0` con ETag non significa "nessun caching": significa
  "verifica sempre, ma se non è cambiato risparmiati il corpo".
  Spesso è la scelta migliore per i dati personali.
```

---
## B7. Versionamento: cos'è un breaking change

Prima di scegliere COME versionare serve sapere QUANDO. La maggior parte delle discussioni salta questo passaggio e finisce a parlare di URL.

```
NON È BREAKING
  ✅ aggiungere un campo FACOLTATIVO, un endpoint o un parametro
     facoltativo
  ✅ rendere facoltativo un campo prima obbligatorio
  ✅ allargare un vincolo (max 100 → max 500 caratteri)
  ⚠ aggiungere un valore a un enum di RISPOSTA: solo se i client
    sono documentati per ignorare i valori sconosciuti. Altrimenti
    un `switch` esaustivo esplode.

È BREAKING
  ❌ rimuovere o rinominare un campo, cambiarne il tipo
  ❌ cambiare il SIGNIFICATO a parità di nome e tipo (`importo` da
     euro a centesimi: ogni client sbaglia di cento volte senza
     accorgersene — il più pericoloso, perché silenzioso)
  ❌ rendere obbligatorio un campo facoltativo, restringere un
     vincolo, rimuovere un valore da un enum
  ❌ cambiare un codice di stato, l'ordinamento predefinito o il
     formato degli id
  ❌ aggiungere una validazione che prima non c'era

IL CRITERIO PER I CASI DUBBI  prendi un client che segue la
  documentazione alla lettera e applica il cambiamento: continua a
  funzionare? Non è breaking. Poi prendi un client scritto MALE ma
  diffuso — perché esiste sempre. Se rompe solo quello, la decisione
  è politica, non tecnica.

LE TRE STRATEGIE
  /api/v1/progetti  NEL PERCORSO — visibile, si prova con browser e
    curl, nei log si vede subito chi usa cosa. ❌ formalmente
    scorretto (due URI per la stessa risorsa) e costringe a
    versionare tutta l'API insieme.
  Accept: application/vnd.esempio.v2+json — un URI per risorsa,
    versionabile per singola risorsa. ❌ invisibile (nel browser si
    ottiene la predefinita); il caching richiede Vary: Accept.
  API-Version: 2026-08-01  A DATA — è ovvio quanto è vecchia la
    versione usata, e si può FISSARE per chiave API: il client non
    cambia comportamento finché non decide lui. ❌ richiede
    infrastruttura per N versioni attive.
  ➜ API interna o piccola → /v1 nel percorso. API pubblica con molti
    client → versione a data, fissata per chiave. In entrambi i casi:
    la versione dal PRIMO giorno, altrimenti /api/progetti resterà in
    vita per sempre come "v0".

IL VERSIONAMENTO MIGLIORE È NON AVERNE BISOGNO: "espandi e contrai"
  1. ESPANDI (mesi 0-6)  il campo nuovo appare accanto al vecchio,
     entrambi funzionano, nessuno si rompe
  2. MIGRA (mesi 6-12)   il vecchio è deprecato nella documentazione
     e nell'header Deprecation; si misura chi lo usa ancora (D5) e
     si contattano quei client
  3. CONTRAI (mese 12+)  il vecchio sparisce
  Evita una versione nuova per il 90% dei cambiamenti.
```

---
## B8. OpenAPI 3.1 come sorgente di verità

> **Analogia:** il progetto depositato in comune. Non è la casa, ma è ciò che l'impresa costruisce e ciò che il geometra verifica. Se il progetto e la casa divergono, il problema non è del progetto.

```yaml
openapi: 3.1.0
info:
  title: API Gestione Progetti
  version: 1.0.0
  license: { name: MIT, identifier: MIT }
servers:
  - url: https://api.esempio.it/v1
security:
  - tokenBearer: []

paths:
  /progetti:
    get:
      summary: Elenca i progetti
      description: |
        La paginazione è a cursore: `paginazione.cursoreSuccessivo`
        va passato tale e quale come parametro `cursore` della
        richiesta successiva, senza interpretarlo.
      operationId: elencaProgetti
      parameters:
        - name: limite
          in: query
          schema: { type: integer, minimum: 1, maximum: 100, default: 20 }
        - name: cursore
          in: query
          description: Token opaco. Non va interpretato né costruito.
          schema: { type: string }
      responses:
        '200':
          description: Elenco dei progetti
          content:
            application/json:
              schema:
                type: object
                required: [elementi, paginazione]
                properties:
                  elementi:
                    type: array
                    items: { $ref: '#/components/schemas/Progetto' }
                  paginazione:
                    type: object
                    required: [limite, haAltri]
                    properties:
                      limite: { type: integer }
                      cursoreSuccessivo: { type: [string, 'null'] }
                      haAltri: { type: boolean }
        '422':
          description: Problem Details secondo RFC 9457
          content:
            application/problem+json:
              schema: { type: object, required: [type, title, status] }

components:
  securitySchemes:
    tokenBearer: { type: http, scheme: bearer, bearerFormat: JWT }
  schemas:
    Progetto:
      type: object
      required: [id, nome, stato, creatoIl]
      properties:
        id:
          type: string
          pattern: '^prg_[0-9A-HJKMNP-TV-Z]{10}$'
          examples: ['prg_01HQ8X2KQZ']
        nome: { type: string, minLength: 1, maxLength: 200 }
        # OpenAPI 3.1: type unione, non più `nullable: true`
        descrizione: { type: [string, 'null'], maxLength: 5000 }
        stato: { type: string, enum: [bozza, attivo, sospeso, archiviato] }
        budgetCentesimi: { type: integer, minimum: 0 }
        creatoIl: { type: string, format: date-time }
```

```powershell
# I tipi TypeScript dal contratto, per i client
pnpm dlx openapi-typescript openapi.yaml -o src/tipi-api.ts
# Verificare che il contratto sia valido e coerente
pnpm dlx @redocly/cli lint openapi.yaml
# Un server mock dal contratto: il frontend parte subito
pnpm dlx @stoplight/prism-cli mock openapi.yaml
```

```
LE NOVITÀ DI OpenAPI 3.1 CHE CAMBIANO COME SI SCRIVE
  1. È JSON SCHEMA 2020-12 COMPLETO. Prima era un dialetto
     quasi-compatibile: ora gli schemi si riusano fra validazione,
     documentazione e test.
  2. `type: [string, 'null']` invece di `nullable: true`
  3. `examples` (array) invece di `example` (deprecato)
  4. `webhooks` come sezione di primo livello
  5. `license.identifier` con un codice SPDX

SCHEMA-FIRST O CODE-FIRST?
  SCHEMA-FIRST  il contratto esiste prima dell'implementazione: il
    frontend lavora da subito su un mock, e il contratto è
    discutibile prima che costi cambiarlo. ❌ codice e schema
    possono divergere → serve un test di conformità in CI
  CODE-FIRST  non possono divergere, meno file da mantenere. ❌ il
    contratto EMERGE dall'implementazione invece di guidarla: si
    finisce con URI che riflettono le tabelle
  LA VIA DI MEZZO: gli schemi Zod sono la sorgente e l'OpenAPI si
  genera da quelli (zod-to-openapi). Un solo posto per validazione
  runtime, tipi e documentazione.
```

---
## B9. Rate limiting, webhook, operazioni bulk

### Rate limiting: gli header del contratto

Gli algoritmi sono in `tutorial_22_rate_limiting_edge.md`. Qui interessa il *contratto*: come l'API comunica il limite.

```http
### Ogni risposta porta lo stato del limite
RateLimit: limit=100, remaining=87, reset=42
RateLimit-Policy: 100;w=60

### Quando il limite è superato: 429 + application/problem+json
RateLimit: limit=100, remaining=0, reset=17
Retry-After: 17
```

```
  limit = il tetto nella finestra · remaining = quante ne restano ·
  reset = fra quanti SECONDI la finestra si azzera. Retry-After solo
  sui 429 e sui 503.

⚠ Gli header vanno su OGNI risposta, non solo sui 429: così un client
  ben scritto rallenta PRIMA di sbattere contro il limite. Senza, chi
  riceve 429 può solo tirare a indovinare — e in pratica riprova
  subito, in ciclo, peggiorando la situazione che il limite doveva
  evitare. Nota: per anni ognuno ha usato la sua versione con
  prefisso X-; un'API nuova usa la forma standardizzata senza.

I LIMITI VANNO DIFFERENZIATI PER OPERAZIONE  GET su collezione
  1000/min · POST che crea 100/min · autenticazione 10/min e
  reimpostazione password 3/ora (forza bruta) · esportazione completa
  2/ora (costo del database). La chiave del contatore è l'UTENTE se
  c'è, altrimenti l'IP: limitare solo per IP penalizza chi è dietro
  NAT aziendale.
```
### Webhook: la consegna at-least-once

> **Analogia:** il postino con l'avviso di ricevimento. Se il cartellino della firma si perde nel tragitto torna di nuovo, anche se il pacco era già stato consegnato. Chi riceve deve essere pronto a vedere lo stesso pacco due volte e a non pagarlo due volte.

```
   evento → coda persistente → motore di consegna → POST
            tentativo 1: subito       ├─ 2xx → consegnato
            tentativo 2: 1 s + jitter ├─ 4xx → PERMANENTE:
            tentativo 3: 4 s + jitter │        non riprovare
            tentativo 4: 16 s         └─ 5xx → riprova
            … fino a 24 ore, poi Dead Letter Queue
```

```json
{
  "id": "evt_01HQ8X2KQZ",
  "tipo": "progetto.archiviato",
  "creatoIl": "2026-08-18T14:30:00Z",
  "versioneApi": "2026-08-01",
  "dati": {
    "oggetto": { "id": "prg_01HQ8X2K", "stato": "archiviato" },
    "attributiPrecedenti": { "stato": "attivo" }
  }
}
```

`attributiPrecedenti` fa la differenza: senza, il consumatore sa che il progetto *ora* è archiviato ma non da quale stato veniva, e per saperlo deve tenere una copia propria o interrogare l'API — a quel punto il webhook ha risparmiato poco.

```typescript
// La firma nello stile Stripe: HMAC su `timestamp.corpoGrezzo`. Il
// timestamp impedisce il replay di una richiesta catturata.
import { createHmac, timingSafeEqual } from 'node:crypto'

export function verificaFirmaWebhook(
  corpoGrezzo: string,
  timestamp: number,
  firmaRicevuta: string,
  segreto: string,
): void {
  if (Math.abs(Date.now() / 1000 - timestamp) > 300) throw new Error('timestamp fuori tolleranza')

  const attesa = createHmac('sha256', segreto)
    .update(`${timestamp}.${corpoGrezzo}`, 'utf8')
    .digest('hex')

  // ⚠ Confronto a tempo costante: con === un attaccante ricostruisce
  //   la firma un byte alla volta misurando i tempi di risposta
  const a = Buffer.from(attesa, 'hex')
  const b = Buffer.from(firmaRicevuta, 'hex')
  if (a.length !== b.length || !timingSafeEqual(a, b)) throw new Error('firma non valida')
}
```

```
LE CINQUE REGOLE DEL WEBHOOK CHE FUNZIONA
  1. FIRMA SUL CORPO GREZZO. ⚠ express.raw PRIMA di express.json su
     quella rotta: se il JSON viene analizzato e riserializzato,
     l'ordine delle chiavi può cambiare e la firma non combacia più.
     Sulla firma non valida si risponde 401, non 400.
  2. RISPOSTA IMMEDIATA (202), elaborazione in sottofondo: il
     produttore ha un timeout di 5-10 secondi.
  3. IDEMPOTENZA presso il consumatore, con la registrazione
     dell'evento NELLA STESSA TRANSAZIONE dell'effetto: se sono due
     transazioni separate, un crash fra le due produce un effetto
     applicato e non registrato, che alla consegna successiva viene
     applicato una seconda volta.
  4. RETRY CON BACKOFF ESPONENZIALE E JITTER: senza jitter, mille
     consumatori riprovano nello stesso istante.
  5. DEAD LETTER QUEUE, monitorata. Una DLQ che cresce è un allarme;
     una che nessuno guarda è un archivio di eventi persi.
```
### Operazioni bulk e successo parziale

Una risposta bulk è `200 OK` — l'operazione bulk *è riuscita*, e riferisce l'esito di ciascuna sotto-operazione in un array di `{ indice, status, dati }` oppure `{ indice, status, problema }`. L'alternativa `207 Multi-Status` è semanticamente più precisa ma molti strumenti non la riconoscono.

```
❌ MAI 201 o 204: non corrispondono a nessuna operazione.
❌ MAI 4xx perché una sotto-operazione è fallita: il client
   penserebbe che tutto è stato rifiutato e riproverebbe tutto,
   duplicando le riuscite.

LE QUATTRO DECISIONI DA DOCUMENTARE ESPLICITAMENTE
  1. IL LIMITE MASSIMO di operazioni (tipicamente 100-1000). Senza,
     un client ne invia centomila e il server resta occupato per
     un'ora su una sola connessione.
  2. ATOMICO O BEST-EFFORT? Sono contratti diversi e i client si
     comportano diversamente. Non si cambia dopo.
  3. L'ORDINE di esecuzione è garantito? Se le operazioni hanno
     dipendenze, l'ordine è parte del contratto.
  4. L'IDEMPOTENCY-KEY COPRE L'INTERO LOTTO, non le singole.
  ⚠ L'esecuzione va SEQUENZIALE, non con Promise.all: cento scritture
    in parallelo saturano il pool e rendono l'intera API lenta per
    tutti gli altri. Oltre le poche centinaia di operazioni serve
    l'accettazione asincrona con 202 (vedi D3).
```

---
## B10. Scegliere il paradigma

| Criterio | REST | GraphQL | gRPC | tRPC |
|---|---|---|---|---|
| Client esterni sconosciuti | ✅ ideale | ⚠ possibile | ❌ | ❌ |
| Caching HTTP nativo | ✅ | ❌ (POST) | ❌ | ❌ |
| Un client, molte forme di dati | ⚠ over-fetching | ✅ ideale | ⚠ | ⚠ |
| Latenza minima fra servizi | ⚠ | ❌ | ✅ ideale | ⚠ |
| Type safety senza generazione | ❌ | ❌ | ❌ | ✅ ideale |
| Strumenti generici (curl) | ✅ | ⚠ | ❌ | ❌ |

```
I COSTI CHE SI SCOPRONO DOPO
  GraphQL  senza DataLoader una query annidata genera migliaia di
           query (N+1); una query arbitrariamente annidata è un
           attacco di esaurimento risorse, e servono limiti di
           profondità, analisi di costo e persisted query. Il caching
           HTTP non funziona.
  gRPC     non funziona da browser senza un proxy (gRPC-Web).
  tRPC     vincola client e server allo stesso linguaggio e
           repository. Il giorno in cui serve un client mobile nativo
           o un partner esterno, si riparte da REST.

LA SCELTA IBRIDA È SPESSO QUELLA GIUSTA: REST per l'API pubblica e i
webhook, gRPC fra i servizi interni, tRPC per il frontend nello
stesso repository. Non è incoerenza: sono tre pubblici diversi.
```

Il trattamento completo di GraphQL è in `tutorial_24_graphql.md`.

---
# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Correggere un'API mal progettata

**Obiettivo:** trovare tutte le violazioni in questa tabella di endpoint, correggerle e dire perché.

```
GET    /api/getAllUsers                POST /api/user/create
POST   /api/user/42/delete             GET  /api/users/role/admin
POST   /api/users/42/setEmail          GET  /api/users.json?page=2
GET    /api/user/42/orders/7/items/3/reviews
POST   /api/orders/42/pay          → risponde 200 { "ok": false }
```

```
# SOLUZIONE

GET /api/v1/utenti?limite=20&cursore=…
  verbo nell'URI; nessuna versione; nessuna paginazione ("getAll" su
  una tabella da due milioni di righe è un incidente in attesa).

POST /api/v1/utenti  → 201 + Location
  verbo nell'URI; singolare; POST già significa "crea".

DELETE /api/v1/utenti/42  → 204
  POST per eliminare rende l'operazione NON idempotente e non
  ripetibile in sicurezza. DELETE lo è.

GET /api/v1/utenti?ruolo=admin
  il filtro come segmento di path è indistinguibile da
  /utenti/{id}/{sotto-risorsa}: il routing diventa ambiguo.

PATCH /api/v1/utenti/42  { "email": "…" }  → 200
  "setEmail" è un verbo; l'aggiornamento parziale di un campo è
  esattamente il caso d'uso di PATCH.

GET /api/v1/articoli-ordine/3/recensioni
  cinque livelli di annidamento: il client deve conoscere tutta la
  catena per arrivare in fondo. La sotto-risorsa profonda diventa
  risorsa di primo livello.

GET /api/v1/utenti?limite=20&cursore=…
  l'estensione .json blocca il formato nell'URI (si negozia con
  Accept); la paginazione a pagine perde e duplica elementi quando i
  dati cambiano sotto.

POST /api/v1/ordini/42/pagamenti  → 201 o 402
  "pay" è un verbo — e il pagamento È una risorsa (ha un id, uno
  stato, si elenca, si rimborsa). Ma soprattutto: 200 con
  { "ok": false } è l'anti-pattern più grave della tabella. Un client
  che controlla solo il codice di stato — cioè quasi tutti — pensa
  che il pagamento sia riuscito. L'errore DEVE stare nel codice di
  stato.
```

---
### Esercizio 2 — Paginazione a cursore con keyset

**Obiettivo:** implementare un elenco paginato che non perde né duplica elementi quando i dati cambiano, con prestazioni costanti a qualunque profondità.

```typescript
// SOLUZIONE — src/repository/progetti.ts
import { sql } from '../database.js'
import { codificaCursore, decodificaCursore, type Cursore } from '../paginazione.js'

export type Progetto = { id: string; nome: string; stato: string; creatoIl: Date }

export async function elencaProgetti(opzioni: { limite: number; cursore?: string }) {
  const dopo: Cursore | null = opzioni.cursore ? decodificaCursore(opzioni.cursore) : null

  // Il confronto a TUPLA: PostgreSQL lo risolve con una ricerca
  // diretta sull'indice composto. Il secondo termine (l'id) rompe i
  // pareggi fra righe con lo stesso istante di creazione: senza, un
  // import che inserisce cento righe nello stesso secondo ne fa
  // saltare novantanove.
  // Si chiede un elemento IN PIÙ del limite: la sua presenza dice
  // che esiste un'altra pagina, senza un SELECT COUNT(*) — che su
  // una tabella grande è più costoso della query stessa.
  const righe = await sql<Progetto[]>`
    SELECT id, nome, stato, creato_il AS "creatoIl"
    FROM progetti
    WHERE ${dopo === null}
       OR (creato_il, id) < (${dopo?.creatoIl ?? null}::timestamptz, ${dopo?.id ?? null})
    ORDER BY creato_il DESC, id DESC
    LIMIT ${opzioni.limite + 1}
  `

  const haAltri = righe.length > opzioni.limite
  const elementi = haAltri ? righe.slice(0, opzioni.limite) : righe
  const ultimo = elementi.at(-1)

  return {
    elementi,
    paginazione: {
      limite: opzioni.limite,
      cursoreSuccessivo:
        haAltri && ultimo
          ? codificaCursore({ creatoIl: ultimo.creatoIl.toISOString(), id: ultimo.id })
          : null,
      haAltri,
    },
  }
}
```

```sql
-- L'indice SENZA il quale tutto questo non serve a nulla. L'ordine
-- delle colonne conta: prima i filtri di uguaglianza, poi quelle di
-- ordinamento nella direzione della query. Il piano di EXPLAIN
-- ANALYZE deve dire "Index Scan", non "Seq Scan".
CREATE INDEX idx_progetti_keyset
  ON progetti (stato, creato_il DESC, id DESC);
```

```
# LA VERIFICA CHE DIMOSTRA LA PROPRIETÀ CHE L'OFFSET NON HA
#   1. carica la pagina 1 con limite=20
#   2. crea un progetto NUOVO, che entra in cima all'ordinamento
#   3. chiedi la pagina 2 con il cursoreSuccessivo
#   → nessun id della pagina 1 deve ricomparire nella pagina 2
#   Con l'offset, l'ultimo elemento della pagina 1 riapparirebbe
#   come primo della pagina 2.
#   4. passa un cursore fabbricato a mano → 400, non 500
```

---
### Esercizio 3 — Idempotenza che scopre il riuso errato della chiave

**Obiettivo:** dimostrare con un test che il middleware distingue un retry legittimo da un riuso sbagliato della chiave — la differenza fra un pagamento e due.

```typescript
// SOLUZIONE — test/idempotenza.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import request from 'supertest'
import { creaApp } from '../src/app.js'
import { redis } from '../src/redis.js'

describe('Idempotency-Key', () => {
  const app = creaApp()
  const chiave = '4f8c2a91-7e3b-4d55-9a01-6c8f2b1e5d3a'
  const corpo = { ordineId: 'ord_01HQ8X', importoCentesimi: 10_000, valuta: 'EUR' }

  const invia = (dati: unknown) =>
    request(app).post('/api/v1/pagamenti').set('Idempotency-Key', chiave).send(dati)

  beforeEach(async () => {
    await redis.flushDb()
    vi.restoreAllMocks()
  })

  it('il retry con la STESSA chiave e lo STESSO corpo non riesegue', async () => {
    const addebita = vi.spyOn(servizioPagamenti, 'addebita')

    const prima = await invia(corpo)
    const seconda = await invia(corpo)

    expect(seconda.body).toEqual(prima.body)
    expect(seconda.headers['idempotent-replay']).toBe('true')
    // ← LA VERIFICA CHE CONTA: l'addebito è avvenuto UNA volta
    expect(addebita).toHaveBeenCalledTimes(1)
  })

  it('la STESSA chiave con un corpo DIVERSO viene rifiutata con 409', async () => {
    await invia(corpo)
    // Importo diverso: è un'operazione DIVERSA, non un retry. Senza
    // il controllo dell'impronta qui arriverebbe 201 con la risposta
    // del PRIMO pagamento: il cliente crederebbe di aver pagato
    // 500 € e ne avrebbe pagati 100.
    expect((await invia({ ...corpo, importoCentesimi: 50_000 })).status).toBe(409)
  })

  it('un errore 500 NON viene memorizzato: si può riprovare', async () => {
    vi.spyOn(servizioPagamenti, 'addebita').mockRejectedValueOnce(new Error('gateway giù'))

    expect((await invia(corpo)).status).toBe(500)
    // Se il 500 fosse stato memorizzato, questa riceverebbe di nuovo
    // 500 per ventiquattro ore
    expect((await invia(corpo)).status).toBe(201)
  })

  it('due richieste concorrenti: una esegue, una riceve 409', async () => {
    // Senza il lock entrambe troverebbero la cache vuota ed
    // eseguirebbero l'addebito
    const [a, b] = await Promise.all([invia(corpo), invia(corpo)])
    expect([a.status, b.status].sort()).toEqual([201, 409])
  })
})
```

---
## C2. Mini-progetto: API di gestione progetti con OpenAPI

L'esercizio chiave del modulo: progettare e implementare un'API RESTful per un sistema di gestione progetti, con documentazione OpenAPI.

```
api-progetti/
├── openapi.yaml            il contratto — si scrive PRIMA
├── src/
│   ├── app.ts              composizione dei middleware
│   ├── errori/problema.ts  la gerarchia RFC 9457
│   ├── paginazione.ts      cursore opaco
│   ├── middleware/         gestore-problemi · idempotenza ·
│   │                       limite-frequenza
│   ├── rotte/              progetti (CRUD + ETag) · attivita
│   └── repository/
└── test/
    ├── contratto.test.ts   conformità a openapi.yaml (jest-openapi:
    │                       `expect(risposta).toSatisfyApiSpec()`)
    └── rotte.test.ts       Supertest

L'ORDINE DEI MIDDLEWARE IN app.ts È TUTTO
  1. id della richiesta   PRIMA di tutto: serve anche ai log degli
                          errori generati dai middleware successivi
  2. limite di frequenza  prima di qualunque lavoro costoso
  3. express.json         CON limite: senza, una richiesta enorme
                          esaurisce la memoria del processo
  4. idempotenza          dopo il parsing: serve l'impronta del corpo
  5. le rotte, 6. il 404, e per ULTIMO il gestore degli errori, con
     QUATTRO parametri: con tre Express lo tratta come middleware
     normale e non lo chiama mai

LA VERIFICA, IN ORDINE
 1. IL CONTRATTO È VALIDO
    pnpm dlx @redocly/cli lint openapi.yaml → nessun $ref rotto
 2. IL CODICE RISPETTA IL CONTRATTO
    il test di conformità fallisce se una risposta ha un campo in
    più, uno in meno, un tipo diverso o un formato non conforme.
    Senza, lo schema-first diventa uno schema-e-poi-si-vede.
 3. LA PAGINAZIONE NON DUPLICA
    inserisci elementi fra due pagine → nessun id ripetuto
 4. L'IDEMPOTENZA REGGE  stessa chiave + stesso corpo → una sola
    esecuzione; stessa chiave + corpo diverso → 409
 5. LA CONCORRENZA È PROTETTA
    due PATCH con lo stesso If-Match → uno 200, uno 412
 6. GLI ERRORI NON PERDONO INFORMAZIONI INTERNE
    forza un 500 → nessun nome di host, query SQL né stack trace nel
    corpo; l'idRichiesta c'è
 7. I LIMITI SONO IMPOSTI DAL SERVER
    ?limite=5000 → 422    corpo da 2 MB → 413
 8. GLI HEADER DEL CONTRATTO CI SONO
    RateLimit su ogni risposta, ETag sulle risorse singole, Location
    sui 201, Retry-After sui 429
```

---
# Parte D — Approfondimento per Esperti

---

## D1. HATEOAS che serve davvero

L'hypermedia completo raramente ripaga. Ma c'è un caso in cui i link risolvono un problema reale: le risorse con una macchina a stati, dove il client altrimenti duplica le regole delle transizioni.

```json
{
  "id": "ord_01HQ8X2K",
  "stato": "in_attesa_pagamento",
  "azioni": {
    "paga": { "href": "/api/v1/ordini/ord_01HQ8X2K/pagamenti", "metodo": "POST" },
    "annulla": { "href": "/api/v1/ordini/ord_01HQ8X2K", "metodo": "DELETE" }
  }
}
```

Senza, il client contiene `if (stato === 'in_attesa_pagamento' && utente.puoPagare && !ordine.scaduto)`. Quella regola esiste già sul server: ora esiste due volte, e prima o poi divergono — tipicamente quando si aggiunge uno stato. Con, il server include `paga` solo se l'azione È possibile, per quell'utente, adesso: il client mostra i pulsanti che ci sono, e aggiungere uno stato non lo tocca. Il costo è un oggetto in più nella risposta; il guadagno è che permessi e transizioni restano in un posto solo. Qui, non ovunque.

---
## D2. Contract testing e il deploy indipendente

Il problema che risolve: due servizi rilasciati da team diversi, in momenti diversi, senza un ambiente in cui girino insieme prima della produzione. Il consumer scrive i test con un mock e registra il *pact* su un broker; il provider lo verifica, e in CI un `can-i-deploy?` BLOCCA il deploy se il provider non soddisfa più il contratto che un consumer in produzione si aspetta.

```
✅ verifica che il provider restituisca i campi e i tipi che il
   consumer usa; un campo rimosso blocca il deploy PRIMA della
   produzione
❌ NON verifica che i valori siano corretti: quello è compito dei
   test del provider; non sostituisce i test di integrazione

Quando vale la pena: più di due o tre servizi con team e cadenze di
rilascio diversi. Sotto quella soglia, un test di conformità a
OpenAPI in CI (vedi C2) copre l'80% del valore a un decimo del costo.
```

---
## D3. Operazioni lunghe: 202 e la risorsa di stato

Un'esportazione da due milioni di righe non può stare in una richiesta HTTP: il timeout del proxy è tipicamente 30-60 secondi.

```http
### Il client chiede, il server accetta senza eseguire
POST /api/v1/esportazioni    { "formato": "csv" }

HTTP/1.1 202 Accepted
Location: /api/v1/esportazioni/exp_01HQ8X2K
Retry-After: 5
{ "id": "exp_01HQ8X2K", "stato": "in_coda" }

### Il client segue lo stato, e quando è pronto
GET /api/v1/esportazioni/exp_01HQ8X2K
→ { "stato": "in_corso", "avanzamento": 0.42 }
→ { "stato": "completato",
    "risultato": { "href": "…/file", "scadeIl": "2026-08-19T14:30:00Z" } }
```

```
LE DECISIONI CHE RENDONO IL PATTERN USABILE
 · L'OPERAZIONE È UNA RISORSA: ha un id, uno stato, si elenca e si
   annulla (DELETE = richiesta di annullamento).
 · Retry-After sulla 202 dice OGNI QUANTO chiedere: senza, il client
   fa polling ogni cento millisecondi.
 · Gli stati sono un enum chiuso e documentato.
 · Il fallimento porta un Problem Details DENTRO la risorsa, non un
   codice HTTP di errore: la RICHIESTA di stato è riuscita, è
   l'OPERAZIONE che è fallita.
 · Il risultato SCADE: senza, l'archivio cresce per sempre.
 · Un webhook alla fine risparmia il polling a chi può riceverlo.
```

---
## D4. Deprecare senza rompere

```http
HTTP/1.1 200 OK
Deprecation: @1780272000
Sunset: Sat, 01 Jun 2027 00:00:00 GMT
Link: <https://api.esempio.it/docs/migrazione-v2>; rel="deprecation"
```

```
  Deprecation (RFC 9745)  quando è stato deprecato, in secondi epoch
  Sunset (RFC 8594)       quando SPARIRÀ, come data HTTP
  Link rel="deprecation"  dove si legge come migrare

IL CALENDARIO CHE FUNZIONA
  T+0    l'header compare; documentazione e note di rilascio lo dicono
  T+1m   email ai proprietari delle chiavi che lo usano — si sa CHI
         sono perché lo si misura (D5)
  T+6m   "brownout": l'endpoint restituisce 410 per un'ora al giorno,
         in orario lavorativo. È l'unico strumento che fa reagire chi
         ignora le email.
  T+12m  rimozione: 410 Gone, con un Problem Details che dice dove
         andare
  ⚠ 410 Gone, non 404: significa "esisteva ed è stato rimosso di
    proposito", e distingue una migrazione mancata da un errore di
    percorso.
```

---
## D5. Osservabilità di un'API

```
LE QUATTRO METRICHE, PER ENDPOINT E PER VERSIONE
  1. tasso di richieste al secondo
  2. tasso di errori, con 4xx e 5xx SEPARATI: i 4xx dicono che i
     client sbagliano (o che la documentazione è poco chiara), i 5xx
     che sbagli tu
  3. latenza in PERCENTILI — p50, p95, p99, mai la media: una media
     di 100 ms può nascondere che l'1% degli utenti aspetta otto
     secondi
  4. saturazione: connessioni al database, coda dell'event loop,
     memoria

LE METRICHE SPECIFICHE DI UN'API, CHE QUASI NESSUNO RACCOGLIE
 · uso per CAMPO deprecato: senza, la deprecazione è a occhio
 · uso per VERSIONE e per chiave API: dice chi contattare
 · profondità di paginazione: un client che arriva a pagina 500 con
   l'offset sta per far cadere il database
 · tasso di 409 sull'idempotenza: se cresce, un client sta riusando
   male le chiavi
 · tasso di 412: se cresce, ci sono troppe modifiche concorrenti e
   forse serve un blocco più fine
```

```typescript
// Misurare l'uso di un campo deprecato: tre righe che rendono la
// deprecazione una decisione basata su dati invece che una scommessa
export function registraUsoDeprecato(campo: string, richiesta: Request): void {
  metriche.contatore('api_campo_deprecato', {
    campo,
    chiaveApi: richiesta.utente?.chiaveApi ?? 'anonimo',
    versione: richiesta.get('API-Version') ?? 'v1',
  })
}
```

---
# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
API DESIGN — Mappa dei concetti

IL CONTRATTO sopravvive al codice: cambiarlo costa il tempo di TUTTI.
  OpenAPI 3.1 = JSON Schema 2020-12 completo. Quattro decisioni
  irreversibili: id, paginazione, errori, versione.

RISORSE, METODI, STATI
├── sostantivi PLURALI · kebab-case negli URI, camelCase nel JSON
├── massimo due livelli · i filtri sono query parameter
├── safe = non modifica  ·  idempotente = stesso STATO finale
├── PUT sostituisce (un campo omesso viene AZZERATO); con
│     merge-patch, null = rimuovi
├── 400 = non leggibile     422 = leggibile ma viola il dominio
├── 401 = non so chi sei    403 = so chi sei e non puoi
└── 201 con Location · 204 senza corpo · 412 su If-Match

ERRORI — RFC 9457: application/problem+json con type, title, status,
  detail, instance; mai dettagli interni in `detail`; idRichiesta è
  il campo più utile dell'intera risposta.

PAGINAZIONE E FILTRI
├── offset: risultati che scivolano + degradazione profonda
├── cursore = il contratto pubblico, opaco per il client
├── keyset = l'implementazione: (creato_il, id) < (X, Y), a TUPLA,
│     su indice composto, con seconda colonna unica
├── limite+1 invece di COUNT(*); il limite lo IMPONE il server
└── lista chiusa per ordinamento e colonne: i parametri proteggono
      i VALORI, non la STRUTTURA

IDEMPOTENZA, CONCORRENZA, CACHING
├── GET, PUT, DELETE la hanno per natura; POST no
├── Idempotency-Key + IMPRONTA DEL CORPO, lock, solo i successi
├── ETag + If-Match: il controllo DENTRO l'UPDATE, non prima
├── 412 se non combacia · 428 se manca
├── private + Vary: Authorization sui dati personali
└── no-cache ≠ no-store · max-age=0 + ETag = verifica e risparmia

VERSIONAMENTO E CONTRATTO OPERATIVO
├── breaking = un client conforme si rompe; il più pericoloso è
│     cambiare il SIGNIFICATO a parità di tipo
├── espandi-e-contrai evita una versione nuova nel 90% dei casi
├── RateLimit su OGNI risposta, non solo sui 429
├── webhook: firma sul corpo GREZZO, 202 subito, idempotenza nella
│     stessa transazione, jitter, DLQ monitorata
├── bulk: 200 con esiti individuali, limite massimo, sequenziale
└── operazioni lunghe: 202 + risorsa di stato + Retry-After
```

---
## Checklist di competenze

**Parte A — Basi**

- [ ] Sai dire quali decisioni di un endpoint sono irreversibili
- [ ] Progetti URI con sostantivi plurali, sai dove finisce l'annidamento e come modellare un'azione non-CRUD senza inventare un verbo
- [ ] Distingui safe da idempotente e sai perché i proxy ci contano
- [ ] Sai cosa succede a un campo omesso in un PUT, e le tre regole di JSON Merge Patch
- [ ] Scegli fra 400 e 422, e fra 401 e 403, senza esitare
- [ ] Sai perché il denaro va in interi e le date in ISO 8601 con la Z
- [ ] Costruisci un errore RFC 9457 completo, senza dettagli interni
- [ ] Validi corpo, query e parametri di percorso con Zod

**Parte B — Comprensione**

- [ ] Sai spiegare i due modi in cui la paginazione offset si rompe
- [ ] Sai perché il confronto deve essere a tupla e non a colonna singola
- [ ] Sai perché il cursore deve restare opaco, e usi limite+1 invece di COUNT(*)
- [ ] Sai perché i nomi di colonna non possono essere parametri
- [ ] Implementi Idempotency-Key con l'impronta del corpo e il lock, e sai perché memorizzare un 500 è un errore
- [ ] Sai perché il controllo di versione va dentro l'UPDATE, e distingui 412 da 428
- [ ] Sai la differenza fra `no-cache` e `no-store`, e perché `Vary` non è facoltativo
- [ ] Sai classificare un cambiamento come breaking o no, e conosci le tre strategie di versionamento
- [ ] Sai cosa cambia in OpenAPI 3.1 rispetto alla 3.0
- [ ] Sai perché gli header RateLimit vanno su ogni risposta e perché la firma di un webhook va sul corpo grezzo
- [ ] Sai perché una risposta bulk è 200 anche con fallimenti

**Parte C — Pratica**

- [ ] Hai trovato tutte e otto le violazioni dell'esercizio 1
- [ ] Hai implementato la paginazione keyset e verificato con EXPLAIN che il piano usi l'indice
- [ ] Hai dimostrato con un test i quattro casi dell'idempotenza
- [ ] Hai un test di conformità che confronta il codice con OpenAPI

**Parte D — Esperto**

- [ ] Sai in quale caso HATEOAS ripaga davvero, e cosa il contract testing verifica e cosa no
- [ ] Sai progettare un'operazione lunga con 202 e risorsa di stato
- [ ] Conosci Deprecation e Sunset, e la differenza fra 410 e 404
- [ ] Sai perché la latenza si misura in percentili e non in media
- [ ] Misuri l'uso dei campi deprecati prima di rimuoverli

---
## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Verbi nell'URI | Un endpoint nuovo per ogni azione; nessuna struttura | Sostantivi plurali, l'azione la dice il metodo |
| `200 OK` con `{ "ok": false }` | Il client che guarda solo lo stato crede sia riuscito | L'errore sta nel codice di stato |
| `POST` per eliminare | L'operazione non è più idempotente né ripetibile | `DELETE` |
| Nessuna paginazione, o offset su un feed | Cade in produzione; elementi duplicati e persi | Limite imposto dal server; cursore opaco + keyset |
| `SELECT COUNT(*)` per `haAltri` | Un secondo scan completo a ogni pagina | Chiedere limite+1 |
| Ordinamento del client in `ORDER BY` | Iniezione: i parametri non proteggono i nomi di colonna | Mappa a chiavi note |
| Formato di errore diverso per endpoint | Il client scrive un ramo per ogni forma | RFC 9457 ovunque |
| Stack trace in una risposta 500 | Espone host, query, struttura interna | Messaggio generico + `idRichiesta` |
| `POST` senza `Idempotency-Key` sui pagamenti | Doppio addebito al primo timeout di rete | Chiave + impronta del corpo |
| Idempotenza senza impronta del corpo | Un riuso errato della chiave salta un'operazione | Confrontare l'hash del corpo |
| Memorizzare i 500 nell'idempotenza | Il client non può riprovare per 24 ore | Solo i successi |
| Controllo ETag prima dell'UPDATE | Finestra di sovrascrittura fra lettura e scrittura | `WHERE id = … AND versione = …` |
| `public` su dati personali | La CDN serve i dati di Anna a Bruno | `private` + `Vary: Authorization` |
| `no-cache` per dire "non salvare" | Significa l'opposto: salva e rivalida | `no-store` |
| Nessun header `RateLimit` | Il client che prende 429 riprova in ciclo | `RateLimit` su ogni risposta |
| Firma del webhook sul JSON analizzato | La riserializzazione cambia i byte: la firma salta | `express.raw`, firma sui byte |
| Consumatore di webhook non idempotente | La consegna è at-least-once: effetti applicati due volte | Registrazione nella stessa transazione |
| Bulk con `Promise.all` | Cento scritture in parallelo saturano il pool | Sequenziale, o parallelismo limitato |
| Nessuna versione dal primo giorno | `/api/progetti` resta in vita per sempre come "v0" | `/v1` subito |
| Rimuovere un campo senza misurare | Si scopre chi lo usava dalle segnalazioni | Metrica per campo deprecato, poi brownout |

---
## Troubleshooting rapido

**Il client riceve elementi duplicati scorrendo l'elenco**
- Causa: paginazione offset con dati che cambiano sotto
- Fix: cursore + keyset; l'ordinamento deve includere una colonna unica

**Alcuni elementi vengono saltati fra una pagina e l'altra**
- Causa: confronto sulla sola colonna di ordinamento, con valori duplicati
- Fix: confronto a tupla `(creato_il, id) < (X, Y)`

**La paginazione rallenta man mano che si va avanti**
- Causa: `OFFSET` profondo, oppure indice assente
- Fix: keyset; `EXPLAIN ANALYZE` deve dire "Index Scan", non "Seq Scan"

**La firma del webhook non combacia mai**
- Causa: si sta firmando il JSON analizzato invece del corpo grezzo
- Fix: `express.raw` prima di `express.json` su quella rotta

**Doppi addebiti quando la rete è instabile, o 409 inattesi**
- Causa: `POST` non idempotente; oppure la stessa chiave riusata per
  operazioni diverse, o un lock non rilasciato dopo un errore
- Fix: `Idempotency-Key` con impronta del corpo; una chiave per
  operazione logica; rilascio del lock anche su `close`

**Le modifiche di un utente spariscono senza errori**
- Causa: aggiornamento perduto — nessun controllo di concorrenza
- Fix: ETag + `If-Match`, con il controllo dentro l'`UPDATE`

**Un utente vede i dati di un altro**
- Causa: risposta personale marcata `public`, servita da una CDN
- Fix: `private` + `Vary: Authorization`; verificare la CDN

**Il rate limiting non funziona dietro un proxy**
- Causa: `req.ip` è l'indirizzo del proxy, uguale per tutti
- Fix: `app.set('trust proxy', 1)` e verificare `X-Forwarded-For`

**Il gestore degli errori non cattura nulla, o `ZodError` esce come 500**
- Causa: registrato prima delle rotte, con tre parametri invece di
  quattro, oppure non riconosce `ZodError`
- Fix: per ultimo, con la firma `(errore, richiesta, risposta, prossimo)`;
  normalizzare `ZodError` in `ErroreValidazione`

**La risposta non corrisponde a `openapi.yaml`**
- Causa: nessun test di conformità: schema e codice sono divergiti
- Fix: `toSatisfyApiSpec` in CI su ogni endpoint

---
## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_12_database_web.md` | Gli indici che la paginazione keyset richiede, il problema N+1, il pool |
| `tutorial_13_autenticazione_autorizzazione.md` | Cosa c'è dietro il 401 e il 403: token, sessioni, scope |
| `tutorial_14_sicurezza_web.md` | OWASP API Security, iniezione, CORS, esposizione eccessiva di dati |
| `tutorial_15_testing_web.md` | Test di integrazione e contract testing in profondità |
| `tutorial_22_rate_limiting_edge.md` | Gli algoritmi dietro gli header RateLimit |
| `tutorial_24_graphql.md` | Schema, resolver, DataLoader, persisted query |

---

## Risorse di riferimento

**Specifiche:** [RFC 9457 — Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) (sostituisce la 7807) · [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html), la fonte primaria su metodi, stati e header · [RFC 7396 — JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396.html) e [RFC 6902 — JSON Patch](https://www.rfc-editor.org/rfc/rfc6902.html) · [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0.html)

**Guide di stile:** [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/), la più completa e motivata · [Google API Improvement Proposals](https://google.aip.dev/), le decisioni di progetto con il perché · [Stripe API Reference](https://docs.stripe.com/api), il riferimento pratico per idempotenza e versionamento a data

**Strumenti:** [Redocly CLI](https://redocly.com/docs/cli/) per lint e bundle · [openapi-typescript](https://openapi-ts.dev/) per i tipi dal contratto · [Prism](https://stoplight.io/open-source/prism) per il server mock · [Pact](https://docs.pact.io/) per il contract testing

---