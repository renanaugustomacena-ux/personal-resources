---
corso: "Programmazione Python"
fase: "4 — Applicazioni Specializzate"
modulo: "19"
titolo: "CLI Tools con Python"
versione: "argparse 3.x / click 8.x / typer 0.15+ / rich 13.x"
livello: "Intermedio"
prerequisiti:
  - "01-06 — Python Base"
  - "09 — Type Hints e Mypy"
  - "05 — Gestione File e I/O"
obiettivi:
  - "Costruire CLI professionali con argparse, click e typer"
  - "Implementare output ricco e interattivo con rich e textual"
  - "Gestire configurazione, variabili d'ambiente e file di config"
  - "Distribuire CLI come pacchetti installabili con entry_points"
  - "Scrivere test per applicazioni CLI con CliRunner"
  - "Implementare subcomandi, autocompletamento e progress bar"
tag: [CLI, argparse, click, typer, rich, textual, terminal, entry-points]
---

# CLI Tools con Python — Guida Completa

> **Modulo 19** · **Aggiornamento:** 2026-05-24 · **Versione:** argparse 3.x / click 8.x / typer 0.15+ / rich 13.x

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [Type Hints](09-type-hints-e-mypy.md), [Gestione File e I/O](05-gestione-file-io.md)
>
> Al termine di questo modulo saprai:
> 1. Costruire CLI professionali con argparse, click e typer
> 2. Implementare output ricco e interattivo con rich e textual
> 3. Gestire configurazione, variabili d'ambiente e file di config
> 4. Distribuire CLI come pacchetti installabili con `entry_points`
> 5. Scrivere test per applicazioni CLI con `CliRunner`
> 6. Implementare subcomandi, autocompletamento e progress bar
>
> **Tempo stimato:** 5-7 ore · **Livello:** Intermedio

## Idee guida
1. **typer > click > argparse.** Tier moderne.
2. **rich per output colorato/tabular.**
3. **questionary per interactive prompt.**
4. **uv per shipping CLI as zipapp.**


## Mappa concettuale

```
                          ┌──────────────────────────────┐
                          │       CLI Tool Python        │
                          └──────────────┬───────────────┘
              ┌──────────────┬───────────┼────────────┬──────────────┐
              ▼              ▼           ▼            ▼              ▼
       ┌────────────┐ ┌───────────┐ ┌────────┐ ┌──────────┐ ┌────────────┐
       │  Parsing    │ │  Output   │ │ Input  │ │  Config  │ │ Distribuz. │
       │  Argomenti  │ │  Ricco    │ │ Interatt│ │ Multi-src│ │  & Pkg     │
       └──────┬─────┘ └─────┬─────┘ └───┬────┘ └─────┬────┘ └──────┬─────┘
              │              │           │            │              │
    ┌─────┬───┴───┐    ┌────┴────┐      │     ┌──────┴──────┐       │
    ▼     ▼       ▼    ▼         ▼      ▼     ▼             ▼       ▼
argparse click  typer  rich   colorama prompt  TOML/YAML   entry_points
                               tabulate toolkit ENV vars   pipx/PyInstaller
              │                                 │
    ┌─────────┴──────────┐              ┌───────┴────────┐
    ▼                    ▼              ▼                ▼
 subparsers          @click.group   TOML > YAML > INI  pyproject.toml
 mutually_exclusive  @app.callback  CLI > ENV > FILE   [project.scripts]
 custom types/actions CliRunner     XDG config dirs     zipapp / Nuitka
              │
    ┌─────────┴──────────────────┐
    ▼                            ▼
 auto-completion              piping & signal
 (argcomplete/shellingham)    stdin/stdout/stderr
                              exit codes / SIGINT
```


La riga di comando resta il canale di comunicazione piu diretto e potente tra un professionista IT e il sistema che amministra. Ogni script di automazione, ogni pipeline CI/CD, ogni operazione di manutenzione passa attraverso un terminale. Costruire strumenti da riga di comando robusti, documentati e intuitivi non e un esercizio accademico — e una competenza che moltiplica l'efficacia del lavoro quotidiano. Python offre un ecosistema eccezionale per la costruzione di CLI: dalla libreria standard `argparse`, passando per framework maturi come Click e Typer, fino a librerie di output come Rich e strumenti interattivi come Prompt Toolkit. Questa guida copre l'intero spettro, dalla definizione dei parametri alla distribuzione dell'eseguibile finale.

---

## Indice

1. [Panoramica](#panoramica)
2. [argparse](#argparse)
   - [ArgumentParser e add_argument](#argumentparser-e-add_argument)
   - [Argomenti posizionali vs opzionali](#argomenti-posizionali-vs-opzionali)
   - [Types, choices, default, required, help, metavar](#types-choices-default-required-help-metavar)
   - [Subcommands con add_subparsers](#subcommands-con-add_subparsers)
   - [Gruppi mutuamente esclusivi](#gruppi-mutuamente-esclusivi)
   - [Tipi personalizzati e azioni](#tipi-personalizzati-e-azioni)
   - [Subparser avanzati e composizione](#subparser-avanzati-e-composizione)
   - [Esempio completo di CLI tool](#esempio-completo-di-cli-tool)
3. [click](#click)
   - [Fondamenti](#fondamenti-click)
   - [Funzionalita Avanzate](#funzionalita-avanzate-click)
   - [Plugin architecture con click](#plugin-architecture-con-click)
   - [Testing avanzato con CliRunner](#testing-avanzato-con-clirunner)
4. [Typer](#typer)
   - [Fondamenti](#fondamenti-typer)
   - [Funzionalita Avanzate](#funzionalita-avanzate-typer)
   - [Typer Context e invocazione avanzata](#typer-context-e-invocazione-avanzata)
   - [Testing CLI Typer](#testing-cli-typer)
5. [Rich (Output Formattato)](#rich-output-formattato)
   - [Console avanzata](#console-avanzata)
   - [Inspect e debugging visuale](#inspect-e-debugging-visuale)
6. [Textual — TUI Framework](#textual-tui-framework)
   - [Architettura di un'app Textual](#architettura-di-unapp-textual)
   - [Widget e layout](#widget-e-layout)
   - [CSS nel terminale](#css-nel-terminale)
   - [Schermate e navigazione](#schermate-e-navigazione)
   - [Testing di app Textual](#testing-di-app-textual)
7. [Prompt Toolkit](#prompt-toolkit)
8. [Prompt interattivi: questionary e InquirerPy](#prompt-interattivi-questionary-e-inquirerpy)
   - [questionary](#questionary)
   - [InquirerPy](#inquirerpy)
   - [Confronto tra librerie di prompt](#confronto-tra-librerie-di-prompt)
9. [Output e Formattazione](#output-e-formattazione)
10. [Piping e Composizione Unix](#piping-e-composizione-unix)
11. [Exit Codes](#exit-codes)
12. [Gestione Segnali](#gestione-segnali)
13. [Logging nelle applicazioni CLI](#logging-nelle-applicazioni-cli)
    - [Integrazione con i livelli di verbosita](#integrazione-con-i-livelli-di-verbosita)
    - [Logging strutturato con structlog](#logging-strutturato-con-structlog)
    - [Rich logging handler](#rich-logging-handler)
    - [Rotazione dei log e file handler](#rotazione-dei-log-e-file-handler)
14. [Auto-completamento Shell](#auto-completamento-shell)
15. [Configurazione](#configurazione)
16. [Distribuzione CLI](#distribuzione-cli)
    - [shiv e zipapp](#shiv-e-zipapp)
17. [Generazione di man page](#generazione-di-man-page)
18. [Testing avanzato di CLI](#testing-avanzato-di-cli)
    - [pytest-console-scripts](#pytest-console-scripts)
    - [Strategie di test per CLI complessi](#strategie-di-test-per-cli-complessi)
19. [CLI Design Patterns e UX](#cli-design-patterns-e-ux)
    - [Pattern architetturali](#pattern-architetturali)
    - [UX e progressive disclosure](#ux-e-progressive-disclosure)
    - [Convenzioni sui colori e la semantica visuale](#convenzioni-sui-colori-e-la-semantica-visuale)
20. [Best Practices](#best-practices)
21. [Esercizi](#esercizi)
22. [Letture](#letture)
23. [Riferimenti incrociati](#riferimenti-incrociati)
24. [Glossario](#glossario)

---

## Panoramica

Un CLI tool ben progettato condivide le stesse qualita di una buona API: interfaccia coerente, documentazione integrata, messaggi di errore chiari, comportamento prevedibile. La differenza e che l'utente finale e un essere umano seduto davanti a un terminale, non un programma che consuma JSON. Questo impone attenzione particolare alla user experience: help text leggibili, output colorato dove utile, barre di progresso per operazioni lunghe, conferme prima di azioni distruttive.

L'ecosistema Python per CLI si stratifica su tre livelli:

| Livello | Strumento | Caratteristica principale |
|---------|-----------|--------------------------|
| Libreria standard | `argparse` | Zero dipendenze, integrato in Python |
| Framework dichiarativo | `click` | Decoratori, composizione, testabilita |
| Framework type-hint | `typer` | Costruito su Click, sfrutta le type hints |
| Output ricco | `rich` | Tabelle, colori, progress bar, Markdown |
| Input interattivo | `prompt_toolkit` | Completamento, storia, validazione |

La scelta dipende dalla complessita del progetto. Per uno script interno con due flag, `argparse` e piu che sufficiente. Per un tool distribuito con decine di subcommand, Click o Typer offrono una struttura piu manutenibile. Rich e Prompt Toolkit si integrano con qualsiasi framework e arricchiscono l'esperienza utente indipendentemente dalla scelta del parser degli argomenti.

L'anatomia di un CLI tool professionale comprende diversi componenti: un parser degli argomenti che genera automaticamente l'help, un sistema di configurazione multi-livello, output adattivo (colorato per il terminale, strutturato per le pipe), gestione robusta degli errori con exit code significativi, e un meccanismo di distribuzione che renda il tool facilmente installabile. Nelle sezioni seguenti esaminiamo ciascun componente in dettaglio, partendo dal parser piu semplice fino ad arrivare a soluzioni complete pronte per la produzione.

---

## argparse

`argparse` fa parte della libreria standard di Python ed e disponibile senza installare nulla. Per strumenti semplici e script interni, rappresenta la scelta naturale: nessuna dipendenza esterna, documentazione ufficiale estesa, compatibilita garantita con qualsiasi versione di Python 3.

### ArgumentParser e add_argument

La classe `ArgumentParser` e il punto di ingresso. Accetta parametri che definiscono il comportamento globale del parser:

```python
import argparse

parser = argparse.ArgumentParser(
    prog="servermanager",
    description="Gestione server dell'infrastruttura aziendale",
    epilog="Esempio: servermanager deploy --env production app.tar.gz",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
```

Il parametro `prog` sovrascrive il nome dello script mostrato nell'help. `description` appare prima degli argomenti, `epilog` dopo. `formatter_class` controlla la formattazione: `RawDescriptionHelpFormatter` preserva i ritorni a capo nel testo, utile per esempi multi-riga.

Ogni argomento si aggiunge con `add_argument`:

```python
parser.add_argument("filename", help="File di configurazione da processare")
parser.add_argument("-v", "--verbose", action="store_true", help="Output dettagliato")

args = parser.parse_args()
print(args.filename, args.verbose)
```

### Argomenti posizionali vs opzionali

La distinzione e fondamentale. Un argomento posizionale non ha prefisso e il suo valore e determinato dalla posizione nella riga di comando. Un argomento opzionale inizia con `-` (forma breve) o `--` (forma estesa).

```python
# Posizionale: obbligatorio, determinato dalla posizione
parser.add_argument("source", help="File sorgente")
parser.add_argument("destination", help="Directory di destinazione")

# Opzionale: identificato dal prefisso, ordine libero
parser.add_argument("-n", "--dry-run", action="store_true",
                    help="Simula l'operazione senza modificare il file system")
parser.add_argument("-l", "--log-level", default="INFO",
                    help="Livello di logging (default: INFO)")
```

Invocazione: `script.py /tmp/data.csv /backup --dry-run --log-level DEBUG`

L'attributo `nargs` controlla quanti valori un argomento consuma:

```python
parser.add_argument("files", nargs="+", help="Uno o piu file da processare")
parser.add_argument("--exclude", nargs="*", default=[], help="Pattern da escludere")
parser.add_argument("--range", nargs=2, metavar=("MIN", "MAX"), help="Intervallo numerico")
```

I valori speciali di `nargs`: `"?"` (zero o uno), `"*"` (zero o piu), `"+"` (uno o piu), un intero (numero esatto), `argparse.REMAINDER` (tutto il resto).

### Types, choices, default, required, help, metavar

Ogni parametro di `add_argument` controlla un aspetto diverso del comportamento:

```python
parser.add_argument(
    "--port",
    type=int,              # Converte automaticamente la stringa in intero
    default=8080,          # Valore se l'argomento non viene specificato
    choices=range(1024, 65536),  # Valori ammessi
    metavar="PORT",        # Nome mostrato nell'help al posto del valore
    help="Porta del server (default: %(default)s)"
)

parser.add_argument(
    "--format",
    type=str,
    choices=["json", "csv", "xml"],
    required=True,         # Rende obbligatorio un argomento opzionale
    help="Formato di output"
)

parser.add_argument(
    "--timeout",
    type=float,
    default=30.0,
    help="Timeout in secondi (default: %(default)s)"
)
```

Il placeholder `%(default)s` nell'help viene sostituito automaticamente con il valore di default — un dettaglio che migliora sensibilmente la documentazione senza sforzo aggiuntivo.

### Subcommands con add_subparsers

Per CLI con comandi multipli (come `git commit`, `git push`), `add_subparsers` crea sotto-parser indipendenti:

```python
import argparse

parser = argparse.ArgumentParser(prog="dbctl", description="Gestione database")
subparsers = parser.add_subparsers(dest="command", required=True, help="Comando da eseguire")

# Subcommand: backup
backup_parser = subparsers.add_parser("backup", help="Esegui backup del database")
backup_parser.add_argument("--output", "-o", required=True, help="File di output")
backup_parser.add_argument("--compress", action="store_true", help="Comprimi con gzip")

# Subcommand: restore
restore_parser = subparsers.add_parser("restore", help="Ripristina da backup")
restore_parser.add_argument("backup_file", help="File di backup da ripristinare")
restore_parser.add_argument("--force", action="store_true", help="Sovrascrive senza conferma")

# Subcommand: status
status_parser = subparsers.add_parser("status", help="Mostra stato del database")
status_parser.add_argument("--detailed", action="store_true", help="Informazioni dettagliate")

args = parser.parse_args()

if args.command == "backup":
    print(f"Backup verso {args.output}, compress={args.compress}")
elif args.command == "restore":
    print(f"Ripristino da {args.backup_file}, force={args.force}")
elif args.command == "status":
    print(f"Stato database, detailed={args.detailed}")
```

Il parametro `dest="command"` salva il nome del subcommand scelto in `args.command`. Con `required=True`, argparse genera un errore se l'utente non specifica alcun subcommand.

### Gruppi mutuamente esclusivi

Quando due opzioni non possono coesistere, `add_mutually_exclusive_group` impone il vincolo:

```python
parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--json", action="store_true", help="Output in formato JSON")
group.add_argument("--csv", action="store_true", help="Output in formato CSV")
group.add_argument("--table", action="store_true", help="Output tabulare leggibile")
```

Se l'utente specifica `--json --csv`, argparse genera automaticamente un messaggio di errore chiaro senza che lo sviluppatore debba implementare alcuna logica di validazione.

### Tipi personalizzati e azioni

Il parametro `type` accetta qualsiasi callable che trasforma una stringa in un altro tipo. Questo permette di implementare validazione sofisticata:

```python
import argparse
from pathlib import Path

def valid_directory(path_str: str) -> Path:
    """Tipo personalizzato che verifica l'esistenza di una directory."""
    path = Path(path_str)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"La directory '{path_str}' non esiste")
    return path

def positive_int(value_str: str) -> int:
    """Tipo personalizzato per interi positivi."""
    value = int(value_str)
    if value <= 0:
        raise argparse.ArgumentTypeError(f"{value_str} non e un intero positivo")
    return value

parser = argparse.ArgumentParser()
parser.add_argument("--workdir", type=valid_directory, default=Path("."),
                    help="Directory di lavoro (deve esistere)")
parser.add_argument("--workers", type=positive_int, default=4,
                    help="Numero di processi worker (intero positivo)")
```

Le azioni personalizzate estendono il comportamento oltre i semplici flag:

```python
class CountVerbosity(argparse.Action):
    """Azione che conta le occorrenze di -v per determinare il livello di verbosita."""
    def __call__(self, parser, namespace, values, option_string=None):
        current = getattr(namespace, self.dest, 0) or 0
        setattr(namespace, self.dest, current + 1)

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", nargs=0, action=CountVerbosity, default=0,
                    help="Aumenta verbosita (ripetibile: -v, -vv, -vvv)")
```

### Subparser avanzati e composizione

Quando un CLI cresce, i subparser possono essere organizzati in moduli separati con argomenti condivisi tramite `parents`:

```python
import argparse

# Parser padre con opzioni comuni — non viene usato direttamente
parser_comune = argparse.ArgumentParser(add_help=False)
parser_comune.add_argument("--verbose", "-v", action="count", default=0,
                           help="Aumenta verbosita")
parser_comune.add_argument("--config", type=Path, default=Path("~/.myapp.toml"),
                           help="File di configurazione")
parser_comune.add_argument("--dry-run", action="store_true",
                           help="Simula senza eseguire")

# Parser principale
parser = argparse.ArgumentParser(
    prog="infractl",
    description="Gestione infrastruttura",
    parents=[parser_comune],  # Eredita le opzioni comuni
)
subparsers = parser.add_subparsers(dest="command", required=True)

# Subparser con gerarchia: infractl server create / infractl server list
server_parser = subparsers.add_parser("server", help="Gestione server",
                                       parents=[parser_comune])
server_sub = server_parser.add_subparsers(dest="server_command", required=True)

create_parser = server_sub.add_parser("create", help="Crea server",
                                       parents=[parser_comune])
create_parser.add_argument("name", help="Nome del server")
create_parser.add_argument("--cpu", type=int, default=2, help="Numero CPU")
create_parser.add_argument("--ram", type=int, default=4096, help="RAM in MB")

list_parser = server_sub.add_parser("list", help="Elenca server",
                                     parents=[parser_comune])
list_parser.add_argument("--format", choices=["table", "json", "csv"],
                         default="table", help="Formato output")

# Collegare funzioni ai subparser con set_defaults
def handle_server_create(args):
    print(f"Creazione server {args.name}: {args.cpu} CPU, {args.ram} MB RAM")

def handle_server_list(args):
    print(f"Elenco server in formato {args.format}")

create_parser.set_defaults(func=handle_server_create)
list_parser.set_defaults(func=handle_server_list)

args = parser.parse_args()
if hasattr(args, "func"):
    args.func(args)
```

Il pattern `set_defaults(func=...)` e il modo idiomatico per collegare una funzione handler a ogni subcommand, eliminando la catena di `if/elif` sul nome del comando. La documentazione ufficiale di Python (docs.python.org/3/library/argparse.html) lo raccomanda esplicitamente.

La combinazione di `parents` e `set_defaults` permette di costruire CLI con gerarchie arbitrariamente profonde mantenendo il codice modulare: ogni modulo definisce il proprio subparser e la propria funzione handler, e il parser principale li compone.

### Esempio completo di CLI tool

```python
#!/usr/bin/env python3
"""loganalyzer — Analisi e filtraggio di file di log."""

import argparse
import sys
import re
from pathlib import Path
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(
        prog="loganalyzer",
        description="Analizza file di log, filtra per livello, data e pattern.",
        epilog="Esempi:\n"
               "  loganalyzer /var/log/app.log --level ERROR\n"
               "  loganalyzer access.log --pattern '5\\d{2}' --since 2025-01-01\n"
               "  loganalyzer *.log --level WARNING ERROR --count",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("logfiles", nargs="+", type=Path,
                        help="File di log da analizzare")
    parser.add_argument("--level", nargs="+",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Filtra per livello di log")
    parser.add_argument("--pattern", type=str,
                        help="Regex per filtrare le righe")
    parser.add_argument("--since", type=lambda s: datetime.fromisoformat(s),
                        metavar="YYYY-MM-DD", help="Mostra solo righe dopo questa data")
    parser.add_argument("--count", action="store_true",
                        help="Mostra solo il conteggio delle righe corrispondenti")

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", help="Output JSON")
    output_group.add_argument("--csv", action="store_true", help="Output CSV")

    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Aumenta verbosita (-v, -vv)")
    return parser.parse_args()

def main():
    args = parse_args()
    total = 0

    for logfile in args.logfiles:
        if not logfile.exists():
            print(f"ERRORE: File non trovato: {logfile}", file=sys.stderr)
            continue
        with open(logfile) as f:
            for line in f:
                if args.level and not any(lv in line for lv in args.level):
                    continue
                if args.pattern and not re.search(args.pattern, line):
                    continue
                total += 1
                if not args.count:
                    print(line, end="")

    if args.count:
        print(f"Righe corrispondenti: {total}")

if __name__ == "__main__":
    main()
```

---

Questo esempio dimostra i pattern fondamentali: argomenti posizionali con `nargs="+"`, opzioni con tipi e choices, gruppi mutuamente esclusivi per il formato di output, e separazione tra parsing (`parse_args`) e logica (`main`). Il messaggio di help generato automaticamente include la descrizione, le opzioni con i valori di default, e l'epilogo con gli esempi. Lanciando `loganalyzer --help` l'utente ottiene immediatamente una panoramica completa delle funzionalita disponibili.

---

## click

Click (Command Line Interface Creation Kit) e un framework maturo, sviluppato dal creatore di Flask (Armin Ronacher). Rispetto ad argparse, Click offre un approccio dichiarativo basato su decoratori, composizione naturale di comandi, supporto integrato per i test, e una gestione avanzata dell'I/O e dei colori. La curva di apprendimento e minima per chi conosce gia i decoratori Python.

Installazione: `pip install click`

### Fondamenti click

#### @click.command() e @click.group()

Il decoratore `@click.command()` trasforma una funzione in un comando CLI. `@click.group()` crea un contenitore di sotto-comandi:

```python
import click

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Tool di gestione dell'infrastruttura server."""
    pass

@cli.command()
@click.argument("hostname")
@click.option("--port", "-p", default=22, type=int, help="Porta SSH")
@click.option("--user", "-u", default="admin", help="Nome utente")
def connect(hostname, port, user):
    """Connetti a un server remoto via SSH."""
    click.echo(f"Connessione a {user}@{hostname}:{port}...")

@cli.command()
@click.argument("service")
@click.option("--force", is_flag=True, help="Forza il riavvio")
def restart(service, force):
    """Riavvia un servizio sul server."""
    if force:
        click.echo(f"Riavvio forzato di {service}...")
    else:
        click.echo(f"Riavvio graceful di {service}...")

if __name__ == "__main__":
    cli()
```

#### @click.option() e @click.argument()

La distinzione tra option e argument segue la stessa logica di argparse: gli argomenti sono posizionali e tipicamente obbligatori, le opzioni hanno un prefisso e sono tipicamente facoltative.

```python
@click.command()
@click.argument("source", type=click.Path(exists=True))
@click.argument("destination", type=click.Path())
@click.option("--recursive", "-r", is_flag=True, help="Copia ricorsiva")
@click.option("--exclude", multiple=True, help="Pattern da escludere (ripetibile)")
@click.option("--buffer-size", type=int, default=8192,
              show_default=True, help="Dimensione buffer in bytes")
def copy(source, destination, recursive, exclude, buffer_size):
    """Copia file da SOURCE a DESTINATION."""
    click.echo(f"Copia {source} -> {destination}")
    click.echo(f"Ricorsivo: {recursive}, Buffer: {buffer_size}")
    for pattern in exclude:
        click.echo(f"Escluso: {pattern}")
```

#### Types in Click

Click fornisce tipi predefiniti piu espressivi rispetto ad argparse:

```python
@click.command()
@click.option("--name", type=click.STRING, help="Nome del progetto")
@click.option("--count", type=click.INT, help="Numero di iterazioni")
@click.option("--threshold", type=click.FLOAT, help="Soglia percentuale")
@click.option("--verbose", type=click.BOOL, help="Modalita verbosa")
@click.option("--env", type=click.Choice(["dev", "staging", "production"],
              case_sensitive=False), help="Ambiente di deploy")
@click.option("--config", type=click.Path(exists=True, dir_okay=False,
              readable=True), help="File di configurazione")
@click.option("--output", type=click.File("w"), default="-",
              help="File di output (default: stdout)")
def deploy(name, count, threshold, verbose, env, config, output):
    """Deploy dell'applicazione."""
    output.write(f"Deploying {name} in {env}\n")
```

`click.Path` verifica automaticamente l'esistenza, i permessi, e il tipo (file o directory). `click.File` apre automaticamente il file e supporta `-` come alias per stdin/stdout.

#### Prompts, conferma e password

Click integra nativamente i prompt interattivi:

```python
@click.command()
@click.option("--name", prompt="Il tuo nome", help="Nome dell'utente")
@click.option("--password", prompt=True, hide_input=True,
              confirmation_prompt=True, help="Password")
@click.option("--age", prompt="La tua eta", type=int, help="Eta")
def register(name, password, age):
    """Registra un nuovo utente."""
    click.echo(f"Utente {name} registrato (eta: {age})")

@click.command()
@click.argument("filename")
def delete(filename):
    """Elimina un file in modo permanente."""
    if click.confirm(f"Sei sicuro di voler eliminare {filename}?", abort=True):
        click.echo(f"File {filename} eliminato.")
```

Con `prompt=True`, se l'utente non fornisce il valore sulla riga di comando, Click lo chiede interattivamente. `hide_input=True` nasconde l'input per le password. `confirmation_prompt=True` richiede di digitare il valore una seconda volta.

### Funzionalita Avanzate click

#### Gruppi annidati e sotto-comandi

Click permette di annidare gruppi di comandi per creare gerarchie complesse:

```python
@click.group()
def cli():
    """Tool di gestione cloud."""
    pass

@cli.group()
def vm():
    """Gestione macchine virtuali."""
    pass

@vm.command()
@click.argument("name")
@click.option("--cpu", default=2, help="Numero di CPU")
@click.option("--ram", default=4096, help="RAM in MB")
def create(name, cpu, ram):
    """Crea una nuova VM."""
    click.echo(f"VM {name} creata: {cpu} CPU, {ram}MB RAM")

@vm.command()
@click.argument("name")
@click.option("--force", is_flag=True)
def delete(name, force):
    """Elimina una VM."""
    click.echo(f"VM {name} eliminata (force={force})")

@cli.group()
def network():
    """Gestione reti."""
    pass

@network.command("list")
def list_networks():
    """Elenca tutte le reti."""
    click.echo("Elenco reti...")
```

L'utente invoca con: `cloudctl vm create my-server --cpu 4 --ram 8192` oppure `cloudctl network list`.

#### Context (ctx)

Il context di Click trasporta stato tra i comandi di un gruppo:

```python
@click.group()
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx, debug):
    """Applicazione CLI con context condiviso."""
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug

@cli.command()
@click.pass_context
def sync(ctx):
    """Sincronizza i dati."""
    debug = ctx.obj["DEBUG"]
    if debug:
        click.echo("DEBUG: modalita verbosa attiva")
    click.echo("Sincronizzazione in corso...")
```

#### Callbacks e opzioni eager (--version)

Le opzioni eager vengono processate prima di qualsiasi altra logica, utili per `--version`:

```python
def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo("myapp v2.1.0")
    ctx.exit()

@click.command()
@click.option("--version", is_flag=True, callback=print_version,
              expose_value=False, is_eager=True, help="Mostra la versione")
@click.argument("name")
def hello(name):
    click.echo(f"Ciao, {name}!")
```

#### Progress bar e output colorato

```python
import time

@click.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def process(files):
    """Processa una lista di file con barra di progresso."""
    with click.progressbar(files, label="Elaborazione file") as bar:
        for filepath in bar:
            time.sleep(0.5)  # Simula elaborazione

    click.echo(click.style("Completato!", fg="green", bold=True))
    click.echo(click.style("ATTENZIONE: 3 file saltati", fg="yellow"))
    click.echo(click.style("ERRORE: permesso negato su /etc/shadow", fg="red"))
```

`click.style()` applica colori ANSI. I colori disponibili includono: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`. Attributi aggiuntivi: `bold`, `dim`, `underline`, `blink`, `reverse`.

### Plugin architecture con click

Click supporta nativamente l'architettura a plugin tramite gruppi lazy-loaded. Questo permette di costruire CLI estensibili dove i sotto-comandi vengono scoperti a runtime da entry_points o da directory:

```python
import importlib
import pkgutil
import click

class PluginGroup(click.Group):
    """Gruppo che scopre sotto-comandi da un package di plugin."""

    def __init__(self, *args, plugin_package: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._plugin_package = plugin_package

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Scopre i comandi disponibili scansionando il package."""
        commands = []
        try:
            package = importlib.import_module(self._plugin_package)
            for _, name, _ in pkgutil.iter_modules(package.__path__):
                commands.append(name)
        except ImportError:
            pass
        commands.sort()
        return commands

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Carica il comando dal modulo plugin corrispondente."""
        try:
            mod = importlib.import_module(f"{self._plugin_package}.{cmd_name}")
            return mod.cli  # Ogni plugin espone un oggetto 'cli'
        except (ImportError, AttributeError):
            return None

@click.group(cls=PluginGroup, plugin_package="myapp.plugins")
def cli():
    """CLI con architettura a plugin."""
    pass
```

Per la scoperta tramite entry_points (setuptools), si usa `importlib.metadata.entry_points()`:

```python
from importlib.metadata import entry_points

class EntryPointGroup(click.Group):
    """Gruppo che scopre sotto-comandi da entry_points."""

    def __init__(self, *args, entry_point_group: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._ep_group = entry_point_group

    def list_commands(self, ctx: click.Context) -> list[str]:
        eps = entry_points(group=self._ep_group)
        return sorted(ep.name for ep in eps)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        eps = entry_points(group=self._ep_group)
        for ep in eps:
            if ep.name == cmd_name:
                return ep.load()
        return None
```

Questo pattern e usato da molti tool reali: `pip`, `tox`, `pytest` scoprono i propri plugin tramite entry_points. Un plugin di terze parti si registra semplicemente dichiarando il proprio entry_point in `pyproject.toml`:

```toml
[project.entry-points."myapp.plugins"]
export = "myapp_export.cli:cli"
```

### Testing avanzato con CliRunner

Click include un test runner che simula l'invocazione da riga di comando senza lanciare un sottoprocesso:

```python
from click.testing import CliRunner

def test_deploy_command():
    runner = CliRunner()
    result = runner.invoke(deploy, ["--env", "production", "--name", "myapp"])

    assert result.exit_code == 0
    assert "Deploying myapp in production" in result.output

def test_deploy_invalid_env():
    runner = CliRunner()
    result = runner.invoke(deploy, ["--env", "invalid"])

    assert result.exit_code != 0
    assert "Invalid value" in result.output

def test_file_output():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(deploy, ["--output", "result.txt",
                                        "--env", "dev", "--name", "test"])
        assert result.exit_code == 0
        with open("result.txt") as f:
            assert "Deploying test in dev" in f.read()
```

`CliRunner` cattura stdout, stderr, exit code. `isolated_filesystem()` crea una directory temporanea per test che coinvolgono il file system.

Tecniche avanzate di testing con CliRunner:

```python
def test_stdin_input():
    """Test di un comando che legge da stdin."""
    runner = CliRunner()
    result = runner.invoke(process_cmd, ["-"], input="riga1\nriga2\nriga3\n")
    assert result.exit_code == 0
    assert "3 righe processate" in result.output

def test_environment_variables():
    """Test con variabili d'ambiente simulate."""
    runner = CliRunner(env={"MYAPP_DEBUG": "true", "MYAPP_PORT": "9090"})
    result = runner.invoke(serve_cmd)
    assert "porta 9090" in result.output

def test_prompt_input():
    """Test di un comando con prompt interattivo."""
    runner = CliRunner()
    result = runner.invoke(register_cmd, input="Mario\nmario@example.com\n")
    assert result.exit_code == 0
    assert "Mario registrato" in result.output

def test_exception_handling():
    """Verifica che le eccezioni vengano gestite correttamente."""
    runner = CliRunner()
    result = runner.invoke(risky_cmd, ["--force"], catch_exceptions=False)
    # catch_exceptions=False propaga l'eccezione al test framework
```

---

## Typer

Typer e costruito sopra Click ma adotta un paradigma radicalmente diverso: l'interfaccia CLI viene definita automaticamente dalle type hints delle funzioni Python. Nessun decoratore per opzioni e argomenti — il tipo dei parametri determina tutto. Typer e stato creato dallo stesso autore di FastAPI (Sebastian Ramirez) e segue la stessa filosofia: sfruttare al massimo il type system di Python per ridurre la duplicazione.

Installazione: `pip install typer`

### Fondamenti Typer

#### CLI basata su type hints

```python
import typer

app = typer.Typer(help="Gestione utenti del sistema")

@app.command()
def create(
    username: str,
    email: str,
    admin: bool = False,
    groups: list[str] = typer.Option([], "--group", "-g", help="Gruppi dell'utente"),
):
    """Crea un nuovo utente nel sistema."""
    role = "amministratore" if admin else "utente standard"
    typer.echo(f"Creato {username} ({email}) come {role}")
    for group in groups:
        typer.echo(f"  Aggiunto al gruppo: {group}")

@app.command()
def delete(
    username: str,
    force: bool = typer.Option(False, "--force", "-f",
                                help="Elimina senza conferma"),
):
    """Elimina un utente dal sistema."""
    if not force:
        confirm = typer.confirm(f"Eliminare l'utente {username}?")
        if not confirm:
            typer.echo("Operazione annullata.")
            raise typer.Abort()
    typer.echo(f"Utente {username} eliminato.")

@app.command("list")
def list_users(
    format: str = typer.Option("table", help="Formato output (table/json)"),
    limit: int = typer.Option(50, min=1, max=1000, help="Numero massimo di risultati"),
):
    """Elenca gli utenti del sistema."""
    typer.echo(f"Elenco utenti (formato: {format}, limite: {limit})")

if __name__ == "__main__":
    app()
```

La magia di Typer sta nella mappatura automatica: parametri senza default diventano argomenti posizionali obbligatori, parametri con default diventano opzioni. Un parametro `bool` con default `False` diventa un flag `--admin/--no-admin`. `typer.Option()` aggiunge metadata come help text, nomi abbreviati e vincoli.

#### Comandi e gruppi

```python
import typer

app = typer.Typer()
db_app = typer.Typer(help="Operazioni database")
cache_app = typer.Typer(help="Operazioni cache")

app.add_typer(db_app, name="db")
app.add_typer(cache_app, name="cache")

@db_app.command()
def migrate(revision: str = "head"):
    """Esegui le migration del database."""
    typer.echo(f"Migration a: {revision}")

@db_app.command()
def seed(count: int = 100):
    """Popola il database con dati di test."""
    typer.echo(f"Inseriti {count} record di test")

@cache_app.command()
def flush(pattern: str = "*"):
    """Svuota la cache."""
    typer.echo(f"Cache svuotata (pattern: {pattern})")

@cache_app.command()
def stats():
    """Mostra statistiche della cache."""
    typer.echo("Hit rate: 94.2%, Memory: 256MB")
```

Invocazione: `myapp db migrate --revision abc123` oppure `myapp cache flush --pattern "user:*"`.

#### Typer vs Click: confronto

| Aspetto | Click | Typer |
|---------|-------|-------|
| Definizione parametri | Decoratori espliciti | Type hints automatiche |
| Curva di apprendimento | Moderata | Minima (se si conoscono le type hints) |
| Verbosita | Piu codice decoratore | Meno boilerplate |
| Flessibilita | Massima | Leggermente inferiore |
| Testing | CliRunner integrato | Eredita CliRunner da Click |
| Completamento shell | Plugin esterno | Integrato nativamente |
| Dipendenze | Nessuna (a parte Click) | Click + typing-extensions |

### Funzionalita Avanzate Typer

#### Callbacks

Il callback di un gruppo Typer si esegue prima di ogni sotto-comando ed e il posto ideale per opzioni globali:

```python
import typer

app = typer.Typer()
state = {"verbose": False}

@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v",
                                  help="Attiva output verboso"),
    config: str = typer.Option("~/.myapp.toml", envvar="MYAPP_CONFIG",
                                help="Percorso file di configurazione"),
):
    """Tool di gestione infrastruttura."""
    state["verbose"] = verbose
    if verbose:
        typer.echo(f"Config: {config}")

@app.command()
def deploy(env: str):
    """Deploy dell'applicazione."""
    if state["verbose"]:
        typer.echo("DEBUG: inizio deploy")
    typer.echo(f"Deploy in ambiente: {env}")
```

#### Completamento shell

Typer genera automaticamente script di completamento per Bash, Zsh e Fish:

```bash
# Genera lo script di completamento per Bash
myapp --install-completion bash

# Oppure manualmente
_MYAPP_COMPLETE=bash_source myapp > ~/.myapp-complete.bash
source ~/.myapp-complete.bash
```

#### Integrazione con Rich

Typer si integra nativamente con Rich per output piu espressivo:

```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(rich_markup_mode="rich")
console = Console()

@app.command()
def status():
    """Mostra lo stato dei servizi con output [bold green]formattato[/bold green]."""
    table = Table(title="Stato Servizi")
    table.add_column("Servizio", style="cyan")
    table.add_column("Stato", style="bold")
    table.add_column("Uptime")

    table.add_row("nginx", "[green]attivo[/green]", "14d 3h")
    table.add_row("postgres", "[green]attivo[/green]", "14d 3h")
    table.add_row("redis", "[red]inattivo[/red]", "-")

    console.print(table)
```

### Typer Context e invocazione avanzata

Typer espone il context di Click sottostante tramite `typer.Context`, permettendo pattern avanzati come l'invocazione di sotto-comandi, l'accesso ai metadati del parser e il passaggio di stato complesso:

```python
import typer

app = typer.Typer()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """
    Tool di gestione. Se invocato senza sotto-comando, mostra lo stato.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # invoke_without_command=True: esegue questo callback anche senza subcommand
    if ctx.invoked_subcommand is None:
        typer.echo("Nessun comando specificato. Uso: myapp --help")

@app.command()
def info(ctx: typer.Context):
    """Mostra informazioni sul sistema."""
    verbose = ctx.obj.get("verbose", False)
    typer.echo(f"Versione: 2.0.0")
    if verbose:
        typer.echo(f"Python: {sys.version}")
        typer.echo(f"Piattaforma: {sys.platform}")

@app.command()
def run_all(ctx: typer.Context):
    """Esegue tutti i sotto-comandi in sequenza."""
    # Invocazione programmatica di un altro comando
    ctx.invoke(info)
    typer.echo("---")
    ctx.invoke(status)
```

Il `typer.Context` fornisce accesso a:

- `ctx.invoked_subcommand` — il nome del sotto-comando che sta per essere eseguito (utile nel callback)
- `ctx.obj` — dizionario per passare stato tra callback e sotto-comandi
- `ctx.invoke(comando)` — invocazione programmatica di un altro comando
- `ctx.parent` — accesso al context del comando padre nella gerarchia

### Testing CLI Typer

Typer eredita `CliRunner` da Click, ma offre anche `typer.testing.CliRunner` con funzionalita identiche:

```python
from typer.testing import CliRunner

runner = CliRunner()

def test_create_user():
    result = runner.invoke(app, ["create", "mario", "mario@example.com"])
    assert result.exit_code == 0
    assert "Creato mario" in result.output

def test_create_user_admin():
    result = runner.invoke(app, ["create", "admin", "admin@corp.com", "--admin"])
    assert result.exit_code == 0
    assert "amministratore" in result.output

def test_delete_with_confirmation():
    """Test del prompt di conferma — si simula l'input 'y'."""
    result = runner.invoke(app, ["delete", "mario"], input="y\n")
    assert result.exit_code == 0
    assert "eliminato" in result.output

def test_delete_abort():
    """Test dell'annullamento — si simula l'input 'n'."""
    result = runner.invoke(app, ["delete", "mario"], input="n\n")
    assert result.exit_code == 1  # Abort

def test_list_with_options():
    result = runner.invoke(app, ["list", "--format", "json", "--limit", "10"])
    assert result.exit_code == 0
    assert "json" in result.output

def test_global_verbose_flag():
    """Test del callback globale con opzione --verbose."""
    result = runner.invoke(app, ["--verbose", "deploy", "production"])
    assert result.exit_code == 0
    assert "DEBUG" in result.output
```

Quando si testano applicazioni Typer che usano `rich.console.Console`, e buona pratica iniettare un `Console` con `force_terminal=True` e `width` fisso per ottenere output deterministico nei test:

```python
from io import StringIO
from rich.console import Console

def make_test_console() -> tuple[Console, StringIO]:
    """Crea un Console per test con output deterministico."""
    buffer = StringIO()
    console = Console(file=buffer, force_terminal=True, width=120)
    return console, buffer
```

---

## Rich (Output Formattato)

Rich e la libreria di riferimento per l'output formattato nel terminale Python. Trasforma un terminale austero in un'interfaccia ricca con tabelle, colori, barre di progresso, alberi, pannelli, syntax highlighting e rendering Markdown. Rich funziona su tutti i terminali moderni e gestisce automaticamente il fallback quando i colori non sono supportati.

Installazione: `pip install rich`

### Console

L'oggetto `Console` e il punto di ingresso principale:

```python
from rich.console import Console

console = Console()

# Print con markup Rich
console.print("Stato: [bold green]OK[/bold green]")
console.print("[red]ERRORE:[/red] connessione al database fallita")
console.print("File processati: [cyan]142[/cyan] su [cyan]150[/cyan]")

# Log con timestamp automatico
console.log("Avvio elaborazione batch")
console.log("Completati 50 record", style="bold")
console.log("[red]Timeout sulla connessione[/red]")

# Stampa eccezioni formattate
try:
    1 / 0
except Exception:
    console.print_exception(show_locals=True)
```

### Tabelle

```python
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(title="Inventario Server", show_lines=True)
table.add_column("Hostname", style="cyan", no_wrap=True)
table.add_column("IP", style="magenta")
table.add_column("OS", style="green")
table.add_column("CPU %", justify="right")
table.add_column("RAM %", justify="right")
table.add_column("Stato")

table.add_row("web-01", "10.0.1.10", "Ubuntu 24.04", "23%", "67%",
              "[green]Online[/green]")
table.add_row("web-02", "10.0.1.11", "Ubuntu 24.04", "89%", "92%",
              "[red]Critico[/red]")
table.add_row("db-01", "10.0.2.10", "Debian 12", "45%", "78%",
              "[yellow]Warning[/yellow]")

console.print(table)
```

### Progress bar

```python
import time
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Progress bar semplice
with Progress() as progress:
    task = progress.add_task("Download...", total=100)
    for i in range(100):
        time.sleep(0.05)
        progress.update(task, advance=1)

# Progress bar multipla con colonne personalizzate
with Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
) as progress:
    download = progress.add_task("Download pacchetti", total=200)
    install = progress.add_task("Installazione", total=150)

    while not progress.finished:
        progress.update(download, advance=1.5)
        progress.update(install, advance=0.8)
        time.sleep(0.02)
```

### Pannelli, alberi e strutture

```python
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

console = Console()

# Pannello informativo
panel = Panel(
    "[bold]Server web-01[/bold]\n"
    "IP: 10.0.1.10\n"
    "OS: Ubuntu 24.04 LTS\n"
    "Uptime: 42 giorni",
    title="Dettagli Server",
    border_style="green",
)
console.print(panel)

# Albero della struttura di un progetto
tree = Tree("[bold]infrastruttura[/bold]")
production = tree.add("[green]production[/green]")
production.add("web-01 (nginx)")
production.add("web-02 (nginx)")
db = production.add("database")
db.add("db-primary")
db.add("db-replica")

staging = tree.add("[yellow]staging[/yellow]")
staging.add("stage-01 (all-in-one)")

console.print(tree)
```

### Markdown rendering e syntax highlighting

```python
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax

console = Console()

# Rendering Markdown
md = Markdown("""
# Report Giornaliero
## Server attivi: 12/12
- Nessun **incidente** nelle ultime 24 ore
- Backup completati con `successo`
""")
console.print(md)

# Syntax highlighting
code = '''
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
'''
syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
console.print(syntax)
```

### Live display e Prompt

```python
import time
from rich.live import Live
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm

# Live display: aggiornamento in tempo reale
def generate_table(step: int) -> Table:
    table = Table()
    table.add_column("Servizio")
    table.add_column("Richieste/s")
    table.add_row("API", str(100 + step * 10))
    table.add_row("Web", str(250 + step * 5))
    return table

with Live(generate_table(0), refresh_per_second=4) as live:
    for step in range(20):
        time.sleep(0.25)
        live.update(generate_table(step))

# Prompt con Rich
name = Prompt.ask("Nome del progetto", default="my-project")
port = IntPrompt.ask("Porta", default=8080)
proceed = Confirm.ask("Procedere con il deploy?")
env = Prompt.ask("Ambiente", choices=["dev", "staging", "prod"])
```

Rich si distingue per la capacita di rendere qualsiasi output del terminale immediatamente piu leggibile e professionale. L'investimento nell'integrazione e minimo — spesso basta sostituire `print()` con `console.print()` — ma l'impatto sull'esperienza utente e significativo. Le tabelle allineate automaticamente, i colori semantici (verde per successo, rosso per errore, giallo per avvisi) e le barre di progresso per operazioni lunghe trasformano un tool da "script interno" a "prodotto professionale".

### Console avanzata

Oltre alle funzionalita base, `Console` offre metodi specializzati per scenari comuni nei CLI tool:

```python
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

console = Console()

# Status spinner — per operazioni di durata indeterminata
with console.status("[bold green]Connessione al database...") as status:
    # Simula operazione lunga
    import time
    time.sleep(2)
    status.update("[bold green]Migrazione tabelle...")
    time.sleep(1)

console.print("[green]Migrazione completata.[/green]")

# Columns — dispone renderables su piu colonne
dati = [
    Panel(f"Server {i}\n10.0.1.{i}\n[green]Online[/green]", expand=True)
    for i in range(1, 7)
]
console.print(Columns(dati, equal=True, expand=True))

# Console.rule — separatore con titolo
console.rule("[bold red]Errori rilevati")
console.print("Timeout su 3 connessioni")
console.print("Certificato scaduto su web-04")
console.rule()

# Redirect stderr a Console separata
error_console = Console(stderr=True, style="bold red")
error_console.print("Errore critico: disco pieno su /dev/sda1")
```

`console.status()` e particolarmente utile per operazioni dove non si conosce il progresso percentuale — come connessioni di rete, query complesse o operazioni su API esterne. Lo spinner indica all'utente che il programma sta lavorando, prevenendo l'impressione di blocco.

### Inspect e debugging visuale

`rich.inspect` e uno strumento potente per esplorare oggetti Python direttamente nel terminale, utile sia per il debugging che per costruire comandi di diagnostica:

```python
from rich import inspect
from rich.console import Console

console = Console()

# Ispeziona un oggetto mostrando attributi, metodi e documentazione
import pathlib
inspect(pathlib.Path("/tmp"), methods=True)

# Uso pratico in un CLI di debug
@app.command()
def debug_config(config_path: Path = typer.Argument(...)):
    """Ispeziona il file di configurazione caricato."""
    import tomllib
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    inspect(config, title="Configurazione caricata")

# inspect con filtri
inspect(console, methods=True, private=False, title="Console Rich")
```

---

## Textual — TUI Framework

Textual e il framework di riferimento per la costruzione di applicazioni TUI (Terminal User Interface) complete in Python. Sviluppato da Textualize, lo stesso team dietro Rich, Textual porta nel terminale un paradigma di sviluppo ispirato al web: layout dichiarativo, fogli di stile CSS, sistema di eventi, widget riutilizzabili e un ciclo di vita dell'applicazione strutturato. A differenza di un semplice CLI che stampa output e termina, un'applicazione Textual occupa l'intero terminale e offre un'interfaccia interattiva persistente con pulsanti, input, tabelle scrollabili, schede e navigazione tra schermate.

Installazione: `pip install textual`

Textual si basa su Rich per il rendering e aggiunge sopra di esso un framework applicativo completo. Se Rich e il motore di rendering, Textual e il framework che gestisce il layout, gli eventi, lo stato e il ciclo di vita dell'applicazione.

### Architettura di un'app Textual

Ogni applicazione Textual estende la classe `App` e definisce il proprio layout tramite il metodo `compose()`:

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, DataTable
from textual.containers import Container, Horizontal, Vertical

class ServerDashboard(App):
    """Dashboard di monitoraggio server nel terminale."""

    CSS_PATH = "dashboard.tcss"  # Foglio di stile esterno
    BINDINGS = [
        ("q", "quit", "Esci"),
        ("r", "refresh", "Aggiorna"),
        ("d", "toggle_dark", "Tema scuro/chiaro"),
    ]

    def compose(self) -> ComposeResult:
        """Costruisce il layout dell'applicazione."""
        yield Header()
        with Container(id="main"):
            with Horizontal():
                yield Static("CPU: [green]23%[/green]", id="cpu-gauge")
                yield Static("RAM: [yellow]78%[/yellow]", id="ram-gauge")
                yield Static("Disco: [green]45%[/green]", id="disk-gauge")
            yield DataTable(id="server-table")
        yield Footer()

    def on_mount(self) -> None:
        """Evento di montaggio: popola la tabella iniziale."""
        table = self.query_one("#server-table", DataTable)
        table.add_columns("Hostname", "IP", "Stato", "CPU %", "RAM %")
        table.add_rows([
            ("web-01", "10.0.1.10", "Online", "23", "67"),
            ("web-02", "10.0.1.11", "Online", "45", "72"),
            ("db-01", "10.0.2.10", "Warning", "89", "91"),
        ])

    def action_refresh(self) -> None:
        """Azione collegata al keybinding 'r'."""
        self.notify("Dati aggiornati", severity="information")

    def action_toggle_dark(self) -> None:
        """Alterna tra tema scuro e chiaro."""
        self.dark = not self.dark

if __name__ == "__main__":
    app = ServerDashboard()
    app.run()
```

Il metodo `compose()` restituisce un albero di widget tramite `yield`. I container (`Container`, `Horizontal`, `Vertical`) organizzano il layout. `BINDINGS` mappa tasti a metodi `action_*`. Il metodo `on_mount()` viene invocato quando l'applicazione e pronta e tutti i widget sono stati montati nel DOM — il punto ideale per inizializzare dati.

### Widget e layout

Textual fornisce una libreria di widget pronti all'uso che copre i casi d'uso piu comuni:

```python
from textual.app import App, ComposeResult
from textual.widgets import (
    Input, Button, Label, Switch, Select,
    TextArea, ListView, ListItem, Tabs, Tab,
    ProgressBar, Sparkline, RichLog,
)
from textual.containers import VerticalScroll

class FormApp(App):
    """Form interattivo nel terminale."""

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("Configurazione Server")
            yield Input(placeholder="Hostname", id="hostname")
            yield Input(placeholder="Indirizzo IP", id="ip")
            yield Select(
                [("Ubuntu 24.04", "ubuntu"), ("Debian 12", "debian"),
                 ("Rocky 9", "rocky")],
                prompt="Sistema operativo",
                id="os-select",
            )
            yield Switch(value=False, id="monitoring")
            yield Label("Abilita monitoraggio", id="monitoring-label")
            yield Button("Crea Server", variant="primary", id="create-btn")
            yield RichLog(id="log", highlight=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gestisce il click sul pulsante."""
        if event.button.id == "create-btn":
            hostname = self.query_one("#hostname", Input).value
            ip = self.query_one("#ip", Input).value
            log = self.query_one("#log", RichLog)
            log.write(f"[green]Creazione server {hostname} ({ip})...[/green]")
```

I widget disponibili includono: `Input` per l'inserimento di testo, `Button` con varianti (`primary`, `success`, `warning`, `error`), `DataTable` per tabelle interattive con ordinamento, `TextArea` per editing multi-riga con syntax highlighting, `Select` per menu a tendina, `Switch` per toggle booleani, `ListView` per liste scrollabili, `Tabs` per schede, `ProgressBar` per indicatori di avanzamento, `RichLog` per log scrollabile con markup Rich, e `Sparkline` per grafici inline.

### CSS nel terminale

Textual adotta un sottoinsieme di CSS per lo stile dei widget. I fogli di stile possono essere definiti inline tramite la variabile di classe `CSS` o in file esterni `.tcss`:

```css
/* dashboard.tcss — foglio di stile Textual */
Screen {
    layout: vertical;
}

#main {
    layout: vertical;
    padding: 1 2;
    height: 1fr;
}

Horizontal {
    height: auto;
    padding: 1;
}

#server-table {
    height: 1fr;
    border: solid green;
    margin: 1 0;
}

#cpu-gauge, #ram-gauge, #disk-gauge {
    width: 1fr;
    content-align: center middle;
    border: round $accent;
    padding: 1;
    margin: 0 1;
}

Button {
    margin: 1 2;
}

Button:hover {
    background: $accent-lighten-1;
}

Button.-primary {
    background: $primary;
}
```

Le proprieta CSS supportate includono `layout` (vertical, horizontal, grid), `width`/`height` (con unita `fr`, `%`, numeri assoluti), `padding`, `margin`, `border`, `background`, `color`, `text-style`, `content-align`, `dock`, `display`, `visibility` e `overflow`. I selettori funzionano come nel CSS web: per tipo (`Button`), per id (`#main`), per classe (`.highlight`), e con pseudo-classi (`:hover`, `:focus`, `:disabled`). Le variabili di tema come `$accent`, `$primary`, `$background` si adattano automaticamente al tema scuro o chiaro.

### Schermate e navigazione

Per applicazioni multi-schermata, Textual fornisce il sistema di `Screen`:

```python
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable

class HomeScreen(Screen):
    """Schermata principale."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Dashboard Principale", id="title")
        yield Button("Gestione Server", id="btn-servers")
        yield Button("Configurazione", id="btn-config")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-servers":
            self.app.push_screen(ServerScreen())
        elif event.button.id == "btn-config":
            self.app.push_screen(ConfigScreen())

class ServerScreen(Screen):
    """Schermata di gestione server."""
    BINDINGS = [("escape", "app.pop_screen", "Indietro")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="servers")
        yield Button("Indietro", id="btn-back")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#servers", DataTable)
        table.add_columns("Nome", "Stato", "Uptime")
        table.add_rows([("web-01", "Online", "14d"), ("db-01", "Online", "30d")])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()

class InfraApp(App):
    SCREENS = {"home": HomeScreen}

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())
```

`push_screen()` aggiunge una schermata allo stack di navigazione, `pop_screen()` torna alla precedente. Questo modello permette di costruire applicazioni TUI con flussi di navigazione complessi, simili alle applicazioni mobile con stack di schermate. Ogni schermata ha il proprio ciclo di vita, i propri keybinding e il proprio layout CSS.

### Testing di app Textual

Textual include un framework di testing asincrono basato su `pilot`:

```python
import pytest
from textual.pilot import Pilot

async def test_dashboard_loads():
    """Verifica che la dashboard si carichi correttamente."""
    app = ServerDashboard()
    async with app.run_test() as pilot:
        # Verifica che la tabella sia presente
        table = app.query_one("#server-table", DataTable)
        assert table.row_count == 3

        # Simula la pressione del tasto 'r'
        await pilot.press("r")
        # Verifica che la notifica sia apparsa
        assert len(app._notifications) > 0

async def test_form_submission():
    """Verifica il submit del form."""
    app = FormApp()
    async with app.run_test() as pilot:
        # Compila il form
        hostname_input = app.query_one("#hostname", Input)
        await pilot.click(hostname_input)
        await pilot.press(*"web-03")

        # Premi il pulsante
        await pilot.click("#create-btn")

        # Verifica il log
        log = app.query_one("#log", RichLog)
        # Il log dovrebbe contenere il messaggio di creazione
```

Il `pilot` simula interazioni utente (click, pressione tasti, scroll) senza bisogno di un terminale reale. I test sono asincroni perche Textual usa `asyncio` internamente. Questo permette di eseguire test di integrazione completi delle applicazioni TUI nel contesto di una pipeline CI/CD senza display grafico.

Textual rappresenta un salto di paradigma per le applicazioni terminale Python: da semplici script sequenziali a vere applicazioni interattive con interfaccia grafica testuale. I casi d'uso tipici includono dashboard di monitoraggio, client di database interattivi, tool di gestione infrastruttura, file manager e editor di configurazione.

### Textual e il web: serve mode

Una caratteristica notevole di Textual e la possibilita di servire un'applicazione TUI tramite browser web, senza modificare il codice:

```bash
# Avvia l'app nel terminale (comportamento standard)
python dashboard.py

# Serve l'app via browser web
textual serve dashboard.py

# Serve su una porta specifica con accesso remoto
textual serve dashboard.py --host 0.0.0.0 --port 8080
```

Questa dualita permette di sviluppare una sola applicazione che funziona sia nel terminale locale sia come applicazione web accessibile da remoto. Il rendering nel browser sfrutta un terminale emulato via WebSocket, mantenendo l'esperienza identica. Per i team che gestiscono infrastruttura, questo significa poter accedere a una dashboard di monitoraggio sia dal terminale SSH che da un browser, con lo stesso codice.

### Reactive e data binding

Textual supporta attributi reattivi che aggiornano automaticamente l'interfaccia quando il valore cambia:

```python
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Static, Header

class CPUMonitor(App):
    """Monitor CPU con aggiornamento reattivo."""

    cpu_usage: reactive[float] = reactive(0.0)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="cpu-display")

    def watch_cpu_usage(self, old_value: float, new_value: float) -> None:
        """Callback automatico: invocato quando cpu_usage cambia."""
        display = self.query_one("#cpu-display", Static)
        if new_value > 90:
            display.update(f"[bold red]CPU: {new_value:.1f}% — CRITICO[/bold red]")
        elif new_value > 70:
            display.update(f"[yellow]CPU: {new_value:.1f}% — ATTENZIONE[/yellow]")
        else:
            display.update(f"[green]CPU: {new_value:.1f}%[/green]")

    def on_mount(self) -> None:
        """Aggiorna il valore ogni 2 secondi."""
        self.set_interval(2.0, self._update_cpu)

    def _update_cpu(self) -> None:
        import random
        self.cpu_usage = random.uniform(10.0, 100.0)
```

Il metodo `watch_<attributo>()` viene invocato automaticamente quando l'attributo reattivo cambia valore. Questo pattern elimina la necessita di aggiornamento manuale dei widget, riducendo il boilerplate e prevenendo lo stato inconsistente tra dati e visualizzazione. Il modello e analogo al data binding di framework web come Vue.js o Svelte, portato nel contesto del terminale.

---

## Prompt Toolkit

Prompt Toolkit e la libreria per costruire interfacce interattive sofisticate nel terminale. Va oltre il semplice `input()` offrendo completamento automatico, cronologia dei comandi, validazione in tempo reale, input multi-riga e rendering avanzato. E la stessa libreria su cui e costruito IPython.

Installazione: `pip install prompt_toolkit`

### Prompt interattivi con completamento

```python
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.validation import Validator

# Completamento automatico
commands = WordCompleter([
    "deploy", "rollback", "status", "logs", "config",
    "restart", "stop", "start", "scale", "migrate"
])

# Validazione in tempo reale
validator = Validator.from_callable(
    lambda text: len(text) > 0,
    error_message="Il comando non puo essere vuoto",
    move_cursor_to_end=True,
)

# Cronologia persistente
history = FileHistory(".myapp_history")

while True:
    try:
        user_input = prompt(
            "myapp> ",
            completer=commands,
            history=history,
            validator=validator,
            complete_while_typing=True,
        )
        if user_input.strip() == "exit":
            break
        print(f"Esecuzione: {user_input}")
    except KeyboardInterrupt:
        continue
    except EOFError:
        break
```

### Completamento avanzato e input multi-riga

```python
from prompt_toolkit import prompt
from prompt_toolkit.completion import NestedCompleter

# Completamento annidato: simula la struttura dei sotto-comandi
completer = NestedCompleter.from_nested_dict({
    "server": {
        "create": {"--name": None, "--cpu": None, "--ram": None},
        "delete": {"--force": None},
        "list": {"--format": {"json", "table", "csv"}},
    },
    "network": {
        "create": {"--cidr": None, "--name": None},
        "delete": None,
    },
    "help": None,
    "exit": None,
})

text = prompt("infra> ", completer=completer)

# Input multi-riga (utile per query SQL, template, ecc.)
from prompt_toolkit import prompt

sql = prompt(
    "SQL> ",
    multiline=True,
    prompt_continuation="...> ",
)
print(f"Query:\n{sql}")
```

### Validazione dell'input e stile personalizzato

Prompt Toolkit permette di validare l'input in tempo reale e personalizzare l'aspetto del prompt con stili e formattazione condizionale:

```python
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.styles import Style

class PortValidator(Validator):
    """Valida che l'input sia un numero di porta valido."""
    def validate(self, document):
        text = document.text
        if not text.isdigit():
            raise ValidationError(
                message="Inserire un numero intero",
                cursor_position=len(text),
            )
        port = int(text)
        if not (1 <= port <= 65535):
            raise ValidationError(
                message="La porta deve essere tra 1 e 65535",
                cursor_position=len(text),
            )

# Stile personalizzato per il prompt
custom_style = Style.from_dict({
    "prompt": "#00aa00 bold",        # Prompt verde grassetto
    "input": "#ffffff",               # Input bianco
    "completion-menu": "bg:#333333",  # Menu completamento sfondo scuro
})

port = prompt(
    [("class:prompt", "porta> ")],
    validator=PortValidator(),
    validate_while_typing=True,
    style=custom_style,
)
```

Un aspetto particolarmente utile di Prompt Toolkit e la possibilita di costruire shell interattive complete con prompt personalizzato, cronologia persistente tra sessioni, completamento contestuale e keybinding personalizzati. Strumenti come `pgcli` (client PostgreSQL interattivo), `mycli` (client MySQL) e `litecli` (client SQLite) sono tutti costruiti su Prompt Toolkit e dimostrano il livello di sofisticazione raggiungibile.

---

## Prompt interattivi: questionary e InquirerPy

Quando un CLI tool deve guidare l'utente attraverso una sequenza di scelte — selezionare un ambiente di deploy, scegliere componenti da installare, confermare operazioni — le librerie di prompt interattivi offrono un'esperienza superiore rispetto al semplice `input()`. Le due librerie di riferimento nell'ecosistema Python sono `questionary` e `InquirerPy`, entrambe ispirate a Inquirer.js del mondo Node.

### questionary

`questionary` offre un'API pulita e intuitiva per i casi d'uso piu comuni:

```bash
pip install questionary
```

```python
import questionary

# Selezione singola da una lista
env = questionary.select(
    "In quale ambiente vuoi deployare?",
    choices=["development", "staging", "production"],
).ask()

# Selezione multipla con checkbox
services = questionary.checkbox(
    "Quali servizi vuoi riavviare?",
    choices=[
        questionary.Choice("nginx", checked=True),
        questionary.Choice("postgres", checked=False),
        questionary.Choice("redis", checked=False),
        questionary.Choice("celery", checked=True),
    ],
).ask()

# Conferma booleana
if questionary.confirm("Procedere con il deploy in production?", default=False).ask():
    print("Deploy avviato...")

# Input testuale con validazione
port = questionary.text(
    "Porta del server:",
    default="8080",
    validate=lambda val: val.isdigit() and 1 <= int(val) <= 65535,
).ask()

# Password nascosta
secret = questionary.password("Token API:").ask()

# Selezione con auto-completamento
server = questionary.autocomplete(
    "Nome del server:",
    choices=["web-01", "web-02", "db-01", "db-replica", "cache-01"],
).ask()

# Percorso file con completamento del filesystem
filepath = questionary.path("File di configurazione:").ask()
```

`questionary` si integra bene con Typer e Click. Il pattern tipico consiste nell'usare prompt interattivi come fallback quando un argomento obbligatorio non viene fornito da riga di comando:

```python
import typer
import questionary

app = typer.Typer()

@app.command()
def deploy(
    env: str = typer.Argument(None),
    service: str = typer.Option(None, "--service", "-s"),
):
    """Deploy di un servizio."""
    if env is None:
        env = questionary.select(
            "Ambiente:", choices=["dev", "staging", "production"]
        ).ask()
    if service is None:
        service = questionary.select(
            "Servizio:", choices=["api", "web", "worker"]
        ).ask()
    typer.echo(f"Deploy di {service} in {env}")
```

### InquirerPy

`InquirerPy` e una reimplementazione moderna di PyInquirer con piu opzioni di personalizzazione, inclusa una potente modalita fuzzy per la ricerca nei menu lunghi:

```bash
pip install inquirerpy
```

```python
from InquirerPy import inquirer
from InquirerPy.validator import PathValidator

# Selezione con ricerca fuzzy — ideale per liste lunghe
server = inquirer.fuzzy(
    message="Seleziona server:",
    choices=["web-01-eu", "web-02-eu", "web-01-us", "db-primary-eu",
             "db-replica-eu", "cache-01-eu", "cache-02-us"],
    max_height="50%",
).execute()

# Selezione multipla con istruzioni personalizzate
components = inquirer.checkbox(
    message="Componenti da installare:",
    choices=["nginx", "certbot", "fail2ban", "prometheus-node-exporter",
             "filebeat", "auditd"],
    instruction="(Spazio per selezionare, Invio per confermare)",
).execute()

# Input con validazione del percorso
config_path = inquirer.filepath(
    message="Percorso configurazione:",
    default="/etc/myapp/",
    validate=PathValidator(is_file=True, message="Deve essere un file"),
).execute()

# Numero con validazione
workers = inquirer.number(
    message="Numero di worker:",
    min_allowed=1,
    max_allowed=32,
    default=4,
).execute()
```

InquirerPy supporta anche trasformazioni dell'output (mostrare un valore diverso da quello selezionato), filtri personalizzati, keybinding configurabili e temi con colori personalizzati.

### Confronto tra librerie di prompt

| Caratteristica | questionary | InquirerPy | Prompt Toolkit |
|----------------|-------------|------------|----------------|
| Facilita d'uso | Alta | Media | Bassa (piu potente) |
| Prompt fuzzy | No | Si | Manuale |
| Validazione | Callback | Classi Validator | Classi Validator |
| Stili/Temi | Limitati | Ampi | Completo controllo |
| Dipendenze | prompt_toolkit | prompt_toolkit | Nessuna |
| Caso d'uso ideale | Wizard semplici | Menu complessi | Shell interattive |

La scelta dipende dalla complessita: `questionary` per wizard lineari con poche domande, `InquirerPy` per menu con ricerca fuzzy e personalizzazione avanzata, `Prompt Toolkit` per shell interattive complete con cronologia e completamento contestuale.

---

## Output e Formattazione

Un CLI tool professionale deve produrre output adatto sia alla lettura umana che al consumo automatizzato da parte di altri script. La separazione tra output human-friendly e machine-readable e un principio cardine della progettazione CLI.

### Colori ANSI e compatibilita Windows

```python
# colorama: garantisce compatibilita colori su Windows
from colorama import init, Fore, Style

init(autoreset=True)  # Reset automatico dopo ogni print

print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} Servizio avviato")
print(f"{Fore.RED}[ERRORE]{Style.RESET_ALL} Connessione rifiutata")
print(f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} Disco al 90% di capacita")
```

Su sistemi moderni (Windows 10+, qualsiasi terminale Linux/macOS), i codici ANSI funzionano nativamente. `colorama` rimane utile per garantire compatibilita con terminali Windows piu vecchi, dove i codici ANSI non vengono interpretati nativamente. Una buona pratica consiste nel disabilitare i colori quando l'output viene redirezionato: la variabile `NO_COLOR` (standard de facto, vedi no-color.org) e il controllo `sys.stdout.isatty()` permettono al tool di adattarsi automaticamente al contesto.

### Output tabulare

```python
from tabulate import tabulate

data = [
    ["web-01", "10.0.1.10", "Online", "23%"],
    ["web-02", "10.0.1.11", "Offline", "0%"],
    ["db-01", "10.0.2.10", "Online", "67%"],
]
headers = ["Host", "IP", "Stato", "CPU"]

# Diversi formati di tabella
print(tabulate(data, headers=headers, tablefmt="grid"))
print(tabulate(data, headers=headers, tablefmt="github"))
print(tabulate(data, headers=headers, tablefmt="simple"))
```

### Output JSON e machine-readable

```python
import json
import sys

def output_result(data: dict, format: str = "table"):
    """Output flessibile: human-readable o machine-readable."""
    if format == "json":
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    elif format == "jsonl":
        # JSON Lines: una riga JSON per record — ideale per streaming
        for record in data.get("records", []):
            json.dump(record, sys.stdout, ensure_ascii=False)
            sys.stdout.write("\n")
    elif format == "csv":
        import csv
        writer = csv.DictWriter(sys.stdout, fieldnames=data["records"][0].keys())
        writer.writeheader()
        writer.writerows(data["records"])
    else:
        # Formato tabulare per lettura umana
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table()
        for key in data["records"][0]:
            table.add_column(key)
        for record in data["records"]:
            table.add_row(*[str(v) for v in record.values()])
        console.print(table)
```

Una pratica diffusa consiste nell'usare `--format` o `--output-format` per lasciare all'utente la scelta del formato. Quando l'output viene redirezionato tramite pipe, e buona norma disabilitare automaticamente i colori. Rich e Click lo fanno nativamente; con output manuale si controlla `sys.stdout.isatty()`.

Un pattern avanzato prevede la rilevazione automatica del contesto: se stdout e un terminale si usa il formato tabulare colorato; se e un pipe si passa automaticamente a JSON o plain text. Questo comportamento si implementa con un semplice controllo:

```python
import sys
import json

def smart_output(data: list[dict], forced_format: str | None = None):
    """Output intelligente che si adatta al contesto di esecuzione."""
    if forced_format:
        fmt = forced_format
    elif sys.stdout.isatty():
        fmt = "table"
    else:
        fmt = "json"

    if fmt == "json":
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    elif fmt == "table":
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table()
        if data:
            for key in data[0]:
                table.add_column(key)
            for row in data:
                table.add_row(*[str(v) for v in row.values()])
        console.print(table)
```

---

## Piping e Composizione Unix

Un CLI tool professionale si integra nella pipeline Unix. I programmi comunicano attraverso tre canali standard: **stdin** (file descriptor 0), **stdout** (fd 1) e **stderr** (fd 2). La filosofia Unix richiede che ogni tool legga da stdin, scriva i risultati su stdout e gli errori su stderr, permettendo composizione tramite pipe (`|`).

### Leggere da stdin

```python
import sys

def process_stdin():
    """Legge righe da stdin — funziona con pipe e redirezione."""
    if sys.stdin.isatty():
        print("Errore: nessun input da stdin. Uso: cat data.txt | myapp process",
              file=sys.stderr)
        sys.exit(1)

    for line in sys.stdin:
        # Processa ogni riga — strip() rimuove il newline finale
        processed = line.strip().upper()
        print(processed)  # Scrive su stdout — disponibile per la pipe successiva
```

### Pattern: accettare sia file che stdin

Il pattern universale e accettare un file come argomento, con `-` come alias per stdin:

```python
import sys
from pathlib import Path

def open_input(filepath: str | Path) -> "TextIO":
    """Apre un file o stdin se il percorso e '-'."""
    if str(filepath) == "-":
        return sys.stdin
    return open(filepath)

# Con Click — supporto nativo
@click.command()
@click.argument("input_file", type=click.File("r"), default="-")
def transform(input_file):
    """Trasforma l'input riga per riga."""
    for line in input_file:
        click.echo(line.strip().upper())

# Composizione Unix:
# cat access.log | myapp transform | grep ERROR | wc -l
# myapp transform access.log | sort | uniq -c | sort -rn
```

### Scrivere correttamente su stdout e stderr

La separazione e fondamentale per la composabilita:

```python
import sys
import json

def export_data(records: list[dict], verbose: bool = False):
    """
    Scrive i dati su stdout (machine-readable).
    Scrive messaggi di stato su stderr (human-readable).
    """
    if verbose:
        # I messaggi informativi vanno su stderr — non inquinano l'output
        print(f"Elaborazione di {len(records)} record...", file=sys.stderr)

    # I dati vanno su stdout — possono essere catturati dalla pipe
    for record in records:
        json.dump(record, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")

    if verbose:
        print(f"Esportazione completata.", file=sys.stderr)

# L'utente puo redirezionare separatamente:
# myapp export --verbose > data.jsonl 2> export.log
```

### Gestire BrokenPipeError

Quando l'output viene piped a un comando che chiude prematuramente (es. `head -5`), Python riceve un `BrokenPipeError`. Se non gestito, produce un traceback confuso:

```python
import sys
import signal

def main():
    # Ripristina il comportamento di default per SIGPIPE (terminazione silenziosa)
    # Necessario perche Python ignora SIGPIPE di default
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    try:
        for i in range(1_000_000):
            print(f"riga {i}")
    except BrokenPipeError:
        # Chiudi stderr per evitare un secondo errore durante il cleanup
        sys.stderr.close()
        sys.exit(0)

# Ora funziona: myapp generate | head -5
```

La documentazione ufficiale di Python (docs.python.org/3/library/signal.html) conferma che `signal.signal(signal.SIGPIPE, signal.SIG_DFL)` e l'approccio raccomandato per i CLI tool che producono output piped.

---

## Exit Codes

Gli exit code sono il contratto tra un CLI tool e il sistema operativo (o lo script che lo invoca). Un exit code 0 indica successo; qualsiasi altro valore indica un errore. La convenzione POSIX definisce i valori standard, e un tool professionale li rispetta rigorosamente.

### Convenzioni standard

| Codice | Significato | Uso |
|--------|-------------|-----|
| 0 | Successo | L'operazione e stata completata correttamente |
| 1 | Errore generico | Errore applicativo non categorizzato |
| 2 | Errore di utilizzo | Argomenti errati, sintassi non valida (convenzione argparse) |
| 64-78 | Errori BSD `sysexits.h` | Vedere sotto |
| 126 | Non eseguibile | Il file esiste ma non e eseguibile |
| 127 | Comando non trovato | Il comando non esiste nel PATH |
| 128+N | Terminato da segnale N | Es. 130 = SIGINT (Ctrl+C), 137 = SIGKILL, 143 = SIGTERM |

I codici BSD (`/usr/include/sysexits.h`) forniscono una categorizzazione piu fine:

| Codice | Nome | Significato |
|--------|------|-------------|
| 64 | EX_USAGE | Errore di utilizzo della riga di comando |
| 65 | EX_DATAERR | Dati di input errati |
| 66 | EX_NOINPUT | File di input non trovato o non leggibile |
| 69 | EX_UNAVAILABLE | Servizio non disponibile |
| 70 | EX_SOFTWARE | Errore software interno |
| 73 | EX_CANTCREAT | Impossibile creare il file di output |
| 74 | EX_IOERR | Errore di I/O |
| 77 | EX_NOPERM | Permesso negato |
| 78 | EX_CONFIG | Errore di configurazione |

### Implementazione pratica

```python
import sys
from enum import IntEnum

class ExitCode(IntEnum):
    """Exit code per il CLI tool."""
    SUCCESS = 0
    GENERIC_ERROR = 1
    USAGE_ERROR = 2
    INPUT_ERROR = 65
    SERVICE_UNAVAILABLE = 69
    INTERNAL_ERROR = 70
    IO_ERROR = 74
    PERMISSION_ERROR = 77
    CONFIG_ERROR = 78
    INTERRUPTED = 130  # SIGINT (Ctrl+C)

def main() -> int:
    """Funzione main che restituisce un exit code."""
    try:
        config = load_config()
    except FileNotFoundError:
        print("Errore: file di configurazione non trovato", file=sys.stderr)
        return ExitCode.CONFIG_ERROR
    except PermissionError:
        print("Errore: permesso negato sul file di configurazione", file=sys.stderr)
        return ExitCode.PERMISSION_ERROR

    try:
        result = process(config)
    except ConnectionError:
        print("Errore: servizio non raggiungibile", file=sys.stderr)
        return ExitCode.SERVICE_UNAVAILABLE
    except Exception as e:
        print(f"Errore interno: {e}", file=sys.stderr)
        return ExitCode.INTERNAL_ERROR

    print(result)
    return ExitCode.SUCCESS

if __name__ == "__main__":
    sys.exit(main())
```

Con Click e Typer, `sys.exit()` viene chiamato automaticamente dal framework. Per controllare l'exit code, si solleva `click.exceptions.Exit(code)` o `raise typer.Exit(code)`.

---

## Gestione Segnali

I segnali Unix permettono al sistema operativo e all'utente di comunicare con i processi in esecuzione. Un CLI tool robusto deve gestire almeno `SIGINT` (Ctrl+C) e `SIGTERM` (invio da `kill` o da orchestratori container) per eseguire cleanup ordinato.

### SIGINT — Ctrl+C

```python
import signal
import sys

# Approccio 1: signal handler
def handle_sigint(signum: int, frame) -> None:
    """Cleanup ordinato su Ctrl+C."""
    print("\nOperazione interrotta dall'utente.", file=sys.stderr)
    cleanup()
    sys.exit(130)  # 128 + 2 (SIGINT)

signal.signal(signal.SIGINT, handle_sigint)

# Approccio 2: try/except KeyboardInterrupt (piu Pythonico per script semplici)
try:
    for item in elabora_batch():
        process(item)
except KeyboardInterrupt:
    print("\nInterrotto. Pulizia in corso...", file=sys.stderr)
    cleanup()
    sys.exit(130)
```

### SIGTERM — terminazione da orchestratore

```python
import signal
import sys
import threading

# Flag per shutdown graceful
shutdown_event = threading.Event()

def handle_sigterm(signum: int, frame) -> None:
    """Segnala alle goroutine di terminare."""
    print("Ricevuto SIGTERM — avvio shutdown graceful...", file=sys.stderr)
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_sigterm)

def worker_loop():
    """Worker che rispetta il segnale di shutdown."""
    while not shutdown_event.is_set():
        task = get_next_task()
        if task is None:
            shutdown_event.wait(timeout=1.0)
            continue
        process(task)  # Completa il task corrente prima di uscire

    print("Worker terminato ordinatamente.", file=sys.stderr)
```

### Pattern di cleanup con context manager

Il modo piu robusto per garantire il cleanup e combinare i segnali con i context manager:

```python
import signal
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def graceful_shutdown(cleanup_func=None):
    """Context manager che gestisce SIGINT e SIGTERM con cleanup."""
    original_sigint = signal.getsignal(signal.SIGINT)
    original_sigterm = signal.getsignal(signal.SIGTERM)

    def handler(signum, frame):
        sig_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        print(f"\nRicevuto {sig_name} — cleanup in corso...", file=sys.stderr)
        if cleanup_func:
            cleanup_func()
        sys.exit(128 + signum)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    try:
        yield
    finally:
        # Ripristina i handler originali
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)

# Uso
def main():
    temp_files: list[Path] = []

    def cleanup():
        for f in temp_files:
            f.unlink(missing_ok=True)
        print(f"Rimossi {len(temp_files)} file temporanei.", file=sys.stderr)

    with graceful_shutdown(cleanup_func=cleanup):
        for batch in iterate_batches():
            tmp = Path(tempfile.mktemp(suffix=".json"))
            temp_files.append(tmp)
            process_and_write(batch, tmp)
            upload(tmp)
            tmp.unlink()
            temp_files.remove(tmp)
```

---

## Logging nelle applicazioni CLI

Il logging e un aspetto critico delle applicazioni CLI professionali. A differenza di un'applicazione web che scrive log su file e li invia a un aggregatore, un CLI tool deve bilanciare tra output informativo per l'utente (stderr) e log strutturati per il debug e l'auditing. La sfida principale e integrare il sistema di logging standard di Python con i livelli di verbosita tipici dei CLI (`-v`, `-vv`, `-vvv`) senza inquinare l'output su stdout che potrebbe essere consumato da una pipe.

### Integrazione con i livelli di verbosita

Il pattern standard mappa i flag `-v` ripetuti ai livelli del modulo `logging`:

```python
import logging
import sys

def configure_logging(verbosity: int) -> None:
    """
    Configura il logging in base al livello di verbosita.
    -v    = WARNING  (solo avvisi e errori)
    -vv   = INFO     (operazioni normali)
    -vvv  = DEBUG    (tutto, incluso diagnostica dettagliata)
    nessun flag = ERROR (solo errori)
    """
    levels = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }
    level = levels.get(min(verbosity, 3), logging.DEBUG)

    # Log su stderr — non inquina stdout per le pipe
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

# Integrazione con argparse
parser.add_argument("-v", "--verbose", action="count", default=0,
                    help="Aumenta verbosita (-v, -vv, -vvv)")
args = parser.parse_args()
configure_logging(args.verbose)

logger = logging.getLogger("myapp")
logger.debug("Diagnostica dettagliata: connessione al DB con pool_size=10")
logger.info("Elaborazione avviata per 150 record")
logger.warning("Timeout su web-03, tentativo di retry")
logger.error("Connessione rifiutata: database non raggiungibile")
```

Con Click e Typer, il pattern e analogo — il conteggio di `-v` viene passato a `configure_logging()` nel callback del gruppo principale. E fondamentale che il logging venga configurato una sola volta, il piu vicino possibile all'entry point dell'applicazione, per evitare handler duplicati che producono messaggi ripetuti.

Una pratica importante consiste nel silenziare le librerie di terze parti che producono log verbosi. Quando si imposta il livello globale a `DEBUG`, librerie come `urllib3`, `httpx` o `asyncio` inondano lo stderr con messaggi irrilevanti per l'utente del CLI:

```python
def configure_logging(verbosity: int) -> None:
    """Configurazione con silenziamento selettivo."""
    level = {0: logging.ERROR, 1: logging.WARNING,
             2: logging.INFO, 3: logging.DEBUG}.get(min(verbosity, 3))

    logging.basicConfig(level=level, stream=sys.stderr,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # Silenzia le librerie rumorose anche in modalita DEBUG
    for noisy in ("urllib3", "httpx", "asyncio", "httpcore", "botocore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
```

### Logging strutturato con structlog

Per CLI tool che producono log destinati a sistemi di aggregazione (ELK, Loki, Datadog), il logging strutturato in formato JSON e superiore al testo libero. `structlog` e la libreria di riferimento:

```bash
pip install structlog
```

```python
import structlog
import sys

def setup_structlog(json_output: bool = False) -> None:
    """
    Configura structlog.
    json_output=True: log JSON per produzione / aggregazione.
    json_output=False: log colorato per sviluppo locale.
    """
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )

logger = structlog.get_logger()

# Log con contesto strutturato — ogni campo e un valore parsabile
logger.info("deploy_started", env="production", service="api", version="2.1.0")
logger.warning("retry_scheduled", attempt=3, max_retries=5, delay_ms=2000)
logger.error("connection_failed", host="db-primary", port=5432, error="timeout")

# Contesto aggiunto progressivamente — tutte le righe successive lo includeranno
structlog.contextvars.bind_contextvars(request_id="abc-123", user="admin")
logger.info("operation_completed", records_processed=1500)
```

In modalita JSON, ogni riga di log e un oggetto JSON parsabile da `jq`, Loki o Elasticsearch. In modalita sviluppo, lo stesso codice produce output colorato leggibile. Questa dualita permette di usare lo stesso tool sia interattivamente che in una pipeline CI/CD.

### Rich logging handler

Rich fornisce un handler per il modulo `logging` che produce output colorato con timestamp, livelli evidenziati e traceback formattati:

```python
import logging
from rich.logging import RichHandler

# Sostituisce il handler standard con quello di Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(
        rich_tracebacks=True,         # Traceback formattati con syntax highlighting
        tracebacks_show_locals=True,  # Mostra le variabili locali nel traceback
        show_path=True,               # Mostra il file e la riga sorgente
        markup=True,                  # Abilita markup Rich nei messaggi
    )],
)

logger = logging.getLogger("myapp")
logger.info("Server avviato su [bold cyan]porta 8080[/bold cyan]")
logger.warning("Certificato SSL scade tra [yellow]7 giorni[/yellow]")

try:
    result = 1 / 0
except Exception:
    logger.exception("Errore nel calcolo")  # Traceback formattato da Rich
```

`RichHandler` e particolarmente efficace per i CLI tool interattivi dove l'utente legge i log direttamente nel terminale. Per i tool che producono log su file o per pipeline, si preferisce il formato JSON con structlog o il formato standard di logging.

### Rotazione dei log e file handler

Per CLI tool di lunga durata (daemon, watcher, pipeline che girano per ore), la rotazione dei log previene la crescita illimitata dei file:

```python
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

def setup_file_logging(log_dir: Path, max_bytes: int = 10_485_760) -> None:
    """Configura logging su file con rotazione."""
    log_dir.mkdir(parents=True, exist_ok=True)

    # Rotazione per dimensione: max 10 MB, mantiene 5 backup
    size_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=max_bytes,
        backupCount=5,
        encoding="utf-8",
    )
    size_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    # Rotazione per tempo: un file al giorno, mantiene 30 giorni
    time_handler = TimedRotatingFileHandler(
        log_dir / "app-daily.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    time_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    root = logging.getLogger()
    root.addHandler(size_handler)
    root.addHandler(time_handler)
```

La combinazione di handler console (stderr, con colori se terminale) e handler file (con rotazione) permette di avere sia feedback immediato per l'utente che audit trail persistente per il debugging post-mortem.

---

## Auto-completamento Shell

L'auto-completamento nel terminale migliora drasticamente l'usabilita di un CLI tool. L'utente preme Tab e vede i comandi disponibili, le opzioni e talvolta anche i valori possibili (nomi di file, ambienti di deploy, nomi di server).

### argcomplete

`argcomplete` aggiunge il completamento automatico ai parser argparse esistenti con modifiche minime:

```bash
pip install argcomplete
```

```python
#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK  — questo commento attiva il completamento globale
import argparse
import argcomplete

def server_completer(prefix, parsed_args, **kwargs):
    """Completer personalizzato che suggerisce nomi di server."""
    # In un caso reale, questa funzione interrogherebbe un inventario
    servers = ["web-01", "web-02", "db-01", "db-replica", "cache-01"]
    return [s for s in servers if s.startswith(prefix)]

parser = argparse.ArgumentParser(prog="infractl")
subparsers = parser.add_subparsers(dest="command")

ssh_parser = subparsers.add_parser("ssh")
ssh_parser.add_argument("server", help="Nome del server"
                        ).completer = server_completer

deploy_parser = subparsers.add_parser("deploy")
deploy_parser.add_argument("--env", choices=["dev", "staging", "production"])

argcomplete.autocomplete(parser)  # DEVE precedere parse_args()
args = parser.parse_args()
```

Attivazione del completamento:

```bash
# Per singolo script
eval "$(register-python-argcomplete infractl)"

# Globale — attiva per tutti gli script con il commento PYTHON_ARGCOMPLETE_OK
activate-global-python-argcomplete

# Persistente in .bashrc / .zshrc
echo 'eval "$(register-python-argcomplete infractl)"' >> ~/.bashrc
```

### shellingham — rilevazione della shell

`shellingham` rileva automaticamente quale shell sta usando l'utente, utile per generare lo script di completamento corretto:

```python
import shellingham

try:
    shell_name, shell_path = shellingham.detect_shell()
    print(f"Shell rilevata: {shell_name} ({shell_path})")
    # shell_name sara "bash", "zsh", "fish", "powershell", ecc.
except shellingham.ShellDetectionFailure:
    shell_name = "bash"  # fallback

# Genera lo script di completamento per la shell corretta
if shell_name == "bash":
    generate_bash_completion()
elif shell_name == "zsh":
    generate_zsh_completion()
elif shell_name == "fish":
    generate_fish_completion()
```

Typer usa internamente `shellingham` per il suo comando `--install-completion`, che rileva la shell e installa lo script automaticamente.

### Completamento dinamico con Click

Click supporta completamento personalizzato per valori che dipendono dal contesto (es. nomi di risorse che cambiano nel tempo):

```python
import click

class EnvironmentType(click.ParamType):
    name = "environment"

    def shell_complete(self, ctx, param, incomplete):
        """Fornisce suggerimenti per il completamento shell."""
        environments = load_environments()  # Da un file o API
        return [
            click.shell_completion.CompletionItem(env)
            for env in environments
            if env.startswith(incomplete)
        ]

@click.command()
@click.option("--env", type=EnvironmentType(), help="Ambiente di deploy")
def deploy(env):
    click.echo(f"Deploy in {env}")
```

---

## Configurazione

Un CLI tool maturo accetta configurazione da fonti multiple con una gerarchia di precedenza ben definita. La convenzione universalmente accettata e: **argomenti da riga di comando > variabili d'ambiente > file di configurazione > valori di default**.

### File di configurazione (TOML, YAML, INI)

```python
# --- TOML (formato raccomandato per Python, nativo dalla 3.11) ---
import tomllib  # Python 3.11+, altrimenti: pip install tomli

def load_toml_config(path: str) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)

# config.toml
# [server]
# host = "0.0.0.0"
# port = 8080
#
# [database]
# url = "postgresql://localhost/mydb"
# pool_size = 10

# --- YAML ---
import yaml  # pip install pyyaml

def load_yaml_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)

# --- INI ---
import configparser

def load_ini_config(path: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(path)
    return config
```

### Variabili d'ambiente

```python
import os

# Lettura diretta
db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
debug = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")
port = int(os.environ.get("PORT", "8080"))

# Con Click: envvar automatica
@click.command()
@click.option("--db-url", envvar="DATABASE_URL", help="URL del database")
@click.option("--port", envvar="PORT", type=int, default=8080, help="Porta")
def serve(db_url, port):
    click.echo(f"Server su porta {port}, DB: {db_url}")
```

### Posizioni standard dei file di configurazione

```python
from pathlib import Path
import os

def find_config() -> Path | None:
    """Cerca il file di configurazione nelle posizioni standard."""
    # 1. Variabile d'ambiente esplicita
    env_config = os.environ.get("MYAPP_CONFIG")
    if env_config:
        path = Path(env_config)
        if path.exists():
            return path

    # 2. Directory corrente
    local = Path("myapp.toml")
    if local.exists():
        return local

    # 3. XDG config directory (Linux/macOS)
    xdg_config = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    xdg_path = Path(xdg_config) / "myapp" / "config.toml"
    if xdg_path.exists():
        return xdg_path

    # 4. Home directory (fallback classico)
    home_config = Path.home() / ".myapp.toml"
    if home_config.exists():
        return home_config

    return None
```

### Precedenza della configurazione

```python
import os
import tomllib
from dataclasses import dataclass, field

@dataclass
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 8080
    debug: bool = False
    log_level: str = "INFO"
    db_url: str = "sqlite:///app.db"

def build_config(cli_args: dict) -> AppConfig:
    """
    Costruisce la configurazione con precedenza:
    CLI > Variabili d'ambiente > File di configurazione > Default
    """
    config = AppConfig()  # 4. Default

    # 3. File di configurazione
    config_path = find_config()
    if config_path:
        with open(config_path, "rb") as f:
            file_config = tomllib.load(f)
        server = file_config.get("server", {})
        if "host" in server:
            config.host = server["host"]
        if "port" in server:
            config.port = server["port"]
        if "debug" in server:
            config.debug = server["debug"]

    # 2. Variabili d'ambiente
    if env_host := os.environ.get("MYAPP_HOST"):
        config.host = env_host
    if env_port := os.environ.get("MYAPP_PORT"):
        config.port = int(env_port)
    if os.environ.get("MYAPP_DEBUG", "").lower() in ("true", "1"):
        config.debug = True

    # 1. Argomenti CLI (massima precedenza)
    for key, value in cli_args.items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)

    return config
```

### Configurazione TOML con validazione

Per i tool piu sofisticati, la configurazione viene validata con Pydantic o con dataclass e validazione manuale:

```python
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8080
    workers: int = 4

    def __post_init__(self):
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Porta non valida: {self.port}")
        if self.workers < 1:
            raise ValueError(f"Numero worker non valido: {self.workers}")

@dataclass
class DatabaseConfig:
    url: str = "sqlite:///app.db"
    pool_size: int = 5
    echo: bool = False

@dataclass
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    log_level: str = "INFO"

    @classmethod
    def from_toml(cls, path: Path) -> "AppConfig":
        """Carica la configurazione da un file TOML con validazione."""
        with open(path, "rb") as f:
            raw = tomllib.load(f)

        server = ServerConfig(**raw.get("server", {}))
        database = DatabaseConfig(**raw.get("database", {}))
        log_level = raw.get("log_level", "INFO")

        return cls(server=server, database=database, log_level=log_level)
```

---

## Distribuzione CLI

Creare un tool funzionante e metterlo a disposizione degli utenti sono due sfide distinte. Python offre diversi percorsi di distribuzione, ciascuno adatto a scenari differenti.

### Entry points in pyproject.toml

Il meccanismo standard per esporre un pacchetto Python come comando CLI e la sezione `[project.scripts]` in `pyproject.toml`:

```toml
[project]
name = "myinfratool"
version = "1.2.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
]

[project.scripts]
infra = "myinfratool.cli:main"
infra-admin = "myinfratool.admin:main"
```

Dopo `pip install .` (o `pip install -e .` per lo sviluppo), i comandi `infra` e `infra-admin` diventano disponibili nel PATH. Il formato e `nome_comando = "modulo.percorso:funzione"`. La funzione specificata deve essere callable senza argomenti — e il punto di ingresso effettivo del CLI.

Quando si usa `pip install -e .` (installazione in modalita "editable"), le modifiche al codice sorgente sono immediatamente riflesse nel comando installato, senza bisogno di reinstallare. Questo accelera enormemente il ciclo di sviluppo.

Struttura tipica del progetto:

```
myinfratool/
├── pyproject.toml
├── src/
│   └── myinfratool/
│       ├── __init__.py
│       ├── cli.py          # Entry point principale
│       ├── admin.py        # Entry point admin
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── deploy.py
│       │   └── monitor.py
│       └── utils/
│           ├── __init__.py
│           └── config.py
└── tests/
    ├── test_cli.py
    └── test_commands/
```

### pipx per la distribuzione

`pipx` installa applicazioni Python CLI in ambienti virtuali isolati, evitando conflitti di dipendenze con il sistema o altri tool:

```bash
# Installazione di pipx
pip install --user pipx
pipx ensurepath

# Installazione di un CLI tool
pipx install myinfratool
pipx install httpie
pipx install black

# Installazione da repository Git
pipx install git+https://github.com/user/myinfratool.git

# Aggiornamento
pipx upgrade myinfratool
pipx upgrade-all

# Esecuzione temporanea senza installazione permanente
pipx run cowsay "Ciao dal CLI"
```

`pipx` e il metodo raccomandato per distribuire CLI Python agli utenti finali che non devono importare il pacchetto come libreria. Ogni tool vive nel proprio virtualenv isolato, eliminando il rischio di conflitti tra dipendenze.

### Eseguibili standalone

Per distribuire un CLI senza richiedere che l'utente abbia Python installato, si ricorre a strumenti che impacchettano interprete e dipendenze in un unico eseguibile:

```bash
# PyInstaller: il piu diffuso, supporta Windows, macOS, Linux
pip install pyinstaller
pyinstaller --onefile --name infra src/myinfratool/cli.py

# L'eseguibile si trova in dist/infra (o dist/infra.exe su Windows)

# Opzioni utili di PyInstaller
pyinstaller \
    --onefile \
    --name infra \
    --icon assets/icon.ico \
    --add-data "templates:templates" \
    --hidden-import rich.traceback \
    src/myinfratool/cli.py

# Nuitka: compila Python in C, prestazioni migliori
pip install nuitka
nuitka --standalone --onefile --output-filename=infra src/myinfratool/cli.py
```

PyInstaller e la scelta piu pragmatica: ampia compatibilita, buona documentazione, community attiva. Nuitka produce eseguibili piu piccoli e performanti ma ha tempi di compilazione significativamente piu lunghi. Entrambi supportano le tre piattaforme principali, ma l'eseguibile deve essere compilato sulla piattaforma di destinazione — non e possibile cross-compilare un binario Linux da Windows.

### shiv e zipapp

Un'alternativa leggera a PyInstaller e il formato zipapp: un archivio ZIP eseguibile che contiene il codice Python e le dipendenze, ma richiede che l'utente abbia un interprete Python installato. `shiv` (sviluppato da LinkedIn) automatizza la creazione di zipapp con le dipendenze incluse:

```bash
pip install shiv

# Crea uno zipapp dal pacchetto corrente
shiv -c infra -o dist/infra.pyz .

# Crea uno zipapp da un pacchetto PyPI
shiv -c httpie -o dist/http.pyz httpie

# Con Python specifico e ambiente di compilazione
shiv -c myapp -o dist/myapp.pyz \
    --python "/usr/bin/python3.12" \
    --compressed \
    -r requirements.txt .
```

Il file `.pyz` risultante e un singolo file eseguibile: `./dist/infra.pyz server list`. All'interno, shiv scompatta le dipendenze in una directory di cache (`~/.shiv/`) al primo avvio e le riusa nelle esecuzioni successive. Questo garantisce tempi di avvio rapidi dopo la prima esecuzione.

Per casi piu semplici, il modulo `zipapp` della libreria standard crea archivi ZIP eseguibili senza dipendenze esterne:

```python
# Creazione manuale con il modulo zipapp
import zipapp

zipapp.create_archive(
    source="src/myapp",          # Directory sorgente
    target="dist/myapp.pyz",     # File di output
    main="cli:main",             # Funzione di ingresso (modulo:funzione)
    interpreter="/usr/bin/env python3",
    compressed=True,
)
```

```bash
# Equivalente da riga di comando
python -m zipapp src/myapp -o dist/myapp.pyz -m "cli:main" -c
```

Il vantaggio principale di zipapp/shiv rispetto a PyInstaller e la dimensione: un file `.pyz` pesa tipicamente pochi megabyte perche non include l'interprete Python, contro le decine di megabyte di un eseguibile PyInstaller `--onefile`. Lo svantaggio e la dipendenza da un interprete Python preinstallato sulla macchina di destinazione.

| Approccio | Include Python | Dimensione tipica | Caso d'uso |
|-----------|---------------|-------------------|------------|
| PyInstaller `--onefile` | Si | 30-100 MB | Distribuzione a utenti senza Python |
| Nuitka `--onefile` | Si | 15-50 MB | Prestazioni native |
| shiv / zipapp | No | 2-10 MB | Distribuzione interna, server con Python |
| pipx | No (usa venv) | Variabile | Installazione isolata da PyPI |

---

## Generazione di man page

Le pagine di manuale (man page) sono il sistema di documentazione nativo dei sistemi Unix. Anche se molti utenti moderni preferiscono `--help`, le man page offrono documentazione piu dettagliata, navigabile con paginazione, ricerca e link interni. Per CLI tool distribuiti su sistemi Linux, la presenza di una man page e un segno di maturita e professionalita.

### argparse-manpage

`argparse-manpage` genera automaticamente man page in formato groff a partire da un parser argparse esistente:

```bash
pip install argparse-manpage

# Genera la man page da un modulo Python
argparse-manpage --module myapp.cli --function get_parser \
    --author "Nome Autore" \
    --project-name "myapp" \
    --url "https://github.com/user/myapp" \
    > man/myapp.1

# Visualizza la man page generata
man ./man/myapp.1
```

L'integrazione con `setuptools` permette di generare le man page automaticamente durante il build:

```python
# setup.cfg o pyproject.toml
# [options]
# ...
#
# [build_manpages]
# manpages =
#     man/myapp.1:function=get_parser:module=myapp.cli
```

### click-man

Per applicazioni basate su Click, `click-man` genera man page dai comandi Click:

```bash
pip install click-man

# Genera man page per tutti i comandi di un gruppo Click
python -m click_man.cli myapp.cli:cli --target man/

# Risultato: man/myapp.1, man/myapp-deploy.1, man/myapp-server.1, ecc.
```

`click-man` genera una man page separata per ogni sotto-comando, seguendo la convenzione Unix (es. `git-commit(1)`, `git-push(1)`). Ogni pagina include la sinossi, la descrizione, le opzioni con i valori di default, e i riferimenti incrociati agli altri sotto-comandi.

### Struttura di una man page

Per i casi in cui la generazione automatica non e sufficiente, una man page puo essere scritta manualmente in formato groff:

```groff
.TH MYAPP 1 "2026-05-24" "myapp 2.0" "Comandi Utente"
.SH NOME
myapp \- gestione infrastruttura server
.SH SINOSSI
.B myapp
[\fIOPZIONI\fR]
.I comando
[\fIARGOMENTI\fR]
.SH DESCRIZIONE
\fBmyapp\fR e un tool per la gestione dell'infrastruttura server.
Supporta operazioni di deploy, monitoraggio e configurazione.
.SH COMANDI
.TP
\fBdeploy\fR \fIambiente\fR
Esegue il deploy nell'ambiente specificato.
.TP
\fBstatus\fR [\fB\-\-detailed\fR]
Mostra lo stato dell'infrastruttura.
.SH OPZIONI
.TP
\fB\-v\fR, \fB\-\-verbose\fR
Aumenta la verbosita dell'output.
.TP
\fB\-\-config\fR \fIPATH\fR
Specifica il file di configurazione (default: ~/.myapp.toml).
.SH EXIT STATUS
.TP
0
Successo.
.TP
1
Errore generico.
.TP
78
Errore di configurazione.
.SH FILE
.TP
~/.myapp.toml
File di configurazione utente.
.TP
~/.config/myapp/
Directory di configurazione XDG.
.SH VEDERE ANCHE
\fBmyapp-deploy\fR(1), \fBmyapp-status\fR(1)
```

La man page si installa tipicamente nella directory `share/man/man1/` durante il packaging. Per verificare la formattazione durante lo sviluppo: `man -l man/myapp.1`.

### Integrazione nel build system

Per automatizzare la generazione delle man page durante il processo di build, si aggiunge un target nel `Makefile` o nel `justfile`:

```makefile
# Makefile
.PHONY: man
man:
	mkdir -p man
	argparse-manpage \
		--module myapp.cli --function get_parser \
		--author "Nome Autore" \
		--project-name myapp \
		> man/myapp.1
	gzip -f man/myapp.1

install-man: man
	install -d $(DESTDIR)/usr/share/man/man1
	install -m 644 man/myapp.1.gz $(DESTDIR)/usr/share/man/man1/
```

Per progetti che usano `pyproject.toml` con `hatch` o `setuptools`, la man page puo essere inclusa come file di dati nel pacchetto distribuibile, garantendo che venga installata automaticamente con `pip install`.

Un approccio alternativo e generare la documentazione in formato Markdown e convertirla in man page con `pandoc`:

```bash
# Converti Markdown in man page con pandoc
pandoc --standalone --to man docs/myapp.1.md -o man/myapp.1

# Il file Markdown sorgente e piu facile da mantenere:
# % MYAPP(1) myapp 2.0 | Comandi Utente
# % Nome Autore
# % Maggio 2026
#
# # NOME
# myapp - gestione infrastruttura server
#
# # SINOSSI
# **myapp** [*OPZIONI*] *comando* [*ARGOMENTI*]
```

Questo approccio ha il vantaggio di mantenere la documentazione in un formato leggibile e versionabile (Markdown) mentre produce output nativo per il sistema `man`. Il costo e la dipendenza da `pandoc`, ma per la maggior parte degli ambienti di build questo non rappresenta un problema.

---

## Testing avanzato di CLI

Oltre alle tecniche di testing con `CliRunner` gia descritte nelle sezioni su Click e Typer, esistono strumenti e strategie complementari per garantire la qualita di applicazioni CLI complesse.

### pytest-console-scripts

`pytest-console-scripts` e un plugin pytest che testa i comandi CLI installati come entry point, eseguendoli come processi separati o in-process. A differenza di `CliRunner` che simula l'invocazione, `pytest-console-scripts` puo testare il vero eseguibile installato:

```bash
pip install pytest-console-scripts
```

```python
# conftest.py — nessuna configurazione necessaria, il plugin si attiva automaticamente

# test_cli_scripts.py
def test_help_output(script_runner):
    """Verifica che --help funzioni sull'entry point installato."""
    result = script_runner.run("myapp", "--help")
    assert result.success
    assert "Gestione infrastruttura" in result.stdout

def test_version(script_runner):
    """Verifica il flag --version."""
    result = script_runner.run("myapp", "--version")
    assert result.success
    assert "2.0.0" in result.stdout

def test_deploy_dry_run(script_runner):
    """Verifica che --dry-run non esegua operazioni reali."""
    result = script_runner.run("myapp", "deploy", "--env", "staging",
                                "--dry-run")
    assert result.success
    assert "DRY RUN" in result.stdout
    assert "deploy completato" not in result.stdout.lower()

def test_invalid_args(script_runner):
    """Verifica che argomenti non validi producano exit code 2."""
    result = script_runner.run("myapp", "--nonexistent-flag")
    assert not result.success
    assert result.returncode == 2

def test_stdin_processing(script_runner):
    """Verifica la lettura da stdin."""
    result = script_runner.run("myapp", "transform", "-",
                                stdin="riga1\nriga2\n")
    assert result.success
    assert "RIGA1" in result.stdout
```

Il fixture `script_runner` supporta sia l'esecuzione in-process (piu veloce, utile per la maggior parte dei test) che l'esecuzione come subprocess (necessaria per testare il vero packaging con entry_points). La modalita si configura nel file `pyproject.toml`:

```toml
[tool.pytest.ini_options]
script_launch_mode = "inprocess"  # oppure "subprocess" o "both"
```

### Strategie di test per CLI complessi

Per CLI con molti sotto-comandi e opzioni, una strategia di testing strutturata e essenziale:

**Test a livelli:**

```python
import pytest
from click.testing import CliRunner

# 1. Test unitari: logica di business senza CLI
def test_parse_log_line():
    """Testa la funzione di parsing indipendentemente dal CLI."""
    result = parse_log_line("2025-01-15 ERROR Connection timeout")
    assert result.level == "ERROR"
    assert result.message == "Connection timeout"

# 2. Test di integrazione: CLI con CliRunner
def test_cli_filter_by_level():
    """Testa il comando completo con input simulato."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("test.log").write_text(
            "2025-01-15 INFO Start\n"
            "2025-01-15 ERROR Timeout\n"
            "2025-01-15 INFO End\n"
        )
        result = runner.invoke(cli, ["filter", "test.log", "--level", "ERROR"])
        assert result.exit_code == 0
        assert "Timeout" in result.output
        assert "Start" not in result.output

# 3. Test di regressione: output deterministico
def test_output_format_json(snapshot):
    """Verifica che l'output JSON abbia la struttura attesa."""
    runner = CliRunner()
    result = runner.invoke(cli, ["status", "--format", "json"])
    output = json.loads(result.output)
    assert "servers" in output
    assert isinstance(output["servers"], list)

# 4. Test di compatibilita pipe
def test_pipe_compatibility():
    """Verifica che l'output sia compatibile con pipe Unix."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--format", "jsonl"])
    lines = result.output.strip().split("\n")
    for line in lines:
        # Ogni riga deve essere JSON valido
        json.loads(line)

# 5. Test parametrizzati per combinazioni di opzioni
@pytest.mark.parametrize("fmt,expected", [
    ("json", "{"),
    ("csv", "hostname,"),
    ("table", "┌"),
])
def test_output_formats(fmt, expected):
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--format", fmt])
    assert result.exit_code == 0
    assert expected in result.output
```

**Fixture condivise per test CLI:**

```python
@pytest.fixture
def cli_runner():
    """Runner con configurazione comune per tutti i test."""
    return CliRunner(env={
        "MYAPP_CONFIG": "/dev/null",
        "NO_COLOR": "1",
    })

@pytest.fixture
def temp_config(tmp_path):
    """Crea un file di configurazione temporaneo."""
    config = tmp_path / "config.toml"
    config.write_text('[server]\nhost = "localhost"\nport = 9090\n')
    return config
```

---

## CLI Design Patterns e UX

La progettazione dell'interfaccia di un CLI tool merita la stessa attenzione che si dedica alla progettazione di una GUI o di un'API REST. Un CLI ben progettato viene adottato naturalmente; uno mal progettato genera frustrazione e viene sostituito con script shell ad hoc.

### Pattern architetturali

**Command Pattern:** separa la dichiarazione del comando dalla sua esecuzione. Ogni comando e un oggetto con un metodo `execute()` e, opzionalmente, un metodo `undo()`. Questo pattern e particolarmente utile per CLI che supportano operazioni reversibili:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

class Command(ABC):
    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def undo(self) -> None: ...

@dataclass
class CreateServerCommand(Command):
    name: str
    cpu: int
    ram: int
    _created: bool = False

    def execute(self) -> None:
        # Logica di creazione
        print(f"Creazione server {self.name}")
        self._created = True

    def undo(self) -> None:
        if self._created:
            print(f"Eliminazione server {self.name}")
            self._created = False

class CommandHistory:
    """Mantiene la cronologia per supportare undo."""
    def __init__(self):
        self._history: list[Command] = []

    def execute(self, command: Command) -> None:
        command.execute()
        self._history.append(command)

    def undo_last(self) -> None:
        if self._history:
            self._history.pop().undo()
```

**Strategy Pattern per la formattazione dell'output:** incapsula la logica di formattazione in classi intercambiabili, selezionate dall'opzione `--format`:

```python
from abc import ABC, abstractmethod
import json
import csv
import sys

class OutputFormatter(ABC):
    @abstractmethod
    def format(self, data: list[dict]) -> str: ...

class JsonFormatter(OutputFormatter):
    def format(self, data: list[dict]) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False)

class CsvFormatter(OutputFormatter):
    def format(self, data: list[dict]) -> str:
        output = []
        if data:
            writer = csv.DictWriter(
                sys.stdout, fieldnames=data[0].keys()
            )
            writer.writeheader()
            writer.writerows(data)
        return ""

class TableFormatter(OutputFormatter):
    def format(self, data: list[dict]) -> str:
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table()
        if data:
            for key in data[0]:
                table.add_column(key)
            for row in data:
                table.add_row(*[str(v) for v in row.values()])
        console.print(table)
        return ""

FORMATTERS: dict[str, type[OutputFormatter]] = {
    "json": JsonFormatter,
    "csv": CsvFormatter,
    "table": TableFormatter,
}

def get_formatter(name: str) -> OutputFormatter:
    cls = FORMATTERS.get(name)
    if cls is None:
        raise ValueError(f"Formato sconosciuto: {name}")
    return cls()
```

### UX e progressive disclosure

La progressive disclosure e il principio per cui un CLI mostra solo le informazioni necessarie al livello di esperienza dell'utente. Un principiante vede l'help base; un esperto trova le opzioni avanzate cercandole:

**Livello 1 — Invocazione senza argomenti:** messaggio breve con i comandi disponibili e un suggerimento per `--help`. Mai un traceback o un messaggio di errore criptico.

**Livello 2 — `--help`:** documentazione completa con descrizione, opzioni, valori di default e almeno un esempio. L'help dovrebbe essere autosufficiente — l'utente non dovrebbe aver bisogno di consultare documentazione esterna per i casi d'uso comuni.

**Livello 3 — `--help` per sotto-comandi:** documentazione specifica del sotto-comando con esempi contestuali. `myapp deploy --help` mostra solo le opzioni di deploy, non quelle di `status` o `config`.

**Livello 4 — man page o `--help-all`:** documentazione esaustiva con sezioni su configurazione, variabili d'ambiente, exit code, file di configurazione e riferimenti. Per CLI complessi, un comando `help` dedicato con sotto-argomenti: `myapp help config`, `myapp help exit-codes`.

**Convenzioni sui nomi dei sotto-comandi:**

| Azione | Verbo standard | Evitare |
|--------|---------------|---------|
| Creare | `create` | `make`, `new`, `add` (inconsistente) |
| Elencare | `list` / `ls` | `show-all`, `get-all` |
| Mostrare dettagli | `show` / `get` | `info`, `details` |
| Modificare | `update` / `set` | `change`, `modify` |
| Eliminare | `delete` / `rm` | `remove`, `destroy` |
| Applicare configurazione | `apply` | `execute`, `run` |

La coerenza interna e piu importante della scelta specifica: se si usa `create` per un tipo di risorsa, non usare `add` per un altro.

### Convenzioni sui colori e la semantica visuale

I colori nei CLI tool devono seguire convenzioni semantiche universali — non servono per decorare ma per comunicare stato:

| Colore | Semantica | Uso |
|--------|-----------|-----|
| Verde | Successo, attivo, sicuro | Operazione completata, servizio online, test passato |
| Rosso | Errore, critico, pericolo | Errore fatale, servizio down, test fallito |
| Giallo | Avviso, attenzione | Warning, soglia vicina, azione richiesta |
| Blu/Cyan | Informazione, neutrale | Nomi, identificatori, valori |
| Magenta | Evidenziazione | Valori importanti, risultati di ricerca |
| Grigio/Dim | Secondario, meno importante | Timestamp, ID tecnici, metadati |
| Grassetto | Enfasi | Titoli, nomi di risorse, stati |

Non tutti i terminali supportano i colori allo stesso modo. Un CLI professionale deve rispettare la variabile `NO_COLOR` (specifica documentata su no-color.org) e il risultato di `sys.stdout.isatty()`. Rich, Click e Typer gestiscono questo automaticamente; con output manuale, il controllo va implementato esplicitamente.

Un pattern utile e la disabilitazione condizionale dei colori in base al contesto:

```python
import os
import sys

def use_color() -> bool:
    """Determina se usare colori nell'output."""
    # NO_COLOR ha precedenza su tutto (no-color.org)
    if os.environ.get("NO_COLOR") is not None:
        return False
    # FORCE_COLOR sovrascrive il controllo isatty
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    # Default: colori solo se stdout e un terminale
    return sys.stdout.isatty()
```

Seguire queste convenzioni garantisce che i CLI tool siano accessibili, prevedibili e compatibili con gli strumenti di automazione che parsano o redirezionano l'output.

---

## Best Practices

1. **Seguire le convenzioni POSIX per le opzioni.** Usare `-v` per verbose, `-h` per help, `-o` per output, `-f` per force/file, `-q` per quiet. La familiarita riduce la curva di apprendimento. Le opzioni brevi a singola lettera sono per i flag piu usati; le opzioni lunghe con `--` sono per chiarezza e leggibilita negli script. Non inventare convenzioni non standard: un utente esperto si aspetta che `-r` significhi ricorsivo, non "restart".

2. **Separare la logica di business dal parsing degli argomenti.** La funzione che gestisce il comando CLI non dovrebbe contenere logica complessa. Deve parsare gli argomenti, invocare le funzioni appropriate e formattare l'output. Questo principio rende il codice testabile — si possono testare le funzioni di business unitariamente senza simulare un'invocazione CLI — e riusabile in contesti diversi (libreria, API, cron job).

3. **Usare exit code significativi.** `0` per successo, `1` per errore generico, `2` per errore di sintassi negli argomenti (convenzione di argparse). Per tool complessi, definire un set coerente di codici: ad esempio `10` per errore di connessione, `11` per timeout, `12` per errore di autenticazione. Documentare i codici nella manpage o nell'help esteso. `sys.exit(code)` termina lo script con il codice specificato.

4. **Scrivere errori su stderr, risultati su stdout.** Questa separazione permette all'utente di redirezionare i risultati senza catturare anche i messaggi di errore: `mytool process data.csv > output.json 2> errors.log`. Con Click si usa `click.echo(message, err=True)`. Con print standard: `print(message, file=sys.stderr)`. Rich supporta `Console(stderr=True)` per un console dedicato agli errori.

5. **Supportare input da pipe e stdin.** Un buon CLI tool si integra nella pipeline Unix. Se il tool processa un file, accettare `-` come nome di file speciale che indica stdin: `cat data.csv | mytool process -`. Click lo fa nativamente con `type=click.File()` e `default="-"`. Questo permette composizione: `curl -s api.example.com/data | mytool transform | jq '.results'`.

6. **Fornire output strutturato con `--format`.** Per uso interattivo, tabelle colorate e leggibili. Per automazione, `--format json` o `--format csv`. Non forzare l'utente a parsare output formattato con `awk` e `grep` — e fragile e si rompe a ogni modifica cosmetica. L'opzione `--format jsonl` (JSON Lines) e particolarmente utile per lo streaming di grandi volumi di dati, dove ogni riga e un oggetto JSON indipendente.

7. **Implementare `--dry-run` per operazioni distruttive.** Ogni comando che modifica, cancella o sovrascrive dati deve supportare una modalita di simulazione. `--dry-run` mostra cosa verrebbe fatto senza farlo realmente. Questo principio riduce drasticamente gli errori in produzione e aumenta la fiducia degli utenti nel tool. Combinato con `--verbose`, diventa uno strumento di debug insostituibile.

8. **Testare il CLI come se fosse un'API.** Usare `CliRunner` di Click (ereditato da Typer) o `subprocess.run` per test di integrazione. Verificare exit code, output atteso, messaggi di errore, comportamento con input invalido, compatibilita con pipe. I test devono coprire anche i casi limite: file inesistenti, permessi negati, input troppo grande, encoding non-UTF8. Un CLI non testato e un CLI che si rompera in produzione.

9. **Documentare con esempi concreti.** L'help text dovrebbe includere almeno 2-3 esempi reali di utilizzo. Gli utenti leggono gli esempi prima della descrizione formale dei parametri. In argparse si usa l'`epilog` con `RawDescriptionHelpFormatter`. In Click si scrive nella docstring della funzione. Gli esempi dovrebbero mostrare sia l'uso semplice che quello avanzato, e coprire i casi d'uso piu comuni.

10. **Gestire con grazia i segnali e l'interruzione.** Un `Ctrl+C` non deve lasciare file temporanei orfani, connessioni aperte o dati in stato inconsistente. Catturare `KeyboardInterrupt` (o usare `signal.signal`) per eseguire cleanup prima di terminare. Stampare un messaggio breve come "Operazione interrotta" e uscire con un exit code appropriato (convenzionalmente 130 per SIGINT). Lo stesso vale per `SIGTERM` negli ambienti containerizzati dove i processi vengono terminati dal runtime.

---

## Esercizi

### Esercizio 1 — Log analyzer con argparse

Costruire un CLI tool `loggrep` che accetti uno o piu file di log e supporti:
- Filtro per livello (`--level ERROR WARNING`)
- Filtro per regex (`--pattern 'timeout|refused'`)
- Filtro per data (`--since 2025-01-01 --until 2025-12-31`)
- Output in formato table (default), JSON (`--json`) o CSV (`--csv`) usando un gruppo mutuamente esclusivo
- Conteggio con `--count`
- Lettura da stdin quando il file e `-`

Verificare con `CliRunner` che: (a) il filtro per livello funzioni, (b) l'output JSON sia valido, (c) l'exit code sia 2 con argomenti non validi.

### Esercizio 2 — Gestore infrastruttura con Typer

Creare un CLI `infractl` con Typer che esponga i sotto-comandi `server`, `network` e `config`. Ogni gruppo ha almeno due sotto-comandi (es. `server create`, `server list`). Requisiti:
- Callback globale con `--verbose` e `--config` (percorso al file TOML)
- `server create` chiede conferma prima di procedere
- `server list` supporta `--format table|json`
- Output con Rich (tabelle per list, pannelli per dettagli)
- Testare con `typer.testing.CliRunner` almeno 5 scenari

### Esercizio 3 — Dashboard Rich in tempo reale

Scrivere un CLI tool che mostri una dashboard live di monitoraggio server usando `rich.live.Live`. La dashboard deve:
- Mostrare una tabella con hostname, CPU%, RAM%, stato
- Aggiornare i valori ogni 2 secondi (simulare con random)
- Usare colori semantici: verde < 70%, giallo 70-90%, rosso > 90%
- Gestire SIGINT per shutdown graceful (messaggio di uscita, niente traceback)
- Supportare `--refresh-rate` per configurare la frequenza di aggiornamento

### Esercizio 4 — Pipeline Unix: filtro e trasformazione

Costruire un tool `csvtool` che implementi tre sotto-comandi componibili via pipe:
- `csvtool filter --column stato --value attivo` — filtra righe
- `csvtool transform --column prezzo --multiply 1.22` — trasforma valori
- `csvtool summary --column prezzo` — calcola min, max, media, somma

Il tool deve: leggere da stdin o da file, scrivere CSV su stdout, errori su stderr. Verificare che `cat data.csv | csvtool filter ... | csvtool transform ... | csvtool summary` funzioni.

### Esercizio 5 — Click plugin architecture

Implementare un CLI `taskctl` con architettura a plugin usando Click:
- Il comando principale scopre i plugin da un package `taskctl.plugins`
- Ogni plugin e un modulo con un oggetto `cli` di tipo `click.Command`
- Creare almeno 3 plugin: `export` (esporta task in JSON), `import` (importa da JSON), `stats` (mostra statistiche)
- Aggiungere un plugin discovery tramite `importlib.metadata.entry_points`
- Testare che i plugin vengano scoperti e invocati correttamente

### Esercizio 6 — Shell interattiva con Prompt Toolkit

Costruire una shell interattiva `dbshell` con Prompt Toolkit che simuli un client database:
- Completamento annidato per comandi (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) e tabelle
- Cronologia persistente su file
- Validazione in tempo reale della sintassi SQL (controllo base: keyword iniziale valida)
- Stile personalizzato con colori per keyword SQL
- Supporto multi-riga (terminare con `;`)

### Esercizio 7 — Configurazione multi-livello

Creare un CLI `appctl` che dimostri la precedenza della configurazione:
- Default hardcoded nel codice
- File TOML in `~/.config/appctl/config.toml`
- Variabili d'ambiente con prefisso `APPCTL_`
- Argomenti da riga di comando
- Un sotto-comando `config show` che mostri la configurazione finale con l'indicazione della provenienza di ogni valore (default / file / env / cli)

### Esercizio 8 — Distribuzione completa

Prendere uno degli esercizi precedenti e renderlo distribuibile:
- Configurare `pyproject.toml` con `[project.scripts]`
- Aggiungere il completamento shell (con argcomplete o il completamento nativo di Typer)
- Creare un `Makefile` o `justfile` con target: `install`, `dev`, `test`, `lint`, `build`
- Generare un eseguibile standalone con PyInstaller
- Verificare che `pipx install .` funzioni e che il comando sia disponibile nel PATH

---

## Letture

- **Documentazione ufficiale argparse** — docs.python.org/3/library/argparse.html — Riferimento completo per il parser della libreria standard.
- **Click Documentation** — click.palletsprojects.com — Guida ufficiale di Click con esempi, API reference e best practices.
- **Typer Documentation** — typer.tiangolo.com — Documentazione ufficiale di Typer, inclusa la guida al testing e al completamento shell.
- **Rich Documentation** — rich.readthedocs.io — API reference completa di Rich con galleria visuale degli output.
- **Prompt Toolkit Documentation** — python-prompt-toolkit.readthedocs.io — Guida alla costruzione di shell interattive.
- **Command Line Interface Guidelines** — clig.dev — Linee guida indipendenti dal linguaggio per CLI di qualita professionale, con consigli su UX, errori e composabilita.
- **12 Factor CLI Apps** — medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46 — Principi ispirati a The Twelve-Factor App applicati ai CLI tool.
- **POSIX Utility Conventions** — pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap12.html — Standard POSIX per la sintassi degli argomenti da riga di comando.
- **no-color.org** — Specifica de facto per la variabile `NO_COLOR` che disabilita l'output colorato.
- **PEP 668 — Externally Managed Environments** — peps.python.org/pep-0668/ — Spiega perche `pipx` e il metodo raccomandato per installare CLI tool Python.

---

## Riferimenti incrociati

- **Modulo 17 — Packaging e Distribuzione** — per approfondire `pyproject.toml`, `setuptools`, `hatch`, `uv` e la gestione delle dipendenze.
- **Modulo 10 — Testing** — per `pytest`, fixture, parametrizzazione e copertura — applicabili al testing CLI con `CliRunner`.
- **Modulo 12 — Logging** — per `logging`, `structlog`, rotazione dei log e integrazione con la verbosita del CLI (`-v`, `-vv`).
- **Modulo 22 — Clean Code** — per principi di naming, complessita ciclomatica e struttura delle funzioni — direttamente applicabili ai handler dei comandi CLI.
- **Modulo 21 — Design Patterns** — per il pattern Command (undo/redo nei CLI interattivi), Strategy (formattazione output), e Factory (plugin discovery).
- **Modulo 14 — Async/Await** — per CLI asincroni che gestiscono I/O concorrente (es. download paralleli, monitoring multi-server).
- **Modulo 31 — Osservabilita** — per integrare metriche e tracing nei CLI tool di lunga durata.

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **argparse** | Modulo della libreria standard Python per il parsing degli argomenti da riga di comando. Supporta argomenti posizionali, opzionali, subparser e generazione automatica dell'help. |
| **Click** | Framework per CLI basato su decoratori, creato da Armin Ronacher (autore di Flask). Offre composizione, testing integrato e gestione avanzata dell'I/O. |
| **Typer** | Framework per CLI basato su type hints, costruito sopra Click. Creato da Sebastian Ramirez (autore di FastAPI). |
| **Rich** | Libreria per output formattato nel terminale: tabelle, colori, progress bar, syntax highlighting, tree, pannelli. |
| **Prompt Toolkit** | Libreria per la costruzione di shell interattive con completamento, cronologia, validazione e rendering avanzato. |
| **CliRunner** | Classe di test di Click (ereditata da Typer) che simula l'invocazione CLI catturando output, exit code e stderr. |
| **subparser** | Parser secondario associato a un sotto-comando (es. `git commit`, `git push`). Ogni subparser ha i propri argomenti e opzioni. |
| **exit code** | Valore intero restituito da un processo al sistema operativo. 0 = successo, != 0 = errore. Convenzione POSIX. |
| **SIGINT** | Segnale Unix inviato alla pressione di Ctrl+C. Convenzionalmente causa exit code 130 (128 + 2). |
| **SIGTERM** | Segnale Unix di terminazione inviato da `kill` o da orchestratori container. Convenzionalmente causa exit code 143 (128 + 15). |
| **piping** | Meccanismo Unix per connettere stdout di un processo a stdin di un altro tramite l'operatore `|`. |
| **entry_point** | Meccanismo di setuptools/pip che associa un nome di comando a una funzione Python. Definito in `[project.scripts]` di `pyproject.toml`. |
| **pipx** | Strumento per installare CLI Python in ambienti virtuali isolati, evitando conflitti di dipendenze. |
| **argcomplete** | Libreria che aggiunge il completamento shell automatico ai parser argparse. |
| **shellingham** | Libreria che rileva automaticamente la shell in uso (bash, zsh, fish, PowerShell). |
| **NO_COLOR** | Variabile d'ambiente standard de facto (no-color.org) che indica al programma di non usare output colorato. |
| **eager option** | Opzione Click processata prima di tutte le altre, usata tipicamente per `--version` e `--help`. |
| **BrokenPipeError** | Eccezione Python sollevata quando si scrive su una pipe chiusa (es. `myapp | head -5`). |
| **XDG Base Directory** | Specifica freedesktop.org per le directory standard di configurazione (`~/.config`), cache (`~/.cache`) e dati (`~/.local/share`). |
| **Textual** | Framework TUI per Python sviluppato da Textualize. Porta layout dichiarativo, CSS e widget nel terminale per costruire applicazioni interattive complete. |
| **questionary** | Libreria Python per prompt interattivi (selezione singola, checkbox, conferma, input con validazione). Ispirata a Inquirer.js. |
| **InquirerPy** | Reimplementazione moderna di PyInquirer con supporto per ricerca fuzzy, personalizzazione avanzata di stili e keybinding. |
| **shiv** | Tool sviluppato da LinkedIn per creare archivi zipapp eseguibili con dipendenze Python incluse. Non include l'interprete. |
| **zipapp** | Modulo della libreria standard Python che crea archivi ZIP eseguibili come singolo file `.pyz`. Richiede un interprete Python preinstallato. |
| **structlog** | Libreria di logging strutturato per Python. Produce log in formato JSON parsabile o output colorato per lo sviluppo. |
| **man page** | Pagina di manuale nei sistemi Unix, accessibile con il comando `man`. Formato nativo di documentazione per comandi da riga di comando. |
| **argparse-manpage** | Tool che genera man page in formato groff a partire da un parser argparse esistente. |
| **click-man** | Tool che genera man page automaticamente dai comandi Click. |
| **pytest-console-scripts** | Plugin pytest per testare entry point CLI installati, sia in-process che come subprocess. |
| **progressive disclosure** | Principio UX per cui un CLI mostra informazioni crescenti in base al livello di interazione dell'utente (nessun argomento, `--help`, man page). |
| **TUI** | Terminal User Interface — interfaccia utente testuale che occupa l'intero terminale con widget interattivi, distinta da un CLI sequenziale. |
