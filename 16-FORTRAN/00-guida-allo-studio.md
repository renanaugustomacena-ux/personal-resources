# Piano Master — Dominio 16-FORTRAN

## Obiettivo di questo documento

Questo documento è il piano principale per costruire il dominio 16-FORTRAN come una area di studio densa, tecnica, pratica e professionale, con il medesimo standard di profondità che si vuole raggiungere nei domini più completi del repository, inclusi i contenuti di tipo “security” che sono molto estesi, strutturati e ricchi di dettaglio.

Il punto centrale non è solo “insegnare Fortran”, ma costruire un percorso completo che copra:
- il linguaggio e la sua filosofia
- l’ambiente di lavoro e la toolchain
- la programmazione scientifica
- la qualità del software
- l’integrazione con sistemi moderni e strumenti di produzione

## Filosofia di lavoro del dominio

Questo dominio deve essere costruito come un vero percorso di specializzazione, non come una raccolta di appunti sparsi. Ogni documento deve avere una funzione chiara:
- spiegare un concetto tecnico
- mostrare un caso pratico
- fornire esempi compilabili
- indicare errori comuni e best practice
- collegare il tema al contesto reale del scientific computing

## Fonte principale di riferimento

La struttura di questo piano è stata costruita in modo coerente con la documentazione ufficiale di Fortran-lang, in particolare sui temi principali che compaiono nella sezione ufficiale del sito:
- Quickstart tutorial
- Setup dell’ambiente di sviluppo
- Scelta del compilatore
- Compiling programs
- Building programs
- Best practices
- Intrinsic procedures
- Packaging e build tools
- Features moderne del linguaggio
- Fortran 95 e approccio moderno alla programmazione

Le fonti ufficiali da usare come riferimento metodologico sono:
- https://fortran-lang.org/
- https://fortran-lang.org/learn/
- https://fortran-lang.org/learn/quickstart/
- https://fortran-lang.org/learn/quickstart/hello_world/
- https://fortran-lang.org/packaging/

## Regola fondamentale: come fare i documenti lunghi e densi

Per fare documenti come quelli del dominio 15-SECURITY, la regola non è “scrivere più pagine”, ma “scrivere con struttura, profondità e utilità”. Ogni documento deve essere costruito come un capitolo tecnico vero e proprio, non come una pagina di appunti.

### Obiettivo di lunghezza minima
I documenti finali non devono essere mini-guide. Devono essere veri e propri documenti specialistici, con dimensioni comparabili a quelle dei documenti del dominio 15-SECURITY. In pratica, ogni documento principale deve puntare a:
- almeno 8.000-12.000 parole per i temi intermedi
- 12.000-20.000 parole per i temi centrali o molto tecnici
- documenti ancora più estesi per argomenti come performance, interoperabilità, scientific computing, build systems e capstone

Questa è la soglia minima da tenere presente: se un documento si ferma a poche centinaia di righe o a qualche migliaio di parole, non è sufficiente. Il documento deve essere pensato come una guida tecnica vera, non come una nota riassuntiva.

### Regola pratica anti-fintas
Se un documento raggiunge solo una struttura superficiale, poche sezioni e pochi esempi, non è completo. Un documento va considerato “serio” solo se contiene:
- una introduzione approfondita
- una spiegazione tecnica completa
- esempi dettagliati
- casi d’uso reali
- best practice
- errori comuni
- riferimenti e approfondimenti
- una parte sufficientemente estesa da essere utile davvero in studio e lavoro

### Regola mentale da usare durante la scrittura
Quando si scrive, non fermarsi al primo livello di spiegazione. Ogni argomento deve essere sviluppato almeno fino a un livello di dettaglio tale che il lettore possa capire:
- cos’è
- perché esiste
- come si usa
- come si implementa
- dove si sbaglia
- come si fa bene

Se il documento si ferma a “cos’è”, non è abbastanza.

### Struttura da imitare dai documenti di security
Il modello da copiare non è quello di una semplice guida, ma quello di un capitolo tecnico con una struttura forte e riconoscibile:
- apertura con scope chiaro del tema
- audience specifica e livello di apprendimento
- fonti autorevoli citate e messe in relazione con il contenuto
- una introduzione concettuale forte
- sezioni progressive che costruiscono il ragionamento
- esempi tecnici, spesso con snippet o strutture di codice
- spiegazione delle implicazioni pratiche e dei casi d’uso
- note su errori, anomalie, edge cases e troubleshooting
- chiusura con una visione di insieme e collegamenti ai temi successivi

Questa è la forma che va imitata: documenti che non raccontano solo “cosa è Fortran”, ma spiegano davvero come il linguaggio funziona, dove si applica, quali sono le sue complessità e come si lavora con esso in modo professionale.

## Struttura che si deve usare per ogni documento del dominio

Ogni documento deve seguire un formato coerente. La struttura consigliata è:

- Titolo
- Scope
- Audience
- Obiettivo
- Prerequisiti
- Introduzione
- Sezioni tecniche progressive
- Esempi pratici
- Errori comuni e troubleshooting
- Best practices
- Esercizi e approfondimenti
- Riferimenti

Questa struttura garantisce documenti più utili, più leggibili e più “professionali”.

## Template operativo di capitolo da imitare

Ogni documento principale non deve essere scritto come una semplice spiegazione lineare. Deve essere costruito come un capitolo tecnico completo, con la stessa logica di un documento specialistico serio. Il modello minimo da seguire è questo:

1. **Scope e confini del capitolo**
   - dire esattamente cosa il capitolo copre
   - dire anche cosa non copre
   - evitare ambiguità

2. **Audience e livello**
   - indicare a chi è rivolto il contenuto
   - specificare se il capitolo è pensato per principianti, intermedi o utenti avanzati

3. **Fonti autorevoli**
   - citare documentazione ufficiale, standard, manuali, riferimenti tecnici e strumenti reali
   - non scrivere come se il contenuto fosse solo opinione personale

4. **Introduzione concettuale**
   - spiegare il problema tecnico in modo chiaro
   - mostrare perché il tema è importante
   - mettere il tema nel contesto più ampio del linguaggio e del scientific computing

5. **Spiegazione tecnica progressiva**
   - partire dai concetti base
   - poi passare ai dettagli implementativi
   - poi alle implicazioni pratiche
   - poi ai casi difficili, ai limiti e agli edge cases

6. **Esempi reali di codice**
   - almeno un esempio minimale
   - almeno un esempio più realistico
   - almeno un esempio che mostri un errore comune o un caso particolare

7. **Failure modes e troubleshooting**
   - spiegare dove il codice si rompe
   - spiegare gli errori di compilazione, i problemi di precisione, gli errori logici, i problemi di memoria e gli anti-pattern

8. **Best practices e decisioni di design**
   - mostrare cosa fare e cosa evitare
   - spiegare il motivo dietro le scelte migliori

9. **Esercizi e approfondimenti**
   - aggiungere esercizi che costringano il lettore a fare qualcosa di concreto
   - non limitarsi a “leggere e capire”

10. **Conclusione e ponte al capitolo successivo**
   - chiudere il capitolo con una sintesi forte
   - collegare il tema al blocco successivo del dominio

## Regole di qualità minima per ogni documento

Un documento non è completo solo perché ha un titolo e qualche paragrafo. Per essere considerato adeguato, ogni documento principale deve soddisfare almeno questi requisiti:

- essere abbastanza lungo da essere veramente utile, non una nota di poche pagine
- avere almeno 3-5 sezioni tecniche interne ben sviluppate
- includere almeno 2-4 esempi concreti di codice
- spiegare almeno un errore comune o un caso critico
- includere una sezione sulle best practice
- includere riferimenti o collegamenti a fonti ufficiali
- essere scritto in modo tale che un lettore possa applicarlo in pratica

Se un documento è troppo corto, troppo superficiale o troppo schematico, non è sufficiente. La soglia minima è quella di un capitolo tecnico serio, non di una scheda informativa.

## Workflow di produzione consigliato

Il lavoro deve essere fatto in modo progressivo e disciplinato. La sequenza migliore è:

1. **Scrivere la struttura del capitolo prima di tutto**
   - definire scope, audience, sezioni principali e sottosezioni

2. **Sviluppare l’introduzione in modo completo**
   - spiegare il tema, il problema e il contesto tecnico

3. **Scrivere il nucleo tecnico**
   - non fermarsi ai concetti base, ma approfondire davvero i dettagli rilevanti

4. **Aggiungere esempi e casi reali**
   - almeno un esempio minimale e almeno uno più realistico

5. **Aggiungere troubleshooting e best practice**
   - questo è quello che distingue un documento serio da una semplice spiegazione

6. **Revisione finale**
   - verificare che il capitolo sia abbastanza esteso, chiaro e applicabile

## Linee guida per scrivere documenti lunghi e ben fatti

### 1. Non scrivere in modo superficiale
Ogni capitolo deve essere scritto come se fosse una guida tecnica da usare davvero in lavoro o studio. Non basta dire “Fortran supporta gli array”. Devono essere spiegati:
- come si dichiarano
- come si usano
- quali sono le peculiarità
- quali sono i vantaggi
- quali sono i casi in cui si usano bene
- quali sono gli errori comuni

### 2. Ogni documento deve avere un “nucleo pratico”
Il lettore deve sempre trovare almeno una parte concreta, ad esempio:
- un esempio di codice
- un comando di compilazione
- una mini-simulazione
- una spiegazione di un bug reale

### 3. Ogni documento deve essere orientato a chi studia
Il tono deve essere:
- chiaro
- rigoroso
- progressivo
- operativo

### 4. Le spiegazioni devono essere progressive
Non si parte mai da un concetto troppo avanzato. Il percorso deve andare da:
- base -> intermedio -> avanzato

### 5. Il dominio deve essere “riuscito” anche senza essere solo teorico
Per ogni argomento, il documento deve mostrare:
- come si scrive
- come si compila
- come si esegue
- come si testa
- come si migliora

## Struttura del dominio 16-FORTRAN

Il dominio deve essere organizzato in blocchi tematici, ognuno con almeno un documento principale e un supporto pratico.

### Fase 1 — Fondamenti e ambiente
Questa fase introduce il linguaggio e prepara lo studente a lavorare concretamente.
Contenuti previsti:
- introduzione a Fortran moderno
- storia e contesto del linguaggio
- motivazioni per usarlo oggi
- installazione e setup della toolchain
- compilatori rilevanti: gfortran, flang, lfortran, toolchain professionali
- hello world e primo programma
- variabili, tipi, operatori, controllo di flusso

### Fase 2 — Programmazione strutturata e numerica
Questa fase costruisce il cuore dell’apprendimento pratico.
Contenuti previsti:
- subroutines e functions
- program units e scope
- module e organizzazione del codice
- array, stringhe e manipolazione dati
- precisione numerica e tipi scalari
- file I/O

### Fase 3 — Programmazione avanzata e robusta
Questa fase porta il percorso a un livello più professionale.
Contenuti previsti:
- allocatable arrays e puntatori
- derived types
- object-based e object-oriented patterns
- gestione della memoria
- interoperabilità con C/C++
- integrazione con Python e librerie scientifiche

### Fase 4 — Produzione e performance
Questa fase trasforma la conoscenza in competenza reale.
Contenuti previsti:
- build systems e packaging
- fpm, make, CMake
- testing e debugging
- OpenMP e parallelismo
- benchmark e ottimizzazione
- scientific computing e librerie come BLAS/LAPACK
- progetto capstone

## Piano di contenuti minimo da realizzare

Il dominio dovrebbe contenere almeno questi blocchi:

1. Introduzione a Fortran moderno
2. Setup e ambienti di sviluppo
3. Fondamenti sintattici del linguaggio
4. Tipi numerici e precisione
5. Controllo di flusso e procedure
6. Array e stringhe
7. Moduli e organizzazione del codice
8. File I/O e gestione dati
9. Puntatori e memoria
10. Derived types e programmazione strutturata avanzata
11. Interoperabilità con C e sistemi esterni
12. Build systems e packaging
13. Performance e parallel computing
14. Testing, debugging e best practices
15. Scientific computing e librerie scientifiche
16. Progetto finale capstone

## Regole per le cartelle e la struttura dei file

La struttura del dominio deve rimanere ordinata e uniforme. La proposta migliore è:

- cartella principale: 16-FORTRAN
- file principale di guida: 00-guida-allo-studio.md
- file secondari tematici: numerati in ordine progressivo
- cartella tutorials/ per tutorial pratici
- cartella presentations/ per slide e workshop

### Regola di naming
Tutti i documenti devono avere nomi chiari e progressivi, ad esempio:
- 01-fondamenti-del-linguaggio-fortran.md
- 02-setup-compilatori-e-ambienti.md
- 03-programmazione-procedurale-e-controllo-di-flusso.md

Questa regola aiuta a mantenere il dominio ordinato e facilmente navigabile.

## Regole per creare i tutorial

I tutorial devono essere costruiti come mini-laboratori pratici, non come semplici esempi isolati. Ogni tutorial deve avere:

1. Obiettivo chiaro
2. Prerequisiti minimi
3. Esempio di codice
4. Spiegazione passo-passo
5. Comando di compilazione ed esecuzione
6. Output atteso
7. Esercizio di consolidamento
8. Estensione possibile

### Template consigliato per un tutorial

```markdown
# Tutorial X — Titolo

## Obiettivo
Cosa si vuole imparare

## Prerequisiti
Cosa serve sapere prima

## Esempio
Codice Fortran

## Come eseguirlo
Comandi di compilazione ed esecuzione

## Spiegazione
Cosa fa il programma e perché

## Esercizio
Un mini-esercizio da completare
```

### Qualità minima richiesta per un tutorial
Un tutorial va considerato buono solo se permette di:
- capire il concetto
- eseguire il codice
- modificare il codice
- ottenere un risultato concreto

## Metodo di lavoro consigliato per costruire questo dominio

Il lavoro va fatto in modo sequenziale e sistematico.

### Fase 1 — Preparazione
- raccogliere le fonti ufficiali
- definire la mappa del dominio
- stabilire l’ordine dei capitoli
- definire gli obiettivi di apprendimento

### Fase 2 — Scrittura dei documenti base
- creare i documenti principali per ogni blocco
- dare a ciascuno una struttura uniforme
- inserire esempi e best practice

### Fase 3 — Aggiunta dei tutorial
- creare tutorial per ogni area importante
- mantenere il livello pratico e progressivo
- evitare esempi troppo triviali

### Fase 4 — Aggiunta delle presentazioni e del capstone
- trasformare i concetti chiave in slide o workshop brevi
- progettare un progetto finale realistico

### Fase 5 — Revisione e arricchimento
- verificare che ogni documento risponda a “cosa”, “perché”, “come”, “quando”, “quali errori”
- aggiungere riferimenti e approfondimenti
- migliorare la densità del contenuto

## Livello di profondità richiesto

Il dominio deve essere più ricco di un semplice corso introduttivo. Deve essere pensato come:
- una guida tecnica professionale
- una raccolta di riferimento utile per studio e lavoro
- un percorso che prepari a leggere documentazione reale e costruire software serio

Per questo motivo ogni documento deve includere almeno:
- spiegazione concettuale
- implementazione concreta
- casi d’uso
- best practice
- errori comuni
- esercizi pratici

## Piano di produzione consigliato

### Obiettivo finale
Costruire un dominio con:
- 15-20 documenti tecnici completi
- 10-15 tutorial pratici
- 3-5 presentazioni o workshop
- 1 progetto finale capstone
- un livello di dettaglio elevato, simile a una guida specialistica reale

### Priorità di sviluppo
1. Fondamenti del linguaggio
2. Setup e compilazione
3. Programmazione procedurale
4. Array, tipi numerici e stringhe
5. Moduli e organizzazione del codice
6. File I/O e gestione dati
7. Memoria, puntatori e allocazione
8. Derived types e programmazione avanzata
9. Interoperabilità e librerie
10. Performance, parallelismo e packaging
11. Testing, debugging e capstone

## Checklist finale di qualità

Prima di considerare il dominio completo, ogni blocco deve avere:
- una spiegazione chiara del tema
- almeno un esempio pratico
- almeno un esercizio
- un riferimento ufficiale o esterno
- un focus su errori comuni e best practice
- un collegamento logico con il resto del percorso

## Conclusione

Il dominio 16-FORTRAN deve essere costruito con metodo, profondità e coerenza. Non basta creare brevi note. Il valore reale del dominio sta nel far diventare Fortran un linguaggio comprensibile, usabile e applicabile in contesti reali di calcolo scientifico, sviluppo numerico e alta performance.

Il lavoro migliore è quello di procedere in modo progressivo: documenti tecnici ben scritti, tutorial pratici, esempi reali, esercizi, progetti e riferimento ufficiale. Questo è il modo più corretto per trasformare il dominio in una risorsa seria e duratura.
