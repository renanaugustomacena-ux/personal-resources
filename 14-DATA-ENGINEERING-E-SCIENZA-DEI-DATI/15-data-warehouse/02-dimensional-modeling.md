# Modellazione Dimensionale

La modellazione dimensionale è la disciplina di progettazione dello schema del data warehouse. Fu sistematizzata da Ralph Kimball nel suo libro "The Data Warehouse Toolkit" (1996). I suoi principi fondamentali sono rimasti validi nonostante le evoluzioni tecnologiche: i pattern cambiano (columnar storage, lakehouse), ma il modo di pensare al dato analitico rimane lo stesso.

Il principio centrale è: i dati analitici si organizzano attorno a **processi aziendali** (eventi misurabili) e al **contesto** di questi eventi. Le fact tables catturano gli eventi; le dimension tables forniscono il contesto.

## Quattro Passi della Progettazione Dimensionale

Kimball descrive quattro passi per progettare ogni data mart:

**Passo 1: Identificare il processo aziendale**
Non la tabella, non il sistema, ma il processo. "Vendite", "Acquisti", "Chiamate al call center", "Clic su banner", "Prescrizioni mediche". Un processo = una fact table.

**Passo 2: Dichiarare la granularità**
A che livello di dettaglio si rappresenta il fatto? "Una riga per ogni linea d'ordine", "Una riga per ogni giorno e prodotto", "Una riga per ogni clic". La granularità deve essere dichiarata esplicitamente e non cambiare.

**Passo 3: Identificare le dimensioni**
Per ogni fatto alla granularità scelta, chi/cosa/quando/dove/come/perché? Le risposte sono le dimensioni.

**Passo 4: Identificare le misure**
Cosa si misura per ogni fatto alla granularità scelta? Le misure devono essere coerenti con la granularità (non si può sommare una misura che non è additiva alla granularità).

## Tipi di Misure nelle Fact Tables

```sql
-- Le misure si classificano per additività

-- ADDITIVE: possono essere sommate lungo tutte le dimensioni
-- Esempio: revenue, quantity, cost
SELECT
  d.year,
  p.category,
  SUM(f.net_revenue) AS total_revenue  -- additive: ha senso sommare per anno E per categoria
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY d.year, p.category;

-- SEMI-ADDITIVE: possono essere sommate lungo alcune dimensioni ma non altre
-- Esempio: saldo conto corrente (può essere sommato per cliente, NON per tempo)
-- La somma dei saldi di gennaio + febbraio non ha senso (è il saldo di febbraio che conta)
CREATE TABLE fact_account_balance (
  date_key          INT NOT NULL,
  account_key       INT NOT NULL,
  customer_key      INT NOT NULL,
  closing_balance   NUMERIC(15,2),   -- semi-additive
  transaction_count INT,             -- additive
  PRIMARY KEY (date_key, account_key)
);

-- Query corretta per saldo: usare l'ultimo giorno disponibile (non SUM)
SELECT
  c.name,
  f.closing_balance  -- non SUM: prendiamo il saldo più recente
FROM fact_account_balance f
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE f.date_key = (
  SELECT MAX(date_key)
  FROM fact_account_balance
  WHERE account_key = f.account_key
);

-- NON ADDITIVE: non hanno senso sommate in nessun modo
-- Esempio: percentuale, ratio, prezzi unitari
-- Vanno calcolate al momento della query, non pre-aggregate
SELECT
  p.category,
  SUM(f.net_revenue) / NULLIF(SUM(f.quantity), 0) AS avg_unit_revenue  -- calculato
  -- NON pre-aggregare avg_unit_revenue nella fact table
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category;
```

## Fact Tables Senza Misure (Factless Fact Tables)

Esistono processi aziendali dove l'evento stesso è la misura: la presenza o assenza dell'evento.

```sql
-- Fact table per la copertura: quali prodotti erano disponibili in quali negozi in quali date
-- Nessuna misura: l'esistenza della riga dice che il prodotto era disponibile
CREATE TABLE fact_product_availability (
  date_key     INT NOT NULL REFERENCES dim_date(date_key),
  product_key  INT NOT NULL REFERENCES dim_product(product_key),
  store_key    INT NOT NULL REFERENCES dim_store(store_key),
  PRIMARY KEY (date_key, product_key, store_key)
);

-- Query: prodotti disponibili vs venduti (coverage analysis)
-- Quanti prodotti disponibili NON sono stati venduti oggi?
SELECT
  a.product_key,
  p.product_name,
  COALESCE(s.quantity_sold, 0) AS quantity_sold,
  CASE WHEN s.product_key IS NULL THEN 'Not Sold' ELSE 'Sold' END AS status
FROM fact_product_availability a
JOIN dim_product p ON a.product_key = p.product_key
LEFT JOIN (
  SELECT product_key, SUM(quantity) AS quantity_sold
  FROM fact_sales
  WHERE date_key = 20240115
  GROUP BY product_key
) s ON a.product_key = s.product_key
WHERE a.date_key = 20240115
  AND a.store_key = 42;

-- Fact table per gli eventi: accessi al sito web
-- COUNT(*) = numero di accessi, non servono misure esplicite
CREATE TABLE fact_web_sessions (
  date_key      INT NOT NULL,
  hour_key      INT NOT NULL,    -- dimension ora del giorno
  user_key      INT NOT NULL,
  page_key      INT NOT NULL,
  channel_key   INT NOT NULL,
  session_id    VARCHAR(50),     -- chiave degenerata
  PRIMARY KEY (date_key, hour_key, user_key, page_key, session_id)
);
```

## Slowly Changing Dimensions: Tutti i Tipi

```sql
-- SCD Tipo 0: immutabile (alcune dimension non cambiano mai)
-- Esempio: dim_date, dim_postal_code, codici prodotto legacy
CREATE TABLE dim_fiscal_period (
  period_key    INT PRIMARY KEY,
  period_code   CHAR(7),    -- 'FY2024Q1'
  start_date    DATE,
  end_date      DATE
  -- Non cambia mai: i periodi fiscali sono immutabili retroattivamente
);

-- SCD Tipo 1: overwrite (si sovrascrive, nessuna storia)
-- Usa: quando la storia non interessa o il cambiamento corregge un errore
UPDATE dim_customer
SET city = 'Milano', region = 'Lombardia'
WHERE customer_id = 'C001';
-- Semplice, ma dopo non si sa dove viveva prima

-- SCD Tipo 2: row versioning (storia completa)
-- Ogni cambiamento aggiunge una riga; la riga corrente ha is_current=TRUE
-- Usa: quando la storia è importante per l'analisi

-- Procedura per aggiornare un cliente con SCD2
CREATE OR REPLACE PROCEDURE scd2_update_customer(
  p_customer_id VARCHAR,
  p_new_city VARCHAR,
  p_new_region VARCHAR,
  p_effective_date DATE DEFAULT CURRENT_DATE
) LANGUAGE plpgsql AS $$
DECLARE
  v_current_key INT;
BEGIN
  -- 1. Trovare la riga corrente
  SELECT customer_key INTO v_current_key
  FROM dim_customer
  WHERE customer_id = p_customer_id AND is_current = TRUE;
  
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Cliente % non trovato', p_customer_id;
  END IF;
  
  -- 2. Chiudere la riga corrente
  UPDATE dim_customer
  SET is_current = FALSE,
      effective_to = p_effective_date - 1
  WHERE customer_key = v_current_key;
  
  -- 3. Inserire la nuova riga
  INSERT INTO dim_customer (
    customer_id, name, email, city, region, country,
    segment, acquisition_channel, is_current, effective_from, effective_to
  )
  SELECT
    customer_id, name, email,
    p_new_city, p_new_region,  -- aggiornati
    country, segment, acquisition_channel,
    TRUE,          -- is_current
    p_effective_date,
    NULL           -- open-ended
  FROM dim_customer
  WHERE customer_key = v_current_key;
END;
$$;

-- SCD Tipo 3: attributo aggiuntivo (mantieni il valore precedente come colonna separata)
-- Usa: quando si vuole confrontare "prima" e "dopo" senza la complessità del SCD2
ALTER TABLE dim_customer ADD COLUMN previous_city VARCHAR(100);
ALTER TABLE dim_customer ADD COLUMN city_changed_date DATE;

UPDATE dim_customer
SET
  previous_city = city,         -- salva il vecchio valore
  city = 'Milano',
  city_changed_date = CURRENT_DATE
WHERE customer_id = 'C001';

-- Query: clienti che si sono spostati negli ultimi 6 mesi
SELECT name, previous_city, city, city_changed_date
FROM dim_customer
WHERE city_changed_date > CURRENT_DATE - INTERVAL '6 months'
  AND previous_city != city;

-- SCD Tipo 4: tabella mini-dimension (per attributi che cambiano molto frequentemente)
-- Problema SCD2: se un attributo cambia ogni giorno (es. credit score), genera milioni di righe
-- Soluzione: spostare gli attributi volatili in una dimension separata

CREATE TABLE dim_customer_demographics (
  demographics_key    INT PRIMARY KEY,
  income_band         VARCHAR(20),    -- 'Low', 'Medium', 'High'
  credit_score_band   VARCHAR(20),    -- 'Poor', 'Fair', 'Good', 'Excellent'
  age_band            VARCHAR(20),    -- '18-25', '26-35', etc.
  effective_date      DATE
);

-- La fact table riferisce sia dim_customer (stabile) che dim_customer_demographics (volatile)
CREATE TABLE fact_sales_v2 (
  date_key            INT NOT NULL,
  customer_key        INT NOT NULL,       -- riferisce dim_customer (SCD2)
  demographics_key    INT NOT NULL,       -- riferisce dim_customer_demographics
  product_key         INT NOT NULL,
  net_revenue         NUMERIC(12,2),
  PRIMARY KEY (date_key, customer_key, demographics_key, product_key)
);
```

## Conformed Dimensions: Il Bus Matrix

Il concetto di "conformed dimension" (dimensione conforme) di Kimball permette di integrare fact tables diverse usando le stesse dimensioni, abilitando analisi cross-process.

```sql
-- dim_date è una conformed dimension: usata da TUTTE le fact tables
-- Questo permette di unire dati di vendite con dati di ordini per la stessa data

-- Bus Matrix: quale dimension è usata da quale fact table
-- 
--                    dim_date  dim_customer  dim_product  dim_channel  dim_store
-- fact_sales            X          X             X            X
-- fact_orders           X          X             X            X
-- fact_returns          X          X             X                        
-- fact_inventory        X                        X                         X
-- fact_web_sessions     X          X                          X

-- Query cross-process: vendite vs resi per prodotto e mese
WITH sales AS (
  SELECT d.year, d.month_number, p.product_name,
         SUM(f.net_revenue) AS revenue, SUM(f.quantity) AS units_sold
  FROM fact_sales f
  JOIN dim_date d ON f.date_key = d.date_key
  JOIN dim_product p ON f.product_key = p.product_key
  WHERE d.year = 2024
  GROUP BY d.year, d.month_number, p.product_name
),
returns AS (
  SELECT d.year, d.month_number, p.product_name,
         COUNT(*) AS return_count, SUM(r.refund_amount) AS refund_total
  FROM fact_returns r
  JOIN dim_date d ON r.date_key = d.date_key
  JOIN dim_product p ON r.product_key = p.product_key
  WHERE d.year = 2024
  GROUP BY d.year, d.month_number, p.product_name
)
SELECT
  s.year,
  s.month_number,
  s.product_name,
  s.revenue,
  s.units_sold,
  COALESCE(r.return_count, 0) AS returns,
  COALESCE(r.refund_total, 0) AS refunds,
  COALESCE(r.return_count, 0) * 100.0 / NULLIF(s.units_sold, 0) AS return_rate_pct
FROM sales s
LEFT JOIN returns r USING (year, month_number, product_name)
ORDER BY s.year, s.month_number, return_rate_pct DESC;
```

## Tecniche di Aggregazione Pre-Calcolata

Le aggregate tables (o summary tables) pre-calcolano aggregazioni frequenti per accelerare le query.

```sql
-- Aggregato giornaliero per prodotto (riduce la granularità della fact table)
CREATE TABLE agg_daily_product_sales AS
SELECT
  date_key,
  product_key,
  SUM(quantity)     AS total_quantity,
  SUM(net_revenue)  AS total_revenue,
  COUNT(*)          AS transaction_count,
  COUNT(DISTINCT customer_key) AS unique_customers
FROM fact_sales
GROUP BY date_key, product_key;

-- Indici per navigazione BI
CREATE INDEX ON agg_daily_product_sales(date_key);
CREATE INDEX ON agg_daily_product_sales(product_key);

-- Refreshare l'aggregato (in produzione: job incrementale)
-- Cancellare e ricalcolare per la data ieri
DELETE FROM agg_daily_product_sales
WHERE date_key = TO_CHAR(CURRENT_DATE - 1, 'YYYYMMDD')::INT;

INSERT INTO agg_daily_product_sales
SELECT
  date_key, product_key,
  SUM(quantity), SUM(net_revenue), COUNT(*), COUNT(DISTINCT customer_key)
FROM fact_sales
WHERE date_key = TO_CHAR(CURRENT_DATE - 1, 'YYYYMMDD')::INT
GROUP BY date_key, product_key;
```

## Junk Dimensions

Una junk dimension raccoglie attributi di bassa cardinalità che non appartengono a nessuna dimensione principale. Invece di aggiungere decine di colonne alla fact table, si crea una dimension che le raggruppa.

```sql
-- Senza junk dimension: molte colonne boolean/flag nella fact
-- fact_sales.is_promotional, is_gift_wrap, is_express_shipping, payment_type...

-- Con junk dimension: una singola FK alla tabella delle combinazioni
CREATE TABLE dim_sales_flags (
  flags_key         INT PRIMARY KEY,
  is_promotional    BOOLEAN,
  is_gift_wrap      BOOLEAN,
  is_express        BOOLEAN,
  payment_type      VARCHAR(20),  -- 'Credit', 'Debit', 'PayPal', 'Cash'
  UNIQUE (is_promotional, is_gift_wrap, is_express, payment_type)
);

-- Pre-popolare tutte le combinazioni possibili
INSERT INTO dim_sales_flags (is_promotional, is_gift_wrap, is_express, payment_type)
SELECT * FROM
  (VALUES (true), (false)) t1(is_promotional)
  CROSS JOIN (VALUES (true), (false)) t2(is_gift_wrap)
  CROSS JOIN (VALUES (true), (false)) t3(is_express)
  CROSS JOIN (VALUES ('Credit'), ('Debit'), ('PayPal'), ('Cash')) t4(payment_type);
-- 2×2×2×4 = 32 righe, molto gestibile

-- La fact table ora ha solo flags_key invece di 4 colonne separate
-- fact_sales.flags_key INT NOT NULL REFERENCES dim_sales_flags(flags_key)
```

