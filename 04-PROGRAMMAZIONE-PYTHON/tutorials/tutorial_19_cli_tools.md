# Tutorial 19 — CLI Tools in Python: Click, Typer, Rich

> **Companion a:** `19-cli-tools.md`
> **Scope:** Click, Typer, argparse, Rich, output formattato, distribuzione come script
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md`, `tutorial_09_type_hints_mypy.md`
> **Durata stimata:** 12-16 ore
> **Stack:** Python 3.12+, Click 8.x, Typer 0.12+, Rich 13.x

---

## Mappa concettuale

```
CLI Tools
│
├── Framework
│   ├── argparse — stdlib, verboso
│   ├── Click — decoratori, composable
│   └── Typer — type hints, basato su Click
│
├── Rich — output formattato
│   ├── Console — print con stili
│   ├── Table — tabelle ASCII
│   ├── Progress — barre avanzamento
│   ├── Panel / Markdown
│   └── Syntax — syntax highlighting
│
├── Pattern CLI
│   ├── Comandi e sottocomandi
│   ├── Configurazione (env + file + flags)
│   ├── Stdin/stdout pipeline
│   └── Exit codes significativi
│
└── Distribuzione
    ├── pyproject.toml [scripts]
    ├── pipx install — installazione isolata
    └── shebang + chmod +x
```

---

# Parte A — Typer: CLI con type hints

---

## A1. CLI base con Typer

```python
#!/usr/bin/env python3
# cli/main.py
import typer
from rich.console import Console
from rich import print as rprint
from typing import Annotated
from pathlib import Path
import sys

app = typer.Typer(
    name="miotool",
    help="Strumento CLI di esempio con Typer e Rich",
    add_completion=True,  # autocomplete per bash/zsh/fish/powershell
)
console = Console()

@app.command()
def saluta(
    nome: Annotated[str, typer.Argument(help="Nome della persona da salutare")],
    formale: Annotated[bool, typer.Option("--formale/--informale", help="Stile di saluto")] = False,
    ripetizioni: Annotated[int, typer.Option("--ripetizioni", "-r", min=1, max=10)] = 1,
) -> None:
    """Saluta una persona con stile."""
    prefisso = "Egregio" if formale else "Ciao"
    for _ in range(ripetizioni):
        console.print(f"[bold green]{prefisso}, {nome}![/bold green]")

@app.command()
def conta(
    file: Annotated[Path, typer.Argument(help="File da analizzare", exists=True)],
    solo_righe: Annotated[bool, typer.Option("--solo-righe", "-l")] = False,
    solo_parole: Annotated[bool, typer.Option("--solo-parole", "-w")] = False,
) -> None:
    """Conta righe, parole e caratteri in un file."""
    testo = file.read_text(encoding="utf-8")
    righe = testo.count("\n")
    parole = len(testo.split())
    caratteri = len(testo)

    if solo_righe:
        console.print(str(righe))
    elif solo_parole:
        console.print(str(parole))
    else:
        console.print(f"[cyan]Righe:[/cyan] {righe}")
        console.print(f"[cyan]Parole:[/cyan] {parole}")
        console.print(f"[cyan]Caratteri:[/cyan] {caratteri}")

if __name__ == "__main__":
    app()
```

---

## A2. Sottocomandi e gruppi

```python
import typer
from rich.console import Console

app = typer.Typer()
db_app = typer.Typer(help="Gestione database")
utenti_app = typer.Typer(help="Gestione utenti")

app.add_typer(db_app, name="db")
app.add_typer(utenti_app, name="utenti")

console = Console()

@db_app.command("migra")
def db_migra(
    url: str = typer.Option(..., envvar="DATABASE_URL", help="URL database"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simula senza applicare"),
) -> None:
    """Applica migrazioni al database."""
    console.print(f"[yellow]Connessione a {url}[/yellow]")
    if dry_run:
        console.print("[blue]Dry-run: nessuna modifica applicata[/blue]")
    else:
        console.print("[green]Migrazioni applicate[/green]")

@db_app.command("backup")
def db_backup(
    output: Path = typer.Option(Path("."), "--output", "-o"),
) -> None:
    """Crea backup del database."""
    console.print(f"Backup salvato in {output}")

@utenti_app.command("lista")
def utenti_lista(
    formato: str = typer.Option("tabella", "--formato", "-f", help="tabella|json|csv"),
) -> None:
    """Lista tutti gli utenti."""
    console.print(f"Formato: {formato}")

@utenti_app.command("crea")
def utenti_crea(
    email: str = typer.Argument(..., help="Email del nuovo utente"),
    admin: bool = typer.Option(False, "--admin", help="Utente amministratore"),
) -> None:
    """Crea un nuovo utente."""
    ruolo = "admin" if admin else "utente"
    console.print(f"Creato {ruolo}: {email}")

if __name__ == "__main__":
    app()
```

---

## A3. Rich: output professionale

```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint
import time

console = Console()

def mostra_tabella(dati: list[dict]) -> None:
    """Visualizza dati in tabella formattata."""
    if not dati:
        console.print("[yellow]Nessun dato da mostrare[/yellow]")
        return

    table = Table(
        title="Risultati",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
    )
    for colonna in dati[0].keys():
        table.add_column(colonna.replace("_", " ").title(), style="white")

    for riga in dati:
        table.add_row(*[str(v) for v in riga.values()])

    console.print(table)

def mostra_progresso(items: list, fn) -> list:
    """Mostra barra di progresso durante elaborazione."""
    risultati = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Elaborazione...", total=len(items))
        for item in items:
            risultati.append(fn(item))
            progress.advance(task)
    return risultati

def mostra_codice(codice: str, linguaggio: str = "python") -> None:
    """Mostra codice con syntax highlighting."""
    syntax = Syntax(codice, linguaggio, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"[bold]{linguaggio}[/bold]", border_style="green"))

def mostra_errore(msg: str) -> None:
    console.print(Panel(f"[bold red]ERRORE[/bold red]: {msg}", border_style="red"))

def mostra_successo(msg: str) -> None:
    console.print(Panel(f"[bold green]OK[/bold green]: {msg}", border_style="green"))

# Esempio
mostra_tabella([
    {"nome": "Alice", "eta": 25, "ruolo": "developer"},
    {"nome": "Bob", "eta": 32, "ruolo": "admin"},
])
```

---

# Parte B — Click: flessibilità avanzata

---

## B1. Click con configurazione da env e file

```python
import click
import os
from pathlib import Path

@click.group()
@click.option("--config", "-c", type=click.Path(exists=False), envvar="MIOTOOL_CONFIG")
@click.option("--verbose", "-v", count=True, help="-v info, -vv debug")
@click.pass_context
def cli(ctx: click.Context, config: str | None, verbose: int) -> None:
    """Strumento CLI avanzato con Click."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config or Path.home() / ".config" / "miotool" / "config.toml"

@cli.command()
@click.argument("sorgente", type=click.Path(exists=True))
@click.argument("destinazione")
@click.option("--forza", is_flag=True, help="Sovrascrivi senza chiedere")
@click.option("--formato", type=click.Choice(["json", "csv", "parquet"]), default="json")
@click.pass_context
def converti(ctx: click.Context, sorgente: str, destinazione: str, forza: bool, formato: str) -> None:
    """Converte un file da un formato all'altro."""
    if ctx.obj["verbose"] > 0:
        click.echo(f"Verbose mode: {ctx.obj['verbose']}")

    dest_path = Path(destinazione)
    if dest_path.exists() and not forza:
        if not click.confirm(f"{dest_path} esiste già. Sovrascrivere?"):
            raise click.Abort()

    click.echo(f"Conversione {sorgente} → {destinazione} (formato: {formato})")

@cli.command()
@click.option("--email", prompt="Email", help="Email utente")
@click.option("--password", prompt="Password", hide_input=True, confirmation_prompt=True)
def registra(email: str, password: str) -> None:
    """Registra un nuovo utente (con prompt interattivo)."""
    click.echo(f"Registrato: {email}")

if __name__ == "__main__":
    cli()
```

---

# Parte C — Distribuzione

---

## C1. pyproject.toml per CLI

```toml
# pyproject.toml
[project]
name = "miotool"
version = "1.0.0"
description = "Il mio strumento CLI"
requires-python = ">=3.12"
dependencies = [
    "typer[all]>=0.12",
    "rich>=13.0",
    "httpx>=0.27",
]

[project.scripts]
miotool = "miotool.cli.main:app"
# Dopo `pip install .` o `pipx install .`:
# $ miotool --help

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "click.testing",
]
```

```python
# Test CLI
from typer.testing import CliRunner
from miotool.cli.main import app

runner = CliRunner()

def test_saluta():
    result = runner.invoke(app, ["saluta", "Mario"])
    assert result.exit_code == 0
    assert "Mario" in result.output

def test_saluta_formale():
    result = runner.invoke(app, ["saluta", "--formale", "Rossi"])
    assert "Egregio" in result.output

def test_conta_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("prima riga\nseconda riga\n")
    result = runner.invoke(app, ["conta", str(f)])
    assert result.exit_code == 0
    assert "2" in result.output
```

---

# Parte D — Riepilogo

## Click vs Typer vs argparse

| Feature | argparse | Click | Typer |
|---|---|---|---|
| Type hints | No | Parziale | Completo |
| Sottocomandi | Manuale | `@group` | `app.add_typer()` |
| Testing | Manuale | CliRunner | CliRunner (Click) |
| Autocomplete | No | Plugin | Built-in |
| Rich integration | No | Manuale | Built-in (`typer[all]`) |
| Curva di apprendimento | Alta | Media | Bassa |

## Exit codes

```python
import sys
import typer

# Convenzione Unix:
# 0 = successo
# 1 = errore generico
# 2 = errore uso (argomenti sbagliati)
# 130 = interrotto con Ctrl+C

@app.command()
def verifica(file: Path) -> None:
    if not file.exists():
        typer.echo(f"ERRORE: {file} non trovato", err=True)
        raise typer.Exit(code=1)
    typer.echo("OK")
    raise typer.Exit(code=0)
```

## Prossimi passi

- `tutorial_23_packaging.md` — distribuire il CLI su PyPI
- `tutorial_27_ci_cd.md` — pipeline per build e release del CLI
