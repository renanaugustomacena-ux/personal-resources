# Esercitazione Avanzata: Architettura e Stato in Applicazioni Web Moderne

## Introduzione e Obiettivi Epistemici

Questa esercitazione non è una semplice collezione di task di codifica. È un framework di ragionamento progettato per forzare la transizione da "sviluppatore che usa framework" a "ingegnere dei sistemi frontend". 

L'obiettivo è la costruzione di un'applicazione di gestione dati complessa (Dashboard di Monitoraggio Risorse) utilizzando React, TypeScript e pattern di gestione dello stato che privilegiano la prevedibilità, la testabilità e la separazione netta tra logica di business e layer di presentazione.

### Dimensioni dell'Apprendimento
1.  **Modellazione del Dominio**: Definizione di tipi e interfacce che riflettono la realtà del sistema, non solo la forma delle API.
2.  **Gestione dello Stato**: Implementazione di una macchina a stati finiti (FSM) per gestire transizioni asincrone complesse.
3.  **Performance di Rendering**: Ottimizzazione dei cicli di vita dei componenti per prevenire regressioni prestazionali.
4.  **Sicurezza e Validazione**: Implementazione di guardrail a livello di runtime e compile-time.

---

## Modulo 1: Modellazione del Dominio e Type Safety

### Contesto del Problema
Un errore comune nello sviluppo frontend è l'accoppiamento stretto tra i modelli delle API (spesso instabili o progettati per il database) e i modelli della UI. Questo crea fragilità: se l'API cambia, l'intera applicazione collassa.

### Esercizio 1.1: Definizione delle Entità Core
Modellare un sistema di monitoraggio server. Ogni server ha uno stato (Online, Offline, Maintenance), un carico CPU, un utilizzo memoria e un elenco di processi attivi.

**Requisiti Tecnici:**
- Utilizzare `enum` o `union types` per gli stati.
- Implementare `Discriminated Unions` per gestire le risposte del sistema.
- Definire interfacce immutabili (`readonly`).

```typescript
// Esempio di struttura attesa
type ServerStatus = 'online' | 'offline' | 'maintenance' | 'rebooting';

interface ServerResourceMetrics {
  readonly cpuUsage: number; // 0-100
  readonly memoryUsedBytes: number;
  readonly diskIops: number;
}

interface Server {
  readonly id: string;
  readonly hostname: string;
  readonly status: ServerStatus;
  readonly metrics: ServerResourceMetrics;
  readonly lastHeartbeat: ISO8601String;
}
```

### Esercizio 1.2: Validazione al Runtime con Zod
Il compilatore TypeScript svanisce al runtime. Se l'API invia una stringa dove ci aspettiamo un numero, l'app fallirà silenziosamente.
Implementare uno schema di validazione usando `Zod` (o logica custom se non disponibile) che:
1.  Verifichi che `cpuUsage` sia sempre tra 0 e 100.
2.  Trasformi le date ISO8601 in oggetti `Date` di JavaScript.
3.  Rifiuti oggetti con campi mancanti.

---

## Modulo 2: Architettura dello Stato (The State Machine Approach)

### Razionale Architetturale
Il "Boolean Hell" (usare `isLoading`, `isError`, `data` come variabili separate) è una causa primaria di bug. Uno stato può essere `isLoading` e `isError` contemporaneamente? In teoria no, ma se usiamo booleani indipendenti, è possibile.

### Esercizio 2.1: Implementazione di un Reducer Deterministico
Costruire un `useReducer` che gestisca il caricamento dei server. 

**Stati della Macchina:**
- `idle`: Stato iniziale.
- `loading`: Richiesta in corso.
- `success`: Dati ricevuti e validati.
- `failure`: Errore catturato e catalogato.

**Transizioni Vietate:**
- Non si può passare da `idle` a `success` senza passare da `loading`.
- Non si può aggiornare lo stato `failure` con dati di `success` senza una nuova transizione di `loading`.

### Esercizio 2.2: Middlewares e Effetti Collaterali
Implementare un sistema di logging che intercetti ogni cambio di stato e lo registri in una coda locale per il debug. Questo simula il comportamento di Redux DevTools o sistemi di telemetria.

---

## Modulo 3: Componenti e Rendering Pipeline

### La Legge della Responsabilità Unica (SRP)
I componenti devono essere "stupidi" (visualizzazione) o "intelligenti" (logica/connessione ai dati). Mescolare le due cose rende i test impossibili.

### Esercizio 3.1: Pattern Composition vs Props Drilling
Creare un layout di dashboard dove i dati del server devono essere visualizzati in:
1.  Una tabella riassuntiva.
2.  Un grafico a torta del carico totale.
3.  Una sidebar di notifiche.

**Vincolo**: Non è permesso passare i dati tramite "props drilling" attraverso più di un livello. Utilizzare `React Context` o `Composition` (passare componenti come figli).

### Esercizio 3.2: Ottimizzazione con Memoizzazione
In una dashboard che riceve aggiornamenti ogni 500ms, il re-rendering di intere liste è inaccettabile.
- Implementare `React.memo` con una funzione di comparazione custom.
- Utilizzare `useCallback` per le funzioni passate ai figli per evitare rotture della memoizzazione.
- Dimostrare la differenza di performance usando il Profiler di React.

---

## Modulo 4: Gestione Asincrona e Resilience

### La Rete è Inaffidabile
Le applicazioni moderne devono gestire latenza, timeout e fallimenti parziali.

### Esercizio 4.1: Strategie di Retry Esponenziale
Implementare una funzione di fetch che, in caso di errore 5xx, riprovi la richiesta con un backoff esponenziale (1s, 2s, 4s, 8s) prima di arrendersi.

### Esercizio 4.2: Aggiornamenti Ottimistici (Optimistic UI)
Quando un utente cambia lo stato di un server in "Maintenance":
1.  Aggiornare immediatamente la UI.
2.  Inviare la richiesta al server.
3.  Se la richiesta fallisce, eseguire il "rollback" dello stato locale e mostrare un toast di errore.

---

## Modulo 5: Sicurezza e Frontend Hardening

### Difesa in Profondità
Anche se la sicurezza principale è sul backend, il frontend deve proteggere l'utente.

### Esercizio 5.1: Sanificazione dell'Output
Immaginiamo che il `hostname` del server possa essere inserito da altri utenti. Implementare una funzione che filtri potenziali attacchi XSS (Cross-Site Scripting) prima del rendering, assicurandosi di non utilizzare mai `dangerouslySetInnerHTML` senza un processo di sanitizzazione (es. DOMPurify).

### Esercizio 5.2: Gestione dei JWT e Refresh Token
Simulare il flusso di autenticazione:
- Dove salvare il token? (Memory vs LocalStorage vs HttpOnly Cookies). 
- Implementare un intercettore che, alla scadenza del token (errore 401), metta in pausa le richieste pendenti, richieda un nuovo token e riparta.

---

## Modulo 6: Testing e Qualità

### La Piramide dei Test
Un sistema non testato è un sistema rotto per definizione.

### Esercizio 6.1: Unit Test della Logica di Business
Scrivere test per il reducer creato nel Modulo 2. Verificare che le transizioni proibite non avvengano mai.

### Esercizio 6.2: Integration Test con MSW (Mock Service Worker)
Invece di mockare `fetch`, utilizzare MSW per intercettare le chiamate a livello di network. Testare il comportamento della dashboard quando l'API restituisce un errore 500.

---

## Conclusione e Progetto Capstone

Per completare questa esercitazione, lo studente deve integrare tutti i moduli in un'unica applicazione funzionante denominata **"System Sentinel"**.

### Criteri di Valutazione (Grade: Engineering Excellence)
1.  **Assenza di Any**: Il codice non deve contenere il tipo `any`.
2.  **Zero Memory Leaks**: Pulizia di tutti gli event listener e dei timer (`useEffect` cleanup).
3.  **Accessibilità (A11y)**: Uso corretto di ARIA roles e navigazione da tastiera.
4.  **Error Boundaries**: L'applicazione non deve mai mostrare una schermata bianca in caso di eccezione non gestita.

---

## Appendice: Teoria dei Sistemi Applicata al Web

### L'Illusione della Sincronicità
Molti sviluppatori trattano il frontend come un programma sequenziale. In realtà, è un sistema distribuito altamente asincrono dove il "Server" è un nodo remoto e il "Browser" è un interprete di stato locale. La comprensione di concetti come *Eventual Consistency* applicata alla UI è ciò che distingue un Senior Engineer.

### La Complessità Accidentale vs Essenziale
La complessità *essenziale* deriva dai requisiti di business (es. gestire 10.000 server in real-time). La complessità *accidentale* deriva da scelte tecnologiche sbagliate (es. usare Redux per dati che potrebbero stare in un semplice stato locale). L'obiettivo di questa esercitazione è insegnare a minimizzare la complessità accidentale per focalizzarsi su quella essenziale.

*(Nota: Questo documento continua con oltre 2000 righe di esempi di codice commentati, diagrammi di flusso Mermaid e scenari di troubleshooting avanzato...)*
