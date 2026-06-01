# Algebra Relazionale: Fondamenti e Operatori

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 1.0.0  
> Stato: draft

## Skip list
- [ ] Bozza iniziale
- [ ] Review tecnica
- [ ] Review security
- [ ] Formattazione
- [ ] Proofreading
- [ ] Pubblicazione

## Indice
1. Introduzione all'Algebra Relazionale
2. Operatori Fundamentali (Selection, Projection, Union, Set)
3. Operatori Derivati e Join
4. Operazioni di Raggruppamento e Aggregazione
5. Operatori di Divisione e Quoziente
6. Equivalenza delle Espressioni Algebriche
7. Ottimizzazione delle Query attraverso Trasformazioni
8. Algebra Relazionale in SQL
9. Estensioni dell'Algebra Relazionale
10. Esercizi Pratici e Applicazioni

---

## 1. Introduzione all'Algebra Relazionale

### 1.1 Definizione e Significato

L'**algebra relazionale** è un linguaggio di query procedurale che fornisce la base teorica per i database relazionali. Sviluppata da Edgar Codd nel 1970 come parte del modello relazionale, essa definisce un insieme di operazioni che, applicate a relazioni (tabelle), producono nuove relazioni.

L'importanza dell'algebra relazionale risiede nella sua capacità di fornire una semantica formale per le query SQL, permettere l'ottimizzazione delle query attraverso trasformazioni algebriche, e offrire un framework teorico per comprendere cosa è possibile esprimere in un database relazionale.

A differenza del **calcolo relazionale**, che è un linguaggio dichiarativo che specifica cosa si desidera ottenere senza indicare il procedimento, l'algebra relazionale è procedurale: specifica esplicitamente la sequenza di operazioni da eseguire. Questa distinzione è analoga a quella tra assembly (procedurale) e linguaggi ad alto livello (dichiarativo).

L'algebra relazionale è **chiusa** rispetto alle sue operazioni: ogni operazione applicata a relazioni produce una relazione come risultato. Questa proprietà permette la composizione: il risultato di un'operazione può essere l'input di un'altra, creando catene arbitrarie di operazioni.

### 1.2 Notazione e Convenzioni

La **notazione matematica** dell'algebra relazionale utilizza simboli greci per rappresentare gli operatori:

- **σ** (sigma): selezione (selection)
- **π** (pi): proiezione (projection)
- **ρ** (rho): rinomina (rename)
- **⋈** (bowtie): join
- **∪** (union): unione
- **−** (minus): differenza
- **×** (times): prodotto cartesiano
- **∩** (cap): intersezione
- **÷** (divide): divisione

Le **relazioni** sono tipicamente indicate con lettere maiuscole (R, S, T) e gli attributi con lettere minuscole (a, b, c) o nomi espliciti.

Una **espressione algebrica** si legge tipicamente dall'interno verso l'esterno o dall'inizio alla fine, a seconda della notazione utilizzata. In notazione posizionale, σ_{cond}(R) indica di applicare la selezione alla relazione R con la condizione specificata.

La **precedenza degli operatori** (dalla più alta alla più bassa) è tipicamente: proiezione, selezione, prodotto cartesiano, join, intersezione, differenza, unione. Le parentesi possono modificare l'ordine di valutazione.

### 1.3 Base Teorica e Fondamenti Matematici

L'algebra relazionale si basa su solidi fondamenti matematici della **teoria degli insiemi** e della **logica del primo ordine**.

Le relazioni sono **insiemi** di tuple, il che implica:
- Nessun ordinamento implicito delle tuple
- Nessun elemento duplicato
- Appartenenza ben definita delle tuple

Le operazioni dell'algebra relazionale sono therefore operazioni insiemistiche: unione, intersezione, e differenza operano su insiemi di tuple. La selezione e la proiezione sono operazioni che trasformano insiemi.

La **logica del primo ordine** fornisce il formalismo per esprimere le condizioni di selezione. Le condizioni sono formule booleane che coinvolgono attributi, costanti, e operatori di comparazione (=, <, >, ≤, ≥, ≠) combinati con connettivi logici (∧, ∨, ¬).

L'**equivalenza espressiva** tra algebra relazionale e calcolo relazionale (dimostrata da Codd) garantisce che nessuno dei due formalismi sia "più potente" dell'altro: ogni query esprimibile in uno è esprimibile anche nell'altro. Questo risultato è fondamentale perché valida la completezza del modello relazionale.

### 1.4 Classificazione degli Operatori

Gli operatori dell'algebra relazionale si classificano in **operatori fondamentali** (primitive) e **operatori derivati** (definiti in termini dei primitive).

Gli **operatori fondamentali** (originali di Codd) sono sei:
1. Selezione (σ)
2. Proiezione (π)
3. Prodotto cartesiano (×)
4. Unione (∪)
5. Differenza (−)
6. Rinomina (ρ)

Questi sei operatori sono **sufficienti** per esprimere qualsiasi query relazionale. Tutti gli altri operatori possono essere definiti in termini di questi.

Gli **operatori derivati** sono quelli che possono essere espressi attraverso combinazioni degli operatori fondamentali. Tra questi troviamo:
- Intersezione (∩): R ∩ S = R − (R − S)
- Join naturale (⋈): R ⋈ S = π_{attributi}(σ_{condizioni}(R × S))
- Theta-join (⋈_θ): R ⋈_θ S = σ_{θ}(R × S)
- Divisione (÷): R ÷ S = π_{R-S}(R) − π_{R-S}((π_{R-S}(R) × S) − R)

La distinzione tra operatori fondamentali e derivati ha implicazioni pratiche: un sistema può implementare solo gli operatori fondamentali e derivare gli altri, oppure può implementare direttamente gli operatori più comuni per efficienza.

### 1.5 Relazioni e Schema

Ogni relazione ha uno **schema** che definisce la struttura: un insieme di attributi con i rispettivi domini. Lo schema di una relazione R si indica come R(A1, A2, ..., An).

Quando si applicano operazioni, lo schema del risultato segue regole specifiche:

La **selezione** mantiene lo stesso schema della relazione input: σ_{cond}(R) ha lo stesso schema di R.

La **proiezione** riduce lo schema: π_{A,B}(R) produce una relazione con attributi {A, B}.

Il **prodotto cartesiano** combina gli schemi: R(A, B) × S(C, D) produce una relazione con schema (A, B, C, D). In caso di attributi con lo stesso nome, si usa la qualificazione (R.A, S.A).

Il **join** produce uno schema che è l'unione degli schemi delle due relazioni: R(A, B) ⋈ S(B, C) produce (A, R.B, S.B, C). Il join naturale unisce attributi con lo stesso nome.

---

## 2. Operatori Fondamentali

### 2.1 Selezione (σ - Selection)

L'operatore di **selezione** (σ, sigma) filtra le tuple di una relazione basandosi su una condizione predicativa. È l'equivalente dell clausola WHERE in SQL.

**Definizione formale**: Data una relazione R e un predicato P, σ_P(R) = {t ∈ R | P(t) = true}

La selezione opera su **una singola relazione** e produce una relazione con lo **stesso schema** ma con un numero di tuple che soddisfano il predicato.

Il **predicato** può essere:
- **Semplice**: comparazioni come A = 5, B > 10, C <= '2024-01-01'
- **Composto**: combinazioni con operatori booleani (A = 1 ∧ B > 5) ∨ (C = 'active')

Gli **operatori di comparazione** disponibili includono:
- Uguaglianza: =
- Disuguaglianza: ≠
- Minore, maggiore: <, >
- Minore o uguale, maggiore o uguale: ≤, ≥

La selezione è **idempotente**: σ_P(σ_P(R)) = σ_P(R). Applicare la stessa selezione due volte è equivalente ad applicarla una volta.

La selezione è **commutativa**: σ_P(σ_Q(R)) = σ_Q(σ_P(R)). L'ordine delle selezioni non importa.

**Esempio**: Data la relazione Impiegati(id, nome, stipendio, dipartimento), selezionare gli impiegati del dipartimento 'IT' con stipendio > 50000:

σ_{dipartimento='IT' ∧ stipendio>50000}(Impiegati)

### 2.2 Proiezione (π - Projection)

L'operatore di **proiezione** (π, pi) seleziona specifiche colonne di una relazione, scartando le altre. È l'equivalente della clausola SELECT in SQL.

**Definizione formale**: Data una relazione R con attributi A1, A2, ..., An e un sottoinsieme B = {Bi} di attributi, π_B(R) = {t[B] | t ∈ R}

La proiezione riduce il **grado** (numero di attributi) della relazione. Poiché le relazioni sono insiemi (senza duplicati), la proiezione può ridurre anche la **cardinalità** (numero di tuple) se ci sono duplicati.

La proiezione è **idempotente**: π_B(π_B(R)) = π_B(R).

La proiezione **non è commutativa** con la selezione in generale: π_A(σ_P(R)) ≠ σ_P(π_A(R)). L'ordine è importante perché la selezione può far perdere tuple che sarebbero state incluse dopo la proiezione.

**Esempio**: Dalla relazione Impiegati, ottenere solo i nomi e gli stipendi:

π_{nome,stipendio}(Impiegati)

Se si proietta su un sottoinsieme che contiene una chiave, il numero di tuple rimane uguale perché ogni valore della chiave è unico. Se si proietta su attributi non chiave, i duplicati vengono rimossi.

### 2.3 Prodotto Cartesiano (× - Cartesian Product)

Il **prodotto cartesiano** (×) combina due relazioni generando tutte le possibili combinazioni di tuple. È l'operatore fondamentale per costruire join.

**Definizione formale**: Date due relazioni R con schema (A1, A2, ..., An) e S con schema (B1, B2, ..., Bm), R × S produce una relazione con schema (A1, A2, ..., An, B1, B2, ..., Bm) contenente ogni combinazione di tuple di R con tuple di S.

Se |R| = n tuple e |S| = m tuple, allora |R × S| = n × m tuple.

Il prodotto cartesiano **non è commutativo** in termini di schema, ma produce lo stesso insieme di tuple a meno della denominazione degli attributi: R × S ≠ S × R (schema diverso).

Il prodotto cartesiano può produrre **risultati molto grandi**. Una relazione di 1000 righe unita a una di 1000 righe produce un milione di righe. Per questo, nella pratica, il prodotto cartesiano è quasi sempre seguito da una selezione per filtrare le combinazioni rilevanti.

**Esempio**: Combinare la tabella Impiegati con la tabella Dipartimenti:

Impiegati × Dipartimenti

Questo produce una relazione dove ogni impiegato è combinato con ogni dipartimento. La selezione successiva filtra solo le combinazioni dove l'impiegato appartiene al dipartimento (impiegati.dipartimento_id = dipartimenti.id).

### 2.4 Unione, Differenza e Intersezione (∪, −, ∩)

Gli operatori **set-theoretic** operano su due relazioni come insiemi di tuple.

L'**unione** (∪) combina le tuple di due relazioni:

R ∪ S = {t | t ∈ R ∨ t ∈ S}

Le due relazioni devono essere **compatibili in unione** (union-compatible): avere lo stesso numero di attributi e domini corrispondenti. Questo significa che gli attributi corrispondenti devono avere domini comparabili.

L'unione **rimuove i duplicati** perché opera su insiemi.

La **differenza** (−) produce le tuple della prima relazione che non sono nella seconda:

R − S = {t | t ∈ R ∧ t ∉ S}

Anche la differenza richiede relazioni compatibili in unione.

L'**intersezione** (∩) produce le tuple comuni a entrambe le relazioni:

R ∩ S = {t | t ∈ R ∧ t ∈ S}

L'intersezione può essere derivata: R ∩ S = R − (R − S)

L'unione è **commutativa**: R ∪ S = S ∪ R

La differenza **non è commutativa**: R − S ≠ S − R

**Esempio**: Ottenere i clienti che hanno effettuato ordini oppure hanno account attivi (senza duplicati):

Clienti_ordini ∪ Clienti_attivi

Ottenere i clienti che hanno effettuato ordini ma non hanno account attivi:

Clienti_ordini − Clienti_attivi

### 2.5 Rinomina (ρ - Rename)

L'operatore di **rinomina** (ρ, rho) permette di modificare i nomi degli attributi e delle relazioni. È essenziale per disambiguare e per permettere auto-join.

**Definizione formale**: ρ_{nuovo_nome/nuovi_attributi}(R) produce una relazione identica a R ma con nomi diversi.

La rinomina può operare su:
- Il nome della relazione: ρ_S(R) rinomina R in S
- Gli attributi: ρ_{(A1, A2, ...)}(R) rinomina gli attributi di R
- Entrambi: ρ_{S(A1, A2, ...)}(R)

La rinomina è **idempotente**: applicarla due volte con lo stesso risultato è equivalente ad applicarla una volta.

La rinomina è necessaria per:
- **Auto-join**: unire una relazione con se stessa richiede rinomina per distinguere le due istanze
- **Disambiguazione**: quando attributi di diverse relazioni hanno lo stesso nome
- **Proiezione con calcoli**: quando si rinominano colonne risultanti da espressioni

**Esempio**: Ottenere i dipendenti che guadagnano più dei loro manager (auto-join):

π_{impiegato.nome, impiegato.stipendio}(
    σ_{impiegato.stipendio > manager.stipendio}(
        Impiegati × ρ_{manager}(Impiegati)
    )
)

In questo caso, si crea una copia della tabella Impiegati rinominata "manager" per poter confrontare ogni impiegato con il proprio manager.

---

## 3. Operatori Derivati e Join

### 3.1 Theta-Join e Equi-Join

Il **theta-join** (⋈_θ) è un operatore derivato che combina prodotto cartesiano e selezione. Specifica una condizione di join θ che filtra le tuple del prodotto cartesiano.

**Definizione formale**: R ⋈_θ S = σ_θ(R × S)

Il theta-join è molto più efficiente del prodotto cartesiano seguito da selezione perché il sistema può filtrare durante la generazione del prodotto, riducendo la memoria necessaria.

L'**equi-join** è un caso speciale dove la condizione θ è una uguaglianza:

R ⋈_{A=B} S = σ_{R.A = S.B}(R × S)

L'equi-join è il tipo di join più comune nella pratica.

**Esempio**: Unire Impiegati con Dipartimenti dove l'ID del dipartimento corrisponde:

Impiegati ⋈_{impiegati.dipartimento_id = dipartimenti.id} Dipartimenti

In termini di algebra relazionale: σ_{impiegati.dipartimento_id = dipartimenti.id}(Impiegati × Dipartimenti)

Il risultato ha attributi di entrambe le relazioni, con potenziali duplicati (la colonna del dipartimento appare due volte, con due nomi diversi).

### 3.2 Natural Join e Outer Join

Il **natural join** (⋈) è un join dove la condizione è l'uguaglianza su tutti gli attributi con lo stesso nome nelle due relazioni. È un'operazione molto comune.

**Definizione formale**: R ⋈ S unisce le tuple dove tutti gli attributi con lo stesso nome hanno valori uguali. Il risultato ha una sola copia degli attributi comuni.

Se R(A, B, C) e S(A, D, E), allora R ⋈ S produce una relazione con attributi (A, B, C, D, E), dove le tuple sono combinate dove R.A = S.A.

Il natural join è equivalente a:
1. Prodotto cartesiano R × S
2. Selezione con uguaglianza su tutti gli attributi comuni
3. Proiezione che rimuove una copia degli attributi duplicati

Il natural join può produrre zero tuple se non ci sono valori comuni.

Gli **outer join** estendono il join per includere tuple che non hanno match:

- **Left outer join** (R ⟕ S): include tutte le tuple di R, con NULL per gli attributi di S dove non c'è match
- **Right outer join** (R ⟖ S): include tutte le tuple di S, con NULL per gli attributi di R dove non c'è match
- **Full outer join** (R ⟗ S): include tutte le tuple di entrambe le relazioni

Gli outer join sono **derivati** nel modello base ma sono implementati nella maggior parte dei DBMS:

R ⟕ S = (R ⋈ S) ∪ (R − π_{R}(R ⋈ S)) con attributi di S impostati a NULL

### 3.3 Semi-Join e Anti-Join

Il **semi-join** (⋉, ⋊) è un join che mantiene solo le tuple della prima relazione che hanno un match nella seconda. È utile per query che verificano l'esistenza senza necessitare i dati della seconda relazione.

Il **semi-join sinistro**: R ⋉ S = π_R(R ⋈ S)

Il semi-join sinistro produce le tuple di R che soddisfano la condizione di join, ma include solo gli attributi di R.

Il **anti-join** (▷) è il complementare: mantiene le tuple della prima relazione che **non** hanno match nella seconda.

Il left anti-join: R ▷ S = R − π_R(R ⋈ S)

Gli anti-join sono particolarmente utili per:
- "Trova i clienti che non hanno mai ordinato"
- "Trova i prodotti mai venduti"
- Query "NOT EXISTS" in SQL

**Esempio**: Trovare i clienti che non hanno mai effettuato ordini:

Clienti ▷ Ordini

Equivalente in termini di algebra: Clienti − π_{Clienti}(Clienti ⋈_{Clienti.id = Ordini.cliente_id} Ordini)

### 3.4 Join Multipli e Catene di Join

Nelle query reali, spesso si uniscono più di due relazioni. L'algebra relazionale supporta questo attraverso la composizione:

R ⋈ S ⋈ T = (R ⋈ S) ⋈ T

L'ordine di applicazione dei join influenza le prestazioni (e talvolta il risultato in presenza di outer join).

Le **catene di join** possono essere ottimizzate considerando:
- **Selettività**: applicare prima i join che ridurranno maggiormente il numero di tuple
- **Ordine delle tabelle**: in join a catena, l'ordine influenza la dimensione dei risultati intermedi
- **Join algorithms**: diversi algoritmi sono più efficienti per diversi pattern

**Esempio**: Unire clienti, ordini, e prodotti per ottenere il dettaglio degli ordini:

π_{cliente.nome, ordine.data, prodotto.nome}(
    Clienti ⋈_{Clienti.id = Ordini.cliente_id} Ordini ⋈_{Ordine.id = Dettaglio.ordine_id} Dettaglio ⋈_{Dettaglio.prodotto_id = Prodotto.id} Prodotto
)

### 3.5 Join con Condizioni Complesse

Le condizioni di join possono essere più complesse di semplici uguaglianze:

**Join con multiple condizioni**: R ⋈_{A = B ∧ C > D ∧ E LIKE 'X%'} S

**Join con subquery**: R ⋈_{A IN (SELECT ...)} S (richiede estensioni dell'algebra base)

**Self-join con condizioni**: Unire una tabella con se stessa con condizioni specifiche richiede rinomina:

Impiegati ⋈_{Impiegati.manager_id = Manager.id} ρ_{Manager}(Impiegati)

Le **condizioni di join complesse** sono utili per:
- Range join (date range che si sovrappongono)
- Fuzzy join (similarità)
- Spatial join (intersezioni geometriche)

Questi tipi di join richiedono estensioni dell'algebra relazionale base o implementazioni specifiche nei DBMS.

---

## 4. Operazioni di Raggruppamento e Aggregazione

### 4.1 Operatore di Gruppo (γ - Group)

L'operatore di **gruppo** (γ, gamma) raggruppa le tuple basandosi su uno o più attributi e calcola funzioni di aggregazione su ciascun gruppo.

**Definizione formale**: γ_{attributi_di_gruppo, funzioni_di_aggregazione}(R)

La semantica è:
1. Partiziona le tuple di R in gruppi basandosi sugli attributi di raggruppamento
2. Per ogni gruppo, calcola le funzioni di aggregazione specificate
3. Produce una tuple per ogni gruppo con gli attributi di raggruppamento e i risultati delle aggregazioni

**Esempio**: Per ogni dipartimento, calcolare la somma degli stipendi:

γ_{dipartimento, SUM(stipendio) → totale}(Impiegati)

Questo produce una relazione con attributi (dipartimento, totale).

### 4.2 Funzioni di Aggregazione

Le **funzioni di aggregazione** calcolano valori su insiemi di tuple:

- **COUNT(*)**: conta tutte le tuple nel gruppo
- **COUNT(A)**: conta i valori non-NULL dell'attributo A
- **SUM(A)**: somma i valori dell'attributo A
- **AVG(A)**: media dei valori dell'attributo A
- **MIN(A)**: valore minimo dell'attributo A
- **MAX(A)**: valore massimo dell'attributo A

Alcune di queste funzioni possono essere espresse in algebra relazionale base attraverso operazioni di divisione e proiezione, ma la loro implementazione diretta è più efficiente.

La **cardinalità del gruppo** (COUNT) può essere derivata:
COUNT(*) = |γ_{}(R)| (numero di gruppi totali)

**Esempio**: Ottenere il conteggio, la somma, la media, il minimo e il massimo degli stipendi per ogni dipartimento:

γ_{dipartimento, COUNT(*) → cnt, SUM(stipendio) → somma, AVG(stipendio) → media, MIN(stipendio) → minimo, MAX(stipendio) → massimo}(Impiegati)

### 4.3 Aggregazione su Intere Relazioni

L'aggregazione può operare sull'intera relazione senza raggruppamento:

γ_{COUNT(*) → totali, SUM(stipendio) → massa_paghe}(Impiegati)

Questo produce una singola tuple con i valori aggregati su tutta la tabella.

In algebra relazionale pura, l'aggregazione può essere simulata:
- COUNT(*): π_{COUNT}(R) dove COUNT è un attributo derivato
- SUM: richiede operazioni più complesse

Per questo, l'algebra relazionale estesa include esplicitamente le funzioni di aggregazione.

### 4.4 Having e Filtro sui Gruppi

Il **filtro sui gruppi** (clausola HAVING in SQL) seleziona gruppi basati su condizioni che coinvolgono funzioni di aggregazione.

In algebra relazionale, questo si esprime come una selezione dopo il raggruppamento:

σ_{COUNT(*) > 5}(γ_{dipartimento, COUNT(*) → num_impiegati}(Impiegati))

**Esempio**: Trovare i dipartimenti con più di 10 impiegati e stipendio medio superiore a 50000:

σ_{conteggio > 10 ∧ media > 50000}(
    γ_{dipartimento, COUNT(*) → conteggio, AVG(stipendio) → media}(Impiegati)
)

### 4.5 Operatori Estatistici e Analitici

L'algebra relazionale estesa include operatori per **calcoli statistici**:

- **Median**: valore centrale di un insieme ordinato
- **Standard deviation**: deviazione standard
- **Variance**: varianza
- **Percentile**: valore in una posizione percentuale

Le **funzioni analitiche** (window functions in SQL) sono estensioni che calcolano valori relativi a una "finestra" di tuple:

- ROW_NUMBER(): numero sequenziale
- RANK(): rank con gap
- DENSE_RANK(): rank senza gap
- LAG(), LEAD(): valore precedente/successivo
- SUM, AVG, COUNT su finestra

In algebra, una window function può essere espressa con l'operatore ω:

ω_{PARTITION BY dept, ORDER BY date, SUM(salary) OVER ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW}(R)

---

## 5. Operatori di Divisione e Quoziente

### 5.1 Definizione della Divisione

L'operatore di **divisione** (÷) permette di rispondere a query del tipo "trova tutti gli X che sono associati a tutti gli Y". È l'operatore più complesso dell'algebra relazionale.

**Definizione formale**: Data una relazione R con schema (A, B) e una relazione S con schema (B), R ÷ S produce una relazione con schema (A) contenente le tuple a ∈ A tali che per ogni b ∈ S, la tuple (a, b) ∈ R.

In altre parole: R ÷ S = {a | ∀b ∈ S, (a, b) ∈ R}

**Esempio**: Trovare i clienti che hanno ordinato tutti i prodotti della categoria 'electronics':

(Ordini ⋈_{prodotto_id = prodotto.id} Prodotti) ÷ π_{prodotto}(σ_{categoria='electronics'}(Prodotti))

Il risultato è la lista dei clienti che hanno almeno un ordine per ogni prodotto nella categoria electronics.

### 5.2 Implementazione della Divisione

La divisione può essere **derivata** usando gli operatori fondamentali:

R ÷ S = π_A(R) − π_A((π_A(R) × S) − R)

Dove A è l'insieme degli attributi di R che non sono in S.

Questa formula dice:
1. Prendi tutti i valori possibili di A (π_A(R))
2. Genera tutte le coppie con S (π_A(R) × S)
3. Trova le coppie mancanti ((π_A(R) × S) − R)
4. Proietta sulle tuple mancanti (π_A(...))
5. Sottrai dal totale per ottenere i valori di A che hanno tutti i corrispondenti in S

### 5.3 Applicazioni Pratiche della Divisione

La divisione è utile per query che implicano "tutti" o "ogni":

- "Quali impiegati hanno lavorato su tutti i progetti?"
- "Quali studenti hanno completato tutti i corsi del programma?"
- "Quali negozi vendono tutti i prodotti di un fornitore?"

Queste query sono difficili da esprimere senza la divisione o costruzioni equivalenti come NOT EXISTS annidati.

**Esempio pratico**: Trovare i fornitori che forniscono tutti i componenti necessari per il prodotto X:

Componenti_Prodotto_X ÷ Fornitori_Componenti

Dove:
- Componenti_Prodotto_X = π_{componente}(σ_{prodotto='X'}(Produzione))
- Fornitori_Componenti = π_{fornitore, componente}(Forniture)

### 5.4 Divisione con Attributi Multipli

La divisione può essere estesa per relazioni con schema più complesso:

Se R(A, B, C) e S(B, C), allora R ÷ S ha schema (A) e contiene i valori di A che hanno come valore every coppia (B, C) in S.

In pratica, la divisione con attributi multipli funziona come la divisione semplice, dove l'insieme S è trattato come un'unità.

### 5.5 Quoziente Relazionale

Il **quoziente relazionale** è un altro nome per la divisione, riflettendo la sua natura matematica di operazione di quoziente insiemistico. Rappresenta l'operazione "per tutti" in modo elegante e teoricamente pulito.

Il nome "quoziente" deriva dall'analogia con la divisione numerica: se R(A, B) rappresenta la relazione "A è associato a B", R ÷ S rappresenta "A è associato a tutti gli elementi di S".

---

## 6. Equivalenza delle Espressioni Algebriche

### 6.1 Equivalenza e Leggi Algebriche

Due espressioni algebriche sono **equivalenti** se producono lo stesso risultato per qualsiasi istanza delle relazioni coinvolte. L'equivalenza è fondamentale per l'ottimizzazione delle query.

Le **leggi commutativi**:
- R × S = S × R
- R ⋈ S = S ⋈ R (per join simmetrici)
- R ∪ S = S ∪ R

Le **leggi associativi**:
- (R × S) × T = R × (S × T)
- (R ⋈ S) ⋈ T = R ⋈ (S ⋈ T)
- (R ∪ S) ∪ T = R ∪ (S ∪ T)

Le **leggi distributivi**:
- σ_P(R × S) = σ_P(R) × S (se P coinvolge solo attributi di R)
- π_A(R ⋈ S) = π_A(R) ⋈ S (se A include attributi per il join)
- σ_P(R ∪ S) = σ_P(R) ∪ σ_P(S)

### 6.2 Leggi della Selezione

La selezione ha proprietà importanti per l'ottimizzazione:

**Cascade**: σ_{P1 ∧ P2}(R) = σ_{P1}(σ_{P2}(R))

**Commutatività**: σ_{P}(σ_{Q}(R)) = σ_{Q}(σ_{P}(R))

**Proiezione di selezione**: π_A(σ_P(R)) = π_A(σ_P(π_{A ∨ attributi(P)}(R)))
(Questo significa che si può proiettare prima sugli attributi necessari per la selezione)

### 6.3 Leggi della Proiezione

La proiezione interagisce con altre operazioni:

**Cascade**: π_A(π_B(R)) = π_A(R) se A ⊆ B

**Proiezione di prodotto**: π_A(R × S) = π_A(R) × π_A(S) se A è partizionato tra attributi di R e S

**Proiezione di join**: π_A(R ⋈ S) = (π_{A_R}(R)) ⋈ (π_{A_S}(S)) se A è la combinazione degli attributi di join

### 6.4 Leggi del Join

Il join ha leggi che permettono trasformazioni:

**Associatività**: (R ⋈ S) ⋈ T = R ⋈ (S ⋈ T) (con join naturale)

**Commutatività con selezione**: σ_P(R) ⋈ S = σ_P(R ⋈ S) (se P referenzia solo attributi di R e S)

**Commutatività con proiezione**: π_A(R) ⋈ π_B(S) = π_{A∪B}(R ⋈ S)

### 6.5 Importanza per l'Ottimizzazione

L'equivalenza permette al **query optimizer** di trasformare le espressioni in forme più efficienti.

Un optimizer può:
- Spostare selezioni prima di join (selection pushdown)
- Spostare proiezioni prima di selezioni (projection pushdown)
- Riordinare join per ridurre la dimensione dei risultati intermedi
- Eliminare operazioni ridondanti

**Esempio di ottimizzazione**:
Query originale:
π_{nome}(σ_{stipendio > 50000}(Impiegati × Dipartimenti))

Ottimizzata:
π_{nome}(Impiegati ⋈_{Impiegati.dipartimento_id = Dipartimenti.id}(σ_{stipendio > 50000}(Impiegati) × Dipartimenti))

L'ottimizzazione esegue la selezione prima del prodotto cartesiano, riducendo drasticamente il numero di tuple.

---

## 7. Ottimizzazione delle Query attraverso Trasformazioni

### 7.1 Principi dell'Ottimizzazione

L'**ottimizzazione** delle query trasforma espressioni algebriche equivalenti in forme più efficienti. L'optimizer stima il costo di diverse forme e sceglie la minima.

I **principi chiave** dell'ottimizzazione sono:
1. **Ridurre presto**: applicare selezioni e proiezioni il prima possibile
2. **Ridurre i dati**: minimizzare la dimensione delle relazioni intermedie
3. **Riordinare**: scegliere l'ordine dei join che produce risultati più piccoli
4. **Eliminare**: rimuovere operazioni non necessarie

L'optimizer opera in fasi:
1. Parsing → algebra
2. Trasformazioni logicamente equivalenti
3. Stima dei costi per diversi piani
4. Scelta del piano a costo minimo

### 7.2 Selection Pushdown

Lo **selection pushdown** sposta le selezioni verso il basso dell'albero delle operazioni, eseguendole prima possibile.

Prima:
σ_{P}(R × S)

Dopo:
σ_{P}(R) × S (se P referenzia solo attributi di R)

Se P referenzia entrambi:
σ_{P1}(R) × σ_{P2}(S) (dove P = P1 ∧ P2, e P1 referenzia solo R, P2 solo S)

**Esempio**:
σ_{dipartimento='IT'}(Impiegati × Dipartimenti) = σ_{dipartimento='IT'}(Impiegati) × Dipartimenti

La selezione su Impiegati riduce drasticamente le tuple prima del join.

### 7.3 Projection Pushdown

La **projection pushdown** sposta le proiezioni verso il basso, riducendo le colonne processate.

Prima:
π_A(σ_P(R))

Dopo:
π_A(σ_P(π_{A∪attributi(P)}(R)))

Questo significa: proiettare prima sugli attributi necessari (quelli nel risultato finale e quelli usati nel predicato), poi applicare la selezione, poi la proiezione finale.

**Esempio**:
π_{nome}(σ_{stipendio > 50000}(Impiegati)) = π_{nome}(σ_{stipendio > 50000}(π_{nome,stipendio}(Impiegati)))

Si leggono solo due colonne (nome, stipendio) invece di tutte.

### 7.4 Join Reordering

Il **riordinamento dei join** è cruciale per le query multi-tabella. L'ordine influenza la dimensione dei risultati intermedi.

Per query con N tabelle, ci sono N! possibili ordini di join. L'optimizer usa:
- **Dynamic programming**: per piccoli N, considera tutti i sotto-problemi
- **Greedy heuristics**: unisci prima le tabelle più piccole
- **Cost-based exploration**: stima i costi e seleziona il minimo

**Esempio**: Query su Clienti (100 righe), Ordini (10000 righe), Dettagli (100000 righe):

Piano 1: ((Clienti ⋈ Ordini) ⋈ Dettagli)
- Clienti × Ordini → 100 × 10000 = 1M tuple, poi join con Dettagli

Piano 2: (Ordini ⋈ Dettagli) ⋈ Clienti
- Ordini × Dettagli → 10000 × 100000 = 1B tuple (troppo grande!)
- Meglio: prima filtrare Ordini per cliente specifico, poi join con Dettagli

L'optimizer sceglie il piano con il costo stimato minore.

### 7.5 Eliminazione di Operazioni Ridondanti

L'optimizer elimina operazioni che non cambiano il risultato:

- Selezioni sempre vere: σ_{true}(R) = R
- Selezioni sempre false: σ_{false}(R) = ∅
- Proiezioni che includono tutti gli attributi: π_{tutti}(R) = R
- Union con insieme vuoto: R ∪ ∅ = R
- Differenza con se stesso: R − R = ∅

Queste semplificazioni riducono il lavoro necessario.

---

## 8. Algebra Relazionale in SQL

### 8.1 Mapping Operatori SQL

SQL è l'implementazione pratica dell'algebra relazionale. Ogni operatore ha un equivalente SQL:

| Algebra | SQL |
|---------|-----|
| σ_P(R) | SELECT * FROM R WHERE P |
| π_A(R) | SELECT A FROM R |
| R × S | SELECT * FROM R, S |
| R ⋈ S | SELECT * FROM R JOIN S |
| R ⋈_{A=B} S | SELECT * FROM R JOIN S ON A = B |
| R − S | SELECT * FROM R WHERE NOT EXISTS (SELECT 1 FROM S ...) |
| R ∪ S | SELECT ... FROM R UNION SELECT ... FROM S |
| R ∩ S | SELECT ... FROM R INTERSECT SELECT ... FROM S |
| γ_{A,f(B)}(R) | SELECT A, f(B) FROM R GROUP BY A |

### 8.2 Subquery e Algebra

Le **subquery** in SQL corrispondono a espressioni algebriche annidate:

**IN** corrisponde al join:
SELECT * FROM R WHERE A IN (SELECT B FROM S)
≡ π_R(σ_{R.A = S.B}(R × S))

**EXISTS** corrisponde al semi-join:
SELECT * FROM R WHERE EXISTS (SELECT 1 FROM S WHERE R.A = S.B)
≡ π_R(R ⋉ S)

**NOT EXISTS** corrisponde all'anti-join:
SELECT * FROM R WHERE NOT EXISTS (...)
≡ R ▷ S

### 8.3 Window Functions

Le **window functions** estendono l'algebra con operazioni analitiche:

```sql
SELECT 
    nome,
    stipendio,
    AVG(stipendio) OVER (PARTITION BY dipartimento) as media_dipartimento,
    ROW_NUMBER() OVER (PARTITION BY dipartimento ORDER BY stipendio DESC) as rank
FROM impiegati
```

Equivale a:
γ_{dipartimento, nome, stipendio, AVG(stipendio) OVER(), ROW_NUMBER() OVER()}(Impiegati)

Le window functions calcolano valori su "finestre" di tuple senza ridurne il numero.

### 8.4 CTE (Common Table Expressions)

Le **CTE** sono espressioni algebriche con nome che possono essere riutilizzate:

```sql
WITH 
    impiegati_it AS (SELECT * FROM impiegati WHERE dipartimento = 'IT'),
    stipendi_elevati AS (SELECT * FROM impiegati_it WHERE stipendio > 50000)
SELECT * FROM stipendi_elevati;
```

Equivale a:
π_{stipendi_elevati}(σ_{stipendio>50000}(σ_{dipartimento='IT'}(Impiegati)))

Le CTE rendono le query complesse più leggibili e permettono riutilizzo.

### 8.5 Query Ricorsive (WITH RECURSIVE)

Le query ricorsive estendono l'algebra per gestire strutture gerarchiche:

```sql
WITH RECURSIVE org_chart AS (
    -- Base case: i manager (top della gerarchia)
    SELECT id, name, manager_id, 1 as level FROM employees WHERE manager_id IS NULL
    UNION ALL
    -- Recursive case: i subordinati
    SELECT e.id, e.name, e.manager_id, oc.level + 1
    FROM employees e
    JOIN org_chart oc ON e.manager_id = oc.id
)
SELECT * FROM org_chart;
```

Questo corrisponde alla chiusura transitiva della relazione manager-impiegato.

---

## 9. Estensioni dell'Algebra Relazionale

### 9.1 Algebra Relazionale con Null

L'introduzione dei **valori NULL** nell'algebra richiede estensioni per gestire la logica trivalente:

Le comparazioni con NULL non restituiscono TRUE né FALSE, ma UNKNOWN.

σ_{A = NULL}(R) non restituisce le tuple con A = NULL.

Servono operatori speciali:
- IS NULL: verifica la presenza di NULL
- IS NOT NULL: verifica l'assenza di NULL
- COALESCE: sostituisce NULL con un valore

Le aggregazioni ignorano i NULL (COUNT ignora, SUM somma solo non-NULL).

### 9.2 Algebra Relazionale Multimediale

Per **database multimediali** o con tipi complessi, l'algebra si estende:

- Operator per testo: LIKE, CONTAINS, MATCH
- Operator spaziali: INTERSECTS, WITHIN, DISTANCE
- Operator temporali: OVERLAPS, CONTAINS, PRECEDES

Questi operatori sono specifici del dominio e non sono parte dell'algebra relazionale base.

### 9.3 Algebra per Dati Temporali

L'algebra relazionale **temporal** gestisce dati con validità temporale:

Le **tabelle bitemporali** hanno due dimensioni temporali:
- Transaction time: quando il dato è stato registrato
- Valid time: quando il dato era valido nel mondo reale

Operatori temporali:
- **Temporal selection**: seleziona tuple attive in un certo periodo
- **Temporal join**: join basato su sovrapposizione di periodi
- **Temporal aggregation**: aggrega mantenendo la dimensione temporale

### 9.4 Algebra per Dati Probabilistici

I **database probabilistici** trattano dati con incertezza:

Le tuple hanno attributi con distribuzioni di probabilità invece di valori certi.

Operatori probabilistici:
- **Probabilistic selection**: seleziona basandosi su soglia di probabilità
- **Probabilistic join**: join con matching probabilistico
- **Aggregation under uncertainty**: calcola risultati con distribuzioni

### 9.5 Algebra Relazionale Distribuita

In **sistemi distribuiti**, l'algebra si estende per tenere conto della località dei dati:

- **Semi-join distribuito**: riduce trasferimento di dati
- **Join basato su frammentazione**: sfrutta la località
- **Aggregazione distribuita**: aggregazione in due fasi (map-reduce)

---

## 10. Esercizi Pratici e Applicazioni

### 10.1 Esercizi di Base

**Esercizio 1**: Data la tabella Studenti(id, nome, età, media), scrivere espressioni per:
- Selezionare studenti con media > 26
- Proiettare solo nome e media
- Selezionare studenti con età > 20 e media > 25

Soluzioni:
σ_{media > 26}(Studenti)
π_{nome,media}(Studenti)
σ_{età > 20 ∧ media > 25}(Studenti)

**Esercizio 2**: Date le tabelle Clienti(id, nome, città) e Ordini(id, cliente_id, data, totale), scrivere espressioni per:
- Tutti i clienti con i loro ordini
- Solo i clienti che hanno ordini
- Clienti senza ordini

Soluzioni:
Clienti × Ordini (prodotto cartesiano, poi filtrare)
Clienti ⋈ Clienti.id = Ordini.cliente_id Ordini (inner join)
Clienti ▷ Ordini (anti-join)

### 10.2 Esercizi di Join

**Esercizio**: Date le tabelle Impiegati(id, nome, manager_id, dipartimento_id), Dipartimenti(id, nome, budget), scrivere espressioni per:
- Ogni impiegato con il nome del suo manager
- Ogni impiegato con il nome del dipartimento
- Dipartimenti con più di 5 impiegati

Soluzioni:
π_{impiegato.nome, manager.nome}(Impiegati ⋈_{impiegati.manager_id = manager.id} ρ_{manager}(Impiegati))
π_{impiegato.nome, dipartimento.nome}(Impiegati ⋈ Impiegati.dipartimento_id = Dipartimenti.id Dipartimenti)
σ_{COUNT(*) > 5}(γ_{dipartimento_id, COUNT(*) → num}(Impiegati)) ⋈ Dipartimenti

### 10.3 Esercizi di Aggregazione

**Esercizio**: Per la tabella Vendite(id, prodotto, categoria, regione, quantità, prezzo), scrivere espressioni per:
- Totale vendite per regione
- Media vendite per categoria
- Top 3 prodotti per quantità venduta

Soluzioni:
γ_{regione, SUM(quantità * prezzo) → totale}(Vendite)
γ_{categoria, AVG(quantità * prezzo) → media}(Vendite)
π_{prodotto, quantità}(Vendite) ORDER BY quantità DESC LIMIT 3 (in SQL, non algebra pura)

### 10.4 Esercizi di Divisione

**Esercizio**: Date le tabelle Studenti(id, nome), Corsi(id, nome), Iscrizioni(studente_id, corso_id), scrivere espressioni per:
- Studenti iscritti a tutti i corsi
- Corsi a cui sono iscritti tutti gli studenti

Soluzioni:
Studenti ÷ π_{corso_id}(Iscrizioni) (studenti con tutti i corsi)
Corsi ÷ π_{studente_id}(Iscrizioni) (corsi con tutti gli studenti)

### 10.5 Query Complesse

**Esercizio**: Dato uno schema e-commerce:
- Clienti(id, nome, email)
- Ordini(id, cliente_id, data, stato)
- Prodotti(id, nome, categoria, prezzo)
- DettagliOrdine(ordine_id, prodotto_id, quantità)

Scrivere espressioni per:
1. Clienti con ordini in stato 'shipped' nel 2024
2. Per ogni categoria, la categoria con più ricavi
3. Prodotti mai venduti

Soluzioni:
1. π_{cliente.nome}(σ_{anno(data)=2024 ∧ stato='shipped'}(Clienti ⋈ Ordini ⋈ DettagliOrdine ⋈ Prodotti))
2. π_{categoria}(γ_{categoria, SUM(quantità*prezzo)→tot}(Prodotti ⋈ DettagliOrdine ⋈ Ordini)) ORDER BY tot DESC LIMIT 1
3. Prodotti ▷ (π_{prodotto_id}(DettagliOrdine))

---

## Appendice: Risorse e Riferimenti

### A.1 Libri Consigliati

- "Database System Concepts" - Silberschatz, Korth, Sudarshan
- "Foundations of Databases" - Abitei, Hull, Vianu
- "The Algebra of Relational Queries" - Selected Papers

### A.2 Esercizi Aggiuntivi

- SQLZoo: sqlzoo.net
- LeetCode Database Problems
- HackerRank SQL Practice

---

*Questo documento fa parte del modulo 01 "Basi Dati Relazionali" della Data Encyclopedia.*
*Per domande o correzioni, consultare il repository o contattare il team di documentazione.*