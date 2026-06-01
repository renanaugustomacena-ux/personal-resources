# Cablaggio Strutturato — Standard TIA-568, Categorie, Organizzazione Rack

> **Modulo 18** · **Tempo:** 120 min · **Aggiornamento:** 2026-05-22

## Idee guida

1. **TIA-568.2-D (2024) e standard corrente.** Cat 6A per nuovi installs.
2. **Rack organization: doc + label + slack < 10cm.** Mai cabli sciolti.
3. **Patch panel = single point of change.** Mai modifiche cablaggio dietro racks.
4. **Color coding standard: TIA-606.** Identifica ruolo cavo a colpo d'occhio.


## Indice

1. [Panoramica](#panoramica)
2. [Concetti Fondamentali](#concetti-fondamentali)
   - [Cos'e il Cablaggio Strutturato](#cose-il-cablaggio-strutturato)
   - [Standard di Riferimento](#standard-di-riferimento)
   - [Sottosistemi del Cablaggio Strutturato](#sottosistemi-del-cablaggio-strutturato)
   - [Modello di Canale e Permanent Link](#modello-di-canale-e-permanent-link)
3. [Categorie Cavo Rame](#categorie-cavo-rame)
   - [Tabella Comparativa Categorie](#tabella-comparativa-categorie)
   - [Schermature UTP/FTP/STP/SFTP](#schermature-utpftpstpsftp)
   - [Impedenza Caratteristica e Parametri Elettrici](#impedenza-caratteristica-e-parametri-elettrici)
   - [Pinout T568A vs T568B](#pinout-t568a-vs-t568b)
   - [Tecniche di Terminazione Rame](#tecniche-di-terminazione-rame)
   - [Test e Certificazione Rame](#test-e-certificazione-rame)
   - [Alien Crosstalk e Considerazioni Cat 6A](#alien-crosstalk-e-considerazioni-cat-6a)
4. [Fibra Ottica](#fibra-ottica)
   - [Principi di Propagazione Ottica](#principi-di-propagazione-ottica)
   - [Multimodale OM1-OM5](#multimodale-om1-om5)
   - [Singolomodo OS1/OS2](#singolomodo-os1os2)
   - [Connettori e Polishing](#connettori-e-polishing)
   - [Tecniche di Giunzione: Fusione e Meccanica](#tecniche-di-giunzione-fusione-e-meccanica)
   - [Test OTDR e Insertion Loss](#test-otdr-e-insertion-loss)
   - [Link Budget Calculation](#link-budget-calculation)
5. [Pathway and Spaces — TIA-569](#pathway-and-spaces--tia-569)
   - [Locali Tecnici: MDF e IDF](#locali-tecnici-mdf-e-idf)
   - [Condotti, Canaline e Passaggi](#condotti-canaline-e-passaggi)
   - [Separazione da Impianti Elettrici](#separazione-da-impianti-elettrici)
6. [Guida Pratica](#guida-pratica)
   - [Organizzazione Rack 19"](#organizzazione-rack-19)
   - [Cable Management Avanzato](#cable-management-avanzato)
   - [Etichettatura TIA-606-C](#etichettatura-tia-606-c)
   - [Grounding e Bonding — TIA-607](#grounding-e-bonding--tia-607)
   - [PoE Power over Ethernet](#poe-power-over-ethernet)
7. [Configurazione Tipica PMI](#configurazione-tipica-pmi)
8. [Progettazione per Data Center — TIA-942](#progettazione-per-data-center--tia-942)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Domande Frequenti (Q&A)](#domande-frequenti-qa)
12. [Esercizi e Laboratori](#esercizi-e-laboratori)
13. [Riferimenti](#riferimenti)
14. [Glossario](#glossario)

---

## Panoramica

Il cablaggio strutturato e l'infrastruttura passiva su cui si appoggia tutto il resto: rete dati, telefonia VoIP, building automation, controllo accessi, videosorveglianza IP, sistemi industriali. A differenza del cablaggio ad-hoc — punto a punto, posato all'occorrenza, senza una topologia coerente — il cablaggio strutturato e un sistema gerarchico, modulare e standardizzato che separa nettamente il livello fisico (cavi, prese, patch panel, rack) dai dispositivi attivi che lo utilizzano (switch, router, telefoni, server).

La differenza pratica e enorme. Un cablaggio ad-hoc tipicamente vive cinque o sei anni prima di diventare ingestibile: nessuno sa quale cavo va dove, le modifiche si accumulano senza documentazione, ogni intervento e una piccola archeologia. Un cablaggio strutturato, posato correttamente secondo gli standard, ha una vita utile di **15-25 anni**: l'infrastruttura passiva sopravvive a tre o quattro generazioni di apparati attivi. Il costo iniziale e superiore del 20-40%, ma il TCO su quindici anni e drasticamente inferiore, soprattutto considerando il tempo risparmiato in moves/adds/changes (MAC) e in troubleshooting.

Il cablaggio strutturato e regolato da un corpus di standard internazionali maturi, principalmente la famiglia **ANSI/TIA-568** negli Stati Uniti, lo **ISO/IEC 11801** a livello internazionale e l'**EN 50173** in Europa. Questi documenti definiscono la topologia fisica, le categorie di cavo, le distanze massime, i parametri di test, l'etichettatura e la documentazione. Aderire allo standard significa garantire prestazioni prevedibili, interoperabilita con qualsiasi vendor di apparati attivi e capacita di evolvere senza dover rifare l'infrastruttura.

Questa guida copre in dettaglio gli standard di riferimento, le categorie di cavo rame e fibra, le tecniche di organizzazione rack 19", l'etichettatura sistematica secondo TIA-606-C, le procedure di certificazione con strumenti professionali, il grounding e bonding secondo TIA-607, il design dei locali tecnici secondo TIA-569, le implicazioni del Power over Ethernet ad alta potenza sul dimensionamento dell'impianto e la progettazione per data center secondo TIA-942. Il pubblico di riferimento e il sistemista o network engineer che progetta o mantiene il cablaggio di una PMI italiana o di una sede aziendale di medie dimensioni.

### Perche Investire nel Cablaggio Strutturato

Un errore comune nelle PMI italiane e considerare il cablaggio come voce di costo trascurabile, delegata all'elettricista generico. Questo approccio genera tre tipologie di problemi ricorrenti:

**Problemi di prestazione**: cavi Cat 5e da 15 anni non reggono 10 Gigabit; patch cord economici non certificati degradano il link; terminazioni fatte male generano NEXT elevato e perdita di pacchetti.

**Problemi di manutenibilita**: rack senza cable management diventano "nidi di spaghetti" dove ogni intervento rischia di scollegare qualcosa; assenza di etichettatura costringe a inseguire cavi nei controsoffitti; documentazione inesistente rende impossibile il troubleshooting efficiente.

**Problemi di conformita**: gli standard di certificazione ISO 27001, la normativa NIS2, i requisiti assicurativi per la business continuity richiedono documentazione dell'infrastruttura fisica. Senza certificazione e documentazione, l'azienda e esposta in caso di audit.

---

## Concetti Fondamentali

### Cos'e il Cablaggio Strutturato

Un sistema di cablaggio strutturato e un'architettura gerarchica composta da elementi standardizzati che permettono di interconnettere qualsiasi presa utente con qualsiasi apparato attivo, attraverso una serie di patch flessibili. Il principio cardine e la **separazione** tra cablaggio fisso (orizzontale, dorsale) e cablaggio mobile (patch cord), in modo che le modifiche di configurazione si limitino alla movimentazione dei patch nei rack, senza mai toccare i cavi posati nei muri o nei pavimenti.

I sottosistemi previsti dallo standard TIA-568 sono sei:

1. **Entrance Facility (EF):** punto di ingresso dei servizi esterni (fibra ISP, doppino telefonico storico, link wireless point-to-point). Comprende il punto di demarcazione con l'operatore, la protezione contro sovratensioni e il raccordo verso la rete interna.
2. **Equipment Room (ER):** locale tecnico che ospita gli apparati centrali (core switch, server, centralino). In edifici grandi e spesso un locale dedicato con climatizzazione, UPS, controllo accessi, pavimento sopraelevato.
3. **Backbone Cabling:** dorsale che collega ER ai vari Telecommunications Room (TR), tipicamente in fibra ottica. La dorsale puo essere anche intra-building (tra piani) o inter-building (tra edifici nel campus).
4. **Telecommunications Room / Telecommunications Enclosure (TR/TE):** armadi di piano o di zona dove terminano i cavi orizzontali. In edifici piccoli coincide con l'ER.
5. **Horizontal Cabling:** cavi che vanno dal patch panel del TR alle prese utente (Telecommunications Outlet, TO), distanza massima 90 metri rame + 10 metri patch. E il sottosistema piu esteso e costoso.
6. **Work Area (WA):** zona utente, con presa TO e patch cord verso il dispositivo.

La regola dei 90+10 metri e tassativa per il cablaggio orizzontale rame: massimo 90 metri di cavo "permanent link" tra patch panel e presa, piu fino a 10 metri totali di patch cord (lato rack + lato utente). Superare questi limiti invalida la garanzia prestazionale dello standard ed espone a problemi di insertion loss, NEXT degradato e riduzione del data rate utile.

### Standard di Riferimento

Il cablaggio strutturato professionale si fonda su un insieme di standard che vanno conosciuti per nome e per scopo:

- **ANSI/TIA-568.0-E** (General Requirements): requisiti generali del cablaggio telecom strutturato per edifici commerciali.
- **ANSI/TIA-568.1-E** (Commercial Building Cabling Standard): topologia, distanze, sottosistemi.
- **ANSI/TIA-568.2-E** (Balanced Twisted-Pair Components): specifiche dei componenti rame, definizioni Cat 5e/6/6A/8.
- **ANSI/TIA-568.3-E** (Optical Fiber Components): specifiche fibra OM1-OM5, OS1/OS2, connettori.
- **ANSI/TIA-569-E** (Pathways and Spaces): cavidotti, condotti, locali tecnici, distanze di sicurezza dai cavi elettrici.
- **ANSI/TIA-606-C** (Administration): identificazione, etichettatura, documentazione, schemi.
- **ANSI/TIA-607-D** (Generic Telecommunications Bonding and Grounding): messa a terra e bonding dei sistemi telecom.
- **ANSI/TIA-942-C** (Telecommunications Infrastructure Standard for Data Centers): cablaggio specifico per data center, con i livelli di affidabilita Rated-1/2/3/4.
- **ISO/IEC 11801-1:2017** (Generic Cabling for Customer Premises): controparte internazionale, definisce le classi di link Class D (Cat 5e), E (Cat 6), EA (Cat 6A), F (Cat 7), FA (Cat 7A), I/II (Cat 8.1/8.2).
- **EN 50173** (Information Technology — Generic Cabling Systems): standard europeo CENELEC, allineato a ISO/IEC 11801.
- **EN 50174** (parte 1, 2, 3): installazione e pratica di posa, parte importante per gli installatori italiani.
- **IEEE 802.3bz**: NBASE-T, definisce 2.5GBASE-T e 5GBASE-T su Cat 5e/6 fino a 100 m.
- **TIA TSB-184-A**: linee guida per PoE su cablaggio strutturato, fattori di derating.
- **TIA TSB-162-A**: raccomandazioni per la posa di cablaggio Cat 6A, alien crosstalk.

Nei capitolati italiani si trovano spesso riferimenti misti: TIA-568 per le specifiche di link, EN 50174 per le regole di posa, EN 50173 per la classificazione delle prestazioni. Cio non e un problema: gli standard sono compatibili e si rinforzano a vicenda.

### Sottosistemi del Cablaggio Strutturato

In una sede tipica si trova questa gerarchia:

```
Entrance Facility (EF)
        |
   ISP / WAN (fibra operatore, punto di demarcazione)
        |
Equipment Room (ER) ---- Core Switch / Server Room
        |
   Backbone (fibra OS2 monomodale + multimodale OM4)
        |
Telecommunications Room piano 1 (TR1)
        |
Cablaggio orizzontale Cat 6A (max 90m permanent link)
        |
Work Area: presa TO + patch cord 3-5m + dispositivo
```

In edifici piccoli (sede unica, fino a 30-50 prese) i sottosistemi possono coincidere: ER e TR sono lo stesso armadio. In sedi multi-piano o multi-edificio, la dorsale diventa critica e si pianifica con ridondanza geografica (due percorsi fisici diversi, anche se entrambi in fibra).

**Dorsale intra-building (tra piani)**: tipicamente fibra OM4 multimodale per distanze fino a 300 m (sufficiente per qualsiasi edificio) con capacita 10G-100G. Ridondanza con almeno due percorsi verticali separati fisicamente (scale diverse, cavedi diversi).

**Dorsale inter-building (tra edifici)**: fibra OS2 singolomodo per distanze fino a diversi km. Posa in cavidotto interrato con protezione meccanica (tubo HDPE corrugato 50/63 mm, pozzetti di ispezione ogni 60-80 m, raggio di curvatura minimo nei pozzetti). In alternativa, fibra aerea su catenaria in acciaio, ma soggetta a danni meteo e impatto visivo.

### Modello di Canale e Permanent Link

Lo standard TIA-568 definisce due modelli di test per la conformita del cablaggio:

**Permanent Link (PL)**: dal connettore sul patch panel (escluso il patch cord lato rack) al connettore nella presa utente (escluso il patch cord lato utente). Lunghezza massima 90 m. E il modello standard per la certificazione di nuovi impianti perche misura solo il cablaggio fisso, eliminando la variabilita dei patch cord.

**Channel**: da un capo all'altro, includendo patch cord lato rack e patch cord lato utente. Lunghezza massima 100 m (90 m permanent link + 10 m totali di patch cord). E il modello "end-to-end" usato per verifiche operative e diagnostica.

La distinzione e importante perche:
- La certificazione di un nuovo impianto usa Permanent Link
- La diagnostica di un link problematico usa Channel
- I parametri di pass/fail sono diversi per PL e Channel (il Channel ha soglie piu rilassate per compensare i patch cord)

```
Channel Model (100m totale):
[Apparato]--[Patch 5m]--[PP]====[Permanent Link 90m]====[TO]--[Patch 5m]--[Dispositivo]
                              ^                              ^
                        connettore PP                    connettore TO

Permanent Link Model (90m):
                         [PP]====[Permanent Link 90m]====[TO]
                         ^    solo cavo fisso posato       ^
```

---

## Categorie Cavo Rame

### Tabella Comparativa Categorie

Le categorie definiscono le prestazioni elettriche del cavo balanced twisted-pair. La numerazione e progressiva: categorie superiori supportano frequenze piu alte e quindi data rate maggiori.

| Categoria | Frequenza | Data Rate | Distanza max | Standard | Stato attuale |
|-----------|-----------|-----------|--------------|----------|---------------|
| **Cat 3** | 16 MHz | 10 Mbps | 100 m | TIA-568 (storico) | Obsoleto, solo fonia legacy |
| **Cat 5** | 100 MHz | 100 Mbps | 100 m | TIA-568 (storico) | Obsoleto, deprecato 2001 |
| **Cat 5e** | 100 MHz | 1 Gbps | 100 m | TIA-568.2 | Legacy ma diffuso, rifare in nuovo |
| **Cat 6** | 250 MHz | 1 Gbps (10G fino 55m) | 100 m / 55 m | TIA-568.2 | Maturo, usato in ristrutturazioni |
| **Cat 6A** | 500 MHz | 10 Gbps | 100 m | TIA-568.2 | **Standard PMI moderne** |
| **Cat 7** | 600 MHz | 10 Gbps | 100 m | ISO/IEC 11801 (Class F) | Non riconosciuto TIA, raro in Italia |
| **Cat 7A** | 1000 MHz | 10 Gbps (40G fino 50m teorico) | 100 m | ISO/IEC 11801 (Class FA) | Marginale |
| **Cat 8** (8.1/8.2) | 2000 MHz | 25/40 Gbps | 30 m | TIA-568.2 | Datacenter top-of-rack only |

Il consiglio operativo per un nuovo cablaggio in PMI italiana nel 2026 e: **Cat 6A schermato (F/UTP o U/FTP) per l'orizzontale, fibra OM4 + OS2 per la dorsale**. Cat 6A regge 10 Gbps su 100 metri e copre tutto il ciclo di vita prevedibile dell'edificio. Cat 6 e ancora accettabile in piccole sedi senza prospettiva 10G, ma il differenziale di costo a metri e marginale (~15-20%).

Cat 8 ha senso solo nei data center per collegamenti top-of-rack switch-to-server entro i 30 metri: per qualsiasi distanza superiore si va in fibra. Cat 7/7A sono diffusi in Germania e nordeuropa (tradizione di standardizzazione ISO/IEC) ma rari in Italia, dove i progettisti seguono di solito la nomenclatura TIA.

**NBASE-T (IEEE 802.3bz)**: standard del 2016 che definisce 2.5GBASE-T e 5GBASE-T su cablaggio Cat 5e/6 esistente fino a 100 m. Permette di sfruttare cablaggio gia installato per velocita intermedie, utile per AP WiFi 6/6E che superano 1 Gbps. Non e un sostituto per Cat 6A in nuove installazioni, ma un'opzione per infrastrutture legacy.

### Schermature UTP/FTP/STP/SFTP

La nomenclatura delle schermature e standardizzata da ISO/IEC 11801 con la sintassi `XX/YY-TP`:

- `XX` = schermo complessivo del cavo (U=unshielded, F=foil, S=braid, SF=foil+braid).
- `YY` = schermo individuale di ogni coppia (U=unshielded, F=foil).

Le combinazioni piu comuni:

- **U/UTP** (Unshielded/Unshielded Twisted Pair): nessuno schermo. Economico, flessibile, suscettibile a EMI. Cat 5e/6 tipico.
- **F/UTP** (Foil/UTP): foglio di alluminio attorno alle quattro coppie, nessuno schermo individuale. Buon compromesso costo/performance per Cat 6A.
- **U/FTP**: nessuno schermo complessivo, ma ogni coppia schermata individualmente con foglio. Tipico Cat 6A "PiMF" (Pair in Metal Foil). Eccellente contro alien crosstalk.
- **S/FTP** (Braid + foglio per coppia): schermo a treccia esterno + foglio per coppia. Cat 6A/7 di alta gamma. Massima protezione EMI.
- **SF/UTP**: foglio + treccia esterni, coppie non schermate. Marginale.

**Quando serve schermatura.** In ambienti con forte EMI — vicinanze a inverter industriali, motori trifase, cabine di trasformazione MT/BT, centri elaborazione con alta densita di apparati — la schermatura e obbligatoria per evitare alien crosstalk e interferenze. In un ufficio standard, U/UTP Cat 6A funziona benissimo. In capannoni industriali, accanto a quadri elettrici, sotto plafoni con illuminazione fluorescente vecchia generazione, S/FTP e la scelta sicura.

Attenzione: il cavo schermato **richiede** una messa a terra corretta del rack e del patch panel (TIA-607-D). Schermatura non collegata a terra e peggio che nessuna schermatura, perche lo schermo diventa un'antenna che capta rumore senza scaricarlo.

**Guida alla scelta pratica per ambiente:**

| Ambiente | Schermatura raccomandata | Motivazione |
|----------|--------------------------|-------------|
| Ufficio standard | U/UTP o F/UTP | EMI bassa, costo contenuto |
| Ufficio open space alta densita | F/UTP o U/FTP | Alien crosstalk tra bundle densi |
| Capannone industriale | S/FTP | Motori, inverter, EMI elevata |
| Ospedale | S/FTP | Apparecchiature medicali, EMI mista |
| Data center | U/FTP o S/FTP | Alta densita cavi, PoE elevato |
| Esterno (posa interrata) | S/FTP con guaina PE | Protezione meccanica e EMI |

### Impedenza Caratteristica e Parametri Elettrici

Per comprendere davvero perche un cavo Cat 6A funziona e uno Cat 5e no a 10 Gbps, serve conoscere i parametri elettrici fondamentali:

**Impedenza caratteristica (Z₀)**: 100 Ω ± 15% per tutte le categorie TIA-568. L'impedenza e determinata dalla geometria del cavo (distanza tra conduttori, diametro conduttore, dielettrico). Variazioni di impedenza lungo il percorso causano riflessioni (return loss elevato).

**Insertion Loss (Attenuazione)**: perdita di potenza del segnale in dB. Cresce linearmente con la lunghezza e approssimativamente con la radice quadrata della frequenza. A 500 MHz (Cat 6A), l'insertion loss massimo per 90 m e circa 33.8 dB.

**NEXT (Near-End Crosstalk)**: accoppiamento di segnale da una coppia trasmittente a una coppia ricevente, misurato all'estremita vicina al trasmettitore. E il parametro critico per Ethernet full-duplex su twisted pair, dove tutte e 4 le coppie trasmettono e ricevono simultaneamente.

**ACR-F (Attenuation to Crosstalk Ratio Far-end)**: rapporto tra FEXT e insertion loss, indica il margine di rumore al lato ricevente. Deve essere positivo (segnale > rumore) a tutte le frequenze operative.

**Return Loss**: segnale riflesso verso il trasmettitore, causato da disadattamento di impedenza (giunzioni, piegature, terminazioni imperfette). Aumenta con la frequenza. Soglia minima Cat 6A: 14 dB a 500 MHz.

**Delay Skew**: differenza di tempo di propagazione tra le quattro coppie. Critico per Gigabit Ethernet e superiori perche i dati vengono trasmessi su tutte e 4 le coppie simultaneamente e riassemblati al ricevitore: se una coppia arriva in ritardo di >45 ns, il decoder fallisce.

**Alien Crosstalk (AXT)**: diafonia tra cavi diversi nello stesso bundle. E il parametro che differenzia Cat 6A da Cat 6: Cat 6 non specifica limiti per AXT, Cat 6A si. Motivo per cui Cat 6 regge 10G solo fino a 55 m (bundle corti dove AXT e basso) mentre Cat 6A regge 100 m.

### Pinout T568A vs T568B

Gli standard T568A e T568B definiscono l'ordine dei conduttori nel connettore RJ-45 8P8C. Le due convenzioni differiscono solo per lo scambio delle coppie 2 e 3 (verde e arancione):

```
T568A (pin 1-8):
  Pin 1: Bianco/Verde      (coppia 3, tip)
  Pin 2: Verde             (coppia 3, ring)
  Pin 3: Bianco/Arancione  (coppia 2, tip)
  Pin 4: Blu               (coppia 1, ring)
  Pin 5: Bianco/Blu        (coppia 1, tip)
  Pin 6: Arancione         (coppia 2, ring)
  Pin 7: Bianco/Marrone    (coppia 4, tip)
  Pin 8: Marrone           (coppia 4, ring)

T568B (pin 1-8):
  Pin 1: Bianco/Arancione  (coppia 2, tip)
  Pin 2: Arancione         (coppia 2, ring)
  Pin 3: Bianco/Verde      (coppia 3, tip)
  Pin 4: Blu               (coppia 1, ring)
  Pin 5: Bianco/Blu        (coppia 1, tip)
  Pin 6: Verde             (coppia 3, ring)
  Pin 7: Bianco/Marrone    (coppia 4, tip)
  Pin 8: Marrone           (coppia 4, ring)
```

**Quale scegliere?** T568B e prevalente negli Stati Uniti e nella prassi commerciale; T568A e raccomandato dal governo USA per nuovi impianti e diffuso in alcuni paesi europei. **La regola e: scegli una convenzione e mantienila in tutto l'impianto**. Mischiare T568A e T568B in un permanent link crea un crossover involontario che, su Gigabit Auto-MDIX moderno, di solito funziona — ma rende la documentazione confusa e crea problemi con apparati legacy o con tester che assumono pinout consistente.

In Italia la prassi prevalente nelle PMI e T568B, allineata alla maggior parte dei manuali Cisco e Juniper. Documenta la scelta nel capitolato e riportala su ogni patch panel etichettato.

**Crossover vs straight cable.** Storicamente i cavi crossover (T568A da un lato, T568B dall'altro) servivano per collegare due dispositivi dello stesso tipo (PC-PC, switch-switch). Con **Auto-MDIX**, presente su tutti gli switch Gigabit dal 2003 in poi, l'incrocio avviene automaticamente nel PHY: un cavo straight funziona in qualsiasi combinazione. I crossover sono di fatto obsoleti, ma alcuni apparati industriali o legacy 100Base-TX possono ancora richiederli.

### Tecniche di Terminazione Rame

La terminazione e il momento critico: un cavo Cat 6A perfetto, terminato male, diventa un link Cat 5e degradato. Le tecniche principali sono:

**Keystone Jack (presa utente)**: terminazione a impatto (punch-down) con utensile a molla (Fluke D914, Harris D-914, Krone LSA). Il conduttore viene inserito nel contatto IDC (Insulation Displacement Contact) che taglia l'isolante e crea contatto metallico. Regola fondamentale: **untwist massimo 13 mm per Cat 6A** (6 mm per Cat 7). Maggiore untwist = NEXT degradato.

```
Procedura terminazione Keystone Cat 6A:
1. Spellare la guaina esterna per ~25 mm (no di piu)
2. Separare le coppie mantenendo la torsione
3. Inserire i conduttori nei contatti IDC secondo schema T568B
4. Usare punch-down tool — NON forbici, NON pinze
5. Tagliare il conduttore in eccesso (il tool lo fa automaticamente)
6. Verificare che ogni conduttore sia completamente inserito
7. Chiudere la keystone e montare nella placca
```

**Patch Panel**: terminazione a impatto su pannello 19" da 1U (24 porte) o 2U (48 porte). Due tipologie:

- **Patch panel a terminazione diretta**: il cavo viene terminato direttamente sui contatti IDC del pannello. Piu compatto, meno flessibile.
- **Patch panel modulare keystone**: il pannello ospita jack keystone removibili. Piu flessibile: se un singolo jack e difettoso, si sostituisce solo quello senza toccare il pannello. **Raccomandato** per nuove installazioni.

**Terminazione a connettore RJ-45 (plug)**: usata solo per patch cord, mai per cablaggio fisso. Richiede crimpatrice di precisione e connettori Cat 6A certificati (non usare connettori Cat 5e generici per patch cord Cat 6A).

**Errori comuni di terminazione:**

| Errore | Effetto | Come evitarlo |
|--------|---------|---------------|
| Eccessivo untwist | NEXT degradato, fail Cat 6A | Untwist max 13 mm, misurare |
| Guaina troppo spellata | Stress meccanico, piegatura coppia | Max 25 mm per keystone |
| Conduttore non inserito nel IDC | Wire map fail, coppia aperta | Usare punch-down tool corretto |
| Piega brusca al punch-down | Return loss elevato | Mantenere raggio naturale |
| Schermo non collegato | Schermatura inefficace, antenna | Collegare drain wire a terra |

### Test e Certificazione Rame

La certificazione del cablaggio e la differenza tra "ho posato dei cavi" e "garantisco che il link supporta Cat 6A 10 Gbps a norma TIA". Lo standard distingue tre modelli di test:

- **Permanent Link (PL):** dal patch panel alla presa TO, esclude i patch cord. E il modello tipico per la certificazione di nuovi impianti.
- **Channel:** include patch panel, cavo orizzontale, presa TO e i due patch cord (rack + utente). Modello "end-to-end".
- **Patch Cord:** solo il patch cord, certificato in fabbrica o in laboratorio.

I parametri da verificare sono codificati e ognuno ha soglie precise per categoria:

- **Wire Map:** verifica continuita e ordine dei pin. Rivela cavi tagliati, scambiati, in cortocircuito.
- **Length:** lunghezza elettrica di ogni coppia, deve essere <= 90m PL e <= 100m Channel.
- **Insertion Loss (Attenuation):** attenuazione del segnale, in dB. Cresce con frequenza e lunghezza.
- **NEXT (Near-End Crosstalk):** diafonia tra coppie misurata al lato vicino al trasmettitore.
- **PSNEXT (Power Sum NEXT):** somma del NEXT da tutte le altre tre coppie su una coppia.
- **FEXT (Far-End Crosstalk)** e **PSACR-F** (Power Sum Attenuation to Crosstalk Ratio Far-end): diafonia al lato lontano.
- **Return Loss (RL):** segnale riflesso, indica disadattamento di impedenza (cavi piegati, terminazioni male).
- **Delay Skew:** differenza di tempo di propagazione tra le coppie, critico per 1000Base-T e 10GBase-T.
- **Alien Crosstalk (AXT):** diafonia tra cavi adiacenti, parametro Cat 6A obbligatorio.

Gli strumenti professionali certificati per Cat 6A/8 sono sostanzialmente tre famiglie:

- **Fluke Networks DSX-8000 / DSX-CableAnalyzer / Versiv:** standard de facto in Italia. DSX-8000 certifica fino a Cat 8.2 (2 GHz), risultati esportabili in PDF firmati per accettazione lavori.
- **Ideal Networks LanTEK IV:** alternativa professionale, costo inferiore Fluke, certificazione fino Cat 8.
- **Softing WireXpert 4500 / 500:** terza opzione enterprise, software CertiFi per gestione progetti multi-installatore.

Un report di certificazione tipico per ogni link contiene: identificativo (es. `BLD1.F2.SR1.RACK01.U24.P12`), categoria target, pass/fail per ogni parametro con margine in dB, grafici frequenza/attenuazione, data, operatore, numero seriale tester, calibrazione. La documentazione di certificazione e spesso richiesta per il collaudo SAL e per la garanzia 25 anni dei produttori (Panduit, Belden, Siemon, Nexans LANmark): senza certificazione, niente garanzia estesa.

**Interpretazione dei risultati di certificazione:**

| Risultato | Significato | Azione |
|-----------|-------------|--------|
| **PASS** (margine > 3 dB) | Link conforme con buon margine | Accettare |
| **PASS** (margine 0-3 dB) | Link conforme ma marginale | Accettare, documentare, monitorare |
| **PASS*** (asterisco) | Passato per la categoria target ma con margine negativo su un parametro non critico | Investigare, considerare riterminazione |
| **FAIL** | Non conforme | Riterminare o riposare il cavo |

**Costo della certificazione**: un tester Fluke DSX-8000 costa circa €15.000-25.000 (nuovo). Il noleggio giornaliero si attesta su €200-400/giorno. La certificazione di 150 link richiede tipicamente 1-2 giornate di lavoro per un tecnico esperto (4-8 minuti per link, setup incluso).

### Alien Crosstalk e Considerazioni Cat 6A

L'alien crosstalk (AXT) e il parametro che giustifica il salto di qualita da Cat 6 a Cat 6A per applicazioni 10 Gigabit. Mentre NEXT e FEXT misurano la diafonia tra le coppie *all'interno dello stesso cavo*, l'AXT misura la diafonia *tra cavi diversi* in un bundle.

A frequenze elevate (250-500 MHz), i segnali si accoppiano magneticamente tra cavi vicini. Con Cat 6, questo accoppiamento diventa inaccettabile per 10GBase-T oltre i 55 m. Cat 6A risolve il problema in due modi:

1. **Schermatura individuale delle coppie** (U/FTP, S/FTP): il foglio metallico isola ogni coppia dall'esterno.
2. **Geometria interna migliorata** (spline separator): un separatore plastico a croce tra le coppie aumenta la distanza inter-coppia.

**Test AXT**: la certificazione AXT richiede la misura di 6 cavi disturber attorno al cavo vittima. Il test completo di un bundle di 24 cavi Cat 6A per AXT richiede circa 20 minuti (automazione via DSX-8000 con adattatore AXT).

---

## Fibra Ottica

### Principi di Propagazione Ottica

La fibra ottica trasmette segnali come impulsi di luce attraverso un core di vetro (silice) ad altissima purezza. La propagazione avviene per riflessione interna totale: il core ha indice di rifrazione superiore al cladding circostante, e la luce viene confinata nel core per principio fisico.

**Singolomodo vs Multimodale**: la differenza fondamentale sta nel diametro del core e nel numero di modi (percorsi) che la luce puo seguire.

- **Multimodale (MMF)**: core 50 µm o 62.5 µm. La luce si propaga secondo molti modi, ciascuno con velocita leggermente diversa. Questo causa dispersione modale che limita la banda e la distanza. Trasmettitori VCSEL (LED laser verticali) economici, operano a 850 nm.
- **Singolomodo (SMF)**: core 9 µm. Un solo modo di propagazione, nessuna dispersione modale. Banda virtualmente illimitata, distanze chilometriche. Trasmettitori laser DFB (Distributed Feedback) o EML (Electro-absorption Modulated Laser), piu costosi.

**Lunghezze d'onda operative**:
- **850 nm**: finestra multimodale, attenuazione ~2.5 dB/km, laser VCSEL economici.
- **1310 nm**: finestra singolomodo primaria, attenuazione ~0.35 dB/km, dispersione cromatica minima.
- **1550 nm**: finestra singolomodo secondaria, attenuazione minima ~0.22 dB/km, usata per lunghe distanze.
- **CWDM/DWDM**: multiplexing a lunghezze d'onda multiple nella finestra 1270-1610 nm per singolomodo.

### Multimodale OM1-OM5

La fibra multimodale (MMF) ha core grande (50 o 62.5 micrometri) che permette piu modi di propagazione. Buon mercato in trasmettitori (LED o VCSEL economici), distanze brevi-medie. Le classi sono:

| Classe | Core/Cladding | Lunghezza d'onda | 1G | 10G | 40G | 100G | Note |
|--------|---------------|-------------------|----|----|-----|------|------|
| **OM1** | 62.5/125 | 850/1300 nm | 275m / 550m | 33m | n/a | n/a | Legacy, arancione |
| **OM2** | 50/125 | 850/1300 nm | 550m / 800m | 82m | n/a | n/a | Arancione |
| **OM3** | 50/125 (laser-optimized) | 850 nm | 1000m | 300m | 100m | 70m | **Acquamarina** |
| **OM4** | 50/125 (laser-optimized) | 850 nm | 1100m | 400m | 150m | 100m | Acquamarina o viola |
| **OM5** | 50/125 (WBMMF) | 850-953 nm | 1100m | 400m | 440m SWDM4 | 150m | Verde lime, supporta SWDM |

**OM4 e lo standard pratico** per dorsali interne in PMI e per data center small/medium dal 2018. OM5 ha senso solo se si pianifica di sfruttare la trasmissione SWDM (Short Wavelength Division Multiplexing) per portare 100G/400G su singola coppia, scenario raro fuori dall'hyperscaler. OM1/OM2 vanno sostituiti in qualsiasi rifacimento: i 33 metri di OM1 a 10G sono inadeguati per qualunque dorsale moderna.

I cavi multimodali sono codificati per colore della guaina secondo TIA-598-D: arancione (OM1/OM2), acquamarina (OM3/OM4), verde lime (OM5).

### Singolomodo OS1/OS2

La fibra singolomodale (SMF) ha core piccolo (9 micrometri), un solo modo di propagazione, attenuazione molto bassa, distanze chilometriche. Trasmettitori laser piu costosi (DFB, EML), ma il differenziale si e ridotto molto negli ultimi 5 anni grazie all'industria FTTH e ai transceiver QSFP.

- **OS1:** posa indoor tight-buffered, attenuazione max 1.0 dB/km a 1310/1550 nm.
- **OS2:** posa outdoor loose-tube, attenuazione max 0.4 dB/km a 1310/1550 nm. **Standard moderno** per qualsiasi dorsale, indoor o outdoor.

Distanze tipiche con transceiver SFP/SFP+/QSFP comuni:
- 1000Base-LX (1310 nm): 10 km su SMF.
- 10GBase-LR (1310 nm): 10 km.
- 10GBase-ER (1550 nm): 40 km.
- 100GBase-LR4 (1310 nm CWDM): 10 km.
- 400GBase-DR4 (1310 nm): 500 m.

Per dorsali tra edifici nello stesso campus aziendale (200-800 metri), SMF OS2 e quasi sempre la scelta giusta: costa marginalmente di piu del MMF, ma elimina ogni preoccupazione di distanza per i prossimi 20 anni e supporta upgrade futuri a 100G/400G senza sostituire la fibra. Guaina di colore giallo per identificazione visiva.

### Connettori e Polishing

I connettori fibra in uso oggi:

- **SC (Subscriber Connector):** push-pull, formato 2.5mm ferrule, robusto, ancora diffuso in patch panel ISP e in dorsali industriali.
- **LC (Lucent Connector):** mini push-pull 1.25mm ferrule, **standard de facto** nei rack moderni (densita doppia rispetto a SC).
- **ST (Straight Tip):** baionetta, 2.5mm ferrule, legacy ma ancora diffuso in installazioni anni '90/2000.
- **MTP/MPO (Multi-fiber Push On):** connettore a nastro 12-24-72 fibre, usato per breakout 40G/100G/400G in datacenter e per pre-terminated trunk.
- **E2000:** connettore con otturatore integrato, usato in ambienti FTTH e telco europei (Swisscom, Telecom Italia).

**Polishing del ferrule** determina il return loss del connettore:

- **PC (Physical Contact):** RL ~30 dB. Obsoleto.
- **UPC (Ultra Physical Contact):** RL > 50 dB, ferrule blu. Standard per data e telecom enterprise.
- **APC (Angled Physical Contact):** RL > 60 dB, ferrule verde, taglio a 8 gradi per riflettere segnali fuori asse. **Obbligatorio** per applicazioni con forte sensibilita alle riflessioni: DOCSIS 3.1 cable TV, RFoG, sistemi PON GPON/XGS-PON, applicazioni analogico-CATV. Gli APC e gli UPC **non sono compatibili tra loro**: collegare un APC a un UPC danneggia entrambi i ferrule.

Identificazione visiva: il colore del corpo connettore segnala il polishing. Blu = UPC SMF/MMF, verde = APC SMF (mai APC su MMF), beige = SC MMF UPC, acquamarina = LC OM3/OM4.

### Tecniche di Giunzione: Fusione e Meccanica

Quando la fibra deve essere giuntata (dorsali lunghe, riparazioni, transizioni indoor-outdoor), si usano due tecniche:

**Giunzione per fusione (fusion splice)**: le due estremita della fibra vengono allineate, riscaldate con arco elettrico e fuse insieme. Attenuation loss tipico: 0.02-0.05 dB. Richiede splicer (giuntatrice) professionale, costo €3.000-15.000 per i modelli base, fino a €30.000 per le top di gamma (Fujikura 90S+, Sumitomo TYPE-82C+, INNO Instrument View 12R). Il tecnico deve avere formazione specifica.

**Giunzione meccanica**: le due fibre vengono allineate meccanicamente in un dispositivo con gel di indice (index-matching gel) che riduce le riflessioni. Attenuation loss: 0.1-0.5 dB. Non richiede attrezzatura costosa, usata per riparazioni temporanee o dove il costo della fusione non e giustificato.

**Preparazione della fibra per giunzione:**
1. Spellare la fibra (buffer removal) con pinza a calore o chimica
2. Pulire la fibra nuda con alcol isopropilico e lint-free wipe
3. Cleave (taglio) con cleaver di precisione (angolo < 1°)
4. Inserire nella splicer, allineamento automatico (core alignment o cladding alignment)
5. Eseguire la fusione
6. Proteggere con protettore di giunzione (heat shrink splice protector)

### Test OTDR e Insertion Loss

La certificazione fibra prevede due livelli:

**Tier 1 — Insertion Loss (Power Meter + Light Source):** misura attenuazione end-to-end con sorgente calibrata e misuratore di potenza. Verifica che il loss totale sia entro budget (es. < 1.5 dB per un link OM4 50m con 2 connettori). E il test minimo richiesto per certificazione.

**Tier 2 — OTDR (Optical Time Domain Reflectometer):** invia impulsi ottici e misura le riflessioni nel tempo. Restituisce il "tracciato" del link: ogni evento (connettore, splice, macrobending, end-of-fiber) appare come picco o discontinuita, con misura precisa di posizione e attenuazione. Indispensabile per dorsali lunghe o per troubleshooting di link con loss anomalo.

**Lettura di una traccia OTDR:**

```
dB
^
|   \_________          _____          ___________
|              \       /     \        /            \
|    connettore \     / splice\      /  macrobending \
|    (riflettivo)\___/         \____/                 \___
|                                                          end-of-fiber
+---------------------------------------------------------> distanza (m)
```

- **Riflettivo + loss**: connettore (picco verso l'alto + calo livello). Loss tipico per connettore: 0.3-0.5 dB.
- **Solo loss (non riflettivo)**: splice fusione (calo livello senza picco). Loss tipico: 0.02-0.1 dB.
- **Loss graduale**: macrobending (curva troppo stretta), stress meccanico.
- **Gain apparente**: artefatto OTDR quando fibre con MFD diverso vengono giuntate (misurare in entrambe le direzioni).

Strumenti tipici: **Fluke Networks OFP-200/OFP-100** (OTDR + IL), **EXFO MaxTester 730/940**, **Viavi T-BERD 5800**, **Yokogawa AQ7280**. Per piccole sedi PMI esiste anche la categoria mini-OTDR sotto i 5000 EUR (es. EXFO MAX-715B) che basta per dorsali entro 2-3 km.

Ogni certificazione richiede taratura del setup con bobina di lancio e bobina di ricezione (launch/receive cord) per mascherare la dead zone del connettore di lancio dell'OTDR e per misurare correttamente il loss del primo e ultimo connettore del link.

### Link Budget Calculation

Il calcolo del link budget e il passaggio progettuale che determina se un collegamento in fibra funzionera o no. Si sommano tutte le perdite attese e si verifica che il totale sia inferiore al budget del transceiver.

**Formula:**
```
Link Budget (dB) = Potenza TX (dBm) - Sensibilita RX (dBm)
Perdita totale = (Lunghezza × attenuazione/km) + (N_connettori × loss/connettore) + (N_splice × loss/splice) + margine
Requisito: Link Budget > Perdita totale
```

**Esempio pratico — dorsale inter-building SMF OS2, 500 m:**

```
Transceiver: SFP+ 10GBase-LR
  Potenza TX: -6 dBm (worst case)
  Sensibilita RX: -14.4 dBm
  Link Budget: -6 - (-14.4) = 8.4 dB

Perdite stimate:
  Fibra OS2: 500 m × 0.4 dB/km = 0.2 dB
  Connettori: 4 × 0.5 dB = 2.0 dB (2 per lato, patch panel + transceiver)
  Splices: 2 × 0.1 dB = 0.2 dB (giunzione indoor-outdoor per lato)
  Margine sistema: 3.0 dB (raccomandato TIA per invecchiamento e riparazioni)

Perdita totale: 0.2 + 2.0 + 0.2 + 3.0 = 5.4 dB

Margine residuo: 8.4 - 5.4 = 3.0 dB → OK
```

Se il margine residuo e negativo, il link non funzionera. Azioni correttive: usare transceiver con budget maggiore, ridurre il numero di connettori, usare splice fusione invece di meccaniche, verificare pulizia connettori.

---

## Pathway and Spaces — TIA-569

### Locali Tecnici: MDF e IDF

TIA-569 definisce i requisiti per gli spazi che ospitano il cablaggio strutturato.

**MDF (Main Distribution Frame)**: locale tecnico principale, equivale all'Equipment Room (ER). Requisiti minimi:

- Dimensione minima: 14 mq (3.7 × 3.7 m) per sedi fino a 5.000 mq di superficie servita.
- Altezza minima soffitto: 2.6 m.
- Illuminazione minima: 500 lux a livello rack (EN 12464-1).
- Climatizzazione: temperatura 18-27°C, umidita 30-55% (ASHRAE raccomandate per apparati IT).
- Alimentazione elettrica: minimo 2 circuiti dedicati, UPS, quadro elettrico separato.
- Pavimento sopraelevato: facoltativo ma raccomandato per sedi > 50 prese, altezza 30-50 cm.
- Porta: minimo 90 cm larga, 200 cm alta, senza soglia (per passaggio rack su ruote).
- Protezione antincendio: rilevazione fumo, estintori a gas (non acqua/polvere).
- Controllo accessi: chiave o badge dedicato, log degli accessi.
- Nessuna tubatura idraulica o scarichi nel locale.

**IDF (Intermediate Distribution Frame)**: armadio di distribuzione secondario, equivale al Telecommunications Room (TR). Serve una zona o un piano dell'edificio. Requisiti minimi:

- Dimensione: da armadio a muro (600 × 600 mm per 12U-24U) fino a locale dedicato per sedi piu grandi.
- Alimentazione dedicata con UPS locale o centralizzato.
- Ventilazione adeguata (considerare dissipazione termica switch PoE++).

**Rapporto prese per locale tecnico**: regola pratica TIA-569 prevede un TR ogni 1.000 mq di superficie servita, o ogni 90 m di distanza radiale dall'ultima presa (per rispettare il limite dei 90 m di permanent link).

### Condotti, Canaline e Passaggi

I pathway sono i percorsi fisici per i cavi. TIA-569 specifica:

**Canalizzazione orizzontale**:
- Canalina in acciaio zincato (portacavi): per controsoffitti e pavimenti sopraelevati. Larghezza 100-600 mm, altezza 50-100 mm. Riempimento massimo 40% della sezione trasversale.
- Tubo corrugato (PVC o HDPE): per percorsi a muro. Diametro 20-32 mm per singolo cavo Cat 6A, 40-50 mm per bundle.
- J-hook: ganci a J in acciaio per supporto cavi in controsoffitto senza canalina. Distanza massima 1.5 m tra supporti.
- Wiremold (canale a parete): per retrofit in edifici esistenti dove la canalizzazione incassata non e praticabile.

**Canalizzazione verticale (backbone)**:
- Cavedi verticali dedicati con dimensioni minime 600 × 600 mm per piano.
- Riempimento massimo 40% della sezione.
- Barriere tagliafuoco (firestop) ad ogni attraversamento di piano: requisito normativo italiano (D.M. 3 agosto 2015 — regola tecnica prevenzione incendi).

**Canalizzazione interrata (inter-building)**:
- Tubo HDPE corrugato a doppia parete: diametro 50/63 mm per cavi fibra, 110 mm per bundle misti.
- Profondita minima di posa: 60 cm sotto superficie (70 cm sotto zone carrabili).
- Pozzetti di ispezione: ogni 60-80 m e ad ogni cambio di direzione.
- Raggio di curvatura nei pozzetti: 20 volte il diametro del cavo.
- Tiraggio con filo guida (sonda passacavi, Teflon o nylon).

### Separazione da Impianti Elettrici

La coesistenza tra cavi dati e cavi di alimentazione elettrica e regolata da EN 50174-2 e TIA-569 per evitare interferenze elettromagnetiche.

| Condizione | Distanza minima UTP | Distanza minima STP |
|-----------|---------------------|---------------------|
| Cavi dati e potenza in parallelo, senza barriera | 200 mm | 50 mm |
| Cavi dati e potenza in parallelo, con barriera metallica | 100 mm | 20 mm |
| Incrocio a 90° | Nessuna | Nessuna |
| Vicinanza a lampade fluorescenti | 300 mm | 100 mm |
| Vicinanza a trasformatori/motori | 1.000 mm | 300 mm |
| Vicinanza a quadri elettrici BT | 500 mm | 150 mm |

In pratica: nelle PMI italiane, la canalina dati deve correre su un lato del controsoffitto e la canalina elettrica sull'altro, o su livelli diversi, con incrocio a 90° dove necessario. Mai nello stesso condotto. Anche in canalina metallica con setto divisorio, la separazione e 100 mm per UTP e 20 mm per STP.

---

## Guida Pratica

### Organizzazione Rack 19"

Il rack 19" e l'unita modulare standard per il cablaggio strutturato. Le dimensioni sono codificate:

- **Larghezza utile:** 19" (482.6 mm) tra le colonne forate.
- **Unita di altezza (U):** 1.75" = 44.45 mm. Un rack 42U e alto 42 × 44.45 = 1866 mm + base/sommita.
- **Profondita:** variabile, da 600 mm (telecom) a 1200 mm (server). Per server moderni Dell PowerEdge / HPE ProLiant la profondita 1070-1100 mm e tipica.
- **Formati comuni:** 12U/24U/42U/47U. I 47U si usano per data center con server molto profondi e PDU verticali alte.
- **Larghezza esterna:** 600 mm (telecom/networking) o 800 mm (server, per cable management laterale).

**Layout tipico rack di sede aziendale (24U-42U):**

```
U42  | Cable manager 1U
U41  | Switch core L3 (es. Cisco Catalyst 9300 48-port)  1U
U40  | Cable manager 1U
U39  | Patch panel Cat 6A 24-port - PIANO 2 (P201-P224)  1U
U38  | Cable manager 1U
U37  | Patch panel Cat 6A 24-port - PIANO 1 (P101-P124)  1U
U36  | Cable manager 1U
U35  | Patch panel Cat 6A 24-port - PIANO 1 (P125-P148)  1U
U34  | Cable manager 1U
U33  | Patch panel Cat 6A 24-port - PIANO TERRA (PT01-PT24) 1U
U32  | Cable manager 1U
U31  | Patch panel fibra LC duplex - DORSALI               1U
U30  | Cable manager 1U
...
U10  | Server NAS 2U (Synology RS3621xs+)                  2U
U8   | UPS 2U (APC Smart-UPS 2200VA RM)                    2U
U6   | Server backup 1U                                    1U
U4   | Switch out-of-band management                       1U
U2-3 | Blanking panel                                      2U
U1   | Rack shelf per apparati piccoli                     1U
```

**Regole d'oro per l'organizzazione:**

- **Patch panel sempre con cable manager 1U sopra e sotto.** Anche se sembra spreco di U, e indispensabile per gestire i patch cord senza creare matasse.
- **Switch a meta rack.** Posizionare gli switch piu o meno al centro minimizza la lunghezza media dei patch cord. In data center la convenzione top-of-rack mette lo switch in alto, ma in sede ufficio il middle-of-rack e piu pratico per accessibilita.
- **Server pesanti in basso.** Stabilita meccanica del rack: i pezzi pesanti (UPS soprattutto, server multi-2U) vanno in basso. Un rack 42U con tutto il peso in alto e pericoloso.
- **PDU vertical mount sul lato posteriore.** Le PDU "zero U" verticali liberano spazio orizzontale e organizzano meglio l'alimentazione. Due PDU per ridondanza A+B, ognuna su circuito elettrico separato.
- **Blanking panel su tutti gli U liberi.** Mantengono il flusso d'aria hot/cold corretto e impediscono che l'aria calda riemerga sul lato cold.
- **Etichetta su ogni U.** Anche una semplice etichetta con il numero U e la funzione dell'apparato. L'alternativa e fotografare il rack fronte e retro dopo ogni modifica.

### Cable Management Avanzato

Un buon cable management non e estetica, e affidabilita. Cavi accatastati in modo disordinato:
- non si dissipano correttamente (heat buildup, problema serio per PoE+ ad alta densita),
- impediscono l'accesso ai patch panel,
- creano stress meccanico sui connettori,
- rendono impossibile tracciare un link in caso di guasto.

**Principi di cable management:**

1. **Bend radius minimo:** per Cat 6A il raggio di curvatura minimo e 4 volte il diametro esterno (4 × OD), tipicamente ~28-32 mm. Per fibra OM3/OM4 il raggio minimo e 30 mm a riposo, 15 mm in operativo (ma meglio rispettare 30 mm sempre). Curve piu strette generano insertion loss e nei casi peggiori spezzano la fibra.
2. **Velcro, mai fascette in plastica.** Le fascette (zip-tie) strette deformano la geometria del cavo, alterando impedenza e generando NEXT. Velcro Rip-Tie o equivalenti permettono ri-aggiustamenti senza tagliare nulla.
3. **Lacing verticale e orizzontale.** Cable manager orizzontali (1U o 2U) tra patch panel e switch, manager verticali (full-height) lungo i lati del rack per la dorsale interna del rack.
4. **Lunghezza patch cord giusta.** Patch cord troppo lunghi creano aggrovigliamenti, troppo corti stressano i connettori. Tenere a magazzino tagli da 0.5m / 1m / 2m / 3m / 5m e usare il piu corto che funziona.
5. **Separazione potenza e dati.** Cavi UTP separati di almeno 200 mm dai cavi alimentazione 230V se in parallelo, 100 mm se incrocio a 90 gradi. EN 50174-2 e norma di riferimento.
6. **Cavi fibra in percorsi separati.** La fibra e fragile meccanicamente: mai nel bundle con cavi rame pesanti. Usare canalina fibra dedicata o cassetta fibra nel rack.
7. **Codice colore patch cord per funzione.** Standard aziendale suggerito: blu = LAN dati, giallo = management, rosso = DMZ/security, verde = guest WiFi, grigio = VoIP, arancione = dorsale fibra.

**Hot/cold aisle containment.** In data center con piu rack, l'organizzazione per corridoi caldi/freddi alternati e standard da TIA-942: tutti i front-panel rivolti verso il corridoio freddo (aria condizionata in ingresso), tutti i back-panel verso il corridoio caldo (aria espulsa). Pannelli di contenimento sopra le file di rack chiudono il corridoio caldo o freddo e migliorano drasticamente l'efficienza energetica del raffreddamento (PUE migliore).

### Etichettatura TIA-606-C

L'etichettatura sistematica e cio che distingue un cablaggio professionale da uno improvvisato. TIA-606-C definisce la sintassi e i campi minimi di identificazione. Lo schema raccomandato per un edificio aziendale e:

```
[BUILDING].[FLOOR].[ROOM].[RACK].[U].[PORT]

Esempio: BLD1.F2.SR1.RACK01.U24.P12

dove:
  BLD1   = edificio 1
  F2     = piano 2
  SR1    = Service Room / Telecommunications Room 1
  RACK01 = rack numerato in modo univoco
  U24    = unita rack del patch panel
  P12    = porta sul patch panel
```

**Classi di amministrazione TIA-606-C:**

| Classe | Scope | Elementi etichettati |
|--------|-------|---------------------|
| **Classe 1** | Singolo building | Link orizzontali, TO, patch panel |
| **Classe 2** | Campus (multi-building) | + dorsali, entrance facility |
| **Classe 3** | Multi-campus | + WAN link, external pathways |
| **Classe 4** | Multi-tenant | + tenant identification |

Per la maggior parte delle PMI italiane, Classe 1 o Classe 2 sono sufficienti.

Ogni elemento del cablaggio deve avere etichetta univoca e leggibile:

- **Patch panel:** label sopra ogni porta con identificativo della presa utente corrispondente.
- **Presa TO (utente):** label sopra ogni porta con identificativo (es. `PT-A-12` = piano terra, area A, presa 12).
- **Cavi orizzontali:** etichetta a entrambe le estremita (lato patch panel e lato presa) con stesso identificativo.
- **Patch cord:** etichetta opzionale ma raccomandata, con codice colore per VLAN o servizio.
- **Rack:** label sul fronte e sul retro con identificativo rack.
- **Locale tecnico:** targhetta sulla porta con identificativo TR e contatti emergenza.

**Stampanti etichette professionali:**

- **Brother PT-D610BT / PT-E550W / PT-P710BT:** standard nelle PMI italiane, nastri TZe laminati resistenti a strappo e UV, larghezze 6-24 mm. Modelli E-series (E550W) hanno template predefiniti per cavo, patch panel, rack.
- **Brady BMP41 / BMP21-PLUS / M210:** soluzione enterprise, etichette dedicate per cavi (avvolgenti, autolaminanti, "self-laminating" che proteggono il testo).
- **DYMO RhinoPro 5200:** alternativa entry-level professionale, leggermente meno robusta del Brother.

**Documentazione complementare:**

- **Single-line diagram:** schema a blocchi della topologia di rete con tutti i link dorsali, gli switch core e di distribuzione, gli uplink ISP. Mantenuto in Visio o draw.io.
- **Floor plan cablaggio:** planimetria di ogni piano con la posizione di ogni presa TO e relativo identificativo. Aggiornato a ogni modifica.
- **Patch schedule:** tabella Excel/Google Sheets con tutti i link patch (`patch panel/porta` ↔ `switch/porta`), con campi VLAN, descrizione utente, data attivazione. Mantenuto in repo Git per cronologia delle modifiche.
- **Test report di certificazione:** archiviati in PDF, organizzati per ID link.

### Grounding e Bonding — TIA-607

TIA-607-D definisce il sistema di messa a terra specifico per il cablaggio telecomunicazioni. Una messa a terra corretta e essenziale per:

- Funzionamento della schermatura dei cavi (F/UTP, S/FTP)
- Protezione da scariche elettrostatiche (ESD)
- Protezione da sovratensioni indotte
- Sicurezza del personale
- Conformita normativa (CEI 64-8, CEI EN 62305 per protezione fulmini)

**Componenti del sistema di bonding TIA-607:**

- **TBB (Telecommunications Bonding Backbone):** conduttore in rame minimo 6 AWG (16 mm²) che collega tutti i TR e l'ER alla barra di terra principale.
- **TMGB (Telecommunications Main Grounding Busbar):** barra di rame nel locale tecnico principale, collegata all'impianto di terra dell'edificio.
- **TGB (Telecommunications Grounding Busbar):** barra di rame in ogni TR/armadio di piano, collegata al TMGB via TBB.
- **Bonding conductor per rack:** ogni rack metallico collegato alla TGB locale con conduttore 6 AWG.
- **Drain wire schermatura:** collegato alla barra di terra del patch panel, che a sua volta e collegata alla TGB.

**Errore critico**: collegare la schermatura del cavo a terra da un lato solo (single-point bonding) in corrente continua. Per cablaggio orizzontale entro i 90 m, il bonding a un solo lato e accettabile e anzi raccomandato per evitare ground loop. Per dorsali oltre i 90 m, si usano tecniche specifiche (bonding capacitivo a un lato).

### PoE Power over Ethernet

Power over Ethernet trasmette alimentazione DC sul cavo Ethernet insieme ai dati. E diventato pervasivo per access point WiFi, telefoni VoIP, telecamere IP, controllo accessi, illuminazione LED PoE, sensori IoT. Le revisioni dello standard IEEE 802.3 sono:

| Standard | Anno | Potenza max al PSE | Potenza al PD | Tipo | Coppie usate |
|----------|------|---------------------|---------------|------|--------------|
| **802.3af** (PoE) | 2003 | 15.4 W | 12.95 W | Type 1 | 2 coppie |
| **802.3at** (PoE+) | 2009 | 30 W | 25.5 W | Type 2 | 2 coppie |
| **802.3bt Type 3** (PoE++) | 2018 | 60 W | 51 W | Type 3 | 4 coppie |
| **802.3bt Type 4** (Hi-PoE) | 2018 | 90-100 W | 71.3 W | Type 4 | 4 coppie |

**Implicazioni sul cablaggio:**

- Il PoE genera calore nel cavo (effetto Joule, I²R). Con PoE+ (30W) su un singolo cavo l'effetto e modesto. Con PoE++ Type 3/4 (60-90W) su grandi bundle (24-48 cavi in fascio), la temperatura puo salire di 10-15 gradi C, causando aumento dell'insertion loss.
- Lo standard TIA-568 e TSB-184-A definiscono fattori di derating sulla distanza e sul bundling. In pratica: per PoE Type 4 si raccomanda Cat 6A con bundle massimi di 24 cavi e di limitare la distanza a 70-80 metri per garantire margine termico.
- I cavi schermati (F/UTP, S/FTP) dissipano meglio il calore grazie allo schermo, vantaggio in installazioni PoE++ ad alta densita.
- Patch panel "Cat 6A 10G PoE++" hanno terminali rinforzati per gestire correnti di 1A per coppia.

**Tabella derating PoE per bundling e temperatura (TIA TSB-184-A):**

| Temp. ambiente | Bundle 7 cavi | Bundle 24 cavi | Bundle 48 cavi |
|----------------|---------------|----------------|----------------|
| 20°C | 100 m | 95 m | 85 m |
| 30°C | 95 m | 85 m | 75 m |
| 40°C | 85 m | 75 m | 65 m |
| 45°C | 80 m | 70 m | 60 m |

*Valori indicativi per PoE Type 3 (60W) su Cat 6A U/FTP.*

**Verifica PoE budget switch.** Uno switch PoE 48-port con budget 740W non puo erogare 30W per ogni porta (sarebbero 1440W). In progettazione:
- Inventario dei dispositivi PoE: 24 AP WiFi 6 (15W cad = 360W) + 12 telefoni VoIP (7W cad = 84W) + 8 telecamere IP (12W cad = 96W) = 540W → ok in budget 740W con margine.
- Ridondanza alimentatore PoE: nei modelli mid-range si configurano due power supply ridondanti per evitare interruzione completa dei dispositivi PoE in caso di guasto PSU.

---

## Configurazione Tipica PMI

Esempio reale di dimensionamento per una sede aziendale italiana, 50 dipendenti, edificio singolo su 3 piani (piano terra + 2 piani), in un'area artigianale del Veneto:

**Inventario prese rete:**
- Piano terra: ufficio open space 20 dip × 2 prese = 40 + reception 4 + sala riunioni 6 + cucina/area pausa 2 = **52 prese**.
- Primo piano: uffici 15 dip × 2 = 30 + sala riunioni 4 + ufficio direzione 4 = **38 prese**.
- Secondo piano: uffici tecnici 15 dip × 2 = 30 + laboratorio 4 + magazzino dati 2 = **36 prese**.
- WiFi access point: PT 4 + P1 3 + P2 3 = **10 AP** (PoE+).
- Stampanti rete: 4 (1 per piano + 1 a colori produzione).
- VoIP centralino: 50 telefoni IP (PoE).
- Telecamere IP perimetrali: 8 (PoE+).
- Sovradimensionamento 30%: +38 prese spare distribuite.

**Totale prese cablate:** ~164 prese Cat 6A (~7 patch panel 24-port).

**Cablaggio orizzontale:**
- Cat 6A U/FTP (foiled) per ridurre alien crosstalk.
- Distanza media link: 35-50m, max 75m (verificato sul progetto), nessun link > 90m.
- Patch panel modulari Keystone Cat 6A in rack.

**Locale tecnico (Equipment Room) al piano terra, 18 mq, climatizzato:**
- 1 rack 42U 800×1000 mm per networking + cablaggio.
- 1 rack 42U 800×1200 mm per server (se presente).
- 2 PDU verticali zero-U, alimentate da quadro elettrico dedicato con UPS APC Smart-UPS 3000VA + bypass.
- Climatizzazione split dedicato 12.000 BTU (con allarme temperatura/umidita).
- Allarme temperatura/umidita via sensore Ubiquiti UniFi mPower o Raritan DPX3.
- Rilevatore fumo ottico collegato a impianto antincendio.
- Serratura con chiave specifica o badge elettronico.

**Dorsale inter-piano:**
- 2 fibre OM4 LC duplex per piano (1 attiva + 1 ridondante), terminate su patch panel fibra in rack.
- 2 fibre OS2 LC duplex per piano (predisposizione futura 100G).
- Posa in canalizzazione verticale dedicata, separata da impianti elettrici.
- Firestop certificato ad ogni attraversamento piano.

**Documentazione:**
- Patch schedule mantenuto in Excel + Visio mappa floor.
- Test report Fluke DSX-8000 archiviati per ogni link.
- Etichettatura TIA-606-C: `MZZ.PT.SR1.R01.U35.P12` (Mozzecane.PianoTerra.SR1.Rack01.U35.Porta12).
- Backup documentazione su NAS interno + copia cloud Drive.
- Foto fronte/retro rack aggiornate dopo ogni modifica.

**Costo orientativo (2026):**
- Materiali (cavo, prese, patch panel, fibra, rack, UPS): 22.000-28.000 EUR.
- Manodopera posa (5-7 giorni × 2 tecnici): 8.000-12.000 EUR.
- Certificazione Fluke (1 giornata): 1.200-1.800 EUR.
- **Totale chiavi in mano: 32.000-42.000 EUR.**

Costo per presa: ~250 EUR. Sembra alto rispetto a una posa improvvisata Cat 6 U/UTP (~120 EUR/presa), ma il TCO su 20 anni e identico o inferiore, e l'infrastruttura sopravvive a tre cicli di refresh degli apparati attivi.

---

## Progettazione per Data Center — TIA-942

TIA-942-C definisce i requisiti di cablaggio specifici per data center. I livelli di affidabilita sono:

| Livello | Ridondanza | Uptime | Manutenzione | Uso tipico |
|---------|-----------|--------|--------------|------------|
| **Rated-1** | Nessuna | 99.671% (28.8 h/anno) | Interruzione per manutenzione | Micro DC, PMI |
| **Rated-2** | Componenti ridondanti | 99.749% (22 h/anno) | Ridotta interruzione | PMI media |
| **Rated-3** | Percorsi ridondanti | 99.982% (1.6 h/anno) | Nessuna interruzione | Enterprise |
| **Rated-4** | Fault-tolerant | 99.995% (26 min/anno) | Nessuna interruzione | Mission-critical |

**Topologia cablaggio data center TIA-942:**

```
Entrance Room (ER)                    (punto ingresso carrier/ISP)
       |
Main Distribution Area (MDA)         (core switch, core router)
       |
Horizontal Distribution Area (HDA)   (distribution switch, per fila/zona)
       |
Equipment Distribution Area (EDA)    (top-of-rack switch, server rack)
       |
Zone Distribution Area (ZDA)         (opzionale, punto di consolidamento)
```

**Pre-terminated cabling**: nei data center moderni si usano cavi pre-terminati in fabbrica (trunk cable) con connettori MTP/MPO, che velocizzano il deployment (no terminazione in situ) e garantiscono qualita costante. I trunk si collegano a cassette di breakout (MTP → LC duplex) nei patch panel.

**Structured cabling vs direct-attach (DAC)**: per link top-of-rack entro i 5 m, i cavi DAC (Direct Attach Copper) SFP+/QSFP sono un'alternativa economica al cablaggio strutturato. Oltre i 5 m, fibra o cavo Cat 6A/8.

---

## Best Practices

**Progettazione**

- **Sovradimensiona le prese del 30-40%.** Le esigenze crescono: nuovi dipendenti, sale riunioni con piu monitor, IoT, controllo accessi, sensori. Un cavo non posato oggi costa 5x posarlo domani.
- **Pianifica la dorsale per 10 anni avanti.** OS2 fibra anche per distanze brevi: il differenziale costo e marginale, gli upgrade futuri (40G/100G) sono gratis dal lato infrastruttura.
- **Locale tecnico climatizzato e ventilato.** Anche la sede piu piccola merita un armadio dedicato con almeno split AC. Nei sottoscala caldi gli switch durano la meta.
- **Doppia alimentazione UPS.** Sembra eccessivo per una PMI ma l'esperienza dice che e sempre giustificato: blackout, sbalzi di tensione, manutenzioni elettriche pianificate.
- **Pensa alla WiFi come estensione del cablaggio.** Ogni AP WiFi 6/6E/7 richiede un punto rete Cat 6A PoE+. Pianifica i punti cavo per AP a soffitto con attenzione al site survey RF.
- **Cablaggio di backup per percorsi critici.** Almeno 2 fibre ridondanti per ogni dorsale, su percorsi fisici diversi quando possibile.

**Posa**

- **Rispetta sempre il bend radius.** Curve strette al passacavi, alle scatole 503, agli angoli del rack: sono il primo punto di guasto.
- **Non riutilizzare cavi vecchi in nuovi impianti.** Cat 5e dismesso non torna utile come cavo di scorta: certifica il nuovo da zero.
- **Documenta in tempo reale.** Non rimandare la patch schedule a "lo aggiorniamo a fine progetto": non lo aggiornerai mai. Etichetta mentre posi, non dopo.
- **Foto del rack prima della chiusura.** Una foto da fronte e una da retro, archiviate, salvano ore di troubleshooting futuro.
- **Testa ogni link PRIMA di chiudere controsoffitti e pareti.** Riaprire costa 10x. Meglio certificare con il tester base (wire map + length) subito e con il tester di certificazione in giornata dedicata.
- **LSZH (Low Smoke Zero Halogen).** Per ambienti chiusi e soprattutto per locali tecnici, usare sempre cavi con guaina LSZH (EN 50575 Cca o superiore). In caso di incendio, i cavi PVC rilasciano fumi tossici e corrosivi. Alcuni capitolati italiani lo richiedono obbligatoriamente.

**Manutenzione**

- **Verifica trimestrale visuale del rack.** Cavi spostati, etichette staccate, ventole bloccate: dieci minuti per piano.
- **Ricertifica i link sospetti** dopo ogni intervento di muratura, ristrutturazione, modifica impianto elettrico nelle vicinanze.
- **Audit annuale completo dell'infrastruttura.** Confronto patch schedule reale vs documentazione, identificazione di ghost cable (cavi posati ma mai usati), pianificazione MAC per i prossimi 12 mesi.
- **Spare patch cord di scorta.** Tenere 10-20 patch cord di lunghezze varie, certificati Cat 6A, per sostituzioni rapide.
- **Pulizia connettori fibra.** Usare stick di pulizia a secco (IBC OneClick) prima di ogni collegamento/scollegamento. Un singolo granello di polvere su un connettore fibra puo causare 1+ dB di loss.

**Sicurezza**

- **Rack chiuso a chiave** in locale tecnico chiuso a chiave. Nessun accesso fisico = nessuno schiaffo a uno switch.
- **Segregazione VLAN** sui patch panel etichettata: porta `P101-P112` = VLAN 10 dati, `P113-P120` = VLAN 20 voce, `P121-P124` = VLAN 30 management.
- **Disabilitazione porte switch non utilizzate.** Una porta libera + presa accessibile = vettore di attacco fisico (802.1X port-based authentication consigliata).
- **Port security (MAC limit) su tutte le porte access.** Limita il numero di MAC address per porta a 1-2.

---

## Troubleshooting

**Sintomo: link Gigabit negozia a 100 Mbps anziche 1000.**
- Test wire map con tester base (Fluke MicroScanner): possibile coppia rotta (1000Base-T usa tutte e 4 le coppie, 100Base-TX solo 2).
- Verifica patch cord: probabilmente Cat 5 o 5e degradato.
- Controlla distanza totale Channel: se > 100m, fallback automatico.
- Controlla che entrambe le estremita siano T568B (o T568A): mismatch crea crossover parziale.
- Verifica impostazione speed/duplex sullo switch: auto-negotiation deve essere abilitata su entrambi i lati.

**Sintomo: pacchetti persi su collegamento PoE+.**
- Verifica budget PoE dello switch (`show power inline` su Cisco).
- Misura corrente sul cavo: PoE++ Type 4 puo surriscaldare bundle troppo densi.
- Sostituisci patch cord economico con patch cord certificato Cat 6A LSZH.
- Verifica se il cavo e in un bundle termicamente critico (derating table).

**Sintomo: certificazione Cat 6A fallisce su PSNEXT.**
- Cavo non schermato in ambiente con EMI alta (motori, inverter): passa a F/UTP o S/FTP.
- Bundle troppo stretti con fascette in plastica: rifare con velcro.
- Connettore RJ-45 non keystone certificato Cat 6A: sostituire con keystone Panduit Mini-Com TX6A.
- Untwist eccessivo alla terminazione: riterminare rispettando max 13 mm.

**Sintomo: link fibra con loss eccessivo.**
- Connettore sporco: pulizia con stick a secco IBC OneClick LC + ispezione con microscopio fibra (Fluke FI-7000 FiberInspector).
- Macrobending: cavo curvato troppo stretto in canalizzazione verticale, ispezionare percorso.
- Splice deteriorato: rifare giunto fusione.
- Mismatch connettore: APC collegato a UPC (i ferrule si danneggiano a vicenda).
- Transceiver difettoso: sostituire e riprovare.

**Sintomo: porta switch viene "shutdown" automaticamente in continuazione.**
- Errdisable per port-security violation: check MAC address connesso.
- Errdisable per BPDU guard: dispositivo finale che invia BPDU (switch non gestito attaccato a porta access).
- Cavo intermittente: certifica il link, sostituisci se necessario.
- Errore CRC elevato sul link: indica problema fisico (cavo, connettore, transceiver).

**Sintomo: prese di una zona non funzionano dopo lavori edili.**
- Cavo schiacciato/tagliato durante lavori: certifica e identifica con TDR (Time Domain Reflectometry, funzione del Fluke DSX).
- Patch panel scollegato accidentalmente in rack: foto storica del rack salva la situazione.
- Barriera tagliafuoco applicata sui cavi (resina espandente): verificare che non abbia schiacciato i cavi.

**Sintomo: performance intermittente su link fibra dorsale.**
- Micro-curvatura (microbending): cavo fibra sotto peso di altri cavi o schiacciato da fascetta.
- Temperatura: fibra esposta a temperature estreme (>60°C o <-10°C) in canaline esterne non protette.
- Connettore allentato: verificare serraggio e pulizia.
- Test OTDR bidirezionale per identificare punto esatto del problema.

---

## Domande Frequenti (Q&A)

**D: Posso usare Cat 5e per un nuovo impianto nel 2026?**
R: Tecnicamente funziona per Gigabit Ethernet. Economicamente no: il differenziale di costo Cat 5e vs Cat 6A e circa 15-20% sui materiali (circa €0.50-0.80/metro in piu), ma il cablaggio vive 20 anni. Investire ora in Cat 6A garantisce compatibilita con 10 Gigabit e NBASE-T senza rifare il cablaggio. Cat 5e in nuovo impianto e una falsa economia.

**D: Cat 6 o Cat 6A per un ufficio di 20 persone?**
R: Cat 6A. Il differenziale di costo sull'impianto completo (20 prese × 2 = 40 link) e circa 500-800 EUR. Il cablaggio resta per 15-20 anni. Con WiFi 6E/7 che richiedono uplink 10G e la crescente adozione di 2.5G/5G/10G Ethernet su desktop, Cat 6A e la scelta ragionevole.

**D: Devo certificare anche gli impianti piccoli?**
R: Se vuoi la garanzia 25 anni del produttore (Panduit, Belden, Siemon, Nexans), si — la certificazione e requisito. Se non ti interessa la garanzia estesa, un test base (wire map + length + NVP) con un Fluke MicroScanner e sufficiente per verificare la funzionalita. Ma in caso di problemi futuri, non avrai la baseline di riferimento.

**D: Fibra multimodale OM4 o singolomodo OS2 per dorsali interne?**
R: Dipende dalla distanza. Fino a 300 m, OM4 funziona e i transceiver VCSEL costano meno. Oltre 300 m, OS2 e obbligatorio. Per nuove installazioni, consiglio di posare entrambe (2 OM4 + 2 OS2): il costo aggiuntivo della fibra e trascurabile, mentre il costo di riposare fibra in futuro e elevato.

**D: Posso mixare T568A e T568B nello stesso impianto?**
R: Sconsigliato fortemente. Funziona (grazie ad Auto-MDIX su Gigabit Ethernet), ma rende la documentazione confusa, i tester segnalano errori di wire map e crea potenziali problemi con apparati legacy o con PoE su coppie specifiche.

**D: Quanto dura la certificazione di un impianto?**
R: I produttori offrono garanzia 15-25 anni sull'infrastruttura passiva, a condizione che l'installazione sia stata eseguita da installatore certificato e che la certificazione con tester appropriato sia stata documentata. La certificazione stessa non "scade", ma i dati del tester devono essere conservati per tutta la durata della garanzia.

**D: Serve la schermatura in un ufficio standard?**
R: In un ufficio standard senza fonti EMI significative, U/UTP Cat 6A funziona perfettamente. F/UTP offre un margine di sicurezza in piu con costo marginalmente superiore ed e il consiglio per nuove installazioni. S/FTP e necessario solo in ambienti industriali o con forte EMI. Ricorda: schermatura senza messa a terra corretta e controproducente.

**D: Come dimensiono il budget PoE di uno switch?**
R: Somma la potenza massima di tutti i dispositivi PoE collegati, aggiungi 20% di margine per crescita futura. Verifica che il budget PoE totale dello switch copra il totale. Se hai 48 porte ma solo 24 dispositivi PoE, non serve uno switch con budget per 48 porte a piena potenza.

---

## Esercizi e Laboratori

### Lab 1 — Terminazione e Certificazione
Termina un cavo Cat 6A su keystone jack e patch panel. Verifica con tester la conformita wire map. Se disponibile, certifica con DSX per Cat 6A.

### Lab 2 — Patch Panel Cleanup
Documenta un rack disordinato: fotografa fronte e retro, identifica ogni patch cord, crea la patch schedule, rietichetta secondo TIA-606-C, riorganizza con cable manager e velcro.

### Lab 3 — Link Budget Fibra
Per un collegamento fibra singolomodo OS2 di 10 km con 4 connettori LC UPC e 2 splices fusione, usando transceiver 10GBase-LR, calcola il link budget e il margine residuo.

### Lab 4 — Dimensionamento PoE
Per un ufficio con 30 AP WiFi 6 (25W ciascuno), 60 telefoni VoIP (7W ciascuno) e 20 telecamere IP PoE+ (15W ciascuno), dimensiona il budget PoE necessario sugli switch, includendo 20% di margine.

### Lab 5 — Progettazione PMI
Progetta il cablaggio strutturato per una sede di 80 dipendenti su 2 piani: inventario prese, scelta categoria, dimensionamento dorsale, layout rack, etichettatura, costo preventivo.

### Lab 6 — Troubleshooting OTDR
Data una traccia OTDR che mostra: loss 0.3 dB al primo evento (connettore), loss 0.05 dB al secondo evento (splice), loss 1.2 dB al terzo evento (anomalo) — identifica la probabile causa del terzo evento e proponi azione correttiva.

---

## Auto-valutazione
1. Spiega la differenza tra Permanent Link e Channel model.
2. Perche Cat 6A e preferibile a Cat 6 per nuove installazioni?
3. Descrivi il ruolo di TIA-606-C nel cablaggio strutturato.
4. Cosa succede se la schermatura di un cavo S/FTP non e collegata a terra?
5. Calcola il link budget per un collegamento OM4 di 200m con 4 connettori a 10G.
6. Spiega i tre livelli di cancellazione dati NIST SP 800-88 applicati ai supporti.
7. Descrivi la procedura corretta per la pulizia di un connettore fibra LC.
8. Cosa implica il derating PoE per bundling secondo TSB-184-A?
9. Quali sono le differenze tra Euroclass Cca e B2ca per i cavi dati?
10. Descrivi il ruolo del Single Pair Ethernet (SPE) negli edifici intelligenti.
11. Perche WiFi 7 richiede Cat 6A come baseline minima per l'infrastruttura?
12. Calcola il numero di fibre necessarie per una dorsale 800G con trunk MTP/MPO-16.

---

## Normativa Antincendio e CPR per Cavi

### Regolamento Prodotti da Costruzione (CPR)

Il Regolamento Europeo sui Prodotti da Costruzione (CPR, Regulation EU 305/2011) impone che tutti i cavi installati permanentemente all'interno degli edifici siano classificati secondo la norma armonizzata **EN 50575** per le prestazioni in caso di incendio. Questo requisito e diventato obbligatorio dal 1 luglio 2017 e si applica a tutti i cavi dati, telefonia, fibra ottica e coassiali installati in modo permanente — incluso il cablaggio strutturato.

La classificazione avviene secondo il sistema **Euroclass**, che prevede sette classi di reazione al fuoco:

| Euroclass | Prestazione al fuoco | Applicazione tipica | Sistema AVCP |
|-----------|---------------------|---------------------|--------------|
| **Aca** | Non combustibile | Cavi minerali speciali | Sistema 1+ |
| **B1ca** | Contributo molto limitato al fuoco | Vie di fuga critiche, ospedali | Sistema 1+ |
| **B2ca** | Contributo limitato al fuoco | Vie di fuga, edifici pubblici | Sistema 1+ |
| **Cca** | Contributo limitato al fuoco | Uffici, edifici commerciali standard | Sistema 1+ |
| **Dca** | Contributo medio al fuoco | Aree a basso rischio, magazzini | Sistema 3 |
| **Eca** | Contributo al fuoco non determinato | Uso temporaneo, prove | Sistema 4 |
| **Fca** | Nessuna prestazione dichiarata | Non ammesso in edifici permanenti | Nessuno |

### Criteri Aggiuntivi di Classificazione

Per le classi B1ca, B2ca, Cca e Dca, la classificazione include tre criteri aggiuntivi:

**Produzione di fumo (smoke):**
- **s1** (bassa opacita), con sottoclassi **s1a** (bassissima) e **s1b** (bassa)
- **s2** (opacita media)
- **s3** (nessun requisito di opacita)

**Gocce/particelle infiammate (droplets):**
- **d0** — nessuna goccia/particella infiammata entro 1200 s
- **d1** — nessuna goccia/particella che persiste piu di 10 s entro 1200 s
- **d2** — nessun requisito

**Acidita dei fumi (acidity):**
- **a1** — acidita e conduttivita dei fumi molto basse (equivalente LSZH)
- **a2** — acidita e conduttivita medie
- **a3** — nessun requisito

Un cavo classificato **Cca-s1a,d1,a1** indica: contributo limitato al fuoco, bassissima opacita fumi, nessuna goccia persistente, acidita molto bassa. Questa e la classificazione raccomandata per uffici standard in Italia.

### Requisiti per Ambiente in Italia

La normativa italiana sulla prevenzione incendi (D.M. 3 agosto 2015 — Codice di Prevenzione Incendi, e successive integrazioni) non specifica direttamente le Euroclass per i cavi dati, ma il principio di proporzionalita impone classificazioni adeguate al rischio. La prassi professionale italiana si e consolidata come segue:

| Zona edificio | Euroclass minima raccomandata | Motivazione |
|---------------|-------------------------------|-------------|
| Vie di fuga, scale, corridoi protetti | **B2ca-s1a,d1,a1** | Massima protezione per evacuazione |
| Ambienti ad alto affollamento (sale riunioni, open space >50 pers.) | **B2ca-s1,d1,a1** | Riduzione rischio fumo tossico |
| Uffici standard, locali tecnici | **Cca-s1b,d1,a1** | Buon compromesso prestazione/costo |
| Magazzini, aree tecniche non presidiate | **Dca-s2,d2,a2** | Rischio basso, costo minimo |
| Controsoffitti e plenum | **B2ca-s1a,d0,a1** | Spazio di circolazione aria, critico |
| Locali tecnici IT (server room, MDF) | **Cca-s1a,d0,a1** | Protezione apparecchiature + fumi |

### Differenze tra LSZH e Classificazione CPR

Un errore comune e confondere la dicitura **LSZH** (Low Smoke Zero Halogen) con la classificazione CPR. LSZH descrive il materiale della guaina del cavo: indica che la guaina non contiene alogeni (cloro, bromo, fluoro) e produce fumi a bassa tossicita. Tuttavia, un cavo LSZH **non ha automaticamente** una classificazione Euroclass: solo i test secondo EN 50575 determinano la classe. In pratica, la maggior parte dei cavi LSZH di buona qualita raggiunge Cca o B2ca, ma la classificazione va verificata sulla Dichiarazione di Prestazione (DoP) del produttore.

### Implicazioni Pratiche per il Cablaggio Strutturato

1. **Capitolati e specifiche**: ogni capitolato per cablaggio strutturato deve specificare la Euroclass minima richiesta per ogni zona dell'edificio. Indicare solo "cavo LSZH" e insufficiente.
2. **Documentazione**: conservare la DoP (Dichiarazione di Prestazione) di ogni lotto di cavo installato, con riferimento alla norma EN 50575 e alla Euroclass dichiarata.
3. **Marcatura CE**: ogni cavo CPR deve riportare la marcatura CE con riferimento alla DoP. L'installatore deve verificare la presenza della marcatura prima della posa.
4. **Costo**: i cavi B2ca costano circa 30-50% in piu rispetto a Cca, e Cca costa circa 15-25% in piu rispetto a Dca. Il sovracosto e giustificato dalla riduzione del rischio e dalla conformita normativa.
5. **Fibra ottica**: anche i cavi in fibra ottica sono soggetti alla classificazione CPR. I cavi fibra tight-buffered indoor sono tipicamente classificati Cca o B2ca. I cavi fibra loose-tube per posa esterna non richiedono classificazione CPR se non penetrano all'interno dell'edificio.

### Verifica e Conformita

Prima dell'accettazione di un impianto di cablaggio strutturato, il direttore lavori o il responsabile IT deve verificare:

- [ ] Ogni bobina di cavo ha etichetta con Euroclass e riferimento DoP
- [ ] La Euroclass e conforme a quanto specificato nel capitolato
- [ ] La DoP e disponibile e consultabile (tipicamente su sito web del produttore)
- [ ] I cavi posati in controsoffitti e plenum hanno classe almeno B2ca-s1a,d0,a1
- [ ] I cavi nelle vie di fuga hanno classe almeno B2ca-s1a,d1,a1
- [ ] La documentazione di certificazione include i riferimenti CPR

---

## Aggiornamenti Standard 2024-2026

### TIA-568.2-E (Novembre 2024)

A novembre 2024 la TIA ha pubblicato due documenti significativi:

**ANSI/TIA-568.2-E** (Balanced Twisted-Pair Telecommunications Cabling and Components Standard): aggiornamento della precedente revisione -D. Le principali modifiche includono correzioni di errori noti nelle specifiche di canale, aggiornamento dei requisiti per i componenti Cat 6A in linea con l'esperienza di campo accumulata dal 2020, e allineamento con le ultime revisioni ISO/IEC 11801.

**ANSI/TIA-568.5-1** (Addendum 1: Technical Corrections to Transmission Requirements): corregge un'incompatibilita tra le specifiche PSAFEXT (Power Sum Attenuation to Far-End Crosstalk) del canale e del cavo, che poteva causare risultati di certificazione inconsistenti in condizioni limite. Questo addendum e particolarmente rilevante per i tester di certificazione: i firmware dei Fluke DSX e Ideal LanTEK vanno aggiornati per incorporare le nuove soglie corrette.

### Consolidamento TIA-568.1-F

Il comitato tecnico TR-42 della TIA sta lavorando alla revisione **ANSI/TIA-568.1-F**, che consolidera tre standard esistenti in un unico documento:

- **TIA-568.1** (Commercial Building Cabling Standard)
- **TIA-568.0** (Generic Telecommunications Cabling for Customer Premises)
- **TIA-862** (Building Automation Systems Cabling Standard)

La logica del consolidamento e eliminare sovrapposizioni e contraddizioni tra i tre documenti, semplificando il riferimento per progettisti e installatori. La pubblicazione e stimata per fine 2026 o inizio 2027. Nel frattempo, i tre standard esistenti rimangono attivi e validi.

### Addendum TIA-942 per Intelligenza Artificiale

La TIA ha annunciato la preparazione di un addendum allo standard TIA-942 specificamente orientato alle infrastrutture AI. I data center per carichi di lavoro AI/ML presentano esigenze di cablaggio radicalmente diverse rispetto ai data center tradizionali:

- Densita di fibra 10 volte superiore: un rack GPU NVIDIA DGX richiede decine di fibre contro le 2-4 di un rack server tradizionale.
- Backbone fiber-only sopra la soglia dei 40G/30m: nessun caso d'uso per rame sopra questa velocita/distanza.
- Percorsi di raffreddamento liquido integrati con i pathway del cablaggio: tubi refrigerante e fibre corrono negli stessi spazi, richiedendo separazione e protezione aggiuntive.
- Requisiti di latenza ultra-bassa: le topologie spine-leaf per AI richiedono equalizzazione della lunghezza dei percorsi fibra per minimizzare lo skew tra i link paralleli.

### ISO/IEC 11801 — Classi I e II (Cat 8)

Lo standard ISO/IEC 11801-1:2017 ha introdotto due nuove classi per il cablaggio ad altissima frequenza:

**Classe I (Category 8.1)**: fino a 2000 MHz, design minimo U/FTP o F/UTP, connettore 8P8C (RJ-45). **Pienamente retrocompatibile** con Class EA (Cat 6A) — un link Class I funziona con qualsiasi apparato Cat 6A. Distanza massima 30 m (canale). Uso previsto: data center, collegamento top-of-rack a switch aggregazione.

**Classe II (Category 8.2)**: fino a 2000 MHz, design minimo F/FTP o S/FTP, connettori **TERA** (Siemon) o **GG45** (Nexans). Interoperabile con Class FA (Cat 7A) ma **non compatibile con RJ-45**. Questo limita l'adozione a contesti specifici dove i connettori proprietari sono gia in uso — essenzialmente il mercato tedesco e nordeuropeo.

In Italia, Cat 8.1 (Class I) e la scelta logica per i rari casi che richiedono Cat 8, perche mantiene la compatibilita con l'ecosistema RJ-45 esistente. Cat 8.2 e da considerare solo in ristrutturazioni di data center che gia usano connettori TERA o GG45.

### Allineamento EN 50173 / EN 50174

Gli standard europei CENELEC mantengono l'allineamento con ISO/IEC 11801:

- **EN 50173-1:2018**: recepisce le classi fino a Class II, allineato a ISO/IEC 11801-1.
- **EN 50174-1/2/3**: specifiche di installazione aggiornate per supportare i requisiti di posa dei cavi Cat 6A schermati e Cat 8, con particolare attenzione ai raggi di curvatura, alla separazione da cavi di potenza e alla gestione termica per PoE++ ad alta densita.

---

## Single Pair Ethernet (SPE) e TIA-568.5

### Cos'e il Single Pair Ethernet

Il Single Pair Ethernet (SPE) rappresenta un'evoluzione fondamentale per l'Internet of Things (IoT) industriale e la building automation. A differenza dell'Ethernet tradizionale che utilizza 2 o 4 coppie twistate (4 o 8 conduttori), SPE trasmette dati e, opzionalmente, alimentazione su **una singola coppia** di conduttori (2 fili).

Questa semplificazione riduce drasticamente dimensioni, peso e costo del cablaggio, rendendolo adatto a sensori, attuatori, dispositivi di controllo accessi, illuminazione intelligente, sistemi HVAC e qualsiasi dispositivo IoT che richiede connettivita Ethernet ma non necessita di banda elevata.

### Standard IEEE per SPE

| Standard IEEE | Data Rate | Distanza max | Coppie | Applicazione |
|---------------|-----------|--------------|--------|--------------|
| **10BASE-T1S** | 10 Mbps | 25 m (multidrop) | 1 coppia | Sensori, attuatori, bus locale |
| **10BASE-T1L** | 10 Mbps | 1000 m | 1 coppia | Building automation, HVAC, lunga distanza |
| **100BASE-T1** | 100 Mbps | 15 m | 1 coppia | Automotive, telecamere embedded |
| **1000BASE-T1** | 1 Gbps | 15-40 m | 1 coppia | Automotive, robotica industriale |

**10BASE-T1L** e la variante piu rilevante per il cablaggio strutturato degli edifici commerciali: 10 Mbps su una singola coppia fino a **1000 metri**, con alimentazione PoDL (Power over Data Line) fino a 50W integrata nello stesso doppino. Questo copre edifici interi con un singolo run di cavo, eliminando la necessita di switch intermedi per dispositivi IoT a bassa banda.

### TIA-568.5 e Infrastruttura SPE

La TIA ha pubblicato lo standard **ANSI/TIA-568.5** nel 2022, che definisce le specifiche dei componenti SPE per ambienti commerciali. Parallelamente, lo standard **ANSI/TIA-568.7** (Industrial Single Pair Ethernet) estende le specifiche agli ambienti industriali, dove le condizioni ambientali (temperatura, vibrazioni, polveri, umidita) richiedono componenti rinforzati.

**Connettori SPE standardizzati:**

- **IEC 63171-1** (LC-style, per ufficio): connettore compatto tipo LC per installazione in placche standard.
- **IEC 63171-2** (industrial variant): connettore industriale IP20 per ambienti controllati.
- **IEC 63171-5** (IX Industrial): connettore IP20 per installazioni industriali.
- **IEC 63171-6** (Harting T1 Industrial): connettore IP67 robusto per ambienti gravosi — polvere, acqua, vibrazioni. Standard de facto per l'IIoT industriale.

### Integrazione SPE nel Cablaggio Strutturato

In un edificio commerciale moderno, la coesistenza di cablaggio tradizionale (Cat 6A / fibra) e SPE segue un modello gerarchico:

```
Core network (fibra OS2 / Cat 6A 10G)
        |
Distribution switch con porte SPE
        |
SPE backbone (10BASE-T1L, fino a 1000m)
        |
Dispositivi IoT: sensori temperatura, controllo illuminazione,
                  rilevatori presenza, termostati HVAC,
                  lettori badge, sensori qualita aria,
                  contatori energia, valvole smart
```

Il vantaggio operativo e enorme: un singolo cavo a 2 conduttori (piu sottile, piu leggero, piu economico del Cat 6A a 8 conduttori) porta dati + alimentazione a centinaia di dispositivi IoT distribuiti nell'edificio, senza necessita di switch di piano aggiuntivi per i dispositivi a bassa banda.

### Implicazioni per la Progettazione

Per un nuovo impianto di cablaggio strutturato nel 2026, la raccomandazione e:

1. **Predisporre cavidotti separati** per il futuro cablaggio SPE, anche se i dispositivi IoT non sono ancora pianificati. Il costo della predisposizione e trascurabile rispetto al costo di aggiungere percorsi in futuro.
2. **Prevedere porte SPE** sugli switch di distribuzione: i principali vendor (Cisco, Aruba, Juniper) stanno introducendo moduli SPE nei chassis modulari enterprise.
3. **Documentare l'infrastruttura SPE** con la stessa disciplina del cablaggio Cat 6A: etichettatura TIA-606-C, patch schedule, test di certificazione.

---

## WiFi 7 e Requisiti Infrastrutturali per il Cablaggio

### Perche WiFi 7 Cambia le Regole del Gioco

WiFi 7 (IEEE 802.11be, ratificato 2024) rappresenta un salto generazionale nella velocita wireless: throughput teorico fino a 46 Gbps, con capacita reali per singolo AP che superano facilmente i 5-10 Gbps in condizioni ottimali. Questo ha un impatto diretto sul cablaggio strutturato: **l'access point non puo erogare piu banda di quella che riceve dal cavo**.

Un AP WiFi 7 collegato con un uplink 1 Gbps diventa un collo di bottiglia che spreca il 80-90% della capacita wireless. La regola pratica per il 2025-2026 e:

- **Baseline minima**: uplink **2.5 Gbps** per ogni AP WiFi 6E/7 (NBASE-T su Cat 5e/6 esistente, o Cat 6A nativo).
- **Raccomandato**: uplink **5 Gbps o 10 Gbps** per AP in zone ad alta densita (sale conferenze, open space, auditorium).
- **High-density**: uplink **10 Gbps** con Cat 6A nativo, che e il massimo supportato dall'interfaccia cablata degli AP enterprise attuali.

### Cat 6A come Baseline Obbligatoria per WiFi 7

Cat 6A e la specifica obbligatoria per qualsiasi nuova installazione WiFi 7, per tre ragioni convergenti:

1. **Banda**: supporta 10GBASE-T su 100 m, coprendo il massimo uplink degli AP attuali e futuri.
2. **PoE++**: gli AP WiFi 7 enterprise consumano circa **40-50W** ciascuno, richiedendo IEEE 802.3bt Type 3 (60W al PSE). Cat 6A, con i conduttori AWG 23 a bassa resistenza DC, gestisce questa potenza con margine termico adeguato anche in bundle. Cat 6 (AWG 24) e marginale per PoE++ a piena distanza.
3. **Alien crosstalk**: in installazioni con AP densi (uno ogni 10-15 m nei corridoi), i cavi corrono in bundle stretti. Cat 6A e l'unica categoria che specifica e testa i limiti AXT, garantendo che la diafonia tra cavi nel bundle non degradi il link 10G.

### Dimensionamento Infrastruttura WiFi 7

Per un edificio commerciale che pianifica WiFi 7, il dimensionamento del cablaggio segue queste regole:

**Densita AP**: rispetto a WiFi 5/6, WiFi 7 richiede il **30-50% in piu di access point** per coprire la stessa area con prestazioni ottimali. Questo perche WiFi 7 opera anche nella banda 6 GHz, che ha portata piu ridotta rispetto alle bande 2.4/5 GHz.

**Pianificazione punti rete per AP:**

| Tipo di ambiente | AP per 1000 mq | Uplink consigliato | PoE richiesto |
|-----------------|-----------------|---------------------|---------------|
| Ufficio standard (30-50 utenti/1000mq) | 3-4 AP | 2.5G-5G | Type 3 (60W) |
| Open space alta densita (>80 utenti) | 5-7 AP | 5G-10G | Type 3 (60W) |
| Sala conferenze / auditorium | 1-2 AP per sala | 10G | Type 3 (60W) |
| Magazzino / produzione | 2-3 AP | 2.5G | Type 2 (30W) |
| Aree esterne (cortili, parcheggi) | 1 AP ogni 500 mq | 2.5G | Type 3 (60W) |

**Budget PoE per switch WiFi 7:**

Un piano con 10 AP WiFi 7 a 50W ciascuno richiede 500W di budget PoE solo per gli AP. Aggiungendo telefoni VoIP (7W × 20 = 140W) e telecamere IP (15W × 8 = 120W), il totale supera 760W. Uno switch 48-port con budget PoE di 740W non e sufficiente: servono switch con budget PoE 960W+ o stack con alimentatori ridondanti.

### Integrazione Site Survey RF e Progetto Cablaggio

Il progetto di cablaggio per WiFi 7 non puo essere separato dal site survey RF. La procedura corretta e:

1. **Site survey predittivo**: modellazione RF con software (Ekahau, iBwave, NetAlly AirMagnet) per determinare posizioni AP ottimali.
2. **Verifica punti cavo**: per ogni AP, verificare che un percorso cavo Cat 6A sia fattibile dalla posizione AP al TR piu vicino, entro i 90 m di permanent link.
3. **Predisposizione spare**: posare il 20% di cavi aggiuntivi verso posizioni alternative per futuri riposizionamenti AP.
4. **Posa cavo al soffitto**: gli AP a soffitto richiedono punti rete a soffitto con cassetta 503 o scatola di derivazione dedicata, con slack loop di 2-3 m per flessibilita di montaggio.
5. **Documentazione integrata**: la mappa dei punti AP deve essere parte integrante del floor plan del cablaggio, con riferimenti incrociati tra ID presa e ID AP.

---

## Cablaggio per Infrastrutture AI e Data Center ad Alta Densita

### La Rivoluzione della Densita di Fibra

I data center per carichi di lavoro AI/ML (training e inference di modelli LLM, computer vision, simulazioni) hanno trasformato radicalmente i requisiti di cablaggio rispetto ai data center tradizionali. Le differenze chiave:

**Densita di fibra**: un rack GPU NVIDIA DGX H100/B200 richiede **40-80 fibre ottiche** per la sola connettivita di rete (InfiniBand 400G o Ethernet 800G), contro le 2-4 fibre di un rack server tradizionale. Un cluster AI di 128 GPU richiede migliaia di fibre, organizzate in trunk pre-terminati ad altissima densita.

**Velocita**: la progressione nel 2024-2026 e:
- **400G** (2024): velocita base per backbone AI, 8 fibre per link (4 × 100G).
- **800G** (2025): deployment massivo, 8 fibre per link con transceiver OSFP 2×400G.
- **1.6T** (2026): emergente, 16 fibre per link con transceiver OSFP-XD.

**Topologia**: le reti AI usano topologie fat-tree o Clos multi-tier con migliaia di link paralleli, dove l'equalizzazione della lunghezza dei percorsi fibra e critica per minimizzare lo skew tra i link.

### Trunk Pre-Terminati MTP/MPO

Nei data center AI, il cablaggio pre-terminato in fabbrica (trunk cable) ha sostituito quasi completamente la terminazione in campo per la dorsale. I vantaggi sono decisivi:

- **Qualita**: connettori terminati in fabbrica con attrezzature automatizzate garantiscono loss < 0.1 dB per connettore, contro i 0.3-0.5 dB tipici della terminazione manuale in campo.
- **Velocita di deployment**: un trunk da 288 fibre si installa in minuti, contro giorni di terminazione manuale.
- **Riduzione errori**: nessun rischio di contaminazione connettori durante la terminazione.

**Configurazioni MTP/MPO comuni:**

| Configurazione | Fibre per connettore | Applicazione tipica |
|----------------|----------------------|---------------------|
| **MTP-12** | 12 fibre | 40G (4×10G), 100G SR4, breakout a LC duplex |
| **MTP-16** | 16 fibre | 400G DR4+, 800G, percorso upgrade verso 1.6T |
| **MTP-24** | 24 fibre | 100G SR10 (legacy), alta densita |
| **MTP-32** | 32 fibre | 800G SR8, applicazioni emergenti |

**Gestione della polarita**: i trunk MTP/MPO devono rispettare una delle tre configurazioni di polarita standardizzate (TIA-568.3):

- **Tipo A (straight)**: key up a entrambe le estremita, fibre diritte. Richiede adattatore key-up/key-down a un estremo per mantenere la polarita.
- **Tipo B (reversed)**: key up a un'estremita, key down all'altra. Le fibre si incrociano. Configurazione piu comune per 40G/100G.
- **Tipo C (pair flip)**: coppie adiacenti invertite. Usato per applicazioni duplex senza cassetta di breakout.

La scelta della polarita deve essere coerente in tutto il data center e documentata nel progetto esecutivo. Mescolare polarita diverse causa errori di collegamento che sono difficili da diagnosticare.

### Fibra OS2 vs OM4/OM5 per AI Data Center

Per data center AI nel 2025-2026, le raccomandazioni sono chiare:

**OS2 singolomodo** e la scelta primaria per qualsiasi nuova infrastruttura AI:
- Supporta 800G e 1.6T senza sostituzione fisica della fibra — solo upgrade dei transceiver.
- Distanze fino a 10 km con transceiver standard, fino a 40+ km con amplificazione.
- Percorso di upgrade verso 3.2T e oltre con la stessa fibra installata oggi.
- Trunk MTP-16 in OS2 offrono un percorso chiaro attraverso almeno 3 generazioni di velocita di rete.

**OM5 (WBMMF)** ha un ruolo di nicchia:
- Utile per link brevi (< 100 m) dove il costo inferiore dei transceiver VCSEL compensa il limite di distanza.
- Supporta 400G tramite SWDM4 su una sola coppia di fibre, riducendo il conteggio fibre nei trunk.
- Limitato a ~50-70 m per 800G con tecnologia VCSEL attuale.

**OM4** rimane adeguato per installazioni esistenti che non superano 400G, ma non e la scelta raccomandata per nuove costruzioni orientate all'AI.

### Considerazioni su Raffreddamento Liquido e Pathway

I rack GPU AI generano 30-70 kW per rack (contro i 5-10 kW di un rack server tradizionale), richiedendo raffreddamento liquido diretto (direct-to-chip liquid cooling o rear-door heat exchanger). Questo introduce tubazioni refrigerante (acqua o fluido dielettrico) che condividono gli stessi pathway del cablaggio strutturato.

Implicazioni pratiche:
- **Separazione fisica**: le tubazioni refrigerante devono essere separate dal cablaggio fibra con barriere o canaline dedicate per evitare danni da condensa o perdite.
- **Percorsi sopraelevati**: il cablaggio fibra nei data center AI va preferibilmente su cable tray sopraelevato, sopra i percorsi delle tubazioni.
- **Punti di accesso**: prevedere punti di accesso al cablaggio che non richiedano lo smontaggio delle tubazioni di raffreddamento.
- **Protezione meccanica**: i cavi fibra devono avere guaina rinforzata (armored fiber) nei tratti dove coesistono con tubazioni sotto pressione.

---

## Procedure di Installazione Passo-Passo

### Procedura 1 — Posa Cablaggio Orizzontale Cat 6A

Questa procedura copre la posa di un singolo run orizzontale dal TR alla presa utente.

**Materiali necessari:**
- Bobina cavo Cat 6A F/UTP Cca-s1b,d1,a1 (o classe CPR specificata)
- Keystone jack Cat 6A (es. Panduit Mini-Com TX6A, Belden REVConnect, Nexans LANmark-6A)
- Placca utente 2 porte (es. Panduit CFPE2)
- Scatola da incasso 503
- Fascette velcro (no zip-tie)
- Punch-down tool (Fluke D914 o equivalente)
- Tester base (Fluke MicroScanner PoE o equivalente)
- Metro, tagliacavo, spelacavo di precisione

**Fasi operative:**

```
FASE 1 — Preparazione percorso
  1.1  Verificare il percorso sulla planimetria di progetto
  1.2  Ispezionare visivamente canalina/controsoffitto per spazio disponibile
  1.3  Verificare che il percorso non superi 90 m (misurare con metro laser)
  1.4  Verificare separazione da cavi elettrici (200 mm UTP, 50 mm STP)
  1.5  Identificare passaggi tagliafuoco e preparare materiale firestop

FASE 2 — Tiraggio cavo
  2.1  Inserire sonda passacavi (nylon/teflon) dal TR alla presa utente
  2.2  Fissare il cavo alla sonda con nastro isolante (NON con nodo)
  2.3  Tirare lentamente e uniformemente — forza max 110 N (TIA-568)
  2.4  NON superare mai il raggio di curvatura minimo (4× OD ≈ 28-32mm)
  2.5  Lasciare slack loop di 3 m al lato rack e 30 cm al lato presa
  2.6  Fissare con velcro ogni 1.5 m nella canalina (no zip-tie stretti)
  2.7  Etichettare entrambe le estremita con ID univoco TIA-606-C

FASE 3 — Terminazione lato presa utente
  3.1  Spellare guaina esterna per 25 mm (no di piu)
  3.2  Separare le coppie mantenendo torsione fino al contatto IDC
  3.3  Rispettare schema T568B (o T568A se da capitolato)
  3.4  Untwist massimo 13 mm per Cat 6A
  3.5  Punch-down con utensile a molla — NON forbici, NON pinze
  3.6  Verificare che ogni conduttore sia completamente inserito nel IDC
  3.7  Tagliare eccesso conduttore (il tool lo fa in automatico)
  3.8  Chiudere keystone, montare in placca, fissare in scatola 503

FASE 4 — Terminazione lato patch panel
  4.1  Lasciare 3 m di slack loop nel rack (per futuri riterminazioni)
  4.2  Instradare il cavo nella canalina verticale del rack
  4.3  Terminare sul keystone jack del patch panel modulare
  4.4  Schema identico al lato presa (T568B-T568B, mai misto)
  4.5  Untwist massimo 13 mm
  4.6  Punch-down e verifica inserimento
  4.7  Montare keystone nel patch panel
  4.8  Etichettare la porta con ID presa corrispondente

FASE 5 — Test immediato
  5.1  Collegare tester base (MicroScanner) al lato rack
  5.2  Inserire remoto terminale al lato presa
  5.3  Verificare: wire map OK, lunghezza OK (< 90 m), no split pair
  5.4  Se FAIL: verificare terminazione, riterminare se necessario
  5.5  Documentare risultato nel log di posa
```

### Procedura 2 — Terminazione Fibra con Connettore Pre-Polished (Meccanico)

Per installazioni dove la giunzione per fusione non e disponibile o non e giustificata economicamente, i connettori pre-polished (field-installable) offrono un'alternativa pratica.

**Materiali:**
- Connettori field-installable LC UPC (es. Corning UniCam, 3M NPC, Panduit OptiCam)
- Cleaver di precisione
- Pinza spelatura fibra
- Alcol isopropilico 99%+ e lint-free wipe
- Microscopio ispezione 200-400x

**Fasi operative:**

```
1. Spellare guaina esterna del cavo per la lunghezza specificata dal produttore connettore
2. Rimuovere buffer (tight-buffer) con pinza a calore per 40 mm
3. Pulire fibra nuda con alcol isopropilico e lint-free wipe
4. Effettuare cleave di precisione alla lunghezza specificata (tipicamente 10-12 mm)
5. Inserire la fibra nel connettore pre-polished fino al contatto con la fibra stub interna
6. Aggraffare/bloccare il connettore secondo le istruzioni del produttore
7. Ispezionare il ferrule con microscopio: verificare assenza di contaminanti,
   graffi o difetti sulla superficie di contatto
8. Misurare insertion loss con power meter: deve essere < 0.5 dB per connettore
9. Se IL > 0.5 dB: ripulire, re-inserire o sostituire il connettore
```

### Procedura 3 — Popolamento Rack 19"

**Sequenza raccomandata per il montaggio di un nuovo rack:**

```
1. Posizionare il rack nella posizione definitiva, livellare, fissare al pavimento
2. Installare le PDU verticali zero-U sui montanti laterali posteriori
3. Installare i cable manager verticali (se previsti) sui montanti anteriori laterali
4. Installare dal BASSO verso l'ALTO:
   4.1  UPS (peso massimo, in basso per stabilita)
   4.2  Server e NAS (pesanti)
   4.3  Switch out-of-band management
   4.4  Blanking panel per gli U vuoti
   4.5  Switch dati (al centro o top-of-rack per data center)
   4.6  Cable manager orizzontale 1U
   4.7  Patch panel dati (sopra ogni switch)
   4.8  Cable manager orizzontale 1U
   4.9  Patch panel fibra (in alto)
   4.10 Cable manager orizzontale 1U
5. Collegare alimentazione: PDU A su circuito 1, PDU B su circuito 2
6. Collegare bonding: rack → TGB con conduttore 6 AWG (16 mm²)
7. Instradare i cavi orizzontali nella canalina verticale del rack
8. Collegare patch cord dati: instradare in cable manager prima di inserire
9. Collegare patch fibra: instradare in cassetta fibra dedicata
10. Etichettare ogni porta, ogni cavo, ogni apparato
11. Fotografare fronte e retro del rack completato
12. Aggiornare patch schedule e documentazione
```

---

## Checklist Operativa di Progetto

### Pre-Installazione

- [ ] Site survey completato con misure distanze e percorsi
- [ ] Planimetria aggiornata con posizione di ogni presa TO
- [ ] Capitolato tecnico approvato con specifiche categoria cavo, Euroclass CPR, schermatura
- [ ] Bill of Materials (BoM) completa con codici prodotto e quantita
- [ ] Verifica disponibilita materiali presso distributore
- [ ] Locali tecnici (MDF/IDF) preparati: alimentazione, climatizzazione, accesso
- [ ] Rack ordinati e in loco
- [ ] Canalizzazione (canaline, tubi, J-hook) installata
- [ ] Barriere tagliafuoco predisposte per ogni attraversamento piano/parete REI
- [ ] Coordinamento con elettricista per separazione cavi potenza/dati
- [ ] Piano di etichettatura TIA-606-C definito e condiviso con il team
- [ ] Tester di certificazione prenotato e calibrato (Fluke DSX-8000 o equivalente)

### Durante la Posa

- [ ] Ogni cavo etichettato a entrambe le estremita prima della posa
- [ ] Forza di tiro non superiore a 110 N (monitorare con dinamometro se necessario)
- [ ] Raggio di curvatura minimo rispettato in ogni punto (4× OD per rame, 30 mm per fibra)
- [ ] Separazione da cavi elettrici verificata (200 mm UTP, 50 mm STP parallelo)
- [ ] Velcro utilizzato per fissaggio (no zip-tie stretti)
- [ ] Riempimento canalina non superiore al 40%
- [ ] Slack loop lasciato a entrambe le estremita (3 m lato rack, 30 cm lato presa)
- [ ] Firestop applicato ad ogni attraversamento piano/parete REI
- [ ] Test wire map eseguito su ogni link immediatamente dopo la terminazione
- [ ] Foto di documentazione scattate durante la posa (percorsi critici, passaggi)

### Post-Installazione

- [ ] Certificazione completa di ogni link (Permanent Link model) con tester professionale
- [ ] Report di certificazione esportato in PDF e archiviato per ogni link
- [ ] Patch schedule completa e aggiornata (patch panel ↔ switch, VLAN, utente)
- [ ] Floor plan cablaggio aggiornato con posizione esatta di ogni presa
- [ ] Foto fronte e retro di ogni rack, archiviate con data
- [ ] Documentazione CPR: DoP di ogni lotto cavo archiviata
- [ ] Bonding/grounding verificato: continuita rack → TGB → TMGB
- [ ] Test PoE funzionale su ogni porta destinata a dispositivi PoE
- [ ] Consegna documentazione al committente (certificazione, planimetrie, patch schedule, foto rack)

### Collaudo Finale

- [ ] Tutti i link certificati PASS (margine > 3 dB consigliato)
- [ ] Link con margine 0-3 dB documentati e accettati con riserva
- [ ] Link FAIL riterminati e ricertificati
- [ ] Verifica funzionale end-to-end: collegamento apparato → presa → dispositivo
- [ ] Verifica PoE operativa con dispositivi reali (AP, telefoni, telecamere)
- [ ] Verifica dorsale fibra: OTDR o Tier 1 insertion loss su ogni tratta
- [ ] Accettazione formale con firma del committente e dell'installatore
- [ ] Attivazione garanzia produttore (se applicabile: inviare certificazione al vendor)

---

## Gestione del Ciclo di Vita dell'Infrastruttura

### Audit Annuale

L'infrastruttura di cablaggio strutturato ha una vita utile di 15-25 anni, ma richiede manutenzione e verifica periodica per mantenere le prestazioni. L'audit annuale e il meccanismo principale di controllo.

**Contenuto dell'audit annuale:**

1. **Riconciliazione documentale**: confronto tra la patch schedule documentata e lo stato fisico reale del rack. In sedi attive, le modifiche non documentate si accumulano rapidamente — entro 2 anni senza audit, la documentazione e tipicamente divergente dal reale per il 15-30% delle porte.

2. **Ispezione visiva rack**: verifica di:
   - Cable management integro (velcro non allentati, patch cord non aggrovigliati)
   - Etichette leggibili (sostituire quelle degradate da calore o UV)
   - Blanking panel presenti su tutti gli U vuoti
   - Ventilazione non ostruita da cavi o oggetti
   - Temperatura nel rack (termometro o sensore ambientale)
   - PDU funzionanti, indicatori visivi normali

3. **Identificazione ghost cable**: cavi posati ma non piu in uso, che occupano spazio nella canalina e riducono la capacita disponibile. In sedi con piu di 5 anni di attivita, i ghost cable possono rappresentare il 10-20% del cablaggio installato.

4. **Verifica PoE**: confronto tra budget PoE utilizzato e budget disponibile sugli switch, per identificare switch in sovraccarico o prossimi al limite.

5. **Test campione**: ricertificazione del 10% dei link (scelti a rotazione) per verificare che le prestazioni non siano degradate nel tempo.

### Pianificazione del Refresh

Il refresh del cablaggio va pianificato con anticipo di 2-3 anni rispetto alla fine vita prevista. I segnali che indicano la necessita di un refresh:

- **Prestazioni**: link che non reggono le velocita richieste (es. Cat 5e in un'infrastruttura che necessita 10G).
- **Densita**: canalizzazione al 90%+ di riempimento, impossibilita di aggiungere nuovi cavi.
- **Standard**: cablaggio installato con standard obsoleti (es. Cat 3 per fonia analogica, Cat 5 non-enhanced).
- **Conformita**: classificazione CPR insufficiente per il nuovo uso del locale (es. ufficio convertito in spazio ad alto affollamento).
- **Integrita**: link con certificazione marginale (margine 0-3 dB) che si avvicinano al limite dopo anni di invecchiamento.

### Decommissioning

La dismissione del cablaggio vecchio segue una procedura precisa:

1. **Mappatura**: identificare ogni cavo da rimuovere sulla planimetria, verificare che non ci siano cavi attivi nello stesso percorso che potrebbero essere disturbati.
2. **Disconnessione**: scollegare entrambe le estremita (rack e presa), etichettare come "da rimuovere".
3. **Rimozione**: estrarre il cavo dal percorso. Attenzione ai firestop: ogni barriera tagliafuoco attraversata deve essere ripristinata dopo la rimozione del cavo.
4. **Smaltimento**: i cavi in rame hanno valore di recupero (rame al kg). I cavi in fibra vanno smaltiti come rifiuto speciale (vetro). Le guaine PVC vanno separate dalle guaine LSZH per il riciclo corretto. Riferimento normativo: D.Lgs. 152/2006 (Codice dell'ambiente) per la gestione dei rifiuti da apparecchiature e cablaggio.
5. **Aggiornamento documentazione**: rimuovere i cavi dismessi dalla patch schedule e dalla planimetria, aggiornare le foto del rack.

### Documentazione del Ciclo di Vita

La documentazione dell'infrastruttura deve essere mantenuta per l'intera vita utile del cablaggio. I documenti critici sono:

| Documento | Formato | Conservazione | Aggiornamento |
|-----------|---------|---------------|---------------|
| Report certificazione link | PDF firmato | Intera vita utile + 5 anni | Mai modificato dopo collaudo |
| Patch schedule | Excel/CSV in repo Git | Permanente con versioning | Ad ogni modifica MAC |
| Floor plan cablaggio | DWG/PDF/Visio | Permanente con versioning | Ad ogni modifica |
| Foto rack | JPEG con timestamp | Permanente | Ad ogni modifica |
| DoP cavi (CPR) | PDF dal produttore | Intera vita utile | Mai (documento statico) |
| Bill of Materials | Excel | Permanente | Mai dopo collaudo |
| Registro audit | PDF/Excel | Permanente | Annuale |
| Mappa ghost cable | Aggiornamento floor plan | Con floor plan | Annuale |

**Suggerimento pratico**: mantenere tutta la documentazione in un repository Git dedicato (es. `infra-cabling-docs`) con commit per ogni modifica. Il versioning permette di ricostruire lo stato dell'infrastruttura a qualsiasi punto nel tempo — informazione preziosa durante il troubleshooting o per audit di conformita ISO 27001 / NIS2.

---

## Riferimenti

**Standard normativi**

- ANSI/TIA-568.0-E, .1-E, .2-E, .3-E (Commercial Building Telecommunications Cabling Standard).
- ANSI/TIA-569-E (Telecommunications Pathways and Spaces).
- ANSI/TIA-606-C (Administration Standard for Telecommunications Infrastructure).
- ANSI/TIA-607-D (Generic Telecommunications Bonding and Grounding).
- ANSI/TIA-942-C (Telecommunications Infrastructure Standard for Data Centers).
- ANSI/TIA TSB-184-A (Guidelines for Supporting Power Delivery over Balanced Twisted-Pair Cabling).
- ANSI/TIA TSB-162-A (Telecommunications Cabling Guidelines for 10GBase-T).
- ISO/IEC 11801-1:2017 (Generic cabling for customer premises).
- EN 50173-1:2018 (Information technology — Generic cabling systems).
- EN 50174-1/2/3 (Cabling installation specification and quality assurance).
- EN 50575 (Fire performance of cables — Euroclasses Cca, B2ca, etc.).
- IEEE 802.3af / 802.3at / 802.3bt (Power over Ethernet specifications).
- IEEE 802.3bz (NBASE-T, 2.5G/5G su Cat 5e/6).
- CEI 64-8 (Impianti elettrici utilizzatori — norma italiana).
- D.M. 3 agosto 2015 (Regola tecnica prevenzione incendi — barriere tagliafuoco).

**Risorse pratiche**

- BICSI Telecommunications Distribution Methods Manual (TDMM) — bibbia degli installatori cablaggio strutturato.
- Fluke Networks Cabling Knowledge Base (flukenetworks.com/knowledge-base).
- Panduit Design Guide for Structured Cabling.
- Belden Cable Selector Guide.
- The Fiber Optic Association (FOA) — corsi e certificazioni CFOT.
- Siemon Cabling System Design Guide.
- Nexans LANmark System Guide.
- CommScope SYSTIMAX Solutions Design Guide.

**Strumenti consigliati**

- Tester certificazione: Fluke DSX-8000, Ideal LanTEK IV, Softing WireXpert 4500.
- Tester base (wire map, TDR): Fluke MicroScanner PoE, Ideal VDV II.
- OTDR: Fluke OFP-200, EXFO MaxTester 730/940, Viavi T-BERD 5800.
- Microscopio fibra: Fluke FI-7000 FiberInspector Pro, EXFO FIP-435B.
- Splicer fusione: Fujikura 90S+, Sumitomo TYPE-82C+, INNO View 12R.
- Stampante etichette: Brother PT-D610BT/PT-E550W, Brady BMP41/BMP21.
- Pulizia connettori fibra: IBC OneClick LC/SC, Cletop Type-A.
- Punch-down tool: Fluke D914, Harris D-914, Krone LSA.

**Codici colore standard**

- TIA-598-D (Optical fiber cable color coding).
- ANSI/TIA-568.2-E Annex E (Wire color codes T568A/T568B).

**Certificazioni professionali per cablaggio**

- **BICSI RCDD** (Registered Communications Distribution Designer): certificazione di design per progettisti.
- **BICSI RTPM** (Registered Telecommunications Project Manager): gestione progetti cablaggio.
- **FOA CFOT** (Certified Fiber Optic Technician): certificazione specifica fibra ottica.
- **Vendor-specific**: Panduit CPST, Siemon CI, CommScope CI, Belden CI — installatore certificato dal produttore.

---

## Glossario

| Termine | Definizione |
|---|---|
| **TIA-568** | Standard cablaggio strutturato per edifici commerciali (ANSI/TIA). |
| **Cat 5e/6/6A/8** | Categorie di prestazione cavi balanced twisted-pair. |
| **T568A/B** | Convenzioni di pinout per connettori RJ-45. |
| **Patch panel** | Pannello di permutazione che collega cablaggio fisso a apparati attivi. |
| **TIA-606** | Standard di etichettatura e documentazione infrastruttura telecom. |
| **TIA-607** | Standard di messa a terra e bonding per sistemi telecom. |
| **TIA-569** | Standard per spazi e percorsi cablaggio (locali tecnici, condotti). |
| **TIA-942** | Standard cablaggio per data center. |
| **Permanent Link** | Tratto di cablaggio fisso dal patch panel alla presa utente (max 90 m). |
| **Channel** | Canale completo inclusi patch cord (max 100 m). |
| **NEXT** | Near-End Crosstalk — diafonia al lato trasmettitore. |
| **AXT** | Alien Crosstalk — diafonia tra cavi diversi. |
| **Insertion Loss** | Attenuazione del segnale lungo il cavo (dB). |
| **Return Loss** | Segnale riflesso per disadattamento impedenza (dB). |
| **OTDR** | Optical Time Domain Reflectometer — strumento diagnostica fibra. |
| **MDF/IDF** | Main/Intermediate Distribution Frame — locali tecnici. |
| **PoE/PoE+/PoE++** | Power over Ethernet (IEEE 802.3af/at/bt). |
| **UPC/APC** | Ultra Physical Contact / Angled Physical Contact — polishing fibra. |
| **SMF/MMF** | Single-Mode Fiber / Multi-Mode Fiber. |
| **OM3/OM4/OM5** | Classi di fibra multimodale laser-optimized. |
| **OS1/OS2** | Classi di fibra singolomodo. |
| **LSZH** | Low Smoke Zero Halogen — guaina cavo a bassa emissione fumi. |
| **VCSEL** | Vertical-Cavity Surface-Emitting Laser — trasmettitore fibra multimodale. |
| **Keystone jack** | Presa modulare removibile per patch panel e placche utente. |
| **Fusion splice** | Giunzione per fusione termica di fibre ottiche. |
| **TSB-184-A** | Linee guida TIA per PoE su cablaggio strutturato. |
| **Wire map** | Test di continuita e ordine dei conduttori. |
| **Delay skew** | Differenza di tempo di propagazione tra le coppie di un cavo. |
| **IDC** | Insulation Displacement Contact — contatto a spostamento di isolante. |
| **SPE** | Single Pair Ethernet — Ethernet su singola coppia, standard IEEE 802.3cg/cy. |
| **10BASE-T1L** | Standard SPE long-reach (fino a 1 km) per automazione industriale e building. |
| **10BASE-T1S** | Standard SPE short-reach multidrop con topologia bus, per sensori e IoT. |
| **PoDL** | Power over Data Line — alimentazione su singola coppia SPE (IEEE 802.3bu). |
| **CPR** | Construction Products Regulation (UE 305/2011) — regolamento prodotti da costruzione. |
| **Euroclass** | Sistema di classificazione europea reazione al fuoco cavi (Aca-Fca). |
| **DoP** | Declaration of Performance — dichiarazione di prestazione obbligatoria CPR. |
| **AVCP** | Assessment and Verification of Constancy of Performance — sistema di valutazione CPR. |
| **MTP/MPO** | Multi-fiber Push On — connettore multifibra ad alta densità (12/16/24/32 fibre). |
| **SWDM** | Short Wavelength Division Multiplexing — multiplazione su fibra multimodale OM5. |
| **WBMMF** | Wideband Multimode Fiber — fibra multimodale a banda larga (OM5, 850-953 nm). |
| **Fat-tree / Clos** | Topologia di rete non-blocking usata in data center ad alta densità. |
| **OSFP** | Octal Small Form Factor Pluggable — modulo ottico 800G/1.6T per data center AI. |
| **Leaf-spine** | Architettura di rete a due livelli tipica dei data center moderni. |
| **WiFi 7 (802.11be)** | Standard Wi-Fi di settima generazione con MLO, 320 MHz, 4K-QAM. |
| **MLO** | Multi-Link Operation — funzionalità WiFi 7 per aggregazione simultanea di bande. |
| **EN 50575** | Norma europea armonizzata per prestazione al fuoco dei cavi da costruzione. |
| **TIA-568.1-F** | Progetto di consolidamento standard cablaggio TIA (previsto 2026). |
| **TIA-568.5** | Standard TIA per cablaggio SPE single-pair in edifici commerciali. |
| **Classe I / II (ISO 11801)** | Classi cablaggio ISO per 25G/40G: Classe I = Cat 8.1 (RJ-45), Classe II = Cat 8.2 (non-RJ-45). |
| **IEC 63171-6** | Connettore SPE industriale IP20/IP67 per automazione e building. |
