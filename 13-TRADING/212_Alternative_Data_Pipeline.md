# 212 — Alternative Data: Sourcing, Cleaning, and Alpha Extraction

> Practitioner reference for systematic use of alternative data in trading. Covers satellite, web scraping, credit card transactions, app usage, geolocation, NLP from filings/news/social, on-chain crypto data, ESG. Discusses data ingestion, point-in-time construction, signal decay, NLP pipelines, and integration with traditional models. Self-contained beyond document 200.

---

## Table of Contents

1. [Introduction — The Alt Data Landscape](#introduction)
2. [Taxonomy of Alt Data](#taxonomy)
3. [Satellite Imagery](#satellite)
4. [Web Scraping](#scraping)
5. [Credit Card Transactions](#credit-card)
6. [App Usage Data](#app-usage)
7. [Geolocation](#geolocation)
8. [B2B Transactions and Supply Chain](#b2b)
9. [Patent Data](#patents)
10. [Government and Regulatory Data](#government-data)
11. [News and Text Data](#news)
12. [Social Media](#social-media)
13. [Earnings Call Transcripts](#earnings-calls)
14. [Audio and Video Analytics](#audio-video)
15. [Onchain Crypto Data](#onchain)
16. [ESG Data](#esg)
17. [Data Ingestion Architecture](#ingestion)
18. [Point-in-Time Database Construction](#pit)
19. [Data Cleaning](#cleaning)
20. [Entity Resolution](#entity-resolution)
21. [Feature Engineering](#feature-engineering)
22. [Signal Decay Analysis](#signal-decay)
23. [Backtesting Alt Data Signals](#backtesting)
24. [Combining with Traditional Features](#combining)
25. [NLP Pipeline](#nlp-pipeline)
26. [Sentiment Scoring](#sentiment)
27. [Topic Modeling](#topic-modeling)
28. [Knowledge Graphs](#knowledge-graphs)
29. [Causal Inference](#causal)
30. [Privacy and Ethics](#privacy)
31. [Vendor Selection](#vendor)
32. [Cost-Benefit Analysis](#cost-benefit)
33. [Code Examples](#code)
34. [Case Studies](#case-studies)
35. [Reality Checks](#reality-checks)
36. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction — The Alt Data Landscape

Alternative data ("alt data") is data that is not traditional market or financial data — not prices, not earnings, not analyst forecasts. Examples: satellite images of parking lots, credit card transaction aggregates, app usage statistics, news sentiment, social media chatter, on-chain blockchain activity. The thesis is that alt data carries information about future returns *before* it's incorporated into prices through traditional channels.

The hedge fund industry's spend on alt data was estimated at $1B in 2018 and growing at 30%+ annually. Major fundamental long-short funds, quant equity firms, and macro hedge funds all maintain alt-data teams.

The alpha cycle is well-documented:
1. New data source emerges (e.g., parking lot satellites).
2. Early adopters extract alpha (~20-50bp/year for 1-3 years).
3. Vendor scales coverage; more buyers join.
4. Alpha decays toward zero as the signal becomes consensus.
5. Data becomes a "table stakes" input rather than alpha.

This life cycle motivates continuous innovation. The funds with edge are those who can identify, ingest, and operationalize new data sources before the rest of the market.

The challenges are different from traditional data: alt data is messier, has variable coverage, requires entity resolution to map to tradable instruments, has potential privacy and regulatory concerns, and often arrives in unstructured forms (text, images, geocoordinates).

This document covers the operational machinery — sourcing, cleaning, modeling, and integrating alt data into systematic trading. We assume basic familiarity with Python data science (pandas, numpy, scikit-learn) and quantitative trading concepts.

---

## Taxonomy of Alt Data

| Category | Examples | Typical Use |
|---|---|---|
| Satellite imagery | Parking lots, ship traffic, mining | Same-store sales, commodity supply |
| Web scraping | Pricing pages, job postings, reviews | Revenue forecasts, hiring trends |
| Transaction data | Credit card, B2B payments | Same-store sales, market share |
| App usage | DAU, MAU, time spent | User engagement, growth |
| Geolocation | Foot traffic, store visits | Retail traffic, competitive analysis |
| Patents | Filings, citations | Innovation flows, R&D output |
| Government | SEC filings, FDA, court records | Insider activity, regulatory events |
| News | Articles, briefs, ratings | Sentiment, event detection |
| Social | Twitter, Reddit, Discord | Retail sentiment, viral signals |
| Audio/video | Earnings calls, video footage | Manager confidence, executive sentiment |
| Onchain crypto | Wallet flows, contract events | Whale tracking, protocol metrics |
| ESG | Controversies, ratings | Risk filtering, compliance |

Each category has its own data infrastructure, signal characteristics, and best-practice methodology. We treat the largest below.

---

## Satellite Imagery

### Sources

Commercial vendors:
- **Planet Labs**: ~3m resolution, daily revisit. Largest commercial constellation.
- **Maxar / DigitalGlobe**: high-resolution (30cm), less frequent.
- **Capella Space, ICEYE**: synthetic aperture radar (SAR), all-weather imaging.

Specialized providers:
- **Orbital Insight**: pre-processed analytics (parking counts, etc.).
- **RS Metrics**: industrial site monitoring.
- **SpaceKnow**: economic activity indices from satellite.

### Use Cases

- **Retail parking**: count cars at Walmart, Target, Home Depot. Predict same-store sales.
- **Crude oil storage**: tank fill levels in Cushing, OK. Predict WTI price.
- **Crop yields**: NDVI (vegetation index) over agricultural land. Predict commodity prices.
- **Ship traffic**: container ships at ports. Predict trade flows.
- **Mining activity**: heap leach pad, tailings dam. Predict supply.
- **Construction**: building progress on real estate developments.

### Pipeline

1. Acquire imagery for relevant locations.
2. Pre-process (geo-reference, atmospheric correction).
3. Apply ML model (object detection, segmentation, regression).
4. Aggregate to time series of metric (e.g., daily parking count).
5. Convert to economic indicator (e.g., y/y change in parking).
6. Backtest as a signal for relevant ticker.

### Reality Check — Satellite Limitations

- **Cost**: imagery + processing can be $100K-$10M annually.
- **Coverage**: not every location of interest is observable.
- **Timeliness**: 1-7 day delay typical.
- **Weather**: optical limited; SAR more expensive.
- **Crowding**: parking-lot signals are well-known; alpha decayed.

---

## Web Scraping

Scraping public web pages for structured data:
- **Pricing pages**: e-commerce prices, hotel/airline fares.
- **Job postings**: Indeed, LinkedIn, Glassdoor. Predict hiring intentions.
- **Reviews**: Yelp, Google, app store. Predict consumer sentiment.
- **Search trends**: Google Trends. Predict consumer interest.
- **News articles**: from news sites.

### Tools

- **Python**: requests, BeautifulSoup, scrapy, playwright, selenium.
- **Headless browsers**: for JS-heavy pages (Playwright, Selenium).
- **Anti-bot**: rotating proxies, browser fingerprint randomization.

### Legal/ToS

Web scraping is legally murky:
- US: hiQ vs LinkedIn (2022) — public data scraping is generally legal.
- EU: GDPR concerns with personal data.
- Site ToS: many prohibit automated scraping (enforcement varies).

Hedge funds typically use commercial vendors (e.g., **Burning Glass** for job postings, **DataMinr** for news) to avoid legal/ToS issues.

### Reality Check — Scraping Costs

- Engineering: 1-2 FTEs per asset class.
- Infrastructure: cloud + proxies.
- Maintenance: pages change; pipelines break weekly.
- Legal: indemnification for scraping vendors.

---

## Credit Card Transactions

Aggregated transaction data from card networks or panel providers:

### Vendors

- **Yodlee**: anonymized transaction panel from millions of consumers.
- **Earnest**: similar; sold to Plaid in 2018.
- **SecondMeasure**: focused on hedge funds.
- **Visa Predictive**: Visa's own analytics.

### Granularity

- Merchant-level: transactions at "Walmart" by zip code.
- Industry-level: aggregate retail spending.
- Time: usually daily, sometimes hourly.

### Use Cases

- **Same-store sales prediction**: predict reported retail sales.
- **Market share**: relative performance of competitors.
- **Consumer trends**: sector rotation, e.g., e-commerce vs brick-and-mortar.
- **Travel and leisure**: hotels, airlines, restaurants.

### Coverage

- Covers ~10-20% of US consumer transactions for top vendors.
- Sample is biased (younger, higher income, more digital).
- Calibration to total spending requires reweighting.

### Reality Check — Cost

- $100K-$1M+ annually for major hedge fund.
- Diminishing alpha as more buyers use it.

---

## App Usage Data

User behavior on mobile apps:

### Vendors

- **App Annie / Data.AI**: download counts, daily active users, time spent.
- **SimilarWeb**: web + app traffic.
- **Sensor Tower**: similar.

### Metrics

- **DAU**: daily active users.
- **MAU**: monthly active users.
- **Session length**.
- **Retention**: D1, D7, D30 cohort retention.
- **Revenue**: estimates from purchases.

### Use Cases

- **Tech stock fundamentals**: predict revenue from app metrics.
- **Competitive landscape**: app rankings shift.
- **Trend detection**: viral apps before they show in financial reports.

### Reality Check — Data Quality

- App store data is sampled, not measured (extrapolations from panels).
- App vendors often dispute external estimates.
- Estimates can be off by 30-50% in absolute terms; trends more reliable.

---

## Geolocation

GPS data from phones:

### Vendors

- **SafeGraph**: anonymized foot traffic to ~7M US POIs.
- **Veraset**: similar.
- **GroundTruth, Cuebiq**: location panels.

### Use Cases

- **Retail traffic**: visits to Walmart, McDonald's, Home Depot.
- **Office occupancy**: post-COVID work-from-home trends.
- **Travel destinations**: tourism trends.
- **Competitive analysis**: competing locations' traffic.

### Privacy

- All anonymized at source.
- US, EU CCPA / GDPR compliant.
- Aggregated reporting (no individual tracking).

### Reality Check — Coverage

Some POIs have many visits sampled; others have few. Less-frequent POIs require different statistical treatment.

---

## B2B Transactions and Supply Chain

### Trade Data

- **Panjiva**: customs declaration data for ocean shipments to/from US.
- **Import Genius**: similar.
- **ShipNext**: real-time shipping data.

### Use Cases

- **Supply chain stress**: detect input shortages.
- **Geopolitical effects**: sanctions, tariffs.
- **Companies' sourcing**: where do they get inputs?
- **Inventory levels**: from shipping volumes.

### Ad Spend

- **Pathmatics, MediaRadar**: digital ad spend tracking.
- **Use case**: predict marketing campaigns, product launches.

### Reality Check — Sample Bias

Customs data captures formal trade. Off-the-books trade and small-scale shipments missed. Useful for major supply chains but not for niche markets.

---

## Patent Data

### Sources

- **USPTO**: full text of US patents and applications.
- **Google Patents**: enriched search of multiple patent offices.
- **WIPO**: international (PCT) filings.

### Use Cases

- **Innovation flows**: count patent filings by company.
- **R&D efficiency**: patents per R&D dollar.
- **Technology trends**: clustering of filings by topic.
- **Litigation predictors**: patents being asserted in courts.

### Methodology

- NLP for topic clustering.
- Citation networks for influence/quality assessment.
- Time-series analysis of filing rates.

### Reality Check — Patent ≠ Innovation

- Many patents are defensive (preventing others' patents).
- Patents take years to file and grant.
- Software companies file fewer patents but innovate more.

Use patents as one signal among many.

---

## Government and Regulatory Data

### SEC Filings

- 10-K annual reports.
- 10-Q quarterly reports.
- 8-K event-driven filings.
- S-1 registration statements (IPOs).
- 13F institutional holdings (quarterly, 45-day delay).
- Form 4 insider trading disclosures.

### Use Cases

- **Insider trading signal**: insider buys/sells often predict future returns.
- **13F tracking**: hedge fund holdings analysis.
- **8-K event reaction**: trade on specific event types.
- **NLP on annual reports**: sentiment, risk language, complexity.

### FDA

- Clinical trial registrations.
- Drug approvals.
- Adverse event reports.

For pharma/biotech trading.

### FCC

- Spectrum auction results.
- Wireless company strategy.

### PACER (Court Records)

- Litigation tracking.
- Bankruptcy filings.

### Reality Check — Filing Lag

Filings appear with delay (10-Q within 45 days). Cannot front-run filings; can analyze after.

---

## News and Text Data

### Vendors

- **RavenPack**: structured news sentiment, ESG events.
- **Bloomberg Sentiment**: news + Twitter sentiment.
- **Reuters NewsScope**: tagged news with sentiment.
- **Refinitiv MarketPsych**: psychological state indicators.
- **Dow Jones DNA**: structured news access.

### Pipeline

1. Ingest news (full-text or pre-tagged).
2. Entity resolve to tickers (e.g., "Apple" → AAPL).
3. Compute sentiment.
4. Aggregate to time series per ticker.
5. Use as feature in trading models.

### Reality Check — News Latency

News-driven trading needs sub-second latency to capture moves before price adjusts. Slower analysis (e.g., daily news sentiment) captures only secondary effects.

---

## Social Media

### Twitter/X

Cashtags ($TICKER) and handles for sentiment:
- StockTwits API for trader sentiment.
- Twitter API (now expensive) for general.
- Bot detection: ~30% of "trader" Twitter accounts are bots.

### Reddit

WallStreetBets (WSB) and similar:
- API + web scraping.
- Sentiment via NLP.
- Volume of mentions as predictor.

### Discord

Crypto-focused. Direct API less common; community-monitoring services used.

### Reality Check — Retail Sentiment

Retail sentiment has been predictive in crypto and meme-stock markets:
- 2021 GME: WSB sentiment preceded price moves.
- 2022 LUNA: Discord sentiment shifted before crash.

But signal is noisy and crowded; alpha decay is rapid.

---

## Earnings Call Transcripts

### Sources

- **Capital IQ, Refinitiv, FactSet**: post-call transcripts.
- **Bloomberg**: text + audio.
- **AlphaSense**: searchable transcripts with NLP.

### Use Cases

- **Sentiment scoring**: positive/negative tone.
- **Manager confidence**: language complexity, hedging words ("might", "could").
- **Topic shifts**: changes in what management emphasizes.
- **Q&A response quality**: deflection of analyst questions.

### NLP Methods

- **Loughran-McDonald** finance dictionary: positive/negative word counts.
- **FinBERT**: BERT fine-tuned on financial text.
- **GPT/Claude**: zero-shot classification of complex language.

---

## Audio and Video Analytics

### Voice Stress

Vocal characteristics during earnings calls:
- Pitch variation.
- Speech rate.
- Hesitation patterns.

Some vendors (Speech Analytics by NVivo, Praat-based custom) extract these. Empirical: predictive but noisy.

### Video

Executive body language during interviews. Less mature; some research-stage methods.

### Reality Check — Audio/Video Niche

Audio/video analytics is niche. Significant engineering for moderate alpha. Most quant funds focus on text first.

---

## Onchain Crypto Data

### Vendors

- **Glassnode**: BTC/ETH onchain analytics.
- **Nansen**: wallet labeling, smart money tracking.
- **Dune Analytics**: SQL-queryable blockchain data.
- **Messari, Token Terminal**: protocol metrics.

### Metrics

- **Transactions per day**: network usage.
- **Active addresses**: user growth.
- **Stablecoin supply**: speculative interest indicator.
- **Exchange flows**: in/out of CEXes.
- **Long-term holder vs short-term**: distribution dynamics.
- **Realized cap**: market cap at last move.
- **NUPL (Net Unrealized Profit/Loss)**: aggregate position.

### Use Cases

- **Whale tracking**: large wallet movements predict price.
- **Exchange outflows**: BTC moving off exchanges signals long-term holding.
- **Stablecoin minting**: predicts capital deployment.
- **Smart contract events**: protocol-specific activity.

### Wallet Clustering

Heuristic clustering of addresses to entities:
- **Common spend**: addresses spent in same transaction belong to same entity.
- **Change addresses**: outputs back to sender.
- **Exchange labels**: known exchange addresses.

Production tools (Chainalysis, TRM) sell this as a service.

### Reality Check — Crypto Onchain Edge

Many onchain signals are well-known. Alpha decay rapid. Edge is in:
- Custom metrics.
- Entity-level analysis.
- Cross-protocol correlations.
- Combining onchain with offchain (CEX, derivatives).

---

## ESG Data

### Vendors

- **MSCI ESG**: ratings on 8000+ companies.
- **Sustainalytics**: similar.
- **Refinitiv ESG**: data + methodology.
- **Bloomberg ESG**: data + methodology.

### Components

- **Environmental**: emissions, water, energy.
- **Social**: labor, diversity, community.
- **Governance**: board, executive comp, audit.

### Controversies

- ESG ratings often disagree (correlation across vendors ~0.5).
- Methodologies are opaque.
- Greenwashing prevalent.

### Use Cases

- **Risk filtering**: exclude high-controversy names.
- **Sector tilts**: overweight low-carbon.
- **Compliance**: ESG-compliant funds.
- **Alpha**: less common; ESG sorting hasn't reliably outperformed.

---

## Data Ingestion Architecture

### Batch vs Streaming

- **Batch**: nightly downloads, ETL into warehouse. Fine for most fundamental alt data.
- **Streaming**: Kafka, Kinesis. For news, social, real-time order flow.

### Storage

- **S3 / Cloud Storage**: cheap raw storage.
- **Parquet / Delta Lake**: columnar for analytics.
- **PostgreSQL / BigQuery**: structured queries.
- **Time-series DBs (InfluxDB, TimescaleDB)**: for time-series.

### Pipeline

1. **Ingestion**: API pull, FTP/SFTP, vendor-pushed S3.
2. **Validation**: schema checks, completeness, sanity bounds.
3. **Transformation**: ETL into normalized form.
4. **Storage**: raw + transformed.
5. **Catalog**: metadata index for discovery.
6. **Access**: query layer for downstream models.

### Common Tools

- **Apache Airflow / Dagster**: orchestration.
- **dbt**: SQL-based transformations.
- **Great Expectations**: data validation.
- **Apache Kafka / Redpanda**: streaming.

---

## Point-in-Time Database Construction

Avoid look-ahead by storing data with **as-of** dates:

### Schema

```
CREATE TABLE alt_data_pit (
    id INT,
    ticker VARCHAR(10),
    metric_name VARCHAR(50),
    metric_value FLOAT,
    measurement_date DATE,
    available_date DATETIME,  -- when data was actually published / received
    revision_number INT,
    PRIMARY KEY (id)
);
```

When backtesting, filter `WHERE available_date <= backtest_as_of_date`.

### Revisions

Many data sources publish initial values then revise. Track all revisions:
- Initial publication.
- First revision (e.g., +30 days).
- Final revision.

For backtest, use whichever was available at as-of date.

### Reality Check — PIT Discipline

Building PIT requires capturing as-of metadata at ingestion. Easy to lose. Audit pipelines for PIT correctness regularly.

---

## Data Cleaning

### Missing Data

- **Drop**: simplest; loses data.
- **Impute**: with mean, median, or predicted value.
- **Forward-fill**: use last observed; common for time series.
- **Model-based**: GAM or ML to impute.

For trading: forward-fill or model-based; never look-ahead impute.

### Outliers

- **Visual inspection**: scatter plots.
- **Statistical**: > 3-sigma from rolling mean.
- **Robust**: MAD-based detection.

For trading: outliers may be real (e.g., earnings announcement). Distinguish errors from real events.

### Normalization

- **Z-score**: (x - mean) / std.
- **Rank-based**: percentile within universe.
- **Log transform**: for skewed distributions.
- **Cross-sectional standardization**: each date, normalize across stocks.

---

## Entity Resolution

Mapping alt data identifiers to tradable instruments:

### Identifiers

- **Ticker**: unstable (changes with corporate actions).
- **CUSIP**: stable, US-only.
- **ISIN**: stable, international.
- **CRSP permno**: academic standard.
- **PERMID (Refinitiv)**: vendor-specific.
- **Bloomberg BBGID**: Bloomberg standard.

### Mapping Process

1. Normalize source identifier (e.g., parse merchant name from credit card data).
2. Lookup in master mapping table.
3. Handle aliases, subsidiaries, and corporate hierarchies.
4. Date-aware mapping for corporate actions.

### Tools

- **OpenFIGI**: free identifier mapping (via API).
- **Refinitiv RIC**: vendor mapping.
- **Custom**: in-house cross-reference.

### Reality Check — Entity Mapping Errors

Even sophisticated systems mis-map ~5-10% of alt data. Validate by spot-checking mapped data against expected.

---

## Feature Engineering

### Time-Aware Aggregations

- Last 7 / 30 / 90 days totals.
- Year-over-year change.
- Percentile rank within history.
- Trailing volatility of metric.

### Cross-Sectional Ranking

For each date:
- Rank stocks by metric.
- Convert to percentile (0-100).
- Use rank in regression instead of raw value.

Robust to scale and distribution.

### Residualization

If you want a "factor-neutral" signal:
- Regress alt data feature on factor exposures (size, value, momentum).
- Use residual as factor-neutral signal.

### Lag Optimization

For each feature, find optimal lag for predicting target:
- Compute correlation at lags -1, -7, -30, -90.
- Use lag with maximum predictive power.
- Beware of multiple-testing.

---

## Signal Decay Analysis

### Half-Life

How long does the signal remain predictive after generation? Compute correlation between signal at time t and return at time t+τ for various τ.

```python
import numpy as np

def signal_decay(signal, returns, max_lag=120):
    """Compute correlation of signal with returns at lags 1 to max_lag."""
    corrs = np.zeros(max_lag)
    for lag in range(1, max_lag + 1):
        corrs[lag-1] = np.corrcoef(signal[:-lag], returns[lag:])[0, 1]
    return corrs

# Example: synthetic signal with decay
np.random.seed(0)
signal = np.random.normal(0, 1, 1000)
returns = 0.3*signal + np.random.normal(0, 1, 1000)  # immediate alpha
returns[1:] += 0.1 * signal[:-1]  # 1-day lagged alpha
corrs = signal_decay(signal, returns, max_lag=10)
print(f"Decay: lag 1: {corrs[0]:.3f}, lag 5: {corrs[4]:.3f}")
```

### Crowding

Signals decay faster as more participants use them:
- Original alpha: 30bp/year.
- After widely adopted: 5-10bp/year.

Track decay over months; cut signals that decay below thresholds.

---

## Backtesting Alt Data Signals

### PIT Discipline

Use only data available at backtest as-of date. Crucial for credibility.

### Capacity

Alt data signals often have low capacity. Test at multiple AUM levels.

### Realistic Costs

Include execution costs (spread, impact). Alt data signals often have small alpha; costs can wipe out.

---

## Combining with Traditional Features

### Linear Combination

Simple regression of returns on (alt + traditional) features. Suffers from multicollinearity if features are correlated.

### Tree-Based (XGBoost, LightGBM)

Naturally handles feature interactions and non-linearities. Standard for alt data + traditional combinations.

```python
import xgboost as xgb

# Combine alt data features with traditional
features = pd.concat([alt_features, traditional_features], axis=1)
model = xgb.XGBRegressor(max_depth=5, n_estimators=200)
model.fit(features.shift(1).iloc[1:], target_returns.iloc[1:])
```

### Neural Network Ensembles

For complex non-linear relationships. Requires more data.

### Stacking

Train multiple base models; combine via meta-learner. Reduces overfitting if base models are diverse.

---

## NLP Pipeline

### Tokenization

Standard methods: word-level, sub-word (BPE, WordPiece), character-level.

### Embeddings

Pre-trained:
- **Word2Vec, GloVe**: traditional. Less common now.
- **BERT**: contextualized embeddings.
- **FinBERT**: finance-specific BERT.
- **GPT/Claude**: large language models for zero-shot tasks.

### Domain Adaptation

Pre-trained models are general. Fine-tune on financial corpus:
- Earnings call transcripts.
- 10-K filings.
- Financial news.

Domain-adapted models outperform general by 5-15% on financial NLP tasks.

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finbert')
model = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')

inputs = tokenizer("Apple reported strong earnings", return_tensors='pt')
outputs = model(**inputs)
# outputs.logits gives sentiment scores
```

---

## Sentiment Scoring

### Lexicon-Based

**Loughran-McDonald** finance dictionary:
- Positive words: ~350.
- Negative words: ~2300.
- Uncertainty words: ~290.

Count words in text, weight by frequency.

```python
def lm_sentiment(text, positive_words, negative_words):
    words = text.lower().split()
    pos = sum(1 for w in words if w in positive_words)
    neg = sum(1 for w in words if w in negative_words)
    return (pos - neg) / max(len(words), 1)
```

### Supervised

Train classifier (SVM, BERT) on labeled examples (positive/negative/neutral).

### LLM Zero-Shot

Use GPT/Claude to classify sentiment without training data:

```
Prompt: "Classify the sentiment of this earnings call snippet:
'We expect challenges in Q2 due to supply chain disruption.'
Reply with one word: positive, negative, neutral."
```

### Reality Check — Sentiment Limits

- Sentiment alone has weak predictive power (correlation 0.05-0.15).
- Combined with other features, contributes meaningfully.
- Crowded: many funds have sentiment models.

---

## Topic Modeling

### LDA (Latent Dirichlet Allocation)

Bayesian topic model. Each document is mix of topics; each topic is distribution over words.

### BERTopic

Modern variant using BERT embeddings + clustering. Better topic coherence than LDA.

### Use

- Cluster news/calls into topics.
- Track topic prevalence over time.
- Detect topic shifts as predictor.

### Reality Check — Topic Stability

Topics drift over time as language evolves. Re-train periodically.

---

## Knowledge Graphs

### Entity-Relation-Entity Triples

E.g., "Apple supplies iPhone" → (Apple, supplies, iPhone).

### Construction

- NER (Named Entity Recognition) to identify entities.
- Relation extraction to identify links.
- Aggregation across documents.

### Use Cases

- Supply chain mapping (who supplies whom).
- Competitor identification.
- Influence networks (executive moves).

### Reality Check — Knowledge Graph Maintenance

Building is moderately easy; maintaining accuracy at scale is hard. Most production systems use vendor data (Refinitiv KG, Bloomberg).

---

## Causal Inference

### Instrumental Variables

For causal effect identification when confounding present.

### Regression Discontinuity

When treatment determined by a cutoff (e.g., S&P 500 inclusion).

### Difference-in-Differences

Compare changes over time for treatment vs control groups.

### Synthetic Control

Construct control group from weighted combination of donors.

### Application

Causal questions in trading:
- Does index inclusion cause price impact?
- Does ESG rating change cause flows?
- Does insider buying cause future returns?

Document 99 covers causal inference in trading detail.

---

## Privacy and Ethics

### Anonymization

All consumer data should be anonymized at source. Re-identification risk: combining datasets can de-anonymize.

### GDPR (EU)

- Right to be forgotten.
- Data minimization.
- Lawful basis required for processing.

### CCPA (California)

- Right to know what's collected.
- Right to deletion.
- Opt-out for sale.

### Best Practice

- Use vendor data (vendor handles compliance).
- Avoid personal identifiers in your own data.
- Document data flows for audit.

### Insider Trading Concerns

If alt data provides material non-public information, trading is illegal:
- Aggregate data: usually OK.
- Individual-level: risky.
- Specific companies: especially risky.

Legal review for novel data sources.

---

## Vendor Selection

### Evaluation Criteria

- **Coverage**: which tickers/markets included?
- **History**: how far back does data go?
- **Frequency**: daily, weekly, monthly?
- **Latency**: when after the event is data available?
- **Methodology**: how is data collected and processed?
- **Track record**: do they have other client successes?
- **Cost**: subscription + integration.

### Pilot

Negotiate pilot access (1-3 months) before commit:
- Test integration.
- Backtest the data.
- Validate vendor claims.

### Multi-Vendor

For critical data, use multiple vendors:
- Cross-validate quality.
- Avoid single point of failure.
- Compare methodologies.

---

## Cost-Benefit Analysis

### Cost Components

- Vendor subscription: $50K - $5M annually.
- Engineering: 1-3 FTEs to integrate per vendor.
- Compute: cloud + storage.
- Maintenance: ongoing.

### Benefit Estimation

Pre-purchase: estimate Sharpe contribution from backtest. Post-purchase: track actual contribution.

### Threshold

- Required Sharpe contribution: 0.05-0.2.
- Required AUM: ratio depends on vendor cost.

For a $1B fund: vendor at $500K must contribute ~5bp/year. Lower bar than smaller funds.

---

## Code Examples

### Credit Card Data Pipeline

```python
import pandas as pd

def credit_card_signal(transactions, ticker_mapping):
    """Build same-store sales signal from credit card data."""
    # transactions: DataFrame with merchant, date, amount
    # ticker_mapping: merchant -> ticker
    transactions['ticker'] = transactions['merchant'].map(ticker_mapping)
    daily = transactions.groupby(['ticker', 'date'])['amount'].sum().unstack('ticker')
    
    # Year-over-year change
    yoy = (daily / daily.shift(252) - 1)
    
    # Cross-sectional rank
    yoy_rank = yoy.rank(axis=1, pct=True) - 0.5
    return yoy_rank

# Use as input to portfolio model
```

### NLP Sentiment

```python
from transformers import pipeline

# FinBERT pipeline
sentiment = pipeline('sentiment-analysis', model='ProsusAI/finbert')

def call_sentiment(transcript):
    """Score earnings call transcript."""
    # Split into chunks (FinBERT max ~512 tokens)
    chunks = [transcript[i:i+1000] for i in range(0, len(transcript), 1000)]
    scores = sentiment(chunks)
    pos = sum(s['score'] for s in scores if s['label'] == 'Positive')
    neg = sum(s['score'] for s in scores if s['label'] == 'Negative')
    return (pos - neg) / len(chunks)
```

---

## Case Studies

### Walmart Parking Lot

Famous example: Orbital Insight + Walmart parking lots predict same-store sales. Edge ~50bp/quarter in early years (2015-2018). Decayed as adoption spread.

### Tesla Deliveries

Satellite imagery of Tesla factories + parking lots predicted quarterly deliveries. Worked 2018-2020; decayed thereafter.

### COVID Lockdown Signals

Foot traffic data (SafeGraph) anticipated retail/restaurant collapses in March 2020 by 1-2 weeks.

### WSB GME Squeeze

Reddit WSB sentiment predicted GME squeeze in January 2021. Some funds caught the move; many were squeezed.

---

## Reality Checks

- **Alpha decay**: alt data signals decay faster than traditional.
- **Vendor risk**: vendors fail or change methodology.
- **Integration cost**: 6-12 months and significant engineering.
- **Diminishing returns**: marginal value of next data source decreases.
- **Privacy/regulatory**: legal landscape changing.

---

## Reference Tables, Cheat Sheets, Bibliography

### Vendor Reference

| Category | Vendor | Cost (annual, est) |
|---|---|---|
| Satellite | Orbital Insight | $1-5M |
| Satellite | Planet | $200K-2M |
| Credit card | Yodlee | $200K-2M |
| Credit card | SecondMeasure | $300K-2M |
| App | App Annie | $50-500K |
| Geolocation | SafeGraph | $100-500K |
| News sentiment | RavenPack | $200K-1M |
| Onchain | Glassnode | $50-200K |
| ESG | MSCI ESG | $200K-2M |
| Patents | USPTO public | free |

### Bibliography

- **Denev, A. and Amen, S. (2020), *The Book of Alternative Data*, Wiley.** Standard reference.
- **López de Prado, M. (2018), *Advances in Financial Machine Learning*, Wiley.** Including alt data.
- **Lucca, D. and Moench, E. (2015), "The Pre-FOMC Announcement Drift", *J. Finance*.** Government data.
- **Loughran, T. and McDonald, B. (2011), "When Is a Liability Not a Liability?", *J. Finance*.** Finance dictionary.
- **Tetlock, P. (2007), "Giving Content to Investor Sentiment: The Role of Media in the Stock Market", *J. Finance*.** News sentiment.
- **Cohen, L., Diether, K., Malloy, C. (2013), "Misvaluing Innovation", *Review of Financial Studies*.** Patent data.
- **Da, Z., Engelberg, J., Gao, P. (2011), "In Search of Attention", *J. Finance*.** Search trends.
- **Devlin, J. et al. (2018), "BERT: Pre-training of Deep Bidirectional Transformers", arXiv.**
- **Araci, D. (2019), "FinBERT: Financial Sentiment Analysis with Pre-trained Language Models".**

### Cross-References

- Document 200 — Stochastic Calculus.
- Document 203 — Bayesian Methods.
- Document 204 — Information Theory.
- Document 211 — Backtesting.
- Document 75 — XGBoost LightGBM.
- Document 99 — Causal Inference Pearl.

---

*End of document 212. ~1,400 lines.*
