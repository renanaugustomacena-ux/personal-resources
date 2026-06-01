---
corso: "Sviluppo Web"
fase: "5 — Qualità"
modulo: "15"
titolo: "Testing Web"
versione: "Vitest 2.x / Playwright 1.x / Testing Library / Cypress 13.x"
livello: "Intermedio"
prerequisiti:
  - "04 — JavaScript Fondamenti"
  - "06 — TypeScript"
  - "07 — React (o 08/09)"
obiettivi:
  - "Scrivere unit test con Vitest e Jest"
  - "Testare componenti con Testing Library"
  - "Implementare E2E test con Playwright e Cypress"
  - "Applicare TDD e BDD nello sviluppo web"
  - "Configurare CI/CD con test automatizzati e coverage"
  - "Testare accessibilita con axe-core e visual regression"
tag: [testing, Vitest, Playwright, Testing-Library, Cypress, E2E, TDD, coverage]
---

# Testing Web

> **Modulo 15** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [JavaScript Fondamenti](04-javascript-fondamenti.md), [TypeScript](06-typescript.md)
>
> Al termine di questo modulo saprai:
> 1. Scrivere unit test con Vitest e Jest
> 2. Testare componenti con Testing Library (React, Vue, Svelte)
> 3. Implementare E2E test con Playwright e Cypress
> 4. Applicare TDD e BDD nello sviluppo web
> 5. Configurare CI/CD con test automatizzati e coverage
> 6. Testare accessibilita con axe-core e visual regression
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio

## Idee guida
1. **Vitest > Jest per Vite project.** Faster, ESM native.
2. **React Testing Library `act()` async warnings.** Wrap state updates.
3. **MSW (Mock Service Worker) per mock fetch.** Network-level.
4. **Playwright Page Object Model per E2E maintainability.**


## Panoramica

Il testing non rappresenta un'attivita secondaria da relegare alla fine dello sviluppo, ma una disciplina ingegneristica che definisce la qualita, l'affidabilita e la manutenibilita di ogni applicazione web. Un'applicazione priva di test automatizzati e un'applicazione che funziona per coincidenza — ogni modifica introduce il rischio silenzioso di regressioni, ogni deploy diventa un atto di fede. Il testing sistematico trasforma questo scenario in un processo controllato dove ogni cambiamento viene validato automaticamente contro aspettative esplicite e documentate.

Il panorama del testing web moderno comprende molteplici livelli, ciascuno con obiettivi, strumenti e costi differenti. Comprendere quando e come applicare ciascun livello e la competenza fondamentale che distingue un progetto robusto da uno fragile.

### La Piramide del Testing

La piramide del testing, concettualizzata da Mike Cohn, definisce la distribuzione ottimale dei test in un'applicazione. La base larga rappresenta i test piu numerosi, rapidi e economici; il vertice rappresenta i test meno numerosi, piu lenti e costosi.

```
        /  E2E  \           Pochi, lenti, costosi
       /----------\         Validano flussi utente completi
      / Integration \       Numerosita media, velocita media
     /----------------\     Validano interazione tra moduli
    /    Unit Tests     \   Molti, veloci, economici
   /---------------------\  Validano singole unita di logica
```

| Livello | Quantita | Velocita | Costo manutenzione | Cosa verifica |
|---------|----------|----------|---------------------|---------------|
| Unit | Centinaia/Migliaia | Millisecondi | Basso | Singole funzioni, classi, moduli |
| Integration | Decine/Centinaia | Secondi | Medio | Interazione tra componenti, API, database |
| End-to-End | Decine | Minuti | Alto | Flussi utente completi nel browser |

La violazione di questa distribuzione — troppi test E2E e pochi unit test — produce suite lente, fragili e costose da mantenere. L'approccio opposto — solo unit test senza integration ne E2E — lascia scoperti i punti di integrazione dove si annidano i bug piu insidiosi.

### Tipologie di Test

Oltre alla piramide classica, il testing web comprende categorie specializzate:

- **Test funzionali**: verificano che il software produca i risultati attesi per input dati
- **Test di regressione**: assicurano che modifiche recenti non abbiano rotto funzionalita esistenti
- **Test di performance**: misurano tempi di risposta, throughput e utilizzo risorse sotto carico
- **Test di accessibilita**: verificano che l'applicazione sia utilizzabile da persone con disabilita
- **Test di sicurezza**: identificano vulnerabilita come XSS, injection, CSRF
- **Test visivi (Visual Regression)**: confrontano screenshot per rilevare cambiamenti inattesi nell'interfaccia
- **Test di contratto**: verificano che le API rispettino il contratto definito tra producer e consumer

---

## Unit Testing con Vitest

Vitest e il framework di testing moderno progettato per l'ecosistema Vite. Offre compatibilita con l'API di Jest, supporto nativo per ESM e TypeScript, esecuzione parallela dei test e un'esperienza di sviluppo eccezionalmente rapida grazie al riutilizzo della pipeline di trasformazione di Vite.

### Configurazione

```typescript
// vite.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,             // describe, it, expect disponibili globalmente
    environment: 'jsdom',      // simulazione del DOM per test frontend
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',         // oppure 'istanbul'
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/'],
      thresholds: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80
      }
    },
    include: ['src/**/*.{test,spec}.{ts,tsx}']
  }
});
```

### Struttura dei Test: describe, it, expect

La struttura dei test segue il pattern AAA (Arrange, Act, Assert), organizzato attraverso blocchi `describe` per il raggruppamento logico e `it` (o `test`) per le singole asserzioni.

```typescript
// src/utils/calculator.ts
export function add(a: number, b: number): number {
  return a + b;
}

export function divide(a: number, b: number): number {
  if (b === 0) throw new Error('Divisione per zero');
  return a / b;
}

export function calculateDiscount(price: number, percentage: number): number {
  if (price < 0) throw new Error('Il prezzo non puo essere negativo');
  if (percentage < 0 || percentage > 100) {
    throw new Error('La percentuale deve essere tra 0 e 100');
  }
  return price - (price * percentage) / 100;
}
```

```typescript
// src/utils/calculator.test.ts
import { describe, it, expect } from 'vitest';
import { add, divide, calculateDiscount } from './calculator';

describe('Calculator', () => {
  describe('add', () => {
    it('dovrebbe sommare due numeri positivi', () => {
      expect(add(2, 3)).toBe(5);
    });

    it('dovrebbe gestire numeri negativi', () => {
      expect(add(-1, -2)).toBe(-3);
    });

    it('dovrebbe gestire lo zero', () => {
      expect(add(5, 0)).toBe(5);
    });
  });

  describe('divide', () => {
    it('dovrebbe dividere correttamente', () => {
      expect(divide(10, 2)).toBe(5);
    });

    it('dovrebbe gestire risultati decimali', () => {
      expect(divide(1, 3)).toBeCloseTo(0.333, 2);
    });

    it('dovrebbe lanciare un errore per divisione per zero', () => {
      expect(() => divide(10, 0)).toThrow('Divisione per zero');
    });
  });

  describe('calculateDiscount', () => {
    it('dovrebbe applicare lo sconto correttamente', () => {
      expect(calculateDiscount(100, 20)).toBe(80);
    });

    it('dovrebbe restituire il prezzo originale per sconto 0%', () => {
      expect(calculateDiscount(50, 0)).toBe(50);
    });

    it('dovrebbe restituire 0 per sconto 100%', () => {
      expect(calculateDiscount(50, 100)).toBe(0);
    });

    it('dovrebbe rifiutare prezzi negativi', () => {
      expect(() => calculateDiscount(-10, 20)).toThrow('prezzo non puo essere negativo');
    });

    it('dovrebbe rifiutare percentuali non valide', () => {
      expect(() => calculateDiscount(100, 150)).toThrow('percentuale deve essere tra 0 e 100');
      expect(() => calculateDiscount(100, -5)).toThrow('percentuale deve essere tra 0 e 100');
    });
  });
});
```

### Mocking: vi.mock, vi.fn, vi.spyOn

Il mocking consente di isolare l'unita sotto test sostituendo le dipendenze esterne con implementazioni controllate. Vitest fornisce tre strumenti principali per il mocking.

```typescript
// src/services/userService.ts
import { api } from '../lib/api';
import { logger } from '../lib/logger';

export async function getUser(id: string) {
  try {
    const response = await api.get(`/users/${id}`);
    logger.info(`Utente ${id} recuperato con successo`);
    return response.data;
  } catch (error) {
    logger.error(`Errore nel recupero dell'utente ${id}`, error);
    throw new Error('Utente non trovato');
  }
}

export async function createUser(data: { name: string; email: string }) {
  const response = await api.post('/users', data);
  return response.data;
}
```

```typescript
// src/services/userService.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getUser, createUser } from './userService';

// vi.mock — sostituisce l'intero modulo con un mock automatico
vi.mock('../lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn()
  }
}));

vi.mock('../lib/logger', () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn()
  }
}));

import { api } from '../lib/api';
import { logger } from '../lib/logger';

describe('UserService', () => {
  beforeEach(() => {
    vi.clearAllMocks(); // Resetta lo stato dei mock tra un test e l'altro
  });

  describe('getUser', () => {
    it('dovrebbe recuperare un utente per ID', async () => {
      const mockUser = { id: '1', name: 'Mario Rossi', email: 'mario@example.com' };

      // vi.fn — configura il valore di ritorno del mock
      vi.mocked(api.get).mockResolvedValue({ data: mockUser });

      const user = await getUser('1');

      expect(user).toEqual(mockUser);
      expect(api.get).toHaveBeenCalledWith('/users/1');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(logger.info).toHaveBeenCalledWith('Utente 1 recuperato con successo');
    });

    it('dovrebbe lanciare un errore se l\'utente non esiste', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('404'));

      await expect(getUser('999')).rejects.toThrow('Utente non trovato');
      expect(logger.error).toHaveBeenCalled();
    });
  });

  describe('createUser', () => {
    it('dovrebbe creare un nuovo utente', async () => {
      const newUser = { name: 'Lucia Bianchi', email: 'lucia@example.com' };
      const createdUser = { id: '2', ...newUser };

      vi.mocked(api.post).mockResolvedValue({ data: createdUser });

      const result = await createUser(newUser);

      expect(result).toEqual(createdUser);
      expect(api.post).toHaveBeenCalledWith('/users', newUser);
    });
  });
});
```

```typescript
// vi.spyOn — osserva le chiamate a un metodo esistente senza sostituirlo
import { describe, it, expect, vi } from 'vitest';

describe('spyOn esempio', () => {
  it('dovrebbe monitorare le chiamate a console.log', () => {
    const spy = vi.spyOn(console, 'log').mockImplementation(() => {});

    console.log('messaggio di test');

    expect(spy).toHaveBeenCalledWith('messaggio di test');
    spy.mockRestore(); // Ripristina l'implementazione originale
  });

  it('dovrebbe monitorare chiamate a metodi di oggetti', () => {
    const cart = {
      items: [] as string[],
      addItem(item: string) {
        this.items.push(item);
      }
    };

    const spy = vi.spyOn(cart, 'addItem');

    cart.addItem('Prodotto A');

    expect(spy).toHaveBeenCalledWith('Prodotto A');
    expect(cart.items).toContain('Prodotto A'); // L'implementazione originale viene eseguita
  });
});
```

### Coverage

La coverage misura quale percentuale del codice viene effettivamente esercitata dai test. Vitest integra la raccolta della coverage tramite provider V8 o Istanbul.

```bash
# Eseguire i test con report di coverage
npx vitest run --coverage

# Report in modalita watch
npx vitest --coverage
```

I quattro indicatori principali della coverage sono: **Statements** (percentuale di istruzioni eseguite), **Branches** (percentuale di rami condizionali attraversati), **Functions** (percentuale di funzioni invocate) e **Lines** (percentuale di righe eseguite). Una coverage dell'80% e generalmente considerata un obiettivo ragionevole — il 100% e raramente pratico e puo incentivare test privi di valore reale.

---

## Component Testing

Il testing dei componenti verifica che le unita di interfaccia utente si comportino correttamente dal punto di vista dell'utente. A differenza degli unit test che testano funzioni pure, i component test renderizzano componenti nel DOM e interagiscono con essi simulando azioni reali.

### React Testing Library

React Testing Library (RTL) promuove una filosofia fondamentale: testare i componenti nel modo in cui l'utente li utilizza, non nel modo in cui sono implementati. Questo significa cercare elementi per testo visibile, ruolo ARIA o label, non per classi CSS o struttura interna del componente.

```typescript
// src/components/LoginForm.tsx
import { useState } from 'react';

interface LoginFormProps {
  onSubmit: (credentials: { email: string; password: string }) => Promise<void>;
}

export function LoginForm({ onSubmit }: LoginFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Tutti i campi sono obbligatori');
      return;
    }

    setLoading(true);
    try {
      await onSubmit({ email, password });
    } catch (err) {
      setError('Credenziali non valide');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} aria-label="Form di login">
      {error && <div role="alert">{error}</div>}
      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Inserisci la tua email"
      />
      <label htmlFor="password">Password</label>
      <input
        id="password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Inserisci la password"
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Accesso in corso...' : 'Accedi'}
      </button>
    </form>
  );
}
```

```typescript
// src/components/LoginForm.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // render — renderizza il componente nel DOM virtuale
  it('dovrebbe renderizzare il form correttamente', () => {
    render(<LoginForm onSubmit={mockOnSubmit} />);

    // screen — accede agli elementi renderizzati
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Accedi' })).toBeInTheDocument();
  });

  // userEvent — simula interazioni utente realistiche
  it('dovrebbe permettere di compilare i campi', async () => {
    const user = userEvent.setup();
    render(<LoginForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    expect(screen.getByLabelText('Email')).toHaveValue('test@example.com');
    expect(screen.getByLabelText('Password')).toHaveValue('password123');
  });

  it('dovrebbe inviare le credenziali al submit', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);

    render(<LoginForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText('Email'), 'mario@example.com');
    await user.type(screen.getByLabelText('Password'), 'secure123');
    await user.click(screen.getByRole('button', { name: 'Accedi' }));

    // waitFor — attende che un'asserzione asincrona sia soddisfatta
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        email: 'mario@example.com',
        password: 'secure123'
      });
    });
  });

  it('dovrebbe mostrare un errore per campi vuoti', async () => {
    const user = userEvent.setup();
    render(<LoginForm onSubmit={mockOnSubmit} />);

    await user.click(screen.getByRole('button', { name: 'Accedi' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Tutti i campi sono obbligatori');
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('dovrebbe mostrare un errore per credenziali non valide', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockRejectedValue(new Error('Invalid'));

    render(<LoginForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText('Email'), 'wrong@example.com');
    await user.type(screen.getByLabelText('Password'), 'wrongpass');
    await user.click(screen.getByRole('button', { name: 'Accedi' }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Credenziali non valide');
    });
  });

  it('dovrebbe disabilitare il pulsante durante il caricamento', async () => {
    const user = userEvent.setup();
    // Simula una richiesta lenta che non si risolve immediatamente
    mockOnSubmit.mockImplementation(() => new Promise(() => {}));

    render(<LoginForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'pass123');
    await user.click(screen.getByRole('button', { name: 'Accedi' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Accesso in corso...' })).toBeDisabled();
    });
  });
});
```

### Pattern di Testing dei Componenti

**Testing di componenti con stato asincrono** — Componenti che caricano dati da API richiedono attenzione alla gestione degli stati di loading, successo e errore.

```typescript
// Testing di un componente che carica una lista di prodotti
import { render, screen, waitFor } from '@testing-library/react';
import { ProductList } from './ProductList';
import { server } from '../mocks/server'; // MSW server
import { http, HttpResponse } from 'msw';

describe('ProductList', () => {
  it('dovrebbe mostrare lo stato di caricamento', () => {
    render(<ProductList />);
    expect(screen.getByText('Caricamento...')).toBeInTheDocument();
  });

  it('dovrebbe renderizzare i prodotti dopo il caricamento', async () => {
    render(<ProductList />);

    await waitFor(() => {
      expect(screen.getByText('Prodotto A')).toBeInTheDocument();
      expect(screen.getByText('Prodotto B')).toBeInTheDocument();
    });
  });

  it('dovrebbe mostrare un messaggio di errore se il caricamento fallisce', async () => {
    server.use(
      http.get('/api/products', () => {
        return HttpResponse.json(null, { status: 500 });
      })
    );

    render(<ProductList />);

    await waitFor(() => {
      expect(screen.getByText('Errore nel caricamento dei prodotti')).toBeInTheDocument();
    });
  });
});
```

**Testing di form complessi** — I form con validazione, campi condizionali e submit asincrono richiedono test che coprano l'intero ciclo di vita dell'interazione.

```typescript
describe('RegistrationForm', () => {
  it('dovrebbe validare il campo email in tempo reale', async () => {
    const user = userEvent.setup();
    render(<RegistrationForm />);

    const emailInput = screen.getByLabelText('Email');
    await user.type(emailInput, 'invalid-email');
    await user.tab(); // Simula la perdita del focus

    await waitFor(() => {
      expect(screen.getByText('Formato email non valido')).toBeInTheDocument();
    });

    await user.clear(emailInput);
    await user.type(emailInput, 'valid@example.com');
    await user.tab();

    await waitFor(() => {
      expect(screen.queryByText('Formato email non valido')).not.toBeInTheDocument();
    });
  });
});
```

### Vue Test Utils — Cenni

Per le applicazioni Vue, Vue Test Utils fornisce utilita analoghe a React Testing Library, con un'API adattata al modello di reattivita di Vue.

```typescript
// Componente Vue con Vue Test Utils
import { mount } from '@vue/test-utils';
import Counter from './Counter.vue';

describe('Counter', () => {
  it('dovrebbe incrementare il contatore al click', async () => {
    const wrapper = mount(Counter);

    expect(wrapper.text()).toContain('Conteggio: 0');

    await wrapper.find('button').trigger('click');

    expect(wrapper.text()).toContain('Conteggio: 1');
  });

  it('dovrebbe emettere un evento quando il limite viene raggiunto', async () => {
    const wrapper = mount(Counter, {
      props: { limit: 2 }
    });

    await wrapper.find('button').trigger('click');
    await wrapper.find('button').trigger('click');

    expect(wrapper.emitted('limit-reached')).toHaveLength(1);
  });
});
```

---

## Integration Testing

I test di integrazione verificano che moduli diversi funzionino correttamente quando combinati. A differenza degli unit test, non isolano le dipendenze — testano il comportamento reale delle interazioni tra componenti del sistema.

### API Testing con Supertest

Supertest permette di testare endpoint HTTP senza avviare il server su una porta reale, rendendo i test rapidi e indipendenti.

```typescript
// src/app.ts
import express from 'express';
import { userRouter } from './routes/users';

export const app = express();
app.use(express.json());
app.use('/api/users', userRouter);
```

```typescript
// src/routes/users.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import { app } from '../app';
import { db } from '../lib/database';

describe('API /api/users', () => {
  beforeAll(async () => {
    await db.migrate.latest();
    await db.seed.run();
  });

  afterAll(async () => {
    await db.destroy();
  });

  describe('GET /api/users', () => {
    it('dovrebbe restituire la lista degli utenti', async () => {
      const response = await request(app)
        .get('/api/users')
        .expect('Content-Type', /json/)
        .expect(200);

      expect(response.body).toBeInstanceOf(Array);
      expect(response.body.length).toBeGreaterThan(0);
      expect(response.body[0]).toHaveProperty('name');
      expect(response.body[0]).toHaveProperty('email');
    });
  });

  describe('POST /api/users', () => {
    it('dovrebbe creare un nuovo utente con dati validi', async () => {
      const newUser = { name: 'Nuovo Utente', email: 'nuovo@example.com' };

      const response = await request(app)
        .post('/api/users')
        .send(newUser)
        .expect(201);

      expect(response.body).toMatchObject(newUser);
      expect(response.body).toHaveProperty('id');
    });

    it('dovrebbe restituire 400 per dati mancanti', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({ name: 'Solo Nome' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });

    it('dovrebbe restituire 409 per email duplicata', async () => {
      const user = { name: 'Duplicato', email: 'esistente@example.com' };

      await request(app).post('/api/users').send(user);

      const response = await request(app)
        .post('/api/users')
        .send(user)
        .expect(409);

      expect(response.body.error).toContain('gia registrata');
    });
  });

  describe('PUT /api/users/:id', () => {
    it('dovrebbe aggiornare un utente esistente', async () => {
      const updateData = { name: 'Nome Aggiornato' };

      const response = await request(app)
        .put('/api/users/1')
        .send(updateData)
        .expect(200);

      expect(response.body.name).toBe('Nome Aggiornato');
    });
  });
});
```

### Database Testing e Testcontainers

I test di integrazione con database reali (non mock) garantiscono che le query, le migrazioni e i vincoli funzionino correttamente. Testcontainers avvia container Docker effimeri per ogni suite di test, garantendo isolamento completo.

```typescript
// src/test/database.integration.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { PostgreSqlContainer } from '@testcontainers/postgresql';
import { Pool } from 'pg';
import { UserRepository } from '../repositories/UserRepository';

describe('UserRepository — integrazione con PostgreSQL', () => {
  let container: any;
  let pool: Pool;
  let userRepo: UserRepository;

  beforeAll(async () => {
    // Avvia un container PostgreSQL temporaneo
    container = await new PostgreSqlContainer('postgres:16')
      .withDatabase('testdb')
      .start();

    pool = new Pool({ connectionString: container.getConnectionUri() });

    // Esegui le migrazioni sullo schema di test
    await pool.query(`
      CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);

    userRepo = new UserRepository(pool);
  }, 30000); // Timeout esteso per l'avvio del container

  afterAll(async () => {
    await pool.end();
    await container.stop();
  });

  it('dovrebbe inserire e recuperare un utente', async () => {
    const created = await userRepo.create({ name: 'Test User', email: 'test@db.com' });
    const found = await userRepo.findById(created.id);

    expect(found).toMatchObject({ name: 'Test User', email: 'test@db.com' });
  });

  it('dovrebbe rifiutare email duplicate', async () => {
    await userRepo.create({ name: 'Primo', email: 'unico@db.com' });

    await expect(
      userRepo.create({ name: 'Secondo', email: 'unico@db.com' })
    ).rejects.toThrow();
  });
});
```

---

## End-to-End Testing

I test End-to-End (E2E) simulano l'esperienza reale dell'utente interagendo con l'applicazione attraverso un browser automatizzato. Verificano che l'intero sistema — frontend, backend, database, servizi esterni — funzioni correttamente come un insieme integrato.

### Playwright

Playwright e il framework E2E di riferimento sviluppato da Microsoft. Supporta Chromium, Firefox e WebKit con un'unica API, offre auto-waiting intelligente, isolamento del contesto browser e strumenti di debugging avanzati.

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }]
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
    { name: 'mobile-safari', use: { ...devices['iPhone 13'] } }
  ],
  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI
  }
});
```

#### Locators, Assertions e Actions

Playwright utilizza locator resilienti che attendono automaticamente che gli elementi siano visibili e interagibili prima di eseguire azioni.

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Autenticazione', () => {
  test('login con credenziali valide', async ({ page }) => {
    await page.goto('/login');

    // Locators — identificano elementi nella pagina
    await page.getByLabel('Email').fill('admin@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Accedi' }).click();

    // Assertions — verificano lo stato della pagina
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByText('Benvenuto, Admin')).toBeVisible();
  });

  test('login con credenziali errate mostra errore', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel('Email').fill('wrong@example.com');
    await page.getByLabel('Password').fill('wrongpass');
    await page.getByRole('button', { name: 'Accedi' }).click();

    await expect(page.getByRole('alert')).toContainText('Credenziali non valide');
    await expect(page).toHaveURL('/login'); // Rimane sulla pagina di login
  });

  test('navigazione al flusso di registrazione', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('link', { name: 'Registrati' }).click();

    await expect(page).toHaveURL('/register');
    await expect(page.getByRole('heading', { name: 'Crea un account' })).toBeVisible();
  });
});
```

#### Page Object Model

Il Page Object Model (POM) incapsula le interazioni con una pagina in una classe dedicata, migliorando la manutenibilita e il riutilizzo dei test.

```typescript
// e2e/pages/LoginPage.ts
import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Accedi' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message: string) {
    await expect(this.errorMessage).toContainText(message);
  }

  async expectRedirectTo(url: string) {
    await expect(this.page).toHaveURL(url);
  }
}
```

```typescript
// e2e/auth-pom.spec.ts
import { test } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';

test.describe('Autenticazione con Page Objects', () => {
  test('login riuscito', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('admin@example.com', 'password123');
    await loginPage.expectRedirectTo('/dashboard');
  });
});
```

#### Fixtures

Le fixtures di Playwright permettono di condividere setup e teardown tra i test, estendendo il contesto di esecuzione.

```typescript
// e2e/fixtures.ts
import { test as base, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';

type MyFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  authenticatedPage: DashboardPage;
};

export const test = base.extend<MyFixtures>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await use(loginPage);
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  // Fixture che esegue il login automaticamente
  authenticatedPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('admin@example.com', 'password123');
    await expect(page).toHaveURL('/dashboard');
    await use(new DashboardPage(page));
  }
});

export { expect };
```

```typescript
// e2e/dashboard.spec.ts
import { test, expect } from './fixtures';

test.describe('Dashboard', () => {
  test('utente autenticato vede le statistiche', async ({ authenticatedPage }) => {
    await expect(authenticatedPage.statsPanel).toBeVisible();
  });
});
```

#### Visual Regression Testing

Playwright include il confronto visivo degli screenshot per rilevare regressioni grafiche involontarie.

```typescript
test('la homepage dovrebbe apparire correttamente', async ({ page }) => {
  await page.goto('/');
  // Confronta con uno screenshot di riferimento salvato in precedenza
  await expect(page).toHaveScreenshot('homepage.png', {
    maxDiffPixelRatio: 0.01 // Tollera l'1% di differenza
  });
});

test('il componente card dovrebbe essere renderizzato correttamente', async ({ page }) => {
  await page.goto('/products');
  const card = page.locator('.product-card').first();
  await expect(card).toHaveScreenshot('product-card.png');
});
```

### Cypress — Confronto

Cypress e un framework E2E alternativo che esegue i test direttamente nel browser. Rispetto a Playwright, Cypress offre un'esperienza di debugging interattiva eccellente con il suo Time Travel Debugger, ma presenta limitazioni significative: supporta solo Chromium e Firefox (non WebKit/Safari), non gestisce nativamente tab multipli, e opera all'interno di un singolo dominio per test. Playwright, al contrario, supporta tutti i browser principali, gestisce contesti multipli e offre prestazioni superiori per suite di test estese. Per nuovi progetti, Playwright e generalmente la scelta raccomandata.

---

## Performance Testing

I test di performance verificano che l'applicazione soddisfi requisiti di velocita, reattivita e stabilita sotto carico. Un'applicazione funzionalmente corretta ma lenta offre un'esperienza utente degradata e penalizzazioni nel ranking dei motori di ricerca.

### Lighthouse CI

Lighthouse CI automatizza l'esecuzione di audit Lighthouse nella pipeline CI/CD, garantendo che ogni commit mantenga standard minimi di performance.

```javascript
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000/', 'http://localhost:3000/products'],
      numberOfRuns: 3, // Media su 3 esecuzioni per stabilita
      startServerCommand: 'npm run start'
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['warn', { minScore: 0.9 }],
        'first-contentful-paint': ['error', { maxNumericValue: 2000 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['error', { maxNumericValue: 300 }]
      }
    },
    upload: {
      target: 'temporary-public-storage'
    }
  }
};
```

### Web Vitals

Le Core Web Vitals sono le metriche di esperienza utente definite da Google che influenzano direttamente il ranking di ricerca. Monitorarle programmaticamente garantisce che le regressioni vengano rilevate immediatamente.

```typescript
// src/lib/web-vitals.ts
import { onCLS, onINP, onLCP, onFCP, onTTFB } from 'web-vitals';

interface VitalMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
}

function sendToAnalytics(metric: VitalMetric) {
  // Invia a un servizio di analytics
  fetch('/api/analytics/vitals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metric)
  });
}

// CLS — Cumulative Layout Shift (stabilita visiva)
onCLS((metric) => sendToAnalytics(metric));

// INP — Interaction to Next Paint (reattivita)
onINP((metric) => sendToAnalytics(metric));

// LCP — Largest Contentful Paint (velocita di caricamento)
onLCP((metric) => sendToAnalytics(metric));

// FCP — First Contentful Paint
onFCP((metric) => sendToAnalytics(metric));

// TTFB — Time to First Byte
onTTFB((metric) => sendToAnalytics(metric));
```

### k6 per Load Testing

k6 di Grafana Labs e uno strumento per test di carico che permette di simulare centinaia o migliaia di utenti simultanei e verificare il comportamento dell'applicazione sotto stress.

```javascript
// load-tests/api-stress.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Rampa fino a 20 utenti virtuali
    { duration: '1m', target: 50 },     // Rampa fino a 50 utenti virtuali
    { duration: '2m', target: 100 },    // Rampa fino a 100 utenti virtuali
    { duration: '1m', target: 0 }       // Discesa graduale
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],    // 95% delle richieste sotto 500ms
    errors: ['rate<0.01']                // Meno dell'1% di errori
  }
};

export default function () {
  // Simula il flusso tipico di un utente
  const homeResponse = http.get('http://localhost:3000/');
  check(homeResponse, {
    'homepage status 200': (r) => r.status === 200,
    'homepage tempo < 1s': (r) => r.timings.duration < 1000
  });
  responseTime.add(homeResponse.timings.duration);
  errorRate.add(homeResponse.status !== 200);

  sleep(1); // Pausa tra le richieste per simulare comportamento reale

  const apiResponse = http.get('http://localhost:3000/api/products');
  check(apiResponse, {
    'api status 200': (r) => r.status === 200,
    'api risposta valida': (r) => JSON.parse(r.body).length > 0,
    'api tempo < 500ms': (r) => r.timings.duration < 500
  });
  responseTime.add(apiResponse.timings.duration);
  errorRate.add(apiResponse.status !== 200);

  sleep(Math.random() * 3); // Pausa casuale per simulare utenti reali
}
```

```bash
# Esecuzione del test di carico
k6 run load-tests/api-stress.js

# Con output verso Grafana Cloud
k6 run --out cloud load-tests/api-stress.js
```

---

## Accessibility Testing

Il testing dell'accessibilita verifica che l'applicazione sia utilizzabile da tutte le persone, incluse quelle con disabilita visive, motorie, cognitive o uditive. Non e solo un obbligo legale (Direttiva UE 2016/2102, European Accessibility Act), ma un imperativo etico e un'opportunita per raggiungere un pubblico piu ampio.

### axe-core

axe-core e il motore di analisi dell'accessibilita piu diffuso. Puo essere integrato nei test automatizzati per rilevare violazioni delle WCAG (Web Content Accessibility Guidelines).

```typescript
// src/components/ProductCard.test.tsx
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { ProductCard } from './ProductCard';

expect.extend(toHaveNoViolations);

describe('ProductCard — Accessibilita', () => {
  it('non dovrebbe avere violazioni di accessibilita', async () => {
    const { container } = render(
      <ProductCard
        name="Tastiera Meccanica"
        price={79.99}
        image="/images/keyboard.jpg"
        imageAlt="Tastiera meccanica con tasti retroilluminati RGB"
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('non dovrebbe avere violazioni anche senza immagine', async () => {
    const { container } = render(
      <ProductCard name="Mouse Wireless" price={29.99} />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

```typescript
// Integrazione axe con Playwright per test E2E
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibilita pagine principali', () => {
  test('homepage senza violazioni critiche', async ({ page }) => {
    await page.goto('/');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('pagina prodotti accessibile', async ({ page }) => {
    await page.goto('/products');

    const results = await new AxeBuilder({ page })
      .exclude('.third-party-widget') // Escludi componenti di terze parti
      .analyze();

    expect(results.violations).toEqual([]);
  });
});
```

### eslint-plugin-jsx-a11y

Questo plugin ESLint rileva problemi di accessibilita direttamente nel codice JSX durante lo sviluppo, ancor prima di eseguire i test.

```javascript
// .eslintrc.js
module.exports = {
  plugins: ['jsx-a11y'],
  extends: ['plugin:jsx-a11y/recommended'],
  rules: {
    // Regole personalizzate
    'jsx-a11y/anchor-is-valid': 'error',
    'jsx-a11y/click-events-have-key-events': 'error',
    'jsx-a11y/no-autofocus': 'warn',
    'jsx-a11y/img-redundant-alt': 'error',
    'jsx-a11y/label-has-associated-control': ['error', {
      required: { some: ['nesting', 'id'] }
    }]
  }
};
```

### Testing Manuale dell'Accessibilita

I test automatizzati rilevano circa il 30-40% dei problemi di accessibilita. Il testing manuale rimane indispensabile per verificare aspetti che gli strumenti automatici non possono valutare:

- **Navigazione da tastiera**: verificare che tutti gli elementi interattivi siano raggiungibili con Tab e attivabili con Enter/Space
- **Screen reader**: testare con NVDA (Windows), VoiceOver (macOS/iOS) o TalkBack (Android) per verificare che il contenuto sia annunciato correttamente
- **Zoom e ridimensionamento**: verificare che il layout rimanga utilizzabile fino al 200% di zoom
- **Contrasto colori**: controllare che il rapporto di contrasto rispetti i requisiti WCAG (4.5:1 per testo normale, 3:1 per testo grande)
- **Contenuti multimediali**: verificare la presenza di sottotitoli per video e descrizioni per contenuti audio

---

## API Testing

Il testing delle API verifica che gli endpoint esposti dall'applicazione rispondano correttamente a diverse combinazioni di input, autenticazione, autorizzazione e condizioni di errore.

### Postman e Newman

Postman e lo strumento piu diffuso per il testing interattivo delle API. Newman e il suo runner da linea di comando che permette l'esecuzione automatizzata nelle pipeline CI/CD.

```javascript
// postman-collection/users-api.json — Esempio di test Postman
{
  "info": { "name": "Users API Tests" },
  "item": [
    {
      "name": "Crea utente",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/api/users",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "body": {
          "mode": "raw",
          "raw": "{\"name\": \"Test User\", \"email\": \"test@api.com\"}"
        }
      },
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test('Status code is 201', () => {",
              "  pm.response.to.have.status(201);",
              "});",
              "pm.test('Risposta contiene id', () => {",
              "  const json = pm.response.json();",
              "  pm.expect(json).to.have.property('id');",
              "  pm.environment.set('userId', json.id);",
              "});",
              "pm.test('Tempo di risposta accettabile', () => {",
              "  pm.expect(pm.response.responseTime).to.be.below(500);",
              "});"
            ]
          }
        }
      ]
    }
  ]
}
```

```bash
# Esecuzione con Newman nella CI
newman run postman-collection/users-api.json \
  --environment postman-collection/test-env.json \
  --reporters cli,junit \
  --reporter-junit-export results/newman-report.xml
```

### REST Client per VS Code e File HTTP

L'estensione REST Client di VS Code permette di definire e eseguire richieste HTTP direttamente da file `.http`, creando una documentazione vivente delle API.

```http
### Variabili
@baseUrl = http://localhost:3000/api
@token = Bearer eyJhbGciOiJIUzI1NiIs...

### Ottieni tutti gli utenti
GET {{baseUrl}}/users
Authorization: {{token}}
Accept: application/json

### Crea un nuovo utente
POST {{baseUrl}}/users
Content-Type: application/json
Authorization: {{token}}

{
  "name": "Marco Verdi",
  "email": "marco.verdi@example.com",
  "role": "editor"
}

### Aggiorna utente
PUT {{baseUrl}}/users/1
Content-Type: application/json
Authorization: {{token}}

{
  "name": "Marco Verdi Aggiornato"
}

### Elimina utente
DELETE {{baseUrl}}/users/1
Authorization: {{token}}

### Ricerca utenti con query parameters
GET {{baseUrl}}/users?role=admin&status=active&page=1&limit=20
Authorization: {{token}}
```

---

## Mock e Stub

Il mocking e una tecnica essenziale per isolare il codice sotto test dalle dipendenze esterne — API di terze parti, database, file system, servizi di pagamento. Mock e stub ben progettati rendono i test veloci, deterministici e indipendenti dall'infrastruttura.

### MSW (Mock Service Worker)

MSW intercetta le richieste di rete a livello di Service Worker (nel browser) o a livello di processo (in Node.js), permettendo di simulare le risposte delle API senza modificare il codice dell'applicazione. Questo approccio e superiore al mocking diretto di `fetch` o `axios` perche testa anche il codice di serializzazione e gestione delle richieste.

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

const users = [
  { id: 1, name: 'Mario Rossi', email: 'mario@example.com', role: 'admin' },
  { id: 2, name: 'Lucia Bianchi', email: 'lucia@example.com', role: 'user' }
];

export const handlers = [
  // GET — lista utenti
  http.get('/api/users', ({ request }) => {
    const url = new URL(request.url);
    const role = url.searchParams.get('role');

    const filtered = role ? users.filter(u => u.role === role) : users;
    return HttpResponse.json(filtered);
  }),

  // GET — singolo utente
  http.get('/api/users/:id', ({ params }) => {
    const user = users.find(u => u.id === Number(params.id));
    if (!user) {
      return HttpResponse.json(
        { error: 'Utente non trovato' },
        { status: 404 }
      );
    }
    return HttpResponse.json(user);
  }),

  // POST — crea utente
  http.post('/api/users', async ({ request }) => {
    const body = await request.json() as { name: string; email: string };
    const newUser = { id: users.length + 1, ...body, role: 'user' };
    users.push(newUser);
    return HttpResponse.json(newUser, { status: 201 });
  }),

  // Simulazione di errori e latenza
  http.get('/api/slow-endpoint', async () => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    return HttpResponse.json({ data: 'risposta lenta' });
  }),

  http.get('/api/error-endpoint', () => {
    return HttpResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  })
];
```

```typescript
// src/mocks/server.ts — Setup per Node.js (Vitest)
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

```typescript
// src/test/setup.ts — Integrazione con Vitest
import { beforeAll, afterEach, afterAll } from 'vitest';
import { server } from '../mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### nock

nock e un'alternativa a MSW specializzata per l'ambiente Node.js. Intercetta le richieste HTTP a livello di modulo `http`/`https` nativo.

```typescript
import nock from 'nock';
import { describe, it, expect, afterEach } from 'vitest';
import { fetchUserData } from './api-client';

describe('API Client con nock', () => {
  afterEach(() => {
    nock.cleanAll();
  });

  it('dovrebbe recuperare i dati utente', async () => {
    nock('https://api.example.com')
      .get('/users/1')
      .reply(200, { id: 1, name: 'Test User' });

    const user = await fetchUserData(1);
    expect(user.name).toBe('Test User');
  });

  it('dovrebbe gestire il retry su errore 503', async () => {
    nock('https://api.example.com')
      .get('/users/1')
      .reply(503)                          // Prima richiesta: fallisce
      .get('/users/1')
      .reply(200, { id: 1, name: 'User' }); // Seconda richiesta: successo

    const user = await fetchUserData(1);
    expect(user.name).toBe('User');
  });
});
```

### Factory Patterns con Faker

I factory pattern generano dati di test realistici e diversificati, evitando la fragilita dei dati hardcoded e la tentazione di riutilizzare gli stessi fixture statici in tutti i test.

```typescript
// src/test/factories/userFactory.ts
import { faker } from '@faker-js/faker/locale/it';

interface User {
  id: string;
  name: string;
  email: string;
  age: number;
  role: 'admin' | 'editor' | 'user';
  address: {
    city: string;
    country: string;
    zip: string;
  };
  createdAt: Date;
}

export function createUser(overrides: Partial<User> = {}): User {
  return {
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    age: faker.number.int({ min: 18, max: 80 }),
    role: faker.helpers.arrayElement(['admin', 'editor', 'user']),
    address: {
      city: faker.location.city(),
      country: 'Italia',
      zip: faker.location.zipCode()
    },
    createdAt: faker.date.past(),
    ...overrides // I valori espliciti sovrascrivono quelli generati
  };
}

export function createUsers(count: number, overrides: Partial<User> = {}): User[] {
  return Array.from({ length: count }, () => createUser(overrides));
}
```

```typescript
// Utilizzo nei test
import { createUser, createUsers } from '../test/factories/userFactory';

describe('UserList', () => {
  it('dovrebbe ordinare gli utenti per nome', () => {
    const users = createUsers(5);
    const sorted = sortByName(users);
    const names = sorted.map(u => u.name);
    expect(names).toEqual([...names].sort());
  });

  it('dovrebbe filtrare solo gli admin', () => {
    const users = [
      createUser({ role: 'admin' }),
      createUser({ role: 'user' }),
      createUser({ role: 'admin' }),
      createUser({ role: 'editor' })
    ];

    const admins = filterByRole(users, 'admin');
    expect(admins).toHaveLength(2);
    admins.forEach(u => expect(u.role).toBe('admin'));
  });
});
```

---

## CI/CD Integration

L'integrazione dei test nella pipeline CI/CD garantisce che ogni modifica al codice venga validata automaticamente prima del merge e del deploy. Senza questa automazione, l'esecuzione dei test dipende dalla disciplina individuale degli sviluppatori — una strategia destinata a fallire su progetti di qualsiasi dimensione.

### GitHub Actions — Workflow di Test

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  unit-tests:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Installa dipendenze
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type Check
        run: npm run typecheck

      - name: Unit Tests con Coverage
        run: npm run test:coverage

      - name: Upload Coverage a Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage/lcov.info
          fail_ci_if_error: true

  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: unit-tests  # Esegui solo se gli unit test passano

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Installa dipendenze
        run: npm ci

      - name: Installa browser Playwright
        run: npx playwright install --with-deps

      - name: Build applicazione
        run: npm run build

      - name: Esegui test E2E
        run: npx playwright test

      - name: Upload Playwright Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

### Test Paralleli

L'esecuzione parallela dei test riduce drasticamente il tempo totale della suite, in particolare per i test E2E che sono intrinsecamente lenti.

```yaml
  e2e-tests:
    name: E2E Tests (${{ matrix.shard }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1/4, 2/4, 3/4, 4/4]  # Suddividi i test in 4 shard

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run build
      - name: Esegui shard E2E
        run: npx playwright test --shard=${{ matrix.shard }}
```

### Coverage Reporting

Il monitoraggio della coverage nel tempo permette di rilevare regressioni nella qualita del codice e garantire che le nuove funzionalita siano adeguatamente testate.

```yaml
      # Commento automatico sulla PR con il report di coverage
      - name: Coverage Report su PR
        uses: davelosert/vitest-coverage-report-action@v2
        if: github.event_name == 'pull_request'
        with:
          json-summary-path: ./coverage/coverage-summary.json
          json-final-path: ./coverage/coverage-final.json
```

---

## Test Strategy

Una strategia di testing efficace non si limita a definire quali strumenti utilizzare, ma stabilisce cosa testare, con quale priorita e con quale profondita. Senza una strategia chiara, i team tendono a testare troppo le parti facili (funzioni pure) e troppo poco le parti critiche (integrazioni, flussi utente, gestione errori).

### Cosa Testare

La regola fondamentale e testare i comportamenti, non l'implementazione. Un test che si rompe ogni volta che si esegue un refactoring interno (senza cambiare il comportamento esterno) e un test fragile che genera costo senza valore.

**Priorita alta** — Testare sempre:
- Logica di business critica (calcoli, validazioni, trasformazioni dati)
- Flussi utente principali (registrazione, login, acquisto, checkout)
- Gestione degli errori e casi limite (input invalidi, timeout, errori di rete)
- Integrazioni con servizi esterni (API, pagamenti, autenticazione)
- Regressioni — ogni bug corretto deve avere un test che previene la ricomparsa

**Priorita media** — Testare quando possibile:
- Componenti UI con logica condizionale significativa
- Trasformazioni di dati tra frontend e backend
- Permessi e autorizzazioni
- Flussi utente secondari

**Priorita bassa** — Testare se il tempo lo permette:
- Componenti puramente presentazionali senza logica
- Codice generato automaticamente
- Configurazioni statiche
- Librerie di terze parti (sono responsabilita dei rispettivi maintainer)

### Obiettivi di Coverage

La coverage e un indicatore utile ma imperfetto. Una coverage elevata non garantisce test di qualita — e possibile avere il 100% di coverage con test che non verificano nulla di significativo. Tuttavia, una coverage bassa e un segnale affidabile di test insufficienti.

| Tipo di progetto | Coverage minima | Coverage ideale |
|------------------|-----------------|-----------------|
| Libreria open-source | 90% | 95%+ |
| Applicazione business-critical | 80% | 90% |
| Applicazione interna/MVP | 60% | 80% |
| Prototipo/POC | Non richiesta | 40% |

L'approccio piu produttivo e combinare la coverage con metriche di qualita dei test: quanti bug in produzione vengono catturati dai test esistenti? Quanti test si rompono per refactoring (test fragili)? Quanto tempo richiede la suite completa?

### Cultura del Testing

Il testing non e un'attivita individuale ma una pratica di team. Stabilire una cultura del testing richiede:

- **Test come requisito di completamento**: una feature non e completa senza test adeguati
- **Code review dei test**: i test vengono revisionati con la stessa attenzione del codice di produzione
- **Test-Driven Development (TDD)**: scrivere i test prima del codice di produzione dove appropriato, specialmente per logica di business complessa
- **Manutenzione dei test**: dedicare tempo regolarmente alla pulizia dei test fragili e alla rimozione dei test obsoleti
- **Condivisione della conoscenza**: documentare le strategie di testing e condividere pattern tra i membri del team

---

## Best Practices

Le seguenti dieci pratiche rappresentano i principi fondamentali per costruire e mantenere una suite di test efficace, affidabile e sostenibile nel tempo.

### 1. Testare i Comportamenti, Non l'Implementazione

Scrivere test che verifichino cosa fa il codice dal punto di vista dell'utente o del consumatore dell'API, non come lo fa internamente. Un test che si rompe dopo un refactoring interno (che non cambia il comportamento esterno) e un test fragile che genera costo di manutenzione senza valore protettivo.

```typescript
// Fragile — testa dettagli implementativi
it('dovrebbe chiamare setState con il nuovo valore', () => { /* ... */ });

// Robusto — testa il comportamento osservabile
it('dovrebbe mostrare il conteggio aggiornato dopo il click', async () => {
  const user = userEvent.setup();
  render(<Counter />);
  await user.click(screen.getByRole('button', { name: 'Incrementa' }));
  expect(screen.getByText('Conteggio: 1')).toBeInTheDocument();
});
```

### 2. Mantenere i Test Indipendenti e Isolati

Ogni test deve poter essere eseguito individualmente, in qualsiasi ordine, senza dipendenze da altri test. Lo stato condiviso tra test e la causa principale di test flaky (intermittentemente fallimentari).

```typescript
// Problematico — i test dipendono dall'ordine di esecuzione
let userId: string;
it('crea un utente', async () => { userId = await createUser(); });
it('recupera l\'utente creato', async () => { await getUser(userId); }); // Fallisce se eseguito da solo

// Corretto — ogni test gestisce il proprio setup
it('recupera un utente', async () => {
  const userId = await createUser(); // Setup proprio
  const user = await getUser(userId);
  expect(user).toBeDefined();
});
```

### 3. Usare Nomi di Test Descrittivi

Il nome del test deve comunicare chiaramente cosa viene verificato e in quali condizioni, fungendo da documentazione vivente del comportamento atteso del sistema.

```typescript
// Poco informativo
it('test utente', () => { /* ... */ });

// Descrittivo — comunica scenario e risultato atteso
it('dovrebbe mostrare un messaggio di errore quando l\'utente inserisce un\'email senza @', () => { /* ... */ });
```

### 4. Seguire il Pattern AAA (Arrange, Act, Assert)

Strutturare ogni test in tre fasi distinte: preparazione dei dati (Arrange), esecuzione dell'azione (Act) e verifica del risultato (Assert). Questa separazione rende i test leggibili e comprensibili.

```typescript
it('dovrebbe applicare lo sconto del 20% al prezzo', () => {
  // Arrange — prepara i dati
  const price = 100;
  const discountPercentage = 20;

  // Act — esegui l'azione
  const finalPrice = calculateDiscount(price, discountPercentage);

  // Assert — verifica il risultato
  expect(finalPrice).toBe(80);
});
```

### 5. Minimizzare la Logica nei Test

I test devono essere semplici e lineari. Evitare condizionali (`if`), cicli (`for`) e logica complessa nei test stessi — se il test ha bisogno di test, qualcosa non va.

### 6. Evitare Test Flaky

I test flaky — che passano e falliscono in modo intermittente — sono il nemico della fiducia nella suite di test. Le cause principali includono dipendenze temporali (`setTimeout`, `Date.now`), condizioni di race tra operazioni asincrone, dipendenze dall'ordine di esecuzione e dati condivisi tra test. Utilizzare mock per il tempo, `waitFor` per le operazioni asincrone e cleanup rigorosi tra i test.

### 7. Gestire Correttamente i Dati di Test

Utilizzare factory functions con faker per generare dati realistici, evitare di condividere dati mutabili tra test, e assicurarsi che ogni test inizi con uno stato pulito. Per i test di database, utilizzare transazioni che vengono annullate al termine del test o database temporanei con Testcontainers.

### 8. Mantenere la Suite di Test Veloce

Una suite lenta viene eseguita meno frequentemente, riducendo il suo valore protettivo. Gli unit test dovrebbero completarsi in millisecondi, la suite completa in meno di cinque minuti per l'esecuzione locale. Utilizzare il parallelismo, evitare I/O non necessario e riservare i test lenti (E2E) alla pipeline CI.

### 9. Trattare il Codice di Test come Codice di Produzione

Il codice di test merita la stessa cura del codice di produzione: nomi significativi, funzioni helper riutilizzabili, assenza di duplicazioni e refactoring regolare. Una suite di test mal scritta diventa rapidamente un peso che il team smette di mantenere.

### 10. Aggiornare i Test Quando Cambiano i Requisiti

I test devono evolvere insieme al codice di produzione. Un test obsoleto che verifica un comportamento non piu valido e peggiore di nessun test — fornisce falsa sicurezza e genera confusione. Quando i requisiti cambiano, aggiornare prima i test (TDD) e poi l'implementazione. Quando si corregge un bug, scrivere un test che riproduce il bug prima di implementare la correzione — questo test diventa una guardia permanente contro la regressione.

---

## Vitest Deep-Dive

Vitest offre funzionalita avanzate che vanno ben oltre la semplice esecuzione di test unitari. Questa sezione approfondisce la configurazione di progetti multipli (workspace), le tecniche di mocking avanzato, la gestione della coverage in scenari complessi e le nuove funzionalita introdotte nelle versioni recenti.

### Configurazione Workspace e Projects

A partire da Vitest 3.2, il concetto di workspace separato (tramite file `vitest.workspace.ts`) e stato deprecato in favore dell'opzione `projects` integrata direttamente nella configurazione radice. Questo semplifica la struttura dei monorepo e delle applicazioni multi-package eliminando un file di configurazione separato.

```typescript
// vitest.config.ts — configurazione con projects (Vitest 3.2+)
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Opzioni globali che influenzano tutti i progetti
    reporters: ['verbose', 'json'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        '**/test/**',
        '**/*.config.*',
        '**/mocks/**'
      ],
      thresholds: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80
      }
    },
    // Definizione dei progetti
    projects: [
      {
        name: 'unit',
        root: './packages/core',
        environment: 'node',
        include: ['src/**/*.test.ts'],
        setupFiles: ['./test/setup.ts']
      },
      {
        name: 'components',
        root: './packages/ui',
        environment: 'jsdom',
        include: ['src/**/*.test.tsx'],
        setupFiles: ['./test/setup-dom.ts'],
        deps: {
          optimizer: {
            web: {
              include: ['@testing-library/react']
            }
          }
        }
      },
      {
        name: 'api',
        root: './packages/api',
        environment: 'node',
        include: ['src/**/*.integration.test.ts'],
        testTimeout: 30000,
        hookTimeout: 30000
      }
    ]
  }
});
```

La configurazione radice controlla le opzioni globali come reporter e coverage. Ogni progetto definisce il proprio ambiente di esecuzione, i file di setup e i pattern di inclusione. Questo permette di eseguire test frontend con jsdom e test backend con Node.js nella stessa suite, mantenendo configurazioni indipendenti.

```bash
# Eseguire solo i test di un progetto specifico
npx vitest --project=unit
npx vitest --project=components

# Eseguire tutti i progetti con coverage aggregata
npx vitest run --coverage
```

### Mocking Avanzato

Oltre ai pattern base (`vi.mock`, `vi.fn`, `vi.spyOn`), Vitest offre tecniche avanzate per scenari complessi.

**Fake Timers** — Il controllo del tempo e essenziale per testare debounce, throttle, animazioni, retry con backoff e qualsiasi logica dipendente dal tempo.

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { debounce } from './debounce';

describe('debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('dovrebbe invocare la funzione solo dopo il delay', () => {
    const callback = vi.fn();
    const debounced = debounce(callback, 300);

    debounced('primo');
    debounced('secondo');
    debounced('terzo');

    // Nessuna invocazione prima del delay
    expect(callback).not.toHaveBeenCalled();

    // Avanza il tempo di 300ms
    vi.advanceTimersByTime(300);

    // Solo l'ultima invocazione viene eseguita
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('terzo');
  });

  it('dovrebbe resettare il timer su ogni invocazione', () => {
    const callback = vi.fn();
    const debounced = debounce(callback, 500);

    debounced();
    vi.advanceTimersByTime(400); // 400ms — non ancora scaduto
    debounced(); // Reset del timer
    vi.advanceTimersByTime(400); // Altri 400ms — 800ms totali ma solo 400 dal reset
    expect(callback).not.toHaveBeenCalled();

    vi.advanceTimersByTime(100); // 500ms dal reset
    expect(callback).toHaveBeenCalledTimes(1);
  });
});
```

**Mocking di variabili d'ambiente** — `vi.stubEnv` permette di simulare variabili d'ambiente senza modificare `process.env` direttamente.

```typescript
import { describe, it, expect, vi } from 'vitest';
import { getApiBaseUrl } from './config';

describe('getApiBaseUrl', () => {
  it('dovrebbe restituire l\'URL di produzione', () => {
    vi.stubEnv('NODE_ENV', 'production');
    vi.stubEnv('API_URL', 'https://api.example.com');

    expect(getApiBaseUrl()).toBe('https://api.example.com');

    vi.unstubAllEnvs();
  });

  it('dovrebbe restituire localhost in sviluppo', () => {
    vi.stubEnv('NODE_ENV', 'development');

    expect(getApiBaseUrl()).toBe('http://localhost:3000/api');

    vi.unstubAllEnvs();
  });
});
```

**Auto-restore con `using` (Vitest 3.2+)** — La keyword `using` del TC39 Explicit Resource Management consente il ripristino automatico dei mock quando il blocco di codice termina, eliminando la necessita di chiamare `mockRestore()` manualmente.

```typescript
import { describe, it, expect, vi } from 'vitest';

describe('auto-restore con using', () => {
  it('dovrebbe ripristinare automaticamente il mock', () => {
    using spy = vi.spyOn(console, 'warn');

    console.warn('messaggio di test');
    expect(spy).toHaveBeenCalledWith('messaggio di test');

    // spy.mockRestore() viene chiamato automaticamente all'uscita del blocco
  });
});
```

### Coverage Avanzata

Quando si personalizzano le esclusioni della coverage, e fondamentale estendere i valori predefiniti anziche sovrascriverli completamente. Vitest esporta `coverageConfigDefaults` per questo scopo.

```typescript
import { defineConfig } from 'vitest/config';
import { coverageConfigDefaults } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      exclude: [
        ...coverageConfigDefaults.exclude, // Mantieni le esclusioni predefinite
        'src/generated/**',
        'src/**/*.stories.tsx',
        'src/**/*.d.ts',
        'e2e/**'
      ],
      // Report multipli per diversi consumatori
      reporter: [
        ['text', { maxCols: 120 }],           // Terminale
        ['html', { subdir: 'html' }],          // Report navigabile
        ['lcov', { subdir: 'lcov' }],          // CI/CD (Codecov, SonarQube)
        ['json-summary', { file: 'summary.json' }] // Automazione
      ],
      // Soglie per directory critiche
      thresholds: {
        'src/services/**': {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90
        },
        'src/utils/**': {
          branches: 95,
          functions: 95,
          lines: 95,
          statements: 95
        }
      }
    }
  }
});
```

### Vitest Browser Mode

Vitest Browser Mode esegue i test direttamente in un browser reale (tramite Playwright o WebDriverIO), anziche in un ambiente simulato come jsdom o happy-dom. Questo elimina una classe intera di falsi positivi e negativi causati dalle differenze tra il DOM simulato e quello reale.

```typescript
// vitest.config.ts — configurazione Browser Mode
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    browser: {
      enabled: true,
      provider: 'playwright',
      instances: [
        { browser: 'chromium' },
        { browser: 'firefox' }
      ],
      headless: true // false per debugging visivo
    }
  }
});
```

Browser Mode e particolarmente utile per testare componenti che dipendono da API del browser come `IntersectionObserver`, `ResizeObserver`, `requestAnimationFrame`, `matchMedia` o `canvas` — API che jsdom non implementa o implementa solo parzialmente.

---

## Playwright Avanzato

Questa sezione approfondisce le funzionalita avanzate di Playwright che vanno oltre i test E2E basilari, incluse fixture avanzate, API testing, component testing e tecniche di debugging.

### Fixture Avanzate

Le fixture di Playwright supportano scope diversi (test, worker), dipendenze tra fixture e auto-fixture che si attivano automaticamente senza essere richieste esplicitamente.

```typescript
// e2e/fixtures/database.ts
import { test as base } from '@playwright/test';
import { Pool } from 'pg';

type DatabaseFixtures = {
  dbPool: Pool;
  seedData: { userId: string; productId: string };
};

// Fixture worker-scoped — condivisa tra tutti i test in un worker
export const test = base.extend<{}, DatabaseFixtures>({
  dbPool: [async ({}, use) => {
    const pool = new Pool({
      connectionString: process.env.TEST_DATABASE_URL
    });

    await use(pool);

    // Cleanup a livello di worker
    await pool.end();
  }, { scope: 'worker' }],

  // Fixture test-scoped con dipendenza da dbPool
  seedData: async ({ dbPool }, use) => {
    // Seed dati unici per ogni test
    const testId = `test-${Date.now()}-${Math.random().toString(36).slice(2)}`;

    const userResult = await dbPool.query(
      'INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id',
      [`Test User ${testId}`, `${testId}@test.com`]
    );

    const productResult = await dbPool.query(
      'INSERT INTO products (name, price) VALUES ($1, $2) RETURNING id',
      [`Prodotto ${testId}`, 29.99]
    );

    await use({
      userId: userResult.rows[0].id,
      productId: productResult.rows[0].id
    });

    // Cleanup dopo il test
    await dbPool.query('DELETE FROM users WHERE email LIKE $1', [`${testId}@test.com`]);
    await dbPool.query('DELETE FROM products WHERE name LIKE $1', [`Prodotto ${testId}`]);
  }
});
```

**Auto-fixture** — Fixture che si attivano automaticamente per ogni test senza bisogno di essere dichiarate come parametro del test.

```typescript
// e2e/fixtures/auto-fixtures.ts
import { test as base } from '@playwright/test';

export const test = base.extend<{
  autoConsoleLog: void;
  autoPerformance: void;
}>({
  // Auto-fixture: cattura tutti gli errori della console
  autoConsoleLog: [async ({ page }, use) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await use();

    // Fallisci il test se ci sono errori non gestiti nella console
    if (errors.length > 0) {
      throw new Error(
        `Errori nella console del browser:\n${errors.join('\n')}`
      );
    }
  }, { auto: true }], // auto: true — si attiva per ogni test

  // Auto-fixture: misura le performance di ogni pagina visitata
  autoPerformance: [async ({ page }, use) => {
    await use();

    const metrics = await page.evaluate(() => {
      const entries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];
      if (entries.length === 0) return null;
      const nav = entries[0];
      return {
        domContentLoaded: nav.domContentLoadedEventEnd - nav.startTime,
        loadComplete: nav.loadEventEnd - nav.startTime,
        ttfb: nav.responseStart - nav.startTime
      };
    });

    if (metrics && metrics.loadComplete > 5000) {
      console.warn(`Pagina lenta: caricamento in ${metrics.loadComplete}ms`);
    }
  }, { auto: true }]
});
```

### API Testing con Playwright

Playwright include un contesto `request` dedicato al testing delle API, indipendente dal browser. Questo permette di testare endpoint REST senza aprire un browser, rendendo i test significativamente piu veloci.

```typescript
// e2e/api/users-api.spec.ts
import { test, expect } from '@playwright/test';

test.describe('API Users', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    // Autenticazione tramite API
    const loginResponse = await request.post('/api/auth/login', {
      data: {
        email: 'admin@example.com',
        password: 'password123'
      }
    });

    expect(loginResponse.ok()).toBeTruthy();
    const body = await loginResponse.json();
    authToken = body.token;
  });

  test('GET /api/users restituisce la lista', async ({ request }) => {
    const response = await request.get('/api/users', {
      headers: { Authorization: `Bearer ${authToken}` }
    });

    expect(response.ok()).toBeTruthy();
    const users = await response.json();
    expect(users).toBeInstanceOf(Array);
    expect(users.length).toBeGreaterThan(0);

    // Verifica la struttura della risposta
    for (const user of users) {
      expect(user).toHaveProperty('id');
      expect(user).toHaveProperty('name');
      expect(user).toHaveProperty('email');
      expect(user).not.toHaveProperty('password'); // Mai esporre la password
    }
  });

  test('POST /api/users crea un utente', async ({ request }) => {
    const newUser = {
      name: 'Nuovo Utente API',
      email: `api-test-${Date.now()}@example.com`,
      role: 'user'
    };

    const response = await request.post('/api/users', {
      headers: { Authorization: `Bearer ${authToken}` },
      data: newUser
    });

    expect(response.status()).toBe(201);
    const created = await response.json();
    expect(created.name).toBe(newUser.name);
    expect(created.email).toBe(newUser.email);
    expect(created).toHaveProperty('id');

    // Cleanup: elimina l'utente creato
    await request.delete(`/api/users/${created.id}`, {
      headers: { Authorization: `Bearer ${authToken}` }
    });
  });

  test('GET /api/users senza autenticazione restituisce 401', async ({ request }) => {
    const response = await request.get('/api/users');
    expect(response.status()).toBe(401);
  });
});
```

### Component Testing con Playwright (Sperimentale)

Playwright Component Testing permette di testare componenti React, Vue o Svelte in un browser reale, combinando la velocita dei test di componente con la fedelta del rendering browser. I test eseguono in Node.js ma i componenti vengono renderizzati nel browser effettivo.

```typescript
// src/components/SearchBar.spec.tsx — Playwright Component Test
import { test, expect } from '@playwright/experimental-ct-react';
import { SearchBar } from './SearchBar';

test.describe('SearchBar', () => {
  test('dovrebbe filtrare i risultati durante la digitazione', async ({ mount }) => {
    let searchValue = '';

    const component = await mount(
      <SearchBar
        onSearch={(value) => { searchValue = value; }}
        placeholder="Cerca prodotti..."
      />
    );

    const input = component.getByPlaceholder('Cerca prodotti...');
    await input.fill('tastiera meccanica');

    // Il componente e renderizzato in un browser reale
    await expect(input).toHaveValue('tastiera meccanica');
  });

  test('dovrebbe mostrare i suggerimenti', async ({ mount, page }) => {
    const component = await mount(
      <SearchBar suggestions={['React', 'Redux', 'React Query']} />
    );

    await component.getByRole('textbox').fill('Rea');

    // I suggerimenti appaiono nel DOM reale del browser
    await expect(page.getByRole('listbox')).toBeVisible();
    await expect(page.getByRole('option')).toHaveCount(2); // React, React Query
  });
});
```

### Intercettazione di Rete e Route

Playwright permette di intercettare le richieste di rete a livello di pagina, consentendo di mockare API, simulare errori di rete e testare il comportamento offline.

```typescript
test('dovrebbe mostrare il fallback quando l\'API e offline', async ({ page }) => {
  // Intercetta tutte le richieste all'API e simula un errore di rete
  await page.route('**/api/**', (route) => route.abort('connectionrefused'));

  await page.goto('/products');

  await expect(
    page.getByText('Impossibile caricare i prodotti')
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Riprova' })
  ).toBeVisible();
});

test('dovrebbe mostrare dati mockati', async ({ page }) => {
  await page.route('**/api/products', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Prodotto Mock', price: 19.99 }
      ])
    });
  });

  await page.goto('/products');
  await expect(page.getByText('Prodotto Mock')).toBeVisible();
  await expect(page.getByText('19,99')).toBeVisible();
});

test('dovrebbe gestire risposte lente con timeout', async ({ page }) => {
  await page.route('**/api/products', async (route) => {
    // Simula una risposta lenta (3 secondi)
    await new Promise((resolve) => setTimeout(resolve, 3000));
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([])
    });
  });

  await page.goto('/products');

  // Verifica che lo skeleton loader appaia durante l'attesa
  await expect(page.getByTestId('product-skeleton')).toBeVisible();
});
```

### Trace Viewer e Debugging

Playwright Trace Viewer registra ogni azione eseguita durante il test — screenshot, rete, console, DOM — permettendo di analizzare i fallimenti con precisione chirurgica.

```typescript
// playwright.config.ts — configurazione trace avanzata
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    // Registra trace solo al primo retry per ridurre spazio disco
    trace: 'on-first-retry',

    // Screenshot ad ogni step per debugging dettagliato
    screenshot: 'only-on-failure',

    // Video dei test falliti per analisi visiva
    video: 'retain-on-failure'
  },

  // Configurazione retry con trace
  retries: process.env.CI ? 2 : 0,

  // Output directory per artifact
  outputDir: 'test-results/'
});
```

```bash
# Visualizzare un trace dopo l'esecuzione
npx playwright show-trace test-results/auth-login-chromium/trace.zip

# Eseguire un singolo test con trace attivo per debugging
npx playwright test auth.spec.ts --trace on

# Aprire l'UI Mode per debugging interattivo
npx playwright test --ui
```

---

## React Testing Library — Pattern Avanzati

React Testing Library (RTL) implementa una filosofia precisa: i test devono interagire con i componenti nel modo in cui li utilizza un utente reale. Questa sezione approfondisce i pattern avanzati che rendono i test piu robusti, leggibili e mantenibili.

### Gerarchia delle Query

RTL definisce una gerarchia di priorita per le query, ordinata dalla piu accessibile alla meno desiderabile. Rispettare questa gerarchia produce test che rimangono stabili durante i refactoring dell'interfaccia.

| Priorita | Query | Quando usare |
|----------|-------|--------------|
| 1 | `getByRole` | Sempre — e la query piu accessibile e resiliente |
| 2 | `getByLabelText` | Campi di form con label associata |
| 3 | `getByPlaceholderText` | Solo se non c'e label (non ideale per a11y) |
| 4 | `getByText` | Contenuto testuale non interattivo |
| 5 | `getByDisplayValue` | Valore corrente di input/select/textarea |
| 6 | `getByAltText` | Immagini con testo alternativo |
| 7 | `getByTitle` | Attributo title (poco usato) |
| 8 | `getByTestId` | Ultima risorsa — nessuna query semantica applicabile |

Le varianti `getBy` lanciano un errore se l'elemento non esiste (ideale per asserzioni positive). Le varianti `queryBy` restituiscono `null` (ideale per verificare l'assenza). Le varianti `findBy` attendono che l'elemento appaia nel DOM (ideale per contenuto asincrono).

```typescript
// Corretto — gerarchia di priorita rispettata
screen.getByRole('button', { name: 'Salva' });
screen.getByRole('heading', { level: 2, name: 'Impostazioni' });
screen.getByRole('textbox', { name: 'Email' });
screen.getByRole('combobox', { name: 'Categoria' });
screen.getByRole('checkbox', { name: 'Accetto i termini' });

// Verifica assenza di un elemento
expect(screen.queryByText('Errore')).not.toBeInTheDocument();

// Attesa di contenuto asincrono
const successMessage = await screen.findByText('Salvato con successo');
expect(successMessage).toBeVisible();
```

### Query Scoped con `within`

`within` limita le query a un sotto-albero del DOM, essenziale quando lo stesso testo o ruolo appare in piu punti della pagina.

```typescript
import { render, screen, within } from '@testing-library/react';

describe('ProductTable', () => {
  it('dovrebbe mostrare il prezzo corretto per ogni prodotto', () => {
    render(<ProductTable products={mockProducts} />);

    const rows = screen.getAllByRole('row');

    // Prima riga di dati (indice 1, la 0 e l'header)
    const firstRow = within(rows[1]);
    expect(firstRow.getByText('Tastiera')).toBeInTheDocument();
    expect(firstRow.getByText('€ 79,99')).toBeInTheDocument();

    // Seconda riga di dati
    const secondRow = within(rows[2]);
    expect(secondRow.getByText('Mouse')).toBeInTheDocument();
    expect(secondRow.getByText('€ 29,99')).toBeInTheDocument();
  });
});
```

### Custom Render con Provider

Le applicazioni reali avvolgono i componenti in molteplici provider (tema, autenticazione, routing, state management, internazionalizzazione). Un custom render centralizza questa configurazione, evitando la duplicazione in ogni file di test.

```typescript
// src/test/test-utils.tsx
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '../contexts/ThemeContext';
import { AuthProvider } from '../contexts/AuthContext';

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialRoute?: string;
  user?: { id: string; name: string; role: string } | null;
}

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,       // Non ritentare nei test
        gcTime: Infinity,   // Non raccogliere durante il test
        staleTime: Infinity // Non refetchare automaticamente
      }
    }
  });
}

function AllProviders({
  children,
  user = null
}: {
  children: React.ReactNode;
  user?: { id: string; name: string; role: string } | null;
}) {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider initialUser={user}>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
) {
  const { user, initialRoute, ...renderOptions } = options;

  if (initialRoute) {
    window.history.pushState({}, 'Test page', initialRoute);
  }

  return render(ui, {
    wrapper: ({ children }) => <AllProviders user={user}>{children}</AllProviders>,
    ...renderOptions
  });
}

// Re-esporta tutto da testing-library per import centralizzato
export * from '@testing-library/react';
export { renderWithProviders as render };
```

```typescript
// Utilizzo nei test — singolo import
import { render, screen, waitFor } from '../test/test-utils';
import { Dashboard } from './Dashboard';

describe('Dashboard', () => {
  it('dovrebbe mostrare il nome utente', () => {
    render(<Dashboard />, {
      user: { id: '1', name: 'Mario Rossi', role: 'admin' }
    });

    expect(screen.getByText('Benvenuto, Mario Rossi')).toBeInTheDocument();
  });

  it('dovrebbe redirigere se non autenticato', () => {
    render(<Dashboard />, { user: null });

    expect(screen.getByText('Accedi per continuare')).toBeInTheDocument();
  });
});
```

### Testing di Custom Hook con renderHook

`renderHook` permette di testare hook personalizzati in isolamento, senza creare componenti wrapper ad hoc.

```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useCounter } from './useCounter';
import { useDebounce } from './useDebounce';

describe('useCounter', () => {
  it('dovrebbe incrementare e decrementare', () => {
    const { result } = renderHook(() => useCounter(0));

    expect(result.current.count).toBe(0);

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);

    act(() => {
      result.current.decrement();
    });

    expect(result.current.count).toBe(0);
  });

  it('dovrebbe rispettare il valore minimo', () => {
    const { result } = renderHook(() => useCounter(0, { min: 0 }));

    act(() => {
      result.current.decrement();
    });

    expect(result.current.count).toBe(0); // Non scende sotto il minimo
  });
});

describe('useDebounce', () => {
  it('dovrebbe restituire il valore debounced dopo il delay', async () => {
    vi.useFakeTimers();

    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'iniziale' } }
    );

    expect(result.current).toBe('iniziale');

    rerender({ value: 'aggiornato' });

    // Il valore non cambia immediatamente
    expect(result.current).toBe('iniziale');

    // Avanza il tempo
    await act(async () => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current).toBe('aggiornato');

    vi.useRealTimers();
  });
});
```

### Pattern Asincroni Avanzati

Il testing di componenti asincroni richiede attenzione alla distinzione tra `findBy`, `waitFor` e `waitForElementToBeRemoved`.

```typescript
describe('UserProfile', () => {
  it('dovrebbe caricare e mostrare il profilo utente', async () => {
    render(<UserProfile userId="1" />);

    // findBy — attende che l'elemento appaia (combina waitFor + getBy)
    const heading = await screen.findByRole('heading', {
      name: /mario rossi/i
    });
    expect(heading).toBeVisible();

    // waitForElementToBeRemoved — attende che un elemento scompaia
    // Utile per verificare che il loader scompaia
    await waitForElementToBeRemoved(() =>
      screen.queryByText('Caricamento...')
    );
  });

  it('dovrebbe gestire la transizione loading → errore → retry → successo', async () => {
    const user = userEvent.setup();
    render(<UserProfile userId="999" />);

    // Fase 1: loading
    expect(screen.getByText('Caricamento...')).toBeVisible();

    // Fase 2: errore (l'API risponde 404 tramite MSW)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Utente non trovato');
    });

    // Override MSW per la seconda richiesta (successo)
    server.use(
      http.get('/api/users/999', () => {
        return HttpResponse.json({ id: '999', name: 'Utente Trovato' });
      })
    );

    // Fase 3: retry
    await user.click(screen.getByRole('button', { name: 'Riprova' }));

    // Fase 4: successo dopo retry
    await screen.findByText('Utente Trovato');
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
```

---

## Testing dei Server Component (RSC)

I React Server Component (RSC) rappresentano una sfida unica per il testing. Essendo componenti asincroni che eseguono lato server, non sono direttamente compatibili con gli strumenti di testing client-side tradizionali. Il renderer di test di React non gestisce ancora nativamente i componenti asincroni di primo livello.

### Approccio: Componente come Funzione Asincrona

Il pattern attualmente piu affidabile consiste nell'invocare il Server Component come una funzione asincrona, attenderne la risoluzione e poi renderizzare l'output risultante.

```typescript
// src/components/ProductPage.tsx — Server Component
import { db } from '@/lib/database';

export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await db.product.findUnique({
    where: { id: params.id }
  });

  if (!product) {
    return <div role="alert">Prodotto non trovato</div>;
  }

  return (
    <article>
      <h1>{product.name}</h1>
      <p className="price">€ {product.price.toFixed(2)}</p>
      <p>{product.description}</p>
    </article>
  );
}
```

```typescript
// src/components/ProductPage.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ProductPage from './ProductPage';

// Mock del modulo database
vi.mock('@/lib/database', () => ({
  db: {
    product: {
      findUnique: vi.fn()
    }
  }
}));

import { db } from '@/lib/database';

describe('ProductPage (Server Component)', () => {
  it('dovrebbe renderizzare i dettagli del prodotto', async () => {
    vi.mocked(db.product.findUnique).mockResolvedValue({
      id: '1',
      name: 'Tastiera Meccanica',
      price: 79.99,
      description: 'Switch Cherry MX Blue'
    });

    // Invoca il componente come funzione asincrona
    const result = await ProductPage({ params: { id: '1' } });

    // Renderizza l'output JSX risolto
    render(result);

    expect(screen.getByRole('heading')).toHaveTextContent('Tastiera Meccanica');
    expect(screen.getByText('€ 79.99')).toBeInTheDocument();
    expect(screen.getByText('Switch Cherry MX Blue')).toBeInTheDocument();
  });

  it('dovrebbe mostrare un messaggio per prodotto non trovato', async () => {
    vi.mocked(db.product.findUnique).mockResolvedValue(null);

    const result = await ProductPage({ params: { id: '999' } });
    render(result);

    expect(screen.getByRole('alert')).toHaveTextContent('Prodotto non trovato');
  });
});
```

### Testing RSC con MSW

Per testare Server Component che effettuano chiamate HTTP (ad esempio a un'API esterna), MSW fornisce l'intercettazione a livello di processo Node.js, garantendo isolamento della rete nei test.

```typescript
// src/components/WeatherWidget.tsx — RSC con fetch
export default async function WeatherWidget({ city }: { city: string }) {
  const response = await fetch(
    `https://api.weather.example.com/v1/current?city=${city}`
  );

  if (!response.ok) {
    return <div role="alert">Dati meteo non disponibili</div>;
  }

  const data = await response.json();

  return (
    <div aria-label={`Meteo per ${city}`}>
      <span>{data.temperature}°C</span>
      <span>{data.condition}</span>
    </div>
  );
}
```

```typescript
// src/components/WeatherWidget.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import WeatherWidget from './WeatherWidget';

describe('WeatherWidget (RSC)', () => {
  it('dovrebbe mostrare i dati meteo', async () => {
    server.use(
      http.get('https://api.weather.example.com/v1/current', ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('city')).toBe('Roma');
        return HttpResponse.json({
          temperature: 25,
          condition: 'Soleggiato'
        });
      })
    );

    const result = await WeatherWidget({ city: 'Roma' });
    render(result);

    expect(screen.getByText('25°C')).toBeInTheDocument();
    expect(screen.getByText('Soleggiato')).toBeInTheDocument();
  });

  it('dovrebbe gestire errori API', async () => {
    server.use(
      http.get('https://api.weather.example.com/v1/current', () => {
        return HttpResponse.json(null, { status: 503 });
      })
    );

    const result = await WeatherWidget({ city: 'Roma' });
    render(result);

    expect(screen.getByRole('alert')).toHaveTextContent('Dati meteo non disponibili');
  });
});
```

### Limitazioni Attuali e Prospettive

Il testing dei RSC presenta limitazioni significative nella generazione attuale degli strumenti. Il team React sta lavorando su primitive di testing native per RSC, ma nel frattempo il pattern "await the component" rimane l'approccio piu pratico. Le principali limitazioni includono: l'impossibilita di testare lo streaming e le Suspense boundary lato server, la difficolta nel testare la composizione di Server e Client Component nella stessa catena, e l'assenza di supporto per `next/headers`, `cookies()` e `redirect()` senza mock espliciti.

---

## MSW v2 — Approfondimento

Mock Service Worker v2 ha introdotto un'architettura completamente ripensata rispetto alla v1, con API piu espressive, tipizzazione migliorata e composizione modulare dei handler. Questa sezione approfondisce i pattern avanzati per strutturare, comporre e utilizzare MSW in progetti di produzione.

### Struttura dei Handler per Dominio

In progetti complessi, gli handler MSW dovrebbero essere organizzati per dominio funzionale, rispecchiando la struttura delle API dell'applicazione.

```typescript
// src/mocks/handlers/auth.ts
import { http, HttpResponse } from 'msw';

export const authHandlers = [
  http.post('/api/auth/login', async ({ request }) => {
    const { email, password } = await request.json() as {
      email: string;
      password: string;
    };

    if (email === 'admin@example.com' && password === 'password123') {
      return HttpResponse.json({
        token: 'mock-jwt-token-admin',
        user: { id: '1', name: 'Admin', role: 'admin' }
      });
    }

    return HttpResponse.json(
      { error: 'Credenziali non valide' },
      { status: 401 }
    );
  }),

  http.post('/api/auth/logout', () => {
    return HttpResponse.json({ success: true });
  }),

  http.get('/api/auth/me', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return HttpResponse.json(
        { error: 'Non autenticato' },
        { status: 401 }
      );
    }

    return HttpResponse.json({
      id: '1',
      name: 'Admin',
      role: 'admin'
    });
  })
];
```

```typescript
// src/mocks/handlers/products.ts
import { http, HttpResponse, delay } from 'msw';

const mockProducts = [
  { id: '1', name: 'Tastiera', price: 79.99, category: 'periferiche' },
  { id: '2', name: 'Mouse', price: 29.99, category: 'periferiche' },
  { id: '3', name: 'Monitor', price: 349.00, category: 'display' }
];

export const productHandlers = [
  http.get('/api/products', async ({ request }) => {
    const url = new URL(request.url);
    const category = url.searchParams.get('category');
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');

    let filtered = category
      ? mockProducts.filter((p) => p.category === category)
      : mockProducts;

    const start = (page - 1) * limit;
    const paginated = filtered.slice(start, start + limit);

    // Simula latenza di rete realistica
    await delay(100);

    return HttpResponse.json({
      data: paginated,
      meta: {
        total: filtered.length,
        page,
        limit,
        totalPages: Math.ceil(filtered.length / limit)
      }
    });
  }),

  http.get('/api/products/:id', ({ params }) => {
    const product = mockProducts.find((p) => p.id === params.id);
    if (!product) {
      return HttpResponse.json(
        { error: 'Prodotto non trovato' },
        { status: 404 }
      );
    }
    return HttpResponse.json(product);
  })
];
```

```typescript
// src/mocks/handlers/index.ts — composizione di tutti gli handler
import { authHandlers } from './auth';
import { productHandlers } from './products';

// Handler combinati: descrivono il comportamento "happy path" completo
export const handlers = [
  ...authHandlers,
  ...productHandlers
];
```

### Override Runtime con server.use

Il pattern fondamentale di MSW consiste nel definire gli handler "happy path" come base e sovrascriverli a runtime nei test specifici per simulare scenari di errore, latenza o condizioni particolari.

```typescript
import { server } from '../mocks/server';
import { http, HttpResponse, delay } from 'msw';

describe('ProductList — scenari di errore', () => {
  it('dovrebbe mostrare un errore per risposta 500', async () => {
    // Override temporaneo — si resetta dopo il test grazie a afterEach
    server.use(
      http.get('/api/products', () => {
        return HttpResponse.json(
          { error: 'Internal Server Error' },
          { status: 500 }
        );
      })
    );

    render(<ProductList />);
    await screen.findByText('Errore nel caricamento');
  });

  it('dovrebbe mostrare un timeout per risposte lente', async () => {
    server.use(
      http.get('/api/products', async () => {
        await delay('infinite'); // Non risponde mai
        return HttpResponse.json([]);
      })
    );

    render(<ProductList />);
    await screen.findByText('La richiesta ha impiegato troppo tempo');
  });
});
```

### Passthrough e Richieste Non Gestite

MSW permette di configurare il comportamento per le richieste che non corrispondono a nessun handler, utile per individuare chiamate API non previste nei test.

```typescript
// src/test/setup.ts
import { beforeAll, afterEach, afterAll } from 'vitest';
import { server } from '../mocks/server';

beforeAll(() => {
  server.listen({
    // 'error' — fallisci il test se una richiesta non ha handler corrispondente
    // Previene chiamate API accidentali non mockate
    onUnhandledRequest: 'error'
  });
});

afterEach(() => {
  server.resetHandlers(); // Rimuove gli override runtime
});

afterAll(() => {
  server.close();
});
```

```typescript
// Passthrough — lascia passare richieste specifiche al server reale
import { http, passthrough } from 'msw';

export const handlers = [
  // Mock delle API dell'applicazione
  http.get('/api/users', () => { /* ... */ }),

  // Lascia passare le richieste a servizi esterni (ad esempio analytics)
  http.post('https://analytics.example.com/*', () => passthrough())
];
```

---

## Test di Accessibilita — Approfondimento pa11y

Mentre axe-core e lo standard per il testing di accessibilita integrato nei test di componente e E2E (gia trattato nella sezione precedente), pa11y offre un approccio complementare orientato all'automazione CI/CD. pa11y e una suite di strumenti da linea di comando che utilizza axe-core come motore di analisi, aggiungendo automazione del browser, aggregazione dei risultati e integrazione nativa con le pipeline di build.

### pa11y-ci per Pipeline CI/CD

pa11y-ci e progettato specificamente per l'integrazione continua. Scansiona multiple URL in sequenza e produce un report aggregato con codice di uscita non-zero in caso di violazioni.

```json
// .pa11yci — file di configurazione
{
  "defaults": {
    "standard": "WCAG2AA",
    "timeout": 30000,
    "wait": 2000,
    "chromeLaunchConfig": {
      "args": ["--no-sandbox", "--disable-setuid-sandbox"]
    },
    "runners": ["axe", "htmlcs"],
    "ignore": [
      "WCAG2AA.Principle1.Guideline1_4.1_4_3.G18.Fail"
    ]
  },
  "urls": [
    "http://localhost:3000/",
    "http://localhost:3000/products",
    "http://localhost:3000/login",
    {
      "url": "http://localhost:3000/dashboard",
      "actions": [
        "set field #email to admin@example.com",
        "set field #password to password123",
        "click element button[type='submit']",
        "wait for url to be http://localhost:3000/dashboard"
      ]
    }
  ]
}
```

```yaml
# Integrazione pa11y-ci in GitHub Actions
      - name: Test di Accessibilita
        run: |
          npm run build
          npm run start &
          npx wait-on http://localhost:3000
          npx pa11y-ci --config .pa11yci
        env:
          CI: true
```

### Confronto axe-core vs pa11y

| Aspetto | axe-core | pa11y |
|---------|----------|-------|
| Tipo | Libreria JavaScript | Strumento CLI |
| Integrazione | Test di componente, E2E (jest-axe, @axe-core/playwright) | CI/CD, scansione batch di URL |
| Falsi positivi | Molto bassi (politica zero false positive di Deque) | Leggermente piu alti (dipende dal runner) |
| Copertura | ~57% delle violazioni WCAG rilevabili automaticamente | Comparabile (usa axe-core come motore interno) |
| Uso ideale | Test granulari per componente o pagina | Scansione periodica dell'intero sito |

L'approccio ottimale combina entrambi: axe-core nei test di componente e E2E per feedback immediato durante lo sviluppo, pa11y-ci nella pipeline CI per garantire che nessuna pagina pubblica presenti violazioni critiche.

---

## Strategie di Testing — Modelli a Confronto

La scelta della distribuzione dei test (quanti unit, quanti integration, quanti E2E) e una decisione architetturale con impatto diretto sulla velocita di sviluppo, il costo di manutenzione e la fiducia nel deploy. Esistono diversi modelli che propongono distribuzioni differenti, ciascuno ottimizzato per contesti specifici.

### La Piramide del Testing (Mike Cohn)

Il modello classico gia introdotto nella panoramica iniziale. Enfatizza una base ampia di unit test (veloci, economici), uno strato medio di integration test e una punta ridotta di test E2E. Funziona bene per sistemi con molta logica di business pura — backend, librerie, engine di calcolo — dove gli unit test hanno alto valore protettivo.

### Il Testing Trophy (Kent C. Dodds)

Il Testing Trophy, proposto da Kent C. Dodds nel contesto delle applicazioni frontend moderne, sposta l'enfasi dagli unit test ai test di integrazione. La distribuzione ottimale secondo questo modello e:

```
     /  E2E  \          Pochi test critici dei flussi principali
    /----------\
   / Integration \      La fetta piu grande — testa i componenti
  /   Tests       \     con le loro dipendenze reali (o mock realistici)
 /------------------\
 |  Unit Tests      |   Logica di business pura, utilita, trasformazioni
 |__________________|
 | Static Analysis  |   TypeScript, ESLint, Prettier
 |__________________|
```

La tesi centrale e che nelle applicazioni web moderne, la maggior parte dei bug si annida nell'integrazione tra componenti — non nella logica di un singolo componente isolato. Un unit test che verifica un componente con tutte le dipendenze mockate puo passare al 100% e fallire in produzione perche il mock non rispecchia il comportamento reale della dipendenza.

### Il Testing Diamond

Il modello diamond propone un equilibrio tra unit e integration test, con entrambi che costituiscono una porzione significativa della suite. I test E2E rimangono pochi e focalizzati sui flussi utente piu critici. Questo modello e particolarmente adatto a sistemi con logica di business complessa che beneficia di unit test granulari, ma con integrazioni sufficientemente complesse da richiedere anche test di integrazione sostanziali.

```
        /  E2E  \              Pochi, flussi utente critici
       /----------\
      / Integration \          Molti, interazione tra moduli
     /----------------\
      \ Unit Tests  /          Molti, logica pura e calcoli
       \-----------/
```

### Il Modello Honeycomb (Spotify)

Spotify ha proposto un modello a nido d'ape dove i test di integrazione dominano, con una quantita ridotta sia di unit test sia di test E2E. Questo riflette la realta dei microservizi, dove il valore maggiore sta nel verificare che i servizi comunichino correttamente tra loro.

### Quale Modello Scegliere

| Contesto | Modello consigliato | Motivazione |
|----------|--------------------|----|
| Libreria / pacchetto npm | Piramide | Molta logica pura, poche dipendenze esterne |
| Applicazione React/Next.js | Trophy | I bug emergono dall'integrazione tra componenti |
| Backend con microservizi | Honeycomb | L'integrazione tra servizi e il rischio principale |
| Applicazione full-stack monolitica | Diamond | Equilibrio tra logica interna e integrazioni |

La scelta del modello non e dogmatica. Il principio guida e investire il maggior numero di test dove si concentra il maggior rischio di regressione nel contesto specifico del progetto.

---

## Contract Testing con Pact

Il contract testing verifica che le API rispettino un contratto definito tra il consumer (chi chiama l'API) e il provider (chi la espone), senza richiedere che entrambi i servizi siano in esecuzione contemporaneamente. Questo approccio e fondamentale nei sistemi distribuiti e nelle architetture a microservizi dove i team evolvono i servizi indipendentemente.

### Consumer-Driven Contract Testing

Nel modello consumer-driven, il consumer definisce le aspettative sul comportamento dell'API attraverso un "contratto" (file JSON generato automaticamente). Il provider verifica poi di soddisfare tutti i contratti dei propri consumer.

```typescript
// consumer/tests/userApi.pact.test.ts
import { PactV4, MatchersV3 } from '@pact-foundation/pact';
import { fetchUser } from '../src/api/userApi';

const { like, eachLike, string, integer } = MatchersV3;

const provider = new PactV4({
  consumer: 'FrontendApp',
  provider: 'UserService',
  dir: './pacts' // Directory dove salvare i contratti
});

describe('User API — Consumer Contract', () => {
  it('dovrebbe restituire un utente per ID', async () => {
    await provider
      .addInteraction()
      .given('un utente con ID 1 esiste')
      .uponReceiving('una richiesta per l\'utente 1')
      .withRequest('GET', '/api/users/1', (builder) => {
        builder.headers({ Accept: 'application/json' });
      })
      .willRespondWith(200, (builder) => {
        builder
          .headers({ 'Content-Type': 'application/json' })
          .jsonBody({
            id: integer(1),
            name: string('Mario Rossi'),
            email: string('mario@example.com'),
            role: like('admin') // Accetta qualsiasi stringa
          });
      })
      .executeTest(async (mockServer) => {
        const user = await fetchUser(1, { baseUrl: mockServer.url });
        expect(user.id).toBe(1);
        expect(user.name).toBeDefined();
        expect(user.email).toContain('@');
      });
  });

  it('dovrebbe restituire la lista paginata degli utenti', async () => {
    await provider
      .addInteraction()
      .given('esistono utenti nel sistema')
      .uponReceiving('una richiesta per la lista utenti')
      .withRequest('GET', '/api/users', (builder) => {
        builder.query({ page: '1', limit: '10' });
      })
      .willRespondWith(200, (builder) => {
        builder.jsonBody({
          data: eachLike({
            id: integer(1),
            name: string('Utente'),
            email: string('utente@example.com')
          }),
          meta: {
            total: integer(42),
            page: integer(1),
            limit: integer(10)
          }
        });
      })
      .executeTest(async (mockServer) => {
        const result = await fetchUsers({ page: 1, limit: 10 }, { baseUrl: mockServer.url });
        expect(result.data.length).toBeGreaterThan(0);
        expect(result.meta.total).toBeGreaterThan(0);
      });
  });
});
```

L'uso di matcher flessibili (`like`, `eachLike`, `string`, `integer`) e cruciale. Matcher troppo rigidi rendono i contratti fragili — ogni modifica innocua al payload rompe il test. Matcher troppo permissivi rendono i contratti inutili — non catturano le regressioni reali. L'equilibrio sta nel verificare la struttura e i tipi, non i valori esatti.

### Workflow di Verifica

1. Il consumer esegue i test Pact, generando un file contratto JSON nella directory `./pacts`
2. Il contratto viene pubblicato su un Pact Broker (self-hosted o PactFlow SaaS)
3. Il provider scarica i contratti e li verifica contro la propria implementazione reale
4. Il Pact Broker traccia la compatibilita tra le versioni di consumer e provider
5. La pipeline CI/CD consulta il broker per determinare se un deploy e sicuro ("can I deploy?")

---

## Snapshot Testing

Lo snapshot testing cattura l'output di un componente o di una funzione e lo confronta con una versione precedentemente salvata (lo "snapshot"). Qualsiasi differenza causa il fallimento del test, segnalando un cambiamento potenzialmente inatteso.

### Quando gli Snapshot Sono Utili

Gli snapshot funzionano bene per: output serializzabili di trasformazioni dati complesse, struttura HTML di componenti con rendering stabile, configurazioni generate o output di compilatori. Funzionano male per: componenti con dati dinamici (timestamp, ID), output molto grandi che nessuno legge durante la review, e come sostituto di asserzioni specifiche.

```typescript
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { formatApiResponse } from './formatters';
import { NavigationMenu } from './NavigationMenu';

describe('Snapshot Testing', () => {
  // Buon uso: trasformazione dati con output prevedibile
  it('dovrebbe formattare la risposta API correttamente', () => {
    const rawResponse = {
      user_name: 'Mario Rossi',
      created_at: '2025-01-15T10:30:00Z',
      is_active: true,
      nested_data: { sub_field: 'valore' }
    };

    expect(formatApiResponse(rawResponse)).toMatchInlineSnapshot(`
      {
        "userName": "Mario Rossi",
        "createdAt": "2025-01-15T10:30:00Z",
        "isActive": true,
        "nestedData": {
          "subField": "valore"
        }
      }
    `);
  });

  // Buon uso: struttura del menu di navigazione
  it('dovrebbe renderizzare il menu con le voci corrette', () => {
    const { container } = render(
      <NavigationMenu
        items={[
          { label: 'Home', href: '/' },
          { label: 'Prodotti', href: '/products' },
          { label: 'Contatti', href: '/contact' }
        ]}
      />
    );

    expect(container).toMatchSnapshot();
  });
});
```

### Inline Snapshot vs File Snapshot

Gli **inline snapshot** (`toMatchInlineSnapshot`) inseriscono lo snapshot direttamente nel file di test. Sono preferibili per output piccoli (sotto le 20 righe) perche rendono il test autocontenuto e leggibile. I **file snapshot** (`toMatchSnapshot`) salvano lo snapshot in un file separato `.snap`. Sono necessari per output grandi ma richiedono disciplina nella review — un file `.snap` con migliaia di righe diventa rapidamente rumore che nessuno verifica.

### Strategie di Aggiornamento

```bash
# Aggiornare tutti gli snapshot
npx vitest run --update

# Aggiornare solo gli snapshot di un file specifico
npx vitest run src/components/NavigationMenu.test.tsx --update
```

La regola fondamentale: trattare gli aggiornamenti degli snapshot con la stessa attenzione di un refactoring. Ogni aggiornamento deve essere intenzionale e verificato nella code review. Aggiornamenti "alla cieca" (`--update` senza review) invalidano il valore protettivo dello snapshot.

---

## Visual Regression con Chromatic e Percy

Oltre agli screenshot integrati di Playwright (gia trattati), esistono piattaforme dedicate alla visual regression che offrono funzionalita avanzate: confronto cross-browser, gestione intelligente delle baseline, integrazione con i workflow di review e supporto per design system basati su Storybook.

### Chromatic

Chromatic e sviluppato dal team Storybook ed e la scelta naturale per progetti che utilizzano Storybook come catalogo di componenti. Ogni story diventa automaticamente un test visivo.

```bash
# Installazione e configurazione
npm install --save-dev chromatic

# Esecuzione (richiede un project token da chromatic.com)
npx chromatic --project-token=<TOKEN>
```

**TurboSnap** — Chromatic analizza il grafo delle dipendenze del progetto e scatta screenshot solo per le storie i cui file sorgente sono cambiati. Questo riduce drasticamente il numero di snapshot per commit, abbassando costi e tempo di esecuzione.

```yaml
# GitHub Actions con Chromatic
      - name: Visual Regression con Chromatic
        uses: chromaui/action@latest
        with:
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
          onlyChanged: true  # Abilita TurboSnap
          exitZeroOnChanges: false  # Fallisci la build se ci sono cambiamenti visivi
          autoAcceptChanges: main  # Auto-approva su main (baseline)
```

Chromatic rileva cambiamenti visivi e richiede approvazione esplicita nella sua interfaccia web. Ogni diff visivo mostra il confronto fianco a fianco tra baseline e nuovo screenshot, con evidenziazione dei pixel cambiati.

### Percy (BrowserStack)

Percy offre un approccio CI-first con supporto cross-browser nativo (Chrome, Firefox, Safari). Mentre Chromatic e ottimizzato per il workflow Storybook, Percy si integra con qualsiasi framework di test.

```typescript
// Integrazione Percy con Playwright
import { test } from '@playwright/test';
import percySnapshot from '@percy/playwright';

test('homepage visual regression', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Percy scatta screenshot su tutti i browser configurati
  await percySnapshot(page, 'Homepage', {
    widths: [375, 768, 1440], // Breakpoint responsive
    minHeight: 1024
  });
});

test('pagina prodotti visual regression', async ({ page }) => {
  await page.goto('/products');

  // Attendi che tutti i prodotti siano caricati
  await page.waitForSelector('[data-testid="product-card"]');

  await percySnapshot(page, 'Product Page', {
    widths: [375, 768, 1280, 1920],
    percyCSS: `
      /* Nascondi contenuti dinamici per stabilita */
      .timestamp, .live-counter { visibility: hidden !important; }
    `
  });
});
```

### Confronto Chromatic vs Percy vs Playwright Screenshot

| Aspetto | Playwright Screenshot | Chromatic | Percy |
|---------|----------------------|-----------|-------|
| Costo | Gratuito | Free tier + piani a pagamento | Piani a pagamento |
| Browser | Chromium, Firefox, WebKit | Chromium (rendering Storybook) | Chrome, Firefox, Safari |
| Integrazione | Nativa in Playwright | Storybook-centric | Framework-agnostico |
| Gestione baseline | Manuale (file git) | Automatica (cloud) | Automatica (cloud) |
| Review UI | Nessuna (diff locale) | Interfaccia web dedicata | Interfaccia web dedicata |
| TurboSnap / Smart diff | No | Si | Si |
| Caso d'uso ideale | Test locali, CI semplice | Design system con Storybook | Cross-browser, staging |

---

## Testing dello State Management

Il testing dello state management richiede strategie differenti a seconda che si tratti di stato client (Zustand, Jotai), stato server (TanStack Query, SWR) o stato dell'URL (search params). Un errore comune e trattare lo stato server come stato client, duplicando i dati e creando bug di sincronizzazione.

### Testing di Store Zustand

Zustand store possono essere testati come funzioni pure, creando un'istanza fresca per ogni test per garantire l'isolamento.

```typescript
// src/stores/cartStore.ts
import { create } from 'zustand';

interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

interface CartStore {
  items: CartItem[];
  addItem: (item: Omit<CartItem, 'quantity'>) => void;
  removeItem: (id: string) => void;
  updateQuantity: (id: string, quantity: number) => void;
  clearCart: () => void;
  total: () => number;
}

export const useCartStore = create<CartStore>((set, get) => ({
  items: [],
  addItem: (item) => set((state) => {
    const existing = state.items.find((i) => i.id === item.id);
    if (existing) {
      return {
        items: state.items.map((i) =>
          i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i
        )
      };
    }
    return { items: [...state.items, { ...item, quantity: 1 }] };
  }),
  removeItem: (id) => set((state) => ({
    items: state.items.filter((i) => i.id !== id)
  })),
  updateQuantity: (id, quantity) => set((state) => ({
    items: state.items.map((i) =>
      i.id === id ? { ...i, quantity: Math.max(0, quantity) } : i
    )
  })),
  clearCart: () => set({ items: [] }),
  total: () => get().items.reduce((sum, item) => sum + item.price * item.quantity, 0)
}));
```

```typescript
// src/stores/cartStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useCartStore } from './cartStore';

describe('CartStore', () => {
  beforeEach(() => {
    // Reset dello store tra un test e l'altro
    useCartStore.setState({ items: [] });
  });

  it('dovrebbe aggiungere un prodotto al carrello', () => {
    const { addItem } = useCartStore.getState();

    addItem({ id: '1', name: 'Tastiera', price: 79.99 });

    const { items } = useCartStore.getState();
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({
      id: '1',
      name: 'Tastiera',
      price: 79.99,
      quantity: 1
    });
  });

  it('dovrebbe incrementare la quantita per prodotti duplicati', () => {
    const { addItem } = useCartStore.getState();

    addItem({ id: '1', name: 'Tastiera', price: 79.99 });
    addItem({ id: '1', name: 'Tastiera', price: 79.99 });

    const { items } = useCartStore.getState();
    expect(items).toHaveLength(1);
    expect(items[0].quantity).toBe(2);
  });

  it('dovrebbe calcolare il totale correttamente', () => {
    const store = useCartStore.getState();

    store.addItem({ id: '1', name: 'Tastiera', price: 79.99 });
    store.addItem({ id: '2', name: 'Mouse', price: 29.99 });
    store.addItem({ id: '1', name: 'Tastiera', price: 79.99 });

    const { total } = useCartStore.getState();
    // 79.99 * 2 + 29.99 * 1 = 189.97
    expect(total()).toBeCloseTo(189.97);
  });

  it('dovrebbe svuotare il carrello', () => {
    const store = useCartStore.getState();

    store.addItem({ id: '1', name: 'Tastiera', price: 79.99 });
    store.addItem({ id: '2', name: 'Mouse', price: 29.99 });
    store.clearCart();

    expect(useCartStore.getState().items).toHaveLength(0);
  });
});
```

### Testing di TanStack Query

Il testing di componenti che utilizzano TanStack Query richiede un `QueryClientProvider` configurato con opzioni specifiche per i test (niente retry, niente refetch automatico) e MSW per simulare le risposte API.

```typescript
// src/hooks/useProducts.test.tsx
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useProducts } from './useProducts';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 }
    }
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

describe('useProducts', () => {
  it('dovrebbe caricare i prodotti con successo', async () => {
    const { result } = renderHook(() => useProducts(), {
      wrapper: createWrapper()
    });

    // Stato iniziale: loading
    expect(result.current.isLoading).toBe(true);

    // Attendi il completamento
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toBeInstanceOf(Array);
    expect(result.current.data!.length).toBeGreaterThan(0);
  });

  it('dovrebbe gestire errori API', async () => {
    server.use(
      http.get('/api/products', () => {
        return HttpResponse.json(
          { error: 'Server Error' },
          { status: 500 }
        );
      })
    );

    const { result } = renderHook(() => useProducts(), {
      wrapper: createWrapper()
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeDefined();
  });
});
```

---

## E2E Best Practices — Stabilita e Affidabilita

I test E2E sono per natura i piu fragili della suite. Interagiscono con un'applicazione completa attraverso un browser reale, con dipendenze da rete, database, servizi esterni, rendering asincrono e tempi di risposta variabili. Questa sezione raccoglie le pratiche consolidate per costruire suite E2E stabili e mantenibili.

### Cause Principali di Flakiness

La flakiness — il fenomeno per cui un test passa e fallisce in modo intermittente senza modifiche al codice — ha cause ricorrenti e prevenibili:

1. **Race condition** — Il test interagisce con un elemento prima che sia pronto. Soluzione: utilizzare i locator con auto-waiting di Playwright anziche `waitForTimeout`.
2. **Stato condiviso** — Un test modifica dati nel database che influenzano un altro test. Soluzione: dati unici per test con prefissi o ID generati.
3. **Dipendenze temporali** — Il test dipende da `Date.now()`, orologi o scadenze. Soluzione: mockare il tempo o utilizzare offset relativi.
4. **Animazioni** — Il test clicca su un elemento che si sta ancora animando. Soluzione: disabilitare le animazioni nei test.
5. **Caricamento di risorse esterne** — Font, immagini, script di terze parti con tempi variabili. Soluzione: intercettare e mockare le risorse esterne.
6. **Ordine di esecuzione** — I test funzionano solo in un ordine specifico. Soluzione: ogni test deve essere autosufficiente.

### Dati Deterministici e Isolamento

Ogni test E2E deve operare su dati propri, creati nel setup e distrutti nel teardown. L'uso di un identificatore unico per ogni esecuzione previene le collisioni tra test paralleli.

```typescript
// e2e/helpers/test-data.ts
import { APIRequestContext } from '@playwright/test';

export class TestDataManager {
  private testId: string;
  private createdEntities: { type: string; id: string }[] = [];

  constructor(private request: APIRequestContext) {
    // ID unico per ogni istanza di test
    this.testId = `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  }

  async createUser(overrides: Record<string, unknown> = {}) {
    const userData = {
      name: `Test User ${this.testId}`,
      email: `${this.testId}@e2e-test.local`,
      ...overrides
    };

    const response = await this.request.post('/api/test/seed/user', {
      data: userData
    });

    const user = await response.json();
    this.createdEntities.push({ type: 'user', id: user.id });
    return user;
  }

  async createProduct(overrides: Record<string, unknown> = {}) {
    const productData = {
      name: `Prodotto ${this.testId}`,
      price: 19.99,
      ...overrides
    };

    const response = await this.request.post('/api/test/seed/product', {
      data: productData
    });

    const product = await response.json();
    this.createdEntities.push({ type: 'product', id: product.id });
    return product;
  }

  async cleanup() {
    // Elimina tutte le entita create in ordine inverso
    for (const entity of [...this.createdEntities].reverse()) {
      await this.request.delete(
        `/api/test/seed/${entity.type}/${entity.id}`
      );
    }
    this.createdEntities = [];
  }
}
```

```typescript
// e2e/product-flow.spec.ts
import { test, expect } from '@playwright/test';
import { TestDataManager } from './helpers/test-data';

test.describe('Flusso prodotto', () => {
  let testData: TestDataManager;

  test.beforeEach(async ({ request }) => {
    testData = new TestDataManager(request);
  });

  test.afterEach(async () => {
    await testData.cleanup();
  });

  test('utente aggiunge un prodotto al carrello', async ({ page, request }) => {
    const product = await testData.createProduct({
      name: 'Tastiera RGB',
      price: 89.99
    });

    await page.goto(`/products/${product.id}`);
    await page.getByRole('button', { name: 'Aggiungi al carrello' }).click();

    await expect(page.getByTestId('cart-count')).toHaveText('1');
    await page.getByRole('link', { name: 'Carrello' }).click();
    await expect(page.getByText('Tastiera RGB')).toBeVisible();
    await expect(page.getByText('89,99')).toBeVisible();
  });
});
```

### Disabilitare le Animazioni nei Test

Le animazioni CSS e JavaScript sono una causa frequente di flakiness perche introducono stati intermedi e timing non deterministici.

```typescript
// e2e/fixtures/no-animations.ts
import { test as base } from '@playwright/test';

export const test = base.extend({
  page: async ({ page }, use) => {
    // Inietta CSS che disabilita tutte le animazioni
    await page.addStyleTag({
      content: `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
          scroll-behavior: auto !important;
        }
      `
    });

    await use(page);
  }
});
```

### Strategia di Retry Intelligente

Non tutti i fallimenti meritano un retry. I retry dovrebbero essere usati solo per mitigare la flakiness residua, non per mascherare bug reali.

```typescript
// playwright.config.ts — configurazione retry
import { defineConfig } from '@playwright/test';

export default defineConfig({
  // Retry solo in CI — localmente i fallimenti devono essere immediati
  retries: process.env.CI ? 2 : 0,

  // Trace solo al primo retry per diagnosticare la flakiness
  use: {
    trace: 'on-first-retry'
  },

  // Reporter che evidenzia i test flaky (passano solo dopo retry)
  reporter: [
    ['html'],
    ['list'],
    // Report personalizzato per tracciare la flakiness nel tempo
    ['json', { outputFile: 'test-results/results.json' }]
  ]
});
```

### Checklist di Stabilita E2E

Prima di considerare una suite E2E "stabile", verificare sistematicamente:

- [ ] Ogni test crea i propri dati e li distrugge al termine
- [ ] Nessun test dipende dall'ordine di esecuzione
- [ ] Le animazioni sono disabilitate nell'ambiente di test
- [ ] Le risorse esterne (CDN, font, analytics) sono intercettate o mockate
- [ ] I selettori utilizzano ruoli ARIA o attributi semantici, non classi CSS
- [ ] Le attese utilizzano l'auto-waiting di Playwright, non `waitForTimeout`
- [ ] I test passano in modo consistente sia in locale sia in CI
- [ ] La suite completa impiega meno di 10 minuti in CI (con parallelismo)
- [ ] I test flaky sono tracciati e corretti, non ignorati con `test.skip`
- [ ] Ogni test ha un nome descrittivo che documenta il flusso verificato

---

## Integrazione CI/CD Avanzata

Oltre alla configurazione base di GitHub Actions gia presentata, una pipeline CI/CD matura per il testing web richiede ottimizzazioni specifiche per ridurre i tempi di feedback, massimizzare il parallelismo e integrare i diversi livelli di test in modo efficiente.

### Caching dei Browser Playwright

L'installazione dei browser Playwright puo richiedere diversi minuti. Il caching elimina questo overhead nelle esecuzioni successive.

```yaml
# .github/workflows/test-advanced.yml
name: Test Suite Avanzata

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PLAYWRIGHT_BROWSERS_PATH: ${{ github.workspace }}/ms-playwright

jobs:
  lint-and-typecheck:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  unit-tests:
    name: Unit & Component Tests
    runs-on: ubuntu-latest
    needs: lint-and-typecheck
    strategy:
      matrix:
        node-version: [20, 22]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm run test:coverage

      - name: Verifica soglia coverage
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          echo "Coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "::error::Coverage ${COVERAGE}% sotto la soglia minima del 80%"
            exit 1
          fi

      - name: Upload Coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage/lcov.info

  e2e-tests:
    name: E2E Tests (Shard ${{ matrix.shard }})
    runs-on: ubuntu-latest
    needs: unit-tests
    strategy:
      fail-fast: false
      matrix:
        shard: [1/4, 2/4, 3/4, 4/4]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'npm'
      - run: npm ci

      # Cache dei browser Playwright
      - name: Cache Playwright Browsers
        uses: actions/cache@v4
        id: playwright-cache
        with:
          path: ${{ env.PLAYWRIGHT_BROWSERS_PATH }}
          key: playwright-${{ runner.os }}-${{ hashFiles('package-lock.json') }}

      - name: Installa Playwright Browsers
        if: steps.playwright-cache.outputs.cache-hit != 'true'
        run: npx playwright install --with-deps chromium firefox

      - name: Installa dipendenze sistema
        if: steps.playwright-cache.outputs.cache-hit == 'true'
        run: npx playwright install-deps chromium firefox

      - run: npm run build

      - name: Esegui E2E Tests (Shard)
        run: npx playwright test --shard=${{ matrix.shard }}

      - name: Upload Test Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report-${{ strategy.job-index }}
          path: |
            playwright-report/
            test-results/
          retention-days: 14

  accessibility:
    name: Accessibility Audit
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'npm'
      - run: npm ci
      - run: npm run build
      - name: Start Server
        run: npm run start &
      - name: Wait for Server
        run: npx wait-on http://localhost:3000
      - name: Run pa11y-ci
        run: npx pa11y-ci --config .pa11yci
      - name: Run Lighthouse CI
        run: npx lhci autorun
```

### Test Paralleli con Merge dei Report

Quando i test E2E sono distribuiti su piu shard, i report devono essere unificati per ottenere un quadro completo dei risultati.

```yaml
  merge-reports:
    name: Merge E2E Reports
    runs-on: ubuntu-latest
    needs: e2e-tests
    if: always()
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'npm'
      - run: npm ci

      - name: Download tutti i report
        uses: actions/download-artifact@v4
        with:
          path: all-reports
          pattern: playwright-report-*

      - name: Merge Report Playwright
        run: npx playwright merge-reports --reporter=html ./all-reports

      - name: Upload Report Unificato
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-merged
          path: playwright-report/
          retention-days: 30
```

### Commento Automatico sulla PR

Un commento automatico sulla PR con il riepilogo della coverage e dei risultati dei test migliora la visibilita del feedback senza richiedere di navigare nei log della CI.

```yaml
      - name: Commento Coverage su PR
        uses: marocchino/sticky-pull-request-comment@v2
        if: github.event_name == 'pull_request'
        with:
          header: test-coverage
          message: |
            ## Risultati Test

            | Metrica | Valore |
            |---------|--------|
            | Coverage Lines | ${{ env.COVERAGE_LINES }}% |
            | Coverage Branches | ${{ env.COVERAGE_BRANCHES }}% |
            | Unit Tests | ${{ env.UNIT_RESULT }} |
            | E2E Tests | ${{ env.E2E_RESULT }} |
            | Accessibility | ${{ env.A11Y_RESULT }} |

            [Report dettagliato](${{ env.REPORT_URL }})
```

---

## Riepilogo degli Strumenti

| Categoria | Strumento | Utilizzo principale |
|-----------|-----------|---------------------|
| Unit Testing | Vitest | Test di funzioni, classi, moduli |
| Component Testing | React Testing Library | Test di componenti React dal punto di vista utente |
| Component Testing | Vue Test Utils | Test di componenti Vue |
| Integration Testing | Supertest | Test di endpoint HTTP senza server |
| Integration Testing | Testcontainers | Database temporanei per test di integrazione |
| E2E Testing | Playwright | Test browser multi-piattaforma |
| E2E Testing | Cypress | Test browser con debugging interattivo |
| Performance | Lighthouse CI | Audit automatizzati di performance |
| Performance | k6 | Test di carico e stress |
| Accessibilita | axe-core | Analisi automatizzata WCAG |
| Accessibilita | eslint-plugin-jsx-a11y | Lint accessibilita nel codice |
| API Testing | Postman / Newman | Test e documentazione API |
| Mocking | MSW | Intercettazione richieste di rete |
| Mocking | nock | Mock HTTP per Node.js |
| Mocking | Faker.js | Generazione dati di test realistici |
| CI/CD | GitHub Actions | Automazione pipeline di test |
| Coverage | V8 / Istanbul | Raccolta metriche di copertura del codice |

---

## Esercizi

### Esercizio 1 — Unit Test per Modulo di Utilita

**Obiettivo:** scrivere una suite di unit test completa con Vitest per un modulo di funzioni pure.

Crea un modulo `utils/cart.ts` che espone le seguenti funzioni: `calculateTotal(items)`, `applyDiscount(total, percentage)`, `formatPrice(cents, locale)`, `validateCoupon(code, validCoupons)`. Scrivi i test seguendo il pattern AAA (Arrange-Act-Assert):

- Almeno 3 test case per ogni funzione (caso normale, edge case, errore)
- Usa `describe` per raggruppare i test per funzione
- Testa i casi limite: array vuoto, sconto negativo, codice coupon inesistente, valori `NaN`
- Verifica che la copertura del modulo raggiunga il 100%
- Esegui con `vitest run --coverage` e allega il report

### Esercizio 2 — Component Testing con Testing Library

**Obiettivo:** testare un componente React interattivo dal punto di vista dell'utente.

Dato un componente `<SearchFilter />` che contiene un campo di ricerca, un menu a tendina per categoria e un pulsante di reset:

- Scrivi test che verifichino il rendering iniziale con placeholder e opzioni predefinite
- Testa la digitazione nel campo di ricerca e verifica che il callback `onSearch` venga invocato con debounce di 300ms (usa `vi.useFakeTimers()`)
- Testa la selezione di una categoria dal dropdown e verifica il cambio di stato
- Testa il pulsante di reset: tutti i campi devono tornare ai valori iniziali
- Usa `userEvent` invece di `fireEvent` per simulazioni realistiche
- Verifica l'accessibilita: label associate ai campi, ruoli ARIA corretti

### Esercizio 3 — Mock di API con MSW

**Obiettivo:** testare un flusso di data fetching completo usando Mock Service Worker.

Implementa i test per un hook `useProducts()` che chiama `GET /api/products` e gestisce paginazione:

- Configura MSW con `setupServer` per intercettare le richieste HTTP
- Definisci handler per: risposta con successo (lista prodotti), risposta vuota, errore 500, errore di rete (timeout)
- Testa lo stato di loading, il rendering dei dati e lo stato di errore
- Testa la paginazione: verifica che il cambio di pagina invii il parametro `?page=N` corretto
- Testa il retry automatico dopo un errore transitorio
- Verifica che il componente mostri uno skeleton loader durante il caricamento e un messaggio appropriato in caso di errore

### Esercizio 4 — E2E Test con Playwright e Page Object Model

**Obiettivo:** implementare una suite E2E completa per un flusso di autenticazione usando il pattern Page Object Model.

Crea una suite Playwright per il flusso login → dashboard → logout:

- Definisci le classi `LoginPage`, `DashboardPage`, `NavBar` con metodi per ogni azione utente
- Test 1: login con credenziali valide, verifica redirect alla dashboard e presenza del nome utente
- Test 2: login con credenziali errate, verifica messaggio di errore visibile e campo password svuotato
- Test 3: accesso alla dashboard senza autenticazione, verifica redirect alla pagina di login
- Test 4: logout, verifica che la sessione venga invalidata e il tentativo di navigare alla dashboard rediriga al login
- Configura `playwright.config.ts` con progetto per Chrome, Firefox e WebKit
- Genera report HTML con screenshot delle pagine visitate

### Esercizio 5 — Pipeline CI/CD con Coverage Gate e Visual Regression

**Obiettivo:** configurare una pipeline GitHub Actions completa che integri test, coverage e visual regression.

Crea un workflow `.github/workflows/test.yml` che:

- Esegua unit test e component test con Vitest in parallelo su Node 20 e 22
- Esegua E2E test con Playwright su Chrome e Firefox (matrice di browser)
- Raccolga la copertura con V8 e fallisca la pipeline se la copertura scende sotto l'80%
- Integri visual regression con `@playwright/test` e `toHaveScreenshot()` su 3 breakpoint (mobile 375px, tablet 768px, desktop 1440px)
- Pubblichi i report di copertura e gli screenshot come artifact della pipeline
- Integri un commento automatico sulla PR con il riepilogo della copertura (usa `marocchino/sticky-pull-request-comment`)
- Aggiungi caching di `node_modules` e dei browser Playwright per velocizzare le esecuzioni successive

---

## Letture e Riferimenti

### Documentazione ufficiale

- **Vitest** — framework di test unitari nativo per Vite, compatibile con l'API Jest. https://vitest.dev/ (consultato: 2026-05-24)
- **Playwright** — framework E2E multi-browser di Microsoft con auto-wait e tracing. https://playwright.dev/ (consultato: 2026-05-24)
- **Testing Library** — famiglia di utility per testare componenti dal punto di vista dell'utente. https://testing-library.com/ (consultato: 2026-05-24)
- **Cypress** — framework E2E con runner interattivo e time-travel debugging. https://docs.cypress.io/ (consultato: 2026-05-24)
- **MSW (Mock Service Worker)** — intercettazione di richieste di rete a livello di Service Worker per test e sviluppo. https://mswjs.io/ (consultato: 2026-05-24)
- **axe-core** — motore di analisi automatizzata dell'accessibilita conforme a WCAG 2.x. https://github.com/dequelabs/axe-core (consultato: 2026-05-24)
- **Istanbul / nyc** — strumento di copertura del codice JavaScript con supporto per statement, branch, function e line coverage. https://istanbul.js.org/ (consultato: 2026-05-24)
- **GitHub Actions** — documentazione per l'automazione di workflow CI/CD. https://docs.github.com/en/actions (consultato: 2026-05-24)

### Libri e approfondimenti

- Kent C. Dodds, *Testing JavaScript Applications*, Manning, 2024.
- Mark Ethan Trostler, *Testable JavaScript*, O'Reilly, 2013.
- Gleb Bahmutov, *Cypress in Action*, Manning, 2021.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Basi del linguaggio necessarie per scrivere asserzioni, mock e fixture nei test |
| [06 — TypeScript](06-typescript.md) | Tipizzazione statica che migliora l'affidabilita dei test e abilita autocompletamento nelle asserzioni |
| [07 — React](07-react.md) | Framework target principale per component testing con Testing Library e test di hook |
| [14 — Sicurezza Web](14-sicurezza-web.md) | I test di sicurezza (CSRF, XSS, injection) complementano i test funzionali trattati qui |
| [16 — Build Tools e Deploy](16-build-tools-e-deploy.md) | Integrazione dei test nella pipeline CI/CD e configurazione degli step di build |
| [17 — Performance Web](17-performance-web.md) | Lighthouse CI e test di performance automatizzati integrano la strategia di testing |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Unit test** | Test che verifica il comportamento di una singola unita di codice (funzione, classe, modulo) in isolamento. |
| **Integration test** | Test che verifica l'interazione tra due o piu moduli, come un endpoint API con il database. |
| **E2E test** | Test end-to-end che simula il comportamento di un utente reale attraverso l'intera applicazione nel browser. |
| **TDD** | Test-Driven Development: metodologia in cui si scrivono i test prima dell'implementazione (Red-Green-Refactor). |
| **BDD** | Behaviour-Driven Development: estensione di TDD che usa un linguaggio naturale (Given-When-Then) per descrivere i test. |
| **Coverage** | Percentuale di codice sorgente eseguita durante l'esecuzione dei test, misurata per statement, branch, funzione e riga. |
| **Mock** | Oggetto simulato che sostituisce una dipendenza reale durante i test, permettendo di controllare il comportamento e verificare le interazioni. |
| **Stub** | Implementazione semplificata di una dipendenza che restituisce valori predefiniti senza logica complessa. |
| **Fixture** | Dati predefiniti utilizzati come input per i test, che garantiscono condizioni iniziali ripetibili. |
| **Assertion** | Verifica esplicita di una condizione attesa nel test; il fallimento di un'assertion causa il fallimento del test. |
| **Page Object Model** | Pattern di design per E2E test che incapsula i selettori e le azioni di una pagina in una classe riutilizzabile. |
| **Visual regression** | Tecnica di testing che confronta screenshot della UI tra versioni per rilevare cambiamenti visivi non intenzionali. |
| **Flaky test** | Test instabile che produce risultati diversi su esecuzioni successive senza modifiche al codice, spesso causato da dipendenze temporali o di stato. |
| **Test isolation** | Principio per cui ogni test deve essere indipendente dagli altri, senza condivisione di stato o effetti collaterali. |
| **Code coverage gate** | Soglia minima di copertura del codice configurata nella pipeline CI/CD; la build fallisce se la copertura scende sotto il limite. |

Ogni strumento ha un ruolo specifico nella strategia di testing complessiva. La scelta degli strumenti dipende dalle tecnologie dell'applicazione, dalla dimensione del team e dai requisiti di qualita del progetto. L'importante non e utilizzare tutti gli strumenti disponibili, ma costruire una suite di test che copra i rischi reali dell'applicazione con il giusto equilibrio tra costo e valore protettivo.