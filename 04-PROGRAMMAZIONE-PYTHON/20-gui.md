---
corso: "Programmazione Python"
fase: "3 — Librerie e Framework"
modulo: "20"
titolo: "GUI con Python"
versione: "PySide6 6.7+ / PyQt6 6.7+ / CustomTkinter 5.x / Flet 0.23+ / tkinter (stdlib)"
livello: "Intermedio"
prerequisiti:
  - "07 — OOP"
  - "03 — Funzioni e Scope"
  - "08 — Concorrenza e Parallelismo"
obiettivi:
  - "Costruire interfacce grafiche con tkinter e CustomTkinter"
  - "Sviluppare applicazioni desktop professionali con PySide6 (Qt 6)"
  - "Utilizzare Flet per interfacce cross-platform con Flutter"
  - "Applicare il pattern MVC alla progettazione GUI"
  - "Gestire threading e operazioni asincrone senza bloccare la UI"
  - "Distribuire applicazioni come eseguibili con PyInstaller e Nuitka"
tag: [gui, tkinter, pyside6, qt6, customtkinter, flet, pyinstaller, nuitka]
---

# GUI con Python — Guida Completa

> **Modulo 20** · **Aggiornamento:** 2026-05-24 · **Versione:** PySide6 6.7+ / PyQt6 6.7+ / CustomTkinter 5.x / Flet 0.23+ / tkinter (stdlib)

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [OOP](07-oop.md), [Funzioni e Scope](03-funzioni-scope.md), [Concorrenza](08-concorrenza.md)
>
> Al termine di questo modulo saprai:
> 1. Costruire interfacce grafiche con tkinter e CustomTkinter
> 2. Sviluppare applicazioni desktop professionali con PySide6 (Qt 6)
> 3. Utilizzare Flet per interfacce cross-platform basate su Flutter
> 4. Applicare il pattern MVC alla progettazione di applicazioni GUI
> 5. Gestire threading e operazioni asincrone senza bloccare l'interfaccia
> 6. Distribuire applicazioni come eseguibili con PyInstaller e Nuitka
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio

## Idee guida
1. **PySide6 (Qt 6) > PyQt5 (license LGPL vs GPL).**
2. **CustomTkinter per moderno look-and-feel su tkinter.**
3. **Toga per cross-platform native (BeeWare).**
4. **Streamlit/Gradio per web-based GUI rapide.**

### Mappa concettuale

```
                        ┌─────────────────────┐
                        │    GUI con PYTHON    │
                        └──────────┬──────────┘
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
 ┌─────────────────┐     ┌─────────────────┐      ┌─────────────────┐
 │  Toolkit nativi   │     │  Framework mod.  │      │  Web-based GUI  │
 │  tkinter (stdlib)│     │  PySide6 / Qt6  │      │  Streamlit      │
 │  CustomTkinter   │     │  Flet (Flutter) │      │  Gradio         │
 │  ttk              │     │  Dear PyGui     │      │  NiceGUI        │
 └────────┬────────┘     └────────┬────────┘      └─────────────────┘
          │                       │
          ▼                       ▼
 ┌─────────────────┐     ┌─────────────────┐
 │  Architettura    │     │  Distribuzione  │
 │  Event loop      │     │  PyInstaller    │
 │  Signals/Slots   │     │  Nuitka         │
 │  MVC pattern     │     │  Briefcase      │
 │  Threading GUI   │     │  cx_Freeze      │
 └─────────────────┘     └─────────────────┘
```


## Indice

1. [Panoramica](#panoramica)
2. [tkinter](#tkinter)
   - [Fondamenti](#fondamenti)
   - [Funzionalità Avanzate](#funzionalità-avanzate)
   - [Applicazione Completa](#applicazione-completa)
3. [PyQt6 / PySide6](#pyqt6--pyside6)
   - [Fondamenti PyQt6](#fondamenti-pyqt6)
   - [Funzionalità Avanzate PyQt6](#funzionalità-avanzate-pyqt6)
   - [Qt Designer](#qt-designer)
4. [CustomTkinter](#customtkinter)
5. [Flet](#flet)
6. [Dear PyGui](#dear-pygui)
7. [Packaging GUI Applications](#packaging-gui-applications)
8. [Best Practices](#best-practices)
9. [PySide6 Deep Dive — Widget, Layout, QML](#pyside6-deep-dive--widget-layout-qml)
10. [Tkinter Patterns Avanzati](#tkinter-patterns-avanzati)
11. [Event Loop e Threading nelle GUI](#event-loop-e-threading-nelle-gui)
12. [Packaging Avanzato — PyInstaller, Briefcase, Nuitka](#packaging-avanzato--pyinstaller-briefcase-nuitka)
13. [Accessibilita nelle Applicazioni GUI](#accessibilità-nelle-applicazioni-gui)
14. [Kivy — GUI per Mobile](#kivy--gui-per-mobile)
15. [GUI Testing — pytest-qt, pyautogui e Strategie di Test](#gui-testing--pytest-qt-pyautogui-e-strategie-di-test)
16. [Sviluppo di Widget Personalizzati](#sviluppo-di-widget-personalizzati)
17. [Layout Responsivi e Adattivi](#layout-responsivi-e-adattivi)
18. [Integrazione con la System Tray](#integrazione-con-la-system-tray)
19. [Pattern MVC/MVP — Architettura Approfondita per GUI](#pattern-mvcmvp--architettura-approfondita-per-gui)
20. [FAQ](#faq)
21. [Esercizi](#esercizi)
22. [Letture e Riferimenti](#letture-e-riferimenti)
23. [Glossario](#glossario)

---

## Panoramica

La programmazione di interfacce grafiche (GUI — Graphical User Interface) rappresenta uno dei campi più ampi e trasversali dello sviluppo software. Python, grazie alla sua versatilità, offre un ecosistema ricco di framework e librerie per la creazione di applicazioni desktop con interfacce visive complete. Questa guida esplora in modo approfondito le principali opzioni disponibili, dai fondamenti di tkinter fino ai framework più moderni come Flet e Dear PyGui.

### Il Panorama dei Framework GUI in Python

Python dispone di numerosi framework per lo sviluppo di interfacce grafiche. Ognuno possiede caratteristiche proprie, punti di forza specifici e casi d'uso ideali.

**tkinter** è il toolkit GUI incluso nella libreria standard di Python. Non richiede installazioni aggiuntive, è multipiattaforma e rappresenta la scelta più immediata per applicazioni semplici o per chi si avvicina per la prima volta alla programmazione GUI. L'aspetto grafico è essenziale, ma con il modulo `ttk` si possono ottenere risultati decorosi.

**PyQt6 e PySide6** sono i binding Python per il framework Qt, uno dei toolkit GUI più potenti e maturi in circolazione. Offrono un set enorme di widget, supporto per stylesheet CSS-like, strumenti di design visuale (Qt Designer) e prestazioni eccellenti. La differenza principale tra i due è la licenza: PyQt6 è distribuito sotto licenza GPL o commerciale, mentre PySide6 usa la licenza LGPL, più permissiva per progetti proprietari.

**CustomTkinter** è una libreria moderna che estende tkinter con widget dall'aspetto contemporaneo, temi chiari e scuri, e un'API intuitiva. Rappresenta un ottimo compromesso tra la semplicità di tkinter e l'estetica di framework più avanzati.

**Flet** è un framework relativamente recente basato su Flutter (di Google) che permette di costruire applicazioni web, desktop e mobile partendo dallo stesso codice Python, senza necessità di conoscere HTML, CSS o JavaScript.

**Dear PyGui** adotta il paradigma dell'immediate-mode GUI, particolarmente adatto per strumenti di sviluppo, visualizzazione dati e applicazioni ad alte prestazioni.

### Quando Costruire una GUI vs Interfaccia Web vs CLI

La scelta tra GUI desktop, interfaccia web e CLI dipende da diversi fattori. Una **GUI desktop** è preferibile quando l'applicazione deve funzionare offline, necessita di accesso diretto al filesystem o a periferiche hardware, richiede prestazioni elevate per elaborazioni grafiche, oppure quando gli utenti si aspettano un'esperienza nativa del sistema operativo.

Un'**interfaccia web** è più indicata quando l'applicazione deve essere accessibile da più dispositivi e piattaforme senza installazione, quando è necessario l'accesso concorrente di più utenti, o quando l'aggiornamento dell'applicazione deve essere centralizzato e immediato.

Una **CLI** è la scelta giusta per strumenti destinati a sviluppatori, script di automazione, operazioni batch, o quando l'applicazione deve integrarsi facilmente in pipeline e workflow di sistema.

---

## tkinter

### Fondamenti

tkinter (abbreviazione di "Tk interface") è il modulo GUI standard di Python. Si basa sul toolkit Tcl/Tk ed è disponibile su tutte le installazioni Python senza pacchetti aggiuntivi.

#### La Finestra Principale e il Loop degli Eventi

Ogni applicazione tkinter parte dalla creazione di una finestra principale (`Tk()`) e dall'avvio del loop degli eventi (`mainloop()`), che mantiene la finestra aperta e reattiva agli input dell'utente.

```python
import tkinter as tk

# Creazione della finestra principale
root = tk.Tk()
root.title("La Mia Prima Applicazione")
root.geometry("800x600")        # Larghezza x Altezza in pixel
root.minsize(400, 300)          # Dimensione minima
root.maxsize(1200, 900)         # Dimensione massima
root.resizable(True, True)      # Ridimensionabile (larghezza, altezza)
root.configure(bg="#f0f0f0")    # Colore di sfondo

# Centrare la finestra sullo schermo
root.update_idletasks()
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
x = (screen_w - 800) // 2
y = (screen_h - 600) // 2
root.geometry(f"800x600+{x}+{y}")

# Avvio del loop degli eventi
root.mainloop()
```

#### Widget Fondamentali

tkinter mette a disposizione una vasta gamma di widget. Ogni widget è un oggetto Python che viene creato specificando il widget genitore come primo argomento.

```python
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Catalogo Widget")
root.geometry("600x700")

# Label — etichetta di testo
label = tk.Label(root, text="Benvenuto nell'applicazione",
                 font=("Helvetica", 16, "bold"), fg="#333333")
label.pack(pady=10)

# Button — pulsante
def on_click():
    label.config(text="Pulsante premuto!")

btn = tk.Button(root, text="Cliccami", command=on_click,
                bg="#4CAF50", fg="white", font=("Helvetica", 12),
                padx=20, pady=5, relief="raised", cursor="hand2")
btn.pack(pady=5)

# Entry — campo di input a riga singola
entry = tk.Entry(root, width=40, font=("Helvetica", 12),
                 bd=2, relief="groove")
entry.insert(0, "Scrivi qui...")
entry.pack(pady=5)

# Text — area di testo multilinea
text = tk.Text(root, width=50, height=5, font=("Courier", 10),
               wrap="word", bd=2, relief="sunken")
text.insert("1.0", "Area di testo multilinea.\nScrivi liberamente.")
text.pack(pady=5)

# Listbox — lista di selezione
listbox = tk.Listbox(root, width=40, height=5, selectmode="multiple")
for elemento in ["Python", "Java", "C++", "Rust", "Go"]:
    listbox.insert(tk.END, elemento)
listbox.pack(pady=5)

# Combobox (ttk) — menu a tendina
combo = ttk.Combobox(root, values=["Opzione A", "Opzione B", "Opzione C"],
                     state="readonly", width=37)
combo.set("Seleziona un'opzione")
combo.pack(pady=5)

# Checkbutton — casella di spunta
check_var = tk.BooleanVar()
check = tk.Checkbutton(root, text="Accetto i termini",
                       variable=check_var, font=("Helvetica", 11))
check.pack(pady=5)

# Radiobutton — pulsante di opzione
radio_var = tk.StringVar(value="opzione1")
for testo, val in [("Opzione 1", "opzione1"), ("Opzione 2", "opzione2")]:
    tk.Radiobutton(root, text=testo, variable=radio_var,
                   value=val, font=("Helvetica", 11)).pack()

# Scale — cursore a scorrimento
scale = tk.Scale(root, from_=0, to=100, orient="horizontal",
                 length=300, label="Volume")
scale.pack(pady=5)

# Spinbox — selettore numerico
spinbox = tk.Spinbox(root, from_=1, to=50, width=10,
                     font=("Helvetica", 12))
spinbox.pack(pady=5)

root.mainloop()
```

#### Canvas — L'Area di Disegno

Il widget `Canvas` è uno degli strumenti più versatili di tkinter. Permette di disegnare forme geometriche, testo, immagini e di creare interfacce altamente personalizzate.

```python
import tkinter as tk

root = tk.Tk()
root.title("Canvas Demo")

canvas = tk.Canvas(root, width=500, height=400, bg="white")
canvas.pack(padx=10, pady=10)

# Forme geometriche
canvas.create_rectangle(20, 20, 150, 100, fill="#3498db",
                        outline="#2c3e50", width=2)
canvas.create_oval(170, 20, 300, 100, fill="#e74c3c",
                   outline="#c0392b", width=2)
canvas.create_line(20, 130, 300, 130, fill="#2ecc71",
                   width=3, dash=(5, 3))
canvas.create_polygon(350, 20, 480, 20, 415, 100,
                      fill="#f39c12", outline="#e67e22", width=2)
canvas.create_arc(20, 150, 150, 280, start=0, extent=270,
                  fill="#9b59b6", style="pieslice")

# Testo sul canvas
canvas.create_text(250, 350, text="Testo sul Canvas",
                   font=("Helvetica", 18, "italic"), fill="#34495e")

root.mainloop()
```

#### Layout Manager

tkinter offre tre layout manager per disporre i widget nella finestra.

**pack()** dispone i widget in blocchi, uno dopo l'altro. È il più semplice da usare ma offre meno controllo.

```python
import tkinter as tk

root = tk.Tk()
root.title("Pack Layout")

tk.Label(root, text="In alto", bg="#e74c3c", fg="white").pack(
    side="top", fill="x", pady=2)
tk.Label(root, text="In basso", bg="#3498db", fg="white").pack(
    side="bottom", fill="x", pady=2)
tk.Label(root, text="A sinistra", bg="#2ecc71", fg="white").pack(
    side="left", fill="y", padx=2)
tk.Label(root, text="A destra", bg="#f39c12", fg="white").pack(
    side="right", fill="y", padx=2)

root.mainloop()
```

**grid()** organizza i widget in una griglia di righe e colonne. Offre un controllo preciso sul posizionamento ed è il layout manager più utilizzato per form e interfacce strutturate.

```python
import tkinter as tk

root = tk.Tk()
root.title("Grid Layout — Form di Login")

tk.Label(root, text="Username:").grid(row=0, column=0,
                                       padx=10, pady=5, sticky="e")
tk.Entry(root, width=30).grid(row=0, column=1,
                               padx=10, pady=5, sticky="w")

tk.Label(root, text="Password:").grid(row=1, column=0,
                                       padx=10, pady=5, sticky="e")
tk.Entry(root, width=30, show="*").grid(row=1, column=1,
                                         padx=10, pady=5, sticky="w")

tk.Button(root, text="Accedi").grid(row=2, column=0, columnspan=2,
                                     pady=10)

# Configurare il peso delle colonne per il ridimensionamento
root.columnconfigure(1, weight=1)

root.mainloop()
```

**place()** posiziona i widget tramite coordinate assolute o relative. Offre il massimo controllo ma rende difficile la gestione del ridimensionamento.

```python
import tkinter as tk

root = tk.Tk()
root.title("Place Layout")
root.geometry("400x300")

# Coordinate assolute
tk.Label(root, text="Posizione fissa", bg="lightblue").place(x=50, y=30)

# Coordinate relative (0.0 = inizio, 1.0 = fine)
tk.Button(root, text="Centro").place(relx=0.5, rely=0.5, anchor="center")

# Combinazione di relative e dimensioni proporzionali
tk.Label(root, text="Barra in basso", bg="#34495e", fg="white").place(
    relx=0, rely=1.0, relwidth=1.0, height=30, anchor="sw")

root.mainloop()
```

#### Eventi e Binding

Il sistema di eventi di tkinter permette di collegare funzioni a eventi specifici come click del mouse, pressione dei tasti o movimenti del cursore.

```python
import tkinter as tk

root = tk.Tk()
root.title("Eventi e Binding")

label = tk.Label(root, text="Interagisci con la finestra",
                 font=("Helvetica", 14))
label.pack(pady=20)

# Binding di eventi al widget
def on_enter(event):
    label.config(text=f"Mouse in posizione: ({event.x}, {event.y})")

def on_key(event):
    label.config(text=f"Tasto premuto: {event.keysym}")

def on_right_click(event):
    label.config(text="Click destro rilevato!")

# <Button-1> = click sinistro, <Button-3> = click destro
root.bind("<Motion>", on_enter)
root.bind("<Key>", on_key)
root.bind("<Button-3>", on_right_click)

# Binding con lambda per passare argomenti aggiuntivi
btn = tk.Button(root, text="Premi Enter qui")
btn.pack(pady=10)
btn.bind("<Return>", lambda e: label.config(text="Enter premuto sul pulsante"))
btn.bind("<Enter>", lambda e: btn.config(bg="#e0e0e0"))
btn.bind("<Leave>", lambda e: btn.config(bg="SystemButtonFace"))

root.mainloop()
```

---

### Funzionalità Avanzate

#### Barre di Menu e Menu Contestuali

```python
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("Menu Completo")
root.geometry("500x400")

# Barra dei menu principale
menubar = tk.Menu(root)
root.config(menu=menubar)

# Menu File
file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Nuovo", accelerator="Ctrl+N",
                      command=lambda: messagebox.showinfo("Info", "Nuovo file"))
file_menu.add_command(label="Apri...", accelerator="Ctrl+O")
file_menu.add_command(label="Salva", accelerator="Ctrl+S")
file_menu.add_separator()
file_menu.add_command(label="Esci", command=root.quit)

# Menu Modifica con sottomenu
edit_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Modifica", menu=edit_menu)
edit_menu.add_command(label="Taglia", accelerator="Ctrl+X")
edit_menu.add_command(label="Copia", accelerator="Ctrl+C")
edit_menu.add_command(label="Incolla", accelerator="Ctrl+V")

# Menu contestuale (click destro)
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Copia")
context_menu.add_command(label="Incolla")
context_menu.add_separator()
context_menu.add_command(label="Proprietà")

def show_context_menu(event):
    context_menu.tk_popup(event.x_root, event.y_root)

root.bind("<Button-3>", show_context_menu)

root.mainloop()
```

#### Dialogs — Finestre di Dialogo

tkinter fornisce diversi moduli per finestre di dialogo predefinite.

```python
import tkinter as tk
from tkinter import messagebox, filedialog, colorchooser, simpledialog

root = tk.Tk()
root.title("Dialogs Demo")

# messagebox — finestre di messaggio
def mostra_info():
    messagebox.showinfo("Informazione", "Operazione completata con successo.")

def mostra_avviso():
    messagebox.showwarning("Attenzione", "Questa azione non è reversibile.")

def mostra_errore():
    messagebox.showerror("Errore", "Si è verificato un errore imprevisto.")

def chiedi_conferma():
    risposta = messagebox.askyesnocancel("Conferma", "Vuoi salvare le modifiche?")
    # risposta: True (Sì), False (No), None (Annulla)
    print(f"Risposta: {risposta}")

# filedialog — selezione file e cartelle
def apri_file():
    percorso = filedialog.askopenfilename(
        title="Seleziona un file",
        initialdir="/home",
        filetypes=[("File Python", "*.py"),
                   ("File di testo", "*.txt"),
                   ("Tutti i file", "*.*")]
    )
    if percorso:
        print(f"File selezionato: {percorso}")

def salva_file():
    percorso = filedialog.asksaveasfilename(
        title="Salva con nome",
        defaultextension=".txt",
        filetypes=[("File di testo", "*.txt"), ("Tutti i file", "*.*")]
    )
    if percorso:
        print(f"Salva in: {percorso}")

def seleziona_cartella():
    cartella = filedialog.askdirectory(title="Seleziona una cartella")
    if cartella:
        print(f"Cartella: {cartella}")

# colorchooser — selettore di colore
def scegli_colore():
    colore = colorchooser.askcolor(title="Scegli un colore")
    # colore: ((R, G, B), "#hexcode") oppure (None, None)
    if colore[1]:
        root.configure(bg=colore[1])

# simpledialog — input semplice
def chiedi_nome():
    nome = simpledialog.askstring("Input", "Come ti chiami?")
    if nome:
        print(f"Nome: {nome}")

def chiedi_eta():
    eta = simpledialog.askinteger("Input", "Quanti anni hai?",
                                   minvalue=0, maxvalue=150)
    if eta is not None:
        print(f"Età: {eta}")

# Creazione dei pulsanti
for testo, comando in [("Info", mostra_info), ("Avviso", mostra_avviso),
                        ("Errore", mostra_errore), ("Conferma", chiedi_conferma),
                        ("Apri File", apri_file), ("Salva File", salva_file),
                        ("Cartella", seleziona_cartella), ("Colore", scegli_colore),
                        ("Nome", chiedi_nome), ("Età", chiedi_eta)]:
    tk.Button(root, text=testo, command=comando, width=15).pack(pady=3)

root.mainloop()
```

#### ttk — Widget con Temi

Il modulo `ttk` (themed tkinter) fornisce versioni stilizzate dei widget standard. Utilizzano il tema nativo del sistema operativo, offrendo un aspetto più professionale e coerente.

```python
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("ttk Themed Widgets")

# Visualizzare i temi disponibili
stile = ttk.Style()
print("Temi disponibili:", stile.theme_names())
stile.theme_use("clam")  # 'clam', 'alt', 'default', 'classic'

# Personalizzazione degli stili
stile.configure("Custom.TButton",
                foreground="white",
                background="#3498db",
                font=("Helvetica", 11, "bold"),
                padding=10)
stile.map("Custom.TButton",
          background=[("active", "#2980b9"), ("disabled", "#bdc3c7")])

# Notebook — widget a schede
notebook = ttk.Notebook(root)
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
notebook.add(tab1, text="Scheda 1")
notebook.add(tab2, text="Scheda 2")
notebook.pack(expand=True, fill="both", padx=10, pady=10)

# Treeview — tabella/albero
tree = ttk.Treeview(tab1, columns=("nome", "eta", "citta"),
                    show="headings", height=5)
tree.heading("nome", text="Nome")
tree.heading("eta", text="Età")
tree.heading("citta", text="Città")
tree.column("nome", width=150)
tree.column("eta", width=50, anchor="center")
tree.column("citta", width=120)

dati = [("Mario Rossi", 35, "Roma"),
        ("Giulia Bianchi", 28, "Milano"),
        ("Luca Verdi", 42, "Napoli")]
for d in dati:
    tree.insert("", tk.END, values=d)
tree.pack(padx=10, pady=10)

# Progressbar
progress = ttk.Progressbar(tab2, length=300, mode="determinate")
progress.pack(pady=20)

def avanza():
    progress["value"] += 10
    if progress["value"] >= 100:
        progress["value"] = 0

ttk.Button(tab2, text="Avanza", command=avanza,
           style="Custom.TButton").pack(pady=5)

# Separator
ttk.Separator(tab2, orient="horizontal").pack(fill="x", padx=20, pady=10)

# LabelFrame
frame = ttk.LabelFrame(tab2, text="Opzioni", padding=10)
frame.pack(padx=20, pady=5, fill="x")
ttk.Checkbutton(frame, text="Opzione attiva").pack(anchor="w")

root.mainloop()
```

#### Variabili di Controllo

Le variabili di controllo (`StringVar`, `IntVar`, `DoubleVar`, `BooleanVar`) permettono di sincronizzare automaticamente i dati tra widget e logica applicativa.

```python
import tkinter as tk

root = tk.Tk()
root.title("Variabili di Controllo")

# StringVar — si aggiorna automaticamente in tutti i widget collegati
nome_var = tk.StringVar(value="Inserisci il tuo nome")
nome_var.trace_add("write", lambda *args: label.config(
    text=f"Ciao, {nome_var.get()}!"))

tk.Entry(root, textvariable=nome_var, width=30).pack(pady=5)
label = tk.Label(root, text="Ciao!", font=("Helvetica", 14))
label.pack(pady=5)

# IntVar — per valori interi
contatore = tk.IntVar(value=0)
tk.Label(root, textvariable=contatore, font=("Helvetica", 24)).pack()
tk.Button(root, text="+1",
          command=lambda: contatore.set(contatore.get() + 1)).pack()

# BooleanVar — per checkbox
dark_mode = tk.BooleanVar(value=False)
def toggle_dark():
    bg = "#2c3e50" if dark_mode.get() else "SystemButtonFace"
    fg = "white" if dark_mode.get() else "black"
    root.configure(bg=bg)
    label.config(bg=bg, fg=fg)

tk.Checkbutton(root, text="Modalità scura", variable=dark_mode,
               command=toggle_dark).pack(pady=10)

root.mainloop()
```

#### Finestre Multiple — Toplevel

```python
import tkinter as tk

root = tk.Tk()
root.title("Finestra Principale")

def apri_secondaria():
    finestra = tk.Toplevel(root)
    finestra.title("Finestra Secondaria")
    finestra.geometry("300x200")
    finestra.transient(root)     # Collegata alla finestra principale
    finestra.grab_set()          # Modale: blocca l'interazione con la principale

    tk.Label(finestra, text="Finestra secondaria",
             font=("Helvetica", 14)).pack(pady=20)
    tk.Button(finestra, text="Chiudi",
              command=finestra.destroy).pack(pady=10)

    # Centrare rispetto alla finestra principale
    finestra.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - 300) // 2
    y = root.winfo_y() + (root.winfo_height() - 200) // 2
    finestra.geometry(f"+{x}+{y}")

tk.Button(root, text="Apri Finestra", command=apri_secondaria).pack(pady=30)
root.mainloop()
```

#### Threading con tkinter

Le operazioni di lunga durata (richieste di rete, elaborazioni pesanti) bloccano il `mainloop()` e rendono l'interfaccia non reattiva. La soluzione è eseguire queste operazioni in thread separati, comunicando con l'interfaccia tramite il metodo `after()`.

```python
import tkinter as tk
from tkinter import ttk
import threading
import time

root = tk.Tk()
root.title("Threading con tkinter")

progress = ttk.Progressbar(root, length=400, mode="determinate")
progress.pack(pady=20, padx=20)

status_label = tk.Label(root, text="Pronto", font=("Helvetica", 12))
status_label.pack(pady=5)

def operazione_lunga():
    """Simula un'operazione lunga in un thread separato."""
    for i in range(101):
        time.sleep(0.05)  # Simula lavoro
        # Aggiorna l'interfaccia dal thread principale tramite after()
        root.after(0, lambda v=i: aggiorna_progresso(v))
    root.after(0, operazione_completata)

def aggiorna_progresso(valore):
    progress["value"] = valore
    status_label.config(text=f"Elaborazione: {valore}%")

def operazione_completata():
    status_label.config(text="Completato!")
    btn.config(state="normal")

def avvia():
    btn.config(state="disabled")
    status_label.config(text="Elaborazione in corso...")
    thread = threading.Thread(target=operazione_lunga, daemon=True)
    thread.start()

btn = tk.Button(root, text="Avvia Operazione", command=avvia,
                font=("Helvetica", 12))
btn.pack(pady=10)

root.mainloop()
```

---

### Applicazione Completa

Di seguito un'applicazione CRUD completa per la gestione dei contatti, strutturata secondo il pattern MVC (Model-View-Controller).

```python
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# ───────────────── MODEL ─────────────────
class ContattoModel:
    """Gestisce i dati dei contatti con persistenza su file JSON."""

    def __init__(self, filepath="contatti.json"):
        self.filepath = filepath
        self.contatti = []
        self.carica()

    def carica(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.contatti = json.load(f)

    def salva(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.contatti, f, indent=2, ensure_ascii=False)

    def aggiungi(self, nome, telefono, email):
        contatto = {"nome": nome, "telefono": telefono, "email": email}
        self.contatti.append(contatto)
        self.salva()
        return contatto

    def aggiorna(self, indice, nome, telefono, email):
        self.contatti[indice] = {"nome": nome, "telefono": telefono,
                                 "email": email}
        self.salva()

    def elimina(self, indice):
        del self.contatti[indice]
        self.salva()

    def cerca(self, termine):
        termine = termine.lower()
        return [(i, c) for i, c in enumerate(self.contatti)
                if termine in c["nome"].lower()
                or termine in c["telefono"]
                or termine in c["email"].lower()]

    def tutti(self):
        return list(enumerate(self.contatti))


# ───────────────── VIEW ─────────────────
class ContattoView(ttk.Frame):
    """Interfaccia grafica per la gestione dei contatti."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.pack(expand=True, fill="both")
        self._crea_barra_ricerca()
        self._crea_tabella()
        self._crea_form()
        self._crea_pulsanti()

    def _crea_barra_ricerca(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", pady=(0, 10))
        ttk.Label(frame, text="Cerca:").pack(side="left")
        self.ricerca_var = tk.StringVar()
        self.entry_ricerca = ttk.Entry(frame, textvariable=self.ricerca_var,
                                       width=40)
        self.entry_ricerca.pack(side="left", padx=5)
        self.btn_cerca = ttk.Button(frame, text="Cerca")
        self.btn_cerca.pack(side="left")
        self.btn_mostra_tutti = ttk.Button(frame, text="Mostra Tutti")
        self.btn_mostra_tutti.pack(side="left", padx=5)

    def _crea_tabella(self):
        cols = ("nome", "telefono", "email")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                 height=10)
        self.tree.heading("nome", text="Nome")
        self.tree.heading("telefono", text="Telefono")
        self.tree.heading("email", text="Email")
        self.tree.column("nome", width=180)
        self.tree.column("telefono", width=130)
        self.tree.column("email", width=200)

        scrollbar = ttk.Scrollbar(self, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

    def _crea_form(self):
        frame = ttk.LabelFrame(self, text="Dettagli Contatto", padding=10)
        frame.pack(fill="x", pady=10)

        self.nome_var = tk.StringVar()
        self.telefono_var = tk.StringVar()
        self.email_var = tk.StringVar()

        for r, (lbl, var) in enumerate([("Nome:", self.nome_var),
                                         ("Telefono:", self.telefono_var),
                                         ("Email:", self.email_var)]):
            ttk.Label(frame, text=lbl).grid(row=r, column=0,
                                             sticky="e", padx=5, pady=3)
            ttk.Entry(frame, textvariable=var, width=35).grid(
                row=r, column=1, sticky="w", padx=5, pady=3)

    def _crea_pulsanti(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x")
        self.btn_aggiungi = ttk.Button(frame, text="Aggiungi")
        self.btn_aggiorna = ttk.Button(frame, text="Aggiorna")
        self.btn_elimina = ttk.Button(frame, text="Elimina")
        self.btn_pulisci = ttk.Button(frame, text="Pulisci")
        for btn in (self.btn_aggiungi, self.btn_aggiorna,
                    self.btn_elimina, self.btn_pulisci):
            btn.pack(side="left", padx=5, pady=5)


# ───────────────── CONTROLLER ─────────────────
class ContattoController:
    """Collega il Model alla View e gestisce la logica."""

    def __init__(self, root):
        self.model = ContattoModel()
        self.view = ContattoView(root)
        self._bind_eventi()
        self.aggiorna_tabella(self.model.tutti())

    def _bind_eventi(self):
        self.view.btn_aggiungi.config(command=self.aggiungi)
        self.view.btn_aggiorna.config(command=self.aggiorna)
        self.view.btn_elimina.config(command=self.elimina)
        self.view.btn_pulisci.config(command=self.pulisci_form)
        self.view.btn_cerca.config(command=self.cerca)
        self.view.btn_mostra_tutti.config(command=self.mostra_tutti)
        self.view.tree.bind("<<TreeviewSelect>>", self.on_seleziona)

    def aggiorna_tabella(self, contatti):
        for item in self.view.tree.get_children():
            self.view.tree.delete(item)
        for indice, c in contatti:
            self.view.tree.insert("", tk.END, iid=str(indice),
                                  values=(c["nome"], c["telefono"],
                                          c["email"]))

    def aggiungi(self):
        nome = self.view.nome_var.get().strip()
        telefono = self.view.telefono_var.get().strip()
        email = self.view.email_var.get().strip()
        if not nome:
            messagebox.showwarning("Attenzione", "Il nome è obbligatorio.")
            return
        self.model.aggiungi(nome, telefono, email)
        self.aggiorna_tabella(self.model.tutti())
        self.pulisci_form()

    def aggiorna(self):
        selezione = self.view.tree.selection()
        if not selezione:
            messagebox.showwarning("Attenzione", "Seleziona un contatto.")
            return
        indice = int(selezione[0])
        self.model.aggiorna(indice,
                            self.view.nome_var.get().strip(),
                            self.view.telefono_var.get().strip(),
                            self.view.email_var.get().strip())
        self.aggiorna_tabella(self.model.tutti())
        self.pulisci_form()

    def elimina(self):
        selezione = self.view.tree.selection()
        if not selezione:
            messagebox.showwarning("Attenzione", "Seleziona un contatto.")
            return
        if messagebox.askyesno("Conferma", "Eliminare il contatto?"):
            self.model.elimina(int(selezione[0]))
            self.aggiorna_tabella(self.model.tutti())
            self.pulisci_form()

    def cerca(self):
        termine = self.view.ricerca_var.get().strip()
        risultati = self.model.cerca(termine) if termine else self.model.tutti()
        self.aggiorna_tabella(risultati)

    def mostra_tutti(self):
        self.view.ricerca_var.set("")
        self.aggiorna_tabella(self.model.tutti())

    def on_seleziona(self, event):
        selezione = self.view.tree.selection()
        if selezione:
            valori = self.view.tree.item(selezione[0])["values"]
            self.view.nome_var.set(valori[0])
            self.view.telefono_var.set(valori[1])
            self.view.email_var.set(valori[2])

    def pulisci_form(self):
        self.view.nome_var.set("")
        self.view.telefono_var.set("")
        self.view.email_var.set("")
        self.view.tree.selection_remove(*self.view.tree.selection())


# ───────────────── MAIN ─────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Gestione Contatti")
    root.geometry("650x550")
    app = ContattoController(root)
    root.mainloop()
```

Il pattern MVC separa chiaramente le responsabilità: il **Model** gestisce i dati e la persistenza, la **View** si occupa dell'interfaccia grafica, e il **Controller** coordina la comunicazione tra i due. Questa separazione facilita la manutenzione, il testing e l'evoluzione dell'applicazione.

---

## PyQt6 / PySide6

### Fondamenti PyQt6

PyQt6 e PySide6 sono i binding Python per Qt 6, uno dei framework GUI più completi e maturi disponibili. L'API dei due è quasi identica; gli esempi seguenti usano PyQt6 ma sono facilmente adattabili a PySide6 cambiando semplicemente gli import.

```bash
pip install PyQt6
# oppure
pip install PySide6
```

#### La Struttura Base

```python
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget,
                              QVBoxLayout, QLabel, QPushButton)
from PyQt6.QtCore import Qt

class FinestraPrincipale(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prima App PyQt6")
        self.setGeometry(200, 200, 600, 400)

        # Widget centrale obbligatorio per QMainWindow
        widget_centrale = QWidget()
        self.setCentralWidget(widget_centrale)

        # Layout
        layout = QVBoxLayout(widget_centrale)

        # Widget
        self.label = QLabel("Benvenuto in PyQt6!")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 20px; color: #2c3e50;")
        layout.addWidget(self.label)

        btn = QPushButton("Cliccami")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14px;
                padding: 10px 30px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        btn.clicked.connect(self.on_click)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def on_click(self):
        self.label.setText("Pulsante premuto!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    finestra = FinestraPrincipale()
    finestra.show()
    sys.exit(app.exec())
```

#### Widget Principali e Layout

```python
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QRadioButton,
    QSlider, QProgressBar, QSpinBox, QGroupBox)
from PyQt6.QtCore import Qt

class DemoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Widget PyQt6")
        self.setMinimumSize(700, 600)

        layout_principale = QVBoxLayout(self)

        # ── QFormLayout per i campi di input ──
        form_group = QGroupBox("Form di Input")
        form_layout = QFormLayout(form_group)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Scrivi il tuo nome...")
        form_layout.addRow("Nome:", self.line_edit)

        self.combo = QComboBox()
        self.combo.addItems(["Python", "Java", "C++", "Rust"])
        form_layout.addRow("Linguaggio:", self.combo)

        self.spin = QSpinBox()
        self.spin.setRange(0, 100)
        self.spin.setValue(25)
        form_layout.addRow("Valore:", self.spin)

        layout_principale.addWidget(form_group)

        # ── QGridLayout per checkbox e radio ──
        opzioni_group = QGroupBox("Opzioni")
        grid = QGridLayout(opzioni_group)

        self.check1 = QCheckBox("Opzione A")
        self.check2 = QCheckBox("Opzione B")
        grid.addWidget(self.check1, 0, 0)
        grid.addWidget(self.check2, 0, 1)

        self.radio1 = QRadioButton("Scelta 1")
        self.radio2 = QRadioButton("Scelta 2")
        self.radio1.setChecked(True)
        grid.addWidget(self.radio1, 1, 0)
        grid.addWidget(self.radio2, 1, 1)

        layout_principale.addWidget(opzioni_group)

        # ── Slider e ProgressBar ──
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.progress = QProgressBar()
        self.slider.valueChanged.connect(self.progress.setValue)
        layout_principale.addWidget(QLabel("Slider collegato alla ProgressBar:"))
        layout_principale.addWidget(self.slider)
        layout_principale.addWidget(self.progress)

        # ── QTextEdit ──
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Area di testo multilinea...")
        self.text_edit.setMaximumHeight(100)
        layout_principale.addWidget(self.text_edit)

        # ── Pulsante di riepilogo ──
        btn = QPushButton("Mostra Riepilogo")
        btn.clicked.connect(self.mostra_riepilogo)
        layout_principale.addWidget(btn)

        self.label_risultato = QLabel("")
        layout_principale.addWidget(self.label_risultato)

    def mostra_riepilogo(self):
        riepilogo = (
            f"Nome: {self.line_edit.text()}\n"
            f"Linguaggio: {self.combo.currentText()}\n"
            f"Valore: {self.spin.value()}\n"
            f"Slider: {self.slider.value()}"
        )
        self.label_risultato.setText(riepilogo)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = DemoWidget()
    demo.show()
    sys.exit(app.exec())
```

#### Signals e Slots

Il meccanismo di Signals e Slots è il cuore del sistema di comunicazione tra oggetti in Qt. Un **signal** viene emesso quando si verifica un evento; uno **slot** è una funzione che viene eseguita in risposta.

```python
from PyQt6.QtCore import pyqtSignal, QObject

class Sensore(QObject):
    # Definizione di segnali personalizzati
    temperatura_cambiata = pyqtSignal(float)
    allarme = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._temperatura = 20.0

    @property
    def temperatura(self):
        return self._temperatura

    @temperatura.setter
    def temperatura(self, valore):
        self._temperatura = valore
        self.temperatura_cambiata.emit(valore)
        if valore > 40.0:
            self.allarme.emit(f"Temperatura critica: {valore}°C!")

# Collegamento dei segnali agli slot
sensore = Sensore()
sensore.temperatura_cambiata.connect(
    lambda t: print(f"Temperatura attuale: {t}°C"))
sensore.allarme.connect(
    lambda msg: print(f"ALLARME: {msg}"))

sensore.temperatura = 25.0   # Stampa: Temperatura attuale: 25.0°C
sensore.temperatura = 45.0   # Stampa entrambi: temperatura + allarme
```

---

### Funzionalità Avanzate PyQt6

#### QTableWidget e QTreeWidget

```python
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget,
    QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QHeaderView)
from PyQt6.QtCore import Qt
import sys

class TabellaDemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Table e Tree Widget")
        self.setGeometry(100, 100, 700, 500)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # ── QTableWidget ──
        tabella = QTableWidget(5, 3)
        tabella.setHorizontalHeaderLabels(["Nome", "Età", "Città"])
        tabella.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)

        dati = [("Mario", "35", "Roma"), ("Giulia", "28", "Milano"),
                ("Luca", "42", "Napoli"), ("Sara", "31", "Firenze"),
                ("Marco", "27", "Torino")]
        for riga, (nome, eta, citta) in enumerate(dati):
            tabella.setItem(riga, 0, QTableWidgetItem(nome))
            tabella.setItem(riga, 1, QTableWidgetItem(eta))
            tabella.setItem(riga, 2, QTableWidgetItem(citta))
        tabs.addTab(tabella, "Tabella")

        # ── QTreeWidget ──
        albero = QTreeWidget()
        albero.setHeaderLabels(["Elemento", "Tipo"])
        albero.setColumnWidth(0, 300)

        root_item = QTreeWidgetItem(albero, ["Progetto Python", "Cartella"])
        src = QTreeWidgetItem(root_item, ["src", "Cartella"])
        QTreeWidgetItem(src, ["main.py", "File Python"])
        QTreeWidgetItem(src, ["utils.py", "File Python"])
        tests = QTreeWidgetItem(root_item, ["tests", "Cartella"])
        QTreeWidgetItem(tests, ["test_main.py", "File Test"])
        root_item.setExpanded(True)
        src.setExpanded(True)
        tabs.addTab(albero, "Albero")

app = QApplication(sys.argv)
win = TabellaDemoWindow()
win.show()
sys.exit(app.exec())
```

#### Menu, Toolbar e StatusBar

```python
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit,
    QFileDialog, QMessageBox)
from PyQt6.QtGui import QAction, QIcon, QKeySequence
import sys

class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor di Testo")
        self.setGeometry(100, 100, 800, 600)

        self.editor = QTextEdit()
        self.setCentralWidget(self.editor)

        self._crea_menu()
        self._crea_toolbar()
        self._crea_statusbar()

    def _crea_menu(self):
        menubar = self.menuBar()

        # Menu File
        file_menu = menubar.addMenu("&File")

        apri_action = QAction("&Apri", self)
        apri_action.setShortcut(QKeySequence("Ctrl+O"))
        apri_action.triggered.connect(self.apri_file)
        file_menu.addAction(apri_action)

        salva_action = QAction("&Salva", self)
        salva_action.setShortcut(QKeySequence("Ctrl+S"))
        salva_action.triggered.connect(self.salva_file)
        file_menu.addAction(salva_action)

        file_menu.addSeparator()

        esci_action = QAction("&Esci", self)
        esci_action.setShortcut(QKeySequence("Ctrl+Q"))
        esci_action.triggered.connect(self.close)
        file_menu.addAction(esci_action)

        # Menu Aiuto
        help_menu = menubar.addMenu("&Aiuto")
        info_action = QAction("&Informazioni", self)
        info_action.triggered.connect(lambda: QMessageBox.about(
            self, "Info", "Editor di Testo v1.0"))
        help_menu.addAction(info_action)

    def _crea_toolbar(self):
        toolbar = self.addToolBar("Strumenti")
        toolbar.addAction("Apri")
        toolbar.addAction("Salva")
        toolbar.addSeparator()
        toolbar.addAction("Taglia")
        toolbar.addAction("Copia")
        toolbar.addAction("Incolla")

    def _crea_statusbar(self):
        self.statusBar().showMessage("Pronto")
        self.editor.textChanged.connect(
            lambda: self.statusBar().showMessage(
                f"Caratteri: {len(self.editor.toPlainText())}"))

    def apri_file(self):
        percorso, _ = QFileDialog.getOpenFileName(
            self, "Apri File", "",
            "File di Testo (*.txt);;Tutti i File (*)")
        if percorso:
            with open(percorso, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
            self.statusBar().showMessage(f"Aperto: {percorso}")

    def salva_file(self):
        percorso, _ = QFileDialog.getSaveFileName(
            self, "Salva File", "",
            "File di Testo (*.txt);;Tutti i File (*)")
        if percorso:
            with open(percorso, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.statusBar().showMessage(f"Salvato: {percorso}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = EditorWindow()
    editor.show()
    sys.exit(app.exec())
```

#### Stylesheet — CSS di Qt

Qt supporta un potente sistema di stylesheet simile al CSS per personalizzare l'aspetto di qualsiasi widget.

```python
# Applicare uno stile globale all'intera applicazione
app.setStyleSheet("""
    QMainWindow {
        background-color: #ecf0f1;
    }
    QPushButton {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #2980b9;
    }
    QPushButton:pressed {
        background-color: #21618c;
    }
    QPushButton:disabled {
        background-color: #bdc3c7;
        color: #7f8c8d;
    }
    QLineEdit {
        border: 2px solid #bdc3c7;
        border-radius: 4px;
        padding: 6px;
        font-size: 13px;
    }
    QLineEdit:focus {
        border-color: #3498db;
    }
    QTableWidget {
        gridline-color: #dcdde1;
        selection-background-color: #74b9ff;
    }
    QTableWidget::item:hover {
        background-color: #dfe6e9;
    }
    QHeaderView::section {
        background-color: #2c3e50;
        color: white;
        padding: 6px;
        border: none;
    }
""")
```

#### Threading con QThread

```python
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
    QPushButton, QProgressBar, QLabel)
import sys
import time

class Worker(QObject):
    """Worker che esegue operazioni in un thread separato."""
    progresso = pyqtSignal(int)
    completato = pyqtSignal(str)
    errore = pyqtSignal(str)

    def esegui(self):
        try:
            for i in range(101):
                time.sleep(0.03)
                self.progresso.emit(i)
            self.completato.emit("Elaborazione terminata con successo!")
        except Exception as e:
            self.errore.emit(str(e))

class AppThread(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QThread Demo")
        layout = QVBoxLayout(self)

        self.progress = QProgressBar()
        self.label = QLabel("Pronto")
        self.btn = QPushButton("Avvia")
        self.btn.clicked.connect(self.avvia_worker)

        layout.addWidget(self.progress)
        layout.addWidget(self.label)
        layout.addWidget(self.btn)

    def avvia_worker(self):
        self.btn.setEnabled(False)
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.esegui)
        self.worker.progresso.connect(self.progress.setValue)
        self.worker.completato.connect(self.on_completato)
        self.worker.errore.connect(lambda e: self.label.setText(f"Errore: {e}"))
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_completato(self, messaggio):
        self.label.setText(messaggio)
        self.btn.setEnabled(True)
        self.thread.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AppThread()
    win.show()
    sys.exit(app.exec())
```

---

### Qt Designer

Qt Designer è uno strumento di design visuale incluso nelle installazioni di Qt. Permette di costruire interfacce grafiche tramite drag-and-drop, generando file `.ui` in formato XML che possono essere caricati direttamente da Python.

#### Installazione e Avvio

```bash
pip install pyqt6-tools
# Avviare Qt Designer
pyqt6-tools designer
```

#### Caricamento di File .ui

Esistono due approcci per utilizzare i file `.ui` generati da Qt Designer.

**Approccio 1 — Caricamento diretto a runtime:**

```python
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow
import sys

class MiaFinestra(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("interfaccia.ui", self)

        # Accesso ai widget definiti nel file .ui tramite objectName
        self.pushButton.clicked.connect(self.on_click)

    def on_click(self):
        testo = self.lineEdit.text()
        self.label.setText(f"Hai scritto: {testo}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    finestra = MiaFinestra()
    finestra.show()
    sys.exit(app.exec())
```

**Approccio 2 — Conversione in codice Python:**

```bash
# Genera un file Python dal file .ui
pyuic6 -o ui_interfaccia.py interfaccia.ui
```

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from ui_interfaccia import Ui_MainWindow
import sys

class MiaFinestra(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.on_click)

    def on_click(self):
        self.label.setText(f"Hai scritto: {self.lineEdit.text()}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    finestra = MiaFinestra()
    finestra.show()
    sys.exit(app.exec())
```

Il primo approccio è più rapido durante lo sviluppo perché non richiede la ricompilazione del file `.ui` ad ogni modifica. Il secondo approccio è preferibile per la distribuzione perché elimina la dipendenza dal file `.ui` esterno e consente un migliore controllo tramite IDE e type checking.

---

## CustomTkinter

CustomTkinter è una libreria che estende tkinter con un aspetto moderno e contemporaneo. Offre widget dal design pulito, supporto nativo per temi chiari e scuri, e un'API coerente e intuitiva.

```bash
pip install customtkinter
```

```python
import customtkinter as ctk

# Configurazione globale dell'aspetto
ctk.set_appearance_mode("dark")     # "dark", "light", "system"
ctk.set_default_color_theme("blue") # "blue", "green", "dark-blue"

class AppModerna(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("App CustomTkinter")
        self.geometry("500x450")

        # Frame principale con padding
        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Titolo
        ctk.CTkLabel(frame, text="Registrazione",
                     font=("Helvetica", 24, "bold")).pack(pady=(20, 10))

        # Campi di input con placeholder
        self.entry_nome = ctk.CTkEntry(frame, placeholder_text="Nome",
                                        width=300, height=40)
        self.entry_nome.pack(pady=8)

        self.entry_email = ctk.CTkEntry(frame, placeholder_text="Email",
                                         width=300, height=40)
        self.entry_email.pack(pady=8)

        self.entry_password = ctk.CTkEntry(frame, placeholder_text="Password",
                                            show="*", width=300, height=40)
        self.entry_password.pack(pady=8)

        # Selettore con segmented button
        self.ruolo = ctk.CTkSegmentedButton(frame,
            values=["Utente", "Admin", "Moderatore"], width=300)
        self.ruolo.set("Utente")
        self.ruolo.pack(pady=8)

        # Switch (toggle)
        self.newsletter = ctk.CTkSwitch(frame, text="Iscriviti alla newsletter")
        self.newsletter.pack(pady=8)

        # Slider
        self.slider = ctk.CTkSlider(frame, from_=0, to=100, width=300)
        self.slider.pack(pady=8)

        # Pulsante di conferma
        ctk.CTkButton(frame, text="Registrati", command=self.registra,
                       width=300, height=40, corner_radius=8,
                       font=("Helvetica", 14, "bold")).pack(pady=15)

        # Selettore tema
        ctk.CTkOptionMenu(self, values=["Dark", "Light", "System"],
                          command=self.cambia_tema, width=140).pack(pady=5)

    def registra(self):
        print(f"Nome: {self.entry_nome.get()}")
        print(f"Email: {self.entry_email.get()}")
        print(f"Ruolo: {self.ruolo.get()}")

    def cambia_tema(self, scelta):
        ctk.set_appearance_mode(scelta.lower())

if __name__ == "__main__":
    app = AppModerna()
    app.mainloop()
```

**Confronto con tkinter standard:** CustomTkinter mantiene la stessa architettura e filosofia di tkinter ma offre widget con angoli arrotondati, colori moderni, supporto nativo per la modalità scura, placeholder text negli Entry, e widget aggiuntivi come `CTkSegmentedButton`, `CTkSwitch` e `CTkScrollableFrame`. La curva di apprendimento per chi conosce già tkinter è minima, rendendo CustomTkinter un'ottima scelta per modernizzare rapidamente l'aspetto delle applicazioni.

---

## Flet

Flet è un framework innovativo che porta la potenza di Flutter (il toolkit UI di Google) nel mondo Python. Permette di creare applicazioni web, desktop e mobile partendo da un unico codice sorgente Python, senza necessità di conoscere HTML, CSS, JavaScript o Dart.

```bash
pip install flet
```

```python
import flet as ft

def main(page: ft.Page):
    page.title = "App Flet"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 30
    page.window.width = 500
    page.window.height = 600

    # Lista delle attività
    lista = ft.Column(spacing=5)

    def aggiungi_task(e):
        if campo.value.strip():
            task_row = ft.Row([
                ft.Checkbox(label=campo.value),
                ft.IconButton(ft.Icons.DELETE,
                              on_click=lambda e, r=None: rimuovi(r))
            ])
            # Correzione: assegnare la riga alla closure
            task_row.controls[1].on_click = lambda e, r=task_row: rimuovi(r)
            lista.controls.append(task_row)
            campo.value = ""
            page.update()

    def rimuovi(riga):
        lista.controls.remove(riga)
        page.update()

    # Header
    page.add(
        ft.Text("Lista Attività", size=28, weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_700),
        ft.Divider(height=20),
    )

    # Campo di input e pulsante
    campo = ft.TextField(hint_text="Nuova attività...", expand=True,
                         on_submit=aggiungi_task)
    page.add(
        ft.Row([campo,
                ft.FloatingActionButton(icon=ft.Icons.ADD,
                                         on_click=aggiungi_task)]),
        ft.Divider(height=10),
        lista
    )

# Avvio come app desktop
ft.app(target=main)

# Oppure come web app:
# ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)
```

Flet si distingue per la possibilità di eseguire la stessa applicazione come app desktop nativa, come web app nel browser, o come app mobile (iOS e Android), il tutto partendo dallo stesso codice Python. Questo lo rende particolarmente attraente per progetti che necessitano di distribuzione multipiattaforma.

---

## Dear PyGui

Dear PyGui è un framework GUI Python che adotta il paradigma dell'**immediate-mode GUI** (IMGUI). A differenza dei toolkit tradizionali (retained-mode), in una IMGUI l'interfaccia viene ridisegnata interamente ad ogni frame. Questo approccio è particolarmente efficiente per strumenti di sviluppo, dashboard, visualizzazione dati in tempo reale e applicazioni con rendering GPU.

```bash
pip install dearpygui
```

```python
import dearpygui.dearpygui as dpg

dpg.create_context()

# Funzioni di callback
def slider_callback(sender, app_data):
    dpg.set_value("testo_valore", f"Valore: {app_data:.1f}")

def pulsante_callback():
    dpg.set_value("testo_valore", "Pulsante premuto!")

# Finestra principale
with dpg.window(label="Dashboard", tag="finestra_principale"):
    dpg.add_text("Dear PyGui Demo", color=(100, 200, 255))
    dpg.add_separator()

    dpg.add_input_text(label="Nome", hint="Inserisci il tuo nome")
    dpg.add_slider_float(label="Slider", default_value=50.0,
                         min_value=0, max_value=100,
                         callback=slider_callback)
    dpg.add_text("Valore: 50.0", tag="testo_valore")

    dpg.add_button(label="Premi", callback=pulsante_callback)
    dpg.add_checkbox(label="Opzione attiva")
    dpg.add_color_picker(label="Colore", default_value=(255, 100, 50, 255))

    # Grafico integrato
    with dpg.plot(label="Grafico", height=200, width=-1):
        dpg.add_plot_axis(dpg.mvXAxis, label="X")
        with dpg.plot_axis(dpg.mvYAxis, label="Y"):
            dpg.add_line_series(
                [0, 1, 2, 3, 4, 5],
                [0, 1, 4, 9, 16, 25],
                label="y = x^2"
            )

dpg.create_viewport(title="Dear PyGui App", width=700, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("finestra_principale", True)
dpg.start_dearpygui()
dpg.destroy_context()
```

I casi d'uso ideali per Dear PyGui includono dashboard per la visualizzazione dati in tempo reale, strumenti di debug e profiling, editor di configurazione, interfacce per strumenti di machine learning e applicazioni che richiedono rendering ad alte prestazioni grazie al backend GPU (OpenGL/Vulkan).

---

## Packaging GUI Applications

Distribuire un'applicazione Python con GUI richiede strumenti specifici per creare eseguibili standalone che non necessitino dell'installazione di Python da parte dell'utente finale.

### PyInstaller

PyInstaller è lo strumento più popolare per la creazione di eseguibili Python. Supporta Windows, macOS e Linux ed è in grado di includere automaticamente tutte le dipendenze.

```bash
pip install pyinstaller
```

#### Uso Base

```bash
# Eseguibile in una singola cartella (più veloce da creare)
pyinstaller app.py

# Eseguibile in un singolo file (più comodo da distribuire)
pyinstaller --onefile app.py

# Senza console (per app GUI su Windows)
pyinstaller --onefile --noconsole app.py

# Con icona personalizzata
pyinstaller --onefile --noconsole --icon=icona.ico app.py

# Specificare il nome dell'eseguibile
pyinstaller --onefile --noconsole --name="MiaApp" app.py
```

#### File Spec per Configurazioni Avanzate

Per configurazioni più complesse, PyInstaller genera un file `.spec` che può essere personalizzato.

```python
# app.spec
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/immagini', 'assets/immagini'),  # (sorgente, destinazione)
        ('config.json', '.'),
        ('database.db', '.'),
    ],
    hiddenimports=['pkg_resources.py2_warn'],  # Import nascosti
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy'],  # Escludi librerie non necessarie
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MiaApp',
    debug=False,
    strip=False,
    upx=True,              # Compressione UPX
    console=False,          # Nessuna console
    icon='icona.ico',
)
```

```bash
# Costruire dall'file spec
pyinstaller app.spec
```

#### Gestione dei Percorsi Risorse

Quando si impacchetta un'applicazione, i percorsi relativi ai file di risorse cambiano. È necessario gestire correttamente la risoluzione dei percorsi.

```python
import sys
import os

def percorso_risorsa(percorso_relativo):
    """Restituisce il percorso corretto sia in sviluppo che nell'eseguibile."""
    if hasattr(sys, '_MEIPASS'):
        # Esecuzione da eseguibile PyInstaller
        base = sys._MEIPASS
    else:
        # Esecuzione in modalità sviluppo
        base = os.path.abspath(".")
    return os.path.join(base, percorso_relativo)

# Utilizzo
icona = percorso_risorsa("assets/immagini/icona.png")
config = percorso_risorsa("config.json")
```

### cx_Freeze

cx_Freeze è un'alternativa a PyInstaller, particolarmente solida su Windows. Utilizza un file di configurazione `setup.py` per definire le opzioni di build.

```python
# setup.py
import sys
from cx_Freeze import setup, Executable

build_options = {
    "packages": ["tkinter", "json", "os"],
    "excludes": ["unittest", "test"],
    "include_files": [
        ("assets/", "assets/"),
        "config.json",
    ],
}

# Opzioni specifiche per piattaforma
base = "Win32GUI" if sys.platform == "win32" else None

executables = [
    Executable(
        script="app.py",
        base=base,
        target_name="MiaApp",
        icon="icona.ico",
    )
]

setup(
    name="MiaApp",
    version="1.0.0",
    description="La mia applicazione GUI",
    options={"build_exe": build_options},
    executables=executables,
)
```

```bash
# Installazione
pip install cx_Freeze

# Build
python setup.py build

# Creazione installer MSI (solo Windows)
python setup.py bdist_msi
```

### Nuitka

Nuitka è un compilatore Python-to-C che trasforma il codice Python in codice C compilato, producendo eseguibili nativi con prestazioni significativamente migliori rispetto a PyInstaller e cx_Freeze.

```bash
pip install nuitka

# Compilazione base
python -m nuitka --standalone app.py

# Compilazione in un singolo file
python -m nuitka --onefile app.py

# Con ottimizzazioni per GUI (senza console su Windows)
python -m nuitka --onefile --disable-console --enable-plugin=tk-inter app.py

# Per PyQt6
python -m nuitka --onefile --disable-console --enable-plugin=pyqt6 app.py

# Specificare icona e nome
python -m nuitka --onefile \
    --disable-console \
    --enable-plugin=tk-inter \
    --windows-icon-from-ico=icona.ico \
    --output-filename=MiaApp \
    --include-data-dir=assets=assets \
    app.py
```

I vantaggi di Nuitka rispetto ad altre soluzioni includono prestazioni di avvio notevolmente migliori (il codice viene compilato in C nativo), una migliore protezione del codice sorgente (non è un semplice bundling ma una vera compilazione), dimensioni dell'eseguibile generalmente inferiori, e la compatibilità con la quasi totalità delle librerie Python. Lo svantaggio principale è il tempo di compilazione significativamente più lungo rispetto a PyInstaller.

---

## Best Practices

Le seguenti best practice rappresentano linee guida fondamentali per sviluppare applicazioni GUI Python di qualità professionale.

**1. Non bloccare mai il thread principale dell'interfaccia.** Ogni operazione che richiede più di qualche millisecondo (richieste di rete, accesso a database, elaborazione file, calcoli intensivi) deve essere eseguita in un thread separato o tramite meccanismi asincroni. Un'interfaccia bloccata (frozen) è la principale fonte di frustrazione per l'utente e di percezione di scarsa qualità dell'applicazione.

**2. Adottare il pattern MVC o una variante simile.** La separazione tra modello dei dati, logica di presentazione e gestione degli eventi è essenziale per la manutenibilità del codice. Il Model gestisce i dati e la business logic, la View definisce l'interfaccia grafica, e il Controller orchestra la comunicazione. Anche per piccole applicazioni, questa disciplina previene la crescita incontrollata della complessità.

**3. Progettare interfacce reattive e ridimensionabili.** L'interfaccia deve adattarsi correttamente a diverse dimensioni della finestra e risoluzioni dello schermo. Utilizzare layout manager (grid, box layout) anziché posizionamento assoluto, configurare correttamente i pesi delle righe e colonne, e testare l'applicazione con diverse dimensioni di finestra e fattori di scala DPI.

**4. Validare sempre l'input dell'utente.** Ogni dato inserito dall'utente deve essere validato prima dell'elaborazione. Fornire feedback immediato e chiaro in caso di errori (bordi rossi, messaggi contestuali), utilizzare i tipi di widget appropriati per il tipo di dato atteso (SpinBox per numeri, ComboBox per selezioni predefinite), e non fare mai affidamento sulla sola validazione lato interfaccia se i dati vengono persistiti.

**5. Gestire correttamente le eccezioni nell'interfaccia grafica.** Un'eccezione non catturata in un handler di eventi può causare comportamenti imprevedibili o crash silenziosi. Avvolgere ogni handler in un blocco try-except che mostri all'utente un messaggio di errore comprensibile, registri i dettagli tecnici in un file di log, e mantenga l'applicazione in uno stato consistente.

**6. Implementare la chiusura pulita dell'applicazione.** Intercettare l'evento di chiusura della finestra per salvare lo stato dell'applicazione, chiudere connessioni a database, terminare thread in esecuzione e chiedere conferma se ci sono dati non salvati. In tkinter si usa `protocol("WM_DELETE_WINDOW", callback)`, in PyQt6 si sovrascrive il metodo `closeEvent()`.

**7. Utilizzare costanti e file di configurazione per l'aspetto grafico.** Evitare di sparpagliere colori, font e dimensioni direttamente nel codice dei widget. Centralizzare queste definizioni in un modulo o dizionario di configurazione del tema, oppure utilizzare i meccanismi di stile del framework (stylesheet in Qt, Style in ttk). Questo facilita enormemente le modifiche all'aspetto e l'implementazione di temi multipli.

**8. Scrivere codice testabile separando la logica dalla GUI.** La logica di business non deve dipendere dal framework GUI. Estrarre la logica in classi e funzioni indipendenti che possano essere testate con unit test standard. Solo il sottile strato di collegamento tra logica e interfaccia dovrebbe dipendere dal toolkit grafico. Questo approccio migliora la qualità del codice e permette di cambiare framework GUI con impatto minimo.

**9. Considerare l'accessibilità fin dall'inizio della progettazione.** Assicurarsi che l'applicazione sia utilizzabile tramite tastiera (tab order corretto, shortcut), che i widget abbiano tooltip descrittivi, che i contrasti cromatici siano sufficienti, e che le dimensioni dei testi siano adeguate. Qt offre un supporto nativo per le tecnologie assistive del sistema operativo; per tkinter, è necessaria un'attenzione manuale maggiore.

**10. Ottimizzare le prestazioni di rendering.** Per applicazioni con molti widget o aggiornamenti frequenti, ridurre al minimo le operazioni di ridisegno raggruppando gli aggiornamenti (ad esempio con `update_idletasks()` in tkinter o `blockSignals()` in Qt), utilizzare il virtual scrolling per liste lunghe, e caricare dati in modo incrementale (lazy loading) anziché popolare l'intera interfaccia all'avvio. Per tabelle con migliaia di righe, preferire i model-based widget (`QTableView` con `QAbstractTableModel` in Qt) rispetto ai widget a popolamento diretto.

---

> **Nota:** Tutti gli esempi di codice presentati in questa guida sono compatibili con Python 3.10 e versioni successive. Per le librerie esterne (PyQt6, CustomTkinter, Flet, Dear PyGui), fare riferimento alla documentazione ufficiale di ciascun progetto per le versioni specifiche supportate e le eventuali dipendenze di sistema.

---

## PySide6 Deep Dive — Widget, Layout, QML

Questa sezione approfondisce le funzionalità avanzate di PySide6 e PyQt6, coprendo l'architettura Model-View, l'integrazione con QML, il multithreading avanzato e la creazione di interfacce professionali.

### Architettura Model-View in Qt

L'architettura Model-View di Qt separa la gestione dei dati dalla loro presentazione, consentendo di collegare lo stesso modello a viste diverse (tabella, lista, albero) senza duplicare la logica di accesso ai dati. I tre componenti fondamentali sono il **Model** (gestisce i dati e fornisce un'interfaccia standard), la **View** (visualizza i dati e gestisce l'interazione utente) e il **Delegate** (controlla come ogni elemento viene disegnato e modificato).

#### QAbstractTableModel — Modello Personalizzato per Tabelle

A differenza di `QTableWidget` (che gestisce internamente i dati), `QTableView` con un modello personalizzato offre prestazioni superiori con grandi dataset, perché i dati non vengono duplicati nei widget e la vista richiede solo le righe visibili.

```python
import sys
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableView,
    QVBoxLayout, QWidget, QHeaderView, QLineEdit)
from PyQt6.QtGui import QColor

class ProdottoModel(QAbstractTableModel):
    """Modello personalizzato per una tabella prodotti."""

    COLONNE = ["Nome", "Categoria", "Prezzo", "Quantità"]

    def __init__(self, dati=None):
        super().__init__()
        self._dati = dati or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._dati)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLONNE)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        riga = self._dati[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            valore = riga[col]
            if col == 2:  # Prezzo: formattazione valuta
                return f"€ {valore:,.2f}"
            return str(valore)

        if role == Qt.ItemDataRole.BackgroundRole:
            if col == 3 and riga[3] < 10:  # Quantità bassa: sfondo rosso
                return QColor(255, 200, 200)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (2, 3):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.COLONNE[section]
            return str(section + 1)
        return None

    def flags(self, index):
        return (Qt.ItemFlag.ItemIsEnabled |
                Qt.ItemFlag.ItemIsSelectable |
                Qt.ItemFlag.ItemIsEditable)

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole and index.isValid():
            riga = list(self._dati[index.row()])
            col = index.column()
            try:
                if col in (2, 3):
                    riga[col] = float(value) if col == 2 else int(value)
                else:
                    riga[col] = value
                self._dati[index.row()] = tuple(riga)
                self.dataChanged.emit(index, index, [role])
                return True
            except (ValueError, TypeError):
                return False
        return False

    def aggiungi_prodotto(self, nome, categoria, prezzo, quantita):
        posizione = len(self._dati)
        self.beginInsertRows(QModelIndex(), posizione, posizione)
        self._dati.append((nome, categoria, prezzo, quantita))
        self.endInsertRows()

    def rimuovi_prodotto(self, riga):
        self.beginRemoveRows(QModelIndex(), riga, riga)
        del self._dati[riga]
        self.endRemoveRows()


# Utilizzo
dati_esempio = [
    ("Laptop Pro", "Elettronica", 1299.99, 15),
    ("Mouse Wireless", "Accessori", 29.99, 5),
    ("Tastiera Meccanica", "Accessori", 89.50, 23),
    ("Monitor 27\"", "Elettronica", 449.00, 8),
    ("Cavo USB-C", "Cavi", 12.99, 3),
]

app = QApplication(sys.argv)
modello = ProdottoModel(dati_esempio)
vista = QTableView()
vista.setModel(modello)
vista.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
vista.setAlternatingRowColors(True)
vista.setWindowTitle("Inventario Prodotti")
vista.resize(700, 400)
vista.show()
sys.exit(app.exec())
```

#### QSortFilterProxyModel — Filtro e Ordinamento

`QSortFilterProxyModel` si interpone tra il modello originale e la vista, offrendo ordinamento e filtraggio senza modificare i dati sorgente. Questo è fondamentale per implementare barre di ricerca e filtri su tabelle di grandi dimensioni.

```python
from PyQt6.QtCore import QSortFilterProxyModel, QRegularExpression

class FiltroProxy(QSortFilterProxyModel):
    """Proxy che filtra per nome prodotto e categoria."""

    def __init__(self):
        super().__init__()
        self._categoria_filtro = ""

    def set_categoria(self, categoria):
        self._categoria_filtro = categoria
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        modello = self.sourceModel()
        # Filtro testo (colonna 0 = Nome)
        indice_nome = modello.index(source_row, 0, source_parent)
        nome = modello.data(indice_nome, Qt.ItemDataRole.DisplayRole) or ""

        # Filtro categoria (colonna 1)
        if self._categoria_filtro:
            indice_cat = modello.index(source_row, 1, source_parent)
            cat = modello.data(indice_cat, Qt.ItemDataRole.DisplayRole) or ""
            if cat != self._categoria_filtro:
                return False

        # Filtro testo libero
        regex = self.filterRegularExpression()
        if regex.pattern():
            return bool(QRegularExpression(regex).match(nome).hasMatch())

        return True

# Collegamento alla vista
proxy = FiltroProxy()
proxy.setSourceModel(modello)
proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
vista.setModel(proxy)
vista.setSortingEnabled(True)
```

### Integrazione con QML

QML (Qt Modeling Language) è un linguaggio dichiarativo che permette di definire interfacce grafiche in modo visivo e reattivo. L'integrazione con Python avviene esponendo oggetti Python al contesto QML tramite proprietà e segnali.

#### Struttura di un Progetto QML + Python

```
progetto/
├── main.py
├── qml/
│   └── main.qml
└── modelli/
    └── backend.py
```

```python
# main.py
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot, Signal, Property

class Backend(QObject):
    """Logica Python esposta a QML."""

    contatore_cambiato = Signal(int)

    def __init__(self):
        super().__init__()
        self._contatore = 0

    @Property(int, notify=contatore_cambiato)
    def contatore(self):
        return self._contatore

    @contatore.setter
    def contatore(self, valore):
        if self._contatore != valore:
            self._contatore = valore
            self.contatore_cambiato.emit(valore)

    @Slot()
    def incrementa(self):
        self.contatore = self._contatore + 1

    @Slot()
    def decrementa(self):
        self.contatore = self._contatore - 1

    @Slot(str, result=str)
    def processa_testo(self, testo):
        return testo.upper().strip()


app = QApplication(sys.argv)
engine = QQmlApplicationEngine()

backend = Backend()
engine.rootContext().setContextProperty("backend", backend)

qml_file = Path(__file__).parent / "qml" / "main.qml"
engine.load(qml_file)

if not engine.rootObjects():
    sys.exit(-1)

sys.exit(app.exec())
```

```qml
// qml/main.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    width: 400
    height: 300
    title: "QML + Python"

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 15

        Text {
            text: "Contatore: " + backend.contatore
            font.pixelSize: 28
            Layout.alignment: Qt.AlignHCenter
        }

        RowLayout {
            spacing: 10
            Layout.alignment: Qt.AlignHCenter

            Button {
                text: "-"
                onClicked: backend.decrementa()
                implicitWidth: 60
            }
            Button {
                text: "+"
                onClicked: backend.incrementa()
                implicitWidth: 60
            }
        }

        TextField {
            id: campoTesto
            placeholderText: "Scrivi qualcosa..."
            Layout.preferredWidth: 250
        }

        Button {
            text: "Processa"
            onClicked: risultato.text = backend.processa_testo(campoTesto.text)
            Layout.alignment: Qt.AlignHCenter
        }

        Text {
            id: risultato
            font.pixelSize: 16
            color: "#2980b9"
            Layout.alignment: Qt.AlignHCenter
        }
    }
}
```

#### QAbstractListModel per QML

Per esporre liste di dati da Python a QML, si sottoclassa `QAbstractListModel` definendo ruoli personalizzati che QML può interrogare tramite delegate.

```python
from PySide6.QtCore import (QAbstractListModel, Qt, QModelIndex,
                             Slot, Signal, Property, QByteArray)

class TaskModel(QAbstractListModel):
    """Modello di task per QML ListView."""

    NomeRole = Qt.ItemDataRole.UserRole + 1
    CompletatoRole = Qt.ItemDataRole.UserRole + 2
    PrioritaRole = Qt.ItemDataRole.UserRole + 3

    conteggio_cambiato = Signal()

    def __init__(self):
        super().__init__()
        self._tasks = [
            {"nome": "Comprare il latte", "completato": False, "priorita": 1},
            {"nome": "Scrivere il report", "completato": False, "priorita": 3},
            {"nome": "Fare esercizio", "completato": True, "priorita": 2},
        ]

    def rowCount(self, parent=QModelIndex()):
        return len(self._tasks)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._tasks):
            return None
        task = self._tasks[index.row()]
        if role == self.NomeRole:
            return task["nome"]
        if role == self.CompletatoRole:
            return task["completato"]
        if role == self.PrioritaRole:
            return task["priorita"]
        return None

    def roleNames(self):
        return {
            self.NomeRole: QByteArray(b"nome"),
            self.CompletatoRole: QByteArray(b"completato"),
            self.PrioritaRole: QByteArray(b"priorita"),
        }

    @Slot(str, int)
    def aggiungi(self, nome, priorita):
        self.beginInsertRows(QModelIndex(), len(self._tasks), len(self._tasks))
        self._tasks.append({"nome": nome, "completato": False,
                            "priorita": priorita})
        self.endInsertRows()
        self.conteggio_cambiato.emit()

    @Slot(int)
    def toggle_completato(self, riga):
        if 0 <= riga < len(self._tasks):
            self._tasks[riga]["completato"] = not self._tasks[riga]["completato"]
            indice = self.index(riga)
            self.dataChanged.emit(indice, indice, [self.CompletatoRole])

    @Slot(int)
    def rimuovi(self, riga):
        if 0 <= riga < len(self._tasks):
            self.beginRemoveRows(QModelIndex(), riga, riga)
            del self._tasks[riga]
            self.endRemoveRows()
            self.conteggio_cambiato.emit()

    @Property(int, notify=conteggio_cambiato)
    def conteggio(self):
        return len(self._tasks)
```

### Multithreading Avanzato con QThread

Il pattern `moveToThread` è il modo consigliato per gestire operazioni in background in Qt. A differenza del sottoclassamento di `QThread`, questo approccio separa la logica del worker dal meccanismo di threading.

#### Pattern Worker con Annullamento e Progresso Granulare

```python
from PyQt6.QtCore import QThread, QObject, pyqtSignal, QMutex, QWaitCondition
import time

class WorkerAvanzato(QObject):
    """Worker con supporto per annullamento, pausa e progresso."""

    progresso = pyqtSignal(int, str)  # (percentuale, messaggio)
    completato = pyqtSignal(object)    # risultato
    errore = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._annullato = False
        self._in_pausa = False
        self._mutex = QMutex()
        self._wait = QWaitCondition()

    def annulla(self):
        self._mutex.lock()
        self._annullato = True
        self._in_pausa = False
        self._wait.wakeAll()
        self._mutex.unlock()

    def pausa(self):
        self._mutex.lock()
        self._in_pausa = True
        self._mutex.unlock()

    def riprendi(self):
        self._mutex.lock()
        self._in_pausa = False
        self._wait.wakeAll()
        self._mutex.unlock()

    def esegui(self):
        try:
            risultati = []
            totale = 100
            for i in range(totale):
                # Controllo pausa
                self._mutex.lock()
                while self._in_pausa and not self._annullato:
                    self._wait.wait(self._mutex)
                if self._annullato:
                    self._mutex.unlock()
                    self.progresso.emit(i, "Annullato")
                    return
                self._mutex.unlock()

                # Simulazione lavoro
                time.sleep(0.05)
                risultati.append(i * 2)
                self.progresso.emit(
                    int((i + 1) / totale * 100),
                    f"Elaborazione elemento {i + 1}/{totale}"
                )

            self.completato.emit(risultati)
        except Exception as e:
            self.errore.emit(str(e))


class GestoreThread:
    """Gestisce il ciclo di vita del worker e del thread."""

    def __init__(self, callback_progresso, callback_fine, callback_errore):
        self.thread = QThread()
        self.worker = WorkerAvanzato()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.esegui)
        self.worker.progresso.connect(callback_progresso)
        self.worker.completato.connect(callback_fine)
        self.worker.completato.connect(self.thread.quit)
        self.worker.errore.connect(callback_errore)
        self.worker.errore.connect(self.thread.quit)

    def avvia(self):
        self.thread.start()

    def annulla(self):
        self.worker.annulla()

    def pausa(self):
        self.worker.pausa()

    def riprendi(self):
        self.worker.riprendi()
```

#### QThreadPool e QRunnable — Pool di Thread

Per operazioni concorrenti multiple, `QThreadPool` con `QRunnable` offre un pool gestito che riutilizza i thread ed evita il costo della creazione continua di nuovi thread.

```python
from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject

class SegnaliWorker(QObject):
    """Segnali separati perché QRunnable non supporta pyqtSignal."""
    completato = pyqtSignal(int, object)
    errore = pyqtSignal(int, str)

class TaskParallelo(QRunnable):
    def __init__(self, task_id, funzione, *args):
        super().__init__()
        self.task_id = task_id
        self.funzione = funzione
        self.args = args
        self.segnali = SegnaliWorker()
        self.setAutoDelete(True)

    def run(self):
        try:
            risultato = self.funzione(*self.args)
            self.segnali.completato.emit(self.task_id, risultato)
        except Exception as e:
            self.segnali.errore.emit(self.task_id, str(e))

# Utilizzo del pool
pool = QThreadPool.globalInstance()
pool.setMaxThreadCount(4)

def elabora(dati):
    import time
    time.sleep(1)
    return sum(dati)

for i in range(10):
    task = TaskParallelo(i, elabora, list(range(i * 100, (i + 1) * 100)))
    task.segnali.completato.connect(
        lambda tid, res: print(f"Task {tid} completato: {res}"))
    pool.start(task)
```

---

## Tkinter Patterns Avanzati

### ttk.Treeview Avanzato — Alberi Gerarchici con Ordinamento

Il widget `Treeview` di ttk supporta la visualizzazione sia tabulare che gerarchica. In questa sezione esploriamo funzionalità avanzate come l'ordinamento per colonna, la ricerca inline e lo stile personalizzato.

```python
import tkinter as tk
from tkinter import ttk

class TreeviewAvanzato(ttk.Frame):
    """Treeview con ordinamento cliccando sulle intestazioni,
    ricerca inline e stile personalizzato."""

    def __init__(self, parent):
        super().__init__(parent)
        self.pack(expand=True, fill="both", padx=10, pady=10)
        self._crea_barra_ricerca()
        self._crea_treeview()
        self._popola_dati()

    def _crea_barra_ricerca(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", pady=(0, 5))
        ttk.Label(frame, text="Filtra:").pack(side="left")
        self.filtro_var = tk.StringVar()
        self.filtro_var.trace_add("write", self._filtra)
        ttk.Entry(frame, textvariable=self.filtro_var, width=30).pack(
            side="left", padx=5)

    def _crea_treeview(self):
        colonne = ("nome", "tipo", "dimensione", "data")
        self.tree = ttk.Treeview(self, columns=colonne, show="tree headings",
                                  height=15)

        # Configurazione colonne con ordinamento
        self.tree.heading("#0", text="Struttura", anchor="w")
        for col, testo, larghezza in [
            ("nome", "Nome", 200), ("tipo", "Tipo", 100),
            ("dimensione", "Dimensione", 100), ("data", "Data", 120)
        ]:
            self.tree.heading(col, text=testo,
                              command=lambda c=col: self._ordina(c, False))
            self.tree.column(col, width=larghezza)

        # Scrollbar verticale e orizzontale
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Tag per colorare le righe
        self.tree.tag_configure("cartella", background="#e8f4fd")
        self.tree.tag_configure("python", foreground="#2ecc71")
        self.tree.tag_configure("critico", foreground="#e74c3c", font=("", 10, "bold"))

    def _ordina(self, colonna, inverti):
        """Ordina il Treeview cliccando sull'intestazione della colonna."""
        dati = [(self.tree.set(child, colonna), child)
                for child in self.tree.get_children("")]
        dati.sort(reverse=inverti, key=lambda t: t[0].lower())
        for indice, (_, child) in enumerate(dati):
            self.tree.move(child, "", indice)
        self.tree.heading(colonna,
                          command=lambda: self._ordina(colonna, not inverti))

    def _filtra(self, *args):
        """Filtra le righe mostrando solo quelle che corrispondono."""
        termine = self.filtro_var.get().lower()
        for item in self.tree.get_children(""):
            valori = " ".join(str(v) for v in self.tree.item(item)["values"])
            testo = self.tree.item(item)["text"]
            visibile = termine in valori.lower() or termine in testo.lower()
            if visibile:
                self.tree.reattach(item, "", "end")
            else:
                self.tree.detach(item)

    def _popola_dati(self):
        progetto = self.tree.insert("", "end", text="Progetto",
                                     values=("progetto", "Cartella", "4.2 MB",
                                             "2025-01-15"),
                                     tags=("cartella",))
        src = self.tree.insert(progetto, "end", text="src",
                                values=("src", "Cartella", "2.1 MB",
                                        "2025-01-14"),
                                tags=("cartella",))
        self.tree.insert(src, "end", text="main.py",
                          values=("main.py", "Python", "15 KB", "2025-01-14"),
                          tags=("python",))
        self.tree.insert(src, "end", text="config.py",
                          values=("config.py", "Python", "3 KB", "2025-01-10"),
                          tags=("python",))
        self.tree.item(progetto, open=True)
        self.tree.item(src, open=True)


root = tk.Tk()
root.title("Treeview Avanzato")
root.geometry("700x500")
app = TreeviewAvanzato(root)
root.mainloop()
```

### Canvas — Animazioni e Drag-and-Drop

Il widget Canvas di tkinter supporta animazioni fluide tramite il metodo `after()` e il drag-and-drop di oggetti tramite binding di eventi mouse.

#### Animazione con Canvas

```python
import tkinter as tk
import math

class CanvasAnimazione(tk.Canvas):
    """Canvas con animazione di particelle e forme in movimento."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="black", highlightthickness=0, **kwargs)
        self.pack(expand=True, fill="both")
        self._particelle = []
        self._angolo = 0
        self._crea_particelle(30)
        self._anima()

    def _crea_particelle(self, n):
        for i in range(n):
            x = 300 + math.cos(i * 0.5) * 100
            y = 250 + math.sin(i * 0.5) * 100
            r = 3 + (i % 5)
            colore = f"#{(i*37)%256:02x}{(i*73)%256:02x}{(i*113)%256:02x}"
            obj = self.create_oval(x-r, y-r, x+r, y+r, fill=colore, outline="")
            self._particelle.append({
                "id": obj, "angolo": i * (360/n),
                "raggio_orbita": 50 + i * 4, "velocita": 0.5 + i * 0.1,
                "dim": r
            })

    def _anima(self):
        cx, cy = self.winfo_width() / 2 or 300, self.winfo_height() / 2 or 250
        self._angolo += 1

        for p in self._particelle:
            angolo_rad = math.radians(p["angolo"] + self._angolo * p["velocita"])
            x = cx + math.cos(angolo_rad) * p["raggio_orbita"]
            y = cy + math.sin(angolo_rad) * p["raggio_orbita"]
            r = p["dim"]
            self.coords(p["id"], x-r, y-r, x+r, y+r)

        self.after(16, self._anima)  # ~60 FPS


root = tk.Tk()
root.title("Animazione Canvas")
root.geometry("600x500")
canvas = CanvasAnimazione(root, width=600, height=500)
root.mainloop()
```

#### Drag-and-Drop su Canvas

```python
import tkinter as tk

class CanvasDragDrop(tk.Canvas):
    """Canvas con drag-and-drop di oggetti geometrici."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#f5f5f5", highlightthickness=0, **kwargs)
        self.pack(expand=True, fill="both")
        self._drag_data = {"oggetto": None, "x": 0, "y": 0}
        self._crea_oggetti()
        self._bind_eventi()

    def _crea_oggetti(self):
        self.create_rectangle(50, 50, 150, 120, fill="#3498db",
                               outline="#2c3e50", width=2, tags="draggable")
        self.create_oval(200, 50, 320, 150, fill="#e74c3c",
                          outline="#c0392b", width=2, tags="draggable")
        self.create_polygon(400, 50, 500, 50, 450, 140,
                             fill="#2ecc71", outline="#27ae60", width=2,
                             tags="draggable")

        # Zone di destinazione
        self.create_rectangle(100, 300, 300, 420, fill="",
                               outline="#95a5a6", width=2, dash=(5, 3),
                               tags="zona_dest")
        self.create_text(200, 360, text="Trascina qui",
                          fill="#95a5a6", font=("Helvetica", 12))

    def _bind_eventi(self):
        self.tag_bind("draggable", "<Button-1>", self._inizio_drag)
        self.tag_bind("draggable", "<B1-Motion>", self._durante_drag)
        self.tag_bind("draggable", "<ButtonRelease-1>", self._fine_drag)

    def _inizio_drag(self, event):
        oggetto = self.find_closest(event.x, event.y)[0]
        self._drag_data["oggetto"] = oggetto
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.tag_raise(oggetto)  # Porta in primo piano

    def _durante_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self.move(self._drag_data["oggetto"], dx, dy)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _fine_drag(self, event):
        oggetto = self._drag_data["oggetto"]
        bbox = self.bbox(oggetto)
        if bbox:
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2
            # Verifica se è nella zona di destinazione
            sovrapposizioni = self.find_overlapping(100, 300, 300, 420)
            if oggetto in sovrapposizioni:
                self.itemconfig(oggetto, outline="#f39c12", width=3)
            else:
                self.itemconfig(oggetto, width=2)
        self._drag_data["oggetto"] = None


root = tk.Tk()
root.title("Drag and Drop — Canvas")
root.geometry("600x500")
canvas = CanvasDragDrop(root, width=600, height=500)
root.mainloop()
```

### Stili ttk Personalizzati — Temi Avanzati

Il sistema di stili di ttk è potente ma richiede una comprensione del meccanismo a layer (layout + elementi). Ogni widget ttk è composto da elementi visivi (bordo, sfondo, testo, freccia) che possono essere personalizzati individualmente.

```python
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Stili ttk Avanzati")

stile = ttk.Style()
stile.theme_use("clam")

# Stile pulsante personalizzato con bordo arrotondato simulato
stile.configure("Rounded.TButton",
                foreground="white",
                background="#6c5ce7",
                font=("Segoe UI", 11),
                padding=(20, 10),
                borderwidth=0,
                relief="flat")
stile.map("Rounded.TButton",
          background=[("active", "#5f3dc4"),
                      ("pressed", "#4c2a8a"),
                      ("disabled", "#b2bec3")],
          foreground=[("disabled", "#636e72")])

# Stile Treeview personalizzato
stile.configure("Custom.Treeview",
                background="#fafafa",
                foreground="#2d3436",
                fieldbackground="#fafafa",
                rowheight=30,
                font=("Segoe UI", 10))
stile.configure("Custom.Treeview.Heading",
                background="#2d3436",
                foreground="white",
                font=("Segoe UI", 10, "bold"),
                padding=8)
stile.map("Custom.Treeview",
          background=[("selected", "#74b9ff")],
          foreground=[("selected", "#2d3436")])

# Stile Entry con focus evidenziato
stile.configure("Custom.TEntry",
                fieldbackground="white",
                borderwidth=2,
                relief="solid",
                padding=8)
stile.map("Custom.TEntry",
          bordercolor=[("focus", "#0984e3"),
                       ("!focus", "#b2bec3")],
          lightcolor=[("focus", "#74b9ff")])

# Dimostrazione
ttk.Button(root, text="Pulsante Moderno",
           style="Rounded.TButton").pack(pady=10)
ttk.Entry(root, style="Custom.TEntry", width=35).pack(pady=10)

tree = ttk.Treeview(root, columns=("a", "b"), show="headings",
                     style="Custom.Treeview", height=5)
tree.heading("a", text="Colonna A")
tree.heading("b", text="Colonna B")
for i in range(5):
    tree.insert("", "end", values=(f"Valore {i}", f"Dato {i}"))
tree.pack(pady=10, padx=10)

root.mainloop()
```

---

## Event Loop e Threading nelle GUI

### Anatomia dell'Event Loop

Il cuore di ogni applicazione GUI è l'event loop (ciclo degli eventi), un ciclo infinito che attende eventi dal sistema operativo (click del mouse, pressione di tasti, ridimensionamento della finestra, timer scaduti) e li despaccia agli handler registrati. La comprensione di questo meccanismo è fondamentale per scrivere applicazioni responsive e corrette.

#### Event Loop in tkinter

In tkinter, il `mainloop()` chiama ripetutamente `update()` (che processa tutti gli eventi pendenti) e `update_idletasks()` (che esegue i callback registrati con `after_idle()`). Il metodo `after(ms, callback)` schedula un callback dopo un ritardo specificato in millisecondi, ed è il modo corretto per eseguire operazioni periodiche senza bloccare la UI.

```python
import tkinter as tk
import time

class EventLoopDemo(tk.Tk):
    """Dimostrazione del funzionamento dell'event loop tkinter."""

    def __init__(self):
        super().__init__()
        self.title("Event Loop Demo")
        self.geometry("400x300")

        self.label = tk.Label(self, text="", font=("Courier", 12))
        self.label.pack(pady=10)

        self.log = tk.Text(self, height=10, width=50, font=("Courier", 9))
        self.log.pack(pady=5)

        # after() schedula un callback nel loop principale
        self.after(0, self._log_msg, "Evento: after(0) — eseguito subito")
        self.after(1000, self._log_msg, "Evento: after(1000) — dopo 1s")
        self.after(2000, self._log_msg, "Evento: after(2000) — dopo 2s")

        # after_idle() esegue quando non ci sono altri eventi
        self.after_idle(self._log_msg, "Evento: after_idle — prima iterazione")

        # Timer periodico
        self._aggiorna_orologio()

    def _aggiorna_orologio(self):
        ora = time.strftime("%H:%M:%S")
        self.label.config(text=f"Ora: {ora}")
        self.after(1000, self._aggiorna_orologio)  # Ripeti ogni secondo

    def _log_msg(self, messaggio):
        timestamp = time.strftime("%H:%M:%S.") + f"{int(time.time()*1000)%1000:03d}"
        self.log.insert("end", f"[{timestamp}] {messaggio}\n")
        self.log.see("end")


app = EventLoopDemo()
app.mainloop()
```

#### Event Loop in Qt

In Qt l'event loop è gestito da `QApplication.exec()` che internamente chiama `QEventLoop.processEvents()`. Gli eventi vengono accodati in una coda (event queue) e processati in ordine FIFO, con possibilità di priorità. I timer (`QTimer`), i segnali cross-thread (`QMetaObject.invokeMethod`) e le invocazioni asincrone si basano tutti sull'event loop.

```python
from PyQt6.QtCore import QTimer, QElapsedTimer, Qt
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
import sys

class EventLoopQt(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt Event Loop")
        layout = QVBoxLayout(self)

        self.label_timer = QLabel("Timer: 0")
        layout.addWidget(self.label_timer)

        self.contatore = 0
        self.elapsed = QElapsedTimer()
        self.elapsed.start()

        # QTimer — timer ripetitivo
        self.timer = QTimer(self)
        self.timer.setInterval(100)  # ogni 100ms
        self.timer.timeout.connect(self._on_tick)
        self.timer.start()

        # QTimer singleShot — esecuzione una tantum
        QTimer.singleShot(3000, lambda: self.label_timer.setText(
            "3 secondi trascorsi!"))

    def _on_tick(self):
        self.contatore += 1
        ms = self.elapsed.elapsed()
        self.label_timer.setText(
            f"Tick #{self.contatore} — Tempo: {ms}ms")


app = QApplication(sys.argv)
win = EventLoopQt()
win.show()
sys.exit(app.exec())
```

### Comunicazione Thread-Safe con la UI

Un errore comune e pericoloso è aggiornare i widget dell'interfaccia da un thread secondario. Questo causa crash, corruzione di stato e comportamenti imprevedibili. Ogni toolkit GUI richiede che le modifiche all'interfaccia avvengano esclusivamente dal thread principale.

#### Pattern thread-safe in tkinter

```python
import tkinter as tk
import threading
import queue
import time

class ThreadSafeTkinter(tk.Tk):
    """Pattern producer-consumer per aggiornamenti thread-safe."""

    def __init__(self):
        super().__init__()
        self.title("Thread-Safe Updates")
        self._coda = queue.Queue()

        self.label = tk.Label(self, text="In attesa...", font=("Helvetica", 14))
        self.label.pack(pady=20)

        tk.Button(self, text="Avvia Worker",
                  command=self._avvia_worker).pack(pady=5)

        # Polling periodico della coda
        self._controlla_coda()

    def _controlla_coda(self):
        """Controlla la coda dal thread principale e processa i messaggi."""
        try:
            while True:
                messaggio = self._coda.get_nowait()
                self.label.config(text=messaggio)
        except queue.Empty:
            pass
        self.after(50, self._controlla_coda)  # Controlla ogni 50ms

    def _avvia_worker(self):
        def worker():
            for i in range(10):
                time.sleep(0.5)
                # NON toccare mai i widget da qui!
                # Usa la coda per comunicare col thread principale
                self._coda.put(f"Progresso: {(i+1)*10}%")
            self._coda.put("Completato!")

        threading.Thread(target=worker, daemon=True).start()


app = ThreadSafeTkinter()
app.mainloop()
```

#### Pattern thread-safe in Qt — Signals Cross-Thread

In Qt, i segnali collegati tra thread diversi vengono automaticamente accodati nell'event loop del thread destinatario (`Qt.ConnectionType.QueuedConnection`). Questo rende la comunicazione cross-thread naturale e sicura.

```python
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
import sys
import time

class WorkerCrossThread(QObject):
    """Worker che emette segnali dal suo thread; Qt li accoda
    automaticamente nel thread della UI."""

    aggiornamento = pyqtSignal(str)
    completato = pyqtSignal()

    def lavora(self):
        for i in range(20):
            time.sleep(0.3)
            # Questo segnale viene emesso dal thread worker
            # ma ricevuto nel thread principale (auto-queued)
            self.aggiornamento.emit(f"Step {i+1}/20 — Thread: {QThread.currentThread().objectName()}")
        self.completato.emit()


class AppCrossThread(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cross-Thread Signals")
        layout = QVBoxLayout(self)
        self.label = QLabel("Pronto")
        self.btn = QPushButton("Avvia")
        self.btn.clicked.connect(self._avvia)
        layout.addWidget(self.label)
        layout.addWidget(self.btn)

    def _avvia(self):
        self.btn.setEnabled(False)
        self.thread = QThread()
        self.thread.setObjectName("WorkerThread")
        self.worker = WorkerCrossThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.lavora)
        self.worker.aggiornamento.connect(self.label.setText)
        self.worker.completato.connect(self._on_fine)
        self.thread.start()

    def _on_fine(self):
        self.label.setText("Completato!")
        self.btn.setEnabled(True)
        self.thread.quit()
        self.thread.wait()


app = QApplication(sys.argv)
win = AppCrossThread()
win.show()
sys.exit(app.exec())
```

### asyncio e GUI — Integrazione con Event Loop Asincrono

L'integrazione tra `asyncio` e i toolkit GUI richiede attenzione perché entrambi necessitano del controllo del thread principale. In PySide6, il modulo `qasync` (o `asyncqt`) fornisce un event loop asyncio che si integra con l'event loop di Qt.

```python
# Richiede: pip install qasync
import sys
import asyncio
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from qasync import QEventLoop, asyncSlot

class AppAsync(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("asyncio + Qt")
        layout = QVBoxLayout(self)
        self.label = QLabel("Pronto")
        self.btn = QPushButton("Avvia operazione asincrona")
        self.btn.clicked.connect(self._avvia_async)
        layout.addWidget(self.label)
        layout.addWidget(self.btn)

    @asyncSlot()
    async def _avvia_async(self):
        self.btn.setEnabled(False)
        self.label.setText("Download in corso...")
        # Simula operazioni async (es. aiohttp, database async)
        for i in range(5):
            await asyncio.sleep(0.5)
            self.label.setText(f"Download: {(i+1)*20}%")
        self.label.setText("Download completato!")
        self.btn.setEnabled(True)


app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)
win = AppAsync()
win.show()
with loop:
    loop.run_forever()
```

---

## Packaging Avanzato — PyInstaller, Briefcase, Nuitka

### Briefcase (BeeWare) — Distribuzione Nativa Multi-Piattaforma

Briefcase è lo strumento di packaging del progetto BeeWare. A differenza di PyInstaller e Nuitka, Briefcase produce pacchetti veramente nativi per ogni piattaforma: `.app`/DMG su macOS, MSI su Windows, `.deb`/`.rpm`/AppImage/Flatpak su Linux, e genera progetti Xcode (iOS) e Gradle (Android) per la distribuzione mobile.

```bash
pip install briefcase

# Creare un nuovo progetto
briefcase new

# Creare l'applicazione per la piattaforma corrente
briefcase create

# Compilare
briefcase build

# Eseguire
briefcase run

# Packaging per la distribuzione
briefcase package

# Creare per una piattaforma specifica (esempio: Linux AppImage)
briefcase create linux appimage
briefcase build linux appimage
briefcase package linux appimage

# Creare per Android (richiede Android SDK)
briefcase create android
briefcase build android
briefcase run android
```

#### Configurazione pyproject.toml per Briefcase

```toml
[tool.briefcase]
project_name = "Gestione Contatti"
bundle = "com.example"
version = "1.0.0"
url = "https://example.com/gestione-contatti"
license.file = "LICENSE"
author = "Nome Autore"
author_email = "autore@example.com"

[tool.briefcase.app.gestionecontatti]
formal_name = "Gestione Contatti"
description = "Applicazione per la gestione dei contatti"
sources = ["gestionecontatti"]
requires = ["PySide6>=6.7"]
icon = "gestionecontatti/resources/icona"

[tool.briefcase.app.gestionecontatti.macOS]
requires = []

[tool.briefcase.app.gestionecontatti.linux]
requires = []
system_requires = []

[tool.briefcase.app.gestionecontatti.windows]
requires = []

[tool.briefcase.app.gestionecontatti.iOS]
requires = []

[tool.briefcase.app.gestionecontatti.android]
requires = []
```

### Confronto tra Strumenti di Packaging

| Caratteristica | PyInstaller | Nuitka | cx_Freeze | Briefcase |
|---|---|---|---|---|
| **Tipo** | Bundler | Compilatore C | Bundler | Packaging nativo |
| **Velocità avvio** | Media | Veloce | Media | Veloce |
| **Dimensione output** | Grande | Ridotta | Grande | Media |
| **Mobile (iOS/Android)** | No | No | No | Sì |
| **Protezione sorgente** | Bassa | Alta | Bassa | Media |
| **Tempo di build** | Veloce | Lento | Veloce | Medio |
| **Licenza** | GPL | Apache 2.0 | PSF | BSD |
| **Installatore nativo** | No (serve NSIS) | No | MSI (Win) | Sì (nativo) |

### Strategie per Ridurre le Dimensioni dell'Eseguibile

Indipendentemente dallo strumento scelto, le dimensioni dell'eseguibile possono essere ridotte significativamente con le seguenti strategie.

Primo, utilizzare un ambiente virtuale dedicato con sole le dipendenze necessarie. Secondo, escludere esplicitamente i moduli non utilizzati (`--exclude-module` in PyInstaller, `--nofollow-import-to` in Nuitka). Terzo, applicare la compressione UPX (compatibile con PyInstaller). Quarto, per applicazioni tkinter, evitare di includere l'intero modulo `test` e `unittest` della libreria standard. Quinto, con Nuitka, usare `--lto=yes` per link-time optimization che riduce ulteriormente il binario. Sesto, valutare l'uso di `--onefile` vs `--standalone`: il primo produce un file singolo ma l'avvio è più lento perché decomprime al volo; il secondo produce una cartella ma si avvia più rapidamente.

---

## Accessibilità nelle Applicazioni GUI

L'accessibilità (a11y) nelle applicazioni desktop garantisce che persone con disabilità visive, motorie o cognitive possano utilizzare il software tramite tecnologie assistive (screen reader, tastiera, switch, ingranditori). Progettare applicazioni accessibili non è un optional ma un requisito etico e, in molti contesti, legale.

### Principi Fondamentali di Accessibilità per GUI Desktop

**Navigazione da tastiera completa.** Ogni widget interattivo deve essere raggiungibile e utilizzabile esclusivamente tramite tastiera. Il tab order deve seguire la logica visiva del layout, e le scorciatoie da tastiera devono essere documentate e coerenti.

**Etichette e nomi accessibili.** Ogni widget interattivo deve avere un nome accessibile che lo screen reader possa leggere. In Qt questo si imposta con `setAccessibleName()` e `setAccessibleDescription()`. In tkinter, i tooltip e le label associate ai widget forniscono contesto.

**Contrasto cromatico.** Il rapporto di contrasto tra testo e sfondo deve rispettare almeno il livello AA di WCAG 2.1 (4.5:1 per testo normale, 3:1 per testo grande). Non affidarsi mai al solo colore per trasmettere informazioni; usare anche forme, icone o testo.

**Rispetto delle preferenze di sistema.** Rispettare le impostazioni di accessibilità del sistema operativo: dimensione del font, tema ad alto contrasto, riduzione delle animazioni, modalità scura.

### Accessibilità in Qt (PyQt6/PySide6)

Qt fornisce il supporto più maturo per l'accessibilità tra i toolkit GUI Python. Tramite il modulo `QAccessible`, i widget espongono automaticamente ruolo, stato, nome e descrizione alle tecnologie assistive del sistema operativo (MSAA/UIA su Windows, AT-SPI su Linux, Accessibility API su macOS).

```python
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QGroupBox)
from PyQt6.QtCore import Qt
import sys

class FormAccessibile(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Form Accessibile")
        layout = QVBoxLayout(self)

        gruppo = QGroupBox("Dati Personali")
        gruppo.setAccessibleName("Sezione dati personali")
        group_layout = QVBoxLayout(gruppo)

        # Label + Entry con associazione esplicita
        lbl_nome = QLabel("&Nome:")  # '&' crea un mnemonico Alt+N
        self.entry_nome = QLineEdit()
        self.entry_nome.setAccessibleName("Campo nome completo")
        self.entry_nome.setAccessibleDescription(
            "Inserisci il tuo nome e cognome")
        self.entry_nome.setPlaceholderText("Es. Mario Rossi")
        lbl_nome.setBuddy(self.entry_nome)  # Collega label al widget

        lbl_email = QLabel("&Email:")
        self.entry_email = QLineEdit()
        self.entry_email.setAccessibleName("Campo indirizzo email")
        lbl_email.setBuddy(self.entry_email)

        group_layout.addWidget(lbl_nome)
        group_layout.addWidget(self.entry_nome)
        group_layout.addWidget(lbl_email)
        group_layout.addWidget(self.entry_email)
        layout.addWidget(gruppo)

        btn = QPushButton("&Invia")
        btn.setAccessibleName("Pulsante invio modulo")
        btn.setAccessibleDescription("Invia i dati del modulo")
        btn.setToolTip("Invia il modulo (Alt+I)")
        # Shortcut esplicita oltre al mnemonico
        btn.setShortcut("Ctrl+Return")
        layout.addWidget(btn)

        # Focus iniziale sul primo campo
        self.entry_nome.setFocus()

        # Tab order esplicito
        self.setTabOrder(self.entry_nome, self.entry_email)
        self.setTabOrder(self.entry_email, btn)


app = QApplication(sys.argv)
win = FormAccessibile()
win.show()
sys.exit(app.exec())
```

### Accessibilità in tkinter

tkinter ha un supporto limitato per l'accessibilità. Su Linux, il progetto **Tka11y** (Tk Accessibility) espone i widget tkinter tramite AT-SPI, rendendoli visibili agli screen reader come Orca. Su Windows e macOS il supporto nativo è più limitato, ma alcune buone pratiche migliorano comunque l'esperienza.

```python
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Form Accessibile — tkinter")

# Tab order predefinito segue l'ordine di creazione
# ma si può forzare con lift() e focus_set()

# Mnemonici simulati
def focus_campo(widget):
    widget.focus_set()

lbl_nome = tk.Label(root, text="Nome:", underline=0)
lbl_nome.grid(row=0, column=0, sticky="e", padx=5, pady=5)
entry_nome = ttk.Entry(root, width=30)
entry_nome.grid(row=0, column=1, padx=5, pady=5)
root.bind("<Alt-n>", lambda e: focus_campo(entry_nome))

lbl_cognome = tk.Label(root, text="Cognome:", underline=0)
lbl_cognome.grid(row=1, column=0, sticky="e", padx=5, pady=5)
entry_cognome = ttk.Entry(root, width=30)
entry_cognome.grid(row=1, column=1, padx=5, pady=5)
root.bind("<Alt-c>", lambda e: focus_campo(entry_cognome))

# Tooltip accessibili (indicano la funzione del widget)
class ToolTip:
    """Tooltip leggero per migliorare la comprensione dei widget."""
    def __init__(self, widget, testo):
        self.widget = widget
        self.testo = testo
        self.tip_window = None
        widget.bind("<Enter>", self.mostra)
        widget.bind("<Leave>", self.nascondi)

    def mostra(self, event):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self.testo, background="#ffffe0",
                 relief="solid", borderwidth=1,
                 font=("Helvetica", 9)).pack()

    def nascondi(self, event):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

ToolTip(entry_nome, "Inserisci il nome (Alt+N per focus)")
ToolTip(entry_cognome, "Inserisci il cognome (Alt+C per focus)")

# Shortcut per azioni principali
btn = ttk.Button(root, text="Invia")
btn.grid(row=2, column=0, columnspan=2, pady=10)
root.bind("<Control-Return>", lambda e: btn.invoke())
ToolTip(btn, "Invia il modulo (Ctrl+Invio)")

# Focus iniziale
entry_nome.focus_set()

root.mainloop()
```

### Checklist Accessibilità per GUI Python

- [ ] Tutti i widget interattivi raggiungibili con Tab/Shift+Tab
- [ ] Tab order logico e coerente con il layout visivo
- [ ] Mnemonici (Alt+lettera) per i campi e pulsanti principali
- [ ] Shortcut da tastiera per le azioni frequenti (Ctrl+S, Ctrl+N, ecc.)
- [ ] Nome accessibile su ogni widget interattivo (`setAccessibleName` in Qt)
- [ ] Contrasto colori >= 4.5:1 (testo normale) e >= 3:1 (testo grande)
- [ ] Nessuna informazione trasmessa solo tramite colore
- [ ] Tooltip su widget non auto-esplicativi
- [ ] Dimensioni dei target cliccabili >= 44x44 pixel (WCAG 2.5.5)
- [ ] Test con screen reader (NVDA su Windows, Orca su Linux, VoiceOver su macOS)
- [ ] Rispetto del tema sistema (alto contrasto, riduzione animazioni)
- [ ] Feedback visivo dello stato di focus chiaramente distinguibile

---

## Kivy — GUI per Mobile

Kivy è un framework Python open-source per lo sviluppo di applicazioni con interfacce multi-touch, progettato specificamente per funzionare su desktop (Windows, macOS, Linux), dispositivi mobili (Android, iOS) e altri dispositivi con input touch. Kivy utilizza un proprio motore di rendering basato su OpenGL ES 2, il che significa che i widget non hanno l'aspetto nativo del sistema operativo ma sono completamente personalizzabili.

### Installazione e Primo Esempio

```bash
pip install kivy
```

```python
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class SalutoApp(App):
    def build(self):
        self.title = "Saluto App"
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        self.label = Label(text="Inserisci il tuo nome",
                           font_size=24, size_hint_y=0.3)
        layout.add_widget(self.label)

        self.campo = TextInput(hint_text="Nome...",
                                multiline=False, font_size=18,
                                size_hint_y=0.2)
        layout.add_widget(self.campo)

        btn = Button(text="Saluta", font_size=18,
                     size_hint_y=0.2,
                     background_color=(0.2, 0.6, 1.0, 1))
        btn.bind(on_press=self.saluta)
        layout.add_widget(btn)

        return layout

    def saluta(self, istanza):
        nome = self.campo.text.strip()
        if nome:
            self.label.text = f"Ciao, {nome}!"
        else:
            self.label.text = "Per favore inserisci un nome"


SalutoApp().run()
```

### Il Linguaggio Kv — Interfacce Dichiarative

Kivy offre un linguaggio dichiarativo (Kv language) simile a QML che separa la definizione dell'interfaccia dalla logica Python. Il file `.kv` viene associato automaticamente all'app se il suo nome corrisponde al nome della classe App (senza il suffisso "App", in minuscolo).

```python
# todo_app.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, StringProperty

class TodoRoot(BoxLayout):
    tasks = ListProperty([])
    nuovo_task = StringProperty("")

    def aggiungi(self):
        if self.nuovo_task.strip():
            self.tasks.append(self.nuovo_task.strip())
            self.nuovo_task = ""

    def rimuovi(self, indice):
        if 0 <= indice < len(self.tasks):
            del self.tasks[indice]


class TodoApp(App):
    def build(self):
        return TodoRoot()


TodoApp().run()
```

```yaml
# todo.kv (caricato automaticamente)
<TodoRoot>:
    orientation: "vertical"
    padding: 15
    spacing: 10

    Label:
        text: "Lista Attività"
        font_size: 28
        bold: True
        size_hint_y: 0.15
        color: 0.2, 0.6, 1, 1

    BoxLayout:
        size_hint_y: 0.12
        spacing: 5

        TextInput:
            text: root.nuovo_task
            on_text: root.nuovo_task = self.text
            hint_text: "Nuova attività..."
            multiline: False
            on_text_validate: root.aggiungi()

        Button:
            text: "Aggiungi"
            size_hint_x: 0.3
            on_press: root.aggiungi()
            background_color: 0.2, 0.7, 0.3, 1

    ScrollView:
        size_hint_y: 0.73

        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            spacing: 3

            # Iterazione dinamica sui task
```

### Packaging Kivy per Mobile

Per distribuire applicazioni Kivy su Android si utilizza **Buildozer**, che automatizza la creazione di APK tramite Python-For-Android.

```bash
pip install buildozer

# Inizializzare il progetto
buildozer init

# Compilare per Android (debug)
buildozer android debug

# Compilare e installare sul dispositivo connesso
buildozer android debug deploy run

# Compilare per il rilascio
buildozer android release
```

Il file `buildozer.spec` generato dal comando `init` contiene tutte le configurazioni necessarie: nome dell'app, package, versione, requisiti Python, permessi Android, orientamento dello schermo, icona e splash screen.

Per iOS, BeeWare Briefcase offre un percorso alternativo: `briefcase create iOS` genera un progetto Xcode che può essere compilato e distribuito tramite App Store Connect.

---

## GUI Testing — pytest-qt, pyautogui e Strategie di Test

Il testing delle applicazioni GUI è tradizionalmente considerato difficile a causa della dipendenza dall'event loop, dal rendering grafico e dalla temporizzazione degli eventi. Tuttavia, strumenti moderni rendono possibile testare sia i singoli widget che i flussi utente completi in modo affidabile e automatizzato.

### pytest-qt — Test per Applicazioni Qt

`pytest-qt` è un plugin pytest progettato per il testing di applicazioni PyQt e PySide. Fornisce un fixture `qtbot` che gestisce automaticamente la creazione e la distruzione dei widget e offre metodi per simulare interazioni utente.

```bash
pip install pytest-qt
```

```python
# test_app.py
import pytest
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton
from PyQt6.QtCore import Qt

class CalcolatriceWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.input_a = QLineEdit()
        self.input_a.setObjectName("input_a")
        self.input_b = QLineEdit()
        self.input_b.setObjectName("input_b")
        self.risultato = QLabel("Risultato: —")
        self.risultato.setObjectName("risultato")
        self.btn_somma = QPushButton("Somma")
        self.btn_somma.setObjectName("btn_somma")
        self.btn_somma.clicked.connect(self._calcola)
        layout.addWidget(self.input_a)
        layout.addWidget(self.input_b)
        layout.addWidget(self.btn_somma)
        layout.addWidget(self.risultato)

    def _calcola(self):
        try:
            a = float(self.input_a.text())
            b = float(self.input_b.text())
            self.risultato.setText(f"Risultato: {a + b}")
        except ValueError:
            self.risultato.setText("Errore: inserire numeri validi")


# ─── TEST ───
class TestCalcolatrice:
    @pytest.fixture
    def widget(self, qtbot):
        w = CalcolatriceWidget()
        qtbot.addWidget(w)
        w.show()
        return w

    def test_somma_corretta(self, widget, qtbot):
        """Verifica che la somma di due numeri produca il risultato atteso."""
        qtbot.keyClicks(widget.input_a, "10")
        qtbot.keyClicks(widget.input_b, "25")
        qtbot.mouseClick(widget.btn_somma, Qt.MouseButton.LeftButton)
        assert widget.risultato.text() == "Risultato: 35.0"

    def test_input_non_valido(self, widget, qtbot):
        """Verifica il messaggio di errore con input non numerico."""
        qtbot.keyClicks(widget.input_a, "abc")
        qtbot.keyClicks(widget.input_b, "5")
        qtbot.mouseClick(widget.btn_somma, Qt.MouseButton.LeftButton)
        assert "Errore" in widget.risultato.text()

    def test_somma_decimali(self, widget, qtbot):
        """Verifica la somma con numeri decimali."""
        qtbot.keyClicks(widget.input_a, "3.14")
        qtbot.keyClicks(widget.input_b, "2.86")
        qtbot.mouseClick(widget.btn_somma, Qt.MouseButton.LeftButton)
        assert "6.0" in widget.risultato.text()

    def test_widget_visibile(self, widget):
        """Verifica che tutti i componenti siano presenti."""
        assert widget.input_a.isVisible()
        assert widget.input_b.isVisible()
        assert widget.btn_somma.isVisible()
        assert widget.risultato.isVisible()
```

```bash
# Eseguire i test
pytest test_app.py -v

# Con test headless (CI/CD su Linux senza display)
# Richiede: xvfb-run o QT_QPA_PLATFORM=offscreen
QT_QPA_PLATFORM=offscreen pytest test_app.py -v
```

#### waitUntil e waitSignal — Attese Non Flaky

Per evitare test flaky (intermittenti), `pytest-qt` offre metodi di attesa basati su condizioni o segnali anziché `time.sleep()`.

```python
def test_operazione_asincrona(self, widget, qtbot):
    """Test di un'operazione che richiede tempo."""
    qtbot.mouseClick(widget.btn_avvia, Qt.MouseButton.LeftButton)

    # Attendi che un segnale venga emesso (timeout 5s)
    with qtbot.waitSignal(widget.worker.completato, timeout=5000):
        pass

    assert widget.label_stato.text() == "Completato"


def test_attesa_condizione(self, widget, qtbot):
    """Attendi che una condizione diventi vera."""
    qtbot.mouseClick(widget.btn_carica, Qt.MouseButton.LeftButton)

    def tabella_popolata():
        assert widget.tabella.rowCount() > 0

    qtbot.waitUntil(tabella_popolata, timeout=3000)
```

### pyautogui — Test Visuale e Automazione Desktop

`pyautogui` opera a livello di sistema operativo, controllando mouse e tastiera in modo indipendente dal toolkit GUI. È utile per test end-to-end che verificano il comportamento reale dell'applicazione.

```bash
pip install pyautogui
```

```python
import pyautogui
import subprocess
import time

def test_app_e2e():
    """Test end-to-end: avvia l'app, interagisce e verifica."""
    # Avvia l'applicazione
    processo = subprocess.Popen(["python", "app.py"])
    time.sleep(2)  # Attendi l'avvio

    try:
        # Trova e clicca un pulsante tramite immagine
        posizione = pyautogui.locateOnScreen("btn_aggiungi.png", confidence=0.9)
        if posizione:
            pyautogui.click(posizione)

        # Scrivi nel campo di input attivo
        pyautogui.typewrite("Test automatico", interval=0.05)
        pyautogui.press("enter")

        # Screenshot per verifica visuale
        screenshot = pyautogui.screenshot(region=(100, 100, 600, 400))
        screenshot.save("test_risultato.png")

        # Verifica che un elemento sia visibile
        trovato = pyautogui.locateOnScreen("elemento_atteso.png",
                                            confidence=0.8)
        assert trovato is not None, "Elemento atteso non trovato sullo schermo"
    finally:
        processo.terminate()
        processo.wait()
```

### Strategie di Test per GUI

**Unit test della logica separata dalla GUI.** La strategia più efficace è estrarre tutta la business logic in classi e funzioni pure che non dipendono dal toolkit GUI. Queste possono essere testate con pytest standard senza alcuna complessità aggiuntiva. Il sottile strato di collegamento tra logica e interfaccia richiede `pytest-qt` o strumenti simili, ma è minimo se l'architettura è ben separata (MVC/MVP).

**Test di integrazione con pytest-qt.** Verificano che i widget siano collegati correttamente alla logica: cliccando un pulsante il risultato atteso appare, inserendo dati in un form la validazione funziona, selezionando una riga in una tabella i dettagli si aggiornano.

**Test end-to-end con pyautogui.** Verificano il flusso utente completo partendo dall'avvio dell'applicazione. Sono i più fragili (dipendono da risoluzione, tema, posizione finestra) ma catturano problemi che gli altri livelli non vedono.

**Test headless in CI/CD.** Su server di integrazione continua senza display fisico, si utilizza `xvfb-run` (X Virtual Framebuffer) su Linux oppure la variabile d'ambiente `QT_QPA_PLATFORM=offscreen` per Qt. Questo permette di eseguire test GUI completi nelle pipeline CI senza hardware grafico.

---

## Sviluppo di Widget Personalizzati

Creare widget personalizzati è essenziale quando i widget standard del toolkit non soddisfano i requisiti dell'interfaccia. Ogni framework offre meccanismi diversi per la creazione di componenti riutilizzabili.

### Widget Personalizzati in tkinter

In tkinter, un widget personalizzato è tipicamente una classe che estende `tk.Frame` o `tk.Canvas` e compone widget standard in un'unità coerente con un'interfaccia pubblica pulita.

```python
import tkinter as tk
from tkinter import ttk

class RatingWidget(tk.Frame):
    """Widget di valutazione a stelle cliccabili."""

    def __init__(self, parent, max_stelle=5, dimensione=24, **kwargs):
        super().__init__(parent, **kwargs)
        self._max = max_stelle
        self._valore = 0
        self._stelle = []
        self._callback = None

        for i in range(max_stelle):
            lbl = tk.Label(self, text="☆", font=("", dimensione),
                           cursor="hand2", fg="#bdc3c7")
            lbl.pack(side="left", padx=1)
            lbl.bind("<Button-1>", lambda e, idx=i: self._click(idx))
            lbl.bind("<Enter>", lambda e, idx=i: self._hover(idx))
            lbl.bind("<Leave>", lambda e: self._aggiorna())
            self._stelle.append(lbl)

    def _click(self, indice):
        self._valore = indice + 1
        self._aggiorna()
        if self._callback:
            self._callback(self._valore)

    def _hover(self, indice):
        for i, s in enumerate(self._stelle):
            s.config(text="★" if i <= indice else "☆",
                     fg="#f39c12" if i <= indice else "#bdc3c7")

    def _aggiorna(self):
        for i, s in enumerate(self._stelle):
            s.config(text="★" if i < self._valore else "☆",
                     fg="#f1c40f" if i < self._valore else "#bdc3c7")

    @property
    def valore(self):
        return self._valore

    @valore.setter
    def valore(self, val):
        self._valore = max(0, min(val, self._max))
        self._aggiorna()

    def on_change(self, callback):
        self._callback = callback


# Utilizzo
root = tk.Tk()
root.title("Widget Personalizzato")
rating = RatingWidget(root, max_stelle=5, dimensione=28)
rating.pack(pady=20)
lbl = tk.Label(root, text="Valutazione: 0", font=("Helvetica", 14))
lbl.pack()
rating.on_change(lambda v: lbl.config(text=f"Valutazione: {v}"))
root.mainloop()
```

### Widget Personalizzati in Qt — QPainter e paintEvent

In Qt, i widget personalizzati si creano sottoclassando `QWidget` e sovrascrivendo il metodo `paintEvent()` per il rendering personalizzato tramite `QPainter`. Questo offre il massimo controllo sull'aspetto e sul comportamento del widget.

```python
from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient
import sys
import math

class GaugeWidget(QWidget):
    """Widget gauge circolare personalizzato con QPainter."""

    valore_cambiato = pyqtSignal(float)

    def __init__(self, parent=None, min_val=0, max_val=100):
        super().__init__(parent)
        self._min = min_val
        self._max = max_val
        self._valore = 0
        self.setMinimumSize(200, 200)

    @property
    def valore(self):
        return self._valore

    @valore.setter
    def valore(self, val):
        val = max(self._min, min(val, self._max))
        if val != self._valore:
            self._valore = val
            self.valore_cambiato.emit(val)
            self.update()  # Schedula un repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        lato = min(self.width(), self.height())
        rect = QRectF(
            (self.width() - lato) / 2 + 10,
            (self.height() - lato) / 2 + 10,
            lato - 20, lato - 20
        )

        # Sfondo arco (grigio)
        pen_bg = QPen(QColor(220, 220, 220), 12, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 225 * 16, -270 * 16)

        # Arco valore (gradiente dal verde al rosso)
        percentuale = (self._valore - self._min) / (self._max - self._min)
        r = int(255 * percentuale)
        g = int(255 * (1 - percentuale))
        pen_val = QPen(QColor(r, g, 50), 12, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_val)
        span = int(-270 * percentuale * 16)
        painter.drawArc(rect, 225 * 16, span)

        # Testo centrale
        painter.setPen(QColor(50, 50, 50))
        font = QFont("Segoe UI", int(lato / 5), QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter,
                          f"{self._valore:.0f}")

        # Etichetta unità
        font_piccolo = QFont("Segoe UI", int(lato / 12))
        painter.setFont(font_piccolo)
        painter.setPen(QColor(130, 130, 130))
        rect_basso = QRectF(rect.x(), rect.y() + lato * 0.25,
                             rect.width(), rect.height())
        painter.drawText(rect_basso, Qt.AlignmentFlag.AlignCenter, "%")

        painter.end()

    def mousePressEvent(self, event):
        """Permette di impostare il valore cliccando sul gauge."""
        self._aggiorna_da_posizione(event.position())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._aggiorna_da_posizione(event.position())

    def _aggiorna_da_posizione(self, pos):
        cx = self.width() / 2
        cy = self.height() / 2
        angolo = math.atan2(cy - pos.y(), pos.x() - cx)
        gradi = math.degrees(angolo)
        # Converti in range 0-270 partendo da 225°
        norm = (225 - gradi) % 360
        if norm <= 270:
            percentuale = norm / 270
            self.valore = self._min + percentuale * (self._max - self._min)


# Dimostrazione
app = QApplication(sys.argv)
win = QWidget()
win.setWindowTitle("Gauge Personalizzato")
layout = QVBoxLayout(win)
gauge = GaugeWidget()
gauge.valore = 65
layout.addWidget(gauge)
win.resize(300, 300)
win.show()
sys.exit(app.exec())
```

### Principi per Widget Riutilizzabili

**Incapsulamento.** Il widget deve esporre un'interfaccia pubblica chiara (proprietà, metodi, segnali/callback) e nascondere i dettagli implementativi. L'utente del widget non dovrebbe mai accedere direttamente ai componenti interni.

**Configurabilità.** Permettere la personalizzazione di colori, font, dimensioni e comportamenti tramite proprietà o parametri del costruttore, con valori predefiniti sensati.

**Segnali e callback.** Notificare i cambiamenti di stato tramite il meccanismo nativo del toolkit (segnali in Qt, callback/variabili di controllo in tkinter). Non usare polling o pattern non standard.

**Ridimensionamento.** Il widget deve adattarsi correttamente quando la finestra viene ridimensionata, usando `sizeHint()` e `minimumSizeHint()` in Qt, o `pack(expand=True, fill="both")` / `grid(sticky="nsew")` in tkinter.

---

## Layout Responsivi e Adattivi

Un layout responsivo si adatta dinamicamente alla dimensione della finestra e alla risoluzione dello schermo, garantendo un'esperienza utente ottimale su schermi di dimensioni diverse. Questo è particolarmente importante per applicazioni che devono funzionare su monitor da 13" a 32" e su schermi con diversi fattori DPI.

### Layout Responsivi in tkinter

```python
import tkinter as tk
from tkinter import ttk

class LayoutResponsivo(tk.Tk):
    """Layout che si adatta alla dimensione della finestra."""

    def __init__(self):
        super().__init__()
        self.title("Layout Responsivo")
        self.geometry("900x600")
        self.minsize(600, 400)

        # Configurazione pesi per il ridimensionamento
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Header fisso
        header = ttk.Frame(self, padding=10)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Applicazione Responsiva",
                  font=("Helvetica", 18, "bold")).pack(side="left")

        # Contenuto principale con pannelli ridimensionabili
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Pannello sinistro (sidebar)
        sidebar = ttk.Frame(paned, padding=5)
        paned.add(sidebar, weight=1)

        ttk.Label(sidebar, text="Navigazione",
                  font=("Helvetica", 12, "bold")).pack(anchor="w")
        for voce in ["Dashboard", "Utenti", "Impostazioni", "Report"]:
            ttk.Button(sidebar, text=voce).pack(fill="x", pady=2)

        # Pannello destro (contenuto)
        contenuto = ttk.Frame(paned, padding=5)
        paned.add(contenuto, weight=3)

        contenuto.columnconfigure(0, weight=1)
        contenuto.columnconfigure(1, weight=1)
        contenuto.rowconfigure(1, weight=1)

        # Schede statistiche che si adattano
        for i, (testo, colore) in enumerate([
            ("Utenti: 1.234", "#3498db"),
            ("Vendite: €5.678", "#2ecc71")
        ]):
            card = tk.Frame(contenuto, bg=colore, padx=15, pady=15)
            card.grid(row=0, column=i, sticky="ew", padx=3, pady=3)
            tk.Label(card, text=testo, bg=colore, fg="white",
                     font=("Helvetica", 14, "bold")).pack()

        # Tabella che occupa lo spazio rimanente
        tree = ttk.Treeview(contenuto, columns=("a", "b", "c"),
                             show="headings")
        tree.heading("a", text="Nome")
        tree.heading("b", text="Email")
        tree.heading("c", text="Ruolo")
        tree.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)

        # Footer
        footer = ttk.Frame(self, padding=5)
        footer.grid(row=2, column=0, sticky="ew")
        ttk.Label(footer, text="Stato: Connesso",
                  foreground="green").pack(side="left")

        # Reagire al ridimensionamento
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        if event.widget == self:
            w = event.width
            # Adatta il layout in base alla larghezza
            if w < 700:
                self.title("Layout Responsivo [Compatto]")
            else:
                self.title("Layout Responsivo [Ampio]")


app = LayoutResponsivo()
app.mainloop()
```

### Layout Responsivi in Qt

Qt offre un sistema di layout più sofisticato con `QSplitter`, `QStackedWidget` e la capacità di cambiare layout dinamicamente in base alle dimensioni della finestra.

```python
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel, QPushButton,
    QSplitter, QFrame)
from PyQt6.QtCore import Qt, QSize
import sys

class WidgetAdattivo(QMainWindow):
    """Finestra che cambia layout in base alla dimensione."""

    SOGLIA_COMPATTO = 600

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layout Adattivo Qt")
        self.setMinimumSize(400, 300)
        self.resize(900, 600)

        self.widget_centrale = QWidget()
        self.setCentralWidget(self.widget_centrale)
        self.layout_principale = QVBoxLayout(self.widget_centrale)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout_principale.addWidget(self.splitter)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.addWidget(QLabel("Menu"))
        for testo in ["Home", "Profilo", "Dati", "Aiuto"]:
            sidebar_layout.addWidget(QPushButton(testo))
        sidebar_layout.addStretch()
        self.splitter.addWidget(self.sidebar)

        # Area contenuto
        self.contenuto = QFrame()
        self.contenuto.setFrameShape(QFrame.Shape.StyledPanel)
        cont_layout = QVBoxLayout(self.contenuto)
        cont_layout.addWidget(QLabel("Contenuto Principale"))
        self.splitter.addWidget(self.contenuto)

        # Proporzioni splitter
        self.splitter.setSizes([200, 700])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() < self.SOGLIA_COMPATTO:
            self.sidebar.hide()
        else:
            self.sidebar.show()


app = QApplication(sys.argv)
win = WidgetAdattivo()
win.show()
sys.exit(app.exec())
```

### Gestione DPI e HiDPI

Sui display ad alta densità (Retina, 4K), le applicazioni devono scalare correttamente testo, icone e spaziature. In Qt, il supporto HiDPI è attivato di default da Qt 6. In tkinter, si può impostare il fattore di scala con `tk.call('tk', 'scaling', fattore)`.

```python
# Qt — DPI awareness (automatico in Qt 6)
import os
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

# tkinter — DPI awareness su Windows
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
except (AttributeError, OSError):
    pass  # Non su Windows o versione non supportata
```

---

## Integrazione con la System Tray

L'integrazione con la system tray (area di notifica) permette alle applicazioni di rimanere attive in background, mostrare notifiche e offrire un menu contestuale rapido senza occupare spazio nella barra delle applicazioni.

### System Tray con Qt — QSystemTrayIcon

```python
from PyQt6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon,
    QMenu, QLabel, QVBoxLayout, QWidget)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt
import sys

class AppSystemTray(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App con System Tray")
        self.resize(400, 300)

        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Chiudi la finestra: l'app resta nella tray."))

        # Crea un'icona programmaticamente (in produzione usare un file .png)
        icona = self._crea_icona()

        # System Tray Icon
        self.tray = QSystemTrayIcon(icona, self)
        self.tray.setToolTip("La Mia Applicazione")

        # Menu contestuale della tray
        menu = QMenu()

        mostra_action = QAction("Mostra finestra", self)
        mostra_action.triggered.connect(self._mostra_finestra)
        menu.addAction(mostra_action)

        stato_action = QAction("Stato: Attivo", self)
        stato_action.setEnabled(False)
        menu.addAction(stato_action)

        menu.addSeparator()

        esci_action = QAction("Esci", self)
        esci_action.triggered.connect(QApplication.quit)
        menu.addAction(esci_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        # Non terminare alla chiusura della finestra
        QApplication.setQuitOnLastWindowClosed(False)

    def _crea_icona(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#3498db"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.setPen(QColor("white"))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "A")
        painter.end()
        return QIcon(pixmap)

    def _mostra_finestra(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._mostra_finestra()

    def closeEvent(self, event):
        """Override: minimizza nella tray anziché chiudere."""
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "Applicazione minimizzata",
            "L'applicazione continua in background.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )


app = QApplication(sys.argv)
win = AppSystemTray()
win.show()
sys.exit(app.exec())
```

### System Tray con pystray — Toolkit-Indipendente

Per applicazioni che non usano Qt, la libreria `pystray` offre un'interfaccia cross-platform per la system tray che funziona con qualsiasi toolkit GUI o anche con applicazioni senza GUI (script di monitoraggio, servizi).

```bash
pip install pystray Pillow
```

```python
import pystray
from PIL import Image, ImageDraw
import threading

def crea_icona():
    """Crea un'icona semplice con Pillow."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=(52, 152, 219), outline=(41, 128, 185))
    return img

def on_mostra(icon, item):
    print("Mostra finestra richiesta")

def on_esci(icon, item):
    icon.stop()

# Creazione dell'icona e del menu
icona = pystray.Icon(
    "mia_app",
    crea_icona(),
    "La Mia App",
    menu=pystray.Menu(
        pystray.MenuItem("Mostra", on_mostra, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Esci", on_esci)
    )
)

# pystray.Icon.run() è bloccante: eseguire in un thread separato
# oppure integrare con il loop del toolkit GUI
icona.run()
```

### Notifiche Desktop

Sia Qt che pystray supportano le notifiche desktop native. In Qt, `QSystemTrayIcon.showMessage()` mostra una notifica balloon/toast. Per un controllo più fine, la libreria `plyer` offre un'interfaccia unificata per notifiche, vibrazioni e altri servizi di sistema.

```python
# Con Qt
tray.showMessage("Titolo", "Corpo della notifica",
                  QSystemTrayIcon.MessageIcon.Information, 3000)

# Con plyer (pip install plyer)
from plyer import notification
notification.notify(
    title="Titolo Notifica",
    message="Corpo della notifica desktop",
    app_name="Mia App",
    timeout=5
)
```

---

## Pattern MVC/MVP — Architettura Approfondita per GUI

I pattern architetturali MVC (Model-View-Controller) e MVP (Model-View-Presenter) sono fondamentali per organizzare il codice delle applicazioni GUI in modo manutenibile, testabile e scalabile. Questa sezione approfondisce le differenze tra i due pattern e le strategie di implementazione specifiche per i toolkit Python.

### MVC vs MVP — Differenze Sostanziali

Nel pattern **MVC** il Controller gestisce gli input dell'utente e aggiorna il Model; la View osserva il Model e si aggiorna automaticamente quando i dati cambiano. In questo schema esiste una comunicazione diretta tra View e Model (la View legge i dati dal Model).

Nel pattern **MVP** il Presenter sostituisce il Controller e funge da intermediario completo: la View non ha alcun contatto diretto con il Model. Ogni interazione passa attraverso il Presenter, che recupera i dati dal Model, li formatta e li passa alla View tramite un'interfaccia. Questo rende la View completamente passiva e molto più facile da testare (si può sostituire con un mock).

```
MVC:   View ←→ Model ←→ Controller ←→ View
MVP:   View ←→ Presenter ←→ Model
       (View non vede il Model)
```

### Implementazione MVP in Qt

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
    QLineEdit, QPushButton, QListWidget, QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt
import sys

# ── MODEL ──
@dataclass
class NoteModel:
    """Modello dati — nessuna dipendenza dal framework GUI."""
    _note: list = field(default_factory=list)

    def aggiungi(self, testo: str) -> int:
        self._note.append(testo)
        return len(self._note) - 1

    def rimuovi(self, indice: int) -> None:
        if 0 <= indice < len(self._note):
            del self._note[indice]

    def tutte(self) -> list[str]:
        return list(self._note)  # Copia difensiva

    @property
    def conteggio(self) -> int:
        return len(self._note)


# ── VIEW INTERFACE ──
class INoteView(ABC):
    """Interfaccia che il Presenter usa per comunicare con la View.
    Permette di sostituire la View reale con un mock nei test."""

    @abstractmethod
    def mostra_note(self, note: list[str]) -> None: ...

    @abstractmethod
    def get_testo_input(self) -> str: ...

    @abstractmethod
    def pulisci_input(self) -> None: ...

    @abstractmethod
    def mostra_conteggio(self, n: int) -> None: ...

    @abstractmethod
    def get_indice_selezionato(self) -> int: ...

    @abstractmethod
    def mostra_errore(self, messaggio: str) -> None: ...


# ── PRESENTER ──
class NotePresenter:
    """Presenter — orchestra Model e View senza conoscere Qt."""

    def __init__(self, model: NoteModel, view: INoteView):
        self._model = model
        self._view = view
        self._aggiorna_vista()

    def on_aggiungi(self):
        testo = self._view.get_testo_input().strip()
        if not testo:
            self._view.mostra_errore("Il testo non può essere vuoto")
            return
        self._model.aggiungi(testo)
        self._view.pulisci_input()
        self._aggiorna_vista()

    def on_rimuovi(self):
        indice = self._view.get_indice_selezionato()
        if indice < 0:
            self._view.mostra_errore("Seleziona una nota da rimuovere")
            return
        self._model.rimuovi(indice)
        self._aggiorna_vista()

    def _aggiorna_vista(self):
        self._view.mostra_note(self._model.tutte())
        self._view.mostra_conteggio(self._model.conteggio)


# ── VIEW (Qt) ──
class NoteViewQt(QWidget, INoteView):
    """Implementazione Qt della View — passiva, delegata al Presenter."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Note — Pattern MVP")
        self.resize(400, 400)
        layout = QVBoxLayout(self)

        # Input
        riga_input = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Nuova nota...")
        self._btn_aggiungi = QPushButton("Aggiungi")
        riga_input.addWidget(self._input)
        riga_input.addWidget(self._btn_aggiungi)
        layout.addLayout(riga_input)

        # Lista
        self._lista = QListWidget()
        layout.addWidget(self._lista)

        # Footer
        riga_footer = QHBoxLayout()
        self._lbl_conteggio = QLabel("Note: 0")
        self._btn_rimuovi = QPushButton("Rimuovi Selezionata")
        riga_footer.addWidget(self._lbl_conteggio)
        riga_footer.addStretch()
        riga_footer.addWidget(self._btn_rimuovi)
        layout.addLayout(riga_footer)

        self._lbl_errore = QLabel("")
        self._lbl_errore.setStyleSheet("color: red;")
        layout.addWidget(self._lbl_errore)

    def collega_presenter(self, presenter: NotePresenter):
        self._btn_aggiungi.clicked.connect(presenter.on_aggiungi)
        self._btn_rimuovi.clicked.connect(presenter.on_rimuovi)
        self._input.returnPressed.connect(presenter.on_aggiungi)

    # ── Implementazione INoteView ──
    def mostra_note(self, note):
        self._lista.clear()
        self._lista.addItems(note)
        self._lbl_errore.clear()

    def get_testo_input(self):
        return self._input.text()

    def pulisci_input(self):
        self._input.clear()

    def mostra_conteggio(self, n):
        self._lbl_conteggio.setText(f"Note: {n}")

    def get_indice_selezionato(self):
        items = self._lista.selectedItems()
        if items:
            return self._lista.row(items[0])
        return -1

    def mostra_errore(self, messaggio):
        self._lbl_errore.setText(messaggio)


# ── MAIN ──
app = QApplication(sys.argv)
model = NoteModel()
view = NoteViewQt()
presenter = NotePresenter(model, view)
view.collega_presenter(presenter)
view.show()
sys.exit(app.exec())
```

### Test del Presenter senza GUI

Il vantaggio chiave del pattern MVP è la testabilità: il Presenter può essere testato con un mock della View, senza avviare alcun toolkit GUI.

```python
# test_presenter.py
import pytest

class MockNoteView:
    """Mock della View per testare il Presenter."""

    def __init__(self):
        self.note_mostrate = []
        self.conteggio_mostrato = 0
        self.errore_mostrato = ""
        self.testo_input = ""
        self.indice_selezionato = -1
        self.input_pulito = False

    def mostra_note(self, note):
        self.note_mostrate = note
        self.errore_mostrato = ""

    def get_testo_input(self):
        return self.testo_input

    def pulisci_input(self):
        self.input_pulito = True
        self.testo_input = ""

    def mostra_conteggio(self, n):
        self.conteggio_mostrato = n

    def get_indice_selezionato(self):
        return self.indice_selezionato

    def mostra_errore(self, messaggio):
        self.errore_mostrato = messaggio


class TestNotePresenter:
    @pytest.fixture
    def setup(self):
        model = NoteModel()
        view = MockNoteView()
        presenter = NotePresenter(model, view)
        return model, view, presenter

    def test_aggiungi_nota(self, setup):
        model, view, presenter = setup
        view.testo_input = "Comprare il pane"
        presenter.on_aggiungi()
        assert "Comprare il pane" in view.note_mostrate
        assert view.conteggio_mostrato == 1
        assert view.input_pulito

    def test_aggiungi_vuoto_mostra_errore(self, setup):
        _, view, presenter = setup
        view.testo_input = "   "
        presenter.on_aggiungi()
        assert "vuoto" in view.errore_mostrato.lower()
        assert view.conteggio_mostrato == 0

    def test_rimuovi_senza_selezione(self, setup):
        _, view, presenter = setup
        view.indice_selezionato = -1
        presenter.on_rimuovi()
        assert "Seleziona" in view.errore_mostrato
```

### Quando Scegliere MVC vs MVP

**MVC** è più naturale in Qt dove il meccanismo di signals/slots permette alla View di osservare direttamente i cambiamenti nel Model. L'architettura Model-View di Qt (`QAbstractItemModel` + `QTableView`) è una variante di MVC già integrata nel framework.

**MVP** è preferibile quando la testabilità è prioritaria, quando la View è complessa con molti stati, quando si prevede di cambiare framework GUI, o quando si lavora con tkinter che non ha un sistema di osservazione reattivo come i segnali Qt.

In entrambi i casi, la regola fondamentale resta la stessa: la business logic non deve mai dipendere dal toolkit GUI. Questa separazione è il singolo fattore più importante per la manutenibilità a lungo termine dell'applicazione.

---

## FAQ

**Quale framework GUI Python scegliere per un progetto nuovo nel 2025-2026?**

La scelta dipende dal contesto. Per prototipi rapidi e applicazioni semplici, **tkinter** (con **CustomTkinter** per un aspetto moderno) resta la scelta più veloce perché non richiede installazioni aggiuntive. Per applicazioni desktop professionali con interfacce complesse, **PySide6** offre il toolkit più completo con licenza LGPL compatibile con software proprietario. Per applicazioni cross-platform desktop+web+mobile da un unico codebase, **Flet** è l'opzione più promettente. Per strumenti di visualizzazione dati ad alte prestazioni, **Dear PyGui** sfrutta la GPU per rendering efficiente. Per il targeting specifico di Android e iOS con Python, **Kivy** con Buildozer o **BeeWare** con Briefcase rappresentano le soluzioni principali.

**Qual è la differenza pratica tra PyQt6 e PySide6?**

L'API è quasi identica — nella maggior parte dei casi basta cambiare gli import. La differenza sostanziale è la licenza: PyQt6 è disponibile sotto GPL (obbliga a rilasciare il proprio codice come GPL) o licenza commerciale a pagamento. PySide6, mantenuto direttamente da Qt Company, usa la licenza LGPL che permette l'uso in software proprietario senza obbligo di rilascio del sorgente. Per progetti commerciali o proprietari, PySide6 è la scelta consigliata. Un'altra differenza minore riguarda i nomi dei decoratori: `pyqtSignal`/`pyqtSlot` in PyQt6 diventano `Signal`/`Slot` in PySide6.

**Come rendere un'applicazione GUI Python professionale e moderna nell'aspetto?**

Tre strategie principali: con **Qt**, utilizzare stylesheet CSS-like per personalizzare ogni aspetto visivo dei widget, oppure adottare QML per interfacce dichiarative con animazioni fluide. Con **tkinter**, passare a CustomTkinter che offre widget moderni con temi chiari/scuri out-of-the-box. In generale: definire un sistema di design coerente con palette colori, tipografia e spaziatura consistenti; evitare l'uso dei widget con l'aspetto di default; implementare stati hover/focus/disabled su tutti i controlli interattivi; e testare l'interfaccia su diversi sistemi operativi per verificare la coerenza visiva.

**Come gestire operazioni lunghe senza bloccare l'interfaccia?**

La regola d'oro è: mai eseguire operazioni che richiedono più di ~50ms nel thread principale della GUI. Le soluzioni variano per framework. In **tkinter**: usare `threading.Thread` per il lavoro pesante e comunicare col thread principale tramite `after()` o `queue.Queue`. In **Qt**: usare il pattern `QObject.moveToThread(QThread)` con signals/slots per la comunicazione thread-safe, oppure `QThreadPool` con `QRunnable` per task paralleli multipli. Per operazioni async (I/O di rete, database): integrare `asyncio` con il toolkit tramite librerie come `qasync` per Qt. In tutti i casi, non accedere mai ai widget dell'interfaccia da un thread secondario.

**Come distribuire un'applicazione GUI Python come eseguibile?**

Esistono quattro strumenti principali. **PyInstaller** è il più semplice e popolare: `pyinstaller --onefile --noconsole app.py` produce un eseguibile standalone, ma le dimensioni possono essere elevate. **Nuitka** compila Python in C nativo, producendo eseguibili più piccoli e veloci, ma richiede un compilatore C e tempi di build più lunghi. **cx_Freeze** è un'alternativa solida, specialmente per la creazione di installer MSI su Windows. **Briefcase** (BeeWare) produce pacchetti veramente nativi per ogni piattaforma (DMG, MSI, deb, AppImage) e supporta anche iOS e Android. Per scegliere: PyInstaller per la distribuzione rapida, Nuitka per prestazioni e protezione del sorgente, Briefcase per packaging nativo e distribuzione mobile.

**Come testare un'applicazione GUI in modo automatizzato in CI/CD?**

Per applicazioni Qt, **pytest-qt** è lo standard: fornisce fixture per creare widget, simulare click/input e attendere segnali senza flakiness. Per eseguire i test senza display fisico in CI, usare `QT_QPA_PLATFORM=offscreen` o `xvfb-run pytest`. Per test end-to-end indipendenti dal toolkit, **pyautogui** controlla mouse e tastiera a livello di sistema operativo, ma richiede un display (reale o virtuale). La strategia più efficace è estrarre la business logic in moduli puri testabili con pytest standard, minimizzando il codice che richiede test GUI-specifici. Il pattern MVP facilita questo approccio rendendo la View completamente passiva e sostituibile con mock nei test.

**tkinter supporta le tecnologie assistive e gli screen reader?**

Il supporto è limitato. Su Linux, il progetto **Tka11y** espone i widget tkinter tramite AT-SPI, rendendoli visibili a screen reader come Orca. Su Windows e macOS il supporto nativo per le tecnologie assistive è più limitato rispetto a Qt. Le best practice per migliorare l'accessibilità in tkinter includono: garantire navigazione completa da tastiera, aggiungere tooltip descrittivi, simulare mnemonici con binding `Alt+lettera`, mantenere un contrasto adeguato (WCAG AA), e usare `focus_set()` per gestire il tab order logicamente. Se l'accessibilità è un requisito critico, PySide6/PyQt6 offre un supporto significativamente superiore tramite il modulo `QAccessible` che si integra con MSAA/UIA (Windows), AT-SPI (Linux) e Accessibility API (macOS).

---

## Esercizi

1. **Todo App con tkinter** — Costruisci un'applicazione todo list con tkinter o CustomTkinter che supporti: aggiunta, modifica, eliminazione e completamento di task, persistenza su file JSON, filtro per stato (tutti/attivi/completati), e shortcut da tastiera (Ctrl+N per nuovo, Delete per eliminare). Applica il pattern MVC separando modello, vista e controller in moduli distinti.

2. **Dashboard con PySide6** — Crea una dashboard con PySide6 che mostri dati da un file CSV in una `QTableView` con `QAbstractTableModel`, includa un grafico (tramite `matplotlib` embedded o `QtCharts`), supporti il filtraggio e l'ordinamento delle colonne, e abbia un menu con import/export. Implementa il caricamento dati in un thread separato con `QThread` e segnala il progresso tramite `QProgressBar`.

3. **App cross-platform con Flet** — Sviluppa un'applicazione calcolatrice scientifica con Flet che funzioni su desktop e web. Implementa: layout responsive che si adatti alla dimensione della finestra, tema chiaro/scuro con toggle, cronologia delle operazioni, e gestione degli errori con feedback visivo. Testa sia in modalita desktop che nel browser.

4. **Distribuzione multi-piattaforma** — Prendi una delle applicazioni precedenti e creane un eseguibile distribuibile per il tuo sistema operativo usando PyInstaller. Configura: icona personalizzata, inclusione di asset (immagini, font), esclusione di moduli non necessari per ridurre le dimensioni, e one-file mode. Documenta le dimensioni dell'eseguibile e il tempo di avvio.

5. **Accessibilita e testing GUI** — Aggiungi a un'applicazione GUI esistente: navigazione completa da tastiera con tab order logico, tooltip su tutti i widget interattivi, contrasto cromatico conforme WCAG AA, supporto per screen reader (dove il toolkit lo permette). Scrivi test automatizzati che verifichino la creazione della finestra, il funzionamento dei pulsanti e la persistenza dei dati.

---

## Letture e Riferimenti

### Fonti primarie

- Python Documentation — *tkinter* — https://docs.python.org/3/library/tkinter.html (consultato: 2026-05-24)
- Python Documentation — *tkinter.dnd* — https://docs.python.org/3/library/tkinter.dnd.html (consultato: 2026-05-24)
- Qt for Python Documentation — *PySide6* — https://doc.qt.io/qtforpython-6/ (consultato: 2026-05-24)
- Qt for Python — *Model/View Programming* — https://doc.qt.io/qtforpython-6/overviews/qtwidgets-model-view-programming.html (consultato: 2026-05-24)
- Qt for Python — *QAbstractListModel in QML* — https://doc.qt.io/qtforpython-6/examples/example_qml_editingmodel.html (consultato: 2026-05-24)
- Qt for Python — *QSystemTrayIcon Example* — https://doc.qt.io/qtforpython-6/examples/example_widgets_desktop_systray.html (consultato: 2026-05-24)
- CustomTkinter Documentation — https://customtkinter.tomschimansky.com/ (consultato: 2026-05-24)
- Flet Documentation — https://flet.dev/docs/ (consultato: 2026-05-24)
- Dear PyGui Documentation — https://dearpygui.readthedocs.io/ (consultato: 2026-05-24)
- Kivy Documentation — https://kivy.org/doc/stable/ (consultato: 2026-05-24)
- PyInstaller Documentation — https://pyinstaller.org/en/stable/ (consultato: 2026-05-24)
- Nuitka Documentation — https://nuitka.net/doc/user-manual.html (consultato: 2026-05-24)
- BeeWare / Briefcase Documentation — https://briefcase.beeware.org/ (consultato: 2026-05-24)
- BeeWare / Toga Documentation — https://toga.readthedocs.io/ (consultato: 2026-05-24)
- pytest-qt Documentation — https://pytest-qt.readthedocs.io/ (consultato: 2026-05-24)
- pystray Documentation — https://pystray.readthedocs.io/en/latest/usage.html (consultato: 2026-05-24)
- Tka11y (Tk Accessibility) — https://pypi.org/project/Tka11y/ (consultato: 2026-05-24)
- WCAG 2.1 — Web Content Accessibility Guidelines — https://www.w3.org/TR/WCAG21/ (consultato: 2026-05-24)

### Libri consigliati

- *Create GUI Applications with Python & Qt6* — Martin Fitzpatrick — 2022
- *Python GUI Programming with Tkinter, 2nd Edition* — Alan D. Moore — Packt, 2021
- *Kivy — Interactive Applications and Games in Python, 2nd Edition* — Roberto Ulloa — Packt, 2019

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [07 — OOP](07-oop.md) | Classi, ereditarieta, pattern MVC — fondamenta per architetture GUI |
| [08 — Concorrenza e Parallelismo](08-concorrenza.md) | Threading per operazioni non bloccanti nella UI |
| [21 — Design Patterns](21-design-patterns.md) | Pattern Observer (signals/slots), MVC, Command per undo/redo |
| [22 — Clean Code](22-clean-code.md) | Separazione logica/presentazione, naming, organizzazione del codice |
| [05 — Gestione File e I/O](05-gestione-file-io.md) | Persistenza dati dell'applicazione su file |
| [26 — Docker](26-docker-per-python.md) | Distribuzione di applicazioni GUI containerizzate |

---

## Glossario

| Termine | Definizione |
|---|---|
| **GUI** | Graphical User Interface — interfaccia grafica che permette l'interazione tramite elementi visivi (finestre, pulsanti, menu) |
| **Widget** | Elemento grafico interattivo dell'interfaccia (pulsante, campo di testo, slider, checkbox, ecc.) |
| **Event Loop** | Ciclo infinito che attende e despaccia eventi dell'interfaccia (click, tastiera, ridimensionamento) |
| **Signal/Slot** | Meccanismo di Qt per la comunicazione tra oggetti: un signal emesso da un widget viene ricevuto da uno slot (funzione) collegato |
| **Layout Manager** | Sistema che posiziona e ridimensiona automaticamente i widget all'interno di un container |
| **MVC** | Model-View-Controller — pattern architetturale che separa dati (Model), presentazione (View) e logica di controllo (Controller) |
| **tkinter** | Libreria GUI standard di Python, binding del toolkit Tk/Tcl |
| **PySide6** | Binding ufficiale Qt per Python con licenza LGPL, mantenuto da Qt Company |
| **CustomTkinter** | Estensione moderna di tkinter che aggiunge widget con aspetto contemporaneo |
| **Flet** | Framework Python per GUI cross-platform basato su Flutter, con supporto desktop/web/mobile |
| **PyInstaller** | Strumento per impacchettare applicazioni Python in eseguibili standalone per Windows, macOS e Linux |
| **Nuitka** | Compilatore Python-to-C che produce eseguibili nativi con prestazioni superiori a PyInstaller |
| **DPI Scaling** | Adattamento dell'interfaccia alla densita di pixel dello schermo per garantire leggibilita su display ad alta risoluzione |
| **MVP** | Model-View-Presenter — variante di MVC dove il Presenter media completamente tra View e Model, rendendo la View passiva e altamente testabile |
| **QML** | Qt Modeling Language — linguaggio dichiarativo di Qt per definire interfacce grafiche in modo reattivo, integrato con Python tramite PySide6 |
| **QAbstractTableModel** | Classe base Qt per modelli di dati tabulari personalizzati, parte dell'architettura Model-View |
| **QSortFilterProxyModel** | Modello proxy Qt che aggiunge ordinamento e filtraggio sopra un modello sorgente senza modificarne i dati |
| **QThread** | Classe Qt per l'esecuzione di codice in un thread separato, integrata con il sistema signals/slots per la comunicazione thread-safe |
| **QRunnable** | Interfaccia Qt per task eseguibili in un pool di thread (`QThreadPool`), utile per operazioni concorrenti multiple |
| **Kivy** | Framework Python open-source per interfacce multi-touch, basato su OpenGL ES 2, con supporto per desktop, Android e iOS |
| **Kv Language** | Linguaggio dichiarativo di Kivy per definire interfacce separando la struttura UI dalla logica Python |
| **Buildozer** | Strumento per compilare applicazioni Kivy in pacchetti Android (APK) e iOS |
| **Briefcase** | Strumento BeeWare per packaging di applicazioni Python in formati nativi per desktop (MSI, DMG, deb) e mobile (Xcode, Gradle) |
| **pytest-qt** | Plugin pytest per il testing di applicazioni PyQt e PySide, con fixture `qtbot` per simulare interazioni utente |
| **pyautogui** | Libreria Python per l'automazione GUI a livello di sistema operativo tramite controllo di mouse e tastiera |
| **pystray** | Libreria Python cross-platform per la creazione di icone nella system tray, indipendente dal toolkit GUI |
| **QSystemTrayIcon** | Classe Qt per aggiungere un'icona nell'area di notifica del sistema operativo con menu contestuale e notifiche |
| **QPainter** | Classe Qt per il disegno 2D personalizzato: forme, testo, gradienti e immagini su qualsiasi widget o pixmap |
| **Immediate-Mode GUI** | Paradigma GUI dove l'interfaccia viene ridisegnata interamente ad ogni frame (usato da Dear PyGui) anziché mantenere uno stato persistente dei widget |
| **a11y** | Abbreviazione di "accessibility" (a + 11 lettere + y) — insieme di pratiche per rendere il software utilizzabile da persone con disabilita |
| **AT-SPI** | Assistive Technology Service Provider Interface — protocollo Linux per l'interazione tra applicazioni e tecnologie assistive (screen reader, ingranditori) |
| **WCAG** | Web Content Accessibility Guidelines — standard W3C per l'accessibilita dei contenuti, applicabile anche alle interfacce desktop per i criteri di contrasto e navigabilita |
| **Tab Order** | Ordine in cui il focus si sposta tra i widget quando l'utente preme il tasto Tab; deve seguire la logica visiva del layout |
| **HiDPI** | High Dots Per Inch — display ad alta risoluzione (Retina, 4K) che richiedono il corretto scaling delle interfacce per evitare elementi troppo piccoli |
| **Retained-Mode GUI** | Paradigma GUI tradizionale dove i widget mantengono il proprio stato interno e vengono aggiornati solo quando necessario (usato da tkinter, Qt, GTK) |
