---
corso: "Programmazione Python"
fase: "3 — Librerie e Framework"
modulo: "11"
titolo: "Web Framework Python"
versione: "Flask 3.1+ / FastAPI 0.115+ / Django 5.1+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01-06 — Python Base"
  - "02 — OOP"
  - "10 — Programmazione Asincrona"
obiettivi:
  - "Costruire API REST con Flask, FastAPI e Django"
  - "Implementare autenticazione, validazione e serializzazione"
  - "Utilizzare ORM (SQLAlchemy, Django ORM) per persistenza dati"
  - "Configurare middleware, CORS e rate limiting"
  - "Scrivere test per endpoint API con client di test"
  - "Deployare applicazioni web con Docker e reverse proxy"
tag: [flask, fastapi, django, REST-API, web, ORM, SQLAlchemy, middleware]
---

# Web Framework Python — Guida Completa

> **Modulo 11** · **Aggiornamento:** 2026-05-24 · **Versione:** Flask 3.1+ / FastAPI 0.115+ / Django 5.1+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [OOP](02-oop.md), [Programmazione Asincrona](10-programmazione-asincrona.md)
>
> Al termine di questo modulo saprai:
> 1. Costruire API REST con Flask, FastAPI e Django
> 2. Implementare autenticazione, validazione e serializzazione dei dati
> 3. Utilizzare ORM (SQLAlchemy, Django ORM) per la persistenza
> 4. Configurare middleware, CORS, rate limiting e security headers
> 5. Scrivere test per endpoint API con client di test integrati
> 6. Deployare applicazioni web con Docker e reverse proxy
>
> **Tempo stimato:** 10-12 ore · **Livello:** Intermedio-Avanzato

```
corso:        Programmazione Python
fase:         Intermedia-Avanzata
versione:     3.0
livello:      Intermedio → Avanzato
obiettivi:
  - Padroneggiare Flask 3.x con async views, nested blueprints e gestione errori migliorata
  - Implementare il pattern lifespan di FastAPI sostituendo on_startup/on_shutdown deprecati
  - Comprendere in profondita ASGI, il protocollo lifespan e il flusso delle richieste sotto uvloop
  - Progettare middleware riutilizzabili per autenticazione, rate limiting, compressione e request ID
  - Costruire sistemi di dependency injection testabili con sub-dipendenze e override
  - Gestire sessioni, file statici, template Jinja2, API versioning e personalizzazione OpenAPI
  - Confrontare strategie di background task: BackgroundTasks, Celery, arq, dramatiq
  - Configurare deployment di produzione con uvicorn, gunicorn + uvicorn workers, hypercorn e Daphne
```

## Idee guida
1. **FastAPI > Flask per nuove API.** Async, type-safe, auto-OpenAPI.
2. **Flask 3.x: blueprint + extension stack mature.**
3. **FastAPI lifespan event > startup/shutdown.**
4. **Django per full-stack monolith.** ORM + admin + auth out-of-box.
5. **ASGI e il futuro.** WebSocket, HTTP/2, streaming nativo — WSGI resta per legacy ma ASGI e la direzione.
6. **Middleware come infrastruttura.** CORS, auth, rate limiting, compressione, request ID — cross-framework.


## Indice

1. [Panoramica](#panoramica)
2. [Mappa Concettuale — WSGI vs ASGI](#mappa-concettuale--wsgi-vs-asgi)
3. [Flask](#flask)
4. [Flask 3.x — Novita](#flask-3x--novita)
5. [FastAPI](#fastapi)
6. [FastAPI Lifespan — Approfondimento](#fastapi-lifespan--approfondimento)
7. [Django (Panoramica)](#django-panoramica)
8. [Confronto Framework](#confronto-framework)
9. [ASGI — Approfondimento](#asgi--approfondimento)
10. [Pattern Middleware Cross-Framework](#pattern-middleware-cross-framework)
11. [Dependency Injection — Approfondimento](#dependency-injection--approfondimento)
12. [Template Engine e Jinja2](#template-engine-e-jinja2)
13. [File Statici in Produzione](#file-statici-in-produzione)
14. [Gestione Sessioni](#gestione-sessioni)
15. [Background Tasks — Confronto](#background-tasks--confronto)
16. [Deployment](#deployment)
17. [Deployment Avanzato — ASGI Servers](#deployment-avanzato--asgi-servers)
18. [API Versioning](#api-versioning)
19. [Personalizzazione OpenAPI](#personalizzazione-openapi)
20. [Best Practices](#best-practices)
21. [Troubleshooting](#troubleshooting)
22. [Esercizi](#esercizi)
23. [Letture](#letture)
24. [Cross-link](#cross-link)
25. [Glossario](#glossario)

---

## Panoramica

I web framework Python rappresentano uno degli strumenti piu potenti e versatili nel panorama dello sviluppo web moderno. Python, grazie alla sua sintassi leggibile e al vasto ecosistema di librerie, si e affermato come linguaggio di riferimento per la costruzione di applicazioni web, API RESTful, microservizi e piattaforme complesse.

### Il panorama dei web framework Python

L'ecosistema Python offre una varieta di framework che coprono esigenze diverse. I tre protagonisti principali sono **Flask**, **FastAPI** e **Django**, ciascuno con una filosofia progettuale distinta e un insieme di casi d'uso ideali. Accanto a questi esistono alternative come Bottle, Tornado, Starlette, Sanic e Falcon, ma i tre menzionati dominano il mercato e le offerte di lavoro.

### Microframework vs Full-Stack

La distinzione fondamentale nel mondo dei web framework riguarda l'approccio architetturale:

**Microframework** (Flask, FastAPI): forniscono il minimo indispensabile per gestire richieste HTTP e costruire applicazioni web. Non impongono un ORM, un sistema di template o una struttura di progetto specifica. Lo sviluppatore sceglie i componenti da integrare, ottenendo massima flessibilita ma anche maggiore responsabilita nelle decisioni architetturali.

**Full-Stack Framework** (Django): includono tutto il necessario fin dall'inizio — ORM, sistema di template, autenticazione, pannello di amministrazione, gestione delle migrazioni del database e molto altro. Seguono il principio "batteries included" e offrono una struttura di progetto ben definita, accelerando lo sviluppo iniziale ma imponendo convenzioni specifiche.

### WSGI vs ASGI

Due protocolli fondamentali regolano la comunicazione tra il server web e l'applicazione Python:

**WSGI** (Web Server Gateway Interface) e lo standard tradizionale, definito nella PEP 3333. Opera in modo sincrono: ogni richiesta viene gestita da un singolo thread o processo. Flask e Django (nella configurazione classica) utilizzano WSGI. I server WSGI piu diffusi sono Gunicorn e uWSGI.

```python
# Esempio minimo di applicazione WSGI
def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b'Ciao dal mondo WSGI!']
```

**ASGI** (Asynchronous Server Gateway Interface) e l'evoluzione asincrona di WSGI. Supporta WebSocket, HTTP/2 e operazioni asincrone native. FastAPI e Django (dalla versione 3.0+) supportano ASGI. Il server ASGI di riferimento e Uvicorn.

```python
# Esempio minimo di applicazione ASGI
async def application(scope, receive, send):
    if scope['type'] == 'http':
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [[b'content-type', b'text/plain']],
        })
        await send({
            'type': 'http.response.body',
            'body': b'Ciao dal mondo ASGI!',
        })
```

La scelta tra WSGI e ASGI dipende dalle necessita del progetto: WSGI e piu semplice e maturo, mentre ASGI e indispensabile quando servono WebSocket, streaming o gestione concorrente di molte connessioni lente (come chiamate a servizi esterni).

---

## Mappa Concettuale — WSGI vs ASGI

Il flusso di una richiesta HTTP attraverso i due protocolli differisce radicalmente nella gestione della concorrenza.

### Flusso WSGI (sincrono, PEP 3333)

```
Client HTTP
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  Reverse Proxy (Nginx)                                       │
│  - TLS termination                                           │
│  - static files                                              │
│  - gzip                                                      │
└──────────────┬───────────────────────────────────────────────┘
               │  proxy_pass → 127.0.0.1:8000
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Gunicorn (WSGI Server)                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │  Worker 1   │ │  Worker 2   │ │  Worker N   │              │
│  │  (processo) │ │  (processo) │ │  (processo) │              │
│  │             │ │             │ │             │              │
│  │  1 richiesta│ │  1 richiesta│ │  1 richiesta│              │
│  │  alla volta │ │  alla volta │ │  alla volta │              │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘             │
│         │               │               │                     │
│         ▼               ▼               ▼                     │
│  ┌─────────────────────────────────────────────────┐         │
│  │  Flask / Django App                              │         │
│  │  application(environ, start_response)            │         │
│  │                                                   │         │
│  │  environ = dict con HTTP headers, path, method   │         │
│  │  start_response = callback per status + headers  │         │
│  │  return = iterable di bytes (body)               │         │
│  └─────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────┘
```

**Caratteristiche chiave WSGI:**
- Un worker = un thread/processo = una richiesta alla volta
- Concorrenza tramite processi multipli (pre-fork)
- Blocking I/O: il worker attende il database, l'API esterna, il filesystem
- Memoria: ogni worker replica l'intero interprete Python
- Formula worker: `2 * num_cpu + 1` (regola empirica Gunicorn)

### Flusso ASGI (asincrono)

```
Client HTTP / WebSocket
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  Reverse Proxy (Nginx)                                       │
│  - TLS termination                                           │
│  - WebSocket upgrade (proxy_set_header Upgrade)              │
└──────────────┬───────────────────────────────────────────────┘
               │  proxy_pass → 127.0.0.1:8000
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Uvicorn (ASGI Server)                                       │
│  ┌─────────────────────────────────────────────┐             │
│  │  Worker (processo)                            │            │
│  │  ┌─────────────────────────────────────┐     │            │
│  │  │  Event Loop (asyncio / uvloop)      │     │            │
│  │  │                                      │     │            │
│  │  │  Richiesta A ──┐  (await db.query)  │     │            │
│  │  │  Richiesta B ──┤  (await api.call)  │     │            │
│  │  │  Richiesta C ──┤  (await file.read) │     │            │
│  │  │  WebSocket D ──┘  (await ws.recv)   │     │            │
│  │  │                                      │     │            │
│  │  │  → Tutte condividono lo stesso loop  │     │            │
│  │  │  → Nessun thread aggiuntivo          │     │            │
│  │  └─────────────────────────────────────┘     │            │
│  └─────────────────────────────────────────────┘             │
│                                                               │
│  ASGI callable: async def app(scope, receive, send)          │
│                                                               │
│  scope['type']:                                               │
│    'http'      → richiesta HTTP standard                     │
│    'websocket' → connessione WebSocket                       │
│    'lifespan'  → eventi di avvio/arresto                     │
└──────────────────────────────────────────────────────────────┘
```

**Caratteristiche chiave ASGI:**
- Un worker puo gestire migliaia di richieste concorrenti tramite l'event loop
- Non-blocking I/O: il worker cede il controllo durante l'attesa (await)
- Supporto nativo per WebSocket, Server-Sent Events, HTTP/2
- Memoria: un singolo worker e sufficiente per carichi I/O-bound
- uvloop (implementazione in Cython di asyncio) raddoppia il throughput rispetto all'event loop standard

### Confronto quantitativo

| Aspetto | WSGI (Gunicorn sync) | ASGI (Uvicorn + uvloop) |
|---------|---------------------|------------------------|
| Richieste/sec (I/O-bound) | ~500-2000/worker | ~5000-15000/worker |
| Connessioni simultanee | = numero worker | migliaia per worker |
| WebSocket | No (richiede addon) | Nativo |
| Memoria per 1000 connessioni | ~4 GB (4 worker x 1 GB) | ~200 MB |
| CPU-bound tasks | OK (GIL per processo) | Problema (blocca event loop) |

> **Regola pratica:** Se il servizio fa prevalentemente I/O (database, API, file), ASGI vince. Se fa calcolo CPU-intensive, WSGI con worker sync e piu predicibile — oppure ASGI con `run_in_executor`.

---

## Flask

Flask e un microframework creato da Armin Ronacher nel 2010. La sua filosofia e "una goccia alla volta": fornisce il nucleo essenziale e lascia allo sviluppatore la liberta di estendere l'applicazione secondo le proprie necessita. Flask si basa su due componenti fondamentali: **Werkzeug** (toolkit WSGI) e **Jinja2** (motore di template).

### Fondamenti

#### Application Factory Pattern

Il pattern Application Factory e la pratica consigliata per strutturare applicazioni Flask di medie e grandi dimensioni. Consiste nel creare una funzione che costruisce e configura l'istanza dell'applicazione, anziche definirla come variabile globale.

```python
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inizializzazione estensioni
    db.init_app(app)
    migrate.init_app(app, db)

    # Registrazione blueprint
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Registrazione error handler
    from app.errors import register_error_handlers
    register_error_handlers(app)

    return app
```

Questo pattern offre diversi vantaggi: facilita il testing (ogni test puo creare un'istanza con configurazione diversa), evita problemi con le importazioni circolari e rende l'applicazione piu modulare.

#### Routes and Views

Le route in Flask collegano URL a funzioni Python (dette view function). Si definiscono tramite il decoratore `@app.route()` o, piu comunemente nei progetti strutturati, tramite i blueprint.

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

# Route base con metodo GET
@app.route('/')
def index():
    return '<h1>Benvenuto nella mia applicazione Flask</h1>'

# Route con parametro dinamico
@app.route('/utenti/<int:user_id>')
def get_utente(user_id):
    utente = Utente.query.get_or_404(user_id)
    return jsonify(utente.to_dict())

# Route con metodi multipli
@app.route('/utenti', methods=['GET', 'POST'])
def gestisci_utenti():
    if request.method == 'POST':
        dati = request.get_json()
        nuovo_utente = Utente(nome=dati['nome'], email=dati['email'])
        db.session.add(nuovo_utente)
        db.session.commit()
        return jsonify(nuovo_utente.to_dict()), 201

    # GET: restituisci tutti gli utenti
    utenti = Utente.query.all()
    return jsonify([u.to_dict() for u in utenti])

# Convertitori di URL supportati: string, int, float, path, uuid
@app.route('/file/<path:percorso_file>')
def mostra_file(percorso_file):
    return f'Il percorso richiesto e: {percorso_file}'
```

#### Request e Response Objects

Flask fornisce oggetti `request` e `Response` per gestire i dati in entrata e in uscita.

```python
from flask import Flask, request, make_response, jsonify

app = Flask(__name__)

@app.route('/esempio', methods=['POST'])
def esempio_request():
    # Accesso ai dati della richiesta
    metodo = request.method                    # 'POST'
    content_type = request.content_type        # 'application/json'
    dati_json = request.get_json()             # body JSON parsato
    parametri_query = request.args             # parametri URL (?chiave=valore)
    dati_form = request.form                   # dati da form HTML
    file_caricati = request.files              # file uploadati
    headers = request.headers                  # header HTTP
    cookies = request.cookies                  # cookie del client
    ip_client = request.remote_addr            # indirizzo IP del client

    # Creazione di una risposta personalizzata
    risposta = make_response(jsonify({'messaggio': 'Creato con successo'}))
    risposta.status_code = 201
    risposta.headers['X-Custom-Header'] = 'valore-personalizzato'
    risposta.set_cookie('sessione_id', 'abc123', httponly=True, secure=True)

    return risposta
```

#### URL Building (url_for)

La funzione `url_for()` genera URL dinamicamente a partire dal nome della view function. E fondamentale per evitare URL hardcoded nel codice e nei template.

```python
from flask import Flask, url_for, redirect

app = Flask(__name__)

@app.route('/utenti/<int:user_id>/profilo')
def profilo_utente(user_id):
    return f'Profilo utente {user_id}'

@app.route('/login')
def login():
    # Redirect dopo il login
    return redirect(url_for('profilo_utente', user_id=42))
    # Genera: /utenti/42/profilo

# Nei template Jinja2:
# <a href="{{ url_for('profilo_utente', user_id=utente.id) }}">Profilo</a>
# File statici:
# <link rel="stylesheet" href="{{ url_for('static', filename='css/stile.css') }}">
```

#### Templates (Jinja2)

Jinja2 e il motore di template integrato in Flask. Permette di generare HTML dinamico con variabili, cicli, condizioni e ereditarieta dei template.

```html
{# templates/base.html — Template base con ereditarieta #}
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}La Mia App{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/stile.css') }}">
</head>
<body>
    <nav>
        {% if current_user.is_authenticated %}
            <span>Benvenuto, {{ current_user.nome }}</span>
            <a href="{{ url_for('auth.logout') }}">Esci</a>
        {% else %}
            <a href="{{ url_for('auth.login') }}">Accedi</a>
        {% endif %}
    </nav>

    <main>
        {# Messaggi flash per notifiche #}
        {% with messaggi = get_flashed_messages(with_categories=true) %}
            {% for categoria, messaggio in messaggi %}
                <div class="alert alert-{{ categoria }}">{{ messaggio }}</div>
            {% endfor %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

```html
{# templates/utenti/lista.html — Template figlio #}
{% extends "base.html" %}

{% block title %}Lista Utenti{% endblock %}

{% block content %}
<h1>Utenti registrati</h1>
<ul>
    {% for utente in utenti %}
        <li>
            <a href="{{ url_for('main.profilo_utente', user_id=utente.id) }}">
                {{ utente.nome | capitalize }} — {{ utente.email }}
            </a>
        </li>
    {% else %}
        <li>Nessun utente trovato.</li>
    {% endfor %}
</ul>
{% endblock %}
```

### Funzionalita Avanzate

#### Blueprints (Applicazioni Modulari)

I Blueprint permettono di organizzare un'applicazione Flask in moduli separati, ciascuno con le proprie route, template e file statici.

```python
# app/auth/__init__.py
from flask import Blueprint

bp = Blueprint('auth', __name__, template_folder='templates')

from app.auth import routes  # importazione in fondo per evitare circolarita


# app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.auth import bp
from app.models import Utente

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        utente = Utente.query.filter_by(email=email).first()
        if utente and utente.verifica_password(password):
            login_user(utente)
            flash('Accesso effettuato con successo!', 'success')
            return redirect(url_for('main.index'))
        flash('Credenziali non valide.', 'error')
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Disconnessione effettuata.', 'info')
    return redirect(url_for('main.index'))
```

#### Extensions

Flask dispone di un ricco ecosistema di estensioni per aggiungere funzionalita specifiche:

```python
# Configurazione delle estensioni principali

# Flask-SQLAlchemy — ORM per database relazionali
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Utente(db.Model):
    __tablename__ = 'utenti'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    articoli = db.relationship('Articolo', backref='autore', lazy='dynamic')

# Flask-Login — Gestione sessioni utente
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina.'

# Flask-Migrate — Migrazioni database con Alembic
from flask_migrate import Migrate
migrate = Migrate()
# Comandi: flask db init, flask db migrate -m "descrizione", flask db upgrade

# Flask-CORS — Cross-Origin Resource Sharing
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "https://miosito.it"}})

# Flask-Mail — Invio email
from flask_mail import Mail, Message
mail = Mail()

def invia_email_benvenuto(utente):
    msg = Message(
        subject='Benvenuto!',
        sender='noreply@miaapp.it',
        recipients=[utente.email]
    )
    msg.body = f'Ciao {utente.nome}, benvenuto nella nostra piattaforma!'
    mail.send(msg)
```

#### Error Handlers

I gestori di errore personalizzano le risposte per codici di stato HTTP specifici.

```python
# app/errors/__init__.py
from flask import jsonify, render_template, request

def register_error_handlers(app):

    @app.errorhandler(404)
    def not_found(error):
        if request.accept_mimetypes.accept_json and \
           not request.accept_mimetypes.accept_html:
            return jsonify({'errore': 'Risorsa non trovata'}), 404
        return render_template('errori/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from app import db
        db.session.rollback()
        return jsonify({'errore': 'Errore interno del server'}), 500

    @app.errorhandler(429)
    def too_many_requests(error):
        return jsonify({'errore': 'Troppe richieste. Riprova piu tardi.'}), 429
```

#### Middleware

I middleware in Flask si implementano tramite i decoratori `before_request`, `after_request` e `teardown_request`.

```python
from flask import Flask, g, request
import time

app = Flask(__name__)

@app.before_request
def prima_della_richiesta():
    g.inizio_richiesta = time.time()
    # Autenticazione API tramite token
    if request.path.startswith('/api/'):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'errore': 'Token mancante'}), 401

@app.after_request
def dopo_la_richiesta(response):
    durata = time.time() - g.get('inizio_richiesta', time.time())
    response.headers['X-Tempo-Risposta'] = f'{durata:.4f}s'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

@app.teardown_request
def chiusura_richiesta(exception):
    # Pulizia risorse (connessioni DB, file temporanei)
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()
```

#### Configuration Management

La gestione della configurazione in Flask segue un pattern basato su classi.

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'chiave-segreta-di-default')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DEV_DATABASE_URL', 'sqlite:///dev.db'
    )

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

configurazioni = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

#### Application Context e Request Context

Flask utilizza due contesti fondamentali: l'application context (accessibile tramite `current_app` e `g`) e il request context (accessibile tramite `request` e `session`). Comprendere questi contesti e essenziale per evitare errori come "Working outside of application context".

```python
from flask import Flask, current_app, g, request

app = Flask(__name__)

# L'application context e attivo all'interno delle view
# oppure puo essere attivato manualmente
with app.app_context():
    print(current_app.config['SECRET_KEY'])

# g e un oggetto per memorizzare dati durante una singola richiesta
@app.before_request
def carica_utente():
    token = request.headers.get('Authorization')
    if token:
        g.utente_corrente = Utente.verifica_token(token)
```

### API con Flask

#### Flask-RESTful e flask-smorest

Per costruire API RESTful strutturate, si utilizzano estensioni dedicate.

```python
# Esempio con flask-smorest (approccio moderno basato su OpenAPI)
from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['API_TITLE'] = 'La Mia API'
app.config['API_VERSION'] = 'v1'
app.config['OPENAPI_VERSION'] = '3.0.2'
app.config['OPENAPI_URL_PREFIX'] = '/'
app.config['OPENAPI_SWAGGER_UI_PATH'] = '/docs'
app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

api = Api(app)

# Schema Marshmallow per serializzazione e validazione
class ArticoloSchema(Schema):
    id = fields.Int(dump_only=True)
    titolo = fields.Str(required=True)
    contenuto = fields.Str(required=True)
    data_creazione = fields.DateTime(dump_only=True)
    autore_id = fields.Int(required=True)

class ArticoloQuerySchema(Schema):
    pagina = fields.Int(load_default=1)
    per_pagina = fields.Int(load_default=20)

# Blueprint per gli articoli
blp = Blueprint('articoli', __name__, url_prefix='/api/v1/articoli',
                description='Operazioni sugli articoli')

@blp.route('/')
class ArticoliList(MethodView):
    @blp.arguments(ArticoloQuerySchema, location='query')
    @blp.response(200, ArticoloSchema(many=True))
    def get(self, args):
        """Ottieni la lista degli articoli con paginazione."""
        pagina = args.get('pagina', 1)
        per_pagina = args.get('per_pagina', 20)
        return Articolo.query.paginate(
            page=pagina, per_page=per_pagina
        ).items

    @blp.arguments(ArticoloSchema)
    @blp.response(201, ArticoloSchema)
    def post(self, dati_articolo):
        """Crea un nuovo articolo."""
        articolo = Articolo(**dati_articolo)
        db.session.add(articolo)
        db.session.commit()
        return articolo

api.register_blueprint(blp)
```

#### Marshmallow per la Serializzazione

Marshmallow e la libreria standard per la serializzazione, deserializzazione e validazione dei dati in Flask.

```python
from marshmallow import Schema, fields, validate, validates, ValidationError

class UtenteSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(load_only=True, required=True,
                          validate=validate.Length(min=8))
    ruolo = fields.Str(validate=validate.OneOf(['admin', 'utente', 'moderatore']))
    data_registrazione = fields.DateTime(dump_only=True)

    @validates('nome')
    def valida_nome(self, valore):
        if valore.strip() != valore:
            raise ValidationError('Il nome non puo avere spazi iniziali o finali.')
```

#### JWT Authentication (Flask-JWT-Extended)

L'autenticazione tramite JSON Web Token e lo standard per le API stateless.

```python
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import timedelta

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'la-tua-chiave-segreta-molto-lunga'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

jwt = JWTManager(app)

# Set per i token revocati (in produzione usare Redis)
token_revocati = set()

@jwt.token_in_blocklist_loader
def controlla_se_revocato(jwt_header, jwt_payload):
    return jwt_payload['jti'] in token_revocati

@app.route('/auth/login', methods=['POST'])
def login():
    dati = request.get_json()
    utente = Utente.query.filter_by(email=dati['email']).first()
    if utente and utente.verifica_password(dati['password']):
        access_token = create_access_token(
            identity=utente.id,
            additional_claims={'ruolo': utente.ruolo}
        )
        refresh_token = create_refresh_token(identity=utente.id)
        return jsonify(access_token=access_token, refresh_token=refresh_token)
    return jsonify({'errore': 'Credenziali non valide'}), 401

@app.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identita = get_jwt_identity()
    nuovo_token = create_access_token(identity=identita)
    return jsonify(access_token=nuovo_token)

@app.route('/api/protetto')
@jwt_required()
def risorsa_protetta():
    utente_id = get_jwt_identity()
    claims = get_jwt()
    return jsonify(
        utente_id=utente_id,
        ruolo=claims.get('ruolo'),
        messaggio='Accesso autorizzato'
    )
```

---

## Flask 3.x — Novita

Flask 3.0 (rilasciato nel 2023) e Flask 3.1 rappresentano un salto significativo nella modernizzazione del framework. Le novita principali riguardano il supporto nativo per le view asincrone, i blueprint annidati, le modifiche al CLI e i miglioramenti alla gestione degli errori.

> **Fonte:** Flask Changelog — https://flask.palletsprojects.com/en/stable/changes/

### Async Views (Flask 3.x)

A partire da Flask 2.0, le view asincrone erano supportate sperimentalmente. Con Flask 3.x il supporto e stabile e pronto per la produzione. Flask esegue le coroutine tramite `asyncio.run()` all'interno di ciascun thread del worker WSGI, quindi non si ottiene la stessa concorrenza di un server ASGI puro, ma si possono utilizzare librerie asincrone come `httpx`, `aiohttp` e driver asincroni per database.

```python
from flask import Flask, jsonify
import httpx

app = Flask(__name__)

# View sincrona classica
@app.route('/sync')
def view_sincrona():
    return jsonify({"tipo": "sincrona"})

# View asincrona — Flask 3.x
@app.route('/async')
async def view_asincrona():
    async with httpx.AsyncClient() as client:
        risposta = await client.get('https://api.esempio.it/dati')
    return jsonify(risposta.json())

# Async con multiple chiamate parallele
@app.route('/parallel')
async def view_parallela():
    import asyncio
    async with httpx.AsyncClient() as client:
        risultati = await asyncio.gather(
            client.get('https://api.esempio.it/utenti'),
            client.get('https://api.esempio.it/prodotti'),
            client.get('https://api.esempio.it/ordini'),
        )
    return jsonify({
        "utenti": risultati[0].json(),
        "prodotti": risultati[1].json(),
        "ordini": risultati[2].json(),
    })

# Async error handler
@app.errorhandler(500)
async def errore_interno(error):
    await registra_errore_async(error)
    return jsonify({"errore": "Errore interno del server"}), 500

# Async before_request
@app.before_request
async def prima_della_richiesta_async():
    # Utile per validazione token asincrona
    token = request.headers.get('Authorization')
    if token:
        g.utente = await valida_token_async(token)
```

**Attenzione:** Flask esegue ogni view asincrona in un event loop temporaneo. Questo significa che:
- Non si possono condividere oggetti `asyncio` tra richieste diverse
- Non ci sono WebSocket nativi (per quelli serve un server ASGI come Uvicorn con Quart o FastAPI)
- Il vantaggio principale e poter usare client HTTP asincroni per aggregare chiamate a servizi esterni

### Nested Blueprints (Blueprint Annidati)

Flask 3.x consolida il supporto per i blueprint annidati, introdotto in Flask 2.0. Un blueprint puo registrare altri blueprint al proprio interno, creando gerarchie modulari con prefissi URL cumulativi.

```python
from flask import Blueprint

# Blueprint padre per l'API
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Blueprint figlio per la versione 1
v1_bp = Blueprint('v1', __name__, url_prefix='/v1')

# Blueprint nipote per le risorse utenti
utenti_bp = Blueprint('utenti', __name__, url_prefix='/utenti')

@utenti_bp.route('/')
def lista_utenti():
    """GET /api/v1/utenti/"""
    return jsonify({"utenti": []})

@utenti_bp.route('/<int:uid>')
def dettaglio_utente(uid):
    """GET /api/v1/utenti/123"""
    return jsonify({"id": uid})

# Blueprint nipote per i prodotti
prodotti_bp = Blueprint('prodotti', __name__, url_prefix='/prodotti')

@prodotti_bp.route('/')
def lista_prodotti():
    """GET /api/v1/prodotti/"""
    return jsonify({"prodotti": []})

# Composizione gerarchica
v1_bp.register_blueprint(utenti_bp)
v1_bp.register_blueprint(prodotti_bp)
api_bp.register_blueprint(v1_bp)

# Nella factory
def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    # URL risultanti:
    # /api/v1/utenti/
    # /api/v1/utenti/<int:uid>
    # /api/v1/prodotti/
    return app
```

**Pattern utile — blueprint per versione API:**

```python
# Versione 2 con blueprint separato
v2_bp = Blueprint('v2', __name__, url_prefix='/v2')

# Riutilizza le route di v1 dove compatibili
v2_bp.register_blueprint(prodotti_bp)

# Registra entrambe le versioni
api_bp.register_blueprint(v1_bp)
api_bp.register_blueprint(v2_bp)
# → /api/v1/prodotti/ e /api/v2/prodotti/ convivono
```

### Modifiche al CLI (Flask 3.x)

Flask 3.x semplifica il CLI e rimuove comportamenti legacy:

```bash
# Flask 3.x: il comando `flask run` usa --app invece di FLASK_APP
flask --app app run --debug

# Il flag --debug sostituisce FLASK_ENV=development (deprecato dal 2.3)
# --debug abilita sia il debugger sia il reloader

# Custom CLI commands con click (invariato ma consigliato con app factory)
```

```python
import click
from flask import Flask

def create_app():
    app = Flask(__name__)

    @app.cli.command('seed-db')
    @click.option('--count', default=10, help='Numero di record da creare')
    def seed_db(count):
        """Popola il database con dati di esempio."""
        for i in range(count):
            utente = Utente(nome=f'Utente {i}', email=f'utente{i}@esempio.it')
            db.session.add(utente)
        db.session.commit()
        click.echo(f'Creati {count} utenti di esempio.')

    @app.cli.command('clean-expired')
    def clean_expired():
        """Rimuove i token scaduti dal database."""
        rimossi = Token.query.filter(Token.scadenza < datetime.utcnow()).delete()
        db.session.commit()
        click.echo(f'Rimossi {rimossi} token scaduti.')

    return app
```

### Gestione Errori Migliorata (Flask 3.x)

Flask 3.x migliora il sistema di error handling con supporto per eccezioni personalizzate e risposte strutturate piu coerenti.

```python
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

# Eccezione personalizzata con contesto strutturato
class AppException(Exception):
    def __init__(self, messaggio, codice=400, dettagli=None):
        super().__init__(messaggio)
        self.messaggio = messaggio
        self.codice = codice
        self.dettagli = dettagli or {}

class RisorsaNonTrovata(AppException):
    def __init__(self, risorsa, id_risorsa):
        super().__init__(
            messaggio=f'{risorsa} con ID {id_risorsa} non trovato',
            codice=404,
            dettagli={'risorsa': risorsa, 'id': id_risorsa}
        )

class ValidazioneErrata(AppException):
    def __init__(self, errori_campo):
        super().__init__(
            messaggio='Errore di validazione',
            codice=422,
            dettagli={'errori': errori_campo}
        )

# Handler unificato per eccezioni applicative
@app.errorhandler(AppException)
def gestisci_eccezione_app(errore):
    return jsonify({
        'successo': False,
        'errore': {
            'messaggio': errore.messaggio,
            'codice': errore.codice,
            'dettagli': errore.dettagli
        }
    }), errore.codice

# Handler per tutte le eccezioni Werkzeug (404, 405, 413, ecc.)
@app.errorhandler(HTTPException)
def gestisci_eccezione_http(errore):
    return jsonify({
        'successo': False,
        'errore': {
            'messaggio': errore.description,
            'codice': errore.code
        }
    }), errore.code

# Handler per eccezioni non gestite (500)
@app.errorhandler(Exception)
def gestisci_eccezione_generica(errore):
    # Log completo per il debugging, risposta generica al client
    app.logger.exception(f'Eccezione non gestita: {errore}')
    return jsonify({
        'successo': False,
        'errore': {
            'messaggio': 'Errore interno del server',
            'codice': 500
        }
    }), 500

# Utilizzo nelle route
@app.route('/utenti/<int:uid>')
def get_utente(uid):
    utente = db.session.get(Utente, uid)
    if not utente:
        raise RisorsaNonTrovata('Utente', uid)
    return jsonify(utente.to_dict())
```

---

## FastAPI

FastAPI e un framework moderno e ad alte prestazioni creato da Sebastian Ramirez nel 2018. Si basa su Starlette (per la parte web) e Pydantic (per la validazione dei dati) e sfrutta appieno i type hint di Python per generare automaticamente documentazione OpenAPI, validare i dati in ingresso e serializzare le risposte.

### Fondamenti

#### Creazione dell'Applicazione

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Lifespan per gestire startup e shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Codice eseguito all'avvio
    print("Avvio applicazione: connessione al database...")
    await database.connect()
    yield
    # Codice eseguito allo spegnimento
    print("Chiusura applicazione: disconnessione dal database...")
    await database.disconnect()

app = FastAPI(
    title="La Mia API",
    description="API di esempio con FastAPI",
    version="1.0.0",
    lifespan=lifespan
)
```

#### Path Operations (GET, POST, PUT, DELETE)

Le operazioni sui path sono il cuore di FastAPI. Ogni decoratore corrisponde a un metodo HTTP.

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI()

# Modello Pydantic per la validazione
class ArticoloCreate(BaseModel):
    titolo: str
    contenuto: str
    pubblicato: bool = False

class ArticoloResponse(BaseModel):
    id: int
    titolo: str
    contenuto: str
    pubblicato: bool
    data_creazione: datetime

    model_config = {"from_attributes": True}

# Database simulato
articoli_db: dict[int, dict] = {}
contatore_id = 0

@app.get("/articoli", response_model=list[ArticoloResponse])
async def lista_articoli(pubblicato: Optional[bool] = None, skip: int = 0, limit: int = 10):
    """Restituisce la lista degli articoli con filtri opzionali."""
    risultati = list(articoli_db.values())
    if pubblicato is not None:
        risultati = [a for a in risultati if a['pubblicato'] == pubblicato]
    return risultati[skip:skip + limit]

@app.post("/articoli", response_model=ArticoloResponse, status_code=status.HTTP_201_CREATED)
async def crea_articolo(articolo: ArticoloCreate):
    """Crea un nuovo articolo."""
    global contatore_id
    contatore_id += 1
    nuovo = {
        'id': contatore_id,
        **articolo.model_dump(),
        'data_creazione': datetime.now()
    }
    articoli_db[contatore_id] = nuovo
    return nuovo

@app.get("/articoli/{articolo_id}", response_model=ArticoloResponse)
async def leggi_articolo(articolo_id: int):
    """Restituisce un singolo articolo per ID."""
    if articolo_id not in articoli_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Articolo con ID {articolo_id} non trovato"
        )
    return articoli_db[articolo_id]

@app.put("/articoli/{articolo_id}", response_model=ArticoloResponse)
async def aggiorna_articolo(articolo_id: int, articolo: ArticoloCreate):
    """Aggiorna un articolo esistente."""
    if articolo_id not in articoli_db:
        raise HTTPException(status_code=404, detail="Articolo non trovato")
    articoli_db[articolo_id].update(articolo.model_dump())
    return articoli_db[articolo_id]

@app.delete("/articoli/{articolo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def elimina_articolo(articolo_id: int):
    """Elimina un articolo."""
    if articolo_id not in articoli_db:
        raise HTTPException(status_code=404, detail="Articolo non trovato")
    del articoli_db[articolo_id]
```

#### Path Parameters e Query Parameters

FastAPI distingue automaticamente tra parametri del path e parametri di query in base alla firma della funzione.

```python
from fastapi import FastAPI, Query, Path
from enum import Enum

app = FastAPI()

class OrdinamentoArticolo(str, Enum):
    data = "data"
    titolo = "titolo"
    popolarita = "popolarita"

@app.get("/articoli/{categoria}")
async def cerca_articoli(
    # Path parameter con validazione
    categoria: str = Path(
        ...,
        min_length=2,
        max_length=50,
        description="Categoria dell'articolo"
    ),
    # Query parameters con valori di default e validazione
    q: str | None = Query(
        None,
        min_length=3,
        max_length=100,
        description="Termine di ricerca"
    ),
    ordina_per: OrdinamentoArticolo = OrdinamentoArticolo.data,
    pagina: int = Query(1, ge=1, description="Numero di pagina"),
    per_pagina: int = Query(20, ge=1, le=100, description="Risultati per pagina")
):
    """Cerca articoli per categoria con filtri e paginazione."""
    return {
        "categoria": categoria,
        "ricerca": q,
        "ordinamento": ordina_per,
        "pagina": pagina,
        "per_pagina": per_pagina
    }
```

#### Documentazione OpenAPI Automatica

Uno dei punti di forza piu apprezzati di FastAPI e la generazione automatica della documentazione interattiva. Non e necessaria alcuna configurazione aggiuntiva: basta avviare l'applicazione e navigare verso:

- **Swagger UI**: `http://localhost:8000/docs` — interfaccia interattiva per testare le API direttamente dal browser.
- **ReDoc**: `http://localhost:8000/redoc` — documentazione in formato leggibile e navigabile.

FastAPI genera lo schema OpenAPI a partire dai type hint, dai modelli Pydantic e dalle docstring delle funzioni. Ogni parametro, corpo della richiesta e modello di risposta viene documentato automaticamente.

### Funzionalita Avanzate

#### Dependency Injection System

Il sistema di dependency injection di FastAPI e uno dei suoi meccanismi piu potenti. Permette di iniettare dipendenze nelle path operation function in modo dichiarativo.

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

app = FastAPI()

# Dipendenza per la sessione del database
async def get_db() -> AsyncSession:
    async with async_session_maker() as sessione:
        try:
            yield sessione
        finally:
            await sessione.close()

# Dipendenza per l'autenticazione
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_utente_corrente(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Utente:
    credenziali_eccezione = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token non valido",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        utente_id: int = payload.get("sub")
        if utente_id is None:
            raise credenziali_eccezione
    except JWTError:
        raise credenziali_eccezione

    utente = await db.get(Utente, utente_id)
    if utente is None:
        raise credenziali_eccezione
    return utente

# Dipendenza per verificare i ruoli
def richiedi_ruolo(ruolo_richiesto: str):
    async def verificatore(
        utente: Annotated[Utente, Depends(get_utente_corrente)]
    ) -> Utente:
        if utente.ruolo != ruolo_richiesto:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permessi insufficienti"
            )
        return utente
    return verificatore

# Utilizzo nelle route
@app.get("/admin/utenti")
async def lista_utenti_admin(
    utente: Annotated[Utente, Depends(richiedi_ruolo("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    risultato = await db.execute(select(Utente))
    return risultato.scalars().all()
```

#### Background Tasks

FastAPI fornisce un meccanismo semplice per eseguire attivita in background dopo l'invio della risposta al client.

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

async def invia_email_notifica(email: str, messaggio: str):
    """Funzione eseguita in background dopo la risposta."""
    # Simula l'invio di una email
    import asyncio
    await asyncio.sleep(2)
    print(f"Email inviata a {email}: {messaggio}")

async def scrivi_log(operazione: str, dettagli: str):
    """Scrittura log in background."""
    with open("operazioni.log", "a") as f:
        f.write(f"{datetime.now()} | {operazione} | {dettagli}\n")

@app.post("/utenti/registrazione")
async def registra_utente(utente: UtenteCreate, background_tasks: BackgroundTasks):
    # Crea l'utente nel database
    nuovo_utente = await crea_utente_db(utente)

    # Aggiunge attivita in background (eseguite dopo la risposta)
    background_tasks.add_task(
        invia_email_notifica, utente.email, "Benvenuto nella piattaforma!"
    )
    background_tasks.add_task(
        scrivi_log, "REGISTRAZIONE", f"Nuovo utente: {utente.email}"
    )

    return {"messaggio": "Registrazione completata", "id": nuovo_utente.id}
```

#### Static Files e Lifespan Events

FastAPI puo servire file statici (CSS, JavaScript, immagini) direttamente, sebbene in produzione sia preferibile delegare questa responsabilita a Nginx o a un CDN.

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Montare una directory di file statici
app.mount("/static", StaticFiles(directory="static"), name="static")

# Servire un file specifico (ad esempio, favicon)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")
```

I lifespan events permettono di eseguire codice all'avvio e allo spegnimento dell'applicazione, ideali per inizializzare connessioni al database, caricare modelli di machine learning o configurare pool di connessioni.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Simulazione di un cache o pool di risorse
risorse_condivise = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Codice di startup: eseguito prima di accettare richieste
    print("Inizializzazione risorse...")
    risorse_condivise["pool_db"] = await crea_pool_database()
    risorse_condivise["modello_ml"] = carica_modello_predittivo()
    risorse_condivise["cache_redis"] = await connetti_redis()
    yield
    # Codice di shutdown: eseguito alla chiusura dell'applicazione
    print("Rilascio risorse...")
    await risorse_condivise["pool_db"].close()
    await risorse_condivise["cache_redis"].close()

app = FastAPI(lifespan=lifespan)
```

#### Middleware e CORS

I middleware intercettano ogni richiesta prima che raggiunga la route e ogni risposta prima che venga inviata al client. Sono utili per logging, autenticazione, compressione e manipolazione degli header.

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://miosito.it", "https://app.miosito.it"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Middleware personalizzato per il logging
@app.middleware("http")
async def middleware_tempo_risposta(request: Request, call_next):
    inizio = time.time()
    response = await call_next(request)
    durata = time.time() - inizio
    response.headers["X-Tempo-Processo"] = f"{durata:.4f}"
    print(f"{request.method} {request.url.path} - {response.status_code} - {durata:.4f}s")
    return response
```

#### WebSocket Support

FastAPI supporta nativamente i WebSocket per la comunicazione bidirezionale in tempo reale.

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import list

app = FastAPI()

class GestoreConnessioni:
    def __init__(self):
        self.connessioni_attive: list[WebSocket] = []

    async def connetti(self, websocket: WebSocket):
        await websocket.accept()
        self.connessioni_attive.append(websocket)

    def disconnetti(self, websocket: WebSocket):
        self.connessioni_attive.remove(websocket)

    async def broadcast(self, messaggio: str):
        for connessione in self.connessioni_attive:
            await connessione.send_text(messaggio)

gestore = GestoreConnessioni()

@app.websocket("/ws/chat/{stanza}")
async def endpoint_chat(websocket: WebSocket, stanza: str):
    await gestore.connetti(websocket)
    try:
        while True:
            dati = await websocket.receive_text()
            await gestore.broadcast(f"[{stanza}] {dati}")
    except WebSocketDisconnect:
        gestore.disconnetti(websocket)
        await gestore.broadcast(f"Un utente ha lasciato la stanza {stanza}")
```

### Validazione e Serializzazione

#### Integrazione con Pydantic

Pydantic e il cuore del sistema di validazione di FastAPI. Ogni modello definisce la struttura dei dati attesi e le regole di validazione.

```python
from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr
from typing import Optional
from datetime import datetime

class IndirizzoSchema(BaseModel):
    via: str = Field(..., min_length=5, max_length=200)
    citta: str = Field(..., min_length=2, max_length=100)
    cap: str = Field(..., pattern=r'^\d{5}$')
    provincia: str = Field(..., min_length=2, max_length=2)

class UtenteCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100, examples=["Mario Rossi"])
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    conferma_password: str
    eta: int = Field(..., ge=18, le=120)
    indirizzo: Optional[IndirizzoSchema] = None
    interessi: list[str] = Field(default_factory=list, max_length=10)

    @field_validator('nome')
    @classmethod
    def valida_nome(cls, v: str) -> str:
        if not v.replace(' ', '').isalpha():
            raise ValueError('Il nome deve contenere solo lettere e spazi')
        return v.title()

    @field_validator('password')
    @classmethod
    def valida_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('La password deve contenere almeno una maiuscola')
        if not any(c.isdigit() for c in v):
            raise ValueError('La password deve contenere almeno un numero')
        if not any(c in '!@#$%^&*()' for c in v):
            raise ValueError('La password deve contenere almeno un carattere speciale')
        return v

    @model_validator(mode='after')
    def verifica_password_corrispondenti(self):
        if self.password != self.conferma_password:
            raise ValueError('Le password non corrispondono')
        return self

class UtenteResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    eta: int
    indirizzo: Optional[IndirizzoSchema] = None
    data_registrazione: datetime

    model_config = {"from_attributes": True}

# Response model con status code
@app.post(
    "/utenti",
    response_model=UtenteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Email gia registrata"},
        422: {"description": "Errore di validazione"}
    }
)
async def crea_utente(utente: UtenteCreate):
    # La validazione e gia stata eseguita automaticamente da Pydantic
    # Se i dati non sono validi, FastAPI restituisce automaticamente un 422
    return await salva_utente_db(utente)
```

### Autenticazione

#### OAuth2 con Password Bearer e JWT

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Annotated

SECRET_KEY = "la-tua-chiave-segreta-molto-lunga-e-casuale"
ALGORITHM = "HS256"
SCADENZA_ACCESS_TOKEN = 30  # minuti

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

app = FastAPI()

class Token(BaseModel):
    access_token: str
    token_type: str

class DatiToken(BaseModel):
    sub: int | None = None
    ruolo: str | None = None

def crea_access_token(dati: dict, scadenza: timedelta | None = None) -> str:
    da_codificare = dati.copy()
    scade = datetime.utcnow() + (scadenza or timedelta(minutes=SCADENZA_ACCESS_TOKEN))
    da_codificare.update({"exp": scade})
    return jwt.encode(da_codificare, SECRET_KEY, algorithm=ALGORITHM)

async def get_utente_corrente(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> Utente:
    eccezione = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossibile validare le credenziali",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        utente_id: int = payload.get("sub")
        if utente_id is None:
            raise eccezione
    except JWTError:
        raise eccezione
    utente = await get_utente_per_id(utente_id)
    if utente is None:
        raise eccezione
    return utente

@app.post("/auth/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    utente = await autentica_utente(form_data.username, form_data.password)
    if not utente:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corretti",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = crea_access_token(
        dati={"sub": utente.id, "ruolo": utente.ruolo}
    )
    return Token(access_token=access_token, token_type="bearer")

# API Key Authentication alternativo
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verifica_api_key(
    api_key: Annotated[str, Depends(api_key_header)]
) -> str:
    if api_key not in API_KEYS_VALIDE:
        raise HTTPException(status_code=403, detail="API Key non valida")
    return api_key

@app.get("/dati-esterni")
async def dati_esterni(api_key: Annotated[str, Depends(verifica_api_key)]):
    return {"dati": "contenuto protetto da API Key"}
```

### Database Integration

#### SQLAlchemy Async con FastAPI

```python
# database.py — Configurazione del database asincrono
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://utente:password@localhost:5432/mio_db"

engine = create_async_engine(DATABASE_URL, echo=True, pool_size=20, max_overflow=10)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# Dipendenza per ottenere la sessione
async def get_db():
    async with async_session_maker() as sessione:
        try:
            yield sessione
            await sessione.commit()
        except Exception:
            await sessione.rollback()
            raise
        finally:
            await sessione.close()


# models.py — Definizione dei modelli
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

class Utente(Base):
    __tablename__ = "utenti"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(100))
    hash_password: Mapped[str] = mapped_column(String(255))
    attivo: Mapped[bool] = mapped_column(default=True)
    data_creazione: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    articoli: Mapped[list["Articolo"]] = relationship(back_populates="autore")

class Articolo(Base):
    __tablename__ = "articoli"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    titolo: Mapped[str] = mapped_column(String(200))
    contenuto: Mapped[str] = mapped_column(String)
    autore_id: Mapped[int] = mapped_column(ForeignKey("utenti.id"))
    data_creazione: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    autore: Mapped["Utente"] = relationship(back_populates="articoli")


# crud.py — Pattern CRUD riutilizzabile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class CRUDBase:
    def __init__(self, modello):
        self.modello = modello

    async def get(self, db: AsyncSession, id: int):
        risultato = await db.execute(
            select(self.modello).where(self.modello.id == id)
        )
        return risultato.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100):
        risultato = await db.execute(
            select(self.modello).offset(skip).limit(limit)
        )
        return risultato.scalars().all()

    async def create(self, db: AsyncSession, dati: dict):
        oggetto = self.modello(**dati)
        db.add(oggetto)
        await db.flush()
        await db.refresh(oggetto)
        return oggetto

    async def update(self, db: AsyncSession, id: int, dati: dict):
        oggetto = await self.get(db, id)
        if oggetto:
            for chiave, valore in dati.items():
                setattr(oggetto, chiave, valore)
            await db.flush()
            await db.refresh(oggetto)
        return oggetto

    async def delete(self, db: AsyncSession, id: int) -> bool:
        oggetto = await self.get(db, id)
        if oggetto:
            await db.delete(oggetto)
            await db.flush()
            return True
        return False

crud_utenti = CRUDBase(Utente)
crud_articoli = CRUDBase(Articolo)


# routes con integrazione completa
from fastapi import APIRouter, Depends
from typing import Annotated

router = APIRouter(prefix="/api/v1", tags=["utenti"])

@router.get("/utenti/{utente_id}", response_model=UtenteResponse)
async def leggi_utente(
    utente_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    utente = await crud_utenti.get(db, utente_id)
    if not utente:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return utente
```

#### Alembic per le Migrazioni

```bash
# Inizializzazione di Alembic
alembic init alembic

# Configurazione env.py per il supporto asincrono
# Creazione di una migrazione
alembic revision --autogenerate -m "creazione tabelle utenti e articoli"

# Applicazione delle migrazioni
alembic upgrade head

# Rollback dell'ultima migrazione
alembic downgrade -1
```

---

## FastAPI Lifespan — Approfondimento

> **Fonte:** FastAPI Lifespan Events — https://fastapi.tiangolo.com/advanced/events/
> **Fonte:** Starlette Lifespan — https://www.starlette.io/lifespan/

### Perche il lifespan sostituisce on_startup e on_shutdown

I decoratori `@app.on_event("startup")` e `@app.on_event("shutdown")` erano il meccanismo originale di FastAPI per eseguire codice all'avvio e alla chiusura dell'applicazione. Sono stati deprecati a partire da FastAPI 0.93+ per diverse ragioni:

1. **Nessuna condivisione di stato garantita** — con `on_startup`/`on_shutdown` la risorsa creata in startup doveva essere memorizzata in una variabile globale, senza garanzia che lo shutdown accedesse alla stessa istanza.
2. **Nessun legame strutturale** — startup e shutdown erano funzioni indipendenti; un errore nello shutdown poteva non corrispondere alla risorsa inizializzata.
3. **Il context manager risolve entrambi** — il pattern `asynccontextmanager` lega strutturalmente la creazione e la distruzione della risorsa.

```python
# DEPRECATO — non usare in codice nuovo
@app.on_event("startup")
async def startup():
    app.state.db = await create_pool()

@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()

# CORRETTO — lifespan con context manager
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tutto cio che precede yield e startup
    pool = await create_pool()
    app.state.db = pool
    yield
    # Tutto cio che segue yield e shutdown
    await pool.close()

app = FastAPI(lifespan=lifespan)
```

### Pattern avanzati con lifespan

#### Lifespan con risorse multiple e gestione errori

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inizializzazione ordinata delle risorse
    logger.info("Inizializzazione pool database...")
    pool_db = await asyncpg.create_pool(
        dsn="postgresql://utente:password@localhost/db",
        min_size=5,
        max_size=20,
    )
    app.state.db = pool_db

    logger.info("Connessione a Redis...")
    redis = await aioredis.from_url("redis://localhost:6379/0")
    app.state.redis = redis

    logger.info("Caricamento modello ML...")
    modello = await caricare_modello("modelli/predittore_v3.onnx")
    app.state.modello_ml = modello

    logger.info("Tutte le risorse inizializzate. Pronto per le richieste.")

    try:
        yield
    finally:
        # Shutdown ordinato — in ordine inverso rispetto alla creazione
        logger.info("Shutdown: rilascio risorse...")
        await redis.close()
        await pool_db.close()
        logger.info("Shutdown completato.")

app = FastAPI(lifespan=lifespan)

# Accesso alle risorse nelle route tramite request.app.state
@app.get("/predizioni/{item_id}")
async def predici(item_id: int, request: Request):
    modello = request.app.state.modello_ml
    db = request.app.state.db
    async with db.acquire() as conn:
        dati = await conn.fetchrow("SELECT * FROM items WHERE id = $1", item_id)
    risultato = modello.predict(dati)
    return {"predizione": risultato}
```

#### Lifespan con dependency injection (yield dependencies)

Le dipendenze con `yield` in FastAPI seguono lo stesso pattern del lifespan ma a livello di singola richiesta. La combinazione dei due livelli crea una gerarchia pulita di gestione delle risorse.

```python
from fastapi import FastAPI, Depends, Request
from typing import Annotated, AsyncGenerator
from contextlib import asynccontextmanager

# Livello 1: lifespan — risorse globali (pool, cache, modelli)
@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await asyncpg.create_pool(dsn="postgresql://...")
    app.state.pool = pool
    yield
    await pool.close()

app = FastAPI(lifespan=lifespan)

# Livello 2: dipendenza con yield — risorse per-request (connessione, transazione)
async def get_connessione(request: Request) -> AsyncGenerator:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        # La connessione e disponibile per la durata della richiesta
        yield conn
        # Dopo yield: la connessione viene rilasciata al pool

# Livello 3: dipendenza con yield + transazione
async def get_transazione(
    conn: Annotated[asyncpg.Connection, Depends(get_connessione)]
) -> AsyncGenerator:
    async with conn.transaction():
        yield conn
        # Se la route alza un'eccezione, la transazione fa rollback automatico

@app.post("/ordini")
async def crea_ordine(
    ordine: OrdineCreate,
    conn: Annotated[asyncpg.Connection, Depends(get_transazione)]
):
    # Tutto all'interno di una transazione database
    ordine_id = await conn.fetchval(
        "INSERT INTO ordini (prodotto, quantita) VALUES ($1, $2) RETURNING id",
        ordine.prodotto, ordine.quantita
    )
    await conn.execute(
        "UPDATE inventario SET disponibilita = disponibilita - $1 WHERE prodotto = $2",
        ordine.quantita, ordine.prodotto
    )
    return {"id": ordine_id}
```

#### Lifespan per test — override

```python
# test_app.py
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import pytest

@asynccontextmanager
async def lifespan_test(app: FastAPI):
    """Lifespan per i test: database in-memory, mock dei servizi."""
    app.state.db = await asyncpg.create_pool(dsn="postgresql://localhost/test_db")
    app.state.redis = FakeRedis()
    app.state.modello_ml = MockModello()
    yield
    await app.state.db.close()

@pytest.fixture
def app_test():
    from app.main import create_app
    app = create_app()
    app.router.lifespan_context = lifespan_test
    return app

@pytest.fixture
async def client(app_test):
    transport = ASGITransport(app=app_test)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

---

## Django (Panoramica)

Django e il framework full-stack piu maturo e completo dell'ecosistema Python, creato nel 2005. Segue il principio "batteries included" e il pattern MTV (Model-Template-View), una variante del classico MVC.

### Fondamenti

#### Struttura del Progetto

```
mio_progetto/
    manage.py                  # Utility per i comandi di gestione
    mio_progetto/
        __init__.py
        settings.py            # Configurazione globale
        urls.py                # URL routing principale
        wsgi.py                # Entry point WSGI
        asgi.py                # Entry point ASGI
    blog/                      # App Django
        __init__.py
        admin.py               # Configurazione pannello admin
        apps.py                # Configurazione dell'app
        models.py              # Modelli del database
        views.py               # Logica delle view
        urls.py                # URL routing dell'app
        serializers.py         # Serializzatori (per DRF)
        templates/
            blog/
                lista.html
                dettaglio.html
        static/
            blog/
                css/
                js/
        tests/
            test_models.py
            test_views.py
        migrations/
            0001_initial.py
```

#### Modelli e ORM

L'ORM di Django e uno dei piu potenti e intuitivi disponibili. Permette di definire la struttura del database interamente in Python.

```python
# blog/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    descrizione = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categorie"
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

class Articolo(models.Model):
    class Stato(models.TextChoices):
        BOZZA = 'BO', 'Bozza'
        PUBBLICATO = 'PU', 'Pubblicato'
        ARCHIVIATO = 'AR', 'Archiviato'

    titolo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    autore = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articoli')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    contenuto = models.TextField()
    stato = models.CharField(max_length=2, choices=Stato.choices, default=Stato.BOZZA)
    data_creazione = models.DateTimeField(auto_now_add=True)
    data_modifica = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_creazione']
        verbose_name_plural = "Articoli"

    def __str__(self):
        return self.titolo

# Esempi di query ORM
# articoli = Articolo.objects.filter(stato='PU', categoria__nome='Python')
# articoli = Articolo.objects.select_related('autore', 'categoria').all()
# conteggio = Articolo.objects.filter(autore__username='mario').count()
```

#### View e URL

```python
# blog/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Articolo

# View basata su funzione
def lista_articoli(request):
    articoli = Articolo.objects.filter(stato='PU').select_related('autore')
    return render(request, 'blog/lista.html', {'articoli': articoli})

# View basata su classe (CBV) — approccio consigliato
class ArticoloListView(ListView):
    model = Articolo
    template_name = 'blog/lista.html'
    context_object_name = 'articoli'
    paginate_by = 10

    def get_queryset(self):
        return Articolo.objects.filter(stato='PU').select_related('autore', 'categoria')

class ArticoloDetailView(DetailView):
    model = Articolo
    template_name = 'blog/dettaglio.html'
    slug_url_kwarg = 'slug'

class ArticoloCreateView(LoginRequiredMixin, CreateView):
    model = Articolo
    fields = ['titolo', 'contenuto', 'categoria']
    template_name = 'blog/crea.html'

    def form_valid(self, form):
        form.instance.autore = self.request.user
        return super().form_valid(form)


# blog/urls.py
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.ArticoloListView.as_view(), name='lista'),
    path('<slug:slug>/', views.ArticoloDetailView.as_view(), name='dettaglio'),
    path('nuovo/', views.ArticoloCreateView.as_view(), name='crea'),
]
```

#### Pannello di Amministrazione

Il pannello admin di Django e una delle sue funzionalita piu apprezzate. Genera automaticamente un'interfaccia CRUD per i modelli.

```python
# blog/admin.py
from django.contrib import admin
from .models import Articolo, Categoria

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug']
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(Articolo)
class ArticoloAdmin(admin.ModelAdmin):
    list_display = ['titolo', 'autore', 'categoria', 'stato', 'data_creazione']
    list_filter = ['stato', 'categoria', 'data_creazione']
    search_fields = ['titolo', 'contenuto']
    prepopulated_fields = {'slug': ('titolo',)}
    raw_id_fields = ['autore']
    date_hierarchy = 'data_creazione'
    list_editable = ['stato']
```

### Funzionalita Chiave

#### Django REST Framework (DRF)

DRF e l'estensione di riferimento per costruire API RESTful con Django. Fornisce serializzatori, viewset, router, autenticazione e permessi.

```python
# blog/serializers.py
from rest_framework import serializers
from .models import Articolo, Categoria

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome', 'slug', 'descrizione']

class ArticoloSerializer(serializers.ModelSerializer):
    autore_nome = serializers.CharField(source='autore.get_full_name', read_only=True)
    categoria = CategoriaSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source='categoria', write_only=True
    )

    class Meta:
        model = Articolo
        fields = ['id', 'titolo', 'slug', 'autore_nome', 'categoria',
                  'categoria_id', 'contenuto', 'stato', 'data_creazione']
        read_only_fields = ['slug', 'data_creazione']


# blog/views_api.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

class ArticoloViewSet(viewsets.ModelViewSet):
    queryset = Articolo.objects.select_related('autore', 'categoria')
    serializer_class = ArticoloSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['stato', 'categoria']
    search_fields = ['titolo', 'contenuto']
    ordering_fields = ['data_creazione', 'titolo']

    def perform_create(self, serializer):
        serializer.save(autore=self.request.user)

    @action(detail=False, methods=['get'])
    def pubblicati(self, request):
        pubblicati = self.queryset.filter(stato='PU')
        serializer = self.get_serializer(pubblicati, many=True)
        return Response(serializer.data)


# blog/urls.py (con router DRF)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'articoli', ArticoloViewSet)
# Genera automaticamente: GET/POST /articoli/, GET/PUT/DELETE /articoli/{id}/
```

#### Middleware in Django

Django utilizza un sistema di middleware basato su classi, configurato nell'impostazione `MIDDLEWARE` del file `settings.py`. Ogni middleware riceve la richiesta in ordine dall'alto verso il basso e la risposta in ordine inverso.

```python
# mio_progetto/middleware.py
import time
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class TimingMiddleware:
    """Middleware che misura il tempo di elaborazione di ogni richiesta."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inizio = time.time()
        response = self.get_response(request)
        durata = time.time() - inizio
        response['X-Tempo-Processo'] = f'{durata:.4f}s'
        if durata > 1.0:
            logger.warning(f'Richiesta lenta: {request.method} {request.path} ({durata:.2f}s)')
        return response

class ForceJsonResponseMiddleware:
    """Forza risposte JSON per tutte le route API."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if request.path.startswith('/api/'):
            return JsonResponse(
                {'errore': str(exception)},
                status=500
            )
```

```python
# settings.py — Ordine dei middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'mio_progetto.middleware.TimingMiddleware',
    'mio_progetto.middleware.ForceJsonResponseMiddleware',
]
```

#### Signals e Celery

I signals di Django implementano il pattern Observer, permettendo a componenti disaccoppiati di reagire ad eventi specifici come il salvataggio di un modello, la creazione di un utente o l'arrivo di una richiesta HTTP.

```python
# Signals — notifiche tra componenti dell'applicazione
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Articolo

@receiver(post_save, sender=Articolo)
def dopo_salvataggio_articolo(sender, instance, created, **kwargs):
    if created:
        invia_notifica_nuovo_articolo.delay(instance.id)

# Integrazione Celery per task asincroni
# blog/tasks.py
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def invia_notifica_nuovo_articolo(articolo_id):
    articolo = Articolo.objects.get(id=articolo_id)
    iscritti = Utente.objects.filter(iscritto_newsletter=True)
    for utente in iscritti:
        send_mail(
            subject=f'Nuovo articolo: {articolo.titolo}',
            message=f'Leggi il nuovo articolo sul nostro blog: {articolo.titolo}',
            from_email='noreply@miosito.it',
            recipient_list=[utente.email]
        )
```

---

## Confronto Framework

La scelta del framework dipende dalle esigenze specifiche del progetto. La seguente tabella riassume le differenze principali:

| Caratteristica       | Flask                     | FastAPI                    | Django                       |
|----------------------|---------------------------|----------------------------|------------------------------|
| **Tipo**             | Microframework            | Microframework             | Full-stack                   |
| **Performance**      | Buone                     | Eccellenti                 | Buone                        |
| **Curva di apprendimento** | Bassa               | Media                      | Media-Alta                   |
| **Supporto Async**   | Limitato (Flask 2.0+)    | Nativo                     | Parziale (Django 4.1+)       |
| **ORM integrato**    | No (Flask-SQLAlchemy)     | No (SQLAlchemy)            | Si (Django ORM)              |
| **Admin Panel**       | No                       | No                         | Si (built-in)                |
| **Documentazione API**| Manuale (flask-smorest)  | Automatica (OpenAPI)       | DRF (semi-automatica)        |
| **Ecosistema**        | Ampio (estensioni)       | In crescita                | Molto ampio                  |
| **Validazione dati**  | Marshmallow              | Pydantic (integrato)       | Forms / DRF Serializers      |
| **WebSocket**         | Flask-SocketIO           | Nativo                     | Django Channels              |
| **Caso d'uso ideale** | Microservizi, API semplici, prototipazione | API ad alte prestazioni, microservizi, ML serving | Applicazioni web complete, CMS, e-commerce |

**Flask** e la scelta ideale quando si desidera massima flessibilita e controllo sulla struttura del progetto. E perfetto per microservizi, API semplici e prototipi rapidi. La curva di apprendimento e la piu bassa tra i tre framework, il che lo rende un eccellente punto di partenza per chi si avvicina allo sviluppo web con Python. Tuttavia, per progetti di grandi dimensioni, la mancanza di struttura imposta puo portare a codice disorganizzato se non si adottano convenzioni disciplinate fin dall'inizio.

**FastAPI** eccelle nella costruzione di API ad alte prestazioni. Il supporto asincrono nativo, la validazione automatica tramite Pydantic e la documentazione OpenAPI generata automaticamente lo rendono la scelta migliore per API moderne, microservizi e applicazioni che richiedono alta concorrenza. I benchmark dimostrano prestazioni paragonabili a framework Node.js e Go, grazie all'architettura asincrona basata su Starlette. E particolarmente adatto per servire modelli di machine learning, costruire gateway API e realizzare applicazioni in tempo reale con WebSocket.

**Django** e la scelta obbligata per applicazioni web complete che necessitano di un pannello di amministrazione, autenticazione utente, gestione dei contenuti e un ORM maturo. E il framework preferito per CMS, piattaforme e-commerce e applicazioni enterprise. Il suo ecosistema e il piu vasto tra i tre, con migliaia di pacchetti di terze parti disponibili su PyPI. La comunita e molto attiva e la documentazione e considerata tra le migliori nel panorama dei framework web in qualsiasi linguaggio.

Un approccio sempre piu comune nei team di sviluppo consiste nell'utilizzare Django per il backend amministrativo e il rendering lato server, affiancandolo a FastAPI per le API ad alte prestazioni destinate ai client mobile e alle single-page application (SPA).

---

## Testing Cross-Framework

### Strategie di Test per ogni Framework

```python
# Il testing e` fondamentale per qualsiasi applicazione web.
# Ogni framework offre un test client integrato con API diverse
# ma concetti simili. Di seguito i pattern principali per ciascuno.

# ── Flask: Testing con pytest e client fixture ──
import pytest
from myapp import create_app

@pytest.fixture
def app():
    """Crea un'istanza dell'app configurata per il testing."""
    app = create_app({
        "TESTING": True,
        "DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-only-for-tests",
    })
    with app.app_context():
        # Inizializzare il database di test
        from myapp.db import init_db
        init_db()
        yield app

@pytest.fixture
def client(app):
    """Client HTTP per le richieste di test."""
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Client autenticato con token JWT."""
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    token = response.get_json()["access_token"]
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client

def test_create_item(auth_client):
    """Test creazione risorsa con autenticazione."""
    response = auth_client.post("/api/items", json={
        "name": "Test Item",
        "price": 29.99
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Test Item"
    assert data["id"] is not None

def test_create_item_unauthorized(client):
    """Test che richieste senza token vengano rifiutate."""
    response = client.post("/api/items", json={"name": "Test"})
    assert response.status_code == 401

def test_validation_error(auth_client):
    """Test validazione input con dati mancanti."""
    response = auth_client.post("/api/items", json={})
    assert response.status_code == 400
    errors = response.get_json()["errors"]
    assert "name" in errors
```

```python
# ── FastAPI: Testing con TestClient (basato su httpx) ──
from fastapi.testclient import TestClient
from myapp.main import app
from myapp.dependencies import get_db
from myapp.database import create_test_engine
import pytest

# Override delle dipendenze per il testing
@pytest.fixture
def db_session():
    engine = create_test_engine()
    # Creare le tabelle nel DB di test
    from myapp.models import Base
    Base.metadata.create_all(engine)
    from sqlalchemy.orm import Session
    session = Session(engine)
    yield session
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_list_items(client):
    """Test endpoint lista con paginazione."""
    response = client.get("/api/v1/items?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 0

def test_openapi_schema(client):
    """Verificare che lo schema OpenAPI sia generato correttamente."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/items" in schema["paths"]

# Test asincroni con pytest-asyncio (per endpoint async)
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.anyio
async def test_async_endpoint(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

```python
# ── Django: Testing con django.test e pytest-django ──
# Django ha il sistema di testing piu` completo dei tre framework,
# con supporto integrato per fixture, database transazionali e LiveServerTestCase.

# conftest.py
import pytest

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, django_user_model):
    user = django_user_model.objects.create_user(
        username="testuser",
        password="testpass123",
        email="test@example.com"
    )
    api_client.force_authenticate(user=user)
    return api_client

# test_views.py
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_create_item(authenticated_client):
    url = reverse("item-list")
    response = authenticated_client.post(url, {
        "name": "Django Test Item",
        "price": "49.99",
        "category": "electronics"
    }, format="json")
    assert response.status_code == 201
    assert response.data["name"] == "Django Test Item"

@pytest.mark.django_db
def test_item_permissions(api_client):
    """Utente non autenticato non puo` creare items."""
    url = reverse("item-list")
    response = api_client.post(url, {"name": "Test"}, format="json")
    assert response.status_code in (401, 403)

@pytest.mark.django_db
class TestItemFilters:
    """Test per i filtri della lista items."""

    def test_filter_by_category(self, authenticated_client):
        url = reverse("item-list")
        response = authenticated_client.get(url, {"category": "electronics"})
        assert response.status_code == 200
        for item in response.data["results"]:
            assert item["category"] == "electronics"

    def test_search(self, authenticated_client):
        url = reverse("item-list")
        response = authenticated_client.get(url, {"search": "laptop"})
        assert response.status_code == 200
```

### Pattern di Test Comuni

```python
# ── Fixture Factory Pattern (riutilizzabile tra framework) ──
# Centralizzare la creazione di dati di test con factory functions

import factory
from myapp.models import User, Item

class UserFactory(factory.Factory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    is_active = True

class ItemFactory(factory.Factory):
    class Meta:
        model = Item
    name = factory.Faker("product_name", locale="it_IT")
    price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    owner = factory.SubFactory(UserFactory)

# Utilizzo nei test:
# item = ItemFactory(name="Prodotto Custom", price=99.99)

# ── Test di Performance / Load (applicabile a tutti i framework) ──
# Usare locust per load testing:
# pip install locust

# locustfile.py:
from locust import HttpUser, task, between

class WebAppUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        response = self.client.post("/auth/login", json={
            "username": "loadtest",
            "password": "testpass123"
        })
        self.token = response.json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {self.token}"

    @task(3)
    def list_items(self):
        self.client.get("/api/v1/items?page=1&size=20")

    @task(1)
    def create_item(self):
        self.client.post("/api/v1/items", json={
            "name": "Load Test Item",
            "price": 19.99
        })

# Eseguire: locust -f locustfile.py --host=http://localhost:8000
# Dashboard web su http://localhost:8089
```

---

## ASGI — Approfondimento

> **Fonte:** ASGI Spec — https://asgi.readthedocs.io/en/latest/
> **Fonte:** Starlette Documentation — https://www.starlette.io/

### Starlette — Il cuore di FastAPI

FastAPI e costruito su Starlette, che a sua volta implementa la specifica ASGI. Comprendere Starlette significa comprendere cosa accade sotto il cofano di FastAPI.

Starlette fornisce:
- Routing HTTP e WebSocket
- Middleware stack (basato su classi ASGI)
- Gestione sessioni e cookie
- Template con Jinja2
- File statici
- Test client integrato

```python
# Applicazione Starlette pura (senza FastAPI)
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

async def homepage(request):
    return JSONResponse({"messaggio": "Ciao da Starlette"})

async def dettaglio_utente(request):
    uid = request.path_params['uid']
    return JSONResponse({"id": uid})

app = Starlette(
    routes=[
        Route('/', homepage),
        Route('/utenti/{uid:int}', dettaglio_utente),
    ]
)
```

### Lo stack middleware ASGI

In ASGI, ogni middleware e un'applicazione ASGI che wrappa un'altra applicazione ASGI. La catena di chiamate segue il pattern onion (cipolla): la richiesta attraversa i middleware dall'esterno verso l'interno, la risposta dall'interno verso l'esterno.

```python
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# L'ordine e importante: il primo middleware wrappa tutti gli altri
middleware = [
    # Layer esterno: sicurezza host
    Middleware(TrustedHostMiddleware, allowed_hosts=["miosito.it", "*.miosito.it"]),
    # Layer 2: compressione
    Middleware(GZipMiddleware, minimum_size=1000),
    # Layer 3: CORS
    Middleware(CORSMiddleware, allow_origins=["https://app.miosito.it"]),
]

app = Starlette(routes=[...], middleware=middleware)
```

### Protocollo Lifespan ASGI

Il protocollo lifespan e uno dei tre tipi di scope ASGI (`http`, `websocket`, `lifespan`). Il server ASGI invia eventi lifespan all'applicazione per segnalare l'avvio e l'arresto.

```python
# Implementazione raw del protocollo lifespan
async def app(scope, receive, send):
    if scope['type'] == 'lifespan':
        while True:
            messaggio = await receive()
            if messaggio['type'] == 'lifespan.startup':
                # Inizializza risorse
                try:
                    await inizializza_database()
                    await send({'type': 'lifespan.startup.complete'})
                except Exception:
                    await send({
                        'type': 'lifespan.startup.failed',
                        'message': 'Errore inizializzazione DB'
                    })
                    return
            elif messaggio['type'] == 'lifespan.shutdown':
                # Rilascia risorse
                await chiudi_database()
                await send({'type': 'lifespan.shutdown.complete'})
                return

    elif scope['type'] == 'http':
        # Gestisci richiesta HTTP
        await gestisci_http(scope, receive, send)

    elif scope['type'] == 'websocket':
        # Gestisci connessione WebSocket
        await gestisci_websocket(scope, receive, send)
```

### Protocollo WebSocket ASGI

La gestione WebSocket in ASGI segue un ciclo di vita ben definito: connessione, scambio messaggi, disconnessione.

```python
# Protocollo WebSocket a basso livello (scope type = 'websocket')
async def websocket_app(scope, receive, send):
    # scope contiene: path, headers, query_string, client
    while True:
        messaggio = await receive()

        if messaggio['type'] == 'websocket.connect':
            # Il client vuole connettersi — accetta o rifiuta
            await send({'type': 'websocket.accept'})

        elif messaggio['type'] == 'websocket.receive':
            # Messaggio ricevuto dal client
            testo = messaggio.get('text', '')
            bytes_data = messaggio.get('bytes', b'')

            # Echo: rimanda il messaggio
            await send({
                'type': 'websocket.send',
                'text': f'Echo: {testo}'
            })

        elif messaggio['type'] == 'websocket.disconnect':
            # Il client si e disconnesso
            break
```

---

## Pattern Middleware Cross-Framework

I middleware sono il meccanismo principale per implementare logica trasversale (cross-cutting concerns) senza inquinare le route. Questa sezione presenta pattern riutilizzabili indipendentemente dal framework.

### Middleware di Compressione

```python
# FastAPI — GZipMiddleware di Starlette
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=500)
# Comprime automaticamente risposte > 500 byte quando il client
# invia Accept-Encoding: gzip

# Flask — flask-compress
from flask_compress import Compress
compress = Compress()
compress.init_app(app)
app.config['COMPRESS_ALGORITHM'] = 'gzip'
app.config['COMPRESS_MIN_SIZE'] = 500
```

### Middleware Request ID

Inietta un identificatore unico per ogni richiesta, fondamentale per il tracing distribuito e la correlazione dei log.

```python
# FastAPI — middleware Request ID
import uuid
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Usa l'ID fornito dal client o ne genera uno nuovo
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        # Rendi disponibile a tutta la catena
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        return response

app.add_middleware(RequestIDMiddleware)
```

```python
# Flask — equivalente con before/after_request
import uuid
from flask import Flask, g, request

@app.before_request
def aggiungi_request_id():
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

@app.after_request
def propaga_request_id(response):
    response.headers['X-Request-ID'] = g.get('request_id', '')
    return response
```

### Middleware di Rate Limiting

```python
# FastAPI con slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/ricerca")
@limiter.limit("30/minute")
async def ricerca(request: Request, q: str):
    return {"risultati": await esegui_ricerca(q)}

# Flask con Flask-Limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200/day", "50/hour"]
)

@app.route("/api/ricerca")
@limiter.limit("30/minute")
def ricerca():
    return jsonify({"risultati": esegui_ricerca(request.args.get('q'))})
```

### Middleware di Autenticazione ASGI puro

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware che verifica il token JWT per tutte le route /api/."""

    PERCORSI_PUBBLICI = {"/health", "/docs", "/openapi.json", "/auth/login"}

    async def dispatch(self, request: Request, call_next):
        # Salta i percorsi pubblici
        if request.url.path in self.PERCORSI_PUBBLICI:
            return await call_next(request)

        # Verifica solo le route API
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"errore": "Token mancante o formato non valido"}
            )

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            request.state.utente_id = payload["sub"]
            request.state.ruolo = payload.get("ruolo", "utente")
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"errore": "Token non valido o scaduto"}
            )

        return await call_next(request)
```

### Middleware Trusted Host

```python
# FastAPI / Starlette
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["miosito.it", "*.miosito.it"]
)
# Blocca richieste con header Host non autorizzati
# Previene attacchi di host header injection
```

---

## Dependency Injection — Approfondimento

> **Fonte:** FastAPI Dependencies — https://fastapi.tiangolo.com/tutorial/dependencies/

### Sub-dipendenze (catena di dipendenze)

FastAPI risolve automaticamente l'albero delle dipendenze. Ogni dipendenza puo dipendere da altre dipendenze, formando una catena.

```python
from fastapi import Depends, Query
from typing import Annotated

# Dipendenza livello 1: parametri di paginazione
def parametri_paginazione(
    pagina: int = Query(1, ge=1),
    per_pagina: int = Query(20, ge=1, le=100)
) -> dict:
    return {"skip": (pagina - 1) * per_pagina, "limit": per_pagina}

# Dipendenza livello 2: filtri comuni (dipende da paginazione)
def parametri_filtro(
    paginazione: Annotated[dict, Depends(parametri_paginazione)],
    ordinamento: str = Query("data_creazione", regex=r'^[a-z_]+$'),
    direzione: str = Query("desc", regex=r'^(asc|desc)$'),
    q: str | None = Query(None, min_length=2)
) -> dict:
    return {
        **paginazione,
        "ordinamento": ordinamento,
        "direzione": direzione,
        "ricerca": q
    }

# Dipendenza livello 3: query builder (dipende da filtri e db)
async def query_articoli(
    filtri: Annotated[dict, Depends(parametri_filtro)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    query = select(Articolo)
    if filtri["ricerca"]:
        query = query.where(Articolo.titolo.ilike(f'%{filtri["ricerca"]}%'))
    query = query.order_by(
        getattr(Articolo, filtri["ordinamento"]).desc()
        if filtri["direzione"] == "desc"
        else getattr(Articolo, filtri["ordinamento"]).asc()
    )
    query = query.offset(filtri["skip"]).limit(filtri["limit"])
    risultato = await db.execute(query)
    return risultato.scalars().all()

# Nella route: una sola dipendenza nasconde l'intera catena
@app.get("/articoli")
async def lista_articoli(
    articoli: Annotated[list, Depends(query_articoli)]
):
    return articoli
```

### Override delle dipendenze per il testing

```python
# Override per i test — sostituire dipendenze reali con mock
from fastapi.testclient import TestClient

# Dipendenza reale
async def get_servizio_pagamento() -> ServizioPagamento:
    return ServizioPagamento(api_key=os.environ["STRIPE_KEY"])

# Dipendenza mock per i test
async def get_servizio_pagamento_mock() -> ServizioPagamento:
    return ServizioPagamentoFake()

# Override nel test
app.dependency_overrides[get_servizio_pagamento] = get_servizio_pagamento_mock

with TestClient(app) as client:
    risposta = client.post("/pagamenti", json={"importo": 100})
    assert risposta.status_code == 200

# Pulizia: rimuovere l'override dopo il test
app.dependency_overrides.clear()
```

```python
# Pattern consigliato con pytest fixtures
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.fixture
def override_dipendenze(app):
    app.dependency_overrides[get_db] = lambda: FakeDB()
    app.dependency_overrides[get_utente_corrente] = lambda: Utente(id=1, ruolo="admin")
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_crea_articolo(app, override_dipendenze):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        risposta = await client.post("/articoli", json={"titolo": "Test", "contenuto": "..."})
        assert risposta.status_code == 201
```

---

## Template Engine e Jinja2

> **Fonte:** Jinja2 Documentation — https://jinja.palletsprojects.com/en/stable/

### Sicurezza: Autoescape

Jinja2 in Flask ha l'autoescape abilitato per default sui file `.html`, `.htm`, `.xml`, `.xhtml`. Questo protegge automaticamente dall'XSS convertendo i caratteri speciali HTML in entita.

```python
# Configurazione autoescape in Flask (default gia sicuro per HTML)
app = Flask(__name__)
# app.jinja_env.autoescape e True per template .html

# In FastAPI con Jinja2Templates
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
# Autoescape abilitato per default

# Per disabilitare l'escape su contenuto fidato (usare con cautela)
# {{ contenuto_html_fidato | safe }}
# oppure
# {% autoescape false %}
#   {{ contenuto_html }}
# {% endautoescape %}
```

**Regola di sicurezza:** Non usare mai `| safe` o `{% autoescape false %}` su dati provenienti dall'utente. Sanitizzare sempre il contenuto HTML con una libreria come `bleach` o `nh3` prima di contrassegnarlo come sicuro.

```python
import nh3

# Sanitizzazione server-side prima del rendering
contenuto_pulito = nh3.clean(
    contenuto_utente,
    tags={"p", "b", "i", "a", "ul", "li", "br"},
    attributes={"a": {"href"}},
)
# Ora e sicuro usare {{ contenuto_pulito | safe }} nel template
```

### Ereditarieta dei Template

L'ereditarieta e il meccanismo piu potente di Jinja2 per evitare duplicazione.

```html
{# templates/base.html — template radice #}
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Il Mio Sito{% endblock %} | Brand</title>
    {% block head_extra %}{% endblock %}
</head>
<body>
    {% block navbar %}
    <nav>
        <a href="/">Home</a>
        <a href="/blog">Blog</a>
    </nav>
    {% endblock %}

    <main>
        {% block content %}{% endblock %}
    </main>

    {% block scripts %}{% endblock %}
</body>
</html>
```

```html
{# templates/blog/layout.html — template intermedio per la sezione blog #}
{% extends "base.html" %}

{% block navbar %}
    {{ super() }}  {# Mantiene il navbar del genitore #}
    <nav class="blog-nav">
        <a href="/blog/categorie">Categorie</a>
        <a href="/blog/archivio">Archivio</a>
    </nav>
{% endblock %}

{% block content %}
    <div class="blog-container">
        <article>{% block article %}{% endblock %}</article>
        <aside>{% block sidebar %}{% endblock %}</aside>
    </div>
{% endblock %}
```

```html
{# templates/blog/dettaglio.html — template foglia #}
{% extends "blog/layout.html" %}

{% block title %}{{ articolo.titolo }}{% endblock %}

{% block article %}
    <h1>{{ articolo.titolo }}</h1>
    <p class="meta">{{ articolo.data | dateformat }}</p>
    {{ articolo.contenuto }}
{% endblock %}

{% block sidebar %}
    <h3>Articoli correlati</h3>
    {% for correlato in correlati %}
        <a href="{{ url_for('blog.dettaglio', slug=correlato.slug) }}">
            {{ correlato.titolo }}
        </a>
    {% endfor %}
{% endblock %}
```

### Macro (componenti riutilizzabili)

Le macro sono l'equivalente Jinja2 delle funzioni: accettano parametri e restituiscono markup.

```html
{# templates/macro/form.html #}
{% macro campo_input(nome, tipo="text", etichetta="", richiesto=false, valore="") %}
<div class="campo-form">
    {% if etichetta %}
        <label for="{{ nome }}">{{ etichetta }}{% if richiesto %} *{% endif %}</label>
    {% endif %}
    <input type="{{ tipo }}"
           id="{{ nome }}"
           name="{{ nome }}"
           value="{{ valore }}"
           {% if richiesto %}required{% endif %}>
</div>
{% endmacro %}

{% macro campo_select(nome, opzioni, etichetta="", selezionato="") %}
<div class="campo-form">
    {% if etichetta %}<label for="{{ nome }}">{{ etichetta }}</label>{% endif %}
    <select id="{{ nome }}" name="{{ nome }}">
        {% for valore, testo in opzioni %}
            <option value="{{ valore }}" {% if valore == selezionato %}selected{% endif %}>
                {{ testo }}
            </option>
        {% endfor %}
    </select>
</div>
{% endmacro %}

{% macro pulsante(testo, tipo="submit", classe="btn-primary") %}
<button type="{{ tipo }}" class="{{ classe }}">{{ testo }}</button>
{% endmacro %}
```

```html
{# Utilizzo delle macro in un template #}
{% from "macro/form.html" import campo_input, campo_select, pulsante %}

<form method="POST" action="{{ url_for('utenti.registra') }}">
    {{ campo_input("nome", etichetta="Nome completo", richiesto=true) }}
    {{ campo_input("email", tipo="email", etichetta="Email", richiesto=true) }}
    {{ campo_input("password", tipo="password", etichetta="Password", richiesto=true) }}
    {{ campo_select("ruolo", [("utente", "Utente"), ("admin", "Amministratore")], etichetta="Ruolo") }}
    {{ pulsante("Registrati") }}
</form>
```

---

## File Statici in Produzione

In sviluppo, Flask e FastAPI servono file statici direttamente. In produzione, servire file statici dall'application server e inefficiente: ogni richiesta di un CSS o un'immagine occupa un worker che potrebbe gestire logica applicativa.

### WhiteNoise (Python-native)

WhiteNoise serve file statici direttamente dall'applicazione Python, aggiungendo header di cache e compressione. E la soluzione piu semplice per deployment su PaaS (Heroku, Render, Railway).

```python
# Django — settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Subito dopo SecurityMiddleware
    # ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Genera file .gz e .br compressi e aggiunge hash al nome (cache busting)

# Flask
from whitenoise import WhiteNoise

app = Flask(__name__)
app.wsgi_app = WhiteNoise(
    app.wsgi_app,
    root='static/',
    prefix='static/',
    max_age=31536000  # 1 anno (immutable con hash)
)
```

### CDN e Cache Busting

Per applicazioni con traffico elevato, i file statici vanno serviti da un CDN (CloudFront, Cloudflare, Fastly).

```python
# Flask — URL statici con hash per cache busting
# url_for('static', filename='css/stile.css')
# → /static/css/stile.css?v=abc123  (con Flask-Assets)

# Django — ManifestStaticFilesStorage aggiunge hash automaticamente
# {% static 'css/stile.css' %}
# → /static/css/stile.abc123def.css

# FastAPI — implementazione manuale con hash del file
import hashlib
from pathlib import Path

def static_url(filename: str) -> str:
    """Genera URL con hash per cache busting."""
    percorso = Path("static") / filename
    if percorso.exists():
        contenuto_hash = hashlib.md5(percorso.read_bytes()).hexdigest()[:8]
        return f"/static/{filename}?v={contenuto_hash}"
    return f"/static/{filename}"
```

---

## Gestione Sessioni

### Server-side Sessions vs JWT

| Aspetto | Sessioni Server-side | JWT |
|---------|---------------------|-----|
| **Storage** | Server (Redis, DB) | Client (cookie, localStorage) |
| **Stato** | Stateful | Stateless |
| **Invalidazione** | Immediata (cancella dal server) | Difficile (richiede blocklist) |
| **Scalabilita** | Richiede session store condiviso | Nativa (nessuno stato server) |
| **Dimensione** | ID piccolo (~32 byte) | Token grande (~1-2 KB) |
| **Sicurezza** | Dati sensibili restano sul server | Dati nel token leggibili (non criptati) |
| **Caso d'uso** | Web app con browser, SSR | API mobile, SPA, microservizi |

### Cookie HttpOnly e sicurezza

```python
# Flask — configurazione sessione sicura
app.config.update(
    SESSION_COOKIE_SECURE=True,       # Solo HTTPS
    SESSION_COOKIE_HTTPONLY=True,      # Non accessibile da JavaScript
    SESSION_COOKIE_SAMESITE='Lax',    # Protezione CSRF base
    SESSION_COOKIE_NAME='__Host-sid', # Cookie prefix sicuro
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
)

# FastAPI — impostare cookie sicuro manualmente
from fastapi.responses import JSONResponse

@app.post("/auth/login")
async def login(credenziali: Credenziali):
    token = crea_session_token(credenziali.utente_id)
    risposta = JSONResponse(content={"messaggio": "Login riuscito"})
    risposta.set_cookie(
        key="session_id",
        value=token,
        httponly=True,        # Non leggibile da JS
        secure=True,          # Solo HTTPS
        samesite="lax",       # Protezione CSRF
        max_age=3600,         # 1 ora
        path="/",
    )
    return risposta
```

### Protezione CSRF

```python
# Flask — Flask-WTF include protezione CSRF automatica
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# Nei template: {{ form.hidden_tag() }} include il token CSRF

# Per API con token bearer, il CSRF non e necessario perche
# il token non viene inviato automaticamente dal browser

# FastAPI — per form HTML (raro), implementare manualmente
from secrets import token_urlsafe

def genera_csrf_token() -> str:
    return token_urlsafe(32)

# Validare il token nel middleware per richieste POST/PUT/DELETE
# che arrivano da form HTML (non da API con Authorization header)
```

### Session Hardening e Token Rotation

```python
# ── Rotazione del Session ID (prevenzione session fixation) ──
# Dopo il login, e` CRITICO generare un nuovo session ID.
# Se si riutilizza il session ID pre-login, un attaccante
# potrebbe fissare il session ID della vittima.

# Flask — rotazione session dopo login
from flask import session
import secrets

@app.route("/auth/login", methods=["POST"])
def login():
    utente = verifica_credenziali(request.json)
    if utente:
        # Rigenerare il session ID (crea una nuova sessione)
        session.clear()
        session["user_id"] = utente.id
        session["login_time"] = datetime.utcnow().isoformat()
        session["fingerprint"] = genera_fingerprint(request)
        # Il session cookie viene riscritto con il nuovo ID
        return jsonify({"status": "ok"}), 200
    return jsonify({"error": "credenziali non valide"}), 401

def genera_fingerprint(req) -> str:
    """Fingerprint leggero per rilevare session hijacking."""
    import hashlib
    data = f"{req.user_agent.string}:{req.accept_languages}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

# ── Validazione sessione ad ogni richiesta ──
@app.before_request
def valida_sessione():
    if "user_id" in session:
        # Verificare fingerprint (session hijacking detection)
        fp = genera_fingerprint(request)
        if session.get("fingerprint") != fp:
            session.clear()
            return jsonify({"error": "sessione invalidata"}), 401

        # Verificare scadenza (idle timeout)
        login_time = datetime.fromisoformat(session["login_time"])
        if datetime.utcnow() - login_time > timedelta(hours=8):
            session.clear()
            return jsonify({"error": "sessione scaduta"}), 401

# ── Redis Session Store (per ambienti distribuiti) ──
# pip install flask-session redis
from flask_session import Session

app.config.update(
    SESSION_TYPE="redis",
    SESSION_REDIS=Redis(host="redis", port=6379, db=0),
    SESSION_KEY_PREFIX="app:session:",
    SESSION_USE_SIGNER=True,      # Firma il session ID nel cookie
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
)
Session(app)

# Vantaggi Redis session store:
# - Invalidazione immediata (delete dalla chiave Redis)
# - TTL automatico (Redis scade le sessioni)
# - Condiviso tra piu` istanze dell'applicazione
# - Persistenza opzionale (RDB/AOF)
```

---

## Background Tasks — Confronto

La scelta del sistema di background tasks dipende dalla complessita, dalla durata e dall'affidabilita richiesta.

| Caratteristica | FastAPI BackgroundTasks | Celery | arq | dramatiq |
|----------------|----------------------|--------|-----|----------|
| **Broker** | Nessuno (in-process) | Redis / RabbitMQ | Redis | Redis / RabbitMQ |
| **Persistenza** | No | Si | Si | Si |
| **Retry** | No | Si (configurabile) | Si | Si |
| **Scheduling** | No | Si (Celery Beat) | Si (cron) | No (serve apscheduler) |
| **Monitoring** | No | Flower | Dashboard arq | No built-in |
| **Async nativo** | Si | No (usa prefork) | Si | No (usa threading) |
| **Complessita setup** | Nessuna | Alta | Bassa | Media |
| **Caso d'uso** | Task brevi (<30s), non critici | Task complessi, pipeline, scheduled | Task async, Redis-only | Task affidabili, semplici |

### FastAPI BackgroundTasks

Adatto per operazioni brevi e non critiche che non richiedono retry o persistenza (invio email, scrittura log, aggiornamento cache).

```python
# Gia illustrato nella sezione FastAPI — riassunto:
# - Esegue dopo la risposta, nello stesso processo
# - Nessun broker, nessuna configurazione
# - Se il processo muore, il task e perso
```

### Celery — il riferimento per task complessi

```python
# tasks.py — con retry e rate limiting
from celery import shared_task

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    rate_limit='10/m',           # Max 10 esecuzioni al minuto
    acks_late=True,              # ACK solo dopo il completamento
    reject_on_worker_lost=True,  # Re-invia se il worker muore
)
def elabora_pagamento(self, ordine_id: int):
    try:
        ordine = Ordine.objects.get(id=ordine_id)
        risultato = gateway_pagamento.addebita(ordine.importo, ordine.metodo)
        ordine.stato = 'pagato'
        ordine.save()
        return risultato
    except GatewayTemporaneamenteNonDisponibile as exc:
        raise self.retry(exc=exc)
```

### arq — alternativa async leggera

```python
# worker.py — arq con funzioni async native
from arq import create_pool
from arq.connections import RedisSettings

async def invia_report(ctx, utente_id: int, periodo: str):
    """Task asincrono eseguito dal worker arq."""
    dati = await genera_report_async(utente_id, periodo)
    await invia_email_async(utente_id, dati)

class WorkerSettings:
    functions = [invia_report]
    redis_settings = RedisSettings(host='localhost', port=6379)
    max_jobs = 10

# Enqueue da FastAPI
@app.post("/report")
async def richiedi_report(utente_id: int, periodo: str):
    redis = await create_pool(RedisSettings())
    await redis.enqueue_job('invia_report', utente_id, periodo)
    return {"stato": "in_coda"}
```

---

## Deployment

Il deployment di un'applicazione Python in produzione richiede un server applicativo (Gunicorn, Uvicorn) dietro un reverse proxy (Nginx) e, idealmente, un'orchestrazione tramite container Docker.

### Gunicorn + Nginx (Flask/Django)

#### Configurazione Gunicorn

```python
# gunicorn.conf.py
import multiprocessing

# Indirizzo e porta di ascolto
bind = "0.0.0.0:8000"

# Numero di worker (regola generale: 2 * CPU + 1)
workers = multiprocessing.cpu_count() * 2 + 1

# Tipo di worker
worker_class = "sync"  # oppure "gthread" per thread

# Thread per worker (se worker_class e "gthread")
threads = 2

# Timeout per le richieste (in secondi)
timeout = 120

# Riavvia i worker dopo N richieste (previene memory leak)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Connessioni in attesa
backlog = 2048

# Preload dell'applicazione (riduce tempo di avvio dei worker)
preload_app = True
```

```bash
# Avvio per Flask
gunicorn "app:create_app()" --config gunicorn.conf.py

# Avvio per Django
gunicorn mio_progetto.wsgi:application --config gunicorn.conf.py
```

#### Configurazione Nginx come Reverse Proxy

```nginx
# /etc/nginx/sites-available/mia_app
upstream app_server {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name miosito.it www.miosito.it;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name miosito.it www.miosito.it;

    ssl_certificate /etc/letsencrypt/live/miosito.it/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/miosito.it/privkey.pem;

    # File statici serviti direttamente da Nginx
    location /static/ {
        alias /var/www/mia_app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/mia_app/media/;
        expires 7d;
    }

    # Proxy verso Gunicorn
    location / {
        proxy_pass http://app_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;

        # Timeout
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }

    # Limiti di sicurezza
    client_max_body_size 10M;

    # Compressione gzip
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;
    gzip_min_length 1000;
}
```

### Uvicorn (FastAPI)

#### Configurazione Uvicorn

```bash
# Avvio in sviluppo (con auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Avvio in produzione con worker multipli
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Oppure tramite Gunicorn con worker Uvicorn (consigliato in produzione)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

La configurazione Nginx per Uvicorn e identica a quella per Gunicorn. Per il supporto WebSocket, aggiungere il blocco seguente:

```nginx
location /ws/ {
    proxy_pass http://app_server;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
}
```

### Docker Deployment

#### Dockerfile per Applicazioni Python Web

```dockerfile
# Dockerfile — Build multi-stage per ridurre la dimensione dell'immagine

# Stage 1: Build delle dipendenze
FROM python:3.12-slim AS builder

WORKDIR /app

# Installazione delle dipendenze di sistema necessarie per la compilazione
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e installazione delle dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Immagine finale leggera
FROM python:3.12-slim

WORKDIR /app

# Solo le librerie runtime necessarie
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copia le dipendenze dallo stage di build
COPY --from=builder /install /usr/local

# Crea un utente non-root per la sicurezza
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copia il codice dell'applicazione
COPY . .

# Imposta i permessi
RUN chown -R appuser:appgroup /app

USER appuser

# Variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Avvio dell'applicazione
# Per Flask/Django:
# CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]
# Per FastAPI:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Docker Compose con Web + Database + Redis

```yaml
# docker-compose.yml
version: "3.9"

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/mia_app
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - static_files:/app/static
      - media_files:/app/media
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=mia_app
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - static_files:/var/www/static
      - media_files:/var/www/media
      - ./certbot/conf:/etc/letsencrypt
    depends_on:
      - web
    restart: unless-stopped

  # Worker Celery per task asincroni (opzionale, per Django/Flask)
  celery_worker:
    build: .
    command: celery -A mio_progetto worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/mia_app
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  static_files:
  media_files:
```

```bash
# Comandi utili per Docker
docker compose up -d --build          # Avvio con rebuild delle immagini
docker compose logs -f web             # Segui i log del servizio web
docker compose exec web alembic upgrade head   # Esegui migrazioni
docker compose exec web python manage.py migrate  # Migrazioni Django
docker compose down -v                 # Arresta e rimuovi volumi
```

---

## Deployment Avanzato — ASGI Servers

### Uvicorn sotto uvloop

uvloop e un'implementazione dell'event loop asyncio scritta in Cython e basata su libuv (la stessa libreria alla base di Node.js). Sostituisce l'event loop standard di CPython offrendo un throughput significativamente superiore.

```bash
# Installazione
pip install uvloop

# Uvicorn usa uvloop automaticamente se disponibile
uvicorn app.main:app --loop uvloop --host 0.0.0.0 --port 8000

# Verifica che uvloop sia attivo nei log di avvio:
# INFO:     Started server process [12345]
# INFO:     Using uvloop event loop implementation
```

```python
# Configurazione programmatica
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        loop="uvloop",              # Usa uvloop
        http="httptools",           # Parser HTTP veloce (C-based)
        log_level="info",
        access_log=False,           # Disabilita in produzione per performance
        server_header=False,        # Non esporre la versione del server
        date_header=True,
    )
```

**Benchmark indicativi (richieste/sec su endpoint JSON semplice):**

| Configurazione | Richieste/sec |
|---------------|--------------|
| Uvicorn + asyncio (default) | ~12,000 |
| Uvicorn + uvloop | ~22,000 |
| Uvicorn + uvloop + httptools | ~28,000 |
| Gunicorn + UvicornWorker (4 worker) | ~90,000 |

### Gunicorn + Uvicorn Workers (produzione consigliata)

La combinazione di Gunicorn come process manager e Uvicorn come worker ASGI e la configurazione raccomandata per la produzione.

```python
# gunicorn_asgi.conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Gunicorn gestisce:
# - Processo master (supervisore)
# - Fork dei worker
# - Riavvio worker in caso di crash
# - Graceful shutdown (SIGTERM)
# - max_requests per prevenire memory leak

max_requests = 5000
max_requests_jitter = 500
timeout = 120
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"

# Pre-fork: carica l'app prima del fork per risparmiare memoria (copy-on-write)
preload_app = True
```

```bash
gunicorn app.main:app --config gunicorn_asgi.conf.py
```

### Hypercorn

Server ASGI alternativo a Uvicorn con supporto nativo per HTTP/2 e HTTP/3 (QUIC).

```bash
# Installazione
pip install hypercorn

# Avvio base
hypercorn app.main:app --bind 0.0.0.0:8000

# Con HTTP/2
hypercorn app.main:app --bind 0.0.0.0:443 \
    --certfile cert.pem --keyfile key.pem

# Con worker multipli
hypercorn app.main:app --bind 0.0.0.0:8000 --workers 4
```

```python
# hypercorn_config.py
bind = "0.0.0.0:8000"
workers = 4
accesslog = "-"
errorlog = "-"
graceful_timeout = 30
keep_alive_timeout = 5
```

### Daphne

Server ASGI sviluppato dal team Django Channels. E la scelta naturale per progetti Django con ASGI.

```bash
# Installazione
pip install daphne

# Avvio
daphne -b 0.0.0.0 -p 8000 mio_progetto.asgi:application

# Con worker multipli (Daphne non supporta worker interni,
# usare un process manager esterno come supervisord o systemd)
```

### Confronto ASGI Servers

| Caratteristica | Uvicorn | Hypercorn | Daphne |
|---------------|---------|-----------|--------|
| **HTTP/2** | No (richiede Nginx) | Si (nativo) | Si |
| **HTTP/3 (QUIC)** | No | Si | No |
| **uvloop** | Si | Si | No |
| **Worker multipli** | Si (o via Gunicorn) | Si | No (esterno) |
| **Caso d'uso** | FastAPI, Starlette | HTTP/2 nativo | Django Channels |
| **Performance** | Eccellente | Buona | Buona |

---

## API Versioning

Il versioning delle API e fondamentale per evolverle senza rompere i client esistenti. Esistono tre strategie principali.

### Strategia 1: URL Path (consigliata)

```python
# FastAPI — versioning tramite path prefix
from fastapi import FastAPI, APIRouter

app = FastAPI()

v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

@v1_router.get("/utenti")
async def lista_utenti_v1():
    """V1: restituisce nome e email."""
    return [{"nome": "Mario", "email": "mario@esempio.it"}]

@v2_router.get("/utenti")
async def lista_utenti_v2():
    """V2: aggiunge campo 'ruoli' e rinomina 'nome' in 'nome_completo'."""
    return [{"nome_completo": "Mario Rossi", "email": "mario@esempio.it", "ruoli": ["admin"]}]

app.include_router(v1_router)
app.include_router(v2_router)
```

**Vantaggi:** semplice, esplicito, cache-friendly, facile da documentare.
**Svantaggi:** duplicazione di route, URL piu lunghi.

### Strategia 2: Header (Accept/Custom)

```python
# FastAPI — versioning tramite header Accept
from fastapi import FastAPI, Header, HTTPException

@app.get("/api/utenti")
async def lista_utenti(accept: str = Header("application/json")):
    if "version=2" in accept:
        return [{"nome_completo": "Mario Rossi", "ruoli": ["admin"]}]
    # Default: v1
    return [{"nome": "Mario", "email": "mario@esempio.it"}]

# Oppure header custom
@app.get("/api/utenti")
async def lista_utenti(x_api_version: str = Header("1")):
    if x_api_version == "2":
        return [{"nome_completo": "Mario Rossi", "ruoli": ["admin"]}]
    return [{"nome": "Mario", "email": "mario@esempio.it"}]
```

**Vantaggi:** URL puliti, un solo endpoint.
**Svantaggi:** meno visibile, problematico per il caching HTTP, difficile da testare nel browser.

### Strategia 3: Query Parameter

```python
@app.get("/api/utenti")
async def lista_utenti(version: int = 1):
    if version == 2:
        return [{"nome_completo": "Mario Rossi", "ruoli": ["admin"]}]
    return [{"nome": "Mario", "email": "mario@esempio.it"}]
# GET /api/utenti?version=2
```

**Vantaggi:** semplice, compatibile con tutti i client.
**Svantaggi:** non semantico, inquina i parametri di query, problematico per il caching.

> **Raccomandazione:** URL path versioning e la strategia piu adottata (GitHub API, Stripe, Twilio). E la piu chiara per documentazione e debugging.

---

## Personalizzazione OpenAPI

> **Fonte:** FastAPI OpenAPI — https://fastapi.tiangolo.com/advanced/extending-openapi/

### Response Models con esempi

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

class UtenteResponse(BaseModel):
    id: int = Field(..., examples=[42])
    nome: str = Field(..., examples=["Mario Rossi"])
    email: str = Field(..., examples=["mario@esempio.it"])
    ruolo: str = Field("utente", examples=["admin"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 42,
                    "nome": "Mario Rossi",
                    "email": "mario@esempio.it",
                    "ruolo": "admin"
                }
            ]
        }
    }
```

### Tag e raggruppamento

```python
app = FastAPI(
    title="La Mia API",
    version="2.0.0",
    description="API di gestione utenti e articoli",
    openapi_tags=[
        {
            "name": "autenticazione",
            "description": "Operazioni di login, registrazione e gestione token.",
        },
        {
            "name": "utenti",
            "description": "CRUD utenti. Richiede autenticazione.",
        },
        {
            "name": "articoli",
            "description": "Gestione articoli del blog.",
            "externalDocs": {
                "description": "Documentazione estesa",
                "url": "https://docs.miosito.it/articoli",
            },
        },
    ],
)

@app.post("/auth/login", tags=["autenticazione"])
async def login(): ...

@app.get("/utenti", tags=["utenti"])
async def lista_utenti(): ...
```

### Security Schemes

```python
from fastapi import FastAPI, Security
from fastapi.security import HTTPBearer, OAuth2PasswordBearer, APIKeyHeader

# Bearer Token
bearer_scheme = HTTPBearer(
    scheme_name="Bearer Token",
    description="Token JWT ottenuto dall'endpoint /auth/login"
)

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={
        "lettura": "Lettura risorse",
        "scrittura": "Creazione e modifica risorse",
        "admin": "Accesso completo"
    }
)

# API Key
api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    description="API key per accesso programmatico"
)

@app.get(
    "/utenti",
    responses={
        200: {"description": "Lista utenti"},
        401: {"description": "Token mancante o non valido"},
        403: {"description": "Permessi insufficienti"},
    }
)
async def lista_utenti(token: str = Security(bearer_scheme)):
    ...
```

### Escludere endpoint dalla documentazione

```python
# Endpoint interni non visibili nella doc pubblica
@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}

@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

---

## Best Practices

Le seguenti dieci best practice sono fondamentali per costruire applicazioni web Python robuste, sicure e manutenibili:

**1. Utilizzare variabili d'ambiente per la configurazione sensibile.** Non inserire mai chiavi segrete, credenziali del database o token API direttamente nel codice sorgente. Utilizzare librerie come `python-dotenv` per caricare le variabili da file `.env` (esclusi dal version control tramite `.gitignore`) e accedervi tramite `os.environ`. In produzione, utilizzare il sistema di secrets del proprio orchestratore (Docker Secrets, Kubernetes Secrets, AWS Secrets Manager).

**2. Implementare la validazione rigorosa di tutti i dati in ingresso.** Mai fidarsi dei dati provenienti dal client. Con FastAPI, sfruttare i modelli Pydantic per una validazione dichiarativa e automatica. Con Flask, utilizzare Marshmallow o WTForms. Con Django, sfruttare i serializzatori DRF o i form Django. Validare non solo il tipo dei dati, ma anche i range, i formati e la coerenza tra campi correlati.

**3. Adottare una strategia di gestione degli errori coerente.** Definire error handler personalizzati per ogni codice di stato HTTP rilevante. Restituire risposte JSON strutturate con messaggi di errore comprensibili per il client ma senza esporre dettagli interni del sistema. Registrare i dettagli completi degli errori nei log del server per il debugging.

**4. Strutturare il progetto in moduli ben definiti fin dall'inizio.** Utilizzare i Blueprint in Flask, i router in FastAPI e le app in Django per separare le responsabilita. Ogni modulo dovrebbe gestire un dominio specifico dell'applicazione (autenticazione, utenti, articoli, pagamenti). Questa organizzazione facilita la manutenzione, il testing e la collaborazione in team.

**5. Scrivere test automatizzati per ogni endpoint e logica di business.** Utilizzare pytest come framework di testing, insieme a pytest-asyncio per FastAPI e pytest-django per Django. Testare non solo i casi di successo, ma anche i casi di errore, le validazioni e i permessi. Puntare a una copertura minima dell'80% e automatizzare l'esecuzione dei test nella pipeline CI/CD.

**6. Implementare il logging strutturato e il monitoring.** Configurare il logging con livelli appropriati (DEBUG, INFO, WARNING, ERROR, CRITICAL) e formati strutturati (JSON). Integrare strumenti di monitoring come Prometheus per le metriche e Sentry per il tracciamento degli errori. In produzione, aggregare i log con strumenti come ELK Stack o Loki.

**7. Utilizzare le migrazioni del database in modo sistematico.** Che si tratti di Alembic (Flask/FastAPI) o delle migrazioni integrate di Django, ogni modifica alla struttura del database deve essere tracciata tramite una migrazione versionata. Non modificare mai manualmente lo schema del database in produzione. Testare sempre le migrazioni in ambiente di staging prima di applicarle in produzione.

**8. Implementare rate limiting e protezione dagli abusi.** Proteggere le API dal sovraccarico e dagli attacchi brute-force implementando il rate limiting. Utilizzare librerie come `slowapi` per FastAPI, `Flask-Limiter` per Flask o `django-ratelimit` per Django. Configurare limiti diversi per endpoint diversi (ad esempio, limiti piu restrittivi per gli endpoint di autenticazione).

**9. Ottimizzare le query al database e gestire correttamente le connessioni.** Utilizzare il connection pooling per evitare di aprire e chiudere connessioni ad ogni richiesta. Con SQLAlchemy, utilizzare `select_related` (o `joinedload`) per prevenire il problema N+1. Analizzare le query lente tramite strumenti come Django Debug Toolbar o SQLAlchemy echo mode. Aggiungere indici del database dove necessario.

**10. Automatizzare il deployment con Docker e CI/CD.** Containerizzare l'applicazione con Docker per garantire coerenza tra ambienti di sviluppo, staging e produzione. Utilizzare build multi-stage per ridurre la dimensione delle immagini. Configurare una pipeline CI/CD (GitHub Actions, GitLab CI, Jenkins) che esegua automaticamente test, linting, build dell'immagine Docker e deployment su ogni push al branch principale.

---

## Troubleshooting

### Problemi comuni Flask

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| `RuntimeError: Working outside of application context` | Accesso a `current_app` o `g` fuori da una richiesta | Usare `with app.app_context():` o ristrutturare il codice |
| `RuntimeError: Working outside of request context` | Accesso a `request` fuori da una view | Passare i dati come parametri anziche accedere a `request` direttamente |
| Importazioni circolari | Blueprint importa modelli che importano il blueprint | Usare import lazy (in fondo al file `__init__.py`) |
| `404` su tutte le route con blueprint | Blueprint non registrato nella factory | Verificare `app.register_blueprint(bp)` in `create_app()` |
| Sessioni non persistenti tra richieste | `SECRET_KEY` non impostata o che cambia ad ogni restart | Impostare `SECRET_KEY` come variabile d'ambiente fissa |
| Async view lenta quanto sync | Flask esegue le coroutine in un event loop per-richiesta | Per vera concorrenza async, usare FastAPI con Uvicorn |

### Problemi comuni FastAPI

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| `422 Unprocessable Entity` | Validazione Pydantic fallita | Leggere il campo `detail` nella risposta per i campi non validi |
| `Event loop is closed` | Tentativo di usare oggetti asyncio dopo la chiusura | Non condividere coroutine tra richieste; creare nuove istanze |
| Dipendenza non risolta | Mancata dichiarazione di `Depends()` | Verificare la signature della funzione e i type hint |
| Endpoint lento con `def` (non `async def`) | FastAPI esegue le funzioni sync in un thread pool | Usare `async def` per I/O-bound, `def` solo per CPU-bound breve |
| `on_startup` / `on_shutdown` ignorati | Deprecati a favore di `lifespan` | Migrare al pattern `asynccontextmanager` con `lifespan` |
| WebSocket si disconnette subito | Client o proxy non configurato per upgrade | Verificare header `Upgrade: websocket` e configurazione Nginx |

### Problemi comuni Django

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| `OperationalError: no such table` | Migrazioni non eseguite | `python manage.py migrate` |
| N+1 query | Query lazy su relazioni | Usare `select_related()` (FK) e `prefetch_related()` (M2M) |
| `CSRF verification failed` | Token CSRF mancante nel form | Aggiungere `{% csrf_token %}` nel template |
| Static files 404 in produzione | `DEBUG=False` disabilita il serving statico | Usare `collectstatic` + WhiteNoise o Nginx |
| `ImproperlyConfigured: DATABASES` | Configurazione DB mancante | Verificare `settings.py` e variabili d'ambiente |

### Problemi di deployment

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| Worker timeout con Gunicorn | Richieste che superano `timeout` | Aumentare `timeout` o rendere le richieste asincrone |
| `[CRITICAL] WORKER TIMEOUT` | Task CPU-bound blocca il worker | Spostare task pesanti in Celery o usare `run_in_executor` |
| Connessioni DB esaurite | Troppi worker senza connection pooling | Configurare `pool_size` e `max_overflow` in SQLAlchemy |
| `OSError: [Errno 98] Address already in use` | Porta gia occupata | `lsof -ti:8000 \| xargs kill` oppure cambiare porta |
| Memory leak nei worker | Riferimenti circolari o cache non limitata | Impostare `max_requests` in Gunicorn per riciclare i worker |

---

## Esercizi

### Esercizio 1 — Flask Application Factory con Blueprint annidati

Creare un'applicazione Flask con:
- Application factory con tre configurazioni (dev, test, prod)
- API blueprint con versioning (v1, v2) tramite nested blueprints
- Almeno 3 endpoint CRUD per una risorsa (es. "prodotti")
- Error handler centralizzato per 400, 404, 422, 500
- Test con pytest per ogni endpoint in tutte le configurazioni

### Esercizio 2 — Flask 3.x Async Views

Creare un aggregatore di API che:
- Espone un endpoint `/api/dashboard` che chiama 3 API esterne in parallelo (usare `httpx.AsyncClient` e `asyncio.gather`)
- Misura il tempo di risposta totale (confrontare sync vs async)
- Implementa caching con TTL per le risposte aggregate
- Gestisce timeout e fallback per ciascuna API esterna

### Esercizio 3 — FastAPI Lifespan completo

Costruire un servizio FastAPI con:
- Lifespan che inizializza: pool PostgreSQL (asyncpg), connessione Redis, modello ML fittizio
- Dipendenze con `yield` per connessione e transazione
- Endpoint che usa tutte le risorse inizializzate nel lifespan
- Test con lifespan override (database in-memory, mock Redis)

### Esercizio 4 — Dependency Injection con sub-dipendenze

Progettare un sistema di DI FastAPI con:
- Almeno 3 livelli di dipendenze annidate (autenticazione → autorizzazione → query builder)
- Override di tutte le dipendenze nei test (nessuna connessione reale)
- Dipendenza parametrizzata (es. `richiedi_ruolo("admin")`)

### Esercizio 5 — Middleware Cross-Framework

Implementare lo stesso middleware (Request ID + timing + rate limiting) in:
- Flask (usando `before_request`/`after_request`)
- FastAPI (usando `BaseHTTPMiddleware` di Starlette)
- Confrontare la struttura e la testabilita dei due approcci

### Esercizio 6 — Background Tasks Pipeline

Costruire un sistema di elaborazione ordini con:
- FastAPI endpoint che accetta un ordine e lo mette in coda
- Worker Celery (o arq) che elabora il pagamento
- Worker che invia email di conferma
- Dashboard status con polling endpoint
- Retry con backoff esponenziale per fallimenti gateway pagamento

### Esercizio 7 — ASGI WebSocket Chat

Creare un sistema di chat con:
- FastAPI WebSocket endpoint per stanze multiple
- Broadcast dei messaggi a tutti i partecipanti della stanza
- Heartbeat ping/pong per rilevare disconnessioni
- Persistenza messaggi in Redis (ultimi 100 per stanza)
- Test con `httpx` WebSocket client

### Esercizio 8 — Deployment Production-Ready

Containerizzare un'applicazione FastAPI con:
- Dockerfile multi-stage
- docker-compose con web, PostgreSQL, Redis, Nginx
- Gunicorn + UvicornWorker (4 worker)
- Nginx con TLS (self-signed per test), gzip, static files, WebSocket proxy
- Health check endpoint
- Configurazione uvloop e httptools

### Esercizio 9 — API Versioning con migrazione

Implementare un'API con:
- V1 con schema originale
- V2 con schema rinominato e campo aggiuntivo
- Adapter layer che converte tra v1 e v2
- Test che verifica la retrocompatibilita di v1 quando v2 e attiva
- Deprecation header su v1

### Esercizio 10 — OpenAPI personalizzata con security

Costruire un'API FastAPI con:
- Documentazione OpenAPI personalizzata (tag, descrizioni, esempi)
- Tre security schemes (Bearer JWT, API Key, OAuth2 con scopes)
- Response models per tutti gli status code (200, 201, 400, 401, 403, 404, 422, 500)
- Endpoint `/health` e `/metrics` esclusi dalla documentazione

---

## Letture

- Flask Documentation (3.1.x). https://flask.palletsprojects.com/en/stable/
- Flask Changelog. https://flask.palletsprojects.com/en/stable/changes/
- FastAPI Documentation. https://fastapi.tiangolo.com/
- FastAPI Advanced — Lifespan Events. https://fastapi.tiangolo.com/advanced/events/
- FastAPI Advanced — Dependencies with yield. https://fastapi.tiangolo.com/advanced/dependencies/dependencies-with-yield/
- Starlette Documentation. https://www.starlette.io/
- Django Documentation (5.x). https://docs.djangoproject.com/
- Django REST Framework. https://www.django-rest-framework.org/
- Pydantic v2 Documentation. https://docs.pydantic.dev/latest/
- Uvicorn Documentation. https://www.uvicorn.org/
- Gunicorn Documentation. https://docs.gunicorn.org/en/stable/
- Hypercorn Documentation. https://hypercorn.readthedocs.io/
- ASGI Specification. https://asgi.readthedocs.io/en/latest/
- PEP 3333 — Python Web Server Gateway Interface v1.0.1. https://peps.python.org/pep-3333/
- PEP 3156 — Asynchronous IO Support Rebooted. https://peps.python.org/pep-3156/
- Jinja2 Documentation. https://jinja.palletsprojects.com/en/stable/
- WhiteNoise Documentation. https://whitenoise.readthedocs.io/
- Celery Documentation. https://docs.celeryq.dev/en/stable/
- arq Documentation. https://arq-docs.helpmanual.io/
- slowapi Documentation. https://slowapi.readthedocs.io/

---

## Cross-link

| Modulo | Relazione |
|--------|-----------|
| `04-PROGRAMMAZIONE-PYTHON/09-async.md` | Fondamenti asyncio, event loop, coroutine — prerequisito per ASGI |
| `04-PROGRAMMAZIONE-PYTHON/10-testing.md` | pytest, pytest-asyncio, fixture, mock — base per test dei framework |
| `04-PROGRAMMAZIONE-PYTHON/12-database.md` | SQLAlchemy, asyncpg, pattern CRUD, migrazioni — integrazione DB |
| `04-PROGRAMMAZIONE-PYTHON/14-sicurezza.md` | Hashing password, JWT, CORS, input validation — sicurezza applicativa |
| `04-PROGRAMMAZIONE-PYTHON/31-osservabilita-otel-prometheus.md` | OpenTelemetry, Prometheus, tracing, metriche — osservabilita dei servizi |
| `03-WINDOWS-POWERUSER/` | Fondamenti networking, DNS, porte — contesto infrastrutturale |
| `15-SECURITY/` | OWASP Top 10, penetration testing, threat modeling — sicurezza offensiva/difensiva |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **ASGI** | Asynchronous Server Gateway Interface — protocollo asincrono per la comunicazione tra server web e applicazione Python. Supporta HTTP, WebSocket e lifespan events. |
| **Blueprint** | Componente Flask per organizzare un'applicazione in moduli riutilizzabili, ciascuno con proprie route, template e file statici. |
| **Cache busting** | Tecnica per invalidare la cache del browser aggiungendo un hash al nome dei file statici, forzando il download della versione aggiornata. |
| **Celery** | Libreria Python per l'esecuzione distribuita di task asincroni, basata su un broker di messaggi (Redis o RabbitMQ). |
| **CORS** | Cross-Origin Resource Sharing — meccanismo HTTP che consente a un server di indicare quali origini diverse possono accedere alle sue risorse. |
| **CSRF** | Cross-Site Request Forgery — attacco in cui un sito malevolo invia richieste autenticate per conto dell'utente vittima. |
| **Daphne** | Server ASGI sviluppato dal team Django Channels, ottimizzato per applicazioni Django con supporto WebSocket. |
| **Dependency Injection** | Pattern in cui le dipendenze di una funzione vengono fornite dall'esterno anziche create internamente. In FastAPI, implementato tramite `Depends()`. |
| **Event Loop** | Meccanismo di concorrenza single-threaded che gestisce operazioni I/O asincrone tramite callback e coroutine (asyncio). |
| **Gunicorn** | Green Unicorn — server WSGI pre-fork per applicazioni Python. Puo ospitare worker Uvicorn per servire applicazioni ASGI. |
| **Hypercorn** | Server ASGI con supporto nativo per HTTP/2 e HTTP/3 (QUIC). |
| **Jinja2** | Motore di template Python utilizzato da Flask e FastAPI per la generazione di HTML dinamico. Supporta ereditarieta, macro e autoescape. |
| **Lifespan** | Protocollo ASGI per gestire eventi di avvio e arresto dell'applicazione tramite un context manager asincrono. |
| **Marshmallow** | Libreria Python per la serializzazione, deserializzazione e validazione dei dati. Standard de facto in Flask. |
| **Middleware** | Componente che intercetta ogni richiesta e risposta HTTP per aggiungere logica trasversale (logging, autenticazione, compressione). |
| **Pydantic** | Libreria Python per la validazione dei dati tramite modelli basati su type hint. Cuore del sistema di validazione di FastAPI. |
| **Rate Limiting** | Tecnica per limitare il numero di richieste che un client puo effettuare in un intervallo di tempo, proteggendo il server da abusi. |
| **Starlette** | Framework ASGI leggero su cui e costruito FastAPI. Fornisce routing, middleware, sessioni, template e WebSocket. |
| **uvloop** | Implementazione dell'event loop asyncio scritta in Cython e basata su libuv. Offre throughput 2-3x superiore rispetto all'event loop standard. |
| **Uvicorn** | Server ASGI ad alte prestazioni basato su uvloop e httptools. Server di riferimento per FastAPI. |
| **WhiteNoise** | Libreria Python per servire file statici direttamente dall'applicazione, con compressione e cache busting automatici. |
| **WSGI** | Web Server Gateway Interface (PEP 3333) — protocollo sincrono per la comunicazione tra server web e applicazione Python. |

---

> **Nota**: Questa guida copre i fondamenti e le funzionalita avanzate dei principali web framework Python. Per approfondire ciascun framework, si consiglia di consultare la documentazione ufficiale: [Flask](https://flask.palletsprojects.com/), [FastAPI](https://fastapi.tiangolo.com/), [Django](https://docs.djangoproject.com/). La pratica costante attraverso la costruzione di progetti reali e il metodo piu efficace per padroneggiare questi strumenti.
