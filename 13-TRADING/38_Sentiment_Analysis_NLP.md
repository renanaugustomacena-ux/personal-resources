# 38 - Sentiment Analysis: Trading the News (NLP)

**Volume:** 38 of 50
**Strategy Type:** Alternative Data / AI / Quantitative Fundamental
**Risk Profile:** Model Risk / Hallucination
**Mathematical Basis:** Vector Embeddings / Probability of "Positive" vs "Negative"

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: Information Asymmetry](#2-the-theory-information-asymmetry)
    * 2.1. The "Ravenous Beast" (The Market eats information)
    * 2.2. Human Latency (Reading speed: 200 wpm) vs AI Latency (Computers: 1ms)
    * 2.3. The "Over-Reaction" Hypothesis
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. The Setup: Connect to News API (Bloomberg, Reuters, Twitter)
    * 3.2. Processing: Calculate Sentiment Score (-1 to +1)
    * 3.3. The Trade: Long if Score > 0.8. Short if Score < -0.8.
    * 3.4. The Exit: Time-based (15 mins) or Momentum reversal.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Bag of Words (Loughran-McDonald Dictionary)
    * 4.2. Transformer Models (BERT / FinBERT)
    * 4.3. Attention Mechanisms (Self-Attention weights)
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. The "Hathaway" Effect (Anne Hathaway news moving Berkshire Hathaway)
    * 5.2. Elon Musk's Tweets (DOGE, TSLA)
    * 5.3. Fake News Flash Crashes (Associated Press hacked: "White House Explosion")
6. [Python Implementation (Production Grade)](#6-python-implementation-production-grade)
    * 6.1. FinBERT for Financial Sentiment
    * 6.2. LLM Integration (OpenAI/Anthropic for summary)
    * 6.3. Calculating "Buzz" (Volume of mentions)
7. [Optimization & Variations](#7-optimization--variations)
    * 7.1. "Earnings Call" Analysis (Tone of CEO voice)
    * 7.2. "Social Arb" (Reddit/WallStreetBets trends)
    * 7.3. "Fedspeak" (Parsing FOMC Minutes for Hawkish/Dovish/Unchanged)
8. [Risk Management: The Hallucination](#8-risk-management-the-hallucination)
    * 8.1. Sarcasm Detection (AI is bad at irony).
    * 8.2. Negation Handling ("Not bad" is good, but "Not good" is bad).
    * 8.3. Position Sizing based on Confidence Score.
9. [Conclusion: The Machine Reads Faster](#9-conclusion-the-machine-reads-faster)

---

# 1. Executive Summary

**Sentiment Analysis** uses Natural Language Processing (NLP) to quantify the qualitative.
Markets move on "Narratives".
Before 2018, narratives were processed by humans.
Today, **Large Language Models (LLMs)** read the internet in real-time.
They predict the *emotional reaction* of the market to a headline before a human has even read the first word.
This is the cutting edge of Alpha.

---

# 2. The Theory

### 2.1. Speed of Information

When a headline hits the terminal: "FDA Approves Drug X".

1. **Algos (L1):** Read header. Keyword "Approves". Buy. (Latency: 10ms).
2. **Quants (L2):** Parse full text. Sentiment Score +0.9. Buy more. (Latency: 100ms).
3. **Humans (L3):** Read article. Think. Buy. (Latency: 10 seconds).
The Alpha is in being L1 or L2.

### 2.2. Efficient Market Hypothesis (EMH)

EMH says news is instantly priced in.
Reality says: It takes time for the *magnitude* to settle.
Sentiment Strategies capture the initial "Shock" and the subsequent "Drift".

---

# 3. Strategy Rules

### 3.1. Data Sources

* **Tier 1:** Bloomberg Terminal (Machine Readable News). Expensive.
* **Tier 2:** Twitter/X API (Cashtags `$TSLA`). Noisy.
* **Tier 3:** Reddit (WallStreetBets). Retail Sentiment. Good for Meme Stocks.
* **Tier 4:** SEC EDGAR (10-K, 10-Q). Fundamental.

### 3.2. Scoring

Input: "Tesla recalls 2 million vehicles due to autopilot defect."
Model: FinBERT (Financial BERT).
Output: `[Negative: 0.98, Neutral: 0.01, Positive: 0.01]`
Score: -0.98.
Action: Short TSLA.

---

# 4. Mathematical Derivation

Dictionary Approach (Old School):
$$ S = \frac{N_{pos} - N_{neg}}{N_{pos} + N_{neg}} $$
Transformer Approach (New School):
$$ \vec{v} = \text{Embedding}(Text) $$
$$ P(Sentiment) = \text{Softmax}(W \times \vec{v} + b) $$
The vector $\vec{v}$ captures context ("Profit *fell*" vs "Loss *narrowed*").

---

# 5. Historical Case Studies

### 5.1. The AP Hack (2013)

Associated Press Twitter: "Breaking: Two Explosions in the White House and Barack Obama is injured."
The S&P 500 crashed 1% in seconds.
Why? Because Algos read "Explosion" + "Obama" + "White House".
Humans realized it was fake news 2 minutes later.
Market recovered instanty.
**Lesson:** NLP Algos are literal and dangerously fast.

### 5.2. GameStop (2021)

Hedge Funds ignoring Reddit were destroyed.
Sentiment Algos tracking `/r/wallstreetbets` saw a 10,000% increase in mentions of "GME".
They went Long.
They made billions while Melvin Capital lost billions.

---

# 6. Python Implementation

```python
from transformers import pipeline
import pandas as pd

# Load Financial BERT (Pre-trained on financial text)
classifier = pipeline('sentiment-analysis', model='yiyanghkust/finbert-tone')

class NewsTrader:
    def __init__(self, threshold=0.9):
        self.pipeline = classifier
        self.threshold = threshold

    def analyze_headline(self, headline):
        # Result: [{'label': 'Negative', 'score': 0.99}]
        result = self.pipeline(headline)[0]
        
        label = result['label']
        score = result['score']
        
        if score < self.threshold:
             return "NO_TRADE" # Not confident enough
             
        if label == "Positive":
            return "BUY"
        elif label == "Negative":
            return "SELL"
        else:
            return "NEUTRAL"
```

### 6.3. The "Buzz" Factor

Sentiment is Direction. Buzz is Magnitude.
$$ Signal = Sentiment \times \log(Buzz) $$
If Sentiment is mildly positive (+0.2) but Buzz is HUGE (everyone talking about it), price moves.
If Sentiment is extremely positive (+0.9) but nobody cares (Buzz=0), price stays flat.

---

# 7. Optimization

### 7.1. Fed Watch

Parsing FOMC Minutes.
"The Committee judges that risks... are balanced." (Neutral).
"The Committee judges that risks... are elevated." (Hawkish).
Using "Cosine Similarity" to compare this month's statement vs last month's.
High Similarity = No Change. Low Similarity = Pivot.

### 7.2. Ealry Adopter vs Laggard

* **Twitter:** Early Signal (Minutes). Noisy.
* **Mainstream Media:** Late Signal (Hours). Confirmed.
Strategy: Buy on Twitter spike. Sell into Media confirmation.

---

# 8. Risk Management

### 8.1. Sarcasm & Irony

"Great job crashing the economy via inflation, JPowell!"
Model reads "Great job" $\to$ Positive.
Human reads sarcasm $\to$ Negative.
FinBERT handles this better than Dictionary methods, but still fails.

### 8.2. Fake News

AI generated fake news is the new threat.
"Deepfake of CEO resigning".
Algos will dump the stock.
**Defense:** Only trade on Verified Sources (Blue check / Bloomberg ID).

---

# 9. Conclusion

Sentiment Analysis is standard in 2024.
You cannot trade Earnings without checking the AI Score.
You cannot trade Crypto without checking X.
For GOLIATH, we integrate FinBERT scores into our "Regime Filter".
If Market Sentiment is Negative, we reduce Long exposure even if Techncials are Bullish.
It acts as a qualitative "Veto" on quantitative signals.
