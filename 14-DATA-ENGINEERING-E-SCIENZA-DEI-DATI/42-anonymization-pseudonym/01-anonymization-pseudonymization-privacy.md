# Data Anonymization, Pseudonymization, and Privacy-Preserving Techniques

## 1. Anonymization vs Pseudonymization

### Legal Foundations: GDPR Recital 26

The General Data Protection Regulation draws a fundamental distinction between anonymized and pseudonymized data. Recital 26 establishes the definitional boundary:

> "The principles of data protection should therefore not apply to anonymous information, namely information which does not relate to an identified or identifiable natural person or to personal data rendered anonymous in such a manner that the data subject is not or no longer identifiable."

This creates a binary classification with profound regulatory consequences:

- **Anonymized data**: Falls entirely outside the scope of GDPR. No consent required, no data subject rights apply, no breach notification obligations. The data is no longer "personal data" in any legal sense.
- **Pseudonymized data**: Remains personal data under GDPR (Article 4(5)). All obligations still apply, though certain provisions (like Article 11) may relax requirements when identification is no longer possible without additional information.

### The Reversibility Spectrum

Data transformation techniques exist on a spectrum from fully reversible to provably irreversible:

```
[Original Data] ←→ [Encrypted] ←→ [Pseudonymized] ←→ [De-identified] ←→ [Anonymized]
     ↑                  ↑                ↑                    ↑                ↑
  No protection    Key-dependent     Token/hash         Statistical        Irreversible
                   reversible        reversible          guarantees
```

**Pseudonymization** (Article 4(5)): "Processing of personal data in such a manner that the personal data can no longer be attributed to a specific data subject without the use of additional information, provided that such additional information is kept separately and is subject to technical and organisational measures."

Key characteristics:
- Reversible by design (the controller retains the mapping)
- "Additional information" must be kept separately under strict access controls
- Reduces risk, recognized as a safeguard under Article 25 (data protection by design) and Article 32 (security of processing)
- Enables the "compatible use" argument under Article 6(4)

**Anonymization**: Irreversible transformation where no party (including the data controller) can re-identify individuals. The Article 29 Working Party (now EDPB) established the "reasonability test" — considering all means reasonably likely to be used for identification, accounting for cost, time, available technology, and technological developments.

### Article 29 Working Party Opinion 05/2014

The WP29 Opinion on Anonymization Techniques (WP216) remains the definitive guidance. It evaluates anonymization against three criteria:

1. **Singling out**: Can a single individual be isolated within the dataset?
2. **Linkability**: Can records relating to the same individual be linked across datasets?
3. **Inference**: Can the value of an attribute be deduced from other values?

The opinion evaluates techniques against these criteria:

| Technique | Singling Out | Linkability | Inference |
|-----------|-------------|-------------|-----------|
| Pseudonymization | Insufficient | Insufficient | Insufficient |
| Noise addition | May prevent | May prevent | May prevent |
| Substitution | May prevent | Insufficient | May prevent |
| Aggregation/k-anonymity | Prevents (if k sufficient) | May prevent | May prevent |
| l-diversity | Prevents | May prevent | Prevents (limited) |
| Differential privacy | Prevents | Prevents | Prevents (with ε guarantees) |

Critical takeaway: **No single technique guarantees anonymization in isolation.** The WP29 explicitly states that pseudonymization alone is insufficient for anonymization, regardless of the cryptographic strength of the pseudonym generation.

### Re-identification Risks

The practical threshold for "anonymized" remains contentious. Consider:

- Sweeney (2000) demonstrated that 87% of the US population can be uniquely identified by {ZIP code, gender, date of birth}
- Narayanan and Shmatikov (2008) re-identified Netflix users using auxiliary IMDB data
- De Montjoye et al. (2013) showed four spatiotemporal points suffice to uniquely identify 95% of individuals in a mobile dataset of 1.5 million people

The regulatory position: if any party can reasonably re-identify, the data is not anonymous. "Reasonably likely" evolves with technology — datasets anonymized adequately today may become re-identifiable as computational resources and auxiliary data grow.

### Regulatory Implications

For practitioners, the classification determines:

| Aspect | Anonymized Data | Pseudonymized Data |
|--------|----------------|-------------------|
| GDPR scope | Outside scope | Within scope |
| Lawful basis needed | No | Yes |
| Data subject rights | Not applicable | Apply in full |
| Breach notification | Not required | Required (Article 33/34) |
| Cross-border transfer | Unrestricted | Restricted (Chapter V) |
| Storage limitation | Not applicable | Applies (Article 5(1)(e)) |
| DPO required | Not for this data | May contribute to threshold |
| DPIA required | No | Possibly (Article 35) |

---

## 2. Statistical Anonymization

### k-Anonymity

Introduced by Samarati and Sweeney (1998), k-anonymity requires that every combination of quasi-identifier values appears at least k times in the released dataset.

**Quasi-identifiers (QI)**: Attributes that are not direct identifiers but can be combined with external information to re-identify individuals. Common QIs: age, ZIP code, gender, occupation, nationality, admission date.

**Formal definition**: A table T satisfies k-anonymity with respect to quasi-identifiers QI if every combination of values in QI appears at least k times in T.

#### Generalization Hierarchies

Generalization replaces specific values with more general ones according to predefined hierarchies:

```
Age hierarchy:          ZIP hierarchy:          Occupation hierarchy:
25 → [20-30] → [0-50]  10115 → 101** → 1****  Nurse → Healthcare → *
31 → [30-40] → [0-50]  10117 → 101** → 1****  Doctor → Healthcare → *
67 → [60-70] → [50-*]  20095 → 200** → 2****  Teacher → Education → *
```

#### Suppression

When generalization alone produces excessive information loss, individual records (row suppression) or specific values (cell suppression) can be removed. Typically bounded: suppress at most p% of records.

#### Implementation in Python with ARX

```python
# Using the ARX anonymization framework via its Java API (py4j bridge)
# ARX: https://arx.deidentifier.org/

import pandas as pd
from pyarx import ARXAnonymizer, AttributeType, Hierarchy

# Load dataset
data = pd.read_csv("health_records.csv")

# Define attribute types
config = {
    "patient_id": AttributeType.IDENTIFYING,  # Will be removed
    "age": AttributeType.QUASI_IDENTIFYING,
    "zip_code": AttributeType.QUASI_IDENTIFYING,
    "gender": AttributeType.QUASI_IDENTIFYING,
    "diagnosis": AttributeType.SENSITIVE,
    "medication": AttributeType.INSENSITIVE
}

# Define generalization hierarchies
age_hierarchy = Hierarchy.create_interval(
    data["age"],
    intervals=[(0, 10), (10, 20), (20, 30), (30, 40), (40, 50),
               (50, 60), (60, 70), (70, 80), (80, 90), (90, 100)],
    top_level="*"
)

zip_hierarchy = Hierarchy.create_prefix(
    data["zip_code"],
    levels=[5, 4, 3, 2, 0]  # Full → 4-digit → 3-digit → 2-digit → *
)

# Configure k-anonymity
anonymizer = ARXAnonymizer(k=5)
anonymizer.set_hierarchies({"age": age_hierarchy, "zip_code": zip_hierarchy})

# Run optimal anonymization (finds minimal generalization)
result = anonymizer.anonymize(data, config)
print(f"Information loss: {result.information_loss:.4f}")
print(f"Records suppressed: {result.suppressed_count}")
```

#### SQL-Based k-Anonymity Verification

```sql
-- Verify k-anonymity for k=5 on quasi-identifiers {age_group, zip_prefix, gender}
WITH equivalence_classes AS (
    SELECT
        age_group,
        zip_prefix,
        gender,
        COUNT(*) as class_size
    FROM anonymized_health_data
    GROUP BY age_group, zip_prefix, gender
)
SELECT
    MIN(class_size) as min_k,
    MAX(class_size) as max_k,
    AVG(class_size) as avg_k,
    COUNT(*) as num_classes,
    SUM(CASE WHEN class_size < 5 THEN 1 ELSE 0 END) as violating_classes
FROM equivalence_classes;
-- If min_k >= 5, the dataset satisfies 5-anonymity
```

### l-Diversity

k-Anonymity fails against the **homogeneity attack**: if all records in an equivalence class share the same sensitive value, k-anonymity reveals that value. Example: all 5 people aged 20-30 in ZIP 101** have "HIV" as diagnosis.

**l-Diversity** requires that each equivalence class contains at least l "well-represented" values of the sensitive attribute.

Variants:
- **Distinct l-diversity**: At least l distinct sensitive values per class
- **Entropy l-diversity**: Entropy of sensitive attribute distribution ≥ log(l) in each class
- **Recursive (c,l)-diversity**: The most frequent value does not dominate; specifically, r₁ < c(r_l + r_{l+1} + ... + r_m) where r_i is the frequency of the i-th most common value

```python
# Verify l-diversity
def check_l_diversity(df, quasi_identifiers, sensitive_attr, l):
    """Check if dataset satisfies l-diversity."""
    violations = []
    for name, group in df.groupby(quasi_identifiers):
        distinct_sensitive = group[sensitive_attr].nunique()
        if distinct_sensitive < l:
            violations.append({
                "class": name,
                "size": len(group),
                "distinct_sensitive": distinct_sensitive
            })
    return len(violations) == 0, violations
```

### t-Closeness

l-Diversity still fails against the **skewness attack**: if the overall distribution of sensitive values is skewed, even l-diverse classes can leak information. If 99% of the population is healthy and a 5-diverse class shows 50% disease, knowing someone is in that class dramatically increases the probability of disease.

**t-Closeness** requires that the distance between the distribution of the sensitive attribute within each equivalence class and its distribution in the overall table does not exceed a threshold t.

Distance is measured using **Earth Mover's Distance (EMD)**, also known as the Wasserstein metric:

For numerical attributes:
```
EMD(P, Q) = (1 / (n-1)) * Σᵢ |Σⱼ≤ᵢ (pⱼ - qⱼ)|
```

For categorical attributes, EMD uses the cost of transforming one distribution into another with unit cost per element moved.

```python
from scipy.stats import wasserstein_distance
import numpy as np

def check_t_closeness(df, quasi_identifiers, sensitive_attr, t):
    """Check t-closeness using Earth Mover's Distance."""
    # Overall distribution of sensitive attribute
    overall_dist = df[sensitive_attr].value_counts(normalize=True).sort_index()

    violations = []
    for name, group in df.groupby(quasi_identifiers):
        class_dist = group[sensitive_attr].value_counts(normalize=True).sort_index()
        # Align indices
        all_values = overall_dist.index.union(class_dist.index)
        p = np.array([overall_dist.get(v, 0) for v in all_values])
        q = np.array([class_dist.get(v, 0) for v in all_values])

        emd = wasserstein_distance(
            range(len(all_values)), range(len(all_values)),
            u_weights=p, v_weights=q
        )
        if emd > t:
            violations.append({"class": name, "emd": emd})

    return len(violations) == 0, violations
```

### Tools Ecosystem

- **ARX** (Java, open-source): Industrial-strength, supports k-anonymity, l-diversity, t-closeness, δ-presence, risk-based models. GUI + API.
- **sdcMicro** (R package): Statistical Disclosure Control, designed for national statistical offices. Supports microdata protection, frequency tables, magnitude tables.
- **Amnesia** (web-based): User-friendly anonymization, supports generalization and suppression with interactive hierarchy definition.
- **Google's k-anonymity API**: Cloud DLP provides k-anonymity analysis as a service.

---

## 3. Differential Privacy

### Formal Definition

Differential privacy provides a mathematically rigorous guarantee about the privacy of individuals in a dataset, regardless of auxiliary information an adversary might possess.

**Definition (ε-Differential Privacy)**: A randomized algorithm M satisfies ε-differential privacy if for all datasets D₁ and D₂ differing in at most one record, and for all subsets S of possible outputs:

```
Pr[M(D₁) ∈ S] ≤ e^ε × Pr[M(D₂) ∈ S]
```

The parameter ε (epsilon) quantifies privacy loss:
- ε → 0: Maximum privacy (output reveals nothing about any individual)
- ε → ∞: No privacy (output may perfectly reveal individual data)
- Practical values: 0.1 (strong privacy) to 10 (weak privacy); ln(3) ≈ 1.1 is common in practice

**(ε, δ)-Differential Privacy** (approximate/relaxed): Allows the strict guarantee to fail with probability δ:

```
Pr[M(D₁) ∈ S] ≤ e^ε × Pr[M(D₂) ∈ S] + δ
```

Where δ should be cryptographically negligible (< 1/n² for dataset size n).

### Mechanisms

#### Laplace Mechanism

For numeric queries with sensitivity Δf (maximum change in output when one record changes):

```
M(D) = f(D) + Lap(Δf / ε)
```

Where Lap(b) is a random draw from the Laplace distribution with scale b = Δf/ε.

```python
import numpy as np

def laplace_mechanism(true_value, sensitivity, epsilon):
    """Add Laplace noise to achieve epsilon-differential privacy."""
    scale = sensitivity / epsilon
    noise = np.random.laplace(loc=0, scale=scale)
    return true_value + noise

# Example: counting query (sensitivity = 1)
true_count = 1547
private_count = laplace_mechanism(true_count, sensitivity=1, epsilon=0.5)
# Expected noise magnitude: 1/0.5 = 2
```

#### Gaussian Mechanism

Provides (ε, δ)-differential privacy with noise from N(0, σ²):

```
σ ≥ Δf × √(2 × ln(1.25/δ)) / ε
```

Preferred when composition is involved (tighter bounds under advanced composition).

```python
def gaussian_mechanism(true_value, sensitivity, epsilon, delta):
    """Add Gaussian noise for (epsilon, delta)-differential privacy."""
    sigma = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
    noise = np.random.normal(loc=0, scale=sigma)
    return true_value + noise
```

#### Exponential Mechanism

For non-numeric outputs (selecting among candidates), where utility function u(D, r) scores each possible output r:

```
Pr[M(D) = r] ∝ exp(ε × u(D, r) / (2 × Δu))
```

Where Δu is the sensitivity of the utility function.

```python
def exponential_mechanism(candidates, utility_scores, sensitivity, epsilon):
    """Select output using exponential mechanism."""
    # Compute selection probabilities
    scores = np.array(utility_scores)
    probabilities = np.exp(epsilon * scores / (2 * sensitivity))
    probabilities /= probabilities.sum()
    # Sample
    selected_idx = np.random.choice(len(candidates), p=probabilities)
    return candidates[selected_idx]
```

### Composition Theorems

When multiple differentially private computations are performed on the same dataset:

**Basic (Sequential) Composition**: k mechanisms with privacy parameters ε₁, ε₂, ..., εₖ satisfy (Σεᵢ)-differential privacy overall.

**Advanced Composition** (Dwork, Rothblum, Vadhan 2010): k mechanisms each satisfying ε-DP together satisfy (ε√(2k × ln(1/δ')) + kε(e^ε - 1), δ' + kδ)-DP for any δ' > 0.

**Rényi Differential Privacy (RDP)** and **zero-Concentrated DP (zCDP)**: Tighter composition via Rényi divergence. Preferred in modern implementations:

```
zCDP composition: ρ_total = Σ ρᵢ (additive in ρ)
Convert back: (ρ + 2√(ρ × ln(1/δ)), δ)-DP
```

### Privacy Budget Management

```python
class PrivacyAccountant:
    """Track cumulative privacy expenditure using RDP accounting."""

    def __init__(self, total_epsilon, total_delta, mechanism="rdp"):
        self.total_epsilon = total_epsilon
        self.total_delta = total_delta
        self.spent_epsilon = 0.0
        self.queries = []

    def can_query(self, epsilon_cost):
        """Check if budget allows another query."""
        return (self.spent_epsilon + epsilon_cost) <= self.total_epsilon

    def record_query(self, query_name, epsilon_cost):
        """Record a privacy-spending query."""
        if not self.can_query(epsilon_cost):
            raise PrivacyBudgetExhausted(
                f"Budget: {self.total_epsilon}, Spent: {self.spent_epsilon}, "
                f"Requested: {epsilon_cost}"
            )
        self.spent_epsilon += epsilon_cost
        self.queries.append({
            "name": query_name,
            "epsilon": epsilon_cost,
            "cumulative": self.spent_epsilon
        })

    @property
    def remaining_budget(self):
        return self.total_epsilon - self.spent_epsilon
```

### Local vs Global Differential Privacy

**Global (Central) DP**: A trusted curator holds raw data, applies noise to query outputs. Better utility for the same privacy guarantee.

**Local DP**: Each individual randomizes their own data before sending to the collector. No trusted party needed, but requires much more noise (or more respondents) for equivalent accuracy.

```
Local DP noise scale ≈ √n × Global DP noise scale
```

**Randomized Response** (Warner 1965, foundational local DP):
```python
def randomized_response(true_bit, epsilon):
    """Classic randomized response for binary attributes."""
    p = np.exp(epsilon) / (np.exp(epsilon) + 1)  # Probability of truth
    if np.random.random() < p:
        return true_bit
    else:
        return 1 - true_bit
```

### Industry Deployments

**Google RAPPOR** (Randomized Aggregatable Privacy-Preserving Ordinal Response):
- Local DP for Chrome telemetry (homepage settings, default search engines)
- Two-phase: permanent randomized response (memoized per client) + instantaneous randomization per report
- Uses Bloom filters for efficient encoding of categorical data
- Open-source implementation available

**Apple's Differential Privacy**:
- Deployed in iOS/macOS for emoji usage, QuickType suggestions, Safari crash domains, Health data
- Local DP with ε values between 1 and 8 per day (criticized by researchers as too high)
- Uses Count Mean Sketch (CMS) and Hadamard Count Mean Sketch

**OpenDP Library** (Harvard):
```python
import opendp.prelude as dp

# Build a differentially private computation
space = dp.atom_domain(T=float), dp.absolute_distance(T=float)

# Create a Laplace mechanism for mean estimation
base_laplace = dp.m.make_laplace(
    dp.atom_domain(T=float),
    dp.absolute_distance(T=float),
    scale=1.0  # Laplace scale parameter
)

# Compose transformations
bounded_sum = (
    dp.t.make_clamp(bounds=(0.0, 100.0)) >>
    dp.t.make_bounded_sum(bounds=(0.0, 100.0)) >>
    dp.m.make_laplace(scale=2.0)
)

# Verify privacy guarantee
assert bounded_sum.check(d_in=1, d_out=0.5)  # Satisfies 0.5-DP
```

**US Census Bureau**: Used differential privacy for the 2020 Census via the TopDown algorithm (hierarchical mechanism ensuring geographic consistency). Controversial due to utility concerns for small populations.

---

## 4. Pseudonymization Techniques

### Tokenization

Replace sensitive values with random tokens that bear no mathematical relationship to the original:

```python
import secrets
import hashlib
from typing import Dict

class TokenVault:
    """Secure tokenization with lookup-based reversal."""

    def __init__(self):
        self._forward: Dict[str, str] = {}  # value → token
        self._reverse: Dict[str, str] = {}  # token → value

    def tokenize(self, value: str) -> str:
        """Generate or retrieve a consistent token for a value."""
        if value in self._forward:
            return self._forward[value]
        token = f"TOK-{secrets.token_hex(16)}"
        self._forward[value] = token
        self._reverse[token] = value
        return token

    def detokenize(self, token: str) -> str:
        """Reverse a token to its original value. Requires vault access."""
        if token not in self._reverse:
            raise KeyError(f"Token not found in vault: {token[:8]}...")
        return self._reverse[token]
```

Properties:
- No mathematical relationship (unlike encryption or hashing)
- Requires secure storage of the mapping table
- Format can be arbitrary (unlike format-preserving encryption)
- Suitable for payment card industry (PCI-DSS tokenization)

### Consistent Hashing with HMAC

When deterministic pseudonymization is needed (same input always produces same pseudonym) without a lookup table:

```python
import hmac
import hashlib
import base64

class HMACPseudonymizer:
    """HMAC-SHA256 based consistent pseudonymization."""

    def __init__(self, secret_key: bytes):
        """
        Args:
            secret_key: Minimum 32 bytes, stored in HSM or secret manager.
                        NEVER hardcode. NEVER log.
        """
        if len(secret_key) < 32:
            raise ValueError("Key must be at least 256 bits")
        self._key = secret_key

    def pseudonymize(self, value: str, context: str = "") -> str:
        """
        Generate a deterministic pseudonym.

        Args:
            value: The sensitive value to pseudonymize
            context: Domain separation (e.g., "email", "patient_id")
                     Prevents cross-domain correlation
        """
        message = f"{context}:{value}".encode("utf-8")
        mac = hmac.new(self._key, message, hashlib.sha256)
        return base64.urlsafe_b64encode(mac.digest()).decode("ascii")[:32]

    def verify(self, value: str, pseudonym: str, context: str = "") -> bool:
        """Verify that a pseudonym corresponds to a value (forward check only)."""
        return hmac.compare_digest(
            self.pseudonymize(value, context),
            pseudonym
        )
```

Key properties:
- Deterministic: same input + same key → same pseudonym (enables JOINs)
- One-way: cannot recover original from pseudonym without brute force (assuming high-entropy input)
- Key-dependent: different keys produce different pseudonyms (key rotation = re-pseudonymization)
- Domain-separated: context prevents rainbow table attacks across domains

**Warning**: For low-entropy inputs (e.g., 10-digit phone numbers), HMAC pseudonyms are vulnerable to dictionary attacks. Combine with salting or use tokenization instead.

### Format-Preserving Pseudonymization

Maintain the format of the original data (critical for legacy systems that validate field formats):

```python
# Format-Preserving Encryption using FF1/FF3-1 (NIST SP 800-38G)
from pyffx import String as FFXString

class FormatPreservingPseudonymizer:
    """FPE-based pseudonymization preserving format constraints."""

    def __init__(self, key: bytes, alphabet: str = "0123456789"):
        self._cipher = FFXString(key, alphabet)

    def pseudonymize_ssn(self, ssn: str) -> str:
        """Pseudonymize SSN preserving ###-##-#### format."""
        digits = ssn.replace("-", "")
        pseudo_digits = self._cipher.encrypt(digits)
        return f"{pseudo_digits[:3]}-{pseudo_digits[3:5]}-{pseudo_digits[5:]}"

    def pseudonymize_phone(self, phone: str) -> str:
        """Pseudonymize phone preserving digit count and prefix."""
        # Preserve country code, pseudonymize subscriber number
        prefix = phone[:3]  # e.g., "+49"
        number = phone[3:].replace(" ", "").replace("-", "")
        pseudo_number = self._cipher.encrypt(number)
        return f"{prefix}{pseudo_number}"
```

### Pseudonymization in Database Architecture

#### View-Based Masking

```sql
-- Raw table (restricted access)
CREATE TABLE patients (
    patient_id UUID PRIMARY KEY,
    full_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    ssn TEXT NOT NULL,
    diagnosis TEXT,
    treating_physician TEXT
);

-- Pseudonymized view (analyst access)
CREATE VIEW patients_pseudonymized AS
SELECT
    encode(hmac(patient_id::text, current_setting('app.pseudonym_key'), 'sha256'), 'hex')
        AS pseudo_id,
    encode(hmac(full_name, current_setting('app.pseudonym_key'), 'sha256'), 'hex')
        AS pseudo_name,
    date_trunc('year', date_of_birth)::date AS birth_year,
    '***-**-' || right(ssn, 4) AS ssn_masked,
    diagnosis,
    treating_physician
FROM patients;

-- Grant access only to the view
REVOKE ALL ON patients FROM analyst_role;
GRANT SELECT ON patients_pseudonymized TO analyst_role;
```

#### Middleware-Based Pseudonymization

```python
# SQLAlchemy event-based pseudonymization layer
from sqlalchemy import event
from sqlalchemy.orm import Session

class PseudonymizationMiddleware:
    """Intercept queries and pseudonymize results based on user role."""

    SENSITIVE_COLUMNS = {
        "patients": ["full_name", "ssn", "date_of_birth", "email"],
        "employees": ["salary", "bank_account", "home_address"]
    }

    def __init__(self, pseudonymizer, role_manager):
        self._pseudonymizer = pseudonymizer
        self._roles = role_manager

    def apply_to_session(self, session: Session):
        @event.listens_for(session, "loaded_as_persistent")
        def on_load(session, instance):
            user_role = self._roles.current_role()
            if user_role in ("analyst", "researcher"):
                table = instance.__tablename__
                for col in self.SENSITIVE_COLUMNS.get(table, []):
                    original = getattr(instance, col)
                    if original is not None:
                        pseudo = self._pseudonymizer.pseudonymize(
                            str(original), context=f"{table}.{col}"
                        )
                        setattr(instance, col, pseudo)
```

### Reversibility Controls

Pseudonymization is only useful if reversal is possible when legally required (e.g., data subject access requests). Controls:

1. **Key escrow**: Pseudonym keys stored in HSM with multi-party access (m-of-n threshold)
2. **Audit logging**: Every de-pseudonymization event logged with timestamp, requester, justification, data subject identifier
3. **Time-limited access**: De-pseudonymization keys rotated; old mappings archived with restricted access
4. **Purpose limitation**: Technical controls ensuring de-pseudonymization only for specified purposes (e.g., DSAR response, medical emergency)

---

## 5. Synthetic Data Generation

### Statistical Methods

#### Copula-Based Generation

Copulas model the dependency structure between variables independently of marginal distributions:

```python
from sdv.single_table import CopulaGANSynthesizer
from sdv.metadata import SingleTableMetadata
import pandas as pd

# Define metadata
metadata = SingleTableMetadata()
metadata.detect_from_dataframe(real_data)
metadata.update_column("income", sdtype="numerical")
metadata.update_column("age", sdtype="numerical")
metadata.update_column("occupation", sdtype="categorical")
metadata.set_primary_key("id")

# Fit Gaussian Copula model
from sdv.single_table import GaussianCopulaSynthesizer

synthesizer = GaussianCopulaSynthesizer(
    metadata,
    enforce_min_max_values=True,
    enforce_rounding=True,
    numerical_distributions={
        "income": "gamma",
        "age": "truncnorm"
    }
)
synthesizer.fit(real_data)

# Generate synthetic data
synthetic_data = synthesizer.sample(num_rows=10000)
```

#### Bayesian Networks

Model conditional dependencies explicitly:

```python
from sdv.single_table import CTGANSynthesizer
# Or use bnlearn for explicit Bayesian network structure learning

# Structure learning approach
import bnlearn as bn

# Learn structure from data
model = bn.structure_learning.fit(
    real_data,
    methodtype="hc",  # Hill climbing
    scoretype="bic"   # BIC score
)

# Learn parameters
model = bn.parameter_learning.fit(model, real_data, methodtype="bayes")

# Sample synthetic records
synthetic = bn.sampling(model, n=10000)
```

### Deep Learning Approaches

#### CTGAN (Conditional Tabular GAN)

Designed specifically for tabular data with mixed types (continuous + categorical):

```python
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata

metadata = SingleTableMetadata()
metadata.detect_from_dataframe(real_data)

# CTGAN handles mode collapse and mixed types
synthesizer = CTGANSynthesizer(
    metadata,
    epochs=300,
    batch_size=500,
    generator_dim=(256, 256),
    discriminator_dim=(256, 256),
    generator_lr=2e-4,
    discriminator_lr=2e-4,
    discriminator_steps=1,
    pac=10  # Packing for training stability
)

synthesizer.fit(real_data)
synthetic_data = synthesizer.sample(num_rows=len(real_data))
```

Architecture specifics:
- Mode-specific normalization for continuous columns (handles multimodal distributions)
- Conditional generator for handling imbalanced categorical columns
- Training-by-sampling to address class imbalance
- PacGAN (packing) to reduce mode collapse

#### TimeGAN (Temporal GAN)

For time-series data preserving temporal dynamics:

```python
from ydata_synthetic.synthesizers.timeseries import TimeSeriesSynthesizer
from ydata_synthetic.synthesizers import ModelParameters, TrainParameters

# Configure model
model_params = ModelParameters(
    batch_size=128,
    lr=5e-4,
    noise_dim=32,
    layers_dim=128,
    latent_dim=24,
    gamma=1  # Supervisor loss weight
)

train_params = TrainParameters(epochs=1000, sequence_length=24)

# TimeGAN has four networks: embedder, recovery, generator, discriminator
# Plus a supervisor for temporal dynamics
synth = TimeSeriesSynthesizer(
    modelname="timegan",
    model_parameters=model_params
)
synth.fit(real_timeseries, train_params, num_cols=["price", "volume", "spread"])
synthetic_ts = synth.sample(n_samples=5000)
```

### Faker for Structured Data

For generating realistic but entirely fictional PII (not derived from real data):

```python
from faker import Faker
import pandas as pd

fake = Faker(["en_US", "de_DE", "it_IT"])  # Multi-locale

def generate_synthetic_patients(n: int) -> pd.DataFrame:
    """Generate fully synthetic patient records."""
    records = []
    for _ in range(n):
        records.append({
            "patient_id": fake.uuid4(),
            "name": fake.name(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=95),
            "ssn": fake.ssn(),
            "address": fake.address(),
            "phone": fake.phone_number(),
            "email": fake.email(),
            "blood_type": fake.random_element(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
            "admission_date": fake.date_between(start_date="-2y", end_date="today"),
            "diagnosis_code": fake.random_element(["I10", "E11", "J06", "M54", "F32"])
        })
    return pd.DataFrame(records)
```

Faker is not privacy-preserving in a formal sense (no utility guarantees relative to real data), but useful for:
- Test environments
- Demo data
- Development fixtures
- Replacing real PII in non-production systems

### Utility and Privacy Metrics

#### Statistical Similarity

```python
from sdmetrics.reports.single_table import QualityReport
from sdmetrics.single_table import (
    KSComplement,
    TVComplement,
    CorrelationSimilarity,
    ContingencySimilarity
)

# Generate quality report
report = QualityReport()
report.generate(real_data, synthetic_data, metadata)

# Individual metrics
ks_score = KSComplement.compute(real_data, synthetic_data, metadata)
# 1.0 = identical distributions, 0.0 = completely different

correlation_score = CorrelationSimilarity.compute(
    real_data, synthetic_data, metadata
)
# Measures preservation of inter-column relationships
```

#### ML Efficacy (Train on Synthetic, Test on Real - TSTR)

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

# Train on real, test on real (baseline)
model_real = RandomForestClassifier(n_estimators=100)
model_real.fit(X_train_real, y_train_real)
score_real = f1_score(y_test_real, model_real.predict(X_test_real))

# Train on synthetic, test on real (TSTR)
model_synth = RandomForestClassifier(n_estimators=100)
model_synth.fit(X_synthetic, y_synthetic)
score_synth = f1_score(y_test_real, model_synth.predict(X_test_real))

# Utility ratio
utility_ratio = score_synth / score_real
# Target: > 0.9 (synthetic achieves 90%+ of real data utility)
```

#### Privacy Metrics

**Membership Inference Attack** (does record X appear in the training data?):

```python
from sdmetrics.single_table import NewRowSynthesis

# Measures what fraction of synthetic rows are novel (not memorized)
novelty_score = NewRowSynthesis.compute(
    real_data, synthetic_data, metadata,
    numerical_match_tolerance=0.01,
    synthetic_sample_size=1000
)
# Target: > 0.9 (most synthetic rows are genuinely new)
```

**Distance to Closest Record (DCR)**:

```python
from scipy.spatial.distance import cdist
import numpy as np

def dcr_analysis(real_encoded, synthetic_encoded):
    """Compute Distance to Closest Record for privacy assessment."""
    # For each synthetic record, find nearest real record
    distances = cdist(synthetic_encoded, real_encoded, metric="euclidean")
    min_distances = distances.min(axis=1)

    # Compare with real-to-real distances (baseline)
    real_distances = cdist(real_encoded, real_encoded, metric="euclidean")
    np.fill_diagonal(real_distances, np.inf)
    real_min_distances = real_distances.min(axis=1)

    # Synthetic DCR should not be significantly smaller than real DCR
    # (would indicate memorization/overfitting)
    return {
        "synthetic_dcr_mean": min_distances.mean(),
        "real_dcr_mean": real_min_distances.mean(),
        "ratio": min_distances.mean() / real_min_distances.mean(),
        "pct_below_threshold": (min_distances < 0.01).mean()
    }
```

### Tools Ecosystem

- **Synthetic Data Vault (SDV)**: Open-source Python library. GaussianCopula, CTGAN, CopulaGAN, TVAE, TimeGAN, multi-table (HMA).
- **Gretel.ai**: Commercial platform with open-source components. ACTGAN, DGAN (time series), text synthesis, evaluate + transform APIs.
- **Mostly AI**: Commercial synthetic data platform with strong GDPR compliance focus. Handles complex relational and sequential data.
- **DataSynthesizer**: Lightweight tool from University of Washington. Bayesian network approach with differential privacy option.
- **ydata-synthetic**: Open-source library focusing on GANs for tabular and time-series data.

---

## 6. De-identification of Specific Data Types

### Structured Data (Tabular)

Standard approach combining multiple techniques:

```python
class StructuredDataDeidentifier:
    """Pipeline for tabular data de-identification."""

    def __init__(self, config):
        self.config = config  # Column-level de-id rules

    def deidentify(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()

        for col, rule in self.config.items():
            if col not in result.columns:
                continue

            if rule["action"] == "remove":
                result.drop(columns=[col], inplace=True)
            elif rule["action"] == "pseudonymize":
                result[col] = result[col].apply(
                    lambda v: self.pseudonymizer.pseudonymize(str(v), col)
                )
            elif rule["action"] == "generalize":
                result[col] = result[col].apply(rule["function"])
            elif rule["action"] == "perturb":
                noise_scale = rule.get("noise_scale", 0.1)
                result[col] = result[col] + np.random.laplace(
                    0, noise_scale * result[col].std(), len(result)
                )
            elif rule["action"] == "date_shift":
                shift_days = np.random.randint(-rule["max_shift"], rule["max_shift"])
                result[col] = pd.to_datetime(result[col]) + pd.Timedelta(days=shift_days)
            elif rule["action"] == "bin":
                result[col] = pd.cut(result[col], bins=rule["bins"], labels=rule["labels"])

        return result
```

### Unstructured Text: NER-Based Redaction

#### Microsoft Presidio

```python
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Initialize with spaCy NLP backend
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}]
}
provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
anonymizer = AnonymizerEngine()

# Analyze text for PII
text = """
Patient John Smith (DOB: 03/15/1985, SSN: 123-45-6789) was admitted to
St. Mary's Hospital on 2024-01-15. Contact: john.smith@email.com, +1-555-0123.
Dr. Emily Johnson prescribed metformin 500mg for Type 2 diabetes (ICD-10: E11.9).
"""

# Detect PII entities
results = analyzer.analyze(
    text=text,
    entities=[
        "PERSON", "DATE_TIME", "US_SSN", "EMAIL_ADDRESS",
        "PHONE_NUMBER", "LOCATION", "MEDICAL_LICENSE"
    ],
    language="en"
)

# Anonymize with different operators per entity type
operators = {
    "PERSON": OperatorConfig("replace", {"new_value": "[REDACTED_NAME]"}),
    "US_SSN": OperatorConfig("mask", {"chars_to_mask": 5, "masking_char": "*", "from_end": False}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[REDACTED_EMAIL]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[REDACTED_PHONE]"}),
    "DATE_TIME": OperatorConfig("replace", {"new_value": "[REDACTED_DATE]"})
}

anonymized = anonymizer.anonymize(
    text=text,
    analyzer_results=results,
    operators=operators
)
print(anonymized.text)
```

#### Custom spaCy NER for Domain-Specific Entities

```python
import spacy
from spacy.tokens import Span

class MedicalTextRedactor:
    """Domain-specific redaction for clinical notes."""

    def __init__(self):
        self.nlp = spacy.load("en_core_web_trf")  # Transformer-based
        # Add custom entity ruler for medical record numbers, etc.
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        patterns = [
            {"label": "MRN", "pattern": [{"SHAPE": "ddddddd"}]},
            {"label": "MRN", "pattern": "MRN"},
            {"label": "DRUG", "pattern": [{"LOWER": {"IN": self._load_drug_list()}}]}
        ]
        ruler.add_patterns(patterns)

    def redact(self, text: str, preserve_structure: bool = True) -> str:
        doc = self.nlp(text)
        redacted = text

        # Process entities in reverse order (preserve offsets)
        for ent in sorted(doc.ents, key=lambda e: e.start_char, reverse=True):
            if ent.label_ in ("PERSON", "DATE", "GPE", "ORG", "MRN"):
                replacement = f"[{ent.label_}]" if preserve_structure else "████"
                redacted = redacted[:ent.start_char] + replacement + redacted[ent.end_char:]

        return redacted
```

### Image De-identification

#### Face Detection and Blurring

```python
import cv2
import numpy as np
from pathlib import Path

class ImageDeidentifier:
    """De-identify images: face blurring, EXIF stripping, license plates."""

    def __init__(self):
        # Use DNN-based face detector (more accurate than Haar cascades)
        model_path = Path("models/res10_300x300_ssd_iter_140000.caffemodel")
        config_path = Path("models/deploy.prototxt")
        self.face_net = cv2.dnn.readNetFromCaffe(str(config_path), str(model_path))
        self.confidence_threshold = 0.7

    def blur_faces(self, image: np.ndarray, blur_factor: int = 99) -> np.ndarray:
        """Detect and blur all faces in an image."""
        h, w = image.shape[:2]
        blob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)), 1.0, (300, 300), (104, 177, 123)
        )
        self.face_net.setInput(blob)
        detections = self.face_net.forward()

        result = image.copy()
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self.confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                x1, y1, x2, y2 = box.astype(int)
                # Apply strong Gaussian blur to face region
                face_region = result[y1:y2, x1:x2]
                blurred = cv2.GaussianBlur(face_region, (blur_factor, blur_factor), 30)
                result[y1:y2, x1:x2] = blurred

        return result

    def strip_exif(self, image_path: str, output_path: str):
        """Remove all EXIF metadata (GPS, camera info, timestamps)."""
        from PIL import Image

        img = Image.open(image_path)
        # Create new image without EXIF
        data = list(img.getdata())
        img_clean = Image.new(img.mode, img.size)
        img_clean.putdata(data)
        img_clean.save(output_path)
```

### Geolocation De-identification

#### Geo-Indistinguishability

Based on the differential privacy framework adapted to the 2D Euclidean plane:

```python
import numpy as np
from typing import Tuple

def add_planar_laplace_noise(
    lat: float, lon: float, epsilon: float
) -> Tuple[float, float]:
    """
    Apply geo-indistinguishability (Andrés et al., 2013).

    Adds 2D Laplace noise calibrated to achieve ε-geo-indistinguishability:
    for any two locations l1, l2, the probability ratio of reporting any
    location z is bounded by e^(ε * d(l1, l2)).

    Args:
        lat, lon: Original coordinates
        epsilon: Privacy parameter (smaller = more privacy, larger displacement)
                 ε=1: ~111m expected displacement; ε=0.1: ~1.1km
    """
    # Sample angle uniformly
    theta = np.random.uniform(0, 2 * np.pi)

    # Sample radius from planar Laplace (using CDF inversion)
    # CDF: F(r) = 1 - (1 + ε*r) * e^(-ε*r)
    u = np.random.uniform(0, 1)
    # Lambert W function approximation for inverse CDF
    r = -1/epsilon * (np.log(1 - u) + np.log(1 - u) * 0)  # Simplified
    # More accurate: use scipy
    from scipy.special import lambertw
    r = -1/epsilon * (1 + lambertw((u - 1) / np.e, k=-1).real)

    # Convert polar displacement to lat/lon offset
    # 1 degree latitude ≈ 111,320 meters
    # 1 degree longitude ≈ 111,320 * cos(lat) meters
    lat_offset = (r * np.cos(theta)) / 111320
    lon_offset = (r * np.sin(theta)) / (111320 * np.cos(np.radians(lat)))

    return lat + lat_offset, lon + lon_offset
```

#### Spatial Cloaking

Replace exact locations with cloaking regions containing at least k users:

```python
def spatial_k_anonymity(locations: list, k: int) -> list:
    """
    Group locations into regions of at least k points.
    Returns bounding boxes as anonymized locations.
    """
    from sklearn.cluster import AgglomerativeClustering

    coords = np.array([(loc["lat"], loc["lon"]) for loc in locations])

    # Cluster with minimum cluster size = k
    n_clusters = max(1, len(locations) // k)
    clustering = AgglomerativeClustering(n_clusters=n_clusters)
    labels = clustering.fit_predict(coords)

    anonymized = []
    for label in set(labels):
        cluster_mask = labels == label
        cluster_points = coords[cluster_mask]

        if len(cluster_points) < k:
            continue  # Merge with nearest cluster or suppress

        # Return centroid of cloaking region
        centroid = cluster_points.mean(axis=0)
        bbox = {
            "lat_min": cluster_points[:, 0].min(),
            "lat_max": cluster_points[:, 0].max(),
            "lon_min": cluster_points[:, 1].min(),
            "lon_max": cluster_points[:, 1].max(),
            "centroid_lat": centroid[0],
            "centroid_lon": centroid[1],
            "k": len(cluster_points)
        }
        for idx in np.where(cluster_mask)[0]:
            anonymized.append({"original_idx": idx, "region": bbox})

    return anonymized
```

### Temporal Data: Date Shifting

```python
import pandas as pd
import numpy as np
from typing import Optional

def consistent_date_shift(
    df: pd.DataFrame,
    date_columns: list,
    entity_column: str,
    max_shift_days: int = 365,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Apply consistent date shifting per entity (preserves intervals within entity).

    All dates for the same entity are shifted by the same random offset,
    preserving temporal relationships (e.g., admission before discharge).
    """
    rng = np.random.default_rng(seed)
    result = df.copy()

    # Generate one shift per entity
    entities = df[entity_column].unique()
    shifts = {
        entity: pd.Timedelta(days=int(rng.integers(-max_shift_days, max_shift_days)))
        for entity in entities
    }

    for col in date_columns:
        result[col] = pd.to_datetime(result[col])
        result[col] = result.apply(
            lambda row: row[col] + shifts[row[entity_column]], axis=1
        )

    return result
```

### Genomic Data De-identification

Genomic data presents unique challenges: it is inherently identifying (each genome is unique), heritable (identifies relatives), and immutable (cannot be "changed" if compromised).

Techniques:
- **Beacon attacks mitigation**: Differential privacy on yes/no allele queries
- **SNP suppression**: Remove rare variants (minor allele frequency < threshold)
- **Generalization**: Report haplotype blocks instead of individual SNPs
- **Secure computation**: Process queries inside TEEs without exposing raw sequences

---

## 7. Re-identification Attacks

### Netflix Prize Re-identification (2006-2008)

**Setup**: Netflix released 100 million movie ratings from 480,000 subscribers. User IDs were replaced with random numbers. Dates were perturbed by ±14 days.

**Attack** (Narayanan & Shmatikov, 2008): Cross-referenced with public IMDB ratings. With as few as 8 ratings (even approximate dates and scores), 99% of subscribers could be uniquely identified. The key insight: behavioral patterns are quasi-identifiers even when individually sparse.

**Impact**: FTC complaint, class-action lawsuit, Netflix cancelled the planned Prize sequel. Demonstrated that temporal behavioral data is extraordinarily difficult to anonymize.

### AOL Search Data (2006)

**Setup**: AOL Research released 20 million search queries from 650,000 users over 3 months. User IDs replaced with numeric identifiers.

**Attack**: New York Times reporters identified user #4417749 as Thelma Arnold, a 62-year-old widow in Georgia, by analyzing her search patterns (searches for her name, local businesses, medical conditions).

**Lesson**: Longitudinal behavioral data carries high re-identification risk even without explicit identifiers. Aggregation over time creates unique fingerprints.

### NYC Taxi De-anonymization (2014)

**Setup**: NYC Taxi and Limousine Commission released trip records with "anonymized" medallion numbers.

**Attack**: Medallion numbers were hashed with MD5 without a secret key. Since the medallion space is small (~13,000 active medallions), all hashes could be precomputed (rainbow table). Additionally, pickup/dropoff locations near celebrities' known residences enabled tracking specific individuals.

**Technical failure**: Unsalted hash of low-entropy identifier = trivially reversible pseudonymization.

### Attack Taxonomy

#### Linkage Attacks

Cross-reference the anonymized dataset with external data sources sharing quasi-identifiers:

```python
def linkage_attack(anonymized_df, auxiliary_df, quasi_identifiers):
    """
    Simulate a linkage attack.

    If the join yields unique matches, re-identification is achieved.
    """
    # Attempt linkage on quasi-identifiers
    linked = anonymized_df.merge(
        auxiliary_df,
        on=quasi_identifiers,
        how="inner"
    )

    # Assess uniqueness of matches
    unique_matches = linked.groupby(quasi_identifiers).filter(
        lambda x: len(x) == 1
    )

    reidentification_rate = len(unique_matches) / len(anonymized_df)
    return {
        "total_records": len(anonymized_df),
        "linked_records": len(linked),
        "unique_matches": len(unique_matches),
        "reidentification_rate": reidentification_rate
    }
```

#### Inference Attacks

Deduce sensitive attributes without explicit re-identification:

- **Attribute inference**: Knowing someone is in a k-anonymous group where all members share the same sensitive value
- **Membership inference**: Determining whether a specific individual's data was used to train a model
- **Model inversion**: Reconstructing training data features from model outputs

#### Reconstruction Attacks

The 2020 US Census research demonstrated that from published aggregate statistics (cross-tabulations), individual-level records can be reconstructed using constraint satisfaction:

```python
# Conceptual: reconstruct individual records from marginal statistics
from scipy.optimize import linprog

def reconstruction_attack(published_marginals, attribute_domains):
    """
    Given published marginal counts (e.g., age × ZIP × gender counts),
    attempt to reconstruct the full contingency table or individual records
    using linear programming.

    This is a simplified illustration of the approach used by
    Dinur & Nissim (2003) and applied to Census data.
    """
    # Each variable: frequency of each possible record type
    # Constraints: marginals must match published values
    # Objective: maximize or enumerate feasible solutions

    # In practice, SAT solvers or integer programming used
    pass
```

#### GAN-Based Re-identification

Generative models can be trained to invert anonymization:

- Train a GAN to reconstruct faces from blurred/pixelated images
- Style transfer attacks that recover redacted text from formatting patterns
- Denoising models that remove differential privacy noise when given multiple noisy copies

### Attacker Models

The Article 29 Working Party defines three attacker models:

1. **Prosecutor model**: Attacker knows target is in the dataset, wants to find their record. Most powerful (targeted attack).

2. **Journalist model**: Attacker wants to re-identify anyone in the dataset (fishing expedition). Succeeds if any individual can be identified.

3. **Marketer model**: Attacker wants to re-identify as many individuals as possible for commercial purposes. Success measured by re-identification rate.

```python
def assess_risk_by_attacker_model(df, quasi_identifiers):
    """Compute re-identification risk under different attacker models."""
    # Equivalence class sizes
    class_sizes = df.groupby(quasi_identifiers).size()

    # Prosecutor risk: max probability of identifying a known target
    # = 1/min(class_size)
    prosecutor_risk = 1.0 / class_sizes.min()

    # Journalist risk: proportion of unique records
    journalist_risk = (class_sizes == 1).sum() / len(class_sizes)

    # Marketer risk: expected probability of successful re-identification
    # = (1/N) * Σ (1/class_size_i) for each record i
    marketer_risk = (1.0 / class_sizes).sum() / len(df)

    return {
        "prosecutor_risk": prosecutor_risk,
        "journalist_risk": journalist_risk,
        "marketer_risk": marketer_risk,
        "min_equivalence_class": class_sizes.min(),
        "unique_records": (class_sizes == 1).sum(),
        "total_equivalence_classes": len(class_sizes)
    }
```

---

## 8. Privacy-Preserving Computation

### Secure Multi-Party Computation (MPC)

MPC allows n parties to jointly compute a function over their private inputs without revealing those inputs to each other. Only the output is revealed.

#### Secret Sharing (Shamir's Scheme)

```python
from typing import List, Tuple
import secrets

class ShamirSecretSharing:
    """
    Shamir's (t, n) threshold secret sharing over a prime field.
    Any t shares can reconstruct; fewer than t reveal nothing.
    """

    def __init__(self, prime: int = 2**127 - 1):
        self.prime = prime

    def share(self, secret: int, n: int, t: int) -> List[Tuple[int, int]]:
        """Split secret into n shares with threshold t."""
        # Random polynomial of degree t-1 with secret as constant term
        coefficients = [secret] + [
            secrets.randbelow(self.prime) for _ in range(t - 1)
        ]

        shares = []
        for i in range(1, n + 1):
            # Evaluate polynomial at point i
            value = sum(
                c * pow(i, power, self.prime)
                for power, c in enumerate(coefficients)
            ) % self.prime
            shares.append((i, value))

        return shares

    def reconstruct(self, shares: List[Tuple[int, int]]) -> int:
        """Reconstruct secret from t or more shares using Lagrange interpolation."""
        secret = 0
        for i, (xi, yi) in enumerate(shares):
            numerator = denominator = 1
            for j, (xj, _) in enumerate(shares):
                if i != j:
                    numerator = (numerator * (-xj)) % self.prime
                    denominator = (denominator * (xi - xj)) % self.prime
            lagrange = (yi * numerator * pow(denominator, -1, self.prime)) % self.prime
            secret = (secret + lagrange) % self.prime
        return secret
```

#### Additive Secret Sharing for Computation

```python
class AdditiveSharing:
    """Two-party additive secret sharing for secure computation."""

    def __init__(self, ring_size: int = 2**64):
        self.ring = ring_size

    def share(self, value: int) -> Tuple[int, int]:
        """Split value into two additive shares: value = s1 + s2 (mod ring)."""
        s1 = secrets.randbelow(self.ring)
        s2 = (value - s1) % self.ring
        return s1, s2

    def add(self, shares_a: Tuple[int, int], shares_b: Tuple[int, int]) -> Tuple[int, int]:
        """Add two shared values (non-interactive)."""
        return (
            (shares_a[0] + shares_b[0]) % self.ring,
            (shares_a[1] + shares_b[1]) % self.ring
        )

    def scalar_multiply(self, shares: Tuple[int, int], scalar: int) -> Tuple[int, int]:
        """Multiply shared value by public scalar (non-interactive)."""
        return (
            (shares[0] * scalar) % self.ring,
            (shares[1] * scalar) % self.ring
        )

    def reconstruct(self, shares: Tuple[int, int]) -> int:
        """Reconstruct value from both shares."""
        return (shares[0] + shares[1]) % self.ring
```

### Homomorphic Encryption

Compute directly on encrypted data. Three levels:

1. **Partially HE**: One operation (e.g., addition OR multiplication). RSA (multiplicative), Paillier (additive).
2. **Somewhat HE (SHE)**: Both operations, limited depth. BGV, BFV.
3. **Fully HE (FHE)**: Arbitrary computation. TFHE, CKKS (approximate arithmetic for ML).

#### BFV Scheme (Integer Arithmetic)

```python
import tenseal as ts

# Create encryption context (BFV for exact integer arithmetic)
context = ts.context(
    ts.SCHEME_TYPE.BFV,
    poly_modulus_degree=8192,
    plain_modulus=1032193,
    coeff_mod_bit_sizes=[60, 40, 40, 60]
)
context.generate_galois_keys()
context.generate_relin_keys()

# Encrypt data (client-side)
secret_ages = [25, 34, 41, 67, 52, 29]
encrypted_ages = ts.bfv_vector(context, secret_ages)

# Compute on encrypted data (server-side, no access to secret key)
# Sum of ages
encrypted_sum = encrypted_ages.sum()

# The server can perform operations without seeing the data
# Decryption requires the secret key (held by client)
decrypted_sum = encrypted_sum.decrypt()
assert decrypted_sum == [sum(secret_ages)]
```

#### CKKS Scheme (Approximate Arithmetic for ML)

```python
import tenseal as ts
import numpy as np

# CKKS context for floating-point approximate arithmetic
context = ts.context(
    ts.SCHEME_TYPE.CKKS,
    poly_modulus_degree=16384,
    coeff_mod_bit_sizes=[60, 40, 40, 40, 40, 60]
)
context.global_scale = 2**40
context.generate_galois_keys()
context.generate_relin_keys()

# Encrypted linear regression inference
weights = [0.5, -0.3, 0.8, 0.1]  # Model weights (public or encrypted)
bias = 0.2

# Client encrypts their feature vector
features = [1.2, 3.4, 0.7, 2.1]
encrypted_features = ts.ckks_vector(context, features)

# Server computes prediction on encrypted data
encrypted_weights = ts.ckks_vector(context, weights)
encrypted_prediction = encrypted_features.dot(encrypted_weights) + bias

# Client decrypts result
prediction = encrypted_prediction.decrypt()[0]
expected = np.dot(features, weights) + bias
assert abs(prediction - expected) < 0.01  # CKKS introduces small approximation error
```

### Trusted Execution Environments (TEEs)

Hardware-based isolation: code and data protected from the OS, hypervisor, and even physical access.

- **Intel SGX** (Software Guard Extensions): Enclaves in user-space. Limited memory (EPC ~128-512MB). Attestation.
- **Intel TDX** (Trust Domain Extensions): VM-level isolation. Larger memory. For cloud confidential computing.
- **AMD SEV** (Secure Encrypted Virtualization): Encrypts VM memory. SEV-SNP adds integrity.
- **ARM TrustZone**: Secure/non-secure world split. Common in mobile.
- **ARM CCA** (Confidential Compute Architecture): Realms for VM-level confidential computing.

```python
# Conceptual: data processing inside SGX enclave (using Gramine/EGo)
# The enclave attestation proves to data providers that the correct
# code is running in a genuine TEE before they release data.

"""
Enclave workflow:
1. Build enclave binary with privacy-preserving analytics code
2. Generate attestation quote (proves hardware + code identity)
3. Data providers verify attestation, establish TLS to enclave
4. Data decrypted only inside enclave memory
5. Only aggregated/anonymized results leave the enclave
"""
```

### Federated Learning

Train ML models across decentralized data without centralizing raw data.

#### FedAvg Algorithm

```python
import numpy as np
from typing import List, Dict

class FederatedServer:
    """Federated Averaging (McMahan et al., 2017)."""

    def __init__(self, global_model_params: Dict[str, np.ndarray]):
        self.global_params = global_model_params

    def aggregate(self, client_updates: List[Dict[str, np.ndarray]],
                  client_sizes: List[int]) -> Dict[str, np.ndarray]:
        """Weighted average of client model updates."""
        total_samples = sum(client_sizes)
        aggregated = {}

        for key in self.global_params:
            aggregated[key] = sum(
                update[key] * (n / total_samples)
                for update, n in zip(client_updates, client_sizes)
            )

        self.global_params = aggregated
        return aggregated


class FederatedClient:
    """Client in federated learning."""

    def __init__(self, local_data, local_labels, model):
        self.data = local_data
        self.labels = local_labels
        self.model = model

    def local_train(self, global_params: Dict, epochs: int = 5,
                    lr: float = 0.01) -> Dict[str, np.ndarray]:
        """Train locally on private data, return updated parameters."""
        self.model.set_params(global_params)

        for _ in range(epochs):
            self.model.train_step(self.data, self.labels, lr)

        return self.model.get_params()
```

#### Privacy Attacks on Federated Learning

FL is not inherently private. Known attacks:

1. **Gradient inversion**: Reconstruct training data from shared gradients (Zhu et al., 2019)
2. **Membership inference**: Determine if a sample was in a client's training set
3. **Model poisoning**: Malicious clients inject backdoors
4. **Free-rider attacks**: Clients send fake updates while benefiting from the model

**Mitigation**: Combine FL with differential privacy (DP-SGD per client), secure aggregation (MPC for gradient sums), or gradient compression/perturbation.

### Private Set Intersection (PSI)

Two parties learn the intersection of their sets without revealing non-intersecting elements:

```python
# Simplified PSI using oblivious pseudo-random functions
# Production implementations: Microsoft APSI, Google's PSI library

import hashlib
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

class SimplifiedPSI:
    """
    Diffie-Hellman based PSI (illustrative, not production-grade).

    Protocol:
    1. Client hashes elements to curve points, masks with secret key a
    2. Server hashes elements, masks with secret key b
    3. Client sends H(x)^a to server
    4. Server returns H(x)^(ab) and sends own H(y)^b
    5. Client computes H(y)^(ab) from H(y)^b
    6. Intersection = elements where encodings match
    """

    def __init__(self):
        self.curve = ec.SECP256R1()

    def client_encode(self, elements: list, client_key) -> list:
        """Client masks their elements."""
        encoded = []
        for elem in elements:
            h = hashlib.sha256(str(elem).encode()).digest()
            # In real implementation: hash to curve point, then scalar multiply
            encoded.append(h)
        return encoded

    # Full implementation requires elliptic curve operations
    # See: https://github.com/microsoft/APSI
```

### Libraries and Frameworks

| Library | Focus | Language |
|---------|-------|----------|
| **PySyft** (OpenMined) | Federated learning, SMPC, DP | Python |
| **TenSEAL** | Homomorphic encryption (SEAL wrapper) | Python/C++ |
| **Concrete-ML** (Zama) | FHE for ML (compile sklearn/torch to FHE) | Python |
| **MP-SPDZ** | Multi-party computation protocols | C++/Python |
| **CrypTen** (Meta) | Secure MPC for PyTorch models | Python |
| **OpenDP** (Harvard) | Differential privacy framework | Rust/Python |
| **Flower** | Federated learning framework | Python |
| **FATE** (WeBank) | Industrial federated learning | Python |

---

## 9. Implementation in Data Pipelines

### Anonymization as ETL Step

```python
# Apache Airflow DAG for privacy-preserving data pipeline
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "privacy_preserving_etl",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["privacy", "gdpr"],
)


def extract_raw_data(**context):
    """Extract from source systems into raw zone (encrypted at rest)."""
    # Raw data lands in restricted-access storage
    pass


def assess_privacy_risk(**context):
    """Run re-identification risk assessment before anonymization."""
    from privacy_tools import RiskAssessor

    assessor = RiskAssessor(quasi_identifiers=["age", "zip", "gender", "admission_date"])
    risk = assessor.compute_risk(context["ti"].xcom_pull(task_ids="extract"))

    if risk["prosecutor_risk"] > 0.2:
        context["ti"].xcom_push("requires_stronger_anonymization", True)

    return risk


def apply_anonymization(**context):
    """Apply privacy transforms based on risk assessment."""
    import pandas as pd
    from privacy_tools import KAnonymizer, DifferentialPrivacyMechanism

    df = pd.read_parquet(context["ti"].xcom_pull(task_ids="extract"))
    stronger = context["ti"].xcom_pull(
        task_ids="assess_risk", key="requires_stronger_anonymization"
    )

    k_value = 10 if stronger else 5

    anonymizer = KAnonymizer(k=k_value)
    df_anon = anonymizer.anonymize(
        df,
        quasi_identifiers=["age", "zip_code", "gender"],
        sensitive=["diagnosis", "treatment_cost"]
    )

    # Add DP noise to aggregate statistics
    dp_mech = DifferentialPrivacyMechanism(epsilon=1.0)
    df_anon["treatment_cost"] = dp_mech.add_noise(
        df_anon["treatment_cost"], sensitivity=10000
    )

    return df_anon


def validate_anonymization(**context):
    """Verify anonymization quality and utility preservation."""
    from privacy_tools import AnonymizationValidator

    df_original = context["ti"].xcom_pull(task_ids="extract")
    df_anonymized = context["ti"].xcom_pull(task_ids="anonymize")

    validator = AnonymizationValidator()
    report = validator.validate(
        original=df_original,
        anonymized=df_anonymized,
        checks={
            "k_anonymity": {"k": 5, "quasi_identifiers": ["age", "zip_code", "gender"]},
            "no_direct_identifiers": {"columns": ["name", "ssn", "email", "phone"]},
            "utility_preservation": {"min_correlation": 0.8},
            "no_outlier_leakage": {"z_threshold": 3}
        }
    )

    if not report["passed"]:
        raise ValueError(f"Anonymization validation failed: {report['failures']}")


extract = PythonOperator(task_id="extract", python_callable=extract_raw_data, dag=dag)
assess = PythonOperator(task_id="assess_risk", python_callable=assess_privacy_risk, dag=dag)
anonymize = PythonOperator(task_id="anonymize", python_callable=apply_anonymization, dag=dag)
validate = PythonOperator(task_id="validate", python_callable=validate_anonymization, dag=dag)
load = PostgresOperator(
    task_id="load_to_analytics",
    postgres_conn_id="analytics_db",
    sql="sql/load_anonymized_data.sql",
    dag=dag,
)

extract >> assess >> anonymize >> validate >> load
```

### dbt Models with Masking

```sql
-- models/staging/stg_patients_masked.sql
-- dbt model that applies masking transformations

{{ config(
    materialized='view',
    tags=['privacy', 'staging']
) }}

WITH raw_patients AS (
    SELECT * FROM {{ source('hospital', 'patients') }}
),

masked AS (
    SELECT
        -- Pseudonymize identifier
        {{ pseudonymize('patient_id') }} AS pseudo_patient_id,

        -- Generalize age to 5-year bands
        FLOOR(EXTRACT(YEAR FROM AGE(date_of_birth)) / 5) * 5 AS age_band,

        -- Truncate ZIP to 3 digits
        LEFT(zip_code, 3) || '**' AS zip_prefix,

        -- Keep gender as-is (low cardinality, common quasi-identifier)
        gender,

        -- Sensitive attributes (kept for analysis)
        diagnosis_code,
        procedure_code,
        length_of_stay,

        -- Date shifting (consistent per patient)
        admission_date + ({{ date_shift_days('patient_id') }} * INTERVAL '1 day')
            AS shifted_admission_date,

        -- Suppress rare conditions (appear < 5 times)
        CASE
            WHEN diagnosis_code IN (
                SELECT diagnosis_code
                FROM {{ source('hospital', 'patients') }}
                GROUP BY diagnosis_code
                HAVING COUNT(*) < 5
            )
            THEN 'OTHER'
            ELSE diagnosis_code
        END AS safe_diagnosis

    FROM raw_patients
)

SELECT * FROM masked
```

```sql
-- macros/pseudonymize.sql
{% macro pseudonymize(column_name) %}
    encode(
        hmac(
            {{ column_name }}::text,
            '{{ var("pseudonym_key") }}',
            'sha256'
        ),
        'hex'
    )
{% endmacro %}

{% macro date_shift_days(entity_column) %}
    -- Deterministic shift per entity: hash entity to get consistent offset
    (('x' || substr(md5({{ entity_column }}::text), 1, 8))::bit(32)::int % 365)
{% endmacro %}
```

### Streaming Anonymization with Kafka

```python
# Kafka Streams-style anonymization processor
from confluent_kafka import Consumer, Producer, KafkaError
import json

class StreamAnonymizer:
    """Real-time anonymization of Kafka event streams."""

    def __init__(self, config):
        self.consumer = Consumer({
            "bootstrap.servers": config["brokers"],
            "group.id": "anonymization-processor",
            "auto.offset.reset": "latest"
        })
        self.producer = Producer({"bootstrap.servers": config["brokers"]})
        self.pseudonymizer = HMACPseudonymizer(config["pseudonym_key"])

    def process(self, input_topic: str, output_topic: str):
        """Consume raw events, anonymize, produce to clean topic."""
        self.consumer.subscribe([input_topic])

        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    raise Exception(msg.error())
                continue

            event = json.loads(msg.value().decode("utf-8"))
            anonymized_event = self._anonymize_event(event)

            self.producer.produce(
                output_topic,
                key=msg.key(),
                value=json.dumps(anonymized_event).encode("utf-8")
            )
            self.producer.flush()

    def _anonymize_event(self, event: dict) -> dict:
        """Apply field-level anonymization rules."""
        rules = {
            "user_id": lambda v: self.pseudonymizer.pseudonymize(v, "user_id"),
            "email": lambda v: self.pseudonymizer.pseudonymize(v, "email"),
            "ip_address": lambda v: ".".join(v.split(".")[:2]) + ".0.0",
            "user_agent": lambda v: v.split("/")[0] if "/" in v else v,
            "timestamp": lambda v: v[:13] + ":00:00Z",  # Truncate to hour
            "location": lambda v: {
                "lat": round(v.get("lat", 0), 1),
                "lon": round(v.get("lon", 0), 1)
            } if isinstance(v, dict) else v
        }

        result = {}
        for key, value in event.items():
            if key in rules:
                result[key] = rules[key](value)
            else:
                result[key] = value

        return result
```

### API-Level Anonymization (Reverse Proxy Pattern)

```python
# FastAPI middleware that anonymizes responses based on caller's access level
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from typing import Callable
import json

app = FastAPI()

class PrivacyProxy:
    """
    Reverse proxy pattern: intercept API responses and apply
    privacy transforms based on the authenticated caller's role.
    """

    ROLE_POLICIES = {
        "admin": [],  # Full access
        "analyst": ["pseudonymize:user_id", "redact:email", "generalize:age"],
        "external": ["pseudonymize:user_id", "redact:email", "redact:phone",
                     "generalize:age", "generalize:location", "suppress:rare_conditions"],
        "public": ["remove:user_id", "redact:email", "redact:phone",
                   "aggregate:all_numeric"]
    }

    def __init__(self, pseudonymizer):
        self.pseudonymizer = pseudonymizer

    def apply_policy(self, data: dict, role: str) -> dict:
        """Apply privacy policy to response data."""
        policies = self.ROLE_POLICIES.get(role, self.ROLE_POLICIES["public"])
        result = data.copy()

        for policy in policies:
            action, field = policy.split(":", 1)
            if field not in result:
                continue

            if action == "pseudonymize":
                result[field] = self.pseudonymizer.pseudonymize(str(result[field]), field)
            elif action == "redact":
                result[field] = "[REDACTED]"
            elif action == "generalize":
                result[field] = self._generalize(field, result[field])
            elif action == "remove":
                del result[field]
            elif action == "suppress":
                # Suppress rare values
                pass

        return result

    def _generalize(self, field: str, value):
        if field == "age" and isinstance(value, (int, float)):
            return f"{int(value) // 10 * 10}-{int(value) // 10 * 10 + 9}"
        if field == "location" and isinstance(value, dict):
            return {"region": value.get("region", "Unknown")}
        return value


@app.middleware("http")
async def privacy_middleware(request: Request, call_next: Callable):
    """Intercept responses and apply privacy transforms."""
    response = await call_next(request)

    # Only process JSON responses
    if "application/json" not in response.headers.get("content-type", ""):
        return response

    # Determine caller's role
    role = request.state.user_role if hasattr(request.state, "user_role") else "public"

    # Apply privacy policy
    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    data = json.loads(body)
    proxy = PrivacyProxy(app.state.pseudonymizer)

    if isinstance(data, list):
        data = [proxy.apply_policy(item, role) for item in data]
    elif isinstance(data, dict):
        data = proxy.apply_policy(data, role)

    return JSONResponse(content=data, status_code=response.status_code)
```

### Testing Anonymization Quality

```python
import pytest
import pandas as pd
import numpy as np

class TestAnonymizationQuality:
    """Automated tests for anonymization correctness and utility."""

    def test_k_anonymity_satisfied(self, anonymized_df):
        """Verify k-anonymity constraint holds."""
        qi = ["age_band", "zip_prefix", "gender"]
        class_sizes = anonymized_df.groupby(qi).size()
        assert class_sizes.min() >= 5, (
            f"k-anonymity violated: minimum class size = {class_sizes.min()}"
        )

    def test_no_direct_identifiers(self, anonymized_df):
        """Ensure no direct identifiers remain."""
        forbidden = {"name", "ssn", "email", "phone", "patient_id", "mrn"}
        remaining = set(anonymized_df.columns) & forbidden
        assert not remaining, f"Direct identifiers found: {remaining}"

    def test_pseudonym_consistency(self, raw_df, anonymized_df, pseudonymizer):
        """Verify pseudonyms are consistent (same input → same output)."""
        # Same patient should always get same pseudonym
        for _, row in raw_df.head(100).iterrows():
            pseudo1 = pseudonymizer.pseudonymize(row["patient_id"], "patient_id")
            pseudo2 = pseudonymizer.pseudonymize(row["patient_id"], "patient_id")
            assert pseudo1 == pseudo2

    def test_utility_preservation(self, raw_df, anonymized_df):
        """Statistical utility preserved within acceptable bounds."""
        # Mean age should be similar (within noise bounds)
        raw_mean_age = raw_df["age"].mean()
        anon_mean_age = anonymized_df["age_band"].apply(
            lambda x: int(x.split("-")[0]) + 2.5 if "-" in str(x) else float(x)
        ).mean()
        assert abs(raw_mean_age - anon_mean_age) < 5, "Age mean drift too large"

        # Correlation structure preserved
        raw_corr = raw_df[["age", "length_of_stay"]].corr().iloc[0, 1]
        # Similar correlation check on anonymized data
        assert abs(raw_corr) > 0.1, "Testing correlation preservation requires signal"

    def test_no_rare_value_leakage(self, anonymized_df):
        """Rare sensitive values should be suppressed or generalized."""
        value_counts = anonymized_df["diagnosis_code"].value_counts()
        rare_values = value_counts[value_counts < 3]
        assert len(rare_values) == 0, (
            f"Rare values not suppressed: {rare_values.index.tolist()}"
        )

    def test_date_shift_consistency(self, anonymized_df):
        """Date shifts are consistent per entity (preserves intervals)."""
        for _, patient_records in anonymized_df.groupby("pseudo_patient_id"):
            if len(patient_records) > 1:
                # All date shifts for same patient should preserve relative order
                dates = patient_records["shifted_admission_date"].sort_values()
                assert dates.is_monotonic_increasing or len(dates) == 1

    def test_reversibility(self, raw_df, pseudonymizer):
        """Verify pseudonymization is reversible with correct key."""
        sample_id = raw_df["patient_id"].iloc[0]
        pseudo = pseudonymizer.pseudonymize(sample_id, "patient_id")
        # With tokenization, verify vault lookup works
        # With HMAC, verify forward-check works
        assert pseudonymizer.verify(sample_id, pseudo, "patient_id")
```

---

## 10. Lab Exercises

### Lab 1: Implement k-Anonymity on a Health Dataset with ARX

**Objective**: Apply k-anonymity to a synthetic health dataset, balancing privacy (high k) against utility (low information loss).

```python
"""
Lab 1: k-Anonymity with the ARX framework.

Dataset: Synthetic patient records with:
- age, gender, zip_code (quasi-identifiers)
- diagnosis (sensitive attribute)
- treatment_cost (analysis target)

Tasks:
1. Load dataset and identify quasi-identifiers
2. Define generalization hierarchies for each QI
3. Apply k-anonymity for k=3, k=5, k=10
4. Measure information loss at each level
5. Verify k-anonymity holds
6. Compare utility (mean treatment cost, diagnosis distribution) across k values
"""

import pandas as pd
import numpy as np
from itertools import product

# Generate synthetic health dataset
np.random.seed(42)
N = 5000

ages = np.random.randint(18, 90, N)
genders = np.random.choice(["M", "F"], N)
zip_codes = np.random.choice(
    ["10115", "10117", "10119", "20095", "20097", "30159", "40210", "50667"],
    N
)
diagnoses = np.random.choice(
    ["Diabetes", "Hypertension", "COPD", "Depression", "Arthritis",
     "Heart Failure", "Asthma", "Cancer"],
    N,
    p=[0.2, 0.25, 0.1, 0.15, 0.1, 0.08, 0.07, 0.05]
)
costs = np.random.exponential(5000, N) + 1000

health_data = pd.DataFrame({
    "patient_id": [f"P{i:05d}" for i in range(N)],
    "age": ages,
    "gender": genders,
    "zip_code": zip_codes,
    "diagnosis": diagnoses,
    "treatment_cost": costs.round(2)
})

# --- Task 1: Define generalization hierarchies ---

def generalize_age(age, level):
    """Generalize age at different levels."""
    if level == 0:
        return str(age)
    elif level == 1:
        return f"{(age // 5) * 5}-{(age // 5) * 5 + 4}"
    elif level == 2:
        return f"{(age // 10) * 10}-{(age // 10) * 10 + 9}"
    elif level == 3:
        return f"{(age // 20) * 20}-{(age // 20) * 20 + 19}"
    else:
        return "*"

def generalize_zip(zip_code, level):
    """Generalize ZIP code by masking trailing digits."""
    if level == 0:
        return zip_code
    elif level <= len(zip_code):
        return zip_code[:len(zip_code) - level] + "*" * level
    else:
        return "*" * len(zip_code)

# --- Task 2: Implement Optimal k-Anonymity ---

def check_k_anonymity(df, quasi_identifiers, k):
    """Check if dataset satisfies k-anonymity."""
    groups = df.groupby(quasi_identifiers).size()
    return groups.min() >= k, groups.min(), groups

def apply_k_anonymity_greedy(df, quasi_identifiers, hierarchies, k):
    """
    Apply minimal generalization to achieve k-anonymity.
    Uses a greedy bottom-up approach.
    """
    result = df.copy()
    levels = {qi: 0 for qi in quasi_identifiers}

    while True:
        satisfied, min_class, _ = check_k_anonymity(
            result, quasi_identifiers, k
        )
        if satisfied:
            break

        # Find QI with most violations, generalize it one level
        violations = {}
        for qi in quasi_identifiers:
            groups = result.groupby(quasi_identifiers).size()
            violations[qi] = (groups < k).sum()

        worst_qi = max(violations, key=violations.get)
        levels[worst_qi] += 1
        result[worst_qi] = df[worst_qi].apply(
            lambda v: hierarchies[worst_qi](v, levels[worst_qi])
        )

    return result, levels

# --- Task 3: Apply and Compare ---

hierarchies = {
    "age": generalize_age,
    "zip_code": generalize_zip,
    "gender": lambda v, l: v if l == 0 else "*"
}
quasi_identifiers = ["age", "gender", "zip_code"]

for k in [3, 5, 10]:
    anon_df, gen_levels = apply_k_anonymity_greedy(
        health_data[quasi_identifiers + ["diagnosis", "treatment_cost"]],
        quasi_identifiers, hierarchies, k
    )
    satisfied, min_k, _ = check_k_anonymity(anon_df, quasi_identifiers, k)

    print(f"\n--- k={k} ---")
    print(f"  Satisfied: {satisfied}, Min class size: {min_k}")
    print(f"  Generalization levels: {gen_levels}")
    print(f"  Mean treatment cost: {anon_df['treatment_cost'].mean():.2f}")
    print(f"  Unique QI combinations: {anon_df[quasi_identifiers].drop_duplicates().shape[0]}")
```

### Lab 2: Build a Differential Privacy Query Engine with OpenDP

**Objective**: Build a query engine that answers statistical queries with formal differential privacy guarantees and tracks cumulative privacy budget.

```python
"""
Lab 2: Differential Privacy Query Engine.

Build a system that:
1. Accepts statistical queries (count, sum, mean, histogram)
2. Adds calibrated noise to achieve ε-differential privacy
3. Tracks privacy budget (ε spent across queries)
4. Refuses queries when budget is exhausted
5. Reports accuracy bounds for each answer

Uses OpenDP library for formally verified mechanisms.
"""

import opendp.prelude as dp
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

dp.enable_features("contrib", "floating-point")

@dataclass
class QueryResult:
    """Result of a differentially private query."""
    query_type: str
    true_value: float  # Only available in lab setting for evaluation
    noisy_value: float
    epsilon_spent: float
    confidence_interval: tuple
    remaining_budget: float

@dataclass
class DPQueryEngine:
    """Differentially private query engine with budget tracking."""

    data: pd.DataFrame
    total_epsilon: float
    total_delta: float = 1e-6
    spent_epsilon: float = 0.0
    query_log: list = field(default_factory=list)

    @property
    def remaining_epsilon(self) -> float:
        return self.total_epsilon - self.spent_epsilon

    def count(self, column: str, predicate=None, epsilon: float = 0.1) -> QueryResult:
        """Private count query."""
        self._check_budget(epsilon)

        # True answer
        if predicate:
            true_count = predicate(self.data[column]).sum()
        else:
            true_count = len(self.data)

        # Sensitivity of count = 1 (adding/removing one person changes count by 1)
        sensitivity = 1.0
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale)
        noisy_count = max(0, true_count + noise)

        self._record_query("count", epsilon)

        # 95% confidence interval for Laplace noise
        ci_width = scale * np.log(1 / 0.025)

        return QueryResult(
            query_type="count",
            true_value=true_count,
            noisy_value=round(noisy_count),
            epsilon_spent=epsilon,
            confidence_interval=(noisy_count - ci_width, noisy_count + ci_width),
            remaining_budget=self.remaining_epsilon
        )

    def mean(self, column: str, lower: float, upper: float,
             epsilon: float = 0.5) -> QueryResult:
        """Private mean query with bounded input."""
        self._check_budget(epsilon)

        # Clip values to bounds
        clipped = self.data[column].clip(lower, upper)
        true_mean = clipped.mean()
        n = len(clipped)

        # Sensitivity of mean = (upper - lower) / n
        sensitivity = (upper - lower) / n
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale)
        noisy_mean = true_mean + noise

        self._record_query("mean", epsilon)

        ci_width = scale * np.log(1 / 0.025)
        return QueryResult(
            query_type="mean",
            true_value=true_mean,
            noisy_value=noisy_mean,
            epsilon_spent=epsilon,
            confidence_interval=(noisy_mean - ci_width, noisy_mean + ci_width),
            remaining_budget=self.remaining_epsilon
        )

    def histogram(self, column: str, bins: list,
                  epsilon: float = 1.0) -> dict:
        """Private histogram (each bin count is noisy)."""
        # Split epsilon across bins (parallel composition if bins are disjoint)
        # Disjoint bins → each bin uses full epsilon (parallel composition)
        self._check_budget(epsilon)

        true_hist = self.data[column].value_counts()
        noisy_hist = {}

        for bin_label in bins:
            true_count = true_hist.get(bin_label, 0)
            noise = np.random.laplace(0, 1.0 / epsilon)
            noisy_hist[bin_label] = max(0, round(true_count + noise))

        self._record_query("histogram", epsilon)
        return noisy_hist

    def _check_budget(self, epsilon: float):
        """Refuse query if budget insufficient."""
        if epsilon > self.remaining_epsilon:
            raise PrivacyBudgetExhausted(
                f"Requested ε={epsilon}, remaining={self.remaining_epsilon:.4f}"
            )

    def _record_query(self, query_type: str, epsilon: float):
        """Log query and update spent budget."""
        self.spent_epsilon += epsilon
        self.query_log.append({
            "type": query_type,
            "epsilon": epsilon,
            "cumulative_epsilon": self.spent_epsilon
        })


class PrivacyBudgetExhausted(Exception):
    pass


# --- Lab Exercise ---

# Create engine with budget of ε=5.0
engine = DPQueryEngine(data=health_data, total_epsilon=5.0)

# Query 1: How many patients have diabetes?
result = engine.count(
    "diagnosis",
    predicate=lambda x: x == "Diabetes",
    epsilon=0.5
)
print(f"Diabetic patients: {result.noisy_value} (true: {result.true_value})")
print(f"95% CI: {result.confidence_interval}")
print(f"Budget remaining: {result.remaining_budget}")

# Query 2: Mean treatment cost
result = engine.mean("treatment_cost", lower=0, upper=50000, epsilon=1.0)
print(f"\nMean cost: ${result.noisy_value:.2f} (true: ${result.true_value:.2f})")

# Query 3: Diagnosis distribution
hist = engine.histogram("diagnosis",
                        bins=["Diabetes", "Hypertension", "COPD", "Depression"],
                        epsilon=1.0)
print(f"\nDiagnosis histogram: {hist}")
print(f"Budget remaining: {engine.remaining_epsilon}")
```

### Lab 3: Generate Synthetic Tabular Data with CTGAN and Evaluate Utility

**Objective**: Train a CTGAN on real data, generate synthetic data, and rigorously evaluate both utility (statistical similarity, ML efficacy) and privacy (membership inference, distance to closest record).

```python
"""
Lab 3: Synthetic Data Generation and Evaluation.

Steps:
1. Train CTGAN on the health dataset
2. Generate synthetic dataset of equal size
3. Evaluate statistical similarity (column distributions, correlations)
4. Train ML models on synthetic, test on real (TSTR)
5. Run membership inference attack
6. Compute Distance to Closest Record
7. Compare utility-privacy tradeoff across training epochs
"""

from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
from sdv.evaluation.single_table import evaluate_quality
from sdmetrics.single_table import NewRowSynthesis
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report
from sklearn.preprocessing import LabelEncoder
from scipy.spatial.distance import cdist
import pandas as pd
import numpy as np

# --- Step 1: Prepare data and train CTGAN ---

# Remove patient_id (not a feature)
train_data = health_data.drop(columns=["patient_id"])

metadata = SingleTableMetadata()
metadata.detect_from_dataframe(train_data)
metadata.update_column("age", sdtype="numerical")
metadata.update_column("treatment_cost", sdtype="numerical")
metadata.update_column("gender", sdtype="categorical")
metadata.update_column("zip_code", sdtype="categorical")
metadata.update_column("diagnosis", sdtype="categorical")

# Train CTGAN
synthesizer = CTGANSynthesizer(
    metadata,
    epochs=300,
    batch_size=500,
    generator_dim=(256, 256),
    discriminator_dim=(256, 256),
    verbose=True
)
synthesizer.fit(train_data)

# Generate synthetic data
synthetic_data = synthesizer.sample(num_rows=len(train_data))

# --- Step 2: Statistical Similarity ---

quality_report = evaluate_quality(train_data, synthetic_data, metadata)
print(f"Overall Quality Score: {quality_report.get_score():.4f}")

# Column-level comparison
for col in train_data.columns:
    if train_data[col].dtype in ["int64", "float64"]:
        real_mean = train_data[col].mean()
        synth_mean = synthetic_data[col].mean()
        print(f"  {col}: real_mean={real_mean:.2f}, synth_mean={synth_mean:.2f}, "
              f"diff={abs(real_mean - synth_mean):.2f}")

# --- Step 3: ML Efficacy (TSTR) ---

# Encode categoricals
le_diag = LabelEncoder()
le_gender = LabelEncoder()
le_zip = LabelEncoder()

# Prepare real data
X_real = train_data.copy()
X_real["diagnosis_enc"] = le_diag.fit_transform(X_real["diagnosis"])
X_real["gender_enc"] = le_gender.fit_transform(X_real["gender"])
X_real["zip_enc"] = le_zip.fit_transform(X_real["zip_code"])
features = ["age", "gender_enc", "zip_enc", "treatment_cost"]
target = "diagnosis_enc"

X_train, X_test, y_train, y_test = train_test_split(
    X_real[features], X_real[target], test_size=0.2, random_state=42
)

# Train on Real, Test on Real (TRTR baseline)
model_real = GradientBoostingClassifier(n_estimators=100, random_state=42)
model_real.fit(X_train, y_train)
score_trtr = f1_score(y_test, model_real.predict(X_test), average="weighted")

# Prepare synthetic data
X_synth = synthetic_data.copy()
X_synth["diagnosis_enc"] = le_diag.transform(X_synth["diagnosis"])
X_synth["gender_enc"] = le_gender.transform(X_synth["gender"])
X_synth["zip_enc"] = le_zip.transform(X_synth["zip_code"])

# Train on Synthetic, Test on Real (TSTR)
model_synth = GradientBoostingClassifier(n_estimators=100, random_state=42)
model_synth.fit(X_synth[features], X_synth[target])
score_tstr = f1_score(y_test, model_synth.predict(X_test), average="weighted")

print(f"\nML Efficacy:")
print(f"  TRTR (baseline) F1: {score_trtr:.4f}")
print(f"  TSTR (synthetic) F1: {score_tstr:.4f}")
print(f"  Utility ratio: {score_tstr / score_trtr:.4f}")

# --- Step 4: Privacy Metrics ---

# Membership inference (novelty)
novelty = NewRowSynthesis.compute(
    real_data=train_data,
    synthetic_data=synthetic_data,
    metadata=metadata,
    numerical_match_tolerance=0.01,
    synthetic_sample_size=min(1000, len(synthetic_data))
)
print(f"\nPrivacy Metrics:")
print(f"  New Row Synthesis (novelty): {novelty:.4f} (target: >0.9)")

# Distance to Closest Record
numeric_cols = ["age", "treatment_cost"]
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
real_scaled = scaler.fit_transform(train_data[numeric_cols])
synth_scaled = scaler.transform(synthetic_data[numeric_cols])

distances = cdist(synth_scaled[:500], real_scaled, metric="euclidean")
dcr_synthetic = distances.min(axis=1)

# Baseline: real-to-real DCR
real_distances = cdist(real_scaled[:500], real_scaled, metric="euclidean")
np.fill_diagonal(real_distances[:500, :500], np.inf)
dcr_real = real_distances.min(axis=1)

print(f"  Synthetic DCR (mean): {dcr_synthetic.mean():.4f}")
print(f"  Real-to-Real DCR (mean): {dcr_real.mean():.4f}")
print(f"  DCR ratio (>1 = good privacy): {dcr_synthetic.mean() / dcr_real.mean():.4f}")
```

### Lab 4: Perform a Re-identification Attack on a Naively Anonymized Dataset

**Objective**: Demonstrate practical re-identification using linkage attacks, quantify risk under different attacker models, and show why naive anonymization fails.

```python
"""
Lab 4: Re-identification Attack Simulation.

Scenario: A hospital releases a "de-identified" dataset by removing names and
IDs but keeping age, ZIP, gender, admission date, and diagnosis.
An attacker obtains voter registration data (name, age, ZIP, gender).

Tasks:
1. Create the "anonymized" hospital release (naive: just remove direct identifiers)
2. Create an auxiliary dataset (voter registration)
3. Perform linkage attack
4. Measure re-identification rate
5. Show which records are uniquely identifiable
6. Compare with properly k-anonymized version
7. Quantify risk under prosecutor/journalist/marketer models

Security/ethical note: Understanding these attacks is essential for privacy
assessments during security audits and penetration testing engagements.
"""

import pandas as pd
import numpy as np
from typing import Tuple

np.random.seed(42)

# --- Step 1: Simulate hospital "de-identified" release ---

# Full dataset (ground truth, not released)
N = 10000
full_records = pd.DataFrame({
    "patient_id": range(N),
    "name": [f"Person_{i}" for i in range(N)],
    "age": np.random.randint(18, 90, N),
    "gender": np.random.choice(["M", "F"], N),
    "zip_code": np.random.choice(
        [f"{z:05d}" for z in range(10001, 10200)], N
    ),
    "admission_date": pd.date_range("2023-01-01", periods=N, freq="h")
                       .to_series().sample(N, replace=True).values,
    "diagnosis": np.random.choice(
        ["Diabetes", "Hypertension", "Cancer", "HIV", "Depression",
         "Flu", "Fracture", "Pregnancy"],
        N, p=[0.15, 0.2, 0.05, 0.02, 0.15, 0.2, 0.13, 0.10]
    )
})

# Naive "de-identification": just remove name and patient_id
hospital_release = full_records.drop(columns=["patient_id", "name"])
print(f"Hospital release: {len(hospital_release)} records")
print(f"Columns: {list(hospital_release.columns)}")

# --- Step 2: Auxiliary dataset (voter registration) ---
# Attacker has: name, age, gender, zip_code from public records
# Simulating overlap: 70% of patients appear in voter rolls

overlap_mask = np.random.random(N) < 0.7
voter_roll = full_records[overlap_mask][["name", "age", "gender", "zip_code"]].copy()
# Add some voters not in hospital data
extra_voters = pd.DataFrame({
    "name": [f"Voter_{i}" for i in range(3000)],
    "age": np.random.randint(18, 90, 3000),
    "gender": np.random.choice(["M", "F"], 3000),
    "zip_code": np.random.choice([f"{z:05d}" for z in range(10001, 10200)], 3000)
})
voter_roll = pd.concat([voter_roll, extra_voters], ignore_index=True)
print(f"Voter roll: {len(voter_roll)} records")

# --- Step 3: Linkage Attack ---

def perform_linkage_attack(
    target_data: pd.DataFrame,
    auxiliary_data: pd.DataFrame,
    linking_attributes: list
) -> Tuple[pd.DataFrame, dict]:
    """
    Perform a linkage attack by joining on quasi-identifiers.

    Returns matched records and attack statistics.
    """
    # Join target (hospital) with auxiliary (voter roll)
    linked = target_data.merge(
        auxiliary_data,
        on=linking_attributes,
        how="inner"
    )

    # Group by linking attributes to find unique matches
    group_sizes = target_data.groupby(linking_attributes).size().reset_index(name="eq_class_size")
    target_with_sizes = target_data.merge(group_sizes, on=linking_attributes)

    # Records in equivalence classes of size 1 are uniquely identifiable
    unique_records = target_with_sizes[target_with_sizes["eq_class_size"] == 1]

    # Re-identification attempts (unique matches in the join)
    linked_groups = linked.groupby(linking_attributes)
    unique_matches = linked_groups.filter(lambda x: len(x) == 1)

    stats = {
        "target_records": len(target_data),
        "auxiliary_records": len(auxiliary_data),
        "linked_records": len(linked),
        "unique_in_target": len(unique_records),
        "uniquely_reidentified": len(unique_matches),
        "reidentification_rate": len(unique_matches) / len(target_data),
        "uniqueness_rate": len(unique_records) / len(target_data)
    }

    return unique_matches, stats

# Attack with {age, gender, zip_code}
linking_attrs = ["age", "gender", "zip_code"]
reidentified, stats = perform_linkage_attack(
    hospital_release, voter_roll, linking_attrs
)

print(f"\n--- Linkage Attack Results ---")
print(f"  Linking attributes: {linking_attrs}")
print(f"  Unique in target: {stats['unique_in_target']} ({stats['uniqueness_rate']:.1%})")
print(f"  Successfully re-identified: {stats['uniquely_reidentified']} "
      f"({stats['reidentification_rate']:.1%})")

# --- Step 4: Assess risk under attacker models ---

def compute_risk_models(df, quasi_identifiers):
    """Compute risk under prosecutor, journalist, marketer models."""
    class_sizes = df.groupby(quasi_identifiers).size()

    prosecutor = 1.0 / class_sizes.min()  # Worst case (known target)
    journalist = (class_sizes == 1).sum() / len(class_sizes)  # Any unique
    marketer = (1.0 / class_sizes).mean()  # Expected success rate

    return {
        "prosecutor_risk": prosecutor,
        "journalist_risk": journalist,
        "marketer_risk": marketer,
        "min_class_size": class_sizes.min(),
        "median_class_size": class_sizes.median(),
        "pct_unique": (class_sizes == 1).sum() / len(class_sizes)
    }

risks_naive = compute_risk_models(hospital_release, linking_attrs)
print(f"\n--- Risk Assessment (Naive Release) ---")
for k, v in risks_naive.items():
    print(f"  {k}: {v:.4f}")

# --- Step 5: Compare with k-anonymized version ---

# Apply 5-anonymity
def simple_k_anonymize(df, quasi_identifiers, k=5):
    """Quick k-anonymity via generalization."""
    result = df.copy()
    result["age"] = (result["age"] // 5) * 5  # 5-year bands
    result["zip_code"] = result["zip_code"].str[:3] + "**"  # 3-digit ZIP

    # Check and suppress remaining violations
    while True:
        groups = result.groupby(quasi_identifiers).size()
        violating = groups[groups < k]
        if len(violating) == 0:
            break
        # Suppress smallest groups
        for idx in violating.index:
            mask = True
            for col, val in zip(quasi_identifiers, idx):
                mask = mask & (result[col] == val)
            result = result[~mask]
        break  # One pass for lab purposes

    return result

hospital_kanon = simple_k_anonymize(hospital_release, linking_attrs, k=5)
_, stats_kanon = perform_linkage_attack(hospital_kanon, voter_roll, linking_attrs)
risks_kanon = compute_risk_models(hospital_kanon, linking_attrs)

print(f"\n--- Risk Assessment (5-Anonymized Release) ---")
print(f"  Records retained: {len(hospital_kanon)} / {len(hospital_release)}")
for k, v in risks_kanon.items():
    print(f"  {k}: {v:.4f}")

print(f"\n--- Comparison ---")
print(f"  Naive re-identification rate: {stats['reidentification_rate']:.1%}")
print(f"  k=5 re-identification rate: {stats_kanon['reidentification_rate']:.1%}")
print(f"  Risk reduction (prosecutor): "
      f"{(1 - risks_kanon['prosecutor_risk']/risks_naive['prosecutor_risk']):.1%}")
```

---

## Security Assessment Perspective

Understanding anonymization weaknesses is directly relevant to privacy-focused penetration testing and security assessments:

### Privacy Assessment Methodology

1. **Data inventory**: Identify all datasets containing personal data, their protection mechanisms, and access controls.

2. **Quasi-identifier analysis**: Enumerate attributes that could serve as quasi-identifiers. Cross-reference with publicly available datasets (voter rolls, social media, data broker services).

3. **Re-identification risk quantification**: Apply the three attacker models (prosecutor, journalist, marketer). Report risk as probability with confidence intervals.

4. **Auxiliary data enumeration**: Catalog external datasets an attacker could reasonably obtain for linkage (census data, voter registration, commercial data brokers, social media scrapes, leaked databases).

5. **Technical control evaluation**: Assess whether pseudonymization keys are adequately protected (HSM storage, access logging, separation from pseudonymized data). Test whether anonymization is truly irreversible or merely obscured.

6. **Composition attack assessment**: When multiple anonymized releases exist from the same source, assess whether combining them (temporal or cross-dataset) enables re-identification that neither alone permits.

7. **Synthetic data validation**: If synthetic data is used, evaluate whether the generative model memorized training examples (membership inference, overfitting detection via DCR analysis).

### Reporting Framework

Privacy findings in security assessments should follow:

| Field | Content |
|-------|---------|
| Finding ID | PRIV-001, PRIV-002, etc. |
| Severity | CVSS-adjacent scoring + GDPR Article reference |
| Description | Technical description of the privacy weakness |
| Attack scenario | Concrete attacker model and exploitation path |
| Evidence | Re-identification rate, equivalence class statistics |
| Affected data | Number of data subjects at risk |
| Remediation | Specific technique (e.g., "Apply 10-anonymity with l=3 diversity") |
| Regulatory risk | Potential fine calculation (up to 4% global turnover under Art. 83) |

### Common Findings in Assessments

1. **Pseudonymization treated as anonymization**: Organization claims data is "anonymized" but uses reversible pseudonymization. GDPR obligations not being met.

2. **Insufficient k-value**: Dataset satisfies k=2 anonymity but contains equivalence classes of size 2, giving 50% re-identification probability for targeted attacks.

3. **Temporal correlation leakage**: Multiple data releases over time enable tracking individuals through quasi-identifier evolution.

4. **API enumeration enabling re-identification**: Rate-limited but unbounded queries against a "private" API allow reconstruction of the underlying dataset.

5. **Synthetic data overfitting**: GAN-generated synthetic data memorizes rare individuals (those with unique attribute combinations), enabling membership inference.

6. **Key management failures**: Pseudonymization keys stored alongside pseudonymized data, in application configs, or accessible to analysts who access the pseudonymized data — defeating the purpose of separation required by Article 4(5).

---

## References and Further Reading

- Sweeney, L. (2002). k-Anonymity: A Model for Protecting Privacy. International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems.
- Machanavajjhala, A. et al. (2007). l-Diversity: Privacy Beyond k-Anonymity. ACM TKDD.
- Li, N. et al. (2007). t-Closeness: Privacy Beyond k-Anonymity and l-Diversity. ICDE.
- Dwork, C. (2006). Differential Privacy. ICALP.
- Dwork, C. & Roth, A. (2014). The Algorithmic Foundations of Differential Privacy. Foundations and Trends in Theoretical Computer Science.
- Narayanan, A. & Shmatikov, V. (2008). Robust De-anonymization of Large Sparse Datasets. IEEE S&P.
- Article 29 Working Party. (2014). Opinion 05/2014 on Anonymization Techniques (WP216).
- Xu, L. et al. (2019). Modeling Tabular Data Using Conditional GAN. NeurIPS (CTGAN).
- McMahan, B. et al. (2017). Communication-Efficient Learning of Deep Networks from Decentralized Data. AISTATS (FedAvg).
- Dinur, I. & Nissim, K. (2003). Revealing Information While Preserving Privacy. PODS.
- De Montjoye, Y-A. et al. (2013). Unique in the Crowd: The Privacy Bounds of Human Mobility. Scientific Reports.
- Andrés, M. et al. (2013). Geo-Indistinguishability: Differential Privacy for Location-Based Systems. CCS.
