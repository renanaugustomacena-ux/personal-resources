# Tutorial 12 — Database per il Web: Dal Principiante all'Esperto

> **Companion a:** `12-database-web.md`
> **Scope:** SQL e PostgreSQL, vincoli, relazioni, transazioni e ACID, Prisma, migrazioni, indici e piani di esecuzione, problema N+1, livelli di isolamento, connection pooling, normalizzazione, JSONB, migrazioni senza downtime, Redis come cache, Row-Level Security, testing con database reale
> **Prerequisiti:** `tutorial_10_nodejs.md` — server e configurazione; `tutorial_11_api_design.md` — paginazione keyset, che qui trova gli indici che le servono
> **Durata stimata:** 8-10 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** PostgreSQL 17 · Prisma 6 · Redis 7 · Node.js LTS

---

## Indice Generale

- [Mappa concettuale](#mappa-concettuale)
- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Lo schema sopravvive all'applicazione](#a1-lo-schema-sopravvive-allapplicazione)
  - [A2. Modellare: chiavi, relazioni, tabelle ponte](#a2-modellare-chiavi-relazioni-tabelle-ponte)
  - [A3. Interrogare: SELECT, JOIN, aggregazioni](#a3-interrogare-select-join-aggregazioni)
  - [A4. Transazioni e ACID](#a4-transazioni-e-acid)
  - [A5. Prisma: lo schema come sorgente di verità](#a5-prisma-lo-schema-come-sorgente-di-verità)
  - [A6. Migrazioni: file immutabili, mai modificati a mano](#a6-migrazioni-file-immutabili-mai-modificati-a-mano)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. Indici: come funzionano e quando non vengono usati](#b1-indici-come-funzionano-e-quando-non-vengono-usati)
  - [B2. EXPLAIN ANALYZE: leggere un piano](#b2-explain-analyze-leggere-un-piano)
  - [B3. Il problema N+1](#b3-il-problema-n1)
  - [B4. Isolamento e anomalie](#b4-isolamento-e-anomalie)
  - [B5. Connection pooling](#b5-connection-pooling)
  - [B6. Normalizzazione, e quando denormalizzare](#b6-normalizzazione-e-quando-denormalizzare)
  - [B7. JSONB: quando il relazionale non basta](#b7-jsonb-quando-il-relazionale-non-basta)
  - [B8. Migrazioni senza downtime](#b8-migrazioni-senza-downtime)
  - [B9. Redis come cache: le tre trappole](#b9-redis-come-cache-le-tre-trappole)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: schema e-commerce con Prisma](#c2-mini-progetto-schema-e-commerce-con-prisma)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Row-Level Security e multi-tenancy](#d1-row-level-security-e-multi-tenancy)
  - [D2. Testare con un database vero](#d2-testare-con-un-database-vero)
  - [D3. pg_stat_statements: trovare le query che costano](#d3-pg_stat_statements-trovare-le-query-che-costano)
  - [D4. Il denaro nel database](#d4-il-denaro-nel-database)
  - [D5. Un backup non esiste finché non è stato ripristinato](#d5-un-backup-non-esiste-finché-non-è-stato-ripristinato)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   APPLICAZIONE
        │  Prisma Client (tipi generati dallo schema)
        ▼
   ┌────────────────────┐
   │ POOL DI CONNESSIONI│  dimensionato sui core del DB, non
   └─────────┬──────────┘  sui processi dell'app
             ▼
   ┌──────────────────────────────────────────────────────┐
   │  PostgreSQL                                          │
   │   query planner → piano di accesso → esecuzione      │
   │        ▲ statistiche (ANALYZE)      ▲ indici         │
   │  ┌─────┴──────────────────────────────────────────┐  │
   │  │ VINCOLI: NOT NULL · CHECK · UNIQUE · FOREIGN KEY│ │
   │  │ l'ultima linea di difesa: valgono anche per chi │ │
   │  │ scrive fuori dall'applicazione                  │ │
   │  └────────────────────────────────────────────────┘  │
   └──────────────────────────────────────────────────────┘

   LE TRE DOMANDE DA FARE A OGNI QUERY LENTA
     1. il piano dice "Seq Scan" dove ti aspetti "Index Scan"?
     2. le righe STIMATE e quelle REALI differiscono di ordini
        di grandezza?  → le statistiche sono vecchie
     3. la query viene eseguita una volta, o una per riga?  → N+1
```

---

# Parte A — Basi Assolute

---

## A1. Lo schema sopravvive all'applicazione

> **Analogia:** le fondamenta di una casa. Le pareti si spostano, gli impianti si rifanno, il tetto si cambia. Le fondamenta no: quando servono più profonde, si abbatte tutto. E come le fondamenta, uno schema sbagliato non si vede finché non arriva il carico.

Il codice che oggi scrive nel database verrà riscritto. I dati restano, e con essi ogni decisione presa quando la tabella è stata creata. Da qui la regola che vale per tutto il resto del tutorial: **i vincoli stanno nel database, non solo nel codice.**

```sql
-- ❌ Nessun vincolo: lo schema accetta qualunque cosa
CREATE TABLE ordini (
  id serial, utente_id integer, totale real,
  stato text, creato_il timestamp
);
```

```
COSA PUÒ FINIRCI DENTRO
  · un ordine senza utente, o di un utente cancellato (nessuna
    foreign key)          · un totale negativo
  · stato = 'Spedito', 'spedito', 'SPEDITO', 'spdito'
  · 19.99 memorizzato come 19.989999771118164 (real = float)
  · due righe con lo stesso id (serial non è una chiave primaria)

Il codice applicativo "controlla tutto"? Non controllano nulla: lo
script di importazione scritto in fretta, la correzione manuale
fatta in psql alle due di notte, il secondo servizio che qualcuno
collegherà fra un anno, e il bug che passerà la validazione.
```

```sql
-- ✅ Lo schema come contratto
CREATE TABLE ordini (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  utente_id     bigint NOT NULL REFERENCES utenti(id) ON DELETE RESTRICT,
  totale_centesimi integer NOT NULL CHECK (totale_centesimi >= 0),
  valuta        char(3) NOT NULL DEFAULT 'EUR',
  stato         text NOT NULL DEFAULT 'in_attesa'
                CHECK (stato IN ('in_attesa','pagato','spedito','annullato')),
  creato_il     timestamptz NOT NULL DEFAULT now(),
  aggiornato_il timestamptz NOT NULL DEFAULT now()
);
```

```
LE SCELTE, UNA PER UNA
  bigint invece di integer   integer arriva a 2,1 miliardi. Sembra
    tanto finché non è una tabella di eventi, e cambiare il tipo di
    una chiave primaria dopo è una migrazione dolorosa.
  GENERATED ALWAYS AS IDENTITY  lo standard SQL; `serial` è
    l'eredità di PostgreSQL e lascia una sequenza scollegata.
  ON DELETE RESTRICT  cancellare un utente con ordini FALLISCE.
    CASCADE cancellerebbe silenziosamente i documenti contabili.
  CHECK sullo stato  un enum a lista chiusa. Aggiungerne uno è una
    migrazione, ed è giusto che lo sia.
  timestamptz, MAI timestamp  `timestamp` non porta il fuso: la
    stessa riga letta da un server a Roma e uno a Londra dà due
    istanti diversi.
  numeric o interi, MAI real  vedi D4.
```

---
## A2. Modellare: chiavi, relazioni, tabelle ponte

Ci sono tre forme di relazione, e una sola si sbaglia spesso.

```
UNO A MOLTI   un utente ha molti ordini. La chiave esterna sta dalla
  parte del MOLTI: ordini.utente_id → utenti.id
UNO A UNO     un utente ha un profilo. Chiave esterna + UNIQUE dalla
  parte che può mancare. ⚠ Se i due sono sempre presenti insieme, è
  una tabella sola: una "profili" che esiste per ogni utente è una
  divisione senza motivo.
MOLTI A MOLTI un ordine contiene molti prodotti, un prodotto sta in
  molti ordini. NON si esprime con una chiave esterna: serve una
  TABELLA PONTE.
```

```sql
CREATE TABLE ordini_articoli (
  ordine_id    bigint NOT NULL REFERENCES ordini(id) ON DELETE CASCADE,
  prodotto_id  bigint NOT NULL REFERENCES prodotti(id) ON DELETE RESTRICT,
  quantita     integer NOT NULL CHECK (quantita > 0),
  -- Il prezzo si COPIA al momento dell'ordine: se domani il
  -- prodotto rincara, la fattura di ieri non deve cambiare
  prezzo_unitario_centesimi integer NOT NULL CHECK (prezzo_unitario_centesimi >= 0),
  PRIMARY KEY (ordine_id, prodotto_id)
);
```

```
DUE DECISIONI CHE SEMBRANO DETTAGLI E NON LO SONO
1. LA CHIAVE PRIMARIA COMPOSTA (ordine_id, prodotto_id) impedisce
   che lo stesso prodotto compaia due volte nello stesso ordine.
   Senza, ci si accorge del duplicato dal totale sbagliato.
2. IL PREZZO COPIATO. Un'entità che descrive un FATTO AVVENUTO — una
   riga d'ordine, un movimento contabile, una fattura — copia i
   valori che aveva al momento del fatto. Riferirsi al prodotto per
   il prezzo significa che il passato cambia quando cambia il
   listino: è il bug che si scopre da una contestazione.

⚠ ON DELETE CASCADE sulle righe d'ordine è corretto (non esistono
  senza l'ordine), RESTRICT sul prodotto è corretto (cancellare un
  prodotto venduto distruggerebbe lo storico). La stessa parola in
  due posti, due significati opposti: la scelta va fatta relazione
  per relazione, non per abitudine.
```

---
## A3. Interrogare: SELECT, JOIN, aggregazioni

```sql
-- Le colonne SEMPRE esplicite: SELECT * si rompe quando qualcuno
-- aggiunge una colonna, e trasferisce dati che non servono
SELECT o.id, o.creato_il, u.email, o.totale_centesimi
FROM ordini o
JOIN utenti u ON u.id = o.utente_id
WHERE o.stato = 'pagato'
  AND o.creato_il >= now() - interval '30 days'
ORDER BY o.creato_il DESC
LIMIT 20;
```

```
INNER JOIN CONTRO LEFT JOIN — la differenza che cambia i risultati
  JOIN (inner) tiene solo le righe con corrispondenza in ENTRAMBE le
    tabelle: un ordine il cui utente è stato cancellato sparisce dal
    risultato, senza avvisi.
  LEFT JOIN tiene tutte le righe di sinistra; le colonne di destra
    sono NULL dove non c'è corrispondenza.

⚠ LA TRAPPOLA: una condizione sulla tabella di destra messa in WHERE
  invece che in ON trasforma un LEFT JOIN in un INNER JOIN, perché
  `destra.colonna = 'x'` è falsa quando la colonna è NULL.
    WHERE r.voto >= 4                     ← i prodotti senza
                                            recensioni spariscono
    ON r.prodotto_id = p.id AND r.voto >= 4  ← restano, con NULL
```

```sql
-- Aggregazioni: ogni colonna del SELECT o è in GROUP BY o è dentro
-- una funzione di aggregazione
SELECT p.categoria, count(*) AS ordini, sum(oa.quantita) AS pezzi
FROM prodotti p
JOIN ordini_articoli oa ON oa.prodotto_id = p.id
GROUP BY p.categoria
-- HAVING filtra DOPO il raggruppamento, WHERE PRIMA: mettere qui
-- una condizione che potrebbe stare in WHERE significa aggregare
-- righe che poi si buttano
HAVING count(*) >= 10
ORDER BY pezzi DESC;
```

```
⚠ count(*) CONTRO count(colonna): il primo conta le righe, il secondo
  i valori NON NULL. Su un LEFT JOIN sono numeri diversi, e count(*)
  è quasi sempre quello sbagliato: conta 1 anche quando la riga di
  destra non esiste.
```

---
## A4. Transazioni e ACID

> **Analogia:** un bonifico. Togliere cento euro da un conto e aggiungerli a un altro sono due operazioni, ma devono valere come una: non esiste uno stato del mondo in cui i cento euro non sono da nessuna parte. La transazione è la promessa che quello stato non si vedrà mai.

```sql
BEGIN;
  UPDATE conti SET saldo_centesimi = saldo_centesimi - 10000 WHERE id = 1;
  UPDATE conti SET saldo_centesimi = saldo_centesimi + 10000 WHERE id = 2;
COMMIT;   -- oppure ROLLBACK: o entrambe, o nessuna
```

```
ACID, E COSA SIGNIFICA DAVVERO
  ATOMICITÀ    o tutte le operazioni, o nessuna. Un crash a metà
    lascia il database come prima.
  COERENZA     i vincoli valgono anche a fine transazione: una
    CHECK violata fa fallire il COMMIT.
  ISOLAMENTO   le transazioni concorrenti non si vedono a metà.
    ⚠ Quanto isolamento dipende dal LIVELLO: è la parte che quasi
      tutti danno per scontata, e vale la Parte B4.
  DURABILITÀ   dopo il COMMIT il dato sopravvive a un crash — se il
    disco lo ha davvero scritto (`fsync`).
```

```typescript
// In Prisma: tutto ciò che sta dentro la callback è una transazione.
// Se il codice solleva, la transazione viene annullata.
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export async function trasferisci(daId: bigint, aId: bigint, centesimi: number) {
  return prisma.$transaction(async (tx) => {
    const origine = await tx.conto.update({
      where: { id: daId },
      data: { saldoCentesimi: { decrement: centesimi } },
    })

    // Il controllo va DENTRO la transazione: farlo prima lascia una
    // finestra in cui un'altra operazione svuota il conto
    if (origine.saldoCentesimi < 0) {
      throw new Error('Saldo insufficiente')
    }

    await tx.conto.update({
      where: { id: aId },
      data: { saldoCentesimi: { increment: centesimi } },
    })
  })
}
```

```
⚠ TRE ERRORI RICORRENTI
  1. Chiamare un servizio esterno DENTRO la transazione. La
     transazione tiene i lock per tutta la durata della chiamata
     HTTP; se il servizio è lento, il database si blocca. E se la
     transazione viene annullata, la chiamata è già partita.
  2. Transazioni lunghe. Ogni riga toccata resta bloccata fino al
     COMMIT. Una transazione di trenta secondi su una tabella calda
     mette in coda tutti gli altri.
  3. Leggere fuori e scrivere dentro. `if (await esiste(x))` prima
     del BEGIN è un controllo su uno stato che può essere già
     cambiato quando la scrittura avviene.
```

---

## A5. Prisma: lo schema come sorgente di verità

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Utente {
  id        BigInt   @id @default(autoincrement())
  email     String   @unique
  nome      String?
  creatoIl  DateTime @default(now()) @map("creato_il")

  ordini    Ordine[]

  @@map("utenti")
}

model Ordine {
  id               BigInt      @id @default(autoincrement())
  utenteId         BigInt      @map("utente_id")
  totaleCentesimi  Int         @map("totale_centesimi")
  stato            StatoOrdine @default(in_attesa)
  creatoIl         DateTime    @default(now()) @map("creato_il")

  utente           Utente           @relation(fields: [utenteId], references: [id])
  articoli         OrdineArticolo[]

  // L'indice che serve alla paginazione keyset del tutorial 11
  @@index([utenteId, creatoIl(sort: Desc)])
  @@map("ordini")
}

enum StatoOrdine {
  in_attesa
  pagato
  spedito
  annullato
}
```

```
`@map` E `@@map` SERVONO DAVVERO  tengono i nomi TypeScript in
  camelCase e quelli SQL in snake_case, che è la convenzione di
  PostgreSQL. Senza, ogni query scritta a mano in psql deve usare
  virgolette doppie ("creatoIl") perché PostgreSQL abbassa i nomi
  non quotati. È un fastidio che dura per sempre.
```

```typescript
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

// `select` restituisce SOLO i campi elencati: il tipo di ritorno lo
// riflette, e il database trasferisce meno dati
const ordini = await prisma.ordine.findMany({
  where: { stato: 'pagato', creatoIl: { gte: new Date('2026-01-01') } },
  select: {
    id: true,
    totaleCentesimi: true,
    utente: { select: { email: true } },
  },
  orderBy: { creatoIl: 'desc' },
  take: 20,
})

// ordini[0].utente.email  ✅ tipizzato
// ordini[0].stato         ❌ errore di compilazione: non selezionato
```

```
DOVE FINISCE LA TYPE SAFETY DI PRISMA
  ✅ nomi di modelli, campi, relazioni, operatori e valori di enum
  ✅ la forma del risultato riflette select/include
  ❌ `$queryRaw` senza generico: il risultato è `unknown`
  ❌ i vincoli CHECK, i trigger e le regole scritte in SQL: Prisma
     non li conosce e li scopre come errori a runtime
  ❌ la coerenza fra schema Prisma e database REALE, se qualcuno ha
     modificato il database a mano
```

---

## A6. Migrazioni: file immutabili, mai modificati a mano

```powershell
# Sviluppo: genera il file di migrazione e lo applica
pnpm prisma migrate dev --name aggiunge_stato_ordine

# Produzione: applica solo ciò che manca, senza generare nulla
pnpm prisma migrate deploy

# Verifica che database e schema coincidano — da usare in CI
pnpm prisma migrate diff --from-schema-datasource prisma/schema.prisma `
  --to-schema-datamodel prisma/schema.prisma --exit-code
```

```
LE TRE REGOLE NON NEGOZIABILI

1. UN FILE DI MIGRAZIONE APPLICATO NON SI TOCCA PIÙ. Il suo hash è
   registrato nella tabella `_prisma_migrations`: modificarlo fa
   fallire ogni ambiente che l'aveva già applicato. Serve una
   correzione? Una migrazione NUOVA.

2. `prisma db push` NON VA IN PRODUZIONE. Sincronizza lo schema
   senza generare un file: nessuna storia, nessun rollback, e ciò
   che ha fatto in staging non è riproducibile altrove. Va bene solo
   per un prototipo usa e getta.

3. LE MIGRAZIONI DISTRUTTIVE SI LEGGONO PRIMA DI APPLICARLE. Prisma
   avvisa quando una modifica perde dati, ma l'avviso passa
   inosservato nella foga. Un `DROP COLUMN` su una tabella di
   produzione non ha un annullamento.
```

```sql
-- Il file generato è SQL leggibile, e va letto:
-- prisma/migrations/20260819_aggiunge_stato_ordine/migration.sql
ALTER TABLE "ordini" ADD COLUMN "stato" TEXT NOT NULL DEFAULT 'in_attesa';
```

```
⚠ QUELL'`ALTER TABLE` NON È INNOCUO SU UNA TABELLA GRANDE. Da
  PostgreSQL 11 aggiungere una colonna con DEFAULT non riscrive la
  tabella, ma prende comunque un lock ACCESS EXCLUSIVE per il tempo
  della modifica del catalogo: se una transazione lunga tiene la
  tabella, l'ALTER si mette in coda — e tutte le query che arrivano
  dopo si accodano dietro di lui. Il trattamento è in B8.
```

---

# Parte B — Comprensione Profonda

---

## B1. Indici: come funzionano e quando non vengono usati

> **Analogia:** l'indice analitico di un libro. Cercare "transazioni" fra le pagine significa sfogliarle tutte; l'indice dice "pagina 214" in tre secondi. Ma l'indice è ordinato per parola: se cerchi *tutte le parole che finiscono in -zione*, non serve a niente e devi sfogliare comunque.

```
UN B-TREE È UN ALBERO ORDINATO. Trovare un valore costa O(log n):
su dieci milioni di righe sono circa quattro letture invece di
dieci milioni.

Costa anche: ogni INSERT, UPDATE e DELETE deve aggiornare OGNI
indice della tabella. Dieci indici su una tabella di scrittura
intensa sono dieci strutture da mantenere a ogni riga.
  ➜ un indice si aggiunge per una query che esiste, non per ogni
    colonna "che potrebbe servire".
```

```sql
-- L'ORDINE DELLE COLONNE IN UN INDICE COMPOSTO NON È ARBITRARIO
CREATE INDEX idx_ordini_utente_data ON ordini (utente_id, creato_il DESC);

-- ✅ usa l'indice: filtra sul PRIMO campo
SELECT * FROM ordini WHERE utente_id = 42;
SELECT * FROM ordini WHERE utente_id = 42 ORDER BY creato_il DESC;

-- ❌ NON usa l'indice: salta il primo campo
SELECT * FROM ordini WHERE creato_il > now() - interval '1 day';
```

```
LA REGOLA DEL PREFISSO: un indice su (A, B, C) serve le query che
filtrano su A, su (A,B) o su (A,B,C) — mai quelle che partono da B.
È lo stesso motivo per cui un elenco telefonico ordinato per
cognome-nome non aiuta a cercare per nome.

L'ORDINE GIUSTO: prima le colonne su cui si filtra per UGUAGLIANZA,
poi quelle di ordinamento o di intervallo. Un indice su
(creato_il, utente_id) non serve la query per utente.
```

```sql
-- ❌ I QUATTRO MODI PIÙ COMUNI DI RENDERE UN INDICE INUTILE

-- 1. una funzione applicata alla colonna
WHERE lower(email) = 'mario@example.com';
--    → serve un indice sull'ESPRESSIONE:
--    CREATE INDEX idx_utenti_email_lower ON utenti (lower(email));

-- 2. il carattere jolly a sinistra
WHERE nome LIKE '%tastiera%';
--    → un B-tree è ordinato dall'inizio: serve un indice GIN con
--    pg_trgm, oppure la ricerca full-text

-- 3. un tipo diverso, che forza una conversione implicita
WHERE utente_id = '42';        -- bigint confrontato con text

-- 4. una condizione OR su colonne diverse
WHERE email = 'x' OR telefono = 'y';
--    → spesso conviene una UNION di due query, ciascuna
--    servita dal proprio indice
```

```
I TIPI DI INDICE OLTRE AL B-TREE, E QUANDO SERVONO
  PARZIALE   CREATE INDEX … WHERE stato = 'attivo'
    Indicizza solo le righe che interessano. Su una tabella dove il
    5% è attivo, l'indice è venti volte più piccolo.
  COPERTURA  CREATE INDEX … (utente_id) INCLUDE (email, nome)
    La query si soddisfa dall'indice senza toccare la tabella
    (index-only scan).
  GIN        per JSONB, array e ricerca full-text.
  BRIN       per tabelle enormi e ordinate fisicamente (serie
    storiche): occupa una frazione di un B-tree, ma funziona solo
    se la correlazione fisica è alta (`pg_stats.correlation` > 0,9).
```

---

## B2. EXPLAIN ANALYZE: leggere un piano

`EXPLAIN` mostra il piano che il planner ha scelto. `EXPLAIN ANALYZE` **esegue davvero** la query e affianca i numeri reali alle stime.

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM ordini WHERE utente_id = 42 ORDER BY creato_il DESC LIMIT 20;
```

```
-- PRIMA dell'indice
Limit  (cost=254831.02..254831.07 rows=20 width=64)
       (actual time=1842.331..1842.338 rows=20 loops=1)
  ->  Sort  (cost=254831.02..254864.19 rows=13268 width=64)
            (actual time=1842.329..1842.333 rows=20 loops=1)
        Sort Method: top-N heapsort  Memory: 28kB
        ->  Seq Scan on ordini  (cost=0.00..254478.00 rows=13268 …)
                                (actual time=0.038..1836.114 rows=13102 …)
              Filter: (utente_id = 42)
              Rows Removed by Filter: 9986898
              Buffers: shared hit=1204 read=153274
Execution Time: 1842.401 ms
```

```
COSA LEGGERE, IN QUEST'ORDINE

1. "Seq Scan" + "Rows Removed by Filter: 9986898"
   Il database ha letto dieci milioni di righe per tenerne 13.102.
   È il segnale più chiaro che manca un indice.

2. rows STIMATE contro rows REALI
   `rows=13268` (stima) contro `rows=13102` (reale): qui la stima è
   buona. Quando differiscono di ordini di grandezza — stima 10,
   reale 400.000 — il planner sta scegliendo il piano sbagliato
   perché le statistiche sono vecchie: `ANALYZE nome_tabella;`

3. Buffers: read=153274
   Pagine lette dal DISCO (8 kB l'una: ~1,2 GB). `hit` sono quelle
   trovate in memoria. Un rapporto read/hit alto su una query
   frequente significa che i dati caldi non stanno nella cache.

4. Execution Time contro Planning Time
   Se il planning domina, il problema è la query (troppe JOIN,
   troppi indici da valutare), non i dati.
```

```
-- DOPO  CREATE INDEX idx_ordini_utente_data ON ordini (utente_id, creato_il DESC);
Limit  (cost=0.43..8.61 rows=20 width=64)
       (actual time=0.031..0.048 rows=20 loops=1)
  ->  Index Scan using idx_ordini_utente_data on ordini
        (actual time=0.029..0.042 rows=20 loops=1)
        Index Cond: (utente_id = 42)
        Buffers: shared hit=6
Execution Time: 0.071 ms
```

```
Da 1842 ms a 0,07 ms, e da 153.274 pagine lette a 6. Non c'è "Sort":
l'indice è già nell'ordine richiesto, quindi il LIMIT si ferma dopo
venti righe invece di ordinarne tredicimila.

⚠ Questi numeri vengono da una tabella di prova: misura i tuoi.
  Il rapporto, però, è tipico — ed è il motivo per cui la domanda
  "hai guardato il piano?" precede qualunque altra ottimizzazione.
```

---

## B3. Il problema N+1

> **Analogia:** andare al supermercato e tornare a casa dopo ogni articolo. Venti articoli, venti viaggi. Il tempo non lo passi a comprare: lo passi in strada.

```typescript
// ❌ N+1: una query per l'elenco, più una per ogni riga
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

const ordini = await prisma.ordine.findMany({ take: 100 })

for (const ordine of ordini) {
  // 100 query, una per iterazione
  const utente = await prisma.utente.findUnique({ where: { id: ordine.utenteId } })
  console.log(utente?.email, ordine.totaleCentesimi)
}
// Totale: 101 round-trip. Con 2 ms di latenza di rete: 202 ms di
// sola attesa, prima ancora del lavoro del database.
```

```typescript
// ✅ Una query sola: il dato correlato arriva insieme
import { prisma } from './database.js'

const ordiniConUtente = await prisma.ordine.findMany({
  take: 100,
  select: { id: true, totaleCentesimi: true, utente: { select: { email: true } } },
})

for (const ordine of ordiniConUtente) {
  console.log(ordine.utente.email, ordine.totaleCentesimi)
}
```

```
COME SI SCOPRE UN N+1 PRIMA CHE LO SCOPRA LA PRODUZIONE

1. IL LOG DELLE QUERY IN SVILUPPO
   new PrismaClient({ log: ['query'] })
   Se una richiesta HTTP produce centoquattro righe di log, hai
   trovato l'N+1 senza cercarlo.

2. IL CONTATORE PER RICHIESTA
   Un middleware che conta le query e registra un avviso oltre una
   soglia (per esempio venti). È tre righe di codice e intercetta
   ogni regressione futura.

3. IN PRODUZIONE: pg_stat_statements (vedi D3). Una query con
   `calls` enormemente più alto delle richieste servite è un N+1.
```

```
⚠ ATTENZIONE ALL'ESTREMO OPPOSTO. `include` annidato su tre livelli
  su un elenco da cento righe genera una JOIN che moltiplica le
  righe trasferite: cento ordini × dieci articoli × cinque immagini
  sono cinquemila righe per mostrarne cento. Prisma per default
  esegue query separate per le relazioni proprio per evitarlo; il
  punto è chiedere solo i livelli che si useranno.
```

---

## B4. Isolamento e anomalie

Il livello di isolamento decide *quali anomalie sono possibili*. PostgreSQL usa `READ COMMITTED` come predefinito, e quasi nessuno lo cambia — spesso senza sapere cosa comporta.

```
LE ANOMALIE
  DIRTY READ  leggere dati non confermati: PostgreSQL non lo permette
    a nessun livello.
  NON-REPEATABLE READ  la stessa riga letta due volte nella stessa
    transazione ha valori diversi.  Possibile in READ COMMITTED.
  PHANTOM READ  la stessa query restituisce righe NUOVE.  Idem.
  LOST UPDATE  due transazioni leggono, calcolano, scrivono: la
    seconda cancella il lavoro della prima.  ← il più frequente, e
    il più silenzioso

I LIVELLI
  READ COMMITTED (predefinito)  ogni comando vede uno snapshot
    aggiornato: veloce, e sufficiente per la maggior parte delle letture.
  REPEATABLE READ  l'intera transazione vede un solo snapshot; le
    scritture in conflitto falliscono con l'errore 40001.
  SERIALIZABLE  come se le transazioni fossero eseguite una dopo
    l'altra: il più sicuro, e quello che fallisce di più — richiede
    che l'applicazione sappia RIPROVARE.
```

```sql
-- ❌ LOST UPDATE: due prenotazioni concorrenti sull'ultimo posto
-- T1: SELECT posti FROM eventi WHERE id = 1;      → 1
-- T2: SELECT posti FROM eventi WHERE id = 1;      → 1
-- T1: UPDATE eventi SET posti = 0 WHERE id = 1;   → ok
-- T2: UPDATE eventi SET posti = 0 WHERE id = 1;   → ok
-- Due posti venduti, uno disponibile.

-- ✅ SOLUZIONE 1 — l'aggiornamento è RELATIVO, non assoluto
UPDATE eventi SET posti = posti - 1
WHERE id = 1 AND posti > 0;
-- Zero righe aggiornate = niente posti. Atomico, nessun lock esplicito.

-- ✅ SOLUZIONE 2 — il lock esplicito, quando serve leggere e decidere
BEGIN;
  SELECT posti FROM eventi WHERE id = 1 FOR UPDATE;  -- blocca la riga
  -- … logica applicativa …
  UPDATE eventi SET posti = posti - 1 WHERE id = 1;
COMMIT;
```

```
QUALE SCEGLIERE
  L'aggiornamento relativo quando la logica sta in una sola
  istruzione: è più veloce e non tiene lock fra due round-trip.
  FOR UPDATE quando fra la lettura e la scrittura serve logica
  applicativa. ⚠ Blocca le righe fino al COMMIT: transazione corta.
  SERIALIZABLE quando l'invariante coinvolge righe DIVERSE ("la
  somma delle prenotazioni non supera la capienza"): nessun lock di
  riga la protegge, e serve il riavvio automatico su errore 40001.
```

---

## B5. Connection pooling

```
UNA CONNESSIONE POSTGRESQL È UN PROCESSO DEL SISTEMA OPERATIVO:
aprirne una costa millisecondi e alcuni megabyte. Il pool le apre una
volta e le riusa. Il numero giusto NON è "quante ne servono
all'applicazione": è quante il DATABASE riesce a servire davvero.
  Punto di partenza: (core del database × 2) + spindle
  Su una macchina a 8 core con SSD: ~16-20 connessioni TOTALI

⚠ TOTALI, non per processo. Quattro istanze con `connection_limit=20`
  ciascuna sono ottanta connessioni: il pool si divide fra le
  istanze, non si moltiplica.

CONTROINTUITIVO MA VERO: oltre il punto di saturazione, aggiungere
connessioni RALLENTA tutto. Cento query in parallelo su otto core si
contendono CPU e lock; venti alla volta, con le altre in coda,
finiscono prima.
```

```typescript
// L'URL porta i parametri del pool
// postgresql://utente:…@host:5432/db?connection_limit=10&pool_timeout=20
import { PrismaClient } from '@prisma/client'

export const prisma = new PrismaClient({
  log: process.env['NODE_ENV'] === 'development' ? ['query', 'warn'] : ['warn', 'error'],
})

// Lo spegnimento pulito chiude il pool: senza, le connessioni
// restano appese finché il database non le scade
process.on('SIGTERM', () => {
  void prisma.$disconnect()
})
```

```
IL SERVERLESS ROMPE IL MODELLO. Ogni istanza di funzione ha il suo
pool, e le istanze possono essere centinaia: il database esaurisce
le connessioni prima di essere sotto carico. Le tre risposte:
  · PgBouncer in modalità `transaction`: molte connessioni client
    condividono poche connessioni al database. ⚠ In questa modalità
    i prepared statement e le sessioni non funzionano: con Prisma
    serve `?pgbouncer=true`.
  · un pooler gestito (Prisma Accelerate, Neon, Supabase pooler)
  · un driver HTTP, che non tiene una connessione TCP aperta
```

---

## B6. Normalizzazione, e quando denormalizzare

```
LE TRE FORME NORMALI, IN UNA RIGA CIASCUNA
  1NF  ogni cella contiene UN valore. Niente "rosso,verde,blu" in
       una colonna di testo.
  2NF  ogni colonna dipende dalla chiave INTERA. In una tabella con
       chiave (ordine_id, prodotto_id), il nome del prodotto non ci
       sta: dipende solo da prodotto_id.
  3NF  nessuna colonna dipende da un'altra colonna non chiave. Se ci
       sono cap e città, la città dipende dal cap, non dall'ordine.

In pratica: OGNI FATTO STA IN UN POSTO SOLO. Se un dato è scritto in
due tabelle, prima o poi le due divergono — e nessuno sa quale ha
ragione.

LE TRE DENORMALIZZAZIONI CHE SI RIPAGANO
1. I VALORI STORICI COPIATI (vedi A2). Il prezzo sulla riga d'ordine
   non è denormalizzazione: è un fatto diverso dal prezzo di listino
   di oggi.
2. I CONTATORI AGGREGATI. `prodotti.numero_recensioni` evita un
   count(*) su ogni pagina di catalogo. Il costo è mantenerlo
   allineato — con un trigger, non con il codice applicativo, che
   dimentica il caso in cui la recensione viene cancellata.
3. LE VISTE MATERIALIZZATE per la reportistica: il report mensile non
   deve aggregare dieci milioni di righe a ogni apertura.
   ⚠ REFRESH MATERIALIZED VIEW blocca le letture; la variante
     CONCURRENTLY no, ma richiede un indice unico sulla vista.

LA REGOLA: normalizza per primo, denormalizza quando hai MISURATO
che serve, e scrivi accanto alla denormalizzazione chi la mantiene
allineata. Una denormalizzazione senza un proprietario diventa un
dato sbagliato.
```

---
## B7. JSONB: quando il relazionale non basta

```sql
-- jsonb, non json: json memorizza il testo così com'è, jsonb lo
-- analizza in forma binaria — più lento in scrittura, molto più
-- veloce in lettura, e indicizzabile
ALTER TABLE prodotti ADD COLUMN attributi jsonb NOT NULL DEFAULT '{}';

-- L'indice GIN rende interrogabile il contenuto
CREATE INDEX idx_prodotti_attributi ON prodotti USING GIN (attributi);

-- @> "contiene": usa l'indice GIN
SELECT id, nome FROM prodotti WHERE attributi @> '{"colore": "rosso"}';

-- ->> estrae un valore come testo: NON usa l'indice GIN generico.
-- Per questa serve un indice sull'espressione:
CREATE INDEX idx_prodotti_taglia ON prodotti ((attributi->>'taglia'));
SELECT id FROM prodotti WHERE attributi->>'taglia' = 'M';
```

```
QUANDO JSONB È LA SCELTA GIUSTA
  ✅ attributi che variano per riga e che nessuno interroga per nome
     fisso: le specifiche di un prodotto, dove una tastiera ha
     "layout" e una sedia ha "portata_kg"
  ✅ il payload grezzo di un webhook, per poter rileggere ciò che
     era arrivato · configurazioni e preferenze utente

QUANDO NON LO È
  ❌ dati su cui si fa JOIN, si aggrega o si applicano vincoli: un
     CHECK non guarda dentro un JSONB in modo ragionevole, e una
     foreign key nemmeno
  ❌ campi che tutte le righe hanno: se il 100% dei prodotti ha
     `attributi->>'peso'`, quella è una colonna
  ❌ come scusa per non decidere lo schema. Il debito si paga al
     primo report che deve aggregare su un campo dentro il JSON.
```

---

## B8. Migrazioni senza downtime

> **Analogia:** sostituire i binari mentre i treni passano. Non si chiude la linea: si posa il binario nuovo accanto, si spostano i treni, si toglie il vecchio. Tre operazioni invece di una, e nessuna interruzione.

```
IL PROBLEMA: durante un deploy convivono per qualche minuto la
versione VECCHIA e quella NUOVA dell'applicazione. Una migrazione
che rompe la vecchia interrompe il servizio; una che rompe la nuova
fa fallire il deploy.

EXPAND-CONTRACT, IN TRE RILASCI
  1. ESPANDI   aggiungi il nuovo, senza toccare il vecchio. Il
     codice vecchio continua a funzionare.
  2. MIGRA     il codice nuovo scrive su ENTRAMBI e legge dal
     nuovo; uno script riempie il nuovo per le righe esistenti.
  3. CONTRAI   quando nessuna versione in esecuzione usa il
     vecchio, lo si rimuove.
```

```sql
-- RILASCIO 1 — espandi: nullable, senza default costoso
ALTER TABLE utenti ADD COLUMN email_verificata_il timestamptz;

-- RILASCIO 2 — riempi a LOTTI, non con un solo UPDATE
-- (un UPDATE su dieci milioni di righe tiene un lock e riempie il WAL)
UPDATE utenti SET email_verificata_il = creato_il
WHERE email_verificata_il IS NULL AND id IN (
  SELECT id FROM utenti WHERE email_verificata_il IS NULL LIMIT 10000
);
-- ripetuto finché non aggiorna zero righe

-- RILASCIO 3 — contrai: il vincolo in DUE passi
-- NOT VALID non verifica le righe esistenti: lock breve
ALTER TABLE utenti ADD CONSTRAINT utenti_email_verificata_non_nulla
  CHECK (email_verificata_il IS NOT NULL) NOT VALID;
-- VALIDATE legge la tabella ma NON blocca scritture e letture
ALTER TABLE utenti VALIDATE CONSTRAINT utenti_email_verificata_non_nulla;
```

```
LE OPERAZIONI CHE BLOCCANO, E LE ALTERNATIVE
  CREATE INDEX                blocca le SCRITTURE per tutta la durata
    → CREATE INDEX CONCURRENTLY (più lento, non blocca; ⚠ non può
      stare in una transazione, e se fallisce lascia un indice
      INVALID da eliminare a mano)
  ALTER TABLE … SET NOT NULL  scansione completa con lock esclusivo
    → il CHECK … NOT VALID + VALIDATE mostrato sopra
  ALTER COLUMN … TYPE         riscrive l'intera tabella
    → colonna nuova + copia a lotti + rename (expand-contract)
  DROP COLUMN                 istantaneo, ma IRREVERSIBILE
    → prima si smette di usarla, si aspetta un rilascio, poi si
      elimina

⚠ Qualunque ALTER TABLE si mette in coda dietro le transazioni
  aperte sulla tabella, e tutto ciò che arriva dopo si accoda dietro
  di lui. Su una tabella calda, imposta `lock_timeout = '3s'` prima
  della migrazione: meglio fallire e riprovare che bloccare tutto.
```

---

## B9. Redis come cache: le tre trappole

```typescript
// Il pattern cache-aside: leggi dalla cache, se manca leggi dal
// database e riscrivi la cache
import { createClient } from 'redis'
import { prisma } from './database.js'

const redis = createClient({ url: process.env['REDIS_URL'] })

export async function leggiProdotto(id: bigint) {
  const chiave = `prodotto:${id}`

  const memorizzato = await redis.get(chiave)
  if (memorizzato) return JSON.parse(memorizzato)

  const prodotto = await prisma.prodotto.findUnique({ where: { id } })
  if (!prodotto) return null

  // Il TTL è obbligatorio: una cache senza scadenza è una copia che
  // diverge per sempre
  await redis.set(chiave, JSON.stringify(prodotto), { EX: 300 })
  return prodotto
}
```

```
TRAPPOLA 1 — L'INVALIDAZIONE DIMENTICATA  chi scrive nel database
  deve invalidare la cache, e chi scrive è in venti punti diversi.
  La soluzione che regge: l'invalidazione sta nella STESSA funzione
  della scrittura, e il TTL è la rete di sicurezza per i punti
  dimenticati.

TRAPPOLA 2 — IL CACHE STAMPEDE  una chiave molto richiesta scade, e
  mille richieste concorrenti vanno tutte al database nello stesso
  millisecondo. Le difese: un lock per chiave (solo il primo
  ricalcola), oppure un TTL con jitter (300 s ± 30) così le chiavi
  non scadono tutte insieme.

TRAPPOLA 3 — LA CACHE TRATTATA COME UN DATABASE  Redis può perdere
  dati: è in memoria, e la persistenza è asincrona. Se il sistema non
  funziona quando Redis è vuoto, quello non è una cache ma un
  database senza durabilità. Provalo: `FLUSHALL` in staging, e guarda
  cosa si rompe.

COSA VALE LA PENA METTERE IN CACHE  dati letti spesso e cambiati
  raramente: catalogo, listini, configurazioni, aggregazioni costose.
  NON i dati per utente con bassa frequenza di lettura (la cache non
  viene mai colpita), NON i dati che devono essere esatti al
  millisecondo (saldi, giacenze all'acquisto). Prima di aggiungere
  Redis, misura: molto spesso la query lenta diventa veloce con
  l'indice giusto, e un livello in meno da mantenere vale più di
  qualche millisecondo.
```

---
# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Diagnosticare e correggere un N+1

**Obiettivo:** dato un endpoint lento, trovare l'N+1 con gli strumenti e correggerlo.

```typescript
// IL CODICE DA CORREGGERE — la pagina "i miei ordini" impiega 2,4 s
export async function ordiniUtente(utenteId: bigint) {
  const ordini = await prisma.ordine.findMany({ where: { utenteId } })

  const risultato = []
  for (const ordine of ordini) {
    const articoli = await prisma.ordineArticolo.findMany({
      where: { ordineId: ordine.id },
    })

    const conNomi = []
    for (const articolo of articoli) {
      const prodotto = await prisma.prodotto.findUnique({
        where: { id: articolo.prodottoId },
      })
      conNomi.push({ ...articolo, nome: prodotto?.nome })
    }

    risultato.push({ ...ordine, articoli: conNomi })
  }
  return risultato
}
```

```
# LA DIAGNOSI
#   new PrismaClient({ log: ['query'] }) e una richiesta:
#     SELECT … FROM ordini WHERE utente_id = $1        ×1
#     SELECT … FROM ordini_articoli WHERE ordine_id=$1 ×40
#     SELECT … FROM prodotti WHERE id = $1             ×178
#   219 query per una pagina. Con 2 ms di latenza sono 438 ms di
#   sola rete, prima del lavoro del database.
#
#   È un N+1 ANNIDATO: il ciclo interno moltiplica quello esterno.
#   Ogni ordine in più costa una query per sé e una per articolo.
```

```typescript
// LA SOLUZIONE — una query per livello, non una per riga
export async function ordiniUtente(utenteId: bigint) {
  return prisma.ordine.findMany({
    where: { utenteId },
    orderBy: { creatoIl: 'desc' },
    // Il limite: senza, l'utente con diecimila ordini li scarica tutti
    take: 20,
    select: {
      id: true,
      creatoIl: true,
      totaleCentesimi: true,
      stato: true,
      articoli: {
        select: {
          quantita: true,
          prezzoUnitarioCentesimi: true,
          // Prisma risolve la relazione annidata con una seconda
          // query per LIVELLO, non per riga
          prodotto: { select: { id: true, nome: true } },
        },
      },
    },
  })
}
```

```sql
-- L'indice che rende veloce il filtro e l'ordinamento
CREATE INDEX idx_ordini_utente_data ON ordini (utente_id, creato_il DESC);
-- E quello sulla chiave esterna: PostgreSQL NON lo crea da solo
CREATE INDEX idx_ordini_articoli_ordine ON ordini_articoli (ordine_id);
```

```
# IL RISULTATO: da 219 query a 3, e da 2,4 s a circa 15 ms.
#
# ⚠ IL DETTAGLIO CHE QUASI TUTTI IGNORANO: PostgreSQL crea
#   automaticamente un indice sulla PRIMARY KEY e sui vincoli
#   UNIQUE, ma NON sulle FOREIGN KEY. Ogni `WHERE chiave_esterna = …`
#   senza indice è una scansione completa — ed è la causa più
#   comune di lentezza inspiegabile dopo un N+1 già corretto.
```

---

### Esercizio 2 — Dalla query lenta all'indice giusto

**Obiettivo:** partire da `EXPLAIN ANALYZE`, capire cosa manca, aggiungere l'indice e verificare.

```sql
-- LA QUERY: il pannello amministrativo, ordini pagati dell'ultimo
-- mese sopra i cento euro, dal più recente
EXPLAIN (ANALYZE, BUFFERS)
SELECT o.id, o.creato_il, o.totale_centesimi, u.email
FROM ordini o
JOIN utenti u ON u.id = o.utente_id
WHERE o.stato = 'pagato'
  AND o.creato_il >= now() - interval '30 days'
  AND o.totale_centesimi >= 10000
ORDER BY o.creato_il DESC
LIMIT 50;
```

```
# IL PIANO PRIMA
#   Seq Scan on ordini  (actual rows=41892 loops=1)
#     Filter: ((stato = 'pagato') AND (creato_il >= …)
#              AND (totale_centesimi >= 10000))
#     Rows Removed by Filter: 9958108
#     Buffers: shared read=153274
#   Execution Time: 2104.882 ms
#
# LA LETTURA
#   Dieci milioni di righe lette, 41.892 tenute, 50 restituite.
#   Nessun indice serve nessuna delle tre condizioni.
```

```sql
-- ❌ IL PRIMO TENTATIVO SBAGLIATO: tre indici separati
CREATE INDEX ON ordini (stato);
CREATE INDEX ON ordini (creato_il);
CREATE INDEX ON ordini (totale_centesimi);
-- PostgreSQL può combinarli con un BitmapAnd, ma è molto più lento
-- di un indice composto, e mantenerne tre costa a ogni scrittura.
-- Peggio: `stato` ha quattro valori distinti su dieci milioni di
-- righe — la selettività è pessima e il planner lo ignorerà.

-- ✅ L'INDICE GIUSTO: parziale sullo stato, composto sul resto
CREATE INDEX idx_ordini_pagati_recenti
  ON ordini (creato_il DESC, totale_centesimi)
  WHERE stato = 'pagato';
```

```
# PERCHÉ QUESTO
#   · WHERE stato = 'pagato' è un indice PARZIALE: contiene solo le
#     righe che la query guarda. Se i pagati sono il 30%, l'indice è
#     un terzo, e le scritture sugli altri stati non lo toccano.
#   · creato_il DESC come PRIMA colonna: serve sia l'intervallo sia
#     l'ORDER BY, quindi sparisce il nodo "Sort" e il LIMIT si ferma
#     dopo cinquanta righe.
#   · totale_centesimi come SECONDA: filtra le righe già trovate
#     senza tornare alla tabella.
#
# IL PIANO DOPO
#   Index Scan using idx_ordini_pagati_recenti  (actual rows=50)
#     Index Cond: (creato_il >= …)
#     Filter: (totale_centesimi >= 10000)
#     Buffers: shared hit=62
#   Execution Time: 1.204 ms
#
# LA VERIFICA CHE NON VA SALTATA
#   SELECT indexrelname, idx_scan FROM pg_stat_user_indexes
#   WHERE relname = 'ordini';
#   Un indice con idx_scan = 0 dopo una settimana di produzione non
#   serve a nessuno: costa a ogni scrittura e va eliminato.
```

---

### Esercizio 3 — Rendere obbligatoria una colonna senza downtime

**Obiettivo:** `ordini.valuta` è nullable su dieci milioni di righe. Renderla `NOT NULL` con `DEFAULT 'EUR'` senza interrompere il servizio.

```sql
-- ❌ LA MIGRAZIONE INGENUA — non fatelo su una tabella calda
ALTER TABLE ordini ALTER COLUMN valuta SET DEFAULT 'EUR';
UPDATE ordini SET valuta = 'EUR' WHERE valuta IS NULL;
ALTER TABLE ordini ALTER COLUMN valuta SET NOT NULL;

-- COSA SUCCEDE
--  · l'UPDATE tocca dieci milioni di righe in una transazione:
--    minuti di esecuzione, gigabyte di WAL, e ogni riga bloccata
--  · SET NOT NULL prende un lock ACCESS EXCLUSIVE e scansiona
--    tutta la tabella: nessuno può nemmeno LEGGERE nel frattempo
--  · la versione vecchia dell'applicazione, che scrive NULL, va in
--    errore appena il vincolo esiste
```

```sql
-- ✅ PASSO 1 (rilascio 1) — il default, che è solo catalogo
-- Da PostgreSQL 11 non riscrive la tabella: lock brevissimo.
SET lock_timeout = '3s';
ALTER TABLE ordini ALTER COLUMN valuta SET DEFAULT 'EUR';
-- Da qui le righe NUOVE hanno la valuta. Il codice vecchio
-- continua a funzionare: la colonna è ancora nullable.
```

```sql
-- ✅ PASSO 2 — riempire le righe vecchie A LOTTI
-- Ogni lotto è una transazione breve: i lock durano millisecondi e
-- il WAL non esplode. Da eseguire in un ciclo finché aggiorna 0 righe.
UPDATE ordini SET valuta = 'EUR'
WHERE id IN (
  SELECT id FROM ordini WHERE valuta IS NULL ORDER BY id LIMIT 5000
);
```

```sql
-- ✅ PASSO 3 (rilascio 2) — il vincolo in DUE passi
-- NOT VALID: il vincolo vale per le righe NUOVE senza verificare le
-- esistenti. Lock breve.
ALTER TABLE ordini
  ADD CONSTRAINT ordini_valuta_non_nulla CHECK (valuta IS NOT NULL) NOT VALID;

-- VALIDATE legge tutta la tabella ma prende solo un lock SHARE
-- UPDATE EXCLUSIVE: letture e scritture ordinarie continuano.
ALTER TABLE ordini VALIDATE CONSTRAINT ordini_valuta_non_nulla;
```

```sql
-- ✅ PASSO 4 (facoltativo, rilascio 3) — il vero NOT NULL
-- Da PostgreSQL 12, se esiste già un CHECK validato equivalente,
-- SET NOT NULL non riscansiona la tabella: il lock dura un istante.
ALTER TABLE ordini ALTER COLUMN valuta SET NOT NULL;
ALTER TABLE ordini DROP CONSTRAINT ordini_valuta_non_nulla;
```

```
# LA VERIFICA, DURANTE E DOPO
#  1. mentre i lotti girano, controlla i lock in attesa:
#     SELECT pid, wait_event_type, query FROM pg_stat_activity
#     WHERE wait_event_type = 'Lock';
#  2. a fine passo 2:  SELECT count(*) FROM ordini WHERE valuta IS NULL;  → 0
#  3. dopo il passo 3: un INSERT con valuta NULL deve fallire
#  4. il tempo di risposta dell'API non deve avere picchi in nessun
#     momento: se ne vedi uno, il lotto è troppo grande
```

---

## C2. Mini-progetto: schema e-commerce con Prisma

L'esercizio chiave del modulo: schema di un sistema e-commerce con migrazioni, seed e query ottimizzate.

```prisma
// prisma/schema.prisma (estratto — le parti che portano le decisioni)
model Prodotto {
  id           BigInt   @id @default(autoincrement())
  sku          String   @unique
  nome         String
  // Il prezzo di LISTINO di oggi. Quello dell'ordine si copia.
  prezzoCentesimi Int   @map("prezzo_centesimi")
  giacenza     Int      @default(0)
  attivo       Boolean  @default(true)
  attributi    Json     @default("{}")

  righe        RigaOrdine[]

  // Parziale: le query di catalogo filtrano sempre attivo = true
  @@index([attivo, nome])
  @@map("prodotti")
}

model Ordine {
  id              BigInt      @id @default(autoincrement())
  numero          String      @unique
  utenteId        BigInt      @map("utente_id")
  totaleCentesimi Int         @map("totale_centesimi")
  stato           StatoOrdine @default(in_attesa)
  creatoIl        DateTime    @default(now()) @map("creato_il")

  utente          Utente       @relation(fields: [utenteId], references: [id])
  righe           RigaOrdine[]

  @@index([utenteId, creatoIl(sort: Desc)])
  @@map("ordini")
}

model RigaOrdine {
  ordineId    BigInt @map("ordine_id")
  prodottoId  BigInt @map("prodotto_id")
  quantita    Int
  // COPIATO al momento dell'ordine: il listino può cambiare, la
  // fattura di ieri no
  prezzoUnitarioCentesimi Int @map("prezzo_unitario_centesimi")

  ordine      Ordine   @relation(fields: [ordineId], references: [id], onDelete: Cascade)
  prodotto    Prodotto @relation(fields: [prodottoId], references: [id], onDelete: Restrict)

  @@id([ordineId, prodottoId])
  @@index([prodottoId])
  @@map("righe_ordine")
}
```

```typescript
// src/servizi/ordini.ts — la creazione di un ordine è UNA
// transazione: giacenza, righe e totale devono essere coerenti
import { PrismaClient, Prisma } from '@prisma/client'

const prisma = new PrismaClient()

export async function creaOrdine(utenteId: bigint, carrello: { prodottoId: bigint; quantita: number }[]) {
  return prisma.$transaction(
    async (tx) => {
      let totale = 0
      const righe = []

      for (const voce of carrello) {
        // updateMany con la condizione sulla giacenza è ATOMICO:
        // se un altro ordine ha svuotato il magazzino, aggiorna
        // zero righe e lo scopriamo qui
        const scalato = await tx.prodotto.updateMany({
          where: { id: voce.prodottoId, attivo: true, giacenza: { gte: voce.quantita } },
          data: { giacenza: { decrement: voce.quantita } },
        })

        if (scalato.count === 0) {
          throw new Error(`Giacenza insufficiente per il prodotto ${voce.prodottoId}`)
        }

        const prodotto = await tx.prodotto.findUniqueOrThrow({ where: { id: voce.prodottoId } })
        totale += prodotto.prezzoCentesimi * voce.quantita
        righe.push({
          prodottoId: voce.prodottoId,
          quantita: voce.quantita,
          prezzoUnitarioCentesimi: prodotto.prezzoCentesimi,
        })
      }

      return tx.ordine.create({
        data: {
          numero: `ORD-${Date.now()}`,
          utenteId,
          totaleCentesimi: totale,
          righe: { create: righe },
        },
        select: { id: true, numero: true, totaleCentesimi: true },
      })
    },
    // Il timeout evita che una transazione appesa blocchi le righe
    { isolationLevel: Prisma.TransactionIsolationLevel.ReadCommitted, timeout: 10_000 },
  )
}
```

```
# LA VERIFICA, IN ORDINE
# 1. LO SCHEMA È COERENTE CON IL DATABASE
#    pnpm prisma migrate diff … --exit-code   → nessuna differenza
# 2. IL SEED È RIPETIBILE
#    eseguirlo due volte non deve duplicare né fallire (upsert)
# 3. LA GIACENZA NON VA MAI SOTTO ZERO
#    lancia venti ordini CONCORRENTI sull'ultimo pezzo: uno solo
#    deve riuscire, diciannove devono ricevere l'errore
# 4. NESSUN N+1
#    log: ['query'] su "i miei ordini" → poche query, non una per riga
# 5. OGNI QUERY DELL'APPLICAZIONE HA IL SUO INDICE
#    EXPLAIN su ognuna: nessun "Seq Scan" su tabelle grandi
# 6. GLI INDICI SERVONO DAVVERO
#    pg_stat_user_indexes dopo una settimana: idx_scan = 0 → eliminalo
# 7. UNA CANCELLAZIONE NON DISTRUGGE LO STORICO
#    cancellare un prodotto venduto deve FALLIRE (onDelete: Restrict)
# 8. IL RESTORE FUNZIONA
#    ripristina il dump su un database vuoto e riesegui i test (D5)
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Row-Level Security e multi-tenancy

Con più clienti nella stessa tabella, l'isolamento affidato al `WHERE tenant_id = …` dell'applicazione dipende dal fatto che *nessuno lo dimentichi mai*. La Row-Level Security sposta la garanzia nel database.

```sql
ALTER TABLE ordini ENABLE ROW LEVEL SECURITY;

CREATE POLICY isolamento_tenant ON ordini
  USING (tenant_id = current_setting('app.tenant_id')::bigint);

-- ⚠ Il proprietario della tabella BYPASSA le policy per default.
--    L'applicazione deve connettersi con un ruolo che non lo è.
ALTER TABLE ordini FORCE ROW LEVEL SECURITY;
```

```typescript
// L'impostazione va fatta sulla STESSA connessione della query:
// con un pool, questo significa dentro una transazione
export async function conTenant<T>(tenantId: bigint, azione: (tx: unknown) => Promise<T>) {
  return prisma.$transaction(async (tx) => {
    // set_config con local=true: il valore vale solo per questa
    // transazione e non inquina la connessione successiva
    await tx.$executeRaw`SELECT set_config('app.tenant_id', ${tenantId.toString()}, true)`
    return azione(tx)
  })
}
```

```
LE TRE STRATEGIE DI MULTI-TENANCY
  TABELLA CONDIVISA + tenant_id  la più semplice ed economica; con
    RLS è anche sicura. ⚠ Ogni indice deve avere tenant_id come
    PRIMA colonna, altrimenti ogni query scansiona tutti i clienti.
  SCHEMA PER TENANT  isolamento più forte, migrazioni moltiplicate
    per cliente: oltre qualche centinaio diventa ingestibile.
  DATABASE PER TENANT  isolamento e costo massimi: si giustifica con
    requisiti di legge o clienti molto grandi.
```

---

## D2. Testare con un database vero

```typescript
// Un mock del database verifica che il mock funzioni. I vincoli, le
// transazioni, i tipi e i piani di esecuzione esistono solo nel
// database reale: quelli sono i bug che i test devono trovare.
import { PostgreSqlContainer, type StartedPostgreSqlContainer } from '@testcontainers/postgresql'
import { beforeAll, afterAll } from 'vitest'

let container: StartedPostgreSqlContainer

beforeAll(async () => {
  container = await new PostgreSqlContainer('postgres:17-alpine').start()
  process.env['DATABASE_URL'] = container.getConnectionUri()
  await eseguiMigrazioni()
}, 60_000)

afterAll(async () => {
  await container.stop()
})
```

```
COSA VERIFICARE, IN ORDINE DI VALORE
  1. i VINCOLI: un inserimento che viola una CHECK o una foreign key
     DEVE fallire. Se passa, il vincolo non esiste davvero.
  2. la CONCORRENZA: venti operazioni parallele sull'ultimo pezzo di
     magazzino. È l'unico modo di provare che la transazione regge.
  3. le MIGRAZIONI applicate da zero su un database vuoto a ogni
     esecuzione della CI: una migrazione che funziona solo sul
     database di sviluppo non è una migrazione.
  4. il ROLLBACK: la transazione che fallisce a metà non deve
     lasciare righe.

L'ISOLAMENTO FRA TEST: aprire una transazione in `beforeEach` e
annullarla in `afterEach` è più veloce di TRUNCATE e non tocca le
sequenze.
```

---
## D3. pg_stat_statements: trovare le query che costano

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Ordinate per TEMPO TOTALE, non per tempo medio: una query da 5 ms
-- eseguita un milione di volte costa più di una da 2 s eseguita dieci
SELECT
  round(total_exec_time::numeric / 1000, 1) AS secondi_totali,
  calls,
  round(mean_exec_time::numeric, 2)         AS ms_medi,
  round(stddev_exec_time::numeric, 2)       AS deviazione,
  rows / GREATEST(calls, 1)                 AS righe_per_chiamata,
  left(query, 90)                           AS query
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY total_exec_time DESC LIMIT 20;
```

```
COME SI LEGGE
  · `calls` enormemente più alto del numero di richieste servite →
    N+1. È il modo più affidabile di trovarli in produzione.
  · `stddev` alto con `mean` basso → il planner cambia piano al
    variare dei parametri, oppure la cache a volte manca.
  · `righe_per_chiamata` enorme → manca un LIMIT, o si stanno
    selezionando colonne inutili.
⚠ Azzera i contatori dopo un deploy (`pg_stat_statements_reset()`):
  altrimenti i numeri mescolano il prima e il dopo, e non si capisce
  se il rilascio ha migliorato o peggiorato.
```

---

## D4. Il denaro nel database

```sql
-- ❌ real e double precision sono in VIRGOLA MOBILE
SELECT 0.1::real + 0.2::real;   -- 0.3 apparente, non esatto
-- Su diecimila righe l'errore diventa visibile in bilancio.

-- ✅ DUE SCELTE CORRETTE
--   1. numeric(12,2) — decimale esatto, aritmetica precisa,
--      leggibile. Più lento delle operazioni su interi.
--   2. integer nei centesimi — il più veloce e il più difficile da
--      sbagliare, purché il nome della colonna dica l'unità.
totale_centesimi integer NOT NULL CHECK (totale_centesimi >= 0)
```

```typescript
// ⚠ IL PUNTO IN CUI SI PERDE COMUNQUE LA PRECISIONE: il numero di
//    JavaScript è un double. Una colonna numeric perfetta letta in
//    un `number` è già rovinata.
//
//    Prisma mappa Decimal su un oggetto Decimal.js, non su number:
//    conserva la precisione FINCHÉ non chiami .toNumber().
//    Con i centesimi interi il problema non esiste: Number.MAX_SAFE_INTEGER
//    copre novantamila miliardi di euro.

// La regola operativa: interi in centesimi dal database fino al
// JSON, e la formattazione SOLO al momento di mostrare il valore
export function formattaEuro(centesimi: number): string {
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(
    centesimi / 100,
  )
}
```

---

## D5. Un backup non esiste finché non è stato ripristinato

```powershell
# Il dump logico: portabile fra versioni, lento su database grandi
pg_dump --format=custom --file=backup.dump $env:DATABASE_URL

# Il ripristino su un database VUOTO — la parte che quasi nessuno prova
createdb verifica_restore
pg_restore --dbname=verifica_restore --exit-on-error backup.dump
```

```
LE QUATTRO DOMANDE A CUI UN PIANO DI BACKUP DEVE RISPONDERE
  1. QUANTO POSSO PERDERE (RPO)? Un dump notturno significa fino a
     ventiquattro ore di dati persi. Se non è accettabile, serve
     l'archiviazione continua del WAL (point-in-time recovery).
  2. QUANTO POSSO STARE FERMO (RTO)? Il ripristino di un dump da
     500 GB non è un'operazione da dieci minuti: misuralo.
  3. IL RIPRISTINO FUNZIONA? Provalo su un calendario, non "quando
     ci sarà tempo". Un backup mai ripristinato è una speranza.
  4. IL BACKUP SOPRAVVIVE A CHI CANCELLA? Un backup sullo stesso
     account cloud sparisce insieme all'account compromesso.
     Servono copie separate e immutabili.

⚠ UNA REPLICA NON È UN BACKUP: replica ogni cosa, compreso l'errore
  umano, in pochi secondi.
```

---
# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
DATABASE PER IL WEB — Mappa dei concetti

LO SCHEMA
├── i vincoli stanno nel DATABASE: valgono anche per chi scrive
│     fuori dall'applicazione (NOT NULL · CHECK · UNIQUE · FK con
│     ON DELETE scelto relazione per relazione)
├── timestamptz mai timestamp · bigint per le chiavi · mai float
│     per il denaro
└── i valori storici si COPIANO: il prezzo dell'ordine non è il
      prezzo di listino di oggi

RELAZIONI
├── uno-a-molti: chiave esterna dalla parte del molti
├── molti-a-molti: tabella ponte con chiave primaria composta
└── PostgreSQL indicizza la primary key, NON le foreign key

TRANSAZIONI
├── READ COMMITTED è il predefinito: lost update possibile
├── aggiornamento RELATIVO (SET x = x - 1 WHERE x > 0) o FOR UPDATE
├── SERIALIZABLE quando l'invariante coinvolge righe diverse, con
│     riavvio automatico sull'errore 40001
└── mai chiamate esterne dentro una transazione; mai transazioni lunghe

INDICI E PIANI
├── B-tree: regola del prefisso, uguaglianze prima, ordinamento poi
├── li rendono inutili: funzioni sulla colonna, LIKE '%x', tipi
│     diversi, OR fra colonne diverse
├── parziale · copertura (INCLUDE) · GIN per JSONB · BRIN per serie
└── EXPLAIN ANALYZE: Seq Scan, righe stimate contro reali, Buffers

N+1  una query per l'elenco più una per riga. Si scopre con
  log:['query'], un contatore per richiesta o pg_stat_statements; si
  corregge con select/include, non con un ciclo.

PRODUZIONE
├── pool dimensionato sul DATABASE (core × 2), TOTALE fra le istanze
├── serverless: PgBouncer transaction, pooler gestito, o driver HTTP
├── migrazioni: file immutabili, mai db push, mai a mano
├── senza downtime: expand-contract, lotti, CHECK NOT VALID +
│     VALIDATE, CREATE INDEX CONCURRENTLY, lock_timeout
├── Redis: TTL obbligatorio, invalidazione accanto alla scrittura,
│     jitter contro lo stampede — e non è un database
├── RLS per il multi-tenancy, con FORCE e un ruolo non proprietario
└── il backup esiste solo dopo un restore riuscito
```

---
## Checklist di competenze

**Parte A — Basi**

- [ ] Sai perché i vincoli vanno nel database e non solo nel codice
- [ ] Scegli fra `ON DELETE CASCADE` e `RESTRICT` con una motivazione
- [ ] Sai perché `timestamptz` e non `timestamp`, `bigint` e non `integer`
- [ ] Modelli un molti-a-molti con la tabella ponte e la chiave composta
- [ ] Sai perché il prezzo si copia sulla riga d'ordine
- [ ] Sai in cosa `LEFT JOIN` differisce da `JOIN`, e la trappola del `WHERE`
- [ ] Sai cosa garantisce ciascuna lettera di ACID, e perché una chiamata HTTP non va dentro una transazione
- [ ] Leggi uno schema Prisma e conosci le tre regole delle migrazioni

**Parte B — Comprensione**

- [ ] Sai spiegare la regola del prefisso su un indice composto, e quattro modi di rendere inutile un indice
- [ ] Sai quando serve un indice parziale, di copertura, GIN o BRIN
- [ ] Leggi un `EXPLAIN ANALYZE` e riconosci Seq Scan, stime sbagliate e Buffers
- [ ] Riconosci un N+1 dal log, e sai correggerlo
- [ ] Sai cos'è un lost update e conosci due modi di evitarlo
- [ ] Sai perché aumentare il pool oltre un certo punto rallenta, e perché il serverless rompe il pooling
- [ ] Sai quando una denormalizzazione si ripaga e chi la mantiene
- [ ] Sai quando JSONB è la scelta giusta e quando è un debito
- [ ] Sai eseguire un `SET NOT NULL` su una tabella grande senza fermare il servizio
- [ ] Conosci le tre trappole di una cache Redis

**Parte C — Pratica**

- [ ] Hai trovato l'N+1 annidato e lo hai ridotto a tre query
- [ ] Hai aggiunto l'indice sulla foreign key mancante
- [ ] Hai progettato l'indice parziale e verificato il piano prima e dopo
- [ ] Hai eseguito la migrazione in quattro passi senza picchi di latenza
- [ ] Hai verificato che venti ordini concorrenti sull'ultimo pezzo ne facciano passare uno

**Parte D — Esperto**

- [ ] Configuri la RLS con `FORCE` e un ruolo non proprietario, e sai perché `tenant_id` va per primo in ogni indice
- [ ] Testi contro un database reale e verifichi i vincoli
- [ ] Trovi le query costose con `pg_stat_statements` ordinando per tempo totale
- [ ] Sai perché il denaro non va in virgola mobile, nel database e in JavaScript
- [ ] Hai provato un restore, e sai quanto dura

---
## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Vincoli solo nel codice applicativo | Script, correzioni manuali e altri servizi li aggirano | `NOT NULL`, `CHECK`, `UNIQUE`, foreign key nello schema |
| `real`/`float` per il denaro | Errori di arrotondamento che emergono in bilancio | `numeric(12,2)` o interi in centesimi |
| `timestamp` senza fuso | La stessa riga vale istanti diversi in fusi diversi | `timestamptz` |
| `ON DELETE CASCADE` ovunque | Cancellare un utente distrugge i suoi documenti contabili | `RESTRICT` dove il dato è storico |
| Prezzo letto dal prodotto in fattura | Il passato cambia quando cambia il listino | Copiare il valore sulla riga d'ordine |
| Nessun indice sulle foreign key | Ogni `WHERE fk = …` è una scansione completa | Crearlo esplicitamente: PostgreSQL non lo fa |
| Ciclo che interroga il database | N+1: cento round-trip per una pagina | `select`/`include`, una query per livello |
| Ottimizzare senza `EXPLAIN` | Si aggiungono indici che non vengono usati | Il piano prima, la modifica dopo |
| Pool grande "per sicurezza" | Oltre la saturazione le query rallentano tutte | (core × 2), totale fra le istanze |
| `prisma db push` in produzione, o modificare una migrazione applicata | Nessuna storia né rollback; l'hash non combacia più | `migrate deploy`; una migrazione nuova |
| `UPDATE` massivo in una transazione | Lock lunghi, WAL enorme, servizio fermo | A lotti, una transazione per lotto |
| `CREATE INDEX` su tabella calda | Blocca le scritture per tutta la durata | `CREATE INDEX CONCURRENTLY` |
| `tenant_id` non primo nell'indice | Ogni query scansiona i dati di tutti i clienti | Prima colonna di ogni indice |
| Replica scambiata per backup | Replica anche `DROP TABLE`, in pochi secondi | Copie separate, immutabili, ripristinate |

---
## Troubleshooting rapido

**Una query è improvvisamente lenta, e il codice non è cambiato**
- Causa: statistiche vecchie dopo un caricamento massivo; il planner sceglie un piano sbagliato
- Fix: `ANALYZE nome_tabella;` e confronta `EXPLAIN` prima e dopo

**`EXPLAIN` dice Seq Scan anche se l'indice esiste**
- Causa: funzione applicata alla colonna, tipo diverso, `LIKE '%…'`, oppure la tabella è così piccola che la scansione è più veloce
- Fix: indice sull'espressione; allineare i tipi; su tabelle piccole non è un problema

**La pagina è lenta e il database dice che ogni query è veloce**
- Causa: N+1 — tante query rapide invece di una
- Fix: `log: ['query']` in sviluppo; `select`/`include`

**`too many connections`**
- Causa: pool per istanza moltiplicato per il numero di istanze, o connessioni non chiuse
- Fix: ridurre `connection_limit`; PgBouncer; `$disconnect()` sullo spegnimento

**Una migrazione resta appesa e il servizio si blocca**
- Causa: l'`ALTER TABLE` aspetta un lock, e tutto il resto si accoda dietro
- Fix: `lock_timeout` prima della migrazione; trovare il blocco in `pg_stat_activity`

**`deadlock detected`**
- Causa: due transazioni bloccano le stesse righe in ordine opposto
- Fix: acquisire i lock sempre nello stesso ordine (per esempio per id); transazioni più corte

**Il saldo o la giacenza vanno in negativo sotto carico**
- Causa: lost update — lettura e scrittura separate
- Fix: `UPDATE … WHERE giacenza >= n` controllando le righe aggiornate, oppure `FOR UPDATE`

**`could not serialize access due to concurrent update` (40001)**
- Causa: conflitto in `REPEATABLE READ` o `SERIALIZABLE`
- Fix: è previsto — l'applicazione deve riprovare la transazione con backoff

**I dati mostrati sono vecchi**
- Causa: cache non invalidata alla scrittura, o lettura da una replica in ritardo
- Fix: invalidare accanto alla scrittura; leggere dal primario dopo una scrittura

**Prisma solleva un errore su un vincolo che lo schema non mostra**
- Causa: il database ha vincoli o trigger creati a mano che Prisma non conosce
- Fix: `prisma migrate diff` per vedere la divergenza; portare tutto nelle migrazioni

---
## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_13_autenticazione_autorizzazione.md` | Dove finiscono utenti, sessioni e password; hash e refresh token |
| `tutorial_14_sicurezza_web.md` | SQL injection, esposizione dei dati, cifratura a riposo |
| `tutorial_15_testing_web.md` | Testcontainers, fixture e isolamento fra test in profondità |
| `tutorial_17_performance_web.md` | Dove il database entra nel budget di latenza della pagina |
| `tutorial_19_troubleshooting.md` | Diagnosi in produzione: query lente, lock, saturazione |
| `tutorial_24_graphql.md` | Il problema N+1 nella sua forma più acuta, e DataLoader |

---

## Risorse di riferimento

**Documentazione:** [PostgreSQL — Manuale](https://www.postgresql.org/docs/current/), in particolare *Indexes*, *Concurrency Control* e *Performance Tips* · [Prisma](https://www.prisma.io/docs) · [Redis — Data types](https://redis.io/docs/latest/develop/data-types/)

**Approfondimenti:** [Use The Index, Luke](https://use-the-index-luke.com/), il testo di riferimento sugli indici, con esempi per ogni database · [PostgreSQL Wiki — Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This), l'elenco degli errori ricorrenti con la spiegazione · [Postgres Weekly](https://postgresweekly.com/)

**Strumenti:** [pgAdmin](https://www.pgadmin.org/) e [DBeaver](https://dbeaver.io/) per l'ispezione · [explain.dalibo.com](https://explain.dalibo.com/) per visualizzare un piano · [pgbench](https://www.postgresql.org/docs/current/pgbench.html) per il carico · [Testcontainers](https://node.testcontainers.org/)

---

> **Fine del Tutorial 12 — Database per il Web**
>
> Prossimo tutorial: `tutorial_13_autenticazione_autorizzazione.md`
