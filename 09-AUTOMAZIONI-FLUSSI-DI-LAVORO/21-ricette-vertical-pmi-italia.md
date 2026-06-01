---
corso: "Automazioni e Flussi di Lavoro"
fase: "3 — Piattaforme"
modulo: 21
titolo: "Ricette di Automazione per PMI Italiana — Casi Pratici Verticali"
versione: "FatturaPA 1.2.2, SDI 2024+"
livello: "competent"
prerequisiti: ["Moduli 01-20", "Concetti fatturazione elettronica italiana", "GDPR basics"]
obiettivi:
  - "Automatizzare il ciclo fattura elettronica SDI: generazione XML, firma, invio e gestione ricevute"
  - "Implementare conservazione digitale a norma AGID con retention 10 anni e integrita verificabile"
  - "Configurare workflow GDPR-compliant per PMI: consenso, breach notification entro 72h, registro trattamenti"
  - "Integrare vendor italiani (Aruba, Fatture in Cloud, Fattura24) con n8n e API REST"
  - "Progettare automazioni per scontrino elettronico e corrispettivi telematici verso Agenzia Entrate"
tag: [pmi-italia, fattura-elettronica, sdi, gdpr, agid, conservazione-digitale, corrispettivi]
---

# Ricette di Automazione per PMI Italiana — Casi Pratici Verticali

> **Obiettivi di apprendimento**
> 1. Automatizzare il ciclo fattura elettronica SDI: generazione XML, firma, invio e gestione ricevute
> 2. Implementare conservazione digitale a norma AGID con retention 10 anni e integrita verificabile
> 3. Configurare workflow GDPR-compliant per PMI: consenso, breach notification entro 72h, registro trattamenti
> 4. Integrare vendor italiani (Aruba, Fatture in Cloud, Fattura24) con n8n e API REST
> 5. Progettare automazioni per scontrino elettronico e corrispettivi telematici verso Agenzia Entrate

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 5 — Governance · Modulo 21
> **Prerequisiti:** Moduli 01-20.
> **Obiettivi:** ricette concrete per PMI italiana: fattura elettronica SDI, scontrino elettronico, integrazione Agenzia Entrate, conservazione digitale, GDPR.
> **Tempo:** lettura 60 min · lab 240 min
> **Livello:** competent
> **Ultimo aggiornamento:** 2026-05-24

## Idee guida

1. **Fattura elettronica SDI = obbligo.** Tutti i B2B/B2C italiani. SDI accetta solo XML firmato.
2. **Conservazione digitale a norma = 10 anni.** AGID-conformity richiesto.
3. **GDPR e tema centrale.** Anche per PMI, breach reporting entro 72h.
4. **Integrazioni ecosistema italiano.** Aruba, Register.it, Fattura24, Fatture in Cloud, Bluenext.
5. **Lingua e cultura: ricette devono parlare italiano + slang business locale.**

---

## Indice

1. [Panoramica](#panoramica)
2. [Concetti Fondamentali](#concetti-fondamentali)
3. [Guida Pratica: ricette per settore](#guida-pratica-ricette-per-settore)
   - [Commercialista / Studio Tributario](#commercialista--studio-tributario)
   - [E-commerce (Shopify / WooCommerce)](#e-commerce-shopify--woocommerce)
   - [Studio Medico / Sanitario](#studio-medico--sanitario)
   - [Agenzia Comunicazione / Marketing](#agenzia-comunicazione--marketing)
   - [Industria / Manifatturiero (Industria 4.0)](#industria--manifatturiero-industria-40)
   - [HR / Risorse Umane](#hr--risorse-umane)
   - [Studi Professionali (Avvocati / Architetti)](#studi-professionali-avvocati--architetti)
4. [Configurazione](#configurazione)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [Tabella Riepilogativa ROI](#tabella-riepilogativa-roi)
8. [Riferimenti](#riferimenti)

---

## Panoramica

La PMI italiana è un terreno di automazione completamente diverso da quello che immagina chi lavora per multinazionali tech. Lo studio commercialista di Verona con quattro persone, l'agenzia di comunicazione di Padova con dodici dipendenti, il piccolo manifatturiero veneto da quaranta operai e tre impiegati amministrativi: hanno tutti una cosa in comune che cambia radicalmente le scelte di automazione — non hanno un team IT interno, non hanno budget per progetti SaaS da decine di migliaia di euro all'anno, ma hanno un volume di lavoro ripetitivo che brucia ore preziose ogni settimana.

Il contesto normativo italiano impone vincoli specifici che molti tutorial internazionali ignorano completamente:

- **Fatturazione elettronica obbligatoria** verso il Sistema di Interscambio (SDI). Dal 2024 anche per i forfettari oltre soglia. Significa che ogni ricetta che tocca le fatture deve gestire XML-PA, formati FatturaPA 1.2.2 e successivi, conservazione decennale.
- **GDPR rigoroso** con interpretazione del Garante particolarmente severa su PEC, sanitario, marketing diretto. Data residency UE quasi sempre richiesta nei contratti B2B.
- **Tessera Sanitaria** per studi medici, con scadenza annuale spese sanitarie.
- **Industria 4.0** (oggi Transizione 5.0) con incentivi fiscali condizionati a interconnessione e attestazione di interoperabilità — leva potente per giustificare investimenti in automazione produttiva.
- **CCNL e UNIEMENS** per chiunque tocchi payroll o HR.
- **F24, scadenze fiscali** con calendario serrato e penalità severe per tardività.

Le ricette di questo documento sono progettate per essere implementabili **in giornata** da un consulente freelance o da un IT manager interno con un setup minimo: tipicamente n8n self-hosted su una VPS Hetzner o Aruba da 5-15 €/mese, oppure Make/Zapier per chi preferisce zero infrastruttura. Per ogni ricetta forniamo: scenario realistico, trigger, step concreti, strumenti consigliati con alternative paid, tempo risparmiato stimato su una PMI tipo (10-50 dipendenti), costo piattaforma, e ROI annuo orientativo.

L'obiettivo non è elencare cose teoricamente possibili: è mostrare automazioni che ripagano il primo mese e continuano a generare valore composto.

---

## Concetti Fondamentali

**Stack tipo PMI italiana** (€5-50/mese totali per piattaforme):

- **Orchestratore workflow**: n8n self-hosted (€5/mese VPS Hetzner CX11, gratuito unlimited workflow), Make Free/Core (€0-9/mese, 1.000-10.000 ops), Zapier Starter (€19/mese, 750 task), Power Automate (incluso in molte licenze M365 Business).
- **Storage documentale**: Google Drive (15GB gratis, €1,99/mese 100GB), OneDrive (incluso M365), Nextcloud self-hosted.
- **Comunicazione team**: Slack (gratis fino a 90gg storia messaggi), Telegram Bot (gratis, ottimo per alert), Microsoft Teams (incluso M365).
- **Notifiche cliente**: Twilio per SMS (€0,05-0,07 per SMS Italia), WhatsApp Business API via 360dialog/MessageBird, email transazionale Brevo/Mailgun (gratis fino a 300/giorno).
- **Database / CRM**: Airtable (gratis fino a 1.000 record), Notion Free, HubSpot CRM Free, Pipedrive (€14/mese), Postgres self-hosted incluso nella stessa VPS di n8n.
- **Form**: Tally Free, Typeform (€25/mese), Google Forms gratuito, Microsoft Forms incluso M365.
- **Firma elettronica**: Aruba PEC e Aruba Firma (~€36/anno), DocuSign (€10/mese), Yousign (~€9/mese).

**Considerazioni GDPR ricorrenti per ogni ricetta**:

1. **DPA (Data Processing Agreement)** firmato con ogni vendor che tocca dati personali. Gratis e standard per la quasi totalità dei vendor SaaS seri.
2. **Data residency UE**: privilegiare istanze EU dei provider (n8n self-hosted in Italia/UE risolve nativamente). Per servizi USA con SCC, valutare caso per caso e documentare in ROPA.
3. **Minimizzazione**: non passare nei workflow dati personali oltre lo stretto necessario. Mai inviare CF completi a Telegram, mai loggare email plaintext.
4. **Retention**: definire TTL per dati nei sistemi di automazione (logs, payload webhook). 30-90 giorni tipico, salvo obblighi specifici.
5. **Audit log**: registrare chi ha eseguito quale workflow, quando, su quali dati. Necessario per ROPA e per gestire eventuali richieste di accesso/cancellazione.

**Pattern di error handling** comune a tutte le ricette:

- **Branch errore esplicito** in n8n/Make su ogni nodo di integrazione esterna.
- **Notifica al team IT** (Slack/Telegram) in caso di errore: workflow name, step fallito, payload sintetico, link a log completo.
- **Retry esponenziale** (3-5 tentativi, 1s/5s/30s/2min/5min) per errori transient (HTTP 5xx, timeout).
- **Dead Letter Queue** per richieste che falliscono tutti i retry: salvataggio su tabella DB o canale dedicato per riprocessing manuale.
- **Idempotenza**: ogni workflow deve poter essere rieseguito senza creare duplicati. Usare ID esterni (es. ID fattura SDI) come chiave di dedup.

---

## Guida Pratica: ricette per settore

### Commercialista / Studio Tributario

#### Ricetta 1.1 — Importazione fatture XML SDI da PEC

**Scenario**: lo studio riceve quotidianamente decine di fatture passive dei clienti via PEC (canale SDI). Oggi il commercialista o segretaria scarica manualmente, controlla, importa nel gestionale (Fatture in Cloud, Aruba Fatturazione, Fattura24), notifica il cliente.

**Trigger**: nuova email PEC contenente allegato `.xml` o `.xml.p7m`.

**Step workflow** (n8n):

1. **IMAP node** verso casella PEC (Aruba/Legalmail/Aruba: server `imaps.pec.<provider>.it:993`). Filtro `subject:contains "fattura elettronica"` o `from:notifica.sdi@pec.fatturapa.it`.
2. **Filter node**: solo email con allegato `.xml` o `.xml.p7m`.
3. **Code node JS** per estrarre allegato. Se `.p7m`, usare `node-forge` per estrarre payload firmato.
4. **XML Parse node** per parsing FatturaPA. Estrarre: CedentePrestatore (P.IVA, denominazione), CessionarioCommittente, NumeroDocumento, Data, ImportoTotaleDocumento, righe dettaglio.
5. **HTTP Request node** verso API Fatture in Cloud: `POST /c/{company_id}/issued_documents` con payload mappato.
6. **Switch node** sul cliente (CessionarioCommittente.IdFiscaleIVA): instradare verso il company_id corretto.
7. **Telegram node**: bot dello studio invia al canale del cliente "Nuova fattura passiva caricata: [fornitore] €[totale] del [data]".
8. **Database node**: log su tabella `fatture_importate(uuid, sdi_id, cliente_id, importo, timestamp)` per dedup e audit.

**Strumenti**:
- n8n self-hosted (€5/mese).
- API Fatture in Cloud (incluso piano Pro €18/mese).
- Bot Telegram (gratuito).

**Alternative paid**: Make + integrazione Aruba Fatturazione (€9-29/mese).

**Tempo risparmiato**: ~3 minuti per fattura. Studio con 30 clienti × 20 fatture/mese = 1.800 minuti = **30 ore/mese**.

**Costo piattaforma**: ~€25/mese all-in.

**ROI annuo**: 30h × 12 × €35/h (costo orario segretaria amministrativa) = **€12.600/anno** risparmiati, vs ~€300 di piattaforma.

#### Ricetta 1.2 — Promemoria scadenze F24

**Scenario**: ogni mese ci sono scadenze F24 diverse per ogni cliente (16 del mese tipico per dipendenti, IVA mensile/trimestrale, IRPEF, ecc.). Lo studio rischia penali se manca un promemoria.

**Trigger**: cron giornaliero, esecuzione 08:00.

**Step workflow**:

1. **Postgres query**: SELECT clienti con scadenze F24 nei prossimi 7 giorni.
2. **Loop** sui risultati.
3. **HTTP Request** a Google Calendar API: crea evento "F24 [tipo] cliente [nome] - €[importo]" il giorno della scadenza.
4. **Email node** (SMTP studio): invia al cliente promemoria con dettagli, IBAN per pagamento, allegato modello F24 precompilato (PDF generato da template + dati).
5. **Telegram node**: notifica al canale interno studio con elenco scadenze del giorno.
6. **DB update**: marca scadenza come "promemoria inviato".

**Strumenti**: n8n + Postgres (stessa VPS) + Google Calendar API + SMTP (Brevo).

**Alternative paid**: Zapier (€19/mese) + integrazione Google Calendar.

**Tempo risparmiato**: 5 minuti/cliente/mese × 50 clienti = 250 min/mese ≈ **4 ore/mese**, ma soprattutto evitare anche una sola penale (€100-1.000) ripaga il sistema.

**Costo piattaforma**: ~€10/mese.

**ROI annuo**: 4h × 12 × €40/h + risparmio penali (~€500-2.000/anno) = **€2.420-3.920/anno**.

#### Ricetta 1.3 — Riconciliazione bancaria automatica

**Scenario**: il commercialista riceve estratti conto bancari (CSV/CBI) e deve abbinare ogni movimento a una fattura attiva o passiva. Lavoro lungo e ripetitivo.

**Trigger**: upload manuale CSV o pull automatico da PSD2 API (Banca Sella, Fabrick).

**Step workflow**:

1. **Read CSV node**: parsing estratto conto.
2. **Loop** su ogni movimento.
3. **Code node**: estrazione importo, data, causale, controparte (se presente).
4. **Postgres query**: cerca fattura con importo identico ± 5% e data ± 30 giorni rispetto al movimento.
5. **Switch**:
   - Match unico → marca fattura come "incassata", aggiorna gestionale via API.
   - Match multipli → flag per revisione manuale, notifica Slack.
   - Nessun match → flag come "movimento non riconciliato".
6. **Report node**: a fine batch, email al commercialista con riepilogo (X riconciliati, Y da rivedere).

**Strumenti**: n8n + Postgres + API Fatture in Cloud + Slack.

**Alternative paid**: piattaforme dedicate come Banana, Yokoy, ma costo €50-200/mese.

**Tempo risparmiato**: studio con 200 movimenti/mese × 1 min/movimento = ~3 ore/mese di matching automatico, restano ~20 min/mese per i casi dubbi. **~3,5 ore/mese**.

**Costo piattaforma**: ~€10/mese.

**ROI annuo**: 3,5h × 12 × €45/h = **€1.890/anno**.

---

### E-commerce (Shopify / WooCommerce)

#### Ricetta 2.1 — Ordine → fattura elettronica → DDT → tracking WhatsApp

**Scenario**: e-commerce italiano riceve ordine Shopify, deve generare fattura elettronica SDI (per cliente B2B con P.IVA o per ricevuta verso privato), produrre DDT, comunicare tracking spedizione.

**Trigger**: Webhook Shopify `orders/paid`.

**Step workflow**:

1. **Webhook node** in n8n.
2. **Validate signature** Shopify (`X-Shopify-Hmac-Sha256` con secret app).
3. **Switch node**: B2B (P.IVA presente) vs B2C.
4. **HTTP Request** ad API gestionale (Fatture in Cloud, Aruba): crea documento.
   - B2B: fattura elettronica → invio SDI automatico.
   - B2C: ricevuta + comunicazione corrispettivi telematici (se obbligato).
5. **PDF node**: genera DDT da template HTML + dati ordine.
6. **HTTP Request** a corriere (BRT, GLS, SDA, Poste) per creare spedizione e ottenere `tracking_number`.
7. **WhatsApp Business node** (via 360dialog o Twilio): messaggio cliente "Ciao [nome], il tuo ordine è in spedizione. Tracking: [link]".
8. **Database**: log ordine processato.
9. **Branch errore**: notifica Slack al team operativo con dettaglio.

**Strumenti**: n8n + Fatture in Cloud + corriere API + WhatsApp Business API.

**Alternative paid**: Shopify Flow + plugin Italia (~€30-80/mese).

**Tempo risparmiato**: 5-8 minuti per ordine × 100 ordini/mese = **~10 ore/mese**.

**Costo piattaforma**: n8n €5 + WhatsApp ~€0,05/messaggio × 100 = €10 + gestionale già esistente. Totale ~€15-20/mese incrementali.

**ROI annuo**: 10h × 12 × €25/h = **€3.000/anno**, plus aumento NPS cliente.

#### Ricetta 2.2 — Carrello abbandonato → email recovery sequence

**Scenario**: cliente Shopify aggiunge prodotti al carrello ma non completa checkout. Tasso conversione tipico 30% senza recovery, 50%+ con sequenza ben fatta.

**Trigger**: webhook Shopify `checkouts/create` con `completed_at: null` dopo N minuti.

**Step workflow**:

1. **Webhook** Shopify checkout creato.
2. **Wait node**: 1 ora.
3. **HTTP Request**: verifica se checkout completato (GET `/checkouts/{token}`).
4. **If not completed** → **Email node** sequenza:
   - **Email 1 (1h dopo abbandono)**: "Hai dimenticato qualcosa nel carrello?"
   - Wait 23h. Se ancora non completato → **Email 2 (24h)**: "Ancora pensandoci? Ecco il tuo carrello".
   - Wait 6gg. Se ancora non completato → **Email 3 (7gg)**: "Ultimo sconto del 10% solo per te" + codice univoco.
5. **Loop check** ad ogni step: se l'utente compra, esce dalla sequenza (importante!).
6. **Postgres**: log eventi inviati per cliente, evita re-trigger eccessivi.

**Strumenti**: n8n + Brevo/Mailgun (transactional email gratis fino a 300/giorno).

**Alternative paid**: Klaviyo (~€45-150/mese), Omnisend (~€16+/mese).

**Tempo risparmiato**: setup una tantum 4 ore, poi automatico. **Recovery rate 10-20%** su carrelli abbandonati = **€10.000-50.000/anno** di fatturato recuperato per shop con 100 carrelli/mese a €80 medio.

**Costo piattaforma**: ~€10/mese.

**ROI annuo**: dipende da volume; minimo 10× il costo della piattaforma per qualsiasi shop con >50 carrelli/mese.

#### Ricetta 2.3 — Sincronizzazione magazzino multi-canale

**Scenario**: prodotto venduto su Shopify, Amazon, eBay simultaneamente. Senza sync, rischio di vendere stock già esaurito.

**Trigger**: cron ogni 15 minuti.

**Step workflow**:

1. **HTTP Request Shopify**: GET inventory di tutti i prodotti.
2. **HTTP Request Amazon SP-API**: GET inventory.
3. **HTTP Request eBay**: GET inventory.
4. **Merge node**: confronto stock per SKU.
5. **Code node**: identifica master (es. ERP interno) e calcola delta da propagare.
6. **Update HTTP Request** verso ogni piattaforma con nuovo stock.
7. **Alert se stock < soglia**: notifica Slack/Telegram al magazzino.

**Strumenti**: n8n + API delle 3 piattaforme.

**Alternative paid**: Linnworks, ChannelAdvisor, Sellbrite (€50-300/mese).

**Tempo risparmiato**: evita oversold (~5 oversold/mese × €30 di costo per gestione/rimborso) = **€150/mese** + 3-5 ore/mese di check manuale.

**Costo piattaforma**: ~€5-10/mese.

**ROI annuo**: ~**€3.000-5.000/anno** tra risparmio ore e oversold evitati.

---

### Studio Medico / Sanitario

#### Ricetta 3.1 — Promemoria appuntamento SMS 24h prima

**Scenario**: studio medico/dentistico/fisioterapista. No-show rate tipico 10-20% senza reminder, scende a 3-5% con reminder.

**Trigger**: cron giornaliero alle 18:00.

**Step workflow**:

1. **API gestionale appuntamenti** (Doctolio, MioDottore, Cliniko, Calendly, o foglio Google Sheets): GET appuntamenti del giorno seguente.
2. **Filter**: solo appuntamenti confermati, non già con reminder inviato.
3. **Twilio SMS node**: "Gentile [Nome], ti ricordiamo l'appuntamento di domani [data ora] presso [studio]. Per disdire rispondi NO o chiama [numero]. Studio Dott. [Nome]".
4. **Postgres**: marca reminder inviato.
5. **Webhook Twilio reply**: se cliente risponde NO, marca appuntamento da disdire e notifica reception.

**Disclaimer GDPR**: il consenso al reminder SMS deve essere acquisito all'atto della prenotazione (checkbox modulo) e documentato. Privacy policy aggiornata. Mai mandare dettagli clinici via SMS.

**Strumenti**: n8n + Twilio SMS (€0,07/SMS Italia).

**Alternative paid**: il gestionale stesso spesso include reminder (es. MioDottore), valutare se disponibile.

**Tempo risparmiato**: studio con 30 appuntamenti/giorno = ~600/mese. Riduzione no-show del 10% = 60 appuntamenti recuperati × €50 valore medio = **€3.000/mese di fatturato salvato**.

**Costo piattaforma**: 600 SMS × €0,07 = €42/mese + n8n €5.

**ROI annuo**: ~**€36.000/anno** di fatturato salvato vs ~€600 di costi.

#### Ricetta 3.2 — Modulo consenso GDPR firmato → archivio cifrato → CRM

**Scenario**: nuovo paziente compila modulo consenso trattamento dati e privacy. Va archiviato in modo sicuro e tracciabile per 10+ anni.

**Trigger**: form Tally o Typeform compilato dal paziente.

**Step workflow**:

1. **Webhook Tally**: nuovo modulo.
2. **HTTP Request Yousign/DocuSign**: invio modulo per firma elettronica avanzata (FEA).
3. **Wait webhook completamento firma**.
4. **PDF node**: genera PDF firmato con metadata (timestamp, IP firmatario, hash documento).
5. **Cloud Storage** (Google Drive cifrato lato client con `gcloud kms` o Nextcloud E2EE) → cartella `/consensi/[anno]/[paziente_id]`.
6. **HTTP Request CRM** (HubSpot Free, gestionale studio): aggiorna record paziente con `consenso_gdpr: true, data_consenso: [date], doc_url: [link cifrato]`.
7. **Email paziente**: copia del consenso firmato.
8. **Audit log**: tabella `consensi_log(paziente_id, evento, timestamp, ip)` immutabile.

**Strumenti**: n8n + Tally (free) + Yousign (~€9/mese) + Drive cifrato.

**Alternative paid**: piattaforma sanitaria all-in-one (~€100-300/mese).

**Tempo risparmiato**: 15 min per paziente × 20 nuovi/mese = **5 ore/mese** + drastica riduzione rischio sanzione GDPR (€1.000-100.000+).

**Costo piattaforma**: ~€20/mese.

**ROI annuo**: 5h × 12 × €30/h = **€1.800/anno** + riduzione rischio sanzione.

#### Ricetta 3.3 — Export annuale spese sanitarie Tessera Sanitaria

**Scenario**: ogni gennaio lo studio deve trasmettere tutte le spese sanitarie dell'anno precedente al Sistema Tessera Sanitaria (STS) per la dichiarazione 730 precompilata.

**Trigger**: manuale (eseguito a gennaio) o cron annuale.

**Step workflow**:

1. **Postgres query**: SELECT tutte le ricevute/fatture dell'anno con codice fiscale paziente, importo, data, tipo prestazione.
2. **Code node**: trasformazione in formato XML STS (schema XSD pubblicato dall'Agenzia delle Entrate).
3. **Validation node**: validazione XSD locale prima di invio.
4. **HTTP Request a portale STS**: upload con autenticazione tramite certificato Entratel/Fisconline o tramite API STS (richiede credenziali rilasciate da AdE).
5. **Wait response** + scarica ricevuta esito.
6. **Email al titolare**: "Trasmissione STS [anno] completata. [N] ricevute trasmesse, [N] errori".
7. **Archive**: salva XML inviato + ricevuta in Drive `/sts/[anno]/`.

**Strumenti**: n8n + Postgres + libreria validazione XSD (`libxml2`).

**Alternative paid**: gestionali con STS integrato (~€500-1.500/anno).

**Tempo risparmiato**: 8-16 ore/anno di lavoro manuale critico (errori = sanzioni e disagio pazienti).

**Costo piattaforma**: già incluso in n8n self-hosted.

**ROI annuo**: ~**€500-1.000/anno** + riduzione errori (errori STS = sanzioni AdE).

---

### Agenzia Comunicazione / Marketing

#### Ricetta 4.1 — Lead Facebook Ads → CRM → round-robin → Slack

**Scenario**: agenzia gira campagne lead-gen su Facebook/Instagram per clienti finali (e per sé stessa). Ogni lead va distribuito velocemente al venditore giusto.

**Trigger**: nuovo lead form Facebook (webhook nativo).

**Step workflow**:

1. **Facebook Lead Ads webhook** in n8n.
2. **HTTP Request HubSpot**: cerca contatto esistente (per email).
3. **If not exists** → crea contatto. **If exists** → aggiorna con nuova interazione.
4. **Round-robin assignment**: lookup tabella `venditori` con `last_assigned_at`. Selezione del venditore con timestamp più vecchio. Update timestamp.
5. **HubSpot HTTP**: assegna lead al venditore selezionato.
6. **Slack node**: messaggio nel canale del venditore con riepilogo lead + link diretto HubSpot.
7. **Email node** (SLA 5min): se venditore non risponde entro 1h, alert al team lead.

**Strumenti**: n8n + HubSpot CRM Free + Slack.

**Alternative paid**: Zapier (€19/mese), HubSpot paid plans con automazione nativa (~€45/mese).

**Tempo risparmiato**: distribuzione manuale ~5 min/lead × 50 lead/mese = **~4 ore/mese**, ma soprattutto **lead response time** scende da 2-4 ore a <1 minuto = +30-50% conversion.

**Costo piattaforma**: ~€10/mese (n8n + storage).

**ROI annuo**: 4h × 12 × €40/h + uplift conversione (variabile, tipicamente 3-10× costo) = **€3.000-15.000/anno**.

#### Ricetta 4.2 — Report mensile clienti automatico

**Scenario**: agenzia gestisce 20 clienti, ognuno aspetta report mensile su Google Analytics, Meta Ads, Google Ads. Lavoro che oggi richiede 2-4 ore per cliente.

**Trigger**: cron il 1° del mese alle 09:00.

**Step workflow**:

1. **Loop** sulla tabella clienti.
2. Per ogni cliente:
   - **HTTP GA4 API**: metriche mese precedente (sessions, users, conversions, revenue).
   - **HTTP Meta Ads API**: spesa, impression, click, conversioni.
   - **HTTP Google Ads API**: stesse metriche.
3. **Code node**: aggregazione e calcolo KPI (CAC, ROAS, CTR, etc.).
4. **PDF generation node** (Puppeteer/Chromium su template HTML brandizzato cliente con grafici Chart.js).
5. **Drive upload** in cartella cliente.
6. **Email node**: invio al cliente con PDF allegato e link Drive.
7. **Slack interno**: notifica account manager "Report [cliente] inviato".

**Strumenti**: n8n + API marketing + Puppeteer (su VPS).

**Alternative paid**: AgencyAnalytics (~€60/mese), DashThis (~€39/mese), Whatagraph (~€80/mese).

**Tempo risparmiato**: 3 ore/cliente × 20 clienti = **60 ore/mese**.

**Costo piattaforma**: ~€10/mese (VPS leggermente più potente per Puppeteer).

**ROI annuo**: 60h × 12 × €50/h = **€36.000/anno**.

#### Ricetta 4.3 — Onboarding nuovo cliente

**Scenario**: cliente firma contratto, va creata cartella Drive, canale Slack, board ClickUp/Notion, email kickoff, calendar invite per kickoff meeting.

**Trigger**: documento DocuSign firmato (webhook).

**Step workflow**:

1. **Webhook DocuSign** envelope completed.
2. **Parse** dati cliente da fields del documento.
3. **Drive API**: crea cartella `/clienti/[nome_cliente]` con sottocartelle standard (Contratti, Brief, Asset, Output, Report).
4. **Slack API**: crea canale `#cli-[nome]`, invita team account + manager + cliente (single-channel guest).
5. **ClickUp API**: duplica template board "Onboarding Cliente" e personalizza con nome.
6. **Notion**: crea pagina cliente in DB clienti con link a tutto.
7. **Calendar API**: crea evento kickoff meeting (proposta 3 slot).
8. **Email node** al cliente: "Benvenuto! Ecco il tuo kit onboarding. Link: [drive] [slack] [meeting]".
9. **Slack interno**: "Nuovo cliente onboardato: [nome]. Account: [@manager]".

**Strumenti**: n8n + DocuSign + Drive + Slack + ClickUp + Notion + Google Calendar.

**Alternative paid**: Zapier multi-step (~€49/mese), Process Street (~€100/mese).

**Tempo risparmiato**: ~90 min per onboarding × 4 nuovi clienti/mese = **6 ore/mese** + standardizzazione (zero "abbiamo dimenticato di creare X").

**Costo piattaforma**: ~€10-20/mese.

**ROI annuo**: 6h × 12 × €50/h = **€3.600/anno**.

---

### Industria / Manifatturiero (Industria 4.0)

#### Ricetta 5.1 — Allarme macchina (PLC/MQTT) → Telegram + ticket Jira

**Scenario**: piccolo manifatturiero veneto con 15 macchine CNC connesse via OPC-UA / MQTT. Quando una macchina va in allarme, il manutentore deve essere allertato immediatamente e il fermo va tracciato (per OEE e per garanzia Industria 4.0).

**Trigger**: messaggio MQTT su topic `factory/+/alarm`.

**Step workflow**:

1. **MQTT Trigger node** n8n sottoscritto a broker (Mosquitto/EMQX self-hosted o HiveMQ Cloud).
2. **Parse payload**: `{machine_id, alarm_code, severity, timestamp}`.
3. **HTTP Request** a knowledge base interna: lookup `alarm_code` → descrizione + checklist troubleshoot.
4. **Switch sulla severity**:
   - HIGH → Telegram al canale manutenzione + chiamata vocale via Twilio al reperibile.
   - MEDIUM → Telegram + ticket Jira automatico assegnato a turno corrente.
   - LOW → solo log + ticket schedulato per fine turno.
5. **Postgres insert** in tabella `eventi_macchina` per analytics OEE.
6. **Update Grafana annotation** sul dashboard di linea.

**Strumenti**: n8n + Mosquitto MQTT + Postgres + Telegram + Jira + Grafana.

**Alternative paid**: piattaforme MOM/MES (~€500-5.000/mese, sproporzionate per PMI).

**Tempo risparmiato**: riduzione tempo medio risposta da 30 min a 5 min × 20 fermi/mese = **~8 ore/mese di produzione recuperata** + tracciabilità per attestazione I4.0 (decine di migliaia in credito d'imposta).

**Costo piattaforma**: ~€20/mese (VPS + broker).

**ROI annuo**: 8h × 12 × €100/h (costo orario fermo macchina con manodopera) = **€9.600/anno** + sblocco/protezione credito imposta I4.0.

#### Ricetta 5.2 — Report OEE giornaliero → email direzione

**Scenario**: direttore di stabilimento vuole ricevere ogni mattina alle 07:00 il report OEE (Overall Equipment Effectiveness) del giorno precedente, con grafici per linea, top 3 fermi, andamento settimanale.

**Trigger**: cron giornaliero 06:30.

**Step workflow**:

1. **Postgres query**: aggregazione metriche OEE giorno precedente per linea (Availability, Performance, Quality).
2. **Grafana API**: snapshot dashboard via `/render/d/<dashboard_id>` con `from=now-1d&to=now&width=1200&height=800` → PNG.
3. **PDF node**: composizione PDF con sintesi testuale + screenshot dashboard + tabella top fermi.
4. **Email node**: invio a `direzione@azienda.it` + cc a `produzione@azienda.it`.
5. **Slack canale management**: stesso PDF + sintesi 3 righe.

**Strumenti**: n8n + Postgres + Grafana + Brevo/SMTP.

**Alternative paid**: piattaforme analytics MES dedicate (~€200-500/mese).

**Tempo risparmiato**: 30-60 min/giorno × 22 giorni = **~15 ore/mese** + reattività decisionale direzione.

**Costo piattaforma**: ~€10/mese.

**ROI annuo**: 15h × 12 × €40/h = **€7.200/anno**.

#### Ricetta 5.3 — Ordine cliente → BOM esplosa → richiesta fornitore → tracking

**Scenario**: ordine cliente arrivato. Va esplosa la distinta base, verificata disponibilità materie prime, lanciato ordine al fornitore per quanto manca, tracciata consegna.

**Trigger**: nuovo ordine inserito nel gestionale (webhook o cron poll).

**Step workflow**:

1. **HTTP gestionale**: GET dettagli ordine cliente.
2. **Postgres BOM lookup**: ricava distinta base per ogni codice prodotto in ordine.
3. **Loop sui componenti**:
   - **Postgres magazzino**: verifica giacenza.
   - **If sotto soglia o insufficiente** → aggiungi a `lista_acquisti`.
4. **Group by fornitore**.
5. **HTTP Request al portale EDI fornitore** o **email auto** con RDA (richiesta d'acquisto).
6. **Postgres**: traccia ordine fornitore con `expected_delivery_date`.
7. **Cron daily**: check stato consegne. Se ritardo → alert + email fornitore.

**Strumenti**: n8n + Postgres + integrazioni fornitori (mix di API/EDI/email).

**Alternative paid**: ERP completo (~€5.000-50.000 setup + €100-500/mese).

**Tempo risparmiato**: ~2 ore/ordine × 30 ordini/mese = **60 ore/mese**.

**Costo piattaforma**: ~€20/mese.

**ROI annuo**: 60h × 12 × €35/h = **€25.200/anno**.

---

### HR / Risorse Umane

#### Ricetta 6.1 — Onboarding nuovo dipendente

**Scenario**: HR deve provisionare account Google Workspace, Slack, email kit benvenuto, assegnare buddy.

**Trigger**: form Tally compilato da HR con dati nuovo assunto + data inizio.

**Step workflow**:

1. **Webhook Tally**.
2. **Wait until** data inizio assunto - 1 giorno.
3. **Google Admin API**: crea utente Workspace, password temporanea, gruppi default (`@all`, `@dept-x`).
4. **Slack API**: invita a workspace, aggiungi a canali default per dipartimento.
5. **Drive API**: crea cartella personale `/dipendenti/[nome]` condivisa con HR e manager.
6. **Email kit benvenuto**: PDF brandizzato con info azienda, contatti utili, link manuale dipendenti.
7. **ClickUp/Asana**: crea task di onboarding (con checklist firmare contratto, formazione GDPR, etc.) assegnato a HR + buddy.
8. **Calendar invite** primo meeting con manager + buddy lunch.
9. **Slack notification** al canale team: "Benvenuto a [nome] che inizia il [data]!".

**Strumenti**: n8n + Google Admin SDK + Slack + Drive + ClickUp.

**Alternative paid**: BambooHR, Personio, Factorial (~€5-12/dipendente/mese).

**Tempo risparmiato**: ~3 ore per onboarding × 3 nuovi/mese (PMI 30 dip., turnover 10%) = **9 ore/mese**.

**Costo piattaforma**: ~€10/mese.

**ROI annuo**: 9h × 12 × €40/h = **€4.320/anno**.

#### Ricetta 6.2 — Richiesta ferie → approvazione → calendario + payroll

**Scenario**: dipendente richiede ferie. Manager approva. Si aggiorna calendario condiviso e gestionale paghe.

**Trigger**: form ferie compilato (Tally / Microsoft Forms).

**Step workflow**:

1. **Webhook form**: dati richiesta (dipendente, date, tipo: ferie/permesso/malattia).
2. **HTTP Request gestionale HR**: verifica saldo ferie disponibile.
3. **If insufficient** → email dipendente con rifiuto auto + saldo attuale.
4. **If sufficient** → **Slack DM al manager** con bottoni "Approva" / "Rifiuta".
5. **Webhook Slack interactive** alla risposta:
   - Approva → **Calendar API**: crea evento "Ferie [nome]" su calendario team. **Gestionale API**: scala giorni dal saldo. **Email dipendente** conferma.
   - Rifiuta → **Email dipendente** con motivo (testo libero da Slack).
6. **Audit log** tabella `richieste_ferie`.

**Strumenti**: n8n + Tally + Slack interactive + Google Calendar + gestionale HR (anche solo Sheet).

**Alternative paid**: BambooHR/Personio ferie module incluso.

**Tempo risparmiato**: ~10 min per richiesta × 30 richieste/mese (PMI 30 dip.) = **5 ore/mese** HR + manager.

**Costo piattaforma**: ~€10/mese.

**ROI annuo**: 5h × 12 × €35/h = **€2.100/anno**.

#### Ricetta 6.3 — Survey clima trimestrale → sentiment → report HR

**Scenario**: HR vuole tracciare trimestralmente il clima aziendale con survey anonimo.

**Trigger**: cron trimestrale (1° gennaio/aprile/luglio/ottobre).

**Step workflow**:

1. **Email broadcast** a tutti i dipendenti con link Typeform anonimo (10 domande Likert + 1 testo libero).
2. **Webhook Typeform** ad ogni risposta.
3. **OpenAI / Claude API node**: analisi sentiment del testo libero (positive/neutral/negative + tematiche emerse).
4. **Postgres insert** risposta + sentiment.
5. **Cron 14 giorni dopo invio**: chiusura survey, generazione report.
6. **PDF report**: aggregazione Likert + word cloud temi + grafici trend rispetto a trimestri precedenti.
7. **Email a HR Director + CEO**: PDF + sintesi.

**Strumenti**: n8n + Typeform + OpenAI/Claude API + Postgres.

**Alternative paid**: Officevibe (~€4/dipendente/mese), CultureAmp (più caro).

**Tempo risparmiato**: ~8 ore/trimestre di analisi manuale = **~32 ore/anno**.

**Costo piattaforma**: ~€15/mese (Typeform + LLM API ~€2/survey).

**ROI annuo**: 32h × €40/h = **€1.280/anno** + valore strategico insight clima.

---

### Studi Professionali (Avvocati / Architetti)

#### Ricetta 7.1 — Timesheet automatico → fatturazione cliente

**Scenario**: studio legale o di architettura traccia ore lavorate per cliente. A fine mese, generazione fattura proforma basata su ore × tariffa.

**Trigger**: cron mensile + integrazione Toggl/Harvest.

**Step workflow**:

1. **Toggl/Harvest API**: GET tutte le entries del mese precedente con tag cliente + project.
2. **Group by cliente**: somma ore × tariffa per cliente.
3. **HTTP gestionale fatturazione**: crea documento proforma con dettaglio righe (data, descrizione, ore, tariffa).
4. **PDF generation**: proforma con logo studio + dettaglio attività.
5. **Email cliente**: "In allegato proforma del mese di [mese]. Per conferma rispondere a questa mail entro [data]".
6. **Webhook reply parser** (o follow-up manuale): alla conferma, conversione in fattura definitiva con invio SDI.

**Strumenti**: n8n + Toggl/Harvest + gestionale + email.

**Alternative paid**: Clio (legal-specific, ~€60/utente/mese), Bill4Time.

**Tempo risparmiato**: 30 min/cliente × 20 clienti = **10 ore/mese**.

**Costo piattaforma**: ~€20/mese (Toggl Premium €9/utente + n8n).

**ROI annuo**: 10h × 12 × €80/h (tariffa orari studio) = **€9.600/anno**.

#### Ricetta 7.2 — Scadenzario pratiche → reminder cliente

**Scenario**: studio gestisce decine di pratiche con scadenze legali rigide (ricorsi, deposito atti, udienze). Una scadenza persa = malpractice grave.

**Trigger**: cron giornaliero 07:00.

**Step workflow**:

1. **Notion DB query** (o Airtable): SELECT pratiche con `prossima_scadenza` nei prossimi 30 giorni.
2. **For each**:
   - **Slack DM all'avvocato responsabile** se scadenza ≤ 7 giorni.
   - **Email cliente** se scadenza ≤ 14 giorni e tipo "documenti da fornire".
   - **Calendar event** auto-creato se non esiste.
3. **Critical alert**: se scadenza ≤ 2 giorni e task non ancora marcato "in lavorazione" → alert anche al senior partner.
4. **Postgres log**: tracking azioni eseguite.

**Strumenti**: n8n + Notion/Airtable + Slack + Calendar + email.

**Alternative paid**: software legali italiani (Cliens, Lextel) con scadenzario integrato (~€40-100/utente/mese).

**Tempo risparmiato**: check manuale ~30 min/giorno = **10 ore/mese**, ma soprattutto **rischio malpractice ridotto a quasi zero** (potenziali risparmi su sanzioni/contenziosi nell'ordine delle decine di migliaia di euro).

**Costo piattaforma**: ~€15/mese.

**ROI annuo**: 10h × 12 × €60/h = **€7.200/anno** + de-risking malpractice.

---

## Configurazione

### Stack base raccomandato per uno studio/PMI

**VPS Hetzner CX22** (€4,50/mese, Falkenstein DE — UE):
- Ubuntu 24.04 LTS.
- Docker + Docker Compose.
- Nginx Proxy Manager per HTTPS automatico (Let's Encrypt).
- Volumi persistenti per dati n8n e Postgres.

**Stack docker-compose.yml minimo**:

```yaml
version: "3.8"
services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports: ["5678:5678"]
    environment:
      - N8N_HOST=n8n.studio.example.com
      - N8N_PROTOCOL=https
      - N8N_ENCRYPTION_KEY=<chiave-32-char-random>
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=<password>
      - GENERIC_TIMEZONE=Europe/Rome
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on: [postgres]

  postgres:
    image: postgres:16-alpine
    restart: always
    environment:
      - POSTGRES_DB=n8n
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=<password>
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  n8n_data:
  pg_data:
```

**Backup**:
- Postgres: `pg_dump` notturno via cron, push su Backblaze B2 (€0,005/GB/mese) o S3 Glacier.
- Volumi n8n: snapshot Hetzner settimanale (€3/mese opzione).
- Test restore trimestrale obbligatorio.

**Hardening minimo**:
- Firewall UFW: solo 22, 80, 443 aperti.
- SSH: chiavi only, no password, fail2ban.
- n8n dietro reverse proxy con Basic Auth aggiuntivo se non usato N8N_USER_MANAGEMENT.
- `N8N_ENCRYPTION_KEY` salvato anche in 1Password / Bitwarden offsite.

### Pattern setup ricorrenti

**OAuth credentials**: configura una volta per provider (Google, Microsoft, Stripe, ecc.) e riusa in tutti i workflow. Vedi documento companion `20-oauth2-flows-refresh-token-automazione.md` per dettagli flow.

**Webhook security**: ogni endpoint webhook esposto deve validare signature/HMAC del provider:
- Shopify: `X-Shopify-Hmac-Sha256` con app secret.
- Stripe: `Stripe-Signature` con webhook signing secret.
- Telegram: token nell'URL + IP allowlist Telegram.
- Generic: HMAC-SHA256 con secret condiviso.

**Rate limiting verso API esterne**: implementare ovunque, anche se l'API non lo impone esplicitamente. Pattern token bucket nel codice n8n con Redis o tabella Postgres come backing store.

---

## Best Practices

**Architettura**:
- Una VPS unica per studio piccolo va bene fino a ~500-1.000 esecuzioni workflow/giorno. Oltre, considerare separazione DB / worker queue mode di n8n.
- Mai eseguire workflow direttamente in produzione senza test in staging. Anche un workflow "banale" che invia email a clienti, se mal costruito, può generare 10.000 email duplicate in 2 minuti.
- Versionare i workflow esportati in JSON in un repo Git privato. Tag per rilascio, branch per dev/prod.

**GDPR operativo**:
- Tenere ROPA aggiornato con elenco tutti i workflow e dati trattati per ogni cliente.
- DPA firmato con ogni vendor (n8n, Make, Zapier, OpenAI/Anthropic, Twilio, ecc.).
- Procedura documentata per gestire richieste di accesso/cancellazione dati ricevute dai clienti finali.
- Mai inviare CF, dati sanitari, dati finanziari completi a Telegram/Slack: usare ID interni e link a sistemi che richiedono autenticazione.

**Operational excellence**:
- Health check endpoint monitorato (UptimeRobot gratis fino a 50 monitor) su n8n.
- Alert su workflow falliti più di N volte in M minuti.
- Dashboard interna (Grafana o anche Notion) con KPI: workflow totali, esecuzioni/giorno, error rate, latenza media.
- Code review reciproca dei workflow critici (anche in studio piccolo: il commercialista guarda quello che ha fatto il consulente esterno).

**Costi**:
- Iniziare con free tier di tutto, upgrade solo quando volumi lo giustificano economicamente.
- Self-hosting n8n vs SaaS: break-even ~50 €/mese di consumo SaaS (n8n cloud parte da €20/mese, Make €9/mese 10k ops).
- LLM costs: usare modelli più piccoli (Haiku, GPT-4o-mini) per task semplici (sentiment, categorizzazione). Modelli grandi solo per task che li richiedono davvero.

---

## Troubleshooting

**Workflow n8n falliscono random con `ECONNRESET`**: tipicamente API lente o flaky. Aggiungere retry nodo con backoff esponenziale. Aumentare `N8N_DEFAULT_BINARY_DATA_MODE=filesystem` se workload con file grandi.

**PEC IMAP non scarica nuove email**: verificare che la casella PEC abbia abilitato accesso IMAP (alcuni provider lo disabilitano di default). Aruba: pannello Webmail → Impostazioni → Account → Abilita IMAP. Verificare anche che la casella non sia piena (limite 1GB tipico).

**SDI rifiuta XML fattura**: errore comune `00200 - File non conforme al formato`. Validare XML con schema XSD ufficiale dell'AdE prima di invio. Errore `00400 - Dati anagrafici cedente non validi`: verificare P.IVA con servizio AdE `verificaPIVA`.

**Telegram bot non riceve messaggi**: webhook Telegram richiede HTTPS valido (no self-signed). Verifica con `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`. Se `last_error_message` popolato, mostra il problema esatto.

**Webhook Shopify firma sempre invalida**: assicurarsi di usare il body **raw** per il calcolo HMAC, non il JSON parsed. In n8n, il nodo Webhook ha opzione "Raw Body" da abilitare.

**Reminder SMS Twilio bloccati in IT**: alcune carrier IT bloccano numeri non registrati per A2P. Soluzione: registrare un Sender ID alfanumerico (es. "Studio") presso Twilio per traffico Italia. Tempi: 1-2 settimane.

**Google API error `invalid_grant`** ricorrente: refresh token revocato o scaduto. Rieseguire flow OAuth interattivo. Vedere documento companion OAuth per dettagli rotation.

**Errore "rate limit" su Meta Ads API**: limiti per token, non per account. Distribuire chiamate su token diversi (uno per cliente) o aumentare intervallo cron.

---

## Tabella Riepilogativa ROI

PMI tipo: 10-50 dipendenti, settore corrispondente.

| Settore | Ricetta | Tempo risparmiato/mese | Costo piattaforma/mese | ROI annuo stimato |
|---------|---------|------------------------|------------------------|-------------------|
| Commercialista | Import fatture SDI da PEC | 30h | €25 | €12.600 |
| Commercialista | Promemoria F24 | 4h + risparmio penali | €10 | €2.420-3.920 |
| Commercialista | Riconciliazione bancaria | 3,5h | €10 | €1.890 |
| E-commerce | Ordine → fattura → DDT → tracking | 10h | €15-20 | €3.000+ |
| E-commerce | Carrello abbandonato | n/a (uplift conversion) | €10 | €10.000-50.000 |
| E-commerce | Sync magazzino multi-canale | 5h + oversold evitati | €5-10 | €3.000-5.000 |
| Sanitario | Reminder SMS appuntamenti | n/a (no-show ridotto) | €50 | €36.000 |
| Sanitario | Consenso GDPR firmato | 5h + de-risking | €20 | €1.800+ |
| Sanitario | Export STS annuale | 8-16h/anno | incluso | €500-1.000 |
| Marketing | Lead Facebook → CRM round-robin | 4h + uplift conversion | €10 | €3.000-15.000 |
| Marketing | Report mensile clienti | 60h | €10 | €36.000 |
| Marketing | Onboarding nuovo cliente | 6h | €10-20 | €3.600 |
| Industria | Allarme PLC/MQTT → Telegram | 8h + I4.0 | €20 | €9.600+ |
| Industria | Report OEE giornaliero | 15h | €10 | €7.200 |
| Industria | Ordine → BOM → fornitore | 60h | €20 | €25.200 |
| HR | Onboarding dipendente | 9h | €10 | €4.320 |
| HR | Richiesta ferie | 5h | €10 | €2.100 |
| HR | Survey clima trimestrale | 32h/anno | €15 | €1.280 |
| Studi prof. | Timesheet → fatturazione | 10h | €20 | €9.600 |
| Studi prof. | Scadenzario pratiche | 10h + de-risking malpractice | €15 | €7.200+ |

**Totale ROI cumulato per PMI multi-funzione che adotta 5-7 ricette mirate**: tipicamente **€30.000-80.000/anno** netti, contro costo piattaforma totale **€50-150/mese** (€600-1.800/anno).

Il break-even di un setup completo è tipicamente **mese 1-2**. Da lì in poi, valore composto per ogni ricetta che continua a girare.

---

## Riferimenti

**Normativa italiana rilevante**:
- Provvedimento AdE 30/04/2018 e successivi — Fatturazione elettronica via SDI.
- D.Lgs. 196/2003 + Reg. UE 2016/679 — Codice Privacy + GDPR.
- Provvedimento AdE 31/07/2015 — Sistema Tessera Sanitaria.
- Legge di Bilancio 2024 (commi su Transizione 5.0) — Crediti d'imposta interconnessione macchinari.
- D.Lgs. 152/1997 — Privacy in ambito sanitario.

**Documentazione provider tecnici**:
- n8n docs (`docs.n8n.io`) — nodi, espressioni, hosting.
- Make Help Center — scenarios, ops, error handling.
- Shopify API reference — webhooks, GraphQL Admin API.
- Microsoft Graph documentation — Outlook, Teams, SharePoint.
- Google Workspace Admin SDK.
- Stripe API reference + webhooks.

**Provider italiani**:
- Fatture in Cloud API documentation.
- Aruba PEC IMAP/SMTP guide.
- Aruba Fatturazione Elettronica API.
- AgID — Sistema di Interscambio specifiche tecniche.
- Sistema Tessera Sanitaria — manuale tecnico XSD.

**Tools**:
- Twilio (SMS, voice, WhatsApp).
- 360dialog / MessageBird (WhatsApp Business API ufficiale).
- Brevo / Mailgun (email transazionale).
- HiveMQ Cloud / EMQX (MQTT broker).
- Grafana (dashboard OEE).
- HubSpot CRM Free.
- Tally / Typeform (form builder).
- Yousign / DocuSign (firma elettronica).

**Risorse community italiane**:
- Forum n8n Italia (ufficiali su `community.n8n.io`).
- Gruppo Telegram "Automazione PMI Italia" (community informale).
- Webinar AssoSoftware su digitalizzazione studi.

---

## Esercizi

1. **Lab — fattura elettronica SDI.** Workflow che genera XML conforme, firma digitalmente, invia a SDI sandbox; gestisce ricevute MC/RC/NS/NE.
2. **Lab — onboarding cliente PMI.** Form anagrafica → CRM → contratto Aruba Sign → fattura prima rata SDI → benvenuto email con DKIM.
3. **Stretch — GDPR data subject access request.** Workflow che riceve richiesta cliente, raccoglie dati da N sistemi, genera export PDF cifrato, invia con scadenza 30g.

## Auto-valutazione

1. SDI: cosa accetta?
2. Conservazione digitale: requisiti AGID.
3. GDPR breach: tempo reporting?
4. Vendor italiani principali per fatturazione.

## Collegamenti incrociati

- Modulo 24 (NEW) — `24-audit-logging-compliance.md`: audit GDPR.
- Vedi `00-BIBLIOGRAFIA.md`: AGID, SDI, fatturapa.

## Glossario locale

| Termine | Definizione |
|---|---|
| **SDI** | Sistema di Interscambio Agenzia Entrate. |
| **Fattura elettronica** | XML conforme schema Agenzia Entrate. |
| **MC/RC/NS/NE** | Ricevute SDI: mancata consegna, ricevuta, scarto, esito negativo. |
| **AGID** | Agenzia per l'Italia Digitale. |
| **Conservazione digitale** | Storage 10 anni a norma (AgID). |
| **DPO** | Data Protection Officer (GDPR). |
| **Aruba PEC / Aruba Sign** | Servizi italiani PEC e firma digitale. |
| **Fatture in Cloud / Fattura24** | SaaS italiani per fatturazione. |

---

## Letture e Riferimenti

- Agenzia delle Entrate — Fatturazione elettronica: specifiche tecniche. https://www.fatturapa.gov.it/it/norme-e-regole/documentazione-fattura-elettronica/
- Agenzia delle Entrate — Corrispettivi telematici. https://www.agenziaentrate.gov.it/portale/web/guest/corrispettivi-telematici
- AGID — Linee guida sulla conservazione dei documenti informatici. https://www.agid.gov.it/it/piattaforme/conservazione
- Garante Privacy — GDPR: guida all'applicazione del regolamento. https://www.garanteprivacy.it/regolamentoue
- Aruba — Fatturazione elettronica API. https://developers.aruba.it/
- Fatture in Cloud — API Reference. https://developers.fattureincloud.it/
- Bocchiola, Nicola. *Fatturazione elettronica e conservazione digitale*. Maggioli Editore, 2023. — Normativa e implementazione per PMI.
- Finocchiaro, Giusella. *GDPR e trattamento dei dati personali*. Zanichelli, 2021. — Compliance privacy per imprese italiane.
