# Stripe — Integrazione Pratica per SaaS — Guida Approfondita

## Indice
- [Panoramica](#panoramica)
- [Architettura delle API Stripe](#architettura-delle-api-stripe)
- [Setup Iniziale e Architettura](#setup-iniziale-e-architettura)
- [Products, Prices e il Modello Catalogo](#products-prices-e-il-modello-catalogo)
- [Checkout Sessions — Pagamenti One-Time e Subscription](#checkout-sessions--pagamenti-one-time-e-subscription)
- [Stripe Elements — Pagamenti Embeddabili](#stripe-elements--pagamenti-embeddabili)
- [Payment Links — Pagamenti Senza Codice](#payment-links--pagamenti-senza-codice)
- [Checkout vs Elements vs Payment Links — Quando Usare Cosa](#checkout-vs-elements-vs-payment-links--quando-usare-cosa)
- [Subscriptions API — Gestione Completa degli Abbonamenti](#subscriptions-api--gestione-completa-degli-abbonamenti)
- [Ciclo di Vita delle Subscription](#ciclo-di-vita-delle-subscription)
- [Proration — Calcolo Proporzionale](#proration--calcolo-proporzionale)
- [Webhook Integration — Event-Driven Architecture](#webhook-integration--event-driven-architecture)
- [Webhook Best Practices Avanzate](#webhook-best-practices-avanzate)
- [Customer Portal — Self-Service per i Clienti](#customer-portal--self-service-per-i-clienti)
- [Metered Billing — Fatturazione a Consumo](#metered-billing--fatturazione-a-consumo)
- [Stripe Meters — API di Nuova Generazione per il Consumo](#stripe-meters--api-di-nuova-generazione-per-il-consumo)
- [Invoice API — Fatturazione Personalizzata](#invoice-api--fatturazione-personalizzata)
- [Multi-Currency — Pagamenti Internazionali](#multi-currency--pagamenti-internazionali)
- [Stripe Tax — Automazione Fiscale](#stripe-tax--automazione-fiscale)
- [Stripe Connect — Marketplace e Piattaforme](#stripe-connect--marketplace-e-piattaforme)
- [Revenue Recognition](#revenue-recognition)
- [PCI Compliance con Stripe](#pci-compliance-con-stripe)
- [Testing con Stripe CLI](#testing-con-stripe-cli)
- [Test Clocks — Simulazione Temporale delle Subscription](#test-clocks--simulazione-temporale-delle-subscription)
- [Gestione degli Errori e Retry Logic](#gestione-degli-errori-e-retry-logic)
- [Migrazione da Altri Payment Processor](#migrazione-da-altri-payment-processor)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Riferimenti](#riferimenti)

---

## Panoramica

Stripe è diventata la piattaforma di pagamento dominante per le aziende SaaS, servendo dal piccolo side project alla grande enterprise. La sua popolarità nel mondo SaaS non è casuale: Stripe offre un'API developer-first che semplifica enormemente la complessità intrinseca della gestione dei pagamenti ricorrenti, della fatturazione, della compliance PCI, e delle operazioni finanziarie internazionali. Per un fondatore SaaS, Stripe non è semplicemente un "payment processor" — è l'infrastruttura finanziaria su cui poggia l'intero modello di business.

Questa guida fornisce un'analisi pratica e approfondita dell'integrazione di Stripe per un prodotto SaaS. Non ci limitiamo a una panoramica delle API: affrontiamo ogni aspetto con codice funzionante, pattern architetturali, strategie di gestione degli errori, e le trappole più comuni che i team incontrano durante l'implementazione. L'obiettivo è fornire una guida completa che permetta di passare da zero a un sistema di billing production-ready.

È importante sottolineare che l'integrazione di Stripe non è un'attività "una tantum". Il billing è un sistema vivente che evolve con il prodotto: nuovi piani, promozioni, upgrade/downgrade, metered billing, multi-currency, tax compliance — ogni evoluzione del modello di business richiede aggiornamenti all'integrazione. Progettare l'integrazione con flessibilità e maintainability fin dall'inizio è fondamentale per evitare costosi refactoring in futuro.

---

## Architettura delle API Stripe

### Struttura Generale delle API

Le API Stripe seguono un design REST convenzionale, con risorse che si mappano su URL prevedibili. Ogni oggetto in Stripe ha un identificativo unico con prefisso che indica il tipo di risorsa:

| Prefisso | Risorsa | Esempio |
|----------|---------|---------|
| `cus_` | Customer | `cus_Rk3b9fAx2q` |
| `sub_` | Subscription | `sub_1NxEJz2eZv` |
| `pi_` | PaymentIntent | `pi_3MtwBwLkdI` |
| `in_` | Invoice | `in_1MtGbR2eZv` |
| `price_` | Price | `price_1NfKx32eZv` |
| `prod_` | Product | `prod_NWjs8kKbJW` |
| `pm_` | PaymentMethod | `pm_1MqLiJLkdI` |
| `cs_` | Checkout Session | `cs_test_a1b2c3` |
| `evt_` | Event | `evt_1NfLm02eZv` |
| `ch_` | Charge | `ch_3MmlLrLkdI` |
| `re_` | Refund | `re_1Nispe2eZv` |
| `si_` | Subscription Item | `si_NfLm02eZvKI` |
| `ii_` | Invoice Item | `ii_1NfLm02eZv` |
| `acct_` | Account (Connect) | `acct_1NfKx32eZv` |

### Versioning delle API

Stripe mantiene un sistema di versioning basato sulla data. Ogni account ha una versione API predefinita (la versione corrente al momento della creazione dell'account). È possibile — e consigliato — eseguire il pin di una versione specifica nel codice:

```python
import stripe

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
stripe.api_version = '2024-06-20'  # Pin della versione API
```

Quando Stripe rilascia una nuova versione API, le breaking changes sono documentate nella changelog. Il proprio codice continua a funzionare con la versione pinnata. L'upgrade avviene manualmente, testando i cambiamenti:

```python
# Sovrascrivere la versione per una singola chiamata
stripe.Customer.create(
    email='test@example.com',
    stripe_version='2024-09-30.acacia'  # Testare una versione nuova
)
```

### Paginazione e List API

Tutte le list API di Stripe usano cursor-based pagination con il pattern `starting_after` / `ending_before`:

```python
def fetch_all_customers():
    """Iterare su tutti i customer usando auto-pagination"""
    customers = []
    for customer in stripe.Customer.list(limit=100).auto_paging_iter():
        customers.append(customer)
    return customers

# Oppure paginazione manuale
def fetch_customers_page(starting_after=None):
    return stripe.Customer.list(
        limit=100,
        starting_after=starting_after
    )
```

### Expand e Lazy Loading

Per default, Stripe restituisce riferimenti (ID) per le risorse correlate. Con `expand` si possono includere gli oggetti completi in una singola chiamata, riducendo le round-trip:

```python
# Senza expand: subscription.latest_invoice == 'in_xxx'
# Con expand: subscription.latest_invoice == { id: 'in_xxx', ... }
subscription = stripe.Subscription.retrieve(
    'sub_xxx',
    expand=[
        'latest_invoice',
        'latest_invoice.payment_intent',
        'default_payment_method'
    ]
)
```

### Idempotency Key

Ogni richiesta POST (creazione) può includere un `Idempotency-Key` header per garantire che la stessa operazione non venga eseguita due volte, anche in caso di retry:

```python
stripe.Customer.create(
    email='user@example.com',
    idempotency_key='create_customer_user_42'
)

# Se la rete fallisce e si ripete la chiamata con la stessa chiave,
# Stripe restituisce il risultato originale senza creare un duplicato.
```

Stripe conserva le idempotency key per 24 ore. Usare sempre chiavi deterministiche basate sull'operazione (es. `f"create_sub_{user_id}_{plan_id}"`).

### Rate Limiting

Stripe applica rate limit di 100 richieste/secondo in live mode e 25 richieste/secondo in test mode. Le risposte con status 429 includono un `Retry-After` header. Gli SDK ufficiali implementano retry automatico con exponential backoff:

```python
stripe.max_network_retries = 2  # Massimo 2 retry automatici
```

---

## Setup Iniziale e Architettura

### Struttura dell'Account Stripe

Prima di scrivere codice, è necessario comprendere la struttura dell'account Stripe e configurarlo correttamente:

**Test Mode vs Live Mode**: Stripe mantiene due ambienti completamente separati, ciascuno con le proprie API keys, dati e configurazioni. Tutto lo sviluppo e il testing avvengono in Test Mode. La migrazione a Live Mode avviene solo quando il sistema è validato. Le API keys di test iniziano con `sk_test_` e `pk_test_`, quelle live con `sk_live_` e `pk_live_`.

**API Keys**: Stripe utilizza due tipi di chiavi:
- **Secret Key (`sk_`)**: utilizzata server-side per tutte le operazioni. DEVE essere mantenuta segreta e mai esposta al client.
- **Publishable Key (`pk_`)**: utilizzata client-side per inizializzare Stripe.js e creare token di pagamento. Può essere inclusa nel codice frontend.

### Architettura dell'Integrazione

L'architettura tipica di un'integrazione Stripe per SaaS include quattro componenti:

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend   │      │   Backend    │      │   Stripe     │
│  (React/Vue) │◄────►│  (Node/Py)   │◄────►│   API        │
│              │      │              │      │              │
│ Stripe.js    │      │ Stripe SDK   │      │              │
│ Elements     │      │ Webhook      │      │              │
│              │      │ Handler      │      │              │
└─────────────┘      └──────┬───────┘      └──────┬───────┘
                            │                      │
                     ┌──────┴───────┐              │
                     │  Database     │              │
                     │              │◄─────────────┘
                     │ customers    │  Webhooks
                     │ subscriptions│
                     │ invoices     │
                     └──────────────┘
```

### Setup del Progetto

```bash
# Installazione delle dipendenze
# Node.js
npm install stripe

# Python
pip install stripe

# Ruby
gem install stripe
```

```python
# Configurazione iniziale in Python
import stripe
import os

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
stripe.api_version = '2023-10-16'  # Pinning della versione API

# Verificare la connettività
try:
    stripe.Account.retrieve()
    print("Stripe connection successful")
except stripe.error.AuthenticationError:
    print("Invalid API key")
```

### Modello di Dati Locale

È fondamentale mantenere una copia locale dei dati Stripe rilevanti nel proprio database. Non dipendere esclusivamente dalle API Stripe per recuperare informazioni: le API hanno rate limits e aggiungono latenza.

```sql
-- Schema di base per il billing
CREATE TABLE billing_customers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE billing_subscriptions (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES billing_customers(id),
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_price_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- active, past_due, canceled, trialing
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE billing_invoices (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES billing_customers(id),
    stripe_invoice_id VARCHAR(255) UNIQUE NOT NULL,
    amount_due INTEGER NOT NULL,  -- In centesimi
    amount_paid INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'eur',
    status VARCHAR(50) NOT NULL,
    invoice_pdf_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Products, Prices e il Modello Catalogo

### Gerarchia del Catalogo Stripe

In Stripe, la struttura dei prodotti segue una gerarchia a due livelli. Un **Product** rappresenta il bene o servizio venduto, mentre un **Price** rappresenta una specifica configurazione di prezzo per quel prodotto. Questa separazione è fondamentale: un singolo prodotto può avere molteplici prezzi (mensile, annuale, diverse valute, diversi tier).

```
Product (es. "Piano Pro")
  ├── Price (es. "€15/mese")
  ├── Price (es. "€150/anno")
  ├── Price (es. "$17/mese" — USD)
  └── Price (es. "€0.01/API call" — metered)

Product (es. "Piano Enterprise")
  ├── Price (es. "€99/mese")
  └── Price (es. "€990/anno")

Product (es. "Addon: Storage Extra")
  └── Price (es. "€5/mese per 100GB")
```

### Creare Prodotti e Prezzi

I prodotti e prezzi possono essere creati dalla Dashboard Stripe (consigliato per setup iniziale) oppure programmaticamente (necessario per automazione e ambienti multipli):

```python
def setup_stripe_catalog():
    """Setup completo del catalogo prodotti"""

    # --- Prodotto base: Free Tier ---
    free_product = stripe.Product.create(
        name='Piano Free',
        description='Funzionalità base per iniziare',
        metadata={'tier': 'free', 'sort_order': '1'},
        # Le immagini appaiono in Checkout, Portal, e fatture
        images=['https://example.com/assets/free-icon.png'],
    )

    free_price = stripe.Price.create(
        product=free_product.id,
        unit_amount=0,
        currency='eur',
        recurring={'interval': 'month'},
        metadata={'billing_period': 'monthly', 'tier': 'free'}
    )

    # --- Prodotto Pro ---
    pro_product = stripe.Product.create(
        name='Piano Pro',
        description='Tutte le funzionalità per team in crescita',
        metadata={'tier': 'pro', 'sort_order': '2'},
        # feature_list per Pricing Table hosted
        marketing_features=[
            {'name': 'Utenti illimitati'},
            {'name': '100GB storage'},
            {'name': 'Supporto prioritario'},
            {'name': 'API access'},
        ],
    )

    pro_monthly = stripe.Price.create(
        product=pro_product.id,
        unit_amount=1500,  # €15.00 in centesimi
        currency='eur',
        recurring={'interval': 'month'},
        metadata={'billing_period': 'monthly'}
    )

    pro_annual = stripe.Price.create(
        product=pro_product.id,
        unit_amount=15000,  # €150.00 (= €12.50/mese, sconto ~17%)
        currency='eur',
        recurring={'interval': 'year'},
        metadata={'billing_period': 'annual'}
    )

    # --- Prodotto Enterprise ---
    enterprise_product = stripe.Product.create(
        name='Piano Enterprise',
        description='Per grandi organizzazioni con esigenze custom',
        metadata={'tier': 'enterprise', 'sort_order': '3'},
    )

    enterprise_monthly = stripe.Price.create(
        product=enterprise_product.id,
        unit_amount=9900,  # €99.00
        currency='eur',
        recurring={'interval': 'month'},
        metadata={'billing_period': 'monthly'}
    )

    return {
        'free': {'product': free_product, 'monthly': free_price},
        'pro': {'product': pro_product, 'monthly': pro_monthly, 'annual': pro_annual},
        'enterprise': {'product': enterprise_product, 'monthly': enterprise_monthly},
    }
```

### Prezzi Archivati vs Attivi

I prezzi in Stripe non possono essere eliminati — solo archiviati. Un prezzo archiviato continua a funzionare per le subscription esistenti ma non può essere assegnato a nuove subscription. Questo è essenziale per gestire i cambi di listino:

```python
# Archiviare un vecchio prezzo
stripe.Price.modify('price_old_xxx', active=False)

# Il prezzo archiviato resta sulle subscription attive
# Le nuove subscription useranno il prezzo aggiornato
```

### Lookup Key per Prezzi Stabili

I Price ID cambiano se si ricrea un prezzo. Per evitare di hardcodare ID nel frontend, usare le `lookup_key`:

```python
# Creare un prezzo con lookup key
stripe.Price.create(
    product=pro_product.id,
    unit_amount=1500,
    currency='eur',
    recurring={'interval': 'month'},
    lookup_key='pro_monthly',            # Chiave stabile
    transfer_lookup_key=True,            # Se esiste già, la trasferisce a questo prezzo
)

# Recuperare il prezzo tramite lookup key
prices = stripe.Price.list(lookup_keys=['pro_monthly', 'pro_annual'])
# prices.data[0].id → il Price ID corrente per 'pro_monthly'
```

---

## Checkout Sessions — Pagamenti One-Time e Subscription

### Stripe Checkout vs Custom Payment Form

Stripe offre due approcci per raccogliere i pagamenti:

**Stripe Checkout**: una pagina di pagamento hosted da Stripe, completamente gestita. Il cliente viene reindirizzato a una pagina Stripe per inserire i dati di pagamento. Vantaggi: zero complessità frontend, PCI compliance automatica, supporto per tutti i metodi di pagamento, ottimizzazione mobile, localizzazione automatica. Svantaggio: meno personalizzazione dell'esperienza utente.

**Stripe Elements**: componenti UI embeddabili (card input, IBAN input, etc.) che si integrano direttamente nel proprio frontend. Vantaggi: pieno controllo sull'esperienza utente. Svantaggi: più codice da scrivere e mantenere, responsabilità PCI più ampia (SAQ A-EP invece di SAQ A).

Per la maggior parte delle startup SaaS, Stripe Checkout è la scelta ottimale nelle fasi iniziali. L'esperienza utente è eccellente e la riduzione della complessità è significativa.

### Creazione di una Checkout Session per Subscription

```python
# Backend: creare una Checkout Session per un nuovo abbonamento
@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    user = get_current_user()
    price_id = request.json.get('price_id')

    # Ottenere o creare il customer Stripe
    customer = get_or_create_stripe_customer(user)

    try:
        session = stripe.checkout.Session.create(
            customer=customer.stripe_customer_id,
            mode='subscription',
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            success_url=f'{BASE_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{BASE_URL}/billing/cancel',
            subscription_data={
                'trial_period_days': 14,
                'metadata': {
                    'user_id': str(user.id),
                    'plan': 'pro',
                }
            },
            allow_promotion_codes=True,
            billing_address_collection='required',
            tax_id_collection={'enabled': True},
        )

        return jsonify({'url': session.url})

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400


def get_or_create_stripe_customer(user):
    """Ottieni il customer Stripe esistente o creane uno nuovo"""
    billing_customer = BillingCustomer.query.filter_by(
        user_id=user.id
    ).first()

    if billing_customer:
        return billing_customer

    # Creare il customer su Stripe
    stripe_customer = stripe.Customer.create(
        email=user.email,
        name=user.name,
        metadata={'user_id': str(user.id)}
    )

    # Salvare localmente
    billing_customer = BillingCustomer(
        user_id=user.id,
        stripe_customer_id=stripe_customer.id,
        email=user.email,
        name=user.name
    )
    db.session.add(billing_customer)
    db.session.commit()

    return billing_customer
```

```javascript
// Frontend: reindirizzare l'utente alla Checkout Session
async function handleSubscribe(priceId) {
  try {
    const response = await fetch('/api/create-checkout-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ price_id: priceId }),
    });

    const { url } = await response.json();
    window.location.href = url;  // Redirect a Stripe Checkout
  } catch (error) {
    console.error('Error creating checkout session:', error);
  }
}
```

### Gestione del Success URL

Dopo il pagamento, Stripe reindirizza alla `success_url`. È importante NON considerare il pagamento confermato solo perché l'utente è arrivato alla success page — la conferma ufficiale arriva via webhook.

```python
@app.route('/billing/success')
def billing_success():
    session_id = request.args.get('session_id')

    # Recuperare la session per mostrare informazioni
    session = stripe.checkout.Session.retrieve(session_id)

    # NON attivare la subscription qui.
    # La subscription viene attivata nel webhook handler.
    # Mostrare un messaggio di attesa/conferma.

    return render_template('billing_success.html', session=session)
```

---

## Stripe Elements — Pagamenti Embeddabili

### Quando Usare Elements

Stripe Elements è la scelta quando si ha bisogno di pieno controllo sull'UI del pagamento, mantenendolo integrato nella propria applicazione senza redirect. Elements gestisce la raccolta sicura dei dati della carta direttamente nel browser dell'utente, inviandoli a Stripe senza che transitino dal proprio server.

### Payment Element — Il Componente Universale

Il `Payment Element` è il componente Elements più moderno e flessibile: mostra automaticamente i metodi di pagamento rilevanti in base alla localizzazione del cliente e alla configurazione dell'account Stripe.

```javascript
// Frontend: inizializzare Payment Element
const stripe = Stripe('pk_test_xxx');

// 1. Creare un PaymentIntent o SetupIntent sul backend
const response = await fetch('/api/create-payment-intent', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ price_id: 'price_xxx' }),
});
const { client_secret } = await response.json();

// 2. Montare il Payment Element
const elements = stripe.elements({
  clientSecret: client_secret,
  appearance: {
    theme: 'stripe',       // 'stripe', 'night', 'flat', 'none'
    variables: {
      colorPrimary: '#0570de',
      borderRadius: '8px',
      fontFamily: 'Inter, system-ui, sans-serif',
    },
  },
});

const paymentElement = elements.create('payment', {
  layout: 'tabs',          // 'tabs', 'accordion', 'auto'
});
paymentElement.mount('#payment-element');

// 3. Gestire il submit del form
document.getElementById('payment-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const { error } = await stripe.confirmPayment({
    elements,
    confirmParams: {
      return_url: 'https://example.com/billing/complete',
    },
  });

  if (error) {
    document.getElementById('error-message').textContent = error.message;
  }
});
```

```python
# Backend: creare il PaymentIntent per Elements
@app.route('/api/create-payment-intent', methods=['POST'])
def create_payment_intent():
    user = get_current_user()
    customer = get_or_create_stripe_customer(user)

    intent = stripe.PaymentIntent.create(
        amount=1500,            # €15.00 in centesimi
        currency='eur',
        customer=customer.stripe_customer_id,
        automatic_payment_methods={'enabled': True},
        metadata={'user_id': str(user.id)},
    )

    return jsonify({'client_secret': intent.client_secret})
```

### Elements per Subscription (SetupIntent)

Per le subscription, il pattern è diverso: si raccoglie il metodo di pagamento con un `SetupIntent`, poi si crea la subscription server-side:

```python
# Backend: creare SetupIntent per salvare il metodo di pagamento
@app.route('/api/create-setup-intent', methods=['POST'])
def create_setup_intent():
    user = get_current_user()
    customer = get_or_create_stripe_customer(user)

    intent = stripe.SetupIntent.create(
        customer=customer.stripe_customer_id,
        automatic_payment_methods={'enabled': True},
        metadata={'user_id': str(user.id)},
    )
    return jsonify({'client_secret': intent.client_secret})


# Dopo che il frontend conferma il SetupIntent, creare la subscription
@app.route('/api/create-subscription', methods=['POST'])
def create_subscription():
    user = get_current_user()
    customer = get_billing_customer(user.id)
    price_id = request.json.get('price_id')

    subscription = stripe.Subscription.create(
        customer=customer.stripe_customer_id,
        items=[{'price': price_id}],
        default_payment_method=request.json.get('payment_method_id'),
        trial_period_days=14,
        metadata={'user_id': str(user.id)},
    )
    return jsonify({'subscription_id': subscription.id, 'status': subscription.status})
```

---

## Payment Links — Pagamenti Senza Codice

### Cos'è un Payment Link

I Payment Links sono URL permanenti che aprono una pagina di pagamento Stripe hosted. Non richiedono backend, integrazione API, o codice frontend. Si creano dalla Dashboard o via API e si condividono ovunque: email, SMS, social media, QR code.

```python
# Creare un Payment Link via API
payment_link = stripe.PaymentLink.create(
    line_items=[{'price': 'price_xxx', 'quantity': 1}],
    after_completion={
        'type': 'redirect',
        'redirect': {'url': 'https://example.com/thank-you'},
    },
    allow_promotion_codes=True,
    automatic_tax={'enabled': True},
    # Personalizzazione
    custom_text={
        'submit': {'message': 'Il tuo abbonamento partirà dopo la conferma del pagamento.'},
    },
)
# payment_link.url → 'https://buy.stripe.com/xxx'
```

### Limitazioni

I Payment Links non supportano la pre-associazione a un Customer esistente, quindi non sono ideali per upgrade/downgrade di utenti già registrati. Sono perfetti per:
- Landing page senza backend
- Condivisione diretta via email/chat
- Campagne marketing
- Vendita di addon o one-time purchases

---

## Checkout vs Elements vs Payment Links — Quando Usare Cosa

| Criterio | Checkout Session | Elements | Payment Links |
|----------|-----------------|----------|---------------|
| Complessità di implementazione | Bassa | Media-Alta | Zero (no code) |
| Personalizzazione UI | Limitata (temi) | Totale | Limitata |
| PCI scope | SAQ A (minimo) | SAQ A-EP | SAQ A (minimo) |
| Pre-associazione Customer | Sì | Sì | No |
| Metodi di pagamento | Tutti automatici | Tutti configurabili | Tutti automatici |
| Codice backend necessario | Sì (create session) | Sì (Intent + sub) | No |
| Codice frontend necessario | Minimo (redirect) | Significativo | No |
| Ottimizzazione mobile | Automatica | Manuale | Automatica |
| A/B testing del form | No | Sì | No |
| Subscription management | Sì | Sì | Sì |
| Caso d'uso ideale | MVP, standard SaaS | Brand-critical UX | Marketing, no-code |

**Raccomandazione pratica**: iniziare con Checkout Sessions. Migrare a Elements solo quando il brand e l'UX lo richiedono (di solito dopo il product-market fit). Usare Payment Links per vendite one-off, link condivisibili, e landing page statiche.

---

## Subscriptions API — Gestione Completa degli Abbonamenti

### Struttura dei Prodotti e Prezzi

In Stripe, la struttura dei prodotti segue una gerarchia:

```
Product (es. "Piano Pro")
  └── Price (es. "€15/mese")
  └── Price (es. "€150/anno")
  └── Price (es. "€0.01/API call" - metered)

Product (es. "Piano Enterprise")
  └── Price (es. "€99/mese")
  └── Price (es. "€990/anno")
```

```python
# Creare prodotti e prezzi programmaticamente
def setup_stripe_products():
    # Creare il prodotto
    pro_product = stripe.Product.create(
        name='Piano Pro',
        description='Tutte le funzionalità per team in crescita',
        metadata={'tier': 'pro'}
    )

    # Prezzo mensile
    pro_monthly = stripe.Price.create(
        product=pro_product.id,
        unit_amount=1500,  # €15.00 in centesimi
        currency='eur',
        recurring={'interval': 'month'},
        metadata={'billing_period': 'monthly'}
    )

    # Prezzo annuale (con sconto)
    pro_annual = stripe.Price.create(
        product=pro_product.id,
        unit_amount=15000,  # €150.00 in centesimi (= €12.50/mese)
        currency='eur',
        recurring={'interval': 'year'},
        metadata={'billing_period': 'annual'}
    )

    return pro_product, pro_monthly, pro_annual
```

### Upgrade e Downgrade di Piano

La gestione degli upgrade e downgrade è uno degli aspetti più complessi del billing SaaS:

```python
def change_subscription_plan(user_id: int, new_price_id: str):
    """Cambia il piano di un utente (upgrade o downgrade)"""

    subscription = get_user_subscription(user_id)

    # Recuperare la subscription da Stripe
    stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)

    # Aggiornare la subscription con il nuovo prezzo
    updated_sub = stripe.Subscription.modify(
        stripe_sub.id,
        items=[{
            'id': stripe_sub['items']['data'][0].id,
            'price': new_price_id,
        }],
        # Proration behavior:
        # 'create_prorations' - calcola il credito/debito proporzionale (default)
        # 'none' - nessun proration, il nuovo prezzo inizia al prossimo ciclo
        # 'always_invoice' - crea e paga immediatamente una fattura di proration
        proration_behavior='create_prorations',

        # Per upgrade: addebitare immediatamente
        # Per downgrade: applicare al prossimo ciclo
        # payment_behavior='default_incomplete',  # richiede conferma pagamento
    )

    # Aggiornare il record locale
    subscription.stripe_price_id = new_price_id
    subscription.updated_at = datetime.utcnow()
    db.session.commit()

    return updated_sub
```

### Cancellazione della Subscription

```python
def cancel_subscription(user_id: int, immediate: bool = False):
    """Cancella la subscription di un utente"""

    subscription = get_user_subscription(user_id)

    if immediate:
        # Cancellazione immediata - l'accesso termina subito
        stripe.Subscription.delete(subscription.stripe_subscription_id)
    else:
        # Cancellazione alla fine del periodo corrente
        # L'utente mantiene l'accesso fino alla fine del periodo pagato
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )

    # Aggiornare il record locale
    subscription.cancel_at_period_end = True
    subscription.updated_at = datetime.utcnow()
    db.session.commit()
```

### Trial Period e Grace Period

```python
# Creare una subscription con trial
session = stripe.checkout.Session.create(
    customer=customer_id,
    mode='subscription',
    line_items=[{'price': price_id, 'quantity': 1}],
    subscription_data={
        'trial_period_days': 14,
        'trial_settings': {
            'end_behavior': {
                'missing_payment_method': 'cancel'
                # oppure 'pause' per sospendere invece di cancellare
            }
        }
    },
    # Richiedere il metodo di pagamento anche durante il trial
    payment_method_collection='always',
    success_url=f'{BASE_URL}/billing/success',
    cancel_url=f'{BASE_URL}/billing/cancel',
)
```

---

## Ciclo di Vita delle Subscription

### Diagramma degli Stati

Una subscription in Stripe attraversa diversi stati durante il suo ciclo di vita. Comprendere ogni transizione è essenziale per gestire correttamente l'accesso alle feature:

```
                     ┌──────────────────────────────┐
                     │          CREATED              │
                     │ (incomplete / incomplete_expired) │
                     └──────────┬───────────────────┘
                                │ Pagamento confermato
                                ▼
                     ┌──────────────────────┐
              ┌──────│       TRIALING        │
              │      └──────────┬───────────┘
              │                 │ Trial finisce + pagamento OK
              │                 ▼
              │      ┌──────────────────────┐
              │      │        ACTIVE         │◄─── Rinnovo pagato
              │      └──┬──────────┬────────┘
              │         │          │
              │   Pagamento    cancel_at_period_end=true
              │   fallito          │
              │         │          ▼
              │         │  ┌──────────────────────┐
              │         │  │      ACTIVE           │
              │         │  │ (cancel_at_period_end) │
              │         │  └──────────┬────────────┘
              │         │             │ Periodo scade
              │         ▼             ▼
              │  ┌──────────────┐  ┌──────────────┐
              │  │   PAST_DUE   │  │   CANCELED    │
              │  └──────┬───────┘  └──────────────┘
              │         │
              │   Tutti i retry falliti
              │         │
              │         ▼
              │  ┌──────────────┐
              └─►│  UNPAID /     │
                 │  CANCELED     │
                 └──────────────┘
```

### Gestire Ogni Stato nel Codice

```python
SUBSCRIPTION_ACCESS_MAP = {
    'trialing': 'full',         # Accesso completo durante il trial
    'active': 'full',           # Accesso completo, pagamento OK
    'past_due': 'limited',      # Grace period — banner di avviso
    'unpaid': 'blocked',        # Accesso bloccato fino al pagamento
    'canceled': 'none',         # Nessun accesso
    'incomplete': 'none',       # Pagamento iniziale non confermato
    'incomplete_expired': 'none',
    'paused': 'none',           # Subscription in pausa
}

def check_feature_access(user_id: int, feature: str) -> bool:
    """Verifica se l'utente ha accesso a una feature in base allo stato subscription"""
    sub = get_user_subscription(user_id)
    if not sub:
        return feature in FREE_FEATURES

    access_level = SUBSCRIPTION_ACCESS_MAP.get(sub.status, 'none')

    if access_level == 'full':
        return True
    elif access_level == 'limited':
        # Grace period: accesso alle feature esistenti ma non a nuove
        return feature in EXISTING_FEATURE_SET
    else:
        return feature in FREE_FEATURES


def handle_subscription_updated(event):
    """Handler per customer.subscription.updated"""
    subscription = event.data.object
    previous_attributes = event.data.previous_attributes

    sub = BillingSubscription.query.filter_by(
        stripe_subscription_id=subscription.id
    ).first()
    if not sub:
        return

    old_status = previous_attributes.get('status', sub.status)
    new_status = subscription.status

    sub.status = new_status
    sub.stripe_price_id = subscription['items']['data'][0].price.id
    sub.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
    sub.cancel_at_period_end = subscription.cancel_at_period_end
    db.session.commit()

    # Reagire ai cambi di stato
    if old_status != new_status:
        if new_status == 'past_due':
            send_email(sub.customer.user_id, 'payment_issue')
        elif new_status == 'active' and old_status == 'past_due':
            send_email(sub.customer.user_id, 'payment_resolved')
        elif new_status == 'canceled':
            revoke_plan_features(sub.customer.user_id)
```

### Riattivare una Subscription Cancellata

Se l'utente ha cancellato con `cancel_at_period_end=True` ma cambia idea prima della fine del periodo:

```python
def reactivate_subscription(user_id: int):
    """Riattiva una subscription in fase di cancellazione"""
    sub = get_user_subscription(user_id)

    if not sub.cancel_at_period_end:
        raise ValueError("La subscription non è in fase di cancellazione")

    stripe.Subscription.modify(
        sub.stripe_subscription_id,
        cancel_at_period_end=False
    )
    sub.cancel_at_period_end = False
    db.session.commit()
```

### Pause e Resume

Stripe supporta la pausa delle subscription (utile per stagionalità o utenti che vogliono una pausa temporanea):

```python
def pause_subscription(user_id: int, resume_at: datetime = None):
    """Mette in pausa la subscription — la fatturazione si ferma"""
    sub = get_user_subscription(user_id)

    params = {
        'pause_collection': {
            'behavior': 'void',  # 'void' = niente fatture, 'mark_uncollectible', 'keep_as_draft'
        }
    }
    if resume_at:
        params['pause_collection']['resumes_at'] = int(resume_at.timestamp())

    stripe.Subscription.modify(sub.stripe_subscription_id, **params)
    sub.status = 'paused'
    db.session.commit()


def resume_subscription(user_id: int):
    """Riprende una subscription in pausa"""
    sub = get_user_subscription(user_id)

    stripe.Subscription.modify(
        sub.stripe_subscription_id,
        pause_collection=''  # Stringa vuota per rimuovere la pausa
    )
    sub.status = 'active'
    db.session.commit()
```

---

## Proration — Calcolo Proporzionale

### Come Funziona la Proration

La proration è il calcolo proporzionale che avviene quando un utente cambia piano a metà ciclo di fatturazione. Stripe gestisce la proration automaticamente, ma è importante comprenderne la meccanica per comunicarla correttamente all'utente.

**Esempio**: l'utente paga €30/mese (Pro) e al giorno 15 fa upgrade a €90/mese (Enterprise).
- Credito per Pro non usato: €30 × (15/30) = €15
- Costo Enterprise rimanente: €90 × (15/30) = €45
- Importo netto da addebitare: €45 - €15 = €30

### Preview della Proration

Prima di effettuare il cambio piano, mostrare all'utente una preview con `upcoming_invoice`:

```python
def preview_plan_change(user_id: int, new_price_id: str) -> dict:
    """Mostra il costo del cambio piano prima di confermarlo"""
    sub = get_user_subscription(user_id)
    stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)

    # Simulare il cambio piano senza eseguirlo
    upcoming = stripe.Invoice.upcoming(
        customer=sub.customer.stripe_customer_id,
        subscription=stripe_sub.id,
        subscription_items=[{
            'id': stripe_sub['items']['data'][0].id,
            'price': new_price_id,
        }],
        subscription_proration_behavior='create_prorations',
    )

    # Estrarre solo le righe di proration
    proration_lines = [
        line for line in upcoming.lines.data
        if line.proration
    ]

    return {
        'total_due': upcoming.total,           # Totale in centesimi
        'credit': sum(l.amount for l in proration_lines if l.amount < 0),
        'charge': sum(l.amount for l in proration_lines if l.amount > 0),
        'currency': upcoming.currency,
        'next_billing_date': datetime.fromtimestamp(upcoming.period_end).isoformat(),
    }
```

### Opzioni di Proration Behavior

| Valore | Comportamento | Caso d'uso |
|--------|--------------|------------|
| `create_prorations` | Crea righe di proration, addebitate alla prossima fattura | Default — per la maggior parte dei casi |
| `always_invoice` | Crea una fattura immediata con il proration | Upgrade con addebito istantaneo |
| `none` | Nessun proration — il nuovo prezzo parte dal prossimo ciclo | Downgrade semplice |

---

## Webhook Integration — Event-Driven Architecture

### Perché i Webhook Sono Critici

I webhook sono il meccanismo attraverso il quale Stripe comunica al proprio backend gli eventi che accadono nel sistema di pagamento. Senza webhook, il backend non ha modo affidabile di sapere quando:
- Un pagamento è stato confermato
- Una subscription è stata attivata, rinnovata o cancellata
- Un pagamento è fallito
- Un rimborso è stato processato
- Il metodo di pagamento è stato aggiornato

**Regola fondamentale**: non dipendere mai dal redirect della Checkout Session per confermare un pagamento. Il webhook è l'unica fonte affidabile di verità.

### Implementazione del Webhook Handler

```python
import stripe
from flask import Flask, request, jsonify

WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    # Idempotency: verificare che l'evento non sia già stato processato
    if EventLog.query.filter_by(stripe_event_id=event.id).first():
        return jsonify({'status': 'already_processed'}), 200

    # Dispatch dell'evento al handler appropriato
    handler = WEBHOOK_HANDLERS.get(event.type)
    if handler:
        try:
            handler(event)
            # Registrare l'evento come processato
            log = EventLog(stripe_event_id=event.id, event_type=event.type)
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Webhook handler error: {e}")
            return jsonify({'error': str(e)}), 500
    else:
        logger.info(f"Unhandled event type: {event.type}")

    return jsonify({'status': 'success'}), 200


# Handler per eventi specifici
def handle_checkout_session_completed(event):
    session = event.data.object

    if session.mode == 'subscription':
        subscription_id = session.subscription
        customer_id = session.customer
        user_id = session.metadata.get('user_id')

        # Recuperare i dettagli della subscription
        subscription = stripe.Subscription.retrieve(subscription_id)

        # Creare/aggiornare il record locale
        billing_sub = BillingSubscription(
            customer_id=get_billing_customer(customer_id).id,
            stripe_subscription_id=subscription_id,
            stripe_price_id=subscription['items']['data'][0].price.id,
            status=subscription.status,
            current_period_start=datetime.fromtimestamp(
                subscription.current_period_start
            ),
            current_period_end=datetime.fromtimestamp(
                subscription.current_period_end
            ),
        )
        db.session.add(billing_sub)
        db.session.commit()

        # Attivare le feature del piano per l'utente
        activate_plan_features(user_id, subscription['items']['data'][0].price.id)


def handle_invoice_paid(event):
    invoice = event.data.object

    # Aggiornare la subscription locale con il nuovo periodo
    if invoice.subscription:
        sub = BillingSubscription.query.filter_by(
            stripe_subscription_id=invoice.subscription
        ).first()
        if sub:
            stripe_sub = stripe.Subscription.retrieve(invoice.subscription)
            sub.current_period_start = datetime.fromtimestamp(
                stripe_sub.current_period_start
            )
            sub.current_period_end = datetime.fromtimestamp(
                stripe_sub.current_period_end
            )
            sub.status = 'active'
            db.session.commit()

    # Salvare la fattura localmente
    save_invoice_locally(invoice)


def handle_invoice_payment_failed(event):
    invoice = event.data.object

    # Aggiornare lo stato della subscription
    if invoice.subscription:
        sub = BillingSubscription.query.filter_by(
            stripe_subscription_id=invoice.subscription
        ).first()
        if sub:
            sub.status = 'past_due'
            db.session.commit()

    # Notificare l'utente
    customer = BillingCustomer.query.filter_by(
        stripe_customer_id=invoice.customer
    ).first()
    if customer:
        send_payment_failed_email(customer.user_id)


def handle_customer_subscription_deleted(event):
    subscription = event.data.object

    sub = BillingSubscription.query.filter_by(
        stripe_subscription_id=subscription.id
    ).first()
    if sub:
        sub.status = 'canceled'
        db.session.commit()

        # Revocare le feature del piano
        revoke_plan_features(sub.customer.user_id)


# Registro degli handler
WEBHOOK_HANDLERS = {
    'checkout.session.completed': handle_checkout_session_completed,
    'invoice.paid': handle_invoice_paid,
    'invoice.payment_failed': handle_invoice_payment_failed,
    'customer.subscription.deleted': handle_customer_subscription_deleted,
    'customer.subscription.updated': handle_subscription_updated,
    'customer.subscription.trial_will_end': handle_trial_ending,
}
```

### Eventi Critici da Gestire

| Evento | Descrizione | Azione |
|---|---|---|
| `checkout.session.completed` | Checkout completato | Attivare la subscription |
| `invoice.paid` | Fattura pagata | Confermare il rinnovo |
| `invoice.payment_failed` | Pagamento fallito | Notificare, degradare accesso |
| `customer.subscription.updated` | Subscription modificata | Aggiornare piano/status |
| `customer.subscription.deleted` | Subscription cancellata | Revocare accesso |
| `customer.subscription.trial_will_end` | Trial in scadenza (3 giorni) | Notificare l'utente |
| `customer.updated` | Customer aggiornato | Sincronizzare dati locali |

---

## Webhook Best Practices Avanzate

### Verifica della Firma (Signature Verification)

Ogni webhook inviato da Stripe include un header `Stripe-Signature` che contiene un timestamp e una firma HMAC-SHA256. Verificare questa firma è obbligatorio per prevenire attacchi di spoofing:

```python
# La firma ha il formato: t=timestamp,v1=signature
# Stripe calcola la firma come HMAC-SHA256 di:
#   "{timestamp}.{raw_body}"
# usando il webhook secret come chiave.

# ERRORE CRITICO: parsare il JSON prima della verifica
# Il body DEVE essere il raw payload, non il JSON parsato.

@app.route('/webhooks/stripe', methods=['POST'])
def webhook():
    # CORRETTO: raw bytes
    payload = request.get_data(as_text=False)
    sig = request.headers.get('Stripe-Signature')

    # SBAGLIATO: request.json o request.get_json()
    # parsare il JSON altera il payload e la verifica fallisce

    event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
```

In Express/Node.js il problema analogo è il body-parser che parsifica il JSON prima del webhook route:

```javascript
// CORRETTO: usare raw body per il webhook endpoint
app.post('/webhooks/stripe',
  express.raw({ type: 'application/json' }),  // raw body
  (req, res) => {
    const sig = req.headers['stripe-signature'];
    const event = stripe.webhooks.constructEvent(req.body, sig, endpointSecret);
    // ...
  }
);

// Applicare il JSON parser a tutte le ALTRE route
app.use(express.json());
```

### Idempotency nella Gestione dei Webhook

Stripe garantisce at-least-once delivery: lo stesso evento può essere inviato più volte. Il proprio handler DEVE essere idempotente:

```python
# Pattern robusto: event log + upsert
CREATE TABLE webhook_event_log (
    stripe_event_id VARCHAR(255) PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    processed_at TIMESTAMP DEFAULT NOW(),
    idempotency_hash VARCHAR(64)  -- Hash del payload per detect duplicati
);

def process_event_idempotently(event):
    """Wrapper idempotente per webhook handler"""
    # Check 1: evento già processato?
    existing = db.execute(
        "SELECT 1 FROM webhook_event_log WHERE stripe_event_id = %s",
        (event.id,)
    ).fetchone()

    if existing:
        logger.info(f"Evento {event.id} già processato, skip")
        return True

    # Check 2: lock pessimistico per evitare race condition
    # tra worker concorrenti
    try:
        db.execute(
            """INSERT INTO webhook_event_log (stripe_event_id, event_type)
               VALUES (%s, %s)
               ON CONFLICT (stripe_event_id) DO NOTHING""",
            (event.id, event.type)
        )
        db.commit()
    except IntegrityError:
        logger.info(f"Race condition su evento {event.id}, skip")
        return True

    return False  # Evento non ancora processato, procedere
```

### Retry Logic e Timeout

Stripe si aspetta una risposta 2xx entro 20 secondi. Se il server non risponde o risponde con un errore:
- Stripe riprova fino a 3 volte su un periodo di ore
- Le retry avvengono con backoff: ~1 ora, ~6 ore, ~2 giorni

**Implicazioni architetturali**: se l'elaborazione del webhook richiede più di qualche secondo (es. chiamate a servizi esterni, operazioni batch), rispondere 200 immediatamente e processare in modo asincrono:

```python
@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    # Verificare la firma (veloce)
    event = verify_signature(request)

    # Rispondere 200 subito — Stripe non deve attendere
    # Enqueue il processing asincrono
    celery_task_process_webhook.delay(event.id, event.type, event.data.object)

    return '', 200


@celery.task(bind=True, max_retries=3)
def celery_task_process_webhook(self, event_id, event_type, data):
    """Processare il webhook in modo asincrono con retry"""
    try:
        handler = WEBHOOK_HANDLERS.get(event_type)
        if handler:
            handler(data)
    except Exception as exc:
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### Ordine degli Eventi

Stripe NON garantisce l'ordine di consegna degli eventi. Un evento `invoice.paid` potrebbe arrivare prima di `checkout.session.completed`. Il proprio handler deve essere resiliente:

```python
def handle_invoice_paid(event):
    invoice = event.data.object

    # La subscription potrebbe non esistere ancora nel DB locale
    # se checkout.session.completed non è ancora stato processato
    sub = BillingSubscription.query.filter_by(
        stripe_subscription_id=invoice.subscription
    ).first()

    if not sub:
        # Creare un record provvisorio — checkout.session.completed
        # lo completerà successivamente
        stripe_sub = stripe.Subscription.retrieve(invoice.subscription)
        sub = create_provisional_subscription(stripe_sub)

    sub.status = 'active'
    db.session.commit()
```

---

## Customer Portal — Self-Service per i Clienti

### Configurazione e Utilizzo

Il Customer Portal di Stripe è una pagina hosted che permette ai clienti di gestire autonomamente la propria subscription: aggiornare il metodo di pagamento, cambiare piano, visualizzare le fatture, e cancellare la subscription.

```python
@app.route('/api/create-portal-session', methods=['POST'])
def create_portal_session():
    user = get_current_user()
    customer = get_billing_customer(user.id)

    session = stripe.billing_portal.Session.create(
        customer=customer.stripe_customer_id,
        return_url=f'{BASE_URL}/settings/billing',
    )

    return jsonify({'url': session.url})
```

La configurazione del Customer Portal avviene nella Dashboard Stripe (Settings → Billing → Customer Portal) dove si definiscono: quali piani sono disponibili per upgrade/downgrade, se il cliente può cancellare la subscription, se può aggiornare le informazioni di fatturazione, e quali metodi di pagamento sono accettati.

### Configurazione Programmatica del Portal

Per ambienti multipli (dev/staging/prod), la configurazione del portal si gestisce via API:

```python
def configure_billing_portal():
    """Configurare il Customer Portal via API"""
    configuration = stripe.billing_portal.Configuration.create(
        business_profile={
            'headline': 'Gestisci il tuo abbonamento MyApp',
            'privacy_policy_url': 'https://example.com/privacy',
            'terms_of_service_url': 'https://example.com/tos',
        },
        features={
            'subscription_update': {
                'enabled': True,
                'default_allowed_updates': ['price', 'quantity'],
                'proration_behavior': 'create_prorations',
                'products': [
                    {
                        'product': 'prod_pro_xxx',
                        'prices': ['price_pro_monthly', 'price_pro_annual'],
                    },
                    {
                        'product': 'prod_enterprise_xxx',
                        'prices': ['price_ent_monthly', 'price_ent_annual'],
                    },
                ],
            },
            'subscription_cancel': {
                'enabled': True,
                'mode': 'at_period_end',  # 'at_period_end' o 'immediately'
                'cancellation_reason': {
                    'enabled': True,
                    'options': [
                        'too_expensive', 'missing_features',
                        'switched_service', 'unused', 'other',
                    ],
                },
            },
            'customer_update': {
                'enabled': True,
                'allowed_updates': ['email', 'address', 'tax_id'],
            },
            'invoice_history': {'enabled': True},
            'payment_method_update': {'enabled': True},
        },
    )
    return configuration
```

### Deep Link nel Portal

Si possono creare link diretti a sezioni specifiche del portal:

```python
# Link diretto alla sezione di aggiornamento del metodo di pagamento
session = stripe.billing_portal.Session.create(
    customer=customer_id,
    return_url=f'{BASE_URL}/settings/billing',
    flow_data={
        'type': 'payment_method_update',
    },
)
```

---

## Metered Billing — Fatturazione a Consumo

### Architettura del Metered Billing

Il metered billing è il modello in cui il cliente paga in base all'utilizzo effettivo, non in base a un prezzo fisso. Esempi: API calls, storage utilizzato, email inviate, compute hours.

```python
# Creare un prezzo metered
metered_price = stripe.Price.create(
    product=product_id,
    currency='eur',
    recurring={
        'interval': 'month',
        'usage_type': 'metered',
        'aggregate_usage': 'sum',  # sum, last_during_period, last_ever, max
    },
    unit_amount=1,  # €0.01 per unità
    billing_scheme='per_unit',
)
```

### Reporting dell'Utilizzo

```python
# Reportare l'utilizzo a Stripe
def report_usage(subscription_item_id: str, quantity: int,
                  timestamp: int = None):
    """Reporta l'utilizzo per un subscription item metered"""

    usage_record = stripe.SubscriptionItem.create_usage_record(
        subscription_item_id,
        quantity=quantity,
        timestamp=timestamp or int(time.time()),
        action='increment',  # 'increment' o 'set'
    )

    return usage_record


# Esempio: reportare l'utilizzo API ogni ora
def report_hourly_api_usage():
    """Job schedulato ogni ora per reportare l'utilizzo API"""

    active_subscriptions = BillingSubscription.query.filter_by(
        status='active'
    ).all()

    for sub in active_subscriptions:
        # Recuperare il conteggio API calls dell'ultima ora
        api_calls = get_api_calls_last_hour(sub.customer.user_id)

        if api_calls > 0:
            stripe_sub = stripe.Subscription.retrieve(
                sub.stripe_subscription_id
            )
            # Trovare il subscription item metered
            for item in stripe_sub['items']['data']:
                if item.price.recurring.usage_type == 'metered':
                    report_usage(item.id, api_calls)
                    break
```

### Tiered Pricing

Per pricing a scaglioni (es. prime 1,000 API calls gratuite, poi €0.01/call):

```python
# Prezzo con tier graduati
tiered_price = stripe.Price.create(
    product=product_id,
    currency='eur',
    recurring={
        'interval': 'month',
        'usage_type': 'metered',
        'aggregate_usage': 'sum',
    },
    billing_scheme='tiered',
    tiers_mode='graduated',  # 'graduated' o 'volume'
    tiers=[
        {'up_to': 1000, 'unit_amount': 0},           # Prime 1,000 gratuite
        {'up_to': 10000, 'unit_amount': 1},           # 1,001-10,000: €0.01
        {'up_to': 100000, 'unit_amount': 0.5},        # 10,001-100,000: €0.005
        {'up_to': 'inf', 'unit_amount': 0.25},        # 100,001+: €0.0025
    ],
)
```

---

## Stripe Meters — API di Nuova Generazione per il Consumo

### Differenza tra Usage Records e Meters

L'approccio tradizionale (`create_usage_record` su SubscriptionItem) ha limitazioni: richiede il `subscription_item_id` e funziona solo con subscription già attive. **Stripe Meters** è l'API più recente che disaccoppia l'ingestione degli eventi di utilizzo dalla subscription stessa.

Con Meters:
- Si invia l'utilizzo come eventi generici associati al customer
- Il meter aggrega gli eventi automaticamente
- La fatturazione viene calcolata in base all'aggregazione del meter
- Si può visualizzare l'utilizzo in real-time

### Creare un Meter

```python
# Creare un Meter per tracciare le API calls
meter = stripe.billing.Meter.create(
    display_name='API Requests',
    event_name='api_request',        # Nome dell'evento da inviare
    default_aggregation={
        'formula': 'sum',            # 'sum', 'count', 'last'
    },
    customer_mapping={
        'type': 'by_id',
        'event_payload_key': 'stripe_customer_id',
    },
)
```

### Inviare Eventi di Utilizzo

```python
# Inviare un evento di utilizzo al Meter
def track_api_usage(customer_id: str, endpoint: str, tokens_used: int = 1):
    """Invia un evento di utilizzo al Meter Stripe"""
    stripe.billing.MeterEvent.create(
        event_name='api_request',
        payload={
            'stripe_customer_id': customer_id,
            'value': str(tokens_used),
        },
        # Timestamp opzionale — default è now()
    )


# Batch: inviare molti eventi in una volta
# Utile per sincronizzazione periodica piuttosto che real-time
def sync_usage_batch(customer_id: str, events: list):
    """Invia un batch di eventi di utilizzo"""
    for event in events:
        stripe.billing.MeterEvent.create(
            event_name='api_request',
            payload={
                'stripe_customer_id': customer_id,
                'value': str(event['quantity']),
            },
            timestamp=event['timestamp'],
        )
```

### Creare un Prezzo Basato su Meter

```python
# Prezzo associato al Meter
meter_price = stripe.Price.create(
    product=product_id,
    currency='eur',
    billing_scheme='per_unit',
    unit_amount=1,  # €0.01 per unità
    recurring={
        'interval': 'month',
        'usage_type': 'metered',
        'meter': meter.id,           # Collegamento al Meter
    },
)
```

### Consultare l'Utilizzo in Tempo Reale

```python
# Recuperare il riepilogo di utilizzo corrente
summary = stripe.billing.Meter.list_event_summaries(
    meter.id,
    customer='cus_xxx',
    start_time=int(period_start.timestamp()),
    end_time=int(datetime.utcnow().timestamp()),
)
# summary.data[0].aggregated_value → utilizzo totale nel periodo
```

---

## Invoice API — Fatturazione Personalizzata

### Creare Fatture Manuali

Per scenari che richiedono fatturazione personalizzata (one-time charges, professional services, setup fees):

```python
def create_custom_invoice(customer_id: str, items: list, due_days: int = 30):
    """Creare una fattura personalizzata"""

    # Creare gli invoice items
    for item in items:
        stripe.InvoiceItem.create(
            customer=customer_id,
            amount=item['amount'],  # In centesimi
            currency='eur',
            description=item['description'],
        )

    # Creare e finalizzare la fattura
    invoice = stripe.Invoice.create(
        customer=customer_id,
        collection_method='send_invoice',
        days_until_due=due_days,
        auto_advance=True,  # Finalizzare automaticamente
    )

    # Finalizzare la fattura (la rende immutabile e genera il PDF)
    invoice = stripe.Invoice.finalize_invoice(invoice.id)

    # Inviare la fattura via email
    stripe.Invoice.send_invoice(invoice.id)

    return invoice
```

### Credit Notes (Note di Credito)

Per emettere rimborsi parziali o crediti senza fare un refund completo:

```python
def issue_credit_note(invoice_id: str, amount: int, reason: str):
    """Emette una nota di credito su una fattura"""
    credit_note = stripe.CreditNote.create(
        invoice=invoice_id,
        lines=[{
            'type': 'custom_line_item',
            'unit_amount': amount,
            'quantity': 1,
            'description': reason,
        }],
        reason='order_change',  # 'duplicate', 'fraudulent', 'order_change', 'product_unsatisfactory'
    )
    return credit_note
```

### Customer Balance (Credito Prepagato)

Stripe supporta un balance sul Customer — utile per crediti, rimborsi futuri, o prepagato:

```python
# Aggiungere credito al customer balance
stripe.Customer.create_balance_transaction(
    'cus_xxx',
    amount=-5000,  # Negativo = credito (€50 di credito)
    currency='eur',
    description='Credito per disservizio',
)
# Il credito verrà applicato automaticamente alla prossima fattura
```

---

## Multi-Currency — Pagamenti Internazionali

### Strategia Multi-Currency

Un SaaS internazionale deve decidere tra due approcci:

**Approccio 1 — Prezzi distinti per valuta**: creare un Price separato per ogni valuta supportata. Questo permette di ottimizzare i prezzi per ciascun mercato (es. $15 USD non è necessariamente uguale a €15 EUR).

```python
# Creare prezzi per diverse valute
currencies = {
    'eur': 1500,   # €15.00
    'usd': 1700,   # $17.00
    'gbp': 1300,   # £13.00
    'jpy': 2000,   # ¥2,000
}

for currency, amount in currencies.items():
    stripe.Price.create(
        product=pro_product.id,
        unit_amount=amount,
        currency=currency,
        recurring={'interval': 'month'},
        metadata={'billing_period': 'monthly'},
        lookup_key=f'pro_monthly_{currency}',
        transfer_lookup_key=True,
    )
```

**Approccio 2 — Presentment currency con Adaptive Pricing**: Stripe può mostrare automaticamente i prezzi nella valuta locale dell'utente usando un singolo prezzo base. Stripe gestisce la conversione:

```python
session = stripe.checkout.Session.create(
    customer=customer_id,
    mode='subscription',
    line_items=[{'price': 'price_base_eur', 'quantity': 1}],
    currency='auto',  # Stripe sceglie la valuta basandosi sull'IP del cliente
    success_url=f'{BASE_URL}/success',
    cancel_url=f'{BASE_URL}/cancel',
)
```

### Selezionare la Valuta Lato Server

```python
def get_price_for_user(user, plan: str, period: str) -> str:
    """Restituisce il Price ID appropriato per la valuta dell'utente"""
    currency = detect_user_currency(user)  # Basato su IP, profilo, o preferenza

    lookup_key = f'{plan}_{period}_{currency}'
    prices = stripe.Price.list(lookup_keys=[lookup_key])

    if prices.data:
        return prices.data[0].id

    # Fallback alla valuta base
    fallback_key = f'{plan}_{period}_eur'
    return stripe.Price.list(lookup_keys=[fallback_key]).data[0].id
```

### Considerazioni Multi-Currency

- Le fatture Stripe sono sempre in una singola valuta — non si possono mixare valute in una fattura.
- I payout al proprio conto bancario sono nella valuta del conto. Stripe converte automaticamente.
- Le commissioni Stripe includono un sovrapprezzo di ~1% per conversione di valuta.
- Per valute zero-decimal (JPY, KRW), `unit_amount` è in unità intere (non centesimi).

---

## Stripe Tax — Automazione Fiscale

### Perché Stripe Tax

La gestione delle tasse per un SaaS internazionale è complessa: IVA in Europa, Sales Tax negli USA (varia per stato e contea), GST in Australia e India, Consumption Tax in Giappone. Stripe Tax automatizza il calcolo, la raccolta e il reporting fiscale.

### Configurazione Iniziale

Nella Dashboard Stripe (Settings → Tax):
1. **Registrare la propria sede fiscale** (head office location)
2. **Aggiungere le registrazioni fiscali** per ogni giurisdizione dove si ha obbligo di riscossione
3. **Scegliere il product tax code** per ciascun prodotto (software-as-a-service ha codici specifici)

```python
# Creare un prodotto con tax code
product = stripe.Product.create(
    name='Piano Pro',
    tax_code='txcd_10103001',  # SaaS - business use
    # Tax codes comuni per SaaS:
    # txcd_10103001 - Software as a service, business use
    # txcd_10103000 - Software as a service, personal use
    # txcd_10201000 - Infrastructure as a service
)
```

### Abilitare Tax su Checkout

```python
session = stripe.checkout.Session.create(
    customer=customer_id,
    mode='subscription',
    line_items=[{
        'price': price_id,
        'quantity': 1,
    }],
    automatic_tax={'enabled': True},
    customer_update={
        'address': 'auto',  # Stripe raccoglie l'indirizzo per calcolo tasse
    },
    tax_id_collection={'enabled': True},  # Raccoglie Partita IVA / VAT ID
    success_url=f'{BASE_URL}/success',
    cancel_url=f'{BASE_URL}/cancel',
)
```

### Tax su Subscription Dirette

```python
# Abilitare Tax su una subscription creata via API
subscription = stripe.Subscription.create(
    customer=customer_id,
    items=[{'price': price_id}],
    automatic_tax={'enabled': True},
)
```

### Tax Reporting e Nexus

Stripe Tax genera report fiscali scaricabili dalla Dashboard: IVA/VAT return data, US state sales tax filing, e riepiloghi per giurisdizione. Stripe monitora anche il nexus — la soglia di vendite che obbliga alla riscossione delle tasse in una nuova giurisdizione — e notifica quando si raggiunge.

### Reverse Charge per B2B

Per vendite B2B intra-UE, Stripe Tax gestisce automaticamente il reverse charge quando il cliente fornisce un VAT ID valido. La fattura riporta "Reverse Charge" e l'IVA non viene addebitata.

---

## Stripe Connect — Marketplace e Piattaforme

### Cos'è Connect

Stripe Connect è la soluzione per piattaforme e marketplace che devono gestire pagamenti tra tre parti: l'acquirente, il venditore (connected account), e la piattaforma che trattiene una commissione.

### Tipi di Account Connect

| Tipo | Controllo piattaforma | Onboarding | Caso d'uso |
|------|----------------------|------------|------------|
| **Standard** | Minimo | Gestito da Stripe | Marketplace (Etsy-like) |
| **Express** | Medio | Dashboard Stripe semplificata | Economia gig, delivery |
| **Custom** | Totale | UI propria della piattaforma | White-label, embedded finance |

### Flusso Tipico di un Marketplace

```python
# 1. Onboarding di un venditore (Express account)
def onboard_seller(seller_user_id: int):
    account = stripe.Account.create(
        type='express',
        country='IT',
        email=get_user_email(seller_user_id),
        capabilities={
            'card_payments': {'requested': True},
            'transfers': {'requested': True},
        },
        metadata={'seller_user_id': str(seller_user_id)},
    )

    # Creare il link di onboarding
    account_link = stripe.AccountLink.create(
        account=account.id,
        refresh_url=f'{BASE_URL}/sellers/onboarding/refresh',
        return_url=f'{BASE_URL}/sellers/onboarding/complete',
        type='account_onboarding',
    )

    save_seller_account(seller_user_id, account.id)
    return account_link.url  # Redirect il venditore qui


# 2. Creare un pagamento con split (destination charge)
def create_marketplace_payment(buyer_customer_id: str,
                                seller_account_id: str,
                                amount: int,
                                platform_fee: int):
    """Pagamento con split: il buyer paga, il seller riceve, la piattaforma trattiene"""
    payment_intent = stripe.PaymentIntent.create(
        amount=amount,                    # Importo totale
        currency='eur',
        customer=buyer_customer_id,
        application_fee_amount=platform_fee,  # Commissione piattaforma
        transfer_data={
            'destination': seller_account_id,  # Il seller riceve (amount - fee)
        },
        metadata={
            'order_id': '12345',
            'seller_id': seller_account_id,
        },
    )
    return payment_intent


# 3. Transfer manuale (alternativa più flessibile)
def transfer_to_seller(seller_account_id: str, amount: int, order_id: str):
    transfer = stripe.Transfer.create(
        amount=amount,
        currency='eur',
        destination=seller_account_id,
        metadata={'order_id': order_id},
    )
    return transfer
```

### Webhook per Connect

Connect aggiunge eventi specifici con il prefisso `account.`:

```python
CONNECT_WEBHOOK_HANDLERS = {
    'account.updated': handle_account_updated,           # KYC completato / status change
    'account.application.deauthorized': handle_deauth,   # Venditore disconnesso
    'payout.paid': handle_payout_paid,                   # Payout al venditore completato
    'payout.failed': handle_payout_failed,               # Payout fallito
}
```

---

## Revenue Recognition

### Il Problema della Revenue Recognition

Per SaaS con contabilità basata su principi contabili (GAAP/IFRS), i ricavi da subscription non si riconoscono al momento del pagamento ma si distribuiscono lungo il periodo di servizio. Ad esempio, un pagamento annuale di €1.200 ricevuto a gennaio si riconosce come €100/mese per 12 mesi.

### Stripe Revenue Recognition

Stripe Revenue Recognition automatizza questo processo:
- **Deferred Revenue Tracking**: traccia automaticamente i ricavi differiti per ogni subscription
- **Waterfall Reports**: genera i report di riconoscimento ricavi con la cascata temporale
- **Journal Entries**: esporta le scritture contabili per l'integrazione con il software contabile

### Configurazione

Revenue Recognition si abilita dalla Dashboard (Revenue Recognition → Settings). I report vengono generati automaticamente ogni mese e includono:
- Balance sheet impact (deferred revenue, recognized revenue)
- Revenue waterfall per mese di riconoscimento
- Dettaglio per prodotto/prezzo
- Export CSV/Excel per il team finance

### Regole Personalizzate

```python
# Le regole di revenue recognition si configurano nella Dashboard
# ma è utile associare metadata ai prodotti per il mapping contabile:
stripe.Product.create(
    name='Piano Pro - Annuale',
    metadata={
        'revenue_category': 'subscription_saas',
        'recognition_period': '12_months',
        'gl_account': '4100',  # Conto contabile
    },
)
```

---

## PCI Compliance con Stripe

### Livelli di PCI Compliance

Il Payment Card Industry Data Security Standard (PCI DSS) definisce i requisiti di sicurezza per chi gestisce dati di carte di credito. Con Stripe, il livello di compliance richiesto dipende dall'approccio di integrazione scelto:

| Approccio | SAQ Richiesto | Complessità Compliance |
|-----------|---------------|----------------------|
| Checkout Session, Payment Links | **SAQ A** | Minima — questionario ~22 domande |
| Elements (Payment Element, Card Element) | **SAQ A-EP** | Media — questionario ~139 domande |
| Direct API (raw card data) | **SAQ D** | Massima — 300+ requisiti, audit annuale |

### SAQ A — Il Percorso Raccomandato

Con Stripe Checkout o Payment Links, i dati della carta non toccano MAI i propri server. Tutto il processing avviene su domini Stripe. Questo riduce la compliance a SAQ A, il livello più semplice:

- Nessun dato di carta transita dal proprio server
- Nessun log contenente PAN (Primary Account Number)
- Nessun requisito di cifratura dei dati di carta a riposo
- Questionario annuale di autovalutazione (~22 domande)

### SAQ A-EP — Con Elements

Con Stripe Elements, i dati della carta vengono inseriti in iframe ospitati da Stripe ma serviti dalla propria pagina. Questo richiede SAQ A-EP:

- Il proprio server serve la pagina ma NON processa i dati della carta
- Serve HTTPS/TLS obbligatorio su tutta l'applicazione
- CSP (Content Security Policy) deve permettere `js.stripe.com` e `api.stripe.com`
- Vulnerability scanning trimestrale (ASV scan) è raccomandato

### Checklist di Sicurezza PCI per Sviluppatori

```
[ ] Mai loggare numeri di carta, CVC, date di scadenza
[ ] Mai salvare dati di carta nel proprio database
[ ] HTTPS obbligatorio su tutto il sito (non solo checkout)
[ ] Secret key mai esposta nel frontend
[ ] Webhook endpoint con verifica firma
[ ] CSP configurato per Stripe.js
[ ] Stripe.js caricato sempre da js.stripe.com (non self-hosted)
[ ] Test regolari con stripe.js integrity check
```

---

## Testing con Stripe CLI

### Setup della Stripe CLI

```bash
# Installazione
# macOS
brew install stripe/stripe-cli/stripe

# Linux
curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg
echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.dev/stripe-cli-debian-local stable main" | sudo tee -a /etc/apt/sources.list.d/stripe.list
sudo apt update && sudo apt install stripe

# Login
stripe login

# Ascoltare i webhook in locale
stripe listen --forward-to localhost:8000/webhooks/stripe
# Output: Ready! Your webhook signing secret is whsec_xxxxx
```

### Testare Scenari Specifici

```bash
# Triggerare un evento specifico
stripe trigger checkout.session.completed
stripe trigger invoice.payment_failed
stripe trigger customer.subscription.deleted

# Creare un pagamento di test
stripe payments create --amount 1500 --currency eur

# Visualizzare i log
stripe logs tail

# Testare con carte specifiche
# 4242424242424242 - Pagamento riuscito
# 4000000000000002 - Carta rifiutata
# 4000002500003155 - Richiede autenticazione 3D Secure
# 4000000000009995 - Fondi insufficienti
```

### Carte di Test Avanzate

| Numero Carta | Scenario |
|-------------|----------|
| `4242424242424242` | Pagamento riuscito |
| `4000000000000002` | Carta rifiutata generica |
| `4000000000009995` | Fondi insufficienti |
| `4000002500003155` | 3D Secure richiesto |
| `4000000000000341` | Attach riesce, pagamento fallisce |
| `4000000000003220` | 3D Secure 2 — authentication flow completo |
| `4000000000000077` | Charge riesce, dispute viene creata |
| `4000003720000278` | Carta India — richiede mandate |
| `pm_card_visa_debit` | Visa debit |
| `pm_card_mastercard` | Mastercard |
| `4000000000000101` | CVC check fallisce |
| `4100000000000019` | Carta bloccata per frode |

### Test Automatizzati

```python
# Test con mock di Stripe (usando pytest e unittest.mock)
import pytest
from unittest.mock import patch, MagicMock

class TestStripeIntegration:

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_create):
        mock_create.return_value = MagicMock(
            id='cs_test_123',
            url='https://checkout.stripe.com/test'
        )

        response = client.post('/api/create-checkout-session',
            json={'price_id': 'price_test_123'}
        )

        assert response.status_code == 200
        assert 'url' in response.json

    def test_webhook_signature_verification(self):
        """Verificare che webhook senza firma valida vengano rifiutati"""
        response = client.post('/webhooks/stripe',
            data='{"type": "fake"}',
            headers={'Stripe-Signature': 'invalid'}
        )
        assert response.status_code == 400

    @patch('stripe.Webhook.construct_event')
    def test_webhook_idempotency(self, mock_construct):
        """Verificare che eventi duplicati non vengano processati due volte"""
        mock_event = MagicMock()
        mock_event.id = 'evt_test_123'
        mock_event.type = 'invoice.paid'
        mock_construct.return_value = mock_event

        # Prima chiamata - dovrebbe essere processata
        response1 = client.post('/webhooks/stripe', ...)
        assert response1.status_code == 200

        # Seconda chiamata con lo stesso evento - dovrebbe essere ignorata
        response2 = client.post('/webhooks/stripe', ...)
        assert response2.status_code == 200
        assert response2.json['status'] == 'already_processed'
```

---

## Test Clocks — Simulazione Temporale delle Subscription

### Cos'è un Test Clock

I Test Clock sono una funzionalità esclusiva dell'ambiente di test che permette di simulare il passaggio del tempo. Questo è fondamentale per testare scenari che nel mondo reale richiederebbero settimane o mesi:

- Fine del trial period
- Rinnovo della subscription
- Scadenza della carta
- Sequenza di dunning (pagamento fallito → retry → cancellazione)
- Proration dopo cambio piano a metà ciclo

### Creare e Utilizzare un Test Clock

```python
# Creare un Test Clock
test_clock = stripe.test_helpers.TestClock.create(
    frozen_time=int(datetime(2025, 1, 1).timestamp()),
    name='Test ciclo subscription annuale',
)

# Creare un customer associato al Test Clock
customer = stripe.Customer.create(
    email='test-clock@example.com',
    test_clock=test_clock.id,
)

# Creare una subscription con trial di 14 giorni
subscription = stripe.Subscription.create(
    customer=customer.id,
    items=[{'price': 'price_xxx'}],
    trial_period_days=14,
)

# subscription.status == 'trialing'
# subscription.trial_end == 2025-01-15

# Avanzare il tempo di 14 giorni → il trial finisce
stripe.test_helpers.TestClock.advance(
    test_clock.id,
    frozen_time=int(datetime(2025, 1, 15).timestamp()),
)
# Attendere che Stripe processi — verificare subscription.status == 'active'

# Avanzare di 1 mese → primo rinnovo
stripe.test_helpers.TestClock.advance(
    test_clock.id,
    frozen_time=int(datetime(2025, 2, 1).timestamp()),
)

# Avanzare di 1 anno → verificare rinnovo annuale e dunning
stripe.test_helpers.TestClock.advance(
    test_clock.id,
    frozen_time=int(datetime(2026, 1, 1).timestamp()),
)
```

### Testare il Dunning con Test Clock

```python
def test_dunning_sequence():
    """Testare l'intera sequenza di pagamento fallito → retry → cancellazione"""
    clock = stripe.test_helpers.TestClock.create(
        frozen_time=int(datetime(2025, 1, 1).timestamp()),
    )

    customer = stripe.Customer.create(
        email='dunning-test@example.com',
        test_clock=clock.id,
    )

    # Attaccare una carta che fallirà
    stripe.PaymentMethod.attach('pm_card_chargeDeclined', customer=customer.id)
    stripe.Customer.modify(customer.id,
        invoice_settings={'default_payment_method': 'pm_card_chargeDeclined'})

    # Creare subscription
    sub = stripe.Subscription.create(
        customer=customer.id,
        items=[{'price': 'price_xxx'}],
    )

    # Avanzare al rinnovo — il pagamento fallisce
    stripe.test_helpers.TestClock.advance(
        clock.id,
        frozen_time=int(datetime(2025, 2, 1).timestamp()),
    )
    # Verificare: sub.status == 'past_due'

    # Avanzare oltre tutti i retry → subscription cancellata
    stripe.test_helpers.TestClock.advance(
        clock.id,
        frozen_time=int(datetime(2025, 2, 15).timestamp()),
    )
    # Verificare: sub.status == 'canceled' (se configurato così)
```

### Limitazioni dei Test Clock

- Funzionano solo in test mode
- Massimo 3 test clock attivi contemporaneamente
- Le risorse associate a un test clock non interagiscono con risorse normali
- L'avanzamento è asincrono — verificare lo stato dopo ogni advance

---

## Gestione degli Errori e Retry Logic

### Errori Comuni di Stripe

```python
def handle_stripe_error(func):
    """Decorator per gestire gli errori Stripe in modo uniforme"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except stripe.error.CardError as e:
            # Errore della carta (fondi insufficienti, carta scaduta, etc.)
            return {'error': e.user_message, 'code': e.code}, 402
        except stripe.error.RateLimitError:
            # Rate limit raggiunto - retry con exponential backoff
            return {'error': 'Too many requests, please retry'}, 429
        except stripe.error.InvalidRequestError as e:
            # Parametri invalidi - bug nel codice
            logger.error(f"Stripe InvalidRequestError: {e}")
            return {'error': 'Invalid request'}, 400
        except stripe.error.AuthenticationError:
            # API key non valida
            logger.critical("Stripe authentication failed!")
            return {'error': 'Payment service unavailable'}, 503
        except stripe.error.APIConnectionError:
            # Problema di rete
            return {'error': 'Payment service temporarily unavailable'}, 503
        except stripe.error.StripeError as e:
            # Errore generico di Stripe
            logger.error(f"Stripe error: {e}")
            return {'error': 'Payment processing error'}, 500
    return wrapper
```

### Codici di Errore Carta Comuni

| Codice | Significato | Azione Consigliata |
|--------|-------------|-------------------|
| `card_declined` | Carta rifiutata generica | Chiedere un altro metodo di pagamento |
| `insufficient_funds` | Fondi insufficienti | Suggerire di riprovare o usare altra carta |
| `expired_card` | Carta scaduta | Aggiornare i dati della carta |
| `incorrect_cvc` | CVC errato | Far reinserire i dati |
| `processing_error` | Errore del processore | Riprovare dopo qualche minuto |
| `authentication_required` | 3D Secure richiesto | Reindirizzare a 3DS flow |
| `do_not_honor` | Banca rifiuta senza motivo | Contattare la propria banca |

### Dunning Management (Gestione Pagamenti Falliti)

Quando un pagamento ricorrente fallisce, Stripe implementa automaticamente una logica di retry (configurabile nella Dashboard). Il processo tipico è:

1. **Primo tentativo fallito**: Stripe riprova dopo 1 giorno
2. **Secondo tentativo fallito**: Stripe riprova dopo 3 giorni
3. **Terzo tentativo fallito**: Stripe riprova dopo 5 giorni
4. **Tutti i tentativi falliti**: la subscription viene marcata come `past_due` o `canceled` (configurabile)

Il proprio sistema deve gestire ogni fase:

```python
def handle_payment_failed(event):
    invoice = event.data.object
    attempt_count = invoice.attempt_count

    customer = get_billing_customer_by_stripe_id(invoice.customer)
    user = get_user(customer.user_id)

    if attempt_count == 1:
        # Primo fallimento: notifica gentile
        send_email(user, 'payment_failed_first',
                   next_retry_date=calculate_next_retry())
    elif attempt_count == 2:
        # Secondo fallimento: notifica più urgente
        send_email(user, 'payment_failed_second')
        # Mostrare un banner in-app
        set_user_flag(user, 'payment_issue', True)
    elif attempt_count == 3:
        # Terzo fallimento: ultima notifica
        send_email(user, 'payment_failed_final')
        # Limitare le funzionalità (grace period)
        downgrade_to_limited_access(user)
    else:
        # Tutti i tentativi falliti: subscription cancellata
        send_email(user, 'subscription_canceled')
        revoke_all_paid_features(user)
```

### Endpoint di Riconciliazione

Un endpoint di riconciliazione permette di verificare e correggere discrepanze tra il database locale e Stripe. Da eseguire periodicamente (es. cron giornaliero):

```python
def reconcile_subscriptions():
    """Sincronizza lo stato locale con Stripe — cron giornaliero"""
    local_subs = BillingSubscription.query.filter(
        BillingSubscription.status.in_(['active', 'trialing', 'past_due'])
    ).all()

    discrepancies = []
    for local_sub in local_subs:
        try:
            stripe_sub = stripe.Subscription.retrieve(
                local_sub.stripe_subscription_id
            )
        except stripe.error.InvalidRequestError:
            # Subscription non esiste su Stripe — dati orfani
            discrepancies.append({
                'type': 'orphan',
                'local_id': local_sub.id,
                'stripe_id': local_sub.stripe_subscription_id,
            })
            continue

        if local_sub.status != stripe_sub.status:
            discrepancies.append({
                'type': 'status_mismatch',
                'local_status': local_sub.status,
                'stripe_status': stripe_sub.status,
                'sub_id': local_sub.stripe_subscription_id,
            })
            # Auto-fix
            local_sub.status = stripe_sub.status
            db.session.commit()

    if discrepancies:
        logger.warning(f"Riconciliazione: {len(discrepancies)} discrepanze trovate")
        notify_ops_team(discrepancies)

    return discrepancies
```

---

## Migrazione da Altri Payment Processor

### Da Chargebee/Recurly a Stripe

La migrazione dei dati di pagamento richiede pianificazione attenta:

1. **Esportare i dati dal vecchio provider**: clienti, subscription, metodi di pagamento (solo se il provider supporta token portability)
2. **Creare i customer su Stripe**: importare i dati dei clienti preservando gli ID di mapping
3. **Migrare le carte**: se il vecchio provider supporta PAN forwarding (raramente disponibile), le carte possono essere migrate direttamente. Altrimenti, chiedere ai clienti di reinserire il metodo di pagamento.
4. **Creare le subscription su Stripe**: ricreare le subscription con lo stesso billing cycle e prezzo
5. **Cutover**: switchare il billing al nuovo sistema per i nuovi rinnovi

### Strategia Dettagliata di Migrazione

La migrazione va eseguita in fasi per minimizzare il rischio:

**Fase 1 — Setup parallelo (2-4 settimane)**
```python
# Creare i prodotti e prezzi equivalenti su Stripe
# Mapping tra i vecchi ID e i nuovi ID Stripe
PLAN_MAPPING = {
    'old_pro_monthly': 'price_new_pro_monthly',
    'old_pro_annual': 'price_new_pro_annual',
    'old_enterprise_monthly': 'price_new_enterprise_monthly',
}
```

**Fase 2 — Migrazione dei customer (1-2 settimane)**
```python
def migrate_customers_batch(old_customers: list):
    """Migrare un batch di customer dal vecchio sistema a Stripe"""
    results = {'success': 0, 'failed': 0, 'errors': []}

    for old_cust in old_customers:
        try:
            stripe_customer = stripe.Customer.create(
                email=old_cust['email'],
                name=old_cust['name'],
                metadata={
                    'old_customer_id': old_cust['id'],
                    'migrated_from': 'chargebee',
                    'migration_date': datetime.utcnow().isoformat(),
                },
                address=old_cust.get('address'),
            )

            # Aggiornare il mapping nel proprio database
            update_customer_mapping(old_cust['id'], stripe_customer.id)
            results['success'] += 1

        except stripe.error.StripeError as e:
            results['failed'] += 1
            results['errors'].append({'customer': old_cust['id'], 'error': str(e)})

    return results
```

**Fase 3 — Raccolta nuovi metodi di pagamento**
```python
# Inviare un'email a ogni cliente con un link per aggiornare il metodo di pagamento
def send_card_update_request(user_id: int):
    customer = get_billing_customer(user_id)

    # Creare un SetupIntent per raccogliere il nuovo metodo di pagamento
    setup_intent = stripe.SetupIntent.create(
        customer=customer.stripe_customer_id,
        usage='off_session',  # Per pagamenti ricorrenti futuri
    )

    # Oppure usare il Customer Portal
    portal_session = stripe.billing_portal.Session.create(
        customer=customer.stripe_customer_id,
        return_url=f'{BASE_URL}/settings/billing',
        flow_data={'type': 'payment_method_update'},
    )

    send_email(user_id, 'update_payment_method', url=portal_session.url)
```

**Fase 4 — Cutover graduale**
- Migrare prima i clienti con rinnovo più lontano
- Mantenere il vecchio sistema attivo per i clienti non ancora migrati
- Monitorare attivamente errori e discrepanze
- Avere un piano di rollback per ogni batch

---

## Best Practices

1. **Webhook-first architecture**: progettare il sistema con i webhook come fonte primaria di verità per gli eventi di pagamento. Non fare affidamento sui redirect o sulle risposte API sincrone.
2. **Idempotency per tutti i webhook**: verificare che ogni evento venga processato una sola volta, anche in caso di delivery duplicata.
3. **Mantenere dati locali sincronizzati**: salvare una copia locale dei dati Stripe critici (subscription status, period dates, invoices) per evitare chiamate API per ogni page load.
4. **Pin della versione API**: specificare sempre `stripe.api_version` per evitare breaking changes.
5. **Testare con la Stripe CLI**: utilizzare `stripe listen` e `stripe trigger` per testare tutti gli scenari di webhook localmente.
6. **Gestire il dunning proattivamente**: implementare email e notifiche in-app per pagamenti falliti prima che la subscription venga cancellata.
7. **Non esporre mai la Secret Key**: la secret key deve essere solo server-side, mai nel frontend, mai in repository pubblici.
8. **Utilizzare il Customer Portal**: delegare a Stripe la gestione self-service del billing per ridurre il carico di supporto.
9. **Usare Idempotency Key per creazioni**: includere idempotency key in tutte le chiamate POST per prevenire duplicati causati da retry di rete.
10. **Riconciliazione periodica**: implementare un job giornaliero che verifica la coerenza tra il database locale e lo stato su Stripe, segnalando discrepanze.
11. **Metadata disciplinate**: usare i `metadata` in modo consistente su Customer, Subscription e Invoice per il mapping con il proprio sistema (`user_id`, `plan`, `source`).
12. **Logging strutturato per il billing**: ogni operazione di billing deve loggare event_id, customer_id, subscription_id, amount, currency, risultato. Questi log sono essenziali per debug e audit.
13. **Separare webhook endpoint dal body parsing**: in Express/Node.js, il webhook route deve ricevere il raw body, non il JSON parsato. Configurare il body-parser per escludere il path del webhook.
14. **Test Clocks per ogni scenario di ciclo di vita**: non limitarsi a testare la creazione; testare trial end, rinnovo, fallimento, dunning, cancellazione, riattivazione con test clocks.

---

## Troubleshooting

### Problema: Webhook Non Ricevuti

**Diagnosi**: verificare nella Dashboard Stripe (Developers → Webhooks) lo stato delle delivery. Errori comuni: URL non raggiungibile, certificato SSL non valido, server che risponde con errori.

**Soluzione**: verificare che l'endpoint sia pubblicamente raggiungibile, che risponda con 200 entro 20 secondi, che il WEBHOOK_SECRET sia corretto. Utilizzare `stripe listen` per debug locale.

### Problema: Subscription Attiva ma Utente Non Ha Accesso

**Diagnosi**: il webhook `checkout.session.completed` potrebbe non essere stato processato, o il mapping tra Stripe customer e utente locale potrebbe essere errato.

**Soluzione**: verificare l'EventLog per confermare che l'evento è stato ricevuto e processato. Verificare i metadata della subscription per il `user_id`. Implementare un endpoint di riconciliazione che sincronizza lo stato da Stripe.

### Problema: Pagamento Duplicato

**Diagnosi**: l'utente ha cliccato più volte sul pulsante di pagamento, creando multiple Checkout Sessions.

**Soluzione**: disabilitare il pulsante dopo il primo click. Utilizzare `client_reference_id` nella Checkout Session per identificare e prevenire duplicati. Verificare che il webhook handler sia idempotente.

### Problema: Proration Errata dopo Upgrade

**Diagnosi**: il calcolo del proration non corrisponde alle aspettative. Stripe calcola il proration basandosi sul costo giornaliero proporzionale.

**Soluzione**: utilizzare `upcoming_invoice` per mostrare al cliente il costo del proration prima di confermare il cambio piano. Considerare `proration_behavior='none'` per applicare il cambio solo al prossimo ciclo.

### Problema: Webhook Signature Verification Fallisce

**Diagnosi**: l'errore `SignatureVerificationError` indica che il payload è stato alterato tra l'invio da Stripe e la ricezione dal proprio server.

**Soluzione**: assicurarsi che il body del webhook venga letto come raw bytes prima del parsing JSON. In Express/Node.js, usare `express.raw()` per il webhook route. In Flask/Django, usare `request.get_data()` non `request.json`. Proxy, WAF, o CDN che modificano il body causano lo stesso errore.

### Problema: Customer Creato Duplicato su Stripe

**Diagnosi**: ogni volta che un utente tenta di pagare, viene creato un nuovo Customer Stripe invece di riutilizzare quello esistente.

**Soluzione**: implementare sempre `get_or_create_stripe_customer()` che verifica prima l'esistenza nel database locale. Aggiungere un vincolo UNIQUE su `stripe_customer_id` nel database. Se i duplicati esistono già, usare `stripe.Customer.list(email=...)` per trovare e consolidare i duplicati.

### Problema: Invoice Non Pagata — Subscription Bloccata

**Diagnosi**: la subscription è in stato `past_due` o `incomplete` perché l'invoice iniziale o di rinnovo non è stata pagata.

**Soluzione**: per `incomplete`, il pagamento iniziale è fallito — l'utente deve completare il pagamento. Creare un nuovo PaymentIntent o reindirizzare al Customer Portal. Per `past_due`, configurare il dunning nella Dashboard (Settings → Billing → Subscriptions → Retry schedule).

### Problema: Webhook Handler Lento — Timeout 20s

**Diagnosi**: il webhook handler esegue operazioni pesanti (chiamate a servizi esterni, invio email, aggiornamento di più tabelle) e supera il timeout di 20 secondi di Stripe.

**Soluzione**: rispondere 200 immediatamente e processare l'evento in modo asincrono con una coda (Celery, Bull, SQS). Il webhook handler deve solo: verificare la firma, controllare l'idempotency, enqueue il job, restituire 200.

### Problema: Metodo di Pagamento Non Funzionante per Rinnovi

**Diagnosi**: la carta salvata funzionava al primo pagamento ma fallisce ai rinnovi (carta scaduta, fondi insufficienti, carte prepagate esaurite).

**Soluzione**: usare l'evento `customer.subscription.trial_will_end` per verificare il metodo di pagamento 3 giorni prima. Implementare l'aggiornamento automatico della carta con `payment_method_update` nel Customer Portal. Stripe Card Account Updater aggiorna automaticamente le carte rinnovate dalla banca.

### Problema: Importi Errati nelle Fatture

**Diagnosi**: gli importi nelle fatture non corrispondono ai prezzi configurati, specialmente dopo upgrade/downgrade.

**Soluzione**: verificare la `proration_behavior` usata nel cambio piano. Usare `stripe.Invoice.upcoming()` per simulare la prossima fattura e verificare gli importi prima di confermare. Controllare che non ci siano `InvoiceItem` pendenti non associati (creati e mai fatturati).

### Problema: 3D Secure Bloccante — Pagamento Richiede Autenticazione

**Diagnosi**: il pagamento richiede 3D Secure (SCA) ma l'utente non completa l'autenticazione, lasciando il PaymentIntent in stato `requires_action`.

**Soluzione**: per pagamenti on-session, reindirizzare l'utente al flusso 3DS tramite `stripe.confirmPayment()` o il `hosted_invoice_url`. Per pagamenti off-session (rinnovi), richiedere il consenso esplicito al momento del setup con `setup_future_usage: 'off_session'` e usare `payment_behavior: 'default_incomplete'` per gestire i casi che richiedono azione.

### Problema: Tax ID / Partita IVA Non Validata

**Diagnosi**: il cliente inserisce un VAT ID nella Checkout ma il reverse charge non viene applicato.

**Soluzione**: Stripe valida i VAT ID in modo asincrono tramite il database VIES. Lo stato della validazione si verifica nel webhook `customer.tax_id.updated`. Se il VAT ID non è valido, notificare il cliente e chiedere di reinserirlo. La validazione può richiedere fino a qualche minuto.

### Problema: Payout Non Ricevuti (Connect)

**Diagnosi**: un connected account (venditore) non riceve i fondi.

**Soluzione**: verificare lo stato dell'account con `stripe.Account.retrieve(acct_id)`. L'onboarding potrebbe essere incompleto (`requirements.currently_due` non vuoto). Il payout schedule potrebbe avere un delay. Verificare gli eventi `payout.failed` per errori bancari. Assicurarsi che il conto bancario del venditore sia correttamente configurato.

### Problema: Rate Limit Raggiunto (429)

**Diagnosi**: il backend effettua troppe chiamate API in poco tempo, ricevendo `429 Too Many Requests`.

**Soluzione**: implementare caching locale per dati letti frequentemente (subscription status, customer data). Usare `expand` per ridurre le round-trip. Consolidare le operazioni batch. Gli SDK Stripe implementano retry automatico, ma il proprio codice deve ridurre il volume di chiamate a monte.

### Problema: Ambiente di Test con Dati Inconsistenti

**Diagnosi**: i dati di test sono diventati incoerenti dopo molti test, con customer orfani, subscription fantasma, e prezzi archiviati.

**Soluzione**: non usare mai l'ambiente di test condiviso tra sviluppatori per test automatizzati. Creare customer dedicati per i test con prefisso riconoscibile. Usare i Test Clock per scenari temporali. Periodicamente, pulire i dati di test dalla Dashboard (Developers → Test Data → Delete all test data).

### Problema: Migrazione — Duplicazione delle Fatture durante il Cutover

**Diagnosi**: durante la migrazione dal vecchio provider, alcuni clienti vengono fatturati da entrambi i sistemi.

**Soluzione**: creare le subscription su Stripe con `billing_cycle_anchor` impostato alla data di fine del ciclo corrente sul vecchio provider, e `proration_behavior='none'`. Disabilitare il rinnovo automatico sul vecchio provider prima di attivare quello su Stripe. Mantenere un log di cutover per ogni cliente.

---

## FAQ — Domande Frequenti

### 1. Qual è la differenza tra PaymentIntent e SetupIntent?

**PaymentIntent** si usa per raccogliere un pagamento immediato. **SetupIntent** si usa per salvare un metodo di pagamento per usi futuri senza addebitare immediatamente. Per le subscription, se si usa Checkout Session il flusso è automatico; con Elements, si usa SetupIntent per raccogliere la carta e poi si crea la subscription server-side.

### 2. Devo usare Checkout Session o Elements per il mio SaaS?

Per la maggior parte dei SaaS in fase iniziale, Checkout Session è la scelta migliore: meno codice, PCI compliance semplificata (SAQ A), supporto automatico per tutti i metodi di pagamento, ottimizzazione mobile inclusa. Migrare a Elements ha senso quando il brand richiede un'esperienza di pagamento totalmente integrata nella propria UI (tipicamente dopo il product-market fit).

### 3. Come gestisco i prezzi diversi per paese?

Due approcci: (a) creare Price separati per ogni valuta e selezionare quello giusto in base alla geolocalizzazione dell'utente, (b) usare un prezzo base e lasciare che Stripe converta con Adaptive Pricing. L'approccio (a) è preferibile perché permette di ottimizzare i prezzi per mercato (purchasing power parity).

### 4. Posso cambiare il prezzo per i clienti esistenti?

Sì. Ci sono due strategie: (a) "grandfather" — i clienti esistenti mantengono il vecchio prezzo, i nuovi clienti ottengono il nuovo prezzo (si archiviano i vecchi Price ma restano attivi sulle subscription esistenti), (b) migrazione — si aggiornano le subscription esistenti al nuovo Price, con o senza proration. Stripe non cambia automaticamente il prezzo ai clienti esistenti quando si modifica un Price; bisogna aggiornare esplicitamente ogni subscription.

### 5. Come funzionano i coupon e le promozioni?

Creare un `Coupon` (es. 20% off per 3 mesi) e poi un `Promotion Code` (il codice che l'utente inserisce). Abilitare `allow_promotion_codes=True` nella Checkout Session. I coupon possono essere percentuali o importi fissi, con durata limitata (N mesi) o permanente.

### 6. Come gestisco i rimborsi?

`stripe.Refund.create(payment_intent='pi_xxx')` per un rimborso completo, oppure `stripe.Refund.create(payment_intent='pi_xxx', amount=500)` per un rimborso parziale (€5.00). Per subscription, è più appropriato usare Credit Notes o balance adjustment sul Customer piuttosto che un refund diretto.

### 7. Devo gestire la Strong Customer Authentication (SCA/3D Secure)?

In Europa (PSD2), SCA è obbligatoria per la maggior parte dei pagamenti. Stripe gestisce 3D Secure automaticamente con il `Payment Element` e `Checkout Session`. Per pagamenti off-session (rinnovi), Stripe richiede l'esenzione SCA dove possibile. Non è necessario implementare manualmente il flusso 3DS — Stripe se ne occupa.

### 8. Come testo i webhook in locale senza esporre il mio server?

Usare `stripe listen --forward-to localhost:8000/webhooks/stripe`. La Stripe CLI crea un tunnel temporaneo e inoltra gli eventi al server locale. Il webhook secret fornito dalla CLI (`whsec_...`) è diverso da quello di produzione — usare variabili d'ambiente.

### 9. Quanti webhook endpoint devo configurare?

Uno è sufficiente per la maggior parte dei SaaS. L'endpoint riceve tutti gli eventi e li dispatcha internamente. Configurare endpoint separati ha senso solo in architetture a microservizi dove diversi servizi gestiscono diversi aspetti del billing (es. un servizio per subscription, uno per invoicing, uno per analytics).

### 10. Come gestisco le subscription con più componenti (base + addon)?

Usare subscription con più `items`. Ogni item ha un suo Price. Si possono aggiungere e rimuovere item dalla subscription senza ricrearla:

```python
# Aggiungere un addon alla subscription esistente
stripe.SubscriptionItem.create(
    subscription='sub_xxx',
    price='price_addon_storage',
    quantity=1,
)
```

### 11. Stripe trattiene le tasse dalla mia commissione?

No. Stripe addebita la propria commissione (tipicamente 1.5% + €0.25 in Europa per carte europee) separatamente. Le tasse che Stripe Tax raccoglie dai clienti vengono trasferite al proprio conto e si è responsabili del versamento alle autorità fiscali. Stripe fornisce i report per facilitare il versamento.

### 12. Come gestisco i pagamenti falliti per carte scadute?

Stripe Card Account Updater aggiorna automaticamente i dati delle carte rinnovate dalle banche partecipanti (la maggior parte delle banche europee e americane). Per le carte non aggiornabili, l'evento `invoice.payment_failed` segnala il problema; implementare un flusso di dunning con email e link al Customer Portal per aggiornare il metodo di pagamento.

### 13. Posso usare Stripe in modalità "test" per demo e staging?

Sì. L'ambiente di test è completamente separato e gratuito. Si possono creare customer, subscription, e processare pagamenti con le carte di test senza addebiti reali. Per staging, usare Restricted API Keys con permessi limitati per minimizzare il rischio.

### 14. Come gestisco la fatturazione per clienti B2B che richiedono pagamento su fattura (net 30/60)?

Usare `collection_method='send_invoice'` con `days_until_due=30` (o 60). Stripe genera la fattura, la invia via email, e traccia il pagamento. L'utente può pagare tramite il link nella fattura con carta, bonifico (se abilitato), o altri metodi. Implementare reminder automatici nella Dashboard (Settings → Billing → Invoices → Reminders).

### 15. Qual è il costo effettivo di Stripe per un SaaS europeo?

La commissione standard per carte europee è 1.5% + €0.25 per transazione riuscita. Per carte non-europee: 2.9% + €0.25. Stripe Billing aggiunge 0.5% per fatture di subscription. Stripe Tax aggiunge 0.5% per transazione dove calcola le tasse. I payout sul conto bancario sono gratuiti. Non ci sono costi fissi mensili o costi di setup.

### 16. Come posso vedere in anticipo quanto pagherà un cliente al rinnovo?

Usare `stripe.Invoice.upcoming(customer='cus_xxx')` per ottenere una preview della prossima fattura. Questa include l'importo, le righe dettagliate, le tasse, e la data di emissione. Mostrare questa informazione nella pagina di billing dell'utente per trasparenza.

### 17. Come implemento un "credito" o "wallet" per l'utente?

Usare il Customer Balance di Stripe. Aggiungere credito con `stripe.Customer.create_balance_transaction()` con amount negativo. Il credito viene applicato automaticamente alla prossima fattura. Utile per: rimborsi parziali, crediti promozionali, prepagato.

### 18. Cosa succede se Stripe è down durante un pagamento?

Stripe ha un uptime del 99.999%. In caso di downtime, i pagamenti off-session (rinnovi) vengono retried automaticamente. Per pagamenti on-session, mostrare un messaggio all'utente e suggerire di riprovare. Mai cachare dati di carta localmente come fallback — viola PCI DSS.

---

## Riferimenti

- Stripe Documentation: https://stripe.com/docs — Documentazione ufficiale completa
- Stripe API Reference: https://stripe.com/docs/api — Reference API dettagliato
- Stripe CLI Reference: https://stripe.com/docs/stripe-cli — Documentazione CLI
- Stripe Billing Best Practices: https://stripe.com/docs/billing/subscriptions/overview — Guida alle subscription
- Stripe Webhooks Best Practices: https://stripe.com/docs/webhooks/best-practices — Pattern per webhook
- Stripe Testing: https://stripe.com/docs/testing — Carte di test e scenari
- Stripe Test Clocks: https://stripe.com/docs/billing/testing/test-clocks — Simulazione temporale
- Stripe Tax Documentation: https://stripe.com/docs/tax — Gestione automatica delle tasse
- Stripe Connect: https://stripe.com/docs/connect — Documentazione marketplace
- Stripe Revenue Recognition: https://stripe.com/docs/revenue-recognition — Riconoscimento ricavi
- Stripe Elements: https://stripe.com/docs/payments/elements — Componenti UI embeddabili
- Stripe Payment Links: https://stripe.com/docs/payment-links — Pagamenti senza codice
- Stripe Meters: https://stripe.com/docs/billing/subscriptions/usage-based/meters — Fatturazione a consumo
- PCI DSS Compliance Guide: https://stripe.com/docs/security — Compliance di sicurezza
- "Stripe Engineering Blog" — Architettura e design decisions di Stripe
- "Designing Billing Systems" — Patrick McKenzie (patio11) — Considerazioni architetturali
