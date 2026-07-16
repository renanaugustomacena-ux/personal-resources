# Tutorial: Hardware Lifecycle Management — Hands-On Lab

> **Documento di riferimento:** `16-hardware-lifecycle-refresh.md`
> **Dominio:** Operations Advanced
> **Ambito:** Lifecycle hardware, EOL/EOSL, ROI refresh, smaltimento RAEE, sanitizzazione dati, ITAD
> **Durata lab:** 8-10 ore (suddivise in sessioni da 2 ore)
> **Livello:** Da principiante (Parte A) ad avanzato (Parte C)
> **Prerequisiti:** `tutorial_ops08_ch1a_asset_lifecycle_lab.md` (gestione asset base), GLPI installato nel lab
> **Ambiente:** Solo lab isolato — mai su sistemi di produzione

---

## Lab Environment Setup

### Requisiti Hardware

| Componente | Minimo | Raccomandato |
|---|---|---|
| RAM host | 6 GB | 12 GB |
| Storage host | 30 GB liberi | 60 GB liberi |
| OS host | Windows 10/11, Ubuntu 22.04 | Qualsiasi |

### VM necessarie

```
Lab Hardware Lifecycle
======================
VM1  Ubuntu 22.04 — Python 3.11, script lifecycle
     IP: 192.168.56.10
     RAM: 2 GB, 2 vCPU

VM2  Ubuntu 22.04 — Disco da sanitizzare (lab)
     IP: 192.168.56.11
     RAM: 1 GB, 1 vCPU
     Disco aggiuntivo: /dev/sdb (virtuale, 5 GB, non montato)

HOST  Windows/Linux — Excel/LibreOffice, browser, terminali
```

### Setup disco lab per esercizi sanitizzazione

```bash
# Su VM2 — aggiungi disco virtuale da VirtualBox GUI:
# Impostazioni → Storage → Aggiungi disco → 5 GB → dinamico
# Avvia VM2, verifica disco:
lsblk
# Output atteso:
# NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
# sda      8:0    0   20G  0 disk
# └─sda1   8:1    0   20G  0 part /
# sdb      8:16   0    5G  0 disk     ← disco lab da sanitizzare

# Scrivi dati fittizi per simulare disco con dati
sudo dd if=/dev/urandom of=/dev/sdb bs=1M count=100 status=progress
```

### Struttura directory lab

```bash
# Su VM1
mkdir -p ~/lifecycle_lab/{data,scripts,reports,certificates}
cd ~/lifecycle_lab
```

---

## PART A: FONDAMENTI — Capire il Perché e il Cosa

### Concetto A1: Il Ciclo di Vita dell'Hardware — Perché Gestirlo

**Analogia.** Un'automobile ha un ciclo di vita preciso: acquisto → manutenzione ordinaria → revisione → usura componenti → decisione di tenere o cambiare → smaltimento conforme. Se la gestisci bene, la vendi prima che diventi un peso; se la trascuri, ti blocca in autostrada e paghi il carro attrezzi. L'hardware IT funziona esattamente così — con in più la dimensione della sicurezza dei dati che ci sono dentro.

**Il ciclo in 7 fasi:**

```
  1. PLAN     → Definisci requisiti, budget, standard
      ↓
  2. PROCURE  → RFQ/RFP, negoziazione, ordine
      ↓
  3. DEPLOY   → Installazione, configurazione, inventario
      ↓
  4. OPERATE  → Uso produttivo quotidiano
      ↓
  5. MAINTAIN → Manutenzione, aggiornamenti firmware, monitoring
      ↓
  6. REFRESH  → Valutazione sostituzione (ROI, EOL, performance)
      ↓
  7. RETIRE/DISPOSE → Sanitizzazione dati, smaltimento RAEE conforme
      ↑__________________________|
           (nuovo ciclo)
```

**Perché mi interessa?** Senza lifecycle management:
- Un server core va in crash e la garanzia è scaduta da 18 mesi senza che nessuno lo sapesse
- Hardware con dati personali finisce nella spazzatura comune → violazione GDPR → sanzione fino al 4% del fatturato globale
- Il budget IT non è mai prevedibile: acquisti in emergenza, costi tripli
- Audit ISO 27001 fallisce su A.7.14 (secure disposal) e A.5.9 (asset inventory)

Con lifecycle management:
- Budget refresh pianificato 12-18 mesi prima
- Zero sorprese su garanzie scadute
- Conformità GDPR, RAEE e ISO 27001 documentata
- ROI refresh calcolato e difendibile al CFO

---

### Concetto A2: Cicli di Refresh per Tipo di Hardware

**Analogia.** Un pneumatico da corsa dura 50 km; un pneumatico stradale 60.000 km. Stessa gomma, usi diversi → aspettative di vita diverse. In IT, diversi tipi di hardware hanno "chilometraggio" molto diverso.

**Cicli di refresh raccomandati:**

| Tipo Hardware | Ciclo Tipico | Driver Principale | Note |
|---|---|---|---|
| Server rack/tower | 3-5 anni | Performance gap, garanzia | HPE Gen10 → Gen12: 3x densità compute |
| Storage array enterprise | 5-7 anni | Capacità, IOPS, EOSL vendor | NetApp, Pure, HPE Nimble |
| Switch/router enterprise | 5-7 anni | Throughput, feature set | Core switch può durare 7+ anni |
| Firewall/NGFW | 5 anni | SSL throughput, CVE firmware | EOSL licenze spesso forzante |
| Laptop/notebook | 3-4 anni (intensivo) 4-5 anni (standard) | Batteria, TPM, Windows 11 compat | |
| Desktop fisso | 4-5 anni | Raramente prima del necessario | Rischio prolungare a 7-8 anni |
| UPS (unità) | 7-10 anni | Componenti elettronici | |
| UPS (batterie) | 3-5 anni VRLA, 8-10 anni Li-ion | Capacità effettiva | Pianificare separatamente |
| Stampanti enterprise | 4-7 anni | Spesso in noleggio full-service | |

**Perché refresh periodico invece di "finché funziona"?**

```
Costo annuo di mantenimento
  ╔════════════════════════════════════════╗
  ║  Extended warranty     ████████████    ║  15-25% costo nuovo
  ║  Energia (vecchio HW)  ██████          ║  +40-60% vs nuovo
  ║  Cooling associato     ████            ║
  ║  Tempo IT extra        ████            ║  3-5 ore/mese in più
  ║  Rischio downtime      ██████████      ║  incalcolabile
  ╚════════════════════════════════════════╝
  VS
  ╔════════════════════════════════════════╗
  ║  Ammortamento nuovo HW ████████        ║  lineare 5 anni
  ║  Contratto incluso 3a  ██              ║  compreso nel prezzo
  ║  Energia (nuovo HW)    ████            ║  -40-60% vs vecchio
  ╚════════════════════════════════════════╝
```

---

### Concetto A3: EOL, EOS, EOSL, EOVS — la Terminologia Vendor

**Analogia.** Un'auto fuori produzione: prima smettono di produrla (EOA), poi i concessionari smettono di venderla (EOS), poi Fiat smette di aggiornare i software (EOSW), poi smettono di fornire ricambi originali (EOSL). Per la sicurezza, la data critica è quando i produttori di software di terze parti smettono di testare la compatibilità (EOVS). L'hardware IT ha la stessa progressione.

**Glossario definitivo:**

| Sigla | Significato | Impatto operativo |
|---|---|---|
| **EOA / LDoO** | End of Availability — ultima data ordine | Non puoi ordinare nuovo |
| **EOS** | End of Sale — esce dal listino | = EOA, spesso sinonimo |
| **EOL** | End of Life — annuncio formale | Segnale: inizia pianificazione refresh |
| **EOSW** | End of Software Maintenance | Stop nuove versioni firmware |
| **EOVS** | End of Vulnerability/Security Support | **SOGLIA CRITICA**: stop patch CVE |
| **EOSL / LDoS** | End of Service Life | No più RMA, no supporto, no KB |

**Timeline tipica Cisco (standard de facto):**

```
Annuncio → +18 mesi → EOA → +6 mesi → EOS → +12 mesi → EOSW
→ +24 mesi → EOVS → +12 mesi → EOSL (= LDoS)
                                    ↑
                            Totale ~5 anni da EOA
```

**Esempio concreto (Cisco Catalyst 9300):**
- EOA: marzo 2026
- EoSale: settembre 2026
- EoSWMaint: settembre 2027
- EoSL (LDoS): settembre 2031

**Regola pratica:** pianificare il refresh entro 12 mesi da EOVS. Continuare a usare hardware oltre EOSL è accettabile solo con risk assessment documentato.

---

### Concetto A4: ROI del Refresh — Calcolo TCO Comparativo

**Analogia.** Tieni la vecchia macchina o compri la nuova? Fai i conti: revisione ogni anno, consumo alto, rischio guasto → vs. rata finanziamento + assicurazione + consumi ridotti. Se i costi di mantenimento superano il costo annualizzato del nuovo, conviene cambiare.

**Framework TCO comparativo:**

```
TCO Mantenimento (per anno):
  + Extended warranty        (15-25% del costo nuovo equivalente)
  + Energia vecchio HW       (kWh × 8760 × €/kWh)
  + Cooling associato        (50-80% del consumo IT)
  + Tempo IT extra           (ore/mese × €/ora)
  + Rischio downtime         (P(guasto) × impatto orario €)
  ──────────────────────────
  = TCO_mantieni / anno

TCO Refresh (ammortizzato 5 anni):
  + Acquisto HW              / 5 anni
  + Licenze refresh          / 5 anni
  + Migration project        / 5 anni
  + Contratto vendor         (incluso anni 1-3)
  + Energia nuovo HW         (-40-60% vs vecchio)
  ──────────────────────────
  = TCO_refresh / anno
```

**Se TCO_mantieni > TCO_refresh → refresh giustificato economicamente.**

---

### Concetto A5: NIST SP 800-88 — Tre Livelli di Sanitizzazione

**Analogia.** Prima di vendere casa, pulisci: sgombero base (via scatole), pulizia profonda (vernici, pavimenti), demolizione (se vuoi costruire da zero). I livelli di sanitizzazione dei dischi IT seguono la stessa logica crescente.

**I tre livelli NIST SP 800-88:**

| Livello | Tecnica | Quando usarlo | Recuperabilità |
|---|---|---|---|
| **Clear** | Sovrascrittura logica (DoD 3-pass, ATA Secure Erase) | Riuso interno, donazione basso rischio | Non recuperabile con software standard |
| **Purge** | ATA Secure Erase Enhanced, NVMe Crypto Erase, degausser | Dismissione esterna, vendita refurbish | Non recuperabile con laboratorio |
| **Destroy** | Trituratore fisico (DIN 66399), incenerimento | Dati top secret, quando Purge non possibile | Impossibile |

**Quale scegliere?**

```
Dati sensibili/personali (GDPR) + dismissione esterna → Purge minimo
Dati riservati/segreti commerciali → Destroy
Riuso interno sicuro → Clear
Donazione ente benefico → Purge
```

---

### Concetto A6: RAEE e D.Lgs 49/2014 — Obbligo di Legge

**Analogia.** I rifiuti elettronici non si buttano nel cassonetto normale, come le pile. C'è una normativa specifica, sanzioni pesanti, e una catena di custodia obbligatoria. In Italia il riferimento è il D.Lgs 49/2014 (recepimento direttiva europea 2012/19/UE).

**Categorie RAEE rilevanti per IT:**

| Categoria | Contenuto | Esempi IT |
|---|---|---|
| R4 — Grandi apparecchi (> 50 cm) | Server rack, UPS, switch enterprise | HPE DL380, APC Smart-UPS 5000 |
| R5 — Piccole apparecchiature (< 50 cm) | Laptop, mini PC, switch desktop | ThinkPad, Mac mini, Cisco SG300 |
| R2 — Schermi > 100 cm² | Monitor, display | Qualsiasi monitor |

**Procedura obbligatoria:**

```
1. Inventario asset → 2. Cancellazione dati → 3. Selezione gestore autorizzato
→ 4. FIR (Formulario Identificazione Rifiuto) → 5. Trasporto autorizzato
→ 6. Ricezione FIR controfirmato (entro 90 giorni)
→ 7. Conservazione documentazione
```

**Sanzioni per smaltimento illegale:**
- Abbandono RAEE: €260 – €1.500
- Smaltimento senza autorizzazione: €2.600 – €26.000 + penale
- Mancata compilazione FIR: €1.600 – €9.300

---

## PART B: OPERAZIONI — Costruire e Configurare

### Esercizio B1: Asset Lifecycle Tracker — Database Python

**Obiettivo.** Creare un tracker lifecycle asset in Python con tutte le date critiche e alerting automatico.

```python
# scripts/b1_asset_tracker.py
import json
import csv
from datetime import date, datetime
from dataclasses import dataclass, field, asdict

TRACKER_FILE = 'data/asset_lifecycle.json'
ALERT_DAYS   = [180, 90, 30]  # giorni prima delle date critiche

@dataclass
class AssetRecord:
    asset_tag: str
    tipo: str          # Server / Switch / NB / WS / UPS / Firewall
    vendor: str
    modello: str
    serial_number: str
    data_acquisto: str    # YYYY-MM-DD
    costo_acquisto: float
    ubicazione: str
    owner: str
    ruolo: str         # Production / Test / DR / Backup
    garanzia_fine: str    # YYYY-MM-DD
    contratto_supporto: str
    contratto_fine: str   # YYYY-MM-DD
    eol_vendor: str       # YYYY-MM-DD
    eosl_vendor: str      # YYYY-MM-DD
    refresh_planned: str  # YYYY-MM o ''
    stato: str         # Active / Deprecated / Retired / Disposed
    note: str = ''

def load_assets() -> list[AssetRecord]:
    try:
        with open(TRACKER_FILE, 'r', encoding='utf-8') as f:
            return [AssetRecord(**a) for a in json.load(f)]
    except FileNotFoundError:
        return []

def save_assets(assets: list[AssetRecord]):
    with open(TRACKER_FILE, 'w', encoding='utf-8') as f:
        json.dump([asdict(a) for a in assets], f, indent=2, ensure_ascii=False)

def check_alerts(assets: list[AssetRecord]) -> list[dict]:
    today   = date.today()
    alerts  = []
    
    for a in assets:
        if a.stato != 'Active':
            continue
        
        critical_dates = {
            'Garanzia':         a.garanzia_fine,
            'Contratto':        a.contratto_fine,
            'EOL Vendor':       a.eol_vendor,
            'EOSL Vendor':      a.eosl_vendor,
        }
        
        for label, date_str in critical_dates.items():
            if not date_str or date_str == '':
                continue
            try:
                target = date.fromisoformat(date_str)
                days_left = (target - today).days
                for threshold in ALERT_DAYS:
                    if days_left <= threshold:
                        level = 'CRITICAL' if days_left <= 30 else ('WARNING' if days_left <= 90 else 'INFO')
                        alerts.append({
                            'asset_tag': a.asset_tag,
                            'modello':   a.modello,
                            'event':     label,
                            'date':      date_str,
                            'days_left': days_left,
                            'level':     level,
                        })
                        break  # solo l'alert più urgente per evento
            except ValueError:
                continue
    
    return sorted(alerts, key=lambda x: x['days_left'])

def print_alerts(alerts: list[dict]):
    if not alerts:
        print("✅ Nessun alert attivo.")
        return
    
    print(f"\n{'='*70}")
    print(f"ASSET LIFECYCLE ALERTS — {date.today().isoformat()}")
    print(f"{'='*70}")
    
    for a in alerts:
        icon = {'CRITICAL': '🔴', 'WARNING': '🟡', 'INFO': '🔵'}[a['level']]
        print(f"{icon} {a['level']:>8}  {a['asset_tag']:>12}  {a['modello']:<25}  "
              f"{a['event']:<15}  {a['days_left']:>4} gg  ({a['date']})")

def add_sample_assets():
    """Aggiunge asset di esempio per il lab."""
    today = date.today()
    
    assets = [
        AssetRecord(
            asset_tag='IT-SRV-001',
            tipo='Server',
            vendor='HPE',
            modello='ProLiant DL380 Gen10',
            serial_number='MXQ1234567',
            data_acquisto='2020-03-15',
            costo_acquisto=8500.00,
            ubicazione='DC1-Rack3-U18',
            owner='infrastruttura@azienda.it',
            ruolo='Production',
            garanzia_fine='2023-03-15',  # già scaduta
            contratto_supporto='HPE Pointnext NBD',
            contratto_fine=(today.replace(year=today.year - 1)).isoformat(),
            eol_vendor='2027-09-30',
            eosl_vendor='2030-09-30',
            refresh_planned='2025-Q2',
            stato='Active',
            note='SAP applicativo primario',
        ),
        AssetRecord(
            asset_tag='IT-SW-005',
            tipo='Switch',
            vendor='Cisco',
            modello='Catalyst 9300-48P',
            serial_number='FCW2145B0DE',
            data_acquisto='2021-06-01',
            costo_acquisto=12000.00,
            ubicazione='DC1-Rack1-U2',
            owner='network@azienda.it',
            ruolo='Production',
            garanzia_fine='2024-06-01',
            contratto_supporto='Cisco SmartNet 24x7x4',
            contratto_fine=(today.replace(year=today.year + 1)).isoformat(),
            eol_vendor='2028-03-31',
            eosl_vendor='2031-03-31',
            refresh_planned='',
            stato='Active',
        ),
        AssetRecord(
            asset_tag='IT-NB-042',
            tipo='Notebook',
            vendor='Lenovo',
            modello='ThinkPad T490',
            serial_number='PF2Y3456',
            data_acquisto='2019-09-10',
            costo_acquisto=1200.00,
            ubicazione='Ufficio-Admin',
            owner='mario.rossi@azienda.it',
            ruolo='Production',
            garanzia_fine='2022-09-10',
            contratto_supporto='Lenovo Premier 1 anno',
            contratto_fine='2022-09-10',
            eol_vendor='2025-12-31',
            eosl_vendor='2026-12-31',
            refresh_planned='2025-Q1',
            stato='Active',
            note='Batteria da sostituire',
        ),
    ]
    save_assets(assets)
    print(f"Aggiunti {len(assets)} asset di esempio.")

if __name__ == '__main__':
    add_sample_assets()
    assets = load_assets()
    print(f"Asset in inventario: {len(assets)}")
    
    alerts = check_alerts(assets)
    print_alerts(alerts)
```

```bash
python3 scripts/b1_asset_tracker.py
```

**Output atteso:**

```
Aggiunti 3 asset di esempio.
Asset in inventario: 3

======================================================================
ASSET LIFECYCLE ALERTS — 2025-07-15
======================================================================
🔴 CRITICAL    IT-SRV-001  ProLiant DL380 Gen10     Contratto       -312 gg  (2024-07-15)
🔴 CRITICAL    IT-NB-042   ThinkPad T490            Garanzia      -1039 gg  (2022-09-10)
🟡  WARNING    IT-NB-042   ThinkPad T490            EOL Vendor       169 gg  (2025-12-31)
```

---

### Esercizio B2: Calcolo ROI Refresh — Confronto TCO

**Obiettivo.** Calcolare e confrontare TCO di mantenimento vs refresh per un server aging.

```python
# scripts/b2_tco_refresh.py
from dataclasses import dataclass

@dataclass
class MaintenanceTCO:
    """TCO annuo di mantenimento hardware esistente."""
    extended_warranty_eur: float    # estensione garanzia
    power_watts: float              # consumo energetico
    electricity_price_kwh: float    # prezzo energia (IT: 0.18-0.30 €/kWh)
    pue: float                      # Power Usage Effectiveness datacenter (tipico 1.3-1.6)
    it_hours_per_month: float       # ore IT manutenzione extra
    it_hourly_rate_eur: float       # costo orario tecnico IT
    downtime_prob_annual: float     # probabilità guasto nell'anno (%)
    downtime_cost_per_hour: float   # costo orario downtime aziendale

    @property
    def energy_cost_annual(self) -> float:
        return self.power_watts / 1000 * 8760 * self.electricity_price_kwh * self.pue

    @property
    def it_cost_annual(self) -> float:
        return self.it_hours_per_month * 12 * self.it_hourly_rate_eur

    @property
    def downtime_risk_annual(self) -> float:
        avg_mttr_hours = 4
        return (self.downtime_prob_annual / 100) * avg_mttr_hours * self.downtime_cost_per_hour

    @property
    def total_annual(self) -> float:
        return (self.extended_warranty_eur + self.energy_cost_annual
                + self.it_cost_annual + self.downtime_risk_annual)

@dataclass
class RefreshTCO:
    """TCO annualizzato refresh hardware (su 5 anni)."""
    hardware_cost: float
    licenses_cost: float
    migration_cost: float
    power_watts_new: float
    electricity_price_kwh: float
    pue: float
    warranty_years_included: int = 3   # garanzia inclusa nell'acquisto
    warranty_extension_eur: float = 0  # costo estensione anni 4-5
    amortization_years: int = 5

    @property
    def energy_cost_annual(self) -> float:
        return self.power_watts_new / 1000 * 8760 * self.electricity_price_kwh * self.pue

    @property
    def amortized_hardware(self) -> float:
        return self.hardware_cost / self.amortization_years

    @property
    def amortized_licenses(self) -> float:
        return self.licenses_cost / self.amortization_years

    @property
    def amortized_migration(self) -> float:
        return self.migration_cost / self.amortization_years

    @property
    def warranty_annual_avg(self) -> float:
        return self.warranty_extension_eur / max(1, self.amortization_years - self.warranty_years_included)

    @property
    def total_annual_avg(self) -> float:
        return (self.amortized_hardware + self.amortized_licenses
                + self.amortized_migration + self.energy_cost_annual
                + self.warranty_annual_avg)

def compare_tco(maintain: MaintenanceTCO, refresh: RefreshTCO, asset_name: str):
    print(f"\n{'='*60}")
    print(f"TCO Analysis: {asset_name}")
    print(f"{'='*60}")
    print(f"\n--- Mantenimento (annuo) ---")
    print(f"  Extended warranty:  €{maintain.extended_warranty_eur:>8,.0f}")
    print(f"  Energia:            €{maintain.energy_cost_annual:>8,.0f}  ({maintain.power_watts}W × 8760h × {maintain.electricity_price_kwh}€/kWh × PUE{maintain.pue})")
    print(f"  IT extra:           €{maintain.it_cost_annual:>8,.0f}  ({maintain.it_hours_per_month}h/mese × €{maintain.it_hourly_rate_eur}/h)")
    print(f"  Rischio downtime:   €{maintain.downtime_risk_annual:>8,.0f}")
    print(f"  TOTALE annuo:       €{maintain.total_annual:>8,.0f}")
    
    print(f"\n--- Refresh (annuo medio 5 anni) ---")
    print(f"  Hardware ammort.:   €{refresh.amortized_hardware:>8,.0f}  (€{refresh.hardware_cost:,.0f} / {refresh.amortization_years} anni)")
    print(f"  Licenze ammort.:    €{refresh.amortized_licenses:>8,.0f}")
    print(f"  Migration ammort.:  €{refresh.amortized_migration:>8,.0f}")
    print(f"  Energia:            €{refresh.energy_cost_annual:>8,.0f}  ({refresh.power_watts_new}W, -{int((1-refresh.power_watts_new/maintain.power_watts)*100)}% vs attuale)")
    print(f"  Warranty ext.:      €{refresh.warranty_annual_avg:>8,.0f}")
    print(f"  TOTALE annuo medio: €{refresh.total_annual_avg:>8,.0f}")
    
    delta = maintain.total_annual - refresh.total_annual_avg
    print(f"\n--- Confronto ---")
    print(f"  Risparmio annuo refresh: €{delta:>8,.0f}")
    if delta > 0:
        payback = refresh.hardware_cost / delta if delta > 0 else float('inf')
        print(f"  Payback hardware:        {payback:.1f} anni")
        print(f"  ✅ REFRESH ECONOMICAMENTE VANTAGGIOSO")
    else:
        print(f"  ℹ️  Mantenimento ancora economico (diff: €{abs(delta):,.0f}/anno)")

# Caso reale: HPE DL380 Gen10 (2020, anno 6) vs Gen12 nuovo
maintain = MaintenanceTCO(
    extended_warranty_eur=4500,
    power_watts=450,
    electricity_price_kwh=0.25,  # costo energia IT Italia 2025
    pue=1.5,
    it_hours_per_month=3,
    it_hourly_rate_eur=60,
    downtime_prob_annual=15,
    downtime_cost_per_hour=2000,
)

refresh = RefreshTCO(
    hardware_cost=18000,
    licenses_cost=3000,
    migration_cost=5000,
    power_watts_new=220,
    electricity_price_kwh=0.25,
    pue=1.5,
    warranty_years_included=3,
    warranty_extension_eur=3600,
)

compare_tco(maintain, refresh, "HPE ProLiant DL380 Gen10 → Gen12")
```

---

### Esercizio B3: Monitoraggio EOL via API Cisco

**Obiettivo.** Interrogare l'API Cisco EoX per ottenere informazioni EOL di un dispositivo.

```bash
# Richiede account developer.cisco.com (gratuito)
# Ottieni token OAuth2 dalla console developer Cisco

CLIENT_ID="il-tuo-client-id"
CLIENT_SECRET="il-tuo-client-secret"

# Richiesta token
TOKEN=$(curl -s -X POST \
  "https://id.cisco.com/oauth2/default/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token ottenuto: ${TOKEN:0:20}..."

# Query EOL per numero seriale
SERIAL="FCW2145B0DE"
curl -s -X GET \
  "https://api.cisco.com/supporttools/eox/rest/5/EOXBySerialNumber/1/${SERIAL}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/json" \
  | python3 -m json.tool
```

**Alternativa offline per il lab (senza credenziali API):**

```python
# scripts/b3_eol_mock_api.py
# Simula risposta API Cisco EoX per il lab

import json

MOCK_EOL_DB = {
    'FCW2145B0DE': {
        'ProductID': 'WS-C9300-48P',
        'ProductName': 'Catalyst 9300 48-port PoE+',
        'EOXInputType': 'EOX_BY_SERIAL_NUMBER',
        'LastDateOfSupport': {
            'value': '2031-03-31',
            'dateFormat': 'YYYY-MM-DD',
        },
        'EndOfSaleDate': {
            'value': '2026-09-30',
        },
        'EndOfSWMaintenanceReleases': {
            'value': '2027-09-30',
        },
        'EndOfVulnerabilitySupport': {
            'value': '2028-09-30',
        },
        'EndOfServiceContractRenewal': {
            'value': '2031-03-31',
        },
    }
}

def query_eol(serial: str) -> dict | None:
    """Simula query API Cisco EoX."""
    return MOCK_EOL_DB.get(serial)

def format_eol_report(serial: str):
    data = query_eol(serial)
    if not data:
        print(f"Nessun dato EOL per serial {serial}")
        return
    
    print(f"\n=== EOL Report: {serial} ===")
    print(f"Prodotto:    {data['ProductID']} — {data['ProductName']}")
    print(f"End of Sale: {data['EndOfSaleDate']['value']}")
    print(f"End of SW:   {data['EndOfSWMaintenanceReleases']['value']}")
    print(f"End of CVE:  {data['EndOfVulnerabilitySupport']['value']}")
    print(f"End of Life: {data['LastDateOfSupport']['value']}")

format_eol_report('FCW2145B0DE')
```

---

### Esercizio B4: Piano Refresh Rolling 5 Anni

**Obiettivo.** Generare un piano refresh multi-anno con proiezione CAPEX.

```python
# scripts/b4_refresh_plan.py
from dataclasses import dataclass

@dataclass
class RefreshItem:
    anno: int
    categoria: str
    descrizione: str
    quantita: int
    costo_unitario: float
    priorita: str   # Obbligatorio / Pianificato / Opportunistico
    driver: str

REFRESH_PLAN = [
    RefreshItem(2025, 'Notebook',  '25 notebook cluster 2021 in scadenza garanzia', 25, 1100, 'Obbligatorio', 'Garanzia scaduta, Windows 11 compat'),
    RefreshItem(2025, 'Firewall',  'Firewall HQ — EOSL firmware 2025',               1, 8000, 'Obbligatorio', 'EOSL firmware + SSL throughput insufficiente'),
    RefreshItem(2026, 'Server',    'Server SAP applicativo HPE Gen10 anno 6',          1, 18000,'Pianificato',  'TCO mantenimento > refresh (vedi B2)'),
    RefreshItem(2026, 'Switch',    '2 switch core accesso — anno 7',                  2, 6000, 'Pianificato',  'Transizione a 10G uplink, PoE++'),
    RefreshItem(2027, 'Storage',   'Storage SAN principale — EOSL 2027',              1, 45000,'Obbligatorio', 'EOSL vendor, capacità insufficiente'),
    RefreshItem(2027, 'Desktop',   '25 desktop — anno 6, Windows 11 support',        25, 800,  'Pianificato',  'Obsolescenza TPM, CPU non supportata'),
    RefreshItem(2027, 'UPS',       'Batterie UPS sala server',                         4, 900,  'Pianificato',  'VRLA 4 anni, capacità degradata'),
    RefreshItem(2028, 'Notebook',  '25 notebook cluster 2024',                        25, 1100, 'Pianificato',  'Ciclo 4 anni'),
    RefreshItem(2028, 'Server',    'Server backup e file server',                      2, 9000, 'Pianificato',  'Anno 7, garanzia scaduta'),
    RefreshItem(2029, 'Notebook',  '25 notebook cluster 2025',                        25, 1100, 'Pianificato',  'Ciclo 4 anni'),
    RefreshItem(2029, 'Hypervisor','Refresh cluster hypervisor vSphere',               3, 20000,'Pianificato',  'vSphere 9.0 richiede CPU più recenti'),
]

def print_refresh_plan():
    print("=== Piano Refresh Rolling 5 Anni ===\n")
    anni = sorted(set(r.anno for r in REFRESH_PLAN))
    
    total_all = 0
    for anno in anni:
        items = [r for r in REFRESH_PLAN if r.anno == anno]
        anno_total = sum(r.quantita * r.costo_unitario for r in items)
        total_all += anno_total
        
        print(f"{'='*70}")
        print(f"  {anno}  —  CAPEX stimato: €{anno_total:>10,.0f}")
        print(f"{'='*70}")
        for r in items:
            costo = r.quantita * r.costo_unitario
            print(f"  [{r.priorita[:3].upper()}] {r.descrizione}")
            print(f"         Qtà: {r.quantita}× €{r.costo_unitario:,.0f} = €{costo:,.0f}  |  Driver: {r.driver}")
        print()
    
    print(f"{'='*70}")
    print(f"CAPEX TOTALE 5 ANNI: €{total_all:>10,.0f}")
    print(f"Media annua:         €{total_all/5:>10,.0f}")

print_refresh_plan()

# Esporta CSV per CFO/budget
import csv
with open('reports/refresh_plan_5y.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Anno', 'Categoria', 'Descrizione', 'Qtà', 'Costo unitario', 'Totale', 'Priorità', 'Driver'])
    for r in REFRESH_PLAN:
        w.writerow([r.anno, r.categoria, r.descrizione, r.quantita,
                    r.costo_unitario, r.quantita * r.costo_unitario,
                    r.priorita, r.driver])
print("\n📊 CSV esportato: reports/refresh_plan_5y.csv")
```

---

### Esercizio B5: Sanitizzazione Disco — Clear Level (Lab)

**Obiettivo.** Eseguire cancellazione sicura livello Clear su disco virtuale di test.

> ⚠️ **ATTENZIONE**: eseguire SOLO su `/dev/sdb` nella VM lab. Mai su `/dev/sda` (disco sistema). Verificare sempre con `lsblk` prima di procedere.

```bash
# Connetti a VM2
ssh lab@192.168.56.11

# VERIFICA OBBLIGATORIA: identifica il disco corretto
lsblk
# Assicurati che /dev/sdb sia il disco da 5 GB NON montato

# Verifica informazioni dispositivo
sudo hdparm -I /dev/sdb 2>/dev/null | grep -E "Model|Serial|Security"
# Se il dispositivo non supporta ATA Secure Erase, usa shred

# Metodo 1: shred (DoD 3-pass) — funziona su qualsiasi disco
echo "=== INIZIO SANITIZZAZIONE ==="
date
sudo shred -v -n 3 -z /dev/sdb
echo "=== FINE SANITIZZAZIONE ==="
date

# Verifica: i primi 1MB dovrebbero essere tutti zero (dopo il -z finale)
sudo dd if=/dev/sdb bs=1M count=1 2>/dev/null | hexdump -C | head -5
# Output atteso: tutti 00 00 00 00 (dopo il pass zero finale)
```

```bash
# Metodo 2: ATA Secure Erase (se supportato dal disco virtuale)
sudo hdparm -I /dev/sdb | grep -i "security mode"

# Se "enabled" o "supported":
sudo hdparm --user-master u --security-set-pass PasS /dev/sdb
sudo hdparm --user-master u --security-erase PasS /dev/sdb
sudo hdparm -I /dev/sdb | grep -i security  # verificare "not enabled, not locked"
```

```bash
# Metodo 3: NVMe Cryptographic Erase (per NVMe — se applicabile al lab)
sudo nvme list
sudo nvme format /dev/nvme0n1 --ses=1  # Secure Erase (user data)
# oppure
sudo nvme format /dev/nvme0n1 --ses=2  # Cryptographic Erase
```

---

### Esercizio B6: Script di Sanitizzazione con Log e Certificato

**Obiettivo.** Creare lo script completo di sanitizzazione con log audit e generazione certificato.

```bash
#!/bin/bash
# scripts/b6_sanitize_disk.sh
# Sanitizzazione disco con log completo per audit GDPR/ISO 27001
# USAGE: sudo ./b6_sanitize_disk.sh /dev/sdb "IT-NB-042" "ThinkPad T490" "PF2Y3456"

set -euo pipefail

DEVICE="${1:-}"
ASSET_TAG="${2:-UNKNOWN}"
ASSET_MODEL="${3:-UNKNOWN}"
ASSET_SERIAL="${4:-UNKNOWN}"

if [ -z "$DEVICE" ]; then
    echo "Usage: $0 <device> <asset_tag> <model> <serial>" >&2
    exit 1
fi

# Variabili audit
LOG_DIR="$HOME/lifecycle_lab/certificates"
TIMESTAMP=$(date -Iseconds)
OPERATOR="${USER}"
LOG_FILE="${LOG_DIR}/sanitize_${ASSET_TAG}_${TIMESTAMP//:/}.log"

mkdir -p "$LOG_DIR"

log() { echo "$@" | tee -a "$LOG_FILE"; }

log "=========================================="
log "  DISK SANITIZATION CERTIFICATE"
log "=========================================="
log "Date/Time:    $TIMESTAMP"
log "Operator:     $OPERATOR"
log "Asset Tag:    $ASSET_TAG"
log "Model:        $ASSET_MODEL"
log "Serial:       $ASSET_SERIAL"
log "Device:       $DEVICE"
log "Standard:     NIST SP 800-88 — Clear Level"
log "Method:       shred 3-pass DoD + zero-fill"
log "=========================================="

# Informazioni dispositivo
log ""
log "--- Device Information ---"
sudo hdparm -I "$DEVICE" 2>/dev/null | grep -E "Model|Serial|capacity|Security" | tee -a "$LOG_FILE" || true
log "Rotational: $(cat /sys/block/$(basename $DEVICE)/queue/rotational 2>/dev/null || echo 'N/A')"
log "Size: $(sudo blockdev --getsize64 "$DEVICE" 2>/dev/null | numfmt --to=iec || echo 'N/A')"

# Pre-sanitizzazione: verifica hash primo settore
log ""
log "--- Pre-Sanitization Hash (first 1MB) ---"
PRE_HASH=$(sudo dd if="$DEVICE" bs=1M count=1 2>/dev/null | sha256sum | cut -d' ' -f1)
log "SHA256 (pre):  $PRE_HASH"

# Sanitizzazione
log ""
log "--- Sanitization in Progress ---"
log "Start: $(date -Iseconds)"
sudo shred -v -n 3 -z "$DEVICE" 2>&1 | tee -a "$LOG_FILE"
log "End:   $(date -Iseconds)"

# Post-sanitizzazione: verifica
log ""
log "--- Post-Sanitization Verification ---"
POST_HASH=$(sudo dd if="$DEVICE" bs=1M count=1 2>/dev/null | sha256sum | cut -d' ' -f1)
log "SHA256 (post): $POST_HASH"
log "First 64 bytes (hex):"
sudo dd if="$DEVICE" bs=64 count=1 2>/dev/null | hexdump -C | head -4 | tee -a "$LOG_FILE"

# Risultato
log ""
if [ "$PRE_HASH" != "$POST_HASH" ]; then
    log "RESULT: PASS — Hash changed (data overwritten)"
    log "CERTIFICATION: Sanitization completed successfully"
    log "               Device ready for: Donation / External disposal"
else
    log "RESULT: INCONCLUSIVE — Hash unchanged (may indicate empty device)"
fi
log "=========================================="
log "Signed: $OPERATOR"
log "Certificate file: $LOG_FILE"
log "=========================================="

echo ""
echo "📜 Certificato salvato: $LOG_FILE"
```

```bash
# Esecuzione sul disco lab
chmod +x scripts/b6_sanitize_disk.sh
sudo scripts/b6_sanitize_disk.sh /dev/sdb IT-NB-042 "ThinkPad T490" PF2Y3456
```

---

### Esercizio B7: Asset Lifecycle Report Automatico

**Obiettivo.** Generare report completo lifecycle per audit ISO 27001.

```python
# scripts/b7_lifecycle_report.py
import json
from datetime import date

def load_assets():
    with open('data/asset_lifecycle.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_report(assets: list[dict]) -> str:
    today  = date.today()
    active = [a for a in assets if a['stato'] == 'Active']
    
    # Analisi per stato garanzia
    expired_warranty = []
    expiring_90d     = []
    eosl_risk        = []
    
    for a in active:
        try:
            gf = date.fromisoformat(a.get('garanzia_fine', '2099-01-01'))
            if gf < today:
                expired_warranty.append(a)
            elif (gf - today).days <= 90:
                expiring_90d.append(a)
        except ValueError:
            pass
        
        try:
            eosl = date.fromisoformat(a.get('eosl_vendor', '2099-01-01'))
            if (eosl - today).days <= 365:
                eosl_risk.append(a)
        except ValueError:
            pass
    
    report = f"""# Asset Lifecycle Report — {today.isoformat()}

## Statistiche Flotta

| Metrica | Valore |
|---|---|
| Asset totali (Active) | {len(active)} |
| Garanzia scaduta | {len(expired_warranty)} |
| Garanzia in scadenza (< 90 gg) | {len(expiring_90d)} |
| EOSL entro 12 mesi | {len(eosl_risk)} |

## Asset con Garanzia Scaduta (Azione richiesta)

| Asset Tag | Modello | Garanzia Fine | Contratto |
|---|---|---|---|
"""
    for a in expired_warranty:
        report += f"| {a['asset_tag']} | {a['modello']} | {a['garanzia_fine']} | {a['contratto_supporto']} |\n"
    
    report += """
## Asset EOSL entro 12 mesi

| Asset Tag | Modello | EOSL Vendor | Refresh Planned |
|---|---|---|---|
"""
    for a in eosl_risk:
        report += f"| {a['asset_tag']} | {a['modello']} | {a['eosl_vendor']} | {a.get('refresh_planned', 'NON PIANIFICATO')} |\n"
    
    report += f"""
## Conformità

- ISO 27001 A.5.9 (Asset Management): {'✅ Inventario completo' if len(active) > 0 else '❌ Inventario vuoto'}
- ISO 27001 A.7.14 (Secure Disposal): Verificare certificati smaltimento archiviati
- GDPR Art. 25 (Privacy by design): Sanitizzazione prima di ogni dismissione
- D.Lgs 49/2014 (RAEE): Smaltimento solo tramite gestori autorizzati

---
*Generato automaticamente — Conservare 5 anni per audit compliance*
"""
    return report

assets = load_assets()
report = generate_report(assets)
report_file = f"reports/lifecycle_report_{date.today().isoformat()}.md"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report)
print(report)
print(f"\n📄 Report: {report_file}")
```

---

## PART C: SISTEMATIZZARE — Dall'Esecuzione alla Governance

### Progetto C1: SOP Hardware Lifecycle Management

```markdown
<!-- reports/SOP_hardware_lifecycle_v1.md -->
# SOP: Hardware Lifecycle Management

## Responsabilità
- **Owner**: IT Asset Manager
- **Executor**: Sysadmin / IT Support
- **Review**: IT Manager + CFO (piano refresh annuale)

## Fase 1 — Inventario Continuativo
- Ogni nuovo asset riceve asset_tag prima del deploy
- Dati registrati: modello, S/N, data acquisto, costo, garanzia, EOSL vendor
- Fonte garanzie: portale vendor (Dell TechDirect, HPE iLO, Cisco SmartNet)
- Strumento: GLPI o asset_lifecycle.json + script tracker

## Fase 2 — Alert Automatico (mensile)
- Eseguire script b1_asset_tracker.py ogni primo del mese
- Ticket GLPI creato automaticamente per ogni alert 90 giorni prima
- Alert 30 giorni: escalation automatica IT Manager

## Fase 3 — Valutazione Refresh
Per ogni asset con alert EOSL/garanzia < 6 mesi:
1. Eseguire calcolo TCO comparativo (script b2_tco_refresh.py)
2. Se refresh vantaggioso: richiedere quotazioni (RFQ a 3 vendor)
3. Inserire nel piano refresh 5 anni con stima CAPEX
4. Presentare al CFO entro 2 mesi dall'alert

## Fase 4 — Smaltimento Conforme
### 4a. Cancellazione Dati
- Livello minimo: NIST Clear (shred 3-pass) per riuso interno
- Livello standard: NIST Purge (ATA Secure Erase / NVMe Crypto Erase) per dismissione
- Livello massimo: distruzione fisica per dati riservati
- **Certificato obbligatorio** per ogni disco dismesso (script b6_sanitize_disk.sh)

### 4b. Smaltimento Fisico (D.Lgs 49/2014)
1. Compilare FIR (4 copie)
2. Contattare gestore RAEE autorizzato (verificare su albogestoririfiuti.it)
3. Trasporto a carico del gestore
4. Ricevere FIR controfirmato entro 90 giorni
5. Conservare certificati minimo 5 anni

### 4c. Donazione
- Verificare funzionamento asset
- Cancellazione dati livello Purge
- DDT con causale "Donazione"
- Registrazione contabile e vantaggi fiscali (D.Lgs 117/2017)

## Archiviazione Documenti
| Documento | Dove | Retention |
|---|---|---|
| Certificati sanitizzazione | /lifecycle_lab/certificates/ + GLPI | 5 anni |
| FIR RAEE | GLPI allegato + cartella fisica | 5 anni |
| Contratti vendor | GLPI asset → documenti | Durata contratto +2 anni |
| Piano refresh | reports/refresh_plan_5y.csv + Git | Indefinito |
```

---

### Progetto C2: Dashboard Grafana Lifecycle

```python
# scripts/c2_grafana_lifecycle_dashboard.py
# Crea dashboard Grafana per visualizzare aging flotta hardware

import requests
import json

GRAFANA_URL  = 'http://192.168.56.10:3000'
GRAFANA_USER = 'admin'
GRAFANA_PASS = 'admin'

# Dashboard JSON per aging flotta (mock — in prod usa dati reali da GLPI API)
dashboard = {
    "title":  "Hardware Lifecycle Overview",
    "uid":    "hw-lifecycle-01",
    "panels": [
        {
            "title":   "Asset per Anno Acquisto",
            "type":    "barchart",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
            "options": {"legend": {"displayMode": "list"}},
        },
        {
            "title":   "Garanzie in Scadenza (prossimi 180 giorni)",
            "type":    "table",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        },
        {
            "title":   "Asset oltre 5 anni (% flotta)",
            "type":    "gauge",
            "gridPos": {"h": 6, "w": 6, "x": 0, "y": 8},
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "steps": [
                            {"color": "green", "value": 0},
                            {"color": "yellow", "value": 20},
                            {"color": "red", "value": 40},
                        ]
                    }
                }
            },
        },
    ],
    "schemaVersion": 38,
    "version":       1,
}

try:
    resp = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        json={"dashboard": dashboard, "overwrite": True, "folderId": 0},
        timeout=10,
    )
    resp.raise_for_status()
    url = resp.json().get('url', '')
    print(f"✅ Dashboard creata: {GRAFANA_URL}{url}")
except requests.exceptions.ConnectionError:
    print("⚠️  Grafana non raggiungibile — la struttura dashboard è corretta, verificare il servizio")
```

---

### Progetto C3: ITAD — IT Asset Disposition Policy

Il documento di policy formalizza il processo ITAD per conformità ISO 27001, GDPR e D.Lgs 49/2014.

```markdown
<!-- reports/ITAD_policy_v1.md -->
# IT Asset Disposition (ITAD) Policy — v1.0

## Scopo
Definire il processo di dismissione sicura e conforme di tutti i dispositivi IT
che contengono o hanno contenuto dati, garantendo protezione GDPR, conformità
RAEE e recupero del valore residuo.

## Ambito
Tutti i dispositivi IT dell'organizzazione: server, storage, switch, router,
firewall, notebook, desktop, smartphone, tablet, stampanti MFP, UPS con
schede di gestione, dispositivi IoT con storage locale.

## Requisiti Prima della Dismissione

### 1. De-inventario (obbligatorio)
- Stato asset aggiornato a "Retired" in GLPI/tracker
- Data dismissione registrata
- Motivo dismissione documentato (fine vita, sostituzione, guasto irreparabile)

### 2. Cancellazione Dati (obbligatorio per ogni dispositivo con storage)

| Destinazione Asset | Livello Richiesto | Metodo |
|---|---|---|
| Riuso interno | Clear | shred 3-pass o ATA Secure Erase |
| Donazione | Purge | ATA Secure Erase Enhanced o NVMe Crypto |
| Vendita/Refurbish | Purge | come sopra |
| Smaltimento esterno | Purge | come sopra |
| Dati riservati/segreti | Destroy | Trituratore fisico certificato DIN 66399 |

Certificato di cancellazione firmato richiesto per ogni dispositivo.

### 3. Smaltimento Fisico

**Opzione A — Restituzione vendor** (One-to-One al momento del nuovo acquisto):
Comunicare al vendor al momento dell'ordine; ritiro incluso o a basso costo.

**Opzione B — Gestore RAEE autorizzato**:
- Verificare iscrizione Albo Nazionale Gestori Ambientali
- Compilare FIR, organizzare ritiro
- Conservare FIR controfirmato

**Opzione C — Donazione**:
- Solo per asset funzionanti < 7 anni
- Purge dati obbligatorio
- DDT + convenzione con ente beneficiario

## Conservazione Documentazione
| Documento | Retention |
|---|---|
| Certificati sanitizzazione dati | 5 anni |
| FIR (Formulario Identificazione Rifiuto) | 5 anni |
| Certificati distruzione fisica | 5 anni |
| DDT donazioni | 5 anni |
| Registro ITAD completo | Indefinito |

## KPI di Conformità
- % asset dismessi con certificato sanitizzazione: target 100%
- % FIR ricevuti entro 90 giorni: target 100%
- Audit annuale inventario fisico vs CMDB: delta < 2%
```

---

## Checklist di Validazione Lab

- [ ] **A1**: Ciclo 7 fasi lifecycle spiegato, motivazione gestione lifecycle chiara
- [ ] **A2**: Cicli di refresh per tipo hardware memorizzati con relative motivazioni
- [ ] **A3**: Distinzione EOL/EOSL/EOVS compresa e applicata agli asset di esempio
- [ ] **A4**: Calcolo ROI refresh comprensivo di TCO mantenimento vs refresh
- [ ] **A5**: Tre livelli NIST SP 800-88 (Clear/Purge/Destroy) e quando usarli
- [ ] **A6**: Procedura RAEE con FIR e sanzioni per smaltimento illegale
- [ ] **B1**: Script tracker creato, alert 3 asset identificati correttamente
- [ ] **B2**: Calcolo TCO comparativo eseguito, risparmio annuo quantificato
- [ ] **B3**: Query EOL (mock API o reale) completata con output strutturato
- [ ] **B4**: Piano refresh 5 anni generato con CAPEX per anno e CSV esportato
- [ ] **B5**: Sanitizzazione disco lab eseguita con shred, verifica hex completata
- [ ] **B6**: Script sanitizzazione con log eseguito, certificato generato in `/certificates/`
- [ ] **B7**: Report lifecycle automatico generato con tabella garanzie scadute e EOSL risk
- [ ] **C1**: SOP Hardware Lifecycle documentata con fasi, responsabilità, archiviazione
- [ ] **C2**: Dashboard Grafana struttura definita (con o senza connessione)
- [ ] **C3**: ITAD Policy v1.0 scritta con ambito, requisiti, KPI di conformità

---

## Appendice A: Checklist Pre-Dismissione Asset

```
☐ Asset registrato come "Retired" in CMDB/GLPI
☐ Data dismissione e motivo documentati
☐ Backup finale effettuato (se applicabile)
☐ Licenze software disinstallate/trasferite
☐ Active Directory: account computer rimosso / spostato in OU Retired
☐ Cancellazione dati completata (livello appropriato)
☐ Certificato sanitizzazione firmato e archiviato
☐ Etichetta "SANITIZZATO" applicata fisicamente al dispositivo
☐ FIR compilato (se smaltimento RAEE)
☐ Gestore RAEE autorizzato contattato e schedulato
☐ FIR controfirmato ricevuto e archiviato (entro 90 giorni)
```

---

## Appendice B: Vendor Lifecycle Resources

| Vendor | Tool/Portale | Note |
|---|---|---|
| Cisco | [EoX API](https://developer.cisco.com) + cisco.com/go/eos-eol | API EoX per query programmatica per S/N |
| HPE | [HPE InfoSight](https://infosight.hpe.com) | Tracking automatico EOL asset registrati |
| Dell | [Dell TechDirect](https://techdirect.dell.com) | Warranty status + EOL per service tag |
| Lenovo | [Lenovo DCSC](https://datacentersupport.lenovo.com) | Product Discontinuance Notices |
| NetApp | [NetApp HWU](https://hwu.netapp.com) | Hardware Universe con EOL/EOSL |
| Cisco (multi) | Cisco Migration Incentive Program | Rebate per refresh da EOL a nuovi |

---

## Appendice C: Normativa di Riferimento

| Norma | Ambito | Contenuto Rilevante |
|---|---|---|
| **D.Lgs 49/2014** | RAEE Italia | Smaltimento RAEE, FIR, sanzioni, categorie R1-R5 |
| **D.Lgs 152/2006** | TUA (Testo Unico Ambientale) | Sanzioni generali rifiuti, art. 255-256 |
| **GDPR Reg. 2016/679** | Protezione dati | Art. 5 (integrità), Art. 25 (privacy by design) |
| **D.Lgs 117/2017** | Codice Terzo Settore | Deducibilità donazioni hardware |
| **ISO/IEC 27001:2022** | SGSI | A.5.9 inventario, A.7.10 supporti, A.7.14 smaltimento |
| **NIST SP 800-88 Rev.1** | Media Sanitization | Clear / Purge / Destroy methodology |
| **ISO/IEC 21964** (DIN 66399) | Distruzione fisica | Classi E-1 → E-7 per diversi tipi dato |
| **CSRD Dir. 2022/2464** | ESG Reporting | Carbon footprint HW, ciclo vita, report sostenibilità |

---

## Riferimenti

1. ITIL 4 — *IT Asset Management Practice Guide* (Axelos, 2020)
2. ISO/IEC 27001:2022 — Annex A.5.9, A.7.10, A.7.14
3. NIST SP 800-88 Rev. 1 — *Guidelines for Media Sanitization* (2014)
4. D.Lgs 49/2014 — Attuazione direttiva 2012/19/UE (RAEE)
5. DIN 66399 / ISO/IEC 21964 — Distruzione supporti dati
6. Cisco EoX API Documentation — developer.cisco.com
7. HPE Lifecycle Policy — support.hpe.com
8. Albo Nazionale Gestori Ambientali — albogestoririfiuti.it
9. CSRD (Direttiva UE 2022/2464) — Sostenibilità e carbon footprint HW
10. GDPR (Regolamento UE 2016/679) — Art. 5, 25, 83
