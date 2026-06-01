# Billing e Pagamenti SaaS — Guida Completa

## Indice

- [Panoramica](#panoramica)
- [Architettura del Sistema di Billing](#architettura-del-sistema-di-billing)
- [Confronto Payment Processor](#confronto-payment-processor)
- [PCI DSS Compliance](#pci-dss-compliance)
- [Gestione Sottoscrizioni](#gestione-sottoscrizioni)
- [Proration — Calcolo Pro-Rata Approfondito](#proration--calcolo-pro-rata-approfondito)
- [Billing Metered e Usage-Based](#billing-metered-e-usage-based)
- [Fatturazione e Invoicing](#fatturazione-e-invoicing)
- [Gestione Multi-Currency e FX](#gestione-multi-currency-e-fx)
- [Billing Enterprise](#billing-enterprise)
- [Payment Processing](#payment-processing)
- [Revenue Recognition](#revenue-recognition)
- [Tassazione Internazionale](#tassazione-internazionale)
- [Dunning e Recupero Pagamenti](#dunning-e-recupero-pagamenti)
- [Webhook Integration Patterns](#webhook-integration-patterns)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Checklist di Implementazione](#checklist-di-implementazione)

---

## Panoramica

Il billing è il cuore operativo di un SaaS: gestisce le sottoscrizioni, processa i pagamenti, emette le fatture, gestisce le tasse e riconosce il revenue. Un sistema di billing mal progettato crea frizione per il cliente (churn), errori contabili, problemi fiscali e overhead operativo. La complessità cresce rapidamente: upgrade, downgrade, proration, annual vs monthly, multi-currency, tax compliance, dunning. La scelta tra build vs buy è critica.

### Perché il Billing Merita un Investimento Strategico

Il billing non è un componente "commodity" da implementare alla fine. È il sistema che:

- **Determina il cash flow**: ritardi di settlement, retry falliti, pagamenti in sospeso influiscono direttamente sulla liquidità.
- **Condiziona il churn**: il 20-40% del churn è involontario (pagamento fallito). Un dunning system efficace recupera il 50-70% di questo revenue.
- **Impatta la compliance**: errori di fatturazione o tax handling espongono a sanzioni, audit fiscali e rischi legali.
- **Scala con il business**: un billing system che funziona per 100 clienti potrebbe non reggere 10.000 clienti in 30 paesi con 5 valute.
- **Abilita upsell e expansion**: proration, add-on, usage-based billing sono meccanismi di crescita del revenue che richiedono un billing sofisticato.

### Metriche Chiave di un Billing System

| Metrica | Target | Cosa Indica |
|---|---|---|
| Payment success rate | > 95% | Efficacia del payment processing |
| Involuntary churn rate | < 2% mensile | Efficacia del dunning |
| Time to invoice | < 1 min | Automazione della fatturazione |
| Revenue leakage | < 0.5% | Accuratezza del billing |
| Dispute/chargeback rate | < 0.1% | Qualità del servizio e comunicazione |
| Dunning recovery rate | > 60% | Efficacia del recupero pagamenti |
| Tax compliance accuracy | 100% | Correttezza fiscale |
| Settlement time | < 3 giorni | Velocità del cash flow |

---

## Architettura del Sistema di Billing

### Build vs Buy

**Buy (consigliato per il 95% dei SaaS)**:
- **Stripe Billing**: lo standard per SaaS. Gestisce sottoscrizioni, proration, dunning, invoicing, tax (Stripe Tax). API eccellente, documentazione impeccabile.
- **Chargebee**: più completo per scenari enterprise (quote-to-cash, revenue recognition). Costoso.
- **Paddle/LemonSqueezy**: Merchant of Record — gestiscono anche le tasse (IVA, sales tax) come rivenditori. Ideale per SaaS che vendono globalmente senza voler gestire la compliance fiscale.
- **Recurly**: alternativa a Chargebee, forte su dunning management.

**Build (solo se necessario)**: solo se il modello di pricing è così unico che nessuna piattaforma lo supporta (raro). Costo stimato: 6-12 mesi di engineering per un sistema base, manutenzione continua.

### Architettura Tipica

```
Frontend (pricing page, checkout)
  → Backend (subscription logic, entitlement)
    → Payment Processor (Stripe, Braintree)
      → Acquirer → Card Network → Issuing Bank
    → Invoicing System
    → Tax Engine (Stripe Tax, Avalara, TaxJar)
    → Accounting System (Xero, QuickBooks)
    → Revenue Recognition (se necessario)
```

### Architettura a Layer Dettagliata

```
┌──────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                           │
│  Pricing Page │ Checkout Flow │ Customer Portal │ Admin Dashboard│
└──────────────┬───────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────┐
│                     API / ORCHESTRATION LAYER                    │
│  Subscription API │ Invoice API │ Payment API │ Webhook Handler  │
└──────────────┬───────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────┐
│                     DOMAIN LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐        │
│  │ Subscription │  │  Entitlement │  │ Usage Metering  │        │
│  │   Engine     │  │    System    │  │    Pipeline     │        │
│  └──────────────┘  └──────────────┘  └─────────────────┘        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐        │
│  │   Proration  │  │    Dunning   │  │  Tax Calculator │        │
│  │  Calculator  │  │   Manager    │  │                 │        │
│  └──────────────┘  └──────────────┘  └─────────────────┘        │
└──────────────┬───────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────┐
│                     INTEGRATION LAYER                            │
│  Stripe/Paddle │ Tax Engine │ Accounting │ CRM │ Notification    │
└──────────────────────────────────────────────────────────────────┘
```

### Entitlement System

L'entitlement system determina cosa ogni cliente può fare in base al piano sottoscritto:

```python
# Esempio di entitlement check
def can_access_feature(tenant, feature):
    plan = get_current_plan(tenant)
    return feature in plan.features

def check_usage_limit(tenant, resource):
    plan = get_current_plan(tenant)
    current_usage = get_usage(tenant, resource)
    limit = plan.limits.get(resource)
    return current_usage < limit

# L'entitlement deve essere:
# - Veloce (cacheable, no DB query per ogni richiesta)
# - Consistente (aggiornato in real-time al cambio piano)
# - Flessibile (override per tenant, feature flag)
```

### Entitlement System — Pattern Avanzato

```python
# Entitlement service con cache e fallback
class EntitlementService:
    def __init__(self, cache, billing_provider, feature_flags):
        self.cache = cache
        self.billing = billing_provider
        self.flags = feature_flags

    def check(self, tenant_id, feature):
        # 1. Check feature flag override (per-tenant)
        override = self.flags.get_override(tenant_id, feature)
        if override is not None:
            return override

        # 2. Check cache
        cached = self.cache.get(f"entitlement:{tenant_id}:{feature}")
        if cached is not None:
            return cached

        # 3. Fetch from billing provider
        plan = self.billing.get_subscription(tenant_id)
        entitled = feature in plan.entitled_features
        
        # 4. Cache con TTL breve (5 min) per bilanciare
        #    performance e consistenza
        self.cache.set(
            f"entitlement:{tenant_id}:{feature}",
            entitled,
            ttl_seconds=300
        )
        return entitled

    def invalidate(self, tenant_id):
        """Chiamato via webhook quando cambia la subscription."""
        self.cache.delete_pattern(f"entitlement:{tenant_id}:*")
```

---

## Confronto Payment Processor

### Matrice Decisionale

| Criterio | Stripe | Paddle | Chargebee | Recurly |
|---|---|---|---|---|
| **Modello** | Payment processor | Merchant of Record | Billing platform | Billing platform |
| **Commissioni base** | 2.9% + $0.30 | 5% + $0.50 | $249-$549/mese + % | $249/mese + % |
| **Gestisce tasse** | Sì (Stripe Tax, add-on) | Sì (incluso, è il rivenditore) | Parziale (integra Avalara) | Parziale (integra TaxJar) |
| **Merchant of Record** | No (tu sei il MoR) | Sì (Paddle è il MoR) | No | No |
| **API quality** | Eccellente (gold standard) | Buona | Buona | Media |
| **Self-service checkout** | Stripe Checkout / Elements | Paddle.js overlay | Checkout Pages | Checkout widget |
| **Enterprise billing** | Stripe Invoicing | Limitato | Ottimo (quote-to-cash) | Buono |
| **Revenue recognition** | Stripe Revenue Recognition | Limitato | Integrato (RevenueStory) | Limitato |
| **Dunning management** | Smart Retries (ML) | Incluso | Avanzato (altamente configurabile) | Best-in-class |
| **Usage-based billing** | Sì (Stripe Meters) | Limitato | Sì | Sì |
| **Multi-currency** | 135+ valute | 40+ valute | 100+ valute | 20+ valute |
| **Scalabilità** | Illimitata | Buona | Fino a enterprise | Fino a mid-market |
| **Tempo di integrazione** | 1-4 settimane | 1-2 settimane | 2-6 settimane | 2-4 settimane |
| **Costo per $1M ARR** | ~$29K-35K | ~$50K-55K | ~$15K-20K + processing | ~$12K-18K + processing |

### Quando Usare Cosa

**Stripe** — Scegliere quando:
- Si vuole controllo totale sulla checkout experience.
- Si hanno requisiti di billing complessi (usage-based, proration avanzata).
- Il team ha capacità engineering per integrare le API.
- Si vende prevalentemente in mercati dove si ha già presenza fiscale.
- Volume di transazioni > 1.000/mese (commissioni negoziabili).

**Paddle** — Scegliere quando:
- Si vuole eliminare completamente la gestione fiscale (IVA, sales tax).
- Team piccolo senza risorse per compliance fiscale multi-paese.
- Si vende a consumatori (B2C) in molti paesi.
- ARR < $5M (sopra questa soglia la commissione del 5% pesa).
- Si preferisce andare live velocemente senza complessità.

**Chargebee** — Scegliere quando:
- Si ha un modello di pricing complesso (tiered, volume, stairstep).
- Si serve il segmento enterprise con quote-to-cash workflow.
- Si necessita di revenue recognition integrata.
- Il team finance richiede reporting avanzato.
- Si vuole separare billing platform da payment processor (Chargebee usa Stripe/Braintree/Adyen sotto).

**Recurly** — Scegliere quando:
- Il dunning management è la priorità numero uno (Recurly è il migliore).
- Si hanno tassi alti di involuntary churn da risolvere.
- Il modello è subscription pura (no marketplace, no usage complesso).
- Budget limitato per la billing platform.

### Costi Nascosti da Considerare

| Voce di Costo | Stripe | Paddle | Chargebee | Recurly |
|---|---|---|---|---|
| Chargeback fee | $15/evento | Incluso (MoR risk) | Dipende dal processor | Dipende dal processor |
| Stripe Tax add-on | +0.5% per transazione | Incluso | Non applicabile | Non applicabile |
| Payout internazionale | 0.25-1% | Incluso | Dipende | Dipende |
| 3D Secure | Gratuito | Incluso | Dipende | Dipende |
| ACH processing | 0.8% (cap $5) | Non supportato | Dipende | 0.8% + fee |
| API call overage | Nessun limite | Limiti per piano | Limiti per piano | Limiti per piano |
| Revenue Recognition | $10/fattura/mese | Non disponibile | Incluso in alcuni piani | Non disponibile |

---

## PCI DSS Compliance

### Cos'è PCI DSS

Il Payment Card Industry Data Security Standard (PCI DSS) è un set di requisiti di sicurezza obbligatorio per qualsiasi entità che processa, trasmette o memorizza dati di carte di pagamento. La versione corrente è PCI DSS v4.0 (in vigore dal 31 marzo 2024, con alcune clausole posticipate al 31 marzo 2025).

### Livelli di Compliance PCI

Il livello dipende dal volume annuo di transazioni con carta:

| Livello | Volume Transazioni/Anno | Requisiti |
|---|---|---|
| **Level 1** | > 6 milioni | Report on Compliance (ROC) da QSA esterno, scan ASV trimestrale, penetration test annuale |
| **Level 2** | 1-6 milioni | SAQ (Self-Assessment Questionnaire), scan ASV trimestrale |
| **Level 3** | 20.000 - 1 milione (e-commerce) | SAQ, scan ASV trimestrale |
| **Level 4** | < 20.000 (e-commerce) o < 1 milione (altri) | SAQ, scan ASV consigliato |

La maggior parte dei SaaS rientra nei livelli 3 o 4.

### Tipi di SAQ (Self-Assessment Questionnaire)

| SAQ | Scenario | N° Requisiti | Complessità |
|---|---|---|---|
| **SAQ-A** | Checkout completamente in outsourcing (Stripe Checkout, Paddle). Nessun dato carta tocca il server. | ~22 domande | Minima |
| **SAQ-A-EP** | La pagina di pagamento è sul tuo dominio ma usa iframe/JS del processor (Stripe Elements). Il server non vede i dati carta ma il frontend li gestisce indirettamente. | ~139 domande | Media |
| **SAQ-D** | Gestione diretta dei dati carta (il server riceve e/o memorizza PAN, CVV, scadenza). | ~329 domande | Massima |

### Cosa Serve a un SaaS Tipico

**Scenario consigliato — SAQ-A (minimo sforzo)**:
Usare Stripe Checkout o Paddle Checkout. Il cliente viene reindirizzato a una pagina di pagamento ospitata dal processor. Nessun dato carta transita dal server SaaS.

**Scenario comune — SAQ-A-EP (Stripe Elements)**:
Il form di pagamento è integrato nella pagina del SaaS usando Stripe Elements (iframe). I dati carta vanno direttamente a Stripe via JavaScript, il backend riceve solo un `PaymentMethod` token. Il server SaaS non vede mai il PAN.

Requisiti SAQ-A-EP:
- TLS 1.2+ su tutte le pagine con checkout.
- CSP (Content Security Policy) che blocca script injection.
- Scan ASV trimestrale del dominio che ospita il checkout.
- Nessun log che contenga dati carta (nemmeno parziali).
- Vulnerability scan del frontend.

**Scenario da evitare — SAQ-D**:
Raccogliere direttamente i dati carta lato server (raw PAN nel POST). Richiede centinaia di controlli, audit esterni, segmentazione di rete, crittografia at-rest e in-transit, log monitoring, IDS/IPS. Nessun SaaS moderno dovrebbe trovarsi in questa situazione.

### Checklist PCI per SaaS con Stripe Elements

```
[ ] TLS 1.2+ attivo su tutto il dominio (non solo checkout)
[ ] Stripe Elements o Checkout integrato (no raw card input)
[ ] CSP header configurata per permettere solo js.stripe.com
[ ] Nessun log contiene dati carta (grep per pattern PAN)
[ ] Scan ASV trimestrale del dominio (es. Qualys, Trustwave)
[ ] SAQ-A-EP compilato e firmato annualmente
[ ] Incidenti di sicurezza: processo documentato di notifica
[ ] Accesso ai sistemi di pagamento limitato (principle of least privilege)
[ ] Review annuale delle pratiche PCI
[ ] Training annuale PCI per il team che gestisce il checkout
```

### Errori Comuni PCI

| Errore | Rischio | Soluzione |
|---|---|---|
| Loggare `card_number` o `cvc` nei log server | SAQ-D obbligatorio, data breach | Grep per pattern `\d{13,19}` nei log, eliminare |
| Non avere TLS sulla pricing page | Man-in-the-middle, form hijacking | TLS su tutto il dominio, HSTS header |
| Memorizzare card token nel localStorage | Token theft via XSS | Token solo server-side, mai nel browser |
| Nessuna CSP sulla checkout page | Script injection, skimming | CSP rigorosa: `script-src 'self' js.stripe.com` |
| Usare iframe del processor ma senza scan ASV | Non conformità SAQ-A-EP | Scan trimestrale obbligatorio |

---

## Gestione Sottoscrizioni

### Ciclo di Vita della Sottoscrizione

```
                                    ┌─────────────┐
                                    │   Created    │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                              ┌─────│   Trialing  │─────┐
                              │     └──────┬──────┘     │
                              │            │             │
                         (trial scaduto    │        (converte)
                          no payment)      │             │
                              │     ┌──────▼──────┐     │
                              │     │   Active     │◄────┘
                              │     └──┬───┬───┬──┘
                              │        │   │   │
                         ┌────▼────┐   │   │   │
                         │Cancelled│   │   │   │
                         └─────────┘   │   │   │
                                       │   │   │
                    ┌──────────────────┘   │   └──────────────────┐
                    │                      │                       │
             ┌──────▼──────┐        ┌──────▼──────┐        ┌──────▼──────┐
             │  Upgrade /  │        │   Past Due  │        │   Paused    │
             │  Downgrade  │        └──────┬──────┘        └──────┬──────┘
             └──────┬──────┘               │                      │
                    │                ┌─────┴─────┐                │
                    │           (recuperato)  (non recuperato)     │
                    │                │           │                 │
                    │         ┌──────▼──┐  ┌─────▼─────┐          │
                    └────────►│  Active  │  │ Cancelled │          │
                              └─────────┘  └───────────┘          │
                                    ▲                              │
                                    │         (riattivato)        │
                                    └─────────────────────────────┘
```

### Stati della Sottoscrizione — Dettaglio

| Stato | Significato | Entitlement | Billing |
|---|---|---|---|
| `trialing` | Periodo di prova, con o senza carta | Accesso pieno (o limitato) | Nessun addebito fino a fine trial |
| `active` | Pagamento corrente, servizio attivo | Accesso pieno al piano | Addebiti regolari al ciclo |
| `past_due` | Pagamento fallito, in dunning | Accesso mantenuto (grazia) | Retry automatici in corso |
| `paused` | Sospeso dal cliente o dal sistema | Accesso negato | Nessun addebito |
| `canceled` | Cancellato (potrebbe avere accesso fino a fine periodo) | Accesso fino a `current_period_end` | Nessun addebito futuro |
| `unpaid` | Tutti i retry falliti, dunning esaurito | Accesso negato | Ultimo tentativo fallito |
| `expired` | Trial scaduto senza conversione | Accesso negato | Mai addebitato |

### Creazione della Sottoscrizione

```python
# Pseudocode: creazione subscription con Stripe-like API
def create_subscription(customer_id, price_id, options=None):
    # 1. Validare il customer
    customer = billing.get_customer(customer_id)
    if not customer:
        raise CustomerNotFoundError(customer_id)

    # 2. Verificare che abbia un payment method
    if not customer.default_payment_method:
        raise NoPaymentMethodError(customer_id)

    # 3. Creare la subscription
    subscription = billing.create_subscription(
        customer=customer_id,
        items=[{"price": price_id}],
        trial_period_days=options.get("trial_days", 0),
        payment_behavior="default_incomplete",  # Gestire 3DS
        expand=["latest_invoice.payment_intent"],
        metadata={
            "source": options.get("source", "checkout"),
            "campaign": options.get("campaign"),
        }
    )

    # 4. Gestire lo stato iniziale
    if subscription.status == "incomplete":
        # 3D Secure richiesto — restituire client_secret al frontend
        return {
            "status": "requires_action",
            "client_secret": subscription.latest_invoice
                .payment_intent.client_secret,
            "subscription_id": subscription.id,
        }

    # 5. Provisioning degli entitlement
    entitlement_service.grant(customer_id, price_id)

    # 6. Tracking
    analytics.track("subscription_created", {
        "customer_id": customer_id,
        "plan": price_id,
        "trial": options.get("trial_days", 0) > 0,
    })

    return {"status": "active", "subscription_id": subscription.id}
```

### Upgrade e Downgrade

**Upgrade**: il cliente passa a un piano superiore. Approcci:
- **Immediato con proration**: il cliente paga la differenza pro-rata per il periodo rimanente. Standard per monthly billing.
- **Al prossimo rinnovo**: il piano cambia alla scadenza corrente. Meno friction, ma il cliente non accede alle feature premium subito.

**Downgrade**: il cliente passa a un piano inferiore.
- **Al prossimo rinnovo** (standard): il cliente mantiene il piano premium fino alla scadenza. Evita rimborsi e complessità.
- **Immediato con credito**: meno comune, genera credito da applicare ai prossimi cicli.

```python
# Pseudocode: gestione upgrade/downgrade
def change_plan(subscription_id, new_price_id, mode="immediate"):
    subscription = billing.get_subscription(subscription_id)
    old_price = subscription.items[0].price.id
    old_amount = subscription.items[0].price.unit_amount
    new_amount = billing.get_price(new_price_id).unit_amount

    is_upgrade = new_amount > old_amount

    if mode == "immediate":
        # Upgrade immediato: proration attiva
        updated = billing.update_subscription(subscription_id,
            items=[{
                "id": subscription.items[0].id,
                "price": new_price_id,
            }],
            proration_behavior="create_prorations",
        )
        # Entitlement aggiornato subito
        entitlement_service.update(subscription.customer, new_price_id)

    elif mode == "at_period_end":
        # Cambio al prossimo rinnovo (tipico per downgrade)
        schedule = billing.create_subscription_schedule(
            from_subscription=subscription_id,
        )
        billing.update_subscription_schedule(schedule.id,
            phases=[
                {
                    "items": [{"price": old_price}],
                    "end_date": subscription.current_period_end,
                },
                {
                    "items": [{"price": new_price_id}],
                },
            ]
        )
        # Entitlement invariato fino al cambio fase

    analytics.track("plan_changed", {
        "direction": "upgrade" if is_upgrade else "downgrade",
        "old_plan": old_price,
        "new_plan": new_price_id,
        "mode": mode,
    })
```

### Pausa della Sottoscrizione

La pausa è un'alternativa alla cancellazione che preserva il cliente:

```python
# Pseudocode: pausa e riattivazione
def pause_subscription(subscription_id, resume_date=None):
    """
    Pausa: blocca il billing, nega l'accesso, preserva i dati.
    resume_date: data di riattivazione automatica (opzionale).
    """
    billing.update_subscription(subscription_id,
        pause_collection={"behavior": "void"},  # Non addebitare
    )
    entitlement_service.revoke(subscription_id)
    
    if resume_date:
        scheduler.schedule(
            action="resume_subscription",
            subscription_id=subscription_id,
            execute_at=resume_date,
        )

def resume_subscription(subscription_id):
    """Riattiva una subscription in pausa."""
    billing.update_subscription(subscription_id,
        pause_collection=None,  # Riprendi il billing
    )
    # Verifica che il payment method sia ancora valido
    subscription = billing.get_subscription(subscription_id)
    validate_payment_method(subscription.customer)
    entitlement_service.grant(subscription_id)
```

### Cancellazione e Riattivazione

```python
# Pseudocode: cancellazione con opzioni
def cancel_subscription(subscription_id, mode="at_period_end", reason=None):
    """
    at_period_end: accesso fino a fine periodo pagato (standard).
    immediate: accesso revocato subito, possibile rimborso pro-rata.
    """
    if mode == "at_period_end":
        billing.update_subscription(subscription_id,
            cancel_at_period_end=True,
        )
        # L'utente mantiene l'accesso fino a current_period_end

    elif mode == "immediate":
        billing.cancel_subscription(subscription_id,
            prorate=True,  # Rimborso pro-rata dei giorni non usati
        )
        entitlement_service.revoke(subscription_id)

    # Logging del motivo di cancellazione per analisi churn
    if reason:
        analytics.track("subscription_cancelled", {
            "subscription_id": subscription_id,
            "mode": mode,
            "reason": reason,  # "too_expensive", "missing_feature", etc.
        })

def reactivate_subscription(subscription_id):
    """Riattiva una subscription cancellata ma non ancora scaduta."""
    subscription = billing.get_subscription(subscription_id)
    
    if subscription.status != "canceled":
        raise InvalidStateError("Subscription non è in stato cancelled")
    
    if now() > subscription.current_period_end:
        # Periodo scaduto: serve una nuova subscription
        raise PeriodExpiredError("Creare una nuova subscription")
    
    billing.update_subscription(subscription_id,
        cancel_at_period_end=False,  # Rimuovi la cancellazione
    )
    entitlement_service.grant(subscription_id)
```

### Annual vs Monthly

| Aspetto | Monthly | Annual |
|---|---|---|
| Cash flow | Graduale | Upfront (12 mesi) |
| Churn rate | Più alto (decisione mensile) | Più basso (commitment) |
| Sconto tipico | Nessuno | 15-25% vs monthly |
| LTV | Potenzialmente più basso | Potenzialmente più alto |
| Contabilità | Semplice | Deferred revenue |

**Strategia**: offrire entrambi. Mostrare il prezzo annuale come default con il risparmio evidenziato ("Risparmia il 20%"). Il 30-50% dei clienti SaaS sceglie annuale quando l'opzione è ben presentata.

### Trial Management

| Strategia Trial | Pro | Contro | Quando Usare |
|---|---|---|---|
| Free trial (no carta) | Bassa frizione, più sign-up | Bassa conversione (2-5%) | Prodotto virale, PMF non validato |
| Free trial (carta richiesta) | Conversione più alta (15-30%) | Meno sign-up, friction | PMF validato, prodotto sticky |
| Reverse trial (full → free) | Esperienza premium, urgenza | Complessità di implementazione | Prodotto con feature gate forte |
| Freemium (no trial) | Acquisizione continua | Lenta conversione | Mercato grande, network effect |

```python
# Pseudocode: trial con carta e auto-conversione
def start_trial_with_card(customer_id, price_id, trial_days=14):
    subscription = billing.create_subscription(
        customer=customer_id,
        items=[{"price": price_id}],
        trial_period_days=trial_days,
        # Non addebitare fino a fine trial
        payment_behavior="default_incomplete",
    )
    
    # Schedulare reminder pre-scadenza trial
    scheduler.schedule(
        action="send_trial_ending_email",
        execute_at=subscription.trial_end - days(3),
        data={"customer_id": customer_id},
    )
    
    return subscription
```

---

## Proration — Calcolo Pro-Rata Approfondito

### Principio Base

La proration calcola il costo equo quando un cambio di piano avviene a metà ciclo di billing. Il principio: il cliente paga solo per ciò che usa.

### Esempio Base

```
Esempio: upgrade da $50/mese a $100/mese il giorno 15 (mese di 30 giorni)

Credito per giorni non usati del piano vecchio:
  $50 × (15/30) = $25

Addebito per giorni rimanenti del piano nuovo:
  $100 × (15/30) = $50

Netto da addebitare: $50 - $25 = $25

Stripe gestisce automaticamente la proration.
```

### Calcolo Dettagliato — Formulario

```python
# Pseudocode: calcolo proration preciso
def calculate_proration(
    old_price,          # Prezzo mensile del piano corrente
    new_price,          # Prezzo mensile del nuovo piano
    change_date,        # Data del cambio
    period_start,       # Inizio del ciclo corrente
    period_end,         # Fine del ciclo corrente
):
    total_days = (period_end - period_start).days
    days_used = (change_date - period_start).days
    days_remaining = total_days - days_used

    # Credito per il piano vecchio (giorni non usati)
    credit = old_price * (days_remaining / total_days)
    
    # Addebito per il piano nuovo (giorni rimanenti)
    charge = new_price * (days_remaining / total_days)
    
    # Netto
    net = charge - credit
    
    return {
        "credit": round(credit, 2),
        "charge": round(charge, 2),
        "net": round(net, 2),
        "days_remaining": days_remaining,
        "total_days": total_days,
    }

# Esempio:
# calculate_proration(50, 100, day_15, day_1, day_30)
# → credit: 25.00, charge: 50.00, net: 25.00
```

### Edge Cases della Proration

| Scenario | Comportamento | Nota |
|---|---|---|
| Upgrade giorno 1 del ciclo | Credito pieno del vecchio piano, addebito pieno del nuovo | Quasi equivalente a un semplice cambio piano |
| Upgrade ultimo giorno del ciclo | Credito quasi zero, addebito quasi zero | In pratica conviene aspettare il rinnovo |
| Downgrade con credito > costo | Il credito viene applicato ai cicli successivi | Il cliente non paga per 1+ cicli |
| Multipli cambi nello stesso ciclo | Ogni cambio genera una proration line item | Può diventare confuso in fattura — limitare |
| Cambio da monthly ad annual | Calcolare il credito monthly, addebitare l'intero annual | Attenzione: somma grande, comunicare chiaramente |
| Piano con add-on | Proration su piano base + proration su ogni add-on | Complessità moltiplicata |

### Strategie di Proration

| Strategia | Come Funziona | Quando Usarla |
|---|---|---|
| `create_prorations` | Genera line item di credito e addebito | Standard per upgrade immediati |
| `none` | Nessuna proration, il cambio avviene ma senza aggiustamento | Cambio al prossimo rinnovo |
| `always_invoice` | Genera una fattura immediata per la proration | Quando serve pagamento immediato |

---

## Billing Metered e Usage-Based

### Architettura del Metering

Il billing usage-based richiede un pipeline di metering robusto:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  Applicazione│────►│  Event Queue │────►│  Aggregation │────►│  Billing   │
│  (emette     │     │  (Kafka,     │     │   Engine     │     │  Provider  │
│   eventi)    │     │   SQS, etc.) │     │              │     │  (Stripe)  │
└─────────────┘     └──────────────┘     └──────────────┘     └────────────┘
      │                                        │
      │                                        ▼
      │                                  ┌──────────────┐
      └─────────────────────────────────►│  Dashboard   │
                                         │  (real-time  │
                                         │   usage)     │
                                         └──────────────┘
```

### Modelli di Usage-Based Billing

| Modello | Descrizione | Esempio | Pro | Contro |
|---|---|---|---|---|
| **Pay-as-you-go** | Paga solo per ciò che usi | AWS Lambda ($0.20/1M invocazioni) | Bassa barriera d'ingresso | Revenue imprevedibile |
| **Tiered pricing** | Prezzo per unità scende con il volume | Twilio ($0.0075/SMS 1-500K, $0.005/SMS 500K+) | Incentiva il volume | Complessità di calcolo |
| **Volume pricing** | Prezzo per tutte le unità basato sul tier raggiunto | "Tutte le API call a $0.01 se usi 0-10K, tutte a $0.008 se usi 10K+" | Semplice per il cliente | Cliff pricing (improvviso calo) |
| **Staircase** | Pacchetti fissi, si paga il prossimo blocco | "$49 per 0-1.000 eventi, $99 per 1.001-5.000" | Revenue prevedibile | Sprechi per il cliente |
| **Prepaid credits** | Il cliente compra crediti, li consuma | OpenAI ($5 di crediti prepaid) | Cash flow anticipato | Gestione crediti scaduti |
| **Hybrid** | Base fissa + usage variabile | Plataforma con $99/mese + $0.01/API call | Revenue base stabile | Complessità di billing |

### Implementazione del Metering

```python
# Pseudocode: pipeline di metering

# 1. EMISSIONE EVENTI — nel codice applicativo
def track_usage_event(tenant_id, metric, quantity=1, properties=None):
    """Emette un evento di usage. Deve essere:
    - Idempotente (idempotency_key per evitare doppi conteggi)
    - Asincrono (non bloccare la request del cliente)
    - Resiliente (buffer locale se la queue è down)
    """
    event = {
        "tenant_id": tenant_id,
        "metric": metric,           # es. "api_calls", "storage_gb"
        "quantity": quantity,
        "timestamp": utc_now(),
        "idempotency_key": generate_idempotency_key(
            tenant_id, metric, request_id
        ),
        "properties": properties,   # metadata opzionale
    }
    event_queue.publish("usage_events", event)

# 2. AGGREGAZIONE — processo batch o streaming
def aggregate_usage(tenant_id, metric, period_start, period_end):
    """Aggrega gli eventi in un totale per il periodo di billing."""
    events = event_store.query(
        tenant_id=tenant_id,
        metric=metric,
        timestamp_gte=period_start,
        timestamp_lt=period_end,
    )
    # Deduplica per idempotency_key
    unique_events = deduplicate(events, key="idempotency_key")
    total = sum(e.quantity for e in unique_events)
    return total

# 3. REPORTING AL BILLING PROVIDER — prima della fatturazione
def report_usage_to_billing(tenant_id, billing_period):
    """Riporta l'usage aggregato al billing provider."""
    for metric in METERED_METRICS:
        total = aggregate_usage(
            tenant_id, metric,
            billing_period.start, billing_period.end
        )
        billing.create_usage_record(
            subscription_item=get_sub_item(tenant_id, metric),
            quantity=total,
            timestamp=billing_period.end,
            action="set",  # "set" = valore assoluto, "increment" = cumulativo
        )
```

### Gestione Crediti Prepaid

```python
# Pseudocode: sistema di crediti prepaid
class CreditLedger:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id

    def purchase_credits(self, amount, payment_method):
        """Il cliente compra crediti."""
        # Addebitare il pagamento
        payment = billing.charge(
            customer=self.tenant_id,
            amount=amount,
            payment_method=payment_method,
        )
        # Aggiungere al ledger
        ledger.add_entry(
            tenant_id=self.tenant_id,
            type="purchase",
            amount=amount,
            balance_after=self.get_balance() + amount,
            reference=payment.id,
        )

    def consume_credits(self, amount, description):
        """Consumo di crediti per usage."""
        balance = self.get_balance()
        if balance < amount:
            raise InsufficientCreditsError(
                f"Servono {amount} crediti, disponibili {balance}"
            )
        ledger.add_entry(
            tenant_id=self.tenant_id,
            type="consumption",
            amount=-amount,
            balance_after=balance - amount,
            description=description,
        )

    def get_balance(self):
        """Saldo corrente."""
        return ledger.sum_entries(self.tenant_id)

    def check_low_balance(self, threshold_pct=20):
        """Alert quando il saldo scende sotto la soglia."""
        balance = self.get_balance()
        avg_daily = self.avg_daily_consumption(days=30)
        days_remaining = balance / avg_daily if avg_daily > 0 else float('inf')
        if days_remaining < 7:
            notify.send(self.tenant_id, "low_credit_balance", {
                "balance": balance,
                "estimated_days": days_remaining,
            })
```

### Sfide del Metered Billing

| Sfida | Soluzione |
|---|---|
| Doppio conteggio eventi | Idempotency key su ogni evento |
| Latenza tra uso e fatturazione | Streaming aggregation (non solo batch) |
| Dispute sui volumi fatturati | Dashboard real-time del consumo per il cliente |
| Spike di usage imprevisti | Alert proattivo + cap configurabile dal cliente |
| Crediti scaduti | Policy chiara nei ToS, notifica 30 giorni prima |
| Riconciliazione usage vs billing | Audit log immutabile con checksum |

---

## Fatturazione e Invoicing

### Componenti della Fattura SaaS

Ogni fattura deve includere:
- Dati del fornitore (ragione sociale, P.IVA/VAT, indirizzo)
- Dati del cliente (ragione sociale, P.IVA/VAT se B2B, indirizzo)
- Numero fattura progressivo e univoco
- Data emissione e periodo di riferimento
- Dettaglio servizi (piano, quantità, prezzo unitario)
- Subtotale, tasse (IVA/VAT/sales tax), totale
- Metodo di pagamento e termini

### Numerazione Fatture

La numerazione deve essere sequenziale, senza buchi, e conforme alla legislazione locale.

```python
# Pseudocode: generazione numero fattura
class InvoiceNumberGenerator:
    """
    Pattern: {PREFIX}-{ANNO}-{SEQUENZA}
    Esempio: INV-2026-00142
    
    Requisiti:
    - Sequenza monotona crescente (no buchi)
    - Univoco per entità fiscale
    - Anno solare per reset opzionale (dipende dal paese)
    """
    def next_number(self, entity_id, year):
        # Atomic increment per evitare race condition
        sequence = db.atomic_increment(
            table="invoice_sequences",
            entity_id=entity_id,
            year=year,
        )
        return f"INV-{year}-{sequence:05d}"

    # ATTENZIONE: paesi diversi hanno regole diverse:
    # Italia: numerazione progressiva per anno solare, no buchi
    # UK: nessun formato obbligatorio, ma sequenziale consigliato
    # Germania: sequenziale senza buchi, qualsiasi formato
    # Francia: sequenziale cronologica, senza buchi
```

### Struttura della Fattura — Esempio

```
┌──────────────────────────────────────────────────────────────┐
│ FATTURA N° INV-2026-00142                                    │
│ Data emissione: 2026-01-15                                   │
│ Periodo: 2026-01-01 — 2026-01-31                             │
├──────────────────────────────────────────────────────────────┤
│ FORNITORE                    │ CLIENTE                        │
│ SaaS Corp S.r.l.             │ Acme GmbH                     │
│ Via Roma 1, 00100 Roma       │ Berliner Str. 10, 10115 Berlin│
│ P.IVA: IT12345678901         │ VAT: DE123456789              │
│ PEC: fatture@saascorp.it     │                               │
├──────────────────────────────┴───────────────────────────────┤
│ DETTAGLIO                                                    │
│ Descrizione              Qtà    Prezzo Unit.    Totale       │
│ Piano Professional       1      €199.00         €199.00      │
│ Add-on: Extra Storage    50 GB  €0.10/GB        €5.00        │
│ API Calls (over quota)   12.340 €0.001/call     €12.34       │
│──────────────────────────────────────────────────────────────│
│ Subtotale                                       €216.34      │
│ IVA 19% (DE)                                    €41.10       │
│ TOTALE                                          €257.44      │
│──────────────────────────────────────────────────────────────│
│ Pagamento: Carta **** 4242 (addebitato il 2026-01-15)        │
│ Termini: Pagamento alla conferma                             │
└──────────────────────────────────────────────────────────────┘
```

### Fatturazione Automatica

Per self-service (SMB): fattura automatica emessa al momento del pagamento. Stripe genera automaticamente le invoice.

Per enterprise: spesso Net 30/60 (pagamento 30-60 giorni dopo l'emissione). Richiede: PO (Purchase Order) dal cliente, fattura emessa manualmente o semi-automatica, tracking dei pagamenti in scadenza.

### Gestione Multi-Currency nelle Fatture

```python
# Pseudocode: fattura multi-currency
def generate_invoice(subscription, customer):
    # La valuta della fattura è quella del customer
    currency = customer.currency  # es. "EUR", "USD", "GBP"
    
    line_items = []
    for item in subscription.items:
        # Il prezzo deve essere definito nella valuta del customer
        price = get_price_in_currency(item.price_id, currency)
        if not price:
            # Fallback: conversione dal prezzo base (USD)
            base_price = get_base_price(item.price_id)
            price = convert_currency(base_price, "USD", currency,
                                     rate=get_fx_rate("USD", currency))
        line_items.append({
            "description": item.description,
            "quantity": item.quantity,
            "unit_price": price,
            "total": price * item.quantity,
            "currency": currency,
        })
    
    # Calcolo tasse nella stessa valuta
    tax = calculate_tax(line_items, customer)
    
    invoice = create_invoice(
        customer=customer,
        line_items=line_items,
        tax=tax,
        currency=currency,
        invoice_number=invoice_numbering.next_number(
            entity_id=get_fiscal_entity(currency),
            year=current_year(),
        ),
    )
    return invoice
```

### Crediti e Note di Credito

Quando emettere un credito:
- Downgrade mid-cycle (credito per la differenza)
- Disservizio coperto da SLA (credito per downtime)
- Errore di fatturazione
- Gesto commerciale per retention

Mai fare un rimborso diretto se possibile — il credito mantiene il cliente nell'ecosistema.

```python
# Pseudocode: emissione nota di credito
def issue_credit_note(invoice_id, reason, amount=None, lines=None):
    """
    amount: credito parziale in valore fisso.
    lines: credito su line item specifici.
    Se entrambi None, credito totale (storno completo).
    """
    invoice = billing.get_invoice(invoice_id)
    
    credit_note = billing.create_credit_note(
        invoice=invoice_id,
        reason=reason,  # "order_change", "product_unsatisfactory", etc.
        amount=amount,
        lines=lines,
        # La nota di credito deve avere un numero progressivo proprio
        metadata={
            "credit_note_number": credit_note_numbering.next_number(
                entity_id=invoice.fiscal_entity,
                year=current_year(),
            ),
        }
    )
    
    # Opzione 1: applicare come credito al prossimo ciclo
    billing.apply_credit_to_customer(
        customer=invoice.customer,
        amount=credit_note.amount,
    )
    
    # Opzione 2: rimborso diretto (meno preferibile)
    # billing.refund(invoice.payment_intent, amount=credit_note.amount)
    
    return credit_note
```

---

## Gestione Multi-Currency e FX

### Concetti Chiave

| Termine | Significato |
|---|---|
| **Presentment currency** | La valuta mostrata al cliente (es. EUR per un cliente italiano) |
| **Settlement currency** | La valuta in cui il SaaS riceve i fondi (es. USD se il conto è in USD) |
| **FX rate** | Tasso di cambio applicato alla conversione |
| **FX markup** | Commissione aggiuntiva sul tasso di cambio (Stripe: 1-2%) |

### Strategia Multi-Currency

Per SaaS internazionali: mostrare il prezzo nella valuta locale del cliente, addebitare nella valuta locale, gestire le conversioni. Stripe supporta 135+ valute. Attenzione: il tasso di cambio fluttua — decidere se assorbire il rischio o passarlo al cliente.

### Approcci alla Gestione FX

| Approccio | Come Funziona | Pro | Contro |
|---|---|---|---|
| **Prezzo fisso per valuta** | Definire prezzi espliciti: $99/€89/£79 | Nessun rischio FX, prezzo chiaro | Richiede aggiornamento manuale periodico |
| **Conversione dinamica** | Prezzo base USD, convertito al tasso corrente | Sempre allineato al mercato | Prezzo fluttua, cliente confuso |
| **Conversione con lock periodico** | Fissare il tasso mensilmente/trimestralmente | Stabilità per il cliente | Rischio FX contenuto |

**Raccomandazione per la maggior parte dei SaaS**: prezzo fisso per valuta per le 5-10 valute principali (USD, EUR, GBP, CAD, AUD, BRL, JPY), con revisione trimestrale. Per le valute minori, conversione dal prezzo USD.

```python
# Pseudocode: pricing multi-currency
FIXED_PRICES = {
    "plan_pro": {
        "USD": 9900,   # $99.00
        "EUR": 8900,   # €89.00
        "GBP": 7900,   # £79.00
        "BRL": 29900,  # R$299.00
        "JPY": 14800,  # ¥14,800
    }
}

def get_display_price(plan_id, currency):
    fixed = FIXED_PRICES.get(plan_id, {}).get(currency)
    if fixed:
        return {"amount": fixed, "currency": currency, "type": "fixed"}
    
    # Fallback: conversione da USD
    base_usd = FIXED_PRICES[plan_id]["USD"]
    rate = fx_service.get_rate("USD", currency)
    converted = round(base_usd * rate)
    return {"amount": converted, "currency": currency, "type": "converted"}
```

### Riconciliazione Multi-Currency

Quando il cliente paga in EUR e il SaaS riceve in USD:

```
Cliente paga: €89.00
Tasso Stripe: 1 EUR = 1.08 USD (tasso interbancario + 1% markup)
SaaS riceve: $96.12 (lordo)
Commissione Stripe: $96.12 × 2.9% + $0.30 = $3.09
SaaS netto: $93.03
```

La differenza tra il "prezzo in USD" ($99) e ciò che il SaaS riceve ($93.03) è il costo FX + commissioni. Tracciare questa differenza per ogni transazione.

---

## Billing Enterprise

### Differenze tra Billing Self-Service e Enterprise

| Aspetto | Self-Service (SMB) | Enterprise |
|---|---|---|
| Checkout | Self-service online | Sales-assisted |
| Pagamento | Carta di credito | Bonifico, ACH, Net-30/60/90 |
| Contratto | ToS online (click-through) | MSA + Order Form firmati |
| Fatturazione | Automatica al rinnovo | Manuale o semi-auto, con PO |
| Prezzo | Listino pubblico | Negoziato, volume discount |
| Ciclo | Mensile o annuale | Annuale o multi-anno |
| Supporto billing | Self-service portal | Account manager dedicato |

### Workflow PO (Purchase Order)

```
1. Trattativa commerciale → Prezzo negoziato
2. Il cliente emette un Purchase Order (PO)
   - Contiene: PO number, importo approvato, termini, contatto billing
3. Il SaaS emette la fattura con il PO number
4. Il cliente processa la fattura internamente (AP = Accounts Payable)
5. Pagamento entro i termini (Net-30/60/90)
6. Riconciliazione del pagamento con la fattura

ATTENZIONE: molte enterprise non pagano senza PO number in fattura.
Senza PO → fattura rifiutata → ritardo di settimane/mesi.
```

```python
# Pseudocode: gestione contratti enterprise
class EnterpriseContract:
    def __init__(self, customer_id, terms):
        self.customer_id = customer_id
        self.po_number = terms.get("po_number")
        self.payment_terms = terms.get("net_days", 30)  # Net-30, 60, 90
        self.contract_value = terms.get("annual_value")
        self.start_date = terms.get("start_date")
        self.end_date = terms.get("end_date")
        self.auto_renew = terms.get("auto_renew", True)

    def generate_invoice(self):
        """Genera fattura enterprise con PO e termini custom."""
        due_date = today() + timedelta(days=self.payment_terms)
        
        invoice = billing.create_invoice(
            customer=self.customer_id,
            collection_method="send_invoice",  # Non addebitare carta
            days_until_due=self.payment_terms,
            custom_fields=[
                {"name": "PO Number", "value": self.po_number},
                {"name": "Contract ID", "value": self.contract_id},
            ],
            metadata={
                "contract_type": "enterprise",
                "net_days": self.payment_terms,
            }
        )
        
        # Inviare al contatto billing del cliente
        billing.send_invoice(invoice.id)
        
        # Schedulare reminder prima della scadenza
        scheduler.schedule("invoice_reminder",
            execute_at=due_date - timedelta(days=7),
            data={"invoice_id": invoice.id},
        )
        return invoice

    def check_overdue(self):
        """Controlla fatture scadute per questo contratto."""
        overdue = billing.list_invoices(
            customer=self.customer_id,
            status="open",
            due_date_lt=today(),
        )
        if overdue:
            # Escalation: notifica account manager
            notify_account_manager(self.customer_id, overdue)
            # Late payment fee (se previsto nel contratto)
            if self.contract_terms.get("late_fee_pct"):
                for inv in overdue:
                    days_late = (today() - inv.due_date).days
                    fee = inv.amount * self.contract_terms["late_fee_pct"] / 100
                    apply_late_fee(inv, fee, days_late)
```

### Termini di Pagamento Enterprise

| Termine | Significato | Quando Usarlo |
|---|---|---|
| **Net-30** | Pagamento entro 30 giorni dalla fattura | Standard enterprise |
| **Net-60** | Pagamento entro 60 giorni | Enterprise grandi, settore pubblico |
| **Net-90** | Pagamento entro 90 giorni | Grandi corporazioni, governo |
| **Due on receipt** | Pagamento immediato alla ricezione | SMB enterprise |
| **Quarterly invoicing** | Fattura trimestrale per contratti annuali | Semplifica l'AP del cliente |

### Contratti Multi-Anno

```python
# Pseudocode: contratto multi-anno con scaglioni
def create_multi_year_contract(customer_id, years=3, base_price=50000):
    """
    Contratto di 3 anni con prezzo crescente:
    Anno 1: $50,000
    Anno 2: $52,500 (+5%)
    Anno 3: $55,125 (+5%)
    """
    phases = []
    current_price = base_price
    for year in range(years):
        phases.append({
            "start_date": contract_start + timedelta(days=365 * year),
            "end_date": contract_start + timedelta(days=365 * (year + 1)),
            "price": current_price,
            "invoicing": "annual_upfront",  # o "quarterly"
        })
        current_price = round(current_price * 1.05)  # +5% annuo
    
    contract = create_contract(
        customer=customer_id,
        phases=phases,
        auto_renew=True,
        renewal_notice_days=90,  # Notifica 90 giorni prima della scadenza
        cancellation_notice_days=60,
    )
    return contract
```

---

## Payment Processing

### Metodi di Pagamento per SaaS

**Carta di credito/debito**: standard per self-service. Commissione: 2.9% + $0.30 per transazione (Stripe). Volume alto = negoziazione possibile (2.2-2.5%).

**ACH/SEPA (bonifico diretto)**: commissione più bassa (0.8% con cap $5). Ideale per piani annual enterprise. Tempo di settlement: 3-5 giorni. Rischio: chargeback/dispute.

**Wire transfer (bonifico bancario)**: per contratti enterprise > $50K. Nessuna commissione per il SaaS. Processo manuale, reconciliation necessaria.

**PayPal**: opzionale, richiesto da alcuni mercati (Germania, Australia). Commissione: 2.9% + $0.30.

### Flusso di un Pagamento con Carta

```
1. Cliente inserisce i dati carta (Stripe Elements / iframe)
2. Stripe.js crea un PaymentMethod (token) → inviato al backend
3. Backend crea PaymentIntent con il PaymentMethod
4. Stripe invia la richiesta all'Acquirer (es. Worldpay, Adyen)
5. Acquirer la inoltra al Card Network (Visa, Mastercard)
6. Card Network la inoltra all'Issuing Bank (banca del cliente)
7. Issuing Bank approva o rifiuta
8. Risposta torna indietro: Network → Acquirer → Stripe → SaaS
9. Se approvato: pagamento confermato, webhook inviato
10. Se rifiutato: codice di errore specifico restituito

Tempo totale: 1-5 secondi (senza 3DS)
Con 3DS: +10-30 secondi per l'autenticazione
```

### 3D Secure (3DS / SCA)

La Strong Customer Authentication (SCA) è obbligatoria in Europa (PSD2). 3D Secure è il meccanismo standard.

| Aspetto | 3DS 1.0 | 3DS 2.0 |
|---|---|---|
| UX | Redirect a pagina della banca | Challenge in-app / iframe |
| Friction | Alta (password) | Bassa (biometrico, OTP) |
| Frictionless flow | No | Sì (se la banca approva senza challenge) |
| Conversion impact | -10-20% | -2-5% |

**Strategia raccomandata**: usare Adaptive 3DS (Stripe lo fa di default). 3DS viene richiesto solo quando necessario (Europa) o quando riduce il rischio di dispute.

### Gestione dei Decline Codes

| Codice | Significato | Azione |
|---|---|---|
| `card_declined` | Rifiuto generico | Chiedere altra carta o contattare la banca |
| `insufficient_funds` | Fondi insufficienti | Retry tra 3-5 giorni |
| `expired_card` | Carta scaduta | Aggiornare i dati carta |
| `incorrect_cvc` | CVC errato | Richiedere input corretto |
| `processing_error` | Errore temporaneo del processor | Retry immediato |
| `do_not_honor` | Rifiuto dalla banca senza dettaglio | Contattare la banca |
| `fraudulent` | Sospetta frode | Non riprovare, segnalare |
| `stolen_card` | Carta rubata | Non riprovare, bloccare |

### PCI Compliance

Se si processano pagamenti con carta, la PCI-DSS compliance è obbligatoria.

**Approccio consigliato**: non toccare mai i dati della carta. Usare Stripe Elements / Checkout — i dati della carta vanno direttamente a Stripe, il server SaaS non li vede mai. Questo riduce il livello PCI a SAQ-A (il più semplice).

### Gestione Chargeback e Dispute

```python
# Pseudocode: gestione dispute
def handle_dispute(dispute_event):
    """Webhook handler per dispute/chargeback."""
    dispute = dispute_event.data
    invoice = billing.get_invoice(dispute.payment_intent)
    customer = billing.get_customer(invoice.customer)

    # 1. Raccogliere evidenze automaticamente
    evidence = {
        "customer_email_address": customer.email,
        "billing_address": customer.address,
        # Log di accesso: prova che il servizio è stato usato
        "access_log": get_access_log(
            customer.id,
            dispute.created - timedelta(days=30),
            dispute.created,
        ),
        # Comunicazioni: email inviate al cliente
        "customer_communication": get_email_history(customer.email),
        # ToS accettato
        "service_documentation_url": "https://saas.com/terms",
    }

    # 2. Sottomettere le evidenze
    billing.submit_dispute_evidence(dispute.id, evidence)

    # 3. Tracciare
    analytics.track("dispute_received", {
        "customer_id": customer.id,
        "amount": dispute.amount,
        "reason": dispute.reason,
        "invoice": invoice.id,
    })

    # 4. Alert al team
    notify_team("billing-disputes", {
        "customer": customer.email,
        "amount": format_currency(dispute.amount, dispute.currency),
        "reason": dispute.reason,
        "deadline": dispute.evidence_due_by,
    })
```

---

## Revenue Recognition

### ASC 606 / IFRS 15

Per SaaS con revenue significativo, il riconoscimento del ricavo segue standard contabili specifici:

**Principio**: il ricavo si riconosce quando il servizio viene erogato, non quando il pagamento è ricevuto.

**Implicazione per annual billing**: se un cliente paga $12.000 per un anno, il ricavo non è $12.000 nel mese di pagamento. È $1.000/mese per 12 mesi. I $11.000 restanti sono **deferred revenue** (debito in bilancio).

```
Esempio:
  Cliente paga $12.000 il 1 gennaio per piano annuale.

  Gennaio:   Ricavo riconosciuto: $1.000 | Deferred: $11.000
  Febbraio:  Ricavo riconosciuto: $1.000 | Deferred: $10.000
  ...
  Dicembre:  Ricavo riconosciuto: $1.000 | Deferred: $0
```

Per SaaS early-stage (< $5M ARR): spesso si usa cash-basis accounting (più semplice). Oltre i $5M ARR o per fundraising/IPO: ASC 606 diventa necessario.

### ASC 606 — Il Modello a 5 Step

Lo standard ASC 606 (Revenue from Contracts with Customers) definisce 5 step obbligatori:

| Step | Descrizione | Applicazione SaaS |
|---|---|---|
| **1. Identificare il contratto** | Accordo con diritti e obblighi esercibili | Sottoscrizione accettata (click-through ToS o MSA firmato) |
| **2. Identificare le performance obligation** | Promesse distinte al cliente | Accesso al software, supporto, onboarding, storage |
| **3. Determinare il transaction price** | Importo che l'entità si aspetta di ricevere | Prezzo del piano (inclusi sconti, crediti, variabili) |
| **4. Allocare il prezzo alle obligation** | Distribuire il prezzo tra le obligation | Se piano + onboarding: allocare proporzionalmente |
| **5. Riconoscere il ricavo** | Quando (o nel tempo in cui) l'obligation è soddisfatta | SaaS: ricavo riconosciuto rateo nel periodo di servizio |

### Scenari Comuni di Revenue Recognition

**Scenario 1 — Subscription pura (semplice)**

```
Contratto: piano Pro $1.200/anno, pagato upfront il 1 gennaio.
Performance obligation: accesso al software per 12 mesi.
Recognition: $100/mese per 12 mesi (rateo lineare).

Journal entries:
  1 Gen:  Debit Cash $1.200  |  Credit Deferred Revenue $1.200
  31 Gen: Debit Deferred Revenue $100  |  Credit Revenue $100
  28 Feb: Debit Deferred Revenue $100  |  Credit Revenue $100
  ... (ogni mese)
```

**Scenario 2 — Subscription + Setup fee**

```
Contratto: piano Enterprise $60.000/anno + setup fee $12.000.
Performance obligations:
  1. Setup/Onboarding (servizio distinto, completato in 1 mese)
  2. Accesso al software (12 mesi)

Allocazione (stand-alone selling price):
  Setup: $12.000 (riconosciuto alla completion dell'onboarding)
  Software: $60.000 ($5.000/mese per 12 mesi)

Journal entries:
  1 Gen:  Debit Cash $72.000  |  Credit Deferred Revenue $72.000
  31 Gen: Debit Deferred Revenue $17.000  |  Credit Revenue $17.000
          ($12.000 setup completato + $5.000 primo mese software)
  28 Feb: Debit Deferred Revenue $5.000  |  Credit Revenue $5.000
  ... (ogni mese)
```

**Scenario 3 — Usage-based (variabile)**

```
Contratto: $0.01/API call, fatturato mensilmente a consuntivo.
Il ricavo si riconosce nel mese in cui l'usage avviene.
Nessun deferred revenue (pagamento è post-consumo).

Gennaio: 500.000 API call → Revenue $5.000 (riconosciuto a gennaio)
Febbraio: 750.000 API call → Revenue $7.500 (riconosciuto a febbraio)
```

**Scenario 4 — Prepaid credits**

```
Cliente compra $10.000 di crediti il 1 gennaio.
I crediti scadono dopo 12 mesi.

1 Gen: Debit Cash $10.000  |  Credit Deferred Revenue $10.000

Ogni utilizzo: Debit Deferred Revenue X  |  Credit Revenue X

Se crediti scadono non usati (breakage):
  Riconoscere gradualmente se il pattern di consumo è prevedibile,
  o alla scadenza se non prevedibile.
```

### Deferred Revenue vs Prepaid

| Termine | Significato | Dove in Bilancio |
|---|---|---|
| **Deferred Revenue** | Pagamento ricevuto per servizio non ancora erogato | Passivo (debito verso il cliente) |
| **Accrued Revenue** | Servizio erogato ma non ancora fatturato | Attivo (credito verso il cliente) |
| **Prepaid Expense** | Pagamento anticipato per un servizio futuro (dal punto di vista del cliente) | Attivo del cliente |
| **Contract Liability** | Termine ASC 606 per deferred revenue | Passivo |
| **Contract Asset** | Termine ASC 606 per accrued revenue | Attivo |

### Tool per Revenue Recognition

| Tool | Per Chi | Costo Indicativo |
|---|---|---|
| Stripe Revenue Recognition | SaaS su Stripe | $10/fattura/mese |
| Maxio (ex SaaSOptics + Chargify) | SaaS growth/enterprise | $5.000-20.000/anno |
| ChartMogul | Metriche + rev rec base | $100-1.000/mese |
| Sage Intacct | Enterprise, audit-ready | $15.000+/anno |
| NetSuite | Enterprise complesso | $25.000+/anno |

---

## Tassazione Internazionale

### IVA / VAT (Europa)

Per vendite B2C in UE: applicare l'IVA del paese del cliente (aliquote 17-27%). Registrarsi per il VAT-OSS (One-Stop Shop) per semplificare: un'unica dichiarazione per tutti i paesi UE.

Per vendite B2B in UE: reverse charge (IVA a carico del cliente, se ha VAT ID valido). Validare il VAT ID tramite il sistema VIES.

### EU VAT — Dettaglio Operativo

#### Aliquote IVA per Paese (Servizi Digitali, 2025)

| Paese | Aliquota Standard | Note |
|---|---|---|
| Austria | 20% | |
| Belgio | 21% | |
| Bulgaria | 20% | |
| Croazia | 25% | |
| Cipro | 19% | |
| Rep. Ceca | 21% | |
| Danimarca | 25% | |
| Estonia | 22% | Aumentata da 20% nel 2024 |
| Finlandia | 25.5% | Aumentata da 24% nel 2024 |
| Francia | 20% | |
| Germania | 19% | |
| Grecia | 24% | |
| Ungheria | 27% | Più alta nell'UE |
| Irlanda | 23% | |
| Italia | 22% | |
| Lettonia | 21% | |
| Lituania | 21% | |
| Lussemburgo | 17% | Più bassa nell'UE |
| Malta | 18% | |
| Paesi Bassi | 21% | |
| Polonia | 23% | |
| Portogallo | 23% | |
| Romania | 19% | |
| Slovacchia | 23% | |
| Slovenia | 22% | |
| Spagna | 21% | |
| Svezia | 25% | |

#### VAT-OSS (One-Stop Shop)

Il VAT-OSS (ex VAT-MOSS) semplifica la compliance IVA per vendite B2C digitali intra-UE:

```
SENZA OSS:
  - Registrarsi per VAT in ogni paese UE dove si vende
  - Presentare dichiarazione IVA in ogni paese
  - Fino a 27 registrazioni + 27 dichiarazioni trimestrali

CON OSS:
  - Registrarsi per OSS nel proprio paese UE di stabilimento
  - Una sola dichiarazione trimestrale che copre tutti i paesi UE
  - Un solo pagamento all'autorità fiscale del proprio paese
  - L'autorità redistribuisce ai paesi destinatari
```

**Soglia OSS**: dal 1° luglio 2021, la soglia unificata è €10.000/anno di vendite B2C cross-border in UE. Sotto questa soglia, si applica l'IVA del proprio paese. Sopra, si applica l'IVA del paese del cliente (e serve OSS o registrazione locale).

#### Reverse Charge Mechanism (B2B)

```python
# Pseudocode: logica reverse charge
def calculate_vat(customer, seller, amount):
    """
    Reverse charge: l'IVA non viene addebitata dal venditore,
    ma auto-liquidata dal cliente (B2B intra-UE).
    """
    # 1. Il cliente ha un VAT ID valido?
    if customer.vat_id:
        is_valid = vies_service.validate(customer.vat_id)
        if not is_valid:
            # VAT ID non valido → trattare come B2C
            return calculate_b2c_vat(customer, amount)
        
        # 2. È una vendita intra-UE? (venditore e cliente in paesi UE diversi)
        if (seller.country in EU_COUNTRIES 
            and customer.country in EU_COUNTRIES
            and seller.country != customer.country):
            # Reverse charge: IVA = 0, ma annotazione in fattura
            return {
                "vat_amount": 0,
                "vat_rate": 0,
                "mechanism": "reverse_charge",
                "note": "Inversione contabile art. 196 Direttiva 2006/112/CE",
            }
        
        # 3. Stesso paese → IVA locale normale
        if seller.country == customer.country:
            rate = get_vat_rate(seller.country)
            return {
                "vat_amount": amount * rate,
                "vat_rate": rate,
                "mechanism": "standard",
            }
    
    # 4. Nessun VAT ID → B2C, IVA del paese del cliente
    return calculate_b2c_vat(customer, amount)

def validate_vat_id(vat_id):
    """Validazione tramite VIES (VAT Information Exchange System)."""
    # Formato: codice paese (2 lettere) + numero
    # Esempio: IT12345678901, DE123456789, FR12345678901
    country_code = vat_id[:2]
    number = vat_id[2:]
    
    result = vies_api.check_vat(country_code, number)
    return {
        "valid": result.valid,
        "name": result.name,        # Ragione sociale registrata
        "address": result.address,   # Indirizzo registrato
    }
```

### Sales Tax (USA)

Ogni stato ha regole diverse. Nexus (obbligo di raccogliere la tax) scatta quando: hai presenza fisica nello stato, superi una soglia di vendita ($100K o 200 transazioni in molti stati — regola post-Wayfair).

#### Economic Nexus Post-Wayfair — Dettaglio

La decisione South Dakota v. Wayfair (2018) della Corte Suprema USA ha stabilito che il nexus economico è sufficiente (non serve presenza fisica):

| Stato | Soglia Revenue | Soglia Transazioni | SaaS Tassato? |
|---|---|---|---|
| California | $500K | N/A | Sì (dal 2024) |
| Texas | $500K | N/A | Sì (data processing) |
| New York | $500K | 100 | Sì |
| Florida | $100K | N/A | No (SaaS esente) |
| Washington | $100K | N/A | Sì |
| Pennsylvania | $100K | N/A | Sì |
| Illinois | $100K | 200 | Sì |
| Massachusetts | $100K | N/A | Sì |
| Ohio | $100K | 200 | Sì (dal 2024) |
| Georgia | $100K | 200 | No (SaaS esente) |

**Nota critica**: non tutti gli stati tassano il SaaS. Circa 20 stati considerano il SaaS un servizio (non tassato), gli altri lo considerano un bene tangibile (tassato). Le regole cambiano frequentemente.

Tool: Stripe Tax, Avalara, TaxJar per calcolo e compliance automatica.

### Merchant of Record (MoR)

Un MoR (Paddle, LemonSqueezy, FastSpring) agisce come rivenditore: il cliente paga il MoR, il MoR paga il SaaS. Il MoR gestisce IVA, sales tax, fatturazione locale. Il SaaS riceve il netto. Commissione: 5-10% del revenue. **Ideale per SaaS < $5M ARR che vendono globalmente** — elimina la complessità fiscale.

### MoR vs Self-Managed — Decision Matrix

| Criterio | MoR (Paddle) | Self-Managed (Stripe + Tax Engine) |
|---|---|---|
| Complessità di setup | Bassa (1-2 settimane) | Media-Alta (2-6 settimane) |
| Costo per $1M ARR | ~$50K-100K (5-10%) | ~$30K-40K (2.9% + tax tool) |
| Controllo sulla checkout UX | Limitato | Totale |
| Gestione tasse | Inclusa (il MoR è il rivenditore) | Tu sei responsabile |
| Fatturazione locale | Inclusa | Da implementare |
| Chargeback/dispute | MoR li gestisce | Tu li gestisci |
| Revenue recognition | Più semplice (un solo fornitore) | Più complesso |
| Dati del cliente | Limitati (il cliente è del MoR) | Pieni |
| Branding | Limitato (il checkout è del MoR) | Pieno |
| Scalabilità > $10M | Commissione pesa troppo | Più conveniente |

---

## Dunning e Recupero Pagamenti

Il 20-40% del churn è involuntario (pagamento fallito). Un buon dunning management può recuperare il 50-70% di questi pagamenti.

### Sequenza di Dunning

```
Giorno 0: Pagamento fallito
  → Retry automatico immediato (diverso orario/giorno)
  → Email: "Aggiorna il metodo di pagamento" (tono neutro)

Giorno 3: Secondo retry
  → Email: "Il pagamento non è andato a buon fine" + link per aggiornare

Giorno 7: Terzo retry
  → Email: "Rischio sospensione account" (urgenza)
  → In-app banner: "Azione richiesta: aggiorna il pagamento"

Giorno 14: Ultimo tentativo
  → Email: "Ultimo avviso prima della sospensione"
  → SMS (se disponibile)

Giorno 21: Account sospeso (non cancellato)
  → L'utente può riattivare aggiornando il pagamento
  → Dati preservati per 90 giorni

Giorno 90: Cancellazione definitiva
  → Dati eliminati (nel rispetto del GDPR)
```

### Smart Retry

Non fare retry fisso ogni 3 giorni. Retry intelligente:
- Riprovare in giorni diversi della settimana (il lunedì va meglio del venerdì)
- Riprovare a orari diversi (le banche hanno window di approvazione)
- Riprovare il 1° del mese (stipendio accreditato)
- Stripe Smart Retries usa ML per ottimizzare il timing

### Pre-Dunning

Prevenire il pagamento fallito:
- Notificare 30 giorni prima della scadenza della carta
- In-app prompt per aggiornare la carta
- Supportare card updater (Stripe aggiorna automaticamente le carte rinnovate)

### Dunning Email — Template e Tono

| Email | Giorno | Tono | Oggetto Esempio |
|---|---|---|---|
| 1 | 0 | Neutro, informativo | "Azione necessaria: aggiorna il pagamento per [Prodotto]" |
| 2 | 3 | Amichevole, supportivo | "Il tuo pagamento non è andato a buon fine — possiamo aiutarti" |
| 3 | 7 | Urgente, chiaro | "Il tuo account [Prodotto] rischia la sospensione" |
| 4 | 14 | Finale, diretto | "Ultimo avviso: il tuo account verrà sospeso tra 7 giorni" |
| 5 | 21 | Post-sospensione | "Il tuo account è stato sospeso — riattivalo in 2 minuti" |

### Metriche di Dunning

| Metrica | Formula | Target |
|---|---|---|
| Recovery rate | Pagamenti recuperati / Pagamenti falliti | > 60% |
| Involuntary churn rate | Cancellazioni per pagamento / Totale clienti | < 2%/mese |
| Time to recovery | Tempo medio dal primo fallimento al pagamento riuscito | < 7 giorni |
| Email open rate (dunning) | Email aperte / Email inviate | > 40% |
| Card update rate | Carte aggiornate dopo prompt / Carte scadute | > 30% |

### Implementazione Dunning Avanzata

```python
# Pseudocode: dunning engine configurabile
class DunningEngine:
    def __init__(self, config):
        self.retry_schedule = config.retry_schedule  
        # Es: [0, 3, 7, 14, 21]
        self.channels = config.channels
        # Es: ["email", "in_app", "sms"]
        
    def handle_payment_failure(self, subscription_id, failure_info):
        attempt = get_dunning_attempt_count(subscription_id)
        
        if attempt >= len(self.retry_schedule):
            # Tutti i retry esauriti
            self.suspend_subscription(subscription_id)
            return
        
        next_retry_day = self.retry_schedule[attempt]
        
        # Smart retry: scegliere il momento migliore
        retry_time = self.optimal_retry_time(
            failure_info.decline_code,
            subscription_id,
        )
        
        # Schedulare il retry
        scheduler.schedule("payment_retry",
            execute_at=retry_time,
            data={
                "subscription_id": subscription_id,
                "attempt": attempt + 1,
            },
        )
        
        # Comunicazione basata sull'urgenza
        urgency = self.get_urgency_level(attempt)
        self.send_dunning_communication(
            subscription_id, urgency, failure_info
        )

    def optimal_retry_time(self, decline_code, subscription_id):
        """Logica di retry intelligente."""
        if decline_code == "insufficient_funds":
            # Riprovare il 1° del mese o il prossimo lunedì
            next_first = next_month_first_day()
            next_monday = next_weekday(0)  # Lunedì
            return min(next_first, next_monday)
        
        elif decline_code == "processing_error":
            # Errore temporaneo: riprovare tra 4-6 ore
            return now() + timedelta(hours=random.randint(4, 6))
        
        else:
            # Default: riprovare tra 3 giorni, alle 10:00 locale
            customer_tz = get_customer_timezone(subscription_id)
            return (now() + timedelta(days=3)).replace(
                hour=10, minute=0, tzinfo=customer_tz
            )
```

---

## Webhook Integration Patterns

### Architettura Webhook per Billing

I webhook sono il meccanismo primario per reagire a eventi di billing in real-time. Il billing provider (Stripe, Paddle, etc.) invia HTTP POST al server SaaS ogni volta che avviene un evento rilevante.

### Eventi Critici da Gestire

| Evento | Azione Necessaria |
|---|---|
| `invoice.payment_succeeded` | Confermare entitlement, aggiornare status subscription |
| `invoice.payment_failed` | Iniziare dunning sequence |
| `customer.subscription.created` | Provisioning iniziale, welcome email |
| `customer.subscription.updated` | Aggiornare entitlement (upgrade/downgrade) |
| `customer.subscription.deleted` | Revocare accesso, retention workflow |
| `customer.subscription.trial_will_end` | Reminder email 3 giorni prima |
| `charge.dispute.created` | Alert team, raccogliere evidenze |
| `charge.refunded` | Aggiornare contabilità, notificare il cliente |
| `payment_method.attached` | Aggiornare card-on-file, pre-dunning reset |
| `invoice.upcoming` | Preview della prossima fattura al cliente |

### Pattern di Implementazione

```python
# Pseudocode: webhook handler robusto

# 1. VERIFICA DELLA FIRMA
def verify_webhook_signature(payload, signature, secret):
    """
    CRITICO: verificare SEMPRE la firma del webhook.
    Senza verifica, chiunque può inviare eventi fake.
    """
    expected = hmac_sha256(secret, payload)
    if not constant_time_compare(signature, expected):
        raise WebhookSignatureError("Firma webhook non valida")

# 2. HANDLER PRINCIPALE
def handle_webhook(request):
    # Verificare la firma
    verify_webhook_signature(
        payload=request.body,
        signature=request.headers["Stripe-Signature"],
        secret=WEBHOOK_SIGNING_SECRET,
    )
    
    event = parse_event(request.body)
    
    # Idempotency: verificare se l'evento è già stato processato
    if event_store.exists(event.id):
        return Response(200)  # Già gestito, rispondere OK
    
    # Processare l'evento
    try:
        handler = EVENT_HANDLERS.get(event.type)
        if handler:
            handler(event)
        else:
            log.info(f"Evento non gestito: {event.type}")
        
        # Marcare come processato
        event_store.save(event.id, processed_at=utc_now())
        
    except TemporaryError as e:
        # Errore temporaneo: rispondere 500, il provider riproverà
        log.warning(f"Errore temporaneo webhook: {e}")
        return Response(500)
    
    except PermanentError as e:
        # Errore permanente: loggare, rispondere 200 per non riprovare
        log.error(f"Errore permanente webhook: {e}")
        event_store.save(event.id, error=str(e))
        return Response(200)
    
    return Response(200)

# 3. HANDLER SPECIFICI
EVENT_HANDLERS = {
    "invoice.payment_succeeded": handle_payment_success,
    "invoice.payment_failed": handle_payment_failure,
    "customer.subscription.updated": handle_subscription_update,
    "customer.subscription.deleted": handle_subscription_cancel,
    "customer.subscription.trial_will_end": handle_trial_ending,
    "charge.dispute.created": handle_dispute,
}

def handle_payment_success(event):
    invoice = event.data.object
    subscription_id = invoice.subscription
    
    # Aggiornare lo status della subscription
    db.update_subscription(subscription_id, status="active")
    
    # Confermare gli entitlement
    entitlement_service.confirm(subscription_id)
    
    # Aggiornare la contabilità
    accounting.record_payment(
        invoice_id=invoice.id,
        amount=invoice.amount_paid,
        currency=invoice.currency,
        paid_at=utc_now(),
    )

def handle_subscription_update(event):
    subscription = event.data.object
    previous = event.data.previous_attributes
    
    # Cambiamento di piano?
    if "items" in previous:
        old_plan = previous["items"]["data"][0]["price"]["id"]
        new_plan = subscription.items.data[0].price.id
        
        # Aggiornare entitlement
        entitlement_service.update(
            subscription.customer, new_plan
        )
        
        analytics.track("plan_changed_via_webhook", {
            "old_plan": old_plan,
            "new_plan": new_plan,
        })
```

### Resilienza dei Webhook

| Problema | Soluzione |
|---|---|
| Webhook duplicato | Idempotency key (event.id) in un database |
| Webhook out-of-order | Controllare il timestamp, usare lo stato corrente dal provider |
| Server down | Il provider riprova (Stripe: fino a 3 giorni, backoff esponenziale) |
| Handler lento (> 30s) | Processare in async (queue), rispondere 200 subito |
| Firma non verificata | Rifiutare sempre (rispondere 400) |
| Event type sconosciuto | Loggare e rispondere 200 (non 500, altrimenti riprova) |

### Retry Policy dei Provider

| Provider | Retry | Intervallo | Timeout |
|---|---|---|---|
| Stripe | Fino a 3 giorni | Backoff esponenziale | Ogni ora per 3 giorni |
| Paddle | 24 ore | Ogni 30 minuti | 5 secondi per richiesta |
| Chargebee | 48 ore | Backoff esponenziale | 15 secondi per richiesta |
| Recurly | 24 ore | Ogni 1 ora | 45 secondi per richiesta |

---

## Best Practices

1. **Stripe come default**: a meno di esigenze molto specifiche, Stripe Billing è la scelta migliore per rapporto qualità/complessità/costo
2. **Non costruire il billing in-house**: il billing è un problema risolto. L'engineering time è meglio speso sul prodotto core
3. **Annuale con sconto**: offrire sempre l'opzione annuale con sconto 15-20%. Migliora cash flow e riduce churn
4. **Dunning automatizzato**: non lasciare che i pagamenti falliti diventino churn. Smart retry + email sequence + in-app banner
5. **Pre-dunning**: notificare carta in scadenza 30 giorni prima. Card updater automatico
6. **MoR per semplificare le tasse**: se vendi in < 10 paesi e hai < $5M ARR, un Merchant of Record come Paddle elimina la complessità fiscale
7. **Deferred revenue tracking**: anche se non obbligatorio, tracciare il deferred revenue fin dall'inizio. Sarà necessario per fundraising e audit
8. **Checkout semplice**: meno campi, più conversione. Carta + PayPal + ACH copre il 95% dei casi
9. **Idempotency nei webhook**: ogni webhook handler deve essere idempotente. Lo stesso evento può arrivare più volte
10. **Audit trail**: loggare ogni operazione di billing (creazione, modifica, cancellazione, pagamento, rimborso) con timestamp UTC
11. **Separare entitlement da billing**: il check "il cliente può usare questa feature?" deve essere veloce (cache), non dipendere dal billing provider in real-time
12. **Test del billing in sandbox**: ogni billing provider ha un ambiente sandbox/test. Testare ogni flusso (pagamento, fallimento, dunning, upgrade, downgrade) prima del go-live
13. **Multi-currency con prezzi fissi**: non affidarsi alla conversione dinamica. Definire prezzi fissi per le valute principali
14. **PCI scope minimo**: usare Stripe Elements o Checkout. Non toccare mai i dati carta. SAQ-A o SAQ-A-EP
15. **Revenue recognition early**: iniziare a tracciare il deferred revenue anche se non legalmente obbligatorio. Ogni investor e auditor lo chiederà

---

## Troubleshooting

### 1. "Tasso di decline delle carte alto (> 10%)"

**Cause**: carte scadute, 3D Secure non ottimizzato, network token non attivi.
**Soluzioni**:
- Attivare card updater automatico (Stripe lo fa di default se abilitato).
- Usare Adaptive 3DS (non forzare 3DS su ogni transazione).
- Attivare network tokens (Stripe li supporta, migliorano l'approval rate del 2-5%).
- Verificare con Stripe Radar le cause specifiche di decline (insufficient_funds vs. do_not_honor).
- Attivare Stripe Smart Retries.

### 2. "Clienti enterprise richiedono fatturazione Net 30/60"

**Soluzioni**:
- Non usare il billing self-service per enterprise.
- Implementare: invoice manuale o semi-automatica, integrazione con il CRM per PO tracking, reminder automatici per pagamenti in scadenza, late payment fee nel contratto.
- Usare `collection_method: "send_invoice"` in Stripe con `days_until_due: 30`.

### 3. "Complessità fiscale insostenibile"

**Soluzioni**:
- Opzione 1: Stripe Tax (automatico per i paesi supportati, +0.5%/transazione).
- Opzione 2: MoR (Paddle, LemonSqueezy) — gestiscono tutto, ma commissione 5-10%.
- Opzione 3: consulente fiscale specializzato in digital services.
- Per USA: monitorare il nexus con TaxJar o Avalara che tracciano le soglie.

### 4. "Revenue recognition è un incubo"

**Soluzioni**:
- Per early-stage (< $5M ARR): cash basis è sufficiente.
- Per growth-stage: tool come Stripe Revenue Recognition, Maxio, o ChartMogul gestiscono ASC 606 automaticamente.
- Non provare a farlo in un foglio Excel.

### 5. "Proration genera fatture confuse per il cliente"

**Cause**: multipli upgrade/downgrade nello stesso ciclo creano molte proration line items.
**Soluzioni**:
- Limitare i cambi piano a 1 per ciclo (il secondo cambio si applica al prossimo rinnovo).
- Mostrare un preview della proration prima della conferma.
- Aggiungere una riga di spiegazione nella fattura ("Credito per piano precedente", "Addebito pro-rata piano nuovo").

### 6. "I webhook arrivano in ordine sbagliato"

**Cause**: Stripe non garantisce l'ordine dei webhook. Un `invoice.payment_succeeded` può arrivare prima di `customer.subscription.created`.
**Soluzioni**:
- Non dipendere dall'ordine: ogni handler deve essere auto-sufficiente.
- Usare `event.data.object` per leggere lo stato corrente.
- Se serve lo stato precedente, usare `event.data.previous_attributes`.
- In caso di dubbio, fare un API call per leggere lo stato aggiornato dal provider.

### 7. "Il cliente ha cambiato carta ma il pagamento fallisce ancora"

**Cause**: la nuova carta è stata aggiunta ma non impostata come default per la subscription.
**Soluzioni**:
- Usare `invoice_settings.default_payment_method` sul Customer (non solo `default_source`).
- Aggiornare il payment method sulla subscription specifica, non solo sul customer.
- Dopo l'aggiornamento, ritentare immediatamente il pagamento pending.

### 8. "Discrepanza tra MRR calcolato e revenue effettivo"

**Cause**: MRR include abbonamenti in trial, crediti non dedotti, o currency conversion errata.
**Soluzioni**:
- Escludere i trial senza carta dal calcolo MRR.
- Normalizzare tutti gli importi in una singola valuta di reporting.
- Dedurre i crediti attivi dal MRR.
- Riconciliare mensilmente con il report del billing provider.

### 9. "Il checkout ha un conversion rate basso (< 3%)"

**Cause**: troppi campi, 3DS friction, pricing non chiaro, mancanza di metodi di pagamento locali.
**Soluzioni**:
- Ridurre i campi al minimo (email + carta, tutto il resto opzionale o derivato).
- Usare Stripe Checkout (ottimizzato per conversione) o Stripe Payment Links.
- Mostrare il prezzo nella valuta locale.
- Aggiungere metodi locali (iDEAL in NL, Bancontact in BE, SEPA in DACH).
- Testare Adaptive 3DS (non forzare su ogni transazione).

### 10. "Il cliente contesta una fattura per usage-based billing"

**Cause**: il cliente non ha visibilità sul consumo, aggregazione errata, eventi duplicati.
**Soluzioni**:
- Dashboard real-time del consumo accessibile al cliente.
- Notifiche proattive quando il consumo supera soglie (50%, 80%, 100% del budget).
- Audit log immutabile di tutti gli eventi di usage.
- Periodo di contestazione (7 giorni dalla fattura) con review manuale.
- Idempotency key su ogni evento per prevenire doppi conteggi.

### 11. "Il pagamento ACH/SEPA impiega troppo tempo a confermarsi"

**Cause**: ACH richiede 3-5 giorni lavorativi per il settlement, SEPA 1-2 giorni.
**Soluzioni**:
- Non attendere la conferma per attivare il servizio (il rischio di chargeback ACH è basso per SaaS).
- Attivare l'accesso provvisorio al momento della creazione del mandato.
- Usare micro-deposit verification per nuovi conti ACH.
- Per SEPA: Instant SEPA Credit Transfer riduce i tempi a secondi (se supportato).

### 12. "I crediti del cliente non vengono applicati correttamente"

**Cause**: crediti non collegati al customer balance, credit note non collegata alla prossima invoice.
**Soluzioni**:
- Usare il `customer_balance` in Stripe per applicare crediti automaticamente alla prossima fattura.
- Verificare che la credit note abbia `credit_amount` (non solo `refund_amount`).
- Implementare un ledger di crediti con audit trail.

### 13. "Il VAT ID del cliente non è valido secondo VIES"

**Cause**: errore di digitazione, azienda non ancora registrata, VIES temporaneamente down.
**Soluzioni**:
- Validare il formato prima di chiamare VIES (regex per ogni paese).
- VIES ha downtime frequenti: implementare retry con backoff (3 tentativi in 24 ore).
- Se VIES non risponde, accettare provvisoriamente con flag per rivalidazione.
- Tenere un log delle validazioni con timestamp per compliance audit.

### 14. "Dunning recovery rate sotto il 40%"

**Cause**: timing dei retry non ottimale, comunicazione poco efficace, nessun canale alternativo.
**Soluzioni**:
- Passare a Smart Retries (ML-based) se disponibili.
- Diversificare i canali: email + in-app banner + SMS.
- A/B testare le email di dunning (oggetto, CTA, urgenza).
- Offrire metodi di pagamento alternativi nelle email di dunning.
- Per piani annual di alto valore: chiamata diretta dal customer success.

### 15. "Il contratto enterprise si rinnova automaticamente ma il cliente non ha firmato il rinnovo"

**Cause**: il contratto ha auto-renew ma il cliente si aspettava una rinegoziazione.
**Soluzioni**:
- Notificare 90 giorni prima della scadenza contrattuale.
- Implementare un renewal workflow: notifica → proposta → firma → rinnovo.
- Nel contratto, specificare chiaramente: auto-renew alle stesse condizioni salvo disdetta entro X giorni.
- CRM reminder per l'account manager 120 giorni prima della scadenza.

### 16. "Riconciliazione tra billing provider e contabilità non quadra"

**Cause**: timing dei payout, FX conversion, commissioni dedotte, rimborsi non registrati.
**Soluzioni**:
- Usare il Stripe Balance Transaction report per la riconciliazione.
- Registrare ogni payout come un'entità separata in contabilità.
- Tracciare commissioni, FX e rimborsi come voci separate.
- Automatizzare con l'integrazione diretta al sistema contabile (Xero, QuickBooks).
- Riconciliazione mensile obbligatoria, non trimestrale.

---

## FAQ — Domande Frequenti

### Q1: Devo costruire il billing system in-house?

**No, nel 99% dei casi.** Costruire un billing system in-house è uno degli errori più costosi che un SaaS possa fare. Stripe Billing, Chargebee o un MoR come Paddle coprono virtualmente ogni scenario. Il costo di build è 6-12 mesi di engineering + manutenzione continua per tasse, compliance, nuovi metodi di pagamento, edge case. Usare quel tempo per il prodotto core.

### Q2: Stripe o Paddle? Come scelgo?

Se il team ha risorse per gestire la compliance fiscale (o usa Stripe Tax) e vuole controllo totale sulla UX: **Stripe**. Se il team è piccolo, vende in molti paesi, e vuole eliminare la complessità fiscale: **Paddle** (o LemonSqueezy). La regola pratica: sotto $5M ARR e team < 20 persone, il MoR fa risparmiare più tempo di quanto costi. Sopra $5M ARR, la commissione del 5% pesa e conviene Stripe + Tax Engine.

### Q3: Come gestisco la proration quando il cliente fa upgrade/downgrade?

Per gli upgrade: proration immediata (addebita la differenza pro-rata). Per i downgrade: cambio al prossimo rinnovo (il cliente mantiene il piano corrente fino alla scadenza). Stripe gestisce la proration automaticamente con `proration_behavior: "create_prorations"`. Mostrare sempre un preview dell'importo prima di confermare.

### Q4: Devo raccogliere la carta durante il free trial?

Dipende dalla strategia. Trial con carta: conversion rate 15-30%, meno sign-up. Trial senza carta: conversion rate 2-5%, più sign-up. Se il prodotto ha un forte "aha moment" nei primi giorni, trial con carta converte meglio. Se serve volume per network effect, trial senza carta è preferibile.

### Q5: Come funziona il reverse charge IVA per vendite B2B intra-UE?

Se il venditore è in un paese UE e il cliente B2B è in un altro paese UE con VAT ID valido: il venditore non addebita l'IVA. L'IVA viene "auto-liquidata" dal cliente nel proprio paese. Requisiti: validare il VAT ID tramite VIES, indicare in fattura "Inversione contabile art. 196 Dir. 2006/112/CE", dichiarare la vendita nel modello Intrastat (se applicabile).

### Q6: Quanto costa la compliance per la sales tax USA?

Con un tool automatizzato (Stripe Tax, Avalara, TaxJar): $50-500/mese base + 0.2-0.5% per transazione. Senza tool: il costo di un commercialista specializzato in multi-state tax filing è $5.000-20.000/anno. Per SaaS che vendono poco negli USA, un MoR elimina il problema.

### Q7: Come gestisco i pagamenti enterprise con PO e Net-30?

Separare completamente il billing enterprise dal self-service. Workflow: ricevere il PO dal procurement, creare una fattura con il PO number, inviarla al contatto AP del cliente, impostare reminder a 7 e 1 giorno prima della scadenza, tracciare i pagamenti ricevuti via bonifico, riconciliare manualmente (o con tool di reconciliation).

### Q8: Devo supportare PayPal?

In generale no, a meno che una percentuale significativa dei clienti lo richieda. PayPal introduce complessità (account bloccati, dispute più facili per il cliente, commissioni simili alla carta). Eccezioni: mercato tedesco (PayPal è molto usato), B2C con clienti non business.

### Q9: Quando devo iniziare con la revenue recognition ASC 606?

Se il SaaS ha revenue < $5M ARR e non sta pianificando un fundraising imminente: cash-basis accounting è sufficiente. Se il SaaS sta crescendo verso $5M+ o sta preparando un Series A/B: iniziare a tracciare il deferred revenue. Non è obbligatorio per la contabilità ma ogni investor e auditor lo chiederà. Tool come Stripe Revenue Recognition o ChartMogul automatizzano il processo.

### Q10: Come prevedo e riduco l'involuntary churn?

Tre livelli: (1) Pre-dunning — notificare le carte in scadenza 30 giorni prima, attivare card updater automatico. (2) Dunning — smart retry con ML, email sequence con urgenza crescente, in-app banner, SMS. (3) Post-churn — email di "win-back" con offerta di sconto per riattivare, preservare i dati per 90 giorni. Target: recovery rate > 60%.

### Q11: Come gestisco le tasse per i clienti non-UE/non-USA?

Dipende dal paese. Molti paesi non hanno GST/VAT sui servizi digitali importati (o non lo applicano nella pratica). Per semplificare: usare un MoR che gestisca la compliance globale, oppure concentrarsi sui paesi dove si ha nexus/obbligo reale e per gli altri addebitare senza tax. Consultare un fiscalista specializzato in digital services per i mercati principali.

### Q12: Il mio SaaS deve emettere fattura elettronica?

Dipende dal paese. In Italia è obbligatorio (Sistema di Interscambio SDI, formato FatturaPA XML). In Francia sarà obbligatorio progressivamente dal 2026. In Germania non è obbligatorio per B2C ma lo è per B2G. In ogni caso, emettere una fattura conforme (PDF o elettronica) per ogni transazione è una best practice.

### Q13: Come gestisco un chargeback/dispute?

Rispondere entro il deadline (Stripe: 7-21 giorni, dipende dalla reason). Raccogliere evidenze: log di accesso che mostrano l'uso del servizio, email al cliente, ToS accettati, IP di login. Sottomettere la risposta con le evidenze. Tasso di vittoria medio per SaaS con buone evidenze: 40-60%. Prevenzione: usare statement descriptor chiaro (il nome del SaaS deve apparire sull'estratto conto del cliente), inviare receipt email per ogni pagamento.

### Q14: Devo implementare il billing per metered/usage-based subito?

Solo se il modello di pricing lo richiede. Il metered billing aggiunge complessità significativa: event pipeline, aggregation, idempotency, dashboard real-time. Se il SaaS è early-stage, iniziare con un modello seat-based o flat-rate e migrare a usage-based quando il product-market fit è validato e il team ha le risorse per implementarlo correttamente.

### Q15: Come scelgo tra fatturazione mensile e annuale per i contratti enterprise?

Di default, offrire fatturazione annuale upfront con sconto (15-20% vs. mensile). Benefici: migliore cash flow, commitment del cliente, meno cicli di fatturazione. Se il cliente richiede fatturazione mensile o trimestrale, concederla ma senza sconto. Per contratti > $100K/anno, il quarterly invoicing è un buon compromesso (4 fatture/anno invece di 12, cash flow ragionevole).

### Q16: Come faccio testing del billing senza addebitare carte reali?

Ogni billing provider ha un ambiente sandbox/test. Stripe: usare le API key di test (`sk_test_*`), carte di test (`4242 4242 4242 4242`), e il Stripe CLI per simulare webhook. Paddle: sandbox environment separato. Testare ogni flusso: pagamento riuscito, pagamento fallito, 3DS, upgrade, downgrade, cancellazione, dunning, dispute. Automatizzare i test con il sandbox in CI/CD.

---

## Checklist di Implementazione

### Fase 1 — Fondamenta (Settimana 1-2)

```
[ ] Scegliere il billing provider (Stripe / Paddle / Chargebee)
[ ] Configurare l'account sandbox/test
[ ] Definire i piani di pricing (prodotti e prezzi nel provider)
[ ] Implementare il checkout flow (Stripe Checkout o Elements)
[ ] Integrare il customer creation (sync utenti → billing provider)
[ ] Testare il pagamento con carta di test
[ ] Verificare PCI compliance (SAQ-A o SAQ-A-EP)
[ ] Configurare il webhook endpoint
[ ] Implementare verifica firma webhook
[ ] Implementare idempotency nel webhook handler
```

### Fase 2 — Subscription Management (Settimana 2-3)

```
[ ] Implementare creazione subscription
[ ] Gestire trial (con/senza carta)
[ ] Implementare upgrade (immediato con proration)
[ ] Implementare downgrade (al prossimo rinnovo)
[ ] Implementare cancellazione (at_period_end)
[ ] Implementare riattivazione
[ ] Implementare pausa (se richiesta dal business)
[ ] Costruire l'entitlement system (cache + webhook invalidation)
[ ] Testare ogni transizione di stato
[ ] Implementare il customer portal (Stripe Customer Portal o custom)
```

### Fase 3 — Fatturazione e Tasse (Settimana 3-4)

```
[ ] Configurare la generazione automatica delle fatture
[ ] Implementare la numerazione progressiva delle fatture
[ ] Configurare Stripe Tax o il tax engine scelto
[ ] Implementare la validazione VAT ID (VIES) per B2B UE
[ ] Configurare il reverse charge per B2B intra-UE
[ ] Gestire le aliquote IVA per paese (B2C UE)
[ ] Implementare le note di credito
[ ] Configurare l'integrazione con il sistema contabile
[ ] Testare la fatturazione in multi-currency (se applicabile)
[ ] Verificare la compliance fiscale con un commercialista
```

### Fase 4 — Dunning e Recovery (Settimana 4-5)

```
[ ] Configurare gli Smart Retries (Stripe) o custom retry schedule
[ ] Implementare la sequenza email di dunning (4-5 email)
[ ] Implementare in-app banner per pagamenti falliti
[ ] Configurare il card updater automatico
[ ] Implementare la notifica carta in scadenza (pre-dunning)
[ ] Definire la policy di sospensione (giorno 21)
[ ] Definire la policy di cancellazione (giorno 90)
[ ] Implementare la riattivazione post-sospensione
[ ] Monitorare il recovery rate (target > 60%)
[ ] A/B testare le email di dunning
```

### Fase 5 — Enterprise e Avanzato (Settimana 5-8)

```
[ ] Implementare il billing enterprise (PO, Net-30/60)
[ ] Configurare i contratti annuali e multi-anno
[ ] Implementare usage-based billing (se necessario)
[ ] Costruire la pipeline di metering (se usage-based)
[ ] Implementare multi-currency con prezzi fissi
[ ] Configurare la revenue recognition (se > $5M ARR)
[ ] Implementare la gestione dispute/chargeback
[ ] Costruire dashboard metriche billing (MRR, churn, recovery rate)
[ ] Audit di sicurezza PCI pre-lancio
[ ] Load test del billing system
```

### Fase 6 — Go-Live e Monitoring (Settimana 8+)

```
[ ] Migrazione dall'ambiente test al live (chiavi API live)
[ ] Verificare i webhook in ambiente live
[ ] Monitorare il payment success rate (primo mese)
[ ] Monitorare il decline rate e ottimizzare
[ ] Riconciliazione contabile del primo mese
[ ] Verificare la compliance fiscale del primo mese
[ ] Documentare le procedure operative per il team
[ ] Formare il team support sulla gestione billing
[ ] Pianificare la revisione trimestrale dei prezzi multi-currency
[ ] Impostare alert per anomalie (spike di decline, chargeback, etc.)
```
