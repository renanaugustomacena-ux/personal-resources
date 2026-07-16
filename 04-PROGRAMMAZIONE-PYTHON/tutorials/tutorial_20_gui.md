# Tutorial 20 — GUI in Python: Tkinter, PyQt6, Kivy

> **Companion a:** `20-gui.md`
> **Scope:** Tkinter (stdlib), PyQt6/PySide6, Kivy per mobile, pattern MVC, threading UI
> **Prerequisiti:** `tutorial_02_oop.md`, `tutorial_10_programmazione_asincrona.md`
> **Durata stimata:** 16-20 ore
> **Stack:** Python 3.12+, Tkinter (stdlib), PyQt6 6.x, Kivy 2.x

---

## Mappa concettuale

```
GUI Python
│
├── Tkinter — stdlib, semplice, nativo
│   ├── Tk() — finestra root
│   ├── Widget — Label, Button, Entry, Text...
│   ├── Layout — pack, grid, place
│   ├── Event loop — mainloop()
│   └── StringVar/IntVar — binding variabili
│
├── PyQt6/PySide6 — professionale, cross-platform
│   ├── QApplication — processo UI
│   ├── QMainWindow / QDialog / QWidget
│   ├── Layout — QVBoxLayout, QHBoxLayout, QGridLayout
│   ├── Signals & Slots — pattern Observer Qt
│   ├── QThread / asyncio — non bloccare la UI
│   └── Qt Designer → .ui → pyuic6
│
├── Kivy — mobile-first
│   ├── App.run() — entry point
│   ├── Widget — building block
│   ├── KV Language — markup dichiarativo
│   ├── ScreenManager — navigazione schermate
│   └── Build: kivy → APK/IPA con Buildozer
│
└── Pattern comuni
    ├── MVC — Model-View-Controller
    ├── Threading — worker thread per operazioni lente
    ├── Event-driven — risposta a eventi utente
    └── Data binding — view riflette il model
```

---

# Parte A — Tkinter: partenza rapida

---

## A1. Applicazione Tkinter base

```python
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

class AppContatore(tk.Tk):
    """Applicazione contatore con Tkinter puro."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Contatore")
        self.geometry("300x200")
        self.resizable(False, False)

        self._contatore = tk.IntVar(value=0)
        self._passo = tk.IntVar(value=1)

        self._crea_widget()
        self._crea_layout()

    def _crea_widget(self) -> None:
        # Visualizzazione numero
        self._lbl_valore = ttk.Label(
            self, textvariable=self._contatore,
            font=("Arial", 48, "bold"), foreground="navy"
        )

        # Controlli passo
        self._frm_passo = ttk.Frame(self)
        self._lbl_passo = ttk.Label(self._frm_passo, text="Passo:")
        self._spn_passo = ttk.Spinbox(
            self._frm_passo, from_=1, to=100,
            textvariable=self._passo, width=5
        )

        # Bottoni
        self._frm_bottoni = ttk.Frame(self)
        self._btn_decrementa = ttk.Button(
            self._frm_bottoni, text="−",
            command=self._decrementa, width=5
        )
        self._btn_reset = ttk.Button(
            self._frm_bottoni, text="Reset",
            command=self._reset, width=8
        )
        self._btn_incrementa = ttk.Button(
            self._frm_bottoni, text="+",
            command=self._incrementa, width=5
        )

    def _crea_layout(self) -> None:
        self._lbl_valore.pack(pady=20)
        self._frm_passo.pack()
        self._lbl_passo.pack(side="left")
        self._spn_passo.pack(side="left", padx=5)
        self._frm_bottoni.pack(pady=10)
        self._btn_decrementa.pack(side="left", padx=5)
        self._btn_reset.pack(side="left")
        self._btn_incrementa.pack(side="left", padx=5)

        # Binding tastiera
        self.bind("<Up>", lambda e: self._incrementa())
        self.bind("<Down>", lambda e: self._decrementa())
        self.bind("<r>", lambda e: self._reset())

    def _incrementa(self) -> None:
        self._contatore.set(self._contatore.get() + self._passo.get())

    def _decrementa(self) -> None:
        self._contatore.set(self._contatore.get() - self._passo.get())

    def _reset(self) -> None:
        if messagebox.askyesno("Conferma", "Vuoi davvero resettare il contatore?"):
            self._contatore.set(0)

if __name__ == "__main__":
    app = AppContatore()
    app.mainloop()
```

> **Analogia:** Una GUI è come un ristorante: il cliente (utente) interagisce con il menu (widget), ordina (evento), il cameriere porta l'ordine in cucina (event loop), la cucina prepara il piatto (logica business), e il risultato torna al tavolo (aggiorna la UI). Tenere la cucina (logica lenta) fuori dal percorso del cameriere (main thread UI) è fondamentale per non bloccare il ristorante.

---

## A2. Tkinter con grid layout e menu

```python
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

class EditorTesto(tk.Tk):
    """Editor di testo semplice."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Editor di Testo")
        self.geometry("800x600")
        self._file_corrente: Path | None = None
        self._crea_menu()
        self._crea_area_testo()
        self._crea_barra_stato()

    def _crea_menu(self) -> None:
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        menu_file = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=menu_file)
        menu_file.add_command(label="Nuovo", command=self._nuovo, accelerator="Ctrl+N")
        menu_file.add_command(label="Apri...", command=self._apri, accelerator="Ctrl+O")
        menu_file.add_command(label="Salva", command=self._salva, accelerator="Ctrl+S")
        menu_file.add_separator()
        menu_file.add_command(label="Esci", command=self.quit)

        self.bind("<Control-n>", lambda e: self._nuovo())
        self.bind("<Control-o>", lambda e: self._apri())
        self.bind("<Control-s>", lambda e: self._salva())

    def _crea_area_testo(self) -> None:
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        self._testo = tk.Text(frame, wrap="word", undo=True, font=("Consolas", 12))
        scrollbar_v = ttk.Scrollbar(frame, command=self._testo.yview)
        self._testo.config(yscrollcommand=scrollbar_v.set)

        scrollbar_v.pack(side="right", fill="y")
        self._testo.pack(side="left", fill="both", expand=True)

    def _crea_barra_stato(self) -> None:
        self._var_stato = tk.StringVar(value="Pronto")
        ttk.Label(self, textvariable=self._var_stato, relief="sunken", anchor="w").pack(
            side="bottom", fill="x", padx=2
        )

    def _nuovo(self) -> None:
        self._testo.delete("1.0", "end")
        self._file_corrente = None
        self.title("Editor di Testo — Senza titolo")

    def _apri(self) -> None:
        percorso = filedialog.askopenfilename(
            filetypes=[("File di testo", "*.txt"), ("Tutti i file", "*.*")]
        )
        if percorso:
            self._file_corrente = Path(percorso)
            self._testo.delete("1.0", "end")
            self._testo.insert("1.0", self._file_corrente.read_text(encoding="utf-8"))
            self.title(f"Editor — {self._file_corrente.name}")
            self._var_stato.set(f"Aperto: {percorso}")

    def _salva(self) -> None:
        if not self._file_corrente:
            percorso = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File di testo", "*.txt")]
            )
            if not percorso:
                return
            self._file_corrente = Path(percorso)
        self._file_corrente.write_text(
            self._testo.get("1.0", "end-1c"), encoding="utf-8"
        )
        self._var_stato.set(f"Salvato: {self._file_corrente}")

if __name__ == "__main__":
    EditorTesto().mainloop()
```

---

# Parte B — PyQt6: GUI professionale

---

## B1. Applicazione PyQt6 base

```python
# pip install PyQt6
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

class FinestraPrincipale(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Todo List — PyQt6")
        self.setMinimumSize(500, 400)
        self._crea_ui()

    def _crea_ui(self) -> None:
        widget_centrale = QWidget()
        self.setCentralWidget(widget_centrale)
        layout_principale = QVBoxLayout(widget_centrale)

        # Titolo
        titolo = QLabel("Lista Todo")
        titolo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        titolo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principale.addWidget(titolo)

        # Input aggiunta
        layout_input = QHBoxLayout()
        self._input_todo = QLineEdit()
        self._input_todo.setPlaceholderText("Inserisci un'attività...")
        self._input_todo.returnPressed.connect(self._aggiungi_todo)

        btn_aggiungi = QPushButton("Aggiungi")
        btn_aggiungi.clicked.connect(self._aggiungi_todo)

        layout_input.addWidget(self._input_todo)
        layout_input.addWidget(btn_aggiungi)
        layout_principale.addLayout(layout_input)

        # Lista
        self._lista = QListWidget()
        self._lista.itemDoubleClicked.connect(self._rimuovi_todo)
        layout_principale.addWidget(self._lista)

        # Label istruzioni
        layout_principale.addWidget(QLabel("Doppio click per rimuovere"))

    def _aggiungi_todo(self) -> None:
        testo = self._input_todo.text().strip()
        if not testo:
            QMessageBox.warning(self, "Errore", "Inserisci un'attività")
            return
        self._lista.addItem(f"☐ {testo}")
        self._input_todo.clear()

    def _rimuovi_todo(self, item) -> None:
        riga = self._lista.row(item)
        self._lista.takeItem(riga)

def main() -> None:
    app = QApplication(sys.argv)
    finestra = FinestraPrincipale()
    finestra.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## B2. QThread: operazioni in background

```python
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import time

class WorkerSegnali(QObject):
    avanzamento = pyqtSignal(int)        # 0-100
    risultato = pyqtSignal(str)
    errore = pyqtSignal(str)
    completato = pyqtSignal()

class Worker(QThread):
    def __init__(self, dati: list) -> None:
        super().__init__()
        self.segnali = WorkerSegnali()
        self._dati = dati
        self._annullato = False

    def annulla(self) -> None:
        self._annullato = True

    def run(self) -> None:
        """Eseguito in un thread separato — NON blocca la UI."""
        try:
            risultati = []
            for i, elemento in enumerate(self._dati):
                if self._annullato:
                    break
                time.sleep(0.1)   # simula operazione lenta
                risultati.append(elemento.upper())
                pct = int((i + 1) / len(self._dati) * 100)
                self.segnali.avanzamento.emit(pct)
            self.segnali.risultato.emit(", ".join(risultati))
            self.segnali.completato.emit()
        except Exception as e:
            self.segnali.errore.emit(str(e))

# In un QWidget:
# self._worker = Worker(["a", "b", "c"])
# self._worker.segnali.avanzamento.connect(self._progress_bar.setValue)
# self._worker.segnali.risultato.connect(self._mostra_risultato)
# self._worker.segnali.errore.connect(lambda e: QMessageBox.critical(self, "Errore", e))
# self._worker.start()
```

---

# Parte C — Kivy: mobile-first

---

## C1. App Kivy con KV language

```python
# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty, ListProperty

class SchermataPrincipale(Screen):
    pass

class SchermataDettaglio(Screen):
    titolo_item = StringProperty("")

class MioScreenManager(ScreenManager):
    pass

# La struttura UI va nel file .kv per separare logica e presentazione
KV = """
<SchermataPrincipale>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10

        Label:
            text: 'Lista Note'
            font_size: '24sp'
            size_hint_y: None
            height: '50dp'

        TextInput:
            id: input_nota
            hint_text: 'Inserisci una nota...'
            size_hint_y: None
            height: '50dp'

        Button:
            text: 'Aggiungi'
            size_hint_y: None
            height: '50dp'
            on_press: app.aggiungi_nota(input_nota.text)

        ScrollView:
            GridLayout:
                id: lista_note
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: 5
"""

class AppNote(App):
    note: list[str] = ListProperty([])

    def build(self):
        from kivy.lang import Builder
        Builder.load_string(KV)
        self.sm = MioScreenManager()
        self.sm.add_widget(SchermataPrincipale(name="principale"))
        return self.sm

    def aggiungi_nota(self, testo: str) -> None:
        if not testo.strip():
            return
        self.note.append(testo)
        schermata = self.sm.get_screen("principale")
        lista = schermata.ids.lista_note

        btn = Button(
            text=testo,
            size_hint_y=None,
            height="40dp",
        )
        lista.add_widget(btn)

if __name__ == "__main__":
    AppNote().run()
```

---

# Parte D — Pattern MVC per GUI

---

## D1. Model-View-Controller pattern

```python
# Model — dati e logica business
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class ModeloTodo:
    items: list[str] = field(default_factory=list)
    _listeners: list[Callable] = field(default_factory=list, repr=False)

    def aggiungi(self, testo: str) -> None:
        if testo.strip():
            self.items.append(testo.strip())
            self._notifica()

    def rimuovi(self, indice: int) -> None:
        if 0 <= indice < len(self.items):
            self.items.pop(indice)
            self._notifica()

    def abbonati(self, listener: Callable) -> None:
        self._listeners.append(listener)

    def _notifica(self) -> None:
        for l in self._listeners:
            l(self.items[:])   # copia per evitare mutazioni

# Controller — collegamento Model-View
class ControllerTodo:
    def __init__(self, model: ModeloTodo) -> None:
        self._model = model

    def aggiungi_todo(self, testo: str) -> None:
        self._model.aggiungi(testo)

    def rimuovi_todo(self, indice: int) -> None:
        self._model.rimuovi(indice)

    def abbonati_cambiamenti(self, callback: Callable) -> None:
        self._model.abbonati(callback)

# View (Tkinter) — pura UI, non conosce il Model
class ViewTodo:
    def __init__(self, controller: ControllerTodo) -> None:
        self._ctrl = controller
        self._root = tk.Tk()
        self._root.title("Todo MVC")
        self._crea_ui()
        self._ctrl.abbonati_cambiamenti(self._aggiorna_lista)

    def _crea_ui(self) -> None:
        frame = ttk.Frame(self._root, padding=10)
        frame.pack(fill="both", expand=True)

        self._var_input = tk.StringVar()
        ttk.Entry(frame, textvariable=self._var_input).pack(fill="x")
        ttk.Button(frame, text="Aggiungi", command=self._aggiungi).pack()

        self._listbox = tk.Listbox(frame)
        self._listbox.pack(fill="both", expand=True)
        ttk.Button(frame, text="Rimuovi selezionato", command=self._rimuovi).pack()

    def _aggiungi(self) -> None:
        self._ctrl.aggiungi_todo(self._var_input.get())
        self._var_input.set("")

    def _rimuovi(self) -> None:
        sel = self._listbox.curselection()
        if sel:
            self._ctrl.rimuovi_todo(sel[0])

    def _aggiorna_lista(self, items: list[str]) -> None:
        self._listbox.delete(0, "end")
        for item in items:
            self._listbox.insert("end", item)

    def avvia(self) -> None:
        self._root.mainloop()

# Composizione
import tkinter as tk
from tkinter import ttk

modello = ModeloTodo()
controller = ControllerTodo(modello)
view = ViewTodo(controller)
view.avvia()
```

---

# Parte E — Riepilogo

## Scelta del framework

| Framework | Ideale per | Distribuzione |
|---|---|---|
| **Tkinter** | Tool interni, Python built-in | `pyinstaller` → .exe/.app |
| **PyQt6** | Desktop professionale, complesso | `pyinstaller` / `cx_Freeze` |
| **PySide6** | Come PyQt6, licenza LGPL | Stessa di PyQt6 |
| **Kivy** | Mobile, touch, iOS/Android | `Buildozer` → APK/IPA |
| **DearPyGui** | Dashboard, giochi, performance | `pyinstaller` |
| **Gradio/Streamlit** | Web UI per ML/dati | Docker/cloud |

## Anti-pattern UI

- **Codice di business nel widget** — sempre separare Model da View
- **Operazioni lente nel main thread** — blocca la UI; usare QThread o `threading.Thread`
- **Aggiornare widget da thread worker** — illegale in Qt; usare Signal o `after()` in Tkinter
- **Widget annidati eccessivamente** — usare layout compositi con Frame/Panel

## Prossimi passi

- `tutorial_21_design_patterns.md` — Observer, Strategy e altri pattern usati nella GUI
- `tutorial_22_clean_code.md` — codice leggibile e manutenibile per applicazioni GUI
