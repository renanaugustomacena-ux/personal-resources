# Programmazione procedurale e controllo di flusso

## Scope
Questo capitolo approfondisce il cuore della programmazione Fortran: il modello procedurale, la strutturazione del codice tramite subroutine e function, i meccanismi di controllo del flusso di esecuzione e le tecniche per scrivere codice modulare, chiaro e riutilizzabile. Si parte dal concetto di program unit e scope, si analizzano in dettaglio le procedure (subroutine e function), gli attributi degli argomenti, le interfacce, la ricorsione e i costrutti avanzati di controllo. L'obiettivo non è solo conoscere la sintassi, ma comprendere come pensare in modo procedurale per costruire programmi scientifici ben organizzati.

## Audience
Questo documento è pensato per chi ha già letto il capitolo sui fondamenti del linguaggio Fortran e vuole approfondire la progettazione procedurale. È particolarmente utile per studenti, ricercatori e sviluppatori che devono scrivere programmi scientifici strutturati, con routine riutilizzabili e flussi di esecuzione complessi.

## Obiettivo didattico
Alla fine di questo capitolo lo studente dovrebbe essere in grado di:
- comprendere la differenza tra subroutine e function e sapere quando usare l'una o l'altra
- usare correttamente gli attributi intent(in), intent(out) e intent(inout)
- scrivere interfacce esplicite per le procedure
- usare argomenti opzionali e keyword arguments
- scrivere procedure interne con `contains`
- implementare funzioni ricorsive
- padroneggiare i costrutti if/else if/else, select case, do, do while, do concurrent
- usare cycle, exit e loop etichettati
- comprendere il costrutto block e associate
- scrivere procedure pure ed elemental
- evitare gli errori più comuni nella programmazione procedurale Fortran

## Prerequisiti
Prima di affrontare questo capitolo è utile avere:
- una comprensione solida della sintassi di base di Fortran (capitolo 01)
- familiarità con la dichiarazione di variabili e tipi primitivi
- il compilatore gfortran installato e funzionante (capitolo 02)
- esperienza minima con la compilazione e l'esecuzione di programmi Fortran

## Fonti autorevoli da tenere come riferimento
- Fortran-lang Learn: Procedures
- Fortran-lang Best Practices: Procedures
- GCC gfortran documentation
- Standard Fortran 2008 e 2018 per i costrutti moderni (block, do concurrent, associate)

## 1. Program units e scope
In Fortran, il codice è organizzato in unità di programma (program units). Ogni program unit è un blocco autonomo con il proprio scope, cioè il proprio spazio di nomi. Le principali program units sono:

- **program**: il punto di ingresso del programma
- **module**: un contenitore di dichiarazioni, tipi, costanti e procedure
- **subroutine**: una procedura che non restituisce un valore direttamente
- **function**: una procedura che restituisce un valore
- **submodule**: un'estensione di un modulo (Fortran 2008)

Lo scope è il contesto in cui le variabili sono visibili e accessibili. In Fortran, ogni program unit ha il proprio scope: le variabili dichiarate in una subroutine non sono visibili al di fuori di essa, e viceversa. Questo principio di isolamento è fondamentale per scrivere codice robusto.

```fortran
program esempio_scope
  implicit none
  integer :: x
  x = 10
  call mostra()
  print *, 'Nel program: x =', x
contains
  subroutine mostra()
    ! Qui x del program è accessibile tramite host association
    print *, 'Nella subroutine: x =', x
  end subroutine mostra
end program esempio_scope
```

In questo esempio, la subroutine `mostra` è una procedura interna (contenuta nel `program` tramite `contains`). Le procedure interne hanno accesso alle variabili del blocco che le contiene tramite il meccanismo di host association. Le procedure esterne, invece, non hanno questa visibilità e comunicano solo attraverso i loro argomenti.

La regola pratica è: più lo scope è ristretto, più il codice è sicuro e facile da mantenere. Variabili globali o con scope troppo ampio rendono il codice fragile e difficile da debuggare.

## 2. Subroutine: il blocco procedurale fondamentale
Una subroutine è una procedura che esegue un'azione senza restituire direttamente un valore. La comunicazione avviene attraverso i suoi argomenti. Le subroutine sono il mattone fondamentale della programmazione procedurale Fortran e sono usate per operazioni che modificano dati, producono output, o eseguono calcoli i cui risultati vengono restituiti attraverso più argomenti.

```fortran
subroutine scambia(a, b)
  implicit none
  real, intent(inout) :: a, b
  real :: temp
  temp = a
  a = b
  b = temp
end subroutine scambia
```

Per chiamare una subroutine si usa la parola chiave `call`:

```fortran
program test_scambia
  implicit none
  real :: x, y
  x = 3.0
  y = 7.0
  print *, 'Prima:', x, y
  call scambia(x, y)
  print *, 'Dopo:', x, y
end program test_scambia
```

La subroutine `scambia` riceve due argomenti reali, li scambia e li restituisce modificati. L'uso di `intent(inout)` indica che entrambi gli argomenti sono sia letti sia scritti.

### Quando usare una subroutine
Le subroutine sono preferibili quando:
- l'operazione ha effetti collaterali (modifica i dati, scrive su file, stampa output)
- si devono restituire più valori
- l'operazione non ha un singolo risultato naturale
- si implementano algoritmi che trasformano dati in-place

## 3. Function: procedure che restituiscono un valore
Una function è una procedura che restituisce un singolo valore. A differenza della subroutine, la function ha un tipo di ritorno e può essere usata direttamente nelle espressioni.

```fortran
function distanza(x1, y1, x2, y2) result(d)
  implicit none
  real, intent(in) :: x1, y1, x2, y2
  real :: d
  d = sqrt((x2 - x1)**2 + (y2 - y1)**2)
end function distanza
```

La clausola `result(d)` specifica il nome della variabile di ritorno. Se non si usa `result`, il nome della funzione stessa è la variabile di ritorno:

```fortran
function area_rettangolo(base, altezza)
  implicit none
  real, intent(in) :: base, altezza
  real :: area_rettangolo
  area_rettangolo = base * altezza
end function area_rettangolo
```

L'uso di `result` è consigliato perché rende il codice più leggibile, specialmente per funzioni ricorsive dove il nome della funzione deve poter essere usato nella chiamata ricorsiva.

### Quando usare una function
Le function sono preferibili quando:
- l'operazione ha un singolo risultato naturale (un calcolo matematico, una conversione, un test)
- il risultato deve essere usato direttamente in un'espressione
- la procedura non ha effetti collaterali

```fortran
program test_funzioni
  implicit none
  real :: d

  ! La function può essere usata direttamente in un'espressione
  d = distanza(0.0, 0.0, 3.0, 4.0)
  print *, 'Distanza:', d

  ! Oppure direttamente nella print
  print *, 'Area:', area_rettangolo(5.0, 3.0)

contains
  function distanza(x1, y1, x2, y2) result(d)
    implicit none
    real, intent(in) :: x1, y1, x2, y2
    real :: d
    d = sqrt((x2 - x1)**2 + (y2 - y1)**2)
  end function distanza

  function area_rettangolo(base, altezza) result(area)
    implicit none
    real, intent(in) :: base, altezza
    real :: area
    area = base * altezza
  end function area_rettangolo
end program test_funzioni
```

## 4. Intent: il contratto degli argomenti
L'attributo `intent` è uno dei concetti più importanti della programmazione procedurale Fortran. Definisce come un argomento viene usato dalla procedura e costituisce un contratto tra la procedura e chi la chiama.

### intent(in)
L'argomento è solo in lettura. La procedura lo riceve ma non lo modifica. Il compilatore genera un errore se si tenta di assegnare un valore a un argomento `intent(in)`.

```fortran
function quadrato(x) result(q)
  implicit none
  real, intent(in) :: x
  real :: q
  q = x * x
  ! x = 0.0  ! ERRORE: non si può modificare un intent(in)
end function quadrato
```

### intent(out)
L'argomento è solo in scrittura. La procedura lo usa per restituire un valore. Il valore iniziale dell'argomento è indefinito all'ingresso nella procedura. Questo significa che non si deve leggere un argomento `intent(out)` prima di avergli assegnato un valore.

```fortran
subroutine inizializza(valore, stato)
  implicit none
  real, intent(out) :: valore
  integer, intent(out) :: stato
  valore = 0.0
  stato = 0
end subroutine inizializza
```

### intent(inout)
L'argomento è sia in lettura sia in scrittura. La procedura lo riceve, lo legge e può modificarlo. Questo è l'intent da usare quando si vuole trasformare un dato in-place.

```fortran
subroutine raddoppia(x)
  implicit none
  real, intent(inout) :: x
  x = x * 2.0
end subroutine raddoppia
```

### Perché usare intent è fondamentale
Specificare l'intent non è solo una buona pratica: è un meccanismo di sicurezza. Il compilatore può verificare che gli argomenti siano usati correttamente e segnalare errori a compile-time anziché a runtime. Inoltre, `intent` documenta il comportamento della procedura in modo chiaro e verificabile.

Regola pratica: usare sempre `intent`. Preferire `intent(in)` quando possibile, perché rende la procedura più sicura e più facile da ragionare. Usare `intent(out)` per i risultati e `intent(inout)` solo quando è davvero necessario modificare l'argomento originale.

```fortran
! Esempio completo che mostra tutti e tre gli intent
subroutine statistiche(dati, n, media, varianza)
  implicit none
  integer, intent(in) :: n
  real, intent(in) :: dati(n)
  real, intent(out) :: media, varianza
  integer :: i
  real :: somma, somma_sq

  somma = 0.0
  do i = 1, n
    somma = somma + dati(i)
  end do
  media = somma / real(n)

  somma_sq = 0.0
  do i = 1, n
    somma_sq = somma_sq + (dati(i) - media)**2
  end do
  varianza = somma_sq / real(n)
end subroutine statistiche
```

## 5. Argomenti opzionali e keyword arguments
Fortran supporta argomenti opzionali tramite l'attributo `optional` e il costrutto `present()` per verificare se un argomento è stato passato.

```fortran
subroutine saluta(nome, formale)
  implicit none
  character(len=*), intent(in) :: nome
  logical, intent(in), optional :: formale
  logical :: usa_formale

  if (present(formale)) then
    usa_formale = formale
  else
    usa_formale = .false.
  end if

  if (usa_formale) then
    print *, 'Gentile ', trim(nome), ', buongiorno.'
  else
    print *, 'Ciao, ', trim(nome), '!'
  end if
end subroutine saluta
```

La funzione intrinseca `present()` restituisce `.true.` se l'argomento opzionale è stato passato nella chiamata, `.false.` altrimenti. È fondamentale controllare `present()` prima di accedere a un argomento opzionale, altrimenti il comportamento è indefinito.

### Keyword arguments
In Fortran, gli argomenti possono essere passati per posizione o per nome (keyword). I keyword arguments sono particolarmente utili quando ci sono molti argomenti opzionali.

```fortran
program test_saluta
  implicit none

  interface
    subroutine saluta(nome, formale)
      character(len=*), intent(in) :: nome
      logical, intent(in), optional :: formale
    end subroutine saluta
  end interface

  call saluta('Mario')                    ! Solo argomento obbligatorio
  call saluta('Dottoressa Rossi', .true.)  ! Per posizione
  call saluta('Professor Bianchi', formale=.true.)  ! Per keyword
  call saluta(formale=.false., nome='Luca')  ! Ordine invertito con keyword
end program test_saluta
```

I keyword arguments permettono di chiamare procedure in modo più leggibile, soprattutto quando ci sono molti parametri. L'unica regola è che, una volta che si inizia a usare keyword arguments in una chiamata, tutti gli argomenti successivi devono anch'essi essere specificati per keyword.

## 6. Interfacce esplicite e implicite
In Fortran, un'interfaccia descrive la firma di una procedura: il numero e il tipo dei suoi argomenti, i loro intent, e il tipo di ritorno per le function. Le interfacce possono essere esplicite o implicite.

### Interfaccia implicita
Quando si chiama una procedura esterna senza fornire informazioni sulla sua interfaccia, il compilatore usa un'interfaccia implicita. In questo caso, il compilatore non può verificare che gli argomenti passati siano corretti in tipo, numero e intent. Questo è pericoloso e può causare errori difficili da trovare.

### Interfaccia esplicita
Un'interfaccia esplicita fornisce al compilatore tutte le informazioni necessarie per verificare la correttezza della chiamata. Ci sono tre modi per ottenere un'interfaccia esplicita:

1. **Procedure interne** (tramite `contains`): l'interfaccia è automaticamente esplicita
2. **Procedure in un module**: l'interfaccia è automaticamente esplicita quando si usa `use`
3. **Blocco interface**: si dichiara esplicitamente l'interfaccia

```fortran
! Metodo 3: blocco interface esplicito
program test_interfaccia
  implicit none

  interface
    function fattoriale(n) result(f)
      integer, intent(in) :: n
      integer :: f
    end function fattoriale
  end interface

  print *, 'Fattoriale di 5:', fattoriale(5)
end program test_interfaccia

function fattoriale(n) result(f)
  implicit none
  integer, intent(in) :: n
  integer :: f
  integer :: i
  f = 1
  do i = 2, n
    f = f * i
  end do
end function fattoriale
```

### La pratica consigliata
La pratica moderna è evitare le interfacce implicite. Il modo più semplice è mettere le procedure all'interno di un module, il che garantisce interfacce esplicite automatiche. Le procedure interne (con `contains`) sono un'alternativa per programmi semplici.

```fortran
module operazioni
  implicit none
contains
  function fattoriale(n) result(f)
    integer, intent(in) :: n
    integer :: f
    integer :: i
    f = 1
    do i = 2, n
      f = f * i
    end do
  end function fattoriale
end module operazioni

program test
  use operazioni, only: fattoriale
  implicit none
  print *, fattoriale(5)  ! Interfaccia esplicita garantita dal module
end program test
```

## 7. Procedure interne con contains
La parola chiave `contains` permette di definire procedure interne a un program, module, subroutine o function. Le procedure interne sono visibili solo all'interno del blocco che le contiene e hanno accesso alle variabili del blocco ospitante tramite host association.

```fortran
program calcolo_cerchio
  implicit none
  real, parameter :: pi = 3.14159265
  real :: raggio, a, c

  raggio = 5.0
  a = area(raggio)
  c = circonferenza(raggio)

  print *, 'Raggio:', raggio
  print *, 'Area:', a
  print *, 'Circonferenza:', c

contains
  function area(r) result(a)
    real, intent(in) :: r
    real :: a
    a = pi * r**2   ! pi è accessibile per host association
  end function area

  function circonferenza(r) result(c)
    real, intent(in) :: r
    real :: c
    c = 2.0 * pi * r
  end function circonferenza
end program calcolo_cerchio
```

### Vantaggi delle procedure interne
- Interfaccia esplicita automatica
- Accesso alle variabili del host
- Organizzazione logica del codice
- Nessun bisogno di blocchi interface

### Limiti delle procedure interne
- Non sono riutilizzabili in altri file o moduli
- Non possono contenere a loro volta procedure interne (una sola nidificazione)
- Per codice condiviso tra più programmi, i moduli sono preferibili

## 8. Procedure esterne
Le procedure esterne sono definite al di fuori di qualsiasi program unit. Sono il modo più antico di organizzare il codice in Fortran e richiedono interfacce esplicite (tramite blocco `interface`) per essere usate correttamente.

```fortran
! File: media.f90 — procedura esterna
function media_aritmetica(dati, n) result(m)
  implicit none
  integer, intent(in) :: n
  real, intent(in) :: dati(n)
  real :: m
  m = sum(dati) / real(n)
end function media_aritmetica
```

```fortran
! File: main.f90 — programma principale
program test_media
  implicit none

  interface
    function media_aritmetica(dati, n) result(m)
      integer, intent(in) :: n
      real, intent(in) :: dati(n)
      real :: m
    end function media_aritmetica
  end interface

  real :: valori(5) = [1.0, 2.0, 3.0, 4.0, 5.0]
  print *, 'Media:', media_aritmetica(valori, 5)
end program test_media
```

Le procedure esterne sono oggi considerate una pratica legacy. La raccomandazione moderna è usare i moduli, che forniscono interfacce esplicite automatiche e una migliore organizzazione del codice.

## 9. Ricorsione
Fortran supporta le procedure ricorsive. Dal Fortran 2018, tutte le procedure sono implicitamente ricorsive. Nelle versioni precedenti, è necessario usare la parola chiave `recursive`.

```fortran
recursive function fattoriale(n) result(f)
  implicit none
  integer, intent(in) :: n
  integer :: f

  if (n <= 1) then
    f = 1
  else
    f = n * fattoriale(n - 1)
  end if
end function fattoriale
```

La clausola `result` è obbligatoria per le funzioni ricorsive (nelle versioni pre-2018), perché il nome della funzione è usato per la chiamata ricorsiva e non può essere anche la variabile di ritorno.

### Esempio: sequenza di Fibonacci

```fortran
program test_fibonacci
  implicit none
  integer :: i

  print *, 'Sequenza di Fibonacci:'
  do i = 1, 15
    print '(A, I2, A, I8)', '  F(', i, ') = ', fibonacci(i)
  end do

contains
  recursive function fibonacci(n) result(f)
    integer, intent(in) :: n
    integer :: f
    if (n <= 1) then
      f = n
    else
      f = fibonacci(n - 1) + fibonacci(n - 2)
    end if
  end function fibonacci
end program test_fibonacci
```

### Considerazioni sulla ricorsione
La ricorsione in Fortran funziona bene per problemi che hanno una struttura naturalmente ricorsiva. Tuttavia, per problemi come Fibonacci, la ricorsione ingenua è molto inefficiente perché ricalcola gli stessi valori più volte. In pratica, per il calcolo scientifico si preferiscono spesso approcci iterativi, che sono più efficienti e non hanno il rischio di stack overflow per input grandi.

## 10. Il costrutto if-else
Il costrutto `if` è il meccanismo fondamentale di branching in Fortran. Permette di eseguire blocchi di codice diversi in base a condizioni logiche.

### if semplice

```fortran
if (x > 0.0) then
  print *, 'x è positivo'
end if
```

### if-else

```fortran
if (x > 0.0) then
  print *, 'x è positivo'
else
  print *, 'x è zero o negativo'
end if
```

### if-else if-else

```fortran
if (x > 0.0) then
  print *, 'x è positivo'
else if (x < 0.0) then
  print *, 'x è negativo'
else
  print *, 'x è zero'
end if
```

### if su una riga
Per azioni semplici, Fortran permette un if su una riga senza `then` e `end if`:

```fortran
if (x > 0.0) print *, 'positivo'
```

Questa forma è utile per controlli rapidi, ma per blocchi più complessi è sempre meglio usare la forma completa con `then` e `end if`.

### Operatori relazionali e logici

| Operatore | Significato |
|-----------|-------------|
| `==` o `.eq.` | Uguale a |
| `/=` o `.ne.` | Diverso da |
| `>` o `.gt.` | Maggiore di |
| `<` o `.lt.` | Minore di |
| `>=` o `.ge.` | Maggiore o uguale a |
| `<=` o `.le.` | Minore o uguale a |
| `.and.` | AND logico |
| `.or.` | OR logico |
| `.not.` | NOT logico |
| `.eqv.` | Equivalenza logica |
| `.neqv.` | Non-equivalenza logica |

La sintassi moderna (`==`, `/=`, `>`, `<`, `>=`, `<=`) è preferibile alle forme storiche (`.eq.`, `.ne.`, etc.) perché è più leggibile.

```fortran
program test_condizioni
  implicit none
  real :: temperatura
  logical :: piove

  temperatura = 25.0
  piove = .false.

  if (temperatura > 20.0 .and. .not. piove) then
    print *, 'Bel tempo per uscire!'
  else if (temperatura > 20.0 .and. piove) then
    print *, 'Caldo ma piove, prendi l''ombrello'
  else
    print *, 'Resta a casa'
  end if
end program test_condizioni
```

## 11. Select case: selezione multipla
Il costrutto `select case` è l'alternativa Fortran al `switch` di C/C++. È più chiaro e sicuro di una catena di `if-else if` quando si deve selezionare tra valori discreti.

```fortran
program giorno_settimana
  implicit none
  integer :: giorno

  giorno = 3

  select case (giorno)
    case (1)
      print *, 'Lunedì'
    case (2)
      print *, 'Martedì'
    case (3)
      print *, 'Mercoledì'
    case (4)
      print *, 'Giovedì'
    case (5)
      print *, 'Venerdì'
    case (6, 7)
      print *, 'Weekend!'
    case default
      print *, 'Valore non valido'
  end select
end program giorno_settimana
```

### Range nel select case
Il `select case` supporta range di valori, che lo rendono molto espressivo:

```fortran
program valutazione
  implicit none
  integer :: voto

  voto = 85

  select case (voto)
    case (90:100)
      print *, 'Eccellente'
    case (80:89)
      print *, 'Ottimo'
    case (70:79)
      print *, 'Buono'
    case (60:69)
      print *, 'Sufficiente'
    case (:59)
      print *, 'Insufficiente'
    case default
      print *, 'Voto non valido'
  end select
end program valutazione
```

Il `select case` funziona con `integer`, `character` e `logical`. Non funziona con `real`, perché i confronti in virgola mobile per uguaglianza sono intrinsecamente problematici. Per valori reali, usare catene di `if-else if`.

### Select case con character

```fortran
program menu
  implicit none
  character(len=1) :: scelta

  scelta = 'b'

  select case (scelta)
    case ('a', 'A')
      print *, 'Hai scelto: Avvia'
    case ('b', 'B')
      print *, 'Hai scelto: Backup'
    case ('q', 'Q')
      print *, 'Uscita'
    case default
      print *, 'Scelta non valida'
  end select
end program menu
```

## 12. Il ciclo do: iterazione fondamentale
Il ciclo `do` è il costrutto di iterazione principale in Fortran. Esistono diverse forme.

### do con contatore

```fortran
program somma_naturali
  implicit none
  integer :: i, somma

  somma = 0
  do i = 1, 100
    somma = somma + i
  end do

  print *, 'Somma dei primi 100 naturali:', somma
end program somma_naturali
```

La variabile `i` va da 1 a 100, incrementata di 1 a ogni iterazione. Si può specificare un passo diverso:

```fortran
! Conta da 10 a 1 (passo -1)
do i = 10, 1, -1
  print *, i
end do

! Conta i pari da 2 a 20 (passo 2)
do i = 2, 20, 2
  print *, i
end do
```

### do while

```fortran
program radice_babilonese
  implicit none
  real :: x, guess, tolerance

  x = 25.0
  guess = x / 2.0
  tolerance = 1.0e-6

  do while (abs(guess**2 - x) > tolerance)
    guess = (guess + x / guess) / 2.0
  end do

  print *, 'Radice quadrata di', x, 'è circa', guess
end program radice_babilonese
```

Il `do while` continua a iterare finché la condizione è vera. È utile quando non si conosce in anticipo il numero di iterazioni.

### do infinito (con exit)

```fortran
program input_validato
  implicit none
  integer :: n

  do
    print *, 'Inserisci un numero positivo:'
    read *, n
    if (n > 0) exit
    print *, 'Numero non valido, riprova.'
  end do

  print *, 'Hai inserito:', n
end program input_validato
```

Il `do` senza limiti crea un loop infinito. L'istruzione `exit` esce dal loop. Questo pattern è molto comune per la validazione dell'input.

## 13. Cycle e exit: controllo fine del loop
`cycle` e `exit` permettono di controllare il flusso all'interno di un loop in modo preciso.

### exit
Termina immediatamente il loop e continua con l'istruzione successiva al loop.

### cycle
Salta il resto dell'iterazione corrente e passa all'iterazione successiva.

```fortran
program filtra_pari
  implicit none
  integer :: i

  print *, 'Numeri dispari da 1 a 20:'
  do i = 1, 20
    if (mod(i, 2) == 0) cycle  ! Salta i pari
    print *, i
  end do
end program filtra_pari
```

```fortran
program cerca_primo_multiplo
  implicit none
  integer :: i

  ! Trova il primo multiplo di 7 maggiore di 100
  do i = 101, 200
    if (mod(i, 7) == 0) then
      print *, 'Primo multiplo di 7 dopo 100:', i
      exit
    end if
  end do
end program cerca_primo_multiplo
```

## 14. Loop etichettati (named loops)
In Fortran, i loop possono avere etichette (nomi). Questo è particolarmente utile con loop annidati, dove `exit` e `cycle` devono riferirsi a un loop specifico.

```fortran
program loop_etichettati
  implicit none
  integer :: i, j

  esterno: do i = 1, 10
    interno: do j = 1, 10
      if (i * j > 25) then
        print *, 'Primo prodotto > 25:', i, '*', j, '=', i*j
        exit esterno  ! Esce dal loop esterno, non solo dall'interno
      end if
    end do interno
  end do esterno

  print *, 'Fine'
end program loop_etichettati
```

Senza l'etichetta, `exit` uscirebbe solo dal loop interno. Con `exit esterno`, si esce dal loop esterno. Lo stesso vale per `cycle`: `cycle esterno` salta all'iterazione successiva del loop esterno.

```fortran
program cerca_nella_matrice
  implicit none
  integer :: matrice(5, 5)
  integer :: i, j, obiettivo
  logical :: trovato

  ! Inizializza la matrice
  do i = 1, 5
    do j = 1, 5
      matrice(i, j) = i * 10 + j
    end do
  end do

  obiettivo = 34
  trovato = .false.

  ricerca: do i = 1, 5
    do j = 1, 5
      if (matrice(i, j) == obiettivo) then
        print *, 'Trovato', obiettivo, 'alla posizione (', i, ',', j, ')'
        trovato = .true.
        exit ricerca
      end if
    end do
  end do ricerca

  if (.not. trovato) print *, obiettivo, 'non trovato'
end program cerca_nella_matrice
```

## 15. do concurrent: parallelismo implicito
Il costrutto `do concurrent` è stato introdotto in Fortran 2008 per esprimere loop che possono essere eseguiti in qualsiasi ordine, e quindi potenzialmente in parallelo. Non è una garanzia di parallelismo, ma è un'indicazione al compilatore.

```fortran
program operazione_vettoriale
  implicit none
  integer, parameter :: n = 1000
  real :: a(n), b(n), c(n)
  integer :: i

  ! Inizializzazione
  do concurrent (i = 1:n)
    a(i) = real(i)
    b(i) = real(i) * 2.0
  end do

  ! Operazione vettoriale
  do concurrent (i = 1:n)
    c(i) = a(i) + b(i)
  end do

  print *, 'c(1) =', c(1), 'c(n) =', c(n)
end program operazione_vettoriale
```

Le regole per `do concurrent` sono importanti:
- Ogni iterazione deve essere indipendente dalle altre
- Non si può usare `exit` o `cycle` dentro un `do concurrent`
- Non si devono modificare variabili che sono lette in altre iterazioni
- Le operazioni di I/O non sono permesse (in linea di principio)

`do concurrent` è un concetto avanzato che verrà approfondito nel capitolo sul parallel computing, ma è utile iniziare a usarlo fin da subito per loop indipendenti.

## 16. Il costrutto block (Fortran 2008)
Il costrutto `block` permette di creare uno scope locale all'interno di una procedura. Le variabili dichiarate in un blocco sono visibili solo all'interno di quel blocco.

```fortran
program esempio_block
  implicit none
  integer :: x

  x = 10
  print *, 'x nel program:', x

  block
    integer :: x  ! Questa è una variabile diversa, locale al block
    x = 99
    print *, 'x nel block:', x
  end block

  print *, 'x dopo il block:', x  ! Stampa 10, non 99
end program esempio_block
```

Il costrutto `block` è utile per:
- limitare lo scope di variabili temporanee
- dichiarare variabili nel punto in cui servono, anziché all'inizio della procedura
- evitare conflitti di nomi

```fortran
subroutine elabora(dati, n)
  implicit none
  integer, intent(in) :: n
  real, intent(inout) :: dati(n)
  integer :: i

  ! Normalizzazione con variabili temporanee in un block
  block
    real :: valore_max
    valore_max = maxval(dati)
    if (valore_max > 0.0) then
      do i = 1, n
        dati(i) = dati(i) / valore_max
      end do
    end if
  end block
  ! valore_max non esiste più qui
end subroutine elabora
```

## 17. Il costrutto associate (Fortran 2003)
Il costrutto `associate` permette di creare alias temporanei per espressioni complesse, migliorando la leggibilità del codice.

```fortran
program esempio_associate
  implicit none
  real :: punti(100, 3)  ! 100 punti in 3D
  integer :: i

  ! Inizializza con valori casuali
  call random_number(punti)

  ! Calcola la distanza dall'origine per ogni punto
  do i = 1, 100
    associate(x => punti(i, 1), y => punti(i, 2), z => punti(i, 3))
      if (sqrt(x**2 + y**2 + z**2) > 1.0) then
        print '(A, I3, A, F6.3)', 'Punto ', i, ' fuori dalla sfera unitaria, distanza: ', &
          sqrt(x**2 + y**2 + z**2)
      end if
    end associate
  end do
end program esempio_associate
```

`associate` è particolarmente utile quando si lavora con strutture dati complesse, dove accedere a un campo può richiedere espressioni lunghe come `configurazione%sistema%particelle(i)%posizione%x`. Con `associate`, si crea un alias semplice per questa espressione.

## 18. Procedure pure
Una procedura `pure` è una procedura che non ha effetti collaterali. In pratica, questo significa che:
- non modifica variabili globali o di modulo
- non esegue operazioni di I/O
- non modifica argomenti con `intent(in)` (ovviamente) e non ha argomenti senza intent
- tutti gli argomenti di una function pure devono essere `intent(in)`

```fortran
pure function norma_vettore(v, n) result(norma)
  implicit none
  integer, intent(in) :: n
  real, intent(in) :: v(n)
  real :: norma
  norma = sqrt(sum(v**2))
end function norma_vettore
```

Le procedure `pure` possono essere usate in contesti dove le procedure normali non sono ammesse, ad esempio dentro `do concurrent` e `forall`. Dichiarare una procedura come `pure` è un impegno formale a non avere effetti collaterali, e il compilatore verifica questo impegno.

### Perché le procedure pure sono importanti
Le procedure pure sono importanti per il calcolo scientifico perché:
- sono sicure da chiamare in contesti paralleli
- il compilatore può ottimizzarle più aggressivamente
- documentano formalmente l'assenza di effetti collaterali
- sono riutilizzabili in più contesti

## 19. Procedure elemental
Una procedura `elemental` è una procedura pure che opera su scalari ma può essere automaticamente applicata a interi array.

```fortran
elemental function celsius_in_fahrenheit(c) result(f)
  implicit none
  real, intent(in) :: c
  real :: f
  f = c * 9.0 / 5.0 + 32.0
end function celsius_in_fahrenheit
```

```fortran
program test_elemental
  implicit none
  real :: temperature_c(5) = [0.0, 20.0, 37.0, 100.0, -40.0]
  real :: temperature_f(5)

  interface
    elemental function celsius_in_fahrenheit(c) result(f)
      real, intent(in) :: c
      real :: f
    end function celsius_in_fahrenheit
  end interface

  ! La funzione elemental si applica automaticamente a tutto l'array
  temperature_f = celsius_in_fahrenheit(temperature_c)

  print *, 'Celsius:    ', temperature_c
  print *, 'Fahrenheit: ', temperature_f
end program test_elemental
```

Le procedure `elemental` sono estremamente potenti in Fortran perché permettono di scrivere codice che opera naturalmente sia su scalari sia su array di qualsiasi forma, senza duplicare la logica. Il compilatore si occupa di applicare la funzione a ogni elemento dell'array.

Le procedure elemental devono rispettare tutte le regole delle procedure pure (sono implicitamente pure), con l'aggiunta che tutti gli argomenti devono essere scalari.

## 20. Passaggio di array alle procedure
Il passaggio di array alle procedure in Fortran ha diverse modalità, ognuna con implicazioni diverse per la flessibilità e la sicurezza.

### Assumed-shape arrays (consigliato)
Con gli array assumed-shape, la procedura riceve la forma dell'array automaticamente:

```fortran
subroutine stampa_array(arr)
  implicit none
  real, intent(in) :: arr(:)  ! Assumed-shape: dimensione determinata dall'argomento
  integer :: i

  do i = 1, size(arr)
    print *, 'arr(', i, ') =', arr(i)
  end do
end subroutine stampa_array
```

Gli array assumed-shape richiedono un'interfaccia esplicita (quindi moduli o contains). La procedura usa `size(arr)` per conoscere la dimensione.

### Explicit-shape arrays
Con array explicit-shape, la dimensione è passata come argomento separato:

```fortran
subroutine somma_vettori(a, b, c, n)
  implicit none
  integer, intent(in) :: n
  real, intent(in) :: a(n), b(n)
  real, intent(out) :: c(n)
  integer :: i

  do i = 1, n
    c(i) = a(i) + b(i)
  end do
end subroutine somma_vettori
```

Questo stile è più antico e meno sicuro, perché il compilatore non può verificare che `n` corrisponda effettivamente alla dimensione degli array passati. Tuttavia, è ancora comune in codice legacy e non richiede interfacce esplicite.

### Array multidimensionali

```fortran
module algebra
  implicit none
contains
  subroutine moltiplica_matrice_vettore(A, x, y)
    real, intent(in) :: A(:,:)    ! Matrice assumed-shape 2D
    real, intent(in) :: x(:)      ! Vettore assumed-shape
    real, intent(out) :: y(:)     ! Risultato
    integer :: i, j, m, n

    m = size(A, 1)   ! Numero di righe
    n = size(A, 2)   ! Numero di colonne

    do i = 1, m
      y(i) = 0.0
      do j = 1, n
        y(i) = y(i) + A(i, j) * x(j)
      end do
    end do
  end subroutine moltiplica_matrice_vettore
end module algebra
```

## 21. Esempio integrato: un risolutore di equazioni di secondo grado
Per mettere insieme molti dei concetti visti in questo capitolo, vediamo un programma completo che risolve equazioni di secondo grado.

```fortran
module equazioni
  implicit none
  integer, parameter :: dp = selected_real_kind(15, 307)
contains

  subroutine risolvi_secondo_grado(a, b, c, x1, x2, n_soluzioni)
    real(dp), intent(in) :: a, b, c
    complex(dp), intent(out) :: x1, x2
    integer, intent(out) :: n_soluzioni
    real(dp) :: discriminante

    if (abs(a) < epsilon(a)) then
      ! Non è un'equazione di secondo grado
      if (abs(b) < epsilon(b)) then
        n_soluzioni = 0
        x1 = (0.0_dp, 0.0_dp)
        x2 = (0.0_dp, 0.0_dp)
      else
        n_soluzioni = 1
        x1 = cmplx(-c / b, 0.0_dp, dp)
        x2 = x1
      end if
      return
    end if

    discriminante = b**2 - 4.0_dp * a * c

    if (discriminante > 0.0_dp) then
      n_soluzioni = 2
      x1 = cmplx((-b + sqrt(discriminante)) / (2.0_dp * a), 0.0_dp, dp)
      x2 = cmplx((-b - sqrt(discriminante)) / (2.0_dp * a), 0.0_dp, dp)
    else if (abs(discriminante) < epsilon(discriminante)) then
      n_soluzioni = 1
      x1 = cmplx(-b / (2.0_dp * a), 0.0_dp, dp)
      x2 = x1
    else
      n_soluzioni = 2
      x1 = cmplx(-b / (2.0_dp * a), sqrt(-discriminante) / (2.0_dp * a), dp)
      x2 = cmplx(-b / (2.0_dp * a), -sqrt(-discriminante) / (2.0_dp * a), dp)
    end if
  end subroutine risolvi_secondo_grado

  subroutine stampa_risultato(a, b, c, x1, x2, n_soluzioni)
    real(dp), intent(in) :: a, b, c
    complex(dp), intent(in) :: x1, x2
    integer, intent(in) :: n_soluzioni

    print '(A, F6.2, A, F6.2, A, F6.2)', &
      'Equazione: ', a, 'x² + ', b, 'x + ', c
    
    select case (n_soluzioni)
      case (0)
        print *, '  Nessuna soluzione'
      case (1)
        print '(A, F10.4)', '  Soluzione unica: x = ', real(x1)
      case (2)
        if (aimag(x1) == 0.0_dp) then
          print '(A, F10.4)', '  x1 = ', real(x1)
          print '(A, F10.4)', '  x2 = ', real(x2)
        else
          print '(A, F10.4, A, F10.4, A)', '  x1 = ', real(x1), ' + ', aimag(x1), 'i'
          print '(A, F10.4, A, F10.4, A)', '  x2 = ', real(x2), ' + ', aimag(x2), 'i'
        end if
    end select
    print *
  end subroutine stampa_risultato

end module equazioni

program risolutore
  use equazioni
  implicit none
  real(dp) :: a, b, c
  complex(dp) :: x1, x2
  integer :: n_sol

  ! Caso 1: due soluzioni reali
  a = 1.0_dp; b = -5.0_dp; c = 6.0_dp
  call risolvi_secondo_grado(a, b, c, x1, x2, n_sol)
  call stampa_risultato(a, b, c, x1, x2, n_sol)

  ! Caso 2: soluzione unica
  a = 1.0_dp; b = -2.0_dp; c = 1.0_dp
  call risolvi_secondo_grado(a, b, c, x1, x2, n_sol)
  call stampa_risultato(a, b, c, x1, x2, n_sol)

  ! Caso 3: soluzioni complesse
  a = 1.0_dp; b = 2.0_dp; c = 5.0_dp
  call risolvi_secondo_grado(a, b, c, x1, x2, n_sol)
  call stampa_risultato(a, b, c, x1, x2, n_sol)
end program risolutore
```

Questo esempio mostra l'uso combinato di moduli, subroutine, function, intent, select case, epsilon per confronti numerici e tipi complessi.

## 22. Continuazione di riga e formattazione del codice
Un aspetto pratico della programmazione procedurale è la formattazione del codice. In Fortran, una riga troppo lunga può essere continuata usando il carattere `&` alla fine della riga:

```fortran
risultato = valore_iniziale + coefficiente_primo * x &
          + coefficiente_secondo * x**2 &
          + coefficiente_terzo * x**3
```

Quando si usa `&` in una stringa, è necessario mettere `&` anche all'inizio della riga successiva:

```fortran
print *, 'Questo è un messaggio molto lungo che &
         &continua sulla riga successiva'
```

La formattazione ordinata del codice è parte della qualità professionale. In Fortran, l'indentazione standard è di 2 spazi per livello di nesting. Usare un'indentazione coerente rende il codice molto più leggibile, soprattutto con loop e condizioni annidate.

## 23. Errori frequenti nella programmazione procedurale Fortran
Questi sono gli errori più comuni che si incontrano quando si inizia a scrivere procedure in Fortran:

- **Dimenticare `intent`**: senza intent, il compilatore non può verificare l'uso corretto degli argomenti. Dichiarare sempre l'intent.
- **Interfaccia implicita con argomenti sbagliati**: chiamare una procedura esterna senza interfaccia esplicita con argomenti di tipo errato causa errori silenti. Usare moduli.
- **Confondere subroutine e function**: tentare di usare una subroutine in un'espressione o chiamare una function con `call`.
- **Modificare un argomento `intent(in)`**: il compilatore lo segnala, ma è un errore di design che indica che l'intent è sbagliato.
- **Non controllare `present()` per argomenti opzionali**: accedere a un argomento opzionale non passato è un comportamento indefinito.
- **Ricorsione senza caso base**: come in tutti i linguaggi, la ricorsione senza condizione di uscita causa stack overflow.
- **Ordine di compilazione errato**: i moduli devono essere compilati prima di chi li usa.
- **Loop infiniti**: dimenticare di aggiornare la condizione di uscita in un `do while` o dimenticare `exit` in un `do` infinito.
- **Confondere `=` e `==`**: `=` è assegnazione, `==` è confronto. In una condizione `if`, usare `==`.

## 24. Una prospettiva finale sulla programmazione procedurale
La programmazione procedurale è il paradigma naturale di Fortran e rimane il modo più diretto di strutturare codice scientifico. Le subroutine e le function sono i mattoni con cui si costruiscono programmi complessi, e gli attributi come `intent`, `pure` e `elemental` forniscono strumenti potenti per scrivere codice sicuro e ottimizzabile.

Il punto chiave è che la buona programmazione procedurale non è "mettere tutto in subroutine". È pensare in termini di responsabilità chiare: ogni procedura dovrebbe fare una cosa sola, farla bene, e comunicare con il resto del programma solo attraverso i suoi argomenti. Questo principio di separazione delle responsabilità è alla base di qualsiasi software di qualità, indipendentemente dal paradigma.

Con le basi procedurali solide coperte in questo capitolo, si è pronti per affrontare argomenti più avanzati come i moduli e l'organizzazione di progetti complessi, i tipi derivati e la programmazione orientata agli oggetti in Fortran.
